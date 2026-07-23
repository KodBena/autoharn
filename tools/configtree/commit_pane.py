#!/usr/bin/env python3
"""tools/configtree/commit_pane.py -- `CommitPane`, split out of `panes.py` on ADR-0007 grounds
(no file over 400 lines, `gates/max_lines.py`'s own ratcheting-baseline gate: this package has no
baselined entry, so growth over 400 is refused outright, not merely reviewed) -- the off-UI-
thread worker fix (ledger row 1130's own sibling audit) pushed `panes.py` from 288 to 432 lines.
`SectionPane` (the per-section form) stays in `panes.py`; this is the ONE generic commit node
(design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3 v2), App-adjacent like its former sibling."""
from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Button, Static
from textual.worker import Worker, get_current_worker

from tools.configtree.layout_primitives import ContentHorizontal
from tools.configtree.spec import CommitSpec, ready_for_commit, section_answers


class CommitPane(Vertical):
    """The library's own generic commit node (spec §3 v2): the resolved decision set, ONE commit
    confirmation -- the ONLY action button in the app besides quit. Pressing it runs the FULL
    two-phase sequence: every section's `submit` exactly once, in registry order (the live-model
    rebuild's own deferred business-logic pass -- see `panes.py`'s own module docstring), THEN,
    only if every section accepted, the actual commit boundary (`CommitSpec.commit`). A section
    that REFUSES at this point (a business-rule check no field-level validator could see) halts
    the sweep before any commit act runs, records the refusal into `state["_commit_errors"]` (so
    the tree reads that section INVALID with the reason), and re-enables this button for a retry.

    OFF THE UI THREAD (audit finding, ledger row 1130's own sibling audit; ADR-0019 C24/C26/C9):
    the sweep calls every section's own `submit` -- real subprocesses (`git`), a real 5s-timeout
    network probe (`probes.pg_reachable`), and, once the sweep clears, the actual commit act
    (`CommitSpec.commit` -- autoharn's own `steps.commit`, which drives the live scaffold via
    `commit_executor.execute`) -- ALL of which used to run synchronously inside this Button's own
    `Pressed` handler, freezing the entire shell (no keypress, no redraw, no cancel) for however
    long the slowest probe/subprocess/scaffold act took. FIXED: `_run_commit_and_sweep` is a
    `@work(thread=True)` method (Textual's own sanctioned "blocking IO belongs in a worker"
    idiom, C24's Textual substrate note) -- the pure business logic (`_run_submit_sweep`/
    `commit_spec.commit`) still touches ONLY the shared `state` dict, never a widget, from that
    background thread; every widget mutation (busy chrome, mounted result lines, the tree/status
    recompute) is marshalled back via `App.call_from_thread` (verified empirically against the
    installed Textual version: it accepts a plain callable OR an async one, dispatched onto the
    main event loop). CANCELLATION (C9): a genuinely clean cancel exists BETWEEN sections -- the
    worker checks `Worker.is_cancelled` before each section's own `submit` and, once more, after
    the sweep clears but BEFORE the real commit act starts, so a cancel pressed any time up to
    that point stops the run with zero side effect recorded. Past that point this is HONESTLY
    NOT CANCELLABLE: `commit_spec.commit` is the live scaffold act itself (subprocesses, file
    writes, in some paths a running boundary service) and neither this library nor its one
    consumer has ever implemented mid-act rollback for it -- faking a cancel there would either
    hang waiting for an act that does not check any token, or abandon a partially-applied commit
    with no journal entry, which is worse than not offering cancel at all. The existing halted-
    commit recovery path (`steps.commit`'s own docstring: "re-run this tool against the same
    destination to resume") is the honest answer for that window, unchanged by this fix.

    MID-SECTION CANCELLATION TOKEN (cycle-4 audit finding 1, ledger rows 1124/1133 -- the ONE
    MINOR the converged audit/fix loop left): the paragraph above ("Cancel is honored between
    sections") was true but incomplete -- ONE section's own `submit` (autoharn's
    `rehearsal_submit`, the one declared exception besides commit itself that shells out live,
    mid-flow) can itself run tens of seconds (witnessed: ~61s for one real, non-dry-run
    rehearsal), and for that whole window Cancel was enabled and clickable but structurally
    inert -- the flag it set had no effect until that already-running child exited on its own.
    FIXED at the real layer, not by narrowing the disclaimer: this class, right before starting
    the worker (`on_button_pressed`), stashes two callables into the SAME shared `state` dict
    the sweep already touches -- `state["_cancel_check"]` (`() -> bool`, reads THIS worker's own
    `is_cancelled`) and `state["_cancel_note"]` (`(str) -> None`, updates the busy text via
    `call_from_thread`, so a section that keeps running past a cancel press -- teardown, below
    -- can say so live rather than leaving the indicator looking frozen). `rehearsal_submit`
    threads `_cancel_check` into `runner.run_command`'s new `cancel_check` parameter for its
    scratch-birth subprocess call ONLY (never its own teardown call -- residue safety: a birth
    cancelled mid-run may already have created a live scratch world/db, and teardown must still
    run to completion to clean that up, exactly the self-cleaning contract this whole section
    exists to prove holds); `run_command` polls that callable while the child is running and, on
    a positive poll, SIGTERMs the child, waits up to 5s, then SIGKILLs it -- a REAL stop of the
    in-flight process, not a flag nobody reads until the process was going to exit anyway.
    `_run_submit_sweep` (below) now also checks `worker.is_cancelled` right AFTER each section's
    `submit` returns (previously only BEFORE) -- a section that detected and honored a mid-run
    cancel already recorded its own honest `checklist.CANCELLED` rows (a new, dedicated status,
    never a `REFUSED` reuse -- the same closed-vocabulary discipline `checklist.NOT_UP` was
    added under); the sweep itself then treats that exactly like the pre-existing between-
    sections cancel path (`_finish_cancelled`), not a refusal-to-retry, so this class did not
    need a new SectionResult shape to tell the two apart. No other section's `submit` reaches a
    long-running subprocess mid-flow today (grepped: `birth_submit` only QUEUES a `PlanEntry`
    for the real, honestly-non-cancellable commit act; every other section's own subprocess use
    is a `subprocess.run` bounded by a short probe timeout, already well under C9's ~10s
    threshold) -- this fix reaches exactly the one place the audit found the gap, not a
    speculative general mechanism nothing yet needs."""

    def __init__(self, commit: CommitSpec, sections: tuple, state: dict) -> None:
        super().__init__(id="pane-commit")
        self.commit_spec = commit
        self.sections = sections
        self.state = state
        self._committed = False
        # NAMED DISTINCTLY FROM `_running` (verified empirically: `textual.message_pump.
        # MessagePump.__init__` ALREADY owns a plain instance attribute called `self._running`,
        # flipped True the instant this widget's own message pump starts -- essentially always
        # True once mounted, nothing to do with whether a commit sweep is in flight. An earlier
        # draft of this fix named the sweep flag `_running` and silently inherited/clobbered the
        # SAME dict slot the framework already writes, permanently reading True from the moment
        # of mount -- the commit button never got a first real press through. `_sweep_running`
        # cannot collide with any base-class attribute by construction (grepped, empirically,
        # against the installed Textual version).
        self._sweep_running = False
        self._worker: "Worker | None" = None

    def compose(self) -> ComposeResult:
        yield Static("Review & commit", classes="ct-section-title")
        with VerticalScroll(id="ct-commit-body", classes="ct-section-body"):
            yield Static(self.commit_spec.render_summary(self.state), id="ct-commit-summary")
            sweep_error = self.state.get("_commit_sweep_error")
            if sweep_error:
                yield Static(sweep_error, classes="ct-blocked-reason")
        ready = ready_for_commit(self.sections, self.state)
        with ContentHorizontal(classes="ct-section-buttons"):
            label = self.commit_spec.confirm_label if ready else \
                f"{self.commit_spec.confirm_label} (blocked -- sections incomplete)"
            yield Button(label, id="ct-commit", variant="primary", disabled=not ready)
            yield Button("Cancel", id="ct-commit-cancel", variant="warning", disabled=True)
        busy = Static("", id="ct-commit-busy", classes="ct-commit-busy")
        busy.display = False
        yield busy

    @property
    def is_committed(self) -> bool:
        return self._committed

    @property
    def is_commit_running(self) -> bool:
        """Deliberately NOT named `is_running` -- `Widget`/`MessagePump` (a base class) already
        publish a property of that exact name with a DIFFERENT meaning (message-pump-active,
        essentially always True once mounted; see `__init__`'s own note on `_sweep_running`).
        Shadowing it with sweep semantics would work for THIS class's own callers but risks
        confusing anything upstream in Textual that reads `.is_running` off a generic `Widget`
        expecting the base meaning -- a new, unambiguous name costs nothing and removes the
        landmine entirely."""
        return self._sweep_running

    async def refresh_readiness(self) -> None:
        await self.recompose()

    def _set_busy(self, busy: bool, *, text: str = "") -> None:
        """The ONE place the busy chrome (C26: 'every operation past ~1s shows a busy
        indicator') is toggled -- called only on the main thread (either directly, from the
        button-press handler, or via `call_from_thread` from the worker's own completion). The
        commit button is disabled the ENTIRE time a run is in flight (never just during the
        final commit act) -- a second press mid-sweep would replay `submit` concurrently with
        the first pass, corrupting the SAME accumulators (`_plan`/`_checklist`) both passes
        write into."""
        self._sweep_running = busy
        try:
            self.query_one("#ct-commit", Button).disabled = busy or self._committed
            self.query_one("#ct-commit-cancel", Button).disabled = not busy
            indicator = self.query_one("#ct-commit-busy", Static)
            indicator.display = busy
            if busy:
                indicator.update(text or "working -- this can take a while (network probes, "
                                  "subprocesses); Cancel is honored between sections AND, for "
                                  "the one section that shells out live mid-flow, DURING it "
                                  "too (the in-flight child is actually terminated) -- never "
                                  "mid-commit-act (see this pane's own docstring)")
        except Exception:  # noqa: BLE001 -- the pane may already be gone (app exiting mid-run)
            pass

    def _run_submit_sweep(self, worker: "Worker | None" = None) -> "str | None":
        """Every section's `submit`, exactly once, in registry order, REPLAYED FRESH on every
        commit attempt (a retry after fixing one section must not append onto a stale prior
        attempt's queued effects -- `CommitSpec.reset`, if given, clears the consumer's own
        accumulator first). Returns `None` on full success (every section accepted its own
        current live answers) OR a clean between-section cancel (the caller distinguishes the
        two by checking `worker.is_cancelled` itself, since a cancelled run's own state must
        NOT be treated as a refusal-to-retry); otherwise the human-readable refusal to show,
        having already recorded which section failed into `state["_commit_errors"]`."""
        self.state.pop("_commit_errors", None)
        if self.commit_spec.reset is not None:
            self.commit_spec.reset(self.state)
        for spec in self.sections:
            if worker is not None and worker.is_cancelled:
                return None
            answers = section_answers(spec, self.state)
            result = spec.submit(self.state, answers)
            # MID-SECTION CANCEL (cycle-4 audit finding 1, ledger rows 1124/1133): checked HERE
            # too, not only before the call above -- a section whose own `submit` reached a real
            # subprocess mid-flow (`state["_cancel_check"]`, threaded to exactly one section
            # today: rehearsal) may have honored a cancel pressed WHILE it was running and
            # already recorded its own honest `checklist.CANCELLED` rows for what it did (see
            # `steps_rehearsal_birth.rehearsal_submit`); this class does not need a new
            # `SectionResult` shape to tell that apart from an ordinary refusal -- the SAME
            # `worker.is_cancelled` flag the section itself read is still readable here, right
            # after it returns. Treated exactly like the between-sections cancel path above
            # (return `None`, not the refusal string), so a mid-run cancel never gets rendered
            # as "fix it there and commit again".
            if worker is not None and worker.is_cancelled:
                return None
            if not result.ok:
                errors = result.errors or {"": "refused (no field named)"}
                self.state["_commit_errors"] = {str(spec.slug): errors}
                return (f"REFUSED at section '{spec.slug}' ({spec.title}): {errors} -- fix it "
                        f"there (the tree node now reads INVALID) and commit again.")
            if result.state_updates:
                self.state.update(result.state_updates)
            # NOTE: no blind `self.state.update(answers)` here (removed 2026-07-22, the same
            # fix as `panes.SectionPane._write_through`'s own docstring) -- a section's OWN
            # field values already live in their scoped slots (or the bare key, for an
            # explicitly `shared=True` field); re-copying every field's raw value onto a bare
            # top-level key here was the SAME aliasing hazard `set_field_value` exists to
            # prevent, just at commit time instead of per-keystroke. `submit`'s own
            # `state_updates` is the sole, deliberate, named channel by which a section exports
            # a fact to the rest of the model.
        return None

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ct-commit-cancel":
            if self._worker is not None:
                self._worker.cancel()
            return
        if event.button.id != "ct-commit" or self._committed or self._sweep_running:
            return
        if not ready_for_commit(self.sections, self.state):
            return
        self._set_busy(True, text="running the submit sweep (every section's own submit, "
                        "once) -- Cancel is honored between sections and, for rehearsal's own "
                        "subprocess work, during it too")
        self._worker = self._run_commit_and_sweep()

    @work(thread=True, exclusive=True, group="ct-commit-sweep")
    def _run_commit_and_sweep(self) -> None:
        """The ENTIRE two-phase sequence, off the UI thread (this method's docstring lives on
        the class -- see the "OFF THE UI THREAD" note above). Runs in a worker thread; touches
        ONLY `self.state` directly (the pure business logic's own contract), and reaches back to
        the widget tree exclusively through `self.app.call_from_thread`.

        Also the one place THIS worker's own cancellation token is published into `state`
        (`_cancel_check`/`_cancel_note`, see the class docstring's "MID-SECTION CANCELLATION
        TOKEN" paragraph) for the one section that reaches a real subprocess mid-flow to read --
        stashed here (not in `on_button_pressed`) because only here does `get_current_worker()`
        resolve to THIS sweep's own worker; popped in `finally` so a stale token never lingers
        into a later, unrelated sweep attempt or a direct (non-Textual) call to a section's own
        `submit` (e.g. a unit test), which must see `state.get("_cancel_check")` as `None`, the
        same "absent means behave exactly as before this fix" contract `rehearsal_submit`'s own
        docstring names."""
        worker = get_current_worker()
        self.state["_cancel_check"] = lambda: worker.is_cancelled
        self.state["_cancel_note"] = lambda text: self.app.call_from_thread(
            self._set_busy, True, text=text)
        try:
            sweep_error = self._run_submit_sweep(worker)
        finally:
            self.state.pop("_cancel_check", None)
            self.state.pop("_cancel_note", None)
        if worker.is_cancelled:
            self.app.call_from_thread(self._finish_cancelled,
                                       "cancelled -- the submit sweep did not finish, the "
                                       "commit act never started, nothing changed (if the "
                                       "cancel landed mid-section, that section's own subprocess "
                                       "was terminated and any required cleanup already ran to "
                                       "completion -- see its checklist rows).")
            return
        if sweep_error:
            self.app.call_from_thread(self._finish_sweep_refusal, sweep_error)
            return
        if worker.is_cancelled:  # last chance BEFORE the non-cancellable commit act starts
            self.app.call_from_thread(self._finish_cancelled,
                                       "cancelled after the submit sweep cleared, before the "
                                       "commit act started -- nothing was committed.")
            return
        self.state.pop("_commit_sweep_error", None)
        result = self.commit_spec.commit(self.state)  # the live scaffold act -- NOT cancellable
        self.app.call_from_thread(self._finish_committed, result)

    async def _finish_cancelled(self, message: str) -> None:
        self._set_busy(False)
        app = getattr(self, "app", None)
        if app is not None and hasattr(app, "on_model_changed"):
            app.on_model_changed()
        try:
            body = self.query_one("#ct-commit-body", VerticalScroll)
            await body.mount(Static(message, classes="ct-blocked-reason"))
        except Exception:  # noqa: BLE001 -- pane may be gone (app exiting)
            pass

    async def _finish_sweep_refusal(self, sweep_error: str) -> None:
        self.state["_commit_sweep_error"] = sweep_error
        self._set_busy(False)
        app = getattr(self, "app", None)
        if app is not None and hasattr(app, "on_model_changed"):
            app.on_model_changed()
        await self.recompose()

    async def _finish_committed(self, result) -> None:
        self.state.pop("_commit_sweep_error", None)
        self._committed = True
        self._set_busy(False)
        self.query_one("#ct-commit", Button).disabled = True
        self.query_one("#ct-commit-cancel", Button).disabled = True
        body = self.query_one("#ct-commit-body", VerticalScroll)
        for line in result.info_lines:
            await body.mount(Static(line, classes="ct-info-line"))
        await body.mount(Button("Finish", id="ct-finish", variant="success"))
        self.state["_commit_ok"] = result.ok
