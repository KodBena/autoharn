-- s56 RESERVATION RESIDUE (design/FABLE-RESERVATION-RESIDUE-SPEC.md -- Fable-authored,
-- maintainer-ratified 2026-07-22, "Kernel semantics change approved as a matter of course. If
-- the kernel is wrong, it would be pointless. Let's do it.", against autoharn2 ledger rows
-- 1093-1095). Sonnet-executed per the standing delegation contract, from this Fable-authored,
-- maintainer-ratified spec. VIEW-ONLY, ZERO NEW LEDGER COLUMNS, ZERO NEW KINDS -- compute_row_hash
-- is UNTOUCHED (the s46/s54 discipline, restated). Writes are unaffected -- the s43 boundary
-- continues to own them; this delta touches no INSERT path whatsoever.
--
-- This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/existing world is
-- the maintainer's act at a FUTURE world's birth (runs-are-strictly-linear, 2026-07-11) -- never
-- taken here.
--
-- PREREQUISITE: s32 (kernel/lineage/s32-edge-views-single-home.sql) -- a HARD dependency: this
-- delta widens discharging_attest IN PLACE (CREATE OR REPLACE, s32's own object) and adds
-- reservations_outstanding/review_verdicts, both of which read review_detail and ledger_current
-- directly. Applying this file on a pre-s32 kernel fails loudly at CREATE VIEW time (undefined
-- relation discharging_attest for the re-issue), the correct, disclosed failure mode for a hard
-- dependency, matching the s34/s48/s54 PREREQUISITE precedent.
--
-- WHY (operator-side prose; NOT subject-visible -- only the catalog objects inside the opaque db
-- are): the experience2 backflow finding (AUTOHARN_BACKFLOW.md 2026-07-22, "work_review_gap
-- discharge inconsistency"): a genuinely-performed, distinct-actor, reservation-carrying
-- countersign left its work item surfaced as open, indistinguishable from an item nobody
-- reviewed, and created live pressure to fabricate a clean `attest` to satisfy the gate (resisted,
-- disclosed there). ADR-0002's ground, restated: a gate that surfaces a reviewed-with-concerns
-- item identically to an unreviewed one REWARDS fabricating a clean verdict where the honest
-- act is to attest WITH the reservation on record; this delta removes the reward (the
-- reservation-carrying countersign now discharges, exactly as a clean attest does) while
-- PRESERVING the concern (it lands on a dedicated, tracked surface -- reservations_outstanding
-- -- until it is itself dispositioned, never silently dropped). Industry basis (informing, not
-- authority): formal-inspection regimes (Fagan, IEEE 1028; the shapes DO-178C / ISO 26262 / NRC
-- licensing reviews expect) close the review event on an accept-with-rework verdict and track
-- each reservation to its own independent closure -- the reviewer's verdict is final; the
-- system, not trust, carries the residue.
--
-- ELEMENT 1 -- discharging_attest (s32's own single home, ADR-0012 P1) WIDENED IN PLACE: the
-- verdict filter becomes `verdict IN ('attest','attest_with_reservations')` -- both attesting
-- verdicts now answer YES to "has row R been discharged by an un-superseded distinct-actor
-- review", exactly as `attest` alone did before. `refuse` continues to answer NO everywhere (its
-- own domain member, untouched). The name is KEPT (renaming would force re-issuing every
-- consumer for zero semantic gain; the view's identity is "the attest-family discharge edge",
-- and its own COMMENT now says so explicitly) -- every one of s32's consumers (review_gap,
-- countersigned_in_force, work_review_gap, work_item_strict_blockers, and every later re-issue
-- of those four objects, s33 through s53) acquires the widened semantics through this ONE
-- re-issue, composing, with ZERO edits of its own (verified below, QUANTIFICATION UNIVERSE).
--
-- ELEMENT 2 -- reservations_outstanding (new view, additive): one row per un-superseded `review`
-- row whose review_detail.verdict = 'attest_with_reservations' that has not itself been
-- dispositioned. Columns: review_id, regards (the row the review regarded), reviewer (actor),
-- basis (the reservation prose -- the load-bearing content). DISPOSITION, existing vocabulary
-- only, no new kinds: a reservation leaves the view when (a) the review row is itself superseded
-- (the existing uniform-retraction path, s31), OR (b) an un-superseded `review` row REGARDING THE
-- RESERVATION REVIEW ITSELF (r2.regards = review_id) carries verdict 'attest' -- "reservation
-- dispositioned", by any actor including the original reviewer withdrawing their own concern.
--
-- ELEMENT 3 -- review_verdicts (new view, additive): the general review-legibility surface --
-- every `review` row joined with its review_detail (review_id, regards, reviewer, verdict,
-- independence, basis, antecedent, superseded boolean). This is the read path whose absence
-- forced experience2 to inspect the wrong column (attest_verdict, the s44 model-identity field)
-- and mis-diagnose a storage bug -- verdict storage was verified sound there; the defect was
-- semantic (discharging_attest's narrow filter) and this view's absence (no direct "what did
-- this review actually say" read path), both closed by this delta.
--
-- WHAT THIS DELTA DELIBERATELY DOES NOT DO (ADR-0013 Rule 4, filed not buried):
--   - NO residue surface for `refuse` (spec's own "named as not covered" (i)): a refusal already
--     blocks discharge loudly; a refuse-residue view is a separate question, filed not built.
--   - NO retro-grading of past ledger PROSE -- historical narration that said "gap open" stands
--     as written, append-only (ADR-0005 Rule 8); only an existing world's CURRENT derived views
--     re-grade (the stated, intended HISTORY effect below).
--   - NO SPA/panel presentation work -- the panel deployment's own concern, not this delta's.
--   - NO CLI verb (`led review-gap`/`led work review-gap` etc.) is re-shaped -- they read the
--     views this delta widens/adds, unchanged themselves.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form):
--
--   - INVARIANT: everywhere the kernel asks "has row R been discharged by an un-superseded
--     distinct-actor review," a review whose verdict is attest_with_reservations answers YES
--     exactly as attest does, and every such reservation additionally appears on exactly one
--     derived surface (reservations_outstanding) until it is itself dispositioned. refuse
--     continues to answer NO everywhere. No consumer distinguishes the two attesting verdicts by
--     hand-copying a verdict filter (s32's F6 class, re-foreclosed here at its single home).
--
--   - QUANTIFICATION UNIVERSE -- every consumer of discharging_attest, re-verified against its
--     CURRENT (latest re-issued) definition, not its historical one (grep -l discharging_attest
--     kernel/lineage/*.sql, cross-checked against every CREATE OR REPLACE of the four s32-named
--     objects in the tree):
--       * review_gap            -- latest re-issue: s32 (kernel/lineage/s32-edge-views-single-
--         home.sql). Composes with discharging_attest via `da.reviewer <> l.actor`, NO own
--         verdict predicate. Re-verified.
--       * countersigned_in_force -- latest re-issue: s53 (kernel/lineage/s53-belief-substrate.sql,
--         the s42-law column-complete re-issue chain's current head). Composes with
--         discharging_attest via a bare EXISTS, NO distinct-actor predicate and NO own verdict
--         predicate (unchanged semantics -- s32's own header reasoning, re-verified here).
--       * work_review_gap       -- latest re-issue: s37 (kernel/lineage/
--         s37-violation-disposition.sql, consult A5's second UNION arm over
--         work_violation_disposition). Both UNION arms discharge through the SAME outer
--         `NOT EXISTS (... discharging_attest ...)` wrapper, NO own verdict predicate.
--         Re-verified.
--       * work_item_strict_blockers() -- latest re-issue: s33 (kernel/lineage/
--         s33-composite-discharge.sql, the composite-tree-exemption extension). Its
--         `review_unresolved` CTE composes with discharging_attest via
--         `da.reviewer <> c.closer`, NO own verdict predicate. Re-verified.
--     COMPOSITE DISCHARGE (s33) and its own `work_discharge='composite'` gate reads
--     work_item_strict_blockers() above -- covered transitively, no separate verdict predicate of
--     its own.
--     DECISION GRADE (s36-decision-grade.sql) -- its own countersigned_in_force re-issue (an
--     intermediate column-complete link in the same chain re-verified above) composes with
--     discharging_attest via a bare EXISTS, NO own verdict predicate.
--     VIOLATION DISPOSITION (s37-violation-disposition.sql) -- its own countersigned_in_force
--     re-issue (same chain) and its work_review_gap re-issue (re-verified above as the LATEST
--     one) both compose with discharging_attest, NO own verdict predicate anywhere in that file.
--     s40/s41/s43/s44/s53 (principal-identity-events, principal-bindings-and-relations,
--     typed-verdict-write-boundary, model-identity-attestation, belief-substrate) -- each is an
--     intermediate link in the SAME countersigned_in_force column-complete re-issue chain (s53 is
--     its current head, re-verified above); every one composes with discharging_attest via a
--     bare EXISTS, NO own verdict predicate in any of the five files.
--     NONE of the above carries a second, hand-copied `verdict = 'attest'` predicate on its OWN
--     discharge leg -- NO F6 recurrence found in this delta's own re-verification (named
--     explicitly per the spec's own instruction: had one been found, it would be fixed in this
--     same file and flagged loudly here; none was).
--     s13/s14/s15/s20/s22/s23/s24/s26/s28/s29/s30/s31 each carry their OWN, now-historical,
--     pre-s32 `d.verdict = 'attest'` predicate -- every one of these objects was RE-ISSUED at s32
--     or later to compose with discharging_attest instead (s32's own ELEMENT 3), so none of these
--     dozen historical bodies governs any CURRENT world; only the four latest-re-issue objects
--     named above (and their column-complete-chain siblings, which carry no verdict predicate of
--     their own at all) are load-bearing today.
--     NEW VIEWS (two): reservations_outstanding, review_verdicts.
--     RE-ISSUED (one): discharging_attest -- WHERE clause widened, column list UNCHANGED
--     (regards_id, reviewer -- zero columns added or removed), COMMENT amended.
--     KIND VOCABULARY -- unchanged. No new `kind` value, no new column, no CHECK touched (the
--     verdict CHECK -- 'attest'/'attest_with_reservations'/'refuse', s15 -- is READ, never
--     widened; this delta uses only the existing, closed domain).
--     GRANTS -- the two new views each get a fresh GRANT SELECT (security_invoker views compose
--     through invoker privilege on every underlying relation they read, so :role needs direct
--     SELECT even though it also reaches review_detail/ledger_current indirectly through other
--     views). discharging_attest's existing grant (s32) is untouched -- same view, same name.
--     READER TYPING (gates/ledger_reader_allowlist.py) -- discharging_attest and
--     reservations_outstanding read ONLY ledger_current and review_detail (never raw `ledger`)
--     -- current-truth-typed by construction, no allowlist entry needed for either. review_verdicts
--     is a DECLARED raw/history reader BY DESIGN (spec section 3: "every review row" must include
--     a superseded one, with its own `superseded` column named explicitly -- ledger_current would
--     silently drop exactly the rows this view exists to show) -- added to the gate's ALLOWLIST
--     with its reason, in this same delta's own commit (the gate file is not engine/** or law/ and
--     is the standing mechanical detect s31 shipped for exactly this class of change).
--     ENGINE -- NONE shipped or touched in this delta (mirrors s32/s54's own "ENGINE -- NONE"
--     disclosure): engine/ledger_floor.py's work_item_floor_atoms()/work_review_floor_atoms()
--     already read ledger_current/review_detail directly (their own independent SQL-floor
--     mirror) and would need their OWN verdict-domain widening to track this delta's kernel-view
--     semantics -- named here as a residual gap this delta does NOT close (the spec's own scope:
--     kernel views only), not silently assumed closed. `./judge`'s SQL/ASP differential over the
--     'work'/'tnow' layers derives T_now facts from kind/status/supersedes, none of which this
--     delta touches at the KERNEL-VIEW level -- but engine/ledger_floor.py's own discharge
--     predicate is a SEPARATE, independent mirror this delta does not re-issue, so the engine
--     differential is witnessed for AGREEMENT on this delta's fixture worlds as a matter of
--     record, not claimed closed by construction.
--
--   - DENOMINATION: no numeric bounds exist in this delta; the only "currency" is the verdict
--     domain itself, and the widened filter is denominated in exactly the existing
--     CHECK-constrained values (attest, attest_with_reservations, refuse) -- no new values, no
--     string matching outside the constrained domain. reservations_outstanding's identity column
--     (review_id) and its `regards`/`reviewer` columns are the SAME ledger-row-id/actor-id
--     denomination discharging_attest and review_detail already use (s15/s29), never a second
--     identity for the same fact.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT claimed class-ratified
-- fail-safe (the widening RELAXES an existing discharge predicate -- a review that previously
-- left a gap open now closes it, the ratified PURPOSE of this delta, spec section 5) -- it ships
-- under design/FABLE-RESERVATION-RESIDUE-SPEC.md's own maintainer ratification (2026-07-22,
-- against autoharn2 ledger rows 1093-1095), the s36/s37/s44/s53 precedent of routing a
-- non-fail-safe, ratified-by-name kernel delta through its own spec rather than self-certifying.
--
-- LIMITS (pre-registered, matching the s32/s54 disclosure convention):
--   - reservations_outstanding shows a reservation until DISPOSITIONED by the two named paths
--     (supersede the review row; attest-review the review row itself) -- there is no THIRD
--     disposition path and none is invented ahead of need (ADR-0004).
--   - review_verdicts is a DISPLAY surface (spec section 3): it reads and reports the verdict
--     domain, it does not itself gate anything -- gating stays entirely on discharging_attest and
--     its consumers, unchanged in shape by this element.
--   - engine/ledger_floor.py's own discharge mirror is NOT re-issued by this delta (see ENGINE
--     above) -- a world relying on the engine floor's discharge computation directly (rather than
--     the kernel views this delta widens) does not see the widened semantics until that mirror is
--     separately updated; named, not silently assumed covered.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s55):
--   VALIDATE (reachable throwaway): apply the full chain through s32 (minimum) or through today's
--   head (s55), then -f s56-reservation-residue.sql.
--   REAL: NEVER applied to any existing world by this authoring act. Enters a FUTURE world's
--   birth chain via bootstrap/new-project.sh's LINEAGE_CHAIN, wired by the maintainer/orchestrator
--   at that world's birth (not taken here -- this build's own scope is kernel + serving + docs +
--   fixture only, matching the s34/s48 "do not wire LINEAGE_CHAIN" precedent for a delta not
--   itself commissioned to land the chain wiring). Authored and scratch-witnessed on scratch
--   schema pairs in the TOY db only -- NOT applied to any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE VIEW).
--
-- HISTORY: safe -- this delta touches derived views only; zero stored rows change, no data
-- rewrite, no re-denomination. The stated, intended effect on an existing world's CURRENT
-- displays: previously-stuck reservation-countersigned items discharge (experience2 rows 111/113
-- are the known specimens), and their reservations surface in reservations_outstanding until
-- dispositioned. That re-grading IS the ratified purpose, stated here rather than discovered.
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
-- ELEMENT 1 -- discharging_attest (s32) WIDENED IN PLACE: verdict IN ('attest',
-- 'attest_with_reservations') -- the attest-family discharge edge. Column list UNCHANGED
-- (regards_id, reviewer). The distinct-actor predicate remains DELIBERATELY NOT baked in here
-- (s32's own reasoning, unchanged): each consumer applies its own comparison at the join site.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".discharging_attest
    WITH (security_invoker = true) AS
SELECT r.regards AS regards_id, r.actor AS reviewer
FROM   :"schema".ledger_current r
JOIN   :"schema".review_detail d ON d.ledger_id = r.id
WHERE  r.kind = 'review' AND d.verdict IN ('attest', 'attest_with_reservations');

COMMENT ON VIEW :"schema".discharging_attest IS
  'Single home (kernel/lineage/s32-edge-views-single-home.sql, ADR-0012 P1) of "an un-superseded
   attest-family review regarding row R" -- regards_id names R, reviewer is the reviewing actor.
   WIDENED (kernel/lineage/s56-reservation-residue.sql, design/FABLE-RESERVATION-RESIDUE-SPEC.md,
   maintainer-ratified 2026-07-22): verdict IN (attest, attest_with_reservations) -- a
   reservation-carrying countersign discharges exactly as a clean attest does; the reservation
   itself surfaces separately on reservations_outstanding until dispositioned. refuse continues
   to answer NO everywhere (not selected here, unchanged). The name is kept -- the view''s
   identity is "the attest-family discharge edge". Deliberately does NOT filter reviewer against
   any particular actor -- that predicate varies per consumer (ADR-0008: no fuzzy-matching two
   distinct facts into one).';

-- ============================================================================================
-- ELEMENT 2 -- reservations_outstanding (new, additive): one row per un-superseded review row
-- carrying verdict='attest_with_reservations' that has not itself been dispositioned.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".reservations_outstanding
    WITH (security_invoker = true) AS
SELECT r.id AS review_id, r.regards, r.actor AS reviewer, d.basis
FROM   :"schema".ledger_current r
JOIN   :"schema".review_detail d ON d.ledger_id = r.id
WHERE  r.kind = 'review' AND d.verdict = 'attest_with_reservations'
AND    NOT EXISTS (
  SELECT 1
  FROM   :"schema".ledger_current r2
  JOIN   :"schema".review_detail d2 ON d2.ledger_id = r2.id
  WHERE  r2.kind = 'review' AND r2.regards = r.id AND d2.verdict = 'attest'
);

COMMENT ON VIEW :"schema".reservations_outstanding IS
  'design/FABLE-RESERVATION-RESIDUE-SPEC.md section 2 Element 2: one row per un-superseded review
   row whose verdict is attest_with_reservations, not itself dispositioned. review_id, regards
   (the row the review regarded), reviewer (actor), basis (the reservation prose -- the
   load-bearing content). A reservation leaves this view when (a) its own review row is
   superseded (ledger_current''s uniform-retraction filter, applied to r above), or (b) an
   un-superseded review row REGARDING THIS review (regards = review_id) carries verdict attest --
   "reservation dispositioned", by any actor including the original reviewer withdrawing their
   own concern. kernel/lineage/s56-reservation-residue.sql.';

GRANT SELECT ON :"schema".reservations_outstanding TO :"role";

-- ============================================================================================
-- ELEMENT 3 -- review_verdicts (new, additive): the general review-legibility surface -- every
-- review row joined with its review_detail.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".review_verdicts
    WITH (security_invoker = true) AS
SELECT r.id AS review_id, r.regards, r.actor AS reviewer, d.verdict, d.independence, d.basis,
       d.antecedent,
       EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = r.id) AS superseded
FROM   :"schema".ledger r
JOIN   :"schema".review_detail d ON d.ledger_id = r.id
WHERE  r.kind = 'review';

COMMENT ON VIEW :"schema".review_verdicts IS
  'design/FABLE-RESERVATION-RESIDUE-SPEC.md section 3: the general review-legibility surface --
   every review row (superseded or not, superseded flag named explicitly) joined with its
   review_detail -- review_id, regards, reviewer, verdict, independence, basis, antecedent,
   superseded. The read path whose absence forced the experience2 backflow finding to inspect the
   wrong column (attest_verdict, the s44 model-identity field) and mis-diagnose a storage bug.
   kernel/lineage/s56-reservation-residue.sql.';

GRANT SELECT ON :"schema".review_verdicts TO :"role";

-- ============================================================================================
-- GRANTS: discharging_attest keeps its EXISTING grant (s32) -- same view, same name, same
-- column list. reservations_outstanding/review_verdicts' grants are issued above (ELEMENT 2/3).
-- ============================================================================================
