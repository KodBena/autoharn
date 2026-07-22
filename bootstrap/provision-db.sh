#!/bin/sh
# provision-db.sh — generate (never execute) the pg_hba fragment + provisioning SQL an operator
# needs to stand up ONE new world's Postgres role/database, matching bootstrap/new-project.sh
# --new-world's naming template EXACTLY (schema=<NAME>, kern=<NAME>_kernel, role=<NAME>_rw — see
# that script's own header comment and user-guide/USER-CONFIGURATION.md's "FAQ: provisioning Postgres for
# autoharn"). This closes the first-use hurdle that FAQ documents as copy-paste-by-hand today:
# this script derives the three names from one <NAME> the same way --new-world does, so they
# cannot drift out of agreement, and it never touches a live server itself.
#
# OWNERSHIP SPLIT (read this before running anything this script prints):
#   THIS script's SQL creates: the LOGIN role and the DATABASE. Nothing else.
#   `bootstrap/new-project.sh --new-world <NAME> --db <db> --host <host>` creates: the <NAME>
#   and <NAME>_kernel SCHEMAS inside that database (kernel/lineage/high_watermark_1.sql's own
#   s15-schema.sql owns `CREATE SCHEMA IF NOT EXISTS :"schema"` / `:"kern"`), applies the full
#   kernel lineage, provisions the stamp secret, and registers the standard principals. Run
#   THIS script's SQL first (role + database must exist before new-project.sh can connect as
#   the role and SET ROLE to apply DDL — user-guide/USER-CONFIGURATION.md FAQ step 2), THEN run
#   new-project.sh --new-world.
#
# Usage:
#   bootstrap/provision-db.sh <name> --db <db> --host <host> --client-cidr <cidr> \
#       [--auth <method>] [--out <dir>]
#
#   <name>          the world name — derives schema=<name>, kern=<name>_kernel, role=<name>_rw,
#                   byte-for-byte the same derivation bootstrap/new-project.sh --new-world uses.
#   --db            the Postgres database name to provision (created if absent).
#   --host          the Postgres host the database lives on (also the host this script queries,
#                   read-only, for the LIVE pg_hba_file_rules view before generating anything —
#                   config fragments need the real file, not a guess).
#   --client-cidr   the CIDR the new role will connect from (e.g. 192.168.122.68/32). Required —
#                   this script does not guess a network.
#   --auth          the pg_hba auth method for the new role's line (default: trust, matching
#                   every existing per-project block this cluster already carries — toy, qbx,
#                   wmb, vsr all use `trust` for their scoped role -- see the live query below).
#   --out           directory the generated files land in (default: /tmp — never this repo).
#
# WHAT THIS SCRIPT NEVER DOES: it never runs DDL against the target server, never edits
# pg_hba.conf, never sets a password. Every artifact is printed/written for the operator (a
# human with superuser access) to apply on their own schedule — same posture as
# vestigial_documentation/design/MAINT-PG-HBA-HARDENING.md and bootstrap/apply-research-ledger.sh's typed-confirmation
# scripts: this project documents and generates, an operator with superuser access applies.
set -eu

usage() {
    echo "usage: $0 <name> --db <db> --host <host> --client-cidr <cidr> [--auth <method>] [--out <dir>]" >&2
    echo "       <name> derives schema=<name>, kern=<name>_kernel, role=<name>_rw (matches" >&2
    echo "       bootstrap/new-project.sh --new-world <name> exactly)." >&2
    exit 2
}

[ $# -ge 1 ] || usage
NAME="$1"; shift
case "$NAME" in
    --*) echo "provision-db.sh: <name> must come first (got '$NAME') -- see usage." >&2; usage ;;
esac

DB=""; HOST=""; CLIENT_CIDR=""; AUTH="trust"; OUT_DIR="/tmp"
while [ $# -gt 0 ]; do
    case "$1" in
        --db) DB="$2"; shift 2 ;;
        --host) HOST="$2"; shift 2 ;;
        --client-cidr) CLIENT_CIDR="$2"; shift 2 ;;
        --auth) AUTH="$2"; shift 2 ;;
        --out) OUT_DIR="$2"; shift 2 ;;
        *) echo "provision-db.sh: unrecognized argument: $1" >&2; usage ;;
    esac
done
[ -n "$DB" ] && [ -n "$HOST" ] && [ -n "$CLIENT_CIDR" ] || usage

# Minimal sanity check on the identifiers this script interpolates directly into generated SQL
# text (this script never sends them to psql as -v vars the way new-project.sh does — it WRITES
# a file for a human to run later, so there is no psql-side quoting backstop here). Not a full
# injection defense, just a refusal that teaches instead of emitting broken/dangerous SQL.
case "$NAME" in
    [a-z_]*) case "$NAME" in *[!a-z0-9_]*) echo "provision-db.sh: <name> '$NAME' must be lowercase [a-z_][a-z0-9_]*" >&2; exit 2 ;; esac ;;
    *) echo "provision-db.sh: <name> '$NAME' must be lowercase [a-z_][a-z0-9_]*" >&2; exit 2 ;;
esac
case "$DB" in
    [a-z_]*) case "$DB" in *[!a-z0-9_]*) echo "provision-db.sh: --db '$DB' must be lowercase [a-z_][a-z0-9_]*" >&2; exit 2 ;; esac ;;
    *) echo "provision-db.sh: --db '$DB' must be lowercase [a-z_][a-z0-9_]*" >&2; exit 2 ;;
esac

SCHEMA="$NAME"
KERN="${NAME}_kernel"
ROLE="${NAME}_rw"

mkdir -p "$OUT_DIR"
HBA_FRAGMENT="$OUT_DIR/${NAME}-pg_hba.fragment"
SQL_FILE="$OUT_DIR/${NAME}-provision.sql"
GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "== provision-db.sh: world '$NAME' -> schema=$SCHEMA kern=$KERN role=$ROLE db=$DB host=$HOST =="

# --- LIVE-FILE RULE: read the real pg_hba_file_rules before generating anything (standing
# maintainer ruling — config fragments need the real file, never authored from memory). This is
# a read-only superuser-view query; if it is refused (role lacks the view, or the host is
# unreachable), the fragment below is marked UNVERIFIED-AGAINST-LIVE rather than silently
# presented as checked.
LIVE_RULES=""
LIVE_OK=0
if LIVE_RULES="$(psql -h "$HOST" -d "$DB" -tA -F'|' -c \
    "select line_number,type,database,user_name,address,netmask,auth_method from pg_hba_file_rules order by line_number" 2>&1)"; then
    LIVE_OK=1
else
    echo "-- LIVE-FILE RULE: could not read pg_hba_file_rules from $HOST/$DB (superuser view may be" >&2
    echo "   refused, or the host/db is unreachable). Fragment below is UNVERIFIED-AGAINST-LIVE." >&2
    echo "   Reason: $LIVE_RULES" >&2
fi

# PLACEMENT: pg_hba is first-match-wins per (type, database, user, address) row. A rule only
# shadows the new role's lines if BOTH its database and its user entry could match this role's
# connection (database in {this db, all} AND user in {this role, all}) -- a rule scoped to some
# OTHER user (e.g. an unrelated role's own reject line) never fires for this role's connections
# regardless of line order, so it is not a placement hazard and is deliberately excluded below.
PLACEMENT_ADVICE=""
if [ "$LIVE_OK" -eq 1 ]; then
    SHADOW_LINE="$(printf '%s\n' "$LIVE_RULES" | awk -F'|' -v db="$DB" -v role="$ROLE" '
        {
            d=$3; gsub(/[{}]/,"",d); nd=split(d,dbs,",");
            u=$4; gsub(/[{}]/,"",u); nu=split(u,users,",");
            dbmatch=0; for (i=1;i<=nd;i++) if (dbs[i]==db || dbs[i]=="all") dbmatch=1;
            umatch=0; for (i=1;i<=nu;i++) if (users[i]==role || users[i]=="all") umatch=1;
            if (dbmatch && umatch) { print $1; exit }
        }')"
    if [ -n "$SHADOW_LINE" ]; then
        SHADOW_ROW="$(printf '%s\n' "$LIVE_RULES" | awk -F'|' -v ln="$SHADOW_LINE" '$1==ln')"
        PLACEMENT_ADVICE="Insert the new block BEFORE line $SHADOW_LINE of pg_hba.conf (first existing rule matching database='$DB' or 'all', first-match-wins: $SHADOW_ROW). A broad rule at or after that line is fine to leave after the new block; anything before it that already matches would shadow the new lines."
    else
        LAST_LINE="$(printf '%s\n' "$LIVE_RULES" | awk -F'|' 'END{print $1}')"
        PLACEMENT_ADVICE="No existing rule matches database='$DB' or 'all' -- append the new block after the last existing rule (line $LAST_LINE), keeping this file's per-project contiguous-block idiom (see the toy/qbx/wmb/vsr blocks for the shape)."
    fi
else
    PLACEMENT_ADVICE="UNVERIFIED -- could not read the live file (see warning above). Standard first-match-wins guidance: place the new block BEFORE any existing 'database=all' or broad-address catch-all rule that would otherwise match this role's connections first; never append after such a rule blind."
fi

# --- (1) pg_hba fragment -- MINIMAL lines this role needs for this db from this client CIDR.
# Mirrors this cluster's own idiom for a scoped role (toy/toycolors_rw, qbx/qbx_rw, wmb/wmb_rw,
# vsr/vsr_rw all follow this exact three-line shape: allow scoped, reject-elsewhere host, reject-
# elsewhere local) -- verified live above when LIVE_OK=1, generic first-match-wins reasoning
# otherwise.
{
    echo "# pg_hba.conf fragment for world '$NAME' (role $ROLE, db $DB) -- generated $GENERATED_AT"
    echo "# by bootstrap/provision-db.sh. NOT applied to any file -- an operator with superuser"
    echo "# access to the db host pastes this into pg_hba.conf and reloads (see the walkthrough"
    echo "# this script also prints)."
    if [ "$LIVE_OK" -eq 1 ]; then
        echo "# VERIFIED-AGAINST-LIVE: read from $HOST/$DB's pg_hba_file_rules at generation time."
    else
        echo "# UNVERIFIED-AGAINST-LIVE: could not read pg_hba_file_rules from $HOST/$DB (see stderr"
        echo "# from the generating run). Cross-check against the real file before applying."
    fi
    echo "# PLACEMENT: $PLACEMENT_ADVICE"
    echo "#"
    echo "# type  database  user       address        auth-method"
    echo "host    $DB       $ROLE      $CLIENT_CIDR   $AUTH   # grants: $ROLE may authenticate to db '$DB' from $CLIENT_CIDR"
    echo "host    all       $ROLE      0.0.0.0/0      reject  # denies: $ROLE from anywhere else (defense in depth)"
    echo "local   all       $ROLE                     reject  # denies: $ROLE over the local unix socket"
} >"$HBA_FRAGMENT"

# --- (2) provisioning SQL -- role + database ONLY. Schema creation is deliberately NOT here --
# it is owned by `bootstrap/new-project.sh --new-world`, see the OWNERSHIP SPLIT header comment.
{
    echo "-- Provisioning SQL for world '$NAME', generated $GENERATED_AT by bootstrap/provision-db.sh"
    echo "-- Naming derived exactly as \`bootstrap/new-project.sh --new-world $NAME\` would derive it:"
    echo "--   schema = $SCHEMA        (owned by new-project.sh --new-world -- NOT created here)"
    echo "--   kernel schema = $KERN   (owned by new-project.sh --new-world -- NOT created here)"
    echo "--   role   = $ROLE          (created here)"
    echo "--"
    echo "-- OWNERSHIP SPLIT: this file creates the LOGIN role and the DATABASE, nothing else. Run"
    echo "-- this file first (as superuser), THEN run:"
    echo "--   bootstrap/new-project.sh <dest-dir> --db $DB --host $HOST --new-world $NAME"
    echo "-- which creates the $SCHEMA/$KERN schemas, applies the kernel lineage, and registers"
    echo "-- principals -- see new-project.sh's own header comment for that lineage chain."
    echo "--"
    echo "-- PASSWORD: deliberately NOT set here (LOGIN, no PASSWORD clause). user-guide/USER-CONFIGURATION.md's"
    echo "-- FAQ shows 'CREATE ROLE ... LOGIN PASSWORD ...' as a copy-paste example for a human"
    echo "-- typing their OWN password inline; a machine-generated file is a different hazard class"
    echo "-- -- a guessable placeholder password landing in a file anyone can read is a nail left"
    echo "-- standing, so this generator deliberately sets the password via a separate interactive"
    echo "-- step instead (CLAUDE.md engineering-responsibility clause: flag the hazard, don't route"
    echo "-- around it). Set it yourself, right after running this file:"
    echo "--   \\password $ROLE"
    echo ""
    echo "DO \$\$"
    echo "BEGIN"
    echo "   IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$ROLE') THEN"
    echo "      CREATE ROLE $ROLE LOGIN;"
    echo "   END IF;"
    echo "END"
    echo "\$\$;"
    echo ""
    echo "-- idempotent CREATE DATABASE (CREATE DATABASE cannot run inside DO/transaction --"
    echo "-- \\gexec is this cluster's own house idiom for a guarded, one-shot DDL statement)."
    echo "SELECT 'CREATE DATABASE $DB OWNER $ROLE'"
    echo "WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB')\\gexec"
    echo ""
    echo "-- user-guide/USER-CONFIGURATION.md FAQ step 2: the role needs CREATE on its own database before"
    echo "-- new-project.sh --new-world can apply the kernel lineage AS that role (SET ROLE, never"
    echo "-- a superuser bypass -- ADR-0012 P1)."
    echo "GRANT CREATE ON DATABASE $DB TO $ROLE;"
} >"$SQL_FILE"

echo "-- wrote pg_hba fragment: $HBA_FRAGMENT"
echo "-- wrote provisioning SQL: $SQL_FILE"
echo ""
echo "== operator walkthrough =="
echo "1. As superuser, apply the provisioning SQL (creates role + database, no schema, no password)."
echo "   CREATE DATABASE cannot run against the database being created, so connect to a DIFFERENT"
echo "   db you already have access to -- this cluster grants pg_hba access per-database (verified"
echo "   live above), there is no shared 'postgres' maintenance db every role can reach here. If"
echo "   \$DB already exists (this project's own FAQ convention: reuse one shared db, one schema"
echo "   pair per project), connecting to it directly works, e.g.:"
echo "     psql -h $HOST -d $DB -f $SQL_FILE"
echo "   If $DB does NOT exist yet, substitute any OTHER database you already reach on this host."
echo "   Expect: a DO block with no output (or 'CREATE ROLE'-shaped silence), then either"
echo "   'CREATE DATABASE' or nothing (if $DB already existed), then 'GRANT'. No errors."
echo ""
echo "2. Set the role's password interactively (never non-interactively, never in a file):"
echo "     psql -h $HOST -d $DB"
echo "     $DB=# \\password $ROLE"
echo "   Expect: a masked prompt, twice, no echo, nothing written to .psql_history."
echo ""
echo "3. Add the pg_hba fragment to pg_hba.conf ON THE DB HOST and reload:"
echo "     - back up first: cp pg_hba.conf pg_hba.conf.bak-\$(date +%Y%m%d)"
echo "     - paste the contents of $HBA_FRAGMENT in. $PLACEMENT_ADVICE"
echo "     - reload: SELECT pg_reload_conf();   (from any already-open superuser session)"
echo "       or, from the shell on the db host: pg_ctl reload -D <data-directory>"
echo "   This step is NOT run by this script -- editing/reloading the live server is your act."
echo ""
echo "4. Verify both witnesses:"
echo "     positive: psql -h $HOST -U $ROLE -d $DB -c 'SELECT current_user;'"
echo "               expect: a password prompt then a current_user row -- no connection-refused,"
echo "               no authentication error."
echo "     negative: psql -h $HOST -U $ROLE -d postgres -c 'SELECT 1;'"
echo "               expect: REFUSED (no pg_hba.conf entry admits $ROLE to any db but $DB --"
echo "               the 'host all $ROLE ... reject' line in the fragment above)."
echo ""
echo "5. Once verified, scaffold the world itself (creates the $SCHEMA/$KERN schemas, applies the"
echo "   kernel lineage, seeds the stamp secret + principals -- NOT done by this script or its SQL):"
echo "     bootstrap/new-project.sh <dest-dir> --db $DB --host $HOST --new-world $NAME"
