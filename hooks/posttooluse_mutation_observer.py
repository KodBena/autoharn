#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-10T20:50:18Z
#   last-change: 2026-07-12T12:45:40Z
#   contributors: be693afb/main, e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""hooks/posttooluse_mutation_observer.py -- the bash-mutation OBSERVER (Part 2, maintainer
mandate 2026-07-10; closes the epistemic half of a gap the hooks agent flagged:
hooks/pretooluse_change_gate.py's `bash_mutates_governed()` is a command-SHAPE enumeration --
`>`/`sed -i`/`tee`/`patch`/`git checkout --`/`git apply`/`open(...,'w')` -- and any enumeration is
a finite list chasing an infinite command-shape space (ADR-0011 Rule 4: enumeration fails open).
A `python3 -c "open('x.py','w').write(...)"`, a `perl`/`ruby`/`node` one-liner, or any other
descendant process that writes bytes without ever spelling a recognized shell redirection evades
that matcher completely -- and PREDICTING every command shape that COULD mutate a file is
unfixable in principle for the same reason matcherless stamping (hooks/stamp_intercept.py)
retired its own shape-matcher for the psql-stamping problem: PreToolUse only ever sees command
TEXT, never what a shell/interpreter will actually do once it runs. So this hook does not try to
predict; it DETECTS, after the fact, by watching the filesystem itself change.

TWO LEGS, ONE FILE, dispatched on `hook_event_name`:
  PreToolUse(Bash)  -- touches ONE marker file under this world's `.claude/` (an mtime bump via
                       `Path.touch()`) recording the instant just before the command runs.
  PostToolUse(Bash) -- runs `find SUBJECT_ROOT -newer <marker> -type f` (EXCLUSIONS below) and,
                       for every file that changed during the just-finished command, checks this
                       world's ledger for an open+claimed work item -- reusing the EXACT
                       has_work_item_layer()/has_open_claimed_work_item() query shape
                       hooks/pretooluse_change_gate.py's permit-to-work check already established
                       (re-derived here, not imported -- see WHY A SEPARATE RESOLUTION below). If
                       mutated files exist and the ledger carries the work-item layer (s22) but
                       shows no live open+claimed item, this hook journals a line and injects a
                       loud, non-blocking `additionalContext` warning naming the mutated files,
                       the command that just ran, and the `./led work open`/`./led work claim`
                       teach-text. If a live permit exists, it is silent -- exactly like
                       permit-to-work's own allow.

OBSERVER ONLY, BY CONSTRUCTION -- NOT A DEGRADED ENFORCE MODE (named honestly, not a euphemism):
PostToolUse fires AFTER the command has already completed; the mutation has already happened by
the time this leg runs. There is no shape of "deny" available here at all. `mode: "enforce"` is
therefore not merely unimplemented-this-pass (the posture a few other queued mechanisms carry) --
it is IMPOSSIBLE for this attachment point, full stop. If apparatus.json ever names
`mode: "enforce"` for `mutation_observer`, this hook warns loudly on stderr and behaves as
`"observe"` (see `_resolve_mode` below) rather than either silently doing nothing or pretending to
an enforcement surface that cannot exist here.

APPARATUS.JSON SWITCHBOARD (maintainer mandate, 2026-07-10): `mechanisms.mutation_observer.mode`
at `<SUBJECT_ROOT>/.claude/apparatus.json`, read once per invocation inside `_configure()`, only
when WIRED (an unwired session has no SUBJECT_ROOT to look under, exactly like every sibling hook
in this project). `"off"` -- both legs return 0 immediately: the marker is never touched and no
`find`/DB query ever runs, i.e. genuinely zero cost, not merely zero warnings. `"observe"` --
this mechanism's only real behavior (see above); the default (rule c: `"observe"`, NOT
`"enforce"`, because enforce is impossible here -- the DEFAULTS rule "free mechanisms default to
enforce" does not apply verbatim to a mechanism with no enforce state to default to). An
unrecognized mode string never widens permissions (rule d) -- falls back to `"observe"` with a
loud stderr warning naming the bad value.

NAMED RESIDUES (v1, stated honestly rather than left for a future reader to discover):
  - DELETIONS are invisible to `find -newer` (a removed file is not "a file that changed", it is
    gone) -- a bash command that deletes a governed file with no open work item produces NO
    warning here. Filed, not fixed, in this pass.
  - MTIME-PRESERVING WRITES (`touch -r`, `cp --preserve=timestamps`, or any tool that explicitly
    restores an old mtime after writing) defeat the `-newer` comparison this hook's whole
    detection rests on. Filed, not fixed.
  - ONE SHARED MARKER PER WORLD, not one per Bash invocation: two Bash tool calls overlapping in
    real time (e.g. two subagents concurrently running Bash in the same session) could see each
    other's mutations cross-attributed to the wrong command's PostToolUse leg. Not observed in
    any single-agent-at-a-time session this project has run so far; named here so a future
    concurrent-subagent user does not discover it the hard way.

EXCLUSIONS (module docstring's own honest scope, not silent): `.claude/logs/` (every hook's own
journal churn), a short list of named hook STATE files (`change_gate_state.json`,
`stop_clean_exit_state.json`, this hook's own marker file), and `.git/` (internal churn, no
subject-authored content) are excluded from the mutated-file report -- everything ELSE under
`.claude/` (`governed_files.json`, `apparatus.json`, `secrets/`, `HOOKS.md`, ...) is real project
surface and IS observed: a bash command weakening `governed_files.json` with no open work item is
exactly the kind of hazard this observer exists to catch, not a bookkeeping file to exempt.

WHY A SEPARATE RESOLUTION, NOT A SHARED IMPORT of hooks/pretooluse_change_gate.py's or
hooks/stop_clean_exit.py's near-identical config/query helpers: the same "no load-bearing coupling
across independently-touched hook files" posture hooks/stop_clean_exit.py's own docstring already
states -- re-derived here, byte-similar, on purpose.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below is imported at module load.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

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
MARKER = ""
JOURNAL = ""
WIRED = False
MODE = "observe"

FS = "\x1f"
RS = "\x1e"
_VALID_MODES = ("off", "observe", "enforce")

_MARKER_BASENAME = "mutation_observer_marker"
_EXCLUDED_RELDIRS = (".claude/logs/", ".git/")
_EXCLUDED_BASENAMES = {
    "change_gate_state.json", "stop_clean_exit_state.json", _MARKER_BASENAME,
    # hooks/posttooluse_apparatus_flip.py's own control-plane state (tracker item
    # `apparatus-flip-witnessing`, 2026-07-12): a Bash-driven apparatus.json edit already touches
    # this file within the same command (that hook's own baseline rewrite), which would otherwise
    # show up here as a second, confusing "mutated file" alongside the real one on every such edit
    # -- excluded for the same reason the two state files above are, not a new exemption class.
    "apparatus_flip_state.json",
}


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
    """apparatus["mechanisms"]["mutation_observer"]["mode"], defaulted/validated per the
    maintainer's 2026-07-10 switchboard mandate. Default is `"observe"` (module docstring:
    `"enforce"` is impossible for a PostToolUse observation, so there is no stricter state to
    default to). `"enforce"` in config is a NAMED-IMPOSSIBLE case, not an ordinary unrecognized
    value -- warned and downgraded to `"observe"` explicitly."""
    default = "observe"
    mechs = apparatus.get("mechanisms")
    entry = mechs.get("mutation_observer") if isinstance(mechs, dict) else None
    raw = entry.get("mode") if isinstance(entry, dict) else None
    if raw is None:
        return default
    if raw == "enforce":
        print("[apparatus] WARNING: mechanisms.mutation_observer.mode='enforce' is IMPOSSIBLE "
              "for this hook (PostToolUse fires after the mutation already happened -- there is "
              "no 'deny' available); behaving as 'observe'. See hooks/"
              "posttooluse_mutation_observer.py module docstring.", file=sys.stderr)
        return "observe"
    if raw in _VALID_MODES:
        return raw
    print(f"[apparatus] WARNING: mechanisms.mutation_observer.mode={raw!r} in "
          f"{root}/.claude/apparatus.json is unrecognized (must be one of {_VALID_MODES}) -- "
          f"never widening permissions; falling back to {default!r}.", file=sys.stderr)
    return default


def _configure(data: dict) -> None:
    """Resolve every connection/config value for THIS invocation. Called once, at the top of
    `main()`, right after stdin is parsed. Same env-override > deployment.json > byte-held-default
    precedence, and the same WIRED derivation, hooks/stop_clean_exit.py already established."""
    global PGHOST, PGDB, LEDGER, SUBJECT_ROOT, MARKER, JOURNAL, WIRED, MODE
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

    MARKER = os.path.join(SUBJECT_ROOT, ".claude", _MARKER_BASENAME) if WIRED else ""
    JOURNAL = (os.path.join(SUBJECT_ROOT, ".claude", "logs", "mutation_observer.journal.jsonl")
               if WIRED else "")

    apparatus = _load_apparatus_quiet(SUBJECT_ROOT) if WIRED else {}
    MODE = _resolve_mode(apparatus, SUBJECT_ROOT)


def _ledger_schema() -> str:
    return LEDGER.rsplit(".", 1)[0] if "." in LEDGER else "public"


def has_work_item_layer() -> bool:
    """Cheap, lock-free, catalog-only existence probe -- mirrors
    hooks/pretooluse_change_gate.py's identically-named function exactly (the permit-to-work
    query shape this mandate asks to be reused)."""
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


def _touch_marker() -> None:
    if not MARKER:
        return
    try:
        os.makedirs(os.path.dirname(MARKER), exist_ok=True)
        Path(MARKER).touch(exist_ok=True)
    except OSError:
        pass  # never break the tool call over a marker-file hiccup


def _excluded(relpath: str) -> bool:
    if any(relpath.startswith(d) for d in _EXCLUDED_RELDIRS):
        return True
    return os.path.basename(relpath) in _EXCLUDED_BASENAMES


def mutated_files() -> list[str]:
    """Every regular file under SUBJECT_ROOT strictly newer than MARKER, EXCLUSIONS applied,
    relative-path-sorted. Returns [] (never raises) on any error -- an observer must never break
    a tool call over a `find` hiccup."""
    if not MARKER or not os.path.isfile(MARKER):
        return []
    try:
        cp = subprocess.run(["find", SUBJECT_ROOT, "-newer", MARKER, "-type", "f"],
                             capture_output=True, text=True, timeout=15, check=True)
    except Exception:  # noqa: BLE001
        return []
    out = []
    for line in cp.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        rel = os.path.relpath(line, SUBJECT_ROOT)
        if not _excluded(rel):
            out.append(rel)
    return sorted(out)


def _journal(rec: dict) -> None:
    if not JOURNAL:
        return
    try:
        os.makedirs(os.path.dirname(JOURNAL), exist_ok=True)
        with open(JOURNAL, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


DENY_HINT = "./led work open <slug> \"<title>\"\n  ./led work claim <slug>"


def _emit_warning(files: list[str], command: str) -> None:
    file_list = "\n".join(f"  - {f}" for f in files)
    warning = (
        "[mutation-observer WARNING, observer-mode -- never blocks] the bash command below "
        "mutated file(s) in this world with NO open+claimed work item in the ledger "
        "(permit-to-work's own check, run here AFTER the fact since a PostToolUse observation "
        "cannot deny -- hooks/posttooluse_mutation_observer.py):\n"
        f"command: {command}\n"
        f"mutated file(s):\n{file_list}\n"
        f"open + claim a work item to cover this work:\n  {DENY_HINT}"
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

    if not WIRED or MODE == "off":
        return 0

    tool = _first(data, "tool_name", "toolName", "name", default="")
    if tool != "Bash":
        return 0

    event = _first(data, "hook_event_name", "hookEventName", default="")
    if event == "PreToolUse":
        _touch_marker()
        return 0
    if event != "PostToolUse":
        return 0

    command = str((data.get("tool_input") or {}).get("command", ""))
    try:
        files = mutated_files()
        if not files:
            return 0
        # NAMED CHOICE, pre-s22 world (mirrors hooks/pretooluse_change_gate.py's permit-to-work
        # posture): no work-item layer to compare against -- nothing to observe, not an error.
        if not has_work_item_layer():
            return 0
        if has_open_claimed_work_item():
            return 0  # a live permit exists -- silent, exactly like permit-to-work's own allow
        _journal({"ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z",
                  "outcome": "unpermitted_mutation", "command": command[:400], "files": files})
        _emit_warning(files, command[:200])
    except Exception:  # noqa: BLE001 -- an observer must never crash a tool call over a DB hiccup
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
