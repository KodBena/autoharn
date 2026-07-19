# BACKLOG — retired as a file; the work tracker is the ledger

Audience: anyone who followed a link here

This repository's work tracking lives in its append-only Postgres ledger, not in this
file (maintainer ruling, 2026-07-12 afternoon, witnessed as tracker ledger row 137 —
`./led show 137` reads it: while the work is not yet in maintenance mode, the tracker
is maintained in local Postgres only; this file's only remaining job is to say where).
The coordinates, from this repository's own `deployment.json` (untracked; see
`deployment.json.example` + README.md "Configuration" for the field shape):

- database `toy` on this deployment's own `host`
- schema `autoharn` (kernel schema `autoharn_kernel`, role `autoharn_rw`)

To read it: `./pickup` at this repository's root shows the open set, in-force decisions,
and resources; `./led --recent` shows the latest rows; `./led show <id>` shows one row
in full. The ledger is the only liveness surface — nothing in any `.md` file, this one
included, says what is currently open or decided.

The 6,222-line dated narrative record this file carried until 2026-07-12 (the
"BACKLOG's dated tail" that other documents in this repository cite by entry name) is
preserved in git history, not deleted: read it with `git show d6f64ee:BACKLOG.md` (the
last commit carrying the full file). Those citations remain honest pointers into that
frozen record — the same declared-history standing the `judgment/` directory has. New
narrative goes into standalone committed documents (retrospectives, specs, incident
notes) cited by ledger rows, never into a growing file of unknown liveness — a 6k-line
markdown file where nobody can tell live from dust is the disease the SQL tracker
cures, which is exactly why this file retired.

<!-- doc-attest-exempt: pointer stub; the dated-record era it points at is point-in-time history -->

## Filed deferral, 2026-07-19 (ledger row 1810, tools/setup_tui residual item 4)

Filed HERE rather than as a `./led decision` row because this entry was written from an
isolated builder worktree with no `deployment.json` (no ledger access) — per ADR-0013 Rule 4
("a known defect is fixed or filed, never narrated-and-left") and ADR-0000's Exceptions
clause, a real defect gets a real disposition even when the preferred filing surface (the
ledger, per this file's own 2026-07-12 retirement notice above) is unreachable from where the
defect was found. **Migrate this to a `./led decision` row and delete this section the next
time someone with ledger access touches this area** — it does not belong here permanently.

- **The pair:** `design/FABLE-SETUP-TUI-SPEC.md`'s numbered flow list (items 1–11, "**Preflight**
  —", "**Substrate** —", … "**Checklist** —") duplicates, by hand, the ELEVEN-screen order
  `tools/setup_tui/screens.py`'s `SCREENS` list already declares once and derives
  `SCREEN_TITLES`/`SCREEN_NUMBER` from (see that file's own "Drift-proofing" comment above
  `SCREEN_TITLES`, ledger row 1790 finding 3, which fixed the SAME class of hazard for the
  banner/skip-detail strings but did not reach the spec's own prose list).
- **Current-accurate status:** WITNESSED accurate as of this filing — both lists agree, in
  order: Preflight, Substrate, Fork/target, Rehearsal, Birth, Principals & authority, Signed
  genesis, Boundary, Observability, Hydration, Checklist. Nothing is wrong today; the hazard
  is that nothing CHECKS this stays true the next time a screen is inserted, renamed, or
  reordered (exactly what already happened once, silently, to the banner/skip-detail strings
  before row 1790's fix) — nothing here is a live bug, it is an un-mechanized invariant.
  Editing the spec or building the fixture is explicitly OUT OF SCOPE for this filing (ledger
  row 1810 residual item 4: "FILE don't fix").
- **Candidate fixture shape:** a `seen-red/setup-tui-spec-flow-drift/run_fixtures.py` sibling
  to the existing `seen-red/setup-tui-class-vocabulary-drift/run_fixtures.py` (same real-vs-
  hand-mirror comparison shape, GREEN leg + two RED legs): parse `design/FABLE-SETUP-TUI-
  SPEC.md`'s numbered flow section with a small regex (`^\d+\.\s+\*\*([^*]+)\*\*\s+—`) into an
  ordered title list, and assert it equals `[SCREEN_TITLES[slug] for slug, _ in SCREENS]` from
  `tools.setup_tui.screens` (imported read-only). RED legs: a synthetic spec excerpt with one
  item removed, and one with two items swapped — both must read a mismatch. Zero residue (pure
  text parse + in-memory list compare, no filesystem mutation, no db state) — register it in
  `gates/fixture_census.py`'s `REGISTRY` once built.

