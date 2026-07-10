#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T08:07:02Z
#   last-change: 2026-07-10T20:51:48Z
#   contributors: 9bcc0113/main, be693afb/main
# <<< PROVENANCE-STAMP <<<

"""PreToolUse change-policy gate (e13 / s13) — the act-gate, fully label-indifferent.

DELTA FROM THE e11/e12 GATE (F45, consult 17 §6 item 5 — the event-61 repair): ticket matching is
re-keyed from "the basename appears ANYWHERE in the entry text" to "the basename is DECLARED by the
ticket" — a declared `files:` list, plus free-text naming with COMMAND SPANS excluded. e12's gate
event 61 unlocked a ruling-work edit to tests/test_milestone_b.py under an UNRELATED stale
verification row (#24) whose only tie to the file was that its evidence QUOTED the command `pytest
tests/test_milestone_b.py` — a file named as a command ARGUMENT is not a declaration to CHANGE it.
The honest ticket (#31) existed but omitted the file from its `files:` list, so the gate fell back
to the coincidental command-quote. The repair (type-driven, ADR-0000): the match surface is the
ticket's DECLARATION of intent (the `files:` convention made structural, plus prose naming with
command spans stripped), so a coincidental command-quote can no longer authorize a change. This is
NOT a label-priced mechanism (F26): the declaration is a file list, never the subject's kind/concern.
Two further consult-17 item-5 clauses live in the instruments, not here: the long-lag fresh-unlock
flag (a new `long_lag_unlock` ticket_flag below) and the no-antecedent unreachable-by-debt report
(stale_enactment_debt). Everything else is the e11 gate verbatim, re-pointed at s14.ledger.

Byte-held from the e10 build EXCEPT the disclosed apparatus repairs above and the F33 invariant
re-key (below).

Byte-held from the e10 build EXCEPT one disclosed apparatus repair: the governed set is
re-keyed to the INVARIANT (consult 13 §5.3 / F33). e8–e10 hardcoded a package name the
FIRST subject happened to choose (`substrate/`), so the e10 subject's differently-named
engine (`nlafs/`, plus the top-level driver) produced ZERO gate events — 15 of 20 files, 21
of 32 mutation events, silently ungoverned under a green apparatus (the instance-keyed
governance defect, F33). The fix keys governance to WHAT THE THING IS, not what a subject
named it: every `*.py` file under the subject repo is governed. No package-name choice can
exit governance; drivers and tests are included by construction. This is not a lever — it is
the wholesale repair of a critical bypass, disclosed and probe-decided (F13/F14 precedent),
subject-visible only as the same gate footprint the standing mechanism already had.

Everything else is the e10 gate verbatim (consult 12 §1): §4.4 demoted to flag-and-journal
(keying is filename + currency ONLY, kind/concern-agnostic; every §4.4-class phenomenon
ALLOWs and is journaled as `ticket_flags`), BOUNDARY_RE quote-strip (a `pytest`/`commit`
token inside a SQL string literal is DATA, not a boundary), and the single deny kind
(needs_entry) whose message names only the file. The three deltas from e9 are unchanged:

  1. §4.4 DEMOTED from deny to flag-and-journal. Keying is filename + currency ONLY —
     kind- and concern-agnostic, positive OR negative. Every ALLOW journal record carries
     `ticket_flags` — computed telemetry, invisible to the subject, consumed by the
     review-queue instrument (measured, not prevented — a deny corrupts the label, F26).

     ticket_flags classes (consult 11 §4.5 / §7.1):
       - enactment_no_enacts    : concern='enactment' with enacts NULL/{} (honest-empty).
       - enacts_nondesign_target: some enacts element points at a non-`decision`-kind row.
       - enacts_stale_antecedent: some enacts element points at a row superseded as of the
                                  entry's ts (the first true stale-linkback datum if it fires).
       - window_redundant_entry : the unlocking entry was logged within WINDOW_S of the file's
                                  prior ticket while that window was still (nominally) open.

  2. BOUNDARY_RE quote-stripping (§7.2). The boundary scan runs on the command with
     dollar-quoted ($$…$$) and single/double-quoted spans stripped, so a `pytest`/`commit`
     token counts only as a COMMAND token, never as DATA inside a SQL string literal.

  3. Deny message: with §4.4 gone it is the only deny kind again — naming the file IS the
     whole contract. The message names no kind, concern, label, or governed-set vocabulary.

Governed paths: every `*.py` file under the subject repo (invariant-keyed; no package name).

Qualification posture (link 6): for an IDENTIFIED governed mutation the hook fails CLOSED
(deny) on any error — an unlogged change is the thing the target domains exist to prevent.
Unidentifiable input is passed through (the audit hook still records it; a slipped mutation
is recoverable post-hoc via the mtime × statement-log join). Emits both the modern
permissionDecision JSON and a non-zero exit for cross-version reliability.

FAIL-CLOSED ON A DANGLING SUBJECT_ROOT (BACKLOG "Run-2 integrity finding", 2026-07-09): if
GATE_SUBJECT_ROOT (or its deprecated alias E13_SUBJECT_ROOT) is explicitly set but does not
exist on disk — the exact run-2 shape, a moved project directory leaving a stale env var baked
into `.claude/settings.json` — every Write/Edit/NotebookEdit call is DENIED with teach-text
naming the configured path and the settings.json fix, instead of `is_governed()` silently
matching nothing and governing zero files; an unset SUBJECT_ROOT (unwired sessions) or one that
resolves to a real directory is completely unaffected.

PERMIT-TO-WORK (BACKLOG "Run-5 forensics", 2026-07-10): run 5's forensic pass found the ledger is
a retroactive diary, not a permit log — 8m23s of witnessed work landed as 19 rows in 89.4s, after
the fact, in a session the gate had otherwise governed correctly all along (every ticket it saw was
honest). A ledger ENTRY naming a file is necessary but not sufficient: it proves the file was
declared, never that work on it was authorized to START. The fix composes a SECOND, PRIOR gate in
front of the existing ticket/window logic (which is otherwise untouched): when this gate is WIRED
(SUBJECT_ROOT explicitly configured via env or a located deployment.json, and resolving to a real
directory — see `SUBJECT_ROOT_WIRED`) AND this world's ledger schema carries the s22 work-item
layer (the `work_item_current` view exists — see `has_work_item_layer()`), a Write/Edit/NotebookEdit
under SUBJECT_ROOT is DENIED unless `work_item_current` shows at least one row with state='open'
AND a non-NULL claimant (`has_open_claimed_work_item()`) — with teach-text naming the exact
`./led work open`/`./led work claim` commands. This is deliberately ORTHOGONAL to the ticket/window
mechanism: even a currently-open consumption WINDOW (a reused ticket) still requires a live
open+claimed work item, since permit-to-work sits IN FRONT of that reuse check, not behind it.
The SAME check is also consulted in the Bash branch's already-denied bash-mutation-into-governed-
file class below (`bash_mutates_governed()`) — PRECISELY stated, that class denies unconditionally
either way (byte-held), so consulting the check there changes only WHICH teach-text is shown
(the more actionable permit-to-work message when it applies), never whether the call is allowed;
it is not a second enforcement point, only a better-informed message on an existing one.

NAMED CHOICE — pre-s22 fail-OPEN (deliberate, not an oversight): a world whose ledger schema does
NOT carry `work_item_current` (any pre-s22 world) SKIPS this check entirely and keeps EXACTLY
today's ticket-only behavior. `to_regclass` reporting "no such view" is not an error — only a
genuine DB-unreachable failure fails closed (propagated into the existing fail-closed except
below, same posture as every other check here). This keeps older, already-deployed worlds working
unchanged; it does not retroactively demand a work-item layer they were never given.

APPARATUS.JSON MECHANISM SWITCHBOARD (maintainer mandate, 2026-07-10 — "the configuration layer"):
this file implements TWO separately-switchable mechanisms out of the project's six —
`change_gate` (the SUBJECT_ROOT-integrity check plus the ticket/window logic, everything above
this note) and `permit_to_work` (the s22 open+claimed-work-item check, immediately above) — each
reads its OWN mode from `<SUBJECT_ROOT>/.claude/apparatus.json`'s `mechanisms.<name>.mode`, once
per invocation, inside `_configure()`. Three modes, binding for every mechanism project-wide
(rule a): `"off"` — the mechanism's own deny paths are skipped entirely, no journal, no state
touched, exactly as if that code did not exist; `"observe"` — the SAME checks run (so the ticket/
work-item logic is exercised and its state is kept current), but a would-have-denied outcome is
turned into an ALLOW carrying a loud `additionalContext` warning plus a journal record, never a
block; `"enforce"` — byte-identical to this file's behavior before this pass. Missing file/key
(rule b) resolves to the mechanism's OWN stated default — `"enforce"` for BOTH `change_gate` and
`permit_to_work` (rule c: both are free — no per-invocation spend — so they default to their
current strength, unchanged for every world that predates this pass and never edits
apparatus.json). An unrecognized mode string (rule d) NEVER widens permissions: since `"enforce"`
is already the strictest state either mechanism has, falling back to the mechanism's own default
IS falling back to the strictest available option for both of these — `_resolve_mode()` below
prints a loud stderr warning naming the exact bad value and the file it came from, then uses that
default. NOTE the load-bearing asymmetry: `change_gate` being `"off"` does NOT turn
`permit_to_work` off too — they are independent switches (a world could disable ticket-checking
while still requiring an open work item, or vice versa); the one thing `change_gate=off` DOES
still leave standing is `is_governed()` itself (which mechanism/pattern a path matches is shared
infrastructure both mechanisms consult, never itself a mode-gated decision — see the code below
for exactly where each mode is read).
"""
import fnmatch
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

# Eager, top-of-file sys.path insert + import (lazy imports banned; the same pattern
# engine/targets.py and hooks/stamp_intercept.py already use to reach a sibling module):
# filing/deployment_record.py is the ONE home for the deployment.json shape (ADR-0012 P1), reached
# via a file-relative sys.path insert since this hook lives in the SAME autoharn checkout as filing/.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)  # hooks/ -> autoharn root
sys.path.insert(0, os.path.join(_REPO_ROOT, "filing"))
import deployment_record  # noqa: E402  (filing/deployment_record.py, the ONE home for the deployment.json shape)

# ---------------------------------------------------------------------------------------------
# CONNECTION/CONFIG RESOLUTION (design/OPUS-READINESS.md move 1; BACKLOG "PGHOST hardcoded" +
# "E13 retirement", both 2026-07-09) — two defects fixed together because they share one root
# cause: a connection/config value with no live per-project source, so it either had no override
# at all, or an override vocabulary tied to one dead experiment's name.
#   (1) PGHOST used to be a bare literal with NO env override — every sibling parameter
#       (E13_GATE_DB, E13_GATE_LEDGER, ...) was already os.environ.get(...)-overridable; PGHOST
#       alone was not. A scaffolded instance whose postgres lives on a different host would have
#       had this gate silently querying the WRONG HOST — the exact "silent wrong database" class
#       engine/targets.py's own docstring names and forecloses for itself, one hop over.
#   (2) The E13_GATE_*/E13_SUBJECT_ROOT env-var family carries a dead experiment's name (e13) as
#       its whole vocabulary and has no relationship to a project's own deployment.json (the ONE
#       home for db/host/schema/kern/role, filing/deployment_record.py) — a scaffolded project
#       had to re-author these names a second time in its own settings.json, the exact
#       N-places-re-authored friction OPUS-READINESS move 1 names.
#
# THE FIX: this hook is a fresh short-lived process per tool call with no persistent config of
# its own; its only per-call context is the hook-input JSON on stdin, which Claude Code populates
# with `cwd` (the session's working directory when the tool call fired — the same field
# hooks/stamp_provenance.py and hooks/stamp_intercept.py already read). That locates a project's
# deployment.json (repo root, next to .claude/) with zero new plumbing a project's settings.json
# would otherwise have to carry. PRECEDENCE per value, stated once: an env var (neutral name, or
# its deprecated alias) OVERRIDES the deployment record; the deployment record is used when no
# env var is set; the byte-held hardcoded default is used when NEITHER resolves — so autoharn's
# own long-lived gate usage against `nla` (no deployment.json anywhere in that flow) is completely
# unaffected. Neutral names replace the dead e13-prefixed family (OPUS-READINESS: "the E13_*
# experiment prefix dies"); LEDGER_DB/LEDGER_HOST mirror engine/targets.py's own
# LEDGER_DB/LEDGER_SCHEMA/LEDGER_KERN env-var convention (ADR-0012 P1 — one vocabulary, not
# reinvented). The old E13_*/STAMP_* names are kept working as deprecated aliases (accepted
# silently, nothing logged) so no existing deployment breaks mid-transition.
#
#   value        | neutral env       | deprecated alias   | deployment.json field (when no env set)
#   PGHOST       | LEDGER_HOST       | E13_GATE_HOST       | host
#   PGDB         | LEDGER_DB         | E13_GATE_DB          | db
#   LEDGER       | GATE_LEDGER       | E13_GATE_LEDGER      | f"{schema}.ledger"
#   SUBJECT_ROOT | GATE_SUBJECT_ROOT | E13_SUBJECT_ROOT     | the deployment.json's own directory
#   STATE        | GATE_STATE        | E13_GATE_STATE       | f"{SUBJECT_ROOT}/.claude/change_gate_state.json"
#   JOURNAL      | GATE_JOURNAL      | E13_GATE_JOURNAL     | f"{SUBJECT_ROOT}/.claude/logs/change_gate.journal.jsonl"
#
# (STATE/JOURNAL's deployment-relative defaults only apply when a deployment record was actually
# found — else they fall back to the byte-held absolute epistemic-audit paths, exactly as before
# this pass, so autoharn's own e13/e14 flow — whose state/journal never lived under SUBJECT_ROOT —
# is unaffected.)
#
# Config is resolved once per invocation, inside `_configure()`, called at the top of `main()`
# right after stdin is parsed — the deployment.json lookup needs the hook input's own `cwd`, only
# available once stdin has been read. This is still "once per call" (a fresh short-lived process
# per tool call, per the GOVERNED-SET CONFIG comment below): only WHEN the resolution happens
# moved, not how often, so there is no new P4 staleness.
# ---------------------------------------------------------------------------------------------
_DEFAULT_PGHOST = "192.168.122.1"
_DEFAULT_PGDB = "nla"
_DEFAULT_LEDGER = "public.ledger"
_DEFAULT_SUBJECT_ROOT = os.path.expanduser("~/w/vdc/1/epistemic-e14")
_DEFAULT_STATE = os.path.expanduser("~/w/vdc/1/epistemic-audit/change_gate_state.json")
_DEFAULT_JOURNAL = os.path.expanduser("~/w/vdc/1/epistemic-audit/logs/change_gate.journal.jsonl")

# Module globals every function below reads as plain globals, populated by `_configure()` at the
# start of every `main()` call. Declared here at their byte-held defaults so the module still
# imports cleanly (e.g. under a test harness that imports functions directly without calling
# `main()`/`_configure()` first) — only WHEN they are computed moved by this pass, not their names.
PGHOST = _DEFAULT_PGHOST
PGDB = _DEFAULT_PGDB
LEDGER = _DEFAULT_LEDGER
SUBJECT_ROOT = _DEFAULT_SUBJECT_ROOT
STATE = _DEFAULT_STATE
JOURNAL = _DEFAULT_JOURNAL
# True iff GATE_SUBJECT_ROOT (or its deprecated alias E13_SUBJECT_ROOT) was EXPLICITLY set for
# this invocation and the resolved SUBJECT_ROOT does not exist on disk (run-2 integrity finding,
# BACKLOG 2026-07-09: a moved project directory left a stale absolute path baked into
# `.claude/settings.json`, so `is_governed()` matched no real file and silently governed nothing
# for the session's entire life). Set by `_configure()`; deliberately false when SUBJECT_ROOT was
# never configured via env at all (an unwired session stays untouched) or resolves to a real dir.
SUBJECT_ROOT_MISCONFIGURED = False
# True iff this invocation's SUBJECT_ROOT is "configured" (an explicit GATE_SUBJECT_ROOT/
# E13_SUBJECT_ROOT env var, OR a located+loaded deployment.json) AND resolves to a real directory
# (permit-to-work, BACKLOG "Run-5 forensics", 2026-07-10). Deliberately the disjunction of BOTH
# wiring paths — unlike SUBJECT_ROOT_MISCONFIGURED above (which only ever fires for the explicit-
# env-var shape, since a not-yet-existing deployment-derived root is a different, normal state) —
# because permit-to-work must also apply to a scaffolded project driven purely by deployment.json,
# not only one pinned via env var. Set by `_configure()`; false for autoharn's own bare hardcoded-
# default usage (no deployment.json, no env override) so that flow is completely unaffected.
SUBJECT_ROOT_WIRED = False
EPOCH = "1970-01-01 00:00:00"
WINDOW_S = 600.0  # a ticket, once consumed, stays open on its file for this long …
# … or until the next test-run / commit boundary, whichever comes first.
LONG_LAG_S = 3600.0  # a FRESH unlock whose ticket is older than this is flagged long_lag_unlock
# (F45 / consult 17 item 5): event 61 unlocked at lag_pre 4880s under a stale verification row.
# Measured-not-prevented (a flag, never a deny — the lag may be legitimate; F26).

# Field / record separators for psql -tA output: ASCII US / RS. Chosen so entry text
# containing tabs or newlines (multi-line statements) cannot corrupt row parsing.
FS = "\x1f"
RS = "\x1e"

# Project-specific, concrete "what to run" appended to every deny message (fix-point ergonomics,
# maintainer requirement 2026-07-09): the gate's own refusal is the loop's only feedback channel,
# so it must name the exact next command, not just the policy. Empty by default (byte-held
# behavior for existing deployments); a project's settings.json sets DENY_HINT to its own
# ledger-insert one-liner (see toy-project's `led` helper).
DENY_HINT = os.environ.get("DENY_HINT", "")

DENY_NEEDS_ENTRY = (
    "Ledger policy: a change to a source file must be preceded by a ledger entry naming the "
    "file it changes. Insert the entry (one INSERT, as usual), then RE-ISSUE THE SAME EDIT — "
    "the gate re-checks on every attempt, so retrying after the insert is the whole fix."
    + (f"\n{DENY_HINT}" if DENY_HINT else "")
)
DENY_BASH_WRITE = (
    "Ledger policy: source files are modified via the Write/Edit tools, so each change is tied "
    "to its ledger entry — shell writes into these files are disabled."
    + (f"\n{DENY_HINT}" if DENY_HINT else "")
)
DENY_NO_OPEN_WORK_ITEM = (
    "Ledger policy (s22 permit-to-work): this world's ledger carries the work-item layer and no "
    "work item is currently OPEN and CLAIMED — a ledger entry written after the fact is not a "
    "permit to work (BACKLOG 'Run-5 forensics', 2026-07-10: 8m23s of witnessed work landed as 19 "
    "ledger rows 89.4s later — honest, but late). Open and claim a work item, THEN retry the "
    "same edit:\n"
    "  ./led work open <slug> \"<title>\"\n"
    "  ./led work claim <slug>"
    + (f"\n{DENY_HINT}" if DENY_HINT else "")
)


def _deny_subject_root_missing() -> str:
    """Teach-text for the run-2 integrity finding (BACKLOG 2026-07-09): SUBJECT_ROOT was
    explicitly configured but does not resolve to a real directory, so this gate cannot tell
    which files it governs. Built as a function (not a module-level constant) because it must
    report THIS invocation's resolved SUBJECT_ROOT, computed by `_configure()` from the hook
    input's own `cwd` — not a value known at import time."""
    return (
        f"Ledger policy: SUBJECT_ROOT is configured as '{SUBJECT_ROOT}' but that path does not "
        "exist on disk, so this gate cannot determine which files it governs — refusing rather "
        "than silently governing nothing (the run-2 integrity finding: a moved project directory "
        "left a stale absolute path baked into a hook command). Fix: repoint .claude/settings.json's "
        "GATE_SUBJECT_ROOT (or its deprecated alias E13_SUBJECT_ROOT) at the real project root, "
        "then retry."
        + (f"\n{DENY_HINT}" if DENY_HINT else "")
    )

# GOVERNED-SET CONFIG (maintainer ruling, 2026-07-09): which files this gate protects is a
# per-project, trivially-editable choice — a small config file the PROJECT'S USER selects
# patterns in, never a set hardcoded here. Resolved once per invocation, inside `_configure()`
# (this process is a fresh short-lived hook invocation per tool call, so "once per call" is the
# relevant unit — no P4 staleness; only WHEN this is computed moved with this pass, from import
# time to inside main(), because its default now depends on SUBJECT_ROOT which itself can depend
# on the hook input's `cwd`). Format: {"patterns": ["*.py", ...]}, fnmatch'd against the path
# relative to SUBJECT_ROOT (fnmatch's "*" matches "/" too, so "*.py" alone reaches nested files —
# no "**" needed). Missing/unreadable/malformed config -> the F33 invariant default: every *.py
# file, class-keyed, exactly the old hardcoded behavior, so a project that has not yet configured
# governance is not silently ungoverned.
GOVERNED_CONFIG = os.path.join(SUBJECT_ROOT, ".claude", "governed_files.json")
_DEFAULT_GOVERNED_PATTERNS = ["*.py"]


def _load_governed_patterns(cfg_path: str) -> list[str]:
    try:
        with open(cfg_path, encoding="utf-8") as f:
            cfg = json.load(f)
        patterns = cfg.get("patterns")
        if isinstance(patterns, list) and patterns and all(isinstance(p, str) for p in patterns):
            return patterns
    except Exception:
        pass
    return _DEFAULT_GOVERNED_PATTERNS


GOVERNED_PATTERNS = _load_governed_patterns(GOVERNED_CONFIG)

# APPARATUS.JSON MECHANISM SWITCHBOARD (module docstring, maintainer mandate 2026-07-10). Two
# mechanisms live in this file; each gets its own module-global mode, resolved once per invocation
# inside `_configure()` (same "fresh short-lived process, resolve once" posture as every other
# config value here).
_VALID_MODES = ("off", "observe", "enforce")
CHANGE_GATE_MODE = "enforce"
PERMIT_TO_WORK_MODE = "enforce"


def _load_apparatus_quiet(root: str) -> dict:
    """Best-effort apparatus.json load for THIS invocation's SUBJECT_ROOT. Missing file, unreadable
    bytes, invalid JSON, or a non-object JSON value all degrade to {} (rule b: every mechanism
    reader below then falls to ITS OWN stated default) -- never an error, mirroring
    `_load_governed_patterns`'s identical missing-file posture."""
    if not root:
        return {}
    path = os.path.join(root, ".claude", "apparatus.json")
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg if isinstance(cfg, dict) else {}
    except Exception:
        return {}


def _resolve_mode(apparatus: dict, mechanism: str, default: str, root: str) -> str:
    """apparatus["mechanisms"][mechanism]["mode"], defaulted/validated per the maintainer's
    2026-07-10 switchboard mandate: (b) a missing apparatus.json, missing "mechanisms" key, or
    missing per-mechanism entry -> `default` (the CALLER's job to pass this mechanism's own
    stated default -- NOT the same value for every mechanism, see module docstring); (d) an
    unrecognized mode string (anything but off/observe/enforce) must NEVER WIDEN permissions --
    falls back to `default` with a loud stderr warning naming the exact bad value and the file it
    came from, so a typo in apparatus.json is never silently read as a wider grant than intended."""
    mechs = apparatus.get("mechanisms")
    entry = mechs.get(mechanism) if isinstance(mechs, dict) else None
    raw = entry.get("mode") if isinstance(entry, dict) else None
    if raw is None:
        return default
    if raw in _VALID_MODES:
        return raw
    print(f"[apparatus] WARNING: mechanisms.{mechanism}.mode={raw!r} in "
          f"{root}/.claude/apparatus.json is unrecognized (must be one of {_VALID_MODES}) -- "
          f"never widening permissions on a bad config value; falling back to {mechanism}'s own "
          f"default {default!r}.", file=sys.stderr)
    return default


def _find_deployment_path(data: dict) -> str | None:
    """Locate this project's deployment.json: an explicit LEDGER_DEPLOYMENT override first, else
    `<cwd>/deployment.json` using the hook input's own `cwd` field (falling back to this process's
    os.getcwd(), mirroring stamp_provenance.py's/stamp_intercept.py's identical convention).
    Returns None -- never raises -- when neither resolves to an existing file (a missing record
    degrades quietly to the env-var/hardcoded path, same posture as every other config value
    here)."""
    explicit = os.environ.get("LEDGER_DEPLOYMENT", "")
    if explicit:
        return explicit
    cwd = data.get("cwd") or os.getcwd()
    candidate = os.path.join(cwd, "deployment.json")
    return candidate if os.path.isfile(candidate) else None


def _load_deployment_quiet(path: str) -> deployment_record.DeploymentRecord | None:
    """Best-effort deployment.json load. Never raises -- a missing/malformed record degrades to
    the env-var/hardcoded path exactly like any other mis-provisioning this hook tolerates."""
    try:
        return deployment_record.load_deployment(path)
    except deployment_record.DeploymentError:
        return None


def _configure(data: dict) -> None:
    """Resolve every connection/config value for THIS invocation and set the module globals every
    function below reads (see the module-docstring precedence table above: env override >
    deployment.json > byte-held hardcoded default). Called once, at the top of `main()`, right
    after stdin is parsed -- the deployment.json lookup needs the hook input's own `cwd`, which is
    only available once stdin has been read."""
    global PGHOST, PGDB, LEDGER, SUBJECT_ROOT, STATE, JOURNAL, GOVERNED_CONFIG, GOVERNED_PATTERNS
    global SUBJECT_ROOT_MISCONFIGURED, SUBJECT_ROOT_WIRED, CHANGE_GATE_MODE, PERMIT_TO_WORK_MODE
    dep_path = _find_deployment_path(data)
    dep = _load_deployment_quiet(dep_path) if dep_path else None

    PGHOST = (os.environ.get("LEDGER_HOST") or os.environ.get("E13_GATE_HOST")
              or (dep.host if dep else None) or _DEFAULT_PGHOST)
    PGDB = (os.environ.get("LEDGER_DB") or os.environ.get("E13_GATE_DB")
            or (dep.db if dep else None) or _DEFAULT_PGDB)
    LEDGER = (os.environ.get("GATE_LEDGER") or os.environ.get("E13_GATE_LEDGER")
              or (f"{dep.schema}.ledger" if dep else None) or _DEFAULT_LEDGER)

    using_deployment = bool(dep_path and dep)
    default_root = os.path.dirname(dep_path) if using_deployment else _DEFAULT_SUBJECT_ROOT
    env_subject_root = os.environ.get("GATE_SUBJECT_ROOT") or os.environ.get("E13_SUBJECT_ROOT")
    SUBJECT_ROOT = os.path.abspath(env_subject_root or default_root)
    # Run-2 integrity finding (BACKLOG 2026-07-09): SUBJECT_ROOT is "configured" for this check
    # only when an operator explicitly set the env var -- a deployment.json-/hardcoded-derived
    # default that happens not to exist is a DIFFERENT, unwired-session shape this fix must leave
    # alone (see module docstring). An explicit-but-dangling path is the exact defect: a moved
    # project directory leaves a stale absolute path in `.claude/settings.json`.
    SUBJECT_ROOT_MISCONFIGURED = bool(env_subject_root) and not os.path.isdir(SUBJECT_ROOT)
    # Permit-to-work (BACKLOG "Run-5 forensics", 2026-07-10): "wired" is broader than the
    # misconfiguration check above — EITHER wiring path (explicit env var OR a located deployment
    # record) counts, since a scaffolded project driven purely by deployment.json must still get
    # permit-to-work, not only one pinned via an explicit env var.
    SUBJECT_ROOT_WIRED = bool(env_subject_root or using_deployment) and os.path.isdir(SUBJECT_ROOT)
    default_state = (os.path.join(SUBJECT_ROOT, ".claude", "change_gate_state.json")
                      if using_deployment else _DEFAULT_STATE)
    default_journal = (os.path.join(SUBJECT_ROOT, ".claude", "logs", "change_gate.journal.jsonl")
                        if using_deployment else _DEFAULT_JOURNAL)
    STATE = os.environ.get("GATE_STATE") or os.environ.get("E13_GATE_STATE") or default_state
    JOURNAL = os.environ.get("GATE_JOURNAL") or os.environ.get("E13_GATE_JOURNAL") or default_journal

    GOVERNED_CONFIG = os.environ.get(
        "GOVERNED_CONFIG", os.path.join(SUBJECT_ROOT, ".claude", "governed_files.json"))
    GOVERNED_PATTERNS = _load_governed_patterns(GOVERNED_CONFIG)

    apparatus = _load_apparatus_quiet(SUBJECT_ROOT)
    CHANGE_GATE_MODE = _resolve_mode(apparatus, "change_gate", "enforce", SUBJECT_ROOT)
    PERMIT_TO_WORK_MODE = _resolve_mode(apparatus, "permit_to_work", "enforce", SUBJECT_ROOT)


# Governance is CLASS-keyed (F33): match by pattern/nature, never by an enumerated file list.
# Containment in the operator-fixed SUBJECT_ROOT is still absolute — no pattern can govern
# outside it, and no pattern choice can exit governance for a file the config's patterns cover.
def is_governed(path: str) -> bool:
    if not path:
        return False
    ap = os.path.abspath(path)
    if not (ap == SUBJECT_ROOT or ap.startswith(SUBJECT_ROOT + os.sep)):
        return False
    rel = os.path.relpath(ap, SUBJECT_ROOT)
    return any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(os.path.basename(ap), pat)
               for pat in GOVERNED_PATTERNS)


# bash writes INTO a governed path: redirection, sed -i, tee, patch, git checkout/apply, py
# open(w). Keyed on the `.py` nature (F33), not on any package name. Over-matching a `.py` path
# outside the repo only forces the Write/Edit route (safe); a false ALLOW is never produced.
_PY = r"[\w./+-]*\.py\b"
BASH_MUT_RES = [
    re.compile(r">>?\s*\S*" + _PY),                          # > / >> into a .py path
    re.compile(r"\bsed\b[^\n]*-i[^\n]*" + _PY),              # sed -i on a .py
    re.compile(r"\btee\b[^\n]*" + _PY),                      # tee into a .py
    re.compile(r"\bpatch\b[^\n]*" + _PY),                    # patch a .py
    re.compile(r"\bgit\s+checkout\b[^\n]*--[^\n]*" + _PY),   # git checkout -- file.py
    re.compile(r"\bgit\s+apply\b"),                          # git apply (conservative)
    re.compile(r"open\s*\([^)]*" + _PY.replace(r"\b", "") + r"[^)]*['\"]\s*w"),  # open(...'x.py'...,'w')
]
# a test-run or commit closes any open consumption window (repair 2). Scanned on the
# quote-STRIPPED command (repair 3, §7.2) so a token inside a SQL string literal is data, not
# a boundary. Byte-held from e10 (the boundary vocabulary is not part of the F33 re-key).
BOUNDARY_RE = re.compile(
    r"\bpytest\b|python\s+-m\s+pytest|\brun_conformance\b|\bgit\s+commit\b", re.IGNORECASE
)
# dollar-quoted spans ($$…$$ and $tag$…$tag$) and single/double-quoted spans — SQL/shell string
# literals whose contents are DATA, stripped before the boundary scan.
_DOLLARQ_RE = re.compile(r"\$(\w*)\$.*?\$\1\$", re.DOTALL)
_SQUOTE_RE = re.compile(r"'[^']*'", re.DOTALL)
_DQUOTE_RE = re.compile(r'"[^"]*"', re.DOTALL)


def _first(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return default


def bash_mutates_governed(cmd: str) -> bool:
    return any(r.search(cmd) for r in BASH_MUT_RES)


def strip_quoted(cmd: str) -> str:
    """Blank out SQL/shell string-literal spans so the boundary scan sees only command tokens
    (repair 3). Dollar-quotes first (they may contain ' and "), then '…' and "…"."""
    s = _DOLLARQ_RE.sub("  ", cmd)
    s = _SQUOTE_RE.sub("  ", s)
    s = _DQUOTE_RE.sub("  ", s)
    return s


def is_boundary(cmd: str) -> bool:
    return bool(BOUNDARY_RE.search(strip_quoted(cmd)))


def _brace_expand(s: str) -> list[str]:
    """Expand shell-style brace groups: 'a/{x,y}.py' -> ['a/x.py', 'a/y.py'].
    Single- and multi-group, left-to-right; returns [s] when there is no group."""
    m = re.search(r"\{([^{}]*)\}", s)
    if not m:
        return [s]
    pre, opts, post = s[: m.start()], m.group(1).split(","), s[m.end():]
    out = []
    for o in opts:
        for tail in _brace_expand(post):
            out.append(pre + o.strip() + tail)
    return out


# Command tokens that "quote" a file as an ARGUMENT rather than declaring intent to change it
# (F45 / event-61 repair). A basename appearing only inside such a span is NOT a declaration — the
# span (command token to end of line / next shell separator) is blanked before matching. This closes
# the coincidental-command-quote unlock (row 24's `pytest tests/test_milestone_b.py` authorizing a
# ruling-work edit) without pricing any label. The `files:` convention is prose (no command token),
# so a declared file list survives the strip and remains the primary, authoritative match surface.
_CMD_TOKEN = (r"pytest|python3?|psql|pip|git|bash|sh|source|make|coverage|mypy|ruff|pyright|"
              r"pre-commit|run_conformance|cd|ls|cat|grep|tee|sed|awk|rm|cp|mv|chmod|touch")
_COMMAND_SPAN_RE = re.compile(r"\b(?:" + _CMD_TOKEN + r")\b[^\n;|&]*")


def strip_command_spans(text: str) -> str:
    """Blank shell-command spans so a file named as a command argument (data) is not read as a
    declaration to change it. Fails SAFE: over-blanking only forces an honest re-ticket (a deny),
    never a false allow (the gate's standing qualification posture, link 6)."""
    return _COMMAND_SPAN_RE.sub("  ", text)


def names_file(basename: str, *texts: str) -> bool:
    """True iff the ticket DECLARES `basename` — it appears (brace-expanded) in the entry text
    AFTER command spans are blanked (F45). A `files:` list survives the strip (it is prose, not a
    command); a coincidental `pytest <file>` command-quote does not. Keying is a file DECLARATION,
    never a subject-authored label (F26)."""
    for t in texts:
        if not t:
            continue
        for expanded in _brace_expand(strip_command_spans(t)):
            if basename in expanded:
                return True
    return False


def _load_state() -> dict:
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(st: dict) -> None:
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f)
    os.replace(tmp, STATE)


def _journal(rec: dict) -> None:
    try:
        os.makedirs(os.path.dirname(JOURNAL), exist_ok=True)
        with open(JOURNAL, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass


def _parse_pg_ts(s: str):
    """Parse a psql timestamptz like '2026-07-05 17:45:19.123+02' to a naive datetime (tz
    trimmed). Both operands compared with this are DB-clock, so the trim is consistent."""
    s = re.sub(r"[+-]\d\d(:?\d\d)?$", "", s.strip()).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"unparseable ts: {s!r}")


def candidate_rows(clock_iso: str):
    """All s12.ledger rows with ts > clock_iso, newest first, as tuples
    (id, ts_iso, statement, rationale, evidence). Keying is filename + currency only — the gate
    is concern/enacts-agnostic (§4.4 demoted, consult 11 §7.1). Raises on DB error so the
    caller can fail closed."""
    ck = clock_iso.replace("'", "''")
    sql = (
        f"SELECT id, ts, statement, coalesce(rationale,''), coalesce(evidence,'') "
        f"FROM {LEDGER} l WHERE ts > '{ck}' ORDER BY ts DESC;"
    )
    out = subprocess.run(
        ["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-F", FS, "-R", RS, "-c", sql],
        capture_output=True, text=True, timeout=8, check=True,
    )
    rows = []
    for rec in out.stdout.split(RS):
        if not rec.strip():
            continue
        parts = rec.split(FS)
        if len(parts) < 5:
            continue
        rid, ts, stmt, rat, ev = parts[:5]
        rows.append((int(rid), ts.strip(), stmt, rat, ev))
    return rows


def current_entry(basename: str, clock_iso: str):
    """Newest s12.ledger row that names `basename` (brace-aware) with ts > clock_iso.
    Returns (id, ts_iso) or None. Raises on DB error. No concern/enacts condition (de-priced)."""
    for rid, ts, stmt, rat, ev in candidate_rows(clock_iso):
        if names_file(basename, stmt, rat, ev):
            return rid, ts
    return None


def _ledger_schema() -> str:
    """The schema-name portion of LEDGER (e.g. 'public' from 'public.ledger'), used only by the
    permit-to-work checks below to reach `work_item_current`/`work_item_violations` in the SAME
    schema the ticket queries above already use."""
    return LEDGER.rsplit(".", 1)[0] if "." in LEDGER else "public"


def has_work_item_layer() -> bool:
    """Permit-to-work (BACKLOG "Run-5 forensics", 2026-07-10): True iff THIS world's ledger schema
    carries the s22 work-item layer (the `work_item_current` view exists) — a catalog-only
    `to_regclass` lookup, cheap and lock-free, never touching the table itself. Raises on DB error
    so the caller (inside main()'s existing fail-closed try/except for an identified governed
    mutation) denies the same way every other check here does on an unreachable DB.

    NAMED CHOICE: a pre-s22 world — the view genuinely absent, `to_regclass` returning NULL with NO
    error — is NOT a failure. It is the deliberate fail-OPEN branch (see module docstring): only a
    real DB-reachability failure fails closed here; "the view does not exist" is an ordinary,
    expected, silently-skip-the-check answer."""
    schema = _ledger_schema()
    ident = f"{schema}.work_item_current".replace("'", "''")
    out = subprocess.run(
        ["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-c",
         f"SELECT to_regclass('{ident}') IS NOT NULL;"],
        capture_output=True, text=True, timeout=8, check=True,
    )
    return out.stdout.strip() == "t"


def has_open_claimed_work_item() -> bool:
    """Permit-to-work: True iff `work_item_current` (s22) has at least one row with state='open'
    AND a non-NULL claimant — the permit itself. Only ever called after `has_work_item_layer()` has
    confirmed the view exists. Raises on DB error (fail-closed, same posture as every query here)."""
    schema = _ledger_schema()
    sql = (f"SELECT EXISTS (SELECT 1 FROM {schema}.work_item_current "
           f"WHERE state = 'open' AND claimant IS NOT NULL);")
    out = subprocess.run(
        ["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-c", sql],
        capture_output=True, text=True, timeout=8, check=True,
    )
    return out.stdout.strip() == "t"


def entry_flags(entry_id: int) -> list[str]:
    """The ledger-derived ticket_flags for the unlocking entry (all but window_redundant_entry,
    which is gate-state-derived). Computed from one focused query on the winning entry. Raises
    on DB error (the caller fails closed — a flag we cannot compute is not silently dropped)."""
    sql = (
        f"SELECT coalesce(l.concern,''), "
        f"(l.enacts IS NULL OR cardinality(l.enacts) = 0), "
        f"EXISTS (SELECT 1 FROM {LEDGER} t WHERE t.id = ANY(l.enacts) AND t.kind <> 'decision'), "
        f"EXISTS (SELECT 1 FROM {LEDGER} t WHERE t.id = ANY(l.enacts) AND EXISTS "
        f"(SELECT 1 FROM {LEDGER} s WHERE s.supersedes = t.id AND s.ts <= l.ts)) "
        f"FROM {LEDGER} l WHERE l.id = {int(entry_id)};"
    )
    out = subprocess.run(
        ["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-F", FS, "-c", sql],
        capture_output=True, text=True, timeout=8, check=True,
    )
    line = out.stdout.strip().split(RS)[0]
    parts = line.split(FS)
    if len(parts) < 4:
        return []
    concern, empty, nondesign, stale = parts[0].strip(), parts[1].strip() == "t", \
        parts[2].strip() == "t", parts[3].strip() == "t"
    flags = []
    if concern == "enactment" and empty:
        flags.append("enactment_no_enacts")
    if not empty and nondesign:
        flags.append("enacts_nondesign_target")
    if not empty and stale:
        flags.append("enacts_stale_antecedent")
    return flags


def _window_redundant(prev: dict | None, entry_id: int, entry_ts: str) -> bool:
    """True iff the unlocking entry is a redundant ticket: it was logged within WINDOW_S of the
    file's prior ticket while that window was still (nominally) open — i.e. the prior window
    reached fresh-consume by EXPIRY (open flag still True), NOT by a boundary close (which sets
    open=False, the F18-legitimate fresh entry). Compared in DB-clock only (both ts from psql)."""
    if not (isinstance(prev, dict) and prev.get("open") and prev.get("entry_ts")):
        return False
    if prev.get("entry_id") == entry_id:
        return False  # same ticket re-consumed (unreachable via currency, but guard anyway)
    try:
        delta = (_parse_pg_ts(entry_ts) - _parse_pg_ts(prev["entry_ts"])).total_seconds()
    except Exception:
        return False
    return 0.0 < delta <= WINDOW_S


def _deny(msg: str, kind: str = "?", target: str = "") -> int:
    _journal({"ts": datetime.now().isoformat(timespec="milliseconds"),
              "outcome": "denied", "deny_kind": kind, "target": target})
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": msg}}))
    print(msg, file=sys.stderr)
    return 2


def _observe_allow(kind: str, msg: str, target: str) -> int:
    """Rule (a) `"observe"` mode: never deny — ALLOW, but carry the same message that would have
    denied under `"enforce"` as a loud, non-blocking `additionalContext` warning (the agent sees
    it on its own next turn, mirroring hooks/demurral_detect.py's own warning shape) plus a
    journal record (`outcome: "observed_would_deny"`, distinct from a real `"denied"` row so the
    two are never confused when the journal is read later)."""
    _journal({"ts": datetime.now().isoformat(timespec="milliseconds"),
              "outcome": "observed_would_deny", "deny_kind": kind, "target": target})
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "allow",
        "additionalContext": f"[apparatus observe-mode WARNING — would DENY under enforce] {msg}"}}))
    return 0


def _window_open(entry: dict, now: float) -> bool:
    return bool(entry.get("open")) and (now - entry.get("opened", 0.0)) <= WINDOW_S


def _close_windows(st: dict, reason: str, cmd_head: str) -> None:
    """Close every open consumption window (repair 2 boundary). Idempotent."""
    closed = [k for k, v in st.items() if isinstance(v, dict) and v.get("open")]
    if not closed:
        return
    for k in closed:
        st[k]["open"] = False
    _save_state(st)
    _journal({"ts": datetime.now().isoformat(timespec="milliseconds"),
              "outcome": "boundary", "reason": reason, "closed": len(closed),
              "cmd_head": cmd_head})


def main() -> int:
    raw = sys.stdin.read()
    try:
        p = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # unparseable → cannot identify a governed mutation; pass through (audit logs it)

    try:
        _configure(p)
    except Exception:  # noqa: BLE001 — a config-resolution bug must never break a tool call;
        pass            # the module-level byte-held defaults (set above) are still in effect.

    tool = _first(p, "tool_name", "toolName", "name", default="")
    inp = _first(p, "tool_input", "toolInput", "input", default={})
    if not isinstance(inp, dict):
        return 0

    if tool in ("Write", "Edit", "NotebookEdit"):
        path = _first(inp, "file_path", "filePath", "path", "notebook_path", default="")

        # change_gate mechanism (SUBJECT_ROOT-integrity half): "off" skips this check entirely
        # (module docstring rule a) -- falls through as if SUBJECT_ROOT were healthy; is_governed()
        # below then resolves normally against whatever SUBJECT_ROOT happens to be.
        if SUBJECT_ROOT_MISCONFIGURED and CHANGE_GATE_MODE != "off":
            # Run-2 integrity finding: `is_governed()` below can only ever match a real path
            # under SUBJECT_ROOT, so a dangling SUBJECT_ROOT would otherwise make it return
            # False for every edit — silently governing nothing.
            if CHANGE_GATE_MODE == "enforce":
                return _deny(_deny_subject_root_missing(), "subject_root_missing", path)
            return _observe_allow("subject_root_missing", _deny_subject_root_missing(), path)

        if not is_governed(path):
            return 0
        # identified governed mutation → gate; fail CLOSED on any error (enforce only — see below)
        now = time.time()

        # PERMIT-TO-WORK (its own mechanism, its own mode — independent of CHANGE_GATE_MODE;
        # BACKLOG "Run-5 forensics", 2026-07-10) — composes IN FRONT of the ticket/window logic
        # below: even a currently-open consumption window still requires a live open+claimed work
        # item. Pre-s22 worlds (no work_item_current) skip this and fall straight through to
        # today's ticket-only behavior — see module docstring NAMED CHOICE. mode="off" skips this
        # mechanism's check entirely, same posture.
        if PERMIT_TO_WORK_MODE != "off":
            try:
                if SUBJECT_ROOT_WIRED and has_work_item_layer() and not has_open_claimed_work_item():
                    if PERMIT_TO_WORK_MODE == "enforce":
                        return _deny(DENY_NO_OPEN_WORK_ITEM, "no_open_claimed_work_item", path)
                    return _observe_allow("no_open_claimed_work_item", DENY_NO_OPEN_WORK_ITEM, path)
            except Exception as e:  # noqa: BLE001
                if PERMIT_TO_WORK_MODE == "enforce":
                    return _deny(DENY_NEEDS_ENTRY + f"  [permit-to-work check unavailable: "
                                 f"{type(e).__name__}]", "gate_error", path)
                return _observe_allow(
                    "permit_to_work_check_unavailable",
                    f"permit-to-work check unavailable ({type(e).__name__}: {e}) -- would have "
                    f"denied under enforce if the check itself had run clean.", path)

        # CHANGE_GATE proper: ticket/window logic. "off" allows unconditionally, no state/journal.
        if CHANGE_GATE_MODE == "off":
            return 0

        try:
            st = _load_state()
            key = os.path.abspath(path)
            prev = st.get(key)
            if isinstance(prev, dict) and _window_open(prev, now):
                # repair 2: still inside this file's consumption window — reuse the ticket
                _journal({"ts": datetime.now().isoformat(timespec="milliseconds"),
                          "outcome": "allowed", "file": path, "tool": tool,
                          "unlocked_by_entry": prev.get("entry_id"),
                          "entry_ts": prev.get("entry_ts"), "reused_ticket": True,
                          "ticket_flags": []})
                return 0
            clock = prev.get("entry_ts", EPOCH) if isinstance(prev, dict) else EPOCH
            hit = current_entry(os.path.basename(path), clock)
            if hit is None:
                if CHANGE_GATE_MODE == "enforce":
                    return _deny(DENY_NEEDS_ENTRY, "needs_entry", path)
                return _observe_allow("needs_entry", DENY_NEEDS_ENTRY, path)
            entry_id, entry_ts = hit
            flags = entry_flags(entry_id)
            if _window_redundant(prev, entry_id, entry_ts):
                flags.append("window_redundant_entry")
            # F45 / consult 17 item 5: a FRESH unlock under a ticket older than LONG_LAG_S is
            # flagged (event 61 unlocked at 4880s lag). Measured, never denied — the lag may be
            # legitimate; the review queue consumes the flag. Compared in DB-clock (both from psql).
            try:
                if (datetime.now() - _parse_pg_ts(entry_ts)).total_seconds() > LONG_LAG_S:
                    flags.append("long_lag_unlock")
            except Exception:  # noqa: BLE001
                pass
        except Exception as e:  # noqa: BLE001
            if CHANGE_GATE_MODE == "enforce":
                return _deny(DENY_NEEDS_ENTRY + f"  [gate check unavailable: {type(e).__name__}]",
                             "gate_error", path)
            return _observe_allow(
                "gate_check_unavailable",
                f"change-gate ticket check unavailable ({type(e).__name__}: {e}) -- would have "
                f"denied under enforce if the check itself had run clean.", path)
        st[key] = {"entry_id": entry_id, "entry_ts": entry_ts, "opened": now, "open": True}
        _save_state(st)
        _journal({"ts": datetime.now().isoformat(timespec="milliseconds"), "outcome": "allowed",
                  "file": path, "unlocked_by_entry": entry_id, "entry_ts": entry_ts,
                  "tool": tool, "reused_ticket": False, "ticket_flags": flags})
        return 0

    if tool == "Bash":
        cmd = _first(inp, "command", default="")
        if isinstance(cmd, str):
            if CHANGE_GATE_MODE != "off" and is_boundary(cmd):
                _close_windows(_load_state(), "test-run/commit", cmd[:80])
            if CHANGE_GATE_MODE != "off" and bash_mutates_governed(cmd):
                # Permit-to-work covers this already-denied class too (module docstring): the
                # more actionable teach-text wins over the generic bash-write message when it
                # applies, but a DB error here never blocks the mutation deny that already holds.
                if PERMIT_TO_WORK_MODE != "off" and SUBJECT_ROOT_WIRED:
                    try:
                        if has_work_item_layer() and not has_open_claimed_work_item():
                            if PERMIT_TO_WORK_MODE == "enforce":
                                return _deny(DENY_NO_OPEN_WORK_ITEM, "no_open_claimed_work_item",
                                             cmd[:80])
                            return _observe_allow("no_open_claimed_work_item",
                                                  DENY_NO_OPEN_WORK_ITEM, cmd[:80])
                    except Exception:  # noqa: BLE001
                        pass
                if CHANGE_GATE_MODE == "enforce":
                    return _deny(DENY_BASH_WRITE, "bash_write", cmd[:80])
                return _observe_allow("bash_write", DENY_BASH_WRITE, cmd[:80])

    return 0


if __name__ == "__main__":
    sys.exit(main())
