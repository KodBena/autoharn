#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T02:22:11Z
#   last-change: 2026-07-12T02:22:43Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""preamble_audit -- the OBSERVER-GRADE report half of Part 3 (design/
ORCH-CONTEMPORANEITY-PART3-SPEC.md §8: "a `--preamble` mode of the existing `./audit` verb ...
exit 0/1 by family verdict, typed refusal on capability absence, the
[engine/contemp_audit.py] harness idiom"). Runs engine/lp/preamble_ordering.lp (+
engine/lp/contemporaneity.lp + engine/contemp_thresholds.lp + engine/preamble_obligations.lp +
engine/lp/work_items.lp, the load order that program's own header names) over the SAME EDB
engine/contemp_edb.py already exports for Part 2 -- Part 3 adds no separate EDB, per spec §4's
binding one-anchor rule -- and prints the twelve family verdicts, never silence (E8's
preamble_obligation/2 grounds every family even on an empty world).

WIRED INTO `./audit --preamble` via a flag on engine/contemp_audit.py's own argparse (that
module's main() imports `build_report`/`print_report` from here and calls them when `--preamble`
is passed) -- bootstrap/templates/audit.tmpl's shell wrapper passes an unrecognized flag straight
through to contemp_audit.py already, so no shell-script change was needed for this flag to reach
here (unlike `--differential`, which the shell wrapper strips to invoke a separate subprocess --
`--preamble` is cheap enough, and shares enough of `run_audit`'s own EDB build, to live in-process
instead).

EXIT-CODE COMPOSITION RULE (stated explicitly, per this build's own commission): `--preamble`
NEVER overrides a non-zero base `./audit` exit (1 BACKFILL_SUSPECT, 2 tool error, 3 N/A capability
refusal) -- the FIRST problem found stays the reported one, mirroring `--differential`'s own
already-shipped rule ("A non-zero contemp_audit exit (1/2/3) is NEVER overwritten by the
differential's own code"). When the base exit IS 0 (clean or vacuously clean), `--preamble`
may additionally raise it to 5 -- ONE NEW CODE, reachable ONLY through this flag, exactly as 4 is
reachable only through `--differential` -- iff at least one family verdict is `violated`. A family
verdict of `undecidable` or `vacuous` does NOT raise the exit (this is an OBSERVER, per spec §8:
"it gates nothing"; UNDECIDABLE is an honest non-finding, not evidence of a defect, and is
expected to be the COMMON case on this project's own pre-E1-E9 historical corpus). The report is
printed regardless of the base exit code, same as `--differential`'s own "[OK]/[!!] line is still
printed either way" rule -- an operator always sees BOTH axes even when only one moves the exit.

Read-only. Lazy imports banned (top-of-file only)."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from clingo_run import run_clingo
from contemp_edb import ContempEdbExport

HERE = Path(__file__).resolve().parent
PREAMBLE_LP = HERE / "lp" / "preamble_ordering.lp"
CONTEMP_LP = HERE / "lp" / "contemporaneity.lp"
WORK_ITEMS_LP = HERE / "lp" / "work_items.lp"
THRESHOLDS_LP = HERE / "contemp_thresholds.lp"
OBLIGATIONS_LP = HERE / "preamble_obligations.lp"
PROGRAM_FILES = [PREAMBLE_LP, CONTEMP_LP, THRESHOLDS_LP, OBLIGATIONS_LP, WORK_ITEMS_LP]

FAMILIES = tuple(f"f{n}" for n in range(1, 13))
# The preamble point each family formalizes (engine/preamble_obligations.lp's own E8 catalogue,
# mirrored here as DISPLAY TEXT ONLY -- never a second closed-vocabulary source of truth; the
# EDB's own preamble_obligation/2 facts are what actually ground the twelve family verdicts).
_POINTS = {"f1": 10, "f2": 10, "f3": 10, "f4": 1, "f5": 1, "f6": 1, "f7": 2, "f8": 3,
          "f9": 7, "f10": 8, "f11": 5, "f12": 9}


def build_report(exp: ContempEdbExport) -> dict:
    """The whole preamble-ordering report for one already-exported EDB (the SAME
    ContempEdbExport engine/contemp_audit.py's own run_audit() built for Part 2 -- never a
    second export, per spec §4's one-anchor rule). Never raises for an honest capability
    shortfall (every family gets SOME verdict, by E8's own construction); raises only for a
    genuine clingo/tool error, matching engine/contemp_audit.py's own run_audit() posture."""
    edb_text = exp.edb_text()
    atoms = run_clingo(PROGRAM_FILES, edb_text)
    parsed: dict[str, list[tuple]] = defaultdict(list)
    for a in atoms:
        if "(" not in a or not a.endswith(")"):
            continue
        name, rest = a.split("(", 1)
        rest = rest[:-1]
        args, cur, depth, in_str = [], "", 0, False
        for ch in rest:
            if ch == '"' and (not cur or cur[-1] != "\\"):
                in_str = not in_str
                cur += ch
            elif ch == "," and depth == 0 and not in_str:
                args.append(cur); cur = ""
            else:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                cur += ch
        if cur:
            args.append(cur)
        parsed[name].append(tuple(x.strip().strip('"') for x in args))

    verdict_by_family = {a[0]: a[1] for a in parsed.get("preamble_verdict", [])}
    reasons_by_family: dict[str, list[str]] = defaultdict(list)
    for fam, anchor, reason in parsed.get("ob_undecidable", []):
        reasons_by_family[fam].append(reason)
    for fam, reason in parsed.get("ob_family_forced_undecidable", []):
        reasons_by_family[fam].append(reason)

    families = []
    missing = []
    for f in FAMILIES:
        v = verdict_by_family.get(f)
        if v is None:
            missing.append(f)  # a missing family verdict is itself a loud defect (spec §5) --
                                # never silently treated as clean; reported, not raised, so the
                                # OTHER eleven families' verdicts still reach the operator.
            continue
        families.append({
            "family": f, "point": _POINTS[f], "verdict": v,
            "reasons": sorted(set(reasons_by_family.get(f, []))),
            "n_discharged": len([x for x in parsed.get("ob_discharged", []) if x[0] == f]),
            "n_violated": len([x for x in parsed.get("ob_violated", []) if x[0] == f]),
        })

    return {
        "families": families,
        "missing_families": missing,
        "any_violated": any(f["verdict"] == "violated" for f in families),
        "any_undecidable": any(f["verdict"] == "undecidable" for f in families),
        "program_files": [p.name for p in PROGRAM_FILES],
    }


def print_report(r: dict) -> None:
    print("PREAMBLE-ORDERING REPORT (design/ORCH-CONTEMPORANEITY-PART3-SPEC.md, F1-F12; observer-"
         "grade -- gates nothing):")
    for f in r["families"]:
        reasons = f", reasons={f['reasons']}" if f["reasons"] else ""
        counts = f" (discharged={f['n_discharged']}, violated={f['n_violated']})" if f["verdict"] in (
            "discharged", "violated") else ""
        print(f"  {f['family'].upper()} (preamble pt {f['point']}): {f['verdict'].upper()}{counts}{reasons}")
    if r["missing_families"]:
        print(f"  [!!] MISSING FAMILY VERDICT(S) (loud defect, never silent): "
             f"{[m.upper() for m in r['missing_families']]}")


def preamble_exit_addendum(r: dict) -> int | None:
    """The exit-code composition this module's own docstring names: None if `--preamble` should
    not move the exit code at all (no violation found, or missing families -- a defect the
    caller should already be surfacing some other way); 5 iff at least one family is VIOLATED."""
    if r["missing_families"]:
        return 5  # a missing family verdict is a defect too -- never silently 0.
    return 5 if r["any_violated"] else None


# NO standalone CLI entry point here, deliberately (ADR-0012 P1 / lazy-imports-banned corollary):
# a `main()` needing `--root`/`--target` resolution would need engine/contemp_audit.py's own
# `_resolve_target_name` + `contemp_edb.export`, and contemp_audit.py already imports THIS module
# (to call build_report/print_report when `--preamble` is passed) -- importing back the other way
# at module top would be a circular import, and importing it lazily inside a function body is
# exactly what the lazy-imports ban forecloses. This module is reached the one way its own
# docstring names: `./audit --preamble` -> engine/contemp_audit.py's own main().
