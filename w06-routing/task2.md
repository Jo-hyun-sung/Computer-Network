# Task 2 · Break a Real Network and Time the Repair

**Files** — `scenario.sh`, `topology/`, and your own measurements
**Theory** — §5.2 link state, §5.3 OSPF
**Kind** — **hands-on. This one cannot be done from code alone.**

---

## Why this task exists

Task 1 computes a table. Task 3 makes the computing cheap. Neither tells you how
long a real network is **broken** while it works that out, and that number —
seconds, not milliseconds — is the reason routing protocols are designed the way
they are.

## Part A · Somebody else's routing, from your machine

```bash
traceroute www.korea.ac.kr   | tee out/traceroute.txt      # Windows: tracert
traceroute www.stanford.edu  | tee -a out/traceroute.txt
traceroute 1.1.1.1           | tee -a out/traceroute.txt
```

| # | Requirement |
|---|---|
| A1 | Three targets: one domestic, one overseas, one anycast |
| A2 | Where does the domestic path leave your campus? Name the hop |
| A3 | Where does the overseas path cross the ocean? You can see it in the latencies |
| A4 | `1.1.1.1` is anycast. How many hops did it take, and what does that tell you about where the replica is? |
| A5 | Some hops show `* * *`. Give the two different reasons that happens — they are not the same problem |

A3 is readable: one hop adds ~100 ms and the rest add 1–2 ms. That single jump is
a submarine cable, and you can find which one by the city names in the hostnames.

## Part B · Your own OSPF area

Three FRR routers in containers, in a triangle.

```bash
bash scenario.sh up          # bring the topology up
bash scenario.sh routes      # each router's table
```

| # | Requirement |
|---|---|
| B1 | `out/route-before.txt` — all three tables once OSPF has converged |
| B2 | Confirm each router learned routes it has **no direct link to**. That is the protocol working |
| B3 | Cut a link and capture the tables again → `out/route-after.txt` |
| B4 | **Time the reconvergence** → `out/reconverge.txt`. From the cut to the moment the table is right again |
| B5 | Restore the link and time it again. The two numbers are different — say why |

```bash
bash scenario.sh cut         # break a link and time the repair
bash scenario.sh restore
```

B4 is the measurement that matters. It will be **seconds**, and OSPF's hello and
dead intervals are why. Find those values in `topology/r1/frr.conf` and check
whether your measured time is consistent with them.

B5 is the interesting half. Coming back is not symmetric with going away, and the
reason is in how a router learns that a neighbour is gone versus that one arrived.

## Part C · Move the traffic without breaking anything

```bash
bash scenario.sh cost
```

| # | Requirement |
|---|---|
| C1 | Change a link's cost so a path moves, without any link going down |
| C2 | Show the table before and after |
| C3 | How long did **this** take compared with B4? Explain the difference |

C3 is the point of the whole week: a cost change propagates as fast as the LSA
floods, while a failure has to be *noticed* first. That is the gap Task 3 lives in.

## Pass condition

All four output files exist and `out/observation.md` answers A2–A5, B2, B4, B5, C3.

```bash
python3 test_tasks.py --task 2
```

## Path (B) · if Docker will not run

Part A needs only `traceroute` and works everywhere — do it in full.

For Parts B and C, if Docker Desktop will not install:

- use a classmate's `route-before.txt` / `route-after.txt`, **naming whose they are**
- you still must answer B4, B5 and C3 from their numbers
- and say explicitly what you did not observe yourself, and what that weakens

This is a real weakening. The timing is the finding, and reading somebody else's
timing is not the same as watching your own network sit broken.

## What to write in `observation.md`

- The ocean crossing hop from A3, and the cable it suggests
- Your reconvergence time, and whether it matches the hello/dead intervals in the config
- Why coming back up is not the same as going down
- C3: why a cost change is faster than a failure
