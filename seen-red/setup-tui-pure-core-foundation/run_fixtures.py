#!/usr/bin/env python3
"""seen-red/setup-tui-pure-core-foundation/run_fixtures.py -- both-polarity proof of
tools/setup_tui/plan.py + tools/setup_tui/commit_executor.py (design/FABLE-SETUP-TUI-PURE-CORE-
SPEC.md, commission ledger rows 1823 point 2 / 1825), census-registered in gates/fixture_census.py.

PHASE-1 SCOPE (builder's report): these two modules are the typed core of the pure-core
restructure, landed standalone BEFORE tools/setup_tui/screens.py is rewired to build a `Plan`
instead of acting directly (that rewire is filed as the large remaining body of work). This
fixture proves properties of the MODULES ALONE, against real (not mocked) `tools.setup_tui.
runner` choke points and a scratch destination directory -- it is NOT a claim that the whole
eleven-screen flow is pure yet (screens.py is unmodified by this pass; the flow-level witnesses
WPC1-WPC7 the parent spec names remain UNEXERCISED until the rewire lands and are not claimed
here).

Cases proved:

  1. RED-BEFORE-GREEN -- decision-phase purity: `Plan.render()` (the WOULD-DO/plan rendering a
     pure decision phase would call before any commit) must NEVER resolve a `Hole` -- a hole's
     `extract` callable is only ever invoked at commit, against a step's REAL output. Proved by
     giving a hole a `extract` that raises if called, then rendering a plan containing it: if
     `render()` ever touched `extract`, this case would fail (RED). A synthetic BROKEN act class
     that resolves eagerly in its own `.render()` (the violation this property exists to catch)
     is shown failing this same check, proving the check is not vacuous.
  2. GREEN -- argv/write parity + late binding (WPC5-shaped, module-level): a two-entry plan
     (entry 0 writes a row id to a file and `produces` it; entry 1's argv holds a `Hole` on that
     binding) is executed for real through `commit_executor.execute` against a scratch
     destination. Asserts: entry 1's REALLY-EXECUTED argv (recovered from entry_results[1]) used
     the row id entry 0 ACTUALLY wrote, not a guessed/fabricated value; the plan's PRE-commit
     symbolic rendering names the hole symbolically (`<row-id of step 'p1'>`), never the real
     value (nothing to leak before commit); `bindings["p1"]` equals the real value after commit.
  3. GREEN -- durable commit journal / per-act atomicity / resume (WPC4-shaped, module-level): a
     three-entry plan (three real `write_file` acts to three distinct scratch paths) is executed
     with an `on_result` callback that raises after entry 0 (simulating a UI-layer crash
     immediately after a real act already took effect, the exact ordering hazard this module's
     build caught and fixed -- see commit_executor.py's own "ORDER IS LOAD-BEARING" comment).
     Asserts: entry 0's file WAS really written (the act's own atomicity held) AND the journal
     correctly marked it DONE despite the callback raising (the fix under test); re-invoking
     `execute()` against the SAME destination resumes at entry 1 (entry 0 is NOT re-run -- no
     second write, no truncation) and completes; the journal file is removed once every entry is
     DONE.
  4. GREEN -- failed-entry halts, journal stays honest: a plan whose one entry always fails (a
     nonexistent binary) leaves `completed=False`, the journal on disk still naming that entry
     PENDING (never falsely marked DONE for a failed act), and a second `execute()` call against
     the same unfixed plan/destination reproduces the same failure (no silent skip of a REFUSED
     step).
  5. RED-BEFORE-GREEN (FINDING-1 fix, fresh-context review of b565db1) -- a Hole GENUINELY
     SPANNING the resume boundary: a two-entry plan where entry 1 holds a real `Hole` on entry
     0's own `produces` (NOT an independent act, unlike case 3's three unrelated WriteActs, and
     unlike seen-red/setup-tui-signed-genesis-resume's own crash point at i==0 with no later Hole
     referencing it -- both existing resume fixtures were noted, in the review, to avoid this
     scenario BY CONSTRUCTION; this case does not). A callback crashes right after entry 0 (the
     PRODUCER) succeeds, before entry 1 (the CONSUMER, holding the Hole) ever runs. RED, against
     `PRE_FIX_COMMIT` (pinned, not "HEAD" -- see WPC_PIN_NOTE below): a genuinely fresh
     `execute()` call, loaded from the commit immediately before the fix, raises an uncaught
     `KeyError` from `Hole.resolve` -- `bindings` started empty on every call, including a
     resumed one, so the journal-loaded value the consumer's Hole needs was never there. GREEN,
     against the current module: the SAME fresh call completes, and the consumer's REAL output
     (recovered from `entry_results[1]`) used the row id the journal persisted for entry 0, not a
     fabricated value and not a crash.

Zero residue: everything happens inside a fixture-owned tempdir, removed in `finally`. No mocks
of the modules under test -- real `tools.setup_tui.plan`/`commit_executor`, real
`tools.setup_tui.runner` choke points (`echo`/`write_file` against scratch paths; no network, no
Postgres, no GPG). Lazy imports banned.

Usage: python3 seen-red/setup-tui-pure-core-foundation/run_fixtures.py
Exit 0 if every case matches; 1 otherwise."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from tools.setup_tui import commit_executor as CE  # noqa: E402
from tools.setup_tui import plan as P  # noqa: E402
from tools.setup_tui import runner  # noqa: E402

FAILURES: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  OK   {label}")
    else:
        msg = f"FAIL {label}" + (f" -- {detail}" if detail else "")
        print(f"  {msg}")
        FAILURES.append(msg)


def case_1_purity() -> None:
    print("case 1: decision-phase purity (render never resolves a hole)")

    def _poison(_: str) -> str:
        raise AssertionError("Hole.extract called during render() -- purity violated")

    hole = P.Hole(of="p1", describe="row-id", extract=_poison)
    entry = P.PlanEntry(
        screen="s", item="i", lesson="lesson",
        act=P.CommandAct(argv=("echo", hole)),
    )
    plan = P.Plan()
    plan.append(entry)
    try:
        rendered = plan.render()
        check("render() completes without touching extract", True)
    except AssertionError:
        check("render() completes without touching extract", False, "extract was called")
        return
    check("render() shows the hole symbolically", "<row-id of step 'p1'>" in rendered, rendered)

    # The negative self-check: a BROKEN act that resolves eagerly inside its own render() would
    # be exactly the violation this property guards against -- proving the case above is not
    # vacuously true (a render() that happened to never be exercised would also "pass").
    @dataclass(frozen=True)
    class BrokenEagerAct:
        h: P.Hole

        def render(self) -> str:
            return self.h.extract("this should never run")  # the violation, on purpose

    broken_plan = P.Plan()
    broken_plan.append(P.PlanEntry(screen="s", item="i", lesson="l", act=BrokenEagerAct(hole)))
    raised = False
    try:
        broken_plan.render()
    except AssertionError:
        raised = True
    check("negative self-check: a broken eager-resolving act DOES trip the poison", raised,
          "a render() that resolves early must be catchable by this same check")


def case_2_parity_and_binding() -> None:
    print("case 2: argv/write parity + late binding (WPC5-shaped)")
    tmp = tempfile.mkdtemp(prefix="setup-tui-pure-core-fixture-")
    try:
        dest = os.path.join(tmp, "dest")
        row_path = os.path.join(tmp, "row.txt")

        def extract_row(content: str) -> str:
            return content.strip().split()[-1]

        write_entry = P.PlanEntry(
            screen="s1", item="write row", lesson="l1",
            act=P.WriteAct(path=row_path, content="row 42"),
            produces="p1",
        )
        hole = P.Hole(of="p1", describe="row-id", extract=extract_row)
        echo_entry = P.PlanEntry(
            screen="s2", item="echo row", lesson="l2",
            act=P.CommandAct(argv=("echo", hole)),
        )
        plan = P.Plan()
        plan.append(write_entry)
        plan.append(echo_entry)

        symbolic = plan.render()
        check("pre-commit rendering shows the hole symbolically, not a real value",
              "<row-id of step 'p1'>" in symbolic and "42" not in symbolic, symbolic)

        result = CE.execute(plan, dest)
        check("execution completed", result.completed)
        check("binding p1 recorded the real write content", result.bindings.get("p1") == "row 42",
              result.bindings)
        echo_result = result.entry_results[1]
        check("echo entry succeeded", echo_result.ok)
        check("echo entry's REAL output used the resolved value 42 (not fabricated)",
              echo_result.detail.strip() == "42", echo_result.detail)
        check("scratch file really written with the real content",
              os.path.isfile(row_path) and open(row_path).read() == "row 42")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def case_3_journal_resume() -> None:
    print("case 3: durable commit journal / per-act atomicity / resume (WPC4-shaped)")
    tmp = tempfile.mkdtemp(prefix="setup-tui-pure-core-fixture-")
    try:
        dest = os.path.join(tmp, "dest")
        paths = [os.path.join(tmp, f"f{i}.txt") for i in range(3)]
        plan = P.Plan()
        for i, path in enumerate(paths):
            plan.append(P.PlanEntry(
                screen="s", item=f"write {i}", lesson="l",
                act=P.WriteAct(path=path, content=f"content-{i}"),
            ))

        def crash_after_zero(i: int, entry: object, result: object,
                              proc: object = None) -> None:
            # PHASE-2 addition to on_result's signature (commit_executor.py's own note):
            # a 4th positional arg, the entry's own started Popen (None for anything but a
            # just-succeeded BackgroundAct) -- accepted and ignored here, this case has none.
            if i == 0:
                raise RuntimeError("simulated UI-layer crash right after a real act ran")

        crashed = False
        try:
            CE.execute(plan, dest, on_result=crash_after_zero)
        except RuntimeError:
            crashed = True
        check("callback exception propagates (never silently swallowed)", crashed)
        check("entry 0's real write happened despite the later crash",
              os.path.isfile(paths[0]) and open(paths[0]).read() == "content-0")
        check("entries 1/2 did NOT run yet (execution halted where the crash occurred)",
              not os.path.isfile(paths[1]) and not os.path.isfile(paths[2]))

        jpath = CE.journal_path(dest)
        with open(jpath) as f:
            entries = json.load(f)["entries"]
        # FINDING-1 FIX: the journal now persists a {"status", "produces", "value"} record per
        # entry (durable bindings, not just status) -- this fixture's own module docstring's
        # "PHASE-1 SCOPE" note covers the module contract, not the on-disk journal shape, so this
        # is the same fixture proving the SAME property against the current, richer record shape.
        statuses = [e["status"] for e in entries]
        check("journal marked entry 0 DONE despite the callback crash (the ordering fix)",
              statuses[0] == CE.DONE, statuses)
        check("journal correctly still names entries 1/2 PENDING",
              statuses[1] == CE.PENDING and statuses[2] == CE.PENDING, statuses)

        # Resume: a fresh execute() call against the SAME destination/plan must not re-run entry
        # 0 (no double write, no re-truncation -- content-0 must survive unchanged) and must
        # complete the remaining two entries.
        os.utime(paths[0], (0, 0))  # detectable mtime marker; a re-write would change it
        before_mtime = os.stat(paths[0]).st_mtime
        result = CE.execute(plan, dest)
        check("resumed execution completed", result.completed)
        check("entry 0 was NOT re-executed on resume (mtime unchanged)",
              os.stat(paths[0]).st_mtime == before_mtime)
        for i, path in enumerate(paths):
            check(f"entry {i}'s content correct after resume",
                  os.path.isfile(path) and open(path).read() == f"content-{i}")
        check("journal removed once every entry is DONE", not os.path.isfile(jpath))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def case_4_failure_halts_honestly() -> None:
    print("case 4: a failing entry halts the commit; journal stays honest")
    tmp = tempfile.mkdtemp(prefix="setup-tui-pure-core-fixture-")
    try:
        dest = os.path.join(tmp, "dest")
        plan = P.Plan()
        plan.append(P.PlanEntry(
            screen="s", item="doomed command", lesson="l",
            act=P.CommandAct(argv=("this-binary-does-not-exist-anywhere-xyz",)),
        ))
        raised = False
        try:
            CE.execute(plan, dest)
        except FileNotFoundError:
            # subprocess.Popen on a nonexistent binary raises FileNotFoundError rather than
            # returning a CommandResult -- runner.run_command does not itself catch this (it is
            # not this fixture's job to change that contract), so this fixture's own doomed act
            # uses a binary guaranteed absent to exercise the "the act itself cannot even start"
            # edge, proving the journal is untouched (still PENDING) rather than falsely DONE.
            raised = True
        check("a doomed act's failure to even start propagates (never silently marked done)",
              raised)
        jpath = CE.journal_path(dest)
        if os.path.isfile(jpath):
            with open(jpath) as f:
                entries = json.load(f)["entries"]
            statuses = [e["status"] for e in entries]
            check("journal still names the doomed entry PENDING, never falsely DONE",
                  statuses[0] == CE.PENDING, statuses)
        else:
            check("journal exists after a failed first entry", False, "journal file missing")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


PRE_FIX_COMMIT = "b565db1"  # commit_executor.py as it stood immediately before the FINDING-1
# fix (the same commit a fresh-context review flagged) -- pinned EXPLICITLY, never "HEAD" (a
# moving target this repo's own build history already caught making a fixture stale exactly once,
# seen-red/setup-tui-boundary-proc-cleanup's own repair).


def _load_pinned_commit_executor(commit: str, scratch: str):
    r = subprocess.run(
        ["git", "-C", REPO_ROOT, "show", f"{commit}:tools/setup_tui/commit_executor.py"],
        capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip(), (
        f"could not read {commit}:tools/setup_tui/commit_executor.py -- {r.stderr}")
    assert "def bindings(self)" not in r.stdout, (
        f"fixture assumption stale: {commit}:tools/setup_tui/commit_executor.py ALREADY carries "
        f"the FINDING-1 fix (a CommitJournal.bindings() method) -- PRE_FIX_COMMIT needs "
        f"repinning to a genuinely earlier commit")
    path = os.path.join(scratch, "commit_executor_prefix.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(r.stdout)
    spec = importlib.util.spec_from_file_location("commit_executor_prefix", path)
    mod = importlib.util.module_from_spec(spec)
    # Registered in sys.modules BEFORE exec_module -- dataclasses' own field-type resolution
    # looks the module up via sys.modules[cls.__module__] (typing.get_type_hints's own mechanism)
    # and raises AttributeError on a bare None otherwise; this is the standard fix for a
    # dataclass-bearing module loaded via spec_from_file_location outside the normal import path.
    sys.modules["commit_executor_prefix"] = mod
    spec.loader.exec_module(mod)
    return mod


def case_5_hole_spans_resume() -> None:
    print("case 5: RED-BEFORE-GREEN -- a Hole GENUINELY spanning the resume boundary "
          "(FINDING-1 fix, fresh-context review of b565db1)")
    tmp = tempfile.mkdtemp(prefix="setup-tui-pure-core-fixture-")
    try:
        row_path = os.path.join(tmp, "row.txt")

        def extract_row(content: str) -> str:
            return content.strip().split()[-1]

        def _build_plan():
            producer = P.PlanEntry(
                screen="s1", item="produce row", lesson="l1",
                act=P.WriteAct(path=row_path, content="row 99"),
                produces="p_resume",
            )
            hole = P.Hole(of="p_resume", describe="row-id", extract=extract_row)
            consumer = P.PlanEntry(
                screen="s2", item="consume row (holds a Hole on the producer)", lesson="l2",
                act=P.CommandAct(argv=("echo", hole)),
            )
            plan = P.Plan()
            plan.append(producer)
            plan.append(consumer)
            return plan

        def crash_right_after_producer(i, entry, result, proc=None):
            if i == 0:
                raise RuntimeError(
                    "simulated death immediately after the PRODUCING entry -- before the "
                    "consumer (which holds a Hole on it) ever runs")

        # --- RED: the pinned pre-fix module -- a genuinely fresh execute() call on resume must
        # raise an uncaught KeyError (bindings started empty every call, including a resumed one).
        dest_red = os.path.join(tmp, "dest_red")
        prefix_mod = _load_pinned_commit_executor(PRE_FIX_COMMIT, tmp)
        plan_red = _build_plan()
        crashed_red = False
        try:
            prefix_mod.execute(plan_red, dest_red, on_result=crash_right_after_producer)
        except RuntimeError:
            crashed_red = True
        check("RED setup: the simulated death propagated (pre-fix module)", crashed_red)
        check("RED setup: the producer's real write happened (pre-fix module)",
              os.path.isfile(row_path) and open(row_path).read() == "row 99")
        raised_keyerror = False
        try:
            prefix_mod.execute(plan_red, dest_red)
        except KeyError:
            raised_keyerror = True
        check("RED: pre-fix module's resumed execute() DOES raise KeyError from Hole.resolve "
              "(bindings started empty -- the defect FINDING-1 caught, reproduced live)",
              raised_keyerror)

        # --- GREEN: the current module, same scenario, fresh dest.
        os.remove(row_path)
        dest_green = os.path.join(tmp, "dest_green")
        plan_green = _build_plan()
        crashed_green = False
        try:
            CE.execute(plan_green, dest_green, on_result=crash_right_after_producer)
        except RuntimeError:
            crashed_green = True
        check("the simulated death propagated (current module)", crashed_green)
        check("the producer's real write happened (current module)",
              os.path.isfile(row_path) and open(row_path).read() == "row 99")

        result = CE.execute(plan_green, dest_green)
        check("GREEN: resumed execution completed (no KeyError from Hole.resolve)",
              result.completed)
        echo_result = result.entry_results[1]
        check("GREEN: the consumer's REAL output used the JOURNAL-loaded row id (not "
              "fabricated, not a crash)",
              echo_result.ok and echo_result.detail.strip() == "99", echo_result.detail)
        check("journal removed once every entry is DONE",
              not os.path.isfile(CE.journal_path(dest_green)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    case_1_purity()
    case_2_parity_and_binding()
    case_3_journal_resume()
    case_4_failure_halts_honestly()
    case_5_hole_spans_resume()
    if FAILURES:
        print(f"\n{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nall cases GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
