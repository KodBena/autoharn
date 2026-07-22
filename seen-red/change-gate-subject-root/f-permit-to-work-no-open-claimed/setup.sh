#!/usr/bin/env bash
# Scratch schema for the permit-to-work "no open+claimed item" case (1a, BACKLOG "Run-5
# forensics" 2026-07-10): applies the s22 lineage delta to a throwaway schema in the toy db, then
# opens (but never claims) one work item -- has_work_item_layer() must see the view, and
# has_open_claimed_work_item() must see it as False.
set -euo pipefail
PGHOST="${PGHOST:?PGHOST not set -- run this fixture via run_fixtures.py, which resolves it via seen-red/_fixture_env.py (EPISTEMIC_PGHOST/HARNESS_PGHOST or deployment.json), never a literal host default}"
DB=toy
SCHEMA=hookprobe_ptw_f
KERN=hookprobe_ptw_f_kernel
ROLE=hookprobe_ptw_f_rw
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
LINEAGE="$REPO/kernel/lineage"

psql -h "$PGHOST" -d "$DB" -c \
  "DROP SCHEMA IF EXISTS $SCHEMA CASCADE; DROP SCHEMA IF EXISTS $KERN CASCADE; DROP OWNED BY $ROLE; DROP ROLE IF EXISTS $ROLE;" \
  >/dev/null 2>&1 || true

for f in high_watermark_1.sql s20-obligation-grants-and-view-refresh.sql \
         s21-session-aware-distinctness.sql s22-work-item-ledger.sql; do
  psql -h "$PGHOST" -d "$DB" -v ON_ERROR_STOP=1 -v schema="$SCHEMA" -v kern="$KERN" -v role="$ROLE" \
    -f "$LINEAGE/$f"
done

psql -h "$PGHOST" -d "$DB" -v ON_ERROR_STOP=1 -c \
  "SET ROLE $ROLE; INSERT INTO $SCHEMA.ledger(kind, work_slug, work_title, statement) VALUES ('work_opened','fixture-item','Fixture item (unclaimed)','work_opened: fixture-item -- Fixture item (unclaimed)');"
