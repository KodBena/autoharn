-- s59 MISSIVE VIEWS (design/FABLE-MISSIVES-KERNEL-SPEC.md §3 -- Fable-authored, OUT OF FRAME,
-- maintainer-ratified AS IT STANDS 2026-07-25, ledger row 1263). Sonnet-executed per the
-- standing delegation contract. VIEW-ONLY, ZERO NEW LEDGER COLUMNS, ZERO NEW KINDS -- the
-- s54/s56 discipline, restated: compute_row_hash is UNTOUCHED, writes are unaffected (the s43
-- boundary continues to own them; this delta touches no INSERT path whatsoever).
--
-- This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/existing world is
-- the maintainer's act at a FUTURE world's birth (runs-are-strictly-linear, 2026-07-11) -- never
-- taken here.
--
-- PREREQUISITE: s58 (kernel/lineage/s58-missive-substrate.sql) -- a HARD dependency: every view
-- below reads the ten missive_* typed columns s58 adds. Applying this file on a pre-s58 kernel
-- fails loudly at CREATE VIEW time (undefined column) -- the correct, disclosed failure mode.
--
-- SIX NEW VIEWS (spec §3, every consumer named, row 1906 discipline), all security_invoker, all
-- reading ledger_current (the s31 discipline -- every missive view is a current-truth
-- working-set surface, no HISTORY read is the view's own point here, unlike s56's
-- review_verdicts):
--   1. missive_outbound -- THE SERVED TRANSPORT FEED (spec §3 item 1, §13 item 3): all in-force
--      missive_sent rows, all ten envelope columns plus statement, plus the MINTED provenance
--      token ('xrow:' || author_world || ':' || id || ':' || row_hash). Deliberately the FULL
--      cursor-paged set, no "minus acknowledged" filter (that working set lives in view 5
--      instead) and no ?addressee= parameter (client-side filter, spec §5 step 2). Keyed/
--      paginated by id. Consumer: the counterpart world's courier.
--   2. missive_receipts -- courier index (spec §3 item 2): id, author_world, thread, seq, act,
--      provenance, and provenance_row_id (parsed from the pinned token, derived, never a second
--      home). In-force missive_received rows. Keyed by id. Consumer: the courier verb's
--      high-water cursor and set-diff.
--   3. missive_undisposed -- in-force missive_received, act <> 'acknowledgment', with no
--      in-force missive_disposed regarding it (spec §3 item 3). Keyed by id. Consumer:
--      ./pickup and the deciding principal choosing dispositions.
--   4. missive_stale -- undisposed receipts for which a later in-force receipt exists (same
--      thread, same author_world) whose responds_to names exactly the frozen predecessor's own
--      provenance token (spec §3 item 4). Keyed by id (the stale receipt's). Consumer:
--      ./pickup surfacing "do not act on this one" before an agent does.
--   5. missive_delivery_audit -- author-side: in-force missive_sent rows (act <> 'acknowledgment'),
--      each with an `acknowledged` boolean and the ack's typed disposition (spec §3 item 5).
--      Keyed by id. Consumer: the author-side operator/orchestrator and the audit verb leg.
--   6. missive_open_threads -- one row per thread open for THIS world: an undisposed non-ack
--      receipt, or an unacknowledged non-ack sent missive (spec §3 item 6). Keyed by
--      missive_thread. Consumer: the orchestrator's working set.
--
-- VIEW_REGISTRY additions (serving/boundary_service.py, same-build, separate commit-file):
--   missive_outbound/missive_receipts/missive_undisposed/missive_stale/missive_delivery_audit
--   key on id (bigint, id-shaped pagination); missive_open_threads keys on missive_thread
--   (slug-shaped, the work_startable/work_edge_parent precedent).
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a)): this delta's own slice of the spec's own §10 (s58's
-- own header carries the kinds/columns/triggers/function slice):
--   - INVARIANT: every lifecycle transition (sent, received, disposed, acknowledged,
--     withdrawn/superseded) is queryable through exactly one of these six named, single-purpose
--     views -- no consumer re-derives a discharge or staleness predicate by hand-copying one of
--     these views' own WHERE clauses (the s32 F6-class lesson, restated one family over).
--   - QUANTIFICATION UNIVERSE: views: SIX, each with a named consumer (above); non-member views
--     re-verified -- none of the existing 20-odd kernel views reads any missive_* column
--     (grep -l missive_ kernel/lineage/*.sql at this delta's own authoring time finds only
--     s58/s59 themselves); GRANTS: all six get a fresh GRANT SELECT (security_invoker views
--     compose through invoker privilege on every underlying relation they read, so :role needs
--     direct SELECT even though ledger_current is already granted -- the s56 ELEMENT 2/3
--     precedent, restated).
--   - DENOMINATION: identity in (author_world, thread, seq); the minted provenance token in the
--     SAME xrow:<world>:<id>:<row_hash> currency s58's own value CHECKs already use, never a
--     second encoding. No bound in this delta is a bare round literal (view-only; no numeric
--     bound is introduced by this file at all).
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT CLASS-RATIFIED FAIL-SAFE
-- -- mints the served transport route (missive_outbound) and ecosystem vocabulary alongside s58,
-- the s53/s56/s57 precedent of routing a non-fail-safe, ratified-by-name kernel delta through its
-- own spec. Ships under design/FABLE-MISSIVES-KERNEL-SPEC.md's own maintainer ratification
-- (ledger row 1263, 2026-07-25).
--
-- LIMITS (pre-registered): these views compute nothing the underlying missive_* columns and
-- ledger_current do not already carry (strictly additive convenience, the s56 reservations_
-- outstanding precedent); missive_delivery_audit's `acknowledged` boolean answers "does an ack
-- exist", never "was the disposition JUST"; missive_stale is hash-pinned (responds_to must name
-- EXACTLY the frozen predecessor's own token), never fuzzy thread-recency (spec §3 item 4).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s58):
--   VALIDATE (reachable throwaway): apply the full chain through s58 (s58's own VALIDATE list),
--   then -f s59-missive-views.sql.
--   REAL: NEVER applied to any existing world by this authoring act. Enters a FUTURE world's
--   birth chain via bootstrap/new-project.sh's LINEAGE_CHAIN, wired by the maintainer/
--   orchestrator at that world's birth (not taken here, the s34/s48/s56/s57 precedent).
--   Authored and scratch-witnessed on scratch schema pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE VIEW).
--
-- HISTORY: safe -- this delta touches derived views only; zero stored rows change, no data
-- rewrite, no re-denomination. s59 re-issues nothing (no pre-existing reader of any of the six
-- names -- verified by grep at build time, the s56 §7 discipline).
-- ============================================================================================

\if :{?schema}
\else
  \set schema public
\endif
\if :{?kern}
\else
  \set kern kernel
\endif
\if :{?role}
\else
  \set role vsr_rw
\endif

-- ============================================================================================
-- 1. missive_outbound -- THE SERVED TRANSPORT FEED.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".missive_outbound
    WITH (security_invoker = true) AS
SELECT s.id, s.ts, s.statement, s.actor,
       s.missive_protocol, s.missive_author_world, s.missive_addressee_world,
       s.missive_thread, s.missive_seq, s.missive_act, s.missive_responds_to,
       s.missive_cites, s.missive_disposition,
       'xrow:' || s.missive_author_world || ':' || s.id || ':' || s.row_hash AS missive_provenance
FROM   :"schema".ledger_current s
WHERE  s.kind = 'missive_sent';

COMMENT ON VIEW :"schema".missive_outbound IS
  'design/FABLE-MISSIVES-KERNEL-SPEC.md §3 item 1: THE SERVED TRANSPORT FEED -- every in-force
   missive_sent row plus the MINTED provenance token (xrow:<author_world>:<id>:<row_hash>, spec
   §13 item 1 -- a row cannot carry its own row_hash, so this view is where the token is born).
   Deliberately the FULL cursor-paged set, no "minus acknowledged" filter (missive_delivery_audit
   carries that working set instead) and no addressee filter (client-side, the courier verb).
   Keyed/paginated by id. Consumer: the counterpart world''s courier.
   kernel/lineage/s59-missive-views.sql.';

GRANT SELECT ON :"schema".missive_outbound TO :"role";

-- ============================================================================================
-- 2. missive_receipts -- courier index.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".missive_receipts
    WITH (security_invoker = true) AS
SELECT r.id, r.missive_author_world, r.missive_thread, r.missive_seq, r.missive_act,
       r.missive_provenance,
       split_part(r.missive_provenance, ':', 3)::bigint AS provenance_row_id
FROM   :"schema".ledger_current r
WHERE  r.kind = 'missive_received';

COMMENT ON VIEW :"schema".missive_receipts IS
  'design/FABLE-MISSIVES-KERNEL-SPEC.md §3 item 2: courier index -- id, author_world, thread,
   seq, act, provenance, and provenance_row_id (the author-side row id, PARSED from the pinned
   token, derived, never a second home). In-force missive_received rows. Keyed by id. Consumer:
   the courier verb''s high-water cursor and set-diff (the mechanism that makes exactly-once
   RECORDING also exactly-once ATTEMPTING in the common case).
   kernel/lineage/s59-missive-views.sql.';

GRANT SELECT ON :"schema".missive_receipts TO :"role";

-- ============================================================================================
-- 3. missive_undisposed.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".missive_undisposed
    WITH (security_invoker = true) AS
SELECT r.id, r.ts, r.missive_author_world, r.missive_addressee_world, r.missive_thread,
       r.missive_seq, r.missive_act, r.missive_responds_to, r.missive_provenance,
       r.missive_cites, r.statement
FROM   :"schema".ledger_current r
WHERE  r.kind = 'missive_received'
AND    r.missive_act <> 'acknowledgment'
AND    NOT EXISTS (
  SELECT 1 FROM :"schema".ledger_current d
  WHERE d.kind = 'missive_disposed' AND d.missive_regards = r.id
);

COMMENT ON VIEW :"schema".missive_undisposed IS
  'design/FABLE-MISSIVES-KERNEL-SPEC.md §3 item 3: in-force missive_received, act <>
   ''acknowledgment'', with no in-force missive_disposed regarding it (AMENDMENT 1:
   missive_regards, not the core regards column). Keyed by id. Consumer:
   ./pickup (mail is part of hydration) and the deciding principal choosing dispositions.
   kernel/lineage/s59-missive-views.sql.';

GRANT SELECT ON :"schema".missive_undisposed TO :"role";

-- ============================================================================================
-- 4. missive_stale.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".missive_stale
    WITH (security_invoker = true) AS
SELECT r.id, r.missive_author_world, r.missive_thread, r.missive_seq, r.missive_provenance,
       r2.id AS superseding_id, r2.missive_act AS superseding_act
FROM   :"schema".missive_undisposed r
JOIN   :"schema".ledger_current r2
       ON  r2.kind = 'missive_received'
       AND r2.missive_thread = r.missive_thread
       AND r2.missive_author_world = r.missive_author_world
       AND r2.missive_responds_to = r.missive_provenance;

COMMENT ON VIEW :"schema".missive_stale IS
  'design/FABLE-MISSIVES-KERNEL-SPEC.md §3 item 4: undisposed receipts for which a later
   in-force receipt exists in the same thread from the same author, whose responds_to names
   EXACTLY the frozen predecessor''s own provenance token -- hash-pinned, never fuzzy
   thread-recency. Keyed by id (the stale receipt''s). Consumer: ./pickup, surfacing "do not
   act on this one" before an agent does. kernel/lineage/s59-missive-views.sql.';

GRANT SELECT ON :"schema".missive_stale TO :"role";

-- ============================================================================================
-- 5. missive_delivery_audit.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".missive_delivery_audit
    WITH (security_invoker = true) AS
SELECT s.id, s.ts, s.missive_author_world, s.missive_addressee_world, s.missive_thread,
       s.missive_seq, s.missive_act, s.statement,
       EXISTS (
         SELECT 1 FROM :"schema".ledger_current a
         WHERE a.kind = 'missive_received' AND a.missive_act = 'acknowledgment'
           AND a.missive_responds_to =
               'xrow:' || s.missive_author_world || ':' || s.id || ':' || s.row_hash
           AND a.missive_author_world = s.missive_addressee_world
       ) AS acknowledged,
       (SELECT a.missive_disposition FROM :"schema".ledger_current a
         WHERE a.kind = 'missive_received' AND a.missive_act = 'acknowledgment'
           AND a.missive_responds_to =
               'xrow:' || s.missive_author_world || ':' || s.id || ':' || s.row_hash
           AND a.missive_author_world = s.missive_addressee_world
         LIMIT 1) AS missive_disposition
FROM   :"schema".ledger_current s
WHERE  s.kind = 'missive_sent'
AND    s.missive_act <> 'acknowledgment';

COMMENT ON VIEW :"schema".missive_delivery_audit IS
  'design/FABLE-MISSIVES-KERNEL-SPEC.md §3 item 5: author-side -- in-force missive_sent rows
   (act <> ''acknowledgment''), each with an `acknowledged` boolean (an in-force
   missive_received ack row exists whose responds_to equals this row''s own minted token) and
   the ack''s typed disposition (NULL until acknowledged). Also where the "minus acknowledged"
   working set lives (spec §13 item 3''s note). Keyed by id. Consumer: the author-side
   operator/orchestrator and the audit verb leg. kernel/lineage/s59-missive-views.sql.';

GRANT SELECT ON :"schema".missive_delivery_audit TO :"role";

-- ============================================================================================
-- 6. missive_open_threads.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".missive_open_threads
    WITH (security_invoker = true) AS
SELECT thread AS missive_thread,
       count(*) FILTER (WHERE reason = 'undisposed_receipt') AS undisposed_receipts,
       count(*) FILTER (WHERE reason = 'unacknowledged_sent') AS unacknowledged_sent
FROM (
  SELECT missive_thread AS thread, 'undisposed_receipt' AS reason
  FROM :"schema".missive_undisposed
  UNION ALL
  SELECT missive_thread AS thread, 'unacknowledged_sent' AS reason
  FROM :"schema".missive_delivery_audit
  WHERE NOT acknowledged
) opens
GROUP BY thread;

COMMENT ON VIEW :"schema".missive_open_threads IS
  'design/FABLE-MISSIVES-KERNEL-SPEC.md §3 item 6: one row per thread open for THIS world -- it
   holds an undisposed non-ack receipt, or an unacknowledged non-ack sent missive. Keyed by
   missive_thread. Consumer: the orchestrator''s working set -- the BACKFLOW shrink-as-resolved
   discipline as a derived view over append-only rows. kernel/lineage/s59-missive-views.sql.';

GRANT SELECT ON :"schema".missive_open_threads TO :"role";
-- ============================================================================================
