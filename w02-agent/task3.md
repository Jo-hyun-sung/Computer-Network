# Task 3 · Make It Wrong Less Often

**Theory** — §2.1 – §2.2
**Kind** — improvement · you are the thing being improved

---

## The baseline is your own Task 1

In Task 2 you counted: **N of M rows had something wrong**. That is your
baseline, and you produced it yourself with an agent driven by hand, one
instruction at a time.

Now change how you work and produce the table again. Same sources, same
columns, new setup. Then check it again by hand and report the new count.

## What "a better setup" means

Typing instructions one at a time worked for four RFCs. It does not work for
forty, and it is not repeatable — you cannot hand your prompt history to
somebody else and expect the same output.

Build something that persists instead. At minimum:

| # | Requirement |
|---|---|
| R1 | A written instruction file the agent reads every time — `AGENTS.md`, `CLAUDE.md`, or your harness's equivalent |
| R2 | It states the **rules that were broken** in Task 1. Yours, specifically, not generic advice |
| R3 | A verification step **the agent runs on itself** before claiming it is done |
| R4 | Repeat the collection and analysis with this setup → `out/analysis-2.md` |
| R5 | Hand-check it again → `out/verification-2.md`, ending with the new N of M |
| R6 | Copy the setup file into `out/` so it can be read with your submission |

R2 is the requirement that carries the task. "Be accurate" is not a rule. "Do not
write an RFC number unless you have opened that file in this session and seen the
number in its header" is a rule, because it can be broken visibly.

R3 is where this gets interesting: the agent cannot verify what it cannot check.
Work out which of your Task 2 checks it *can* do and which it structurally cannot.
That line is the useful finding of this lab.

## Grading

| | Requirement |
|---|---|
| pass | R1–R6, with both counts reported |
| good | the second count is lower than the first |
| **strong** | the second count is lower **and** you can name a class of error your setup cannot catch, with an example from your own output |

Note that "good" is not guaranteed. If your second count is the same or worse,
say so and explain why — an honest negative result with a diagnosis scores above
a number nobody can reproduce.

## What to write in `observation.md`

- Both counts, and what changed between them
- The rule in R2 that caught the most, and one that turned out to be useless
- R3: which of your checks the agent could run on itself, and which it could not.
  Why not?
- Is hallucination solved here, or have you just got better at finding it?
