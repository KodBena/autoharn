#!/bin/sh
# new-project.sh — stamp a new instance directory: deployment.json, .claude/ wiring
# (settings.json, governed_files.json, apparatus.json, HOOKS.md), and the three verbs (led, judge,
# pickup) as thin shims exec'ing bootstrap/templates/*.tmpl LIVE out of this autoharn checkout
# (vestigial_documentation/design/ORCH-OPUS-READINESS.md move 2's template/instance split, then BACKLOG maintainer ruling
# 2026-07-11 "runs are strictly linear" disposition 6 "live verbs": the verbs stopped being
# sed-substituted frozen copies — a template fix here now reaches every already-scaffolded world
# instantly, matching how the two PreToolUse hooks already execute live per invocation). Only
# deployment.json and the .claude/ wiring stay scaffold-written, per-world config.
#
# Usage:
#   bootstrap/new-project.sh <dest-dir> --db <db> --host <host> --schema <schema> \
#       --kern <kern> --role <role> [--name <project-name>] [--governed <patterns>] [--force]
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
#   --governed   comma-separated fnmatch patterns for `.claude/governed_files.json` (e.g.
#                "*.py,*.sql,*.tf") -- what the change gate protects in THIS deployment (tracker
#                item `scaffold-governed-set-language-default`, ent testbed finding 4, 2026-07-13:
#                the scaffold used to write ['*.py'] unconditionally, so any non-Python deployment
#                was born with its real work surfaces silently ungoverned). Omit it and the
#                scaffold falls back to the historical `*.py`-only default -- but then prints a
#                LOUD post-scaffold notice naming that default and the one-line widening act, so
#                the gap is never silent again.
#   --force      overwrite an existing deployment.json/scaffold at <dest-dir> (default: refuse).
#
# CONTRACT, named explicitly (findings-RCA, DRIVEN-INTERFACE fix): <dest-dir> is created with
# `mkdir -p`, so an OCCUPIED directory that does not already contain a deployment.json is
# permitted and MERGED into silently -- the refusal above fires ONLY on an existing
# deployment.json (or, under --pin submodule, an existing .autoharn), never on an occupied
# directory in general. A caller that wants a guaranteed-fresh directory must check for that
# itself before invoking this script; this script does not and will not make that check for you.
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

# LINEAGE HEAD, derived live from kernel/lineage/*.sql itself (never hand-typed) -- usability
# review finding 14 (ledger row 1180): this usage text used to name a fixed generation ("s20
# through s43 + s45") that fell 12 generations stale the moment a later delta landed and nobody
# remembered to edit this string. Deriving it here means it cannot drift from the code beneath
# it -- the SAME "derive, don't freeze" discipline kernel/lineage/README.md already applies to
# its own "current generation" claim.
_LINEAGE_DIR="$(cd "$(dirname "$0")/../kernel/lineage" && pwd)"
LINEAGE_HEAD="$(cd "$_LINEAGE_DIR" && ls s*.sql 2>/dev/null | grep -v '\.detect\.sql$' \
    | sed -E 's/^s([0-9]+).*/\1/' | sort -n | tail -1)"
[ -n "$LINEAGE_HEAD" ] || LINEAGE_HEAD="?"  # never silently blank if the directory is ever empty

usage() {
    echo "usage: $0 <dest-dir> --db <db> --host <host> --schema <schema> --kern <kern> --role <role> [--name <name>] [--governed <patterns>] [--force]" >&2
    echo "       $0 <dest-dir> --new-world <world> --db <db> --host <host> [--name <name>] [--governed <patterns>] [--force]" >&2
    echo "         (--boundary-url <url> --boundary-deployment <name> write deployment.json's two" >&2
    echo "          new served-shim keys, design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md" >&2
    echo "          §5 -- both optional; the rebased led/pickup/asof-export/distance-to-clean" >&2
    echo "          shims refuse loudly, teaching both names, when either is absent at RUN time" >&2
    echo "          rather than this scaffold guessing a boundary URL or standing one up)" >&2
    echo "         (--new-world derives --schema/--kern/--role from <world> unless given explicitly;" >&2
    echo "          also applies high_watermark_1.sql + every kernel/lineage/sNN delta through the" >&2
    echo "          current head (s${LINEAGE_HEAD} as of this run -- derived live from" >&2
    echo "          kernel/lineage/ itself, never hand-typed here), seeds the stamp secret, and" >&2
    echo "          runs the s40 birth sequence (author registration event, standing declaration," >&2
    echo "          reviewer/commissioner ceremony) -- see the --new-world block in this script's" >&2
    echo "          own header comment)" >&2
    echo "         (--governed <comma-separated-fnmatch-patterns> sets .claude/governed_files.json;" >&2
    echo "          omit it and the *.py-only default is used, with a loud post-scaffold notice)" >&2
    echo "         (--pin submodule adds autoharn as a git submodule at <dest-dir>/.autoharn, pinned" >&2
    echo "          to THIS checkout's current commit, and points every operator verb + hook at that" >&2
    echo "          pinned copy instead of this live checkout -- design/ORCH-DEPLOYMENT-PINNING.md," >&2
    echo "          NOT combinable with --new-world. --pin-url <url> overrides the submodule remote" >&2
    echo "          (default: this checkout's own on-disk path -- portable only on this machine;" >&2
    echo "          pass a real git remote URL for a submodule another machine can also fetch))" >&2
    echo "         (--no-law suppresses the generated LAW section (portable ADR subset + pointers)" >&2
    echo "          this scaffold otherwise writes into .claude/HOOKS.md (and root CLAUDE.md in" >&2
    echo "          --new-world mode) by default -- tracker item portable-adr-delivery, maintainer" >&2
    echo "          instruction 2026-07-15: deployments must at least optionally receive the" >&2
    echo "          portable ADRs; default is ON)" >&2
    echo "         (--accept-existing-content: <dest-dir> classifies FOREIGN -- non-empty, no" >&2
    echo "          autoharn birth evidence (design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md) --" >&2
    echo "          is REFUSED unless this flag is given explicitly; the setup TUI passes it" >&2
    echo "          exactly when its own fork-target screen recorded the operator's typed" >&2
    echo "          acknowledgment. Has no effect on AUTOHARN_COMPLETE/AUTOHARN_PARTIAL, which" >&2
    echo "          keep the existing deployment.json-exists / --force gate above)" >&2
    exit 2
}

[ $# -ge 1 ] || usage
DEST="$1"; shift
NAME=""
FORCE=0
NEW_WORLD=""
GOVERNED=""
DB=""; HOST=""; SCHEMA=""; KERN=""; ROLE=""
# design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md §5 (ledger decision row 1631):
# deployment.json's two new OPTIONAL keys the REBASED shims (led/pickup/asof-export/
# distance-to-clean, now served-HTTP clients by default) need -- refused-if-absent BY THE SHIMS
# THEMSELVES, never by this scaffold (no search-path magic, no auto-launched boundary process:
# standing one up is a separate operator act, spec §3's own "no defaults file" posture extended
# here). Both default empty (unset in the written deployment.json, exactly like `name` above when
# --name is omitted) -- a scaffolded world with neither flag gets the new shims in
# REFUSAL-TEACHING mode until its operator supplies both, which is the correct default (a
# just-scaffolded world has no boundary process running yet either).
BOUNDARY_URL=""
BOUNDARY_DEPLOYMENT=""
# --pin submodule (tracker item deployment-live-exec-coupling, design/ORCH-DEPLOYMENT-PINNING.md,
# maintainer commission 2026-07-14 late "submodule deployment must be IDIOT-PROOF"): an OPT-IN
# scaffold-time flag, default UNSET so every existing caller (every --new-world run world, every
# seen-red/instruments fixture that scaffolds a classic deployment without this flag) keeps
# TODAY'S live-exec shape byte-for-byte -- this design's own text scopes the submodule shape to
# "an adopter", never to autoharn's own run* worlds, so the flag is refused in combination with
# --new-world below rather than silently accepted and ignored (ADR-0002: a refusal that teaches,
# not a caveat buried in a comment nobody reads).
PIN=""
PIN_URL=""
# LAW section (tracker item portable-adr-delivery, maintainer instruction 2026-07-15:
# deployments must at least optionally receive the portable ADRs). Default ON -- opt out with
# --no-law -- so a scaffold never silently withholds the LAW delivery the maintainer asked for;
# an adopter who genuinely wants no ADR pointers says so explicitly, once, rather than the
# scaffold defaulting to silence (mirrors this script's own --governed default-notice posture:
# the safe default is loud, not absent).
LAW_SECTION=1
# design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md §3: opt-in, default UNSET so every existing
# caller keeps today's shape -- a FOREIGN <dest-dir> (non-empty, no autoharn birth evidence) is
# now REFUSED (see the classify_destination gate below, right before mkdir -p) unless this flag
# says so explicitly.
ACCEPT_EXISTING_CONTENT=0
while [ $# -gt 0 ]; do
    case "$1" in
        --db) DB="$2"; shift 2 ;;
        --host) HOST="$2"; shift 2 ;;
        --schema) SCHEMA="$2"; shift 2 ;;
        --kern) KERN="$2"; shift 2 ;;
        --role) ROLE="$2"; shift 2 ;;
        --name) NAME="$2"; shift 2 ;;
        --boundary-url) BOUNDARY_URL="$2"; shift 2 ;;
        --boundary-deployment) BOUNDARY_DEPLOYMENT="$2"; shift 2 ;;
        --new-world) NEW_WORLD="$2"; shift 2 ;;
        --governed) GOVERNED="$2"; shift 2 ;;
        --pin) PIN="$2"; shift 2 ;;
        --pin-url) PIN_URL="$2"; shift 2 ;;
        --no-law) LAW_SECTION=0; shift ;;
        --force) FORCE=1; shift ;;
        --accept-existing-content) ACCEPT_EXISTING_CONTENT=1; shift ;;
        *) echo "unrecognized argument: $1" >&2; usage ;;
    esac
done
if [ -n "$PIN" ] && [ "$PIN" != "submodule" ]; then
    echo "new-project.sh: --pin '$PIN' is not a recognized value -- only 'submodule' is supported" >&2
    echo "                today (the copy-at-scaffold fallback design/ORCH-DEPLOYMENT-PINNING.md" >&2
    echo "                names is deliberately out of scope for this build; the 2026-07-14" >&2
    echo "                maintainer commission asked for the submodule path specifically)." >&2
    exit 2
fi
if [ -n "$PIN" ] && [ -n "$NEW_WORLD" ]; then
    echo "new-project.sh: --pin submodule cannot be combined with --new-world -- autoharn's own" >&2
    echo "                run*-style throwaway worlds are DELIBERATELY scoped OUT of pinning" >&2
    echo "                (design/ORCH-DEPLOYMENT-PINNING.md: \"autoharn's own run* worlds keep" >&2
    echo "                the live-exec shape; that ruling was correctly scoped to them\"). Drop" >&2
    echo "                --pin for a --new-world scaffold, or drop --new-world for a pinned" >&2
    echo "                adopter deployment." >&2
    exit 2
fi
if [ -n "$PIN_URL" ] && [ -z "$PIN" ]; then
    echo "new-project.sh: --pin-url given without --pin submodule -- it has nothing to apply to." >&2
    exit 2
fi
if [ -n "$NEW_WORLD" ]; then
    # Derive, never require, the three names that must agree (P1: one source -- the world name --
    # not three hand-typed strings the caller must keep in sync). An explicit --schema/--kern/--role
    # still wins if the caller passed one (e.g. the world name collides with an existing schema).
    [ -n "$SCHEMA" ] || SCHEMA="$NEW_WORLD"
    [ -n "$KERN" ] || KERN="${NEW_WORLD}_kernel"
    [ -n "$ROLE" ] || ROLE="${NEW_WORLD}_rw"
fi
[ -n "$DB" ] && [ -n "$HOST" ] && [ -n "$SCHEMA" ] && [ -n "$KERN" ] && [ -n "$ROLE" ] || usage

# --- STRICT CHARACTER ALLOWLIST on every name that becomes SQL text ----------------------------
# ADR-0012's 2026-07-18 amendment ("The interpreter boundary -- a value never crosses as program
# text") + ADR-0000's same-day Rule 2(a) amendment (ledger row 1637: this exact raw-interpolation-
# into-psql shape, fixed first in bootstrap/teardown-world.sh, commit 0ce5055): SCHEMA/KERN/ROLE
# reach SQL text below (as psql -v bind identifiers where a carrier exists, and directly spliced
# into PL/pgSQL DO-block bodies where a carrier genuinely does not -- psql's :"var" substitution is
# plain client-side text substitution and does NOT reach inside a dollar-quoted DO $bw$...$bw$ body,
# verified live against 192.168.122.1 db toy before this fix was written) -- this scaffold had NO
# validation on these names at all before this fix, unlike teardown-world.sh's sibling check. This
# is the SAME allowlist, checked before ANY SQL is built, covering both --new-world's own derivation
# and a hand-picked --schema/--kern/--role override alike (a caller can pass either, and both reach
# the identical downstream SQL sites).
for _name in "$SCHEMA" "$KERN" "$ROLE"; do
    case "$_name" in
        ''|*[!A-Za-z0-9_]*)
            echo "new-project.sh: REFUSED -- '$_name' contains characters outside the allowlist" >&2
            echo "                for a schema/kernel/role name (letters, digits, underscore only)." >&2
            echo "                This applies to --new-world-derived names and to --schema/--kern/" >&2
            echo "                --role overrides alike. Nothing was touched." >&2
            exit 1
            ;;
    esac
done
unset _name

# LINEAGE_CHAIN: what kernel DDL THIS scaffold run applied (or didn't), for the PROVENANCE header
# below -- the honest record of which sNN deltas this world was born on, so a future reader never
# has to reconstruct it from source the way run3's own history had to be reconstructed.
#
# FORMAT (usability review finding 18, ledger row 1180): one line per generation, not the single
# ~9,000-character run-on paragraph this used to be. Each bullet below is separated by a literal
# `\n` (two characters, not a newline byte) -- `sedsubst`'s `s|__LINEAGE_CHAIN__|$LINEAGE_CHAIN|g`
# is fed as a single `-e` argument, and this sed does not accept a real embedded newline there
# (tested: "unterminated `s' command"), but DOES expand a literal `\n` in the replacement text to
# a real newline in its output -- so HOOKS.md itself renders as an actual multi-line list; only
# this shell variable's own source representation uses the two-character escape. No prose below
# was altered from the paragraph it replaces (ADR-0020) -- every clause, ratification reference,
# and HISTORY-safe note is byte-identical, split at each generation's own existing sentence
# boundary rather than reworded.
if [ -n "$NEW_WORLD" ]; then
    LINEAGE_CHAIN="s15 -> s17-stamp-mechanism -> s17-independence-vocabulary -> s19 -> s20 -> s21-session-aware-distinctness -> s22-work-item-ledger -> s23-per-invocation-stamp-token -> s24-declared-event-time -> s25-commission-kind -> s26-row-hash-chain -> s27-chain-high-water -> s28-work-parent-edge -> s29-obligation-item-key-and-typed-close -> s30-typed-dependency-edges -> s31-supersession-uniform-retraction -> s32-edge-views-single-home -> s33-composite-discharge -> s34-computed-grade-refusal -> s35-validation-decomposition -> s36-decision-grade -> s37-violation-disposition -> s38-bookkeeping-close -> s39-blocks-start -> s40-principal-identity-events -> s41-principal-bindings-and-relations -> s42-row-hash-full-coverage -> s43-typed-verdict-write-boundary -> s44-model-identity-attestation -> s45-standing-lifecycle -> s46-credited-views -> s47-claim-on-closed-refusal -> s48-review-witness-existence -> s49-journaler-overflow-guard -> s50-defeat-input-raw-domain -> s51-artifact-store -> s52-artifact-witness-check -> s53-belief-substrate -> s54-belief-views -> s55-dispatch-grain-independence -> s56-reservation-residue -> s57-obligation-revocation-event (via kernel/lineage/high_watermark_1.sql + kernel/lineage/s20-obligation-grants-and-view-refresh.sql + kernel/lineage/s21-session-aware-distinctness.sql + kernel/lineage/s22-work-item-ledger.sql + kernel/lineage/s23-per-invocation-stamp-token.sql + kernel/lineage/s24-declared-event-time.sql + kernel/lineage/s25-commission-kind.sql + kernel/lineage/s26-row-hash-chain.sql + kernel/lineage/s27-chain-high-water.sql + kernel/lineage/s28-work-parent-edge.sql + kernel/lineage/s29-obligation-item-key-and-typed-close.sql + kernel/lineage/s30-typed-dependency-edges.sql + kernel/lineage/s31-supersession-uniform-retraction.sql + kernel/lineage/s32-edge-views-single-home.sql + kernel/lineage/s33-composite-discharge.sql + kernel/lineage/s34-computed-grade-refusal.sql + kernel/lineage/s35-validation-decomposition.sql + kernel/lineage/s36-decision-grade.sql + kernel/lineage/s37-violation-disposition.sql + kernel/lineage/s38-bookkeeping-close.sql + kernel/lineage/s39-blocks-start.sql + kernel/lineage/s40-principal-identity-events.sql + kernel/lineage/s41-principal-bindings-and-relations.sql + kernel/lineage/s42-row-hash-full-coverage.sql + kernel/lineage/s43-typed-verdict-write-boundary.sql + kernel/lineage/s44-model-identity-attestation.sql + kernel/lineage/s45-standing-lifecycle.sql + kernel/lineage/s46-credited-views.sql + kernel/lineage/s47-claim-on-closed-refusal.sql + kernel/lineage/s48-review-witness-existence.sql + kernel/lineage/s49-journaler-overflow-guard.sql + kernel/lineage/s50-defeat-input-raw-domain.sql + kernel/lineage/s51-artifact-store.sql + kernel/lineage/s52-artifact-witness-check.sql + kernel/lineage/s53-belief-substrate.sql + kernel/lineage/s54-belief-views.sql + kernel/lineage/s55-dispatch-grain-independence.sql + kernel/lineage/s56-reservation-residue.sql + kernel/lineage/s57-obligation-revocation-event.sql), applied automatically by this --new-world run, delta by delta:\n- s29 wired in via its sec-10 migration-epoch amendment (ledger decision row 935's conditional ratification), which yields epoch=0 on this empty, freshly-scaffolded ledger (see that file's own AMENDMENT header for why)\n- s30 (typed dependency edges, ledger decision row 1018) needs no epoch machinery of its own -- HISTORY: safe, see that file's own header\n- s31 (supersession uniform retraction, ratified spec design/FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md) re-issues readers only, no epoch, HISTORY: safe per its own header\n- s32 (edge-views-single-home) is a pure refactor, output-equality witnessed, HISTORY: safe per its own header\n- s33 (composite-discharge, ratified spec design/FABLE-COMPOSITE-DISCHARGE-SPEC.md) adds an opt-in typed column + refusals, nothing relaxed, HISTORY: safe per its own header\n- s34 (computed-grade refusal) adds one refusal, class-ratified fail-safe, HISTORY: safe per its own header\n- s35 (validation decomposition) is a pure refactor -- every refusal text byte-identical, leaf byte-identity gate polices future re-issues -- HISTORY: safe per its own header\n- s36 (decision grade, ratified spec design/FABLE-GRADED-DECISIONS-SPEC.md) adds a nullable writer-supplied column + one derived view, nothing relaxed, HISTORY: safe per its own header\n- s37 (violation disposition, ratified spec design/FABLE-ORPHAN-DISPOSITION-SPEC.md v3) adds one kind + validator and re-issues the violations/history views, nothing relaxed, HISTORY: safe per its own header\n- s38 (bookkeeping close, ratified spec design/FABLE-BOOKKEEPING-CLOSE-SPEC.md) widens the review-disposition vocabulary to a third, machine-verified value (a git-commit witness, existence-checked CLI-side) plus one new narrowing CHECK and one new audit view, re-issue-only / additive-vocabulary, HISTORY: safe per its own header\n- s39 (blocks-start, the maintainer's claim-time precondition-foreclosure commission) widens the edge_type vocabulary to a third value (blocks-start), adds a claim-time refusal (a new validate_work_item_claim leaf) and two new derived views (work_edge_blocks_start, work_startable), nothing existing relaxed, HISTORY: safe per its own header\n- s40 (principal identity events, ratified spec design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md, first of the s40/s41 family) makes identity facts append-only attributed ledger events (four new kinds), derives standing (kernel.principal_standing), converts kernel.principal_role from table to derived view, re-issues set_actor as strict-declared-default attribution, and couples the anchor to its registration event -- NOT class-ratified fail-safe (table->view + live trigger re-issue), ships under its own ratified spec; HISTORY: safe per its own header, and this scaffold's own birth sequence below discharges the three explicit s40 birth acts (author registration event, standing declaration, reviewer/commissioner ceremony)\n- s41 (principal bindings and relations, second of the same ratified family) adds the four binding/relation event kinds (typed acts-for/dispatched-by/same-natural-person/succeeds edges, role bindings, human-only key-binding slots, G13 competence grants), the human-attested managerial/financial independence scoping (D-6), and retires the anchor's acts_for column by CHECK -- NOT class-ratified fail-safe, ships under the same ratified spec; HISTORY: safe per its own header, no birth act of its own\n- s42 (row-hash full coverage, ratified spec design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md, first of the s42/s43 family) re-issues compute_row_hash so the tamper-evidence chain serializes EVERY ledger column except row_hash itself (52 at this head; the 22 post-s26 columns were outside the chain, ledger row 1449), held complete forever by gates/hash_coverage_gate.py -- NOT class-ratified fail-safe (it changes what row_hash MEANS), ships under its own ratified spec; HISTORY: safe per its own header (function/view re-issues and brand-new objects only, no history-validating statement over pre-existing rows -- true of any deployment this delta reaches, not merely a fresh scaffold), no birth act of its own\n- s43 (typed-verdict write boundary, second of the same ratified s42/s43 family) REVOKES the granted role's INSERT on every kernel-governed table and makes four SECURITY DEFINER jsonb-payload functions (ledger_write/review_write/registration_write/obligation_write) the only write path -- a refusal is caught inside them, journaled as a committed write_refused ledger row (attributed to the write-boundary tool principal, digest-only payload, R4) and returned as a typed verdict, never an abort; adds the refusal_seq completeness oracle (reconciled by ./verify-chain), re-issues set_actor on session_user, and re-issues compute_row_hash to 58 columns under s42's own law -- NOT class-ratified fail-safe, ships under the same ratified spec; HISTORY: safe per its own header, and this scaffold's birth sequence below routes every birth act through the boundary functions and adds two s43 birth acts (the login-role standing declaration and the write-boundary principal registration)\n- s45 (standing lifecycle, ratified spec design/FABLE-STANDING-LIFECYCLE-SPEC.md, maintainer batch ratification ledger row 1481) licenses principal_binding_active on principal_standing_declared and principal_suspended (deliberately NOT principal_revoked -- that absence IS ratified terminal-by-type), re-issues kernel.principal_role with resurrection-proof governing-row semantics, re-issues the standing functions with the in-force filter a lift needs to be observable, and re-issues validate_supersession_target with a same-kind identity-continuous supersession discipline for the three lifecycle kinds -- NOT class-ratified fail-safe (four live re-issues), ships under its own ratification; HISTORY: safe per its own header, and this scaffold's standing declarations above now carry principal_binding_active true\n- s44 (model-identity attestation) adds the model_identity_attested kind, seven attest_* columns under two-way kind-shape CHECKs with closed grade/verdict vocabularies, a self-table FK making the attested target's existence structural, the model_attestations view, and re-issues compute_row_hash to 65 columns under s42's law -- additive kind + refusals, nothing relaxed, supersession deliberately allowed (contrast s43 R6); HISTORY: safe per its own header\n- s46 (credited views) adds the defeat-calculus display layer (model_defeated_rows + credited_current), additive derived views, nothing relaxed; HISTORY: safe per its own header (its defeat-input exclusion domain is re-issued by s50 below, ruling ledger row 1647)\n- s47 (claim-on-closed refusal, maintainer-prioritized 2026-07-18) prepends a third claim-time precondition -- a slug with an in-force work_closed row is not claimable -- class 2(a) fail-safe additive refusal; HISTORY: safe per its own header\n- s48 (review-witness row existence, spec design/FABLE-KERNEL-INTAKE-PAIR-SPEC.md delta 1, ledger row 1600) verifies at insert time that row:<id> tokens in the review-witness position of close-family kinds cite rows that exist -- class 2(a) fail-safe additive refusal, prose refs deliberately untouched; HISTORY: safe per its own header\n- s49 (journaler overflow guard, same spec delta 2, ledger row 1581, built under the maintainer's direct instruction) totalizes the attempted-identity resolution inside kernel.journal_write_refusal so an over-bigint actor string is journaled with attempted-id NULL instead of aborting the refusal recording -- strictly fail-safe effect, more refusals recorded, nothing newly permitted; HISTORY: safe per its own header\n- s50 (defeat-input raw domain, ratified spec design/FABLE-S46-DEFEAT-INPUT-DOMAIN-SPEC.md, maintainer-delegated ruling ledger row 1647) re-issues model_defeated_rows so its defeat-input exclusion quantifies over raw history, matching both engine producers -- protective-only, the defeated set can only shrink (witnessed WS46-c); HISTORY: safe per its own header. CHAIN ACT: s44 + s46-s50 entered by the maintainer's ratified act of 2026-07-18 (prepared by the orchestrator, ratified via the decision queue; the first --new-world run after this entry is the six deltas' first sequential witness as a chain)\n- s51 (artifact store, ratified spec design/FABLE-ARTIFACT-STORE-SPEC.md accepted as-is ledger row 1666, essential-records admission criterion row 1665) adds kernel.artifact -- content-addressed, append-only custody for bytes a ledger row's evidentiary force relies on -- and kernel.artifact_write, the fifth SECURITY DEFINER boundary function in s43's own verdict/journaling shape (refusals journaled digest-only, bytes never in the journal; artifact_too_large typed at 1 MiB; closed media vocabulary) -- NOT class-ratified fail-safe (new write path), ships under its accepted spec; HISTORY: safe per its own header\n- CHAIN ACT: s51 entered by the maintainer's ruling of 2026-07-18 (ledger row 1673 item 1)\n- s52 (artifact witness check, ratified spec design/FABLE-ARTIFACT-WITNESS-CHECK-SPEC.md, build ratified row 1673 item 2, merged row 1675) makes artifact:<hash> tokens in the review-witness position of the two close-family kinds insert-time existence-checked against kernel.artifact, malformed tokens refusing in the same shape -- class 2(a) fail-safe additive refusal, s48's sibling arms and prose refs untouched, judge --layer work AGREE both polarities; HISTORY: safe per its own header\n- CHAIN ACT: s52 entered by the maintainer's ruling of 2026-07-18 ('Well, we'll apply s52.')\n- s53 (belief substrate, ratified spec design/FABLE-BELIEF-SUBSTRATE-SPEC.md v2 Delta B1, ledger rows 1914/1919) adds the belief kind, nine belief_* columns under two-way (polarity/basis) and one-way (the other seven) kind-shape CHECKs plus five polarity/basis coupling CHECKs, two new refusal triggers (validate_belief_evidence, validate_belief_edges), one belief branch added to validate_supersession_target (a belief is revised only by its own holder; a cross-principal supersession attempt is refused, the correct act being a CONTEST), and re-issues compute_row_hash/ledger_current/countersigned_in_force to 74 columns under s42's law -- NOT class-ratified fail-safe (it mints vocabulary the whole project will reason in, per that spec's own §11), ships under its own ratification; HISTORY: safe per its own header\n- s54 (belief views, same spec v2 Delta B2) adds the typed-arm-only display layer (belief_current, contested_beliefs, credited_beliefs, corroboration, shared_premise), additive derived views, nothing relaxed, zero new columns/kinds; HISTORY: safe per its own header\n- s55 (dispatch-grain independence, same spec v2 Delta B3, Q6) widens review_detail_independence_check by one member (disclosed-isolated-dispatch), an honest disclosure treated exactly as self-review, zero function/trigger edits; HISTORY: safe per its own header. CHAIN ACT: s53/s54/s55 entered by this build's own commission (design/FABLE-BELIEF-SUBSTRATE-SPEC.md, ratified ledger rows 1914/1919), the s40-s44 same-commit-wiring precedent, chosen because this build's own task requires scratch witnessing via --new-world\n- s56 (reservation residue, Fable-authored spec design/FABLE-RESERVATION-RESIDUE-SPEC.md, maintainer-ratified 2026-07-22 against autoharn2 ledger rows 1093-1095) widens discharging_attest (s32's own single home) IN PLACE to also discharge attest_with_reservations verdicts, and adds two additive views (reservations_outstanding, review_verdicts) -- VIEW-ONLY, zero new ledger columns, zero new kinds, compute_row_hash untouched; HISTORY: safe per its own header\n- s57 (obligation revocation as a typed event, design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part A, maintainer-ratified in the same act as Parts B/C, ledger row 1150) adds the obligation_revoked kind (two mandatory columns, kind-shape CHECKs split from value CHECKs per the s40 house idiom) and kernel.obligation_revoke, the SIXTH SECURITY DEFINER write-boundary function (reuses s43's write_verdict type and journal_write_refusal unchanged) -- NOT class-ratified fail-safe (new write path + kind), ships under its own ratification; HISTORY: safe per its own header. CHAIN ACT: s56/s57 entered by this closing-batch build (ledger rows 1176/1178), following the s53-s55 same-commit-wiring precedent immediately above -- this --new-world run is the two deltas' first sequential witness as a chain, both detect queries (s56.detect.sql, s57.detect.sql) exercised against the newborn below."
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
    REVIEWER_STATUS="Registered automatically by this --new-world scaffold run through the s40 ceremony (principal 'reviewer', class subagent, purpose stated, a principal_registered event on the ledger; see the birth-sequence step in this same run, right after the stamp secret above) -- do NOT re-register; a repeat \`./led register-principal reviewer ...\` is REFUSED loudly with teach-text (s40 deleted the silent ON CONFLICT no-op), and the scaffold's own re-run existence check prints 'already registered' instead of attempting one."
    # COMMISSIONER_STATUS: mirrors REVIEWER_STATUS exactly -- the honest, mode-aware record of
    # whether the 'commissioner' principal (kernel/lineage/s25-commission-kind.sql's FULL signing
    # mode; BACKLOG "Five-item batch, maintainer-approved 2026-07-11 evening", item 2) exists yet.
    # Registering it here, alongside 'reviewer', means the maintainer's OWN signing act (see the
    # printed copy-paste line at the end of this script) never has to register its own principal
    # first -- the same "starting a run becomes a verb" closure REVIEWER_STATUS already documents.
    COMMISSIONER_STATUS="Registered automatically by this --new-world scaffold run through the s40 ceremony (principal 'commissioner', class human, purpose stated, a principal_registered event on the ledger; see the birth-sequence step in this same run, right after 'reviewer' above) -- do NOT re-register; a repeat is REFUSED loudly (s40 deleted the silent ON CONFLICT no-op), and the scaffold's own re-run existence check prints 'already registered' instead of attempting one. FULL-mode signing (the maintainer signs the ask himself): \`LED_ACTOR=commissioner ./led commission \"<the ask verbatim>\"\` -- typed by the maintainer in his OWN terminal, inside this world. LAZY-mode (the implementer vicariously transcribes the ask on receiving it, first ledger act, no commissioner guarantee): see this world's CLAUDE.md preamble."
else
    LINEAGE_CHAIN="NOT applied by this scaffold run -- apply a kernel lineage to $SCHEMA/$KERN/$ROLE manually (kernel/lineage/, see kernel/lineage/README.md) before first use"
    STAMP_SECRET_STATUS="**One manual step remains: provision the stamp secret. UNWITNESSED — the block below has not been run in this instance.**"
    S21_STATUS="NOT applied by this scaffold run (classic --schema/--kern/--role mode applies no kernel lineage at all -- see item 1 above). If this world's kernel predates s21, apply it as a separate, explicit operator act from autoharn's own checkout: \`bootstrap/apply-delta.sh <this-project's-directory> kernel/lineage/s21-session-aware-distinctness.sql\` (prints the resolved command, requires a typed schema confirmation, never applies bare) -- status/witness live in autoharn's BACKLOG.md (search \"s21\")."
    REVIEWER_STATUS="NOT registered by this scaffold run (classic --schema/--kern/--role mode applies no kernel lineage at all -- see item 1 above, so there is no \`principal\` table yet to register into). Once a kernel lineage is applied, register one explicitly: \`./led register-principal reviewer subagent\`."
    COMMISSIONER_STATUS="NOT registered by this scaffold run (classic --schema/--kern/--role mode applies no kernel lineage at all -- see item 1 above). Once a kernel lineage carrying kernel/lineage/s25-commission-kind.sql is applied, register one explicitly: \`./led register-principal commissioner human\`."
fi

AUTOHARN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# AUTOHARN_COMMIT -- the autoharn checkout's own commit hash at scaffold time, so a world's
# evidence can be tied to the INSTRUMENT VERSION that produced it (prior regulator-panel
# assessment's Tier-1 item 4: "no record ties a historical DENY to the hook bytes that produced
# it" -- vestigial_documentation/design/MAINT-RELITIGATION-SYNTHESIS.md, "No configuration index"). Read once, here,
# never re-derived: this same value is written into the PROVENANCE header below (ADR-0012 P1).
# Degrades honestly rather than silently blank -- a git failure or a dirty checkout are both
# real facts about the instrument that produced this world, not to be hidden behind an empty
# string (ADR-0002).
AUTOHARN_COMMIT_SHA="$(cd "$AUTOHARN_ROOT" && git rev-parse HEAD 2>/dev/null || true)"
AUTOHARN_COMMIT="$AUTOHARN_COMMIT_SHA"
AUTOHARN_DIRTY=0
if [ -n "$AUTOHARN_COMMIT" ]; then
    if ! (cd "$AUTOHARN_ROOT" && git diff --quiet && git diff --cached --quiet) 2>/dev/null; then
        AUTOHARN_DIRTY=1
        AUTOHARN_COMMIT="$AUTOHARN_COMMIT (DIRTY -- uncommitted changes were present in the autoharn checkout at scaffold time; this world's evidence cannot be reproduced from this commit hash alone)"
    fi
else
    AUTOHARN_COMMIT="UNAVAILABLE -- $AUTOHARN_ROOT is not a git checkout, or git is not on PATH (git rev-parse HEAD failed); this world's evidence cannot be tied to an instrument version by commit hash"
fi

# --pin submodule needs a REPRODUCIBLE commit to pin to -- a dirty or unavailable checkout would
# pin a deployment to bytes that cannot be reconstructed from the SHA alone, defeating the whole
# point (ADR-0002: refuse loudly rather than pin to a lie).
if [ "$PIN" = "submodule" ]; then
    if [ -z "$AUTOHARN_COMMIT_SHA" ]; then
        echo "new-project.sh: --pin submodule requires this autoharn checkout ($AUTOHARN_ROOT) to be" >&2
        echo "                a git repository with git on PATH -- git rev-parse HEAD failed." >&2
        exit 1
    fi
    if [ "$AUTOHARN_DIRTY" -eq 1 ]; then
        echo "new-project.sh: --pin submodule refuses to pin a deployment to a DIRTY autoharn" >&2
        echo "                checkout ($AUTOHARN_ROOT has uncommitted changes) -- the pinned SHA" >&2
        echo "                would not reproduce what actually gets copied into the submodule." >&2
        echo "                Commit or stash the changes in $AUTOHARN_ROOT, then re-run." >&2
        exit 1
    fi
fi

TEMPLATES="$AUTOHARN_ROOT/bootstrap/templates"
PY="$HOME/w/vdc/venvs/generic/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"

# design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md §3: the FOREIGN-content refusal, BEFORE
# `mkdir -p` (this used to `mkdir -p` and merge into ANY occupied directory lacking
# deployment.json, silently -- the defect the spec's commission names). AUTOHARN_COMPLETE/
# AUTOHARN_PARTIAL are untouched here -- they keep the deployment.json-exists/--force gate below,
# unchanged. `classify_destination` is bootstrap/classify-destination.sh's own shell
# re-derivation of tools/setup_tui/destination.py's Python classifier (that module is the
# authority; see this sourced file's own header for why the two are kept in sync by a parity
# fixture, not codegen).
. "$AUTOHARN_ROOT/bootstrap/classify-destination.sh"
DEST_KIND="$(classify_destination "$DEST")"
if [ "$DEST_KIND" = "foreign" ] && [ "$ACCEPT_EXISTING_CONTENT" -ne 1 ]; then
    echo "new-project.sh: REFUSED -- '$DEST' is non-empty and carries no autoharn birth" >&2
    echo "                evidence (FOREIGN, design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md)." >&2
    echo "                Pass --accept-existing-content to scaffold into it anyway (the setup" >&2
    echo "                TUI passes this exactly when its fork-target screen recorded the" >&2
    echo "                operator's typed acknowledgment). Nothing touched." >&2
    exit 1
fi

mkdir -p "$DEST"
PROJECT_ROOT="$(cd "$DEST" && pwd)"
[ -n "$NAME" ] || NAME="$(basename "$PROJECT_ROOT")"

DEPLOYMENT="$PROJECT_ROOT/deployment.json"
if [ -f "$DEPLOYMENT" ] && [ "$FORCE" -ne 1 ]; then
    echo "new-project.sh: $DEPLOYMENT already exists -- refusing to overwrite (pass --force to replace it)." >&2
    exit 1
fi

echo "== stamping instance at $PROJECT_ROOT (name=$NAME) =="

# EXEC_ROOT -- the autoharn tree every operator verb + hook actually points at. Unpinned (the
# default, unchanged from before this flag existed): the live checkout, $AUTOHARN_ROOT, same as
# every world scaffolded before this build. --pin submodule: a FROZEN copy of THIS commit, living
# inside the deployment's own git tree at $PROJECT_ROOT/.autoharn -- design/ORCH-DEPLOYMENT-
# PINNING.md's whole point (a deployment stops executing another project's mutable working tree).
EXEC_ROOT="$AUTOHARN_ROOT"
if [ "$PIN" = "submodule" ]; then
    echo "-- --pin submodule: pinning autoharn@$AUTOHARN_COMMIT_SHA into $PROJECT_ROOT/.autoharn --"
    if [ -e "$PROJECT_ROOT/.autoharn" ] && [ "$FORCE" -ne 1 ]; then
        echo "new-project.sh: $PROJECT_ROOT/.autoharn already exists -- refusing to overwrite" >&2
        echo "                (pass --force to replace it, or this deployment is already pinned)." >&2
        exit 1
    fi
    if [ -e "$PROJECT_ROOT/.autoharn" ] && [ "$FORCE" -eq 1 ]; then
        echo "   --force: removing existing $PROJECT_ROOT/.autoharn before re-adding"
        (cd "$PROJECT_ROOT" && git submodule deinit -f .autoharn 2>/dev/null || true)
        rm -rf "$PROJECT_ROOT/.autoharn" "$PROJECT_ROOT/.git/modules/.autoharn"
    fi
    if (cd "$PROJECT_ROOT" && git rev-parse --is-inside-work-tree >/dev/null 2>&1); then
        echo "   $PROJECT_ROOT is already a git repository -- using it"
    else
        echo "   $PROJECT_ROOT is not yet a git repository -- running git init"
        (cd "$PROJECT_ROOT" && git init --quiet)
    fi
    # Default submodule URL: THIS checkout's own on-disk path -- a plain local-filesystem submodule
    # git supports natively, works with no network access, and is HONEST about its portability
    # limit (printed below). --pin-url overrides with a real remote for a submodule another
    # machine can also fetch.
    SUBMODULE_URL="${PIN_URL:-$AUTOHARN_ROOT}"
    # -c protocol.file.allow=always: ONLY set when SUBMODULE_URL is a local filesystem path (the
    # default absent --pin-url) -- git 2.38.1+ (CVE-2022-39253) refuses the "file" transport for a
    # submodule's internal clone unless explicitly allowed, even though `git submodule add` itself
    # was a direct, deliberate operator/scaffold action. A real remote URL (--pin-url) never needs
    # this override.
    _submodule_add_opts=""
    case "$SUBMODULE_URL" in
        *://*) ;;  # a real URL (https://, ssh://, git://, ...) -- no override needed
        *) _submodule_add_opts="-c protocol.file.allow=always" ;;
    esac
    (cd "$PROJECT_ROOT" && git $_submodule_add_opts submodule add --quiet "$SUBMODULE_URL" .autoharn)
    (cd "$PROJECT_ROOT/.autoharn" && git checkout --quiet "$AUTOHARN_COMMIT_SHA")
    (cd "$PROJECT_ROOT" && git add .gitmodules .autoharn)
    echo "   submodule added and pinned to $AUTOHARN_COMMIT_SHA (staged; this scaffold run commits"
    echo "   it, along with the operator verbs + hook wiring it points at, at the end of this run)"
    if [ -z "$PIN_URL" ]; then
        echo "   NOTE: submodule URL is a LOCAL PATH ($SUBMODULE_URL) -- this deployment's git clone"
        echo "   is portable on THIS machine only. For a submodule another machine can also fetch,"
        echo "   re-run with --pin-url <a real git remote for autoharn>."
    fi
    EXEC_ROOT="$PROJECT_ROOT/.autoharn"
fi

if [ -n "$NEW_WORLD" ]; then
    # DB-SIDE PRE-FLIGHT GUARD (ledger row 1148's ratified direction, reproduced mechanism):
    # `CREATE TABLE IF NOT EXISTS` silently SKIPS a wrong-shaped leftover relation from a prior,
    # partial birth, and s15-schema.sql's later `INSERT ... ON CONFLICT (db_role)` then dies
    # because the skipped table's own PK never got created -- the "s15 dead end" row 1148 closed:
    # re-birth over partial DB state, not a kernel defect. This mirrors the dest-DIRECTORY guard
    # above (classify_destination, ~line 336) but on the DATABASE side: query the catalog for
    # ANY existing relation under the target schema OR kernel-schema namespaces, BEFORE any DDL
    # below runs, and refuse loudly rather than walk in and die partway through. Queried live,
    # right here (never cached) -- a rehearsal that just tore its own scratch world down to zero
    # residue (teardown-world.sh's own verified-zero-residue step) sees an empty catalog and
    # passes; only genuine leftover state trips this.
    _preflight_psql_in() { printf '%s\n' "$1"; }
    PREFLIGHT_RELS=$(_preflight_psql_in \
        "SELECT n.nspname || '.' || c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname IN (:'schema', :'kern') AND c.relkind IN ('r','v','m','p','S') ORDER BY 1;" \
        | psql -h "$HOST" -d "$DB" -v schema="$SCHEMA" -v kern="$KERN" -tA)
    PREFLIGHT_COUNT=$(printf '%s\n' "$PREFLIGHT_RELS" | grep -c . || true)
    if [ "$PREFLIGHT_COUNT" -gt 0 ]; then
        PREFLIGHT_SAMPLE=$(printf '%s\n' "$PREFLIGHT_RELS" | head -5 | sed 's/^/     - /')
        # Same scratch-safe naming test teardown-world.sh itself applies to $NEW_WORLD -- so the
        # teardown command this refusal prints is the EXACT command that will succeed, including
        # the --force-non-scratch flag when (and only when) the world name needs it.
        PREFLIGHT_FORCE_FLAG=""
        case "$NEW_WORLD" in
            run[0-9]*|s[0-9]*|faqwit*|svcfx*|probeworld*|*_scratch) ;;
            *) PREFLIGHT_FORCE_FLAG=" --force-non-scratch" ;;
        esac
        echo "new-project.sh: REFUSED -- schema '$SCHEMA' and/or kernel schema '$KERN' in $DB@$HOST" >&2
        echo "                already carry $PREFLIGHT_COUNT relation(s)/object(s) -- this is NOT" >&2
        echo "                an empty target for a fresh --new-world birth. Found (up to 5 shown):" >&2
        printf '%s\n' "$PREFLIGHT_SAMPLE" >&2
        echo "                Re-birthing a kernel lineage over partial DB state is the known s15" >&2
        echo "                dead end (ledger row 1148): CREATE TABLE IF NOT EXISTS silently skips" >&2
        echo "                a wrong-shaped leftover table, and s15's own ON CONFLICT (db_role)" >&2
        echo "                insert later dies because that skipped table's PK was never created." >&2
        echo "                Clear it first with the sanctioned teardown verb, then re-run:" >&2
        echo "                    bootstrap/teardown-world.sh $NEW_WORLD --db $DB --host $HOST \\" >&2
        echo "                        --schema $SCHEMA --kern $KERN --role $ROLE$PREFLIGHT_FORCE_FLAG" >&2
        echo "                Nothing was touched -- no DDL below has run yet." >&2
        exit 1
    fi
    unset -f _preflight_psql_in

    echo "-- new-world '$NEW_WORLD': applying high_watermark_1.sql + s20 + s21 + s22 + s23 + s24 + s25 + s26 + s27 + s28 + s29 + s30 + s31 + s32 + s33 + s34 + s35 + s36 + s37 + s38 + s39 + s40 + s41 + s42 + s43 + s44 + s45 + s46 + s47 + s48 + s49 + s50 + s51 + s52 + s53 + s54 + s55 + s56 + s57 to $DB (schema=$SCHEMA kern=$KERN role=$ROLE) --"
    psql -h "$HOST" -d "$DB" -v ON_ERROR_STOP=1 \
        -v schema="$SCHEMA" -v kern="$KERN" -v role="$ROLE" \
        -f "$AUTOHARN_ROOT/kernel/lineage/high_watermark_1.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s20-obligation-grants-and-view-refresh.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s21-session-aware-distinctness.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s22-work-item-ledger.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s23-per-invocation-stamp-token.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s24-declared-event-time.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s25-commission-kind.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s26-row-hash-chain.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s27-chain-high-water.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s28-work-parent-edge.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s29-obligation-item-key-and-typed-close.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s30-typed-dependency-edges.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s31-supersession-uniform-retraction.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s32-edge-views-single-home.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s33-composite-discharge.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s34-computed-grade-refusal.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s35-validation-decomposition.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s36-decision-grade.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s37-violation-disposition.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s38-bookkeeping-close.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s39-blocks-start.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s40-principal-identity-events.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s41-principal-bindings-and-relations.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s42-row-hash-full-coverage.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s43-typed-verdict-write-boundary.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s44-model-identity-attestation.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s45-standing-lifecycle.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s46-credited-views.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s47-claim-on-closed-refusal.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s48-review-witness-existence.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s49-journaler-overflow-guard.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s50-defeat-input-raw-domain.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s51-artifact-store.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s52-artifact-witness-check.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s53-belief-substrate.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s54-belief-views.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s55-dispatch-grain-independence.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s56-reservation-residue.sql" \
        -f "$AUTOHARN_ROOT/kernel/lineage/s57-obligation-revocation-event.sql"
    echo "   kernel applied (schema $SCHEMA + kernel schema $KERN + role $ROLE, s20 + s21 + s22 + s23 + s24 + s25 + s26 + s27 + s28 + s29 + s30 + s31 + s32 + s33 + s34 + s35 + s36 + s37 + s38 + s39 + s40 + s41 + s42 + s43 + s44 + s45 + s46 + s47 + s48 + s49 + s50 + s51 + s52 + s53 + s54 + s55 + s56 + s57 included -- s29's migration_epoch naturally seeds 0 on this empty ledger, see that file's own AMENDMENT header; s30 needs no epoch machinery of its own, HISTORY: safe; s40's own birth acts run below, after the seeds; s45 licenses principal_binding_active on the two standing-lifecycle kinds and is honored by the standing declarations below, which now carry the flag; s56/s57 are view-only/new-write-path respectively, neither needs a birth-sequence act of its own)"

    # _psql_in: SQL text is always fed on stdin, never via -c -- psql's :'var'/:"var" bind-variable
    # interpolation (verified live against a real server, psql 18.3) is only performed for input it
    # parses as a script (stdin or -f), and is a silent no-op under -c (the literal colon reaches the
    # server and the statement errors out). Same fix shape/rationale as bootstrap/teardown-world.sh
    # commit 0ce5055 (ledger row 1637) and this file's own allowlist block above.
    _psql_in() { printf '%s\n' "$1"; }

    echo "-- new-world '$NEW_WORLD': seeding the stamp secret (idempotent, mirrors drive/arm.sh ruling 43) --"
    mkdir -p "$PROJECT_ROOT/.claude/secrets"
    chmod 700 "$PROJECT_ROOT/.claude/secrets"
    SECRET_FILE="$PROJECT_ROOT/.claude/secrets/stamp_secret.hex"
    HAVE=$(_psql_in "SELECT count(*) FROM :\"kern\".stamp_secret;" | psql -h "$HOST" -d "$DB" -v kern="$KERN" -tA)
    if [ "$HAVE" = "1" ]; then
        echo "   a secret is already provisioned for ${KERN}.stamp_secret (1 row); not rotating"
    else
        ( umask 077; openssl rand -hex 32 > "$SECRET_FILE" )
        chmod 600 "$SECRET_FILE"
        HEX=$(cat "$SECRET_FILE")
        # KERN reaches DROP/TRUNCATE-adjacent DDL text as an identifier bind (:"kern"), HEX as a
        # literal bind (:'hex') -- both bound as psql -v variables via stdin, never spliced into the
        # SQL string (the allowlist above already restricts KERN to [A-Za-z0-9_]+; this is the
        # primary carrier per ADR-0012's 2026-07-18 amendment, not just defense-in-depth on KERN).
        _psql_in 'TRUNCATE :"kern".stamp_secret;' \
            | psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v kern="$KERN"
        _psql_in "INSERT INTO :\"kern\".stamp_secret (secret) VALUES (decode(:'hex','hex'));" \
            | psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v kern="$KERN" -v hex="$HEX"
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
    HAVE_GENESIS=$(_psql_in "SELECT count(*) FROM :\"kern\".chain_genesis;" \
        | psql -h "$HOST" -d "$DB" -v kern="$KERN" -tA 2>/dev/null || echo "0")
    if [ "$HAVE_GENESIS" = "1" ]; then
        echo "   a genesis seed is already provisioned for ${KERN}.chain_genesis (1 row); not rotating"
    elif [ "$HAVE_GENESIS" = "0" ]; then
        GENESIS_HEX=$(openssl rand -hex 32)
        _psql_in "INSERT INTO :\"kern\".chain_genesis (seed) VALUES (:'genesis_hex') ON CONFLICT (only_one) DO NOTHING;" \
            | psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v kern="$KERN" -v genesis_hex="$GENESIS_HEX"
        echo "   one fresh genesis seed provisioned (DB ${KERN}.chain_genesis)"
    else
        echo "   ${KERN}.chain_genesis does not exist -- this world's kernel predates s26-row-hash-chain.sql; skipping (not an error, an older lineage)"
    fi

    # THE s40 BIRTH SEQUENCE (kernel/lineage/s40-principal-identity-events.sql §3.7; replaces
    # the pre-s40 ON CONFLICT DO NOTHING block that stood here -- the silent-no-op idiom s40
    # deleted from the verb is replaced at the scaffold by EXISTENCE CHECKS that print "already
    # registered": idempotent at the scaffold, never silent at the verb). Three explicit acts,
    # in this order, all as the granted role (SET ROLE, never a superuser bypass), all kept in
    # lockstep with bootstrap/templates/led.tmpl's own SQL by inspection:
    #   (1) `author`'s principal_registered EVENT -- the anchor row was seeded by s15 inside the
    #       chain apply (pre-s40 position, so the anchor-coupling trigger did not exist yet);
    #       the scaffold discharges its event explicitly. THE ONE GENESIS EXCEPTION: the event
    #       is SELF-ATTRIBUTED (actor = author) -- a first identity event cannot be attributed
    #       to any earlier-registered principal, mirroring the hash chain's genesis-seed
    #       precedent for a first link that cannot reference a predecessor; the self-attribution
    #       is named in the event's own statement text.
    #   (2) a principal_standing_declared event binding this world's role to `author` (actor =
    #       author, explicit) -- the DECLARED-not-silent default every strict-mode NULL-actor
    #       write resolves through: strict-on costs the solo operator nothing, the ratified
    #       reconciliation (basis row 1398).
    #   (3) `reviewer` (subagent) and `commissioner` (human) registered through the FULL
    #       ceremony (anchor + event atomically, actor = author, purposes stated) -- the same
    #       two standard principals every world was already born with, now with recorded
    #       registrations (BACKLOG "Maintainer ruling: self-application" 2026-07-09 closure,
    #       carried forward under s40's ceremony).
    # THE s40 BIRTH ACTS, ROUTED THROUGH THE s43 WRITE BOUNDARY (kernel/lineage/
    # s43-typed-verdict-write-boundary.sql: the granted role holds NO INSERT anywhere after
    # the chain above applied -- every birth act below is a boundary-function call, and a
    # 'refused' verdict is converted back into a LOUD scaffold failure by the DO-block
    # pattern each act uses: the birth of a world is exactly the place a refusal must stop
    # the line, not land as a quiet journal row). Two NEW s43 acts join the sequence: the
    # LOGIN-role standing declaration (step 2b -- s43 Element 8's dual declaration:
    # set_actor resolves on session_user now, so the login role the world's DSN
    # authenticates as needs its own declared standing, witnessed here at scaffold time as
    # session_user) and the write-boundary tool principal's registration (step 4 -- s43
    # Element 6: the identity that authors every write_refused row).
    echo "-- new-world '$NEW_WORLD': s40/s43 birth sequence (author event, dual standing declarations, reviewer/commissioner/write-boundary ceremony) --"
    LOGIN_ROLE=$(psql -h "$HOST" -d "$DB" -tAc "SELECT session_user;")
    HAVE_AUTHOR_EVENT=$(_psql_in "SELECT count(*) FROM :\"schema\".ledger l JOIN :\"kern\".principal p ON p.id = l.principal_subject WHERE l.kind = 'principal_registered' AND p.name = 'author';" \
        | psql -h "$HOST" -d "$DB" -v schema="$SCHEMA" -v kern="$KERN" -tA)
    if [ "$HAVE_AUTHOR_EVENT" != "0" ]; then
        echo "   'author' already carries a registration event ($HAVE_AUTHOR_EVENT); not re-registering"
    else
        psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v role="$ROLE" -v schema="$SCHEMA" -v kern="$KERN" <<SQL
        SET ROLE :"role";
        SET search_path = :"schema", :"kern";
        -- KERN below (write_verdict's type qualifier) is inside a dollar-quoted DO body: psql's
        -- :"var" substitution does not reach dollar-quoted text (verified live), so this one
        -- reference is guarded by the allowlist check earlier in this script, not by a bind.
        DO \$bw\$
        DECLARE v ${KERN}.write_verdict;
        BEGIN
          SELECT * INTO v FROM ${KERN}.ledger_write(jsonb_build_object(
            'kind', 'principal_registered',
            'statement', 'principal ''author'' registered (class model) -- genesis exception: self-attributed (actor = author), the first identity event of this world; no earlier-registered principal exists to attribute it to (s40 birth sequence step 1)',
            'actor', (SELECT id FROM principal WHERE name = 'author'),
            'principal_subject', (SELECT id FROM principal WHERE name = 'author'),
            'principal_purpose', 'the scaffold connection principal: the identity this world''s granted role writes as by default'));
          IF v.disposition <> 'accepted' THEN
            RAISE EXCEPTION 'birth sequence step 1 refused (SQLSTATE %): %', v.sqlstate, v.message;
          END IF;
        END \$bw\$;
SQL
        echo "   (1) 'author' registration event recorded via the write boundary (genesis exception, self-attributed)"
    fi
    for _drole in "$ROLE" "$LOGIN_ROLE"; do
        HAVE_DECL=$(_psql_in "SELECT count(*) FROM :\"schema\".ledger_current lc WHERE lc.kind = 'principal_standing_declared' AND lc.principal_db_role = :'drole';" \
            | psql -h "$HOST" -d "$DB" -v schema="$SCHEMA" -v drole="$_drole" -tA)
        if [ "$HAVE_DECL" != "0" ]; then
            echo "   role '${_drole}' already carries a standing declaration; not re-declaring"
            continue
        fi
        psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v role="$ROLE" -v schema="$SCHEMA" -v kern="$KERN" -v drole="$_drole" <<SQL
        SET ROLE :"role";
        SET search_path = :"schema", :"kern";
        SELECT set_config('birth.drole', :'drole', false);
        -- KERN below (write_verdict's type qualifier) is inside a dollar-quoted DO body: guarded
        -- by the allowlist check earlier in this script, not by a bind (see the step-1 comment above).
        DO \$bw\$
        DECLARE v ${KERN}.write_verdict;
        BEGIN
          SELECT * INTO v FROM ${KERN}.ledger_write(jsonb_build_object(
            'kind', 'principal_standing_declared',
            'statement', format('database role ''%s'' speaks for principal ''author'' by default (standing declaration, s40 birth sequence step 2 / s43 Element 8''s dual declaration -- the declared-not-silent default)', current_setting('birth.drole')),
            'actor', (SELECT id FROM principal WHERE name = 'author'),
            'principal_subject', (SELECT id FROM principal WHERE name = 'author'),
            'principal_db_role', current_setting('birth.drole'),
            'principal_binding_active', true));
          IF v.disposition <> 'accepted' THEN
            RAISE EXCEPTION 'birth sequence step 2 refused (SQLSTATE %): %', v.sqlstate, v.message;
          END IF;
        END \$bw\$;
SQL
        echo "   (2) standing declaration recorded via the write boundary (role ${_drole} -> author)"
    done
    for _pname in reviewer commissioner write-boundary; do
        case "$_pname" in
            reviewer)       _pclass="subagent"; _ppurpose="the standard second principal a run needs: countersigns the author principal's rows (BACKLOG self-application ruling 2026-07-09)" ;;
            commissioner)   _pclass="human";    _ppurpose="the maintainer's own registered identity for FULL-mode commission signing (s25; five-item batch 2026-07-11 item 2)" ;;
            write-boundary) _pclass="tool";     _ppurpose="the kernel write boundary's own recording identity: every write_refused meta-event is authored by this principal; the attempted identity is carried in the event's refusal_attempted_* columns (s43)" ;;
        esac
        HAVE_P=$(_psql_in "SELECT count(*) FROM :\"kern\".principal WHERE name = :'pname';" \
            | psql -h "$HOST" -d "$DB" -v kern="$KERN" -v pname="$_pname" -tA)
        if [ "$HAVE_P" != "0" ]; then
            echo "   '${_pname}' already registered; skipping"
        else
            psql -h "$HOST" -d "$DB" -q -v ON_ERROR_STOP=1 -v role="$ROLE" -v schema="$SCHEMA" -v kern="$KERN" -v pname="$_pname" -v pclass="$_pclass" -v ppurpose="$_ppurpose" <<SQL
        SET ROLE :"role";
        SET search_path = :"schema", :"kern";
        SELECT set_config('birth.pname', :'pname', false),
               set_config('birth.pclass', :'pclass', false),
               set_config('birth.ppurpose', :'ppurpose', false);
        -- KERN below (write_verdict's type qualifier) is inside a dollar-quoted DO body: guarded
        -- by the allowlist check earlier in this script, not by a bind (see the step-1 comment above).
        DO \$bw\$
        DECLARE v ${KERN}.write_verdict;
        BEGIN
          SELECT * INTO v FROM ${KERN}.registration_write(jsonb_build_object(
            'name', current_setting('birth.pname'),
            'agent_class', current_setting('birth.pclass'),
            'purpose', current_setting('birth.ppurpose'),
            'statement', format('principal ''%s'' registered (class %s) -- s40 birth sequence step 3/4, registrar: author', current_setting('birth.pname'), current_setting('birth.pclass')),
            'actor', (SELECT id FROM principal WHERE name = 'author')));
          IF v.disposition <> 'accepted' THEN
            RAISE EXCEPTION 'birth sequence step 3/4 refused (SQLSTATE %): %', v.sqlstate, v.message;
          END IF;
        END \$bw\$;
SQL
            echo "   (3/4) '${_pname}' registered through the boundary ceremony (class ${_pclass}, registrar author)"
        fi
    done
fi

echo "-- deployment.json --"
"$PY" - "$DEPLOYMENT" "$DB" "$HOST" "$SCHEMA" "$KERN" "$ROLE" "$NAME" "$BOUNDARY_URL" "$BOUNDARY_DEPLOYMENT" <<PYEOF
import sys
sys.path.insert(0, "$AUTOHARN_ROOT/filing")
from deployment_record import DeploymentRecord, write_deployment

path, db, host, schema, kern, role, name, boundary_url, boundary_deployment = sys.argv[1:10]
write_deployment(path, DeploymentRecord(
    db=db, host=host, schema=schema, kern=kern, role=role, name=name or None,
    boundary_url=boundary_url or None, boundary_deployment=boundary_deployment or None))
print(f"wrote {path}")
if not boundary_url or not boundary_deployment:
    print("   (boundary_url/boundary_deployment not supplied -- the rebased led/pickup/"
          "asof-export/distance-to-clean shims will refuse, teaching both names, until this "
          "deployment.json gains them by hand or a future --boundary-url/--boundary-deployment "
          "re-scaffold; ./legacy/ holds the direct-psql originals in the meantime)")
PYEOF

# .autoharn-world.json sentinel (design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md §2), written
# at the SAME point as deployment.json above -- the DECLARED birth marker; deployment.json +
# legacy/led remain the BEHAVIORAL evidence. `world` is written as the SAME value as
# deployment.json's own `name` field just written above (tools/setup_tui/destination.py's module
# docstring names this resolution explicitly: the two denote the same fact at birth time, and can
# only drift apart from a LATER hand-edit or a --force re-scaffold under a different --name --
# exactly the drift classify_destination's contradiction check exists to catch). `run` is
# `--new-world`'s own value, empty for a classic --schema/--kern/--role scaffold (no world/run
# concept at all). SENTINEL_SCHEMA is imported from destination.py, not re-typed (ADR-0012 P1).
echo "-- .autoharn-world.json sentinel --"
"$PY" - "$PROJECT_ROOT/.autoharn-world.json" "$NAME" "$NEW_WORLD" "$CREATED_AT" "$AUTOHARN_COMMIT_SHA" <<PYEOF
import json
import sys
sys.path.insert(0, "$AUTOHARN_ROOT")
from tools.setup_tui import destination

path, world, run, born, commit = sys.argv[1:6]
with open(path, "w", encoding="utf-8") as f:
    json.dump({
        "world": world, "run": run or None, "born": born,
        "autoharn_commit": commit or None, "schema": destination.SENTINEL_SCHEMA,
    }, f, indent=2)
    f.write("\n")
print(f"wrote {path}")
PYEOF

mkdir -p "$PROJECT_ROOT/.claude/logs" "$PROJECT_ROOT/.claude/secrets"
chmod 700 "$PROJECT_ROOT/.claude/secrets"

# .gitignore the scaffolding-owned churn paths INSIDE the subject repo this scaffold is stamping
# (tracker item `scaffold-log-churn-in-subject-repo`, ent-observatory cycle-001 NEW lesson 1: the
# invocation log landed git-tracked inside an audited subject repo -- picom/.claude/logs -- and
# churned on every session action; that cycle's audit agent handled it correctly by hand
# (excluding .claude from its diffs), but nothing stops the NEXT audit agent from missing that
# exclusion and treating the churn as a false-positive mutation signal. Fixed at birth here rather
# than left for every future audit to route around by hand.
#
# Append-if-missing (idempotent, mirrors the stamp-secret/genesis-seed never-rotate posture
# elsewhere in this script): a marker pair brackets the block so a re-scaffold (--force) or a
# second scaffold call against the same dest-dir never duplicates it.
echo "-- .gitignore (scaffolding-owned churn paths in the subject repo) --"
GITIGNORE="$PROJECT_ROOT/.gitignore"
GITIGNORE_MARK_BEGIN="# >>> autoharn scaffold-owned churn (bootstrap/new-project.sh) >>>"
GITIGNORE_MARK_END="# <<< autoharn scaffold-owned churn <<<"
if [ -f "$GITIGNORE" ] && grep -qF "$GITIGNORE_MARK_BEGIN" "$GITIGNORE" 2>/dev/null; then
    echo "   $GITIGNORE already carries the scaffold-owned churn block -- left untouched (idempotent)"
else
    {
        echo ""
        echo "$GITIGNORE_MARK_BEGIN"
        echo "# Written by bootstrap/new-project.sh ($CREATED_AT), tracker item"
        echo "# scaffold-log-churn-in-subject-repo: these paths are scaffolding/hook RUNTIME OUTPUT"
        echo "# (invocation logs, change-gate state), not audited subject-repo content, and churn on"
        echo "# every session action -- tracking them git-side is a false-positive generator for any"
        echo "# diff/mutation-purity check run against this repo (ent-observatory cycle-001, NEW"
        echo "# lesson 1). Append-if-missing; safe to re-run."
        echo ".claude/logs/"
        echo "$GITIGNORE_MARK_END"
    } >> "$GITIGNORE"
    echo "   appended scaffold-owned churn block to $GITIGNORE (.claude/logs/)"
fi
if (cd "$PROJECT_ROOT" && git rev-parse --is-inside-work-tree >/dev/null 2>&1); then
    :
else
    echo "   NOTE: $PROJECT_ROOT is not (yet) a git repo -- the .gitignore above was still written;"
    echo "   it is inert until this directory becomes one (e.g. \`git init\`), at which point it"
    echo "   takes effect immediately with no further action."
    echo "   Consequence while this window is open: \`led work close --review-bookkeeping"
    echo "   --witness commit:<sha>\` (the ceremony-free close for note-class work) needs a"
    echo "   commit to witness and is unusable without a repo here -- every close must go"
    echo "   --review-deferred instead, and each one accrues review-gap debt until this"
    echo "   directory is \`git init\`'d. Weigh initializing sooner against absorbing that debt."
fi

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
        -e "s|__AUTOHARN_ROOT__|$EXEC_ROOT|g" \
        -e "s|__CREATED_AT__|$CREATED_AT|g" \
        -e "s|__CREATE_CMD__|$CREATE_CMD|g" \
        -e "s|__AUTOHARN_COMMIT__|$AUTOHARN_COMMIT|g" \
        -e "s|__LINEAGE_CHAIN__|$LINEAGE_CHAIN|g" \
        -e "s|__STAMP_SECRET_STATUS__|$STAMP_SECRET_STATUS|g" \
        -e "s|__S21_STATUS__|$S21_STATUS|g" \
        -e "s|__REVIEWER_STATUS__|$REVIEWER_STATUS|g" \
        -e "s|__COMMISSIONER_STATUS__|$COMMISSIONER_STATUS|g"
}

# LAW section (tracker item portable-adr-delivery, maintainer instruction 2026-07-15): the
# portable ADR subset (design/MAINT-ADR-PORTABILITY-SPEC.md's own per-ADR treatment table --
# every ADR file under law/adr/ EXCEPT a Status:Retired-to-history tombstone already carries a
# generalize-in-place/examples-extract/already-portable/ui-scoped treatment, i.e. is written to
# be read and applied outside autoharn itself), each pointed at its file INSIDE THIS DEPLOYMENT'S
# OWN EXEC_ROOT -- REQUIRED SHAPE is no-copying: a pinned deployment (--pin submodule) already
# carries the full corpus at .autoharn/law/adr/ by construction (the submodule IS the copy), so
# this writes pointers, never a second copy of the ADR bytes. Derived from the filesystem, not a
# hand-maintained duplicate list (ADR-0012 P1: one source -- the corpus itself is the
# enumeration; a hardcoded second list would drift the moment an ADR's Status changes, exactly
# the "fossil array" ADR-0008 names). Two honest shapes, per EXEC_ROOT: PINNED (submodule, frozen
# to a commit -- pointers move only via bootstrap/upgrade-submodule.sh, deliberately) and
# UNPINNED live-exec (EXEC_ROOT is the shared checkout -- pointers move whenever that checkout
# changes, stated plainly rather than implying a frozen copy that does not exist; this is the
# deliberate shape for a deployment autoharn itself vendors, e.g. a panel project that cannot
# embed autoharn as a submodule without a cycle). Written into .claude/HOOKS.md always (the one
# doc guaranteed in every scaffold mode, pinned or not, new-world or classic) and into root
# CLAUDE.md too when --new-world writes one (auto-loaded at session start). --no-law suppresses
# this entirely -- an adopter who wants no ADR pointers says so explicitly, once.
LAW_SECTION_FILE="$PROJECT_ROOT/.claude/.law-section.md.tmp"
if [ "$LAW_SECTION" -eq 1 ]; then
    echo "-- LAW section (portable ADR subset, design/MAINT-ADR-PORTABILITY-SPEC.md) --"
    if [ "$PIN" = "submodule" ]; then
        LAW_PIN_NOTE="This deployment is **PINNED** (git submodule at \`.autoharn\`, frozen to commit \`$AUTOHARN_COMMIT_SHA\`) -- the pointers below are frozen along with it. A newer autoharn's ADR corpus reaches this deployment only via a deliberate \`bootstrap/upgrade-submodule.sh\`, never silently on a \`git pull\` of autoharn itself."
    else
        LAW_PIN_NOTE="This deployment is **UNPINNED** (live-exec against the checkout at \`$EXEC_ROOT\`, no \`.autoharn\` submodule) -- the pointers below resolve into that checkout and MOVE whenever it changes; there is no frozen copy here. (Deliberate for a deployment that autoharn itself vendors -- e.g. a panel/demo project -- where pinning autoharn in as a submodule would create a submodule cycle.)"
    fi
    "$PY" - "$AUTOHARN_ROOT/law/adr" "$EXEC_ROOT" "$LAW_SECTION_FILE" "$LAW_PIN_NOTE" <<'PYEOF'
import pathlib
import sys

adr_dir, exec_root, out_path, pin_note = sys.argv[1:5]
adr_dir = pathlib.Path(adr_dir)
rows = []
for f in sorted(adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md")):
    text = f.read_text(encoding="utf-8")
    lines = text.splitlines()
    # Find the first real H1 (`# ...`), not necessarily line 0 -- some ADRs open with an
    # HTML doc-attest-exempt comment block (e.g. 0012, 2026-07-15 table-sweep commission)
    # ahead of the heading; a fossil "read line 0 as the title" assumption would silently
    # mislabel every such ADR (exactly the fossil-array failure mode ADR-0008 names).
    title = f.name
    for ln in lines:
        s = ln.strip()
        if s.startswith("# "):
            title = s[2:].strip()
            break
    # Same reasoning for the Status line: search the whole file, not a fixed line-count
    # window, since a leading comment block can push it past any fixed cutoff.
    status_line = ""
    for ln in lines:
        if ln.strip().startswith("- **Status:**"):
            status_line = ln
            break
    if "Retired-to-history" in status_line:
        continue  # a tombstone carries no live rule content -- excluded from the served set
    rows.append((f.name, title))

with open(out_path, "w", encoding="utf-8") as out:
    out.write("## LAW (portable ADR subset, vendored via this scaffold)\n\n")
    out.write(
        "Written by `bootstrap/new-project.sh` (tracker item `portable-adr-delivery`, maintainer "
        "instruction 2026-07-15). The subset below is the CURRENTLY-SERVED, "
        "cross-project-portable slice of autoharn's ADR corpus -- "
        "`design/MAINT-ADR-PORTABILITY-SPEC.md`'s own per-ADR treatment table: every entry here "
        "already carries a `generalize-in-place`/`examples-extract`/`already-portable`/"
        "`ui-scoped-generalize-or-unserve` treatment, i.e. it is written to be read and applied "
        "outside autoharn itself (ADR-0001 is excluded -- its own Status retired it to a history "
        "tombstone; it carries no live rule content to extrapolate from). " + pin_note + "\n\n"
        "**Reading posture:** read each ADR IN FULL before any work requiring it -- diagnosing, "
        "designing, or touching code shaped by its rule -- and read it for its SPIRIT: these are "
        "principles to extrapolate from and interpret judiciously, not rules to satisfy by letter "
        "alone. Where letter and spirit appear to diverge, the spirit governs, and the divergence "
        "is surfaced, not silently resolved.\n\n"
    )
    for name, title in rows:
        out.write(f"- **{title}** -- `{exec_root}/law/adr/{name}`\n")
    out.write("\n")
PYEOF
    N=$(grep -c '^- \*\*' "$LAW_SECTION_FILE" 2>/dev/null || echo 0)
    echo "   generated LAW section ($N portable ADRs enumerated)"
else
    : > "$LAW_SECTION_FILE"
    echo "-- LAW section: --no-law given -- deployment scaffolded WITHOUT the portable-ADR LAW section --"
fi

echo "-- .claude/ wiring --"
sedsubst < "$TEMPLATES/settings.json.tmpl" > "$PROJECT_ROOT/.claude/settings.json"
# governed_files.json: --governed <comma-separated-patterns> lets THIS deployment declare its
# real work surface at birth (tracker item `scaffold-governed-set-language-default`, ent testbed
# finding 4, 2026-07-13) instead of inheriting the historical *.py-only default silently. Absent
# --governed, the old default template is copied unchanged (byte-identical scaffold behavior for
# every existing caller) -- but the gap it can leave is no longer silent: the loud notice below
# names the default and the exact one-line widening act, refusal-grade rather than a footnote.
if [ -n "$GOVERNED" ]; then
    "$PY" - "$PROJECT_ROOT/.claude/governed_files.json" "$GOVERNED" <<'PYEOF'
import json
import sys

path, patterns_csv = sys.argv[1:3]
patterns = [p.strip() for p in patterns_csv.split(",") if p.strip()]
with open(path, "w") as f:
    json.dump({"patterns": patterns}, f, indent=2)
    f.write("\n")
PYEOF
    echo "wrote .claude/governed_files.json (custom, --governed '$GOVERNED')"
else
    cp "$TEMPLATES/governed_files.json" "$PROJECT_ROOT/.claude/governed_files.json"
    echo "wrote .claude/governed_files.json (DEFAULT: *.py only)"
    echo ""
    echo "!! GOVERNED-SET DEFAULT NOTICE (no --governed given) !!"
    echo "This deployment's change gate governs *.py files ONLY -- the scaffold's historical"
    echo "default, not a judgment about what THIS project's real work surface is. If this"
    echo "deployment's work is not Python (SQL, shell, Terraform, config, docs, anything else),"
    echo "those files are UNGOVERNED right now: Claude Code can edit them with NO preceding ledger"
    echo "entry, and nothing will warn you again after this line."
    echo "Widen it with exactly one edit -- $PROJECT_ROOT/.claude/governed_files.json:"
    echo "  { \"patterns\": [\"*.py\", \"*.sql\", \"*.tf\"] }"
    echo "(fnmatch semantics, no restart needed: $PROJECT_ROOT/.claude/GOVERNED_FILES.md)"
    echo ""
fi
# COHERENCE PARTNER: .claude/GOVERNED_FILES.md and .claude/APPARATUS.md below are AUTOHARN's own
# prose, named in gates/doc_attestation_presence.py's DEPLOYMENT_SCAFFOLD_OWNED_MD (tracker item
# `abc-loop-offering`) so a scaffolded deployment's ./attest-doc/./distance-to-clean never asks
# an adopter to re-attest autoharn's own docs. Add any NEW scaffold-written .md file to BOTH
# sides -- an out-of-frame audit already caught one addition (attestations/README.md) missing
# from that set on day one; this comment exists so the next one is not missed the same way.
cp "$TEMPLATES/GOVERNED_FILES.md" "$PROJECT_ROOT/.claude/GOVERNED_FILES.md"
cp "$TEMPLATES/apparatus.json" "$PROJECT_ROOT/.claude/apparatus.json"
cp "$TEMPLATES/APPARATUS.md" "$PROJECT_ROOT/.claude/APPARATUS.md"
sedsubst < "$TEMPLATES/HOOKS.md.tmpl" > "$PROJECT_ROOT/.claude/HOOKS.md"
# LAW section insertion: the __LAW_SECTION__ placeholder line in HOOKS.md.tmpl is replaced with
# LAW_SECTION_FILE's content (`r` reads the file in raw, so its own __AUTOHARN_ROOT__-style
# tokens were already resolved when it was generated above -- no double-substitution needed) and
# the placeholder line itself is dropped. LAW_SECTION_FILE is empty (`--no-law`) or a real
# section (default) -- either way this is a no-op-safe insert (an empty `r` inserts nothing).
sed -i -e "/^__LAW_SECTION__\$/r $LAW_SECTION_FILE" -e "/^__LAW_SECTION__\$/d" "$PROJECT_ROOT/.claude/HOOKS.md"
echo "wrote .claude/settings.json, governed_files.json, GOVERNED_FILES.md, apparatus.json, APPARATUS.md, HOOKS.md"

# Vendored skills (tracker item skill-vendoring-hack-rationalization, maintainer commission
# 2026-07-15): install every skill under bootstrap/templates/claude-skills/ into this
# deployment's own .claude/skills/, verbatim -- a plain recursive copy, never a template
# substitution (the skill body is not autoharn's to rewrite; see each skill's own PROVENANCE.md
# for the precedence fact: Claude Code resolves same-named skills enterprise > personal >
# project, so a user's personal copy of the same name silently shadows this one -- duplication
# is idempotent by that platform rule, not a drift hazard needing a warning mechanism here).
if [ -d "$TEMPLATES/claude-skills" ]; then
    mkdir -p "$PROJECT_ROOT/.claude/skills"
    for _skill_dir in "$TEMPLATES/claude-skills"/*/; do
        [ -d "$_skill_dir" ] || continue
        _skill_name="$(basename "$_skill_dir")"
        cp -r "$_skill_dir" "$PROJECT_ROOT/.claude/skills/$_skill_name"
        echo "wrote .claude/skills/$_skill_name (vendored skill, verbatim)"
    done
fi

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
    # COHERENCE PARTNER: this CLAUDE.md is in gates/doc_attestation_presence.py's
    # DEPLOYMENT_SCAFFOLD_OWNED_MD (see the .claude/ wiring block above's own coherence-partner
    # comment) -- it is autoharn's own prose, not an adopter's to re-attest.
    sedsubst < "$TEMPLATES/CLAUDE.md.tmpl" > "$PROJECT_ROOT/CLAUDE.md"
    sed -i -e "/^__LAW_SECTION__\$/r $LAW_SECTION_FILE" -e "/^__LAW_SECTION__\$/d" "$PROJECT_ROOT/CLAUDE.md"
    echo "wrote CLAUDE.md (governance preamble, auto-loaded at session start)"
fi
rm -f "$LAW_SECTION_FILE"

# the ten verbs (led, judge, pickup, audit, distance-to-clean, verify-commission, verify-chain,
# asof-export, attest-doc, doctor): thin shims,
# not frozen sed-substituted copies (BACKLOG maintainer ruling 2026-07-11, "runs are strictly
# linear" disposition 6, "live verbs"; audit and distance-to-clean joined the same way later,
# each a new template file rather than an edit to an existing live one -- see their own
# commissions; verify-commission (design/MAINT-GPG-TRUST-LAYER.md Rung 2) and asof-export
# (ledger item asof-export-inspection-copy, vestigial_documentation/design/FABLE-21CFR11-STANDING-ASSESSMENT.md §11.10(b))
# each follow the SAME distance-to-clean precedent -- a brand-new template file carries none of
# led.tmpl's freeze risk, so it is safe to add regardless of any live wired session elsewhere.
# doctor (ledger rows 1147/1148, virgin-experience round) is the newest of these, same precedent.
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
# COHERENCE PARTNER: keys/README.md and attestations/README.md below are BOTH in gates/
# doc_attestation_presence.py's DEPLOYMENT_SCAFFOLD_OWNED_MD (tracker item `abc-loop-offering`)
# -- they are autoharn's own templated prose, not an adopter's to re-attest. If a future template
# adds another scaffold-written .md file, add it to that set too (that module's own docstring
# names this exact scaffold as the coherence partner in the other direction).
echo "-- keys/ (this deployment's OWN GPG keyring; never autoharn's law/keys/) --"
mkdir -p "$PROJECT_ROOT/keys"
sedsubst < "$TEMPLATES/keys-README.md.tmpl" > "$PROJECT_ROOT/keys/README.md"
echo "wrote keys/README.md (AWAITING-KEY stub; commit THIS deployment's own signing key here)"

# attestations/ -- this deployment's OWN ADR-0017 A:B:C fresh-context attestation ledger
# (tracker item `abc-loop-offering`; design/ORCH-SPEC-ABC-OFFERING.md §3), deliberately separate
# from autoharn's own ledger of the same name, exactly the keys/ split above. The ledger FILE
# itself is created empty ONLY if it does not already exist -- the same idempotent,
# never-clobber-real-data posture this script's own header comment documents for the stamp
# secret ("skipped if a secret already exists, never silently rotated"): a --force re-scaffold
# must never truncate a ledger that already carries real attestation history.
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

# roles/ -- design/FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md deliverable 4 (commission ledger row
# 1663): an EMPTY scaffold + README stating the register-before-binding rule -- ADDITIVE ONLY,
# NO LINEAGE_CHAIN CONTACT (this block writes a directory and one templated README, nothing
# else; no kernel act, no ledger row -- a charter binds only when a LATER, explicit
# `tools/role_charter.py register` call writes the registration row, never at scaffold time).
# COHERENCE PARTNER: roles/README.md is in gates/doc_attestation_presence.py's
# DEPLOYMENT_SCAFFOLD_OWNED_MD (same set keys/README.md and attestations/README.md are already
# in, immediately above) -- it is autoharn's own templated prose, not an adopter's to re-attest.
echo "-- roles/ (this deployment's OWN role-charter directory; empty at birth, register-before-binding) --"
mkdir -p "$PROJECT_ROOT/roles"
sedsubst < "$TEMPLATES/roles-README.md.tmpl" > "$PROJECT_ROOT/roles/README.md"
echo "wrote roles/README.md"

echo "-- the ten project-local shims (the operator verbs led, judge, pickup, audit, distance-to-clean, attest-doc, asof-export, doctor, plus the two signing tools verify-commission and verify-chain): thin shims exec'ing autoharn's live templates --"
for verb in led judge pickup audit distance-to-clean verify-commission verify-chain attest-doc asof-export doctor; do
    cat > "$PROJECT_ROOT/$verb" <<SHIM
#!/bin/sh
HERE="\$(cd "\$(dirname "\$0")" && pwd)"
exec env PICKUP_DEPLOYMENT="\$HERE/deployment.json" $EXEC_ROOT/bootstrap/templates/$verb.tmpl "\$@"
SHIM
    chmod +x "$PROJECT_ROOT/$verb"
    echo "wrote $verb (shim -> $EXEC_ROOT/bootstrap/templates/$verb.tmpl)"
done

# ./legacy/ (design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md §5, ratified ledger row 1631):
# the direct-psql originals of the rebased verbs, whole and executable, demoted by placement
# never deleted -- "operator recovery when the boundary is down" (spec §5's own words). judge/
# audit/attest-doc/verify-commission/verify-chain do NOT rebase (spec §5's own closed
# enumeration: judge "drives clingo + differential against the world, not a ledger client in the
# boundary's sense"; audit is the SAME class -- engine/contemp_audit.py + engine/
# contemp_differential.py, clingo-driven -- so it stays in the single, unforked family above,
# never duplicated here) -- so this loop covers ONLY led/pickup/asof-export/distance-to-clean,
# each pointed at its OWN `legacy-<verb>.tmpl` sibling (bootstrap/templates/, the pre-rebase
# content, byte-identical save the one-line recovery header each carries at its own top).
#
# `led` IS THE ONE EXCEPTION (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md's retirement act,
# ledger row 1149/1150): `legacy-led.tmpl` is DELETED from this repository outright -- the
# boundary is mandatory at every birth now (no decline path left that needs a working direct-
# psql `led`), and `led principal *` closed the one family that was ever missing from the served
# path. `legacy/led` still gets a FILE here (destination.py's own AUTOHARN_COMPLETE classifier
# guarantee depends on its existence), but it is a one-line teaching refusal, never a working
# CLI -- pickup/asof-export/distance-to-clean are UNCHANGED, real shims, same as always.
echo "-- ./legacy/ (pickup/asof-export/distance-to-clean's direct-psql originals; led is a teaching-refusal stub, retired) --"
mkdir -p "$PROJECT_ROOT/legacy"
cat > "$PROJECT_ROOT/legacy/led" <<'STUB'
#!/bin/sh
echo "legacy/led: RETIRED 2026-07 (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md) -- every surface" >&2
echo "  serves through ./led now; the boundary is mandatory at every birth, and led principal *" >&2
echo "  (grant-competence/relate and their 11 siblings) closed the one family the served path" >&2
echo "  was ever missing. Use ./led instead." >&2
exit 1
STUB
chmod +x "$PROJECT_ROOT/legacy/led"
echo "wrote legacy/led (RETIRED teaching-refusal stub, design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md)"
for verb in pickup asof-export distance-to-clean; do
    cat > "$PROJECT_ROOT/legacy/$verb" <<SHIM
#!/bin/sh
HERE="\$(cd "\$(dirname "\$0")" && cd .. && pwd)"
exec env PICKUP_DEPLOYMENT="\$HERE/deployment.json" $EXEC_ROOT/bootstrap/templates/legacy-$verb.tmpl "\$@"
SHIM
    chmod +x "$PROJECT_ROOT/legacy/$verb"
    echo "wrote legacy/$verb (shim -> $EXEC_ROOT/bootstrap/templates/legacy-$verb.tmpl)"
done

# orchlog wrapper (deployment-orchlog-surfacing item, half (b) -- half (a), migrate printing the
# span, belongs to ./migrate and is untouched here). A DIFFERENT shape from the eight shims just
# above on purpose: orchlog is not a bootstrap/templates/*.tmpl instance-config resolver -- it is
# a repo-root verb (like led/judge/pickup themselves) that reads ITS OWN repo's git history
# (orchlog.d/*.md notes, keyed off each note's adding commit -- see orchlog's own module
# docstring), never this deployment's ledger, so it needs no PICKUP_DEPLOYMENT and no
# deployment.json at all. This wrapper only points it at the harness whose changelog a restarting
# deployment session wants to read: `exec harness orchlog --repo <harness-root>`, literally, with
# EXEC_ROOT (the live-exec harness tree every other verb/hook here already resolves against) as
# <harness-root> -- so a fresh session in THIS deployment can self-serve "what changed in autoharn
# since I was last here" without hand-relayed memo rows.
echo "-- orchlog wrapper (self-serve harness changelog, beside led/judge/pickup): exec's autoharn's own orchlog verb against $EXEC_ROOT, no deployment.json involved --"
cat > "$PROJECT_ROOT/orchlog" <<SHIM
#!/bin/sh
exec $EXEC_ROOT/orchlog --repo $EXEC_ROOT "\$@"
SHIM
chmod +x "$PROJECT_ROOT/orchlog"
echo "wrote orchlog (wrapper -> $EXEC_ROOT/orchlog --repo $EXEC_ROOT)"

if [ "$PIN" = "submodule" ]; then
    echo "-- --pin submodule: committing the pin + the verbs/hooks it points at --"
    (cd "$PROJECT_ROOT" && git add \
        led judge pickup audit distance-to-clean verify-commission verify-chain attest-doc asof-export doctor orchlog \
        .claude/settings.json .gitignore 2>/dev/null || true)
    if (cd "$PROJECT_ROOT" && git diff --cached --quiet) 2>/dev/null; then
        echo "   nothing new to commit (already committed by an earlier --force re-run)"
    else
        (cd "$PROJECT_ROOT" && git commit --quiet -m "pin autoharn@$AUTOHARN_COMMIT_SHA via .autoharn submodule (bootstrap/new-project.sh --pin submodule)")
        echo "   committed: $(cd "$PROJECT_ROOT" && git log -1 --oneline)"
    fi
fi

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
    echo " ./verify-chain, ./attest-doc, ./asof-export, ./doctor, ./orchlog are ready to use from inside that session; read"
    echo " $PROJECT_ROOT/.claude/HOOKS.md and replace its UNWITNESSED marks as you exercise each"
    echo " command. (./doctor answers \"is this world set up right?\" in one witnessed call --"
    echo " read it first if anything below looks off. ./orchlog lists the harness changelog --"
    echo " notes on things a restarting session would want to know about autoharn itself, e.g."
    echo " \`./orchlog\` or \`./orchlog since <sha>\`.)"
    echo ""
    echo "----- BEGIN MAINTAINER SIGNING BLOCK -----"
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
    echo "FORGED-OR-CORRUPT, per user-guide/USER-GPG-TRUST-LAYER-FAQ.md) -- exercise the ceremony with a"
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
    echo "before it will print anything: user-guide/USER-GPG-TRUST-LAYER-FAQ.md."
    echo "----- END MAINTAINER SIGNING BLOCK -----"
else
    echo "  1. Apply a kernel lineage to $DB/$SCHEMA/$KERN/$ROLE if not already applied (kernel/lineage/, autoharn)."
    echo "  2. Provision the stamp secret -- see $PROJECT_ROOT/.claude/HOOKS.md (marked UNWITNESSED until you run it)."
    echo "  3. cd $PROJECT_ROOT && ./led decision \"...\"  /  ./judge  /  ./pickup"
    echo "  4. Read $PROJECT_ROOT/.claude/HOOKS.md and replace its UNWITNESSED marks as you exercise each command."
    if [ "$PIN" = "submodule" ]; then
        echo ""
        echo "PINNED DEPLOYMENT: every verb above and every hook in .claude/settings.json now runs"
        echo "out of $PROJECT_ROOT/.autoharn (git submodule, pinned to $AUTOHARN_COMMIT_SHA) -- a"
        echo "merge to autoharn's own working branch will NEVER change this deployment's behavior"
        echo "again. To take a newer autoharn deliberately: bootstrap/upgrade-submodule.sh"
        echo "$PROJECT_ROOT <new-sha> (from the autoharn checkout, not from inside $PROJECT_ROOT)."
    fi
fi
