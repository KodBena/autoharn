"""tools/setup_tui -- the guided setup wizard (design/FABLE-SETUP-TUI-SPEC.md, commission
ledger row 1656, spec row 1671; wholesale rebuilt 2026-07-22 per
design/FABLE-SETUP-TUI-REBUILD-SPEC.md).

Three honesty rules this whole package is built to (spec "Posture") -- unchanged by the rebuild,
only the UI carrying them changed:
  1. Driver-only: every action is one of the repo's existing verbs/scripts
     (bootstrap/new-project.sh, bootstrap/teardown-world.sh, serving.boundary_service, led,
     tools/role_charter.py). Every section shows the EXACT command it is about to run, and the
     commit boundary streams that command's real, unedited output. If the TUI dies mid-flow, the
     operator can finish by hand from what was shown.
  2. Prepared, not skipped: an act this process cannot itself perform (anything on the cluster
     host -- pg_hba install, reload, createdb) is rendered as a copy-paste block plus a
     what-you-should-see line, then a gate that VERIFIES the effect with a live probe rather
     than trusting the operator's keypress.
  3. Checklist truth: the commit node's own output is a per-item WITNESSED/SKIPPED/PREPARED
     table of everything the flow touched.

v1 boundaries (spec, named): no daemon management beyond emitting unit text (PREPARED); no
in-place pg_hba edits (this package only ever reads the live file to generate a block --
applying it is always the operator's own act); no teardown flows beyond the rehearsal's own;
writes nothing to any ledger except through `led`; writes nothing anywhere except the target
directory and its own saved checklist.

`--dry-run`: the SAME ten sections, but no destructive or externally visible act --
`tools/setup_tui/runner.py`'s three act-execution choke points (`run_command`,
`start_background`, `write_file`) and `checklist.status_for`/`Checklist.save` are the only
places `state["dry_run"]` is consulted; every section still computes and shows its would-be acts
(rule 1's exact-argv discipline is unconditional). Read-only probes are unaffected.

UI substrate (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3 v2/§6): interactive mode is
`tools/configtree` -- a generic hierarchical-configuration-editor library, ZERO autoharn
knowledge, imported here ONLY via `tools/setup_tui/tui_app.py` (the one-way dependency
`gates/setup_tui_purity_gate.py` enforces mechanically). A sidebar `Tree` shows every section at
once (complete/incomplete/invalid/blocked-with-reason); the right pane is the selected section
as an ordinary form, all fields at once, inline validation; a persistent status line states what
remains; the commit node lives in the tree and enables exactly when the record is complete. NO
Back/Next -- navigation IS the tree, in any order. If `textual` is not importable, this REFUSES
with the install command -- there is no fallback UI (the teletype `ui.py`/`ui_textual.py`/
`flow_position.py`/`elements.py` stack this superseded is deleted, not degraded-to).
`--from-config <config-file> --world <name> <dest>` drives the SAME ten sections' `submit`
functions directly, zero Textual involved -- the textual-free headless path (spec §4:
"`--from-config` exercises the ENTIRE core ... with zero UI").

Content (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §6): all prose/tables/step definitions/defaults
live in `tools/setup_tui/data/*.toml`, loaded and validated once by `content.py` (a malformed or
incomplete data file REFUSES loudly at load, naming the key) -- Python here holds behavior only.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import in every module here is top of
file.
"""
from __future__ import annotations
