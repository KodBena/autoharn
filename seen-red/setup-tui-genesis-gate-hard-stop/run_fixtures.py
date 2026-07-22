#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-21T23:52:35Z
#   last-change: 2026-07-22T00:26:12Z
#   contributors: 1fa3ab69/main
# <<< PROVENANCE-STAMP <<<

"""seen-red/setup-tui-genesis-gate-hard-stop/run_fixtures.py -- RED-then-GREEN witness for the
GENESIS-GATE HARD-STOP (ledger row 1918; maintainer's verbatim "Yes, it should stop"; the row
also names the class this closes: AUTOHARN_BACKFLOW.md finding 1, "the wrong-key instance was
fixed at 238b4ea, this closes the CLASS").

THE DEFECT, REPRODUCED FOR REAL (not asserted from prose): `verify-commission` exits 0 whether
or not its JSON body's `verdict` is VERIFIED (module docstring's own "TWO VERBS" note) -- so a
`commit_executor` that judges an act's success by exit code alone (every version through
b9f3612) treats a FAILED ceremony verification exactly like a success and runs every plan entry
after it. This fixture pins `tools/setup_tui/commit_executor.py` AS IT STOOD at commit b9f3612
(the commit named in the commission, loaded via `importlib`, the same technique
seen-red/setup-tui-signed-genesis-key-pinning/run_fixtures.py's `_load_pinned_signed_genesis`
uses) and runs it, for real, against a plan whose verify-commission act is a SCRATCH stand-in
script with the exact I/O contract of the real `bootstrap/templates/verify-commission.tmpl`
(argv ignored, always exits 0, prints a JSON body) but a deliberately NOT_VERIFIED verdict --
never a mock of `commit_executor`/`signed_genesis`/`screens` (this project's own code), only of
the external `verify-commission` binary those modules already treat as an opaque subprocess.

SCOPE, NAMED HONESTLY (same discipline seen-red/setup-tui-signed-genesis-resume/run_fixtures.py
already uses for this exact ceremony): this fixture proves the property at the layer that
actually carries the defect and its fix -- `commit_executor.execute()`'s halt/continue decision,
`signed_genesis.verify_commission_act`'s `verdict_check`, and `screens.py`'s `_dispatch_result`
teaching text + checklist rows + `app.py`'s non-zero-exit propagation -- using a SCRATCH
verify-commission stand-in, not a full `new-project.sh` birth against a live Postgres substrate.
A full live-birth ceremony (real gpg keygen, real sign, a real mismatched key, a real fix, a real
resume through the REAL `verify-commission.tmpl`) is a materially larger task than this
commission's own scoped claim and is marked UNEXERCISED below with its concrete blocker, matching
this exact package's own precedent (setup-tui-signed-genesis-resume's docstring scopes its own
live-DB extended case identically). The STOP-FIX-RESUME property itself IS witnessed here, for
real, at the commit_executor/journal layer (case 4) -- fixing the SAME scratch verify-commission
script's verdict and re-invoking `execute()` against the SAME destination/journal.

Needs a real `git show` of this repo's own history (b9f3612) and no other external dependency.
Zero residue: every scratch directory removed in a `finally`. Lazy imports banned.

Usage: python3 seen-red/setup-tui-genesis-gate-hard-stop/run_fixtures.py
Exit 0 if every case matches (or reports its own UNEXERCISED honestly); 1 otherwise."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))

from tools.setup_tui import app as APP  # noqa: E402 -- the CURRENT, fixed app.py
from tools.setup_tui import checklist as CK  # noqa: E402
from tools.setup_tui import commit_executor as CE  # noqa: E402 -- the CURRENT, fixed module
from tools.setup_tui import plan as P  # noqa: E402
from tools.setup_tui.elements import render_text  # noqa: E402
from tools.setup_tui import screens as SCREENS  # noqa: E402 -- the CURRENT, fixed module
from tools.setup_tui import signed_genesis as SG  # noqa: E402

FAILURES: list[str] = []


def check(label: str, cond: bool, detail: object = "") -> None:
    if cond:
        print(f"  OK   {label}")
    else:
        msg = f"FAIL {label}" + (f" -- {detail}" if detail != "" else "")
        print(f"  {msg}")
        FAILURES.append(msg)


PRE_FIX_COMMIT = "b9f3612"  # named verbatim in the commission -- the commit the wizard's genesis
# verification gate STILL COMPLETED THE BIRTH on a failed verdict at, per AUTOHARN_BACKFLOW.md
# finding 1's class (the wrong-key INSTANCE was already fixed at 238b4ea; this pins the commit
# where the CLASS -- exit-code-is-not-the-signal -- was still live).

NOT_VERIFIED_BODY = {"verdict": "NOT_VERIFIED",
                     "detail": "signature does not match any trusted key in keys/ (scratch fixture)"}
VERIFIED_BODY = {"verdict": "VERIFIED", "detail": "scratch fixture -- signature matches"}


def _load_pinned_commit_executor(commit: str, scratch: str):
    r = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{commit}:tools/setup_tui/commit_executor.py"],
        capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip(), (
        f"could not read {commit}:tools/setup_tui/commit_executor.py -- {r.stderr}")
    assert "verdict_check" not in r.stdout, (
        f"fixture assumption stale: {commit}:tools/setup_tui/commit_executor.py ALREADY carries "
        f"the verdict_check fix -- PRE_FIX_COMMIT needs repinning to a genuinely earlier commit")
    path = os.path.join(scratch, "commit_executor_prefix.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(r.stdout)
    spec = importlib.util.spec_from_file_location("commit_executor_prefix", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["commit_executor_prefix"] = mod  # dataclass field-type resolution needs this
    spec.loader.exec_module(mod)
    return mod


def _write_scratch_verify_commission(dest: str, body: dict) -> None:
    """A scratch stand-in for `<dest>/verify-commission` carrying the REAL binary's I/O contract
    (module docstring's own "TWO VERBS" note: exits 0 unconditionally, the verdict lives in the
    JSON body) -- never a mock of THIS project's own code, only of the external subprocess
    `signed_genesis.verify_commission_act` already treats as opaque."""
    path = os.path.join(dest, "verify-commission")
    script = "#!/usr/bin/env python3\nimport sys\nprint(" + repr(json.dumps(body)) + ")\nsys.exit(0)\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(script)
    os.chmod(path, 0o755)


def _build_plan(dest: str, *, accept_unverified: bool) -> P.Plan:
    """The two-entry plan every case below drives: the real `verify_commission_act` (built the
    SAME way `screens.py`'s `screen_signed_genesis` builds it) against `dest`'s scratch
    verify-commission stand-in, then a canary write that only a CONTINUED commit ever reaches --
    the fixture's own observable for "did the commit halt here, or not"."""
    verify_act, verify_produces = SG.verify_commission_act(
        dest, "fixture-commission-id", accept_unverified=accept_unverified)
    plan = P.Plan()
    plan.append(P.PlanEntry(screen="signed-genesis", item="ceremony gate (verify-commission)",
                             lesson="requires the VERIFIED verdict before recording WITNESSED",
                             act=verify_act, produces=verify_produces))
    plan.append(P.PlanEntry(
        screen="signed-genesis", item="canary after verify", lesson="canary",
        act=P.WriteAct(path=os.path.join(dest, "AFTER_VERIFY_RAN"), content="canary\n")))
    return plan


def case_red_prefix_completes_anyway(scratch: str) -> None:
    print("case 1 (RED): pre-fix commit_executor (b9f3612) COMPLETES past a NOT_VERIFIED verdict")
    pre = _load_pinned_commit_executor(PRE_FIX_COMMIT, scratch)
    dest = os.path.join(scratch, "dest-red")
    os.makedirs(dest)
    _write_scratch_verify_commission(dest, NOT_VERIFIED_BODY)
    plan = _build_plan(dest, accept_unverified=False)
    result = pre.execute(plan, dest)
    check("RED: pre-fix commit reports completed=True despite the NOT_VERIFIED verdict "
          "(the defect, reproduced for real)", result.completed)
    check("RED: pre-fix commit ran the canary entry AFTER the failed verify (nothing halted it)",
          os.path.isfile(os.path.join(dest, "AFTER_VERIFY_RAN")))


def case_green_post_fix_stops(scratch: str) -> None:
    print("case 2 (GREEN): post-fix commit_executor STOPS on the same NOT_VERIFIED verdict")
    dest = os.path.join(scratch, "dest-stop")
    os.makedirs(dest)
    _write_scratch_verify_commission(dest, NOT_VERIFIED_BODY)
    plan = _build_plan(dest, accept_unverified=False)
    result = CE.execute(plan, dest)
    check("GREEN: post-fix commit reports completed=False -- the commit HALTED", not result.completed)
    check("GREEN: the canary entry never ran -- nothing after the failed gate executed",
          not os.path.isfile(os.path.join(dest, "AFTER_VERIFY_RAN")))
    check("GREEN: the verify entry's own EntryResult is ok=False (the real halt signal)",
          not result.entry_results[0].ok)
    journal = CE.CommitJournal.open_or_create(CE.journal_path(dest), len(plan.entries))
    check("GREEN: the commit journal still names the verify-commission entry PENDING (never "
          "marked DONE) -- a fixed-keyring re-run resumes exactly here",
          journal.statuses[0] == CE.PENDING, journal.statuses)

    # The full teaching refusal + checklist row, driven through the REAL screens.py dispatch.
    class _RecordingUi:
        def __init__(self) -> None:
            self.lines: list[str] = []

        def emit(self, element) -> None:
            self.lines.extend(render_text(element))

    ui = _RecordingUi()
    cl = CK.Checklist()
    entry = plan.entries[0]
    SCREENS._dispatch_result(ui, cl, {}, 0, entry, result.entry_results[0])
    transcript = "\n".join(ui.lines)
    for phrase in ("GENESIS-GATE HARD STOP", "WHAT FAILED", "WHY IT MATTERS", "WHAT TO CHECK",
                   "HOW TO RESUME", "OVERRIDE:", "--accept-unverified-genesis"):
        check(f"GREEN: the refusal teaches -- transcript names {phrase!r}", phrase in transcript,
              transcript[:400])
    refused_rows = [it for it in cl.items if it.item == "ceremony gate (verify-commission)"]
    check("GREEN: the checklist records the stop with the existing, honest REFUSED status "
          "(no new vocabulary minted)",
          len(refused_rows) == 1 and refused_rows[0].status == CK.REFUSED, cl.render())


def case_green_override_continues_and_records(scratch: str) -> None:
    print("case 3 (GREEN): --accept-unverified-genesis continues past the SAME verdict, "
          "eyes open, recorded")
    dest = os.path.join(scratch, "dest-override")
    os.makedirs(dest)
    _write_scratch_verify_commission(dest, NOT_VERIFIED_BODY)
    plan = _build_plan(dest, accept_unverified=True)
    result = CE.execute(plan, dest)
    check("GREEN: override -- commit reports completed=True (today's note-and-continue preserved)",
          result.completed)
    check("GREEN: override -- the canary entry ran (the commit was NOT halted)",
          os.path.isfile(os.path.join(dest, "AFTER_VERIFY_RAN")))
    verify_result = result.entry_results[0]
    check("GREEN: override -- the verify entry's own EntryResult is ok=True (override honored)",
          verify_result.ok)
    body = json.loads(verify_result.detail)
    check("GREEN: override -- the REAL verdict (NOT_VERIFIED) is still carried in detail, never "
          "faked as VERIFIED", body.get("verdict") == "NOT_VERIFIED", body)

    class _RecordingUi:
        def __init__(self) -> None:
            self.lines: list[str] = []

        def emit(self, element) -> None:
            self.lines.extend(render_text(element))

    ui = _RecordingUi()
    cl = CK.Checklist()
    entry = plan.entries[0]
    SCREENS._dispatch_result(ui, cl, {"accept_unverified_genesis": True}, 0, entry, verify_result)
    transcript = "\n".join(ui.lines)
    # Space-joined, not newline-joined: this phrase is long enough that `elements.render_text`
    # (design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md §2's 78-column measure) wraps it across two
    # printed lines -- the CONTENT is unchanged, only its line breaks, so this check reads the
    # same words with wrap boundaries collapsed back to spaces rather than asserting on exactly
    # where the renderer chose to break the line.
    flat = " ".join(" ".join(ui.lines).split())
    check("GREEN: override -- transcript names the eyes-open continuation",
          "DESPITE this unverified genesis signature" in flat, flat[:400])
    override_rows = [it for it in cl.items if it.item == "verify-commission override exercised"]
    check("GREEN: override -- an EXPLICIT, separate checklist row records the override "
          "(the eyes-open record the commission asks for), status WITNESSED",
          len(override_rows) == 1 and override_rows[0].status == CK.WITNESSED, cl.render())
    gate_rows = [it for it in cl.items if it.item == "ceremony gate (verify-commission)"]
    check("GREEN: override -- the gate's OWN row still honestly reads REFUSED (the override "
          "does not make the signature verify, only lets the commit continue past the fact)",
          len(gate_rows) == 1 and gate_rows[0].status == CK.REFUSED, cl.render())


def case_stop_fix_resume(scratch: str) -> None:
    print("case 4 (GREEN): stop -> fix the scratch verify-commission -> resume completes "
          "(journal-level, real commit_executor.execute() re-entry)")
    dest = os.path.join(scratch, "dest-resume")
    os.makedirs(dest)
    _write_scratch_verify_commission(dest, NOT_VERIFIED_BODY)
    plan = _build_plan(dest, accept_unverified=False)
    first = CE.execute(plan, dest)
    check("stop-fix-resume: first run halted", not first.completed)
    check("stop-fix-resume: canary absent after the halted run",
          not os.path.isfile(os.path.join(dest, "AFTER_VERIFY_RAN")))

    # THE FIX: an operator who fixed the keys/keyring mismatch re-runs against the SAME
    # destination -- proxied here by rewriting the scratch verify-commission script's own
    # verdict (the REAL binary would now report VERIFIED against the corrected keys/), never
    # touching the journal by hand.
    _write_scratch_verify_commission(dest, VERIFIED_BODY)
    second = CE.execute(plan, dest)
    check("stop-fix-resume: the RESUMED run (same destination, same journal) completed",
          second.completed)
    check("stop-fix-resume: the canary entry ran on resume", os.path.isfile(
        os.path.join(dest, "AFTER_VERIFY_RAN")))
    check("stop-fix-resume: the commit journal is removed once every entry is DONE",
          not os.path.isfile(CE.journal_path(dest)))
    print("  NOTE (scope, honest): this proves the resume property at the commit_executor/"
          "journal layer, using the scratch verify-commission stand-in. A full live-birth "
          "resume through the REAL bootstrap/templates/verify-commission.tmpl (real gpg keygen, "
          "a real mismatched key, a real re-sign) needs a real new-project.sh birth against a "
          "live Postgres substrate -- UNEXERCISED here, out of this fixture's scoped claim, "
          "matching seen-red/setup-tui-signed-genesis-resume/run_fixtures.py's own identical "
          "scoping for its live-DB extended case.")


def case_app_exit_code_control_flow() -> None:
    print("case 5 (GREEN): app.py's non-zero exit on a halted commit (control-flow unit check, "
          "no live TUI needed)")
    halted_screens = [("fake", lambda ui, cl, state: {**state, "commit_halted": True})]
    state_h: dict = {}
    code_halted = APP._drive_screens(None, CK.Checklist(), state_h, [state_h], halted_screens)
    check("app.py: a halted commit -> non-zero exit code (previously always 0)",
          code_halted != 0, code_halted)

    clean_screens = [("fake", lambda ui, cl, state: dict(state))]
    state_c: dict = {}
    code_clean = APP._drive_screens(None, CK.Checklist(), state_c, [state_c], clean_screens)
    check("app.py: a NORMAL run (no commit_halted) -> exit 0, unaffected",
          code_clean == 0, code_clean)

    args = APP.parse_args(["--accept-unverified-genesis"])
    check("app.py: --accept-unverified-genesis parses and is threaded", args.accept_unverified_genesis)


def main() -> int:
    scratch = tempfile.mkdtemp(prefix="setup-tui-genesis-gate-hard-stop-")
    try:
        case_red_prefix_completes_anyway(scratch)
        case_green_post_fix_stops(scratch)
        case_green_override_continues_and_records(scratch)
        case_stop_fix_resume(scratch)
        case_app_exit_code_control_flow()
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    if FAILURES:
        print(f"\n{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nall cases GREEN (or honestly UNEXERCISED)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
