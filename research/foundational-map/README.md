# Foundational map — claude_harness / autoharn

_Generated 2026-06-27 by a 10-reader parallel workflow over `chocofarm` and `omega`, run `wf_64eb31fd-6c9`._

> **Vocabulary:** coined terms (Pillar, intent SSOT, Mechanization Discipline, …) are defined in the root **[GLOSSARY.md](../../GLOSSARY.md)** and linked on first use; you should never have to grep to learn a term.

This directory is the **evidence base** for the harness design: a high-fidelity map of
the maintainer's existing ADR disciplines, the SQL/lint mechanisms already in use, the
benchmark-attribution gap, and the tool/intent surface — read so the harness grows *out of*
the existing conventions instead of imposing foreign ones.

## Contents

- **[00-synthesis.md](00-synthesis.md)** — the integrated design seed (three pillars, invariants, sequencing, open questions). **Start here.**

- [01-choco-adr-0011-mechanization.md](01-choco-adr-0011-mechanization.md) — choco/ADR-0011-mechanization (chocofarm's "Mechanization Discipline" tenet — the harness north star)
- [02-omega-adr-0011-mechanization-discipline.md](02-omega-adr-0011-mechanization-discipline.md) — omega/ADR-0011 Mechanization Discipline (vs chocofarm fork) + meta-review cadence
- [03-choco-typing-classification-logic.md](03-choco-typing-classification-logic.md) — choco / typing + classification-logic (ADR-0008 + ADR-0000) — the philosophical root for the harness LOGIC layer (classical + non-classical)
- [04-chocofarm-perf-investigation-discipline.md](04-chocofarm-perf-investigation-discipline.md) — chocofarm perf-investigation discipline (ADR-0009) + execution stamina (ADR-0013) + executor second-opinion (ADR-0014), and the throughput_research provenance DB that already mechanizes part of ADR-0009
- [05-omega-adr-0009-performance-investigation-discipline.md](05-omega-adr-0009-performance-investigation-discipline.md) — omega/ADR-0009 Performance Investigation Discipline — perf-number provenance/attribution (harness Pillar 2)
- [06-omega-work-status-sql-anti-corruption-layer.md](06-omega-work-status-sql-anti-corruption-layer.md) — omega / work-status SQL anti-corruption layer (the key precedent for the harness's SQL layer)
- [07-omega-existing-lint-gates.md](07-omega-existing-lint-gates.md) — omega/existing-lint-gates
- [08-cross-benchmark-attribution-today.md](08-cross-benchmark-attribution-today.md) — cross/benchmark-attribution-today (Pillar 2 — provenance/accountability ledger)
- [09-cross-memories-and-resource-facts.md](09-cross-memories-and-resource-facts.md) — cross/memories-and-resource-facts — Claude memory dirs vs. queryable resource registry (motivating Pillar 1 "pull not push")
- [10-choco-tool-venv-surface.md](10-choco-tool-venv-surface.md) — choco/tool-venv-surface — chocofarm's tool / venv / capability surface (Pillar 1; authored directly after the structured-output reader hit its retry cap twice)

## Provenance & integrity

- Source: structured output of the `claude-harness-understand` workflow (model claude-opus-4-8[1m]), 2026-06-27.
- Reports 01–09 are verbatim structured agent output; anchors cite `file:line/section` in the source projects.
- **Report 10 is hand-authored**, not workflow output: the `choco/tool-venv-surface` reader (Z3/OR-Tools/
  venv inventory for Pillar 1) exceeded its structured-output retry cap on BOTH the original run and a
  dedicated backfill run (`wf_ead2d79d-647`). The inventory was gathered directly (verified venv imports +
  a grep use-site census, 2026-06-27) and written in the same schema; its footer says so.

## On machine-local detail

These reports cite real resource topology (hosts, ports, venv paths) drawn from
`omega/services_local.gitignore`. Published deliberately and full-fidelity, per the maintainer's call:
the existence of a Redis/Postgres on a private RFC-1918 address is low-sensitivity (≈ "this machine has
an ethernet port"). The one genuinely sensitive class the maintainer redacts — directory structure /
suspected-cheater data in the Go project — does **not** appear in any of these reports (they cover ADR
disciplines, perf rigor, the work-status *todo* SQL, and lint gates). Volatile facts (e.g. the X11 cookie
host) are cited as *derivations to run*, never as literals.
