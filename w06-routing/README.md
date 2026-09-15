# Week 6 Lab · Routing and Reconvergence

**Theory** — 6-1 link state and distance vector (§5.2) · 6-2 OSPF (§5.3)
**Submit to** — `w06-routing/out/`

A routing protocol's job is not to find the shortest path. It is to find the
shortest path **again**, quickly, every time something breaks. This week you
compute the table, watch three real routers rebuild theirs after you cut a
cable, and then make the rebuilding cheap.

```bash
cd w06-routing
```

| | Task | You build |
|---|---|---|
| 1 | Link state by hand | Dijkstra, and the forwarding table it produces |
| 2 | Break a real network | three OSPF routers, a cut link, a measured reconvergence |
| 3 | Reconverge without recomputing the world | a router that knows when it can skip SPF |

Details and requirements are in **`task1.md`**, **`task2.md`**, **`task3.md`**.

---

## Running everything

```bash
python3 task1_linkstate.py --verify
bash scenario.sh up                   # Task 2 - needs Docker
python3 bench.py --yours
python3 test_tasks.py
```

## What to submit

| File | From |
|---|---|
| `task1_linkstate.py` | your Dijkstra and forwarding table |
| `out/traceroute.txt` | domestic and overseas paths from your machine |
| `out/route-before.txt` · `out/route-after.txt` | the routers' tables either side of the cut |
| `out/reconverge.txt` | the measured reconvergence time |
| `task3_reconverge.py` · `out/bench.txt` | your router and its SPF count |
| `out/observation.md` | 2–3 lines per task |

```bash
python3 ../check.py w06
```

## Path (B) · when Docker will not run

Task 2 is the one that needs it. If Docker Desktop will not install on your
laptop, `task2.md` has a route that uses only `traceroute` and a classmate's
captured tables — it is weaker, and you have to say what it weakens.
Tasks 1 and 3 are pure Python and run anywhere.
