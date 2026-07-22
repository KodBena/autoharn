#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-21T00:00:00Z
#   last-change: 2026-07-22T00:27:03Z
#   contributors: 43f77bff/main, 1fa3ab69/main
# <<< PROVENANCE-STAMP <<<

"""seen-red/setup-tui-boundary-interpreter-fallback/run_fixtures.py -- both-polarity proof for
the commission's field observation g (first half, verbatim): "had to manually start boundary-
multiplex". A fresh-context investigation traced this to `tools/setup_tui/screens.py`'s
`screen_boundary`: when the operator answers YES to "Start the boundary service now?", the
auto-start was gated on a HARDCODED interpreter path
(`os.path.expanduser("~/w/vdc/venvs/generic/bin/python")`) with NO fallback and NO message --
absent that one exact path, the code silently fell into the manual/systemd-unit-text branch,
never saying an auto-start was even attempted or why it degraded. That is a silent override of
an explicit operator "yes" (ADR-0002 rule 1) with no rung-4 diagnostic naming the reason (ADR-0002
rule 4) -- exactly the class of hazard this project's founding annoyance names: a tool that
pre-resolves a choice against what happens to be installed without ever saying so.

THE FIX (this same commit) gives `screen_boundary` `bootstrap/new-project.sh:319-320`'s own
fallback pattern (ADR-0012 P1 -- one pattern, not a second hand-rolled rule): preferred venv if
executable, else `python3` on PATH, stated to the operator as one honest "interpreter: ..." line
either way. If NEITHER exists, the degradation to manual instructions now says so loudly: a named
"REFUSED auto-start" line plus a REFUSED checklist row carrying the concrete reason -- rung 4 of
ADR-0002's loudness hierarchy ("Logged warning / surfaced diagnostic"), never a silent downgrade.

METHOD -- no real infra needed (interpreter RESOLUTION is a read-only, decision-phase-legal probe
per design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md §2.5's first declared exception; `screen_boundary`
itself, Phase 2, is a PURE DECIDER that only queues plan entries -- nothing executes, so this
fixture calls `screen_boundary(ui, cl, state)` directly, in-process, no Postgres, no venv, no
subprocess): the PINNED-PRE-FIX-MODULE idiom (the same one `seen-red/setup-tui-boundary-proc-
cleanup/run_fixtures.py` uses for app.py) loads `git show <PRE_FIX_COMMIT>:tools/setup_tui/
screens.py` -- this worktree's own pre-fix commit -- into a scratch file via
`importlib.util.spec_from_file_location` under a distinct module name, and drives it against the
SAME scenario the current, on-disk (fixed) `tools/setup_tui/screens.py` is driven against.
`HOME` is overridden to a nonexistent scratch path for BOTH legs (deterministic across dev
machines: whether the *actual* operator running this fixture happens to have
~/w/vdc/venvs/generic/bin/python is irrelevant to what's under test) so the preferred venv is
always absent; `probes.which` (the ONE home for interpreter-on-PATH lookups, reused rather than
re-derived -- ADR-0012 P1) is monkeypatched per case to make `python3`-on-PATH present or absent
on demand, independent of the real host's PATH.

TWO CASES, each leg:
  CASE fallback-available:   preferred venv absent, python3 present on PATH.
  CASE fallback-unavailable: preferred venv absent, python3 ALSO absent.

RED (pre-fix, both cases IDENTICAL -- the old code never looks at python3 at all): the operator's
"yes" is silently swallowed -- zero "interpreter:" line, zero REFUSED row, straight to the
PREPARED systemd/manual block as if nothing had been attempted.
GREEN (post-fix): fallback-available names the chosen interpreter and queues the real
BackgroundAct with it; fallback-unavailable names the concrete reason, records a REFUSED
checklist row, and ONLY THEN falls back to the manual block.

Usage: python3 seen-red/setup-tui-boundary-interpreter-fallback/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Zero residue (scratch dirs removed). Lazy imports
banned."""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))

from tools.setup_tui import checklist as ck  # noqa: E402
from tools.setup_tui import probes as probes_mod  # noqa: E402
from tools.setup_tui.elements import render_text  # noqa: E402
from tools.setup_tui.ui import ScriptedUi  # noqa: E402

# This worktree's own pre-fix commit (immediately before this fixture's own fix landed) --
# verified below to carry no fallback/REFUSED-auto-start behavior, so a future drift that
# happens to touch this same region cannot silently invalidate the RED leg's premise.
PRE_FIX_COMMIT = "7e29101"

FAKE_VENV_PATH = "~/w/vdc/venvs/generic/bin/python"  # what screens.py hardcodes, expanded below
FAKE_PYTHON3_PATH = "/fixture/scratch/bin/python3"  # deterministic stand-in, never a real binary

SCRATCH_DIRS: list[str] = []  # every tempfile.mkdtemp() this run makes, removed in main()'s
# finally regardless of outcome -- zero residue.


def _mkscratch(prefix: str) -> str:
    d = tempfile.mkdtemp(prefix=prefix)
    SCRATCH_DIRS.append(d)
    return d


class RecordingScriptedUi(ScriptedUi):
    """Same driving contract as `ScriptedUi` (answers file, in order) -- adds a plain-text
    transcript of every `emit` call (rendered via `elements.render_text`) so the fixture can
    assert on exactly what the operator would have seen, without scraping stdout. This fixture
    also drives a PINNED pre-fix `screens.py` (still calling the OLD `say`/`banner` shape) for
    its RED leg, alongside the current `emit`-based one for GREEN -- `say`/`banner` stay here as
    a compatibility RECORDING shim for the pinned historical module only (never reintroduced into
    the live `Ui` class -- design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md §1's "no compatibility shim"
    is about the production seam, not a fixture replaying old code on purpose)."""

    def __init__(self, answers_path: str) -> None:
        super().__init__(answers_path)
        self.transcript: list[str] = []

    def say(self, text: str = "") -> None:
        self.transcript.append(text)

    def banner(self, text: str) -> None:
        self.transcript.append(text)

    def emit(self, element) -> None:
        self.transcript.extend(render_text(element))


def load_screens_module(source: str, tag: str) -> object:
    """Loads `source` (either 'HEAD' for the current on-disk fix, or a pinned commit SHA for the
    pre-fix leg) as a standalone module under its own name -- the pinned-pre-fix-module idiom
    (mirrors seen-red/setup-tui-boundary-proc-cleanup/run_fixtures.py's DRIVER_SOURCE approach,
    applied directly to screens.py instead of a subprocess driver, since Phase 2's pure decider
    means no subprocess/real infra is needed to exercise this code path at all). Its own
    `from tools.setup_tui import ...` sub-imports resolve against the REAL, installed package
    (already on sys.path above) regardless of where this loaded copy's own file happens to sit."""
    if source == "HEAD":
        path = REPO / "tools" / "setup_tui" / "screens.py"
        text = path.read_text(encoding="utf-8")
    else:
        r = subprocess.run(["git", "-C", str(REPO), "show", f"{source}:tools/setup_tui/screens.py"],
                            capture_output=True, text=True)
        assert r.returncode == 0 and r.stdout.strip(), (
            f"could not read {source}:tools/setup_tui/screens.py -- {r.stderr}"
        )
        text = r.stdout

    scratch_dir = _mkscratch(f"screens-{tag}-")
    scratch_path = os.path.join(scratch_dir, f"screens_{tag}.py")
    with open(scratch_path, "w", encoding="utf-8") as f:
        f.write(text)

    modname = f"setup_tui_screens_under_test_{tag}"
    spec = importlib.util.spec_from_file_location(modname, scratch_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


def run_scenario(mod, tag: str, python3_present: bool) -> tuple[list[str], ck.Checklist, object]:
    """Drives `mod.screen_boundary` for one (fallback-available / fallback-unavailable) case
    against a fresh scratch destination and a fresh Checklist/Plan. Returns
    (transcript, checklist, resulting state) for the caller to assert against."""
    orig_which = probes_mod.which

    def fake_which(name: str):
        if name == "python3":
            return FAKE_PYTHON3_PATH if python3_present else None
        return orig_which(name)

    probes_mod.which = fake_which
    orig_home = os.environ.get("HOME")
    os.environ["HOME"] = "/fixture/scratch/nonexistent-home"  # guarantees the preferred venv is
    # absent regardless of what the machine actually running this fixture has installed.
    top = _mkscratch(f"boundary-fallback-{tag}-")
    dest = os.path.join(top, "dest")
    os.makedirs(dest)
    # HAZARD FIX (found live while touching this exact fixture for the CHECKLIST-SPLIT-SPEC
    # build, not this build's own commission -- pulled per CLAUDE.md's engineering-responsibility
    # rule, "a hazard within reach of the work you are touching, you fix or you flag loudly"):
    # design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md (commit 93050a9, this worktree's own base)
    # reclassified an EMPTY existing directory as FRESH, same as nonexistent -- this fixture's
    # bare `os.makedirs(dest)` used to be enough to make `screens.py`'s destination-exists check
    # pass; after that spec landed it instead hits screen_boundary's OWN "destination directory
    # does not exist" REFUSED leg before ever reaching the interpreter-fallback logic this
    # fixture exists to test, silently invalidating BOTH the RED and the GREEN legs (proven: this
    # same mismatch reproduces against the unmodified worktree base, `git stash` verified). A
    # placeholder file keeps `dest` non-empty (FOREIGN, not FRESH) -- the same shape scripted-
    # smoke's own case 5 already uses for exactly this reason.
    with open(os.path.join(dest, "placeholder.txt"), "w", encoding="utf-8") as f:
        f.write("not autoharn's -- this fixture only needs a non-empty (non-FRESH) directory\n")
    answers_path = os.path.join(top, "answers.txt")
    with open(answers_path, "w", encoding="utf-8") as f:
        f.write("y\ny\n")  # "Configure the boundary service now?" / "Start the boundary
        # service now (this process)?" -- dest/world/pghost/db/dry_run are pre-seeded in state
        # below so no further ask_text prompts fire, and dry_run=True means the PREPARED block's
        # post-keypress verify (which would consume a 3rd answer) never runs either.

    ui = RecordingScriptedUi(answers_path)
    cl = ck.Checklist()
    state = {
        "birth_ok": True,
        "dest": dest,
        "world": "fixtureworld",
        "pghost": "192.0.2.1",  # TEST-NET-1 (RFC 5737) -- never dialed; decision phase is pure
        "db": "toy",
        "dry_run": True,
    }
    try:
        state = mod.screen_boundary(ui, cl, state)
    finally:
        probes_mod.which = orig_which
        if orig_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = orig_home
    return ui.transcript, cl, state


def check(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    try:
        return _main_inner()
    finally:
        # Zero residue regardless of outcome -- every mkdtemp() this run made (module scratch
        # copies, per-case dest/answers dirs), removed.
        for d in SCRATCH_DIRS:
            shutil.rmtree(d, ignore_errors=True)


def _main_inner() -> int:
    pre_fix_source = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{PRE_FIX_COMMIT}:tools/setup_tui/screens.py"],
        capture_output=True, text=True,
    )
    check(pre_fix_source.returncode == 0 and pre_fix_source.stdout.strip(),
          f"could not read {PRE_FIX_COMMIT}:tools/setup_tui/screens.py")
    check("REFUSED auto-start" not in pre_fix_source.stdout,
          f"fixture assumption stale: {PRE_FIX_COMMIT}:tools/setup_tui/screens.py already carries "
          f"the fix -- PRE_FIX_COMMIT needs repinning to a genuinely earlier commit")

    pre_mod = load_screens_module(PRE_FIX_COMMIT, "prefix")
    post_mod = load_screens_module("HEAD", "postfix")

    results = []

    # ===================================== RED (pre-fix) =====================================
    for py3 in (True, False):
        tag = f"pre-fix/python3-{'present' if py3 else 'absent'}"
        transcript, cl, _state = run_scenario(pre_mod, f"pre-{py3}", py3)
        joined = "\n".join(transcript)
        check("interpreter:" not in joined,
              f"{tag}: RED leg unexpectedly names an interpreter choice -- fixture premise stale "
              f"(pre-fix code should silently swallow the operator's 'yes'): {joined!r}")
        refused_rows = [it for it in cl.items if it.item == "service auto-start"]
        check(not refused_rows,
              f"{tag}: RED leg unexpectedly recorded a 'service auto-start' checklist row -- "
              f"fixture premise stale: {refused_rows!r}")
        unit_rows = [it for it in cl.items if it.item == "service unit text"]
        check(len(unit_rows) == 1 and unit_rows[0].status == ck.PREPARED,
              f"{tag}: expected the silent fall-through straight to the PREPARED systemd block: "
              f"{cl.items!r}")
        results.append(f"RED ok ({tag}): silently fell to the manual block, zero 'interpreter:' "
                        f"line, zero REFUSED row -- the operator's 'yes' vanished without a trace")

    # ==================================== GREEN (post-fix) ===================================
    transcript, cl, state = run_scenario(post_mod, "post-avail", True)
    joined = "\n".join(transcript)
    check("interpreter:" in joined, f"GREEN fallback-available: no 'interpreter:' line: {joined!r}")
    check(FAKE_PYTHON3_PATH in joined and "using python3 on PATH" in joined,
          f"GREEN fallback-available: interpreter line doesn't name the chosen fallback and why: "
          f"{joined!r}")
    plan = state["plan"]
    started = [e for e in plan.entries if e.item == "service started"]
    check(len(started) == 1, f"GREEN fallback-available: expected one 'service started' plan "
          f"entry, got {len(started)}: {[e.item for e in plan.entries]!r}")
    check(started[0].act.argv[0] == FAKE_PYTHON3_PATH,
          f"GREEN fallback-available: BackgroundAct should exec the resolved fallback interpreter, "
          f"got argv[0]={started[0].act.argv[0]!r}")
    refused_rows = [it for it in cl.items if it.item == "service auto-start"]
    check(not refused_rows, f"GREEN fallback-available: unexpected REFUSED auto-start row: "
          f"{refused_rows!r}")
    results.append("GREEN ok (post-fix/python3-present): names the resolved fallback interpreter "
                    "and its reason, queues the real BackgroundAct against it")

    transcript, cl, state = run_scenario(post_mod, "post-unavail", False)
    joined = "\n".join(transcript)
    check("interpreter:" in joined and "NEITHER" in joined and "python3 is on PATH" in joined,
          f"GREEN fallback-unavailable: no honest 'neither is available' interpreter line: "
          f"{joined!r}")
    check("REFUSED auto-start" in joined and "operator answered yes" in joined,
          f"GREEN fallback-unavailable: no loud REFUSED-auto-start line naming the operator's "
          f"'yes': {joined!r}")
    refused_rows = [it for it in cl.items if it.item == "service auto-start"]
    check(len(refused_rows) == 1 and refused_rows[0].status == ck.REFUSED,
          f"GREEN fallback-unavailable: expected exactly one REFUSED 'service auto-start' "
          f"checklist row, got: {[it for it in cl.items]!r}")
    plan = state["plan"]
    started = [e for e in plan.entries if e.item == "service started"]
    check(not started, f"GREEN fallback-unavailable: no BackgroundAct should have been queued "
          f"(no interpreter to exec): {[e.item for e in plan.entries]!r}")
    unit_rows = [it for it in cl.items if it.item == "service unit text"]
    # FIXTURE-CONTRACT CHANGE (design/FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC.md §2, this build):
    # ck.INSTRUCTED, not ck.PREPARED -- the narrowed PREPARED now requires a confirmed-present
    # prerequisite named in its own detail; unit TEXT shown with nothing about the world's state
    # checked is the vocabulary's INSTRUCTED case (the OLD PREPARED's honest reading). Only the
    # POST-fix leg changes here -- the RED (pre-fix) leg above still asserts ck.PREPARED, and
    # correctly so: it loads the PINNED pre-fix screens.py via `git show`, unaffected by this
    # commit's edits to the on-disk module.
    check(len(unit_rows) == 1 and unit_rows[0].status == ck.INSTRUCTED,
          f"GREEN fallback-unavailable: expected the manual/systemd block to still be shown "
          f"(INSTRUCTED) AFTER the loud refusal: {cl.items!r}")
    results.append("GREEN ok (post-fix/python3-absent): names the concrete reason, records a "
                    "REFUSED checklist row naming it, THEN falls back to the manual block")

    for line in results:
        print(line)
    print("ALL CASES OK -- screen_boundary's interpreter fallback names its choice, and its "
          "refusal, loudly; red before green")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(f"RED/GREEN MISMATCH: {exc}", file=sys.stderr)
        sys.exit(1)
