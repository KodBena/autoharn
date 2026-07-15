#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T14:11:41Z
#   last-change: 2026-07-15T14:12:34Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""doc_tables — the mechanical GFM-table-shape checker (work item doc-table-mechanization,
maintainer commission 2026-07-15). Wraps `tools/markdown_tables.py` (the single-home GFM table
parser/renderer/classifier) as a gate, following `gates/link_integrity.py`'s own precedent:
same two declared exclusions, same GATE-mode-vs-REPORT-mode split as `gates/doc_shapes.py`.

CLOSURE STATEMENT (ADR-0000 Rule 2a):
  - INVARIANT: every table-shaped region `tools/markdown_tables.find_tables` locates in a
    tracked `*.md` file in scope classifies CORRECT — no MISSING-SEPARATOR,
    SEPARATOR-WITHOUT-HEADER, CELL-COUNT-MISMATCH, or SEPARATOR-INVALID-CHARS reason recorded
    against it (see `tools/markdown_tables.py`'s own docstring for the four rules' soundness
    stories).
  - QUANTIFICATION UNIVERSE: every table-shaped region found by that same classifier's own
    row-candidate detection, in every git-TRACKED `*.md` file in scope, minus the two
    exclusions below (both printed on every run, never silent — link_integrity.py's own
    discipline, reused rather than re-invented).
  - DENOMINATION: the resource is "a table-shaped region", not a proxy (not doc count, not
    line count) — one violation per borked table, every occurrence reported with its reason(s).

EXCLUSIONS (both declared, both principled, matching link_integrity.py's own two exactly —
this gate rides the same judgment about what "live" documentation means):
  1. judgment/** — predecessor era, history unless a current spec cites it (ORCH-OPERATING-
     CARD.md's own words, quoted in link_integrity.py).
  2. vestigial_documentation/** — the 2026-07-12 vestigial-doc-sweep's declared-history
     archive; carried as a design witness, not live authority. NOTE, and stated honestly: this
     work item's own corpus scan found borked tables inside
     vestigial_documentation/research/nlp-logic-interface/INVENTORY.md and fixed them anyway
     (the fix is content-preserving and costs nothing to apply even to an excluded doc) — the
     EXCLUSION here governs what this GATE blocks going forward, not what the one-time corpus
     sweep was permitted to mechanically repair. A borked table under this prefix is reported
     in REPORT mode (never silently invisible) but never fails GATE mode.

MODES, mirroring gates/doc_shapes.py:
  - `python3 gates/doc_tables.py FILE [FILE...]` — GATE mode: exit 1 listing every borked table
    found in the named files (after the two exclusions), exit 0 clean.
  - `python3 gates/doc_tables.py` — REPORT mode over every tracked `*.md`: prints findings
    (including the two excluded prefixes, clearly labeled), ALWAYS exits 0.

Exit codes: 0 clean (or report mode), 1 violations in gate mode, 2 usage/IO error.
Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))
from markdown_tables import find_tables  # noqa: E402

EXCLUDED_PREFIXES = ("judgment/", "vestigial_documentation/")


def _excluded(relpath: str) -> "str | None":
    for prefix in EXCLUDED_PREFIXES:
        if relpath.startswith(prefix):
            return prefix
    return None


def _tracked_md() -> list:
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-files", "*.md"],
                          capture_output=True, text=True, check=True)
    return [l for l in out.stdout.splitlines() if l.strip()]


def _scan_file(path: Path) -> list:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"IO ERROR reading {path}: {exc}"]
    findings = []
    for b in find_tables(text):
        if b.classification == "BORKED":
            findings.append(f"{path}:{b.start_line}-{b.end_line}: " + "; ".join(b.reasons))
    return findings


def _to_relpath(f: str) -> str:
    """Best-effort path relative to REPO_ROOT, for the exclusion-prefix check only. A path
    outside the repo (a temp-dir fixture, e.g.) has no meaningful relpath — falls back to the
    given string as-is, which simply will not match either exclusion prefix."""
    p = Path(f)
    if not p.is_absolute():
        return f
    try:
        return str(p.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return f


def cmd_gate(files: list) -> int:
    violations = []
    for f in files:
        relpath = _to_relpath(f)
        excl = _excluded(relpath)
        if excl:
            print(f"doc-tables: {relpath} under excluded prefix {excl!r} — not gated")
            continue
        violations.extend(_scan_file(Path(f)))
    if violations:
        print(f"doc-tables: {len(violations)} borked table(s):\n")
        for v in violations:
            print(f"  !! {v}")
        return 1
    print("doc-tables: clean ✓")
    return 0


def cmd_report() -> int:
    print(f"doc-tables REPORT mode — declared exclusions (never silent): {EXCLUDED_PREFIXES}\n")
    total_borked = 0
    total_correct = 0
    for f in _tracked_md():
        excl = _excluded(f)
        findings = _scan_file(REPO_ROOT / f)
        text = (REPO_ROOT / f).read_text(encoding="utf-8")
        blocks = find_tables(text)
        total_correct += sum(1 for b in blocks if b.classification == "CORRECT")
        if findings:
            total_borked += len(findings)
            label = f" (EXCLUDED: {excl})" if excl else ""
            print(f"{f}{label}:")
            for v in findings:
                print(f"  !! {v}")
    print(f"\ndoc-tables: {total_correct} correct table(s), {total_borked} borked table(s), "
          f"over {len(_tracked_md())} tracked *.md file(s). REPORT mode always exits 0.")
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        return cmd_report()
    return cmd_gate(argv)


if __name__ == "__main__":
    sys.exit(main())
