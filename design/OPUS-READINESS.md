# OPUS-READINESS — the simplification spec (2026-07-09)

Status: DESIGN, Fable-authored (session be693afb), grounded in evidence, awaiting maintainer
ratification. Purpose: make this repo orchestratable by Opus (and usable by Sonnet executors)
without Fable in the loop, WITHOUT lowering the product quality bar (NRC/aviation-adoptable
product, best-effort process — maintainer ruling 2026-07-09). The maintainer's finding this
spec answers: the repo as it stands is beyond Opus's ability to hold — so the fix is not a
smarter orchestrator, it is a repo whose safe-operation surface is small, mechanical, and
self-teaching.

Evidence base (all from the 2026-07-09 toy-pilot day): the hooks-wiring friction log (8
items), the countersign friction log, the full-surface exercise report (9-item verdict table,
2 kernel defects), the kernel capability-vs-exposure audit (26-row table), the engine
reconnaissance, and the maintainer rulings logged in BACKLOG.md and memory.

## The organizing principle

**The gates carry the intelligence; the orchestrator does not have to.** Opus fails here when
correctness depends on it *knowing* things (which -v vars, which schema names, what "applied
in full" means). Opus succeeds when every wrong move it can make is refused loudly by a
mechanism that tells it the fix (the deny→led→retry loop already witnessed working — an agent
that has never seen the apparatus completes the loop because the refusal teaches it). So the
program is: shrink what an orchestrator must know to near zero, and convert every
must-not-get-wrong into a gate that refuses-and-teaches. This is ADR-0011 applied to the
orchestration layer itself.

## The five moves (priority order)

### 1. One deployment record, everywhere (foreclose the names class)
The single largest friction source: db/schema/kern/role names re-authored in N places
(engine _SPECIAL dicts, `kernel.principal` literal, led defaults, settings.json env,
E13_* gate env, WALKTHROUGH -v vars). `engine/targets.py` (landing now) is the first home;
finish the class:
- The kernel APPLY step emits a machine-readable deployment record (`deployment.json`:
  db/schema/kern/role/host, written next to the project's .claude/) — the walkthrough stops
  being the only carrier of the names.
- led, judge, the hooks, and the engine registry all READ that record; env vars become
  overrides, not the primary interface. Neutral names (the E13_* experiment prefix dies).
- A project with no deployment record gets a loud, teaching refusal from every tool.
Opus impact: "point the apparatus at a project" stops requiring five undocumented env vars
(friction item 1) and a DB-inspection round to resolve name splits (friction item 2).

### 2. One project config; instance/template split made physical
- `.claude/apparatus.json` (or fold into deployment.json): governed-file patterns, deny-hint
  text, assurance level. The per-project choice surface in ONE user-editable file — the
  maintainer's ergonomics ruling ("someone using this project should have no ergonomic
  problem selecting what they want").
- **Assurance levels as configuration** (the DO-178C DAL move, maintainer-endorsed): a level
  field selects which gates enforce vs observe (census off here, on for a power-plant
  instance; review independence required or not; engine observer vs gating). The
  bureaucracy-is-conditionally-due ruling becomes structure, not ad-hoc toggling.
- **Scaffold, not clone**: a `bootstrap/new-project.sh` that stamps a new instance (config +
  led + judge + hooks wiring + HOOKS.md template with UNWITNESSED marks) — the
  template/instance separation that dissolves the dev-vs-use branch confusion structurally.
  toy-project's .claude/ is the worked prototype; the scaffold generalizes it.

### 3. The operator/orchestrator surface is exactly three verbs
`led` (speak to the ledger — full kernel vocabulary, landed today), `judge` (run the deductive
engine, observer-first — landing per USE-MODE-ENGINE-WIRING.md), and the scaffold. Everything
else is hooks (automatic) or gates (refusals). An Opus orchestrating a user project needs to
know: edits to governed files need a led entry; judge tells you what the ledger's logic says;
refusals teach the fix. That is the WHOLE required model. Docs follow the doc-witness
discipline (every example carries observed output or UNWITNESSED — BACKLOG-filed, exercised
in HOOKS.md today), so the docs Opus reads cannot silently lie about what was never run.

### 4. The law gets a mechanical enforcement companion
The ADR corpus is the part Opus demonstrably cannot hold (it is subtle, long, and
spirit-over-letter by design). Do not ask it to. Instead:
- The Rule-3 demurral-detector hook (BACKLOG-filed, maintainer-proposed): catches the
  cop-out/attrition shapes mechanically at Stop/AskUserQuestion time.
- The commission/result-conformance instrument ADR-0013 R1 names: an Opus-run task carries a
  structured commission (scope list); the result is diffed against it mechanically. Opus's
  known failure mode (confident narrowing) becomes a gate refusal instead of a maintainer
  discovery.
- CLAUDE.md gains a short ORCHESTRATION section: the standing delegation contract (Sonnet
  executes; Opus only multi-boundary unambiguous specs; neither touches kernel lineage, law/,
  or engine ASP semantics without a Fable-authored spec). Written for the orchestrator that
  cannot infer it.

### 5. Cut and quarantine (what Opus must never need to read)
- RESEARCH/DOC trees (judgment/, drive/, design/ archives, e-series) are already classed in
  DIRCLASS.md; add a one-line pointer in CLAUDE.md: "operational truth lives in CAPABILITIES.md
  + the three verbs; judgment/ and design/ are history unless a spec cites them." Opus's
  context budget goes to the operational surface only.
- refgraph: condemned and reverted (done today).
- The engine's five .lp programs stay Fable/maintainer territory (grayhairs ruling: the engine
  is the POINT — it gets wired IN, per USE-MODE-ENGINE-WIRING.md, but its semantics are not
  Opus-editable; judge's closed verdict vocabulary is the interface).

## What is deliberately NOT simplified
The kernel lineage (frozen, constitutional), the law corpus (spirit-bearing; gets a mechanical
companion, not a rewrite), the engine ASP programs (the raison d'être), the append-only and
SoD invariants (witnessed today at two layers; they are the product). Simplification here
means shrinking the REQUIRED-KNOWLEDGE surface, never the guarantee surface.

## Sequencing (Sonnet-executable after ratification)
1. deployment.json emission + consumers (move 1) — mechanical, spec above.
2. apparatus.json + assurance levels + scaffold (move 2).
3. ORCHESTRATION section + commission/conformance instrument (move 4) — the instrument is the
   one design-heavy item; Fable reviews its schema, Sonnet builds it.
4. Demurral-detector hook (BACKLOG spec exists; corpus fix-point is a cheap Haiku loop).
5. CLAUDE.md pointer + CAPABILITIES.md refresh (move 5).
Each lands independently; nothing blocks the toy pilot continuing meanwhile.
