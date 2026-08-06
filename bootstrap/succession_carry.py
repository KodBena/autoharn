#!/usr/bin/env python3
"""succession_carry.py -- the automatic succession carry (design/BRIEF-SUCCESSION-CARRY-AND-
SCAFFOLD-HARDENING-2026-08-06.md, ledger rows 17/22/50/126-128). Invoked by bootstrap/
new-project.sh's --new-world birth sequence, as its OWN last step, when --succeeds
<predecessor-world> is given: carries the predecessor's durable-graded standing decisions and
open work items (with in-force dependency edges between carried items) into the just-birthed
successor, each re-asserted with a "re-asserted from <predecessor> ..." prefix -- reproducing
this same day's manual phoenix-step precedent (autoharn3->autoharn4, ledger rows 20/48, reviewed
independently at rows 51/123 -- 24/24 durable decisions, 68/68 open items, both bidirectionally
verified) as an automatic, refuse-teachably mechanism instead of a hand sweep a maintainer has to
remember and an operator can silently skip (row 126: "a service we should provide right now to
all autoharn users").

READ PATH -- direct schema read, never the boundary HTTP service:
  new-project.sh already holds direct psql/postgres access to HOST for this run's own DDL apply;
  this script reuses that SAME channel to read the predecessor's ledger, for two reasons the
  dispatching brief names explicitly: (1) the boundary daemon may not be running at birth time --
  a fresh newborn's own boundary is not started until first use (serving/ensure_running.py), and
  the PREDECESSOR's boundary may already be torn down mid-cutover; a carry mechanism that NEEDS a
  running daemon at exactly the moment a world is born is a fragile mechanism to make load-bearing
  for every future birth. (2) the boundary's own HTTP view pagination carries a known anomaly
  (ledger row 122: GET .../views/work_item_current?limit=2000 returned ONE row where limit=1000
  returned the full, stable set) -- a raw SQL SELECT issued here carries no LIMIT clause at all,
  so it is not merely a workaround for that bug, it is structurally outside the class of bug that
  produced it. Completeness is still independently re-verified below (see _fetch_* functions) --
  defense-in-depth against a bug in THIS script, never because this read path is suspected of the
  SAME serving-side defect.
  TRADEOFF, disclosed rather than silently assumed: this requires the predecessor's schema to live
  on the SAME postgres host/db as the newborn -- true of every --new-world/--succeeds use this
  project's own conventions produce (world/world_kernel/world_rw triples in one shared db). A
  cross-host succession is a named, un-built follow-on (it would need the boundary-HTTP path this
  script deliberately avoids, with its own completeness/pagination story re-solved).

WRITE PATH -- mirrors new-project.sh's own s40/s43/s60 birth-sequence pattern exactly (ADR-0012
  P1: one mechanism, not two drifting copies): SET ROLE to the newborn's granted role, then call
  kernel.ledger_write(jsonb) directly -- the SAME SECURITY DEFINER write boundary the birth
  sequence itself uses -- never through `led` (an HTTP client against a boundary that, again, may
  not be running yet for a newborn). Every write in this carry rides ONE database transaction:
  any failure anywhere (predecessor unreachable, a read that fails an internal completeness check,
  a single write the kernel refuses) rolls back the WHOLE transaction, so a failed carry leaves
  the newborn's ledger with ZERO partial carry rows -- never a half-carried state (item 4's
  "REFUSES TO COMPLETE" requirement). The transaction is committed only after every carried row
  has been accepted.

STAMPING -- composes with this same brief's Half-2 "birth-stamp honesty" fix: the newborn's own
  just-seeded/just-resolved stamp secret (passed in hex via --secret-hex, the SAME value
  new-project.sh's own birth-sequence writes mint their stamps from) is used to compute a fresh
  HMAC stamp exactly as hooks/stamp_intercept.py would, set via set_config(..., false)
  (session-scoped, verified live to survive across this script's own statement/transaction
  boundaries -- see set_stamp()'s own docstring) before any write -- so every carried row lands
  stamp_verified=true, never the env-u-PGOPTIONS fail-open class row 14/17 document.

OPT-OUT -- --opt-out-reason <text> skips the carry deliberately and instead records the opt-out
  itself, verbatim, as a stamped decision row in the newborn -- "whose use is itself recorded in
  the newborn's ledger" (item 4).
"""
from __future__ import annotations

import argparse
import hashlib
import hmac as hmac_mod
import json
import sys
import time
import uuid
from dataclasses import dataclass

import psycopg
from psycopg import sql


# =================================================================================================
# TYPED RECORDS (CLAUDE.md 2026-07-22 "no bare types" standing rule: every value construction goes
# through one SSOT that checks a contract appropriate to its use). Frozen dataclasses with
# validating __post_init__ for every domain value this script threads through its own carry logic
# -- never a bare dict/tuple passed between the fetch/write halves below.
# =================================================================================================

def _non_empty_str(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string, got {value!r}")
    return value


@dataclass(frozen=True)
class DurableDecision:
    """One predecessor durable-graded `decision` row, as read from its standing_decisions view."""
    source_id: int
    statement: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, int) or self.source_id <= 0:
            raise ValueError(f"DurableDecision.source_id must be a positive int, got {self.source_id!r}")
        _non_empty_str("DurableDecision.statement", self.statement)


@dataclass(frozen=True)
class OpenWorkItem:
    """One predecessor open work item, as read from its work_item_current view."""
    slug: str
    title: str
    parent_slug: str | None

    def __post_init__(self) -> None:
        _non_empty_str("OpenWorkItem.slug", self.slug)
        _non_empty_str("OpenWorkItem.title", self.title)
        if self.parent_slug is not None:
            _non_empty_str("OpenWorkItem.parent_slug", self.parent_slug)


_EDGE_TYPES = ("blocks-close", "blocks-start", "informs")


@dataclass(frozen=True)
class DependencyEdge:
    """One in-force work_depends_on edge between two CARRIED (both-open) predecessor items."""
    dependent_slug: str
    antecedent_slug: str
    edge_type: str

    def __post_init__(self) -> None:
        _non_empty_str("DependencyEdge.dependent_slug", self.dependent_slug)
        _non_empty_str("DependencyEdge.antecedent_slug", self.antecedent_slug)
        if self.edge_type not in _EDGE_TYPES:
            raise ValueError(f"DependencyEdge.edge_type must be one of {_EDGE_TYPES}, got {self.edge_type!r}")


@dataclass(frozen=True)
class StampContext:
    """A freshly-minted interception stamp, matching hooks/stamp_intercept.py's own HMAC formula
    byte-for-byte (kernel/lineage/s17-stamp-mechanism.sql's stamp_valid: HMAC-SHA256(secret,
    "session|agent|ts"))."""
    session: str
    agent: str
    ts: int
    hmac_hex: str
    invocation: str

    @classmethod
    def mint(cls, secret_hex: str, session: str, agent: str) -> "StampContext":
        try:
            key = bytes.fromhex(secret_hex)
        except ValueError as exc:
            raise ValueError(f"--secret-hex is not valid hex: {exc}") from exc
        if not key:
            raise ValueError("--secret-hex resolved to zero bytes -- no secret to stamp with")
        ts = int(time.time())
        digest = hmac_mod.new(key, f"{session}|{agent}|{ts}".encode(), hashlib.sha256).hexdigest()
        return cls(session=session, agent=agent, ts=ts, hmac_hex=digest, invocation=str(uuid.uuid4()))


@dataclass(frozen=True)
class WorldCoordinates:
    """A schema+kernel pair naming one world's ledger on a shared host/db -- the SAME derivation
    convention new-project.sh itself uses (world -> world / world_kernel), applied here to BOTH
    the predecessor and (implicitly, via CLI args) the newborn."""
    world: str
    schema: str
    kern: str

    def __post_init__(self) -> None:
        for label, value in (("world", self.world), ("schema", self.schema), ("kern", self.kern)):
            _non_empty_str(f"WorldCoordinates.{label}", value)


# =================================================================================================
# REFUSAL -- one home, teach-text, matching the surrounding scaffold's own "Nothing was touched
# beyond what already succeeded" posture. Every refusal here fires BEFORE the transaction commits
# (or, for the read-side checks, before any write has even been attempted), so the newborn's
# ledger carries zero partial carry rows on any of these paths.
# =================================================================================================

class SuccessionCarryRefused(Exception):
    pass


def refuse(msg: str) -> None:
    raise SuccessionCarryRefused(msg)


# =================================================================================================
# READ SIDE -- direct schema read against the predecessor, with an independent completeness
# cross-check on every fetch (module docstring, "READ PATH").
# =================================================================================================

def fetch_durable_decisions(cur: psycopg.Cursor, pred: WorldCoordinates) -> list[DurableDecision]:
    cur.execute(sql.SQL("SELECT id, statement FROM {}.standing_decisions ORDER BY id")
                .format(sql.Identifier(pred.schema)))
    view_rows = cur.fetchall()
    # Independent cross-check (mirrors ledger row 51's own dual-verification method): the raw
    # kind/decision_grade filter must name the IDENTICAL id set as the view -- a view that is
    # silently narrowing or widening its source is exactly the false-small/false-wide hazard a
    # completeness-dependent consumer like this carry must never trust on faith alone.
    cur.execute(sql.SQL(
        "SELECT id, statement FROM {}.ledger_current WHERE kind = 'decision' AND decision_grade = 'durable' ORDER BY id"
    ).format(sql.Identifier(pred.schema)))
    raw_rows = cur.fetchall()
    view_ids = {r[0] for r in view_rows}
    raw_ids = {r[0] for r in raw_rows}
    if view_ids != raw_ids:
        refuse(
            f"predecessor '{pred.world}': standing_decisions view ({sorted(view_ids)}) and the raw "
            f"kind='decision' AND decision_grade='durable' filter over ledger_current "
            f"({sorted(raw_ids)}) disagree on which rows are durable -- refusing rather than "
            f"silently trusting either set (a completeness hazard on the READ side, before any "
            f"write is attempted)."
        )
    return [DurableDecision(source_id=r[0], statement=r[1]) for r in view_rows]


def fetch_open_work_items(cur: psycopg.Cursor, pred: WorldCoordinates) -> list[OpenWorkItem]:
    cur.execute(sql.SQL(
        "SELECT slug, title, parent_slug FROM {}.work_item_current WHERE state = 'open' ORDER BY slug"
    ).format(sql.Identifier(pred.schema)))
    rows = cur.fetchall()
    # Defense-in-depth completeness self-check: a second, independently-phrased query (a plain
    # COUNT(*) over the identical predicate) must agree on cardinality with what was actually
    # fetched -- guards against a cursor/driver-level truncation bug in THIS script, not because
    # the underlying view is suspected of row-122's class of defect (a raw SELECT with no LIMIT
    # is not in that class at all -- see module docstring).
    cur.execute(sql.SQL("SELECT count(*) FROM {}.work_item_current WHERE state = 'open'")
                .format(sql.Identifier(pred.schema)))
    (n,) = cur.fetchone()
    if n != len(rows):
        refuse(
            f"predecessor '{pred.world}': work_item_current reports {n} open items by COUNT(*) but "
            f"the row fetch returned {len(rows)} -- refusing rather than carrying a possibly-"
            f"truncated set."
        )
    items = [OpenWorkItem(slug=r[0], title=r[1], parent_slug=r[2]) for r in rows]
    slugs = {i.slug for i in items}
    if len(slugs) != len(items):
        refuse(f"predecessor '{pred.world}': work_item_current returned a duplicate slug among its "
               f"open items -- refusing (this should be structurally impossible; the kernel's own "
               f"one-opening-act-per-slug invariant would have refused a duplicate at construction).")
    return items


def fetch_dependency_edges(cur: psycopg.Cursor, pred: WorldCoordinates,
                            carried: list[OpenWorkItem]) -> list[DependencyEdge]:
    """All in-force work_depends_on edges (every edge_type -- blocks-close, blocks-start, informs)
    whose BOTH endpoints are in the carried-open set; an edge with either endpoint outside that
    set stays behind, per the brief's own item 3 ("both endpoints open or the edge stays behind")."""
    open_slugs = {i.slug for i in carried}
    cur.execute(sql.SQL(
        "SELECT work_slug, work_depends_on, edge_type FROM {}.ledger_current WHERE kind = 'work_depends_on'"
    ).format(sql.Identifier(pred.schema)))
    rows = cur.fetchall()
    edges = []
    for dependent, antecedent, edge_type in rows:
        if dependent in open_slugs and antecedent in open_slugs:
            edges.append(DependencyEdge(dependent_slug=dependent, antecedent_slug=antecedent, edge_type=edge_type))
    return edges


def verify_predecessor_reachable(cur: psycopg.Cursor, pred: WorldCoordinates) -> None:
    try:
        cur.execute(sql.SQL("SELECT 1 FROM {}.standing_decisions LIMIT 1").format(sql.Identifier(pred.schema)))
        cur.fetchall()
        cur.execute(sql.SQL("SELECT 1 FROM {}.world_identity LIMIT 1").format(sql.Identifier(pred.kern)))
        cur.fetchall()
    except psycopg.Error as exc:
        refuse(
            f"predecessor '{pred.world}' (schema={pred.schema}, kern={pred.kern}) is unreachable or "
            f"missing an expected view -- {exc}. Nothing was carried; this run's own deployment.json "
            f"was NOT written. Pass --succession-opt-out '<reason>' to birth this world without a "
            f"carry (recorded, not silent), or fix the predecessor's reachability and re-run."
        )


# =================================================================================================
# WRITE SIDE -- mirrors new-project.sh's own s40/s43 birth-sequence write shape (module docstring,
# "WRITE PATH").
# =================================================================================================

def _write_verdict(cur: psycopg.Cursor, payload: dict) -> None:
    # NAMED HAZARD, FOUND AND FIXED IN REACH OF THIS EXACT LINE (rehearsal witness, this brief's
    # own commit): `SELECT (ledger_write(x)).*` WITHOUT a subquery wrapper is a documented
    # PostgreSQL footgun for a VOLATILE composite-returning function -- Postgres evaluates the
    # function call ONCE PER REFERENCED OUTPUT COLUMN when it cannot prove common-subexpression
    # elimination, so write_verdict's five columns (disposition/row_id/refusal_id/sqlstate/
    # message) meant `ledger_write` actually ran FIVE TIMES per call -- witnessed live during this
    # script's own rehearsal (five duplicate rows per single carried decision/edge, five write
    # attempts per work item with four refused-as-duplicate-slug). The subquery form below forces
    # exactly ONE evaluation (`ledger_write` runs once, in the inner SELECT; the outer SELECT only
    # destructures its already-computed result) -- verified live to land exactly one row per call.
    cur.execute("SELECT (v).* FROM (SELECT ledger_write(%s::jsonb) AS v) s", (json.dumps(payload),))
    disposition, row_id, refusal_id, sqlstate, message = cur.fetchone()
    if disposition != "accepted":
        refuse(f"write refused (SQLSTATE {sqlstate}, refusal row {refusal_id}): {message} "
               f"-- payload kind={payload.get('kind')!r}")


def set_stamp(cur: psycopg.Cursor, stamp: StampContext) -> None:
    """Sets the four app.vendor_* GUCs the s17 set_stamp trigger reads. SESSION-scoped (`false`),
    matching new-project.sh's own BIRTH_STAMP_SQL fix (NOT transaction-local `true` -- verified
    live that `true` evaporates the moment its own SELECT statement's implicit transaction ends
    under ordinary autocommit; `false` persists it for the rest of this connection's session,
    covering every write below regardless of how psycopg's own transaction boundaries fall)."""
    cur.execute(
        "SELECT set_config('app.vendor_session', %s, false), set_config('app.vendor_agent', %s, false), "
        "set_config('app.vendor_ts', %s, false), set_config('app.vendor_hmac', %s, false), "
        "set_config('app.vendor_invocation', %s, false)",
        (stamp.session, stamp.agent, str(stamp.ts), stamp.hmac_hex, stamp.invocation),
    )
    cur.fetchone()


def _toposort_by_parent(items: list[OpenWorkItem]) -> list[OpenWorkItem]:
    """Parents-before-children ordering (a work_opened row's own work_parent column requires the
    parent slug to already exist as an opened item at insert time -- s28's own dangling-parent
    guard). The source is acyclic by construction (s28's own cycle refusal on the predecessor),
    so this always terminates; a slug whose parent is NOT itself in the carried set is treated as
    a root here (its parent edge stays behind, per fetch/build_work_opened_payload below)."""
    by_slug = {i.slug: i for i in items}
    ordered: list[OpenWorkItem] = []
    placed: set[str] = set()
    remaining = list(items)
    while remaining:
        progressed = False
        still_remaining = []
        for item in remaining:
            parent_carried = item.parent_slug is not None and item.parent_slug in by_slug
            if not parent_carried or item.parent_slug in placed:
                ordered.append(item)
                placed.add(item.slug)
                progressed = True
            else:
                still_remaining.append(item)
        remaining = still_remaining
        if not progressed and remaining:
            # Structurally unreachable (source cycle would have been refused at construction) --
            # refuse loudly rather than loop forever or silently drop the remainder.
            refuse(f"work item parent chain did not resolve for slugs {[i.slug for i in remaining]} "
                   f"-- a cycle would already have been refused on the predecessor at construction; "
                   f"this should be unreachable.")
    return ordered


def carry_durable_decisions(cur: psycopg.Cursor, pred: WorldCoordinates, author_id: int,
                             decisions: list[DurableDecision]) -> int:
    for d in decisions:
        statement = f"re-asserted from {pred.world} row {d.source_id}: {d.statement}"
        _write_verdict(cur, {
            "kind": "decision", "statement": statement, "decision_grade": "durable", "actor": author_id,
        })
    return len(decisions)


def carry_open_work_items(cur: psycopg.Cursor, pred: WorldCoordinates, author_id: int,
                           items: list[OpenWorkItem]) -> int:
    open_slugs = {i.slug for i in items}
    for item in _toposort_by_parent(items):
        title = f"re-asserted from {pred.world}: {item.title}"
        payload = {
            "kind": "work_opened", "work_slug": item.slug, "work_title": title,
            "statement": f"work_opened: {item.slug} -- {title}", "actor": author_id,
        }
        if item.parent_slug is not None and item.parent_slug in open_slugs:
            payload["work_parent"] = item.parent_slug
        _write_verdict(cur, payload)
    return len(items)


def carry_dependency_edges(cur: psycopg.Cursor, pred: WorldCoordinates, author_id: int,
                            edges: list[DependencyEdge]) -> int:
    for e in edges:
        _write_verdict(cur, {
            "kind": "work_depends_on", "work_slug": e.dependent_slug, "work_depends_on": e.antecedent_slug,
            "edge_type": e.edge_type, "actor": author_id,
            "statement": (f"work_depends_on: {e.dependent_slug} -> {e.antecedent_slug} "
                           f"(edge_type={e.edge_type}, re-asserted from {pred.world})"),
        })
    return len(edges)


def record_opt_out(cur: psycopg.Cursor, pred: WorldCoordinates, author_id: int, reason: str) -> None:
    _write_verdict(cur, {
        "kind": "decision",
        "statement": (f"SUCCESSION OPT-OUT: this world's birth was scaffolded with --succeeds "
                       f"{pred.world} --succession-opt-out, deliberately DECLINING the automatic "
                       f"succession carry (design/BRIEF-SUCCESSION-CARRY-AND-SCAFFOLD-HARDENING-"
                       f"2026-08-06.md item 4) -- no durable decisions, open work items, or "
                       f"dependency edges were carried from {pred.world}. Operator-stated reason, "
                       f"verbatim: {reason}"),
        "actor": author_id,
    })


# =================================================================================================
# MAIN
# =================================================================================================

def _resolve_author_id(cur: psycopg.Cursor) -> int:
    cur.execute("SELECT id FROM principal WHERE name = 'author'")
    row = cur.fetchone()
    if row is None:
        refuse("newborn: no 'author' principal found -- this script must run AFTER new-project.sh's "
               "own s40 birth-sequence step 1 (author registration event), never before it.")
    return row[0]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="the automatic succession carry -- see module docstring")
    p.add_argument("--host", required=True)
    p.add_argument("--db", required=True)
    p.add_argument("--pred-schema", required=True)
    p.add_argument("--pred-kern", required=True)
    p.add_argument("--pred-world", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--kern", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--world", required=True)
    p.add_argument("--secret-hex", required=True)
    p.add_argument("--opt-out-reason", default=None)
    args = p.parse_args(argv)

    pred = WorldCoordinates(world=args.pred_world, schema=args.pred_schema, kern=args.pred_kern)
    newborn = WorldCoordinates(world=args.world, schema=args.schema, kern=args.kern)

    conninfo = f"host={args.host} dbname={args.db}"
    try:
        with psycopg.connect(conninfo, autocommit=False) as conn:
            with conn.cursor() as cur:
                if args.opt_out_reason:
                    # No predecessor read needed for an opt-out -- SET ROLE straight away (mirrors
                    # new-project.sh's own birth-sequence idiom exactly).
                    cur.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(args.role)))
                    cur.execute(sql.SQL("SET search_path = {}, {}").format(
                        sql.Identifier(newborn.schema), sql.Identifier(newborn.kern)))
                    stamp = StampContext.mint(args.secret_hex, session="succession-carry", agent="succession_carry.py")
                    set_stamp(cur, stamp)
                    author_id = _resolve_author_id(cur)
                    record_opt_out(cur, pred, author_id, args.opt_out_reason)
                    conn.commit()
                    print(f"succession_carry: opt-out recorded ('{args.opt_out_reason}') -- no carry performed "
                          f"from '{pred.world}'.")
                    return 0

                # READ SIDE FIRST, as the connecting OWNER, BEFORE any SET ROLE: the newborn's own
                # granted role (args.role) is deliberately UNGRANTED on the predecessor's schema
                # (the "many worlds" cross-world isolation this whole project's kernel enforces --
                # BACKLOG "Ruling: one world per run") -- SET ROLE-ing before this read would hit
                # exactly that isolation as a permission-denied error, witnessed live while
                # rehearsing this script (fixed here, not routed around). The owner connection
                # (no SET ROLE yet) can read across schemas on this shared host/db, matching the
                # SAME owner-direct-read posture new-project.sh's own world_identity seed uses.
                verify_predecessor_reachable(cur, pred)
                decisions = fetch_durable_decisions(cur, pred)
                items = fetch_open_work_items(cur, pred)
                edges = fetch_dependency_edges(cur, pred, items)

                # WRITE SIDE: only now SET ROLE to the newborn's own granted role (mirrors
                # new-project.sh's own birth-sequence idiom exactly) -- every write below goes
                # through the SAME SECURITY DEFINER write boundary the birth sequence itself used.
                cur.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(args.role)))
                cur.execute(sql.SQL("SET search_path = {}, {}").format(
                    sql.Identifier(newborn.schema), sql.Identifier(newborn.kern)))
                stamp = StampContext.mint(args.secret_hex, session="succession-carry", agent="succession_carry.py")
                set_stamp(cur, stamp)
                author_id = _resolve_author_id(cur)

                n_decisions = carry_durable_decisions(cur, pred, author_id, decisions)
                n_items = carry_open_work_items(cur, pred, author_id, items)
                n_edges = carry_dependency_edges(cur, pred, author_id, edges)

                conn.commit()
                print(f"succession_carry: carried {n_decisions} durable decision(s), {n_items} open work "
                      f"item(s), {n_edges} dependency edge(s) from '{pred.world}' into '{newborn.world}' "
                      f"(one transaction, committed).")
                return 0
    except SuccessionCarryRefused as exc:
        print(f"succession_carry.py: REFUSED -- {exc}", file=sys.stderr)
        print("  The transaction was rolled back (or never opened past this point) -- the newborn's "
              "ledger carries ZERO partial carry rows.", file=sys.stderr)
        return 1
    except psycopg.Error as exc:
        print(f"succession_carry.py: REFUSED -- unhandled database error: {exc}", file=sys.stderr)
        print("  The transaction was rolled back -- the newborn's ledger carries ZERO partial carry "
              "rows.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
