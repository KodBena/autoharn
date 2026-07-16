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
||| AS-OF: kernel chain through s35 LAGGING: s36 (decision-grade: nullable writer-supplied
|||   grade on decision rows + standing_decisions in-force view, ratified spec
|||   design/FABLE-GRADED-DECISIONS-SPEC.md) is additive vocabulary not yet transcribed --
|||   a parity pass should model the grade at the write boundary and the standing view as
|||   a derived read. (verified through s35, no semantic delta to transcribe since s33:
|||   s34 adds the kernel-side refusal of a writer-supplied discharge_grade -- an illegal
|||   state this model's Draft-stage index already made UNREPRESENTABLE (GradeF Draft = ()),
|||   so the substrate caught up to the model, not vice versa; s35 is a behavior-identical
|||   dispatcher refactor of validate_work_item, every refusal text byte-identical by its
|||   own leaf-manifest gate's witness. Same shapes, same derivations, same refusals.)
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

||| s29 Element B: the two close constructors. A review-silent close is
||| unrepresentable (post-epoch; see the epoch-gate fidelity note, header).
data ReviewDisposition = DWitnessed | DDeferred

||| s30 typed dependency edges; closed vocabulary, 'supersedes' actively
||| refused as a reserved word (a vocabulary refusal the closed data type
||| renders by omission).
data EdgeType = BlocksClose | Informs

Eq EdgeType where
  BlocksClose == BlocksClose = True
  Informs     == Informs     = True
  _           == _           = False

||| R3: the eight s15 prose kinds, single-homed as one constructor's argument.
data ProseKind = KAssumption | KDecision | KQuestion | KVerification
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
isWitnessed DWitnessed = True
isWitnessed DDeferred  = False

||| s22 work_shipped_requires_witness, via Gated.
witnessTy : Resolution -> Type
witnessTy r = Gated (isShipped r) NonEmptyText

||| s29 work_review_witnessed_requires_ref, same idiom one column over.
reviewRefTy : ReviewDisposition -> Type
reviewRefTy d = Gated (isWitnessed d) NonEmptyText

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
data Payload : (st : Stage) -> (n : Nat) -> Type where
  PProse      : ProseKind -> Payload st n
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
              -> (disp : ReviewDisposition) -> reviewRefTy disp
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

||| s29 Element C at the root: strict close needs a witnessed disposition and
||| an empty blocker set (IN-FORCE, via strictBlockers, §4); non-strict
||| closes carry no premise.
strictPremise : {n : Nat} -> Ledger n -> Slug -> (strict : Bool)
             -> ReviewDisposition -> Bool
strictPremise l s False _          = True
strictPremise l s True  DDeferred  = False
strictPremise l s True  DWitnessed = null (strictBlockers l s)

||| The write-boundary judgment: which appends the kernel accepts, one
||| constructor per licensed Payload shape. Raw-vs-derived domains kept per
||| s31's allowlist: freshness/opened/cycle premises quantify RAW; the
||| strict-close premise quantifies the projection (via strictBlockers).
||| Both visible in one indexed family -- the model keeps the two
||| quantification domains it must, rather than uniformizing them away.
data ValidPayload : {n : Nat} -> Ledger n -> Payload Draft n -> Type where
  VProse  : ValidPayload l (PProse k)
  ||| regards earlier-row: already unrepresentable via Fin n (unchanged).
  VReview : ValidPayload l (PReview r d)
  ||| An opening act: the slug must be fresh in RAW history (slug burned --
  ||| no constructor exists that re-opens; a genuine redo is a NEW slug).
  VOpen   : (0 fresh : So (not (everOpened l s)))
         -> ValidPayload l (PWorkOpened s title parent comp)
  ||| Claim: the slug must have an opening act (raw read).
  VClaim  : (0 opened : So (everOpened l s))
         -> ValidPayload l (PWorkClaimed s)
  ||| informs / untyped keep s22's deliberately lax posture: dangling
  ||| antecedent NOT refused (the violations view reads it) -- no ant premise.
  VDepLax : (0 opened : So (everOpened l s))
         -> (0 lax : So (not (et == Just BlocksClose)))
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
recordPayload l st (PReview r (MkReviewDetail v i b a ())) =
  let tgt = case entryAt l r of (_ ** e) => e.stamp
  in PReview r (MkReviewDetail v i b a (gradeLadder (stampPair st) (stampPair tgt)))
recordPayload l st (PWorkOpened s t p c) = PWorkOpened s t p c
recordPayload l st (PWorkClaimed s)      = PWorkClaimed s
recordPayload l st (PWorkDepends s a Nothing)   = PWorkDepends s a Informs  -- s30 default
recordPayload l st (PWorkDepends s a (Just et)) = PWorkDepends s a et
recordPayload l st (PWorkClosed s r w d f b)    = PWorkClosed s r w d f b

||| The sanctioned growth step: the write boundary as the ONLY exported
||| introduction form for a bigger ledger (in a multi-module rendering (:<)
||| would be hidden and `append` the API -- trigger-as-smart-constructor).
append : {n : Nat} -> (l : Ledger n) -> (e : Entry Draft n)
      -> (0 ok : ValidPayload l e.payload) -> Ledger (S n)
append l e _ = l :< MkEntry e.session e.statement e.actor e.stamp e.supersedes
                          e.amends e.answers e.enacts (recordPayload l e.stamp e.payload)

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

-- ... a shipped close carries its witness (the Pi demands it) ...
shippedClose : Payload Recorded 3
shippedClose = PWorkClosed "fix-gate" RShipped
                 (MkNonEmptyText "seen-red/gate-run.txt" Oh)
                 DWitnessed (MkNonEmptyText "ledger row 42" Oh)
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
-- work_review_witnessed_requires_ref, same idiom one column over.
failing "Mismatch between: Maybe"
  badWitnessed : Payload Recorded 3
  badWitnessed = PWorkClosed "fix-gate" RDropped Nothing DWitnessed Nothing False

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
              DWitnessed (MkNonEmptyText "ledger row 2" Oh) False)

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
              (MkNonEmptyText "row 1" Oh) False)
  r33a = VClose Oh Oh

-- R33b GREEN: the SAME composite close (strict=False, worldE this time --
-- child "c1" now closed) succeeds, because composite-ness routed it into the
-- strict branch and the obligation tree IS resolved -- "the type sets the
-- flag" (spec's own words) does not mean composite closes are unconditionally
-- refused, only that they are unconditionally strict.
r33b : ValidPayload Autoharn.worldE
         (PWorkClosed "p" RDropped Nothing DWitnessed
            (MkNonEmptyText "row 1" Oh) False)
r33b = VClose Oh Oh
