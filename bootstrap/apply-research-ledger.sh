#!/bin/sh
# apply-research-ledger.sh — the operator's/maintainer's ONE scripted step for applying
# stores/001_research_ledger.sql (the PROJECT-AGNOSTIC measurement-provenance ledger:
# core.project/core.session + research.instrument/research.reading/research.finding + the
# derived research.finding_confirmed view) to the STANDING `research` database.
#
# Usage:
#   bootstrap/apply-research-ledger.sh
#   RL_PGHOST=... RL_DB=... bootstrap/apply-research-ledger.sh    (override target, same as
#                                                                   filing/record_reading.py's
#                                                                   own env-var convention)
#
# What this does NOT do, on purpose (CLAUDE.md ORCHESTRATION: applying to a deployment is the
# operator's/maintainer's act, always explicit — this script PRESERVES that, it does not relax
# it, matching bootstrap/apply-delta.sh's posture for kernel lineage deltas):
#   - it never guesses the target silently past its own printed defaults — RL_PGHOST/RL_DB are
#     named in this file's own usage text, and the resolved host/db are printed before anything
#     runs.
#   - it never applies without an explicit, TYPED confirmation from the operator (no --yes, no
#     env-var override that skips the prompt) — a mismatch aborts with NO db action taken.
#   - it PREFLIGHTS for "already applied" and refuses loudly rather than letting a second run
#     hit psql's own "relation already exists" mid-transaction (idempotent-or-refusing, per the
#     2026-07-11 commission: this script is neither silently idempotent — 001's CREATE TABLE
#     statements are not IF NOT EXISTS, a second literal apply is not a no-op — nor does it fail
#     messily; it checks first and says so in one clear sentence).
#
# What this DOES automate: resolving host/db from one place instead of hand-typed strings,
# printing the fully-resolved psql command before doing anything, preflighting for a prior
# apply, and running the (transaction-wrapped — BEGIN...COMMIT, unlike the kernel lineage
# deltas apply-delta.sh applies) DDL as one atomic unit: a mid-file failure ROLLS BACK cleanly,
# it does not leave a partial schema the way an un-transaction-wrapped delta could.
#
# This script touches NO file under stores/ (read-only) and applies to NO database unless the
# operator types the resolved db name back at the confirmation prompt.
set -eu

AUTOHARN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DDL="$AUTOHARN_ROOT/stores/001_research_ledger.sql"
[ -f "$DDL" ] || { echo "apply-research-ledger.sh: DDL not found at $DDL" >&2; exit 1; }

# --- resolve host/db: explicit env override, else this checkout's own deployment.json 'host'
# field, else a loud refusal -- mirrors filing/record_reading.py's RL_PGHOST resolution (via
# filing/pghost_resolve.py, the ONE home) so the writer and the apply script agree on where
# "the standing research db" is without a second hand-typed pair of strings, and neither ever
# silently defaults to any one host. ---
HOST="${RL_PGHOST:-}"
DEP="${LEDGER_DEPLOYMENT:-$AUTOHARN_ROOT/deployment.json}"
PY="$HOME/w/vdc/venvs/generic/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"
if [ -z "$HOST" ] && [ -f "$DEP" ] && [ -n "$PY" ]; then
    HOST="$("$PY" -c "
import json, sys
try:
    with open(sys.argv[1]) as f:
        print(json.load(f).get('host') or '')
except Exception:
    print('')
" "$DEP" 2>/dev/null)"
fi
if [ -z "$HOST" ]; then
    echo "apply-research-ledger.sh: REFUSED -- no Postgres host resolved. Set RL_PGHOST, or" >&2
    echo "  place a deployment.json with a 'host' field at $DEP (copy deployment.json.example" >&2
    echo "  and fill in your own values; see README.md 'Configuration'). Never defaulting to" >&2
    echo "  any host." >&2
    exit 1
fi
DB="${RL_DB:-research}"

echo "== apply-research-ledger.sh: target =="
echo "   host=$HOST db=$DB  (override with RL_PGHOST / RL_DB env vars)"
echo ""

# --- preflight: refuse loudly if this DDL looks already applied, rather than letting a second
# literal run hit "relation core.project already exists" mid-transaction. Checked as the
# unprivileged connecting role would see it (a missing schema reads as "not applied", exactly
# the case this script exists to handle; a permissions problem surfaces on the real apply
# below, not swallowed here). ---
set +e
ALREADY="$(psql -h "$HOST" -d "$DB" -tA -c \
    "SELECT to_regclass('core.project') IS NOT NULL OR to_regclass('research.reading') IS NOT NULL;" 2>&1)"
PREFLIGHT_STATUS=$?
set -e
if [ "$PREFLIGHT_STATUS" -ne 0 ]; then
    echo "apply-research-ledger.sh: preflight query FAILED — could not reach $HOST/$DB to check prior state:" >&2
    echo "$ALREADY" >&2
    echo "ABORTED — no action taken." >&2
    exit 1
fi
if [ "$ALREADY" = "t" ]; then
    echo "apply-research-ledger.sh: REFUSING — core.project or research.reading already exists on" >&2
    echo "$HOST/$DB. This script applies stores/001_research_ledger.sql LITERALLY (CREATE TABLE," >&2
    echo "not CREATE TABLE IF NOT EXISTS) — a second run would fail mid-transaction. If this is a" >&2
    echo "genuine re-apply after a rollback, verify by hand (psql -h $HOST -d $DB -c '\\dt core.*'" >&2
    echo "'\\dt research.*') before deciding how to proceed; this script does not attempt a" >&2
    echo "diff/upgrade path. ABORTED — no action taken." >&2
    exit 1
fi

echo "-- resolved apply command --"
echo "psql -h $HOST -d $DB -v ON_ERROR_STOP=1 -f $DDL"
echo ""
echo "This will run the above against a LIVE deployment: db '$DB' @ host '$HOST', creating"
echo "schemas core/research with 5 tables, 1 derived view, and 2 triggers (see the DDL's own"
echo "header + closing 'honest ledger of strength' comment if you have not read it already)."
echo "The DDL is transaction-wrapped (BEGIN...COMMIT): a mid-file failure rolls back cleanly,"
echo "leaving NO partial schema — this apply is atomic, unlike a kernel lineage delta."
echo ""
printf 'Type the database name (%s) to confirm, or anything else to abort: ' "$DB"
read -r CONFIRM
if [ "$CONFIRM" != "$DB" ]; then
    echo "apply-research-ledger.sh: confirmation '$CONFIRM' did not match db '$DB' -- ABORTED, no action taken." >&2
    exit 1
fi

echo ""
echo "-- applying stores/001_research_ledger.sql to $HOST/$DB --"
set +e
OUTPUT="$(psql -h "$HOST" -d "$DB" -v ON_ERROR_STOP=1 -f "$DDL" 2>&1)"
STATUS=$?
set -e
echo "$OUTPUT"

if [ "$STATUS" -ne 0 ]; then
    echo "" >&2
    echo "apply-research-ledger.sh: psql FAILED (exit $STATUS) applying 001_research_ledger.sql to $HOST/$DB." >&2
    echo "The DDL is transaction-wrapped, so this should mean NOTHING landed (a clean ROLLBACK) —" >&2
    echo "verify with '\\dt core.*'/'\\dt research.*' before re-running; do not assume a partial state." >&2
    exit 1
fi

echo ""
echo "-- apply succeeded --"
DATE_UTC="$(date -u +%Y-%m-%d)"
echo ""
echo "REMINDER: ledger the apply so the trail stays true (BACKLOG.md is retired; the tracker is the trail):"
echo "  ./led decision \"001_research_ledger.sql APPLIED $DATE_UTC ($HOST/$DB), transaction-wrapped COMMIT witnessed\""
