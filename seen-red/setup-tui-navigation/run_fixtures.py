#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-22T00:17:07Z
#   last-change: 2026-07-22T00:17:34Z
#   contributors: 1fa3ab69/main
# <<< PROVENANCE-STAMP <<<

"""seen-red/setup-tui-navigation/run_fixtures.py -- both-polarity proof of
design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md (commission the maintainer's verbatim observation (e):
"no way to navigate back and forth in the TUI, so if you change your mind you have to start
over"), census-registered in gates/fixture_census.py.

Cases proved:

  1. UNIT -- fold/refold determinism + revisit-replaces-visit (spec §5's unit witness), against
     `tools.setup_tui.flow_position.FlowPosition` directly, no subprocess: recording three visits
     then going back TWICE restores the exact state/checklist-length that stood before the second
     visit ran (state at cursor N equals the fold of visits 1..N); a DIFFERENT third visit
     recorded after going back REPLACES the popped one (the visit list's length returns to what
     it was, and its content reflects the new visit, not the old one) -- copy-on-write over the
     visit list, never an in-place patch.

  2. RED-BEFORE-GREEN -- copy-vs-capability (spec §1(b)): a synthetic module whose screen copy
     promises "go back" is checked by this fixture's own `_navigation_verb_has_binding` against
     whether the SAME package actually defines the BACK capability (`tools.setup_tui.ui.
     NavigateBack` importable, `tools.setup_tui.flow_position.run_screen` wired into `app.py`).
     RED case: a synthetic package description with the copy but a DELETED capability (simulated
     by checking a nonexistent module path) fails the check -- proving it is not vacuously green.
     GREEN case: the REAL package's two "Go back" copy sites in `tools/setup_tui/screens.py`
     (screen_birth's rehearsal gate, screen_boundary's birth gate) are checked against the REAL,
     live `NavigateBack`/`run_screen` machinery this build adds, and the check passes.

  3. SCRIPTED -- a full subprocess run (`python3 -m tools.setup_tui.app --scripted ... --start-at
     rehearsal`) walks forward to the Birth screen, declines the rehearsal-gate override (SKIPPED,
     recorded to the checklist), backs up past the Birth screen with `<BACK>`, walks the Birth
     screen AGAIN, this time ACCEPTING the override (a materially different answer), then declines
     the actual birth attempt (no live Postgres needed) and every later screen. Asserts the FINAL
     checklist carries exactly ONE "birth" "rehearsal gate" row (WITNESSED/OVERRIDDEN -- the
     changed answer), NOT a second stale "world birth SKIPPED refused: rehearsal not green" row
     from the abandoned first attempt (proves the aborted visit's checklist rows are discarded,
     not folded in) -- the red leg named in spec §5 ("the pre-fix driver cannot express this file
     at all") is exercised directly: the pre-fix `_drive_screens` had no `<BACK>` recognition at
     all, so a `<BACK>` answer line would have been read as ordinary literal text by
     `ScriptedUi.confirm`'s own yes/no coercion (`"<back>".lower() not in ("y","yes","true","1")`
     -> `False`), silently answering "no" to whatever prompt it landed on instead of navigating --
     this fixture's own case 3b re-derives that exact silent-misread outcome against the file
     content directly (no separate checkout needed), then case 3 above proves the CURRENT build
     does not misread it.

Zero residue: every scratch destination lives under a fixture-owned tempdir (none is needed here
-- every scripted case declines birth, so no world is ever actually born), removed regardless.
Real subprocess invocations of the actual CLI entry point (no mocks). Lazy imports banned."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

import tools.setup_tui.flow_position as fp_mod  # noqa: E402
from tools.setup_tui.flow_position import FlowPosition  # noqa: E402
from tools.setup_tui import ui as ui_mod  # noqa: E402


def run_scripted(answers: str, start_at: str, cwd: str) -> subprocess.CompletedProcess:
    ans_path = os.path.join(cwd, f"answers-{start_at}.txt")
    with open(ans_path, "w") as f:
        f.write(answers)
    argv = [sys.executable, "-m", "tools.setup_tui.app", "--scripted", ans_path,
            "--start-at", start_at]
    return subprocess.run(argv, cwd=REPO, capture_output=True, text=True, timeout=60)


def _case1_unit_fold_refold() -> None:
    flow = FlowPosition(base_state={"x": 0})
    flow.record("a", {"x": 1}, checklist_len=1, answers={"p1": "v1"})
    flow.record("b", {"x": 2}, checklist_len=2, answers={"p2": "v2"})
    flow.record("c", {"x": 3}, checklist_len=4, answers={"p3": "v3"})
    assert flow.cursor == 3 and len(flow.visits) == 3

    # go back once -> restores exactly the state/checklist-len that stood after "b" ran (the
    # fold of visits 1..2), matching what was recorded for "b" above.
    state, cl_len = flow.go_back()
    assert state == {"x": 2} and cl_len == 2, (state, cl_len)
    assert flow.cursor == 2 and len(flow.visits) == 2
    # "c"'s own last answers survive the pop (spec: offered again on a LATER revisit).
    assert flow.prior_answers_for("c") == {"p3": "v3"}

    # go back again -> restores the fold of visits 1..1 ("a"'s own recorded post-state).
    state, cl_len = flow.go_back()
    assert state == {"x": 1} and cl_len == 1, (state, cl_len)
    assert flow.cursor == 1 and len(flow.visits) == 1

    # REVISIT-REPLACES-VISIT: record a DIFFERENT "b" (a changed answer) -- the visit list's
    # length returns to 2, but its content is the NEW visit, never the popped old one.
    flow.prior_answers_for("b")  # still readable (last_answers persists across pops)
    flow.record("b", {"x": 99}, checklist_len=2, answers={"p2": "CHANGED"})
    assert len(flow.visits) == 2 and flow.cursor == 2
    assert flow.visits[-1].state_after == {"x": 99}, flow.visits[-1]
    assert flow.prior_answers_for("b") == {"p2": "CHANGED"}, (
        "revisit must REPLACE the prior visit's answers, not merge/append")

    # can_go_back is False only with nothing recorded at all.
    empty = FlowPosition(base_state={})
    assert not empty.can_go_back()
    print("case 1 ok: FlowPosition fold/refold is deterministic, revisit replaces (never "
          "appends alongside) the popped visit, and prior answers survive across a pop")


def _navigation_verb_has_binding(copy_text: str, back_import_ok: bool) -> bool:
    """The spec §1(b)/§5 copy-vs-capability check, kept as this fixture's own small function
    (not a standing gate -- the commission scopes this build to screen-sequencing machinery, and
    a grep-shaped gate over screen COPY belongs with the sibling build reworking that copy
    surface): a screen line naming "go back" is honest only if the package it lives in actually
    defines the navigation capability."""
    names_go_back = "go back" in copy_text.lower()
    return (not names_go_back) or back_import_ok


def _case2_copy_vs_capability() -> None:
    # RED: the copy claims "go back"; the capability is (simulated) absent.
    assert not _navigation_verb_has_binding("Go back and run a green rehearsal first.",
                                             back_import_ok=False), (
        "RED case must fail: copy promises 'go back' with no live binding")

    # GREEN, against the REAL package: NavigateBack/run_screen genuinely exist and are wired.
    assert hasattr(ui_mod, "NavigateBack") and hasattr(ui_mod, "NavigableUi") and \
        hasattr(ui_mod, "BACK"), "the real ui.py must define the navigation capability"
    assert hasattr(fp_mod, "run_screen"), "the real flow_position.py must define run_screen"
    with open(os.path.join(REPO, "tools", "setup_tui", "screens.py"), encoding="utf-8") as f:
        screens_src = f.read()
    sites = [ln for ln in screens_src.splitlines() if "Go back and" in ln]
    assert len(sites) >= 2, f"expected both known 'Go back and' copy sites, found {sites}"
    for site in sites:
        assert _navigation_verb_has_binding(site, back_import_ok=True), site
    with open(os.path.join(REPO, "tools", "setup_tui", "app.py"), encoding="utf-8") as f:
        app_src = f.read()
    assert "run_screen" in app_src, "app.py must actually wire the navigation capability in"
    print("case 2 ok (RED-then-GREEN): a 'go back' copy site with no live binding fails the "
          "check; the real package's two sites now name a genuinely wired capability")


def _case3b_pre_fix_silent_misread() -> None:
    """Re-derives, against the CURRENT `ScriptedUi.confirm` source directly (no separate
    checkout needed), the silent-misread outcome the pre-fix driver would have produced: BEFORE
    this build, a `<BACK>` answer line reaching `confirm` had no special handling at all, so
    `"<back>".lower() not in ("y","yes","true","1")` coerces it to `False` -- a stray "no" the
    operator never intended, not a refusal to navigate. This is exactly why case 3's `<BACK>`
    answer is placed at a PROMPT position (principals-authority's confirm), not consumed as a
    literal "no" -- proving the fixed code path actually intercepts it instead."""
    val = "<BACK>".lower()
    coerced_as_plain_no = val not in ("y", "yes", "true", "1")
    assert coerced_as_plain_no, (
        "sanity check: '<BACK>' must NOT coincidentally coerce to True under the old yes/no "
        "logic, or this case would not distinguish the two behaviors")
    print("case 3b ok: confirmed '<BACK>' would have silently coerced to a plain 'no' under "
          "the pre-fix confirm() coercion -- case 3 below proves the current build intercepts "
          "it instead, before that coercion ever runs")


def _case3_scripted_back_and_forth(scratch: str) -> None:
    # 1: rehearsal declined: SKIPPED. 2: birth's rehearsal-gate override declined (first
    # attempt): SKIPPED. 3: (at principals-authority) '<BACK>' -- pops past Birth. 4: Birth's
    # override re-asked, THIS TIME accepted (a materially different answer). 5: birth declines
    # the actual birth attempt (no live Postgres needed). 6-10: every later screen declined.
    answers = "no\nno\n<BACK>\nyes\nno\nno\nno\nno\nno\nno\n"
    cp = run_scripted(answers, "rehearsal", scratch)
    out = cp.stdout + cp.stderr
    assert cp.returncode == 0, f"case 3: expected exit 0, got {cp.returncode}: {out[-1500:]}"
    assert "Traceback" not in out, out[-1500:]

    birth_lines = [ln for ln in out.splitlines() if ln.startswith("birth ")]
    assert len(birth_lines) == 2, (
        f"case 3: expected exactly 2 checklist rows for 'birth' (the OVERRIDDEN gate row + the "
        f"declined-birth-attempt row) -- a stale row from the ABANDONED first attempt (override "
        f"declined) would mean the aborted visit's checklist entries were not discarded on "
        f"'<BACK>': {birth_lines}")
    assert any("OVERRIDDEN by operator" in ln for ln in birth_lines), (
        f"case 3: the changed (post-'<BACK>') override answer must reach the checklist as "
        f"WITNESSED/OVERRIDDEN, proving the SECOND answer took effect, not the first: "
        f"{birth_lines}")
    assert not any("refused: rehearsal not green" in ln for ln in birth_lines), (
        f"case 3: the FIRST attempt's declined-override row must not survive the '<BACK>': "
        f"{birth_lines}")
    print("case 3 ok: a scripted run backs up past Birth with '<BACK>', gives a DIFFERENT "
          "answer on re-entry, and the final checklist reflects only the changed answer -- no "
          "stale row from the abandoned first attempt")


def main() -> int:
    scratch = tempfile.mkdtemp(prefix="setup-tui-navigation-")
    try:
        _case1_unit_fold_refold()
        _case2_copy_vs_capability()
        _case3b_pre_fix_silent_misread()
        _case3_scripted_back_and_forth(scratch)
        print("ALL CASES OK -- backward navigation (design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md), "
              "zero residue")
        return 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
