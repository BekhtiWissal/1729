import json
import logging
import os
import signal
import sys

log = logging.getLogger(__name__)

_stop_requested = False

MARGIN = 1_000_000      # sieve headroom above LIMIT, for case (B): 2n + p'


def _request_stop(signum, frame):
    global _stop_requested
    _stop_requested = True
    log.info(f"Received signal {signum}; will checkpoint and stop after the current number.")


def setup_logging(start: int, limit: int) -> str:
    log_file = f"tertius_conjecture_{start}_{limit}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[
            logging.FileHandler(log_file, mode="a"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return log_file


def checkpoint_path(start: int, limit: int) -> str:
    return f"tertius_conjecture_checkpoint_{start}_{limit}.json"


def load_checkpoint(start: int, limit: int):
    path = checkpoint_path(start, limit)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def save_checkpoint(start: int, limit: int, next_n: int, solutions_count: int, failures: list):
    path = checkpoint_path(start, limit)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(
            {"next_n": next_n, "solutions_count": solutions_count, "failures": failures},
            f,
        )
    os.replace(tmp_path, path)


def sieve(limit: int):
    """is_prime over [0, limit + MARGIN + 8]: case (B) probes above the limit."""
    top = limit + MARGIN + 8
    is_prime = bytearray([1]) * (top + 1)
    is_prime[0:2] = b"\x00\x00"
    for i in range(2, int(top ** 0.5) + 1):
        if is_prime[i]:
            is_prime[i * i:: i] = bytearray(len(is_prime[i * i:: i]))
    return is_prime


def check_addition(n, is_prime):
    """(A) 2n = p + p' with p or p' a lower cousin member. No lists used."""
    for p in range(3, n // 2 + 1, 2):
        q = n - p
        if is_prime[p] and is_prime[q] and (is_prime[p + 4] or is_prime[q + 4]):
            return (p, q)
    return None


def check_subtraction(n, is_prime, top):
    """(B) 2n = p - p' with p' an upper cousin member. No lists used."""
    pp = 7
    while n + pp <= top:
        if is_prime[pp] and is_prime[pp - 4] and is_prime[n + pp]:
            return (n + pp, pp)
        pp += 2
    return None


def verify(start: int, limit: int):
    checkpoint = load_checkpoint(start, limit)
    if checkpoint:
        resume_n = checkpoint["next_n"]
        solutions_count = checkpoint["solutions_count"]
        failures = checkpoint["failures"]
        log.info(f"Resuming from checkpoint: next number to check is {resume_n}")
    else:
        resume_n = start
        solutions_count = 0
        failures = []

    if resume_n > limit:
        log.info("Checkpoint shows this range is already complete.")
        return solutions_count, failures

    is_prime = sieve(limit)
    top = len(is_prime) - 1

    total = (limit - start) // 2 + 1
    checkpoint_every = max(1, total // 200)

    step = 0
    for n in range(resume_n, limit + 1, 2):
        if n % 3 != 1:                       # residue restriction: skip 2n = 1 (mod 3)
            add = check_addition(n, is_prime)
            sub = check_subtraction(n, is_prime, top)
            if add and sub:                  # success only if BOTH cases have witnesses
                solutions_count += 1
            else:
                which = ("A+B" if not add and not sub
                         else ("A (addition)" if not add else "B (subtraction)"))
                failures.append(n)
                log.info(f"{n}: NO witness for case {which} (FAILURE)")

        step += 1
        if step % checkpoint_every == 0 or n == limit or _stop_requested:
            log.info(
                f"Progress: {n}/{limit} checked "
                f"({solutions_count} solutions, {len(failures)} failures so far)"
            )
            save_checkpoint(start, limit, n + 2, solutions_count, failures)

        if _stop_requested:
            log.info(f"Stopped at {n}/{limit}. Checkpoint saved; re-run the same command to resume.")
            sys.exit(75)

    return solutions_count, failures


def main():
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)

    args = [int(a) for a in sys.argv[1:]]
    if len(args) >= 2:
        start, limit = args[0], args[1]
    elif len(args) == 1:
        start, limit = 6, args[0]
    else:
        start, limit = 6, 1000

    log_file = setup_logging(start, limit)
    solutions_count, failures = verify(start, limit)

    log.info(f"\nChecked even integers from {start} to {limit} with 2n != 1 (mod 3)")
    log.info("Case A: 2n = p + p', p or p' in P4^- (lower cousin member)")
    log.info("Case B: 2n = p - p', p' in P4^+ (upper cousin member)")
    log.info("Both cases must hold; a number fails if either case has no witness.\n")

    log.info(f"Solutions found: {solutions_count}")

    log.info("\nNumbers that did NOT verify the conjecture:")
    if failures:
        for n in failures:
            log.info(f"  {n}")
    else:
        log.info("  none")

    log.info(f"\nLog written to {log_file}")


if __name__ == "__main__":
    main()