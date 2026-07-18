-- s45 STANDING LIFECYCLE -- db_role unbind + suspension lift as one kernel delta
-- (design/FABLE-STANDING-LIFECYCLE-SPEC.md, the RATIFIED build basis -- maintainer batch
-- ratification ledger row 1481, 2026-07-18; that spec's own conversion of the attested
-- design notes' §1.3/§2.3, whose C1-C13-style dated amendment block would GOVERN wherever it
-- conflicted with this delta's body text -- none found; this delta is built AS the spec
-- directs, §9). Sonnet-built (row 1481's build split: "Sonnet builds every component
-- post-conversion" -- the Fable-authoring families s40/s41/s42/s43 are the prior exception,
-- not the standing rule). NOT part of any two-delta family -- ONE delta, confirmed by the
-- spec's own §5 packaging analysis (the CHECK re-issue, the supersession-discipline trigger,
-- and the witness harness are shared indivisibly between the "unbind" and "lift" halves; a
-- split would force the second delta to re-issue the first's constraint/trigger bodies with
-- no independent revert value -- unlike s40/s41 and s42/s43, whose halves each carried
-- distinct object families).
--
-- This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/existing world is
-- the maintainer's act at a FUTURE world's birth (runs-are-strictly-linear ruling, 2026-07-11),
-- never taken here. An ADDITIVE-plus-re-issue delta applied ON TOP of the s15..s44 kernel (the
-- established remediation-delta idiom), NOT a retro-edit of a frozen sNN record (ADR-0005
-- Rule 8) and NOT a second hand-copy of any existing mechanism (ADR-0012 P1: the identity/
-- value-split retraction idiom s41 already established -- a superseding same-kind row with
-- principal_binding_active = false -- is licensed onto the two lifecycle kinds that missed it,
-- never re-minted as a second retraction shape).
--
-- PREREQUISITE: this delta REQUIRES s43 (kernel/lineage/s43-typed-verdict-write-boundary.sql)
-- applied first -- a HARD dependency (spec §2): it re-issues s41's principal_binding_active_
-- kind_shape CHECK (widened here), s40's principal_standing/principal_standing_basis/
-- kernel.principal_role, and s43's set_actor/validate_supersession_target bodies -- every one
-- of those objects must already exist in its s43-head shape for this file's DROP+ADD /
-- CREATE OR REPLACE statements to mean what they say. Applying this file on a pre-s43 kernel
-- fails loudly at the first re-issue referencing an s43-only object (e.g. validate_
-- supersession_target does not exist pre-s43 -- CREATE OR REPLACE still succeeds, but the
-- re-issued trigger then never fires against the pre-existing DROP TRIGGER IF EXISTS target,
-- and, decisively, the s43 columns validate_supersession_target reads pre-date this file by
-- construction) -- the correct, disclosed failure mode, matching every prior PREREQUISITE
-- precedent. THE HEAD-BODY RULE (spec §2, the builder's own most important standing
-- instruction, carried here verbatim): at this delta's authoring the lineage head is s43; an
-- s44 (model-identity attestation) may or may not precede this delta in a given birth chain
-- (row 1481's RD-2, evidence-gated). For EVERY object this delta re-issues, the base body is
-- the LINEAGE HEAD's declaration at build time, never a frozen sNN text (the migrate-detect-
-- drift ruling, 2026-07-16). This file's bodies below are quoted, verified, against the s43
-- head as built (no s44 exists in this repository's kernel/lineage/ at authoring time -- the
-- builder confirmed this by directory listing before authoring, per the head-body rule's own
-- STOP-and-surface duty: an s44 file landing later changes nothing here unless it re-issues
-- one of THIS delta's five re-issued objects, in which case a future re-application of s45 to
-- a chain carrying that s44 would need re-verification against s44's own head text -- named,
-- not silently assumed forever-safe).
--
-- WHY (operator-side prose; NOT subject-visible -- only the catalog objects inside the opaque
-- db are): the spec §1's class, in its most general form -- *a governance state with a
-- sanctioned way in and no sanctioned way out, so every exit is either impossible or a kludge
-- that re-mints the disease the state exists to manage.* Two witnessed instances: (1) a
-- db_role's standing declaration (kernel/lineage/s40-principal-identity-events.sql §3.6) is
-- repointable forever but never removable -- s40's own LIMITS named this gap explicitly (C8:
-- "a db_role cannot return to undeclared"), and every workaround (suspending the bound
-- principal; superseding with a declaration binding a different principal) either has
-- collateral (blocking that identity on EVERY channel, not just this role) or re-mints the
-- misattribution-window disease s40 was built to close (parking the role on a fabricated
-- tombstone principal); (2) suspension (kernel/lineage/s40-principal-identity-events.sql
-- Element 4, "REINSTATEMENT, honestly: NOT BUILT in v1") is enterable and not exitable, so it
-- degenerates into a soft revocation and the suspended/revoked vocabulary promises a
-- temporary/permanent distinction the machinery never delivered. The foreclosing type is the
-- kernel's OWN idiom, already proven at s41: identity/value-split retraction (a superseding
-- same-kind row, active = false, identity restated) -- licensed here onto the two kinds that
-- missed it, PLUS a genuinely new closure this conversion found in the field and did not
-- inherit from the source notes: a supersession-discipline type for the three standing-
-- lifecycle kinds (declaration/suspension/revocation), without which "terminal by type" and
-- "resurrection-proof" are both defeasible by a bare CROSS-KIND supersession (§3.4 below).
--
-- ELEMENT 1 -- principal_binding_active LICENSED ON TWO MORE KINDS (spec §3.1). The existing
-- s41 CHECK (principal_binding_active_kind_shape) is re-issued (its ONE home; DROP+ADD, never
-- a second patching constraint -- the principal_subject_kind_shape precedent, s40->s41),
-- widened from four kinds to six: principal_standing_declared and principal_suspended join
-- the four s41 binding kinds. principal_revoked is DELIBERATELY ABSENT -- that absence IS the
-- ratified "terminal by type": a lift-shaped revocation row (active = false) is refused by
-- this CHECK at construction, not by policy, not by convention, not by a CLI guard alone. The
-- existing kind-free CHECK principal_binding_inactive_needs_supersedes (s41: "active IS NULL
-- OR active OR supersedes IS NOT NULL") covers the two new members with ZERO edit: an
-- inactive-from-birth declaration or suspension is unrepresentable, exactly as it already is
-- for the four s41 kinds. Semantics, fixed by the spec (declaration: true = an in-force-
-- candidate binding, false = an unbind restating BOTH principal_db_role AND principal_subject;
-- suspension: true = an in-force-candidate suspension, false = a lift restating principal_
-- subject). Writers always supply the flag explicitly (the s30 no-column-DEFAULT lesson; the
-- column already carries no default from its s41 birth).
--
-- ELEMENT 2 -- kernel.principal_role RE-ISSUED, RESURRECTION-PROOF (spec §3.2). The trap: the
-- s40/s43-head view picks the max-id UNSUPERSEDED declaration per db_role. Non-superseding
-- declarations are legal (rotation "optionally supersedes" -- s40's own COMMENT; any direct
-- kernel.ledger_write caller may omit supersedes), so older unsuperseded declarations can
-- coexist under one role. If the view naively filtered active INSIDE its max-id selection, an
-- unbind of the NEWEST declaration would make the NEXT-OLDEST one the maximum -- silently
-- re-binding the role to a principal nobody chose (the resurrection this delta's witness plan
-- leads with, seen red on a harness-local naive variant before the shipped semantics is
-- trusted). The ratified semantics: select the governing row per db_role as the LATEST
-- unsuperseded declaration REGARDLESS of its active flag; emit it ONLY if that governing row
-- is active. The ONE change against the s40/s43-head body is the final conjunct
-- (AND lc.principal_binding_active) -- the max(lc2.id) subquery is BYTE-IDENTICAL and must
-- never gain an active filter itself, which is the exact trap this comment exists to name for
-- the next reader. Re-bind after unbind works by construction: a later fresh declaration
-- (higher id, active = true) becomes the new governing row. Owner-rights preserved (no
-- security_invoker clause -- s40's own C4 finding-45 argument is untouched by this edit);
-- GRANT SELECT re-stated after the re-issue (belt-and-braces; CREATE OR REPLACE VIEW preserves
-- grants -- stated so a future reader does not "fix" the apparent redundancy away). Two
-- transparent consumers, unchanged by this edit's own text: set_actor reads this view by name
-- on every default-resolved write (no set_actor edit needed for an unbind to take effect --
-- Element 5 below is teach-text only); s43's journal_write_refusal resolves the attempted-actor
-- default through it (an unbound role now yields a NULL refusal_attempted_actor with the role
-- still recorded in refusal_attempted_role -- correct, and witnessed in this delta's fixture,
-- never asserted).
--
-- ELEMENT 3 -- THE STANDING FUNCTIONS GAIN THE IN-FORCE FILTER (spec §3.3, correctness-
-- critical: without this edit the lift is WORSE than unbuilt). A lift row is itself kind
-- principal_suspended and unsuperseded (it is the terminal row of its own chain), so the
-- s40-era principal_standing's suspended-leg EXISTS test -- bare kind-existence in
-- ledger_current -- would read EVERY LIFTED suspension as still suspended, forever, which is
-- worse than the pre-s45 honest "no v1 verb lifts this" because it would silently pretend to
-- lift while changing nothing. Two functions re-issued, base bodies s40's own (unchanged by
-- s41/s42/s43): kernel.principal_standing(pid) gains one conjunct on the suspended-leg EXISTS
-- (AND e.principal_binding_active); the revoked leg and the revoked-dominates-suspended
-- precedence are UNTOUCHED (revocation rows never carry the flag -- Element 1's CHECK forbids
-- it -- so a bare kind-existence test on principal_revoked is, and remains, correct).
-- kernel.principal_standing_basis(pid) is the fork trap the source notes' own conversion
-- pinned: a bare "AND e.principal_binding_active" on the single-query form would DROP every
-- revocation from the result (revocations carry NULL for that column), so the WHERE instead
-- gains the kind-aware conjunct "AND (e.kind = 'principal_revoked' OR e.principal_binding_
-- active)" -- ordering (revoked preferred, then latest) unchanged. THE DECIDED RULE THIS
-- DELTA'S RATIFICATION ATTACHED HERE (I5, ratified YES, row 1481): lifecycle standing NEVER
-- conditions defeat force. Suspending a principal gates its FUTURE writes; it supersedes
-- nothing and withdraws nothing, so its PAST attestations and any trust grant empowering it
-- continue to operate in the (future) defeasibility layer, and a lift changes nothing there --
-- the sanctioned levers over defeat force are the grant and the attestation, never standing.
-- That rule binds a future defeat spec, not this delta's code; restated here (as the spec
-- itself insists) because "why is the suspended principal's past work still credited?" must
-- have its one-line answer ON the mechanism that provokes the question.
--
-- ELEMENT 4 -- SUPERSESSION DISCIPLINE FOR THE LIFECYCLE KINDS: validate_supersession_target
-- RE-ISSUED (spec §3.4, THE CONVERSION-FOUND CLOSURE -- kernel-level, decided here, the one
-- significant addition beyond the source notes). The hole, zero-context: retraction in this
-- kernel is uniformly "write a row whose supersedes names the target" (s31), and until s43
-- nothing constrained what KIND of row may supersede what -- s43's validate_supersession_
-- target added the first target-kind rule (write_refused targets refused). But the standing
-- machinery derives everything from ledger_current, so a `note` row superseding a revocation
-- makes the revocation VANISH from it -- silently reinstating a revoked principal with no
-- typed act; the same move on the governing declaration resurrects a stale older one PAST
-- Element 2's resurrection-proof view (that view is resurrection-proof against unbind, but a
-- cross-kind supersession removes the governing row from ledger_current entirely, changing
-- WHICH row is the max); the same move on a suspension is a lift that bypasses the attributed
-- lift row's own actor/statement rationale entirely. The source notes missed this axis;
-- ratified "terminal by type" is not deliverable without closing it. DECISION (fixed by the
-- spec, not this builder's to re-open): the three standing-lifecycle kinds get a kernel-
-- enforced supersession discipline, carried by RE-ISSUING s43's validate_supersession_target
-- (the trigger that already performs a row-addressed read of every supersession target)
-- rather than minting a second trigger doing the same read (ADR-0012 P1). The re-issued body:
-- the s43 write_refused refusal stays byte-identical and first; after it, one new block widens
-- the target row's SELECT from l.kind alone to (l.kind, l.principal_db_role, l.principal_
-- subject) -- same row-addressed read, three columns -- and refuses (a) any cross-kind
-- supersession of a standing-lifecycle target, (b) a declaration-superseding row whose
-- principal_db_role does not match its target's, or whose principal_subject does not match
-- when the new row is an unbind (active = false; a ROTATION, active = true, may repoint the
-- subject by design), (c) a suspension/revocation-superseding row whose principal_subject does
-- not match its target's. What this deliberately does NOT cover, named per the spec: principal_
-- registered targets (s40's disclosed 'unregistered-legacy' corner -- a real open question row
-- 1481 did not ratify) and the four s41 binding kinds (their value-continuity stays CLI-side
-- per s41's own disclosed limit -- retrofitting them is an unordered sweep ADR-0004 forbids).
-- Trigger name, timing, and position UNCHANGED (validate_supersession_target, BEFORE INSERT,
-- still sorts before validate_work_item and zz_set_row_hash alphabetically).
--
-- CONSEQUENCE, stated for the closure statement's honesty: with Element 1 (no flag on
-- revocations) plus this discipline (revocations superseded only by revocations, same
-- subject), a REVOKED principal's standing can never leave 'revoked' through any granted-role
-- write path: the lift row is unrepresentable (Element 1), the cross-kind escape is refused
-- (this Element), and a same-kind correction preserves the revoked reading. Succession (s41's
-- succeeds relation + a fresh principal) is, as ratified, the ONLY path -- now as a typed
-- fact, not merely an absence of a lift verb.
--
-- ELEMENT 5 -- set_actor RE-ISSUED: TEACH-TEXT BRANCHES ONLY, BEHAVIOR IDENTICAL (spec §3.5).
-- Base body: the s43 head's (session_user resolution for the standing-declaration lookup --
-- that edit MUST survive this re-issue unedited, or every boundary write would misattribute;
-- verified below by reading the re-issued body before shipping it). Exactly one change, in the
-- revoked/suspended refusal branch: the message now branches on v_standing. For 'suspended':
-- teach ./led principal lift-suspension <name> (an act of ANOTHER active principal -- a
-- suspended principal cannot write its own lift), naming the governing standing-event row id
-- as before. For 'revoked': the existing successor-path text stands, minus the now-FALSE "no
-- v1 verb lifts this standing" phrasing it previously shared with the suspended case --
-- revocation's text now says plainly that revocation is terminal by type and succession is the
-- sanctioned path. The undeclared-write refusal and both resolution branches (including the
-- principal_actor_resolution stamping) are BYTE-IDENTICAL to the s43 head. Trigger definition
-- unchanged (still first alphabetically in the BEFORE INSERT chain).
--
-- WHAT THIS DELTA DOES NOT TOUCH, stated as loudly as what it does (spec §3.7): ZERO new
-- columns -- compute_row_hash (s42/s43) is NOT re-issued; s42's law does not fire because there
-- is nothing for it to cover, witnessed by running gates/hash_coverage_gate.py green on the s45
-- head with no serializer change, and its own --inject-column negative control still red (the
-- gate itself stays alive). ZERO new kinds -- no kind-vocabulary CHECK re-issue; the kind_shape_
-- manifest_gate's MANIFEST gains one ROW UPDATE (principal_binding_active_kind_shape's kinds
-- tuple widens four->six), never a new row. No ledger_current/countersigned_in_force re-issue
-- (the s20 obligation fires only on column addition -- none here). ENGINE: no new .lp predicate
-- -- entry/6 is kind-generic (verified at s40, unchanged); the lift/unbind rows flow through as
-- ordinary entries and T_now derives from supersedes exactly as before; the ./judge SQL/ASP
-- differential is witnessed in AGREE on this delta's fixture, never asserted. The two-conjunct
-- in-force notion ("governing AND active") deliberately gets NO ASP home in this delta -- that
-- is the ratified I2 debt on the defeasibility envelope's successor spec (design/FABLE-
-- DEFEASIBILITY-ENVELOPE-2026-07-18.md I1/I2), triggered by this delta shipping, cited here so
-- the omission reads as the filed deferral it is, not a silent gap. Stamp machinery, review
-- paths, work-item machinery, obligation machinery: untouched.
--
-- HISTORY: safe -- per-mechanism grounds (spec §3, executed):
--   * principal_binding_active_kind_shape re-issued WIDER (additive: every pre-existing s41
--     binding row's legality is unchanged; the two new kinds are disjoint from the four old
--     ones and, being born in this delta on any birth chain that carries it, no pre-existing
--     row of either new kind can exist to violate the widened CHECK -- vacuous validation,
--     the s40/s41 precedent).
--   * kernel.principal_role re-issued with ONE new conjunct on an already-filtered subquery --
--     pre-s45, every governing row was implicitly active (no unbind kind existed to make one
--     inactive), so the new conjunct is a no-op on any pre-s45-produced row and only changes
--     behavior for a row this same delta makes representable.
--   * principal_standing/principal_standing_basis re-issued with new conjuncts that are no-ops
--     on any pre-existing suspension row (pre-s45, every suspension row was implicitly active
--     for the same reason as above) and only change behavior for a lift row this delta makes
--     representable.
--   * validate_supersession_target re-issued: the write_refused leg is byte-identical and
--     fires first; the new lifecycle-target leg only fires when the SUPERSESSION TARGET is one
--     of the three standing-lifecycle kinds -- on a pre-s45 world (this file never applies to
--     one; it only ever lands in a FUTURE world's birth chain) no such superseding write could
--     previously have been attempted through a CLI verb, so no previously-accepted write is
--     newly refused; a direct-psql caller gains a new, narrower legality, exactly the same
--     "new refusals only" shape s40/s41/s43's own set_actor/validate_independence re-issues
--     carry.
--   * set_actor re-issued with a TEACH-TEXT-ONLY change: the resolve path and the trigger/
--     refusal SHAPE (still refuses exactly {suspended, revoked}, still resolves exactly as
--     before) are unchanged; only the message text differs, verified by output-equality on the
--     non-branching legs (declared-default/explicit resolution) in this delta's fixture.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form):
--   - INVARIANT: in every world born under s45, a db_role's standing default and a principal's
--     suspension are withdrawable ONLY by an attributed, dated, superseding same-kind event
--     restating the identity it retracts; the current binding and the current standing are
--     derived reads that treat a retraction chain's terminal inactive row as ABSENCE, never as
--     force, and can never silently promote a stale older row; a revocation admits no lift row
--     (unrepresentable by CHECK) and no supersession except an identity-continuous same-kind
--     correction, so a revoked principal's derived standing is 'revoked' under every granted-
--     role write path until succession; and every refusal enforcing the above is a committed,
--     journaled write_refused row returned as a typed verdict (s43's boundary), never an
--     unrecorded abort.
--   - QUANTIFICATION UNIVERSE (checked outward, the presumption-of-narrowness inverted):
--       KINDS x the active flag: exactly six kinds carry it (the four s41 kinds + the two
--         licensed here), enumerated in the ONE re-issued CHECK; principal_revoked and every
--         other kind excluded by the same two-way test. No second constraint, no column, no
--         kind minted.
--       THE SUPERSESSION AXIS, both directions: AS TARGET, the three lifecycle kinds accept
--         only same-kind identity-continuous supersessors (Element 4); write_refused stays
--         unretractable (s43, byte-identical); principal_registered and the four s41 binding
--         kinds are named NOT covered (LIMITS below). AS SUPERSESSOR, an inactive row requires
--         a target (the pre-existing s41 CHECK, unedited); rotation/unbind/lift/correction
--         shapes are each enumerated in Element 4's rules with their identity-match
--         obligations.
--       DERIVED READERS OF STANDING/BINDINGS, disposed one by one: kernel.principal_role
--         (re-issued, Element 2); principal_standing/principal_standing_basis (re-issued,
--         Element 3); principal_standing_current (transparent via the function -- no edit);
--         set_actor (reads the view + function -- teach-text re-issue only, Element 5);
--         journal_write_refusal's attempted-actor default (reads the view -- transparent,
--         witnessed); the s41 D-5 binding views and principal_competences (already active-
--         filtered by s41 -- untouched); SPA/pickup/display surfaces (read the views --
--         display-only, named, not touched).
--       WRITE SURFACES: all granted-role writes arrive via the s43 boundary (verdicts +
--         journal); CLI verbs enumerated below (led.tmpl); scaffold birth acts (new-project.sh
--         -- the standing declarations gain the flag); direct owner/superuser DML -- the
--         standing disclosed bound (LIMITS).
--       GATES/ENGINE/HASH: zero columns (gate-witnessed, hash_coverage_gate.py green with no
--         re-issue and its negative control still red); zero kinds; zero .lp predicates; the
--         I2 ASP debt filed on the envelope successor by name, not silently absorbed.
--   - DENOMINATION: standing and bindings in dated, attributed lifecycle EVENTS, computed at
--     read, never stored; in-force-ness in the two-conjunct governing-AND-active test (SQL
--     home = the re-issued view/functions); terminality in a CHECK's kind-set membership plus
--     a supersession-discipline trigger -- never in CLI convention or prose; continuity in
--     immutable principal ids and the target row's own restated columns, never names. No bound
--     is a bare literal.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT CLASS-RATIFIED
-- FAIL-SAFE, stated plainly (spec §5): this delta re-issues FOUR live objects (a view, two
-- functions, one trigger) -- structural acts outside the only-adds class even though every
-- behavioral delta is a new refusal, a new representable retraction, or a teach-text change.
-- It ships ONLY under this spec's own ratification (maintainer batch ratification, ledger row
-- 1481), routed as the Fable-authored, maintainer-ratified spec the CLAUDE.md ORCHESTRATION
-- contract requires for kernel-lineage work.
--
-- LIMITS (pre-registered, the spec §8 in full, this delta's own):
--   - Trigger/CHECK refusals bind the boundary-function path; the schema owner/superuser
--     bypass stands (s26..s44's own disclosure) -- including dropping the very triggers
--     Element 4 adds; the externally-held signed head remains the closing move.
--   - Standing is checked at write time only; a lifted principal's refused-era attempts exist
--     only as write_refused rows (correct -- there are no accepted rows to re-judge), and a
--     suspended principal's PAST accepted rows keep full credit unless positively defeated --
--     the coherent I6 asymmetry (Element 3's decided rule), named here so it is never "fixed".
--   - The duplicate-active suspension guard is CLI-side (led.tmpl's own `suspend` verb, not a
--     kernel CHECK -- a scan-shaped cross-row check the kernel CHECK machinery cannot express
--     and this spec declines to put in a trigger); stacked direct-writer suspensions each need
--     their own lift, fail-safe polarity (standing reads suspended until all are lifted).
--   - The unbind is forward-only; misattributed history is the (future) defeat layer's to
--     discount, never this delta's to rewrite.
--   - In a solo world whose only active principal is suspended, the lift itself cannot be
--     written through the sanctioned surface (no active writer) -- the C7-shaped dead-end,
--     narrowed (a second active principal now suffices where before nothing did) but not
--     closed; recovery below that line remains a schema-owner act, disclosed.
--   - The two-conjunct in-force notion has no ASP twin until the envelope successor pays I2;
--     until then the judge differential's coverage of principal machinery remains what it was
--     at s40 (kind-generic entry flow only) -- witnessed in AGREE, with the deeper pairing
--     debt filed, not hidden.
--   - Registration retraction / an unregister event is deliberately OUT (not ratified);
--     principal_registered stays outside Element 4's discipline, exactly as s40's LIMITS
--     disclosed it.
--   - Kernel-side value-continuity for the four s41 binding kinds stays CLI-side per s41's own
--     disclosed limit; retrofitting them is an unordered sweep (ADR-0004), deliberately not
--     done here.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s43): schema/kern/role
-- are psql variables so this delta is VALIDATED on a throwaway substrate before any real apply.
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s45val -v kern=s45val_kernel -v role=s45val_rw \
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
--        -f s42-row-hash-full-coverage.sql -f s43-typed-verdict-write-boundary.sql \
--        -f s45-standing-lifecycle.sql
--     (provision a genesis seed + stamp secret per s26/s17's own blocks before the first
--     ledger INSERT; birth the world's principals and standing declarations through the s43
--     boundary functions, per that delta's own VALIDATE note -- bootstrap/new-project.sh's
--     --new-world birth sequence is the scripted form, this same commit.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer
--   ruling 2026-07-11, "runs are strictly linear"). This delta reaches reality by entering a
--   FUTURE world's birth chain, wired into bootstrap/new-project.sh's LINEAGE_CHAIN in this
--   SAME commit (s40..s43 precedent). Authored and scratch-witnessed on scratch schema pairs
--   in the TOY db only -- NOT applied to any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (DROP+ADD CONSTRAINT; CREATE OR REPLACE
-- FUNCTION/VIEW; DROP/CREATE TRIGGER).
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
-- ELEMENT 1 -- principal_binding_active LICENSED ON TWO MORE KINDS (its ONE home, DROP+ADD).
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_binding_active_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_binding_active_kind_shape CHECK (
    (kind IN ('principal_relation_asserted','principal_role_bound','principal_key_bound',
              'principal_competence_granted',
              'principal_standing_declared','principal_suspended'))
    = (principal_binding_active IS NOT NULL));

COMMENT ON CONSTRAINT principal_binding_active_kind_shape ON :"schema".ledger IS
  'kernel/lineage/s45-standing-lifecycle.sql: widens s41''s four-kind licensing of the
   identity/value discriminator to SIX -- principal_standing_declared (an unbind: active=false
   restates BOTH principal_db_role and principal_subject) and principal_suspended (a lift:
   active=false restates principal_subject) join the four s41 binding kinds.
   principal_revoked is DELIBERATELY ABSENT -- that absence IS the ratified "terminal by
   type": a lift-shaped revocation row is refused by THIS CHECK at construction.';

-- ============================================================================================
-- ELEMENT 2 -- kernel.principal_role RE-ISSUED, RESURRECTION-PROOF (see header). The ONLY
-- change against the s40/s43-head body is the final conjunct; the max(lc2.id) subquery is
-- BYTE-IDENTICAL and MUST NOT gain an active filter of its own -- that is the trap.
-- ============================================================================================
CREATE OR REPLACE VIEW :"kern".principal_role AS
SELECT lc.principal_db_role AS db_role, lc.principal_subject AS principal_id
FROM   :"schema".ledger_current lc
WHERE  lc.kind = 'principal_standing_declared'
  AND  lc.id = (SELECT max(lc2.id) FROM :"schema".ledger_current lc2
                WHERE lc2.kind = 'principal_standing_declared'
                  AND lc2.principal_db_role = lc.principal_db_role)
  AND  lc.principal_binding_active;

COMMENT ON VIEW :"kern".principal_role IS
  'RESURRECTION-PROOF since s45 (kernel/lineage/s45-standing-lifecycle.sql Element 2): the
   governing row per db_role is the LATEST unsuperseded declaration REGARDLESS of its active
   flag; it is emitted ONLY if that governing row is itself active. This forecloses the
   resurrection trap: if the naive form filtered active INSIDE the max-id selection, an unbind
   of the newest declaration would make the next-oldest one the maximum, silently re-binding
   the role to a principal nobody chose. Unbind yields undeclared (no row emitted); a later
   fresh declaration (higher id, active=true) becomes governing again by construction (re-bind
   works with zero special-casing). OWNER-RIGHTS deliberately (no security_invoker -- s40''s
   own C4 finding-45 argument, untouched by this edit): set_actor reads this view inside the
   SECURITY INVOKER trigger chain, and an invoker-rights view over ledger would refuse
   zero-SELECT s18-class writers there. An s18-class arming script must GRANT SELECT on this
   view to its reviewer roles.';

GRANT SELECT ON :"kern".principal_role TO :"role";

-- ============================================================================================
-- ELEMENT 3 -- THE STANDING FUNCTIONS GAIN THE IN-FORCE FILTER (see header). Base bodies:
-- s40's own (SECURITY DEFINER + STABLE, the finding-45 foreclosure, unchanged by s41/s42/s43).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"kern".principal_standing(pid bigint)
    RETURNS text LANGUAGE plpgsql STABLE SECURITY DEFINER
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM principal WHERE id = pid) THEN
    RETURN NULL;   -- no anchor row at all: not a standing question (every write path's FK
                   -- forecloses reaching here with a live id; NULL is the honest non-answer)
  END IF;
  -- PRECEDENCE (unchanged, s40 Element 4): 'revoked' ALWAYS dominates 'suspended' -- strict
  -- severity ordering, checked first, never event-recency. Revocation rows never carry the
  -- active flag (Element 1's CHECK forbids it), so this leg needs no s45 edit.
  IF EXISTS (SELECT 1 FROM ledger_current e
             WHERE e.kind = 'principal_revoked' AND e.principal_subject = pid) THEN
    RETURN 'revoked';
  END IF;
  -- s45: the in-force filter. Without it a LIFTED suspension (kind=principal_suspended,
  -- active=false, itself the terminal unsuperseded row of its chain) would still read as
  -- 'suspended', forever -- worse than the pre-s45 honest "no verb lifts this", because it
  -- would silently pretend to lift while changing nothing observable.
  IF EXISTS (SELECT 1 FROM ledger_current e
             WHERE e.kind = 'principal_suspended' AND e.principal_subject = pid
               AND e.principal_binding_active) THEN
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
   event, treated as active for writes). Since s45 (kernel/lineage/s45-standing-lifecycle.sql
   Element 3) the suspended leg additionally requires principal_binding_active, so a LIFTED
   suspension (a superseding row, active=false) correctly reads as NOT suspended -- the
   correctness-critical edit without which the lift verb would be worse than unbuilt. SECURITY
   DEFINER so a zero-SELECT s18-class writer can be standing-checked inside the trigger chain
   (finding-45 foreclosure); an s18-class arming script must GRANT EXECUTE on this function to
   its reviewer roles.';

CREATE OR REPLACE FUNCTION :"kern".principal_standing_basis(pid bigint)
    RETURNS bigint LANGUAGE sql STABLE SECURITY DEFINER
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
  -- s45: the kind-aware in-force filter. A bare "AND e.principal_binding_active" would DROP
  -- every revocation from this result (revocation rows carry NULL for that column, forbidden
  -- by Element 1's CHECK) -- the fork trap the source notes' own conversion pinned. The
  -- correct filter is kind-aware: a revocation is always eligible; a suspension only when its
  -- own active flag is still true (a lifted suspension is no longer the governing basis row).
  SELECT e.id FROM ledger_current e
  WHERE  e.principal_subject = pid
    AND  e.kind IN ('principal_revoked', 'principal_suspended')
    AND  (e.kind = 'principal_revoked' OR e.principal_binding_active)
  ORDER BY (e.kind = 'principal_revoked') DESC, e.id DESC
  LIMIT 1;
$fn$;
REVOKE ALL ON FUNCTION :"kern".principal_standing_basis(bigint) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION :"kern".principal_standing_basis(bigint) TO :"role";

COMMENT ON FUNCTION :"kern".principal_standing_basis(bigint) IS
  'The GOVERNING standing-event row id for a suspended/revoked principal (revocation preferred
   over suspension, then latest) -- exists so set_actor''s refusal can NAME the standing event
   row without re-minting the finding-45 invoker-read shape at the refusal site. Since s45
   (kernel/lineage/s45-standing-lifecycle.sql Element 3) the suspension leg is additionally
   gated on principal_binding_active (kind-aware, NOT a bare conjunct -- a bare one would drop
   every revocation, which never carries the flag). NULL for an active/unregistered-legacy
   principal, or for a principal whose only suspension has been lifted.';

-- ============================================================================================
-- ELEMENT 4 -- SUPERSESSION DISCIPLINE FOR THE LIFECYCLE KINDS: validate_supersession_target
-- RE-ISSUED (see header -- the conversion-found closure). Base body: s43's own; the
-- write_refused leg stays byte-identical and fires first.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_supersession_target() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_target_kind text;
  v_target_db_role text;
  v_target_subject bigint;
BEGIN
  IF NEW.supersedes IS NOT NULL THEN
    -- the row-addressed target read widens from l.kind alone to three columns -- same shape
    -- of read, s43's own gates/ledger_reader_allowlist.py entry covers the widened read
    -- without a new entry (verified live, this delta's fixture).
    SELECT l.kind, l.principal_db_role, l.principal_subject
      INTO v_target_kind, v_target_db_role, v_target_subject
      FROM ledger l WHERE l.id = NEW.supersedes;

    IF v_target_kind = 'write_refused' THEN
      RAISE EXCEPTION 'Ledger policy: a write_refused row is UNRETRACTABLE (s43, ratified R6) — row % records a historical fact about a refused attempt; it asserts nothing retractable, and superseding it is the one path by which a later writer could make a refusal vanish from every current view. The record stands; if the refusal was wrong, the corrected write simply succeeds beside it (kernel/lineage/s43-typed-verdict-write-boundary.sql Element 2).', NEW.supersedes;
    END IF;

    -- s45 §3.4: standing-lifecycle supersession discipline (the conversion-found closure --
    -- without it, ANY writer could lift a revocation or resurrect a stale declaration by
    -- superseding it with an unrelated row of a different kind).
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
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_supersession_target ON :"schema".ledger;
CREATE TRIGGER validate_supersession_target BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_supersession_target();

COMMENT ON FUNCTION :"schema".validate_supersession_target() IS
  'BEFORE INSERT trigger (s43 Element 2/R6, widened s45 §3.4): (1) a write_refused row is
   unretractable -- a superseding row naming one is refused (byte-identical to s43); (2) the
   three standing-lifecycle kinds (principal_standing_declared, principal_suspended,
   principal_revoked) accept only SAME-KIND, IDENTITY-CONTINUOUS supersessors -- a cross-kind
   supersession, a role/subject mismatch on a declaration edit, or a subject mismatch on a
   suspension/revocation edit, is refused at construction (kernel/lineage/
   s45-standing-lifecycle.sql Element 4). principal_registered targets and the four s41
   binding kinds are deliberately OUT of this discipline (named limits, s45 §7/§8).';

-- ============================================================================================
-- ELEMENT 5 -- set_actor RE-ISSUED: TEACH-TEXT BRANCHES, BEHAVIOR IDENTICAL (see header). Base
-- body: the s43 head's (session_user resolution -- verified present below, unedited).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".set_actor() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_standing text;
BEGIN
  IF NEW.actor IS NULL THEN
    -- s43: session_user, NOT current_user -- unedited by s45 (see s43's own Element 8 comment
    -- for why: current_user inside SECURITY DEFINER is the function OWNER).
    SELECT principal_id INTO NEW.actor FROM principal_role WHERE db_role = session_user;
    IF NEW.actor IS NULL THEN
      RAISE EXCEPTION 'Ledger policy: strict attribution (s40) — this write supplied no actor and login role ''%'' has no standing declaration, so the kernel cannot attribute it. Declare this role''s standing principal once, as an explicit recorded act: ./led principal declare-standing <principal-name> --db-role % (writes a principal_standing_declared event — the declared-not-silent default; kernel/lineage/s40-principal-identity-events.sql §3.6, resolution on session_user since kernel/lineage/s43-typed-verdict-write-boundary.sql). Alternatively, supply an explicit actor for this one write (LED_ACTOR=<registered-principal-name>).', session_user, session_user;
    END IF;
    NEW.principal_actor_resolution := 'declared-default';
  ELSE
    NEW.principal_actor_resolution := 'explicit';
  END IF;
  v_standing := principal_standing(NEW.actor);
  -- s45: teach-text branches on v_standing -- the RESOLVE/REFUSE SHAPE is unchanged (still
  -- refuses exactly {suspended, revoked}); only the message differs, because the two
  -- standings now have genuinely different sanctioned paths forward (a lift vs. a
  -- succession -- s45 §3.1/§3.4 make revocation terminal by type, which the OLD shared
  -- "no v1 verb lifts this standing" text no longer honestly describes for either case).
  IF v_standing = 'suspended' THEN
    RAISE EXCEPTION 'Ledger policy: strict attribution (s40) — actor principal % is suspended (standing event row %); a suspended principal accepts no further writes. The sanctioned path forward is ANOTHER active principal lifting the suspension: ./led principal lift-suspension <name> (kernel/lineage/s45-standing-lifecycle.sql) — a suspended principal cannot lift its own suspension, since it cannot write. A fresh successor principal remains available too: ./led register-principal <new-name> <class> --purpose "<why>", then record the succession (kernel/lineage/s40-principal-identity-events.sql, Element 4).', NEW.actor, principal_standing_basis(NEW.actor);
  ELSIF v_standing = 'revoked' THEN
    RAISE EXCEPTION 'Ledger policy: strict attribution (s40) — actor principal % is revoked (standing event row %); revocation is TERMINAL BY TYPE (kernel/lineage/s45-standing-lifecycle.sql §3.1/§3.4) — no verb lifts it, and no supersession of the revocation row can either. The sanctioned path forward is a FRESH successor principal: ./led register-principal <new-name> <class> --purpose "<why>", then record the succession (kernel/lineage/s40-principal-identity-events.sql, Element 4 / REINSTATEMENT).', NEW.actor, principal_standing_basis(NEW.actor);
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS set_actor ON :"schema".ledger;
CREATE TRIGGER set_actor BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".set_actor();
