#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T00:11:32Z
#   last-change: 2026-07-18T22:51:43Z
#   contributors: e4410ef6/main, a857c93d/main, ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""record_reading -- the filing path for stores/001_research_ledger.sql (the PROJECT-AGNOSTIC
measurement-provenance ledger: core.project/core.session + research.instrument/research.reading/
research.finding + the derived research.finding_confirmed view). Sibling of filing/file_finding.py:
same psql-subprocess transport, same `:'var'`-injection-safe idiom, same trigger-idiom-respecting
posture (research.reading is DB-trigger-frozen; this module never attempts UPDATE/DELETE on it).

INHERITED from chocofarm's throughput-lab/harness/exp_db.py (the working precedent this store
adapts) -- kept because the failure classes it forecloses are real and would recur here unchanged:
  * measurement (research.reading) is IMMUTABLE -- enforced at the DB (freeze_reading trigger), not
    merely by this module's own discipline; this module never issues UPDATE/DELETE on it.
  * content-hash APPARATUS dedupe: upsert_instrument mirrors exp_db's upsert_config -- an
    INSERT ... ON CONFLICT (project_id, source_hash) DO NOTHING then SELECT, so a harness that
    re-registers the SAME built apparatus every run converges on ONE instrument row rather than
    flooding the table (the UNIQUE constraint this filing module relies on was itself a 2026-07-11
    scratch-validation fix to 001_research_ledger.sql -- see that file's instrument table comment).
  * DERIVED-VALUE CONSTRUCTION-TIME REFUSAL (exp_db's Reading.__post_init__, forecloses chocofarm's
    finding-12 class: a rate recorded with -- or inconsistent with -- operands from a DIFFERENT
    measurement window). `Reading.derived_from=(num_key, den_key)` names two keys the caller ALSO
    put in `raw_operands`; if the caller claims `value` is that ratio, __post_init__ recomputes it
    and raises before any SQL is even built. Generalized from exp_db's fixed rate columns (dps,
    leaf_rows_s, ...) to 001's metric-name-agnostic shape: raw_operands rides in `research.reading
    .config` (the schema's own long-tail seam), keyed by whatever names the caller's metric uses.
    Declaring no `derived_from` (the common case -- most readings, e.g. run7's `distance` and
    `tolerance`, are direct observations with nothing to derive) skips the check entirely; nothing
    is invented to check where the caller asserted no derivation relationship.

DELIBERATELY DIVERGED from exp_db, each divergence load-bearing, not an oversight:
  1. **Transport is psql subprocess** (`-v name=value`, `:'var'` string-literal substitution),
     NOT psycopg3. This repo has no psycopg dependency (`ModuleNotFoundError` confirmed 2026-07-11)
     and filing/'s existing modules (file_finding.py, file_resolution.py) already establish the
     psql-CLI convention for exactly this class of store -- this module follows the house style
     rather than importing a transport the project does not otherwise use.
  2. **git_tree vocabulary is 001's own, lowercase {'clean','dirty'}** (the CHECK 001 actually
     declares), NOT exp_db's uppercase {'clean','DIRTY'}. Confirmed live 2026-07-11: an uppercase
     'DIRTY' value is REFUSED by 001's `reading_git_tree_check` (mirroring `instrument_git_tree_
     check`) -- this module validates against 001's vocabulary, not exp_db's.
  3. **Confirmation is strictly DERIVED, never writable.** 001's `research.finding.status` CHECK
     is `{'provisional','retracted'}` ONLY -- 'confirmed' is not a member (unlike exp_db's tlab_
     finding.status, a writable tri-state that includes 'confirmed'). `research.finding_confirmed`
     computes confirmation from clean-tree + qualified-instrument + not-superseded + attributed;
     nothing here can assert it. `record_finding`'s `status` choices mirror 001's CHECK exactly.
  4. **No first-class command/tool/tag columns.** 001 folds them into `research.reading.config`
     jsonb (the schema's deliberate long-tail seam, scoped down from exp_db's tlab_reading by the
     ADR-0014 second opinion, 2026-06-28 -- not an oversight this module should paper over).
  5. **No `ensure-schema` verb here.** file_finding.py's sibling module owns its DDL directly, but
     001's apply is a SEPARATE, maintainer-gated ceremony (bootstrap/apply-research-ledger.sh,
     "prints exactly what it will do first") -- giving this filing module its own silent schema-
     apply path would create a second owner of the same DDL (ADR-0012 P1). If `research.reading`
     does not yet exist, psql's own "relation does not exist" error is the fail-loud signal
     (ADR-0002) -- run bootstrap/apply-research-ledger.sh first.

CONNECTION -- resolved from explicit args or environment, NEVER hardcoded to one deployment:
  --host / RL_PGHOST (else this deployment's own deployment.json 'host' field, else a loud
                       refusal naming both -- see filing/pghost_resolve.py; never a silent
                       default to any host)
  --db   / RL_DB     (default 'research' -- the STANDING db 001 targets; NEVER 'harness', a
                       different store filing/file_finding.py owns)
  --core-schema / RL_CORE_SCHEMA (default 'core'), --research-schema / RL_RESEARCH_SCHEMA
  (default 'research') -- overridable so this EXACT module can be pointed at a scratch schema
  pair (e.g. rlprobe_core/rlprobe_research) for validation, never a parallel test-only copy.

CLI:
  record_reading.py record-reading --project P --session S \
      [--instrument-id ID | --instrument-name N --instrument-kind K --source-hash H \
        --instrument-git-commit C --instrument-git-tree {clean,dirty} \
        [--instrument-build-recipe JSON] [--instrument-qualification Q]] \
      --metric M (--value V | --value-text T) [--unit U] [--n N] [--stderr S] \
      [--raw-operands JSON] [--derived-from NUM_KEY,DEN_KEY] \
      --git-commit C --git-tree {clean,dirty} [--observed-at ISO8601] [--subject S] \
      [--command CMD] [--tag TAG] [--project-name NAME] [--session-model M] [--session-summary S]
  record_reading.py record-finding --project P --reading ID --interpretation TEXT \
      [--motivation TEXT] [--status provisional|retracted] [--supersedes ID] \
      [--session S] [--git-commit C]

Every import is top-of-file (lazy-import edict, gates/no_lazy_imports.py).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

import pghost_resolve  # filing/pghost_resolve.py, the ONE home -- never a literal host default

PGHOST = pghost_resolve.resolve_pghost("RL_PGHOST")
DB = os.environ.get("RL_DB", "research")
CORE_SCHEMA = os.environ.get("RL_CORE_SCHEMA", "core")
RESEARCH_SCHEMA = os.environ.get("RL_RESEARCH_SCHEMA", "research")

GIT_TREE_VALUES = ("clean", "dirty")                       # 001's own CHECK vocabulary (lowercase)
INSTRUMENT_KINDS = ("benchmark", "probe", "script", "harness")   # research.instrument.kind CHECK
FINDING_STATUSES = ("provisional", "retracted")             # research.finding.status CHECK --
                                                              # 'confirmed' is DERIVED, never a member


class RecordReadingError(Exception):
    """A caller-supplied value would be rejected before (or by) the database -- raised, never
    swallowed (ADR-0002). Construction-time refusals (bad enum, inconsistent derived value) raise
    this before any SQL is built; a DB-side refusal (a CHECK/trigger this module didn't pre-check)
    surfaces psql's own stderr, wrapped the same way."""


def _psql(sql: str, *, params: Mapping[str, str] | None = None,
          host: str = PGHOST, db: str = DB) -> str:
    """Run one statement/batch through psql with `-v name=value` parameters (the injection-safe
    `:'name'` substitution idiom file_finding.py already established), `-tA` (unaligned, no
    header) so a caller can parse the output directly. Raises RecordReadingError with psql's own
    stderr on any non-zero exit -- fail loud (ADR-0002), never a silent None."""
    cmd = ["psql", "-h", host, "-d", db, "-tA", "-v", "ON_ERROR_STOP=1"]
    for k, v in (params or {}).items():
        cmd += ["-v", f"{k}={v}"]
    r = subprocess.run(cmd, input=sql, capture_output=True, text=True)
    if r.returncode != 0:
        raise RecordReadingError(f"psql failed ({r.returncode}): {r.stderr.strip()}")
    return r.stdout.strip()


def _canonical(m: Mapping[str, Any]) -> Any:
    """Stable, sorted-key JSON-able representation (for embedding in a jsonb literal deterministically)."""
    if isinstance(m, Mapping):
        return {k: _canonical(m[k]) for k in sorted(m)}
    if isinstance(m, (list, tuple)):
        return [_canonical(x) for x in m]
    return m


# ============================================================================================
# Typed records -- the contract. Mirrors exp_db's frozen-dataclass-is-the-signature posture
# (ADR-0012 P8 / ADR-0000): an illegal git_tree, kind, or status is unrepresentable at construction.
# ============================================================================================
@dataclass(frozen=True)
class InstrumentKey:
    """The apparatus that produced a reading -- content-hash deduped on (project_id, source_hash)
    by upsert_instrument (mirrors exp_db's ConfigKey/upsert_config)."""
    project_id: str
    name: str
    kind: str
    source_hash: str
    git_commit: str
    git_tree: str
    build_recipe: Mapping[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    qualification: str = "provisional"

    def __post_init__(self) -> None:
        if self.kind not in INSTRUMENT_KINDS:
            raise RecordReadingError(f"InstrumentKey.kind must be one of {INSTRUMENT_KINDS}, got {self.kind!r}")
        if self.git_tree not in GIT_TREE_VALUES:
            raise RecordReadingError(
                f"InstrumentKey.git_tree must be one of {GIT_TREE_VALUES} (001's own CHECK -- "
                f"NOT exp_db's uppercase 'DIRTY'), got {self.git_tree!r}")
        for f in ("project_id", "name", "source_hash", "git_commit"):
            if not getattr(self, f):
                raise RecordReadingError(f"InstrumentKey.{f} must be non-empty (ADR-0002)")


@dataclass(frozen=True)
class Reading:
    """One measurement. `raw_operands` rides in research.reading.config (the long-tail jsonb seam);
    `derived_from=(num_key, den_key)` asserts `value == raw_operands[num_key] / raw_operands[den_key]`
    and is checked HERE, at construction, before any SQL exists -- forecloses chocofarm's finding-12
    class (a derived rate recorded without, or inconsistent with, its own operands). Declaring no
    `derived_from` (the common case for a direct observation) skips the check entirely."""
    project_id: str
    metric: str
    git_commit: str
    git_tree: str
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    n: Optional[int] = None
    stderr: Optional[float] = None
    raw_operands: Mapping[str, float] = field(default_factory=dict)
    derived_from: Optional[tuple[str, str]] = None
    subject_id: Optional[str] = None
    observed_at: Optional[str] = None                      # ISO8601, writer-supplied; NULL if unknown
    session_id: Optional[str] = None
    command: Optional[str] = None                           # folded into config (001 has no own column)
    tag: Optional[str] = None                                # folded into config (001 has no own column)
    tolerance_rel: float = 0.02                              # relative tolerance for derived_from's check

    def __post_init__(self) -> None:
        if self.value is None and self.value_text is None:
            raise RecordReadingError(
                "Reading requires value OR value_text (research.reading's own CHECK -- "
                "a reading must record an outcome; ADR-0002)")
        if self.git_tree not in GIT_TREE_VALUES:
            raise RecordReadingError(
                f"Reading.git_tree must be one of {GIT_TREE_VALUES} (001's own CHECK -- "
                f"NOT exp_db's uppercase 'DIRTY'), got {self.git_tree!r}")
        if not self.project_id or not self.metric:
            raise RecordReadingError("Reading.project_id and Reading.metric must be non-empty (ADR-0002)")
        if self.derived_from is not None:
            num_key, den_key = self.derived_from
            if self.value is None:
                raise RecordReadingError(
                    "Reading.derived_from is set but value is None -- a claimed derivation needs "
                    "the derived VALUE to check it against (ADR-0002)")
            num = self.raw_operands.get(num_key)
            den = self.raw_operands.get(den_key)
            if num is None or den is None:
                raise RecordReadingError(
                    f"Reading.value={self.value} claims derivation from "
                    f"{num_key}/{den_key}, but raw_operands is missing one or both keys "
                    f"(raw_operands={dict(self.raw_operands)!r}) -- a rate stored without its "
                    f"operands is the un-recomputable, un-checkable shape that produced chocofarm's "
                    f"finding-12 artifact (exp_db.py Reading.__post_init__): record the operands, "
                    f"or omit derived_from.")
            if float(den) == 0.0:
                raise RecordReadingError(f"Reading.derived_from: {den_key} is 0 -- cannot derive a rate (ADR-0002)")
            expected = float(num) / float(den)
            tol = max(self.tolerance_rel * abs(expected), 1e-9)
            if abs(float(self.value) - expected) > tol:
                raise RecordReadingError(
                    f"Reading.value={self.value} is INCONSISTENT with {num_key}/{den_key}="
                    f"{num}/{den}={expected:.6g} (|delta|>{tol:.3g}) -- a rate whose numerator and "
                    f"denominator come from a different measurement than the one it is stored "
                    f"against is chocofarm's finding-12 class; foreclosed at construction, not "
                    f"caught downstream (exp_db.py Reading.__post_init__).")

    def config_json(self) -> dict[str, Any]:
        """The `config` jsonb payload: raw_operands + command/tag folded in (001's long-tail seam)."""
        cfg: dict[str, Any] = dict(self.raw_operands)
        if self.command is not None:
            cfg["command"] = self.command
        if self.tag is not None:
            cfg["tag"] = self.tag
        return _canonical(cfg)


# ============================================================================================
# The write API.
# ============================================================================================
def ensure_project(project_id: str, name: Optional[str] = None, *,
                    host: str = PGHOST, db: str = DB, core_schema: str = CORE_SCHEMA) -> None:
    """Idempotently ensure `project_id` exists in core.project. A missing --project-name on a
    FIRST insert falls back to project_id itself (name is NOT NULL); an existing project is never
    renamed by this call (ON CONFLICT DO NOTHING -- the project row is not this module's to edit)."""
    _psql(
        'INSERT INTO :"core_schema".project (project_id, name) VALUES (:\'pid\', :\'name\') '
        "ON CONFLICT (project_id) DO NOTHING;",
        params={"core_schema": core_schema, "pid": project_id, "name": name or project_id},
        host=host, db=db)


def ensure_session(session_id: str, project_id: str, *, model: Optional[str] = None,
                    summary: Optional[str] = None, host: str = PGHOST, db: str = DB,
                    core_schema: str = CORE_SCHEMA) -> None:
    """Idempotently ensure `session_id` exists in core.session, attributed to `project_id`."""
    _psql(
        'INSERT INTO :"core_schema".session (session_id, project_id, model, summary) '
        "VALUES (:'sid', :'pid', NULLIF(:'model',''), NULLIF(:'summary','')) "
        "ON CONFLICT (session_id) DO NOTHING;",
        params={"core_schema": core_schema, "sid": session_id, "pid": project_id,
                "model": model or "", "summary": summary or ""},
        host=host, db=db)


def upsert_instrument(key: InstrumentKey, *, host: str = PGHOST, db: str = DB,
                       research_schema: str = RESEARCH_SCHEMA) -> int:
    """Insert the instrument if (project_id, source_hash) is new, else return the existing row's
    id (the dedupe seam -- mirrors exp_db's upsert_config). Requires 001's `UNIQUE (project_id,
    source_hash)` constraint (2026-07-11 scratch-validation fix)."""
    # WITH ... RETURNING wrapped as a SELECT (file_finding.py's own idiom): psql -tA does NOT
    # suppress the "INSERT 0 1" command-completion tag on a bare INSERT ... RETURNING (only a
    # SELECT's tag is suppressed under tuples-only) -- wrapping keeps stdout to exactly the id.
    out = _psql(
        'WITH ins AS (INSERT INTO :"research_schema".instrument '
        "(project_id, name, kind, source_hash, build_recipe, git_commit, git_tree, session_id, qualification) "
        "VALUES (:'pid', :'name', :'kind', :'hash', :'recipe'::jsonb, :'commit', :'tree', "
        "        NULLIF(:'sid',''), :'qual') "
        "ON CONFLICT (project_id, source_hash) DO NOTHING RETURNING instrument_id) "
        "SELECT instrument_id FROM ins;",
        params={"research_schema": research_schema, "pid": key.project_id, "name": key.name,
                "kind": key.kind, "hash": key.source_hash,
                "recipe": json.dumps(_canonical(key.build_recipe)), "commit": key.git_commit,
                "tree": key.git_tree, "sid": key.session_id or "", "qual": key.qualification},
        host=host, db=db)
    if out:
        return int(out)
    out = _psql(
        'SELECT instrument_id FROM :"research_schema".instrument '
        "WHERE project_id = :'pid' AND source_hash = :'hash';",
        params={"research_schema": research_schema, "pid": key.project_id, "hash": key.source_hash},
        host=host, db=db)
    if not out:
        raise RecordReadingError(
            f"upsert_instrument: instrument (project={key.project_id!r}, source_hash="
            f"{key.source_hash!r}) neither inserted nor found -- contract break")
    return int(out)


def record_reading(reading: Reading, *, instrument_id: Optional[int] = None,
                    instrument: Optional[InstrumentKey] = None,
                    host: str = PGHOST, db: str = DB, research_schema: str = RESEARCH_SCHEMA) -> int:
    """Insert one reading. Exactly one of `instrument_id` (reuse an already-registered apparatus)
    or `instrument` (upsert/dedupe one now, mirroring exp_db's record_reading calling upsert_config
    internally) must be given. Raises RecordReadingError on a bad arg combination, a construction-
    time refusal (already raised by Reading.__post_init__ before this is even called), or a DB
    fault. Returns the new reading_id."""
    if (instrument_id is None) == (instrument is None):
        raise RecordReadingError(
            "record_reading: pass exactly one of instrument_id or instrument (an apparatus is "
            "required to file a reading against -- research.reading.instrument_id is NOT NULL)")
    if instrument is not None:
        instrument_id = upsert_instrument(instrument, host=host, db=db, research_schema=research_schema)
    out = _psql(
        'WITH ins AS (INSERT INTO :"research_schema".reading '
        "(project_id, instrument_id, subject_id, metric, value, value_text, unit, n, stderr, "
        " config, git_commit, git_tree, observed_at, session_id) "
        "VALUES (:'pid', :iid, NULLIF(:'subj',''), :'metric', NULLIF(:'val','')::double precision, "
        "        NULLIF(:'valtext',''), NULLIF(:'unit',''), NULLIF(:'n','')::integer, "
        "        NULLIF(:'stderr','')::double precision, :'config'::jsonb, :'commit', :'tree', "
        "        NULLIF(:'obsat','')::timestamptz, NULLIF(:'sid','')) "
        "RETURNING reading_id) SELECT reading_id FROM ins;",
        params={"research_schema": research_schema, "pid": reading.project_id, "iid": str(instrument_id),
                "subj": reading.subject_id or "", "metric": reading.metric,
                "val": "" if reading.value is None else repr(reading.value),
                "valtext": reading.value_text or "", "unit": reading.unit or "",
                "n": "" if reading.n is None else str(reading.n),
                "stderr": "" if reading.stderr is None else repr(reading.stderr),
                "config": json.dumps(reading.config_json()), "commit": reading.git_commit,
                "tree": reading.git_tree, "obsat": reading.observed_at or "",
                "sid": reading.session_id or ""},
        host=host, db=db)
    if not out:
        raise RecordReadingError("record_reading: INSERT ... RETURNING yielded no reading_id")
    return int(out)


def record_finding(project_id: str, reading_id: int, interpretation: str, *,
                    motivation: Optional[str] = None, status: str = "provisional",
                    supersedes: Optional[int] = None, session_id: Optional[str] = None,
                    git_commit: Optional[str] = None,
                    host: str = PGHOST, db: str = DB, research_schema: str = RESEARCH_SCHEMA) -> int:
    """Append ONE authored belief about `reading_id` (append-only -- a corrected belief is a NEW
    finding with `supersedes` set; the prior row is never rewritten). `status` is 001's own CHECK
    vocabulary {'provisional','retracted'} -- 'confirmed' is DERIVED (research.finding_confirmed),
    never assertable here; passing it raises before the DB even sees it (fail loud earlier, not
    just at the CHECK). Raises on a bad status / empty interpretation / DB fault (ADR-0002)."""
    if status not in FINDING_STATUSES:
        raise RecordReadingError(
            f"record_finding: status must be one of {FINDING_STATUSES} -- 'confirmed' is DERIVED "
            f"by research.finding_confirmed, never writable here (ADR-0014 2026-06-28: stricter "
            f"than exp_db's writable tri-state, by design); got {status!r}")
    if not interpretation or not interpretation.strip():
        raise RecordReadingError("record_finding: interpretation is the load-bearing field -- must be non-empty")
    out = _psql(
        'WITH ins AS (INSERT INTO :"research_schema".finding '
        "(project_id, reading_id, motivation, interpretation, status, supersedes, session_id, git_commit) "
        "VALUES (:'pid', :rid, NULLIF(:'motiv',''), :'interp', :'status', NULLIF(:'sup','')::bigint, "
        "        NULLIF(:'sid',''), NULLIF(:'commit','')) "
        "RETURNING finding_id) SELECT finding_id FROM ins;",
        params={"research_schema": research_schema, "pid": project_id, "rid": str(reading_id),
                "motiv": motivation or "", "interp": interpretation, "status": status,
                "sup": "" if supersedes is None else str(supersedes),
                "sid": session_id or "", "commit": git_commit or ""},
        host=host, db=db)
    if not out:
        raise RecordReadingError("record_finding: INSERT ... RETURNING yielded no finding_id")
    return int(out)


# ============================================================================================
# CLI
# ============================================================================================
def _common_conn_args(ap: argparse.ArgumentParser) -> None:
    ap.add_argument("--host", default=PGHOST)
    ap.add_argument("--db", default=DB)
    ap.add_argument("--core-schema", default=CORE_SCHEMA)
    ap.add_argument("--research-schema", default=RESEARCH_SCHEMA)


def cmd_record_reading(a: argparse.Namespace) -> int:
    ensure_project(a.project, a.project_name, host=a.host, db=a.db, core_schema=a.core_schema)
    if a.session:
        ensure_session(a.session, a.project, model=a.session_model, summary=a.session_summary,
                        host=a.host, db=a.db, core_schema=a.core_schema)
    raw_operands = json.loads(a.raw_operands) if a.raw_operands else {}
    derived_from = None
    if a.derived_from:
        parts = a.derived_from.split(",")
        if len(parts) != 2:
            raise SystemExit("--derived-from expects NUM_KEY,DEN_KEY")
        derived_from = (parts[0], parts[1])
    reading = Reading(
        project_id=a.project, metric=a.metric, git_commit=a.git_commit, git_tree=a.git_tree,
        value=a.value, value_text=a.value_text, unit=a.unit, n=a.n, stderr=a.stderr,
        raw_operands=raw_operands, derived_from=derived_from, subject_id=a.subject,
        observed_at=a.observed_at, session_id=a.session, command=a.command, tag=a.tag)
    if a.instrument_id is not None:
        rid = record_reading(reading, instrument_id=a.instrument_id, host=a.host, db=a.db,
                              research_schema=a.research_schema)
    else:
        if not (a.instrument_name and a.instrument_kind and a.source_hash
                and a.instrument_git_commit and a.instrument_git_tree):
            raise SystemExit(
                "record-reading: pass --instrument-id, or all of --instrument-name/--instrument-kind/"
                "--source-hash/--instrument-git-commit/--instrument-git-tree")
        recipe = json.loads(a.instrument_build_recipe) if a.instrument_build_recipe else {}
        key = InstrumentKey(project_id=a.project, name=a.instrument_name, kind=a.instrument_kind,
                             source_hash=a.source_hash, git_commit=a.instrument_git_commit,
                             git_tree=a.instrument_git_tree, build_recipe=recipe,
                             session_id=a.session, qualification=a.instrument_qualification)
        rid = record_reading(reading, instrument=key, host=a.host, db=a.db,
                              research_schema=a.research_schema)
    print(rid)
    return 0


def cmd_record_finding(a: argparse.Namespace) -> int:
    fid = record_finding(a.project, a.reading, a.interpretation, motivation=a.motivation,
                          status=a.status, supersedes=a.supersedes, session_id=a.session,
                          git_commit=a.git_commit, host=a.host, db=a.db,
                          research_schema=a.research_schema)
    print(fid)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    rr = sub.add_parser("record-reading", help="file one measurement into research.reading")
    _common_conn_args(rr)
    rr.add_argument("--project", required=True)
    rr.add_argument("--project-name", default=None)
    rr.add_argument("--session", default=None)
    rr.add_argument("--session-model", default=None)
    rr.add_argument("--session-summary", default=None)
    rr.add_argument("--instrument-id", type=int, default=None)
    rr.add_argument("--instrument-name", default=None)
    rr.add_argument("--instrument-kind", choices=INSTRUMENT_KINDS, default=None)
    rr.add_argument("--source-hash", default=None)
    rr.add_argument("--instrument-git-commit", default=None)
    rr.add_argument("--instrument-git-tree", choices=GIT_TREE_VALUES, default=None)
    rr.add_argument("--instrument-build-recipe", default=None, help="JSON object")
    rr.add_argument("--instrument-qualification", default="provisional")
    rr.add_argument("--metric", required=True)
    rr.add_argument("--value", type=float, default=None)
    rr.add_argument("--value-text", default=None)
    rr.add_argument("--unit", default=None)
    rr.add_argument("--n", type=int, default=None)
    rr.add_argument("--stderr", type=float, default=None)
    rr.add_argument("--raw-operands", default=None, help="JSON object, e.g. '{\"leaves\":1000,\"wall_s\":4.2}'")
    rr.add_argument("--derived-from", default=None, help="NUM_KEY,DEN_KEY into --raw-operands")
    rr.add_argument("--subject", default=None)
    rr.add_argument("--git-commit", required=True)
    rr.add_argument("--git-tree", choices=GIT_TREE_VALUES, required=True)
    rr.add_argument("--observed-at", default=None, help="ISO8601")
    rr.add_argument("--command", default=None)
    rr.add_argument("--tag", default=None)

    rf = sub.add_parser("record-finding", help="append one interpretation into research.finding")
    _common_conn_args(rf)
    rf.add_argument("--project", required=True)
    rf.add_argument("--reading", type=int, required=True)
    rf.add_argument("--interpretation", required=True)
    rf.add_argument("--motivation", default=None)
    rf.add_argument("--status", choices=FINDING_STATUSES, default="provisional")
    rf.add_argument("--supersedes", type=int, default=None)
    rf.add_argument("--session", default=None)
    rf.add_argument("--git-commit", default=None)

    a = ap.parse_args(argv)
    try:
        if a.cmd == "record-reading":
            return cmd_record_reading(a)
        if a.cmd == "record-finding":
            return cmd_record_finding(a)
    except RecordReadingError as e:
        print(f"record_reading: REFUSED -- {e}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
