# Week 3 Lab · DNS Hierarchy and CDNs

**Theory** — 3-1 DNS hierarchy (§2.4.2) · 3-2 DNS records (§2.4.3) · 3-2 Video streaming and CDNs (§2.5)
**Textbook lab (path B)** — Wireshark Lab: DNS
**Submit to** — `w03-dns/out/`

You type a name and an address comes back. Three questions this week:
**who actually answered, whose machine is it, and how long may we keep the answer?**

```bash
cd w03-dns
```

| | Task | You build |
|---|---|---|
| 1 | Resolve a name yourself | an iterative resolver — no `dig +trace` |
| 2 | Does DNS really steer you? | a measurement over 12 sites and three resolvers |
| 3 | Beat the baseline cache | a correct cache, and an argument about its floor |

---

## Task 1 · Build Your Own Iterative Resolver

`task1_resolve.py`

`dig +trace` walks root → TLD → authoritative for you. Do that walk yourself:
start at a root server, read the delegation, ask the next server, repeat until
someone answers authoritatively.

You may shell out to `dig` for transport (`+norecurse` is the flag that stops a
server from doing the work for you) or use `dnspython`. What matters is that
**you** follow the delegations.

What will actually get in your way:

- a delegation gives you `NS` **names**, sometimes with glue `A` records and sometimes without.
  No glue means you have to resolve *that* name first — another walk. Decide what you do there
- servers that do not answer. Try the next one
- `CNAME`s: the answer may be for a different name than the one you asked, and you start again
- loops. Cap your depth

**Pass condition**

```bash
python3 task1_resolve.py --verify
```

Five names, resolved by you and by `dig`, must agree. CDN names can legitimately
return a different address per query — if that is what happened, say so in `observation.md`.

---

## Task 2 · Does DNS Actually Steer You?

`task2_steering.py`

The lecture claims two things. One is easy to show and one is not:

- **(a)** most large sites are served by a CDN, reached through a `CNAME` chain
- **(b)** DNS steers each user to a *nearby* replica

Build the measurement over the 12 sites in `SITES` and the three resolvers in `RESOLVERS`.

**The hard part is deciding what counts as "served by a third party."**
There is no single right rule.

| Site | What it does |
|---|---|
| `www.microsoft.com` | ends at `akamaiedge.net` — clearly a third party |
| `www.netflix.com` | stops inside `netflix.com` — runs its **own** CDN |
| `www.korea.ac.kr` | no `CNAME` at all, and no CDN either |
| some sites | sit behind a CDN with no `CNAME` at all (anycast) |

A rule that just compares the last two labels **will be wrong on at least one site
in the list.** Find which one, and say so.

**Pass condition** — `out/report.md` contains:

- the table: site · chain length · final zone · third party? · your rule's verdict
- the steering number: "X of N sites answered differently to a different resolver"
- at least one site your rule got wrong, and why

---

## Task 3 · Beat the Baseline Cache

`task3_cache.py` · harness `bench.py` — **do not edit the harness**

`BaselineCache` works. It is also bad in more than one way, and one of its problems
is worse than being slow.

```bash
python3 bench.py            # baseline only
python3 bench.py --yours    # side by side, once you have written YourCache
```

The harness replays 1,000 queries over a simulated hour against a simulated upstream
(fixed 20 ms round trip, a fixture of names with realistic TTLs from 20 s to a day),
so everyone's numbers are comparable and slow Wi-Fi does not decide your grade.

**Where the baseline lands:**

```
  baseline   upstream   325   hit rate  67.5%   stale  266   sim time    6.5s
```

Read that line carefully. The hit rate looks respectable. **266 of 1,000 answers were
expired** — the cache handed out records whose TTL had already run out. A cache that keeps
everything forever would score a beautiful hit rate and be completely wrong.

| | Requirement |
|---|---|
| pass | zero stale answers |
| good | zero stale, and no more upstream queries than the baseline |
| **strong** | the above, plus: **how few upstream queries could any correct cache make on this workload, and why can you not go below that?** |

The last row is the real question, and it is worth reading before you start optimising —
it tells you where to stop. A correct cache does not get to be clever about this.

---

## Path (B) · When Measurement Is Blocked

Some campus and corporate networks block `dig +trace`, or outbound port 53 to public resolvers.

- **Task 1** — use the official **Wireshark Lab: DNS** trace in `traces/` and reconstruct the
  delegation chain by reading the captured queries instead of issuing your own
- **Task 2** — you need at least two resolvers for the steering number. If only one is
  reachable, measure from two different networks instead (campus and phone tethering), and say so
- **Task 3** — unaffected. It is fully simulated
- Source and attribution: `traces/README.md`

---

## What to Submit

| File | What |
|---|---|
| `task1_resolve.py` | your resolver |
| `task2_steering.py` · `out/report.md` | your measurement and its table |
| `task3_cache.py` | your cache |
| `out/bench.txt` | output of `python3 bench.py --yours` |
| `out/observation.md` | 2–3 lines per task, see below |

```bash
python3 ../check.py w03
```

This checks **format only**. It does not grade your answers; it tells you what is missing.

## What to Write in `observation.md`

- **Task 1** — why the root server did not just hand you the address. And: what did you do
  when a delegation arrived without glue?
- **Task 2** — your third-party rule, the site it got wrong, and the steering number
- **Task 3** — the floor. How few upstream queries could a correct cache make here, and why
