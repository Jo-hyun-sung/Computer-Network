# Task 3 · Make Longest-Prefix Match Fast

**Files** — `task3_lpm.py` · harness `bench.py` (**do not edit the harness**)
**Theory** — §4.3.3 forwarding
**Kind** — improvement · fully synthetic, runs anywhere

---

## What you are given

`LinearTable` is correct, and it is probably what you wrote in Task 1: keep the
prefixes in a list, check every one, remember the longest match. On six entries
that is fine. A real router holds close to a million and has to answer while the
packet is still in the buffer.

```bash
python3 bench.py            # baseline only, about 7 seconds
python3 bench.py --yours
```

The harness builds a synthetic table shaped like a real one — mostly `/24`s with
a tail of shorter aggregates and a default route — and asks 20,000 questions,
85% of them inside known prefixes, the way traffic actually falls.

**Where the baseline lands:**

```
  baseline   build   0.00s   lookup   6.715s        2,978 lookups/s
```

A 1 Gbps link delivers on the order of a million small packets a second. The
baseline manages three thousand.

## Requirements

| # | Requirement |
|---|---|
| R1 | `YourTable` exposes `add(network, prefix_len, next_hop)` and `lookup(address)` |
| R2 | `bench.py` unmodified |
| R3 | **Every answer identical to the linear table.** The harness checks all 20,000 |
| R4 | Faster than the baseline |
| R5 | In `observation.md`: what bounds your lookup now? Not "it is faster" — what is the work proportional to? |

R3 is not a formality. A fast router that forwards to the wrong next hop is not
a router, it is an outage.

## Grading

| | Requirement |
|---|---|
| pass | R1–R4, more than 2× |
| good | ≥ **100×** |
| **strong** | ≥ **1000×** |

Both of those are reachable. Two directions:

- **group by prefix length.** There are only 33 possible lengths, and you can ask
  them in an order that lets you stop at the first hit
- **walk the address one bit at a time.** Each bit takes you to at most one child,
  so the work is bounded by the address width, not by the table size

The second is what hardware does. The first is easier — and in Python it is also
faster, which is worth a sentence in `observation.md` about why the textbook
answer and the fast answer are not the same answer here.

## What to write in `observation.md`

- Which structure you chose, and what it cost in memory
- R5: what your lookup time is now proportional to
- Why the bit-walk is what hardware builds even when a hash table beats it in Python
