# Setup TUI — a guided, idiot-proofed path from nothing to a running world

<!-- doc-attest-exempt: build-basis spec; attestation rides witnessed delivery -->

**Status: Fable-authored 2026-07-18, build basis. Commission: ledger row 1656
(maintainer, verbatim there; the ask in one line: "so much to remember ... It's just
too much when you want to *just get started but still have a seriously robust
experience with claude code*"). Deliberately NOT freeze-gated: a `tools/` product,
no kernel/law/boundary-contract contact. The requirements document is the omega-lab
birth itself (rows 1655/1657 and the provisioner's report): every friction that pass
hit by hand is a screen here.**

## Posture (three rules that keep it honest)

1. **The TUI is a driver of existing verbs, never a second implementation.** Every
   action it takes is one of the scripts/verbs the repo already ships
   (`new-project.sh`, `teardown-world.sh`, `boundary_service`, `led`,
   `role_charter.py`); each screen shows the EXACT command it is about to run and
   streams that command's real output. If the TUI dies mid-flow, the operator can
   finish by hand from what the screen showed — no hidden state, no TUI-only path.
2. **Acts it cannot perform are prepared, not skipped.** Anything on the cluster
   host (pg_hba install, reload, createdb) becomes a copy-paste block with a
   what-you-should-see line, then a "press enter when done" gate that VERIFIES the
   effect (a live connection probe) rather than trusting the keypress.
3. **Checklist truth.** The end screen is a per-item WITNESSED/SKIPPED/PREPARED
   table of everything the flow touched — the same claims discipline as everywhere
   else, rendered for an operator.

## The flow (screens, in order; every screen skippable with the skip recorded)

**Feature-facts column (design/FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md, ledger row 1714,
built 2026-07-19):** every selectable act named below (substrate paths, boundary
service, observability's otelcol+watchdog, each hydration item, the preflight-probed
toolchains) now prints a facts line — the standards-conformance aspiration it serves
(with citation, or an honest "none named") and its external costs/dependencies (with
an honest "none") — from `tools/setup_tui/feature_facts.py`'s one-home registry,
shown at the point of selection, BEFORE the operator commits the act. Not repeated
per-screen below; see that spec for the registry and its drift backstop
(seen-red/setup-tui-feature-facts-drift).

1. **Preflight** — repo commit, submodules populated, `idris2`/`clingo`/`python3`/
   `psql` found (clingo non-fatal, matching `bootstrap/bootstrap.sh`'s own posture),
   reachable `HARNESS_PGHOST`, and (informational) whether `textual`/`urwid` are
   installed; each check green/red with the fix command.
2. **Substrate** — pick: existing-db path (zero manual steps, the omega-lab shape)
   or dedicated-db path (generates the confined pg_hba block in the live file's own
   idiom — reading the operator's real pg_hba copy first, per the standing
   config-fragments rule — plus the createdb/copy/reload block for the cluster
   host, then probes until the connection actually works).
3. **Fork/target** — destination directory (fresh dir, or fork-copy of an existing
   project with the CLAUDE.md-preservation move the omega-lab pass established).
4. **Rehearsal** — scratch-name birth + teardown + zero-residue check, streamed;
   the real birth is gated on rehearsal green (the ratified discipline).
5. **Birth** — `new-project.sh --new-world`, streamed; the maintainer copy-paste
   signing line surfaced prominently at the end.
6. **Boundary** — writes the multiplex TOML and the two deployment.json keys,
   picks a free port, starts the service (or emits the systemd-style unit text as
   a PREPARED block), probes `/health` and `/meta`.
7. **Observability** — otelcol start line (localhost-only, per standing config), the
   OTel model-provenance watchdog start line (`./otel-watch --daemon`,
   design/FABLE-OTEL-SENTRY-SPEC.md §3), and the Claude launch line with the right
   env vars, all as copy-paste blocks with what-you-should-see.
8. **Hydration** — fork provenance and role charters to register (via
   `role_charter.py`) stay as free-text prompts; a small, curated
   **durable-decisions catalog** (`tools/setup_tui/durable_decisions.py`, design/
   FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md §3, absorbing and retiring the old
   free-text `adr_corpus`/`makespan_pointer` items) offers standing rules distilled
   from this project's own ledger and the autoharn-panel deployment's, each writing
   a real `led decision` row on selection; an **ADR-adoption submenu**, DERIVED from
   `law/adr/*.md` at runtime (never a hand list), lets the operator adopt any subset
   by number and title. Every selected entry's fragment compiles into the new
   world's CLAUDE.md between generated-section markers (idempotent, fork-
   destination-safe — never touches bytes outside the markers). Kernel `obligate`
   rows are explicitly out of v1 (the catalog itself encodes the reason as one of
   its own entries, ledger row 1640).
9. **Checklist** — the witnessed/skipped/prepared table; offer to save it into the
   new world as a dated file.

## v1 boundaries, named

Python + textual/urwid-class library ONLY if already installed — otherwise plain
curses/prompt-toolkit-free numbered-menu fallback so the tool has zero new
dependencies (the builder states which was available and used). No daemon
management beyond emitting unit text (PREPARED). No editing of the operator's real
pg_hba in place — it generates the block and the diff, the operator applies. No
teardown flows in v1 beyond the rehearsal's own (destroying real worlds stays a
deliberate, separate act). The TUI writes nothing to any ledger except through
`led`, and nothing anywhere except the target directory and its own saved
checklist.

## Witnesses

- **WT1** full existing-db flow end-to-end on a scratch destination against db
  toy: rehearsal, birth, boundary probe, one hydration row, checklist accurate
  per item; then torn down, zero residue.
- **WT2** preflight red path: a missing prerequisite renders red with the fix
  command (witness at least one for real, e.g. an unset HARNESS_PGHOST).
- **WT3** prepared-act verification: the "press enter when done" gate re-probes
  and REFUSES to advance when the operator lies (witness by not doing the act).
- **WT4** mid-flow death: kill the TUI after birth, verify the world is usable by
  hand from the streamed commands alone (rule 1 made real).
- **WT5** dedicated-db path: pg_hba block generated in the live file's idiom from
  a copy of the operator's real file — PREPARED-level witness (the cluster-host
  apply is the operator's act; do not fake it).

## Amendment — 2026-07-19: out-of-sequence entry demands self-validated preconditions

The findings-RCA on the fix-point rounds classified one finding as this spec's own
gap: the flow section describes screens 1–9 in order, but the tool (correctly)
supports entering a screen out of sequence (`--start-at`, or an explicit gate
override), and nothing here said what that obligates. The rule, binding on every
screen present and future: **a screen entered out of its normal sequence must
independently validate every precondition the normal sequence would have
established for it, and refuse legibly (a REFUSED checklist entry with teaching,
never a traceback) when one is missing.** The boundary screen's
nonexistent-destination crash was the witnessed specimen; its repair is this rule's
first instance, not a one-off.

## Amendment — 2026-07-19: `--dry-run`, the nondestructive rehearsal of the whole flow

Commission: ledger row 1719 (maintainer, verbatim there; the ask in one line: a
nondestructive option showing at the end what would have been done, "so I don't
mess up any directory by mistake"). The rule, binding on every screen present and
future:

- Under `--dry-run`, the TUI performs NO destructive or externally visible act:
  no file created or modified outside its own process-private temp space, no
  database act of any kind, no `led` write, no process started, no port bound.
  Read-only probes (preflight checks, connection probes, reading the operator's
  pg_hba copy, globbing `law/adr/`) remain live — a dry run that fakes its reads
  is a lie, not a rehearsal.
- Every screen computes its would-be acts anyway and records them: the EXACT
  command argv it would run (rule 1's show-the-command discipline, unchanged),
  the exact file paths it would write with a one-line content summary each, and
  the ledger rows it would write verbatim. The end screen renders these as a
  **WOULD-DO table** — the dry-run counterpart of the witnessed checklist, same
  per-item discipline, item status `WOULD-DO` instead of `WITNESSED`.
- PREPARED blocks (cluster-host copy-paste acts) are displayed as normal — they
  were already nondestructive — but their "press enter when done" verification
  gates are skipped and recorded as `DRY-SKIPPED`, never silently passed.
- `--dry-run` composes with `--scripted` and `--start-at`; the out-of-sequence
  amendment binds unchanged (a dry run validates every precondition it can
  check read-only and records honestly as `DRY-SKIPPED` any it cannot).
- Witnesses for the build that delivers this: **WDR1** a full dry-run flow
  against a real destination directory leaves the filesystem byte-identical
  (before/after tree hash compared mechanically) and writes zero ledger rows;
  **WDR2** parity — on the scripted happy path, the WOULD-DO table's argv list
  equals the argv list a real scratch run actually executes (compared
  mechanically, order included); **WDR3** a dry run that reaches a refusal
  (hostile input) refuses identically to the live path — validation is never
  weakened by dry-run.

## Build conditions

Lives under `tools/setup_tui/`; no lazy imports; gates apply; no edits to
bootstrap scripts, kernel, law, serving; witnesses on scratch only.
