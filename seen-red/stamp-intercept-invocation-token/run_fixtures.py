#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-10T23:41:36Z
#   last-change: 2026-07-10T23:42:15Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py — both-polarity proof for the per-invocation contemporaneity token that
hooks/stamp_intercept.py mints (vestigial_documentation/design/ORCH-CONTEMPORANEITY-AUDIT.md Part 1; s23 kernel delta).

The existing seen-red/stamp-intercept-secret suite already proves the HMAC-stamp fail-closed
path; this SIBLING suite proves the SIXTH GUC + its journal, which the substring-matching
harness there cannot express (the journal is a written FILE, and the whole point is that the
token in PGOPTIONS and the token in the journal MATCH — a correlation, not a substring).

Three inline cases (self-contained temp worlds, scrubbed in `finally`):

  a-healthy-injects-and-journals (POSITIVE): a wired world, healthy secret, mode enforce ->
     the injected command carries `app.vendor_invocation=<uuid>` AND exactly one
     invocations.jsonl line is written whose `token` EQUALS that injected uuid, carrying
     wall_clock / session_id / command_sha256 / command_head, and tool_use_id iff the payload
     carried one. This is the (3b) hook side of the witness.

  b-off-mode-no-token-no-journal (NEGATIVE): same healthy world but apparatus
     mechanisms.stamp_intercept.mode="off" -> the command passes through untouched (no
     PGOPTIONS, no token) AND no invocations.jsonl is written at all. (3c) — an off-mode world
     mints no token, so the audit verb must read that as an UNJOURNALED ERA, never "no findings".

  c-unwired-no-token-no-journal (NEGATIVE): no deployment.json, STAMP_SECRET unset ->
     byte-held unwired passthrough: no injection, no token, no journal.

RED (pre-feature): the HEAD hook injected the four HMAC GUCs but NEVER `app.vendor_invocation`,
and wrote NO invocations.jsonl — see red.txt (real captured output). Exit 0 iff every case
matches; 1 otherwise. Run: python3 seen-red/stamp-intercept-invocation-token/run_fixtures.py
Lazy imports banned.
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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HOOK = REPO / "hooks" / "stamp_intercept.py"
_TOKEN_RE = re.compile(r"app\.vendor_invocation=([0-9a-f-]+)")


def _make_world(mode: str | None) -> Path:
    """A throwaway wired world: deployment.json + a healthy secret + optional apparatus mode."""
    root = Path(tempfile.mkdtemp(prefix="inv-tok-"))
    (root / ".claude" / "secrets").mkdir(parents=True)
    secret = root / ".claude" / "secrets" / "stamp_secret.hex"
    secret.write_text(os.urandom(32).hex())
    secret.chmod(0o600)
    (root / "deployment.json").write_text(json.dumps(
        {"db": "toy", "host": fixture_pghost(), "schema": "invprobe",
         "kern": "invprobe_kernel", "role": "invprobe_rw"}))
    if mode is not None:
        (root / ".claude").mkdir(exist_ok=True)
        (root / ".claude" / "apparatus.json").write_text(json.dumps(
            {"mechanisms": {"stamp_intercept": {"mode": mode}}}))
    return root, secret


def _drive(root: Path, secret: Path | None, *, tool_use_id: str | None) -> tuple[str, dict | None]:
    payload = {"tool_name": "Bash", "tool_input": {"command": "psql -d toy -c 'select 1'"},
               "cwd": str(root), "session_id": "tok-sess"}
    if tool_use_id is not None:
        payload["tool_use_id"] = tool_use_id
    env = dict(os.environ)
    env.pop("LEDGER_DEPLOYMENT", None)
    env.pop("GATE_SUBJECT_ROOT", None)
    if secret is None:
        env.pop("STAMP_SECRET", None)  # genuinely unwired: STAMP_SECRET unset, no deployment.json
    else:
        env["STAMP_SECRET"] = str(secret)
    cp = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                        capture_output=True, text=True, env=env)
    out = cp.stdout
    try:
        injected = json.loads(out)["hookSpecificOutput"]["updatedInput"]["command"]
    except (ValueError, KeyError):
        injected = out  # passthrough (no updatedInput): the raw stdout, which for a no-op is empty
    journal = root / ".claude" / "logs" / "invocations.jsonl"
    jrec = None
    if journal.exists():
        lines = journal.read_text().splitlines()
        jrec = json.loads(lines[-1]) if lines else None
    return injected, jrec


def case_a() -> list[str]:
    errs: list[str] = []
    root, secret = _make_world(mode="enforce")
    try:
        injected, jrec = _drive(root, secret, tool_use_id="toolu_case_a")
        m = _TOKEN_RE.search(injected)
        if not m:
            errs.append("no app.vendor_invocation in the injected command")
            return errs
        tok = m.group(1)
        if jrec is None:
            errs.append("no invocations.jsonl line written")
            return errs
        if jrec.get("token") != tok:
            errs.append(f"journal token {jrec.get('token')!r} != injected token {tok!r}")
        for k in ("wall_clock", "session_id", "command_sha256", "command_head"):
            if k not in jrec:
                errs.append(f"journal line missing {k}")
        if jrec.get("session_id") != "tok-sess":
            errs.append(f"journal session_id {jrec.get('session_id')!r} != tok-sess")
        if jrec.get("tool_use_id") != "toolu_case_a":
            errs.append("journal did not carry the payload's tool_use_id")
        print(f"  a: injected token={tok}  journal={jrec}")
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return errs


def _negative(mode: str | None, wired: bool, label: str) -> list[str]:
    errs: list[str] = []
    if wired:
        root, secret = _make_world(mode=mode)
    else:
        root = Path(tempfile.mkdtemp(prefix="inv-tok-"))  # no deployment.json, no secret file
        secret = None  # STAMP_SECRET unset in _drive: a genuinely unwired passthrough, not a deny
    try:
        injected, jrec = _drive(root, secret, tool_use_id=None)
        if _TOKEN_RE.search(injected or ""):
            errs.append(f"{label}: a token was injected but should NOT have been")
        if jrec is not None:
            errs.append(f"{label}: an invocations.jsonl line was written but should NOT have been")
        print(f"  {label}: no token, no journal (injected={injected[:40]!r})")
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return errs


def main() -> int:
    failures: list[str] = []
    print("=== a-healthy-injects-and-journals (POSITIVE) ===")
    failures += [f"a: {e}" for e in case_a()]
    print("=== b-off-mode-no-token-no-journal (NEGATIVE) ===")
    failures += _negative(mode="off", wired=True, label="b-off")
    print("=== c-unwired-no-token-no-journal (NEGATIVE) ===")
    failures += _negative(mode=None, wired=False, label="c-unwired")
    print()
    if failures:
        print(f"run_fixtures: {len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  !! {f}")
        return 1
    print("run_fixtures: all 3 case(s) passed (token injected+journaled on a healthy wired world; "
          "no token and no journal off-mode or unwired).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
