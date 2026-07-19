# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T00:00:00Z
#   last-change : 2026-07-19T00:00:00Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/ui_textual.py -- TextualUi, the real Textual application backend behind the
one-home `Ui` seam (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md, commission ledger row 1818: "textual
is not used, at all, it is not a TUI, it is just a collection of prompts... Could we make it into
a real 'textual' app?").

ARCHITECTURE (spec §2, this module's implementation of it).

  1. The imperative screen loop survives unchanged. `app.py` still calls
     `screens.SCREENS`' eleven `screen_*(ui, cl, state)` functions in order, in exactly the same
     shape `InteractiveUi`/`ScriptedUi` already drive -- screens never learn textual exists, they
     keep calling `banner`/`say`/`ask_text`/`ask_choice`/`confirm`/`pause`/`suspend`. The only
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
     `RichLog`. `TextualUi`'s own `say`/`banner` methods also just call `print(...)` (the exact
     same text `InteractiveUi.say`/`Ui.banner` would produce, since `TextualUi` does not override
     them) so the transcript's non-prompt content is text-identical to the plain backend's for the
     same journey; only the `ask_*`/`confirm`/`pause` methods differ, and each of those still
     prints its own one-line "prompt: answer" record into the transcript (the same paper-trail
     discipline `ScriptedUi` already keeps) so nothing the operator was asked, or answered, is
     lost once the docked prompt widget moves on to the next question.

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
from tools.setup_tui.screens import SCREEN_NUMBER, SCREEN_TITLES, SCREEN_TOTAL, SCREENS, screen_banner
from tools.setup_tui.ui import Ui

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
        # spec: "an option list for choices, number keys still accepted" -- OptionList already
        # handles arrow+enter on its own; this adds the numbered-menu muscle memory the plain
        # backend trained operators on.
        if self._pending is not None and self._pending_kind == "choice" and event.key.isdigit():
            idx = int(event.key) - 1
            if 0 <= idx < len(self._pending_options):
                event.stop()
                self._resolve(self._pending_options[idx][0])

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

    def banner(self, text: str) -> None:
        # Same visible text a plain-backend transcript would show (parity, module docstring
        # point 5) -- the App also uses this exact string to drive the sidebar/header ordinal.
        print()
        print("=" * 78)
        print(text)
        print("=" * 78)
        _call_from_thread_safe(self._app, self._app.note_banner, text)

    def say(self, text: str = "") -> None:
        print(text)

    def ask_text(self, prompt: str, default: str | None = None) -> str:
        answer = _Answer()
        _call_from_thread_safe(self._app, self._app.arm_text_prompt, prompt, default, answer)
        while True:
            raw = (_wait_answer(self._app, answer) or "").strip()
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
        label = next((lbl for k, lbl in options if k == value), value)
        print(f"  -> {label}")
        return value

    def confirm(self, prompt: str, default: bool = False) -> bool:
        answer = _Answer()
        _call_from_thread_safe(self._app, self._app.arm_confirm_prompt, prompt, default, answer)
        raw = (_wait_answer(self._app, answer) or "").strip().lower()
        result = default if not raw else raw in ("y", "yes")
        hint = "Y/n" if default else "y/N"
        print(f"{prompt} [{hint}]: {'yes' if result else 'no'}")
        return result

    def pause(self, prompt: str = "Press enter when done: ") -> None:
        answer = _Answer()
        _call_from_thread_safe(self._app, self._app.arm_pause_prompt, prompt, answer)
        _wait_answer(self._app, answer)
        print(prompt)

    @contextlib.contextmanager
    def suspend(self) -> Iterator[None]:
        with _SuspendBridge(self._app):
            yield
