# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T23:22:33Z
#   last-change: 2026-07-14T23:23:33Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""panel.backend.ledger_read — the ONLY place this backend issues SQL (ADR-0012 P1/P3).

Every function here is a read: a plain SELECT over the ledger's own existing views
(`ledger_current`, `work_item_current`, `review_gap`, `question_status`) or the base `ledger`/
`review_detail` tables, never a write (writes are `cosign.py`'s job, and only via `./led`).
Connections mirror `bootstrap/templates/led.tmpl` exactly: connect, `SET ROLE <role>`,
`SET search_path <schema>, <kern>` -- so this module runs under the same grant surface `led`
itself runs under, no wider.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row

from config import PanelConfig
from disposition import WitnessFacts
from manifest_load import Item


@contextmanager
def connect(cfg: PanelConfig) -> Iterator[psycopg.Connection]:
    """One connection, `SET ROLE`+`search_path` applied exactly as `led.tmpl` applies them.
    Autocommit -- every query here is a read, so no transaction/commit dance is needed."""
    conn = psycopg.connect(host=cfg.pghost, dbname=cfg.pgdb, row_factory=dict_row, autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute(f'SET ROLE "{cfg.role}"')
            cur.execute(f'SET search_path = "{cfg.schema}", "{cfg.kern}"')
        yield conn
    finally:
        conn.close()


@contextmanager
def _connect_unrestricted(cfg: PanelConfig) -> Iterator[psycopg.Connection]:
    """A connection that deliberately does NOT `SET ROLE <role>` (spec S9's ledger reads still
    go through `connect()` above, unaltered -- this helper is for exactly one narrow diagnostic:
    kernel/lineage/s17-stamp-mechanism.sql REVOKEs ALL on `<kern>.stamp_secret` FROM PUBLIC and
    grants it to no subject role on purpose (`SELECT * FROM stamp_secret` failing
    `permission denied` for a connecting subject is the verified security property, not an
    oversight -- see that file's own fixture note). `led.tmpl` has the same precedent for an
    administrative fact read outside the subject role: `led obligate revoke`'s
    `has_table_privilege` check also connects without `SET ROLE`. This connection is used ONLY
    to answer "does stamp_secret have any rows" (EXISTS, never the secret's value) for the
    health/co-sign-note UI text (spec S5) -- it never reads a ledger row and is not a write path."""
    conn = psycopg.connect(host=cfg.pghost, dbname=cfg.pgdb, row_factory=dict_row, autocommit=True)
    try:
        yield conn
    finally:
        conn.close()


def health(cfg: PanelConfig) -> dict[str, Any]:
    """GET /api/health facts (spec S3): deployment resolution, whether the kernel's
    `stamp_secret` is armed (drives the co-sign independence note, spec S5), and the connect-
    ability of the configured maintainer principal's row (present once `ensure_principal_registered`
    has run at startup). The `armed` check connects WITHOUT `SET ROLE` -- see
    `_connect_unrestricted`'s docstring: the subject role `<role>` is deliberately REVOKEd from
    reading `stamp_secret` at all, so checking "armed" under `SET ROLE <role>` would always raise
    `permission denied`, not report False."""
    with _connect_unrestricted(cfg) as conn, conn.cursor() as cur:
        cur.execute(f'SELECT EXISTS (SELECT 1 FROM "{cfg.kern}".stamp_secret) AS armed')
        armed = bool(cur.fetchone()["armed"])
    return {
        "ok": True,
        "deployment": {"schema": cfg.schema, "db": cfg.pgdb, "host_resolved": True},
        "stamp_secret_armed": armed,
        "maintainer_principal": cfg.maintainer_principal,
    }


def watermark(cfg: PanelConfig) -> dict[str, Any]:
    """GET /api/watermark and the background poller's own cheap per-tick query (spec S4)."""
    with connect(cfg) as conn, conn.cursor() as cur:
        cur.execute('SELECT max(id) AS max_id, max(ts) AS max_ts, count(*) AS count FROM ledger')
        row = cur.fetchone()
    return {
        "max_id": row["max_id"],
        "max_ts": row["max_ts"].isoformat() if row["max_ts"] else None,
        "count": row["count"],
    }


def recent_ledger(cfg: PanelConfig, n: int) -> list[dict[str, Any]]:
    with connect(cfg) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT l.id, l.kind, l.statement, p.name AS actor_name, l.ts, l.stamp_verified
            FROM ledger_current l LEFT JOIN principal p ON p.id = l.actor
            ORDER BY l.id DESC LIMIT %s
            """,
            (n,),
        )
        rows = cur.fetchall()
    return [_jsonable(r) for r in rows]


def work_items(cfg: PanelConfig) -> list[dict[str, Any]]:
    with connect(cfg) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT w.slug, w.title, w.state, w.resolution, w.witness, p.name AS claimant_name
            FROM work_item_current w LEFT JOIN principal p ON p.id = w.claimant
            ORDER BY w.slug
            """
        )
        rows = cur.fetchall()
    return [_jsonable(r) for r in rows]


def review_gap(cfg: PanelConfig) -> list[dict[str, Any]]:
    with connect(cfg) as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM review_gap ORDER BY id")
        rows = cur.fetchall()
    return [_jsonable(r) for r in rows]


def question_status(cfg: PanelConfig) -> list[dict[str, Any]]:
    with connect(cfg) as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM question_status ORDER BY question_id")
        rows = cur.fetchall()
    return [_jsonable(r) for r in rows]


def ledger_row(cfg: PanelConfig, row_id: int) -> dict[str, Any] | None:
    """One `ledger_current` row (by id) joined to its actor's name, or None if it does not
    resolve (superseded rows drop out of `ledger_current` by design -- a witness ref pointing at
    a superseded row is honestly a non-resolving witness, spec S6)."""
    with connect(cfg) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT l.id, l.kind, l.statement, l.ts, p.name AS actor_name
            FROM ledger_current l LEFT JOIN principal p ON p.id = l.actor
            WHERE l.id = %s
            """,
            (row_id,),
        )
        row = cur.fetchone()
    return _jsonable(row) if row else None


def work_item(cfg: PanelConfig, slug: str) -> dict[str, Any] | None:
    with connect(cfg) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT w.slug, w.title, w.state, w.resolution, w.witness, p.name AS claimant_name
            FROM work_item_current w LEFT JOIN principal p ON p.id = w.claimant
            WHERE w.slug = %s
            """,
            (slug,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        cur.execute(
            """
            SELECT id FROM ledger_current
            WHERE kind = 'work_closed' AND work_slug = %s
            ORDER BY id DESC LIMIT 1
            """,
            (slug,),
        )
        closed = cur.fetchone()
    result = _jsonable(row)
    result["closed_row_id"] = closed["id"] if closed else None
    return result


def maintainer_cosigned(cfg: PanelConfig, target_row_id: int) -> dict[str, Any] | None:
    """The same join `review_gap` uses (verdict='attest', distinct actor, not superseded),
    narrowed to the configured maintainer principal specifically, read fresh on every call --
    never a stored flag (spec S7). Returns the discharging review's facts, or None."""
    with connect(cfg) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT r.id AS review_id, d.verdict, p.name AS actor_name
            FROM ledger_current r
            JOIN review_detail d ON d.ledger_id = r.id
            JOIN principal p ON p.id = r.actor
            WHERE r.kind = 'review' AND r.regards = %s AND d.verdict = 'attest'
              AND p.name = %s
            ORDER BY r.id DESC LIMIT 1
            """,
            (target_row_id, cfg.maintainer_principal),
        )
        row = cur.fetchone()
    return _jsonable(row) if row else None


def latest_review_id(cfg: PanelConfig, regards: int, actor_name: str) -> int | None:
    """A tiny post-hoc lookup for `cosign.py`: the newest review row against `regards` by
    `actor_name` (any verdict -- used right after a `./led review` call whose exit code already
    told us whether it succeeded, so this is identification, not a second correctness check)."""
    with connect(cfg) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT r.id FROM ledger_current r
            JOIN principal p ON p.id = r.actor
            WHERE r.kind = 'review' AND r.regards = %s AND p.name = %s
            ORDER BY r.id DESC LIMIT 1
            """,
            (regards, actor_name),
        )
        row = cur.fetchone()
    return row["id"] if row else None


def resolve_witness(cfg: PanelConfig, ref_kind: str, ref: str) -> tuple[WitnessFacts, dict[str, Any] | None]:
    """Turn one manifest witness (`ref_kind`, `ref`) into `disposition.py`'s pure `WitnessFacts`
    plus the raw `resolved` fact-dict the API returns verbatim (spec S3's `Witness.resolved`).
    A ref that does not resolve at all comes back as `exists=False` -- honestly OPEN, per
    disposition.py's rule, never a fabricated witness (spec S6)."""
    if ref_kind == "work":
        resolved = work_item(cfg, ref)
        if resolved is None:
            return WitnessFacts(ref_kind, ref, exists=False, substantive=False,
                                 cosign_target_row=None, maintainer_cosigned=False), None
        closed_row_id = resolved.get("closed_row_id")
        substantive = resolved.get("state") == "closed"
        cosigned = False
        if closed_row_id is not None:
            cosigned = maintainer_cosigned(cfg, closed_row_id) is not None
        facts = WitnessFacts(
            ref_kind, ref, exists=True, substantive=substantive,
            cosign_target_row=closed_row_id, maintainer_cosigned=cosigned,
        )
        return facts, resolved
    if ref_kind == "row":
        try:
            row_id = int(ref)
        except ValueError:
            return WitnessFacts(ref_kind, ref, exists=False, substantive=False,
                                 cosign_target_row=None, maintainer_cosigned=False), None
        resolved = ledger_row(cfg, row_id)
        if resolved is None:
            return WitnessFacts(ref_kind, ref, exists=False, substantive=False,
                                 cosign_target_row=None, maintainer_cosigned=False), None
        cosigned = maintainer_cosigned(cfg, row_id) is not None
        facts = WitnessFacts(
            ref_kind, ref, exists=True, substantive=True,
            cosign_target_row=row_id, maintainer_cosigned=cosigned,
        )
        return facts, resolved
    raise ValueError(f"unknown ref_kind {ref_kind!r} (expected 'work' or 'row')")


@dataclass(frozen=True)
class ResolvedWitness:
    ref_kind: str
    ref: str
    note: str
    resolved: dict[str, Any] | None
    cosign_target_row: int | None
    cosign: dict[str, Any]
    facts: WitnessFacts


def resolve_item_witnesses(cfg: PanelConfig, item: Item) -> list[ResolvedWitness]:
    """Resolve every declared witness of one manifest `Item` against the live ledger. Used by
    app.py to build both the API's per-witness payload and the `WitnessFacts` list it hands to
    `disposition.derive_status`."""
    out: list[ResolvedWitness] = []
    for w in item.witnesses:
        facts, resolved = resolve_witness(cfg, w.ref_kind, w.ref)
        cosign_info: dict[str, Any] = {"cosigned": False, "by": None, "review_id": None, "verdict": None}
        if facts.cosign_target_row is not None:
            disc = maintainer_cosigned(cfg, facts.cosign_target_row)
            if disc:
                cosign_info = {
                    "cosigned": True,
                    "by": disc["actor_name"],
                    "review_id": disc["review_id"],
                    "verdict": disc["verdict"],
                }
        out.append(
            ResolvedWitness(
                ref_kind=w.ref_kind, ref=w.ref, note=w.note, resolved=resolved,
                cosign_target_row=facts.cosign_target_row, cosign=cosign_info, facts=facts,
            )
        )
    return out


def _jsonable(row: dict[str, Any]) -> dict[str, Any]:
    """psycopg's dict_row hands back native Python types (datetime, Decimal, etc.) that FastAPI's
    default JSON encoder already knows how to serialize via pydantic/starlette's jsonable_encoder
    at the route layer -- this helper only normalizes the one type that encoder does not reach
    for a plain dict return (datetime -> isoformat), keeping every route's response a plain,
    already-JSON-safe dict rather than leaning on framework magic per call site (ADR-0012 P1)."""
    out: dict[str, Any] = {}
    for k, v in row.items():
        out[k] = v.isoformat() if hasattr(v, "isoformat") else v
    return out
