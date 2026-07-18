-- s43 TYPED-VERDICT WRITE BOUNDARY (design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md,
-- the RATIFIED build basis -- R1-R6 ratified ledger row 1460, 2026-07-18; §4 is this delta's
-- own section; the ratified direction is the maintainer's own "Ledger grade, of course",
-- row 1419). Fable-built per the builder ruling (row 1462). SECOND delta of the s42/s43
-- family. This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/existing
-- world is the maintainer's act at a FUTURE world's birth (runs-are-strictly-linear,
-- 2026-07-11). An ADDITIVE-plus-restructure delta on the s15..s42 kernel, NOT a retro-edit of
-- a frozen sNN record (ADR-0005 Rule 8) and NOT a second copy of any mechanism (ADR-0012 P1:
-- refusal journaling has ONE home, kernel.journal_write_refusal, called by all four boundary
-- functions; the serialization keeps its one home, re-issued here under s42's own law).
--
-- PREREQUISITE: this delta REQUIRES s42 (kernel/lineage/s42-row-hash-full-coverage.sql)
-- applied first -- a HARD dependency (spec §2): shipped without s42, every write_refused
-- row's distinguishing columns would sit outside the chain -- the ratified "ledger grade"
-- true of the row's prose and false of its typed content. Positionally enforced by the birth
-- chain (bootstrap/new-project.sh's LINEAGE_CHAIN, this same commit); gates/
-- hash_coverage_gate.py enforces the serializer half mechanically (red on an s43 chain whose
-- compute_row_hash was not re-issued to 58 columns -- the first live exercise of s42's own
-- per-delta law, witnessed both polarities in this delta's fixture).
--
-- WHY (operator-side prose; NOT subject-visible): the spec §1.1's class, in its most general
-- form: *a refusal whose only witness is destroyed by the refusal's own mechanism.* Every
-- kernel policy refusal is a RAISE EXCEPTION from a trigger; the exception aborts the
-- transaction; the transaction was the only place the attempt existed -- the ONE event class
-- the kernel systematically fails to record (NIST AU-2/AC-7-shaped denied-attempt logging,
-- named by the standards work, never forced by any mechanism). The foreclosing type is
-- ADR-0012 P9 rule 5 lifted into SQL: FAILURE IS A TYPED RETURN VALUE, NEVER A THROW. After
-- this delta: the granted role holds NO INSERT privilege on any kernel-governed table; four
-- SECURITY DEFINER jsonb-payload functions are the only write path; a refusal caught inside
-- them is committed as an ordinary `write_refused` ledger row (attributed to the
-- birth-registered `write-boundary` tool principal, carrying the attempted actor, the
-- SQLSTATE, the teach-text, and a digest of the refused payload) and returned to the caller
-- as a typed verdict -- never an abort. A refusal without a committed record becomes
-- unrepresentable for every write that reaches kernel semantics, because the boundary cannot
-- deliver a refusal verdict without having journaled it (single code path, §4.4). The two
-- refuted candidates (dblink autonomous transaction; CLI-side second connection) stay
-- retracted -- their history is preserved in the principal-identity build basis §9(e) and
-- judgment/engine/engine-panel/refute-architecture.md flaw 1, whose one standing demand -- a
-- SECOND WITNESS for the completeness claim -- is discharged here by the non-transactional
-- refusal-counter sequence (Element 5).
--
-- ELEMENT 1 -- THE VERDICT TYPE (spec §4.2, shape fixed): kernel.write_verdict
-- (disposition 'accepted'|'refused'; row_id; refusal_id; sqlstate; message). Created
-- idempotently (CREATE TYPE has no IF NOT EXISTS; a catalog-guarded DO block).
--
-- ELEMENT 2 -- THE write_refused KIND + SIX COLUMNS (spec §4.3): kind CHECK re-issued widened
-- (twenty-fourth member). Six nullable no-DEFAULT columns (the s30 lesson), kind-shape CHECKs
-- split from value CHECKs per the s40 house idiom (one concern per CHECK, for
-- gates/kind_shape_manifest_gate.py's classifier):
--   refusal_sqlstate text        -- mandatory (two-way); value CHECK ^[0-9A-Z]{5}$.
--   refusal_message text         -- mandatory (two-way); non-empty; the teach-text verbatim
--                                   (kernel-authored prose, bounded content -- never raw
--                                   payload).
--   refusal_surface text         -- mandatory (two-way); closed CHECK
--                                   IN ('ledger','review','registration','obligation') --
--                                   kernel-structural (it enumerates the boundary functions
--                                   themselves), so a closed CHECK is right where s41's
--                                   role-name column was ruled free text.
--   refusal_payload_digest text  -- mandatory (two-way); ^[0-9a-f]{64}$; SHA-256 of the
--                                   refused payload's canonical text (payload::text of the
--                                   jsonb argument -- key-sorted, deterministic on a given
--                                   server; the cross-version caveat is a named limit).
--                                   Digest, NEVER verbatim -- R4, RATIFIED (poison/privacy).
--   refusal_attempted_actor bigint REFERENCES kernel.principal(id) -- ONE-WAY (nullable on
--                                   the kind): the attempted principal when it resolved to a
--                                   registered id; NULL when unattributable.
--   refusal_attempted_role text  -- mandatory (two-way); non-empty; session_user at the
--                                   attempt (server-witnessed, never client-asserted).
-- Plus R6 (RATIFIED): write_refused rows are UNRETRACTABLE. Shipped as TWO mechanisms,
-- because the spec §4.3's literal CHECK text does not by itself deliver the ratified
-- substance -- a letter/spirit gap found in the field and SURFACED (ADR-0013; CLAUDE.md's
-- spirit-governs rule), see the inline note at the constraint below: the same-row CHECK
-- (write_refused_unretractable) keeps a refusal row from carrying a supersedes pointer, and
-- a NEW BEFORE INSERT trigger (validate_supersession_target) refuses any row whose
-- supersedes NAMES a write_refused row -- the actual retraction path, which a same-row CHECK
-- cannot see. A named, ratified divergence from s31's supersession uniformity: a refusal
-- event records a historical fact about an attempt; it asserts nothing retractable -- the
-- hiding is made unrepresentable, not merely traceable. The CHECK's idiom (a column
-- FORBIDDEN on one kind) is new to the kind-shape gate's classifier -- extended in this same
-- commit (FORBIDDEN_ON_KIND manifest), never silently unparseable.
--
-- ELEMENT 3 -- THE FOUR BOUNDARY FUNCTIONS (spec §4.2, shape fixed): all SECURITY DEFINER,
-- owned by the schema owner, SET search_path = :schema, :kern, pg_temp (the s19 discipline,
-- mandatory on SECURITY DEFINER), REVOKE ALL FROM PUBLIC, GRANT EXECUTE TO :role; all return
-- kernel.write_verdict; all run their real INSERTs inside BEGIN..EXCEPTION (a PL/pgSQL
-- exception block is an in-process subtransaction -- no connection, no extension, no slot:
-- the refuted candidates' failure modes structurally absent) and issue SET CONSTRAINTS ALL
-- IMMEDIATE at the end of the guarded block (EVERY function, not only registration's --
-- cheap, and forecloses the whole future class of deferred-trigger refusals escaping the
-- handler; quantify over the class):
--   kernel.ledger_write(payload jsonb)       -- the generic single-row path. Payload keys
--     are ledger column names; values cast via jsonb_populate_record(NULL::ledger, payload)
--     field access (per-type casting DERIVED from the rowtype -- P1, no hand cast table);
--     absent keys fall to column defaults (id, ts, session). Validation BEFORE any INSERT,
--     refused loudly as a verdict: (i) any key not a ledger column; (ii) any SERVER-OWNED
--     key: id, ts, row_hash, stamp_session, stamp_agent, stamp_ts, stamp_hmac,
--     stamp_verified, stamp_invocation, principal_actor_resolution (trigger-computed -- a
--     writer-supplied value would be a lying channel), every refusal_* column, and
--     kind = 'write_refused' (only the handler mints refusal rows -- the forgery channel
--     closed at the same trust boundary that does the journaling; the oracle's
--     count>sequence FAIL is the tripwire behind it). Declared event time rides
--     event_declared_ts per s24; ts is server time, never client-supplied.
--   kernel.review_write(payload jsonb)       -- the review ceremony: the kind='review'
--     ledger row and its review_detail row in ONE guarded block (keys: regards, statement,
--     verdict, independence, basis, antecedent, actor). A refusal from EITHER insert --
--     including validate_independence's D-6 human-only refusal and s34's grade refusal,
--     which fire on review_detail and would otherwise stay outside the recorded surface --
--     journals as one write_refused row, surface 'review', and rolls the whole ceremony.
--   kernel.registration_write(payload jsonb) -- the registration ceremony: the
--     kernel.principal anchor INSERT and its principal_registered ledger event, followed
--     INSIDE the guarded block by SET CONSTRAINTS ALL IMMEDIATE, so s40's deferred
--     anchor-coupling trigger fires within the handler's scope and a commit-time refusal is
--     caught and journaled like any other (the consultation's named obligation, discharged).
--     A duplicate name now leaves a durable trace even when attempted raw through the
--     function -- the panel's silent-duplicate class gains its record. Keys: name,
--     agent_class, purpose, actor, event_declared_ts.
--   kernel.obligation_write(payload jsonb)   -- the countersign_obligation INSERT (keys:
--     scope, assigned_by, obliges_actor -- principal ids, the table's own columns).
--     Uniformity is the argument: no granted-role DML except through a verdict-returning
--     function, no config-table carve-out that would re-open the class. row_id is NULL on
--     accept (the table has no bigint id -- scope is its PK; an executor-documented shape,
--     the verdict type is the spec's fixed one).
--   ACTOR VALUES are the ledger's own bigint principal ids (payload keys are column names);
--   a NULL/absent actor resolves through set_actor's standing declaration exactly as today.
--
-- ELEMENT 4 -- HANDLER SEMANTICS (spec §4.4, fixed): the trigger chain the guarded INSERT
-- runs is byte-for-byte today's chain -- refusals are caught GENERICALLY by SQLSTATE class,
-- never by enumerating refusal sites; no trigger is modified to cooperate. Journaled
-- classes: 22___ (data exception -- malformed payload values), 23___ (integrity constraint),
-- P0___ (raise_exception -- every taught policy refusal). Everything else -- serialization
-- (40), resource (53), operator (57), internal (XX), and any class not enumerated -- is
-- RE-RAISED UNJOURNALED: an infrastructure failure is not a denied attempt, and conflating
-- them would poison the refusal record's meaning; the polarity is fail-safe (escaped = loud
-- abort, never silent acceptance). On a journaled class the handler: bumps
-- nextval(kernel.refusal_seq) (the oracle, BEFORE the journal INSERT -- non-transactional,
-- survives everything); INSERTs the write_refused row (explicit VALUES; actor = the
-- write-boundary principal); RETURNs the ('refused', NULL, id, sqlstate, message) verdict;
-- the enclosing transaction commits carrying the refusal event and nothing else. If the
-- journal INSERT itself fails, the exception propagates: loud abort (today's behavior
-- exactly), a counted sequence gap the reconciliation names, the server log as residual
-- coverage -- fail-safe on both legs. The s26 advisory lock, the burned id on the
-- rolled-back INSERT, and the predecessor-hash lookup all behave correctly under the
-- subtransaction (the rolled-back row is invisible to the journal INSERT's predecessor
-- SELECT; the advisory xact lock is same-transaction reentrant).
--
-- ELEMENT 5 -- THE COMPLETENESS ORACLE, kernel.refusal_seq (spec §4.6; flaw 1's standing
-- demand discharged with the consultation's candidate F): a dedicated sequence, bumped by
-- the journaler immediately before each journal INSERT. nextval is non-transactional by
-- design -- no rollback erases it. Reconciliation leg added to ./verify-chain
-- (bootstrap/templates/verify-chain.tmpl, this same commit, beside s27's high-water report):
-- count(*) WHERE kind='write_refused' vs the sequence. Semantics, fixed: count > sequence =>
-- FAIL (rows the handler never counted: forged/replayed refusal rows -- the §4.2 forgery
-- tripwire); sequence > count => EXPLAIN, not fail (legitimate causes named in the output:
-- a journal-INSERT double failure; a raw caller wrapping the function in a transaction it
-- then rolled back). GRANT POSTURE (a spec-internal tension resolved on its own terms,
-- surfaced not silently absorbed): the spec's §4.6 letter says :role gets "no grant on the
-- sequence", mirroring s27 -- but s27's actual posture is SELECT-only (the subject may READ
-- the witness, never write it), and the spec's own reconciliation runs through
-- ./verify-chain, which connects AS the subject role; an unreadable oracle would make the
-- ratified reconciliation impossible. Resolution, the spirit both texts share: GRANT SELECT
-- (read last_value/is_called) and NOTHING else -- no USAGE, no UPDATE, so the subject cannot
-- nextval or setval the witness. Witnessed both polarities in this delta's fixture.
--
-- ELEMENT 6 -- THE write-boundary PRINCIPAL (spec §4.5): the refusal row's actor cannot be
-- the attempted principal (the attempt may be refused precisely because that principal is
-- revoked, unresolvable, or nonexistent -- attribution would either lie or recurse into a
-- second refusal). The enforcement point authors the audit record: the scaffold's birth
-- sequence (bootstrap/new-project.sh, this same commit) registers principal `write-boundary`
-- (agent_class 'tool', an existing s13 vocabulary member) through the full ceremony, purpose
-- text fixed by the spec. The journaler resolves it by name once per call; a scratch world
-- that skipped the birth step gets a loud abort on its first refusal (fail-safe, named). CLI
-- guard (bootstrap/templates/led.tmpl, same commit): `led principal suspend|revoke
-- write-boundary` is refused at the CLI with teach-text (suspending the recorder bricks
-- refusal recording -- the kernel-side dead-end analog of s40's C7, CLI-grade only,
-- disclosed).
--
-- ELEMENT 7 -- THE PRIVILEGE CHANGE IS TOTAL (spec §4.1): REVOKE INSERT on ledger,
-- review_detail, kernel.principal, and countersign_obligation from :role (and from PUBLIC,
-- belt-and-braces); GRANT EXECUTE on the four functions. After s43 a raw INSERT from the
-- granted role fails at the privilege layer (SQLSTATE 42501) before any semantics run -- the
-- bypass path does not exist; THAT refusal class's residual home is the server log (named
-- composition, not a gap). SELECT grants unchanged. s18-CLASS ARMING ENUMERATION (extends
-- s40/s41's; s18 itself is not in the birth chain -- this lives here for its arming script):
-- REVOKE INSERT ON ledger, review_detail FROM rev1, rev2; GRANT EXECUTE ON
-- kernel.ledger_write(jsonb), kernel.review_write(jsonb) TO rev1, rev2; declare standing for
-- their login roles (they authenticate as distinct logins, so §4.7's implicit attribution
-- keeps full per-reviewer distinction). The finding-45 column grants (s18's 2b) remain
-- correct but become vestigial for boundary writes -- see Element 8.
--
-- ELEMENT 8 -- ACTOR RESOLUTION UNDER SECURITY DEFINER: set_actor RE-ISSUED ON session_user
-- (spec §4.7, fixed). Inside a SECURITY DEFINER function current_user is the function owner
-- -- s40's set_actor would resolve every boundary write to the owner's login and
-- misattribute everything. Re-issued here: the s40 body (the lineage head's declaration, per
-- the migrate-detect-drift discipline) with EXACTLY ONE change -- the standing declaration
-- resolves against SESSION_USER (the authenticated login role: server-witnessed, unaffected
-- by SET ROLE and by SECURITY DEFINER). Consequences, fixed: the scaffold's birth
-- declaration now declares standing for the LOGIN role the world's DSN authenticates as
-- (witnessed at scaffold time as session_user), IN ADDITION TO the constrained :role (kept:
-- harmless, one extra declaration event, and the record stays correct about both
-- identities); behavior on a direct connection (no SET ROLE, no SECDEF) is identical
-- (session_user = current_user there), so the re-issue is behavior-preserving for every
-- pre-s43 path -- and the boundary is the only write path left. NAMED LIMIT: a deployment
-- multiplexing several principals over ONE login via SET ROLE loses implicit per-role
-- attribution (all resolve to the login's declaration); the explicit actor channel remains
-- the correct tool there; no current deployment shape does this. STRUCTURAL BONUS, named
-- because it retires a hazard class: the boundary functions run the trigger chain as the
-- owner, so the finding-45 class (zero-SELECT writers refused inside SECURITY INVOKER
-- trigger reads -- s18's 2b, s40's per-object foreclosures) is dissolved wholesale for every
-- boundary write; the s40 per-object mechanisms stay (harmless, still covering any
-- owner-side direct path).
--
-- ELEMENT 9 -- s42'S LAW, SELF-APPLIED: this delta adds six columns, so THIS delta re-issues
-- compute_row_hash to 58 columns (the six appended in catalog ordinal order, all text/bigint
-- renderings per s42's fixed rules) -- the first, immediate, both-polarities exercise of
-- gates/hash_coverage_gate.py's per-delta law (witnessed: the gate red on an
-- s43-columns-without-re-issue scratch, green on this head). ledger_current and
-- countersigned_in_force re-issued +6, appended at the end (the s20 lesson; non-member views
-- re-verified per the s38 discipline -- none of work_item_current, work_item_violations,
-- work_violation_history, work_review_gap, review_gap, question_status,
-- review_stamp_distinctness, work_edge_*, work_startable, work_bookkeeping_closes,
-- standing_decisions, principal_standing_current, principal_relations,
-- principal_role_bindings, principal_keys, principal_competences does general column
-- passthrough; none is re-issued).
--
-- HISTORY: safe -- per-mechanism grounds (spec §4.9): additive kind vocabulary; six nullable
-- no-default columns whose CHECKs validate vacuously on pre-existing rows (the kind is born
-- here); set_actor re-issued with a resolution-source change that is behavior-identical on
-- every connection shape that exists pre-s43 plus no other edit; REVOKEs are pure narrowing
-- (nothing that succeeded before succeeds differently -- it is refused at the privilege
-- layer, the fail-safe polarity; and no pre-s43 world ever runs this delta -- "before"
-- exists only on scratch); the four functions, the verdict type, the journaler, the
-- sequence, and the scaffold's principal-registration step are new objects with no
-- pre-existing reader; the serializer re-issue is s42's law applied. The one genuinely
-- non-additive act -- the write-path restructure itself -- is the ratified point, and is why
-- this family routes as a Fable-authored maintainer-ratified spec.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form; this delta's slice -- the FAMILY
-- closure is the spec §5, checked there in full):
--   - INVARIANT: every row the ledger accepts, and every refusal the kernel issues through
--     its sanctioned write surface, is a committed, attributed, stamped, hash-chained ledger
--     row; no granted role holds a write privilege on any kernel-governed table -- the only
--     write path is a function family whose return type carries acceptance and refusal as
--     values, so a refusal without a committed record is unrepresentable for every write
--     that reaches kernel semantics; and the count of journaled refusals is reconciled
--     against a rollback-proof counter, so the completeness of the refusal record is a
--     checkable claim, not an article of trust.
--   - QUANTIFICATION UNIVERSE (the spec §5's, this delta's slice):
--       WRITE SURFACES, disposed one by one: ledger generic path -- covered (ledger_write);
--         review ceremony incl. review_detail's own refusal triggers -- covered
--         (review_write); registration ceremony incl. the COMMIT-time deferred trigger --
--         covered (registration_write + SET CONSTRAINTS ALL IMMEDIATE); obligation config
--         INSERT -- covered (obligation_write); raw INSERT by a granted role -- FORECLOSED
--         at the privilege layer, its refusal NOT kernel-journaled (residual home: the
--         server log -- named); owner/superuser direct DML -- named not covered (the
--         standing s26..s42 trust bound); countersign_obligation DELETE (obligate revoke) --
--         owner-side escalation path, unchanged, named; nla-schema worlds -- no kernel, out
--         of scope, named.
--       REFUSAL CLASSES: SQLSTATE 22/23/P0 journaled; 40/53/57/XX and unenumerated classes
--         re-raised unjournaled -- named as not covered by the journal, DELIBERATELY
--         (infrastructure failure /= denied attempt), fail-safe polarity stated. The honest
--         fail-open edge: a novel POLICY refusal mechanism minted outside these classes by a
--         future delta would escape journaling -- but every kernel refusal mechanism is
--         RAISE EXCEPTION or a constraint by construction, a new mechanism class needs its
--         own spec, and the polarity is loud-abort, never silent acceptance.
--       KINDS/COLUMNS: write_refused licenses exactly the six refusal_* columns (five
--         two-way, one one-way -- the attempted-actor's legitimate NULL); no other kind may
--         carry them; supersedes is FORBIDDEN on this one kind (R6). The kind-shape gate's
--         manifest gains all six rows plus the new FORBIDDEN_ON_KIND idiom, this commit.
--       VIEWS: the two column-complete homes re-issued (+6); non-members re-verified
--         (Element 9). TRIGGERS: ONE new BEFORE INSERT member on ledger
--         (validate_supersession_target -- R6's substance; reads only NEW plus a
--         row-addressed target-kind lookup, so its position among the validators is
--         immaterial, and 'validate_supersession_target' still sorts before
--         'validate_work_item' and 'zz_set_row_hash', preserving the s26 last-fires
--         mechanism); set_actor re-issued in place (position unchanged: still first
--         alphabetically).
--       ENGINE: entry/6 is kind-generic (verified at s40, unchanged); write_refused flows
--         through; ./judge witnessed in AGREE on a fixture carrying it, never asserted; no
--         new .lp predicate. HASH CHAIN: compute_row_hash re-issued to 58 columns here,
--         under s42's law, gate-witnessed. GATES: hash-coverage (green on this head, red on
--         the no-re-issue scratch), kind-shape manifest (+6 rows, +1 idiom), reader
--         allowlist (CHAIN += s43; the boundary functions live in :kern, OUTSIDE that gate's
--         declared :schema universe -- named per its own standing scope note; each reads raw
--         ledger only through the journaler's INSERT and the s31 discipline is honored by
--         construction), fixture census -- all bumped this commit. CLI: every led.tmpl write
--         site migrated (the shared kernel_write helper is the single home; pre-s43 worlds
--         keep their legacy branches byte-identical -- the live-verbs doctrine); the
--         verify-chain reconciliation leg added.
--   - DENOMINATION: refusal completeness in a non-transactional counter reconciled against
--     committed rows -- never the journal's own self-report (the flaw-1 lesson); the payload
--     digest in the same SHA-256 the chain uses; refusal classes in SQLSTATE classes (the
--     engine's own currency for failure), never message-text matching; attribution in
--     session_user (server-witnessed) and registered principal ids, never names or client
--     assertions. No bound is a bare round literal.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT CLASS-RATIFIED
-- FAIL-SAFE, stated plainly (spec §2): this delta revokes privileges, re-issues set_actor,
-- and restructures every write path. It ships ONLY under the family's ratification
-- (rows 1419/1460/1462).
--
-- LIMITS (pre-registered; the spec §8 in full, this delta's slice):
--   - The superuser/schema-owner bound stands; the closing move remains the signed head.
--   - Privilege-layer refusals (42501) are not kernel-journaled -- server-log residual,
--     diagnostics-grade, subject to rotation. Named composition, not a later-found gap.
--   - The forgery-channel closure for write_refused lives at the boundary functions
--     themselves (payload validation), the same trust boundary as the journaling; the
--     oracle's count>sequence FAIL is the tripwire behind it.
--   - The oracle is one-directional: sequence > count has legitimate causes (client-side
--     rollback around the function; journal double failure) and is EXPLAIN-grade; only
--     count > sequence is FAIL-grade. A raw caller who wraps the function in a transaction
--     and rolls back discards the refusal row (the sequence still counts it); the CLI never
--     wraps.
--   - Suspending/revoking the write-boundary principal bricks refusal recording -- guarded
--     at the CLI only (owner-side repair, the C7 posture, disclosed).
--   - session_user attribution assumes one principal per login role (Element 8's named
--     limit).
--   - jsonb canonical-text digest is deterministic on a given server; a Postgres
--     major-version change could render differently -- which would not break the chain (the
--     digest is content, hashed at write time) but would break RECOMPUTING a digest from a
--     re-supplied payload on a different server. Diagnostic linkage, not a verification
--     path -- stated so nobody builds one on it.
--   - Refused-payload content is not reconstructable from the ledger (digest-only, R4);
--     forensic recovery needs the server log within its retention window. Deliberate.
--   - The refusal journal records what reached kernel semantics; auth-layer failures are
--     below even the privilege layer -- pg_hba/host territory, out of scope by the standing
--     no-perimeter ruling.
--   - In a solo world the whole refusal record is written by machinery the one operator
--     controls -- complete and attributed, not adversarially independent (s17's honesty).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/../s42):
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s43val -v kern=s43val_kernel -v role=s43val_rw \
--        -f high_watermark_1.sql -f s20-obligation-grants-and-view-refresh.sql \
--        ... (s21..s41 as in s42's own VALIDATE list) ... \
--        -f s42-row-hash-full-coverage.sql -f s43-typed-verdict-write-boundary.sql
--     (genesis seed per s26; the s40 birth acts through the BOUNDARY functions -- the
--     scaffold's scripted form in bootstrap/new-project.sh is authoritative; register the
--     write-boundary principal before exercising any refusal path, or the journaler aborts
--     loudly by design.)
--   REAL: NEVER applied to any existing world by this authoring act. Enters a FUTURE world's
--   birth chain via bootstrap/new-project.sh's LINEAGE_CHAIN, wired in this SAME commit.
--   Authored and scratch-witnessed on scratch schema pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (guarded CREATE TYPE; CREATE SEQUENCE IF NOT
-- EXISTS; DROP+ADD CONSTRAINT; ADD COLUMN IF NOT EXISTS; CREATE OR REPLACE FUNCTION/VIEW;
-- REVOKE/GRANT are idempotent).
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
-- ELEMENT 1 -- THE VERDICT TYPE (idempotent: CREATE TYPE has no IF NOT EXISTS).
-- ============================================================================================
SELECT set_config('s43.kern', :'kern', false);
DO $$
DECLARE k text := current_setting('s43.kern');
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace
                 WHERE n.nspname = k AND t.typname = 'write_verdict') THEN
    EXECUTE format(
      'CREATE TYPE %I.write_verdict AS (
         disposition text,     -- ''accepted'' | ''refused''  (the two-member closed vocabulary)
         row_id      bigint,   -- the accepted row''s ledger id (NULL when refused; NULL for
                               -- obligation_write, whose table has no bigint id)
         refusal_id  bigint,   -- the committed write_refused row''s id (NULL when accepted)
         sqlstate    text,     -- the refusal''s SQLSTATE (NULL when accepted)
         message     text      -- the refusal''s teach-text, verbatim (NULL when accepted)
       )', k);
  END IF;
END $$;

-- ============================================================================================
-- ELEMENT 5 (created early: the journaler below references it) -- THE COMPLETENESS ORACLE.
-- SELECT-only to :role (read the witness, never advance/reset it -- s27's posture; see the
-- header's Element 5 for the spec-letter tension this resolves and surfaces).
-- ============================================================================================
CREATE SEQUENCE IF NOT EXISTS :"kern".refusal_seq;
REVOKE ALL ON SEQUENCE :"kern".refusal_seq FROM PUBLIC;
GRANT SELECT ON SEQUENCE :"kern".refusal_seq TO :"role";

COMMENT ON SEQUENCE :"kern".refusal_seq IS
  'The refusal-record completeness oracle (kernel/lineage/s43-typed-verdict-write-boundary.sql
   Element 5; refute-architecture flaw 1''s second-witness demand): bumped by the write
   boundary''s journaler immediately BEFORE each write_refused INSERT. nextval is
   non-transactional -- no rollback erases a bump -- so ./verify-chain can reconcile
   count(write_refused rows) against this counter: count > sequence FAILS (forged/replayed
   refusal rows); sequence > count EXPLAINS (journal double-failure, or a raw caller''s
   client-side rollback around the function). :role holds SELECT only -- it can read the
   witness, never advance or reset it (the s27 chain_high_water grant posture).';

-- ============================================================================================
-- ELEMENT 2 -- KIND VOCABULARY WIDENED (twenty-fourth member) + THE SIX REFUSAL COLUMNS.
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
     'write_refused'));

COMMENT ON CONSTRAINT ledger_kind_check ON :"schema".ledger IS
  'kernel/lineage/s43-typed-verdict-write-boundary.sql: widens s41''s twenty-three-member
   vocabulary by write_refused -- a refusal the write boundary caught, committed as an
   ordinary ledger row (the one event class the kernel used to destroy by the refusal''s own
   abort). Minted ONLY by the boundary functions'' journaler; a payload supplying it is
   refused at the boundary (the forgery channel), and a write_refused row is unretractable
   (R6, write_refused_unretractable).';

ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS refusal_sqlstate text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS refusal_message text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS refusal_surface text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS refusal_payload_digest text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS refusal_attempted_actor bigint
    REFERENCES :"kern".principal(id);
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS refusal_attempted_role text;

COMMENT ON COLUMN :"schema".ledger.refusal_sqlstate IS
  'The refused attempt''s SQLSTATE (the engine''s own failure currency -- 22*/23*/P0* are the
   journaled classes; infrastructure classes re-raise unjournaled). Mandatory on
   write_refused, forbidden elsewhere. kernel/lineage/s43-typed-verdict-write-boundary.sql.';
COMMENT ON COLUMN :"schema".ledger.refusal_message IS
  'The refusal''s teach-text, verbatim -- kernel-authored prose (bounded content; the refused
   payload itself is NEVER stored, only its digest -- R4). Mandatory non-empty on
   write_refused. kernel/lineage/s43-typed-verdict-write-boundary.sql.';
COMMENT ON COLUMN :"schema".ledger.refusal_surface IS
  'WHICH boundary function caught the refusal: ledger | review | registration | obligation
   (closed CHECK -- kernel-structural: it enumerates the boundary functions themselves).
   kernel/lineage/s43-typed-verdict-write-boundary.sql.';
COMMENT ON COLUMN :"schema".ledger.refusal_payload_digest IS
  'SHA-256 (hex) of the refused payload''s canonical text (payload::text of the jsonb
   argument -- key-sorted, deterministic on a given server; a cross-major-version recompute
   is a named limit, diagnostic linkage only). Digest, never verbatim (R4, ratified:
   adversary-authored content gets no permanent hash-chained storage channel).
   kernel/lineage/s43-typed-verdict-write-boundary.sql.';
COMMENT ON COLUMN :"schema".ledger.refusal_attempted_actor IS
  'The ATTEMPTED principal, when it resolved to a registered id (an explicit payload actor,
   or the session''s standing-declaration default that then failed a check); NULL when the
   attempt was unattributable -- exactly the case whose ROLE is still always known
   (refusal_attempted_role). The refusal row''s own actor is the write-boundary tool
   principal (the enforcement point authors the audit record); this column carries who was
   REFUSED. kernel/lineage/s43-typed-verdict-write-boundary.sql.';
COMMENT ON COLUMN :"schema".ledger.refusal_attempted_role IS
  'session_user at the attempt (the authenticated login role -- server-witnessed, never
   client-asserted; unaffected by SET ROLE and SECURITY DEFINER). Mandatory non-empty on
   write_refused. kernel/lineage/s43-typed-verdict-write-boundary.sql.';

-- kind-shape CHECKs (one concern per CHECK -- the s40 idiom; two-way where mandatory,
-- one-way for the legitimately-NULL attempted actor):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_sqlstate_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_sqlstate_kind_shape CHECK (
    (kind = 'write_refused') = (refusal_sqlstate IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_message_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_message_kind_shape CHECK (
    (kind = 'write_refused') = (refusal_message IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_surface_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_surface_kind_shape CHECK (
    (kind = 'write_refused') = (refusal_surface IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_payload_digest_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_payload_digest_kind_shape CHECK (
    (kind = 'write_refused') = (refusal_payload_digest IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_attempted_actor_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_attempted_actor_kind_shape CHECK (
    refusal_attempted_actor IS NULL OR kind = 'write_refused');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_attempted_role_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_attempted_role_kind_shape CHECK (
    (kind = 'write_refused') = (refusal_attempted_role IS NOT NULL));

-- value CHECKs (no kind test -- out of the kind-shape manifest's scope by its classifier):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_sqlstate_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_sqlstate_shape CHECK (
    refusal_sqlstate IS NULL OR refusal_sqlstate ~ '^[0-9A-Z]{5}$');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_message_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_message_nonempty CHECK (
    refusal_message IS NULL OR btrim(refusal_message) <> '');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_surface_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_surface_check CHECK (
    refusal_surface IS NULL
    OR refusal_surface IN ('ledger','review','registration','obligation'));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_payload_digest_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_payload_digest_shape CHECK (
    refusal_payload_digest IS NULL OR refusal_payload_digest ~ '^[0-9a-f]{64}$');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_attempted_role_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_attempted_role_nonempty CHECK (
    refusal_attempted_role IS NULL OR btrim(refusal_attempted_role) <> '');

-- R6 (RATIFIED): write_refused rows are UNRETRACTABLE -- "supersession refused on them"
-- (§9 R6's own words). TWO mechanisms, because the spec's §4.3 literal CHECK
-- (`kind <> 'write_refused' OR supersedes IS NULL`) does not by itself deliver the ratified
-- substance -- A LETTER/SPIRIT GAP FOUND IN THE FIELD AND SURFACED, per ADR-0013 and
-- CLAUDE.md's spirit-governs rule, never silently absorbed: that same-row CHECK only stops a
-- write_refused row from CARRYING a supersedes pointer (which the journaler never sets
-- anyway); what actually drops a refusal row from ledger_current is a LATER row whose
-- supersedes NAMES it, and a same-row CHECK cannot see the target's kind (a cross-row
-- lookup). So:
--   (a) the literal CHECK ships (harmless, true by construction, and it keeps the journal's
--       own shape honest: a refusal row asserts nothing and retracts nothing);
--   (b) the ratified substance ships as a BEFORE INSERT trigger,
--       validate_supersession_target: a row whose supersedes names a write_refused row is
--       refused at construction, with teach-text -- the hiding made unrepresentable, not
--       merely traceable (R6's recommendation-over-alternative, verbatim). Row-addressed
--       raw-ledger read (the target's kind), same history-typed posture as validate_review;
--       gates/ledger_reader_allowlist.py gains its entry in this same commit. Witnessed both
--       polarities in this delta's fixture -- and a boundary-carried attempt to supersede a
--       refusal row is itself journaled (the refusal of the hide attempt becomes a record).
-- The CHECK's idiom (a core column forbidden on one kind) is new to the kind-shape gate's
-- classifier -- extended in this same commit (FORBIDDEN_ON_KIND manifest), never silently
-- unparseable.
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS write_refused_unretractable;
ALTER TABLE :"schema".ledger ADD CONSTRAINT write_refused_unretractable CHECK (
    supersedes IS NULL OR kind <> 'write_refused');

CREATE OR REPLACE FUNCTION :"schema".validate_supersession_target() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_target_kind text;
BEGIN
  IF NEW.supersedes IS NOT NULL THEN
    SELECT l.kind INTO v_target_kind FROM ledger l WHERE l.id = NEW.supersedes;
    IF v_target_kind = 'write_refused' THEN
      RAISE EXCEPTION 'Ledger policy: a write_refused row is UNRETRACTABLE (s43, ratified R6) — row % records a historical fact about a refused attempt; it asserts nothing retractable, and superseding it is the one path by which a later writer could make a refusal vanish from every current view. The record stands; if the refusal was wrong, the corrected write simply succeeds beside it (kernel/lineage/s43-typed-verdict-write-boundary.sql Element 2).', NEW.supersedes;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_supersession_target ON :"schema".ledger;
CREATE TRIGGER validate_supersession_target BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_supersession_target();

-- ============================================================================================
-- ELEMENT 9a -- s42's LAW SELF-APPLIED: compute_row_hash re-issued to 58 columns (the six
-- refusal columns appended in catalog ordinal order, before the predecessor link; every
-- other rendering byte-identical to s42's).
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
      -- s43: the six refusal columns (catalog ordinals 54..59)
      hashfield(r.refusal_sqlstate),
      hashfield(r.refusal_message),
      hashfield(r.refusal_surface),
      hashfield(r.refusal_payload_digest),
      hashfield(r.refusal_attempted_actor::text),
      hashfield(r.refusal_attempted_role),
      hashfield(predecessor_hash)
    ], E'\x1f'),
  'utf8')), 'hex');
$fn$;

-- ============================================================================================
-- ELEMENT 9b -- the two column-complete views, +6 appended (the s20 lesson).
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
       l.refusal_payload_digest, l.refusal_attempted_actor, l.refusal_attempted_role
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
       l.refusal_payload_digest, l.refusal_attempted_actor, l.refusal_attempted_role
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- ELEMENT 8 -- set_actor RE-ISSUED ON session_user (the s40 body, ONE change: the standing
-- declaration resolves against session_user, never current_user -- inside SECURITY DEFINER
-- current_user is the function OWNER and would misattribute every boundary write). Trigger
-- name/timing/position unchanged (still first alphabetically in the BEFORE INSERT chain).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".set_actor() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_standing text;
BEGIN
  IF NEW.actor IS NULL THEN
    -- s43: session_user, NOT current_user -- the authenticated LOGIN role (server-witnessed,
    -- unaffected by SET ROLE and by SECURITY DEFINER). On a direct connection the two are
    -- equal, so every pre-s43 path is behavior-identical; inside the s43 boundary functions
    -- only session_user attributes honestly. The scaffold declares standing for BOTH the
    -- login role and the granted :role at birth (kernel/lineage/
    -- s43-typed-verdict-write-boundary.sql Element 8).
    SELECT principal_id INTO NEW.actor FROM principal_role WHERE db_role = session_user;
    IF NEW.actor IS NULL THEN
      RAISE EXCEPTION 'Ledger policy: strict attribution (s40) — this write supplied no actor and login role ''%'' has no standing declaration, so the kernel cannot attribute it. Declare this role''s standing principal once, as an explicit recorded act: ./led principal declare-standing <principal-name> --db-role % (writes a principal_standing_declared event — the declared-not-silent default; kernel/lineage/s40-principal-identity-events.sql §3.6, resolution on session_user since kernel/lineage/s43-typed-verdict-write-boundary.sql). Alternatively, supply an explicit actor for this one write (LED_ACTOR=<registered-principal-name>).', session_user, session_user;
    END IF;
    NEW.principal_actor_resolution := 'declared-default';
  ELSE
    NEW.principal_actor_resolution := 'explicit';
  END IF;
  v_standing := principal_standing(NEW.actor);
  IF v_standing IN ('revoked', 'suspended') THEN
    RAISE EXCEPTION 'Ledger policy: strict attribution (s40) — actor principal % is % (standing event row %); a % principal accepts no further writes, and no v1 verb lifts this standing. The sanctioned path forward is a FRESH successor principal: ./led register-principal <new-name> <class> --purpose "<why>", then record the succession (kernel/lineage/s40-principal-identity-events.sql, Element 4 / REINSTATEMENT).', NEW.actor, v_standing, principal_standing_basis(NEW.actor), v_standing;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS set_actor ON :"schema".ledger;
CREATE TRIGGER set_actor BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".set_actor();

-- ============================================================================================
-- ELEMENT 4 -- THE JOURNALER, kernel.journal_write_refusal: the ONE home of "a refusal
-- becomes a committed row" (ADR-0012 P1), called by all four boundary functions and by
-- NOTHING else (owner-internal: EXECUTE revoked from PUBLIC, granted to no role -- only the
-- SECURITY DEFINER boundary functions, running as the owner, can call it).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"kern".journal_write_refusal(
    p_surface text, p_payload jsonb, p_sqlstate text, p_message text)
    RETURNS bigint LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_wb bigint;
  v_attempted bigint;
  v_id bigint;
BEGIN
  -- the oracle bump, BEFORE the journal INSERT (non-transactional, survives everything --
  -- Element 5): if the INSERT below then fails, the sequence shows a counted gap the
  -- verify-chain reconciliation names.
  PERFORM nextval('refusal_seq');
  SELECT id INTO v_wb FROM principal WHERE name = 'write-boundary';
  IF v_wb IS NULL THEN
    RAISE EXCEPTION 'write boundary: the ''write-boundary'' tool principal is not registered in this world -- refusal recording has no authoring identity (kernel/lineage/s43-typed-verdict-write-boundary.sql Element 6; bootstrap/new-project.sh''s birth sequence registers it). The original refusal (SQLSTATE %) was: %', p_sqlstate, p_message;
  END IF;
  -- the ATTEMPTED identity: the explicit payload actor when it resolves to a registered id,
  -- else the session's own standing-declaration default (the identity that WOULD have been
  -- attributed); NULL when neither resolves -- the role below is still always known.
  IF (p_payload ? 'actor') AND (p_payload->>'actor') ~ '^[0-9]+$' THEN
    SELECT id INTO v_attempted FROM principal WHERE id = (p_payload->>'actor')::bigint;
  END IF;
  IF v_attempted IS NULL THEN
    SELECT principal_id INTO v_attempted FROM principal_role WHERE db_role = session_user;
  END IF;
  INSERT INTO ledger (kind, statement, actor,
                      refusal_sqlstate, refusal_message, refusal_surface,
                      refusal_payload_digest, refusal_attempted_actor, refusal_attempted_role)
  VALUES ('write_refused',
          format('write refused at surface %s (SQLSTATE %s)', p_surface, p_sqlstate),
          v_wb,
          p_sqlstate, p_message, p_surface,
          encode(sha256(convert_to(p_payload::text, 'utf8')), 'hex'),
          v_attempted, session_user)
  RETURNING id INTO v_id;
  RETURN v_id;
END; $fn$;
REVOKE ALL ON FUNCTION :"kern".journal_write_refusal(text, jsonb, text, text) FROM PUBLIC;

COMMENT ON FUNCTION :"kern".journal_write_refusal(text, jsonb, text, text) IS
  'The ONE home of "a refusal becomes a committed write_refused row" (s43 Element 4), called
   only from inside the four SECURITY DEFINER boundary functions (no role holds EXECUTE).
   Bumps the refusal_seq oracle FIRST (non-transactional), then journals: actor = the
   write-boundary tool principal; the attempted identity in refusal_attempted_*; the payload
   as a SHA-256 digest only (R4). If this INSERT itself fails the exception propagates -- a
   loud abort, a counted sequence gap, the server log as residual coverage (fail-safe on
   both legs). kernel/lineage/s43-typed-verdict-write-boundary.sql.';

-- ============================================================================================
-- ELEMENT 3 -- THE FOUR BOUNDARY FUNCTIONS.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"kern".ledger_write(payload jsonb)
    RETURNS :"kern".write_verdict LANGUAGE plpgsql SECURITY DEFINER
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  k text;
  cols text := '';
  vals text := '';
  v_id bigint;
  v_state text; v_msg text; v_refusal bigint;
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
    GET STACKED DIAGNOSTICS v_state = RETURNED_SQLSTATE, v_msg = MESSAGE_TEXT;
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
   write path -- the granted role holds no ledger INSERT.
   kernel/lineage/s43-typed-verdict-write-boundary.sql.';

CREATE OR REPLACE FUNCTION :"kern".review_write(payload jsonb)
    RETURNS :"kern".write_verdict LANGUAGE plpgsql SECURITY DEFINER
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  k text;
  v_id bigint;
  v_state text; v_msg text; v_refusal bigint;
BEGIN
  BEGIN
    FOR k IN SELECT jsonb_object_keys(payload) LOOP
      IF k NOT IN ('regards', 'statement', 'verdict', 'independence', 'basis',
                   'antecedent', 'actor') THEN
        RAISE EXCEPTION 'write boundary: review payload key ''%'' is not a member of the review ceremony''s contract (regards, statement, verdict, independence, basis, antecedent, actor -- s43 §4.2).', k;
      END IF;
    END LOOP;
    INSERT INTO ledger (kind, statement, regards, actor)
    VALUES ('review', payload->>'statement', (payload->>'regards')::bigint,
            (payload->>'actor')::bigint)
    RETURNING id INTO v_id;
    INSERT INTO review_detail (ledger_id, verdict, independence, basis, antecedent)
    VALUES (v_id, payload->>'verdict', payload->>'independence', payload->>'basis',
            (payload->>'antecedent')::bigint);
    SET CONSTRAINTS ALL IMMEDIATE;
    RETURN ('accepted', v_id, NULL, NULL, NULL)::write_verdict;
  EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS v_state = RETURNED_SQLSTATE, v_msg = MESSAGE_TEXT;
    IF v_state LIKE '22%' OR v_state LIKE '23%' OR v_state LIKE 'P0%' THEN
      v_refusal := journal_write_refusal('review', payload, v_state, v_msg);
      RETURN ('refused', NULL, v_refusal, v_state, v_msg)::write_verdict;
    END IF;
    RAISE;
  END;
END; $fn$;
REVOKE ALL ON FUNCTION :"kern".review_write(jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION :"kern".review_write(jsonb) TO :"role";

COMMENT ON FUNCTION :"kern".review_write(jsonb) IS
  'The review-ceremony write boundary (s43 §4.2): the kind=review ledger row and its
   review_detail row in ONE guarded block, so a refusal from EITHER insert -- including
   validate_independence''s D-6 human-only refusal and s34''s computed-grade refusal, which
   fire on review_detail -- journals as one write_refused row (surface ''review'') and rolls
   the whole ceremony. kernel/lineage/s43-typed-verdict-write-boundary.sql.';

CREATE OR REPLACE FUNCTION :"kern".registration_write(payload jsonb)
    RETURNS :"kern".write_verdict LANGUAGE plpgsql SECURITY DEFINER
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  k text;
  v_pid bigint;
  v_row bigint;
  v_state text; v_msg text; v_refusal bigint;
BEGIN
  BEGIN
    FOR k IN SELECT jsonb_object_keys(payload) LOOP
      IF k NOT IN ('name', 'agent_class', 'purpose', 'actor', 'event_declared_ts',
                   'statement') THEN
        RAISE EXCEPTION 'write boundary: registration payload key ''%'' is not a member of the registration ceremony''s contract (name, agent_class, purpose, actor, event_declared_ts, statement -- s43 §4.2).', k;
      END IF;
    END LOOP;
    INSERT INTO principal (name, agent_class)
    VALUES (payload->>'name', payload->>'agent_class')
    RETURNING id INTO v_pid;
    INSERT INTO ledger (kind, statement, actor, principal_subject, principal_purpose,
                        event_declared_ts)
    VALUES ('principal_registered',
            COALESCE(payload->>'statement',
                     format('principal ''%s'' registered (class %s)',
                            payload->>'name', payload->>'agent_class')),
            (payload->>'actor')::bigint, v_pid, payload->>'purpose',
            (payload->>'event_declared_ts')::timestamptz)
    RETURNING id INTO v_row;
    -- s40's anchor-coupling trigger is DEFERRED (fires at COMMIT -- outside any handler's
    -- scope). Forcing it immediate HERE pulls the commit-time refusal inside the guarded
    -- block, so a registration the anchor coupling would refuse is caught and journaled
    -- like any other (the consultation's named candidate-E obligation, discharged).
    SET CONSTRAINTS ALL IMMEDIATE;
    RETURN ('accepted', v_row, NULL, NULL, NULL)::write_verdict;
  EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS v_state = RETURNED_SQLSTATE, v_msg = MESSAGE_TEXT;
    IF v_state LIKE '22%' OR v_state LIKE '23%' OR v_state LIKE 'P0%' THEN
      v_refusal := journal_write_refusal('registration', payload, v_state, v_msg);
      RETURN ('refused', NULL, v_refusal, v_state, v_msg)::write_verdict;
    END IF;
    RAISE;
  END;
END; $fn$;
REVOKE ALL ON FUNCTION :"kern".registration_write(jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION :"kern".registration_write(jsonb) TO :"role";

COMMENT ON FUNCTION :"kern".registration_write(jsonb) IS
  'The registration-ceremony write boundary (s43 §4.2): the kernel.principal anchor and its
   principal_registered event atomically, with SET CONSTRAINTS ALL IMMEDIATE inside the
   guarded block so s40''s deferred anchor-coupling refusal is caught and journaled (surface
   ''registration'') instead of aborting at COMMIT. A duplicate name now leaves a durable
   write_refused trace (23505) -- the panel''s silent-duplicate class has its record.
   kernel/lineage/s43-typed-verdict-write-boundary.sql.';

CREATE OR REPLACE FUNCTION :"kern".obligation_write(payload jsonb)
    RETURNS :"kern".write_verdict LANGUAGE plpgsql SECURITY DEFINER
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  k text;
  v_state text; v_msg text; v_refusal bigint;
BEGIN
  BEGIN
    FOR k IN SELECT jsonb_object_keys(payload) LOOP
      IF k NOT IN ('scope', 'assigned_by', 'obliges_actor') THEN
        RAISE EXCEPTION 'write boundary: obligation payload key ''%'' is not a countersign_obligation column (scope, assigned_by, obliges_actor -- s43 §4.2).', k;
      END IF;
    END LOOP;
    INSERT INTO countersign_obligation (scope, assigned_by, obliges_actor)
    VALUES (payload->>'scope', (payload->>'assigned_by')::bigint,
            (payload->>'obliges_actor')::bigint);
    SET CONSTRAINTS ALL IMMEDIATE;
    -- row_id NULL: countersign_obligation has no bigint id (scope is its PK) -- documented
    -- in the verdict type's own definition.
    RETURN ('accepted', NULL, NULL, NULL, NULL)::write_verdict;
  EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS v_state = RETURNED_SQLSTATE, v_msg = MESSAGE_TEXT;
    IF v_state LIKE '22%' OR v_state LIKE '23%' OR v_state LIKE 'P0%' THEN
      v_refusal := journal_write_refusal('obligation', payload, v_state, v_msg);
      RETURN ('refused', NULL, v_refusal, v_state, v_msg)::write_verdict;
    END IF;
    RAISE;
  END;
END; $fn$;
REVOKE ALL ON FUNCTION :"kern".obligation_write(jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION :"kern".obligation_write(jsonb) TO :"role";

COMMENT ON FUNCTION :"kern".obligation_write(jsonb) IS
  'The countersign_obligation write boundary (s43 §4.2): uniformity is the argument -- no
   granted-role DML except through a verdict-returning function, no config-table carve-out
   that would re-open the class. The obligate-revoke DELETE stays the owner-side escalation
   path it always was. kernel/lineage/s43-typed-verdict-write-boundary.sql.';

-- ============================================================================================
-- ELEMENT 7 -- THE PRIVILEGE CHANGE (total: after this, a raw INSERT from the granted role
-- dies at SQLSTATE 42501 before any semantics run; the boundary functions are the only path).
-- ============================================================================================
REVOKE INSERT ON :"schema".ledger FROM :"role";
REVOKE INSERT ON :"schema".ledger FROM PUBLIC;
REVOKE INSERT ON :"schema".review_detail FROM :"role";
REVOKE INSERT ON :"schema".review_detail FROM PUBLIC;
REVOKE INSERT ON :"kern".principal FROM :"role";
REVOKE INSERT ON :"kern".principal FROM PUBLIC;
REVOKE INSERT ON :"schema".countersign_obligation FROM :"role";
REVOKE INSERT ON :"schema".countersign_obligation FROM PUBLIC;
