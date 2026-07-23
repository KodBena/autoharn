#!/bin/sh
# track-work.sh — give ANY directory a STANDING work-tracking deployment (the "omega
# work-status" litigation closed as a product: research/foundational-map/06-omega-work-status-
# sql-anti-corruption-layer.md is the precedent this offering generalizes; design/
# USER-WORK-STATUS-OFFERING.md is the closure record and the item-by-item mapping table).
#
# WHAT THIS IS, IN ONE SENTENCE: applies this repo's kernel lineage to a fresh schema pair
# named for the target project, writes deployment.json + this deployment's OWN keys/ directory
# (design/MAINT-GPG-TRUST-LAYER.md §7's key-residence split — never autoharn's own law/keys/) + the
# seven read/write verbs (led, pickup, distance-to-clean, judge, audit, verify-commission,
# verify-chain) as live shims into <project-dir>, and registers the three standard principals —
# nothing else. It is deliberately NOT `bootstrap/new-project.sh`:
# that script stands up a GOVERNED WORLD (hooks wired, CLAUDE.md preamble, a stamp secret, the
# runs-are-strictly-linear regime). This script stands up a WORK TRACKER — a standing,
# indefinite-lifetime Postgres-backed replacement for a hand-edited BACKLOG/TODO file, usable by
# a human, a script, or an occasionally-governed agent alike, in a project that may never run a
# single governed Claude Code session. See "STANDING vs WORLD" below for the full contrast.
#
# Usage:
#   bootstrap/track-work.sh <project-dir> --name <name> --db <db> --host <host> \
#       [--schema <schema>] [--kern <kern>] [--role <role>] [--force]
#
#   <project-dir>  where to stamp the deployment (created if missing) — ANY directory; it need
#                   not be a git repo, need not be a Claude Code project, need not ever run a
#                   governed session.
#   --name          this deployment's identifier. REQUIRED (unlike new-project.sh's --name,
#                   which is optional): it is the one thing an operator must choose, and it
#                   DERIVES --schema/--kern/--role the same way `new-project.sh --new-world
#                   <world>` derives them from a world name — schema=<name>,
#                   kern=<name>_kernel, role=<name>_rw — so the three names that must agree stay
#                   in agreement by construction (ADR-0012 P1), not by the caller's memory. An
#                   explicit --schema/--kern/--role still wins if given (e.g. the name collides
#                   with an existing schema). Also written into deployment.json's `name` field,
#                   read live by the `judge` shim (autoharn's own engine/ledger_differential.py
#                   banking subdirectory name) — pick something that will not collide with
#                   engine/targets.py's curated registry names (toy, nla, e15-e18) or its
#                   scratch-naming conventions (^s\d+[a-z]*$, *_scratch).
#   --db            the ledger's database name.
#   --host          the postgres host this project's ledger lives on.
#   --force         overwrite an existing deployment.json at <project-dir> (default: refuse).
#
# STANDING vs WORLD — the distinction this script exists to keep honest, stated plainly because
# it is easy to blur with `new-project.sh`:
#
#   - A WORLD (`new-project.sh --new-world`) is born for ONE run, is subject to the
#     runs-are-strictly-linear ruling (CLAUDE.md ORCHESTRATION, 2026-07-11 — "run M > N means
#     run N's world is dust and settled"), is wired with hooks (change_gate, stamp_intercept,
#     clean_exit) and a CLAUDE.md governance preamble, and gets a provisioned stamp secret so a
#     live Claude Code session's writes carry a verifiable HMAC.
#   - A STANDING deployment (THIS script) is explicitly OUTSIDE that regime: it has NO run
#     number, NO "settles into dust" event, and NO defined end — it is a perpetual work-tracking
#     store for a project's whole lifetime, the same way a project's issue tracker or TODO.md
#     never "expires". It is applied ONCE and then simply used, indefinitely, by `./led work
#     open/claim/close`, `./pickup`, `./distance-to-clean` — the same seven verbs a world uses,
#     wielded here as a persistent tool rather than a per-run habitat.
#
# WHY NO HOOKS ARE WIRED (deliberate, not an oversight — say this loudly, in the output too): a
# standing project is not a governed world. Wiring change_gate/stamp_intercept/clean_exit is a
# SEPARATE, deliberate act (apply `new-project.sh`'s `.claude/` wiring stanzas by hand, or ask
# for that as a follow-on commission) — this script writes ONLY deployment.json and the five
# verb shims. Consequently every row this deployment's `./led` writes lands UNSTAMPED
# (stamp_agent/stamp_session/stamp_hmac all NULL, stamp_verified=false) — visible, not hidden:
# `./led --recent` shows it plainly, and that is the HONEST state of an unwired store, not a
# defect to work around. The full kernel lineage (through s25) is applied regardless, for
# uniformity with every other deployment this repo mints — a project that later DOES wire hooks
# gets the stamp/independence/work-item/commission machinery for free, with no second kernel
# apply — so an unwired project simply produces unstamped-but-attributed rows today. This
# choice (apply the full chain rather than a trimmed "unwired" subset) is deliberate: trimming
# the chain would need a SECOND kernel variant to maintain (ADR-0012 P1 violation) for a
# capability (the stamp mechanism) that is inert, not harmful, when unused.
#
# WHAT THIS APPLIES: the full current birth chain, identical to `new-project.sh --new-world`'s
# own chain (kernel/lineage/README.md is the SSOT) — high_watermark_1.sql (s15 -> s17-stamp ->
# s17-independence -> s19) -> s20 -> s21 -> s22-work-item-ledger -> s23 -> s24 -> s25. The
# work-item layer (s22: `led work open/claim/depends/close/list/violations/asof`) is this
# offering's actual payload — the omega work-status replacement — everything before it in the
# chain is uniform kernel substrate this deployment shares with every governed world.
#
# WHAT THIS DOES NOT DO: apply any kernel DDL to a deployment that already has one without
# --force; wire ANY `.claude/` hook, apparatus, or governance preamble; provision a stamp
# secret (nothing here will ever read one, absent a separate hook-wiring act); touch git in any
# way (the caller commits deployment.json/the verb shims if <project-dir> is a git repo and the
# caller wants them tracked — this script has no opinion on that).
set -eu

usage() {
    echo "usage: $0 <project-dir> --name <name> --db <db> --host <host> [--schema <schema>]" >&2
    echo "           [--kern <kern>] [--role <role>] [--force]" >&2
    echo "       (--name derives --schema/--kern/--role unless given explicitly: schema=<name>," >&2
    echo "        kern=<name>_kernel, role=<name>_rw — mirrors new-project.sh --new-world's own" >&2
    echo "        derivation from a world name. --name is REQUIRED here, unlike new-project.sh," >&2
    echo "        because it is this script's one derivation input.)" >&2
    exit 2
}

# Captured BEFORE any argument parsing consumes "$@" (mirrors new-project.sh's own
# CREATE_CMD/CREATED_AT capture exactly, same reason: this is the operator's ACTUAL invocation,
# printed at the end so "how was this deployment created" never needs reconstruction — BACKLOG
# "Doc-witness fix: how was run3 created?", 2026-07-09, the lesson applied here from the start).
CREATE_CMD="$0"
for _a in "$@"; do
    case "$_a" in
        *[\ \	]*) CREATE_CMD="$CREATE_CMD '$_a'" ;;
        *) CREATE_CMD="$CREATE_CMD $_a" ;;
    esac
done
CREATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

[ $# -ge 1 ] || usage
DEST="$1"; shift
NAME=""
FORCE=0
DB=""; HOST=""; SCHEMA=""; KERN=""; ROLE=""
while [ $# -gt 0 ]; do
    case "$1" in
        --db) DB="$2"; shift 2 ;;
        --host) HOST="$2"; shift 2 ;;
        --schema) SCHEMA="$2"; shift 2 ;;
        --kern) KERN="$2"; shift 2 ;;
        --role) ROLE="$2"; shift 2 ;;
        --name) NAME="$2"; shift 2 ;;
        --force) FORCE=1; shift ;;
        *) echo "unrecognized argument: $1" >&2; usage ;;
    esac
done
[ -n "$NAME" ] || usage
[ -n "$SCHEMA" ] || SCHEMA="$NAME"
[ -n "$KERN" ] || KERN="${NAME}_kernel"
[ -n "$ROLE" ] || ROLE="${NAME}_rw"
[ -n "$DB" ] && [ -n "$HOST" ] || usage

# --- STRICT CHARACTER ALLOWLIST on every name that becomes SQL text ----------------------------
# ADR-0012's 2026-07-18 amendment ("The interpreter boundary -- a value never crosses as program
# text") + ADR-0000's same-day Rule 2(a) amendment (ledger row 1637, fixed first in
# bootstrap/teardown-world.sh commit 0ce5055): SCHEMA/KERN/ROLE reach SQL text below (as psql -v
# bind identifiers) -- checked before ANY SQL is built, covering both --name's own derivation and
# a hand-picked --schema/--kern/--role override alike.
for _name in "$SCHEMA" "$KERN" "$ROLE"; do
    case "$_name" in
        ''|*[!A-Za-z0-9_]*)
            echo "track-work.sh: REFUSED -- '$_name' contains characters outside the allowlist" >&2
            echo "               for a schema/kernel/role name (letters, digits, underscore only)." >&2
            echo "               This applies to --name-derived names and to --schema/--kern/--role" >&2
            echo "               overrides alike. Nothing was touched." >&2
            exit 1
            ;;
    esac
done
unset _name

AUTOHARN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES="$AUTOHARN_ROOT/bootstrap/templates"
PY="$HOME/w/vdc/venvs/generic/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"

mkdir -p "$DEST"
PROJECT_ROOT="$(cd "$DEST" && pwd)"

DEPLOYMENT="$PROJECT_ROOT/deployment.json"
if [ -f "$DEPLOYMENT" ] && [ "$FORCE" -ne 1 ]; then
    echo "track-work.sh: $DEPLOYMENT already exists -- refusing to overwrite (pass --force to replace it)." >&2
    echo "  (a standing deployment is meant to persist indefinitely; re-running this script against" >&2
    echo "  an existing one is presumptively a mistake, not a routine 'refresh' -- there is no such" >&2
    echo "  concept here, mirroring the runs-are-strictly-linear ruling's own posture on worlds.)" >&2
    exit 1
fi

echo "== standing work-tracking deployment at $PROJECT_ROOT (name=$NAME) =="
echo "   This is a STANDING deployment, not a run-scoped world: it has no run number, is never"
echo "   settled into dust, and has no defined end -- it persists for this project's lifetime,"
echo "   the same way an issue tracker does. See this script's own header comment for the full"
echo "   STANDING vs WORLD contrast."
echo ""

# HAZARD FOUND AND FIXED IN THIS SCRIPT'S OWN SCOPE (CLAUDE.md's hazard-flagging duty — a plank
# with a nail met in passing gets the nail pulled): the birth chain's individual files are each
# idempotent (IF NOT EXISTS / CREATE OR REPLACE / DROP-then-CREATE TRIGGER), but the FULL
# high_watermark_1.sql -> s20 -> ... -> s25 SEQUENCE is NOT safely re-runnable in full against a
# schema that already carries the complete chain: intermediate deltas grow a view's column list
# monotonically (s20's own "column-complete" re-issue idiom, s22's header repeats it for
# ledger_current/countersigned_in_force), so re-running an EARLIER file's own (shorter) view
# definition against the ALREADY-FULLY-UPGRADED view fails Postgres's "cannot drop columns from
# a view" rule for CREATE OR REPLACE VIEW. This is a general property of the chain, not specific
# to this script — `new-project.sh --new-world --force` on an already-migrated schema would hit
# the identical failure, a fact worth flagging loudly since editing that frozen file/the kernel
# SQL itself is out of this offering's scope (CLAUDE.md ORCHESTRATION: kernel/lineage is
# maintainer-ratified-spec-only; new-project.sh is under a stated collision constraint this
# session). The SOUND fix achievable here, in this script's own scope: never re-run the DDL
# apply against a schema that already has it — --force's job is "let me re-point/rewrite
# deployment.json and the verb shims", never "re-run kernel DDL a second time".
# SQL text fed on stdin, never via -c (psql's :"var"/:'var' substitution is a silent no-op under
# -c, verified live -- same fix shape as bootstrap/teardown-world.sh commit 0ce5055).
KERNEL_ALREADY_APPLIED="$(printf '%s\n' "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = :'kern');" \
    | psql -h "$HOST" -d "$DB" -v kern="$KERN" -tA)"
if [ "$KERNEL_ALREADY_APPLIED" = "t" ]; then
    echo "-- kernel schema '$KERN' already exists -- SKIPPING the DDL re-apply (see this script's"
    echo "   own comment above: re-running the full birth chain against an already-migrated schema"
    echo "   is not safe -- CREATE OR REPLACE VIEW cannot drop the columns intermediate deltas"
    echo "   already added). --force here re-derives deployment.json + the verb shims + the"
    echo "   principals only; it does not touch existing kernel structure or ledger rows."
else
    echo "-- applying the full kernel lineage (identical chain to new-project.sh --new-world) to"
    echo "   $DB (schema=$SCHEMA kern=$KERN role=$ROLE) --"
    psql -h "$HOST" -d "$DB" -v ON_ERROR_STOP=1 \
        -v schema="$SCHEMA" -v kern="$KERN" -v role="$ROLE" \
        -f "$AUTOHARN_ROOT/kernel/lineage/high_watermark_1.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s20-obligation-grants-and-view-refresh.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s21-session-aware-distinctness.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s22-work-item-ledger.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s23-per-invocation-stamp-token.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s24-declared-event-time.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s25-commission-kind.sql"
    echo "   kernel applied (schema $SCHEMA + kernel schema $KERN + role $ROLE, s20 through s25 included)"
fi

# NO stamp secret is provisioned here (deliberate — see header comment "WHY NO HOOKS ARE
# WIRED"): nothing reads one absent a separate, deliberate hook-wiring act, and provisioning one
# unused would be theater, not assurance (the same "ritual paperwork gets deleted" posture
# CLAUDE.md's runs-are-linear ruling already applies elsewhere).

echo "-- registering the three standard principals (reviewer, commissioner; 'author' is"
echo "   already auto-seeded by s15-schema.sql, mapped to the connecting role) --"
psql -h "$HOST" -d "$DB" -v ON_ERROR_STOP=1 -v role="$ROLE" -v schema="$SCHEMA" -v kern="$KERN" <<SQL
    SET ROLE :"role";
    SET search_path = :"schema", :"kern";
    INSERT INTO principal (name, agent_class) VALUES ('reviewer', 'subagent')
    ON CONFLICT (name) DO NOTHING;
    INSERT INTO principal (name, agent_class) VALUES ('commissioner', 'human')
    ON CONFLICT (name) DO NOTHING;
SQL
echo "   'reviewer' + 'commissioner' principals registered ('author' was already seeded by s15-schema.sql)"

echo "-- deployment.json --"
"$PY" - "$DEPLOYMENT" "$DB" "$HOST" "$SCHEMA" "$KERN" "$ROLE" "$NAME" <<PYEOF
import sys
sys.path.insert(0, "$AUTOHARN_ROOT/filing")
from deployment_record import DeploymentRecord, write_deployment

path, db, host, schema, kern, role, name = sys.argv[1:8]
write_deployment(path, DeploymentRecord(db=db, host=host, schema=schema, kern=kern, role=role, name=name))
print(f"wrote {path}")
PYEOF

# sed substitution table for the shims below -- shares new-project.sh's convention (though this
# script writes only the shims, never a settings.json/apparatus.json/CLAUDE.md).
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
        -e "s|__CREATE_CMD__|$CREATE_CMD|g"
}
# (sedsubst is used below by keys/README.md.tmpl -- the deployment-local keys directory stub --
# and remains available for future template growth; none of the verb shims below currently
# contain a __TOKEN__ -- they are pure `exec` shims, same as new-project.sh's own.)

# COHERENCE PARTNER: keys/README.md and attestations/README.md below are BOTH in gates/
# doc_attestation_presence.py's DEPLOYMENT_SCAFFOLD_OWNED_MD (tracker item `abc-loop-offering`)
# -- they are autoharn's own templated prose, not an adopter's to re-attest. If a future template
# adds another scaffold-written .md file, add it to that set too.
echo "-- keys/ (this deployment's OWN GPG keyring -- SIGNED commissions, design/MAINT-GPG-TRUST-LAYER.md"
echo "   §3 -- deliberately separate from autoharn's own law/keys/, which is scoped exclusively to"
echo "   autoharn's own ratified/* tags and has no bearing on this deployment) --"
mkdir -p "$PROJECT_ROOT/keys"
sedsubst < "$TEMPLATES/keys-README.md.tmpl" > "$PROJECT_ROOT/keys/README.md"
echo "wrote keys/README.md (AWAITING-KEY stub; commit THIS deployment's own signing key here --"
echo "see user-guide/USER-GPG-TRUST-LAYER-FAQ.md §3 for the ceremony -- never to autoharn's law/keys/)"

# attestations/ -- this deployment's OWN ADR-0017 A:B:C fresh-context attestation ledger
# (tracker item `abc-loop-offering`; design/ORCH-SPEC-ABC-OFFERING.md §3), the same
# deployment-local-artifact split as keys/ above, and the same idempotent never-clobber
# posture new-project.sh's own copy of this block documents.
echo "-- attestations/ (this deployment's OWN ADR-0017 A:B:C attestation ledger; never autoharn's) --"
mkdir -p "$PROJECT_ROOT/attestations"
sedsubst < "$TEMPLATES/attestations-README.md.tmpl" > "$PROJECT_ROOT/attestations/README.md"
if [ -f "$PROJECT_ROOT/attestations/doc-legibility-attestations.jsonl" ]; then
    echo "attestations/doc-legibility-attestations.jsonl already exists -- left untouched (never clobbered)"
else
    : > "$PROJECT_ROOT/attestations/doc-legibility-attestations.jsonl"
    echo "wrote attestations/doc-legibility-attestations.jsonl (empty; the honest starting state)"
fi
echo "wrote attestations/README.md"

echo "-- the ten project-local shims (the operator verbs led, judge, pickup, audit,"
echo "   distance-to-clean, attest-doc, asof-export, doctor, plus the signing tools"
echo "   verify-commission and verify-chain): thin shims exec'ing autoharn's live templates,"
echo "   identical mechanism to new-project.sh's own (a template fix in bootstrap/templates/"
echo "   reaches this deployment instantly, same as every governed world) --"
for verb in led judge pickup audit distance-to-clean verify-commission verify-chain attest-doc asof-export doctor; do
    cat > "$PROJECT_ROOT/$verb" <<SHIM
#!/bin/sh
HERE="\$(cd "\$(dirname "\$0")" && pwd)"
exec env PICKUP_DEPLOYMENT="\$HERE/deployment.json" $AUTOHARN_ROOT/bootstrap/templates/$verb.tmpl "\$@"
SHIM
    chmod +x "$PROJECT_ROOT/$verb"
    echo "wrote $verb (shim -> $AUTOHARN_ROOT/bootstrap/templates/$verb.tmpl)"
done

# ./legacy/ (design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md §5, ratified ledger row
# 1631) -- FIXED 2026-07-18, documentation pass: without this, the four shims above
# (led/pickup/asof-export/distance-to-clean) point at the REBASED templates, which refuse
# loudly (exit 4, teaching "boundary_url, boundary_deployment" missing) on EVERY call, because
# this script writes no boundary_url/boundary_deployment into deployment.json (a standing work
# tracker runs no boundary service by design -- see "STANDING vs WORLD" above) -- and, before
# this fix, the refusal's own suggested recovery ("run the ./legacy/ original instead") named a
# directory this script never wrote, so a freshly track-work.sh'd project had NO working
# led/pickup/asof-export/distance-to-clean at all (witnessed: `HARNESS_PGHOST=192.168.122.1
# ./led --recent 3` against a fresh faqwit0718doc scratch deployment exited 4 with exactly that
# message, and `ls legacy` reported "No such file or directory"). Mirrors new-project.sh's own
# ./legacy/ stanza exactly (same four verbs, same legacy-<verb>.tmpl siblings, same
# demoted-by-placement posture -- spec §5's own words: "operator recovery when the boundary is
# down").
echo "-- ./legacy/ (the four rebased verbs' direct-psql originals, demoted by placement, spec §5;"
echo "   THIS deployment has no boundary service of its own, so these are the working verbs) --"
mkdir -p "$PROJECT_ROOT/legacy"
for verb in led pickup asof-export distance-to-clean; do
    cat > "$PROJECT_ROOT/legacy/$verb" <<SHIM
#!/bin/sh
HERE="\$(cd "\$(dirname "\$0")" && cd .. && pwd)"
exec env PICKUP_DEPLOYMENT="\$HERE/deployment.json" $AUTOHARN_ROOT/bootstrap/templates/legacy-$verb.tmpl "\$@"
SHIM
    chmod +x "$PROJECT_ROOT/legacy/$verb"
    echo "wrote legacy/$verb (shim -> $AUTOHARN_ROOT/bootstrap/templates/legacy-$verb.tmpl)"
done

echo ""
echo "== done =="
echo "   $CREATE_CMD"
echo ""
echo "NO hooks were wired (deliberate — a standing project is not a governed world; see this"
echo "script's header comment). Rows written here via ./led are UNSTAMPED (visible, not hidden:"
echo "stamp_agent/stamp_session/stamp_hmac are NULL, stamp_verified=false) until a separate,"
echo "deliberate act wires change_gate/stamp_intercept/clean_exit and provisions a stamp secret"
echo "(new-project.sh's own .claude/ wiring stanzas are the pattern to copy for that act, done by"
echo "hand — this script does not do it, by design)."
echo ""
echo "This is a STANDING deployment: no run number, never settles into dust, no defined end."
echo "Use it exactly like a world's own verbs, indefinitely:"
echo "  cd $PROJECT_ROOT"
echo "  ./led work open <slug> \"<title>\"     # open a work item"
echo "  ./led work claim <slug>              # claim it"
echo "  ./led work close <slug> shipped --witness \"<ref>\"   # close it, witnessed"
echo "  ./pickup                             # live resume brief incl. IN-FLIGHT work items"
echo "  ./distance-to-clean                  # composed closure-debt read"
echo "  ./doctor                             # is this deployment set up right? (witnessed lines)"
echo "  ./led work violations                # cycles / dangling deps / duplicate opens"
echo "  ./attest-doc check                   # ADR-0017 A:B:C attestation status per doc"
echo ""
echo "keys/README.md (AWAITING-KEY) explains this deployment's OWN GPG keyring: commit a public"
echo "key there (never to autoharn's law/keys/) to move SIGNED commissions from NO-COMMITTED-KEY"
echo "to VERIFIED -- ./verify-commission --id <id>; see user-guide/USER-GPG-TRUST-LAYER-FAQ.md §3."
echo ""
echo "attestations/README.md explains this deployment's OWN ADR-0017 A:B:C attestation ledger."
echo "No .claude/apparatus.json is written here (no hooks were wired -- see above), so"
echo "./distance-to-clean's DOC-ATTESTATION section always reads 'off' unless you scaffold one"
echo "by hand (copy new-project.sh's .claude/ wiring, or just run ./attest-doc check directly --"
echo "it needs no apparatus.json at all)."
