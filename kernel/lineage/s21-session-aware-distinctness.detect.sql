-- s21-session-aware-distinctness.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s21 file itself (ADR-0005 Rule 8).
--
-- FIXED (zero-context audit, 2026-07-15): the previous version of this file detected s21 by the
-- mere EXISTENCE of a trigger named `validate_independence` on `review_detail` -- but s17
-- (s17-independence-vocabulary.sql, folded into high_watermark_1.sql) ALSO creates a trigger of
-- that exact name, wired to the PRE-s21 function body (agent-only distinctness, no
-- stamp_session). On a fresh high_watermark_1-only deployment the s17 trigger exists, so the old
-- query returned applied=true and `./migrate` would silently skip s21's real fix -- the
-- (stamp_session, stamp_agent)-PAIR distinctness check -- while reporting the lineage head as
-- s21. Witnessed via `pg_get_functiondef`: the live function body was the s17 (pre-s21) shape
-- while the old detect said applied=true.
--
-- Fixed by testing the function BODY, not the trigger's name: s21's
-- `validate_independence()` is the ONLY generation of this function that reads `stamp_session`
-- at all (s17's body reads `stamp_agent` alone -- see s17-independence-vocabulary.sql; s21's own
-- header names the fix as exactly this: "an invocation's identity is the PAIR
-- (stamp_session, stamp_agent), never stamp_agent alone"). `stamp_session` is therefore a
-- discriminating, semantic fingerprint of s21's actual behavior change, not a proxy like a
-- comment string or the trigger's name (which s21 deliberately keeps unchanged from s17, since
-- it replaces the function in place rather than renaming it). The trigger-exists check is kept
-- as a second, ANDed condition (defense in depth: the function alone existing with no trigger
-- wired to it would be a different, also-real defect) rather than replaced outright.
SELECT EXISTS (
    SELECT 1 FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_proc p ON p.oid = t.tgfoid
    WHERE n.nspname = :'schema' AND c.relname = 'review_detail'
      AND t.tgname = 'validate_independence'
      AND pg_get_functiondef(p.oid) LIKE '%stamp_session%'
) AS applied;
