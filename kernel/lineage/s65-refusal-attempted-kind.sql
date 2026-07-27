-- s65 REFUSAL JOURNAL RECORDS THE ATTEMPTED KIND (design/FABLE-S65-REFUSAL-ATTEMPTED-KIND-SPEC.md,
-- RATIFIED 2026-07-27, ledger row 1487 -- "Yes, let's have that column" -- verbatim, build
-- dispatched the same day). Basis: ledger rows 1474/1476 (two unattributed refusal probes) and
-- 1483 (the post-mortem: knowing the attempted KIND would have made the cause obvious in
-- seconds -- a three-agent interrogation to answer a one-word question). Sonnet-built per the
-- standing delegation contract, from the ratified spec.
--
-- PREREQUISITE: this delta REQUIRES s64 (kernel/lineage/s64-principal-stamps-delegation-
-- conditions.sql) applied first -- it re-issues compute_row_hash/ledger_current/
-- countersigned_in_force in the EXACT 97-column shape s64 left them (no delta between s64 and
-- this one touches those three objects) and journal_write_refusal in the EXACT shape s49 left
-- it (no delta between s49 and this one re-issues that function -- verified by grep across
-- every tracked kernel/lineage/sNN-*.sql file, see this delta's own §4 caller enumeration in
-- the build report). THE HEAD-BODY RULE (s45's own standing instruction, carried here
-- verbatim): at this delta's authoring the lineage head is s64 (kernel/lineage/'s own directory
-- listing, confirmed by the builder before authoring). The --new-world scaffold path derives
-- its own apply list LIVE from a kernel/lineage/*.sql glob (bootstrap/new-project.sh's own
-- documented "LINEAGE HEAD, derived live... never hand-typed" mechanism), so this file is
-- picked up there automatically the moment it exists in a tree --new-world scaffolds from.
--
-- WHY (the spec's own words, §1 basis): the s43 refusal journal deliberately journals the
-- refused PAYLOAD as a digest only (R4, ratified privacy discipline) -- that discipline is
-- UNCHANGED here. But the payload's `kind` key -- the single, low-sensitivity vocabulary token
-- naming WHAT KIND OF ROW the caller was attempting to write -- was, before this delta, thrown
-- away entirely: a write_refused row told you WHO attempted, WHAT SURFACE caught it, and WHAT
-- SQLSTATE fired, but never WHAT THE CALLER WAS TRYING TO WRITE. Rows 1474/1476's own
-- unattributed refusal probes forced a three-agent interrogation to reconstruct that one word
-- from surrounding evidence -- the maintainer's own ratifying words name the fix precisely
-- ("Yes, let's have that column").
--
-- MECHANISM (spec §1, three items):
--   1. ONE new nullable column, refusal_attempted_kind text, kind-scoped to write_refused rows
--      by the SAME one-way kind-shape CHECK idiom refusal_attempted_actor already uses (s43
--      Element 2): a non-write_refused row carrying it is refused; a write_refused row may
--      carry it OR NULL -- NULL means "not extractable" (no kind key, a non-text kind, or any
--      other malformed shape), NEVER "not attempted". This is deliberately NOT a two-way
--      (mandatory-on-the-kind) CHECK like refusal_sqlstate/refusal_message/refusal_surface/
--      refusal_payload_digest/refusal_attempted_role -- exactly because a caller-supplied
--      payload's `kind` key is, unlike those five, not ALWAYS extractable (the payload might
--      carry no `kind` key at all, e.g. a review/registration/obligation-surface payload whose
--      contract has no `kind` field, or a `ledger`-surface payload whose `kind` value is
--      malformed) -- the SAME "legitimately NULL" shape s43's own header already argues for
--      refusal_attempted_actor, applied here to a different column for a structurally similar
--      reason (an attempt this kernel could not fully characterize before refusing it).
--   2. kernel.journal_write_refusal RE-ISSUED (this delta's ONE function edit) to extract the
--      `kind` key from the refused jsonb payload BEFORE digesting, and record it in the new
--      column. Extraction is TOTAL in the s49 precedent's sense (a payload with no `kind` key,
--      a non-text kind, or any other shape journals with refusal_attempted_kind NULL and NEVER
--      aborts the refusal recording -- more refusals recorded, never fewer) -- but UNLIKE s49's
--      own guarded cast, this extraction needs NO exception handler to achieve totality: the
--      jsonb `->` operator already returns NULL (never raises) when its left operand is not a
--      JSON object with the named key, or when the key's value is JSON null, regardless of the
--      payload's own top-level shape (object/array/scalar/null) -- Postgres's own documented
--      jsonb-operator semantics, not an assumption this delta introduces. So the one honest
--      question left is "is the found value TEXT" (a non-text `kind`, e.g. a JSON number/
--      object/array/boolean, must also yield NULL per the spec's own four-axis enumeration) --
--      answered by `jsonb_typeof(...) = 'string'` before the ->>text extraction, itself total
--      for the same reason (jsonb_typeof never raises on any valid jsonb value, and a jsonb
--      parameter is by definition already a valid jsonb value by the time PL/pgSQL runs the
--      function body -- a syntactically malformed JSON literal never reaches this function AS
--      jsonb at all; it fails at the earlier cast/parse boundary, which is not this function's
--      surface). LENGTH BOUND (amendment 2026-07-27, spec §5): a found text value longer than
--      256 bytes ALSO yields NULL, checked by octet_length before extraction -- the refusal path
--      is precisely where a caller who is already being refused arrives, so an oversized/hostile
--      `kind` string must be assumed rather than ruled out (the first build's premise that a
--      long string would already have been refused by ledger_kind_check was FALSIFIED in review:
--      that CHECK guards ACCEPTED rows, never the refused payload this function journals). The
--      SAME 256-byte bound is carried table-level (refusal_attempted_kind_length CHECK below),
--      so the invariant holds independent of this function's own care. The digest computation
--      (encode(sha256(convert_to(p_payload::text,'utf8')), 'hex')) is BYTE-IDENTICAL to s49's
--      own -- the new column is additional, never a substitute, and reads no smaller a slice of
--      the payload than before (the length bound narrows only what is STORED in the new column,
--      never what is digested).
--   3. compute_row_hash RE-ISSUED (s42's law, self-applied) to cover the new column -- 98
--      columns, the one new column appended in catalog ordinal order, before the predecessor
--      link, every other rendering byte-identical to s64's own 97-column body.
--
-- THE ASP TWIN: NO CHANGE to any derivation. Journal columns are EDB facts like any other
-- ledger column (ADR-0012 P7); grepped, at this delta's own authoring time, across the whole
-- engine/ tree for every one of s43's existing six refusal_* column names
-- (refusal_sqlstate/refusal_message/refusal_surface/refusal_payload_digest/
-- refusal_attempted_actor/refusal_attempted_role) -- ZERO hits in engine/ledger_edb.py or any
-- engine/lp/*.lp file. No exporter emits ANY refusal column today, so none is widened to emit
-- this delta's new one either -- per the s63 finding this spec's own §1 item 4 cites verbatim,
-- the SQL/ASP differential is STRUCTURALLY BLIND to write-boundary refusal behavior (a refused
-- write never becomes a ledger row the exporter's normal EDB-building queries would even
-- consider under most existing WHERE-kind-IN(...) shapes, and no existing shape names
-- 'write_refused' at all) -- the coverage for THIS delta is its own fixtures (seen-red/
-- s65-refusal-attempted-kind/), never the differential, exactly as stated rather than silently
-- assumed.
--
-- PRIVACY CONSIDERATION (spec §1 basis, NOT delegated to the class-ratification routing): the
-- journal now reveals one more token per refusal -- the one axis on which "additive" could be
-- doubted, since s43's own R4 discipline exists precisely to keep refused CONTENT out of the
-- permanent record. The maintainer ratified THIS SPECIFIC revelation in his own words (row
-- 1487); `kind` is a closed, low-sensitivity vocabulary token (twenty-four members as of s43,
-- widened by later deltas -- never free text the caller could smuggle payload content through:
-- the column carries exactly the STRING the caller supplied at the `kind` key, verbatim up to
-- 256 bytes (amendment 2026-07-27, spec §5), but that string's LEGITIMATE domain is a short
-- kernel-defined vocabulary; ledger_kind_check only guards ACCEPTED rows, so a caller supplying
-- a long/adversarial string at the refused path is NOT refused before reaching this extraction
-- (the first build's premise to the contrary was falsified in review, witnessed storing a 2 MiB
-- string verbatim) -- the 256-byte bound below is what now keeps that case from ever reaching
-- storage, journaling NULL instead, strictly fewer bytes revealed than the ratified reading. A
-- write_refused row's own refusal_attempted_kind can therefore carry an arbitrary caller-chosen
-- string UP TO THE BOUND when the refusal's OWN cause is an invalid kind value, which is
-- precisely the rows-1474/1476 incident shape this delta exists to make legible, not a new
-- privacy leak beyond what the refusal's own SQLSTATE/message already disclose).
--
-- CLASS ROUTING (spec §2, resolved, no residual routing question): fail-safe-additive by the
-- 2026-07-09 ruling read plainly -- one nullable column, one narrowing (one-way) CHECK, and
-- additional recording inside an EXISTING refusal path (journal_write_refusal, re-issued, never
-- a NEW write path or NEW kind); nothing existing is relaxed, no new act is permitted, refusal
-- behavior TOWARD CALLERS is byte-identical (the verdict returned is unchanged; only the
-- journaled ROW gains one more populated column). Per s43/s49's own precedent, a live function
-- re-issue is NOT self-certifying under the class-ratified path no matter how narrow the diff
-- (a CREATE OR REPLACE on an existing function body is not itself a letter-2(a) "only adds"
-- shape) -- so this delta ships under the spec's own explicit maintainer ratification (row
-- 1487), stated plainly below in FAIL-SAFE CLASSIFICATION, exactly the s49 precedent's own
-- honesty convention.
--
-- HISTORY: safe -- one nullable no-DEFAULT column whose one-way CHECK validates vacuously on
-- every pre-existing row (refusal_attempted_kind IS NULL is true for every row that predates
-- this delta, since the column did not exist to be non-NULL); journal_write_refusal and
-- compute_row_hash are re-issued function bodies only, no history-validating statement over
-- pre-existing rows (true of any deployment this delta reaches, not merely a fresh scaffold);
-- ledger_current/countersigned_in_force are pure column-list appends (the s20 lesson).
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form; spec §4's own text, elaborated):
--   - INVARIANT: every write_refused row journaled through kernel.journal_write_refusal now
--     carries, IN ADDITION to its s43/s49 columns, the attempted `kind` token whenever the
--     refused payload's own `kind` key held a JSON string value -- extraction is TOTAL (never
--     aborts the refusal recording on any payload shape) and NULL is reserved exclusively for
--     "not extractable", never conflated with "not attempted" (a write_refused row's mere
--     existence already proves an attempt happened; this column only narrows WHAT was
--     attempted, when knowable).
--   - QUANTIFICATION UNIVERSE (per ADR-0000 Rule 2(a): the write surfaces that journal refusals
--     are EXACTLY the SECURITY DEFINER boundary functions calling journal_write_refusal --
--     enumerated by grep across every kernel/lineage/sNN-*.sql file in this delta's own build
--     report, current count SEVEN as of this lineage's head: kernel.ledger_write,
--     kernel.review_write, kernel.registration_write, kernel.obligation_write (all four born
--     s43; ledger_write itself later RE-ISSUED at s58 to widen its payload-key allowlist for
--     missive columns -- same function, same surface name 'ledger', not a new caller),
--     kernel.artifact_write (s51, surface 'artifact'), kernel.obligation_revoke (s57, surface
--     'obligation_revoke'), kernel.missive_dispose (s58, surface 'missive_dispose' -- that
--     file's own header names it "the SEVENTH SECURITY DEFINER boundary function") -- every
--     caller inherits the enrichment through the ONE shared journaler (ADR-0012 P1, "one home"),
--     which is the single home; no per-surface edit exists to forget, and none is needed here.
--     Of these SEVEN, only `ledger_write`'s own payload contract admits a `kind` key at all
--     (review_write/registration_write/obligation_write/artifact_write/obligation_revoke/
--     missive_dispose's own payload contracts, s43/s51/s57/s58's own explicit key allowlists,
--     never include a `kind` key -- their kind is always structurally implied by which function
--     was called, never caller-supplied) -- so refusal_attempted_kind populates ONLY on
--     surface='ledger' rows by construction, and is NULL on every other surface's write_refused
--     row, not because extraction failed but because those payloads never carried the key to
--     begin with (itself a "not extractable" case, consistent with this column's own NULL
--     semantics, named here rather than left as an unexplained asymmetry).
--     AXES (payload with valid kind / missing kind / non-text kind / malformed jsonb) -- all
--     four witnessed or refused-as-expected in this delta's own fixture (seen-red/
--     s65-refusal-attempted-kind/run_fixtures.py): valid text kind extracts verbatim (witnessed
--     with kind 'row', the rows-1474/1476 incident's own probable specimen); missing kind key
--     (a non-ledger-surface refusal, or a ledger-surface payload omitting the key) extracts
--     NULL; non-text kind (a JSON number/object/array/boolean at the `kind` key -- reachable
--     only via a raw boundary call bypassing normal caller conventions, since ledger_write's own
--     jsonb_populate_record cast would itself refuse a non-text kind value against the ledger
--     table's own `kind text` column type before this extraction ever runs on an ACCEPTED path,
--     but the REFUSED path's journaling still receives the raw, pre-cast payload) extracts
--     NULL; "malformed jsonb" -- the fourth axis the spec names -- cannot reach this function AS
--     a distinct case from the three above, because p_payload is a typed jsonb PARAMETER: any
--     JSON syntactically malformed at its own text-to-jsonb cast boundary fails BEFORE this
--     function is ever called (a class-22 data exception at the caller's own INPUT stage, caught
--     by the calling boundary function's own outer handler exactly like any other malformed
--     value), so within journal_write_refusal itself "malformed payload" collapses into
--     "missing/non-text kind" -- named explicitly here rather than silently assumed to be a
--     fourth mechanism.
--     KINDS/COLUMNS: write_refused licenses refusal_attempted_kind (one-way -- forbidden
--     elsewhere, optionally NULL on the kind itself); no other kind may carry it.
--     VIEWS: the two column-complete homes re-issued (+1); non-members untouched (none of
--     work_item_current, work_item_violations, work_violation_history, work_review_gap,
--     review_gap, question_status, review_stamp_distinctness, work_edge_*, work_startable,
--     work_bookkeeping_closes, standing_decisions, principal_standing_current,
--     principal_relations, principal_role_bindings, principal_keys, principal_competences,
--     model_attestations, model_defeated_rows, credited_current, belief_current,
--     contested_beliefs, credited_beliefs, corroboration, shared_premise,
--     reservations_outstanding, review_verdicts, missive_outbound, missive_receipts,
--     missive_undisposed, missive_stale, missive_delivery_audit, missive_open_threads does
--     general column passthrough that would need re-verification; none is re-issued).
--     ENGINE: unaffected -- no derivation reads any refusal_* column today (grep-verified, this
--     file's own ASP TWIN section above); coverage is this delta's own fixtures.
--     HASH CHAIN: compute_row_hash re-issued to 98 columns here, under s42's law, gate-witnessed
--     (gates/hash_coverage_gate.py, mechanically derived both sides -- no hand-maintained
--     manifest to fall stale).
--     GATES: hash-coverage (green on this head, red on a no-re-issue scratch injecting the new
--     column); kind-shape manifest (gates/kind_shape_manifest_gate.py's own MANIFEST list gains
--     one row, one-way arity, matching refusal_attempted_actor's own shape); fixture census
--     (this delta's own seen-red/ entry registered); kernel-function-census (bank updated in
--     this same commit -- schema:compute_row_hash's hash changes; kern:journal_write_refusal is
--     OUTSIDE gates/lineage_reissue_lineage.py's own `:"schema"`-anchored citation-check
--     universe, per that gate's own docstring, but its bank entry still updates here since the
--     census keys BOTH governed namespaces, schema AND kern); lineage-reissue-lineage (CHECK 1
--     citation + CHECK 2 prior-body-sha256, both satisfied for compute_row_hash against its true
--     immediately-prior re-issue, kernel/lineage/s64-principal-stamps-delegation-conditions.sql;
--     journal_write_refusal's AND ledger_write's own citation/hash lines (Elements 4 and 5,
--     added fix round 2 for the MINOR finding) are both carried in this file's own header/
--     Element-window text as a matter of this codebase's house idiom, even though that gate's
--     mechanical CREATE_FN_RE does not parse a `:"kern".`-qualified re-issue at all -- named
--     here rather than silently relied upon).
--   - DENOMINATION: the attempted kind in the SAME closed vocabulary ledger_kind_check already
--     enforces on every accepted row (no new vocabulary minted by this delta); "not extractable"
--     in NULL, never a sentinel string. AMENDMENT 2026-07-27 (spec §5): this delta DOES add one
--     numeric bound, 256 (bytes, octet_length), on the extracted/stored token -- not a bare round
--     literal chosen for roundness, but the same "generous multiple of any real vocabulary token"
--     reasoning as s51's 1048576-byte artifact_too_large cap, stated at the scale of a single
--     kind word rather than a KB-scale document; ledger_kind_check's own longest member is a
--     handful of bytes, so 256 is not a tight fit, it is a hostile-input backstop. Enforced BOTH
--     inside kernel.journal_write_refusal (belt) and as the table-level refusal_attempted_kind_
--     length CHECK (suspenders) -- see Element 1.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT CLASS-RATIFIED
-- FAIL-SAFE, stated plainly (s43/s49's own precedent for this same honesty requirement): this
-- delta re-issues an EXISTING function body via CREATE OR REPLACE (kernel.journal_write_refusal)
-- and another (compute_row_hash), which is not a letter-2(a) "only adds a refusal" shape even
-- though its EFFECT is strictly fail-safe (more information recorded per refusal, nothing newly
-- permitted, no existing verdict/behavior narrowed on any input). It ships under the
-- maintainer's OWN EXPLICIT RATIFICATION of this specific column and this specific revelation
-- (design/FABLE-S65-REFUSAL-ATTEMPTED-KIND-SPEC.md, ledger row 1487, "Yes, let's have that
-- column" -- verbatim), read per the 2026-07-11 vocabulary note, exactly the posture s43/s49
-- shipped under for the same reason -- a live function re-issue is not self-certifying under
-- the class-ratified path no matter how narrow the diff.
--
-- LIMITS (pre-registered, matching s43/s49's own disclosure convention):
--   - refusal_attempted_kind populates ONLY when the refused payload's own `kind` key held a
--     JSON string value AND the refusing surface's payload contract admits a `kind` key at all
--     (today: `ledger_write` only) -- named above (QUANTIFICATION UNIVERSE), not a defect, since
--     the other five surfaces' kind is always structurally implied by which function was
--     called, never ambiguous in the way this column exists to disambiguate.
--   - The column carries the caller's RAW string at the `kind` key verbatim, UP TO 256 BYTES
--     (amendment 2026-07-27) -- it is NOT validated against ledger_kind_check's own vocabulary
--     (a write_refused row's whole POINT is to record an attempt that may have failed EXACTLY
--     that validation); a reader must not assume every value in this column is a legal kind,
--     only that it is what the caller wrote at that key, when that string was 256 bytes or
--     fewer. A `kind` string LONGER than 256 bytes journals NULL, indistinguishable in this
--     column alone from any other "not extractable" case (no `kind` key, a non-text value) --
--     a reader who needs to know WHICH "not extractable" reason applied has no way to recover
--     that from this column alone; the refusal's own SQLSTATE/message may still disclose it.
--   - This delta does not change what happens when the JOURNAL INSERT itself fails (s43's own
--     named, disclosed limit, untouched here) or the attempted-actor cast's own s49 guard
--     (unchanged, unrelated code path in the same function).
--   - Every other named limit in s43/s49's own headers (session_user attribution's
--     one-principal-per-login-role assumption, the digest-only payload posture for the payload
--     AS A WHOLE, the superuser/schema-owner bound) is unchanged by this delta and not
--     re-stated in full here.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s64):
--   VALIDATE (reachable throwaway): apply the FULL s15..s64 chain (see kernel/lineage/
--   s64-principal-stamps-delegation-conditions.sql's own PREREQUISITE chain, itself s63's
--   VALIDATE block +1), THEN -f s65-refusal-attempted-kind.sql (genesis seed per s26; register
--   the write-boundary principal before exercising any refusal path, or the journaler aborts
--   loudly by design, unchanged since s43).
--   REAL: NEVER applied to any existing world by this authoring act (runs-are-strictly-linear,
--   2026-07-11). Enters a FUTURE world's birth chain via bootstrap/new-project.sh's
--   LINEAGE_CHAIN narrative (this same commit) and its GENERATED apply loop (which picks this
--   file up automatically from the kernel/lineage/ directory glob, no separate wiring act
--   needed for the apply side -- ledger rows 1392/1393/1399's own fix). Authored and
--   scratch-witnessed on scratch schema pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (ADD COLUMN IF NOT EXISTS; DROP+ADD CONSTRAINT;
-- CREATE OR REPLACE FUNCTION/VIEW).
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
-- ELEMENT 1 -- ONE NEW COLUMN + ITS ONE-WAY KIND-SHAPE CHECK (same idiom as s43's own
-- refusal_attempted_actor -- legitimately NULL on the kind it is licensed for, forbidden
-- elsewhere).
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS refusal_attempted_kind text;

COMMENT ON COLUMN :"schema".ledger.refusal_attempted_kind IS
  'The refused write''s ATTEMPTED `kind` token, extracted from the refused payload before it is
   digested (s43''s R4 digest-only discipline over the payload AS A WHOLE is unchanged) --
   legitimately NULL when the payload carried no `kind` key, a non-text `kind` value, a `kind`
   value longer than 256 bytes (amendment 2026-07-27: the refusal path is where hostile/oversized
   input arrives, so this is CHECKed table-level too, refusal_attempted_kind_length), or the
   refusing surface''s own payload contract never admits a `kind` key at all (review/
   registration/obligation/artifact/obligation_revoke -- their kind is structurally implied by
   which boundary function was called). NULL means "not extractable", NEVER "not attempted" --
   the row''s own existence already proves an attempt. kernel/lineage/
   s65-refusal-attempted-kind.sql.';

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_attempted_kind_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_attempted_kind_kind_shape CHECK (
    refusal_attempted_kind IS NULL OR kind = 'write_refused');

-- value CHECK (kind-free, non-empty when present -- the s43 refusal_attempted_role idiom,
-- extended to this column so an empty-string extraction can never masquerade as "some kind was
-- attempted" -- the jsonb ->>'kind' extraction below only ever produces a non-empty string or
-- NULL in practice, since ledger_kind_check itself refuses an empty kind on every accepted row
-- and a WRITE_REFUSED payload attempting an empty string still passes through this CHECK
-- unharmed either way, but the CHECK is stated explicitly rather than left an unstated
-- assumption):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_attempted_kind_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_attempted_kind_nonempty CHECK (
    refusal_attempted_kind IS NULL OR btrim(refusal_attempted_kind) <> '');

-- length CHECK (amendment 2026-07-27, spec §5 and §1 item 2): the refusal journal is exactly
-- where a caller who is ALREADY BEING REFUSED arrives -- adversarial payloads are expected here,
-- not the exception (the review that added this CHECK witnessed a 2 MiB string supplied as
-- `kind` stored VERBATIM before this bound existed). 256 bytes is the same "generous multiple of
-- any real vocabulary token" reasoning s51's artifact_too_large cap uses at a different scale
-- (1 MiB there, for KB-scale artifacts; 256 bytes here, for single-word kind tokens no legal
-- kind ever approaches -- ledger_kind_check's own longest member is a handful of bytes). The
-- bound is stated TABLE-LEVEL, not merely inside the extracting function, so the invariant holds
-- against ANY future writer of this column, not only kernel.journal_write_refusal as it exists
-- today (the s42-law self-application precedent: the table itself, not caller trust, carries
-- the guarantee). octet_length (bytes), matching s51's own denomination choice for the same
-- reason: a caller-supplied string's byte length, never its lying self-reported strlen.
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_attempted_kind_length;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_attempted_kind_length CHECK (
    refusal_attempted_kind IS NULL OR octet_length(refusal_attempted_kind) <= 256);

-- ============================================================================================
-- ELEMENT 2 -- s42'S LAW SELF-APPLIED: compute_row_hash RE-ISSUED TO 98 COLUMNS (the one new
-- column appended in serialization order, before the predecessor link; base body = s64's own
-- text, byte-identical above this delta's one appended line).
-- prior-body-sha256: e20b4a6b72ebe0d72e3026b77df67db7a16aab2bf6dc7b6dec5c3cb9e915cc9e (s64-principal-stamps-delegation-conditions.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".compute_row_hash(r :"schema".ledger, predecessor_hash text)
    RETURNS text LANGUAGE sql IMMUTABLE
    SET search_path = :"schema", pg_temp AS $fn$
  SELECT encode(sha256(convert_to(
    array_to_string(ARRAY[
      hashfield(r.id::text),
      hashfield(extract(epoch FROM r.ts)::text),
      hashfield(r.session),
      hashfield(r.kind),
      hashfield(r.statement),
      hashfield(r.rationale),
      hashfield(r.status),
      hashfield(r.evidence),
      hashfield(r.confidence),
      hashfield(r.supersedes::text),
      hashfield(r.refs),
      hashfield(r.concern),
      hashfield(array_to_string(r.enacts, ',')),
      hashfield(r.actor::text),
      hashfield(r.regards::text),
      hashfield(r.amends::text),
      hashfield(r.amends_scope),
      hashfield(r.answers::text),
      hashfield(r.stamp_session),
      hashfield(r.stamp_agent),
      hashfield(r.stamp_ts::text),
      hashfield(r.stamp_hmac),
      hashfield(r.stamp_verified::text),
      hashfield(r.work_slug),
      hashfield(r.work_title),
      hashfield(r.work_depends_on),
      hashfield(r.work_resolution),
      hashfield(r.work_witness),
      hashfield(r.stamp_invocation),
      hashfield(extract(epoch FROM r.event_declared_ts)::text),
      hashfield(r.work_parent),
      hashfield(r.work_review_disposition),
      hashfield(r.work_review_ref),
      hashfield(r.work_strict_close::text),
      hashfield(r.edge_type),
      hashfield(r.work_discharge),
      hashfield(r.decision_grade),
      hashfield(r.work_violation_class),
      hashfield(r.work_violation_target_id::text),
      hashfield(r.work_violation_witness::text),
      hashfield(r.principal_subject::text),
      hashfield(r.principal_purpose),
      hashfield(r.principal_db_role),
      hashfield(r.principal_actor_resolution),
      hashfield(r.principal_binding_active::text),
      hashfield(r.principal_object::text),
      hashfield(r.principal_relation),
      hashfield(r.principal_role_name),
      hashfield(r.principal_key_fingerprint),
      hashfield(r.principal_competence_activity),
      hashfield(r.principal_competence_band),
      hashfield(r.principal_competence_basis),
      hashfield(r.refusal_sqlstate),
      hashfield(r.refusal_message),
      hashfield(r.refusal_surface),
      hashfield(r.refusal_payload_digest),
      hashfield(r.refusal_attempted_actor::text),
      hashfield(r.refusal_attempted_role),
      hashfield(r.attest_row_id::text),
      hashfield(r.attest_model),
      hashfield(r.attest_grade),
      hashfield(r.attest_verdict),
      hashfield(r.attest_expected),
      hashfield(r.attest_session),
      hashfield(r.attest_basis),
      hashfield(r.belief_polarity),
      hashfield(r.belief_basis),
      hashfield(r.belief_universe),
      hashfield(r.belief_witness),
      hashfield(r.belief_source::text),
      hashfield(array_to_string(r.belief_premises, ',')),
      hashfield(r.belief_subject::text),
      hashfield(r.belief_contests::text),
      hashfield(r.belief_concurs::text),
      hashfield(r.obligation_revoked_scope),
      hashfield(r.obligation_revoke_reason),
      hashfield(r.missive_protocol::text),
      hashfield(r.missive_author_world),
      hashfield(r.missive_addressee_world),
      hashfield(r.missive_thread),
      hashfield(r.missive_seq::text),
      hashfield(r.missive_act),
      hashfield(r.missive_responds_to),
      hashfield(r.missive_provenance),
      hashfield(r.missive_cites),
      hashfield(r.missive_disposition),
      hashfield(r.missive_regards::text),
      hashfield(r.entitlement_act_class),
      hashfield(r.signature_attests_row::text),
      hashfield(r.signature_grade),
      hashfield(r.signature_symmetry_witness::text),
      hashfield(r.key_binding_possession_ref::text),
      hashfield(r.delegation_redelegate_depth::text),
      hashfield(r.delegation_must_countersign::text),
      hashfield(extract(epoch FROM r.delegation_expiry)::text),
      hashfield(array_to_string(r.delegation_scope_classes, ',')),
      hashfield(r.delegation_purpose),
      -- s65: the one new column, appended last before the predecessor link.
      hashfield(r.refusal_attempted_kind),
      hashfield(predecessor_hash)
    ], E'\x1f'),
  'utf8')), 'hex');
$fn$;

-- ============================================================================================
-- ELEMENT 3 -- THE TWO COLUMN-COMPLETE VIEWS, +1 APPENDED (the s20 lesson).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".ledger_current
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness,
       l.stamp_invocation, l.event_declared_ts, l.row_hash, l.work_parent,
       l.work_review_disposition, l.work_review_ref, l.work_strict_close, l.edge_type,
       l.work_discharge, l.decision_grade,
       l.work_violation_class, l.work_violation_target_id, l.work_violation_witness,
       l.principal_subject, l.principal_purpose, l.principal_db_role,
       l.principal_actor_resolution,
       l.principal_binding_active, l.principal_object, l.principal_relation,
       l.principal_role_name, l.principal_key_fingerprint,
       l.principal_competence_activity, l.principal_competence_band,
       l.principal_competence_basis,
       l.refusal_sqlstate, l.refusal_message, l.refusal_surface,
       l.refusal_payload_digest, l.refusal_attempted_actor, l.refusal_attempted_role,
       l.attest_row_id, l.attest_model, l.attest_grade, l.attest_verdict, l.attest_expected,
       l.attest_session, l.attest_basis,
       l.belief_polarity, l.belief_basis, l.belief_universe, l.belief_witness, l.belief_source,
       l.belief_premises, l.belief_subject, l.belief_contests, l.belief_concurs,
       l.obligation_revoked_scope, l.obligation_revoke_reason,
       l.missive_protocol, l.missive_author_world, l.missive_addressee_world, l.missive_thread,
       l.missive_seq, l.missive_act, l.missive_responds_to, l.missive_provenance,
       l.missive_cites, l.missive_disposition, l.missive_regards,
       l.entitlement_act_class,
       l.signature_attests_row, l.signature_grade, l.signature_symmetry_witness,
       l.key_binding_possession_ref,
       l.delegation_redelegate_depth, l.delegation_must_countersign, l.delegation_expiry,
       l.delegation_scope_classes, l.delegation_purpose,
       l.refusal_attempted_kind
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id);

CREATE OR REPLACE VIEW :"schema".countersigned_in_force
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness,
       l.stamp_invocation, l.event_declared_ts, l.row_hash, l.work_parent,
       l.work_review_disposition, l.work_review_ref, l.work_strict_close, l.edge_type,
       l.work_discharge, l.decision_grade,
       l.work_violation_class, l.work_violation_target_id, l.work_violation_witness,
       l.principal_subject, l.principal_purpose, l.principal_db_role,
       l.principal_actor_resolution,
       l.principal_binding_active, l.principal_object, l.principal_relation,
       l.principal_role_name, l.principal_key_fingerprint,
       l.principal_competence_activity, l.principal_competence_band,
       l.principal_competence_basis,
       l.refusal_sqlstate, l.refusal_message, l.refusal_surface,
       l.refusal_payload_digest, l.refusal_attempted_actor, l.refusal_attempted_role,
       l.attest_row_id, l.attest_model, l.attest_grade, l.attest_verdict, l.attest_expected,
       l.attest_session, l.attest_basis,
       l.belief_polarity, l.belief_basis, l.belief_universe, l.belief_witness, l.belief_source,
       l.belief_premises, l.belief_subject, l.belief_contests, l.belief_concurs,
       l.obligation_revoked_scope, l.obligation_revoke_reason,
       l.missive_protocol, l.missive_author_world, l.missive_addressee_world, l.missive_thread,
       l.missive_seq, l.missive_act, l.missive_responds_to, l.missive_provenance,
       l.missive_cites, l.missive_disposition, l.missive_regards,
       l.entitlement_act_class,
       l.signature_attests_row, l.signature_grade, l.signature_symmetry_witness,
       l.key_binding_possession_ref,
       l.delegation_redelegate_depth, l.delegation_must_countersign, l.delegation_expiry,
       l.delegation_scope_classes, l.delegation_purpose,
       l.refusal_attempted_kind
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- ELEMENT 4 -- kernel.journal_write_refusal RE-ISSUED: the s49 body (kernel/lineage/
-- s49-journaler-overflow-guard.sql), BYTE-IDENTICAL above and below the new extraction, with
-- ONE addition -- the attempted `kind` extraction (TOTAL, no exception handler needed -- see
-- this file's own header MECHANISM section for why jsonb `->`/`->>`/jsonb_typeof are already
-- total over every payload shape reaching this function) -- and the new column added to the
-- journal INSERT. No other line of this function changes: the oracle bump stays first, the
-- write-boundary principal lookup and its own loud abort stay exactly as s43/s49 left them, the
-- s49 attempted-actor guard is untouched, and the journal INSERT's own loud-abort-on-failure
-- semantics are untouched.
-- prior-body-sha256: 54cbbb1cc29729759d998ccf98e2e52b7be0fd3b8bf3d33ac7f5a903ed46ab21 (s49-journaler-overflow-guard.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"kern".journal_write_refusal(
    p_surface text, p_payload jsonb, p_sqlstate text, p_message text)
    RETURNS bigint LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_wb bigint;
  v_attempted bigint;
  v_attempted_kind text;
  v_id bigint;
BEGIN
  -- the oracle bump, BEFORE the journal INSERT (non-transactional, survives everything --
  -- s43 Element 5): if the INSERT below then fails, the sequence shows a counted gap the
  -- verify-chain reconciliation names. UNCHANGED by s65.
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
  -- (EXACTLY the shape of payload that reaches this function, since it arrives already
  -- refused) previously raised 22003 HERE, inside the one mechanism that exists to record a
  -- refusal, destroying the very record it was resolving an identity for. The cast is now
  -- total: numeric_value_out_of_range is caught locally and yields v_attempted := NULL -- the
  -- SAME value the fallback below already uses for "neither resolves." No other line of this
  -- function changes (UNCHANGED by s65).
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
  -- refused payload -- TOTAL over every payload shape (see this file's own header MECHANISM
  -- section: jsonb `->`/jsonb_typeof never raise, so no exception guard is needed here, unlike
  -- the bigint cast three lines above). Only a JSON STRING value at the `kind` key extracts;
  -- anything else (key absent, JSON null, a non-string value) yields NULL -- "not extractable",
  -- never "not attempted". The digest computation below is UNAFFECTED (still the whole payload).
  --
  -- LENGTH BOUND (amendment 2026-07-27, spec §5 and §1 item 2): the refusal path is precisely
  -- where a hostile/oversized `kind` arrives (the caller is already being refused; nothing
  -- upstream of this function validated the string's length). A found value longer than 256
  -- bytes is treated exactly like "not extractable" -- NULL, never a truncated fragment (a
  -- truncated fragment would be a NEW, function-invented value never actually supplied; NULL
  -- states plainly "not recorded" instead). Checked here in addition to the table-level
  -- refusal_attempted_kind_length CHECK below, so a malformed extraction never even reaches an
  -- INSERT that the CHECK would then have to catch -- belt (function) and suspenders (CHECK),
  -- the s42-law self-application idiom of trusting the table over the caller.
  IF jsonb_typeof(p_payload->'kind') = 'string'
     AND octet_length(p_payload->>'kind') <= 256 THEN
    v_attempted_kind := p_payload->>'kind';
  ELSE
    v_attempted_kind := NULL;
  END IF;
  INSERT INTO ledger (kind, statement, actor,
                      refusal_sqlstate, refusal_message, refusal_surface,
                      refusal_payload_digest, refusal_attempted_actor, refusal_attempted_role,
                      refusal_attempted_kind)
  VALUES ('write_refused',
          format('write refused at surface %s (SQLSTATE %s)', p_surface, p_sqlstate),
          v_wb,
          p_sqlstate, p_message, p_surface,
          encode(sha256(convert_to(p_payload::text, 'utf8')), 'hex'),
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
   attempted `kind` token in refusal_attempted_kind, extracted from the refused payload, TOTAL,
   NULL when not extractable, including when the found value exceeds 256 bytes (s65:
   kernel/lineage/s65-refusal-attempted-kind.sql, amendment 2026-07-27); the payload
   as a SHA-256 digest only (R4). If the journal INSERT itself fails the exception propagates --
   a loud abort, a counted sequence gap, the server log as residual coverage (fail-safe on
   both legs, unchanged by s49/s65). kernel/lineage/s43-typed-verdict-write-boundary.sql;
   kernel/lineage/s49-journaler-overflow-guard.sql; kernel/lineage/
   s65-refusal-attempted-kind.sql.';
-- ============================================================================================

-- ============================================================================================
-- ELEMENT 5 -- kernel.ledger_write RE-ISSUED: extend the SERVER-OWNED payload-key blocklist
-- (s58 Element 7B, kernel/lineage/s58-missive-substrate.sql -- the TRUE immediately-prior
-- re-issue of this function; grepped across every tracked kernel/lineage/sNN-*.sql file: only
-- s43 (birth) and s58 re-issue kernel.ledger_write, s59-s64 never touch it, so s58 is the head
-- at this delta's own authoring time -- the s61 lesson, verified rather than assumed) with the
-- ONE new key this delta mints, refusal_attempted_kind. Body otherwise BYTE-IDENTICAL to s58's
-- own text (base = kernel/lineage/s58-missive-substrate.sql's own text, itself base = s43's own
-- text plus the ADR-0021 Rule B translation -- unedited by s59 through s64). MINOR finding (fix
-- round 2): refusal_attempted_kind is a column ONLY the boundary's own journaler
-- (kernel.journal_write_refusal, Element 4 above) may populate -- a caller-supplied value at
-- this key would be exactly the lying channel s43 Element 4.2's own blocklist exists to close,
-- one column over from its five siblings. This gate lives HERE (ledger_write's own payload-key
-- validation, called on every generic write attempt) rather than in journal_write_refusal
-- itself (which only ever WRITES this column, from its own local extraction, never reads it FROM
-- a caller-supplied payload) -- the SAME separation of concerns the five existing refusal_*
-- blocklist entries already observe.
-- kernel.ledger_write is `:"kern".`-namespaced, OUTSIDE gates/lineage_reissue_lineage.py's own
-- `:"schema".`-anchored citation-check universe (per that gate's own docstring; the SAME
-- disclosed exemption journal_write_refusal's own re-issue above already names) -- the citation/
-- hash below is carried as a matter of this codebase's house idiom, not gate-enforced, exactly
-- like Element 4's.
-- prior-body-sha256: 2df2e77a8d7ddcd07cb6a9d709cabd85cb4cffc2977d46660110f623c0e9ad39 (s58-missive-substrate.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"kern".ledger_write(payload jsonb)
    RETURNS :"kern".write_verdict LANGUAGE plpgsql SECURITY DEFINER
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  k text;
  cols text := '';
  vals text := '';
  v_id bigint;
  v_state text; v_msg text; v_refusal bigint; v_constraint text; v_friendly text;
BEGIN
  BEGIN
    -- payload validation (spec §4.2): every key a ledger column; no server-owned key; no
    -- minted refusal row. Refused loudly AS A VERDICT (RAISE inside the guarded block ->
    -- journaled under class P0), never silently dropped.
    FOR k IN SELECT jsonb_object_keys(payload) LOOP
      IF NOT EXISTS (SELECT 1 FROM pg_attribute a
                     WHERE a.attrelid = 'ledger'::regclass
                       AND a.attname = k AND a.attnum > 0 AND NOT a.attisdropped) THEN
        RAISE EXCEPTION 'write boundary: payload key ''%'' is not a ledger column (kernel/lineage/s43-typed-verdict-write-boundary.sql §4.2) -- payload keys are ledger column names, exactly.', k;
      END IF;
      IF k IN ('id', 'ts', 'row_hash', 'stamp_session', 'stamp_agent', 'stamp_ts',
               'stamp_hmac', 'stamp_verified', 'stamp_invocation',
               'principal_actor_resolution',
               'refusal_sqlstate', 'refusal_message', 'refusal_surface',
               'refusal_payload_digest', 'refusal_attempted_actor',
               'refusal_attempted_role', 'refusal_attempted_kind') THEN
        RAISE EXCEPTION 'write boundary: payload key ''%'' is SERVER-OWNED (id/ts default server-side; stamps and actor-resolution are trigger-computed; refusal_* columns are minted only by the boundary''s own journaler) -- a writer-supplied value would be a lying channel, refused (s43 §4.2). Declared event time rides event_declared_ts (s24); everything else here is the kernel''s to write.', k;
      END IF;
      IF k = 'kind' AND payload->>'kind' = 'write_refused' THEN
        RAISE EXCEPTION 'write boundary: kind ''write_refused'' is minted ONLY by the boundary''s own refusal journaler -- a caller-supplied refusal row is the forgery channel, closed at this same trust boundary (s43 §4.2; the refusal_seq oracle''s count>sequence FAIL is the tripwire behind it).';
      END IF;
      cols := cols || CASE WHEN cols = '' THEN '' ELSE ', ' END || quote_ident(k);
      vals := vals || CASE WHEN vals = '' THEN '' ELSE ', ' END || 'r.' || quote_ident(k);
    END LOOP;
    IF cols = '' THEN
      RAISE EXCEPTION 'write boundary: empty payload -- nothing to write (s43 §4.2).';
    END IF;
    -- per-type casting DERIVED from the rowtype (P1): values pass through
    -- jsonb_populate_record(NULL::ledger, payload); absent keys fall to column defaults.
    EXECUTE format('INSERT INTO ledger (%s) SELECT %s FROM jsonb_populate_record(NULL::ledger, $1) r RETURNING id',
                   cols, vals)
      USING payload INTO v_id;
    SET CONSTRAINTS ALL IMMEDIATE;
    RETURN ('accepted', v_id, NULL, NULL, NULL)::write_verdict;
  EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS v_state = RETURNED_SQLSTATE, v_msg = MESSAGE_TEXT,
                            v_constraint = CONSTRAINT_NAME;
    IF v_state = '23505' THEN
      -- ADR-0021 Rule B: translate a raced ELEMENT 3B unique-violation to the SAME teaching
      -- text the sequential-case EXISTS trigger would have produced, from the surviving
      -- `payload` argument -- never a raw 23505 reaching the caller.
      v_friendly := missive_dedup_race_text(v_constraint, payload);
      IF v_friendly IS NOT NULL THEN v_msg := v_friendly; END IF;
    END IF;
    IF v_state LIKE '22%' OR v_state LIKE '23%' OR v_state LIKE 'P0%' THEN
      v_refusal := journal_write_refusal('ledger', payload, v_state, v_msg);
      RETURN ('refused', NULL, v_refusal, v_state, v_msg)::write_verdict;
    END IF;
    RAISE;   -- infrastructure classes (40/53/57/XX/...): not a denied attempt -- re-raised.
  END;
END; $fn$;
REVOKE ALL ON FUNCTION :"kern".ledger_write(jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION :"kern".ledger_write(jsonb) TO :"role";

COMMENT ON FUNCTION :"kern".ledger_write(jsonb) IS
  'The generic single-row write boundary (s43 §4.2): payload keys are ledger column names,
   values cast via the rowtype (jsonb_populate_record), absent keys fall to defaults;
   server-owned keys and a caller-minted write_refused are refused; a policy/integrity/data
   refusal (SQLSTATE 22*/23*/P0*) is journaled as a committed write_refused row and returned
   as a typed verdict, never an abort; infrastructure classes re-raise. The ONLY generic
   write path -- the granted role holds no ledger INSERT. RE-ISSUED (kernel/lineage/
   s58-missive-substrate.sql ELEMENT 7B, strengthened-tier review, ADR-0021 Rule B): a raced
   ELEMENT 3B unique-violation (SQLSTATE 23505 on missive_sent_dedup_uq/missive_received_
   dedup_uq) is translated to the SAME teaching text validate_missive_dedup''s sequential-case
   EXISTS check produces, via missive_dedup_race_text(). RE-ISSUED AGAIN (kernel/lineage/
   s65-refusal-attempted-kind.sql Element 5, fix round 2): refusal_attempted_kind joins the
   SERVER-OWNED blocklist alongside its five refusal_* siblings -- minted only by
   kernel.journal_write_refusal''s own extraction, never caller-suppliable. Every other
   SQLSTATE/kind is byte-identical to s58''s own path.
   kernel/lineage/s43-typed-verdict-write-boundary.sql; kernel/lineage/s58-missive-substrate.sql;
   kernel/lineage/s65-refusal-attempted-kind.sql.';
-- ============================================================================================
