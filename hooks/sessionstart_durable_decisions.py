#!/usr/bin/env python3
"""sessionstart_durable_decisions -- the SessionStart mechanical half of design/
FABLE-GRADED-DECISIONS-SPEC.md (RATIFIED 2026-07-16, ledger item `graded-decisions-build`).

MOTIVATION (the spec's own Provenance, restated here for a zero-context reader of this file): a
`spy` root-cause analysis of a panel-deployment session (889df121-8ea9-49ca-a224-bad131076799)
found a standing decision (that deployment's own ledger rows 193/200) violated ~34 minutes after a
context-compaction event -- and `./pickup` could not have surfaced it, because its own
IN-FORCE-DECISIONS section is a recency-windowed `ORDER BY id DESC LIMIT 10` read, the same failure
shape a compacted context window has. This hook is the MECHANICAL re-assertion path: on every
SessionStart event whose `source` is `compact` (the witnessed failure surface) or `resume` (shares
its shape -- a `startup` session is expected to run `./pickup` per the resumption doctrine
instead, so `startup` is deliberately NOT wired here, see settings.json.tmpl's own SessionStart
matcher), it reads `standing_decisions` (kernel/lineage/s36-decision-grade.sql) filtered to this
deployment's configured grade set and injects id/grade/statement for each row into the freshly
rebuilt context.

WIRING / UNWIRED POSTURE (the SAME posture hooks/stop_clean_exit.py and hooks/
pretooluse_change_gate.py already establish, re-derived independently here): this hook is WIRED
for a session iff SUBJECT_ROOT is either an explicit `GATE_SUBJECT_ROOT` env var OR derived from a
located `<cwd>/deployment.json`, AND the resolved deployment record loads cleanly. Any other
session (autoharn's own bare checkout, a pre-existing world that predates this hook's rollout and
was never re-wired -- BACKLOG posture: "do not retroactively wire an existing world") is UNWIRED
and this hook returns exit 0 on the very first line of real work, before opening any connection --
zero interference, by construction, for every session that has not opted in. A WIRED session whose
kernel predates s36 (no `standing_decisions` view) degrades to the SAME fail-open path a genuinely
unreachable ledger takes -- see FAILS OPEN below; the spec's own element 3 language ("fails open
... if the ledger is unreachable") covers both: a schema that cannot answer this query is,
functionally, unreachable FOR THIS QUERY.

BYTE CAP, ITEM CAP, LOUD TRUNCATION (spec element 3; the no-silent-caps rule this project holds
everywhere else a display is capped): `apparatus.json` -> `mechanisms.standing_decisions.byte_cap`
(default 4000) bounds the TOTAL rendered size of the injected block, and `mechanisms.
standing_decisions.max_items` (default null -- no count limit, byte cap alone governs, unchanged
from before this key existed) additionally bounds the ROW COUNT. Both apply, independently:
whichever bites first truncates. Rows are included, oldest-first (id order), until the NEXT row
would exceed the byte cap OR `max_items` rows have already been shown; every row after that point
is represented ONLY by a trailing, IMPERATIVE line naming the count omitted and directing the
reader's next action -- `./led standing` -- never a silently truncated mid-row cut, never a
quietly dropped tail with no trace (ledger item `standing-injection-max-items`: an earlier,
parenthetical phrasing of this line was witnessed NOT being acted on by an agent reader). Compaction
happens because context is tight in the first place; an UNBOUNDED re-injection here would be
self-defeating -- the whole point is durability, not volume.

FAILS OPEN (spec element 3): a missing deployment record, an unreachable database, a pre-s36
schema (no `standing_decisions` view), or any other exception anywhere in this pipeline prints
EXACTLY ONE line to stderr naming the failure and exits 0 -- a context-hydration AID must never
block session start. This mirrors `hooks/stop_clean_exit.py`'s own `LEDGER UNREACHABLE` posture
for its debt-collection query, applied here to a read-only, best-effort context injection instead
of a blocking gate.

CONTEXT INJECTION SHAPE: `{"hookSpecificOutput": {"hookEventName": "SessionStart",
"additionalContext": <text>}}` printed to stdout on success -- the SAME shape `hooks/
stop_clean_exit.py`'s own `_allow_with_observe_warning`/`_warn_stop_disposition` already use for
Stop, applied here to SessionStart's own hookEventName. When there are zero standing decisions in
the configured grade set (a clean/new/ungraded world), this hook prints NOTHING and exits 0 --
zero interference for a world that has adopted no standing decisions yet, matching every other
hook's "quiet unless there is something to say" posture.

Stdlib only, top-of-file imports (the lazy-import gate, gates/no_lazy_imports.py, applies).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

# Eager, top-of-file sys.path insert + import (lazy imports banned) -- the identical pattern
# hooks/stop_clean_exit.py / hooks/pretooluse_change_gate.py already use to reach
# filing/deployment_record.py, the ONE home for the deployment.json shape (ADR-0012 P1).
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)  # hooks/ -> autoharn root
sys.path.insert(0, os.path.join(_REPO_ROOT, "filing"))
import deployment_record  # noqa: E402  (filing/deployment_record.py, the ONE home for the shape)
import standing_decisions_config  # noqa: E402  (filing/standing_decisions_config.py, the ONE home
                                   # for the grades/byte_cap defaulting logic -- see that module's
                                   # own docstring NAMED CHOICE for why the mechs.get("standing_
                                   # decisions") EXTRACTION itself still happens here, not there)

_DEFAULT_PGHOST = "192.168.122.1"
_DEFAULT_PGDB = "nla"

# Field / record separators for psql -tA output -- the SAME ASCII US/RS convention hooks/
# stop_clean_exit.py's own _query() uses, so a decision statement containing a tab or newline
# cannot corrupt row parsing.
FS = "\x1f"
RS = "\x1e"


def _find_deployment_path(data: dict) -> str | None:
    """Locate this project's deployment.json: an explicit LEDGER_DEPLOYMENT override first, else
    `<cwd>/deployment.json` using the hook input's own `cwd` field -- the identical convention
    hooks/stop_clean_exit.py's own _find_deployment_path() already uses. Returns None -- never
    raises -- when neither resolves to an existing file."""
    explicit = os.environ.get("LEDGER_DEPLOYMENT", "")
    if explicit:
        return explicit
    cwd = data.get("cwd") or os.getcwd()
    candidate = os.path.join(cwd, "deployment.json")
    return candidate if os.path.isfile(candidate) else None


def _load_deployment_quiet(path: str) -> deployment_record.DeploymentRecord | None:
    """Best-effort deployment.json load. Never raises."""
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


def _resolve_standing_decisions_config(apparatus: dict) -> tuple[list[str], int, int | None]:
    """Extracts `apparatus["mechanisms"]["standing_decisions"]` HERE (the literal `mechs.get(
    "standing_decisions")` shape `filing/apparatus_registry.py`'s mechanical scan of hooks/*.py
    depends on -- see filing/standing_decisions_config.py's own docstring NAMED CHOICE), then
    hands the extracted entry to the ONE shared defaulting/validation home (ADR-0012 P1) --
    identical logic bootstrap/templates/pickup.tmpl's own STANDING-DECISIONS section shares."""
    mechs = apparatus.get("mechanisms")
    entry = mechs.get("standing_decisions") if isinstance(mechs, dict) else None
    return standing_decisions_config.resolve_standing_decisions_config(entry)


def _fetch_standing_decisions(dep: deployment_record.DeploymentRecord,
                               grades: list[str]) -> list[tuple[str, str, str]]:
    """Reads standing_decisions (kernel/lineage/s36-decision-grade.sql), filtered to `grades`,
    under `SET ROLE dep.role` (the granted subject role every led/pickup/hook read already uses --
    never the schema-owner connection identity). Raises on ANY failure (missing view on a pre-s36
    schema, connection refused, a malformed grades list producing no match, etc.) -- the caller's
    job is to turn that into the FAILS OPEN stderr note, exactly hooks/stop_clean_exit.py's own
    `_query()`/`_collect_debt()` split.

    `grades_csv` is bound via psql `-v` (a psql bind, not string concatenation -- P2: a boundary
    translates-and-validates untrusted text; it does not hand-splice it into a query), fed via
    stdin rather than `-c` -- psql's `:'var'` interpolation is only applied to a script read from
    stdin/-f, NOT to a `-c` argument (led.tmpl's own established note, reapplied here)."""
    grades_csv = ",".join(grades)
    sql = (
        f"SET ROLE {dep.role};\n"
        f"SELECT id, grade, statement FROM {dep.schema}.standing_decisions "
        f"WHERE grade = ANY(string_to_array(:'grades_csv', ',')) ORDER BY id;\n"
    )
    out = subprocess.run(
        ["psql", "-h", dep.host, "-d", dep.db, "-tA", "-F", FS, "-R", RS,
         "-v", "ON_ERROR_STOP=1", "-v", f"grades_csv={grades_csv}"],
        input=sql, capture_output=True, text=True, timeout=10, check=True,
    )
    # -t -A echoes one leading "SET\n" line for the preceding `SET ROLE` statement, glued directly
    # onto the FIRST row's own fields with no RS separator before it (verified empirically
    # authoring this hook -- the identical wart bootstrap/templates/pickup.tmpl's own
    # `_psql_tuples()` docstring already names and works around for `resources()`/`estimates()`/
    # etc: "-t -A echoes one leading line for the preceding SET ROLE statement -- drop exactly
    # that one line"). Same fix, applied to FS/RS-framed output instead of newline-framed: strip
    # the "SET\n" prefix from the raw stdout BEFORE splitting on RS, once, so it can never be
    # mistaken for (or corrupt) the first data row.
    stdout = out.stdout
    if stdout.startswith("SET\n"):
        stdout = stdout[len("SET\n"):]
    rows: list[tuple[str, str, str]] = []
    for rec in stdout.split(RS):
        if not rec.strip():
            continue
        parts = rec.split(FS)
        if len(parts) != 3:
            continue  # malformed record (should not happen with FS/RS framing) -- skip, don't crash
        rows.append((parts[0].strip(), parts[1].strip(), parts[2]))
    return rows


def _render(rows: list[tuple[str, str, str]], byte_cap: int, max_items: int | None) -> str:
    """Renders `id  grade  statement` lines, one per row, byte-capped at `byte_cap` with LOUD
    truncation (spec element 3: 'never silent') -- rows are taken IN ORDER (oldest-first; `rows`
    already arrives `ORDER BY id`) until the next row would push the rendered block over the cap
    OR `max_items` rows have already been shown, whichever bites first -- both guards are
    independent and both always apply; every row after that point is represented only by the
    trailing count-and-instruction line. Byte-counted on the UTF-8 encoding (never a character
    count, which can undercount a multi-byte statement)."""
    header = "Standing decisions (durable -- survive context loss; kernel/lineage/s36-decision-grade.sql):"
    lines = [header]
    budget = byte_cap - len(header.encode("utf-8")) - 1  # -1 for the header's own trailing newline
    shown = 0
    for row_id, grade, statement in rows:
        if max_items is not None and shown >= max_items:
            break
        line = f"{row_id}\t{grade}\t{statement}"
        cost = len(line.encode("utf-8")) + 1  # +1 for its own trailing newline
        if cost > budget:
            break
        lines.append(line)
        budget -= cost
        shown += 1
    remaining = len(rows) - shown
    if remaining > 0:
        # Imperative teach-text (ledger item standing-injection-max-items): the witnessed failure
        # was an agent reader that saw an aside naming `./led standing` and did not act on it. This
        # is a DIRECTIVE, not a footnote -- it names the count omitted and the reader's immediate
        # next action, kept to one line since this text itself lives inside the byte cap it polices.
        lines.append(f"ACTION REQUIRED: {remaining} more standing decision(s) omitted -- run "
                      f"`./led standing` NOW to read them before proceeding.")
    return "\n".join(lines)


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # unparseable input -- nothing this hook can act on; allow (never the failure surface)

    try:
        dep_path = _find_deployment_path(data)
        if not dep_path:
            return 0  # unwired session -- zero interference, by design (module docstring)
        dep = _load_deployment_quiet(dep_path)
        if dep is None:
            return 0  # unwired/malformed deployment.json -- same zero-interference posture

        root = os.path.dirname(dep_path)
        apparatus = _load_apparatus_quiet(root)
        grades, byte_cap, max_items = _resolve_standing_decisions_config(apparatus)

        rows = _fetch_standing_decisions(dep, grades)
    except Exception as e:  # noqa: BLE001 -- FAILS OPEN posture (module docstring): a
        # context-hydration aid must never block session start, whatever the underlying cause
        # (unreachable ledger, pre-s36 schema with no standing_decisions view, malformed config).
        print(f"[sessionstart_durable_decisions] LEDGER UNREACHABLE ({type(e).__name__}): {e} -- "
              f"standing decisions were NOT re-injected this session. Check DB connectivity / "
              f"this world's kernel lineage (kernel/lineage/s36-decision-grade.sql) / "
              f"GATE_SUBJECT_ROOT / deployment.json, then run `./led standing` by hand.",
              file=sys.stderr)
        return 0

    if not rows:
        return 0  # a clean/new/ungraded world -- zero interference, matching every other hook's
                  # "quiet unless there is something to say" posture

    context = _render(rows, byte_cap, max_items)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                              "additionalContext": context}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
