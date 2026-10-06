# Task 3 · Reconverge Without Recomputing the World

**Files** — `task3_reconverge.py` · harness `bench.py` (**do not edit the harness**)
**Theory** — §5.2.1, §5.3
**Kind** — improvement · fully synthetic, runs anywhere

---

## What you are given

`FullRecompute` does the honest thing: on every link event, throw the table away
and run SPF again from scratch. It is correct, and it is what the first
implementations did. It is also why one flapping link in a large area used to
pin the CPU of every router that could see it.

```bash
python3 bench.py            # baseline
python3 bench.py --yours
```

The harness builds a 400-router area with about 1,600 links and replays 1,000
events — failures, restorations, cost changes — checking your table against a
full recompute **after every single one**.

**Where the baseline lands:**

```
  baseline       SPF runs  1001   wall   0.51s
```

## The score is SPF runs, not seconds

Wall-clock time in Python says more about dictionary overhead than about routing.
"How many times did the CPU have to recompute the world" is the thing that
actually melted routers, so that is what is counted.

Use the provided `dijkstra_table()` for any full recompute. It increments the
counter. Rolling your own SPF to dodge the meter is not an optimisation.

## Requirements

| # | Requirement |
|---|---|
| R1 | `YourRouter(graph, source)` with `.table` and `.link_change(a, b, cost)` |
| R2 | `bench.py` unmodified, and full recomputes go through `dijkstra_table()` |
| R3 | **Table correct after every event.** The harness checks all 1,000 |
| R4 | Fewer SPF runs than the baseline |
| R5 | In `observation.md`: your incremental version is probably **slower in wall time** than the baseline. Explain that, and say whether it would still be the right choice on a router |

## Grading

| | Requirement |
|---|---|
| pass | R1–R4, more than 5% avoided |
| good | ≥ **40%** avoided |
| **strong** | ≥ **75%** avoided |

What is actually true after one link changes:

- most destinations are not affected at all
- a link going **down** matters only if you were using it
- a link going **up**, or getting cheaper, matters only if it creates something shorter —
  and you can test that against the distances you already have, without running SPF

The first two get you to about 45%. The third is what gets you past 75%, and it
is the one that needs you to keep something extra around between events.

R5 is not a trick question. The answer is about what a router is short of, and it
is not the same thing Python is short of.

## What to write in `observation.md`

- What you keep between events, and what it costs you in memory
- The three cases above: which you handle, and which event type still forces a full SPF
- R5: slower in wall time, still right for a router. Why?
