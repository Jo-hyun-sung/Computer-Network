# Week 4 Lab · TCP — Reliability, Measurement, Congestion

**Theory** — 4-1 TCP (§3.5 handshake, sequence numbers) · 4-2 TCP congestion control (§3.7)
**Textbook lab (path B)** — Wireshark Lab: Exploring TCP
**Submit to** — `w04-tcp/out/`

TCP does three things that IP does not: it numbers what you send, it notices what
went missing, and it slows down when the network is full. This week you build the
first, measure the second on your own link, and fight over the third.

```bash
cd w04-tcp
```

| | Task | You build |
|---|---|---|
| 1 | Reliable delivery over a bad channel | a sender and receiver that survive 10% loss |
| 2 | Measure your own link, twice | a throughput study and a captured handshake |
| 3 | Beat the fixed window | congestion control, judged on a shared link |

Details and requirements are in **`task1.md`**, **`task2.md`**, **`task3.md`**.

---

## Running everything

```bash
python3 task1_rdt.py --verify              # Task 1
python3 task2_measure.py --label "campus"  # Task 2, once per network
python3 bench.py --yours                   # Task 3
python3 test_tasks.py                      # all of it
```

## What to submit

| File | From |
|---|---|
| `task1_rdt.py` | your sender and receiver |
| `out/throughput.json` | at least two labelled networks |
| `out/tcp.pcapng` | your own handshake capture |
| `task3_congestion.py` | your congestion control |
| `out/bench.txt` | output of `python3 bench.py --yours` |
| `out/observation.md` | 2–3 lines per task |

```bash
python3 ../check.py w04
```

## Path (B) · when measurement is blocked

- **Task 1** — unaffected. The channel is simulated
- **Task 2** — if you cannot capture, use the official **Wireshark Lab: Exploring TCP**
  trace in `traces/`. You still need two networks for the throughput half; phone
  tethering counts. If you truly have one network, measure at two very different
  times of day instead and say so
- **Task 3** — unaffected. Fully simulated
