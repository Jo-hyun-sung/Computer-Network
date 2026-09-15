# Task 2 · Measure Your Own Link, Twice

**Files** — `task2_measure.py`, and a capture you take yourself
**Theory** — §3.5 handshake and sequence numbers, §3.7 what limits throughput
**Kind** — **hands-on. This one cannot be done from code alone.**

---

## Why this task exists

Tasks 1 and 3 run on a simulated network. They would give the same answer on a
laptop with the Ethernet port glued shut. This one is about **your** connection,
right now, and the number will not match anybody else's.

## Part A · Capture a real handshake

Run Wireshark with capture filter `tcp port 443`, then start a transfer:

```bash
python3 task2_measure.py --label "campus wifi"
```

Stop, save as `out/tcp.pcapng`, and find one connection's opening.

| # | Requirement |
|---|---|
| A1 | The capture is your own traffic, from your machine |
| A2 | Point to the SYN, SYN-ACK and ACK of one connection by packet number |
| A3 | Report both **initial sequence numbers**. They are not 0, and not each other |
| A4 | Read the SYN's **options**: MSS, window scale factor, SACK permitted |
| A5 | Compute the **advertised window** after scaling, and compare it with the bytes actually in flight later in the transfer |

A3 is worth stopping on. The lecture said sequence numbers count bytes and start
"at some value". Look at what the two ends actually chose, and ask why not zero.

A5 is where §3.7 becomes concrete: the receiver advertised a window, the sender
never filled it, and something else was the limit.

> **Privacy** — narrow the filter to one host if you can, and check the file
> before submitting. If you cannot clean it, use path (B).

## Part B · Measure throughput on two networks

```bash
python3 task2_measure.py --label "campus wifi"
python3 task2_measure.py --label "tethering"
```

Each run does five transfers and appends to `out/throughput.json`.

| # | Requirement |
|---|---|
| B1 | At least **two labelled networks** — campus Wi-Fi and phone tethering, for example |
| B2 | Five runs each, so you have a spread and not a single number |
| B3 | Report median, spread, and **median handshake time** for each |
| B4 | Explain the spread. Five runs on one network do not agree either — say what varies |
| B5 | Relate handshake time to throughput. They are not independent |

B5 is the point of the whole task. One of these two networks will have a worse
handshake time, and that alone will cost it throughput even if its raw capacity
is the same. Name the mechanism from §3.7 that causes it.

## Pass condition

`out/throughput.json` has two or more labels with five runs each, and
`out/observation.md` answers A2–A5 and B3–B5.

```bash
python3 test_tasks.py --task 2
```

The harness checks the files exist and parse. It cannot check that you read the
packets. That is what `observation.md` is for.

## Path (B) · if capture is blocked

- **Part A** — use the official **Wireshark Lab: Exploring TCP** trace in
  `traces/`. Answer A2–A5 from it, and add: whose transfer was this, and how
  can you tell from the capture alone?
- **Part B** — you still need two vantage points. Phone tethering is the easy
  second one. If you genuinely have one network, measure at two very different
  times of day, label them that way, and say what that weakens

## What to write in `observation.md`

- The two initial sequence numbers, and why they are not zero
- The scaled receive window, and what actually limited the transfer instead
- Your two medians, the spread, and the mechanism from B5
