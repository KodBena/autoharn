-- s18 CRITERION-REVIEWER PRINCIPALS + INSERT-only grants (consult 37 §1/§3). e18 arms K=2 fresh
-- FIRST-CONTACT criterion reviews of the final artifact (review_fixpoint). Each reviewer is a genuinely
-- distinct principal with its OWN interception stamp, and — the load-bearing fence — INSERT-only on the
-- review rows with NO SELECT on the unit ledger. A reviewer therefore cannot read the author's rows, the
-- fix history, prior reviews, or the other lens's verdict: first-contact is enforced by privilege, not by
-- politeness. The artifact row id a reviewer attests is a fact supplied in its brief, never read from the
-- ledger (an FK check on `regards` runs with the owner's privilege, so INSERT needs no SELECT).
--
-- Additive delta on the s15/s16 kernel + s17-stamp-mechanism + s17-independence-vocabulary. Parameterized
-- (schema/role, s15 defaults; rev1/rev2 the two reviewer roles). NOT subject-visible prose. Kernel-side
-- only — nothing armed. The reviewers' per-session stamp secrets are provisioned at arm (like the
-- author's), not here.
--     VALIDATE:  ... -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--                    -f s18-criterion-principals.sql
--
-- Token map (M4): db qbx, author role qbx_rw; reviewer roles rev1=correctness lens, rev2=conformance lens
-- (the lens↔role mapping lives only here, kernel-side; the reviewer learns its lens from its brief).
--
-- Note on psql var scope: psql interpolates :'x' / :"x" only OUTSIDE dollar-quoted bodies. The role/schema
-- names are therefore threaded into DO blocks via session GUCs (set below, where interpolation works) and
-- read back with current_setting(); the plain GRANT/REVOKE statements use :"x" directly.

\if :{?schema}
\else
  \set schema public
\endif
\if :{?rev1}
\else
  \set rev1 qbx_rev1
\endif
\if :{?rev2}
\else
  \set rev2 qbx_rev2
\endif
\if :{?kern}
\else
  \set kern kernel
\endif

SELECT set_config('e18.schema', :'schema', false),
       set_config('e18.rev1',   :'rev1',   false),
       set_config('e18.rev2',   :'rev2',   false),
       set_config('e18.kern',   :'kern',   false);

-- 1. The two reviewer principals. LOGIN roles, distinct from the author role and from each other, so their
--    interception stamps (stamp_agent) differ — the review_fixpoint first-contact + stamp-distinct joins
--    hold by construction. Created idempotently.
DO $$
DECLARE r1 text := current_setting('e18.rev1'); r2 text := current_setting('e18.rev2');
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r1) THEN EXECUTE format('CREATE ROLE %I LOGIN', r1); END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r2) THEN EXECUTE format('CREATE ROLE %I LOGIN', r2); END IF;
END $$;

-- 2. INSERT-only on the review rows: a reviewer may append its attestation (a kind='review' ledger row)
--    and its review_detail (independence + verdict), and nothing else. Explicitly REVOKE SELECT/UPDATE/
--    DELETE on the unit ledger so no reviewer can read what came before it or mutate what exists.
REVOKE ALL ON :"schema".ledger        FROM :"rev1", :"rev2";
REVOKE ALL ON :"schema".review_detail FROM :"rev1", :"rev2";
GRANT INSERT ON :"schema".ledger        TO :"rev1", :"rev2";
GRANT INSERT ON :"schema".review_detail TO :"rev1", :"rev2";

-- 2b. THE TRIGGER-CHAIN READS (finding 45): the kernel's validation triggers are SECURITY INVOKER — they
--     run AS THE INSERTING ROLE and read catalog/structural state: set_actor reads
--     kernel.principal_role(db_role, principal_id); validate_review reads ledger(id, actor);
--     validate_independence reads ledger(id, stamp_agent, stamp_verified, regards). A zero-SELECT writer
--     therefore CANNOT pass validation (both e18 criterion reviewers' first writes were refused inside
--     set_actor — the banked seen-red). The fence-honoring resolution is COLUMN-LEVEL grants on exactly
--     the structural columns the trigger chain reads — never a content column: statement, rationale,
--     evidence, confidence and the whole of review_detail remain unreadable, table-level SELECT remains
--     FALSE (first-contact blindness is content-blindness; the structural grant exposes only ids/stamps/
--     the regards graph). Kernel functions stay untouched (s18 = s17 byte-identical, Addendum A).
GRANT USAGE ON SCHEMA :"kern" TO :"rev1", :"rev2";
GRANT SELECT (db_role, principal_id) ON :"kern".principal_role TO :"rev1", :"rev2";
GRANT SELECT (id, actor, stamp_agent, stamp_verified, regards) ON :"schema".ledger TO :"rev1", :"rev2";
-- ... and the chain's ONE function call: set_stamp() invokes kernel.stamp_valid (SECURITY DEFINER — the
-- sanctioned validator that never returns the secret; s17 granted EXECUTE to the author role only, so the
-- reviewers' second write attempt was refused HERE — the finding-45 class's second member, same run).
-- The full chain, enumerated: set_actor (principal_role read ✓) -> set_stamp (stamp_valid EXECUTE, this
-- grant) -> validate_enacts/amends/answers (no-op on NULL fields) -> validate_review (ledger id/actor ✓)
-- -> one_row_per_insert (transition table, no grant) -> review_detail: validate_independence (ledger
-- stamp columns ✓, no function calls). Nothing else executes as the inserting role.
GRANT EXECUTE ON FUNCTION :"kern".stamp_valid(text, text, bigint, text) TO :"rev1", :"rev2";

-- INSERT needs nextval on the surrogate-key sequences (USAGE, not SELECT — USAGE cannot read arbitrary
-- rows, only advance/allocate the sequence). Granted for exactly the two review tables' identity sequences.
DO $$
DECLARE sch text := current_setting('e18.schema'); r1 text := current_setting('e18.rev1');
        r2 text := current_setting('e18.rev2'); seqname text; tbl text;
BEGIN
  FOREACH tbl IN ARRAY ARRAY['ledger','review_detail'] LOOP
    -- only tables with an 'id' column have an identity sequence to grant (review_detail is keyed by
    -- ledger_id, an FK, and allocates no sequence of its own).
    IF EXISTS (SELECT 1 FROM information_schema.columns
                WHERE table_schema = sch AND table_name = tbl AND column_name = 'id') THEN
      seqname := pg_get_serial_sequence(format('%I.%I', sch, tbl), 'id');
      IF seqname IS NOT NULL THEN
        EXECUTE format('GRANT USAGE ON SEQUENCE %s TO %I, %I', seqname, r1, r2);
      END IF;
    END IF;
  END LOOP;
END $$;

-- 3. NEGATIVE CONTROL, asserted here at build (re-run at arm against the live db as each reviewer role):
--    a reviewer must NOT be able to SELECT the unit ledger. This block RAISES if the privilege leaked.
DO $$
DECLARE sch text := current_setting('e18.schema'); r text; col text;
BEGIN
  FOREACH r IN ARRAY ARRAY[current_setting('e18.rev1'), current_setting('e18.rev2')] LOOP
    -- table-level SELECT must be FALSE (the column grants below never widen to the table)
    IF has_table_privilege(r, format('%I.ledger', sch), 'SELECT') THEN
      RAISE EXCEPTION 'negative-control FAILED: reviewer % has TABLE-level SELECT on %.ledger — first-contact fence breached', r, sch;
    END IF;
    IF NOT has_table_privilege(r, format('%I.ledger', sch), 'INSERT') THEN
      RAISE EXCEPTION 'reviewer % lacks INSERT on %.ledger — cannot attest', r, sch;
    END IF;
    IF has_table_privilege(r, format('%I.review_detail', sch), 'SELECT') THEN
      RAISE EXCEPTION 'negative-control FAILED: reviewer % has SELECT on %.review_detail', r, sch;
    END IF;
    -- CONTENT columns must be unreadable (the fence's substance: first-contact = content-blindness).
    -- The structural columns (id/actor/stamp_agent/stamp_verified/regards) are granted for the
    -- SECURITY-INVOKER trigger chain (finding 45) — content columns must never join them.
    FOREACH col IN ARRAY ARRAY['statement','rationale','evidence','confidence'] LOOP
      IF has_column_privilege(r, format('%I.ledger', sch), col, 'SELECT') THEN
        RAISE EXCEPTION 'negative-control FAILED: reviewer % can SELECT content column %.ledger.% — fence breached', r, sch, col;
      END IF;
    END LOOP;
    -- and the trigger-chain structural columns MUST be readable (else every reviewer write is refused
    -- inside set_actor/validate_review/validate_independence — the finding-45 seen-red).
    FOREACH col IN ARRAY ARRAY['id','actor','stamp_agent','stamp_verified','regards'] LOOP
      IF NOT has_column_privilege(r, format('%I.ledger', sch), col, 'SELECT') THEN
        RAISE EXCEPTION 'reviewer % lacks structural column SELECT on %.ledger.% — the trigger chain will refuse its write (finding 45)', r, sch, col;
      END IF;
    END LOOP;
    -- ... and the chain's one function call must be executable (finding 45, second member: set_stamp ->
    -- stamp_valid EXECUTE was author-only; the reviewers' SECOND attempt was refused there).
    IF NOT has_function_privilege(r, format('%I.stamp_valid(text, text, bigint, text)', current_setting('e18.kern')), 'EXECUTE') THEN
      RAISE EXCEPTION 'reviewer % lacks EXECUTE on %.stamp_valid — set_stamp will refuse its write (finding 45)', r, current_setting('e18.kern');
    END IF;
  END LOOP;
  RAISE NOTICE 'negative-control OK: rev1/rev2 hold INSERT + structural-column SELECT only; table-level SELECT false; content columns and review_detail unreadable';
END $$;
