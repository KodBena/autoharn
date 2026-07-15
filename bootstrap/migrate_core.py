#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T21:20:36Z
#   last-change: 2026-07-15T06:57:48Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""migrate_core -- the engine behind `bootstrap/migrate.sh` / the root `./migrate` shim
(tracker item migration-script-stable-interface, 2026-07-14 late commission directive 2:
"~/ent WILL be migrated, BY THE MAINTAINER HIMSELF, using an idiot-proof FORWARD-COMPATIBLE
script; ... users should NEVER under any circumstances have to learn anything new about how the
migration script works, across all future feature migrations").

STABLE USER SURFACE, forever (this is the deliverable -- everything below exists to keep this
surface unchanged as kernel/lineage/ grows):

    ./migrate <deployment-dir>              -- rehearse, ask ONE typed confirmation, apply
    ./migrate <deployment-dir> --dry-run     -- rehearse and print the evidence; never asks,
                                                 never touches live

No other flag, mode, or argument shape is ever added to this surface -- a future kernel delta
(s30, s31, ...) changes what gets migrated, never how the operator invokes migration. See "THE
DATA-DRIVEN CHAIN" below for how that promise is kept mechanically, not by discipline alone.

WHAT ONE RUN DOES, IN ORDER (every step prints what-you-should-see; any deviation refuses
loudly and touches nothing further -- ADR-0002, ADR-0013 Rule 1):
  1. Load the deployment's deployment.json (filing/deployment_record.py -- the one SSOT parser
     every other verb in this project already uses; ADR-0012 P1, not a second reader).
  2. PROCESS CHECK -- refuse if any live process has its cwd under the deployment directory (a
     live Claude Code session, a stray shell, anything) -- migrating out from under a live
     session is exactly the class of hazard CLAUDE.md's "never modify hooks/ or a user project
     while a live session runs there" names for the harness's own files, applied here to the
     deployment's data.
  3. pg_dump the deployment's schema+kern to a timestamped file under ~/backups/, printed as the
     ROLLBACK ARTIFACT. This file is also the REHEARSAL's own data source (step 4), so the
     rehearsal proves the backup itself is restorable -- a backup nobody has restored is a claim,
     not a rollback path (ADR-0013 Rule 5: verify the artifact).
  4. THE DATA-DRIVEN CHAIN: compute which kernel/lineage/ deltas are missing (see below), and
     REHEARSE applying them to a scratch restore of the REAL backup -- never against live.
  5. Per-delta and whole-migration verification against the scratch copy (see "PER-DELTA
     VERIFICATION CONVENTION" below).
  6. On rehearsal PASS: print the full evidence summary, then ask EXACTLY ONE typed confirmation.
     `--dry-run` stops here, before asking anything, having done everything else.
  7. On confirmation: apply the SAME chain to LIVE, in one transaction (`psql -1`), then re-run
     the same verification against live.
  8. On success: record a decision row in the DEPLOYMENT'S OWN ledger (the migration recording
     itself, in the world it changed -- never in autoharn's own ledger).

THE DATA-DRIVEN CHAIN (the forward-compatibility mechanism -- read this before touching anything
below). This module contains NO delta names, NO sNN literals, anywhere in its source. The
ordered list of "what a from-scratch world's kernel is built from" already exists, as data, in
exactly one place: the `-f "$AUTOHARN_ROOT/kernel/lineage/....sql"` lines inside
`bootstrap/new-project.sh`'s own `--new-world` psql invocation -- the SAME lines a human
maintainer or a future delta's author already has to update the moment a new delta is "wired
into LINEAGE_CHAIN" (kernel/lineage/README.md's own words for that act). `_manifest()` below
parses those lines with a regex and nothing else; when s30 lands and gets wired into
new-project.sh (a required step for --new-world births regardless of this script's existence),
migrate.sh picks it up on its very next invocation, with zero edits here. This is P1 (ADR-0012)
applied at the process level: new-project.sh's own invocation IS the manifest; this module reads
it rather than re-typing a second copy that could drift.

"Current lineage head" is then determined by DETECTING, against the live schema, which manifest
entries are already applied -- see the next section for how, since filename order alone cannot
answer "is this one applied" (only presence in the manifest tells you it's canonical; whether the
target schema already carries it is a live catalog fact).

PER-DELTA VERIFICATION CONVENTION (documented here as the once-and-only description; every sibling
file below just implements it). Each `kernel/lineage/sNN-name.sql` manifest entry may carry TWO
sibling files, NEVER edits to the frozen sNN file itself (ADR-0005 Rule 8 -- a shipped generation
is a point-in-time record):

    kernel/lineage/sNN-name.detect.sql   (REQUIRED for every manifest entry -- see below)
    kernel/lineage/sNN-name.verify.sql   (OPTIONAL)

  - `.detect.sql` is exactly one SELECT, returning exactly one row and one boolean column
    aliased `applied` -- true iff this delta's objects are already present on the schema/kern
    named by the `:'schema'`/`:'kern'`/`:'role'` psql variables it is run with (the same
    variables the delta file itself takes). This is how migrate_core answers "what is the
    current head" and "what is missing" WITHOUT hardcoding a single delta name: it walks the
    manifest in order, running each entry's `.detect.sql`, and the first `false` is where the
    missing chain starts. A manifest entry with NO `.detect.sql` sibling is a REFUSAL at the
    very first step (see `_require_detect_files`) -- a delta wired into the birth chain without a
    detect query is a delta this script cannot safely place on the timeline, and guessing would
    be exactly the "invisible-at-authoring" defect ADR-0011 exists to convert into a mechanism,
    here converted into a loud, named refusal instead.
  - `.verify.sql` is zero or more SELECT statements, each returning exactly one row and one
    boolean column aliased `ok`, run AFTER this delta is applied (rehearsal AND live) to confirm
    its invariants hold -- not merely that its objects exist (`.detect.sql`'s job) but that they
    BEHAVE (a view returns the right rows, a constraint actually refuses the right shape). A
    delta with no `.verify.sql` sibling is not refused -- verification degrades to `.detect.sql`
    alone for that one delta, and this script says so plainly in its evidence summary rather than
    silently claiming a fuller check happened (ADR-0011 Rule 1: an absent mechanism is declared,
    never implied). As of this build, `s20` through `s28` (kernel/lineage/README.md's whole
    additive-delta lineage to date) carry `.detect.sql` only -- `.verify.sql` was not backfilled
    onto them by this pass (ADR-0013 Rule 4: a named, filed gap, not a silently narrower claim);
    `s29` (kernel/lineage/s29-obligation-item-key-and-typed-close.sql, staged pending the
    maintainer's own kernel-lineage apply -- CLAUDE.md ORCHESTRATION: "kernel/lineage/... without
    a Fable-authored, maintainer-ratified spec" is nobody's but the maintainer's to commit) is
    the FIRST delta shipped with both files from birth, per this task's own instruction.

GENERIC, DELTA-INDEPENDENT CHECKS (run every migration, regardless of which deltas are missing --
these do not live in any `.verify.sql` because they are not any one delta's invariant):
  - HISTORY BYTE-IDENTITY: a stable projection of every pre-existing ledger row (id, kind, actor,
    statement, event_declared_ts) is hashed before and after the chain is applied; the hash MUST
    be unchanged. A schema migration adds columns/constraints/views; it must never rewrite a
    single existing row's pre-existing fields (ADR-0013 Rule 5: verify the artifact, not the
    "ALTER succeeded" claim).
  - CHAIN CHECK: `bootstrap/templates/verify-chain.tmpl` (the s26/s27 row-hash-chain walker
    already in this tree) is run, unmodified, against the migrated copy via a throwaway
    deployment.json pointing at it -- reused rather than re-implemented (ADR-0012 P1/P7): this
    script issues no row-hash logic of its own.

Stdlib-only, top-of-file imports (gates/no_lazy_imports.py's ban on runtime-deferred imports).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

AUTOHARN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AUTOHARN_ROOT / "filing"))
sys.path.insert(0, str(AUTOHARN_ROOT / "bootstrap"))
from deployment_record import DeploymentError, DeploymentRecord, load_deployment  # noqa: E402
from live_session_check import find_live_sessions  # noqa: E402

LINEAGE_DIR = AUTOHARN_ROOT / "kernel" / "lineage"
NEW_PROJECT_SH = AUTOHARN_ROOT / "bootstrap" / "new-project.sh"
VERIFY_CHAIN_TMPL = AUTOHARN_ROOT / "bootstrap" / "templates" / "verify-chain.tmpl"


class MigrateRefusal(Exception):
    """A loud, named refusal -- printed to stderr, exit 1. Never a stack trace; every refusal
    site names what deviated and, where there is one, the remediation (ADR-0002)."""


# --------------------------------------------------------------------------------------------
# 1. THE MANIFEST -- parsed from new-project.sh, never hardcoded here (see module docstring).
# --------------------------------------------------------------------------------------------

def _manifest() -> list[str]:
    """The ordered list of kernel/lineage/*.sql basenames a from-scratch --new-world birth
    applies, extracted from new-project.sh's own psql -f invocation. Order is the order those
    -f flags appear on the line, which is new-project.sh's own commitment (it is a single psql
    call; psql applies -f files strictly in the order given)."""
    if not NEW_PROJECT_SH.is_file():
        raise MigrateRefusal(
            f"migrate: cannot find {NEW_PROJECT_SH} -- the manifest this script's whole "
            f"data-driven chain depends on lives there (its --new-world psql -f invocation). "
            f"Nothing was touched.")
    text = NEW_PROJECT_SH.read_text(encoding="utf-8")
    names = re.findall(r'kernel/lineage/([A-Za-z0-9_.\-]+\.sql)"', text)
    # De-duplicate while preserving order (defensive -- new-project.sh's invocation should not
    # repeat a file, but a future edit accidentally doing so must not silently double-apply it).
    seen: set[str] = set()
    ordered: list[str] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    if not ordered:
        raise MigrateRefusal(
            f"migrate: parsed {NEW_PROJECT_SH} but found zero kernel/lineage/*.sql references in "
            f"its --new-world psql invocation -- either that invocation moved/changed shape, or "
            f"this world truly has no birth chain yet. Refusing rather than guessing an empty "
            f"chain is correct. Nothing was touched.")
    return ordered


def _require_detect_files(manifest: list[str]) -> dict[str, Path]:
    """Every manifest entry MUST carry a sibling `.detect.sql`, or migrate refuses at the very
    first step -- see the module docstring's PER-DELTA VERIFICATION CONVENTION. Returns
    {basename: detect_path}."""
    missing: list[str] = []
    detects: dict[str, Path] = {}
    for name in manifest:
        stem = name[:-4] if name.endswith(".sql") else name
        detect = LINEAGE_DIR / f"{stem}.detect.sql"
        if detect.is_file():
            detects[name] = detect
        else:
            missing.append(name)
    if missing:
        lines = "\n".join(f"    kernel/lineage/{n[:-4]}.detect.sql  (for {n})" for n in missing)
        raise MigrateRefusal(
            "migrate: REFUSED before touching anything -- the following kernel/lineage/ delta(s) "
            "are wired into new-project.sh's birth chain but carry no sibling `.detect.sql`, so "
            "this script cannot safely tell whether they are already applied to your deployment:\n"
            f"{lines}\n"
            "Remediation: author the missing `.detect.sql` file(s) per bootstrap/migrate_core.py's "
            "own module docstring (PER-DELTA VERIFICATION CONVENTION) before migrating past this "
            "point. Nothing was touched.")
    return detects


# --------------------------------------------------------------------------------------------
# 2. psql PLUMBING
# --------------------------------------------------------------------------------------------

def _psql_args(dep: DeploymentRecord, schema: str, kern: str) -> list[str]:
    return [
        "psql", "-h", dep.host, "-d", dep.db,
        "-v", "ON_ERROR_STOP=1",
        "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={dep.role}",
    ]


def _run_detect(dep: DeploymentRecord, schema: str, kern: str, detect_path: Path) -> bool:
    """Runs a `.detect.sql` (or `.verify.sql`, same shape) file with `-tA` so the ONE boolean
    column prints as a bare `t`/`f` per row, and returns True iff every printed line is `t`
    (empty output -- the query returned zero rows -- is treated as False, never as vacuously
    true: a `.detect.sql`/`.verify.sql` that returns no rows is a defect in that file, not in
    the deployment)."""
    proc = subprocess.run(
        _psql_args(dep, schema, kern) + ["-tA", "-f", str(detect_path)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise MigrateRefusal(
            f"migrate: the query in {detect_path} failed to run against schema={schema} "
            f"kern={kern}:\n{proc.stderr.strip()}\nNothing further was touched.")
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip() != ""]
    if not lines:
        raise MigrateRefusal(
            f"migrate: {detect_path} returned zero rows against schema={schema} kern={kern} -- "
            f"a detect/verify query must return exactly one row per SELECT with a boolean "
            f"`applied`/`ok` column. This is a defect in {detect_path}, not in the deployment. "
            f"Nothing further was touched.")
    return all(ln == "t" for ln in lines)


def _current_head_and_missing(dep: DeploymentRecord, schema: str, kern: str,
                               manifest: list[str], detects: dict[str, Path]
                               ) -> tuple[str | None, list[str]]:
    """Walks the manifest in order against the given (schema, kern), running each entry's
    `.detect.sql`. Returns (last-applied-name-or-None, [missing entries in apply order])."""
    head: str | None = None
    missing: list[str] = []
    still_applying = True
    for name in manifest:
        applied = _run_detect(dep, schema, kern, detects[name]) if still_applying else False
        if applied:
            head = name
        else:
            still_applying = False
            missing.append(name)
    return head, missing


# --------------------------------------------------------------------------------------------
# 3. PROCESS CHECK -- reuses bootstrap/live_session_check.py, the ONE shared "is anything
#    running against this deployment right now" scan (ADR-0012 P1) that
#    convert-to-submodule.sh/upgrade-submodule.sh already use for the identical hazard
#    (CLAUDE.md: "never modify hooks/ or a user project while a live session runs there"). No
#    second cwd-scanner is authored here.
# --------------------------------------------------------------------------------------------

def _refuse_if_live_session(deployment_dir: Path) -> None:
    try:
        matches = find_live_sessions(str(deployment_dir))
    except RuntimeError as e:
        raise MigrateRefusal(f"migrate: REFUSED -- {e}") from e
    if matches:
        lines = "\n".join(f"    pid={m.pid}  {m.reason}  cmd={m.cmdline!r}" for m in matches)
        raise MigrateRefusal(
            f"migrate: REFUSED -- {len(matches)} process(es) appear to be running against "
            f"{deployment_dir} (bootstrap/live_session_check.py):\n{lines}\n"
            f"A migration must not run underneath a live session. End the session(s) above and "
            f"re-run. Nothing was touched.")
    print(f"migrate: process check PASSED -- {find_live_sessions.__module__} reports no live "
          f"session against {deployment_dir.resolve()}.")


# --------------------------------------------------------------------------------------------
# 4. BACKUP
# --------------------------------------------------------------------------------------------

def _backup(dep: DeploymentRecord, name: str) -> Path:
    backups_dir = Path.home() / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    path = backups_dir / f"{name}-pre-migrate-{stamp}.sql"
    print(f"migrate: pg_dump {dep.schema} + {dep.kern} from {dep.db}@{dep.host} -> {path}")
    proc = subprocess.run(
        ["pg_dump", "-h", dep.host, "-d", dep.db, "-n", dep.schema, "-n", dep.kern,
         "-f", str(path)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0 or not path.is_file() or path.stat().st_size == 0:
        raise MigrateRefusal(
            f"migrate: pg_dump FAILED or produced an empty file -- {path}\n{proc.stderr.strip()}\n"
            f"No rollback artifact exists; refusing to proceed. Nothing was touched.")
    print(f"migrate: ROLLBACK ARTIFACT: {path} ({path.stat().st_size} bytes)")
    return path


# --------------------------------------------------------------------------------------------
# 5. SCRATCH RESTORE (the rehearsal's data source -- proves the backup restores, not just exists)
# --------------------------------------------------------------------------------------------

def _scratch_names(dep: DeploymentRecord) -> tuple[str, str]:
    suffix = f"mig{os.getpid()}"
    return f"{dep.schema}_{suffix}", f"{dep.kern}_{suffix}"


def _restore_to_scratch(dep: DeploymentRecord, backup_path: Path,
                         scratch_schema: str, scratch_kern: str) -> None:
    """Renames the two schema identifiers in a COPY of the dump text and applies it into fresh
    scratch schemas in the SAME database. This is the "COPY-data-safe schema renamer" technique
    the 2026-07-14 ent rehearsal used by hand (ledger decision row 747); mechanized here so it
    never has to be re-typed.

    Word-boundary regex, NOT a bare substring replace: pg_dump's plain-SQL output only
    double-quotes an identifier when Postgres would otherwise need quoting (mixed case,
    special characters) -- a plain lowercase schema name like `migfixa` appears BARE
    (`CREATE SCHEMA migfixa;`), so a quoted-only replace silently misses every unquoted
    occurrence (witnessed: `CREATE SCHEMA migfixa;` unrenamed, second restore collided with the
    live schema). `\\b<name>\\b` matches both the bare and the `"quoted"` form (the quote
    characters are non-word, so the boundary still lands) while correctly NOT matching a
    LONGER identifier that happens to start with the same text (`migfixa_kernel`, `migfixa_rw`
    -- the role name, deliberately never renamed) because `_` is itself a word character, so
    no boundary exists between `migfixa` and `_kernel`/`_rw`."""
    text = backup_path.read_text(encoding="utf-8", errors="surrogateescape")
    text = re.sub(rf"\b{re.escape(dep.kern)}\b", scratch_kern, text)
    text = re.sub(rf"\b{re.escape(dep.schema)}\b", scratch_schema, text)
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False,
                                      encoding="utf-8", errors="surrogateescape") as tf:
        tf.write(text)
        renamed_path = Path(tf.name)
    try:
        proc = subprocess.run(
            ["psql", "-h", dep.host, "-d", dep.db, "-v", "ON_ERROR_STOP=1",
             "-1", "-f", str(renamed_path)],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            raise MigrateRefusal(
                f"migrate: REHEARSAL FAIL -- restoring the backup into scratch schemas "
                f"{scratch_schema}/{scratch_kern} failed:\n{proc.stderr.strip()}\n"
                f"Live schema was never touched. Nothing further was touched.")
    finally:
        renamed_path.unlink(missing_ok=True)


def _drop_schema(dep: DeploymentRecord, schema: str) -> None:
    subprocess.run(
        ["psql", "-h", dep.host, "-d", dep.db, "-v", "ON_ERROR_STOP=1",
         "-c", f'DROP SCHEMA IF EXISTS "{schema}" CASCADE;'],
        capture_output=True, text=True,
    )


# --------------------------------------------------------------------------------------------
# 6. APPLYING THE MISSING CHAIN (rehearsal and live share this function -- ADR-0012 P1: one apply
#    path, never a rehearsal-shaped copy and a live-shaped copy that could silently diverge)
# --------------------------------------------------------------------------------------------

def _apply_chain(dep: DeploymentRecord, schema: str, kern: str, missing: list[str],
                  where: str, backup_path: Path | None = None) -> None:
    """`backup_path`, when given, is threaded through as two GENERIC (delta-independent, no sNN
    name here -- see module docstring) psql vars, `epoch_dump_path`/`epoch_applied_by`: any future
    delta that wants to record its own provenance the way s29's sec-10 migration_epoch amendment
    does (kernel/lineage/s29-obligation-item-key-and-typed-close.sql's own AMENDMENT header) reads
    them the same way s29 does, via its own `\\if :{?var}` default-to-empty guard -- a delta that
    does not care about these vars simply never references them, exactly like `schema`/`kern`/
    `role` are already passed to every delta whether or not it uses them. REHEARSAL and LIVE are
    BOTH given the same `backup_path`: REHEARSAL restores from that exact dump (this function's
    own caller), so its provenance is honestly identical to LIVE's -- the same backup file is what
    either apply's history stood on at that moment."""
    args = _psql_args(dep, schema, kern) + ["-1"]
    if backup_path is not None:
        args += ["-v", f"epoch_dump_path={backup_path}",
                 "-v", f"epoch_applied_by={os.environ.get('USER', 'unknown')}"]
    for name in missing:
        args += ["-f", str(LINEAGE_DIR / name)]
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise MigrateRefusal(
            f"migrate: {where} APPLY FAILED (single transaction, rolled back whole -- "
            f"{'scratch' if where == 'REHEARSAL' else 'LIVE'} schema {schema}/{kern} is "
            f"unaffected by this failed attempt):\n{proc.stderr.strip()}\n"
            f"Nothing further was touched.")
    print(f"migrate: {where} apply of {len(missing)} delta(s) to {schema}/{kern}: OK "
          f"(single transaction).")


# --------------------------------------------------------------------------------------------
# 7. GENERIC HISTORY-IDENTITY CHECK
#
# ACTUALLY delta-independent (fixed post-build, out-of-frame hack-rationalization audit,
# 2026-07-14): the first cut of this check hardcoded `event_declared_ts` into its column list --
# a column only `s24-declared-event-time.sql` adds, absent on any pre-s24 head (`s15-schema.sql`'s
# base `ledger` has no such column). That silently broke this check's own docstring claim (this
# is the one place in the file titled "GENERIC, DELTA-INDEPENDENT") the moment `./migrate` ran
# against a deployment stuck behind s24 -- squarely in scope for a tool whose whole premise is
# "any deployment, any missing suffix" -- surfacing a raw, untaught Postgres "column does not
# exist" instead of the tool's own promised evidence trail. Fixed the ADR-0000 Rule 2(a) way: not
# a special case for s24, but the SAME capability-gating idiom `.detect.sql` siblings already use
# (query information_schema.columns for what is actually there), so the NEXT column added to
# `ledger` by some future delta needs zero edit here either -- the projection is derived from the
# live catalog, never a literal list trusted to stay in sync with the lineage.
# --------------------------------------------------------------------------------------------

# Every column this check WOULD project if present -- `id`/`kind` exist on every generation this
# tool supports (the base `ledger` table, s15-schema.sql) and are listed for clarity, not because
# they need gating; `actor`/`statement`/`event_declared_ts` are gated because a real pre-s24 (or
# even pre-s15-successor) head may lack the newer ones. Order here is the order that lands in the
# fingerprint when present -- stable across two calls on the SAME schema, which is all identity
# comparison needs (this list itself never has to match another schema's presence set).
_HISTORY_CANDIDATE_COLUMNS = ("id", "kind", "actor", "statement", "event_declared_ts")


def _history_columns(dep: DeploymentRecord, schema: str) -> list[str]:
    proc = subprocess.run(
        ["psql", "-h", dep.host, "-d", dep.db, "-v", "ON_ERROR_STOP=1", "-tA",
         "-c", f"SELECT column_name FROM information_schema.columns "
               f"WHERE table_schema = '{schema}' AND table_name = 'ledger' "
               f"AND column_name = ANY(ARRAY[{','.join(repr(c) for c in _HISTORY_CANDIDATE_COLUMNS)}]);"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise MigrateRefusal(
            f"migrate: could not read {schema}.ledger's column list:\n{proc.stderr.strip()}\n"
            f"Nothing further was touched.")
    present = {ln.strip() for ln in proc.stdout.splitlines() if ln.strip()}
    if "id" not in present:
        raise MigrateRefusal(
            f"migrate: {schema}.ledger has no `id` column -- this is not a kernel this tool "
            f"recognizes as a migration target. Nothing was touched.")
    return [c for c in _HISTORY_CANDIDATE_COLUMNS if c in present]


def _history_fingerprint(dep: DeploymentRecord, schema: str, columns: list[str]) -> tuple[int, str]:
    """`columns` is ALWAYS the caller's, never recomputed here -- see the caller-side comment in
    `main()` for why: recomputing per call would let a migrated-in column (e.g. `event_declared_ts`
    on a deployment migrating THROUGH s24) silently widen the "after" projection relative to
    "before", producing a false HISTORY BYTE-IDENTITY failure on rows whose content never
    changed. One column set, fixed at the START of a run (`_history_columns` on the PRE-migration
    live schema), used for every fingerprint call in that run -- apples to apples throughout."""
    parts = []
    for c in columns:
        cast = f"{c}::text" if c not in ("kind", "statement") else c
        parts.append(f"coalesce({cast},'')")
    projection = " || '|' || ".join(parts)
    proc = subprocess.run(
        ["psql", "-h", dep.host, "-d", dep.db, "-v", "ON_ERROR_STOP=1", "-tA", "-F", "|",
         "-c", f"SELECT count(*), coalesce(md5(string_agg({projection}, ',' "
               f'ORDER BY id)), \'\') FROM "{schema}".ledger;'],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise MigrateRefusal(
            f"migrate: could not compute the history fingerprint for {schema}.ledger "
            f"(columns projected: {', '.join(columns)}):\n"
            f"{proc.stderr.strip()}\nNothing further was touched.")
    count_s, digest = proc.stdout.strip().split("|", 1)
    return int(count_s), digest


def _run_verify_files(dep: DeploymentRecord, schema: str, kern: str,
                       missing: list[str]) -> list[str]:
    """Runs each missing delta's `.verify.sql` sibling (if present); returns the list of names
    that HAD a verify file, so the evidence summary can name which deltas got the fuller check
    and which fell back to detect-only (per the module docstring's honest-degradation clause)."""
    verified: list[str] = []
    for name in missing:
        stem = name[:-4] if name.endswith(".sql") else name
        verify_path = LINEAGE_DIR / f"{stem}.verify.sql"
        if not verify_path.is_file():
            continue
        ok = _run_detect(dep, schema, kern, verify_path)
        if not ok:
            raise MigrateRefusal(
                f"migrate: VERIFY FAILED -- {verify_path} reported at least one `ok=false` "
                f"against schema={schema} kern={kern}. Nothing further was touched.")
        verified.append(name)
    return verified


def _chain_check(dep: DeploymentRecord, schema: str, kern: str) -> str:
    """Reuses bootstrap/templates/verify-chain.tmpl unmodified (ADR-0012 P1/P7 -- no second
    row-hash walker) by pointing it at a throwaway deployment.json via PICKUP_DEPLOYMENT, the
    same env var pickup.tmpl/led.tmpl already read live."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tf:
        json.dump({"db": dep.db, "host": dep.host, "schema": schema, "kern": kern,
                    "role": dep.role, "name": f"migrate-check-{schema}"}, tf)
        dep_path = tf.name
    try:
        env = dict(os.environ)
        env["PICKUP_DEPLOYMENT"] = dep_path
        proc = subprocess.run(["python3", str(VERIFY_CHAIN_TMPL)], capture_output=True,
                               text=True, env=env)
        # verify-chain.tmpl exit 0 = INTACT/UNAVAILABLE (both honest passes, see its own
        # docstring); any other code is a real finding this migration must not proceed past.
        if proc.returncode != 0:
            raise MigrateRefusal(
                f"migrate: CHAIN CHECK FAILED against schema={schema} kern={kern} "
                f"(verify-chain exit {proc.returncode}):\n{proc.stdout}\n{proc.stderr}\n"
                f"Nothing further was touched.")
        return proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "(no output)"
    finally:
        os.unlink(dep_path)


# --------------------------------------------------------------------------------------------
# 7a. CHAIN GENESIS SEED -- closes the manual-path gap witnessed in the stranger rehearsal
# (tracker item chain-genesis-manual-path, 2026-07-15): README.md's manual deployment route
# (scaffold -> apply a kernel lineage by hand -> ./migrate to catch up) has NO step that seeds
# `:kern.chain_genesis` -- only `bootstrap/new-project.sh --new-world` ever did (see that
# script's own "GENESIS SEED" block, right after its stamp-secret seeding). A manually-kernelled
# world that reaches or passes s26-row-hash-chain.sql this way has the trigger
# (zz_set_row_hash) wired but no seed row for it to read -- the FIRST real ledger INSERT (in
# this script's own case, `_record_in_deployment_ledger`'s `led decision` call) hits
# `RAISE EXCEPTION 'row_hash chain: no world-birth seed ...'` and fails loudly, exactly the
# "post-migrate ledger-recording fails" defect witnessed live.
#
# This is deliberately NOT gated on `missing` (a world that is already at the lineage head --
# the early-return branch in main() -- can STILL lack a genesis seed, since the manual-path gap
# is "nobody ever seeded it," independent of whether THIS run applied anything): every
# `./migrate` invocation checks and seeds if needed, mirroring new-project.sh's own idempotent
# one-row-table pattern (INSERT ... ON CONFLICT (only_one) DO NOTHING) so a second run against an
# already-seeded world is a provable no-op, never a silent second seed / never an error.
# --------------------------------------------------------------------------------------------

def _chain_genesis_status(dep: DeploymentRecord, schema: str, kern: str) -> str:
    """Read-only counterpart of `_seed_chain_genesis` -- reports LIVE `:kern.chain_genesis`
    status for the evidence summary WITHOUT writing anything (used on `--dry-run`, where no LIVE
    touch is permitted, and in the REHEARSAL evidence block). Two SEPARATE queries, not one
    CASE-wrapped query naming `{kern}.chain_genesis` in a branch that may never execute: Postgres
    resolves every relation a query text NAMES at parse/plan time regardless of which CASE arm
    runs, so a single statement referencing the (possibly absent) table always errors on a
    pre-s26 schema -- witnessed directly authoring this function. `to_regclass` first (never
    errors, NULL if absent), the count only issued when the table is confirmed present."""
    exists = subprocess.run(
        ["psql", "-h", dep.host, "-d", dep.db, "-v", "ON_ERROR_STOP=1", "-tAc",
         f"SELECT to_regclass('{kern}.chain_genesis') IS NOT NULL;"],
        capture_output=True, text=True,
    )
    if exists.returncode != 0:
        return f"chain_genesis: could not read LIVE status ({exists.stderr.strip()[-200:]})"
    if exists.stdout.strip() != "t":
        return "chain_genesis: LIVE has no chain_genesis table yet (pre-s26 lineage)."
    have = subprocess.run(
        ["psql", "-h", dep.host, "-d", dep.db, "-v", "ON_ERROR_STOP=1", "-tAc",
         f"SELECT count(*) FROM {kern}.chain_genesis;"],
        capture_output=True, text=True,
    )
    if have.returncode != 0:
        return f"chain_genesis: could not read LIVE status ({have.stderr.strip()[-200:]})"
    v = have.stdout.strip()
    if v == "1":
        return "chain_genesis: LIVE already seeded (1 row) -- would be a no-op."
    return f"chain_genesis: LIVE table exists but UNSEEDED ({v} rows) -- would be seeded on apply."


def _seed_chain_genesis(dep: DeploymentRecord, schema: str, kern: str) -> str:
    """Idempotently provisions `:kern.chain_genesis` (the s26 row-hash chain's world-birth seed)
    if the table exists and is empty -- mirrors bootstrap/new-project.sh's own --new-world
    GENESIS SEED block byte-for-byte (same table shape, same `openssl rand -hex 32`, same
    ON CONFLICT (only_one) DO NOTHING). Returns a one-line, evidence-summary-ready string
    describing what happened: SEEDED / already-seeded (no-op) / SKIPPED (pre-s26 lineage, no
    chain_genesis table -- not an error, an older lineage, exactly new-project.sh's own wording
    for the same case)."""
    exists = subprocess.run(
        ["psql", "-h", dep.host, "-d", dep.db, "-v", "ON_ERROR_STOP=1", "-tAc",
         f"SELECT to_regclass('{kern}.chain_genesis') IS NOT NULL;"],
        capture_output=True, text=True,
    )
    if exists.returncode != 0:
        raise MigrateRefusal(
            f"migrate: could not check for {kern}.chain_genesis:\n{exists.stderr.strip()}\n"
            f"Nothing further was touched.")
    if exists.stdout.strip() != "t":
        return (f"chain_genesis: SKIPPED -- {kern}.chain_genesis does not exist (this world's "
                f"kernel predates s26-row-hash-chain.sql; not an error, an older lineage).")
    have = subprocess.run(
        ["psql", "-h", dep.host, "-d", dep.db, "-v", "ON_ERROR_STOP=1", "-tAc",
         f"SELECT count(*) FROM {kern}.chain_genesis;"],
        capture_output=True, text=True,
    )
    if have.returncode != 0:
        raise MigrateRefusal(
            f"migrate: could not read {kern}.chain_genesis row count:\n{have.stderr.strip()}\n"
            f"Nothing further was touched.")
    if have.stdout.strip() == "1":
        return f"chain_genesis: already seeded (1 row in {kern}.chain_genesis) -- no-op."
    genesis_hex = subprocess.run(["openssl", "rand", "-hex", "32"],
                                  capture_output=True, text=True)
    if genesis_hex.returncode != 0 or not genesis_hex.stdout.strip():
        raise MigrateRefusal(
            f"migrate: `openssl rand -hex 32` failed while seeding {kern}.chain_genesis:\n"
            f"{genesis_hex.stderr.strip()}\nNothing further was touched.")
    ins = subprocess.run(
        ["psql", "-h", dep.host, "-d", dep.db, "-q", "-v", "ON_ERROR_STOP=1", "-c",
         f"INSERT INTO {kern}.chain_genesis (seed) VALUES "
         f"('{genesis_hex.stdout.strip()}') ON CONFLICT (only_one) DO NOTHING;"],
        capture_output=True, text=True,
    )
    if ins.returncode != 0:
        raise MigrateRefusal(
            f"migrate: seeding {kern}.chain_genesis FAILED:\n{ins.stderr.strip()}\n"
            f"Nothing further was touched.")
    return f"chain_genesis: SEEDED (one fresh genesis seed provisioned in {kern}.chain_genesis)."


# --------------------------------------------------------------------------------------------
# 8. THE ONE TYPED CONFIRMATION
# --------------------------------------------------------------------------------------------

def _confirm(dep: DeploymentRecord, missing: list[str]) -> None:
    phrase = f"MIGRATE {dep.schema}"
    print()
    print(f"Type exactly:  {phrase}")
    print(f"to apply {len(missing)} delta(s) to LIVE schema={dep.schema} kern={dep.kern} "
          f"(anything else aborts, nothing touched):")
    try:
        typed = input("> ")
    except EOFError:
        typed = ""
    if typed != phrase:
        raise MigrateRefusal(
            f"migrate: confirmation did not match (typed {typed!r}, expected {phrase!r}) -- "
            f"aborting. Nothing was touched.")


# --------------------------------------------------------------------------------------------
# 9. RECORD THE MIGRATION IN THE DEPLOYMENT'S OWN LEDGER
# --------------------------------------------------------------------------------------------

def _record_in_deployment_ledger(deployment_dir: Path, missing: list[str], backup_path: Path,
                                  chain_note: str) -> None:
    led = deployment_dir / "led"
    if not led.is_file():
        print(f"migrate: NOTE -- {led} does not exist, so the migration decision was NOT "
              f"recorded in this deployment's own ledger (this deployment predates the led "
              f"shim, or is not a scaffolded autoharn world). Record it by hand if this "
              f"deployment keeps a ledger elsewhere.", file=sys.stderr)
        return
    statement = (
        f"migrate: applied {len(missing)} kernel delta(s) [{', '.join(missing)}] via "
        f"bootstrap/migrate.sh -- rehearsal PASS, live apply PASS, post-apply re-verify PASS "
        f"({chain_note}); backup={backup_path}"
    )
    proc = subprocess.run([str(led), "decision", statement], capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"migrate: WARNING -- the migration succeeded, but recording it in this "
              f"deployment's own ledger failed:\n{proc.stderr.strip()}\n"
              f"Record it by hand: {led} decision \"{statement}\"", file=sys.stderr)
    else:
        print(f"migrate: recorded in this deployment's own ledger via {led} decision.")


# --------------------------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[1] in ("--help", "-h"):
        print("usage: migrate <deployment-dir> [--dry-run]")
        return 0
    if len(argv) not in (2, 3) or (len(argv) == 3 and argv[2] != "--dry-run"):
        print("usage: migrate <deployment-dir> [--dry-run]", file=sys.stderr)
        return 2
    deployment_dir = Path(argv[1]).resolve()
    dry_run = len(argv) == 3

    try:
        dep = load_deployment(deployment_dir / "deployment.json")
    except DeploymentError as e:
        print(f"migrate: REFUSED -- {e}", file=sys.stderr)
        return 1
    name = dep.name or deployment_dir.name
    print(f"migrate: deployment '{name}' -- db={dep.db} host={dep.host} "
          f"schema={dep.schema} kern={dep.kern} role={dep.role}")

    try:
        _refuse_if_live_session(deployment_dir)

        manifest = _manifest()
        detects = _require_detect_files(manifest)
        print(f"migrate: manifest has {len(manifest)} entries (parsed from "
              f"{NEW_PROJECT_SH.relative_to(AUTOHARN_ROOT)}, every one carrying a `.detect.sql`).")

        head, missing = _current_head_and_missing(dep, dep.schema, dep.kern, manifest, detects)
        print(f"migrate: current lineage head = {head or '(none -- no manifest entry detected)'}")
        if not missing:
            print(f"migrate: '{name}' is already at the lineage head. Nothing to migrate.")
            genesis_note = (
                _chain_genesis_status(dep, dep.schema, dep.kern) if dry_run
                else _seed_chain_genesis(dep, dep.schema, dep.kern)
            )
            print(f"migrate: {genesis_note}")
            return 0
        print(f"migrate: missing ({len(missing)}): {', '.join(missing)}")

        backup_path = _backup(dep, name)
        # Fixed at the START of the run, on the PRE-migration live schema, and reused for EVERY
        # fingerprint call below -- never recomputed per call. See _history_fingerprint's own
        # docstring: recomputing after a delta that adds a candidate column (event_declared_ts,
        # s24) would widen the "after" projection relative to "before" and manufacture a false
        # HISTORY BYTE-IDENTITY failure on rows that never changed.
        history_columns = _history_columns(dep, dep.schema)
        pre_count, pre_fingerprint = _history_fingerprint(dep, dep.schema, history_columns)
        print(f"migrate: pre-migration history fingerprint: {pre_count} rows, "
              f"md5={pre_fingerprint} (columns: {', '.join(history_columns)})")

        scratch_schema, scratch_kern = _scratch_names(dep)
        print(f"migrate: REHEARSAL -- restoring backup into scratch schemas "
              f"{scratch_schema}/{scratch_kern} ...")
        try:
            _restore_to_scratch(dep, backup_path, scratch_schema, scratch_kern)
            scratch_pre_count, scratch_pre_fp = _history_fingerprint(dep, scratch_schema, history_columns)
            if (scratch_pre_count, scratch_pre_fp) != (pre_count, pre_fingerprint):
                raise MigrateRefusal(
                    "migrate: REHEARSAL FAIL -- the scratch restore's history fingerprint does "
                    "not match the live pre-migration fingerprint; the backup did not restore "
                    "byte-identically. Nothing live was touched.")
            _apply_chain(dep, scratch_schema, scratch_kern, missing, where="REHEARSAL",
                         backup_path=backup_path)
            post_count, post_fingerprint = _history_fingerprint(dep, scratch_schema, history_columns)
            if (post_count, post_fingerprint) != (pre_count, pre_fingerprint):
                raise MigrateRefusal(
                    "migrate: REHEARSAL FAIL -- HISTORY BYTE-IDENTITY check failed: applying the "
                    "missing chain changed the pre-existing ledger rows' stable projection "
                    f"(before: {pre_count} rows md5={pre_fingerprint}; after: {post_count} rows "
                    f"md5={post_fingerprint}). Nothing live was touched.")
            print(f"migrate: HISTORY BYTE-IDENTITY: PASSED ({post_count} rows, unchanged hash).")
            verified = _run_verify_files(dep, scratch_schema, scratch_kern, missing)
            detect_only = [n for n in missing if n not in verified]
            for name_ in missing:
                if not _run_detect(dep, scratch_schema, scratch_kern, detects[name_]):
                    raise MigrateRefusal(
                        f"migrate: REHEARSAL FAIL -- {name_}'s own `.detect.sql` reports "
                        f"NOT applied even after applying it. Nothing live was touched.")
            print(f"migrate: PER-DELTA DETECT: PASSED for all {len(missing)} delta(s).")
            if verified:
                print(f"migrate: PER-DELTA VERIFY: PASSED for {len(verified)} delta(s) with a "
                      f"`.verify.sql` ({', '.join(verified)}).")
            if detect_only:
                print(f"migrate: NOTE -- {len(detect_only)} delta(s) have no `.verify.sql` yet, "
                      f"checked by `.detect.sql` only ({', '.join(detect_only)}).")
            chain_note = _chain_check(dep, scratch_schema, scratch_kern)
            print(f"migrate: CHAIN CHECK (verify-chain, reused unmodified): {chain_note}")
        finally:
            _drop_schema(dep, scratch_schema)
            _drop_schema(dep, scratch_kern)

        print()
        print("=" * 70)
        print(f"REHEARSAL PASS -- evidence summary for '{name}':")
        print(f"  backup / rollback artifact : {backup_path}")
        print(f"  missing delta(s), in order : {', '.join(missing)}")
        print(f"  history byte-identity      : PASSED ({post_count} rows)")
        print(f"  per-delta detect           : PASSED ({len(missing)}/{len(missing)})")
        print(f"  per-delta verify           : PASSED ({len(verified)}/{len(missing)} had a "
              f".verify.sql)")
        print(f"  chain check                : {chain_note}")
        print(f"  {_chain_genesis_status(dep, dep.schema, dep.kern)}")
        print("=" * 70)

        if dry_run:
            print()
            print("migrate: --dry-run -- stopping here. No confirmation was asked; LIVE schema "
                  f"{dep.schema}/{dep.kern} was never touched.")
            return 0

        _confirm(dep, missing)

        print()
        print(f"migrate: applying to LIVE {dep.schema}/{dep.kern} ...")
        _apply_chain(dep, dep.schema, dep.kern, missing, where="LIVE", backup_path=backup_path)

        post_live_count, post_live_fp = _history_fingerprint(dep, dep.schema, history_columns)
        if (post_live_count, post_live_fp) != (pre_count, pre_fingerprint):
            print(
                f"migrate: *** POST-APPLY VERIFICATION FAILURE *** -- LIVE history byte-identity "
                f"broke after a COMMITTED apply (before: {pre_count} rows md5={pre_fingerprint}; "
                f"after: {post_live_count} rows md5={post_live_fp}). This delta is already "
                f"committed; it was NOT auto-rolled-back. Restore from {backup_path} if in doubt: "
                f"psql -h {dep.host} -d {dep.db} -f {backup_path}  (after dropping/renaming the "
                f"current {dep.schema}/{dep.kern} schemas by hand -- a live restore is a "
                f"deliberate operator act, never scripted blind).", file=sys.stderr)
            return 1
        verified_live = _run_verify_files(dep, dep.schema, dep.kern, missing)
        chain_note_live = _chain_check(dep, dep.schema, dep.kern)
        print(f"migrate: LIVE post-apply re-verify -- history byte-identity PASSED "
              f"({post_live_count} rows), per-delta verify PASSED "
              f"({len(verified_live)}/{len(missing)}), chain check: {chain_note_live}")

        # Genesis seed check runs AFTER the lineage apply and BEFORE the first real ledger write
        # below (_record_in_deployment_ledger's own `led decision` call) -- same ordering
        # constraint new-project.sh's --new-world block honors (seed before first write), closing
        # the manual-path gap this defect is filed under: see _seed_chain_genesis's own docstring.
        genesis_note = _seed_chain_genesis(dep, dep.schema, dep.kern)
        print(f"migrate: {genesis_note}")

        _record_in_deployment_ledger(deployment_dir, missing, backup_path, chain_note_live)

        print()
        print(f"migrate: '{name}' is now at lineage head {missing[-1]}. Done.")
        return 0

    except MigrateRefusal as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
