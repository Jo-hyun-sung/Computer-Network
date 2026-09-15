# Task 1 · Subnets and Longest-Prefix Match

**File** — `task1_forward.py`
**Theory** — §4.3.2 CIDR addressing, §4.3.3 forwarding
**Kind** — implementation · fully offline

---

## What you are building

Two things every router does with every packet: work out which prefixes the
destination falls inside, and pick **the longest one**. That second rule is why
the internet's routing table can hold a million entries and still be answerable.

You build both from 32-bit integers up. **Do not use the `ipaddress` module** —
that library is exactly the thing you are meant to understand this week.

## Requirements

| # | Requirement |
|---|---|
| R1 | `parse_cidr` returns (network int, prefix length) and **rejects a prefix length outside 0–32** |
| R2 | `parse_cidr` rejects an address with host bits set — `163.152.6.5/24` is a host, not a network |
| R3 | `network_range` returns first usable, last usable, broadcast |
| R4 | `ForwardingTable.lookup` returns the next hop of the **longest** matching prefix |
| R5 | `0.0.0.0/0` matches everything and must lose to any other match |
| R6 | No `ipaddress`, no `socket.inet_aton`. Shifts and masks |

## The edge cases that matter

`/31` and `/30` have almost no room. `/32` has none at all. The textbook's "first
usable and last usable" language quietly assumes a prefix short enough to have a
middle — decide what you return for `/31` and `/32` and **say so in
`observation.md`**. There is more than one defensible answer and RFC 3021 picked one.

## Pass condition

```bash
python3 task1_forward.py --verify
```

Ten cases: four range computations and six lookups. The lookups are built so that
`10.20.30.70` sits inside **four** different entries at once — that is the case
longest-prefix match exists for.

```
  10/10 ok
```

## What to write in `observation.md`

- What you return for `/31` and `/32`, and why
- `10.20.30.70` matched four entries. List them, and say which rule picked the winner
- If two entries had the same prefix length and different next hops, what did you do?
