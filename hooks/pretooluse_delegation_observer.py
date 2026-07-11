#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-10T23:38:38Z
#   last-change: 2026-07-11T14:58:59Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""hooks/pretooluse_delegation_observer.py -- the delegation OBSERVER (Part 2, BACKLOG "Run-8
mid-run forensics", 2026-07-11 finding 3: "investigation is ungoverned" -- 5m12s and 13 tool
calls, including a 100-second subagent dispatch, landed ZERO ledger rows before the first
`./led` call; no `question` row was ever filed for "the spec is missing" across the ENTIRE
ledger, all runs). Preamble point 7 (mechanized here, observer-first): "Investigation and
delegation are work: ledger them BEFORE doing them ... Dispatching a subagent is a `decision`
row (what is delegated, why)." Finding 3 named the mechanization site explicitly: "the subagent
dispatch is a machine-observable tool event, so a permit/observer at PreToolUse(Task/Agent) IS
mechanizable" -- this hook is that mechanization, queued and now built.

TOOL NAME -- BOTH "Task" AND "Agent" matched defensively: `instruments/act_stream/
claude_code_adapter.py`'s own delegation-recognition comment names the exact history this
mirrors -- "Agent" is the CURRENT tool name; "Task" is its legacy name (that adapter's own
finding 23: recognizing only one silently dropped the other's real spawns). This hook takes the
same defensive stance rather than assume today's name is permanent.

TWO THINGS, EVERY DISPATCH, UNCONDITIONALLY (subject to WIRED + mode != "off" -- see APPARATUS.JSON
SWITCHBOARD below):
  1. JOURNAL every dispatch, always, regardless of ledger state: ts, session id, the tool
     input's own `description` field, and the `prompt` field reduced to a sha256 + first-200-char
     excerpt (mirrors `instruments/act_stream/claude_code_adapter.py`'s own `Act.sha_excerpt`
     convention -- a full prompt is not journaled verbatim; a fingerprint + excerpt is enough to
     recognize it later without duplicating potentially-large or sensitive prompt text into a
     plaintext log).
  2. WARN (never deny -- see OBSERVER ONLY below) via a loud, non-blocking `additionalContext`
     injection, ONLY when this world's ledger carries the s22 work-item layer AND no work item is
     currently open+claimed -- the exact permit-to-work SHAPE `hooks/pretooluse_change_gate.py`
     already established (`has_work_item_layer()` / `has_open_claimed_work_item()`), re-derived
     here rather than imported (see WHY A SEPARATE RESOLUTION below), teaching the operator to
     ledger the delegation itself as a `decision` row (preamble point 7) -- not merely to open a
     work item, since a delegation with no stated "what/why" is the actual defect finding 3 named
     (an OPEN+CLAIMED work item alone does not answer "what is delegated, why").

OBSERVER ONLY, BY MAINTAINER MANDATE -- NOT A TECHNICAL IMPOSSIBILITY (named honestly, the
opposite framing from `hooks/posttooluse_mutation_observer.py`'s own OBSERVER ONLY section): a
PreToolUse hook on Task/Agent COULD deny in principle -- this attachment point fires BEFORE the
subagent is dispatched, unlike mutation_observer's PostToolUse leg, which fires after the
mutation already happened and therefore has no possible deny at all. Here a deny is technically
available but NOT YET SANCTIONED: refusing to let an agent delegate work is a materially more
invasive act than refusing an unticketed file edit (permit_to_work) or warning about an
unpermitted mutation (mutation_observer) -- the build mandate for this hook states the posture
verbatim: "a PreToolUse deny for delegation is possible in principle but NOT sanctioned yet."
This hook is built observer-only on that basis; a future maintainer-ratified spec could add an
`"enforce"` deny path here without changing this hook's attachment point or detection logic.

APPARATUS.JSON SWITCHBOARD (mirrors the project's standing mechanism-mode convention,
maintainer mandate 2026-07-10): `mechanisms.delegation_observer.mode`, read once per invocation
inside `_configure()`, only when WIRED. `"off"` -- return before any journal/DB work at all:
genuinely zero cost, not merely zero warnings (mirrors mutation_observer's own `"off"` posture).
`"observe"` -- this mechanism's real behavior (journal + conditional warning above); the
default (rule c: no enforce state is SANCTIONED yet -- see OBSERVER ONLY above -- so, exactly
like mutation_observer, the "free mechanisms default to enforce" rule does not apply verbatim to
a mechanism with no sanctioned enforce state to default to). `"enforce"` in config is a
NAMED-NOT-YET-SANCTIONED case (distinct from mutation_observer's NAMED-IMPOSSIBLE case -- see
OBSERVER ONLY above): this hook warns loudly on stderr and behaves as `"observe"`, exactly like
mutation_observer's own downgrade, but for a different, honestly-stated reason. An unrecognized
mode string never widens permissions -- falls back to `"observe"` with a loud stderr warning
naming the bad value.

WHY A SEPARATE RESOLUTION, NOT A SHARED IMPORT of hooks/pretooluse_change_gate.py's
has_work_item_layer()/has_open_claimed_work_item(): the same "no load-bearing coupling across
independently-touched hook files" posture hooks/stop_clean_exit.py's and
hooks/posttooluse_mutation_observer.py's own docstrings already state, for the identical reason
-- re-derived here, byte-similar, on purpose, matching this project's own established convention
for this exact function pair (now mirrored a third time; an import would couple this hook's
correctness to pretooluse_change_gate.py's unrelated internals surviving unchanged).

Stdlib only, top-of-file imports (the lazy-import gate, gates/no_lazy_imports.py, applies).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)  # hooks/ -> autoharn root
sys.path.insert(0, os.path.join(_REPO_ROOT, "filing"))
import deployment_record  # noqa: E402  (filing/deployment_record.py, the ONE home for the deployment.json shape)

_DEFAULT_PGHOST = "192.168.122.1"
_DEFAULT_PGDB = "nla"
_DEFAULT_LEDGER = "public.ledger"

PGHOST = _DEFAULT_PGHOST
PGDB = _DEFAULT_PGDB
LEDGER = _DEFAULT_LEDGER
SUBJECT_ROOT = ""
JOURNAL = ""
WIRED = False
MODE = "observe"

_VALID_MODES = ("off", "observe", "enforce")
_DELEGATION_TOOLS = ("Task", "Agent")  # module docstring TOOL NAME section


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
    """apparatus["mechanisms"]["delegation_observer"]["mode"], defaulted/validated per the
    maintainer's mechanism-mode convention. Default is `"observe"` (module docstring: no enforce
    state is SANCTIONED yet -- distinct from mutation_observer's IMPOSSIBLE framing, see OBSERVER
    ONLY). `"enforce"` in config is a NAMED-NOT-YET-SANCTIONED case, not an ordinary unrecognized
    value -- warned and downgraded to `"observe"` explicitly, same mechanics as
    hooks/posttooluse_mutation_observer.py's own downgrade, different stated reason."""
    default = "observe"
    mechs = apparatus.get("mechanisms")
    entry = mechs.get("delegation_observer") if isinstance(mechs, dict) else None
    raw = entry.get("mode") if isinstance(entry, dict) else None
    if raw is None:
        return default
    if raw == "enforce":
        print("[apparatus] WARNING: mechanisms.delegation_observer.mode='enforce' is NOT YET "
              "SANCTIONED for this hook (a PreToolUse deny on Task/Agent dispatch is possible in "
              "principle but has not been ratified -- see hooks/pretooluse_delegation_observer.py "
              "module docstring, OBSERVER ONLY section); behaving as 'observe'.", file=sys.stderr)
        return "observe"
    if raw in _VALID_MODES:
        return raw
    print(f"[apparatus] WARNING: mechanisms.delegation_observer.mode={raw!r} in "
          f"{root}/.claude/apparatus.json is unrecognized (must be one of {_VALID_MODES}) -- "
          f"never widening permissions; falling back to {default!r}.", file=sys.stderr)
    return default


def _configure(data: dict) -> None:
    """Resolve every connection/config value for THIS invocation. Called once, at the top of
    `main()`, right after stdin is parsed. Same env-override > deployment.json > byte-held-default
    precedence, and the same WIRED derivation, every sibling hook in this project already uses."""
    global PGHOST, PGDB, LEDGER, SUBJECT_ROOT, JOURNAL, WIRED, MODE
    dep_path = _find_deployment_path(data)
    dep = _load_deployment_quiet(dep_path) if dep_path else None
    using_deployment = bool(dep_path and dep)

    PGHOST = os.environ.get("LEDGER_HOST") or (dep.host if dep else None) or _DEFAULT_PGHOST
    PGDB = os.environ.get("LEDGER_DB") or (dep.db if dep else None) or _DEFAULT_PGDB
    LEDGER = (os.environ.get("GATE_LEDGER") or (f"{dep.schema}.ledger" if dep else None)
              or _DEFAULT_LEDGER)

    env_subject_root = os.environ.get("GATE_SUBJECT_ROOT")
    default_root = os.path.dirname(dep_path) if using_deployment else ""
    SUBJECT_ROOT = (os.path.abspath(env_subject_root or default_root)
                     if (env_subject_root or default_root) else "")
    WIRED = bool((env_subject_root or using_deployment) and SUBJECT_ROOT
                 and os.path.isdir(SUBJECT_ROOT))

    JOURNAL = (os.path.join(SUBJECT_ROOT, ".claude", "logs", "delegation_observer.journal.jsonl")
               if WIRED else "")

    apparatus = _load_apparatus_quiet(SUBJECT_ROOT) if WIRED else {}
    MODE = _resolve_mode(apparatus, SUBJECT_ROOT)


def _ledger_schema() -> str:
    return LEDGER.rsplit(".", 1)[0] if "." in LEDGER else "public"


def has_work_item_layer() -> bool:
    """Cheap, lock-free, catalog-only existence probe -- mirrors
    hooks/pretooluse_change_gate.py's identically-named function exactly (module docstring, WHY A
    SEPARATE RESOLUTION). Raises on a genuine DB error; the caller treats that as "nothing to
    warn about" (an observer must never break a tool call over a DB hiccup)."""
    schema = _ledger_schema()
    ident = f"{schema}.work_item_current".replace("'", "''")
    out = subprocess.run(
        ["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-c",
         f"SELECT to_regclass('{ident}') IS NOT NULL;"],
        capture_output=True, text=True, timeout=8, check=True,
    )
    return out.stdout.strip() == "t"


def has_open_claimed_work_item() -> bool:
    """Mirrors hooks/pretooluse_change_gate.py's identically-named function exactly: True iff
    `work_item_current` has at least one row with state='open' AND a non-NULL claimant."""
    schema = _ledger_schema()
    sql = (f"SELECT EXISTS (SELECT 1 FROM {schema}.work_item_current "
           f"WHERE state = 'open' AND claimant IS NOT NULL);")
    out = subprocess.run(
        ["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-c", sql],
        capture_output=True, text=True, timeout=8, check=True,
    )
    return out.stdout.strip() == "t"


def _journal(rec: dict) -> None:
    if not JOURNAL:
        return
    try:
        os.makedirs(os.path.dirname(JOURNAL), exist_ok=True)
        with open(JOURNAL, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 -- an observer must never break a tool call over log I/O
        pass


DENY_HINT = ("./led decision \"<what is delegated, why>\"\n"
             "  ./led work open <slug> \"<title>\"\n"
             "  ./led work claim <slug>")


def _emit_warning(description: str) -> None:
    warning = (
        "[delegation-observer WARNING, observer-mode -- never blocks] dispatching a subagent is "
        "work (CLAUDE.md preamble point 7: \"Dispatching a subagent is a `decision` row (what is "
        "delegated, why)\") and this world has NO open+claimed work item covering it "
        "(hooks/pretooluse_delegation_observer.py; BACKLOG 'Run-8 mid-run forensics', 2026-07-11 "
        "finding 3: 5m12s of investigation, including a subagent dispatch, landed zero ledger "
        "rows before the first ./led call):\n"
        f"delegation: {description or '(no description given)'}\n"
        f"ledger the delegation BEFORE it starts, and/or cover it with an open+claimed work item:\n"
        f"  {DENY_HINT}"
    )
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "allow",
        "additionalContext": warning}}))


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

    if not WIRED or MODE == "off":
        return 0

    tool = _first(data, "tool_name", "toolName", "name", default="")
    if tool not in _DELEGATION_TOOLS:
        return 0

    inp = _first(data, "tool_input", "toolInput", "input", default={})
    if not isinstance(inp, dict):
        inp = {}
    description = str(inp.get("description", ""))
    prompt = str(inp.get("prompt", ""))
    session_id = str(data.get("session_id") or "")
    prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    # 1. JOURNAL every dispatch, unconditionally (module docstring) -- before any DB work, so a
    # DB hiccup below never costs the journal record.
    _journal({
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "session_id": session_id,
        "tool": tool,
        "description": description,
        "prompt_sha256": prompt_sha256,
        "prompt_excerpt": prompt[:200],
    })

    # 2. WARN only when the work-item layer exists and no item is open+claimed (module docstring).
    # Never raises past this point -- an observer must never break a tool call over a DB hiccup.
    try:
        if has_work_item_layer() and not has_open_claimed_work_item():
            _emit_warning(description)
    except Exception:  # noqa: BLE001
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
