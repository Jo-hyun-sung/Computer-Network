# Task 1 · A Learning Switch

**File** — `task1_switch.py`
**Theory** — §6.4.1 MAC addresses, §6.4.3 switch self-learning
**Kind** — implementation · fully offline

---

## What you are building

A switch is handed a frame and has to choose which ports to send it out of.
Nobody configures it. It builds its map by **watching where frames come from**.

That is thirty lines. The thirty lines are not the hard part — what it does when
it does *not* know, and what happens to what it learned when a machine moves, is.

## The rules, in the order they matter

1. **Learn** — the source MAC is reachable through the port the frame arrived on
2. **Never** send a frame back out of the port it arrived on
3. Broadcast destination → every other port
4. Known destination → that one port only
5. Unknown destination → every other port (**flooding**)

Rule 5 is why a switch works at all before it has learned anything.

## Requirements

| # | Requirement |
|---|---|
| R1 | `handle(frame, in_port)` returns the ports to forward out of, **ascending** |
| R2 | All five rules above |
| R3 | A station that **moves** must be relearned on its new port |
| R4 | Entries older than `AGE_SECONDS` are gone from `table()` |
| R5 | `table()` returns `{mac: port}` with no aged-out entries |

R3 and R4 are where this stops being easy. R3 says believe the newest evidence.
R4 says distrust old evidence. They are the same mechanism seen from two sides,
and a switch that gets one without the other is broken in a way that is very
hard to debug from the outside.

## Pass condition

```bash
python3 task1_switch.py --verify
```

Seven checks, including the two that matter: a station moving from port 2 to
port 3, and an entry disappearing after 400 seconds of silence.

```
  all ok
```

## What to write in `observation.md`

- Why must a frame never go back out of the port it came in on? Give the
  concrete thing that breaks if it does
- A switch floods when it does not know. A router drops. Why the difference?
- Your aging is a timeout. What does the switch lose by using time rather than
  something more direct, and what would "more direct" even be?
