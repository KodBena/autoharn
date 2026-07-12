#!/bin/sh
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T11:15:53Z
#   last-change: 2026-07-11T22:38:33Z
#   contributors: be693afb/main, e4410ef6/main
# <<< PROVENANCE-STAMP <<<

# new-project.sh — stamp a new instance directory: deployment.json, .claude/ wiring
# (settings.json, governed_files.json, apparatus.json, HOOKS.md), and the three verbs (led, judge,
# pickup) as thin shims exec'ing bootstrap/templates/*.tmpl LIVE out of this autoharn checkout
# (design/ORCH-OPUS-READINESS.md move 2's template/instance split, then BACKLOG maintainer ruling
# 2026-07-11 "runs are strictly linear" disposition 6 "live verbs": the verbs stopped being
# sed-substituted frozen copies — a template fix here now reaches every already-scaffolded world
# instantly, matching how the two PreToolUse hooks already execute live per invocation). Only
# deployment.json and the .claude/ wiring stay scaffold-written, per-world config.
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
#   --name       this project's own identifier, written into deployment.json's `name` field and
#                read live from there by the scaffolded `./judge` shim as the target-name argument
#                to autoharn's engine/ledger_differential.py (and hence the derivations/ banking
#                subdirectory under autoharn's own tree) — default: <dest-dir>'s basename. Pick
#                something that will NOT collide with autoharn engine/targets.py's curated
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
# --new-world ALSO registers the 'reviewer' principal (subagent class, ON CONFLICT DO NOTHING)
# and writes the world's root CLAUDE.md (the templated governance preamble, auto-loaded by
# Claude Code at session start -- no separate read-me-first or paste step) -- BACKLOG
# "Maintainer ruling: self-application" (2026-07-09) named BOTH the hand-registered reviewer
# principal and the hand-pasted six-point governance prompt as the ceremony "starting a run
# becomes a verb" is meant to close; this closes it, so a --new-world scaffold is run-ready at
# birth instead of needing two more hand steps before the first real session (ratifier's
# acceptance bar, same date: at most one scaffold command, one `cd`, one `claude`, no paste).
#
# What this does NOT do: apply any kernel DDL to a deployment that is NOT a --new-world target (a
# separate, explicit -v-vars operator act). (Historical note: an earlier version of this comment
# named "rewire led to read deployment.json live" as future work — that landed 2026-07-11, "live
# verbs" above; led/judge/pickup all read deployment.json live now, same as the PreToolUse hooks
# always have.)
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
    LINEAGE_CHAIN="s15 -> s17-stamp-mechanism -> s17-independence-vocabulary -> s19 -> s20 -> s21-session-aware-distinctness -> s22-work-item-ledger -> s23-per-invocation-stamp-token -> s24-declared-event-time -> s25-commission-kind -> s26-row-hash-chain (via kernel/lineage/high_watermark_1.sql + kernel/lineage/s20-obligation-grants-and-view-refresh.sql + kernel/lineage/s21-session-aware-distinctness.sql + kernel/lineage/s22-work-item-ledger.sql + kernel/lineage/s23-per-invocation-stamp-token.sql + kernel/lineage/s24-declared-event-time.sql + kernel/lineage/s25-commission-kind.sql + kernel/lineage/s26-row-hash-chain.sql), applied automatically by this --new-world run"
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
    # REVIEWER_STATUS: mirrors the STAMP_SECRET_STATUS/S21_STATUS pattern above -- the honest,
    # mode-aware record of whether the `reviewer` principal this world's root CLAUDE.md.tmpl talks
    # about ("a reviewer principal exists") is actually true yet (BACKLOG "Maintainer ruling:
    # self-application", 2026-07-09 -- "starting a run becomes a verb": the operator no longer
    # hand-registers this principal for a --new-world scaffold).
    REVIEWER_STATUS="Registered automatically by this --new-world scaffold run (principal 'reviewer', class subagent; see the registration step in this same run, right after the stamp secret above) -- do NOT re-register; \`ON CONFLICT (name) DO NOTHING\` makes a repeat call harmless if you do anyway."
    # COMMISSIONER_STATUS: mirrors REVIEWER_STATUS exactly -- the honest, mode-aware record of
    # whether the 'commissioner' principal (kernel/lineage/s25-commission-kind.sql's FULL signing
    # mode; BACKLOG "Five-item batch, maintainer-approved 2026-07-11 evening", item 2) exists yet.
    # Registering it here, alongside 'reviewer', means the maintainer's OWN signing act (see the
    # printed copy-paste line at the end of this script) never has to register its own principal
    # first -- the same "starting a run becomes a verb" closure REVIEWER_STATUS already documents.
    COMMISSIONER_STATUS="Registered automatically by this --new-world scaffold run (principal 'commissioner', class human; see the registration step in this same run, right after 'reviewer' above) -- do NOT re-register; \`ON CONFLICT (name) DO NOTHING\` makes a repeat call harmless if you do anyway. FULL-mode signing (the maintainer signs the ask himself): \`LED_ACTOR=commissioner ./led commission \"<the ask verbatim>\"\` -- typed by the maintainer in his OWN terminal, inside this world. LAZY-mode (the implementer vicariously transcribes the ask on receiving it, first ledger act, no commissioner guarantee): see this world's CLAUDE.md preamble."
else
    LINEAGE_CHAIN="NOT applied by this scaffold run -- apply a kernel lineage to $SCHEMA/$KERN/$ROLE manually (kernel/lineage/, see kernel/lineage/README.md) before first use"
    STAMP_SECRET_STATUS="**One manual step remains: provision the stamp secret. UNWITNESSED — the block below has not been run in this instance.**"
    S21_STATUS="NOT applied by this scaffold run (classic --schema/--kern/--role mode applies no kernel lineage at all -- see item 1 above). If this world's kernel predates s21, apply it as a separate, explicit operator act from autoharn's own checkout: \`bootstrap/apply-delta.sh <this-project's-directory> kernel/lineage/s21-session-aware-distinctness.sql\` (prints the resolved command, requires a typed schema confirmation, never applies bare) -- status/witness live in autoharn's BACKLOG.md (search \"s21\")."
    REVIEWER_STATUS="NOT registered by this scaffold run (classic --schema/--kern/--role mode applies no kernel lineage at all -- see item 1 above, so there is no \`principal\` table yet to register into). Once a kernel lineage is applied, register one explicitly: \`./led register-principal reviewer subagent\`."
    COMMISSIONER_STATUS="NOT registered by this scaffold run (classic --schema/--kern/--role mode applies no kernel lineage at all -- see item 1 above). Once a kernel lineage carrying kernel/lineage/s25-commission-kind.sql is applied, register one explicitly: \`./led register-principal commissioner human\`."
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
    echo "-- new-world '$NEW_WORLD': applying high_watermark_1.sql + s20 + s21 + s22 + s23 + s24 + s25 to $DB (schema=$SCHEMA kern=$KERN role=$ROLE) --"
    psql -h "$HOST" -d "$DB" -v ON_ERROR_STOP=1 \
        -v schema="$SCHEMA" -v kern="$KERN" -v role="$ROLE" \
        -f "$AUTOHARN_ROOT/kernel/lineage/high_watermark_1.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s20-obligation-grants-and-view-refresh.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s21-session-aware-distinctness.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s22-work-item-ledger.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s23-per-invocation-stamp-token.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s24-declared-event-time.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s25-commission-kind.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s26-row-hash-chain.sql"
    echo "   kernel applied (schema $SCHEMA + kernel schema $KERN + role $ROLE, s20 + s21 + s22 + s23 + s24 + s25 + s26 included)"

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

    # GENESIS SEED (design/MAINT-GPG-TRUST-LAYER.md Rung 3; kernel/lineage/s26-row-hash-chain.sql):
    # the row_hash chain's zz_set_row_hash trigger REFUSES the first ledger INSERT loudly if no
    # seed is provisioned (see that delta's own header) -- this MUST run before the first write,
    # same ordering constraint as the stamp secret above. Idempotent (INSERT ... ON CONFLICT DO
    # NOTHING via the only_one PK, mirroring stamp_secret's own one-row-table shape) -- but unlike
    # the stamp secret, this is NOT a secret (kernel/lineage/s26-row-hash-chain.sql's GENESIS SEED
    # section explains why: its only job is making two worlds' row-1 hashes differ, not
    # confidentiality), so it is generated and inserted directly, with no on-disk file mirroring
    # the stamp-secret pattern's chmod-600 ceremony -- there is nothing here that needs hiding.
    echo "-- new-world '$NEW_WORLD': seeding the row_hash chain's genesis seed (idempotent) --"
    HAVE_GENESIS=$(psql -h "$HOST" -d "$DB" -tAc "SELECT count(*) FROM ${KERN}.chain_genesis;" 2>/dev/null || echo "0")
    if [ "$HAVE_GENESIS" = "1" ]; then
        echo "   a genesis seed is already provisioned for ${KERN}.chain_genesis (1 row); not rotating"
    elif [ "$HAVE_GENESIS" = "0" ]; then
        GENESIS_HEX=$(openssl rand -hex 32)
        psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 \
            -c "INSERT INTO ${KERN}.chain_genesis (seed) VALUES ('$GENESIS_HEX') ON CONFLICT (only_one) DO NOTHING;"
        echo "   one fresh genesis seed provisioned (DB ${KERN}.chain_genesis)"
    else
        echo "   ${KERN}.chain_genesis does not exist -- this world's kernel predates s26-row-hash-chain.sql; skipping (not an error, an older lineage)"
    fi

    # Register the standard principals this world is born with: `author` is already seeded by
    # s15-schema.sql itself (mapped to the connecting role, ON CONFLICT DO NOTHING -- see this
    # script's own header comment); `reviewer` is the one BACKLOG's "Maintainer ruling:
    # self-application" (2026-07-09) names as still hand-registered today ("do 1. register a
    # reviewer principal ... do 2. paste a six-point governance prompt"). Folding it in here
    # closes exactly that gap: a new world is born with both principals a run needs, not just
    # one. Same connection posture as the kernel apply above (SET ROLE, not a superuser bypass --
    # ADR-0012 P1, one mechanism) and the same INSERT `led register-principal` itself would run
    # (kept in lockstep with bootstrap/templates/led.tmpl's own SQL by inspection, not by sharing
    # code across a shell/psql boundary that has none to share). `commissioner` (class human) is
    # the THIRD standard principal (BACKLOG "Five-item batch, maintainer-approved 2026-07-11
    # evening", item 2's FULL signing mode): the maintainer's own registered identity, so that
    # `LED_ACTOR=commissioner ./led commission "<ask>"` (printed at the end of this script) never
    # has to register a principal first, the same closure REVIEWER_STATUS already gives 'reviewer'.
    echo "-- new-world '$NEW_WORLD': registering standard principals (reviewer, commissioner) --"
    psql -h "$HOST" -d "$DB" -v ON_ERROR_STOP=1 <<SQL
        SET ROLE ${ROLE};
        SET search_path = ${SCHEMA}, ${KERN};
        INSERT INTO principal (name, agent_class) VALUES ('reviewer', 'subagent')
        ON CONFLICT (name) DO NOTHING;
        INSERT INTO principal (name, agent_class) VALUES ('commissioner', 'human')
        ON CONFLICT (name) DO NOTHING;
SQL
    echo "   'reviewer' + 'commissioner' principals registered ('author' was already seeded by s15-schema.sql)"
fi

echo "-- deployment.json --"
"$PY" - "$DEPLOYMENT" "$DB" "$HOST" "$SCHEMA" "$KERN" "$ROLE" "$NAME" <<PYEOF
import sys
sys.path.insert(0, "$AUTOHARN_ROOT/filing")
from deployment_record import DeploymentRecord, write_deployment

path, db, host, schema, kern, role, name = sys.argv[1:8]
write_deployment(path, DeploymentRecord(db=db, host=host, schema=schema, kern=kern, role=role, name=name))
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
        -e "s|__S21_STATUS__|$S21_STATUS|g" \
        -e "s|__REVIEWER_STATUS__|$REVIEWER_STATUS|g" \
        -e "s|__COMMISSIONER_STATUS__|$COMMISSIONER_STATUS|g"
}

echo "-- .claude/ wiring --"
sedsubst < "$TEMPLATES/settings.json.tmpl" > "$PROJECT_ROOT/.claude/settings.json"
cp "$TEMPLATES/governed_files.json" "$PROJECT_ROOT/.claude/governed_files.json"
cp "$TEMPLATES/GOVERNED_FILES.md" "$PROJECT_ROOT/.claude/GOVERNED_FILES.md"
cp "$TEMPLATES/apparatus.json" "$PROJECT_ROOT/.claude/apparatus.json"
cp "$TEMPLATES/APPARATUS.md" "$PROJECT_ROOT/.claude/APPARATUS.md"
sedsubst < "$TEMPLATES/HOOKS.md.tmpl" > "$PROJECT_ROOT/.claude/HOOKS.md"
echo "wrote .claude/settings.json, governed_files.json, GOVERNED_FILES.md, apparatus.json, APPARATUS.md, HOOKS.md"

if [ -n "$NEW_WORLD" ]; then
    # CLAUDE.md's preamble states "a reviewer principal exists" as fact -- only true once the
    # reviewer-registration step above has actually run, so this file is written ONLY for
    # --new-world mode (classic mode has no principal table yet at all -- see REVIEWER_STATUS
    # above). This is the second half of the same BACKLOG ruling the reviewer registration
    # closes: "starting a run becomes a verb" names BOTH the hand-registered reviewer principal
    # AND the hand-pasted six-point governance prompt as the ceremony to fold into the scaffold.
    # Lands at the WORLD ROOT (not .claude/) and named exactly `CLAUDE.md` -- ratifier's
    # acceptance bar (2026-07-09): at most one scaffold command, one `cd`, one `claude`, and NO
    # paste step. A file named anything else, or living anywhere else, is not auto-loaded by
    # Claude Code at session start and would put the paste step right back.
    sedsubst < "$TEMPLATES/CLAUDE.md.tmpl" > "$PROJECT_ROOT/CLAUDE.md"
    echo "wrote CLAUDE.md (governance preamble, auto-loaded at session start)"
fi

# the seven verbs (led, judge, pickup, audit, distance-to-clean, verify-commission, verify-chain): thin shims,
# not frozen sed-substituted copies (BACKLOG maintainer ruling 2026-07-11, "runs are strictly
# linear" disposition 6, "live verbs"; audit and distance-to-clean joined the same way later,
# each a new template file rather than an edit to an existing live one -- see their own
# commissions; verify-commission (design/MAINT-GPG-TRUST-LAYER.md Rung 2) follows the SAME
# distance-to-clean precedent one verb later -- a brand-new template file carries none of
# led.tmpl's freeze risk, so it is safe to add regardless of any live wired session elsewhere).
# Baking was the asymmetry: hooks already execute live from this autoharn checkout per invocation
# (settings.json's __AUTOHARN_ROOT__ above), but led/judge/pickup were frozen copies -- a
# just-fixed led defect stayed live in every already-scaffolded world forever, reachable only by
# the NEXT scaffold. A shim closes that: it `exec`s bootstrap/templates/<verb>.tmpl straight out
# of THIS checkout, every invocation, so a template fix here reaches every existing world
# instantly. World-specific facts (db/host/schema/kern/role/name) are no longer sed-substituted
# either -- the .tmpl itself now resolves them LIVE from deployment.json, found next to the shim
# (the shim computes its own directory and passes it through via PICKUP_DEPLOYMENT -- the same
# env var `pickup`'s own live-resolution already used, extended to all three rather than growing
# three near-identical mechanisms, ADR-0012 P1). deployment.json itself stays scaffold-written
# per-world config (unchanged) -- only the VERBS stopped being copies.
# keys/ -- this deployment's OWN GPG keyring (SIGNED commissions, design/MAINT-GPG-TRUST-LAYER.md §3),
# deliberately separate from autoharn's law/keys/ (scoped exclusively to autoharn's own
# ratified/* tags). Mirrors bootstrap/track-work.sh's identical block; applied at the merge
# window per the key-residence refactor's documented frozen-remainder diff (BACKLOG 2026-07-12).
echo "-- keys/ (this deployment's OWN GPG keyring; never autoharn's law/keys/) --"
mkdir -p "$PROJECT_ROOT/keys"
sedsubst < "$TEMPLATES/keys-README.md.tmpl" > "$PROJECT_ROOT/keys/README.md"
echo "wrote keys/README.md (AWAITING-KEY stub; commit THIS deployment's own signing key here)"

echo "-- the seven verbs (led, judge, pickup, audit, distance-to-clean, verify-commission, verify-chain): thin shims exec'ing autoharn's live templates --"
for verb in led judge pickup audit distance-to-clean verify-commission verify-chain; do
    cat > "$PROJECT_ROOT/$verb" <<SHIM
#!/bin/sh
HERE="\$(cd "\$(dirname "\$0")" && pwd)"
exec env PICKUP_DEPLOYMENT="\$HERE/deployment.json" $AUTOHARN_ROOT/bootstrap/templates/$verb.tmpl "\$@"
SHIM
    chmod +x "$PROJECT_ROOT/$verb"
    echo "wrote $verb (shim -> $AUTOHARN_ROOT/bootstrap/templates/$verb.tmpl)"
done

echo "== done =="
echo "Next steps:"
if [ -n "$NEW_WORLD" ]; then
    # Ratifier's acceptance bar (2026-07-09): starting a run is at most one scaffold command, one
    # `cd`, one `claude`, and NO paste step. This world already got there above (kernel + s20 +
    # s21 applied, stamp secret provisioned, 'reviewer' principal registered, CLAUDE.md written)
    # -- the footer below is the whole remaining ceremony, not an abbreviation of a longer one.
    echo "  $CREATE_CMD"
    echo "  cd $PROJECT_ROOT"
    echo "  claude   # then type your task as your first message -- CLAUDE.md auto-loads the"
    echo "           # governance preamble (author + reviewer + commissioner principals, all"
    echo "           # already registered above); nothing to paste."
    echo ""
    echo "(./led, ./judge, ./pickup, ./audit, ./distance-to-clean, ./verify-commission,"
    echo " ./verify-chain are ready to use from inside that session; read"
    echo " $PROJECT_ROOT/.claude/HOOKS.md and replace its UNWITNESSED marks as you exercise each"
    echo " command.)"
    echo ""
    echo "To SIGN this run's commission yourself (FULL mode -- kernel/lineage/s25-commission-"
    echo "kind.sql; the ask carries the commissioner's own guarantee, not a vicarious one), type"
    echo "this in YOUR OWN terminal, inside $PROJECT_ROOT (not inside the agent's session):"
    echo "  LED_ACTOR=commissioner ./led commission \"<the ask verbatim>\""
    echo "The record then shows a commissioner-actor row, and -- typed from a bare shell with no"
    echo "claude session running -- an unstamped-but-attributed row (\`led --recent\` shows"
    echo "stamp_agent as NULL, actor as 'commissioner'): stamp state + actor together are what"
    echo "make FULL mode mechanically distinguishable from LAZY mode (the implementer's own"
    echo "vicarious transcription, CLAUDE.md preamble point 10), never prose claims alone."
    echo ""
    echo "SIGNED mode (design/MAINT-GPG-TRUST-LAYER.md Rung 2 -- FULL, plus a detached GPG signature"
    echo "over the ask): do THIS INSTEAD of the plain FULL-mode line above, not after it --"
    echo "reading the ask from a file ONCE and reusing that same value for both the ledger write"
    echo "and the signature is what keeps the two byte-for-byte identical (typing the ask inline"
    echo "for FULL mode, then separately re-reading a file for the signature, is itself a"
    echo "byte-fidelity hazard -- see verify-commission.tmpl's own module docstring). With the ask"
    echo "in a file (say ~/aa), from YOUR OWN terminal, inside $PROJECT_ROOT:"
    echo "  STATEMENT=\"\$(cat ~/aa)\"                          # exactly what the ledger stores"
    echo "  LED_ACTOR=commissioner ./led commission \"\$STATEMENT\""
    echo "  printf '%s' \"\$STATEMENT\" | gpg --detach-sign --armor -o ~/aa.asc -"
    echo "  mkdir -p $PROJECT_ROOT/.claude"
    echo "  cp ~/aa.asc $PROJECT_ROOT/.claude/commission-<id>.asc   # <id> from the commission's own output"
    echo "  cd $PROJECT_ROOT && ./verify-commission --id <id>"
    echo "Signing 'printf %s \"\$STATEMENT\"' (never the raw file \"~/aa\") is deliberate: it signs"
    echo "byte-for-byte what \"\$(cat ~/aa)\" actually inserted into the ledger (command"
    echo "substitution strips trailing newlines; a raw-file signature would not, and would verify"
    echo "as FORGED-OR-CORRUPT despite being perfectly honest -- see verify-commission.tmpl's own"
    echo "module docstring for the full account of this hazard and its fix). Expect VERIFIED once"
    echo "a real key is committed at THIS deployment's keys/ directory (never autoharn's"
    echo "law/keys/ -- that one is scoped to autoharn's own law); until then every signature refuses"
    echo "as NO-COMMITTED-KEY, exit 3 (there is nothing to check it against yet -- distinct from"
    echo "FORGED-OR-CORRUPT, per design/USER-GPG-TRUST-LAYER-FAQ.md) -- exercise the ceremony with a"
    echo "throwaway test key first if you want to see VERIFIED before the real key exists."
    echo ""
    echo "The SIGNED HEAD (design/MAINT-GPG-TRUST-LAYER.md Rung 3 -- the run-close ritual, one line):"
    echo "at the end of a session, from YOUR OWN terminal, inside $PROJECT_ROOT:"
    echo "  cd $PROJECT_ROOT"
    echo "  ./verify-chain --head > /tmp/head.json    # refuses (exit 1, empty stdout) if the"
    echo "                                             # chain is not INTACT -- verifies first"
    echo "  gpg --detach-sign --armor /tmp/head.json"
    echo "  mkdir -p $PROJECT_ROOT/.claude"
    echo "  cp /tmp/head.json /tmp/head.json.asc $PROJECT_ROOT/.claude/"
    echo "  git -C $PROJECT_ROOT add .claude/head.json .claude/head.json.asc"
    echo "Both files bank as committed evidence. From that moment, ANY retroactive alteration of"
    echo "this world's ledger -- including by the database superuser -- breaks the chain against a"
    echo "head your key vouches for: \"append-only by trigger\" becomes \"append-only or provably"
    echo "broken\" (design/MAINT-GPG-TRUST-LAYER.md §4). Full walkthrough, including WHY --head verifies"
    echo "before it will print anything: design/USER-GPG-TRUST-LAYER-FAQ.md."
else
    echo "  1. Apply a kernel lineage to $DB/$SCHEMA/$KERN/$ROLE if not already applied (kernel/lineage/, autoharn)."
    echo "  2. Provision the stamp secret -- see $PROJECT_ROOT/.claude/HOOKS.md (marked UNWITNESSED until you run it)."
    echo "  3. cd $PROJECT_ROOT && ./led decision \"...\"  /  ./judge  /  ./pickup"
    echo "  4. Read $PROJECT_ROOT/.claude/HOOKS.md and replace its UNWITNESSED marks as you exercise each command."
fi
