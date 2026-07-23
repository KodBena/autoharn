#!/usr/bin/env python3
"""role_brief.py -- print a role's derived BRIEF (the dynamic half of
design/FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md's "two halves"). Commission: ledger row 1663.

WHAT A "BRIEF" IS, per the governing spec: never authored, always COMPUTED at instantiation
time from the world's own views, scoped to the role's principal -- its in-force decisions, its
obligation debt (review_gap / work_review_gap where it is the obliged actor), open questions in
its concerns, its claimable work, and its standing (an ACTIVE line normally; a suspension is
surfaced LOUDLY with the suspending row's teaching -- an instance must learn it is suspended
from its own brief, not from its first refusal). "The brief is a read -- it grants nothing;
authority remains entirely the kernel's standing/binding facts" (spec's own "Honest limits").

NO RAW SQL: every section below is derived by parsing `led`'s own CLI text output (the aligned
`psql -c` table format for multi-row views, the expanded `psql -x` format for `led show`, and
the `|`-delimited `psql -tA` format for `led current`) -- never a direct psql connection. This
is the SAME "CLI-side derivation over objects that already exist" posture tools/role_charter.py
documents; see that file's own header for the shared parsing/scan-limit conventions this file
reuses (parse_current_line, STATEMENT scanning) without re-importing role_charter.py itself
(kept a standalone stdlib script per the spec's "Deliverables" list -- two files, not one with
a lazy cross-import).

TRANSPORT HONESTY (spec, deliverable 2): `--led` is ONE knob for every section, exactly the
convention tools/workflow_compile.py's generated drive.py already established for the SAME
work-family gap. It defaults to "./legacy/led" (never the served "./led") -- STALE REASONING,
NAMED (found and disclosed during the legacy-led-retirement Part C completion pass, 2026-07-23,
rather than silently carried): this docstring used to say the work-family verbs `led work
startable`/`led work review-gap` were NOT covered by the served boundary -- that gap CLOSED at
legacy-led-retirement phase 1B (ledger row 1149), before this note was ever corrected. The
REAL, live reason this default has not simply flipped to "./led" is DEEPER and still stands:
this file's own PARSERS (`parse_current_line`'s `id|kind|statement|actor_name` pipe format,
and the `psql -x`-shaped `-[ RECORD 1 ]---` scanner) are written against `bootstrap/templates/
legacy-led.tmpl`'s own specific OUTPUT SHAPES -- the served `bootstrap/templates/led.tmpl`
prints a DIFFERENT shape for the same data (`[id] kind: statement` for `--recent`/`current`;
`key : value` lines, no record-header, for `show`) that these parsers do NOT recognize. Pointing
this tool at the served `./led` today would not error -- it would SILENTLY MISPARSE (every
section reading empty or malformed), the exact vacuous-pass class this project's own doctrine
(F49) exists to catch. NOT FIXED in this same pass (a parser rewrite is its own, separately-
scoped piece of work, not a drive-by default flip) -- named here as an open, disclosed gap
rather than either silently left wrong or falsely claimed working. `--led` still defaults to
"./legacy/led"; passing "./led" is UNSUPPORTED until this parser gap is closed, not merely
untested. A deployment where only the served `./led` is reachable can still get the served-covered sections (STANDING, IN-FORCE DECISIONS, the
review_gap half of OBLIGATION DEBT, OPEN QUESTIONS) by passing `--led ./led` explicitly -- the
work-family sections will then fail loudly (this tool relays `led`'s own refusal/error text
verbatim, never silently omits a section) rather than serving a false empty section.

JUDGMENT CALLS THIS TOOL MAKES WHERE THE SPEC IS SILENT ON MECHANICS (mirroring
tools/workflow_compile.py's own J-notes and tools/role_charter.py's own JC-notes):

  JB1. CLAIMABLE WORK IS UNFILTERED. The spec's own text asks for "work_startable
       INTERSECTED WITH what the TOML/charter assigns it" -- but no kernel view or column ties a
       work_startable slug to an assignee principal at all (work_startable carries only
       slug/title; assignment only exists ephemerally, inside a COMPILED workflow-unit driver's
       own --role-map, never written back to the kernel). Silently narrowing this section by an
       invented heuristic (e.g. slug-text matching) would be exactly the kind of hazard CLAUDE.md
       asks to be named rather than routed around: a role could be shown LESS claimable work than
       actually exists, on the strength of a guess. This tool shows work_startable UNFILTERED and
       says so in the section header -- an honest full view, not a silently-narrowed false one.
       Revisit once a real slug-to-role assignment mechanism exists (a natural companion to a
       future ADR-0011 charter-registration kind).
  JB2. "OPEN QUESTIONS IN ITS CONCERNS" IS READ AS "OPEN QUESTIONS THIS ROLE ITSELF RAISED".
       The ledger's `concern` column is a coarse GLOBAL taxonomy (design|enactment|process|other),
       never principal-scoped -- nothing ties a concern category to a role. The only role-scoped
       reading question_status supports is by ACTOR (who raised the question), so that is what
       this section filters on: open (unanswered) `kind=question` rows whose actor is <role>.
  JB3. OBLIGATION-DEBT ROWS ARE RESOLVED TO AN ACTOR NAME VIA `led show`, NOT A NAME-TO-ID
       LOOKUP. `review_gap`/`work_review_gap` expose only the debt row's bigint actor id (no
       `led` verb resolves a bare name to an id) -- rather than inventing a second, unverified
       name<->id mapping, each candidate debt row is re-fetched with `led show <id>`, which
       already joins to the principal name (`actor_name`) the same way `led current` does. One
       extra `led show` call per debt row, bounded by how much debt exists, not by --scan-limit.
  JB4. STANDING IS DERIVED FROM STATEMENT TEXT, NOT A DEDICATED VIEW. No `led` verb exposes
       `principal_standing_current` (kernel/lineage/s40-principal-identity-events.sql's own
       human/SPA read surface) -- it is outside both the legacy tool's own subcommand surface and
       the served boundary's fourteen-route allowlist. This tool instead scans `led current
       <scan-limit>` for the newest (already supersession-resolved) `principal_suspended`/
       `principal_revoked` row whose fixed statement text names <role>
       ("principal '<role>' suspended -- standing withdrawn" / "principal '<role>' suspension
       lifted[: reason]" / a revoke's own statement) -- the exact statement shapes
       bootstrap/templates/legacy-led.tmpl's own suspend/lift-suspension/revoke branches write,
       verbatim. Bounded by --scan-limit exactly like tools/role_charter.py's own JC1.

Usage:
    python3 tools/role_brief.py brief <role> [--led PATH] [--scan-limit N]

Exit 0 on success (even when every section is empty -- "a role with nothing pending gets honest
empty sections, not absence", spec WB2). Exit 1 if a REQUIRED `led` read itself fails (relayed
verbatim). Exit 2 on a local usage error. Lazy imports banned; stdlib only.
"""
from __future__ import annotations

import re
import subprocess
import sys

DEFAULT_LED = "./legacy/led"
DEFAULT_SCAN_LIMIT = 100000

SUSPENDED_RE = re.compile(r"^principal '([^']+)' suspended")
LIFTED_RE = re.compile(r"^principal '([^']+)' suspension lifted")
REVOKED_RE = re.compile(r"^principal '([^']+)' revoked")


class BriefError(Exception):
    """Raised with a message explaining exactly why a required `led` read failed."""


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


def parse_current_line(line: str) -> tuple[int, str, str, str] | None:
    """id|kind|statement|actor_name -- the same `led current`/`led --recent` line shape
    tools/role_charter.py's own parse_current_line documents; duplicated rather than imported
    per this file's own header note (two standalone deliverables, no cross-import)."""
    parts = line.split("|")
    if len(parts) < 4:
        return None
    rid_s, kind, statement, actor_name = parts[0], parts[1], parts[2], "|".join(parts[3:])
    if not rid_s.isdigit():
        return None
    return int(rid_s), kind, statement, actor_name


def parse_psql_table(text: str) -> list[dict]:
    """Generic parser for `psql -c`'s default aligned table output (header row, a '-'/'+'
    separator row, data rows, a trailing '(N rows)' footer) -- shared by every multi-row `led`
    view read this file performs (review-gap, work review-gap, question-status, work startable).
    Never touches SQL; parses only `led`'s own already-printed CLI text."""
    rows: list[dict] = []
    header: list[str] | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("(") and (stripped.endswith("row)") or stripped.endswith("rows)")):
            continue
        if set(stripped) <= set("-+"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if header is None:
            header = cells
            continue
        if len(cells) != len(header):
            continue
        rows.append(dict(zip(header, cells)))
    return rows


def parse_psql_expanded(text: str) -> dict:
    """`psql -x`'s expanded output (led show's own format): '-[ RECORD 1 ]---' header line,
    then 'key | value' lines."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("-["):
            continue
        if "|" not in line:
            continue
        k, _, v = line.partition("|")
        out[k.strip()] = v.strip()
    return out


def section(title: str, provenance: str, lines: list[str]) -> str:
    body = "\n".join(f"  {ln}" for ln in lines) if lines else "  (none)"
    return f"## {title}\n(source: {provenance})\n{body}\n"


def build_standing_section(led: str, role: str, scan_limit: int) -> str:
    out = require_led(led, ["current", str(scan_limit)])
    newest_row: tuple[int, str] | None = None  # (id, disposition-text)
    for line in out.splitlines():
        parsed = parse_current_line(line)
        if not parsed:
            continue
        rid, kind, statement, _actor = parsed
        if kind == "principal_suspended":
            m = SUSPENDED_RE.match(statement) or LIFTED_RE.match(statement)
            if m and m.group(1) == role:
                if newest_row is None or rid > newest_row[0]:
                    newest_row = (rid, statement)
        elif kind == "principal_revoked":
            m = REVOKED_RE.match(statement)
            if m and m.group(1) == role:
                lines = [
                    f"REVOKED (row {rid}, TERMINAL -- dominates any suspension): {statement}",
                    f"  No lift path exists for a revocation (s40 Sec.3.4: revoked dominates "
                    f"suspended); this is a standing fact, not a refusal this tool issued.",
                ]
                return section(
                    "STANDING (leads: a suspension/revocation must be learned from the brief, "
                    "never only from a write refusal)",
                    f"ledger kind=principal_revoked, statement naming '{role}', via `led current "
                    f"{scan_limit}` (JB4)",
                    lines,
                )
    provenance = (
        f"ledger kind=principal_suspended (suspend AND lift-suspension both write this kind, "
        f"same-kind supersession, s45), statement naming '{role}', current row via `led current "
        f"{scan_limit}` (JB4)"
    )
    if newest_row is None:
        return section(
            "STANDING (leads: a suspension must be learned from the brief, never only from a "
            "write refusal)",
            provenance,
            [f"ACTIVE -- no suspend/lift/revoke event found for '{role}' in the last "
              f"{scan_limit} ledger_current rows."],
        )
    rid, statement = newest_row
    if SUSPENDED_RE.match(statement):
        lines = [
            f"SUSPENDED (row {rid}): {statement}",
            f"Writes under '{role}' are refused by the kernel until this is lifted. Lift path "
            f"(s45, by a DIFFERENT active principal): {led} principal lift-suspension {role}",
        ]
    else:
        lines = [f"ACTIVE (lifted at row {rid}): {statement}"]
    return section(
        "STANDING (leads: a suspension must be learned from the brief, never only from a write "
        "refusal)",
        provenance,
        lines,
    )


def build_decisions_section(led: str, role: str, scan_limit: int) -> str:
    out = require_led(led, ["current", str(scan_limit)])
    lines = []
    for line in out.splitlines():
        parsed = parse_current_line(line)
        if not parsed:
            continue
        rid, kind, statement, actor_name = parsed
        if actor_name == role:
            lines.append(f"row {rid} [{kind}]: {statement}")
    lines.sort(key=lambda ln: int(ln.split()[1]))
    return section(
        "IN-FORCE DECISIONS (rows where this role is the actor)",
        f"ledger_current via `led current {scan_limit}`, filtered actor='{role}'",
        lines,
    )


def build_obligation_section(led: str, role: str, scan_limit: int) -> str:
    lines = []
    rg_out = require_led(led, ["review-gap"])
    for row in parse_psql_table(rg_out):
        rid = row.get("id")
        if not rid or not rid.isdigit():
            continue
        show_out = require_led(led, ["show", rid])
        detail = parse_psql_expanded(show_out)
        if detail.get("actor_name") != role:
            continue
        lines.append(
            f"review_gap: row {rid} [{detail.get('kind', '?')}] undischarged "
            f"(scope={row.get('scope', '?')}, statement: {detail.get('statement', '?')})"
        )
    wrg_out = require_led(led, ["work", "review-gap"])
    for row in parse_psql_table(wrg_out):
        close_id = row.get("close_id")
        if not close_id or not close_id.isdigit():
            continue
        show_out = require_led(led, ["show", close_id])
        detail = parse_psql_expanded(show_out)
        if detail.get("actor_name") != role:
            continue
        lines.append(
            f"work_review_gap: slug={row.get('slug', '?')} close row {close_id} deferred and "
            f"undischarged (statement: {detail.get('statement', '?')})"
        )
    return section(
        "OBLIGATION DEBT",
        f"review_gap via `led review-gap` + work_review_gap via `led work review-gap`, each row "
        f"cross-resolved to actor_name='{role}' via `led show` (JB3)",
        lines,
    )


def build_questions_section(led: str, role: str, scan_limit: int) -> str:
    qs_out = require_led(led, ["question-status"])
    lines = []
    for row in parse_psql_table(qs_out):
        qid = row.get("question_id")
        answered = row.get("answered")
        if not qid or not qid.isdigit() or answered != "f":
            continue
        show_out = require_led(led, ["show", qid])
        detail = parse_psql_expanded(show_out)
        if detail.get("actor_name") != role:
            continue
        lines.append(
            f"row {qid} [{row.get('question_kind', '?')}] OPEN, concern={detail.get('concern') or '(none)'}: "
            f"{detail.get('statement', '?')}"
        )
    return section(
        "OPEN QUESTIONS IN ITS CONCERNS (read as: open questions this role itself raised -- JB2, "
        "no principal-scoped concern mechanism exists in the kernel schema)",
        f"question_status via `led question-status`, filtered answered=false and (via `led show`) "
        f"actor_name='{role}'",
        lines,
    )


def build_claimable_work_section(led: str, role: str, scan_limit: int) -> str:
    out = require_led(led, ["work", "startable"])
    lines = [f"{row.get('slug', '?')}: {row.get('title', '?')}" for row in parse_psql_table(out)]
    return section(
        "CLAIMABLE WORK (UNFILTERED -- JB1: no kernel mechanism ties a work_startable slug to a "
        "role assignment; shown in full rather than silently narrowed by a guess)",
        "work_startable via `led work startable`",
        lines,
    )


def cmd_brief(role: str, led: str, scan_limit: int) -> int:
    header = f"# BRIEF -- role '{role}' (computed now, via {led}, scan-limit={scan_limit})\n"
    sections = [
        build_standing_section(led, role, scan_limit),
        build_decisions_section(led, role, scan_limit),
        build_obligation_section(led, role, scan_limit),
        build_questions_section(led, role, scan_limit),
        build_claimable_work_section(led, role, scan_limit),
    ]
    print(header)
    for s in sections:
        print(s)
    return 0


def usage(msg: str | None = None) -> int:
    if msg:
        print(f"role_brief: {msg}", file=sys.stderr)
    print(
        "usage: python3 tools/role_brief.py brief <role> [--led PATH] [--scan-limit N]",
        file=sys.stderr,
    )
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
