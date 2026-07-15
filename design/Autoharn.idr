||| Autoharn.idr -- categorical documentation of the autoharn kernel semantics.
||| TRANSCRIPTION, not design: renders the EXISTING semantics of
|||   kernel/lineage/s15,s22,s29,s30 + engine/lp/ledger_tnow.lp,work_items.lp
|||   + design/FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md
|||   + design/FABLE-COMPOSITE-DISCHARGE-SPEC.md
||| Black-box mocks at every boundary (Postgres, clingo, git, hook transport are
||| opaque). Where the rendering fights the language, the fight is the finding;
||| fidelity notes live in the report, keyed to the section numbers below.
module Autoharn

import Data.Fin
import Data.List
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
-- §1  KINDS AS A SUM TYPE; KIND-SCOPED SHAPES AS CONSTRUCTOR ARGUMENTS.
--     SQL says this with one wide nullable table + two-way CHECKs of the form
--       (kind = 'work_closed') = (work_resolution IS NOT NULL)
--     which is a hand-rolled discriminated union. The constructors below say
--     the same thing natively. One-way CHECKs (work_review_ref legal only on
--     work_closed, optional there) become Maybe INSIDE the licensed
--     constructor. Conditional CHECKs (shipped => witness) become dependent
--     field types (witnessTy below) -- a Pi where SQL used a row predicate.
-- ===========================================================================

data ReviewVerdict = Attest | AttestWithReservations | Refuse

data Independence = Technical | Managerial | Financial

||| s29 discharge_grade -- COMPUTED at write time by validate_independence(),
||| never writer-asserted. The model marks that by keeping it out of the
||| writer-facing payload and in the appended record only (see §3 append).
data DischargeGrade = SamePrincipal | SameSession | DistinctSession | DistinctDeployment

||| s22 closed resolution vocabulary.
data Resolution = RShipped | RSuperseded | RDropped | RDeferred

||| s29 Element B: the two close constructors. A review-silent close is
||| unrepresentable (post-epoch; see fidelity note on the epoch gate).
data ReviewDisposition = DWitnessed | DDeferred

||| s30 typed dependency edges; closed vocabulary, 'supersedes' actively
||| refused as a reserved word (a vocabulary refusal the closed data type
||| renders by omission).
data EdgeType = BlocksClose | Informs

||| Non-empty text (SQL: btrim(x) <> ''). Proof-carrying string.
record NonEmptyText where
  constructor MkNonEmptyText
  text : String
  0 ok : So (text /= "")

||| s22 work_shipped_requires_witness, as a dependent field type:
||| shipped REQUIRES a witness; every other resolution may carry one.
witnessTy : Resolution -> Type
witnessTy RShipped = NonEmptyText
witnessTy _        = Maybe NonEmptyText

||| s29 work_review_witnessed_requires_ref, same idiom one column over.
reviewRefTy : ReviewDisposition -> Type
reviewRefTy DWitnessed = NonEmptyText
reviewRefTy DDeferred  = Maybe NonEmptyText

||| s15 review_detail (frozen-at-insert verdict payload) + s29 grade.
||| antecedent: Ruling A's typed second place for an affirmation-species
||| review (Maybe = "NULL for a plain countersign", exactly the column).
record ReviewDetail (n : Nat) where
  constructor MkReviewDetail
  verdict      : ReviewVerdict
  independence : Independence
  basis        : String
  antecedent   : Maybe (Fin n)
  grade        : DischargeGrade   -- computed, not writer-supplied: see append

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
data Payload : (n : Nat) -> Type where
  -- s15 prose kinds (shapes carried in common fields; nothing kind-scoped).
  PAssumption   : Payload n
  PDecision     : Payload n
  PQuestion     : Payload n
  PVerification : Payload n
  PFinding      : Payload n
  PSnag         : Payload n
  PRevision     : Payload n
  PNote         : Payload n
  -- s15 review: regards is MANDATORY for kind=review and RESERVED to it --
  -- the two-way trigger check is exactly "this constructor and only this
  -- constructor carries the field".
  PReview       : (regards : Fin n) -> ReviewDetail n -> Payload n
  -- s22 work-item event vocabulary + s28 parent + composite-discharge spec.
  PWorkOpened   : (slug : Slug) -> (title : String)
               -> (parent : Maybe Slug)          -- s28: set once at opening
               -> (composite : Bool)             -- composite spec s31: strict-by-type
               -> Payload n
  PWorkClaimed  : (slug : Slug) -> Payload n
  PWorkDepends  : (slug : Slug) -> (antecedent : Slug) -> (edge : EdgeType)
               -> Payload n
  PWorkClosed   : (slug : Slug)
               -> (res : Resolution) -> witnessTy res
               -> (disp : ReviewDisposition) -> reviewRefTy disp
               -> (strict : Bool)                -- s29 opt-in per close act
               -> Payload n

||| One ledger row with n earlier rows. Common (kind-independent) columns.
||| ts is deliberately OMITTED from anything that orders: id-is-order, never
||| ts (ledger_tnow.lp header). The model cannot even express a ts-keyed
||| precedence rule, which is stronger than the .lp file's comment.
record Entry (n : Nat) where
  constructor MkEntry
  session    : String
  statement  : String
  actor      : PrincipalId
  stamp      : Maybe Stamp
  supersedes : Maybe (Fin n)          -- FK is the ONE write constraint (spec §4)
  amends     : Maybe (Fin n, String)  -- target + verbatim quotation
  answers    : Maybe (Fin n)
  enacts     : List (Fin n)
  payload    : Payload n

||| §1 THE LEDGER: indexed append-only structure. The ONLY way a ledger grows
||| is one row on the right (the one_row_per_insert trigger is inherent: the
||| constructor appends exactly one). There is no update/delete constructor at
||| all -- append_only() as absence of syntax rather than a refusing trigger.
data Ledger : Nat -> Type where
  Lin  : Ledger 0
  (:<) : Ledger n -> Entry n -> Ledger (S n)

-- ===========================================================================
-- §2  THE IN-FORCE PROJECTION AS A TOTAL FUNCTION, AND THE READER TYPES.
--     ledger_tnow.lp: superseded(Y) :- sup_star(_,Y);
--                     in_force(Id) :- entry(Id,...), not superseded(Id).
--     Note superseded/1 is MONOTONE: it quantifies over edge EXISTENCE only,
--     never over the superseder's own in-force status. That monotonicity IS
--     reinstatement-freedom (§5).
-- ===========================================================================

||| Is absolute row t superseded by any row of l? Positive/monotone: the
||| superseder's own later defeat is irrelevant by construction.
supersededIn : Ledger n -> (t : Nat) -> Bool
supersededIn Lin        _ = False
supersededIn (l :< e) t =
  maybe False (\f => finToNat f == t) e.supersedes || supersededIn l t

||| The in-force projection, total by construction (a fold over finitely many
||| rows; no termination debt -- SQL pays none either, ASP pays a comment).
inForce : Ledger n -> (t : Nat) -> Bool
inForce l t = not (supersededIn l t)

||| §2 READER TYPING (the ratified judgment of the supersession spec §2).
||| A current-truth reader receives ONLY this type; its constructor is the
||| projection itself. In a multi-module rendering `MkProjection` is not
||| exported -- `project` is the sole introduction form, so "never touches raw
||| ledger" is a scope fact, not a review rule.
record Projection (n : Nat) where
  constructor MkProjection
  liveIds : List Nat            -- ids with inForce = True, ascending

project : {n : Nat} -> Ledger n -> Projection n
project {n} l = MkProjection (filter (inForce l) (allIds n))
  where
    allIds : Nat -> List Nat
    allIds Z     = []
    allIds (S k) = allIds k ++ [k]

||| A history/forensic reader is NAMED on a closed allowlist with its reason:
||| the spec's §2 list as a closed indexed type. Adding a history reader means
||| adding a constructor here -- the diff IS the allowlist amendment.
data HistoryLicense : String -> Type where
  LHashChain      : HistoryLicense "row-hash-chain: every row must chain, superseded or not"
  LLedRecent      : HistoryLicense "led --recent: displays and MARKS superseded rows"
  LDuplicateOpen  : HistoryLicense "duplicate_open arm + trigger: a retracted open still burns its slug"
  LWriteBoundary  : HistoryLicense "BEFORE INSERT triggers: cannot read a view excluding the row being inserted"

||| The two reader signatures. currentReader CANNOT mention Ledger at all;
||| historyReader must present its license.
CurrentReader : Nat -> Type -> Type
CurrentReader n a = Projection n -> a

HistoryReader : Nat -> Type -> Type
HistoryReader n a = {reason : String} -> HistoryLicense reason -> Ledger n -> a

-- ===========================================================================
-- §3  THE WORK-ITEM EVENT GRAMMAR AS AN INDEXED MACHINE.
--     TRANSCRIPTION FINDING (kernel wins over the elegant rendering): the
--     kernel's write-boundary grammar is NOT linear open->claim->close.
--     validate_work_item() (s22..s30) refuses exactly:
--       * a second work_opened for a slug that EVER had one (raw read: burned)
--       * claim/depends/close on a never-opened slug
--       * (s28) a dangling or cycle-forming parent at open
--       * (s30) a blocks-close self-edge / dangling antecedent / cycle
--       * (s29) a post-epoch close with no disposition; strict+deferred;
--         strict close with a non-empty blocker set
--     It does NOT require a claim before close, does NOT refuse a second
--     claim, and does NOT refuse a second close row. Linearity lives in the
--     PROJECTION (latest-event fold, work_item_current), not the write
--     boundary. Both layers are transcribed; conflating them would be the
--     model lying about the kernel.
-- ===========================================================================

||| Raw-history slug facts (HISTORY readers by the ratified fork: a superseded
||| open still counts -- the quantification domain is the raw ledger, which is
||| exactly how "slug burned" appears in the model: not a new mechanism but
||| WHICH structure the freshness proof quantifies over).
everOpened : Ledger n -> Slug -> Bool
everOpened Lin        _ = False
everOpened (l :< e) s = isOpen e.payload || everOpened l s
  where
    isOpen : Payload m -> Bool
    isOpen (PWorkOpened s' _ _ _) = s == s'
    isOpen _                      = False

isWorkPayload : Payload n -> Bool
isWorkPayload (PWorkOpened _ _ _ _)  = True
isWorkPayload (PWorkClaimed _)       = True
isWorkPayload (PWorkDepends _ _ _)   = True
isWorkPayload (PWorkClosed _ _ _ _ _ _) = True
isWorkPayload _                      = False

isOpenOf : Slug -> Payload n -> Bool
isOpenOf s (PWorkOpened s' _ _ _) = s == s'
isOpenOf _ _                      = False

isLaterEventOf : Slug -> Payload n -> Bool
isLaterEventOf s (PWorkClaimed s')      = s == s'
isLaterEventOf s (PWorkDepends s' _ _)  = s == s'
isLaterEventOf s (PWorkClosed s' _ _ _ _ _) = s == s'
isLaterEventOf _ _                      = False

||| The write-boundary judgment: which appends the kernel accepts.
||| So (...) fields are the trigger refusals as proof obligations; the
||| blockers-empty premise for strict closes is deferred to §4's calculus
||| (mirroring the SQL, where the trigger calls the STABLE function).
data ValidAppend : Ledger n -> Entry n -> Type where
  ||| Any non-work prose row: kind-scoped shape already carried by Payload.
  VProse   : {auto 0 notWork : So (not (isWorkPayload e.payload))}
          -> ValidAppend l e
  ||| An opening act: the slug must be fresh in RAW history (slug burned --
  ||| no constructor exists that re-opens; a genuine redo is a NEW slug).
  VOpen    : (0 fresh : So (not (everOpened l s)))
          -> {auto 0 isOp : So (isOpenOf s e.payload)}
          -> ValidAppend l e
  ||| Claim / depends / close: the slug must have an opening act (raw read).
  VLater   : (0 opened : So (everOpened l s))
          -> {auto 0 isLater : So (isLaterEventOf s e.payload)}
          -> ValidAppend l e

||| The sanctioned growth step: the write boundary as the ONLY exported
||| introduction form for a bigger ledger (in a multi-module rendering (:<)
||| is hidden and `append` is the API -- trigger-as-smart-constructor).
append : (l : Ledger n) -> (e : Entry n) -> (0 ok : ValidAppend l e) -> Ledger (S n)
append l e _ = l :< e

||| The DERIVED per-item state -- the projection-side fold that owns the
||| latest-event linearity (work_item_current). Under the supersession spec
||| these legs read the in-force subledger only (they are current-truth
||| readers re-issued to factor through the projection).
data ItemState = StOpen | StClosed Resolution

-- ===========================================================================
-- §4  THE OBLIGATION AND-TREE (work_item_strict_blockers, s29 narrowed by
--     s30) AS A DERIVED FOLD, AND COMPOSITE DISCHARGE AS A READ OF IT.
--     The tree: edges = s28 parent edges (parent->child) UNION blocks-close
--     depends edges (dependent->antecedent, walked AGAINST the column names);
--     members = reachable set from root; blockers = non-root members with no
--     close row, plus deferred-closed members lacking an un-superseded
--     distinct-actor attest. NO STORED VERDICT anywhere: empty iff resolved.
-- ===========================================================================

record Blocker where
  constructor MkBlocker
  blockingSlug : Slug
  reason       : String

||| One successor step of the combined edge relation over the raw event list.
||| (Mixed reader types, faithfully: the close leg reads raw closes -- the
||| named blind spot of composite-spec §3b -- while the review leg reads
||| supersession-aware attests. The model keeps both quantification domains
||| visible in one definition, which is exactly the finding.)
edgesOf : Ledger n -> List (Slug, Slug)   -- (parent, child) pairs
edgesOf Lin        = []
edgesOf (l :< e) = this e.payload ++ edgesOf l
  where
    this : Payload m -> List (Slug, Slug)
    this (PWorkOpened c _ (Just p) _)      = [(p, c)]
    this (PWorkDepends dep ant BlocksClose) = [(dep, ant)]  -- dependent plays parent
    this _                                  = []

||| Reachable set with fuel. ENCODING NOISE, named: SQL's recursive CTE
||| terminates by set semantics for free even on cyclic input; Idris %default
||| total demands a decreasing measure, so the walk carries fuel = row count
||| (a sound bound: each productive step adds a slug drawn from finitely many
||| rows). The kernel refuses cycles at construction for both edge kinds, but
||| this function -- like the SQL one -- must terminate on ANY stored graph.
reach : (fuel : Nat) -> List (Slug, Slug) -> (frontier : List Slug)
     -> (seen : List Slug) -> List Slug
reach Z     _  _        seen = seen
reach (S k) es frontier seen =
  let next = [ c | (p, c) <- es, elem p frontier, not (elem c seen) ] in
  case next of
    [] => seen
    _  => reach k es next (seen ++ next)

||| Does slug s have ANY close row in l? RAW read -- deliberately transcribing
||| the s29 `closes` CTE's supersession-BLINDNESS (a defeated close still reads
||| closed), the blind spot composite-spec 3b names and routes.
hasCloseIn : Ledger m -> Slug -> Bool
hasCloseIn Lin        _ = False
hasCloseIn (ll :< e) s = case e.payload of
                            PWorkClosed s' _ _ _ _ _ => s == s' || hasCloseIn ll s
                            _                        => hasCloseIn ll s

||| Deferred close with no un-superseded distinct-actor attest regarding it.
||| Sketch-level ORACLE STUB (returns False): the real lookup correlates
||| review.regards = close row id, review actor <> closer, and NOT EXISTS a
||| superseder of the review -- it needs absolute row ids threaded through the
||| fold, elided here and declared honestly. The point transcribed is the
||| CONTRAST: this leg is supersession-AWARE while hasCloseIn is raw -- two
||| different reader types inside one calculus, visible as two quantification
||| domains (see fidelity note §4).
deferredUndischargedIn : Ledger m -> Slug -> Bool
deferredUndischargedIn _ _ = False

||| The one conjunction (ADR-0012 P1: the ONE home of "is this item's
||| obligation tree resolved"). Empty iff resolved.
strictBlockers : {n : Nat} -> Ledger n -> Slug -> List Blocker
strictBlockers {n} l root =
  let members = reach n (edgesOf l) [root] [root]
      notRoot = filter (/= root) members
      notClosed = [ MkBlocker s "item is not yet closed"
                  | s <- notRoot, not (hasCloseIn l s) ]
      reviewUnres = [ MkBlocker s "review disposition deferred and undischarged"
                    | s <- members, deferredUndischargedIn l s ]
  in  notClosed ++ reviewUnres

||| Composite discharge -- A READ, never an authored act (composite spec §2:
||| "the derivation is the obligation calculus the kernel ALREADY owns").
||| Vacuous-truth hazard foreclosed: zero children => open, never discharged.
data EffectiveState = ESOpen | ESClosed Resolution | ESDischargedByObligations

effectiveState : {n : Nat} -> Ledger n -> Slug
              -> (composite : Bool) -> (hasChild : Bool) -> ItemState
              -> EffectiveState
effectiveState l s True True _ =
  case strictBlockers l s of
    [] => ESDischargedByObligations
    _  => ESOpen
effectiveState _ _ _ _ StOpen         = ESOpen
effectiveState _ _ _ _ (StClosed r)   = ESClosed r

-- ===========================================================================
-- §5  UNIFORM RETRACTION, REINSTATEMENT-FREE -- AS A THEOREM.
--     "Superseding the superseder does not revive the victim" is, precisely:
--     supersededIn is MONOTONE under append. Any extension of the ledger --
--     including a row that supersedes the victim's superseder -- preserves
--     every existing supersededness fact. Provable by induction; proved below.
-- ===========================================================================

||| Reinstatement-freedom: once superseded, superseded under every extension.
supersededStable : (l : Ledger n) -> (e : Entry n) -> (t : Nat)
                -> supersededIn l t = True
                -> supersededIn (l :< e) t = True
supersededStable l e t prf with (maybe False (\f => finToNat f == t) e.supersedes)
  supersededStable l e t prf | True  = Refl
  supersededStable l e t prf | False = prf

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
--     opposite of the differential's point. What Idris adds is the ONE
--     specification type both are held to; what it cannot state is producer
--     INDEPENDENCE, which is a provenance fact about Postgres and clingo,
--     not a property of the functions' extensions.
-- ===========================================================================

||| The specification BOTH producers answer to: the in-force id set.
InForceSpec : {n : Nat} -> Ledger n -> List Nat -> Type
InForceSpec l ids = (t : Nat) -> (elem t ids = True) -> (inForce l t = True)

record DualProducers (n : Nat) where
  constructor MkDualProducers
  sqlFloor : Ledger n -> List Nat   -- opaque: ledger_floor.py / recursive CTEs
  aspSide  : Ledger n -> List Nat   -- opaque: clingo over ledger_tnow.lp

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
--     claim). Green: legal shapes construct. Red: the `failing` block only
--     type-checks if its body is REFUSED -- the shipped-close-without-witness
--     CHECK witnessed firing at elaboration time.
-- ===========================================================================

||| GREEN: a shipped close carries its witness (the Pi demands it) ...
shippedClose : Payload 3
shippedClose = PWorkClosed "fix-gate" RShipped
                 (MkNonEmptyText "seen-red/gate-run.txt" Oh)
                 DWitnessed (MkNonEmptyText "ledger row 42" Oh)
                 True

||| ... a dropped close may omit it (Maybe on every other resolution) ...
droppedClose : Payload 3
droppedClose = PWorkClosed "spike" RDropped Nothing DDeferred Nothing False

||| ... and a review names its target as Fin n (only earlier rows nameable).
aReview : Payload 3
aReview = PReview 1 (MkReviewDetail Attest Technical "re-derived from scratch"
                       Nothing DistinctSession)

-- RED: a shipped close WITHOUT a witness does not elaborate --
-- work_shipped_requires_witness as a compile-time refusal.
failing "Mismatch between: Maybe"
  badShipped : Payload 3
  badShipped = PWorkClosed "fix-gate" RShipped Nothing DDeferred Nothing False

-- RED: a witnessed disposition WITHOUT a review ref does not elaborate --
-- work_review_witnessed_requires_ref, same idiom one column over.
failing "Mismatch between: Maybe"
  badWitnessed : Payload 3
  badWitnessed = PWorkClosed "fix-gate" RDropped Nothing DWitnessed Nothing False

-- RED: a review payload cannot name a same-or-later row -- Fin 3 has no
-- fourth element; validate_review's earlier-row refusal is unrepresentable
-- rather than trapped.
failing
  badRegards : Payload 3
  badRegards = PReview 3 (MkReviewDetail Attest Technical "x" Nothing SamePrincipal)
