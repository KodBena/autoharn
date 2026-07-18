#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-06T05:35:36Z
#   last-change: 2026-07-18T05:50:47Z
#   contributors: 37017f46/main, be693afb/main, a857c93d/main, 9a17b6b9/main, ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""ledger_floor -- the SQL FLOOR of the T_now judgments: producer ONE of the
marriage differential (design ORCH-LEDGER-LOGIC-MARRIAGE.md §4; "SQL (recursive views)
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


# ===========================================================================
# Increment 3 (s22) -- the WORK-ITEM LEDGER floor: producer ONE of the work-item differential
# (design/ORCH-S22-WORK-ITEM-LEDGER.md; engine/lp/work_items.lp is producer two, reconciled by
# engine/work_item_scratch.py / kernel/fixtures/s22_work_item_fixture.py). Computes the SAME base
# relations + four judgments engine/lp/work_items.lp #shows (work_dep_edge/2, work_dep_star/2,
# work_duplicate_open/1, work_shipped_without_witness/2, work_depends_on_unknown/2,
# work_dependency_cycle/1), as clingo-shaped atom strings, via a Postgres `WITH RECURSIVE` --
# SQL's home turf for the transitive-closure half, matching floor_atoms/support_floor_atoms above.
#
# INDEPENDENCE (I6, ADR-0000 INDEP) PRESERVED: this module's whole reason to exist is sharing NO
# code path with clingo. `_wi_quote` below is a LOCAL, standalone string-escape helper -- NOT
# imported from `clingo_run.quote_term` (which would thread a clingo-side module into the SQL
# producer) -- deliberately duplicated in the SAME spirit `clingo_run.quote_term`'s own docstring
# names ("contra_asp keeps its own spaCy-side `_quote`; this is kb_why's"): a trivial string-escape
# helper is NOT the logic under test, so two independent copies cost nothing and keep the
# producers genuinely separate. Its escaping matches `quote_term` byte-for-byte (backslash then
# quote, in that order) so both producers' quoted-string atoms compare bit-identically.
def _wi_quote(col: str) -> str:
    """A SQL expression rendering `col` (text) as a clingo term -- the SQL-side mirror of
    `ledger_edb._atom` (NOT `clingo_run.quote_term`, and not a call to either -- see the
    independence note above), matched here for the FIRST time (s37 fix, hazard-in-reach per
    CLAUDE.md's engineering-responsibility corollary: found live while building s37's own
    dependency_cycle/orphaned_by_retraction narrowing, witnessed causing DIVERGE_DEFECT on an
    UNTOUCHED s36 baseline world for a single bare `./led work open probe1 ...` -- `_atom()`
    (ledger_edb.py) renders a SAFE lowercase identifier (e.g. a typical slug) as a BARE clingo
    constant, but this function unconditionally quoted every value, so the SQL floor and the .lp
    producer have compared bit-UNEQUAL atom text for every ordinary slug since `_atom`'s own
    bare/quoted branch was written -- `./judge --layer work` could not read AGREE on ANY world,
    for ANY target, independent of this delta's own content). Fixed to the SAME branch: bare when
    `col` is non-empty, starts with a lowercase letter, and contains only lowercase letters,
    digits, and underscores (COALESCE/empty maps to the bare constant `none`, matching `_atom`'s
    own empty-string case); quoted-string otherwise, same escaping as before. The three sibling
    files carrying this same byte-identical 'independent mirror' comment (engine/ordering_floor.py
    `_quote`, engine/preamble_floor.py `_atom_quote`, engine/contemp_floor.py `_atom_quote`) were
    checked and are NOT affected by this same defect: each one's own EDB counterpart quotes
    unconditionally on both sides (no bare-when-safe branch to diverge from), so the asymmetry
    fixed here was specific to `ledger_edb._atom`'s bare/quoted pairing, not a shape the other
    three producers share."""
    quoted = "('\"' || replace(replace(" + col + ", '\\', '\\\\'), '\"', '\\\"') || '\"')"
    return (
        "(CASE WHEN " + col + " IS NULL OR " + col + " = '' THEN 'none' "
        "WHEN " + col + " ~ '^[a-z][a-z0-9_]*$' THEN " + col + " "
        "ELSE " + quoted + " END)"
    )


WORK_ITEM_PREDS = ("work_dep_edge", "work_dep_star", "work_duplicate_open",
                   "work_shipped_without_witness", "work_depends_on_unknown",
                   "work_dependency_cycle", "work_orphaned_by_retraction")


def work_item_floor_atoms(name: str) -> set[str]:
    """The set of work-item atoms the SQL floor derives for `name` (read-only), reading the s22
    work_* columns directly off `<schema>.ledger`. `duplicate_open` and `shipped_without_witness`
    are provably vacuous under normal operation (s22's write-boundary trigger + CHECK constraint
    refuse both at construction -- see s22-work-item-ledger.sql's header); this floor still emits
    them (defense in depth, matching engine/lp/work_items.lp's identical stance) so a scratch
    fixture that bypasses the live trigger (an apparatus-authored negative-control row, never a
    real write path) still differentials correctly against the ASP producer.

    CORRELATED-AUTHORSHIP CAVEAT (named, per the ledger_support_scratch.py precedent): this floor
    and the s22 DDL view (`work_item_violations`) share an author and the same base facts, so
    bit-identity between THIS floor and `work_items.lp` proves ENCODING agreement between the SQL
    and ASP producers, not independent fidelity to the spec -- the same caveat every `*_scratch.py`
    differential in this file already carries.

    s31 (kernel/lineage/s31-supersession-uniform-retraction.sql): gains the ONE current-truth
    member, work_orphaned_by_retraction -- an IN-FORCE later event (claim/close/dep edge/child
    open) whose slug's opening act is retracted -- read off `<schema>.ledger_current` exactly as
    the DDL view's four orphan_* CTEs do.

    s37 v3 amendment (design/FABLE-ORPHAN-DISPOSITION-SPEC.md v3, design/ORCH-CONSULT-DEBT-
    SEMANTICS-2026-07-16.md, ratified 2026-07-16): THE DEBT PROJECTION QUANTIFIES OVER IN-FORCE
    ROWS ONLY. This docstring's OWN prior text here claimed every pre-existing member (duplicate
    opens, dangling deps, cycles) "deliberately KEEPS its raw reading" -- SUPERSEDED by this same
    amendment: dup_open/shipped_no_witness/dangling_dep/the blocks-close cycle arms now carry
    row-scoped in-force anti-joins (or read `{rel_cur}` directly), mirroring the kernel view's own
    move off raw `ledger` onto `ledger_current` throughout (kernel/lineage/
    s37-violation-disposition.sql). The plain, id-less dependency GRAPH (`deps`/`reach`, feeding
    `work_dep_edge`/`work_dep_star`) is the one deliberate exception, UNCHANGED -- it still answers
    "did this edge ever exist", matching work_items.lp's own identical split."""
    t = resolve(name)
    rel = t.rel()
    rel_cur = t.rel("ledger_current")
    q_dependent, q_antecedent = _wi_quote("dependent"), _wi_quote("antecedent")
    q_start, q_cur = _wi_quote("start_slug"), _wi_quote("cur")
    q_slug = _wi_quote("slug")
    # s37 (kernel/lineage/s37-violation-disposition.sql): dependency_cycle NARROWS to blocks-close
    # edges only (RATIFIED sibling narrowing, consult A1(b)) -- column-gated exactly like
    # orphan_children_arm above: a pre-s30 target has no edge_type column at all, so `bc_deps`/
    # `dep_cycle` degrade to an empty set (properly vacuous, matching the ASP twin's own
    # capability-gated #defined work_dep_type/2 degrading identically for free on a pre-s30
    # exporter). `deps`/`dangling_dep`/`reach` below (depends_on_unknown_slug's OWN computation)
    # are UNCHANGED -- this narrowing is scoped to dependency_cycle alone. s37 v3 amendment: reads
    # `{rel_cur}` (was `{rel}`) -- an in-force-only blocks-close edge set, mirroring the kernel
    # view's bc_deps CTE moving to a `work_edge_blocks_close JOIN ledger_current` composition
    # (kernel/lineage/s37-violation-disposition.sql).
    bc_deps_cte = (
        "bc_deps AS (SELECT work_slug AS dependent, work_depends_on AS antecedent "
        f"FROM {rel_cur} WHERE kind = 'work_depends_on' AND edge_type = 'blocks-close'), "
        "bc_reach(start_slug, cur) AS ("
        "  SELECT dependent, antecedent FROM bc_deps"
        "  UNION"
        "  SELECT r.start_slug, d.antecedent FROM bc_reach r JOIN bc_deps d ON d.dependent = r.cur"
        "), "
        "dep_cycle AS (SELECT DISTINCT start_slug AS slug FROM bc_reach WHERE cur = start_slug)"
        if t.has_col("edge_type") else
        "dep_cycle AS (SELECT NULL::text AS slug WHERE false)"
    )
    # s37: a raw arm drops out only while an in-force disposition answers it AND that
    # disposition's basis still holds -- mirroring the kernel view's disposition_basis_holds join
    # (see kernel/lineage/s37-violation-disposition.sql, same predicate, independently re-derived
    # here per ADR-0000 I6's do-not-abstract-across-producers posture). Column-gated: a pre-s37
    # target has no work_violation_class column, so every arm stays exactly its pre-s37 shape.
    #
    # s37 v3 amendment (design/FABLE-ORPHAN-DISPOSITION-SPEC.md v3, design/ORCH-CONSULT-DEBT-
    # SEMANTICS-2026-07-16.md part 2D: "remove the unconditional target-currency requirement").
    # `JOIN {rel_cur} t ON t.id = d.target_id` below is KEPT, not deleted -- mirroring the kernel's
    # own choice (that CTE's own v3 comment carries the full proof). SAME PROOF, restated for this
    # producer: disposition_basis_holds is consulted ONLY via `_disposition_filter`'s anti-join
    # against a candidate row (shipped_no_witness/dangling_dep/orphans/orphan_children below) that
    # is ITSELF now sourced from `{rel_cur}` or carries its own in-force anti-join (this same
    # function's other v3 edits) -- so every (class, target_id) pair this join is ever asked about
    # already has a current target by construction. The join can never again FALSIFY a basis that
    # would otherwise hold; a disposition on a later-retracted target is MOOT (its candidate row
    # already absent upstream), never DEFEATED here -- "moot, never defeated" (spec Element 3),
    # achieved structurally, matching both the kernel producer and work_items.lp's own identical
    # choice so all three stay literal mirrors of the same invariant.
    # s37 fix (reviewer defect 4, ADR-0014-review round): the FIRST draft hardcoded this filter's
    # class literal to 'orphaned_by_retraction' and applied it to ONE arm (`orphans`), while the
    # kernel VIEW's own anti-join is UNIFORM over every arm carrying a real target_id -- a class
    # gaining a real target_id elsewhere (shipped_without_witness always had one; depends_on_
    # unknown_slug gains one in THIS SAME fix round, defect 1) would then narrow in the kernel
    # VIEW but not in this floor, an undetectable-by-construction DIVERGE_DEFECT (the mismatch IS
    # what judge exists to catch; a class-hardcoded filter can't even look at a class it wasn't
    # told about). `_disposition_filter(class_literal, id_expr)` below is the SAME SQL fragment
    # parameterized instead of duplicated -- applied to every arm whose ASP-comparable atom
    # carries a real row id (orphans/orphan_children, shipped_no_witness, dangling_dep -- the
    # SAME three the .lp twin's now-generalized w_vdisp_basis_holds/3 covers). duplicate_open/
    # dependency_cycle/dangling_parent/parent_cycle/blocks_close_cycle are NOT covered -- their
    # ASP-comparable atoms carry no id argument at all (a pre-existing atom-shape limit, not
    # something this fix changes), named here rather than silently left unaddressed.
    disposition_join = ("""
      dispositions AS (
        SELECT id AS disp_id, work_violation_class AS class, work_violation_target_id AS target_id,
               work_resolution AS resolution, work_violation_witness AS witness_id
        FROM """ + rel_cur + """ WHERE kind = 'work_violation_disposition'
      ),
      disposition_basis_holds AS (
        SELECT d.class, d.target_id
        FROM dispositions d
        JOIN """ + rel_cur + """ t ON t.id = d.target_id
        WHERE
          (d.resolution = 'retired' AND (
             t.kind <> 'work_opened'
             OR EXISTS (SELECT 1 FROM """ + rel_cur + """ cw
                        WHERE cw.kind = 'work_closed' AND cw.work_slug = t.work_slug)
          ))
          OR
          (d.resolution = 'reissued' AND (
             d.witness_id IS NULL
             OR EXISTS (SELECT 1 FROM """ + rel_cur + """ w WHERE w.id = d.witness_id)
          ))
      )"""
                        if t.has_col("work_violation_class") else "")

    def _disposition_filter(class_literal: str, id_expr: str) -> str:
        if not t.has_col("work_violation_class"):
            return ""
        return (f"AND NOT EXISTS (SELECT 1 FROM disposition_basis_holds dbh "
                f"WHERE dbh.class = '{class_literal}' AND dbh.target_id = {id_expr})")

    orphans_filter = _disposition_filter("orphaned_by_retraction", "lc.id")
    # the child-orphan arm needs work_parent (s28) -- column-gated so a pre-s28 target (e.g. the
    # s22 fixture's own probe chain) degrades to the three event-kind arms, the same
    # declared-exclusion posture the amends/answers CTEs above already take. The ASP twin
    # degrades identically for free: a pre-s28 exporter emits no work_parent_edge/3 facts. Carries
    # the SAME s37 disposition filter as the main `orphans` WHERE above -- this arm is a
    # UNION ALL'd sibling of that same predicate, not a separate one.
    orphan_children_arm = (f"""UNION ALL
        SELECT lc.work_slug AS slug, lc.id FROM {rel_cur} lc
        WHERE lc.kind = 'work_opened' AND lc.work_parent IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = lc.work_parent)
          {orphans_filter}"""
                           if t.has_col("work_parent") else "")
    sql = f"""
    WITH RECURSIVE
      -- s37 v3 amendment: `opens_cur` is a NEW, separate CTE ({rel_cur}-sourced) feeding ONLY
      -- dup_open below -- mirroring the kernel view's opens_cur CTE. `opens` (unqualified, RAW,
      -- unchanged) stays the one dangling_dep's antecedent check reads (see that CTE's own v3
      -- CORRECTNESS NOTE below for why raw is deliberate, not an oversight).
      opens_cur AS (
        SELECT work_slug AS slug FROM {rel_cur} WHERE kind = 'work_opened'
      ),
      dup_open AS (
        SELECT slug FROM opens_cur GROUP BY slug HAVING count(*) > 1
      ),
      opens AS (
        SELECT work_slug AS slug FROM {rel} WHERE kind = 'work_opened'
      ),
      -- s37 fix (defect 4): shipped_without_witness already carried a real id (the close row's
      -- own) -- narrowed here for the first time, uniformly with the other id-bearing arms. s37
      -- v3 amendment: reads {rel_cur} (was {rel}) -- the close row itself must be in force,
      -- mirroring the kernel view's shipped_no_witness CTE.
      shipped_no_witness AS (
        SELECT work_slug AS slug, id FROM {rel_cur}
        WHERE kind = 'work_closed' AND work_resolution = 'shipped'
          AND (work_witness IS NULL OR btrim(work_witness) = '')
          {_disposition_filter("shipped_without_witness", "id")}
      ),
      -- s37 fix (defect 1): `deps` gains the depending act's OWN id -- see kernel/lineage/
      -- s37-violation-disposition.sql's identical fix for why (NULL never equality-matches, so
      -- depends_on_unknown_slug was permanently unanswerable without it). `deps` itself STAYS raw
      -- (feeds `reach`/work_dep_star, the general dependency GRAPH, deliberately unnarrowed).
      deps AS (
        SELECT work_slug AS dependent, work_depends_on AS antecedent, id FROM {rel}
        WHERE kind = 'work_depends_on'
      ),
      -- s37 v3 amendment: the depends_on row's OWN id must be in force (a row-scoped anti-join on
      -- d.id, since `deps` itself stays raw for `reach`'s sake -- the house idiom this file's own
      -- `review_gap`-shaped in-force anti-joins already use elsewhere) -- mirroring the kernel
      -- view's dangling_dep CTE (element 1's actual gate: the MEMBER'S OWN TARGET row, d.id here).
      --
      -- v3 CORRECTNESS NOTE (hazard-in-reach, found and fixed live building this delta -- see
      -- kernel/lineage/s37-violation-disposition.sql's dangling_dep CTE, same fix, same reason):
      -- the antecedent-opened check below reads `opens` (RAW, defined above) -- UNCHANGED,
      -- deliberately NOT switched to `opens_cur`. Element 1 does not redefine the
      -- antecedent-opened PREDICATE itself, only the target row's (d.id) own currency. Reading
      -- the antecedent check current-truth would make this arm fire for "antecedent was opened,
      -- then later retracted" -- a shape work_items.lp's OWN `not work_opened(Antecedent,_)`
      -- (kept raw, same fix, same file) can never reproduce, which would silently DIVERGE the
      -- SQL/ASP differential `./judge` exists to catch. Kept raw so this floor's member set is
      -- always the in-force-target SUBSET of the raw-antecedent-check set, matching both the
      -- kernel view's and the ASP twin's own corrected posture exactly.
      dangling_dep AS (
        SELECT d.dependent AS slug, d.antecedent, d.id FROM deps d
        WHERE NOT EXISTS (SELECT 1 FROM opens o WHERE o.slug = d.antecedent)
          AND NOT EXISTS (SELECT 1 FROM {rel} s WHERE s.supersedes = d.id)
          {_disposition_filter("depends_on_unknown_slug", "d.id")}
      ),
      reach(start_slug, cur) AS (
        SELECT dependent, antecedent FROM deps
        UNION
        SELECT r.start_slug, d.antecedent FROM reach r JOIN deps d ON d.dependent = r.cur
      ),
      {bc_deps_cte},
      -- s31: the in-force orphan member, mirroring work_item_violations' orphan_* CTEs (see
      -- docstring). Reads ledger_current -- the one SQL home of the in-force projection.
      opened_current AS (
        SELECT work_slug AS slug FROM {rel_cur} WHERE kind = 'work_opened'
      ){"," if disposition_join else ""}
      {disposition_join},
      orphans AS (
        SELECT lc.work_slug AS slug, lc.id FROM {rel_cur} lc
        WHERE lc.kind IN ('work_claimed', 'work_closed', 'work_depends_on')
          AND NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = lc.work_slug)
          {orphans_filter}
        {orphan_children_arm}
      )
    SELECT 'work_dep_edge(' || {q_dependent} || ',' || {q_antecedent} || ')' FROM deps
    UNION ALL SELECT 'work_dep_star(' || {q_start} || ',' || {q_cur} || ')' FROM reach
    UNION ALL SELECT 'work_duplicate_open(' || {q_slug} || ')' FROM dup_open
    UNION ALL SELECT 'work_shipped_without_witness(' || {q_slug} || ',' || id || ')' FROM shipped_no_witness
    UNION ALL SELECT 'work_depends_on_unknown(' || {q_slug} || ',' || {q_antecedent} || ')' FROM dangling_dep
    UNION ALL SELECT 'work_dependency_cycle(' || {q_slug} || ')' FROM dep_cycle
    UNION ALL SELECT DISTINCT 'work_orphaned_by_retraction(' || {q_slug} || ',' || id || ')' FROM orphans
    ;"""
    out = t.run(sql).stdout
    return {line.strip() for line in out.splitlines() if line.strip()}


WORK_REVIEW_PREDS = ("w_tree_member", "w_own_leaf_unresolved", "w_tree_unresolved")


def work_review_floor_atoms(name: str) -> set[str]:
    """The set of s29 obligation-tree atoms the SQL floor derives for `name` (read-only), reading
    the s29 work_review_* columns directly off `<schema>.ledger` + `review_detail` -- the SQL-side
    mirror of `engine/lp/work_review.lp`, independently derived (NO shared code path with clingo,
    the SAME I6 posture `work_item_floor_atoms` above declares -- see that function's own
    INDEPENDENCE PRESERVED note; this floor duplicates the SAME reasoning rather than importing it).

    CORRECTED (out-of-frame hack-rationalization audit, same session, before this file's first
    commit): a first draft walked ONLY the s28 parent edge and treated a `work_depends_on`
    antecedent as resolved once it had ANY close row. Mirrors `work_item_strict_blockers()`'s own
    identical correction in `kernel/lineage/s29-...sql` and `work_review.lp`'s own `w_succ`
    predicate: a `work_depends_on` edge is walked OPPOSITE its own column order (the dependent
    plays the "parent" role in tree-membership terms, its antecedent plays the "child" role).

    CORRELATED-AUTHORSHIP CAVEAT (named, per `work_item_floor_atoms`'s own precedent): this floor
    and the s29 DDL (`work_item_strict_blockers()`, `work_review_gap`) share an author and the same
    base facts, so bit-identity between THIS floor and `work_review.lp` proves ENCODING agreement
    between the SQL and ASP producers, not independent fidelity to the spec.

    s31 (kernel/lineage/s31-supersession-uniform-retraction.sql): opens/succ/closes read
    `<schema>.ledger_current` (in-force events only), byte-for-byte the semantics of the DDL
    twin's own s31 re-issue (work_item_strict_blockers()'s edges/closes CTEs). The `discharged`
    leg is UNCHANGED -- the discharge-review side was already in-force-filtered at its source on
    both producers (the ratified spec's own sec-2 finding), so it keeps its raw read + row-scoped
    anti-join exactly as the DDL does.

    s33 (kernel/lineage/s33-composite-discharge.sql): `not_closed` gains the SAME composite-with-
    children exemption `work_item_strict_blockers()`'s own s33 re-issue adds -- a composite tree
    member (`work_discharge='composite'` on its own IN-FORCE work_opened row) with at least one
    child in THIS SAME `succ` walk is resolved through its own children, never requiring its own
    close row (never vacuously discharged when it has zero children). Column-gated (the SAME
    convention `orphan_children_arm` above uses for `work_parent`) so a pre-s33 target degrades to
    the byte-identical pre-s33 reading -- no `work_discharge` column, no exemption possible."""
    t = resolve(name)
    rel = t.rel()
    rel_cur = t.rel("ledger_current")
    q_root, q_member = _wi_quote("t.root"), _wi_quote("t.member")
    q_slug = _wi_quote("slug")
    composite_exempt = (
        f"""AND NOT (
          EXISTS (SELECT 1 FROM {rel_cur} oo WHERE oo.kind = 'work_opened'
                  AND oo.work_slug = o.slug AND oo.work_discharge = 'composite')
          AND EXISTS (SELECT 1 FROM succ s WHERE s.parent = o.slug)
        )""" if t.has_col("work_discharge") else "")
    sql = f"""
    WITH RECURSIVE
      opens AS (SELECT work_slug AS slug FROM {rel_cur} WHERE kind = 'work_opened'),
      succ AS (
        SELECT work_parent AS parent, work_slug AS child FROM {rel_cur}
        WHERE kind = 'work_opened' AND work_parent IS NOT NULL
        UNION ALL
        -- work_depends_on walked OPPOSITE its own column order -- see this function's docstring.
        SELECT work_slug AS parent, work_depends_on AS child FROM {rel_cur}
        WHERE kind = 'work_depends_on'
      ),
      tree(root, member) AS (
        SELECT slug, slug FROM opens
        UNION
        SELECT t.root, s.child FROM tree t JOIN succ s ON s.parent = t.member
      ),
      closes AS (
        SELECT work_slug AS slug, id AS rid, actor AS closer, work_review_disposition AS disp
        FROM {rel_cur} WHERE kind = 'work_closed'
      ),
      discharged AS (
        SELECT c.rid FROM closes c
        WHERE EXISTS (
          SELECT 1 FROM {rel} r JOIN {t.rel("review_detail")} rd ON rd.ledger_id = r.id
          WHERE r.kind = 'review' AND r.regards = c.rid AND rd.verdict = 'attest' AND r.actor <> c.closer
            AND NOT EXISTS (SELECT 1 FROM {rel} s2 WHERE s2.supersedes = r.id)
        )
      ),
      own_unresolved AS (
        SELECT c.slug FROM closes c
        WHERE c.disp = 'deferred' AND c.rid NOT IN (SELECT rid FROM discharged)
      ),
      not_closed AS (
        SELECT o.slug FROM opens o
        WHERE NOT EXISTS (SELECT 1 FROM closes c WHERE c.slug = o.slug)
        {composite_exempt}
      )
    SELECT 'w_tree_member(' || {q_root} || ',' || {q_member} || ')' FROM tree t
    UNION ALL SELECT 'w_own_leaf_unresolved(' || {q_slug} || ')' FROM own_unresolved
    UNION ALL
      SELECT DISTINCT 'w_tree_unresolved(' || {_wi_quote("t.root")} || ')'
      FROM tree t
      WHERE t.member IN (SELECT slug FROM own_unresolved)
         OR (t.member <> t.root AND t.member IN (SELECT slug FROM not_closed))
    ;"""
    out = t.run(sql).stdout
    return {line.strip() for line in out.splitlines() if line.strip()}


# ===========================================================================
# THE DEFEAT-LAYER floor (design/FABLE-DEFEAT-PIPELINE-SPEC.md §6): the SQL twin of
# engine/lp/ledger_defeat.lp, independently derived (NO shared code path with clingo, and no
# shared code path with engine/ledger_edb.py::export_defeat's own v1 parser either -- the
# floor re-reads the database directly and re-derives everything, including its own v1
# statement parse in SQL, matching work_item_floor_atoms' `_wi_quote` precedent). Bit-identity
# between the two producers is the gate; a shared parser would launder it.
DEFEAT_PREDS = ("model_defeated", "credited", "exposure_model", "exposure_model_undischarged")


def defeat_manifest(name: str) -> dict[str, str]:
    """The capability manifest for the defeat layer on `name` (§4.3/§14, F49). A pre-s41 target
    (no principal_binding_active/principal_competence_activity columns) has NO grant substrate
    -- the whole layer is capability-EXCLUDED, never a silent record-empty."""
    t = resolve(name)
    has_grant = t.has_col("principal_binding_active") and t.has_col("principal_competence_activity")
    has_affirm = t.has_relation(f"{t.schema}.support_affirm")
    m: dict[str, str] = {}
    if not has_grant:
        for fam in DEFEAT_PREDS:
            m[fam] = ("EXCLUDED (no principal_binding_active/principal_competence_activity "
                      "columns on this schema, pre-s41 lineage -- capability absent, not "
                      "record-empty)")
        return m
    for fam in ("model_defeated", "credited"):
        m[fam] = "PRODUCED (basis: mismatch attestation + in-force trust grant closure)"
    m["exposure_model"] = "PRODUCED (basis: model_defeated + the existing support_star closure)"
    m["exposure_model_undischarged"] = (
        "PRODUCED (basis: exposure_model + support_affirm EDB, scratch-only per ledger_support.lp "
        "§3 Ruling A)" if has_affirm else
        "DEFERRED (no support_affirm source on this target -- exposure_model_undischarged equals "
        "exposure_model, said here, never silently, per spec §14)")
    return m


def defeat_floor_atoms(name: str) -> set[str]:
    """The set of defeat-layer atoms the SQL floor derives for `name` (read-only). Every shown
    atom is all-integer (model_defeated(R,A,G), credited(R), exposure_model(F,D),
    exposure_model_undischarged(F,D)) -- no text crosses, so no quoting branch exists to diverge
    (the `_wi_quote` hazard class is structurally absent here). Raises (a SQL-side error,
    propagated as a subprocess failure) on a malformed v1 attestation statement (§3 P-5) --
    the caller (engine/ledger_differential.py's defeat-layer arm) catches this and QUARANTINES,
    exactly as the ASP-side export_defeat()'s DefeatParseError is caught -- "both producers fail
    identically" (§3 P-5), independently derived."""
    t = resolve(name)
    rel = t.rel()
    has_grant = t.has_col("principal_binding_active") and t.has_col("principal_competence_activity")
    if not has_grant:
        return set()  # capability-absent; the caller's require()-equivalent refuses BEFORE this
    has_amends = t.has_col("amends")
    has_answers = t.has_col("answers")
    has_statement = t.has_col("statement")
    has_typed = t.has_col("attest_row_id")
    has_affirm = t.has_relation(f"{t.schema}.support_affirm")
    has_assumes = t.has_relation(f"{t.schema}.support_assumes")

    amends_cte = (f"SELECT id AS a, amends AS t FROM {rel} WHERE amends IS NOT NULL"
                  if has_amends else "SELECT NULL::bigint AS a, NULL::bigint AS t WHERE false")
    answers_cte = (f"SELECT id AS a, answers AS q FROM {rel} WHERE answers IS NOT NULL"
                   if has_answers else "SELECT NULL::bigint AS a, NULL::bigint AS q WHERE false")
    affirm_cte = (f"SELECT r, dependent AS dep, antecedent AS ant FROM {t.schema}.support_affirm"
                  if has_affirm else
                  "SELECT NULL::bigint AS r, NULL::bigint AS dep, NULL::bigint AS ant WHERE false")
    assumes_cte = (f"SELECT assumption AS ant, scope AS dep FROM {t.schema}.support_assumes"
                   if has_assumes else "SELECT NULL::bigint AS ant, NULL::bigint AS dep WHERE false")

    # v1 statement parse (§6 clause 3, the pins of §3 P-1/P-2/P-4/P-5). Candidates: btrim(statement)
    # LIKE 'model-attestation %'; version gate: segment 1 = 'model-attestation v1'; a violated pin
    # RAISES via the sanctioned division-guard (§6: "a strict ::bigint cast ... plus explicit CASE
    # ... ELSE <raise via a division-guard>") -- CASE is short-circuit, so the guard fires ONLY on
    # the malformed branch, never on a well-formed row.
    v1_cte = (f"""
      v1_cand AS (
        SELECT id, btrim(statement) AS s FROM {rel} WHERE btrim(statement) LIKE 'model-attestation %'
      ),
      v1_seg AS (
        SELECT id, s,
          array_length(string_to_array(s, '|'), 1) AS nseg,
          btrim(split_part(s,'|',1)) AS seg1, btrim(split_part(s,'|',2)) AS seg2,
          btrim(split_part(s,'|',3)) AS seg3, btrim(split_part(s,'|',4)) AS seg4,
          btrim(split_part(s,'|',5)) AS seg5, btrim(split_part(s,'|',6)) AS seg6,
          btrim(split_part(s,'|',7)) AS seg7, btrim(split_part(s,'|',8)) AS seg8,
          btrim(split_part(s,'|',9)) AS seg9
        FROM v1_cand
      ),
      v1_rows AS (SELECT * FROM v1_seg WHERE seg1 = 'model-attestation v1'),
      v1_checked AS (
        SELECT id,
          -- P-5's loud refusal, the sanctioned division-guard (§6 clause 3). The divisor is
          -- data-dependent (a CASE over row columns), never a bare literal `1/0` -- Postgres'
          -- planner constant-folds a LITERAL divisor at parse time regardless of which CASE
          -- branch would run at execution time (a witnessed hazard, not a hypothetical one:
          -- `1/0` in the ELSE arm raised on every row, including well-formed ones, because the
          -- constant subexpression was folded before the CASE ever branched). Divisor 0 only
          -- when the row is malformed; 1 when well-formed -- so `1 / <divisor>` raises division
          -- by zero on exactly the malformed rows, never on a valid one.
          (1 / (CASE WHEN nseg = 9
                  AND seg2 LIKE 'row=%' AND seg3 LIKE 'model=%' AND seg4 LIKE 'grade=%'
                  AND seg5 LIKE 'expected=%' AND seg6 LIKE 'verdict=%' AND seg7 LIKE 'session=%'
                  AND seg8 LIKE 'basis=%' AND seg9 LIKE 'rebuttals=%'
                  AND substring(seg2 from 5) ~ '^-?[0-9]+$'
                  AND substring(seg4 from 7) IN ('exact-command','turn-bracketed','session-scoped','ambiguous')
                  AND substring(seg6 from 9) IN ('match','MISMATCH','unevaluated')
                THEN 1
                ELSE 0
           END)) AS ok,
          substring(seg2 from 5)::bigint AS attested_row,
          substring(seg6 from 9) AS verdict
        FROM v1_rows
      )"""
               if has_statement else
               "v1_checked AS (SELECT NULL::bigint AS id, NULL::int AS ok, "
               "NULL::bigint AS attested_row, NULL::text AS verdict WHERE false)")
    typed_any = (f"SELECT id FROM {rel} WHERE kind='model_identity_attested'"
                 if has_typed else "SELECT NULL::bigint AS id WHERE false")
    typed_mismatch = (f"SELECT id AS a_id, attest_row_id AS r_id FROM {rel} "
                      f"WHERE kind='model_identity_attested' AND attest_verdict='mismatch'"
                      if has_typed else "SELECT NULL::bigint AS a_id, NULL::bigint AS r_id WHERE false")

    sql = f"""
    WITH RECURSIVE{_base_ctes(rel, _enacts_cte(t), amends_cte, answers_cte)},
      {v1_cte},
      aff AS ({affirm_cte}),
      asm AS ({assumes_cte}),
      support_edge(dep, ant) AS (
        SELECT e, d FROM en
        UNION ALL SELECT a, q FROM ans
        UNION ALL SELECT dep, ant FROM asm
      ),
      support_star(f, d) AS (
        SELECT dep, ant FROM support_edge
        UNION
        SELECT ss.f, e.ant FROM support_star ss JOIN support_edge e ON e.dep = ss.d
      ),
      sod AS (SELECT DISTINCT a.r FROM aff a
              JOIN {rel} lr ON lr.id = a.r JOIN {rel} lf ON lf.id = a.dep
              WHERE lr.actor = lf.actor),
      affirmed AS (SELECT DISTINCT dep, ant FROM aff
                   WHERE r NOT IN (SELECT id FROM superseded) AND r NOT IN (SELECT r FROM sod)),
      attest_any AS (
        SELECT id AS a_id FROM v1_checked
        UNION SELECT id FROM ({typed_any}) tt
      ),
      mismatch AS (
        SELECT id AS a_id, attested_row AS r_id FROM v1_checked WHERE verdict = 'MISMATCH'
        UNION ALL
        SELECT a_id, r_id FROM ({typed_mismatch}) tm
      ),
      grants AS (
        SELECT id AS g, principal_subject AS p FROM {rel}
        WHERE kind = 'principal_competence_granted' AND principal_binding_active
          AND principal_competence_activity = 'model-identity-attestation'
      ),
      grant_any AS (SELECT id AS g FROM {rel} WHERE kind = 'principal_competence_granted'),
      -- note `ar.actor` is `row_actor` on the floor side (§6 clause 6).
      defeated AS (
        SELECT DISTINCT m.r_id, m.a_id, g.g
        FROM mismatch m
        JOIN {rel} ar ON ar.id = m.a_id
        JOIN grants g ON g.p = ar.actor
        WHERE m.a_id NOT IN (SELECT id FROM superseded)
          AND g.g NOT IN (SELECT id FROM superseded)
          AND m.r_id NOT IN (SELECT a_id FROM attest_any)
          AND m.r_id NOT IN (SELECT g FROM grant_any)
      ),
      credited AS (SELECT id FROM in_force WHERE id NOT IN (SELECT r_id FROM defeated)),
      exposure_model AS (
        SELECT DISTINCT ss.f, d.r_id AS d FROM support_star ss
        JOIN (SELECT DISTINCT r_id FROM defeated) d ON d.r_id = ss.d
        WHERE ss.f IN (SELECT id FROM in_force)
      ),
      exposure_model_undischarged AS (
        SELECT f, d FROM exposure_model EXCEPT SELECT dep, ant FROM affirmed
      )
    SELECT 'model_defeated('||r_id||','||a_id||','||g||')' FROM defeated
    UNION ALL SELECT 'credited('||id||')' FROM credited
    UNION ALL SELECT 'exposure_model('||f||','||d||')' FROM exposure_model
    UNION ALL SELECT 'exposure_model_undischarged('||f||','||d||')' FROM exposure_model_undischarged
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
