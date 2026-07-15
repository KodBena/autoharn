||| RefUniverse.idr -- the payload/kind family as a UNIVERSE (description)
||| pattern: the kind vocabulary as first-class data, and the kind->shape table
||| as ONE function. This is the Idris rendering of what the substrate actually
||| is: s15+s22's ledger_kind_check (one closed kind list) plus the family of
||| kind-scoped shape CHECKs (work_slug_kind_shape, work_title_kind_shape,
||| work_resolution_kind_shape, work_review_ref_kind_shape,
||| work_strict_close_kind_shape, edge_type_kind_shape, ...) -- i.e. a kind
||| column plus a hand-maintained (kind, column, arity) manifest. PayloadTy IS
||| that manifest, single-homed. Contrast: the shipped Autoharn.idr GADT fuses
||| vocabulary and shapes into one closed type, so "which kinds exist" is not
||| a value any function can quantify over.
|||
||| STATUS (2026-07-15, later): design/Autoharn.idr's 2026-07-15 refresh
||| considered adopting this universe pattern and kept the fused GADT instead,
||| on readability grounds for a non-Idris-fluent reader (see Autoharn.idr's
||| own "UNIVERSE DECISION" header note, which cites this file by name as the
||| checked equivalent rendering). Kept here, unmodified, as that consultation's
||| own checked artifact -- revisit if the kind vocabulary starts growing fast.
module RefUniverse

import Data.Fin
import Data.So

%default total

Slug : Type
Slug = String

data Resolution = RShipped | RSuperseded | RDropped | RDeferred
data ReviewDisposition = DWitnessed | DDeferred
data EdgeType = BlocksClose | Informs
data ReviewVerdict = Attest | AttestWithReservations | Refuse

record NonEmptyText where
  constructor MkNonEmptyText
  text : String
  0 ok : So (text /= "")

Gated : Bool -> Type -> Type
Gated True  a = a
Gated False a = Maybe a

isShipped : Resolution -> Bool
isShipped RShipped = True
isShipped _        = False

isWitnessed : ReviewDisposition -> Bool
isWitnessed DWitnessed = True
isWitnessed DDeferred  = False

-- ===========================================================================
-- U1  THE KIND VOCABULARY AS DATA -- exactly ledger_kind_check's closed list,
--     one constructor per CHECK member, first-class (functions can case on
--     it, enumerate it, and carry it in violation rows the way the SQL does).
-- ===========================================================================
data Kind
  = KAssumption | KDecision | KQuestion | KVerification
  | KFinding | KSnag | KRevision | KNote
  | KReview
  | KWorkOpened | KWorkClaimed | KWorkDepends | KWorkClosed

||| A data-level manifest fact the GADT could only express by payload
||| pattern-matching (the shipped model's isWorkPayload, 5 clauses of shapes):
isWorkKind : Kind -> Bool
isWorkKind KWorkOpened  = True
isWorkKind KWorkClaimed = True
isWorkKind KWorkDepends = True
isWorkKind KWorkClosed  = True
isWorkKind _            = False

-- ===========================================================================
-- U2  THE SHAPE MANIFEST AS ONE FUNCTION. Each clause is one row of the
--     (kind -> licensed columns) table the SQL spells as N separate two-way
--     CHECK constraints. Adding a kind = one Kind constructor + one clause
--     here -- the additive authoring shape the lineage's ALTER TABLE deltas
--     actually have (closer than a GADT constructor rewrite, though still a
--     closed function: a delta edits this file, it does not append to it --
--     stated, not oversold).
-- ===========================================================================

record ReviewShape (n : Nat) where
  constructor MkReviewShape
  regards : Fin n
  verdict : ReviewVerdict
  basis   : String
  -- (independence/antecedent/grade elided here; RefKernel.idr R2 owns the
  --  grade-stage refinement -- one probe per claim.)

record OpenShape where
  constructor MkOpenShape
  slug      : Slug
  title     : String
  parent    : Maybe Slug
  composite : Bool

record DependsShape where
  constructor MkDependsShape
  slug       : Slug
  antecedent : Slug
  edge       : EdgeType

record CloseShape where
  constructor MkCloseShape
  slug    : Slug
  res     : Resolution
  witness : Gated (isShipped res) NonEmptyText        -- s22 shipped=>witness
  disp    : ReviewDisposition
  ref     : Gated (isWitnessed disp) NonEmptyText     -- s29 witnessed=>ref
  strict  : Bool

||| THE MANIFEST: one home for every kind-scoped shape fact.
PayloadTy : Kind -> Nat -> Type
PayloadTy KAssumption   n = ()
PayloadTy KDecision     n = ()
PayloadTy KQuestion     n = ()
PayloadTy KVerification n = ()
PayloadTy KFinding      n = ()
PayloadTy KSnag         n = ()
PayloadTy KRevision     n = ()
PayloadTy KNote         n = ()
PayloadTy KReview       n = ReviewShape n
PayloadTy KWorkOpened   n = OpenShape
PayloadTy KWorkClaimed  n = Slug
PayloadTy KWorkDepends  n = DependsShape
PayloadTy KWorkClosed   n = CloseShape

||| A ledger row: the kind column plus its licensed payload -- the dependent
||| record is the typed rendering of "one wide nullable table + shape CHECKs".
record Row (n : Nat) where
  constructor MkRow
  kind    : Kind
  payload : PayloadTy kind n

||| One home for "which kinds carry a slug" (the SQL's work_slug_kind_shape
||| two-way CHECK, as a total manifest read every consumer derives from).
slugOf : (k : Kind) -> PayloadTy k n -> Maybe Slug
slugOf KWorkOpened  p = Just p.slug
slugOf KWorkClaimed p = Just p
slugOf KWorkDepends p = Just p.slug
slugOf KWorkClosed  p = Just p.slug
slugOf _            _ = Nothing

-- ===========================================================================
-- U3  POLARITY WITNESSES.
-- ===========================================================================

-- GREEN: a shipped close carries its witness; a review row constructs.
uShipped : Row 3
uShipped = MkRow KWorkClosed
             (MkCloseShape "fix-gate" RShipped
                (MkNonEmptyText "seen-red/run.txt" Oh)
                DWitnessed (MkNonEmptyText "row 42" Oh) True)

uReview : Row 3
uReview = MkRow KReview (MkReviewShape 1 Attest "re-derived")

-- GREEN: the manifest read agrees with the shape (compile-time evaluation).
u3a : slugOf KWorkClaimed {n = 3} "spike" = Just "spike"
u3a = Refl
u3b : isWorkKind KReview = False
u3b = Refl

-- RED: shipped-without-witness refused (the Gated arm demands NonEmptyText).
failing "Mismatch between: Maybe"
  uBad : Row 3
  uBad = MkRow KWorkClosed
           (MkCloseShape "x" RShipped Nothing DDeferred Nothing False)

-- RED: a prose kind cannot smuggle a work payload -- PayloadTy KNote n = (),
-- so the licensed-shape correlation is the record's own typing.
failing
  uSmuggle : Row 3
  uSmuggle = MkRow KNote (MkOpenShape "a" "t" Nothing False)
