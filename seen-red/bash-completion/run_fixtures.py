#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T21:36:35Z
#   last-change: 2026-07-14T01:15:49Z
#   contributors: e4410ef6/main, a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for hooks/posttooluse_bash_completion.py, REWRITTEN
2026-07-14 (design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md sec-6.4, the M1 counterparty fix).

WHY THIS WAS REWRITTEN, NOT JUST EXTENDED: the RCA that motivated this fix (design/
ORCH-RCA-PAIRING-KEY-DIVERGENCE.md sec-5, lapse 1) found the PRIOR version of this fixture's
positive case authored the dispatch side BY HAND from the completion hook's own assumption
(`append_invocation()` hashed raw, un-rewritten command text into a synthetic dispatch record) --
the real dispatcher, `hooks/stamp_intercept.py`, was never executed, so its command-rewriting
behavior (the actual root cause of the pairing defect this fix repairs) never entered the test.
"Real infra, no mocks" was true of the completion hook and false of its counterparty. Per
ADR-0011's mechanization discipline (the RCA's own M1): a fixture whose subject is a correlation
contract between N producers must execute ALL N real producers in their real sequence for its
positive case. This rewrite does that: the REAL `hooks/stamp_intercept.py` mints the dispatch
line and rewrites the command; the REAL `hooks/posttooluse_bash_completion.py` journals the
completion from that rewritten command; the REAL `engine/contemp_edb.dispatch_token_by_tool_use_id`
/ `join_bash_completions` (the actual consumer join code, not reimplemented here) perform the
read-time join.

Cases:

  a-identity-join-through-real-rewrite (POSITIVE) -- a scratch wired world; the REAL
    stamp_intercept.py dispatches a Bash command carrying a tool_use_id, minting a token AND
    rewriting the command text (the PGOPTIONS injection). The REAL posttooluse_bash_completion.py
    then journals a completion from a PostToolUse payload carrying THAT rewritten command and the
    SAME tool_use_id. The REAL consumer join (engine.contemp_edb) is run over both journals and
    must yield exactly one (token, ts) pair for the dispatch's own token -- proving identity
    survives the command rewrite that killed the old content-hash design.
  b-ts-only-no-tool-use-id (NEGATIVE, mandatory per RCA sec-6.4(ii)) -- a completion payload with
    no tool_use_id journals a line (facts-local-to-this-event, honestly) and the consumer join
    pairs it to nothing.
  c-pre-fix-hook-goes-red (NEGATIVE CONTROL, mandatory per RCA sec-6.4(i)) -- the SAME two-party
    positive sequence (real stamp_intercept.py rewrite + real dispatch journal), fed to the
    PRE-FIX completion hook (materialized from commit 7567dd4, the last commit before this fix)
    instead of the current one: the join must find NO pair, witnessing that this fixture would
    have caught the defect this fix repairs.
  d-mode-off          -- apparatus.json sets bash_completion.mode="off" -> zero cost: no
                         completion line at all.
  e-mode-enforce-downgrade -- mode="enforce" (NAMED-IMPOSSIBLE for a PostToolUse leg) -> warns
                         loudly on STDERR naming the downgrade, still journals (as "observe").
  f-non-bash-tool     -- tool_name="Write" -> no completion line, no output at all.
  g-unwired           -- no GATE_SUBJECT_ROOT and no cwd resolving to a real directory -> silent,
                         nothing to journal into.

Usage: python3 seen-red/bash-completion/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DISPATCH_HOOK = REPO / "hooks" / "stamp_intercept.py"
COMPLETION_HOOK = REPO / "hooks" / "posttooluse_bash_completion.py"
# The commit this fix builds directly on top of -- posttooluse_bash_completion.py's last
# pre-fix state, materialized live for case c's negative control (never hand-copied).
PRE_FIX_REF = "7567dd4"

# TOP-OF-FILE, EAGER (the lazy-import gate, gates/no_lazy_imports.py, bans a deferred import
# inside a function body -- this project's law has no allowlist). The REAL consumer join code
# this fixture proves against (RCA sec-6.4/M1: never a fixture-side reimplementation) lives in
# engine/, which is not normally on sys.path; the path insert must therefore happen here, at
# module scope, before the import that depends on it -- eager, not deferred.
sys.path.insert(0, str(REPO / "engine"))
import contemp_edb  # noqa: E402 -- see the sys.path.insert immediately above

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)


_TOKEN_RE = re.compile(r"app\.vendor_invocation=([0-9a-f-]+)")


def _make_world() -> tuple[Path, Path]:
    """A throwaway wired world for stamp_intercept.py: deployment.json + a healthy secret --
    same shape seen-red/stamp-intercept-invocation-token/run_fixtures.py already uses."""
    root = Path(tempfile.mkdtemp(prefix="bashcomp-m1-"))
    (root / ".claude" / "secrets").mkdir(parents=True)
    secret = root / ".claude" / "secrets" / "stamp_secret.hex"
    secret.write_text(os.urandom(32).hex())
    secret.chmod(0o600)
    (root / "deployment.json").write_text(json.dumps(
        {"db": "toy", "host": fixture_pghost(), "schema": "bashcompm1",
         "kern": "bashcompm1_kernel", "role": "bashcompm1_rw"}))
    return root, secret


def _write_apparatus(root: Path, mechanisms: dict) -> None:
    (root / ".claude").mkdir(exist_ok=True)
    (root / ".claude" / "apparatus.json").write_text(json.dumps({"mechanisms": mechanisms}))


def _run_dispatch(root: Path, secret: Path, command: str, tool_use_id: str,
                   session_id: str) -> tuple[str, dict | None]:
    """Run the REAL hooks/stamp_intercept.py PreToolUse leg. Returns (rewritten_command,
    dispatch_journal_line-or-None)."""
    payload = {"tool_name": "Bash", "tool_input": {"command": command},
               "cwd": str(root), "session_id": session_id, "tool_use_id": tool_use_id}
    env = dict(os.environ)
    env["STAMP_SECRET"] = str(secret)
    env.pop("LEDGER_DEPLOYMENT", None)
    env.pop("GATE_SUBJECT_ROOT", None)
    cp = subprocess.run([sys.executable, str(DISPATCH_HOOK)], input=json.dumps(payload),
                        capture_output=True, text=True, env=env)
    try:
        rewritten = json.loads(cp.stdout)["hookSpecificOutput"]["updatedInput"]["command"]
    except (ValueError, KeyError):
        rewritten = command  # unwired/passthrough (should not happen in a wired world)
    journal = root / ".claude" / "logs" / "invocations.jsonl"
    line = None
    if journal.exists():
        lines = journal.read_text().splitlines()
        line = json.loads(lines[-1]) if lines else None
    return rewritten, line


def _run_completion(hook_path: Path, root: Path, rewritten_command: str,
                     tool_use_id: str | None, session_id: str) -> dict | None:
    """Run a (real, current OR materialized pre-fix) posttooluse_bash_completion.py PostToolUse
    leg against the REWRITTEN command text -- the exact text a real PostToolUse payload would
    carry after stamp_intercept.py's own rewrite. Returns the last journaled line, or None."""
    payload = {"hook_event_name": "PostToolUse", "tool_name": "Bash",
               "tool_input": {"command": rewritten_command}, "session_id": session_id,
               "cwd": str(root), "duration_ms": 42}
    if tool_use_id is not None:
        payload["tool_use_id"] = tool_use_id
    env = dict(os.environ)
    env["GATE_SUBJECT_ROOT"] = str(root)
    subprocess.run([sys.executable, str(hook_path)], input=json.dumps(payload),
                   capture_output=True, text=True, env=env)
    comp_journal = root / ".claude" / "logs" / "bash_completions.jsonl"
    if not comp_journal.exists():
        return None
    lines = comp_journal.read_text().splitlines()
    return json.loads(lines[-1]) if lines else None


def _materialize_pre_fix_hook() -> Path:
    """Extract hooks/posttooluse_bash_completion.py AS IT STOOD at PRE_FIX_REF, live from git --
    never a hand-copied stand-in (RCA sec-5 lapse 1's own lesson, applied to this negative
    control too)."""
    cp = subprocess.run(["git", "show", f"{PRE_FIX_REF}:hooks/posttooluse_bash_completion.py"],
                        cwd=REPO, capture_output=True, text=True, check=True)
    tmp_dir = Path(tempfile.mkdtemp(prefix="prefix-hook-"))
    tmp = tmp_dir / "posttooluse_bash_completion.py"
    tmp.write_text(cp.stdout)
    return tmp


def _real_join(inv_recs: list[dict], comp_recs: list[dict]) -> list[tuple[str, int]]:
    """The REAL consumer join, the module-level `contemp_edb` import above -- never reimplemented
    here (RCA sec-6.4/M1: a pairing fixture's assertion must run the actual join code)."""
    token_map = contemp_edb.dispatch_token_by_tool_use_id(inv_recs)
    joined, _skip = contemp_edb.join_bash_completions(comp_recs, token_map)
    return joined


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def main() -> int:
    failures: list[str] = []

    # --- a-identity-join-through-real-rewrite (POSITIVE): the full two-party sequence ----------
    root_a, secret_a = _make_world()
    try:
        _write_apparatus(root_a, {"stamp_intercept": {"mode": "enforce"},
                                   "bash_completion": {"mode": "observe"}})
        rewritten, dispatch_line = _run_dispatch(
            root_a, secret_a, "echo real-rewrite-a", "toolu_case_a", "sess-a")
        tok_match = _TOKEN_RE.search(rewritten)
        completion_line = _run_completion(
            COMPLETION_HOOK, root_a, rewritten, "toolu_case_a", "sess-a")
        inv_recs = _read_jsonl(root_a / ".claude" / "logs" / "invocations.jsonl")
        comp_recs = _read_jsonl(root_a / ".claude" / "logs" / "bash_completions.jsonl")
        joined = _real_join(inv_recs, comp_recs)
        ok = (rewritten != "echo real-rewrite-a"  # stamp_intercept really rewrote it
              and tok_match is not None
              and dispatch_line is not None
              and dispatch_line.get("tool_use_id") == "toolu_case_a"
              and completion_line is not None
              and completion_line.get("tool_use_id") == "toolu_case_a"
              and "token" not in completion_line  # no stored verdict, per 6.1
              and "pairing" not in completion_line
              and joined == [(dispatch_line.get("token"), joined[0][1])] if joined else False)
        check("a-identity-join-through-real-rewrite", ok,
              f"rewritten={rewritten!r} dispatch_token={dispatch_line.get('token') if dispatch_line else None} "
              f"completion={completion_line} joined={joined}", failures)
    finally:
        shutil.rmtree(root_a, ignore_errors=True)

    # --- b-ts-only-no-tool-use-id (NEGATIVE, mandatory) ------------------------------------------
    root_b, _ = _make_world()
    try:
        _write_apparatus(root_b, {"bash_completion": {"mode": "observe"}})
        completion_line = _run_completion(
            COMPLETION_HOOK, root_b, "echo no-tool-use-id", None, "sess-b")
        comp_recs = _read_jsonl(root_b / ".claude" / "logs" / "bash_completions.jsonl")
        joined = _real_join([{"tool_use_id": "toolu_unrelated", "token": "tok-unrelated",
                              "wall_clock": "2026-07-14T00:00:00Z"}], comp_recs)
        ok = (completion_line is not None and "tool_use_id" not in completion_line
              and joined == [])
        check("b-ts-only-no-tool-use-id", ok,
              f"completion={completion_line} joined={joined}", failures)
    finally:
        shutil.rmtree(root_b, ignore_errors=True)

    # --- c-pre-fix-hook-goes-red (NEGATIVE CONTROL, mandatory per RCA sec-6.4(i)) ----------------
    root_c, secret_c = _make_world()
    pre_fix_hook = None
    try:
        _write_apparatus(root_c, {"stamp_intercept": {"mode": "enforce"},
                                   "bash_completion": {"mode": "observe"}})
        rewritten, dispatch_line = _run_dispatch(
            root_c, secret_c, "echo real-rewrite-c", "toolu_case_c", "sess-c")
        pre_fix_hook = _materialize_pre_fix_hook()
        completion_line = _run_completion(
            pre_fix_hook, root_c, rewritten, "toolu_case_c", "sess-c")
        # The pre-fix hook never read tool_use_id at all -- its own pairing verdict is what we
        # assert went red: it always falls back to ts-only against a real rewritten command,
        # because its FIFO-by-hash never matches (the exact defect this fix repairs).
        ok = (completion_line is not None
              and completion_line.get("pairing") == "ts-only"
              and completion_line.get("token") is None)
        check("c-pre-fix-hook-goes-red", ok,
              f"pre-fix completion record against a REAL post-rewrite command: {completion_line} "
              f"(expected pairing='ts-only', token=None -- the defect this fix repairs, witnessed "
              f"red on the exact commit this fix builds on top of, {PRE_FIX_REF})", failures)
    finally:
        shutil.rmtree(root_c, ignore_errors=True)
        if pre_fix_hook is not None:
            shutil.rmtree(pre_fix_hook.parent, ignore_errors=True)

    # --- d-mode-off: no completion line at all ---------------------------------------------------
    root_d, _ = _make_world()
    try:
        _write_apparatus(root_d, {"bash_completion": {"mode": "off"}})
        before = len(_read_jsonl(root_d / ".claude" / "logs" / "bash_completions.jsonl"))
        _run_completion(COMPLETION_HOOK, root_d, "echo should-not-journal", "toolu-d", "sess-d")
        after = len(_read_jsonl(root_d / ".claude" / "logs" / "bash_completions.jsonl"))
        check("d-mode-off", after == before, f"before={before} after={after}", failures)
    finally:
        shutil.rmtree(root_d, ignore_errors=True)

    # --- e-mode-enforce-downgrade: warns on stderr, still journals like observe -----------------
    root_e, _ = _make_world()
    try:
        _write_apparatus(root_e, {"bash_completion": {"mode": "enforce"}})
        payload = {"hook_event_name": "PostToolUse", "tool_name": "Bash",
                   "tool_input": {"command": "echo enforce-requested"}, "session_id": "sess-e",
                   "cwd": str(root_e), "tool_use_id": "toolu-e"}
        env = dict(os.environ)
        env["GATE_SUBJECT_ROOT"] = str(root_e)
        r = subprocess.run([sys.executable, str(COMPLETION_HOOK)], input=json.dumps(payload),
                           capture_output=True, text=True, env=env)
        lines = _read_jsonl(root_e / ".claude" / "logs" / "bash_completions.jsonl")
        ok = (r.returncode == 0 and len(lines) == 1 and "IMPOSSIBLE" in r.stderr
              and lines[0].get("tool_use_id") == "toolu-e")
        check("e-mode-enforce-downgrade", ok,
              f"exit={r.returncode} stderr_has_impossible_warning={'IMPOSSIBLE' in r.stderr} "
              f"lines={lines}", failures)
    finally:
        shutil.rmtree(root_e, ignore_errors=True)

    # --- f-non-bash-tool: a Write call produces nothing -------------------------------------------
    root_f, _ = _make_world()
    try:
        payload = {"hook_event_name": "PostToolUse", "tool_name": "Write",
                   "tool_input": {"file_path": "/tmp/whatever"}, "session_id": "sess-f",
                   "cwd": str(root_f)}
        env = dict(os.environ)
        env["GATE_SUBJECT_ROOT"] = str(root_f)
        r = subprocess.run([sys.executable, str(COMPLETION_HOOK)], input=json.dumps(payload),
                           capture_output=True, text=True, env=env)
        lines = _read_jsonl(root_f / ".claude" / "logs" / "bash_completions.jsonl")
        ok = (r.returncode == 0 and len(lines) == 0 and r.stdout.strip() == "")
        check("f-non-bash-tool", ok,
              f"exit={r.returncode} stdout={r.stdout.strip()!r} lines={lines}", failures)
    finally:
        shutil.rmtree(root_f, ignore_errors=True)

    # --- g-unwired: no GATE_SUBJECT_ROOT, no real cwd directory -----------------------------------
    payload = {"hook_event_name": "PostToolUse", "tool_name": "Bash",
               "tool_input": {"command": "echo unwired"}, "session_id": "sess-g",
               "cwd": "/nonexistent/nowhere"}
    r = subprocess.run([sys.executable, str(COMPLETION_HOOK)], input=json.dumps(payload),
                       capture_output=True, text=True, env={})
    ok = (r.returncode == 0
          and not Path("/nonexistent/nowhere/.claude/logs/bash_completions.jsonl").exists())
    check("g-unwired", ok, f"exit={r.returncode}", failures)

    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL CASES OK -- bash_completion identity-join proof clean (real stamp_intercept.py "
          "rewrite survives into a real join on tool_use_id; ts-only/no-tool_use_id honest "
          "fallback; the pre-fix hook witnessed red against the same real two-party sequence; "
          "off/enforce-downgrade/non-bash/unwired all behave as designed), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
