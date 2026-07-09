# HANDOFF — session 59c83ca6 → next (2026-07-09)

Orientation: read CLAUDE.md fully (tone: lagom, no unearned confidence; mother's-life bar;
read law/ ADRs IN FULL before work that invokes them — 0000/0013 especially: never recommend
de-scoping mandated work, verify artifacts not claims). GLOSSARY.md has the vocabulary;
CAPABILITIES.md (new) says what's witnessed vs built-unexercised, plainly.

## State: maintainer is standing up Use-mode on a toy project (`../toy-project`, terminal-color
preference optimization), db `toy`, schema `toycolors`(theirs: `toy`), kern `toy_kernel`, role `toy_rw`.

Done this session (all UNCOMMITTED; new root docs trip gates/layout_census.py allowlist — registration pending):
- DIRCLASS.md — top-level dirs classed CORE/DOC/RESEARCH/OTHER (drive/ = RESEARCH, study apparatus).
- WALKTHROUGH.md — rewritten lean; commands verified; watermark apply witnessed GREEN by maintainer.
- kernel/lineage/high_watermark_1.sql — derived \ir chain (s15→s17-stamp→s17-independence→s19),
  deliberately EXCLUDES s18 (project-internal experiment fixture, per maintainer). README updated.
- CAPABILITIES.md — plain-language accountability summary, grounded in BRIEF-CONFORMANCE-MAP.md.
- BACKLOG.md tail — filed: validate_* triggers resolve ledger via SESSION search_path and
  SET ROLE voids s19's login-default premise (masked by explicit SET in docs; fix = future sNN
  delta adding per-function SET search_path). Needs maintainer ruling.
- design/refgraph/ — SSOT schema (SCHEMA.md + schema.json) for a reference graph; deterministic
  extractor+compiler in scratchpad; Sonnet enrichment ran (17 agents, results in task
  wefdf2pva output). NOT merged/compiled yet. Schema gap noted: needs a `requires` edge type
  (DDL builds-on), vestigial_reason if/then. Ephemera NOT yet persisted (filing/persist_claude_ephemera.py — owed).

## Accepted next job (maintainer said the hooks are the point):
Wire Use-mode hooks to toy-project: (1) adapt hooks/pretooluse_change_gate.py off the experiment
schema onto the toy ledger + PreToolUse in toy-project/.claude/settings.json; (2) stamp
interceptor likewise (stamps make independence checks real); (3) a small `led` helper for
one-liner ledger entries. PENDING maintainer decision: governed file set (default: all *.py, class-keyed).
Review fix-point on a user project = new ground, be honest about it.

## Hard-won facts (don't relearn):
- Kernel: ONE row per INSERT (trigger); SET search_path REQUIRED for linked rows; pass every -v
  var (defaults point at LIVE deployment: public/vsr_rw/qbx_*  — never apply bare).
- pg_hba admits only registered dbs from this host; createdb runs on the DB host.
- DB writes to harness may be permission-denied; ask, don't route around.
- Findings 49/50 (engine tests) reproduce; 6 findings OPEN in harness.finding_open.
