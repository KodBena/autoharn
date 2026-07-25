-- s58 MISSIVE SUBSTRATE (design/FABLE-MISSIVES-KERNEL-SPEC.md -- Fable-authored, OUT OF FRAME,
-- maintainer-ratified AS IT STANDS 2026-07-25, ledger row 1263, including every §13 construction
-- decision, AS AMENDED by AMENDMENT 1 (2026-07-25, maintainer-ratified "yes to the column"):
-- missive_disposed's subject moved from the base-schema `regards` column (trigger-locked to
-- kind='review' by s15's validate_review, witnessed live: "Ledger policy: regards is reserved
-- for kind=review.") to a NEW dedicated column, missive_regards -- see ELEMENT 3's own note and
-- the new validate_missive_regards trigger, ELEMENT 4 item 6. Sonnet-executed per the standing
-- delegation contract, from this Fable-authored, maintainer-ratified spec (as amended). This
-- delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/existing world is the
-- maintainer's act at a FUTURE world's birth (runs-are-strictly-linear, 2026-07-11) -- never
-- taken here.
--
-- PREREQUISITE: s57 (kernel/lineage/s57-obligation-revocation-event.sql) -- a HARD dependency:
-- this delta re-issues s57's own head texts (ledger_kind_check, compute_row_hash, ledger_current,
-- countersigned_in_force, refusal_surface_check) and transitively s43 (write_verdict TYPE,
-- journal_write_refusal, the boundary-function shape), s51/s52 (artifact tokens cited by
-- missive_cites), s53 (the belief substrate §4 rides on unchanged). THE HEAD-BODY RULE (the
-- s44/s45/s53 discipline, verbatim): at authoring, the lineage head is s57 -- verified by
-- directory read (kernel/lineage/ ls, this delta's own authoring act) before writing a line below.
-- Base bodies re-issued here are quoted, verified, against s57's own head text (compute_row_hash
-- 77 columns, ledger_current/countersigned_in_force 77-column lists, refusal_surface_check six
-- members, validate_supersession_target's s53-head-plus-nothing body -- s54/s55/s56/s57 each
-- confirmed in their own headers they do not touch validate_supersession_target). Applying this
-- file on a pre-s57 kernel fails loudly at CREATE OR REPLACE time (undefined objects to re-issue,
-- undefined write_verdict/journal_write_refusal) -- the correct, disclosed failure mode for a hard
-- dependency.
--
-- WHAT THIS DELTA IS (spec §0): three new ledger kinds (missive_sent, missive_received,
-- missive_disposed), ten missive_-prefixed kind-scoped columns carrying the wire envelope AS
-- TYPED COLUMNS (the envelope IS the row shape -- one home, no second serialization contract,
-- ADR-0012 P7), a one-row kernel.world_identity table (the deployment's own name, one home,
-- consult §4.2), the birth-registered `courier` principal whose kernel-enforced kind-allowlist
-- (validate_missive_courier_scope) makes "foreign content binds local obligation" unrepresentable
-- (Q3, ratified row 1157), and one new SECURITY DEFINER ceremony function
-- kernel.missive_dispose(jsonb) (the two-row disposition+acknowledgment ceremony). s59 (the
-- sibling delta) adds the six derived views, view-only, on top.
--
-- ELEMENT 1 -- kernel.world_identity (spec §2.1): the local deployment's own name, one home
-- (P1) -- the boundary multiplexer's own `_DEPLOYMENT_NAME_RE` shape, byte-identical CHECK,
-- cited in the column COMMENT. Written ONCE by a future world's birth sequence (not here); an
-- s58 world with an EMPTY world_identity refuses every missive write loudly
-- (validate_missive_identity aborts with teach-text) -- fail-safe, the s43 Element 6 write-
-- boundary-principal precedent (a skipped birth step is a loud abort, never a silent default).
--
-- ELEMENT 2 -- KIND VOCABULARY WIDENED (28th-30th members): missive_sent (author-side),
-- missive_received (addressee-side, the courier's ONE writable kind), missive_disposed
-- (addressee-side lifecycle close). Re-issued DROP+ADD (its one home).
--
-- ELEMENT 3 -- TEN missive_-PREFIXED COLUMNS (spec §2.3 table, transcribed verbatim; all
-- nullable, no DEFAULT -- the s30 lesson): missive_protocol/missive_author_world/
-- missive_addressee_world/missive_thread/missive_seq/missive_act are two-way on the TWO envelope
-- kinds (missive_sent, missive_received) -- `(kind IN ('missive_sent','missive_received')) =
-- (col IS NOT NULL)`, a two-member kind-SET two-way CHECK; missive_responds_to/missive_cites are
-- one-way (envelope kinds only, presence within governed separately); missive_provenance is
-- two-way on missive_received ONLY (spec §13 item 1 -- a row cannot carry its own row_hash, so
-- the author-side token is MINTED by s59's missive_outbound view at serve time, never stored on
-- missive_sent); missive_disposition carries THREE CHECKs (spec §2.3 note 2 / §13 item 7): the
-- mandatory-on-missive_disposed CHECK is spelled `kind <> 'missive_disposed' OR ... IS NOT NULL`
-- (a NEW MANDATORY-ON-KIND idiom this codebase had none of before -- classifier extended in
-- ELEMENT 8 below, mirroring FORBIDDEN-ON-KIND's own precedent, s43); the "allowed homes" and
-- "mandatory on acknowledgments" CHECKs are spelled off `missive_act`'s VALUE (never `kind`
-- directly, except the allowed-homes CHECK's own `kind = 'missive_disposed'` disjunct -- see
-- ELEMENT 8) -- the s53 ELEMENT 3 idiom, vacuous and (mostly) classifier-invisible on every
-- non-missive row.
--
-- ELEMENT 4 -- SIX NEW REFUSAL TRIGGERS (spec §2.4, AMENDMENT 1 adds the sixth), beside the
-- existing validate_* family (never folded into a dispatcher, ADR-0012 P1): validate_missive_
-- identity (world_identity resolution + empty-table loud abort), validate_missive_dedup
-- (received-side AND sent-side (author_world/thread/seq) uniqueness, raw-ledger HISTORY-typed
-- reads -- a superseded receipt still blocks re-receipt), validate_missive_tokens (missive_cites
-- token shape+existence, the s48/s52 mechanism reused verbatim; xrow: tokens shape-checked only,
-- foreign-ledger existence deliberately NOT checked at write time -- isolation is founding, spec
-- §2.4 item 3), validate_missive_courier_scope (THE load-bearing type of the family, Q3/
-- ADR-0000 Rule 2(a): the courier principal can write missive_received and NOTHING else --
-- fires on EVERY insert), validate_missive_disposition (missive_regards must name an existing
-- missive_received row; refuses dispositioning an acknowledgment receipt -- no ack-of-ack
-- regress; refuses a second disposition of the same receipt unless it is the ratified same-kind
-- re-disposition), validate_missive_regards (AMENDMENT 1, s58's own object: the two-way KIND
-- correlation on missive_regards -- the named row must be an in-world missive_received row).
-- ALPHABETICAL FIRING ORDER NOTE (spec §2.4 preamble): set_actor (s < v) fires before every
-- validate_*, so NEW.actor is resolved when validate_missive_courier_scope reads it;
-- zz_set_row_hash still fires last (the s26 mechanism, preserved -- every new trigger name here
-- (validate_missive_*) sorts between set_actor and zz_set_row_hash alphabetically, unchanged
-- ordering discipline; validate_missive_regards sorts between validate_missive_identity and
-- validate_missive_tokens).
--
-- ELEMENT 5 -- validate_supersession_target RE-ISSUED (FOURTH re-issue; base = s53's own head
-- text -- s43 write_refused block + s45 standing-lifecycle block + s53 belief block, verified
-- byte-identical and unedited by s54-s57): THREE new blocks appended (spec §2.5, Q7 ratified):
-- a missive_sent target accepts only a same-thread missive_sent successor (no same-actor
-- condition -- the party is the world, spec's own note, §13 item 6); a missive_received target
-- is refused outright (a receipt is a historical fact of arrival -- superseding it is the one
-- path by which delivery could be un-recorded, spec §13 item 6); a missive_disposed target
-- accepts only a same-regards missive_disposed re-disposition (the s45 identity-continuity
-- pattern, one more instance).
--
-- ELEMENT 6 -- kernel.courier: the load-bearing "courier can never bind local obligation"
-- foreclosure is a KERNEL-SIDE trigger (ELEMENT 4); this file does NOT itself register the
-- courier principal -- birth registration through the full kernel.registration_write ceremony
-- is a FUTURE world's scaffold act (spec §2.6, the s40 write-boundary-principal precedent
-- exactly), seeded by hand as owner in this delta's own scratch witness (§11), exactly as
-- genesis is seeded on scratch worlds today.
--
-- ELEMENT 7 -- kernel.missive_dispose(p_payload jsonb) -- the SEVENTH SECURITY DEFINER write
-- boundary (beside s43's four, s51's fifth, s57's sixth), the ONE two-row ceremony this family
-- needs (spec §2.7 -- single-row missive_sent/missive_received/belief writes ride the generic
-- kernel.ledger_write unchanged, the s53 no-new-function precedent, §13 item 9). Payload keys
-- (closed): receipt (required, bigint), disposition (required, closed vocabulary), statement
-- (optional, kernel-generated default otherwise -- no ADR-0020 witness owed, spec §2.7),
-- actor (optional, the standing set_actor default). Refuse-before-write: receipt must name an
-- in-force missive_received row, not itself an acknowledgment; INSERT the missive_disposed row;
-- compute and INSERT the acknowledgment missive_sent row (author=local world, addressee=
-- receipt's author, same thread, seq = 1+max own-sent-seq-in-thread, act='acknowledgment',
-- responds_to=receipt's own provenance, missive_disposition=the disposition, protocol=1); both
-- inserts run the FULL trigger chain inside the ONE guarded block (a disposed-without-
-- acknowledgment state is unrepresentable through this path, the review_write atomicity
-- argument).
--
-- ELEMENT 8 -- SAME-COMMIT SET (the s53 ELEMENT 6 idiom): (a) compute_row_hash RE-ISSUED TO
-- SERIALIZE 87 COLUMNS TOTAL (eleven missive_* fields appended in serialization order -- the
-- original ten plus AMENDMENT 1's missive_regards, s42's law; PROSE CORRECTION, strengthened-
-- tier review: an earlier revision of this sentence said "88", hand-derived from s57's own
-- header claim of a 77-column base rather than gate-verified -- 87 is the number
-- gates/hash_coverage_gate.py ITSELF reports live against the applied chain, the mechanically-
-- checked surface, and is what this sentence now states); (b) ledger_current/
-- countersigned_in_force re-issued +11 appended
-- at end (the s20 lesson); (c) kind CHECK to 30; (d) refusal_surface_check widened to seven
-- members ('missive_dispose'); (e) gates/kind_shape_manifest_gate.py: MANDATORY-ON-KIND is a
-- GENUINELY NEW kind-shape idiom this codebase had none of before (spec's own text says
-- "extended... to parse it" naming the TWO-MEMBER-KIND-SET two-way idiom specifically --
-- verified LIVE at this delta's own authoring time that the existing _TWO_WAY_RE/_KIND_ANY_RE
-- pair ALREADY parses `(kind IN (...)) = (col IS NOT NULL)` with zero classifier edits, because
-- Postgres canonicalizes `kind IN (a,b)` to `kind = ANY (ARRAY[...])`, which _KIND_ANY_RE
-- already reads, and _TWO_WAY_RE is a bare substring search with no anchor on the LEFT side of
-- `=` -- so the spec's own anticipated classifier edit for THAT idiom turned out unnecessary,
-- disclosed here rather than silently carried out anyway; the missive_disposition mandatory-on-
-- missive_disposed CHECK, however, IS a genuinely new idiom (MANDATORY-ON-KIND, `kind <> 'K' OR
-- col IS NOT NULL` -- the mirror image of s43's own FORBIDDEN-ON-KIND, `col IS NULL OR kind <>
-- 'K'`) and the classifier IS extended for it, its own manifest added, both witnessed
-- both-polarity in gates/kind_shape_manifest_gate.py's own scratch harness; ELEVEN new MANIFEST
-- rows total (the nine plain-shaped columns, missive_provenance's single-kind two-way row, and
-- AMENDMENT 1's missive_regards single-kind two-way row -- the (regards, missive_disposed)
-- MANDATORY_ON_KIND_MANIFEST row this delta ORIGINALLY carried, documenting the conflict, is
-- REMOVED by the amendment: regards is untouched, no MANDATORY-ON-KIND fact about it remains);
-- (f) gates/ledger_reader_allowlist.py: entries for validate_missive_dedup/
-- validate_missive_courier_scope/validate_missive_disposition and the re-issued
-- validate_supersession_target (raw-ledger row-addressed/HISTORY-typed reads); (g)
-- gates/hash_coverage_gate.py: no manual edit owed (mechanical chain derivation); (h)
-- s58-missive-substrate.detect.sql, behavior-fingerprinted (ledger_kind_check carries
-- 'missive_sent' AND column missive_thread exists, the s53 two-fact pattern); (i) fixture census
-- bumped (gates/fixture_census.py).
--
-- HISTORY (per-mechanism grounds, the s53/s57 model): all three kinds are BORN here -- every
-- kind-shape/coupling CHECK validates vacuously on pre-existing rows (no prior row can carry
-- kind IN ('missive_sent','missive_received','missive_disposed')); the supersession re-issue's
-- three new blocks gate on target kinds born here -- unreachable on any prior chain;
-- kernel.missive_dispose and kernel.world_identity are new objects with no pre-existing
-- reader/caller; the surface widening (refusal_surface_check) is pure vocabulary addition; the
-- eleven columns/hash/two column-complete views follow the standing additive arguments (the
-- s20/s42 lessons, applied again). AMENDMENT 1's missive_regards is likewise additive: no
-- missive_disposed row exists anywhere (the pre-amendment defect made writing one impossible),
-- so the new column/CHECK/trigger validate vacuously. NOT class-ratified fail-safe despite the
-- additive shape -- it mints ecosystem vocabulary (the s53 routing restated, spec HISTORY
-- paragraph); ships only under design/FABLE-MISSIVES-KERNEL-SPEC.md's own maintainer
-- ratification (ledger row 1263, AMENDMENT 1 2026-07-25).
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a)): this delta's own slice of the spec's own §10, which is
-- the family-intended closure (s58+s59 together) -- reproduced faithfully in slice here for s58's
-- own scope (kinds/columns/CHECKs/triggers/function/world_identity; s59's own header carries the
-- views slice):
--   - INVARIANT: a cross-world missive is representable only as a typed, hash-chained, attributed
--     row in the ACTING world's own ledger; a malformed envelope, an unimplemented protocol
--     version, a wrong party name, a duplicate (author_world, thread, seq) on either side, a
--     courier write of any non-receipt kind, a disposition of a nonexistent/foreign/acknowledgment
--     receipt, and a missive_sent supersession outside a same-thread successor are each refused
--     at construction with the refusal itself a committed write_refused row (s43, inherited).
--   - QUANTIFICATION UNIVERSE: kinds carrying missive_* columns: exactly the three named above
--     (two-way for six columns over the two-member envelope kind-set, one-way for two, two-way
--     over missive_received alone for missive_provenance, the three-CHECK compound for
--     missive_disposition); triggers: FIVE new (validate_missive_identity/_dedup/_tokens/
--     _courier_scope/_disposition), ONE re-issued (validate_supersession_target, +3 blocks);
--     write surfaces: kernel.ledger_write (sent/received/belief, unchanged, generic-key
--     validation covers missive_* columns with zero edits -- verified against s43's own key loop)
--     and kernel.missive_dispose (the new two-row ceremony), both s43-boundary, both journaling.
--   - DENOMINATION: identity in (author_world, thread, seq); content in the row's own SHA-256
--     row_hash (the existing chain, s26/s42); the protocol version in a closed integer CHECK (=1),
--     not a parsed string. No bound in this delta is a bare round literal (the two length bounds
--     in the world/thread shapes derive from the multiplex config's own {1,64} authority; 128 for
--     the thread slug is generous identifier headroom of the same kind as MAX_AFTER_SLUG_BYTES's
--     stated rationale, cited not invented -- spec §10 DENOMINATION, restated).
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT CLASS-RATIFIED FAIL-SAFE
-- -- this delta adds TWO write paths (the courier's own missive_received-only path through the
-- generic boundary, and the new missive_dispose SECURITY DEFINER function) and mints ecosystem
-- vocabulary the whole project will reason in -- exactly what the class-ratification carve-out
-- reserves for the maintainer (the s53/s57 precedent restated). Ships under design/
-- FABLE-MISSIVES-KERNEL-SPEC.md's own maintainer ratification (ledger row 1263, 2026-07-25).
--
-- LIMITS (pre-registered; spec §12, this delta's own slice): the owner/superuser direct-DML
-- trust bound stands (s26+) -- dedup, courier scope, and receipt-unretractability bind
-- granted-role paths only; missive_dispose's seq computation can race a concurrent same-thread
-- disposition -- the loser gets a journaled typed refusal and retries (disclosed, spec §12 item
-- 6); re-disposition ships kernel-lawful (same-kind supersession) but verb-less in v1 (spec §12
-- item 7); v1 authenticity is the fetch act on a single-operator host (spec §12 item 4) -- this
-- file adds, generates, and requires no cryptography (the standing crypto deferral, honored).
-- NO CLI verb ships in THIS file for missive_sent/missive_received/belief (reachable via the
-- generic kernel.ledger_write(jsonb) boundary directly, mirroring s44/s53's own precedent) --
-- the `courier` VERB (spec §5) and boundary wiring are a SEPARATE, same-build deliverable, not
-- kernel/lineage SQL.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s43/.../s57):
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s58val -v kern=s58val_kernel -v role=s58val_rw \
--        -f high_watermark_1.sql -f s20-obligation-grants-and-view-refresh.sql \
--        ... (s21..s57 as in s57's own VALIDATE list) ... \
--        -f s57-obligation-revocation-event.sql -f s58-missive-substrate.sql
--     (genesis seed per s26; register the write-boundary principal, register `courier`, and at
--     least one standing actor principal; INSERT INTO world_identity (world_name) VALUES
--     ('<name>') AS OWNER before exercising any missive write path -- a world with no
--     world_identity refuses every missive write loudly by design, exactly the s43 Element 6
--     posture; see this delta's own ELEMENT 1.)
--   REAL: NEVER applied to any existing world by this authoring act. Enters a FUTURE world's
--   birth chain via bootstrap/new-project.sh's LINEAGE_CHAIN, ONLY as the maintainer's own act
--   (runs-are-strictly-linear, 2026-07-11) -- NOT wired by this commit (the s56/s57 precedent).
--   Authored and scratch-witnessed on scratch schema pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (ADD COLUMN IF NOT EXISTS; DROP+ADD CONSTRAINT;
-- CREATE OR REPLACE FUNCTION/VIEW; DROP+CREATE TRIGGER; CREATE TABLE IF NOT EXISTS).
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
-- ELEMENT 1 -- kernel.world_identity (spec §2.1).
-- ============================================================================================
CREATE TABLE IF NOT EXISTS :"kern".world_identity (
    one_row    boolean PRIMARY KEY DEFAULT true CHECK (one_row),
    world_name text NOT NULL CHECK (world_name ~ '^[a-z0-9-]{1,64}$')
);
REVOKE ALL ON :"kern".world_identity FROM PUBLIC;
GRANT SELECT ON :"kern".world_identity TO :"role";

COMMENT ON TABLE :"kern".world_identity IS
  'kernel/lineage/s58-missive-substrate.sql, spec §2.1: the ONE home for "which world am I" --
   the deployment name the missive substrate stamps into every missive_sent/missive_received row
   (validate_missive_identity). A birth-time kernel setting: written ONCE by a future world''s
   scaffold, SELECT-only to the granted role. An EMPTY table refuses every missive write loudly
   (fail-safe -- the s43 Element 6 write-boundary-principal precedent). world_name''s shape is
   byte-identical to serving/boundary_multiplex_config.py''s own _DEPLOYMENT_NAME_RE -- one
   existing shape authority for world names (P1: no second registry).';
COMMENT ON COLUMN :"kern".world_identity.world_name IS
  'The deployment name (^[a-z0-9-]{1,64}$, the boundary multiplexer''s own naming surface).
   kernel/lineage/s58-missive-substrate.sql.';

-- ============================================================================================
-- ELEMENT 2 -- KIND VOCABULARY WIDENED (28th-30th members).
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS ledger_kind_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT ledger_kind_check CHECK (kind IN
    ('assumption','decision','question','verification',
     'finding','snag','revision','note','review',
     'work_opened','work_claimed','work_depends_on','work_closed',
     'commission','work_violation_disposition',
     'principal_registered','principal_suspended','principal_revoked',
     'principal_standing_declared',
     'principal_relation_asserted','principal_role_bound','principal_key_bound',
     'principal_competence_granted',
     'write_refused',
     'model_identity_attested',
     'belief',
     'obligation_revoked',
     'missive_sent','missive_received','missive_disposed'));

COMMENT ON CONSTRAINT ledger_kind_check ON :"schema".ledger IS
  'kernel/lineage/s58-missive-substrate.sql: widens s57''s twenty-seven-member vocabulary by
   missive_sent (author-side), missive_received (addressee-side, the courier''s ONE writable
   kind), missive_disposed (addressee-side lifecycle close) -- design/FABLE-MISSIVES-KERNEL-
   SPEC.md, ledger row 1263. Ordinary supersedable kinds (missive_sent/missive_disposed retain
   their own supersession disciplines via validate_supersession_target''s missive blocks;
   missive_received is refused outright as a supersession target -- a receipt is unretractable
   history, ELEMENT 5 below).';

-- ============================================================================================
-- ELEMENT 3 -- TEN missive_-PREFIXED COLUMNS (spec §2.3).
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS missive_protocol int;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS missive_author_world text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS missive_addressee_world text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS missive_thread text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS missive_seq int;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS missive_act text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS missive_responds_to text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS missive_provenance text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS missive_cites text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS missive_disposition text;

COMMENT ON COLUMN :"schema".ledger.missive_protocol IS
  'Wire protocol version -- v1 closed (=1). Two-way on the two envelope kinds (missive_sent,
   missive_received). The forward-compat hinge (spec §7, row 1162): a v2 envelope is
   unrepresentable at construction until this CHECK is widened under its own ratified spec.
   kernel/lineage/s58-missive-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.missive_author_world IS
  'The sending world''s deployment name (^[a-z0-9-]{1,64}$). Two-way on the two envelope kinds;
   self-missives refused (missive_author_world <> missive_addressee_world).
   kernel/lineage/s58-missive-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.missive_addressee_world IS
  'The receiving world''s deployment name (^[a-z0-9-]{1,64}$). Two-way on the two envelope
   kinds. kernel/lineage/s58-missive-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.missive_thread IS
  '<minting_world>/<slug> -- globally unique with zero coordination (one home per name, consult
   §3). Two-way on the two envelope kinds. kernel/lineage/s58-missive-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.missive_seq IS
  'Author-local sequence, >= 1. (author_world, thread, seq) is the missive''s global identity
   and dedup key (validate_missive_dedup). Two-way on the two envelope kinds.
   kernel/lineage/s58-missive-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.missive_act IS
  'The closed five-act vocabulary: assertion, request, response, acknowledgment, withdrawal.
   Two-way on the two envelope kinds. kernel/lineage/s58-missive-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.missive_responds_to IS
  'xrow:<world>:<id>:<row_hash> -- mandatory on response/acknowledgment/withdrawal, optional on
   assertion/request (a successor may cite its predecessor). One-way (envelope kinds only).
   kernel/lineage/s58-missive-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.missive_provenance IS
  'The addressee-side citation of the authoritative author-side missive_sent row
   (xrow:<world>:<id>:<row_hash>, MINTED by s59''s missive_outbound view at serve time --
   FORBIDDEN on missive_sent itself, a row cannot carry its own row_hash, spec §13 item 1).
   Two-way on missive_received ONLY. kernel/lineage/s58-missive-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.missive_cites IS
  'Comma-separated row:/artifact:/xrow: tokens (validate_missive_tokens). One-way (envelope
   kinds only), non-empty when present. kernel/lineage/s58-missive-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.missive_disposition IS
  'consumed | declined | superseded-unread | escalated (spec §8). Mandatory on missive_disposed
   and on an acknowledgment missive_sent row; forbidden elsewhere (the three-CHECK compound,
   spec §2.3 note 2 / §13 item 7). kernel/lineage/s58-missive-substrate.sql.';

-- kind-shape CHECKs -- six two-way over the TWO-MEMBER envelope kind-set (a two-way iff over
-- `kind IN ('missive_sent','missive_received')`, spec footnote 1):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_protocol_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_protocol_kind_shape CHECK (
    (kind IN ('missive_sent','missive_received')) = (missive_protocol IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_author_world_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_author_world_kind_shape CHECK (
    (kind IN ('missive_sent','missive_received')) = (missive_author_world IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_addressee_world_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_addressee_world_kind_shape CHECK (
    (kind IN ('missive_sent','missive_received')) = (missive_addressee_world IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_thread_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_thread_kind_shape CHECK (
    (kind IN ('missive_sent','missive_received')) = (missive_thread IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_seq_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_seq_kind_shape CHECK (
    (kind IN ('missive_sent','missive_received')) = (missive_seq IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_act_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_act_kind_shape CHECK (
    (kind IN ('missive_sent','missive_received')) = (missive_act IS NOT NULL));

-- one-way (envelope kinds only) for missive_responds_to/missive_cites:
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_responds_to_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_responds_to_kind_shape CHECK (
    missive_responds_to IS NULL OR kind IN ('missive_sent','missive_received'));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_cites_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_cites_kind_shape CHECK (
    missive_cites IS NULL OR kind IN ('missive_sent','missive_received'));

-- two-way on missive_received ONLY for missive_provenance (spec §13 item 1):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_provenance_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_provenance_kind_shape CHECK (
    (kind = 'missive_received') = (missive_provenance IS NOT NULL));

-- missive_disposition: THREE CHECKs (spec §2.3 note 2).
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_disposition_mandatory_on_disposed;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_disposition_mandatory_on_disposed CHECK (
    kind <> 'missive_disposed' OR missive_disposition IS NOT NULL);
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_disposition_allowed_homes;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_disposition_allowed_homes CHECK (
    missive_disposition IS NULL OR kind = 'missive_disposed' OR missive_act = 'acknowledgment');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_disposition_mandatory_on_ack;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_disposition_mandatory_on_ack CHECK (
    missive_act IS DISTINCT FROM 'acknowledgment' OR missive_disposition IS NOT NULL);

-- missive_disposed requires its subject -- AMENDMENT 1 (2026-07-25, maintainer-ratified "yes to
-- the column"): a DEDICATED column, missive_regards, NOT the core `regards` column (regards is
-- trigger-locked by s15's validate_review to kind='review' ONLY -- witnessed live, both at the
-- SQL boundary function and the HTTP boundary: "Ledger policy: regards is reserved for
-- kind=review."; validate_review is untouched, missives get their own home, ADR-0012 P1 on both
-- sides). Two-way: FORBIDDEN on every kind except missive_disposed, MANDATORY there.
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS missive_regards bigint
    REFERENCES :"schema".ledger(id);
COMMENT ON COLUMN :"schema".ledger.missive_regards IS
  'AMENDMENT 1 (design/FABLE-MISSIVES-KERNEL-SPEC.md, ledger row 1263): the missive_received
   row a missive_disposed event regards -- mirrors the review/regards design rather than
   squatting on it. Two-way: mandatory on missive_disposed, forbidden elsewhere. Self-FK to
   ledger(id) for structural existence; validate_missive_regards enforces the KIND correlation
   (must be missive_received) with the same friendly nonexistent-target teach-text.
   kernel/lineage/s58-missive-substrate.sql.';
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_regards_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_regards_kind_shape CHECK (
    (kind = 'missive_disposed') = (missive_regards IS NOT NULL));

-- value CHECKs (no kind test -- out of the kind-shape manifest's scope, the attest_grade_check
-- precedent):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_protocol_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_protocol_check CHECK (
    missive_protocol IS NULL OR missive_protocol = 1);
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_author_world_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_author_world_shape CHECK (
    missive_author_world IS NULL OR missive_author_world ~ '^[a-z0-9-]{1,64}$');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_addressee_world_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_addressee_world_shape CHECK (
    missive_addressee_world IS NULL OR missive_addressee_world ~ '^[a-z0-9-]{1,64}$');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_self_missive_refused;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_self_missive_refused CHECK (
    missive_author_world IS NULL OR missive_author_world <> missive_addressee_world);
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_thread_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_thread_shape CHECK (
    missive_thread IS NULL OR missive_thread ~ '^[a-z0-9-]{1,64}/[a-z0-9._-]{1,128}$');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_seq_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_seq_check CHECK (
    missive_seq IS NULL OR missive_seq >= 1);
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_act_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_act_check CHECK (
    missive_act IS NULL
    OR missive_act IN ('assertion','request','response','acknowledgment','withdrawal'));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_responds_to_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_responds_to_shape CHECK (
    missive_responds_to IS NULL
    OR missive_responds_to ~ '^xrow:[a-z0-9-]{1,64}:[0-9]+:[0-9a-f]{64}$');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_responds_to_coupling;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_responds_to_coupling CHECK (
    (missive_act IS DISTINCT FROM 'response' OR missive_responds_to IS NOT NULL)
    AND (missive_act IS DISTINCT FROM 'acknowledgment' OR missive_responds_to IS NOT NULL)
    AND (missive_act IS DISTINCT FROM 'withdrawal' OR missive_responds_to IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_provenance_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_provenance_shape CHECK (
    missive_provenance IS NULL
    OR missive_provenance ~ '^xrow:[a-z0-9-]{1,64}:[0-9]+:[0-9a-f]{64}$');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_cites_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_cites_nonempty CHECK (
    missive_cites IS NULL OR btrim(missive_cites) <> '');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS missive_disposition_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT missive_disposition_check CHECK (
    missive_disposition IS NULL
    OR missive_disposition IN ('consumed','declined','superseded-unread','escalated'));

COMMENT ON CONSTRAINT missive_responds_to_coupling ON :"schema".ledger IS
  'design/FABLE-MISSIVES-KERNEL-SPEC.md §2.3: mandatory on response/acknowledgment/withdrawal,
   optional on assertion/request. Spelled off missive_act''s VALUE (the s53 ELEMENT 3 idiom) --
   vacuous, and invisible to the kind-shape classifier, on every non-envelope row.
   kernel/lineage/s58-missive-substrate.sql.';
COMMENT ON CONSTRAINT missive_disposition_mandatory_on_ack ON :"schema".ledger IS
  'design/FABLE-MISSIVES-KERNEL-SPEC.md §2.3 note 2: the disposition travels TYPED in the
   acknowledgment, never prose-only (ADR-0008/ADR-0020). Spelled off missive_act''s VALUE (no
   `kind` literal) -- vacuous on every non-acknowledgment row.
   kernel/lineage/s58-missive-substrate.sql.';

-- ============================================================================================
-- ELEMENT 3B -- CONCURRENCY BACKSTOP FOR DEDUP (strengthened-tier review, kernel axis, one
-- severe): TWO UNIQUE PARTIAL INDEXES. ADR-0021 Rule B ("a fix names its exclusivity
-- primitive... a timing argument is not one"): validate_missive_dedup's own EXISTS checks
-- (ELEMENT 4 item 2, unchanged below) are a plain SELECT under READ COMMITTED and CANNOT close
-- the race -- reproduced live by the reviewer with two concurrent psql sessions, both
-- committing a duplicate (author_world, thread, seq) row on the SAME side. The EXCLUSIVITY
-- PRIMITIVE is these two indexes: Postgres enforces UNIQUE constraints/indexes with its own
-- index-level locking, which a bare SELECT-then-INSERT can never replicate -- one of two
-- concurrent INSERTs targeting the same key WILL be serialized against the other at the index
-- b-tree level and WILL see a unique-violation (SQLSTATE 23505) if it loses, independent of
-- snapshot isolation. Legal supersession never reuses a key (a withdrawal takes a NEW seq,
-- Q7/§2.5), so PERMANENT uniqueness per (author_world, thread, seq) per side is exactly the
-- invariant -- no partial-index predicate needs to account for supersession at all.
-- validate_missive_dedup's EXISTS check remains the TEACHING layer (fires first, in the
-- ordinary sequential case, with its own friendly message); these indexes are the CONCURRENCY
-- BACKSTOP for the case two writers' EXISTS checks both ran before either committed. A raced
-- 23505 is caught and translated to the SAME typed teaching refusal by
-- kernel.missive_dedup_race_text() (ELEMENT 4B) inside the re-issued kernel.ledger_write
-- (ELEMENT 7B) and kernel.missive_dispose (ELEMENT 7) -- never a raw 23505 reaching the caller.
-- ============================================================================================
DROP INDEX IF EXISTS :"schema".missive_sent_dedup_uq;
CREATE UNIQUE INDEX missive_sent_dedup_uq ON :"schema".ledger
    (missive_author_world, missive_thread, missive_seq) WHERE kind = 'missive_sent';
COMMENT ON INDEX :"schema".missive_sent_dedup_uq IS
  'The CONCURRENCY BACKSTOP for the sent-side half of validate_missive_dedup (ELEMENT 4 item 2)
   -- ADR-0021 Rule B''s exclusivity primitive, named: Postgres''s own unique-index locking,
   not a timing argument. A raced duplicate surfaces as SQLSTATE 23505, translated to the
   trigger''s own teaching text by kernel.missive_dedup_race_text() (ELEMENT 4B).
   kernel/lineage/s58-missive-substrate.sql.';
DROP INDEX IF EXISTS :"schema".missive_received_dedup_uq;
CREATE UNIQUE INDEX missive_received_dedup_uq ON :"schema".ledger
    (missive_author_world, missive_thread, missive_seq) WHERE kind = 'missive_received';
COMMENT ON INDEX :"schema".missive_received_dedup_uq IS
  'The CONCURRENCY BACKSTOP for the received-side half of validate_missive_dedup (ELEMENT 4
   item 2) -- same primitive, same translation path, one side over.
   kernel/lineage/s58-missive-substrate.sql.';

-- ============================================================================================
-- ELEMENT 4B -- kernel.missive_dedup_race_text(text, jsonb): the ONE home (ADR-0012 P1) for
-- "what does a raced ELEMENT 3B unique-violation teach" -- reconstructs the SAME friendly text
-- validate_missive_dedup's own EXISTS-path RAISE EXCEPTION produces, from the ORIGINAL PAYLOAD
-- (the row that lost the race no longer exists to re-query once the exception unwinds; the
-- payload jsonb the caller already has is the one surviving source for author_world/thread/seq).
-- Returns NULL for any constraint name this delta does not own -- callers pass the raw message
-- through unchanged in that case (never assume a 23505 this function does not recognize is
-- ours). Called from the re-issued kernel.ledger_write (ELEMENT 7B) and kernel.missive_dispose
-- (ELEMENT 7)'s own exception handlers -- the two write paths that can raise these two indexes'
-- violations.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"kern".missive_dedup_race_text(p_constraint text, p_payload jsonb)
    RETURNS text LANGUAGE sql IMMUTABLE AS $fn$
  SELECT CASE p_constraint
    WHEN 'missive_received_dedup_uq' THEN
      format('missive policy: a missive_received row already exists for (author_world=''%s'', thread=''%s'', seq=%s) -- at-least-once delivery converts to exactly-once RECORDING (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.4 item 2); this refusal is itself journaled, so re-delivery stays visible, never silent. [raced: caught at the missive_received_dedup_uq unique index, ADR-0021 Rule B -- the sequential-case EXISTS check in validate_missive_dedup lost this race, the index caught it]',
             p_payload->>'missive_author_world', p_payload->>'missive_thread', p_payload->>'missive_seq')
    WHEN 'missive_sent_dedup_uq' THEN
      format('missive policy: a missive_sent row already exists for (thread=''%s'', seq=%s) -- the global identity''s author-side half is a one-time fact (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.4 item 2, §13 item 5). [raced: caught at the missive_sent_dedup_uq unique index, ADR-0021 Rule B]',
             p_payload->>'missive_thread', p_payload->>'missive_seq')
    ELSE NULL
  END;
$fn$;

COMMENT ON FUNCTION :"kern".missive_dedup_race_text(text, jsonb) IS
  'kernel/lineage/s58-missive-substrate.sql ELEMENT 4B: the one home for "what a raced ELEMENT
   3B unique-violation teaches" -- reconstructs validate_missive_dedup''s own friendly text from
   the surviving payload jsonb. Returns NULL for any other constraint name (pass the raw
   message through unchanged). ADR-0021 Rule B: the exclusivity primitive is the unique index,
   this function only translates its SQLSTATE into the SAME teaching text the sequential-case
   trigger would have produced.';

-- ============================================================================================
-- ELEMENT 4 -- SIX NEW REFUSAL TRIGGERS (spec §2.4, AMENDMENT 1).
-- ============================================================================================

-- 1. validate_missive_identity -- world_identity resolution; empty table = loud abort.
CREATE OR REPLACE FUNCTION :"schema".validate_missive_identity() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_local text;
BEGIN
  IF NEW.kind IN ('missive_sent', 'missive_received') THEN
    SELECT world_name INTO v_local FROM world_identity WHERE one_row;
    IF v_local IS NULL THEN
      RAISE EXCEPTION 'missive policy: this world has NO registered world identity (kernel.world_identity is empty) -- the s58 birth step was skipped (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.1). Nothing was recorded; a missive world must be born with its own name before it can send or receive.';
    END IF;
    IF NEW.kind = 'missive_sent' AND NEW.missive_author_world <> v_local THEN
      RAISE EXCEPTION 'missive policy: a missive_sent row must name THIS world (''%'') as missive_author_world -- got ''%''. A world cannot record itself sending another world''s missive (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.4 item 1).', v_local, NEW.missive_author_world;
    END IF;
    IF NEW.kind = 'missive_received' AND NEW.missive_addressee_world <> v_local THEN
      RAISE EXCEPTION 'missive policy: a missive_received row must name THIS world (''%'') as missive_addressee_world -- got ''%''. A world cannot record receiving a missive not addressed to it (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.4 item 1).', v_local, NEW.missive_addressee_world;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_missive_identity ON :"schema".ledger;
CREATE TRIGGER validate_missive_identity BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_missive_identity();

COMMENT ON FUNCTION :"schema".validate_missive_identity() IS
  'kernel/lineage/s58-missive-substrate.sql §2.4 item 1: a missive_sent row must name this
   world as author, a missive_received row must name it as addressee; an empty
   kernel.world_identity refuses every missive write loudly (the s43 Element 6 posture).';

-- 2. validate_missive_dedup -- received-side AND sent-side (author_world, thread, seq) dedup.
CREATE OR REPLACE FUNCTION :"schema".validate_missive_dedup() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
BEGIN
  IF NEW.kind = 'missive_received' THEN
    IF EXISTS (SELECT 1 FROM ledger r
               WHERE r.kind = 'missive_received'
                 AND r.missive_author_world = NEW.missive_author_world
                 AND r.missive_thread = NEW.missive_thread
                 AND r.missive_seq = NEW.missive_seq) THEN
      RAISE EXCEPTION 'missive policy: a missive_received row already exists for (author_world=''%'', thread=''%'', seq=%) -- at-least-once delivery converts to exactly-once RECORDING (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.4 item 2); this refusal is itself journaled, so re-delivery stays visible, never silent.', NEW.missive_author_world, NEW.missive_thread, NEW.missive_seq;
    END IF;
  ELSIF NEW.kind = 'missive_sent' THEN
    IF EXISTS (SELECT 1 FROM ledger s
               WHERE s.kind = 'missive_sent'
                 AND s.missive_thread = NEW.missive_thread
                 AND s.missive_seq = NEW.missive_seq) THEN
      RAISE EXCEPTION 'missive policy: a missive_sent row already exists for (thread=''%'', seq=%) -- the global identity''s author-side half is a one-time fact (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.4 item 2, §13 item 5).', NEW.missive_thread, NEW.missive_seq;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_missive_dedup ON :"schema".ledger;
CREATE TRIGGER validate_missive_dedup BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_missive_dedup();

COMMENT ON FUNCTION :"schema".validate_missive_dedup() IS
  'kernel/lineage/s58-missive-substrate.sql §2.4 item 2: refuses a duplicate (author_world,
   thread, seq) on missive_received (raw-ledger, HISTORY-typed -- a superseded receipt still
   blocks re-receipt) and a duplicate (thread, seq) missive_sent row (author is the local world
   by trigger 1) -- the global identity''s author-side half, and the floor under
   kernel.missive_dispose''s own seq computation.';

-- 3. validate_missive_tokens -- missive_cites shape+existence (row:/artifact: checked; xrow:
--    shape-only, foreign-ledger existence deliberately NOT checked at write time).
CREATE OR REPLACE FUNCTION :"schema".validate_missive_tokens() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_tok text;
  v_id bigint;
BEGIN
  IF NEW.missive_cites IS NOT NULL THEN
    FOREACH v_tok IN ARRAY string_to_array(NEW.missive_cites, ',') LOOP
      v_tok := btrim(v_tok);
      IF v_tok ~ '^row:[0-9]+$' THEN
        v_id := substring(v_tok FROM 5)::bigint;
        IF NOT EXISTS (SELECT 1 FROM ledger WHERE id = v_id) THEN
          RAISE EXCEPTION 'missive policy: missive_cites token ''%'' names no existing row (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.4 item 3).', v_tok;
        END IF;
      ELSIF v_tok ~ '^artifact:[0-9a-f]{64}$' THEN
        IF NOT EXISTS (SELECT 1 FROM artifact WHERE hash = substring(v_tok FROM 10)) THEN
          RAISE EXCEPTION 'missive policy: missive_cites token ''%'' names no existing artifact (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.4 item 3).', v_tok;
        END IF;
      ELSIF v_tok ~ '^xrow:[a-z0-9-]{1,64}:[0-9]+:[0-9a-f]{64}$' THEN
        NULL; -- shape-checked only -- foreign-ledger existence deliberately NOT checked (isolation is founding).
      ELSE
        RAISE EXCEPTION 'missive policy: missive_cites token ''%'' matches no known token shape (row:, artifact:, xrow:) (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.4 item 3).', v_tok;
      END IF;
    END LOOP;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_missive_tokens ON :"schema".ledger;
CREATE TRIGGER validate_missive_tokens BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_missive_tokens();

COMMENT ON FUNCTION :"schema".validate_missive_tokens() IS
  'kernel/lineage/s58-missive-substrate.sql §2.4 item 3: missive_cites token shape check for
   all three forms (row:, artifact:, xrow:); local row:/artifact: tokens are EXISTENCE-checked
   (the s48/s52 mechanism); xrow: tokens are shape-checked ONLY -- foreign-ledger existence is
   deliberately not checked at write time (isolation is founding; the audit leg, spec §9, covers
   it later).';

-- 4. validate_missive_courier_scope -- THE load-bearing type of the family (Q3, ADR-0000 Rule
--    2(a)): fires on EVERY insert.
CREATE OR REPLACE FUNCTION :"schema".validate_missive_courier_scope() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_courier_id bigint;
BEGIN
  SELECT id INTO v_courier_id FROM principal WHERE name = 'courier';
  IF v_courier_id IS NOT NULL AND NEW.actor = v_courier_id AND NEW.kind <> 'missive_received' THEN
    RAISE EXCEPTION 'missive policy: the courier principal records arrivals and NOTHING else (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.4 item 4, Q3 ratified row 1157) -- attempted kind ''%''. The only path from "missive arrived" to local work, decision, belief, or disposition is a non-courier local principal''s own attributable write citing the receipt (Q4). Nothing was recorded.', NEW.kind;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_missive_courier_scope ON :"schema".ledger;
CREATE TRIGGER validate_missive_courier_scope BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_missive_courier_scope();

COMMENT ON FUNCTION :"schema".validate_missive_courier_scope() IS
  'kernel/lineage/s58-missive-substrate.sql §2.4 item 4 (Q3, ratified row 1157): the courier
   principal''s ONLY writable kind is missive_received -- forecloses "foreign content binds
   local obligation" at the type layer. A world with no registered courier is a no-op (absent
   -> nothing to scope). Fires on EVERY insert, ahead of every other validate_* (alphabetical
   firing order: set_actor < validate_missive_courier_scope < zz_set_row_hash).';

-- 5. validate_missive_disposition -- missive_regards must name an existing missive_received
--    row (AMENDMENT 1: was `regards`, moved to the dedicated column); no ack-of-ack;
--    re-disposition only via same-kind supersession.
--
-- CONCURRENCY, FOUND AND CLOSED (strengthened-tier review, kernel axis, one severe -- reproduced
-- live by the reviewer with two concurrent psql sessions: two racing dispositions of the SAME
-- receipt both passed the EXISTS re-disposition check below and both committed, each minting
-- its own acknowledgment). A plain UNIQUE index cannot express "at most one IN-FORCE
-- missive_disposed per receipt" (legal re-disposition, ELEMENT 5/Q7, deliberately leaves BOTH
-- rows in the table -- the superseded one stays, only its in-force-ness changes) -- serialize
-- instead. THE EXCLUSIVITY PRIMITIVE (ADR-0021 Rule B, named, not a timing argument):
-- pg_advisory_xact_lock, keyed on a schema-scoped hash of missive_regards (the s26 row_hash_
-- chain lock's own idiom, one table over -- `hashtext(TG_TABLE_SCHEMA || '.missive_disposed.'
-- || NEW.missive_regards::text)::bigint`), acquired HERE, before the EXISTS check below, and
-- held to COMMIT (a plain pg_advisory_xact_lock, not the _lock()/_unlock() pair -- released
-- automatically at transaction end, matching s26's own choice). THE ORDERING ARGUMENT: two
-- concurrent dispositions of the same receipt call this trigger with the same lock key; the
-- SECOND to arrive at pg_advisory_xact_lock blocks until the FIRST's transaction commits or
-- aborts; once unblocked, the second transaction's EXISTS check runs on ITS OWN (by-then-
-- refreshed) READ COMMITTED snapshot, which now, provably, contains the first transaction's
-- committed missive_disposed row (a snapshot taken after a COMMIT that happened-before it, by
-- MVCC's own visibility rule) -- so the existing EXISTS-based refusal fires for the loser,
-- exactly as it does in the sequential case, not a narrowed window, an actual serialization.
-- Two DIFFERENT receipts take DIFFERENT lock keys and never contend.
CREATE OR REPLACE FUNCTION :"schema".validate_missive_disposition() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_tgt_kind text;
  v_tgt_act text;
BEGIN
  IF NEW.kind = 'missive_disposed' THEN
    IF NEW.missive_regards IS NOT NULL THEN
      -- the exclusivity primitive: serialize every disposition attempt against THIS receipt.
      PERFORM pg_advisory_xact_lock(
        hashtext(TG_TABLE_SCHEMA || '.missive_disposed.' || NEW.missive_regards::text)::bigint);
    END IF;
    SELECT l.kind, l.missive_act INTO v_tgt_kind, v_tgt_act
      FROM ledger l WHERE l.id = NEW.missive_regards;
    IF v_tgt_kind IS NULL THEN
      RAISE EXCEPTION 'missive policy: missive_regards row % does not exist (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.4 item 5, AMENDMENT 1). Nothing was recorded.', NEW.missive_regards;
    ELSIF v_tgt_kind <> 'missive_received' THEN
      RAISE EXCEPTION 'missive policy: missive_regards row % (kind ''%'') is not a missive_received row -- a disposition regards a RECEIPT, nothing else (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.4 item 5, AMENDMENT 1).', NEW.missive_regards, v_tgt_kind;
    ELSIF v_tgt_act = 'acknowledgment' THEN
      RAISE EXCEPTION 'missive policy: row % is an acknowledgment receipt -- acknowledgments are consumed mechanically by missive_delivery_audit; dispositioning one would mint an ack-of-ack regress (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.4 item 5). Nothing was recorded.', NEW.missive_regards;
    ELSIF EXISTS (
      SELECT 1 FROM ledger d
      WHERE d.kind = 'missive_disposed' AND d.missive_regards = NEW.missive_regards
        AND NOT EXISTS (SELECT 1 FROM ledger s2 WHERE s2.supersedes = d.id)
        AND (NEW.supersedes IS NULL OR NEW.supersedes <> d.id)
    ) THEN
      RAISE EXCEPTION 'missive policy: receipt % already carries an in-force disposition -- a second disposition is refused unless this write SUPERSEDES exactly that prior disposition (same-kind re-disposition, design/FABLE-MISSIVES-KERNEL-SPEC.md §2.4 item 5, §2.5). Nothing was recorded.', NEW.missive_regards;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_missive_disposition ON :"schema".ledger;
CREATE TRIGGER validate_missive_disposition BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_missive_disposition();

COMMENT ON FUNCTION :"schema".validate_missive_disposition() IS
  'kernel/lineage/s58-missive-substrate.sql §2.4 item 5 (AMENDMENT 1): missive_regards must name
   an existing missive_received row, not itself an acknowledgment; refuses a second in-force
   disposition of the same receipt unless this write supersedes exactly the prior one
   (re-disposition). CONCURRENCY (strengthened-tier review, ADR-0021 Rule B): pg_advisory_xact_
   lock keyed on missive_regards, taken before the re-disposition EXISTS check, serializes
   concurrent dispositions of the SAME receipt -- the exclusivity primitive and its ordering
   argument are stated in full above this function''s own DEFINE.';

-- 6. validate_missive_regards -- AMENDMENT 1 (2026-07-25, maintainer-ratified "yes to the
--    column"): s58's own dedicated object for the two-way KIND correlation "the named row must
--    be an in-world missive_received row" -- the same nonexistent-target refusal the build
--    already witnessed, now on missive_regards' own home rather than borrowed from validate_
--    missive_disposition (a deliberate, disclosed overlap with that trigger's own existence/kind
--    check -- both independently refuse the same defect class, mirroring validate_review's own
--    FK-plus-trigger duplication precedent one column family over; harmless regardless of
--    firing order since either raising aborts the same INSERT).
CREATE OR REPLACE FUNCTION :"schema".validate_missive_regards() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_tgt_kind text;
BEGIN
  IF NEW.missive_regards IS NOT NULL THEN
    SELECT l.kind INTO v_tgt_kind FROM ledger l WHERE l.id = NEW.missive_regards;
    IF v_tgt_kind IS NULL THEN
      RAISE EXCEPTION 'missive policy: missive_regards row % does not exist (design/FABLE-MISSIVES-KERNEL-SPEC.md AMENDMENT 1). Nothing was recorded.', NEW.missive_regards;
    ELSIF v_tgt_kind <> 'missive_received' THEN
      RAISE EXCEPTION 'missive policy: missive_regards row % (kind ''%'') is not a missive_received row -- a disposition regards a RECEIPT, nothing else (design/FABLE-MISSIVES-KERNEL-SPEC.md AMENDMENT 1).', NEW.missive_regards, v_tgt_kind;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_missive_regards ON :"schema".ledger;
CREATE TRIGGER validate_missive_regards BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_missive_regards();

COMMENT ON FUNCTION :"schema".validate_missive_regards() IS
  'design/FABLE-MISSIVES-KERNEL-SPEC.md AMENDMENT 1 (2026-07-25, ratified "yes to the column"):
   the two-way KIND correlation for missive_regards -- the named row must be an in-world
   missive_received row; a nonexistent or wrong-kind target is refused with teaching. s58''s own
   dedicated object (not folded into validate_missive_disposition, ADR-0012 P1: the
   kind-correlation fact gets its own home, exactly as missive_regards itself got its own column
   rather than reusing regards). kernel/lineage/s58-missive-substrate.sql.';

-- PROSE CORRECTION (strengthened-tier review, prose minor): triggers 2 (validate_missive_
-- dedup), 3 (validate_missive_tokens), 5 (validate_missive_disposition), 6 (validate_missive_
-- regards, AMENDMENT 1) and the re-issued supersession trigger (ELEMENT 5) read raw `ledger`
-- by row-addressed/HISTORY-typed reads -- gates/ledger_reader_allowlist.py gains their entries
-- with reasons, same commit (the s53 ELEMENT 6(e) discipline). Trigger 4 (validate_missive_
-- courier_scope) reads kernel.principal ONLY (a row-addressed lookup by name, resolved once
-- per insert) -- it does NOT read `ledger` at all, and correctly carries no
-- ledger_reader_allowlist entry (verified live: "no raw-ledger access", the gate's own clean
-- classification) -- an earlier revision of this sentence misnamed it as a ledger reader and
-- omitted trigger 3; corrected here to match what the gate itself already verifies.

-- ============================================================================================
-- ELEMENT 5 -- validate_supersession_target RE-ISSUED (FOURTH re-issue): s43's write_refused
-- block, s45's standing-lifecycle block, and s53's belief block stay BYTE-IDENTICAL and first
-- (verified against s53's own head text, unedited by s54-s57); THREE new blocks appended (spec
-- §2.5, Q7 ratified).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_supersession_target() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_target_kind text;
  v_target_db_role text;
  v_target_subject bigint;
  v_target_actor bigint;
  v_target_thread text;
  v_target_regards bigint;
BEGIN
  IF NEW.supersedes IS NOT NULL THEN
    SELECT l.kind, l.principal_db_role, l.principal_subject, l.actor, l.missive_thread,
           l.missive_regards
      INTO v_target_kind, v_target_db_role, v_target_subject, v_target_actor, v_target_thread,
           v_target_regards
      FROM ledger l WHERE l.id = NEW.supersedes;

    IF v_target_kind = 'write_refused' THEN
      RAISE EXCEPTION 'Ledger policy: a write_refused row is UNRETRACTABLE (s43, ratified R6) — row % records a historical fact about a refused attempt; it asserts nothing retractable, and superseding it is the one path by which a later writer could make a refusal vanish from every current view. The record stands; if the refusal was wrong, the corrected write simply succeeds beside it (kernel/lineage/s43-typed-verdict-write-boundary.sql Element 2).', NEW.supersedes;
    END IF;

    -- s45 §3.4: standing-lifecycle supersession discipline (byte-identical, s45's own text).
    IF v_target_kind IN ('principal_standing_declared', 'principal_suspended', 'principal_revoked') THEN
      IF NEW.kind IS DISTINCT FROM v_target_kind THEN
        RAISE EXCEPTION 'Ledger policy: a standing-lifecycle row (kind ''%'', row %) is superseded ONLY by its OWN kind (s45, kernel/lineage/s45-standing-lifecycle.sql §3.4) — this write is kind ''%''. Rotation/re-declaration or unbind for declarations (./led principal declare-standing / ./led principal undeclare-standing); re-suspend-correction or lift for suspensions (./led principal suspend --supersedes / ./led principal lift-suspension); re-revoke-correction for revocations. A cross-kind supersession would silently alter derived standing (who a role speaks for, or whether a principal is suspended/revoked) with no typed act — refused at construction.', v_target_kind, NEW.supersedes, NEW.kind;
      END IF;

      IF v_target_kind = 'principal_standing_declared' THEN
        IF NEW.principal_db_role IS DISTINCT FROM v_target_db_role THEN
          RAISE EXCEPTION 'Ledger policy: a row superseding a standing declaration must restate the SAME db_role its target governs (s45 §3.4) — target row % binds role ''%'', this write names ''%''. A rotation or unbind restates the role it governs; to bind a DIFFERENT role, write a fresh (non-superseding) declaration instead.', NEW.supersedes, v_target_db_role, NEW.principal_db_role;
        END IF;
        IF NEW.principal_binding_active = false AND NEW.principal_subject IS DISTINCT FROM v_target_subject THEN
          RAISE EXCEPTION 'Ledger policy: an UNBIND must restate the SAME subject principal its target declaration binds (s45 §3.4) — target row % binds principal %, this unbind names %. A ROTATION (principal_binding_active=true) may repoint the subject by design; an unbind may not.', NEW.supersedes, v_target_subject, NEW.principal_subject;
        END IF;
      ELSIF v_target_kind IN ('principal_suspended', 'principal_revoked') THEN
        IF NEW.principal_subject IS DISTINCT FROM v_target_subject THEN
          RAISE EXCEPTION 'Ledger policy: a lift or rationale-correction must restate the SAME subject principal its target row regards (s45 §3.4) — target row % (kind ''%'') regards principal %, this write names %.', NEW.supersedes, v_target_kind, v_target_subject, NEW.principal_subject;
        END IF;
      END IF;
    END IF;

    -- s53: belief supersession discipline (unedited).
    IF v_target_kind = 'belief' THEN
      IF NEW.kind IS DISTINCT FROM 'belief' THEN
        RAISE EXCEPTION 'belief policy: a belief is revised only by its own holder through supersession (s31 uniform retraction), same kind (s53, design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.3) — this write is kind ''%'', but row % is a belief. Another principal''s contrary position is a CONTEST — write your own belief with contests=row:% and both enter visible doubt until resolved by evidence class or withdrawal (Q3, paraconsistent; recency never decides between principals).', NEW.kind, NEW.supersedes, NEW.supersedes;
      ELSIF NEW.actor IS NOT NULL AND v_target_actor IS NOT NULL AND NEW.actor <> v_target_actor THEN
        RAISE EXCEPTION 'belief policy: a belief is superseded only by its own holder (supersession = self-revision, s31) — row % is held by a different principal than this write''s actor (s53, design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.3). Another principal''s contrary position is a CONTEST — write your own belief with contests=row:% and both enter visible doubt until resolved by evidence class or withdrawal (Q3, paraconsistent; recency never decides between principals).', NEW.supersedes, NEW.supersedes;
      END IF;
    END IF;

    -- s58: missive_sent supersession discipline (Q7 ratified, spec §2.5) -- superseding a
    -- missive_sent row is refused unless the superseding row is itself the successor missive
    -- in the SAME thread. No same-actor condition -- the party is the world, not the principal
    -- (spec §13 item 6).
    IF v_target_kind = 'missive_sent' THEN
      IF NOT (NEW.kind = 'missive_sent' AND NEW.missive_thread = v_target_thread) THEN
        RAISE EXCEPTION 'missive policy: a missive_sent row (row %, thread ''%'') is superseded ONLY by a same-thread successor missive_sent row (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.5, Q7 ratified) — an author revising its position SENDS the revision (a withdrawal, or a successor assertion/request with responds_to) so the supersession itself travels and the addressee''s missive_stale view sees it; a silent local retraction is exactly the staleness class this family exists to close.', NEW.supersedes, v_target_thread;
      END IF;
    END IF;

    -- s58: missive_received target refused outright -- a receipt is unretractable history
    -- (spec §2.5, §13 item 6).
    IF v_target_kind = 'missive_received' THEN
      RAISE EXCEPTION 'missive policy: a missive_received row (row %) may NEVER be superseded — a receipt is a historical fact of arrival; superseding it is the one path by which delivery could be un-recorded and by which the dedup guarantee could be argued around (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.5, §13 item 6). Nothing was recorded.', NEW.supersedes;
    END IF;

    -- s58: missive_disposed supersession discipline -- re-disposition of the SAME receipt only
    -- (the s45 identity-continuity pattern, spec §2.5; AMENDMENT 1: was `regards`, now
    -- `missive_regards`).
    IF v_target_kind = 'missive_disposed' THEN
      IF NOT (NEW.kind = 'missive_disposed' AND NEW.missive_regards = v_target_regards) THEN
        RAISE EXCEPTION 'missive policy: a missive_disposed row (row %, regards %) is superseded ONLY by a same-kind re-disposition regarding the SAME receipt (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.5) — this write is kind ''%'' regarding %.', NEW.supersedes, v_target_regards, NEW.kind, NEW.missive_regards;
      END IF;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_supersession_target ON :"schema".ledger;
CREATE TRIGGER validate_supersession_target BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_supersession_target();

COMMENT ON FUNCTION :"schema".validate_supersession_target() IS
  'BEFORE INSERT trigger (s43 Element 2/R6, widened s45 §3.4, widened s53 §3.2 item 4/§3.3,
   widened s58 §2.5/Q7): (1) a write_refused row is unretractable; (2) the three
   standing-lifecycle kinds accept only SAME-KIND, IDENTITY-CONTINUOUS supersessors; (3) a
   belief row is superseded only by its own holder; (4) a missive_sent row is superseded only
   by a same-thread successor missive_sent row; (5) a missive_received row may never be
   superseded; (6) a missive_disposed row is superseded only by a same-regards re-disposition
   (kernel/lineage/s58-missive-substrate.sql).';

-- ============================================================================================
-- ELEMENT 6 -- refusal_surface_check WIDENED by one member ('missive_dispose'), the SAME
-- pattern s51's/s57's own widening uses.
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_surface_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_surface_check CHECK (
    refusal_surface IS NULL
    OR refusal_surface IN ('ledger', 'review', 'registration', 'obligation', 'artifact',
                            'obligation_revoke', 'missive_dispose'));

COMMENT ON CONSTRAINT refusal_surface_check ON :"schema".ledger IS
  'kernel/lineage/s58-missive-substrate.sql widens s57''s six-member closed vocabulary by
   ''missive_dispose'' -- the SEVENTH SECURITY DEFINER boundary function''s own surface name,
   journaled by the SAME kernel.journal_write_refusal every other surface already uses. Pure
   value-vocabulary addition.';

-- ============================================================================================
-- ELEMENT 7 -- kernel.missive_dispose(jsonb): the SEVENTH SECURITY DEFINER write boundary.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"kern".missive_dispose(p_payload jsonb)
    RETURNS :"kern".write_verdict LANGUAGE plpgsql SECURITY DEFINER
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  k text;
  v_receipt bigint;
  v_disposition text;
  v_statement text;
  v_actor bigint;
  v_receipt_kind text;
  v_receipt_act text;
  v_receipt_author_world text;
  v_receipt_thread text;
  v_receipt_provenance text;
  v_local_world text;
  v_disp_id bigint;
  v_seq int;
  v_ack_id bigint;
  v_state text; v_msg text; v_refusal bigint; v_constraint text; v_friendly text;
BEGIN
  BEGIN
    FOR k IN SELECT jsonb_object_keys(p_payload) LOOP
      IF k NOT IN ('receipt', 'disposition', 'statement', 'actor') THEN
        RAISE EXCEPTION 'write boundary: missive-disposition payload key ''%'' is not a member of the disposition ceremony''s contract (receipt, disposition, statement, actor -- kernel/lineage/s58-missive-substrate.sql).', k;
      END IF;
    END LOOP;
    IF NOT (p_payload ? 'receipt') THEN
      RAISE EXCEPTION 'write boundary: missive-disposition payload is missing ''receipt'' (kernel/lineage/s58-missive-substrate.sql).';
    END IF;
    v_receipt := (p_payload->>'receipt')::bigint;
    IF NOT (p_payload ? 'disposition') OR btrim(p_payload->>'disposition') = '' THEN
      RAISE EXCEPTION 'write boundary: missive-disposition payload is missing a non-empty ''disposition'' (kernel/lineage/s58-missive-substrate.sql).';
    END IF;
    v_disposition := p_payload->>'disposition';
    v_actor := CASE WHEN p_payload ? 'actor' THEN (p_payload->>'actor')::bigint ELSE NULL END;

    SELECT l.kind, l.missive_act, l.missive_author_world, l.missive_thread, l.missive_provenance
      INTO v_receipt_kind, v_receipt_act, v_receipt_author_world, v_receipt_thread,
           v_receipt_provenance
      FROM ledger l
      WHERE l.id = v_receipt
        AND NOT EXISTS (SELECT 1 FROM ledger s WHERE s.supersedes = l.id);
    IF v_receipt_kind IS NULL THEN
      RAISE EXCEPTION 'write boundary: missive-disposition names receipt % -- no in-force missive_received row exists with that id (kernel/lineage/s58-missive-substrate.sql). Nothing was recorded.', v_receipt;
    END IF;
    IF v_receipt_kind <> 'missive_received' THEN
      RAISE EXCEPTION 'write boundary: missive-disposition names row % (kind ''%'') -- not a missive_received row (kernel/lineage/s58-missive-substrate.sql). Nothing was recorded.', v_receipt, v_receipt_kind;
    END IF;
    IF v_receipt_act = 'acknowledgment' THEN
      RAISE EXCEPTION 'write boundary: receipt % is an acknowledgment -- acknowledgments are consumed mechanically, never dispositioned (kernel/lineage/s58-missive-substrate.sql). Nothing was recorded.', v_receipt;
    END IF;

    SELECT world_name INTO v_local_world FROM world_identity WHERE one_row;
    IF v_local_world IS NULL THEN
      RAISE EXCEPTION 'write boundary: this world has no registered world identity (kernel.world_identity is empty) -- the s58 birth step was skipped (kernel/lineage/s58-missive-substrate.sql).';
    END IF;

    v_statement := COALESCE(p_payload->>'statement',
                             format('disposition: %s of %s', v_disposition, v_receipt_provenance));

    -- step 2: the missive_disposed row (AMENDMENT 1: missive_regards, not regards).
    INSERT INTO ledger (kind, statement, actor, missive_regards, missive_disposition)
    VALUES ('missive_disposed', v_statement, v_actor, v_receipt, v_disposition)
    RETURNING id INTO v_disp_id;

    -- step 3: compute the acknowledgment envelope.
    SELECT 1 + COALESCE(MAX(s.missive_seq), 0) INTO v_seq
      FROM ledger s
      WHERE s.kind = 'missive_sent' AND s.missive_thread = v_receipt_thread;

    -- step 4: the acknowledgment missive_sent row (same actor).
    INSERT INTO ledger (kind, statement, actor,
                         missive_protocol, missive_author_world, missive_addressee_world,
                         missive_thread, missive_seq, missive_act, missive_responds_to,
                         missive_disposition)
    VALUES ('missive_sent', v_statement, v_actor,
            1, v_local_world, v_receipt_author_world,
            v_receipt_thread, v_seq, 'acknowledgment', v_receipt_provenance,
            v_disposition)
    RETURNING id INTO v_ack_id;

    SET CONSTRAINTS ALL IMMEDIATE;
    RETURN ('accepted', v_disp_id, NULL, NULL, NULL)::write_verdict;
  EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS v_state = RETURNED_SQLSTATE, v_msg = MESSAGE_TEXT,
                            v_constraint = CONSTRAINT_NAME;
    IF v_state LIKE '22%' OR v_state LIKE '23%' OR v_state LIKE 'P0%' THEN
      -- ADR-0021 Rule B: a raced ELEMENT 3B unique-violation on the acknowledgment's OWN
      -- missive_sent insert (step 4 -- two concurrent dispositions in the same thread racing
      -- the seq computation, step 3) is translated to the SAME teaching text ELEMENT 4B gives
      -- the generic path, built from the values THIS function already computed (v_receipt_
      -- thread/v_local_world/v_seq), never the caller's p_payload (which carries no envelope
      -- fields of its own -- receipt/disposition/statement/actor only).
      IF v_state = '23505' THEN
        v_friendly := missive_dedup_race_text(v_constraint, jsonb_build_object(
          'missive_author_world', v_local_world, 'missive_thread', v_receipt_thread,
          'missive_seq', v_seq));
        IF v_friendly IS NOT NULL THEN v_msg := v_friendly; END IF;
      END IF;
      v_refusal := journal_write_refusal('missive_dispose', p_payload, v_state, v_msg);
      RETURN ('refused', NULL, v_refusal, v_state, v_msg)::write_verdict;
    END IF;
    RAISE;   -- infrastructure classes (40/53/57/XX/...): not a denied attempt -- re-raised.
  END;
END; $fn$;
REVOKE ALL ON FUNCTION :"kern".missive_dispose(jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION :"kern".missive_dispose(jsonb) TO :"role";

COMMENT ON FUNCTION :"kern".missive_dispose(jsonb) IS
  'The SEVENTH SECURITY DEFINER write boundary (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.7),
   beside s43''s four, s51''s fifth, s57''s sixth: the two-row disposition+acknowledgment
   ceremony. Payload keys: receipt (required, bigint), disposition (required, closed
   vocabulary), statement (optional, kernel-generated otherwise), actor (optional, the standing
   set_actor default). Refuses a nonexistent/foreign/acknowledgment receipt and a duplicate
   disposition (the validate_missive_disposition trigger''s pg_advisory_xact_lock-serialized
   EXISTS check, fired inside this same guarded block -- ADR-0021 Rule B, see that trigger''s
   own header); on accept, writes a missive_disposed row and an acknowledgment missive_sent row
   atomically -- a disposed-without-acknowledgment state is unrepresentable through this path. A
   raced ELEMENT 3B unique-violation on the acknowledgment''s own insert is translated to the
   same teaching text via missive_dedup_race_text(), never a raw 23505. The courier-scope
   trigger makes a courier-actored call refuse at the FIRST insert already.
   kernel/lineage/s58-missive-substrate.sql.';

-- ============================================================================================
-- ELEMENT 7B -- kernel.ledger_write RE-ISSUED (base = s43's own head text, verified byte-
-- identical and unedited by s44-s57): the SAME generic single-row write boundary, with ONE
-- addition -- ADR-0021 Rule B's translation of a raced ELEMENT 3B unique-violation into the
-- SAME teaching text validate_missive_dedup's sequential-case EXISTS check would have produced
-- (ELEMENT 4B's missive_dedup_race_text(), called with THIS function's own surviving `payload`
-- argument, which for the missive_sent/missive_received write paths already carries
-- missive_author_world/missive_thread/missive_seq verbatim -- no reconstruction needed, unlike
-- kernel.missive_dispose's own translation, ELEMENT 7, whose payload carries no envelope
-- fields of its own). Every other kind's write is byte-identical to s43's own path --
-- missive_dedup_race_text() returns NULL for any constraint name it does not recognize, so a
-- non-missive 23505 (e.g. a future unrelated unique index) passes through with its raw message
-- exactly as before this re-issue.
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
               'refusal_attempted_role') THEN
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
   EXISTS check produces, via missive_dedup_race_text() -- every other SQLSTATE/kind is
   byte-identical to s43''s own path.
   kernel/lineage/s43-typed-verdict-write-boundary.sql; kernel/lineage/s58-missive-substrate.sql.';

-- ============================================================================================
-- ELEMENT 8a -- s42'S LAW SELF-APPLIED: compute_row_hash RE-ISSUED TO SERIALIZE 87 COLUMNS
-- TOTAL (the ten missive_* columns plus AMENDMENT 1's missive_regards appended in
-- serialization order, before the predecessor link; base body = s57's own text, verified
-- unedited; 87 is gates/hash_coverage_gate.py's own live-verified count, not hand-derived).
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
      -- s58: the ten missive_* columns, appended in serialization order
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
      -- AMENDMENT 1: missive_regards, the eleventh and last missive_* field serialized
      hashfield(r.missive_regards::text),
      hashfield(predecessor_hash)
    ], E'\x1f'),
  'utf8')), 'hex');
$fn$;

-- ============================================================================================
-- ELEMENT 8b -- the two column-complete views, +10 appended (the s20 lesson).
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
       l.missive_cites, l.missive_disposition, l.missive_regards
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
       l.missive_cites, l.missive_disposition, l.missive_regards
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);
-- ============================================================================================
