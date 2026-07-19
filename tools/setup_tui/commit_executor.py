# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T19:33:56Z
#   last-change: 2026-07-19T19:48:25Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/commit_executor.py -- THE ONE COMMIT BOUNDARY (design/FABLE-SETUP-TUI-
PURE-CORE-SPEC.md §2.3/§2.6, commission ledger rows 1823 point 2 / 1825).

PHASE-1 FOUNDATION MODULE (builder's report): consumes a `tools.setup_tui.plan.Plan` built by a
(future, not-yet-rewired) pure decision phase and executes its entries in order through the SAME
runner choke points (`tools.setup_tui.runner.run_command` / `write_file` / `start_background`) --
never a second implementation of what those choke points already do (ADR-0012 P1). This module,
plus `tools.setup_tui.screens`'s declared rehearsal exception, is where §2.8's forthcoming AST
purity gate will assert those three names are the ONLY call sites in `tools/setup_tui/` -- not
added yet in this pass, because asserting it now would go red against the still-unconverted
`screens.py` (see the builder's report: landing a gate that is red on `main` is a hazard in its
own right, not a proof).

WHAT THIS MODULE PROVIDES, THAT IS ALREADY LOAD-BEARING FOR THE PROPERTIES SPEC §4 NAMES:

  * **Argv/write parity (WPC2).** `execute()` never re-derives an act's command line -- it calls
    `PlanEntry.act.resolve(bindings)`, the SAME resolution `Plan.render()`'s symbolic form is a
    projection of, so the argv a committed run actually executes is provably the argv the
    pre-commit plan rendering showed (modulo hole substitution, which is the whole point of a
    hole).
  * **Durable commit journal (§2.6, WPC4).** `CommitJournal` is a small JSON file written into
    the DESTINATION directory (the "durable commit journal in the destination naming the next
    step" the envelope promises) -- one line per entry, `PENDING` before an entry's act runs,
    `DONE` immediately after it returns, `fsync`'d so a kill between two entries leaves the
    journal naming exactly the next un-run step. Re-invoking `execute()` on the SAME journal path
    with the SAME plan skips every entry already marked `DONE` and resumes at the first `PENDING`
    one -- per-act atomicity (each act's own choke point, e.g. `write_file`'s atomic rename) plus
    this journal is what the envelope calls "resume, or finish by hand from the journal", never a
    claim of whole-flow atomicity across Postgres+filesystem+GPG+processes (spec §2.6 is explicit
    that whole-flow atomicity is NOT claimed).
  * **Late binding (§2.2, WPC5).** After an entry with `produces=name` runs, its real
    stdout/write-content is recorded in `bindings[name]`; a later entry's `Hole(of=name, ...)`
    resolves against that dict, never before. `bindings` is returned from `execute()` so a caller
    (a future `led show`-driven witness) can confirm a hole resolved to the value the world
    actually recorded.

WHAT THIS MODULE DELIBERATELY DOES NOT DO YET: drive the checklist/`Ui` calls a fully-wired
commit boundary needs (rendering the lesson line, the exact argv, the streamed output, and the
checklist row per entry, per spec §2.3) -- those need the SAME `Ui`/`Checklist` objects the
decision phase used, which only exist once `screens.py`/`app.py` are rewired to build a `Plan`
instead of acting directly. `execute()` accepts optional `on_step` / `on_result` callbacks so that
wiring is additive when it lands (a fully-wired caller passes callbacks that call `ui.say`/
`cl.add`; this module's own unit-level proof, `seen-red/setup-tui-pure-core-foundation/
run_fixtures.py`, passes a recording callback instead of a live `Ui`).
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Callable

from tools.setup_tui import runner
from tools.setup_tui.plan import BackgroundAct, CommandAct, Plan, PlanEntry, WriteAct

JOURNAL_FILENAME = ".setup-tui-commit-journal.json"

PENDING = "PENDING"
DONE = "DONE"


# --------------------------------------------------------------------------------------------
# The durable commit journal (spec §2.6).
# --------------------------------------------------------------------------------------------

@dataclass
class CommitJournal:
    """One JSON file, in the destination directory, naming which plan entry runs next. Written
    with the SAME atomic-replace discipline `runner.write_file` already provides (never a second,
    weaker file-write implementation -- ADR-0012 P1) so the journal itself cannot be the thing a
    kill leaves half-written.

    Shape on disk: `{"entries": ["DONE", "DONE", "PENDING", "PENDING", ...]}`, one status per
    plan entry, same order as `Plan.entries`. `next_index()` is the first `PENDING` index, or
    `None` once every entry is `DONE` (commit complete)."""
    path: str
    statuses: list[str] = field(default_factory=list)

    @classmethod
    def open_or_create(cls, path: str, plan_len: int) -> "CommitJournal":
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            statuses = list(data["entries"])
            if len(statuses) != plan_len:
                raise ValueError(
                    f"commit journal at {path!r} has {len(statuses)} entries but this plan has "
                    f"{plan_len} -- refusing to resume against a MISMATCHED plan (the plan the "
                    f"journal was written for is not the plan being executed now; this is a "
                    f"caller error, never silently guessed at, ADR-0002)"
                )
            return cls(path=path, statuses=statuses)
        j = cls(path=path, statuses=[PENDING] * plan_len)
        j._persist()
        return j

    def next_index(self) -> int | None:
        for i, s in enumerate(self.statuses):
            if s == PENDING:
                return i
        return None

    def mark_done(self, index: int) -> None:
        self.statuses[index] = DONE
        self._persist()

    def remove(self) -> None:
        """Called once every entry is DONE -- a completed commit leaves no journal behind (the
        journal's whole purpose is naming the NEXT step of an INCOMPLETE commit; a finished one
        has no next step, and a stale completed-journal file lying around would falsely suggest
        an in-progress commit to the next invocation)."""
        if os.path.isfile(self.path):
            os.remove(self.path)

    def _persist(self) -> None:
        # Same atomic-rename discipline as runner.write_file (ledger row 1810's fix), inlined
        # here rather than imported: runner.write_file's signature is (path, content-as-str,
        # dry_run=) with no caller-visible "this write must never be skipped" guarantee, and a
        # commit journal write is NEVER a dry-run act (there is no dry-run commit phase at all,
        # spec §2.4 -- a dry run IS the decision phase, absent the one act that commits) so
        # threading a dry_run parameter through here would be a dead parameter, not a shared
        # choke point. Kept as its OWN tiny atomic-write rather than a second call path into
        # runner.write_file so that module's docstring claim ("the ONE place this package writes
        # a file directly, besides the checklist save") stays true of THAT module; this journal
        # write is the commit executor's own, equally-atomic, mechanism.
        directory = os.path.dirname(self.path) or "."
        content = json.dumps({"entries": self.statuses}, indent=2) + "\n"
        with tempfile.NamedTemporaryFile(
            "w", dir=directory, prefix=f".{os.path.basename(self.path)}.", suffix=".tmp",
            delete=False, encoding="utf-8",
        ) as tf:
            tf.write(content)
            tf.flush()
            os.fsync(tf.fileno())
            tmp_path = tf.name
        os.chmod(tmp_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        os.replace(tmp_path, self.path)


def journal_path(dest: str) -> str:
    return os.path.join(dest, JOURNAL_FILENAME)


# --------------------------------------------------------------------------------------------
# Execution result
# --------------------------------------------------------------------------------------------

@dataclass
class EntryResult:
    entry: PlanEntry
    ok: bool
    detail: str


@dataclass
class ExecutionResult:
    bindings: dict[str, str]
    entry_results: list[EntryResult]
    completed: bool  # True iff every entry reached DONE (no failure halted the run)
    # PHASE-2 ADDITION (screens.py's boundary screen needs a live handle on a started background
    # process -- for the SIGTERM/abnormal-exit cleanup app.py already provides via
    # `state["boundary_proc"]`, and because a `BackgroundAct` is the one act type that leaves
    # something RUNNING rather than completing, this module is the only place that ever sees the
    # real `Popen` object. Keyed by the entry's own `produces` name (a `BackgroundAct` entry with
    # no `produces` set is not retrievable this way -- a caller that needs the handle sets one,
    # same as any other binding). Never populated for a RESUMED already-DONE entry -- a process
    # from a prior invocation cannot be handed back across process boundaries, exactly like a
    # binding this module "cannot re-derive" per `execute`'s own late-binding-replay comment.
    background_procs: dict[str, "subprocess.Popen"] = field(default_factory=dict)


OnStep = Callable[[int, PlanEntry], None]
OnResult = Callable[[int, PlanEntry, EntryResult, "subprocess.Popen | None"], None]


def execute(
    plan: Plan,
    dest: str,
    *,
    on_step: OnStep | None = None,
    on_result: OnResult | None = None,
) -> ExecutionResult:
    """The ONE commit boundary (spec §2.3): runs every entry of `plan`, in order, through the
    SAME runner choke points, resuming from `dest`'s own commit journal if one already exists
    (a re-entry after a mid-commit kill, WPC4). Stops at the FIRST entry whose act does not
    succeed (`ok=False`) -- per-act atomicity means that entry's own effect either fully happened
    or fully didn't (never partial), but the COMMIT as a whole is not further attempted past a
    failure; the journal is left naming that same still-PENDING entry as the next step, exactly
    what a human finishing by hand, or a corrected re-invocation, needs.

    `on_step`/`on_result`, if given, are called immediately before/after each entry's act runs --
    the seam a fully-wired caller (once `screens.py`/`app.py` build a `Plan` instead of acting
    directly) uses to drive `ui.say`/`cl.add` with the SAME (screen, item) pairs the plan carries,
    per spec §2.3's "checklist per entry" and the lesson-line-at-execution-time rule. Neither
    callback may raise for a reason internal to this function's own control flow -- an exception
    from a callback propagates, which is the correct behavior (a UI callback that crashes should
    stop the commit exactly like a genuine bug would, not be swallowed).

    PHASE-2 FIX (caught live against real Postgres + a real boundary_service, seen-red/setup-tui-
    boundary-proc-cleanup): `on_result`'s FOURTH argument is the entry's own started `Popen`
    (`None` for anything but a just-succeeded `BackgroundAct`) -- passed DIRECTLY, at the moment
    of the callback, rather than only being recoverable from this function's own RETURN VALUE
    (`ExecutionResult.background_procs`). A caller that needs the handle to survive a LATER
    entry's crash (screens.py's own `state["boundary_proc"]`, read by app.py's abnormal-exit
    cleanup) cannot wait for `execute()` to return -- if a later on_result callback itself raises,
    `execute()` never returns at all, and the handle recorded only in its local scope is lost with
    it. Passing the proc through the callback closes that gap."""
    os.makedirs(dest, exist_ok=True)
    journal = CommitJournal.open_or_create(journal_path(dest), len(plan.entries))
    bindings: dict[str, str] = {}
    background_procs: dict[str, subprocess.Popen] = {}
    entry_results: list[EntryResult] = [
        EntryResult(entry=e, ok=(s == DONE), detail="(resumed: already DONE)" if s == DONE else "")
        for e, s in zip(plan.entries, journal.statuses)
    ]

    # Late-binding replay (spec §2.2/WPC5): on a RESUMED run, entries already marked DONE never
    # re-execute (per-act atomicity already happened for them in a prior invocation), but any
    # `produces` binding they contributed must still be populated before a later PENDING entry's
    # hole can resolve against it. Since a completed act's real output is not re-derivable from
    # the journal alone (the journal records status, not content -- content lives wherever the
    # act itself wrote it, e.g. the destination's own ledger), a resumed run's bindings are
    # reconstructed by RE-READING each DONE entry's real effect, the same way a fresh witness
    # would (e.g. `led show` for a row id) -- this is the caller's job for entries the caller
    # knows how to re-derive; entries this module cannot re-derive on its own are surfaced as a
    # missing binding, which fails LOUD the moment a later hole actually needs it (never silently
    # guessed), rather than this function inventing a value.
    start = journal.next_index()
    if start is None:
        journal.remove()
        return ExecutionResult(bindings=bindings, entry_results=entry_results, completed=True,
                                background_procs=background_procs)

    for i in range(start, len(plan.entries)):
        entry = plan.entries[i]
        if on_step is not None:
            on_step(i, entry)
        result, proc = _run_entry(entry, bindings, dest)
        entry_results[i] = result
        if proc is not None and entry.produces is not None:
            background_procs[entry.produces] = proc
        # ORDER IS LOAD-BEARING (a real ordering hazard caught in this module's own build, not a
        # hypothetical): the journal is marked DONE for entry `i` IMMEDIATELY after its act
        # actually ran (and, if it succeeded, its binding recorded) -- BEFORE `on_result` is
        # invoked. `on_result` is a caller-supplied UI callback (`ui.say`/`cl.add` once wired) and
        # may raise for reasons that have nothing to do with whether the act itself succeeded (a
        # rendering bug, a broken terminal). If the journal were marked done AFTER that callback,
        # a callback exception right after a REAL write/command/background-start already happened
        # would leave the journal still naming that same entry PENDING -- a resumed run would then
        # RE-RUN an act that already, truly, took effect: a double keygen, a double `led decision`
        # write, a second `CREATE ROLE`. Marking done first means the journal's truth tracks the
        # ACT, never the UI layer on top of it; per-act atomicity (each choke point's own
        # all-or-nothing contract) is what makes marking done immediately after the act, rather
        # than after every consumer of its result has also succeeded, correct.
        if result.ok:
            if entry.produces is not None:
                bindings[entry.produces] = result.detail
            journal.mark_done(i)
        if on_result is not None:
            on_result(i, entry, result, proc)
        if not result.ok:
            return ExecutionResult(bindings=bindings, entry_results=entry_results, completed=False,
                                    background_procs=background_procs)

    journal.remove()
    return ExecutionResult(bindings=bindings, entry_results=entry_results, completed=True,
                            background_procs=background_procs)


def _run_entry(entry: PlanEntry, bindings: dict[str, str],
                dest: str) -> tuple[EntryResult, "subprocess.Popen | None"]:
    act = entry.act
    if isinstance(act, CommandAct):
        argv, stdin_text = act.resolve(bindings)
        res = runner.run_command(argv, cwd=act.cwd, env=act.resolve_env(), stdin_text=stdin_text)
        return EntryResult(entry=entry, ok=res.ok, detail=res.output), None
    if isinstance(act, WriteAct):
        path, content = act.resolve(bindings)
        wrote = runner.write_file(path, content)
        return EntryResult(entry=entry, ok=wrote, detail=content), None
    if isinstance(act, BackgroundAct):
        argv = act.resolve(bindings)
        bg = runner.start_background(argv, cwd=act.cwd)
        started = bg.proc is not None
        detail = f"pid {bg.proc.pid}" if started else "(background start failed: no process)"
        return EntryResult(entry=entry, ok=started, detail=detail), bg.proc
    raise TypeError(f"unrecognized plan act type: {type(act)!r}")  # pragma: no cover -- exhaustive
