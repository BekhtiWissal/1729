# 1729

**Representations of even integers by primes from prime pairs at a fixed gap**

This repository contains the verification code for nine conjectures on writing even integers as sums or differences of primes that belong to prime pairs at a fixed even gap $g \in \{2, 4, 6, 8\}$ (twin, cousin, sexy and gap-8 primes), including the consecutive restriction at gap 6.

The conjectures extend the Zwillinger–Dubner twin-prime Goldbach statement in two ways:

1. **Differences as well as sums.** An even integer $2n$ is described both by $2n = p + p'$ and by $2n = p - p'$.
2. **Lower vs upper member.** Each prime is labelled by whether it is the smaller or larger member of its pair. A congruence modulo 3 ties this label to the residue of $2n$ and decides which representations are possible.

All nine conjectures have been verified for every even integer $10 < 2n \le 2 \cdot 10^{10}$.

---

## Notation

For an even gap $g \ge 2$:

$$
\mathbb{P}_g = \{\, p \in \mathbb{P} : p - g \in \mathbb{P} \text{ or } p + g \in \mathbb{P} \,\}
$$

$$
\mathbb{P}_g^- = \{\, p \in \mathbb{P} : p + g \in \mathbb{P} \,\} \quad\text{(lower members)}, \qquad
\mathbb{P}_g^+ = \{\, p \in \mathbb{P} : p - g \in \mathbb{P} \,\} \quad\text{(upper members)}
$$

| Symbol | Meaning |
|---|---|
| $\mathbb{P}_2$ | twin primes |
| $\mathbb{P}_4$ | cousin primes |
| $\mathbb{P}_6$ | sexy primes |
| $\mathbb{P}_6^{\text{cons}}$ | consecutive sexy primes |
| $\mathbb{P}_8$ | primes in pairs with gap 8 (not necessarily consecutive) |

---

## The conjectures

| Script | Conjecture | Statement (for $2n > 10$ unless stated) | Exceptions found |
|---|---|---|---|
| `primos.py` | **Primos** | $2n = p - p'$ with $p' \in \mathbb{P}_2$ | 0 |
| `Secondus.py` | **Secondus** | For $2n \not\equiv 1 \pmod 3$: a sum representation exists with one summand in $\mathbb{P}_4^-$, and a difference representation exists with $p' \in \mathbb{P}_4^+$ | 0 |
| `tertius.py` | **Tertius** | $2n = p + p'$ with $p, p' \in \mathbb{P}_2$ or $p, p' \in \mathbb{P}_4$ | 1 — $\{908\}$ |
| `quartus.py` | **Quārtus** | For $g \in \{2,4\}$: if $2n$ is a sum of two members of $\mathbb{P}_g$, it is such a sum with at least one summand in $\mathbb{P}_g^-$ | 20 |
| `1729.py` | **1729** | $2n = p - p'$ with $p' \in \mathbb{P}_2^+$ or $p' \in \mathbb{P}_4^+$ | 0 |
| `Sextus.py` | **Sextus** | Every $2n > 2952$ is $p + p'$ with $p, p' \in \mathbb{P}_4$ | 34 |
| `Septimus.py` | **Septimus** | Every $2n \ge 10$ is $p + p'$ with $p, p' \in \mathbb{P}_6$ | 0 |
| `Octavus.py` | **Octāvus** | Every $2n > 2324$ is $p + p'$ with $p, p' \in \mathbb{P}_8$ | 20 |
| `Nonus.py` | **Nōnus** | Every $2n > 4916$ is $p + p'$ with $p, p' \in \mathbb{P}_6^{\text{cons}}$ | 56 |

The full exception sets are listed in the paper. For Sextus, the exception set matches [OEIS A133802](https://oeis.org/A133802) once the terms 2, 4 and 8 are removed.

### Conjecture 1729

The central statement is named after the Hardy–Ramanujan taxicab number. It says every even $2n > 10$ is a difference of two primes whose subtrahend is the **upper** member of a twin or a cousin pair.

The word *upper* is what makes this a chain: if $p' \in \mathbb{P}_g^+$ then $p' - g$ is prime, so

$$
2n = p - p' \quad\Longrightarrow\quad 2n + g = p - (p' - g).
$$

Each representation hands one down to a neighbouring even integer, so the even integers are linked together by steps made of twin and cousin pairs.

### Neighbour-shift lemma

If $2n = p + p'$ with $p, p' \in \mathbb{P}_g^-$, then $2n + g$ and $2n + 2g$ are also sums of two members of gap-$g$ pairs. This explains why exceptions appear in runs spaced by the gap, e.g. $\{68, 72, 76\}$ for Sextus or $\{166, 174, 182\}$ for Octāvus.

---

## Example decompositions

| Conjecture | Example |
|---|---|
| Primos | $578806008 = 578806237 - 229$, with $(227, 229)$ twin |
| 1729 | $960016 = 960059 - 43$, with $(41, 43)$ twin |
| Tertius | $63342 = 29 + 63313$, with $(29, 31)$ and $(63311, 63313)$ twin |
| Sextus | $362720 = 487 + 362233$, with $(487, 491)$ and $(362233, 362237)$ cousin |
| Septimus | $1281952 = 131 + 1281821$, with $(131, 137)$ and $(1281821, 1281827)$ sexy |
| Octāvus | $82440 = 269 + 82171$, with $(269, 277)$ and $(82163, 82171)$ gap 8 |
| Nōnus | $744720 = 1553 + 743167$, with $(1553, 1559)$ and $(743161, 743167)$ consecutive sexy |

---

## Verification method

- **Range:** every even integer $10 < 2n \le 2 \cdot 10^{10}$.
- **Primality:** deterministic Miller–Rabin with bases $\{2, 3, 5, 7, 11, 13\}$, which is exact for all integers below $3.4 \times 10^{12}$, so there is no probabilistic error over the range.
- **Densities:** observed pair counts are compared against the Hardy–Littlewood Conjecture B predictions. Gap-6 pairs are predicted (and observed) to be twice as frequent as pairs at gaps 2, 4 and 8.

---

## Usage

Requires Python 3.

```bash
git clone https://github.com/BekhtiWissal/1729.git
cd 1729
python 1729.py
```

Each script checks one conjecture; run the one matching the conjecture you want to test (see the table above).

---


## Key references

- H. Dubner, *Twin prime conjectures*, J. Recreational Math. 30 (1999–2000), 199–205.
- D. Zwillinger, *A Goldbach conjecture using twin primes*, Math. Comp. 33 (1979), 1071.
- G. H. Hardy and J. E. Littlewood, *Some problems of 'Partitio Numerorum' III*, Acta Math. 44 (1923), 1–70.
- OEIS [A007534](https://oeis.org/A007534), [A133802](https://oeis.org/A133802), [A005597](https://oeis.org/A005597).
