#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T00:00:00Z
#   last-change: 2026-07-14T18:07:55Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""adr_bare_p_label -- the mechanical bare-P-label detector, work item
adr-bare-p-label-detector (this project's tracker, ledger row 573), maintainer go-ahead
2026-07-14 ("AUTOMATE IT" -- his emphasis).

WHAT IT CATCHES: ADR-0012's nine numbered principles (P1-P9, its own `#### P<n> -- ...`
section labels) recurred as a defect class at least four times during the 2026-07-14
adr-portability refactor -- caught only by manual verification passes each time (WP-7's
0011, WP-8's 0013, the C8/0002 companion, WP-13's own corpus-close pass) -- a P<n> token
cited elsewhere in the corpus with no inline gloss and no link into 0012's anchor for it,
leaving a zero-context reader unable to tell what P<n> even names, let alone where it is
defined. This gate mechanizes the check that manual review kept independently rediscovering.

THE RULE (per ADR-0017 Rule 2(a), "coined terms link to their definition on first use, and
the definition lands in the same change as the coinage" -- P1-P9 are exactly such coined
terms, defined once in ADR-0012): a P<n> token's FIRST occurrence in a document must be
shielded by one of:

  1. A MARKDOWN LINK whose target resolves into ADR-0012's own anchor for that P<n> (the
     established corpus form: `[P7 (cross-language wire discipline)](0012-...md#p7--...)`
     or the bare `[P8](0012-...md#p8--...)` form -- gates/link_integrity.py already owns
     whether the target actually resolves; this gate checks only that the link SHAPE points
     at 0012's own P<n> anchor).
  2. A PARENTHETICAL GLOSS immediately following the token on the same line (the established
     prose form: `P6 (substantiate equivalence/perf claims)`), or an ESTABLISHED-PRINCIPLE
     PARENTHETICAL immediately preceding it: `ADR-0012's numbered principle P8 ("single
     source of truth")` and its near-variants -- checked narrowly as "the token sits inside a
     parenthesized span, or a parenthesized span opens within a short lookahead window on the
     same line."

A SECOND and later occurrence of the SAME P<n> in the SAME document is never flagged --
per Rule 2(a), the obligation is "on first use," and a document that glossed P8 once is not
required to re-gloss every later mention (the corpus's own established practice, e.g.
law/adr/0000 links P8 once near its own top and cites it bare six more times below).

SCOPE, STATED HONESTLY (ADR-0011 Rule 1): this is a narrow, measured-sound heuristic, not a
prose comprehension check (no mechanism reads prose comprehension -- ADR-0017 Rule 1 already
says so). It will not catch a first-use gloss phrased as free-running prose with no
parentheses at all (e.g. "its P1 single-source-of-truth principle" with no parens) --
MEASURED against the real corpus at build time (2026-07-14): the residual after the two
shields above is inspected by hand and either represents a genuine unglossed citation (fixed)
or a free-prose gloss shape that recurs enough to earn a third shield (a later, sound
addition, not built speculatively here -- ADR-0011 Rule 4). The measurement is banked in this
gate's own seen-red fixture.

SCOPE OF FILES: `law/**/*.md`, excluding law/adr/0012-compositional-and-structural-hygiene.md
itself (P1-P9's own home -- every use there is a definition, not a citation) and
law/adr/history/**/*.md (frozen verbatim extractions, ADR-0005 Rule 8 -- not retro-glossed).

WAIVER: `<!-- adr-bare-p-label-allow: <reason> -->` on the line or its immediate predecessor
(mirrors gates/doc_shapes.py's `doc-shapes-allow:` convention exactly) -- for a first-use that
is legitimately unglossed for a stated reason (e.g. a quoted historical passage, ADR-0017's
own quoted-defect Exception).

MODES (mirrors gates/doc_shapes.py and gates/adr_portability_terms.py):
  - `python3 gates/adr_bare_p_label.py FILE [FILE...]` -- GATE mode: check exactly the named
    files, exit 1 listing violations, exit 0 clean.
  - `python3 gates/adr_bare_p_label.py` -- REPORT mode: scans the full `law/**/*.md` scope
    above, exit code reflects the true finding count.

Exit codes: 0 clean, 1 violations found (both modes), 2 usage/IO error.
Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LAW_DIR = REPO_ROOT / "law"
EXCLUDED = {REPO_ROOT / "law" / "adr" / "0012-compositional-and-structural-hygiene.md"}
EXCLUDED_DIR = REPO_ROOT / "law" / "adr" / "history"

# A bare P-label: "P" + one digit 1-9, word-bounded (not P10, not a variable like `P1x`).
_P_LABEL = re.compile(r"\bP([1-9])\b")

# Shield 1: a markdown link whose bracket-text contains the P<n> token and whose URL targets
# 0012's own file and that P<n>'s anchor (e.g. "0012-...md#p7--..." or "...md#p7").
_MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")


_RANGE_TOKEN = re.compile(r"\bP[1-9]\s*[-–—]\s*(?:through\s+)?P[1-9]\b", re.IGNORECASE)
_PRINCIPLES_WORD = re.compile(r"\bnumbered principles\b", re.IGNORECASE)


def _paragraphs(lines: list[str]) -> list[tuple[int, int, str]]:
    """Split lines into blank-line-delimited paragraphs. Markdown wraps one sentence across
    several physical lines, so a P<n> token and its gloss/parenthetical routinely sit on
    different LINES of the same paragraph (e.g. '(ADR-0012\\nP2)') -- checking gloss shape
    per-paragraph rather than per-line is what makes this sound on the real corpus (measured
    2026-07-14: per-line matching alone false-positived on 16 of 19 findings, all genuinely
    glossed across a line wrap; see this gate's seen-red fixture for the measurement).

    Returns (start_line_idx, end_line_idx_exclusive, joined_text) triples; `joined_text` is
    the paragraph's lines joined with a single space, preserving character offsets closely
    enough to map a match position back to a line via bisection over line-start offsets."""
    paras: list[tuple[int, int, str]] = []
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].strip() == "":
            i += 1
            continue
        start = i
        chunk: list[str] = []
        while i < n and lines[i].strip() != "":
            chunk.append(lines[i])
            i += 1
        paras.append((start, i, " ".join(chunk)))
    return paras


def _line_starts(chunk: list[str]) -> list[int]:
    """Character offset (in the ' '.join(chunk) string) where each line begins."""
    starts = []
    pos = 0
    for j, ln in enumerate(chunk):
        starts.append(pos)
        pos += len(ln) + 1  # +1 for the joining space
    return starts


def _link_shields(text: str) -> dict[int, tuple[int, int]]:
    """Shield 1: {n: (start, end)} for each P<n> whose bracket-text span sits inside a link
    that targets 0012's own #p<n> anchor -- the span is the bracket-text span."""
    shields: dict[int, tuple[int, int]] = {}
    for m in _MD_LINK.finditer(text):
        link_text, url = m.group(1), m.group(2)
        url_low = url.lower()
        if "0012-compositional-and-structural-hygiene" not in url_low:
            continue
        for pm in _P_LABEL.finditer(link_text):
            n = pm.group(1)
            if f"#p{n}" in url_low:
                shields[int(n)] = m.span(1)
    return shields


def _has_parenthetical_gloss(text: str, match: re.Match) -> bool:
    """Shield 2: the token sits inside a parenthesized span, or a parenthesized span opens
    within a short lookahead window (the established 'P6 (substantiate ...)' /
    '(... P1 single source of truth ...)' / '**P2** (a boundary ...)' prose shapes), now
    measured over the whole paragraph so a line-wrapped parenthetical is not missed. `[\\s*_]*`
    absorbs markdown emphasis closers (`**`, `_`) that routinely sit between a bolded label
    and its trailing parenthetical."""
    window = 60
    start, end = match.start(), match.end()
    after = text[end:end + window]
    if re.match(r"[\s*_]*\(", after):
        return True
    before = text[:start]
    open_before = before.count("(") - before.count(")")
    return open_before > 0


def _has_range_intro_gloss(text: str, match: re.Match) -> bool:
    """Shield 3: the token is one endpoint of a same-paragraph 'P1-P9' / 'P1 through P9'
    range token that itself sits near the phrase 'numbered principles' -- the corpus's own
    established first-use idiom ('...whose nine numbered principles P1-P9 are that
    document's own section labels...', verbatim or near-verbatim in four law/ documents),
    which names what the range IS in the same breath it introduces it. Narrow by
    construction (ADR-0011 Rule 4): only the range token's own two endpoints qualify, not
    every P<n> in a paragraph that happens to also discuss 'numbered principles'."""
    for rm in _RANGE_TOKEN.finditer(text):
        if not (rm.start() <= match.start() and match.end() <= rm.end()):
            continue
        window_before = text[max(0, rm.start() - 80):rm.start()]
        window_after = text[rm.end():rm.end() + 80]
        if _PRINCIPLES_WORD.search(window_before) or _PRINCIPLES_WORD.search(window_after):
            return True
    return False


WAIVER_TOKEN = "adr-bare-p-label-allow:"


def _waived_lines(lines: list[str]) -> set[int]:
    waived: set[int] = set()
    for i, line in enumerate(lines):
        if WAIVER_TOKEN in line:
            waived.add(i)
            if i + 1 < len(lines):
                waived.add(i + 1)
    return waived


def check_file(path: Path) -> list[str]:
    """Return violation strings for the first unshielded occurrence of each P<n> in path."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as e:
        return [f"{path}:0: IO could not read file ({e})"]
    rel = path
    try:
        rel = path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        pass

    waived = _waived_lines(lines)
    seen: set[int] = set()  # P<n> values already resolved (glossed/linked) in this document
    violations: list[str] = []

    for start, end, text in _paragraphs(lines):
        chunk = lines[start:end]
        line_starts = _line_starts(chunk)
        link_shields = _link_shields(text)
        for m in _P_LABEL.finditer(text):
            n = int(m.group(1))
            if n in seen:
                continue  # not a first use -- Rule 2(a) obligates first use only
            # Map the match's character offset back to its source line for reporting.
            li = 0
            for k, ls in enumerate(line_starts):
                if ls <= m.start():
                    li = k
            src_line = start + li

            shielded_span = link_shields.get(n)
            if shielded_span and shielded_span[0] <= m.start() and m.end() <= shielded_span[1]:
                seen.add(n)
                continue
            if _has_parenthetical_gloss(text, m):
                seen.add(n)
                continue
            if _has_range_intro_gloss(text, m):
                seen.add(n)
                continue
            if src_line in waived:
                seen.add(n)
                continue
            violations.append(
                f"{rel}:{src_line + 1}: BARE P-LABEL 'P{n}' first use has no gloss or link "
                f"into 0012's #p{n} anchor — {lines[src_line].strip()!r}")
            seen.add(n)  # only the first occurrence is reported per document, per label
    return violations


def _law_files() -> list[Path]:
    """law/**/*.md, excluding 0012 itself and the frozen law/adr/history/ extractions."""
    out = []
    for p in sorted(LAW_DIR.rglob("*.md")):
        if p in EXCLUDED:
            continue
        try:
            p.relative_to(EXCLUDED_DIR)
            continue  # inside law/adr/history/ -- frozen, excluded
        except ValueError:
            pass
        out.append(p)
    return out


def main(argv: list[str]) -> int:
    gate_mode = bool(argv)
    if gate_mode:
        targets = []
        for a in argv:
            p = Path(a)
            if not p.is_absolute():
                p = REPO_ROOT / p
            if p.suffix != ".md":
                continue  # non-markdown paths pass through silently (mixed commit sets)
            if not p.exists():
                print(f"adr_bare_p_label: named file does not exist: {a}", file=sys.stderr)
                return 2
            if p.resolve() in EXCLUDED:
                continue  # 0012 itself is never checked against its own labels
            try:
                p.resolve().relative_to(EXCLUDED_DIR)
                continue  # frozen history extraction
            except ValueError:
                pass
            targets.append(p)
    else:
        targets = _law_files()

    all_violations: list[str] = []
    for p in targets:
        all_violations.extend(check_file(p))

    mode_word = "gate" if gate_mode else "report"
    if all_violations:
        print(f"adr_bare_p_label ({mode_word} mode): {len(all_violations)} finding(s) "
              f"across {len(targets)} file(s)")
        for v in all_violations:
            print(f"  {v}")
        return 1
    print(f"adr_bare_p_label ({mode_word} mode): clean — {len(targets)} file(s), 0 findings")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
