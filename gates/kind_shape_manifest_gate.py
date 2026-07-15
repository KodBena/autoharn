#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T20:19:45Z
#   last-change: 2026-07-15T20:20:02Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""kind_shape_manifest_gate -- MANIFEST + GATE for the kernel ledger's kind-scoped shape
invariants (ledger item `kind-shape-manifest-gate`, per
design/ORCH-CATEGORICAL-REFACTOR-CONSULT-2026-07-15.md finding F5 / plan step 6).

WHAT THIS IS. `kernel/lineage/*.sql` re-authors, by hand, per delta, the correlation between
`ledger.kind` and a payload column that only means something for that kind (F5: "the ledger row
as a sum type over kinds"). Ten-plus such CHECKs exist today, split between a TWO-WAY iff
(`(kind = 'X') = (col IS NOT NULL)`, s22's `work_slug_kind_shape`/`work_title_kind_shape`/
`work_resolution_kind_shape`) and a ONE-WAY implication (`col IS NULL OR kind = 'X'`, s22's
`work_witness_kind_shape`, s28's `work_parent_kind_shape`, s30's `edge_type_kind_shape`). The
split is NOT accidental -- s28's own header names "nullable-legal-roots" (a root item legitimately
has kind='work_opened' with work_parent NULL, so the correlation cannot be an iff), and s30's own
header names append-only history (a two-way CHECK would fail ADD CONSTRAINT's whole-table
validation against pre-existing rows a backfill can never touch). F5's own verdict: "do not
uniformize the shapes; state the (kind, column, arity) table once as a manifest and gate the
catalog against it."

TWO COLUMNS ARE LICENSED BUT NOT CHECK-ENFORCED (a real wrinkle this sweep found, named rather
than smoothed over -- CLAUDE.md's hazard-flagging duty): `regards` (s15) and
`work_review_disposition` (s29, the sec-10 epoch amendment) are BOTH genuinely kind-scoped
two-way correlations that CANNOT be expressed as a plain CHECK -- `regards` because
`validate_review()` must look up an EARLIER row's actor (a self-referencing lookup no CHECK can
perform), `work_review_disposition` because its correlation became EPOCH-GATED and a CHECK cannot
consult `migration_epoch`, a different table. Both are enforced by a BEFORE INSERT trigger
instead. The manifest below records this as a distinct `mechanism` value ("trigger") rather than
silently dropping the columns or silently demanding a CHECK that cannot exist -- the variance is
load-bearing, per F5, and this is another instance of it, one level down from arity.

MANIFEST SCOPE: `kernel/lineage/ledger`'s columns only. `review_detail` carries CHECKs of its own
(`discharge_grade_check`, `review_detail_independence_check`, `review_detail_verdict_check`) but
that table has no `kind` column -- nothing on it is "kind-scoped" in F5's sense, confirmed by
reading `kernel/lineage/s13-schema.sql`'s `review_detail` DDL and s29's `discharge_grade` add.
Every OTHER ledger column not appearing in MANIFEST below is CORE (structural, present or legal
on every row regardless of `kind` -- id/ts/session/kind/statement/... /row_hash, see
CORE_COLUMNS) -- `amends`/`amends_scope`/`answers` were checked against their own write-boundary
triggers (`validate_amends`/`validate_answers` in s15-schema.sql) and confirmed NOT kind-scoped
(any kind may amend or answer; the constraint is "must resolve to an earlier own-session row",
never a kind test).

CLOSURE STATEMENT (ADR-0000 Rule 2a):
  - INVARIANT: every ledger column that is NOT in CORE_COLUMNS carries EXACTLY its MANIFEST-
    declared (kinds, arity, mechanism) shape in the live catalog (for mechanism="CHECK": a
    `pg_constraint` CHECK definition that parses to that exact (column, kinds, arity); for
    mechanism="trigger": NO catalog CHECK ties the column to `kind` at all -- the correlation
    lives only in the named trigger function, exactly as documented). A column carrying neither
    a matching CHECK nor a MANIFEST "trigger" declaration is an UNLICENSED PAYLOAD COLUMN,
    refused.
  - QUANTIFICATION UNIVERSE: every column of `<schema>.ledger` in a live catalog produced by
    applying the FULL current birth chain (`high_watermark_1.sql` through
    `s30-typed-dependency-edges.sql`, `bootstrap/new-project.sh`'s own `LINEAGE_CHAIN` order) --
    not a fixture, not memory of an earlier sweep. Every kind-mentioning CHECK on `ledger` is
    parsed generically (regex over `pg_get_constraintdef` output, not a name allowlist), so a
    NEW kind-shape CHECK a future delta adds is caught by this gate on its own shape, not only by
    name collision with something already in MANIFEST. Sibling surface swept and confirmed empty:
    no OTHER table in the chain (`kernel.principal`, `kernel.principal_role`,
    `countersign_obligation`, `kernel.stamp_secret`, `kernel.migration_epoch`,
    `kernel.chain_genesis`, `kernel.chain_high_water`) carries a `kind` column at all.
  - DENOMINATION: the resource is "a (column, catalog-shape) pair", never a proxy (not a
    constraint count, not a table size) -- one violation named per column.

NOT IN SCOPE (deliberately, named per F5's "the variance is load-bearing" instruction, never
silently uniformized): the DEFAULT-then-CHECK ordering inside `validate_work_item()` (plan step
7's own concern); the .lp engine side's kind-tagged predicates (plan step 4/8, a different
producer); WHICH kind values are legal at all (`ledger_kind_check` -- a vocabulary CHECK, not a
shape CHECK, carries no `IS NULL`/`IS NOT NULL` correlate and is correctly parsed-and-skipped by
`_classify_kind_shape` below).

USAGE:
  python3 gates/kind_shape_manifest_gate.py                 # scratch apply, assert, teardown
  python3 gates/kind_shape_manifest_gate.py --keep-scratch   # leave the scratch schema (debug)
  python3 gates/kind_shape_manifest_gate.py --inject-column NAME
      # after the real chain applies, ALSO `ALTER TABLE ledger ADD COLUMN NAME text` (no CHECK)
      # before asserting -- the seen-red negative control (a payload-like column with no
      # licensing CHECK and no MANIFEST entry). Never used by the plain gate invocation.

Exit codes: 0 clean, 1 violations (listed), 2 usage/psql/IO error.
Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LINEAGE = REPO / "kernel" / "lineage"

PGHOST = "192.168.122.1"
PGDB = "toy"

# The full current birth chain, in bootstrap/new-project.sh's own LINEAGE_CHAIN order --
# high_watermark_1.sql itself \ir-chains s15 -> s17(stamp) -> s17(independence) -> s19 (its own
# header, "DELIBERATELY EXCLUDED: s18" -- s18 is Study-mode apparatus, not kernel).
CHAIN = [
    "high_watermark_1.sql",
    "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql",
    "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql",
    "s24-declared-event-time.sql",
    "s25-commission-kind.sql",
    "s26-row-hash-chain.sql",
    "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql",
    "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql",
]

# ================================================================================================
# THE MANIFEST -- the ONE declared table (ADR-0011 Rule 4: a net over the class, never an
# enumeration hand-copied per reader). Per F5: the (kind, column, arity) correlation, PLUS the
# `mechanism` field this sweep found is also load-bearing variance (CHECK vs trigger), PLUS a
# `reason` naming WHY every one-way or trigger-mechanism row is not a two-way CHECK -- filed, not
# silently uniformized (ADR-0000 Rule 2a's "an axis deliberately not covered is named as not
# covered" applied one level down, to enforcement mechanism rather than input axis).
# ================================================================================================
MANIFEST = [
    dict(column="work_slug", kinds=("work_opened", "work_claimed", "work_depends_on", "work_closed"),
         arity="two-way", mechanism="CHECK", constraint="work_slug_kind_shape",
         defining_delta="s22-work-item-ledger.sql", reason=None),
    dict(column="work_title", kinds=("work_opened",),
         arity="two-way", mechanism="CHECK", constraint="work_title_kind_shape",
         defining_delta="s22-work-item-ledger.sql", reason=None),
    dict(column="work_depends_on", kinds=("work_depends_on",),
         arity="two-way", mechanism="CHECK", constraint="work_depends_on_kind_shape",
         defining_delta="s22-work-item-ledger.sql", reason=None),
    dict(column="work_resolution", kinds=("work_closed",),
         arity="two-way", mechanism="CHECK", constraint="work_resolution_kind_shape",
         defining_delta="s22-work-item-ledger.sql", reason=None),
    dict(column="work_witness", kinds=("work_closed",),
         arity="one-way", mechanism="CHECK", constraint="work_witness_kind_shape",
         defining_delta="s22-work-item-ledger.sql",
         reason="not every work_closed row carries a witness -- only a 'shipped' resolution "
                "requires one (work_shipped_requires_witness); one-way forecloses work_witness "
                "appearing on a NON-work_closed row, it does not demand one on every work_closed "
                "row."),
    dict(column="work_parent", kinds=("work_opened",),
         arity="one-way", mechanism="CHECK", constraint="work_parent_kind_shape",
         defining_delta="s28-work-parent-edge.sql",
         reason="nullable-legal-roots (s28 header, verbatim): a root item legitimately has "
                "kind='work_opened' with work_parent NULL, so the correlation is NOT an iff."),
    dict(column="work_review_ref", kinds=("work_closed",),
         arity="one-way", mechanism="CHECK", constraint="work_review_ref_kind_shape",
         defining_delta="s29-obligation-item-key-and-typed-close.sql",
         reason="mirrors work_witness one column over: only a 'witnessed' disposition "
                "(work_review_witnessed_requires_ref) requires a ref; a 'deferred' work_closed "
                "row legitimately has NULL."),
    dict(column="work_strict_close", kinds=("work_closed",),
         arity="one-way", mechanism="CHECK", constraint="work_strict_close_kind_shape",
         defining_delta="s29-obligation-item-key-and-typed-close.sql",
         reason="NULL/false = non-strict is a legal posture on ANY work_closed row (s29: "
                "'the spec's own declared posture, not a universal mandate'); one-way forecloses "
                "work_strict_close appearing on a non-work_closed row only."),
    dict(column="edge_type", kinds=("work_depends_on",),
         arity="one-way", mechanism="CHECK", constraint="edge_type_kind_shape",
         defining_delta="s30-typed-dependency-edges.sql",
         reason="append-only history forces this (s30 header, verbatim): a legacy "
                "work_depends_on row predates this column and can never be backfilled (no "
                "UPDATE, append-only) -- a two-way iff would fail ADD CONSTRAINT's whole-table "
                "validation on any world with pre-existing rows."),
    dict(column="regards", kinds=("review",),
         arity="two-way", mechanism="trigger", constraint=None,
         defining_delta="s15-schema.sql",
         reason="cannot be a plain CHECK: validate_review() must look up an EARLIER row's actor "
                "(self-referencing lookup) to enforce segregation-of-duties -- a CHECK cannot "
                "express that. Logically two-way (kind='review' iff regards IS NOT NULL): the "
                "trigger's first IF raises when kind='review' AND regards IS NULL, its ELSIF "
                "raises when kind<>'review' AND regards IS NOT NULL."),
    dict(column="work_review_disposition", kinds=("work_closed",),
         arity="two-way", mechanism="trigger", constraint=None,
         defining_delta="s29-obligation-item-key-and-typed-close.sql (sec-10 epoch amendment)",
         reason="WAS a table CHECK (work_review_disposition_kind_shape) until the sec-10 "
                "amendment made the two-way correlation EPOCH-GATED (grandfathers pre-amendment "
                "rows) -- a CHECK cannot consult migration_epoch, a different table, so the "
                "correlation moved into validate_work_item()'s trigger clause. The old CHECK's "
                "DROP CONSTRAINT IF EXISTS is kept in s29 as idempotent cleanup, never re-added."),
]
MANIFEST_BY_COLUMN = {row["column"]: row for row in MANIFEST}
assert len(MANIFEST_BY_COLUMN) == len(MANIFEST), "duplicate column in MANIFEST -- SSOT violated"

# CORE_COLUMNS: every OTHER live ledger column, confirmed NOT kind-scoped (see module docstring's
# "MANIFEST SCOPE" paragraph for how amends/amends_scope/answers were checked). A column that is
# neither in MANIFEST nor here is, by construction, an unlicensed payload column.
CORE_COLUMNS = frozenset({
    "id", "ts", "session", "kind", "statement", "rationale", "status", "evidence", "confidence",
    "supersedes", "refs", "concern", "enacts", "actor", "amends", "amends_scope", "answers",
    "stamp_session", "stamp_agent", "stamp_ts", "stamp_hmac", "stamp_verified",
    "stamp_invocation", "event_declared_ts", "row_hash",
})


# ================================================================================================
# THE GATE
# ================================================================================================

def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def _psql(schema_vars: dict[str, str], sql: str) -> subprocess.CompletedProcess:
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-tAq"]
    for k, v in schema_vars.items():
        args += ["-v", f"{k}={v}"]
    args += ["-c", sql]
    return sh(args)


def teardown(schema: str, kern: str, role: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE; "
        f"DROP OWNED BY {role};"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {role};"])


def apply_chain(schema: str, kern: str, role: str) -> None:
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for f in CHAIN:
        args += ["-f", str(LINEAGE / f)]
    cp = sh(args)
    if cp.returncode != 0:
        raise RuntimeError(f"chain apply FAILED:\n{cp.stdout[-2000:]}\n{cp.stderr[-2000:]}")


def catalog_columns(schema: str) -> list[str]:
    cp = _psql({}, f"SELECT column_name FROM information_schema.columns "
                    f"WHERE table_schema = '{schema}' AND table_name = 'ledger' "
                    f"ORDER BY ordinal_position;")
    if cp.returncode != 0:
        raise RuntimeError(f"catalog_columns FAILED: {cp.stderr}")
    return [ln.strip() for ln in cp.stdout.splitlines() if ln.strip()]


def catalog_check_defs(schema: str) -> dict[str, str]:
    """{conname: pg_get_constraintdef(...)} for every CHECK constraint on <schema>.ledger."""
    cp = _psql({}, f"""
        SELECT c.conname || chr(31) || pg_get_constraintdef(c.oid)
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = '{schema}' AND t.relname = 'ledger' AND c.contype = 'c';
    """)
    if cp.returncode != 0:
        raise RuntimeError(f"catalog_check_defs FAILED: {cp.stderr}")
    out = {}
    for ln in cp.stdout.splitlines():
        if not ln.strip():
            continue
        name, defn = ln.split(chr(31), 1)
        out[name] = defn
    return out


_KIND_EQ_RE = re.compile(r"kind = '([^']+)'")
_KIND_ANY_RE = re.compile(r"kind = ANY \(ARRAY\[([^\]]+)\]\)")
_ARRAY_ELEM_RE = re.compile(r"'([^']+)'")
_TWO_WAY_RE = re.compile(r"= \((\w+) IS NOT NULL\)")
_ONE_WAY_A_RE = re.compile(r"\((\w+) IS NULL\) OR \(kind")   # col IS NULL OR kind = ...
_ONE_WAY_B_RE = re.compile(r"kind[^()]*\)\)?\) OR \((\w+) IS NULL\)")  # kind = ... OR col IS NULL


def _extract_kinds(defn: str) -> tuple[str, ...]:
    m = _KIND_ANY_RE.search(defn)
    if m:
        return tuple(_ARRAY_ELEM_RE.findall(m.group(1)))
    return tuple(_KIND_EQ_RE.findall(defn))


def classify_kind_shape(conname: str, defn: str):
    """Parse a single CHECK constraint definition. Returns None if it does not mention `kind` at
    all (an ordinary vocabulary/business-rule CHECK, out of this manifest's scope). Returns
    ("UNPARSEABLE", conname, defn) if it mentions `kind` but matches neither the two-way nor the
    one-way shape this codebase's kind-shape CHECKs use (a NEW shape a future delta introduced,
    refused loudly rather than silently skipped -- ADR-0002). Otherwise returns
    (column, kinds, arity)."""
    if "kind" not in defn:
        return None
    if "IS NULL" not in defn and "IS NOT NULL" not in defn:
        # a pure kind-VOCABULARY CHECK (e.g. ledger_kind_check's `kind = ANY (ARRAY[...])`) --
        # constrains kind's own legal values, correlates it with no OTHER column's nullability,
        # so it is not a "shape" CHECK in F5's sense at all. Out of this manifest's scope.
        return None
    kinds = _extract_kinds(defn)
    if not kinds:
        # mentions the bare word "kind" with no `kind = ...` / `kind = ANY(...)` predicate at
        # all -- not a shape CHECK this manifest's vocabulary covers (none exist today; refused
        # loudly rather than silently treated as core).
        return ("UNPARSEABLE", conname, defn)
    m2 = _TWO_WAY_RE.search(defn)
    if m2 and m2.group(1) != "kind":
        return (m2.group(1), kinds, "two-way")
    m1a = _ONE_WAY_A_RE.search(defn)
    if m1a:
        return (m1a.group(1), kinds, "one-way")
    m1b = _ONE_WAY_B_RE.search(defn)
    if m1b:
        return (m1b.group(1), kinds, "one-way")
    return ("UNPARSEABLE", conname, defn)


def assert_manifest(schema: str) -> list[str]:
    """The core check, independent of scratch-schema lifecycle (unit-testable). Returns a list
    of violation strings; empty means clean."""
    violations: list[str] = []
    columns = set(catalog_columns(schema))
    check_defs = catalog_check_defs(schema)

    # 1. classify every CHECK constraint that mentions `kind`
    catalog_shapes: dict[str, tuple] = {}   # column -> (kinds, arity, conname)
    for conname, defn in check_defs.items():
        parsed = classify_kind_shape(conname, defn)
        if parsed is None:
            continue
        if parsed[0] == "UNPARSEABLE":
            violations.append(
                f"UNPARSEABLE kind-mentioning CHECK {parsed[1]!r} ({parsed[2]!r}) -- this "
                f"gate's classifier recognizes only the two shapes MANIFEST declares "
                f"(two-way iff, one-way implication). Either this is a NEW kind-shape idiom "
                f"(extend classify_kind_shape and MANIFEST together) or it is not truly "
                f"kind-scoped (rename it off 'kind' to stop tripping this gate).")
            continue
        col, kinds, arity = parsed
        if col in catalog_shapes:
            violations.append(f"column {col!r} carries MULTIPLE kind-shape CHECKs "
                               f"({catalog_shapes[col][2]!r} and {conname!r}) -- one home only.")
            continue
        catalog_shapes[col] = (kinds, arity, conname)

    # 2. every catalog kind-shape CHECK must match its MANIFEST row exactly
    for col, (kinds, arity, conname) in catalog_shapes.items():
        row = MANIFEST_BY_COLUMN.get(col)
        if row is None:
            violations.append(
                f"UNLICENSED PAYLOAD COLUMN {col!r}: catalog CHECK {conname!r} ties it to "
                f"kind, but no MANIFEST row declares it. Add it to MANIFEST in "
                f"gates/kind_shape_manifest_gate.py (kind(s)={kinds}, arity={arity!r}), or "
                f"remove the column/constraint if it should not exist.")
            continue
        if row["mechanism"] != "CHECK":
            violations.append(
                f"column {col!r}: MANIFEST declares mechanism={row['mechanism']!r} but the "
                f"catalog carries a CHECK ({conname!r}) -- shape drifted from its licensed "
                f"mechanism.")
            continue
        if row["arity"] != arity:
            violations.append(
                f"column {col!r}: MANIFEST declares arity={row['arity']!r}, catalog CHECK "
                f"{conname!r} is {arity!r} -- shape drifted.")
        if set(row["kinds"]) != set(kinds):
            violations.append(
                f"column {col!r}: MANIFEST declares kinds={row['kinds']}, catalog CHECK "
                f"{conname!r} covers kinds={kinds} -- shape drifted.")

    # 3. every MANIFEST row must exist in the catalog, one way or the other
    for row in MANIFEST:
        col = row["column"]
        if row["mechanism"] == "CHECK":
            if col not in catalog_shapes:
                violations.append(
                    f"MANIFEST row for column {col!r} declares mechanism=CHECK "
                    f"(constraint={row['constraint']!r}) but no such CHECK exists in the live "
                    f"catalog -- stale manifest row or a dropped constraint.")
        elif row["mechanism"] == "trigger":
            if col in catalog_shapes:
                violations.append(
                    f"MANIFEST row for column {col!r} declares mechanism=trigger but the "
                    f"catalog NOW carries a kind-shape CHECK on it too -- update MANIFEST to "
                    f"mechanism=CHECK (and record the new constraint name) or explain the "
                    f"redundancy.")
        else:
            violations.append(f"MANIFEST row for column {col!r} declares an unrecognized "
                               f"mechanism {row['mechanism']!r}.")

    # 4. every payload-like (non-core) column must be licensed, whether or not it carries a
    #    catalog CHECK -- this is what catches a column with NO CHECK at all (the seen-red case:
    #    mechanism="CHECK"-shaped hazard that never got its CHECK written).
    for col in columns:
        if col in CORE_COLUMNS or col in MANIFEST_BY_COLUMN:
            continue
        violations.append(
            f"UNLICENSED PAYLOAD COLUMN {col!r}: not in CORE_COLUMNS (structural/universal) and "
            f"not in MANIFEST (kind-scoped payload) -- an unlicensed column. Discharge paths: "
            f"(a) add a MANIFEST row naming its (kind(s), arity, mechanism, reason) if it is "
            f"genuinely kind-scoped payload, or (b) remove the column if it should not exist.")

    return violations


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-scratch", action="store_true",
                     help="leave the scratch schema/kernel/role standing (debug only)")
    ap.add_argument("--inject-column", default=None,
                     help="seen-red negative control: after the real chain applies, add this "
                          "column (no CHECK) before asserting -- must be REFUSED")
    a = ap.parse_args(argv)

    suffix = "kbmg"
    schema, kern, role = f"{suffix}_scratch", f"{suffix}_scratch_kernel", f"{suffix}_scratch_rw"
    teardown(schema, kern, role)   # pre-clean: never trust residue from a prior interrupted run
    try:
        apply_chain(schema, kern, role)
        if a.inject_column:
            cp = _psql({}, f"ALTER TABLE {schema}.ledger ADD COLUMN {a.inject_column} text;")
            if cp.returncode != 0:
                print(f"kind-shape-manifest-gate: --inject-column FAILED: {cp.stderr}")
                return 2
        violations = assert_manifest(schema)
    except RuntimeError as exc:
        print(f"kind-shape-manifest-gate: SCRATCH APPLY ERROR -- {exc}")
        return 2
    finally:
        if not a.keep_scratch:
            teardown(schema, kern, role)
        else:
            print(f"kind-shape-manifest-gate: --keep-scratch -- schema={schema} kern={kern} "
                  f"role={role} left standing, teardown it yourself when done")

    if violations:
        print(f"kind-shape-manifest-gate: {len(violations)} violation(s):\n")
        for v in violations:
            print(f"  !! {v}")
        return 1
    print(f"kind-shape-manifest-gate: clean -- {len(MANIFEST)} MANIFEST row(s) match the live "
          f"catalog exactly, {len(CORE_COLUMNS)} core column(s) accounted for, no unlicensed "
          f"payload column. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
