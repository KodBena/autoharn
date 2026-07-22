-- s55 DISPATCH-GRAIN INDEPENDENCE (design/FABLE-BELIEF-SUBSTRATE-SPEC.md v2 Delta B3, §3.5 --
-- Q6, ratified build basis, ledger rows 1914/1919). CLASS-RATIFIED FAIL-SAFE SHAPE (adds ONE
-- vocabulary member; relaxes nothing existing -- the new value passes through the SAME no-gate
-- path 'self-review' always had), but routed under the belief-substrate spec's own ratification
-- regardless, per that spec's own §3.5 closing line: "because it mints vocabulary." Sonnet-
-- executed per the standing delegation contract.
--
-- PREREQUISITE: s17 (kernel/lineage/s17-independence-vocabulary.sql), the most recent re-issuer
-- of review_detail_independence_check (confirmed by grep across kernel/lineage/*.sql before
-- authoring: no later delta touches this CHECK). No ordering dependency on s53/s54 -- this delta
-- widens a `review_detail` CHECK, a table with no `kind` column at all (confirmed against
-- gates/kind_shape_manifest_gate.py's own docstring, "MANIFEST SCOPE... review_detail carries
-- CHECKs of its own... but that table has no kind column"), so it is untouched by, and untouches,
-- everything s53/s54 add to `ledger`. Placed after s54 in the birth chain purely because it
-- completes the same spec family (B1/B2/B3 in the spec's own numbered order), not because of any
-- real dependency.
--
-- THE CLASS (backflow finding 6 / access-consult D5, spec §3.5): stamp distinctness is grained
-- at (session, agent), so a genuinely isolated dispatch's verdict, relayed by the orchestrator's
-- own writing invocation, is representable only as 'self-review' plus prose -- honest but LOSSY
-- to any reader of the `independence` column alone: the column cannot distinguish "I reviewed my
-- own work" from "an isolated dispatch reviewed it and I am relaying the verdict, unable to
-- write it myself."
--
-- MECHANISM (spec §3.5, verbatim scoping): ONE additive vocabulary member,
-- 'disclosed-isolated-dispatch', on review_detail.independence (CHECK re-issued, five-member).
-- Semantics: an honest DISCLOSURE -- "this verdict was produced by an isolated dispatch and is
-- relayed by its dispatcher's invocation" -- NOT an independence CLAIM. Because this value is
-- ABSENT from validate_independence()'s gated set (`IN ('technical','managerial','financial')`,
-- kernel/lineage/s34-computed-grade-refusal.sql, the current head of that function, unedited by
-- any later delta -- confirmed by grep), it is treated EXACTLY as 'self-review' already is: NO
-- stamp-distinctness gate fires (because the writing invocation genuinely IS the dispatcher's),
-- and NO crediting rule reads it (this delta's own scope: the value exists to be recorded, not
-- yet consumed -- exactly the spec's own "no crediting rule reads it in v1" framing, transposed:
-- no NEW rule is minted here that reads it either). This delta therefore requires ZERO edit to
-- validate_independence() or to s41's D-6 human-only independence check (which gates on
-- ('managerial','financial') only, confirmed unaffected by grep) -- the CHECK widening alone is
-- the complete mechanism, verified by inspection of every function that inspects
-- review_detail.independence's value (validate_independence, the s41 D-6 block) before
-- authoring, per this delta's own PREREQUISITE note above.
--
-- ALTERNATIVE CONSIDERED AND REJECTED, ON THE RECORD (spec §3.5): dispatch-id-keyed stamp
-- distinctness (treating a dispatch id as a third stamp component). Rejected because no
-- server-witnessed dispatch-id channel exists for a non-writing subagent -- the id would be
-- dispatcher-asserted, a client-claimed identity doing independence duty, precisely the
-- lying-signature shape s17/s21 exist to refuse. Promotion from disclosure to claim is a future
-- amendment, named, not built, once a server-witnessed per-dispatch token exists (an s23
-- sibling).
--
-- HISTORY: safe -- the CHECK is re-issued WIDER (additive: every pre-existing independence value
-- stays legal; the new value is disjoint from the four already licensed). No function, trigger,
-- table, or column is touched -- ZERO edits verified by inspection (see MECHANISM above), the
-- smallest possible delta in this family.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form):
--   - INVARIANT: a review_detail row may declare independence='disclosed-isolated-dispatch' --
--     an honest disclosure that its verdict was produced by an isolated dispatch and is relayed
--     by the dispatcher's own writing invocation -- without triggering the stamp-distinctness
--     gate 'technical'/'managerial'/'financial' independence claims require, and without any
--     crediting rule (none exists yet) reading it as license.
--   - QUANTIFICATION UNIVERSE: the ONE CHECK this touches -- review_detail_independence_check
--     (s17, the sole home, re-issued here); every function that INSPECTS independence's value
--     (validate_independence/s34, the s41 D-6 block) -- verified unaffected, both named above,
--     by inspection before authoring, not merely asserted; sibling surfaces -- none: this value
--     is not read by review_write's payload validation (s43, which only checks key MEMBERSHIP,
--     not value vocabulary -- the CHECK is the value gate) nor by any engine/lp producer (the
--     defeat/belief layers read `independence` nowhere in engine/ledger_edb.py, confirmed by
--     grep before authoring).
--   - DENOMINATION: the independence vocabulary stays a closed, five-member set -- no proxy, no
--     numeric grade. 'disclosed-isolated-dispatch' records strictly more truth than
--     'self-review' while claiming nothing a stamp cannot witness (spec's own words).
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): SHAPE-fail-safe (adds one
-- vocabulary member, relaxes nothing) but routed under design/FABLE-BELIEF-SUBSTRATE-SPEC.md's
-- own ratification (rows 1914/1919), not claimed under the class-ratified track, per that spec's
-- own explicit instruction (§3.5's closing line, transcribed in MECHANISM above).
--
-- LIMITS (pre-registered, spec §3.5/§9):
--   - 'disclosed-isolated-dispatch' is a DISCLOSURE, not a witnessed claim -- promotion to a
--     server-witnessed independence grade awaits a dispatch-id channel that does not exist
--     (named above, not built).
--   - No crediting rule reads this value this delta, or any prior one -- recording it changes
--     no derived judgment until a FUTURE rule is ratified to consume it.
--   - Reaches reality only at a FUTURE world's birth; this builder's act does NOT itself apply it
--     to any existing world (runs-are-strictly-linear).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s54):
--   VALIDATE (reachable throwaway): apply the full chain through s54, then
--   -f s55-dispatch-grain-independence.sql (any position after s17 -- no ordering dependency on
--   s53/s54, per the PREREQUISITE note above).
--   REAL: NEVER applied to any existing world by this authoring act. Enters a FUTURE world's
--   birth chain via bootstrap/new-project.sh's LINEAGE_CHAIN, wired in the SAME commit as
--   s53/s54. Authored and scratch-witnessed on scratch schema pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (DROP+ADD CONSTRAINT).
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
-- ELEMENT 1 -- review_detail_independence_check WIDENED (five-member, +'disclosed-isolated-
-- dispatch'). Its ONE home (s17); DROP+ADD, never a second patching constraint.
-- ============================================================================================
ALTER TABLE :"schema".review_detail DROP CONSTRAINT IF EXISTS review_detail_independence_check;
ALTER TABLE :"schema".review_detail ADD CONSTRAINT review_detail_independence_check
    CHECK (independence IN
      ('self-review', 'technical', 'managerial', 'financial', 'disclosed-isolated-dispatch'));

COMMENT ON CONSTRAINT review_detail_independence_check ON :"schema".review_detail IS
  'kernel/lineage/s55-dispatch-grain-independence.sql widens s17''s four-member vocabulary by
   disclosed-isolated-dispatch (design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.5, Q6): an honest
   DISCLOSURE that a verdict was produced by an isolated dispatch and is relayed by the
   dispatcher''s own writing invocation -- NOT an independence claim. Treated exactly as
   self-review by validate_independence() (absent from its gated set, so no stamp-distinctness
   test fires) and read by no crediting rule this delta or any prior one.';
-- ============================================================================================
