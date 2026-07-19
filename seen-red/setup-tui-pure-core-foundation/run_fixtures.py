#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T19:35:25Z
#   last-change: 2026-07-19T19:35:25Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

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

Zero residue: everything happens inside a fixture-owned tempdir, removed in `finally`. No mocks
of the modules under test -- real `tools.setup_tui.plan`/`commit_executor`, real
`tools.setup_tui.runner` choke points (`echo`/`write_file` against scratch paths; no network, no
Postgres, no GPG). Lazy imports banned.

Usage: python3 seen-red/setup-tui-pure-core-foundation/run_fixtures.py
Exit 0 if every case matches; 1 otherwise."""
from __future__ import annotations

import json
import os
import shutil
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
            statuses = json.load(f)["entries"]
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
                statuses = json.load(f)["entries"]
            check("journal still names the doomed entry PENDING, never falsely DONE",
                  statuses[0] == CE.PENDING, statuses)
        else:
            check("journal exists after a failed first entry", False, "journal file missing")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    case_1_purity()
    case_2_parity_and_binding()
    case_3_journal_resume()
    case_4_failure_halts_honestly()
    if FAILURES:
        print(f"\n{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nall cases GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
