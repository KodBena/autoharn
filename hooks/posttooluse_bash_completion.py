#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T21:35:25Z
#   last-change: 2026-07-14T01:07:14Z
#   contributors: e4410ef6/main, a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""hooks/posttooluse_bash_completion.py -- the Bash TOOL-COMPLETION timestamp (small-follow-ups
commission item 4; BACKLOG "Maintainer principle: the action stream is the evidentiary basis;
session internals are diagnostics", 2026-07-11, and "Follow-ups commission scope extended"
item 1: "journal a PostToolUse completion timestamp beside the existing PreToolUse stamp -- the
value is the non-null tail: builds, test suites, dispatches").

WHAT THIS ADDS: `hooks/stamp_intercept.py`'s PER-INVOCATION CONTEMPORANEITY TOKEN journals ONE
side of a Bash call -- the moment it was ABOUT to run (`invocations.jsonl`: token, wall_clock,
session_id, command_sha256, command_head). Every arithmetic reader of that journal
(`engine/contemp_edb.py`) has only ever had that one side: WHEN a command started, never how
long it took. Most Bash calls are ~0s (the maintainer's own reading, cited in the BACKLOG entry
above) -- the value this hook exists to bank is the NON-NULL TAIL: a build, a test suite, a
long-running subprocess, where start-to-finish duration is itself diagnostic signal.

WHY A SIBLING FILE, NOT A NEW LINE SHAPE IN `invocations.jsonl` ITSELF: `engine/contemp_edb.py`
(the ONE consumer of that file today) parses every line as a dispatch record with an
unconditional `rec.get("token"), rec.get("wall_clock")` read (its own `export()`, PASS 1) --
injecting a differently-shaped "completion" line into that same file would either be silently
misread as a malformed dispatch record (inflating `skipped_lines` for a line that is not
actually malformed, just a different kind) or, worse, misread as a SECOND dispatch of the same
token if the shape happened to coincide. `<world>/.claude/logs/bash_completions.jsonl` is a new,
separate, PURELY ADDITIVE file: it changes no existing consumer's read of `invocations.jsonl`
and needs no change to `contemp_edb.py` (ADR-0004's minimal-touch posture -- this is a small
follow-up, not a redesign of the contemporaneity EDB's own capability manifest).

PAIRING RULE, CORRECTED 2026-07-14 (design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md sec-4/6.1 -- an RCA
found the ORIGINAL content-hash FIFO design below was dead at birth: `stamp_intercept.py`
REWRITES every Bash command -- injecting a fresh per-call uuid4 into PGOPTIONS -- AFTER hashing
the pre-rewrite text but BEFORE the command actually runs, so this hook's own `command_sha256`
(hashed from the POST-rewrite text PostToolUse's payload carries) never equalled the dispatch
side's hash. Measured live: 0 of 2093 completions ever paired in this deployment's history. The
false premise that motivated the hash approach -- "Claude Code's hook-input contract has never
been observed to carry a `tool_use_id`" -- was itself false the day it was written: every dispatch
line `stamp_intercept.py` journals carries `tool_use_id` when the payload does (see that hook's
own journal), and the official hooks contract documents PostToolUse's `tool_use_id` as "the same
ID used in the corresponding PreToolUse event" -- i.e. the harness mints and transports this
identity for exactly this correlation purpose. See `seen-red/hook-payload-contract/` for the
captured payload-pair fixture proving both events carry it.

THE FIX: this hook no longer computes or stores any pairing verdict. It journals ONLY facts
local to this event -- `{ts, session_id, tool_use_id, duration_ms?, command_sha256, command_head}`
-- and stops reading `invocations.jsonl` entirely (cheaper AND correct: no FIFO scan, no
already-paired-token scan). `command_sha256`/`command_head` are RETAINED as event facts (of the
AS-EXECUTED, post-rewrite text this payload carried -- honestly re-documented; they are no longer
correlation keys and are never compared against the dispatch side's hash of the pre-rewrite
text). Pairing is now a READ-TIME JOIN on `tool_use_id`, performed by whoever reads both
journals (`engine/contemp_edb.py`'s E5 family; a future `tools/watchdog_liveness.py`) -- never
computed or cached here. A stored pairing verdict is a second, derivable copy of a join result
(ADR-0012 P1); removing it makes a false pairing record unwritable, not merely less likely.

When the payload carries no `tool_use_id` (a Claude Code version that omits it, or a subagent
leg not yet witnessed to carry one -- see NAMED RESIDUAL GAPS): the line is journaled WITHOUT a
`tool_use_id` key. No guessed pairing, ever -- the one behavior preserved from the old design is
its honesty about absence.

NAMED RESIDUAL GAPS (v2, stated honestly rather than left for a future reader to discover):
  - Subagent-side PostToolUse payloads carrying `tool_use_id` are UNWITNESSED (only main-thread
    sessions and one dispatch journal were checked, per the RCA's own §3 disclosure) -- the
    absent-`tool_use_id` fallback above makes this safe either way; it degrades to an unjoinable
    (but still honestly journaled) line, never a wrong join.
  - If `stamp_intercept` is off/unwired for this invocation, no dispatch line exists to join
    against at all -- this hook still journals the completion (it does not know or care whether
    a dispatch line exists), and a reader's join simply finds nothing on that side.
  - The CONCURRENT-IDENTICAL-COMMAND-TEXT residual gap the old FIFO-by-hash design carried is
    DELETED, not merely reduced: it does not exist under an identity key. Two Bash calls sharing
    byte-identical command text now carry two distinct `tool_use_id`s (the harness mints one per
    tool call, not per command text), so a read-time join can never confuse them.

APPARATUS.JSON SWITCHBOARD (mirrors the project's standing mechanism-mode convention):
`mechanisms.bash_completion.mode`. `"off"` -- return before any read/write, genuinely zero
cost. `"observe"` -- this hook's one real behavior (journal the completion) -- THE DEFAULT, per
the house convention that a free (uncosted) observer defaults ON (mirrors mutation_observer,
delegation_observer, read_observer: nothing here bills the operator). `"enforce"` is a
NAMED-IMPOSSIBLE case exactly like `posttooluse_mutation_observer.py`'s own framing: PostToolUse
fires after the command has already completed, so there is no "deny" available here at all --
`"enforce"` in config warns loudly on stderr and behaves as `"observe"`.

FAIL-OPEN, ALWAYS: this is a diagnostic timing journal, not a safety-critical refusal domain.
Every except path is silent; a journal write failure never surfaces to the tool call.

Stdlib only, top-of-file imports (the lazy-import gate, gates/no_lazy_imports.py, applies).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_VALID_MODES = ("off", "observe", "enforce")
_DEFAULT_MODE = "observe"  # costless observer -- defaults ON, mirrors mutation_observer/read_observer
MECHANISM_KEY = "bash_completion"
_COMPLETION_JOURNAL = "bash_completions.jsonl"


def _first(d, *keys: str, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return default


def _subject_root(data: dict) -> str:
    """Resolve the world root: GATE_SUBJECT_ROOT env var first, else the hook input's own
    `cwd` field -- same convention every sibling hook in this project already uses."""
    env_root = os.environ.get("GATE_SUBJECT_ROOT")
    if env_root:
        return env_root
    cwd = data.get("cwd") or os.getcwd()
    return cwd if isinstance(cwd, str) else ""


def _load_apparatus_quiet(root: str) -> dict:
    if not root:
        return {}
    try:
        with open(os.path.join(root, ".claude", "apparatus.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg if isinstance(cfg, dict) else {}
    except Exception:
        return {}


def _resolve_mode(apparatus: dict, root: str) -> str:
    mechs = apparatus.get("mechanisms")
    entry = mechs.get(MECHANISM_KEY) if isinstance(mechs, dict) else None
    raw = entry.get("mode") if isinstance(entry, dict) else None
    if raw is None:
        return _DEFAULT_MODE
    if raw == "enforce":
        print("[apparatus] WARNING: mechanisms.bash_completion.mode='enforce' is IMPOSSIBLE "
              "for this hook (PostToolUse fires after the command already completed -- there is "
              "no 'deny' available); behaving as 'observe'. See "
              "hooks/posttooluse_bash_completion.py module docstring.", file=sys.stderr)
        return "observe"
    if raw in _VALID_MODES:
        return raw
    print(f"[apparatus] WARNING: mechanisms.{MECHANISM_KEY}.mode={raw!r} in "
          f"{root}/.claude/apparatus.json is unrecognized (must be one of {_VALID_MODES}) -- "
          f"never widening permissions; falling back to {_DEFAULT_MODE!r}.", file=sys.stderr)
    return _DEFAULT_MODE


def _journal_completion(root: Path, rec: dict) -> None:
    path = root / ".claude" / "logs" / _COMPLETION_JOURNAL
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 -- journaling failure must never affect the tool call
        pass


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0
    if not isinstance(data, dict):
        return 0

    try:
        tool = _first(data, "tool_name", "toolName", "name", default="")
        if tool != "Bash":
            return 0

        root_str = _subject_root(data)
        if not root_str:
            return 0
        root = Path(root_str)
        mode = _resolve_mode(_load_apparatus_quiet(root_str), root_str)
        if mode == "off":
            return 0

        command = str((data.get("tool_input") or {}).get("command", ""))
        command_bytes = command.encode("utf-8", "surrogatepass")
        command_sha256 = hashlib.sha256(command_bytes).hexdigest()
        session_id = str(data.get("session_id") or "")

        # IDENTITY, NOT A COMPUTED VERDICT (module docstring, PAIRING RULE): the harness-assigned
        # tool_use_id, transported as-is when the payload carries one, never guessed or paired
        # here. Pairing is a read-time join performed by the consumer, not this hook.
        rec: dict = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "session_id": session_id,
            "command_sha256": command_sha256,
            "command_head": command[:120],
        }
        tool_use_id = data.get("tool_use_id")
        if tool_use_id:
            rec["tool_use_id"] = str(tool_use_id)
        duration_ms = data.get("duration_ms")
        if isinstance(duration_ms, (int, float)):
            rec["duration_ms"] = duration_ms
        _journal_completion(root, rec)
    except Exception:  # noqa: BLE001 -- a diagnostic timing hook must never break a tool call
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
