# Task 3 · Beat the Baseline Cache

**Files** — `task3_cache.py` · harness `bench.py` (**do not edit the harness**)
**Theory** — §2.4.2 caching, §2.4.3 TTL
**Kind** — improvement · fully simulated, so it works on any network

---

## What you are given

`BaselineCache` in `task3_cache.py` works. Somebody wrote it in a hurry. It is bad in
more than one way, and **one of its problems is worse than being slow**.

You are not told where the bugs are. Finding them is half the task.

```bash
python3 bench.py            # baseline only
python3 bench.py --yours    # side by side, once YourCache exists
```

## How you are measured

The harness replays **1,000 queries over a simulated hour** against a simulated upstream:
a fixed 20 ms round trip and a fixture of names with realistic TTLs, from 20 seconds
(a CDN name) to a day (a root server). Everyone runs the same workload, so slow Wi-Fi
does not decide your grade.

Four numbers come back:

| | |
|---|---|
| `upstream` | round trips actually made — lower is better |
| `hit rate` | served without going upstream |
| `stale` | answers served **after their TTL had expired** — must be 0 |
| `sim time` | what the workload would have cost in the real world |

**Where the baseline lands:**

```
  baseline   upstream   325   hit rate  67.5%   stale  266   sim time    6.5s
```

Read that line twice. A 67.5% hit rate looks respectable. **266 of 1,000 answers were
expired records.** A cache that keeps everything forever would post a beautiful hit rate
and be completely wrong — so speed alone is not the score.

## Requirements

| # | Requirement |
|---|---|
| R1 | `YourCache` exposes the same interface: `__init__(upstream)`, `lookup(name, now)`, `stats()` |
| R2 | `bench.py` is unmodified. If you need to change the harness to win, you are not winning |
| R3 | Zero stale answers |
| R4 | No more upstream queries than the baseline |
| R5 | In `observation.md`: the **floor** — how few upstream queries could *any* correct cache make on this workload, and why you cannot go below it |

## Grading

| | Requirement |
|---|---|
| pass | R1–R3 |
| good | R1–R4 |
| **strong** | R1–R5 |

R5 is the real question, and it is worth working out **before** you start optimising,
because it tells you where to stop. There is a number below which no correct cache can go,
and it is not set by how clever your data structure is.

If you find yourself trying to be clever about it, re-read what the TTL is for.

## What to write in `observation.md`

- The two things wrong with the baseline. Name them separately — one is a performance
  problem and one is a correctness problem, and they have the same root cause
- Your floor number from R5, with the reasoning
- Which record in the fixture the baseline handles worst, and why that one
