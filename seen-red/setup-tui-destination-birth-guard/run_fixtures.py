#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-21T21:49:51Z
#   last-change: 2026-07-21T21:53:08Z
#   contributors: 43f77bff/main
# <<< PROVENANCE-STAMP <<<

"""seen-red/setup-tui-destination-birth-guard/run_fixtures.py -- spec §5's third witness-set
item, first closed defect: "screen_birth accepting an unchecked dest (red against pinned pre-fix
module)". Census-registered in gates/fixture_census.py.

design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md §1(a) names the defect: `screen_birth` checked
NOTHING and trusted `state["dest"]` unchecked -- a FOREIGN destination (non-empty, no autoharn
birth evidence) reached the queued plan silently unless the operator happened to come through
fork-target's own refusal first (e.g. a `--start-at birth` entry never does). This fixture pins
`tools/setup_tui/screens.py` AS IT STOOD at commit a9d779f (this build's own base commit, the
last commit before the destination-state build touched the file -- the SAME pinned-module
technique seen-red/setup-tui-pure-core-foundation/run_fixtures.py's `_load_pinned_commit_executor`
established), drives its `screen_birth` against a real, on-disk FOREIGN scratch directory, and
shows the pre-fix module queues the birth plan entry anyway (RED); the current module refuses
instead, recording a REFUSED checklist row and leaving the plan untouched (GREEN).

Pure decision-phase call only -- `screen_birth` builds a Plan entry, it does not execute
anything (design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md's decision/commit split), so this fixture
never touches Postgres, gpg, or the network. Zero mocks (the real `Checklist`/`ScriptedUi`/`Plan`
classes), zero residue (tmpdir rmtree in `finally`). Lazy imports banned."""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from tools.setup_tui import screens as current_screens  # noqa: E402
from tools.setup_tui.checklist import Checklist  # noqa: E402
from tools.setup_tui.ui import ScriptedUi  # noqa: E402

PRE_FIX_COMMIT = "a9d779f"  # this build's own base commit -- the last commit to touch
# screens.py before the destination-state build added the FOREIGN-classification gate to
# screen_birth. Pinned EXPLICITLY, never "HEAD" (a moving target -- see
# seen-red/setup-tui-boundary-proc-cleanup's own repair for why that already burned this repo
# once).


def _load_pinned_screens(commit: str, scratch: str):
    r = subprocess.run(
        ["git", "-C", REPO, "show", f"{commit}:tools/setup_tui/screens.py"],
        capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip(), (
        f"could not read {commit}:tools/setup_tui/screens.py -- {r.stderr}")
    assert "from tools.setup_tui import destination" not in r.stdout, (
        f"fixture assumption stale: {commit}:tools/setup_tui/screens.py ALREADY imports "
        f"tools.setup_tui.destination -- PRE_FIX_COMMIT needs repinning to a genuinely earlier "
        f"commit")
    path = os.path.join(scratch, "screens_prefix.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(r.stdout)
    spec = importlib.util.spec_from_file_location("screens_prefix", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["screens_prefix"] = mod
    spec.loader.exec_module(mod)
    return mod


def _answers_path(scratch: str, lines: list[str]) -> str:
    path = os.path.join(scratch, "answers.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="setup-tui-destination-birth-guard-")
    ok = True
    try:
        foreign_dir = os.path.join(tmp, "foreign_dest")
        os.makedirs(foreign_dir)
        with open(os.path.join(foreign_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write("some pre-existing project, not autoharn's\n")

        # Same three answers drive both legs: "Run the real birth now?" -> yes, "World name" ->
        # a name, "Project name" -> "-" (accept the default). Neither leg reaches a FOURTH
        # prompt: host/db/dest are pre-seeded in `state`, and the FOREIGN gate (when it fires)
        # returns before any further prompt.
        base_state = {"rehearsal_green": True, "dest": foreign_dir,
                      "pghost": "192.0.2.1", "db": "toy"}

        # --- RED: the pinned pre-fix module queues the birth into FOREIGN content anyway ---
        prefix_mod = _load_pinned_screens(PRE_FIX_COMMIT, tmp)
        cl_red = Checklist()
        ui_red = ScriptedUi(_answers_path(tmp, ["yes", "scratchworld-red", "-"]))
        result_state = prefix_mod.screen_birth(ui_red, cl_red, dict(base_state))
        plan_red = result_state.get("plan")
        queued_red = bool(plan_red and any(
            e.screen == "birth" and e.item == "world birth" for e in plan_red.entries))
        assert queued_red, (
            "RED setup failed: pre-fix screen_birth was expected to queue a birth entry into "
            "FOREIGN content unconditionally -- it did not (fixture assumption stale?)")
        print("case RED ok: pre-fix screen_birth queues a birth plan entry against a FOREIGN "
              "destination, no acknowledgment, no refusal -- reproducing the closed defect")

        # --- GREEN: the current module refuses, plan stays empty ---
        cl_green = Checklist()
        ui_green = ScriptedUi(_answers_path(tmp, ["yes", "scratchworld-green", "-"]))
        result_state = current_screens.screen_birth(ui_green, cl_green, dict(base_state))
        plan_green = result_state.get("plan")
        queued_green = bool(plan_green and any(
            e.screen == "birth" and e.item == "world birth" for e in plan_green.entries))
        assert not queued_green, (
            "GREEN: current screen_birth must NOT queue a birth entry against an "
            "unacknowledged FOREIGN destination -- it did")
        refused = any(it.status == "REFUSED" for it in cl_green.items)
        assert refused, "GREEN: current screen_birth must record a REFUSED checklist row"
        print("case GREEN ok: current screen_birth refuses -- no birth entry queued, a REFUSED "
              "checklist row recorded instead")

        print("ALL CASES OK -- screen_birth's FOREIGN-destination gate, red before green, "
              "pinned pre-fix module vs current, zero mocks")
    except AssertionError as exc:
        print(f"FAILED: {exc}")
        ok = False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
