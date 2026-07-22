#!/usr/bin/env python3
"""acts_join -- the REAL acts.act <-> s15 MATCHING DERIVER (consult 25 §7, Increment-5; finding-4's
load-bearing work).

THE GAP THIS CLOSES. Increment 4 proved the acts<->ledger CONSUMER ARITHMETIC (ledger_acts.lp ASP vs
acts_edb.acts_floor_atoms SQL) on HAND-AUTHORED scratch side tables. It did NOT build the MATCHING: the
real s15 ledger carries NO `act_id` (its columns are evidence/refs/regards/enacts), so the row<->act
edge must be DERIVED from what the subject DID (`acts.act`, parsed by the CC adapter) against what it
RECORDED (the s15 ledger). This module is that derivation. It materializes the three EDB families the
consumers need -- `ledger_relevant_act/1`, `ledger_claim/2`, `ledger_ref/2` -- into a self-contained
JOIN schema, then runs the EXISTING two-producer consumer differential over it (ledger_acts.lp +
acts_edb.py stay BYTE-IDENTICAL; this module only feeds them derived, not hand-authored, edges).

THE DERIVATION (honest about its fuzziness -- F28, adjudication disposes; NEVER a silent hard match):
  - ledger_relevant_act(A) : oracle §4, applied per acts.act row -- plan_item_*/delegation_* are
      relevant; a tool_call that WRITES the fenced dir (Write/Edit/NotebookEdit under FENCED) is
      relevant; a READ tool_call, a message, a tool_result are NOT. (Mechanical, unambiguous.)
  - ledger_claim(R,T)      : a ledger row whose `evidence` names a fenced-dir path T -- an
      implementation-milestone claim. (Mechanical.)
  - ledger_ref(R,A)        : the DERIVED, inherently-FUZZY row<->act edge, by two named rules:
      * evidence edge (an act WITH a target -- a fenced write): A.target == R.evidence. CLEAN.
      * tag edge (an act WITHOUT a target -- plan/delegation): the act's TAG (a plan act's leading
        `stepN` token; a delegation act's `sub:`-stripped label) appears in R.refs' token set.
      Where no legible link exists the act is UNMATCHED -> it surfaces as unledgered_span, DESCRIPTIVE.
      The tag edge rests on the subject leaving a legible `refs` link; where it does not, the readout is
      "these acts were not individually ledgered" -- an honest descriptive finding, not a false match.
      HONEST BOUND ON WHAT THE TAG EDGE PROVES (finding-4 residual, out-of-frame audit): the s15
      contract defines `refs` as a FREE-TEXT reference with NO required token grammar, so the tag rule
      is a HEURISTIC, not a contract edge. Its EFFICACY is validated ONLY against the mock (whose refs
      were authored to carry `stepN`/`sub:`-labels); on a REAL e15 ledger with prose or empty refs it
      OVER-reports (plan/delegation acts show unledgered). The direction is FAIL-SAFE (over-report,
      descriptive, non-gating -- adjudication disposes), but "differential AGREE" certifies only that
      the two CONSUMERS agree on the edges THIS single deriver handed them, NEVER that the edges are
      the right ones. The real-refs efficacy is UNVALIDATED here and is link-27's to assess on the
      actual run. There is no contract-defined act reference to denominate this in (enacts/regards/
      amends are ROW->ROW bigint edges, not row->act), so the honest disposition is disclosure +
      routing to the maintainer/link-27, not a fabricated stronger matcher.

NON-FORECLOSURE (WORK-UNIT-exposure-discharge §1 -- INHERITED VERBATIM from ledger_acts.lp, which this
module FEEDS and does not touch): §1.1 the base relations are first-class #shown; §1.2 no verdict
vocabulary over the subject (claimed_without_act/unledgered_span/stale_attestation are statements about
the acts<->ledger GRAPH); §1.3 zero `:-` constraints; §1.4 no feedback edges (ledger_tnow/support/dto/
assumes byte-identical); §1.5 monotone base, NAF only at the labeled seam; §1.6 additive byte-identity
on all banked s10-s13/nla derivations (this module is never loaded for them).

Closure statement (ADR-0000 2026-07-02 amendment):
  - invariant: the three acts EDB families a consumer reads are DERIVED (never hand-authored) from
    `acts.act` + the s15 ledger, by mechanical classification (relevant/claim) and two NAMED,
    fuzzy-honest match rules (evidence + tag); an unmatched relevant act surfaces DESCRIPTIVELY as
    unledgered, never a fabricated match, never a silent drop.
  - quantification universe: act kinds {plan_item_*, delegation_*, tool_call(write|read), message_*,
    tool_result}; edge kinds {evidence-path, refs-tag}; ledger cols {evidence, refs, regards,
    supersedes, amends}; sources {mock synthetic schema, vsr s15 (read-only)}.
  - denomination: "ledgered" is denominated in a DERIVED ledger_ref edge (evidence-path OR refs-tag),
    never in a proxy (a timestamp coincidence, an id adjacency).

READ-ONLY on every source ledger (vsr/mock stay untouched). The only writes are to the apparatus-owned
JOIN schema in `epistemic`. Every import is top-of-file (lazy-import edict). NOT an evidence write.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from acts_edb import ACTS_PREDS, acts_edb, acts_floor_atoms
from clingo_run import run_clingo
from ledger_edb import resolve as resolve_ledger

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "filing"))
from pghost_resolve import resolve_pghost  # noqa: E402  (filing/pghost_resolve.py, the ONE home -- never a literal host default)

HERE = Path(__file__).resolve().parent
TNOW_LP = HERE / "lp" / "ledger_tnow.lp"
ACTS_LP = HERE / "lp" / "ledger_acts.lp"

HARNESS_PGHOST = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")  # unchanged precedence
HARNESS_DB = os.environ.get("HARNESS_DB", "harness")
EPISTEMIC_PGHOST = resolve_pghost("EPISTEMIC_PGHOST")  # unchanged precedence
FS, RS = "\x1f", "\x1e"

# oracle §4, one home (ADR-0012 P1) -- the ledger-relevant classification.
# DELIBERATE PARTIALITY vs oracle §4, marked at the site (ADR-0008/0013 R4, honest label): oracle §4
# also names the change-order-receipt `message_in` ledger-relevant AS A SPECIAL CASE (measurement (e)).
# It is NOT mechanized here because WHICH `message_in` is the change-order is not mechanically knowable
# from the act stream (any `message_in` could be one) -- so mechanizing it would fabricate an edge.
# Change-order handling is instead measured by `stale_attestation` (measurement (f), the currency of the
# countersign the change-order defeats), which IS mechanically grounded. So `ledger_relevant_act` here
# is oracle §4 MINUS the change-order clause, by design; the omission is named, not silent.
RELEVANT_KINDS = frozenset({"plan_item_created", "plan_item_updated", "plan_item_closed",
                            "delegation_spawn", "delegation_return"})
# A fenced WRITE is ledger-relevant. The Write/Edit/NotebookEdit tools name their target directly; a
# Bash-mediated write (printf/heredoc/tee > path) is ALSO a fenced write (finding 18) — the adapter sets
# a Bash act's target ONLY for a write-redirection (never a read), so a Bash tool_call carrying a fenced
# target is a write by that contract. `Bash` is therefore write-capable here, gated on _is_fenced(target).
WRITE_TOOLS = frozenset({"Write", "Edit", "NotebookEdit", "Bash"})


@dataclass(frozen=True)
class ActRow:
    id: int
    kind: str
    name: str
    target: str


@dataclass(frozen=True)
class LedgerRow:
    id: int
    kind: str
    statement: str
    evidence: str
    refs: str


@dataclass(frozen=True)
class Derivation:
    """The derived EDB families (id-keyed). The deriver's output; checked against the pre-registration."""
    relevant: dict[int, bool]                 # act id -> ledger-relevant (oracle §4)
    ledger_claim: list[tuple[int, str]]       # (ledger row id, fenced target)
    ledger_ref: list[tuple[int, int]]         # (ledger row id, act id)


def _is_fenced(target: str, fenced_prefix: str) -> bool:
    return bool(target) and target.startswith(fenced_prefix)


def act_tag(a: ActRow) -> str | None:
    """The legible tag a ledger row's `refs` would carry to account for a NON-write relevant act:
    a plan act's leading `stepN` token, a delegation act's `sub:`-stripped label. None for a write."""
    if a.kind.startswith("plan_item"):
        toks = a.name.split()
        return toks[0] if toks else None
    if a.kind.startswith("delegation"):
        return a.name[4:] if a.name.startswith("sub:") else a.name or None
    return None


def _refs_tokens(refs: str) -> set[str]:
    return {t for t in re.split(r"[,\s]+", refs or "") if t}


def derive(acts: list[ActRow], ledger: list[LedgerRow], fenced_prefix: str) -> Derivation:
    """The PURE derivation (testable in isolation, no DB). oracle §4 + the two named ref rules."""
    relevant: dict[int, bool] = {}
    for a in acts:
        rel = a.kind in RELEVANT_KINDS or (
            a.kind == "tool_call" and a.name in WRITE_TOOLS and _is_fenced(a.target, fenced_prefix))
        relevant[a.id] = rel

    ledger_claim = [(r.id, r.evidence) for r in ledger if _is_fenced(r.evidence, fenced_prefix)]

    ref: set[tuple[int, int]] = set()
    # evidence edge: a fenced-write act is referenced by a ledger row citing its target as evidence.
    writes = [a for a in acts if relevant[a.id] and a.target]
    for r in ledger:
        for a in writes:
            if r.evidence and r.evidence == a.target:
                ref.add((r.id, a.id))
    # tag edge: a plan/delegation act (no target) is referenced by a ledger row whose refs carries its tag.
    tagged = [(a, act_tag(a)) for a in acts if relevant[a.id] and not a.target]
    for r in ledger:
        toks = _refs_tokens(r.refs)
        for a, tag in tagged:
            if tag and tag in toks:
                ref.add((r.id, a.id))
    return Derivation(relevant=relevant, ledger_claim=sorted(ledger_claim),
                      ledger_ref=sorted(ref))


# ---- DB plumbing (read-only on sources; writes ONLY to the apparatus join schema) ----------------
def _psql(db: str, sql: str, host: str = EPISTEMIC_PGHOST) -> str:
    r = subprocess.run(["psql", "-h", host, "-d", db, "-tA", "-F", FS, "-R", RS, "-v",
                        "ON_ERROR_STOP=1", "-c", sql], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"psql {db} failed ({r.returncode}): {r.stderr.strip()}")
    return r.stdout


def _rows(db: str, sql: str, host: str = EPISTEMIC_PGHOST) -> list[list[str]]:
    out = _psql(db, sql, host)
    return [r.split(FS) for r in out.rstrip("\n").split(RS) if r.strip()]


def _has_relation(db: str, qualified: str) -> bool:
    return _psql(db, f"SELECT to_regclass('{qualified}') IS NOT NULL;").strip().startswith("t")


def _read_acts(acts_schema: str, run_id: str) -> list[ActRow]:
    """Read the parsed act stream for a run from the harness acts contract (READ-ONLY). id-is-order."""
    rows = _rows(HARNESS_DB,
                 f"SELECT id, kind, coalesce(name,''), coalesce(target,'') "
                 f'FROM "{acts_schema}".act WHERE run_id = {_q(run_id)} ORDER BY id;',
                 host=HARNESS_PGHOST)
    return [ActRow(int(i), k, n, t) for i, k, n, t in rows]


def _read_ledger(source_name: str) -> tuple[str, str, list[LedgerRow]]:
    """Read the source s15-shaped ledger (READ-ONLY). Returns (db, schema, rows). Resolved via the
    ledger_edb SSOT (special targets: e15->vsr; a plain name is a schema in epistemic)."""
    t = resolve_ledger(source_name)
    rows = _rows(t.db, f"SELECT id, kind, coalesce(statement,''), coalesce(evidence,''), "
                 f"coalesce(refs,'') FROM {t.schema}.ledger ORDER BY id;")
    return t.db, t.schema, [LedgerRow(int(i), k, s, e, rf) for i, k, s, e, rf in rows]


def _q(s: str) -> str:
    return "'" + (s or "").replace("'", "''") + "'"


def build_join(acts_schema: str, run_id: str, source_name: str, join_schema: str,
               fenced_prefix: str) -> Derivation:
    """Materialize a self-contained JOIN schema in `epistemic`: a snapshot of the source ledger + the
    acts stream with DERIVED `relevant` + the DERIVED ledger_ref/ledger_claim. The source ledger is
    NEVER modified. Returns the Derivation (also queryable from the join schema)."""
    src_db, src_schema, ledger = _read_ledger(source_name)
    acts = _read_acts(acts_schema, run_id)
    d = derive(acts, ledger, fenced_prefix)

    # (re)create the join schema -- s15-shaped ledger + the three acts side tables the consumers read.
    _psql("epistemic", f'DROP SCHEMA IF EXISTS "{join_schema}" CASCADE; CREATE SCHEMA "{join_schema}";')  # declared-drop: {join_schema} (declared scratch/test reset; blast radius = this schema only)
    _psql("epistemic", f"""
      CREATE TABLE "{join_schema}".ledger (
        id bigint PRIMARY KEY, ts timestamptz NOT NULL DEFAULT now(), kind text NOT NULL,
        concern text, status text, confidence text, statement text, rationale text, actor text,
        supersedes bigint, enacts bigint[], answers bigint, amends bigint, amends_scope text,
        regards bigint, evidence text, refs text);
      CREATE TABLE "{join_schema}".acts (id bigint PRIMARY KEY, kind text NOT NULL, name text,
        target text, relevant boolean NOT NULL);
      CREATE TABLE "{join_schema}".ledger_ref (row_id bigint NOT NULL, act_id bigint NOT NULL);
      CREATE TABLE "{join_schema}".ledger_claim (row_id bigint NOT NULL, target text NOT NULL);
      CREATE TABLE "{join_schema}".review_detail (ledger_id bigint PRIMARY KEY, verdict text NOT NULL);""")

    # snapshot review_detail (verdict-aware staleness, finding 29) if the source carries it (s15 kernel
    # does; a lean/nla source does not — the table stays empty, stale_attest/nonattest simply don't fire).
    if _has_relation(src_db, f"{src_schema}.review_detail"):
        for rid, verdict in _rows(src_db, f"SELECT ledger_id, verdict FROM {src_schema}.review_detail ORDER BY ledger_id;"):
            _psql("epistemic", f'INSERT INTO "{join_schema}".review_detail (ledger_id, verdict) '
                  f"VALUES ({int(rid)}, {_q(verdict)});")

    # snapshot the ledger (all columns the downstream reads -- ledger_edb + acts_edb.regards/evidence).
    src_rows = _rows(src_db, f"SELECT id, extract(epoch FROM ts)::bigint, kind, "
                     f"coalesce(concern,''), coalesce(status,''), coalesce(confidence,''), "
                     f"coalesce(statement,''), coalesce(supersedes::text,''), "
                     f"coalesce(enacts::text,''), coalesce(answers::text,''), "
                     f"coalesce(amends::text,''), coalesce(amends_scope,''), "
                     f"coalesce(regards::text,''), coalesce(evidence,''), coalesce(refs,'') "
                     f"FROM {src_schema}.ledger ORDER BY id;")
    for (i, ep, k, con, st, cf, stmt, sup, en, ans, am, ams, reg, ev, rf) in src_rows:
        cols = (f"INSERT INTO \"{join_schema}\".ledger "
                f"(id, ts, kind, concern, status, confidence, statement, supersedes, enacts, "
                f"answers, amends, amends_scope, regards, evidence, refs) VALUES ("
                f"{int(i)}, to_timestamp({int(ep)}), {_q(k)}, "
                f"{('NULL' if con=='' else _q(con))}, {('NULL' if st=='' else _q(st))}, "
                f"{('NULL' if cf=='' else _q(cf))}, {_q(stmt)}, "
                f"{('NULL' if sup=='' else int(sup))}, "
                f"{('NULL' if en=='' else _q(en)+'::bigint[]')}, "
                f"{('NULL' if ans=='' else int(ans))}, {('NULL' if am=='' else int(am))}, "
                f"{('NULL' if ams=='' else _q(ams))}, {('NULL' if reg=='' else int(reg))}, "
                f"{('NULL' if ev=='' else _q(ev))}, {('NULL' if rf=='' else _q(rf))});")
        _psql("epistemic", cols)

    for a in acts:
        _psql("epistemic", f'INSERT INTO "{join_schema}".acts (id, kind, name, target, relevant) '
              f"VALUES ({a.id}, {_q(a.kind)}, {('NULL' if a.name=='' else _q(a.name))}, "
              f"{('NULL' if a.target=='' else _q(a.target))}, {str(d.relevant[a.id]).lower()});")
    for rid, tgt in d.ledger_claim:
        _psql("epistemic", f'INSERT INTO "{join_schema}".ledger_claim (row_id, target) '
              f"VALUES ({rid}, {_q(tgt)});")
    for rid, aid in d.ledger_ref:
        _psql("epistemic", f'INSERT INTO "{join_schema}".ledger_ref (row_id, act_id) '
              f"VALUES ({rid}, {aid});")
    return d


# ---- the consumer differential over the join schema (reuses ledger_acts.lp + acts_edb, unchanged) --
@dataclass(frozen=True)
class ConsumerResult:
    verdict: str                          # AGREE | DIVERGE | QUARANTINED
    asp: set[str]
    sql: set[str]
    detail: str


def differential(join_schema: str) -> ConsumerResult:
    """Run BOTH producers over the join schema and compare. AGREE iff the acts-vocabulary atom sets
    are identical (the substance of the differential -- two independent code paths agreeing)."""
    try:
        edb = acts_edb(join_schema)
        asp = {a for a in run_clingo([TNOW_LP, ACTS_LP], edb)
               if "(" in a and a.split("(", 1)[0] in ACTS_PREDS}
        sql = acts_floor_atoms(join_schema)
    except Exception as e:  # noqa: BLE001 -- a crash QUARANTINES (never a silent empty; F49/ADR-0015 R3)
        return ConsumerResult("QUARANTINED", set(), set(), f"{type(e).__name__}: {e}")
    only_asp, only_sql = asp - sql, sql - asp
    if only_asp or only_sql:
        return ConsumerResult("DIVERGE", asp, sql,
                              f"only_asp={sorted(only_asp)} only_sql={sorted(only_sql)}")
    return ConsumerResult("AGREE", asp, sql, f"{len(asp)} acts-atoms agree")


def consumer_atoms(result: ConsumerResult, pred: str) -> list[str]:
    return sorted(a for a in result.asp if a.startswith(pred + "("))


# ---- close_manifest entry point (the three consumers, LIVE MANDATORY -- promoted from DEFERRED) ----
def run_close(acts_schema: str, run_id: str, source_name: str, join_schema: str,
              fenced_prefix: str) -> tuple[int, list[tuple[str, str, str]]]:
    """Build the join + run the differential for close_manifest. Returns (exit_code, per-consumer
    [(name, status, detail)]). exit != 0 iff a consumer QUARANTINES or the differential DIVERGES (an
    instrument defect -- F49 loud). A FINDING atom is DESCRIPTIVE data (non-foreclosure §1.3) and does
    NOT gate red; only a crash/divergence does. This REPLACES the Increment-4 NOT-WIRED placeholder."""
    try:
        build_join(acts_schema, run_id, source_name, join_schema, fenced_prefix)
    except Exception as e:  # noqa: BLE001
        return 1, [(c, "QUARANTINED", f"deriver failed to build join: {type(e).__name__}: {e}")
                   for c in ("stale_attestation", "claimed_without_act", "unledgered_span")]
    res = differential(join_schema)
    if res.verdict == "QUARANTINED":
        return 1, [(c, "QUARANTINED", res.detail)
                   for c in ("stale_attestation", "claimed_without_act", "unledgered_span")]
    if res.verdict == "DIVERGE":
        return 1, [(c, "QUARANTINED", f"ASP<->SQL DIVERGE (instrument defect): {res.detail}")
                   for c in ("stale_attestation", "claimed_without_act", "unledgered_span")]
    out = []
    for c in ("stale_attestation", "claimed_without_act", "unledgered_span"):
        atoms = consumer_atoms(res, c)
        out.append((c, "OK", f"{len(atoms)} finding(s): {atoms if atoms else '(none)'} "
                    f"[DESCRIPTIVE — adjudication disposes; does not gate]"))
    return 0, out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Derive the acts<->s15 join and run the consumer differential.")
    ap.add_argument("--acts-schema", default="acts")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--source", required=True, help="the source s15 ledger target name (e15 | a schema)")
    ap.add_argument("--join-schema", required=True)
    ap.add_argument("--fenced", required=True, help="the fenced-dir path prefix (e.g. /synthetic/nk4-mock)")
    ap.add_argument("--close", action="store_true", help="close_manifest mode: per-consumer status + exit code")
    args = ap.parse_args(argv)
    if args.close:
        code, rows = run_close(args.acts_schema, args.run_id, args.source, args.join_schema, args.fenced)
        for name, status, detail in rows:
            print(f"acts:{name:19} {status:12} {detail}")
        return code
    d = build_join(args.acts_schema, args.run_id, args.source, args.join_schema, args.fenced)
    res = differential(args.join_schema)
    print(f"# acts<->s15 join built: {sum(d.relevant.values())} relevant acts, "
          f"{len(d.ledger_claim)} claims, {len(d.ledger_ref)} refs")
    print(f"# consumer differential: {res.verdict} ({res.detail})")
    for pred in ("stale_attestation", "claimed_without_act", "unledgered_span"):
        print(f"  {pred:22} {consumer_atoms(res, pred) or '(none)'}")
    return 0 if res.verdict == "AGREE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
