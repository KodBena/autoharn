#!/usr/bin/env python3
"""ledger_diff_scratch -- a purpose-built scratch lineage that makes EVERY T_now predicate
FIRE on non-empty input, so the marriage differential (ledger_floor.py SQL vs ledger_tnow.lp
ASP) is exercised on firing input for ALL 12 predicates -- not empty-vs-empty agreement.

WHY THIS EXISTS (out-of-frame audit finding 1). The five banked targets carry ZERO `amends`
and ZERO `answers` rows (ground truth: the columns are absent on s10-s12, present-but-empty on
s13/nla). So over the banked set, `clause_defeat`, `clause_defeat_moot`, `clause_defeat_withdrawn`,
`condition2_individuation`, and `question_answered` are EMPTY on both producers -- their SQL-floor
CTEs (ledger_floor.py) were never once compared to their ASP twins on input where they fire. That
is the F49 vacuous-pass at the differential level: agreement because there is nothing to compare.
This scratch lineage closes it -- a hand-authored record where every predicate has a live instance,
differentialed by the SAME runner (ledger_differential.run_differential), so the SQL encoding of the
clause-defeat family is VERIFIED, not asserted.

SCRATCH DISCIPLINE: `epistemic.marriage_diff_scratch` -- outside every evidence lineage,
apparatus-owned, writable, idempotent (DROP+CREATE). Evidence ledgers stay read-only."""
from __future__ import annotations

import subprocess
import sys

from ledger_edb import PGHOST

DB = "epistemic"
SCHEMA = "marriage_diff_scratch"

# The predicate families this fixture is built to make FIRE (the differential-coverage contract).
COVERAGE = (
    "in_force", "head", "unsound_derivation", "launder", "alias_surface",
    "stale_enactment_row", "question_open", "question_answered",
    "clause_defeat", "clause_defeat_moot", "clause_defeat_withdrawn", "condition2_individuation",
)


def _psql(sql: str) -> str:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-tAc", sql],
                          capture_output=True, text=True, check=True).stdout.strip()


def setup() -> None:
    """Author a small ledger where every T_now predicate has a live instance. All edges are
    strictly backward in id (append-only + earlier-target validation), so closures terminate."""
    _psql(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; CREATE SCHEMA {SCHEMA};")  # declared-drop: {SCHEMA} (declared scratch/test reset; blast radius = this schema only)
    _psql(f"""CREATE TABLE {SCHEMA}.ledger (
      id bigint PRIMARY KEY, ts timestamptz NOT NULL, kind text NOT NULL, concern text,
      status text, confidence text, statement text, rationale text, actor text,
      supersedes bigint, enacts bigint[], answers bigint, amends bigint, amends_scope text);""")
    # id | kind | edges  (design: every predicate fires)
    #  1 question (answered by 20)         -> question_answered(1); alias target of enacts(17,1)
    #  2 question (stays open)             -> question_open(2)
    #  3 decision (in force)               -> target of two live amends (4,5) => condition2(3)
    #  4 snag amends 3                     -> clause_defeat(4,3)
    #  5 snag amends 3                     -> clause_defeat(5,3) + condition2_individuation(3)
    #  6 decision, superseded by 7         -> defeated
    #  7 decision supersedes 6
    #  8 snag amends 6 (6 gone, 8 live)    -> clause_defeat_moot(8,6)
    #  9 decision (in force)               -> target of amends 10
    # 10 snag amends 9, superseded by 11   -> clause_defeat_withdrawn(10,9)
    # 11 decision supersedes 10
    # 15 verification enacts 3 (sound)     -> gate_ok, not unsound
    # 16 verification enacts 6 (6 defeated pre-16) -> unsound_derivation(16,6), launder(16,6,7), stale_enactment_row(16,6)
    # 17 verification enacts 1 (1 question)-> alias_surface(17,1)
    # 20 decision answers 1                -> question_answered(1)
    # --- F-A superseded-answer fixture (fidelity review §1): a question whose answer is
    #     later RETRACTED (superseded) must REOPEN. Before the fix both producers left it
    #     "answered" forever; the differential was blind because no fixture exercised the
    #     branch. With the fix (`answered :- answers(A,Q), not superseded(A)`) it flips to open.
    # 21 question (answered by 23, answer 23 then superseded by 24) -> question_open(21), NOT question_answered(21)
    # 23 decision answers 21               -> answered(21) ONLY while 23 in force
    # 24 decision supersedes 23            -> answer 23 retracted -> question 21 reopens
    # --- F-D self-superseding-citation fixture (fidelity review §1 / boundary): a row that
    #     BOTH supersedes D and enacts D. Under STRICT id-precedence (`X < E`, the ratified
    #     id-is-order law, consult 17 §5.3) the self-citer names the antecedent it replaces
    #     and is SOUND (no unsound_derivation(26,22)); under ts-`<=` it would be unsound. This
    #     is the boundary case absent from every banked record (id-order == ts-order there),
    #     so the differential could not see the strict/non-strict choice until this fixture.
    # 22 decision (design antecedent D)    -> superseded by its own enactor 26
    # 26 verification enacts 22 AND supersedes 22 -> gate_ok(26,22), SOUND (strict); stale_enactment_row(26,22); head(22,26)
    rows = f"""INSERT INTO {SCHEMA}.ledger (id,ts,kind,concern,statement,actor,supersedes,enacts,answers,amends,amends_scope) VALUES
     (1 ,'2026-07-06 10:00:00+00','question','design','q1','a',NULL,NULL,NULL,NULL,NULL),
     (2 ,'2026-07-06 10:00:01+00','question','design','q2','a',NULL,NULL,NULL,NULL,NULL),
     (3 ,'2026-07-06 10:00:02+00','decision','design','d3','a',NULL,NULL,NULL,NULL,NULL),
     (4 ,'2026-07-06 10:00:03+00','snag','design','s4','a',NULL,NULL,NULL,3,'clause quote alpha'),
     (5 ,'2026-07-06 10:00:04+00','snag','design','s5','a',NULL,NULL,NULL,3,'clause quote beta'),
     (6 ,'2026-07-06 10:00:05+00','decision','design','d6','a',NULL,NULL,NULL,NULL,NULL),
     (7 ,'2026-07-06 10:00:06+00','decision','design','d7','a',6,NULL,NULL,NULL,NULL),
     (8 ,'2026-07-06 10:00:07+00','snag','design','s8','a',NULL,NULL,NULL,6,'clause quote gamma'),
     (9 ,'2026-07-06 10:00:08+00','decision','design','d9','a',NULL,NULL,NULL,NULL,NULL),
     (10,'2026-07-06 10:00:09+00','snag','design','s10','a',NULL,NULL,NULL,9,'clause quote delta'),
     (11,'2026-07-06 10:00:10+00','decision','design','d11','a',10,NULL,NULL,NULL,NULL),
     (15,'2026-07-06 10:00:11+00','verification','enactment','v15','a',NULL,ARRAY[3]::bigint[],NULL,NULL,NULL),
     (16,'2026-07-06 10:00:12+00','verification','enactment','v16','a',NULL,ARRAY[6]::bigint[],NULL,NULL,NULL),
     (17,'2026-07-06 10:00:13+00','verification','enactment','v17','a',NULL,ARRAY[1]::bigint[],NULL,NULL,NULL),
     (20,'2026-07-06 10:00:14+00','decision','design','d20','a',NULL,NULL,1,NULL,NULL),
     (21,'2026-07-06 10:00:15+00','question','design','q21','a',NULL,NULL,NULL,NULL,NULL),
     (22,'2026-07-06 10:00:16+00','decision','design','d22','a',NULL,NULL,NULL,NULL,NULL),
     (23,'2026-07-06 10:00:17+00','decision','design','d23','a',NULL,NULL,21,NULL,NULL),
     (24,'2026-07-06 10:00:18+00','decision','design','d24','a',23,NULL,NULL,NULL,NULL),
     (26,'2026-07-06 10:00:19+00','verification','enactment','v26','a',22,ARRAY[22]::bigint[],NULL,NULL,NULL);"""
    _psql(rows)


def main(argv: list[str] | None = None) -> int:
    setup()
    # import here would be lazy; the runner is imported at module top of the test. For the CLI
    # demo we shell out to the differential so this module stays import-light for setup use.
    cp = subprocess.run([sys.executable, "ledger_differential.py", SCHEMA],
                        capture_output=True, text=True)
    print(cp.stdout)
    return cp.returncode


if __name__ == "__main__":
    raise SystemExit(main())
