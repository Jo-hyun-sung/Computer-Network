# Task 2 · On the Wire, and Does DNS Really Steer You?

**Files** — `task2_steering.py`, and a capture you take yourself
**Theory** — §2.4.3 DNS records, §2.5 Video streaming and CDNs
**Kind** — **hands-on. This one cannot be done from code alone.**

---

## Why this task exists

Tasks 1 and 3 are programs. You could write both without a network card.
This is a networking course, so one task each week makes you **look at the real thing**:
your own machine, your own traffic, your own two networks.

Nobody can hand you this capture. It has to come off your interface.

---

## Part A · Capture the exchange

Run Wireshark on the interface you actually use, with capture filter `port 53`,
then run your Task 1 resolver in another window.

```bash
python3 task1_resolve.py www.korea.ac.kr
```

Stop the capture and save as `out/dns.pcapng`.

| # | Requirement |
|---|---|
| A1 | The capture contains **your own** queries, taken on your machine |
| A2 | You can point to one query and its matching response, and read the transaction ID on both |
| A3 | You can point to a response that is a **delegation** (answer count 0, authority section with `NS`) and one that is an **answer** (`A` in the answer section) |
| A4 | Report the size in bytes of the largest DNS response you captured, and say what made it large |

A3 is the point of the whole exercise. In Task 1 you *inferred* the delegation from
parsed text. Here you see that a delegation and an answer are the **same packet format**
with different sections filled in.

> **Privacy** — a `port 53` capture records every name your machine looked up, which
> includes browser tabs and background apps. Before you submit, open the file and check.
> Close other applications first, or capture for a shorter window. If you cannot clean it,
> use path (B) below.

## Part B · Measure the steering

The lecture claims two things. One is easy to show and one is not:

- **(a)** most large sites are served by a CDN, reached through a `CNAME` chain
- **(b)** DNS steers each user to a *nearby* replica

Build the measurement over the 12 sites in `SITES` and the three resolvers in `RESOLVERS`.

| # | Requirement |
|---|---|
| B1 | For each site, follow the `CNAME` chain to its end and record every hop → `out/chains.json` |
| B2 | Ask **each resolver** for each site and record the address sets |
| B3 | Repeat from a **second network** — campus Wi-Fi and phone tethering, for example — and keep both results |
| B4 | Decide which sites are served by a **third party**, and write down the rule you used |
| B5 | Report: of N CDN-hosted sites, how many answered differently from a different resolver or network? |

B3 is the other part you cannot fake. Claim (b) is about *where you are*, so one
vantage point cannot test it.

### The hard part is B4

There is no single right rule.

| Site | What it does |
|---|---|
| `www.microsoft.com` | ends at `akamaiedge.net` — clearly a third party |
| `www.netflix.com` | stops inside `netflix.com` — runs its **own** CDN |
| `www.korea.ac.kr` | no `CNAME`, and no CDN either |
| some sites | sit behind a CDN with **no `CNAME` at all** (anycast) |

A rule that just compares the last two labels **will be wrong on at least one site in
the list.** Find which, and say so. Being wrong and knowing why scores better than a
rule that happens to work.

## Pass condition

`out/report.md` contains:

- the table: site · chain length · final zone · third party? · your rule's verdict
- the steering number from B5, with both networks named
- at least one site your rule got wrong, and why
- from Part A: the two packet numbers for A3, and the byte count for A4

```bash
python3 test_tasks.py        # checks the files exist and the capture is readable
```

The harness can check that your capture parses and that the report has its sections.
It cannot check that you understood the packets. That is what `observation.md` is for.

## Path (B) · If capture is blocked

Some campus and corporate networks block `dig +trace`, or outbound port 53 to public
resolvers, or you may not be able to install Wireshark.

- **Part A** — use the official **Wireshark Lab: DNS** trace in `traces/`. You lose
  "it is my own traffic", so instead answer: whose machine was this, and how can you tell?
- **Part B** — you still need two vantage points. If only one network is available,
  compare **two resolvers at very different distances** (a Korean ISP resolver and
  a US one) and say that is what you did, and what it weakens about your conclusion
- Source and attribution: `traces/README.md`

## What to write in `observation.md`

- The one-sentence difference between a delegation response and an answer response,
  written from what you saw in the capture rather than from the slide
- Your third-party rule, the site it got wrong, and why
- The steering number — and whether it supports claim (b) or not. It is allowed not to.
