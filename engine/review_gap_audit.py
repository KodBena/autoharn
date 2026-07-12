#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T07:49:59Z
#   last-change: 2026-07-12T07:50:24Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""review_gap_audit -- the OBSERVER-GRADE report half of the content-free-review-discharge audit
(tracker item `content-free-review-audit`). Mirrors engine/preamble_audit.py's own structure
EXACTLY (build_report/print_report + an exit-code-addendum function, wired into
engine/contemp_audit.py's own `--review-gap` flag the same way that module's `--preamble` flag
already works) -- see that module's own docstring for the pattern this one follows.

WHY A SEPARATE EDB, NOT contemp_edb.py's (a deliberate divergence from --preamble's own
one-anchor-rule precedent, named honestly): Part 3's `--preamble` reuses engine/contemp_edb.py's
STAGED EDB because that domain reasons over event TIMESTAMPS, and design/
ORCH-CONTEMPORANEITY-PART3-SPEC.md §4 binds every timestamp-bearing family to ONE shared anchor
(two exports on two different anchors compared in one program is the exact silent-wraparound
hazard contemp_edb.py's own docstring documents). This audit carries NO timestamp at all -- it is
a purely relational judgment over ledger rows (id-ordered supersession, actor identity, verdict,
statement length) -- so there is no anchor to share and no reason to grow contemp_edb.py's already
large export() with four more columns a temporal domain has no use for. engine/review_gap_edb.py
is this audit's own small, honest EDB (see that module's docstring in full for the specimen this
whole audit family answers to: run12 ledger row 20).

WIRED INTO `./audit --review-gap` via a flag on engine/contemp_audit.py's own argparse (mirrors
`--preamble` exactly): that module's main() imports `build_report`/`print_report` from here and
calls them when `--review-gap` is passed, over the SAME `target_name` that module's own
`_resolve_target_name(root, args.target)` already computed for the base audit -- this domain has
no notion of a "world root" at all (only a ledger_edb.resolve()-able target name), but reusing
the verb's own already-resolved target keeps ONE resolution point (ADR-0012 P1) rather than a
second `--target`-only flag pair.

EXIT-CODE COMPOSITION RULE (mirrors engine/preamble_audit.py's own, verbatim in spirit):
`--review-gap` NEVER overrides a non-zero base `./audit` exit, and (per contemp_audit.py's own
composition, extended there) never overrides an EARLIER flag's own addendum either -- the FIRST
problem found stays the reported one. When nothing else has already raised the exit, `--review-gap`
may additionally raise it to 6 -- ONE NEW CODE, reachable ONLY through this flag (5 is
`--preamble`'s own, 4 is `--differential`'s own) -- iff at least one review row is FLAGGED. A
target that lacks a required capability (pre-s15 schema) is reported as a NAMED, non-fatal
exclusion -- see build_report()'s own `capable` field -- and does NOT raise the exit on its own
(an honestly-incapable target is not evidence of a defect, the same posture engine/contemp_audit.py
already takes for its own capability-gated refusal at exit 3, except THIS check's absence of
capability is reported inline rather than as the whole verb's own exit).

Read-only. Lazy imports banned (top-of-file only)."""
from __future__ import annotations

from clingo_run import run_clingo
from review_gap_edb import REVIEW_GAP_LP, export


def build_report(target_name: str) -> dict:
    """The whole content-free-review-discharge report for one target. Never raises for an honest
    capability shortfall (the report's own `capable`/`exclusions` fields carry it); raises only
    for a genuine clingo/tool error, matching engine/preamble_audit.py's own build_report()
    posture."""
    exp = export(target_name)
    report: dict = {
        "target": target_name,
        "capable": exp.full_capable(),
        "exclusions": [{"family": c.family, "reason": c.reason} for c in exp.exclusions()],
        "counts": exp.counts,
        "discharges": [],
        "flagged": [],
    }
    if not exp.full_capable():
        return report

    edb_text = exp.edb_text()
    atoms = run_clingo([REVIEW_GAP_LP], edb_text)
    discharges: list[tuple[int, int]] = []
    flagged: list[int] = []
    for a in atoms:
        if a.startswith("discharges(") and a.endswith(")"):
            rid, lid = a[len("discharges("):-1].split(",")
            discharges.append((int(rid), int(lid)))
        elif a.startswith("flagged(") and a.endswith(")"):
            rid = a[len("flagged("):-1]
            flagged.append(int(rid))
    report["discharges"] = sorted(discharges)
    report["flagged"] = sorted(flagged)
    return report


def print_report(r: dict) -> None:
    print(f"CONTENT-FREE-REVIEW-DISCHARGE AUDIT (tracker item `content-free-review-audit`; "
          f"target={r['target']!r}):")
    if not r["capable"]:
        print("  N/A: this target lacks a required capability for the review_gap discharge "
              "check -- never a guessed verdict:")
        for e in r["exclusions"]:
            print(f"    EXCLUDED {e['family']}: {e['reason']}")
        return
    print(f"  counts: {r['counts']}")
    if not r["discharges"]:
        print("  no obliged row has ever been discharged by a review on this target -- nothing "
              "to check (VACUOUS, not evidence of conduct).")
        return
    print(f"  DISCHARGING REVIEWS (review_id, target_row_id): {r['discharges']}")
    if r["flagged"]:
        print(f"  FLAGGED (content-free statement discharging an obligation; suspicious, NOT "
              f"proven dishonest -- see engine/review_gap_edb.py's own 'THE HONEST LIMIT'): "
              f"{r['flagged']}")
    else:
        print("  FLAGGED: none -- every discharging review's statement clears the "
              "content-free-length threshold (engine/review_gap_thresholds."
              "CONTENT_FREE_STATEMENT_THRESHOLD).")


def review_gap_exit_addendum(r: dict) -> int | None:
    """The exit-code composition this module's own docstring names: None if `--review-gap`
    should not move the exit code at all (nothing flagged, or the target is incapable -- an
    honest N/A, not a defect); 6 iff at least one review row is FLAGGED."""
    if not r["capable"]:
        return None
    return 6 if r["flagged"] else None


# NO standalone CLI entry point here, deliberately -- mirrors engine/preamble_audit.py's own
# closing comment (ADR-0012 P1 / lazy-imports-banned corollary): this module is reached the one
# way its own docstring names, `./audit --review-gap` -> engine/contemp_audit.py's own main().
