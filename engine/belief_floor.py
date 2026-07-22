#!/usr/bin/env python3
"""belief_floor -- the SQL FLOOR of the v1 belief-substrate judgments (design/
FABLE-BELIEF-SUBSTRATE-SPEC.md §2-§3.4, ratified ledger rows 1914/1919): producer ONE of the
belief-layer differential, a SEPARATE sibling of engine/ledger_floor.py per spec §2.2 item 2.
Computes the SAME judgment predicates as engine/lp/ledger_belief.lp (contested_belief/2,
contest_resolved/2, credited_belief/1, corroboration_grade/2, shared_ancestor/3), read-only,
as clingo-shaped ATOM STRINGS so engine/ledger_differential.py compares the two by set-equality.

INDEPENDENCE (I6, the export_defeat/defeat_floor_atoms precedent): shares NO code path with
clingo, AND none with engine/belief_edb.py's own v1 parser -- it re-derives the ENTIRE grammar
parse independently, in SQL, via its own regex (_BELIEF_PATTERN below), authored fresh in
Postgres ARE syntax rather than transcribed from the Python `re` pattern. ONE `regexp_match`
call per candidate row extracts every field in canonical order; an out-of-order or unrecognized
field fails the match (NULL), mirroring the Python parser's single-pass consumption -- verified
live against psql (see the build report) rejecting an out-of-order candidate the same way.

NAMED DEVIATION FROM THE "RECURSIVE CTE" IDIOM (reported, not silently chosen). Belief
WELL-FOUNDEDNESS is an AND-type (conjunctive, "every premise founded") fixpoint over
belief_edge(_,premise,_); Postgres forbids a recursive CTE's self-reference inside a NOT
EXISTS/aggregate subquery, which universal quantification over premises structurally needs --
no single recursive CTE expresses it (a real SQL limitation, not a preference), unlike
ledger_floor.py's OR-type edge closures (sup_star/support_star). This floor computes the
well-founded closure via an explicit Python fixpoint loop driving ONLY raw, independently-parsed
SQL facts -- no clingo, no shared parser -- the same "SQL facts, Python-side monotone closure"
shape ledger_edb.py's own supersession-transitive-closure already uses for the identical reason.
Still "the SQL floor": every fact and validity check is SQL-derived; only the fixpoint driver
is Python, exactly as for the EDB producer's own supersession math.

Read-only. Reuses `ledger_floor._base_ctes`/`_enacts_cte` (supersession/in-force, SQL-to-SQL, I6
unaffected) and `ledger_floor.defeat_floor_atoms` (model-identity defeat, parallel composition
with `ledger_belief.lp`'s own `ledger_defeat.lp` composition). v2 typed arm (s53) split into
engine/belief_floor_typed.py (ADR-0007 headroom, reported not silent).

Lazy imports are banned (CLAUDE.md)."""
from __future__ import annotations

import sys

from belief_floor_typed import typed_arm_rows
from ledger_edb import Target, resolve
from ledger_floor import _base_ctes, _enacts_cte, defeat_floor_atoms
from ledger_floor import floor_atoms as _tnow_floor_atoms

BELIEF_PREDS = ("contested_belief", "contest_resolved", "credited_belief",
               "corroboration_grade", "shared_ancestor")

# The single regex extracting every v1 belief field in ONE `regexp_match` call, in the SAME
# canonical field order engine/ledger_edb.py's Python parser enforces via sequential
# consumption -- an out-of-order or unrecognized field fails the WHOLE match (NULL), never a
# partial parse. Independently authored (not copied from the Python `re` pattern; POSIX ARE's
# `(?:...)` non-capturing-group syntax is used here, absent from the Python module).
_BELIEF_PATTERN = (
    r'^belief\[(universal|existential)\]\s*basis=(observed|derived|testimony|assumed)'
    r'(?:\s+universe=\{([^}]*)\})?'
    r'(?:\s+witness=(\S+))?'
    r'(?:\s+source=(\S+))?'
    r'(?:\s+premises=(\S+))?'
    r'(?:\s+subject=(\S+))?'
    r'(?:\s+contests=(\S+))?'
    r'(?:\s+concurs=(\S+))?'
    r'\s*::\s*(.+)$'
)


def _bad_universe_tokens(expr: str, rel: str, artifact_rel: str, has_artifact: bool) -> str:
    """TRUE iff `expr` (semicolon-separated) has a row:/artifact: shaped token that doesn't
    exist. Free-text tokens are always legal (a universe names territory, not only rows)."""
    artifact_leg = (f"(btrim(tok.v) ~ '^artifact:[0-9a-f]{{64}}$' AND NOT EXISTS "
                    f"(SELECT 1 FROM {artifact_rel} ax WHERE ax.hash = substring(btrim(tok.v) from 10)))"
                    if has_artifact else
                    "(btrim(tok.v) ~ '^artifact:[0-9a-f]{64}$')")  # no store -> every artifact: token is dangling
    return (f"EXISTS (SELECT 1 FROM unnest(string_to_array(coalesce({expr},''), ';')) AS tok(v) "
            f"WHERE btrim(tok.v) <> '' AND ("
            f"(btrim(tok.v) ~ '^row:[0-9]+$' AND NOT EXISTS "
            f"(SELECT 1 FROM {rel} lx WHERE lx.id = (substring(btrim(tok.v) from 5))::bigint)) "
            f"OR {artifact_leg}))")


def _bad_strict_tokens(expr: str, rel: str, artifact_rel: str, has_artifact: bool,
                      allow_artifact: bool) -> str:
    """TRUE iff `expr` (comma-separated) has any token not a row:/artifact: shaped, existing
    reference (no free text -- witness/premises/source/subject/contests/concurs share this
    shape; `allow_artifact` gates whether artifact: is legal here -- only witness accepts it)."""
    if allow_artifact:
        shape = "(btrim(tok.v) ~ '^row:[0-9]+$' OR btrim(tok.v) ~ '^artifact:[0-9a-f]{64}$')"
        artifact_missing = (f"(btrim(tok.v) ~ '^artifact:[0-9a-f]{{64}}$' AND NOT EXISTS "
                            f"(SELECT 1 FROM {artifact_rel} ax WHERE ax.hash = substring(btrim(tok.v) from 10)))"
                            if has_artifact else "(btrim(tok.v) ~ '^artifact:[0-9a-f]{64}$')")
        exist_bad = (f"(btrim(tok.v) ~ '^row:[0-9]+$' AND NOT EXISTS "
                    f"(SELECT 1 FROM {rel} lx WHERE lx.id = (substring(btrim(tok.v) from 5))::bigint)) "
                    f"OR {artifact_missing}")
    else:
        shape = "(btrim(tok.v) ~ '^row:[0-9]+$')"
        exist_bad = (f"(NOT EXISTS (SELECT 1 FROM {rel} lx "
                    f"WHERE lx.id = (substring(btrim(tok.v) from 5))::bigint))")
    return (f"EXISTS (SELECT 1 FROM unnest(string_to_array(coalesce({expr},''), ',')) AS tok(v) "
            f"WHERE btrim(tok.v) <> '' AND (NOT {shape} OR {exist_bad}))")


def _bad_edge_tokens(expr: str, rel: str, cand_cte: str, superseded_cte: str, actor_col: str) -> str:
    """TRUE iff `expr` fails contest/concurs's cross-row semantics (spec §3.2 item 2/3): must
    exist, be a belief candidate (`belief[` prefix), be UNSUPERSEDED, carry a DIFFERENT actor."""
    return (f"EXISTS (SELECT 1 FROM unnest(string_to_array(coalesce({expr},''), ',')) AS tok(v) "
            f"WHERE btrim(tok.v) <> '' AND ("
            f"btrim(tok.v) !~ '^row:[0-9]+$' "
            f"OR NOT EXISTS (SELECT 1 FROM {rel} lx WHERE lx.id = (substring(btrim(tok.v) from 5))::bigint) "
            f"OR NOT EXISTS (SELECT 1 FROM {cand_cte} c WHERE c.id = (substring(btrim(tok.v) from 5))::bigint) "
            f"OR EXISTS (SELECT 1 FROM {superseded_cte} sup WHERE sup.id = (substring(btrim(tok.v) from 5))::bigint) "
            f"OR EXISTS (SELECT 1 FROM {rel} lr WHERE lr.id = (substring(btrim(tok.v) from 5))::bigint "
            f"AND lr.actor = {actor_col})))")


def _parse_and_validate(t: Target) -> list[tuple]:
    """SQL-side parse + obligation/token/edge validation for every v1 belief candidate on `t`,
    forcing a division-by-zero raise (the defeat_floor_atoms idiom) on the first malformed
    candidate. Returns one tuple per well-formed belief: (id, actor, polarity, basis,
    has_universe, has_witness, premises_raw, source_raw, subject_raw, contests_raw, concurs_raw)."""
    rel = t.rel()
    has_artifact = t.has_relation(f"{t.kern}.artifact")
    artifact_rel = f"{t.kern}.artifact"
    universe_bad = _bad_universe_tokens("o.universe_raw", rel, artifact_rel, has_artifact)
    witness_bad = _bad_strict_tokens("o.witness_raw", rel, artifact_rel, has_artifact, allow_artifact=True)
    premises_bad = _bad_strict_tokens("o.premises_raw", rel, artifact_rel, has_artifact, allow_artifact=False)
    source_bad = _bad_strict_tokens("o.source_raw", rel, artifact_rel, has_artifact, allow_artifact=False)
    subject_bad = _bad_strict_tokens("o.subject_raw", rel, artifact_rel, has_artifact, allow_artifact=False)
    contests_bad = _bad_edge_tokens("o.contests_raw", rel, "cand", "superseded", "o.actor")
    concurs_bad = _bad_edge_tokens("o.concurs_raw", rel, "cand", "superseded", "o.actor")
    # cardinality-1 checks (source/subject/contests/concurs are a SINGLE row:<id>, unlike
    # witness/premises' comma-lists -- the same rule ledger_edb.py's Python parser enforces).
    card1 = lambda expr: (  # noqa: E731 -- a tiny local helper, not worth a def for one call site
        f"(({expr}) IS NOT NULL AND array_length(string_to_array(btrim({expr}), ','), 1) <> 1)")

    is_array = t.scalar(
        f"SELECT data_type FROM information_schema.columns WHERE table_schema='{t.schema}' "
        f"AND table_name='ledger' AND column_name='enacts';") == "ARRAY"
    amends_cte = (f"SELECT id AS a, amends AS tgt FROM {rel} WHERE amends IS NOT NULL"
                 if t.has_col("amends") else "SELECT NULL::bigint AS a, NULL::bigint AS tgt WHERE false")
    answers_cte = (f"SELECT id AS a, answers AS q FROM {rel} WHERE answers IS NOT NULL"
                  if t.has_col("answers") else "SELECT NULL::bigint AS a, NULL::bigint AS q WHERE false")

    sql = f"""
    WITH RECURSIVE{_base_ctes(rel, _enacts_cte(t), amends_cte, answers_cte)},
      cand AS (SELECT id, actor, btrim(statement) AS s FROM {rel} WHERE btrim(statement) LIKE 'belief[%'),
      parsed AS (SELECT id, actor, s, regexp_match(s, '{_BELIEF_PATTERN}') AS m FROM cand),
      extracted AS (
        SELECT id, actor,
          m[1] AS polarity, m[2] AS basis, m[3] AS universe_raw, m[4] AS witness_raw,
          m[5] AS source_raw, m[6] AS premises_raw, m[7] AS subject_raw,
          m[8] AS contests_raw, m[9] AS concurs_raw, m[10] AS proposition,
          (m IS NOT NULL) AS header_ok
        FROM parsed
      ),
      o AS (
        SELECT *,
          (CASE
             WHEN NOT header_ok THEN false
             WHEN polarity = 'universal' THEN
               (universe_raw IS NOT NULL AND btrim(universe_raw) <> '') AND witness_raw IS NULL
             WHEN polarity = 'existential' THEN
               universe_raw IS NULL AND
               (basis <> 'observed' OR (witness_raw IS NOT NULL AND btrim(witness_raw) <> ''))
             ELSE false
           END) AS polarity_ok,
          (CASE WHEN basis = 'testimony' THEN source_raw IS NOT NULL ELSE source_raw IS NULL END) AS source_ok,
          (CASE WHEN basis = 'derived'
                THEN (premises_raw IS NOT NULL AND btrim(premises_raw) <> '')
                ELSE premises_raw IS NULL END) AS premises_ok,
          (btrim(coalesce(proposition,'')) <> '') AS prop_ok
        FROM extracted
      )
    SELECT o.id, o.actor, o.polarity, o.basis,
      (o.universe_raw IS NOT NULL AND btrim(o.universe_raw) <> '') AS has_universe,
      (o.witness_raw IS NOT NULL AND btrim(o.witness_raw) <> '') AS has_witness,
      coalesce(o.premises_raw,''), coalesce(o.source_raw,''), coalesce(o.subject_raw,''),
      coalesce(o.contests_raw,''), coalesce(o.concurs_raw,''),
      (1 / (CASE WHEN o.header_ok AND o.polarity_ok AND o.source_ok AND o.premises_ok AND o.prop_ok
                     AND NOT ({universe_bad}) AND NOT ({witness_bad}) AND NOT ({premises_bad})
                     AND NOT ({source_bad}) AND NOT ({subject_bad})
                     AND NOT ({contests_bad}) AND NOT ({concurs_bad})
                     AND NOT {card1('o.source_raw')} AND NOT {card1('o.subject_raw')}
                     AND NOT {card1('o.contests_raw')} AND NOT {card1('o.concurs_raw')}
                THEN 1 ELSE 0 END)) AS guard
    FROM o
    ORDER BY o.id;
    """
    rows = t.rows(sql)
    out: list[tuple] = []
    for (rid, actor, polarity, basis, has_u, has_w, prem, src, subj, cont, conc, _guard) in rows:
        out.append((int(rid), int(actor) if actor else None, polarity, basis,
                   has_u == "t", has_w == "t", prem, src, subj, cont, conc))
    return out


def _ids(raw: str) -> list[int]:
    return [int(tok.strip()[4:]) for tok in raw.split(",") if tok.strip()]

def belief_capable(t: Target) -> bool:
    """The ONE home of the belief layer's capability test (I12) -- (statement, v1 arm, OR
    belief_polarity, s53 typed arm) + integer-typed actor. Mirrors belief_edb.py's gate."""
    has_actor = t.has_col("actor") and t.scalar(
        f"SELECT data_type FROM information_schema.columns WHERE table_schema='{t.schema}' "
        f"AND table_name='ledger' AND column_name='actor';") in ("bigint", "integer", "smallint")
    return (t.has_col("statement") or t.has_col("belief_polarity")) and has_actor


def belief_manifest(name: str) -> dict[str, str]:
    """The capability manifest for the belief layer on `name` (I12)."""
    capable = belief_capable(resolve(name))
    reason = ("PRODUCED (statement/belief_polarity + integer-typed actor)" if capable else
             "EXCLUDED (no statement/belief_polarity column, or actor not integer-typed)")
    return {fam: reason for fam in BELIEF_PREDS}


def belief_floor_atoms(name: str) -> set[str]:
    """The set of belief-layer atoms the SQL floor derives for `name` (read-only), BOTH arms
    combined (v1 + s53 typed, the s44 dual-arm precedent). Raises on a malformed v1 belief
    statement (caught by the caller, QUARANTINED); the typed arm never raises -- s53's kernel
    CHECKs/triggers already refused malformed rows at write time."""
    t = resolve(name)
    if not belief_capable(t):
        return set()  # capability-absent; the caller's require()-equivalent refuses BEFORE this
    rows: list[tuple] = []
    if t.has_col("statement"):
        rows += _parse_and_validate(t)  # raises on the first malformed candidate (SQL-side guard)
    if t.has_col("belief_polarity"):
        rows += typed_arm_rows(t)  # s53 typed arm -- write-time validated, no re-parse here

    # ---- in_force / superseded (SQL-derived, via the SAME base closure ledger_floor.py's other
    # floors share -- SQL-to-SQL reuse, not a clingo code path) ------------------------------
    tnow_atoms = _tnow_floor_atoms(name)
    in_force = {int(a[len("in_force("):-1]) for a in tnow_atoms if a.startswith("in_force(")}

    # ---- model-identity defeat (SQL-side, parallel composition with the defeat floor -- the
    # SAME composition ledger_belief.lp does on the ASP side via model_defeated_row/1) --------
    defeated_atoms = defeat_floor_atoms(name) if (
        t.has_col("principal_binding_active") and t.has_col("principal_competence_activity")) else set()
    model_defeated_row = set()
    for a in defeated_atoms:
        if a.startswith("model_defeated("):
            r_id = a[len("model_defeated("):].split(",", 1)[0]
            model_defeated_row.add(int(r_id))

    # ---- assemble typed per-belief records + edges ------------------------------------------
    belief_ids = {r[0] for r in rows}
    basis_of: dict[int, str] = {}; polarity_of: dict[int, str] = {}  # noqa: E702
    has_universe: dict[int, bool] = {}; has_witness: dict[int, bool] = {}  # noqa: E702
    premise_edges: dict[int, list[int]] = {}
    source_edge: dict[int, int] = {}
    contests_edge: dict[int, int] = {}
    concurs_edge: dict[int, int] = {}
    actor_of: dict[int, int] = {}
    for (rid, actor, polarity, basis, has_u, has_w, prem, src, subj, cont, conc) in rows:
        basis_of[rid], polarity_of[rid] = basis, polarity
        has_universe[rid], has_witness[rid] = has_u, has_w
        actor_of[rid] = actor
        if prem:
            premise_edges[rid] = _ids(prem)
        if src:
            ids = _ids(src)
            if ids:
                source_edge[rid] = ids[0]
        if cont:
            ids = _ids(cont)
            if ids:
                contests_edge[rid] = ids[0]
        if conc:
            ids = _ids(conc)
            if ids:
                concurs_edge[rid] = ids[0]

    # ---- contested_belief / contest_resolved / doubt (mirrors ledger_belief.lp exactly) -----
    basis_rank = {"observed": 4, "derived": 3, "testimony": 2, "assumed": 1}
    contested_belief: set[tuple[int, int]] = set()
    contest_resolved: set[tuple[int, int]] = set()
    doubt: set[int] = set()
    for c, tgt in contests_edge.items():
        if c in belief_ids and tgt in belief_ids and c in in_force and tgt in in_force:
            contested_belief.add((c, tgt))
            rc, rt = basis_rank[basis_of[c]], basis_rank[basis_of[tgt]]
            if rc > rt:
                contest_resolved.add((c, tgt))
                doubt.add(tgt)
            elif rt > rc:
                contest_resolved.add((tgt, c))
                doubt.add(c)
            else:
                doubt.add(c)
                doubt.add(tgt)

    # ---- well-foundedness fixpoint (the named Python-driven closure -- see module docstring) -
    grounded = {i for i in in_force if i not in belief_ids and i not in model_defeated_row}
    wellfounded: set[int] = set()
    for rid in belief_ids:
        if rid not in in_force or rid in doubt:
            continue
        basis, polarity = basis_of[rid], polarity_of[rid]
        if basis == "observed" and polarity == "existential" and has_witness.get(rid):
            wellfounded.add(rid)
        elif basis == "observed" and polarity == "universal" and has_universe.get(rid):
            wellfounded.add(rid)
    changed = True
    while changed:
        changed = False
        founded_nodes = grounded | wellfounded
        for rid in belief_ids:
            if rid in wellfounded or rid not in in_force or rid in doubt:
                continue
            basis = basis_of[rid]
            if basis == "derived":
                prem = premise_edges.get(rid, [])
                if prem and all(p in founded_nodes for p in prem):
                    wellfounded.add(rid)
                    changed = True
            elif basis == "testimony":
                src = source_edge.get(rid)
                if src is not None and src in founded_nodes:
                    wellfounded.add(rid)
                    changed = True
            # basis == "assumed": never well-founded, never credited (spec §3.4).

    credited_belief = wellfounded  # credited_belief(X) :- belief(X), belief_wellfounded(X).

    # ---- corroboration (concurrence-connected, SoD-distinct-by-parse-time-construction,
    # agent_class-diversity grade -- mirrors ledger_belief.lp's concur_pair/concur_class) ------
    concur_pair: set[tuple[int, int]] = set()
    for c, tgt in concurs_edge.items():
        if c in belief_ids and tgt in belief_ids and c in in_force and tgt in in_force:
            concur_pair.add((tgt, c))
            concur_pair.add((c, tgt))
    row_actor: dict[int, int] = {}
    for i, a in t.rows(f"SELECT id, actor FROM {t.rel()} WHERE actor IS NOT NULL ORDER BY id;"):
        row_actor[int(i)] = int(a)
    agent_class: dict[int, str] = {}
    if t.has_relation(f"{t.kern}.principal"):
        for pid, cls in t.rows(f"SELECT id, agent_class FROM {t.kern}.principal ORDER BY id;"):
            agent_class[int(pid)] = cls
    corroboration_grade: dict[int, str] = {}
    for x in credited_belief:
        classes = set()
        for (a, y) in ((a, y) for (a, y) in concur_pair if a == x):
            p = row_actor.get(y)
            if p is not None and p in agent_class:
                classes.add(agent_class[p])
        x_class = agent_class.get(row_actor.get(x))
        if not classes:
            corroboration_grade[x] = "uncorroborated"
        elif any(c != x_class for c in classes):
            corroboration_grade[x] = "corroborated-cross-class"
        else:
            corroboration_grade[x] = "corroborated-same-class"

    # ---- shared ancestor (premise/source transitive closure, per concurrence-connected pair) -
    ancestor: dict[int, set[int]] = {i: set() for i in belief_ids}
    changed = True
    while changed:
        changed = False
        for rid in belief_ids:
            direct = set(premise_edges.get(rid, [])) | ({source_edge[rid]} if rid in source_edge else set())
            new = set(direct)
            for a in list(ancestor[rid]):
                new |= set(premise_edges.get(a, [])) | ({source_edge[a]} if a in source_edge else set())
            if not new <= ancestor[rid]:
                ancestor[rid] |= new
                changed = True
    shared_ancestor: set[tuple[int, int, int]] = set()
    for (a, b) in {(a, b) for (a, b) in concur_pair if a < b}:
        for s in ancestor[a] & ancestor[b]:
            shared_ancestor.add((a, b, s))

    atoms: set[str] = set()
    for (c, tgt) in contested_belief:
        atoms.add(f"contested_belief({c},{tgt})")
    for (w, loser) in contest_resolved:
        atoms.add(f"contest_resolved({w},{loser})")
    for x in sorted(credited_belief):
        atoms.add(f"credited_belief({x})")
    for x, grade in corroboration_grade.items():
        atoms.add(f'corroboration_grade({x},"{grade}")')
    for (a, b, s) in shared_ancestor:
        atoms.add(f"shared_ancestor({a},{b},{s})")
    return atoms


def main(argv: list[str] | None = None) -> int:
    for name in (argv if argv is not None else sys.argv[1:]) or ["s10"]:
        atoms = belief_floor_atoms(name)
        print(f"# belief_floor(SQL) -- {name}: {len(atoms)} atoms")
        for a in sorted(atoms): print(f"  {a}")  # noqa: E701
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
