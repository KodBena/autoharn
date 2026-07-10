#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-10T19:38:38Z
#   last-change: 2026-07-10T20:47:58Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

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
  - work_item_current     : work items with state='open' (s22; see NAMED CHOICE below).
  - work_item_violations  : duplicate_open / shipped_without_witness / depends_on_unknown_slug /
                            dependency_cycle rows (s22; same NAMED CHOICE).
If every check that APPLIES to this world is empty, the stop is ALLOWED (silently -- exit 0, no
output; a clean world sees zero interference from this hook, every single time). If ANY check is
non-empty, the stop is BLOCKED with a message enumerating exactly what is open, by id/slug, each
paired with the concrete command that closes it -- the same fix-point-ergonomics posture
`hooks/pretooluse_change_gate.py`'s DENY_HINT already uses: the refusal IS the loop's feedback
channel, so it must name the next command, never just the policy.

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
handed to whoever reads the transcript next). Any CHANGE in the debt fingerprint (the agent closed
something, even if new debt appeared) resets the counter to 1 -- the breaker only fires on
genuinely repeated, unchanged debt, never on ordinary multi-step progress. A clean stop also
clears the state file, so an old fingerprint never leaks into an unrelated future debt episode.

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
import subprocess
import sys
from datetime import datetime

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


def _collect_debt() -> tuple[list[str], list[str]]:
    """Read every governance check that applies to this world. Returns (debt_lines, entries):
    `debt_lines` is the human-readable, per-item teach-text (one item per open row/violation,
    each paired with the command that closes it); `entries` is the same information in a stable,
    machine-comparable form used only to fingerprint the debt set for the circuit breaker.
    Raises on a genuine DB error -- the caller converts that into the ledger_unreachable category."""
    schema = _ledger_schema()
    debt_lines: list[str] = []
    entries: list[str] = []

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
    if _view_exists(schema, "work_item_current"):
        rows = _query(
            f"SELECT slug, (claimant IS NOT NULL) FROM {schema}.work_item_current "
            f"WHERE state = 'open' ORDER BY slug;")
        if rows:
            debt_lines.append(f"OPEN WORK ITEMS ({schema}.work_item_current, state=open) -- {len(rows)} item(s):")
            for slug, has_claimant in rows:
                if has_claimant == "t":
                    debt_lines.append(
                        f"  - work item '{slug}' is open and claimed ->\n"
                        f"      ./led work close {slug} <shipped|superseded|dropped|deferred> "
                        f"[--witness <ref>]")
                else:
                    debt_lines.append(
                        f"  - work item '{slug}' is open and UNCLAIMED ->\n"
                        f"      ./led work claim {slug}   (then ./led work close {slug} "
                        f"<resolution> [--witness <ref>])")
                entries.append(f"work_open:{slug}")

    if _view_exists(schema, "work_item_violations"):
        rows = _query(
            f"SELECT violation, slug, coalesce(detail,'') FROM {schema}.work_item_violations "
            f"ORDER BY violation, slug;")
        if rows:
            debt_lines.append(f"WORK ITEM VIOLATIONS ({schema}.work_item_violations) -- {len(rows)} row(s):")
            for violation, slug, detail in rows:
                if violation == "depends_on_unknown_slug":
                    hint = (f"open the missing antecedent (./led work open <antecedent-slug> "
                             f"\"<title>\"), or correct the typo'd dependency -- {detail}")
                elif violation == "dependency_cycle":
                    hint = ("break the cycle: review ./led work list / ./led work violations for "
                             "slug '" + slug + "' and record a corrected dependency -- no single "
                             "command resolves a cycle automatically")
                else:
                    # duplicate_open / shipped_without_witness are provably vacuous under normal
                    # operation (refused at insert by the s22 kernel trigger/CHECK) -- seeing one
                    # here indicates a kernel anomaly, not a normal debt item.
                    hint = ("this violation class is normally refused at INSERT by the kernel -- "
                             "seeing it live indicates a kernel/trigger anomaly; escalate to the "
                             "maintainer rather than attempting a ledger fix")
                debt_lines.append(f"  - {violation}: slug '{slug}' ({detail}) -> {hint}")
                entries.append(f"violation:{violation}:{slug}:{detail}")

    return debt_lines, entries


def _debt_hash(entries: list[str]) -> str:
    return hashlib.sha256("|".join(sorted(entries)).encode("utf-8")).hexdigest()


def _load_state() -> dict:
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
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
        f"The identical debt set below has now blocked {DEBT_REPEAT_LIMIT} consecutive stop "
        "attempts and is being let through as a last resort (fail-open by design -- see "
        "hooks/stop_clean_exit.py module docstring). A HUMAN MUST REVIEW THIS WORLD'S LEDGER:\n"
        + reason + "\n" + "!" * 78 + "\n"
    )
    print(banner, file=sys.stderr)
    return 0


def _journal(rec: dict) -> None:
    if not JOURNAL:
        return
    try:
        os.makedirs(os.path.dirname(JOURNAL), exist_ok=True)
        with open(JOURNAL, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def _allow_with_observe_warning(reason: str, entries: list[str]) -> int:
    """`"observe"` mode (module docstring): never blocks the stop -- always allow (exit 0), but
    surface the SAME debt enumeration as a loud, non-blocking `additionalContext` warning (mirrors
    hooks/demurral_detect.py's own Stop-leg warning shape) plus a journal record. No circuit
    breaker here: this mode never blocks in the first place, so there is nothing for a breaker to
    eventually let through."""
    warning = ("[apparatus observe-mode WARNING] this world's ledger shows unfinished governance "
               "state -- would BLOCK this stop under clean_exit mode=enforce:\n\n" + reason)
    _journal({"ts": datetime.now().isoformat(timespec="milliseconds"),
              "outcome": "observed_would_block", "entries": entries})
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

    try:
        debt_lines, entries = _collect_debt()
    except Exception as e:  # noqa: BLE001 -- DB-unreachable posture (module docstring)
        debt_lines = [f"LEDGER UNREACHABLE ({type(e).__name__}): {e} -- check DB connectivity / "
                       f"GATE_SUBJECT_ROOT / deployment.json for this world, then retry."]
        entries = [f"error:{type(e).__name__}"]

    if not debt_lines:
        _clear_state()
        return 0  # all clean -- allow, silently, zero interference for a clean world

    debt_hash = _debt_hash(entries)
    st = _load_state()
    count = (st.get("count", 0) + 1) if st.get("debt_hash") == debt_hash else 1

    reason = (
        "Ledger policy (clean-exit gate, hooks/stop_clean_exit.py): this world's ledger shows "
        "unfinished governance state -- the turn cannot end until it is clean (CLAUDE.md point 5: "
        "\"Done means ./led review-gap, question-status, and ./led work violations are all "
        "clean.\"). Close each item below, THEN try to stop again -- this gate re-checks on every "
        f"attempt, so retrying after closing the debt is the whole fix. "
        f"(this identical debt set has now been seen {count}/{DEBT_REPEAT_LIMIT} times at stop)\n\n"
        + "\n".join(debt_lines)
    )

    if CLEAN_EXIT_MODE == "observe":
        return _allow_with_observe_warning(reason, entries)

    if count >= DEBT_REPEAT_LIMIT:
        _save_state({"debt_hash": debt_hash, "count": count})
        return _allow_with_warning(reason)

    _save_state({"debt_hash": debt_hash, "count": count})
    return _block(reason)


if __name__ == "__main__":
    sys.exit(main())
