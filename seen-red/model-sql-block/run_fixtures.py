#!/usr/bin/env python3
"""seen-red/model-sql-block/run_fixtures.py -- both-polarity proof for
hooks/pretooluse_sql_block.py (work item model-conditional-sql-block: "conditionally block raw
sql depending on which model does it", enforcing the standing delegation policy -- memory
delegation-policy-sonnet-first, 2026-07-14 -- at the PreToolUse/Bash boundary instead of leaving
it to executor discipline).

No DB, no scratch schema: this hook's whole config surface is one project's `.claude/
apparatus.json`, one throwaway scratch directory. Nine cases, each a fresh subprocess invocation
of the real hook (no mocks):

  a-deny-model-strong-enforce  -- session_model="fable-1" (matches policy "fable*": "deny"),
                                 mode="enforce", a real `psql -c "SELECT ..."` command -> DENIED
                                 (permissionDecision=deny, exit 2), teach-text names the
                                 2026-07-14 delegation policy, the two sanctioned routes, and the
                                 governing config key; journal records outcome="denied".
  b-allow-model-strong-enforce -- session_model="sonnet-4-5" (matches "sonnet*": "allow"),
                                 mode="enforce", the IDENTICAL command -> ALLOWED, silent
                                 (permissionDecision=allow, no additionalContext), journal
                                 records outcome="allowed".
  c-sanctioned-wrapper-deny-model -- session_model="fable-1" (a deny model), mode="enforce",
                                 command is `./led decision "..."` naming SQL in its own
                                 argument text -> hook is COMPLETELY INERT: no journal line at
                                 all, allow, no warning -- sanctioned verbs never match,
                                 regardless of model.
  d-weak-mention-deny-model-enforce -- session_model="fable-1", mode="enforce", a command that
                                 merely MENTIONS an SQL keyword with no psql/-c/-f/heredoc/pipe
                                 shape -> WARNS, never blocks (permissionDecision=allow,
                                 additionalContext present), journal outcome="weak_match_warned".
  e-observe-would-deny         -- session_model="fable-1", mode="observe", the strong SQL
                                 command from (a) -> ALLOWED with a loud "would be denied under
                                 enforce" warning, journal outcome="observed_would_deny".
  f-mode-off                   -- mode="off", the strong SQL command from (a) -> genuinely zero
                                 cost: no journal line written at all, exit 0, no stdout.
  g-unknown-model-enforce      -- session_model absent (defaults "unknown"), mode="enforce",
                                 the strong SQL command from (a) -> the shipped default policy's
                                 unknown_model_mode="observe" fires: WARNS, never blocks, even
                                 under enforce.
  h-heredoc-and-pipe-shapes    -- two more STRONG-shape variants (a heredoc `psql ... <<SQL`, and
                                 `echo ... | psql`) against a deny model in enforce -> both
                                 DENIED, proving the match is not `-c`/`-f`-only.
  i-unrecognized-mode          -- mode="bogus" -> falls back to "off" (never widens permission
                                 to enforce/observe on a typo) with a loud stderr warning; the
                                 strong SQL command passes through with NO journal line (mirrors
                                 f-mode-off's own zero-cost fallback).

Plus a final journal-shape check: every case that should have journaled did, in the right order,
each line carrying its own `tool_use_id`.

Usage: python3 seen-red/model-sql-block/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HOOK = REPO / "hooks" / "pretooluse_sql_block.py"

PROBE_DIR = Path("/tmp/.sqlblockprobe")
APPARATUS_PATH = PROBE_DIR / ".claude" / "apparatus.json"
JOURNAL_PATH = PROBE_DIR / ".claude" / "logs" / "sql_block.journal.jsonl"

STRONG_SQL_CMD = 'psql -h h -d d -c "SELECT * FROM kernel.ledger LIMIT 1"'

failures: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    status = "OK" if cond else "FAIL"
    print(f"  [{status}] {label}" + (f" -- {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(f"{label}: {detail}")


def write_apparatus(entry: dict) -> None:
    APPARATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    APPARATUS_PATH.write_text(json.dumps({"mechanisms": {"sql_block": entry}}), encoding="utf-8")


def run_hook(command: str, tool_use_id: str, session_id: str = "sess-1") -> subprocess.CompletedProcess[str]:
    payload = {
        "hook_event_name": "PreToolUse", "tool_name": "Bash",
        "session_id": session_id, "cwd": str(PROBE_DIR), "tool_use_id": tool_use_id,
        "tool_input": {"command": command},
    }
    return subprocess.run(["python3", str(HOOK)], input=json.dumps(payload),
                           capture_output=True, text=True, timeout=15)


def stdout_json(cp: subprocess.CompletedProcess[str]) -> dict | None:
    if not cp.stdout.strip():
        return None
    try:
        return json.loads(cp.stdout.strip().splitlines()[-1])
    except Exception:
        return None


def last_journal_line() -> dict | None:
    if not JOURNAL_PATH.is_file():
        return None
    lines = [l for l in JOURNAL_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    return json.loads(lines[-1]) if lines else None


def journal_line_count() -> int:
    if not JOURNAL_PATH.is_file():
        return 0
    return len([l for l in JOURNAL_PATH.read_text(encoding="utf-8").splitlines() if l.strip()])


def setup() -> None:
    shutil.rmtree(PROBE_DIR, ignore_errors=True)
    PROBE_DIR.mkdir(parents=True)


def teardown() -> None:
    shutil.rmtree(PROBE_DIR, ignore_errors=True)


def main() -> int:
    setup()
    try:
        # ---------------- a: deny-model, strong, enforce -> DENIED ----------------
        print("a-deny-model-strong-enforce")
        write_apparatus({"mode": "enforce", "session_model": "fable-1"})
        cp = run_hook(STRONG_SQL_CMD, "tu-a")
        out = stdout_json(cp)
        check("exit code 2", cp.returncode == 2, f"got {cp.returncode}")
        check("permissionDecision=deny", bool(out) and
              out["hookSpecificOutput"]["permissionDecision"] == "deny", str(out))
        reason = (out or {}).get("hookSpecificOutput", {}).get("permissionDecisionReason", "")
        check("teach-text names delegation policy", "delegation-policy-sonnet-first" in reason
              or "2026-07-14" in reason, reason[:200])
        check("teach-text names sanctioned routes", "Sonnet subagent" in reason and "./led" in reason,
              reason[:200])
        check("teach-text names governing config key", "mechanisms.sql_block" in reason, reason[:200])
        rec = last_journal_line()
        check("journal outcome=denied", bool(rec) and rec.get("outcome") == "denied", str(rec))
        check("journal carries tool_use_id", bool(rec) and rec.get("tool_use_id") == "tu-a", str(rec))

        # ---------------- b: allow-model, strong, enforce -> ALLOWED, silent ----------------
        print("b-allow-model-strong-enforce")
        write_apparatus({"mode": "enforce", "session_model": "sonnet-4-5"})
        cp = run_hook(STRONG_SQL_CMD, "tu-b")
        check("exit code 0", cp.returncode == 0, f"got {cp.returncode}")
        check("no stdout (silent allow)", cp.stdout.strip() == "", cp.stdout[:200])
        rec = last_journal_line()
        check("journal outcome=allowed", bool(rec) and rec.get("outcome") == "allowed", str(rec))

        # ---------------- c: sanctioned wrapper, deny model -> never matches ----------------
        print("c-sanctioned-wrapper-deny-model")
        write_apparatus({"mode": "enforce", "session_model": "fable-1"})
        before = journal_line_count()
        cp = run_hook('./led decision "we need a SELECT against the ledger for this"', "tu-c")
        check("exit code 0", cp.returncode == 0, f"got {cp.returncode}")
        check("no stdout at all", cp.stdout.strip() == "", cp.stdout[:200])
        check("no new journal line", journal_line_count() == before,
              f"before={before} after={journal_line_count()}")

        # ---------------- d: weak mention, deny model, enforce -> WARN not block ----------------
        print("d-weak-mention-deny-model-enforce")
        cp = run_hook("echo we should run a SELECT query later today", "tu-d")
        out = stdout_json(cp)
        check("exit code 0", cp.returncode == 0, f"got {cp.returncode}")
        check("permissionDecision=allow", bool(out) and
              out["hookSpecificOutput"]["permissionDecision"] == "allow", str(out))
        ctx = (out or {}).get("hookSpecificOutput", {}).get("additionalContext", "")
        check("warns about false-positive/weak match", "merely mentions" in ctx, ctx[:200])
        rec = last_journal_line()
        check("journal outcome=weak_match_warned", bool(rec) and
              rec.get("outcome") == "weak_match_warned", str(rec))

        # ---------------- e: observe mode, deny model, strong -> would-deny warn ----------------
        print("e-observe-would-deny")
        write_apparatus({"mode": "observe", "session_model": "fable-1"})
        cp = run_hook(STRONG_SQL_CMD, "tu-e")
        out = stdout_json(cp)
        check("exit code 0", cp.returncode == 0, f"got {cp.returncode}")
        check("permissionDecision=allow (never blocks in observe)", bool(out) and
              out["hookSpecificOutput"]["permissionDecision"] == "allow", str(out))
        ctx = (out or {}).get("hookSpecificOutput", {}).get("additionalContext", "")
        check("warns 'would be denied under enforce'", "WOULD BE DENIED" in ctx, ctx[:200])
        rec = last_journal_line()
        check("journal outcome=observed_would_deny", bool(rec) and
              rec.get("outcome") == "observed_would_deny", str(rec))

        # ---------------- f: mode off -> genuinely zero cost ----------------
        print("f-mode-off")
        write_apparatus({"mode": "off", "session_model": "fable-1"})
        before = journal_line_count()
        cp = run_hook(STRONG_SQL_CMD, "tu-f")
        check("exit code 0", cp.returncode == 0, f"got {cp.returncode}")
        check("no stdout", cp.stdout.strip() == "", cp.stdout[:200])
        check("no new journal line", journal_line_count() == before,
              f"before={before} after={journal_line_count()}")

        # ---------------- g: unknown model, enforce -> observe-only, warn not block ------------
        print("g-unknown-model-enforce")
        write_apparatus({"mode": "enforce"})  # no session_model key at all -> defaults "unknown"
        cp = run_hook(STRONG_SQL_CMD, "tu-g")
        out = stdout_json(cp)
        check("exit code 0 (never blocks unknown model)", cp.returncode == 0, f"got {cp.returncode}")
        check("permissionDecision=allow", bool(out) and
              out["hookSpecificOutput"]["permissionDecision"] == "allow", str(out))
        rec = last_journal_line()
        check("journal session_model=unknown", bool(rec) and rec.get("session_model") == "unknown",
              str(rec))
        check("journal outcome=unknown_model_warned", bool(rec) and
              rec.get("outcome") == "unknown_model_warned", str(rec))

        # ---------------- h: heredoc and pipe shapes, deny model, enforce -> both DENIED --------
        print("h-heredoc-and-pipe-shapes")
        write_apparatus({"mode": "enforce", "session_model": "opus-4"})
        cp1 = run_hook('psql -h h -d d <<SQL\nSELECT 1;\nSQL', "tu-h1")
        check("heredoc form denied", cp1.returncode == 2, f"got {cp1.returncode}")
        cp2 = run_hook("echo 'DROP TABLE foo;' | psql -h h -d d", "tu-h2")
        check("pipe form denied", cp2.returncode == 2, f"got {cp2.returncode}")

        # ---------------- i: unrecognized mode -> falls back to off, warns on stderr -----------
        print("i-unrecognized-mode")
        write_apparatus({"mode": "bogus", "session_model": "fable-1"})
        before = journal_line_count()
        cp = run_hook(STRONG_SQL_CMD, "tu-i")
        check("exit code 0", cp.returncode == 0, f"got {cp.returncode}")
        check("no journal line (degrades to off)", journal_line_count() == before,
              f"before={before} after={journal_line_count()}")
        check("stderr names the bad mode", "mode='bogus'" in cp.stderr or "mode=bogus" in cp.stderr
              or "bogus" in cp.stderr, cp.stderr[:200])

        # ---------------- final: journal shape / ordering ----------------
        print("journal-shape")
        lines = [json.loads(l) for l in JOURNAL_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
        ids = [l.get("tool_use_id") for l in lines]
        expected = ["tu-a", "tu-b", "tu-d", "tu-e", "tu-g", "tu-h1", "tu-h2"]  # c, f, i journal nothing
        check("journal carries exactly the expected lines, in order", ids == expected,
              f"got {ids}")
    finally:
        teardown()

    if failures:
        print(f"\nFAILURES ({len(failures)}):")
        for f in failures:
            print(f"  !! {f}")
        return 1
    print("\nOK -- all cases pass. hooks/pretooluse_sql_block.py both-polarity proven.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
