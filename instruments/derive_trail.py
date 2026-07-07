#!/usr/bin/env python3
"""derive_trail — reconstruct a session's activity trail from tool-provenance alone,
independent of the collaborator's self-report (FINDINGS F21 route (a)).

The e7 result (F21) said contemporaneity is not attainable as a *behavior*; the two
deployment routes are (a) derive the trail from tool-provenance, or (b) gate acts on entries
(the e8 experiment). This instrument is route (a): it emits a G1-shape register — (ts, actor,
act, target[, status]) — for a session purely from the PreToolUse audit log (every tool call,
witnessed) joined with the off-host statement log (SQL verbs and error status for the session
role). It authors nothing; the collaborator's ledger is not consulted. Its existence lets the
deployment recommendation compare routes (a) and (b) on evidence rather than argument.

Honest scope: the PreToolUse audit hook fires BEFORE execution, so per-tool exit status is not
captured here (a PostToolUse witness would add it); SQL error status IS available from the
statement log. This is marked in the output rather than implied away.
Read-only. Consumes all.audit.jsonl and the statement log.
"""
import glob
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta

AUDIT = "/home/bork/w/vdc/1/epistemic-audit/logs/all.audit.jsonl"
LOG_DIR = "/home/bork/pg_log"
LOG_GLOB = "epistemic-*.log"  # date-stamped; scanned across days so a session spanning
#                               midnight (or a future-dated run) is still covered.

# session label -> (audit session_id, statement-log role)
SESSIONS = {
    "s8": ("f264354e-b741-450e-b502-e72ce320dbcd", "led_s8"),
    "s9": ("1fee6cdb-b784-4939-ab41-2a5106a2fecf", "led_s9"),  # e8 subject run (§2.6.ii: was unfilled)
    "s10": ("29d0ebb3-e8fd-42e3-af81-60e97c3178e2", "led_s10"),  # e9 — recovered from all.audit.jsonl (sole epistemic-e9 session, first event 17:15:36)
    "s11": ("51384fb5-5d9e-4dbe-8d6b-61746f1d3b32", "led_s11"),  # e10 — derived from all.audit.jsonl (sole epistemic-e10 session, first event 19:18:35)
    "s12": ("b4d18df8-97d5-4345-9ade-2edbfa4c1be5", "led_s12"),  # e11 — derived from all.audit.jsonl (sole epistemic-e11 session, first event 20:57:47)
}

# pg_log line prefix: '2026-07-05 08:07:47.757 CEST [pid] role=led_sN db=... ERROR: ...'
_PGLOG_TS_RE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)")


@dataclass
class Ev:
    ts: str
    actor: str
    act: str
    target: str
    status: str


def _audit_events(session_id: str, since: datetime | None = None) -> list[Ev]:
    evs = []
    for line in open(AUDIT, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("session_id") != session_id:
            continue
        if since is not None:  # run-window key (§7-5b): isolate the e12 window of a two-window session
            try:
                if datetime.fromisoformat(r["ts"]).replace(tzinfo=None) < since:
                    continue
            except (KeyError, ValueError):
                continue
        tool = r.get("tool", "?")
        sal = r.get("salient", "")
        if tool in ("Write", "Edit", "NotebookEdit", "Read"):
            target = sal if isinstance(sal, str) else json.dumps(sal)
            act = tool.lower()
        elif tool == "Bash":
            cmd = sal if isinstance(sal, str) else ""
            low = cmd.lower()
            if low.startswith(("git ",)):  # check git first: a commit msg may contain "pytest"/"conformance"
                act, target = "git", cmd[:48]
            elif "insert into ledger" in low:
                act, target = "ledger-insert", "ledger"
            elif "select" in low and "ledger" in low:
                act, target = "ledger-read", "ledger"
            elif "prior_decisions" in low:
                act, target = "reference-read", "ref.prior_decisions"
            elif "pytest" in low or "conformance" in low:
                act, target = "test-run", cmd[:48]
            else:
                act, target = "bash", cmd[:48]
        else:
            act, target = tool.lower(), str(sal)[:48]
        evs.append(Ev(r.get("ts", "")[11:23], "collaborator", act, target, "—"))
    return evs


def _session_window(session_id: str, since: datetime | None = None) -> tuple[datetime, datetime] | None:
    """Full-datetime [start, end] of the session's audit events, for scoping the pg_log
    error attribution to the session window (§2.6.iii — role-scoped over-counted the
    operator's pre-launch probes as the subject's). With `since`, the window starts at the
    run boundary (§7-5b) so a two-window session's e11 half does not widen the e12 window."""
    ts = []
    for line in open(AUDIT, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("session_id") != session_id:
            continue
        try:
            t = datetime.fromisoformat(r["ts"]).replace(tzinfo=None)
        except (KeyError, ValueError):
            continue
        if since is not None and t < since:
            continue
        ts.append(t)
    if not ts:
        return None
    return min(ts), max(ts)


def _sql_errors(role: str, window: tuple[datetime, datetime] | None) -> tuple[int, int]:
    """(in_window, total) ERROR lines for `role` across the pg_log(s). `in_window` counts
    only errors within the session window (padded 5s for guest/server skew); it is the
    honest per-session number. total is kept so operator/pre-launch probes stay visible."""
    in_window = total = 0
    lo = hi = None
    if window:
        lo, hi = window[0] - timedelta(seconds=5), window[1] + timedelta(seconds=5)
    for path in sorted(glob.glob(os.path.join(LOG_DIR, LOG_GLOB))):
        try:
            fh = open(path, encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in fh:
            if f"role={role}" not in line or "ERROR:" not in line:
                continue
            total += 1
            if lo is None:
                continue
            m = _PGLOG_TS_RE.match(line)
            if not m:
                continue
            try:
                t = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                continue
            if lo <= t <= hi:
                in_window += 1
        fh.close()
    return in_window, total


def derive(session: str, since: datetime | None = None) -> list[Ev]:
    sid, role = SESSIONS[session]
    if sid is None:
        return []
    evs = _audit_events(sid, since)
    evs.sort(key=lambda e: e.ts)
    return evs


def print_trail(session: str, since: datetime | None = None) -> None:
    sid, role = SESSIONS[session]
    if sid is None:
        print(f"# derived provenance trail — session {session} (role {role}): "
              f"session_id not yet filled (paste it into SESSIONS at launch)")
        return
    evs = derive(session, since)
    win_note = f" [run-window since {since.isoformat(sep=' ')}]" if since else ""
    print(f"# derived provenance trail — session {session} (role {role}), {len(evs)} events{win_note}")
    print(f"# (route (a): authored from tool-provenance, ledger NOT consulted; "
          f"per-tool exit status not captured by the PreToolUse witness)")
    print(f"{'ts':12} {'actor':12} {'act':16} target")
    for e in evs:
        print(f"{e.ts:12} {e.actor:12} {e.act:16} {e.target}")
    if role:
        win = _session_window(sid, since)
        in_win, total = _sql_errors(role, win)
        print(f"# statement-log ERROR lines for {role} within the session window: {in_win}"
              f"  (all-time for this role across pg_log: {total}; the difference is "
              f"operator/pre-launch activity, not the subject's)")


if __name__ == "__main__":
    # --since='YYYY-MM-DD HH:MM:SS' (or ISO 'T') isolates the e12 run window of a two-window
    # session (§7-5b); absent → full history (banked s8–s11 trails reproduce unchanged).
    _since: datetime | None = None
    _targets = []
    for a in sys.argv[1:]:
        if a.startswith("--since="):
            raw = a.split("=", 1)[1].replace("T", " ").strip()
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    _since = datetime.strptime(raw, fmt)
                    break
                except ValueError:
                    continue
            if _since is None:
                print(f"# derive_trail: unparseable --since={raw!r} (use 'YYYY-MM-DD HH:MM:SS')")
                sys.exit(2)
        else:
            _targets.append(a)
    for s in (_targets or ["s8"]):
        print_trail(s, _since)
