-- s40 PRINCIPAL IDENTITY EVENTS (design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md, the
-- FROZEN build basis, Fable-authored spec, RATIFIED 2026-07-18 -- six reserved decisions
-- ratified ledger rows 1419 and 1426, technical corrections C1-C13 in the basis's own dated
-- amendment block GOVERN wherever they conflict with its body text; this delta is built against
-- the basis AS CORRECTED). Fable-built per the basis's C12 (maintainer-ruled 2026-07-18: this
-- family is built by Fable, nothing in it touched by Sonnet; later families revert to the
-- standing Sonnet-executes default). First of the TWO-delta family s40/s41 (basis §9(d),
-- ratified: two deltas, git-revertible independently); s41 hard-depends on THIS delta.
--
-- This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/existing world is
-- the maintainer's act at a FUTURE world's birth (runs-are-strictly-linear ruling, 2026-07-11),
-- never taken here. An ADDITIVE delta applied ON TOP of the s15..s39 kernel (the established
-- remediation-delta idiom), NOT a retro-edit of a frozen sNN record (ADR-0005 Rule 8) and NOT a
-- second hand-copy of any existing mechanism (ADR-0012 P1: identity events live on the EXISTING
-- ledger -- basis §2's load-bearing choice -- inheriting append-only, actor attribution, stamps,
-- the s26 hash chain, review/countersign, and s31 supersession wholesale, rather than re-minting
-- a second copy of the kernel's record machinery on a new principal_event table).
--
-- PREREQUISITE: this delta REQUIRES s39 (kernel/lineage/s39-blocks-start.sql) applied first --
-- it re-issues ledger_current/countersigned_in_force in the EXACT column-list shape s37 left
-- them (s38/s39 added no column) appending its own four columns, and re-issues ledger_kind_check
-- in the exact 15-member shape s37 left it, widened by four. Applying this file on a pre-s37
-- kernel fails loudly at CREATE OR REPLACE VIEW time (column l.work_violation_witness does not
-- exist), the correct, disclosed failure mode for a hard dependency, matching every prior
-- delta's own PREREQUISITE precedent. The s39 requirement specifically is POSITIONAL (this
-- delta's place in the birth chain, wired into bootstrap/new-project.sh's LINEAGE_CHAIN in this
-- same commit), not syntactic -- named honestly rather than overclaimed.
--
-- WHY (operator-side prose; NOT subject-visible -- only the catalog objects inside the opaque db
-- are): the basis §1, verbatim in substance. The kernel's `principal` table -- the record of WHO
-- every ledger row is attributed to -- is four flat columns with no history, no registrar, no
-- lifecycle, and no link to any authentication machinery: the ONE load-bearing surface in the
-- kernel exempt from the kernel's own append-only, attributed, tamper-evident record discipline.
-- The defect class, in its most general form (basis §1(a)): an authority-carrying identity whose
-- authority, scope, and validity period are not representable, so every misuse of it IS
-- representable. Witnessed instances (the panel deployment's lived history): silent duplicate
-- registrations (`ON CONFLICT (name) DO NOTHING` swallowing every re-registration by name as a
-- no-op, panel ids 1-27 with burned gaps); registration producing no record of registrar, time,
-- purpose, or approval; reviewer/reviewer2 class drift with no event recording either
-- assignment. The foreclosing type is the kernel's OWN idiom: identity facts as append-only
-- attributed ledger EVENTS; current standing as a DERIVED read; the anchor IMMUTABLE. This
-- delta ships the identity/lifecycle/attribution half (four event kinds, derived standing,
-- strict attribution, the anchor coupling); s41 ships the bindings/relations half.
--
-- ELEMENT 1 -- FOUR NEW LEDGER KINDS (basis §3.1; s38 idiom: DROP/ADD, additive vocabulary):
--   principal_registered       -- the birth event of an identity.
--   principal_suspended        -- standing withdrawn. NO v1 verb lifts it (see REINSTATEMENT
--                                 below); the only v1 path back to active standing is a fresh
--                                 successor principal.
--   principal_revoked          -- standing withdrawn, same posture (no v1 reinstatement).
--   principal_standing_declared -- the explicit act binding a database role to a principal as
--                                 its standing (default) attribution: the DECLARED-not-silent
--                                 default the ratification requires (basis §3.6 / row 1398).
--
-- ELEMENT 2 -- FOUR NEW KIND-SCOPED LEDGER COLUMNS (basis §3.2 + C1; all nullable, NO column
-- DEFAULT -- the s30 lesson: a column-level DEFAULT would backfill every kind of row):
--   principal_subject bigint REFERENCES kernel.principal(id) -- the principal the event is
--     ABOUT (distinct from `actor`, who performed the act). TWO-WAY kind-shape CHECK over the
--     four s40 kinds (s41 re-issues the SAME CHECK widened to its own four kinds -- one home,
--     never a second patching constraint). Two-way is safe where s30 had to be one-way: no
--     pre-existing row can carry these kinds (the kind values are born in this same delta), so
--     ADD CONSTRAINT validates vacuously.
--   principal_purpose text -- mandatory non-empty on principal_registered, NULL on every other
--     kind. TWO-WAY per the basis's C5 (the kind is born here; there was never a grandfathering
--     reason for one-way). The non-emptiness is a SEPARATE value CHECK (house split: kind-shape
--     vs value-shape, s29's witnessed_requires_ref precedent) so gates/kind_shape_manifest_
--     gate.py's classifier parses each CHECK as exactly one concern. This is AC-2's "account
--     with a stated purpose" landed as a typed column, not decision-row prose.
--   principal_db_role text -- mandatory on principal_standing_declared, forbidden elsewhere
--     (two-way).
--   principal_actor_resolution text -- basis §9(f) RATIFIED build + C1 (minted HERE, in the
--     same delta and commit that re-issues set_actor -- NOT in s41). Nullable, KIND-AGNOSTIC
--     (every ledger row of any kind may carry it -- a CORE column in gates/kind_shape_manifest_
--     gate.py's vocabulary, registered there in this same commit), value CHECK
--     IN ('explicit','declared-default') when non-NULL. Set by the re-issued set_actor at write
--     time: 'explicit' when the write supplied a non-NULL actor before resolution, 'declared-
--     default' when set_actor resolved a NULL actor via the standing declaration. NULL only on
--     pre-s40 history, where the distinction cannot be reconstructed. Recordable, not gating:
--     nothing refuses on this column's value; it exists so the declared-default regime is
--     AUDITABLE (the panel's misattribution investigation had to reconstruct exactly this
--     intent from session transcripts), not merely correct.
--
-- ELEMENT 3 -- THE ANCHOR COUPLING (basis §3.3): a BARE registration is unrepresentable. A new
-- DEFERRED CONSTRAINT TRIGGER on kernel.principal (AFTER INSERT, DEFERRABLE INITIALLY DEFERRED)
-- refuses, at COMMIT, any newly-inserted principal row with no same-transaction
-- principal_registered ledger row whose principal_subject is the new id -- the kernel can now
-- distinguish a governed registration from a bare one, because a bare one CANNOT COMMIT.
-- Anchor rows predating s40 (in a birth chain: exactly the s15-seeded 'author') are untouched
-- (AFTER INSERT triggers never fire retroactively); the scaffold discharges author's event
-- explicitly (bootstrap/new-project.sh, this same commit). The anchor also gains explicit
-- append-only triggers (UPDATE/DELETE/TRUNCATE refused for every role, reusing the ledger's own
-- append_only() -- ADR-0012 P1; its message text says "the ledger", accepted as the reuse cost
-- the basis itself chose) so agent_class/name immutability is ENFORCED, not assumed.
--
-- ELEMENT 4 -- STANDING, DERIVED (basis §3.4). kernel.principal_standing(pid) returns 'active',
-- 'suspended', 'revoked', or 'unregistered-legacy' -- NEVER a stored status column. A
-- disambiguation, stated once (the basis's own): "standing" here means an IDENTITY's current
-- status and is unrelated to s36's standing_decisions / `led standing` vocabulary (decision
-- durability); the new verb is namespaced `led principal declare-standing` and shares nothing
-- with `led standing`. SECURITY DEFINER (s17 stamp_valid precedent) + STABLE (a correct
-- ADDITION over that precedent: nothing this function reads changes within one statement --
-- stamp_valid's own volatility is forced by its per-session secret, not shared here), EXECUTE
-- granted to :role: the standing computation reads ledger structural columns, and a zero-SELECT
-- writer in an s18-style deployment must not be refused inside the trigger chain -- the
-- finding-45 class (s18's own 2b block), foreclosed STRUCTURALLY here rather than by widening
-- column grants. A sibling kernel.principal_standing_basis(pid) (same SECURITY DEFINER shape,
-- same rationale, same grant) returns the governing standing-event row id so set_actor's
-- refusal can NAME the row (basis §3.6 refusal 2) without re-minting the finding-45 shape at
-- the refusal site. PRECEDENCE, stated because nothing prevents an unsuperseded suspension and
-- an unsuperseded revocation coexisting: 'revoked' ALWAYS dominates 'suspended' -- a strict
-- severity ordering, not event-recency (revoking an already-suspended principal is a clean
-- escalation; suspending an already-revoked one is legal to write, changes nothing observable).
-- REINSTATEMENT, honestly: NOT BUILT in v1, for either kind (basis §3.4/§9(b), ratified). No
-- kind exists whose write, superseding a principal_suspended/principal_revoked row, means
-- "lift" -- same-kind supersession would read as re-suspend/re-revoke, and inventing lift
-- semantics under review pressure is exactly what the basis declined twice. The only v1 escape
-- is a fresh successor principal (+ s41's `succeeds` edge). 'unregistered-legacy' (an anchor
-- row with no in-force registration event -- the pre-s40 seeds' state on a partially-migrated
-- scratch, and, under s31 uniform retraction, a principal whose registration event was later
-- superseded) is treated as ACTIVE for write purposes so a legacy 'author' is never bricked --
-- named, not hidden. A companion read view principal_standing_current (one row per principal:
-- name, class, standing, registered_at, registrar, purpose) is the human/SPA surface
-- (security_invoker, SELECT to :role; first registration event per principal wins its
-- registered_at/registrar/purpose columns -- min(id), a raw direct-writer's hypothetical second
-- registration event never multiplies rows).
--
-- ELEMENT 5 -- principal_role BECOMES A DERIVED VIEW (basis §3.5; one fact, one home). The s15
-- TABLE kernel.principal_role is dropped and re-created as a VIEW of the same name and column
-- shape (db_role, principal_id) over unsuperseded principal_standing_declared events (latest
-- unsuperseded declaration per db_role wins -- one current binding per role BY CONSTRUCTION).
-- Same shape means set_actor and every existing reader keep their query text. The view is
-- OWNER-RIGHTS (NO security_invoker clause -- basis C4, a deliberate, argued departure from the
-- s41 D-5 house default): set_actor is SECURITY INVOKER and reads this view on every
-- default-resolved write, so an invoker-rights view over `ledger` would demand structural-
-- column SELECT from zero-SELECT s18-class writers inside the trigger chain -- the finding-45
-- shape, re-minted at the neighboring object. Owner-rights closes it structurally (view
-- ownership rather than function SECURITY DEFINER -- same rationale as Element 4, different
-- mechanism). GRANT SELECT to :role is enumerated below (C4: the ordinary birth-chain leg the
-- basis's §3.5 omitted). The view factors through ledger_current (the s31 reader discipline --
-- no raw-`ledger` leg of its own).
--
-- ELEMENT 6 -- STRICT ATTRIBUTION: set_actor RE-ISSUED (basis §3.6; the s19 search_path-
-- carrying body is the one re-issued -- the meta-consult Axis 3 finding, honored: the delta
-- targets the LINEAGE HEAD's declaration, never s15's frozen text). There is NO mode toggle:
-- in an s40+ kernel strict is the only posture; the reconciliation with ergonomics is the
-- DECLARED default, not a switch (a dormant permissive branch would be untestable dead code and
-- an invitation to silent flips). Existing worlds keep their posture by construction (deltas
-- are never applied to them). Strict REFUSES, with teach-text: (1) an undeclared write --
-- NEW.actor IS NULL and no principal_role row for current_user -> refuse teaching `./led
-- principal declare-standing` (a legible refusal replacing today's bare NOT NULL violation;
-- the semantics tighten from "any hand-inserted map row silences this" to "only a declared,
-- attributed, dated event does"); (2) a write under a revoked or suspended principal (after
-- resolution, explicit or defaulted) -> refuse, naming the standing event row id. Strict NEVER
-- refuses: a NULL actor under a role with a current standing declaration (it resolves -- this
-- IS the sanctioned default); an explicit actor that is registered and active; an
-- unregistered-legacy anchor (never bricked). A write under an UNREGISTERED principal id is
-- already unrepresentable by the actor FK -- VERIFIED, not new work; stated so the closure
-- statement can claim it without claiming new mechanism. set_actor also stamps
-- principal_actor_resolution (Element 2 / C1's assignment leg). Trigger name, timing, and
-- alphabetical position are UNCHANGED (set_actor still fires FIRST in the BEFORE INSERT chain:
-- set_actor < set_stamp < validate_* < zz_set_row_hash, the s17/s21/s26 ordering mechanism).
--
-- HISTORY: safe -- per-mechanism grounds (basis §3.8, executed as corrected by C1):
--   * kind CHECK re-issued WIDER (additive vocabulary: every pre-existing row's kind remains
--     exactly as legal; the four new values are disjoint from the fifteen old ones).
--   * FOUR new nullable no-DEFAULT columns (C1's count fix: principal_subject,
--     principal_purpose, principal_db_role, principal_actor_resolution); no backfill, no UPDATE
--     (the append-only trigger refuses it anyway, s30's witnessed lesson).
--   * every new CHECK vacuously satisfied by every pre-existing row (no pre-existing row
--     carries the new kinds or non-NULL new columns -- the kinds are born in this delta).
--   * set_actor re-issued with NEW REFUSALS ONLY: the pre-existing resolution branch is
--     behavior-identical for a declared binding (output-equality on the resolve path --
--     witnessed by the scaffold leg of this delta's fixture: a NULL-actor write under a
--     declared role resolves to the same principal id the s19 body resolved); the
--     undeclared path converts a bare NOT NULL constraint violation into a taught refusal
--     (still a refusal -- no write that succeeded before succeeds differently, none that
--     failed now passes); the revoked/suspended refusals fire only on kinds/events born here.
--     The principal_actor_resolution assignment writes a column no pre-existing reader names.
--   * the anchor's new append-only/deferred-constraint triggers fire only on post-s40 writes
--     (AFTER INSERT never retroactive; UPDATE/DELETE/TRUNCATE were already ungranted paths --
--     now refused for every role including the owner's ordinary DML).
--   * THE ONE NON-PURELY-ADDITIVE ACT -- principal_role table -> view -- analyzed explicitly:
--     at its birth-chain position the table carries exactly the s15 seed row; the DROP discards
--     it and the scaffold's birth-sequence step (2) re-establishes the same binding as a
--     declared event in the same birth run, so no world ever observes a binding gap. On a
--     scratch chain, the gap window between DROP and declaration REFUSES an actor-NULL write
--     (fail-safe polarity -- refused, never misattributed), witnessed in this delta's fixture.
--   * ledger_current/countersigned_in_force re-issued with the four new columns APPENDED AT THE
--     END (the s20 lesson, re-applied; column list = s37's exact list + the four). Re-verified
--     NOT members needing re-issue (no general column passthrough): work_item_current,
--     work_item_violations, work_violation_history, work_review_gap, review_gap,
--     question_status, review_stamp_distinctness, work_edge_* single homes, work_startable,
--     work_bookkeeping_closes, standing_decisions (reads ledger_current by explicit columns
--     id/decision_grade/statement -- none new).
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form; this delta's slice of the family
-- invariant -- the FAMILY closure is the basis §5, checked there against the consultation's §4
-- universe; s41 carries the bindings/relations slice):
--   - INVARIANT: every act the kernel records is attributable to a registered identity whose
--     registration, current standing, and role-binding (db-role standing declaration) are
--     themselves append-only, attributed, dated ledger events; no act is acceptable under an
--     identity that is revoked or suspended at write time, nor under no identity at all unless
--     a standing declaration -- itself such an event -- supplies one; no identity fact is
--     mutable (anchor append-only; events superseded, never rewritten), and no identity fact
--     has a second home outside its event (principal_role is a derived read of the events).
--   - QUANTIFICATION UNIVERSE (this delta's own additions, checked outward per the s38 lesson
--     -- enumerate every kind carrying every column constrained):
--       KINDS carrying principal_subject: exactly the four s40 kinds (two-way CHECK); s41
--         re-issues the SAME constraint widened to its own four -- enumerated in the CHECK
--         itself, never patched by a second constraint. principal_purpose: exactly
--         principal_registered (two-way). principal_db_role: exactly
--         principal_standing_declared (two-way). principal_actor_resolution: EVERY kind
--         (kind-agnostic by ratified design, §9(f)) -- a CORE column, registered as such in
--         gates/kind_shape_manifest_gate.py in this same commit.
--       VIEWS: ledger_current/countersigned_in_force re-issued here (+4 columns); the non-
--         member re-verification is in HISTORY above. principal_role (view, this delta) and
--         principal_standing_current (this delta) are new derived reads factoring through
--         ledger_current -- neither carries a raw-`ledger` leg (gates/ledger_reader_allowlist
--         .py's scratch chain extended in this same commit witnesses both classifying clean).
--       TRIGGERS: set_actor re-issued (first in chain, position unchanged); two new anchor
--         append-only triggers + one deferred constraint trigger on kernel.principal (NOT on
--         ledger -- the BEFORE INSERT chain on ledger gains no member, no ordering impact).
--       ENGINE: engine/ledger_edb.py's entry/6 emission carries `kind` generically (verified
--         by reading its cols list -- no closed kind enumeration anywhere on the entry path),
--         so the four new kinds flow through as ordinary entry facts and T_now derives from
--         supersedes exactly as before; the SQL/ASP differential (./judge, both layers) is
--         witnessed in AGREE on a fixture carrying every new kind (this delta's fixture),
--         never asserted. No new .lp predicate is minted (the new kinds have no T_now
--         derivation of their own -- same "ENGINE -- NONE" posture as s23/s25/s26/s30).
--       HASH CHAIN: compute_row_hash (s26) enumerates the s24-era column set and has NOT been
--         re-issued by any column-adding delta since (s28..s39 precedent, followed here) --
--         the four new columns are OUTSIDE the row-hash serialization, exactly like
--         work_parent..decision_grade before them. Named in LIMITS below, not silently
--         inherited.
--       GATES: gates/kind_shape_manifest_gate.py gains this delta in CHAIN + three MANIFEST
--         rows + one CORE column; gates/ledger_reader_allowlist.py gains this delta in CHAIN
--         (no new allowlist entry needed -- witnessed clean). Both in this same commit.
--   - DENOMINATION: standing is denominated in dated lifecycle EVENTS, computed at read, never
--     stored; attribution default in a declared standing EVENT (never a hand-inserted map
--     row); the actor-resolution mark in a closed two-value vocabulary on the row itself. No
--     bound in this delta is a bare literal; no name is a proxy for standing (the standing
--     function keys on principal id, the anchor's immutable primary key).
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT CLASS-RATIFIED
-- FAIL-SAFE, stated plainly (basis §9): this delta REPLACES a table with a view
-- (principal_role) and RE-ISSUES a live trigger body (set_actor) -- structural acts outside
-- the only-adds class even though every behavioral delta is a new refusal or a new column. It
-- ships ONLY under the basis's own ratification (rows 1419/1426, C1-C13 governing), routed as
-- the Fable-authored, maintainer-ratified spec the ORCHESTRATION contract requires for kernel
-- lineage.
--
-- LIMITS (pre-registered, the basis §8 + C7, this delta's slice):
--   - Trigger/CHECK refusals bind the granted role's ordinary INSERT path only; a
--     schema-owner/superuser can bypass -- the same disclosed bound s26..s39 carry.
--   - Standing is checked AT WRITE TIME; history under a later-revoked principal stands
--     (correct for a record; revocation is never retroactive doubt).
--   - Reinstatement has no verb and no kind in v1 (Element 4) -- deliberate, ratified (§9(b)).
--   - TOTAL-REVOCATION DEAD-END (C7, maintainer-ruled): if every registered principal in a
--     world ends revoked or suspended, no successor can be registered through the sanctioned
--     surface (register-principal's own ledger row requires an active actor) -- recovery below
--     one active principal is a schema-owner/superuser act, disclosed as such. A CLI refusal
--     on suspending/revoking the last active principal was considered and deliberately NOT
--     built in v1.
--   - THE db_role STANDING "REVOKE" LEG IS NOT COVERED in v1 (C8): a declaration is only ever
--     superseded by a newer declaration; a db_role cannot return to *undeclared*. Workarounds:
--     suspend/revoke the bound principal, or supersede with a declaration binding a different
--     principal. A true unbind kind is a future amendment on reinstatement's footing.
--   - A declared standing default still AUTHENTICATES nothing: the declaration says who the
--     connection speaks for, not who is at the keyboard. The stamp remains a tripwire; strict
--     attribution is honest bookkeeping, not authentication (never overclaims IA-2).
--   - Purpose text quality is unenforceable beyond non-emptiness; the countersign path is the
--     control.
--   - The four new columns are OUTSIDE compute_row_hash's serialization (s28..s39 precedent --
--     the hash covers the s24-era column set plus predecessor). A schema-owner tamper of a
--     post-s24 column is not chain-detected; flagged to the maintainer in this delta's own
--     report as a standing, lineage-wide limit, not new to (or closable by) this delta.
--   - 'unregistered-legacy' covers BOTH a pre-s40 seed and (under s31 uniform retraction) a
--     principal whose registration event was later superseded -- both treated as active for
--     writes. Retraction semantics for registration events themselves are deliberately NOT
--     specified in v1 (no lift/unregister kind exists); named, not silently resolved.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s39): schema/kern/role
-- are psql variables so this delta is VALIDATED on a throwaway substrate before any real apply.
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s40val -v kern=s40val_kernel -v role=s40val_rw \
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
--        -f s40-principal-identity-events.sql
--     (provision a genesis seed per s26's own block before the first ledger INSERT; NOTE the
--     s40-specific birth step: after the chain, the world's principals must be REGISTERED and a
--     standing DECLARED -- bootstrap/new-project.sh's --new-world birth sequence, this same
--     commit, is the scripted form; a hand-driven scratch does the same three acts explicitly,
--     as this delta's own fixture does.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer
--   ruling 2026-07-11, "runs are strictly linear"). This delta reaches reality by entering a
--   FUTURE world's birth chain, wired into bootstrap/new-project.sh's LINEAGE_CHAIN in this
--   SAME commit (s37/s38/s39 precedent). Authored and scratch-witnessed on scratch schema pairs
--   in the TOY db only -- NOT applied to any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (DROP+ADD CONSTRAINT; ADD COLUMN IF NOT EXISTS;
-- CREATE OR REPLACE FUNCTION/VIEW; DROP/CREATE TRIGGER; the table->view conversion is guarded
-- by a relkind check so a re-run against an already-converted schema is a no-op).
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
-- ELEMENT 1 -- KIND VOCABULARY WIDENED (s22/s25/s37's own re-issue point, four members later --
-- additive union, no removal, no reordering of the pre-existing members).
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS ledger_kind_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT ledger_kind_check CHECK (kind IN
    ('assumption','decision','question','verification',
     'finding','snag','revision','note','review',
     'work_opened','work_claimed','work_depends_on','work_closed',
     'commission','work_violation_disposition',
     'principal_registered','principal_suspended','principal_revoked',
     'principal_standing_declared'));

COMMENT ON CONSTRAINT ledger_kind_check ON :"schema".ledger IS
  'kernel/lineage/s40-principal-identity-events.sql: widens s37''s fifteen-member vocabulary by
   the four principal-identity event kinds (registered/suspended/revoked/standing_declared) --
   identity facts as append-only attributed ledger events, the kernel''s own record idiom
   applied to the one table that predated it (design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-
   BASIS.md §3.1). s41 widens it again by the four binding/relation kinds.';

-- ============================================================================================
-- ELEMENT 2 -- THE FOUR NEW COLUMNS (nullable, NO column DEFAULT -- the s30 lesson) + their
-- kind-shape and value CHECKs (split per concern so each CHECK is one classifiable shape).
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS principal_subject bigint
    REFERENCES :"kern".principal(id);
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS principal_purpose text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS principal_db_role text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS principal_actor_resolution text;

COMMENT ON COLUMN :"schema".ledger.principal_subject IS
  'The principal this identity event is ABOUT (distinct from actor, who performed the act).
   Mandatory on every principal_* kind, forbidden elsewhere (two-way kind-shape CHECK; s41
   re-issues it widened to the binding/relation kinds). kernel/lineage/s40-principal-identity-
   events.sql.';
COMMENT ON COLUMN :"schema".ledger.principal_purpose IS
  'The stated purpose of a registration (AC-2''s "account with a stated purpose" as a typed
   column). Mandatory non-empty on principal_registered, NULL on every other kind (two-way,
   basis C5). kernel/lineage/s40-principal-identity-events.sql.';
COMMENT ON COLUMN :"schema".ledger.principal_db_role IS
  'The database role a principal_standing_declared event binds to its subject principal as the
   standing (default) attribution -- the declared-not-silent default. Mandatory on that kind,
   forbidden elsewhere (two-way). kernel/lineage/s40-principal-identity-events.sql.';
COMMENT ON COLUMN :"schema".ledger.principal_actor_resolution IS
  'HOW this row''s actor was resolved: ''explicit'' (a non-NULL actor was supplied before
   set_actor ran -- an explicit LED_ACTOR) or ''declared-default'' (set_actor resolved a NULL
   actor via the standing declaration). KIND-AGNOSTIC (every row of any kind carries it from
   s40 onward; NULL only on pre-s40 history, where the distinction cannot be reconstructed).
   Recordable, not gating -- it exists so the declared-default regime is auditable (basis
   §9(f)). Set by set_actor, never writer-supplied in practice (a writer-supplied value is
   overwritten by the trigger''s own assignment -- both branches assign unconditionally).
   kernel/lineage/s40-principal-identity-events.sql.';

-- kind-shape CHECKs (each parses as exactly one (kind, column, arity) shape for
-- gates/kind_shape_manifest_gate.py -- MANIFEST rows added in this same commit):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_subject_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_subject_kind_shape CHECK (
    (kind IN ('principal_registered','principal_suspended','principal_revoked',
              'principal_standing_declared')) = (principal_subject IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_purpose_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_purpose_kind_shape CHECK (
    (kind = 'principal_registered') = (principal_purpose IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_db_role_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_db_role_kind_shape CHECK (
    (kind = 'principal_standing_declared') = (principal_db_role IS NOT NULL));

-- value CHECKs (no kind test -- ordinary vocabulary/business-rule CHECKs, out of the
-- kind-shape manifest's scope by that gate's own classifier):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_purpose_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_purpose_nonempty CHECK (
    principal_purpose IS NULL OR btrim(principal_purpose) <> '');

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_actor_resolution_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_actor_resolution_check CHECK (
    principal_actor_resolution IS NULL
    OR principal_actor_resolution IN ('explicit', 'declared-default'));

-- ============================================================================================
-- s20 LESSON RE-APPLIED: ledger_current + countersigned_in_force GAIN the four new columns,
-- APPENDED AT THE END. Explicit column lists throughout -- never `l.*`. Column list = s37's
-- exact list (s38/s39 added no column) + the four s40 columns.
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
       l.principal_actor_resolution
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
       l.principal_actor_resolution
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- ELEMENT 4 -- STANDING, DERIVED. SECURITY DEFINER + STABLE (see header for the s17 precedent
-- and the argued STABLE addition); EXECUTE revoked from PUBLIC, granted to :role (the
-- finding-45 foreclosure: a zero-SELECT s18-class writer must be able to have its standing
-- computed inside the trigger chain). Both functions factor through ledger_current (the s31
-- reader discipline; inside SECURITY DEFINER the invoker-rights view reads as the owner).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"kern".principal_standing(pid bigint)
    RETURNS text LANGUAGE plpgsql STABLE SECURITY DEFINER
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM principal WHERE id = pid) THEN
    RETURN NULL;   -- no anchor row at all: not a standing question (every write path's FK
                   -- forecloses reaching here with a live id; NULL is the honest non-answer)
  END IF;
  -- PRECEDENCE (header Element 4): 'revoked' ALWAYS dominates 'suspended' -- strict severity
  -- ordering, checked first, never event-recency.
  IF EXISTS (SELECT 1 FROM ledger_current e
             WHERE e.kind = 'principal_revoked' AND e.principal_subject = pid) THEN
    RETURN 'revoked';
  END IF;
  IF EXISTS (SELECT 1 FROM ledger_current e
             WHERE e.kind = 'principal_suspended' AND e.principal_subject = pid) THEN
    RETURN 'suspended';
  END IF;
  IF EXISTS (SELECT 1 FROM ledger_current e
             WHERE e.kind = 'principal_registered' AND e.principal_subject = pid) THEN
    RETURN 'active';
  END IF;
  RETURN 'unregistered-legacy';   -- an anchor with no in-force registration event: pre-s40
                                  -- seeds (and a retracted registration, s31 uniform
                                  -- retraction) -- treated as ACTIVE for write purposes by
                                  -- set_actor, so a legacy 'author' is never bricked.
END; $fn$;
REVOKE ALL ON FUNCTION :"kern".principal_standing(bigint) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION :"kern".principal_standing(bigint) TO :"role";

COMMENT ON FUNCTION :"kern".principal_standing(bigint) IS
  'An identity''s CURRENT standing, derived fresh on every call from the in-force lifecycle
   events -- never a stored status column: active | suspended | revoked | unregistered-legacy
   (revoked dominates suspended; unregistered-legacy = anchor with no in-force registration
   event, treated as active for writes). Unrelated to s36''s standing_decisions/`led standing`
   vocabulary (decision durability) -- see kernel/lineage/s40-principal-identity-events.sql''s
   own disambiguation note. SECURITY DEFINER so a zero-SELECT s18-class writer can be standing-
   checked inside the trigger chain (finding-45 foreclosure); an s18-class arming script must
   GRANT EXECUTE on this function to its reviewer roles.';

CREATE OR REPLACE FUNCTION :"kern".principal_standing_basis(pid bigint)
    RETURNS bigint LANGUAGE sql STABLE SECURITY DEFINER
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
  SELECT e.id FROM ledger_current e
  WHERE  e.principal_subject = pid
    AND  e.kind IN ('principal_revoked', 'principal_suspended')
  ORDER BY (e.kind = 'principal_revoked') DESC, e.id DESC
  LIMIT 1;
$fn$;
REVOKE ALL ON FUNCTION :"kern".principal_standing_basis(bigint) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION :"kern".principal_standing_basis(bigint) TO :"role";

COMMENT ON FUNCTION :"kern".principal_standing_basis(bigint) IS
  'The GOVERNING standing-event row id for a suspended/revoked principal (revocation preferred
   over suspension, then latest) -- exists so set_actor''s refusal can NAME the standing event
   row without re-minting the finding-45 invoker-read shape at the refusal site. NULL for an
   active/unregistered-legacy principal. kernel/lineage/s40-principal-identity-events.sql.';

-- ============================================================================================
-- ELEMENT 5 -- principal_role: TABLE -> DERIVED VIEW (same name, same column shape). The DROP
-- is guarded by a relkind check (idempotent: a re-run against an already-converted schema
-- skips it; DROP TABLE IF EXISTS alone would ERROR on the name now being a view). OWNER-RIGHTS
-- view (NO security_invoker -- basis C4; see header Element 5 for the finding-45 argument).
-- ============================================================================================
SELECT set_config('s40.kern', :'kern', false);
DO $$
DECLARE k text := current_setting('s40.kern');
BEGIN
  IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
             WHERE n.nspname = k AND c.relname = 'principal_role' AND c.relkind = 'r') THEN
    EXECUTE format('DROP TABLE %I.principal_role', k);
  END IF;
END $$;

CREATE OR REPLACE VIEW :"kern".principal_role AS
SELECT lc.principal_db_role AS db_role, lc.principal_subject AS principal_id
FROM   :"schema".ledger_current lc
WHERE  lc.kind = 'principal_standing_declared'
  AND  lc.id = (SELECT max(lc2.id) FROM :"schema".ledger_current lc2
                WHERE lc2.kind = 'principal_standing_declared'
                  AND lc2.principal_db_role = lc.principal_db_role);

COMMENT ON VIEW :"kern".principal_role IS
  'DERIVED VIEW since s40 (was an s15 TABLE -- kernel/lineage/s40-principal-identity-events.sql
   Element 5): the current db-role -> principal standing bindings, read off the LATEST
   unsuperseded principal_standing_declared event per db_role (one current binding per role by
   construction; rotation = a newer declaration, optionally superseding the old). Same column
   shape as the s15 table (db_role, principal_id) so set_actor and every reader keep their
   query text. OWNER-RIGHTS deliberately (no security_invoker -- basis C4): set_actor reads
   this view inside the SECURITY INVOKER trigger chain, and an invoker-rights view over ledger
   would refuse zero-SELECT s18-class writers there (the finding-45 shape). An s18-class arming
   script must GRANT SELECT on this view to its reviewer roles.';

GRANT SELECT ON :"kern".principal_role TO :"role";

-- ============================================================================================
-- ELEMENT 6 -- STRICT ATTRIBUTION: set_actor RE-ISSUED (the s19 search_path-carrying body is
-- the base -- the lineage head's declaration, per the meta-consult Axis 3 finding). New
-- refusals only; the resolve path is behavior-identical for a declared binding. Trigger
-- definition (name, timing, position) unchanged: set_actor still fires FIRST alphabetically.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".set_actor() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_standing text;
BEGIN
  IF NEW.actor IS NULL THEN
    SELECT principal_id INTO NEW.actor FROM principal_role WHERE db_role = current_user;
    IF NEW.actor IS NULL THEN
      RAISE EXCEPTION 'Ledger policy: strict attribution (s40) — this write supplied no actor and connection role ''%'' has no standing declaration, so the kernel cannot attribute it. Declare this role''s standing principal once, as an explicit recorded act: ./led principal declare-standing <principal-name> (writes a principal_standing_declared event — the declared-not-silent default; kernel/lineage/s40-principal-identity-events.sql §3.6). Alternatively, supply an explicit actor for this one write (LED_ACTOR=<registered-principal-name>).', current_user;
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
-- ELEMENT 3 -- THE ANCHOR COUPLING + ANCHOR APPEND-ONLY. Placed AFTER the set_actor re-issue
-- only for file legibility (nothing here depends on it); the deferred trigger fires at COMMIT.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"kern".principal_requires_registration_event() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM ledger_current e
                 WHERE e.kind = 'principal_registered' AND e.principal_subject = NEW.id) THEN
    RAISE EXCEPTION 'Ledger policy: a BARE principal registration is unrepresentable (s40 §3.3) — principal % (''%'') was inserted with no same-transaction principal_registered ledger event naming it as subject, so this transaction cannot commit. Register through the governed ceremony instead: ./led register-principal % <class> --purpose "<why this identity exists>" — it writes the anchor row and its registration event atomically (kernel/lineage/s40-principal-identity-events.sql Element 3).', NEW.id, NEW.name, NEW.name;
  END IF;
  RETURN NULL;
END; $fn$;
DROP TRIGGER IF EXISTS principal_registered_event_required ON :"kern".principal;
CREATE CONSTRAINT TRIGGER principal_registered_event_required
    AFTER INSERT ON :"kern".principal
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION :"kern".principal_requires_registration_event();

-- The anchor is IMMUTABLE: UPDATE/DELETE/TRUNCATE refused for every role (the ledger's own
-- append_only() reused, ADR-0012 P1 -- its message names "the ledger"; the reuse is the basis's
-- own choice, accepted over minting a near-identical second function). A class change is not an
-- event; it is a NEW principal plus (s41) a `succeeds` edge -- this is what forecloses the
-- reviewer/reviewer2 class-drift class rather than recording it politely.
DROP TRIGGER IF EXISTS principal_append_only_row ON :"kern".principal;
CREATE TRIGGER principal_append_only_row BEFORE UPDATE OR DELETE ON :"kern".principal
    FOR EACH ROW EXECUTE FUNCTION :"schema".append_only();
DROP TRIGGER IF EXISTS principal_append_only_truncate ON :"kern".principal;
CREATE TRIGGER principal_append_only_truncate BEFORE TRUNCATE ON :"kern".principal
    FOR EACH STATEMENT EXECUTE FUNCTION :"schema".append_only();

-- ============================================================================================
-- principal_standing_current -- the human/SPA read surface (one row per principal). The
-- registration-detail columns come from the FIRST (min-id) in-force registration event -- a
-- raw direct writer''s hypothetical second registration event never multiplies rows; named in
-- the header, not silently absorbed.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".principal_standing_current
    WITH (security_invoker = true) AS
SELECT p.id, p.name, p.agent_class,
       :"kern".principal_standing(p.id) AS standing,
       reg.ts AS registered_at, reg.actor AS registrar, reg.principal_purpose AS purpose
FROM   :"kern".principal p
LEFT JOIN :"schema".ledger_current reg
       ON reg.id = (SELECT min(r2.id) FROM :"schema".ledger_current r2
                    WHERE r2.kind = 'principal_registered' AND r2.principal_subject = p.id);

COMMENT ON VIEW :"schema".principal_standing_current IS
  'One row per principal: name, class, derived standing (kernel.principal_standing), and the
   first in-force registration event''s time/registrar/purpose (NULLs for an unregistered-legacy
   anchor). The human/SPA surface of s40''s identity events -- display, never enforcement.
   kernel/lineage/s40-principal-identity-events.sql.';

GRANT SELECT ON :"schema".principal_standing_current TO :"role";
