#!/usr/bin/env python3
"""adr_portability_terms -- the §5 A1 acceptance gate for the ADR portability refactor
(design/MAINT-ADR-PORTABILITY-SPEC.md §5, §8 WP-0; law/adr/history/README.md is this gate's
own "Related" cross-reference). Mechanizes the spec's own grep, verbatim:

    grep -rniE 'chocofarm|lengyue|ffxiii|throughput-lab' law/adr/*.md
    (and 'fact-mining' outside 0015/0016's preserved provenance)

A1's acceptance bar is that every remaining hit sits either (a) inside a verbatim-preserved
dated Amendment/Provenance/Revisit block (§4's MUST-preserve list: "All dated Amendment
sections, Revisit entries that are dated appends, ratification provisos, and quoted
maintainer words"), or (b) on an Extraction Pointer line (§3, law/adr/history/README.md) --
never in live rule/Decision prose. This gate implements exactly that shielding and nothing
more.

SCOPE, STATED HONESTLY (ADR-0011 Rule 1): this gate is built in WP-0, BEFORE any ADR is
refactored (WP-1 through WP-13). Run against the corpus as it stands today, it is EXPECTED
and WITNESSED to go RED -- every project-bound term sits in ordinary Context/Provenance prose
that is not yet wrapped in a shielded block or replaced by a pointer. That RED run is this
gate's own negative control (ADR-0011's 2026-07-02 amendment: shown red before its later green
is credited) -- it proves the gate can detect the shape it exists to catch, on the real
substrate, not only on a synthetic fixture. The gate turns (and stays) GREEN only as later work
packages actually extract the flagged prose; WP-0 does not touch any existing ADR (its own
commission says so), so no attempt is made to make today's corpus pass.

SHIELDING, five mechanisms (kept deliberately narrow -- ADR-0011 Rule 4, quantify over the
class the spec actually names, not a speculative wider one). The first three shipped at
WP-0; shields 4 and 5 were added 2026-07-14 (work item adr-portability-terms-gate-shield-gaps,
ledger row 572) to close three gate-shape gaps the WP-3/WP-10/WP-12 refactor passes found and
named but had no license to fix (gates/ was out of that phase's touch license) -- corpus prose
was legitimate the whole time, the shield regex just did not recognize the shape yet:

  1. METADATA-FIELD BLOCK -- a top-level list bullet whose bold label is Provenance, Genre,
     Scope, Status, or Date (the ADR header-block fields the spec's Provenance/Genre/Scope
     citations actually sit in, e.g. 0000:30-39, 0009:14-18), from the bullet line through
     (not including) the next top-level `- **` bullet or the next heading.
  2. DATED-SECTION BLOCK -- a heading matching /Amendments?|Revisits?/ (case-insensitive;
     §4's "dated Amendment sections, Revisit entries that are dated appends"), from the
     heading line through (not including) the next heading at the SAME OR SHALLOWER level.
     The plural was added 2026-07-14: 0000/0012/0014/0016/0017 file their frozen amendment
     history under one `## Amendments` container with content-titled dated `###` sub-headings
     (e.g. "### 2026-07-02 -- Rule 2(a) sharpened...") rather than 0002/0009's one-Amendment-
     per-heading style; the old singular-only `\bAmendment\b` regex has a word boundary between
     "Amendment" and the trailing "s" that never matches, so the whole plural container went
     unrecognized and everything inside it -- legitimately frozen, dated, unretouchable per
     ADR-0005 Rule 8 -- reported as a live violation. Witnessed before the fix: 5 of the
     corpus-wide report-mode findings sat in exactly this shape (0000:405/409, 0016:393/421).
  3. EXTRACTION-POINTER BLOCK -- a contiguous blockquote (lines starting with optional
     whitespace then `>`) whose first line matches a bolded "Extracted record" label
     (law/adr/history/README.md's own worked example), through the last contiguous `>` line.
  4. MARKDOWN-LINK-TARGET -- a term match that falls entirely inside the bracket-text or the
     parenthesized URL of an inline markdown link (`[...](...)`) on the same line. Added
     2026-07-14: a link that legitimately points at a history file necessarily carries that
     file's project-bound name in its path (e.g.
     `[history/0002-chocofarm-fail-loud-substrate.md](history/0002-chocofarm-fail-loud-substrate.md)`),
     and outside a Shield-3 blockquote that link is a real reference, not prose -- ADR-0002's
     own Rule 2/Rule 4 text was forced into weaker one-hop prose ("the extracted record the
     Context's Extraction Pointer above links") specifically to dodge this gap during the
     refactor, which is the regression this shield removes the need for. This shield checks
     link SHAPE only, exactly like gates/link_integrity.py owns whether the target actually
     resolves -- this gate does not re-derive that.
  5. INLINE WAIVER COMMENT -- a line (or its immediate predecessor) containing the token
     `adr-portability-terms-allow:` inside an HTML comment is skipped, mirroring
     gates/doc_shapes.py's `doc-shapes-allow:` convention exactly. Added 2026-07-14 for the
     one class the spec's two structural shields cannot reach by shape alone: ADR-0017's own
     quoted-defect Exception ("quoting a defect to diagnose it is not a violation") cites a
     project-bound path as an in-house illegibility specimen inside ordinary Context prose,
     not inside a Provenance bullet, a dated Amendment, or an Extraction Pointer -- there is no
     structural container to widen, so a reviewed, reasoned inline waiver is the honest
     mechanism (a waiver is a claim reviewed like any other, never a silent bypass).

A hit inside none of the five is a VIOLATION: a project-bound term sitting in live rule or
Decision prose, exactly what A1 forbids.

WHAT THIS DOES NOT CHECK, named rather than silently omitted (ADR-0011 Rule 1): it does not
verify a Provenance/Amendment/Revisit block is itself DATED, or that a pointer's or a Shield-4
link's destination actually resolves (gates/link_integrity.py already owns link resolution) --
it verifies SHAPE (is the hit sitting inside one of the five sanctioned containers), not the
container's own completeness. A block that merely LOOKS like a Provenance bullet but carries no
real content would shield a hit it should not; this is the same honestly-declared residue
doc_shapes.py's own header names for its declined heuristics.

MODES (mirrors gates/doc_shapes.py's own two-mode split):
  - `python3 gates/adr_portability_terms.py FILE [FILE...]` -- GATE mode: check exactly the
    named files, exit 1 listing violations, exit 0 clean. This is the only mode a future
    pre-commit wiring would invoke (WP-0 does not wire it -- see below).
  - `python3 gates/adr_portability_terms.py` -- REPORT mode: scans `law/adr/*.md` (the literal
    scope of the spec's own grep -- NOT `law/adr/history/*.md`, which is frozen extracted
    material expected to carry these terms freely, and not recursive for that reason). Exit
    code reflects the TRUE finding count (unlike doc_shapes.py's report mode, which never
    fails by design because that ADR binds only on touch) -- A1 is a corpus-wide completeness
    criterion for the finished refactor, so a stale exit-0 report would misstate progress.
    WP-0 deliberately does NOT wire this into hooks/pre-commit: doing so today would block
    every commit until Phase 2's later work packages (WP-1..WP-13) finish extracting the
    flagged prose. Wiring is a later work package's decision (§8 WP-13's corpus-wide close),
    not this one's.

WAIVER: `<!-- adr-portability-terms-allow: <reason> -->` (Shield 5, added 2026-07-14) -- the
one narrow escape, reserved for the quoted-defect Exception class named in Shield 5 above,
where no structural container exists to widen. It is reviewed like any other waiver, never a
silent bypass: the reason travels with the marker, in the file, forever.

Exit codes: 0 clean, 1 violations found (both modes), 2 usage/IO error.
Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# The spec's own term list, §5 A1, verbatim plus the fact-mining addendum it names in the same
# sentence. Word-boundary-free (fact-mining and throughput-lab contain hyphens, not \w
# boundaries in the usual sense) but anchored so a hit is reported with real context.
TERMS = ["chocofarm", "lengyue", "ffxiii", "throughput-lab", "fact-mining"]
_TERM_RE = re.compile("(" + "|".join(TERMS) + ")", re.IGNORECASE)

# Shield 1: metadata-field bullets in the ADR header block.
_METADATA_BULLET = re.compile(r"^-\s+\*\*(Provenance|Genre|Scope|Status|Date)\s*:?\*\*", re.IGNORECASE)
_TOP_BULLET = re.compile(r"^-\s+\*\*")

# Shield 2: dated Amendment(s) / Revisit(s) section headings (§4's MUST-preserve list). The
# trailing `s?` matters: 0000/0012/0014/0016/0017 file frozen amendment history under a single
# plural "## Amendments" container, not a per-amendment singular heading (2026-07-14 fix).
_DATED_HEADING = re.compile(r"^(#{1,6})\s*.*\b(Amendments?|Revisits?)\b", re.IGNORECASE)
_HEADING = re.compile(r"^(#{1,6})\s")

# Shield 3: an Extraction Pointer's opening blockquote line (law/adr/history/README.md's
# worked-example shape: "> **Extracted record ...").
_POINTER_OPEN = re.compile(r"^\s*>\s*\*\*Extracted record", re.IGNORECASE)
_BLOCKQUOTE = re.compile(r"^\s*>")

# Shield 4 (2026-07-14): inline markdown links -- `[text](url)`. A term match is shielded if it
# falls entirely within the bracket-text span or the paren-URL span of a link on the same line.
_MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")

# Shield 5 (2026-07-14): the one inline waiver, mirroring gates/doc_shapes.py's WAIVER_TOKEN
# convention exactly -- a line (or its immediate predecessor) carrying this token is skipped.
WAIVER_TOKEN = "adr-portability-terms-allow:"


def _shielded_lines(lines: list[str]) -> set[int]:
    """Return the 0-indexed line numbers shielded by one of the three sanctioned containers."""
    shielded: set[int] = set()
    n = len(lines)

    # Shield 1: metadata bullet -> until the next top-level `- **` bullet or any heading.
    i = 0
    while i < n:
        if _METADATA_BULLET.match(lines[i]):
            shielded.add(i)
            j = i + 1
            while j < n and not _TOP_BULLET.match(lines[j]) and not _HEADING.match(lines[j]):
                shielded.add(j)
                j += 1
            i = j
        else:
            i += 1

    # Shield 2: dated Amendment/Revisit heading -> until the next heading at same-or-shallower level.
    i = 0
    while i < n:
        m = _DATED_HEADING.match(lines[i])
        if m:
            level = len(m.group(1))
            shielded.add(i)
            j = i + 1
            while j < n:
                hm = _HEADING.match(lines[j])
                if hm and len(hm.group(1)) <= level:
                    break
                shielded.add(j)
                j += 1
            i = j
        else:
            i += 1

    # Shield 3: Extraction Pointer blockquote -> contiguous `>` lines from its opening line.
    i = 0
    while i < n:
        if _POINTER_OPEN.match(lines[i]):
            shielded.add(i)
            j = i + 1
            while j < n and _BLOCKQUOTE.match(lines[j]):
                shielded.add(j)
                j += 1
            i = j
        else:
            i += 1

    return shielded


def _link_spans(line: str) -> list[tuple[int, int]]:
    """Shield 4: character spans of every inline markdown link's bracket-text and paren-URL
    on this line -- a term match wholly inside one of these spans is a link, not prose."""
    spans: list[tuple[int, int]] = []
    for m in _MD_LINK.finditer(line):
        spans.append(m.span(1))  # [text]
        spans.append(m.span(2))  # (url)
    return spans


def _waived_lines(lines: list[str]) -> set[int]:
    """Shield 5: a line, or its immediate successor, following gates/doc_shapes.py's
    WAIVER_TOKEN convention (token on line N shields lines N and N+1)."""
    waived: set[int] = set()
    for i, line in enumerate(lines):
        if WAIVER_TOKEN in line:
            waived.add(i)
            if i + 1 < len(lines):
                waived.add(i + 1)
    return waived


def check_file(path: Path) -> list[str]:
    """Return violation strings ('path:line: TERM "hit" not shielded — <excerpt>') for one file."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as e:
        return [f"{path}:0: IO could not read file ({e})"]
    rel = path
    try:
        rel = path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        pass
    shielded = _shielded_lines(lines) | _waived_lines(lines)
    violations: list[str] = []
    for i, line in enumerate(lines):
        if i in shielded:
            continue
        link_spans = _link_spans(line)
        for m in _TERM_RE.finditer(line):
            if any(start <= m.start() and m.end() <= end for start, end in link_spans):
                continue  # Shield 4: term sits wholly inside a markdown link's text or URL
            violations.append(
                f"{rel}:{i + 1}: TERM {m.group(1)!r} not inside a shielded Provenance/"
                f"Amendment-or-Revisit/Extraction-Pointer/link-target block — {line.strip()!r}")
    return violations


def _adr_top_level_files() -> list[Path]:
    """The literal scope of the spec's own grep: law/adr/*.md, non-recursive — excludes
    law/adr/history/*.md by construction (glob does not descend), which is deliberate: history
    files are frozen verbatim extractions expected to carry these terms freely."""
    return sorted((REPO_ROOT / "law" / "adr").glob("*.md"))


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
                print(f"adr_portability_terms: named file does not exist: {a}", file=sys.stderr)
                return 2
            targets.append(p)
    else:
        targets = _adr_top_level_files()

    all_violations: list[str] = []
    for p in targets:
        all_violations.extend(check_file(p))

    mode_word = "gate" if gate_mode else "report"
    if all_violations:
        print(f"adr_portability_terms ({mode_word} mode): {len(all_violations)} finding(s) "
              f"across {len(targets)} file(s)")
        for v in all_violations:
            print(f"  {v}")
        return 1
    print(f"adr_portability_terms ({mode_word} mode): clean — {len(targets)} file(s), 0 findings")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
