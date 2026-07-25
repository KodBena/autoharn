#!/usr/bin/env python3
"""role_brief.py -- print a role's derived BRIEF (the dynamic half of
design/FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md's "two halves"). Commission: ledger row 1663;
served-parser rebuild commission: ledger row 1224.

A BRIEF is never authored, always COMPUTED at instantiation from the world's own views, scoped
to the role's principal: in-force decisions, obligation debt (review_gap/work_review_gap where
it is the obliged actor), open questions in its concerns, claimable work, and standing (a
suspension surfaces LOUDLY, with teaching, so an instance learns it is suspended from its own
brief, never only from its first refusal). "The brief is a read -- it grants nothing."

NO RAW SQL, NO DIRECT HTTP: every section is parsed off `led`'s own CLI text -- the same
CLI-side-derivation posture tools/role_charter.py documents (parse_current_line/JC1's
scan-limit discipline reused here without a cross-import -- two standalone deliverables).

TRANSPORT, AS OF THIS REBUILD (row 1224): `--led` defaults to "./led" (served,
bootstrap/templates/led.tmpl), matching role_charter.py. Parsers here are written against
led.tmpl's ACTUAL served shapes (read in full before this rewrite), never the retired direct-
psql shapes:
  - `led current <N>`/`--recent <N>`: `f"[{id}] {kind}: {statement}"` -- NO actor field at all
    (serving/boundary_service.py's /rows/current serves bare `ledger l.*`, no actor-name join;
    "no truth of its own").
  - `led show <id>`: `f"{k:28s}: {v}"` per non-null column, split on POSITION (identical to
    role_charter.py's own parse_served_show). Carries the raw `actor` id (never a name).
  - `led question-status`/`review-gap`/`work review-gap`/`work startable`: one
    `json.dumps(row, sort_keys=True)` line per row, NOT a psql table. `review_gap` carries
    `actor` direct (kernel/lineage/s57, unchanged since s32); `work_review_gap` carries
    `closer` direct (s31) -- neither needs a per-row `led show` to learn its actor (JB3).
    `question_status` (s31) carries NO actor at all -- a per-open-row `led show` is the only
    route (JB2), bounded by open-question count, not --scan-limit.

Every parser refuses LOUDLY, naming the missing/malformed field and the producing command, on
any shape it does not recognize -- never a silent empty section (F49's vacuous-pass class).

JUDGMENT CALLS (mirroring role_charter.py's own JC-notes):

  JB1. CLAIMABLE WORK IS UNFILTERED -- no kernel mechanism ties a work_startable slug to an
       assignee (assignment lives only ephemerally in a compiled workflow-unit's --role-map).
       Guessing by slug-text could show a role LESS work than exists; shown unfiltered, stated.
  JB2. "OPEN QUESTIONS IN ITS CONCERNS" = questions THIS ROLE RAISED. `concern` is a coarse
       global taxonomy, never principal-scoped; the only role-scoped read is by ACTOR, via
       `led show` per open row, compared to the role's resolved actor id (JB5).
  JB3. OBLIGATION-DEBT FILTERED BY ACTOR ID DIRECTLY OFF THE VIEW -- review_gap/work_review_gap
       already carry a bigint actor id (actor/closer); the legacy port's extra `led show`-per-
       candidate to LEARN an actor is gone. `led show` still runs per MATCHED row, but only for
       kind/statement DISPLAY, never the match itself.
  JB4. STANDING FROM STATEMENT TEXT, NOT A DEDICATED VIEW -- no `led` verb exposes
       principal_standing_current; scans `led current <scan-limit>` for the newest
       principal_suspended/principal_revoked row naming <role>, the exact fixed statement
       shapes led.tmpl's suspend/lift-suspension/revoke branches write (confirmed against
       source). Bounded by --scan-limit like role_charter.py's own JC1.
  JB5. RESOLVING <role> TO ITS ACTOR ID -- THE REAL GAP THIS REBUILD CLOSES. Every actor-scoped
       filter needs the role's bigint id; the served surface has no actor-name join anywhere.
       Real route: registration_write() writes each principal's birth event as a
       `principal_registered` row whose `principal_subject` IS the new principal's id,
       statement `"principal '<name>' registered (class <class>)"` (verified against source;
       matches role_charter.py's own principal_is_registered regex). resolve_role_actor_id
       scans `current` for that row (permanent, never superseded) then one `led show` for
       `principal_subject`. Replaces the retired parsers' silently-broken `actor_name` string
       comparison (a field the served surface never emits -- always False, collapsing every
       actor-scoped section to empty). No `principal_registered` event found is a REFUSAL
       (BriefError), not an empty brief.
       COST, DISCLOSED: build_decisions_section has no view/line carrying actor at all --
       filtering it costs ONE `led show` per scanned `current` row (O(scan-limit) round trips),
       flagged via a one-line stderr NOTE before the section runs. Real ledgers to date run low
       thousands of rows (seconds, not minutes); pass a smaller --scan-limit on an unusually
       large one.

Usage: python3 tools/role_brief.py brief <role> [--led PATH] [--scan-limit N]

Exit 0 on success (empty sections are honest, not absence). Exit 1 if a REQUIRED `led` read
fails, or a served shape does not match what a parser expects (never misparsed). Exit 2 on a
local usage error. Lazy imports banned; stdlib only.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys

from served_shapes import parse_current_line as _parse_current_line
from served_shapes import parse_served_show as _parse_served_show

DEFAULT_LED = "./led"
DEFAULT_SCAN_LIMIT = 100000

SUSPENDED_RE = re.compile(r"^principal '([^']+)' suspended")
LIFTED_RE = re.compile(r"^principal '([^']+)' suspension lifted")
REVOKED_RE = re.compile(r"^principal '([^']+)' revoked")
PRINCIPAL_REGISTERED_RE = re.compile(r"^principal '([^']+)' registered")


class BriefError(Exception):
    """Explains exactly why a required `led` read failed, or why a served shape did not match
    what this tool expected -- a loud, named refusal, never a silent misparse."""


def run_led(led: str, args: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run([led] + args, capture_output=True, text=True)
    except OSError as exc:
        # same conversion role_charter.py's own run_led performs -- a wrong --led path is an
        # ordinary, expected-shape failure, never an uncaught traceback.
        return 127, "", f"could not execute '{led}': {exc}"
    return proc.returncode, proc.stdout, proc.stderr


def require_led(led: str, args: list[str]) -> str:
    rc, out, err = run_led(led, args)
    if rc != 0:
        raise BriefError(f"'{led} {' '.join(args)}' failed:\n{(err or out).strip()}")
    return out


def parse_current_line(led_cmd_label: str, line: str) -> tuple[int, str, str]:
    """`led current <N>`/`led --recent <N>`: `[id] kind: statement`. No actor field exists on
    this line -- see JB5. Thin wrapper over served_shapes.parse_current_line, binding this
    tool's own BriefError as the raised type (role_charter.py binds CharterError instead --
    same shared parser, see tools/served_shapes.py)."""
    return _parse_current_line(BriefError, led_cmd_label, line)


def parse_served_show(led_cmd_label: str, text: str) -> dict[str, str]:
    """`led show <id>`: one `f"{k:28s}: {v}"` line per non-null field. Thin wrapper over
    served_shapes.parse_served_show (extracted this fix round -- see that module's own header
    for the fix-round finding and the long-key-name edge case this parser now handles), binding
    BriefError as the raised type."""
    return _parse_served_show(BriefError, led_cmd_label, text)


def parse_json_lines(led_cmd_label: str, text: str) -> list[dict]:
    """Served view/list commands print one `json.dumps(row, sort_keys=True)` object per line --
    NOT a psql aligned table (the retired tool's own shape these parsers used to assume). A line
    that fails to decode as a JSON object is a SHAPE DRIFT refused loudly, naming the offending
    command and line, rather than silently treating the section as empty."""
    rows: list[dict] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BriefError(f"SHAPE DRIFT -- `{led_cmd_label}` line {lineno} is not valid JSON "
                              f"(expected one JSON object per line); got {line!r}: {exc}")
        if not isinstance(obj, dict):
            raise BriefError(f"SHAPE DRIFT -- `{led_cmd_label}` line {lineno} decoded to a "
                              f"{type(obj).__name__}, not a JSON object: {obj!r}")
        rows.append(obj)
    return rows


def _actor_id_from_show(detail: dict[str, str], row_id, led_cmd_label: str) -> int | None:
    """The served `led show <id>`'s own `actor` column (a bigint FK), out of an already-parsed
    parse_served_show dict. None when the row genuinely has no actor (cmd_show prints only
    NON-NULL fields, so an absent key means a null column, not a shape drift). Raises
    BriefError if the field is PRESENT but not an integer -- a real shape drift."""
    if "actor" not in detail:
        return None
    raw = detail["actor"]
    if not raw.strip().lstrip("-").isdigit():
        raise BriefError(f"SHAPE DRIFT -- `{led_cmd_label}` row {row_id}'s 'actor' field is not an "
                          f"integer (got {raw!r}); 'actor' is a bigint FK. Refusing rather than "
                          f"silently skipping this row.")
    return int(raw)


def resolve_role_actor_id(led: str, role: str, scan_limit: int) -> int:
    """JB5: the role's OWN principal id, off its `principal_registered` birth event
    (registration_write(): `principal_subject` IS the new principal's id; statement is the
    fixed "principal '<name>' registered (class <class>)" text). Permanent, never superseded,
    so at most one match is expected; the first encountered is used."""
    led_cmd_label = f"{led} current {scan_limit}"
    out = require_led(led, ["current", str(scan_limit)])
    reg_row_id: int | None = None
    for line in out.splitlines():
        rid, kind, statement = parse_current_line(led_cmd_label, line)
        if kind != "principal_registered":
            continue
        m = PRINCIPAL_REGISTERED_RE.match(statement)
        if m and m.group(1) == role:
            reg_row_id = rid
            break
    if reg_row_id is None:
        raise BriefError(
            f"role '{role}' has no `principal_registered` event in the last {scan_limit} "
            f"ledger_current rows -- a brief cannot be scoped to a principal the ledger has "
            f"never actually registered (JB5; older than --scan-limit rows ago?). Register it "
            f"first:\n  {led} register-principal {role} <human|model|subagent|tool> --purpose \"...\"")
    show_cmd_label = f"{led} show {reg_row_id}"
    show_out = require_led(led, ["show", str(reg_row_id)])
    detail = parse_served_show(show_cmd_label, show_out)
    subj = detail.get("principal_subject")
    if subj is None or not subj.strip().lstrip("-").isdigit():
        raise BriefError(f"SHAPE DRIFT -- `{led} show {reg_row_id}` (principal_registered naming "
                          f"'{role}') carries no usable 'principal_subject' field (got {subj!r}); "
                          f"refusing rather than treating this role as having no actor id.")
    return int(subj)


def section(title: str, provenance: str, lines: list[str]) -> str:
    body = "\n".join(f"  {ln}" for ln in lines) if lines else "  (none)"
    return f"## {title}\n(source: {provenance})\n{body}\n"


STANDING_TITLE = ("STANDING (leads: a suspension/revocation must be learned from the brief, "
                   "never only from a write refusal)")


def build_standing_section(led: str, role: str, scan_limit: int) -> str:
    led_cmd_label = f"{led} current {scan_limit}"
    out = require_led(led, ["current", str(scan_limit)])
    newest_row: tuple[int, str] | None = None  # (id, disposition-text)
    for line in out.splitlines():
        rid, kind, statement = parse_current_line(led_cmd_label, line)
        if kind == "principal_suspended":
            m = SUSPENDED_RE.match(statement) or LIFTED_RE.match(statement)
            if m and m.group(1) == role:
                if newest_row is None or rid > newest_row[0]:
                    newest_row = (rid, statement)
        elif kind == "principal_revoked":
            m = REVOKED_RE.match(statement)
            if m and m.group(1) == role:
                lines = [f"REVOKED (row {rid}, TERMINAL -- dominates any suspension): {statement}",
                         "  No lift path exists for a revocation (s40 Sec.3.4); a standing fact, "
                         "not a refusal this tool issued."]
                return section(STANDING_TITLE,
                                f"ledger kind=principal_revoked, statement naming '{role}', via "
                                f"`led current {scan_limit}` (JB4)", lines)
    provenance = (f"ledger kind=principal_suspended (suspend/lift-suspension share this kind, "
                  f"s45), statement naming '{role}', current row via `led current {scan_limit}` "
                  f"(JB4)")
    if newest_row is None:
        return section(STANDING_TITLE, provenance,
                        [f"ACTIVE -- no suspend/lift/revoke event found for '{role}' in the last "
                         f"{scan_limit} ledger_current rows."])
    rid, statement = newest_row
    if SUSPENDED_RE.match(statement):
        lines = [f"SUSPENDED (row {rid}): {statement}",
                 f"Writes under '{role}' are refused until this is lifted. Lift path (s45, by a "
                 f"DIFFERENT active principal): {led} principal lift-suspension {role}"]
    else:
        lines = [f"ACTIVE (lifted at row {rid}): {statement}"]
    return section(STANDING_TITLE, provenance, lines)


def build_decisions_section(led: str, role: str, role_actor_id: int, scan_limit: int) -> str:
    print(f"role_brief: NOTE -- IN-FORCE DECISIONS filters by actor id; `current`/`--recent` "
          f"carry no actor field (JB5): issues one `led show` per scanned row, up to "
          f"--scan-limit={scan_limit}. Pass a smaller --scan-limit on a large ledger if slow.",
          file=sys.stderr)
    led_cmd_label = f"{led} current {scan_limit}"
    out = require_led(led, ["current", str(scan_limit)])
    lines = []
    for line in out.splitlines():
        rid, kind, statement = parse_current_line(led_cmd_label, line)
        show_cmd_label = f"{led} show {rid}"
        show_out = require_led(led, ["show", str(rid)])
        detail = parse_served_show(show_cmd_label, show_out)
        actor_id = _actor_id_from_show(detail, rid, show_cmd_label)
        if actor_id == role_actor_id:
            lines.append(f"row {rid} [{kind}]: {statement}")
    lines.sort(key=lambda ln: int(ln.split()[1]))
    return section("IN-FORCE DECISIONS (rows where this role is the actor)",
                    f"ledger_current via `led current {scan_limit}`, each row's actor resolved "
                    f"via `led show <id>` vs. '{role}''s own resolved actor id (JB5) -- served "
                    f"`current` carries no actor field to filter on directly", lines)


def build_obligation_section(led: str, role: str, role_actor_id: int, scan_limit: int) -> str:
    lines = []
    rg_out = require_led(led, ["review-gap"])
    for row in parse_json_lines(f"{led} review-gap", rg_out):
        if row.get("actor") != role_actor_id:
            continue
        rid = row.get("id")
        kind, statement = "?", "?"
        if rid is not None:
            detail = parse_served_show(f"{led} show {rid}", require_led(led, ["show", str(rid)]))
            kind, statement = detail.get("kind", "?"), detail.get("statement", "?")
        lines.append(f"review_gap: row {rid} [{kind}] undischarged (scope={row.get('scope', '?')}, "
                     f"assigned_by actor={row.get('assigned_by', '?')}, statement: {statement})")
    wrg_out = require_led(led, ["work", "review-gap"])
    for row in parse_json_lines(f"{led} work review-gap", wrg_out):
        if row.get("closer") != role_actor_id:
            continue
        close_id = row.get("close_id")
        statement = "?"
        if close_id is not None:
            statement = parse_served_show(
                f"{led} show {close_id}", require_led(led, ["show", str(close_id)])
            ).get("statement", "?")
        lines.append(f"work_review_gap: slug={row.get('slug', '?')} close row {close_id} deferred "
                     f"and undischarged (statement: {statement})")
    return section("OBLIGATION DEBT",
                    f"review_gap (actor, direct) + work_review_gap (closer, direct) filtered "
                    f"against '{role}''s own resolved actor id (JB5); matched rows re-fetched via "
                    f"`led show` for kind/statement display only (JB3)", lines)


def build_questions_section(led: str, role: str, role_actor_id: int, scan_limit: int) -> str:
    qs_out = require_led(led, ["question-status"])
    lines = []
    for row in parse_json_lines(f"{led} question-status", qs_out):
        if row.get("answered") is not False:
            continue
        qid = row.get("question_id")
        if qid is None:
            raise BriefError(f"SHAPE DRIFT -- `{led} question-status` row has no 'question_id': {row!r}")
        show_cmd_label = f"{led} show {qid}"
        detail = parse_served_show(show_cmd_label, require_led(led, ["show", str(qid)]))
        if _actor_id_from_show(detail, qid, show_cmd_label) != role_actor_id:
            continue
        lines.append(f"row {qid} [{row.get('question_kind', '?')}] OPEN, "
                     f"concern={detail.get('concern') or '(none)'}: {detail.get('statement', '?')}")
    return section("OPEN QUESTIONS IN ITS CONCERNS (read as: open questions this role itself "
                    "raised -- JB2, no principal-scoped concern mechanism exists)",
                    f"question_status (answered=false rows), each open row's actor resolved via "
                    f"`led show` vs. '{role}''s own resolved actor id (JB5) -- question_status "
                    f"itself carries no actor column", lines)


def build_claimable_work_section(led: str, role: str, scan_limit: int) -> str:
    rows = parse_json_lines(f"{led} work startable", require_led(led, ["work", "startable"]))
    lines = [f"{row.get('slug', '?')}: {row.get('title', '?')}" for row in rows]
    return section("CLAIMABLE WORK (UNFILTERED -- JB1: no kernel mechanism ties a work_startable "
                    "slug to a role assignment; shown in full rather than narrowed by a guess)",
                    "work_startable via `led work startable`", lines)


def cmd_brief(role: str, led: str, scan_limit: int) -> int:
    print(f"# BRIEF -- role '{role}' (computed now, via {led}, scan-limit={scan_limit})\n")
    standing = build_standing_section(led, role, scan_limit)
    # JB5: every remaining section is actor-id-scoped -- resolve ONCE, up front, so an
    # unregistered role refuses loudly before any section runs, not partway through the brief.
    role_actor_id = resolve_role_actor_id(led, role, scan_limit)
    for s in (standing, build_decisions_section(led, role, role_actor_id, scan_limit),
              build_obligation_section(led, role, role_actor_id, scan_limit),
              build_questions_section(led, role, role_actor_id, scan_limit),
              build_claimable_work_section(led, role, scan_limit)):
        print(s)
    return 0


def usage(msg: str | None = None) -> int:
    if msg:
        print(f"role_brief: {msg}", file=sys.stderr)
    print("usage: python3 tools/role_brief.py brief <role> [--led PATH] [--scan-limit N]",
          file=sys.stderr)
    return 2


def main(argv: list[str]) -> int:
    if not argv:
        return usage()
    sub = argv[0]
    rest = argv[1:]
    led = DEFAULT_LED
    scan_limit = DEFAULT_SCAN_LIMIT
    positional: list[str] = []
    i = 0
    while i < len(rest):
        a = rest[i]
        if a == "--led":
            if i + 1 >= len(rest):
                return usage("--led requires a value")
            led = rest[i + 1]
            i += 2
        elif a == "--scan-limit":
            if i + 1 >= len(rest):
                return usage("--scan-limit requires a value")
            try:
                scan_limit = int(rest[i + 1])
            except ValueError:
                return usage(f"--scan-limit value '{rest[i + 1]}' is not an integer")
            i += 2
        else:
            positional.append(a)
            i += 1

    if sub != "brief" or len(positional) != 1:
        return usage("'brief' takes exactly <role>")

    try:
        return cmd_brief(positional[0], led, scan_limit)
    except BriefError as exc:
        print(f"role_brief: REFUSED -- {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
