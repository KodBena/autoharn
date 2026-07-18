||| Autoharn.idr -- categorical documentation of the autoharn kernel semantics.
|||
||| READ THIS FIRST IF YOU DO NOT KNOW IDRIS (the maintainer's own case; this file is
||| meant to double as the architecture tour, easier to follow than the directory tree):
|||   * A `data` block lists the SHAPES that can exist -- each `|` line is one legal
|||     row shape, and the arguments after a constructor name are that shape's fields.
|||     If a shape isn't listed, it cannot be built: read "what data types exist" as
|||     "what the kernel's tables/CHECKs allow", literally.
|||   * A plain function (`foo : A -> B`) is a DERIVATION -- a pure read, no side effect,
|||     computed the same way every time from its arguments. Read these as the SQL
|||     views/functions and the ASP rules they transcribe.
|||   * `Type` fields that are themselves functions of an index (e.g. `witnessTy res`)
|||     encode a CONDITIONAL rule ("this field is mandatory only when ..."). Read the
|||     index, then read what the field becomes for each case -- that's the whole rule.
|||   * A `failing` block is a REFUSAL, witnessed at compile time: the block only
|||     type-checks if the code inside it is illegal. Every `failing` block below is a
|||     kernel trigger's rejection rendered as "this does not even parse", the strongest
|||     form of "refused".
|||   * Reading the file top to bottom (kinds -> projection -> write boundary ->
|||     obligation tree -> theorems -> dual producers -> worked examples) IS the tour:
|||     each section is one architectural layer of the kernel, in the kernel's own
|||     dependency order.
||| THE HONESTY CONTRACT: this file is DOCUMENTATION, never the source of truth -- the
||| kernel (kernel/lineage/*.sql + engine/lp/*.lp) governs, always. Where the model
||| below is deliberately ugly, unfinished, or narrower than you'd expect, that is
||| because the SUBSTRATE is -- see the "PRESERVED, ON PURPOSE" list in this header.
||| Beauty that would erase one of those facts is a regression, not a cleanup.
|||
||| AS-OF: kernel chain through s51
||| (s50, 2026-07-18, landed WHILE the s44-s49 parity pass below was in flight and absorbed
|||   by it before landing: the defeat-input exclusion fork this pass had rendered as an
|||   unadjudicated PARAMETER was adjudicated by the maintainer (row 1647,
|||   kernel/lineage/s50-defeat-input-raw-domain.sql) -- RAW HISTORY, the engine producers'
|||   own domain, on the LDuplicateOpen-class ground now carried by the LDefeatInput
|||   history license. What s50 became here: defeatInputRaw is named THE kernel semantics,
|||   instantiated as defeatedRowsKernel/creditedCurrentKernel (fixtures d50a/d50b);
|||   defeatInputCur stays as the superseded s46-era reading, R7-kept, because the
|||   parameterized machinery + the §2d lemmas are what make the ruling and its exact
|||   divergence class statable. Below, the parity-pass note stands as written -- its
|||   "NEITHER adjudicated" sentences described the world as of its own writing and are
|||   superseded by this note.)
||| (s44-s49 PARITY PASS, 2026-07-18 -- the same-day pay-down of the fresh-context consult
|||   (design/FABLE-AUTOHARN-IDR-CONSULT-2026-07-18.md, adjudicated ledger row 1644), which
|||   found the six-delta gap plus one wrong claim (s47 -- fixed first, commit 830e753). What
|||   each delta became here: s44 -- PModelAttested with the self-table FK as Fin n (the SQL's
|||   "structural, never CLI-side" met in this model's own signature idiom), the closed
|||   AttestGrade vocabulary, and the expectation/verdict coupling as the AttestVerdict/
|||   ExpectedF index pair -- unrepresentability, stronger than the CHECK (k44a-d);
|||   modelAttestations is the derived read; supersession stays ALLOWED (maySupersede's
|||   catch-all arm -- s44's argued contrast with R6). s45 -- the two lifecycle kinds carry
|||   the s41 discriminator, so a lift/unbind is representable at last (p45a/b); revocation is
|||   TERMINAL BY TYPE -- no flag position exists to spell a lift-shaped revocation (k45a);
|||   principalStanding's suspended leg gains the in-force+active filter; rowForce is the
|||   THREE-VALUED row-force read the old LAGGING note asked for, and principalRole is the
|||   resurrection-proof governing read with the trap structural (g45a-f); maySupersede
|||   carries s45 3.4's same-kind/identity-continuity discipline beside s43 R6 (b45d-j) --
|||   ONE typed supersession relation, the upgrade the consult argued would have PREDICTED
|||   3.4 had it existed at s43. A design-probe finding was filed at maySupersede (the
|||   unblessed false->true flag-transition cell) and RULED intended by the maintainer
|||   the same day (2026-07-18, ledger row 1650) -- see the dated note at maySupersede.
|||   s46 -- the defeat calculus with the defeat-input exclusion fork rendered as a PARAMETER:
|||   both horns defined (defeatInputRaw/defeatInputCur), NEITHER adjudicated (the
|||   maintainer's call, per the delta's own spec-silent disclosure); the agree/diverge
|||   boundary is machine-checked (inputsAgreeInForce/inputsAgreeNonInput/
|||   inputsDivergeSuperseded) and witnessed both polarities (worldDF/worldDG, d46a-d) --
|||   with a second design-probe finding at the lemmas: the divergence class is ANY
|||   superseded defeat-kind target, strictly wider than s46's own "kind-change chain"
|||   wording. s47 -- landed at commit 830e753 (VClaim notClosed, r8e); RClaimOnClosed now
|||   also names it in the verdict vocabulary. s48 -- reviewRefTy is n-indexed; the witnessed/
|||   deferred citation is the three-armed WitnessRef sum whose row arm is Fin n, so the
|||   head-guess defect that motivated s48 is unrepresentable (r48a); the SQL approximates
|||   that arm by regex over free text -- the typed-column lowering stays a FILED kernel
|||   proposal, named at WitnessRef, never claimed. s49 -- subsumed by construction and now
|||   HONESTLY so: the model's journaler (write's refusal arm, §3b) is total because
|||   PrincipalId = Nat has no range to overflow; that idealization is named in PRESERVED
|||   (Nat vs bigint), exactly where s49's defect class lived. AND THE BOUNDARY ITSELF
|||   (consult scope item 1): §3b's `write` is the TOTAL verdict function -- Ledger (S n) on
|||   BOTH arms, refusal as a journaled PWriteRefused row -- so the s43 totality invariant
|||   the note below declares out-of-model is NOW A TYPE FACT. That one sentence of the s43
|||   note is thereby superseded (kept verbatim below, the R7 record-don't-erase precedent);
|||   still genuinely out-of-model: the refusal_seq oracle, the journal-INSERT-failure leg,
|||   the SHA-256 digest. RefusalReason (§3b) is the boundary's premise family as an
|||   ENUMERABLE DATUM -- one constructor per kernel refusal arm, auditable against the SQL's
|||   refusal list, the correspondence surface whose absence let the s47 gap go unnoticed.
|||   The two stale LAGGING/correction blocks further below stand verbatim as superseded
|||   history, each marked at its head.)
||| (s43, 2026-07-18, same-commit extension: the
|||   typed-verdict write boundary. What s43 became here: PWriteRefused -- the journaled
|||   refusal as an ordinary payload constructor with its six typed fields and the closed
|||   RefusalSurface sum; VWriteRefused (no payload premise of its own -- the who-may-mint
|||   guard is boundary-side authorship, named); and boundaryOk gains premise (d), the
|||   ratified R6: an entry superseding a write_refused row is refused, the hiding
|||   unrepresentable (fixtures b43a/b43b, both polarities). What s43 deliberately does NOT
|||   get a rendering, named at PWriteRefused's own doc: the boundary functions' totality
|||   invariant (refusal-implies-journal) and the refusal_seq oracle are operational
|||   control-flow/reconciliation facts whose mechanical witnesses are the SQL, the gate,
|||   and ./verify-chain -- this model's append already IS the typed-verdict idea
|||   (proof-carrying acceptance), which is why s43 lands as one premise and one
|||   constructor, not a parallel machinery. Below this line the s42 note, then the s41
|||   parity note, stand verbatim. Prior head: s42 -- s42, 2026-07-18, same-commit bump: s42-row-hash-full-
|||   coverage re-issues compute_row_hash so the tamper-evidence serialization covers the
|||   full row -- a change ENTIRELY OUTSIDE this model's own universe, verified before
|||   bumping rather than bumped on faith: the hash chain has never been modeled here
|||   beyond LHashChain (the history-license vocabulary member naming zz_set_row_hash's
|||   raw read), because a byte-serialization's injectivity is a cryptographic/encoding
|||   fact with no categorical structure this transcription renders -- the coverage
|||   invariant's mechanical home is gates/hash_coverage_gate.py, named here as the
|||   deliberate out-of-model boundary, not silently absent. Below this line the s41
|||   parity note stands verbatim. Prior head: s41 -- the s36-s41 parity pass,
|||   2026-07-18 -- the six-delta
|||   gap the prior LAGGING note enumerated, closed in one pass, plus the s40/s41
|||   principal-identity family the same pass transcribes fresh from
|||   design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md's two landed deltas. What each
|||   delta became here: s36 -- PDecision carries its writer-supplied Maybe grade and
|||   standingDecisionIds is the in-force graded-decision read; s37 --
|||   PViolationDisposition is the typed answering act, and the debt/record projection
|||   split is modeled on the ONE violation class this model can even represent
|||   (danglingDepDebt vs danglingDepHistory -- most violation classes are structurally
|||   unrepresentable here BY the model's own types, which is the model agreeing with the
|||   views' purpose, noted at the definitions); s38 -- ReviewDisposition gains
|||   DBookkeeping with a proof-carrying CommitRef (the commit-shape regex as a boolean
|||   refinement) and strictPremise refuses it under strict, the s38 ELSIF; s39 --
|||   EdgeType gains BlocksStart, VDepBS mirrors VDepBC over the separate blocks-start
|||   subgraph, and VClaim gains the claim-time startBlockers precondition; s40 --
|||   principal identity events as four payload constructors, principalStanding as the
|||   derived read (revoked dominates suspended), and the write boundary's entry-level
|||   premise family (boundaryOk: actor standing checked at append); s41 -- the four
|||   binding/relation constructors with the identity/value split as a type index
|||   (CompetenceValueF: a withdrawal CANNOT carry band/basis, unrepresentable), the
|||   human-only key premise, the same-natural-person canonical-order premise, and D-6's
|||   human-attested managerial/financial scoping inside boundaryOk. s34's own note
|||   stands: the Draft-stage GradeF index still models that refusal for free.)
|||
||| [SUPERSEDED 2026-07-18 by the s44-s49 parity pass, header above -- kept verbatim, R7
|||  record-don't-erase precedent. Its closing "AS-OF stays s43" sentence no longer holds.]
||| LAGGING: s45-standing-lifecycle (kernel/lineage/s45-standing-lifecycle.sql, ratified spec
|||   design/FABLE-STANDING-LIFECYCLE-SPEC.md, maintainer batch ratification ledger row 1481)
|||   is NOT YET TRANSCRIBED here, named rather than silently absorbed (row 1481's own carve-
|||   out: "the gate, witnessed working at s42/s43, is the enforcement; the builder closes the
|||   model gap to the head or the gate stays honest about the lag"). s45's SQL semantics --
|||   principal_binding_active licensed on principal_standing_declared/principal_suspended
|||   (deliberately NOT principal_revoked -- terminal by type), kernel.principal_role's
|||   resurrection-proof governing-row read (latest unsuperseded declaration REGARDLESS of its
|||   active flag, emitted only if that governing row is itself active), the standing
|||   functions' in-force filter, and the standing-lifecycle supersession discipline -- are all
|||   witnessed at the SQL layer (seen-red/s45-standing-lifecycle/run_fixtures.py) and would,
|||   transcribed here, require genuine new type-level structure this model does not yet carry:
|||   a THREE-VALUED (not boolean) read of "does this row govern" (superseded / unsuperseded-
|||   inactive / unsuperseded-active) is exactly the kind of derived-read refinement this file's
|||   existing sections model well (see principalStanding's own revoked-dominates ordering), but
|||   it was not built this pass -- named as a filed debt, not a silent gap, per this file's own
|||   HONESTY CONTRACT above. AS-OF stays s43 until a future pass pays this down; the freshness
|||   gate (gates/idris_model_freshness.py) reads this line as a WARN, not a failure, exactly as
|||   designed for this disclosure.
|||
||| [SUPERSEDED 2026-07-18, same day, by the s44-s49 parity pass, header above -- kept
|||  verbatim; every "NOT TRANSCRIBED" status below is discharged by that pass.]
||| 2026-07-18 correction (fresh-context consult): the paragraph above named ONE lagging delta
|||   while the actual head had advanced to s49 -- the disclosure itself had gone stale, the
|||   exact silent-under-enumeration this file's HONESTY CONTRACT forbids. The full per-delta
|||   state as of this date:
|||   - s44 (model-identity attestation): NOT TRANSCRIBED. Its mechanisms (self-table FK =
|||     Fin n; closed grade/verdict sums; expectation/verdict coupling as an indexed family a la
|||     CompetenceValueF) are all inside this file's demonstrated idiom -- cheapest to pay down.
|||   - s45 (standing lifecycle): NOT TRANSCRIBED, as the paragraph above already names. Worse
|||     than lag on two points: the model cannot represent a lift (a same-kind active=false
|||     superseding row) and does not make revocation terminal (boundaryOk checks supersession
|||     targets only for PWriteRefused), so on both it PERMITS what the kernel refuses.
|||   - s46 (credited views / defeat calculus): NOT TRANSCRIBED. DualProducers does not know
|||     the defeat layer; the delta's own named raw-vs-current quantification divergence in the
|||     defeat-input exclusion is exactly this file's central subject, unmodeled.
|||   - s47 (claim-on-closed refusal): TRANSCRIBED this date -- VClaim's notClosed premise and
|||     red fixture r8e. Before this correction the model asserted a legality the kernel
|||     refuses (ValidPayload worldA (PWorkClaimed "a") elaborated); that was a wrong claim,
|||     not a lag.
|||   - s48 (review-witness row existence): NOT TRANSCRIBED. reviewRefTy DWitnessed stays
|||     NonEmptyText with no row-token semantics; the faithful form is a three-armed sum whose
|||     row arm is Fin n (this file's own idiom, which s48's regex approximates CLI-side).
|||   - s49 (journaler overflow guard): lands under the existing s43 out-of-model boundary
|||     carve-out at PWriteRefused (boundary control flow, not row algebra) -- and note the
|||     undisclosed idealization it exposes: PrincipalId = Nat is unbounded while the kernel's
|||     is bigint; s49's defect lived precisely in that numeric-range gap.
|||   - s51 (artifact store, 2026-07-18, spec design/FABLE-ARTIFACT-STORE-SPEC.md): adds a
|||     NON-LEDGER content-addressed table (kernel.artifact) and the fifth boundary function
|||     (artifact_write). Zero new ledger kinds/columns (hash-coverage gate witnessed), so the
|||     row algebra this model transcribes is UNCHANGED; the one in-model fact -- the refusal
|||     surface vocabulary gaining 'artifact' -- is rendered (SurfArtifact, with its
|||     unreachable-from-payload-families note). The store's own semantics (content addressing,
|||     size cap, append-only, corruption-refusing get) are out-of-model per the same boundary
|||     carve-out that covers the refusal_seq oracle: storage control flow, not row algebra.
|||
||| PROVENANCE:
|||   v1 (2026-07-15, night) -- an Opus transcription consultation, machine-checked,
|||     rendering kernel/lineage/s15,s22,s29,s30 + engine/lp/ledger_tnow.lp,work_items.lp
|||     + the two Fable specs then current. Banked verbatim in
|||     design/ORCH-IDRIS-TRANSCRIPTION-CONSULT-2026-07-15.md. Disposition: categorical
|||     documentation of what exists; kludgy-where-true is a first-class finding.
|||   THIS REFRESH (2026-07-15, later) -- supersedes v1 IN PLACE per a fresh-context
|||     refinement consultation (design/ORCH-IDRIS-REFINEMENT-CONSULT-2026-07-15.md,
|||     verdict REFINE-AND-LOWER), folding in its checked fragments
|||     design/RefKernel.idr (R1-R9) and design/RefUniverse.idr (kind-universe pattern).
|||     What changed: (1) R7 -- v1 transcribed the pre-s31 "closes"-CTE blind spot as the
|||     kernel's live behavior; kernel/lineage/s31-supersession-uniform-retraction.sql
|||     (ratified the same day) fixed that blind spot in the substrate, so v1 was one
|||     delta stale. This refresh reads in-force throughout the obligation calculus,
|||     matching s31, and keeps a short note (below, and at hasCloseCur) recording that
|||     v1's raw reading WAS once faithful and is now superseded history, not erased.
|||     (2) R2 -- discharge_grade and edge_type, both trigger-computed/defaulted in SQL,
|||     are now a `Stage` index (`Draft` vs `Recorded`) so a writer-supplied grade is
|||     UNREPRESENTABLE, not merely unconventional. (3) R4 -- the §4 review-obligation
|||     oracle stub is de-stubbed via one total row lookup (`entryAt`); no structural gap
|||     remains in the obligation calculus. (4) R5/R5b -- the in-force projection is
|||     Fin-typed (a question about a nonexistent row is unaskable) and the one theorem
|||     (reinstatement-freedom) is restated and reproved over the refined index.
|||     (5) R6 -- `Projection` now CARRIES its own soundness proof, erased, rather than
|||     asserting it in a comment. (6) R8 -- the write-boundary judgment now carries the
|||     FULL s29/s30/s31 premise family (blocks-close self-edge/dangling/cycle refusals,
|||     strict+deferred contradiction, strict-with-blockers), where v1's comment promised
|||     more than its type. (7) R1/R3 -- two small idiom collapses (the mandatory-iff
|||     `Gated` combinator; the eight nullary prose constructors folded into one
|||     `PProse ProseKind`). Every refinement above is CHECKED (elaborates, zero holes,
|||     zero postulates) -- see the file-level `idris2 --check` witness in the commit
|||     this refresh lands in.
|||
||| UNIVERSE DECISION (the refinement consult's one open call, decided here): RefUniverse
||| .idr renders the kind vocabulary as first-class data (`Kind`) plus one manifest
||| function (`PayloadTy : Kind -> Nat -> Type`) -- a form that matches the SQL
||| substrate's own architecture (one kind column + a family of kind-scoped shape
||| CHECKs) more closely than a fused GADT, and lets a function enumerate "which kinds
||| exist" as a value. This file keeps the FUSED GADT below instead, on readability
||| grounds stated plainly: the maintainer reads this file to fathom the architecture
||| without reading Idris fluently, and a closed sum type -- "here is the list of shapes,
||| each spelling out its own fields" -- is one indirection shallower to read top-to-
||| bottom than a kind tag plus a separate lookup table. The two forms are checked
||| equivalent (RefUniverse.idr, banked alongside this file as the consultation's
||| checked fragment, kept for a reader who wants the universe rendering, or who is
||| about to add many more kinds and would rather edit one manifest than extend one
||| GADT). If the kind vocabulary starts growing fast, revisit this call -- the
||| refinement consult's own finding is that the universe form scales additively where
||| the GADT does not.
|||
||| S33 PARITY PASS (2026-07-15, ledger item autoharn-idr-s33-parity): re-derived directly
||| from kernel/lineage/s33-composite-discharge.sql (the DELTA is the truth transcribed,
||| not the gate author's own prose description of it -- the two divergences
||| gates/idris_model_freshness.py's author flagged when this file was deliberately left
||| at s32 are both closed here). (1) Element 2, STRICT-BY-TYPE: VClose's strict premise
||| now reads the slug's OWN declared work_discharge via `isComposite` (a raw
||| write-boundary read, the same posture `everOpened` already has) and widens to the
||| strict branch whenever the slug is composite, REGARDLESS of the writer-supplied
||| strict flag (quoted inline at both sites) -- a composite hand-close with an
||| unresolved obligation tree now fails to construct even with strict=False (r33a). (2)
||| Element 4: the prior refresh's `effectiveState` was WRONG for a composite item -- it
||| ignored the passed-in `ItemState` entirely and applied the never-hand-closed
||| child-count gate unconditionally. The landed SQL's hand-close branch (`WHEN c.slug IS
||| NOT NULL THEN CASE WHEN EXISTS(blockers) THEN 'open' ELSE 'closed' END`) has NO
||| child-count requirement at all -- re-derived from the SQL lines, quoted at the
||| definition below, not taken on the gate author's description on faith. rc4/rc5/rc6
||| witness the corrected branch (defeat-reopens-a-hand-close,
||| hand-close-respected-once-resolved, zero-children-hand-close-still-closes), none of
||| which the prior code could have produced.
|||
||| PRESERVED, ON PURPOSE (beauty that would erase these is a regression, not a fix):
|||   * The epoch gate stays OUT (s29 sec-10: disposition mandatory iff row id exceeds
|||     an operator-set migration epoch). This renders the POST-EPOCH STEADY STATE only;
|||     the migration accommodation is operator state, not ledger shape.
|||   * The ts-vs-id nonuniformity stays surfaced, not smoothed: `id` is the ONLY
|||     ordering primitive anywhere in this file (ledger_tnow.lp's own "id is the order,
|||     never ts" discipline) -- there is no type here that could even express a
|||     ts-keyed precedence rule, which is stronger than the .lp file's own comment.
|||   * Raw write-boundary reads (`everOpened`, the raw blocks-close cycle walk) stay
|||     RAW, with their s31 allowlist licenses named at each site (`LWriteBoundary`,
|||     `LDuplicateOpen`) -- a BEFORE INSERT trigger cannot read a view excluding the row
|||     being inserted, and slug-burning is deliberately retraction-blind (s31 fork 2).
|||   * The two producers (SQL floor, ASP/clingo side) stay BLACK BOXES (opaque
|||     parameters) -- giving them Idris bodies would replace two independent substrates
|||     with two functions sharing one compiler, one author: the opposite of what the
|||     differential is for.
|||   * `EdgeF Recorded = EdgeType` (every recorded dependency edge has a concrete type)
|||     is honest only for a birth-chain world; a MIGRATED world can carry legacy NULL
|||     edges from before s30. Named here, not hidden.
|||   * The composite-discharge field (`composite : Bool` on an opening act) models
|||     design/FABLE-COMPOSITE-DISCHARGE-SPEC.md as LANDED, kernel/lineage/s33-composite-
|||     discharge.sql (s33 parity pass, header above). The write boundary now enforces
|||     strict-by-type at close (`isComposite`, VClose, Element 2) and `effectiveState`'s
|||     hand-close branch matches Element 4's landed SQL byte-for-byte (no child-count
|||     requirement there -- see its own definition-site comment, quoted from the SQL).
|||     Still preserved, unchanged from the prior refresh: the vacuous-truth foreclosure
|||     for a NEVER-hand-closed zero-child composite (spec sec-3's own named LIMIT), and
|||     the fact that `composite` is a Bool parameter models the declared TYPE, never
|||     inferred from having children (spec's own Rejected list).
|||   * PrincipalId = Nat (unbounded) where the kernel's ids are bigint: numeric RANGE is
|||     out of this model's universe, and s49's defect (an over-bigint digit string
|||     defeating the journaler's own cast) lived precisely in that gap -- the model's
|||     journaler (write, §3b) is total BY THIS IDEALIZATION where the SQL's is total by
|||     s49's local exception guard. Named since the s44-s49 parity pass, not hidden.
|||   * The s46 defeat-input exclusion machinery stays PARAMETERIZED over its exclusion
|||     read even though s50 (row 1647) has adjudicated the horn (raw history, now
|||     instantiated as defeatedRowsKernel/creditedCurrentKernel): the parameter plus the
|||     §2d lemmas are what make the s46->s50 ruling STATABLE and its exact divergence
|||     class provable -- collapsing to the ruled horn would erase the record of what was
|||     ruled between (R7 record-don't-erase).
|||
||| Black-box mocks at every boundary (Postgres, clingo, git, hook transport are
||| opaque). Where the rendering fights the language, the fight is the finding;
||| fidelity notes live inline, keyed to the section numbers below.
module Autoharn

import Data.Fin
import Data.List
import Data.List.Quantifiers
import Data.Nat
import Data.So
import Data.Maybe
import Decidable.Equality

%default total

-- ===========================================================================
-- §0  BLACK-BOX MOCKS. Everything the kernel trusts at runtime but the model
--     does not open: the HMAC stamp (s17/s23 -- secret lives outside the
--     subject role), the two producers' substrates (Postgres, clingo), the
--     hook transport. Modelled as opaque types / function parameters only.
-- ===========================================================================

||| An interception stamp (s17/s23). Opaque: validity is a runtime recompute
||| against a secret the model (like the subject role) cannot read.
data Stamp : Type where
  MkStamp : (session : String) -> (agent : String) -> (hmacHex : String) -> Stamp

||| The s17 stamp_valid SECURITY DEFINER boundary: a boolean oracle, never the
||| secret. The model can only carry the verdict, not derive it.
record StampOracle where
  constructor MkStampOracle
  stampValid : Stamp -> Bool

PrincipalId : Type
PrincipalId = Nat

Slug : Type
Slug = String

-- ===========================================================================
-- §1  KINDS AS A SUM TYPE; KIND-SCOPED SHAPES AS CONSTRUCTOR ARGUMENTS;
--     TRIGGER-COMPUTED FIELDS AS A STAGE INDEX (R1, R2, R3 folded in).
--     SQL says the shape half with one wide nullable table + two-way CHECKs
--     of the form (kind = 'work_closed') = (work_resolution IS NOT NULL),
--     which is a hand-rolled discriminated union; the constructors below say
--     the same thing natively (R1 names the mandatory-iff idiom ONCE, `Gated`,
--     instead of two hand-rolled copies -- s29's own comment: "mirrors s22's
--     ... pattern exactly, one column over"). SQL says the computed-field half
--     with two triggers that overwrite/default a column regardless of what
--     was written; R2's `Stage` index (Draft = what a writer may say, Recorded
--     = what the ledger holds) makes "a writer cannot supply this" a TYPE
--     fact rather than a convention (red fixture r2a below). R3 collapses the
--     eight nullary prose constructors into one `PProse ProseKind` -- the SQL
--     kind list already single-homes them; the GADT should too.
-- ===========================================================================

||| s40: the anchor's closed agent-class vocabulary. In SQL the class lives on the
||| kernel.principal ANCHOR row (immutable by the s40 append-only triggers); this model
||| carries it on the registration EVENT instead -- the model's rendering of the s40
||| anchor-coupling (anchor + event commit atomically, so the event is a faithful witness
||| of the anchor's birth facts). classOf below is the derived read.
data AgentClass = ACHuman | ACModel | ACSubagent | ACTool

Eq AgentClass where
  ACHuman    == ACHuman    = True
  ACModel    == ACModel    = True
  ACSubagent == ACSubagent = True
  ACTool     == ACTool     = True
  _          == _          = False

||| s41 D-2: the closed relation vocabulary (the kernel's OWN refusals key off these
||| values -- contrast the ratified FREE role-name text, which is deliberately a plain
||| String field below, per basis §9(c)/C13).
data Relation = ActsFor | DispatchedBy | SameNaturalPerson | Succeeds

Eq Relation where
  ActsFor           == ActsFor           = True
  DispatchedBy      == DispatchedBy      = True
  SameNaturalPerson == SameNaturalPerson = True
  Succeeds          == Succeeds          = True
  _                 == _                 = False

data ReviewVerdict = Attest | AttestWithReservations | Refuse

isAttest : ReviewVerdict -> Bool
isAttest Attest = True
isAttest _      = False

data Independence = Technical | Managerial | Financial

||| s29 discharge_grade -- COMPUTED at write time by validate_independence(),
||| never writer-asserted (see GradeF below: unrepresentable at Draft stage).
data DischargeGrade = SamePrincipal | SameSession | DistinctSession | DistinctDeployment

||| s22 closed resolution vocabulary.
data Resolution = RShipped | RSuperseded | RDropped | RDeferred

||| s29 Element B + s38: the THREE close constructors. A review-silent close is
||| unrepresentable (post-epoch; see the epoch-gate fidelity note, header).
||| DBookkeeping (s38): a close with NO judgment content, whose witness is a
||| commit-shaped ref (CommitRef below) -- the category is CLOSED to that one
||| form; strictPremise refuses it under strict (the s38 ELSIF).
data ReviewDisposition = DWitnessed | DDeferred | DBookkeeping

||| s30/s39 typed dependency edges; closed vocabulary, 'supersedes' actively
||| refused as a reserved word (a vocabulary refusal the closed data type
||| renders by omission). BlocksStart (s39): the antecedent must be CLOSED
||| before the dependent may be CLAIMED -- a different lifecycle moment than
||| BlocksClose, verified over its own SEPARATE subgraph (s39 Element 2's own
||| two named grounds, preserved: merging the two graphs would false-positive
||| a legal opposite-direction pair).
data EdgeType = BlocksClose | BlocksStart | Informs

Eq EdgeType where
  BlocksClose == BlocksClose = True
  BlocksStart == BlocksStart = True
  Informs     == Informs     = True
  _           == _           = False

||| R3: the s15 prose kinds, single-homed as one constructor's argument.
||| s36 PARITY: KDecision LEAVES this sum -- a decision now has its own
||| constructor (PDecision) because it alone carries a payload column
||| (decision_grade, writer-supplied, kind-scoped by s36's one-way CHECK).
data ProseKind = KAssumption | KQuestion | KVerification
               | KFinding | KSnag | KRevision | KNote

||| Non-empty text (SQL: btrim(x) <> ''). Proof-carrying string.
record NonEmptyText where
  constructor MkNonEmptyText
  text : String
  0 ok : So (text /= "")

||| R1: the mandatory-iff idiom, named once. Gated True a = mandatory (the
||| CHECK's required arm); Gated False a = optional (legal, may be absent).
Gated : Bool -> Type -> Type
Gated True  a = a
Gated False a = Maybe a

isShipped : Resolution -> Bool
isShipped RShipped = True
isShipped _        = False

isWitnessed : ReviewDisposition -> Bool
isWitnessed DWitnessed   = True
isWitnessed DDeferred    = False
isWitnessed DBookkeeping = False

||| s22 work_shipped_requires_witness, via Gated.
witnessTy : Resolution -> Type
witnessTy r = Gated (isShipped r) NonEmptyText

||| s38: the commit-shape refinement (`^commit:[0-9a-f]{7,40}$`, s38's own regex
||| rendered as a boolean the proof-carrying CommitRef demands). First-order
||| character walk so a Refl witness on a concrete string reduces.
isLowerHex : Char -> Bool
isLowerHex c = elem c (unpack "0123456789abcdef")

allChars : (Char -> Bool) -> List Char -> Bool
allChars f []        = True
allChars f (c :: cs) = f c && allChars f cs

isCommitShaped : String -> Bool
isCommitShaped s = case unpack s of
  ('c' :: 'o' :: 'm' :: 'm' :: 'i' :: 't' :: ':' :: rest) =>
    let n = length rest in
    n >= 7 && n <= 40 && allChars isLowerHex rest
  _ => False

||| s38: a bookkeeping close's witness -- a git commit ref, SHAPE-checked at
||| construction (the kernel half; commit EXISTENCE stays a CLI-side check, the
||| honest trust boundary s38's own Element 3 names -- not representable here
||| and not claimed).
record CommitRef where
  constructor MkCommitRef
  ref : String
  0 ok : So (isCommitShaped ref)

||| s41 D-2: an OpenPGP v4 fingerprint (40 uppercase hex chars), shape-checked
||| at construction -- the empty-until-ceremony slot's one regex.
isUpperHex : Char -> Bool
isUpperHex c = elem c (unpack "0123456789ABCDEF")

isV4Fingerprint : String -> Bool
isV4Fingerprint s = let cs = unpack s in
  length cs == 40 && allChars isUpperHex cs

record Fingerprint where
  constructor MkFingerprint
  fp : String
  0 ok : So (isV4Fingerprint fp)

||| s48: the review-witness citation as the CLOSED sum of its three legal
||| forms (s29's own COMMENT ON COLUMN names exactly these: row id, commit
||| hash, or artifact path). The row arm is Fin n -- a citation of a same-or-
||| later (head-guessed) or nonexistent row is UNREPRESENTABLE, which is
||| exactly what s48's trigger enforces for the `row:<id>` sub-shape (existence
||| at INSERT time of a server-assigned id IS "earlier row"). HONESTY NOTES:
||| (1) the SQL approximates the WRRow arm by regex over ONE free-text column
||| (kernel/lineage/s48-review-witness-existence.sql) -- splitting that column
||| into a typed FK + text forms is a FILED kernel proposal (consult, ledger
||| row 1644), maintainer-ratification territory, and this model documents the
||| honest type without claiming the SQL carries it; (2) the commit/artifact
||| arms stay existence-UNCHECKED in SQL (s48's own LIMITS) and are equally
||| unchecked here -- shape-checked only (CommitRef) or free non-empty text;
||| (3) the s48 check also covers work_violation_disposition's work_review_ref,
||| a column this model's PViolationDisposition does not carry (its s37
||| transcription is scoped to the violation columns) -- named, not silent.
data WitnessRef : Nat -> Type where
  WRRow      : Fin n -> WitnessRef n
  WRCommit   : CommitRef -> WitnessRef n
  WRArtifact : NonEmptyText -> WitnessRef n

||| s29/s38/s48 work_review_*_requires_ref: witnessed demands a citation (the
||| three-armed WitnessRef sum), deferred may omit one, bookkeeping demands a
||| COMMIT-SHAPED one (the s38 widening -- a fourth value is unrepresentable,
||| the closed sum). Now n-indexed so the row arm can be Fin-typed (s48).
reviewRefTy : ReviewDisposition -> Nat -> Type
reviewRefTy DWitnessed   n = WitnessRef n
reviewRefTy DDeferred    n = Maybe (WitnessRef n)
reviewRefTy DBookkeeping n = CommitRef

||| R2: Draft = the writer-facing surface; Recorded = what the ledger holds
||| after the recording trigger runs. A writer literally cannot supply a
||| grade (GradeF Draft = ()); an edge type may be omitted at Draft and is
||| always present once Recorded (s30's NULL -> 'informs' default).
data Stage = Draft | Recorded

||| discharge_grade: absent from the writer surface, present in the record.
GradeF : Stage -> Type
GradeF Draft    = ()
GradeF Recorded = DischargeGrade

||| edge_type: optional at the writer surface (trigger defaults), total in
||| the record. HONESTY NOTE (preserved): this is the steady-state/birth-
||| chain reading. A world MIGRATED from before s30 can carry legacy NULL
||| edges this type cannot represent -- the same fidelity choice v1 made,
||| kept and named rather than silently tightened.
EdgeF : Stage -> Type
EdgeF Draft    = Maybe EdgeType
EdgeF Recorded = EdgeType

||| s15 review_detail (frozen-at-insert verdict payload) + s29 grade.
||| antecedent: a typed second place for an affirmation-species review
||| (Maybe = "NULL for a plain countersign", exactly the column).
record ReviewDetail (st : Stage) (n : Nat) where
  constructor MkReviewDetail
  verdict      : ReviewVerdict
  independence : Independence
  basis        : String
  antecedent   : Maybe (Fin n)
  grade        : GradeF st

||| The kind payload of a row with n earlier rows. Every back-reference is a
||| Fin n: a reference to a later or nonexistent row is UNREPRESENTABLE, which
||| is the constructor-idiom rendering of the validate_* "must resolve to an
||| earlier row" trigger family, and makes every closure acyclic by
||| construction (ledger_tnow.lp's "acyclic by construction" comment, here a
||| structural fact rather than a discipline).
|||
||| NOTE the slug-edges asymmetry, kept deliberately: work_depends_on names its
||| antecedent by SLUG (text), not by row id -- and s22 deliberately does NOT
||| refuse a dangling antecedent. So that field is Slug, not Fin n: the model
||| preserves the kernel's own choice of a weakly-typed edge there, because the
||| violations view (depends_on_unknown_slug) exists precisely to read it.
||| s41 D-1a: the competence identity/value split AS A TYPE INDEX. An active
||| grant carries (band, basis) mandatorily; a withdrawal CANNOT carry them at
||| all -- the mandatory-iff-active CHECK pair rendered as unrepresentability
||| rather than a refusal (stronger than the SQL, noted honestly: the SQL
||| refuses at construction, this type cannot even spell the illegal row).
CompetenceValueF : Bool -> Type
CompetenceValueF True  = (NonEmptyText, NonEmptyText)   -- (band, basis), G13's value fields
CompetenceValueF False = ()

||| s44: the closed join-set confidence grade (attest_grade's value CHECK --
||| kernel-structural like s43's refusal_surface: it enumerates the sentry
||| design's own join algebra, never organizational naming). Deliberately
||| UNREAD by the defeat rule (grade-conditioned defeat is ratified
||| direction-only, Q3 -- the s44 column comment's own words).
data AttestGrade = GExactCommand | GTurnBracketed | GSessionScoped | GAmbiguous

||| s44: the verdict, INDEXED by whether an expected model was declared --
||| the structural expectation/verdict coupling ((attest_expected IS NULL) =
||| (attest_verdict = 'unevaluated'), s44's attest_expected_verdict_coupling
||| CHECK) rendered as unrepresentability: an unevaluated verdict WITH a
||| declared expectation, or a match/mismatch claim with nothing to match
||| against, cannot even be spelled (stronger than the SQL, which refuses at
||| construction -- the CompetenceValueF relationship to its CHECK pair,
||| repeated one family over; red fixtures k44c/k44d).
data AttestVerdict : Bool -> Type where
  AVMatch       : AttestVerdict True
  AVMismatch    : AttestVerdict True
  AVUnevaluated : AttestVerdict False

||| s44: the declared expectation, present exactly when the index says so
||| (True = mandatory NonEmptyText, False = cannot carry one at all).
ExpectedF : Bool -> Type
ExpectedF True  = NonEmptyText
ExpectedF False = ()

||| s43: WHICH boundary function caught a refusal -- a closed sum because the
||| SQL's refusal_surface_check is a closed CHECK (kernel-structural: it
||| enumerates the four boundary functions themselves; contrast
||| principal_role_name's ratified free text).
data RefusalSurface = SurfLedger | SurfReview | SurfRegistration | SurfObligation
                    | SurfArtifact  -- s51: the fifth boundary function (artifact_write);
                    -- like SurfObligation it is unreachable from surfaceFor's payload
                    -- families -- an artifact write mints NO ledger row on acceptance,
                    -- only on refusal (digest-only journal), so the surface exists in
                    -- the vocabulary without a payload constructor behind it.

data Payload : (st : Stage) -> (n : Nat) -> Type where
  PProse      : ProseKind -> Payload st n
  ||| s36: a decision row with its writer-supplied durability grade (nullable,
  ||| no vocabulary CHECK -- "the kernel stores a word; which words matter is
  ||| deployment policy", s36's own header, so a plain Maybe String is the
  ||| honest type, not an enum).
  PDecision   : (grade : Maybe String) -> Payload st n
  ||| s37: the typed answering act for a violations-view member. vclass is the
  ||| violation-class word (free text here -- the SQL's own CHECK constrains it
  ||| against work_violation_class's vocabulary via trigger machinery this
  ||| model does not re-derive); target is the answered member's own row, Fin-
  ||| typed so a dangling disposition is unrepresentable; witness (reissued
  ||| successor) stays Maybe -- s37's "warns, never refused".
  PViolationDisposition : (vclass : String) -> (target : Fin n)
                       -> (retired : Bool) -> (witness : Maybe (Fin n))
                       -> Payload st n
  -- s40: the four identity-event kinds. The registration carries the class
  -- (see AgentClass's own note: the model's rendering of the anchor coupling)
  -- and the mandatory non-empty purpose (AC-2's stated-purpose field).
  PPrincipalRegistered : (subject : PrincipalId) -> (cls : AgentClass)
                      -> (purpose : NonEmptyText) -> Payload st n
  ||| s45: a suspension now carries the s41 identity/value discriminator --
  ||| active=True is an in-force-candidate suspension, active=False is a LIFT
  ||| restating the subject (a superseding same-kind row, the s41 retraction
  ||| idiom licensed onto this kind by s45 Element 1). Pre-s45 this model
  ||| could not represent a lift at all, and its nearest encoding (a bare
  ||| second suspension row) read as suspended-forever -- the exact "worse
  ||| than unbuilt" defect s45's own header names.
  PPrincipalSuspended  : (subject : PrincipalId) -> (active : Bool) -> Payload st n
  ||| s45 TERMINAL BY TYPE: a revocation carries NO active flag -- there is no
  ||| lift arm to spell (mirroring principal_binding_active_kind_shape's
  ||| deliberate omission of principal_revoked; red fixture k45a below).
  ||| Succession (s41's succeeds relation + a fresh principal) is the only
  ||| path, as ratified.
  PPrincipalRevoked    : (subject : PrincipalId) -> Payload st n
  ||| the declared-not-silent default: binds a db role (a plain String -- the
  ||| role name is deployment infrastructure, not a modeled identity) to its
  ||| standing principal. s45: carries the discriminator -- active=True is a
  ||| declaration/rotation, active=False is an UNBIND restating BOTH the role
  ||| and the subject (s45 Element 1's fixed semantics).
  PStandingDeclared    : (subject : PrincipalId) -> (dbRole : String)
                      -> (active : Bool) -> Payload st n
  -- s41: the four binding/relation kinds, each indexed by its active flag
  -- (true = assertion, false = retraction restating identity fields only --
  -- the entry-level inactive-needs-supersedes half lives in boundaryOk, §3).
  PRelationAsserted    : (subject : PrincipalId) -> (rel : Relation)
                      -> (object : PrincipalId) -> (active : Bool) -> Payload st n
  ||| roleName is FREE non-empty text BY RATIFIED RULING (basis §9(c)/C13) --
  ||| deliberately NOT a closed sum, the one vocabulary in this family the
  ||| kernel refuses to own.
  PRoleBound           : (subject : PrincipalId) -> (roleName : NonEmptyText)
                      -> (active : Bool) -> Payload st n
  PKeyBound            : (subject : PrincipalId) -> (fingerprint : Fingerprint)
                      -> (active : Bool) -> Payload st n
  PCompetenceGranted   : (subject : PrincipalId) -> (activity : NonEmptyText)
                      -> (active : Bool) -> CompetenceValueF active -> Payload st n
  ||| s43: a refusal the write boundary caught, COMMITTED as an ordinary row
  ||| (the one event class the pre-s43 kernel destroyed by the refusal's own
  ||| abort). Six typed fields, the SQL's six refusal_* columns: sqlstate and
  ||| digest are NonEmptyText here where the SQL refines further by regex
  ||| (^[0-9A-Z]{5}$ / 64-hex -- shape refinements below this rendering's
  ||| altitude, named); the attempted actor is legitimately Maybe (an
  ||| unattributable attempt), the attempted ROLE always known. SINCE THE
  ||| s44-s49 PARITY PASS the boundary's totality invariant ("a refusal
  ||| verdict cannot be delivered unjournaled", s43 §4.4) IS rendered --
  ||| §3b's `write` returns Ledger (S n) on both arms, the refusal arm
  ||| minting exactly this constructor -- superseding this doc's earlier
  ||| out-of-model claim (recorded in the header note). What STAYS out,
  ||| named: the refusal_seq oracle and the journal-INSERT-failure leg (the
  ||| SQL's residual loud-abort + counted-gap path, ./verify-chain's
  ||| reconciliation), and the digest's SHA-256 (an opaque literal here --
  ||| the s42 crypto boundary). s49's overflow guard is also subsumed at
  ||| this constructor's altitude: attemptedActor's resolution is total in
  ||| the model because PrincipalId = Nat is unbounded -- the PRESERVED
  ||| list's Nat-vs-bigint entry names that idealization.
  PWriteRefused : (sqlstate : NonEmptyText) -> (message : NonEmptyText)
               -> (surface : RefusalSurface) -> (digest : NonEmptyText)
               -> (attemptedActor : Maybe PrincipalId)
               -> (attemptedRole : NonEmptyText) -> Payload st n
  ||| s44: a model-identity attestation, the typed defeasible-claim shape.
  ||| target is Fin n -- the SQL's self-table FK (attest_row_id REFERENCES
  ||| ledger(id): "the target's existence is thereby structural, never
  ||| CLI-side", s44's own words) IS this model's signature idiom, met in the
  ||| substrate. model is the observed string VERBATIM (never normalized --
  ||| aliasing is a reader concern); grade/verdict are the two closed
  ||| vocabularies; the expectation/verdict coupling is the hasExpected index
  ||| (AttestVerdict/ExpectedF above). Supersession is deliberately ALLOWED
  ||| (an attestation is a defeasible claim -- s44's argued contrast with
  ||| s43's R6; maySupersede's catch-all arm, §3). CLI-side residue named by
  ||| s44 itself and equally unmodeled here: one-attestation-per-(actor,row)
  ||| and no-self-attestation are cross-row verb-side rules.
  PModelAttested : (target : Fin n) -> (model : NonEmptyText)
                -> (grade : AttestGrade)
                -> (otelSession : NonEmptyText) -> (joinBasis : NonEmptyText)
                -> (hasExpected : Bool) -> (verdict : AttestVerdict hasExpected)
                -> (expected : ExpectedF hasExpected)
                -> Payload st n
  -- s15 review: regards is MANDATORY for kind=review and RESERVED to it --
  -- the two-way trigger check is exactly "this constructor and only this
  -- constructor carries the field".
  PReview     : (regards : Fin n) -> ReviewDetail st n -> Payload st n
  -- s22 work-item event vocabulary + s28 parent + composite-discharge spec.
  PWorkOpened : (slug : Slug) -> (title : String)
             -> (parent : Maybe Slug)          -- s28: set once at opening
             -> (composite : Bool)             -- s33-composite-discharge.sql, LANDED:
                                                -- read by isComposite (VClose, §3) and
                                                -- effectiveState (§4).
             -> Payload st n
  PWorkClaimed : (slug : Slug) -> Payload st n
  PWorkDepends : (slug : Slug) -> (antecedent : Slug) -> EdgeF st -> Payload st n
  PWorkClosed  : (slug : Slug)
              -> (res : Resolution) -> witnessTy res
              -> (disp : ReviewDisposition) -> reviewRefTy disp n  -- s48: n-indexed
              -> (strict : Bool)                -- s29 opt-in per close act
              -> Payload st n

||| One ledger row with n earlier rows. ts is deliberately OMITTED from
||| anything that orders: id-is-order, never ts (ledger_tnow.lp header,
||| preserved as the "ts-vs-id nonuniformity" fidelity note, header above).
record Entry (st : Stage) (n : Nat) where
  constructor MkEntry
  session    : String
  statement  : String
  actor      : PrincipalId
  stamp      : Maybe Stamp
  supersedes : Maybe (Fin n)          -- FK is the ONE write constraint (spec §4)
  amends     : Maybe (Fin n, String)  -- target + verbatim quotation
  answers    : Maybe (Fin n)
  enacts     : List (Fin n)
  payload    : Payload st n

||| §1 THE LEDGER: indexed append-only structure. The ledger holds RECORDED
||| rows only -- a Draft never lands unprocessed (R2). There is no
||| update/delete constructor at all -- append_only() as absence of syntax
||| rather than a refusing trigger, and one_row_per_insert is inherent in the
||| single-row shape of (:<).
data Ledger : Nat -> Type where
  Lin  : Ledger 0
  (:<) : Ledger n -> Entry Recorded n -> Ledger (S n)

-- ===========================================================================
-- §2  THE IN-FORCE PROJECTION AS A TOTAL FUNCTION, Fin-TYPED (R5), AND THE
--     PROOF-CARRYING READER TYPES (R6).
--     ledger_tnow.lp: superseded(Y) :- sup_star(_,Y);
--                     in_force(Id) :- entry(Id,...), not superseded(Id).
--     Note superseded/1 is MONOTONE: it quantifies over edge EXISTENCE only,
--     never over the superseder's own in-force status. That monotonicity IS
--     reinstatement-freedom (§5).
-- ===========================================================================

||| Reduction-transparent strengthen (base library's `strengthen` is `export`,
||| not `public export`, so it cannot reduce in a Refl proof outside
||| Data.Fin itself -- a toolchain fact from the refinement consult; every
||| Refl witness in §7 relies on this local copy reducing).
public export
strong : {n : Nat} -> Fin (S n) -> Maybe (Fin n)
strong {n = S _} FZ     = Just FZ
strong {n = S _} (FS p) = map FS (strong p)
strong _                = Nothing

||| Is absolute row t superseded by any row of l (R5: t is now a Fin n --
||| asking about a row that does not exist is unrepresentable, not merely
||| false)? Positive/monotone: the superseder's own later defeat is
||| irrelevant by construction.
supersededIn : {n : Nat} -> Ledger n -> Fin n -> Bool
supersededIn Lin      t = absurd t
supersededIn (l :< e) t =
     maybe False (\f => finToNat f == finToNat t) e.supersedes
  || (case strong t of
        Nothing => False
        Just t' => supersededIn l t')

||| The in-force projection, total by construction (a fold over finitely many
||| rows; no termination debt -- SQL pays none either, ASP pays a comment).
inForce : {n : Nat} -> Ledger n -> Fin n -> Bool
inForce l t = not (supersededIn l t)

allIds : (n : Nat) -> List (Fin n)
allIds Z     = []
allIds (S k) = FZ :: map FS (allIds k)

||| R6: §2 READER TYPING (the ratified judgment of the supersession spec §2),
||| now CARRYING its own soundness rather than asserting it in a comment. A
||| current-truth reader receives ONLY this type; `project` is the sole
||| introduction form (in a multi-module rendering `MkProjection` would not
||| be exported, so "never touches raw ledger" is a scope fact, not a review
||| rule), and every id it carries is erased-proved in force.
record Projection {n : Nat} (l : Ledger n) where
  constructor MkProjection
  liveIds : List (Fin n)
  0 sound : All (\t => inForce l t = True) liveIds

keepLive : {n : Nat} -> (l : Ledger n) -> (ids : List (Fin n))
        -> (out : List (Fin n) ** All (\t => inForce l t = True) out)
keepLive l [] = ([] ** [])
keepLive l (t :: ts) with (inForce l t) proof p
  keepLive l (t :: ts) | True  = let (out ** prf) = keepLive l ts
                                 in (t :: out ** p :: prf)
  keepLive l (t :: ts) | False = keepLive l ts

project : {n : Nat} -> (l : Ledger n) -> Projection l
project l = let (out ** prf) = keepLive l (allIds n) in MkProjection out prf

||| A history/forensic reader is NAMED on a closed allowlist with its reason:
||| the spec's §2 list as a closed indexed type, extended (comment only, no
||| new constructor needed) by s31/s32's own allowlist entries
||| (gates/ledger_reader_allowlist.py): work_edge_parent/work_edge_blocks_close
||| are RAW by the same LWriteBoundary-shaped reasoning -- a cycle check or a
||| structural-existence question must see every edge ever written, retracted
||| or not. Adding a history reader means adding a constructor here -- the
||| diff IS the allowlist amendment.
data HistoryLicense : String -> Type where
  LHashChain      : HistoryLicense "row-hash-chain: every row must chain, superseded or not"
  LLedRecent      : HistoryLicense "led --recent: displays and MARKS superseded rows"
  LDuplicateOpen  : HistoryLicense "duplicate_open arm + trigger: a retracted open still burns its slug"
  LWriteBoundary  : HistoryLicense "BEFORE INSERT triggers: cannot read a view excluding the row being inserted"
  ||| s50 (ruling row 1647): "was this row ever machinery input" is a HISTORY
  ||| fact -- later supersession cannot retroactively un-input it; the exact
  ||| LDuplicateOpen-shaped reasoning, one mechanism over. Licenses the raw
  ||| defeat-input exclusion read (defeatInputRaw, §2d) that s50 re-points
  ||| the s46 kernel view onto.
  LDefeatInput    : HistoryLicense "defeat-input exclusion: ever-machinery-input is a history fact (s50)"

||| The two reader signatures. currentReader CANNOT mention Ledger at all;
||| historyReader must present its license.
CurrentReader : {n : Nat} -> (l : Ledger n) -> Type -> Type
CurrentReader l a = Projection l -> a

HistoryReader : Nat -> Type -> Type
HistoryReader n a = {reason : String} -> HistoryLicense reason -> Ledger n -> a

-- ===========================================================================
-- §2b THE OBLIGATION AND-TREE (work_item_strict_blockers, s29 narrowed by
--     s30, RE-ISSUED IN FORCE by s31/s32) AS A DERIVED FOLD (R4, R7 folded
--     in). Placed here, ahead of §3, because the write boundary's strict-
--     close premise (below) reads this calculus directly -- the SQL trigger
--     calls the same STABLE function, so the model's definition order
--     mirrors that dependency rather than the kernel's own narrative order.
--
--     R7 FIDELITY FIX, RECORDED NOT ERASED: v1 deliberately transcribed the
--     s30-era "closes" CTE reading RAW history (composite-spec §3b's named
--     blind spot: a defeated close still read closed) -- that WAS the
--     kernel's real behavior when v1 was written. s31 (ratified the same
--     day) re-issued edges/closes to read ledger_current; the blind spot is
--     no longer live substrate behavior, so this refresh reads IN FORCE
--     throughout (hasCloseCur, edgesCur below), matching s31 Elements 1/2,
--     and matching s32's single-homed work_edge_obligation/discharging_attest
--     views functionally (this file's edgesCur/deferredUndischarged are the
--     Idris analogs of those two SQL views).
--
--     R4: the review-obligation leaf was a stub (returns False) in v1,
--     declared honestly as needing "absolute row ids threaded through the
--     fold". `entryAt` below closes that gap with one total lookup: prefix
--     position in a `Ledger n` index already IS the absolute row id.
-- ===========================================================================

||| Reachable set with fuel. ENCODING NOISE, named: SQL's recursive CTE
||| terminates by set semantics for free even on cyclic input; Idris %default
||| total demands a decreasing measure, so the walk carries fuel = row count
||| (a sound bound: each productive step adds a slug drawn from finitely many
||| rows).
reach : (fuel : Nat) -> List (Slug, Slug) -> (frontier : List Slug)
     -> (seen : List Slug) -> List Slug
reach Z     _  _        seen = seen
reach (S k) es frontier seen =
  let next = [ c | (p, c) <- es, elem p frontier, not (elem c seen) ] in
  case next of
    [] => seen
    _  => reach k es next (seen ++ next)

||| The entry at absolute row id t (prefix size existentially packed).
entryAt : {n : Nat} -> Ledger n -> Fin n -> (m ** Entry Recorded m)
entryAt Lin      t = absurd t
entryAt (l :< e) t = case strong t of
                       Nothing => (_ ** e)
                       Just t' => entryAt l t'

||| First-order any (Prelude's Foldable `any` does not reduce under Refl).
anyB : (a -> Bool) -> List a -> Bool
anyB f []        = False
anyB f (x :: xs) = f x || anyB f xs

||| s31 Element 2 / s32 work_edge_obligation: both edge arms (s28 parent,
||| s30 blocks-close) read IN FORCE only -- a retracted parent or
||| blocks-close edge no longer feeds the AND-tree.
edgesCur : {n : Nat} -> Ledger n -> List (Slug, Slug)
edgesCur l = concatMap edgeAt (allIds n)
  where
    edgeAt : Fin n -> List (Slug, Slug)
    edgeAt t = if inForce l t
               then case entryAt l t of
                      (_ ** e) => case e.payload of
                        PWorkOpened c _ (Just p) _        => [(p, c)]
                        PWorkDepends dep ant BlocksClose  => [(dep, ant)]
                        _                                 => []
               else []

||| s31 Element 2: does slug s have an IN-FORCE close row? A retracted close
||| no longer counts as "this member is closed" (the fixed blind spot; see
||| the R7 note above and the r7 fixtures in §7 which prove the divergence
||| from the pre-s31 raw reading at compile time).
hasCloseCur : {n : Nat} -> Ledger n -> Slug -> Bool
hasCloseCur l s = anyB closesHere (allIds n)
  where
    closesHere : Fin n -> Bool
    closesHere t = inForce l t &&
      (case entryAt l t of
         (_ ** e) => case e.payload of
                       PWorkClosed s' _ _ _ _ _ => s == s'
                       _                        => False)

||| The de-stubbed review leg (R4): an in-force deferred close of s with NO
||| in-force distinct-actor attest regarding it -- s29's review_unresolved
||| CTE / s32's discharging_attest view, composed here rather than
||| re-derived. CHECKED, not an oracle: the absolute ids come from entryAt,
||| nothing was structurally missing once the fold could address rows.
deferredUndischarged : {n : Nat} -> Ledger n -> Slug -> Bool
deferredUndischarged l s = anyB bad (allIds n)
  where
    attests : (closeId : Nat) -> (closer : PrincipalId) -> Fin n -> Bool
    attests c closer r = inForce l r &&
      (case entryAt l r of
         (_ ** e) => case e.payload of
           PReview regards d => finToNat regards == c
                             && isAttest d.verdict
                             && not (e.actor == closer)
           _                 => False)
    bad : Fin n -> Bool
    bad t = inForce l t &&
      (case entryAt l t of
         (_ ** e) => case e.payload of
           PWorkClosed s' _ _ DDeferred _ _ =>
             s == s' && not (anyB (attests (finToNat t) e.actor) (allIds n))
           _ => False)

record Blocker where
  constructor MkBlocker
  blockingSlug : Slug
  reason       : String

||| ADR-0012 P1: still the ONE home of "is this item's obligation tree
||| resolved" -- now with BOTH legs on the SAME (in-force) quantification
||| domain, as s31 ratified and s32 single-homed. Empty iff resolved.
strictBlockers : {n : Nat} -> Ledger n -> Slug -> List Blocker
strictBlockers {n} l root =
  let members   = reach n (edgesCur l) [root] [root]
      notRoot   = filter (/= root) members
      notClosed = [ MkBlocker s "item is not yet closed"
                  | s <- notRoot, not (hasCloseCur l s) ]
      reviewUn  = [ MkBlocker s "review disposition deferred and undischarged"
                  | s <- members, deferredUndischarged l s ]
  in  notClosed ++ reviewUn

-- ===========================================================================
-- §2c  THE s36-s41 DERIVED READS (the parity pass's new section; every read
--      here is a CURRENT-TRUTH fold over the in-force projection, matching
--      the SQL views' own ledger_current factoring -- except where a read is
--      EXPLICITLY the record/history side, named at its definition).
-- ===========================================================================

||| s36 standing_decisions: the in-force graded decisions, as absolute row
||| ids rendered to Nat (so a Refl fixture compares plain lists).
standingDecisionIds : {n : Nat} -> Ledger n -> List Nat
standingDecisionIds l = [ finToNat t | t <- allIds n, graded t ]
  where
    graded : Fin n -> Bool
    graded t = inForce l t &&
      (case entryAt l t of
         (_ ** e) => case e.payload of
                       PDecision (Just _) => True
                       _                  => False)

||| s37, the debt/record split -- modeled on the ONE violations-view member
||| this model can even represent: depends_on_unknown_slug (a dangling
||| work_depends_on antecedent; s22 deliberately leaves it unrefused, so the
||| view is its only home). Most other members are UNREPRESENTABLE here by the
||| model's own types (a shipped close without witness cannot construct; a
||| Fin-typed regards cannot dangle) -- which is the model AGREEING with the
||| views' purpose, not a transcription gap: the SQL views watch for states
||| the SQL types permit, and this model forecloses most of them upstream.
||| DEBT (work_item_violations' semantics): in-force dangling deps, MINUS
||| those answered by an in-force disposition targeting them.
danglingDepDebt : {n : Nat} -> Ledger n -> List Nat
danglingDepDebt l = [ finToNat t | t <- allIds n, dangling t, not (disposed t) ]
  where
    dangling : Fin n -> Bool
    dangling t = inForce l t &&
      (case entryAt l t of
         (_ ** e) => case e.payload of
                       PWorkDepends _ ant _ => not (everOpenedAt ant)
                       _                    => False)
      where
        everOpenedAt : Slug -> Bool
        everOpenedAt s = anyB opens (allIds n)
          where
            opens : Fin n -> Bool
            opens u = case entryAt l u of
                        (_ ** e2) => case e2.payload of
                                       PWorkOpened s' _ _ _ => s == s'
                                       _                    => False
    disposed : Fin n -> Bool
    disposed t = anyB answers (allIds n)
      where
        answers : Fin n -> Bool
        answers u = inForce l u &&
          (case entryAt l u of
             (_ ** e) => case e.payload of
                           PViolationDisposition _ tgt _ _ => finToNat tgt == finToNat t
                           _                               => False)

||| RECORD (work_violation_history's semantics): every dangling dep EVER
||| surfaced, disposition or not, retraction or not -- raw, never thinner
||| than debt (s37's own invariant, here a structural consequence of the
||| missing filters).
danglingDepHistory : {n : Nat} -> Ledger n -> List Nat
danglingDepHistory l = [ finToNat t | t <- allIds n, dangling t ]
  where
    dangling : Fin n -> Bool
    dangling t = case entryAt l t of
      (_ ** e) => case e.payload of
        PWorkDepends _ ant _ => not (anyB (opens ant) (allIds n))
        _                    => False
      where
        opens : Slug -> Fin n -> Bool
        opens s u = case entryAt l u of
                      (_ ** e2) => case e2.payload of
                                     PWorkOpened s' _ _ _ => s == s'
                                     _                    => False

||| s40 principal standing -- the derived read (kernel.principal_standing).
||| REVOKED DOMINATES SUSPENDED (checked first -- strict severity ordering,
||| never event recency, s40 §3.4); PsUnregisteredLegacy (an actor with no
||| in-force registration event) is treated as ACTIVE by the write boundary
||| (a legacy 'author' is never bricked -- boundaryOk below).
data Standing = PsActive | PsSuspended | PsRevoked | PsUnregisteredLegacy

principalStanding : {n : Nat} -> Ledger n -> PrincipalId -> Standing
principalStanding l p =
  if      anyB revokedHere   (allIds n) then PsRevoked
  else if anyB suspendedHere (allIds n) then PsSuspended
  else if anyB registeredHere (allIds n) then PsActive
  else PsUnregisteredLegacy
  where
    revokedHere : Fin n -> Bool
    revokedHere t = inForce l t &&
      (case entryAt l t of
         (_ ** e) => case e.payload of
                       PPrincipalRevoked s => s == p
                       _                   => False)
    -- s45 Element 3, the in-force filter: a LIFT row (same kind, active=False,
    -- itself the terminal unsuperseded row of its chain) must NOT read as
    -- suspended -- hence the True pattern. Without it a lifted suspension
    -- reads suspended forever, "worse than unbuilt" (s45's own words). The
    -- revoked leg above needs no such filter: revocations carry no flag
    -- (terminal by type), so bare kind-existence is, and remains, correct.
    -- (principal_standing_basis, s45's second function -- the governing
    -- event-row id read feeding set_actor's refusal message -- is not
    -- rendered: teach-text plumbing below this transcription's altitude; its
    -- one semantic subtlety, the kind-AWARE in-force filter that must not
    -- drop flag-less revocations, is the same rule this pattern pair carries.)
    suspendedHere : Fin n -> Bool
    suspendedHere t = inForce l t &&
      (case entryAt l t of
         (_ ** e) => case e.payload of
                       PPrincipalSuspended s True => s == p
                       _                          => False)
    registeredHere : Fin n -> Bool
    registeredHere t = inForce l t &&
      (case entryAt l t of
         (_ ** e) => case e.payload of
                       PPrincipalRegistered s _ _ => s == p
                       _                          => False)

||| s40: the anchor class, read off the first in-force registration event
||| (the model's home for the immutable-at-birth class -- see AgentClass).
classOf : {n : Nat} -> Ledger n -> PrincipalId -> Maybe AgentClass
classOf l p = go (allIds n)
  where
    go : List (Fin n) -> Maybe AgentClass
    go [] = Nothing
    go (t :: ts) =
      if inForce l t
        then case entryAt l t of
               (_ ** e) => case e.payload of
                             PPrincipalRegistered s c _ =>
                               if s == p then Just c else go ts
                             _ => go ts
        else go ts

||| s40 §3.6: which standings accept writes. unregistered-legacy is ACTIVE
||| for write purposes (never bricked); suspended/revoked refuse.
writeAllowed : Standing -> Bool
writeAllowed PsActive             = True
writeAllowed PsUnregisteredLegacy = True
writeAllowed PsSuspended          = False
writeAllowed PsRevoked            = False

||| s39: root's own DIRECT, in-force blocks-start antecedents not yet closed
||| (work_item_blocks_start_blockers -- direct only, not transitive, the SQL's
||| own named LIMIT preserved).
startBlockers : {n : Nat} -> Ledger n -> Slug -> List Slug
startBlockers l root =
  [ ant | (dep, ant) <- bsEdgesCur, dep == root, not (hasCloseCur l ant) ]
  where
    bsEdgesCur : List (Slug, Slug)
    bsEdgesCur = concatMap edgeAt (allIds n)
      where
        edgeAt : Fin n -> List (Slug, Slug)
        edgeAt t = if inForce l t
                   then case entryAt l t of
                          (_ ** e) => case e.payload of
                            PWorkDepends dep ant BlocksStart => [(dep, ant)]
                            _                                => []
                   else []

||| s39 work_startable's predicate half: no unresolved blocks-start
||| antecedent (the open+unclaimed half of the SQL view lives in the
||| projection-side ItemState fold this file deliberately leaves uncomputed --
||| §4's own posture, unchanged).
startable : {n : Nat} -> Ledger n -> Slug -> Bool
startable l s = null (startBlockers l s)

-- ===========================================================================
-- §2d  THE s44/s45/s46 DERIVED READS. Three families: the s45 THREE-VALUED
--      row-force refinement and the resurrection-proof governing-role read;
--      the s44 attestation surface; the s46 defeat calculus, with the
--      defeat-input quantification fork rendered as a PARAMETER and its
--      agree/diverge boundary as machine-checked lemmas -- the fork itself is
--      deliberately NOT adjudicated here (the maintainer's call, s46's own
--      named spec-silent choice).
-- ===========================================================================

||| s45: the three-valued refinement of the boolean in-force read that the
||| standing-lifecycle machinery needs -- superseded / unsuperseded-inactive
||| (a retraction row standing as ABSENCE, never force) / unsuperseded-active.
||| The Bool `inForce` collapses the last two; s45's governing-row semantics
||| cannot be stated without separating them.
data RowForce = RFSuperseded | RFRetracted | RFAsserting

||| Which payloads carry the s41/s45 identity/value discriminator (the six
||| kinds of principal_binding_active_kind_shape as re-issued by s45 Element 1
||| -- four s41 binding kinds + the two lifecycle kinds licensed there;
||| principal_revoked's absence from this list IS the terminal-by-type fact).
activeFlagOf : Payload st m -> Maybe Bool
activeFlagOf (PRelationAsserted _ _ _ a)  = Just a
activeFlagOf (PRoleBound _ _ a)           = Just a
activeFlagOf (PKeyBound _ _ a)            = Just a
activeFlagOf (PCompetenceGranted _ _ a _) = Just a
activeFlagOf (PStandingDeclared _ _ a)    = Just a
activeFlagOf (PPrincipalSuspended _ a)    = Just a
activeFlagOf _                            = Nothing

rowForce : {n : Nat} -> Ledger n -> Fin n -> RowForce
rowForce l t =
  if supersededIn l t then RFSuperseded
  else case entryAt l t of
         (_ ** e) => case activeFlagOf e.payload of
                       Just False => RFRetracted
                       _          => RFAsserting

||| First-order "last match wins" (highest id -- allIds is ascending; the
||| recursion takes the TAIL's answer first, so the latest candidate wins).
lastJust : (a -> Maybe b) -> List a -> Maybe b
lastJust f []        = Nothing
lastJust f (x :: xs) = case lastJust f xs of
                         Just y  => Just y
                         Nothing => f x

||| s45 Element 2, kernel.principal_role RESURRECTION-PROOF: the governing
||| row per db_role is the LATEST UNSUPERSEDED declaration REGARDLESS of its
||| active flag; it is emitted ONLY if that governing row is itself active.
||| THE TRAP, structural here where the SQL carries it as a comment ("the
||| max(lc2.id) subquery ... must never gain an active filter itself"): a
||| candidate is discarded ONLY for being superseded -- an RFRetracted unbind
||| row still GOVERNS (and yields Nothing), which is exactly what forecloses
||| the resurrection of the next-oldest declaration nobody chose (g45a below).
||| Re-bind after unbind works by construction: a later fresh declaration is a
||| higher-id asserting candidate (g45c).
principalRole : {n : Nat} -> Ledger n -> (dbRole : String) -> Maybe PrincipalId
principalRole l role =
  case lastJust governCandidate (allIds n) of
    Just (subj, RFAsserting) => Just subj
    _                        => Nothing
  where
    governCandidate : Fin n -> Maybe (PrincipalId, RowForce)
    governCandidate t = case rowForce l t of
      RFSuperseded => Nothing     -- the ONLY discard: superseded never governs
      f => case entryAt l t of
        (_ ** e) => case e.payload of
          PStandingDeclared s r _ => if r == role then Just (s, f) else Nothing
          _                       => Nothing

||| s44 model_attestations (display surface, ledger_current-factored): one
||| (attestation row id, attested row id) pair per IN-FORCE attestation.
modelAttestations : {n : Nat} -> Ledger n -> List (Nat, Nat)
modelAttestations l = concatMap att (allIds n)
  where
    att : Fin n -> List (Nat, Nat)
    att t = if inForce l t
            then case entryAt l t of
                   (_ ** e) => case e.payload of
                     PModelAttested tgt _ _ _ _ _ _ _ => [(finToNat t, finToNat tgt)]
                     _                                => []
            else []

||| s46: does principal p hold an in-force, ACTIVE competence grant for the
||| one fixed defeat activity (spec §5.2's literal)? The I1 two-conjunct: the
||| active flag is a same-row fact, "not superseded" is the projection's --
||| kept structurally apart exactly as the trust-grant entry demands.
hasDefeatGrant : {n : Nat} -> Ledger n -> PrincipalId -> Bool
hasDefeatGrant l p = anyB g (allIds n)
  where
    g : Fin n -> Bool
    g t = inForce l t &&
      (case entryAt l t of
         (_ ** e) => case e.payload of
           PCompetenceGranted s act True _ =>
             s == p && act.text == "model-identity-attestation"
           _ => False)

||| s46's defeat-input law (spec §10 law 2): the machinery's input KINDS are
||| outside its target domain. Kind-level, exactly the SQL's IN-list.
isDefeatInputP : Payload st m -> Bool
isDefeatInputP (PModelAttested _ _ _ _ _ _ _ _) = True
isDefeatInputP (PCompetenceGranted _ _ _ _)     = True
isDefeatInputP _                                = False

||| THE FORK, both horns, named after s46's own ELEMENT 1 disclosure -- and
||| ADJUDICATED while this pass was in flight: s50 (kernel/lineage/
||| s50-defeat-input-raw-domain.sql, ruling row 1647) re-points the kernel
||| view's exclusion onto RAW HISTORY, the engine producers' own domain,
||| on exactly the LDuplicateOpen-class ground the LDefeatInput license
||| carries -- "ever machinery input" is a history fact, and the direction is
||| fail-safe (raw excludes strictly MORE, nothing becomes newly defeatable;
||| lemma 3 below is the machine-checked form of "strictly more").
||| defeatInputRaw is therefore THE KERNEL SEMANTICS as of s50;
||| defeatInputCur is the superseded s46-era reading, KEPT (R7 record-don't-
||| erase) because the parameterized machinery below is what makes the
||| s46->s50 ruling statable and its boundary provable.
defeatInputRaw : {n : Nat} -> Ledger n -> Fin n -> Bool
defeatInputRaw l t = case entryAt l t of (_ ** e) => isDefeatInputP e.payload

defeatInputCur : {n : Nat} -> Ledger n -> Fin n -> Bool
defeatInputCur l t = inForce l t && defeatInputRaw l t

andTrueL : (b : Bool) -> (True && b) = b
andTrueL True  = Refl
andTrueL False = Refl

andFalseR : (b : Bool) -> (b && False) = False
andFalseR True  = Refl
andFalseR False = Refl

||| Fork-boundary lemma 1: on any IN-FORCE row the two exclusion reads agree.
inputsAgreeInForce : {n : Nat} -> (l : Ledger n) -> (t : Fin n)
                  -> inForce l t = True
                  -> defeatInputCur l t = defeatInputRaw l t
inputsAgreeInForce l t prf = rewrite prf in andTrueL (defeatInputRaw l t)

||| Fork-boundary lemma 2: on any NON-defeat-kind row the two reads agree
||| (both False -- an ordinary row is nobody's protected input).
inputsAgreeNonInput : {n : Nat} -> (l : Ledger n) -> (t : Fin n)
                   -> defeatInputRaw l t = False
                   -> defeatInputCur l t = False
inputsAgreeNonInput l t prf = rewrite prf in andFalseR (inForce l t)

||| Fork-boundary lemma 3: on a SUPERSEDED row the current-scoped read is
||| always False -- so with lemmas 1/2, the two horns diverge EXACTLY on
||| superseded defeat-kind rows (cur=False, raw=True there, nowhere else).
||| DESIGN-PROBE RECORD (found by this pass, now moot in effect but kept as
||| the record): s46's header characterized the divergence as "a kind CHANGE
||| across a supersession chain" -- but membership in the SQL view's NOT-IN
||| set is by ROW ID, and a row's kind never changes, so ANY superseded
||| attestation/grant target diverged, same-kind supersession included --
||| strictly wider than the stated class. The s50 ruling (row 1647) unifies
||| the domains, dissolving the divergence entirely; its "vanishingly narrow"
||| spirit had survived anyway (c46b/c46c: the fork was INVISIBLE to
||| credited_current, reaching only the with-cause display surface).
inputsDivergeSuperseded : {n : Nat} -> (l : Ledger n) -> (t : Fin n)
                       -> supersededIn l t = True
                       -> defeatInputCur l t = False
inputsDivergeSuperseded l t prf =
  let 0 ifPrf : (inForce l t = False)
      ifPrf = cong not prf
  in rewrite ifPrf in Refl

||| The exclusion reads as Nat-keyed adapters (encoding noise, named: the
||| attestation's target lives at the entry's OWN prefix index m, so the
||| defeat fold below compares absolute ids as Nat, exactly as the s37/R4
||| folds already do).
rawInputAt : {n : Nat} -> Ledger n -> Nat -> Bool
rawInputAt l k = anyB (\u => finToNat u == k && defeatInputRaw l u) (allIds n)

curInputAt : {n : Nat} -> Ledger n -> Nat -> Bool
curInputAt l k = anyB (\u => finToNat u == k && defeatInputCur l u) (allIds n)

||| s46 model_defeated_rows, the with-cause surface: one (defeated row id,
||| attestation row id) pair per in-force MISMATCH attestation whose actor
||| holds the defeat grant, minus excluded targets -- the exclusion read is
||| the caller's horn of the fork. (The SQL view also carries grant id,
||| model, grade -- display columns this pair-shaped rendering omits; the
||| JUDGMENT half is complete.)
defeatedRows : {n : Nat} -> (excludeTarget : Nat -> Bool) -> Ledger n
            -> List (Nat, Nat)
defeatedRows excl l = concatMap d (allIds n)
  where
    d : Fin n -> List (Nat, Nat)
    d a = if inForce l a
          then case entryAt l a of
            (_ ** e) => case e.payload of
              PModelAttested tgt _ _ _ _ True AVMismatch _ =>
                if hasDefeatGrant l e.actor && not (excl (finToNat tgt))
                  then [(finToNat tgt, finToNat a)]
                  else []
              _ => []
          else []

||| s46 credited_current: ledger_current minus every defeated row id --
||| computed fresh, nothing stored, no write gated, the underlying row never
||| touched (the spec's own serving-option-(c) sentence).
creditedCurrentIds : {n : Nat} -> (excludeTarget : Nat -> Bool) -> Ledger n
                  -> List Nat
creditedCurrentIds excl l =
  [ finToNat t | t <- allIds n, inForce l t
               , not (anyB (\p => fst p == finToNat t) (defeatedRows excl l)) ]

||| s50: the ADJUDICATED kernel semantics -- the parameterized machinery
||| instantiated at the ruled horn (raw history). These two are what an s50+
||| world's model_defeated_rows / credited_current compute.
defeatedRowsKernel : {n : Nat} -> Ledger n -> List (Nat, Nat)
defeatedRowsKernel l = defeatedRows (rawInputAt l) l

creditedCurrentKernel : {n : Nat} -> Ledger n -> List Nat
creditedCurrentKernel l = creditedCurrentIds (rawInputAt l) l

-- ===========================================================================
-- §3  THE WORK-ITEM EVENT GRAMMAR AS A RELATIONAL WRITE BOUNDARY (R8).
--     TRANSCRIPTION FINDING (kernel wins over the elegant rendering): the
--     kernel's write-boundary grammar is NOT linear open->claim->close.
--     validate_work_item() (s22..s31) refuses exactly:
--       * a second work_opened for a slug that EVER had one (raw read: burned,
--         s31 fork 2 -- retraction-blind on purpose)
--       * claim/depends/close on a never-opened slug
--       * (s28) a dangling or cycle-forming parent at open
--       * (s30) a blocks-close self-edge / dangling antecedent / cycle (raw
--         walk against history, matching work_depends_on_would_cycle())
--       * (s29) a post-epoch close with no disposition; strict+deferred;
--         strict close with a non-empty blocker set (IN-FORCE, s31 Element 2)
--     It does NOT require a claim before close, does NOT refuse a second
--     claim, and does NOT refuse a second close row. Linearity lives in the
--     PROJECTION (latest-event fold, work_item_current), not the write
--     boundary. R8 folds in the full premise family v1's comment enumerated
--     but its type did not carry -- ValidPayload is now indexed directly by
--     the Payload constructor it licenses, so the shape checks v1 needed
--     (isOpenOf/isLaterEventOf) are subsumed by the index itself.
-- ===========================================================================

||| Raw-history slug facts (HISTORY readers by the ratified fork: a superseded
||| open still counts -- LDuplicateOpen -- the quantification domain is the
||| raw ledger, which is exactly how "slug burned" appears in the model: not
||| a new mechanism but WHICH structure the freshness proof quantifies over).
everOpened : Ledger n -> Slug -> Bool
everOpened Lin      _ = False
everOpened (l :< e) s = isOpen e.payload || everOpened l s
  where
    isOpen : Payload st m -> Bool
    isOpen (PWorkOpened s' _ _ _) = s == s'
    isOpen _                      = False

||| s33 Element 2 -- STRICT-BY-TYPE, the read half. RAW write-boundary read of
||| slug s's OWN work_opened row's declared discharge -- the SAME posture
||| `everOpened` already has (a BEFORE INSERT trigger cannot read a view
||| excluding the row being inserted; composite-ness is set exactly once, at
||| opening, s33 Element 1, so the raw domain is also the correct one, not
||| merely the only available one). QUOTE (s33-composite-discharge.sql, lines
||| 374-377): "IF NEW.kind = 'work_closed' THEN is_composite := EXISTS (SELECT
||| 1 FROM ledger WHERE kind = 'work_opened' AND work_slug = NEW.work_slug AND
||| work_discharge = 'composite'); END IF;" -- rendered here as a plain fold
||| over the SAME raw ledger everOpened walks.
isComposite : Ledger n -> Slug -> Bool
isComposite Lin      _ = False
isComposite (l :< e) s = isCompOpen e.payload || isComposite l s
  where
    isCompOpen : Payload st m -> Bool
    isCompOpen (PWorkOpened s' _ _ True) = s == s'
    isCompOpen _                         = False

||| Raw blocks-close reachability, seeded at `from` (LWriteBoundary: a BEFORE
||| INSERT trigger cannot read a view excluding the row being inserted, so
||| the cycle check -- s30's work_depends_on_would_cycle -- is a declared RAW
||| walk even after s31; matches s32's work_edge_blocks_close, kept RAW there
||| for the identical reason).
bcReach : {n : Nat} -> Ledger n -> (from : Slug) -> List Slug
bcReach l from = reach n bcEdges [from] [from]
  where
    bcEdges : List (Slug, Slug)
    bcEdges = concatMap edgeAt (allIds n)
      where
        edgeAt : Fin n -> List (Slug, Slug)
        edgeAt t = case entryAt l t of
          (_ ** e) => case e.payload of
            PWorkDepends dep ant BlocksClose => [(dep, ant)]
            _                                => []
    -- (entryAt defined in §2b, above the write boundary)

||| Raw blocks-START reachability (s39; LWriteBoundary, same reasoning as
||| bcReach one edge-type over -- the SEPARATE subgraph, never merged with
||| blocks-close's, per s39 Element 2's own two grounds).
bsReach : {n : Nat} -> Ledger n -> (from : Slug) -> List Slug
bsReach l from = reach n bsEdges [from] [from]
  where
    bsEdges : List (Slug, Slug)
    bsEdges = concatMap edgeAt (allIds n)
      where
        edgeAt : Fin n -> List (Slug, Slug)
        edgeAt t = case entryAt l t of
          (_ ** e) => case e.payload of
            PWorkDepends dep ant BlocksStart => [(dep, ant)]
            _                                => []

||| s29 Element C at the root: strict close needs a witnessed disposition and
||| an empty blocker set (IN-FORCE, via strictBlockers, §4); non-strict
||| closes carry no premise. s38's ELSIF: a strict BOOKKEEPING close is a
||| contradiction in terms (a judgment-free close cannot satisfy strict
||| mode's obligation-tree requirement) -- refused exactly like strict +
||| deferred.
strictPremise : {n : Nat} -> Ledger n -> Slug -> (strict : Bool)
             -> ReviewDisposition -> Bool
strictPremise l s False _            = True
strictPremise l s True  DDeferred    = False
strictPremise l s True  DBookkeeping = False
strictPremise l s True  DWitnessed   = null (strictBlockers l s)

||| The write-boundary judgment: which appends the kernel accepts, one
||| constructor per licensed Payload shape. Raw-vs-derived domains kept per
||| s31's allowlist: freshness/opened/cycle premises quantify RAW; the
||| strict-close premise quantifies the projection (via strictBlockers).
||| Both visible in one indexed family -- the model keeps the two
||| quantification domains it must, rather than uniformizing them away.
data ValidPayload : {n : Nat} -> Ledger n -> Payload Draft n -> Type where
  VProse  : ValidPayload l (PProse k)
  ||| s36: a decision's grade is writer-supplied and unvalidated at the kernel
  ||| (no vocabulary CHECK by ratified design) -- no premise.
  VDecision : ValidPayload l (PDecision g)
  ||| s37: the target is Fin-typed (a dangling disposition is unrepresentable,
  ||| stronger than the SQL's FK); the class-word/target-class agreement is
  ||| the SQL trigger's own deeper check, not re-derived here (noted, not
  ||| hidden).
  VViolationDisposition : ValidPayload l (PViolationDisposition c t r w)
  ||| regards earlier-row: already unrepresentable via Fin n (unchanged).
  VReview : ValidPayload l (PReview r d)
  ||| s43: a write_refused row's payload judgment carries no premise of its
  ||| own -- the SQL's guard on WHO may mint it (only the boundary's own
  ||| journaler; a caller-supplied kind='write_refused' is the refused forgery
  ||| channel) is boundary-side payload VALIDATION at the SECURITY DEFINER
  ||| trust line, an authorship fact this row algebra cannot see (named, not
  ||| hidden; the oracle's count>sequence FAIL is its mechanical tripwire).
  VWriteRefused : ValidPayload l (PWriteRefused q m sf d aa ar)
  ||| s40: the four identity events. Registration freshness by NAME lives on
  ||| the SQL anchor's UNIQUE(name) + the CLI ceremony -- this model's
  ||| PrincipalId is the id, not the name, so name-duplicate refusal is out of
  ||| its universe (named honestly; the SUBJECT-standing write refusals live in
  ||| boundaryOk, entry-level, below).
  VPrincipalRegistered : ValidPayload l (PPrincipalRegistered s c purpose)
  VPrincipalSuspended  : ValidPayload l (PPrincipalSuspended s active)
  VPrincipalRevoked    : ValidPayload l (PPrincipalRevoked s)
  VStandingDeclared    : ValidPayload l (PStandingDeclared s dbRole active)
  ||| s44: no payload premise of its own -- the target is Fin-typed (the FK,
  ||| structural), the coupling is the index; the two CLI-side cross-row rules
  ||| (one-per-(actor,row), no-self-attestation) are s44's own named residue,
  ||| out of this judgment exactly as they are out of the SQL CHECKs.
  VModelAttested : ValidPayload l (PModelAttested t m g os jb he v ex)
  ||| s41 D-3: a self-relation is refused for every relation value; a
  ||| same-natural-person row must be canonically ordered (subject id <
  ||| object id -- immutable ids, so the verdict cannot flip; the kernel's
  ||| plain CHECK, here a So premise).
  VRelate : (0 notSelf : So (not (s == o)))
         -> (0 canonical : So (not (rel == SameNaturalPerson) || (s < o)))
         -> ValidPayload l (PRelationAsserted s rel o active)
  VRoleBound : ValidPayload l (PRoleBound s roleName active)
  ||| s41 D-3: agent keys stay refused -- a key binding demands a HUMAN
  ||| subject (classOf reads the registration event).
  VKeyBound : (0 human : So (classOf l s == Just ACHuman))
           -> ValidPayload l (PKeyBound s fp active)
  VCompetenceGranted : ValidPayload l (PCompetenceGranted s activity active v)
  ||| An opening act: the slug must be fresh in RAW history (slug burned --
  ||| no constructor exists that re-opens; a genuine redo is a NEW slug).
  VOpen   : (0 fresh : So (not (everOpened l s)))
         -> ValidPayload l (PWorkOpened s title parent comp)
  ||| Claim: the slug must have an opening act (raw read) AND -- s39 -- no
  ||| unresolved direct blocks-start antecedent (the claim-time precondition
  ||| foreclosure; in-force edges, antecedent closed, via startBlockers) AND
  ||| -- s47 -- no in-force close (a closed item is not claimable; the same
  ||| hasCloseCur read the close/depends legs already consume, one home).
  VClaim  : (0 opened : So (everOpened l s))
         -> (0 startOk : So (null (startBlockers l s)))
         -> (0 notClosed : So (not (hasCloseCur l s)))
         -> ValidPayload l (PWorkClaimed s)
  ||| s39: a blocks-start edge refuses self-edge, dangling antecedent, and a
  ||| cycle in its OWN raw subgraph (bsReach) -- mirroring VDepBC one
  ||| edge-type over, the two subgraphs deliberately separate.
  VDepBS  : (0 opened    : So (everOpened l s))
         -> (0 notSelf   : So (not (ant == s)))
         -> (0 antOpened : So (everOpened l ant))
         -> (0 acyclic   : So (not (elem s (bsReach l ant))))
         -> ValidPayload l (PWorkDepends s ant (Just BlocksStart))
  ||| informs / untyped keep s22's deliberately lax posture: dangling
  ||| antecedent NOT refused (the violations view reads it) -- no ant premise.
  ||| (s39: the lax premise now excludes BOTH gating edge types -- a
  ||| blocks-start edge routes through VDepBS below, exactly as blocks-close
  ||| routes through VDepBC.)
  VDepLax : (0 opened : So (everOpened l s))
         -> (0 lax : So (not (et == Just BlocksClose || et == Just BlocksStart)))
         -> ValidPayload l (PWorkDepends s ant et)
  ||| s30: blocks-close refuses self-edge, dangling antecedent, and a cycle in
  ||| the RAW blocks-close subgraph, at construction.
  VDepBC  : (0 opened    : So (everOpened l s))
         -> (0 notSelf   : So (not (ant == s)))
         -> (0 antOpened : So (everOpened l ant))
         -> (0 acyclic   : So (not (elem s (bcReach l ant))))
         -> ValidPayload l (PWorkDepends s ant (Just BlocksClose))
  ||| s29: epoch steady state (disposition is total by type -- unchanged
  ||| fidelity choice, see header) + Element C strict premises (s31 in-force)
  ||| + s33 Element 2 STRICT-BY-TYPE: the entry condition into the strict
  ||| branch widens from the writer-supplied flag alone to
  ||| `strict || isComposite l s` -- QUOTE (s33-composite-discharge.sql, lines
  ||| 380-381): "IF NEW.kind = 'work_closed' AND (COALESCE(NEW.work_strict_close,
  ||| false) OR COALESCE(is_composite, false)) THEN" -- nothing INSIDE the
  ||| strict branch changes (strictPremise itself is untouched, s29 Element C,
  ||| byte-for-byte); only what ROUTES a close into it widens. A composite
  ||| slug's close is therefore ALWAYS strict, regardless of the strict field
  ||| the writer supplied (r33a below: refused even at strict=False).
  VClose  : (0 opened   : So (everOpened l s))
         -> (0 strictOk : So (strictPremise l s (strict || isComposite l s) disp))
         -> ValidPayload l (PWorkClosed s res w disp ref strict)

-- ===========================================================================
-- R9  THE RECORDING STEP: append = validate + compute-and-record (the trigger
--     as the ONLY Draft -> Recorded arrow). The s29 grade ladder is a CHECKED
--     transcription of validate_independence()'s ELSIF chain, not an opaque
--     enum: fail-safe same-principal on any absent identity half.
-- ===========================================================================

stampPair : Maybe Stamp -> Maybe (String, String)
stampPair Nothing                = Nothing
stampPair (Just (MkStamp s a _)) = Just (s, a)

||| s29 validate_independence(), the grade computation, verbatim in shape.
gradeLadder : Maybe (String, String) -> Maybe (String, String) -> DischargeGrade
gradeLadder Nothing  _        = SamePrincipal
gradeLadder _        Nothing  = SamePrincipal
gradeLadder (Just (rs, ra)) (Just (ts, ta)) =
  if rs == ts && ra == ta then SamePrincipal
  else if rs == ts        then SameSession
  else                         DistinctSession
  -- distinct-deployment: closed vocabulary, unreachable here today -- the
  -- SAME disclosed limit as s29's LIMITS block, kept, not polished away.

recordPayload : {n : Nat} -> Ledger n -> Maybe Stamp -> Payload Draft n -> Payload Recorded n
recordPayload l st (PProse k)            = PProse k
recordPayload l st (PDecision g)         = PDecision g          -- s36: writer-supplied, no trigger
recordPayload l st (PViolationDisposition c t r w) = PViolationDisposition c t r w
recordPayload l st (PReview r (MkReviewDetail v i b a ())) =
  let tgt = case entryAt l r of (_ ** e) => e.stamp
  in PReview r (MkReviewDetail v i b a (gradeLadder (stampPair st) (stampPair tgt)))
recordPayload l st (PWriteRefused q m sf d aa ar) = PWriteRefused q m sf d aa ar
recordPayload l st (PModelAttested t m g os jb he v ex) = PModelAttested t m g os jb he v ex
recordPayload l st (PPrincipalRegistered s c p) = PPrincipalRegistered s c p
recordPayload l st (PPrincipalSuspended s a)    = PPrincipalSuspended s a
recordPayload l st (PPrincipalRevoked s)        = PPrincipalRevoked s
recordPayload l st (PStandingDeclared s r a)    = PStandingDeclared s r a
recordPayload l st (PRelationAsserted s r o a)  = PRelationAsserted s r o a
recordPayload l st (PRoleBound s r a)           = PRoleBound s r a
recordPayload l st (PKeyBound s f a)            = PKeyBound s f a
recordPayload l st (PCompetenceGranted s act a v) = PCompetenceGranted s act a v
recordPayload l st (PWorkOpened s t p c) = PWorkOpened s t p c
recordPayload l st (PWorkClaimed s)      = PWorkClaimed s
recordPayload l st (PWorkDepends s a Nothing)   = PWorkDepends s a Informs  -- s30 default
recordPayload l st (PWorkDepends s a (Just et)) = PWorkDepends s a et
recordPayload l st (PWorkClosed s r w d f b)    = PWorkClosed s r w d f b

||| s40/s41: the ENTRY-LEVEL premise family (facts that live on the row, not
||| the payload alone -- exactly the checks the SQL's set_actor /
||| validate_independence / inactive-needs-supersedes CHECK make against the
||| whole row):
|||   (a) s40 strict attribution: the actor's standing accepts writes
|||       (suspended/revoked refuse; unregistered-legacy is never bricked).
|||       The DECLARED-DEFAULT half (a NULL actor resolving via the standing
|||       declaration) is not representable here -- Entry.actor is total, the
|||       model's writer always names a principal; the resolution mark
|||       (principal_actor_resolution) is likewise a recording detail below
|||       this model's altitude. Named, not hidden.
|||   (b) s41 D-1: an INACTIVE binding row must supersede something (a
|||       retraction that retracts nothing is unrepresentable at commit).
|||   (c) s41 D-6: a managerial/financial independence claim demands a HUMAN
|||       actor (the ratified human-attested scoping; technical stays
|||       stamp-witnessed, the s21 gate -- which this model already carries as
|||       the distinctness question, out of this boolean's scope).
|||   (d) s43 R6 + s45 §3.4, now ONE typed relation (maySupersede below):
|||       which recorded payload may be superseded by which draft payload.
|||       The premise family is spelled as four NAMED top-level predicates so
|||       the total write verdict (§3b) can report WHICH premise refused --
|||       the enumerable-premise-list goal of the consult this pass executes.
maySupersede : Payload Recorded m -> Payload Draft k -> Bool
-- s43 R6 (RATIFIED): a write_refused row is UNRETRACTABLE -- it records a
-- historical fact about a refused attempt and asserts nothing retractable.
maySupersede (PWriteRefused _ _ _ _ _ _) _ = False
-- s45 §3.4, the conversion-found closure: the three standing-lifecycle kinds
-- accept only SAME-KIND, IDENTITY-CONTINUOUS supersessors. A declaration's
-- supersessor restates the SAME db_role always, and the SAME subject when it
-- is an UNBIND (active=False); a ROTATION (active=True) may repoint the
-- subject by design. DESIGN-PROBE FINDING (this pass's commission, scope
-- item 3 -- NAMED for the maintainer, not resolved): the active-flag
-- TRANSITION matrix (target.active x new.active) on a same-kind lifecycle
-- supersession is fully unconstrained by s45 Element 4, and this rendering
-- transcribes that faithfully. Three of the four cells have blessed names in
-- s45's own teach-text (true->true rotation/re-suspend-correction,
-- true->false unbind/lift, false->false retraction-rationale-fix); the
-- FOURTH cell -- false->true, re-asserting by SUPERSEDING a retraction row
-- rather than writing a fresh declaration/suspension -- is representable,
-- standing-effective (it removes the retraction from ledger_current and
-- installs an active governing row), and nowhere named or blessed: s45's own
-- comment says "re-bind after unbind works by construction: a later FRESH
-- declaration", implying the fresh path is the sanctioned one, yet the
-- supersession path also works. Whether that cell is intended (a correction
-- of an erroneous retraction) or should be refused is the maintainer's call.
-- RULED 2026-07-18 (maintainer, same day the finding was filed; ledger row
-- 1650): the cell is INTENDED -- "as a matter of practice it makes sense
-- ... that this should be possible." Re-assertion by superseding a
-- retraction row is sanctioned alongside the fresh-row path; no kernel
-- change follows (the SQL already permits it), and this rendering stands
-- as the blessed semantics, no longer an open question.
maySupersede (PStandingDeclared tSubj tRole _) new = case new of
  PStandingDeclared nSubj nRole nAct => nRole == tRole && (nAct || nSubj == tSubj)
  _                                  => False
maySupersede (PPrincipalSuspended tSubj _) new = case new of
  PPrincipalSuspended nSubj _ => nSubj == tSubj
  _                           => False
maySupersede (PPrincipalRevoked tSubj) new = case new of
  PPrincipalRevoked nSubj => nSubj == tSubj
  _                       => False
-- everything else: s31 uniform retraction, unchanged -- including s44
-- attestations, deliberately supersession-retractable (a defeasible claim,
-- NOT given R6's unretractability; s44's own argued contrast).
maySupersede _ _ = True

||| Premise (a): the actor's standing accepts writes (s40 §3.6).
actorStandingOkB : {n : Nat} -> Ledger n -> Entry Draft n -> Bool
actorStandingOkB l e = writeAllowed (principalStanding l e.actor)

||| Premise (d): the supersession target, if any, admits this supersessor
||| (maySupersede -- R6 + the s45 lifecycle discipline, one home).
supersessionOkB : {n : Nat} -> Ledger n -> Entry Draft n -> Bool
supersessionOkB l e = case e.supersedes of
  Nothing => True
  Just t  => case entryAt l t of
    (_ ** te) => maySupersede te.payload e.payload

||| Premise (b): an INACTIVE (retraction-shaped) row must supersede something
||| -- s41 D-1's CHECK, which s45 Element 1 extends to the two lifecycle
||| kinds with ZERO edit in SQL (the kind-free CHECK already covered them);
||| here the two new arms are explicit because the model's discriminator
||| lives per-constructor.
retractionAnchoredB : {n : Nat} -> Entry Draft n -> Bool
retractionAnchoredB e = case e.payload of
  PRelationAsserted _ _ _ False  => isJust e.supersedes
  PRoleBound _ _ False           => isJust e.supersedes
  PKeyBound _ _ False            => isJust e.supersedes
  PCompetenceGranted _ _ False _ => isJust e.supersedes
  PStandingDeclared _ _ False    => isJust e.supersedes   -- s45: an unbind
  PPrincipalSuspended _ False    => isJust e.supersedes   -- s45: a lift
  _                              => True

||| Premise (c): s41 D-6 human-attested managerial/financial scoping.
independenceScopeOkB : {n : Nat} -> Ledger n -> Entry Draft n -> Bool
independenceScopeOkB l e = case e.payload of
  PReview _ d => case d.independence of
                   Managerial => classOf l e.actor == Just ACHuman
                   Financial  => classOf l e.actor == Just ACHuman
                   Technical  => True
  _           => True

boundaryOk : {n : Nat} -> Ledger n -> Entry Draft n -> Bool
boundaryOk l e =
     actorStandingOkB l e
  && retractionAnchoredB e
  && independenceScopeOkB l e
  && supersessionOkB l e

||| The sanctioned growth step: the write boundary as the ONLY exported
||| introduction form for a bigger ledger (in a multi-module rendering (:<)
||| would be hidden and `append` the API -- trigger-as-smart-constructor).
||| s40/s41: appends now ALSO demand the entry-level premise family
||| (boundaryOk) -- the payload judgment alone no longer exhausts the write
||| boundary, exactly as the SQL's own chain (set_actor's standing refusals,
||| the inactive-needs-supersedes CHECK, D-6) runs beside validate_*.
append : {n : Nat} -> (l : Ledger n) -> (e : Entry Draft n)
      -> (0 ok : ValidPayload l e.payload)
      -> (0 entryOk : So (boundaryOk l e)) -> Ledger (S n)
append l e _ _ = l :< MkEntry e.session e.statement e.actor e.stamp e.supersedes
                          e.amends e.answers e.enacts (recordPayload l e.stamp e.payload)

-- ===========================================================================
-- §3b  THE TOTAL WRITE VERDICT (s43 internalized -- this pass's commission,
--      scope item 1). `append` above is proof-DEMANDING: the caller must
--      already hold the validity evidence, which renders the acceptance half
--      of s43 but not its point -- the kernel's boundary is a TOTAL function
--      whose refusal is a VALUE (a committed write_refused row), never an
--      abort. `write` below is that function. Its type IS the s43 totality
--      invariant the header used to declare out-of-model: EVERY call grows
--      the ledger by exactly one row -- the accepted entry, or the journaled
--      refusal -- so "a refusal verdict cannot be delivered unjournaled" is
--      now a type fact, not an operational note. (What stays out-of-model,
--      still named: the refusal_seq oracle and the journal-INSERT-failure
--      leg -- the SQL's own residual "loud abort + counted gap" path -- are
--      recovery machinery BELOW this rendering; and the SHA-256 payload
--      digest is the same crypto boundary s42 already names.)
--      `RefusalReason` makes the boundary's premise family an ENUMERABLE
--      DATUM: one constructor per refusal arm, auditable against the SQL's
--      refusal list -- the correspondence surface whose absence let the s47
--      gap go unnoticed.
-- ===========================================================================

||| The closed refusal vocabulary: every arm of ValidPayload's premise family
||| and boundaryOk's (a)-(d), one constructor each. Adding a kernel refusal
||| means adding a constructor here -- the diff IS the premise-list amendment
||| (the HistoryLicense pattern, §2, applied to refusals).
data RefusalReason
  = RActorStanding             -- (a) s40: suspended/revoked actor
  | RSupersedeWriteRefused     -- (d) s43 R6
  | RSupersedeLifecycleKind    -- (d) s45 §3.4: cross-kind lifecycle target
  | RSupersedeLifecycleIdentity -- (d) s45 §3.4: role/subject discontinuity
  | RRetractionUnanchored      -- (b) s41 D-1 / s45: inactive without target
  | RIndependenceNeedsHuman    -- (c) s41 D-6
  | RRelationSelf              -- s41 D-3
  | RRelationNonCanonical      -- s41 D-3 (same-natural-person ordering)
  | RKeyNonHuman               -- s41 D-3 (agent keys refused)
  | RSlugBurned                -- s22/s31 fork 2
  | RClaimUnopened             -- s22
  | RClaimStartBlocked         -- s39
  | RClaimOnClosed             -- s47
  | RDepUnopened               -- s22
  | RDepSelfEdge               -- s30/s39
  | RDepDangling               -- s30/s39
  | RDepCycle                  -- s30/s39
  | RCloseUnopened             -- s22
  | RStrictUnresolved          -- s29 Element C / s33 / s38

||| Which SQL boundary function would have carried this write -- refusal
||| surfaces are per-FUNCTION (s43's closed CHECK), and the function is
||| determined by the payload family. SurfObligation is UNREACHABLE here,
||| named: countersign-obligation writes are not modeled in this file at all.
surfaceFor : Payload st m -> RefusalSurface
surfaceFor (PReview _ _)                  = SurfReview
surfaceFor (PPrincipalRegistered _ _ _)   = SurfRegistration
surfaceFor (PPrincipalSuspended _ _)      = SurfRegistration
surfaceFor (PPrincipalRevoked _)          = SurfRegistration
surfaceFor (PStandingDeclared _ _ _)      = SurfRegistration
surfaceFor (PRelationAsserted _ _ _ _)    = SurfRegistration
surfaceFor (PRoleBound _ _ _)             = SurfRegistration
surfaceFor (PKeyBound _ _ _)              = SurfRegistration
surfaceFor (PCompetenceGranted _ _ _ _)   = SurfRegistration
surfaceFor _                              = SurfLedger

||| The teach-text, one literal per reason (each a compile-time-checked
||| NonEmptyText -- the SQL's message payload, at headline altitude).
refusalText : RefusalReason -> NonEmptyText
refusalText RActorStanding              = MkNonEmptyText "strict attribution: actor standing refuses writes (s40/s45)" Oh
refusalText RSupersedeWriteRefused      = MkNonEmptyText "a write_refused row is unretractable (s43 R6)" Oh
refusalText RSupersedeLifecycleKind     = MkNonEmptyText "a standing-lifecycle row is superseded only by its own kind (s45 3.4)" Oh
refusalText RSupersedeLifecycleIdentity = MkNonEmptyText "a lifecycle supersessor must restate its target's identity (s45 3.4)" Oh
refusalText RRetractionUnanchored       = MkNonEmptyText "an inactive binding row must supersede something (s41 D-1/s45)" Oh
refusalText RIndependenceNeedsHuman     = MkNonEmptyText "managerial/financial independence demands a human actor (s41 D-6)" Oh
refusalText RRelationSelf               = MkNonEmptyText "a self-relation is refused (s41 D-3)" Oh
refusalText RRelationNonCanonical       = MkNonEmptyText "same-natural-person must be canonically ordered (s41 D-3)" Oh
refusalText RKeyNonHuman                = MkNonEmptyText "a key binding demands a human subject (s41 D-3)" Oh
refusalText RSlugBurned                 = MkNonEmptyText "slug already opened once: burned (s22/s31)" Oh
refusalText RClaimUnopened              = MkNonEmptyText "claim of a never-opened slug (s22)" Oh
refusalText RClaimStartBlocked          = MkNonEmptyText "blocks-start antecedent unresolved at claim (s39)" Oh
refusalText RClaimOnClosed              = MkNonEmptyText "a closed item is not claimable (s47)" Oh
refusalText RDepUnopened                = MkNonEmptyText "dependency on a never-opened dependent slug (s22)" Oh
refusalText RDepSelfEdge                = MkNonEmptyText "a gating self-edge is refused (s30/s39)" Oh
refusalText RDepDangling                = MkNonEmptyText "a gating edge to a never-opened antecedent is refused (s30/s39)" Oh
refusalText RDepCycle                   = MkNonEmptyText "a gating-edge cycle is refused (s30/s39)" Oh
refusalText RCloseUnopened              = MkNonEmptyText "close of a never-opened slug (s22)" Oh
refusalText RStrictUnresolved           = MkNonEmptyText "strict close with an unresolved obligation tree or judgment-free disposition (s29/s33/s38)" Oh

||| SQLSTATE at headline altitude: the model journals every policy refusal as
||| P0001 (RAISE EXCEPTION's default). Per-arm granularity (23514 for CHECKs,
||| 22003, ...) is SQL-mechanical detail below this rendering -- named.
pstate : NonEmptyText
pstate = MkNonEmptyText "P0001" Oh

||| The payload digest: a SHA-256 rendering, out of this model's universe
||| (the s42 crypto boundary, one more member) -- carried as a named opaque
||| literal, never claimed computed.
unmodeledDigest : NonEmptyText
unmodeledDigest = MkNonEmptyText "sha256(payload):out-of-model" Oh

||| Reduction-transparent decide (Data.So's `choose` is not relied on for the
||| same reason `strong` exists -- every Refl fixture in §7 needs this to
||| reduce).
public export
chooseB : (b : Bool) -> Either (So b) (So (not b))
chooseB True  = Left Oh
chooseB False = Right Oh

||| The DECIDED payload judgment: for every draft payload, either the premise
||| that refuses it or the ValidPayload evidence that licenses it -- each
||| premise decided by chooseB, so acceptance carries the SAME proofs append
||| demands. Refusal order within an arm follows the SQL trigger's own check
||| order.
checkPayload : {n : Nat} -> (l : Ledger n) -> (p : Payload Draft n)
            -> Either RefusalReason (ValidPayload l p)
checkPayload l (PProse k)                      = Right VProse
checkPayload l (PDecision g)                   = Right VDecision
checkPayload l (PViolationDisposition c t r w) = Right VViolationDisposition
checkPayload l (PReview r d)                   = Right VReview
checkPayload l (PWriteRefused q m sf d aa ar)  = Right VWriteRefused
checkPayload l (PModelAttested t m g os jb he v ex) = Right VModelAttested
checkPayload l (PPrincipalRegistered s c p)    = Right VPrincipalRegistered
checkPayload l (PPrincipalSuspended s a)       = Right VPrincipalSuspended
checkPayload l (PPrincipalRevoked s)           = Right VPrincipalRevoked
checkPayload l (PStandingDeclared s r a)       = Right VStandingDeclared
checkPayload l (PRelationAsserted s rel o act) =
  case chooseB (not (s == o)) of
    Right _      => Left RRelationSelf
    Left notSelf => case chooseB (not (rel == SameNaturalPerson) || (s < o)) of
      Right _    => Left RRelationNonCanonical
      Left canon => Right (VRelate notSelf canon)
checkPayload l (PRoleBound s r a)              = Right VRoleBound
checkPayload l (PKeyBound s fp a) =
  case chooseB (classOf l s == Just ACHuman) of
    Left h  => Right (VKeyBound h)
    Right _ => Left RKeyNonHuman
checkPayload l (PCompetenceGranted s act a v)  = Right VCompetenceGranted
checkPayload l (PWorkOpened s title par comp) =
  case chooseB (everOpened l s) of
    Left _      => Left RSlugBurned
    Right fresh => Right (VOpen fresh)
checkPayload l (PWorkClaimed s) =
  case chooseB (everOpened l s) of
    Right _     => Left RClaimUnopened
    Left opened => case chooseB (null (startBlockers l s)) of
      Right _  => Left RClaimStartBlocked
      Left st  => case chooseB (hasCloseCur l s) of
        Left _   => Left RClaimOnClosed
        Right nc => Right (VClaim opened st nc)
checkPayload l (PWorkDepends s ant Nothing) =
  case chooseB (everOpened l s) of
    Right _ => Left RDepUnopened
    Left op => Right (VDepLax op Oh)
checkPayload l (PWorkDepends s ant (Just Informs)) =
  case chooseB (everOpened l s) of
    Right _ => Left RDepUnopened
    Left op => Right (VDepLax op Oh)
checkPayload l (PWorkDepends s ant (Just BlocksClose)) =
  case chooseB (everOpened l s) of
    Right _ => Left RDepUnopened
    Left op => case chooseB (not (ant == s)) of
      Right _ => Left RDepSelfEdge
      Left ns => case chooseB (everOpened l ant) of
        Right _ => Left RDepDangling
        Left ao => case chooseB (not (elem s (bcReach l ant))) of
          Right _ => Left RDepCycle
          Left ac => Right (VDepBC op ns ao ac)
checkPayload l (PWorkDepends s ant (Just BlocksStart)) =
  case chooseB (everOpened l s) of
    Right _ => Left RDepUnopened
    Left op => case chooseB (not (ant == s)) of
      Right _ => Left RDepSelfEdge
      Left ns => case chooseB (everOpened l ant) of
        Right _ => Left RDepDangling
        Left ao => case chooseB (not (elem s (bsReach l ant))) of
          Right _ => Left RDepCycle
          Left ac => Right (VDepBS op ns ao ac)
checkPayload l (PWorkClosed s res w disp ref strict) =
  case chooseB (everOpened l s) of
    Right _ => Left RCloseUnopened
    Left op => case chooseB (strictPremise l s (strict || isComposite l s) disp) of
      Left ok => Right (VClose op ok)
      Right _ => Left RStrictUnresolved

||| Which entry-level premise refused (called only on the not-boundaryOk
||| path; total anyway -- the unreachable arms return the nearest reason).
boundaryReason : {n : Nat} -> Ledger n -> Entry Draft n -> RefusalReason
boundaryReason l e =
  if      not (actorStandingOkB l e)    then RActorStanding
  else if not (retractionAnchoredB e)   then RRetractionUnanchored
  else if not (independenceScopeOkB l e) then RIndependenceNeedsHuman
  else supersedeReason
  where
    supersedeReason : RefusalReason
    supersedeReason = case e.supersedes of
      -- unreachable under the call contract (supersessionOkB is True on
      -- Nothing); total anyway:
      Nothing => RSupersedeLifecycleKind
      Just t  => case entryAt l t of
        (_ ** te) => case te.payload of
          PWriteRefused _ _ _ _ _ _ => RSupersedeWriteRefused
          PStandingDeclared _ _ _   => case e.payload of
            PStandingDeclared _ _ _   => RSupersedeLifecycleIdentity
            _                         => RSupersedeLifecycleKind
          PPrincipalSuspended _ _   => case e.payload of
            PPrincipalSuspended _ _   => RSupersedeLifecycleIdentity
            _                         => RSupersedeLifecycleKind
          PPrincipalRevoked _       => case e.payload of
            PPrincipalRevoked _       => RSupersedeLifecycleIdentity
            _                         => RSupersedeLifecycleKind
          _                         => RSupersedeLifecycleKind

||| The composed decision: payload judgment then entry-level premises. (The
||| SQL's trigger chain runs set_actor FIRST, alphabetically -- the composed
||| VERDICT is identical either way; on a draft failing both, the two
||| renderings report different first-reasons. A rendering choice, named.)
checkEntry : {n : Nat} -> (l : Ledger n) -> (e : Entry Draft n)
          -> Either RefusalReason (ValidPayload l e.payload, So (boundaryOk l e))
checkEntry l e = case checkPayload l e.payload of
  Left r   => Left r
  Right pv => case chooseB (boundaryOk l e) of
    Left ok => Right (pv, ok)
    Right _ => Left (boundaryReason l e)

||| THE TOTAL WRITE. Ledger (S n) on BOTH arms -- acceptance appends the
||| recorded entry (via append, proofs from checkEntry); refusal appends the
||| journaled write_refused row. The journaler principal and the session's
||| role are the boundary's two ambient facts (SQL: the 'write-boundary' tool
||| principal, s43 Element 6, and session_user) -- passed as arguments here
||| because the model has no ambient session. The refusal arm mints its row
||| DIRECTLY (raw (:<)): who-may-mint is boundary-side authorship, exactly
||| VWriteRefused's own note -- in a multi-module rendering this function and
||| append would be the only exports, so the journaler's bypass is a scope
||| fact, not a hole.
write : {n : Nat} -> (journaler : PrincipalId) -> (sessionRole : NonEmptyText)
     -> (l : Ledger n) -> (e : Entry Draft n) -> Ledger (S n)
write j role l e = case checkEntry l e of
  Right (pv, bOk) => append l e pv bOk
  Left r =>
    l :< MkEntry e.session "write refused (journaled verdict)" j Nothing
           Nothing Nothing Nothing []
           (PWriteRefused Autoharn.pstate (refusalText r) (surfaceFor e.payload)
              Autoharn.unmodeledDigest (Just e.actor) role)

||| Probes for the §7 fixtures: is the head row a journaled refusal, and at
||| which surface. Pattern-total: a Ledger (S n) is always (:<).
headRefused : {n : Nat} -> Ledger (S n) -> Bool
headRefused (l :< e) = case e.payload of
  PWriteRefused _ _ _ _ _ _ => True
  _                         => False

headSurface : {n : Nat} -> Ledger (S n) -> Maybe RefusalSurface
headSurface (l :< e) = case e.payload of
  PWriteRefused _ _ sf _ _ _ => Just sf
  _                          => Nothing

-- ===========================================================================
-- §4  COMPOSITE DISCHARGE AS A READ OF THE §2b OBLIGATION CALCULUS. No new
--     tree walker is minted here -- ADR-0012 P1: one home, two readers,
--     cannot drift (composite-spec §2's own principle, checked against the
--     kernel: strictBlockers is that one home already).
-- ===========================================================================

||| The DERIVED per-item state -- the projection-side fold that owns the
||| latest-event linearity (work_item_current). Deliberately left as a bare
||| data type, not computed here: the fold itself is encoding noise this
||| file's R1-R9 claims did not need to re-derive (untouched from v1).
data ItemState = StOpen | StClosed Resolution

||| Composite discharge -- A READ, never an authored act (composite spec §2:
||| "the derivation is the obligation calculus the kernel ALREADY owns").
||| Vacuous-truth hazard foreclosed: a NEVER-hand-closed zero-child composite
||| stays open, never discharged (that gate lives in the never-hand-closed
||| branch below; see its own comment for why the hand-closed branch does not
||| repeat it). s33 LANDED (header): this function now matches Element 4's
||| ACTUAL SQL, re-derived from the delta itself (not the gate author's
||| description of it) -- quoted at the definition below.
data EffectiveState = ESOpen | ESClosed Resolution | ESDischargedByObligations

||| Does root have at least one direct child edge (parent or blocks-close),
||| IN FORCE? De-stubbed the same way R4 de-stubbed the review leg -- no
||| parameter is taken on faith; the tree is asked directly.
hasDirectChild : {n : Nat} -> Ledger n -> Slug -> Bool
hasDirectChild l root = anyB (\e => fst e == root) (edgesCur l)

||| s33 Element 4, re-derived from the landed SQL (s33-composite-discharge.sql,
||| lines 494-504), quoted:
|||   CASE
|||     WHEN o.discharge IS DISTINCT FROM 'composite' THEN <state>
|||     WHEN c.slug IS NOT NULL THEN                          -- hand-closed
|||       CASE WHEN EXISTS (blockers) THEN 'open' ELSE 'closed' END
|||     WHEN COALESCE(cc.n, 0) >= 1 AND NOT EXISTS (blockers)  -- never hand-closed
|||       THEN 'discharged-by-obligations'
|||     ELSE 'open'
|||   END
||| The gate author's own PRESERVED note (superseded by this pass, header)
||| named the divergence but not its shape; reading the SQL directly shows the
||| `c.slug IS NOT NULL` (hand-closed, i.e. `StClosed`) arm tests ONLY the
||| blocker set -- NO child-count test appears in that branch at all. Only the
||| `ELSE` (never-hand-closed, `StOpen`) arm gates on `cc.n >= 1`, which is
||| where the vacuous-truth foreclosure actually lives. The prior refresh's
||| code ignored `ItemState` for every composite item and applied the
||| child-count gate unconditionally -- wrong in both directions (a
||| hand-closed zero-child composite should read closed once resolved; a
||| hand-closed composite with an unresolved tree should re-open even with
||| children present). Fixed here by matching on ItemState first, exactly as
||| the SQL's CASE order does.
effectiveState : {n : Nat} -> Ledger n -> Slug
              -> (composite : Bool) -> ItemState -> EffectiveState
-- hand-closed (raw `state = 'closed'`): derived reading ALWAYS wins over the
-- hand-close (spec sec-3b) -- blockers non-empty reopens it IN THE SAME READ
-- even though the raw close row still stands; no child-count test, matching
-- the SQL's `c.slug IS NOT NULL` arm byte-for-byte.
effectiveState l s True (StClosed r) =
  case strictBlockers l s of
    [] => ESClosed r
    _  => ESOpen
-- never hand-closed: discharged-by-obligations iff >=1 direct child AND
-- blockers empty; the ELSE arm (including the zero-children case) is 'open'
-- -- vacuous-truth foreclosure lives HERE, and only here (spec sec-3's own
-- named LIMIT).
effectiveState l s True StOpen =
  if hasDirectChild l s && null (strictBlockers l s)
    then ESDischargedByObligations
    else ESOpen
effectiveState _ _ False StOpen       = ESOpen
effectiveState _ _ False (StClosed r) = ESClosed r

-- ===========================================================================
-- §5  UNIFORM RETRACTION, REINSTATEMENT-FREE -- AS A THEOREM (R5b: restated
--     and reproved over the Fin-typed projection).
--     "Superseding the superseder does not revive the victim" is, precisely:
--     supersededIn is MONOTONE under append. Any extension of the ledger --
--     including a row that supersedes the victim's superseder -- preserves
--     every existing supersededness fact.
-- ===========================================================================

strongWeaken : {n : Nat} -> (t : Fin n) -> strong (weaken t) = Just t
strongWeaken FZ     = Refl
strongWeaken (FS p) = rewrite strongWeaken p in Refl

orRightTrue : (b : Bool) -> (b || True) = True
orRightTrue True  = Refl
orRightTrue False = Refl

||| Reinstatement-freedom: once superseded (at row t, addressed against the
||| n-row ledger l), superseded under every extension (l :< e, where t is
||| re-addressed via `weaken` into the (n+1)-row index space).
supersededStable : {n : Nat} -> (l : Ledger n) -> (e : Entry Recorded n)
                -> (t : Fin n)
                -> supersededIn l t = True
                -> supersededIn (l :< e) (weaken t) = True
supersededStable l e t prf =
  rewrite strongWeaken t in
  rewrite prf in
  orRightTrue (maybe False (\f => finToNat f == finToNat (weaken t)) e.supersedes)

-- The CONVERSE design (genuine reinstatement: in-force iff no IN-FORCE
-- superseder) is ALSO a perfectly definable total Idris function -- the
-- recursion runs upward in id and is well-founded because ids are finite:
--
--   inForceReinstating l t = not (any (\j => supersedesEdge j t
--                                          && inForceReinstating l j) ...)
--
-- So Idris does NOT make the rejected semantics unrepresentable; it makes the
-- CHOICE legible (a monotone definition vs recursion through negation) and
-- the ratified property provable (supersededStable). The spec's remark that
-- reinstatement is "stable-model territory, not expressible as a plain SQL
-- anti-join" is about the SQL producer's expressive floor, not about
-- semantic definability -- in Idris both sides of the fork are cheap, and
-- only discipline (or module abstraction over the edge set) keeps readers on
-- the ratified side. Stated as a limit, not resolved away.

-- ===========================================================================
-- §6  THE DUAL-PRODUCER DIFFERENTIAL (SQL/ASP AGREE) -- what the model can
--     and cannot say. Both producers are BLACK BOXES (parameters): giving
--     them Idris bodies would silently replace two independent substrates
--     with two functions sharing one compiler, one stdlib, one author -- the
--     opposite of the differential's point. Signatures now quantify over
--     List (Fin n) rather than List Nat, the natural downstream ripple of
--     R5's Fin-typed projection: a producer that reported an out-of-range id
--     would be reporting nonsense, and this makes that unrepresentable too.
-- ===========================================================================

||| The specification BOTH producers answer to: the in-force id set.
InForceSpec : {n : Nat} -> Ledger n -> List (Fin n) -> Type
InForceSpec l ids = (t : Fin n) -> (elem t ids = True) -> (inForce l t = True)

record DualProducers (n : Nat) where
  constructor MkDualProducers
  sqlFloor : Ledger n -> List (Fin n)   -- opaque: ledger_floor.py / recursive CTEs
  aspSide  : Ledger n -> List (Fin n)   -- opaque: clingo over ledger_tnow.lp

||| The AGREE verdict: bit-identical output (empty symmetric difference).
||| A runtime observation per world (./judge), rendered as a decidable
||| proposition -- the model can STATE it and a run can WITNESS it; the model
||| cannot prove it once the producers are honest black boxes.
Agree : {n : Nat} -> DualProducers n -> Ledger n -> Type
Agree p l = p.sqlFloor l = p.aspSide l

judge : {n : Nat} -> (p : DualProducers n) -> (l : Ledger n)
     -> Dec (Agree p l)
judge p l = decEq (p.sqlFloor l) (p.aspSide l)

-- ===========================================================================
-- §7  POLARITY WITNESSES (GLOSSARY both-polarity: a gate never seen red is a
--     claim). Green: legal shapes construct, and some are Refl SEMANTIC
--     witnesses (the reader functions evaluated at compile time on concrete
--     worlds). Red: the `failing` block only type-checks if its body is
--     REFUSED -- the shipped-close-without-witness CHECK witnessed firing at
--     elaboration time, extended here to the full R8 premise family.
-- ===========================================================================

mkE : PrincipalId -> Maybe (Fin n) -> Payload Recorded n -> Entry Recorded n
mkE a sup p = MkEntry "" "" a Nothing sup Nothing Nothing [] p

-- world A: open a (row 0); deferred close a by actor 1 (row 1).
worldA : Ledger 2
worldA = Lin :< mkE 1 Nothing (PWorkOpened "a" "t" Nothing False)
             :< mkE 1 Nothing (PWorkClosed "a" RDropped Nothing DDeferred Nothing False)

-- world B: world A + distinct-actor attest review of the close (row 2).
worldB : Ledger 3
worldB = worldA :< mkE 2 Nothing
           (PReview 1 (MkReviewDetail Attest Technical "re-derived" Nothing DistinctSession))

-- world C: world A + retraction of the close (row 2 supersedes row 1).
worldC : Ledger 3
worldC = worldA :< mkE 1 (Just 1) (PProse KNote)

-- ... a shipped close carries its witness (the Pi demands it); its s48
-- review-witness citation is the Fin-typed ROW arm (an earlier row only) ...
shippedClose : Payload Recorded 3
shippedClose = PWorkClosed "fix-gate" RShipped
                 (MkNonEmptyText "seen-red/gate-run.txt" Oh)
                 DWitnessed (WRRow 1)
                 True

-- ... a dropped close may omit it (Maybe on every other resolution) ...
droppedClose : Payload Recorded 3
droppedClose = PWorkClosed "spike" RDropped Nothing DDeferred Nothing False

-- ... and a review names its target as Fin n (only earlier rows nameable).
aReview : Payload Recorded 3
aReview = PReview 1 (MkReviewDetail Attest Technical "re-derived from scratch"
                       Nothing DistinctSession)

-- RED: a shipped close WITHOUT a witness does not elaborate --
-- work_shipped_requires_witness as a compile-time refusal.
failing "Mismatch between: Maybe"
  badShipped : Payload Recorded 3
  badShipped = PWorkClosed "fix-gate" RShipped Nothing DDeferred Nothing False

-- RED: a witnessed disposition WITHOUT a review ref does not elaborate --
-- work_review_witnessed_requires_ref, same idiom one column over (the ref is
-- now the s48 WitnessRef sum, so Nothing is not even the right SHAPE).
failing
  badWitnessed : Payload Recorded 3
  badWitnessed = PWorkClosed "fix-gate" RDropped Nothing DWitnessed Nothing False

-- s48 RED: a review-witness row citation cannot name a same-or-later row --
-- Fin 3 has no fourth element, so the head-guess that motivated s48 (citing
-- one's own not-yet-assigned id, kernel/lineage/s48-review-witness-existence
-- .sql's witnessed defect) is UNREPRESENTABLE here, stronger than the SQL's
-- INSERT-time existence check. The commit/artifact arms stay existence-
-- unchecked in both renderings (s48's own LIMITS, mirrored at WitnessRef).
failing
  r48a : Payload Recorded 3
  r48a = PWorkClosed "fix-gate" RDropped Nothing DWitnessed (WRRow 3) False

-- RED: a review payload cannot name a same-or-later row -- Fin 3 has no
-- fourth element; validate_review's earlier-row refusal is unrepresentable
-- rather than trapped.
failing
  badRegards : Payload Recorded 3
  badRegards = PReview 3 (MkReviewDetail Attest Technical "x" Nothing SamePrincipal)

-- R7a GREEN/Refl: raw and in-force readings AGREE while nothing is retracted
-- (the pre-s31 raw reading is not modeled separately in this refresh -- see
-- RefKernel.idr's hasCloseRaw for the side-by-side divergence proof this
-- refresh's header narrates).
r7a : hasCloseCur Autoharn.worldA "a" = True
r7a = Refl

-- R7b GREEN/Refl: after retraction, the item re-opens -- the s31 semantics
-- (a retracted close re-opens the item) as a compile-time fact.
r7b : hasCloseCur Autoharn.worldC "a" = False
r7b = Refl

-- R4a GREEN/Refl: the de-stubbed review leg, all three polarities.
r4a1 : deferredUndischarged Autoharn.worldA "a" = True   -- deferred, no attest yet
r4a1 = Refl
r4a2 : deferredUndischarged Autoharn.worldB "a" = False  -- distinct-actor attest lands
r4a2 = Refl
r4a3 : deferredUndischarged Autoharn.worldC "a" = False  -- close retracted: no obligation
r4a3 = Refl

-- R9a GREEN/Refl: the grade ladder, fail-safe polarity first.
r9a1 : gradeLadder Nothing (Just ("s","a")) = SamePrincipal
r9a1 = Refl
r9a2 : gradeLadder (Just ("s","x")) (Just ("s","y")) = SameSession
r9a2 = Refl
r9a3 : gradeLadder (Just ("s1","x")) (Just ("s2","x")) = DistinctSession
r9a3 = Refl

-- R8a GREEN: a lax (informs) dependency on a NEVER-OPENED antecedent
-- constructs -- s22's deliberately unrefused posture, preserved.
r8a : ValidPayload Autoharn.worldA (PWorkDepends "a" "ghost" (Just Informs))
r8a = VDepLax Oh Oh

-- R8b RED: the SAME dangling antecedent as blocks-close is REFUSED (s30) --
-- antOpened demands So (everOpened l "ghost") = So False.
failing
  r8b : ValidPayload Autoharn.worldA (PWorkDepends "a" "ghost" (Just BlocksClose))
  r8b = VDepBC Oh Oh Oh Oh

-- R8c RED: a blocks-close self-edge is refused (s30).
failing
  r8c : ValidPayload Autoharn.worldA (PWorkDepends "a" "a" (Just BlocksClose))
  r8c = VDepBC Oh Oh Oh Oh

-- R8e RED: claiming a slug with an in-force close is refused (s47) --
-- notClosed demands So (not (hasCloseCur worldA "a")) = So False (r7a above
-- is the green polarity of the same read).
failing
  r8e : ValidPayload Autoharn.worldA (PWorkClaimed "a")
  r8e = VClaim Oh Oh Oh

-- R8d RED: strict + deferred is a contradiction in terms (s29) -- the
-- strictPremise evaluates to False, So is uninhabited.
failing
  r8d : ValidPayload Autoharn.worldA
          (PWorkClosed "a" RDropped Nothing DDeferred Nothing True)
  r8d = VClose Oh Oh

-- R2a RED: a WRITER-SUPPLIED grade is now unrepresentable, not just
-- unconventional -- a Draft review's grade field has type ().
failing
  r2a : Payload Draft 3
  r2a = PReview 1 (MkReviewDetail Attest Technical "x" Nothing DistinctSession)

-- R6a GREEN: the projection now CARRIES its soundness; a consumer may demand
-- the proof. (Erased, so zero runtime cost -- same as the SQL view costing
-- nothing beyond its WHERE clause.)
r6a : Projection Autoharn.worldC
r6a = project worldC

-- Composite-discharge fixtures (s33 LANDED, header): a two-child composite
-- discharges once both children close, a zero-child never-hand-closed
-- composite never vacuously discharges, a composite close is always strict
-- regardless of the writer's strict flag, and a hand-close's derived reading
-- always wins over the raw state column (both directions).
-- world D: composite root "p" opened; child "c1" opened, parented to "p".
worldD : Ledger 2
worldD = Lin :< mkE 1 Nothing (PWorkOpened "p" "parent" Nothing True)
             :< mkE 1 Nothing (PWorkOpened "c1" "child" (Just "p") False)

-- world E: world D + c1 closed shipped-witnessed.
worldE : Ledger 3
worldE = worldD :< mkE 1 Nothing
           (PWorkClosed "c1" RShipped (MkNonEmptyText "done" Oh)
              DWitnessed (WRRow 1) False)

-- R-composite-1 GREEN/Refl: zero children (root alone), never hand-closed --
-- never discharges (the vacuous-truth foreclosure, ELSE arm, StOpen leg).
rc1 : effectiveState Autoharn.worldA "a" True StOpen = ESOpen
rc1 = Refl

-- R-composite-2 GREEN/Refl: one child, still open -> parent stays open.
rc2 : effectiveState Autoharn.worldD "p" True StOpen = ESOpen
rc2 = Refl

-- R-composite-3 GREEN/Refl: the one child closes -> parent derives
-- discharged, no authored close row on "p" anywhere in worldE.
rc3 : effectiveState Autoharn.worldE "p" True StOpen = ESDischargedByObligations
rc3 = Refl

-- R-composite-4 GREEN/Refl (Element 4 fix, CORRECTED BEHAVIOR): a HAND-CLOSED
-- composite ("p" read as StClosed) whose child is still open (worldD) re-
-- opens -- derived state ALWAYS wins over a hand-close (spec sec-3b), which
-- the prior code could not produce (it ignored ItemState for every composite
-- item and never returned ESOpen from a StClosed input).
rc4 : effectiveState Autoharn.worldD "p" True (StClosed RShipped) = ESOpen
rc4 = Refl

-- R-composite-5 GREEN/Refl (Element 4 fix, CORRECTED BEHAVIOR): the SAME
-- hand-closed composite, but the child has since closed (worldE) -- blockers
-- are now empty, so the hand-close is respected and reads ESClosed, exactly
-- the raw resolution the writer supplied. The prior code could not produce
-- this either (it never read ESClosed for a composite item at all).
rc5 : effectiveState Autoharn.worldE "p" True (StClosed RShipped) = ESClosed RShipped
rc5 = Refl

-- world G: a composite root "z" opened ALONE -- no children, no close row of
-- any kind (worldA is deliberately not reused here: it already carries a
-- deferred, unattested close on "a", which would itself contribute a
-- review_unresolved blocker on the root and confound this fixture's point).
worldG : Ledger 1
worldG = Lin :< mkE 1 Nothing (PWorkOpened "z" "solo" Nothing True)

-- R-composite-6 GREEN/Refl (Element 4 fix, NO CHILD-COUNT IN THE HAND-CLOSE
-- BRANCH): a hand-closed composite with ZERO children (worldG) still reads
-- ESClosed -- the SQL's `c.slug IS NOT NULL` arm has no `cc.n >= 1` test,
-- unlike the never-hand-closed ELSE arm (rc1). The prior code's single
-- unconditional `hasDirectChild` gate would have read this as ESOpen,
-- silently overriding a resolved hand-close for want of children it was
-- never asked to have.
rc6 : effectiveState Autoharn.worldG "z" True (StClosed RDropped) = ESClosed RDropped
rc6 = Refl

-- R33a RED (Element 2, STRICT-BY-TYPE): closing composite "p" (worldD: child
-- "c1" still OPEN) with the WRITER-SUPPLIED strict flag set to False still
-- routes into the strict branch -- composite-ness alone widens the entry
-- condition (isComposite worldD "p" = True, read off p's own PWorkOpened row)
-- -- and the obligation tree is unresolved, so strictPremise evaluates False
-- and the term does not construct. This is the fixture task 1 names: a
-- composite hand-close with an open child fails WITHOUT the strict flag set.
failing
  r33a : ValidPayload Autoharn.worldD
           (PWorkClosed "p" RDropped Nothing DWitnessed
              (WRRow 1) False)
  r33a = VClose Oh Oh

-- R33b GREEN: the SAME composite close (strict=False, worldE this time --
-- child "c1" now closed) succeeds, because composite-ness routed it into the
-- strict branch and the obligation tree IS resolved -- "the type sets the
-- flag" (spec's own words) does not mean composite closes are unconditionally
-- refused, only that they are unconditionally strict.
r33b : ValidPayload Autoharn.worldE
         (PWorkClosed "p" RDropped Nothing DWitnessed
            (WRRow 1) False)
r33b = VClose Oh Oh

-- ===========================================================================
-- §7b  THE s36-s41 PARITY FIXTURES (both polarities per new mechanism; a
--      `failing` block is the refusal witnessed at elaboration time, a Refl
--      is the derivation computed on a concrete world at compile time).
-- ===========================================================================

||| Draft-entry maker for the entry-level (boundaryOk) fixtures.
mkD : PrincipalId -> Maybe (Fin n) -> Payload Draft n -> Entry Draft n
mkD a sup p = MkEntry "" "" a Nothing sup Nothing Nothing [] p

-- s36: standing decisions -- graded in-force decisions only, retraction drops.
worldS36 : Ledger 2
worldS36 = Lin :< mkE 1 Nothing (PDecision (Just "durable"))
               :< mkE 1 Nothing (PDecision Nothing)

s36a : standingDecisionIds Autoharn.worldS36 = [0]
s36a = Refl

worldS36b : Ledger 3
worldS36b = worldS36 :< mkE 1 (Just 0) (PProse KNote)   -- retract the graded one

s36b : standingDecisionIds Autoharn.worldS36b = []
s36b = Refl

-- s37: the debt/record split on the one representable member (dangling dep).
worldVD : Ledger 2
worldVD = Lin :< mkE 1 Nothing (PWorkOpened "d" "t" Nothing False)
              :< mkE 1 Nothing (PWorkDepends "d" "ghost" Informs)

s37a1 : danglingDepDebt Autoharn.worldVD = [1]      -- open debt
s37a1 = Refl
s37a2 : danglingDepHistory Autoharn.worldVD = [1]   -- record agrees while unanswered
s37a2 = Refl

worldVD2 : Ledger 3
worldVD2 = worldVD :< mkE 2 Nothing
             (PViolationDisposition "depends_on_unknown_slug" 1 True Nothing)

s37b1 : danglingDepDebt Autoharn.worldVD2 = []      -- disposition answers the debt...
s37b1 = Refl
s37b2 : danglingDepHistory Autoharn.worldVD2 = [1]  -- ...the record never thins
s37b2 = Refl

-- s38 GREEN: a bookkeeping close carries a commit-shaped ref (the Pi demands it).
bookkeepingClose : Payload Recorded 3
bookkeepingClose = PWorkClosed "spike" RDropped Nothing DBookkeeping
                     (MkCommitRef "commit:abc1234" Oh) False

-- s38 RED: a non-commit-shaped ref does not elaborate (isCommitShaped = False,
-- So is uninhabited).
failing
  badBookkeeping : Payload Recorded 3
  badBookkeeping = PWorkClosed "spike" RDropped Nothing DBookkeeping
                     (MkCommitRef "not-a-commit" Oh) False

-- s38 RED: strict + bookkeeping is a contradiction in terms (the s38 ELSIF) --
-- strictPremise evaluates False, So uninhabited.
failing
  r38 : ValidPayload Autoharn.worldA
          (PWorkClosed "a" RDropped Nothing DBookkeeping
             (MkCommitRef "commit:abc1234" Oh) True)
  r38 = VClose Oh Oh

-- s39: blocks-start claim-time foreclosure.
worldBS : Ledger 3
worldBS = Lin :< mkE 1 Nothing (PWorkOpened "p" "antecedent" Nothing False)
              :< mkE 1 Nothing (PWorkOpened "q" "dependent" Nothing False)
              :< mkE 1 Nothing (PWorkDepends "q" "p" BlocksStart)

-- RED: claiming "q" while its blocks-start antecedent "p" is not closed.
failing
  r39a : ValidPayload Autoharn.worldBS (PWorkClaimed "q")
  r39a = VClaim Oh Oh Oh

-- GREEN: "p" itself has no antecedents -- vacuously claimable (work_startable's
-- own NOT EXISTS posture).
r39b : ValidPayload Autoharn.worldBS (PWorkClaimed "p")
r39b = VClaim Oh Oh Oh

worldBS2 : Ledger 4
worldBS2 = worldBS :< mkE 1 Nothing
             (PWorkClosed "p" RDropped Nothing DDeferred Nothing False)

-- GREEN: the antecedent closed -- the same claim now constructs.
r39c : ValidPayload Autoharn.worldBS2 (PWorkClaimed "q")
r39c = VClaim Oh Oh Oh

-- RED: a blocks-start self-edge is refused (s39, mirroring s30's own).
failing
  r39d : ValidPayload Autoharn.worldBS (PWorkDepends "q" "q" (Just BlocksStart))
  r39d = VDepBS Oh Oh Oh Oh

-- s40: standing, both construction orders, revoked dominates; write refusals.
-- worldP: principal 2 (human) and 3 (model) registered; 3 suspended THEN revoked.
worldP : Ledger 4
worldP = Lin :< mkE 1 Nothing (PPrincipalRegistered 2 ACHuman (MkNonEmptyText "human fixture" Oh))
             :< mkE 1 Nothing (PPrincipalRegistered 3 ACModel (MkNonEmptyText "model fixture" Oh))
             :< mkE 1 Nothing (PPrincipalSuspended 3 True)
             :< mkE 1 Nothing (PPrincipalRevoked 3)

-- worldQ: the SAME two events for 3 in the OPPOSITE order (revoke then suspend).
worldQ : Ledger 4
worldQ = Lin :< mkE 1 Nothing (PPrincipalRegistered 2 ACHuman (MkNonEmptyText "human fixture" Oh))
             :< mkE 1 Nothing (PPrincipalRegistered 3 ACModel (MkNonEmptyText "model fixture" Oh))
             :< mkE 1 Nothing (PPrincipalRevoked 3)
             :< mkE 1 Nothing (PPrincipalSuspended 3 True)

p40a : principalStanding Autoharn.worldP 3 = PsRevoked   -- suspend-then-revoke
p40a = Refl
p40b : principalStanding Autoharn.worldQ 3 = PsRevoked   -- revoke-then-suspend: same verdict
p40b = Refl
p40c : principalStanding Autoharn.worldP 2 = PsActive
p40c = Refl
p40d : principalStanding Autoharn.worldP 1 = PsUnregisteredLegacy  -- the legacy anchor
p40d = Refl

-- s40 write boundary: a revoked actor's entry fails boundaryOk; the legacy
-- anchor (actor 1, no registration event) stays writable -- never bricked.
b40a : boundaryOk Autoharn.worldP (mkD 3 Nothing (PProse KNote)) = False
b40a = Refl
b40b : boundaryOk Autoharn.worldP (mkD 1 Nothing (PProse KNote)) = True
b40b = Refl

-- worldR: both classes registered, nobody suspended -- the s41 fixtures' base.
worldR : Ledger 2
worldR = Lin :< mkE 1 Nothing (PPrincipalRegistered 2 ACHuman (MkNonEmptyText "human fixture" Oh))
             :< mkE 1 Nothing (PPrincipalRegistered 3 ACModel (MkNonEmptyText "model fixture" Oh))

-- s41 GREEN: a key binds to a HUMAN subject.
k41a : ValidPayload Autoharn.worldR
         (PKeyBound 2 (MkFingerprint "ABCDEF0123456789ABCDEF0123456789ABCDEF01" Oh) True)
k41a = VKeyBound Oh

-- s41 RED: an agent key is refused (classOf = Just ACModel, So uninhabited).
failing
  k41b : ValidPayload Autoharn.worldR
           (PKeyBound 3 (MkFingerprint "ABCDEF0123456789ABCDEF0123456789ABCDEF01" Oh) True)
  k41b = VKeyBound Oh

-- s41 RED: a malformed fingerprint does not elaborate (shape refinement).
failing
  k41c : Fingerprint
  k41c = MkFingerprint "abc" Oh

-- s41 GREEN: canonical same-natural-person (subject 2 < object 3).
r41a : ValidPayload Autoharn.worldR (PRelationAsserted 2 SameNaturalPerson 3 True)
r41a = VRelate Oh Oh

-- s41 RED: the non-canonical ordering is refused (the kernel's plain CHECK).
failing
  r41b : ValidPayload Autoharn.worldR (PRelationAsserted 3 SameNaturalPerson 2 True)
  r41b = VRelate Oh Oh

-- s41 RED: a self-relation is refused for every relation value.
failing
  r41c : ValidPayload Autoharn.worldR (PRelationAsserted 2 Succeeds 2 True)
  r41c = VRelate Oh Oh

-- s41 GREEN: an active competence grant carries (band, basis) mandatorily.
c41a : ValidPayload Autoharn.worldR
         (PCompetenceGranted 3 (MkNonEmptyText "sql-review" Oh) True
            (MkNonEmptyText "B" Oh, MkNonEmptyText "track record" Oh))
c41a = VCompetenceGranted

-- s41 RED: a WITHDRAWAL carrying band/basis is unrepresentable BY TYPE
-- (CompetenceValueF False = (); the pair does not even typecheck -- stronger
-- than the SQL's construction-time refusal, noted at CompetenceValueF).
failing
  c41b : Payload Recorded 2
  c41b = PCompetenceGranted 3 (MkNonEmptyText "sql-review" Oh) False
           (MkNonEmptyText "B" Oh, MkNonEmptyText "track record" Oh)

-- s41 entry-level: an INACTIVE binding row without a supersedes target fails
-- boundaryOk (inactive-from-birth unrepresentable at commit); with one, it
-- passes.
b41a : boundaryOk Autoharn.worldR
         (mkD 1 Nothing (PRoleBound 3 (MkNonEmptyText "scout" Oh) False)) = False
b41a = Refl
b41b : boundaryOk Autoharn.worldR
         (mkD 1 (Just 0) (PRoleBound 3 (MkNonEmptyText "scout" Oh) False)) = True
b41b = Refl

-- s41 D-6 (human-attested scoping): a managerial claim by a MODEL actor fails
-- boundaryOk; by the HUMAN actor it passes; technical stays class-blind.
b41c : boundaryOk Autoharn.worldR
         (mkD 3 Nothing (PReview 0 (MkReviewDetail Attest Managerial "b" Nothing ()))) = False
b41c = Refl
b41d : boundaryOk Autoharn.worldR
         (mkD 2 Nothing (PReview 0 (MkReviewDetail Attest Managerial "b" Nothing ()))) = True
b41d = Refl
b41e : boundaryOk Autoharn.worldR
         (mkD 3 Nothing (PReview 0 (MkReviewDetail Attest Technical "b" Nothing ()))) = True
b41e = Refl

-- ---------------------------------------------------------------------------
-- §7c  THE s43 FIXTURES (both polarities): a write_refused row exists as an
--      ordinary committed row; R6 makes it unretractable at the boundary.
-- ---------------------------------------------------------------------------

||| a note (row 0) and a journaled refusal (row 1) -- the refusal row is
||| ordinary ledger content now, the s43 point.
worldWF : Ledger 2
worldWF = Lin :< mkE 1 Nothing (PProse KNote)
              :< mkE 1 Nothing (PWriteRefused (MkNonEmptyText "P0001" Oh)
                                  (MkNonEmptyText "Ledger policy: refused" Oh)
                                  SurfLedger
                                  (MkNonEmptyText "deadbeef" Oh)
                                  (Just 1) (MkNonEmptyText "bork" Oh))

-- s43 GREEN: the refusal payload judgment carries no premise of its own.
k43a : ValidPayload Autoharn.worldWF
         (PWriteRefused (MkNonEmptyText "23505" Oh) (MkNonEmptyText "dup" Oh)
            SurfRegistration (MkNonEmptyText "beef" Oh) Nothing
            (MkNonEmptyText "bork" Oh))
k43a = VWriteRefused

-- s43 R6 RED: superseding the write_refused row (index 1) fails boundaryOk --
-- the hiding is unrepresentable at the boundary, not merely traceable.
b43a : boundaryOk Autoharn.worldWF (mkD 1 (Just 1) (PProse KNote)) = False
b43a = Refl
-- s43 R6 GREEN: superseding the ORDINARY row (index 0) stays legal -- R6
-- confines unretractability to the one kind, s31 uniformity elsewhere.
b43b : boundaryOk Autoharn.worldWF (mkD 1 (Just 0) (PProse KNote)) = True
b43b = Refl

-- ---------------------------------------------------------------------------
-- §7d  THE s45 FIXTURES (standing lifecycle -- both polarities per mechanism).
-- ---------------------------------------------------------------------------

-- worldL: humans/models registered, then principal 3 suspended (active=True:
-- an in-force-candidate suspension, the s45 discriminator).
worldL : Ledger 3
worldL = Lin :< mkE 1 Nothing (PPrincipalRegistered 2 ACHuman (MkNonEmptyText "human fixture" Oh))
             :< mkE 1 Nothing (PPrincipalRegistered 3 ACModel (MkNonEmptyText "model fixture" Oh))
             :< mkE 1 Nothing (PPrincipalSuspended 3 True)

p45a : principalStanding Autoharn.worldL 3 = PsSuspended
p45a = Refl

-- THE LIFT: a same-kind, active=False row superseding the suspension (row 2),
-- written by ANOTHER active principal (2) -- the pre-s45 model could not
-- spell this row at all.
worldL2 : Ledger 4
worldL2 = worldL :< mkE 2 (Just 2) (PPrincipalSuspended 3 False)

-- GREEN/Refl: the lift lifts -- the lift row is itself unsuperseded and of
-- kind principal_suspended, and WITHOUT the s45 active filter it would read
-- as suspended forever ("worse than unbuilt"); with it, standing returns to
-- active.
p45b : principalStanding Autoharn.worldL2 3 = PsActive
p45b = Refl

-- s45 entry-level, both polarities: a lift must supersede its suspension
-- (retraction anchored); a suspended principal cannot write its own lift
-- (actor standing -- s45's teach-text: "an act of ANOTHER active principal").
b45a : boundaryOk Autoharn.worldL (mkD 2 Nothing (PPrincipalSuspended 3 False)) = False
b45a = Refl
b45b : boundaryOk Autoharn.worldL (mkD 2 (Just 2) (PPrincipalSuspended 3 False)) = True
b45b = Refl
b45c : boundaryOk Autoharn.worldL (mkD 3 (Just 2) (PPrincipalSuspended 3 False)) = False
b45c = Refl

-- worldRv: principal 3 registered then revoked.
worldRv : Ledger 2
worldRv = Lin :< mkE 1 Nothing (PPrincipalRegistered 3 ACModel (MkNonEmptyText "model fixture" Oh))
              :< mkE 1 Nothing (PPrincipalRevoked 3)

-- k45a RED: TERMINAL BY TYPE -- a lift-shaped revocation row does not even
-- have a flag position to spell (PPrincipalRevoked takes one argument);
-- mirrors principal_binding_active_kind_shape's deliberate omission.
failing
  k45a : Payload Recorded 2
  k45a = PPrincipalRevoked 3 False

-- s45 §3.4 at the boundary, both polarities: a cross-kind supersession of a
-- revocation is refused (the silent-reinstatement hole, closed); a same-kind
-- same-subject correction stays legal; a subject-discontinuous one is
-- refused.
b45d : boundaryOk Autoharn.worldRv (mkD 1 (Just 1) (PProse KNote)) = False
b45d = Refl
b45e : boundaryOk Autoharn.worldRv (mkD 1 (Just 1) (PPrincipalRevoked 3)) = True
b45e = Refl
b45f : boundaryOk Autoharn.worldRv (mkD 1 (Just 1) (PPrincipalRevoked 4)) = False
b45f = Refl

-- GREEN/Refl: a same-kind CORRECTION of a revocation preserves the revoked
-- reading (the corrected chain's terminal row is still a revocation).
worldRv2 : Ledger 3
worldRv2 = worldRv :< mkE 1 (Just 1) (PPrincipalRevoked 3)
p45c : principalStanding Autoharn.worldRv2 3 = PsRevoked
p45c = Refl

-- worldDcl0/worldDcl: the resurrection fixture. Two independent
-- (non-superseding) declarations bind "vsr_rw" -- p2 (row 0) then p3
-- (row 1); then p3's is UNBOUND (same-kind, active=False, supersedes row 1).
worldDcl0 : Ledger 2
worldDcl0 = Lin :< mkE 1 Nothing (PStandingDeclared 2 "vsr_rw" True)
                :< mkE 1 Nothing (PStandingDeclared 3 "vsr_rw" True)

worldDcl : Ledger 3
worldDcl = worldDcl0 :< mkE 1 (Just 1) (PStandingDeclared 3 "vsr_rw" False)

-- GREEN/Refl: before the unbind, the latest declaration governs.
g45b : principalRole Autoharn.worldDcl0 "vsr_rw" = Just 3
g45b = Refl

-- GREEN/Refl, THE RESURRECTION FORECLOSED: after the unbind the role is
-- UNDECLARED (Nothing) -- NOT Just 2. The unbind row itself governs (latest
-- unsuperseded declaration REGARDLESS of flag) and, being inactive, emits
-- nothing; a naive active-filtered selection would have silently re-bound
-- the role to p2, a principal nobody chose (s45 Element 2's named trap).
g45a : principalRole Autoharn.worldDcl "vsr_rw" = Nothing
g45a = Refl

-- GREEN/Refl: re-bind after unbind by a FRESH declaration (higher id,
-- active) -- zero special-casing.
worldDcl2 : Ledger 4
worldDcl2 = worldDcl :< mkE 1 Nothing (PStandingDeclared 4 "vsr_rw" True)
g45c : principalRole Autoharn.worldDcl2 "vsr_rw" = Just 4
g45c = Refl

-- The three-valued row-force read itself, all three values on one world:
g45d : rowForce Autoharn.worldDcl 1 = RFSuperseded
g45d = Refl
g45e : rowForce Autoharn.worldDcl 2 = RFRetracted
g45e = Refl
g45f : rowForce Autoharn.worldDcl 0 = RFAsserting
g45f = Refl

-- s45 §3.4 declaration arms at the boundary: role mismatch refused; an
-- unbind naming a different subject refused; a ROTATION (active=True) may
-- repoint the subject by design; cross-kind refused.
b45g : boundaryOk Autoharn.worldDcl0 (mkD 1 (Just 1) (PStandingDeclared 3 "other_role" True)) = False
b45g = Refl
b45h : boundaryOk Autoharn.worldDcl0 (mkD 1 (Just 1) (PStandingDeclared 4 "vsr_rw" False)) = False
b45h = Refl
b45i : boundaryOk Autoharn.worldDcl0 (mkD 1 (Just 1) (PStandingDeclared 4 "vsr_rw" True)) = True
b45i = Refl
b45j : boundaryOk Autoharn.worldDcl0 (mkD 1 (Just 1) (PProse KNote)) = False
b45j = Refl

-- ---------------------------------------------------------------------------
-- §7e  THE s44 FIXTURES (typed attestation shape, coupling both polarities).
-- ---------------------------------------------------------------------------

attModel : NonEmptyText
attModel = MkNonEmptyText "claude-fable-5" Oh
attSess : NonEmptyText
attSess = MkNonEmptyText "otel-sess-1" Oh
attBasis : NonEmptyText
attBasis = MkNonEmptyText "command,session" Oh

-- GREEN: a mismatch attestation with its declared expectation (coupling
-- satisfied by the index).
k44a : Payload Recorded 3
k44a = PModelAttested 1 Autoharn.attModel GExactCommand Autoharn.attSess
         Autoharn.attBasis True AVMismatch (MkNonEmptyText "claude-opus-4" Oh)

-- GREEN: unevaluated with NO expectation (ExpectedF False = ()).
k44b : Payload Recorded 3
k44b = PModelAttested 1 Autoharn.attModel GAmbiguous Autoharn.attSess
         Autoharn.attBasis False AVUnevaluated ()

-- RED: an unevaluated verdict WITH a declared expectation is unrepresentable
-- (attest_expected_verdict_coupling, the stronger rendering).
failing
  k44c : Payload Recorded 3
  k44c = PModelAttested 1 Autoharn.attModel GAmbiguous Autoharn.attSess
           Autoharn.attBasis False AVUnevaluated (MkNonEmptyText "x" Oh)

-- RED: a match claim with nothing to match against is unrepresentable
-- (AVMatch demands the True index).
failing
  k44d : Payload Recorded 3
  k44d = PModelAttested 1 Autoharn.attModel GExactCommand Autoharn.attSess
           Autoharn.attBasis False AVMatch ()

-- ---------------------------------------------------------------------------
-- §7f  THE s46 FIXTURES (defeat calculus; the fork's both-polarity pair).
-- ---------------------------------------------------------------------------

grantAct : NonEmptyText
grantAct = MkNonEmptyText "model-identity-attestation" Oh
bandB : NonEmptyText
bandB = MkNonEmptyText "B" Oh
basisTR : NonEmptyText
basisTR = MkNonEmptyText "track record" Oh

-- worldDF (the AGREE world): a prose target (row 0), the defeat grant to
-- principal 2 (row 1), and 2's mismatch attestation of row 0 (row 2).
-- Nothing superseded -- lemma 1's regime, the two horns agree.
worldDF : Ledger 3
worldDF = Lin :< mkE 1 Nothing (PProse KNote)
              :< mkE 1 Nothing (PCompetenceGranted 2 Autoharn.grantAct True
                                  (Autoharn.bandB, Autoharn.basisTR))
              :< mkE 2 Nothing (PModelAttested 0 Autoharn.attModel GExactCommand
                                  Autoharn.attSess Autoharn.attBasis
                                  True AVMismatch (MkNonEmptyText "claude-opus-4" Oh))

s44a : modelAttestations Autoharn.worldDF = [(2, 0)]
s44a = Refl

d46a : defeatedRows (rawInputAt Autoharn.worldDF) Autoharn.worldDF = [(0, 2)]
d46a = Refl
d46b : defeatedRows (curInputAt Autoharn.worldDF) Autoharn.worldDF = [(0, 2)]
d46b = Refl
c46a : creditedCurrentIds (curInputAt Autoharn.worldDF) Autoharn.worldDF = [1, 2]
c46a = Refl

-- worldDG (the DIVERGENCE world): grant to 2 (row 0); attestation X by 2
-- targeting the grant (row 1 -- defeats nothing: its target is an in-force
-- defeat-input row under BOTH horns); a note superseding X (row 2 -- legal:
-- s44 attestations are deliberately supersession-retractable); attestation Y
-- by 2 targeting the now-SUPERSEDED X (row 3). Y's target is a superseded
-- defeat-KIND row -- lemma 3's regime, the exact divergence class.
worldDG : Ledger 4
worldDG = Lin :< mkE 1 Nothing (PCompetenceGranted 2 Autoharn.grantAct True
                                  (Autoharn.bandB, Autoharn.basisTR))
              :< mkE 2 Nothing (PModelAttested 0 Autoharn.attModel GSessionScoped
                                  Autoharn.attSess Autoharn.attBasis
                                  True AVMismatch (MkNonEmptyText "claude-opus-4" Oh))
              :< mkE 1 (Just 1) (PProse KNote)
              :< mkE 2 Nothing (PModelAttested 1 Autoharn.attModel GExactCommand
                                  Autoharn.attSess Autoharn.attBasis
                                  True AVMismatch (MkNonEmptyText "claude-opus-4" Oh))

-- BOTH POLARITIES OF THE FORK, Refl: the superseded s46-era current-scoped
-- horn let Y defeat the superseded attestation X; the raw-history horn --
-- THE RULED SEMANTICS (s50, row 1647) -- excludes X as machinery input
-- forever. Same world, different with-cause surfaces; d46d is what an s50+
-- world computes, d46c the R7-style record of what s46 would have.
d46c : defeatedRows (curInputAt Autoharn.worldDG) Autoharn.worldDG = [(1, 3)]
d46c = Refl
d46d : defeatedRows (rawInputAt Autoharn.worldDG) Autoharn.worldDG = []
d46d = Refl

-- s50 GREEN/Refl: the adjudicated kernel reads, both worlds -- the agree
-- world unchanged by the ruling, the divergence world protectively empty
-- (nothing newly defeatable, the ruling's own fail-safe ground).
d50a : defeatedRowsKernel Autoharn.worldDF = [(0, 2)]
d50a = Refl
d50b : defeatedRowsKernel Autoharn.worldDG = []
d50b = Refl

-- ...and the fork is INVISIBLE to credited_current (the superseded target is
-- already absent from it) -- witnessed here on the divergence world, argued
-- in prose at inputsDivergeSuperseded, not machine-proved in general.
c46b : creditedCurrentIds (curInputAt Autoharn.worldDG) Autoharn.worldDG = [0, 2, 3]
c46b = Refl
c46c : creditedCurrentIds (rawInputAt Autoharn.worldDG) Autoharn.worldDG = [0, 2, 3]
c46c = Refl

-- ---------------------------------------------------------------------------
-- §7g  THE TOTAL WRITE VERDICT FIXTURES (both arms land a row -- the type
--      already says so; these witness WHICH row).
-- ---------------------------------------------------------------------------

wbRole : NonEmptyText
wbRole = MkNonEmptyText "vsr_rw" Oh

-- GREEN/Refl: an accepted draft lands as its recorded self (head is not a
-- refusal row).
w43a : headRefused (write 9 Autoharn.wbRole Autoharn.worldA
                      (mkD 1 Nothing (PProse KNote))) = False
w43a = Refl

-- GREEN/Refl (the refusal ARM, s47's own specimen): claiming the closed "a"
-- is refused-and-JOURNALED -- the head of the grown ledger is the
-- write_refused row, at the ledger surface. The draft that red fixture r8e
-- proves unconstructable is exactly the one this arm survives totally.
w43b : headRefused (write 9 Autoharn.wbRole Autoharn.worldA
                      (mkD 1 Nothing (PWorkClaimed "a"))) = True
w43b = Refl
w43c : headSurface (write 9 Autoharn.wbRole Autoharn.worldA
                      (mkD 1 Nothing (PWorkClaimed "a"))) = Just SurfLedger
w43c = Refl

-- GREEN/Refl: an entry-level refusal journals at the surface of its PAYLOAD
-- family -- a revoked actor's registration-family write refuses at the
-- registration surface (worldP: principal 3 is revoked).
w43d : headRefused (write 9 Autoharn.wbRole Autoharn.worldP
                      (mkD 3 Nothing (PPrincipalSuspended 2 True))) = True
w43d = Refl
w43e : headSurface (write 9 Autoharn.wbRole Autoharn.worldP
                      (mkD 3 Nothing (PPrincipalSuspended 2 True))) = Just SurfRegistration
w43e = Refl
