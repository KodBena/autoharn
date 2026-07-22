"""tools/setup_tui/ui.py -- the ONE numbered-menu UI substrate (ADR-0012 P1: one home for the
prompt/print shape, no screen module talks to stdin/stdout directly).

THREE backends behind the same `Ui` interface, selected once at startup by
`tools/setup_tui/app.py` (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md, commission ledger row 1818):

  * `TextualUi` (`tools/setup_tui/ui_textual.py`) -- a real Textual application: Header/sidebar/
    transcript/docked-prompt/Footer, with the SAME imperative screen loop below run unchanged in
    a Textual worker thread. Selected for interactive runs when `textual` is importable -- this
    is the default face now that the v1 "library ONLY if already installed" clause is superseded
    (see that spec, which also supersedes FABLE-SETUP-TUI-SPEC.md's original v1-boundaries text).
  * `InteractiveUi` -- plain `input()`/`print()`, no curses, no prompt-toolkit. The `--plain`
    flag forces this backend explicitly, and it is also the automatic fallback when `textual` is
    not importable (one teaching line naming the exact venv/pip command, then this backend, per
    the Textual spec's "degraded-but-possible beats frozen").
  * `ScriptedUi` -- reads answers, one per line, from a file given via `--scripted
    <answers-file>`, in the exact order the screens ask for them. It calls the SAME
    `ask_text`/`ask_choice`/`confirm`/`pause` methods a human would drive interactively; only
    where the next answer comes from differs. This is how WT1/WT2/WT3/WT4/WT5 (and the newer
    WX-series Textual witnesses) are witnessed without a human at the keyboard. `--scripted`
    NEVER selects `TextualUi` -- headless witnessing must not grow a dependency (the Textual
    spec's own selection rule).

Every method also ECHOES the question and the answer actually used to stdout, so a transcript of
a scripted run reads exactly like a transcript of an interactive one -- `TextualUi` keeps this
property too (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md §3: the transcript pane carries everything
the flow says, and its `$ `-prefixed lines stay text-identical to the plain backend's).

`Ui.emit(element)` (design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md, the typed-UI content vocabulary) is
the ONE place a screen shows content to the operator -- `element` is one of the six closed types
in `tools/setup_tui/elements.py` (`Heading`/`Paragraph`/`Table`/`StatusLine`/`Note`/`Rule`). The
old free-text `Ui.say(str)`/`Ui.banner(str)` are REMOVED, not shimmed: a shim would let the old
`str` register persist indefinitely, the same silent-fallback class the spec's field strategy
condemns. Every call site across `tools/setup_tui/` converts to `emit` in the same commission
that adds it (spec §1's closure statement) -- `gates/setup_tui_purity_gate.py`'s new check
enforces no module but this one and `ui_textual.py` may call `print(`/`.say(` directly.
"""
from __future__ import annotations

import contextlib
import sys
from collections.abc import Iterator
from pathlib import Path

from tools.setup_tui.elements import Note, render_text


class ScriptExhausted(RuntimeError):
    """A ScriptedUi ran out of answers -- the answers file did not supply enough lines for the
    flow it drove. Never silently defaults; the caller sees exactly which prompt starved."""


class NavigateBack(Exception):
    """design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md §3: raised by `NavigableUi` (below) when the
    operator's answer at ANY prompt is the BACK sentinel, instead of that sentinel ever being
    returned to a screen function as if it were a real answer. Caught in exactly one place --
    `tools.setup_tui.app._drive_screens`'s screen loop -- which pops the cursor back to the
    previous completed screen and re-enters it. Never expected to reach a screen module."""


class _BackSentinel:
    """A private, unique value every backend's ask-method returns instead of a real answer when
    the operator asks to go back -- recognized by identity (`is BACK`, never string equality) so
    a legitimate typed answer that happens to collide with one of the trigger spellings below is
    never confused with an actual request to navigate (each backend converts its own trigger
    spelling to this ONE object before returning, so nothing downstream ever sees the trigger
    text itself)."""

    def __repr__(self) -> str:
        return "<BACK>"


BACK = _BackSentinel()

# The two trigger spellings design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md §3 names: plain interactive
# input takes a bare "<" (fast to type at any prompt, and distinct from any legitimate answer this
# package's screens ever ask for -- world names/paths/hostnames never consist of nothing but "<");
# a `--scripted` answers file spells it "<BACK>" (an answers file is read by a human too -- the
# module docstring's own "commented for a human reader" clause -- so its trigger line is spelled
# out rather than a bare punctuation mark that reads as a typo in a column of answers).
_BACK_TRIGGER_PLAIN = "<"
_BACK_TRIGGER_SCRIPTED = "<BACK>"


class Ui:
    """Shared surface both backends implement. Never instantiated directly."""

    def emit(self, element: object) -> None:
        """Prints `render_text(element)`'s lines verbatim -- the canonical rendering every
        backend but `TextualUi` (which overrides this to also drive the sidebar/header ordinal
        off a `Heading` and to style a refusal `Note`, `tools/setup_tui/ui_textual.py`) uses
        unchanged."""
        for line in render_text(element):
            print(line)

    def ask_text(self, prompt: str, default: str | None = None) -> str:
        raise NotImplementedError

    def ask_choice(self, prompt: str, options: list[tuple[str, str]]) -> str:
        """`options` is [(key, label), ...]. Returns the chosen key."""
        raise NotImplementedError

    def confirm(self, prompt: str, default: bool = False) -> bool:
        raise NotImplementedError

    def pause(self, prompt: str = "Press enter when done: ") -> None:
        raise NotImplementedError

    @contextlib.contextmanager
    def suspend(self) -> Iterator[None]:
        """Yield control of the terminal to an interactive CHILD process for the duration of the
        `with` block (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md §2 item 4) -- the known case is
        gpg's own pinentry prompt during the Signed genesis ceremony (`screens.py`
        `screen_signed_genesis`'s `keygen_operator`/`sign_statement` calls, wrapped in
        `with ui.suspend():`). A no-op here (and in `InteractiveUi`/`ScriptedUi`, which never
        override it): `InteractiveUi` already IS the raw terminal (nothing to yield), and
        `ScriptedUi` never runs an act that could invoke a real pinentry (its own scratch-
        GNUPGHOME/fixture-passphrase path is fully non-interactive, `signed_genesis.
        keygen_scripted`/the `--batch`/`--pinentry-mode loopback` leg of `sign_statement`).
        `TextualUi` (`tools/setup_tui/ui_textual.py`) is the one backend that overrides this --
        it yields the App's own `App.suspend()` context manager so the operator's pinentry runs
        against the real terminal, never scraped or scripted by this tool -- so screens.py can
        wrap an interactive-child act in `with ui.suspend():` without ever knowing which backend
        is live (screens stay backend-blind, this seam's own standing rule)."""
        yield


class InteractiveUi(Ui):
    # NAVIGATION (design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md §3): each ask-method below checks the
    # RAW keystroke against `_BACK_TRIGGER_PLAIN` BEFORE any of its own validation/default/
    # coercion logic runs, and returns the shared `BACK` sentinel instead of a real answer when it
    # matches -- never `NotImplementedError`'d, never coerced into "y"/"n"/an index the way an
    # ordinary stray character would be. The four return-type annotations below (`str`/`bool`/
    # `None`) are honest for every answer that is NOT `BACK`; the sentinel escape is the one typed
    # exception every caller of this class already goes through `NavigableUi` for (below), which
    # is the ONE place `is BACK` is ever checked -- a screen calling these methods directly would
    # never route a bare "<" specially, which is exactly why `app.py` never hands a screen a raw
    # backend, only a `NavigableUi` wrapping one.
    def ask_text(self, prompt: str, default: str | None = None) -> str:
        suffix = f" [{default}]" if default is not None else ""
        while True:
            raw = input(f"{prompt}{suffix}: ").strip()
            if raw == _BACK_TRIGGER_PLAIN:
                return BACK  # type: ignore[return-value]
            if raw:
                return raw
            if default is not None:
                return default
            print("  (a value is required)")

    def ask_choice(self, prompt: str, options: list[tuple[str, str]]) -> str:
        print(prompt)
        for i, (key, label) in enumerate(options, start=1):
            print(f"  {i}. {label}")
        keys = [k for k, _ in options]
        while True:
            raw = input(f"choose 1-{len(options)}: ").strip()
            if raw == _BACK_TRIGGER_PLAIN:
                return BACK  # type: ignore[return-value]
            if raw in keys:
                return raw
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                return keys[int(raw) - 1]
            print(f"  (enter a number 1-{len(options)}, or one of: {', '.join(keys)}, or '<' to "
                  f"go back)")

    def confirm(self, prompt: str, default: bool = False) -> bool:
        hint = "Y/n" if default else "y/N"
        raw = input(f"{prompt} [{hint}]: ").strip()
        if raw == _BACK_TRIGGER_PLAIN:
            return BACK  # type: ignore[return-value]
        raw = raw.lower()
        if not raw:
            return default
        return raw in ("y", "yes")

    def pause(self, prompt: str = "Press enter when done: ") -> None:
        raw = input(prompt).strip()
        if raw == _BACK_TRIGGER_PLAIN:
            return BACK  # type: ignore[return-value]


class ScriptedUi(Ui):
    """Drives the same `Ui` call sites from a pre-written answers file -- one answer per
    non-blank, non-`#`-comment line, consumed strictly in order. Blank lines and lines starting
    with `#` are skipped (so an answers file can be commented for a human reader), never counted
    as an answer."""

    def __init__(self, answers_path: str | Path) -> None:
        path = Path(answers_path)
        if not path.is_file():
            raise SystemExit(f"setup_tui: --scripted answers file not found: {path}")
        lines = []
        for raw in path.read_text().splitlines():
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            lines.append(stripped)
        self._answers = lines
        self._i = 0
        self._source = str(path)

    def _next(self, prompt: str) -> str:
        if self._i >= len(self._answers):
            raise ScriptExhausted(
                f"setup_tui --scripted: {self._source} ran out of answers at prompt "
                f"'{prompt}' (needed answer #{self._i + 1}, only {len(self._answers)} given)."
            )
        val = self._answers[self._i]
        self._i += 1
        return val

    # NAVIGATION (design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md §3): each ask-method below checks the
    # RAW answer line against `_BACK_TRIGGER_SCRIPTED` BEFORE any of its own "-"-default/index/
    # yes-no coercion -- `confirm`'s own `val in ("y", "yes", ...)` coercion would otherwise
    # silently read "<BACK>" as "no", and `ask_choice`'s own key/index validation would otherwise
    # raise `SystemExit` on it as an invalid answer. See `InteractiveUi`'s matching comment for
    # why the sentinel never reaches a screen directly.
    def ask_text(self, prompt: str, default: str | None = None) -> str:
        val = self._next(prompt)
        if val == _BACK_TRIGGER_SCRIPTED:
            print(f"{prompt}: <BACK>   [scripted]")
            return BACK  # type: ignore[return-value]
        if val == "-" and default is not None:
            val = default
        print(f"{prompt}: {val}   [scripted]")
        return val

    def ask_choice(self, prompt: str, options: list[tuple[str, str]]) -> str:
        print(prompt)
        for i, (key, label) in enumerate(options, start=1):
            print(f"  {i}. {label}")
        keys = [k for k, _ in options]
        val = self._next(prompt)
        if val == _BACK_TRIGGER_SCRIPTED:
            print(f"choice: <BACK>   [scripted]")
            return BACK  # type: ignore[return-value]
        if val.isdigit() and 1 <= int(val) <= len(options):
            val = keys[int(val) - 1]
        if val not in keys:
            raise SystemExit(
                f"setup_tui --scripted: answer '{val}' for '{prompt}' is not one of "
                f"{keys} and not a valid index."
            )
        print(f"choice: {val}   [scripted]")
        return val

    def confirm(self, prompt: str, default: bool = False) -> bool:
        raw = self._next(prompt)
        if raw == _BACK_TRIGGER_SCRIPTED:
            print(f"{prompt}: <BACK>   [scripted]")
            return BACK  # type: ignore[return-value]
        val = raw.lower()
        result = val in ("y", "yes", "true", "1")
        print(f"{prompt}: {'yes' if result else 'no'}   [scripted]")
        return result

    def pause(self, prompt: str = "Press enter when done: ") -> None:
        # The scripted backend still consumes one answer line here -- this is the exact point a
        # WT3 (lie-detection) or WT4 (mid-flow-kill) witness controls: the answers file names
        # what the operator claims ("done") vs. what they actually did (nothing), and the
        # post-keypress probe downstream is what catches the gap, not this method itself.
        val = self._next(prompt)
        if val == _BACK_TRIGGER_SCRIPTED:
            print(f"{prompt}<BACK>   [scripted]")
            return BACK  # type: ignore[return-value]
        print(f"{prompt}{val}   [scripted]")


class NavigableUi(Ui):
    """design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md §3: wraps ANY other `Ui` backend and gives every
    one of its ask-methods the BACK affordance WITHOUT any screen module knowing about it --
    screens.py calls `ui.ask_text`/`ask_choice`/`confirm`/`pause` exactly as it always has; THIS
    seam is the one place "does the answer mean navigate back" is decided (ADR-0012 P1), so no
    screen function needed to change. `tools.setup_tui.app._drive_screens` constructs one of
    these per screen visited, wrapping whatever real backend `_select_backend` chose, seeded with
    that SAME screen's own answers from its last visit (if this is a revisit) so a re-entered
    screen can offer them back as defaults/hints -- `design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md`
    §1(a)'s "re-enter the screen with its previous answers offered as defaults".

    `emit`/`suspend` pass straight through -- this wrapper touches no screen COPY, only the
    answer-collection seam."""

    def __init__(self, inner: Ui, *, prior_answers: dict[str, object] | None = None) -> None:
        self._inner = inner
        self._prior = dict(prior_answers or {})
        # Every answer THIS visit actually gave, keyed by the exact prompt string -- read back by
        # `tools.setup_tui.flow_position.FlowPosition.record` once the screen returns normally, so
        # the NEXT time this screen is (re-)entered its own `_prior` above is seeded from here.
        self.answers: dict[str, object] = {}

    def emit(self, element: object) -> None:
        self._inner.emit(element)

    def suspend(self):
        return self._inner.suspend()

    def _note_prior(self, prompt: str) -> None:
        # BUG FIX (found live while building design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md's
        # --initial-config seam, which is the first caller to reliably populate `_prior` for a
        # `ScriptedUi`-backed run): this used to call `self._inner.say(...)`, a method the typed-
        # UI migration REMOVED without a shim (`Ui`'s own module docstring: "not shimmed") --
        # `ScriptedUi`/`InteractiveUi` have no `say`, so ANY revisit (or, now, any
        # `--initial-config` default) with a real prior value raised `AttributeError` the moment
        # it fired (seen-red/setup-tui-navigation's own case 3, pre-existing and RED on this
        # build's base commit before this fix -- confirmed via `git stash`). Routed through the
        # SAME typed `emit`/`Note` vocabulary every other operator-facing line in this package
        # uses now, tone="info" (the same tone `app.py`'s own NAV_HINT line uses).
        prior = self._prior.get(prompt)
        if prior is not None:
            self._inner.emit(Note(
                f"  (you answered this {prior!r} last time -- press enter to keep it, or "
                f"answer again)", tone="info"))

    def ask_text(self, prompt: str, default: str | None = None) -> str:
        self._note_prior(prompt)
        prior = self._prior.get(prompt)
        eff_default = prior if isinstance(prior, str) else default
        val = self._inner.ask_text(prompt, eff_default)
        if val is BACK:
            raise NavigateBack()
        self.answers[prompt] = val
        return val

    def ask_choice(self, prompt: str, options: list[tuple[str, str]]) -> str:
        self._note_prior(prompt)
        val = self._inner.ask_choice(prompt, options)
        if val is BACK:
            raise NavigateBack()
        self.answers[prompt] = val
        return val

    def confirm(self, prompt: str, default: bool = False) -> bool:
        self._note_prior(prompt)
        prior = self._prior.get(prompt)
        eff_default = prior if isinstance(prior, bool) else default
        val = self._inner.confirm(prompt, eff_default)
        if val is BACK:
            raise NavigateBack()
        self.answers[prompt] = val
        return val

    def pause(self, prompt: str = "Press enter when done: ") -> None:
        val = self._inner.pause(prompt)
        if val is BACK:
            raise NavigateBack()
        return None


def build_ui(scripted_path: str | None) -> Ui:
    if scripted_path:
        return ScriptedUi(scripted_path)
    if not sys.stdin.isatty():
        raise SystemExit(
            "setup_tui: stdin is not a terminal and --scripted was not given -- refusing to "
            "run an interactive flow against a non-interactive stdin (it would hang or read "
            "garbage). Pass --scripted <answers-file> for a non-interactive run."
        )
    return InteractiveUi()
