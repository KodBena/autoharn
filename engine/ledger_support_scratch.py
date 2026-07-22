#!/usr/bin/env python3
"""ledger_support_scratch -- the apparatus-authored exercise of the Increment-2 support-exposure
closure + discharge vocabulary (WORK-UNIT-exposure-discharge.md), on MY OWN scratch lineage, with
BOTH producers (ledger_support.lp ASP and the ledger_floor.support_floor_atoms CTE mirror)
differentialed bit-identically over eight hand-pre-registered fixtures.

CORRELATED-AUTHORSHIP MITIGATION (work unit §4). Both producers share an author, so bit-identity
proves agreement, not fidelity. The independent oracle is the hand-computed expected model in
consults/marriage-i2-exposure-discharge.md §0, WRITTEN AND COMMITTED BEFORE either producer ran;
each fixture ships a verdict-flipping mutation (DIVERGE_DEFECT). This module is the executable side.

SCRATCH DISCIPLINE. The lineage is `epistemic.marriage_support_scratch` -- created OUTSIDE every
evidence lineage (never nla, never any s* subject ledger, and NEVER marriage_dto_scratch -- the
maintainer's DTO attestation touchpoint is a SEPARATE, engineer-handled act this build does not
touch). Apparatus-owned, WRITABLE, idempotent (DROP+CREATE). NAMED IN THE WITNESS. The
affirms/assumes side tables are apparatus-authored SCRATCH-ONLY EDB (§3 pending ruling: whether
`affirms` becomes a kernel edge kind or a review-row convention is the maintainer's, unresolved).
Subject-facing bytes are untouched anywhere; evidence ledgers stay read-only."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from clingo_run import quote_term, run_clingo
from ledger_differential import AGREE, DIVERGE_DEFECT
from ledger_edb import PGHOST, export
from ledger_floor import SUPPORT_PREDS, support_floor_atoms, support_manifest

HERE = Path(__file__).resolve().parent
DB = "epistemic"
SCHEMA = "marriage_support_scratch"
TNOW_LP = HERE / "lp" / "ledger_tnow.lp"
ASSUMES_LP = HERE / "lp" / "ledger_assumes.lp"
SUPPORT_LP = HERE / "lp" / "ledger_support.lp"
WITNESS = HERE / "docs" / "ledger-marriage" / "support-scratch.witness.txt"

# The single-home wall-clock cursor: injected into the ASP EDB as now/1 AND passed to the SQL
# floor's temporal expiry, so both producers compare against ONE value (P1). PAST_BOUND is a year
# earlier, so assumption 800's validity is expired at NOW_EPOCH.
NOW_EPOCH = 1783324800   # 2026-07-06
PAST_BOUND = 1751788800  # 2025-07-06 -- a year past => expired


def _psql(sql: str) -> str:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-tAc", sql],
                          capture_output=True, text=True, check=True).stdout.strip()


# --------------------------------------------------------------- scratch schema --
def setup() -> None:
    """Author the fixture record. Idempotent (DROP+CREATE). All support edges are strictly backward
    in id EXCEPT the deliberate cycle fixture 7 (500<->510, apparatus-authored: the kernel's
    append-only earlier-target validation would not produce it -- that is WHY it is a fixture)."""
    _psql(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; CREATE SCHEMA {SCHEMA};")  # declared-drop: {SCHEMA} (declared scratch/test reset; blast radius = this schema only)
    _psql(f"""CREATE TABLE {SCHEMA}.ledger (
      id bigint PRIMARY KEY, ts timestamptz NOT NULL, kind text NOT NULL, concern text,
      status text, confidence text, statement text, rationale text, actor text,
      supersedes bigint, enacts bigint[], answers bigint, amends bigint, amends_scope text);""")
    # affirms(R,F,D): row R records F survives D's defeat. affirm_author derives from ledger.actor[R]
    # (P1: actor has one home). assumes(A,Scope) + I7 validity bound.
    _psql(f"""CREATE TABLE {SCHEMA}.support_affirm (
      r bigint NOT NULL, dependent bigint NOT NULL, antecedent bigint NOT NULL);""")
    _psql(f"""CREATE TABLE {SCHEMA}.support_assumes (
      assumption bigint NOT NULL, scope bigint NOT NULL, valid_until bigint NOT NULL);""")
    ts = "2026-07-06 10:00:00+00"
    rows = f"""INSERT INTO {SCHEMA}.ledger (id,ts,kind,concern,statement,actor,supersedes,enacts,answers) VALUES
     -- fixture 1: depth-3 chain (D superseded; E enacts D; F enacts E; G answers F)
     (100,'{ts}','decision','design','d100','a1',NULL,NULL,NULL),
     (105,'{ts}','decision','design','sup100','a1',100,NULL,NULL),
     (110,'{ts}','verification','enactment','E110','a1',NULL,ARRAY[100]::bigint[],NULL),
     (120,'{ts}','verification','enactment','F120','a1',NULL,ARRAY[110]::bigint[],NULL),
     (130,'{ts}','decision','design','G130','a1',NULL,NULL,120),
     -- fixture 2: dead intermediate (E itself also superseded)
     (200,'{ts}','decision','design','d200','a1',NULL,NULL,NULL),
     (205,'{ts}','decision','design','sup200','a1',200,NULL,NULL),
     (210,'{ts}','verification','enactment','E210','a1',NULL,ARRAY[200]::bigint[],NULL),
     (215,'{ts}','decision','design','sup210','a1',210,NULL,NULL),
     (220,'{ts}','verification','enactment','F220','a1',NULL,ARRAY[210]::bigint[],NULL),
     -- fixtures 3+4: discharge (350 by reviewer_b) + currency re-raise (X=320 undischarged)
     (300,'{ts}','decision','design','D300','a1',NULL,NULL,NULL),
     (305,'{ts}','decision','design','sup300','a1',300,NULL,NULL),
     (320,'{ts}','decision','design','X320','a1',NULL,NULL,NULL),
     (325,'{ts}','decision','design','sup320','a1',320,NULL,NULL),
     (310,'{ts}','verification','enactment','F310','author_f',NULL,ARRAY[300,320]::bigint[],NULL),
     (350,'{ts}','review','adjudication','affirm 310 survives 300','reviewer_b',NULL,NULL,NULL),
     -- fixture 6: self-affirmation (author of F=410 affirms F via 450)
     (400,'{ts}','decision','design','d400','a1',NULL,NULL,NULL),
     (405,'{ts}','decision','design','sup400','a1',400,NULL,NULL),
     (410,'{ts}','verification','enactment','F410','author_g',NULL,ARRAY[400]::bigint[],NULL),
     (450,'{ts}','review','adjudication','author_g self-affirms 410','author_g',NULL,NULL,NULL),
     -- fixture 7: cycle (500 enacts 510, 510 enacts 500 -- apparatus-authored)
     (500,'{ts}','verification','enactment','C500','a1',NULL,ARRAY[510]::bigint[],NULL),
     (510,'{ts}','verification','enactment','C510','a1',NULL,ARRAY[500]::bigint[],NULL),
     -- fixture 8: expired-assumption exposure (810 scope; 820 enacts 810; assumes 800 expired)
     (810,'{ts}','decision','design','scope810','a1',NULL,NULL,NULL),
     (820,'{ts}','verification','enactment','E820','a1',NULL,ARRAY[810]::bigint[],NULL);"""
    _psql(rows)
    _psql(f"INSERT INTO {SCHEMA}.support_affirm (r,dependent,antecedent) VALUES "
          f"(350,310,300), (450,410,400);")
    _psql(f"INSERT INTO {SCHEMA}.support_assumes (assumption,scope,valid_until) VALUES "
          f"(800,810,{PAST_BOUND});")


def add_superseded_affirmation() -> None:
    """Fixture 5: supersede the affirmation row 350 (row 360 supersedes 350). The discharge lapses
    -- affirmed(310,300) retracts and exposure_undischarged(310,300) returns, on BOTH producers."""
    _psql(f"""INSERT INTO {SCHEMA}.ledger (id,ts,kind,concern,statement,actor,supersedes) VALUES
      (360,'2026-07-06 10:00:00+00','decision','adjudication','retract affirmation 350','a1',350);""")


# -------------------------------------------------------------------- EDB + producers --
def support_edb() -> str:
    """The base EDB (ledger_edb over the scratch schema) PLUS the support/discharge/assumes fact
    families the ASP producer consumes. row_actor from ledger.actor (one home); affirm_author from
    the ledger.actor of the affirmation row; assumes/valid_until/now for the I7 expiry closure."""
    os.environ["LEDGER_DB"] = DB
    os.environ["LEDGER_SCHEMA"] = SCHEMA
    try:
        base = export(SCHEMA).edb_text()
    finally:
        del os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"]
    lines = [base, "% ---- support discharge EDB (scratch-only, §3 pending ruling) ----"]
    for row in _psql(f"SELECT id, actor FROM {SCHEMA}.ledger ORDER BY id;").splitlines():
        if row.strip():
            i, actor = row.split("|")
            lines.append(f"row_actor({int(i)},{quote_term(actor)}).")
    for row in _psql(f"SELECT sa.r, sa.dependent, sa.antecedent, l.actor FROM {SCHEMA}.support_affirm sa "
                     f"JOIN {SCHEMA}.ledger l ON l.id = sa.r ORDER BY sa.r;").splitlines():
        if row.strip():
            r, dep, ant, actor = row.split("|")
            lines.append(f"affirms({int(r)},{int(dep)},{int(ant)}).")
            lines.append(f"affirm_author({int(r)},{quote_term(actor)}).")
    lines.append("% ---- I7 assumes with validity bound + the run-time now cursor ----")
    lines.append(f"now({NOW_EPOCH}).")
    for row in _psql(f"SELECT assumption, scope, valid_until FROM {SCHEMA}.support_assumes "
                     f"ORDER BY assumption;").splitlines():
        if row.strip():
            a, scope, vu = row.split("|")
            lines.append(f"assumes({int(a)},{int(scope)}).")
            lines.append(f"valid_until({int(a)},{int(vu)}).")
    return "\n".join(lines) + "\n"


def asp_support_atoms(edb: str, programs: list[Path]) -> set[str]:
    """The ASP producer's SUPPORT-layer slice: run [tnow, assumes, support] and keep only the
    support vocabulary (the kernel + assumes predicates are differentialed in their own gates)."""
    atoms = {a for a in run_clingo(programs, edb) if "(" in a}
    return {a for a in atoms if a.split("(", 1)[0] in SUPPORT_PREDS}


@dataclass
class SupportDiff:
    verdict: str
    asp: set[str] = field(default_factory=set)
    sql: set[str] = field(default_factory=set)
    only_asp: set[str] = field(default_factory=set)
    only_sql: set[str] = field(default_factory=set)


def support_differential(*, programs: list[Path] | None = None, edb: str | None = None) -> SupportDiff:
    """Differential the support layer: ASP ([tnow, assumes, support], filtered to SUPPORT_PREDS)
    vs the SQL floor (support_floor_atoms). AGREE iff empty symmetric difference; any Δ is a
    DIVERGE_DEFECT (no defeater lens is declared this increment). `programs`/`edb` are the
    negative-control seams (a mutated support program / a mutated EDB)."""
    programs = programs or [TNOW_LP, ASSUMES_LP, SUPPORT_LP]
    edb = support_edb() if edb is None else edb
    asp = asp_support_atoms(edb, programs)
    sql = support_floor_atoms(SCHEMA, NOW_EPOCH)
    only_asp, only_sql = asp - sql, sql - asp
    verdict = AGREE if not only_asp and not only_sql else DIVERGE_DEFECT
    return SupportDiff(verdict, asp, sql, only_asp, only_sql)


# -------------------------------------------------------------- mutation variants --
# The recursive support_star line and the discharge lines, verbatim from ledger_support.lp. A
# mutation rewrites ONE to a never-firing / mis-keyed form so the ASP producer diverges from the
# unmutated SQL floor (a gate seen red -- ADR-0011: a clause never flipped is a claim, not a net).
_RECURSION = "support_star(F,D) :- support_edge(F,X,_), support_star(X,D)."
_AFFIRMED = "affirmed(F,D) :- affirms(R,F,D), not superseded(R), not affirm_sod_violation(R)."
_SOD = "affirm_sod_violation(R) :- affirms(R,F,_), affirm_author(R,P), row_actor(F,P)."
_CYCLE = "support_cycle(F) :- support_star(F,F)."

MUTATIONS = {
    # fixture: (find, replace) on ledger_support.lp text; "" replace deletes the recursive rule.
    "fix1_drop_recursion": (_RECURSION, ""),
    "fix2_drop_recursion": (_RECURSION, ""),
    "fix3_break_affirmed": (_AFFIRMED, "affirmed(F,D) :- affirms(R,F,D), superseded(R)."),
    "fix4_key_on_F_only": (_AFFIRMED, "affirmed(F,D) :- affirms(R,F,_), not superseded(R), exposure(F,D)."),
    "fix5_drop_currency": (_AFFIRMED, "affirmed(F,D) :- affirms(R,F,D)."),
    "fix6_drop_sod": (_SOD, _SOD[:-1] + ", R < 0."),
    "fix7_drop_cycle": (_CYCLE, _CYCLE[:-1] + ", F < 0."),
    "fix8_drop_recursion": (_RECURSION, ""),
}


def mutated_program(name: str, tmp: Path) -> list[Path]:
    """Write a mutated ledger_support.lp for the named fixture and return the program list."""
    find, repl = MUTATIONS[name]
    text = SUPPORT_LP.read_text(encoding="utf-8")
    assert find in text, f"mutation anchor not found for {name}"
    mut = tmp / f"ledger_support.{name}.lp"
    mut.write_text(text.replace(find, repl), encoding="utf-8")
    return [TNOW_LP, ASSUMES_LP, mut]


def show(atoms: set[str], pred: str) -> str:
    got = sorted(a for a in atoms if a.startswith(pred + "("))
    return " ".join(got) if got else "(none)"


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__,
                            formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    setup()
    WITNESS.parent.mkdir(parents=True, exist_ok=True)
    edb = support_edb()
    WITNESS.write_text(
        "# support-exposure scratch witness (Increment 2) -- the apparatus-authored §2/§3 exercise.\n"
        f"# scratch lineage: {DB}.{SCHEMA}  (OUTSIDE every evidence lineage; NEVER marriage_dto_scratch;\n"
        "#   apparatus-owned, writable, idempotent). Evidence ledgers (nla, s*): READ-ONLY throughout.\n"
        "# affirms/assumes side tables are SCRATCH-ONLY EDB (§3 pending ruling: affirms as a kernel\n"
        "#   edge kind vs a review-row convention is the maintainer's, unresolved).\n"
        f"# now cursor (one home; injected into ASP now/1 and the SQL floor): {NOW_EPOCH}\n\n" + edb,
        encoding="utf-8")

    res = support_differential(edb=edb)
    print(f"# support differential -- ASP [tnow+assumes+support] vs SQL support floor over {SCHEMA}")
    print(f"#   verdict: {res.verdict}   asp={len(res.asp)} sql={len(res.sql)} atoms")
    if res.only_asp or res.only_sql:
        print(f"#   Δasp={sorted(res.only_asp)}\n#   Δsql={sorted(res.only_sql)}")
    print("\n## capability manifest (§5, F49):")
    for fam, status in support_manifest(SCHEMA).items():
        print(f"  {fam:22} {status}")
    print("\n## the eight fixtures (support-layer atoms):")
    for label, pred in (("f1/2 exposure", "exposure"), ("f8 exposure_expired", "exposure_expired"),
                        ("affirmed", "affirmed"), ("f3/4/5 undischarged", "exposure_undischarged"),
                        ("f6 sod", "affirm_sod_violation"), ("f7 cycle", "support_cycle")):
        print(f"  {label:22} {show(res.asp, pred)}")
    print(f"\n# witness written: {WITNESS}")
    return 0 if res.verdict == AGREE else 1


if __name__ == "__main__":
    raise SystemExit(main())
