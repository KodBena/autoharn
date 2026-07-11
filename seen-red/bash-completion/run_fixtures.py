#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T21:36:35Z
#   last-change: 2026-07-11T21:36:35Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for hooks/posttooluse_bash_completion.py (small-
follow-ups commission item 4). No database is involved -- this hook's only inputs are the
stdin payload and two on-disk JSONL files (invocations.jsonl to pair against, its own
bash_completions.jsonl to write) -- so this fixture is pure filesystem, mirroring
seen-red/read-observer/run_fixtures.py's own shape.

Real infra, no mocks: a throwaway scratch directory under /tmp, torn down before AND after this
file runs so re-running it never leaves residue. Cases, run as an independent sequence unless
noted:

  a-token-pairing     -- invocations.jsonl carries one dispatch record with a known token and
                         command_sha256; a completion for the SAME command text pairs to it:
                         token set, pairing="token", dispatch_wall_clock carried through.
  b-ts-only-fallback  -- a completion for a command with NO matching dispatch record ->
                         pairing="ts-only", token=null -- the honest fallback, not a failure.
  c-fifo-double-dispatch -- TWO dispatch records share the same command_sha256 (a command run
                         twice); TWO completions for that same text pair FIFO -- the first
                         completion claims the earlier dispatch, the second claims the later
                         one, never the same dispatch twice.
  d-mode-off          -- apparatus.json sets bash_completion.mode="off" -> genuinely zero cost:
                         no completion line at all, even though a real Bash call just finished.
  e-mode-enforce-downgrade -- mode="enforce" (NAMED-IMPOSSIBLE for a PostToolUse leg) -> warns
                         loudly on STDERR naming the downgrade, then behaves like "observe".
  f-non-bash-tool     -- tool_name="Write" -> no completion line, no output at all.
  g-unwired           -- no GATE_SUBJECT_ROOT and no cwd resolving to a real directory -> silent,
                         nothing to journal into.

Usage: python3 seen-red/bash-completion/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HOOK = REPO / "hooks" / "posttooluse_bash_completion.py"

PROBE_DIR = Path("/tmp/.bashcompprobe")
INV_PATH = PROBE_DIR / ".claude" / "logs" / "invocations.jsonl"
COMPLETION_PATH = PROBE_DIR / ".claude" / "logs" / "bash_completions.jsonl"


def teardown() -> None:
    shutil.rmtree(PROBE_DIR, ignore_errors=True)


def write_apparatus(mechanisms: dict) -> None:
    (PROBE_DIR / ".claude").mkdir(parents=True, exist_ok=True)
    (PROBE_DIR / ".claude" / "apparatus.json").write_text(
        json.dumps({"mechanisms": mechanisms}), encoding="utf-8")


def append_invocation(token: str, wall_clock: str, command: str) -> None:
    INV_PATH.parent.mkdir(parents=True, exist_ok=True)
    rec = {"token": token, "wall_clock": wall_clock, "session_id": "dispatcher-sess",
           "command_sha256": hashlib.sha256(command.encode("utf-8")).hexdigest(),
           "command_head": command[:120]}
    with open(INV_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def run_hook(command: str, session_id: str, cwd: str | None,
             env_extra: dict[str, str]) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({
        "hook_event_name": "PostToolUse", "tool_name": "Bash",
        "tool_input": {"command": command},
        "session_id": session_id, "cwd": cwd or "",
    })
    env = dict(os.environ)
    env.update(env_extra)
    return subprocess.run([sys.executable, str(HOOK)], input=payload,
                          capture_output=True, text=True, env=env)


def run_hook_other_tool(tool_name: str, cwd: str) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({
        "hook_event_name": "PostToolUse", "tool_name": tool_name,
        "tool_input": {"file_path": "/tmp/whatever"},
        "session_id": "sess-f", "cwd": cwd,
    })
    env = dict(os.environ)
    env["GATE_SUBJECT_ROOT"] = cwd
    return subprocess.run([sys.executable, str(HOOK)], input=payload,
                          capture_output=True, text=True, env=env)


def completion_lines() -> list[dict]:
    if not COMPLETION_PATH.exists():
        return []
    return [json.loads(ln) for ln in COMPLETION_PATH.read_text(encoding="utf-8").splitlines()
            if ln.strip()]


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def main() -> int:
    teardown()
    failures: list[str] = []
    env = {"GATE_SUBJECT_ROOT": str(PROBE_DIR)}

    # --- a-token-pairing: one dispatch record, one matching completion -----------------------
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    write_apparatus({})  # default -- bash_completion resolves to "observe"
    append_invocation("tok-a", "2026-07-11T10:00:00.000Z", "echo hello-a")
    r = run_hook("echo hello-a", "sess-a", str(PROBE_DIR), env)
    lines = completion_lines()
    ok = (r.returncode == 0 and len(lines) == 1
          and lines[0].get("token") == "tok-a"
          and lines[0].get("pairing") == "token"
          and lines[0].get("dispatch_wall_clock") == "2026-07-11T10:00:00.000Z"
          and isinstance(lines[0].get("ts"), str) and lines[0]["ts"].endswith("Z"))
    check("a-token-pairing", ok,
          f"exit={r.returncode} rec={lines[-1] if lines else None}", failures)

    # --- b-ts-only-fallback: no matching dispatch record --------------------------------------
    r = run_hook("echo no-dispatch-for-this", "sess-b", str(PROBE_DIR), env)
    lines = completion_lines()
    ok = (r.returncode == 0 and len(lines) == 2
          and lines[1].get("token") is None
          and lines[1].get("pairing") == "ts-only"
          and "dispatch_wall_clock" not in lines[1])
    check("b-ts-only-fallback", ok,
          f"exit={r.returncode} rec={lines[-1] if lines else None}", failures)

    # --- c-fifo-double-dispatch: two dispatches, same command text, FIFO pairing --------------
    append_invocation("tok-c1", "2026-07-11T10:05:00.000Z", "echo hello-c")
    append_invocation("tok-c2", "2026-07-11T10:05:05.000Z", "echo hello-c")
    r1 = run_hook("echo hello-c", "sess-c1", str(PROBE_DIR), env)
    r2 = run_hook("echo hello-c", "sess-c2", str(PROBE_DIR), env)
    lines = completion_lines()
    ok = (r1.returncode == 0 and r2.returncode == 0 and len(lines) == 4
          and lines[2].get("token") == "tok-c1" and lines[3].get("token") == "tok-c2")
    check("c-fifo-double-dispatch", ok,
          f"lines[2].token={lines[2].get('token') if len(lines) > 2 else None} "
          f"lines[3].token={lines[3].get('token') if len(lines) > 3 else None} "
          f"(expect tok-c1 then tok-c2, never the same dispatch reused)", failures)

    # --- d-mode-off: no completion line at all -------------------------------------------------
    write_apparatus({"bash_completion": {"mode": "off"}})
    before = len(completion_lines())
    r = run_hook("echo should-not-journal", "sess-d", str(PROBE_DIR), env)
    after = len(completion_lines())
    ok = (r.returncode == 0 and after == before)
    check("d-mode-off", ok, f"exit={r.returncode} before={before} after={after}", failures)

    # --- e-mode-enforce-downgrade: warns on stderr, still journals like observe ---------------
    write_apparatus({"bash_completion": {"mode": "enforce"}})
    before = len(completion_lines())
    r = run_hook("echo enforce-requested", "sess-e", str(PROBE_DIR), env)
    after = completion_lines()
    ok = (r.returncode == 0 and len(after) == before + 1
          and "IMPOSSIBLE" in r.stderr and after[-1].get("pairing") == "ts-only")
    check("e-mode-enforce-downgrade", ok,
          f"exit={r.returncode} stderr_has_impossible_warning={'IMPOSSIBLE' in r.stderr} "
          f"before={before} after={len(after)}", failures)
    write_apparatus({})  # restore default

    # --- f-non-bash-tool: a Write call produces nothing -----------------------------------------
    before = len(completion_lines())
    r = run_hook_other_tool("Write", str(PROBE_DIR))
    after = len(completion_lines())
    ok = (r.returncode == 0 and after == before and r.stdout.strip() == "")
    check("f-non-bash-tool", ok,
          f"exit={r.returncode} stdout={r.stdout.strip()!r} before={before} after={after}",
          failures)

    # --- g-unwired: no GATE_SUBJECT_ROOT, no real cwd directory --------------------------------
    before = len(completion_lines())
    r = run_hook("echo unwired", "sess-g", "/nonexistent/nowhere", {})
    after = len(completion_lines())
    ok = (r.returncode == 0 and after == before)
    check("g-unwired", ok, f"exit={r.returncode} before={before} after={after}", failures)

    teardown()

    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL CASES OK -- bash_completion both-polarity proof clean (token-pairing, ts-only "
          "fallback, FIFO double-dispatch, off/enforce-downgrade/non-bash/unwired all behave "
          "as designed), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
