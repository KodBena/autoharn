# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T21:31:20Z
#   last-change: 2026-07-18T21:31:20Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/ui.py -- the ONE numbered-menu UI substrate (ADR-0012 P1: one home for the
prompt/print shape, no screen module talks to stdin/stdout directly).

Two backends behind the same `Ui` interface, selected once at startup by `tools/setup_tui/app.py`:

  * `InteractiveUi` -- plain `input()`/`print()`, no curses, no prompt-toolkit (see this
    package's own `__init__.py` docstring for why: neither `textual` nor `urwid` was found
    installed at build time, so the spec's numbered-menu fallback applies).
  * `ScriptedUi` -- reads answers, one per line, from a file given via `--scripted
    <answers-file>`, in the exact order the screens ask for them. It calls the SAME
    `ask_text`/`ask_choice`/`confirm`/`pause` methods a human would drive interactively; only
    where the next answer comes from differs. This is how WT1/WT2/WT3/WT4/WT5 are witnessed
    without a human at the keyboard.

Every method also ECHOES the question and the answer actually used to stdout, so a transcript of
a scripted run reads exactly like a transcript of an interactive one.
"""
from __future__ import annotations

import sys
from pathlib import Path


class ScriptExhausted(RuntimeError):
    """A ScriptedUi ran out of answers -- the answers file did not supply enough lines for the
    flow it drove. Never silently defaults; the caller sees exactly which prompt starved."""


class Ui:
    """Shared surface both backends implement. Never instantiated directly."""

    def banner(self, text: str) -> None:
        print()
        print("=" * 78)
        print(text)
        print("=" * 78)

    def say(self, text: str = "") -> None:
        print(text)

    def ask_text(self, prompt: str, default: str | None = None) -> str:
        raise NotImplementedError

    def ask_choice(self, prompt: str, options: list[tuple[str, str]]) -> str:
        """`options` is [(key, label), ...]. Returns the chosen key."""
        raise NotImplementedError

    def confirm(self, prompt: str, default: bool = False) -> bool:
        raise NotImplementedError

    def pause(self, prompt: str = "Press enter when done: ") -> None:
        raise NotImplementedError


class InteractiveUi(Ui):
    def ask_text(self, prompt: str, default: str | None = None) -> str:
        suffix = f" [{default}]" if default is not None else ""
        while True:
            raw = input(f"{prompt}{suffix}: ").strip()
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
            if raw in keys:
                return raw
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                return keys[int(raw) - 1]
            print(f"  (enter a number 1-{len(options)}, or one of: {', '.join(keys)})")

    def confirm(self, prompt: str, default: bool = False) -> bool:
        hint = "Y/n" if default else "y/N"
        raw = input(f"{prompt} [{hint}]: ").strip().lower()
        if not raw:
            return default
        return raw in ("y", "yes")

    def pause(self, prompt: str = "Press enter when done: ") -> None:
        input(prompt)


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

    def ask_text(self, prompt: str, default: str | None = None) -> str:
        val = self._next(prompt)
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
        val = self._next(prompt).lower()
        result = val in ("y", "yes", "true", "1")
        print(f"{prompt}: {'yes' if result else 'no'}   [scripted]")
        return result

    def pause(self, prompt: str = "Press enter when done: ") -> None:
        # The scripted backend still consumes one answer line here -- this is the exact point a
        # WT3 (lie-detection) or WT4 (mid-flow-kill) witness controls: the answers file names
        # what the operator claims ("done") vs. what they actually did (nothing), and the
        # post-keypress probe downstream is what catches the gap, not this method itself.
        val = self._next(prompt)
        print(f"{prompt}{val}   [scripted]")


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
