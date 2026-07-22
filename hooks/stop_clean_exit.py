#!/usr/bin/env python3
"""stop_clean_exit — the clean-exit gate (Claude Code Stop hook).

MOTIVATION (BACKLOG "Run-5 forensics" family, 2026-07-10): run 5 handed off with two open
review_gap rows and one never-closed work item. A world's own CLAUDE.md preamble already says
"Done means ./led review-gap, question-status, and ./led work violations are all clean" (point
5) -- but that is ADVICE inside a context window, and advice drifts under load, gets skimmed, or
just loses the fight against "the task looks done, let's wrap up." This hook MECHANIZES point 5:
on every Stop event, it reads the world's OWN ledger (read-only, no write, no side effect on the
governed schema) and refuses to let the turn end while governance state is visibly unfinished.

WHAT IT CHECKS (read-only SELECTs against views the kernel already exposes):
  - review_gap            : obliged-actor ledger rows with no distinct-actor attest yet.
  - question_status       : kind=question rows with no answers edge landed yet.
  - work_item_current     : OPEN items CLAIMED BY THIS SESSION, still undischarged and not
                            bequeathed (s22; see NAMED CHOICE -- STOP-GATE QUEUE SEMANTICS below).
                            Open UNCLAIMED items are never debt -- they are the queue -- and are
                            surfaced only as an informational count on allow paths.
  - work_item_violations  : duplicate_open / shipped_without_witness / depends_on_unknown_slug /
                            dependency_cycle rows (s22; same NAMED CHOICE).
  - work_review_gap       : item-keyed close acts with disposition=deferred not yet discharged by
                            a distinct-actor attest review (s29; same NAMED CHOICE, probed the
                            same way -- design/MAINT-COUNTERSIGN-CLOSE-SEMANTICS-SPEC.md Element B).

DEBT-TYPE CONVERSION (s29 Element B's own text: "a review_gap entry whose obligation row carries a
close-origin identity is debt CONVERSION -- the same debt changing type -- and
hooks/stop_clean_exit.py inherits breaker state over it exactly as it already inherits over
strict-subset shrinkage"). Under s29, a slug's debt entry naturally CONVERTS from `work_open:<slug>`
(the item hasn't closed yet) to `work_review_deferred:<slug>` (it closed with disposition=deferred
and has not yet been discharged) the moment `led work close ... --review-deferred` runs -- the SAME
underlying obligation on the SAME slug, now needing a different next action. `_debt_identity()` /
`_breaker_transition()` below normalize this pair to one identity so the breaker INHERITS across
the conversion instead of treating it as fresh debt and resetting the count to 1 -- see
`_debt_identity()`'s own docstring for the mechanism.
If every check that APPLIES to this world is empty, the stop is ALLOWED -- silently (exit 0, no
output) UNLESS open-but-non-blocking queue items exist (NAMED CHOICE -- STOP-GATE QUEUE SEMANTICS
below), in which case a one-line informational count is printed but the stop is still allowed; a
truly empty world (no open items of any kind) still sees zero interference from this hook, every
single time. If ANY check is non-empty, the stop is BLOCKED with a message enumerating exactly
what is open, by id/slug, each paired with the concrete command that closes it -- the same
fix-point-ergonomics posture `hooks/pretooluse_change_gate.py`'s DENY_HINT already uses: the
refusal IS the loop's feedback channel, so it must name the next command, never just the policy.

WIRING / UNWIRED POSTURE (same posture as `hooks/pretooluse_change_gate.py`, re-derived
independently in this file -- see "WHY A SEPARATE RESOLUTION" below): this hook is WIRED for a
session iff SUBJECT_ROOT is either an explicit `GATE_SUBJECT_ROOT` env var OR derived from a
located `<cwd>/deployment.json`, AND the resolved path is a real directory on disk. Any other
session (no env var, no deployment.json found, e.g. autoharn's own bare checkout, or a project
that predates this hook's rollout and was never re-wired into it -- ADR/BACKLOG posture: "do not
retroactively wire an existing world") is UNWIRED and this hook returns exit 0 on the very first
line of real work, before opening any connection -- zero interference, by construction, for every
session this project has not opted in.

NAMED CHOICE -- a dangling explicit SUBJECT_ROOT is treated as UNWIRED here, not specially
flagged. `hooks/pretooluse_change_gate.py` owns SUBJECT_ROOT *integrity* (the run-2 finding: a
moved project leaving a stale path baked into settings.json) and denies loudly on that specific
defect for every governed edit. This hook's job is the LEDGER check, not subject-root hygiene --
re-diagnosing the same defect a second, differently-worded way here would just be noise; the
existing gate already teaches the fix (repoint GATE_SUBJECT_ROOT), and once repointed this hook
starts working too, at zero extra cost.

NAMED CHOICE -- pre-s22 worlds (BACKLOG "Run-5 forensics", 2026-07-10 introduced the work-item
layer; older worlds do not carry it). `work_item_current`/`work_item_violations` are each probed
with a cheap catalog-only `to_regclass` lookup (mirroring
`hooks/pretooluse_change_gate.py`'s `has_work_item_layer()`) before being queried; a view that
does not exist is NOT an error -- it is silently excluded from the clean/dirty computation, so a
pre-s22 world is judged on review_gap + question_status alone, exactly the two checks its own
CLAUDE.md point 5 could always name. `review_gap`/`question_status` themselves get the same
existence probe for uniform defensive coverage (every wired world since s15 carries both, so this
branch is not expected to fire in practice, but an absent view is architecturally the same "check
only what exists" shape either way -- treating it identically costs nothing and avoids a second,
differently-reasoned code path).

NAMED CHOICE -- STOP-GATE QUEUE SEMANTICS (design/FABLE-STOP-GATE-QUEUE-SEMANTICS-SPEC.md,
ratified by the maintainer 2026-07-15, ledger decision row same date): the work-item leg's
predicate narrowed from "any state='open' item is debt" to "an item THIS session still HOLDS a
claim on, undischarged and unbequeathed, is debt." Witnessed live in the experience world:
preamble point 1's own mandated queue decomposition (open, unclaimed items are the PLANNED,
not-yet-started work every scaffolded deployment is told to ledger up front, including items "you
will not start this session") was tripping the OLD predicate on every routine multi-session or
background-workflow commission, driving the circuit breaker's loudest fail-open banner onto the
routine happy path and destroying its evidentiary meaning (alarm fatigue). The principle (spec
§2): "A stop is dirty when THIS session abandons something it holds -- never because the world
contains planned work." Three cases, in this order:
  1. UNCLAIMED open items NEVER block -- they are the queue, exactly what preamble point 1 asks
     every deployment to pre-ledger. They are still surfaced, on ALLOW paths only, as a one-line
     informational count ("N open unclaimed item(s) remain -- the successor's queue"), never as
     debt and never as a reason to block.
  2. An item CLAIMED BY THIS SESSION -- kernel-visible: the claiming `work_claimed` row's own
     `stamp_session` (the interception stamp, not a writer-supplied value -- the same field the
     STOP-DISPOSITION WARNING below already reads) equals the Stop hook input's own `session_id`
     -- blocks UNLESS bequeathed (case 3). This is exactly run-5's original defect (a session
     abandoning its own open claim) and is still refused, unchanged.
  3. BEQUEST: a `kind='decision'` row stamped to this session whose `statement` begins `stopping:`
     and whose `remains:` clause names the claimed slug as a literal token (substring/token match
     against the `remains:` text only -- no inference) discharges the item: the handoff becomes a
     typed, stamped, on-ledger act instead of archaeology. Listed on the allow path as bequeathed,
     never silently dropped.
Items claimed by a DIFFERENT session -- including one whose claimant session no longer exists,
the "orphaned claim" case -- are OUT OF THIS SPEC'S SCOPE, deliberately (spec §3 last bullet):
under the new predicate they never block a different session's stop either way, so this pass does
not manufacture new coverage for them; they need a home in `work_item_violations` or an audit
view instead, named here as a known gap, not solved here.
DEGRADE (spec §4 4th bullet, fail direction stated): when THIS session's ownership of a claim
CANNOT be proven -- no `session_id` on stdin, a pre-s17 world with no `stamp_session` column at
all, or the column-existence probe itself fails -- the work-item leg degrades to the CURRENT
(pre-this-pass) behavior: every claimed open item blocks, unconditionally, exactly as it always
did before this NAMED CHOICE. This is the conservative direction: narrowing needs the proof;
absent the proof, the old, stricter predicate stands rather than silently under-blocking.

DB-UNREACHABLE POSTURE -- NAMED CHOICE, fail direction stated: a DB error (any query failing, not
"the view is absent" -- that is the OK branch above) is treated as its own single non-clean
"debt" category (`ledger_unreachable`), which BLOCKS the stop with teach-text naming the failure,
exactly like a real debt item. This is fail-CLOSED on the first and second occurrence (an
unreachable ledger is exactly the kind of silent-governance-gap this project's own ADR-0002 rules
out tolerating quietly) -- but it is NOT exempt from the circuit breaker below, so a genuinely
broken DB (not a transient blip) eventually fails OPEN after three identical stops rather than
trapping the session forever. That is a deliberate trade: never let an infrastructure outage
become an un-endable session, at the cost of (rare, loudly-flagged) governance blindness during
a sustained outage.

CIRCUIT BREAKER -- Stop hooks are DESIGNED to re-fire after the agent does more work (the agent
goes and closes the debt, tries to stop, the hook re-checks); that is the whole mechanism, not a
bug to route around. But an agent can get stuck on debt it structurally cannot close in-session
(a review obligated to a DIFFERENT principal it cannot act as; a dependency cycle it cannot
one-sidedly resolve) -- an unconditional block would then spin forever with no way out. NAMED
CHOICE: this hook fingerprints the exact debt set (every open id/slug/violation, sorted and
hashed) into a small state file under the world's `.claude/` (same pattern and same atomic
tmp+os.replace write `hooks/pretooluse_change_gate.py`'s own STATE file uses). The IDENTICAL
fingerprint blocks the first two times it is seen; the THIRD time the identical fingerprint is
seen, this hook ALLOWS the stop instead of blocking, printing a loud, impossible-to-miss final
warning to stderr (visible in the hook's own output/logs) so a human reading the transcript sees
it -- no separate journal file is kept (unlike pretooluse_change_gate.py's JOURNAL: this hook is
read-only and the state file itself already retains the last debt-hash/count, sufficient for this
hook's own narrower purpose). FAIL DIRECTION,
stated plainly: this fails OPEN on unclosable debt after N=3 identical blocks -- a session that
can make no further progress on its own ledger is allowed to end rather than being trapped by its
own gate; the warning is the compensating control (the debt is not silently dropped, it is loudly
handed to whoever reads the transcript next).

MAINTAINER RULING, 2026-07-16: the fail-open-after-3-identical-fingerprints trade-off above is a
DELIBERATE, maintainer-ratified posture, not a placeholder awaiting hardening -- chosen over
hardening the third strike with a distinct signal (e.g. a harder block, an escalation channel, or
a different N). The stated condition for reopening this question is a WITNESSED SPECIMEN of the
breaker actually being gamed by bare repetition (an agent deliberately re-emitting the identical
debt fingerprint to cash the fail-open rather than genuinely being stuck) -- absent that specimen,
this trade-off stands as designed.

BREAKER TRANSITION -- PROGRESS DOES NOT RE-ARM (ENT TESTBED FINDING 5, 2026-07-13, DEFECT fix --
`stop-breaker-progress-reset-defect`, diagnosed from ent's own stop_clean_exit journal
16:01-16:32): the naive rule "any change in the debt fingerprint resets the counter to 1" was
wrong for a WIDE DECOMPOSITION -- a session carrying many parallel open work items closes one,
the entries set shrinks, the fingerprint changes, and under the naive rule the breaker reset to
1/3 even though the agent had just made real progress. Witnessed live: fail-open at count 4 (an
earlier per-session limit) at 16:18, item `upstream-anchoring` closed, then blocked/blocked/
fail-open again 16:31:30-57 -- the session paid two fresh Stop blocks per unit of progress. The
false assumption the naive rule encoded: fingerprint-change == new-debt-deserving-fresh-scrutiny;
in a wide decomposition it usually means an item LEFT, not one ARRIVED. THE FIX
(`_breaker_transition()` below): a debt-set change is inspected, not just hashed. If the new
entries set is a STRICT SUBSET of the prior entries set (every current entry was already present
last time; at least one prior entry is now gone; nothing new was added) the breaker INHERITS the
prior open count instead of resetting -- progress never re-arms the blocker. Any entry that was
NOT in the prior set (a genuinely NEW debt item, or a same-size swap) still resets the counter to
1, exactly as before -- this fix narrows the reset condition, it does not remove it. A clean stop
still clears the state file entirely, so an old fingerprint never leaks into an unrelated future
debt episode, and the state file now additionally retains the prior entries LIST (not just its
hash), because the subset comparison needs the actual member set, not a one-way digest.

APPARATUS.JSON SWITCHBOARD (maintainer mandate, 2026-07-10): this mechanism's mode
(`mechanisms.clean_exit.mode`) lives at `<SUBJECT_ROOT>/.claude/apparatus.json`, read once inside
`_configure()` -- but only when WIRED (an unwired session never had a debt-check notion at all;
apparatus.json is irrelevant to it). `"off"` -- return 0 before any debt collection, even though
the session IS wired (an explicit "I don't want this check" distinct from "not wired"); `"observe"`
-- runs the SAME `_collect_debt()` as `"enforce"` (so the debt enumeration is real, not guessed),
but a non-empty debt set never BLOCKS the stop: it allows (exit 0) with the identical debt text
carried as a loud `additionalContext` warning (mirrors hooks/demurral_detect.py's own Stop-leg
warning shape) plus a journal record -- no circuit breaker is needed here (unlike enforce's
DEBT_REPEAT_LIMIT), since this mode never blocks in the first place; `"enforce"` -- byte-identical
to this file's behavior before this pass, circuit breaker included. Missing file/key resolves to
`"enforce"` (rule c: this mechanism spends nothing per invocation, so it defaults to its current
strength). An unrecognized mode string never widens permissions (rule d) -- falls back to
`"enforce"`, already the strictest state, with a loud stderr warning naming the bad value.

STOP-DISPOSITION WARNING (BACKLOG "Run-8 mid-run forensics", 2026-07-11 -- preamble point 8,
mechanized): "stopping is a ledgered act" -- a worker leaves its work resumable for whoever picks
it up next by writing `./led decision "stopping: <why>; stands: <done>; remains: <slugs>"` before
it stops. Point 8's own composition note names the class this catches: it would have caught run
7's gap AT ITS OWN EXIT ("stopping: phase 2 remains" cannot be written without ledgering phase 2
first). This hook is the natural mechanization site -- it already fires at every Stop event and
already reads this world's ledger read-only. WHAT IT CHECKS, additively (never in place of the
existing debt collection above): a `kind='decision'` row whose `statement` begins `stopping:`,
STAMPED to the stopping session's own id (`stamp_session` = the hook input's own `session_id`
field -- the interception stamp, not a writer-supplied value, so this cannot be satisfied by
typing the word "stopping:" into an unrelated row). Missing -> a WARNING is appended to the
hook's output; this NEVER blocks and NEVER introduces a new deny reason (unlike the debt checks
above, which really do block in `"enforce"` mode) -- it rides the SAME `CLEAN_EXIT_MODE` this
mechanism already reads (`"off"` skips the check entirely; `"observe"`/`"enforce"` both run it,
both only ever warn), so there is no new apparatus.json switchboard entry for it. It is only ever
consulted on an ALLOW path (silent-clean, the observe-mode allow, or the circuit-breaker's
loud-allow) -- never on a `"enforce"`-mode BLOCK, since the turn is not actually ending there; the
successor gets another chance to write the disposition row before the stop that does succeed.
DEGRADES SILENT (module-wide convention, same posture as every other best-effort probe in this
file) on: no `session_id` on stdin, a pre-stamp world (the `stamp_session` column itself does not
exist -- s17 introduced it; a world older than that never carries the column), or a genuinely
unreachable ledger (the query fails the same way `_collect_debt()`'s queries do) -- none of these
are treated as "missing disposition", since none of them can distinguish a real gap from a world
this check simply cannot evaluate.

WHY A SEPARATE RESOLUTION, NOT A SHARED IMPORT OF pretooluse_change_gate.py's `_configure()`: this
file is deliberately self-contained (no import of, or dependency on, hooks/pretooluse_change_gate.py
or hooks/stamp_intercept.py -- both are under concurrent edit by another pass; this hook must not
create a merge hazard or a load-bearing coupling to their in-flight internals). It re-derives the
SAME conventions independently: env override > `<cwd>/deployment.json` (filing/deployment_record.py,
the one home for that shape) > byte-held default -- the same three-tier precedence, the same env-var
names (LEDGER_HOST/LEDGER_DB/GATE_LEDGER/GATE_SUBJECT_ROOT) pretooluse_change_gate.py already
established as this project's neutral vocabulary (BACKLOG "E13 retirement", 2026-07-09) -- just
without that file's now-deprecated E13_* alias support, which has no reason to exist for a hook
that was never named e13 in the first place.

Stdlib only, top-of-file imports (the lazy-import gate, gates/no_lazy_imports.py, applies).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

# Eager, top-of-file sys.path insert + import (lazy imports banned) -- the identical pattern
# hooks/pretooluse_change_gate.py itself uses to reach filing/deployment_record.py, the ONE home
# for the deployment.json shape (ADR-0012 P1).
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)  # hooks/ -> autoharn root
sys.path.insert(0, os.path.join(_REPO_ROOT, "filing"))
import deployment_record  # noqa: E402  (filing/deployment_record.py, the ONE home for the deployment.json shape)

# ---------------------------------------------------------------------------------------------
# CONFIG RESOLUTION -- see module docstring "WHY A SEPARATE RESOLUTION". Same three-tier
# precedence as pretooluse_change_gate.py: an env var overrides the deployment record; the
# deployment record is used when no env var is set; the byte-held default is used when neither
# resolves.
# ---------------------------------------------------------------------------------------------
_DEFAULT_PGHOST = "192.168.122.1"
_DEFAULT_PGDB = "nla"
_DEFAULT_LEDGER = "public.ledger"

PGHOST = _DEFAULT_PGHOST
PGDB = _DEFAULT_PGDB
LEDGER = _DEFAULT_LEDGER
SUBJECT_ROOT = ""
STATE = ""
JOURNAL = ""
# True iff this invocation is WIRED: SUBJECT_ROOT is "configured" (explicit GATE_SUBJECT_ROOT env
# var, OR a located+loaded deployment.json) AND resolves to a real directory. False for autoharn's
# own bare checkout (no deployment.json, no env override) and for any pre-existing world this pass
# deliberately does not retroactively wire -- see module docstring.
WIRED = False
# APPARATUS.JSON SWITCHBOARD (module docstring, maintainer mandate 2026-07-10).
_VALID_MODES = ("off", "observe", "enforce")
CLEAN_EXIT_MODE = "enforce"

DEBT_REPEAT_LIMIT = 3  # N: the circuit breaker's threshold (see module docstring).

# Field / record separators for psql -tA output, byte-identical convention to
# hooks/pretooluse_change_gate.py: ASCII US / RS, so entry text containing tabs or newlines
# (multi-line statements, work titles) cannot corrupt row parsing.
FS = "\x1f"
RS = "\x1e"


def _find_deployment_path(data: dict) -> str | None:
    """Locate this project's deployment.json: an explicit LEDGER_DEPLOYMENT override first, else
    `<cwd>/deployment.json` using the hook input's own `cwd` field (mirroring
    pretooluse_change_gate.py's/stamp_provenance.py's/stamp_intercept.py's identical convention).
    Returns None -- never raises -- when neither resolves to an existing file."""
    explicit = os.environ.get("LEDGER_DEPLOYMENT", "")
    if explicit:
        return explicit
    cwd = data.get("cwd") or os.getcwd()
    candidate = os.path.join(cwd, "deployment.json")
    return candidate if os.path.isfile(candidate) else None


def _load_deployment_quiet(path: str) -> deployment_record.DeploymentRecord | None:
    """Best-effort deployment.json load. Never raises -- a missing/malformed record degrades to
    the env-var/hardcoded path exactly like every other mis-provisioning this hook tolerates."""
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
    """apparatus["mechanisms"]["clean_exit"]["mode"], defaulted/validated per the maintainer's
    2026-07-10 switchboard mandate (rules b/d -- see module docstring's APPARATUS.JSON section)."""
    default = "enforce"
    mechs = apparatus.get("mechanisms")
    entry = mechs.get("clean_exit") if isinstance(mechs, dict) else None
    raw = entry.get("mode") if isinstance(entry, dict) else None
    if raw is None:
        return default
    if raw in _VALID_MODES:
        return raw
    print(f"[apparatus] WARNING: mechanisms.clean_exit.mode={raw!r} in "
          f"{root}/.claude/apparatus.json is unrecognized (must be one of {_VALID_MODES}) -- "
          f"never widening permissions; falling back to {default!r}.", file=sys.stderr)
    return default


def _configure(data: dict) -> None:
    """Resolve every connection/config value for THIS invocation. Called once, at the top of
    `main()`, right after stdin is parsed (the deployment.json lookup needs the hook input's own
    `cwd`, only available once stdin has been read)."""
    global PGHOST, PGDB, LEDGER, SUBJECT_ROOT, STATE, JOURNAL, WIRED, CLEAN_EXIT_MODE
    dep_path = _find_deployment_path(data)
    dep = _load_deployment_quiet(dep_path) if dep_path else None
    using_deployment = bool(dep_path and dep)

    PGHOST = os.environ.get("LEDGER_HOST") or (dep.host if dep else None) or _DEFAULT_PGHOST
    PGDB = os.environ.get("LEDGER_DB") or (dep.db if dep else None) or _DEFAULT_PGDB
    LEDGER = (os.environ.get("GATE_LEDGER") or (f"{dep.schema}.ledger" if dep else None)
              or _DEFAULT_LEDGER)

    env_subject_root = os.environ.get("GATE_SUBJECT_ROOT")
    default_root = os.path.dirname(dep_path) if using_deployment else ""
    SUBJECT_ROOT = os.path.abspath(env_subject_root or default_root) if (env_subject_root or default_root) else ""
    WIRED = bool((env_subject_root or using_deployment) and SUBJECT_ROOT and os.path.isdir(SUBJECT_ROOT))

    default_state = os.path.join(SUBJECT_ROOT, ".claude", "stop_clean_exit_state.json") if WIRED else ""
    STATE = os.environ.get("STOP_CLEAN_EXIT_STATE") or default_state
    default_journal = os.path.join(SUBJECT_ROOT, ".claude", "logs", "stop_clean_exit.journal.jsonl") if WIRED else ""
    JOURNAL = os.environ.get("STOP_CLEAN_EXIT_JOURNAL") or default_journal

    CLEAN_EXIT_MODE = _resolve_mode(_load_apparatus_quiet(SUBJECT_ROOT) if WIRED else {}, SUBJECT_ROOT)


def _ledger_schema() -> str:
    """The schema-name portion of LEDGER (e.g. 'public' from 'public.ledger') -- every view this
    hook reads lives in the same schema the ledger table itself does."""
    return LEDGER.rsplit(".", 1)[0] if "." in LEDGER else "public"


def _view_exists(schema: str, view: str) -> bool:
    """Cheap, lock-free, catalog-only existence probe (mirrors
    pretooluse_change_gate.py's `has_work_item_layer()`). Raises on a genuine DB error so the
    caller's fail-closed-but-breaker-bounded posture applies; "the view does not exist" is a
    normal `to_regclass(...) IS NOT NULL -> false` answer, not an exception."""
    ident = f"{schema}.{view}".replace("'", "''")
    out = subprocess.run(
        ["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-c",
         f"SELECT to_regclass('{ident}') IS NOT NULL;"],
        capture_output=True, text=True, timeout=8, check=True,
    )
    return out.stdout.strip() == "t"


def _column_exists(schema: str, table: str, column: str) -> bool:
    """Cheap, lock-free, catalog-only existence probe -- the STOP-DISPOSITION WARNING's own
    pre-stamp-world check (module docstring): `stamp_session` was introduced by s17, so a world
    that predates it never carries the column. Raises on a genuine DB error, same posture as
    `_view_exists()` -- the caller (the stop-disposition check only) treats any error as
    "degrade silent", never as debt."""
    sch, tab, col = (schema.replace("'", "''"), table.replace("'", "''"), column.replace("'", "''"))
    out = subprocess.run(
        ["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-c",
         f"SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = '{sch}' "
         f"AND table_name = '{tab}' AND column_name = '{col}');"],
        capture_output=True, text=True, timeout=8, check=True,
    )
    return out.stdout.strip() == "t"


def _stop_disposition_reason(session_id: str) -> str | None:
    """STOP-DISPOSITION WARNING (module docstring, BACKLOG "Run-8 mid-run forensics",
    2026-07-11): returns teach-text iff no `kind='decision'` row whose `statement` begins
    `stopping:` is stamped (`stamp_session`) to THIS session. Returns None -- the check simply
    does not apply, never "disposition present" -- when: no `session_id` on stdin, a pre-stamp
    world (no `stamp_session` column), a genuine DB error, OR the row really is present. Never
    raises; this function alone decides nothing about block/allow -- callers only ever use it to
    decide whether to print an ADDITIONAL warning on a path that was already going to allow."""
    if not session_id:
        return None
    try:
        schema = _ledger_schema()
        if not _column_exists(schema, "ledger", "stamp_session"):
            return None  # pre-stamp world (s17 introduced the column) -- nothing to check
        sid = session_id.replace("'", "''")
        out = subprocess.run(
            ["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-c",
             f"SELECT EXISTS (SELECT 1 FROM {schema}.ledger WHERE kind = 'decision' "
             f"AND statement LIKE 'stopping:%' AND stamp_session = '{sid}');"],
            capture_output=True, text=True, timeout=8, check=True,
        )
        if out.stdout.strip() == "t":
            return None  # disposition row present -- nothing to warn about
    except Exception:  # noqa: BLE001 -- an unreadable ledger degrades silent for THIS check
        return None     # (module docstring); the primary debt collection already covers the
                         # "ledger unreachable" category as its own blocking debt line.
    return (
        "Ledger policy (stop-disposition, CLAUDE.md point 8 / hooks/stop_clean_exit.py): no "
        "`decision` row beginning 'stopping:' is stamped to this session -- stopping is a "
        "ledgered act (BACKLOG 'Run-8 mid-run forensics', 2026-07-11: a stop with no trail "
        "strands the successor in archaeology). Before you stop, write the disposition a "
        "successor resumes from:\n"
        "  ./led decision \"stopping: <why>; stands: <what is done>; remains: <slugs/refs>\""
    )


def _warn_stop_disposition(session_id: str) -> None:
    """Prints the stop-disposition warning (module docstring) as a side effect ONLY -- never
    changes the caller's return code. Called only from `main()`'s ALLOW paths (never from
    `_block()`'s path -- the turn is not ending there, so there is nothing yet to warn about).
    Mirrors `_allow_with_warning()`'s own loud stderr-banner shape exactly ("exactly like the
    circuit-breaker's loud-allow path" -- the build mandate's own words) so this warning is
    visually identical to the mechanism's existing loud-allow convention, in EVERY mode
    (`"observe"` and `"enforce"` alike -- this check itself never distinguishes between them,
    since it never blocks either way)."""
    reason = _stop_disposition_reason(session_id)
    if reason is None:
        return
    banner = (
        "\n" + "!" * 78 + "\n"
        "STOP-DISPOSITION WARNING -- allowing this stop, but no stop-disposition row was found "
        "for this session:\n" + reason + "\n" + "!" * 78 + "\n"
    )
    print(banner, file=sys.stderr)


def _query(sql: str) -> list[tuple[str, ...]]:
    """Run one read-only SELECT, FS/RS-separated for safe parsing of free-text columns. Raises on
    a genuine DB error (subprocess.CalledProcessError / TimeoutExpired) -- caller's job to turn
    that into the `ledger_unreachable` debt category."""
    out = subprocess.run(
        ["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-F", FS, "-R", RS, "-c", sql],
        capture_output=True, text=True, timeout=8, check=True,
    )
    rows = []
    for rec in out.stdout.split(RS):
        if not rec.strip():
            continue
        rows.append(tuple(p.strip() for p in rec.split(FS)))
    return rows


def _stamp_session_available(schema: str) -> bool:
    """NAMED CHOICE -- STOP-GATE QUEUE SEMANTICS (module docstring): True iff `ledger.stamp_session`
    can be PROVEN to exist this call. Wraps `_column_exists()` (which raises on a genuine DB error)
    in a try/except that returns False instead -- unlike most of this hook's checks, an inability
    to prove the column exists is NOT "ledger unreachable" debt here; it is the DEGRADE signal:
    the caller (the work-item leg) falls back to the pre-this-pass conservative predicate rather
    than raising. Never raises."""
    try:
        return _column_exists(schema, "ledger", "stamp_session")
    except Exception:  # noqa: BLE001 -- degrade, don't fail (see docstring above)
        return False


def _claim_sessions(schema: str, slugs: list[str]) -> dict[str, str | None]:
    """For each already-claimed `slugs` (per `work_item_current`), returns the CLAIMING
    `work_claimed` row's own `stamp_session` -- the interception stamp, the only thing that proves
    a claim is THIS session's (spec §3, module docstring NAMED CHOICE). Mirrors
    `work_item_current`'s own `claimed` CTE exactly (`DISTINCT ON (work_slug) ... ORDER BY
    work_slug, id DESC`) so this reads the identical latest-claim row the view itself resolved
    `claimant` from -- never a stale or wrong-row answer. Caller has already proven the
    `stamp_session` column exists (`_stamp_session_available()`) before calling this; raises on a
    genuine DB error like every other `_query()` call in this module (the caller's normal
    ledger_unreachable posture applies)."""
    if not slugs:
        return {}
    quoted = ",".join("'" + s.replace("'", "''") + "'" for s in slugs)
    rows = _query(
        f"SELECT DISTINCT ON (work_slug) work_slug, coalesce(stamp_session, '') "
        f"FROM {schema}.ledger WHERE kind = 'work_claimed' AND work_slug IN ({quoted}) "
        f"ORDER BY work_slug, id DESC;")
    return {slug: (sess or None) for slug, sess in rows}


def _bequeathed_slugs(schema: str, session_id: str) -> set[str]:
    """BEQUEST (module docstring NAMED CHOICE, spec §3 third bullet): every slug named as a
    LITERAL TOKEN in the `remains:` clause of a `kind='decision'` row stamped to THIS session
    whose `statement` begins `stopping:`. Literal token match ONLY -- no inference: the
    `remains:` text (everything after the literal substring `remains:` up to the next `;` or end
    of string) is split on commas/whitespace and each token stripped of trailing punctuation;
    a slug bequeaths iff it appears there verbatim. A session may write more than one qualifying
    disposition row (e.g. amending an earlier one); every row's `remains:` clause contributes.
    Raises on a genuine DB error like every other `_query()` call here (ledger_unreachable)."""
    if not session_id:
        return set()
    sid = session_id.replace("'", "''")
    rows = _query(
        f"SELECT statement FROM {schema}.ledger WHERE kind = 'decision' "
        f"AND statement LIKE 'stopping:%' AND stamp_session = '{sid}';")
    slugs: set[str] = set()
    for (statement,) in rows:
        m = re.search(r"remains:\s*([^;]*)", statement)
        if not m:
            continue
        for tok in re.split(r"[,\s]+", m.group(1)):
            tok = tok.strip(" \t.,;")
            if tok:
                slugs.add(tok)
    return slugs


def _collect_debt(session_id: str) -> tuple[list[str], list[str], list[str]]:
    """Read every governance check that applies to this world. Returns (debt_lines, entries,
    info_lines): `debt_lines` is the human-readable, per-item teach-text (one item per open
    row/violation, each paired with the command that closes it); `entries` is the same
    information in a stable, machine-comparable form used only to fingerprint the debt set for
    the circuit breaker; `info_lines` (NAMED CHOICE -- STOP-GATE QUEUE SEMANTICS, module
    docstring) is NEVER debt -- it is informational-only text (the open-unclaimed-queue count,
    bequeathed items) a caller MAY surface on an ALLOW path, never on a block.
    Raises on a genuine DB error -- the caller converts that into the ledger_unreachable category."""
    schema = _ledger_schema()
    debt_lines: list[str] = []
    entries: list[str] = []
    info_lines: list[str] = []

    if _view_exists(schema, "review_gap"):
        rows = _query(f"SELECT id, coalesce(scope,'') FROM {schema}.review_gap ORDER BY id;")
        if rows:
            debt_lines.append(f"OPEN REVIEW GAPS ({schema}.review_gap) -- {len(rows)} row(s):")
            for rid, scope in rows:
                debt_lines.append(
                    f"  - ledger row {rid} (obligation scope: {scope!r}) has no distinct-actor "
                    f"attest yet ->\n"
                    f"      ./led review {rid} <attest|attest_with_reservations|refuse> "
                    f"<technical|managerial|financial> \"<basis>\"")
                entries.append(f"review_gap:{rid}")

    if _view_exists(schema, "question_status"):
        rows = _query(
            f"SELECT question_id, question_kind FROM {schema}.question_status "
            f"WHERE NOT answered ORDER BY question_id;")
        if rows:
            debt_lines.append(f"UNANSWERED QUESTIONS ({schema}.question_status) -- {len(rows)} row(s):")
            for qid, kind in rows:
                debt_lines.append(
                    f"  - question {qid} (kind={kind}) is unanswered ->\n"
                    f"      ./led <kind> \"<answer>\" --answers {qid}")
                entries.append(f"question:{qid}")

    # NAMED CHOICE (module docstring): work_item_current/work_item_violations are s22-only.
    # A view that does not exist is skipped entirely, not an error -- "check only what exists."
    #
    # NAMED CHOICE -- STOP-GATE QUEUE SEMANTICS (module docstring, full rationale there):
    # unclaimed open items are the queue, never debt (informational only, allow paths only);
    # items claimed by THIS session are debt unless bequeathed; items whose claim ownership
    # cannot be proven this call (no session_id, no stamp_session column) DEGRADE to the
    # pre-this-pass conservative predicate (every claimed open item blocks).
    if _view_exists(schema, "work_item_current"):
        # EFFECTIVE_STATE (kernel/lineage/s33-composite-discharge.sql, ledger item
        # composite-parent-autodischarge): the INFORMATIONAL "open unclaimed item(s) remain"
        # line below reads effective_state, when present -- a discharged-by-obligations
        # composite leaves the queue with no act (spec's own text). The DEBT predicate
        # (claimed items, below) is deliberately UNTOUCHED -- it keeps reading the SAME `rows`
        # this query returns, filtered on `has_claimant` only, exactly as before this pass
        # (minimal-touch, ADR-0004; this commission's own scope names only the informational
        # line). A pre-s33 kernel (no effective_state column) degrades to `eff == state`
        # always, so `unclaimed`'s filter below is a no-op and behavior is byte-identical.
        has_eff = _query(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            f"WHERE table_schema = '{schema}' AND table_name = 'work_item_current' "
            "AND column_name = 'effective_state');")
        eff_col = "effective_state" if (has_eff and has_eff[0][0] == "t") else "state"
        rows = _query(
            f"SELECT slug, (claimant IS NOT NULL), {eff_col} FROM {schema}.work_item_current "
            f"WHERE state = 'open' ORDER BY slug;")
        unclaimed = [slug for slug, has_claimant, eff in rows
                     if has_claimant != "t" and eff != "discharged-by-obligations"]
        claimed = [slug for slug, has_claimant, eff in rows if has_claimant == "t"]

        if unclaimed:
            info_lines.append(
                f"{len(unclaimed)} open unclaimed item(s) remain -- the successor's queue: "
                + ", ".join(unclaimed))

        if claimed:
            narrow_ok = bool(session_id) and _stamp_session_available(schema)
            blocking_lines: list[str] = []
            blocking_entries: list[str] = []

            if not narrow_ok:
                # DEGRADE (spec §4 4th bullet, module docstring): this session's ownership of a
                # claim cannot be proven this call -- fall back to the CURRENT (pre-this-pass)
                # conservative predicate: every claimed open item blocks, unconditionally.
                for slug in claimed:
                    blocking_lines.append(
                        f"  - work item '{slug}' is open and claimed (session-narrowing "
                        f"unavailable this call -- degraded to the pre-queue-semantics "
                        f"conservative predicate; see hooks/stop_clean_exit.py's NAMED CHOICE "
                        f"-- STOP-GATE QUEUE SEMANTICS) ->\n"
                        f"      ./led work close {slug} <shipped|superseded|dropped|deferred> "
                        f"[--witness <ref>]")
                    blocking_entries.append(f"work_open:{slug}")
            else:
                claim_sessions = _claim_sessions(schema, claimed)
                bequeathed = _bequeathed_slugs(schema, session_id)
                for slug in claimed:
                    if claim_sessions.get(slug) != session_id:
                        # not THIS session's claim -- out of this spec's scope (the orphaned-claim
                        # gap, module docstring / spec §3 last bullet): never blocks a DIFFERENT
                        # session's stop under the new predicate either way.
                        continue
                    if slug in bequeathed:
                        info_lines.append(
                            f"work item '{slug}' is claimed by this session and still open, but "
                            f"bequeathed via a stopping-disposition row -- not blocking")
                        continue
                    blocking_lines.append(
                        f"  - work item '{slug}' is open and claimed by THIS session ->\n"
                        f"      ./led work close {slug} <shipped|superseded|dropped|deferred> "
                        f"[--witness <ref>]\n"
                        f"      -- or bequeath it to a successor: ./led decision \"stopping: "
                        f"<why>; remains: {slug}\"")
                    blocking_entries.append(f"work_open:{slug}")

            if blocking_lines:
                debt_lines.append(
                    f"OPEN WORK ITEMS ({schema}.work_item_current, state=open, claimed by this "
                    f"session, undischarged) -- {len(blocking_lines)} item(s):")
                debt_lines.extend(blocking_lines)
                entries.extend(blocking_entries)

    if _view_exists(schema, "work_item_violations"):
        # s37 (kernel/lineage/s37-violation-disposition.sql, consult A6(i)): LIVE column-existence
        # gate for target_id (the SAME convention this whole module uses for every kernel-version-
        # dependent read) -- a pre-s37 view has no target_id column, so the discharge-path hint
        # below degrades to the pre-s37 generic escalate-to-maintainer text for EVERY member
        # (there is no answering act on a pre-s37 world; that text was correct there, and stays
        # correct there -- only a POST-s37 world gets the new, accurate hint).
        has_target_id = bool(_query(
            f"SELECT 1 FROM information_schema.columns WHERE table_schema = '{schema}' "
            f"AND table_name = 'work_item_violations' AND column_name = 'target_id';"))
        if has_target_id:
            rows = _query(
                f"SELECT violation, slug, coalesce(detail,''), target_id "
                f"FROM {schema}.work_item_violations ORDER BY violation, slug;")
        else:
            rows = [(v, s, d, None) for v, s, d in _query(
                f"SELECT violation, slug, coalesce(detail,'') FROM {schema}.work_item_violations "
                f"ORDER BY violation, slug;")]
        if rows:
            debt_lines.append(f"WORK ITEM VIOLATIONS ({schema}.work_item_violations) -- {len(rows)} row(s):")
            for violation, slug, detail, target_id in rows:
                if target_id is not None:
                    # s37: every violations-view member is answerable now (debt until answered,
                    # record forever) -- this is the discharge path, not "escalate to the
                    # maintainer" (that text was WRONG for a class that is legal-and-surfaced by
                    # design, consult A6(i)'s own finding).
                    hint = (f"answer it: ./led work resolve-violation {target_id} "
                             f"<reissued|retired> \"<basis>\" "
                             f"(--review-witness <ref> | --review-deferred) "
                             f"[--witness <successor-ref>] -- debt until answered, record forever "
                             f"(kernel/lineage/s37-violation-disposition.sql)")
                elif violation == "depends_on_unknown_slug":
                    hint = (f"open the missing antecedent (./led work open <antecedent-slug> "
                             f"\"<title>\"), or correct the typo'd dependency -- {detail}")
                elif violation == "dependency_cycle":
                    hint = ("break the cycle: review ./led work list / ./led work violations for "
                             "slug '" + slug + "' and record a corrected dependency -- no single "
                             "command resolves a cycle automatically (pre-s37 world: no answering "
                             "act exists yet -- apply kernel/lineage/s37-violation-disposition.sql)")
                else:
                    # duplicate_open / shipped_without_witness are provably vacuous under normal
                    # operation (refused at insert by the s22 kernel trigger/CHECK) -- seeing one
                    # here indicates a kernel anomaly, not a normal debt item. (pre-s37 world only
                    # -- see has_target_id branch above for the post-s37 discharge-path hint.)
                    hint = ("this violation class is normally refused at INSERT by the kernel -- "
                             "seeing it live indicates a kernel/trigger anomaly; escalate to the "
                             "maintainer rather than attempting a ledger fix (pre-s37 world: no "
                             "answering act exists yet -- apply kernel/lineage/"
                             "s37-violation-disposition.sql)")
                debt_lines.append(f"  - {violation}: slug '{slug}' ({detail}) -> {hint}")
                entries.append(f"violation:{violation}:{slug}:{detail}")

    # NAMED CHOICE (module docstring): work_review_gap is s29-only, same "check only what exists"
    # posture as work_item_current/work_item_violations above (s22). ENTRY PREFIX
    # work_review_deferred:<slug> is deliberately the CONVERSION partner of work_open:<slug> above
    # -- see `_debt_identity()`'s docstring for why (s29 Element B's own text).
    if _view_exists(schema, "work_review_gap"):
        rows = _query(f"SELECT slug, close_id FROM {schema}.work_review_gap ORDER BY slug;")
        if rows:
            debt_lines.append(f"DEFERRED REVIEW OBLIGATIONS ({schema}.work_review_gap) -- {len(rows)} item(s):")
            for slug, close_id in rows:
                debt_lines.append(
                    f"  - work item '{slug}' closed with --review-deferred (close row {close_id}) "
                    f"and has no distinct-actor attest yet ->\n"
                    f"      ./led review {close_id} <attest|attest_with_reservations|refuse> "
                    f"<technical|managerial|financial> \"<basis>\"   (written by a DIFFERENT actor)")
                entries.append(f"work_review_deferred:{slug}")

    return debt_lines, entries, info_lines


def _debt_identity(entry: str) -> str:
    """Normalizes an `entries` list item to its DEBT IDENTITY -- the underlying thing the debt is
    ABOUT, stripped of its current TYPE tag. Two entries with the same identity are the SAME debt
    that changed type (a CONVERSION, s29 Element B / kernel/lineage/s29-obligation-item-key-and-
    typed-close.sql), not new debt -- `_breaker_transition()` below inherits over an
    identity-subset exactly as it already inherits over a literal (string-identical) shrinkage.
    Today's one conversion pair: `work_open:<slug>` <-> `work_review_deferred:<slug>` (an item that
    closes with `--review-deferred` converts from "needs closing" debt to "needs a distinct-actor
    review" debt on the SAME slug -- s29's own header names this the CONVERSION case Element B's
    text predicts, quoted in this module's own docstring). Every other entry's identity is itself
    (no conversion partner is named yet for review_gap/question_status/violations entries)."""
    if entry.startswith("work_open:"):
        return "work:" + entry[len("work_open:") :]
    if entry.startswith("work_review_deferred:"):
        return "work:" + entry[len("work_review_deferred:") :]
    return entry


def _debt_hash(entries: list[str]) -> str:
    return hashlib.sha256("|".join(sorted(entries)).encode("utf-8")).hexdigest()


def _safe_prior_count(st: dict) -> int:
    """GUARDED (`stop-breaker-state-type-guard`, from the 0cd0a6f seam review, WITNESSED by
    direct test: an unguarded `st['count'] + 1` raises an uncaught TypeError when the on-disk
    state file holds a non-numeric count -- reachable only via external corruption/hand-edit
    (this hook itself only ever writes an int there), but the state file is plain JSON, so a
    truncated write or a hand-edit can leave any shape). A non-int (or a bool, which is
    technically an int subclass in Python but not a count this hook ever wrote) degrades to 0
    -- 'no prior count on record' -- exactly as a MISSING count already does via `st.get("count",
    0)`, never an uncaught exception escaping into `main()` and turning a Stop event into a
    traceback exit instead of the hook's documented exit-0/exit-2 contract."""
    val = st.get("count", 0)
    return val if isinstance(val, int) and not isinstance(val, bool) else 0


def _safe_prior_entries(st: dict) -> list[str] | None:
    """GUARDED (`stop-breaker-state-type-guard`): the STRICT-SUBSET inheritance rule
    (`_breaker_transition()` below, `stop-breaker-progress-reset-defect`) reads `st['entries']` --
    a field this hook itself only ever writes as a list of strings, but which an on-disk
    corruption/hand-edit (null, an int, a bare string, a dict) can leave wrong-typed. Returns the
    list iff it really is a list of strings; returns None -- 'no usable prior entries, behave as
    if this is a fresh signature' -- for anything else, mirroring `_load_apparatus_quiet()`'s and
    `_load_deployment_quiet()`'s own best-effort-degrade posture elsewhere in this file. This is
    the sole guarded read site for the field; `_breaker_transition()` never touches
    `st['entries']` directly."""
    val = st.get("entries")
    if isinstance(val, list) and all(isinstance(x, str) for x in val):
        return val
    return None


def _breaker_transition(st: dict, entries: list[str], debt_hash: str) -> int:
    """Compute the circuit breaker's count for THIS stop (module docstring, "BREAKER TRANSITION
    -- PROGRESS DOES NOT RE-ARM", `stop-breaker-progress-reset-defect`). The naive rule was
    "any debt-hash change resets to 1"; the fix inspects the SET, not just its hash: if the
    current entries are a STRICT SUBSET of the prior saved entries (every current entry was
    already open last time, at least one prior entry is now gone, and nothing new was added),
    the prior count is INHERITED (+1) -- progress never re-arms the blocker. An identical hash
    still inherits as before; a genuinely NEW entry (anything not in the prior set) still resets
    to 1, exactly as the original rule did -- this fix narrows the reset condition, it does not
    remove it. Reads `st['entries']`/`st['count']` only through the guarded accessors above
    (`stop-breaker-state-type-guard`), so a corrupted/wrong-typed state file degrades to
    'treat as a fresh signature' (count 1) rather than raising.

    DEBT-TYPE CONVERSION (s29, this module's own docstring quotes the spec's mandate verbatim):
    a SECOND, IDENTITY-NORMALIZED subset check (`_debt_identity()` above) runs alongside the
    literal one. Raw-string subset catches literal shrinkage (an entry disappears outright);
    identity subset ALSO catches an entry changing its TYPE TAG while naming the SAME underlying
    debt (`work_open:<slug>` becoming `work_review_deferred:<slug>` the moment that slug closes
    with `--review-deferred`) -- a case the raw-string check misses because neither string is a
    substring/subset of the other, even though nothing NEW happened. Both checks are tried; either
    inheriting is sufficient (a conversion is, by construction, never a case the literal check
    would have caught, so the two are complementary, not redundant)."""
    if st.get("debt_hash") == debt_hash:
        return _safe_prior_count(st) + 1

    prior_entries = _safe_prior_entries(st)
    if prior_entries is not None:
        cur_set = set(entries)
        prior_set = set(prior_entries)
        if cur_set and cur_set < prior_set:  # strict subset: progress, not new debt
            return _safe_prior_count(st) + 1

        cur_ids = {_debt_identity(e) for e in entries}
        prior_ids = {_debt_identity(e) for e in prior_entries}
        if cur_ids and cur_ids <= prior_ids:  # every current debt is a KNOWN identity (a
            # conversion of, or identical to, something already open) -- inherited, not new
            return _safe_prior_count(st) + 1

    return 1


def _load_state() -> dict:
    """GUARDED (`stop-breaker-state-type-guard`, generalized one level up from
    `_safe_prior_count()`/`_safe_prior_entries()`: those two guard individual FIELDS of the
    state dict; this guards the state dict's own TOP-LEVEL SHAPE). The on-disk file is plain
    JSON -- a hand-edit or truncated write can leave syntactically-valid JSON that is not an
    object at all (a bare `42`, `"corrupt"`, `[1, 2, 3]`). `json.load` happily returns that
    non-dict value, and every caller (`_breaker_transition()` first among them) calls
    `st.get(...)` on it -- an untyped-but-annotated `dict` return that is actually a str/list/int
    at runtime raises an uncaught AttributeError, the exact same 'traceback instead of the
    hook's documented exit-0/exit-2 contract' failure the field-level guards exist to foreclose,
    one layer up. Guarding it HERE, at the single load site, is the general form: every
    caller's `st: dict` contract is honestly enforced at its one boundary, rather than every
    caller re-checking `isinstance(st, dict)` for itself."""
    try:
        with open(STATE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_state(st: dict) -> None:
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f)
    os.replace(tmp, STATE)


def _clear_state() -> None:
    try:
        os.remove(STATE)
    except OSError:
        pass


def _block(reason: str) -> int:
    """Block the stop. Emits BOTH channels the Stop-hook contract offers (docs.claude.com/en/docs/
    claude-code/hooks): the top-level `decision`/`reason` JSON (the documented exit-0 mechanism)
    AND a plain-text reason on stderr with a non-zero exit (the documented exit-2 mechanism,
    version-independent of JSON support) -- the identical belt-and-braces posture
    hooks/pretooluse_change_gate.py's own `_deny()` already uses for cross-version reliability."""
    print(json.dumps({"decision": "block", "reason": reason}))
    print(reason, file=sys.stderr)
    return 2


def _allow_with_warning(reason: str) -> int:
    """Circuit breaker fired: ALLOW the stop (exit 0, no decision field) but print a loud warning
    to stderr so a human reading the transcript/logs sees it -- the compensating control for
    failing open on unclosable debt (module docstring)."""
    banner = (
        "\n" + "!" * 78 + "\n"
        "STOP-CLEAN-EXIT CIRCUIT BREAKER FIRED -- allowing this stop DESPITE open governance debt.\n"
        f"This debt set (or an unclosed remainder of it -- see BREAKER TRANSITION in the module "
        f"docstring) has now blocked {DEBT_REPEAT_LIMIT} consecutive stop attempts and is being "
        "let through as a last resort (fail-open by design -- see hooks/stop_clean_exit.py module "
        "docstring). A HUMAN MUST REVIEW THIS WORLD'S LEDGER:\n"
        + reason + "\n" + "!" * 78 + "\n"
    )
    print(banner, file=sys.stderr)
    return 0


def _journal(rec: dict) -> None:
    """Journaling is unconditional across ALL FOUR outcome paths (clean allow, observe
    would-block, enforce block, breaker fail-open) as of 2026-07-11 — the run-10 closure
    audit's class-b finding: enforce mode previously left NO durable trace of a block or a
    circuit-breaker event, an auditability gap under the maintainer's auditability-outranks-
    ergonomics ruling. Timestamps are UTC-Z per the unified hook-journal convention."""
    if not JOURNAL:
        return
    try:
        os.makedirs(os.path.dirname(JOURNAL), exist_ok=True)
        with open(JOURNAL, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _allow_with_observe_warning(reason: str, entries: list[str]) -> int:
    """`"observe"` mode (module docstring): never blocks the stop -- always allow (exit 0), but
    surface the SAME debt enumeration as a loud, non-blocking `additionalContext` warning (mirrors
    hooks/demurral_detect.py's own Stop-leg warning shape) plus a journal record. No circuit
    breaker here: this mode never blocks in the first place, so there is nothing for a breaker to
    eventually let through."""
    warning = ("[apparatus observe-mode WARNING] this world's ledger shows unfinished governance "
               "state -- would BLOCK this stop under clean_exit mode=enforce:\n\n" + reason)
    _journal({"ts": _ts(), "outcome": "observed_would_block", "entries": entries})
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": warning}}))
    return 0


def main() -> int:
    raw = sys.stdin.read()
    try:
        p = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # unparseable input -- nothing this hook can act on; allow (never the failure surface)

    try:
        _configure(p)
    except Exception:  # noqa: BLE001 -- a config-resolution bug must never trap a Stop event
        return 0

    if not WIRED:
        return 0  # unwired session: zero interference, by design (module docstring)

    if CLEAN_EXIT_MODE == "off":
        return 0  # apparatus.json switchboard: explicitly disabled even though this session IS
                  # wired -- distinct from "unwired" above, same zero-interference effect

    # STOP-DISPOSITION WARNING (module docstring): the hook input's own session id, the same
    # field hooks/stamp_intercept.py/hooks/stamp_provenance.py already read as `session_id`.
    # Resolved once here, consulted only on the ALLOW paths below -- never on `_block()`'s path.
    session_id = str(p.get("session_id") or "")

    try:
        debt_lines, entries, info_lines = _collect_debt(session_id)
    except Exception as e:  # noqa: BLE001 -- DB-unreachable posture (module docstring)
        debt_lines = [f"LEDGER UNREACHABLE ({type(e).__name__}): {e} -- check DB connectivity / "
                       f"GATE_SUBJECT_ROOT / deployment.json for this world, then retry."]
        entries = [f"error:{type(e).__name__}"]
        info_lines = []

    if not debt_lines:
        _clear_state()
        _journal({"ts": _ts(), "outcome": "clean_allow", "info": info_lines})
        if info_lines:
            # NAMED CHOICE -- STOP-GATE QUEUE SEMANTICS (module docstring): the queue/bequest
            # count is informational-only and never blocks -- printed plainly (no "decision"
            # field, no exit-2), so a truly empty world's silence stays byte-identical.
            print("\n".join(info_lines))
        _warn_stop_disposition(session_id)  # side effect only -- never changes this allow
        return 0  # all clean -- allow, zero interference for a clean world UNLESS the
                  # informational queue line or the stop-disposition warning above just fired

    debt_hash = _debt_hash(entries)
    st = _load_state()
    count = _breaker_transition(st, entries, debt_hash)

    reason = (
        "Ledger policy (clean-exit gate, hooks/stop_clean_exit.py): this world's ledger shows "
        "unfinished governance state -- this gate blocks the stop until it is clean, until the "
        "named items below are bequeathed via a stopping-disposition row, or until this gate "
        f"fails open after {DEBT_REPEAT_LIMIT} identical attempts as a last resort (CLAUDE.md "
        "point 5: \"Done means ./led review-gap, question-status, and ./led work violations are "
        "all clean.\"). Close each item below, or bequeath a claimed item to a successor "
        "(./led decision \"stopping: <why>; remains: <slug>\"), THEN try to stop again -- this "
        "gate re-checks on every attempt. "
        f"(this debt set, or an unclosed remainder of it, has now been seen "
        f"{count}/{DEBT_REPEAT_LIMIT} times at stop)\n\n"
        + "\n".join(debt_lines)
    )

    if CLEAN_EXIT_MODE == "observe":
        rc = _allow_with_observe_warning(reason, entries)
        if info_lines:
            print("\n".join(info_lines))
        _warn_stop_disposition(session_id)  # side effect only -- observe mode already never blocks
        return rc

    if count >= DEBT_REPEAT_LIMIT:
        _save_state({"debt_hash": debt_hash, "count": count, "entries": entries})
        _journal({"ts": _ts(), "outcome": "breaker_fail_open", "count": count, "entries": entries})
        rc = _allow_with_warning(reason)
        if info_lines:
            print("\n".join(info_lines))
        _warn_stop_disposition(session_id)  # side effect only -- breaker already fired to allow
        return rc

    _save_state({"debt_hash": debt_hash, "count": count, "entries": entries})
    _journal({"ts": _ts(), "outcome": "blocked", "count": count, "entries": entries})
    return _block(reason)  # turn is NOT ending here -- stop-disposition is not yet consulted;
                            # the successor attempt (once this debt clears) re-enters an ALLOW path


if __name__ == "__main__":
    sys.exit(main())
