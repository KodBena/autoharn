#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-10T23:38:38Z
#   last-change: 2026-07-14T01:07:03Z
#   contributors: e4410ef6/main, a857c93d/main
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

THE RETURN LEG (small-follow-ups commission item 5; BACKLOG "Follow-ups commission scope
extended" item 2: "the delegation observer gains a return leg (PostToolUse on Task) --
dispatch-to-return duration per subagent, closing the reviewer-execution-window inference gap
by measurement"). This file now handles BOTH `hook_event_name` values on the SAME `Task|Agent`
matcher, dispatched on `hook_event_name` exactly as `hooks/posttooluse_mutation_observer.py`
already does for its own two legs (one file, two attachment points, PreToolUse touches/journals
dispatch, PostToolUse journals the return) -- the module BASENAME staying "pretooluse_..." even
though it now also handles PostToolUse mirrors that same sibling file's own precedent (its own
basename is "posttooluse_..." despite ALSO handling a PreToolUse leg): this project's convention
is to name a dual-leg observer file for whichever leg it was first built for, not to rename on
extension. THE EXISTING DISPATCH LINE'S SHAPE IS UNCHANGED (module docstring's own "TWO THINGS,
EVERY DISPATCH" section, byte-identical) -- the return leg is a strictly ADDITIVE new line kind,
appended to the SAME journal file, never a rewrite of an existing line.

CORRELATION FIELD -- IDENTITY, NOT DERIVATION (2026-07-14 rebuild; ledger row 582, the pairing-
key review commissioned off design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md sec-3/sec-4/sec-6.6, the
sibling item to that RCA's Bash dispatch/completion fix). This file used to claim, verbatim, the
SAME false premise `hooks/stamp_intercept.py`'s own module docstring stated for Bash --
"Claude Code's hook-input contract has never been observed to carry a `tool_use_id` this project
could rely on" -- and FIFO-paired dispatch/return lines by `session_id` + a recomputed `prompt`
sha256 instead. That premise was checked, not assumed, and found false: a captured real
PreToolUse+PostToolUse payload pair for the `Agent` tool (`seen-red/delegation-observer/
agent_payload_capture/`, `check_contract.py`) shows `tool_use_id` present and BYTE-IDENTICAL
across both legs of one Task/Agent dispatch, exactly as the RCA sec-3 witnessed for Bash (that
RCA's own §7 item 2 named this specific leg -- Task/Agent's PostToolUse payload -- UNWITNESSED;
this capture settles it). PostToolUse also carries `duration_ms` directly, computed by the
harness itself, no local subtraction needed.

So this leg is now identity-keyed, not derived: the dispatch line and the return line each carry
the SAME `tool_use_id` (read defensively from the payload, `data.get("tool_use_id")`, the same
posture `hooks/stamp_intercept.py` already uses for Bash). Neither leg computes a "does this
pair with that" verdict -- there is no `_pair_return`, no FIFO, no stored `pairing`/`dispatch_ts`
field. A false pairing record is unrepresentable: each journal line states only facts local to
its own event (`tool_use_id`, and for the return leg, `duration_ms` copied straight from the
payload when present). Pairing two lines into "one dispatch, one return" is a READ-TIME JOIN on
`tool_use_id`, left to whichever consumer wants it (today: nobody -- `engine/contemp_edb.py`'s
E4 family reads `ts`/`kind` only and never touched `pairing`, so this rebuild changes no
consumer). When a payload carries no `tool_use_id` (an honest possibility this hook still
degrades to, never guessed): the line journals without that key, and there is nothing to join
it against -- the SAME per-line honesty the old FIFO fallback offered, without the concurrency
residual gap FIFO-by-content-match named (two dispatches sharing byte-identical prompt text in
the same session no longer collide: the harness's own per-call identity individuates them, not a
recomputed hash of shared content).

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


def _handle_return(data: dict, tool: str) -> int:
    """THE RETURN LEG (module docstring, CORRELATION FIELD). Journals one `kind: "return"` line
    per Task/Agent PostToolUse event, carrying facts local to THIS event only -- `tool_use_id`
    (when the payload has one) and `duration_ms` (copied straight from the payload when present,
    the harness's own computed figure, never re-derived here). No read of the dispatch journal,
    no pairing attempt, no stored verdict: pairing is a read-time join on `tool_use_id` left to
    whichever consumer wants it. Never raises -- a malformed/missing field degrades to that key's
    honest absence, not a broken tool call."""
    session_id = str(data.get("session_id") or "")
    tool_use_id = data.get("tool_use_id")
    duration_ms = data.get("duration_ms")
    now = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    rec: dict = {"ts": now, "session_id": session_id, "tool": tool, "kind": "return"}
    if tool_use_id:
        rec["tool_use_id"] = str(tool_use_id)
    if isinstance(duration_ms, (int, float)):
        rec["duration_ms"] = int(duration_ms)
    _journal(rec)
    return 0


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

    # DISPATCH on hook_event_name (module docstring, THE RETURN LEG) -- this file now attaches
    # to BOTH PreToolUse (the original dispatch leg, unchanged below) and PostToolUse (the new
    # return leg), mirroring hooks/posttooluse_mutation_observer.py's own two-leg-one-file shape.
    # Missing/unrecognized hook_event_name defaults to the ORIGINAL PreToolUse behavior (byte-
    # held prior behavior for any caller that never sent the field at all).
    event = _first(data, "hook_event_name", "hookEventName", default="PreToolUse")
    if event == "PostToolUse":
        try:
            return _handle_return(data, tool)
        except Exception:  # noqa: BLE001 -- an observer must never break a tool call
            return 0
    if event != "PreToolUse":
        return 0

    inp = _first(data, "tool_input", "toolInput", "input", default={})
    if not isinstance(inp, dict):
        inp = {}
    description = str(inp.get("description", ""))
    prompt = str(inp.get("prompt", ""))
    session_id = str(data.get("session_id") or "")
    prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    tool_use_id = data.get("tool_use_id")

    # 1. JOURNAL every dispatch, unconditionally (module docstring) -- before any DB work, so a
    # DB hiccup below never costs the journal record. `tool_use_id` (read defensively, same
    # posture as hooks/stamp_intercept.py) is the identity the return leg now keys on (module
    # docstring, CORRELATION FIELD) -- `prompt_sha256`/`prompt_excerpt` remain, as event facts
    # for a human/consumer to recognize the dispatch by, no longer as a correlation key.
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "session_id": session_id,
        "tool": tool,
        "description": description,
        "prompt_sha256": prompt_sha256,
        "prompt_excerpt": prompt[:200],
    }
    if tool_use_id:
        rec["tool_use_id"] = str(tool_use_id)
    _journal(rec)

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
