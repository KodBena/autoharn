#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T12:38:35Z
#   last-change: 2026-07-09T12:38:35Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

"""stamp_intercept — the WRITE-TIME interception hook (BACKLOG ffafa59). A PreToolUse hook on Bash: when
the subject's command invokes psql against the ledger database -- directly, OR indirectly through a
`led`-family wrapper script that hides psql inside it (the matcher-fix class below) -- it computes the
interception stamp HMAC(secret, session_id||agent_id||ts) and REWRITES the command to carry it into the
connection as `app.vendor_*` GUCs (via PGOPTIONS). The kernel's set_stamp trigger then validates the
stamp against the apparatus secret it recomputes SECURITY-DEFINER-side. The hook STAMPS; the trigger
LANDS it; the model neither types the stamp (it has no secret) nor omits it (the hook stamps every
intercepted write). A self-review by one invocation carries the SAME agent id as its authoring —
visible; a genuinely distinct subagent carries a different one (its `agent_id`, confirmed present in
hook context by the lab shakedown).

MATCHER FIX (BACKLOG "Correction to finding 3", 2026-07-09): the matcher used to require the literal
token `psql` naming the ledger db in the command TEXT -- `./led decision "..."` hides its own internal
psql call inside the script, so every led-mediated write passed through UNSTAMPED even in a
toy-launched, hook-wired session (led is an accidental instance of this file's own script-evasion
tripwire). Fixed by adding a SECOND, independent match: a command whose first word (after optional
leading `VAR=value` env-var prefixes) is `./led`, bare `led`, or any absolute/relative path ending
`/led`. Kept conservative on purpose (fail-open spirit unchanged): only the LED WRAPPER'S OWN invocation
is recognized this way -- a command that merely mentions "led" as data, or that reaches led via a
shell construct this simple regex does not parse (e.g. `cd x && ./led ...`), is not matched, and is
therefore treated exactly the way an ordinary unmatched write always was (unstamped, never blocked; the
trigger, not this hook, is the fail-closed side of that boundary). The existing `export PGOPTIONS=...;`
rewrite is reused UNCHANGED for a led match: it is an export, not a one-command prefix, so it inherits
into whatever psql `led`'s own script body invokes, with zero changes to `led` itself.

CONFIG (provisioned at arm; the subject never sees this file's prose, only the injected GUCs):
  STAMP_DB / LEDGER_DB  — the ledger database name to match for the raw-psql shape (only psql calls
                  naming it are stamped by that path; the led-invocation match below does not consult
                  this value at all, since a project's `led` script is always bound to that project's
                  one ledger). LEDGER_DB is the neutral name (matches engine/targets.py's own
                  LEDGER_DB/LEDGER_SCHEMA/LEDGER_KERN convention, ADR-0012 P1); STAMP_DB is kept
                  working as a deprecated alias so nothing breaks mid-transition. Precedence when both
                  are set: LEDGER_DB, then STAMP_DB, then the project's deployment.json `db` field
                  (below), then unmatched.
  STAMP_SECRET  — path to a chmod-600 file holding the apparatus secret as hex (the hook's read of the
                  one secret; the trigger reads the same value from kernel.stamp_secret). Same OS user =
                  hunt-able secret — the pre-registered tripwire limit, not authentication. When unset,
                  defaults to `<project-root>/.claude/secrets/stamp_secret.hex` if a deployment.json is
                  located (below); with neither, no secret resolves and the hook passes writes through
                  unstamped (fail-open, per SAFETY).

DEPLOYMENT-RECORD CONSUMPTION (design/OPUS-READINESS.md move 1, BACKLOG "E13 retirement", 2026-07-09):
this hook is a fresh short-lived process per tool call and receives no persistent config of its own --
its only per-call context is the hook-input JSON on stdin, which Claude Code populates with `cwd` (the
session's working directory when the tool call fired; the same field `hooks/stamp_provenance.py`
already reads). That makes `cwd` the natural, zero-extra-plumbing way to locate a project's
`deployment.json` (repo root, next to `.claude/`) -- cleaner than a NEW env var a project's
settings.json would otherwise have to carry, since Claude Code hands `cwd` over for free on every
invocation. Resolution order: an explicit `LEDGER_DEPLOYMENT=/path/to/deployment.json` env var (an
override, same name `engine/targets.py`/`pickup` already use) wins if set; else `<cwd>/deployment.json`
if that file exists; else no deployment record (byte-held prior behavior: STAMP_DB/STAMP_SECRET env
vars, or nothing, exactly as before this pass). A missing or malformed deployment.json is never an
error here -- SAFETY (below) governs: it degrades silently to the env-var/hardcoded path, exactly like
every other mis-provisioning this hook tolerates.

SAFETY: this hook must NEVER break a tool call. Any error, any non-matching command -> allow the command
UNCHANGED (exit 0, no output). It only ever ADDS a stamp to a genuine ledger-bound psql call or led
invocation. Lazy imports banned.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shlex
import sys
import time
from pathlib import Path

# Eager, top-of-file sys.path insert + import (lazy imports banned; this is the same pattern
# engine/targets.py and bootstrap/templates/pickup.tmpl already use to reach a sibling module):
# filing/deployment_record.py is the ONE home for the deployment.json shape (ADR-0012 P1), and this
# hook lives inside the SAME autoharn checkout as filing/, so no cross-repo path guessing is needed.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)  # hooks/ -> autoharn root
sys.path.insert(0, os.path.join(_REPO_ROOT, "filing"))
import deployment_record  # noqa: E402  (filing/deployment_record.py, the ONE home for the deployment.json shape)


def _passthrough() -> int:
    """Allow the command unchanged (defer). A hook that emits nothing and exits 0 is a no-op."""
    return 0


def _find_deployment_path(data: dict) -> str | None:
    """Locate this project's deployment.json: an explicit LEDGER_DEPLOYMENT override first, else
    `<cwd>/deployment.json` using the hook input's own `cwd` field (falling back to this process's
    os.getcwd(), mirroring stamp_provenance.py's identical convention). Returns None -- never raises
    -- when neither resolves to an existing file (SAFETY: a missing record degrades quietly)."""
    explicit = os.environ.get("LEDGER_DEPLOYMENT", "")
    if explicit:
        return explicit
    cwd = data.get("cwd") or os.getcwd()
    candidate = os.path.join(cwd, "deployment.json")
    return candidate if os.path.isfile(candidate) else None


def _load_deployment_quiet(data: dict) -> deployment_record.DeploymentRecord | None:
    """Best-effort deployment.json load for this invocation. Never raises -- a missing/malformed
    record degrades to the env-var/hardcoded path, exactly like any other mis-provisioning here."""
    path = _find_deployment_path(data)
    if not path:
        return None
    try:
        return deployment_record.load_deployment(path)
    except deployment_record.DeploymentError:
        return None


def _secret(dep: deployment_record.DeploymentRecord | None, dep_path: str | None) -> bytes | None:
    path = os.environ.get("STAMP_SECRET", "")
    if not path and dep_path:
        # Derive the project-convention default from the deployment record's own directory (the
        # project root, next to .claude/) -- see bootstrap/new-project.sh / toy-project's own layout.
        path = os.path.join(os.path.dirname(dep_path), ".claude", "secrets", "stamp_secret.hex")
    if not path or not Path(path).is_file():
        return None
    try:
        return bytes.fromhex(Path(path).read_text().strip())
    except (ValueError, OSError):
        # OSError: an existing-but-unreadable secret file (perms, I/O). FAIL OPEN like every other
        # mis-provisioning: the hook must never break a tool call (rider 1, Inc-14 hook ruling) — the
        # trigger fail-closes on the DB side instead (an unprovisioned/unreadable secret -> unstamped
        # write -> stamp_verified=false; a required stamp then refuses THERE, never here).
        return None


def _is_ledger_psql(command: str, db: str) -> bool:
    """True iff the command runs psql against the ledger db (a `-d <db>` or `psql <db>` token). Kept
    conservative: only a real psql invocation naming the ledger db is stamped; a non-psql write (a
    python/psycopg script) is deliberately NOT matched — it is the pre-registered script-evasion tripwire
    (unstamped -> refused where a stamp is required, a disposition finding, never a harness fault)."""
    if "psql" not in command or not db:
        return False
    return bool(re.search(rf"(?:-d\s+|--dbname[=\s]+|\bpsql\s+){re.escape(db)}\b", command))


# Leading `VAR=value` env-var assignments (any number, e.g. `LED_ACTOR=reviewer ./led review ...`),
# stripped once before reading the command's first real word.
_ENV_ASSIGN_RE = re.compile(r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*")


def _is_led_invocation(command: str) -> bool:
    """True iff the command's first word -- after stripping any leading `VAR=value` prefixes -- is
    `./led`, bare `led`, or any absolute/relative path ending `/led`. This is the fix for the
    script-evasion class BACKLOG's "Correction to finding 3" names: `led` hides a real psql call
    inside its own script body, invisible to `_is_ledger_psql`'s literal-`psql`-in-the-command-text
    match. Deliberately narrow (matches the task's own conservative-spirit instruction): only the
    executable word itself is checked, not any occurrence of "led" anywhere in the command -- a
    command that merely mentions led as data (`echo led is a word`) does not match, and a command
    that reaches led via `cd x && ./led ...` (led is not the FIRST word) does not match either. Both
    non-matches are safe (unstamped, never blocked) per this file's fail-open SAFETY contract."""
    rest = _ENV_ASSIGN_RE.sub("", command, count=1)
    m = re.match(r"\S+", rest)
    if not m:
        return False
    token = m.group(0)
    return token == "led" or token == "./led" or token.endswith("/led")


def main() -> int:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:  # noqa: BLE001 — never break a tool call
        return _passthrough()
    if data.get("tool_name") != "Bash":
        return _passthrough()
    command = str((data.get("tool_input") or {}).get("command", ""))

    dep_path = _find_deployment_path(data)
    dep = _load_deployment_quiet(data) if dep_path else None

    db = os.environ.get("LEDGER_DB") or os.environ.get("STAMP_DB") or (dep.db if dep else "")
    matched = _is_ledger_psql(command, db) or _is_led_invocation(command)
    if not matched:
        return _passthrough()
    secret = _secret(dep, dep_path)
    if secret is None:
        return _passthrough()  # unprovisioned: the trigger fail-closes; do not block here
    session = str(data.get("session_id", "unknown"))
    agent = str(data.get("agent_id") or "main")   # ABSENT in main thread (shakedown); a subagent's UUID otherwise
    ts = int(time.time())
    mac = hmac.new(secret, f"{session}|{agent}|{ts}".encode(), hashlib.sha256).hexdigest()
    pgopts = (f"-c app.vendor_session={session} -c app.vendor_agent={agent} "
              f"-c app.vendor_ts={ts} -c app.vendor_hmac={mac}")
    # EXPORT (not a one-command prefix): a Bash command may chain several psql calls; a bare
    # `PGOPTIONS=.. cmd1; cmd2` would stamp only cmd1. export makes every psql in the command inherit it
    # -- including, unchanged, a psql invocation hidden inside a `led` script's own body (the fix above).
    new_command = f"export PGOPTIONS={shlex.quote(pgopts)}; {command}"
    out = {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "updatedInput": {**(data.get("tool_input") or {}), "command": new_command},
    }}
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
