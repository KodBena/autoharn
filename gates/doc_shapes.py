#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T15:09:26Z
#   last-change: 2026-07-12T01:25:24Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""doc_shapes — the deterministic core of the zero-context-reader documentation discipline
(design/ADR-DRAFT-documentation-discipline.md, Rule 3; BACKLOG "Documentation legibility
indictment (maintainer, 2026-07-11 morning)"). It catches, mechanically, the two — and only
two — legibility shapes whose false-positive load was MEASURED low enough on the real corpus
to gate on. Everything else the discipline names stays with the LLM critic
(hooks/doc_legibility_critic.py, observer-grade) and review, and this docstring records the
declined heuristics with their measurements so the next pass does not re-litigate them. The
in-repo cautionary tale this gate is designed against is gates/doc-legibility/ (the acronym
gate): witnessed 2026-07-11 reporting "1619 undefined acronym(s) across 206 docs" — 1410 of
them the token "ADR" — wired into nothing. A gate that cries wolf gets ignored; this one is
deliberately narrow.

WHAT IT CHECKS (both measured on the full 208-doc corpus, 2026-07-11):

  1. FRAGMENT — a standalone prose paragraph of <= 4 words ending in "." (the "The core
     deliverable." shape: a noun phrase doing a paragraph's job). Measured: 18 hits repo-wide,
     16 of them the ADR boilerplate license line "Public Domain (The Unlicense)." (exempted
     by name below), the remaining 2 both genuine specimens (FINDINGS.md:107 "Block-and-ask +
     witness-integrity mandate."; law/adr/0015:50 "Four rules."). Zero observed false
     positives after the license exemption.

  2. HANDOFF-POSITIONAL — a reference into user-guide/ORCH-HANDOFF.md by bare position ("HANDOFF ... item 2")
     with no quoted named handle between "HANDOFF" and the position word. HANDOFF is rewritten
     wholesale (its own header: "supersedes prior handoff wholesale"), so a positional pointer
     into it dangles on the next rewrite — the maintainer's morning defect (a), hit live on
     2026-07-11. The quoted-handle form (HANDOFF "Open work" item 1) is deliberately NOT
     flagged: it carries a stable named anchor, and it is the exact form the maintainer-
     accepted fix in commit 48dce0c uses. Nor is a QUOTED mention flagged (a match whose
     line-prefix holds an odd number of double quotes is inside a quotation — text
     diagnosing the defect, not committing it; live specimen: REVIEW-GAP's 'an earlier
     revision of this line cited "HANDOFF open-work item 2," ...'). Measured on the live
     corpus at authoring: 1 flag (vestigial_documentation/design/ORCH-ARTIFACT-VS-REQUIREMENTS-DETECTOR.md:4, a genuine
     instance — independently confirmed and fixed by the concurrent doc-legibility sweep,
     merged b5f9180 the same day), 0 false positives after the two exemptions; BACKLOG.md
     and user-guide/ORCH-HANDOFF.md (renamed from HANDOFF.md, doc-audience-taxonomy sweep 2026-07-12)
     are exempt wholesale (point-in-time entries and self-references respectively).

WHAT WAS MEASURED AND DECLINED (UNBUILT, with reasons — ADR-0011 Rule 1 honesty):

  - grounding-sentence-before-table/list: 602 hits across 208 docs. House style legitimately
    sets tables and lists directly under headings (OPERATING-CARD's maps, CLAUDE.md's rule
    lists); the shape does not discriminate defect from convention. Stays with the critic.
  - slash-soup density: no sound textual predicate found — "/" is dense in legitimate
    registers (paths, alternatives, dates) and the offending form is a paraphrase engine;
    an enumeration would fail open (ADR-0011 Rule 4). Stays with the critic.
  - coined-term-without-glossary-link: this project's coinages are common words ("world",
    "run", "stamp"); no deterministic separation of coined use from plain use. Stays with
    the critic and review.
  - jargon-first openings: a judgment about audience and register. Stays with the critic.

MODES (the ADR's Rule 4 binding point, mechanized):
  - `python3 gates/doc_shapes.py FILE [FILE...]` — GATE mode, for the touched set at
    write/commit time: exit 1 listing violations in the named files, exit 0 clean. This is
    the only blocking mode, because the discipline binds documents ON TOUCH.
  - `python3 gates/doc_shapes.py` — REPORT mode over the whole repo: prints findings,
    ALWAYS exits 0. The back-catalog migrates opportunistically, never by gate (Rule 4);
    this mode exists so the standing debt is visible, not enforced.

WAIVER: a line (or its immediate predecessor) containing `doc-shapes-allow:` is skipped —
for deliberate fragments and quoted historical references. A waiver is a claim reviewed like
any other; it names its reason inline by construction.

Exit codes: 0 clean (or report mode), 1 violations in gate mode, 2 usage/IO error.
Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Directories never scanned in report mode (not documentation surfaces).
SKIP_DIR_PARTS = {".git", ".claude", "ephemera", "node_modules", "__pycache__"}

# Check 1 exemption: the ADR boilerplate license line (16 of the 18 measured hits).
LICENSE_LINE = "Public Domain (The Unlicense)."

WAIVER_TOKEN = "doc-shapes-allow:"

FRAGMENT_MAX_WORDS = 4

# Check 2: "HANDOFF" then, within 40 chars on the same line, a positional word + number.
# The negative lookahead-free approach: match, then reject if the span between HANDOFF and
# the position word contains a double-quoted handle (a stable named anchor).
_HANDOFF_POSITIONAL = re.compile(
    r'HANDOFF(?P<between>[^.|)\n]{0,40}?)\b(?:item|entry|point|row|bullet)\s+\d+',
    re.IGNORECASE,
)

# Check 2 exemptions: point-in-time entries (BACKLOG) and HANDOFF's self-references. HANDOFF.md
# was renamed to user-guide/ORCH-HANDOFF.md by the doc-audience-taxonomy sweep (2026-07-12); the exemption
# follows the file, not the old name (a hazard caught while sweeping non-md hardcoded references).
HANDOFF_CHECK_EXEMPT_NAMES = {"BACKLOG.md", "user-guide/ORCH-HANDOFF.md"}

_HEADING = re.compile(r"#{1,6}\s")
_LIST_ITEM = re.compile(r"([-*+]|\d+\.)\s")


def _line_kind(stripped: str) -> str:
    if _HEADING.match(stripped):
        return "heading"
    if stripped.startswith("|"):
        return "table"
    if _LIST_ITEM.match(stripped):
        return "list"
    if stripped.startswith((">", "<!--")):
        return "other"
    return "prose"


def check_file(path: Path) -> list[str]:
    """Return violation strings ('path:line: CHECK message') for one markdown file."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as e:
        return [f"{path}:0: IO could not read file ({e})"]
    rel = path
    try:
        rel = path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        pass
    violations: list[str] = []
    in_code = False
    handoff_exempt = path.name in HANDOFF_CHECK_EXEMPT_NAMES
    for i, raw in enumerate(lines):
        stripped = raw.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code = not in_code
            continue
        if in_code or not stripped:
            continue
        waived = WAIVER_TOKEN in raw or (i > 0 and WAIVER_TOKEN in lines[i - 1])
        if waived:
            continue
        kind = _line_kind(stripped)

        # Check 1 — FRAGMENT: standalone short prose paragraph ending in ".".
        if kind == "prose" and stripped != LICENSE_LINE:
            prev_blank = i == 0 or not lines[i - 1].strip()
            next_blank = i + 1 >= len(lines) or not lines[i + 1].strip()
            words = stripped.split()
            if (prev_blank and next_blank and len(words) <= FRAGMENT_MAX_WORDS
                    and stripped.endswith(".") and not stripped.endswith("..")
                    and "](" not in stripped):
                violations.append(
                    f"{rel}:{i + 1}: FRAGMENT standalone {len(words)}-word paragraph "
                    f"({stripped!r}) — a noun phrase is not a paragraph; write the sentence "
                    f"(or waive with '{WAIVER_TOKEN} <reason>')")

        # Check 2 — HANDOFF-POSITIONAL: bare positional reference into a wholesale-rewritten doc.
        if not handoff_exempt:
            for m in _HANDOFF_POSITIONAL.finditer(raw):
                if '"' in m.group("between") or "“" in m.group("between"):
                    continue  # quoted named handle present — the sanctioned 48dce0c form
                # Quoted-mention exemption: if the match starts inside an open double-quoted
                # span (odd number of quote chars before it on the line), the text is QUOTING
                # a positional reference — usually to diagnose it — not making one. Live FP
                # specimen this closes: design/MAINT-REVIEW-GAP-SCOPE-SEMANTICS-RULING.md's 'an
                # earlier revision of this line cited "HANDOFF open-work item 2," ...'.
                prefix = raw[:m.start()]
                if (prefix.count('"') + prefix.count('“') + prefix.count('”')) % 2 == 1:
                    continue
                violations.append(
                    f"{rel}:{i + 1}: HANDOFF-POSITIONAL bare positional reference "
                    f"({m.group(0)!r}) into a wholesale-rewritten document — cite a quoted "
                    f"named item/anchor instead (HANDOFF \"Open work\" item N is fine), or "
                    f"waive with '{WAIVER_TOKEN} <reason>'")
    return violations


def _repo_markdown_files() -> list[Path]:
    files = []
    for p in sorted(REPO_ROOT.rglob("*.md")):
        # Skip-parts are judged RELATIVE to the repo root: the checkout itself may live
        # under a path containing ".claude" (a worktree does), and that must not skip
        # everything.
        rel_parts = p.relative_to(REPO_ROOT).parts
        if any(part in SKIP_DIR_PARTS for part in rel_parts):
            continue
        files.append(p)
    return files


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
                print(f"doc_shapes: named file does not exist: {a}", file=sys.stderr)
                return 2
            targets.append(p)
    else:
        targets = _repo_markdown_files()

    all_violations: list[str] = []
    for p in targets:
        all_violations.extend(check_file(p))

    mode_word = "gate" if gate_mode else "report"
    if all_violations:
        print(f"doc_shapes ({mode_word} mode): {len(all_violations)} finding(s) "
              f"across {len(targets)} file(s)")
        for v in all_violations:
            print(f"  {v}")
        if not gate_mode:
            print("doc_shapes: report mode never fails — the back-catalog binds on touch "
                  "(ADR draft Rule 4), not by sweep")
        return 1 if gate_mode else 0
    print(f"doc_shapes ({mode_word} mode): clean — {len(targets)} file(s), 0 findings")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
