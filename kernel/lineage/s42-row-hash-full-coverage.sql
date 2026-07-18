-- s42 ROW-HASH FULL COVERAGE (design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md, the
-- RATIFIED build basis -- R1-R6 ratified ledger row 1460, 2026-07-18; §3 is this delta's own
-- section). Fable-built per the builder ruling (ledger row 1462: this family is built by Fable;
-- later families revert to the standing Sonnet-executes default). FIRST of the TWO-delta family
-- s42/s43 (spec §2: two deltas, git-revertible independently); s43 hard-depends on THIS delta.
--
-- This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/existing world is
-- the maintainer's act at a FUTURE world's birth (runs-are-strictly-linear ruling, 2026-07-11),
-- never taken here. An ADDITIVE delta applied ON TOP of the s15..s41 kernel (the established
-- remediation-delta idiom), NOT a retro-edit of a frozen sNN record (ADR-0005 Rule 8) and NOT a
-- second hand-copy of any existing mechanism (ADR-0012 P1: compute_row_hash keeps its ONE home
-- -- this file RE-ISSUES it, same name, same signature, same two callers, wider body).
--
-- PREREQUISITE: this delta REQUIRES s41 (kernel/lineage/s41-principal-bindings-and-relations
-- .sql) applied first: its serialization enumerates every ledger column at the s41 head, so on a
-- pre-s41 kernel the CREATE OR REPLACE FUNCTION below fails loudly at first execution --
-- actually at TRIGGER time, the first INSERT: `record "r" has no field
-- "principal_competence_basis"` -- and, decisively, the s42 witness harness applies it only on a
-- full s15..s41 chain. The requirement is POSITIONAL (this delta's place in the birth chain,
-- wired into bootstrap/new-project.sh's LINEAGE_CHAIN in this same commit), same posture as
-- s40's own PREREQUISITE note. (LANGUAGE sql function bodies here use string syntax, not
-- LANGUAGE-sql standard bodies, so the CREATE itself does not validate column references at
-- definition time -- named honestly rather than overclaimed.)
--
-- WHY (operator-side prose; NOT subject-visible -- only the catalog objects inside the opaque
-- db are): the witnessed hazard, ledger row 1449, quoted in substance by the spec §1.2:
-- compute_row_hash (s26) serializes only the s24-era column set. EVERY ledger column added
-- since s28 -- twenty-two of them, including all twelve s40/s41 principal columns -- is OUTSIDE
-- the tamper-evidence hash chain, so a schema-owner tamper of any of them (which principal a
-- revocation regards; a violation disposition's class; a work item's parent) changes NO hash
-- and `./verify-chain` reports INTACT over the rewrite. The class, in its most general form
-- (spec §1.2(a)): *a tamper-evidence serialization whose column enumeration is open at every
-- subsequent delta, silently* -- the exact enumeration-fails-open-at-the-next-instance failure
-- ADR-0011 Rule 4 names, paid thirteen times (s28..s41, each correctly leaving the serializer
-- alone under the not-class-ratifiable rule, no gate ever forcing the question). The fix is the
-- ratified R1/R2 pair: the chain covers THE FULL ROW minus `row_hash` (R1), by an ENUMERATED
-- serializer held complete forever by a repository coverage gate that goes red on any
-- column-set/serializer-set disagreement (R2; gates/hash_coverage_gate.py, shipped in this SAME
-- commit -- ADR-0011's 2026-07-02 amendment: the mechanism ships WITH the first fix).
--
-- THE SERIALIZATION, v2 (spec §3.1, ratified): every ledger column except `row_hash` itself
-- (it cannot include itself -- the one deliberate exclusion, named), in the ledger's catalog
-- ordinal order (verified live against a full s15..s41 scratch chain before authoring: 53
-- columns, row_hash at ordinal 31, so 52 serialized), each through the UNCHANGED s26
-- `hashfield()` length-prefixed presence-tagged token encoding (`N:` for SQL NULL,
-- `V<char-length>:<value>` for present -- the injectivity argument s26's own header carries
-- over verbatim: the encoding is self-delimiting, so no two different column-value tuples can
-- serialize to one string), joined with the same `\x1f` legibility separator, with
-- hashfield(predecessor_hash) as the final token. Per-type renderings, fixed by the spec so no
-- builder forks: bigint/boolean -> ::text; bigint[] (enacts) -> array_to_string(r.enacts, ',')
-- (s26 precedent, injective over bigint elements); every TIMESTAMPTZ column ->
-- extract(epoch FROM ...)::text (timezone-independent -- s26's own rule, now confirmed to
-- cover the whole timestamptz set); text -> as-is.
--
-- SPEC DIVERGENCE, SURFACED AT THE MOMENT OF DISCOVERY (ADR-0013's renegotiation-upward duty;
-- never silently narrowed, never maliciously complied with): the spec's §3.1 asserts that
-- `stamp_ts` is a timestamptz column whose s26 `::text` rendering was a latent
-- session-timezone hazard, and that this delta "fixes it by construction". THE PREMISE IS
-- FACTUALLY WRONG: `stamp_ts` has been BIGINT since its birth (kernel/lineage/
-- s17-stamp-mechanism.sql line "stamp_ts bigint" -- an epoch-seconds integer set by set_stamp
-- from the interception GUC), verified live against the catalog census above
-- (information_schema reports bigint). A bigint's ::text rendering is timezone-independent by
-- construction, so THERE NEVER WAS A stamp_ts TIMEZONE HAZARD and there is nothing for s42 to
-- fix on that column: it keeps the honest bigint `::text` rendering below (spec §3.1's OWN
-- per-type rule -- ::text for bigint -- applied to the column's TRUE catalog type; forcing
-- `extract(epoch FROM ...)` onto a bigint would be a type error). The spec's operational
-- guidance for verifying old worlds from a same-timezone session is therefore moot for
-- stamp_ts; the two REAL timestamptz columns (`ts`, `event_declared_ts`) were already
-- epoch-rendered by s26/s26's own rule and remain so here. The RATIFIED SUBSTANCE of §3.1 --
-- every timestamptz column is epoch-rendered, so the serialization is timezone-independent --
-- holds in full under this correction; only the spec's factual claim about stamp_ts's type
-- does not survive the field, and it is flagged in this delta's own build report to the
-- maintainer rather than absorbed.
--
-- RE-DENOMINATION CONSEQUENCE, stated honestly (spec §3.1, ratified analysis): every hash a v2
-- world computes differs from what a v1 world would compute on identical content. Under
-- runs-are-linear this costs NOTHING operationally: a serialization is world-scoped (each
-- world's chain is computed and verified by that world's own compute_row_hash, born with it;
-- no world ever mixes eras, because deltas never apply to live worlds), genesis seeds already
-- make chains world-unique, and GPG-signed heads are per-world artifacts. What it does mean:
-- cross-world hash comparison (which nothing does today) is meaningless across the s42
-- boundary, and the s26 `.accommodate.sql` machinery (a v1-era artifact for mid-history
-- migration of a v1 world) is NOT carried forward to v2 -- there is no v2 accommodation
-- artifact, because there is nothing to migrate: this change reaches only worlds BORN under
-- it. The frozen s26-row-hash-chain.accommodate.sql stays what it is, a v1-era record.
--
-- THE COVERAGE GATE (spec §3.2 -- the net that closes the class, ADR-0011 Rules 2/4, shipped
-- in this same commit): gates/hash_coverage_gate.py builds the standard scratch chain to the
-- lineage head on the toy db (the gates/ledger_reader_allowlist.py harness pattern), then
-- compares two sets: (i) `ledger`'s columns per information_schema.columns, minus `row_hash`;
-- (ii) the columns compute_row_hash serializes, derived FROM THE FUNCTION'S OWN SOURCE via
-- pg_get_functiondef (regex over `r.<name>` references) -- derived from the one home, never a
-- second hand-maintained manifest (ADR-0012 P1: a manifest would be the two-writers cancer the
-- gate exists to prevent). Set inequality in EITHER direction goes red, naming the missing/
-- extra columns and teaching the per-delta law: "a delta that adds a ledger column re-issues
-- compute_row_hash in the same delta." Negative control (a gate never seen red is a claim):
-- --inject-column applies a synthetic ADD COLUMN to the scratch and asserts red; seen-red
-- banked at seen-red/s42-row-hash-full-coverage/ and registered in gates/fixture_census.py.
-- The gate quantifies over the CLASS (any future column, any delta) -- the s28..s41 silence
-- cannot recur without a red gate in the offending commit.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form; this delta's slice -- the FAMILY
-- closure is the spec §5, s43 carries the write-boundary slice):
--   - INVARIANT: every ledger row's row_hash, in every world born under this delta, commits to
--     the value of EVERY column of that row except row_hash itself (52 columns at the s41
--     head), plus the predecessor's hash, through an injective (length-prefixed,
--     presence-tagged, self-delimiting) serialization computed by ONE function
--     (compute_row_hash) that both the insert trigger and ./verify-chain's walk call; and a
--     mechanical repository gate holds the serialized-column set equal to the table's column
--     set at every future delta, so the coverage cannot silently drift again.
--   - QUANTIFICATION UNIVERSE (enumerated; checked outward per ADR-0000's
--     presumption-of-narrowness):
--       * COLUMNS: all 52 non-row_hash columns at the s41 head, verified live by catalog
--         census (30 s24-era + 22 added by s28/s29/s30/s33/s36/s37/s40/s41 -- the spec §1.2
--         table, re-derived, matches). `row_hash` is the one deliberate exclusion, named. The
--         gate covers every FUTURE column.
--       * TIMESTAMPTZ AXIS: exactly two members at this head (ts, event_declared_ts), both
--         epoch-rendered; stamp_ts is bigint (see SPEC DIVERGENCE above), ::text-rendered,
--         timezone-independent either way. No other column's rendering is session-dependent
--         (text as-is; bigint/boolean ::text are locale/timezone-free in Postgres).
--       * CALLERS of compute_row_hash: exactly two -- the zz_set_row_hash trigger (s26,
--         UNTOUCHED here: its body calls compute_row_hash(NEW, pred), so it picks up the v2
--         body with zero edit) and bootstrap/templates/verify-chain.tmpl's walk (verified by
--         grep before building, per the spec's own instruction: that template contains NO
--         second serialization -- its module docstring's "NO CANONICALIZATION LOGIC LIVES
--         HERE" holds; the recomputation is this function, called in SQL).
--       * VIEWS: NONE re-issued -- this delta adds no column, so the s20 column-complete
--         obligation does not fire (named, not skipped; re-checked against s26's own
--         precedent, where the obligation fired because s26 ADDED row_hash).
--       * TRIGGERS: no trigger definition, ordering, or membership changes; hashfield, the
--         advisory lock, the genesis seed, and s27's high-water witness are all untouched.
--       * CONSTRAINTS/GRANTS: none touched.
--       * ENGINE: NONE (mirrors s23/s25/s26's own "ENGINE -- NONE" disclosure): row_hash has
--         no T_now derivation; the SQL/ASP differential derives from kind/status/supersedes,
--         none touched -- witnessed in AGREE on this delta's own fixture
--         (seen-red/s42-row-hash-full-coverage/), never asserted.
--       * GATES: gates/hash_coverage_gate.py is NEW in this commit;
--         gates/ledger_reader_allowlist.py and gates/kind_shape_manifest_gate.py gain s42 in
--         their CHAINs in this same commit (no new reader -- compute_row_hash reads no table,
--         it is a pure function of its row argument; no kind/column change), both witnessed
--         green on the extended chain.
--       * SIBLING TABLES (the outward check): review_detail, countersign_obligation,
--         kernel.principal, chain_high_water have NO hash chain of their own and never did --
--         this delta widens the LEDGER's chain only; sibling coverage is the spec's R3,
--         RATIFIED as deferred (a named follow-on family if wanted), not smuggled in.
--   - DENOMINATION: coverage is denominated in the serialized-column SET held equal to the
--     table's column set by a gate deriving both sides mechanically (catalog + function
--     source) -- never a hand-kept list, never a count; timestamps in epoch seconds (the
--     timezone-free instant); the hash in the same 64-hex-char SHA-256 text s26/s17 already
--     denominate in. No bound here is a bare literal.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT CLASS-RATIFIED
-- FAIL-SAFE, stated plainly (spec §2): this delta CHANGES WHAT row_hash MEANS -- a semantics
-- change to an existing mechanism, outside the only-adds class even though no refusal, grant,
-- or reader changes. It ships ONLY under the spec's own ratification (rows 1460/1462), routed
-- as the Fable-authored, maintainer-ratified spec the ORCHESTRATION contract requires.
--
-- LIMITS (pre-registered, s26's own disclosure convention inherited):
--   - The superuser/schema-owner bound stands (s26..s41's standing disclosure): the chain and
--     the gate bind below DDL privilege; the closing move for that adversary remains the
--     externally-held GPG-signed head (verify-chain --head), unchanged.
--   - The gate is repository-side (delta-authoring/acceptance time), not a kernel refusal: a
--     delta authored OUTSIDE this repository's gates could still forget the re-issue; within
--     this repository's discipline the gate is the net, and the per-delta law is stated in its
--     teach-text.
--   - Sibling tables stay chainless (R3, ratified deferral -- named above, not covered).
--   - SHA-256 preimage/collision resistance against chosen column CONTENT is the same bound
--     every SHA-256 use in this project carries, not a gap specific to this delta.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/../s41): schema/kern/role
-- are psql variables so this delta is VALIDATED on a throwaway substrate before any real apply.
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s42val -v kern=s42val_kernel -v role=s42val_rw \
--        -f high_watermark_1.sql -f s20-obligation-grants-and-view-refresh.sql \
--        -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--        -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--        -f s25-commission-kind.sql -f s26-row-hash-chain.sql -f s27-chain-high-water.sql \
--        -f s28-work-parent-edge.sql -f s29-obligation-item-key-and-typed-close.sql \
--        -f s30-typed-dependency-edges.sql -f s31-supersession-uniform-retraction.sql \
--        -f s32-edge-views-single-home.sql -f s33-composite-discharge.sql \
--        -f s34-computed-grade-refusal.sql -f s35-validation-decomposition.sql \
--        -f s36-decision-grade.sql -f s37-violation-disposition.sql \
--        -f s38-bookkeeping-close.sql -f s39-blocks-start.sql \
--        -f s40-principal-identity-events.sql -f s41-principal-bindings-and-relations.sql \
--        -f s42-row-hash-full-coverage.sql
--     (genesis seed per s26; the s40 birth acts per that delta's own VALIDATE note.)
--   REAL: NEVER applied to any existing world by this authoring act (maintainer ruling
--   2026-07-11, "runs are strictly linear"). This delta reaches reality by entering a FUTURE
--   world's birth chain via bootstrap/new-project.sh's LINEAGE_CHAIN, wired in this SAME
--   commit. On any birth chain the function is re-issued before the first ledger row exists,
--   so no row is ever hashed under two regimes. Authored and scratch-witnessed on scratch
--   schema pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE FUNCTION only).
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
-- compute_row_hash, v2 -- the ONE home of "what a row's content means" (ADR-0012 P1/P7),
-- re-issued to full-row coverage (every column except row_hash, catalog ordinal order,
-- predecessor last). Same name, same signature, same two callers (the zz_set_row_hash trigger
-- and ./verify-chain's walk), same hashfield() token encoding, same \x1f legibility separator.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".compute_row_hash(r :"schema".ledger, predecessor_hash text)
    RETURNS text LANGUAGE sql IMMUTABLE
    SET search_path = :"schema", pg_temp AS $fn$
  SELECT encode(sha256(convert_to(
    array_to_string(ARRAY[
      -- s15-era columns (ordinals 1..18)
      hashfield(r.id::text),
      hashfield(extract(epoch FROM r.ts)::text),               -- timestamptz -> epoch (TZ-safe)
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
      -- s17 stamp columns (19..23; stamp_ts is BIGINT epoch seconds since birth -- see the
      -- header's SPEC DIVERGENCE note: ::text on a bigint is timezone-independent already)
      hashfield(r.stamp_session),
      hashfield(r.stamp_agent),
      hashfield(r.stamp_ts::text),
      hashfield(r.stamp_hmac),
      hashfield(r.stamp_verified::text),
      -- s22 work columns (24..28)
      hashfield(r.work_slug),
      hashfield(r.work_title),
      hashfield(r.work_depends_on),
      hashfield(r.work_resolution),
      hashfield(r.work_witness),
      -- s23/s24 (29..30)
      hashfield(r.stamp_invocation),
      hashfield(extract(epoch FROM r.event_declared_ts)::text),  -- timestamptz -> epoch
      -- ordinal 31 is row_hash itself: the ONE deliberate exclusion (it cannot include itself)
      -- s28..s39 columns (32..41) -- the first ten of the twenty-two the v1 serialization left
      -- outside the chain (ledger row 1449; spec §1.2)
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
      -- s40 principal-identity columns (42..45)
      hashfield(r.principal_subject::text),
      hashfield(r.principal_purpose),
      hashfield(r.principal_db_role),
      hashfield(r.principal_actor_resolution),
      -- s41 binding/relation columns (46..53)
      hashfield(r.principal_binding_active::text),
      hashfield(r.principal_object::text),
      hashfield(r.principal_relation),
      hashfield(r.principal_role_name),
      hashfield(r.principal_key_fingerprint),
      hashfield(r.principal_competence_activity),
      hashfield(r.principal_competence_band),
      hashfield(r.principal_competence_basis),
      -- the chain link
      hashfield(predecessor_hash)
    ], E'\x1f'),
  'utf8')), 'hex');
$fn$;

COMMENT ON FUNCTION :"schema".compute_row_hash(:"schema".ledger, text) IS
  'v2 (kernel/lineage/s42-row-hash-full-coverage.sql): the canonical row serialization the
   tamper-evidence chain rests on -- EVERY ledger column except row_hash itself (52 at the s41
   head, catalog ordinal order), each through hashfield()''s injective length-prefixed token
   encoding, predecessor hash last, SHA-256 hex out. The ONE home of "what a row''s content
   means" (called by the zz_set_row_hash trigger and by ./verify-chain''s walk, and by nothing
   else). A delta that adds a ledger column RE-ISSUES this function in the same delta --
   enforced by gates/hash_coverage_gate.py, which derives the serialized set from this
   function''s own source and goes red on any disagreement with the catalog. v1 (s26) covered
   only the s24-era 30 columns; the 22 columns of s28..s41 were outside the chain (witnessed
   hazard, ledger row 1449) -- closed here, ratified spec
   design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md §3.';
