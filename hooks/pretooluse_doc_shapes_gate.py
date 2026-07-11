#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T17:02:12Z
#   last-change: 2026-07-11T17:02:12Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""pretooluse_doc_shapes_gate — the world-side, live-write-time transport of
gates/doc_shapes.py (ADR-0017's deterministic zero-context-reader core), commissioned so a
scaffolded world can get the same measured-sound checks (standalone fragment paragraphs; bare
positional references into HANDOFF.md) DURING the session that writes its documentation, not
only when the world's own repo eventually runs a pre-commit gate (BACKLOG "ADR-0017 A:B:C
attestation loop", orchestrator extension "leverage the mandatory documentation step for
run11").

WHY A NEW HOOK, NOT A COPY OF gates/doc_shapes.py: a scaffolded world is not a git repo at
scaffold time (BACKLOG "run10's task 1 was git init") — a pre-commit hook has nothing to attach
to before that. The sound surface is the write itself: this is a PreToolUse hook on
`Write`/`Edit` of a `.md` file, so a defective document can be refused (in enforce mode) or
flagged (in observe mode) before it ever lands on disk, mirroring
hooks/pretooluse_change_gate.py's PreToolUse-deny contract exactly (same JSON shape, same
exit codes) rather than inventing a new refusal vocabulary. It reuses gates/doc_shapes.py
directly (imported by path, sibling directory of this file in the SAME autoharn checkout every
scaffolded world already references by absolute path for every other hook) rather than
duplicating its two checks — one judgment, one home, per ADR-0012 P1.

WHAT IT CHECKS: gates/doc_shapes.py's `check_file()` against the FULL PROPOSED content of the
write, not just the changed span. For `Write`, that is `tool_input.content` directly. For
`Edit`, the current on-disk content of `tool_input.file_path` is read and `old_string` is
replaced with `new_string` (every occurrence if `tool_input.replace_all` is true, else the
first) to reconstruct the file as it would read AFTER the edit — necessary because
doc_shapes.py's FRAGMENT check is context-sensitive (it looks at the blank-or-not lines
immediately before/after a candidate paragraph), so checking only the new_string snippet in
isolation would misjudge a snippet's edges as if they were the whole file's edges. The proposed
content is written to a private temp file and checked there (gates/doc_shapes.py operates on a
real path); the violation strings it returns are then rewritten to name the real target path,
never the temp file, so the teach-text reads naturally.

APPARATUS.JSON MECHANISM SWITCHBOARD: `mechanisms.doc_shapes_gate.mode` at
`<world>/.claude/apparatus.json` (world = GATE_SUBJECT_ROOT env var, else the session's cwd),
same resolution order and three-mode contract (off/observe/enforce) as every sibling mechanism
in this file's own docstring precedent (hooks/doc_legibility_critic.py, hooks/demurral_detect.py).
Missing file/key resolves to **`"observe"`**, not `"off"` and not `"enforce"` — the deliberate,
stated choice for this pass, not an oversight:

  - It is NOT `"off"` by default (unlike the costed `demurral_detect`/`doc_legibility_critic`
    critics): this check spends nothing — pure-stdlib text scanning, no subprocess, no `claude
    -p` call — so there is no "no world silently bills its operator" reason to start it
    disabled, and a scaffolded world with the discipline available but invisible would defeat
    the point of offering it.
  - It is NOT `"enforce"` by default: this is the FIRST time gates/doc_shapes.py's two checks
    run as a LIVE, interactive, write-time blocking gate anywhere — even this repo's own
    pre-commit chain does not yet invoke it (a pre-existing gap noted in the attestation-loop
    BACKLOG entry). Its false-positive rate is measured (BACKLOG "Documentation legibility
    indictment" packet: 18 fragment hits / 208 docs, 1 HANDOFF-positional hit, both near-zero
    after exemptions) against this REPO's static corpus, not against the different shape of
    documents a fresh scaffolded world's own agents will write in real time. Observer-first
    matches this project's own precedent for a newly-introduced observation point
    (`mutation_observer`, `delegation_observer` both default to `"observe"`, never `"enforce"`,
    on first introduction) rather than assuming day-one blocking is safe.
  - **The one-line flip to enforce for a specific world** (e.g. run11, if the maintainer wants
    it live-blocking from birth): set `"doc_shapes_gate": {"mode": "enforce"}` in that world's
    `.claude/apparatus.json` under `mechanisms` — no code change, no re-scaffold, live on the
    very next `Write`/`Edit` of a `.md` file (same live-read guarantee APPARATUS.md documents
    for every other mechanism here).

ENFORCE MODE: a violation DENIES the tool call — `hookSpecificOutput.permissionDecision:
"deny"` plus `permissionDecisionReason` naming every violation (file:line, the check name, the
offending text, and the waiver escape hatch `doc-shapes-allow: <reason>`), byte-shape-identical
to hooks/pretooluse_change_gate.py's `_deny()` contract, exit 2. OBSERVE MODE: the SAME check
runs, but a would-have-denied outcome becomes ALLOW with the identical message riding
`additionalContext` (prefixed, matching `_observe_allow()`'s convention), exit 0. OFF MODE:
exits before the check runs, no cost, no journal. A CLEAN document is silent and ALLOWs in
every mode — no journal noise for the common case.

FAIL-OPEN ON ANY UNEXPECTED ERROR (reading the current file for an Edit, decoding stdin,
importing the gate module): this is a documentation-legibility check, not a safety-critical
refusal domain: an error here must never block an otherwise-legitimate Write/Edit the way a
change-gate or stamp-intercept failure fails CLOSED. Every except path returns an ALLOW.

Journal: `<world>/.claude/logs/doc_shapes_gate.journal.jsonl`, one line per DENY or
OBSERVED-WOULD-DENY outcome (a clean pass is not journaled, matching
hooks/doc_legibility_critic.py's own convention of only recording the interesting case).

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gates"))
import doc_shapes  # noqa: E402 -- sibling-directory import, path set immediately above

MECHANISM_KEY = "doc_shapes_gate"
_VALID_MODES = ("off", "observe", "enforce")
_DEFAULT_MODE = "observe"  # see module docstring: neither costed-off nor battle-tested-enforce


def _first(d: Any, *keys: str, default: Any = None) -> Any:
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return default


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


def _resolve_mode(apparatus: dict, root: Optional[str]) -> str:
    mechs = apparatus.get("mechanisms")
    entry = mechs.get(MECHANISM_KEY) if isinstance(mechs, dict) else None
    entry = entry if isinstance(entry, dict) else {}
    raw = entry.get("mode")
    if raw is None:
        return _DEFAULT_MODE
    if raw in _VALID_MODES:
        return raw
    print(f"[apparatus] WARNING: mechanisms.{MECHANISM_KEY}.mode={raw!r} in "
          f"{root}/.claude/apparatus.json is unrecognized (must be one of {_VALID_MODES}) — "
          f"falling back to {_DEFAULT_MODE!r} (never widening toward 'enforce' on a bad value).",
          file=sys.stderr)
    return _DEFAULT_MODE


def _proposed_content(payload: dict) -> tuple[str, str] | None:
    """Return (file_path, proposed_full_content) for a Write/Edit of a .md file that can be
    checked, else None (not a .md write, or content could not be reconstructed -- fail-open)."""
    tool = _first(payload, "tool_name", "toolName", "name", default="")
    if tool not in ("Write", "Edit"):
        return None
    tool_input = _first(payload, "tool_input", "toolInput", "input", default={})
    if not isinstance(tool_input, dict):
        return None
    file_path = _first(tool_input, "file_path", "filePath", default="")
    if not isinstance(file_path, str) or not file_path.endswith(".md"):
        return None

    if tool == "Write":
        content = _first(tool_input, "content", default="")
        return file_path, content if isinstance(content, str) else ""

    # Edit: reconstruct the post-edit content from the current on-disk file.
    old_string = _first(tool_input, "old_string", "oldString", default=None)
    new_string = _first(tool_input, "new_string", "newString", default="")
    if not isinstance(old_string, str) or not isinstance(new_string, str):
        return None
    try:
        current = Path(file_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None  # can't reconstruct -- fail-open, let the real Edit tool sort it out
    if old_string not in current:
        return None  # the real Edit call will itself fail on this; nothing sound to check
    replace_all = bool(_first(tool_input, "replace_all", "replaceAll", default=False))
    proposed = current.replace(old_string, new_string) if replace_all \
        else current.replace(old_string, new_string, 1)
    return file_path, proposed


def _check(file_path: str, content: str) -> list[str]:
    """Run gates/doc_shapes.check_file against the proposed content via a private temp file,
    then rewrite each violation's leading path to the real target path (never the temp path)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False,
                                     encoding="utf-8") as tf:
        tf.write(content)
        tmp_path = Path(tf.name)
    try:
        raw = doc_shapes.check_file(tmp_path)
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass
    prefix = f"{tmp_path}:"
    rewritten = []
    for v in raw:
        rewritten.append(file_path + ":" + v[len(prefix):] if v.startswith(prefix) else v)
    return rewritten


def _journal(payload: dict, record: dict) -> None:
    cwd = _first(payload, "cwd", default="")
    root = os.environ.get("GATE_SUBJECT_ROOT") or (cwd if isinstance(cwd, str) else "")
    if not root:
        return
    path = Path(root) / ".claude" / "logs" / "doc_shapes_gate.journal.jsonl"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 -- journaling failure must never affect the decision
        pass


def _deny(payload: dict, file_path: str, violations: list[str]) -> int:
    msg = (f"doc-shapes gate: {len(violations)} zero-context-reader finding(s) in {file_path} "
           f"(ADR-0017 Rules 2-3) — " + " | ".join(violations))
    _journal(payload, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z",
                       "outcome": "denied", "file": file_path, "violations": violations})
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": msg}}))
    print(msg, file=sys.stderr)
    return 2


def _observe_allow(payload: dict, file_path: str, violations: list[str]) -> int:
    msg = (f"doc-shapes gate: {len(violations)} zero-context-reader finding(s) in {file_path} "
           f"(ADR-0017 Rules 2-3) — " + " | ".join(violations))
    _journal(payload, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z",
                       "outcome": "observed_would_deny", "file": file_path,
                       "violations": violations})
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "allow",
        "additionalContext": f"[apparatus observe-mode WARNING — would DENY under enforce] {msg}"}}))
    return 0


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0
    if not isinstance(payload, dict):
        return 0

    root = _apparatus_root(payload)
    mode = _resolve_mode(_load_apparatus_quiet(root), root)
    if mode == "off":
        return 0

    try:
        located = _proposed_content(payload)
        if located is None:
            return 0
        file_path, content = located
        violations = _check(file_path, content)
    except Exception:  # noqa: BLE001 -- fail-open: a legibility check must never block a write
        return 0

    if not violations:
        return 0  # clean -- silent allow, no journal noise for the common case

    if mode == "enforce":
        return _deny(payload, file_path, violations)
    return _observe_allow(payload, file_path, violations)  # mode == "observe"


if __name__ == "__main__":
    sys.exit(main())
