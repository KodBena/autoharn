-- s67 REFUSAL-DIGEST BOUND (design/FABLE-S66-S67-JOURNAL-TOTALITY-SPEC.md §2, RATIFIED
-- 2026-07-27, ledger row 1514 item 1 -- "all should go in," verbatim). Second of the s66/s67
-- journal-totality pair, same s49 family: the refusal journal must record refusals under
-- hostile conditions, because the refusal path is exactly where hostile input arrives (the s65
-- lesson, restated once more). Sonnet-built per the standing delegation contract, from the
-- ratified spec.
--
-- PREREQUISITE / THE HEAD-BODY RULE (s45's own standing instruction): at this delta's
-- authoring the lineage head is s66 (kernel/lineage/s66-forged-stamp-journal-totality.sql,
-- this same commit -- the builder's own directory listing, confirmed before authoring). THE
-- ONE FUNCTION THIS DELTA RE-ISSUES, kernel.journal_write_refusal, is NOT touched by s66 (s66's
-- own header states plainly: "NO CHANGE to kernel.journal_write_refusal or the four (now seven)
-- boundary functions calling it" -- grep-verified against s66-forged-stamp-journal-totality.sql
-- above, which re-issues ONLY kernel.set_stamp). So the TRUE immediately-prior re-issue of
-- kernel.journal_write_refusal is s65 (kernel/lineage/s65-refusal-attempted-kind.sql Element 4),
-- NOT s66 -- stated here explicitly per the spec's own instruction ("the builder states which").
-- kernel.journal_write_refusal is `:"kern".`-namespaced, OUTSIDE gates/lineage_reissue_lineage.py's
-- own `:"schema".`-anchored citation-check universe (per that gate's own docstring; the SAME
-- disclosed exemption s65's own Element 4/Element 5 re-issues already name) -- the citation/
-- prior-body-sha256 line below is carried as a matter of this codebase's house idiom, NOT
-- mechanically gate-enforced, named here rather than silently assumed to be checked.
--
-- WHY (spec §2's own words): kernel.journal_write_refusal digests the refused payload WHOLE,
-- whatever its size (encode(sha256(convert_to(p_payload::text,'utf8')),'hex')). The service
-- caps write bodies at 1 MiB (MAX_WRITE_BODY_BYTES), but a direct psql caller bypasses the
-- service entirely -- the kernel journaler is the ONLY backstop on that path, and until this
-- delta it has none. RE-WITNESSED on this delta's own scratch world (pre-fix, s66probe, s15..
-- s65+s66 head): an oversized (>1 MiB) refused payload journals TODAY with a full 64-hex
-- digest computed over the whole payload (build report has the verbatim transcript) -- the
-- unbounded baseline this delta closes.
--
-- MECHANISM (spec §2, one bound): when octet_length(p_payload::text) exceeds 1,048,576 bytes
-- (the s51 artifact_too_large precedent, and the exact figure the service already enforces),
-- refusal_payload_digest is recorded NULL -- the SAME "not extractable" meaning s65 gave
-- refusal_attempted_kind beyond ITS OWN bound (256 bytes, a different column, the same shape of
-- reasoning at a different scale) -- and the refusal journals exactly as before in every OTHER
-- respect (oracle bump first, write-boundary lookup, attempted-actor/kind extraction, the
-- INSERT itself). BELOW the bound, byte-identical: the same sha256-over-canonical-text digest
-- computation as s43/s49/s65 left it, unconditionally. The digest is a grep handle, never a
-- join key (the row-1498 witness: joins anchor on refusal_id) -- losing it beyond the bound
-- costs an attacker-sized payload its vanity hash, nothing else; the refusal ITSELF (surface,
-- sqlstate, message, attempted actor/role/kind) is unaffected and fully recorded regardless of
-- payload size.
--
-- THE CHECK MUST WIDEN TOO (a consequence the spec's prose states but does not dwell on --
-- surfaced explicitly here rather than silently done): s43's own
-- refusal_payload_digest_kind_shape CHECK is MANDATORY-TWO-WAY --
-- `(kind = 'write_refused') = (refusal_payload_digest IS NOT NULL)` -- which would REFUSE the
-- very row this delta means to accept (a write_refused row with digest NULL). This delta
-- therefore ALSO loosens that one CHECK to ONE-WAY -- `refusal_payload_digest IS NULL OR
-- kind = 'write_refused'` -- the SAME idiom refusal_attempted_actor (s43) and
-- refusal_attempted_kind (s65) already use for "legitimately NULL on the licensed kind too."
-- This is the one genuinely non-additive act in this delta (a CHECK loosened, not merely a
-- function re-issued) -- named plainly in FAIL-SAFE CLASSIFICATION below, not folded silently
-- into "just a digest bound."
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a)): the payloads this delta bounds are EXACTLY those
-- reaching kernel.journal_write_refusal -- every one of the SEVEN boundary functions'
-- refusal legs (grep-enumerated, current count seven as of this lineage's head: ledger_write,
-- review_write, registration_write, obligation_write -- all four born s43; artifact_write --
-- s51; obligation_revoke -- s57; missive_dispose -- s58), all calling journal_write_refusal
-- identically -- this ONE re-issue covers every call site, the same "one home" argument s43's
-- own header makes and s49/s65 both re-verify rather than merely assume. TABLES/COLUMNS: no new
-- column -- refusal_payload_digest already exists (s43); only its NULLABILITY circumstance
-- widens (function-computed value, and the CHECK licensing it). KINDS: unchanged. VIEWS:
-- unchanged -- ledger_current/countersigned_in_force already expose refusal_payload_digest
-- (s43), nullable-or-not is not a column-list question. compute_row_hash: UNCHANGED -- no new
-- column to append, and hashfield(r.refusal_payload_digest) already renders NULL correctly (the
-- s26 hashfield convention handles NULL for every existing nullable column identically; a
-- write_refused row's digest going from "always populated" to "sometimes NULL" changes what
-- gets HASHED, never the hashing MECHANISM or the column SET, so no re-issue is needed here --
-- verified by reading s65's own 98-column body, unaltered). ENGINE: unaffected, grep-verified
-- across engine/ for refusal_payload_digest -- ZERO hits (the s65 finding, restated: no
-- exporter emits any refusal_* column today). GATES: hash-coverage (unaffected, no column/
-- function-signature change to compute_row_hash); kind-shape manifest
-- (gates/kind_shape_manifest_gate.py's CHAIN extended through s67, this same commit; the
-- MANIFEST row for refusal_payload_digest re-classified two-way -> one-way, matching the
-- widened CHECK exactly); lineage-reissue-lineage (citation of s65 stated above, NOT
-- mechanically checked for a `:"kern".`-namespaced function -- named, not silently assumed
-- enforced); kernel-function-census (bank updated same commit -- kern:journal_write_refusal's
-- hash changes; schema-side unaffected since no :"schema" function is touched by THIS file).
--
-- DENOMINATION: the 1,048,576-byte bound is NOT a bare round literal -- it is s51's own
-- artifact_too_large figure (2^20, the same "1 MiB" the service's MAX_WRITE_BODY_BYTES already
-- enforces), reused rather than re-derived, so a payload the service itself would already have
-- refused for size is never the FIRST place this bound bites -- it exists for the direct-psql
-- bypass path the service's own cap cannot reach. octet_length (bytes, never a lying
-- self-reported strlen), the same denomination choice s51 and s65's own length CHECK both use.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT CLASS-RATIFIED
-- FAIL-SAFE, stated plainly (s43/s49/s65/s66's own precedent for this same honesty
-- requirement): this delta re-issues an EXISTING function body via CREATE OR REPLACE
-- (kernel.journal_write_refusal) AND loosens an existing MANDATORY-TWO-WAY CHECK to one-way
-- (refusal_payload_digest_kind_shape) -- neither is a letter-2(a) "only adds" shape, even
-- though the EFFECT is strictly fail-safe (more refusals survive with a full record in every
-- respect except one grep handle; nothing ACCEPTED before is accepted differently; every
-- refusal that journaled a digest before still journals the SAME digest, below the bound). It
-- ships under the maintainer's OWN EXPLICIT RATIFICATION (design/FABLE-S66-S67-JOURNAL-
-- TOTALITY-SPEC.md, ledger row 1514 item 1, "all should go in" -- verbatim), read per the
-- 2026-07-11 vocabulary note, exactly the posture s43/s49/s65/s66 shipped under for the same
-- reason.
--
-- LIMITS (pre-registered, matching s43/s49/s65/s66's own disclosure convention):
--   - refusal_payload_digest is NULL for exactly two reasons after this delta, indistinguishable
--     from the column alone: (a) the payload exceeded 1,048,576 bytes (this delta), or
--     (b)... there is no (b) today -- s43 minted this column mandatory-on-write_refused
--     originally, so pre-s67 every write_refused row's digest was populated; this delta's own
--     NULL is a NEW, single-cause state. Named so a future delta that adds a SECOND
--     NULL-producing cause does not silently conflate two "not extractable" reasons the way
--     refusal_attempted_kind's own NULL already can (that column's own LIMITS section, s65).
--   - The bound applies to the WHOLE payload's canonical text (octet_length(p_payload::text)),
--     not to any individual key inside it -- a payload with one enormous value and otherwise
--     tiny keys is bounded the same as one uniformly large, matching s51's own artifact-size
--     reasoning (the whole write body is what the service caps, not a per-field measure).
--   - This delta does not change the attempted-actor guard (s49, unchanged), the
--     attempted-kind extraction (s65, unchanged), or what happens when the journal INSERT
--     itself fails (s43's own named, disclosed loud-abort/sequence-gap/server-log composition,
--     untouched here).
--   - Every other named limit in s17/s23/s43/s49/s65/s66's own headers is unchanged by this
--     delta and not re-stated in full here.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s66): schema/kern/role
-- are psql variables so this delta is VALIDATED on a throwaway substrate before any real apply.
--   VALIDATE (reachable throwaway): apply the FULL s15..s66 chain (s65's own VALIDATE block +
--   s66), THEN -f s67-refusal-digest-bound.sql (genesis seed per s26; register the
--   write-boundary principal before exercising any refusal path, or the journaler aborts
--   loudly by design, unchanged since s43).
--   REAL: NEVER applied to any existing world by this authoring act (runs-are-strictly-linear,
--   2026-07-11). Enters a FUTURE world's birth chain via bootstrap/new-project.sh's
--   LINEAGE_CHAIN narrative (this same commit) and its GENERATED apply loop. Authored and
--   scratch-witnessed on a scratch schema pair in the TOY db only (world s66probe /
--   s66probe_kernel / s66probe_rw, torn down after).
-- Run as the schema owner (bork). Idempotent (DROP+ADD CONSTRAINT; CREATE OR REPLACE FUNCTION).
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
-- ELEMENT 1 -- refusal_payload_digest_kind_shape WIDENED two-way -> one-way (the
-- refusal_attempted_actor / refusal_attempted_kind idiom, s43/s65): a write_refused row MAY
-- carry a NULL digest now (the oversized-payload case); no other kind may carry one, unchanged.
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_payload_digest_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_payload_digest_kind_shape CHECK (
    refusal_payload_digest IS NULL OR kind = 'write_refused');

COMMENT ON COLUMN :"schema".ledger.refusal_payload_digest IS
  'SHA-256 (hex) of the refused payload''s canonical text (payload::text of the jsonb
   argument -- key-sorted, deterministic on a given server; a cross-major-version recompute
   is a named limit, diagnostic linkage only). Digest, never verbatim (R4, ratified:
   adversary-authored content gets no permanent hash-chained storage channel). LEGITIMATELY
   NULL when the refused payload''s canonical text exceeds 1,048,576 bytes (s67:
   kernel/lineage/s67-refusal-digest-bound.sql -- the direct-psql-bypass hazard the service''s
   own MAX_WRITE_BODY_BYTES cap cannot reach; a grep handle lost, never the refusal record
   itself, which is otherwise complete) -- the SAME "not extractable beyond a named bound"
   shape refusal_attempted_kind (s65) already uses at a different column and a different
   scale. kernel/lineage/s43-typed-verdict-write-boundary.sql;
   kernel/lineage/s67-refusal-digest-bound.sql.';

-- ============================================================================================
-- ELEMENT 2 -- kernel.journal_write_refusal RE-ISSUED: the s65 body (kernel/lineage/
-- s65-refusal-attempted-kind.sql Element 4 -- the TRUE immediately-prior re-issue; s66 does NOT
-- touch this function, see this file's own header), BYTE-IDENTICAL above and below the new
-- bound, with ONE addition -- the payload-size check gating the digest computation. No other
-- line of this function changes: the oracle bump stays first, the write-boundary principal
-- lookup and its own loud abort stay exactly as s43/s49/s65 left them, the s49 attempted-actor
-- guard and s65 attempted-kind extraction are untouched, and the journal INSERT's own
-- loud-abort-on-failure semantics are untouched.
-- prior-body-sha256: 59f5ba9b2a27015d51d692f90f97d043fa250b965b20a8239ca8bdb0c771362b (s65-refusal-attempted-kind.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"kern".journal_write_refusal(
    p_surface text, p_payload jsonb, p_sqlstate text, p_message text)
    RETURNS bigint LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_wb bigint;
  v_attempted bigint;
  v_attempted_kind text;
  v_digest text;
  v_id bigint;
BEGIN
  -- the oracle bump, BEFORE the journal INSERT (non-transactional, survives everything --
  -- s43 Element 5): if the INSERT below then fails, the sequence shows a counted gap the
  -- verify-chain reconciliation names. UNCHANGED by s67.
  PERFORM nextval('refusal_seq');
  SELECT id INTO v_wb FROM principal WHERE name = 'write-boundary';
  IF v_wb IS NULL THEN
    RAISE EXCEPTION 'write boundary: the ''write-boundary'' tool principal is not registered in this world -- refusal recording has no authoring identity (kernel/lineage/s43-typed-verdict-write-boundary.sql Element 6; bootstrap/new-project.sh''s birth sequence registers it). The original refusal (SQLSTATE %) was: %', p_sqlstate, p_message;
  END IF;
  -- the ATTEMPTED identity: the explicit payload actor when it resolves to a registered id,
  -- else the session's own standing-declaration default (the identity that WOULD have been
  -- attributed); NULL when neither resolves -- the role below is still always known.
  --
  -- s49 GUARD (kernel/lineage/s49-journaler-overflow-guard.sql): the regex `^[0-9]+$` admits
  -- arbitrary-length digit strings, but bigint's own range does not -- an over-bigint numeral
  -- previously raised 22003 HERE; the cast is total (UNCHANGED by s67).
  IF (p_payload ? 'actor') AND (p_payload->>'actor') ~ '^[0-9]+$' THEN
    BEGIN
      SELECT id INTO v_attempted FROM principal WHERE id = (p_payload->>'actor')::bigint;
    EXCEPTION WHEN numeric_value_out_of_range THEN
      v_attempted := NULL;
    END;
  END IF;
  IF v_attempted IS NULL THEN
    SELECT principal_id INTO v_attempted FROM principal_role WHERE db_role = session_user;
  END IF;
  -- s65 (kernel/lineage/s65-refusal-attempted-kind.sql): the ATTEMPTED kind, extracted from the
  -- refused payload -- TOTAL, NULL when not extractable (key absent, non-string, or over the
  -- 256-byte bound). UNCHANGED by s67.
  IF jsonb_typeof(p_payload->'kind') = 'string'
     AND octet_length(p_payload->>'kind') <= 256 THEN
    v_attempted_kind := p_payload->>'kind';
  ELSE
    v_attempted_kind := NULL;
  END IF;
  -- s67 BOUND (kernel/lineage/s67-refusal-digest-bound.sql): the refused payload's canonical
  -- text is digested WHOLE only up to 1,048,576 bytes (the s51 artifact_too_large precedent --
  -- the same figure the service's own MAX_WRITE_BODY_BYTES already enforces on the served
  -- path, restated here for the direct-psql bypass that cap cannot reach). Over the bound,
  -- refusal_payload_digest is recorded NULL -- "not extractable," the SAME shape s65 gave
  -- refusal_attempted_kind beyond ITS bound, applied here to a different column at a different
  -- scale. The refusal ITSELF (surface/sqlstate/message/attempted actor/role/kind) is unaffected
  -- and journals in full regardless of payload size -- only the digest, a grep handle never a
  -- join key (row-1498 witness), is foreclosed on an attacker-sized payload.
  IF octet_length(p_payload::text) > 1048576 THEN
    v_digest := NULL;
  ELSE
    v_digest := encode(sha256(convert_to(p_payload::text, 'utf8')), 'hex');
  END IF;
  INSERT INTO ledger (kind, statement, actor,
                      refusal_sqlstate, refusal_message, refusal_surface,
                      refusal_payload_digest, refusal_attempted_actor, refusal_attempted_role,
                      refusal_attempted_kind)
  VALUES ('write_refused',
          format('write refused at surface %s (SQLSTATE %s)', p_surface, p_sqlstate),
          v_wb,
          p_sqlstate, p_message, p_surface,
          v_digest,
          v_attempted, session_user,
          v_attempted_kind)
  RETURNING id INTO v_id;
  RETURN v_id;
END; $fn$;
REVOKE ALL ON FUNCTION :"kern".journal_write_refusal(text, jsonb, text, text) FROM PUBLIC;

COMMENT ON FUNCTION :"kern".journal_write_refusal(text, jsonb, text, text) IS
  'The ONE home of "a refusal becomes a committed write_refused row" (s43 Element 4), called
   only from inside the SECURITY DEFINER boundary functions (no role holds EXECUTE). Bumps the
   refusal_seq oracle FIRST (non-transactional), then journals: actor = the write-boundary tool
   principal; the attempted identity in refusal_attempted_* (s49: the actor cast is TOTAL); the
   attempted kind token in refusal_attempted_kind (s65: TOTAL, 256-byte bound); the payload as a
   SHA-256 digest, NULL when the payload''s canonical text exceeds 1,048,576 bytes (s67:
   kernel/lineage/s67-refusal-digest-bound.sql -- the direct-psql-bypass hazard the service''s
   own size cap cannot reach). If the journal INSERT itself fails the exception propagates -- a
   loud abort, a counted sequence gap, the server log as residual coverage (fail-safe on both
   legs, unchanged by s49/s65/s67). kernel/lineage/s43-typed-verdict-write-boundary.sql;
   kernel/lineage/s49-journaler-overflow-guard.sql; kernel/lineage/
   s65-refusal-attempted-kind.sql; kernel/lineage/s67-refusal-digest-bound.sql.';
-- ============================================================================================
