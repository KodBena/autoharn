#!/usr/bin/env python3
"""hooks/posttooluse_error_recurrence.py -- the SELF-TRIGGERING half of the error-capture
discipline (design/FABLE-ERROR-RECURRENCE-HOOK-SPEC.md, ledger row 1697; the manual half --
"cross-check the ledger for a `defect:` prior before fixing anything new" -- is
user-guide/USER-RECIPES-FAQ.md's "Capturing errors so they cannot quietly recur" section,
ADR-0000/ADR-0011). Named there as NOT built ("a Claude Code hook that observes an error signal
and itself runs the cross-check ... does not exist"), filed as ledger row 1696, built here on the
maintainer's 2026-07-19 instruction superseding that hold.

WHAT THIS DOES, ONE SENTENCE: on a PostToolUse(Bash) result whose stdout/stderr text matches one
of a small, ENUMERATED error signature (below), read-only-query this world's ledger for `defect:`
rows (the FAQ's grammar: `defect: <CLASS-SLUG> | <SPECIMEN> | <FORECLOSING-FIX> | <REFS>`, written
as a `decision`-kind row) whose CLASS-SLUG or SPECIMEN text look like this error, and if any do,
print their id/slug/foreclosing-fix plus one ADR-0011 teach-line to the session's own
`additionalContext` channel. DETECTIVE CONTROL ONLY (spec verbatim): never blocks, never writes a
ledger row, never polices -- it can only make an existing prior more visible, never enforce
anything.

THE ONE HARD SAFETY RULE THIS BUILD IS SHAPED BY (CLAUDE.md's standing "never modify hooks/ ...
while a live session runs there", restated in the spec's own "one hard safety rule" section):
hooks execute LIVE from this checkout, per invocation, in every session that runs here. This file
is therefore ADDITIVE-AND-INERT: a brand NEW file, gated internally by a brand NEW apparatus key
(`error_recurrence`) that defaults to fully inert (see APPARATUS.JSON SWITCHBOARD below) --
absent-or-"off" everywhere until an operator deliberately flips it -- and it is NOT wired into
this repo's own `.claude/settings.json`, nor into `bootstrap/templates/settings.json.tmpl` (the
template every NEW world's own settings.json is generated from). That second omission is
DELIBERATE, not an oversight: the spec's own "Apparatus + docs" step (point 4) names exactly two
template edits -- `bootstrap/templates/apparatus.json` (this mechanism's default MODE) and
`HOOKS.md.tmpl` (its documentation) -- and its "Build conditions" section closes the file list
with "New files only under hooks/ + the two template edits". `settings.json.tmpl` is not one of
those two, and WE6 (below) only claims the config default and the doc land in a fresh scaffold, not
that the new world's settings.json actually invokes this hook. Wiring the actual PostToolUse
dispatch line into `settings.json.tmpl` -- for this repo or for future worlds -- is therefore left
as an OPEN SEAM for a future, separately-ratified commission, not delivered by this build; see this
file's own "OPEN SEAM" note near the bottom of this docstring, and HOOKS.md.tmpl's own manual
wiring line for an operator who wants to arm it today.

DISPATCH/CONFIG CONVENTION -- mirrored, not reinvented, from hooks/posttooluse_bash_completion.py
(module-level MECHANISM_KEY constant, apparatus.json quiet-load, off/observe/enforce resolution
with a loud stderr warning on an unrecognized value, GATE_SUBJECT_ROOT-or-cwd subject-root
resolution) and hooks/posttooluse_mutation_observer.py (deployment_record-based PGHOST/PGDB/LEDGER
resolution, the env-var > deployment.json > hardcoded-default precedence). Every function below
that has a same-named sibling in one of those two files is intentionally byte-similar to it, not
imported (the standing "no load-bearing coupling across independently-touched hook files" posture
hooks/stop_clean_exit.py's own docstring already states, restated by mutation_observer.py's own
"WHY A SEPARATE RESOLUTION" section).

PAYLOAD SHAPE, AND HOW IT WAS DERIVED. `seen-red/hook-payload-contract/captured_posttooluse_bash.json`
is a real, live-captured PostToolUse(Bash) payload for a SUCCESSFUL command (banked 2026-07-14,
see that fixture's own docstring for its capture method) -- it establishes the shape this hook
reads: `tool_name`, `tool_input.command`, `tool_response.{stdout,stderr,interrupted,isImage,
noOutputExpected}`, `tool_use_id`, `session_id`, `cwd`. That fixture has no FAILING-command
example, so a second, ad hoc capture was run for this build (2026-07-19, same method that
fixture's own docstring documents: a scratch project under
`/tmp/claude-1000/.../scratchpad/hookcap{2,3,4,5}` with dump-to-file PreToolUse/PostToolUse hooks
on `*`, driven by headless `claude -p ... --permission-mode bypassPermissions` runs). RESULT,
WITNESSED THREE TIMES INDEPENDENTLY (`false` alone; `exit 7` alone; `echo x 1>&2; exit 1` alone;
each its own scratch project, each reproduced with an UNRESTRICTED PostToolUse matcher so a
different-shaped event firing instead would still have been caught): **PostToolUse never fires at
all for a Bash tool call whose own exit status is non-zero, in this harness version (Claude Code
2.1.214)** -- only PreToolUse fires; the harness's documented contract ("runs after a tool
completes successfully") holds exactly, not merely approximately. This is a REAL, NAMED RESIDUAL
GAP for the "non-zero exit of a governed verb" signature (below): on live Bash wiring, that branch
is presently unreachable via a command's OWN exit status -- there is no `tool_response` payload to
even inspect for those calls. It does NOT block this build (the commission's own witnessing method
is DIRECT INVOCATION with a synthesized payload, never live wiring -- see WITNESSES below, and this
gap is exactly why that witnessing method matters: a synthesized payload proves the hook's own
logic without depending on whether the harness would ever deliver a matching live payload). The
other two enumerated signatures (SQLSTATE line, gate-VIOLATIONS line) remain live-reachable any
time a Bash call's OWN exit is 0 but its stdout/stderr text still carries one of those markers
(e.g. a wrapper that captures a failing sub-command's output but itself exits 0) -- narrower than
the spec's own three-way list promised for live use, named honestly rather than glossed over.

ERROR SIGNATURES -- the small, ENUMERATED, documented list (spec: "not a general regex zoo"),
each grounded in a real, grep-verified convention already live in this project (see
`_ERROR_SIGNATURES` below for the compiled patterns):
  1. `sqlstate_refusal` -- the literal word `SQLSTATE`, case-insensitive. This project's own
     kernel-refusal teach-text convention: `serving/boundary_cli_client.py`'s
     `write_and_report()` prints "REFUSED by the kernel write boundary (SQLSTATE
     {verdict.get('sqlstate')}; ...)" on every kernel-level write refusal.
  2. `refused_line` -- the literal word `REFUSED`. The house-wide refusal-teach-text convention
     used by essentially every governed verb and gate in this project on its own failure path
     (grep-verified: `bootstrap/templates/led.tmpl`'s `led: REFUSED -- ...`,
     `serving/boundary_cli_client.py`'s three REFUSED branches, and a dozen-plus `gates/*.py`
     files' own `"<gate>: REFUSED -- ..."` lines, e.g. `gates/no_conflict_markers.py`,
     `gates/staging_guard.py`, `gates/cut_probe_inventory.py`).
  3. `gate_violations_line` -- `VIOLATIONS (` followed by a digit run and a close-paren, e.g.
     `LAZY-IMPORT VIOLATIONS (3):` (`gates/no_lazy_imports.py`'s own failure line) -- the gate
     failure-count convention several `gates/*.py` files share.
A payload matching NONE of the three is silent, by construction (WE5's own precision leg) -- no
ledger query is ever attempted for an ordinary success payload.

CROSS-CHECK MATCHING, DELIBERATELY DUMB IN V1 (spec verbatim: "ADR-0011 mints anything smarter on
witnessed misses"). From the matched signature's own LINE of text (not the whole payload -- see
`_matched_line()`), two independent, cheap comparisons against every `defect:` row this world's
ledger carries (kind='decision', statement `LIKE 'defect:%'`, read from `ledger_current` --
supersedes-aware, so an updated foreclosing-fix field is the one seen):
  - SLUG-TOKEN OVERLAP: the row's CLASS-SLUG, split on `-`, versus the matched line's own
    lowercase alphanumeric tokens (len >= 3) -- a HIT if at least `_SLUG_OVERLAP_THRESHOLD`
    (1/3) of the slug's own tokens appear in the matched line.
  - TRIGRAM SIMILARITY: character-trigram Jaccard similarity between the matched line and the
    row's SPECIMEN field -- a HIT if it clears `_TRIGRAM_THRESHOLD` (0.15).
Either comparison alone is sufficient (spec: "whose CLASS-SLUG OR specimen text matches").
Thresholds are named constants below, not tuned against any corpus -- exactly the "deliberately
dumb" posture the spec asks for; a witnessed miss is the trigger to improve them, not anticipation.

READ PATH, THE FALLBACK CHAIN (spec point 3: "the hook must not hang on a dead boundary -- short
timeout, then the legacy path, then fail-open"). Mirrors how a served world's boundary keys are
read by the rebased shims (`serving/boundary_cli_client.py`'s `load_served_config` -- optional
`boundary_url`/`boundary_deployment` fields on `deployment.json`, refused-if-absent BY THOSE
SHIMS, but here simply treated as "not available, fall back" since this hook must never refuse):
  1. BOUNDARY (only attempted when `deployment.json` carries both `boundary_url` AND
     `boundary_deployment`): a minimal, LOCAL `urllib` GET against `{boundary_url}/d/
     {boundary_deployment}/rows/current`, paginated by `after_id`, capped at
     `_BOUNDARY_MAX_PAGES` pages of `_BOUNDARY_PAGE_LIMIT` rows each, EACH REQUEST bounded by
     `_BOUNDARY_TIMEOUT_S` (5s, "short" -- deliberately shorter than the legacy leg's own 8s, so a
     dead boundary is abandoned quickly in favor of the leg more likely to answer). Written LOCAL
     to this file rather than reusing `serving/boundary_cli_client.py`'s own `get_all_rows`/`_http`
     (which hardcode a 65s per-request timeout with no override plumbed through) -- reusing it
     would silently violate the "short timeout" requirement this leg exists to satisfy; this is a
     small, disclosed, deliberate duplication (the same class `serving/boundary_cli_client.py`'s
     own `_ID_FIELD_OVERRIDE`/`_SLUG_FIELD_OVERRIDE` comment already names and accepts), NOT an
     import of a `serving/` module this hook has no business depending on for a 5s-bounded probe.
  2. LEGACY (`psql`, mirrors `hooks/posttooluse_mutation_observer.py`'s own query shape exactly):
     attempted whenever the boundary leg above did not run or did not answer. Bounded by
     `subprocess.run(..., timeout=8)` -- the same house convention every sibling hook's own DB
     query already uses; this is what makes WE4 (a bad host) fail FAST rather than hang on the
     OS's own multi-minute TCP connect timeout -- the bound is this hook's own, not psql's.
  3. FAIL-OPEN: if neither leg answers, one line to stderr naming that the cross-check did not
     run, and exit 0. Never a hang, never a block, never silent about its own failure (spec point
     2's "a detective control that silently dies is worse than none").

APPARATUS.JSON SWITCHBOARD. `mechanisms.error_recurrence.mode`, read once per invocation, same
off/observe/enforce three-state convention as every mode-gated mechanism in this project
(`bootstrap/templates/APPARATUS.md`). Default when the key or the whole file is absent/malformed:
**`"off"`** -- the ONE deliberate departure from the "costless observer defaults to observe" house
convention `bash_completion`/`mutation_observer`/`read_observer` all use, because THE ONE HARD
SAFETY RULE above requires this mechanism to be inert everywhere it has not been explicitly armed
(spec: "absent-or-off everywhere until an operator flips it"); `bootstrap/templates/apparatus.json`
ships `"observe"` as ITS OWN default so a fresh scaffold that copies that file verbatim starts
armed, but a world/checkout with no entry at all (this repo's own, forever, by this build's own
rule) stays inert. `"enforce"` is a NAMED-IMPOSSIBLE case, same shape as `mutation_observer`'s own
framing: this is PostToolUse (the mutation/error has already happened) AND the spec itself states
this mechanism is "detective control ONLY ... it never blocks" -- `"enforce"` in config warns
loudly on stderr and behaves as `"observe"`.

FAIL-OPEN, ALWAYS, EVERYWHERE: every except path in this file is silent to the tool call itself
(at most one stderr line on the cross-check's own failure, per spec point 2) -- a hook whose own
bug or DB hiccup could break an unrelated Bash call would be a far worse hazard than the detective
control it is trying to add.

Stdlib only, top-of-file imports (the lazy-import gate, gates/no_lazy_imports.py, applies).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)  # hooks/ -> autoharn root
sys.path.insert(0, os.path.join(_REPO_ROOT, "filing"))
import deployment_record  # noqa: E402  (filing/deployment_record.py, the ONE home for the deployment.json shape)

MECHANISM_KEY = "error_recurrence"
_VALID_MODES = ("off", "observe", "enforce")
_DEFAULT_MODE = "off"  # inert everywhere until an operator flips it -- see module docstring

_DEFAULT_PGHOST = "192.168.122.1"
_DEFAULT_PGDB = "nla"
_DEFAULT_LEDGER = "public.ledger"

FS = "\x1f"
RS = "\x1e"

# --- ERROR SIGNATURES (module docstring "ERROR SIGNATURES" section) ---------------------------
_ERROR_SIGNATURES: tuple[tuple[str, re.Pattern], ...] = (
    ("sqlstate_refusal", re.compile(r"\bSQLSTATE\b", re.IGNORECASE)),
    ("refused_line", re.compile(r"\bREFUSED\b")),
    ("gate_violations_line", re.compile(r"\bVIOLATIONS\s*\(\d+\)")),
)
_SCAN_CAP = 4000  # bytes of combined stdout+stderr actually scanned/tokenized -- bounded cost

# --- CROSS-CHECK matching thresholds (module docstring "CROSS-CHECK MATCHING" section) ---------
_SLUG_OVERLAP_THRESHOLD = 1.0 / 3.0
_TRIGRAM_THRESHOLD = 0.15
_TOKEN_RE = re.compile(r"[a-z0-9]+")

# --- boundary read leg bounds (module docstring "READ PATH" section) ---------------------------
_BOUNDARY_TIMEOUT_S = 5.0
_BOUNDARY_PAGE_LIMIT = 1000
_BOUNDARY_MAX_PAGES = 5
_LEGACY_TIMEOUT_S = 8


def _first(d, *keys: str, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return default


def _find_deployment_path(data: dict) -> str | None:
    """Mirrors hooks/posttooluse_mutation_observer.py's identically-named function exactly: an
    explicit LEDGER_DEPLOYMENT override first, else `<cwd>/deployment.json` using the hook
    input's own `cwd` field."""
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
        print("[apparatus] WARNING: mechanisms.error_recurrence.mode='enforce' is IMPOSSIBLE for "
              "this hook (a PostToolUse detective control that the spec itself binds to NEVER "
              "block/write/police); behaving as 'observe'. See "
              "hooks/posttooluse_error_recurrence.py module docstring.", file=sys.stderr)
        return "observe"
    if raw in _VALID_MODES:
        return raw
    print(f"[apparatus] WARNING: mechanisms.{MECHANISM_KEY}.mode={raw!r} in "
          f"{root}/.claude/apparatus.json is unrecognized (must be one of {_VALID_MODES}) -- "
          f"never widening permissions; falling back to {_DEFAULT_MODE!r}.", file=sys.stderr)
    return _DEFAULT_MODE


class _Config:
    """Every connection/config value resolved for ONE invocation -- mirrors
    hooks/posttooluse_mutation_observer.py's own `_configure()` shape, as an instance rather than
    module globals only because this file has no shared module-level mutable state to race
    against across the direct-invocation witnessing this build relies on (multiple `main()` calls
    in one test process, see the WE* witness scripts)."""

    def __init__(self, data: dict) -> None:
        dep_path = _find_deployment_path(data)
        dep = _load_deployment_quiet(dep_path) if dep_path else None
        using_deployment = bool(dep_path and dep)

        self.pghost = os.environ.get("LEDGER_HOST") or (dep.host if dep else None) or _DEFAULT_PGHOST
        self.pgdb = os.environ.get("LEDGER_DB") or (dep.db if dep else None) or _DEFAULT_PGDB
        self.ledger = (os.environ.get("GATE_LEDGER") or (f"{dep.schema}.ledger" if dep else None)
                       or _DEFAULT_LEDGER)
        self.boundary_url = dep.boundary_url if dep else None
        self.boundary_deployment = dep.boundary_deployment if dep else None

        env_subject_root = os.environ.get("GATE_SUBJECT_ROOT")
        default_root = os.path.dirname(dep_path) if using_deployment else (data.get("cwd") or "")
        self.subject_root = (os.path.abspath(env_subject_root or default_root)
                              if (env_subject_root or default_root) else "")
        self.wired = bool(self.subject_root and os.path.isdir(self.subject_root))

        apparatus = _load_apparatus_quiet(self.subject_root) if self.wired else {}
        self.mode = _resolve_mode(apparatus, self.subject_root)

    @property
    def ledger_schema(self) -> str:
        return self.ledger.rsplit(".", 1)[0] if "." in self.ledger else "public"


# --- signature scan ------------------------------------------------------------------------


def _combined_text(tool_response: dict) -> str:
    stdout = tool_response.get("stdout") if isinstance(tool_response, dict) else None
    stderr = tool_response.get("stderr") if isinstance(tool_response, dict) else None
    parts = [s for s in (stdout, stderr) if isinstance(s, str) and s]
    return "\n".join(parts)[:_SCAN_CAP]


def _detect_signature(text: str, tool_response: dict) -> tuple[str, str] | None:
    """Returns (signature_name, matched_line) for the FIRST enumerated signature that fires, or
    None. `matched_line` is the first line of `text` containing the match, truncated to 300
    chars -- the compact class signature the CROSS-CHECK below matches against."""
    for name, pattern in _ERROR_SIGNATURES:
        m = pattern.search(text)
        if not m:
            continue
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        if line_end == -1:
            line_end = len(text)
        return name, text[line_start:line_end][:300]
    # Defensive, forward-compatible fourth check: an explicit exit/return-code field, if the
    # payload ever carries one (module docstring: not observed live in this harness version,
    # exercised only via a synthesized payload -- see the WE* witnesses).
    if isinstance(tool_response, dict):
        for key in ("exit_code", "exitCode", "returncode", "return_code"):
            val = tool_response.get(key)
            if isinstance(val, int) and val != 0:
                return "nonzero_exit_field", f"{key}={val}"
    return None


# --- CROSS-CHECK matching -------------------------------------------------------------------


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(text.lower()) if len(t) >= 3}


def _trigrams(text: str) -> set[str]:
    norm = re.sub(r"\s+", " ", text.lower()).strip()
    return {norm[i:i + 3] for i in range(max(0, len(norm) - 2))}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _parse_defect_statement(statement: str) -> tuple[str, str, str] | None:
    """`defect: <CLASS-SLUG> | <SPECIMEN> | <FORECLOSING-FIX> | <REFS>` -> (slug, specimen, fix),
    or None for anything that does not parse (a malformed row is skipped, never crashes the
    cross-check -- spec point 2's "malformed rows" fail-open case)."""
    if not isinstance(statement, str):
        return None
    body = statement.strip()
    if not body.lower().startswith("defect:"):
        return None
    body = body[len("defect:"):].strip()
    fields = [f.strip() for f in body.split("|")]
    if len(fields) < 3:
        return None
    return fields[0], fields[1], fields[2]


def _matches(matched_line: str, slug: str, specimen: str) -> tuple[bool, float]:
    """(hit, score) -- score is the higher of the two comparisons, used only for ranking a
    multi-hit report; the hit itself only needs ONE comparison to clear its own threshold (spec:
    "CLASS-SLUG OR specimen text")."""
    line_tokens = _tokens(matched_line)
    slug_tokens = {t for t in slug.lower().split("-") if t}
    slug_score = (len(line_tokens & slug_tokens) / len(slug_tokens)) if slug_tokens else 0.0
    trigram_score = _jaccard(_trigrams(matched_line), _trigrams(specimen))
    hit = slug_score >= _SLUG_OVERLAP_THRESHOLD or trigram_score >= _TRIGRAM_THRESHOLD
    return hit, max(slug_score, trigram_score)


# --- read path -------------------------------------------------------------------------------


class _CrossCheckUnavailable(Exception):
    """Raised, never propagated past main() -- the ONE signal that neither read leg answered
    (module docstring "READ PATH", step 3: fail-open with exactly one stderr line)."""


def _read_defect_rows_boundary(cfg: _Config) -> list[tuple[int, str]] | None:
    """Returns the (id, statement) pairs for every `defect:` row visible via the served boundary,
    or None if the boundary leg was not attempted/did not answer within its short bound (never
    raises -- the legacy leg is the fallback, not an error path from this function's own
    caller's point of view)."""
    if not cfg.boundary_url or not cfg.boundary_deployment:
        return None
    base = f"{cfg.boundary_url}/d/{cfg.boundary_deployment}"
    out: list[tuple[int, str]] = []
    after_id = 0
    try:
        for _ in range(_BOUNDARY_MAX_PAGES):
            url = (f"{base}/rows/current?after_id={after_id}&limit={_BOUNDARY_PAGE_LIMIT}")
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=_BOUNDARY_TIMEOUT_S) as resp:
                if resp.status != 200:
                    return None
                page = json.loads(resp.read())
            if not isinstance(page, list) or not page:
                break
            for row in page:
                if not isinstance(row, dict):
                    continue
                if row.get("kind") == "decision" and isinstance(row.get("statement"), str) \
                        and row["statement"].strip().lower().startswith("defect:"):
                    rid = row.get("id")
                    if isinstance(rid, int):
                        out.append((rid, row["statement"]))
            after_id = page[-1].get("id", after_id)
            if len(page) < _BOUNDARY_PAGE_LIMIT:
                break
        return out
    except (urllib.error.URLError, OSError, TimeoutError, ValueError, json.JSONDecodeError):
        return None


def _read_defect_rows_legacy(cfg: _Config) -> list[tuple[int, str]]:
    """Raises on any DB error/timeout (caller converts to `_CrossCheckUnavailable`) -- mirrors
    hooks/posttooluse_mutation_observer.py's own query shape exactly (psql -tA -F FS -R RS)."""
    schema = cfg.ledger_schema
    sql = (f"SELECT id, statement FROM {schema}.ledger_current "
           f"WHERE kind = 'decision' AND statement LIKE 'defect:%' ORDER BY id;")
    out = subprocess.run(
        ["psql", "-h", cfg.pghost, "-d", cfg.pgdb, "-tA", "-F", FS, "-R", RS, "-c", sql],
        capture_output=True, text=True, timeout=_LEGACY_TIMEOUT_S, check=True,
    )
    rows: list[tuple[int, str]] = []
    for rec in out.stdout.split(RS):
        if not rec.strip():
            continue
        parts = rec.split(FS)
        if len(parts) < 2:
            continue
        try:
            rid = int(parts[0])
        except ValueError:
            continue
        rows.append((rid, parts[1]))
    return rows


def _read_defect_rows(cfg: _Config) -> list[tuple[int, str]]:
    """The fallback chain itself (module docstring "READ PATH"): boundary (short timeout) ->
    legacy (bounded timeout) -> `_CrossCheckUnavailable` (fail-open, one stderr line, caller's
    job)."""
    boundary_rows = _read_defect_rows_boundary(cfg)
    if boundary_rows is not None:
        return boundary_rows
    try:
        return _read_defect_rows_legacy(cfg)
    except Exception as e:  # noqa: BLE001 -- any DB/timeout/parse failure is "unavailable"
        raise _CrossCheckUnavailable(f"{e.__class__.__name__}: {e}") from e


# --- output ----------------------------------------------------------------------------------


def _emit_hits(hits: list[tuple[int, str, str, float]]) -> None:
    """`hits` = [(id, slug, foreclosing_fix, score), ...], already sorted best-first. Mirrors
    hooks/posttooluse_mutation_observer.py's own `additionalContext` emission shape exactly."""
    lines = [f"  - prior row {rid}: class {slug!r}, foreclosing-fix: {fix}"
             for rid, slug, fix, _ in hits]
    text = (
        "[error-recurrence NOTICE, observer-only -- never blocks] this tool result matches an "
        "error signature this world has seen before:\n"
        + "\n".join(lines)
        + "\nthis class has priors -- ADR-0011 says a recurrence mints a mechanical check."
    )
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse", "additionalContext": text}}))


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

        cfg = _Config(data)
        if not cfg.wired or cfg.mode == "off":
            return 0  # WE3: inert -- no signature scan, no ledger query, nothing touched

        tool_response = data.get("tool_response")
        if not isinstance(tool_response, dict):
            return 0
        text = _combined_text(tool_response)
        detected = _detect_signature(text, tool_response)
        if detected is None:
            return 0  # WE5: no signature match, no query
        _sig_name, matched_line = detected

        try:
            defect_rows = _read_defect_rows(cfg)
        except _CrossCheckUnavailable as e:
            print(f"[error-recurrence] cross-check did not run: {e}", file=sys.stderr)
            return 0  # WE4: fail-open, one stderr line, no hang, no block

        hits: list[tuple[int, str, str, float]] = []
        for rid, statement in defect_rows:
            parsed = _parse_defect_statement(statement)
            if parsed is None:
                continue  # malformed row -- skipped, never crashes the cross-check
            slug, specimen, fix = parsed
            is_hit, score = _matches(matched_line, slug, specimen)
            if is_hit:
                hits.append((rid, slug, fix, score))
        if not hits:
            return 0  # WE2: no hit -- silence

        hits.sort(key=lambda h: h[3], reverse=True)
        _emit_hits(hits)  # WE1: hit -- prior surfaced, never blocking
    except Exception:  # noqa: BLE001 -- a detective control must never break the tool call
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
