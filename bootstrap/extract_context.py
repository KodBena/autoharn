#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-22T02:32:51Z
#   last-change: 2026-07-22T02:42:43Z
#   contributors: 1fa3ab69/main
# <<< PROVENANCE-STAMP <<<

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
                                                     wanted, is ingestion-side re-reading)
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
    "1.6": "resources registry has no distinct ledger `kind` — resource rows are ordinary "
           "kind=decision rows, already covered by class 1.2's query",
    "1.8": "estimates/actuals have no ledger `kind` in this kernel lineage (ledger_kind_check "
           "carries no 'estimate' member) — nothing to SELECT; CITE-ONLY is moot here",
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
    part of it) and the CSV block's own header row (column names), leaving just data rows."""
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

    vc_path = project_root / "verify-chain"
    if vc_path.exists() and os.access(vc_path, os.X_OK):
        r = subprocess.run([str(vc_path)], capture_output=True, text=True,
                            cwd=str(project_root), timeout=60)
        verify_chain_output = (r.stdout + r.stderr).strip()
    else:
        verify_chain_output = f"UNAVAILABLE: no executable verify-chain shim at {vc_path}"

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
    """1.1 Identity: the principal roster — carry-reopened (RE-ENACT)."""
    r = _psql_tuples(dep, f"SELECT id, name, agent_class FROM {dep.kern}.principal ORDER BY id;")
    items = []
    for pid, name, agent_class in _rows(r):
        items.append({
            "record": "item", "class": "1.1_principal_roster", "disposition": "carry-reopened",
            "dust_row_ids": [], "row_kind": "principal", "principal_id": pid,
            "statement": f"principal '{name}' (class {agent_class})",
            "actor_attribution": {"agent_class": agent_class, "name": name},
            "refs": f"{dep.name}:principal:{pid}",
            "reason": None,
        })
    return items


def extract_standing_decisions(dep) -> list[dict]:
    """1.2/1.3 Standing decisions and procedures — carry-verbatim (RE-ASSERT)."""
    if not _relation_exists(dep, dep.schema, "standing_decisions"):
        return [{"record": "class-summary", "class": "1.2_standing_decisions",
                  "disposition": "drop-with-reason", "count": 0,
                  "reason": "UNAVAILABLE: this world's kernel predates s36 "
                            "(standing_decisions does not exist)"}]
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


def extract_all(dep) -> list[dict]:
    items: list[dict] = []
    items += extract_principals(dep)
    items += extract_standing_decisions(dep)
    items += extract_open_work(dep)
    items += extract_open_questions(dep)
    items += extract_drop_and_never(dep)
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


def _find_led(project_root: Path) -> Path | None:
    """legacy/led (the direct-psql original) is preferred over ./led (the boundary_url/
    boundary_deployment-requiring HTTP client, bootstrap/templates/led.tmpl) here specifically:
    ingestion is a batch of ordinary attributed writes into a target world that need not have a
    boundary service wired or running at all -- requiring one would make this tool depend on
    serving infrastructure orthogonal to its own job. If a deployment has no legacy/led (an
    older pre-split scaffold, MAINT-EXPERIENCE-REBIRTH-RUNBOOK.md Step 1's own witnessed case),
    fall back to ./led."""
    for cand in (project_root / "legacy" / "led", project_root / "led"):
        if cand.exists() and os.access(cand, os.X_OK):
            return cand
    return None


def _run_led(led: Path, args: list[str], actor: str, cwd: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["LED_ACTOR"] = actor  # EVERY invocation sets this explicitly (row 1943 lesson (a)) --
    # never inherited from whatever the ambient environment happened to carry.
    return subprocess.run([str(led), *args], capture_output=True, text=True, cwd=str(cwd), env=env)


REASSERT_MARKER = "re-asserted from {world}:"


def _generic_outcome(cls: str, disp: str, r: subprocess.CompletedProcess, **extra) -> dict:
    if r.returncode == 0:
        outcome = "RE-ASSERTED" if disp == "carry-verbatim" else "RE-ENACTED"
        return {"class": cls, "disposition": disp, "outcome": outcome,
                "led_stdout": r.stdout.strip(), **extra}
    return {"class": cls, "disposition": disp, "outcome": "DROPPED",
            "reason": f"led refused: {r.stderr.strip()}", **extra}


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
            r = _run_led(led, ["register-principal", name, agent_class, "--purpose",
                               f"{marker} re-registered per extract from {world}"],
                        actor=args.actor, cwd=project_root)
            if r.returncode == 0:
                outcomes.append({"class": cls, "disposition": disp, "outcome": "RE-ENACTED",
                                  "principal": name, "led_stdout": r.stdout.strip()})
            elif "already registered" in r.stderr:
                outcomes.append({"class": cls, "disposition": disp,
                                  "outcome": "SUPERSEDED-BY-KERNEL",
                                  "principal": name,
                                  "reason": "already registered in target world (birth-standard "
                                            "or an earlier ingestion pass) -- not re-registered"})
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
