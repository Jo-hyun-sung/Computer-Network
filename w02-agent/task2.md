# Task 2 · Verify It Yourself

**Theory** — §2.1 – §2.2
**Kind** — **hands-on. The agent cannot do this one for you, and that is the point.**

---

## Why this task exists

Task 1 produced a table that reads perfectly. This task asks whether it is true.

You cannot delegate this. An agent checking its own work has the same blind
spots it had the first time, and asking a second agent gives you two confident
opinions rather than one fact.

## What to do

Take `out/analysis.md` row by row. For each row, **open the source file** and
confirm the claim against the text in front of you.

| # | Requirement |
|---|---|
| A1 | Every RFC number checked against the document that number actually names |
| A2 | Every year checked against the document's own date |
| A3 | Each "key mechanism" claim located in the source text — give the section number |
| A4 | Each "what it gave up" claim either located or marked unsupported |
| A5 | A count: **how many rows had at least one thing wrong?** Out of how many? |

A1 catches the failure that matters most. A file named `rfc9114_http3` may
contain something else entirely, and the agent will never know, because it named
the file itself.

## The count is the deliverable

Write `out/verification.md` with a table:

| Row | Claim checked | Correct? | Where you confirmed it |
|---|---|---|---|

and end with one line:

> **N of M rows contained at least one error.**

That number is what Task 3 tries to reduce. Without it, Task 3 has nothing to
measure against, so do not skip it or round it.

## Also compare against the lecture

You sat through 2-1 and 2-2 this week.

| # | Requirement |
|---|---|
| A6 | Does anything in the table **contradict a slide**? If so, which, and which is right? |

A6 is worth more than the rest. An agent contradicting your lecture quietly is
the exact failure you will not notice in a subject you do not know yet.

## Pass condition

`out/verification.md` exists, covers every row of `analysis.md`, and ends with
the N-of-M line.

## What to write in `observation.md`

- Your N of M
- The single worst error you found, and how you found it
- Would you have noticed it if you had not opened the source? Answer honestly
