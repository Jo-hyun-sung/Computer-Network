# Task 1 · Collect the Sources

**Theory** — §2.1 – §2.2
**Kind** — tool use · the agent does the work, you direct it

---

## What you are producing

A folder of primary sources on HTTP and QUIC, and a table comparing them.
**You do not download anything by hand.** Directing the agent is the exercise.

## Step 1 · Somewhere to put it

Ask the agent to make a `materials/` folder inside `w02-agent/`.

## Step 2 · The sources

Give it an instruction of roughly this shape. Write your own wording — copying
this verbatim and copying it thoughtfully are different, and Task 3 will ask you
what your wording did.

```
> collect the specifications behind HTTP and QUIC into materials/
> - the RFCs for HTTP/1.1, HTTP/2, HTTP/3 and QUIC, full text
> - plus 2 or 3 papers or design documents on why QUIC was built
> - name them  rfc<number>_<short title>  and  author_year_title
> - write the list to out/source-list.md
```

It needs network access, so an approval prompt will appear. Read what it is
asking for before you approve it.

## Step 3 · The analysis

```
> read everything in materials/ and write out/analysis.md
> - one row per document: RFC number, year, problem solved, key mechanism, what it gave up
> - below the table, how the problem moved from HTTP/1.1 to HTTP/3
> - mark anything you could not confirm from the source text as (unverified)
> - do not cite an RFC number you did not open
```

## Requirements

| # | Requirement |
|---|---|
| R1 | `materials/` holds the **full text** of each source, not a summary page |
| R2 | `out/source-list.md` lists every file with where it came from |
| R3 | `out/analysis.md` has one row per document with all five columns |
| R4 | Items the agent could not confirm are marked, not quietly asserted |
| R5 | You approved each network access deliberately, and can say what each was for |

R1 matters more than it looks. Summary pages are easier to reach than RFC text,
and an agent that settles for one will produce an analysis that reads perfectly
and is built on nothing. Open two or three files and check what is in them.

## Pass condition

Both files exist and the table is complete.

```bash
python3 ../check.py w02
```

Format only. Whether the table is **true** is Task 2.

## What to write in `observation.md`

- What you actually typed, and one thing you would word differently next time
- Did it get the originals, or summary pages that were easier to reach?
