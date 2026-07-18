# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T21:30:53Z
#   last-change: 2026-07-18T21:30:53Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

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

UI substrate: this build found neither `textual` nor `urwid` installed in the interpreter that
runs it (`python3 -c "import textual"` / `"import urwid"` both raised `ModuleNotFoundError` at
build time) -- so per the spec's v1 boundary ("Python + textual/urwid-class library ONLY if
already installed -- otherwise plain curses/prompt-toolkit-free numbered-menu fallback"), this
package uses the numbered-menu fallback (`tools/setup_tui/ui.py`): plain stdin/stdout, no
curses, no prompt-toolkit, no new dependency of any kind. The same module also backs
`--scripted <answers-file>` (an ordered list of newline-separated answers consumed in prompt
order) for witnessing an otherwise-interactive flow without a human at the keyboard -- it drives
the identical `Ui.ask_text`/`Ui.ask_choice`/`Ui.confirm`/`Ui.pause` call sites the interactive
backend uses, swapping only where the next answer string comes from.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import in every module here is top of
file.
"""
from __future__ import annotations
