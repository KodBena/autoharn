#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T07:49:29Z
#   last-change: 2026-07-12T07:49:29Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""review_gap_differential -- the content-free-review-discharge audit's marriage gate: the ASP
program (engine/lp/review_gap_audit.lp, producer two) differentialed BIT-IDENTICALLY against the
SQL floor (engine/review_gap_floor.py, producer one) over one target's real ledger. MATCHES
engine/ledger_differential.py's / engine/contemp_differential.py's / engine/preamble_differential.py's
OWN CONVENTIONS EXACTLY (imported, not re-derived): the closed verdict vocabulary (AGREE /
DIVERGE_BY_DESIGN / DIVERGE_DEFECT / QUARANTINED), the DerivationRecord shape, the
override-one-producer negative-control seam, and the RED = non-zero-exit set.

NO ANCHOR / NO DENOMINATION NORMALIZATION NEEDED (unlike its Part 2/Part 3 siblings): this
domain carries no timestamp at all -- see engine/review_gap_edb.py's own docstring, "NO TIME
CORRELATION" -- so there is no anchor-relative-vs-absolute rewrite step here. The two producers'
atoms are compared as emitted.

Read-only on every ledger. Standalone (not wired into `./audit`'s own flag set -- mirrors
engine/preamble_differential.py's own precedent: the REPORT surface is wired into
`./audit --review-gap` via engine/review_gap_audit.py + engine/contemp_audit.py, and this
differential is the separate verification/witness instrument a gate or a seen-red fixture invokes
directly). Lazy imports banned (top-of-file only)."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
from dataclasses import asdict, dataclass, field
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
from review_gap_edb import REVIEW_GAP_LP, export
from review_gap_floor import floor_atoms, full_capable, snapshot_text

HERE = Path(__file__).resolve().parent
RETENTION = HERE / "docs" / "ledger-marriage" / "derivations" / "review-gap-audit"


def run_asp(target_name: str) -> ProducerRun:
    """The ASP producer, run over `target_name`'s real EDB (engine/review_gap_edb.py)."""
    try:
        exp = export(target_name)
        if not exp.full_capable():
            missing = [c.family for c in exp.exclusions()]
            return ProducerRun("asp:clingo", quarantine=(
                f"target lacks a required capability: {missing} -- see engine/review_gap_edb.py's "
                f"own capability manifest; this is a capability-gated refusal, not a genuine "
                f"clingo/tool error, but the differential has NO verdict to compare without it"))
        edb_text = exp.edb_text()
        atoms = {a for a in run_clingo([REVIEW_GAP_LP], edb_text) if "(" in a}
    except Exception as e:  # noqa: BLE001 -- a genuine tool/DB/clingo error, not a finding
        return ProducerRun("asp:clingo", quarantine=f"clingo/EDB failed: {type(e).__name__}: {e}")
    program_text = REVIEW_GAP_LP.read_text(encoding="utf-8")
    rec = DerivationRecord(
        engine="clingo", version=_clingo_version(), config=[REVIEW_GAP_LP.name],
        input_basis="edb-text (review-gap-audit EDB export, serialized; engine/review_gap_edb.py)",
        input_hash=_sha(edb_text), program_hash=_sha(program_text),
        output_hash=_sha("\n".join(sorted(atoms))), target=target_name, ts=_now())
    return ProducerRun("asp:clingo", atoms=atoms, record=rec)


def run_sql(target_name: str) -> ProducerRun:
    """The SQL floor producer (engine/review_gap_floor.py)."""
    t = resolve_ledger(target_name)
    capable, _ = full_capable(t)
    if not capable:
        return ProducerRun("sql:floor", quarantine=(
            "target lacks a required capability -- see engine/review_gap_floor.py's own "
            "full_capable(); the differential has NO verdict to compare without it"))
    try:
        atoms = floor_atoms(target_name)
        snap = snapshot_text(target_name)
    except Exception as e:  # noqa: BLE001
        return ProducerRun("sql:floor", quarantine=f"SQL floor failed: {type(e).__name__}: {e}")
    db = t.db
    rec = DerivationRecord(
        engine="postgres", version=_pg_version(db), config=["review_gap_floor.py::floor_atoms"],
        input_basis=f"live-db rows read directly ({db}.{t.schema}.ledger + review_detail + "
                    f"countersign_obligation)",
        input_hash=_sha(snap),
        program_hash=_sha((HERE / "review_gap_floor.py").read_text(encoding="utf-8")),
        output_hash=_sha("\n".join(sorted(atoms))), target=target_name, ts=_now())
    return ProducerRun("sql:floor", atoms=atoms, record=rec)


@dataclass
class DifferentialResult:
    target: str
    asp: ProducerRun
    sql: ProducerRun
    only_asp: set[str] = field(default_factory=set)
    only_sql: set[str] = field(default_factory=set)

    def verdict(self) -> str:
        if self.asp.quarantine or self.sql.quarantine:
            return QUARANTINED
        if self.asp.record is None or self.sql.record is None:
            return QUARANTINED
        if not self.only_asp and not self.only_sql:
            return AGREE
        return DIVERGE_DEFECT  # no defeater-lens declared for this domain; any Δ is a defect


def run_differential(target_name: str, *,
                     asp_atoms_override: set[str] | None = None,
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
    res = DifferentialResult(target=target_name, asp=asp, sql=sql)
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
    ap.add_argument("target", help="ledger target name (ledger_edb.resolve()-able)")
    ap.add_argument("--retain", action="store_true",
                    help="bank proof artifacts under engine/docs/ledger-marriage/derivations/review-gap-audit/")
    ap.add_argument("--drop-record", action="store_true",
                    help="negative control: drop the ASP derivation record and show the "
                         "consumer refuses (a verdict without its witness is NO RESULT)")
    args = ap.parse_args(argv)

    print("# review-gap-audit marriage differential -- ASP (engine/lp/review_gap_audit.lp) vs "
          "SQL floor (engine/review_gap_floor.py)")
    print(f"#   target={args.target!r}")
    print(f"#   closed verdict vocabulary: {sorted(VERDICTS)}; RED = {sorted(RED)}\n")

    res = run_differential(args.target)
    if args.drop_record and res.asp.record is not None:
        res.asp.record = None
    print_result(res)
    if args.retain:
        d = retain(res)
        print(f"\n# retained: {d}")

    red = 1 if res.verdict() in RED else 0
    print(f"\n# {'DIFFERENTIAL RED' if red else 'DIFFERENTIAL GREEN'} -- "
          f"{'diverged/quarantined (NO RESULT)' if red else 'SQL floor bit-identical to the ASP verdict program'}")
    return red


if __name__ == "__main__":
    raise SystemExit(main())
