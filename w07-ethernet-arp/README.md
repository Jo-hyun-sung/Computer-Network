# Week 7 Lab · Ethernet, ARP and Switching

**Theory** — 7-2 MAC addresses and ARP (§6.4.1) · switch self-learning (§6.4.3)
**Textbook lab (path B)** — Wireshark Lab: 802.11 / Ethernet
**Submit to** — `w07-ethernet-arp/out/`

Below IP there is a second addressing system that nobody configures and that
forgets everything every few minutes. This week: build the switch that learns it,
watch your own machine ask "who has this address", and then make the learning fit
in a table that is too small.

```bash
cd w07-ethernet-arp
```

| | Task | You build |
|---|---|---|
| 1 | A learning switch | self-learning, flooding, aging — about thirty lines that have to be exactly right |
| 2 | Watch ARP happen | your own ARP table emptied and refilled, captured |
| 3 | A switch that runs out of room | an eviction policy for a table that cannot hold everyone |

Details and requirements are in **`task1.md`**, **`task2.md`**, **`task3.md`**.

---

## Running everything

```bash
python3 task1_switch.py --verify
python3 bench.py --yours
python3 test_tasks.py
```

## What to submit

| File | From |
|---|---|
| `task1_switch.py` | your learning switch |
| `out/arp-before.txt` · `out/arp-after.txt` | your ARP table, emptied and refilled |
| `out/arp.pcapng` | request and reply on the wire |
| `task3_flooding.py` · `out/bench.txt` | your eviction policy and its numbers |
| `out/observation.md` | 2–3 lines per task |

```bash
python3 ../check.py w07
```

## Path (B) · when capture is blocked

Task 2 needs your own machine — clearing an ARP table requires administrator
rights. If you cannot get them, `task2.md` has a route using the official trace,
and you say what it weakens. Tasks 1 and 3 are pure Python and run anywhere.
