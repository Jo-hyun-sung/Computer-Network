# Task 1 · Build Your Own Iterative Resolver

**File** — `task1_resolve.py`
**Theory** — §2.4.2 DNS hierarchy, §2.4.3 DNS records
**Kind** — implementation · can be done entirely in code

---

## What you are building

`dig +trace` walks root → TLD → authoritative for you. In this task you do that walk
yourself: start at a root server, read the delegation it returns, ask the next server,
and keep going until somebody answers authoritatively.

You may shell out to `dig` for transport or use `dnspython` (it is in the container).
What matters is that **you** follow the delegations. The flag that stops a server from
doing the work for you is `+norecurse`:

```bash
dig @198.41.0.4 www.korea.ac.kr +norecurse
```

## Requirements

| # | Requirement |
|---|---|
| R1 | `Resolver.resolve(name)` returns `(address, path)` where `path` is the servers you asked, in order |
| R2 | You start at a root server in `ROOT_SERVERS`. No recursive query to anyone's resolver |
| R3 | Handle a delegation that arrives **without glue** — you must resolve the nameserver's own name first |
| R4 | Handle a server that does not answer: move to the next one rather than failing |
| R5 | Handle `CNAME`: if the answer is for a different name, restart the walk with that name |
| R6 | Cap the depth. A malformed zone must not hang you forever |

R3 and R6 are the ones people skip. R3 is where the recursion in "recursive resolver"
actually comes from.

## Pass condition

```bash
python3 task1_resolve.py --verify
```

Five names are resolved by your resolver and by `dig`, and the addresses must agree.

```
  ok    www.korea.ac.kr        you=163.152.6.10    dig=163.152.6.10   hops=3
```

A CDN-hosted name may legitimately return a different address on each query. If that is
what happened, that is not a failure — record it in `observation.md` and say why you know
the difference.

Run the whole week's checks with:

```bash
python3 test_tasks.py
```

## What to write in `observation.md`

- Why did the root server not simply hand you the address?
- What did you do when a delegation arrived **without glue**, and how many extra
  lookups did that cost you?
- How many servers did you end up asking for one name? Compare that with the single
  question your laptop normally asks its resolver.
