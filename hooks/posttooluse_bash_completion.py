#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T21:35:25Z
#   last-change: 2026-07-11T21:35:31Z
#   contributors: e4410ef6/main
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

PAIRING RULE, STATED HONESTLY (the maintainer's own words in the commission: "invocation token
if recoverable, else ts-pairing"). There is no side-channel this hook can use to recover
stamp_intercept's own per-invocation UUID directly -- that token is exported into PGOPTIONS on
the command's OWN execution (an env var, not something PostToolUse's JSON payload echoes back),
and Claude Code's own hook-input contract has never been observed to carry a `tool_use_id` this
project could rely on either (`hooks/stamp_intercept.py`'s own module docstring: "the parsed
stdin contract has never carried one"). So this hook does the next best thing, exactly like
`stamp_intercept.py`'s own journal was designed to be correlated: it computes the SAME
`command_sha256` (sha256 of the command TEXT PostToolUse's own payload carries) and does a
FIFO match against `invocations.jsonl`'s own dispatch records --

  1. Read every dispatch record (token, wall_clock, command_sha256) from `invocations.jsonl`.
  2. Read every ALREADY-PAIRED token from THIS hook's own `bash_completions.jsonl` (the tokens
     any earlier completion already claimed), so a repeated identical command
     (`command_sha256` collides) does not double-pair the same dispatch to two completions.
  3. Among UNPAIRED dispatch records sharing this completion's `command_sha256`, pick the
     EARLIEST one by wall_clock (FIFO -- the natural correlation for sequential Bash calls; two
     concurrent Bash calls with byte-identical command text is a named residual gap, disclosed
     here rather than silently mismatched: see NAMED RESIDUAL GAPS below).
  4. A match yields `pairing: "token"` (the dispatch's own token, plus `dispatch_wall_clock` so
     a reader can compute duration_ms without a second file join). No match yields
     `pairing: "ts-only"` (`token: null`) -- the honest fallback the commission itself named,
     not a failure: a completion line with no token is still the ONLY record of "this command,
     with this hash, finished at this wall-clock time," which is strictly more than nothing.

NAMED RESIDUAL GAPS (v1, stated honestly rather than left for a future reader to discover):
  - Two Bash calls with BYTE-IDENTICAL command text in flight concurrently (subagents running
    the same command in parallel) can pair to the wrong dispatch -- FIFO order is a heuristic,
    not a guarantee, when more than one candidate is genuinely eligible at once. Named, not
    fixed: this project's own standing posture (`hooks/posttooluse_mutation_observer.py`'s own
    "ONE SHARED MARKER PER WORLD" residue) is that single-agent-at-a-time sessions are the
    overwhelmingly common case this pass is sized for.
  - If `stamp_intercept` is off/unwired for this invocation (no healthy secret, or mode="off"),
    no dispatch record exists to pair against at all -- every completion in that world reads
    `pairing: "ts-only"` honestly, never a guessed token.
  - PostToolUse's own `tool_input.command` is ASSUMED to echo the same text stamp_intercept's
    PreToolUse leg saw (both hash the command BEFORE any hook-side modification) -- if a future
    Claude Code version diverges on this, the sha256 match degrades gracefully to `"ts-only"`
    for every call (never a wrong pairing silently accepted), because a hash mismatch simply
    finds no candidate.

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
_INVOCATION_JOURNAL = "invocations.jsonl"
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


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def _find_pairing(root: Path, command_sha256: str) -> tuple[str | None, str | None]:
    """FIFO-pair this completion against an unpaired stamp_intercept dispatch record sharing the
    same command_sha256 (module docstring, PAIRING RULE). Returns (token, dispatch_wall_clock),
    both None if no candidate remains. Never raises -- caller treats any read failure as
    'nothing to pair against', the honest ts-only fallback."""
    dispatches = _read_jsonl(root / ".claude" / "logs" / _INVOCATION_JOURNAL)
    already_paired = {
        rec.get("token") for rec in _read_jsonl(root / ".claude" / "logs" / _COMPLETION_JOURNAL)
        if rec.get("token")
    }
    candidates = [
        d for d in dispatches
        if d.get("command_sha256") == command_sha256 and d.get("token")
        and d.get("token") not in already_paired
    ]
    if not candidates:
        return None, None
    # FIFO: earliest by wall_clock (lexicographic ISO-8601-Z sort is chronological).
    candidates.sort(key=lambda d: str(d.get("wall_clock", "")))
    chosen = candidates[0]
    return str(chosen["token"]), str(chosen.get("wall_clock") or "")


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

        token, dispatch_wall_clock = _find_pairing(root, command_sha256)
        rec = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "session_id": session_id,
            "command_sha256": command_sha256,
            "command_head": command[:120],
            "token": token,
            "pairing": "token" if token else "ts-only",
        }
        if dispatch_wall_clock:
            rec["dispatch_wall_clock"] = dispatch_wall_clock
        _journal_completion(root, rec)
    except Exception:  # noqa: BLE001 -- a diagnostic timing hook must never break a tool call
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
