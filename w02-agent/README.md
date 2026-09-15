# Week 2 Lab · Working With a Coding Agent

**Theory** — 2-1 · 2-2 Application layer and HTTP (§2.1 – §2.2)
**Prerequisite** — the agent you installed in **2-3**, this same week. Codex, Claude Code, either
**Submit to** — `w02-agent/out/`

This is the only lab in the course where the subject is the tool rather than the
network. Every later week assumes you have it and can drive it.

The material is **this week's topic** — the RFCs and papers behind HTTP and QUIC —
so you are learning the tool on something you will be examined on anyway.

```bash
cd w02-agent
```

| | Task | You produce |
|---|---|---|
| 1 | Collect the sources | a `materials/` folder and a source list, gathered by the agent |
| 2 | Verify it yourself | a count of how often the agent was wrong, checked by hand |
| 3 | Make it wrong less often | a better working setup, and the same count again |

Details and requirements are in **`task1.md`**, **`task2.md`**, **`task3.md`**.

Point your agent's project folder at **this directory**. It does not need to see
the rest of the repository, and it will behave better if it cannot.

## What to submit

| File | From |
|---|---|
| `out/source-list.md` | what the agent collected |
| `out/analysis.md` | its comparison table |
| `out/verification.md` | your hand check, with the count |
| `out/AGENTS.md` or equivalent | the setup you built in Task 3 |
| `out/verification-2.md` | the count after your changes |
| `out/observation.md` | 2–3 lines per task |

```bash
python3 ../check.py w02
```

## A warning about this week

The agent will produce something that looks finished very quickly. Task 2 exists
because looking finished and being right are different properties, and the whole
point of this lab is to find out how different.
