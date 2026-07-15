#!/usr/bin/env python3
"""hooks/pretooluse_sql_block.py -- model-conditional raw-SQL refusal (work item
model-conditional-sql-block, ledger row opened 2026-07-14; maintainer near-verbatim: "it would
be helpful ... if our harness can conditionally block raw sql depending on which model does
it"). A PreToolUse hook on Bash: enforces the standing delegation policy (memory
delegation-policy-sonnet-first, 2026-07-14 -- "Sonnet for everything; Fable never writes SQL";
Opus permanently off limits for a quota-burn incident the same date) AT THE TOOL BOUNDARY,
instead of leaving it to executor discipline alone.

EMPIRICAL FINDING THIS HOOK IS BUILT ON (load-bearing -- read before touching the matching
logic below): a PreToolUse hook firing on the Bash tool carries NO model-identity field at all.
A live-captured PreToolUse payload for Bash (seen-red/hook-payload-contract/
captured_pretooluse_bash.json, this deployment's own fixture) carries exactly: cwd, effort,
hook_event_name, permission_mode, prompt_id, session_id, tool_input, tool_name, tool_use_id,
transcript_path -- no `model`. The environment a hook subprocess inherits carries no model
identity either (checked live: CLAUDE_EFFORT is exported, no CLAUDE_MODEL/ANTHROPIC_MODEL or
equivalent is). hooks/pretooluse_delegation_observer.py's own `model` field is the ONE place a
model name appears anywhere in this project's hook-visible surface, and it is DECLARED-BY-
DISPATCHER (verbatim from a Task/Agent tool_input a caller populated), not witnessed by the
harness, and it is only present on a SUBAGENT dispatch, not on the driving/main session's own
identity -- of no help here, since the raw-SQL Bash calls this hook must gate are typically
issued directly by the main session, which carries no `tool_input.model` at all.

So a guessed model is not on the table (this hook does not invent one from prompt_id/session_id
heuristics -- ADR-0011 Rule 4 territory, and a wrong guess here is either a false deny of a
legitimate Sonnet session or a false pass of a Fable/Opus session, both worse than admitting the
signal does not exist). The honest v1: the session's own model is DECLARED in apparatus.json at
scaffold/arm time by the session's owner (`mechanisms.sql_block.session_model`), the same
"config declares what the harness cannot witness" shape `pretooluse_delegation_observer.py`
already uses for `subagent_type`. Missing/absent declares as `"unknown"`, which the shipped
default policy maps to `"observe"` (never a silent block, never a silent allow) -- see POLICY
below.

MATCHING -- STRONG vs WEAK, false-positive-averse (module design constraint, verbatim: "when
unsure, in enforce mode prefer WARN-and-allow over block for commands that merely mention
SQL-ish words outside psql context; the refusal must never make the harness unusable"):
  STRONG  -- the command carries a `psql` invocation (word-boundary token, not merely the
             substring) AND an SQL keyword (SELECT/INSERT/UPDATE/DELETE/CREATE/ALTER/DROP/
             GRANT/REVOKE/TRUNCATE/COPY/MERGE/WITH, case-insensitive, word-boundary) AND a
             concrete SQL-carrying shape on that invocation: a `-c`/`--command` or `-f`/`--file`
             flag, a heredoc (`<<`) feeding stdin, or a pipe (`|`) feeding stdin into `psql`.
             This is the shape the commission names as the actual target: "psql with -c/-f
             whose payload contains SQL keywords ... heredocs piped into psql".
  WEAK    -- an SQL keyword appears in the command text WITHOUT the strong shape above (no
             `psql` token at all, or a `psql` token present but with none of -c/-f/heredoc/pipe
             feeding it -- e.g. `psql -l`, or a comment/echo that merely mentions "SELECT").
             This is the "merely mentions SQL-ish words" case the false-positive posture names.
  NEITHER -- no SQL keyword at all: not this hook's business, full stop, zero cost past the
             regex scan.

SANCTIONED WRAPPERS NEVER MATCH (module design constraint, verbatim: "the point is to force the
grammar and delegation, not to break the verbs"). Before any SQL scan, every top-level command
segment (split on `;`, `&&`, `||`, `|`, after stripping a leading `cd <dir> &&`/`cd <dir>;`
prefix and leading env-var assignments) is checked against the sanctioned-verb allowlist
(`./led`, `./pickup`, `./judge`, `./distance-to-clean`, `./attest-tags`, `./audit`, or a
`bootstrap/*.sh` path). If EVERY segment is a sanctioned-verb call, the WHOLE command is
inert to this hook -- no scan, no journal, no warning -- even though `./led` itself shells out
to `psql` internally carrying real SQL: this is a discipline/delegation nudge, not a
cryptographic security boundary (that job belongs to hooks/stamp_intercept.py's HMAC layer,
which still stamps and lands every write regardless of what this hook does). NAMED, DISCLOSED
GAP: this is a plain per-segment token check, not a shell parser -- a command that hides a raw
psql call inside a generated script or an unusual quoting shape can, in principle, evade the
allowlist check in the OTHER direction too (fail to recognize a sanctioned verb, or fail to
recognize a real SQL call it wraps) exactly as hooks/stamp_intercept.py's own module docstring
disclosed for its now-deleted matcher. Given this hook's own false-positive-averse mandate
(WARN over block when unsure), that asymmetry is accepted here, unlike stamp_intercept's own
security boundary.

POLICY (apparatus.json `mechanisms.sql_block`): `mode` is the standing off/observe/enforce
switchboard (maintainer mandate 2026-07-10) -- `"off"` (default of the SHIPPED config) exits
before any command inspection at all, genuinely zero cost; `"observe"` scans, journals, and
WARNS on anything that would have been denied under `"enforce"`, but never blocks;
`"enforce"` scans, journals, and actually DENIES a STRONG match whose `session_model` maps to
policy `"deny"`. `policy` is a dict of glob patterns (fnmatch, e.g. `"fable*"`, `"opus*"`) to
one of `"deny"` / `"allow"` / `"observe"`, checked in the dict's own iteration order (first
match wins); an unmatched model falls through to `policy["*"]` if present, else
`unknown_model_mode` (default `"observe"`). `"observe"` as a PER-MODEL disposition (as opposed
to the mechanism's own mode) NEVER blocks regardless of mechanism mode -- it means "this model
identity is not confidently classified, so warn, never deny" (the unknown-model case the
commission calls for). A WEAK match is NEVER denied regardless of policy disposition or
mechanism mode -- it only ever warns (false-positive posture, module docstring above) when the
resolved disposition is `"deny"`.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below is imported at module load.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import shlex
import sys
import time
from pathlib import Path
from typing import Any, Optional

_VALID_MODES = ("off", "observe", "enforce")
_VALID_DISPOSITIONS = ("deny", "allow", "observe")

# Sanctioned verbs (module docstring, SANCTIONED WRAPPERS NEVER MATCH). Matched against a
# segment's OWN first token after stripping a leading `cd ... &&`/`cd ...;` prefix and leading
# `NAME=value` env assignments -- see `_strip_prefix` / `_segment_is_sanctioned` below.
_SANCTIONED_VERB_RE = re.compile(
    r"^(?:\./(?:led|pickup|judge|distance-to-clean|attest-tags|audit)\b"
    r"|(?:\./)?bootstrap/[^\s]+\.sh\b)"
)

_SQL_KEYWORD_RE = re.compile(
    r"\b(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|GRANT|REVOKE|TRUNCATE|COPY|MERGE|WITH)\b",
    re.IGNORECASE,
)
_PSQL_TOKEN_RE = re.compile(r"(?:^|[\s;&|(])psql\b")
_DASH_C_OR_F_RE = re.compile(r"(?:^|\s)--?(?:c|command|f|file)\b")
_HEREDOC_RE = re.compile(r"<<-?\s*['\"]?\w+")
_PIPE_INTO_PSQL_RE = re.compile(r"\|\s*psql\b")

_ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=\S*\s+")
_CD_PREFIX_RE = re.compile(r"^cd\s+\S+\s*(?:&&|;)\s*")


def _first(d: Any, *keys: str, default: Any = None) -> Any:
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return default


# ---------------------------------------------------------------------------------------
# SANCTIONED WRAPPERS NEVER MATCH
# ---------------------------------------------------------------------------------------

def _strip_leading_noise(segment: str) -> str:
    s = segment.strip()
    # a `cd <dir> &&`/`cd <dir>;` prefix, then any number of leading env-var assignments
    s = _CD_PREFIX_RE.sub("", s).strip()
    while True:
        m = _ENV_ASSIGN_RE.match(s)
        if not m:
            break
        s = s[m.end():].strip()
    return s


def _split_segments(command: str) -> list[str]:
    # top-level split on ; && || | -- deliberately crude (module docstring's named, disclosed
    # gap): good enough to recognize the common "./led ...", "./pickup ...", chained-verb shapes
    # without attempting a real shell parse.
    return [seg for seg in re.split(r"&&|\|\||;|\|", command) if seg.strip()]


def _command_is_sanctioned(command: str) -> bool:
    segments = _split_segments(command)
    if not segments:
        return False
    return all(_SANCTIONED_VERB_RE.match(_strip_leading_noise(seg)) for seg in segments)


# ---------------------------------------------------------------------------------------
# MATCHING -- STRONG vs WEAK vs NEITHER
# ---------------------------------------------------------------------------------------

def classify_command(command: str) -> str:
    """Returns "strong", "weak", or "none" -- module docstring MATCHING section."""
    if not _SQL_KEYWORD_RE.search(command):
        return "none"
    has_psql = bool(_PSQL_TOKEN_RE.search(command))
    sql_carrying_shape = bool(
        _DASH_C_OR_F_RE.search(command) or _HEREDOC_RE.search(command)
        or _PIPE_INTO_PSQL_RE.search(command)
    )
    if has_psql and sql_carrying_shape:
        return "strong"
    return "weak"


# ---------------------------------------------------------------------------------------
# APPARATUS.JSON SWITCHBOARD (maintainer mandate 2026-07-10, mirrors every sibling hook)
# ---------------------------------------------------------------------------------------

def _apparatus_root(payload: dict) -> Optional[str]:
    env_root = os.environ.get("GATE_SUBJECT_ROOT")
    if env_root:
        return env_root
    cwd = _first(payload, "cwd", default="")
    return cwd if cwd and isinstance(cwd, str) else None


def _load_apparatus_quiet(root: Optional[str]) -> dict:
    if not root:
        return {}
    path = os.path.join(root, ".claude", "apparatus.json")
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg if isinstance(cfg, dict) else {}
    except Exception:
        return {}


def _mechanism_entry(apparatus: dict) -> dict:
    mechs = apparatus.get("mechanisms")
    entry = mechs.get("sql_block") if isinstance(mechs, dict) else None
    return entry if isinstance(entry, dict) else {}


def _resolve_mode(entry: dict, root: Optional[str]) -> str:
    default = "off"
    raw = entry.get("mode")
    if raw is None:
        return default
    if raw in _VALID_MODES:
        return raw
    print(f"[apparatus] WARNING: mechanisms.sql_block.mode={raw!r} in "
          f"{root}/.claude/apparatus.json is unrecognized (must be one of {_VALID_MODES}) -- "
          f"never widening permissions; falling back to {default!r}.", file=sys.stderr)
    return default


_DEFAULT_POLICY = {
    "fable*": "deny",
    "opus*": "deny",
    "sonnet*": "allow",
    "haiku*": "allow",
}


def _resolve_policy(entry: dict) -> dict:
    raw = entry.get("policy")
    if isinstance(raw, dict) and raw:
        return raw
    return dict(_DEFAULT_POLICY)


def _resolve_unknown_mode(entry: dict) -> str:
    raw = entry.get("unknown_model_mode")
    return raw if raw in _VALID_DISPOSITIONS else "observe"


def _resolve_session_model(entry: dict) -> str:
    raw = entry.get("session_model")
    return raw if isinstance(raw, str) and raw else "unknown"


def _disposition_for_model(model: str, policy: dict, unknown_mode: str) -> str:
    for pattern, disposition in policy.items():
        if pattern == "*":
            continue
        if fnmatch.fnmatch(model, pattern) and disposition in _VALID_DISPOSITIONS:
            return disposition
    if "*" in policy and policy["*"] in _VALID_DISPOSITIONS:
        return policy["*"]
    return unknown_mode


# ---------------------------------------------------------------------------------------
# JOURNAL
# ---------------------------------------------------------------------------------------

def _journal_path(payload: dict) -> Optional[Path]:
    cwd = _first(payload, "cwd", default="")
    if not cwd or not isinstance(cwd, str):
        return None
    return Path(cwd) / ".claude" / "logs" / "sql_block.journal.jsonl"


def _journal(payload: dict, record: dict) -> None:
    path = _journal_path(payload)
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def _base_record(payload: dict, command: str, strength: str, model: str,
                  mode: str, disposition: str, outcome: str) -> dict:
    tool_use_id = payload.get("tool_use_id")
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z",
        "session_id": str(payload.get("session_id") or ""),
        "mode": mode,
        "session_model": model,
        "disposition": disposition,
        "strength": strength,
        "outcome": outcome,
        "command_sha256": hashlib.sha256(command.encode("utf-8", "surrogatepass")).hexdigest(),
        "command_head": command[:200],
    }
    if tool_use_id:
        rec["tool_use_id"] = str(tool_use_id)
    return rec


# ---------------------------------------------------------------------------------------
# TEACH-TEXT
# ---------------------------------------------------------------------------------------

def _teach_text(model: str, command_head: str) -> str:
    return (
        "[sql-block] the standing delegation policy (memory delegation-policy-sonnet-first, "
        "2026-07-14: \"Sonnet for everything; Fable never writes SQL\"; Opus permanently off "
        "limits) refuses raw SQL-bearing Bash commands from this session's declared model "
        f"({model!r}, apparatus.json mechanisms.sql_block.session_model).\n"
        f"command: {command_head}\n"
        "Two sanctioned routes instead of a raw psql call:\n"
        "  1. Delegate the SQL-touching work to a Sonnet subagent (Task/Agent tool, "
        "model='sonnet') -- Sonnet executes SQL, Fable/Opus author/orchestrate only.\n"
        "  2. Use the repo-root verb grammar instead of hand-typed psql -- ./led, ./pickup, "
        "./judge, ./distance-to-clean, ./attest-tags, ./audit (and bootstrap/*.sh) are never "
        "matched by this refusal.\n"
        "Governing config key: .claude/apparatus.json -> mechanisms.sql_block "
        "(mode / policy / session_model)."
    )


def _deny(payload: dict, command: str, model: str, mode: str, disposition: str) -> int:
    msg = _teach_text(model, command[:200])
    _journal(payload, _base_record(payload, command, "strong", model, mode, disposition, "denied"))
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": msg}}))
    print(msg, file=sys.stderr)
    return 2


def _warn(payload: dict, command: str, model: str, mode: str, disposition: str,
          strength: str, would_deny: bool) -> int:
    lead = ("[sql-block] WARNING (observer-mode, non-blocking): this command WOULD BE DENIED "
            "under mechanisms.sql_block.mode='enforce'.\n") if (mode == "observe" and would_deny) \
        else ("[sql-block] WARNING: this command merely mentions SQL-ish keywords without a "
              "clear psql -c/-f/heredoc/pipe shape -- never blocked on that basis alone "
              "(false-positive posture).\n") if strength == "weak" \
        else ("[sql-block] WARNING: this session's declared model is not confidently "
              "classified by mechanisms.sql_block.policy -- never blocked on an unknown model, "
              "review advised.\n")
    warning = lead + _teach_text(model, command[:200])
    outcome = "observed_would_deny" if (mode == "observe" and would_deny and strength == "strong") \
        else ("weak_match_warned" if strength == "weak" else "unknown_model_warned")
    _journal(payload, _base_record(payload, command, strength, model, mode, disposition, outcome))
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "allow",
        "additionalContext": warning}}))
    return 0


def _allow_quiet(payload: dict, command: str, model: str, mode: str, disposition: str,
                  strength: str) -> int:
    _journal(payload, _base_record(payload, command, strength, model, mode, disposition, "allowed"))
    return 0


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # unparseable stdin -- nothing this hook can act on
    if not isinstance(payload, dict):
        return 0

    if _first(payload, "tool_name", "toolName", "name", default="") != "Bash":
        return 0

    root = _apparatus_root(payload)
    apparatus = _load_apparatus_quiet(root)
    entry = _mechanism_entry(apparatus)
    mode = _resolve_mode(entry, root)
    if mode == "off":
        return 0  # genuinely zero cost -- no command inspection at all

    tool_input = _first(payload, "tool_input", "toolInput", "input", default={})
    if not isinstance(tool_input, dict):
        return 0
    command = str(tool_input.get("command", ""))
    if not command:
        return 0

    # SANCTIONED WRAPPERS NEVER MATCH (module docstring): fully inert, no journal, no warning.
    if _command_is_sanctioned(command):
        return 0

    strength = classify_command(command)
    if strength == "none":
        return 0

    policy = _resolve_policy(entry)
    unknown_mode = _resolve_unknown_mode(entry)
    model = _resolve_session_model(entry)
    disposition = _disposition_for_model(model, policy, unknown_mode)

    # A WEAK match never blocks, regardless of policy/mode (false-positive posture) -- it only
    # warns when the resolved disposition is "deny" (otherwise it is inert noise not worth a
    # warning at all: an allow-model mentioning SQL words in passing is not this hook's business).
    if strength == "weak":
        if disposition == "deny":
            return _warn(payload, command, model, mode, disposition, strength, would_deny=False)
        return 0

    # strength == "strong" from here down.
    if disposition == "allow":
        return _allow_quiet(payload, command, model, mode, disposition, strength)

    if disposition == "observe":
        # unknown/not-confidently-classified model -- never blocks regardless of mechanism mode.
        return _warn(payload, command, model, mode, disposition, strength, would_deny=False)

    # disposition == "deny" from here down.
    if mode == "enforce":
        return _deny(payload, command, model, mode, disposition)
    # mode == "observe": would-deny, surfaced as a loud warning, never a block.
    return _warn(payload, command, model, mode, disposition, strength, would_deny=True)


if __name__ == "__main__":
    sys.exit(main())
