#!/bin/sh
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T11:15:53Z
#   last-change: 2026-07-09T13:50:03Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

# new-project.sh — stamp a new instance directory: deployment.json, .claude/ wiring
# (settings.json, governed_files.json, apparatus.json, HOOKS.md), and the three portable verbs
# (led, judge, pickup) — instantiated from bootstrap/templates/ with this project's deployment
# values substituted in (design/OPUS-READINESS.md move 2: scaffold, not clone — the
# template/instance split made physical).
#
# Usage:
#   bootstrap/new-project.sh <dest-dir> --db <db> --host <host> --schema <schema> \
#       --kern <kern> --role <role> [--name <project-name>] [--force]
#
#   <dest-dir>   where to stamp the new instance (created if missing).
#   --db         the ledger's database name.
#   --host       the postgres host this project's ledger lives on.
#   --schema     the ledger schema (e.g. "toycolors").
#   --kern       the kernel schema (e.g. "toycolors_kernel").
#   --role       the granted subject role led/judge/pickup connect as (e.g. "toycolors_rw").
#   --name       this project's own identifier, used ONLY as the target-name argument `judge`
#                passes to autoharn's engine/ledger_differential.py (and hence the derivations/
#                banking subdirectory under autoharn's own tree) — default: <dest-dir>'s basename.
#                Pick something that will NOT collide with autoharn engine/targets.py's curated
#                registry names (toy, nla, e15-e18) or its scratch-naming conventions
#                (^s\d+[a-z]*$, *_scratch), or `judge` will resolve to the WRONG target.
#   --force      overwrite an existing deployment.json/scaffold at <dest-dir> (default: refuse).
#
# --new-world <world> mode (BACKLOG "Ruling: one world per run", 2026-07-09; this session's
# batch item 7): a run's subject must not see a sibling run's ledger history (the many-worlds
# argument -- branches share only the branch point, never each other's ledgers). This mode
# stands up exactly that branch point in an EXISTING db, in one call: applies
# kernel/lineage/high_watermark_1.sql THEN kernel/lineage/s20-obligation-grants-and-view-
# refresh.sql THEN kernel/lineage/s21-session-aware-distinctness.sql (RATIFIED, BACKLOG.md
# 2026-07-09 -- so every new world is born on the current kernel, s20 AND s21 included, never
# the pre-s20 grants-gap shape the toy pilot found the hard way, and never the session-blind
# distinctness s21 fixes) into fresh schemas derived from <world> (e.g. --new-world run3 ->
# schema=run3, kern=run3_kernel, role=run3_rw -- override any
# of the three with an explicit --schema/--kern/--role if the naming convention does not fit),
# seeds the stamp secret (openssl rand -hex 32, mirroring drive/arm.sh ruling 43's own idempotent
# pattern -- skipped if a secret already exists, never silently rotated), and writes the matching
# deployment.json -- the operator step HOOKS.md documents as a manual "one manual step remains"
# for a HAND-scaffolded project is fully automated here for a probe/run world. EVERY -v var is
# still spelled out explicitly to psql (standing rule: never apply bare against a deployment that
# matters) -- --new-world does not relax that, it only derives the VALUES from one name instead
# of requiring the caller to keep schema/kern/role in agreement by hand (ADR-0012 P1). The
# 'author' principal is seeded automatically by s15-schema.sql itself (INSERT ... ON CONFLICT DO
# NOTHING, mapped to the connecting role) -- no separate registration step is needed here; it
# mirrors the toy WALKTHROUGH's own kernel-apply step exactly, nothing new to invoke.
#
# What this does NOT do (deliberately, per design/OPUS-READINESS.md's scope for this pass):
# rewire `led` to READ deployment.json live (deferred; a live session reads it per-event; the two
# PreToolUse hooks in hooks/ already do, per this same session's items 2-3), or apply any kernel
# DDL to a deployment that is NOT a --new-world target (a separate, explicit -v-vars operator act).
set -eu

# Captured BEFORE any argument parsing consumes "$@", so the PROVENANCE header this script writes
# into .claude/HOOKS.md (below) records the operator's ACTUAL invocation, not a reconstruction —
# closing exactly the gap the maintainer flagged for run3 ("an operator cannot create world N
# without reading script source" / "how was run3 created? that of course needs to be documented",
# 2026-07-09): no future world should be born without this line writing itself (ADR-0012 P1 --
# one source, the real argv, not a hand-typed guess reconstructed after the fact).
CREATE_CMD="$0"
for _a in "$@"; do
    case "$_a" in
        *[\ \	]*) CREATE_CMD="$CREATE_CMD '$_a'" ;;
        *) CREATE_CMD="$CREATE_CMD $_a" ;;
    esac
done
CREATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

usage() {
    echo "usage: $0 <dest-dir> --db <db> --host <host> --schema <schema> --kern <kern> --role <role> [--name <name>] [--force]" >&2
    echo "       $0 <dest-dir> --new-world <world> --db <db> --host <host> [--name <name>] [--force]" >&2
    echo "         (--new-world derives --schema/--kern/--role from <world> unless given explicitly;" >&2
    echo "          also applies high_watermark_1.sql + s20 + s21 and seeds the stamp secret -- see" >&2
    echo "          the --new-world block in this script's own header comment)" >&2
    exit 2
}

[ $# -ge 1 ] || usage
DEST="$1"; shift
NAME=""
FORCE=0
NEW_WORLD=""
DB=""; HOST=""; SCHEMA=""; KERN=""; ROLE=""
while [ $# -gt 0 ]; do
    case "$1" in
        --db) DB="$2"; shift 2 ;;
        --host) HOST="$2"; shift 2 ;;
        --schema) SCHEMA="$2"; shift 2 ;;
        --kern) KERN="$2"; shift 2 ;;
        --role) ROLE="$2"; shift 2 ;;
        --name) NAME="$2"; shift 2 ;;
        --new-world) NEW_WORLD="$2"; shift 2 ;;
        --force) FORCE=1; shift ;;
        *) echo "unrecognized argument: $1" >&2; usage ;;
    esac
done
if [ -n "$NEW_WORLD" ]; then
    # Derive, never require, the three names that must agree (P1: one source -- the world name --
    # not three hand-typed strings the caller must keep in sync). An explicit --schema/--kern/--role
    # still wins if the caller passed one (e.g. the world name collides with an existing schema).
    [ -n "$SCHEMA" ] || SCHEMA="$NEW_WORLD"
    [ -n "$KERN" ] || KERN="${NEW_WORLD}_kernel"
    [ -n "$ROLE" ] || ROLE="${NEW_WORLD}_rw"
fi
[ -n "$DB" ] && [ -n "$HOST" ] && [ -n "$SCHEMA" ] && [ -n "$KERN" ] && [ -n "$ROLE" ] || usage

# LINEAGE_CHAIN: what kernel DDL THIS scaffold run applied (or didn't), for the PROVENANCE header
# below -- the honest record of which sNN deltas this world was born on, so a future reader never
# has to reconstruct it from source the way run3's own history had to be reconstructed.
if [ -n "$NEW_WORLD" ]; then
    LINEAGE_CHAIN="s15 -> s17-stamp-mechanism -> s17-independence-vocabulary -> s19 -> s20 -> s21-session-aware-distinctness (via kernel/lineage/high_watermark_1.sql + kernel/lineage/s20-obligation-grants-and-view-refresh.sql + kernel/lineage/s21-session-aware-distinctness.sql), applied automatically by this --new-world run"
    # --new-world ALSO auto-seeds the stamp secret (below) -- HOOKS.md must say so, not repeat the
    # generic "one manual step remains" text verbatim: an operator who trusted that stale claim and
    # re-ran the seeding block would TRUNCATE + re-INSERT an already-provisioned secret, ROTATING it
    # and invalidating every stamp already written under it (the exact hazard the block's own
    # comment warns against). Fixed here rather than left for the next reader to trip over.
    STAMP_SECRET_STATUS="**Already provisioned automatically by this --new-world scaffold run (see PROVENANCE above) — do NOT re-run the block below; re-seeding ROTATES the secret and invalidates every stamp already written under it. Shown for reference/recovery only.**"
    # s21 is now part of THIS world's birth lineage (line above) -- the template's own s21 status
    # bullet must say so, not the stale "NOT applied by any scaffold mode" claim (BACKLOG 2026-07-09,
    # "make the s21-and-future-delta apply step scriptable" mandate, piece 2).
    S21_STATUS="Applied automatically by this --new-world scaffold run (see the lineage chain above) -- this world's kernel already carries s21's (stamp_session, stamp_agent) pair-keyed distinctness and the s19 residue fix. No separate apply is needed."
else
    LINEAGE_CHAIN="NOT applied by this scaffold run -- apply a kernel lineage to $SCHEMA/$KERN/$ROLE manually (kernel/lineage/, see kernel/lineage/README.md) before first use"
    STAMP_SECRET_STATUS="**One manual step remains: provision the stamp secret. UNWITNESSED — the block below has not been run in this instance.**"
    S21_STATUS="NOT applied by this scaffold run (classic --schema/--kern/--role mode applies no kernel lineage at all -- see item 1 above). If this world's kernel predates s21, apply it as a separate, explicit operator act from autoharn's own checkout: \`bootstrap/apply-delta.sh <this-project's-directory> kernel/lineage/s21-session-aware-distinctness.sql\` (prints the resolved command, requires a typed schema confirmation, never applies bare) -- status/witness live in autoharn's BACKLOG.md (search \"s21\")."
fi

AUTOHARN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES="$AUTOHARN_ROOT/bootstrap/templates"
PY="$HOME/w/vdc/venvs/generic/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"

mkdir -p "$DEST"
PROJECT_ROOT="$(cd "$DEST" && pwd)"
[ -n "$NAME" ] || NAME="$(basename "$PROJECT_ROOT")"

DEPLOYMENT="$PROJECT_ROOT/deployment.json"
if [ -f "$DEPLOYMENT" ] && [ "$FORCE" -ne 1 ]; then
    echo "new-project.sh: $DEPLOYMENT already exists -- refusing to overwrite (pass --force to replace it)." >&2
    exit 1
fi

echo "== stamping instance at $PROJECT_ROOT (name=$NAME) =="

if [ -n "$NEW_WORLD" ]; then
    echo "-- new-world '$NEW_WORLD': applying high_watermark_1.sql + s20 + s21 to $DB (schema=$SCHEMA kern=$KERN role=$ROLE) --"
    psql -h "$HOST" -d "$DB" -v ON_ERROR_STOP=1 \
        -v schema="$SCHEMA" -v kern="$KERN" -v role="$ROLE" \
        -f "$AUTOHARN_ROOT/kernel/lineage/high_watermark_1.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s20-obligation-grants-and-view-refresh.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s21-session-aware-distinctness.sql"
    echo "   kernel applied (schema $SCHEMA + kernel schema $KERN + role $ROLE, s20 + s21 included)"

    echo "-- new-world '$NEW_WORLD': seeding the stamp secret (idempotent, mirrors drive/arm.sh ruling 43) --"
    mkdir -p "$PROJECT_ROOT/.claude/secrets"
    chmod 700 "$PROJECT_ROOT/.claude/secrets"
    SECRET_FILE="$PROJECT_ROOT/.claude/secrets/stamp_secret.hex"
    HAVE=$(psql -h "$HOST" -d "$DB" -tAc "SELECT count(*) FROM ${KERN}.stamp_secret;")
    if [ "$HAVE" = "1" ]; then
        echo "   a secret is already provisioned for ${KERN}.stamp_secret (1 row); not rotating"
    else
        ( umask 077; openssl rand -hex 32 > "$SECRET_FILE" )
        chmod 600 "$SECRET_FILE"
        HEX=$(cat "$SECRET_FILE")
        # psql -c does NOT interpolate -v vars; the hex is [0-9a-f] so it inlines safely (no
        # injection surface) -- same posture as drive/arm.sh's identical seeding block.
        psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 \
            -c "TRUNCATE ${KERN}.stamp_secret;" \
            -c "INSERT INTO ${KERN}.stamp_secret (secret) VALUES (decode('$HEX','hex'));"
        echo "   one fresh secret provisioned ($SECRET_FILE [chmod 600]; DB ${KERN}.stamp_secret)"
    fi
fi

echo "-- deployment.json --"
"$PY" - "$DEPLOYMENT" "$DB" "$HOST" "$SCHEMA" "$KERN" "$ROLE" <<PYEOF
import sys
sys.path.insert(0, "$AUTOHARN_ROOT/filing")
from deployment_record import DeploymentRecord, write_deployment

path, db, host, schema, kern, role = sys.argv[1:7]
write_deployment(path, DeploymentRecord(db=db, host=host, schema=schema, kern=kern, role=role))
print(f"wrote {path}")
PYEOF

mkdir -p "$PROJECT_ROOT/.claude/logs" "$PROJECT_ROOT/.claude/secrets"
chmod 700 "$PROJECT_ROOT/.claude/secrets"

# sed substitution table, shared by every template below. `|` delimiter (paths contain `/`).
sedsubst() {
    sed \
        -e "s|__DB__|$DB|g" \
        -e "s|__HOST__|$HOST|g" \
        -e "s|__SCHEMA__|$SCHEMA|g" \
        -e "s|__KERN__|$KERN|g" \
        -e "s|__ROLE__|$ROLE|g" \
        -e "s|__PROJECT_ROOT__|$PROJECT_ROOT|g" \
        -e "s|__PROJECT_NAME__|$NAME|g" \
        -e "s|__AUTOHARN_ROOT__|$AUTOHARN_ROOT|g" \
        -e "s|__CREATED_AT__|$CREATED_AT|g" \
        -e "s|__CREATE_CMD__|$CREATE_CMD|g" \
        -e "s|__LINEAGE_CHAIN__|$LINEAGE_CHAIN|g" \
        -e "s|__STAMP_SECRET_STATUS__|$STAMP_SECRET_STATUS|g" \
        -e "s|__S21_STATUS__|$S21_STATUS|g"
}

echo "-- .claude/ wiring --"
sedsubst < "$TEMPLATES/settings.json.tmpl" > "$PROJECT_ROOT/.claude/settings.json"
cp "$TEMPLATES/governed_files.json" "$PROJECT_ROOT/.claude/governed_files.json"
cp "$TEMPLATES/GOVERNED_FILES.md" "$PROJECT_ROOT/.claude/GOVERNED_FILES.md"
cp "$TEMPLATES/apparatus.json" "$PROJECT_ROOT/.claude/apparatus.json"
cp "$TEMPLATES/APPARATUS.md" "$PROJECT_ROOT/.claude/APPARATUS.md"
sedsubst < "$TEMPLATES/HOOKS.md.tmpl" > "$PROJECT_ROOT/.claude/HOOKS.md"
echo "wrote .claude/settings.json, governed_files.json, GOVERNED_FILES.md, apparatus.json, APPARATUS.md, HOOKS.md"

echo "-- the three verbs (led, judge, pickup) --"
for verb in led judge pickup; do
    sedsubst < "$TEMPLATES/$verb.tmpl" > "$PROJECT_ROOT/$verb"
    chmod +x "$PROJECT_ROOT/$verb"
    echo "wrote $verb (executable)"
done

echo "== done =="
echo "Next steps:"
if [ -n "$NEW_WORLD" ]; then
    echo "  1. Kernel + s20 + s21 already applied and the stamp secret already provisioned above (new-world '$NEW_WORLD')."
    echo "  2. cd $PROJECT_ROOT && ./led decision \"...\"  /  ./judge  /  ./pickup"
    echo "  3. Read $PROJECT_ROOT/.claude/HOOKS.md and replace its UNWITNESSED marks as you exercise each command."
else
    echo "  1. Apply a kernel lineage to $DB/$SCHEMA/$KERN/$ROLE if not already applied (kernel/lineage/, autoharn)."
    echo "  2. Provision the stamp secret -- see $PROJECT_ROOT/.claude/HOOKS.md (marked UNWITNESSED until you run it)."
    echo "  3. cd $PROJECT_ROOT && ./led decision \"...\"  /  ./judge  /  ./pickup"
    echo "  4. Read $PROJECT_ROOT/.claude/HOOKS.md and replace its UNWITNESSED marks as you exercise each command."
fi
