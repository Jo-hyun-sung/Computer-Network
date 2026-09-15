# Task 2 · Where Exactly Are You on the Internet?

**Files** — `task2_myaddr.py`, and a capture you take yourself
**Theory** — §4.3.2 addressing and DHCP, §4.3.3 NAT
**Kind** — **hands-on. This one cannot be done from code alone.**

---

## Why this task exists

Task 1 and Task 3 are arithmetic. This one is about the address **your machine
actually holds right now**, which nobody else has and which will be different
tomorrow.

## Part A · Your address, by hand

```bash
python3 task2_myaddr.py --collect "campus wifi"
```

The script dumps raw `ifconfig` / `ip addr` / `ipconfig` output and asks the
outside world what address it sees. **It deliberately does not parse any of it.**

| # | Requirement |
|---|---|
| A1 | Your interface address and mask, read off the raw output yourself |
| A2 | The subnet's range, **computed by hand**, then checked against your Task 1 `network_range` |
| A3 | Your default gateway, and whether it is inside that range. Say why it has to be |
| A4 | The public address the outside world saw |
| A5 | Is A1 private (RFC 1918) and A4 public? If they differ, **how many layers of NAT** are you behind — and how would you tell the difference between one and two? |

A5 is the real question. If A1 is `10.x` and A4 is something else, there is at
least one NAT. If A1 is `100.64.x` you have found carrier-grade NAT and there are
two. Mobile networks often do this; campus networks sometimes do.

## Part B · Two networks

Run `--collect` again with a different label on a **different network** —
phone tethering is the easy one.

| # | Requirement |
|---|---|
| B1 | Two labelled records in `out/addresses.json` |
| B2 | Compare the two: private address, mask, gateway, public address |
| B3 | Did the **public** address change? Did the **private** one? Explain both |

## Part C · Catch DHCP in the act

A DHCP exchange happens when you **join** a network, so you have to catch it.
Start Wireshark with capture filter `port 67 or port 68`, then disconnect and
reconnect your Wi-Fi.

| # | Requirement |
|---|---|
| C1 | `out/dhcp.pcapng` contains the four messages: Discover, Offer, Request, Ack |
| C2 | Report the source and destination addresses of **Discover**. One of them is strange — say why it has to be that |
| C3 | Report the **lease time** the server offered |
| C4 | Discover is broadcast, Ack may not be. Say what changed between them that makes that possible |

C2 is the point. The client has no address yet, and it is asking for one. Look at
what it puts in the source field, and what that forces about the destination.

## Pass condition

`out/addresses.json` has two labels, `out/dhcp.pcapng` contains DORA, and
`out/report.md` answers A2–A5, B3, C2–C4.

```bash
python3 test_tasks.py --task 2
```

## Path (B) · if capture is blocked

- **Part C** — use the official **DHCP trace** in `traces/`. Answer C2–C4 from it,
  and add: how long was that lease, and what happens at half of it?
- **Parts A and B** still need your own machine. There is no substitute — if you
  genuinely cannot get a second network, say so and compare with a classmate's
  numbers instead, naming whose they are

## What to write in `observation.md`

- How many NATs you are behind, and the evidence
- What changed and what did not between your two networks, and why
- The Discover source address, and why it could not be anything else
