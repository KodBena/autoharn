#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-16T02:44:15Z
#   last-change: 2026-07-16T02:44:15Z
#   contributors: 9a17b6b9/main
# <<< PROVENANCE-STAMP <<<

"""export_precedence -- emit the ledger's IN-FORCE blocks-close precedence edges
(kernel/lineage/s30-typed-dependency-edges.sql's `edge_type='blocks-close'` work_depends_on rows)
in `tools/makespan-scheduler/`'s landed `depends_on` input format (scheduler commit 196030d,
"feat: add directed precedence constraints (depends_on)").

WHAT "blocks-close" MEANS HERE, AND WHY ONLY THAT EDGE TYPE. `led work depends <slug> <on-slug>
--type blocks-close` records that <on-slug> (the ANTECEDENT) must fully close before <slug> (the
DEPENDENT) may close -- a real "A before B" precondition, kernel-typed and validate_work_item()-
enforced (kernel/lineage/s30). `--type informs` records a merely advisory, non-enforced context
edge (led.tmpl's own default-type advisory: "informs -- advisory only -- never enforced at
close"). The scheduler's `depends_on` field means "A must fully complete before B may start" --
the same "must finish first" shape blocks-close carries and informs deliberately does not. Only
blocks-close is exported; informs edges are read and silently dropped (not an error -- an
advisory edge choosing to stay advisory is not a defect), so a caller cannot mistake "I typed an
edge" for "I typed a scheduling constraint."

WHY THIS FACTORS THROUGH work_edge_blocks_close + ledger_current, NEVER RAW `ledger` DIRECTLY
(this project's own kernel/lineage/s31-supersession-uniform-retraction.sql +
gates/ledger_reader_allowlist.py standing rule: every ledger reader is either a declared
CURRENT-TRUTH reader -- factors through `ledger_current`, no raw `ledger` reference -- or a
declared HISTORY/FORENSIC reader on the gate's own allowlist; this script is neither an allowlist
member nor exempt, so it must be the former). `work_edge_blocks_close` (kernel/lineage/
s32-edge-views-single-home.sql, ELEMENT 1b) is the single home of the RAW blocks-close edge
relation -- deliberately RAW (includes a retracted edge too), by that delta's own design, because
its other consumers are declared history readers. This script wants the IN-FORCE reading only (a
retracted `work_depends_on` row is not a live scheduling constraint), so it joins the raw view to
`ledger_current` on the edge's own carrying row itself -- EXACTLY the composition s32's own header
prescribes for a reader that "wants the in-force-only reading of either edge kind alone (not the
obligation-tree union)": "it would JOIN the raw view to ledger_current itself, exactly as
work_edge_obligation does internally. No such reader exists in this tree today" -- this script is
that reader, arriving after s32's own text was written; no fourth edge view is minted (s32's own
"no speculative generality" LIMITS note), this script performs the one-line join at its own call
site instead. `work_edge_obligation` itself is NOT used here -- it UNIONS the parent-edge and
blocks-close arms into one undifferentiated from_slug/to_slug pair, which would silently fold s28
parent/child structure into the precedence export; this script needs the blocks-close arm ALONE.

PRE-s30 / PRE-s32 REFUSAL (teach-text, never a silent empty export). Two capabilities are
required and checked independently, in the order a caller would apply them to their own kernel:
  1. `edge_type` column on `<schema>.ledger` (s30) -- absent means the deployment predates typed
     dependency edges entirely; every `work_depends_on` row on such a world is untyped (the
     historical shape led.tmpl's own pre-s30 INSERT path still writes), so "blocks-close" cannot
     even be asked of it.
  2. `<schema>.work_edge_blocks_close` view (s32) -- absent on a post-s30 world means s30 is
     applied but s32 (the single-homed edge views) is not; this script deliberately reads ONLY
     the s32 view (per the WHY above), never a hand-rolled second copy of s30's own
     `edge_type='blocks-close'` predicate over raw `ledger` (that would be exactly the
     ADR-0012 P1 two-writers drift s32 was built to collapse), so it refuses rather than
     re-deriving the predicate itself.
Both refusals name the missing kernel/lineage file and stop before issuing the edge query.

OUTPUT SHAPE: `{"jobs": [{"id": <slug>, "depends_on": [<slug>, ...]}, ...]}`, sorted by id for a
deterministic diff. Every slug that appears as either a dependent or an antecedent of an in-force
blocks-close edge is emitted as a job (so the scheduler never sees a `depends_on` entry naming an
unlisted id, its own `job <id>: depends_on references unknown job id` refusal). `resources` and
`duration` are deliberately OMITTED (default to `()`/`1` on the scheduler's own `Job` dataclass,
README.md "Input JSON") -- this exporter's only honest claim is about PRECEDENCE; it has no
opinion on what files a work item touches or how long it takes, and inventing placeholder values
for either would misrepresent a fact this script does not have (ADR-0002, never a guessed
default). A caller wanting a full schedule merges this output's `depends_on` lists into a job list
that separately supplies `resources`/`duration` -- this script's own honestly-disclosed limit,
matching design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md's existing disclosure discipline (nothing
here can audit whether a `resources` list is complete either).

USAGE:
  python3 tools/export_precedence.py [target-name]

Reads the SAME deployment config `led`/`judge`/`pickup` read (bootstrap/templates/led.tmpl
"Connection defaults are sourced LIVE from this project's deployment.json"; filing/
deployment_record.py, the ONE home for that JSON shape): PICKUP_DEPLOYMENT env var if set (the
mechanism the scaffolded `led`/`judge`/`pickup` shims already use), else LEDGER_DEPLOYMENT (engine/
targets.py's THIRD RESOLUTION SOURCE), else `<repo-root>/deployment.json` next to this checkout.
`target-name` is accepted but unused today (no name->deployment registry lookup exists for this
script; kept as a reserved positional for parity with `led`'s own target-name-taking verbs and to
avoid a silent-argument-swallow surprise if one is passed) -- pass nothing on a normal scaffolded
project.

Stdlib-only, top-of-file imports (gates/no_lazy_imports.py; CLAUDE.md, "Lazy imports are BANNED").
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
sys.path.insert(0, str(_REPO_ROOT / "filing"))

import deployment_record  # noqa: E402  (filing/deployment_record.py, the ONE home for the deployment.json shape)


def _load_deployment() -> deployment_record.DeploymentRecord:
    """Resolve this project's deployment.json exactly as led.tmpl/judge/pickup do: PICKUP_DEPLOYMENT
    (the scaffolded-shim mechanism) first, then LEDGER_DEPLOYMENT (engine/targets.py's own env
    override), then the repo-root default. Refuses loudly (DeploymentError propagates) on a
    missing/malformed record -- never a guessed connection."""
    dep_path = os.environ.get("PICKUP_DEPLOYMENT") or os.environ.get("LEDGER_DEPLOYMENT") \
        or str(_REPO_ROOT / "deployment.json")
    return deployment_record.load_deployment(dep_path)


def _psql(dep: deployment_record.DeploymentRecord, sql: str) -> str:
    """Run one read-only statement via `psql` (the same CLI transport instruments/ledger_target.py
    and bootstrap/templates/led.tmpl already use -- no second psycopg2/DB-API dependency, keeping
    this script stdlib-only). Returns raw stdout; caller parses."""
    result = subprocess.run(
        ["psql", "-h", dep.host, "-d", dep.db, "-v", "ON_ERROR_STOP=1", "-tAc", sql],
        capture_output=True, text=True, check=True)
    return result.stdout


def _has_column(dep: deployment_record.DeploymentRecord, schema: str, table: str, column: str) -> bool:
    out = _psql(dep, f"""
        SELECT EXISTS (
          SELECT 1 FROM information_schema.columns
          WHERE table_schema = '{schema}' AND table_name = '{table}' AND column_name = '{column}'
        );""")
    return out.strip() == "t"


def _has_relation(dep: deployment_record.DeploymentRecord, qualified: str) -> bool:
    out = _psql(dep, f"SELECT to_regclass('{qualified}') IS NOT NULL;")
    return out.strip() == "t"


def _refuse(message: str) -> None:
    print(f"export_precedence: REFUSED -- {message}", file=sys.stderr)
    raise SystemExit(1)


def export_precedence(dep: deployment_record.DeploymentRecord) -> dict:
    """Return the scheduler-format dict. Raises SystemExit (via `_refuse`) with teach-text on a
    pre-s30 (no edge_type column) or pre-s32 (no work_edge_blocks_close view) world, before
    issuing the edge query -- see module docstring's "PRE-s30 / PRE-s32 REFUSAL" section."""
    if not _has_column(dep, dep.schema, "ledger", "edge_type"):
        _refuse(
            f"{dep.schema}.ledger has no edge_type column -- this world predates typed "
            "dependency edges. Apply kernel/lineage/s30-typed-dependency-edges.sql to this "
            "project's schema (a maintainer act, ORCH-OPERATING-CARD.md's kernel-delta decision "
            "tree) before blocks-close precedence can be exported; every work_depends_on row on "
            "this world is untyped, so 'blocks-close' cannot be distinguished from 'informs' at all.")
    if not _has_relation(dep, f"{dep.schema}.work_edge_blocks_close"):
        _refuse(
            f"{dep.schema}.work_edge_blocks_close does not exist -- this world has "
            "kernel/lineage/s30-typed-dependency-edges.sql (edge_type present) but not "
            "kernel/lineage/s32-edge-views-single-home.sql, the single home this script reads "
            "the blocks-close edge relation from (module docstring's WHY). Apply s32 to this "
            "project's schema before exporting; this script deliberately does not re-derive "
            "s30's edge_type='blocks-close' predicate over raw ledger a second time.")

    rows_out = _psql(dep, f"""
        SELECT e.dependent_slug, e.antecedent_slug
        FROM {dep.schema}.work_edge_blocks_close e
        JOIN {dep.schema}.ledger_current lc ON lc.id = e.edge_row_id
        ORDER BY e.dependent_slug, e.antecedent_slug;""")

    depends_on: dict[str, set[str]] = {}
    for line in rows_out.splitlines():
        if not line.strip():
            continue
        dependent, antecedent = line.split("|", 1)
        depends_on.setdefault(dependent, set()).add(antecedent)
        depends_on.setdefault(antecedent, set())

    jobs = [
        {"id": slug, "depends_on": sorted(deps)}
        for slug, deps in sorted(depends_on.items())
    ]
    return {"jobs": jobs}


def main(argv: list[str]) -> int:
    # `target-name` positional accepted-but-unused -- see module docstring USAGE.
    dep = _load_deployment()
    result = export_precedence(dep)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
