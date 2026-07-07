#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-06T05:37:25Z
#   last-change: 2026-07-06T06:06:28Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""ledger_differential -- the marriage's load-bearing gate: the ASP `T_now` program
(ledger_tnow.lp, second producer) differentialed BIT-IDENTICALLY against the SQL
floor (ledger_floor.py, producer one) over the banked, closed evidence. This is the
composability-as-correctness criterion made executable (design §3.1): the seam either
reproduces the floor's atoms exactly or it is WRONG WORK.

CLOSED VERDICT VOCABULARY (B4 / AC6; the F49 lesson -- a non-run read as clean is
forbidden). Every compared target gets ONE verdict from the closed set:
  AGREE               -- empty symmetric difference; the two producers match exactly.
  DIVERGE_BY_DESIGN   -- divergence only in a DECLARED defeater-lens set (none in this
                         increment; the FDE lens is deferred, §9.5) -- reserved, honest.
  DIVERGE_DEFECT      -- an undeclared divergence: an encoding bug surfaced before trust.
  QUARANTINED         -- a producer crashed / produced no result / its derivation record
                         is missing. NO RESULT (ADR-0015 Rule 3), never a pass.
QUARANTINED or DIVERGE_DEFECT exits NON-ZERO (turns a run red).

PER-SOLVER SELF-PROVENANCE (B3 / AC5; F6/I8 + F16/I11 -- "an unqualified prover is an
unverified verifier"). Every producer invocation banks a DerivationRecord
{engine + version, config/args, EDB hash, program hash, output hash, target, wall ts}
and its programs + EDB + output are RETAINED under docs/ledger-marriage/derivations/.
A verdict WITHOUT its two derivation records is treated as NO RESULT (demonstrated by
the --drop-record negative control: the consumer refuses, QUARANTINED).

Read-only on every ledger. Registered in the operator close_manifest as a declared
observer line (AC7; not yet mandatory -- observer-first, link 23 M-2)."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from clingo_run import run_clingo
from ledger_edb import PGHOST, export, resolve
from ledger_floor import floor_atoms

HERE = Path(__file__).resolve().parent
TNOW_LP = HERE / "lp" / "ledger_tnow.lp"
RETENTION = HERE / "docs" / "ledger-marriage" / "derivations"

# The closed verdict vocabulary -- a frozen set, so a stray string can never masquerade
# as a verdict (ADR-0012 P8: illegal states unrepresentable at the seam).
AGREE = "AGREE"
DIVERGE_BY_DESIGN = "DIVERGE_BY_DESIGN"
DIVERGE_DEFECT = "DIVERGE_DEFECT"
QUARANTINED = "QUARANTINED"
VERDICTS = frozenset({AGREE, DIVERGE_BY_DESIGN, DIVERGE_DEFECT, QUARANTINED})
RED = frozenset({DIVERGE_DEFECT, QUARANTINED})


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


@dataclass(frozen=True)
class DerivationRecord:
    """The F6/F16 provenance of ONE producer run: enough to re-run it decades later and
    to detect a silently-changed program or input. A differential verdict without BOTH
    producers' records is NO RESULT (ADR-0005 Rule 9 / ADR-0013 amendment).

    `input_basis` names WHAT the engine actually consumed, and `input_hash` hashes THAT --
    honestly per producer (out-of-frame audit finding 4): the ASP engine consumes the
    serialized EDB text (input_basis 'edb-text'), the SQL floor consumes the LIVE DB rows
    directly (input_basis 'live-db'), so the two records do NOT falsely assert a shared
    hashed artifact. Both derive from the same ledger; they hash their own true input."""
    engine: str
    version: str
    config: list[str]
    input_basis: str
    input_hash: str
    program_hash: str
    output_hash: str
    target: str
    ts: str


def _clingo_version() -> str:
    try:
        out = subprocess.run(["clingo", "--version"], capture_output=True, text=True, timeout=10)
        return out.stdout.splitlines()[0].strip() if out.stdout else "unknown"
    except Exception as e:  # noqa: BLE001 -- a missing engine version is a loud unknown, not a crash
        return f"unknown ({type(e).__name__})"


def _pg_version(db: str) -> str:
    try:
        out = subprocess.run(["psql", "-h", PGHOST, "-d", db, "-tAc", "SELECT version();"],
                             capture_output=True, text=True, timeout=15)
        return out.stdout.strip().split(" on ")[0] if out.stdout else "unknown"
    except Exception as e:  # noqa: BLE001
        return f"unknown ({type(e).__name__})"


@dataclass
class ProducerRun:
    """One producer's atoms + its derivation record (or a quarantine reason if it failed)."""
    name: str
    atoms: set[str] = field(default_factory=set)
    record: DerivationRecord | None = None
    quarantine: str | None = None


def run_asp(name: str, edb_text: str, program: Path = TNOW_LP) -> ProducerRun:
    """The ASP second producer. A grounding/solve crash QUARANTINES it (never silent)."""
    try:
        program_text = program.read_text(encoding="utf-8")  # a missing program is a quarantine,
        atoms = {a for a in run_clingo([program], edb_text) if "(" in a}  # not an uncaught crash
    except Exception as e:  # noqa: BLE001 -- clingo_run raises on a no-JSON grounding error
        return ProducerRun("asp:clingo", quarantine=f"clingo failed: {type(e).__name__}: {e}")
    # THE SILENT-NON-RUN HAZARD (F49, surfaced live): clingo emits valid JSON with an
    # UNKNOWN/empty model on a GROUNDING ERROR -- run_clingo returns [] rather than raising,
    # so a broken program would bank an empty-atom "result" as if it were a derivation. A
    # T_now run over a record with >=1 entry ALWAYS yields >=1 in_force atom (every ledger
    # has an unsuperseded row); zero atoms over a non-empty EDB means the engine did NOT run
    # the program -- QUARANTINE it (ADR-0015 Rule 3), never read the silence as a clean set.
    if "entry(" in edb_text and not atoms:
        return ProducerRun("asp:clingo",
                           quarantine="clingo produced ZERO atoms over a non-empty EDB "
                                       "(a grounding error emits empty JSON, not a raise) -- NO RESULT")
    rec = DerivationRecord(
        engine="clingo", version=_clingo_version(), config=[program.name],
        input_basis="edb-text (ledger_edb export, serialized)", input_hash=_sha(edb_text),
        program_hash=_sha(program_text),
        output_hash=_sha("\n".join(sorted(atoms))), target=name, ts=_now())
    return ProducerRun("asp:clingo", atoms=atoms, record=rec)


def _ledger_snapshot_hash(name: str) -> str:
    """A hash of the ACTUAL ledger rows the SQL floor reads (id, kind, supersedes, enacts,
    amends, answers) -- the floor's true input. NOT the EDB text (which the floor never
    consumes): the honest input hash for the SQL producer's derivation record (finding 4)."""
    t = resolve(name)
    amends_col = "coalesce(amends::text,'')" if t.has_col("amends") else "''"
    answers_col = "coalesce(answers::text,'')" if t.has_col("answers") else "''"
    cols = ["id", "kind", "coalesce(supersedes::text,'')", "coalesce(enacts::text,'')",
            amends_col, answers_col]
    snap = t.run(f"SELECT {', '.join(cols)} FROM {t.rel()} ORDER BY id;").stdout
    return _sha(snap)


def run_sql(name: str, edb_text: str) -> ProducerRun:
    """The SQL floor, producer one. Its input is the LIVE DB rows read directly by the
    recursive-CTE program, NOT the EDB text -- so the record hashes the ledger snapshot it
    actually consumed (input_basis 'live-db'), never over-claiming a shared artifact (finding 4)."""
    try:
        atoms = floor_atoms(name)
    except Exception as e:  # noqa: BLE001
        return ProducerRun("sql:floor", quarantine=f"SQL floor failed: {type(e).__name__}: {e}")
    db = resolve(name).db
    rec = DerivationRecord(
        engine="postgres", version=_pg_version(db), config=["ledger_floor.py::floor_atoms"],
        input_basis=f"live-db rows read directly ({db}.{resolve(name).schema}.ledger)",
        input_hash=_ledger_snapshot_hash(name),
        program_hash=_sha((HERE / "ledger_floor.py").read_text(encoding="utf-8")),
        output_hash=_sha("\n".join(sorted(atoms))), target=name, ts=_now())
    return ProducerRun("sql:floor", atoms=atoms, record=rec)


@dataclass
class DifferentialResult:
    target: str
    asp: ProducerRun
    sql: ProducerRun
    only_asp: set[str] = field(default_factory=set)
    only_sql: set[str] = field(default_factory=set)

    def verdict(self) -> str:
        # NO RESULT unless BOTH producers ran AND both derivation records are present
        # (AC5: a verdict without its witness is nothing).
        if self.asp.quarantine or self.sql.quarantine:
            return QUARANTINED
        if self.asp.record is None or self.sql.record is None:
            return QUARANTINED
        if not self.only_asp and not self.only_sql:
            return AGREE
        return DIVERGE_DEFECT  # no defeater-lens is declared this increment; any Δ is a defect


def run_differential(name: str, *, edb_text: str | None = None,
                     asp_program: Path = TNOW_LP,
                     asp_atoms_override: set[str] | None = None) -> DifferentialResult:
    """Differential one target. `edb_text` defaults to the live export; `asp_program`
    and `asp_atoms_override` are the negative-control seams (mutate one producer)."""
    if edb_text is None:
        edb_text = export(name).edb_text()
    asp = run_asp(name, edb_text, asp_program)
    if asp_atoms_override is not None and asp.quarantine is None:
        asp.atoms = asp_atoms_override
    sql = run_sql(name, edb_text)
    res = DifferentialResult(target=name, asp=asp, sql=sql)
    if asp.quarantine is None and sql.quarantine is None:
        res.only_asp = asp.atoms - sql.atoms
        res.only_sql = sql.atoms - asp.atoms
    return res


def retain(res: DifferentialResult, edb_text: str) -> Path:
    """Bank the proof artifacts (F16): the EDB, the derivation records, the atom outputs,
    under versioned storage so the derivation is re-runnable, not merely asserted."""
    d = RETENTION / res.target
    d.mkdir(parents=True, exist_ok=True)
    (d / "edb.lp").write_text(edb_text, encoding="utf-8")
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
    n = len(res.asp.atoms)
    print(f"  [{mark}] {res.target:6} {v:18} "
          f"asp={len(res.asp.atoms)} sql={len(res.sql.atoms)} atoms; "
          f"Δasp={sorted(res.only_asp)} Δsql={sorted(res.only_sql)}")
    if res.asp.quarantine:
        print(f"          asp QUARANTINED: {res.asp.quarantine}")
    if res.sql.quarantine:
        print(f"          sql QUARANTINED: {res.sql.quarantine}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="*", default=["s10", "s11", "s12", "s13", "nla"])
    ap.add_argument("--retain", action="store_true", help="bank proof artifacts (F16)")
    ap.add_argument("--drop-record", action="store_true",
                    help="negative control: drop the ASP derivation record and show the "
                         "consumer refuses (a verdict without its witness is NO RESULT)")
    args = ap.parse_args(argv)
    targets = args.targets or ["s10", "s11", "s12", "s13", "nla"]

    print("# marriage differential -- ASP T_now (ledger_tnow.lp) vs SQL floor (ledger_floor.py)")
    print(f"#   closed verdict vocabulary: {sorted(VERDICTS)}; RED = {sorted(RED)}\n")
    red = 0
    for name in targets:
        edb_text = export(name).edb_text()
        res = run_differential(name, edb_text=edb_text)
        if args.drop_record and res.asp.record is not None:
            res.asp.record = None  # simulate a lost witness
        print_result(res)
        if args.retain:
            retain(res, edb_text)
        if res.verdict() in RED:
            red = 1
    print(f"\n# {'DIFFERENTIAL RED' if red else 'DIFFERENTIAL GREEN'} -- "
          f"{'a target diverged/quarantined (NO RESULT)' if red else 'every target bit-identical to the SQL floor'}")
    return red


if __name__ == "__main__":
    raise SystemExit(main())
