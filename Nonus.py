
import json
import logging
import os
import signal
import sys

log = logging.getLogger(__name__)

_stop_requested = False


def _request_stop(signum, frame):
    global _stop_requested
    _stop_requested = True
    log.info(f"Received signal {signum}; will checkpoint and stop after the current number.")


def setup_logging(start: int, limit: int) -> str:
    log_file = f"consecutive_sexy_prime_conjecture_{start}_{limit}.log"
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
    return f"consecutive_sexy_prime_conjecture_checkpoint_{start}_{limit}.json"


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
    is_prime = bytearray([1]) * (limit + 1)
    is_prime[0:2] = b"\x00\x00"
    for i in range(2, int(limit ** 0.5) + 1):
        if is_prime[i]:
            is_prime[i * i:: i] = bytearray(len(is_prime[i * i:: i]))
    return [i for i, v in enumerate(is_prime) if v]


def consecutive_sexy_members(primes):
    """Primes that belong to a consecutive sexy pair (gap 6, no prime in between), ascending."""
    members = set()
    for a, b in zip(primes, primes[1:]):
        if b - a == 6:
            members.add(a)
            members.add(b)
    return sorted(members)


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

    primes = sieve(limit)
    members = consecutive_sexy_members(primes)
    member_set = set(members)

    total = (limit - start) // 2 + 1
    checkpoint_every = max(1, total // 200)

    step = 0
    for n in range(resume_n, limit + 1, 2):
        found = None
        for p in members:
            if p > n - p:
                break
            q = n - p
            if q in member_set:
                found = (p, q)
                break
        if found:
            solutions_count += 1
        else:
            failures.append(n)
            log.info(f"{n}: NO consecutive-sexy-prime decomposition found (FAILURE)")

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
        start, limit = 4, args[0]
    else:
        start, limit = 4, 1000

    log_file = setup_logging(start, limit)
    solutions_count, failures = verify(start, limit)

    log.info(f"\nChecked even integers from {start} to {limit}")
    log.info("Consecutive sexy prime pairs: primes p, q with |p - q| = 6 and no prime strictly between them\n")

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
