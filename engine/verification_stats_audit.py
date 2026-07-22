#!/usr/bin/env python3
"""verification_stats_audit -- the OBSERVER-GRADE report half of work item
`verification-stats-asp-harvester`. Mirrors engine/review_gap_audit.py's own build_report()/
print_report() shape (that module's own docstring names the pattern this one clones).

NOT WIRED INTO `./audit` (a named scope decision, not an oversight): engine/review_gap_audit.py's
`--review-gap` flag is wired into engine/contemp_audit.py because that verb already resolves a
`target_name` for the base audit and review-gap rides along. This harvester answers a DIFFERENT
question (a downstream orchestrator's own verdict distributions), for a DIFFERENT consumer (`ent`,
not this repo's own `./audit` verb) -- this repo's own ledger carries no `kind=verification` rows
(this work item's own instruction), so there is no live target here for `./audit` to report against
today. Wiring a flag onto `./audit` for a capability no in-repo target can yet exercise would be
exactly the "declares a produced family it cannot emit" shape ADR-0000/F49 already reject.
`build_report()`/`print_report()` are exported for direct import (by `ent`'s own driver, or by a
future in-repo target once one carries `kind=verification` rows) and via the standalone CLI below.

Read-only. Lazy imports banned (top-of-file only)."""
from __future__ import annotations

import sys

from clingo_run import run_clingo
from verification_stats_edb import VERIFICATION_STATS_LP, export


def build_report(target_name: str) -> dict:
    """The whole verification-stats report for one target. Never raises for an honest capability
    shortfall (the report's own `capable`/`exclusions` fields carry it); raises only for a genuine
    clingo/tool error, matching engine/review_gap_audit.py's own build_report() posture."""
    exp = export(target_name)
    report: dict = {
        "target": target_name,
        "capable": exp.full_capable(),
        "exclusions": [{"family": c.family, "reason": c.reason} for c in exp.exclusions()],
        "counts": exp.counts,
        "count_workflow_verdict": [],
        "count_role_verdict": [],
        "count_round_verdict": [],
        "count_verdict": [],
        "count_unparseable": 0,
        "unparseable_rows": [],
    }
    if not exp.full_capable():
        return report

    edb_text = exp.edb_text()
    atoms = run_clingo([VERIFICATION_STATS_LP], edb_text)
    for a in atoms:
        if a.startswith("count_workflow_verdict(") and a.endswith(")"):
            wf, v, n = _split3(a, "count_workflow_verdict(")
            report["count_workflow_verdict"].append((wf, v, int(n)))
        elif a.startswith("count_role_verdict(") and a.endswith(")"):
            role, v, n = _split3(a, "count_role_verdict(")
            report["count_role_verdict"].append((role, v, int(n)))
        elif a.startswith("count_round_verdict(") and a.endswith(")"):
            rnd, v, n = _split3(a, "count_round_verdict(")
            report["count_round_verdict"].append((rnd, v, int(n)))
        elif a.startswith("count_verdict(") and a.endswith(")"):
            v, n = a[len("count_verdict("):-1].rsplit(",", 1)
            report["count_verdict"].append((v, int(n)))
        elif a.startswith("count_unparseable(") and a.endswith(")"):
            report["count_unparseable"] = int(a[len("count_unparseable("):-1])
        elif a.startswith("unparseable_verification(") and a.endswith(")"):
            report["unparseable_rows"].append(int(a[len("unparseable_verification("):-1]))
    report["count_workflow_verdict"].sort()
    report["count_role_verdict"].sort()
    report["count_round_verdict"].sort()
    report["count_verdict"].sort()
    report["unparseable_rows"].sort()
    return report


def _split3(atom: str, prefix: str) -> tuple[str, str, str]:
    """Split a 3-arity atom's argument list on its LAST two commas (the first argument may itself
    contain commas only if it were a quoted string with an escaped comma inside -- clingo's JSON
    #show output never re-quotes at this layer, so a plain rsplit twice from the right is exact for
    every argument shape this program actually emits: bare atoms and unquoted small integers)."""
    body = atom[len(prefix):-1]
    a, rest = body.split(",", 1)
    b, n = rest.rsplit(",", 1)
    return a, b, n


def print_report(r: dict) -> None:
    print(f"VERIFICATION-STATS AUDIT (work item `verification-stats-asp-harvester`; "
          f"target={r['target']!r}):")
    if not r["capable"]:
        print("  N/A: this target lacks a required capability for the verification-stats "
              "harvester -- never a guessed verdict:")
        for e in r["exclusions"]:
            print(f"    EXCLUDED {e['family']}: {e['reason']}")
        return
    print(f"  counts: {r['counts']}")
    if not r["counts"].get("verification_row"):
        print("  no kind=verification rows on this target -- nothing to derive (VACUOUS, not "
              "evidence of conduct).")
        return
    print(f"  OVERALL per-verdict totals: {r['count_verdict']}")
    print(f"  per-workflow (workflow, verdict, count): {r['count_workflow_verdict']}")
    print(f"  per-role (role, verdict, count): {r['count_role_verdict']}")
    print(f"  per-round (round, verdict, count): {r['count_round_verdict']}")
    if r["unparseable_rows"]:
        print(f"  UNPARSEABLE ({r['count_unparseable']} row(s), REFUSED LOUDLY, never guessed at "
              f"-- see engine/verification_evidence.py's own closed grammar): "
              f"{r['unparseable_rows']}")
    else:
        print("  UNPARSEABLE: none -- every kind=verification row on this target parsed under "
              "the verdict=/role=/workflow=/round=/task= convention.")
    print("  NOTE: these are COUNTS, not a judgment -- this harvester never opines on whether an "
          "approve/revise/reject ratio is good or bad (see engine/lp/verification_stats.lp's own "
          "header).")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("usage: verification_stats_audit.py <target-name>", file=sys.stderr)
        return 2
    r = build_report(args[0])
    print_report(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
