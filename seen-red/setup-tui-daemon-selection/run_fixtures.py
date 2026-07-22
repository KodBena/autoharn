#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-21T22:35:44Z
#   last-change: 2026-07-22T00:26:44Z
#   contributors: 43f77bff/main, 1fa3ab69/main
# <<< PROVENANCE-STAMP <<<

"""seen-red/setup-tui-daemon-selection/run_fixtures.py -- both-polarity witness set for
design/FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC.md: the status-vocabulary split (§2) and
DaemonSelection/start-daemons (§3), commissioned against the maintainer's field observation g.1
("should create a daemon collection script depending on selected options that start all
relevant daemons and stores into the project folder") and backflow finding 3 ("have the setup
checklist's 'PREPARED' status distinguish 'instructions printed' from 'prerequisite file
confirmed present,' and/or have the checklist verify at the end whether an operator-selected
feature ever actually came up").

CASES (real filesystem, real subprocess, zero mocks; `otelcol-contrib` genuinely absent from
this host -- verified below, not assumed -- which makes the missing-prerequisite leg a REAL
refusal, not a simulated one):

  1. VOCABULARY, construction-time (spec §2): `ChecklistItem(status=PREPARED, detail="")`
     raises; the SAME status with a real detail succeeds; INSTRUCTED/VERIFIED_UP/NOT_UP are all
     legal closed-vocabulary members.
  2. RED (pinned pre-fix screens.py, this worktree's own base commit 93050a9) vs GREEN (current,
     on-disk): driving `screen_observability` through the SAME "select otelcol" answer, the
     pre-fix module emits `ck.PREPARED` for the otelcol start line with ZERO filesystem evidence
     a config was ever written or ever would be (the exact silent-assurance defect backflow
     finding 3 names); the post-fix module NEVER emits `ck.PREPARED` for otelcol at all -- only
     `ck.INSTRUCTED` -- because the new vocabulary makes the false-assurance status
     unrepresentable at this site by construction (ADR-0000: the class is foreclosed, not
     guarded).
  3. LIVE otelcol prerequisite refusal + NOT-UP (spec §5's red leg + start-daemons witness,
     combined): `screen_observability` selects otelcol against a real scratch destination;
     `commit_executor.execute` really writes `otelcol-config.yaml`, really writes and RUNS
     `start-daemons` (best-effort), and the generated script's own captured output shows the
     REAL per-daemon refusal (`otelcol-contrib` not on PATH on this host); the end-of-run
     verification sweep then reports NOT-UP (not silence, not a REFUSED/WITNESSED conflation --
     the spec §5 NOT_UP absence-rendering).
  4. LIVE start-daemons idempotence + a real daemon coming up (spec §5's scripted-birth leg,
     otelcol substituted by a harmless real long-lived command -- `otelcol-contrib` itself is not
     installed on this host, so the ACTUAL binary cannot be exercised; a synthetic
     `DaemonSelection` running `sleep` stands in for "a daemon whose prerequisite IS met", the
     same substitution this fixture's own report states plainly): first `execute()` call starts
     it (VERIFIED_UP via a pidof probe), a second call against the SAME plan/dest reports
     "already up" in the script's own captured output, never a double-start (checked via a live
     `ps` count of matching processes). Killed and reaped in `finally`, zero residue.

Zero residue: every scratch destination lives under a fixture-owned tempdir, removed in a
`finally`; every spawned process is killed and reaped regardless of outcome. Lazy imports
banned."""
from __future__ import annotations

import os
import shutil
import importlib.util
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

from tools.setup_tui import checklist as ck  # noqa: E402
from tools.setup_tui import commit_executor as CE  # noqa: E402
from tools.setup_tui import screens  # noqa: E402
from tools.setup_tui.elements import render_text  # noqa: E402
from tools.setup_tui.plan import DaemonSelection, Plan  # noqa: E402
from tools.setup_tui.ui import ScriptedUi  # noqa: E402

PRE_FIX_COMMIT = "93050a9"  # this worktree's own base commit -- pre-dates this build entirely.

SCRATCH_DIRS: list[str] = []
LIVE_PIDS: list[int] = []


def _mkscratch(prefix: str) -> str:
    d = tempfile.mkdtemp(prefix=prefix)
    SCRATCH_DIRS.append(d)
    return d


def check(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


class RecordingScriptedUi(ScriptedUi):
    """Drives BOTH a pinned pre-fix `screens.py` (`PRE_FIX_COMMIT`, still calling the OLD
    `say`/`banner` shape) AND the current, `emit`-based one -- this fixture's own pre/post
    comparison needs a single driver both eras of the module can call, so `say`/`banner` stay
    here as a compatibility RECORDING shim for the pinned historical module (never reintroduced
    into the live `Ui` class itself -- design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md §1's own "no
    compatibility shim" is about the PRODUCTION seam, not a fixture replaying old code on
    purpose)."""

    def __init__(self, answers_path: str) -> None:
        super().__init__(answers_path)
        self.transcript: list[str] = []

    def say(self, text: str = "") -> None:
        self.transcript.append(text)

    def banner(self, text: str) -> None:
        self.transcript.append(text)

    def emit(self, element) -> None:
        self.transcript.extend(render_text(element))


def _seed_dest() -> str:
    """A scratch destination classified non-FRESH (a placeholder file, same idiom
    seen-red/setup-tui-boundary-interpreter-fallback uses) -- observability's own destination-
    exists check needs this, and this fixture never runs a real birth."""
    top = _mkscratch("daemon-selection-dest-")
    dest = os.path.join(top, "dest")
    os.makedirs(dest)
    with open(os.path.join(dest, "placeholder.txt"), "w", encoding="utf-8") as f:
        f.write("not autoharn's -- FOREIGN classification only, no real world here\n")
    return dest


def load_screens_module(source: str, tag: str):
    if source == "HEAD":
        text = open(os.path.join(REPO, "tools", "setup_tui", "screens.py"),
                    encoding="utf-8").read()
    else:
        r = subprocess.run(["git", "-C", REPO, "show", f"{source}:tools/setup_tui/screens.py"],
                            capture_output=True, text=True)
        check(r.returncode == 0 and bool(r.stdout.strip()),
              f"could not read {source}:tools/setup_tui/screens.py -- {r.stderr}")
        text = r.stdout
    scratch_dir = _mkscratch(f"screens-{tag}-")
    scratch_path = os.path.join(scratch_dir, f"screens_{tag}.py")
    with open(scratch_path, "w", encoding="utf-8") as f:
        f.write(text)
    modname = f"setup_tui_screens_under_test_{tag}"
    spec = importlib.util.spec_from_file_location(modname, scratch_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


def _drive_observability(mod, dest: str, answers: str):
    ui = RecordingScriptedUi(_write_answers(dest, answers))
    cl = ck.Checklist()
    state = {"dest": dest}
    state = mod.screen_observability(ui, cl, state)
    return ui, cl, state


def _write_answers(dest: str, answers: str) -> str:
    path = os.path.join(dest, "..", f"answers-{id(answers)}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(answers)
    return path


def case1_vocabulary() -> None:
    try:
        ck.ChecklistItem(screen="x", item="y", status=ck.PREPARED, detail="")
        raise AssertionError("case 1: PREPARED with empty detail must raise, did not")
    except ValueError as exc:
        check("PREPARED requires a non-empty detail" in str(exc), f"case 1: wrong message: {exc}")
    ck.ChecklistItem(screen="x", item="y", status=ck.PREPARED, detail="config.yaml confirmed present")
    for s in (ck.INSTRUCTED, ck.VERIFIED_UP, ck.NOT_UP, ck.WITNESSED, ck.SKIPPED, ck.REFUSED,
              ck.WOULD_DO, ck.DRY_SKIPPED):
        ck.ChecklistItem(screen="x", item="y", status=s)
    print("case 1 ok: PREPARED requires a non-empty detail (construction-time, ADR-0002 rung 1); "
          "INSTRUCTED/VERIFIED_UP/NOT_UP are legal closed-vocabulary members")


def case2_red_green() -> None:
    pre_mod = load_screens_module(PRE_FIX_COMMIT, "prefix")
    post_mod = load_screens_module("HEAD", "postfix")

    # RED: pre-fix module -- one confirm ("show blocks?" = y) is its whole answer shape.
    dest_red = _seed_dest()
    ui_r, cl_r, _ = _drive_observability(pre_mod, dest_red, "y\n")
    otelcol_rows = [it for it in cl_r.items if "otelcol" in it.item]
    check(any(it.status == ck.PREPARED for it in otelcol_rows),
          f"case 2 RED: pre-fix module should emit PREPARED for otelcol: {otelcol_rows!r}")
    check(not os.path.exists(os.path.join(dest_red, "otelcol-config.yaml")),
          "case 2 RED: pre-fix module must never have written a config (the defect's own shape)")
    print("case 2 RED ok: pinned pre-fix screens.py emits PREPARED for the otelcol start line "
          "with zero config ever written -- the silent-assurance defect, reproduced live")

    # GREEN: post-fix module -- "configure? y", "select otelcol? y", "select otel-watch? n".
    dest_green = _seed_dest()
    ui_g, cl_g, state_g = _drive_observability(post_mod, dest_green, "y\ny\nn\n")
    otelcol_rows_g = [it for it in cl_g.items if "otelcol" in it.item]
    check(all(it.status != ck.PREPARED for it in otelcol_rows_g),
          f"case 2 GREEN: PREPARED must be UNREPRESENTABLE here now: {otelcol_rows_g!r}")
    check(any(it.status == ck.INSTRUCTED for it in otelcol_rows_g),
          f"case 2 GREEN: expected an INSTRUCTED otelcol row: {otelcol_rows_g!r}")
    plan_g = state_g["plan"]
    check(len(plan_g.daemons) == 1 and plan_g.daemons[0].name == "otelcol",
          f"case 2 GREEN: expected exactly one otelcol DaemonSelection: {plan_g.daemons!r}")
    config_entries = [e for e in plan_g.entries if e.item == "otelcol-config.yaml written"]
    check(len(config_entries) == 1, f"case 2 GREEN: expected the config WriteAct queued: "
          f"{[e.item for e in plan_g.entries]!r}")
    print("case 2 GREEN ok: post-fix screens.py never emits PREPARED for otelcol -- only "
          "INSTRUCTED -- and queues both a real config WriteAct and a DaemonSelection")
    return post_mod


def case3_live_refusal_and_notup(post_mod) -> None:
    otelcol_on_path = shutil.which("otelcol-contrib")
    check(otelcol_on_path is None,
          f"case 3 assumption stale: otelcol-contrib IS on PATH ({otelcol_on_path}) -- this "
          f"case's whole premise (a real missing-prerequisite refusal) needs it absent; if this "
          f"host now has it installed, this case needs a different prerequisite to break")

    dest = _seed_dest()
    _, cl, state = _drive_observability(post_mod, dest, "y\ny\nn\n")
    plan = state["plan"]
    result = CE.execute(plan, dest)
    check(result.completed, f"case 3: commit should complete (best-effort daemon run never "
          f"halts it): {result.entry_results!r}")

    config_path = os.path.join(dest, "otelcol-config.yaml")
    check(os.path.isfile(config_path), "case 3: otelcol-config.yaml was not really written")
    script_path = CE.daemon_script_path(dest)
    check(os.path.isfile(script_path) and os.access(script_path, os.X_OK),
          "case 3: start-daemons was not written executable")

    run_result = next(r for r in result.entry_results if r.entry.item == "start-daemons script run")
    check("REFUSED: otelcol -- missing prerequisite" in run_result.detail,
          f"case 3: the generated script's REAL captured output should show the per-daemon "
          f"refusal: {run_result.detail!r}")
    check(run_result.ok, "case 3: best_effort must report ok=True despite the script's nonzero "
          "exit -- the whole point of best_effort")

    check(len(result.daemon_verifications) == 1, "case 3: expected one daemon verification")
    v = result.daemon_verifications[0]
    check(v.daemon.name == "otelcol" and not v.up,
          f"case 3: otelcol must verify NOT-UP (nothing is listening on 13133): {v!r}")
    print(f"case 3 ok: LIVE -- otelcol-config.yaml written, start-daemons written+run, REAL "
          f"per-daemon refusal captured ({run_result.detail.splitlines()[0]!r}), end-of-run "
          f"sweep reports NOT-UP (never silence, never a false WITNESSED)")


def case4_live_idempotent_start() -> None:
    dest = _seed_dest()
    tag_marker = f"daemon-selection-fixture-marker-{os.getpid()}"
    sel = DaemonSelection(
        name="stand-in",
        argv=(sys.executable, "-c", f"import time; time.sleep(100)  # {tag_marker}"), cwd=dest,
        env_notes="a harmless long-lived process standing in for a daemon whose prerequisite "
                   "IS met (otelcol-contrib itself is not installed on this host)",
        health_probe=f"pidof:{tag_marker}", prerequisite=None,
    )
    plan = Plan()
    plan.add_daemon(sel)
    try:
        r1 = CE.execute(plan, dest)
        check(r1.completed, f"case 4: first execute should complete: {r1.entry_results!r}")
        run1 = next(x for x in r1.entry_results if x.entry.item == "start-daemons script run")
        check("started (pid" in run1.detail, f"case 4: expected a real start: {run1.detail!r}")
        time.sleep(0.3)
        pgrep1 = subprocess.run(["pgrep", "-f", tag_marker], capture_output=True, text=True)
        pids = [int(p) for p in pgrep1.stdout.split()]
        LIVE_PIDS.extend(pids)
        check(len(pids) == 1, f"case 4: expected exactly one live process after the first run: "
              f"{pids!r}")
        check(r1.daemon_verifications and r1.daemon_verifications[0].up,
              f"case 4: end-of-run sweep should report the stand-in VERIFIED-UP: "
              f"{r1.daemon_verifications!r}")

        r2 = CE.execute(plan, dest)
        check(r2.completed, f"case 4: second execute should complete: {r2.entry_results!r}")
        run2 = next(x for x in r2.entry_results if x.entry.item == "start-daemons script run")
        check("already up" in run2.detail, f"case 4: second run should report idempotence, not "
              f"a double-start: {run2.detail!r}")
        pgrep2 = subprocess.run(["pgrep", "-f", tag_marker], capture_output=True, text=True)
        pids2 = [int(p) for p in pgrep2.stdout.split()]
        check(pids2 == pids, f"case 4: still exactly the SAME one process, never doubled: "
              f"before={pids!r} after={pids2!r}")
        print("case 4 ok: LIVE -- start-daemons really starts a daemon (VERIFIED-UP via a real "
              "pidof probe), a second execute() against the same plan/dest reports 'already up' "
              "in the script's own captured output, and a live process count confirms it: "
              "still exactly one process, never doubled")
    finally:
        for pid in LIVE_PIDS:
            try:
                os.kill(pid, 9)
            except ProcessLookupError:
                pass


def main() -> int:
    try:
        case1_vocabulary()
        post_mod = case2_red_green()
        case3_live_refusal_and_notup(post_mod)
        case4_live_idempotent_start()
        print("ALL CASES OK -- checklist-split vocabulary + DaemonSelection/start-daemons, "
              "both polarities, live infra, zero residue")
        return 0
    finally:
        for d in SCRATCH_DIRS:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(f"RED/GREEN MISMATCH: {exc}", file=sys.stderr)
        sys.exit(1)
