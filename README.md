# Computer Networks · Labs

2026-2 · Korea University Sejong · **Weeks 2 – 7**

This is the lab repository. Clone it and work inside it.

```bash
git clone https://github.com/codingchild2424/2026-lecture-network-practice.git
cd 2026-lecture-network-practice
```

The slides live separately and link here week by week.

---

## The weeks

| Week | Folder | Subject |
|---|---|---|
| 2 | `w02-agent/` | working with a coding agent |
| 3 | `w03-dns/` | DNS hierarchy and CDNs |
| 4 | `w04-tcp/` | reliability, measurement, congestion |
| 5 | `w05-ip-nat/` | addresses, subnets, NAT, DHCP |
| 6 | `w06-routing/` | routing and reconvergence |
| 7 | `w07-ethernet-arp/` | Ethernet, ARP and switching |

Weeks 9 – 15 are the project. There are no folders for them here.

## How a week works

Every folder holds the same things:

```
wNN-topic/
├── README.md        what the week is about, and the three tasks
├── task1.md         one task, its requirements, its pass condition
├── task2.md
├── task3.md
├── task1_*.py       the code you write
├── task2_*.py
├── task3_*.py
├── bench.py         the measuring harness for task 3 - do not edit it
└── test_tasks.py    run this before you submit
```

**Three tasks a week**, and they are different in kind:

| | |
|---|---|
| **Task 1 · implementation** | build the mechanism yourself. The tool that normally does it is not allowed |
| **Task 2 · measurement** | your own machine, your own traffic, your own two networks. **This is the one nobody can do for you** |
| **Task 3 · improvement** | a deliberately bad implementation is committed here. Beat it, measured by `bench.py` |

There is no separate assignment. **The three tasks are the assignment.**

## Submitting

Put everything under that week's `out/`. Then:

```bash
python3 test_tasks.py         # does it pass?
python3 ../check.py w03       # is anything missing?
```

`test_tasks.py` runs your code and checks it against a reference where one exists.
`check.py` only looks for files. Neither of them can tell whether you understood
anything, which is what `out/observation.md` is for — **2 to 3 lines per task**,
and it is the centre of the grade. A capture file proves you ran a tool. It does
not prove you read what came back.

---

## Running environment

### Recommended · the container

One container instead of installing twelve tools, and everybody gets the same
output from `dig` and `iperf3`.

```bash
# with Docker Desktop installed (Windows and macOS alike)
cd 2026-lecture-network-practice
docker compose build
docker compose run --rm lab        # an Ubuntu shell
```

Inside: `tshark` `tcpdump` `dig` `curl` `traceroute` `mtr` `iperf3` `python3`
`jq` `ipcalc`.

### Capture on the host

The container cannot see your laptop's network card — on macOS especially, since
it runs inside a Linux VM.

- **capture** with Wireshark on the host
- **analyse** by putting the file in `wNN-*/out/` and running `tshark -r` in the container

### If you cannot run Docker

Nothing here is blocked by that. Tasks 1 and 3 are pure Python everywhere. Task 2
has a **path (B)** in every week, using the textbook authors' published traces —
see `traces/README.md`. Path (B) is weaker, and each week's `task2.md` says
exactly what it weakens and what you have to write instead.

---

## Measurement ethics

This course handles packets. Breaking any of these is not a lab, it is an incident.

- Measure **only networks and devices you are authorised to use**
- Do not intercept anyone else's traffic, and do not capture wireless you do not own
- Do not run load tests against university infrastructure
- **Check your captures for other people's data before submitting.** A `port 53`
  or `port 443` capture records every site your machine touched, including
  background applications. Close what you can, capture briefly, and look at the
  file before you hand it in

If a capture caught someone's personal data, delete it and take it again. If you
cannot clean it, switch to path (B).

## Grading

Part of the 10% participation score. Each week is small, which makes it easy to
skip. The observation write-up is the centre of it.
