# Task 1 · Reliable Delivery Over a Bad Channel

**File** — `task1_rdt.py`
**Theory** — §3.4 reliable data transfer, §3.5 TCP sequence numbers
**Kind** — implementation · fully simulated

---

## What you are building

`UnreliableChannel` loses 10% of packets, duplicates 3%, reorders, and never
tells you which. Move 2,000 bytes across it and have them arrive byte-identical.

This is TCP's reliability with congestion control removed. It is worth building
once by hand before you trust a socket again.

## Requirements

| # | Requirement |
|---|---|
| R1 | Split the data into `PAYLOAD`-sized pieces and number them |
| R2 | The receiver reassembles **in order**, even though the channel reorders |
| R3 | A duplicate arriving twice must not corrupt the output |
| R4 | Anything unacknowledged is retransmitted until it is acknowledged |
| R5 | Do not modify `UnreliableChannel`, and do not read its internals |
| R6 | Terminate. `--verify` gives you 200,000 steps; needing more means a livelock |

R3 is the one people lose. A duplicate ACK and a duplicate data packet fail in
different ways, and both happen here.

## Choose your protocol

Stop-and-wait is easiest to get right and the slowest. A sliding window is the
point of §3.4.3 and will cost you an afternoon. Either passes — **say which you
chose and why** in `observation.md`.

## Pass condition

```bash
python3 task1_rdt.py --verify
```

```
  result   IDENTICAL
```

The harness compares SHA-256 of what went in and what came out. Then try a
different seed — a protocol that only works on seed 246 is not a protocol:

```bash
python3 task1_rdt.py --verify --seed 999
```

## What to write in `observation.md`

- Which protocol you chose, and the one case that forced the choice
- How many packets did the channel actually carry for 2,000 bytes of data?
  Compare with the minimum — that ratio is what reliability cost you
- What broke first: loss, reordering, or duplication?
