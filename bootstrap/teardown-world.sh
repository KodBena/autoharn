#!/bin/sh
# teardown-world.sh -- the scripted, witnessed teardown verb for a --new-world scratch scaffold
# (ledger work item scratch-world-teardown-verb, row 1624). Filed because the recipes author
# correctly REFUSED to hand-author DROP SCHEMA/ROLE prose-SQL on the shared toy host (written
# commission constraint + no sanctioned verb existed) -- leaving faqwit0718* objects on db toy
# for the maintainer's hand. This script is the sanctioned verb that refusal called for: never
# again does scratch cleanup route through prose SQL typed into a terminal.
#
# WHY TYPED CONFIRMATION HERE, WHEN THE APPLY-DELTA CEREMONY WAS RETIRED FOR BEING RITUAL
# (CLAUDE.md "Runs are strictly linear", maintainer ruling 2026-07-11): that ceremony was killed
# because it protected an action that could not actually go wrong for a non-expert operator
# (applying an already-vetted, idempotent kernel delta) -- the ceremony was pure friction with
# no matching hazard, so it was deleted rather than documented. THIS ceremony is load-bearing:
# DROP SCHEMA ... CASCADE and DROP ROLE are DESTRUCTIVE and IRREVERSIBLE (no undo, no soft
# delete, no recycle bin -- the ledger rows, review history, and every artifact inside the
# dropped schema are gone the instant the statement commits). A typed-confirmation step that
# guards an irreversible act against a fat-fingered world name is exactly the kind of paperwork
# CLAUDE.md's self-application section asks for: load-bearing safety, not cargo-cult sysadmin
# ritual. The two ceremonies look similar on the page; the hazard behind them is why one was
# deleted and the other exists.
#
# WHAT THIS MIRRORS (must match bootstrap/new-project.sh's --new-world derivation exactly, or
# teardown silently misses what creation actually built): --new-world <world> derives
# schema=<world>, kern=<world>_kernel, role=<world>_rw unless the scaffold call overrode one of
# those explicitly (bootstrap/new-project.sh lines ~182-189). This script defaults to the same
# derivation and accepts the same --schema/--kern/--role overrides for a world scaffolded with
# a non-default name, so teardown can mirror creation byte-for-byte even in the override case.
#
# Usage:
#   bootstrap/teardown-world.sh <world> --db <db> --host <host> \
#       [--schema <schema>] [--kern <kern>] [--role <role>] \
#       [--force-non-scratch] [--dir <path>]
#
#   <world>              the world name (e.g. faqwit0718). Checked against the scratch-safe
#                         pattern below before anything else happens.
#   --db, --host          the Postgres database/host to resolve and drop against (operator-named,
#                         never guessed or defaulted -- ADR-0002, same posture as every other
#                         bootstrap/ verb).
#   --schema/--kern/--role  override the derived names (default: <world>, <world>_kernel,
#                         <world>_rw -- see "WHAT THIS MIRRORS" above).
#   --force-non-scratch   required to proceed against a world name that does NOT match the
#                         scratch-safe pattern (see below). This flag lifts ONLY the pattern
#                         refusal -- the typed confirmation below still applies, and the
#                         autoharn1 refusal below is NEVER lifted by any flag.
#   --dir <path>          also remove this directory (the scaffolded deployment directory) after
#                         a successful teardown. Never inferred or guessed -- omit it and no
#                         directory is touched, no matter what <world> looks like.
#
# THE SCRATCH-SAFE PATTERN, derived from how scratch worlds are actually named in this repo's
# history (not invented fresh here):
#   - `run[0-9]*`        -- the throwaway run/probe worlds this project scaffolds for its own
#                            sessions (run3, run5, run7, run9, ... design/ORCH-* and BACKLOG.md
#                            passim; also covers derivatives like run3_kernel if ever passed
#                            directly).
#   - `s[0-9]*`           -- kernel-lineage-delta-named probe worlds (s20probe et al.,
#                            vestigial_documentation/design/MAINT-PG-HBA-HARDENING.md's own toy-host schema inventory).
#   - `faqwit*`           -- the FAQ-demo scratch-world family (user-guide/USER-RECIPES-FAQ.md's own
#                            `faqwit0718` walkthrough world -- THIS row's own cleanup target).
#   - `svcfx*`            -- the boundary-service fixture family (seen-red/boundary-service/
#                            run_fixtures.py's own RUN_SUFFIX = os.getpid() naming: svcfxpre<pid>,
#                            svcfxb<pid>, svcfxnocap<pid>, svcfxw7ok<pid>, ... -- i.e. a short
#                            alpha tag PID-suffixed at fixture-run time).
#   - `probeworld*`       -- the generic probe-world naming convention named alongside the above
#                            in this row's own commission text.
#   - `*_scratch`         -- README.md's own Configuration-table carve-out ("scratch-naming
#                            conventions ... or ending in `_scratch`"), the convention
#                            bootstrap/rehearse-from-origin.sh's own SCHEMA/KERN/ROLE derivation
#                            uses (rehearse_<suffix>_scratch, rehearse_<suffix>_kernel_scratch,
#                            rehearse_<suffix>_rw -- note the role does NOT end in `_scratch`,
#                            which is exactly why the pattern is checked against the WORLD name
#                            the operator types, not against each derived object name).
# A name matching none of these needs --force-non-scratch (plus the same typed confirmation
# below) to proceed -- the safe default is refusal, not a guess that an unfamiliar name is fine
# to drop (ADR-0002).
#
# THE autoharn1 REFUSAL IS UNCONDITIONAL: `autoharn1` is this deployment's own live ledger
# (CLAUDE.md's "row 1624" self-application context, and BACKLOG.md's own self-deployment-
# migrate-s36plus item names it as autoharn's live dev deployment). No flag -- not
# --force-non-scratch, nothing -- lifts this refusal. It is checked before the scratch-pattern
# check, before catalog resolution, before anything else this script does.
#
# WHAT THIS DOES, in order:
#   0. Refuse any derived/overridden schema, kernel, or role name containing a character outside
#      [A-Za-z0-9_] -- defense-in-depth ahead of the psql -v bind-variable queries below (row
#      1637: a crafted world name previously reached raw SQL-text interpolation here).
#   1. Refuse `autoharn1` unconditionally.
#   2. Refuse a non-scratch-safe name unless --force-non-scratch.
#   3. RESOLVE what exists for <schema>/<kern>/<role> by querying pg_namespace/pg_roles (never
#      assumed from the name alone).
#   4. Refuse if nothing resolved (teaching message -- there is nothing to tear down).
#   5. PRINT the exact enumerated drop plan (only the statements for objects that actually
#      exist).
#   6. Require the operator to TYPE THE WORLD NAME BACK exactly.
#   7. Execute EXACTLY the printed plan -- nothing discovered or dropped mid-flight.
#   8. VERIFY via a fresh catalog query that zero objects remain for this world. Nonzero exit
#      if residue is found.
#   9. If --dir was given, remove that directory (only then, only that exact path).
set -eu

usage() {
    echo "usage: $0 <world> --db <db> --host <host> [--schema <schema>] [--kern <kern>]" >&2
    echo "          [--role <role>] [--force-non-scratch] [--dir <path>]" >&2
    echo "       (reads the world name to type back from stdin; run interactively, or pipe" >&2
    echo "        \`echo '<world>' | $0 ...\` for a scripted/witnessed invocation)" >&2
    exit 2
}

[ $# -ge 1 ] || usage
WORLD="$1"; shift
DB=""; HOST=""
SCHEMA=""; KERN=""; ROLE=""
FORCE_NON_SCRATCH=0
DIR=""
while [ $# -gt 0 ]; do
    case "$1" in
        --db) DB="$2"; shift 2 ;;
        --host) HOST="$2"; shift 2 ;;
        --schema) SCHEMA="$2"; shift 2 ;;
        --kern) KERN="$2"; shift 2 ;;
        --role) ROLE="$2"; shift 2 ;;
        --force-non-scratch) FORCE_NON_SCRATCH=1; shift ;;
        --dir) DIR="$2"; shift 2 ;;
        *) echo "teardown-world.sh: unrecognized argument: $1" >&2; usage ;;
    esac
done
[ -n "$DB" ] && [ -n "$HOST" ] || usage
[ -n "$WORLD" ] || usage

[ -n "$SCHEMA" ] || SCHEMA="$WORLD"
[ -n "$KERN" ] || KERN="${WORLD}_kernel"
[ -n "$ROLE" ] || ROLE="${WORLD}_rw"

# --- 0. STRICT CHARACTER ALLOWLIST on every name that becomes SQL text -------------------------
# Defense-in-depth alongside the psql -v bind-variable interpolation used below (see RESOLVE and
# execute steps): SCHEMA/KERN/ROLE reach DROP SCHEMA/DROP ROLE as quoted *identifiers*, and an
# identifier-quoted string is not injectable, but a name outside this allowlist is not a name any
# real scaffold call produces either (--new-world derivation or a hand-picked --schema/--kern/
# --role override) -- refusing early keeps this script's own catalog/DROP text boring and
# reviewable, independent of how well psql's quoting holds up. Checked for all three, since
# --schema/--kern/--role are operator-supplied overrides with no other check on them.
for _name in "$SCHEMA" "$KERN" "$ROLE"; do
    case "$_name" in
        ''|*[!A-Za-z0-9_]*)
            echo "teardown-world.sh: REFUSED -- '$_name' contains characters outside the" >&2
            echo "                   allowlist for a schema/kernel/role name (letters, digits," >&2
            echo "                   underscore only). This applies to derived names and to" >&2
            echo "                   --schema/--kern/--role overrides alike. Nothing touched." >&2
            exit 1
            ;;
    esac
done
unset _name

# --- 1. THE UNCONDITIONAL autoharn1 REFUSAL -- checked first, no flag overrides it -------------
if [ "$WORLD" = "autoharn1" ]; then
    echo "teardown-world.sh: REFUSED -- 'autoharn1' is this deployment's own live ledger, not a" >&2
    echo "                   scratch world. This refusal is unconditional: no flag, including" >&2
    echo "                   --force-non-scratch, overrides it. Nothing touched." >&2
    exit 1
fi

# --- 2. the scratch-safe pattern -----------------------------------------------------------------
SCRATCH_SAFE=0
case "$WORLD" in
    run[0-9]*|s[0-9]*|faqwit*|svcfx*|probeworld*|*_scratch) SCRATCH_SAFE=1 ;;
esac
if [ "$SCRATCH_SAFE" -ne 1 ]; then
    if [ "$FORCE_NON_SCRATCH" -ne 1 ]; then
        echo "teardown-world.sh: REFUSED -- '$WORLD' does not match the scratch-safe naming" >&2
        echo "                   pattern this verb recognizes (run[0-9]*, s[0-9]*, faqwit*," >&2
        echo "                   svcfx*, probeworld*, *_scratch -- see this script's own header" >&2
        echo "                   comment for where each of these comes from in this repo's" >&2
        echo "                   history). Dropping a name outside that pattern needs" >&2
        echo "                   --force-non-scratch (plus the same typed confirmation every" >&2
        echo "                   teardown requires) -- the default is refusal, not a guess that" >&2
        echo "                   an unfamiliar name is safe to drop. Nothing touched." >&2
        exit 1
    fi
    echo "-- --force-non-scratch: '$WORLD' does not match the scratch-safe pattern, proceeding anyway --"
fi

# --- 3. RESOLVE what exists, by querying the catalogs, never assumed from the name alone --------
PGPASSWORD="${PGPASSWORD:-}"
_psql() { PGPASSWORD="$PGPASSWORD" psql -h "$HOST" -d "$DB" ${PGUSER:+-U "$PGUSER"} "$@"; }
# SQL text is always fed on stdin, never via -c: psql's :'var' / :"var" bind-variable
# interpolation (verified live against a real server, psql 18.3) is only performed for input it
# parses as a script -- stdin or -f -- and is a silent no-op under -c (the string reaches the
# server with the literal colon still in it and errors out). _psql_in wraps that stdin-piping
# discipline once so every call site below gets the working form of the fix, not the broken one.
_psql_in() { printf '%s\n' "$1"; }

# Bound as psql -v variables, never interpolated as raw shell text into the SQL string: :'var'
# has psql itself substitute a properly-escaped SQL string literal client-side, before the query
# ever reaches the server, so no crafted name can smuggle a second statement past the semicolon
# in the query text below (the RESOLVE-stage injection this whole block was rewritten to close).
HAVE_SCHEMA=$(_psql_in "SELECT count(*) FROM pg_namespace WHERE nspname = :'schema';" | _psql -v schema="$SCHEMA" -tA)
HAVE_KERN=$(_psql_in "SELECT count(*) FROM pg_namespace WHERE nspname = :'kern';" | _psql -v kern="$KERN" -tA)
HAVE_ROLE=$(_psql_in "SELECT count(*) FROM pg_roles WHERE rolname = :'role';" | _psql -v role="$ROLE" -tA)

if [ "$HAVE_SCHEMA" = "0" ] && [ "$HAVE_KERN" = "0" ] && [ "$HAVE_ROLE" = "0" ]; then
    echo "teardown-world.sh: REFUSED -- '$WORLD' resolves to NOTHING in $DB@$HOST: no schema" >&2
    echo "                   '$SCHEMA', no kernel schema '$KERN', no role '$ROLE'. Either it was" >&2
    echo "                   already torn down, it was never scaffolded under this derivation," >&2
    echo "                   or --schema/--kern/--role need to be given explicitly to match a" >&2
    echo "                   non-default scaffold call. Nothing to do; nothing touched." >&2
    exit 1
fi

# --- 4. PRINT the exact enumerated drop plan (only what actually resolved) ----------------------
echo "== teardown-world.sh: drop plan for '$WORLD' in $DB@$HOST =="
PLAN_N=0
if [ "$HAVE_SCHEMA" != "0" ]; then
    PLAN_N=$((PLAN_N + 1))
    echo "  $PLAN_N. DROP SCHEMA ${SCHEMA} CASCADE;   -- ledger schema (exists)"
fi
if [ "$HAVE_KERN" != "0" ]; then
    PLAN_N=$((PLAN_N + 1))
    echo "  $PLAN_N. DROP SCHEMA ${KERN} CASCADE;   -- kernel schema (exists)"
fi
if [ "$HAVE_ROLE" != "0" ]; then
    PLAN_N=$((PLAN_N + 1))
    echo "  $PLAN_N. DROP ROLE ${ROLE};   -- granted role (exists)"
fi
if [ -n "$DIR" ]; then
    echo "  +. rm -rf ${DIR}   -- scaffolded deployment directory (--dir given explicitly)"
fi
echo "Exactly the $PLAN_N statement(s) above will run. Nothing else is discovered mid-flight."

# --- 5. typed confirmation -- load-bearing (see header comment), not bypassable by any flag -----
echo ""
printf "Type the world name (%s) to proceed: " "$WORLD"
read -r ans
if [ "$ans" != "$WORLD" ]; then
    echo "teardown-world.sh: confirmation did not match '$WORLD' -- nothing touched." >&2
    exit 1
fi

# --- 6. execute EXACTLY the printed plan ---------------------------------------------------------
# Same psql -v binding discipline as RESOLVE above, but with :"var" (double-quoted-identifier
# substitution) rather than :'var' (string-literal substitution): SCHEMA/KERN/ROLE name objects
# here, not string values, and psql escapes embedded double-quotes/backslashes in an identifier
# bind the same safe way it escapes a literal bind -- no raw shell interpolation into the SQL text
# either way. The allowlist check above already restricts these to [A-Za-z0-9_]+, so this is
# belt-and-suspenders against the same class of hazard the RESOLVE-stage fix closes.
echo "-- executing --"
if [ "$HAVE_SCHEMA" != "0" ]; then
    # the ledger schema this entire script exists to tear down; blast radius (everything inside
    # $SCHEMA) is exactly what the printed plan above named and the typed confirmation covered.
    # declared-drop: SCHEMA
    _psql_in 'DROP SCHEMA :"schema" CASCADE;' | _psql -v ON_ERROR_STOP=1 -v schema="$SCHEMA" -q
    echo "   dropped schema ${SCHEMA}"
fi
if [ "$HAVE_KERN" != "0" ]; then
    # the kernel schema paired with $SCHEMA above; same declared blast radius, printed in the
    # same plan, confirmed by the same typed world-name check.
    # declared-drop: KERN
    _psql_in 'DROP SCHEMA :"kern" CASCADE;' | _psql -v ON_ERROR_STOP=1 -v kern="$KERN" -q
    echo "   dropped schema ${KERN}"
fi
if [ "$HAVE_ROLE" != "0" ]; then
    _psql_in 'DROP ROLE :"role";' | _psql -v ON_ERROR_STOP=1 -v role="$ROLE" -q
    echo "   dropped role ${ROLE}"
fi

# --- 7. VERIFY zero residue via a fresh catalog query --------------------------------------------
# Same -v bind-variable discipline as RESOLVE (step 3) -- no raw interpolation here either.
RESIDUE_SCHEMA=$(_psql_in "SELECT count(*) FROM pg_namespace WHERE nspname = :'schema';" | _psql -v schema="$SCHEMA" -tA)
RESIDUE_KERN=$(_psql_in "SELECT count(*) FROM pg_namespace WHERE nspname = :'kern';" | _psql -v kern="$KERN" -tA)
RESIDUE_ROLE=$(_psql_in "SELECT count(*) FROM pg_roles WHERE rolname = :'role';" | _psql -v role="$ROLE" -tA)
if [ "$RESIDUE_SCHEMA" != "0" ] || [ "$RESIDUE_KERN" != "0" ] || [ "$RESIDUE_ROLE" != "0" ]; then
    echo "teardown-world.sh: RESIDUE DETECTED after teardown -- schema='$RESIDUE_SCHEMA'" >&2
    echo "                   kern='$RESIDUE_KERN' role='$RESIDUE_ROLE' (counts, expect all 0)." >&2
    echo "                   The drop plan executed but the catalogs still show objects for" >&2
    echo "                   '$WORLD'. Investigate by hand before re-running -- this is a" >&2
    echo "                   loud failure, not a silent partial success." >&2
    exit 1
fi
echo "-- verified: zero residue for '$WORLD' in $DB@$HOST --"

# --- 8. the deployment directory, only when --dir was given explicitly --------------------------
if [ -n "$DIR" ]; then
    rm -rf "$DIR"
    echo "-- removed deployment directory $DIR --"
fi

echo "== teardown-world.sh: '$WORLD' torn down, zero residue verified =="
