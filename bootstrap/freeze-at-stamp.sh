#!/bin/sh
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T18:06:58Z
#   last-change: 2026-07-14T23:23:00Z
#   contributors: 3c50e030/main, a857c93d/main
# <<< PROVENANCE-STAMP <<<

# freeze-at-stamp.sh -- produce a "tree correlated with db frozen in time": a git tree pinned at
# one commit PLUS this repo's own tracker (the autoharn root ledger) truncated to the same
# instant, wired together so the frozen dest's own ./pickup/./led/./judge/etc. read ONLY the
# frozen snapshot, never the live tracker and never the live checkout.
#
# WHY THIS EXISTS (tracker slug `freeze-at-stamp`, `./led show 225` for the full commission; see
# also decision rows 228/229 for the two spec amendments this script implements): a control-
# evaluation ran in a git worktree pinned at an old commit, but (a) its ./pickup shim exec'd the
# LIVE checkout's templates against the LIVE tracker (a later, ungraded ledger row leaked into a
# session that was supposed to see frozen history), and (b) the worktree resolved to the parent
# repo's project identity, importing the orchestrator's own auto-memory. This script forecloses
# both: a default git-archive export (no `.git`, so the dest has no path back to the parent
# project's identity) plus a frozen-and-truncated copy of the tracker, with the dest's verb shims
# repointed at the DEST's own `bootstrap/templates/` (never the live checkout's).
#
# ISOLATION LEVEL (ratified via two tracker amendments; `./led show 228` then `./led show 229`
# supersedes it): the frozen tracker copy lives in its OWN, STANDING, single-tenant database
# (`autoharn_test` by default -- never a schema pair inside the live db that also holds this
# repo's own root tracker). Rationale, the maintainer's own: if read-access to the tracker is
# ever instrumented, an experiment/probe read against a same-database copy would contaminate the
# live database's observation surface regardless of how fresh or stale the copied data is --
# isolation is about the OBSERVATION SURFACE (which database a read lands on), not only data
# freshness. Two standing roles on that database do the actual work, both provisioned ONCE by
# the maintainer (never by this script -- see REFUSALS below): `<db>_owner` (LOGIN, owns the
# database -- this script's own infrastructure identity: wipe/restore/truncate) and `<db>_ro`
# (LOGIN, CONNECT only -- the identity the frozen dest's shims read as). The two-role split keeps
# provisioning reads (as `_owner`) and experiment/evidence reads (as `_ro`) distinguishable by
# ROLE as well as by database, which is the maintainer's actual read-tracking motive.
#
# HONEST RESIDUAL, named not hidden: this isolates the DATABASE and the ROLE, not the whole
# Postgres CLUSTER -- same-cluster surfaces (the server's global log stream, `pg_stat_activity`)
# remain shared across every database on this host, with entries distinguishable by database name
# and connecting role, never by a harder boundary. Full cluster separation is a host-level act and,
# per this project's standing no-perimeter-questions ruling, is not proposed here.
#
# WHAT THIS SCRIPT DOES NOT DO: provision the standing database or its two roles (a one-time
# maintainer act -- see the REFUSALS section's teach-text for the exact CREATE DATABASE/CREATE
# ROLE lines), touch pg_hba.conf or any host/credential configuration (CLAUDE.md ORCHESTRATION:
# "credentials/pg_hba/hosts ... routes to the maintainer, always" -- this script probes
# reachability and refuses loudly if the standing infrastructure is not there or not reachable; it
# never edits server configuration to make itself reachable), or touch the LIVE tracker beyond
# read-only SELECTs (append-only and runs-are-linear are preserved; the source's own row count is
# provably unchanged by this script, witnessed by the fixture).
#
# Usage:
#   bootstrap/freeze-at-stamp.sh <commit> <dest-dir>
#       [--db <name>]            standing frozen-snapshot database (default: autoharn_test)
#       [--host <host>]          postgres host (default: this checkout's own deployment.json
#                                'host' field; refuses loudly if neither resolves)
#       [--as-of <iso-ts|id>]    cutoff override (default: the commit's own committer timestamp)
#       [--worktree]             `git worktree add` instead of the default `git archive` export
#       [--writable]             skip the REVOKE that makes the frozen copy SELECT-only
#       [--no-wipe]              skip the default wipe-before-use of the standing database
#       [--force]                overwrite an existing <dest-dir>
#
# STRUCTURE MECHANISM CHOSEN (spec's own open choice, decided here): `pg_dump`/`psql`
# schema-then-data restore of the SOURCE schema pair (this repo's own `autoharn`/`autoharn_kernel`,
# read live from THIS checkout's own deployment.json -- never hardcoded, see `_source_deployment()`
# below), NOT a from-scratch re-application of the kernel/lineage/*.sql birth chain. Reason: this
# script's job is freezing WHATEVER STRUCTURE THE LIVE TRACKER ACTUALLY HAS RIGHT NOW, including any
# hand-applied delta or drift from the nominal birth chain -- re-deriving structure from the sNN
# files would silently paper over any such drift instead of freezing the honest, actually-live
# shape (ADR-0012 P1: one structural fact, the LIVE schema, copied, not a second independent
# re-derivation of what it is supposed to look like).
#
# WHY SCHEMA NAMES ARE KEPT, NOT RENAMED: the destination database is single-tenant by design (one
# snapshot at a time; wiped before each use -- see WIPE below), so `autoharn`/`autoharn_kernel` in
# the frozen db can never collide with anything else living there. Renaming to `frozen_<shortsha>`
# would only add bookkeeping with no isolation benefit the database boundary does not already give.
#
# CHAIN CONTINUITY (s26 row-hash chain / s27 chain_high_water witness -- read kernel/lineage/
# s26-row-hash-chain.sql and s27-chain-high-water.sql in full before touching this script's DB
# logic): the schema+data restore below copies `chain_genesis` and every ledger row (including its
# stored `row_hash`) VERBATIM. The `zz_set_row_hash`/`zz_bump_chain_high_water` triggers are left
# ENABLED during the restore (never disabled) -- `compute_row_hash()` is a PURE function of a row's
# own content plus its predecessor's hash (kernel/lineage/s26's own "ONE HOME" design), so
# recomputing it during the restore, against the SAME copied genesis and the SAME copied prior
# rows, reproduces the IDENTICAL hash chain the source already had; it is not disabled-and-trusted,
# it is exercised and self-verifying. `zz_bump_chain_high_water` likewise fires per copied row in
# ascending id order, so once the copy is truncated to the cutoff id (below), the witness lands
# EXACTLY on the cutoff's own max id -- never manually poked to that value, the natural consequence
# of copying in order and truncating afterward. The ONE trigger that IS disabled during the copy is
# `set_stamp` (kernel/lineage/s17-stamp-mechanism.sql): it unconditionally overwrites
# stamp_session/agent/ts/hmac/verified from the `app.vendor_*` session GUCs on every INSERT/COPY
# (present or not) -- undisabled, a plain restore would silently blank every row's real stamp
# provenance to NULL/false. Disabling it for the data-load step only (re-enabled immediately after)
# preserves the source's actual stamp columns byte-for-byte, which is the point of a frozen
# EVIDENCE copy: who really wrote which row must survive the freeze intact.
#
# PER-TABLE COPY/TRUNCATE/RESEED DISPOSITION (enumerated explicitly, ADR-0000 2026-07-02 amendment's
# closure-statement discipline -- no table in the copied kernel/schema pair is silently skipped):
#   - principal, principal_role      COPIED WHOLE (small identity tables; ledger.actor is an FK to
#                                    principal.id, so ids must match the source exactly -- copied
#                                    verbatim, sequence advanced to match, never re-registered).
#   - stamp_secret                   COPIED WHOLE. Never leaves the database (no GRANT to the ro
#                                    role either way -- s17's own posture, unaffected by this
#                                    script); copying it lets a --writable frozen copy's stamps
#                                    validate against the SAME secret the source rows were stamped
#                                    under, if that mode is ever exercised.
#   - chain_genesis                 COPIED WHOLE (the one-row world-birth nonce every row_hash in
#                                    the chain was computed against -- see CHAIN CONTINUITY above;
#                                    this is why the restore reproduces byte-identical row_hash
#                                    values rather than a fresh, differently-seeded chain).
#   - ledger                        COPIED then TRUNCATED to `id <= cutoff` (append_only_row
#                                    disabled around the truncating DELETE, re-enabled after --
#                                    mirrors seen-red/s27-chain-high-water/run_fixtures.py's own
#                                    delete_row() idiom, the established pattern for a
#                                    schema-owner-level DELETE against this append-only table).
#   - review_detail                 COPIED then TRUNCATED to rows whose `ledger_id` still exists
#                                    after the ledger truncation above (a review row past the
#                                    cutoff no longer exists to have review_detail about).
#   - countersign_obligation        COPIED WHOLE. It has no FK to a ledger row id (scope is a
#                                    free-text label per its own kernel comment; obliges_actor/
#                                    assigned_by are principal ids, already copied whole above) --
#                                    there is no cutoff-shaped truncation that means anything here.
#   - chain_high_water              RESEEDED, not copied verbatim: the source's own live value (the
#                                    current, un-truncated max id) is WRONG for a frozen world truncated
#                                    to an earlier cutoff -- left at the source's value, `./verify-chain`
#                                    in the frozen dest would report TAIL-DELETION-SUSPECT (the
#                                    witness would be ahead of the truncated ledger's own walked max,
#                                    exactly the false-positive kernel/lineage/s27-chain-high-water.sql's
#                                    own header warns a stale witness produces). Set explicitly to the
#                                    cutoff id AFTER the ledger truncation (this script's one manual
#                                    UPDATE against this table; done as the owning role, which is not
#                                    subject to the ordinary role's read-only grant on this table).
#
# REFUSALS (every one names the fix, ADR-0002):
#   - <dest-dir> already exists                          -> refuse, unless --force
#   - <commit> does not resolve in this checkout          -> refuse (git rev-parse teach-text)
#   - the standing db/roles are unreachable               -> refuse with the one-time provisioning
#                                                             SQL in the teach-text (see
#                                                             _refuse_unreachable() below)
#   - --as-of names a ledger id beyond the source's max, or a timestamp with no row at-or-before it
#                                                          -> refuse, naming the source's actual max
#   - --as-of names a timestamp in the future              -> refuse
#
# Self-application (CLAUDE.md ORCHESTRATION): one scripted verb, no prose-steps-plus-hand-pasted
# SQL. Lazy imports N/A (POSIX sh + inline psql, no Python module here).
set -eu

usage() {
    echo "usage: $0 <commit> <dest-dir> [--db <name>] [--host <host>] [--as-of <iso-ts|id>]" >&2
    echo "           [--worktree] [--writable] [--no-wipe] [--force]" >&2
    echo "       (see this script's own header comment for the full design rationale --" >&2
    echo "        tracker slug freeze-at-stamp, './led show 225' then 228/229 for the two" >&2
    echo "        spec amendments this build implements)" >&2
    exit 2
}

[ $# -ge 2 ] || usage
COMMIT="$1"; DEST="$2"; shift 2

DB="autoharn_test"
HOST=""
AS_OF=""
WORKTREE=0
WRITABLE=0
NO_WIPE=0
FORCE=0
while [ $# -gt 0 ]; do
    case "$1" in
        --db) DB="$2"; shift 2 ;;
        --host) HOST="$2"; shift 2 ;;
        --as-of) AS_OF="$2"; shift 2 ;;
        --worktree) WORKTREE=1; shift ;;
        --writable) WRITABLE=1; shift ;;
        --no-wipe) NO_WIPE=1; shift ;;
        --force) FORCE=1; shift ;;
        *) echo "freeze-at-stamp.sh: unrecognized argument: $1" >&2; usage ;;
    esac
done

AUTOHARN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$HOME/w/vdc/venvs/generic/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"

# HOST: --host flag, else this checkout's own deployment.json 'host' field, else a loud refusal
# -- never a silent literal default (the maintainer's own LAN host is not every operator's fact).
if [ -z "$HOST" ] && [ -f "$AUTOHARN_ROOT/deployment.json" ] && [ -n "$PY" ]; then
    HOST="$("$PY" -c "
import json, sys
try:
    with open(sys.argv[1]) as f:
        print(json.load(f).get('host') or '')
except Exception:
    print('')
" "$AUTOHARN_ROOT/deployment.json" 2>/dev/null)"
fi
if [ -z "$HOST" ]; then
    echo "freeze-at-stamp.sh: REFUSED -- no Postgres host resolved. Pass --host <host>, or" >&2
    echo "  place a deployment.json with a 'host' field at $AUTOHARN_ROOT/deployment.json" >&2
    echo "  (copy deployment.json.example and fill in your own values; see README.md" >&2
    echo "  'Configuration'). Never defaulting to any host." >&2
    exit 2
fi

# --- source deployment: THIS checkout's own root tracker (deployment.json at the repo root) -----
# derived LIVE via filing/deployment_record.py, never a hardcoded 'autoharn'/'autoharn_kernel'
# literal -- see this file's own header (STRUCTURE MECHANISM CHOSEN) for why the source is always
# this repo's own root deployment.json, not a caller-supplied schema/kern pair: the motivating
# defect (row-220 leak) was specifically THIS repo's own tracker leaking into a pinned worktree.
SRC_DEPLOYMENT="$AUTOHARN_ROOT/deployment.json"
_src_vars="$("$PY" - "$AUTOHARN_ROOT" "$SRC_DEPLOYMENT" <<'PYEOF'
import sys, shlex
autoharn_root, dep_path = sys.argv[1:3]
sys.path.insert(0, autoharn_root + "/filing")
import deployment_record as dr
try:
    d = dr.load_deployment(dep_path)
except dr.DeploymentError as e:
    print(f"freeze-at-stamp: cannot resolve the source tracker: {e}", file=sys.stderr)
    sys.exit(2)
for k in ("db", "host", "schema", "kern", "role"):
    print(f"SRC_{k.upper()}={shlex.quote(getattr(d, k))}")
PYEOF
)" || exit 2
eval "$_src_vars"

echo "== freeze-at-stamp: source tracker = ${SRC_DB}/${SRC_SCHEMA}+${SRC_KERN} on ${SRC_HOST} (from $SRC_DEPLOYMENT) =="

# --- dest-dir refusal -----------------------------------------------------------------------
if [ -e "$DEST" ] && [ "$FORCE" -ne 1 ]; then
    echo "freeze-at-stamp: REFUSED -- $DEST already exists. Pass --force to overwrite, or pick" >&2
    echo "  a fresh destination (a frozen snapshot is settled evidence; overwriting one in place" >&2
    echo "  by default would silently discard whatever was frozen there before)." >&2
    exit 1
fi

# --- commit resolution ------------------------------------------------------------------------
RESOLVED_SHA="$(cd "$AUTOHARN_ROOT" && git rev-parse --verify "${COMMIT}^{commit}" 2>&1)" || {
    echo "freeze-at-stamp: REFUSED -- '$COMMIT' does not resolve to a commit in $AUTOHARN_ROOT:" >&2
    echo "  $RESOLVED_SHA" >&2
    echo "  (git rev-parse --verify \"${COMMIT}^{commit}\" failed -- check the ref/sha and try again)" >&2
    exit 1
}
SHORT_SHA="$(cd "$AUTOHARN_ROOT" && git rev-parse --short "$RESOLVED_SHA")"
COMMITTER_TS="$(cd "$AUTOHARN_ROOT" && git show -s --format=%cI "$RESOLVED_SHA")"
echo "== commit $COMMIT resolves to $RESOLVED_SHA (short $SHORT_SHA), committer ts $COMMITTER_TS =="

# --- cutoff derivation (--as-of overrides; default = the commit's own committer timestamp) ------
# Two forms accepted for --as-of: a bare positive integer is an EXPLICIT ledger id; anything else is
# parsed as a timestamp by postgres's own ::timestamptz cast (ADR-0002: validate via the one real
# parser, never a hand-rolled second one). Resolved against the SOURCE tracker (read-only SELECTs
# only -- this script never writes to the source).
if [ -n "$AS_OF" ]; then
    CUTOFF_INPUT="$AS_OF"
else
    CUTOFF_INPUT="$COMMITTER_TS"
fi

case "$CUTOFF_INPUT" in
    ''|*[!0-9]*) CUTOFF_IS_ID=0 ;;
    *) CUTOFF_IS_ID=1 ;;
esac

SRC_MAX_ID="$(psql -h "$SRC_HOST" -d "$SRC_DB" -tAc "SELECT max(id) FROM ${SRC_SCHEMA}.ledger;")"
if [ -z "$SRC_MAX_ID" ] || [ "$SRC_MAX_ID" = "" ]; then
    echo "freeze-at-stamp: REFUSED -- the source tracker ${SRC_SCHEMA} has no ledger rows at all;" >&2
    echo "  there is nothing to freeze a cutoff of." >&2
    exit 1
fi

if [ "$CUTOFF_IS_ID" = "1" ]; then
    if [ "$CUTOFF_INPUT" -gt "$SRC_MAX_ID" ]; then
        echo "freeze-at-stamp: REFUSED -- --as-of $CUTOFF_INPUT names a ledger id beyond the source" >&2
        echo "  tracker's own max id ($SRC_MAX_ID). Pick an id <= $SRC_MAX_ID, or omit --as-of to" >&2
        echo "  default to the commit's own committer timestamp." >&2
        exit 1
    fi
    CUTOFF_ID="$CUTOFF_INPUT"
    CUTOFF_TS="$(psql -h "$SRC_HOST" -d "$SRC_DB" -tAc "SELECT ts FROM ${SRC_SCHEMA}.ledger WHERE id = ${CUTOFF_ID};")"
else
    NOW_TS="$(psql -h "$SRC_HOST" -d "$SRC_DB" -tAc "SELECT now();")"
    FUTURE="$(psql -h "$SRC_HOST" -d "$SRC_DB" -tAc "SELECT ('${CUTOFF_INPUT}'::timestamptz > now());")"
    if [ "$FUTURE" = "t" ]; then
        echo "freeze-at-stamp: REFUSED -- the cutoff timestamp '$CUTOFF_INPUT' is in the future" >&2
        echo "  (server now() = $NOW_TS). A frozen snapshot cannot include rows that have not" >&2
        echo "  happened yet." >&2
        exit 1
    fi
    CUTOFF_ID="$(psql -h "$SRC_HOST" -d "$SRC_DB" -tAc \
        "SELECT max(id) FROM ${SRC_SCHEMA}.ledger WHERE ts <= '${CUTOFF_INPUT}'::timestamptz;")"
    if [ -z "$CUTOFF_ID" ]; then
        echo "freeze-at-stamp: REFUSED -- no ledger row exists at or before '$CUTOFF_INPUT' in the" >&2
        echo "  source tracker (its earliest row is later than this cutoff). Pick a later --as-of," >&2
        echo "  or omit it to default to the commit's own committer timestamp." >&2
        exit 1
    fi
    CUTOFF_TS="$CUTOFF_INPUT"
fi
echo "== cutoff resolved: ledger id <= $CUTOFF_ID (source max is $SRC_MAX_ID), ts basis: $CUTOFF_TS =="

# --- standing frozen-db reachability probe (NEVER creates the db/roles -- see header) ------------
# A superuser/admin connection is needed just to CHECK pg_database/pg_roles; use the source
# connection (this script's own caller must already be able to reach $SRC_HOST/$SRC_DB, which the
# cutoff derivation above already proved) as the read-only probe channel, then attempt an ACTUAL
# connection to the target db as each of the two standing roles -- an entry in pg_database/pg_roles
# is not proof of REACHABILITY (pg_hba.conf governs that separately, and is exactly the axis this
# repo's own witnessed run of this script found broken -- see the fixture and final report).
DB_OWNER_ROLE="${DB}_owner"
DB_RO_ROLE="${DB}_ro"

DB_EXISTS="$(psql -h "$SRC_HOST" -d "$SRC_DB" -tAc "SELECT count(*) FROM pg_database WHERE datname = '${DB}';")"
OWNER_ROLE_EXISTS="$(psql -h "$SRC_HOST" -d "$SRC_DB" -tAc "SELECT count(*) FROM pg_roles WHERE rolname = '${DB_OWNER_ROLE}';")"
RO_ROLE_EXISTS="$(psql -h "$SRC_HOST" -d "$SRC_DB" -tAc "SELECT count(*) FROM pg_roles WHERE rolname = '${DB_RO_ROLE}';")"

_refuse_unreachable() {
    echo "freeze-at-stamp: REFUSED -- the standing frozen-snapshot database is not reachable." >&2
    echo "  db '${DB}' exists: $([ "$DB_EXISTS" = "1" ] && echo yes || echo NO)" >&2
    echo "  role '${DB_OWNER_ROLE}' exists: $([ "$OWNER_ROLE_EXISTS" = "1" ] && echo yes || echo NO)" >&2
    echo "  role '${DB_RO_ROLE}' exists: $([ "$RO_ROLE_EXISTS" = "1" ] && echo yes || echo NO)" >&2
    echo "  connect-as-owner probe: $1" >&2
    echo "" >&2
    echo "  This script NEVER creates the database, the roles, or edits pg_hba.conf itself --" >&2
    echo "  CLAUDE.md ORCHESTRATION: credentials/pg_hba/hosts route to the maintainer, always." >&2
    echo "  One-time provisioning (a maintainer act, on $HOST, as a superuser), per tracker" >&2
    echo "  decision row 229 ('./led show 229' in this checkout for the ratified statement):" >&2
    echo "    CREATE DATABASE ${DB};" >&2
    echo "    CREATE ROLE ${DB_OWNER_ROLE} LOGIN;" >&2
    echo "    CREATE ROLE ${DB_RO_ROLE} LOGIN;" >&2
    echo "    ALTER DATABASE ${DB} OWNER TO ${DB_OWNER_ROLE};" >&2
    echo "    GRANT CONNECT ON DATABASE ${DB} TO ${DB_RO_ROLE};" >&2
    echo "  plus a pg_hba.conf entry permitting ${DB_OWNER_ROLE}/${DB_RO_ROLE} to connect to" >&2
    echo "  ${DB} from this host's LAN (scoped to ${DB} only, never widened to any other" >&2
    echo "  database on this cluster)." >&2
    exit 1
}

if [ "$DB_EXISTS" != "1" ] || [ "$OWNER_ROLE_EXISTS" != "1" ] || [ "$RO_ROLE_EXISTS" != "1" ]; then
    _refuse_unreachable "not attempted (db/role(s) missing above)"
fi
PROBE_OUT="$(psql -h "$HOST" -d "$DB" -U "$DB_OWNER_ROLE" -tAc "SELECT 1;" 2>&1)" || _refuse_unreachable "$PROBE_OUT"
echo "== standing db '${DB}' reachable as '${DB_OWNER_ROLE}' =="

# --- TREE: git-archive export (default) or --worktree ------------------------------------------
if [ "$WORKTREE" = "1" ]; then
    echo "== --worktree: git worktree add $DEST $RESOLVED_SHA (git history included) =="
    (cd "$AUTOHARN_ROOT" && git worktree add --detach "$DEST" "$RESOLVED_SHA")
else
    echo "== default: git-archive export of $RESOLVED_SHA into $DEST (no .git -- no path back to" \
         "this checkout's project identity) =="
    mkdir -p "$DEST"
    (cd "$AUTOHARN_ROOT" && git archive --format=tar "$RESOLVED_SHA") | (cd "$DEST" && tar -xf -)
fi

# --- WIPE (default; --no-wipe skips) -----------------------------------------------------------
# Single-tenant by construction (standing practice, per decision row 229): the standing db holds
# exactly one snapshot at a time, so this script's DEFAULT first DB act is to make sure it starts
# from empty -- witnessed both before and after, never a silent assumption that it already was.
if [ "$NO_WIPE" != "1" ]; then
    BEFORE_SCHEMAS="$(psql -h "$HOST" -d "$DB" -U "$DB_OWNER_ROLE" -tAc \
        "SELECT string_agg(schema_name, ', ') FROM information_schema.schemata WHERE schema_name NOT LIKE 'pg\_%' AND schema_name NOT IN ('information_schema','public');")"
    echo "== wipe: schemas in ${DB} before: ${BEFORE_SCHEMAS:-(none)} =="
    if [ -n "$BEFORE_SCHEMAS" ]; then
        psql -h "$HOST" -d "$DB" -U "$DB_OWNER_ROLE" -v ON_ERROR_STOP=1 -tAc \
            "SELECT 'DROP SCHEMA IF EXISTS \"' || schema_name || '\" CASCADE;' FROM information_schema.schemata WHERE schema_name NOT LIKE 'pg\_%' AND schema_name NOT IN ('information_schema','public');" \
            | psql -h "$HOST" -d "$DB" -U "$DB_OWNER_ROLE" -v ON_ERROR_STOP=1
    fi
    AFTER_SCHEMAS="$(psql -h "$HOST" -d "$DB" -U "$DB_OWNER_ROLE" -tAc \
        "SELECT string_agg(schema_name, ', ') FROM information_schema.schemata WHERE schema_name NOT LIKE 'pg\_%' AND schema_name NOT IN ('information_schema','public');")"
    echo "== wipe: schemas in ${DB} after: ${AFTER_SCHEMAS:-(none)} =="
    if [ -n "$AFTER_SCHEMAS" ]; then
        echo "freeze-at-stamp: REFUSED -- wipe did not achieve an empty database (schemas remain:" >&2
        echo "  $AFTER_SCHEMAS). Refusing to restore on top of an unexpectedly non-empty target." >&2
        exit 1
    fi
else
    echo "== --no-wipe: skipping the default wipe (caller's own responsibility that ${DB} is empty) =="
fi

# --- STRUCTURE + DATA restore (schema-then-data, set_stamp disabled around the data load) --------
echo "== restoring structure: pg_dump --schema-only of ${SRC_SCHEMA}+${SRC_KERN} -> ${DB} =="
pg_dump -h "$SRC_HOST" -d "$SRC_DB" -n "$SRC_SCHEMA" -n "$SRC_KERN" --schema-only --no-owner --no-privileges \
    | psql -h "$HOST" -d "$DB" -U "$DB_OWNER_ROLE" -v ON_ERROR_STOP=1

echo "== disabling set_stamp + the referential validate_* triggers on ${DB}.${SRC_SCHEMA}.ledger" \
     "for the data load (see header: CHAIN CONTINUITY / per-table disposition) ==" >&2
echo "   set_stamp: unconditionally overwrites stamp_* from empty GUCs on a plain restore --" >&2
echo "   disabled so the source's real stamp columns copy byte-for-byte." >&2
echo "   validate_enacts/review/amends/answers/work_item: each re-checks that a referenced row" >&2
echo "   is an EARLIER row in the same session/ts order. pg_dump's --data-only COPY order is the" >&2
echo "   table's on-disk physical order, which is NOT guaranteed to equal ascending id/ts order" >&2
echo "   for a live table -- re-validating a graph that ALREADY passed these exact checks when" >&2
echo "   each row was first written is redundant work, and redundant work that is fragile" >&2
echo "   against an ordering pg_dump does not promise. Disabling them for a verbatim,"  >&2
echo "   content-preserving copy is the correct disposition, not a shortcut: nothing about the" >&2
echo "   copy can introduce a graph the source did not already have. row_hash/chain_high_water" >&2
echo "   triggers stay ENABLED throughout -- they are what this script relies on to self-verify" >&2
echo "   the copy (see CHAIN CONTINUITY above)." >&2
psql -h "$HOST" -d "$DB" -U "$DB_OWNER_ROLE" -v ON_ERROR_STOP=1 -c \
    "ALTER TABLE ${SRC_SCHEMA}.ledger DISABLE TRIGGER set_stamp;
     ALTER TABLE ${SRC_SCHEMA}.ledger DISABLE TRIGGER validate_enacts;
     ALTER TABLE ${SRC_SCHEMA}.ledger DISABLE TRIGGER validate_review;
     ALTER TABLE ${SRC_SCHEMA}.ledger DISABLE TRIGGER validate_amends;
     ALTER TABLE ${SRC_SCHEMA}.ledger DISABLE TRIGGER validate_answers;
     ALTER TABLE ${SRC_SCHEMA}.ledger DISABLE TRIGGER validate_work_item;
     ALTER TABLE ${SRC_SCHEMA}.ledger DISABLE TRIGGER one_row_per_insert;"

echo "== restoring data: pg_dump --data-only of ${SRC_SCHEMA}+${SRC_KERN} -> ${DB} (row_hash /" \
     "chain_high_water triggers stay ENABLED and self-verify on replay) =="
# NOTE: pg_dump's OWN --disable-triggers flag is deliberately NOT used here -- it emits
# `ALTER TABLE ... DISABLE TRIGGER ALL`, which requires superuser (this script's owner role is
# not one). The six triggers that actually need disabling are already handled by hand, above; the
# "circular foreign-key" NOTICE pg_dump prints for the self-referencing ledger/principal tables is
# expected (both tables genuinely self-reference: ledger.supersedes/regards/amends/answers ->
# ledger.id, principal.acts_for -> principal.id) and harmless once those triggers are off.
pg_dump -h "$SRC_HOST" -d "$SRC_DB" -n "$SRC_SCHEMA" -n "$SRC_KERN" --data-only --no-owner --no-privileges \
    | psql -h "$HOST" -d "$DB" -U "$DB_OWNER_ROLE" -v ON_ERROR_STOP=1

echo "== re-enabling set_stamp + the referential validate_* triggers =="
psql -h "$HOST" -d "$DB" -U "$DB_OWNER_ROLE" -v ON_ERROR_STOP=1 -c \
    "ALTER TABLE ${SRC_SCHEMA}.ledger ENABLE TRIGGER set_stamp;
     ALTER TABLE ${SRC_SCHEMA}.ledger ENABLE TRIGGER validate_enacts;
     ALTER TABLE ${SRC_SCHEMA}.ledger ENABLE TRIGGER validate_review;
     ALTER TABLE ${SRC_SCHEMA}.ledger ENABLE TRIGGER validate_amends;
     ALTER TABLE ${SRC_SCHEMA}.ledger ENABLE TRIGGER validate_answers;
     ALTER TABLE ${SRC_SCHEMA}.ledger ENABLE TRIGGER validate_work_item;
     ALTER TABLE ${SRC_SCHEMA}.ledger ENABLE TRIGGER one_row_per_insert;"

# --- TRUNCATE at cutoff (ledger, then review_detail's now-dangling rows) -------------------------
echo "== truncating ${DB}.${SRC_SCHEMA}.ledger to id <= ${CUTOFF_ID} (disabling append_only_row" \
     "around the DELETE, schema-owner-level act, mirrors seen-red/s27-chain-high-water/'s own" \
     "delete_row() idiom) =="
psql -h "$HOST" -d "$DB" -U "$DB_OWNER_ROLE" -v ON_ERROR_STOP=1 <<SQL
ALTER TABLE ${SRC_SCHEMA}.ledger DISABLE TRIGGER append_only_row;
ALTER TABLE ${SRC_SCHEMA}.review_detail DISABLE TRIGGER review_detail_append_only;
DELETE FROM ${SRC_SCHEMA}.review_detail WHERE ledger_id NOT IN (SELECT id FROM ${SRC_SCHEMA}.ledger WHERE id <= ${CUTOFF_ID});
DELETE FROM ${SRC_SCHEMA}.ledger WHERE id > ${CUTOFF_ID};
ALTER TABLE ${SRC_SCHEMA}.review_detail ENABLE TRIGGER review_detail_append_only;
ALTER TABLE ${SRC_SCHEMA}.ledger ENABLE TRIGGER append_only_row;
SQL

# chain_high_water is a POST-s27 relation (kernel/lineage/s27-chain-high-water.sql) -- LIVE-probed,
# never assumed present, exactly the convention verify-chain.tmpl's own has_high_water_layer() uses:
# this repo's own root tracker was found (2026-07-12, while building this script) to predate s26/s27
# entirely (no row_hash column, no chain_genesis/chain_high_water relations at all) -- an honest fact
# about the live source, not a defect to paper over. A source that DOES carry s27 gets its witness
# reseeded to the cutoff (never left at the live value, or the frozen dest would misreport
# TAIL-DELETION-SUSPECT); a pre-s27 source has nothing to reseed, and the frozen copy inherits that
# same honest pre-s27 shape, which ./verify-chain there reports as WITNESS-UNAVAILABLE, never a crash.
HAS_HIGH_WATER="$(psql -h "$HOST" -d "$DB" -U "$DB_OWNER_ROLE" -tAc \
    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = '${SRC_KERN}' AND table_name = 'chain_high_water');")"
if [ "$HAS_HIGH_WATER" = "t" ]; then
    echo "== resetting ${DB}.${SRC_KERN}.chain_high_water to the cutoff max id (${CUTOFF_ID}), never" \
         "left at the source's live value -- see header's per-table disposition =="
    psql -h "$HOST" -d "$DB" -U "$DB_OWNER_ROLE" -v ON_ERROR_STOP=1 -c \
        "UPDATE ${SRC_KERN}.chain_high_water SET max_id = ${CUTOFF_ID};"
else
    echo "== ${SRC_KERN}.chain_high_water not present in the source -- this tracker's kernel" \
         "predates kernel/lineage/s27-chain-high-water.sql; nothing to reseed, and the frozen" \
         "copy honestly inherits the same pre-s27 shape (./verify-chain there reports" \
         "WITNESS-UNAVAILABLE, never a false SUSPECT) =="
fi

echo "== resyncing sequences to the truncated max ids (never left ahead of the surviving rows) =="
psql -h "$HOST" -d "$DB" -U "$DB_OWNER_ROLE" -v ON_ERROR_STOP=1 <<SQL
SELECT setval(pg_get_serial_sequence('${SRC_SCHEMA}.ledger', 'id'), ${CUTOFF_ID});
SELECT setval(pg_get_serial_sequence('${SRC_KERN}.principal', 'id'),
              (SELECT max(id) FROM ${SRC_KERN}.principal));
SQL

# --- GRANTS: SELECT-only by default (--writable skips the revoke) --------------------------------
psql -h "$HOST" -d "$DB" -U "$DB_OWNER_ROLE" -v ON_ERROR_STOP=1 <<SQL
GRANT USAGE ON SCHEMA ${SRC_SCHEMA}, ${SRC_KERN} TO ${DB_RO_ROLE};
GRANT SELECT ON ALL TABLES IN SCHEMA ${SRC_SCHEMA} TO ${DB_RO_ROLE};
GRANT SELECT ON ALL TABLES IN SCHEMA ${SRC_KERN} TO ${DB_RO_ROLE};
SQL
if [ "$WRITABLE" != "1" ]; then
    echo "== SELECT-only grants (default): no INSERT/UPDATE/DELETE for ${DB_RO_ROLE} -- a write" \
         "attempt fails at the db, refused by GRANT, not by convention =="
else
    echo "== --writable: granting INSERT on ${SRC_SCHEMA}.ledger + related tables to ${DB_RO_ROLE}" \
         "(evidence-grade default overridden explicitly) =="
    psql -h "$HOST" -d "$DB" -U "$DB_OWNER_ROLE" -v ON_ERROR_STOP=1 <<SQL
GRANT INSERT ON ${SRC_SCHEMA}.ledger, ${SRC_SCHEMA}.review_detail, ${SRC_SCHEMA}.countersign_obligation TO ${DB_RO_ROLE};
GRANT INSERT ON ${SRC_KERN}.principal TO ${DB_RO_ROLE};
GRANT USAGE ON SEQUENCE ${SRC_SCHEMA}.ledger_id_seq, ${SRC_KERN}.principal_id_seq TO ${DB_RO_ROLE};
SQL
fi

# --- REPOINT: dest deployment.json + shims exec the DEST's own bootstrap/templates --------------
echo "== writing $DEST/deployment.json (db=${DB}, role=${DB_RO_ROLE}) =="
"$PY" - "$AUTOHARN_ROOT" "$DEST/deployment.json" "$DB" "$HOST" "$SRC_SCHEMA" "$SRC_KERN" "$DB_RO_ROLE" "frozen-${SHORT_SHA}" <<'PYEOF'
import sys
autoharn_root, path, db, host, schema, kern, role, name = sys.argv[1:9]
sys.path.insert(0, autoharn_root + "/filing")
from deployment_record import DeploymentRecord, write_deployment
write_deployment(path, DeploymentRecord(db=db, host=host, schema=schema, kern=kern, role=role, name=name))
print(f"wrote {path}")
PYEOF

echo "== writing $DEST verb shims (exec the DEST's OWN bootstrap/templates, never the live" \
     "checkout's -- live-verbs semantics are exactly wrong for settled evidence) =="
# WHY PGUSER=$DB_RO_ROLE IS SET HERE (a real hazard found and closed while witnessing this script,
# not assumed): every existing verb template (led.tmpl/pickup.tmpl/judge.tmpl/verify-chain.tmpl/...)
# connects with a bare `psql -h <host> -d <db> ...` -- NO `-U` flag anywhere -- and relies on the
# CONNECTING OS/ambient identity already having pg_hba access, plus a `SET ROLE <granted-role>`
# inside the SQL for a scaffolded --new-world (where the operator's own login is a member of that
# role). That convention is exactly wrong for THIS deployment's pg_hba scoping (decision row
# 229): pg_hba on this host permits ONLY `autoharn_test_owner`/`autoharn_test_ro` to connect to
# `autoharn_test` at all -- the operator's own OS login (e.g. `bork`) has NO entry for this
# database, witnessed live while building this script (a bare `psql -h ... -d autoharn_test`
# refuses with "no pg_hba.conf entry for ... user \"bork\"", before any SET ROLE is even reached).
# `PGUSER` is libpq's own standard env-var override for the connecting role (psql's `-U` flag reads
# the identical variable) -- setting it in the shim's exec environment makes every one of those
# unmodified verb templates connect AS `$DB_RO_ROLE` directly, with no edit to any .tmpl file
# needed (ADR-0012 P1: the ONE existing connection mechanism, given the right identity, rather than
# a second one grown here). The subsequent `SET ROLE <role>` each template still issues becomes a
# harmless no-op (a role may always SET ROLE to itself).
for verb in led judge pickup audit distance-to-clean verify-commission verify-chain attest-doc; do
    cat > "$DEST/$verb" <<SHIM
#!/bin/sh
HERE="\$(cd "\$(dirname "\$0")" && pwd)"
exec env PICKUP_DEPLOYMENT="\$HERE/deployment.json" AUTOHARN="\$HERE" PGUSER="$DB_RO_ROLE" "\$HERE/bootstrap/templates/$verb.tmpl" "\$@"
SHIM
    chmod +x "$DEST/$verb"
done
echo "wrote led, judge, pickup, audit, distance-to-clean, verify-commission, verify-chain, attest-doc"

# --- PROVENANCE: the honest "settled evidence, never refreshed" record --------------------------
cat > "$DEST/FROZEN-PROVENANCE.md" <<PROV
# FROZEN-PROVENANCE — this tree is settled evidence, never refreshed

Produced by \`bootstrap/freeze-at-stamp.sh\` (autoharn) on $(date -u +%Y-%m-%dT%H:%M:%SZ).

- **Source commit:** $RESOLVED_SHA (short $SHORT_SHA), committer ts $COMMITTER_TS.
- **Tree mode:** $([ "$WORKTREE" = "1" ] && echo "git worktree (history included)" || echo "git-archive export (no .git — no path back to the parent project's identity)").
- **Tracker cutoff:** ledger id <= $CUTOFF_ID (basis: $CUTOFF_TS), source tracker's own max id at
  freeze time was $SRC_MAX_ID.
- **Frozen database:** \`$DB\` (standing, single-tenant; wiped before this snapshot unless
  --no-wipe was passed), schema pair \`$SRC_SCHEMA\`/\`$SRC_KERN\`, read as role \`$DB_RO_ROLE\`
  ($([ "$WRITABLE" = "1" ] && echo "writable — explicitly overridden" || echo "SELECT-only — the default")).

**This is settled evidence frozen at that instant. It is never refreshed, never delta'd, never
re-synced with the live tracker or the live checkout — runs-are-linear applies here exactly as it
does to a dead run's world (CLAUDE.md ORCHESTRATION, 2026-07-11 ruling). If the underlying work
continues, that continuation is a NEW freeze of a NEW cutoff, not an update to this one.**

Honest residual: the frozen database is isolated from the live tracker's database and connecting
role, but same-Postgres-cluster surfaces (the server's log stream, \`pg_stat_activity\`) remain
shared across every database on this host — distinguishable by database name and role, not by a
harder boundary. Full cluster separation is a host-level act, out of this script's scope.
PROV
echo "wrote $DEST/FROZEN-PROVENANCE.md"

echo "== done: $DEST is frozen at $RESOLVED_SHA / ledger id <= $CUTOFF_ID =="
echo "   cd $DEST && ./pickup   # reads ONLY the frozen ${DB} snapshot, via this dest's own templates"
