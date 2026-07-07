#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-06T05:35:36Z
#   last-change: 2026-07-06T14:58:09Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""ledger_floor -- the SQL FLOOR of the T_now judgments: producer ONE of the
marriage differential (design LEDGER-LOGIC-MARRIAGE.md §4; "SQL (recursive views)
-- this IS SQL's home turf" for monotone closure). Computes the SAME judgment
predicates as ledger_tnow.lp, in SQL recursive CTEs, over the same target, and
returns them as clingo-shaped ATOM STRINGS so ledger_differential.py can compare
the two producers by set-equality.

INDEPENDENCE (I6, ADR-0000 INDEP). This producer shares NO code path with clingo:
the closure is a Postgres `WITH RECURSIVE`, not the ASP grounder. Two genuinely
independent producers agreeing bit-identically is the substance of the differential;
a shared helper would defeat it. The only thing shared is the EDB source (one
ledger, read-only) and the id-is-order law (design §3 rule 2) -- every precedence
below keys on the integer id, never ts.

Read-only. Emits the SAME #show set as ledger_tnow.lp (minus DTO/assumes, which have
no SQL floor -- they are engine-layer-only consumers on the scratch lineage)."""
from __future__ import annotations

import sys

from ledger_edb import Target, resolve


def _enacts_cte(t: Target) -> str:
    """The normalized enacts edge source (e,d), for scalar (s10) or array enacts."""
    is_array = t.scalar(
        f"SELECT data_type FROM information_schema.columns WHERE table_schema='{t.schema}' "
        f"AND table_name='ledger' AND column_name='enacts';") == "ARRAY"
    if is_array:
        return (f"SELECT e.id AS e, u.tid AS d FROM {t.rel()} e "
                f"CROSS JOIN LATERAL unnest(e.enacts) AS u(tid)")
    return f"SELECT id AS e, enacts AS d FROM {t.rel()} WHERE enacts IS NOT NULL"


def _base_ctes(rel: str, enacts_cte: str, amends_cte: str, answers_cte: str) -> str:
    """The SHARED supersession/in-force/head closure + edge sources, as ONE SQL home
    (ADR-0012 P1: the supersession closure is a fact with one authoritative encoding, not a
    second CTE re-authored per consumer -- cancer B). floor_atoms (the kernel T_now floor) and
    support_floor_atoms (the Increment-2 support-exposure floor) BOTH build on this identical
    block, so the id-ordered supersession math cannot drift between the two SQL producers. The
    text is semantics-identical to the pre-extraction inline block; the byte-identity of the
    banked #show atoms is verified (§1.6), not asserted."""
    return f"""
      led AS (SELECT id, kind FROM {rel}),
      en AS ({enacts_cte}),
      am AS ({amends_cte}),
      ans AS ({answers_cte}),
      sup AS (SELECT id AS x, supersedes AS y FROM {rel} WHERE supersedes IS NOT NULL),
      sup_star(x,y) AS (
        SELECT x,y FROM sup
        UNION
        SELECT s.x, ss.y FROM sup s JOIN sup_star ss ON s.y = ss.x
      ),
      superseded AS (SELECT DISTINCT y AS id FROM sup_star),
      in_force AS (SELECT id FROM led WHERE id NOT IN (SELECT id FROM superseded)),
      head AS (
        SELECT id AS y, id AS h FROM in_force
        UNION
        SELECT ss.y, ss.x FROM sup_star ss WHERE ss.x NOT IN (SELECT id FROM superseded)
      )"""


def floor_atoms(name: str) -> set[str]:
    """The set of T_now judgment atoms the SQL floor derives for `name` (read-only)."""
    t = resolve(name)
    rel = t.rel()
    has_amends = t.has_col("amends")
    has_answers = t.has_col("answers")

    # amends/answers CTEs degrade to an empty relation where the capability is absent
    # (a pre-e13 schema) -- the same declared-exclusion posture as ledger_edb, in SQL.
    amends_cte = (f"SELECT id AS a, amends AS t FROM {rel} WHERE amends IS NOT NULL"
                  if has_amends else "SELECT NULL::bigint AS a, NULL::bigint AS t WHERE false")
    answers_cte = (f"SELECT id AS a, answers AS q FROM {rel} WHERE answers IS NOT NULL"
                   if has_answers else "SELECT NULL::bigint AS a, NULL::bigint AS q WHERE false")

    sql = f"""
    WITH RECURSIVE{_base_ctes(rel, _enacts_cte(t), amends_cte, answers_cte)},
      -- gate_ok(e,d): d<e ; sound rejects when some superseder x of d has x<e
      unsound AS (
        SELECT e.e, e.d FROM en e
        WHERE e.d < e.e
          AND EXISTS (SELECT 1 FROM sup_star ss WHERE ss.y = e.d AND ss.x < e.e)
      ),
      launder AS (
        SELECT u.e, u.d, h.h FROM unsound u JOIN head h ON h.y = u.d WHERE h.h <> u.d
      ),
      alias AS (
        SELECT e.e, e.d FROM en e JOIN led d ON d.id = e.d WHERE d.kind <> 'decision'
      ),
      stale AS (
        SELECT e.e, e.d FROM en e
        WHERE e.e IN (SELECT id FROM in_force) AND e.d IN (SELECT id FROM superseded)
      ),
      q AS (SELECT id FROM led WHERE kind = 'question'),
      -- F-A (fidelity review §1): a question is answered only by an IN-FORCE answer -- the
      -- answering row must not be superseded (the s13.question_status judgment). The mirror
      -- of ledger_tnow.lp's `answered(Q) :- answers(A,Q), not superseded(A).`; q_open derives
      -- from q_answered so the in-force filter has ONE home on this side too.
      q_answered AS (SELECT DISTINCT q.id FROM q JOIN ans ON ans.q = q.id
                     WHERE ans.a NOT IN (SELECT id FROM superseded)),
      q_open AS (SELECT id FROM q WHERE id NOT IN (SELECT id FROM q_answered)),
      cd_withdrawn AS (SELECT a, t FROM am WHERE a IN (SELECT id FROM superseded)),
      cd_moot AS (SELECT a, t FROM am
                  WHERE t IN (SELECT id FROM superseded)
                    AND a NOT IN (SELECT id FROM superseded)),
      cd_live AS (SELECT a, t FROM am
                  WHERE t NOT IN (SELECT id FROM superseded)
                    AND a NOT IN (SELECT id FROM superseded)),
      cond2 AS (SELECT t FROM cd_live GROUP BY t HAVING count(*) >= 2)
    SELECT 'in_force('||id||')' FROM in_force
    UNION ALL SELECT 'head('||y||','||h||')' FROM head
    UNION ALL SELECT 'unsound_derivation('||e||','||d||')' FROM unsound
    UNION ALL SELECT 'launder('||e||','||d||','||h||')' FROM launder
    UNION ALL SELECT 'alias_surface('||e||','||d||')' FROM alias
    UNION ALL SELECT 'stale_enactment_row('||e||','||d||')' FROM stale
    UNION ALL SELECT 'question_open('||id||')' FROM q_open
    UNION ALL SELECT 'question_answered('||id||')' FROM q_answered
    UNION ALL SELECT 'clause_defeat('||a||','||t||')' FROM cd_live
    UNION ALL SELECT 'clause_defeat_moot('||a||','||t||')' FROM cd_moot
    UNION ALL SELECT 'clause_defeat_withdrawn('||a||','||t||')' FROM cd_withdrawn
    UNION ALL SELECT 'condition2_individuation('||t||')' FROM cond2
    ;"""
    out = t.run(sql).stdout
    return {line.strip() for line in out.splitlines() if line.strip()}


# ===========================================================================
# Increment 2 -- the SUPPORT-EXPOSURE floor: producer ONE of the support differential
# (WORK-UNIT-exposure-discharge.md §2/§3). The SQL mirror of ledger_support.lp, computed in a
# recursive CTE over the union of the three support-edge kinds, differentialed bit-identically
# against the ASP producer over the scratch lineage. Reuses _base_ctes so the supersession/
# in-force closure has ONE SQL home (P1). Read-only.
#
# CYCLE-SAFETY (work unit §2 "cycle-safe ... the floor must not loop on a scratch cycle fixture";
# proven by fixture 7, not asserted). support_star is a set-`UNION` recursion over (dep,ant)
# PAIRS -- the pair domain is finite, so the recursion reaches fixpoint and TERMINATES on a cyclic
# graph, INCLUDING the self-pairs (F,F) that make support_cycle(F) fire. SPIRIT-OVER-LETTER (surfaced
# in the build consult): the work unit's literal suggestion (a path array / the SQL `CYCLE` clause)
# would DROP the self-pair that closes a cycle and thus DIVERGE from the ASP self-pair closure --
# breaking the differential AGREE requirement. The established ledger_floor.py idiom (set-UNION on
# pairs, exactly as sup_star above) IS the cycle guard here, and it is the only form that agrees
# with the monotone ASP recursion. Fixture 7 proves termination + agreement.
#
# The APPARATUS-AUTHORED SCRATCH-ONLY inputs (§3 pending ruling; side tables on the scratch schema):
#   <schema>.support_affirm(r, dependent, antecedent)   -- affirms(R,F,D); affirm_author is derived
#                                                          from the ledger `actor` of row r (P1: actor
#                                                          has one home, the ledger.actor column).
#   <schema>.support_assumes(assumption, scope, valid_until)  -- assumes(A,Scope) + the I7 bound.
# A schema lacking support_assumes marks exposure_expired DEFERRED (support_manifest), never a
# silent empty (F49). row_actor(F,P) is the ledger.actor column; affirm_sod_violation needs only
# the EQUALITY actor(r)==actor(dependent) -- no actor value crosses into a #shown support atom.

SUPPORT_PREDS = ("support_edge", "support_star", "support_cycle", "exposure",
                 "exposure_expired", "affirmed", "exposure_undischarged", "affirm_sod_violation")


def support_manifest(name: str) -> dict[str, str]:
    """The capability manifest for the support-exposure layer on `name` (§5, F49). Every family
    is declared PRODUCED or DEFERRED with its input basis -- a target lacking `support_assumes`
    facts gets `exposure_expired` marked DEFERRED, never a silent empty a consumer misreads as
    'no expired exposures exist'."""
    t = resolve(name)
    has_affirm = t.has_relation(f"{t.schema}.support_affirm")
    has_assumes = t.has_relation(f"{t.schema}.support_assumes")
    m: dict[str, str] = {}
    for fam in ("support_edge", "support_star", "support_cycle", "exposure"):
        m[fam] = "PRODUCED (basis: enacts/answers edges + supersession closure -- always available)"
    m["exposure_expired"] = ("PRODUCED (basis: support_assumes + now)" if has_assumes else
                             "DEFERRED (no support_assumes source on this target -- not a silent empty)")
    for fam in ("affirmed", "exposure_undischarged", "affirm_sod_violation"):
        m[fam] = ("PRODUCED (basis: support_affirm EDB, scratch-only per §3 pending ruling)"
                  if has_affirm else "DEFERRED (no support_affirm source on this target)")
    return m


def support_floor_atoms(name: str, now_epoch: int) -> set[str]:
    """The set of support-exposure atoms the SQL floor derives for `name` (read-only). `now_epoch`
    is the single-home wall-clock cursor the scratch loader also injects into the ASP EDB as
    now/1, so the temporal expiry compares against ONE value on both producers (P1)."""
    t = resolve(name)
    rel = t.rel()
    has_answers = t.has_col("answers")
    has_amends = t.has_col("amends")
    has_affirm = t.has_relation(f"{t.schema}.support_affirm")
    has_assumes = t.has_relation(f"{t.schema}.support_assumes")

    amends_cte = (f"SELECT id AS a, amends AS t FROM {rel} WHERE amends IS NOT NULL"
                  if has_amends else "SELECT NULL::bigint AS a, NULL::bigint AS t WHERE false")
    answers_cte = (f"SELECT id AS a, answers AS q FROM {rel} WHERE answers IS NOT NULL"
                   if has_answers else "SELECT NULL::bigint AS a, NULL::bigint AS q WHERE false")
    # affirm/assumes degrade to an empty relation where the scratch side-table is absent (the same
    # declared-exclusion posture as the column-gated CTEs) -- support_manifest names the DEFERRAL.
    affirm_cte = (f"SELECT r, dependent AS dep, antecedent AS ant FROM {t.schema}.support_affirm"
                  if has_affirm else
                  "SELECT NULL::bigint AS r, NULL::bigint AS dep, NULL::bigint AS ant WHERE false")
    assumes_cte = (f"SELECT assumption AS ant, scope AS dep, valid_until FROM {t.schema}.support_assumes"
                   if has_assumes else
                   "SELECT NULL::bigint AS ant, NULL::bigint AS dep, NULL::bigint AS valid_until WHERE false")

    sql = f"""
    WITH RECURSIVE{_base_ctes(rel, _enacts_cte(t), amends_cte, answers_cte)},
      aff AS ({affirm_cte}),
      asm AS ({assumes_cte}),
      support_edge(dep, ant, kind) AS (
        SELECT e, d, 'enacts' FROM en
        UNION ALL SELECT a, q, 'answers' FROM ans
        UNION ALL SELECT dep, ant, 'assumes' FROM asm
      ),
      support_star(f, d) AS (
        SELECT dep, ant FROM support_edge
        UNION
        SELECT ss.f, e.ant FROM support_star ss JOIN support_edge e ON e.dep = ss.d
      ),
      expired AS (SELECT ant FROM asm WHERE valid_until < {int(now_epoch)}),
      exposure AS (
        SELECT DISTINCT ss.f, ss.d FROM support_star ss
        WHERE ss.f IN (SELECT id FROM in_force) AND ss.d IN (SELECT id FROM superseded)
      ),
      exposure_expired AS (
        SELECT DISTINCT ss.f, ss.d FROM support_star ss
        WHERE ss.f IN (SELECT id FROM in_force) AND ss.d IN (SELECT ant FROM expired)
      ),
      sod AS (SELECT DISTINCT a.r FROM aff a
              JOIN {rel} lr ON lr.id = a.r JOIN {rel} lf ON lf.id = a.dep
              WHERE lr.actor = lf.actor),
      -- affirmed GATES on SoD-distinctness (r NOT IN sod), the exact mirror of ledger_dto.lp's
      -- decomp_attested gate -- a self-affirmation does not discharge (never a pass). See the
      -- spirit-over-letter note in ledger_support.lp; both producers gate identically.
      affirmed AS (SELECT DISTINCT dep, ant FROM aff
                   WHERE r NOT IN (SELECT id FROM superseded) AND r NOT IN (SELECT r FROM sod)),
      undischarged AS (SELECT f, d FROM exposure EXCEPT SELECT dep, ant FROM affirmed)
    SELECT 'support_edge('||dep||','||ant||','||kind||')' FROM support_edge
    UNION ALL SELECT 'support_star('||f||','||d||')' FROM support_star
    UNION ALL SELECT 'support_cycle('||f||')' FROM support_star WHERE f = d
    UNION ALL SELECT 'exposure('||f||','||d||')' FROM exposure
    UNION ALL SELECT 'exposure_expired('||f||','||d||')' FROM exposure_expired
    UNION ALL SELECT 'affirmed('||dep||','||ant||')' FROM affirmed
    UNION ALL SELECT 'exposure_undischarged('||f||','||d||')' FROM undischarged
    UNION ALL SELECT 'affirm_sod_violation('||r||')' FROM sod
    ;"""
    out = t.run(sql).stdout
    return {line.strip() for line in out.splitlines() if line.strip()}


def main(argv: list[str] | None = None) -> int:
    for name in (argv if argv is not None else sys.argv[1:]) or ["s10"]:
        atoms = floor_atoms(name)
        print(f"# ledger_floor(SQL) -- {name}: {len(atoms)} atoms")
        for a in sorted(atoms):
            print(f"  {a}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
