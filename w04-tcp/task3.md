# Task 3 · Beat the Fixed Window

**Files** — `task3_congestion.py` · harness `bench.py` (**do not edit the harness**)
**Theory** — §3.7 TCP congestion control
**Kind** — improvement · fully simulated

---

## What you are given

`FixedWindow` sends 64 packets at a time and never listens. This is not a
strawman — it is what you get with no congestion control at all, and it is
roughly what the internet did until it collapsed in October 1986.

Your sender sees exactly what a real one sees:

```python
.window        how many packets you are willing to have in flight
.on_ack()      one packet made it there and back
.on_loss()     a packet timed out
```

No queue depth, no link rate. You infer them from those two events. That
inference *is* §3.7.

## The link

```
  1 packet per slot   ·   round trip 20 slots   ·   queue 10, tail drop   ·   4000 slots
```

So the pipe holds about 20 packets. Above that you are filling a queue, and
above 30 you are dropping.

## Where the baseline lands

```
  baseline   goodput  986.8/1000 slots   loss  37.4%   retx  2340   avg queue   8.8
```

**Read that before you plan anything.** The baseline has nearly the highest
goodput the link can give. It gets there by keeping the queue permanently full
and throwing away 37% of everything it sends. Every other flow sharing this
link waits behind those 8.8 packets.

So "beat it" does not mean "more goodput". It means: get almost as much, without
wrecking the link.

## Requirements

| # | Requirement |
|---|---|
| R1 | `YourControl` exposes `.window`, `.on_ack()`, `.on_loss()` |
| R2 | `bench.py` unmodified |
| R3 | Loss at most **5%** |
| R4 | Average queue at most **5.0** |
| R5 | In `observation.md`: the baseline has the highest goodput here. Why is it still the worst sender? |

## Grading

| | Requirement |
|---|---|
| pass | R1–R4 |
| good | R1–R4, and goodput ≥ **85%** of the baseline |
| **strong** | R1–R4, and goodput ≥ **93%** of the baseline |

Textbook AIMD lands around 82% — a pass, not a good. Getting past 90% needs you
to think about what the window should converge *to*, not just how to back off.

## What to write in `observation.md`

- R5, in your own words
- What your window converges to, and how that number relates to the link
- What happened to goodput when you made the backoff gentler, and what it cost
