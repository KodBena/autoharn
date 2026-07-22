"""tools/setup_tui -- the guided setup wizard (design/FABLE-SETUP-TUI-SPEC.md, commission
ledger row 1656, spec row 1671).

Three honesty rules this whole package is built to (spec "Posture"):
  1. Driver-only: every action is one of the repo's existing verbs/scripts
     (bootstrap/new-project.sh, bootstrap/teardown-world.sh, serving.boundary_service, led,
     tools/role_charter.py). Every screen prints the EXACT command it is about to run and
     streams that command's real, unedited output. If the TUI dies mid-flow, the operator can
     finish by hand from what the screen showed.
  2. Prepared, not skipped: an act this process cannot itself perform (anything on the cluster
     host -- pg_hba install, reload, createdb) is rendered as a copy-paste block plus a
     what-you-should-see line, then a gate that VERIFIES the effect with a live probe rather
     than trusting the operator's keypress.
  3. Checklist truth: the closing screen is a per-item WITNESSED/SKIPPED/PREPARED table of
     everything the flow touched.

v1 boundaries (spec, named): no daemon management beyond emitting unit text (PREPARED); no
in-place pg_hba edits (this package only ever reads the live file to generate a block --
applying it is always the operator's own act); no teardown flows beyond the rehearsal's own;
writes nothing to any ledger except through `led`; writes nothing anywhere except the target
directory and its own saved checklist.

`--dry-run` (2026-07-19 amendment, ledger row 1719): the SAME eleven screens, but no destructive
or externally visible act -- `tools/setup_tui/runner.py`'s three act-execution choke points
(`run_command`, `start_background`, `write_file`) and `checklist.status_for`/`Checklist.save`
are the only places `state["dry_run"]` is consulted; every screen still computes and shows its
would-be acts (rule 1's exact-argv discipline is unconditional). Read-only probes are
unaffected. See the amendment's own "Built" note in FABLE-SETUP-TUI-SPEC.md for the
implementation seam in full.

UI substrate (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md, commission ledger row 1818 -- supersedes
the v1 "library ONLY if already installed" clause this paragraph originally described): three
backends behind the one-home `Ui` seam (`tools/setup_tui/ui.py`), selected once at startup by
`tools/setup_tui/app.py`. Interactive runs get the real Textual application
(`tools/setup_tui/ui_textual.py`'s `TextualUi`) when `textual` is importable -- a genuine TUI
(Header/sidebar/scrolling transcript/docked prompt/Footer), not a collection of numbered prompts
dressed up. Absent `textual`, ONE teaching line names the exact venv/pip command and the
zero-dependency numbered-menu fallback (`InteractiveUi`: plain stdin/stdout, no curses, no
prompt-toolkit) proceeds automatically -- `--plain` forces that fallback explicitly even when
`textual` is installed. `--scripted <answers-file>` (`ScriptedUi`, an ordered list of
newline-separated answers consumed in prompt order) NEVER touches `textual` -- headless
witnessing stays dependency-free, as it always has; it drives the identical
`Ui.ask_text`/`Ui.ask_choice`/`Ui.confirm`/`Ui.pause` call sites every other backend uses,
swapping only where the next answer string comes from. `textual` remains a declared external
cost of this package's interactive face only -- never of the harness, a born world, or the
witnessing path.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import in every module here is top of
file.
"""
from __future__ import annotations
