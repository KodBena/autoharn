||| RefKernel.idr -- REFINEMENT PROBE for design/Autoharn.idr (fresh-context review,
||| 2026-07-15). Not a replacement: each section is one refinement CLAIM from the
||| review, written so the claim is machine-checked rather than paper-only.
||| Substrate ground truth for every section: kernel/lineage/s22/s29/s30/s31.sql +
||| engine/lp/ledger_tnow.lp, work_items.lp. Common Entry columns not load-bearing
||| for a claim (session/statement/amends/answers/enacts) are elided and said so.
|||
||| STATUS (2026-07-15, later): all nine refinements (R1-R9) folded into
||| design/Autoharn.idr, which now supersedes this file as the checked model.
||| This file is kept, unmodified, as the consultation's own checked artifact --
||| historical record of the refinement claims as first proved, one probe per
||| claim, referenced from Autoharn.idr's provenance header.
module RefKernel

import Data.Fin
import Data.List
import Data.List.Quantifiers
import Data.Nat
import Data.So
import Data.Maybe

%default total

-- ===========================================================================
-- R0  Shared vocabulary (unchanged from Autoharn.idr where not under review).
-- ===========================================================================

PrincipalId : Type
PrincipalId = Nat

Slug : Type
Slug = String

data ReviewVerdict = Attest | AttestWithReservations | Refuse

isAttest : ReviewVerdict -> Bool
isAttest Attest = True
isAttest _      = False

data Independence = Technical | Managerial | Financial

data DischargeGrade = SamePrincipal | SameSession | DistinctSession | DistinctDeployment

data Resolution = RShipped | RSuperseded | RDropped | RDeferred

data ReviewDisposition = DWitnessed | DDeferred

data EdgeType = BlocksClose | Informs

data ProseKind = KAssumption | KDecision | KQuestion | KVerification
               | KFinding | KSnag | KRevision | KNote

record NonEmptyText where
  constructor MkNonEmptyText
  text : String
  0 ok : So (text /= "")

data Stamp : Type where
  MkStamp : (session : String) -> (agent : String) -> (hmacHex : String) -> Stamp

-- ===========================================================================
-- R1  THE "MANDATORY-IFF" IDIOM NAMED ONCE (refines witnessTy/reviewRefTy).
--     Substrate fact: s29's work_review_witnessed_requires_ref comment says it
--     "mirrors s22's work_shipped_requires_witness pattern exactly, one column
--     over" -- the idiom has two hand homes in SQL and two in the model.
--     One combinator is the P1 move; each use names only its gate condition.
-- ===========================================================================

||| Gated True  a = the field is mandatory (the CHECK's required arm).
||| Gated False a = the field is optional  (legal, may be absent).
Gated : Bool -> Type -> Type
Gated True  a = a
Gated False a = Maybe a

isShipped : Resolution -> Bool
isShipped RShipped = True
isShipped _        = False

isWitnessed : ReviewDisposition -> Bool
isWitnessed DWitnessed = True
isWitnessed DDeferred  = False

witnessTy : Resolution -> Type
witnessTy r = Gated (isShipped r) NonEmptyText

reviewRefTy : ReviewDisposition -> Type
reviewRefTy d = Gated (isWitnessed d) NonEmptyText

-- ===========================================================================
-- R2  TRIGGER-COMPUTED FIELDS AS A STAGE INDEX (refines the grade-is-computed
--     half-rendering the transcription consult names as "convention in a
--     one-file sketch"). Substrate facts unified by ONE index:
--       * s29: review_detail.discharge_grade is COMPUTED by
--         validate_independence(), never writer-asserted (NEW.discharge_grade
--         is overwritten unconditionally).
--       * s30: work_depends_on.edge_type is DEFAULTED by validate_work_item()
--         (NULL -> 'informs') -- writer may supply, absence is filled in.
--     Draft = what the writer can say; Recorded = what the ledger holds.
--     "A writer cannot supply a grade" is now a TYPE fact (GradeF Draft = ()),
--     not a module-abstraction promise.
-- ===========================================================================

data Stage = Draft | Recorded

||| discharge_grade: absent from the writer surface, present in the record.
GradeF : Stage -> Type
GradeF Draft    = ()
GradeF Recorded = DischargeGrade

||| edge_type: optional at the writer surface (trigger defaults), total in the
||| record. (Steady-state/birth-chain world: the s30 pre-history NULL rows do
||| not exist -- same fidelity choice as the shipped model, kept and named.)
EdgeF : Stage -> Type
EdgeF Draft    = Maybe EdgeType
EdgeF Recorded = EdgeType

record ReviewDetail (st : Stage) (n : Nat) where
  constructor MkReviewDetail
  verdict      : ReviewVerdict
  independence : Independence
  basis        : String
  antecedent   : Maybe (Fin n)
  grade        : GradeF st

data Payload : (st : Stage) -> (n : Nat) -> Type where
  ||| R3: eight nullary prose constructors collapse to one carrying ProseKind.
  PProse      : ProseKind -> Payload st n
  PReview     : (regards : Fin n) -> ReviewDetail st n -> Payload st n
  PWorkOpened : (slug : Slug) -> (title : String)
             -> (parent : Maybe Slug) -> (composite : Bool) -> Payload st n
  PWorkClaimed : (slug : Slug) -> Payload st n
  PWorkDepends : (slug : Slug) -> (antecedent : Slug) -> EdgeF st -> Payload st n
  PWorkClosed : (slug : Slug)
             -> (res : Resolution) -> witnessTy res
             -> (disp : ReviewDisposition) -> reviewRefTy disp
             -> (strict : Bool) -> Payload st n

record Entry (st : Stage) (n : Nat) where
  constructor MkEntry
  actor      : PrincipalId
  stamp      : Maybe Stamp
  supersedes : Maybe (Fin n)
  payload    : Payload st n

||| The ledger holds RECORDED rows only; a Draft never lands unprocessed.
data Ledger : Nat -> Type where
  Lin  : Ledger 0
  (:<) : Ledger n -> Entry Recorded n -> Ledger (S n)

-- ===========================================================================
-- R4  ONE ROW-ADDRESSING HOME (de-stubs deferredUndischargedIn). The shipped
--     model's §4 oracle stub says the real lookup "needs absolute row ids
--     threaded through the fold, elided here". Observation: the Ledger index
--     ALREADY carries every absolute id -- prefix position IS the id (row 0 is
--     the oldest, globally and in every prefix), so finToNat of a Fin n index
--     or of a stored Fin m back-reference are the same currency. One total
--     lookup replaces the stub; no structural change to the model was needed.
-- ===========================================================================

||| Reduction-transparent strengthen (base's is `export`, so it cannot reduce
||| in Refl proofs outside Data.Fin -- a toolchain fact, noted in the report).
public export
strong : {n : Nat} -> Fin (S n) -> Maybe (Fin n)
strong {n = S _} FZ     = Just FZ
strong {n = S _} (FS p) = map FS (strong p)
strong _                = Nothing

||| The entry at absolute row id t (prefix size existentially packed).
entryAt : {n : Nat} -> Ledger n -> Fin n -> (m ** Entry Recorded m)
entryAt Lin      t = absurd t
entryAt (l :< e) t = case strong t of
                       Nothing => (_ ** e)
                       Just t' => entryAt l t'

||| First-order any (Prelude's Foldable `any` does not reduce under Refl here).
anyB : (a -> Bool) -> List a -> Bool
anyB f []        = False
anyB f (x :: xs) = f x || anyB f xs

allIds : (n : Nat) -> List (Fin n)
allIds Z     = []
allIds (S k) = FZ :: map FS (allIds k)

-- ===========================================================================
-- R5  Fin-TYPED IN-FORCE PROJECTION (refines supersededIn : ... -> Nat -> Bool).
--     A question about a row that does not exist is now unaskable; the
--     finToNat/Nat-equality comparison survives only INSIDE the fold, where
--     the stored edge (Fin m) meets the queried id (Fin n).
--     Monotonicity (reinstatement-freedom) is untouched: edge existence only.
-- ===========================================================================

supersededIn : {n : Nat} -> Ledger n -> Fin n -> Bool
supersededIn Lin      t = absurd t
supersededIn (l :< e) t =
     maybe False (\f => finToNat f == finToNat t) e.supersedes
  || (case strong t of
        Nothing => False
        Just t' => supersededIn l t')

inForce : {n : Nat} -> Ledger n -> Fin n -> Bool
inForce l t = not (supersededIn l t)

-- ===========================================================================
-- R5b  THE THEOREM SURVIVES THE Fin REFINEMENT. Autoharn.idr's one proof
--      (supersededStable, reinstatement-freedom) restated over Fin indices:
--      extension re-addresses old rows via weaken, and the monotonicity
--      argument goes through with one strengthen/weaken cancellation lemma.
-- ===========================================================================

strongWeaken : {n : Nat} -> (t : Fin n) -> strong (weaken t) = Just t
strongWeaken FZ     = Refl
strongWeaken (FS p) = rewrite strongWeaken p in Refl

orRightTrue : (b : Bool) -> (b || True) = True
orRightTrue True  = Refl
orRightTrue False = Refl

supersededStable : {n : Nat} -> (l : Ledger n) -> (e : Entry Recorded n)
                -> (t : Fin n)
                -> supersededIn l t = True
                -> supersededIn (l :< e) (weaken t) = True
supersededStable l e t prf =
  rewrite strongWeaken t in
  rewrite prf in
  orRightTrue (maybe False (\f => finToNat f == finToNat (weaken t)) e.supersedes)

-- ===========================================================================
-- R6  PROOF-CARRYING PROJECTION (refines Projection's "liveIds ... ascending,
--     in-force" COMMENT into a carried fact). A Projection over l can no
--     longer contain an id that is out of range (Fin n) or superseded (the
--     erased All). The reader-typing judgment is unchanged; its data is honest.
-- ===========================================================================

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

-- ===========================================================================
-- R7  s31 ALIGNMENT (a FIDELITY fix, not polish). The shipped model transcribes
--     the s30-era read semantics: hasCloseIn reads RAW closes ("the named blind
--     spot of composite-spec §3b"). s31 (RATIFIED 2026-07-15, in lineage) has
--     since re-issued work_item_strict_blockers' edges+closes CTEs to read
--     ledger_current. The blind spot is no longer the substrate's behavior, so
--     preserving it now makes the model LIE one delta stale. Below: both legs
--     of the calculus read in force, matching s31 Elements 1/2. The write
--     boundary's raw reads (everOpened; the would_cycle walk) stay RAW -- that
--     is s31's own closed allowlist (LWriteBoundary/LDuplicateOpen), and
--     uniformizing them away would be the dishonest polish.
-- ===========================================================================

||| Raw-history read: slug ever opened (fork 2, slug burned -- allowlisted).
everOpened : Ledger n -> Slug -> Bool
everOpened Lin      _ = False
everOpened (l :< e) s = isOpen e.payload || everOpened l s
  where
    isOpen : Payload st m -> Bool
    isOpen (PWorkOpened s' _ _ _) = s == s'
    isOpen _                      = False

||| s31 Element 2: in-force close only (a retracted close no longer closes).
hasCloseCur : {n : Nat} -> Ledger n -> Slug -> Bool
hasCloseCur l s = anyB closesHere (allIds n)
  where
    closesHere : Fin n -> Bool
    closesHere t = inForce l t &&
      (case entryAt l t of
         (_ ** e) => case e.payload of
                       PWorkClosed s' _ _ _ _ _ => s == s'
                       _                        => False)

||| Raw-history contrast (the pre-s31 semantics, kept ONLY as a witness that
||| the two readings now provably differ -- see fixture R7a/R7b).
hasCloseRaw : Ledger n -> Slug -> Bool
hasCloseRaw Lin      _ = False
hasCloseRaw (l :< e) s = case e.payload of
                           PWorkClosed s' _ _ _ _ _ => s == s' || hasCloseRaw l s
                           _                        => hasCloseRaw l s

||| s31 Element 2: both edge arms read in force.
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

||| Reachable set with fuel (encoding noise, unchanged from the shipped model).
reach : (fuel : Nat) -> List (Slug, Slug) -> (frontier : List Slug)
     -> (seen : List Slug) -> List Slug
reach Z     _  _        seen = seen
reach (S k) es frontier seen =
  let next = [ c | (p, c) <- es, elem p frontier, not (elem c seen) ] in
  case next of
    [] => seen
    _  => reach k es next (seen ++ next)

||| The de-stubbed review leg: an in-force deferred close of s with NO
||| in-force distinct-actor attest regarding it (s29's review_unresolved CTE,
||| discharge subquery byte-kept by s31). CHECKED, not an oracle: the absolute
||| ids come from R4's entryAt, nothing was structurally missing.
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

||| ADR-0012 P1: still the ONE home of the obligation conjunction -- now with
||| both legs on the SAME (in-force) quantification domain, as s31 ratified.
strictBlockers : {n : Nat} -> Ledger n -> Slug -> List Blocker
strictBlockers l root =
  let members   = reach n (edgesCur l) [root] [root]
      notRoot   = filter (/= root) members
      notClosed = [ MkBlocker s "item is not yet closed"
                  | s <- notRoot, not (hasCloseCur l s) ]
      reviewUn  = [ MkBlocker s "review disposition deferred and undischarged"
                  | s <- members, deferredUndischarged l s ]
  in  notClosed ++ reviewUn

-- ===========================================================================
-- R8  RELATIONAL WRITE BOUNDARY (refines ValidAppend's So-of-Bool payload
--     shape tests into constructor-indexed relations, and carries the s29/s30
--     premises the shipped ValidAppend OMITS: its own §3 comment enumerates
--     the s30 blocks-close self/dangling/cycle refusals and the s29
--     strict-close refusals, but VOpen/VLater/VProse encode none of them.
--     The comment and the type disagree -- the type now says what the
--     validate_work_item() chain (s22..s31) actually refuses.
--     Raw-vs-derived domains kept per s31's allowlist: freshness/opened/cycle
--     premises quantify RAW; the strict-close premise quantifies the
--     projection (via strictBlockers). Both visible in one indexed family.
-- ===========================================================================

||| Raw blocks-close reachability, seeded at `from` (s30's
||| work_depends_on_would_cycle: a declared RAW walk even after s31).
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

||| s29 Element C at the root: strict close needs a witnessed disposition and
||| an empty blocker set; non-strict closes carry no premise.
strictPremise : {n : Nat} -> Ledger n -> Slug -> (strict : Bool)
             -> ReviewDisposition -> Bool
strictPremise l s False _          = True
strictPremise l s True  DDeferred  = False
strictPremise l s True  DWitnessed = null (strictBlockers l s)

Eq EdgeType where
  BlocksClose == BlocksClose = True
  Informs     == Informs     = True
  _           == _           = False

data ValidPayload : {n : Nat} -> Ledger n -> Payload Draft n -> Type where
  VProse  : ValidPayload l (PProse k)
  ||| regards earlier-row: already unrepresentable via Fin n (unchanged).
  VReview : ValidPayload l (PReview r d)
  VOpen   : (0 fresh : So (not (everOpened l s)))
         -> ValidPayload l (PWorkOpened s title parent comp)
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
  ||| fidelity choice) + Element C strict premises.
  VClose  : (0 opened   : So (everOpened l s))
         -> (0 strictOk : So (strictPremise l s strict disp))
         -> ValidPayload l (PWorkClosed s res w disp ref strict)

-- ===========================================================================
-- R9  THE RECORDING STEP: append = validate + compute-and-record (the trigger
--     as the ONLY Draft -> Recorded arrow). The s29 grade ladder is now a
--     CHECKED transcription of validate_independence()'s ELSIF chain, not an
--     opaque enum: fail-safe same-principal on any absent identity half.
-- ===========================================================================

stampPair : Maybe Stamp -> Maybe (String, String)
stampPair Nothing                    = Nothing
stampPair (Just (MkStamp s a _))     = Just (s, a)

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

append : {n : Nat} -> (l : Ledger n) -> (e : Entry Draft n)
      -> (0 ok : ValidPayload l e.payload) -> Ledger (S n)
append l e _ = l :< MkEntry e.actor e.stamp e.supersedes
                          (recordPayload l e.stamp e.payload)

-- ===========================================================================
-- R10  POLARITY WITNESSES. Green fixtures construct; red `failing` blocks are
--      refusals witnessed at elaboration; Refl fixtures are SEMANTIC witnesses
--      (the reader functions evaluated at compile time on a concrete world).
-- ===========================================================================

mkE : PrincipalId -> Maybe (Fin n) -> Payload Recorded n -> Entry Recorded n
mkE a sup p = MkEntry a Nothing sup p

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

-- R7a GREEN/Refl: raw and in-force readings AGREE while nothing is retracted.
r7a1 : hasCloseRaw RefKernel.worldA "a" = True
r7a1 = Refl
r7a2 : hasCloseCur RefKernel.worldA "a" = True
r7a2 = Refl

-- R7b GREEN/Refl: after retraction they PROVABLY DIVERGE -- the s31 semantics
-- (a retracted close re-opens the item) as a compile-time fact, and the exact
-- delta the shipped model's raw hasCloseIn can no longer represent faithfully.
r7b1 : hasCloseRaw RefKernel.worldC "a" = True
r7b1 = Refl
r7b2 : hasCloseCur RefKernel.worldC "a" = False
r7b2 = Refl

-- R4a GREEN/Refl: the de-stubbed review leg, both polarities of discharge.
r4a1 : deferredUndischarged RefKernel.worldA "a" = True   -- deferred, no attest yet
r4a1 = Refl
r4a2 : deferredUndischarged RefKernel.worldB "a" = False  -- distinct-actor attest lands
r4a2 = Refl
r4a3 : deferredUndischarged RefKernel.worldC "a" = False  -- close retracted: no obligation
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
r8a : ValidPayload RefKernel.worldA (PWorkDepends "a" "ghost" (Just Informs))
r8a = VDepLax Oh Oh

-- R8b RED: the SAME dangling antecedent as blocks-close is REFUSED (s30) --
-- antOpened demands So (everOpened l "ghost") = So False.
failing
  r8b : ValidPayload RefKernel.worldA (PWorkDepends "a" "ghost" (Just BlocksClose))
  r8b = VDepBC Oh Oh Oh Oh

-- R8c RED: a blocks-close self-edge is refused (s30).
failing
  r8c : ValidPayload RefKernel.worldA (PWorkDepends "a" "a" (Just BlocksClose))
  r8c = VDepBC Oh Oh Oh Oh

-- R8d RED: strict + deferred is a contradiction in terms (s29) -- the
-- strictPremise evaluates to False, So is uninhabited.
failing
  r8d : ValidPayload RefKernel.worldA
          (PWorkClosed "a" RDropped Nothing DDeferred Nothing True)
  r8d = VClose Oh Oh

-- R2a RED: a WRITER-SUPPLIED grade is now unrepresentable, not just
-- unconventional -- a Draft review's grade field has type ().
failing
  r2a : Payload Draft 3
  r2a = PReview 1 (MkReviewDetail Attest Technical "x" Nothing DistinctSession)

-- R1a RED (unchanged strength after the Gated collapse): a shipped close
-- without a witness still does not elaborate.
failing "Mismatch between: Maybe"
  r1a : Payload Recorded 3
  r1a = PWorkClosed "x" RShipped Nothing DDeferred Nothing False

-- R6a GREEN: the projection now CARRIES its soundness; a consumer may demand
-- the proof. (Erased, so zero runtime cost -- same as the SQL view costing
-- nothing beyond its WHERE clause.)
r6a : Projection RefKernel.worldC
r6a = project worldC
