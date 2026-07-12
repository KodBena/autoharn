#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T12:45:30Z
#   last-change: 2026-07-12T12:45:30Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""hooks/posttooluse_apparatus_flip.py -- a typed journal event for every mutation of
`<SUBJECT_ROOT>/.claude/apparatus.json` (tracker item "apparatus-flip-witnessing", panel finding
NIST G1, re-litigation 2026-07-12: "a governed agent can Write .claude/apparatus.json and flip a
mechanism to off mid-session with NO witnessed event -- no refusal, no journal line, no ledger
row, in a system whose evidentiary basis is 'hooks only'").

WHY A DEDICATED, ALWAYS-ON HOOK, NEVER MODE-GATED THROUGH apparatus.json ITSELF -- the load-
bearing design choice, read before ever adding a `mechanisms.apparatus_flip` entry to any
apparatus.json. Every OTHER hook in this project reads its own off/observe/enforce mode FROM
apparatus.json (the switchboard; hooks/pretooluse_change_gate.py's own module docstring). This
hook's entire job is to witness edits to THAT SAME FILE, so if it read its own mode from the file
it watches, the single most dangerous edit -- turning THIS hook off in the same Write that flips
something else -- would have this hook read its own brand-new "off" value BEFORE deciding whether
to journal, and skip journaling the very flip that disabled it: self-silencing exactly the class
of hazard this hook exists to close, one layer up. hooks/pretooluse_change_gate.py's own module
docstring already names the precedent this hook follows: `is_governed()` (the containment +
pattern-match check) is "never itself a mode-gated decision" -- some layer of the switchboard-
guarded system must stay observable no matter what any one mechanism's mode says. This hook is
that floor for apparatus.json itself: it runs UNCONDITIONALLY whenever WIRED, and deliberately
does NOT read any `mechanisms.apparatus_flip` key. A stray `"apparatus_flip"` key someone adds to
apparatus.json expecting it to matter is caught, correctly, by the EXISTING unknown-mechanism-name
sweep (`filing/apparatus_registry.py`, wired into hooks/pretooluse_change_gate.py) -- "no hook
reads this key" is the honest, loud truth, not a silent no-op.

DETECTION METHOD: a content-hash diff against a persisted baseline, not a directory mtime scan.
Contrast hooks/posttooluse_mutation_observer.py, which watches the WHOLE SUBJECT_ROOT tree for
evasive Bash writes and therefore needs a PreToolUse marker + `find -newer` (its detection unit is
"did anything under this tree change"). This hook watches exactly ONE file, so the simplest
mechanism that discharges the job is preferred (ADR-0012 P3: one owner, no more apparatus than the
job needs): PostToolUse fires, reads the CURRENT bytes of `<SUBJECT_ROOT>/.claude/apparatus.json`
(or records their absence), hashes them, and compares against the LAST-OBSERVED hash recorded in a
small state file. No PreToolUse leg is needed -- the whole detection is a single compare, not a
before/after captured within one call. The matcher is `*` (every tool), not an enumerated
`Write|Edit|NotebookEdit|Bash` list -- ADR-0011 Rule 4, enumeration fails open at the next tool
shape (a future MCP tool, a plugin) that can write a file; the check is cheap enough (one stat, one
small read, one sha256, one tiny state file) that watching every call costs nothing worth trading
away the coverage for.

TYPED EVENT (the mandatory deliverable). A flip -- current hash != the last-observed baseline hash
-- journals ONE line to `<SUBJECT_ROOT>/.claude/logs/apparatus_flip.journal.jsonl`:
  {"ts": ..., "event": "apparatus_flip", "tool": <best-effort tool name>,
   "before": {"present": bool, "hash": sha256-hex-or-null, "malformed": bool},
   "after":  {"present": bool, "hash": sha256-hex-or-null, "malformed": bool},
   "mechanisms_changed": {<name>: {"before": mode-or-null, "after": mode-or-null}, ...}}
`mechanisms_changed` is cheap, best-effort per-mechanism detail (ADR-0000 Rule 2's "name the class,
then the honest gap" discipline): if EITHER side's bytes do not parse as a JSON object, the diff is
skipped and `mechanisms_changed` is `{}` -- the flip itself is still journaled via the hash, which
is what makes it detectable at all; only the bonus per-mechanism breakdown degrades. A loud,
non-blocking `additionalContext` warning is ALSO emitted on a flip (mirrors
posttooluse_mutation_observer.py's own convention) so the change is visible on the agent's own next
turn, not only to a later journal reader.

BASELINE, NOT A DENY: the FIRST invocation in a world's life (no persisted state file yet)
establishes the baseline SILENTLY -- no event -- matching every sibling hook's "session start is
not itself a violation" posture, and the no-flip fixture polarity below (seen-red/apparatus-flip/).
Every later call compares against the LAST flip-or-baseline recorded, so a run of N identical calls
between two real content changes journals exactly one event per actual change, never once per call.

FAIL-SAFE ON MALFORMED/MISSING apparatus.json (the other mandatory deliverable). Content is always
hashed over RAW BYTES, so a missing file, an empty file, a truncated file, or an invalid-JSON file
all still produce a comparable state (hash=None only for "file does not exist"; any readable bytes,
however broken as JSON, get a real hash) -- there is no input shape this hook cannot represent as a
state to diff. Every filesystem/JSON operation below is wrapped so a degrade never raises past
`main()`. This hook NEVER blocks: a PostToolUse leg has no deny to offer even in principle (the
same honest impossibility hooks/posttooluse_mutation_observer.py already names for itself), and it
NEVER crashes a tool call over a read/hash/journal hiccup.

NAMED RESIDUE, stated honestly (mirrors the disclosure convention hooks/
posttooluse_mutation_observer.py's own module docstring uses): the read-baseline / compare /
write-baseline sequence is not atomic across two genuinely concurrent tool calls in the same
session -- a rare race could in principle let one of two overlapping flips go unrecorded if their
PostToolUse legs interleave around the same state-file write. Not a correctness issue for the
common single-agent-at-a-time session this project mostly runs; named here rather than discovered
the hard way, exactly the posture the mutation observer's own docstring already sets for the
identical class of race.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)  # hooks/ -> autoharn root
sys.path.insert(0, os.path.join(_REPO_ROOT, "filing"))
import deployment_record  # noqa: E402  (filing/deployment_record.py, the ONE home for the deployment.json shape)

SUBJECT_ROOT = ""
WIRED = False
APPARATUS_PATH = ""
STATE_PATH = ""
JOURNAL_PATH = ""

# Excluded from hooks/posttooluse_mutation_observer.py's own mutated-file report (see that hook's
# _EXCLUDED_BASENAMES, updated alongside this file) -- this is control-plane churn belonging to
# THIS mechanism, not subject-authored content the mutation observer exists to flag.
STATE_BASENAME = "apparatus_flip_state.json"


def _first(d, *keys: str, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return default


def _find_deployment_path(data: dict) -> str | None:
    """Locate this project's deployment.json: an explicit LEDGER_DEPLOYMENT override first, else
    `<cwd>/deployment.json` using the hook input's own `cwd` field (the same convention every
    sibling hook in this project already uses). Returns None -- never raises -- when neither
    resolves to an existing file."""
    explicit = os.environ.get("LEDGER_DEPLOYMENT", "")
    if explicit:
        return explicit
    cwd = data.get("cwd") or os.getcwd()
    candidate = os.path.join(cwd, "deployment.json")
    return candidate if os.path.isfile(candidate) else None


def _load_deployment_quiet(path: str) -> deployment_record.DeploymentRecord | None:
    try:
        return deployment_record.load_deployment(path)
    except deployment_record.DeploymentError:
        return None


def _configure(data: dict) -> None:
    """Resolve SUBJECT_ROOT for THIS invocation, mirroring hooks/posttooluse_mutation_observer.py's
    own `_configure()` precedence (env override > deployment.json > unwired). No PGHOST/PGDB/LEDGER
    resolution here at all -- unlike its siblings, this hook never touches the DB."""
    global SUBJECT_ROOT, WIRED, APPARATUS_PATH, STATE_PATH, JOURNAL_PATH
    dep_path = _find_deployment_path(data)
    dep = _load_deployment_quiet(dep_path) if dep_path else None
    using_deployment = bool(dep_path and dep)

    env_subject_root = os.environ.get("GATE_SUBJECT_ROOT")
    default_root = os.path.dirname(dep_path) if using_deployment else ""
    SUBJECT_ROOT = (os.path.abspath(env_subject_root or default_root)
                     if (env_subject_root or default_root) else "")
    WIRED = bool((env_subject_root or using_deployment) and SUBJECT_ROOT
                 and os.path.isdir(SUBJECT_ROOT))
    if WIRED:
        APPARATUS_PATH = os.path.join(SUBJECT_ROOT, ".claude", "apparatus.json")
        STATE_PATH = os.path.join(SUBJECT_ROOT, ".claude", STATE_BASENAME)
        JOURNAL_PATH = os.path.join(SUBJECT_ROOT, ".claude", "logs", "apparatus_flip.journal.jsonl")
    else:
        APPARATUS_PATH = STATE_PATH = JOURNAL_PATH = ""


def _read_current_state() -> dict:
    """{"present": bool, "hash": sha256-hex|None, "malformed": bool, "mechanisms": dict|None}.
    Never raises: every failure mode (missing file, unreadable bytes, invalid JSON, a JSON value
    that is not an object) degrades to an honest state rather than an exception -- the fail-safe
    deliverable in code."""
    if not os.path.isfile(APPARATUS_PATH):
        return {"present": False, "hash": None, "malformed": False, "mechanisms": None}
    try:
        raw = Path(APPARATUS_PATH).read_bytes()
    except OSError:
        return {"present": False, "hash": None, "malformed": False, "mechanisms": None}
    h = hashlib.sha256(raw).hexdigest()
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except Exception:
        return {"present": True, "hash": h, "malformed": True, "mechanisms": None}
    if not isinstance(parsed, dict):
        return {"present": True, "hash": h, "malformed": True, "mechanisms": None}
    mechs = parsed.get("mechanisms")
    modes: dict[str, str] = {}
    if isinstance(mechs, dict):
        for name, entry in mechs.items():
            mode = entry.get("mode") if isinstance(entry, dict) else None
            modes[str(name)] = mode if isinstance(mode, str) else "?"
    return {"present": True, "hash": h, "malformed": False, "mechanisms": modes}


def _load_baseline() -> dict | None:
    """The persisted last-observed state, or None -- treated as "no baseline yet" (first-ever
    observation for this world, OR a corrupt/missing state file, which degrades identically: a
    fresh baseline is established silently rather than a stale one trusted)."""
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            wrapper = json.load(f)
        state = wrapper.get("state") if isinstance(wrapper, dict) else None
        return state if isinstance(state, dict) else None
    except Exception:
        return None


def _save_baseline(state: dict, ts: str) -> None:
    try:
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        tmp = STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"state": state, "observed_at": ts}, f)
        os.replace(tmp, STATE_PATH)
    except OSError:
        pass


def _mechanisms_diff(before: dict | None, after: dict | None) -> dict:
    """Best-effort per-mechanism mode diff. {} whenever EITHER side could not be parsed as a JSON
    object (before/after "mechanisms" is None) -- the flip is still journaled via the hash; only
    this bonus breakdown degrades, named honestly rather than guessed at."""
    if not isinstance(before, dict) or not isinstance(after, dict):
        return {}
    changed = {}
    for name in sorted(set(before) | set(after)):
        b, a = before.get(name), after.get(name)
        if b != a:
            changed[name] = {"before": b, "after": a}
    return changed


def _journal(rec: dict) -> None:
    try:
        os.makedirs(os.path.dirname(JOURNAL_PATH), exist_ok=True)
        with open(JOURNAL_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _emit_warning(before: dict, after: dict, mechanisms_changed: dict, tool: str) -> None:
    if mechanisms_changed:
        mech_text = "\n".join(f"  - {name}: {c['before']!r} -> {c['after']!r}"
                               for name, c in mechanisms_changed.items())
    else:
        mech_text = ("  (per-mechanism detail unavailable -- the before or after content did not "
                     "parse as a JSON object; the flip is still journaled via its content hash)")
    warning = (
        "[apparatus-flip WARNING, observer-mode -- never blocks] .claude/apparatus.json changed "
        f"during this session via a {tool} call (hooks/posttooluse_apparatus_flip.py):\n"
        f"before: present={before['present']} hash={before['hash']}\n"
        f"after:  present={after['present']} hash={after['hash']}\n"
        f"mechanism mode changes:\n{mech_text}\n"
        "This mechanism only watches and journals -- it never denies. If this change was not "
        "expected, review .claude/logs/apparatus_flip.journal.jsonl."
    )
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse", "additionalContext": warning}}))


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # unparseable input -- nothing this hook can act on
    if not isinstance(data, dict):
        return 0

    try:
        _configure(data)
    except Exception:  # noqa: BLE001 -- a config-resolution bug must never break a tool call
        return 0
    if not WIRED:
        return 0

    tool = str(_first(data, "tool_name", "toolName", "name", default="?"))

    try:
        current = _read_current_state()
        before = _load_baseline()
        now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z"
        if before is None:
            # First-ever observation for this world: establish baseline silently, no event --
            # session start is not itself a flip (mirrors every sibling hook's posture).
            _save_baseline(current, now)
            return 0
        if before.get("hash") == current.get("hash") and before.get("present") == current.get("present"):
            return 0  # unchanged -- no journal, no state rewrite, genuinely a no-op
        mechanisms_changed = _mechanisms_diff(before.get("mechanisms"), current.get("mechanisms"))
        before_out = {"present": before.get("present"), "hash": before.get("hash"),
                      "malformed": before.get("malformed")}
        after_out = {"present": current.get("present"), "hash": current.get("hash"),
                     "malformed": current.get("malformed")}
        _journal({"ts": now, "event": "apparatus_flip", "tool": tool,
                  "before": before_out, "after": after_out,
                  "mechanisms_changed": mechanisms_changed})
        _emit_warning(before_out, after_out, mechanisms_changed, tool)
        _save_baseline(current, now)
    except Exception:  # noqa: BLE001 -- an observer must never crash a tool call over a hiccup
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
