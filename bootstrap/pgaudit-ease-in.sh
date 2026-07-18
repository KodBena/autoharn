#!/bin/sh
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T17:00:20Z
#   last-change: 2026-07-15T17:00:20Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

# pgaudit-ease-in.sh -- pave the path for pgAudit adoption WITHOUT touching any server (ledger
# item `pgaudit-ease-in`, maintainer 2026-07-15: TESTING parked, path paved for whenever he or an
# adopter wants to try). Reads a deployment's live Postgres target read-only and reports pgAudit's
# state (`inspect`), and separately prints -- never runs -- the scoped enable/disable statement
# pair for that deployment's own role (`emit`). Same emits-never-executes contract as
# `bootstrap/provision-db.sh`: every SQL fragment this script prints is for an operator with
# appropriate privilege to run on their own schedule; this script issues SELECT/SHOW-shaped reads
# only, never DDL/DML, never ALTER SYSTEM, never CREATE EXTENSION, never ALTER ROLE.
#
# SIBLING SCRIPT, NOT A provision-db.sh FLAG -- WHY:
#   provision-db.sh's whole job is PRE-provisioning: it derives schema/kern/role from a bare
#   <name> the same way new-project.sh --new-world does, because the role and database do not
#   exist yet. This script is POST-provisioning: it targets a deployment that already exists, and
#   takes its target from that deployment's OWN deployment.json (db/host/role -- the same record
#   every other live verb in a scaffolded project reads, filing/deployment_record.py, ADR-0012
#   P1: one home for that shape). The live queries are unrelated too -- pg_hba_file_rules vs.
#   pg_settings/pg_extension/pg_db_role_setting -- and the output shape differs (a report plus an
#   emitted statement pair, not files written to an --out directory). Bolting a second input axis
#   (deployment.json vs. --db/--host/--client-cidr) onto one script's flag parser would blur one
#   script, one job -- the same compositional-hygiene reasoning ADR-0012 already applies elsewhere
#   in bootstrap/.
#
# Usage:
#   bootstrap/pgaudit-ease-in.sh inspect [--deployment <path>]
#   bootstrap/pgaudit-ease-in.sh emit    [--deployment <path>] [--classes <classes>]
#
#   inspect          read-only report: is the module loaded, the master GUC value + its
#                     sourcefile:line, whether the extension is available/installed, and any
#                     existing pgaudit.* per-role/per-database override -- nothing is written or
#                     changed.
#   emit             prints (never runs) the scoped ALTER ROLE enable/disable pair for this
#                     deployment's own role, the verification query, and the honest shared-cluster
#                     note. Also runs the same read-only checks `inspect` does, so the printed
#                     block can name loudly whether its own prerequisites (module loaded, extension
#                     created) are actually met on the live target right now.
#   --deployment      path to a deployment.json (default: this checkout's own root
#                     deployment.json, mirroring bootstrap/freeze-at-stamp.sh's own default). A
#                     missing or malformed record is REFUSED loudly (filing/deployment_record.py),
#                     never silently guessed.
#   --classes         comma-separated pgaudit.log class list for `emit`'s ENABLE statement
#                     (default: ddl,role -- see the justification comment `emit` prints alongside
#                     it). Lightly validated against pgaudit's own documented class vocabulary
#                     (READ, WRITE, FUNCTION, ROLE, DDL, MISC, MISC_SET, ALL; a leading '-'
#                     subtracts) -- a refusal that teaches on a typo, not a full parser.
#
# CONNECTION: by default this script connects as the deployment's OWN role (the `role` field in
# deployment.json) -- the realistic question is "what will THIS role see," since that is exactly
# the role `emit`'s statement would apply to. Set PGUSER to connect as someone else instead (libpq
# reads PGUSER ahead of any -U this script would pass; precedented already by
# bootstrap/rehearse-from-origin.sh's own PGUSER pass-through) -- e.g. PGUSER=bork for a
# superuser-visibility read when the deployment role itself lacks pg_read_all_settings (see
# inspect's own permission-story output for exactly when that matters).
set -eu

usage() {
    echo "usage: $0 inspect [--deployment <path>]" >&2
    echo "       $0 emit    [--deployment <path>] [--classes <classes>]" >&2
    exit 2
}

[ $# -ge 1 ] || usage
MODE="$1"; shift
case "$MODE" in
    inspect|emit) ;;
    *) echo "pgaudit-ease-in.sh: unrecognized mode '$MODE' (want 'inspect' or 'emit')" >&2; usage ;;
esac

AUTOHARN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEPLOYMENT="$AUTOHARN_ROOT/deployment.json"
CLASSES="ddl,role"
while [ $# -gt 0 ]; do
    case "$1" in
        --deployment) DEPLOYMENT="$2"; shift 2 ;;
        --classes) CLASSES="$2"; shift 2 ;;
        *) echo "pgaudit-ease-in.sh: unrecognized argument: $1" >&2; usage ;;
    esac
done

PY="$HOME/w/vdc/venvs/generic/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"
[ -n "$PY" ] || { echo "pgaudit-ease-in.sh: REFUSED -- no python3 found to read deployment.json." >&2; exit 2; }

# --- resolve the deployment record via the ONE home for its shape (filing/deployment_record.py,
# ADR-0012 P1) -- same idiom bootstrap/freeze-at-stamp.sh already uses for its source deployment.
# A missing file, bad JSON, or a missing/empty required field is refused LOUDLY here, never
# silently guessed -- this is also the negative-polarity witness path (point --deployment at a
# bogus dir and this refusal is what fires).
_dep_vars="$("$PY" - "$AUTOHARN_ROOT" "$DEPLOYMENT" <<'PYEOF'
import sys, shlex
autoharn_root, dep_path = sys.argv[1:3]
sys.path.insert(0, autoharn_root + "/filing")
import deployment_record as dr
try:
    d = dr.load_deployment(dep_path)
except dr.DeploymentError as e:
    print(f"pgaudit-ease-in.sh: REFUSED -- cannot resolve the target deployment: {e}", file=sys.stderr)
    sys.exit(2)
for k in ("db", "host", "schema", "kern", "role"):
    print(f"DEP_{k.upper()}={shlex.quote(getattr(d, k))}")
PYEOF
)" || exit 2
eval "$_dep_vars"

# CLASS SANITY CHECK (emit only) -- refusal that teaches on a typo, not a full pgaudit parser.
if [ "$MODE" = "emit" ]; then
    OLD_IFS="$IFS"; IFS=','
    for tok in $CLASSES; do
        t="$(printf '%s' "$tok" | tr '[:upper:]' '[:lower:]')"
        case "$t" in
            -*) t="${t#-}" ;;
        esac
        case "$t" in
            read|write|function|role|ddl|misc|misc_set|all) ;;
            *) IFS="$OLD_IFS"; echo "pgaudit-ease-in.sh: REFUSED -- unrecognized pgaudit.log class '$tok' in --classes '$CLASSES' (known classes: READ WRITE FUNCTION ROLE DDL MISC MISC_SET ALL, optionally '-'-prefixed to subtract)." >&2; exit 2 ;;
        esac
    done
    IFS="$OLD_IFS"
fi

PSQL_USER="${PGUSER:-$DEP_ROLE}"
echo "== pgaudit-ease-in.sh $MODE: deployment role=$DEP_ROLE db=$DEP_DB host=$DEP_HOST (from $DEPLOYMENT), connecting as ${PSQL_USER} =="

# --- read-only live probes. Every query here is a plain SELECT/SHOW against catalog views; this
# script never issues DDL/DML/ALTER SYSTEM/ALTER ROLE/CREATE EXTENSION. -----------------------
PGAUDIT_GUCS="$(PGUSER="$PSQL_USER" psql -h "$DEP_HOST" -d "$DEP_DB" -tA -F'|' -c \
    "select name, setting, coalesce(sourcefile,''), coalesce(sourceline::text,''), context from pg_settings where name like 'pgaudit%' order by name" 2>&1)" || {
    echo "pgaudit-ease-in.sh: REFUSED -- could not read pg_settings from $DEP_HOST/$DEP_DB as $PSQL_USER:" >&2
    echo "  $PGAUDIT_GUCS" >&2
    exit 1
}
PRELOAD_ROW="$(PGUSER="$PSQL_USER" psql -h "$DEP_HOST" -d "$DEP_DB" -tA -F'|' -c \
    "select setting, coalesce(sourcefile,''), coalesce(sourceline::text,'') from pg_settings where name = 'shared_preload_libraries'" 2>&1)" || PRELOAD_ROW=""
AVAIL_EXT_ROW="$(PGUSER="$PSQL_USER" psql -h "$DEP_HOST" -d "$DEP_DB" -tA -F'|' -c \
    "select coalesce(default_version,''), coalesce(installed_version,'') from pg_available_extensions where name = 'pgaudit'" 2>&1)" || AVAIL_EXT_ROW=""
INSTALLED_EXT="$(PGUSER="$PSQL_USER" psql -h "$DEP_HOST" -d "$DEP_DB" -tA -c \
    "select extversion from pg_extension where extname = 'pgaudit'" 2>&1)" || INSTALLED_EXT=""
OVERRIDES="$(PGUSER="$PSQL_USER" psql -h "$DEP_HOST" -d "$DEP_DB" -tA -F'|' -c \
    "select r.rolname, coalesce(d.datname,'(cluster-wide role default)'), s.setconfig from pg_db_role_setting s join pg_roles r on r.oid = s.setrole left join pg_database d on d.oid = s.setdatabase where exists (select 1 from unnest(s.setconfig) c where c like 'pgaudit%') order by 1,2" 2>&1)" || OVERRIDES=""

if [ "$MODE" = "inspect" ]; then
    echo ""
    echo "-- (1) module loaded? --"
    echo "Primary check (no special permission needed -- a custom GUC like pgaudit.log can only"
    echo "appear in pg_settings at all once its owning module has been preloaded, so ANY role"
    echo "seeing rows here has its answer regardless of pg_read_all_settings):"
    N_ROWS="$(printf '%s\n' "$PGAUDIT_GUCS" | grep -c . || true)"
    if [ "$N_ROWS" -gt 0 ]; then
        echo "  name|setting|sourcefile|sourceline|context"
        printf '%s\n' "$PGAUDIT_GUCS" | sed 's/^/  /'
        echo "  => LOADED ($N_ROWS pgaudit.* GUC(s) visible)."
    else
        echo "  (0 rows)"
        echo "  => NOT LOADED (no pgaudit.* row exists in pg_settings at all)."
    fi
    echo ""
    echo "Secondary corroboration (needs pg_read_all_settings or superuser -- shared_preload_libraries"
    echo "is GUC_SUPERUSER_ONLY, hidden from pg_settings entirely for a role lacking that grant;"
    echo "witnessed live: an ordinary scoped role like ${DEP_ROLE} gets 0 rows here even though the"
    echo "primary check above already answered LOADED):"
    if [ -n "$PRELOAD_ROW" ] && [ "$(printf '%s' "$PRELOAD_ROW" | grep -c . || true)" -gt 0 ]; then
        echo "  shared_preload_libraries = $PRELOAD_ROW"
    else
        echo "  HIDDEN -- connecting role '${PSQL_USER}' cannot see shared_preload_libraries (lacks"
        echo "  pg_read_all_settings and is not superuser, or the query itself failed). Fallback:"
        echo "  retry with PGUSER=<a role holding pg_read_all_settings or superuser>, e.g. PGUSER=bork"
        echo "  on this cluster, to see the full preload list and confirm pgaudit.so's exact position"
        echo "  in it."
    fi
    echo ""
    echo "-- (2) master GUC value + sourcefile:line --"
    LOG_ROW="$(printf '%s\n' "$PGAUDIT_GUCS" | awk -F'|' '$1=="pgaudit.log"{print}')"
    if [ -n "$LOG_ROW" ]; then
        LOG_VAL="$(printf '%s' "$LOG_ROW" | awk -F'|' '{print $2}')"
        LOG_FILE="$(printf '%s' "$LOG_ROW" | awk -F'|' '{print $3}')"
        LOG_LINE="$(printf '%s' "$LOG_ROW" | awk -F'|' '{print $4}')"
        if [ -n "$LOG_FILE" ]; then
            echo "  pgaudit.log = '${LOG_VAL}'   (${LOG_FILE}:${LOG_LINE})"
        else
            echo "  pgaudit.log = '${LOG_VAL}'   (sourcefile:sourceline HIDDEN -- same"
            echo "  pg_read_all_settings/superuser gate as (1)'s secondary check; retry with a"
            echo "  privileged PGUSER to see exactly which conf file/line set it)"
        fi
    else
        echo "  pgaudit.log does not exist as a GUC (module not loaded, per (1))."
    fi
    echo ""
    echo "-- (3) extension present? --"
    echo "pg_available_extensions (cluster-wide -- reflects this SERVER's extension_control_path,"
    echo "NOT scoped to $DEP_DB; if ABSENT here it is absent for every database on this host):"
    if [ -n "$AVAIL_EXT_ROW" ] && [ "$(printf '%s' "$AVAIL_EXT_ROW" | grep -c . || true)" -gt 0 ] && [ "$AVAIL_EXT_ROW" != "|" ]; then
        echo "  default_version|installed_version = $AVAIL_EXT_ROW"
    else
        echo "  ABSENT -- no 'pgaudit' row in pg_available_extensions at all. CREATE EXTENSION pgaudit"
        echo "  would fail ('extension \"pgaudit\" is not available') even where the module IS loaded"
        echo "  per (1) -- the .so being preloaded and the extension's own .control/.sql files being"
        echo "  installed alongside it are two separate installation steps; this view only sees the"
        echo "  second. This script has no host filesystem access, so it cannot tell a genuinely"
        echo "  missing install apart from a partial one (.so present, control/sql files not) --"
        echo "  UNVERIFIED which, from here; an operator with shell access to $DEP_HOST would check"
        echo "  the server's extension directory directly."
    fi
    echo "pg_extension in THIS connection's own database ($DEP_DB) -- has CREATE EXTENSION pgaudit"
    echo "actually been run here (independent of whether it COULD be, per the check above)?"
    if [ -n "$INSTALLED_EXT" ] && [ "$(printf '%s' "$INSTALLED_EXT" | grep -c . || true)" -gt 0 ]; then
        echo "  extversion = $INSTALLED_EXT -- CREATED in $DEP_DB."
    else
        echo "  NOT created in $DEP_DB. (This script only checked the database it connected to; it"
        echo "  does not open a connection to every other database on the cluster to check theirs --"
        echo "  each database's pg_extension is genuinely per-database, unlike (3)'s cluster-wide"
        echo "  pg_available_extensions above.)"
    fi
    echo ""
    echo "-- (4) existing pgaudit.* per-role/per-database overrides (pg_db_role_setting, visible to"
    echo "any role -- not permission-gated like (1)/(2) above) --"
    if [ -n "$OVERRIDES" ] && [ "$(printf '%s\n' "$OVERRIDES" | grep -c . || true)" -gt 0 ]; then
        echo "  role|database|setconfig"
        printf '%s\n' "$OVERRIDES" | sed 's/^/  /'
    else
        echo "  none found -- no role or database on this cluster currently carries a pgaudit.*"
        echo "  ALTER ROLE/ALTER DATABASE SET override."
    fi
    exit 0
fi

# --- emit mode: print (never run) the scoped statement pair, informed by the same live checks. --
N_ROWS="$(printf '%s\n' "$PGAUDIT_GUCS" | grep -c . || true)"
EXT_CREATED="$INSTALLED_EXT"
echo ""
if [ "$N_ROWS" -eq 0 ]; then
    echo "WARNING (live, just checked): pgaudit is NOT currently loaded on $DEP_HOST (0 pgaudit.*"
    echo "GUCs in pg_settings). The statement below will still print -- it is meant to pave the path"
    echo "for whenever the module IS loaded -- but running it today would fail outright: pgaudit.log"
    echo "is not a recognized parameter name until shared_preload_libraries carries pgaudit and the"
    echo "server has been RESTARTED (not reloaded -- shared_preload_libraries is postmaster-context)."
    echo ""
fi
if [ -z "$EXT_CREATED" ]; then
    echo "WARNING (live, just checked): CREATE EXTENSION pgaudit has not been run in $DEP_DB (see"
    echo "inspect's item (3)). pgAudit's own documentation states this plainly: 'CREATE EXTENSION"
    echo "pgaudit must be called before pgaudit.log is set to ensure proper pgaudit functionality'"
    echo "(pgaudit README, REL_18_STABLE branch -- matches this host's PostgreSQL 18). Until an"
    echo "operator with the necessary privilege runs that statement in $DEP_DB, the ALTER ROLE below"
    echo "will be ACCEPTED by Postgres (pgaudit.log is a valid GUC name once the module is loaded --"
    echo "setting it does not itself require the extension to exist) but pgAudit will not actually"
    echo "audit anything until the extension is created."
    echo ""
fi

cat <<SQL
-- pgAudit scoped enable/disable for role '$DEP_ROLE' (deployment '$DEPLOYMENT'), database '$DEP_DB'
-- on host '$DEP_HOST'. Printed only -- run neither statement until you have decided to. Both are
-- an operator act requiring superuser (or a role separately GRANTed SET on this parameter, PG15+
-- GRANT ... ON PARAMETER -- UNVERIFIED whether that grant works for a module-registered custom GUC
-- like pgaudit.log on this cluster; not exercised).
--
-- PERMISSION: pgaudit.log's GUC context is 'superuser' (verified live against $DEP_HOST --
-- see inspect item (1)/(2)) -- per pgaudit's own README, "Settings may be modified only by a
-- superuser." The role being altered ($DEP_ROLE) does NOT need to be a superuser itself; the
-- OPERATOR RUNNING this ALTER ROLE statement does.
--
-- RESTART-FREE: this is a per-role ALTER (context=superuser, not postmaster/sighup), so it takes
-- effect the NEXT time $DEP_ROLE opens a session -- no server restart, no pg_reload_conf() needed.
-- That is the entire point of the scoped shape versus the cluster-wide postgresql.conf lever.

-- ENABLE (classes: $CLASSES):
ALTER ROLE $DEP_ROLE SET pgaudit.log = '$CLASSES';

-- DISABLE (revert to the cluster default -- currently 'none', postgresql.conf:810 on this host):
ALTER ROLE $DEP_ROLE RESET pgaudit.log;

-- VERIFY (after the ENABLE above, from a NEW session -- the current session's setting does not
-- change retroactively):
SHOW pgaudit.log;   -- run while connected AS $DEP_ROLE
-- or, from any role (pg_db_role_setting is not permission-gated, unlike pg_settings' hidden rows):
SELECT r.rolname, s.setconfig FROM pg_db_role_setting s JOIN pg_roles r ON r.oid = s.setrole WHERE r.rolname = '$DEP_ROLE';

-- CLASS CHOICE ('$CLASSES'), justified: this project's own ledger is append-only, hash-chained
-- (kernel/lineage/s26-row-hash-chain.sql), and every write reaches it through a verb (led/pickup/
-- etc) -- so pgaudit's WRITE class would mostly duplicate a trail the ledger already keeps for
-- verb-issued writes. What the ledger's own machinery CANNOT see is exactly what bypasses the verb
-- layer entirely: DDL (schema changes made with raw CREATE/ALTER/DROP by a role with CREATE, not
-- through any verb) and ROLE (grant/role changes -- who can do what -- made outside the verb
-- layer). Those two classes are this deployment's scoped default. READ is deliberately NOT
-- included -- audit-of-reads is a separate, larger decision with its own log-volume and evidence-
-- classification tradeoffs (parked, see vestigial_documentation/design/ORCH-PGAUDIT-EXPLORATION.md, reason 1); add it
-- explicitly (pgaudit.log = 'ddl,role,read') if and when that separate decision is made.

-- SHARED-CLUSTER NOTE: the ALTER ROLE above is scoped to ONE role ($DEP_ROLE) on ONE database
-- ($DEP_DB). Every other project sharing this cluster is unaffected -- verified live (inspect item
-- (4)) that no role or database on this host currently carries a pgaudit.* override. The CLUSTER-
-- WIDE lever is postgresql.conf's own pgaudit.log setting (currently 'none' on this host) -- that
-- line is NOT emitted here and this script never touches it: changing it would affect every
-- project sharing this Postgres instance, and a postgresql.conf edit is always an operator act on
-- the live file, on their own schedule (this project's standing config-fragments rule).
SQL
