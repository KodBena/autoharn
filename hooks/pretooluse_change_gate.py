#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T08:07:02Z
#   last-change: 2026-07-09T08:07:31Z
#   contributors: 9bcc0113/main
# <<< PROVENANCE-STAMP <<<

"""PreToolUse change-policy gate (e13 / s13) — the act-gate, fully label-indifferent.

DELTA FROM THE e11/e12 GATE (F45, consult 17 §6 item 5 — the event-61 repair): ticket matching is
re-keyed from "the basename appears ANYWHERE in the entry text" to "the basename is DECLARED by the
ticket" — a declared `files:` list, plus free-text naming with COMMAND SPANS excluded. e12's gate
event 61 unlocked a ruling-work edit to tests/test_milestone_b.py under an UNRELATED stale
verification row (#24) whose only tie to the file was that its evidence QUOTED the command `pytest
tests/test_milestone_b.py` — a file named as a command ARGUMENT is not a declaration to CHANGE it.
The honest ticket (#31) existed but omitted the file from its `files:` list, so the gate fell back
to the coincidental command-quote. The repair (type-driven, ADR-0000): the match surface is the
ticket's DECLARATION of intent (the `files:` convention made structural, plus prose naming with
command spans stripped), so a coincidental command-quote can no longer authorize a change. This is
NOT a label-priced mechanism (F26): the declaration is a file list, never the subject's kind/concern.
Two further consult-17 item-5 clauses live in the instruments, not here: the long-lag fresh-unlock
flag (a new `long_lag_unlock` ticket_flag below) and the no-antecedent unreachable-by-debt report
(stale_enactment_debt). Everything else is the e11 gate verbatim, re-pointed at s14.ledger.

Byte-held from the e10 build EXCEPT the disclosed apparatus repairs above and the F33 invariant
re-key (below).

Byte-held from the e10 build EXCEPT one disclosed apparatus repair: the governed set is
re-keyed to the INVARIANT (consult 13 §5.3 / F33). e8–e10 hardcoded a package name the
FIRST subject happened to choose (`substrate/`), so the e10 subject's differently-named
engine (`nlafs/`, plus the top-level driver) produced ZERO gate events — 15 of 20 files, 21
of 32 mutation events, silently ungoverned under a green apparatus (the instance-keyed
governance defect, F33). The fix keys governance to WHAT THE THING IS, not what a subject
named it: every `*.py` file under the subject repo is governed. No package-name choice can
exit governance; drivers and tests are included by construction. This is not a lever — it is
the wholesale repair of a critical bypass, disclosed and probe-decided (F13/F14 precedent),
subject-visible only as the same gate footprint the standing mechanism already had.

Everything else is the e10 gate verbatim (consult 12 §1): §4.4 demoted to flag-and-journal
(keying is filename + currency ONLY, kind/concern-agnostic; every §4.4-class phenomenon
ALLOWs and is journaled as `ticket_flags`), BOUNDARY_RE quote-strip (a `pytest`/`commit`
token inside a SQL string literal is DATA, not a boundary), and the single deny kind
(needs_entry) whose message names only the file. The three deltas from e9 are unchanged:

  1. §4.4 DEMOTED from deny to flag-and-journal. Keying is filename + currency ONLY —
     kind- and concern-agnostic, positive OR negative. Every ALLOW journal record carries
     `ticket_flags` — computed telemetry, invisible to the subject, consumed by the
     review-queue instrument (measured, not prevented — a deny corrupts the label, F26).

     ticket_flags classes (consult 11 §4.5 / §7.1):
       - enactment_no_enacts    : concern='enactment' with enacts NULL/{} (honest-empty).
       - enacts_nondesign_target: some enacts element points at a non-`decision`-kind row.
       - enacts_stale_antecedent: some enacts element points at a row superseded as of the
                                  entry's ts (the first true stale-linkback datum if it fires).
       - window_redundant_entry : the unlocking entry was logged within WINDOW_S of the file's
                                  prior ticket while that window was still (nominally) open.

  2. BOUNDARY_RE quote-stripping (§7.2). The boundary scan runs on the command with
     dollar-quoted ($$…$$) and single/double-quoted spans stripped, so a `pytest`/`commit`
     token counts only as a COMMAND token, never as DATA inside a SQL string literal.

  3. Deny message: with §4.4 gone it is the only deny kind again — naming the file IS the
     whole contract. The message names no kind, concern, label, or governed-set vocabulary.

Governed paths: every `*.py` file under the subject repo (invariant-keyed; no package name).

Qualification posture (link 6): for an IDENTIFIED governed mutation the hook fails CLOSED
(deny) on any error — an unlogged change is the thing the target domains exist to prevent.
Unidentifiable input is passed through (the audit hook still records it; a slipped mutation
is recoverable post-hoc via the mtime × statement-log join). Emits both the modern
permissionDecision JSON and a non-zero exit for cross-version reliability.
"""
import fnmatch
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

PGHOST = "192.168.122.1"
# The subject ledger now lives in the ISOLATED database `nla` (catalog-isolated from the apparatus
# in `epistemic`, so the subject role cannot read apparatus vocabulary through the shared catalog).
# The gate is re-pointed at `nla`; env-overridable only so the build-time probe can target its own
# scratch mirror in that same database. Deployment leaves the env unset -> the durable `nla` ledger.
PGDB = os.environ.get("E13_GATE_DB", "nla")
# The ledger the gate reads. Deployment leaves the env unset -> the durable ledger. The override
# exists for exactly one reason (a DISCLOSED deviation from the e11 posture "the ledger the gate
# reads is NOT overridable"): the durable ledger is append-only and untruncatable at the write
# boundary, so the build-time gate probe CANNOT seed or reset fixtures there -- it points the gate at
# a scratch mirror (probe.ledger) instead. The e11 posture's intent (a probe must never write to or
# delete live evidence) is thereby STRENGTHENED, not weakened: the live ledger refuses fixture writes
# structurally, whatever env a caller sets.
LEDGER = os.environ.get("E13_GATE_LEDGER", "public.ledger")
# State + journal default to the deployment paths; a build-time verifier overrides them via
# env so it can never write to or delete the live run's evidence. Deployment leaves them
# unset → the production paths. (The ledger the gate reads is NOT overridable.)
STATE = os.environ.get(
    "E13_GATE_STATE", os.path.expanduser("~/w/vdc/1/epistemic-audit/change_gate_state.json"))
JOURNAL = os.environ.get(
    "E13_GATE_JOURNAL", os.path.expanduser("~/w/vdc/1/epistemic-audit/logs/change_gate.journal.jsonl"))
# The subject repo root. INVARIANT keying (F33): governance is `*.py` UNDER THIS ROOT — the
# root is the operator-fixed arm directory (same disclosure class as LEDGER / the deploy paths),
# NOT a subject-emergent package name. No package the subject invents can escape. Env-overridable
# so the build-time probe can point at its own subject base. Deployment leaves it unset → the
# e11 arm dir. "Under the repo" is honored precisely; a stray `.py` outside the repo (e.g. in the
# shared venv) is not governed, so the footprint is exactly the subject's own code.
SUBJECT_ROOT = os.path.abspath(os.environ.get(
    "E13_SUBJECT_ROOT", os.path.expanduser("~/w/vdc/1/epistemic-e14")))
EPOCH = "1970-01-01 00:00:00"
WINDOW_S = 600.0  # a ticket, once consumed, stays open on its file for this long …
# … or until the next test-run / commit boundary, whichever comes first.
LONG_LAG_S = 3600.0  # a FRESH unlock whose ticket is older than this is flagged long_lag_unlock
# (F45 / consult 17 item 5): event 61 unlocked at lag_pre 4880s under a stale verification row.
# Measured-not-prevented (a flag, never a deny — the lag may be legitimate; F26).

# Field / record separators for psql -tA output: ASCII US / RS. Chosen so entry text
# containing tabs or newlines (multi-line statements) cannot corrupt row parsing.
FS = "\x1f"
RS = "\x1e"

# Project-specific, concrete "what to run" appended to every deny message (fix-point ergonomics,
# maintainer requirement 2026-07-09): the gate's own refusal is the loop's only feedback channel,
# so it must name the exact next command, not just the policy. Empty by default (byte-held
# behavior for existing deployments); a project's settings.json sets DENY_HINT to its own
# ledger-insert one-liner (see toy-project's `led` helper).
DENY_HINT = os.environ.get("DENY_HINT", "")

DENY_NEEDS_ENTRY = (
    "Ledger policy: a change to a source file must be preceded by a ledger entry naming the "
    "file it changes. Insert the entry (one INSERT, as usual), then RE-ISSUE THE SAME EDIT — "
    "the gate re-checks on every attempt, so retrying after the insert is the whole fix."
    + (f"\n{DENY_HINT}" if DENY_HINT else "")
)
DENY_BASH_WRITE = (
    "Ledger policy: source files are modified via the Write/Edit tools, so each change is tied "
    "to its ledger entry — shell writes into these files are disabled."
    + (f"\n{DENY_HINT}" if DENY_HINT else "")
)

# GOVERNED-SET CONFIG (maintainer ruling, 2026-07-09): which files this gate protects is a
# per-project, trivially-editable choice — a small config file the PROJECT'S USER selects
# patterns in, never a set hardcoded here. Read once at import (this process is a fresh
# short-lived hook invocation per tool call, so "once at import" and "once per call" are the
# same thing — no P4 staleness). Format: {"patterns": ["*.py", ...]}, fnmatch'd against the
# path relative to SUBJECT_ROOT (fnmatch's "*" matches "/" too, so "*.py" alone reaches nested
# files — no "**" needed). Missing/unreadable/malformed config -> the F33 invariant default:
# every *.py file, class-keyed, exactly the old hardcoded behavior, so a project that has not
# yet configured governance is not silently ungoverned.
GOVERNED_CONFIG = os.environ.get(
    "GOVERNED_CONFIG", os.path.join(SUBJECT_ROOT, ".claude", "governed_files.json"))
_DEFAULT_GOVERNED_PATTERNS = ["*.py"]


def _load_governed_patterns(cfg_path: str) -> list[str]:
    try:
        with open(cfg_path, encoding="utf-8") as f:
            cfg = json.load(f)
        patterns = cfg.get("patterns")
        if isinstance(patterns, list) and patterns and all(isinstance(p, str) for p in patterns):
            return patterns
    except Exception:
        pass
    return _DEFAULT_GOVERNED_PATTERNS


GOVERNED_PATTERNS = _load_governed_patterns(GOVERNED_CONFIG)


# Governance is CLASS-keyed (F33): match by pattern/nature, never by an enumerated file list.
# Containment in the operator-fixed SUBJECT_ROOT is still absolute — no pattern can govern
# outside it, and no pattern choice can exit governance for a file the config's patterns cover.
def is_governed(path: str) -> bool:
    if not path:
        return False
    ap = os.path.abspath(path)
    if not (ap == SUBJECT_ROOT or ap.startswith(SUBJECT_ROOT + os.sep)):
        return False
    rel = os.path.relpath(ap, SUBJECT_ROOT)
    return any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(os.path.basename(ap), pat)
               for pat in GOVERNED_PATTERNS)


# bash writes INTO a governed path: redirection, sed -i, tee, patch, git checkout/apply, py
# open(w). Keyed on the `.py` nature (F33), not on any package name. Over-matching a `.py` path
# outside the repo only forces the Write/Edit route (safe); a false ALLOW is never produced.
_PY = r"[\w./+-]*\.py\b"
BASH_MUT_RES = [
    re.compile(r">>?\s*\S*" + _PY),                          # > / >> into a .py path
    re.compile(r"\bsed\b[^\n]*-i[^\n]*" + _PY),              # sed -i on a .py
    re.compile(r"\btee\b[^\n]*" + _PY),                      # tee into a .py
    re.compile(r"\bpatch\b[^\n]*" + _PY),                    # patch a .py
    re.compile(r"\bgit\s+checkout\b[^\n]*--[^\n]*" + _PY),   # git checkout -- file.py
    re.compile(r"\bgit\s+apply\b"),                          # git apply (conservative)
    re.compile(r"open\s*\([^)]*" + _PY.replace(r"\b", "") + r"[^)]*['\"]\s*w"),  # open(...'x.py'...,'w')
]
# a test-run or commit closes any open consumption window (repair 2). Scanned on the
# quote-STRIPPED command (repair 3, §7.2) so a token inside a SQL string literal is data, not
# a boundary. Byte-held from e10 (the boundary vocabulary is not part of the F33 re-key).
BOUNDARY_RE = re.compile(
    r"\bpytest\b|python\s+-m\s+pytest|\brun_conformance\b|\bgit\s+commit\b", re.IGNORECASE
)
# dollar-quoted spans ($$…$$ and $tag$…$tag$) and single/double-quoted spans — SQL/shell string
# literals whose contents are DATA, stripped before the boundary scan.
_DOLLARQ_RE = re.compile(r"\$(\w*)\$.*?\$\1\$", re.DOTALL)
_SQUOTE_RE = re.compile(r"'[^']*'", re.DOTALL)
_DQUOTE_RE = re.compile(r'"[^"]*"', re.DOTALL)


def _first(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return default


def bash_mutates_governed(cmd: str) -> bool:
    return any(r.search(cmd) for r in BASH_MUT_RES)


def strip_quoted(cmd: str) -> str:
    """Blank out SQL/shell string-literal spans so the boundary scan sees only command tokens
    (repair 3). Dollar-quotes first (they may contain ' and "), then '…' and "…"."""
    s = _DOLLARQ_RE.sub("  ", cmd)
    s = _SQUOTE_RE.sub("  ", s)
    s = _DQUOTE_RE.sub("  ", s)
    return s


def is_boundary(cmd: str) -> bool:
    return bool(BOUNDARY_RE.search(strip_quoted(cmd)))


def _brace_expand(s: str) -> list[str]:
    """Expand shell-style brace groups: 'a/{x,y}.py' -> ['a/x.py', 'a/y.py'].
    Single- and multi-group, left-to-right; returns [s] when there is no group."""
    m = re.search(r"\{([^{}]*)\}", s)
    if not m:
        return [s]
    pre, opts, post = s[: m.start()], m.group(1).split(","), s[m.end():]
    out = []
    for o in opts:
        for tail in _brace_expand(post):
            out.append(pre + o.strip() + tail)
    return out


# Command tokens that "quote" a file as an ARGUMENT rather than declaring intent to change it
# (F45 / event-61 repair). A basename appearing only inside such a span is NOT a declaration — the
# span (command token to end of line / next shell separator) is blanked before matching. This closes
# the coincidental-command-quote unlock (row 24's `pytest tests/test_milestone_b.py` authorizing a
# ruling-work edit) without pricing any label. The `files:` convention is prose (no command token),
# so a declared file list survives the strip and remains the primary, authoritative match surface.
_CMD_TOKEN = (r"pytest|python3?|psql|pip|git|bash|sh|source|make|coverage|mypy|ruff|pyright|"
              r"pre-commit|run_conformance|cd|ls|cat|grep|tee|sed|awk|rm|cp|mv|chmod|touch")
_COMMAND_SPAN_RE = re.compile(r"\b(?:" + _CMD_TOKEN + r")\b[^\n;|&]*")


def strip_command_spans(text: str) -> str:
    """Blank shell-command spans so a file named as a command argument (data) is not read as a
    declaration to change it. Fails SAFE: over-blanking only forces an honest re-ticket (a deny),
    never a false allow (the gate's standing qualification posture, link 6)."""
    return _COMMAND_SPAN_RE.sub("  ", text)


def names_file(basename: str, *texts: str) -> bool:
    """True iff the ticket DECLARES `basename` — it appears (brace-expanded) in the entry text
    AFTER command spans are blanked (F45). A `files:` list survives the strip (it is prose, not a
    command); a coincidental `pytest <file>` command-quote does not. Keying is a file DECLARATION,
    never a subject-authored label (F26)."""
    for t in texts:
        if not t:
            continue
        for expanded in _brace_expand(strip_command_spans(t)):
            if basename in expanded:
                return True
    return False


def _load_state() -> dict:
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(st: dict) -> None:
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f)
    os.replace(tmp, STATE)


def _journal(rec: dict) -> None:
    try:
        os.makedirs(os.path.dirname(JOURNAL), exist_ok=True)
        with open(JOURNAL, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass


def _parse_pg_ts(s: str):
    """Parse a psql timestamptz like '2026-07-05 17:45:19.123+02' to a naive datetime (tz
    trimmed). Both operands compared with this are DB-clock, so the trim is consistent."""
    s = re.sub(r"[+-]\d\d(:?\d\d)?$", "", s.strip()).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"unparseable ts: {s!r}")


def candidate_rows(clock_iso: str):
    """All s12.ledger rows with ts > clock_iso, newest first, as tuples
    (id, ts_iso, statement, rationale, evidence). Keying is filename + currency only — the gate
    is concern/enacts-agnostic (§4.4 demoted, consult 11 §7.1). Raises on DB error so the
    caller can fail closed."""
    ck = clock_iso.replace("'", "''")
    sql = (
        f"SELECT id, ts, statement, coalesce(rationale,''), coalesce(evidence,'') "
        f"FROM {LEDGER} l WHERE ts > '{ck}' ORDER BY ts DESC;"
    )
    out = subprocess.run(
        ["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-F", FS, "-R", RS, "-c", sql],
        capture_output=True, text=True, timeout=8, check=True,
    )
    rows = []
    for rec in out.stdout.split(RS):
        if not rec.strip():
            continue
        parts = rec.split(FS)
        if len(parts) < 5:
            continue
        rid, ts, stmt, rat, ev = parts[:5]
        rows.append((int(rid), ts.strip(), stmt, rat, ev))
    return rows


def current_entry(basename: str, clock_iso: str):
    """Newest s12.ledger row that names `basename` (brace-aware) with ts > clock_iso.
    Returns (id, ts_iso) or None. Raises on DB error. No concern/enacts condition (de-priced)."""
    for rid, ts, stmt, rat, ev in candidate_rows(clock_iso):
        if names_file(basename, stmt, rat, ev):
            return rid, ts
    return None


def entry_flags(entry_id: int) -> list[str]:
    """The ledger-derived ticket_flags for the unlocking entry (all but window_redundant_entry,
    which is gate-state-derived). Computed from one focused query on the winning entry. Raises
    on DB error (the caller fails closed — a flag we cannot compute is not silently dropped)."""
    sql = (
        f"SELECT coalesce(l.concern,''), "
        f"(l.enacts IS NULL OR cardinality(l.enacts) = 0), "
        f"EXISTS (SELECT 1 FROM {LEDGER} t WHERE t.id = ANY(l.enacts) AND t.kind <> 'decision'), "
        f"EXISTS (SELECT 1 FROM {LEDGER} t WHERE t.id = ANY(l.enacts) AND EXISTS "
        f"(SELECT 1 FROM {LEDGER} s WHERE s.supersedes = t.id AND s.ts <= l.ts)) "
        f"FROM {LEDGER} l WHERE l.id = {int(entry_id)};"
    )
    out = subprocess.run(
        ["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-F", FS, "-c", sql],
        capture_output=True, text=True, timeout=8, check=True,
    )
    line = out.stdout.strip().split(RS)[0]
    parts = line.split(FS)
    if len(parts) < 4:
        return []
    concern, empty, nondesign, stale = parts[0].strip(), parts[1].strip() == "t", \
        parts[2].strip() == "t", parts[3].strip() == "t"
    flags = []
    if concern == "enactment" and empty:
        flags.append("enactment_no_enacts")
    if not empty and nondesign:
        flags.append("enacts_nondesign_target")
    if not empty and stale:
        flags.append("enacts_stale_antecedent")
    return flags


def _window_redundant(prev: dict | None, entry_id: int, entry_ts: str) -> bool:
    """True iff the unlocking entry is a redundant ticket: it was logged within WINDOW_S of the
    file's prior ticket while that window was still (nominally) open — i.e. the prior window
    reached fresh-consume by EXPIRY (open flag still True), NOT by a boundary close (which sets
    open=False, the F18-legitimate fresh entry). Compared in DB-clock only (both ts from psql)."""
    if not (isinstance(prev, dict) and prev.get("open") and prev.get("entry_ts")):
        return False
    if prev.get("entry_id") == entry_id:
        return False  # same ticket re-consumed (unreachable via currency, but guard anyway)
    try:
        delta = (_parse_pg_ts(entry_ts) - _parse_pg_ts(prev["entry_ts"])).total_seconds()
    except Exception:
        return False
    return 0.0 < delta <= WINDOW_S


def _deny(msg: str, kind: str = "?", target: str = "") -> int:
    _journal({"ts": datetime.now().isoformat(timespec="milliseconds"),
              "outcome": "denied", "deny_kind": kind, "target": target})
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": msg}}))
    print(msg, file=sys.stderr)
    return 2


def _window_open(entry: dict, now: float) -> bool:
    return bool(entry.get("open")) and (now - entry.get("opened", 0.0)) <= WINDOW_S


def _close_windows(st: dict, reason: str, cmd_head: str) -> None:
    """Close every open consumption window (repair 2 boundary). Idempotent."""
    closed = [k for k, v in st.items() if isinstance(v, dict) and v.get("open")]
    if not closed:
        return
    for k in closed:
        st[k]["open"] = False
    _save_state(st)
    _journal({"ts": datetime.now().isoformat(timespec="milliseconds"),
              "outcome": "boundary", "reason": reason, "closed": len(closed),
              "cmd_head": cmd_head})


def main() -> int:
    raw = sys.stdin.read()
    try:
        p = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # unparseable → cannot identify a governed mutation; pass through (audit logs it)

    tool = _first(p, "tool_name", "toolName", "name", default="")
    inp = _first(p, "tool_input", "toolInput", "input", default={})
    if not isinstance(inp, dict):
        return 0

    if tool in ("Write", "Edit", "NotebookEdit"):
        path = _first(inp, "file_path", "filePath", "path", "notebook_path", default="")
        if not is_governed(path):
            return 0
        # identified governed mutation → gate; fail CLOSED on any error
        now = time.time()
        try:
            st = _load_state()
            key = os.path.abspath(path)
            prev = st.get(key)
            if isinstance(prev, dict) and _window_open(prev, now):
                # repair 2: still inside this file's consumption window — reuse the ticket
                _journal({"ts": datetime.now().isoformat(timespec="milliseconds"),
                          "outcome": "allowed", "file": path, "tool": tool,
                          "unlocked_by_entry": prev.get("entry_id"),
                          "entry_ts": prev.get("entry_ts"), "reused_ticket": True,
                          "ticket_flags": []})
                return 0
            clock = prev.get("entry_ts", EPOCH) if isinstance(prev, dict) else EPOCH
            hit = current_entry(os.path.basename(path), clock)
            if hit is None:
                return _deny(DENY_NEEDS_ENTRY, "needs_entry", path)
            entry_id, entry_ts = hit
            flags = entry_flags(entry_id)
            if _window_redundant(prev, entry_id, entry_ts):
                flags.append("window_redundant_entry")
            # F45 / consult 17 item 5: a FRESH unlock under a ticket older than LONG_LAG_S is
            # flagged (event 61 unlocked at 4880s lag). Measured, never denied — the lag may be
            # legitimate; the review queue consumes the flag. Compared in DB-clock (both from psql).
            try:
                if (datetime.now() - _parse_pg_ts(entry_ts)).total_seconds() > LONG_LAG_S:
                    flags.append("long_lag_unlock")
            except Exception:  # noqa: BLE001
                pass
        except Exception as e:  # noqa: BLE001
            return _deny(DENY_NEEDS_ENTRY + f"  [gate check unavailable: {type(e).__name__}]",
                         "gate_error", path)
        st[key] = {"entry_id": entry_id, "entry_ts": entry_ts, "opened": now, "open": True}
        _save_state(st)
        _journal({"ts": datetime.now().isoformat(timespec="milliseconds"), "outcome": "allowed",
                  "file": path, "unlocked_by_entry": entry_id, "entry_ts": entry_ts,
                  "tool": tool, "reused_ticket": False, "ticket_flags": flags})
        return 0

    if tool == "Bash":
        cmd = _first(inp, "command", default="")
        if isinstance(cmd, str):
            if is_boundary(cmd):
                _close_windows(_load_state(), "test-run/commit", cmd[:80])
            if bash_mutates_governed(cmd):
                return _deny(DENY_BASH_WRITE, "bash_write", cmd[:80])

    return 0


if __name__ == "__main__":
    sys.exit(main())
