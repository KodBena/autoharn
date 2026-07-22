"""tools/setup_tui/ui_textual.py -- TextualUi, the real Textual application backend behind the
one-home `Ui` seam (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md, commission ledger row 1818: "textual
is not used, at all, it is not a TUI, it is just a collection of prompts... Could we make it into
a real 'textual' app?").

ARCHITECTURE (spec §2, this module's implementation of it).

  1. The imperative screen loop survives unchanged. `app.py` still calls
     `screens.SCREENS`' eleven `screen_*(ui, cl, state)` functions in order, in exactly the same
     shape `InteractiveUi`/`ScriptedUi` already drive -- screens never learn textual exists, they
     keep calling `emit`/`ask_text`/`ask_choice`/`confirm`/`pause`/`suspend`. The only
     difference under this backend: that loop runs inside a Textual WORKER THREAD
     (`App.run_worker(..., thread=True)`) while `SetupWizardApp` itself renders on the main
     thread's asyncio loop. Every `Ui` method below blocks the CALLING (worker) thread until the
     operator answers -- never the App's own render loop -- by handing the actual widget
     mutation to the main thread via `App.call_from_thread` (which is documented thread-safe;
     Textual apps are otherwise not) and then waiting on a plain `threading.Event` the relevant
     Textual message handler (`on_input_submitted`, `on_option_list_option_selected`, a key
     binding) sets once the operator responds.

  2. Output routing: VERIFIED, not assumed (spec §3's own instruction). `App.begin_capture_print`
     + `redirect_stdout`/`redirect_stderr` (Textual's own mechanism, `textual.app.App`) replaces
     the PROCESS-GLOBAL `sys.stdout`/`sys.stderr` for the App's entire run -- not a per-thread
     substitution -- so a bare `print(...)`/`sys.stdout.write(...)` from ANY thread (the worker
     thread running the screen loop, or the main thread's own SIGTERM handler) is captured and
     delivered to whichever widget called `begin_capture_print`, via `Widget.post_message`, which
     is ITSELF documented and empirically confirmed thread-safe (it detects the calling thread
     differs from the App's own and marshals via `loop.call_soon_threadsafe`). This was verified
     empirically before this module was written (not merely read from source): a worker thread
     calling both the `print()` builtin and `sys.stdout.write()`/`sys.stderr.write()` directly,
     under `App.run_test()` (the headless harness WX1 drives), landed in a widget's `on_print`
     handler -- see this build's report for the transcript. ONE wrinkle the empirical check
     surfaced and this module works around: `events.Print` does NOT bubble, and `RichLog` has no
     built-in `on_print` handler, so `begin_capture_print` must target the APP itself (never a
     child widget) with the App defining `on_print` and relaying into the transcript log by hand
     (`SetupWizardApp.on_print` below). This module therefore never threads a second sink through
     `runner.py`/`app.py` -- the existing bare `print`/`sys.stdout.write` call sites there are
     completely unchanged; capture is the mechanism, per spec §3's first-listed option.

  3. Interactive children (gpg pinentry): `Ui.suspend()` (defined on the base class,
     `tools/setup_tui/ui.py`) is overridden here to bridge to `App.suspend()` across the same
     worker/main-thread boundary as every other method -- `App.suspend()` is a context manager
     whose `__enter__`/`__exit__` (driver mode transitions) must run on the App's own thread, but
     whose BODY (`screens.py`'s `with ui.suspend(): keygen = signed_genesis.keygen_operator(...)`
     -- a real, blocking gpg subprocess call) must keep running on the calling worker thread, not
     block the App's event loop for the whole ceremony. `_SuspendBridge` below splits the
     `@contextmanager`-generated object's `__enter__`/`__exit__` calls across two
     `call_from_thread` hops for exactly this reason.

  4. Cleanup: `SetupWizardApp` tracks a `threading.Event` (`_shutdown_event`) set both by its own
     quit binding and by `app.py`'s SIGTERM handler (via `request_shutdown`); every blocking wait
     in this module polls it on a short timeout rather than blocking forever, so an abnormal exit
     (SIGTERM, or the operator quitting the App mid-flow) wakes a worker stuck at a prompt instead
     of leaving a foreground thread that would otherwise hang interpreter shutdown (Python's
     `concurrent.futures.thread` atexit joins the default executor `run_worker(thread=True)` uses
     -- a thread parked on an unbounded `Event.wait()` would hang process exit even after the App
     itself had cleanly restored the terminal). A worker exception (a genuine bug, not this
     module's own shutdown signal) is left to propagate: Textual's own `run_worker(...,
     exit_on_error=True)` (the default) already turns an uncaught worker exception into a legible
     panic/crash report with the terminal cleanly restored first (verified empirically -- see the
     report) -- this module does not catch or re-wrap it, per spec §2 item 5 ("a worker exception
     must surface legibly... never vanish into a blank alternate screen").

  5. Transcript parity (spec §3, WX2): the `$ `-prefixed argv lines `runner.py`'s `run_command`/
     `start_background` print are completely untouched by this module -- they still call the bare
     `print()` builtin, which the capture pipeline above relays byte-for-byte into the transcript
     `RichLog`. `TextualUi.emit` (design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md) prints the SAME
     `elements.render_text(element)` lines the plain backend's `Ui.emit` would produce for the
     identical element (the one exception, a refusal `Note`, still carries the identical lines,
     styled directly rather than printed -- see `emit`'s own docstring) so the transcript's
     non-prompt content is text-identical to the plain backend's for the same journey; only the
     `ask_*`/`confirm`/`pause` methods differ, and each of those still
     prints its own one-line "prompt: answer" record into the transcript (the same paper-trail
     discipline `ScriptedUi` already keeps) so nothing the operator was asked, or answered, is
     lost once the docked prompt widget moves on to the next question.

  6. Backward navigation (design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md §3), fixed live against the
     maintainer's own report that it silently did nothing under this backend: `TextualUi`'s four
     `ask_*` methods below recognize `tools.setup_tui.ui.BACK_TRIGGER_PLAIN` ("<") at the SAME
     point in their own flow `InteractiveUi`'s matching methods do (before any default/coercion
     logic runs) and return `tools.setup_tui.ui.BACK` -- imported from `ui.py`, never redefined
     here, so the trigger spelling has ONE home regardless of which backend recognizes it
     (ADR-0012 P1). A full hoist of the recognition itself into `NavigableUi`
     (`tools/setup_tui/ui.py`) was considered and rejected: `NavigableUi` only ever sees each
     backend's ALREADY-coerced return value (a `str`/`bool`/`None`), never the pre-coercion raw
     keystroke -- by the time `confirm`'s own y/n coercion (say) has run, a raw "<" is already
     gone, turned into `False`. Recognizing the trigger BEFORE that coercion is therefore each
     backend's own job structurally, not a duplication this build introduced; TextualUi simply
     joins `InteractiveUi`/`ScriptedUi` in doing it, reusing their shared vocabulary rather than
     inventing a second one. Two affordances, not one, because a Textual prompt is not always a
     text field: (a) typing "<" and pressing enter in a text/confirm prompt's `Input` widget
     reaches `ask_text`/`confirm` exactly as any other typed answer would (no widget change
     needed -- the check is in `TextualUi`, not the widget); (b) `SetupWizardApp`'s own `on_key`
     additionally recognizes a bare "<" keypress while a choice/pause prompt is pending (an
     `OptionList`/the Continue button take no free text at all, so there is no `Input` for "<" to
     reach); and (c) a dedicated `ctrl+b` binding, shown in the `Footer` next to `ctrl+q`/
     `ctrl+c` (the existing binding idiom this module already follows), resolves whichever prompt
     is pending with the SAME trigger value regardless of its kind -- the one surface an operator
     glancing at the running app actually sees, so the intro banner's "Type '<' ... to go back"
     promise (`tools/setup_tui/content/app_data.py` `NAV_HINT`) is genuinely true under this
     backend, not merely under the two it was originally built against.

Lazy imports are banned (CLAUDE.md, 2026-07-02) -- and this module's own obligation under
design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md §3 is stronger than the general rule: `textual` is
imported unconditionally, at module top, with no `try`/`except` anywhere in this file. The
conditional (`textual` may not be installed) lives ONE level up, in `tools/setup_tui/app.py`'s
own top-level `try`/`except ImportError` around `import tools.setup_tui.ui_textual` -- eager
(module-import-time) either way, so `gates/no_lazy_imports.py` (which only flags a
function-BODY import, never a module-level `try`/`except`) has nothing to flag in either file.
This module is therefore only ever imported into a process where `textual` is already known
good; a caller that imports it without checking first gets the same honest `ModuleNotFoundError`
`import textual` would raise on its own.
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import contextlib
import threading
from collections.abc import Iterator
from typing import Any

import textual
import textual.events
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    OptionList,
    RichLog,
    Static,
)
from textual.widgets.option_list import Option

from tools.setup_tui import checklist as ck
from tools.setup_tui.elements import Heading, Note, render_text
from tools.setup_tui.screens import SCREEN_NUMBER, SCREEN_TITLES, SCREEN_TOTAL, SCREENS, screen_banner
from tools.setup_tui.ui import BACK, BACK_TRIGGER_PLAIN, Ui

# textual's own reported version, recorded here once (not re-derived per call) so
# `feature_facts.py`'s `ui_backend_textual` entry and this build's report can cite the SAME
# value this module actually imported against -- `importlib.metadata` is stdlib, no new
# dependency beyond `textual` itself.
try:
    import importlib.metadata as _ilm

    TEXTUAL_VERSION = _ilm.version("textual")
except Exception:  # noqa: BLE001 -- a version string is cosmetic; never let its lookup crash the app
    TEXTUAL_VERSION = getattr(textual, "__version__", "unknown")

# The banner text every screen actually prints ("N/11 Title", `screens.screen_banner`'s own
# rendering -- SCREEN_NUMBER/SCREEN_TITLES/SCREEN_TOTAL stay the one home, ADR-0012 P1) mapped
# back to the screen's slug, so the sidebar's pending/current/done state is DERIVED from the
# same live list `screens.SCREENS` defines, never a second hand-typed copy of the eleven names
# or their order. `app.py`'s own intro banner ("autoharn setup -- guided wizard...") is not one
# of these and simply misses the lookup below -- the sidebar stays all-pending until the first
# real screen banner arrives, which is correct (nothing has started yet).
_BANNER_TO_SLUG: dict[str, str] = {screen_banner(slug): slug for slug, _ in SCREENS}


class _Answer:
    """A one-shot mailbox between the worker thread (waiting) and the App's main thread (the
    Textual message handler that received the operator's response) -- deliberately NOT a
    `queue.Queue` (only one value is ever produced, and the shutdown-poll loop below needs a
    plain `Event` to `wait(timeout=...)` on)."""

    __slots__ = ("event", "value")

    def __init__(self) -> None:
        self.event = threading.Event()
        self.value: Any = None


# How long a single bridged call is allowed to take before this module gives up on it and reads
# it as a shutdown in progress (see `_call_from_thread_safe` below) -- generous for a call that
# only ever does quick widget mutations (query_one/update/focus), never anything that itself
# waits on the operator.
_BRIDGE_CALL_TIMEOUT = 10.0


def _call_from_thread_safe(app: "SetupWizardApp", callback: Any, *args: Any) -> Any:
    """Like `App.call_from_thread`, but BOUNDED. `call_from_thread`'s own implementation
    (`textual.app.App.call_from_thread`) schedules the callback via `asyncio.
    run_coroutine_threadsafe` and then blocks on `future.result()` with NO TIMEOUT. Empirically
    (this build's own WX5 stress pass, see the report -- reproduced on 2 of 3 consecutive full
    runs) a call scheduled while the App is in its shutdown transition (`App.exit()` already
    called, `ExitApp` posted, the loop about to stop servicing new callbacks) can leave that
    `future.result()` blocked FOREVER -- which would hang the calling WORKER thread, and in turn
    hang interpreter shutdown (module docstring, architecture point 4: the same class of hazard
    `_wait_answer`'s own timeout-poll already guards against for an ANSWER that never arrives;
    this is the same guard for the BRIDGE CALL itself never returning). This wrapper uses the
    SAME underlying primitive `call_from_thread` does, bounded by `_BRIDGE_CALL_TIMEOUT`: on
    timeout, or when the shutdown event is already set before the call even starts, this raises
    `WizardShutdown` -- the same "deliberate shutdown, never a bug" signal `_wait_answer` raises,
    so every caller in this module unwinds through one path regardless of WHICH stage of a
    shutdown it was caught in (waiting for an answer, or waiting for the bridge call itself)."""
    if app._shutdown_event.is_set():
        raise WizardShutdown("setup_tui: shutting down -- bridge call abandoned before it started")
    if app._loop is None:
        raise WizardShutdown("setup_tui: the App is not running -- shutting down")

    async def _run() -> Any:
        return callback(*args)

    future = asyncio.run_coroutine_threadsafe(_run(), loop=app._loop)
    try:
        return future.result(timeout=_BRIDGE_CALL_TIMEOUT)
    except concurrent.futures.TimeoutError:
        future.cancel()
        raise WizardShutdown(
            f"setup_tui: a bridge call to the App did not complete within "
            f"{_BRIDGE_CALL_TIMEOUT}s -- treating this as a shutdown in progress rather than "
            f"hanging the worker thread forever")


class _SuspendBridge:
    """Splits `App.suspend()`'s `@contextmanager`-generated enter/exit across two
    `call_from_thread` hops (module docstring, architecture point 3): the driver-mode
    transitions run on the App's own thread (where `App.suspend()` requires them), the ceremony's
    actual blocking gpg subprocess call -- the `with` block's BODY, in `screens.py` -- runs on
    the calling worker thread, exactly where every other blocking act in this flow already runs."""

    def __init__(self, app: "SetupWizardApp") -> None:
        self._app = app
        self._cm = None

    def __enter__(self) -> "_SuspendBridge":
        # App.suspend() is itself a generator-based context manager; entering/exiting it are two
        # separate calls we can marshal independently, rather than needing the whole `with` body
        # to run on the App's thread.
        self._cm = self._app.suspend()
        _call_from_thread_safe(self._app, self._cm.__enter__)
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        _call_from_thread_safe(self._app, self._cm.__exit__, exc_type, exc, tb)
        return False


class SidebarList(Static):
    """The eleven-screen sidebar (spec §2 item 2: "pending/current/done state"). A plain
    `Static` re-rendered wholesale on every `set_current` call -- eleven short lines is not
    worth a `ListView`'s selection machinery when nothing here is ever clicked."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._current_number: int | None = None

    def set_current(self, number: int) -> None:
        self._current_number = number
        self.update(self._render_text())

    def _render_text(self) -> str:
        lines = ["[b]Screens[/b]"]
        for slug, _ in SCREENS:
            n = SCREEN_NUMBER[slug]
            title = SCREEN_TITLES[slug]
            if self._current_number is None or n > self._current_number:
                marker, style = "o", "dim"
            elif n == self._current_number:
                marker, style = ">", "bold yellow"
            else:
                marker, style = "x", "green"
            lines.append(f"[{style}]{marker} {n:>2}. {title}[/{style}]")
        return "\n".join(lines)


class SetupWizardApp(App):
    """The Textual application (spec §2 item 2, layout v1). Owns the widgets; `TextualUi`
    (below) is the thin `Ui`-shaped adapter every screen function actually calls -- this class
    holds no wizard-domain knowledge beyond rendering what `TextualUi` and the print-capture
    pipeline hand it."""

    TITLE = "autoharn setup -- guided wizard"

    CSS = """
    Screen {
        layout: vertical;
    }
    #body {
        height: 1fr;
    }
    #sidebar {
        width: 26;
        border: solid $primary;
        padding: 0 1;
        overflow-y: auto;
    }
    #main {
        width: 1fr;
    }
    #dryrun-banner {
        dock: top;
        background: $error;
        color: $text;
        text-align: center;
        text-style: bold;
        height: 1;
    }
    #transcript {
        height: 1fr;
        border: solid $primary-darken-1;
    }
    #checklist-table {
        height: 12;
        border: solid $primary-darken-1;
        display: none;
    }
    #prompt {
        height: auto;
        max-height: 40%;
        border: heavy $accent;
        padding: 0 1;
    }
    #prompt-label {
        padding: 0 0 1 0;
    }
    #prompt-input {
        display: none;
    }
    #prompt-options {
        display: none;
        max-height: 10;
    }
    #prompt-continue {
        display: none;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "request_quit", "Quit", priority=True),
        # ctrl+c is the reflexive, universal interrupt keystroke -- ADR-0002 (fail loudly) rules
        # a silent swallow of it is a rung-5 failure. Textual's `Screen` base class itself binds
        # bare "ctrl+c" to `screen.copy_text` (textual/screen.py; DEFAULT_BINDINGS there, not
        # `priority`), which -- left unaddressed -- shadows `App`'s own built-in `ctrl+c` ->
        # `help_quit` in the per-key bindings merge (`Screen.active_bindings`, "Replace priority
        # bindings": a non-priority Screen binding beats a same-key App binding UNLESS the App's
        # is itself `priority=True`, which the base `help_quit` binding is not). Two problems,
        # one fix: (1) even un-shadowed, `App.action_help_quit`'s hint only fires when the bound
        # action is literally "quit"/"app.quit" -- this app renamed its quit action to
        # `request_quit`, so that built-in hint could never have fired here regardless. (2) the
        # copy-text shadow means, today, ctrl+c does NOTHING VISIBLE at all -- confirmed via a
        # headless `App.run_test()` probe (no state change, no rendered feedback) -- exactly the
        # forbidden silent no-op.
        #
        # Design choice: bind ctrl+c to the SAME `request_quit` -> `request_shutdown` path as
        # ctrl+q, not a "press again to confirm" hint. Considered and rejected: gating ctrl+c
        # behind an extra confirm because a commit phase might be in flight. That protection
        # does not actually exist today for ctrl+q -- ctrl+q already triggers this exact
        # unconditional path at ANY point in the wizard, commit included, and that is the
        # already-accepted, already-shipped behavior this fix does not touch. Making ctrl+c
        # behave differently from ctrl+q would invent a NEW asymmetry between two keystrokes an
        # operator reasonably expects to be synonyms for "quit," which is its own footgun
        # (reflexive ctrl+c would look like it worked less well than ctrl+q, when the two are
        # supposed to mean the same thing). `request_shutdown` is also not an abrupt kill of
        # in-flight work: it sets `_shutdown_event` and resolves any prompt currently being
        # waited on, but a worker thread mid-subprocess-call (e.g. mid-commit) keeps running
        # that call to completion -- only the NEXT blocking wait or bridge call observes the
        # shutdown and unwinds via `WizardShutdown` (module docstring, architecture point 4).
        # Symmetry with the existing, working ctrl+q reflex is the right call here, not a new
        # bespoke confirm gate for one of the two keystrokes.
        Binding("ctrl+c", "request_quit", "Quit", priority=True),
        # design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md §3 / module docstring architecture point 6:
        # typing "<" already works at a text/confirm prompt (its `Input` widget submits the
        # literal text, and `TextualUi.ask_text`/`confirm` recognize it same as `InteractiveUi`
        # does) and at a choice/pause prompt via `on_key` below -- this binding is the SAME
        # affordance made visible in the `Footer` (next to Quit) and usable regardless of which
        # kind of prompt is up or which widget currently has focus, never priority (an `Input`
        # or `OptionList` widget's own bindings, if any, still win first; none of them claim
        # ctrl+b today).
        Binding("ctrl+b", "go_back", "◀ Back"),
    ]

    def __init__(self, *, dry_run: bool, checklist: ck.Checklist) -> None:
        super().__init__()
        self._dry_run = dry_run
        self._checklist = checklist
        self._shutdown_event = threading.Event()
        self._pending: _Answer | None = None
        self._pending_kind: str | None = None
        self._pending_options: list[tuple[str, str]] = []
        # Textual's own print()-capture delivers stdout/stderr as raw WRITE fragments, not
        # complete lines -- Python's print() alone calls file.write() twice (the joined text,
        # then a separate write for `end="\n"`), so a naive "one RichLog.write() per Print
        # event" produced a spurious blank row after every plain print() call (verified
        # empirically while building this module; see the report). This buffer reassembles
        # fragments into whole lines the same way a real terminal would, so the transcript's
        # `$ `-prefixed lines (the WX2 parity bar) and every other line render exactly once,
        # with no artifacts from how Textual happened to chunk the capture.
        self._print_buffer = ""
        # A plain, un-wrapped record of every logical line ever written to the transcript --
        # kept SEPARATELY from the RichLog widget's own `.lines` (which are the WORD-WRAPPED
        # render rows, `wrap=True` below: a long `$ argv` line splits across two or more visual
        # rows there, so `str(rendered_row)` for the first one is a truncated prefix, not the
        # full logical line -- confirmed empirically while building WX2's parity witness, see
        # the report). This list is what a `$ `-prefix parity check (or any future "read the
        # transcript back out" need) should read; the RichLog stays responsible for DISPLAY only.
        self.transcript_log: list[str] = []
        # Set by app.py once the wizard body (the screen loop) is handed to a worker -- kept as
        # a plain attribute (not a constructor arg) so `main()` can construct the App first, wire
        # `TextualUi(app)` to it, THEN attach the callable that actually drives the screens --
        # breaking what would otherwise be a construction-order cycle (the driver needs a `ui`
        # that needs the app that needs the driver).
        self.wizard_body = None  # type: ignore[assignment]

    # -- layout (spec §2 item 2) -----------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        if self._dry_run:
            yield Static(
                "*** --dry-run: NOTHING below is destructive or externally visible ***",
                id="dryrun-banner",
            )
        with Horizontal(id="body"):
            yield SidebarList(id="sidebar")
            with Vertical(id="main"):
                yield RichLog(id="transcript", wrap=True, markup=False, highlight=False,
                               max_lines=20000, auto_scroll=True)
                yield DataTable(id="checklist-table")
                with Vertical(id="prompt"):
                    yield Static("", id="prompt-label")
                    yield Input(id="prompt-input")
                    yield OptionList(id="prompt-options")
                    yield Button("Continue", id="prompt-continue", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self.sub_title = "starting..."
        table = self.query_one("#checklist-table", DataTable)
        table.add_columns("SCREEN", "ITEM", "STATUS", "DETAIL")
        # Capture on the APP itself, not a child widget: events.Print does not bubble (module
        # docstring, architecture point 2) -- a target other than the App would never see it.
        self.begin_capture_print(self, stdout=True, stderr=True)
        # A periodic refresh, not a one-shot snapshot at the checklist banner: `cl.add(...)`
        # calls happen directly in screens.py, with no `Ui` call in between (the checklist
        # screen's very last item -- "checklist saved" -- is added AFTER its last `ui.confirm`
        # call returns, with nothing further calling into this App before the screen returns) --
        # so there is no `Ui`-method hook this class could refresh from that is guaranteed to
        # fire after that final row. Polling is the honest fix: cheap (the checklist rarely
        # exceeds ~150 rows) and only does anything once the table is actually visible.
        self.set_interval(0.5, self._refresh_checklist_table_if_visible)
        if self.wizard_body is not None:
            self.run_worker(self.wizard_body, thread=True, exit_on_error=True)

    # -- print capture -> transcript (architecture point 2) ---------------------------------

    def on_print(self, event: textual.events.Print) -> None:
        self._print_buffer += event.text
        *complete_lines, self._print_buffer = self._print_buffer.split("\n")
        if complete_lines:
            log = self.query_one("#transcript", RichLog)
            for line in complete_lines:
                log.write(line)
                self.transcript_log.append(line)

    def write_transcript_styled(self, lines: list[str], style: str) -> None:
        """The one styling seam beyond plain print-capture (design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md
        §2: "the Textual renderer may style beyond the canonical text form but never add or drop
        content relative to it") -- called ONLY for `Note(tone="refusal")` (`TextualUi.emit`
        below), never for anything the plain backend would also print, so the CONTENT (the exact
        `lines` `elements.render_text` produced) is identical either way; only the RichLog's own
        rendering of it differs (a styled `rich.text.Text` object here vs. a captured, unstyled
        `print()` line elsewhere). Runs on the App's own thread (`_call_from_thread_safe`, same as
        every other widget mutation in this module) -- writes bypass `begin_capture_print`
        entirely, so `transcript_log` (the plain-text record every parity check reads) is appended
        to directly here, exactly as `on_print` does for a captured line."""
        log = self.query_one("#transcript", RichLog)
        for line in lines:
            log.write(Text(line, style=style))
            self.transcript_log.append(line)

    def on_unmount(self) -> None:
        # A final, newline-less fragment (a print with no trailing "\n" that nothing after it
        # ever completed) would otherwise never reach the transcript at all -- flush it once,
        # here, rather than silently dropping the tail of a real, unbuffered write. Best-effort:
        # by the time unmount fires the transcript widget may already be gone from the DOM, and
        # this is cosmetic (a partial trailing line), never worth crashing teardown over.
        if self._print_buffer:
            self.transcript_log.append(self._print_buffer)
            try:
                self.query_one("#transcript", RichLog).write(self._print_buffer)
            except Exception:  # noqa: BLE001 -- best-effort flush during teardown, see above
                pass
            self._print_buffer = ""

    # -- sidebar / header ordinal (spec: "Header... the derived N/11 Screen ordinal") -------

    def note_banner(self, text: str) -> None:
        self.sub_title = text
        slug = _BANNER_TO_SLUG.get(text)
        if slug is not None:
            self.query_one("#sidebar", SidebarList).set_current(SCREEN_NUMBER[slug])
            if slug == "checklist":
                self.query_one("#checklist-table", DataTable).display = True
                self._refresh_checklist_table_if_visible()

    def _refresh_checklist_table_if_visible(self) -> None:
        table = self.query_one("#checklist-table", DataTable)
        if not table.display:
            return
        if table.row_count == len(self._checklist.items):
            return  # nothing new since the last refresh -- avoid a pointless rebuild+repaint
        table.clear()
        for it in self._checklist.items:
            table.add_row(it.screen, it.item, it.status, it.detail[:80])

    # -- the docked prompt area (spec: "Input for text... option list for choices... Y/n...
    # a continue control for pause") ---------------------------------------------------------

    def _reset_prompt_widgets(self) -> None:
        """Every `arm_*_prompt` starts from the same clean slate -- exactly one of
        Input/OptionList/the Continue button is visible for the kind of question actually being
        asked, never a stale widget left showing from the previous prompt."""
        self.query_one("#prompt-input", Input).display = False
        self.query_one("#prompt-options", OptionList).display = False
        self.query_one("#prompt-continue", Button).display = False

    def arm_text_prompt(self, prompt: str, default: str | None, answer: _Answer) -> None:
        self._pending = answer
        self._pending_kind = "text"
        suffix = f" [{default}]" if default is not None else ""
        self.query_one("#prompt-label", Static).update(f"{prompt}{suffix}")
        self._reset_prompt_widgets()
        inp = self.query_one("#prompt-input", Input)
        inp.value = ""
        inp.placeholder = default or ""
        inp.display = True
        inp.focus()

    def arm_choice_prompt(self, prompt: str, options: list[tuple[str, str]], answer: _Answer) -> None:
        self._pending = answer
        self._pending_kind = "choice"
        self._pending_options = options
        self.query_one("#prompt-label", Static).update(prompt)
        self._reset_prompt_widgets()
        opts = self.query_one("#prompt-options", OptionList)
        opts.clear_options()
        for i, (key, label) in enumerate(options, start=1):
            opts.add_option(Option(f"{i}. {label}", id=key))
        opts.display = True
        opts.focus()
        opts.highlighted = 0

    def arm_confirm_prompt(self, prompt: str, default: bool, answer: _Answer) -> None:
        self._pending = answer
        self._pending_kind = "confirm"
        hint = "Y/n" if default else "y/N"
        self.query_one("#prompt-label", Static).update(f"{prompt} [{hint}]")
        self._reset_prompt_widgets()
        inp = self.query_one("#prompt-input", Input)
        inp.value = ""
        inp.placeholder = "y" if default else "n"
        inp.display = True
        inp.focus()

    def arm_pause_prompt(self, prompt: str, answer: _Answer) -> None:
        self._pending = answer
        self._pending_kind = "pause"
        self.query_one("#prompt-label", Static).update(prompt)
        self._reset_prompt_widgets()
        btn = self.query_one("#prompt-continue", Button)
        btn.display = True
        btn.focus()

    def _resolve(self, value: Any) -> None:
        pending, self._pending = self._pending, None
        self._pending_kind = None
        if pending is not None:
            pending.value = value
            pending.event.set()

    def on_input_submitted(self, message: Input.Submitted) -> None:
        if self._pending is None or self._pending_kind not in ("text", "confirm"):
            return
        self._resolve(message.value)

    def on_option_list_option_selected(self, message: OptionList.OptionSelected) -> None:
        if self._pending is None or self._pending_kind != "choice":
            return
        option_id = message.option.id
        self._resolve(option_id)

    def on_button_pressed(self, message: Button.Pressed) -> None:
        if self._pending is None or self._pending_kind != "pause":
            return
        if message.button.id == "prompt-continue":
            self._resolve(None)

    def on_key(self, event: textual.events.Key) -> None:
        # design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md §3 / module docstring architecture point 6:
        # a choice/pause prompt has no `Input` widget for a typed "<" to reach (`OptionList`
        # takes arrow+enter/digit selection only; the Continue button takes a click) -- this is
        # the ONE place that affordance exists for those two kinds. Scoped to choice/pause only:
        # a text/confirm prompt's own `Input` already delivers a typed "<" to
        # `TextualUi.ask_text`/`confirm` via `on_input_submitted` above once the operator presses
        # enter, and intercepting every "<" keypress globally (rather than the whole submitted
        # value) would fire mid-keystroke, before the operator finished typing, for those two
        # kinds -- a materially different (and wrong) UX than "<" as a WHOLE bare answer, which
        # is what `InteractiveUi`/`ScriptedUi` (and this class's own ask_text/confirm) mean by it.
        if self._pending is not None and self._pending_kind in ("choice", "pause") and \
                event.character == BACK_TRIGGER_PLAIN:
            event.stop()
            self._resolve(BACK_TRIGGER_PLAIN)
            return
        # spec: "an option list for choices, number keys still accepted" -- OptionList already
        # handles arrow+enter on its own; this adds the numbered-menu muscle memory the plain
        # backend trained operators on.
        if self._pending is not None and self._pending_kind == "choice" and event.key.isdigit():
            idx = int(event.key) - 1
            if 0 <= idx < len(self._pending_options):
                event.stop()
                self._resolve(self._pending_options[idx][0])

    def action_go_back(self) -> None:
        """The `ctrl+b` binding (module docstring architecture point 6) -- the ONE keybinding
        that works at ANY prompt kind, since it never depends on which widget is focused or
        whether that widget accepts free text at all. A no-op (not an error) when nothing is
        pending -- e.g. the binding fires while the App is still starting up, or between two
        prompts -- exactly as `InteractiveUi`'s own "<" is only ever read at a live prompt."""
        if self._pending is not None:
            self._resolve(BACK_TRIGGER_PLAIN)

    # -- shutdown (architecture point 4) -----------------------------------------------------

    def exit(self, result: Any = None, return_code: int = 0, message: Any = None) -> None:
        # The guaranteed final refresh (note_banner docstring above): the checklist screen's own
        # LAST `cl.add(...)` call (the "checklist saved" row) happens with no further `Ui` call
        # after it in screens.py, so the periodic timer might not get another tick in before this
        # process starts tearing down. `exit()` is the one funnel every shutdown path (normal
        # completion, the quit binding, app.py's SIGTERM handler) already calls through, so one
        # more synchronous refresh here -- same thread, no race -- is the deterministic fix the
        # timer alone cannot guarantee.
        self._refresh_checklist_table_if_visible()
        super().exit(result=result, return_code=return_code, message=message)

    def action_request_quit(self) -> None:
        self.request_shutdown(130)

    def request_shutdown(self, return_code: int) -> None:
        """Called from the App's own quit binding (main thread) OR from `app.py`'s SIGTERM
        handler (also the main thread -- Python only ever delivers a signal to the main thread,
        so this never crosses threads itself): wakes any worker-thread wait in this module
        (`_wait_answer` below polls `_shutdown_event`, never blocks on it forever) and asks the
        App to exit so the terminal is restored before the process does."""
        self._shutdown_event.set()
        if self._pending is not None:
            self._resolve(None)
        self.exit(return_code=return_code)


class WizardShutdown(RuntimeError):
    """Raised inside the worker thread when `_wait_answer` observes the shutdown event instead
    of a real answer -- an EXPECTED unwind (SIGTERM, or the operator quitting the App), not a
    bug: `app.py`'s driver function catches this specifically and returns cleanly rather than
    letting it read as a worker crash (which would trigger Textual's panic/crash-report path,
    the wrong signal for a deliberate shutdown)."""


def _wait_answer(app: SetupWizardApp, answer: _Answer) -> Any:
    """Blocks the CALLING thread (a worker thread) until `answer.event` is set, polling
    `app._shutdown_event` on a short timeout rather than waiting forever -- module docstring,
    architecture point 4: an unbounded wait here, left unanswered by an App that has already
    exited, would hang interpreter shutdown (the default `run_worker(thread=True)` executor's
    threads are joined at `atexit`)."""
    while True:
        if answer.event.wait(timeout=0.1):
            return answer.value
        if app._shutdown_event.is_set():
            raise WizardShutdown("setup_tui: shutting down -- prompt abandoned")


class TextualUi(Ui):
    """The `Ui` seam's Textual-application backend (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md).
    Every method here runs on the WORKER thread the screen loop drives from; every widget
    mutation is marshaled onto the App's own thread via `call_from_thread` (module docstring)."""

    def __init__(self, app: SetupWizardApp) -> None:
        self._app = app

    def emit(self, element: object) -> None:
        """Text parity by construction (design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md §2): every
        element's `render_text` lines print exactly as the plain backend's `Ui.emit` would (the
        capture pipeline relays them into the transcript byte-for-byte, module docstring
        architecture point 2) -- this override ADDS two backend-only behaviors, never changes
        the text: a `Heading` also drives the sidebar/header ordinal (`note_banner`, same string
        the old `banner()` used to), and a refusal `Note` renders with loud style DIRECTLY in the
        transcript (`write_transcript_styled`) instead of a plain print -- still the identical
        `lines`, so `transcript_log`'s content is the same either way, only the RichLog's visual
        rendering of a refusal differs from every other line."""
        lines = render_text(element)
        if isinstance(element, Note) and element.tone == "refusal":
            _call_from_thread_safe(self._app, self._app.write_transcript_styled, lines, "bold red")
        elif lines:
            # ONE print() call for the whole element, not one per line (module docstring
            # architecture point 2's own print-capture pipeline posts one `events.Print` message
            # PER CALL, marshaled onto the App's asyncio loop -- a multi-line element split into
            # N separate print() calls is N queued messages instead of one; see this build's F4
            # diagnostic leg report for the reproduction this fixes).
            print("\n".join(lines))
        if isinstance(element, Heading):
            _call_from_thread_safe(self._app, self._app.note_banner, element.text)

    # NAVIGATION (design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md §3, module docstring architecture
    # point 6): each method below checks the RAW answer against `BACK_TRIGGER_PLAIN` BEFORE any
    # of its own default/coercion logic runs -- the SAME shape and the SAME shared trigger
    # constant `InteractiveUi`'s matching methods (`tools/setup_tui/ui.py`) already use, never a
    # second, TextualUi-local spelling of "<". The raw value reaching `_wait_answer` here comes
    # from either the operator's own typed/submitted answer (`on_input_submitted`/
    # `on_option_list_option_selected`) or `SetupWizardApp.on_key`/`action_go_back` resolving the
    # SAME `BACK_TRIGGER_PLAIN` string directly -- both paths are indistinguishable to the code
    # below, which is exactly the point (one recognition, however the operator triggered it).

    def ask_text(self, prompt: str, default: str | None = None) -> str:
        answer = _Answer()
        _call_from_thread_safe(self._app, self._app.arm_text_prompt, prompt, default, answer)
        while True:
            raw = (_wait_answer(self._app, answer) or "").strip()
            if raw == BACK_TRIGGER_PLAIN:
                print(f"{prompt}: <BACK>")
                return BACK  # type: ignore[return-value]
            if raw:
                value = raw
                break
            if default is not None:
                value = default
                break
            # Re-arm the SAME prompt (spec parity with InteractiveUi's own "a value is
            # required" retry loop) -- a fresh _Answer, since the prior one was already resolved.
            answer = _Answer()
            _call_from_thread_safe(self._app, self._app.arm_text_prompt, prompt, default, answer)
        suffix = f" [{default}]" if default is not None else ""
        print(f"{prompt}{suffix}: {value}")
        return value

    def ask_choice(self, prompt: str, options: list[tuple[str, str]]) -> str:
        print(prompt)
        for i, (key, label) in enumerate(options, start=1):
            print(f"  {i}. {label}")
        answer = _Answer()
        _call_from_thread_safe(self._app, self._app.arm_choice_prompt, prompt, options, answer)
        value = _wait_answer(self._app, answer)
        if value == BACK_TRIGGER_PLAIN:
            print("  -> <BACK>")
            return BACK  # type: ignore[return-value]
        label = next((lbl for k, lbl in options if k == value), value)
        print(f"  -> {label}")
        return value

    def confirm(self, prompt: str, default: bool = False) -> bool:
        answer = _Answer()
        _call_from_thread_safe(self._app, self._app.arm_confirm_prompt, prompt, default, answer)
        raw = (_wait_answer(self._app, answer) or "").strip()
        if raw == BACK_TRIGGER_PLAIN:
            print(f"{prompt}: <BACK>")
            return BACK  # type: ignore[return-value]
        raw_l = raw.lower()
        result = default if not raw_l else raw_l in ("y", "yes")
        hint = "Y/n" if default else "y/N"
        print(f"{prompt} [{hint}]: {'yes' if result else 'no'}")
        return result

    def pause(self, prompt: str = "Press enter when done: ") -> None:
        answer = _Answer()
        _call_from_thread_safe(self._app, self._app.arm_pause_prompt, prompt, answer)
        raw = _wait_answer(self._app, answer)
        if raw == BACK_TRIGGER_PLAIN:
            print(f"{prompt}<BACK>")
            return BACK  # type: ignore[return-value]
        print(prompt)

    @contextlib.contextmanager
    def suspend(self) -> Iterator[None]:
        with _SuspendBridge(self._app):
            yield
