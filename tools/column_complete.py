#!/usr/bin/env python3
"""column_complete — the single home for the "column-complete view" catalog functor (work
item column-complete-gate, per vestigial_documentation/design/ORCH-CATEGORICAL-REFACTOR-CONSULT-2026-07-15.md F2 /
plan step 5). Wraps the s20 lesson's own re-issue idiom — "ledger_current +
countersigned_in_force GAIN the new column, APPENDED AT THE END" — as computed data instead
of a hand re-typed column list per delta.

THE HAZARD THIS CLOSES (F2, verbatim): `ledger_current`/`countersigned_in_force` are
re-issued in every one of the 15 kernel/lineage/ deltas that touches the `ledger` table's
column set; each re-issue hand-copies a now-30-plus-column list, and each delta's closure
statement hand-re-verifies the "NOT members" universe by eye. The repetition is FORCED by
Postgres (a `SELECT l.*` view freezes its column set at creation time — the defect s20 itself
closed), so it cannot be collapsed by writing `l.*` instead. What CAN be collapsed is the
AUTHORING MORPHISM: "append column c to the table" -> "the column list every column-complete
view must carry" is a functor computable from the catalog (`information_schema.columns`) plus
one declared fact per view: which columns are DELIBERATELY absent, and why (the "declared
exclusion manifest" F2 names). Today that manifest is empty for both registered views — every
column ledger has ever grown, `ledger_current`/`countersigned_in_force` have carried, in
order, from the day it was added. The manifest exists so a FUTURE view can declare a real
exclusion instead of one more silent gap (ADR-0000 Rule 2a's "named, not silent" bar).

WHAT THIS MODULE OWNS (ADR-0012 P1 — one home):
  - REGISTRY: the set of "column-complete" views, each naming its source table, its FROM-alias,
    its declared exclusions (name -> reason), and its TAIL TEMPLATE (the FROM/WHERE/security
    clause below the SELECT list). The tail is NOT catalog-derivable — it is the view's actual
    business logic (which rows count as "in force", "countersigned") and has been byte-identical
    across every re-issue s22 through s30 (verified by reading the frozen lineage files). It is
    captured here as DECLARED TEXT, current as of s30, and is the one piece of this mechanism
    that is NOT computed — a delta that changes a column-complete view's semantics (not just its
    column set) must update this template alongside the kernel change, exactly as it already
    updates the WHERE clause by hand today. That is stated here, not hidden (ADR-0011 Rule 1):
    this module mechanizes the COLUMN-LIST functor only, per F2's own scoping ("the abstraction
    ladder... cannot state once in SQL... the column-complete re-issue (generator + detect gate)").
  - The catalog introspection (`table_columns`, `view_columns`) — one psql-shelling implementation,
    reused by both the generator CLI below and gates/column_complete_gate.py (which imports this
    module rather than re-deriving the query, mirroring gates/doc_tables.py importing
    tools/markdown_tables.py).
  - `expected_columns()` — the functor itself: table columns, in catalog (ordinal_position, i.e.
    append-at-end) order, minus the view's declared exclusions. This is the ONE definition of
    "what a column-complete view's column set must be"; the gate and the generator both call it,
    so they cannot silently drift from each other.
  - `generate_ddl()` — the authoring aid. Given a LIVE OR SCRATCH schema connection, emits the
    re-issue `CREATE OR REPLACE VIEW` text for a registered view, ready to paste into the NEXT
    kernel/lineage/sNN-*.sql delta. It reads the catalog; it NEVER applies anything itself, and
    it never touches a frozen kernel/lineage/sNN file (ADR-0005 Rule 8) — this module has no
    write path to kernel/lineage/ anywhere in it.

DETERMINISM: `expected_columns()` orders strictly by `information_schema.columns.ordinal_position`
(Postgres's own catalog order, which is append-only for a table that has only ever grown via
`ALTER TABLE ... ADD COLUMN` — every kernel/lineage/ delta to date). Two runs against the same
schema state always emit byte-identical output; this is the "byte-stable ordering" the commission
asked for, and it holds BY CONSTRUCTION (Postgres's own attnum ordering), not by a sort key this
module invents.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "filing"))
import pghost_resolve  # noqa: E402  (filing/pghost_resolve.py, the ONE home for host resolution)
import deployment_record  # noqa: E402  (filing/deployment_record.py, the ONE home for the deployment.json shape)


@dataclass(frozen=True)
class ViewSpec:
    """One registered column-complete view. `exclusions` maps an excluded column name to the
    declared reason it is deliberately absent (F2's "declared exclusion manifest") — empty for
    both views registered below, since neither has ever excluded a column; the field exists so a
    future view CAN declare one instead of silently diverging from the table."""
    source_table: str
    alias: str
    exclusions: dict = field(default_factory=dict)
    tail_template: str = ""  # the FROM/WHERE/options clause below the SELECT list; declared text,
                              # not catalog-derived (see module docstring)


# The registry (F2's "any view registered as column-complete"). Both entries' tail_template is
# transcribed verbatim from kernel/lineage/s30-typed-dependency-edges.sql:445-458 (the latest
# re-issue as of this writing) — read there to re-verify byte-for-byte if this module is ever
# suspected stale.
REGISTRY: dict = {
    "ledger_current": ViewSpec(
        source_table="ledger",
        alias="l",
        exclusions={},
        tail_template=(
            'FROM   :"schema".ledger l\n'
            "WHERE  NOT EXISTS (SELECT 1 FROM :\"schema\".ledger s WHERE s.supersedes = l.id);"
        ),
    ),
    "countersigned_in_force": ViewSpec(
        source_table="ledger",
        alias="l",
        exclusions={},
        tail_template=(
            'FROM   :"schema".ledger l\n'
            "WHERE  NOT EXISTS (SELECT 1 FROM :\"schema\".ledger s WHERE s.supersedes = l.id)\n"
            "AND    EXISTS (SELECT 1 FROM :\"schema\".ledger r JOIN :\"schema\".review_detail d "
            "ON d.ledger_id = r.id\n"
            "               WHERE r.kind = 'review' AND r.regards = l.id AND d.verdict = 'attest'\n"
            "               AND NOT EXISTS (SELECT 1 FROM :\"schema\".ledger s2 "
            "WHERE s2.supersedes = r.id));"
        ),
    ),
}


class CatalogError(RuntimeError):
    pass


def _psql_tuples(host: str, db: str, sql: str) -> list:
    """Run one SQL statement via psql -tAq -F'|', return its output rows as pipe-split lists.
    Raises CatalogError (never a silent empty result) on any non-zero psql exit."""
    cp = subprocess.run(
        ["psql", "-h", host, "-d", db, "-tAq", "-F", "|", "-v", "ON_ERROR_STOP=1", "-c", sql],
        capture_output=True, text=True, timeout=30,
    )
    if cp.returncode != 0:
        raise CatalogError(f"psql query failed: {cp.stderr.strip()[-400:]}")
    return [line.split("|") for line in cp.stdout.splitlines() if line != ""]


def table_columns(host: str, db: str, schema: str, table: str) -> list:
    """Every column of schema.table, in catalog (append-at-end) order. Empty list means the
    table does not exist OR genuinely has no columns — callers that need to distinguish those
    should check table existence separately; this function never raises for an absent table."""
    rows = _psql_tuples(
        host, db,
        "SELECT column_name FROM information_schema.columns "
        f"WHERE table_schema = '{schema}' AND table_name = '{table}' "
        "ORDER BY ordinal_position;",
    )
    return [r[0] for r in rows]


def view_columns(host: str, db: str, schema: str, view: str) -> list:
    """Every column of schema.view, in catalog (SELECT-list) order. Empty list means the view
    does not exist OR genuinely has no columns; same non-raising contract as table_columns."""
    rows = _psql_tuples(
        host, db,
        "SELECT column_name FROM information_schema.columns "
        f"WHERE table_schema = '{schema}' AND table_name = '{view}' "
        "ORDER BY ordinal_position;",
    )
    return [r[0] for r in rows]


def relation_exists(host: str, db: str, schema: str, name: str) -> bool:
    rows = _psql_tuples(
        host, db,
        "SELECT 1 FROM information_schema.tables "
        f"WHERE table_schema = '{schema}' AND table_name = '{name}';",
    )
    return len(rows) > 0


def expected_columns(table_cols: list, spec: ViewSpec) -> list:
    """THE FUNCTOR (F2): table columns, catalog order, minus this view's declared exclusions.
    The single definition both the gate and the generator call — neither re-derives it."""
    return [c for c in table_cols if c not in spec.exclusions]


@dataclass(frozen=True)
class ColumnDiff:
    view: str
    ok: bool
    missing: list      # in expected (table minus exclusions), absent from the live view
    extra: list         # in the live view, not in expected (an undeclared addition)
    view_absent: bool   # the view itself does not exist on this schema
    table_absent: bool  # the source table does not exist on this schema


def diff_view(host: str, db: str, schema: str, view_name: str, spec: ViewSpec) -> ColumnDiff:
    """Compute the live mismatch (if any) between a registered view's actual columns and its
    catalog-computed expected columns. Order-sensitive: `missing`/`extra` are set differences,
    reported in expected-order / actual-order respectively, so a reorder (not just an add/drop)
    is visible in the teach-text even though it would not change the two sets alone -- callers
    that want a strict order check compare `expected` against the raw `view_columns()` list."""
    table_absent = not relation_exists(host, db, schema, spec.source_table)
    view_absent = not relation_exists(host, db, schema, view_name)
    if table_absent or view_absent:
        return ColumnDiff(view=view_name, ok=False, missing=[], extra=[],
                           view_absent=view_absent, table_absent=table_absent)
    tcols = table_columns(host, db, schema, spec.source_table)
    expected = expected_columns(tcols, spec)
    actual = view_columns(host, db, schema, view_name)
    missing = [c for c in expected if c not in actual]
    extra = [c for c in actual if c not in expected]
    order_ok = [c for c in actual if c in expected] == expected
    return ColumnDiff(view=view_name, ok=(not missing and not extra and order_ok),
                       missing=missing, extra=extra, view_absent=False, table_absent=False)


def generate_ddl(host: str, db: str, schema: str, view_name: str, spec: ViewSpec) -> str:
    """THE GENERATOR (an authoring aid only — never applies anything, never touches a frozen
    kernel/lineage/sNN file). Emits the re-issue `CREATE OR REPLACE VIEW` text for `view_name`,
    column list computed from the LIVE catalog via `expected_columns()`, tail taken from the
    view's declared (not catalog-derived) `tail_template`."""
    tcols = table_columns(host, db, schema, spec.source_table)
    if not tcols:
        raise CatalogError(f"{schema}.{spec.source_table}: no columns found (table absent?) — "
                            f"cannot generate {view_name}'s re-issue DDL")
    cols = expected_columns(tcols, spec)
    col_list = ",\n".join(f'       {spec.alias}.{c}' for c in cols)
    col_list = col_list[7:]  # de-indent the first line (it sits right after "SELECT ")
    header = f'CREATE OR REPLACE VIEW :"schema".{view_name}\n    WITH (security_invoker = true) AS'
    excl_note = ""
    if spec.exclusions:
        excl_note = "\n-- DECLARED EXCLUSIONS: " + "; ".join(
            f"{k} ({v})" for k, v in spec.exclusions.items())
    return f"{header}\nSELECT {col_list}\n{spec.tail_template}{excl_note}\n"


def _resolve_schema(explicit: str) -> str:
    if explicit:
        # ADR-0012 interpreter-boundary amendment: this value is spliced directly into SQL text
        # by table_columns/view_columns/relation_exists below (an f-string, no bound carrier
        # available for a schema-name literal), so it is validated to the SAME closed alphabet
        # every DeploymentRecord.schema already is -- deployment_record.py's ONE home for the
        # check, not a second regex grown here (ADR-0012 P1). An explicit --schema bypasses
        # DeploymentRecord entirely (it never goes through load_deployment), so without this call
        # this one path would stay unguarded even after the fix at the one home.
        deployment_record.validate_sql_identifier("schema", explicit)
        return explicit
    dep_path = Path(os.environ.get("LEDGER_DEPLOYMENT",
                                    str(Path(__file__).resolve().parents[1] / "deployment.json")))
    if dep_path.is_file():
        return deployment_record.load_deployment(dep_path).schema
    raise SystemExit("REFUSED: no --schema given and no deployment.json found -- pass --schema "
                      "explicitly (e.g. a scratch world's schema name).")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Authoring aid: emit the catalog-computed re-issue DDL for every registered "
                     "column-complete view (or one named view), against a live/scratch schema. "
                     "Never applies anything; never touches kernel/lineage/.")
    ap.add_argument("--host", default=None)
    ap.add_argument("--db", default="toy")
    ap.add_argument("--schema", default=None,
                     help="schema to introspect (defaults to this deployment.json's schema)")
    ap.add_argument("--view", default=None,
                     help="emit only this registered view (default: every registered view)")
    a = ap.parse_args(argv)
    host = a.host or pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
    try:
        schema = _resolve_schema(a.schema)
    except deployment_record.DeploymentError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    names = [a.view] if a.view else sorted(REGISTRY)
    if a.view and a.view not in REGISTRY:
        print(f"REFUSED: {a.view!r} is not a registered column-complete view "
              f"(registered: {sorted(REGISTRY)})", file=sys.stderr)
        return 2
    try:
        for name in names:
            print(f"-- generated by tools/column_complete.py against {schema} on {host}/{a.db} "
                  f"-- paste into the next kernel/lineage/sNN-*.sql delta; verify against "
                  f"gates/column_complete_gate.py before shipping.")
            print(generate_ddl(host, a.db, schema, name, REGISTRY[name]))
    except CatalogError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
