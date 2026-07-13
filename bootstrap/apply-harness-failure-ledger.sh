#!/bin/sh
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-13T16:51:19Z
#   last-change: 2026-07-13T16:51:19Z
#   contributors: 3c50e030/main
# <<< PROVENANCE-STAMP <<<

# apply-harness-failure-ledger.sh — the operator's/maintainer's ONE scripted step for applying
# stores/008_harness_failure_ledger.sql (the harness_failure schema: record/disposition + the
# derived harness_failure.open_records view) to the STANDING `research` database — the SAME db
# stores/001_research_ledger.sql already uses, as a second auxiliary schema
# (design/ORCH-HARNESS-FAILURE-LEDGER.md, "Why research, not a new database").
#
# Usage:
#   bootstrap/apply-harness-failure-ledger.sh
#   RL_PGHOST=... RL_DB=... bootstrap/apply-harness-failure-ledger.sh    (override target, same
#                                                                         env-var convention as
#                                                                         apply-research-ledger.sh
#                                                                         and filing/record_reading.py)
#
# What this does NOT do, on purpose (CLAUDE.md ORCHESTRATION: applying to a deployment is the
# operator's/maintainer's act, always explicit — this script PRESERVES that, it does not relax
# it, matching bootstrap/apply-research-ledger.sh's own posture for stores/001, which itself
# matches bootstrap/apply-delta.sh's posture for kernel lineage deltas):
#   - it never guesses the target silently past its own printed defaults — RL_PGHOST/RL_DB are
#     named in this file's own usage text, and the resolved host/db are printed before anything
#     runs.
#   - it never applies without an explicit, TYPED confirmation from the operator (no --yes, no
#     env-var override that skips the prompt) — a mismatch aborts with NO db action taken.
#   - it PREFLIGHTS for "already applied" and refuses loudly rather than letting a second run
#     hit psql's own "relation already exists" mid-transaction (idempotent-or-refusing, the same
#     posture apply-research-ledger.sh established for 001: this script is neither silently
#     idempotent — 008's CREATE TABLE statements are not IF NOT EXISTS, a second literal apply
#     is not a no-op — nor does it fail messily; it checks first and says so in one clear
#     sentence).
#
# What this DOES automate: resolving host/db from one place instead of hand-typed strings,
# printing the fully-resolved psql command before doing anything, preflighting for a prior
# apply, and running the (transaction-wrapped — BEGIN...COMMIT, unlike the kernel lineage
# deltas apply-delta.sh applies) DDL as one atomic unit: a mid-file failure ROLLS BACK cleanly,
# it does not leave a partial schema the way an un-transaction-wrapped delta could.
#
# This script touches NO file under stores/ (read-only) and applies to NO database unless the
# operator types the resolved db name back at the confirmation prompt. It never inserts the
# nine ready-to-INSERT backfill records design/ORCH-HARNESS-FAILURE-LEDGER.md's appendix lists —
# those are data, applied separately, by hand, at the maintainer's own discretion, exactly as
# this script only ever creates STRUCTURE.
set -eu

AUTOHARN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DDL="$AUTOHARN_ROOT/stores/008_harness_failure_ledger.sql"
[ -f "$DDL" ] || { echo "apply-harness-failure-ledger.sh: DDL not found at $DDL" >&2; exit 1; }

# --- resolve host/db: explicit env override, else the store's own stated defaults (mirrors
# apply-research-ledger.sh / filing/record_reading.py's RL_PGHOST/RL_DB so every writer and
# apply script agree on where "the standing research db" is without a second hand-typed pair
# of strings). ---
HOST="${RL_PGHOST:-192.168.122.1}"
DB="${RL_DB:-research}"

echo "== apply-harness-failure-ledger.sh: target =="
echo "   host=$HOST db=$DB  (override with RL_PGHOST / RL_DB env vars)"
echo ""

# --- preflight: refuse loudly if this DDL looks already applied, rather than letting a second
# literal run hit "relation already exists" mid-transaction. Checked as the unprivileged
# connecting role would see it (a missing schema reads as "not applied", exactly the case this
# script exists to handle; a permissions problem surfaces on the real apply below, not
# swallowed here). Also refuses if core.project/core.session (001's own tables, a hard
# prerequisite — harness_failure.record REFERENCES core.project) are ABSENT, since that means
# 001 has not been applied yet and 008 would fail immediately on its first CREATE TABLE. ---
set +e
PREREQ="$(psql -h "$HOST" -d "$DB" -tA -c \
    "SELECT to_regclass('core.project') IS NOT NULL;" 2>&1)"
PREREQ_STATUS=$?
set -e
if [ "$PREREQ_STATUS" -ne 0 ]; then
    echo "apply-harness-failure-ledger.sh: preflight query FAILED — could not reach $HOST/$DB to check prior state:" >&2
    echo "$PREREQ" >&2
    echo "ABORTED — no action taken." >&2
    exit 1
fi
if [ "$PREREQ" != "t" ]; then
    echo "apply-harness-failure-ledger.sh: REFUSING — core.project does not exist on $HOST/$DB." >&2
    echo "stores/008_harness_failure_ledger.sql REFERENCES core.project (built by stores/" >&2
    echo "001_research_ledger.sql) for deployment identity — apply 001 first via" >&2
    echo "bootstrap/apply-research-ledger.sh, then re-run this script. ABORTED — no action taken." >&2
    exit 1
fi

set +e
ALREADY="$(psql -h "$HOST" -d "$DB" -tA -c \
    "SELECT to_regclass('harness_failure.record') IS NOT NULL OR to_regclass('harness_failure.disposition') IS NOT NULL;" 2>&1)"
PREFLIGHT_STATUS=$?
set -e
if [ "$PREFLIGHT_STATUS" -ne 0 ]; then
    echo "apply-harness-failure-ledger.sh: preflight query FAILED — could not reach $HOST/$DB to check prior state:" >&2
    echo "$ALREADY" >&2
    echo "ABORTED — no action taken." >&2
    exit 1
fi
if [ "$ALREADY" = "t" ]; then
    echo "apply-harness-failure-ledger.sh: REFUSING — harness_failure.record or" >&2
    echo "harness_failure.disposition already exists on $HOST/$DB. This script applies" >&2
    echo "stores/008_harness_failure_ledger.sql LITERALLY (CREATE TABLE, not CREATE TABLE IF NOT" >&2
    echo "EXISTS) — a second run would fail mid-transaction. If this is a genuine re-apply after a" >&2
    echo "rollback, verify by hand (psql -h $HOST -d $DB -c '\\dt harness_failure.*') before" >&2
    echo "deciding how to proceed; this script does not attempt a diff/upgrade path. ABORTED — no" >&2
    echo "action taken." >&2
    exit 1
fi

echo "-- resolved apply command --"
echo "psql -h $HOST -d $DB -v ON_ERROR_STOP=1 -f $DDL"
echo ""
echo "This will run the above against a LIVE deployment: db '$DB' @ host '$HOST', creating"
echo "schema harness_failure with 2 tables, 1 derived view, and 4 triggers (see the DDL's own"
echo "header + closing 'honest ledger of strength' comment if you have not read it already)."
echo "The DDL is transaction-wrapped (BEGIN...COMMIT): a mid-file failure rolls back cleanly,"
echo "leaving NO partial schema — this apply is atomic, unlike a kernel lineage delta."
echo ""
echo "This does NOT insert the nine ready-to-INSERT backfill records"
echo "design/ORCH-HARNESS-FAILURE-LEDGER.md's appendix lists — structure only, exactly as"
echo "stores/001_research_ledger.sql's own apply never inserted a research.reading row."
echo ""
printf 'Type the database name (%s) to confirm, or anything else to abort: ' "$DB"
read -r CONFIRM
if [ "$CONFIRM" != "$DB" ]; then
    echo "apply-harness-failure-ledger.sh: confirmation '$CONFIRM' did not match db '$DB' -- ABORTED, no action taken." >&2
    exit 1
fi

echo ""
echo "-- applying stores/008_harness_failure_ledger.sql to $HOST/$DB --"
set +e
OUTPUT="$(psql -h "$HOST" -d "$DB" -v ON_ERROR_STOP=1 -f "$DDL" 2>&1)"
STATUS=$?
set -e
echo "$OUTPUT"

if [ "$STATUS" -ne 0 ]; then
    echo "" >&2
    echo "apply-harness-failure-ledger.sh: psql FAILED (exit $STATUS) applying 008_harness_failure_ledger.sql to $HOST/$DB." >&2
    echo "The DDL is transaction-wrapped, so this should mean NOTHING landed (a clean ROLLBACK) —" >&2
    echo "verify with '\\dt harness_failure.*' before re-running; do not assume a partial state." >&2
    exit 1
fi

echo ""
echo "-- apply succeeded --"
DATE_UTC="$(date -u +%Y-%m-%d)"
echo ""
echo "REMINDER: ledger the apply so the trail stays true (BACKLOG.md is retired; the tracker is the trail):"
echo "  ./led decision \"008_harness_failure_ledger.sql APPLIED $DATE_UTC ($HOST/$DB), transaction-wrapped COMMIT witnessed\""
