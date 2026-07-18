#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-06T05:37:25Z
#   last-change: 2026-07-18T05:41:51Z
#   contributors: 37017f46/main, be693afb/main, a857c93d/main, ab5d5bab/main
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

import lp_registry
from clingo_run import run_clingo
from ledger_edb import PGHOST, DefeatParseError, export, export_defeat, export_work, resolve
from ledger_floor import (DEFEAT_PREDS, WORK_ITEM_PREDS, WORK_REVIEW_PREDS, defeat_floor_atoms,
                          floor_atoms, work_item_floor_atoms, work_review_floor_atoms)

HERE = Path(__file__).resolve().parent
LP_DIR = HERE / "lp"
TNOW_LP = LP_DIR / "ledger_tnow.lp"
RETENTION = HERE / "docs" / "ledger-marriage" / "derivations"

# The predicates the "work" layer's differential compares (plan step 8(ii)) -- the union of both
# work-layer #show families, never the whole composed stack's atoms (which also carries
# ledger_tnow.lp's own in_force/head/etc, out of scope for THIS comparison -- the "tnow" layer
# already covers those via the standing run_differential above).
WORK_LAYER_PREDS = frozenset(WORK_ITEM_PREDS) | frozenset(WORK_REVIEW_PREDS)

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


def run_asp(name: str, edb_text: str, program: Path = TNOW_LP,
           programs: list[Path] | None = None) -> ProducerRun:
    """The ASP second producer. A grounding/solve crash QUARANTINES it (never silent).

    `program` (single-Path, the original signature) stays the default -- every existing caller
    (tests, negative controls) is unaffected. `programs` is the plan-step-8(ii) generalization: a
    caller running a NAMED LAYER (engine/lp_registry.py's LAYERS) passes the whole stack here
    instead; when given, it wins over `program`. Neither this function nor `run_differential`
    below CHECKS the stack against the registry -- that is `run_layer_differential`'s job (it
    calls `lp_registry.require_layer_stack` BEFORE reaching here); this function stays a thin,
    registry-agnostic producer, same as it always was for the single-program case."""
    prog_list = programs if programs is not None else [program]
    try:
        program_text = "\n".join(p.read_text(encoding="utf-8") for p in prog_list)  # a missing
        atoms = {a for a in run_clingo(prog_list, edb_text) if "(" in a}  # program is a quarantine
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
        engine="clingo", version=_clingo_version(), config=[p.name for p in prog_list],
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


# ===========================================================================
# THE "work" LAYER DIFFERENTIAL (plan step 8(ii); the second named F7 gap this build closes --
# "ledger_differential.py is single-program-typed with TNOW_LP hardcoded"). Runs the SAME
# AGREE/DIVERGE_DEFECT/QUARANTINED vocabulary as run_differential above, but composes
# engine/lp_registry.py's "work" LAYER (ledger_tnow.lp + work_items.lp + work_review.lp) against
# the work-item/work-review SQL floors, over ledger_edb.export_work's new EDB family -- the SAME
# comparison seen-red/s31-supersession-uniform-retraction/run_fixtures.py hand-assembled as "the
# standing ./judge differential ... named separate seam" (that fixture's own h-differential-agree
# docstring). `judge` (bootstrap/templates/judge.tmpl) forwards every extra CLI flag through to
# this module unchanged (`"$@"`), so `./judge --layer work` reaches `main` below with NO template
# edit needed -- an existing, already-generic passthrough, not a new wiring point.
def run_sql_work(name: str, edb_text: str) -> ProducerRun:
    """The SQL floor for the 'work' layer: work_item_floor_atoms | work_review_floor_atoms,
    restricted to WORK_LAYER_PREDS (the tnow-layer atoms -- in_force/head/etc -- are out of scope
    for this comparison, exactly as run_sql's floor_atoms is out of scope for the work layer)."""
    t = resolve(name)
    if not t.has_col("work_slug"):
        return ProducerRun("sql:floor(work)",
                           quarantine="target has no `work_slug` column (pre-s22 lineage) -- "
                                       "the 'work' layer has no substrate here, capability absent")
    try:
        atoms = work_item_floor_atoms(name) | work_review_floor_atoms(name)
        atoms = {a for a in atoms if a.split("(", 1)[0] in WORK_LAYER_PREDS}
    except Exception as e:  # noqa: BLE001
        return ProducerRun("sql:floor(work)", quarantine=f"SQL work floor failed: {type(e).__name__}: {e}")
    rec = DerivationRecord(
        engine="postgres", version=_pg_version(t.db),
        config=["ledger_floor.py::work_item_floor_atoms", "ledger_floor.py::work_review_floor_atoms"],
        input_basis=f"live-db rows read directly ({t.db}.{t.schema}.ledger[/ledger_current])",
        input_hash=_ledger_snapshot_hash(name),
        program_hash=_sha((HERE / "ledger_floor.py").read_text(encoding="utf-8")),
        output_hash=_sha("\n".join(sorted(atoms))), target=name, ts=_now())
    return ProducerRun("sql:floor(work)", atoms=atoms, record=rec)


def run_sql_defeat(name: str, edb_text: str) -> ProducerRun:
    """The SQL floor for the 'defeat' layer (design/FABLE-DEFEAT-PIPELINE-SPEC.md §7):
    defeat_floor_atoms, restricted to DEFEAT_PREDS. QUARANTINES on a pre-s41 target with the
    capability reason (mirroring run_sql_work's pre-s22 refusal, F49) and on a malformed v1
    attestation statement (§3 P-5 -- the SQL-side raise, caught here, never a silent skip)."""
    t = resolve(name)
    if not (t.has_col("principal_binding_active") and t.has_col("principal_competence_activity")):
        return ProducerRun("sql:floor(defeat)",
                           quarantine="target has no principal_binding_active/"
                                       "principal_competence_activity columns (pre-s41 lineage) "
                                       "-- the 'defeat' layer has no grant substrate here, "
                                       "capability absent, not record-empty")
    try:
        atoms = defeat_floor_atoms(name)
        atoms = {a for a in atoms if a.split("(", 1)[0] in DEFEAT_PREDS}
    except Exception as e:  # noqa: BLE001 -- a malformed v1 row (P-5) raises SQL-side; QUARANTINE, never a crash
        return ProducerRun("sql:floor(defeat)", quarantine=f"SQL defeat floor failed: {type(e).__name__}: {e}")
    rec = DerivationRecord(
        engine="postgres", version=_pg_version(t.db),
        config=["ledger_floor.py::defeat_floor_atoms"],
        input_basis=f"live-db rows read directly ({t.db}.{t.schema}.ledger[/ledger_current])",
        input_hash=_ledger_snapshot_hash(name),
        program_hash=_sha((HERE / "ledger_floor.py").read_text(encoding="utf-8")),
        output_hash=_sha("\n".join(sorted(atoms))), target=name, ts=_now())
    return ProducerRun("sql:floor(defeat)", atoms=atoms, record=rec)


_LAYER_FLOOR_PREDS = {"work": WORK_LAYER_PREDS, "defeat": frozenset(DEFEAT_PREDS)}


def run_layer_differential(name: str, layer: str = "work", *,
                           program_names: list[str] | None = None) -> DifferentialResult:
    """Differential one target on a NAMED layer (engine/lp_registry.py's LAYERS). `program_names`
    defaults to the layer's own full, registry-declared stack (always valid by construction); a
    caller passing an INCOMPLETE list here (the red-polarity seam -- see the seen-red fixture this
    delta ships) hits `lp_registry.require_layer_stack`'s typed refusal (`RegistryError`) BEFORE
    any clingo invocation -- never a silent empty grounding (the F7 hazard this closes)."""
    names = program_names if program_names is not None else list(lp_registry.LAYERS[layer])
    lp_registry.require_layer_stack(layer, names)  # raises RegistryError on a mis-stacked list
    paths = [LP_DIR / n for n in names]
    if layer not in _LAYER_FLOOR_PREDS:
        raise NotImplementedError(f"run_layer_differential only implements the "
                                  f"{sorted(_LAYER_FLOOR_PREDS)} floor comparisons this build "
                                  f"shipped; layer {layer!r} has no SQL floor wired here yet "
                                  f"(the 'tnow' layer's is run_differential).")
    preds = _LAYER_FLOOR_PREDS[layer]
    if layer == "work":
        try:
            edb_text = export(name).edb_text() + "\n" + export_work(name).edb_text()
        except Exception as e:  # noqa: BLE001
            qr = f"EDB export failed: {type(e).__name__}: {e}"
            asp, sql = ProducerRun("asp:clingo", quarantine=qr), ProducerRun("sql:floor(work)", quarantine=qr)
            return DifferentialResult(target=name, asp=asp, sql=sql)
        asp = run_asp(name, edb_text, programs=paths)
        if asp.quarantine is None:
            asp.atoms = {a for a in asp.atoms if a.split("(", 1)[0] in preds}
        sql = run_sql_work(name, edb_text)
    else:  # "defeat" -- §3 P-5: a malformed v1 attestation raises in EACH producer's OWN
        # independent parse (export_defeat's Python parser for ASP; defeat_floor_atoms' SQL
        # parser for the floor). Building the shared edb_text calls export_defeat() first, so a
        # malformed row is caught THERE and both producers are QUARANTINED with the same reason
        # -- "both producers fail identically" (P-5), never a one-sided failure.
        try:
            base = export(name)
            defeat_exp = export_defeat(name)
            # §4.3/§7: require() the four grounding families BEFORE use -- a pre-s41 target (no
            # trust_grant/grant_row substrate) QUARANTINES here with the capability reason,
            # rather than grounding a vacuously-empty derivation that would read AGREE (the F49
            # vacuous-pass class, foreclosed exactly as run_sql_work forecloses pre-s22 targets).
            for fam in ("trust_grant", "attest_row", "mismatch_attest", "row_actor"):
                defeat_exp.require(fam)
            edb_text = base.edb_text() + "\n" + defeat_exp.edb_text()
        except DefeatParseError as e:
            qr = f"malformed v1 attestation (P-5): {e}"
            asp, sql = ProducerRun("asp:clingo", quarantine=qr), ProducerRun("sql:floor(defeat)", quarantine=qr)
            return DifferentialResult(target=name, asp=asp, sql=sql)
        except Exception as e:  # noqa: BLE001 -- e.g. a pre-s41 target's require() capability refusal
            qr = f"EDB export failed: {type(e).__name__}: {e}"
            asp, sql = ProducerRun("asp:clingo", quarantine=qr), ProducerRun("sql:floor(defeat)", quarantine=qr)
            return DifferentialResult(target=name, asp=asp, sql=sql)
        asp = run_asp(name, edb_text, programs=paths)
        if asp.quarantine is None:
            asp.atoms = {a for a in asp.atoms if a.split("(", 1)[0] in preds}
        sql = run_sql_defeat(name, edb_text)
    res = DifferentialResult(target=name, asp=asp, sql=sql)
    if asp.quarantine is None and sql.quarantine is None:
        res.only_asp = asp.atoms - sql.atoms
        res.only_sql = sql.atoms - asp.atoms
    return res


def _run_unique_dir(target: str, edb_text: str) -> Path:
    """The run-unique retention subdir: <target>/<UTC-ts>_<input_hash[:12]>/. Never a single
    mutable slot per target -- a bare `RETENTION / target` was clobbered wholesale by a later
    --retain run reusing the same path, silently overwriting the FIRST run's banked
    DerivationRecord pair with the second's (the exact single-mutable-slot defect this
    directory scheme forecloses; see BACKLOG.md). `edb_text`'s hash disambiguates two runs
    that land in the same UTC second; the timestamp disambiguates two runs over the same EDB."""
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return RETENTION / target / f"{ts}_{_sha(edb_text)[:12]}"


def retain(res: DifferentialResult, edb_text: str) -> Path:
    """Bank the proof artifacts (F16): the EDB, the derivation records, the atom outputs,
    under a RUN-UNIQUE subdirectory of versioned storage, so the derivation is re-runnable
    AND every prior run's evidence stays on disk rather than being overwritten in place."""
    d = _run_unique_dir(res.target, edb_text)
    d.mkdir(parents=True, exist_ok=False)  # exist_ok=False: a same-second, same-EDB collision
                                            # fails loudly (ADR-0002) rather than silently reusing
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
    ap.add_argument("--layer", choices=sorted(lp_registry.LAYERS), default="tnow",
                    help="which engine/lp_registry.py LAYER to differential (plan step 8(ii)): "
                         "'tnow' (default, unchanged behavior -- ledger_tnow.lp vs "
                         "ledger_floor.py::floor_atoms) or 'work' (ledger_tnow.lp + "
                         "work_items.lp + work_review.lp vs the work-item/work-review SQL "
                         "floors, over ledger_edb.export_work's EDB), or 'defeat' "
                         "(ledger_tnow.lp + ledger_support.lp + ledger_defeat.lp vs "
                         "ledger_floor.py::defeat_floor_atoms, over ledger_edb.export_defeat's "
                         "EDB -- design/FABLE-DEFEAT-PIPELINE-SPEC.md §7). `judge` forwards this "
                         "flag through unchanged -- `./judge --layer work`.")
    args = ap.parse_args(argv)
    targets = args.targets or ["s10", "s11", "s12", "s13", "nla"]

    print(f"# marriage differential -- layer={args.layer!r}")
    print(f"#   closed verdict vocabulary: {sorted(VERDICTS)}; RED = {sorted(RED)}\n")
    red = 0
    for name in targets:
        edb_text = ""
        if args.layer == "tnow":
            edb_text = export(name).edb_text()
            res = run_differential(name, edb_text=edb_text)
        else:
            try:
                if args.layer == "work":
                    edb_text = export(name).edb_text() + "\n" + export_work(name).edb_text()
                elif args.layer == "defeat":
                    edb_text = export(name).edb_text() + "\n" + export_defeat(name).edb_text()
            except Exception as e:  # noqa: BLE001 -- e.g. DefeatParseError (P-5); run_layer_differential
                pass                # re-derives and QUARANTINES properly; edb_text stays "" for --retain
            res = run_layer_differential(name, args.layer)
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
