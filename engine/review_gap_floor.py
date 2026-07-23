#!/usr/bin/env python3
"""review_gap_floor -- the SQL FLOOR of the content-free-review-discharge audit: producer ONE of
the marriage differential (engine/review_gap_differential.py), computing the SAME judgment as
engine/lp/review_gap_audit.lp (discharges/2, flagged/1) directly against the live ledger, in one
non-recursive SQL query -- no transitive closure is needed here (review_gap's own "superseded" is
SINGLE-HOP, not the multi-hop sup_star closure ledger_tnow.lp's other consumers need; see
engine/review_gap_edb.py's own docstring for why that distinction matters).

INDEPENDENCE (I6, ADR-0000 INDEP; the ledger_floor.py precedent, restated for this domain): this
producer shares NO code path with clingo, and its own content-free predicate is a SEPARATELY
AUTHORED SQL regex (`regexp_replace(statement, '\\s+', ' ', 'g')` + `btrim` + `length`), never a
call into engine/review_gap_thresholds.normalize()/is_content_free() -- those are Python and
cannot run inside a SQL string anyway, but the discipline point stands even where it is also a
practical necessity: two independently-authored encodings of "whitespace-normalized length"
agreeing on real data is the substance of the differential. The one thing NOT independently
re-derived is the NUMBER itself (CONTENT_FREE_STATEMENT_THRESHOLD) -- imported from
engine/review_gap_thresholds and interpolated into this module's own SQL text, exactly the
pattern engine/ledger_floor.py's own `support_floor_atoms(name, now_epoch)` already uses for a
shared parameter (P1: the VALUE has one home; the COMPUTATION PATH is independent).

KNOWN DIVERGENCE, NAMED HONESTLY: Python's `str.split()` (engine/review_gap_thresholds.normalize)
splits on any character `str.isspace()` recognizes, including some Unicode whitespace forms
Postgres's default (non-ICU) `\\s` regex class does not match. For ASCII statement text (every
review statement in the measured run12 corpus, and the overwhelming likely case in practice) the
two normalizations agree bit-for-bit; an exotic-Unicode-whitespace statement is a theoretical
divergence point this module names rather than silently risks, per ADR-0011 Rule 1's "declare the
enforcement surface honestly" and ADR-0000's closure-statement discipline (the axis named, not
covered, is filed here rather than silently assumed away).

Read-only. Lazy imports banned (top-of-file only)."""
from __future__ import annotations

import sys

from ledger_edb import Target, resolve
from review_gap_thresholds import CONTENT_FREE_STATEMENT_THRESHOLD

_REQUIRED_FAMILIES = ("actor_column", "regards_column", "countersign_obligation", "review_detail")


def full_capable(t: Target) -> tuple[bool, dict[str, bool]]:
    """The same four-family capability check engine/review_gap_edb.py's own export() runs --
    re-derived here (a SEPARATE call, not an import of that module's own logic) so the SQL floor
    does not depend on the ASP producer's own EDB-building code path either (the same
    independence posture this module's docstring states for the content-free predicate)."""
    have = {
        "actor_column": t.has_col("actor"),
        "regards_column": t.has_col("regards"),
        "countersign_obligation": t.has_relation(f"{t.schema}.countersign_obligation"),
        "review_detail": t.has_relation(f"{t.schema}.review_detail"),
    }
    return all(have[f] for f in _REQUIRED_FAMILIES), have


def floor_atoms(target_name: str) -> set[str]:
    """The set of discharges/2 + flagged/1 atoms the SQL floor derives for `target_name`
    (read-only). Empty (never an error) when the target lacks a required capability -- the caller
    (engine/review_gap_audit.py's build_report / engine/review_gap_differential.py) reads
    `full_capable()` separately to distinguish "incapable" from "capable, nothing to flag"."""
    t = resolve(target_name)
    capable, _ = full_capable(t)
    if not capable:
        return set()
    rel = t.rel()
    # kernel/lineage/s57-obligation-revocation-event.sql (design/FABLE-LEGACY-LED-RETIREMENT-
    # SPEC.md Part A): a revoked obligation's scope is excluded from `obliged`, mirroring
    # review_gap's own re-issue INDEPENDENTLY (I6) -- never importing that kernel view. GATED on
    # the ledger carrying obligation_revoked_scope AT ALL (not merely on there being zero rows of
    # that kind): a pre-s57 schema has NO such column, so referencing it unconditionally would be
    # a bare "column does not exist" SQL error, not an empty result -- the capability check below
    # is what keeps this extension behavior-preserving on every schema this floor ran against
    # before s57 existed, rather than merely assuming the column's absence is harmless.
    has_revocation = t.has_col("obligation_revoked_scope")
    revoked_cte = (
        f"""revoked AS (
        SELECT rv.obligation_revoked_scope AS scope
        FROM {rel} rv
        WHERE rv.kind = 'obligation_revoked'
          AND NOT EXISTS (SELECT 1 FROM {rel} s3 WHERE s3.supersedes = rv.id)
      ),
      """
        if has_revocation else ""
    )
    obliged_where = "WHERE o.scope NOT IN (SELECT scope FROM revoked)" if has_revocation else ""
    sql = f"""
    WITH
      led AS (SELECT id, actor, supersedes FROM {rel}),
      {revoked_cte}obliged AS (
        SELECT DISTINCT o.obliges_actor AS actor FROM {t.schema}.countersign_obligation o
        {obliged_where}
      ),
      superseded AS (SELECT DISTINCT supersedes AS id FROM led WHERE supersedes IS NOT NULL),
      reviews AS (
        SELECT l.id, l.actor, l.regards, l.statement FROM {rel} l
        JOIN {t.schema}.review_detail d ON d.ledger_id = l.id
        WHERE l.kind = 'review' AND d.verdict = 'attest'
      ),
      discharges AS (
        SELECT r.id AS rid, l.id AS lid FROM reviews r
        JOIN led l ON l.id = r.regards
        JOIN obliged o ON o.actor = l.actor
        WHERE r.actor <> l.actor
          AND l.id NOT IN (SELECT id FROM superseded)
          AND r.id NOT IN (SELECT id FROM superseded)
      ),
      flagged AS (
        SELECT d.rid, d.lid FROM discharges d
        JOIN reviews r ON r.id = d.rid
        WHERE length(btrim(regexp_replace(r.statement, '\\s+', ' ', 'g'))) < {int(CONTENT_FREE_STATEMENT_THRESHOLD)}
      )
    SELECT 'discharges(' || rid || ',' || lid || ')' FROM discharges
    UNION ALL SELECT 'flagged(' || rid || ')' FROM flagged
    ;"""
    out = t.run(sql).stdout
    return {line.strip() for line in out.splitlines() if line.strip()}


def snapshot_text(target_name: str) -> str:
    """A canonical text snapshot of the TRUE inputs this floor reads (mirrors
    engine/ledger_floor.py's own `_ledger_snapshot_hash` idiom, inlined here as text rather than a
    pre-hashed digest so the caller, engine/review_gap_differential.py, can hash it itself
    alongside the ASP side's own input_hash convention)."""
    t = resolve(target_name)
    cols = ["id", "kind", "coalesce(actor::text,'')", "coalesce(regards::text,'')",
            "coalesce(supersedes::text,'')", "statement"]
    ledger_snap = t.run(f"SELECT {', '.join(cols)} FROM {t.rel()} ORDER BY id;").stdout
    detail_snap = t.run(
        f"SELECT ledger_id, verdict FROM {t.schema}.review_detail ORDER BY ledger_id;").stdout
    obligation_snap = t.run(
        f"SELECT scope, obliges_actor FROM {t.schema}.countersign_obligation ORDER BY scope;").stdout
    return ("# ledger snapshot (id,kind,actor,regards,supersedes,statement)\n" + ledger_snap
            + "# review_detail snapshot (ledger_id,verdict)\n" + detail_snap
            + "# countersign_obligation snapshot (scope,obliges_actor)\n" + obligation_snap)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("usage: review_gap_floor.py <target-name>", file=sys.stderr)
        return 2
    atoms = floor_atoms(args[0])
    print(f"# review_gap_floor(SQL) -- {args[0]}: {len(atoms)} atoms")
    for a in sorted(atoms):
        print(f"  {a}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
