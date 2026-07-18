-- s51 ARTIFACT STORE -- CONTENT-ADDRESSED CUSTODY (design/FABLE-ARTIFACT-STORE-SPEC.md,
-- "Status: Fable-authored 2026-07-18, ratified-to-author same date (maintainer, decision queue;
-- his framing verbatim: 'a new table precisely for "artifacts that should be kept"')". Build
-- basis for ONE kernel lineage delta (this file, next free sNN at build time -- s46..s50 exist,
-- s51 free) + its CLI verb. Sonnet-executed per the standing delegation contract, from this
-- ratified spec.
--
-- THE CUSTODY GAP (spec's own framing): ledger rows reference external artifacts by hash
-- (charter registrations per design/FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md; the s48 witness-ref
-- `Artifact` arm). The hash guarantees identity but not retrievability -- the referent lives
-- outside the database's own custody domain, so a database backup does not cover what its own
-- records rely on. This delta makes the database PRIMARY custody for exactly the essential-
-- records class the spec's amendment delineates (charters, commission texts, ratified specs,
-- attestation bodies, witness transcripts a ledger row cites by hash; NEVER the governed
-- project's own product artifacts, whose custody stays git/build-systems).
--
-- MECHANISM (spec sections 1-3):
--   1. kernel.artifact -- content-addressed: hash (sha256 hex, PK), bytes (bytea), size (bigint,
--      derived server-side and CHECKed against octet_length(bytes)), media_type (closed
--      vocabulary v1: text/markdown, text/plain, application/toml, application/json),
--      registered_at, registered_by (principal, resolved by the same s40/s43 attribution
--      discipline as every write). Append-only: no UPDATE/DELETE grants to any non-owner role,
--      the TRIGGER surface refuses both. Content-addressing makes re-registration of identical
--      bytes an idempotent no-op that returns the existing hash (not an error, not a duplicate
--      row).
--   2. kernel.artifact_write(p_payload jsonb) -- the FIFTH SECURITY DEFINER function, same shape
--      discipline as s43's four: typed verdict (kernel.write_verdict, the s43 type, reused --
--      no new type minted), refusal caught and journaled through s43's own ONE journaler
--      (kernel.journal_write_refusal -- ADR-0012 P1, one home, never a second copy) as a
--      committed write_refused row, digest only (the bytes NEVER enter the refusal journal --
--      this is a STRUCTURAL guarantee of reusing journal_write_refusal unchanged: it only ever
--      computes and stores sha256(p_payload::text), never the payload itself, so the base64
--      bytes traveling inside p_payload can never land in a stored column regardless of which
--      caller invokes it -- R4's "digest, never verbatim" ratified for s43 is inherited here by
--      construction, not re-implemented). Server-side hash computation with a mismatch refusal
--      if the caller also asserts a hash (assert-and-verify -- the caller may not name a hash
--      the server did not compute). SIZE CAP AS A TYPED REFUSAL: artifact_too_large at 1 MiB v1
--      -- a DELIBERATE CONSTANT, stated here per the spec's own instruction: charters, TOMLs,
--      and specs are KB-scale text; 1 MiB (1048576 bytes) is roughly 100x the largest charter/
--      spec this project has authored to date, headroom for a large multi-file spec bundle while
--      remaining firmly in "governance register text", never "binary blob" territory -- raising
--      the cap is an amendment with a stated need, never a silent bump (spec's own words,
--      transcribed). TRANSPORT: bytes travel base64 in the jsonb payload; the CLI feeds the
--      payload via stdin/-f (a local temp file loaded into a psql variable by the SAME
--      value-carrier mechanism kernel_write() already uses -- psql's own `:'var'` literal-quoted
--      substitution, ADR-0012's interpreter-boundary amendment's "bound placeholder" -- never a
--      command-line `-v` argument for this payload, and never `-c`, matching the argstrlen-wall
--      and psql-c-no-op lessons already witnessed and fixed project-wide (ledger rows 1637/1643):
--      MAX_ARG_STRLEN (131072 bytes on Linux) caps any ONE execve argument, and a 1 MiB artifact
--      base64s to ~1.4 MiB, so the payload must reach psql through a channel with no exec-arg
--      ceiling -- stdin/file content has none).
--   3. led artifact put/get/stat -- the verb surface (template-side, see led.tmpl/legacy-
--      led.tmpl). put prints the hash; get verifies bytes-vs-hash on the way out and REFUSES to
--      emit on mismatch (a corrupt store must fail loud, never serve silently wrong bytes); stat
--      shows size/media/registrant without bytes.
--   4. References stay hash-only. NO ledger column changes, NO new ledger kind, NO change to
--      compute_row_hash or the two column-complete views (ledger_current/countersigned_in_force)
--      -- this delta's only touch on the existing s43 surface is WIDENING the closed
--      refusal_surface_check CHECK by one member ('artifact'), a pure value-vocabulary addition
--      (see ELEMENT 2 below), exactly the class of change s43's own kind-vocabulary widening
--      already established as safe (HISTORY, below).
--   5. BOUNDARY: NOT routed in v1 (spec's own explicit scope line) -- reachable via
--      ./legacy/led (and any direct-psql world verb) only; `./led artifact ...` (the served
--      path) REFUSES, teaching ./legacy/led, per this delta's own led.tmpl change -- the served
--      route table is NOT extended (spec's build-conditions section, verbatim: "if the boundary
--      cannot carry it, the verb refuses teaching ./legacy/led -- do not extend the route
--      table"). Adding /artifacts/{hash} routes is a route-table amendment under the
--      read-surface spec's own re-ratification discipline, named as future work, out of scope
--      here.
--
-- PREREQUISITE: this delta REQUIRES s43 (kernel/lineage/s43-typed-verdict-write-boundary.sql)
-- applied first -- a HARD dependency: artifact_write is the FIFTH member of s43's own
-- SECURITY DEFINER write-boundary family, reuses s43's write_verdict TYPE and
-- journal_write_refusal FUNCTION unchanged, and widens s43's own refusal_surface_check CHECK.
-- Applying this file on a pre-s43 kernel fails loudly at CREATE OR REPLACE FUNCTION time (no
-- prior write_verdict type, no journal_write_refusal to call) -- the correct, disclosed failure
-- mode for a hard dependency, matching every prior delta's own PREREQUISITE precedent.
--
-- ADR-0000 2(a) -- THE TYPE THAT FORECLOSES THE CLASS: "a ledger row's evidentiary force relies
-- on bytes the database does not itself hold" is the class; the type that forecloses it is
-- content-addressed custody INSIDE the same database the ledger already lives in -- a hash a
-- ledger row cites now resolves, in-db, to the exact bytes that hash names, backed up by the
-- SAME pg_dump that backs up the ledger (WA7 witnesses this claim, not asserts it). The
-- essential-records/product-artifacts MECE cut (spec amendment) is the closure statement's own
-- quantification universe, restated in this delta's CLOSURE STATEMENT below.
--
-- HISTORY: safe -- per-mechanism grounds, mirroring s43's own HISTORY paragraph exactly (this
-- delta is architecturally the same shape: a new object family plus one closed-vocabulary
-- widening, no restructure of any existing write path):
--   * kernel.artifact is a WHOLLY NEW TABLE -- no pre-existing reader, no pre-existing writer.
--   * kernel.artifact_write is a WHOLLY NEW FUNCTION -- no pre-existing caller.
--   * refusal_surface_check widened by ONE member ('artifact') -- additive, and every existing
--     write_refused row's refusal_surface value (ledger/review/registration/obligation) remains
--     valid under the widened CHECK unchanged (the widening only ADDS a permitted value, exactly
--     s43's own kind-vocabulary-widening precedent, itself safe under the SAME reasoning s43's
--     header already gives for widening ledger_kind_check).
--   * NO ledger column is added, altered, or reinterpreted. compute_row_hash, ledger_current,
--     countersigned_in_force: untouched, byte-identical to their s43-and-later shipped text.
--     NO gates/hash_coverage_gate.py re-issue is owed (zero ledger columns touched -- s42's law
--     applies to ledger row-hash coverage; kernel.artifact is a DIFFERENT table with no row-hash
--     chain of its own, named rather than silently assumed covered).
--   * NO existing grant is narrowed except the belt-and-braces REVOKE this delta issues on ITS
--     OWN new table (kernel.artifact) -- nothing that succeeded on any OTHER object before this
--     delta succeeds differently after it.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form):
--   - INVARIANT: every artifact ever accepted by kernel.artifact_write is retrievable, in-db, by
--     its own sha256 hash, byte-identical to what was submitted (server-computed, never
--     caller-trusted); every artifact_write REFUSAL is a committed, digest-only write_refused
--     ledger row (the bytes never enter that record); no granted role holds UPDATE/DELETE/raw
--     INSERT on kernel.artifact -- the only write path is the verdict-returning function, and
--     the only mutation path period is append (new rows), never edit or removal.
--   - QUANTIFICATION UNIVERSE (explicitly enumerated, per the amendment's own discipline):
--       AXES: size (0 .. 1 MiB, CHECKed both by the function's explicit refusal and the table's
--         own size=octet_length(bytes) CHECK -- denominated in the SAME resource, bytes, at both
--         sites, never a proxy count); media type (closed four-member v1 vocabulary, CHECKed at
--         both the function's explicit refusal and the table's CHECK -- unknown types refused,
--         never coerced into the nearest known type); hash (server-computed always; a
--         caller-asserted hash is VERIFIED, never trusted, and a mismatch refuses); identity
--         (content-addressed PK -- re-submission of identical bytes is idempotent, never a
--         duplicate row or an error); actor (the same s40/s43 registered-principal + standing
--         discipline as every other kernel write -- an unattributable or revoked/suspended actor
--         refuses).
--       SIBLING SURFACES: the four s43 boundary functions (ledger/review/registration/
--         obligation) are UNCHANGED -- this delta adds a fifth, it does not touch their bodies,
--         their grants, or their refusal handling. The refusal JOURNAL itself (write_refused
--         kind, the six refusal_* columns, journal_write_refusal) is the SAME single home,
--         extended by exactly one refusal_surface vocabulary member -- no second journaling
--         mechanism, no parallel refusal record for artifacts.
--       NOT COVERED, NAMED: UPDATE/DELETE by the schema OWNER (superuser/owner-side DML) is
--         NOT foreclosed by this delta -- the standing s26..s50 trust bound (matching s43's own
--         "owner/superuser direct DML -- named not covered"); WA6's corruption drill exercises
--         exactly this named gap deliberately, as the owner, to prove `get`'s OWN hash
--         verification is the actual backstop against a corrupted stored row, not a claim that
--         the owner is architecturally prevented from writing. Existence-checking an s48
--         witness-ref's `Artifact` arm against this store at WRITE time is explicitly NOT this
--         delta (spec section 4: "a separate, later delta", named as the anticipated successor).
--         Route-table exposure (/artifacts/{hash}) is explicitly NOT this delta (spec section 5).
--   - DENOMINATION: the size bound is bytes, the resource that actually detonates (a bytea
--     column, an HTTP-adjacent transport eventually) -- never a character count or a base64
--     length (base64 inflates by ~4/3; the 1 MiB bound is checked against the DECODED byte
--     length, octet_length(v_bytes), never the base64 text's own strlen). The hash is the same
--     SHA-256 currency the ledger's own row-hash chain and s43's refusal-payload digest already
--     use -- one hash algorithm, one hex-lowercase rendering, project-wide.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT CLASS-RATIFIED
-- FAIL-SAFE, stated plainly (spec's own header): this delta adds a WRITE PATH (a fifth SECURITY
-- DEFINER function beside s43's four) -- it is not a pure refusal/vocabulary/view addition, so
-- it does not qualify for the 2026-07-09 class-ratified-fail-safe track even though its
-- DIRECTION is fail-safe (append-only, content-addressed, closed vocabulary, hard size cap). It
-- ships under the spec's own ratification (maintainer, decision queue, 2026-07-18) -- the BUILD
-- DISPATCH and the birth-chain entry each remain the maintainer's separate act, per the standing
-- contract and per runs-are-strictly-linear (this file is authored and scratch-witnessed only;
-- it is never applied to any existing world by this authoring act).
--
-- LIMITS (pre-registered):
--   - The superuser/schema-owner bound stands; owner-side direct DML on kernel.artifact is named
--     not covered (HISTORY/CLOSURE above), exactly the s26..s50 standing trust bound.
--   - v1 media-type vocabulary is markdown/plain/toml/json ONLY -- no binaries, per the
--     essential-records criterion (governance REGISTERS, not arbitrary blobs). Widening it is a
--     future amendment that must argue the essential-records test, not convenience (spec's own
--     words).
--   - The 1 MiB cap is a stated, deliberate constant (see MECHANISM item 2 above for the sizing
--     rationale) -- raising it needs a stated need, never a silent bump.
--   - registered_by resolution mirrors set_actor's session_user-based standing lookup exactly
--     (s43 Element 8's own named limit applies identically here: one principal per login role
--     via SET ROLE loses implicit per-role attribution; the explicit actor channel is the
--     correct tool there).
--   - No ledger row is written by an ACCEPTED artifact_write call -- the artifact row itself,
--     with its own registered_at/registered_by columns, IS the record of the write; a REFUSED
--     call still journals a write_refused ledger row exactly like the other four boundary
--     functions (s43's uniform refusal-journaling invariant extends here, unbroken).
--   - Boundary (HTTP-served) exposure is explicitly out of scope (MECHANISM item 5) --
--     UNEXERCISED by any served route; ./legacy/led and any direct-psql caller are the only
--     live paths this delta wires.
--   - Live operation awaits an s43+ world entering a scaffold's LINEAGE_CHAIN (the maintainer's
--     own act, per runs-are-strictly-linear) -- UNEXERCISED live, scratch-witnessed only, exactly
--     as every sNN delta stands at this same build time.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s43/../s50):
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s51val -v kern=s51val_kernel -v role=s51val_rw \
--        -f high_watermark_1.sql -f s20-obligation-grants-and-view-refresh.sql \
--        ... (s21..s42 as in s43's own VALIDATE list) ... \
--        -f s42-row-hash-full-coverage.sql -f s43-typed-verdict-write-boundary.sql \
--        -f s51-artifact-store.sql
--     (genesis seed per s26; register the write-boundary principal, and at least one standing
--     actor principal, before exercising any artifact_write path -- the write boundary's
--     journaler aborts loudly by design otherwise, exactly s43's own VALIDATE note.)
--   REAL: NEVER applied to any existing world by this authoring act. Enters a FUTURE world's
--   birth chain via bootstrap/new-project.sh's LINEAGE_CHAIN, ONLY as the maintainer's own act
--   (runs-are-strictly-linear, 2026-07-11) -- NOT wired by this commit. Authored and
--   scratch-witnessed on scratch schema pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (CREATE TABLE IF NOT EXISTS; DROP+ADD CONSTRAINT;
-- CREATE OR REPLACE FUNCTION; DROP+CREATE TRIGGER; REVOKE/GRANT are idempotent).
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
-- ELEMENT 1 -- kernel.artifact: content-addressed, append-only.
-- ============================================================================================
CREATE TABLE IF NOT EXISTS :"kern".artifact (
    hash          text PRIMARY KEY,
    bytes         bytea NOT NULL,
    size          bigint NOT NULL,
    media_type    text NOT NULL,
    registered_at timestamptz NOT NULL DEFAULT now(),
    registered_by bigint REFERENCES :"kern".principal(id)
);

ALTER TABLE :"kern".artifact DROP CONSTRAINT IF EXISTS artifact_hash_shape;
ALTER TABLE :"kern".artifact ADD CONSTRAINT artifact_hash_shape CHECK (
    hash ~ '^[0-9a-f]{64}$');
ALTER TABLE :"kern".artifact DROP CONSTRAINT IF EXISTS artifact_size_matches_bytes;
ALTER TABLE :"kern".artifact ADD CONSTRAINT artifact_size_matches_bytes CHECK (
    size = octet_length(bytes));
ALTER TABLE :"kern".artifact DROP CONSTRAINT IF EXISTS artifact_size_within_cap;
ALTER TABLE :"kern".artifact ADD CONSTRAINT artifact_size_within_cap CHECK (
    size <= 1048576);
ALTER TABLE :"kern".artifact DROP CONSTRAINT IF EXISTS artifact_media_type_check;
ALTER TABLE :"kern".artifact ADD CONSTRAINT artifact_media_type_check CHECK (
    media_type IN ('text/markdown', 'text/plain', 'application/toml', 'application/json'));

COMMENT ON TABLE :"kern".artifact IS
  'kernel/lineage/s51-artifact-store.sql, design/FABLE-ARTIFACT-STORE-SPEC.md: content-addressed,
   append-only custody for ESSENTIAL RECORDS (the spec''s own delineation -- charters, commission
   texts, ratified specs, attestation bodies, witness transcripts a ledger row cites by hash;
   NEVER the governed project''s own product artifacts, whose custody stays git/build-systems).
   The ONLY write path is kernel.artifact_write (SECURITY DEFINER) -- no granted role holds
   INSERT/UPDATE/DELETE; UPDATE/DELETE are additionally refused at the trigger level
   (refuse_artifact_mutation). hash is server-computed SHA-256 hex, always -- a caller-asserted
   hash is verified, never trusted (assert-and-verify). size is CHECKed equal to
   octet_length(bytes) (never a writer-supplied, possibly-lying value) and capped at 1048576
   bytes (1 MiB v1, a deliberate constant -- see this file''s own header for the sizing
   rationale). media_type is a closed v1 vocabulary (markdown/plain/toml/json -- governance
   registers, no binaries).';
COMMENT ON COLUMN :"kern".artifact.hash IS
  'SHA-256 (hex, lowercase) of bytes, computed SERVER-SIDE inside kernel.artifact_write -- never
   caller-supplied as the row''s own identity (a caller MAY assert a hash in the write payload;
   it is verified against the server''s own computation and the write refuses on mismatch,
   assert-and-verify, never trust-on-assert). kernel/lineage/s51-artifact-store.sql.';
COMMENT ON COLUMN :"kern".artifact.size IS
  'Bytes, CHECKed equal to octet_length(bytes) (artifact_size_matches_bytes) and CHECKed
   <= 1048576 (artifact_size_within_cap, the 1 MiB v1 cap -- this file''s header states the
   sizing rationale and the amendment discipline for raising it).
   kernel/lineage/s51-artifact-store.sql.';
COMMENT ON COLUMN :"kern".artifact.registered_by IS
  'The principal that registered this artifact, resolved by the SAME s40/s43 attribution
   discipline as every other kernel write (explicit payload actor when it resolves to a
   registered id; else the session''s own standing-declaration default; a revoked/suspended
   actor refuses the write). kernel/lineage/s51-artifact-store.sql.';

-- Append-only enforcement, TWO mechanisms (spec: "UPDATE/DELETE refused at trigger + grant
-- level"), mirroring s43's own R6 two-mechanism posture (a grant-level narrowing plus a trigger
-- that fires regardless of which role issues the DML, defense in depth against a future grant
-- regression):
CREATE OR REPLACE FUNCTION :"kern".refuse_artifact_mutation() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"kern", pg_temp AS $fn$
BEGIN
  RAISE EXCEPTION 'kernel.artifact policy: artifacts are APPEND-ONLY (kernel/lineage/s51-artifact-store.sql) -- % on kernel.artifact is refused unconditionally. A stored artifact is an essential record (design/FABLE-ARTIFACT-STORE-SPEC.md''s amendment): if the bytes were wrong, the correct bytes are registered fresh (a new row, its own hash) beside the old one -- the old row stands as a historical fact, exactly the write_refused unretractability posture s43 already established for the refusal journal.', TG_OP;
END; $fn$;
DROP TRIGGER IF EXISTS refuse_artifact_update ON :"kern".artifact;
CREATE TRIGGER refuse_artifact_update BEFORE UPDATE ON :"kern".artifact
    FOR EACH ROW EXECUTE FUNCTION :"kern".refuse_artifact_mutation();
DROP TRIGGER IF EXISTS refuse_artifact_delete ON :"kern".artifact;
CREATE TRIGGER refuse_artifact_delete BEFORE DELETE ON :"kern".artifact
    FOR EACH ROW EXECUTE FUNCTION :"kern".refuse_artifact_mutation();

REVOKE ALL ON :"kern".artifact FROM PUBLIC;
REVOKE INSERT, UPDATE, DELETE ON :"kern".artifact FROM :"role";
GRANT SELECT ON :"kern".artifact TO :"role";

-- ============================================================================================
-- ELEMENT 2 -- refusal_surface_check WIDENED by one member ('artifact'), the SAME pattern s43's
-- own ledger_kind_check widening uses: a closed CHECK gains a value, every pre-existing row's
-- value stays valid, nothing existing is relaxed.
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_surface_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_surface_check CHECK (
    refusal_surface IS NULL
    OR refusal_surface IN ('ledger', 'review', 'registration', 'obligation', 'artifact'));

COMMENT ON CONSTRAINT refusal_surface_check ON :"schema".ledger IS
  'kernel/lineage/s51-artifact-store.sql widens s43''s four-member closed vocabulary by
   ''artifact'' -- the fifth SECURITY DEFINER boundary function''s own surface name, journaled by
   the SAME kernel.journal_write_refusal (s43 Element 4) every other surface already uses. Pure
   value-vocabulary addition: every pre-s51 write_refused row''s refusal_surface value remains
   valid under this widened CHECK unchanged.';

-- ============================================================================================
-- ELEMENT 3 -- kernel.artifact_write(jsonb): the FIFTH SECURITY DEFINER boundary function.
-- Reuses kernel.write_verdict (s43's TYPE, unchanged) and kernel.journal_write_refusal (s43's
-- ONE journaler, unchanged) -- no new type, no second journaling mechanism.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"kern".artifact_write(p_payload jsonb)
    RETURNS :"kern".write_verdict LANGUAGE plpgsql SECURITY DEFINER
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  k text;
  v_bytes bytea;
  v_hash text;
  v_asserted_hash text;
  v_media text;
  v_size bigint;
  v_actor bigint;
  v_standing text;
  v_existing_hash text;
  v_state text; v_msg text; v_refusal bigint;
BEGIN
  BEGIN
    -- payload validation (mirrors s43 §4.2's own discipline exactly): every key a member of
    -- THIS ceremony's own closed contract; nothing else is silently ignored.
    FOR k IN SELECT jsonb_object_keys(p_payload) LOOP
      IF k NOT IN ('bytes', 'media_type', 'hash', 'actor') THEN
        RAISE EXCEPTION 'write boundary: artifact payload key ''%'' is not a member of the artifact-registration ceremony''s contract (bytes, media_type, hash, actor -- kernel/lineage/s51-artifact-store.sql).', k;
      END IF;
    END LOOP;
    IF NOT (p_payload ? 'bytes') THEN
      RAISE EXCEPTION 'write boundary: artifact payload is missing required key ''bytes'' (base64-encoded content -- kernel/lineage/s51-artifact-store.sql).';
    END IF;
    IF NOT (p_payload ? 'media_type') THEN
      RAISE EXCEPTION 'write boundary: artifact payload is missing required key ''media_type'' (kernel/lineage/s51-artifact-store.sql).';
    END IF;
    v_media := p_payload->>'media_type';
    IF v_media NOT IN ('text/markdown', 'text/plain', 'application/toml', 'application/json') THEN
      RAISE EXCEPTION 'write boundary: artifact media_type ''%'' is not a member of the v1 closed vocabulary (text/markdown, text/plain, application/toml, application/json -- design/FABLE-ARTIFACT-STORE-SPEC.md''s essential-records amendment: governance registers, no binaries; widening this vocabulary is a future amendment that must argue the essential-records test).', v_media;
    END IF;
    -- decode() on malformed base64 raises a 22*-class data exception -- caught and journaled
    -- like any other data exception, no special-casing needed.
    v_bytes := decode(p_payload->>'bytes', 'base64');
    v_size := octet_length(v_bytes);
    IF v_size > 1048576 THEN
      RAISE EXCEPTION 'write boundary: artifact_too_large -- % bytes exceeds the 1048576-byte (1 MiB) v1 cap (kernel/lineage/s51-artifact-store.sql: a deliberate constant -- charters/TOMLs/specs are KB-scale; raising the cap is an amendment with a stated need, never a silent bump). Nothing was stored.', v_size;
    END IF;
    v_hash := encode(sha256(v_bytes), 'hex');
    -- assert-and-verify (ADR-0012 P2/P8): a caller MAY name a hash; the server''s own
    -- computation governs, and a mismatch refuses -- the caller may not name a hash the server
    -- did not compute.
    IF p_payload ? 'hash' THEN
      v_asserted_hash := p_payload->>'hash';
      IF v_asserted_hash <> v_hash THEN
        RAISE EXCEPTION 'write boundary: artifact hash mismatch -- asserted % but the server computed % from the submitted bytes (kernel/lineage/s51-artifact-store.sql: assert-and-verify, the server''s own computation governs; a caller may not name a hash it did not compute). Nothing was stored.', v_asserted_hash, v_hash;
      END IF;
    END IF;
    -- content-addressed idempotency: identical bytes re-registered is a no-op that returns the
    -- EXISTING hash, never an error, never a duplicate row.
    SELECT hash INTO v_existing_hash FROM artifact WHERE hash = v_hash;
    IF v_existing_hash IS NOT NULL THEN
      SET CONSTRAINTS ALL IMMEDIATE;
      RETURN ('accepted', NULL, NULL, NULL, format('artifact already present: %s', v_hash))::write_verdict;
    END IF;
    -- actor resolution: explicit payload actor when it resolves to a registered id, else the
    -- session''s own standing-declaration default -- the SAME s40/s43 discipline set_actor
    -- applies to every ledger write, inlined here because kernel.artifact carries no ledger
    -- trigger of its own.
    IF (p_payload ? 'actor') THEN
      v_actor := (p_payload->>'actor')::bigint;
    ELSE
      SELECT principal_id INTO v_actor FROM principal_role WHERE db_role = session_user;
    END IF;
    IF v_actor IS NULL THEN
      RAISE EXCEPTION 'write boundary: artifact registration supplied no actor and login role ''%'' has no standing declaration, so the kernel cannot attribute it (kernel/lineage/s51-artifact-store.sql, the s40 strict-attribution discipline extended here). Declare this role''s standing principal once: ./led principal declare-standing <principal-name> --db-role %, or supply an explicit actor in the payload.', session_user, session_user;
    END IF;
    v_standing := principal_standing(v_actor);
    IF v_standing IN ('revoked', 'suspended') THEN
      RAISE EXCEPTION 'write boundary: artifact registration actor % is % (kernel/lineage/s51-artifact-store.sql, the s40 strict-attribution discipline extended here) -- a % principal accepts no further writes.', v_actor, v_standing, v_standing;
    END IF;
    INSERT INTO artifact (hash, bytes, size, media_type, registered_by)
    VALUES (v_hash, v_bytes, v_size, v_media, v_actor);
    SET CONSTRAINTS ALL IMMEDIATE;
    RETURN ('accepted', NULL, NULL, NULL, format('artifact registered: %s', v_hash))::write_verdict;
  EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS v_state = RETURNED_SQLSTATE, v_msg = MESSAGE_TEXT;
    IF v_state LIKE '22%' OR v_state LIKE '23%' OR v_state LIKE 'P0%' THEN
      -- journal_write_refusal (s43 Element 4, UNCHANGED) digests p_payload::text ONLY -- the
      -- base64 bytes travel inside p_payload but are NEVER stored verbatim by this call, by
      -- construction (the journaler has never had a column to put them in). R4's "digest, never
      -- verbatim" is inherited here unmodified.
      v_refusal := journal_write_refusal('artifact', p_payload, v_state, v_msg);
      RETURN ('refused', NULL, v_refusal, v_state, v_msg)::write_verdict;
    END IF;
    RAISE;   -- infrastructure classes (40/53/57/XX/...): not a denied attempt -- re-raised.
  END;
END; $fn$;
REVOKE ALL ON FUNCTION :"kern".artifact_write(jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION :"kern".artifact_write(jsonb) TO :"role";

COMMENT ON FUNCTION :"kern".artifact_write(jsonb) IS
  'The FIFTH SECURITY DEFINER write boundary (design/FABLE-ARTIFACT-STORE-SPEC.md), beside
   s43''s four (kernel/lineage/s43-typed-verdict-write-boundary.sql): payload keys bytes
   (base64), media_type (closed v1 vocabulary), optional hash (assert-and-verify) and actor.
   Server-computes the hash always; content-addressed idempotency on re-registration; a
   1048576-byte (1 MiB) size cap as a typed refusal; a refusal is journaled through s43''s own
   journal_write_refusal (digest-only -- bytes never enter the refusal record) and returned as a
   typed verdict, never an abort. On accept, message carries "artifact registered: <hash>" or
   "artifact already present: <hash>" (a DISCLOSED, per-function divergence from the other four
   functions'' "message NULL on accept" convention -- kernel.artifact''s PK is a hash, not a
   bigint id, so row_id cannot carry the result the way it does for ledger_write/
   review_write/registration_write; message is the kernel-authored-prose channel write_verdict
   already provides, repurposed here on accept exactly as documented). row_id is always NULL
   (mirrors obligation_write''s own precedent -- the table has no bigint id).
   kernel/lineage/s51-artifact-store.sql.';
