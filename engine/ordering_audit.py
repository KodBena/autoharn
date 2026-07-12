#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T07:55:10Z
#   last-change: 2026-07-12T07:55:10Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""ordering_audit -- the OBSERVER-GRADE report half of design/ORCH-SPEC-RESOURCE-REGISTRY.md §5
stage 2 ("a report surface ... mirror the existing choice architecture" -- this file mirrors
engine/preamble_audit.py's own `--preamble` addendum shape exactly, as `./audit --ordering`).
Runs engine/lp/ordering_violations.lp + engine/ordering_obligations.lp over
engine/ordering_edb.py's OWN ledger-only EDB (a SEPARATE export from engine/contemp_edb.py's --
see engine/ordering_edb.py's own docstring for why) and prints the three family verdicts, never
silence (engine/ordering_obligations.lp's ordering_family/1 grounds every family even on an
empty world).

WIRED INTO `./audit --ordering` via a flag on engine/contemp_audit.py's own argparse, exactly
the way `--preamble` is wired (that module's main() imports build_report/print_report from here
and calls them when `--ordering` is passed) -- bootstrap/templates/audit.tmpl's shell wrapper
already passes an unrecognized flag straight through, so no shell-script change is needed.

EXIT-CODE COMPOSITION RULE (mirrors engine/preamble_audit.py's own, verbatim in spirit):
`--ordering` NEVER overrides a non-zero base `./audit` exit (1 BACKFILL_SUSPECT, 2 tool error, 3
N/A capability refusal, or 5 from `--preamble` if that flag is ALSO passed and finds a
violation) -- the first problem found stays the reported one. When the base exit IS 0,
`--ordering` may additionally raise it to 6 -- ONE NEW CODE, reachable ONLY through this flag
(5 is already `--preamble`'s own) -- iff at least one family verdict is VIOLATED. UNDECIDABLE or
VACUOUS never move the exit (an observer per §5: "visible-only ... no write-time blocking").

Read-only. Lazy imports banned (top-of-file only)."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from clingo_run import run_clingo
from ordering_edb import export

HERE = Path(__file__).resolve().parent
ORDERING_LP = HERE / "lp" / "ordering_violations.lp"
OBLIGATIONS_LP = HERE / "ordering_obligations.lp"
PROGRAM_FILES = [ORDERING_LP, OBLIGATIONS_LP]

FAMILIES = ("close_before_dependency", "conditional_precedence", "dependency_cycle")
# Per-family (discharged-count-predicate, violated-count-predicate) -- for dependency_cycle the
# "discharged" side has no natural per-instance count (it is a boolean "checked, none found"), so
# ordering_edge/2 (the edge count) stands in as display context, never as a discharge CLAIM.
_COUNT_PREDS = {
    "close_before_dependency": ("close_before_dependency_discharged", "close_before_dependency_violated"),
    "conditional_precedence": ("conditional_precedence_discharged", "conditional_precedence_violated"),
    "dependency_cycle": ("ordering_edge", "dependency_cycle"),
}


def _parse_atoms(atoms: list[str]) -> dict[str, list[tuple]]:
    """A tiny, framework-free parser (no clingo Python binding available in this venv, per
    engine/clingo_run.py's own docstring) -- a THIRD independent copy of the same ~20-line
    parser engine/contemp_audit.py and engine/preamble_audit.py each already keep their own
    (matching that precedent of NOT centralizing it)."""
    out: dict[str, list[tuple]] = defaultdict(list)
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
                args.append(cur)
                cur = ""
            else:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                cur += ch
        if cur:
            args.append(cur)
        out[name].append(tuple(x.strip().strip('"') for x in args))
    return out


def build_report(target_name: str) -> dict:
    """The whole ordering-violations report for one target. Never raises for an honest
    capability shortfall (every family gets SOME verdict, by ordering_family/1's own
    construction); raises only for a genuine clingo/DB/tool error."""
    exp = export(target_name)
    edb_text = exp.edb_text()
    atoms = run_clingo(PROGRAM_FILES, edb_text)
    parsed = _parse_atoms(atoms)

    verdict_by_family = {a[0]: a[1] for a in parsed.get("ordering_verdict", [])}
    reasons_by_family: dict[str, list[str]] = defaultdict(list)
    for fam, reason in parsed.get("ordering_forced_undecidable", []):
        reasons_by_family[fam].append(reason)
    if parsed.get("ordering_undecidable_any", []):
        reasons_by_family["conditional_precedence"].append("constraint_unparsed")

    families = []
    missing = []
    for f in FAMILIES:
        v = verdict_by_family.get(f)
        if v is None:
            missing.append(f)  # a missing family verdict is itself a loud defect -- never
                                # silently treated as clean; reported, not raised, so the OTHER
                                # families' verdicts still reach the operator.
            continue
        disc_pred, viol_pred = _COUNT_PREDS[f]
        families.append({
            "family": f, "verdict": v, "reasons": sorted(set(reasons_by_family.get(f, []))),
            "n_discharged": len(parsed.get(disc_pred, [])),
            "n_violated": len(parsed.get(viol_pred, [])),
        })

    return {
        "target": target_name,
        "families": families,
        "missing_families": missing,
        "any_violated": any(f["verdict"] == "violated" for f in families),
        "capable_work_items": exp.capable_work_items,
        "counts": exp.counts,
        "program_files": [p.name for p in PROGRAM_FILES],
    }


def print_report(r: dict) -> None:
    print("ORDERING-VIOLATIONS REPORT (design/ORCH-SPEC-RESOURCE-REGISTRY.md §5 stage 2; "
         "observer-grade -- gates nothing):")
    print(f"  target={r['target']!r} capable(work_items)={r['capable_work_items']} counts={r['counts']}")
    for f in r["families"]:
        reasons = f", reasons={f['reasons']}" if f["reasons"] else ""
        if f["family"] == "dependency_cycle":
            extra = f" (edges={f['n_discharged']}, cycle_members={f['n_violated']})"
        else:
            extra = (f" (discharged={f['n_discharged']}, violated={f['n_violated']})"
                    if f["verdict"] in ("discharged", "violated") else "")
        print(f"  {f['family'].upper()}: {f['verdict'].upper()}{extra}{reasons}")
    if r["missing_families"]:
        print(f"  [!!] MISSING FAMILY VERDICT(S) (loud defect, never silent): "
             f"{[m.upper() for m in r['missing_families']]}")


def ordering_exit_addendum(r: dict) -> int | None:
    """The exit-code composition this module's own docstring names: None if `--ordering` should
    not move the exit code at all; 6 iff at least one family is VIOLATED, or a family verdict is
    missing (a defect too -- never silently 0)."""
    if r["missing_families"]:
        return 6
    return 6 if r["any_violated"] else None


# NO standalone CLI entry point here, deliberately (mirrors engine/preamble_audit.py's own
# identical rationale): this module is reached the one way its own docstring names --
# `./audit --ordering` -> engine/contemp_audit.py's own main().
