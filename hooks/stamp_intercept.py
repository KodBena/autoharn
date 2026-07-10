#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T12:38:35Z
#   last-change: 2026-07-10T23:34:40Z
#   contributors: be693afb/main, e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""stamp_intercept — the WRITE-TIME interception hook (BACKLOG ffafa59). A PreToolUse hook on Bash:
when this hook is WIRED (a deployment record is located, OR STAMP_SECRET is explicitly set — see
SAFETY below) it computes the interception stamp HMAC(secret, session_id||agent_id||ts) and REWRITES
EVERY Bash command, unconditionally, to carry it into any psql connection the command may make as
`app.vendor_*` GUCs (via PGOPTIONS) — see MATCHERLESS STAMPING below for why there is no longer a
command-shape test gating this. The kernel's set_stamp trigger then validates the stamp against the
apparatus secret it recomputes SECURITY-DEFINER-side. The hook STAMPS; the trigger LANDS it; the model
neither types the stamp (it has no secret) nor omits it (the hook stamps every Bash call in a wired
world). A self-review by one invocation carries the SAME agent id as its authoring — visible; a
genuinely distinct subagent carries a different one (its `agent_id`, confirmed present in hook context
by the lab shakedown).

MATCHERLESS STAMPING (BACKLOG "Run-5 forensics", 2026-07-10): the matcher is DELETED. Three separate
runs found three distinct ways to evade an enumerated command-shape match — a raw psql call (run 1),
`./led`'s own psql call hidden inside its script body (run 2, "Correction to finding 3"), and run 5's
`cd run5 && ./led …` (led is not the first word) plus `cat > run_reviews.sh …; bash run_reviews.sh` (a
GENERATED script, no `led`/`psql` token in the triggering command at all). Any enumeration is a finite
list chasing an infinite command-shape space (ADR-0011 Rule 4: enumeration fails open) — three strikes
is the disclosed pattern, not a coincidence. The fix removes the target: when this hook is WIRED (see
SAFETY below), the stamp is injected into EVERY Bash command, unconditionally, with no shape test at
all. A command that never touches psql simply carries an inert PGOPTIONS export it never reads; a
command that hides psql inside a generated script, a wrapper, or a `cd`-prefixed chain still inherits
the export (see "export, not a prefix" below) because the export happens before ANY of the subject's
own command text runs, not conditional on recognizing it.

CONFIG (provisioned at arm; the subject never sees this file's prose, only the injected GUCs):
  STAMP_SECRET  — path to a chmod-600 file holding the apparatus secret as hex (the hook's read of the
                  one secret; the trigger reads the same value from kernel.stamp_secret). Same OS user =
                  hunt-able secret — the pre-registered tripwire limit, not authentication. When unset,
                  defaults to `<project-root>/.claude/secrets/stamp_secret.hex` if a deployment.json is
                  located (below); with neither, no secret resolves and the hook passes writes through
                  unstamped (fail-open, per SAFETY).

DEPLOYMENT-RECORD PRESENCE (design/OPUS-READINESS.md move 1, BACKLOG "E13 retirement", 2026-07-09):
this hook is a fresh short-lived process per tool call and receives no persistent config of its own --
its only per-call context is the hook-input JSON on stdin, which Claude Code populates with `cwd` (the
session's working directory when the tool call fired; the same field `hooks/stamp_provenance.py`
already reads). That makes `cwd` the natural, zero-extra-plumbing way to locate a project's
`deployment.json` (repo root, next to `.claude/`) -- cleaner than a NEW env var a project's
settings.json would otherwise have to carry, since Claude Code hands `cwd` over for free on every
invocation. Resolution order: an explicit `LEDGER_DEPLOYMENT=/path/to/deployment.json` env var (an
override, same name `engine/targets.py`/`pickup` already use) wins if set; else `<cwd>/deployment.json`
if that file exists; else no deployment record (byte-held prior behavior: STAMP_SECRET env var, or
nothing, exactly as before this pass). This hook only ever checks the file's PRESENCE (`os.path.isfile`)
to derive the project-convention secret-file default below -- it never parses the record's fields (the
matcher that once needed `deployment.json`'s `db` field is gone; `filing/deployment_record.py`'s shape
is consumed by hooks/pretooluse_change_gate.py instead, which still needs host/db/schema). A missing or
malformed deployment.json is never an error here -- SAFETY (below) governs: it degrades silently to the
env-var/hardcoded path, exactly like every other mis-provisioning this hook tolerates.

SAFETY: this hook must NEVER break a tool call for an UNWIRED session -- no deployment.json located AND
no STAMP_SECRET env var set is exactly today's autoharn-dev-flow shape, zero interference, byte-held.
For a WIRED session (a deployment record found, or STAMP_SECRET explicitly set) every Bash command is
now rewritten unconditionally (MATCHERLESS STAMPING above); the one exception remains the dangling-
secret case immediately below. Lazy imports banned.

APPARATUS.JSON SWITCHBOARD (maintainer mandate, 2026-07-10): this mechanism's own mode lives at
`<root>/.claude/apparatus.json`'s `mechanisms.stamp_intercept.mode` (`root` = an explicit
GATE_SUBJECT_ROOT env var, else the located deployment.json's own directory, else no apparatus.json
to read -- see `_apparatus_root()`), resolved once per invocation. Three modes, WITH A NAMED NUANCE
for this hook specifically (injection is free and harmless, unlike a deny): `"off"` -- no injection
at all, the command passes through completely untouched, exactly as an unwired session already does;
`"observe"` -- STILL INJECTS the stamp on a healthy secret (identical to `"enforce"` -- there is no
reason to withhold a free, harmless write-time stamp just because the world is in a lighter assurance
posture), but the one thing this mode never does is DENY: the explicit-but-broken-secret case that
`"enforce"` refuses outright instead passes the command through UNSTAMPED with a loud
`additionalContext` warning plus a journal record; `"enforce"` -- byte-identical to this file's
behavior before this pass, including the dangling-secret deny. Missing file/key resolves to
`"enforce"` (rule c: stamping costs nothing per invocation, so it defaults to its current strength).
An unrecognized mode string never widens permissions (rule d) -- falls back to `"enforce"`, already
the strictest state this mechanism has, with a loud stderr warning naming the bad value.

PER-INVOCATION CONTEMPORANEITY TOKEN (design/CONTEMPORANEITY-AUDIT.md Part 1; BACKLOG "Contemporaneity
indictment", 2026-07-11): on the SAME injection path that carries the HMAC stamp (a wired world, a
healthy secret, mode observe/enforce), this hook additionally mints a per-Bash-invocation UUID and
exports it as a SIXTH GUC `app.vendor_invocation` alongside the four HMAC GUCs. The kernel's set_stamp
trigger (s23 delta) captures it into a nullable `stamp_invocation` ledger column, one register below
stamp_session -- CAPTURE-ONLY, never part of the HMAC or any refusal. It is ALSO journaled, one JSON
line per injection, to `<cwd>/.claude/logs/invocations.jsonl`: {token, wall-clock ISO-8601 UTC at
injection, session_id, tool_use_id iff the hook payload carries one, sha256 of the command text, first
120 chars of the command}. The journal is the "actual event" side; the ledger column is the "recorded
event" side; a later `audit` verb (Part 2, NOT here) joins them to make honest simultaneity and
retroactive backfill stop being the same row shape. The token is minted ONLY where a stamp is actually
injected (a token no ledger row can carry would be a dangling journal line) -- so an "off"-mode, an
unwired, or a dangling-secret (unstamped) invocation mints NO token and writes NO invocation journal
line. Journaling is BEST-EFFORT and degrades SILENTLY (a full disk loses the journal line while the
row still stamps): the token export must never depend on the journal write, and neither may ever break
a tool call. The token is UNAUTHENTICATED (no HMAC over it) -- a same-OS-user subject can self-SET
app.vendor_invocation; a correlation tripwire, not authentication, matching s17's standing framing.

FAIL-CLOSED ON A DANGLING STAMP_SECRET (BACKLOG "Run-2 integrity finding", 2026-07-09; SEVERITY RAISED
BACKLOG "Run-5 forensics", 2026-07-10 — NAMED CHOICE): the one exception to "wired -> stamp every
command" above is an EXPLICITLY-configured STAMP_SECRET (the env var itself, not a not-yet-armed
deployment.json-derived default) whose file is missing, unreadable, or empty -- twice witnessed (runs 1
and 2) silently passing a matched ledger write through UNSTAMPED. That specific, identified case DENIES
the command instead, with teach-text naming the configured path and the seed step. Before the
matcherless pass this only fired for a command the (now-deleted) matcher recognized; with the matcher
gone, EVERY Bash command in that world now hits this same deny — a world with a broken stamp secret
refuses ALL shell commands loudly rather than letting any of them run unstamped. This is a deliberate
severity escalation, not an accident: the one path this fix denies more broadly than before is
precisely the one already-identified misconfiguration (an operator explicitly pointed STAMP_SECRET
somewhere broken), never an ordinary unconfigured or not-yet-armed project (both of those stay fail-
open below, byte-held). An unset STAMP_SECRET or a healthy secret file are unaffected.
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
import uuid
from pathlib import Path


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


def _resolve_secret_path(dep_path: str | None) -> tuple[str, bool]:
    """Resolve the secret-file path for this invocation, and whether it was EXPLICITLY configured
    via the STAMP_SECRET env var -- as opposed to a deployment.json-derived default that simply has
    not been armed yet (bootstrap/templates/HOOKS.md.tmpl's own "one manual step remains" state,
    which is normal and must stay fail-open, not the run-2 misconfiguration this fix targets).
    Returns (path, explicit); path is "" when neither an env var nor a deployment record resolves."""
    explicit_path = os.environ.get("STAMP_SECRET", "")
    if explicit_path:
        return explicit_path, True
    if dep_path:
        # Derive the project-convention default from the deployment record's own directory (the
        # project root, next to .claude/) -- see bootstrap/new-project.sh / toy-project's own layout.
        return os.path.join(os.path.dirname(dep_path), ".claude", "secrets", "stamp_secret.hex"), False
    return "", False


def _load_secret(path: str) -> bytes | None:
    """Best-effort secret load: None for ANY invalid condition -- missing, unreadable, empty, or
    non-hex content -- never raises. An empty-but-present file is treated the SAME as missing (never
    silently accepted as a valid zero-length HMAC key, which would otherwise produce a wrong-but-
    present stamp instead of an honest unstamped write). Whether a None here is fail-open
    (unconfigured / not-yet-armed) or fail-closed (explicitly configured but broken) is the CALLER's
    decision (main(), via `_resolve_secret_path`'s `explicit` flag) -- this loader only reports what
    the file contains."""
    if not path or not Path(path).is_file():
        return None
    try:
        text = Path(path).read_text().strip()
        if not text:
            return None
        return bytes.fromhex(text)
    except (ValueError, OSError):
        # OSError: an existing-but-unreadable secret file (perms, I/O). ValueError: malformed hex.
        return None


# Matches a PGOPTIONS=... token ONLY when its full extent can be determined UNAMBIGUOUSLY from the
# text alone -- SAFETY (this file's prime invariant, "never break a tool call") outranks "our
# injection must win" below: under-stripping only means our export might not win for that one
# exotic shape (a residual, named gap); over-stripping into a partial token would leave BROKEN
# shell syntax behind, an actual break. Three defenses against a wrong/partial match:
#   1. The bare (unquoted) branch stops at any shell metacharacter (;&|()<>), not just whitespace --
#      `\S*` alone would eat straight through `PGOPTIONS=x;echo hi` into "x;echo" (verified: this
#      shipped once and mangled an ordinary, non-adversarial `;`-chained command; fixed here).
#   2. A negative lookahead bails out of the bare branch entirely on `$(` or a backtick -- command
#      substitution needs balanced-paren matching a linear regex cannot do safely, so rather than
#      match a truncated prefix (`PGOPTIONS=$(cat /tmp/x)` -> matching only "PGOPTIONS=$" leaves
#      "(cat /tmp/x)" as a dangling, syntax-broken fragment), THIS hook does not touch it at all.
#   3. A trailing lookahead requires whatever follows the matched token to be whitespace, a shell
#      metacharacter, or end-of-string -- so `PGOPTIONS='foo'\''bar'` (bash's own idiom for
#      embedding a literal quote, three tokens glued with no separator) does not match past the
#      first `'foo'` span and leave `\''bar'` dangling; the WHOLE token is left untouched instead.
# NAMED RESIDUAL GAPS (this hook only strips a literal `PGOPTIONS=` text assignment; it is not a
# shell parser): indirect assignment forms that never contain the substring `PGOPTIONS=` at all --
# `printf -v PGOPTIONS ...`, `read -r PGOPTIONS`, `declare -n ref=PGOPTIONS` -- are NOT detected, so
# in that specific, unusual shape the subject's own later assignment can still win for that one
# psql call. Command substitution and adjacent-quote concatenation (defenses 2/3 above) are also
# left untouched rather than risk a broken command. All are accepted, disclosed limits of a
# same-OS-user tripwire, not authentication (mirrors this file's own STAMP_SECRET framing above) --
# the kernel's set_stamp trigger still fails closed on a bad/absent HMAC regardless.
_PGOPTIONS_STRIP_RE = re.compile(
    r"\bPGOPTIONS=(?:'[^']*'|\"[^\"]*\"|(?!\$\(|`)[^\s;&|()<>'\"]*)"
    r"(?=[\s;&|()<>]|$)"
)


def _neutralize_pgoptions(command: str) -> str:
    """Strip any PGOPTIONS=... assignment the SUBJECT'S OWN command text already carries, WHEN its
    extent can be determined unambiguously (see `_PGOPTIONS_STRIP_RE` above for the three defenses
    and the named residual gaps) -- an inline command-prefix (`PGOPTIONS=x psql ...`) or an explicit
    `export PGOPTIONS=x;` earlier in the chain -- so THIS hook's own export (prepended by the
    caller, after this runs) is the PGOPTIONS source for the whole command in the common cases.
    "Your injection must win": a prefix assignment on the very invocation being stamped always
    outranks an inherited export from an earlier `export` in ANY shell, so without this step a
    command that (deliberately or not) sets its own PGOPTIONS on its psql call would silently drop
    this hook's stamp for that one call. Fails safe in the other direction too: a stripped token
    becomes an empty span -- `export ;` is a harmless no-op (bash's builtin `export` with no operand
    just lists exported vars), and `PGOPTIONS= psql ...` runs psql with an empty PGOPTIONS,
    immediately superseded by this hook's own export prefix."""
    return _PGOPTIONS_STRIP_RE.sub("", command)


def _deny(msg: str) -> int:
    """Deny the command (BACKLOG "Run-2 integrity finding" fail-closed path). Emits the modern
    permissionDecision JSON plus a non-zero exit, mirroring hooks/pretooluse_change_gate.py's own
    dual convention for cross-version reliability."""
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": msg}}))
    print(msg, file=sys.stderr)
    return 2


# ---------------------------------------------------------------------------------------------
# APPARATUS.JSON MECHANISM SWITCHBOARD (module docstring, maintainer mandate 2026-07-10). Self-
# contained (no import of hooks/pretooluse_change_gate.py's near-identical helpers -- same "no
# cross-file coupling" posture hooks/stop_clean_exit.py's own docstring already states).
# ---------------------------------------------------------------------------------------------
_VALID_MODES = ("off", "observe", "enforce")


def _apparatus_root(dep_path: str | None) -> str | None:
    """Where this invocation's apparatus.json would live, if anywhere: an explicit
    GATE_SUBJECT_ROOT env var (the neutral name pretooluse_change_gate.py/stop_clean_exit.py
    already use) wins; else the located deployment.json's own directory; else None -- no project
    root to look under, so the mode reader below falls to this mechanism's own default, the same
    degrade-quietly posture every other mis-provisioning this hook tolerates."""
    env_root = os.environ.get("GATE_SUBJECT_ROOT")
    if env_root:
        return env_root
    return os.path.dirname(dep_path) if dep_path else None


def _load_apparatus_quiet(root: str | None) -> dict:
    if not root:
        return {}
    path = os.path.join(root, ".claude", "apparatus.json")
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg if isinstance(cfg, dict) else {}
    except Exception:
        return {}


def _resolve_mode(apparatus: dict, root: str | None) -> str:
    """apparatus["mechanisms"]["stamp_intercept"]["mode"], defaulted/validated per the maintainer's
    2026-07-10 switchboard mandate (rules b/d -- see module docstring's APPARATUS.JSON section)."""
    default = "enforce"
    mechs = apparatus.get("mechanisms")
    entry = mechs.get("stamp_intercept") if isinstance(mechs, dict) else None
    raw = entry.get("mode") if isinstance(entry, dict) else None
    if raw is None:
        return default
    if raw in _VALID_MODES:
        return raw
    print(f"[apparatus] WARNING: mechanisms.stamp_intercept.mode={raw!r} in "
          f"{root}/.claude/apparatus.json is unrecognized (must be one of {_VALID_MODES}) -- "
          f"never widening permissions; falling back to {default!r}.", file=sys.stderr)
    return default


def _journal_path(cwd) -> Path | None:
    """Same unwired-sessions posture as hooks/demurral_detect.py's own `_journal_path`: only write
    a journal when the hook input actually carries a `cwd` -- no cwd, no journal, never invents a
    path."""
    if not cwd or not isinstance(cwd, str):
        return None
    return Path(cwd) / ".claude" / "logs" / "stamp_intercept.journal.jsonl"


def _journal(cwd, rec: dict) -> None:
    path = _journal_path(cwd)
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def _invocation_journal_path(cwd) -> Path | None:
    """The per-invocation contemporaneity journal (design/CONTEMPORANEITY-AUDIT.md Part 1) -- a
    SEPARATE file from the stamp_intercept.journal above (that one records secret-health outcomes;
    this one is the token<->command<->wall-clock correlation Part 2's audit verb joins against the
    ledger's stamp_invocation column). Same "no cwd, no journal, never invents a path" posture as
    `_journal_path` / hooks/demurral_detect.py."""
    if not cwd or not isinstance(cwd, str):
        return None
    return Path(cwd) / ".claude" / "logs" / "invocations.jsonl"


def _journal_invocation(cwd, rec: dict) -> None:
    """Append one JSON line to invocations.jsonl. BEST-EFFORT: any failure (no cwd, unwritable dir,
    a full disk) is swallowed silently -- the token has ALREADY been exported into PGOPTIONS by the
    caller before this runs, so a lost journal line never un-stamps a row and never breaks the tool
    call. Named residue: on a full disk the row still carries stamp_invocation while its journal
    line is silently dropped, so the audit verb sees a ledger token with no matching journal entry
    (an UNJOURNALED row, distinguishable from an UNJOURNALED ERA where hooks were off entirely)."""
    path = _invocation_journal_path(cwd)
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def _observe_unstamped(data: dict, secret_path: str) -> int:
    """`"observe"` mode's version of the dangling-secret case (module docstring): never deny --
    this command genuinely cannot be stamped (no healthy secret to compute the HMAC with), so it
    passes through UNSTAMPED, but loudly flagged via `additionalContext` (mirrors
    hooks/pretooluse_change_gate.py's own `_observe_allow`) plus a journal record, instead of the
    silent unstamped pass-through an unconfigured/not-yet-armed world already gets."""
    warning = (
        f"[apparatus observe-mode WARNING] STAMP_SECRET ('{secret_path}') is missing, unreadable, "
        f"or empty -- this Bash command is passing through UNSTAMPED (would be DENIED under "
        f"stamp_intercept mode=enforce). " + _deny_secret_missing(secret_path))
    _journal(data.get("cwd"), {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z",
        "outcome": "observed_unstamped", "secret_path": secret_path})
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "allow",
        "additionalContext": warning}}))
    return 0


def _deny_secret_missing(path: str) -> str:
    """Teach-text for an explicitly-configured-but-broken STAMP_SECRET. Quotes the real seed
    sequence from bootstrap/templates/HOOKS.md.tmpl's "Stamp interceptor" section (the one this
    project's own scaffolded HOOKS.md carries, with host/db/kern/role filled in for the instance)."""
    return (
        f"Ledger policy: STAMP_SECRET is configured ('{path}') but that file is missing, unreadable, "
        "or empty -- this write would otherwise pass through UNSTAMPED (the run-1/run-2 silent-"
        "unstamped class, BACKLOG 2026-07-09 'Run-2 integrity finding'). Refusing instead of "
        "silently landing an unstamped ledger write. Fix: seed the secret once (this project's "
        "HOOKS.md, 'Stamp interceptor' section) --\n"
        "  HEX=$(openssl rand -hex 32)\n"
        "  psql -h <host> -d <db> -q -v ON_ERROR_STOP=1 \\\n"
        "    -c \"TRUNCATE <kern>.stamp_secret;\" \\\n"
        "    -c \"INSERT INTO <kern>.stamp_secret (secret) VALUES (decode('$HEX','hex'));\"\n"
        f"  psql -h <host> -d <db> -tAc \"SELECT encode(secret,'hex') FROM <kern>.stamp_secret\" "
        f"> {path}\n"
        f"  chmod 600 {path}\n"
        "Do NOT re-run this if the secret was already seeded once -- re-seeding ROTATES it and "
        "invalidates every stamp already written under the old value."
    )


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

    # APPARATUS.JSON SWITCHBOARD (module docstring, maintainer mandate 2026-07-10): resolved once,
    # before any secret work -- "off" short-circuits the whole hook, exactly like an unwired
    # session, with no secret lookup at all.
    root = _apparatus_root(dep_path)
    apparatus = _load_apparatus_quiet(root)
    mode = _resolve_mode(apparatus, root)
    if mode == "off":
        return _passthrough()

    # MATCHERLESS (BACKLOG "Run-5 forensics", 2026-07-10): no command-shape test gates this any
    # more -- see module docstring. Whether THIS command gets stamped depends only on whether the
    # hook is WIRED (a deployment record resolves, or STAMP_SECRET is explicitly set) and whether
    # the resolved secret is healthy; never on what the command looks like.
    secret_path, explicit = _resolve_secret_path(dep_path)
    secret = _load_secret(secret_path)
    if secret is None:
        if explicit:
            # Run-2 integrity finding, severity raised by the matcherless pass (module docstring):
            # an OPERATOR explicitly pointed STAMP_SECRET somewhere broken -- with no matcher left
            # to narrow this, EVERY Bash command in this world now hits this deny (enforce), or the
            # observe-mode warning-and-passthrough below.
            if mode == "enforce":
                return _deny(_deny_secret_missing(secret_path))
            return _observe_unstamped(data, secret_path)
        return _passthrough()  # unconfigured (unwired), or a not-yet-armed deployment default
    session = str(data.get("session_id", "unknown"))
    agent = str(data.get("agent_id") or "main")   # ABSENT in main thread (shakedown); a subagent's UUID otherwise
    ts = int(time.time())
    mac = hmac.new(secret, f"{session}|{agent}|{ts}".encode(), hashlib.sha256).hexdigest()
    # PER-INVOCATION CONTEMPORANEITY TOKEN (design/CONTEMPORANEITY-AUDIT.md Part 1; module docstring
    # "PER-INVOCATION CONTEMPORANEITY TOKEN"). A fresh uuid4 minted per Bash call, exported as a sixth
    # GUC (app.vendor_invocation) on the SAME injection this stamp rides. It is NOT part of the HMAC --
    # it is a plain correlation token the s23 kernel column captures verification-inert. Minted ONLY
    # here, on the healthy-secret injection path, so a token is never orphaned from the ledger rows
    # that can carry it (an off/unwired/dangling invocation reaches neither this line nor the journal).
    invocation = str(uuid.uuid4())
    pgopts = (f"-c app.vendor_session={session} -c app.vendor_agent={agent} "
              f"-c app.vendor_ts={ts} -c app.vendor_hmac={mac} "
              f"-c app.vendor_invocation={invocation}")
    # BEST-EFFORT journal (the "actual event" side of the correlation) -- written BEFORE the token is
    # returned but AFTER it is fixed, so a journal failure (silent) never affects what gets exported.
    # tool_use_id is included ONLY when the payload actually carries it (the parsed stdin contract has
    # never carried one; read defensively and omit honestly when absent, rather than emit a null key).
    command_bytes = command.encode("utf-8", "surrogatepass")
    inv_rec = {
        "token": invocation,
        "wall_clock": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z",
        "session_id": session,
        "command_sha256": hashlib.sha256(command_bytes).hexdigest(),
        "command_head": command[:120],
    }
    tool_use_id = data.get("tool_use_id")
    if tool_use_id:
        inv_rec["tool_use_id"] = str(tool_use_id)
    _journal_invocation(data.get("cwd"), inv_rec)
    # EXPORT (not a one-command prefix): a Bash command may chain several psql calls; a bare
    # `PGOPTIONS=.. cmd1; cmd2` would stamp only cmd1. export makes every psql in the command
    # inherit it -- including one hidden inside a generated script or a wrapper's own body, and
    # including one reached via `cd x && ...` (the export runs before any of that). Command text
    # is neutralized FIRST of any PGOPTIONS the subject's own text unambiguously sets, so this
    # export wins in the common cases (module docstring / _neutralize_pgoptions's own docstring
    # name the disclosed, narrower-scope residual gaps -- indirect assignment, command
    # substitution, adjacent-quote concatenation -- where it does not).
    new_command = f"export PGOPTIONS={shlex.quote(pgopts)}; {_neutralize_pgoptions(command)}"
    out = {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "updatedInput": {**(data.get("tool_input") or {}), "command": new_command},
    }}
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
