
import argparse
import json
import logging
import os
import signal
import sys

import numpy as np

log = logging.getLogger(__name__)

_stop_requested = False

PROBE_MAX = 1_000_000      # small members up to this bound are tried first
BLOCK = 2_000_000          # even numbers per vectorized block (values, not count)


def _request_stop(signum, frame):
    global _stop_requested
    _stop_requested = True
    log.info(f"Received signal {signum}; will checkpoint and stop after the current block.")


def setup_logging(start: int, limit: int) -> str:
    log_file = f"cousin_two_case_conjecture_{start}_{limit}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.FileHandler(log_file, mode="a"),
                  logging.StreamHandler(sys.stdout)],
    )
    return log_file


def checkpoint_path(start: int, limit: int) -> str:
    return f"cousin_two_case_conjecture_checkpoint_{start}_{limit}.json"


def load_checkpoint(start: int, limit: int):
    path = checkpoint_path(start, limit)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def save_checkpoint(start: int, limit: int, next_even: int,
                    solutions_count: int, failures: list):
    path = checkpoint_path(start, limit)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"next_even": next_even,
                   "solutions_count": solutions_count,
                   "failures": failures}, f)
    os.replace(tmp, path)


def build_sieve(top: int, cache: str | None) -> np.ndarray:
    """Boolean is_prime[0..top]; optionally cached to/from a .npy file."""
    if cache and os.path.exists(cache):
        log.info(f"Loading sieve from cache {cache} ...")
        is_prime = np.load(cache, mmap_mode=None)
        if len(is_prime) >= top + 1:
            return is_prime
        log.info("Cache too small for this limit; rebuilding.")
    log.info(f"Sieving to {top:,} (this is the slow, one-off part) ...")
    is_prime = np.ones(top + 1, dtype=bool)
    is_prime[:2] = False
    for p in range(2, int(top ** 0.5) + 1):
        if is_prime[p]:
            is_prime[p * p::p] = False
    if cache:
        log.info(f"Saving sieve cache to {cache} ...")
        np.save(cache, is_prime)
        if not cache.endswith(".npy"):
            os.replace(cache + ".npy", cache)
    return is_prime


def small_members(is_prime: np.ndarray):
    """Ascending lists of lower (p, p+4 prime) and upper (p, p-4 prime)
    cousin members up to PROBE_MAX."""
    idx = np.arange(PROBE_MAX)
    lower = idx[is_prime[:PROBE_MAX] & is_prime[4:PROBE_MAX + 4]]
    upper = idx[4:][is_prime[4:PROBE_MAX] & is_prime[:PROBE_MAX - 4]]
    return lower.astype(np.int64), upper.astype(np.int64)


def resolve_block(evens: np.ndarray, is_prime: np.ndarray,
                  probes: np.ndarray, sign: int) -> np.ndarray:
    """
    For each 2n in `evens`, search a witness prime at 2n + sign*probe:
      sign = -1 : addition case, tests is_prime[2n - p], p a lower member
      sign = +1 : subtraction case, tests is_prime[2n + p'], p' an upper member
    Returns the boolean mask of evens that remain UNRESOLVED.
    """
    open_idx = np.arange(len(evens))
    vals = evens.copy()
    for p in probes:
        if len(open_idx) == 0:
            break
        targets = vals + sign * int(p)
        ok = (targets > 2) & is_prime[np.clip(targets, 0, len(is_prime) - 1)]
        # for the addition case the summand must stay positive and prime;
        # np.clip only guards indexing, `targets > 2` guards correctness
        open_idx = open_idx[~ok]
        vals = evens[open_idx]
    unresolved = np.zeros(len(evens), dtype=bool)
    unresolved[open_idx] = True
    return unresolved


def exhaustive_check(two_n: int, is_prime: np.ndarray, sign: int) -> bool:
    """Slow per-number fallback beyond the small-member probes."""
    if sign < 0:  # addition: any decomposition with a lower member on either side
        for p in range(3, two_n // 2 + 1, 2):
            q = two_n - p
            if is_prime[p] and is_prime[q]:
                if (q + 4 < len(is_prime) and is_prime[q + 4]) or is_prime[p + 4]:
                    return True
        return False
    # subtraction: p' upper member, p = two_n + p' prime, within the sieve
    top = len(is_prime) - 1
    pp = 7
    while two_n + pp <= top:
        if is_prime[pp] and is_prime[pp - 4] and is_prime[two_n + pp]:
            return True
        pp += 2
    return False


def verify(start: int, limit: int, cache: str | None):
    ckpt = load_checkpoint(start, limit)
    if ckpt:
        resume, solutions_count, failures = (ckpt["next_even"],
                                             ckpt["solutions_count"],
                                             ckpt["failures"])
        log.info(f"Resuming from checkpoint: next even number is {resume}")
    else:
        resume, solutions_count, failures = max(start, 6), 0, []

    if resume > limit:
        log.info("Checkpoint shows this range is already complete.")
        return solutions_count, failures

    is_prime = build_sieve(limit + PROBE_MAX + 8, cache)
    lower, upper = small_members(is_prime)
    log.info(f"Small probe lists: {len(lower)} lower members, "
             f"{len(upper)} upper members (up to {PROBE_MAX:,}).")

    block_start = resume
    while block_start <= limit:
        block_end = min(block_start + BLOCK, limit + 1)
        evens = np.arange(block_start + (block_start & 1), block_end, 2,
                          dtype=np.int64)
        evens = evens[evens % 3 != 1]          # residue restriction
        if len(evens):
            unresolved_A = resolve_block(evens, is_prime, lower, sign=-1)
            unresolved_B = resolve_block(evens, is_prime, upper, sign=+1)
            hard = np.flatnonzero(unresolved_A | unresolved_B)
            for i in hard:
                two_n = int(evens[i])
                ok_A = (not unresolved_A[i]) or exhaustive_check(two_n, is_prime, -1)
                ok_B = (not unresolved_B[i]) or exhaustive_check(two_n, is_prime, +1)
                if not (ok_A and ok_B):
                    which = ("A+B" if not ok_A and not ok_B
                             else ("A (addition)" if not ok_A else "B (subtraction)"))
                    failures.append(two_n)
                    log.info(f"{two_n}: FAILURE of case {which}")
            solutions_count += len(evens) - sum(
                1 for i in hard
                if (unresolved_A[i] and not exhaustive_check(int(evens[i]), is_prime, -1))
                or (unresolved_B[i] and not exhaustive_check(int(evens[i]), is_prime, +1)))

        log.info(f"Progress: {block_end - 1:,}/{limit:,} checked "
                 f"({solutions_count:,} verified, {len(failures)} failures so far)")
        save_checkpoint(start, limit, block_end, solutions_count, failures)

        if _stop_requested:
            log.info(f"Stopped at {block_end - 1:,}/{limit:,}. Checkpoint saved; "
                     "re-run the same command to resume.")
            sys.exit(75)
        block_start = block_end

    return solutions_count, failures


def main():
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)

    ap = argparse.ArgumentParser()
    ap.add_argument("bounds", nargs="*", type=int, default=[1000])
    ap.add_argument("--sieve-cache", default=None,
                    help="path to a .npy file caching the sieve between runs")
    args = ap.parse_args()

    if len(args.bounds) >= 2:
        start, limit = args.bounds[0], args.bounds[1]
    else:
        start, limit = 6, args.bounds[0]

    log_file = setup_logging(start, limit)
    solutions_count, failures = verify(start, limit, args.sieve_cache)

    log.info(f"\nChecked even integers 2n with 2n != 1 (mod 3), "
             f"from {start} to {limit}")
    log.info("Case A: 2n = p + q, p or q a lower cousin member (p, p+4 prime)")
    log.info("Case B: 2n = p - p', p' an upper cousin member (p', p'-4 prime)\n")
    log.info(f"Numbers verified (both cases): {solutions_count}")
    log.info("\nNumbers that did NOT verify the conjecture:")
    if failures:
        for n in failures:
            log.info(f"  {n}")
    else:
        log.info("  none")
    log.info(f"\nLog written to {log_file}")


if __name__ == "__main__":
    main()