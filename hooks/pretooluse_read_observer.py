#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T18:02:52Z
#   last-change: 2026-07-11T18:02:52Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""hooks/pretooluse_read_observer.py -- the READ observer (BACKLOG "Five-item batch,
maintainer-approved 2026-07-11 evening", item 3). Purpose, on the record: makes "did the
reviewer consult the artifact independently" answerable (the run10 retrospective's
could-not-answer item 3, design/ORCH-RETROSPECTIVE-RUN10.md: "the invocation log captures only
Bash, and a reviewer that inspects files via the Read tool leaves no trace ... review rows
that claim 'independently read app/index.html' are trusted, not witnessed"). This hook closes
exactly that gap: every `Read` tool call is journaled, so a later audit can check a review
row's claim ("I read X") against a real, timestamped, session-attributed record instead of
trusting the claim.

SHAPE, FOLLOWED FROM hooks/pretooluse_delegation_observer.py (module docstring there is the
precedent this hook mirrors deliberately -- same apparatus.json switchboard convention, same
WIRED derivation, same fail-open-on-any-error posture, same "re-derive rather than import"
no-coupling-across-hook-files rule this project's hooks already state for themselves):
  1. JOURNAL every Read call, always, when wired and mode != "off": ts (UTC-Z, the unified
     convention BACKLOG's contemporaneity work fixed hooks onto after the pre-run-9 UTC-Z/
     naive-local disagreement, commit 19c9159), session id, and the file path read. Nothing
     else -- no content, no excerpt; the file path and who-read-it-when is the evidentiary
     fact this hook exists to bank, not the file's own text (already on disk, already
     git-tracked where it matters).
  2. NO warning, NO deny path at all -- unlike delegation_observer (which warns when no work
     item is open+claimed) this hook has nothing to teach and nothing to gate: reading a file
     is never itself a policy violation, so there is no enforce state to sanction and no
     observe-mode "would have denied" outcome to surface. This is a COSTLESS observer in the
     mutation_observer/delegation_observer sense (no claude -p call, no external cost) but
     with an even smaller footprint than either: it has exactly one behavior (journal),
     present in every mode except "off".

APPARATUS.JSON SWITCHBOARD: `mechanisms.read_observer.mode`, resolved once per invocation,
only when WIRED (same env/deployment.json resolution order as every sibling hook here).
`"off"` -- return before any file I/O, genuinely zero cost. `"observe"` -- journal (this
hook's one behavior) -- THE DEFAULT, per the house convention that a free (uncosted)
observer defaults ON/observe rather than off (mirrors mutation_observer and
delegation_observer, both `"observe"` by default for the identical reason: nothing here bills
the operator, so there is no "no world silently bills its operator" reason to start it
disabled). `"enforce"` is a NAMED-NOT-YET-SANCTIONED case: this hook has no deny path to
enforce at all (reading a file is not a thing this project's law forbids), so `"enforce"` in
config warns loudly on stderr and behaves as `"observe"` -- distinct from mutation_observer's
"enforce is technically IMPOSSIBLE" framing (this hook's PreToolUse attachment point COULD in
principle deny a Read, the same way delegation_observer's attachment point could in principle
deny a dispatch) and distinct from delegation_observer's own "possible in principle, not yet
sanctioned" framing only in that no one has ever proposed denying a Read at all -- named
honestly rather than asserted impossible.

WHY A SEPARATE RESOLUTION, NOT A SHARED IMPORT of the identically-shaped functions in
pretooluse_delegation_observer.py / pretooluse_change_gate.py: the same "no load-bearing
coupling across independently-touched hook files" posture those two files' own docstrings
already state, re-derived here rather than imported, so this file's correctness never depends
on an unrelated hook's internals surviving unchanged (mirrored a fourth time now).

Stdlib only, top-of-file imports (the lazy-import gate, gates/no_lazy_imports.py, applies).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

_VALID_MODES = ("off", "observe", "enforce")
_DEFAULT_MODE = "observe"  # costless observer -- defaults ON, mirrors mutation_observer/delegation_observer
MECHANISM_KEY = "read_observer"


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
    path = os.path.join(root, ".claude", "apparatus.json")
    try:
        with open(path, encoding="utf-8") as f:
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
        print(f"[apparatus] WARNING: mechanisms.{MECHANISM_KEY}.mode='enforce' is NOT YET "
              f"SANCTIONED for this hook (reading a file is not a refusable act under this "
              f"project's law -- see hooks/pretooluse_read_observer.py module docstring); "
              f"behaving as 'observe'.", file=sys.stderr)
        return "observe"
    if raw in _VALID_MODES:
        return raw
    print(f"[apparatus] WARNING: mechanisms.{MECHANISM_KEY}.mode={raw!r} in "
          f"{root}/.claude/apparatus.json is unrecognized (must be one of {_VALID_MODES}) -- "
          f"never widening permissions; falling back to {_DEFAULT_MODE!r}.", file=sys.stderr)
    return _DEFAULT_MODE


def _journal_path(root: str) -> str:
    return os.path.join(root, ".claude", "logs", "read_observer.journal.jsonl")


def _journal(root: str, rec: dict) -> None:
    path = _journal_path(root)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 -- an observer must never break a tool call over log I/O
        pass


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # unparseable input -- nothing this hook can act on
    if not isinstance(data, dict):
        return 0

    tool = _first(data, "tool_name", "toolName", "name", default="")
    if tool != "Read":
        return 0

    try:
        root = _subject_root(data)
        wired = bool(root and os.path.isdir(root))
        if not wired:
            return 0
        mode = _resolve_mode(_load_apparatus_quiet(root), root)
        if mode == "off":
            return 0

        tool_input = _first(data, "tool_input", "toolInput", "input", default={})
        if not isinstance(tool_input, dict):
            tool_input = {}
        file_path = _first(tool_input, "file_path", "filePath", default="")
        session_id = str(data.get("session_id") or "")

        _journal(root, {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "session_id": session_id,
            "file_path": str(file_path),
        })
    except Exception:  # noqa: BLE001 -- an observer must never break a Read tool call
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
