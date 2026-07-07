-- s19 TRIGGER SEARCH-PATH FORECLOSURE — the set_actor schema-literal class (findings 16, 37, 45).
--
-- An ADDITIVE delta applied ON TOP of the s15 kernel (the established remediation-delta idiom, cf.
-- s17-stamp-mechanism.sql / s13-remediation-*), NOT a retro-edit of a frozen sNN record (ADR-0005 Rule 8)
-- and NOT a second hand-copy of the kernel body (ADR-0012 P1: one home per mechanism).
--
-- WHY (operator-side prose; NOT subject-visible — only the catalog objects inside the opaque db are):
--
--   s15's set_actor() reads `kernel.principal_role` with a HARDCODED schema literal `kernel.` while the
--   kernel schema is parameterized `:kern` everywhere else. On any deployment where the kernel does NOT
--   live in a schema literally named `kernel` (every non-default-schema / isolated-db kernel — the vsr
--   pattern, and every validate-mode throwaway), the reader resolves nothing, NEW.actor stays NULL, and
--   the ledger's `actor NOT NULL` constraint REFUSES an actor-omitted write. The sibling set_stamp()
--   (s17) already resolves via `SET search_path` and its own comment names s15's set_actor as
--   "frozen" — the fix was always owed to a new increment, not a retro-edit.
--
--   Findings 16, 37, and 45 are three instances of ONE class, foreclosed here structurally, not patched:
--
--   CLOSURE STATEMENT (ADR-0000 Rule 2a):
--     - INVARIANT: every kernel trigger/function resolves KERNEL objects via the search_path mechanism
--       (an unqualified reference resolved by a per-function `SET search_path` carrying :"kern"), never a
--       hardcoded schema literal.
--     - QUANTIFICATION UNIVERSE — enumerated by grep over kernel/lineage/ (the whole trigger/function
--       family across all generations AND the SECURITY-INVOKER chain behind every INSERT, the finding-45
--       axis). In the CURRENT (s15+) generation's BEFORE-INSERT chain the KERNEL-object readers are:
--         · set_actor()  — reads :kern.principal_role   → HARDCODED `kernel.` (the violator; fixed here).
--         · set_stamp()  — reads via SECURITY DEFINER stamp_valid, already `SET search_path = :kern`.
--         · validate_enacts/review/amends/answers() — read only the LEDGER (own :schema), unqualified,
--           resolved by the role's login search_path; they touch NO kernel object, so they are outside
--           the "kernel-object resolution" scope and carry no schema literal (verified: not in the class).
--       set_actor is thus the SOLE in-chain violator for the live generation. The historical standalone
--       generations s13/s14 carry the identical hardcode but are FROZEN records (ADR-0005 Rule 8) and are
--       NOT the deployment target — the live kernel applies s15 + these deltas + s19. Named-not-edited,
--       per the never-retro-edit rule; a future s13/s14 REDEPLOYMENT would apply an analogous delta.
--     - DENOMINATION: the fix is the RESOLUTION MECHANISM itself (search_path), never a copied schema
--       name. This delta introduces no new `kernel.`/`:kern`-qualified read inside a function body; the
--       body reference is UNQUALIFIED and the schema set is carried on the function's `SET search_path`.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s17): schema/kern/role are psql vars
--   so the delta is VALIDATED on a throwaway substrate before any real apply.
--     VALIDATE (reachable throwaway, NON-default kern proves the class is closed):
--        psql -h 192.168.122.1 -d harness -v schema=s19val -v kern=s19val_kernel -v role=s19val_rw \
--          -f s15-schema.sql -f s19-trigger-search-path.sql
--     REAL (kern='kernel'; the fix is a no-op behavior change there — the hardcode already matched):
--        psql -h 192.168.122.1 -d vsr -f s15-schema.sql -f s19-trigger-search-path.sql
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE + DROP/CREATE TRIGGER).

\if :{?schema}
\else
  \set schema public
\endif
\if :{?kern}
\else
  \set kern kernel
\endif

-- search_path carries :"kern" (interpolated HERE, outside the $fn$ body where psql vars do not expand),
-- so the body reads principal_role UNQUALIFIED and it resolves in the kernel schema in BOTH validate mode
-- (custom kern) and real apply (kern='kernel') — the exact set_stamp idiom, applied to set_actor.
CREATE OR REPLACE FUNCTION :"schema".set_actor() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
BEGIN
  IF NEW.actor IS NULL THEN
    SELECT principal_id INTO NEW.actor FROM principal_role WHERE db_role = current_user;
  END IF;
  RETURN NEW;
END; $fn$;

-- Re-assert the trigger (unchanged name/order — set_actor still fires first among the alphabetical
-- BEFORE-INSERT chain, before set_stamp and the validate_* SoD reader).
DROP TRIGGER IF EXISTS set_actor ON :"schema".ledger;
CREATE TRIGGER set_actor BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".set_actor();
