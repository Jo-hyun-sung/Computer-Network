# Task 3 · A Switch That Runs Out of Room

**Files** — `task3_flooding.py` · harness `bench.py` (**do not edit the harness**)
**Theory** — §6.4.3
**Kind** — improvement · fully synthetic, runs anywhere

---

## What you are given

A switch does not have room for every station. Its forwarding table lives in a
fixed amount of fast memory, and when that fills, something has to go. Whatever
goes gets **flooded** the next time anyone sends to it — out of every port, to
every station that did not ask for it.

`NaiveSwitch` handles a full table the simplest way: throw out whichever entry
has been there longest. That is a reasonable first idea and, on this traffic, it
is close to the worst thing you can do.

```bash
python3 bench.py
python3 bench.py --yours
```

## The setup

```
  48 ports   ·   400 stations   ·   table capacity 64   ·   ~58,000 frames
```

The table holds 64 of 400 stations. It cannot win — the question is only which
64 it keeps. Traffic is heavily skewed: a handful of stations carry most of it,
as on any real segment.

**Where the baseline lands:**

```
  baseline     wasted   323,380   delivered 46,347   missed      0
```

323,000 wasted deliveries for 46,000 useful ones. Seven frames landing where
they were not wanted for every one that arrived somewhere it was.

## Requirements

| # | Requirement |
|---|---|
| R1 | `YourSwitch(ports, capacity)` with `.table` and `.handle((src, dst, time), in_port)` |
| R2 | `bench.py` unmodified |
| R3 | `.table` **never** holds more than `capacity` entries. Checked after every frame |
| R4 | No more missed deliveries than the baseline |
| R5 | Fewer wasted deliveries |
| R6 | In `observation.md`: what an attacker could do with what you have just learned about this table |

## Grading

| | Requirement |
|---|---|
| pass | R1–R5, more than 2% cut |
| good | ≥ **25%** cut |
| **strong** | ≥ **45%** cut |

The baseline decides what to keep by **when the entry arrived**, which has
nothing to do with whether it is about to be needed. Fixing that gets you into
"good".

Getting to "strong" needs a second idea, and it is the less obvious one:

> should learning a new source ever be **declined**?

Every switch you have ever met learns unconditionally. Think about what that
costs when the table is full and the newcomer is a station that will never be
heard from again.

## R6 · the part that is not about performance

You now know that this table is small, that it fills, and that a full table
floods. Somebody else knows that too. Describe what they would send, and what
the switch would do for them. The attack has a name — you do not need to know it
to describe it, and describing it is worth more than naming it.

## What to write in `observation.md`

- Your eviction rule, and the evidence you keep to run it
- Whether you decline admissions, and what happened to the numbers when you tried
- R6: the attack, in your own words, and one thing a switch could do about it
