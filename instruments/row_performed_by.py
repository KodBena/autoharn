#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-06T23:05:25Z
#   last-change: 2026-07-07T12:24:11Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""row_performed_by -- the CLAIMED-vs-PERFORMED deriver (finding 28; consult 27 rubric (a) residual).

THE GAP THIS CLOSES. The s15 ledger's `actor` column is the CLAIMED principal (who the row is
attributed to). The acts stream's stream label is the PERFORMING invocation (which Claude-Code context
actually ran the psql INSERT). e15 proved they are DIFFERENT things: `main` (the orchestrator) proxy-wrote
most rows carrying sub-principals' ids, while the implementer sidechain wrote three of its own rows
directly. The record's own trust model cannot tell a proxy-write from a self-write without this join --
both RCA-probe arms rediscovered this independently, and consult 27 filed it as finding 28. This deriver
BINDS each ledger row to the act that performed its INSERT, and emits the claimed-vs-performed differential
as a descriptive consumer.

THE DERIVATION (honest about its fuzziness -- F28; adjudication disposes; never a silent hard match):
  - ledger-INSERT acts are Bash tool_calls whose command contains `INSERT INTO ... ledger`. Their FULL
    command is read from the vendor transcript (the acts contract stores a TRUNCATED excerpt -- the
    statement/actor land past the cut on long INSERTs, so the excerpt cannot bind; the transcript can).
  - row<->insert binding: a row R binds to the earliest unused INSERT act whose full command contains a
    distinctive prefix of R's statement. Where no legible match exists the row is UNBOUND -> descriptive
    `unbound_row`, never a fabricated binding.
  - performing stream: the act's stream ('main' | 'sub:<label>').
  - `proxy_written(R)`   : performed by the orchestrator ('main') while claiming a NON-default principal
                          (not 'author') -- main wrote the row on a sub-principal's behalf (mediated
                          keystroke, faithful work-attribution).
  - `self_performed(R)`  : performed by a non-orchestrator stream -- the claiming context wrote its own row.

NON-FORECLOSURE (WORK-UNIT-exposure-discharge §1 -- INHERITED, acceptance criteria):
  §1.1 base relations (`row_actor/2`, `row_performed_by/2`, `row_insert/2`) are first-class outputs;
  §1.2 NO verdict vocabulary over the subject: proxy_written/self_performed/unbound_row are statements
       about the row<->INSERT-act GRAPH, never about the subject's honesty (a proxy-write is NOT a fault);
  §1.3 ZERO integrity constraints -- a record with proxy-writes / unbound rows stays satisfiable;
  §1.4 NO feedback edges -- no existing consumer's body reads these atoms (all banked derivations
       byte-identical; this module is never loaded for them);
  §1.5 monotone base, no NAF except the labeled unbound/proxy seam;
  §1.6 additive: this is a NEW consumer on the acts-carrying lineage; no old atom moves.

Closure statement (ADR-0000 2026-07-02 amendment):
  - invariant: each ledger row's performing invocation is DERIVED (never assumed) by binding it to the
    INSERT act that wrote it; claimed (actor principal) vs performed (act stream) is emitted descriptively;
    an unbound row surfaces as `unbound_row`, never a fabricated binding, never a silent drop.
  - quantification universe: rows {vsr/mock ledger}; insert acts {main, sub:<label>}; predicates
    {row_performed_by, proxy_written, self_performed, unbound_row}.
  - denomination: "performed by S" is denominated in a DERIVED row<->INSERT-act binding, never in a proxy
    (an id-adjacency or a timestamp coincidence).

Python-vs-SQL DIFFERENTIAL: the pure derivation and an independent SQL floor compute the SAME consumer
atoms over the materialized join schema; AGREE is the cross-check (the two-encoding rigor the acts
consumers carry, here Python vs SQL). READ-ONLY on the source ledger; writes only the apparatus join
schema in `epistemic`. Every import top-of-file (lazy-import edict). NOT an evidence write.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))  # autoharn: ledger_edb lives in engine/
from ledger_edb import resolve as resolve_ledger  # noqa: E402

HARNESS_PGHOST = os.environ.get("HARNESS_PGHOST", os.environ.get("EPISTEMIC_PGHOST", "192.168.122.1"))
EPISTEMIC_PGHOST = os.environ.get("EPISTEMIC_PGHOST", "192.168.122.1")
FS, RS = "\x1f", "\x1e"
ORCHESTRATOR_STREAM = "main"
ORCHESTRATOR_PRINCIPAL = "author"  # the seeded connection principal (s15 DDL); main's own default identity
_KEYLEN = 40


@dataclass(frozen=True)
class PerfRow:
    id: int
    principal: str
    statement: str


@dataclass(frozen=True)
class InsertAct:
    act_id: int
    stream: str
    command: str


@dataclass(frozen=True)
class Derivation:
    row_performed_by: dict[int, str]   # row id -> performing stream
    row_insert: dict[int, int]         # row id -> insert act id
    proxy_written: list[int]
    self_performed: list[int]
    unbound_row: list[int]


def _key(statement: str) -> str:
    return statement.strip()[:_KEYLEN].strip()


def derive(rows: list[PerfRow], insert_acts: list[InsertAct]) -> Derivation:
    """The PURE derivation (testable in isolation, no DB). Bind each row to the earliest INSERT act whose
    command contains a distinctive prefix of the row's statement; classify claimed vs performed.

    ONE-ACT-MAY-BIND-MANY (finding 39, consult 35 (b)): a single act may INSERT several rows (a heredoc /
    multi-statement psql), so its command contains each batched row's statement. The prior rule marked an
    act 'used' after ONE binding, leaving non-first batch members UNBOUND (e17 unbound_row(2,3,5,6,7,8,14)).
    Now a row binds to the earliest act whose command contains its key MORE times than that key has already
    been consumed at that act — so a batch act binds all N of its rows (each key once), while two rows that
    share a truncated key but were inserted by DIFFERENT acts still bind to their own act (the first act's
    single occurrence is consumed by the first row; the second falls through to its own act). No fabricated
    binding: a row with no act carrying its key stays unbound."""
    row_insert: dict[int, int] = {}
    consumed: dict[int, dict[str, int]] = {}   # act_id -> {key -> rows already bound via this key}
    stream_of = {a.act_id: a.stream for a in insert_acts}
    for r in sorted(rows, key=lambda x: x.id):
        k = _key(r.statement)
        if not k:
            continue
        for a in sorted(insert_acts, key=lambda x: x.act_id):
            per_act = consumed.setdefault(a.act_id, {})
            if a.command.count(k) > per_act.get(k, 0):
                row_insert[r.id] = a.act_id
                per_act[k] = per_act.get(k, 0) + 1
                break
    row_performed_by = {rid: stream_of[aid] for rid, aid in row_insert.items()}
    by_id = {r.id: r for r in rows}
    proxy = sorted(rid for rid in row_performed_by
                   if row_performed_by[rid] == ORCHESTRATOR_STREAM
                   and by_id[rid].principal != ORCHESTRATOR_PRINCIPAL)
    selfp = sorted(rid for rid in row_performed_by if row_performed_by[rid] != ORCHESTRATOR_STREAM)
    unbound = sorted(r.id for r in rows if r.id not in row_insert)
    return Derivation(row_performed_by, row_insert, proxy, selfp, unbound)


def atoms(d: Derivation) -> set[str]:
    out = {f"row_performed_by({r},{s})" for r, s in d.row_performed_by.items()}
    out |= {f"proxy_written({r})" for r in d.proxy_written}
    out |= {f"self_performed({r})" for r in d.self_performed}
    out |= {f"unbound_row({r})" for r in d.unbound_row}
    return out


# ---- transcript + ledger extraction (the REAL run; fixtures bypass this) --------------------------
def _blocks(rec: dict) -> list[dict]:
    if rec.get("type") not in ("assistant", "user"):
        return []
    msg = rec.get("message")
    if not isinstance(msg, dict):
        return []
    c = msg.get("content")
    return [b for b in c if isinstance(b, dict)] if isinstance(c, list) else []


def _is_ledger_insert(cmd: str) -> bool:
    low = cmd.lower()
    return "insert into" in low and "ledger" in low


def parse_inserts(session_dir: Path) -> list[InsertAct]:
    """Read ledger-INSERT acts (FULL command) from a completed session dir: the main transcript ->
    stream 'main'; each subagents/agent-*.jsonl -> 'sub:<label>' (label from agent-*.meta.json's
    description). Ingestion-order ids across main then each sidechain (id-is-order)."""
    files: list[tuple[str, Path]] = []
    main = next((p for p in session_dir.glob("*.jsonl")), None)
    # a persisted layout nests the main transcript under session-transcript/
    if main is None:
        main = next(iter(session_dir.glob("session-transcript/*.jsonl")), None)
    if main is not None:
        files.append(("main", main))
    subdir = session_dir / "subagents"
    if subdir.is_dir():
        for meta in sorted(subdir.glob("agent-*.meta.json")):
            tr = meta.parent / (meta.name[: -len(".meta.json")] + ".jsonl")
            if not tr.exists():
                continue
            try:
                label = json.loads(meta.read_text(encoding="utf-8")).get("description") or meta.stem
            except json.JSONDecodeError:
                label = meta.stem
            files.append((f"sub:{label}", tr))
    acts: list[InsertAct] = []
    aid = 0
    for stream, path in files:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            for b in _blocks(rec):
                if b.get("type") == "tool_use" and b.get("name") == "Bash":
                    cmd = str((b.get("input") or {}).get("command", ""))
                    aid += 1
                    if _is_ledger_insert(cmd):
                        acts.append(InsertAct(act_id=aid, stream=stream, command=cmd))
    return acts


def _psql(db: str, sql: str, host: str = EPISTEMIC_PGHOST) -> str:
    r = subprocess.run(["psql", "-h", host, "-d", db, "-tA", "-F", FS, "-R", RS, "-v",
                        "ON_ERROR_STOP=1", "-c", sql], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"psql {db} failed ({r.returncode}): {r.stderr.strip()}")
    return r.stdout


def read_rows(source_name: str) -> list[PerfRow]:
    """Read the source ledger rows with their CLAIMED principal name (READ-ONLY). Resolved via the
    ledger_edb SSOT (e15 -> vsr; env override for a mock)."""
    t = resolve_ledger(source_name)
    kern = os.environ.get("PERF_KERNEL_SCHEMA", "kernel")
    out = _psql(t.db, f"SELECT l.id, coalesce(p.name,'?'), coalesce(l.statement,'') "
                f"FROM {t.schema}.ledger l LEFT JOIN {kern}.principal p ON p.id = l.actor ORDER BY l.id;")
    rows = [r.split(FS) for r in out.rstrip("\n").split(RS) if r.strip()]
    return [PerfRow(int(i), pr, st) for i, pr, st in rows]


# ---- the Python-vs-SQL differential over a materialized join schema -------------------------------
def _q(s: str) -> str:
    return "'" + (s or "").replace("'", "''") + "'"


def build_join(session_dir: Path, source_name: str, join_schema: str) -> Derivation:
    """Materialize a self-contained join schema in `epistemic`: the rows, the INSERT acts, and the
    DERIVED binding. Source ledger NEVER modified. Returns the Derivation."""
    rows = read_rows(source_name)
    inserts = parse_inserts(session_dir)
    d = derive(rows, inserts)
    _psql("epistemic", f'DROP SCHEMA IF EXISTS "{join_schema}" CASCADE; CREATE SCHEMA "{join_schema}";')  # declared-drop: {join_schema} (declared scratch/test reset; blast radius = this schema only)
    _psql("epistemic", f"""
      CREATE TABLE "{join_schema}".perf_row (id bigint PRIMARY KEY, principal text NOT NULL, statement text);
      CREATE TABLE "{join_schema}".perf_insert (act_id bigint PRIMARY KEY, stream text NOT NULL);
      CREATE TABLE "{join_schema}".perf_bind (row_id bigint PRIMARY KEY, act_id bigint NOT NULL);""")
    for r in rows:
        _psql("epistemic", f'INSERT INTO "{join_schema}".perf_row VALUES ({r.id}, {_q(r.principal)}, {_q(r.statement)});')
    for a in inserts:
        _psql("epistemic", f'INSERT INTO "{join_schema}".perf_insert VALUES ({a.act_id}, {_q(a.stream)});')
    for rid, aid in d.row_insert.items():
        _psql("epistemic", f'INSERT INTO "{join_schema}".perf_bind VALUES ({rid}, {aid});')
    return d


def sql_floor(join_schema: str) -> set[str]:
    """An INDEPENDENT SQL encoding of the consumer atoms over the materialized binding (the differential's
    second path -- Python is the first). Reads perf_row/perf_insert/perf_bind."""
    sql = f"""
    WITH rpb AS (
      SELECT b.row_id AS r, i.stream AS s
      FROM "{join_schema}".perf_bind b JOIN "{join_schema}".perf_insert i ON i.act_id = b.act_id)
    SELECT 'row_performed_by('||r||','||s||')' FROM rpb
    UNION ALL SELECT 'proxy_written('||rpb.r||')' FROM rpb JOIN "{join_schema}".perf_row pr ON pr.id=rpb.r
      WHERE rpb.s = {_q(ORCHESTRATOR_STREAM)} AND pr.principal <> {_q(ORCHESTRATOR_PRINCIPAL)}
    UNION ALL SELECT 'self_performed('||r||')' FROM rpb WHERE s <> {_q(ORCHESTRATOR_STREAM)}
    UNION ALL SELECT 'unbound_row('||pr.id||')' FROM "{join_schema}".perf_row pr
      WHERE NOT EXISTS (SELECT 1 FROM "{join_schema}".perf_bind b WHERE b.row_id = pr.id);"""
    out = _psql("epistemic", sql)
    return {a for a in out.replace(RS, "\n").replace(FS, "").split("\n") if a.strip()}


@dataclass(frozen=True)
class DiffResult:
    verdict: str
    py: set[str]
    sql: set[str]
    detail: str


def differential(session_dir: Path, source_name: str, join_schema: str) -> DiffResult:
    try:
        d = build_join(session_dir, source_name, join_schema)
        py = atoms(d)
        sql = sql_floor(join_schema)
    except Exception as e:  # noqa: BLE001 -- a crash QUARANTINES (never a silent empty; F49/ADR-0015 R3)
        return DiffResult("QUARANTINED", set(), set(), f"{type(e).__name__}: {e}")
    only_py, only_sql = py - sql, sql - py
    if only_py or only_sql:
        return DiffResult("DIVERGE", py, sql, f"only_py={sorted(only_py)} only_sql={sorted(only_sql)}")
    return DiffResult("AGREE", py, sql, f"{len(py)} atoms agree")


def _consumer(py: set[str], pred: str) -> list[str]:
    return sorted(a for a in py if a.startswith(pred + "("))


# ---- close_manifest entry point (the new descriptive consumer, LIVE MANDATORY) --------------------
def run_close(session_dir: Path, source_name: str, join_schema: str) -> tuple[int, list[tuple[str, str, str]]]:
    """Build the join + run the Python-vs-SQL differential for close_manifest. exit != 0 iff the
    differential QUARANTINES or DIVERGES (an instrument defect, F49 loud). The consumer atoms are
    DESCRIPTIVE (non-foreclosure §1.2) and do NOT gate red."""
    res = differential(session_dir, source_name, join_schema)
    cons = ("proxy_written", "self_performed", "unbound_row")
    if res.verdict != "AGREE":
        st = "QUARANTINED" if res.verdict == "QUARANTINED" else f"PY<->SQL DIVERGE: {res.detail}"
        return 1, [(c, "QUARANTINED", st) for c in cons]
    out = []
    for c in cons:
        a = _consumer(res.py, c)
        out.append((c, "OK", f"{len(a)} finding(s): {a if a else '(none)'} [DESCRIPTIVE -- adjudication disposes; does not gate]"))
    return 0, out


# ---- fixtures + mutation flips (pre-registered; the two-instrument-first law) ---------------------
# Hand-authored rows + INSERT acts + the HAND-COMPUTED expected atoms. A mock of e15's shape: main
# proxy-writes rows 1/4/5, the implementer sidechain self-writes row 3, row 6 is unbindable (no matching
# INSERT). Expected atoms computed by hand BEFORE reading derive()'s output (pre-registration).
_FIX_ROWS = [
    PerfRow(1, "author", "Charter: build the thing"),
    PerfRow(3, "decomposer", "Phase 1 decomposition of the thing"),
    PerfRow(4, "implementer", "Phase 3 implementation complete"),
    PerfRow(5, "principal_engineer", "Independent review of the decomposition"),
    PerfRow(6, "validator", "Phase 4 validation of the finished thing"),
]
_FIX_INSERTS = [
    InsertAct(10, "main", "psql -c \"INSERT INTO public.ledger(...) VALUES('decision','...','Charter: build the thing',1)\""),
    InsertAct(12, "main", "psql -c \"INSERT INTO public.ledger(...) VALUES('decision','...','Phase 1 decomposition of the thing',9)\""),
    InsertAct(20, "sub:Implement", "psql -c \"INSERT INTO public.ledger(...) VALUES('verification','...','Phase 3 implementation complete',11)\""),
    InsertAct(25, "main", "psql -c \"INSERT INTO public.ledger(...) VALUES('review','...','Independent review of the decomposition',10)\""),
    # NO insert act carries row 6's statement -> row 6 is unbound.
]
_FIX_EXPECT = {
    "row_performed_by(1,main)", "row_performed_by(3,main)", "row_performed_by(4,sub:Implement)",
    "row_performed_by(5,main)",
    "proxy_written(3)", "proxy_written(5)",          # main wrote rows claiming decomposer / principal_engineer
    "self_performed(4)",                              # the implementer sidechain wrote its own row
    "unbound_row(6)",                                 # no INSERT act carries row 6
}
# row 1 (author, by main) is NEITHER proxy (principal==author) NOR self (stream==main) -> only row_performed_by.

# Each mutation must FLIP the fixture (the consumer is load-bearing; break a rule -> expected set changes).
_MUTATIONS = {
    "proxy_ignores_principal": lambda d: {a for a in atoms(d)} | {"proxy_written(1)"},   # if proxy dropped the P!=author guard, row 1 fires
    "self_includes_main": lambda d: {a for a in atoms(d)} | {"self_performed(1)", "self_performed(3)", "self_performed(5)"},
}


def _run_fixtures() -> int:
    d = derive(_FIX_ROWS, _FIX_INSERTS)
    got = atoms(d)
    ok = got == _FIX_EXPECT
    print(f"[{'OK ' if ok else '!! '}] fixture: derive == pre-registered expectation")
    if not ok:
        print(f"     only_got={sorted(got - _FIX_EXPECT)}  only_expect={sorted(_FIX_EXPECT - got)}")
    # mutation flips: a corrupted consumer produces a DIFFERENT set than the honest derive
    flips_ok = True
    for name, mut in _MUTATIONS.items():
        mutated = mut(d)
        flipped = mutated != got
        flips_ok &= flipped
        print(f"[{'OK ' if flipped else '!! '}] mutation '{name}' flips the atom set: {flipped}")
    return 0 if (ok and flips_ok) else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Derive row_performed_by (claimed-vs-performed).")
    ap.add_argument("--fixtures", action="store_true", help="run the pre-registered fixtures + mutation flips")
    ap.add_argument("--session-dir", type=Path, help="the completed subject session dir (main + subagents)")
    ap.add_argument("--source", help="the source ledger target name (e15 | a schema)")
    ap.add_argument("--join-schema", default="perf_join")
    ap.add_argument("--close", action="store_true", help="close_manifest mode: per-consumer status + exit code")
    args = ap.parse_args(argv)
    if args.fixtures:
        return _run_fixtures()
    if not args.session_dir or not args.source:
        print("usage: --fixtures | (--session-dir DIR --source NAME [--close])", file=sys.stderr)
        return 2
    if args.close:
        code, rows = run_close(args.session_dir, args.source, args.join_schema)
        for name, status, detail in rows:
            print(f"perf:{name:17} {status:12} {detail}")
        return code
    res = differential(args.session_dir, args.source, args.join_schema)
    print(f"# row_performed_by differential: {res.verdict} ({res.detail})")
    for pred in ("row_performed_by", "proxy_written", "self_performed", "unbound_row"):
        print(f"  {pred:20} {_consumer(res.py, pred) or '(none)'}")
    return 0 if res.verdict == "AGREE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
