LIMIT = 40_000   # sieve bound
N_MAX = 10_000    # verify n = 6 .. N_MAX  (needs 2*N_MAX well below LIMIT)

def sieve(limit):
    is_p = bytearray([1]) * (limit + 1)
    is_p[0] = is_p[1] = 0
    for i in range(2, int(limit ** 0.5) + 1):
        if is_p[i]:
            is_p[i*i::i] = bytearray(len(is_p[i*i::i]))
    return is_p

is_prime = sieve(LIMIT)

# p' in a twin pair: p' is prime and p'-2 or p'+2 is also prime
twins = [q for q in range(3, LIMIT - 2)
         if is_prime[q] and (is_prime[q - 2] or is_prime[q + 2])]

for n in range(6, N_MAX + 1):
    d = 2 * n
    for q in twins:
        if q + d > LIMIT:
            print(f"n = {n}: sieve too small, raise LIMIT")
            raise SystemExit
        if is_prime[q + d]:
            break  # found: p = q + 2n is prime, p' = q is a twin
    else:
        print(f"COUNTEREXAMPLE: n = {n}")
        raise SystemExit

print(f"Conjecture verified for all 6 <= n <= {N_MAX}")