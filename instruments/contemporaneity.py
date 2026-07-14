#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T22:13:03Z
#   last-change: 2026-07-14T22:13:03Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""Contemporaneity gap-detector — a retrospective audit instrument (and the seed of a
deployable Claude-Code hook) for the epistemic-pilot series.

Thesis it operationalizes (FINDINGS F6/F10/F18): a decision ledger mandated to be kept
"as you go" can instead be *batch-reconstructed* — accumulated and bulk-loaded after the
work it records — which silently forfeits the contemporaneity guarantee an audit trail
exists to provide. This tool measures that gap from the witnesses, not the self-report.

Two tiers, by available evidence:

  Tier 1 (any session, ledger timestamps only) — two orthogonal signals.
    * TIMING: cluster inserts by temporal proximity (gap > GAP_S starts a new burst).
      Rows spread through the build → contemporaneous; bunched into a few tight windows
      → batched-in-time, regardless of the SQL vehicle used. `batched_row_frac` = fraction
      of ROWS that sit in a multi-row temporal burst (≈0 contemporaneous; ≈1 clustered).
      When a tool-call log exists, the Tier-2 per-entry lag distribution is the primary
      signal and this fraction is a fallback (burst structure alone can mislead — a mostly
      batched run with a few trailing singletons is still batched).
    * VEHICLE: rows sharing an *identical* insert ts came from one multi-row bulk load;
      `bulk_max` = largest such group (>1 ⇒ a bulk `psql -f`/multi-row VALUES was used;
      =1 ⇒ individual per-row INSERTs). e7 removes the bulk vehicle, so this isolates
      whether batching is a vehicle convenience (bulk_max drops, timing improves) or a
      workflow structure (individual inserts still cluster in time).
    Works across the whole series (s1..s7) from ledger timestamps alone.

  Tier 2 (sessions with a PreToolUse audit log) — PER-ENTRY LAG + ORDERING VIOLATIONS.
    For each ledger row whose `evidence` cites a file, the enacting act is the last
    Write/Edit of that file before the row's insert; lag = insert_ts - enact_ts. A
    `snag`/`revision` row whose insert *follows* the act it resolves is an ordering
    violation (the mandate says record the contest *before* acting on it).

Read-only. Consumes: the Postgres ledger (per-session) and the guest audit log
(all.audit.jsonl). Nothing is written to the DB.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ledger_target import resolve
from pghost_resolve import resolve_pghost

PGHOST = resolve_pghost("EPISTEMIC_PGHOST")
_DB = "epistemic"  # set per-session in load_rows via the SSOT (nla lives in its own db)
AUDIT_LOG = "/home/bork/w/vdc/1/epistemic-audit/logs/all.audit.jsonl"
GAP_S = 60.0  # inserts more than this many seconds apart start a new temporal burst

# session label -> (ledger relation, audit-hook session_id or None)
SESSIONS: dict[str, tuple[str, str | None]] = {
    "s1": ("public.ledger", None),
    "s3": ("public.ledger", None),
    "s3_abort": ("public.ledger", None),
    "s4": ("public.ledger", None),
    "s5": ("public.ledger", None),
    "s6": ("s6.ledger", "b5283567-3c75-41c9-87af-9ae1004e33f2"),
    "s7": ("s7.ledger", "1a295b41-2fd9-46a8-92c5-3585fefad07d"),
    "s8": ("s8.ledger", "f264354e-b741-450e-b502-e72ce320dbcd"),  # e7 (started turn 1 2026-07-05)
    "s9": ("s9.ledger", "1fee6cdb-b784-4939-ab41-2a5106a2fecf"),  # e8 (subject run 15:11–15:47; was the §2.6.ii omission)
    "s10": ("s10.ledger", "29d0ebb3-e8fd-42e3-af81-60e97c3178e2"),  # e9 — recovered from all.audit.jsonl (sole epistemic-e9 session, first event 17:15:36)
    "s11": ("s11.ledger", "51384fb5-5d9e-4dbe-8d6b-61746f1d3b32"),  # e10 — derived from all.audit.jsonl (sole epistemic-e10 session, first event 19:18:35)
    "s12": ("s12.ledger", "b4d18df8-97d5-4345-9ade-2edbfa4c1be5"),  # e11 — derived from all.audit.jsonl (sole epistemic-e11 session, first event 20:57:47)
    "nla": ("public.ledger", "428864a6-3cd2-4d7d-a1bb-f3754d44a033"),  # e14 — isolated nla.public ledger; audit session id from all.audit.jsonl
    "e15": ("public.ledger", None),  # e15 — isolated vsr.public s15 ledger; audit session id filled at run close (the fresh subject session, unknown until Phase 1)
    "e16": ("public.ledger", None),  # e16 — isolated hvn.public s16 ledger; audit session id filled at run close
    "e18": ("public.ledger", None),  # e18 — isolated qbx.public s18 ledger; None RECORDED-WHY at close (mirrors e15/e16): the subject ran in the fenced dir, never under the epistemic-audit hook, so all.audit.jsonl carries no e18 session. The VENDOR session id is 9c467b69 (banked: ledger_target + docs/claude-ephemera/session-9c467b69-e18-subject/)
}

# act-gate journal, per gated session. The DEPLOYED journal is a single transient file the next
# run overwrites, so a historical session must read its ARCHIVED copy (else `contemporaneity.py
# s10` would silently report the live run's gate numbers under the s10 header). The live run
# reads the deployed path. arm_label names the experiment arm that produced the journal.
_DEPLOYED_JOURNAL = "/home/bork/w/vdc/1/epistemic-audit/logs/change_gate.journal.jsonl"
GATE_JOURNALS: dict[str, tuple[str, str]] = {
    "s10": ("/home/bork/w/vdc/1/epistemic-operator/witness/e9-s10.change_gate.journal.jsonl", "e9"),
    "s11": ("/home/bork/w/vdc/1/epistemic-operator/witness/e10-s11.change_gate.journal.jsonl", "e10"),  # archived at e10 close; repointed so its summary survives the e11 run overwriting the deployed journal
    "s12": (_DEPLOYED_JOURNAL, "e11"),  # live during the e11 run; archive it at run close as e11-s12.*
    "nla": (_DEPLOYED_JOURNAL, "e14"),  # live during the e14 run; archive at close as e14-nla.*
    "e15": ("/home/bork/w/vdc/1/epistemic-operator/witness/e15-vsr.change_gate.journal.jsonl", "e15"),  # FORWARD-FIX 2026-07-07 (maintainer ruling, e18-teardown flag): the promised close-time archive was never made, so this entry dangled at the deployed file. Archive = the e16-arm truncation .bak (the deployed journal's content when e15's window closed) — ZERO entries, true run output (fenced-dir subject, no change-gate hook). Recorded-why banked: witness/e15-e16-gate-journal-pointer-forward-fix.md
    "e16": ("/home/bork/w/vdc/1/epistemic-operator/witness/e16-hvn.change_gate.journal.jsonl", "e16"),  # FORWARD-FIX 2026-07-07, same ruling and shape as e15 above. Archive = the first e17-build-launch truncation .bak — ZERO entries, true run output. Recorded-why banked: witness/e15-e16-gate-journal-pointer-forward-fix.md
    "e18": ("/home/bork/w/vdc/1/epistemic-operator/witness/e18-qbx.change_gate.journal.jsonl", "e18"),  # archived at e18 close: ZERO entries — true run output, not loss. The change gate (epistemic-audit/pretooluse_change_policy.py) is e8–e14-era machinery for subjects running INSIDE epistemic-audit; the e18 subject ran in the fenced dir under the stamp hook only. Provenance: the e17-build-launch .bak truncation (zero bytes) bounds the window, and the deployed journal was still zero bytes at close.
}

FILE_RE = re.compile(r"([\w./-]+\.py)")


@dataclass
class Row:
    id: int
    ts: datetime
    kind: str
    statement: str
    evidence: str


@dataclass
class Act:
    ts: datetime
    tool: str
    target: str  # file path for Write/Edit; command for Bash


@dataclass
class RowLag:
    row: Row
    enact: Act | None
    lag: timedelta | None
    violation: bool


@dataclass
class Report:
    session: str
    rows: list[Row]
    bursts: list[list[Row]]      # temporal clusters (GAP_S)
    batched_row_frac: float      # fraction of ROWS sitting in a multi-row temporal burst
    bulk_max: int                # largest group sharing an identical insert ts (vehicle)
    lags: list[RowLag] = field(default_factory=list)
    tier2: bool = False


def _psql(sql: str) -> str:
    out = subprocess.run(
        ["psql", "-h", PGHOST, "-d", _DB, "-tA", "-F", "\t", "-c", sql],
        capture_output=True, text=True, check=True,
    )
    return out.stdout


def _parse_ts(s: str) -> datetime:
    # psql default timestamptz like '2026-07-05 05:35:53.218+02' — trim tz, keep micros
    s = s.strip()
    s = re.sub(r"[+-]\d\d(:?\d\d)?$", "", s).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"unparseable ts: {s!r}")


def load_rows(session: str, since: str | None = None) -> list[Row]:
    global _DB
    tgt = resolve(session)
    _DB = tgt.db
    rel, _ = SESSIONS[session]
    conds = []
    # The historical `epistemic.public.ledger` is SHARED across the s1-s5 era sessions, so it is
    # filtered by session label. The isolated `nla.public.ledger` is dedicated to its one run — no
    # session filter, or it would filter out every row (nla rows carry their kickoff label, not the
    # target name). The discriminator is the database, resolved from the SSOT.
    if rel == "public.ledger" and tgt.db == "epistemic":
        conds.append(f"session = '{session}'")
    if since:
        conds.append(f"ts >= '{since.replace(chr(39), chr(39) * 2)}'")  # run-window key (§7-5b)
    where = (" WHERE " + " AND ".join(conds)) if conds else ""
    sql = (f"SELECT id, ts, kind, statement, coalesce(evidence,'') "
           f"FROM {rel}{where} ORDER BY id;")
    rows = []
    for line in _psql(sql).splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            parts += [""] * (5 - len(parts))
        rid, ts, kind, stmt, ev = parts[:5]
        rows.append(Row(int(rid), _parse_ts(ts), kind, stmt, ev))
    return rows


def load_acts(session_id: str, since: datetime | None = None) -> list[Act]:
    acts = []
    with open(AUDIT_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("session_id") != session_id:
                continue
            tool = r.get("tool", "?")
            sal = r.get("salient", "")
            target = sal if isinstance(sal, str) else json.dumps(sal)
            # audit ts is ISO local without tz
            try:
                ts = datetime.fromisoformat(r["ts"])
            except (KeyError, ValueError):
                continue
            ts = ts.replace(tzinfo=None)
            if since is not None and ts < since:
                continue  # run-window key (§7-5b): drop pre-window acts
            acts.append(Act(ts, tool, target))
    acts.sort(key=lambda a: a.ts)
    return acts


def _enacting_act(row: Row, acts: list[Act]) -> Act | None:
    """Last file-mutation act, before this row's insert, touching a file the row cites.
    Falls back to the last test/conformance Bash run for verification rows citing a run."""
    files = set(FILE_RE.findall(row.evidence))
    best: Act | None = None
    for a in acts:
        if a.ts >= row.ts:
            break
        if a.tool in ("Write", "Edit", "NotebookEdit") and files:
            if any(a.target.endswith(fp) or fp in a.target for fp in files):
                best = a
        elif a.tool == "Bash" and row.kind == "verification" and (
            "pytest" in row.evidence or "conformance" in row.evidence):
            if "pytest" in a.target or "conformance" in a.target:
                best = a
    return best


def analyze(session: str, since: str | None = None) -> Report:
    rows = load_rows(session, since)
    since_dt = _parse_ts(since) if since else None
    # Tier 1 TIMING — cluster inserts by temporal proximity (gap > GAP_S = new burst)
    bursts: list[list[Row]] = []
    for r in rows:
        if bursts and (r.ts - bursts[-1][-1].ts).total_seconds() <= GAP_S:
            bursts[-1].append(r)
        else:
            bursts.append([r])
    batched_rows = sum(len(b) for b in bursts if len(b) > 1)
    batched_row_frac = batched_rows / len(rows) if rows else float("nan")
    # Tier 1 VEHICLE — largest group sharing an identical insert ts (one bulk load)
    bulk_max = max(Counter(r.ts for r in rows).values()) if rows else 0
    rep = Report(session, rows, bursts, batched_row_frac, bulk_max)
    # Tier 2 — per-entry lag, if we have a tool-call log for this session
    _, sid = SESSIONS[session]
    if sid:
        acts = load_acts(sid, since_dt)
        if acts:
            rep.tier2 = True
            for r in rows:
                a = _enacting_act(r, acts)
                lag = (r.ts - a.ts) if a else None
                viol = bool(a and r.kind in ("snag", "revision") and r.ts > a.ts)
                rep.lags.append(RowLag(r, a, lag, viol))
    return rep


def _fmt_td(td: timedelta | None) -> str:
    if td is None:
        return "     n/a"
    s = td.total_seconds()
    return f"{s:8.1f}s"


def print_report(rep: Report) -> None:
    biggest = max((len(b) for b in rep.bursts), default=0)
    lags = [rl.lag.total_seconds() for rl in rep.lags if rl.lag is not None] if rep.tier2 else []
    # verdict PREFERS the Tier-2 per-entry lag distribution (the gold signal); the burst
    # fraction is only the fallback when no tool-call log exists for the session.
    if lags:
        med = sorted(lags)[len(lags) // 2]
        verdict = "CONTEMPORANEOUS" if med <= 10 else ("MIXED" if med <= 30 else "BATCHED")
        basis = f"median_lag={med:.0f}s"
    else:
        bf = rep.batched_row_frac
        verdict = "BATCHED" if bf >= 0.5 else ("CONTEMPORANEOUS" if bf < 0.2 else "MIXED")
        basis = f"batched_row_frac={bf:.2f}"
    vehicle = f"bulk_max={rep.bulk_max} ({'BULK vehicle' if rep.bulk_max > 1 else 'individual inserts'})"
    print(f"\n=== session {rep.session}: contemporaneity report ===")
    print(f"rows={len(rep.rows)}  temporal_bursts={len(rep.bursts)} (biggest={biggest})  "
          f"batched_row_frac={rep.batched_row_frac:.2f}  -> {verdict} (by {basis})   |   {vehicle}")
    print("  bursts (start×count): " + ", ".join(
        f"{b[0].ts.strftime('%H:%M:%S')}×{len(b)}" for b in rep.bursts))
    if rep.tier2:
        viols = [rl for rl in rep.lags if rl.violation]
        if lags:
            print(f"  Tier2 per-entry lag (n={len(lags)}): "
                  f"min={min(lags):.0f}s median={sorted(lags)[len(lags)//2]:.0f}s max={max(lags):.0f}s")
        print(f"  ordering violations (contest logged AFTER its act): {len(viols)}")
        for rl in viols:
            print(f"    row {rl.row.id} [{rl.row.kind}] insert {rl.row.ts.strftime('%H:%M:%S')} "
                  f"> act {rl.enact.ts.strftime('%H:%M:%S')} "
                  f"(+{_fmt_td(rl.lag).strip()}): {rl.row.statement[:50]}")


def print_gate_summary(session: str, since: str | None = None) -> None:
    """act-gate readout from the gate journal: allows (fresh vs window-reused), denials
    decomposed by cause, window boundaries, entry→act cardinality, and the (approximate)
    pre-act lag. Authoritative lag_pre is the off-host INSERT×Write join; this is the quick
    view. Window-aware (repair 2): a fresh allow consumes a ticket and opens a window; a
    reused allow is a later Edit of the same file inside that window (no new entry). lag_pre
    is measured on FRESH allows only — the moments a ticket is actually consumed."""
    journal, label = GATE_JOURNALS[session]
    since_dt = _parse_ts(since) if since else None
    allowed_fresh, allowed_reused, denials, boundaries = [], [], [], []
    try:
        for line in open(journal, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if since_dt is not None:  # run-window key (§7-5b): journal "ts" is local ISO
                try:
                    if datetime.fromisoformat(r["ts"]).replace(tzinfo=None) < since_dt:
                        continue
                except (KeyError, ValueError):
                    pass
            oc = r.get("outcome")
            if oc == "allowed":
                (allowed_reused if r.get("reused_ticket") else allowed_fresh).append(r)
            elif oc == "denied":
                denials.append(r)
            elif oc == "boundary":
                boundaries.append(r)
    except FileNotFoundError:
        print(f"\n=== {label} gate journal: (none yet) ==="); return
    allows = allowed_fresh + allowed_reused
    print(f"\n=== {label} act-gate journal summary ===")
    entries = {r.get("unlocked_by_entry") for r in allowed_fresh}
    print(f"  governed acts allowed: {len(allows)}  "
          f"(fresh-ticket {len(allowed_fresh)}, window-reused {len(allowed_reused)})")
    print(f"  distinct unlocking entries: {len(entries)} -> cardinality entries:fresh-acts "
          f"= {len(entries)}:{len(allowed_fresh)}  "
          f"(near-1:1 ⇒ per-act; 1:many ⇒ front-loaded dump)")
    dk = Counter(r.get("deny_kind", "?") for r in denials)
    print(f"  denials: {len(denials)}  " + (dict(dk).__repr__() if denials else "")
          + "   (needs_entry incl. post-boundary re-edits & unresolved-enactment tickets; "
          "bash_write & any mtime-slip are the limb-3 evasion datum, not malfunction)")
    print(f"  window boundaries (test-run/commit closes): {len(boundaries)}")
    # ticket_flags telemetry (e10 gate; absent on the e9 journal → line suppressed, so the s10
    # gate summary stays byte-identical). The review-queue instrument is the primary consumer.
    flag_counts: Counter = Counter()
    for r in allows:
        flag_counts.update(r.get("ticket_flags") or [])
    if flag_counts:
        print(f"  ticket_flags (§4.5, de-priced §4.4 phenomena, measured not prevented): "
              f"{dict(sorted(flag_counts.items()))}")
    lags = []
    for r in allowed_fresh:
        try:
            act = datetime.fromisoformat(r["ts"]).replace(tzinfo=None)
            ets = re.sub(r"[+-]\d\d(:?\d\d)?$", "", r["entry_ts"]).strip()
            ent = datetime.strptime(ets, "%Y-%m-%d %H:%M:%S.%f")
            lags.append((act - ent).total_seconds())
        except Exception:
            pass
    if lags:
        s = sorted(lags)
        print(f"  lag_pre = fresh-act − unlocking-entry (n={len(lags)}): "
              f"min={min(lags):.0f}s median={s[len(s)//2]:.0f}s max={max(lags):.0f}s  "
              f"(small+per-act ⇒ contemporaneous; large+front-loaded ⇒ dump)")


if __name__ == "__main__":
    # --since='YYYY-MM-DD HH:MM:SS' (or ISO 'T') keys BOTH the ledger rows and the audit/gate acts
    # to a run window — the isolator for a two-window session (e11 close + e12 resume share one
    # session_id after `--resume` without `--fork-session`; consult 16 §7-5b). Absent → full history
    # (every banked s7–s11 number reproduces unchanged).
    _since: str | None = None
    args = []
    for a in sys.argv[1:]:
        if a.startswith("--since="):
            _since = a.split("=", 1)[1].replace("T", " ")
        else:
            args.append(a)
    targets = args or list(SESSIONS)
    errored = False
    na_only = False   # a target contemporaneity legitimately cannot analyze (no registered substrate)
    ran_any = False
    for s in targets:
        # A target with no gate-journal/audit-session config (e.g. a SYNTHETIC rehearsal mock) is
        # DECLARED N/A here, LOUDLY, and exits with a DISTINCT code (3) so a downstream aggregator
        # renders it as N/A — NEVER as OK (the out-of-frame audit's finding: exit-0-with-output read
        # as "tested clean" on a MANDATORY gate is the exact ADR-0015 R4 violation "a reader never
        # mistakes could-not-test for tested-clean", the finding-3/F49 shape). It is ALSO never a
        # KeyError crash reddening the close (ADR-0015 R4: degrade loud, do not crash). A REAL e15
        # target is registered at Phase 0, so it RUNS (OK) — the real gate is untouched; only a
        # genuinely-inapplicable target declares N/A, and that N/A is VISIBLE in the verdict.
        if s not in SESSIONS:
            print(f"\n=== session {s}: UNREGISTERED — no gate-journal/audit-session config; "
                  f"contemporaneity N/A for this target (declared, ADR-0015 R4; NOT clean, NOT a "
                  f"crash — exit 3 so a manifest renders N/A, never OK) ===")
            na_only = True
            continue
        try:
            print_report(analyze(s, _since))
            ran_any = True
        except Exception as e:  # noqa: BLE001 — report-and-continue across targets...
            print(f"\n=== session {s}: ERROR {type(e).__name__}: {e} ===")
            errored = True  # ...but a swallowed error must still make the RUN fail loudly
        if s in GATE_JOURNALS:
            print_gate_summary(s, _since)
    # Exit vocabulary (a closed set a manifest keys on): 1 = an internally-caught error (ADR-0002:
    # never mistaken for clean); 3 = every requested target was a DECLARED N/A (nothing analyzed) —
    # rendered N/A, never OK; 0 = analyzed clean. A mix (some ran, some N/A) exits 0 (something ran).
    sys.exit(1 if errored else (3 if (na_only and not ran_any) else 0))
