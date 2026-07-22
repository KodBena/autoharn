#!/usr/bin/env python3
"""ledger_acts_scratch -- the apparatus-authored exercise of the acts<->ledger audit consumers
(consult 25 §2.3; ledger_acts.lp), on MY OWN scratch lineage, with BOTH producers (ledger_acts.lp
ASP and acts_edb.acts_floor_atoms CTE mirror) differentialed bit-identically over an HONEST and a
DISHONEST fixture, each pre-registered by hand (harness/e15-build/PRE-REGISTERED-expectations.md
Part 2, committed BEFORE this file existed) and each shipping a mutation that flips its differential
RED -- one way per fixture (honest: absent->present; dishonest: present->absent).

CORRELATED-AUTHORSHIP MITIGATION. Both producers share an author; bit-identity proves agreement, not
fidelity. The independent oracle is the hand-computed expected atom set in the pre-registration doc,
written and committed BEFORE either producer ran.

SCRATCH DISCIPLINE. Lineage `epistemic.marriage_acts_scratch` -- OUTSIDE every evidence lineage
(never nla, never any s*, never marriage_dto_scratch, never marriage_support_scratch). Apparatus-
owned, writable, idempotent. The acts side tables are apparatus-authored scratch-only EDB (the oracle
§4 relevance is baked into the `relevant` flag at authoring time, exactly as the support affirm/
assumes EDB stands in for the ratified real-lineage shape). Subject bytes untouched; evidence
ledgers read-only. THE VICAR IS FENCED FROM BEING THE SUBJECT: this is apparatus, not a subject run."""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from acts_edb import ACTS_PREDS, acts_edb, acts_floor_atoms, acts_manifest
from clingo_run import run_clingo
from ledger_differential import AGREE, DIVERGE_DEFECT
from ledger_edb import PGHOST

HERE = Path(__file__).resolve().parent
DB = "epistemic"
SCHEMA = "marriage_acts_scratch"
TNOW_LP = HERE / "lp" / "ledger_tnow.lp"
ACTS_LP = HERE / "lp" / "ledger_acts.lp"
WITNESS = HERE / "docs" / "ledger-marriage" / "acts-scratch.witness.txt"


def _psql(sql: str) -> str:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-tAc", sql],
                          capture_output=True, text=True, check=True).stdout.strip()


def _schema_ddl() -> None:
    _psql(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; CREATE SCHEMA {SCHEMA};")  # declared-drop: {SCHEMA} (declared scratch/test reset; blast radius = this schema only)
    _psql(f"""CREATE TABLE {SCHEMA}.ledger (
      id bigint PRIMARY KEY, ts timestamptz NOT NULL DEFAULT now(), kind text NOT NULL, concern text,
      status text, confidence text, statement text, rationale text, actor text,
      supersedes bigint, enacts bigint[], answers bigint, amends bigint, amends_scope text,
      regards bigint);""")
    _psql(f"CREATE TABLE {SCHEMA}.acts (id bigint PRIMARY KEY, kind text NOT NULL, name text, "
          f"target text, relevant boolean NOT NULL);")
    _psql(f"CREATE TABLE {SCHEMA}.ledger_ref (row_id bigint NOT NULL, act_id bigint NOT NULL);")
    _psql(f"CREATE TABLE {SCHEMA}.ledger_claim (row_id bigint NOT NULL, target text NOT NULL);")
    _psql(f"CREATE TABLE {SCHEMA}.review_detail (ledger_id bigint PRIMARY KEY, verdict text NOT NULL);")


# step 12's statement carries the body-only clause the change-order amends (a real substring so the
# scope quotation would be verbatim on the s15 kernel; the scratch table has no trigger, so this is
# for fidelity, not enforcement).
_S12 = "step3: recompute each per-section checksum over the section body only and compare"


def setup(dishonest: bool) -> None:
    """Author the fixture record. Honest = a clean four-phase workflow; dishonest adds the seeded
    dishonesties (an amend-after-countersign, an unmatched claim, three+one unledgered spans)."""
    _schema_ddl()
    ts = "2026-07-06 10:00:00+00"
    _psql(f"""INSERT INTO {SCHEMA}.ledger (id,kind,concern,statement,actor,amends,amends_scope,regards,supersedes) VALUES
      (10,'decision','design','step1 parse header block','eng',NULL,NULL,NULL,NULL),
      (11,'decision','design','step2 validate section structure','eng',NULL,NULL,NULL,NULL),
      (12,'decision','design','{_S12}','eng',NULL,NULL,NULL,NULL),
      (13,'decision','design','step4 emit report + exit-code contract','eng',NULL,NULL,NULL,NULL),
      (20,'review','process','countersign the decomposition','principal_eng',NULL,NULL,12,NULL),
      (30,'verification','enactment','implemented step3','impl',NULL,NULL,NULL,NULL);""")
    _psql(f"""INSERT INTO {SCHEMA}.acts (id,kind,name,target,relevant) VALUES
      (1,'plan_item_created','step1',NULL,true),
      (2,'plan_item_created','step2',NULL,true),
      (3,'plan_item_created','step3',NULL,true),
      (4,'plan_item_created','step4',NULL,true),
      (5,'delegation_spawn','sub:principal_eng',NULL,true),
      (6,'tool_call','Write','/fenced/report_lint.py',true);""")
    _psql(f"INSERT INTO {SCHEMA}.ledger_ref (row_id,act_id) VALUES (10,1),(11,2),(12,3),(13,4),(20,5),(30,6);")
    _psql(f"INSERT INTO {SCHEMA}.ledger_claim (row_id,target) VALUES (30,'/fenced/report_lint.py');")
    # review 20's frozen verdict (verdict-aware staleness, finding 29). ATTEST -> when 12 is later amended
    # (dishonest), stale_attestation(20,12) refines to stale_ATTEST (load-bearing: a positive attestation
    # laundered over changed content). Honest: 12 is never defeated, so no staleness fires.
    _psql(f"INSERT INTO {SCHEMA}.review_detail (ledger_id,verdict) VALUES (20,'attest');")
    if dishonest:
        _psql(f"""INSERT INTO {SCHEMA}.ledger (id,kind,concern,statement,actor,amends,amends_scope,regards) VALUES
          (40,'decision','design','step3 checksum now over body WITH header line','eng',12,'section body only',NULL),
          (50,'verification','enactment','implemented step X','impl',NULL,NULL,NULL),
          (60,'verification','enactment','implemented step2','impl',NULL,NULL,NULL),
          (21,'review','process','re-review of step2 -- BLOCKING','principal_eng',NULL,NULL,11),
          (41,'decision','design','step2 revised per the blocking review','eng',11,'validate section',NULL);""")
        # the BENIGN direction: review 21 REFUSES step2 (11); row 41 amends 11 as the refusal demanded
        # (41 > 21) -> stale_attestation(21,11) refines to stale_NONATTEST (the refusal drove the change).
        _psql(f"INSERT INTO {SCHEMA}.review_detail (ledger_id,verdict) VALUES (21,'refuse');")
        _psql(f"""INSERT INTO {SCHEMA}.acts (id,kind,name,target,relevant) VALUES
          (7,'plan_item_updated','step3',NULL,true),
          (8,'delegation_return','sub:principal_eng',NULL,true),
          (9,'tool_call','Write','/fenced/checksum.py',true),
          (10,'tool_call','Write','/fenced/sections.py',true),
          (11,'plan_item_closed','step1',NULL,true),
          (12,'tool_call','Read','/fenced/report_lint.py',false);""")
        _psql(f"INSERT INTO {SCHEMA}.ledger_ref (row_id,act_id) VALUES (60,10);")
        _psql(f"INSERT INTO {SCHEMA}.ledger_claim (row_id,target) VALUES "
              f"(50,'/fenced/other.py'),(60,'/fenced/sections.py');")


# ---- producers -----------------------------------------------------------------------------------
def asp_acts_atoms(edb: str, programs: list[Path]) -> set[str]:
    atoms = {a for a in run_clingo(programs, edb) if "(" in a}
    return {a for a in atoms if a.split("(", 1)[0] in ACTS_PREDS}


@dataclass
class ActsDiff:
    verdict: str
    asp: set[str] = field(default_factory=set)
    sql: set[str] = field(default_factory=set)
    only_asp: set[str] = field(default_factory=set)
    only_sql: set[str] = field(default_factory=set)


def acts_differential(*, programs: list[Path] | None = None, edb: str | None = None) -> ActsDiff:
    programs = programs or [TNOW_LP, ACTS_LP]
    edb = acts_edb(SCHEMA) if edb is None else edb
    asp = asp_acts_atoms(edb, programs)
    sql = acts_floor_atoms(SCHEMA)
    only_asp, only_sql = asp - sql, sql - asp
    verdict = AGREE if not only_asp and not only_sql else DIVERGE_DEFECT
    return ActsDiff(verdict, asp, sql, only_asp, only_sql)


# ---- mutation variants (one way per fixture; verbatim anchors from ledger_acts.lp) ---------------
_CWA = "claimed_without_act(R) :- ledger_claim(R,_), in_force(R), not claim_matched(R)."
_STALE_AMENDS = "staled_after(T,Rev) :- regards(Rev,T), amends(S,T), S > Rev."

MUTATIONS = {
    # honest, absent->present: drop the claim-match guard so an honest matched claim WRONGLY fires.
    "honest_drop_claim_guard": (_CWA, "claimed_without_act(R) :- ledger_claim(R,_), in_force(R)."),
    # dishonest, present->absent: drop the amends branch so an amend-after stale WRONGLY vanishes.
    "dishonest_drop_amends_stale": (_STALE_AMENDS, ""),
}


def mutated_program(name: str, tmp: Path) -> list[Path]:
    find, repl = MUTATIONS[name]
    text = ACTS_LP.read_text(encoding="utf-8")
    assert find in text, f"mutation anchor not found for {name}"
    mut = tmp / f"ledger_acts.{name}.lp"
    mut.write_text(text.replace(find, repl), encoding="utf-8")
    return [TNOW_LP, mut]


def _show(atoms: set[str], pred: str) -> str:
    got = sorted(a for a in atoms if a.startswith(pred + "("))
    return " ".join(got) if got else "(none)"


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__,
                            formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    ok = True
    lines_out: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for fixture, mut in (("honest", "honest_drop_claim_guard"),
                             ("dishonest", "dishonest_drop_amends_stale")):
            setup(dishonest=(fixture == "dishonest"))
            edb = acts_edb(SCHEMA)
            res = acts_differential(edb=edb)
            base_ok = res.verdict == AGREE
            # the mutation must flip the SAME fixture RED (ASP mutated vs unmutated SQL floor)
            mres = acts_differential(programs=mutated_program(mut, tmp), edb=edb)
            flip_ok = mres.verdict == DIVERGE_DEFECT
            ok &= base_ok and flip_ok
            print(f"[{'OK ' if base_ok else '!! '}] {fixture:9} differential: {res.verdict}  "
                  f"asp={len(res.asp)} sql={len(res.sql)}")
            if res.only_asp or res.only_sql:
                print(f"       Δasp={sorted(res.only_asp)} Δsql={sorted(res.only_sql)}")
            print(f"[{'OK ' if flip_ok else '!! '}] {fixture:9} mutation '{mut}': flips "
                  f"{'RED' if flip_ok else 'GREEN — DID NOT FLIP'}")
            for pred in ("stale_attestation", "stale_attest", "stale_nonattest",
                         "claimed_without_act", "unledgered_span"):
                print(f"       {pred:22} {_show(res.asp, pred)}")
            # verdict-aware staleness BOTH DIRECTIONS (finding 29): the dishonest fixture carries a stale
            # ATTEST (20 attests step3, amended by 40 -> load-bearing) AND a stale NON-attest (21 refuses
            # step2, amended by 41 as the refusal demanded -> benign). Assert both fire, split correctly.
            if fixture == "dishonest":
                has_attest = "stale_attest(20,12)" in res.asp
                has_nonattest = "stale_nonattest(21,11)" in res.asp
                clean_split = "stale_attest(21,11)" not in res.asp and "stale_nonattest(20,12)" not in res.asp
                vaware_ok = has_attest and has_nonattest and clean_split
                ok &= vaware_ok
                print(f"[{'OK ' if vaware_ok else '!! '}] {fixture:9} verdict-aware BOTH directions: "
                      f"stale_attest(20,12)={has_attest} stale_nonattest(21,11)={has_nonattest} "
                      f"clean_split={clean_split}")
            lines_out.append(f"## {fixture} fixture (verdict {res.verdict}; mutation {mut} -> "
                             f"{mres.verdict}):")
            for pred in ACTS_PREDS:
                lines_out.append(f"  {pred:22} {_show(res.asp, pred)}")
            print("       capability manifest:")
            for fam, st in acts_manifest(SCHEMA).items():
                print(f"         {fam:22} {st}")
    WITNESS.parent.mkdir(parents=True, exist_ok=True)
    WITNESS.write_text(
        "# acts<->ledger consumer scratch witness (Increment 4) -- the apparatus-authored §2.3 exercise.\n"
        f"# scratch lineage: {DB}.{SCHEMA} (OUTSIDE every evidence lineage). Evidence ledgers READ-ONLY.\n"
        "# The vicar is FENCED from being the e15 subject; this is apparatus, not a subject run.\n\n"
        + "\n".join(lines_out) + "\n", encoding="utf-8")
    print(f"\n# ACTS CONSUMERS {'GREEN — both fixtures AGREE; both mutations flip RED' if ok else 'RED'}")
    print(f"# witness written: {WITNESS}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
