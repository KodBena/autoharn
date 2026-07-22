#!/usr/bin/env python3
"""ordering_differential -- the ordering-violations marriage's load-bearing gate: the ASP
verdict program (engine/lp/ordering_violations.lp + engine/ordering_obligations.lp, producer
two) differentialed BIT-IDENTICALLY against the SQL floor (engine/ordering_floor.py, producer
one) over one target's real ledger rows (design/ORCH-SPEC-RESOURCE-REGISTRY.md §6's marriage
discipline, imported from engine/ledger_differential.py's conventions wholesale, never
re-derived): the closed verdict vocabulary (AGREE / DIVERGE_BY_DESIGN / DIVERGE_DEFECT /
QUARANTINED), the DerivationRecord shape + retention idiom, the override-one-producer
negative-control seam, and the RED = non-zero-exit set.

SCOPE: compares ONLY engine/lp/ordering_violations.lp's OWN #show set -- never a raw EDB fact
(work_opened/work_closed/work_depends/constraint_precedes are shared INPUT, not independently
DERIVED, so comparing them would be tautological rather than a test of the two derivations).
`_OWN_PREDICATE_PREFIXES` is the closed, named filter (mirrors engine/preamble_differential.py's
own `_OWN_PREDICATE_PREFIXES`).

NO DENOMINATION NORMALIZATION NEEDED (unlike engine/preamble_differential.py's own anchor-ms
rewrite): this checker carries no timestamp at all -- every Anchor is a RowId/Slug, pure
id-order -- so the ASP and SQL producers' atoms compare directly, no relative-to-absolute
rewrite step.

Read-only on every ledger. Lazy imports banned (top-of-file only)."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

from clingo_run import run_clingo
from ledger_differential import (
    AGREE,
    DIVERGE_DEFECT,
    QUARANTINED,
    RED,
    VERDICTS,
    DerivationRecord,
    ProducerRun,
    _clingo_version,
    _now,
    _pg_version,
    _sha,
)
from ledger_edb import resolve as resolve_ledger
from ordering_edb import export
from ordering_floor import floor_atoms

HERE = Path(__file__).resolve().parent
ORDERING_LP = HERE / "lp" / "ordering_violations.lp"
OBLIGATIONS_LP = HERE / "ordering_obligations.lp"
RETENTION = HERE / "docs" / "ledger-marriage" / "derivations" / "ordering-violations"

_PROGRAM_FILES = [ORDERING_LP, OBLIGATIONS_LP]

# engine/lp/ordering_violations.lp's OWN #show set -- the closed filter (this module's own
# docstring SCOPE section). A future #show added there needs a matching entry here AND a
# matching SQL emission in engine/ordering_floor.py -- named as the one place all three must
# move together (the identical rule engine/preamble_differential.py's own docstring states).
_OWN_PREDICATE_PREFIXES = (
    "cbd_trigger(", "close_before_dependency_discharged(", "close_before_dependency_violated(",
    "cp_trigger(", "conditional_precedence_discharged(", "conditional_precedence_violated(",
    "ordering_edge(", "ordering_edge_star(", "dependency_cycle(",
    "ordering_undecidable_any(", "ordering_forced_undecidable(", "ordering_verdict(",
)


def _filter_own(atoms: set[str]) -> set[str]:
    return {a for a in atoms if a.startswith(_OWN_PREDICATE_PREFIXES)}


def run_asp(target_name: str) -> ProducerRun:
    """The ASP producer, run over `target_name`'s real EDB (engine/ordering_edb.py)."""
    try:
        exp = export(target_name)
    except Exception as e:  # noqa: BLE001 -- a genuine tool/DB error, not a finding
        return ProducerRun("asp:clingo", quarantine=f"EDB export failed: {type(e).__name__}: {e}")
    try:
        edb_text = exp.edb_text()
        raw_atoms = {a for a in run_clingo(_PROGRAM_FILES, edb_text) if "(" in a}
    except Exception as e:  # noqa: BLE001
        return ProducerRun("asp:clingo", quarantine=f"clingo/EDB failed: {type(e).__name__}: {e}")
    atoms = _filter_own(raw_atoms)
    program_text = "".join(p.read_text(encoding="utf-8") for p in _PROGRAM_FILES)
    rec = DerivationRecord(
        engine="clingo", version=_clingo_version(), config=[p.name for p in _PROGRAM_FILES],
        input_basis="edb-text (ordering EDB export, serialized; engine/ordering_edb.py)",
        input_hash=_sha(edb_text), program_hash=_sha(program_text),
        output_hash=_sha("\n".join(sorted(atoms))), target=target_name, ts=_now())
    return ProducerRun("asp:clingo", atoms=atoms, record=rec)


def run_sql(target_name: str) -> ProducerRun:
    """The SQL floor producer, run over `target_name`'s real ledger rows (engine/ordering_floor.py)."""
    try:
        atoms, snapshot = floor_atoms(target_name)
    except Exception as e:  # noqa: BLE001
        return ProducerRun("sql:floor", quarantine=f"SQL floor failed: {type(e).__name__}: {e}")
    db = resolve_ledger(target_name).db
    rec = DerivationRecord(
        engine="postgres", version=_pg_version(db), config=["ordering_floor.py::floor_atoms"],
        input_basis=f"live-db ledger rows ({db}.{resolve_ledger(target_name).schema}.ledger "
                    f"+ .ledger_current)",
        input_hash=_sha(snapshot),
        program_hash=_sha((HERE / "ordering_floor.py").read_text(encoding="utf-8")),
        output_hash=_sha("\n".join(sorted(atoms))), target=target_name, ts=_now())
    return ProducerRun("sql:floor", atoms=atoms, record=rec)


class DifferentialResult:
    def __init__(self, target: str, asp: ProducerRun, sql: ProducerRun):
        self.target = target
        self.asp = asp
        self.sql = sql
        self.only_asp: set[str] = set()
        self.only_sql: set[str] = set()

    def verdict(self) -> str:
        if self.asp.quarantine or self.sql.quarantine:
            return QUARANTINED
        if self.asp.record is None or self.sql.record is None:
            return QUARANTINED
        if not self.only_asp and not self.only_sql:
            return AGREE
        return DIVERGE_DEFECT  # no defeater-lens declared for this domain; any Δ is a defect


def run_differential(target_name: str, *, asp_atoms_override: set[str] | None = None,
                     sql_atoms_override: set[str] | None = None) -> DifferentialResult:
    """Differential one target. `asp_atoms_override`/`sql_atoms_override` are the negative-control
    seams (mirrors engine/preamble_differential.py's own): a fixture may inject a deliberately
    WRONG atom set for exactly one producer's OUTPUT, proving the differential catches a
    manufactured divergence, WITHOUT ever touching either producer's real code."""
    asp = run_asp(target_name)
    if asp_atoms_override is not None and asp.quarantine is None:
        asp.atoms = asp_atoms_override
    sql = run_sql(target_name)
    if sql_atoms_override is not None and sql.quarantine is None:
        sql.atoms = sql_atoms_override
    res = DifferentialResult(target_name, asp, sql)
    if asp.quarantine is None and sql.quarantine is None:
        res.only_asp = asp.atoms - sql.atoms
        res.only_sql = sql.atoms - asp.atoms
    return res


def _run_unique_dir(target: str) -> Path:
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    h = hashlib.sha256(f"{target}{ts}".encode("utf-8")).hexdigest()[:12]
    return RETENTION / target / f"{ts}_{h}"


def retain(res: DifferentialResult) -> Path:
    d = _run_unique_dir(res.target)
    d.mkdir(parents=True, exist_ok=False)
    (d / "asp_atoms.txt").write_text("\n".join(sorted(res.asp.atoms)) + "\n", encoding="utf-8")
    (d / "sql_atoms.txt").write_text("\n".join(sorted(res.sql.atoms)) + "\n", encoding="utf-8")
    records = {"target": res.target, "verdict": res.verdict(),
               "only_asp": sorted(res.only_asp), "only_sql": sorted(res.only_sql),
               "asp_record": asdict(res.asp.record) if res.asp.record else None,
               "sql_record": asdict(res.sql.record) if res.sql.record else None,
               "asp_quarantine": res.asp.quarantine, "sql_quarantine": res.sql.quarantine}
    (d / "derivation.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return d


def print_result(res: DifferentialResult) -> None:
    v = res.verdict()
    mark = "OK " if v == AGREE else "!! "
    print(f"  [{mark}] {res.target:12} {v:18} "
          f"asp={len(res.asp.atoms)} sql={len(res.sql.atoms)} atoms; "
          f"Δasp={sorted(res.only_asp)} Δsql={sorted(res.only_sql)}")
    if res.asp.quarantine:
        print(f"          asp QUARANTINED: {res.asp.quarantine}")
    if res.sql.quarantine:
        print(f"          sql QUARANTINED: {res.sql.quarantine}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="*", default=["toy"])
    ap.add_argument("--retain", action="store_true", help="bank proof artifacts under "
                    "engine/docs/ledger-marriage/derivations/ordering-violations/")
    ap.add_argument("--drop-record", action="store_true",
                    help="negative control: drop the ASP derivation record and show the "
                         "consumer refuses (a verdict without its witness is NO RESULT)")
    args = ap.parse_args(argv)

    print("# ordering-violations marriage differential -- ASP (engine/lp/ordering_violations.lp) "
          "vs SQL floor (engine/ordering_floor.py)")
    print(f"#   closed verdict vocabulary: {sorted(VERDICTS)}; RED = {sorted(RED)}\n")

    red = 0
    for name in args.targets:
        res = run_differential(name)
        if args.drop_record and res.asp.record is not None:
            res.asp.record = None
        print_result(res)
        if args.retain:
            d = retain(res)
            print(f"\n# retained: {d}")
        if res.verdict() in RED:
            red = 1
    print(f"\n# {'DIFFERENTIAL RED' if red else 'DIFFERENTIAL GREEN'} -- "
          f"{'a target diverged/quarantined (NO RESULT)' if red else 'every target bit-identical to the SQL floor'}")
    return red


if __name__ == "__main__":
    raise SystemExit(main())
