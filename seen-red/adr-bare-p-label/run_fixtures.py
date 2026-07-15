#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T00:00:00Z
#   last-change: 2026-07-14T18:08:54Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for gates/adr_bare_p_label.py (the mechanical
bare-P-label detector; work item adr-bare-p-label-detector, this project's tracker, ledger
row 573; gates/fixture_census.py REGISTRY entry "adr-bare-p-label").

Synthetic fixtures in a throwaway temp directory (never against tracked repo content --
seen-red/link-integrity/run_fixtures.py's standing reason applies here too: a defective
fixture committed as tracked content would itself trip the gate's own real run):

  CASE 1 (RED)   -- a fixture citing P3 with no gloss and no link: exit 1, term named.
  CASE 2 (GREEN) -- the identical citation, glossed with a parenthetical: exit 0.
  CASE 3 (GREEN) -- the identical citation, as a markdown link into 0012's own #p<n> anchor:
                    exit 0.
  CASE 4 (GREEN) -- a SECOND, later mention of the SAME label in the SAME document, bare:
                    exit 0 -- Rule 2(a) obligates the FIRST use only.
  CASE 5 (GREEN) -- a gloss that is split across a markdown line-wrap (the real-corpus shape
                    this gate's 2026-07-14 build measured and fixed): exit 0.
  CASE 6 (GREEN) -- the corpus's own "nine numbered principles P1-P9 are that document's own
                    section labels" range-introduction idiom: exit 0.
  CASE 7 (RED)   -- a bolded label with NO trailing gloss (`**P4**` followed by unrelated
                    prose, no parenthetical): exit 1 -- proves Shield 2's markdown-emphasis
                    tolerance (added for the `**P2** (...)` shape) does not over-shield a
                    genuinely bare bolded citation.
  CASE 8 (REPORT, synthetic) -- report mode pointed (via monkeypatch of
                    `adr_bare_p_label._law_files`) at a temp file holding CASE 2's clean
                    fixture: exit 0.
  CASE 9 (NEGATIVE CONTROL, informational) -- the gate's real report mode against the actual
                    `law/**/*.md` corpus. Expected 0 as of 2026-07-14 (measured build: 19 raw
                    findings on the real corpus, all but 2 were false positives from
                    per-line (not per-paragraph) matching and a markdown-bold gloss shape,
                    both fixed in this gate before shipping; the 2 genuine bare citations
                    found (law/adr/0000:301 P7, law/adr/0013:259 P6) were fixed the same
                    session). A nonzero result here after 2026-07-14 is a live regression.

No network, no DB, no cost: pure-stdlib gate, temp files only.

Usage: python3 seen-red/adr-bare-p-label/run_fixtures.py
Exit 0 if cases 1-8 match their expected polarity; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "gates"))
import adr_bare_p_label as g  # noqa: E402

GATE = REPO / "gates" / "adr_bare_p_label.py"

CASE1_BAD = """# ADR-9995: fixture (bare P-label)

## Decision

This composes with ADR-0012 P3 in the obvious way.
"""

CASE2_GOOD = """# ADR-9995: fixture (parenthetical gloss)

## Decision

This composes with ADR-0012 P3 (no god-objects) in the obvious way.
"""

CASE3_GOOD = """# ADR-9995: fixture (markdown link)

## Decision

This composes with
[P3 (no god-objects)](0012-compositional-and-structural-hygiene.md#p3--no-god-objects)
in the obvious way.
"""

CASE4_GOOD = """# ADR-9995: fixture (second mention bare, first mention glossed)

## Decision

ADR-0012 P3 (no god-objects) applies here.

## Consequences

P3 also applies here, cited bare a second time -- this is fine, first use only.
"""

CASE5_GOOD = """# ADR-9995: fixture (gloss split across a line wrap)

## Decision

A boundary is a type that translates-and-validates and refuses what it cannot honor (ADR-0012
P3).
"""

CASE6_GOOD = """# ADR-9995: fixture (range-intro idiom)

## Context

[ADR-0012 (compositional and structural hygiene)](0012-compositional-and-structural-hygiene.md)
-- whose nine numbered principles P1-P9 are that document's own section labels -- ranks highly.
"""

CASE7_BAD = """# ADR-9995: fixture (bolded, still bare)

## Decision

**ADR-0012 P4** is cited here with no trailing gloss at all, just unrelated prose that follows.
"""


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GATE), *args],
                          capture_output=True, text=True, cwd=REPO)


def _check(label: str, path: Path, expect_clean: bool, failures: list[str],
           must_contain: str | None = None) -> None:
    result = run(str(path))
    print(f"{label}: exit={result.returncode}")
    print(result.stdout.rstrip())
    if expect_clean:
        if result.returncode != 0:
            failures.append(f"{label}: expected exit 0; stdout: {result.stdout}")
    else:
        if result.returncode != 1:
            failures.append(f"{label}: expected exit 1")
        if must_contain and must_contain not in result.stdout:
            failures.append(f"{label}: expected {must_contain!r} named in the red output")


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        paths = {}
        for name, text in [
            ("case1", CASE1_BAD), ("case2", CASE2_GOOD), ("case3", CASE3_GOOD),
            ("case4", CASE4_GOOD), ("case5", CASE5_GOOD), ("case6", CASE6_GOOD),
            ("case7", CASE7_BAD),
        ]:
            p = Path(td) / f"{name}.md"
            p.write_text(text, encoding="utf-8")
            paths[name] = p

        _check("CASE 1 (bare P-label, gate mode)", paths["case1"], expect_clean=False,
               failures=failures, must_contain="P3")
        _check("CASE 2 (parenthetical gloss, gate mode)", paths["case2"], expect_clean=True,
               failures=failures)
        _check("CASE 3 (markdown link into 0012, gate mode)", paths["case3"], expect_clean=True,
               failures=failures)
        _check("CASE 4 (second bare mention, first glossed, gate mode)", paths["case4"],
               expect_clean=True, failures=failures)
        _check("CASE 5 (gloss split across line wrap, gate mode)", paths["case5"],
               expect_clean=True, failures=failures)
        _check("CASE 6 (range-intro idiom, gate mode)", paths["case6"], expect_clean=True,
               failures=failures)
        _check("CASE 7 (bolded, still bare, gate mode)", paths["case7"], expect_clean=False,
               failures=failures, must_contain="P4")

        orig = g._law_files
        g._law_files = lambda: [paths["case2"]]
        try:
            rc = g.main([])
        finally:
            g._law_files = orig
        print(f"CASE 8 (report mode, synthetic clean dir): exit={rc}")
        if rc != 0:
            failures.append("CASE 8: expected exit 0 in report mode over a clean synthetic corpus")

    real = run()
    print(f"CASE 9 (negative control -- real law/**/*.md, report mode): exit={real.returncode}")
    print(real.stdout.splitlines()[0] if real.stdout else "(no output)")
    print("  (Expected 0 as of 2026-07-14; a nonzero result here is a live regression, not an "
          "expected baseline state -- unlike adr-portability-terms, this gate was measured "
          "and fixed against the real corpus before it ever shipped.)")

    if failures:
        print("adr-bare-p-label red-specimen: FAILED —", "; ".join(failures))
        return 1
    print("adr-bare-p-label red-specimen: all synthetic cases behaved as designed -- red on "
          "the genuinely bare citation and the bolded-but-ungloosed one, green on every "
          "sanctioned gloss/link/range/second-mention shape; the real corpus negative "
          "control is printed above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
