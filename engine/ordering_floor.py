#!/usr/bin/env python3
"""ordering_floor -- the SQL FLOOR of the ordering-violations verdicts (design/
ORCH-SPEC-RESOURCE-REGISTRY.md §6/§5 stage 2): producer ONE of the marriage differential
(engine/ordering_differential.py), computing the SAME judgment predicates as
engine/lp/ordering_violations.lp (close_before_dependency_discharged/violated,
conditional_precedence_discharged/violated, dependency_cycle, ordering_edge/edge_star,
ordering_undecidable_any, ordering_forced_undecidable, ordering_verdict) in Postgres SQL --
window/join/NOT-EXISTS logic plus one recursive CTE for the cycle closure, mirroring
engine/ledger_floor.py's own `work_item_floor_atoms` precedent (transitive closure over a
dependency edge set is SQL's home turf, per that module's own docstring).

INDEPENDENCE (I6, ADR-0000 INDEP; the SAME posture engine/preamble_floor.py's own docstring
states): this module RE-DERIVES from the live ledger directly -- a SEPARATE query text from
engine/ordering_edb.py's own SELECTs, and a SEPARATE, independent re-parse of the `constraint:`
statement grammar (SQL regexp functions here, Python `re` there) -- never calling into
ordering_edb.py's helpers. The shared input is the real ledger rows on disk; the derivation is
independent on both sides.

SCOPE MATCHES engine/lp/ordering_violations.lp EXACTLY (never more, never less -- an unfaithful
floor is worse than none). `excludes` rows are read (constraint_excludes_deferred is emitted for
completeness/parity with the EDB's own counts) but never checked, matching that program's own
named residue.

Read-only (DB SELECT only). Lazy imports banned (top-of-file only)."""
from __future__ import annotations

import sys

from ledger_edb import Target, resolve


def _quote(col: str) -> str:
    """A SQL expression quoting `col` (text) as a clingo double-quoted string term -- the local,
    independent mirror of clingo_run.quote_term / ledger_floor.py's own `_wi_quote` (deliberately
    a SEPARATE copy, not an import -- see this module's own docstring INDEPENDENCE section)."""
    return "('\"' || replace(replace(" + col + ", '\\', '\\\\'), '\"', '\\\"') || '\"')"


def _snapshot(t: Target, rel: str, curr_rel: str, has_work_cols: bool) -> str:
    """A text snapshot of the true rows this floor reads -- this producer's own honest input
    hash basis (mirrors engine/ledger_differential.py's own `_ledger_snapshot_hash`)."""
    work_cols = ("coalesce(work_slug,''), coalesce(work_resolution,''), coalesce(work_depends_on,'')"
                if has_work_cols else "'', '', ''")
    snap1 = t.run(f"SELECT id, kind, {work_cols} FROM {rel} ORDER BY id;").stdout
    snap2 = t.run(f"SELECT id, statement FROM {curr_rel} WHERE kind='decision' "
                 f"AND statement ~ '^[[:space:]]*constraint:' ORDER BY id;").stdout
    return "# ledger rows\n" + snap1 + "\n# constraint: rows\n" + snap2


def floor_atoms(name: str) -> tuple[set[str], str]:
    """The set of ordering-violations atoms the SQL floor derives for `name` (read-only), plus a
    canonical text snapshot of the true inputs consumed."""
    t = resolve(name)
    rel = t.rel()
    has_work_cols = t.has_col("work_slug")
    has_current = t.has_relation(f"{t.schema}.ledger_current")
    curr_rel = f"{t.schema}.ledger_current" if has_current else rel

    work_slug_expr = "coalesce(work_slug,'')" if has_work_cols else "''"
    work_res_expr = "coalesce(work_resolution,'')" if has_work_cols else "''"
    work_dep_expr = "coalesce(work_depends_on,'')" if has_work_cols else "''"
    row_cte = (f"SELECT id, kind, {work_slug_expr} AS work_slug, {work_res_expr} AS work_resolution, "
              f"{work_dep_expr} AS work_depends_on FROM {rel}")

    constraint_all_cte = (
        f"SELECT id, statement FROM {curr_rel} WHERE kind='decision' "
        f"AND statement ~ '^[[:space:]]*constraint:'")

    q_dependent, q_antecedent = _quote("dependent"), _quote("antecedent")
    q_f, q_d = _quote("f"), _quote("d")
    q_slug_a, q_slug_b = _quote("slug_a"), _quote("slug_b")

    sql = f"""
    WITH RECURSIVE
      row_all AS ({row_cte}),
      any_row AS (SELECT id FROM row_all),
      work_opened AS (SELECT work_slug AS slug, id FROM row_all WHERE kind='work_opened'),
      work_closed AS (SELECT work_slug AS slug, work_resolution AS resolution, id
                       FROM row_all WHERE kind='work_closed'),
      work_depends AS (SELECT work_slug AS dependent, work_depends_on AS antecedent, id
                        FROM row_all WHERE kind='work_depends_on'),

      -- ==== the constraint: grammar, re-parsed independently in SQL (see docstring) ==========
      constraint_all AS ({constraint_all_cte}),
      constraint_match AS (
        SELECT id,
          (regexp_match(statement, '^\\s*constraint:\\s*(\\S+)\\s+(.*)$'))[1] AS relation,
          (regexp_match(statement, '^\\s*constraint:\\s*(\\S+)\\s+(.*)$'))[2] AS rest
        FROM constraint_all
      ),
      constraint_basic_unparsed AS (SELECT id FROM constraint_match WHERE relation IS NULL),
      constraint_typed AS (SELECT id, relation, rest FROM constraint_match WHERE relation IS NOT NULL),
      constraint_bad_relation AS (
        SELECT id FROM constraint_typed WHERE relation NOT IN ('precedes','excludes')),
      constraint_ok AS (
        SELECT id, relation, rest FROM constraint_typed WHERE relation IN ('precedes','excludes')),
      constraint_slugs AS (
        SELECT cr.id, cr.relation, s.slug, s.ord
        FROM constraint_ok cr
        CROSS JOIN LATERAL regexp_split_to_table(btrim(cr.rest), '\\s+') WITH ORDINALITY AS s(slug, ord)
        WHERE btrim(cr.rest) <> ''
      ),
      constraint_slug_counts AS (SELECT id, relation, count(*) AS n FROM constraint_slugs GROUP BY id, relation),
      constraint_underflow AS (
        SELECT id FROM constraint_slug_counts WHERE n < 2
        UNION SELECT co.id FROM constraint_ok co WHERE btrim(co.rest) = ''
      ),
      constraint_unparsed AS (
        SELECT id FROM constraint_basic_unparsed
        UNION SELECT id FROM constraint_bad_relation
        UNION SELECT id FROM constraint_underflow
      ),
      constraint_precedes_edges AS (
        SELECT a.id, a.slug AS slug_a, b.slug AS slug_b
        FROM constraint_slugs a JOIN constraint_slugs b ON b.id = a.id AND b.ord = a.ord + 1
        WHERE a.relation = 'precedes' AND a.id IN (SELECT id FROM constraint_slug_counts WHERE n >= 2)
      ),
      constraint_excludes_deferred AS (
        SELECT DISTINCT id FROM constraint_slugs WHERE relation = 'excludes'
        AND id IN (SELECT id FROM constraint_slug_counts WHERE n >= 2)
      ),

      -- ==== 1: close_before_dependency ========================================================
      cbd_trigger AS (
        SELECT wd.id AS dep_row, wd.dependent, wd.antecedent, wc.id AS close_id
        FROM work_depends wd
        JOIN work_closed wc ON wc.slug = wd.dependent
        JOIN work_opened wo ON wo.slug = wd.antecedent
      ),
      cbd_discharged AS (
        SELECT ct.dep_row, ct.dependent, ct.antecedent FROM cbd_trigger ct
        JOIN work_closed ac ON ac.slug = ct.antecedent
        WHERE ac.id < ct.close_id
      ),
      cbd_violated AS (
        SELECT ct.dep_row, ct.dependent, ct.antecedent FROM cbd_trigger ct
        WHERE NOT EXISTS (SELECT 1 FROM cbd_discharged cd WHERE cd.dep_row = ct.dep_row
                          AND cd.dependent = ct.dependent AND cd.antecedent = ct.antecedent)
      ),

      -- ==== 2: conditional_precedence =========================================================
      cp_trigger AS (
        SELECT cpe.id AS row_id, cpe.slug_a, cpe.slug_b, wc.id AS close_b
        FROM constraint_precedes_edges cpe
        JOIN work_closed wc ON wc.slug = cpe.slug_b
      ),
      cp_discharged AS (
        SELECT ct.row_id, ct.slug_a, ct.slug_b FROM cp_trigger ct
        JOIN work_closed ac ON ac.slug = ct.slug_a
        WHERE ac.id < ct.close_b
      ),
      cp_violated AS (
        SELECT ct.row_id, ct.slug_a, ct.slug_b FROM cp_trigger ct
        WHERE NOT EXISTS (SELECT 1 FROM cp_discharged cd WHERE cd.row_id = ct.row_id
                          AND cd.slug_a = ct.slug_a AND cd.slug_b = ct.slug_b)
      ),

      -- ==== 3: dependency_cycle (re-derived, union of BOTH edge families) ====================
      ord_edge(f, d) AS (
        SELECT dependent, antecedent FROM work_depends
        UNION
        SELECT slug_b, slug_a FROM constraint_precedes_edges
      ),
      ord_star(f, d) AS (
        SELECT f, d FROM ord_edge
        UNION
        SELECT os.f, oe.d FROM ord_star os JOIN ord_edge oe ON oe.f = os.d
      ),
      ord_cycle AS (SELECT DISTINCT f FROM ord_star WHERE f = d)

    -- `any_row` is NOT emitted into the returned atom set: it is a pure EDB-source/grounding
    -- fact (engine/lp/ordering_violations.lp never #shows it either), used here only to gate the
    -- forced-undecidable WHERE clauses below -- comparing it across producers would be
    -- tautological (both read the SAME ledger rows), not a test of either derivation, matching
    -- engine/ordering_differential.py's own SCOPE section (never a raw EDB fact).
    SELECT 'cbd_trigger(' || dep_row || ',' || {q_dependent} || ',' || {q_antecedent}
        || ',' || close_id || ')' FROM cbd_trigger
    UNION ALL SELECT 'close_before_dependency_discharged(' || dep_row || ',' || {q_dependent}
        || ',' || {q_antecedent} || ')' FROM cbd_discharged
    UNION ALL SELECT 'close_before_dependency_violated(' || dep_row || ',' || {q_dependent}
        || ',' || {q_antecedent} || ')' FROM cbd_violated
    UNION ALL SELECT 'cp_trigger(' || row_id || ',' || {q_slug_a} || ',' || {q_slug_b} || ','
        || close_b || ')' FROM cp_trigger
    UNION ALL SELECT 'conditional_precedence_discharged(' || row_id || ',' || {q_slug_a} || ','
        || {q_slug_b} || ')' FROM cp_discharged
    UNION ALL SELECT 'conditional_precedence_violated(' || row_id || ',' || {q_slug_a} || ','
        || {q_slug_b} || ')' FROM cp_violated
    UNION ALL SELECT 'ordering_edge(' || {q_f} || ',' || {q_d} || ')' FROM ord_edge
    UNION ALL SELECT 'ordering_edge_star(' || {q_f} || ',' || {q_d} || ')' FROM ord_star
    UNION ALL SELECT 'dependency_cycle(' || {q_f} || ')' FROM ord_cycle
    UNION ALL SELECT 'ordering_undecidable_any(conditional_precedence)'
        WHERE EXISTS (SELECT 1 FROM constraint_unparsed)
    UNION ALL SELECT 'ordering_forced_undecidable(close_before_dependency,pre_s22)'
        WHERE NOT {"true" if has_work_cols else "false"} AND EXISTS (SELECT 1 FROM any_row)
    UNION ALL SELECT 'ordering_forced_undecidable(dependency_cycle,pre_s22)'
        WHERE NOT {"true" if has_work_cols else "false"} AND EXISTS (SELECT 1 FROM any_row)
    UNION ALL SELECT 'ordering_forced_undecidable(conditional_precedence,pre_s22)'
        WHERE NOT {"true" if has_work_cols else "false"}
        AND EXISTS (SELECT 1 FROM constraint_precedes_edges)
    ;"""
    out = t.run(sql).stdout
    atoms = {line.strip() for line in out.splitlines() if line.strip()}
    atoms |= _family_verdicts(atoms)
    snapshot = _snapshot(t, rel, curr_rel, has_work_cols)
    return atoms, snapshot


_FAMILIES = ("close_before_dependency", "conditional_precedence", "dependency_cycle")
_VIOLATED_PRED = {
    "close_before_dependency": "close_before_dependency_violated(",
    "conditional_precedence": "conditional_precedence_violated(",
    "dependency_cycle": "dependency_cycle(",
}
_DISCHARGED_PRED = {
    "close_before_dependency": "close_before_dependency_discharged(",
    "conditional_precedence": "conditional_precedence_discharged(",
}


def _family_verdicts(atoms: set[str]) -> set[str]:
    """The FAMILY-STRATUM verdict ladder (engine/lp/ordering_violations.lp's own priority),
    computed here as a final Python aggregation over this floor's OWN already-derived instance
    atoms -- NOT a second SQL re-derivation of the same four-way priority (the identical posture
    engine/preamble_floor.py's own `_family_verdicts` already takes, for the identical reason:
    the priority itself is pure set logic over atoms this module already produced independently
    of the ASP program)."""
    undecidable_conditional = any(a == "ordering_undecidable_any(conditional_precedence)" for a in atoms)
    forced = {a[len("ordering_forced_undecidable("):-1].split(",")[0]
             for a in atoms if a.startswith("ordering_forced_undecidable(")}
    out: set[str] = set()
    for fam in _FAMILIES:
        violated = any(a.startswith(_VIOLATED_PRED[fam]) for a in atoms)
        undecidable = undecidable_conditional if fam == "conditional_precedence" else False
        discharged = ((fam in _DISCHARGED_PRED and any(a.startswith(_DISCHARGED_PRED[fam]) for a in atoms))
                      or (fam == "dependency_cycle" and any(a.startswith("ordering_edge(") for a in atoms)
                          and not violated))
        if violated:
            out.add(f"ordering_verdict({fam},violated)")
        elif undecidable:
            out.add(f"ordering_verdict({fam},undecidable)")
        elif fam in forced:
            out.add(f"ordering_verdict({fam},undecidable)")
        elif discharged:
            out.add(f"ordering_verdict({fam},discharged)")
        else:
            out.add(f"ordering_verdict({fam},vacuous)")
    return out


def main(argv: list[str] | None = None) -> int:
    for name in (argv if argv is not None else sys.argv[1:]) or ["toy"]:
        atoms, _snap = floor_atoms(name)
        print(f"# ordering_floor(SQL) -- {name}: {len(atoms)} atoms")
        for a in sorted(atoms):
            print(f"  {a}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
