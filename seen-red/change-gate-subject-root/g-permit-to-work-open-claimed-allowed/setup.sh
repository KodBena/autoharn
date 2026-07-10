#!/usr/bin/env bash
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-10T19:33:31Z
#   last-change: 2026-07-10T19:33:31Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

# Scratch schema for the permit-to-work "open+claimed -> allowed per existing rules" case (1b,
# BACKLOG "Run-5 forensics" 2026-07-10): applies the s22 lineage delta, opens AND claims one work
# item (permit-to-work satisfied), THEN also inserts an ordinary ticket entry declaring the target
# file (the PRE-EXISTING ticket/window logic this fix composes in front of -- permit-to-work alone
# is not sufficient for an overall ALLOW; the ticket requirement is unchanged and still applies).
set -euo pipefail
PGHOST=192.168.122.1
DB=toy
SCHEMA=hookprobe_ptw_g
KERN=hookprobe_ptw_g_kernel
ROLE=hookprobe_ptw_g_rw
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
  "SET ROLE $ROLE; INSERT INTO $SCHEMA.ledger(kind, work_slug, work_title, statement) VALUES ('work_opened','fixture-item','Fixture item','work_opened: fixture-item -- Fixture item');"
psql -h "$PGHOST" -d "$DB" -v ON_ERROR_STOP=1 -c \
  "SET ROLE $ROLE; INSERT INTO $SCHEMA.ledger(kind, work_slug, statement) VALUES ('work_claimed','fixture-item','work_claimed: fixture-item');"
psql -h "$PGHOST" -d "$DB" -v ON_ERROR_STOP=1 -c \
  "SET ROLE $ROLE; INSERT INTO $SCHEMA.ledger(kind, statement, evidence) VALUES ('decision','permit-to-work seen-red fixture ticket','files: fixture_target_ptw_g.py');"
