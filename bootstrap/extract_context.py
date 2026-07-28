#!/usr/bin/env python3
"""extract_context — the mechanized world-context extraction the world-context consult designed
(vestigial_documentation/design/FABLE-WORLD-CONTEXT-MIGRATION-CONSULT-2026-07-19.md, hereafter
"the consult"; ratifying commission autoharn ledger row 1942, sequencing step 1; lessons banked
by row 1943 folded in below). Two modes, one file, both READ-ONLY against any world OTHER than
their own explicit write target:

  extract  — READ-ONLY against the source world. SELECTs the source schema, classifies every
             operative item per the consult's §1 twelve-class taxonomy, and writes a MANIFEST
             file. Extraction NEVER writes to any world (row 1942's own trust condition: "carry
             runs from a maintainer-vetoable manifest"). No judgment beyond the CLASS-LEVEL
             default disposition is made here (consult §2.2: "curation is ingestion-side,
             attributed... extraction is mechanical and complete per class").

  ingest   — takes a REVIEWED manifest (a human has appended a {"record":"review","reviewed":
             true,...} line — the maintainer's veto surface, row 1942) and performs the writes
             through the TARGET deployment's own `led` (or `legacy/led`) binary, one call per
             carried item, LED_ACTOR set EXPLICITLY on every single invocation (row 1943 lesson
             (a): `led --json` injects no LED_ACTOR and the generic CLI path is the one this
             tool therefore uses throughout, with LED_ACTOR passed per-call, never inherited
             from the ambient environment). Refuses WHOLESALE — no partial run — if the manifest
             lacks the reviewed marker.

STANDING-FORCE SURVIVAL CLASSES (added 2026-07-28, work item extract-standing-force-classes,
per design/PHOENIX-SURVIVAL-UNIVERSE-2026-07-28.md -- the matrix the maintainer commissioned
after ADR-0000's "the class as first named is presumed too narrow" direction proved right
again): classes 1.13-1.19 carry every IN-FORCE (unsuperseded) principal-family side-table row
this tool previously ignored structurally, not merely deprioritized -- principal_suspended,
principal_revoked, principal_standing_declared, principal_relation_asserted,
principal_role_bound, principal_key_bound, principal_competence_granted. The matrix's #1-ranked
hazard is the reason this exists: a REVOKED principal's revocation not crossing the phoenix
means the successor world could functionally re-admit a revoked actor with no structural block.
Class 1.20 carries entitlement_class_configured (no principal referent -- see its own
docstring for why it defaults to drop-with-reason, not carry-reopened, despite being a genuine
standing-force class). Class 1.21 carries ungraded `resource:` statement-grammar rows (the
matrix's #2-ranked hazard: a `forbidden:`-tier deontic MUST-NOT, silently grade-filtered out of
1.2 whenever it isn't `--grade durable`). These items carry a `"principal_fields"` dict
(subject/object NAMES, never dust-world-local ids -- the successor's own roster is what
`led principal <verb>` resolves against at ingest) in place of 1.1's `actor_attribution` shape.
1.1's own `actor_attribution` now also carries `"purpose"` (the registration event's free-text
field) -- needed so ingestion can tell a benign birth-standard name duplicate from a genuine
identity collision (see `_compare_existing_principal` below).

FIX ROUND 2 (same work item, four independently witnessed defects closed): (1) `_rows()` now
fails LOUDLY on a nonzero psql exit instead of silently returning `[]` -- a query that references
a column absent on the source kernel's vintage used to look identical to "this world genuinely
has none of these rows"; `extract_principal_lifecycle`'s own SELECT is additionally shaped per
detected vintage so the s40-only kinds never reference an s41-only column in the first place.
(2) PROVENANCE SIDECAR: `led principal declare-standing`/`relate`/`bind-role`/`bind-key`/
`grant-competence` accept no free-text or --refs field, so a bare re-enactment through one of
them is byte-indistinguishable from a fresh maintainer act. Ingest now follows every such
successful re-enactment with a second, ordinary `decision` row (`--refs row:<new-id>`) narrating
"carried from `<world>` row `<id>` at phoenix ingest, `<timestamp>`" -- see
`_reenact_with_provenance` below; the ingest outcome line for these classes carries a
`"provenance_sidecar"` sub-record showing whether it landed. (3) A genuine principal-name
collision between the dust world's principal and an already-registered successor principal is
now DETECTED (the tool's original dedup check never matched any real refusal) and, when the two
identities differ, REFUSED loudly rather than silently treated as the same principal -- see
`_is_principal_name_collision`/`_compare_existing_principal`. (4) A carried `resource:` row's
statement keeps its grammar prefix verbatim (provenance moves to `--refs` only) so the tier
validator, pickup's RESOURCES reader, and this tool's own next-phoenix re-extraction all still
recognize it.

MANIFEST SHAPE (JSONL — one JSON object per line, per the consult §2.3's "provenance block plus
per-item records", chosen over a single nested JSON document so the file is greppable,
line-diffable, and appendable — the reviewed marker is literally appended by the reviewer, no
rewrite of prior lines):

  line 1            {"record": "provenance", ...}                 — written by extract, never by hand
  lines 2..N        {"record": "item", "class": "...", "disposition": ..., ...}
  appended by review {"record": "review", "reviewed": true, "reviewer": "...", "ts": "..."}

Disposition vocabulary (four values, fixed): "carry-verbatim" (RE-ASSERT in the consult's own
words — a fresh decision row restating the statement in full), "carry-reopened" (RE-ENACT — a
fresh typed act: principal registration, work item open, question re-ask), "drop-with-reason"
(CITE-ONLY — stays in the dust world, cited never carried; a reason names why), "never-class"
(NEVER — does not cross in any form; per this project's own house discipline, its payload is
NEVER PLACED IN THE MANIFEST AT ALL, not even as a citation, to make "provably absent" a
structural property rather than a policy one — see PAYLOAD-FREE CLASSES below).

PAYLOAD-FREE CLASSES, structural, not merely policy (§5's closed "what does NOT cross" list):
secrets (stamp secret, chain genesis seed) are NEVER QUERIED by this file at all — grep this
file; no SELECT here ever names a secret/seed column or table. Commission rows (kind=commission),
violation dispositions (work_violation_disposition), write refusals (write_refused), and snags
(snag) — the consult's §1.10/§1.12 NEVER classes plus the closed §5 list's "refusal/violation/
snag history and commission rows" — are recorded ONLY as a count and their dust row ids; their
`statement` text (and `rationale`, `evidence`, every other free-text column) is never read into
the manifest. Review rows (kind=review — discharges/countersigns, §1.7's CITE-ONLY default and
§5's "review discharges... never cross, credit and debt alike") get the same treatment: count and
ids only, drop-with-reason, no statement.

CLASSES EXTRACTED (of the consult's twelve; the rest are either not ledger-row-shaped at all —
§1.9 the git tree, §1.11 apparatus/settings — or have no current kernel machinery to query — §1.6
resources are ordinary decision rows already covered by 1.2, §1.8 estimates have no ledger `kind`
at all as of this kernel lineage; all of this is stated in the provenance block's own
`classes_out_of_scope` list, never silently omitted):
  1.1  principal roster            carry-reopened   kernel.principal
  1.2  standing decisions          carry-verbatim   <schema>.standing_decisions (subsumes 1.3's
                                                     procedures — this tool does not invent a
                                                     heuristic to split "ordinary rule" from
                                                     "invented procedure"; that judgment, if
                                                     wanted, is ingestion-side re-reading). PRE-S36
                                                     FALLBACK (row 1950): if standing_decisions
                                                     does not exist, every unsuperseded kind=
                                                     decision row in <schema>.ledger_current (s31
                                                     semantics) is carried the same way, grade
                                                     honestly null (no grade concept pre-s36), a
                                                     class-summary naming the widening -- see
                                                     extract_standing_decisions()'s own docstring
  1.4  open work items             carry-reopened   <schema>.ledger_current (work_opened) JOIN
                                                     <schema>.work_item_current WHERE state='open'
       + open work DEBT           drop-with-reason  work_review_gap / work_item_violations —
                                                     closure debt itself never crosses (§1.4/§5);
                                                     recorded so it is never silently absent
  1.5  open questions              carry-reopened   <schema>.question_status WHERE answered=false
  1.7  competence/track record     drop-with-reason  kind='review' — count+ids only, no statement
  1.10 commissions                 never-class      kind='commission' — count+ids only
  1.12 refusals/violations/snags   never-class      kind IN (write_refused, snag,
                                                     work_violation_disposition) — count+ids only
  1.13 principal suspensions       carry-reopened   in-force kind='principal_suspended' —
                                                     `led principal suspend` (added 2026-07-28,
                                                     see STANDING-FORCE SURVIVAL CLASSES above)
  1.14 principal revocations       carry-reopened   in-force kind='principal_revoked' —
                                                     `led principal revoke` — matrix's #1-ranked
                                                     hazard, this is the delta that closes it
  1.15 principal standing decls    carry-reopened   in-force kind='principal_standing_declared'
                                                     — `led principal declare-standing`
  1.16 principal relations         carry-reopened   in-force kind='principal_relation_asserted'
                                                     — `led principal relate`
  1.17 principal role bindings     carry-reopened   in-force kind='principal_role_bound' —
                                                     `led principal bind-role`
  1.18 principal key bindings      carry-reopened   in-force kind='principal_key_bound' —
                                                     `led principal bind-key`; CANNOT complete
                                                     without a fresh possession ceremony in the
                                                     SUCCESSOR world (s61 item 3) — see the
                                                     class's own docstring
  1.19 principal competences       carry-reopened   in-force kind='principal_competence_granted'
                                                     — `led principal grant-competence`
  1.20 entitlement class config    drop-with-reason kind='entitlement_class_configured' — NO
                                                     `led` verb writes this kind (only the birth
                                                     sequence's own direct kernel.ledger_write
                                                     call does); extracted for visibility, never
                                                     auto-ingested — see the class's own docstring
  1.21 resource: deontic tiers     carry-verbatim   ungraded kind='decision' rows whose statement
                                                     starts 'resource:' — matrix's #2-ranked
                                                     hazard, the eight statement grammars' one
                                                     genuine standing MUST-NOT (the TIER field);
                                                     the other seven grammars stay out of scope
                                                     (see CLASSES_OUT_OF_SCOPE 1.8, corrected below)

Read-only throughout: every query is a SELECT; ingest's own writes go through `led`, never a
direct psycopg INSERT (ADR-0012 P1: one write path, the kernel's own s43 boundary/legacy INSERT,
never a second hand-rolled one). Lazy imports banned (top-of-file only).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTOHARN = Path(os.environ.get("AUTOHARN", str(HERE / ".."))).resolve()

sys.path.insert(0, str(AUTOHARN / "filing"))
try:
    import deployment_record  # noqa: E402
except ImportError as _e:
    print(f"extract-context: cannot import autoharn's filing/deployment_record.py under "
          f"AUTOHARN={AUTOHARN} ({_e.__class__.__name__}: {_e})", file=sys.stderr)
    print("        set AUTOHARN=/path/to/autoharn, or place a sibling checkout at ../autoharn", file=sys.stderr)
    sys.exit(2)

TOOL_VERSION = "extract-context/1.0"

# Never queried, ever — grep-checkable structural absence (see module docstring).
_NEVER_QUERIED_COLUMNS = ("stamp_hmac", "stamp_session")  # named here ONLY for the negative-
# control test to cite; no SELECT anywhere in this file lists them, and none may be added.

NEVER_KINDS = ("commission", "work_violation_disposition", "write_refused", "snag")
DROP_KINDS = ("review",)

CLASSES_OUT_OF_SCOPE = {
    "1.3": "procedures are a subclass of 1.2 (standing decisions) with no distinct kernel "
           "representation; carried under class 1.2, not separately queried",
    "1.6": "resources registry has no distinct ledger `kind` — resource rows ride ordinary "
           "kind=decision rows. GRADED resource: rows are already covered by class 1.2's "
           "query; UNGRADED ones were silently dropped by 1.2's s36+ grade filter until this "
           "build — class 1.21_resource_tier_ungraded now extracts them separately (design/"
           "PHOENIX-SURVIVAL-UNIVERSE-2026-07-28.md sections 2/4, ranking #2). Corrected "
           "2026-07-28: the prior wording here ('already covered by 1.2's query') was "
           "imprecise in exactly the way that matrix names — true only of the GRADED subset.",
    "1.8": "estimate:/actual:/taxon:/interface:/outcome:/review:/review-done: rows have no "
           "DISTINCT ledger `kind` (ledger_kind_check carries no member for any of them) — "
           "but, corrected 2026-07-28 per design/PHOENIX-SURVIVAL-UNIVERSE-2026-07-28.md "
           "sections 2/4: they DO ride bare kind='decision' rows (led.tmpl's eight statement "
           "grammars, all written through cmd_generic), so they ARE nominally in scope of "
           "1.2's query and are silently GRADE-FILTERED out of it when ungraded, not "
           "kind-absent from it as the prior wording here ('nothing to SELECT') implied. Of "
           "the eight, only resource:'s TIER field carries a standing MUST-NOT (see 1.6, "
           "class 1.21) — the other seven stay genuinely out of scope here, named rather "
           "than silently dropped, because none carries a comparable standing-force hazard "
           "(matrix ranking #8: diagnostic-grade by maintainer ruling, lowest blast radius "
           "of the structural gaps this survey found).",
    "1.9": "domain artifacts (the git tree) are not ledger rows at all — crosses with the "
           "repository per consult §1.9, out of this tool's scope by construction",
    "1.11": "apparatus/settings/secrets are not ledger rows — settings are scaffold-time "
            "advice (consult §1.11), secrets are NEVER queried (see module docstring)",
}


# ---------------------------------------------------------------------------------- psql plumbing

def _load_deployment(path: Path):
    try:
        return deployment_record.load_deployment(path)
    except deployment_record.DeploymentError as e:
        print(f"extract-context: {e}", file=sys.stderr)
        sys.exit(2)


def _psql_tuples(dep, sql: str) -> subprocess.CompletedProcess:
    """SET ROLE <dep.role> first — this verb's honest job is "what can the OPERATING AGENT see",
    the SAME posture distance-to-clean.tmpl's own `_psql_tuples` already documents (ADR-0012 P1:
    reused convention, not re-derived). `--csv`, not `-t -A -F<delim>`: a real ledger statement
    routinely carries embedded newlines (found live against the `experience` world's own row
    397's multi-line resource declaration) that `-t -A`'s one-line-per-row assumption silently
    mis-splits into extra phantom rows -- `--csv`'s RFC-4180 quoting survives embedded newlines,
    commas, and the delimiter alike, parsed back out with the stdlib `csv` module below rather
    than a hand-rolled splitter that would need to reinvent the same quoting rules."""
    full = f"SET ROLE {dep.role};\n{sql}"
    return subprocess.run(
        ["psql", "-h", dep.host, "-d", dep.db, "--csv", "-v", "ON_ERROR_STOP=1", "-c", full],
        capture_output=True, text=True, timeout=60)


def _rows(r: subprocess.CompletedProcess) -> list[list[str]]:
    """Drop the echoed leading `SET` line (the SET ROLE statement's own one-word confirmation,
    psql's normal non-csv echo for a non-SELECT statement -- it precedes the CSV block, is never
    part of it) and the CSV block's own header row (column names), leaving just data rows.

    FAILS LOUDLY ON A NONZERO psql EXIT (fix round 2, finding 1 -- the class fix, not a one-off
    patch): every caller in this file funnels a SELECT's result through this one function, so
    this is the SINGLE choke point where "the query failed" and "the query returned zero rows"
    must never be conflated. Before this fix they WERE conflated -- `extract_principal_lifecycle`
    unconditionally selected s41-only columns (principal_object etc.) for kinds that are actually
    s40-native (principal_suspended/revoked/standing_declared); on an s40-only dust world psql
    errors on the unknown column, and this function, reading only `r.stdout` with no check of
    `r.returncode`/`r.stderr`, silently returned `[]` -- indistinguishable from "this world
    genuinely carries none of these rows". A revoked principal's revocation would vanish from
    the manifest with NO error printed anywhere: matrix hazard #1 reproduced through the
    extractor's OWN new code, the exact silent-loss shape this whole commission exists to close.
    The per-kind query shape is ALSO fixed at the call site (extract_principal_lifecycle no
    longer references a column absent on the detected vintage) -- this check is the second,
    independent net: ANY future query mistake in ANY class (not just lifecycle) now fails the
    whole run loudly instead of degrading to an empty, unremarkable-looking result."""
    if r.returncode != 0:
        print(f"extract-context: REFUSED -- a SELECT failed (psql exit {r.returncode}); "
              f"never treating this the same as a genuine empty result:\n{r.stderr.strip()}",
              file=sys.stderr)
        sys.exit(2)
    text = r.stdout
    if text.startswith("SET\n"):
        text = text[len("SET\n"):]
    rows = list(csv.reader(io.StringIO(text)))
    return rows[1:] if rows else []


def _column_exists(dep, table: str, column: str) -> bool:
    r = _psql_tuples(dep, f"SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                          f"WHERE table_schema = '{dep.schema}' AND table_name = '{table}' "
                          f"AND column_name = '{column}');")
    rows = _rows(r)
    return bool(rows) and rows[0][0] == "t"


def _relation_exists(dep, schema: str, relname: str) -> bool:
    r = _psql_tuples(dep, f"SELECT to_regclass('{schema}.{relname}') IS NOT NULL;")
    rows = _rows(r)
    return bool(rows) and rows[0][0] == "t"


# ------------------------------------------------------------------------------- provenance block

def _git(*args: str, cwd: Path) -> str:
    r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=str(cwd))
    return r.stdout.strip() if r.returncode == 0 else ""


def build_provenance(dep, deployment_path: Path, mode: str, extracting_principal: str) -> dict:
    project_root = deployment_path.parent
    total = _rows(_psql_tuples(dep, f"SELECT count(*), min(id), max(id) FROM {dep.schema}.ledger;"))
    row_count, row_min, row_max = (int(total[0][0]), total[0][1], total[0][2]) if total else (0, None, None)

    chain_head_id = chain_head_hash = None
    if _column_exists(dep, "ledger", "row_hash"):
        head = _rows(_psql_tuples(dep, f"SELECT id, row_hash FROM {dep.schema}.ledger_current "
                                       f"ORDER BY id DESC LIMIT 1;"))
        if head:
            chain_head_id, chain_head_hash = head[0][0], head[0][1]

    # root-shim-pruning residue sweep (ledger row 1357, 2026-07-27): a bare per-verb
    # `verify-chain` shim only exists next to deployment.json for a world scaffolded BEFORE the
    # §6 amendment (rows 1365/1366/1367) -- "a world scaffolded before this migration keeps its
    # ten shims untouched" (CLAUDE.md). A world scaffolded on/after that amendment has ONE
    # `autoharn` dispatcher instead; detect shape rather than assume either.
    vc_bare = project_root / "verify-chain"
    vc_dispatcher = project_root / "autoharn"
    if vc_bare.exists() and os.access(vc_bare, os.X_OK):
        vc_argv = [str(vc_bare)]
    elif vc_dispatcher.exists() and os.access(vc_dispatcher, os.X_OK):
        vc_argv = [str(vc_dispatcher), "verify-chain"]
    else:
        vc_argv = None
    if vc_argv is not None:
        r = subprocess.run(vc_argv, capture_output=True, text=True,
                            cwd=str(project_root), timeout=60)
        verify_chain_output = (r.stdout + r.stderr).strip()
    else:
        verify_chain_output = (f"UNAVAILABLE: no executable verify-chain shim and no autoharn "
                                f"dispatcher at {project_root}")

    return {
        "record": "provenance",
        "tool_version": TOOL_VERSION,
        "world_name": dep.name,
        "schema": dep.schema,
        "kern": dep.kern,
        "host": dep.host,
        "db": dep.db,
        "row_count": row_count,
        "row_span": [row_min, row_max],
        "chain_head_id": chain_head_id,
        "chain_head_hash": chain_head_hash,
        "verify_chain_output": verify_chain_output,
        "extracting_commit": _git("rev-parse", "HEAD", cwd=AUTOHARN) or "UNKNOWN",
        "extraction_mode": mode,
        "extracting_principal": extracting_principal,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "classes_out_of_scope": CLASSES_OUT_OF_SCOPE,
    }


# ---------------------------------------------------------------------------------- class queries

def extract_principals(dep) -> list[dict]:
    """1.1 Identity: the principal roster — carry-reopened (RE-ENACT).

    CARRIES `purpose` (fix round 2, finding 3): a re-registration attempt that collides on name
    with an EXISTING successor principal is not automatically a benign birth-standard duplicate
    (the tool's prior dead dedup check assumed exactly that, wrongly) -- it is only benign when
    the colliding identity actually matches. `purpose` (the registration event's own free-text
    field, `principal_purpose`) is read alongside `agent_class` so ingestion can compare BOTH
    against whatever the successor already holds for that name before deciding. Read from
    `principal_standing_current` (s40+; that view's own "first in-force registration event's
    purpose" -- ADR-0012 P1, reused rather than re-derived) when it exists; honestly `None` on a
    pre-s40 kernel where no registration-event purpose concept exists at all (the `kern.principal`
    table alone, this function's only source pre-s40, carries no purpose column)."""
    if _relation_exists(dep, dep.schema, "principal_standing_current"):
        r = _psql_tuples(dep, f"SELECT id, name, agent_class, purpose FROM "
                              f"{dep.schema}.principal_standing_current ORDER BY id;")
        rows = [(pid, name, agent_class, purpose)
                for pid, name, agent_class, purpose in _rows(r)]
    else:
        r = _psql_tuples(dep, f"SELECT id, name, agent_class FROM {dep.kern}.principal ORDER BY id;")
        rows = [(pid, name, agent_class, None) for pid, name, agent_class in _rows(r)]

    items = []
    for pid, name, agent_class, purpose in rows:
        items.append({
            "record": "item", "class": "1.1_principal_roster", "disposition": "carry-reopened",
            "dust_row_ids": [], "row_kind": "principal", "principal_id": pid,
            "statement": f"principal '{name}' (class {agent_class})",
            "actor_attribution": {"agent_class": agent_class, "name": name, "purpose": purpose},
            "refs": f"{dep.name}:principal:{pid}",
            "reason": None,
        })
    return items


def extract_standing_decisions(dep) -> list[dict]:
    """1.2/1.3 Standing decisions and procedures — carry-verbatim (RE-ASSERT).

    PRE-S36 FALLBACK (row 1950 lesson: this world's own kernel, autoharn1, predates s36 --
    `standing_decisions` (s36) does not exist, but the consult's own trust condition (row 1942:
    "carry verbatim-with-citation, nothing silently dropped") does not relax just because a
    younger world lacks the grading view. Pre-s36, the in-force decision vocabulary IS the
    supersedes-filtered `ledger_current` view (s31 semantics) -- the exact source pickup's own
    IN-FORCE-DECISIONS/RESOURCES/ESTIMATES sections already read (bootstrap/templates/
    legacy-pickup.tmpl's header). So every unsuperseded kind=decision row there crosses as a
    1.2_standing_decisions carry-verbatim item, with NO grade (the concept does not exist on this
    kernel -- `grade` is honestly `None`, never invented). This is a genuine WIDENING relative to
    the s36 path (which reads only the GRADED subset via `standing_decisions` = ledger_current
    WHERE decision_grade IS NOT NULL, kernel/lineage/s36-decision-grade.sql) -- named here, not
    silently matched to it, via the class-summary line appended alongside the items. 1.3
    (procedures) still has no distinct kernel representation on any kernel lineage and stays
    subsumed under 1.2 (CLASSES_OUT_OF_SCOPE) whichever branch runs. The s36-present branch above
    is untouched -- same query, same item shape, byte-identical."""
    if _relation_exists(dep, dep.schema, "standing_decisions"):
        r = _psql_tuples(dep, f"SELECT id, grade, statement FROM {dep.schema}.standing_decisions "
                              f"ORDER BY id;")
        items = []
        for rid, grade, statement in _rows(r):
            items.append({
                "record": "item", "class": "1.2_standing_decisions", "disposition": "carry-verbatim",
                "dust_row_ids": [int(rid)], "row_kind": "decision", "grade": grade,
                "statement": statement, "refs": f"{dep.name}:row:{rid}", "reason": None,
            })
        return items

    if not _relation_exists(dep, dep.schema, "ledger_current"):
        return [{"record": "class-summary", "class": "1.2_standing_decisions",
                  "disposition": "drop-with-reason", "count": 0,
                  "reason": "UNAVAILABLE: this world's kernel predates both s36 (no "
                            "standing_decisions) and s15 (no ledger_current) -- no in-force "
                            "decision vocabulary of any kind exists to extract from."}]

    r = _psql_tuples(dep, f"SELECT id, statement FROM {dep.schema}.ledger_current "
                          f"WHERE kind = 'decision' ORDER BY id;")
    rows = _rows(r)
    items = []
    for rid, statement in rows:
        items.append({
            "record": "item", "class": "1.2_standing_decisions", "disposition": "carry-verbatim",
            "dust_row_ids": [int(rid)], "row_kind": "decision", "grade": None,
            "statement": statement, "refs": f"{dep.name}:row:{rid}", "reason": None,
        })
    items.append({
        "record": "class-summary", "class": "1.2_standing_decisions",
        "disposition": "carry-verbatim", "count": len(rows),
        "reason": "PRE-S36 FALLBACK: this world's kernel predates s36 (standing_decisions does "
                  "not exist). Every unsuperseded kind=decision row in ledger_current (s31 "
                  "supersedes-filtered semantics -- the same source pickup's own IN-FORCE-"
                  "DECISIONS/RESOURCES/ESTIMATES sections read, per bootstrap/templates/"
                  "legacy-pickup.tmpl) is carried verbatim as this class's item, since no grade "
                  "concept exists pre-s36 to filter on. This carries ALL unsuperseded decision "
                  "rows, not only a graded subset -- a genuine widening relative to the s36 path "
                  "(which reads only decision_grade IS NOT NULL rows), named here rather than "
                  "silently matched to it. No grade is represented on any item above (field is "
                  "null) since none exists on this kernel; inventing one would misrepresent the "
                  "source. 1.3 (procedures) has no distinct kernel representation on this kernel "
                  "either and stays subsumed under these same items (CLASSES_OUT_OF_SCOPE).",
    })
    return items


def extract_open_work(dep) -> list[dict]:
    """1.4 Open work — carry-reopened (RE-ENACT, unclaimed), debt written off by name
    (drop-with-reason, never silently absent)."""
    items: list[dict] = []
    if not _relation_exists(dep, dep.schema, "work_item_current"):
        return [{"record": "class-summary", "class": "1.4_open_work",
                  "disposition": "drop-with-reason", "count": 0,
                  "reason": "UNAVAILABLE: this world's kernel predates s22 "
                            "(work_item_current does not exist)"}]
    r = _psql_tuples(dep, f"""
        SELECT o.id, o.slug, o.title, wic.state, wic.claimant, wic.review_disposition
        FROM (SELECT id, work_slug AS slug, work_title AS title
              FROM {dep.schema}.ledger_current WHERE kind = 'work_opened') o
        JOIN {dep.schema}.work_item_current wic ON wic.slug = o.slug
        WHERE wic.state = 'open'
        ORDER BY o.id;
    """)
    for oid, slug, title, state, claimant, review_disp in _rows(r):
        items.append({
            "record": "item", "class": "1.4_open_work", "disposition": "carry-reopened",
            "dust_row_ids": [int(oid)], "row_kind": "work_opened", "slug": slug,
            "statement": title, "refs": f"{dep.name}:row:{oid}",
            "dust_claimant_excluded": bool(claimant),  # never carried -- a claim binds a gone session
            "review_disposition": review_disp, "reason": None,
        })
    # closure debt on already-CLOSED items -- never crosses, per name (consult §1.4/§5)
    if _relation_exists(dep, dep.schema, "work_review_gap"):
        r = _psql_tuples(dep, f"SELECT slug, close_id FROM {dep.schema}.work_review_gap ORDER BY slug;")
        for slug, close_id in _rows(r):
            items.append({
                "record": "item", "class": "1.4_open_work_debt", "disposition": "drop-with-reason",
                "dust_row_ids": [int(close_id)], "row_kind": "work_review_gap", "slug": slug,
                "statement": None,
                "reason": "closure debt (deferred-review obligation) is a creature of the dust "
                          "world's obligation machinery; per the consult it never crosses -- "
                          "the successor's accountability bookkeeping starts at zero. If the "
                          "underlying item is still wanted, it crosses (unclaimed) via its own "
                          "1.4_open_work item if still open, or is reopened by name at ingestion.",
            })
    if _relation_exists(dep, dep.schema, "work_item_violations"):
        r = _psql_tuples(dep, f"SELECT slug FROM {dep.schema}.work_item_violations ORDER BY slug;")
        for (slug,) in _rows(r):
            items.append({
                "record": "item", "class": "1.4_open_work_debt", "disposition": "drop-with-reason",
                "dust_row_ids": [], "row_kind": "work_item_violation", "slug": slug,
                "statement": None,
                "reason": "work-item violation debt never crosses (consult §5).",
            })
    return items


def extract_open_questions(dep) -> list[dict]:
    """1.5 Open questions — carry-reopened (RE-ENACT)."""
    if not _relation_exists(dep, dep.schema, "question_status"):
        return [{"record": "class-summary", "class": "1.5_open_questions",
                  "disposition": "drop-with-reason", "count": 0,
                  "reason": "UNAVAILABLE: question_status does not exist on this kernel"}]
    r = _psql_tuples(dep, f"""
        SELECT qs.question_id, l.statement
        FROM {dep.schema}.question_status qs
        JOIN {dep.schema}.ledger_current l ON l.id = qs.question_id
        WHERE qs.answered = 'f'
        ORDER BY qs.question_id;
    """)
    items = []
    for qid, statement in _rows(r):
        items.append({
            "record": "item", "class": "1.5_open_questions", "disposition": "carry-reopened",
            "dust_row_ids": [int(qid)], "row_kind": "question", "statement": statement,
            "refs": f"{dep.name}:row:{qid}", "reason": None,
        })
    return items


def extract_drop_and_never(dep) -> list[dict]:
    """1.7 competence/track record (review discharges, CITE-ONLY default) and 1.10/1.12
    commissions/refusals/violations/snags (NEVER). Count+ids only -- statement/rationale/evidence
    text is never read into the manifest for any row in either group (PAYLOAD-FREE CLASSES,
    module docstring)."""
    items = []
    for kind in DROP_KINDS:
        r = _psql_tuples(dep, f"SELECT id FROM {dep.schema}.ledger WHERE kind = '{kind}' ORDER BY id;")
        ids = [int(row[0]) for row in _rows(r)]
        cls = "1.7_track_record" if kind == "review" else f"other_{kind}"
        for rid in ids:
            items.append({
                "record": "item", "class": cls, "disposition": "drop-with-reason",
                "dust_row_ids": [rid], "row_kind": kind, "statement": None,
                "reason": f"kind={kind} rows are CITE-ONLY by default (consult §1.7/§5): "
                          f"review discharges never cross, credit and debt alike; the dust "
                          f"world remains queryable read-only forever.",
            })
    for kind in NEVER_KINDS:
        r = _psql_tuples(dep, f"SELECT id FROM {dep.schema}.ledger WHERE kind = '{kind}' ORDER BY id;")
        ids = [int(row[0]) for row in _rows(r)]
        cls = {"commission": "1.10_commissions", "work_violation_disposition": "1.12_violations",
               "write_refused": "1.12_refusals", "snag": "1.12_snags"}[kind]
        for rid in ids:
            items.append({
                "record": "item", "class": cls, "disposition": "never-class",
                "dust_row_ids": [rid], "row_kind": kind, "statement": None,
                "reason": f"kind={kind} is a NEVER-class (consult §1.10/§1.12/§5): does not "
                          f"cross in any form; stays in the dust world as evidence only.",
            })
    return items


def _principal_id_to_name(dep) -> dict[str, str]:
    """id (as the raw csv string _rows() yields) -> name, THIS world's own roster. The one home
    for this lookup — extract_principal_lifecycle's own name-resolution below, and nowhere
    else, so a future second caller derives from here rather than re-issuing the SELECT
    (ADR-0012 P1)."""
    r = _psql_tuples(dep, f"SELECT id, name FROM {dep.kern}.principal;")
    return {pid: name for pid, name in _rows(r)}


# 1.13-1.19: every kind the s40/s41/s45 principal-identity-events family defines, EXCEPT
# principal_registered (already class 1.1) and the historical-record verification markers
# (commission_signature_verified/principal_key_possession_verified — one-time facts, not
# standing-force per the matrix's own §1 table).
_PRINCIPAL_LIFECYCLE_KINDS = {
    "principal_suspended": "1.13_principal_suspended",
    "principal_revoked": "1.14_principal_revoked",
    "principal_standing_declared": "1.15_principal_standing_declared",
    "principal_relation_asserted": "1.16_principal_relation_asserted",
    "principal_role_bound": "1.17_principal_role_bound",
    "principal_key_bound": "1.18_principal_key_bound",
    "principal_competence_granted": "1.19_principal_competence_granted",
}
_S41_ONLY_KINDS = ("principal_relation_asserted", "principal_role_bound",
                   "principal_key_bound", "principal_competence_granted")


def extract_principal_lifecycle(dep) -> list[dict]:
    """1.13-1.19 — the kernel side-tables design/PHOENIX-SURVIVAL-UNIVERSE-2026-07-28.md's §3/§4
    name as STRUCTURALLY IGNORED by every extract_all() class that predates this build:
    principal suspensions/revocations/standing-declarations/relations/role-bindings/
    key-bindings/competence-grants. Every one is carry-reopened (RE-ENACT — a fresh typed act
    through `led principal <verb>`, never a raw INSERT, ADR-0012 P2 — "re-write through the
    kernel's own verbs" per the commissioning work item). Matrix ranking #1: a REVOKED
    principal's revocation not crossing is the single highest-consequence gap the matrix names,
    because the successor could otherwise functionally re-admit a revoked actor with no
    structural block at all.

    IN-FORCE, uniformly across all seven kinds (one filter, not seven hand-derived ones —
    ADR-0012 P1, "derive don't duplicate" applied to the kernel's OWN governing-row logic):
    `ledger_current` (s31 supersession-filtered) already excludes every SUPERSEDED row; the one
    remaining case a bare kind filter would over-carry is a LIFT/UNBIND/RELEASE row — itself
    unsuperseded, same kind, but `principal_binding_active = false` (s41/s45's identity/value-
    split retraction idiom: a superseding same-kind row restates identity and flips active to
    false, rather than a second retraction shape). `principal_binding_active IS NOT FALSE` keeps
    TRUE and NULL (a pre-s41 kernel, where the column and the concept do not exist yet and
    ledger_current's own filtering is already sufficient on its own) and drops only an explicit
    FALSE — one filter, version-safe by construction, never branched per kernel vintage.
    `principal_revoked` never carries this column at all (s45's own CHECK forbids it —
    terminal-by-type, no un-revoke path exists, kernel/lineage/s45-standing-lifecycle.sql
    Element 1's "principal_revoked is DELIBERATELY ABSENT"): the same filter is a costless
    no-op pass-through for it (always NULL there), so it shares this exact code path rather than
    a bespoke one.

    PRINCIPAL NAMES, NEVER DUST-WORLD IDS: `principal_subject`/`principal_object` are this
    world's OWN internal ids, meaningless in a successor with its own fresh `kernel.principal`
    rows. Every id is resolved to its NAME here, at extraction, against THIS world's roster —
    the manifest carries names (`principal_fields`), and ingestion resolves those names against
    the SUCCESSOR's roster via `led principal <verb>`'s own lookup, which already refuses
    loudly, by name, when a referent is not registered there (no second name-existence check is
    invented in this file — one authority, the kernel verb itself, ADR-0012 P1). A subject/
    object id that fails to resolve even in the SOURCE world's own roster is a dust-world data-
    integrity problem, not a silent-skip candidate, so it is refused loudly here, not carried
    as a guess.

    Column availability is probed ONCE per call (s40 adds principal_subject/principal_db_role;
    s41 adds principal_binding_active plus the four binding-family columns): a kernel missing a
    needed column gets an honest UNAVAILABLE class-summary for exactly the kinds it cannot
    carry, never a silent empty result indistinguishable from "nothing to carry" (the same
    UNAVAILABLE idiom extract_open_work/extract_open_questions already use above).

    QUERY SHAPED PER DETECTED VINTAGE (fix round 2, finding 1): the three s40-native kinds
    (principal_suspended/principal_revoked/principal_standing_declared) are selectable on an
    s40-only kernel that has NEVER applied s41 -- but s41's own columns (principal_object,
    principal_relation, principal_role_name, principal_key_fingerprint, principal_competence_*)
    do not exist there at all. Referencing them unconditionally in one shared SELECT (as this
    function used to) makes psql fail on the unknown column for EVERY kind, s40-native ones
    included -- `_rows()`'s own fix (above) now turns that into a loud refusal rather than a
    silent `[]`, but the right fix is to never issue the doomed query in the first place: the
    column list itself is chosen once, per call, from `has_s41_cols`, and every kind reads
    through that one shared shape (still one code path, not seven -- ADR-0012 P1)."""
    if not _column_exists(dep, "ledger", "principal_subject"):
        return [{"record": "class-summary", "class": label, "disposition": "drop-with-reason",
                  "count": 0,
                  "reason": "UNAVAILABLE: this world's kernel predates s40 (kernel/lineage/"
                            "s40-principal-identity-events.sql) — no principal_subject column "
                            "exists to extract from."}
                for label in _PRINCIPAL_LIFECYCLE_KINDS.values()]

    has_binding_active = _column_exists(dep, "ledger", "principal_binding_active")
    has_s41_cols = _column_exists(dep, "ledger", "principal_object")
    names = _principal_id_to_name(dep)
    active_clause = " AND principal_binding_active IS NOT FALSE" if has_binding_active else ""

    if has_s41_cols:
        columns = ("id", "statement", "principal_subject", "principal_object",
                   "principal_relation", "principal_role_name", "principal_key_fingerprint",
                   "principal_competence_activity", "principal_competence_band",
                   "principal_competence_basis", "principal_db_role")
    else:
        # s40-only vintage: ONLY the columns s40 itself adds. Referencing an s41 column here
        # would fail psql outright on every one of the three s40-native kinds below -- the exact
        # silent-loss shape this fix round closes.
        columns = ("id", "statement", "principal_subject", "principal_db_role")
    col_list = ", ".join(columns)

    items: list[dict] = []
    for kind, label in _PRINCIPAL_LIFECYCLE_KINDS.items():
        if kind in _S41_ONLY_KINDS and not has_s41_cols:
            items.append({"record": "class-summary", "class": label,
                          "disposition": "drop-with-reason", "count": 0,
                          "reason": "UNAVAILABLE: this world's kernel predates s41 (kernel/"
                                    "lineage/s41-principal-bindings-and-relations.sql) — the "
                                    "columns this kind needs do not exist."})
            continue
        r = _psql_tuples(dep, f"""
            SELECT {col_list}
            FROM {dep.schema}.ledger_current
            WHERE kind = '{kind}'{active_clause}
            ORDER BY id;
        """)
        for row in _rows(r):
            rec = dict(zip(columns, row))
            rid, statement, subj_id = rec["id"], rec["statement"], rec.get("principal_subject")
            obj_id = rec.get("principal_object")
            relation = rec.get("principal_relation")
            role_name = rec.get("principal_role_name")
            fingerprint = rec.get("principal_key_fingerprint")
            activity = rec.get("principal_competence_activity")
            band = rec.get("principal_competence_band")
            basis = rec.get("principal_competence_basis")
            db_role = rec.get("principal_db_role")
            subj_name = names.get(subj_id) if subj_id else None
            if subj_id and subj_name is None:
                print(f"extract-context: REFUSED — {kind} row {rid} names principal_subject "
                      f"id {subj_id!r}, which is not in {dep.name}'s own principal roster.",
                      file=sys.stderr)
                sys.exit(2)
            obj_name = names.get(obj_id) if obj_id else None
            if obj_id and obj_name is None:
                print(f"extract-context: REFUSED — {kind} row {rid} names principal_object "
                      f"id {obj_id!r}, which is not in {dep.name}'s own principal roster.",
                      file=sys.stderr)
                sys.exit(2)
            fields: dict[str, str | None] = {"subject_name": subj_name}
            if kind == "principal_standing_declared":
                fields["db_role"] = db_role
            elif kind == "principal_relation_asserted":
                fields["relation"], fields["object_name"] = relation, obj_name
            elif kind == "principal_role_bound":
                fields["role_name"] = role_name
            elif kind == "principal_key_bound":
                fields["fingerprint"] = fingerprint
            elif kind == "principal_competence_granted":
                fields["activity"], fields["band"], fields["basis"] = activity, band, basis
            items.append({
                "record": "item", "class": label, "disposition": "carry-reopened",
                "dust_row_ids": [int(rid)], "row_kind": kind, "statement": statement,
                "principal_fields": fields, "refs": f"{dep.name}:row:{rid}", "reason": None,
            })
    return items


def extract_entitlement_class_config(dep) -> list[dict]:
    """1.20 entitlement_class_configured (kernel/lineage/s60-entitlement-enforcement.sql) —
    governs which organizational ROLE NAME an act class requires. NOT principal-referring (the
    role field is a role-name STRING, not a principal id), so this class carries none of
    1.13-1.19's referent-existence risk.

    Governing-row semantics reuse the kernel's OWN `entitlement_class_roles` view (s60 Element
    4) directly, rather than re-deriving its max(id)-per-act_class WHERE-logic a second time in
    Python (ADR-0012 P1: one authority, not a second hand-copy) — that view has no `active`
    column and no `supersedes` concept for this kind at all (v1 supports fresh-assert and
    rotation only, mirroring `kernel.principal_role`'s own pre-s45 shape).

    DEFAULT DISPOSITION IS drop-with-reason, NOT carry-reopened, unlike every other class in
    this file that re-enacts a typed act: as of this kernel lineage, NO `led` verb writes
    entitlement_class_configured at all — only bootstrap/new-project.sh's own birth-sequence
    step 6 does, via a direct `kernel.ledger_write(...)` call in a psql DO block, for the five
    default act classes. This tool refuses to invent a new CLI verb outside its commissioned
    scope (extending extract_context.py, not led.tmpl's write surface) and refuses even harder
    to raw-INSERT around the kernel's own write boundary (ADR-0012 P2). The row is still
    EXTRACTED — so a maintainer reviewing the manifest SEES that the source world reconfigured
    an act class's required role away from birth's default — but ingestion cannot re-enact it
    automatically; the existing drop-with-reason path (cmd_ingest, unmodified by this class)
    reports it, never silently. Named here as a residual gap the commission surfaced, not
    routed around: a future `led principal configure-entitlement` verb would close it."""
    if not _relation_exists(dep, dep.schema, "entitlement_class_roles"):
        return [{"record": "class-summary", "class": "1.20_entitlement_class_configured",
                  "disposition": "drop-with-reason", "count": 0,
                  "reason": "UNAVAILABLE: this world's kernel predates s60 (kernel/lineage/"
                            "s60-entitlement-enforcement.sql) — entitlement_class_roles does "
                            "not exist."}]
    r = _psql_tuples(dep, f"""
        SELECT lc.id, lc.statement, ecr.act_class, ecr.role_name
        FROM {dep.schema}.entitlement_class_roles ecr
        JOIN {dep.schema}.ledger_current lc ON lc.id = ecr.row_id
        ORDER BY lc.id;
    """)
    items = []
    for rid, statement, act_class, role_name in _rows(r):
        items.append({
            "record": "item", "class": "1.20_entitlement_class_configured",
            "disposition": "drop-with-reason", "dust_row_ids": [int(rid)],
            "row_kind": "entitlement_class_configured", "statement": statement,
            "principal_fields": {"act_class": act_class, "role_name": role_name},
            "refs": f"{dep.name}:row:{rid}",
            "reason": "no `led` verb writes entitlement_class_configured (see this function's "
                      "own docstring) — re-configure by hand through the kernel's own "
                      "ledger_write RPC if the successor's default act-class/role map "
                      "genuinely needs to differ from birth's, or file a work item for a "
                      "`led principal configure-entitlement` verb; never raw-INSERT.",
        })
    return items


def extract_resource_tier_ungraded(dep) -> list[dict]:
    """1.21 — every statement-grammar row rides bare kind='decision' (led.tmpl:1462-1470's eight
    grammars — resource:/estimate:/actual:/taxon:/interface:/outcome:/review:/review-done:), so
    extract_standing_decisions' s36+ branch (`WHERE decision_grade IS NOT NULL`) silently drops
    every one of them that is not individually `--grade durable` — design/
    PHOENIX-SURVIVAL-UNIVERSE-2026-07-28.md's own §2 finding, not previously named anywhere in
    this file (see CLASSES_OUT_OF_SCOPE 1.6/1.8, corrected by this same build). Of the eight,
    only `resource:`'s TIER field carries a genuine standing MUST-NOT (`forbidden:`/`mandated:`
    — a deontic constraint on future tool/backend use) — matrix ranking #2. The other seven
    (estimate:/actual:/taxon:/interface:/outcome:/review:/review-done:) are named here, not
    silently excluded: estimate:/actual:/outcome: are diagnostic-only by standing maintainer
    ruling (100% diagnostic, never policy — matrix ranking #8, lowest blast radius of every
    structural gap the matrix found); taxon:/interface: are classificatory conventions, not
    MUST-NOTs; review:/review-done: are already class 1.7_track_record's own CITE-ONLY default.
    None of the seven carries the same revocation-shaped hazard resource:'s forbidden tier
    does, so this class is deliberately resource:-only — a future study naming a genuine
    standing-force need in one of the other seven routes through this same mechanism (a new
    class, named and filed), never a silent widening of this one.

    Pre-s36 kernels are UNTOUCHED by this function (returns nothing): extract_standing_decisions'
    own PRE-S36 FALLBACK already carries every unsuperseded kind=decision row — including any
    resource: rows — unconditionally, with no grade filter to leak through in the first place;
    running this function there too would double-carry the same dust rows under two class
    labels."""
    if not _relation_exists(dep, dep.schema, "standing_decisions"):
        return []
    r = _psql_tuples(dep, f"SELECT id, statement FROM {dep.schema}.ledger_current "
                          f"WHERE kind = 'decision' AND decision_grade IS NULL "
                          f"AND statement ILIKE 'resource:%' ORDER BY id;")
    items = []
    for rid, statement in _rows(r):
        items.append({
            "record": "item", "class": "1.21_resource_tier_ungraded",
            "disposition": "carry-verbatim", "dust_row_ids": [int(rid)], "row_kind": "decision",
            "grade": None, "statement": statement, "refs": f"{dep.name}:row:{rid}",
            "reason": None,
        })
    return items


def extract_all(dep) -> list[dict]:
    items: list[dict] = []
    items += extract_principals(dep)
    items += extract_standing_decisions(dep)
    items += extract_open_work(dep)
    items += extract_open_questions(dep)
    items += extract_drop_and_never(dep)
    items += extract_principal_lifecycle(dep)
    items += extract_entitlement_class_config(dep)
    items += extract_resource_tier_ungraded(dep)
    return items


# --------------------------------------------------------------------------------------- extract

def cmd_extract(args: argparse.Namespace) -> int:
    deployment_path = Path(args.deployment).resolve()
    dep = _load_deployment(deployment_path)
    provenance = build_provenance(dep, deployment_path, args.mode, args.principal)
    items = extract_all(dep)

    out = sys.stdout if args.out == "-" else open(args.out, "w", encoding="utf-8")
    try:
        out.write(json.dumps(provenance, sort_keys=True) + "\n")
        for item in items:
            out.write(json.dumps(item, sort_keys=True) + "\n")
    finally:
        if out is not sys.stdout:
            out.close()

    class_counts: dict[str, int] = {}
    for item in items:
        class_counts[item["class"]] = class_counts.get(item["class"], 0) + 1
    print(f"extract-context: wrote {len(items)} item(s) + 1 provenance line to "
          f"{args.out if args.out != '-' else '<stdout>'}", file=sys.stderr)
    for cls, n in sorted(class_counts.items()):
        print(f"  {cls}: {n}", file=sys.stderr)
    print("extract-context: MANIFEST IS UNREVIEWED. It is the maintainer's veto surface -- "
          "ingest refuses it wholesale until a {\"record\":\"review\",\"reviewed\":true,...} "
          "line is appended by a distinct reviewer.", file=sys.stderr)
    return 0


# --------------------------------------------------------------------------------------- ingest

def _load_manifest(path: Path) -> tuple[dict, list[dict], dict | None]:
    provenance = None
    items: list[dict] = []
    review = None
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"extract-context ingest: REFUSED -- {path}:{lineno} is not valid JSON "
                      f"({e})", file=sys.stderr)
                sys.exit(2)
            rec = obj.get("record")
            if rec == "provenance":
                provenance = obj
            elif rec in ("item", "class-summary"):
                items.append(obj)
            elif rec == "review":
                review = obj
            else:
                print(f"extract-context ingest: REFUSED -- {path}:{lineno} has unrecognized "
                      f"\"record\": {rec!r}.", file=sys.stderr)
                sys.exit(2)
    if provenance is None:
        print(f"extract-context ingest: REFUSED -- {path} has no provenance line (line 1).",
              file=sys.stderr)
        sys.exit(2)
    return provenance, items, review


def _find_led(project_root: Path) -> list[str] | None:
    """legacy-led-retirement (ledger row 1149): the direct-psql `legacy/led` original is
    RETIRED -- every surface, this one included, resolves the served `led` (the boundary_url/
    boundary_deployment-requiring HTTP client, bootstrap/templates/led.tmpl) and no other path.
    This is a genuine behavior change from the pre-retirement docstring here (which preferred
    `legacy/led` specifically so ingestion would not depend on a boundary service being wired at
    all) -- named, not silently absorbed: a target deployment with no boundary configured (no
    `boundary_url`/`boundary_deployment` in its own deployment.json) now REFUSES here with
    `led`'s own teach-text (bcc.load_served_config's own message, exit 4) rather than silently
    falling back to a byte-for-byte legacy original that no longer exists in a post-retirement
    checkout. No candidate search remains -- there is exactly one lawful `led` per world.

    Root-shim-pruning residue sweep (ledger row 1357, 2026-07-27): a bare per-verb `led` shim
    only exists next to deployment.json for a world scaffolded BEFORE the §6 amendment (rows
    1365/1366/1367) -- "a world scaffolded before this migration keeps its ten shims untouched"
    (CLAUDE.md). A world scaffolded on/after that amendment has ONE `autoharn` dispatcher
    instead. Returns the leading argv (a bare-shim path, or `[autoharn, "led"]`) rather than a
    single Path, so callers can invoke either shape uniformly."""
    bare = project_root / "led"
    if bare.exists() and os.access(bare, os.X_OK):
        return [str(bare)]
    dispatcher = project_root / "autoharn"
    if dispatcher.exists() and os.access(dispatcher, os.X_OK):
        return [str(dispatcher), "led"]
    return None


def _run_led(led: list[str], args: list[str], actor: str, cwd: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["LED_ACTOR"] = actor  # EVERY invocation sets this explicitly (row 1943 lesson (a)) --
    # never inherited from whatever the ambient environment happened to carry.
    return subprocess.run([*led, *args], capture_output=True, text=True, cwd=str(cwd), env=env)


REASSERT_MARKER = "re-asserted from {world}:"


def _generic_outcome(cls: str, disp: str, r: subprocess.CompletedProcess, **extra) -> dict:
    if r.returncode == 0:
        outcome = "RE-ASSERTED" if disp == "carry-verbatim" else "RE-ENACTED"
        return {"class": cls, "disposition": disp, "outcome": outcome,
                "led_stdout": r.stdout.strip(), **extra}
    return {"class": cls, "disposition": disp, "outcome": "DROPPED",
            "reason": f"led refused: {r.stderr.strip()}", **extra}


# --------------------------------------------------------------- fix round 2: provenance sidecar

_ROW_WRITTEN_RE = re.compile(r"row (\d+) written")

# PROVENANCE-SIDECAR CONVENTION (fix round 2, finding 2): `led principal declare-standing`/
# `relate`/`bind-role`/`bind-key`/`grant-competence` carry NO free-text or --refs field at all
# (row 1173's own strict-flag parsers -- unlike suspend/revoke/lift-suspension, these five verbs
# build their statement entirely from typed arguments, refusing every shared flag including
# --refs by name, see `_refuse_other_shared_flags` in bootstrap/templates/led.tmpl). A bare
# re-enactment through one of them is therefore BYTE-INDISTINGUISHABLE from a fresh maintainer
# act -- an attribution lie the successor's own ledger cannot see through. The fix: immediately
# after such a re-enactment succeeds, write a SECOND, ordinary `decision` row citing the NEW row
# by id (`--refs row:<new-id>`) and narrating the carry in its statement -- the decision grammar
# is the one place in this file's own vocabulary that both accepts free text AND accepts --refs,
# so it is reused rather than inventing a new mechanism (ADR-0012 P1). The sidecar is its own
# ledger row, queryable like any other decision (`led --recent`, `led show <id>`) -- it does NOT
# change the re-enacted row itself, which stays exactly what the successor's own kernel verb
# would have produced for a fresh act, by design (RE-ENACT, not RE-ASSERT, per the module
# docstring's own disposition vocabulary). Applied to every carry-reopened principal-lifecycle
# class whose verb carries no such field: 1.15/1.16/1.17/1.18/1.19 (suspend/revoke, 1.13/1.14,
# keep the existing marker-in-reason convention -- those two verbs DO accept free text).
def _new_row_id(stdout: str) -> int | None:
    m = _ROW_WRITTEN_RE.search(stdout)
    return int(m.group(1)) if m else None


def _reenact_with_provenance(cls: str, disp: str, r: subprocess.CompletedProcess, *,
                              world: str, dust_row_ids: list[int], led: list[str], actor: str,
                              project_root: Path, **extra) -> dict:
    outcome = _generic_outcome(cls, disp, r, **extra)
    if outcome["outcome"] != "RE-ENACTED":
        return outcome
    new_id = _new_row_id(r.stdout)
    if new_id is None:
        outcome["provenance_sidecar"] = {
            "outcome": "SKIPPED",
            "reason": "could not parse a new row id out of led's own stdout -- no sidecar "
                      "written; the re-enacted row itself still landed (see led_stdout above).",
        }
        return outcome
    dust_ref = dust_row_ids[0] if dust_row_ids else "?"
    stmt = (f"carried from {world} row {dust_ref} at phoenix ingest, "
            f"{datetime.now(timezone.utc).isoformat()}")
    sc = _run_led(led, ["--refs", f"row:{new_id}", "decision", stmt], actor=actor, cwd=project_root)
    if sc.returncode == 0:
        outcome["provenance_sidecar"] = {"outcome": "WRITTEN", "led_stdout": sc.stdout.strip()}
    else:
        outcome["provenance_sidecar"] = {"outcome": "FAILED",
                                          "reason": f"led refused: {sc.stderr.strip()}"}
    return outcome


# ------------------------------------------------------------ fix round 2: real collision check

def _is_principal_name_collision(stderr: str) -> bool:
    """Fix round 2, finding 3: the tool's ORIGINAL dedup check (`"already registered" in
    r.stderr`) never matched ANY real refusal -- `register-principal`'s actual duplicate-name
    refusal is the kernel write boundary's own SQLSTATE 23505 report, `duplicate key value
    violates unique constraint "principal_name_key"` (witnessed against a live collision), which
    contains neither substring. That dead branch is replaced by detecting the REAL refusal
    shape."""
    return "principal_name_key" in stderr and (
        "23505" in stderr or "duplicate key value violates unique constraint" in stderr)


def _compare_existing_principal(dep, name: str, agent_class: str | None,
                                 purpose: str | None) -> bool | None:
    """Fix round 2, finding 3: on a name collision, is it a BENIGN duplicate (the successor
    already holds this exact identity -- birth-standard or an earlier ingestion pass) or a
    GENUINE identity collision (two different principals that happen to share a name)? Read-only
    against the SUCCESSOR (`dep` here is cmd_ingest's TARGET deployment, not a source) via
    `principal_standing_current` (s40+; the same view extract_principals() itself now reads) --
    never a second hand-derivation of "how to look up a principal's registered shape" (ADR-0012
    P1). Returns True (matches), False (differs -- a genuine collision), or None (the successor
    has no such view, or no row for this name at all -- inconclusive, never silently treated as a
    match).

    `name` crosses the psql boundary as DATA via a bound `-v` variable, never spliced into the SQL
    text (ADR-0000's 2026-07-18 amendment: a value that becomes program is a type/mechanism
    hazard, not a convenience) -- an externally-carried manifest's principal name is exactly the
    untrusted value that amendment names, unlike this file's other f-string-interpolated
    identifiers (dep.schema/dep.kern/kind/etc.), which are all operator-config or a closed,
    internally-enumerated vocabulary, never manifest-carried text. Piped over STDIN, not passed
    to `-c` (witnessed live: psql's `:'var'` substitution is honored reading a script off stdin
    but NOT inside a `-c` argument -- the SAME reason every OTHER bound-variable write in this
    tree, e.g. bootstrap/new-project.sh's own `decode(:'hex','hex')` idiom, is always piped in
    rather than passed via `-c`)."""
    if not _relation_exists(dep, dep.schema, "principal_standing_current"):
        return None
    full = (f"SET ROLE {dep.role};\n"
            f"SELECT agent_class, purpose FROM {dep.schema}.principal_standing_current "
            f"WHERE name = :'name';")
    r = subprocess.run(["psql", "-h", dep.host, "-d", dep.db, "--csv", "-v", "ON_ERROR_STOP=1",
                        "-v", f"name={name}"],
                       input=full, capture_output=True, text=True, timeout=60)
    rows = _rows(r)
    if not rows:
        return None
    existing_class, existing_purpose = rows[0][0], rows[0][1]
    return existing_class == (agent_class or "") and existing_purpose == (purpose or "")


def cmd_ingest(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest).resolve()
    provenance, items, review = _load_manifest(manifest_path)

    if not review or review.get("reviewed") is not True:
        print(f"extract-context ingest: REFUSED WHOLESALE -- {manifest_path} carries no "
              f"reviewed marker ({{\"record\":\"review\",\"reviewed\":true,...}}). This is the "
              f"maintainer's veto surface (autoharn ledger row 1942) -- no item, carried or "
              f"dropped, is written until a distinct reviewer appends that line. No write was "
              f"attempted.", file=sys.stderr)
        return 1

    deployment_path = Path(args.deployment).resolve()
    dep = _load_deployment(deployment_path)
    project_root = deployment_path.parent
    led = _find_led(project_root)
    if led is None:
        print(f"extract-context ingest: REFUSED -- no executable led/legacy-led found under "
              f"{project_root}.", file=sys.stderr)
        return 2

    world = provenance.get("world_name", "UNKNOWN")
    marker = REASSERT_MARKER.format(world=world)
    outcomes: list[dict] = []

    for item in items:
        rec = item.get("record")
        cls = item.get("class")
        disp = item.get("disposition")
        if rec != "item":
            continue  # class-summary lines carry no payload to ingest
        if disp in ("drop-with-reason", "never-class"):
            outcomes.append({"class": cls, "disposition": disp, "outcome": "DROPPED",
                              "reason": item.get("reason")})
            continue
        if disp not in ("carry-verbatim", "carry-reopened"):
            outcomes.append({"class": cls, "disposition": disp, "outcome": "DROPPED",
                              "reason": f"unrecognized disposition {disp!r} -- not ingested"})
            continue

        refs = f"{marker} {item.get('refs', '')}".strip()

        if cls == "1.1_principal_roster":
            attrib = item.get("actor_attribution", {})
            name, agent_class = attrib.get("name"), attrib.get("agent_class")
            purpose_src = attrib.get("purpose")
            r = _run_led(led, ["register-principal", name, agent_class, "--purpose",
                               f"{marker} re-registered per extract from {world}"],
                        actor=args.actor, cwd=project_root)
            if r.returncode == 0:
                outcomes.append({"class": cls, "disposition": disp, "outcome": "RE-ENACTED",
                                  "principal": name, "led_stdout": r.stdout.strip()})
            elif _is_principal_name_collision(r.stderr):
                match = _compare_existing_principal(dep, name, agent_class, purpose_src)
                if match is True:
                    outcomes.append({"class": cls, "disposition": disp,
                                      "outcome": "SUPERSEDED-BY-KERNEL", "principal": name,
                                      "reason": "already present in the successor with the "
                                                "SAME agent_class and purpose (birth-standard "
                                                "or an earlier ingestion pass) -- not "
                                                "re-registered"})
                else:
                    # False (genuinely differs) and None (inconclusive -- no comparison view, or
                    # no matching row despite the name-unique-constraint refusal) are BOTH
                    # refused loudly here: a name collision is never silently merged into
                    # whichever identity already holds the name, matching or not.
                    detail = ("differs from" if match is False else
                              "could not be compared against (no principal_standing_current "
                              "view, or no row for this name, on the successor)")
                    outcomes.append({"class": cls, "disposition": disp, "outcome": "DROPPED",
                                      "principal": name,
                                      "reason": f"REFUSED -- '{name}' already exists in the "
                                                f"successor as a DIFFERENT identity ({detail} "
                                                f"the dust world's own agent_class={agent_class!r}"
                                                f"/purpose={purpose_src!r}) -- this is a genuine "
                                                f"name collision between two distinct "
                                                f"principals, not a duplicate registration. The "
                                                f"maintainer must disposition it explicitly at "
                                                f"the manifest (rename-carry the dust principal "
                                                f"under a new name, or drop-with-reason) -- "
                                                f"never silently merged into the existing "
                                                f"identity."})
            else:
                outcomes.append({"class": cls, "disposition": disp, "outcome": "DROPPED",
                                  "principal": name, "reason": f"led refused: {r.stderr.strip()}"})

        elif cls == "1.2_standing_decisions":
            statement = f"{marker} {item['statement']}"
            grade_args = ["--grade", item["grade"]] if item.get("grade") else []
            r = _run_led(led, ["--refs", refs, "decision", *grade_args, statement],
                        actor=args.actor, cwd=project_root)
            outcomes.append(_generic_outcome(cls, disp, r))

        elif cls == "1.4_open_work":
            slug = item["slug"]
            title = f"{marker} {item['statement']}"
            r = _run_led(led, ["work", "open", slug, title, "--refs", refs],
                        actor=args.actor, cwd=project_root)
            outcomes.append(_generic_outcome(cls, disp, r, slug=slug))

        elif cls == "1.5_open_questions":
            statement = f"{marker} {item['statement']}"
            r = _run_led(led, ["--refs", refs, "question", statement],
                        actor=args.actor, cwd=project_root)
            outcomes.append(_generic_outcome(cls, disp, r))

        elif cls in ("1.13_principal_suspended", "1.14_principal_revoked"):
            # suspend/revoke are the ONLY two principal verbs that take a free-text reason (row
            # 1173's own grammar: "suspend/revoke... fold any non-flag remainder into a
            # free-text reason") -- so, and only for these two classes, the marker/provenance
            # convention every other carry-* class already uses fits verbatim.
            verb = "suspend" if cls == "1.13_principal_suspended" else "revoke"
            name = item["principal_fields"]["subject_name"]
            r = _run_led(led, ["principal", verb, name, f"{marker} {item['statement']}"],
                        actor=args.actor, cwd=project_root)
            outcomes.append(_generic_outcome(cls, disp, r, subject=name))

        elif cls == "1.15_principal_standing_declared":
            pf = item["principal_fields"]
            r = _run_led(led, ["principal", "declare-standing", pf["subject_name"],
                               "--db-role", pf["db_role"]], actor=args.actor, cwd=project_root)
            outcomes.append(_reenact_with_provenance(
                cls, disp, r, world=world, dust_row_ids=item.get("dust_row_ids", []), led=led,
                actor=args.actor, project_root=project_root, **pf))

        elif cls == "1.16_principal_relation_asserted":
            pf = item["principal_fields"]
            r = _run_led(led, ["principal", "relate", pf["subject_name"], pf["relation"],
                               pf["object_name"]], actor=args.actor, cwd=project_root)
            outcomes.append(_reenact_with_provenance(
                cls, disp, r, world=world, dust_row_ids=item.get("dust_row_ids", []), led=led,
                actor=args.actor, project_root=project_root, **pf))

        elif cls == "1.17_principal_role_bound":
            pf = item["principal_fields"]
            r = _run_led(led, ["principal", "bind-role", pf["subject_name"],
                               "--role", pf["role_name"]], actor=args.actor, cwd=project_root)
            outcomes.append(_reenact_with_provenance(
                cls, disp, r, world=world, dust_row_ids=item.get("dust_row_ids", []), led=led,
                actor=args.actor, project_root=project_root, **pf))

        elif cls == "1.18_principal_key_bound":
            pf = item["principal_fields"]
            # NEVER fabricate --possession-ref (s61 item 3): a fresh key bind needs a LIVE
            # proof-of-possession ceremony run against the SUCCESSOR world's own committed
            # keys/ (`led principal attest-possession`), which this tool cannot perform on the
            # operator's behalf -- there is no signature to forge one from. Attempted without
            # it deliberately, so `led`'s OWN teach-text (missing --possession-ref) is what
            # lands in this outcome's reason -- never invented, never silently skipped. IF a
            # manifest editor supplied --possession-ref by hand upstream (out of THIS tool's
            # own reach) and the bind succeeds, it still gets the same provenance sidecar every
            # other free-text-less verb does.
            r = _run_led(led, ["principal", "bind-key", pf["subject_name"],
                               "--fingerprint", pf["fingerprint"]],
                        actor=args.actor, cwd=project_root)
            outcomes.append(_reenact_with_provenance(
                cls, disp, r, world=world, dust_row_ids=item.get("dust_row_ids", []), led=led,
                actor=args.actor, project_root=project_root, **pf))

        elif cls == "1.19_principal_competence_granted":
            pf = item["principal_fields"]
            r = _run_led(led, ["principal", "grant-competence", pf["subject_name"],
                               "--activity", pf["activity"], "--band", pf["band"],
                               "--basis", pf["basis"]], actor=args.actor, cwd=project_root)
            outcomes.append(_reenact_with_provenance(
                cls, disp, r, world=world, dust_row_ids=item.get("dust_row_ids", []), led=led,
                actor=args.actor, project_root=project_root, **pf))

        elif cls == "1.21_resource_tier_ungraded":
            # THE STATEMENT KEEPS ITS GRAMMAR PREFIX INTACT -- fix round 2, finding 4 (the
            # sharpest one): prepending the marker ("re-asserted from X: resource: ...") made the
            # carried row FAIL `statement.startswith('resource:')`, so it silently bypassed
            # cmd_generic's own tier validator, would never be recognized by pickup's RESOURCES
            # reader, and would be MISSED by this very extractor's own `ILIKE 'resource:%'` query
            # at the successor's own next phoenix -- matrix hazard #2, reproduced by this tool's
            # first attempt at closing it. Provenance moves entirely to --refs (`refs` already
            # carries the marker + dust world's own refs citation); the statement written here is
            # the ORIGINAL, unprefixed, grammar-valid text, verbatim.
            statement = item["statement"]
            r = _run_led(led, ["--refs", refs, "decision", statement],
                        actor=args.actor, cwd=project_root)
            outcomes.append(_generic_outcome(cls, disp, r))

        else:
            outcomes.append({"class": cls, "disposition": disp, "outcome": "DROPPED",
                              "reason": f"no ingestion handler for class {cls!r}"})

    for o in outcomes:
        print(json.dumps(o, sort_keys=True))

    refused = [o for o in outcomes if o["outcome"] == "DROPPED" and "led refused" in (o.get("reason") or "")]
    print(f"\nextract-context ingest: {len(outcomes)} item(s) processed, "
          f"{sum(1 for o in outcomes if o['outcome'].startswith('RE-'))} re-enacted/re-asserted, "
          f"{sum(1 for o in outcomes if o['outcome'] == 'SUPERSEDED-BY-KERNEL')} superseded-by-kernel, "
          f"{sum(1 for o in outcomes if o['outcome'] == 'DROPPED')} dropped.", file=sys.stderr)
    return 1 if refused else 0


# ----------------------------------------------------------------------------------------- main

def main() -> int:
    p = argparse.ArgumentParser(prog="extract-context", description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    pe = sub.add_parser("extract", help="read-only: emit a manifest from a source world")
    pe.add_argument("--deployment", required=True, help="path to the SOURCE deployment.json")
    pe.add_argument("--out", default="-", help="manifest output path (default: stdout)")
    pe.add_argument("--mode", choices=["in-world", "outside-read"], default="outside-read",
                     help="consult §2.1: in-world if this IS the predecessor's own final "
                          "ledgered act; outside-read (default) is the degraded fallback")
    pe.add_argument("--principal", default="extract-context-tool",
                     help="name recorded as the extracting principal in the provenance block")
    pe.set_defaults(func=cmd_extract)

    pi = sub.add_parser("ingest", help="writes THROUGH the target's own led, reviewed manifest only")
    pi.add_argument("--manifest", required=True, help="path to a REVIEWED manifest")
    pi.add_argument("--deployment", required=True, help="path to the TARGET deployment.json")
    pi.add_argument("--actor", required=True, help="LED_ACTOR set explicitly on every write")
    pi.set_defaults(func=cmd_ingest)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
