#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-22T00:00:00Z
#   last-change: 2026-07-22T00:20:33Z
#   contributors: 1fa3ab69/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/elements.py -- the closed six-element UI content vocabulary
(design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md §1/§2, closing the maintainer's observation a: "walls
of text make reading super-hard; should have a limit on sub-element text width and clearly
deliminate distinct semantic elements").

Every piece of content the wizard shows an operator is exactly one of six frozen dataclasses
below -- `Ui.emit(element)` (`tools/setup_tui/ui.py`) is the ONE place that turns one into
actual output, via `render_text` (the ONE canonical text renderer, ADR-0012 P1: one home). The
plain/scripted backend prints `render_text(element)`'s lines verbatim; `TextualUi`
(`tools/setup_tui/ui_textual.py`) uses the SAME lines for its transcript pane's text, and may
additionally style beyond them (loud style for `Note(tone="refusal")`) but never adds or drops
content relative to this module's own rendering -- the text-parity property is preserved by
construction, not by a second hand-written copy.

THE SIX TYPES (spec §1):
  - `Heading(text, level=1)` -- section/banner. Replaces the old `Ui.banner`.
  - `Paragraph(text)` -- running prose, wrapped to the measure below.
  - `Table(headers, rows, caption=None)` -- real columns, aligned, headers visually distinct.
  - `StatusLine(label, status, detail=None)` -- one checklist/progress row; `status` is the
    existing checklist vocabulary (`tools.setup_tui.checklist`'s closed status constants), never
    free text -- enforced in `StatusLine.__post_init__` below.
  - `Note(text, tone)` -- tone in {"info", "warn", "refusal"}, mapping onto ADR-0002's loudness
    hierarchy; `refusal` renders unmissably in every backend (loud style in Textual; already-
    visible "REFUSED:"-prefixed text in the plain backend, which needed no new marker to be
    grep-able/noticeable -- this module does not invent a second, redundant one).
  - `Rule()` -- a separator (a blank output line). The only element with no content.

`render_text`'s typed-error requirement (spec §1 closure statement): raises `TypeError` on
anything that is not one of the six dataclasses above -- the negative control a fixture proves
(seen-red/setup-tui-typed-elements/).

MEASURE AND WRAPPING (spec §2). `MEASURE = 78` matches the existing banner width (the historical
`"=" * 78` rule already used by `Ui.banner`/`Heading`). Wrapping is deliberately conservative,
not maximal: `_wrap_lines` treats `text` as a sequence of already-authored VISUAL lines (split on
"\n") and only wraps a line that is ITSELF over `MEASURE` -- lines already within the measure
pass through completely unchanged, preserving every existing call site's exact text (manual
indentation, deliberate blank-line spacing, a JSON/TOML preview block's own formatting) rather
than re-flowing content nothing asked to have re-flowed. This is the honest fix for the hazard
the maintainer actually named -- unbounded width -- without silently rewriting content that was
never the complaint. A line that DOES exceed the measure is wrapped with `textwrap.wrap`,
preserving its own leading whitespace as a hanging indent for its continuation lines (so a
manually-indented sub-item that grows too long wraps as a sub-item still, not flush left)."""
from __future__ import annotations

import textwrap
from dataclasses import dataclass
from typing import Literal

from tools.setup_tui import checklist

MEASURE = 78

_NOTE_TONES = ("info", "warn", "refusal")

# The checklist module's own closed status vocabulary (`tools.setup_tui.checklist`) -- a
# `StatusLine.status` must be one of these, never free text (spec §1). Eager, module-level (no
# lazy import, CLAUDE.md).
_VALID_STATUSES = frozenset({
    checklist.WITNESSED, checklist.SKIPPED, checklist.INSTRUCTED, checklist.PREPARED,
    checklist.VERIFIED_UP, checklist.NOT_UP, checklist.REFUSED, checklist.WOULD_DO,
    checklist.DRY_SKIPPED,
})


@dataclass(frozen=True)
class Heading:
    """Section/banner -- replaces the old `Ui.banner(str)`. `level` is reserved for a future
    sub-heading distinction; every current call site is level 1 (the existing banner look)."""
    text: str
    level: int = 1


@dataclass(frozen=True)
class Paragraph:
    """Running prose. Never pre-wrapped with embedded newlines doing layout work -- see this
    module's own docstring for how `render_text` bounds width instead."""
    text: str


@dataclass(frozen=True)
class Table:
    """Real columns, aligned by `render_text`, headers visually distinct from the data rows."""
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    caption: str | None = None


@dataclass(frozen=True)
class StatusLine:
    """One checklist/progress row. `status` MUST be one of `tools.setup_tui.checklist`'s closed
    status constants -- never free text (spec §1); enforced here, construction-time (ADR-0002
    rung 1), the same posture `checklist.ChecklistItem.__post_init__` already takes for the
    identical vocabulary."""
    label: str
    status: str
    detail: str | None = None

    def __post_init__(self) -> None:
        if self.status not in _VALID_STATUSES:
            raise ValueError(
                f"StatusLine status '{self.status}' is not one of the closed checklist "
                f"vocabulary {sorted(_VALID_STATUSES)} -- never free text (spec §1)")


@dataclass(frozen=True)
class Note:
    """Tone maps onto ADR-0002's loudness hierarchy. `refusal` renders unmissably in every
    backend -- loud style in Textual (`ui_textual.TextualUi.emit`), already-visible
    "REFUSED:"-prefixed text in the plain backend."""
    text: str
    tone: Literal["info", "warn", "refusal"] = "info"

    def __post_init__(self) -> None:
        if self.tone not in _NOTE_TONES:
            raise ValueError(f"Note tone '{self.tone}' not one of {_NOTE_TONES}")


@dataclass(frozen=True)
class Rule:
    """A separator -- the only element with no content. Renders as one blank output line, the
    same visual break every existing bare `ui.say(\"\")` call site already used."""


ELEMENT_TYPES = (Heading, Paragraph, Table, StatusLine, Note, Rule)


def _wrap_lines(text: str) -> list[str]:
    """See module docstring's "MEASURE AND WRAPPING" section: only a visual line already over
    `MEASURE` is wrapped; everything else passes through verbatim. ONE further exemption: a line
    that IS a shell-command echo (its stripped content starts with the project-wide `"$ "`
    argv-preview convention -- `runner.py`'s own choke-point prints use exactly this prefix, and
    every screen's decision-time "here is the command this will run" preview copies it) is never
    wrapped, matching `runner.py`'s own single-line convention for the identical shape -- an argv
    is not prose, and splitting it across lines would both misrepresent it visually and break
    every existing witness that scans stdout for one line containing a specific flag."""
    out: list[str] = []
    for raw_line in text.split("\n"):
        if len(raw_line) <= MEASURE or raw_line.lstrip(" ").startswith("$ "):
            out.append(raw_line)
            continue
        stripped = raw_line.lstrip(" ")
        indent = raw_line[: len(raw_line) - len(stripped)]
        # `stripped`, not `raw_line`, is handed to textwrap.wrap: `initial_indent`/
        # `subsequent_indent` below ALREADY supply the leading whitespace -- passing the
        # original (still-indented) text too would double it on the wrapped first line.
        wrapped = textwrap.wrap(
            stripped, width=MEASURE, initial_indent=indent,
            subsequent_indent=indent + "  ", break_long_words=False, break_on_hyphens=False,
        )
        out.extend(wrapped or [raw_line])
    return out


def _render_status_line(sl: StatusLine) -> list[str]:
    head = f"{sl.label}: {sl.status}"
    if not sl.detail:
        return _wrap_lines(head)
    return _wrap_lines(f"{head} -- {sl.detail}")


def _col_width(headers: tuple[str, ...], rows: tuple[tuple[str, ...], ...], cap: int,
               last_uncapped: bool) -> list[int]:
    widths = [len(h) for h in headers]
    for row in rows:
        for i in range(len(headers)):
            cell = row[i] if i < len(row) else ""
            this_cap = None if (last_uncapped and i == len(headers) - 1) else cap
            for ln in str(cell).split("\n"):
                w = len(ln) if this_cap is None else min(len(ln), this_cap)
                widths[i] = max(widths[i], w)
    if last_uncapped:
        return widths
    return [min(w, cap) for w in widths]


def _render_table(t: Table) -> list[str]:
    """The LAST column is deliberately never capped/wrapped -- every existing checklist-shaped
    table's trailing column (`DETAIL`) is free-form explanatory text a screen already composes as
    one coherent line (often itself containing the exact REFUSED/WITNESSED wording a fixture
    scans stdout for via a plain substring check); wrapping it would silently split that text
    across lines and break byte-for-byte substring matching for no rendering benefit the maintainer
    actually asked for (observation a was about column headers/sub-element bounding, not the
    catch-all trailing detail). Every OTHER column still wraps within its per-column cap (spec
    §2's own rule), which is where the real "wall of text" hazard (a long, unbounded column)
    lived."""
    ncols = len(t.headers)
    if ncols == 0:
        return [t.caption] if t.caption else []
    # Per-column cap (spec §2): a cell over cap wraps within its column rather than blowing out
    # the row -- the measure is shared across columns plus a 2-char gutter between each.
    col_cap = max(8, (MEASURE - 2 * (ncols - 1)) // ncols)
    widths = _col_width(t.headers, t.rows, col_cap, last_uncapped=True)
    lines: list[str] = []
    if t.caption:
        lines.append(t.caption)
    header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(t.headers)).rstrip()
    lines.append(header_line)
    lines.append("-" * min(MEASURE, max(len(header_line), 1)))
    for row in t.rows:
        wrapped_cells: list[list[str]] = []
        for i in range(ncols):
            cell = str(row[i]) if i < len(row) else ""
            cell_lines: list[str] = []
            if i == ncols - 1:
                cell_lines.extend(cell.split("\n"))
            else:
                for ln in cell.split("\n"):
                    cell_lines.extend(textwrap.wrap(ln, width=widths[i]) or [""])
            wrapped_cells.append(cell_lines or [""])
        depth = max(len(c) for c in wrapped_cells)
        for d in range(depth):
            parts = [
                (wrapped_cells[i][d] if d < len(wrapped_cells[i]) else "").ljust(widths[i])
                for i in range(ncols)
            ]
            lines.append("  ".join(parts).rstrip())
    return lines


def render_text(element: object) -> list[str]:
    """THE canonical text renderer (spec §2, ADR-0012 P1: one home) -- used verbatim by the
    plain/scripted backend and by `TextualUi`'s transcript pane. Raises `TypeError` on anything
    not one of the six closed element types (spec §1's typed-error requirement; the negative
    control seen-red/setup-tui-typed-elements/ proves this)."""
    if isinstance(element, Heading):
        bar = "=" * MEASURE
        return ["", bar, element.text, bar]
    if isinstance(element, Rule):
        return [""]
    if isinstance(element, Paragraph):
        return _wrap_lines(element.text)
    if isinstance(element, Note):
        return _wrap_lines(element.text)
    if isinstance(element, StatusLine):
        return _render_status_line(element)
    if isinstance(element, Table):
        return _render_table(element)
    raise TypeError(
        f"render_text: {element!r} is not one of the closed element vocabulary "
        f"{[t.__name__ for t in ELEMENT_TYPES]} (design/FABLE-SETUP-TUI-TYPED-UI-SPEC.md §1)")
