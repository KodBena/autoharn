#!/bin/sh
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T13:48:20Z
#   last-change: 2026-07-09T13:48:20Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

# apply-delta.sh — the operator's scriptable step for applying ONE kernel lineage delta
# (kernel/lineage/sNN-*.sql, e.g. s21-session-aware-distinctness.sql) to an EXISTING world.
#
# Usage:
#   bootstrap/apply-delta.sh <world-dir> <delta.sql>
#
# What this does NOT do, on purpose (CLAUDE.md ORCHESTRATION: "applying a lineage delta to a
# deployment is the operator's/maintainer's act, always with every -v var explicit" — this
# script PRESERVES that spirit, it does not relax it):
#   - it never guesses db/host/schema/kern: <world-dir>/deployment.json is the ONE source
#     (filing/deployment_record.py, ADR-0012 P1) and a missing file or missing/malformed key is
#     refused loudly, with the same teach-text deployment_record.py already carries — never a
#     silent default.
#   - it never applies without an explicit, TYPED confirmation from the operator (no --yes, no
#     env-var override that skips the prompt) — a mismatch aborts with NO db action taken.
#   - it never wraps the delta in a transaction it doesn't already declare (kernel/lineage/sNN
#     files are NOT transaction-wrapped by convention — s21's own file is a bare sequence of
#     CREATE OR REPLACE / DROP+CREATE statements); a mid-file error can leave a PARTIAL apply,
#     and this script says so loudly on failure rather than papering over it.
#
# What this DOES automate: resolving the four vars from one file instead of four hand-typed
# strings the operator must keep in agreement (P1 again), printing the fully-resolved psql
# command before doing anything, and — on success — appending a dated one-line PROVENANCE
# record to the world's .claude/HOOKS.md if that file exists (never creating one).
#
# This script touches NO file under kernel/ (read-only) and applies to NO schema unless the
# operator both names it as <world-dir> and types its schema name back at the confirmation
# prompt.
set -eu

usage() {
    echo "usage: $0 <world-dir> <delta.sql>" >&2
    echo "  <world-dir>   a scaffolded project directory with its own deployment.json" >&2
    echo "  <delta.sql>   a kernel lineage delta, e.g. kernel/lineage/s21-session-aware-distinctness.sql" >&2
    exit 2
}

[ $# -eq 2 ] || usage
WORLD_DIR="$1"
DELTA="$2"

[ -d "$WORLD_DIR" ] || { echo "apply-delta.sh: world dir not found: $WORLD_DIR" >&2; exit 1; }
[ -f "$DELTA" ] || { echo "apply-delta.sh: delta file not found: $DELTA" >&2; exit 1; }

AUTOHARN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$HOME/w/vdc/venvs/generic/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"

WORLD_ROOT="$(cd "$WORLD_DIR" && pwd)"
DEPLOYMENT="$WORLD_ROOT/deployment.json"
DELTA_ABS="$(cd "$(dirname "$DELTA")" && pwd)/$(basename "$DELTA")"
DELTA_BASENAME="$(basename "$DELTA")"

echo "== apply-delta.sh: resolving $WORLD_ROOT/deployment.json =="

# --- resolve db/host/schema/kern/role; refuse loudly (deployment_record.py's own teach-text,
# ONE home for this validation per ADR-0012 P1 -- never a second hand-rolled JSON reader here)
# and NEVER guess a missing/malformed field. ---
if ! RESOLVED="$("$PY" - "$DEPLOYMENT" <<PYEOF
import sys
sys.path.insert(0, "$AUTOHARN_ROOT/filing")
from deployment_record import load_deployment, DeploymentError

try:
    rec = load_deployment(sys.argv[1])
except DeploymentError as e:
    print(f"apply-delta.sh: REFUSING -- {e}", file=sys.stderr)
    sys.exit(1)
print(f"{rec.db}\t{rec.host}\t{rec.schema}\t{rec.kern}\t{rec.role}")
PYEOF
)"; then
    exit 1
fi

DB="$(printf '%s' "$RESOLVED" | cut -f1)"
HOST="$(printf '%s' "$RESOLVED" | cut -f2)"
SCHEMA="$(printf '%s' "$RESOLVED" | cut -f3)"
KERN="$(printf '%s' "$RESOLVED" | cut -f4)"
ROLE="$(printf '%s' "$RESOLVED" | cut -f5)"

echo "   resolved: db=$DB host=$HOST schema=$SCHEMA kern=$KERN role=$ROLE"
echo ""
echo "-- resolved apply command (every -v var spelled out; role is passed though this delta may"
echo "   not declare it -- an unused -v var is harmless, and this keeps the invocation identical"
echo "   in shape across every delta this script is pointed at) --"
echo "psql -h $HOST -d $DB -v ON_ERROR_STOP=1 -v schema=$SCHEMA -v kern=$KERN -v role=$ROLE -f $DELTA_ABS"
echo ""
echo "This will run the above against a LIVE deployment: schema '$SCHEMA' / kernel schema '$KERN'"
echo "on db '$DB' @ host '$HOST'. Kernel lineage deltas are NOT transaction-wrapped -- read"
echo "$DELTA_BASENAME yourself first if you have not already."
echo ""
printf 'Type the schema name (%s) to confirm, or anything else to abort: ' "$SCHEMA"
read -r CONFIRM
if [ "$CONFIRM" != "$SCHEMA" ]; then
    echo "apply-delta.sh: confirmation '$CONFIRM' did not match schema '$SCHEMA' -- ABORTED, no action taken." >&2
    exit 1
fi

echo ""
echo "-- applying $DELTA_BASENAME to $SCHEMA/$KERN --"
set +e
OUTPUT="$(psql -h "$HOST" -d "$DB" -v ON_ERROR_STOP=1 -v schema="$SCHEMA" -v kern="$KERN" -v role="$ROLE" \
    -f "$DELTA_ABS" 2>&1)"
STATUS=$?
set -e
echo "$OUTPUT"

if [ "$STATUS" -ne 0 ]; then
    echo "" >&2
    echo "apply-delta.sh: psql FAILED (exit $STATUS) applying $DELTA_BASENAME to $SCHEMA/$KERN." >&2
    echo "This delta is NOT transaction-wrapped, so a mid-file error can leave a PARTIAL apply" >&2
    echo "(some CREATE OR REPLACE/DROP+CREATE statements may have landed, others not)." >&2
    echo "Do NOT re-run this blind. Paste the output above into BACKLOG.md / to the orchestrator" >&2
    echo "for a considered diagnosis of this schema's actual state before touching it again." >&2
    exit 1
fi

echo ""
echo "-- apply succeeded --"

DATE_UTC="$(date -u +%Y-%m-%d)"
RECORD_LINE="- **APPLIED** \`$DELTA_BASENAME\` $DATE_UTC (via bootstrap/apply-delta.sh, schema $SCHEMA/$KERN)"
HOOKS_MD="$WORLD_ROOT/.claude/HOOKS.md"

if [ -f "$HOOKS_MD" ]; then
    if "$PY" - "$HOOKS_MD" "$RECORD_LINE" <<'PYEOF'
import sys

path, line = sys.argv[1], sys.argv[2]
text = open(path, encoding="utf-8").read()
marker = "## PROVENANCE\n"
idx = text.find(marker)
if idx == -1:
    print("apply-delta.sh: no '## PROVENANCE' section found in this file.", file=sys.stderr)
    sys.exit(1)
insert_at = idx + len(marker)
rest = text[insert_at:]
if rest.startswith("\n"):
    insert_at += 1
    rest = rest[1:]
new_text = text[:insert_at] + line + "\n" + rest
open(path, "w", encoding="utf-8").write(new_text)
PYEOF
    then
        echo "-- recorded in $HOOKS_MD's PROVENANCE section: $RECORD_LINE --"
    else
        echo "apply-delta.sh: could not record into $HOOKS_MD (see message above) -- NOT modified." >&2
        echo "File this line yourself: $RECORD_LINE" >&2
    fi
else
    echo "$HOOKS_MD does not exist -- creating nothing. File this line yourself, wherever this"
    echo "world's provenance is tracked: $RECORD_LINE"
fi

echo ""
echo "REMINDER: add a one-line BACKLOG.md note (e.g. \"$DELTA_BASENAME APPLIED $DATE_UTC ($SCHEMA)\")"
echo "so BACKLOG's own apply-status entry for this delta stays true."
