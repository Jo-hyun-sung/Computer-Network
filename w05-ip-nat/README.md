# Week 5 Lab · Addresses, Subnets, NAT, DHCP

**Theory** — 5-2 IPv4 addressing and subnets (§4.3.2) · DHCP (§4.3.2) · NAT (§4.3.3)
**Textbook lab (path B)** — Wireshark Lab: IP, and the DHCP trace
**Submit to** — `w05-ip-nat/out/`

An address is not a name and it is not a place. This week: what your address
actually means, who gave it to you, why the world sees a different one, and how
a router decides where a packet goes when several answers are right at once.

```bash
cd w05-ip-nat
```

| | Task | You build |
|---|---|---|
| 1 | Subnets and longest-prefix match | a CIDR parser and a forwarding table, from integers up |
| 2 | Where exactly are you? | an address study on two networks, and a DHCP capture |
| 3 | Make the lookup fast | a table that answers 20,000 queries without checking every route |

Details and requirements are in **`task1.md`**, **`task2.md`**, **`task3.md`**.

---

## Running everything

```bash
python3 task1_forward.py --verify
python3 task2_myaddr.py --collect "campus wifi"
python3 bench.py --yours
python3 test_tasks.py
```

## What to submit

| File | From |
|---|---|
| `task1_forward.py` | your parser and forwarding table |
| `out/addresses.json` | at least two labelled networks |
| `out/dhcp.pcapng` | your own DORA capture |
| `out/report.md` | the address analysis |
| `task3_lpm.py` · `out/bench.txt` | your fast table and its numbers |
| `out/observation.md` | 2–3 lines per task |

```bash
python3 ../check.py w05
```

## Path (B) · when measurement is blocked

- **Task 1** — unaffected
- **Task 2** — a DHCP exchange only happens when you join a network, so it is easy
  to miss. If you cannot catch one, use the official **DHCP trace** in `traces/`.
  You still need two networks for the address half
- **Task 3** — unaffected. Fully synthetic
