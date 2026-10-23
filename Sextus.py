import argparse
import glob
import json
import os
import sys
import time

import numpy as np

PROBE_MAX = 1_000_000        # small cousin members probed first
BLOCK = 20_000_000           # span of even values per vectorized block


def human(nbytes: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} PiB"


def report_cache(path: str) -> np.ndarray:
    size = os.path.getsize(path)
    sieve = np.load(path, mmap_mode="r")
    n = len(sieve)
    print("=" * 70)
    print("SIEVE CACHE")
    print(f"  file            : {path}")
    print(f"  size on disk    : {human(size)}")
    print(f"  dtype, length   : {sieve.dtype}, {n:,} entries")
    print(f"  valid indices   : 0 .. {n - 1:,}")
    print(f"  primality known up to : {n - 1:,}")
    print(f"  largest even 2n verifiable (needs summands <= 2n) : "
          f"{(n - 1) // 2 * 2:,}")
    if sieve.dtype != np.bool_:
        print("  WARNING: expected a boolean array; this file is not one.")
    return sieve


def report_checkpoints(directory: str) -> None:
    found = sorted(glob.glob(os.path.join(directory, "*checkpoint*.json")))
    print("=" * 70)
    print("CHECKPOINTS FOUND NEXT TO THE CACHE")
    if not found:
        print("  none -- no verification run recorded any progress.")
        print("  (The sieve was written, but the checking loop never "
              "reached its first block.)")
        return
    for f in found:
        try:
            with open(f) as fh:
                d = json.load(fh)
            print(f"  {os.path.basename(f)}")
            print(f"     next number to check : {d.get('next_even', d.get('next_n')):,}")
            print(f"     verified so far      : {d.get('solutions_count', 0):,}")
            print(f"     failures so far      : {len(d.get('failures', []))}")
        except Exception as e:
            print(f"  {os.path.basename(f)}: unreadable ({e})")


def build_members(sieve: np.ndarray, limit: int) -> np.ndarray:
    """members[p] = True iff p prime and (p+4 prime or p-4 prime), p <= limit."""
    print("=" * 70)
    print(f"Building cousin-member array up to {limit:,} "
          f"(~{human(limit)} of RAM) ...")
    t0 = time.time()
    members = np.zeros(limit + 1, dtype=bool)
    CH = 100_000_000
    for lo in range(0, limit + 1, CH):
        hi = min(lo + CH, limit + 1)
        base = np.asarray(sieve[lo:hi], dtype=bool)
        up = np.asarray(sieve[lo + 4:hi + 4], dtype=bool)     # p+4 prime
        dn_lo = max(lo - 4, 0)
        dn = np.asarray(sieve[dn_lo:hi - 4], dtype=bool)      # p-4 prime
        if lo == 0:
            dn = np.concatenate([np.zeros(4, dtype=bool), dn])
        members[lo:hi] = base & (up | dn)
    print(f"  done in {time.time() - t0:.0f}s; "
          f"{int(members.sum()):,} cousin members <= {limit:,}")
    return members


def exhaustive(two_n: int, members: np.ndarray) -> bool:
    for p in range(3, two_n // 2 + 1, 2):
        if members[p] and members[two_n - p]:
            return True
    return False


def find_failures(members: np.ndarray, limit: int):
    small = np.flatnonzero(members[:PROBE_MAX]).astype(np.int64)
    print("=" * 70)
    print(f"Scanning even 2n in [2, {limit:,}] with {len(small):,} small probes ...")
    print("FAILURES (printed as found):")
    failures = []
    checked = 0
    t0 = time.time()
    for lo in range(2, limit + 1, BLOCK):
        hi = min(lo + BLOCK, limit + 1)
        evens = np.arange(lo + (lo & 1), hi, 2, dtype=np.int64)
        if not len(evens):
            continue
        checked += len(evens)
        vals = evens
        idx = np.arange(len(evens))
        for p in small:
            if len(idx) == 0:
                break
            q = vals - int(p)
            ok = (q >= 2) & members[np.clip(q, 0, limit)]
            idx = idx[~ok]
            vals = evens[idx]
        for v in vals:
            v = int(v)
            if not exhaustive(v, members):
                failures.append(v)
                print(f"  {v}")
    print(f"Scan finished in {time.time() - t0:.0f}s.")
    return failures, checked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sieve", help="path to the .npy sieve cache")
    ap.add_argument("--limit", type=int, default=10_000_000_000,
                    help="largest even number to verify (default 10^10)")
    ap.add_argument("--report-only", action="store_true",
                    help="only report cache/checkpoint status, do not scan")
    args = ap.parse_args()

    sieve = report_cache(args.sieve)
    report_checkpoints(os.path.dirname(os.path.abspath(args.sieve)))

    limit = args.limit
    if limit + 4 > len(sieve) - 1:
        sys.exit(f"\nERROR: cache knows primality only to {len(sieve) - 1:,}, "
                 f"but verifying to {limit:,} needs it to {limit + 4:,}.")
    if args.report_only:
        return

    members = build_members(sieve, limit)
    failures, checked = find_failures(members, limit)

    expected = (limit - 2) // 2 + 1
    print("=" * 70)
    print("SUMMARY")
    print(f"  verification limit    : {limit:,}")
    print(f"  even numbers checked  : {checked:,} (expected {expected:,}) -> "
          f"{'OK' if checked == expected else 'MISMATCH'}")
    print(f"  solutions             : {checked - len(failures):,}")
    print(f"  failures              : {len(failures)}")
    print(f"  maximum failure       : {max(failures) if failures else 'none'}")
    print("\nEXCEPTIONAL SET E_4:")
    print("  " + ", ".join(str(f) for f in failures) if failures else "  none")


if __name__ == "__main__":
    main()