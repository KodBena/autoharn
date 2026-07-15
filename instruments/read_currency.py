#!/usr/bin/env python3
"""Read-currency check — the deployable rule banked from the two-read paradigm (FINDINGS
F16/F17/F20). A citation of a *mutable* source S is trustworthy only if the citing role
read S with no intervening write to S between that read and the citing act. This is the
mechanically-checkable half of the witness-scope limit (F20): it cannot prove a citation
was *used*, but it can refuse to bless one that rests on a *stale* read.

Rule (per link 5): for a (role, source, citing_act_ts) triple, GREEN iff there exists a
witnessed read of S by `role` before citing_act_ts AND no write to S (by any role) falls
strictly between that last read and citing_act_ts. Otherwise FLAG. It fails SAFE — a
missing re-read or an intervening write both flag, so a false alarm costs a review while a
false confirm (the thing safety-critical domains exist to prevent) cannot slip.

Evidence: the off-host, role-attributed Postgres statement log (the authoritative witness).
Reads only.
"""
from __future__ import annotations

import glob
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime

# Date-generic: scan every date-stamped statement log (a date-pinned path silently found zero
# statements on a later run). Mirrors derive_trail / cite_check globbing.
LOG_DIR = "/home/bork/pg_log"
LOG_GLOB = "epistemic-*.log"

# a logged statement line: "<ts> CEST [pid] role=<r> db=... app=... LOG:  statement: <sql>"
LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+) \S+ \[\d+\] role=(?P<role>\S+) "
    r".*?(?:LOG|STATEMENT):\s+statement:\s+(?P<sql>.*)$"
)


@dataclass
class Stmt:
    ts: datetime
    role: str
    sql: str


@dataclass
class Verdict:
    ok: bool
    reason: str
    last_read: datetime | None
    intervening_write: datetime | None


def load_statements(path: str | None = None) -> list[Stmt]:
    paths = [path] if path else sorted(glob.glob(os.path.join(LOG_DIR, LOG_GLOB)))
    out = []
    for p in paths:
        for line in open(p, encoding="utf-8", errors="replace"):
            m = LINE_RE.match(line.rstrip("\n"))
            if not m:
                continue
            ts = datetime.strptime(m["ts"], "%Y-%m-%d %H:%M:%S.%f")
            out.append(Stmt(ts, m["role"], m["sql"].strip()))
    out.sort(key=lambda s: s.ts)
    return out


def _touches(sql: str, source: str) -> bool:
    return source.lower() in sql.lower()


def _is_read(sql: str) -> bool:
    return sql.lstrip().lower().startswith("select")


def _is_write(sql: str) -> bool:
    head = sql.lstrip().lower()
    return head.startswith(("update ", "insert ", "delete ")) or head.startswith(
        ("update\n", "insert\n", "delete\n"))


def check(source: str, role: str, citing_act: datetime,
          statements: list[Stmt], ignore_reads_after: datetime | None = None) -> Verdict:
    """ignore_reads_after: for synthetic what-ifs — pretend reads at/after this instant
    did not happen (e.g. to model a subject that skipped the turn-2 re-read)."""
    reads = [s for s in statements
             if s.role == role and _touches(s.sql, source) and _is_read(s.sql)
             and s.ts < citing_act
             and (ignore_reads_after is None or s.ts < ignore_reads_after)]
    if not reads:
        return Verdict(False, "no witnessed read of the source before the citing act", None, None)
    last_read = max(reads, key=lambda s: s.ts).ts
    writes = [s for s in statements
              if _touches(s.sql, source) and _is_write(s.sql)
              and last_read < s.ts < citing_act]
    if writes:
        w = min(writes, key=lambda s: s.ts).ts
        return Verdict(False, "source written after the last read (STALE)", last_read, w)
    return Verdict(True, "read current: no write between last read and citing act", last_read, None)


def _p(label: str, v: Verdict) -> None:
    mark = "GREEN" if v.ok else "FLAG "
    lr = v.last_read.strftime("%H:%M:%S") if v.last_read else "—"
    iw = v.intervening_write.strftime("%H:%M:%S") if v.intervening_write else "—"
    print(f"  [{mark}] {label}: {v.reason}  (last_read={lr}, intervening_write={iw})")


def _validate() -> None:
    st = load_statements()
    src, role = "ref.prior_decisions", "led_s7"
    citing = datetime.strptime("2026-07-05 05:56:06", "%Y-%m-%d %H:%M:%S")  # lowering use (schedule.py write)
    print("read-currency validation on e6 (source=ref.prior_decisions, role=led_s7, "
          "citing act = 05:56:06 lowering):")
    # real e6: the subject re-read at 05:54:20, after the 05:46:06 correction -> current
    _p("e6 actual (re-read happened)", check(src, role, citing, st))
    # synthetic: pretend no turn-2 re-read (ignore reads at/after 05:40) -> only the
    # 05:26:53 turn-1 read remains, and the 05:46:06 correction intervenes -> STALE
    cut = datetime.strptime("2026-07-05 05:40:00", "%Y-%m-%d %H:%M:%S")
    _p("e6 synthetic (no re-read)", check(src, role, citing, st, ignore_reads_after=cut))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        _validate()
    else:
        print("usage: read_currency.py            # run the e6 validation\n"
              "       (import check() for a (source, role, citing_act_ts) triple)")
