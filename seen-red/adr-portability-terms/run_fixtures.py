#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-13T20:02:31Z
#   last-change: 2026-07-13T20:02:31Z
#   contributors: 3c942a60/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for gates/adr_portability_terms.py (the ADR
portability refactor's §5 A1 acceptance gate; design/MAINT-ADR-PORTABILITY-SPEC.md §8 WP-0;
gates/fixture_census.py REGISTRY entry "adr-portability-terms").

Four cases, all against synthetic fixtures in a throwaway temp directory (never against
tracked repo content, exactly the reasoning seen-red/link-integrity/run_fixtures.py already
gives: an intentionally-defective fixture committed as tracked content would itself trip the
gate's own real run):

  CASE 1 (RED)  -- a fixture ADR with a project-bound term in live Decision prose. The gate
                   must name the term and exit 1 (gate mode).
  CASE 2 (GREEN) -- the identical shape, but every occurrence of the same terms sits inside
                   one of the three sanctioned shields (a Provenance bullet, a dated Amendment
                   section, an Extraction Pointer blockquote). The gate must exit 0 (gate mode).
  CASE 3 (REPORT, synthetic) -- report mode pointed (via monkeypatch of
                   `adr_portability_terms._adr_top_level_files`) at a temp directory holding
                   only CASE 2's clean fixture: exit 0, proving report mode reflects true
                   findings rather than being hardcoded to any fixed exit code.
  CASE 4 (NEGATIVE CONTROL, informational) -- the gate's real report mode, run against the
                   actual `law/adr/*.md` corpus as it stands today (pre-refactor, before any
                   of design/MAINT-ADR-PORTABILITY-SPEC.md's WP-1..WP-13 have run). This is
                   the negative control ADR-0011's 2026-07-02 amendment names ("shown red on
                   the pre-refactor tree before its green is credited") -- it is EXPECTED
                   non-zero today and is not counted as a failure of this fixture; its purpose
                   is to keep a live witness of the gate detecting the real, unshielded corpus,
                   not just a synthetic specimen. The count is printed, not asserted, because it
                   legitimately falls as later work packages extract the flagged prose.

No network, no DB, no cost: pure-stdlib gate, temp files only for cases 1-3.

Usage: python3 seen-red/adr-portability-terms/run_fixtures.py
Exit 0 if cases 1-3 match their expected polarity; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "gates"))
import adr_portability_terms as g  # noqa: E402

GATE = REPO / "gates" / "adr_portability_terms.py"

BAD = """# ADR-9999: fixture (unshielded)

- **Status:** Accepted
- **Genre:** Tenet

## Decision

We adopt this rule for chocofarm because it worked there.
"""

GOOD = """# ADR-9999: fixture (shielded)

- **Status:** Accepted
- **Genre:** Tenet
- **Provenance:** Native to chocofarm, transferred here.

## Decision

We adopt this generic rule.

## Amendment — 2026-06-01: a dated note

This amendment mentions throughput-lab and fact-mining for context.

> **Extracted record — the fixture specimen**
> *(moved verbatim to history/9999-fixture.md)*: a chocofarm/FFXIII/LengYue
> worked example lived here before extraction.
"""


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GATE), *args],
                          capture_output=True, text=True, cwd=REPO)


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "0001-fixture.md"
        good = Path(td) / "0002-fixture.md"
        bad.write_text(BAD, encoding="utf-8")
        good.write_text(GOOD, encoding="utf-8")

        red = run(str(bad))
        print(f"CASE 1 (unshielded term, gate mode): exit={red.returncode}")
        print(red.stdout.rstrip())
        if red.returncode != 1:
            failures.append("expected exit 1 on the unshielded fixture")
        if "chocofarm" not in red.stdout:
            failures.append("expected the offending term named in the red output")

        green = run(str(good))
        print(f"CASE 2 (every term shielded, gate mode): exit={green.returncode}")
        print(green.stdout.rstrip())
        if green.returncode != 0:
            failures.append(f"expected exit 0 on the shielded fixture; stdout: {green.stdout}")

        orig = g._adr_top_level_files
        g._adr_top_level_files = lambda: [good]
        try:
            rc = g.main([])
        finally:
            g._adr_top_level_files = orig
        print(f"CASE 3 (report mode, synthetic clean dir): exit={rc}")
        if rc != 0:
            failures.append("expected exit 0 in report mode over a clean synthetic corpus")

    # CASE 4 — negative control against the REAL corpus, informational only.
    real = run()
    print(f"CASE 4 (negative control -- real law/adr/*.md, report mode): exit={real.returncode}")
    print(real.stdout.splitlines()[0] if real.stdout else "(no output)")
    print("  (EXPECTED non-zero pre-refactor -- ADR-0011's 2026-07-02 amendment: shown red "
          "before its green is credited. Not counted as a fixture failure; it legitimately "
          "goes green only as design/MAINT-ADR-PORTABILITY-SPEC.md's WP-1..WP-13 land.)")

    if failures:
        print("adr-portability-terms red-specimen: FAILED —", "; ".join(failures))
        return 1
    print("adr-portability-terms red-specimen: all synthetic cases behaved as designed -- "
          "red on the unshielded term, green on the fully-shielded fixture, report mode "
          "reflecting true findings; the real corpus negative control is printed above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
