#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-13T20:01:24Z
#   last-change: 2026-07-13T20:01:24Z
#   contributors: 3c942a60/main
# <<< PROVENANCE-STAMP <<<

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

SHIELDING, exactly two mechanisms (kept deliberately narrow -- ADR-0011 Rule 4, quantify over
the class the spec actually names, not a speculative wider one):

  1. METADATA-FIELD BLOCK -- a top-level list bullet whose bold label is Provenance, Genre,
     Scope, Status, or Date (the ADR header-block fields the spec's Provenance/Genre/Scope
     citations actually sit in, e.g. 0000:30-39, 0009:14-18), from the bullet line through
     (not including) the next top-level `- **` bullet or the next heading.
  2. DATED-SECTION BLOCK -- a heading matching /Amendment|Revisit/ (case-insensitive; §4's
     "dated Amendment sections, Revisit entries that are dated appends"), from the heading
     line through (not including) the next heading at the SAME OR SHALLOWER level.
  3. EXTRACTION-POINTER BLOCK -- a contiguous blockquote (lines starting with optional
     whitespace then `>`) whose first line matches a bolded "Extracted record" label
     (law/adr/history/README.md's own worked example), through the last contiguous `>` line.

A hit inside none of the three is a VIOLATION: a project-bound term sitting in live rule or
Decision prose, exactly what A1 forbids.

WHAT THIS DOES NOT CHECK, named rather than silently omitted (ADR-0011 Rule 1): it does not
verify a Provenance/Amendment/Revisit block is itself DATED, or that a pointer's destination
link resolves (gates/link_integrity.py already owns link resolution) -- it verifies SHAPE
(is the hit sitting inside one of the three sanctioned containers), not the container's own
completeness. A block that merely LOOKS like a Provenance bullet but carries no real content
would shield a hit it should not; this is the same honestly-declared residue doc_shapes.py's
own header names for its declined heuristics.

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

WAIVER: none. Every hit is either shielded by shape or is a real finding; there is no
`<!-- adr-portability-terms-allow: -->` escape, because the acceptance criterion this gate
exists to check (A1) has no legitimate exception the spec itself does not already name as
one of the two shields above.

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

# Shield 2: dated Amendment / Revisit section headings (§4's MUST-preserve list).
_DATED_HEADING = re.compile(r"^(#{1,6})\s*.*\b(Amendment|Revisit)\b", re.IGNORECASE)
_HEADING = re.compile(r"^(#{1,6})\s")

# Shield 3: an Extraction Pointer's opening blockquote line (law/adr/history/README.md's
# worked-example shape: "> **Extracted record ...").
_POINTER_OPEN = re.compile(r"^\s*>\s*\*\*Extracted record", re.IGNORECASE)
_BLOCKQUOTE = re.compile(r"^\s*>")


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
    shielded = _shielded_lines(lines)
    violations: list[str] = []
    for i, line in enumerate(lines):
        if i in shielded:
            continue
        for m in _TERM_RE.finditer(line):
            violations.append(
                f"{rel}:{i + 1}: TERM {m.group(1)!r} not inside a shielded Provenance/"
                f"Amendment-or-Revisit/Extraction-Pointer block — {line.strip()!r}")
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
