#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for gates/adr_portability_terms.py (the ADR
portability refactor's §5 A1 acceptance gate; design/MAINT-ADR-PORTABILITY-SPEC.md §8 WP-0;
gates/fixture_census.py REGISTRY entry "adr-portability-terms").

Cases 1-4, all against synthetic fixtures in a throwaway temp directory (never against
tracked repo content, exactly the reasoning seen-red/link-integrity/run_fixtures.py already
gives: an intentionally-defective fixture committed as tracked content would itself trip the
gate's own real run):

  CASE 1 (RED)  -- a fixture ADR with a project-bound term in live Decision prose. The gate
                   must name the term and exit 1 (gate mode).
  CASE 2 (GREEN) -- the identical shape, but every occurrence of the same terms sits inside
                   one of the three WP-0 shields (a Provenance bullet, a dated Amendment
                   section, an Extraction Pointer blockquote). The gate must exit 0 (gate mode).
  CASE 3 (REPORT, synthetic) -- report mode pointed (via monkeypatch of
                   `adr_portability_terms._adr_top_level_files`) at a temp directory holding
                   only CASE 2's clean fixture: exit 0, proving report mode reflects true
                   findings rather than being hardcoded to any fixed exit code.
  CASE 4 (NEGATIVE CONTROL, informational) -- the gate's real report mode, run against the
                   actual `law/adr/*.md` corpus as it stands today. Expected 0 now that the
                   full portability refactor (WP-1..WP-13) and the 2026-07-14 shield-gap fix
                   (work item adr-portability-terms-gate-shield-gaps) have both landed; printed
                   rather than asserted so a future regression is visible without this fixture
                   itself needing an update.

Cases 5-7 (added 2026-07-14, work item adr-portability-terms-gate-shield-gaps, ledger row
572) both-polarity-prove the three gate-shape gaps closed that day -- each proves its shield
fires on the legitimate shape AND does not over-shield adjacent unshielded prose in the same
fixture, so a shield that swallowed more than its named shape would be caught here:

  CASE 5 (Shield 2, plural Amendments container) -- a `## Amendments` heading with a
                   content-titled dated `###` sub-heading carrying a term: GREEN. A sibling
                   term placed after the container closes (a same-level heading following)
                   is RED, proving the shield's end boundary still closes.
  CASE 6 (Shield 4, markdown-link-target) -- a term inside a link's bracket-text and URL:
                   GREEN. The identical term repeated in plain prose on the same line,
                   outside the link, is RED, proving the shield is span-scoped, not
                   line-scoped.
  CASE 7 (Shield 5, inline waiver comment) -- a term on the line immediately after a
                   `<!-- adr-portability-terms-allow: -->` marker: GREEN. A second occurrence
                   two lines below the marker (outside its one-line reach) is RED, proving the
                   waiver does not silently spread past its declared scope.

No network, no DB, no cost: pure-stdlib gate, temp files only.

Usage: python3 seen-red/adr-portability-terms/run_fixtures.py
Exit 0 if cases 1-3 and 5-7 match their expected polarity; 1 otherwise. Lazy imports banned.
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

# CASE 5 -- Shield 2, plural "Amendments" container with a content-titled dated sub-heading
# (the 0000/0012/0014/0016/0017 shape). "chocofarm" inside the sub-heading's own prose must be
# shielded; "lengyue" placed after the container closes (a same-level "## " heading follows)
# must NOT be, proving the end boundary still closes.
CASE5_GOOD = """# ADR-9998: fixture, plural container shape

- **Status:** Accepted

## Amendments

### 2026-06-01 — a content-titled sub-heading

This dated sub-heading, frozen per ADR-0005 Rule 8, mentions chocofarm in its own prose.

## Related

lengyue is mentioned here, outside the Amendments container, and must be flagged.
"""

# CASE 6 -- Shield 4, markdown-link-target. The bracket-text and URL both carry "chocofarm"
# (a link to a real history file necessarily does); the same term repeated in plain prose on
# the SAME line, outside the link, must still be flagged.
CASE6_GOOD = """# ADR-9997: fixture (markdown link target)

- **Status:** Accepted

## Context

See [history/chocofarm-notes.md](history/chocofarm-notes.md) and note that chocofarm itself
is also named here in plain prose, outside the link.
"""

# CASE 7 -- Shield 5, inline waiver comment. The term on the line immediately after the marker
# is shielded; an identical term two lines further down, past the marker's one-line reach,
# must still be flagged.
CASE7_GOOD = """# ADR-9996: fixture (inline waiver comment)

- **Status:** Accepted

## Context

A quoted defect specimen follows.
<!-- adr-portability-terms-allow: quoted defect specimen, per this tenet's own Exceptions -->
(a path naming chocofarm, quoted verbatim to diagnose it)
A second, unrelated mention of chocofarm two lines below the marker's reach.
"""


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GATE), *args],
                          capture_output=True, text=True, cwd=REPO)


def _check_polarity(label: str, path: Path, expect_clean: bool, must_contain: str,
                     failures: list[str]) -> None:
    result = run(str(path))
    print(f"{label}: exit={result.returncode}")
    print(result.stdout.rstrip())
    if expect_clean:
        if result.returncode != 0:
            failures.append(f"{label}: expected exit 0 (shielded); stdout: {result.stdout}")
    else:
        if result.returncode != 1:
            failures.append(f"{label}: expected exit 1 (unshielded)")
        if must_contain not in result.stdout:
            failures.append(f"{label}: expected {must_contain!r} named in the red output")


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

        # CASE 5 -- Shield 2, plural Amendments container: GREEN inside, RED outside.
        c5 = Path(td) / "0003-fixture.md"
        c5.write_text(CASE5_GOOD, encoding="utf-8")
        _check_polarity("CASE 5 (plural Amendments container, gate mode)", c5,
                         expect_clean=False, must_contain="lengyue", failures=failures)
        c5_stdout = run(str(c5)).stdout
        if "chocofarm" in c5_stdout:
            failures.append("CASE 5: the Amendments-container term leaked past its shield")

        # CASE 6 -- Shield 4, markdown-link-target: link occurrence shielded, prose occurrence
        # on the same line still flagged.
        c6 = Path(td) / "0004-fixture.md"
        c6.write_text(CASE6_GOOD, encoding="utf-8")
        r6 = run(str(c6))
        print(f"CASE 6 (markdown-link-target, gate mode): exit={r6.returncode}")
        print(r6.stdout.rstrip())
        if r6.returncode != 1:
            failures.append("CASE 6: expected exit 1 (the plain-prose occurrence is unshielded)")
        hit_lines = [ln for ln in r6.stdout.splitlines() if "TERM 'chocofarm'" in ln]
        if len(hit_lines) != 1:
            failures.append(
                f"CASE 6: expected exactly 1 unshielded 'chocofarm' hit (the link occurrence "
                f"shielded, the prose occurrence flagged); got {len(hit_lines)}")

        # CASE 7 -- Shield 5, inline waiver comment: one-line reach only.
        c7 = Path(td) / "0005-fixture.md"
        c7.write_text(CASE7_GOOD, encoding="utf-8")
        r7 = run(str(c7))
        print(f"CASE 7 (inline waiver comment, gate mode): exit={r7.returncode}")
        print(r7.stdout.rstrip())
        if r7.returncode != 1:
            failures.append("CASE 7: expected exit 1 (the second mention is past the waiver's reach)")
        hit_lines7 = [ln for ln in r7.stdout.splitlines() if "TERM 'chocofarm'" in ln]
        if len(hit_lines7) != 1:
            failures.append(
                f"CASE 7: expected exactly 1 unshielded 'chocofarm' hit (the waived line "
                f"shielded, the later line flagged); got {len(hit_lines7)}")

    # CASE 4 — negative control against the REAL corpus, informational only.
    real = run()
    print(f"CASE 4 (negative control -- real law/adr/*.md, report mode): exit={real.returncode}")
    print(real.stdout.splitlines()[0] if real.stdout else "(no output)")
    print("  (Expected 0 post-refactor + post-shield-gap-fix; a nonzero result here after "
          "2026-07-14 is a live regression, not an expected pre-refactor state.)")

    if failures:
        print("adr-portability-terms red-specimen: FAILED —", "; ".join(failures))
        return 1
    print("adr-portability-terms red-specimen: all synthetic cases behaved as designed -- "
          "red on the unshielded term, green on the fully-shielded fixture, report mode "
          "reflecting true findings, and the three 2026-07-14 shield-gap fixes (cases 5-7) "
          "each proven both green-inside and red-outside their declared scope; the real "
          "corpus negative control is printed above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
