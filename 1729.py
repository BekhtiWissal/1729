
import time

N_MIN, N_MAX   = 10_000_000_000, 1_000_000_000_000
CANDIDATE_ROOM = 3_000_000_000               # search room for p' above 2n
LIMIT          = 2 * N_MAX 

def sieve(limit):
    s = bytearray([1]) * limit
    s[0:2] = b"\x00\x00"
    for i in range(2, int(limit ** 0.5) + 1):
        if s[i]:
            s[i*i::i] = bytearray(len(s[i*i::i]))
    return s

t0 = time.time()
isp = sieve(LIMIT)
primes = [i for i in range(3, LIMIT) if isp[i]]

upper_twins   = [q for q in primes if q >= 5 and isp[q - 2]]        # P2+
upper_cousins = [q for q in primes if q >= 7 and isp[q - 4]]        # P4+
lower_twins   = [q for q in primes if q + 2 < LIMIT and isp[q + 2]] # P2^-

def by_E_mod3(cands):
    """For each value of 2n mod 3, the sorted candidates q with 3 ∤ (q + 2n)."""
    buckets = {0: [], 1: [], 2: []}
    for q in cands:
        buckets[q % 3].append(q)
    return {e: sorted(q for r in range(3) if (r + e) % 3 for q in buckets[r])
            for e in range(3)}

UT, UC, LT = by_E_mod3(upper_twins), by_E_mod3(upper_cousins), by_E_mod3(lower_twins)
print(f"setup: {time.time()-t0:.2f}s  "
      f"({len(upper_twins)} P2+, {len(upper_cousins)} P4+, {len(lower_twins)} P2^- candidates)")

def witness(E, table):
    """Smallest viable q with q + E prime, i.e. 2n = (q+E) - q. None if exhausted."""
    for q in table[E % 3]:
        if q + E >= LIMIT:
            return None
        if isp[q + E]:
            return q
    return None

fail_main, fail_mod3, fail_simul = [], [], []
case1 = case2 = 0

t0 = time.time()
for n in range(N_MIN, N_MAX + 1):
    E = 2 * n
    q_twin = witness(E, UT)
    if q_twin is not None:
        case1 += 1
        continue
    if E % 3 == 0:
        fail_mod3.append(E)                       # extra mod-3 claim broken
    q_cousin = witness(E, UC)                     # fallback: P4+ case
    if q_cousin is None:
        fail_main.append(E)
        continue
    case2 += 1
    p2 = witness(E, LT)                           # 2n     = p1 - p2, p2 in P2^-
    p4 = witness(E + 4, LT)                       # 2(n+2) = p3 - p4, p4 in P2^-
    if p2 is None or p4 is None:
        fail_simul.append(E)

print(f"main loop: {time.time()-t0:.2f}s\n")
print(f"Checked n = {N_MIN} .. {N_MAX}  (2n up to {2*N_MAX})")
print(f"  resolved by P2+ (first case)         : {case1}")
print(f"  resolved by P4+ fallback (second case): {case2}")
print(f"  MAIN violations (neither case)        : {fail_main[:10] or 'NONE'}")
print(f"  mod-3 claim violations                : {fail_mod3[:10] or 'NONE'}")
print(f"  simultaneous-pattern violations       : {fail_simul[:10] or 'NONE'}")