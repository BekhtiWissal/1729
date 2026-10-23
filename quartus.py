import sys, time
import numpy as np
from numba import njit, prange, set_num_threads

N_MAX    = int(sys.argv[1]) if len(sys.argv) > 1 else 50_000_000
if len(sys.argv) > 2:
    set_num_threads(int(sys.argv[2]))
E_MAX    = 2 * N_MAX
Q_BOUND  = 2_000_000          # small-summand search bound B
SEG_N    = 5_000_000          # how many n per block
MARGIN   = 5                  # twin/cousin flags need +-4 lookahead

# ---------- base sieve (numpy) ----------
def simple_sieve(limit):
    s = np.ones(limit, dtype=np.bool_)
    s[:2] = False
    for i in range(2, int(limit ** 0.5) + 1):
        if s[i]:
            s[i * i::i] = False
    return s

t0 = time.time()
base_limit  = int((E_MAX + Q_BOUND) ** 0.5) + 2
base_sieve  = simple_sieve(base_limit)
base_primes = np.nonzero(base_sieve)[0].astype(np.int64)

# ---------- small candidates up to Q_BOUND ----------
small = simple_sieve(Q_BOUND + MARGIN)
def build_candidates(gap):
    idx = np.nonzero(small[:Q_BOUND])[0]
    idx = idx[idx >= 3]
    up  = small[idx + gap]                                   # lower member: p+gap prime
    dn  = np.zeros_like(up)
    ok  = idx - gap >= 2
    dn[ok] = small[(idx - gap)[ok]]                          # upper member: p-gap prime
    keep = up | dn
    return idx[keep].astype(np.int64), up[keep].astype(np.uint8)
tw_q, tw_lo = build_candidates(2)     # twins  q ascending, lower-flag
co_q, co_lo = build_candidates(4)     # cousins
print(f"setup: {time.time()-t0:.1f}s  base primes to {base_limit}, "
      f"{len(tw_q)} twin / {len(co_q)} cousin candidates <= {Q_BOUND}")

# ---------- segment machinery ----------
@njit(cache=True)
def sieve_segment(lo, hi, base_primes, out):
    n = hi - lo
    for i in range(n):
        out[i] = 1
    if lo == 0:
        out[0] = 0; out[1] = 0
    for p in base_primes:
        if p * p >= hi:
            break
        start = ((lo + p - 1) // p) * p
        if start < p * p:
            start = p * p
        for m in range(start - lo, n, p):
            out[m] = 0

@njit(cache=True, parallel=True)
def scan_block(E0, nE, lo, isp, tw_q, tw_lo, co_q, co_lo, suspects):
    # isp covers [lo, lo+len); flags computed on the fly:
    #   member(x,g)  = isp[x] and (isp[x+g] or isp[x-g])
    #   lower(x,g)   = isp[x] and isp[x+g]
    for k in prange(nE):
        E = E0 + 2 * k
        r = E % 3
        found = False
        if r != 2:                                   # twin case allowed
            for j in range(len(tw_q)):
                q = tw_q[j]
                if 2 * q > E:
                    break
                x = E - q - lo                       # partner index in window
                if isp[x] and (isp[x + 2] or isp[x - 2]):        # partner is twin
                    if tw_lo[j] or isp[x + 2]:                   # one is lower
                        found = True
                        break
        if not found and r != 1:                     # cousin case allowed
            for j in range(len(co_q)):
                q = co_q[j]
                if 2 * q > E:
                    break
                x = E - q - lo
                if isp[x] and (isp[x + 4] or isp[x - 4]):
                    if co_lo[j] or isp[x + 4]:
                        found = True
                        break
        suspects[k] = 0 if found else 1

# ---------- stage 1: blocked scan ----------
suspect_list = []
seg_buf = np.zeros(2 * SEG_N + Q_BOUND + 2 * MARGIN, dtype=np.uint8)
sus_buf = np.zeros(SEG_N, dtype=np.uint8)
t0 = time.time()
n = 6
while n <= N_MAX:
    nE  = min(SEG_N, N_MAX - n + 1)
    E0  = 2 * n
    lo  = E0 - Q_BOUND - MARGIN
    hi  = E0 + 2 * nE + MARGIN
    sieve_segment(lo, hi, base_primes, seg_buf[: hi - lo])
    scan_block(E0, nE, lo, seg_buf, tw_q, tw_lo, co_q, co_lo, sus_buf)
    for k in np.nonzero(sus_buf[:nE])[0]:
        suspect_list.append(E0 + 2 * int(k))
    done = n + nE - 1
    print(f"  n <= {done:>12,}   elapsed {time.time()-t0:8.1f}s   "
          f"suspects so far: {len(suspect_list)}", flush=True)
    n += nE

# ---------- stage 2: exhaustive recheck of suspects (q <= E/2) ----------
def recheck(E):
    lim = E // 2 + MARGIN
    s = simple_sieve(lim + MARGIN)
    r = E % 3
    half = E // 2
    # window around partners [E/2, E)
    plo = half - MARGIN
    win = np.zeros(E - plo + MARGIN, dtype=np.uint8)
    sieve_segment(plo, E + MARGIN, base_primes, win)
    def member(x, g):   # x >= plo assumed on partner side
        return win[x - plo] and (win[x - plo + g] or win[x - plo - g])
    def memberS(x, g):
        return s[x] and ((x + g < len(s) and s[x + g]) or (x - g >= 2 and s[x - g]))
    for q in range(3, half + 1):
        if not s[q]:
            continue
        x = E - q
        if r != 2 and memberS(q, 2) and member(x, 2):
            if (q + 2 < len(s) and s[q + 2]) or win[x - plo + 2]:
                return True
        if r != 1 and memberS(q, 4) and member(x, 4):
            if (q + 4 < len(s) and s[q + 4]) or win[x - plo + 4]:
                return True
    return False

exceptions = [E for E in suspect_list if not recheck(E)]
print(f"\nchecked n = 6 .. {N_MAX}  (2n up to {E_MAX})")
print(f"stage-1 suspects : {len(suspect_list)}")
print(f"TRUE exceptions  : {len(exceptions)}")
print(exceptions if exceptions else "no exceptions beyond stage-2 recheck")