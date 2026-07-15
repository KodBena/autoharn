#!/usr/bin/env python3
"""observed_currency — reference truth at the moment of citation (FINDINGS F42, consult 17 §2.3/§6
item 6). The e12 law, made mechanical: a citation is trustworthy only if the cited id was OBSERVED
by the subject — in a read-back whose result set actually contained it — within the window before
the citing INSERT. Observed ids were cited correctly in e12; the one DERIVED id (row 31's enacts=27,
computed under "max id = 26") was miscited, and alias_surface caught it only by the luck of 27 being
a note. This instrument catches the class REGARDLESS of the target's kind — the hole alias_surface's
kind-dependence leaves open.

The discriminating mechanism e12 exposed (consult 17 §2.3): the subject's resume read-backs were
KIND-FILTERED (`kind IN ('question','decision')` — rows 27/28, notes, were invisible), and every
`RETURNING id` was piped to /dev/null. So the subject saw 26 and 6 (directly, in filtered
read-backs that included their kinds) but never saw 27..32. This instrument models exactly that:

  Observation (fail-SAFE, the F42 law "a currency mechanism whose output is discarded is a lying
  comfort"): target T is OBSERVED at citing row R iff the SUBJECT ROLE ran a ledger read-back S with
  T.ts < S.ts < R.ts whose kind-filter admits T's kind (no filter = admits all). RETURNING output is
  NOT counted as an observation — it was discarded at the client, so blessing the server-logged
  RETURNING would bless the exact lying comfort F42 names. The engineer/gate reads (role != subject)
  are NOT observations either — they are the apparatus reading, not the subject seeing.

Edges checked: every supersedes / enacts / amends / answers / regards target (whichever the schema
carries). For each, OBSERVED (a qualifying read-back exists) or UNOBSERVED-AT-CITATION (flag).

Evidence: the role-attributed Postgres statement log (the off-host tee.log archive, or the live
/home/bork/pg_log glob) × the ledger. Read-only.
"""
from __future__ import annotations

import glob
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime

from ledger_target import LedgerTarget, resolve

# Resolved once per report() from the target NAME; the SSOT foreclosing the wrong-place class
# (ledger_target.py). This instrument hardcoded PGDB="epistemic" and could not run against the
# isolated `nla` ledger at all — the R5 gap link 21 had to measure by hand (F49).
TARGET: LedgerTarget
DEFAULT_LOG_GLOB = "/home/bork/pg_log/epistemic-*.log"

# a role-attributed statement line: "<ts> CEST [pid] role=<r> ... LOG:  statement: <sql>"
LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+) \S+ \[\d+\] role=(?P<role>\S+) "
    r".*?LOG:\s+statement:\s+(?P<sql>.*)$")
# kind filters the subject read-backs use: `kind IN ('a','b')` and `kind = 'x'` / `kind='x'`.
KIND_IN_RE = re.compile(r"kind\s+in\s*\(([^)]*)\)", re.IGNORECASE)
KIND_EQ_RE = re.compile(r"kind\s*=\s*'([^']+)'", re.IGNORECASE)
_QUOTED_RE = re.compile(r"'([^']*)'")
# the SELECT's projection list (between SELECT and the first FROM). A read-back "shows" a row's id
# to the subject only if it PROJECTS the id (or `*`); a `count(*)` / `kind, count(*)` aggregate
# touches the ledger but exposes no id, so it is not an observation of any particular row.
_SELECT_LIST_RE = re.compile(r"^\s*select\b(.*?)\bfrom\b", re.IGNORECASE | re.DOTALL)
_ID_TOK_RE = re.compile(r"(?:^|[\s,.(])id(?:$|[\s,)])", re.IGNORECASE)
# a select-ALL item ( `*` or `l.*` as a whole projection item) — NOT the `*` inside count(*).
_STAR_ITEM_RE = re.compile(r"(?:^|,)\s*(?:\w+\.)?\*\s*(?:,|$)")


def _exposes_id(sql: str) -> bool:
    m = _SELECT_LIST_RE.match(sql.lstrip())
    if not m:
        return False
    proj = m.group(1)
    return bool(_ID_TOK_RE.search(proj) or _STAR_ITEM_RE.search(proj))


@dataclass(frozen=True)
class Read:
    ts: datetime
    kinds: frozenset[str] | None  # None = no kind filter (admits every kind)


def _psql(sql: str) -> str:
    return TARGET.run(sql).stdout


def _rows(sql: str) -> list[list[str]]:
    return TARGET.rows(sql)


def _has_col(col: str) -> bool:
    return TARGET.has_col(col)


def _parse_ts(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")


def subject_reads(session: str, log_paths: list[str]) -> list[Read]:
    """The subject role's ledger read-backs, with the kind-filter each carries. The subject role is
    led_{session} (F33: attribution keyed to the connection). Gate/engineer reads (other roles) are
    excluded — they are the apparatus reading, not the subject observing."""
    role = TARGET.login_role
    reads: list[Read] = []
    for p in log_paths:
        for line in open(p, encoding="utf-8", errors="replace"):
            m = LINE_RE.match(line.rstrip("\n"))
            if not m or m["role"] != role:
                continue
            sql = m["sql"]
            low = sql.lstrip().lower()
            if not (low.startswith("select") and "ledger" in sql.lower()):
                continue
            if not _exposes_id(sql):
                continue  # a count/aggregate read touches the ledger but exposes no id
            kinds: frozenset[str] | None = None
            mi = KIND_IN_RE.search(sql)
            if mi:
                kinds = frozenset(q.lower() for q in _QUOTED_RE.findall(mi.group(1)))
            else:
                me = KIND_EQ_RE.search(sql)
                if me:
                    kinds = frozenset({me.group(1).lower()})
            reads.append(Read(_parse_ts(m["ts"]), kinds))
    reads.sort(key=lambda r: r.ts)
    return reads


def load_edges(session: str) -> tuple[dict[int, tuple[str, datetime]], list[tuple[int, int, str]]]:
    """(rows by id -> (kind, ts), citing edges [(citing_id, target_id, edge_kind)]). Reads only the
    edge columns the schema carries (supersedes/enacts always; amends/answers/regards on s13+)."""
    rel = TARGET.rel()
    rows: dict[int, tuple[str, datetime]] = {}
    for i, k, ts in _rows(f"SELECT id, kind, to_char(ts,'YYYY-MM-DD HH24:MI:SS.US') FROM {rel};"):
        rows[int(i)] = (k.strip(), _parse_ts(ts))
    edges: list[tuple[int, int, str]] = []
    for a, b in _rows(f"SELECT id, supersedes FROM {rel} WHERE supersedes IS NOT NULL;"):
        edges.append((int(a), int(b), "supersedes"))
    # enacts (scalar in the e9 schema, array from e10): union both shapes.
    is_arr = _psql(f"SELECT data_type FROM information_schema.columns WHERE table_schema='{TARGET.schema}'"
                   f" AND table_name='ledger' AND column_name='enacts';").strip() == "ARRAY"
    if is_arr:
        esql = (f"SELECT e.id, u.tid FROM {rel} e CROSS JOIN LATERAL unnest(e.enacts) AS u(tid);")
    else:
        esql = f"SELECT id, enacts FROM {rel} WHERE enacts IS NOT NULL;"
    for a, b in _rows(esql):
        edges.append((int(a), int(b), "enacts"))
    for col in ("amends", "answers", "regards"):
        if _has_col(col):
            for a, b in _rows(f"SELECT id, {col} FROM {rel} WHERE {col} IS NOT NULL;"):
                edges.append((int(a), int(b), col))
    return rows, edges


def report(session: str, log_paths: list[str]) -> None:
    global TARGET
    TARGET = resolve(session)
    rows, edges = load_edges(session)
    reads = subject_reads(session, log_paths)
    print(f"# observed-currency (F42) — {TARGET.db}.{TARGET.rel()} × subject read-backs "
          f"({len(rows)} rows, {len(edges)} citing edges, {len(reads)} subject read-backs)\n")
    if not reads:
        print("  (no subject read-backs found in the supplied log — supply the session's off-host "
              "tee.log via --log=PATH; without it every edge reads as unobserved and the instrument "
              "cannot discriminate)\n")
    observed, unobserved = [], []
    for a, t, ek in sorted(edges):
        if t not in rows or a not in rows:
            continue
        t_kind, t_ts = rows[t]
        a_ts = rows[a][1]
        seen = any(t_ts < r.ts < a_ts and (r.kinds is None or t_kind in r.kinds) for r in reads)
        (observed if seen else unobserved).append((a, t, ek, t_kind))
    print("OBSERVED-AT-CITATION — the cited id appeared in an id-projecting subject read-back whose "
          "kind-filter admitted it, before the citing act:")
    print("  " + ("  ".join(f"{ek}({a}->{t})" for a, t, ek, _ in observed) or "(none)"))
    print(f"\nUNOBSERVED-AT-CITATION (FLAG, {len(unobserved)}) — cited with NO id-projecting read-back "
          "that admitted the id in the record (fail-SAFE: RETURNING is not counted — discarded/"
          "held-in-memory currency is not a record-level observation, F42). A flag is a REVIEW "
          "trigger — 'unverified by the record', not a miscite verdict; the miscite is the flag "
          "PLUS a wrong target (31->27: cited a note when the ruling decision was intended):")
    if unobserved:
        for a, t, ek, tk in unobserved:
            print(f"  FLAG {ek}({a}->{t}): target #{t} is a '{tk}'; no admitting read-back before "
                  f"row #{a} in the record.")
    else:
        print("  (none)")
    print("\n# NOTE on the alias_surface kind-luck limitation (F42, consult 17 §2.3): the soundness "
          "alias_surface flag catches a miscite ONLY when the wrong target is a non-decision — a "
          "one-slot desync onto a decision, or a decision-typed hidden row, passes it silently. "
          "observed_currency is kind-INDEPENDENT: it flags an unobserved citation whatever the "
          "target's kind, closing that hole. (RETURNING output is not counted as observation — "
          "discarded currency is a lying comfort.)")


def main() -> int:
    args = sys.argv[1:]
    log_paths: list[str] = []
    sessions: list[str] = []
    for a in args:
        if a.startswith("--log="):
            log_paths.append(os.path.expanduser(a.split("=", 1)[1]))
        else:
            sessions.append(a)
    if not log_paths:
        log_paths = sorted(glob.glob(DEFAULT_LOG_GLOB))
    for s in (sessions or ["s12"]):
        report(s, log_paths)
    return 0


if __name__ == "__main__":
    sys.exit(main())
