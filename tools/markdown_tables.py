#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T14:08:12Z
#   last-change: 2026-07-15T14:14:11Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

r"""markdown_tables — the single-home GitHub-flavored-markdown (GFM) table parser, renderer,
and mechanical classifier for this project's doc corpus (work item doc-table-mechanization,
maintainer commission 2026-07-15).

WHY THIS EXISTS, and why it is NOT `tools/experiments/typed_table.py`. That prior work
(vestigial_documentation/design/ORCH-TYPED-TABLE-EXPERIMENT.md) is a CONSTRUCTOR: it builds a table from Python calls
that carry a mandatory, hand-written `inhabits=` semantic judgment per row — it has no `parse()`
and cannot ingest a table that already exists as markdown text, so it is not directly liftable
as the corpus-fixing engine this work item needs. What DOES single-home cleanly (ADR-0012 P1 —
one definition, never a second driftable copy) is the low-level markdown ROW-RENDERING format:
`render_row`/`render_separator` below are the one definition, and `typed_table.py`'s
`Table.render()` has been refactored to import and call them rather than re-typing the same
`"| " + " | ".join(...) + " |"` join a second time. That is the scouted experiment "lifted in"
to the extent it is sound to lift: its rendering primitive, not its (incompatible-purpose,
semantic-judgment-requiring) construction discipline.

WHAT THIS MODULE ADDS, new: a PARSER (`find_tables`) that reads existing markdown text and
locates every table-shaped region, plus a CLASSIFIER that calls each one CORRECT or
ATTEMPTED-BUT-BORKED, plus a content-preserving FIXER (`fix_text`) for the one borked shape
that is mechanically repairable without semantic judgment.

THE FOUR CLASSIFIER RULES (the commission's own heuristics list, each with a soundness note —
ADR-0011's measure-first discipline: state what a rule can and cannot conclude):

  1. MISSING-SEPARATOR — one or more consecutive "row-candidate" lines (see below) with no
     GFM-valid delimiter row as the second line of the block. CAN conclude: no delimiter row
     exists where GFM requires one, so no renderer will treat this as a table at all (it falls
     back to a paragraph of literal pipe text). CANNOT conclude the author intended a table —
     a block could legitimately be prose with a stray pipe; row-candidacy (below) is designed
     to keep this rare, not to eliminate it.
  2. SEPARATOR-WITHOUT-HEADER — the block's FIRST line is itself delimiter-row-shaped (matches
     the empty-cell dash/colon pattern). CAN conclude: there is no header text a reader could
     read as the label column's type former (ADR-0000's own reading of a table, per
     vestigial_documentation/design/ORCH-TYPED-TABLE-EXPERIMENT.md) sitting above the separator. CANNOT conclude why —
     a deleted header line, or a stray decorative rule, look identical to this rule.
  3. CELL-COUNT-MISMATCH — the delimiter row's cell count is well-formed but a data row's cell
     count (escape-aware, see `split_cells`) differs from the header's. CAN conclude: at least
     one row will render mis-aligned or with a blank/truncated cell under GFM's own leniency
     rule (extra cells dropped, missing cells padded empty) — a defect even though most
     renderers do not hard-fail on it. CANNOT conclude which side is wrong (header short, or
     data row long) without reading the content.
  4. SEPARATOR-INVALID-CHARS — a line in the delimiter-row POSITION (immediately below a
     header-shaped line) that is clearly an ATTEMPT at a separator (every cell consists only of
     dash-like, colon, and whitespace characters — colon, hyphen, en-dash, em-dash) but fails
     the strict GFM delimiter grammar (only `-`/`:` are valid; an em-dash is not). CAN conclude:
     the author tried to write a separator row and used the wrong character, almost always by
     the common typographic-substitution slip (an editor or paste autocorrecting `-` to `—`).
     This is the ONLY one of the four that is CONTENT-PRESERVINGLY FIXABLE: a delimiter row
     carries no content (GFM spec — its cells are pure structure), so replacing the wrong-char
     attempt with a canonical `---`-per-column row changes zero content tokens anywhere in the
     table. CANNOT conclude the cell COUNT is right even when the chars are fixed — a count
     mismatch (rule 3) is checked and reported separately, never silently absorbed into this fix.

  A fifth heuristic named in the commission, ESCAPED-PIPE CONFUSION, is checked as a WARNING,
  not a fifth borked classification: `split_cells` below is escape-aware (`\|` is a literal
  pipe, not a cell boundary) by construction, so a row containing `\|` is parsed correctly by
  this module either way. What is flagged is the WEAKER, real risk: whether a NAIVE (non-escape-
  aware) split of the same line would have produced a different cell count than this module's
  escape-aware split — i.e., whether a plainer parser could misread this specific row. That is
  reported as `escaped_pipe_risk` on the block, informational only, never its own borked verdict
  (this module's own reading of the row is not in doubt; a different tool's might be).

ROW-CANDIDATE LINES, the detection boundary (kept deliberately narrow — MEASURED, not assumed;
see `is_block_start`'s own docstring for the false-positive corpus that drove this). A block may
only be STARTED by a line whose stripped form both starts AND ends with an unescaped `|` — the
house convention this corpus's real tables use throughout. A looser test (merely containing >=2
unescaped pipes, with no leading/trailing requirement) is used ONLY to CONTINUE an
already-started block, catching a row that drops its trailing pipe by mistake without
mis-firing on this corpus's common bar-separated prose (`"off" | "observe" | "enforce"`) or
two-line backtick-quoted CLI grammars, neither of which starts a line with a bare `|`. A known,
named gap: a no-leading-pipe 2-column table (exactly one pipe per row) is never detected — this
corpus was measured to use the leading-pipe convention throughout, so the gap costs nothing on
the live corpus, stated here rather than silently uncovered (per gates/link_integrity.py's own
closure-statement discipline). Lines inside fenced code blocks (``` or ~~~) are never row
candidates, tracked by a running fence-toggle scan.

Exit codes for the CLI: 0 clean/report, 1 any BORKED table found (classify mode only).
Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

DELIM_CELL_RE = re.compile(r"^:?-+:?$")
ATTEMPT_DELIM_CHARS_RE = re.compile(r"^[:\-‐‑‒–—―\s]+$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def split_cells(line: str) -> list[str]:
    """Escape-aware split of one table row into cells: `\\|` is a literal pipe (never a cell
    boundary), a bounding leading/trailing `|` is stripped, and every remaining unescaped `|`
    is a boundary. This is the one place unescaping happens; both the classifier and the
    escaped-pipe-risk check below call this, never a second hand-rolled split."""
    s = line.strip()
    s = s.replace("\\|", "\x00")
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    cells = [c.replace("\x00", "\\|").strip() for c in s.split("|")]
    return cells


def _naive_split_count(line: str) -> int:
    """Non-escape-aware cell count — every literal `|` is a boundary, `\\|` included. Used only
    to compute `escaped_pipe_risk`, never to classify a table's own structure."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return len(s.split("|"))


def is_row_candidate(line: str) -> bool:
    """Loose test — used only to CONTINUE an already-started block (a row that happens to
    drop its trailing pipe). Never used to START a block; see `is_block_start` for why."""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("|"):
        return True
    # count unescaped pipes
    unescaped = len(re.sub(r"\\\|", "", stripped).split("|")) - 1
    return unescaped >= 2


def is_block_start(line: str) -> bool:
    """Strong test — used to START a block. Requires the stripped line to both START and END
    with an unescaped `|`, the house convention this corpus's real tables use throughout
    (verified by inspection before this module was written). This is deliberately narrower
    than `is_row_candidate`: this corpus also carries prose that lists bar-separated
    alternatives inline (`"off" | "observe" | "enforce"`) or backtick-quoted CLI grammars
    spanning two lines (`` `taxon: <A> | <B>` ``) — neither starts AND ends with a bare `|`,
    so neither is a block start, even though both would satisfy the looser >=2-pipes test.
    This was MEASURED, not assumed: the looser test alone produced dozens of false positives
    on this exact corpus (single-line and two-line prose, no real table), all eliminated by
    this tightening with zero loss of a real table (every real table found in this corpus's
    297 tracked docs already uses the leading-and-trailing-pipe convention)."""
    stripped = line.strip()
    if len(stripped) < 2:
        return False
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return False
    unescaped = len(re.sub(r"\\\|", "", stripped).split("|")) - 1
    return unescaped >= 1


def is_delimiter_row(cells: list[str]) -> bool:
    return bool(cells) and all(DELIM_CELL_RE.match(c) for c in cells)


def is_delimiter_attempt(cells: list[str]) -> bool:
    """Looks like someone TRIED to write a delimiter row (every cell is dash/colon/whitespace-
    only, using any dash-family character) but did not satisfy strict GFM syntax."""
    return bool(cells) and all(c != "" and ATTEMPT_DELIM_CHARS_RE.match(c) for c in cells)


@dataclass
class TableBlock:
    start_line: int  # 1-indexed, inclusive
    end_line: int  # 1-indexed, inclusive
    raw_lines: list = field(default_factory=list)
    classification: str = "CORRECT"  # or "BORKED"
    reasons: list = field(default_factory=list)
    header_cells: list = field(default_factory=list)
    data_cells: list = field(default_factory=list)  # list[list[str]]
    escaped_pipe_risk: bool = False
    fixable: bool = False


def find_tables(text: str) -> list:
    """Scan `text`, skip fenced code blocks, group consecutive row-candidate lines into blocks,
    and classify each. Returns a list of TableBlock, in document order."""
    lines = text.splitlines()
    blocks: list = []
    in_fence = False
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if FENCE_RE.match(line):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence or not is_block_start(line):
            i += 1
            continue
        start = i
        block_lines = [line]
        j = i + 1
        while j < n and not FENCE_RE.match(lines[j]) and is_row_candidate(lines[j]):
            block_lines.append(lines[j])
            j += 1
        blocks.append(_classify(start + 1, j, block_lines))
        i = j
    return blocks


def _classify(start_line: int, end_line: int, raw_lines: list) -> TableBlock:
    b = TableBlock(start_line=start_line, end_line=end_line, raw_lines=list(raw_lines))
    rows_cells = [split_cells(l) for l in raw_lines]

    # escaped-pipe risk: any row where a naive split disagrees with the escape-aware split
    for l in raw_lines:
        if "\\|" in l and _naive_split_count(l) != len(split_cells(l)):
            b.escaped_pipe_risk = True
            break

    first_cells = rows_cells[0]
    if is_delimiter_row(first_cells) or is_delimiter_attempt(first_cells):
        b.classification = "BORKED"
        b.reasons.append("separator-without-header: block's first line is a delimiter row "
                          "(or an attempt at one) with no header line above it")
        return b

    if len(raw_lines) < 2:
        b.classification = "BORKED"
        b.reasons.append("missing-separator: a single row-candidate line with no delimiter "
                          "row beneath it — not a table by GFM syntax")
        return b

    b.header_cells = first_cells
    second_cells = rows_cells[1]
    if not is_delimiter_row(second_cells):
        if is_delimiter_attempt(second_cells) and len(second_cells) == len(first_cells):
            b.classification = "BORKED"
            b.reasons.append(
                "separator-invalid-chars: row 2 is a delimiter-row ATTEMPT (dash/colon-family "
                "characters only) but fails strict GFM syntax (only '-'/':' are valid) — "
                f"got {second_cells!r}"
            )
            b.fixable = True
            # row 2 is STRUCTURAL (a separator attempt, wrong chars) — it carries no content,
            # same as a valid delimiter row, so it is excluded from data_cells exactly like the
            # valid-delimiter branch below. Content-preservation (extract_cell_stream) and the
            # cell-count check both depend on this: counting it as data would double-count a
            # decoration as a defect and would make a content-preserving fix look like a
            # content change (a real bug this module's own before/after proof caught).
            data_rows = rows_cells[2:]
        else:
            b.classification = "BORKED"
            b.reasons.append(
                "missing-separator: row 2 is not a valid (or attempted) GFM delimiter row"
            )
            # here row 2 genuinely IS data (no separator, structural or attempted, exists at
            # all) — still recorded as data so a cell-count issue below it is visible.
            data_rows = rows_cells[1:]
    else:
        data_rows = rows_cells[2:]

    b.data_cells = data_rows
    ncols = len(first_cells)
    data_line_offset = start_line + (len(raw_lines) - len(data_rows))
    for idx, dc in enumerate(data_rows):
        if len(dc) != ncols:
            b.classification = "BORKED"
            b.fixable = False  # a count mismatch is never mechanically fixable content-preservingly
            b.reasons.append(
                f"cell-count-mismatch: row {idx} (line {data_line_offset + idx}) has "
                f"{len(dc)} cell(s), header declares {ncols}"
            )
    return b


def render_row(cells: list) -> str:
    """The one definition of a rendered GFM table row. `tools/experiments/typed_table.py`
    imports this rather than re-typing the join (ADR-0012 P1)."""
    return "| " + " | ".join(cells) + " |"


def render_separator(ncols: int) -> str:
    """The one definition of a canonical (hyphen-only) GFM delimiter row."""
    return "| " + " | ".join(["---"] * ncols) + " |"


def fix_block(block: TableBlock) -> "str | None":
    """Return the repaired block text if `block` is content-preservingly fixable, else None.
    Only SEPARATOR-INVALID-CHARS (rule 4) is fixable: the delimiter row carries no content, so
    replacing it with a canonical hyphen row changes zero content tokens. Every other borked
    reason is left untouched by design (the maintainer's explicit preference — an unfixed table
    beats a hand-fixed one)."""
    if not block.fixable:
        return None
    ncols = len(block.header_cells)
    new_lines = list(block.raw_lines)
    new_lines[1] = render_separator(ncols)
    return "\n".join(new_lines)


def fix_text(text: str) -> "tuple[str, list]":
    """Apply `fix_block` to every fixable block found in `text`. Returns (new_text, report)
    where report is a list of dicts, one per block touched, each naming the line range and the
    reason fixed. Blocks that are not fixable are left byte-for-byte untouched."""
    blocks = find_tables(text)
    lines = text.splitlines()
    report = []
    # apply from bottom to top so earlier line numbers stay valid as we splice
    for b in sorted(blocks, key=lambda b: b.start_line, reverse=True):
        if b.classification != "BORKED" or not b.fixable:
            continue
        fixed = fix_block(b)
        if fixed is None:
            continue
        fixed_lines = fixed.split("\n")
        lines[b.start_line - 1:b.end_line] = fixed_lines
        report.append({"start_line": b.start_line, "end_line": b.end_line,
                        "reasons": b.reasons})
    new_text = "\n".join(lines)
    if text.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"
    report.sort(key=lambda r: r["start_line"])
    return new_text, report


def extract_cell_stream(text: str) -> list:
    """Every cell of every table block, in document order, as a flat list of strings — the
    content-preservation proof primitive: two calls of this function (before/after a fix)
    compared for equality prove a fix changed no cell content, only separator syntax."""
    out = []
    for b in find_tables(text):
        for row in ([b.header_cells] if b.header_cells else []) + b.data_cells:
            out.extend(row)
    return out


# --------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------

def _classify_file(path: Path) -> list:
    return find_tables(path.read_text(encoding="utf-8"))


def cmd_classify(paths: list) -> int:
    any_borked = False
    correct = borked = 0
    for p in paths:
        path = Path(p)
        blocks = _classify_file(path)
        for b in blocks:
            if b.classification == "BORKED":
                borked += 1
                any_borked = True
                print(f"BORKED  {path}:{b.start_line}-{b.end_line}")
                for r in b.reasons:
                    print(f"          {r}")
                if b.escaped_pipe_risk:
                    print("          (escaped-pipe-risk: a naive parser could miscount this "
                          "row's cells)")
            else:
                correct += 1
    print(f"\nmarkdown_tables: {correct} correct, {borked} borked, over {len(paths)} file(s)")
    return 1 if any_borked else 0


def cmd_apply(paths: list) -> int:
    for p in paths:
        path = Path(p)
        text = path.read_text(encoding="utf-8")
        before_cells = extract_cell_stream(text)
        new_text, report = fix_text(text)
        after_cells = extract_cell_stream(new_text)
        if not report:
            print(f"{path}: nothing mechanically fixable")
            continue
        if before_cells != after_cells:
            print(f"{path}: REFUSING to write — cell stream changed by the fix (should be "
                  f"impossible; not writing)", file=sys.stderr)
            return 2
        path.write_text(new_text, encoding="utf-8")
        print(f"{path}: fixed {len(report)} table(s): "
              f"{[ (r['start_line'], r['end_line']) for r in report ]}; cell stream unchanged "
              f"({len(before_cells)} cells)")
    return 0


def cmd_cells(paths: list) -> int:
    out = {str(p): extract_cell_stream(Path(p).read_text(encoding="utf-8")) for p in paths}
    print(json.dumps(out, indent=2))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+", help="markdown file(s) to process")
    ap.add_argument("--apply", action="store_true",
                     help="content-preservingly fix every mechanically-fixable table in place")
    ap.add_argument("--cells", action="store_true",
                     help="dump the extracted cell stream (JSON) instead of classifying")
    args = ap.parse_args(argv)
    if args.cells:
        return cmd_cells(args.files)
    if args.apply:
        return cmd_apply(args.files)
    return cmd_classify(args.files)


if __name__ == "__main__":
    sys.exit(main())
