#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T20:16:55Z
#   last-change: 2026-07-15T20:16:55Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""column_complete_gate — the mechanical GATE half of the column-complete-view mechanism (work
item column-complete-gate, vestigial_documentation/design/ORCH-CATEGORICAL-REFACTOR-CONSULT-2026-07-15.md F2 / plan
step 5). Wraps tools/column_complete.py's catalog functor as a gate, following
gates/doc_tables.py's own precedent (a thin gate importing its tools/ single-home parser rather
than re-deriving the check): same tools-module-as-source-of-truth shape, same GATE-vs-REPORT
posture as gates/append_only_integrity.py (a live-DB check, host-resolved via
filing/pghost_resolve.py, never a baked-in host literal).

CLOSURE STATEMENT (ADR-0000 Rule 2a):
  - INVARIANT: for every view registered in tools/column_complete.REGISTRY, the view's live
    column set (name AND order, information_schema.columns.ordinal_position) equals its source
    table's live column set, in catalog order, MINUS the view's declared exclusions
    (tools.column_complete.ViewSpec.exclusions) -- no undeclared missing column, no undeclared
    extra column, no silent reorder.
  - QUANTIFICATION UNIVERSE: every view in the registry (as of this delta: `ledger_current`,
    `countersigned_in_force` — both sourced from `ledger`), checked against the schema named by
    `--schema` (or this deployment's own deployment.json). A view NOT in the registry is out of
    scope by construction (it never claimed to be column-complete); the registry itself is the
    enumerated universe, and a new column-complete view enters scope by being ADDED to
    tools/column_complete.REGISTRY, not by this gate re-discovering it.
  - DENOMINATION: one violation per (view, column) mismatch -- a missing column, an extra
    column, or an absent view/table are each reported by name, never rolled into a single
    pass/fail bit with no detail (the "teach-text names the missing/extra column" requirement).

MODE: this is a live-Postgres gate (like append_only_integrity.py, NOT like the file-scanning
gates such as doc_tables.py) -- it is not wired into the file-content pre-commit sweep, because
there is no file content to scan; it is invoked explicitly against a schema (a scratch world, a
live deployment) exactly as append_only_integrity.py already is. Its own seen-red proof
(seen-red/column-complete-gate/run_fixtures.py) is what exercises both polarities on a scratch
schema and banks the red evidence gates/fixture_census.py requires.

Usage:
    python3 gates/column_complete_gate.py [--host H] [--db D] --schema S [--view NAME]
Exit 0 if every registered view (or the one named by --view) is column-complete; exit 1 listing
every (view, missing/extra column) mismatch by name; exit 2 on a usage/connection error.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "filing"))
import pghost_resolve  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import column_complete  # noqa: E402  (tools/column_complete.py, the ONE home for the functor)


def check_registry(host: str, db: str, schema: str, registry: dict) -> list:
    """Run column_complete.diff_view for every (name, spec) in `registry`; return the list of
    failing column_complete.ColumnDiff (ok=False). `registry` is a parameter, not always the
    module-global REGISTRY, so a fixture can point this at a synthetic registry without mutating
    the real one (ADR-0004: no reach into shared global state for a test's own purposes)."""
    bad = []
    for name in sorted(registry):
        diff = column_complete.diff_view(host, db, schema, name, registry[name])
        if not diff.ok:
            bad.append(diff)
    return bad


def _teach(diff) -> str:
    if diff.table_absent:
        return f"{diff.view}: source table is ABSENT on this schema -- cannot check column-completeness"
    if diff.view_absent:
        return f"{diff.view}: the VIEW ITSELF is absent on this schema -- registered as column-complete but never created"
    parts = []
    if diff.missing:
        parts.append(f"MISSING column(s) {diff.missing} (present on the source table, not declared "
                      f"as an exclusion, absent from the view -- the s20-lesson class this gate exists "
                      f"to catch)")
    if diff.extra:
        parts.append(f"EXTRA column(s) {diff.extra} (present on the view, not on the source table -- "
                      f"an undeclared addition)")
    if not parts:
        parts.append("column SET matches but ORDER differs from catalog append order")
    return f"{diff.view}: " + "; ".join(parts)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default=None)
    ap.add_argument("--db", default="toy")
    ap.add_argument("--schema", default=None,
                     help="schema to check (defaults to this deployment.json's schema)")
    ap.add_argument("--view", default=None,
                     help="check only this registered view (default: every registered view)")
    a = ap.parse_args(argv)
    host = a.host or pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
    try:
        schema = column_complete._resolve_schema(a.schema)
    except SystemExit as e:
        print(f"# column-complete-gate ERROR — {e}", file=sys.stderr)
        return 2
    registry = column_complete.REGISTRY
    if a.view:
        if a.view not in registry:
            print(f"# column-complete-gate ERROR — {a.view!r} is not a registered column-complete "
                  f"view (registered: {sorted(registry)})", file=sys.stderr)
            return 2
        registry = {a.view: registry[a.view]}
    try:
        bad = check_registry(host, a.db, schema, registry)
    except column_complete.CatalogError as e:
        print(f"# column-complete-gate ERROR — {e}", file=sys.stderr)
        return 2
    if bad:
        for diff in bad:
            print(f"COLUMN-INCOMPLETE VIEW: {_teach(diff)}")
        print(f"# column-complete-gate FAIL — {len(bad)} registered view(s) do not match "
              f"their source table's catalog column set minus declared exclusions.")
        return 1
    print(f"# column-complete-gate PASS — all {len(registry)} registered view(s) on "
          f"{schema} carry exactly their source table's catalog columns minus declared exclusions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
