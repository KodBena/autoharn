# ent s29 in-place migration — apply runbook (rehearsed 2026-07-14 on ent's real data)

STATUS: rehearsal-witnessed on scratch pair `s29reh`/`s29reh_kernel` inside the `ent` db.
PRECONDITION THAT IS NOT MINE TO WAIVE: the delta file this runbook applies is
`s29-INPLACE-CANDIDATE-notvalid.sql` (this directory) — the ratified s29 file
(worktree-agent-a4f06b5d7e62f03c2 @ 92e1c75, `kernel/lineage/s29-obligation-item-key-and-typed-close.sql`)
plus exactly one clause: `NOT VALID` on constraint `work_review_disposition_kind_shape`.
The ratified file as-is CANNOT apply to ent (witnessed: `ERROR: check constraint
"work_review_disposition_kind_shape" of relation "ledger" is violated by some row` —
157 historical work_closed rows predate the disposition type). The NOT VALID variant
requires maintainer ratification before live use. Everything below was executed and
witnessed on scratch; expected outputs are the actual observed ones.

Connection facts (from ~/ent/deployment.json): host=192.168.122.1 db=ent schema=ent
kern=ent_kernel role=ent_rw. Apply runs as the schema-owner-capable OS user (bork).

## Step 0 — session gap check (hard precondition)

    for pid in $(pgrep -f claude); do readlink -f /proc/$pid/cwd; done | grep -q "^/home/bork/ent" \
      && { echo "LIVE SESSION UNDER ~/ent — ABORT"; exit 1; } || echo "gap open"

Expected: `gap open`. (Idle zsh shells cwd'd there are fine; `claude` processes are not.)

## Step 1 — fresh pre-apply dump (the rollback artifact)

    TS=$(date +%Y%m%d-%H%M%S)
    pg_dump -h 192.168.122.1 -U bork -d ent -n ent -n ent_kernel \
      -f ~/backups/ent-pre-s29-live-$TS.sql
    tail -3 ~/backups/ent-pre-s29-live-$TS.sql   # expect "PostgreSQL database dump complete"
    test -s ~/backups/ent-pre-s29-live-$TS.sql || { echo "EMPTY DUMP — ABORT"; exit 1; }

Rehearsal witness: 2,751,301 bytes, 8 COPY blocks, both CREATE SCHEMA stanzas.

## Step 2 — pre-apply baseline (save these three outputs)

    psql -h 192.168.122.1 -U bork -d ent -tA <<'SQL'
    select count(*) || '|' || md5(string_agg(md5(l::text), '' order by l.id)) from ent.ledger l;
    select count(*) from ent.countersign_obligation;   -- expect 1
    select count(*) from ent.review_gap;               -- expect 0
    SQL

Rehearsal-era baseline: ledger `1889|e9800455f514c89f1382ae8572fceaa4` (WILL differ if
ent has written rows since 2026-07-14 22:01 — recompute, don't compare to this literal).

    cd ~/ent && ./verify-chain

Expected: `verify-chain: INTACT -- <N> row(s) walked, head id=<H> hash=<...>` then
`TAIL-COVERAGE-CONFIRMED`, exit 0. ABORT on anything else.

## Step 3 — the apply (single transaction; failure = automatic full rollback)

    psql -h 192.168.122.1 -U bork -d ent -v ON_ERROR_STOP=1 --single-transaction \
      -v schema=ent -v kern=ent_kernel -v role=ent_rw \
      -f s29-INPLACE-CANDIDATE-notvalid.sql

Expected output (witnessed on scratch): a run of ALTER TABLE / COMMENT lines, several
benign `NOTICE: constraint "..." does not exist, skipping` (idempotent DROP IF EXISTS),
2x CREATE FUNCTION, 2x DROP TRIGGER + CREATE TRIGGER, 4x CREATE VIEW, 1x GRANT, exit 0.
Any ERROR ⇒ the transaction rolled back whole; the schema is unchanged; stop and report.

## Step 4 — post-apply verification (all must hold; any miss ⇒ investigate, restore if needed)

    psql -h 192.168.122.1 -U bork -d ent -tA <<'SQL'
    -- 4a history byte-identity: recompute the Step-2 ledger digest over the PRE-EXISTING
    --    columns; must equal Step 2's value exactly (count and md5)
    select count(*) || '|' || md5(string_agg(md5(ROW(
      l.id,l.ts,l.session,l.kind,l.statement,l.rationale,l.status,l.evidence,l.confidence,
      l.supersedes,l.refs,l.concern,l.enacts,l.actor,l.regards,l.amends,l.amends_scope,l.answers,
      l.stamp_session,l.stamp_agent,l.stamp_ts,l.stamp_hmac,l.stamp_verified,
      l.work_slug,l.work_title,l.work_depends_on,l.work_resolution,l.work_witness,
      l.stamp_invocation,l.event_declared_ts,l.row_hash,l.work_parent)::text), '' order by l.id))
    from ent.ledger l;
    -- 4b nothing backfilled: expect 0
    select count(*) from ent.ledger
     where work_review_disposition is not null or work_review_ref is not null
        or work_strict_close is not null;
    -- 4c legacy obligation machinery untouched: expect 1 then 0
    select count(*) from ent.countersign_obligation;
    select count(*) from ent.review_gap;
    -- 4d new machinery present and resolving: expect 0 (no deferred closes yet),
    --    then a row count equal to ledger_current's, then 160+ work items
    select count(*) from ent.work_review_gap;
    select count(*) from ent.ledger_current;
    select count(*) from ent.work_item_current;
    -- 4e review_detail grade column present, historical rows untouched: expect 0
    select count(*) from ent.review_detail where discharge_grade is not null;
    SQL
    cd ~/ent && ./verify-chain    # expect INTACT + TAIL-COVERAGE-CONFIRMED again, exit 0
    # (compute_row_hash's fixed column list excludes the three new columns — witnessed:
    #  chain INTACT post-apply with identical head hash)

## Step 5 — refusal polarities on LIVE (read-only-safe: both are REFUSED inserts; the
## one row that would land is rolled back by the enclosing BEGIN/ROLLBACK)

    psql -h 192.168.122.1 -U bork -d ent <<'SQL'
    BEGIN;
    SET ROLE ent_rw; SET search_path = ent;
    -- polarity A: review-silent close (expect ERROR ... work_review_disposition_kind_shape)
    SAVEPOINT a;
    INSERT INTO ledger (session,kind,statement,actor,work_slug,work_resolution)
      SELECT 'polarity-probe','work_closed','probe',1,work_slug,'dropped'
        FROM ledger WHERE kind='work_opened' LIMIT 1;
    ROLLBACK TO a;
    ROLLBACK;
    SQL

Expected: `ERROR: new row for relation "ledger" violates check constraint
"work_review_disposition_kind_shape"`. (Witnessed verbatim on scratch. The strict-mode
refusals were additionally witnessed on scratch fixtures: strict+deferred refused with
teach-text; strict over an unresolved tree refused NAMING the leaf and its close row id;
strict close SUCCEEDED after a distinct-actor attest discharge, discharge_grade computed
`same-principal` fail-safe. Live fixture trees are not created by this runbook.)

## Step 6 — record the act

    cd ~/ent && ./led decision "s29 applied in place ... (s29 identity 92e1c75+NOT VALID rider, rehearsal witness <autoharn ledger row ids>, backup ~/backups/ent-pre-s29-live-$TS.sql)"
    cd /home/bork/w/vdc/1/autoharn && ./led decision "ent s29 in-place apply executed by maintainer ..."

## Rollback (catastrophic only — a failed Step 3 needs NO rollback, it self-reverts)

Only if post-apply verification fails in a way that requires restoring pre-apply state:

    # 1. confirm the gap is still open (Step 0)
    # 2. drop the damaged pair and restore the Step-1 dump (it contains CREATE SCHEMA):
    psql -h 192.168.122.1 -U bork -d ent -v ON_ERROR_STOP=1 \
      -c 'DROP SCHEMA ent CASCADE; DROP SCHEMA ent_kernel CASCADE;'
    psql -h 192.168.122.1 -U bork -d ent -v ON_ERROR_STOP=1 -q \
      -f ~/backups/ent-pre-s29-live-$TS.sql
    # 3. re-run Step 2: digest must equal the saved baseline; ./verify-chain INTACT
    # NOTE: DROP ... CASCADE is irreversible — only ever after the dump's trailer line
    # and nonzero size were verified in Step 1, and never while any session runs.

## Scratch evidence left in the ent db (drop whenever done)

    DROP SCHEMA s29reh CASCADE; DROP SCHEMA s29reh_kernel CASCADE;

<!-- doc-attest-exempt: point-in-time rehearsal evidence + runbook from the 2026-07-14 ent s29 rehearsal, staged in proposals/ pending ratification of the NOT VALID variant; mechanized into ./migrate rather than read by humans -- the script build is where living-prose attestation lands. -->
