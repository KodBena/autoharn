-- s59 MISSIVE VIEWS (design/FABLE-MISSIVES-KERNEL-SPEC.md §3 -- Fable-authored, OUT OF FRAME,
-- maintainer-ratified AS IT STANDS 2026-07-25, ledger row 1263, AS AMENDED by AMENDMENT 2
-- (2026-07-25, maintainer-ratified "yes"): missive_outbound re-issued as APPEND-COMPLETE
-- transport -- reads raw `ledger` (superseded missive_sent rows included), never
-- ledger_current; see that view's own header, in place below, for the full witnessed defect
-- and fix). Sonnet-executed per the standing delegation contract. VIEW-ONLY, ZERO NEW LEDGER
-- COLUMNS, ZERO NEW KINDS -- the s54/s56 discipline, restated: compute_row_hash is UNTOUCHED,
-- writes are unaffected (the s43 boundary continues to own them; this delta touches no INSERT
-- path whatsoever).
--
-- This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/existing world is
-- the maintainer's act at a FUTURE world's birth (runs-are-strictly-linear, 2026-07-11) -- never
-- taken here.
--
-- PREREQUISITE: s58 (kernel/lineage/s58-missive-substrate.sql) -- a HARD dependency: every view
-- below reads the ten missive_* typed columns s58 adds. Applying this file on a pre-s58 kernel
-- fails loudly at CREATE VIEW time (undefined column) -- the correct, disclosed failure mode.
--
-- SIX NEW VIEWS (spec §3, every consumer named, row 1906 discipline), all security_invoker.
-- FIVE of the six read ledger_current (the s31 discipline -- a current-truth working-set
-- surface, no HISTORY read is the view's own point there, unlike s56's review_verdicts);
-- missive_outbound is the ONE DECLARED EXCEPTION (AMENDMENT 2, 2026-07-25, maintainer-ratified
-- "yes" -- reads raw `ledger`, superseded rows included, transport is not truth; see that
-- view's own header for the witnessed defect this closes), the SAME declared-raw-reader
-- discipline s56's review_verdicts and s37's work_violation_history already establish
-- one delta/family over -- named here, not silently assumed current-truth-typed:
--   1. missive_outbound -- THE SERVED TRANSPORT FEED (spec §3 item 1, §13 item 3, AS AMENDED BY
--      AMENDMENT 2): EVERY missive_sent row EVER WRITTEN (superseded included, raw `ledger`),
--      all ten envelope columns plus statement, plus the MINTED provenance token ('xrow:' ||
--      author_world || ':' || id || ':' || row_hash). Deliberately the FULL cursor-paged set,
--      no "minus acknowledged" filter (that working set lives in view 5 instead), no
--      ?addressee= parameter (client-side filter, spec §5 step 2), and (AMENDMENT 2) no
--      current-truth filter -- delivery-monotonic, what was sent is what arrives. Keyed/
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
--
-- AMENDMENT 2 CLOSURE ADDENDUM (2026-07-25, maintainer-ratified "yes" -- ADR-0000 form):
-- *Invariant:* every missive_sent row is visible to its addressee's courier exactly once,
-- independent of any later row (supersession is a content-level fact the row itself carries,
-- never a reason the transport withholds it). *Quantification universe:* missive_outbound's
-- row set -- ALL missive_sent rows of the serving world, superseded included; named as not
-- covered: rows a hostile or dead network never lets a courier pull (§7''s honest limit,
-- unchanged); the FIVE receiving-side views are UNCHANGED by this amendment (re-verified: none
-- reads missive_outbound or any other re-issued object). *Denomination check:* no numeric
-- bounds; vacuous, named as such. *Reader-type note (gates/ledger_reader_allowlist.py):*
-- missive_outbound is now a DECLARED raw/history reader by design (the s56 review_verdicts /
-- s37 work_violation_history precedent) -- needs NO additional GRANT (SELECT on raw `ledger`
-- has been granted to `:role` since s15; s43 revoked only INSERT), only the allowlist entry.
-- *History note:* view re-issue only; zero stored rows change.
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
--
-- AMENDMENT 2 (2026-07-25, maintainer-ratified "yes"): RE-ISSUED as APPEND-COMPLETE TRANSPORT.
-- Witnessed defect (strengthened-tier review, serving axis): the pre-amendment body read
-- `ledger_current` (the in-force/un-superseded projection) -- baking a CURRENT-TRUTH view into
-- a TRANSPORT feed, contradicting spec §13 decision 3's own "FULL cursor-paged outbound feed"
-- and the family's own founding purpose (communication where nothing is silently lost).
-- Witnessed live with two ordinary SEQUENTIAL writes (no race): a missive superseded before its
-- first courier pull VANISHES from the only feed a courier ever reads -- the addressee receives
-- a later withdrawal citing a provenance token for a message it never got and never will;
-- missive_stale cannot correlate (the original never arrived); the content is unrecoverably
-- lost; "withdrawn before poll" becomes indistinguishable from "never sent". A drafting error
-- (letter/spirit divergence, CLAUDE.md's reading posture, ADR-0000 Rule 2(a)) -- the spirit
-- governs, corrected here.
--
-- THE FIX: reads raw `ledger` (NOT ledger_current) -- superseded missive_sent rows INCLUDED,
-- cursor on `id`, delivery-monotonic: what was sent is what arrives, in order, always.
-- Supersession remains a CONTENT-level fact carried in the rows themselves (a withdrawal's own
-- `supersedes`/`missive_responds_to` travel WITH it, as an ordinary served row) -- the
-- RECEIVING side's views (missive_undisposed/missive_stale/missive_open_threads) keep their
-- own current-truth semantics UNCHANGED and now correlate correctly, because the original
-- actually arrives for missive_stale to correlate against. No other view changes; no
-- write-path change; the courier needs no change (its cursor is already id-monotonic --
-- verified live, this same witness pass).
--
-- gates/ledger_reader_allowlist.py: missive_outbound gains a NEW ALLOWLIST entry (declared
-- raw/history reader by design, the review_verdicts/work_violation_history precedent -- "every
-- row ever sent, never thinner").
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".missive_outbound
    WITH (security_invoker = true) AS
SELECT s.id, s.ts, s.statement, s.actor,
       s.missive_protocol, s.missive_author_world, s.missive_addressee_world,
       s.missive_thread, s.missive_seq, s.missive_act, s.missive_responds_to,
       s.missive_cites, s.missive_disposition,
       'xrow:' || s.missive_author_world || ':' || s.id || ':' || s.row_hash AS missive_provenance
FROM   :"schema".ledger s
WHERE  s.kind = 'missive_sent';

COMMENT ON VIEW :"schema".missive_outbound IS
  'design/FABLE-MISSIVES-KERNEL-SPEC.md §3 item 1, AS AMENDED BY AMENDMENT 2 (2026-07-25,
   maintainer-ratified "yes"): THE SERVED TRANSPORT FEED, APPEND-COMPLETE -- every missive_sent
   row EVER WRITTEN (superseded included, raw `ledger`, never ledger_current) plus the MINTED
   provenance token (xrow:<author_world>:<id>:<row_hash>, spec §13 item 1 -- a row cannot carry
   its own row_hash, so this view is where the token is born). Deliberately the FULL
   cursor-paged set: no "minus acknowledged" filter (missive_delivery_audit carries that
   working set instead), no addressee filter (client-side, the courier verb), and (AMENDMENT 2)
   no current-truth filter either -- transport is not truth; supersession is a CONTENT-level
   fact the row itself carries (supersedes/missive_responds_to), never a reason to withhold the
   row from the one feed a courier will ever read. Keyed/paginated by id, delivery-monotonic.
   Consumer: the counterpart world''s courier.
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
