# INTERFACE — how the typed spine extends (2026-07-02)

Companion to `DESIGN.md` (the functions and assignments). This document is the
interface design proper: every extension the measurements demand, named as a typed
contract against the artifacts that exist today. Nothing here is prose-only; each
section ends in a type, a field, or a Protocol member.

**The spine as it stands** (exact, from the code):

- `extract.FactBundle` (TypedDict): `sents / entities / temporal / triples`, with
  `TripleRecord = {sent, subj, pred, obj, subj_key, obj_key, negated}` and the two
  `NotRequired` degradation markers `coref_refused` / `parse_refused`. All fields
  `str`/`int`/`bool`; JSON bit-exact.
- `contra_detect.Claim` (frozen dataclass): `subj_key, pred, obj_key, negated,
  subj_surface, obj_surface, sent_i, sent_text, number: float | None`. Produced only
  by `claims_from_bundle(bundle)`.
- `contra_detect.ClaimEnrichment` (frozen): `typed_subj_key: str | None`,
  `number_in_quantity: bool | None` — the GLiNER lane, aligned index-for-index to the
  claim list, consumed by `find_contradictions(..., enrichment=, typed_subject_keying=,
  quantity_gate=)`.
- `contra_detect.Finding` (frozen): `rule, subj_key, pred, claim_a, claim_b, span_a,
  span_b, grounding, extra` — **no score field exists**; `as_row()` is the wire to
  `contra.finding`.
- `logic_backend.LogicFinding` (frozen): `rule, subj_key, pred, text_a, text_b,
  value: str | None, backend, extra`; `Signature = (rule, subj_key, pred,
  sorted(text_a, text_b))`.
- `logic_backend.LogicBackend` (runtime-checkable Protocol): `name: str`,
  `rules: frozenset[str]`, `analyze(claims) -> list[LogicFinding]`.
  `cross_engine_differential(a, b, claims, rules)` — set-equality over shared rules.
- `transcript_prose.Provenance` (attrs frozen): `file, line_index, role, block_type,
  block_index` — the PROSE Port's per-unit role provenance, already produced at ingress.

**The extension law (binds every section below).** Every new field is optional with a
`None` default, and `None` means *exactly today's behavior*, pinned by
default-unchanged tests — the idiom the GLiNER seam established and the trial series
proved out (the control arm reproduced bit-identical through the new code path). This
is not conservatism for its own sake: it is what makes every lever **measurable as an
arm against a reproduced control** through the existing trial machinery, which is the
only way any of this earns its way into the hook. New interchange types follow
`contra_detect`'s frozen-`dataclass` idiom (they live in that module family and must
stay importable without the attrs/wire dependencies); ingress/wire types follow
`wire_types`' attrs idiom. All new code joins the `mypy --strict` surface.

---

## 1. Where extensions attach — one aligned-context lane, not N parallel kwargs

`find_contradictions` already takes one aligned annotation list (`ClaimEnrichment`).
Adding mood, role, and turn as further parallel kwargs would accrete a god-signature
(ADR-0012 P3 at the call boundary). The extension point is therefore **one new aligned
context record**, sibling to the enrichment lane:

```python
@dataclass(frozen=True)
class ClaimContext:
    """Ingress-derived, engine-agnostic context for one Claim (aligned index-for-index).

    Every field optional; None = the field is unknown = today's behavior. Produced at
    the PROSE-Port/extraction boundary, never inside an engine.
    """
    provenance: ClaimProvenance | None = None   # §3 — who said it, where, in what order
    mood: Mood | None = None                    # §2 — speech-act type
    hedge: Hedge | None = None                  # §2 — surface-form commitment marker
    closure_witness: ClosureWitness | None = None  # §2 — present only on witnessed closures
    quantity: Quantity | None = None            # §4 — dimensioned refinement of Claim.number
    standard_index: str | None = None           # §4 — recovered standard for gradable preds
```

`ClaimEnrichment` (the GLiNER lane) stays as-is — it is produced by a different
subsystem on a different failure envelope (a GLiNER outage must not degrade mood
typing). Engines receive `analyze(claims)` unchanged; backends that consume context
take it as constructor/callsite state exactly as `AspBackend` takes
`functional_preds` today — **the `LogicBackend` Protocol does not change.** Where a
rule needs context (the mood guard, the turn order), the driver passes the aligned
lists to the backend's constructor or to `find_contradictions`' keyword surface; a
backend that ignores context remains a valid backend and the differential gate still
runs on the shared-rule intersection. This is the polymorphic seam preserved by
construction, not by promise.

## 2. Mood and hedge — closed vocabularies, not scores (F2)

```python
class Mood(Enum):
    ASSERTION = "assertion"          # declarative claim about the world
    ACTION_REPORT = "action_report"  # "I removed the files" — eventive, verifiable per se
    INTERROGATIVE = "interrogative"  # questions; never enter assertion universes
    MENTION = "mention"              # quoted/cited material — use-vs-mention's mention side
    CLOSURE_CLAIM = "closure_claim"  # "Cleaned / resolved / done" — a claim of closure

class Hedge(Enum):
    NONE = "none"
    HEDGED = "hedged"        # "probably", "I think", "should be"
    EMPHATIC = "emphatic"    # "absolutely", "definitely", "I'm sure"
```

- **Why enums and not a confidence float.** The no-scores rule is load-bearing design
  (honesty = rule-id + grounding; `instances.py` declares no `Field.number`, so a
  fabricated confidence is unrepresentable at the adjudication boundary). `Hedge` does
  not breach it: it is a **surface-form category** — a classification of what the text
  says, groundable by quoting the hedge token — not a degree of belief the system
  invents. The doxastic signal (DESIGN F1) is a *pattern over these categories in
  supersession order*, reported with the quoted markers as grounding. If a future
  contributor reaches for `hedge_strength: float`, that is the exact move this
  paragraph exists to refuse.
- **The closure discrimination as a type.** `ClosureWitness` is ADR-0000's closure
  statement made a record:

```python
@dataclass(frozen=True)
class ClosureWitness:
    invariant: str            # the class-general invariant claimed closed
    universe: str             # the enumerated quantification universe
    witness: str              # the test/gate/measurement that would show it false
```

  A `CLOSURE_CLAIM` claim with `closure_witness=None` is *exactly* the
  "Cleaned [moving on]" shape: a closure claim without its witness. The engine rule is
  then trivial and mechanical — an unwitnessed closure claim can ground nothing beyond
  a defeasible closure inference, and the defeasible inference is retractable by the
  same class recurring (F1's machinery). No NLP heroics are required for v1: the
  witness fields are populated only where a workflow instrument already carries them
  as schema (the ADR-0000 amendment's own enforcement path); prose-extracted witnesses
  are not claimed.
- **Rule guards.** Contradiction universes admit `{ASSERTION, ACTION_REPORT,
  CLOSURE_CLAIM}`; `INTERROGATIVE` and `MENTION` claims are stored (detection ≠
  presentation, per the L1 amendment) but join no pair. `None` mood = admitted
  (today's behavior), so an unclassified corpus reproduces the control arm.

## 3. Provenance, order, and role — the stratification substrate (F1, F5)

`transcript_prose.Provenance` exists at the prose-unit level; claims need it carried
through extraction plus the two fields the engines consume (order and role):

```python
class Role(Enum):
    ASSISTANT = "assistant"
    USER = "user"
    HARNESS = "harness"      # harness-injected content (system-reminders, hook output)
    QUOTED = "quoted"        # material quoted from elsewhere, either role

@dataclass(frozen=True)
class ClaimProvenance:
    session_id: str
    line_index: int          # JSONL line in the transcript (transcript stays authoritative)
    unit_index: int          # prose unit within the line
    turn_index: int          # monotone per-session order — THE temporal index (see below)
    role: Role
```

- **Temporal ordering, scoped honestly.** `turn_index` is a **total order per
  session**, derived from transcript position. That is the *entire* temporal claim:
  R-SUP consumes "B after A", nothing else. Wall-clock time, cross-session ordering,
  and interval semantics are not claimed and not encoded; if a function ever needs
  them, that is a vocabulary revision (ADR-0008), not a reinterpretation of this field.
- **Role at ingress, not post-hoc.** `Role` is decoded from the PROSE Port's
  `Provenance.role` + block type at the boundary (translate-and-validate, ADR-0012
  P2); `HARNESS` and `QUOTED` are separated *before* the user stratum exists, which is
  what makes that stratum honest (dossier §3).
- **The universe type.** Stratification is enforced at construction, not by
  discipline:

```python
class UniverseKind(Enum):
    ASSISTANT_SELF = "assistant_self"
    USER_INSTRUCTION = "user_instruction"
    CROSS_ROLE = "cross_role"

@dataclass(frozen=True)
class ClaimUniverse:
    kind: UniverseKind
    claims: tuple[Claim, ...]
    contexts: tuple[ClaimContext, ...]   # same length, aligned — validated

    # smart constructor `ClaimUniverse.build(kind, claims, contexts)` REFUSES:
    #  - length mismatch;
    #  - a role outside the kind's admitted set (ASSISTANT_SELF admits ASSISTANT only;
    #    USER_INSTRUCTION admits USER only; CROSS_ROLE admits both, never HARNESS/QUOTED);
    #  - CROSS_ROLE construction while mood is None on any member (the ruled gate:
    #    cross-role is not honest before the mood work).
```

An illegal universe is unconstructable (ADR-0000 Specimen 1's shape at the analysis
boundary); the engines never re-check roles on the hot path.

## 4. Quantities and standards — the dimensioned lane (F3, F4)

```python
class Dimension(Enum):
    BYTES = "bytes"; SECONDS = "seconds"; PERCENT = "percent"
    COUNT = "count"; DIMENSIONLESS = "dimensionless"

@dataclass(frozen=True)
class Quantity:
    value: float             # as written ("2.9")
    unit: str                # surface unit token ("GB")
    dimension: Dimension
    base_value: float        # value coerced to the dimension's base unit (2.9 * 2**30)
```

- `parse_quantity(obj_surface, sent_text) -> Quantity | None` extends the
  `parse_number` posture: a closed unit table per dimension, `None` on anything it
  cannot type — never a guess, and non-finite values refused as `parse_number` now
  does. `Claim.number` is untouched (R-NUM's input, control-arm law); `base_value` is
  **derived by one function from `value` + the unit table** — one home, tested, so
  the two numeric fields cannot drift (ADR-0012 P1; the derivation is the SSOT, the
  field a cache of it).
- **`R-QTY` join contract.** Pairs join on `(dimension, regime_key)` where
  `regime_key` is the typed subject (`ClaimEnrichment.typed_subj_key`) when present,
  else the quantity-mention head; incompatibility is `|a.base − b.base| >
  τ[dim] · max(...)` with `τ` a named per-dimension constant table (each entry
  denominated in its own dimension and justified in a comment — the proxy-bound
  amendment; no bare round literals). The join key is experiment E-2's subject
  (DESIGN §3-F3 states the uncertainty); the *contract shape* above is stable either
  way.
- **Standard index (F4).** `ClaimContext.standard_index: str | None` — recovered only
  from explicit markers in v1. `FdeZ3Backend`'s atom-grouping key becomes
  `(subj_key, pred if std is None else f"{pred}@{std}", obj_key)`; a dissolved glut
  produces no finding, an unresolved glut routes to calibration (KB-CODESIGN §4)
  instead of injection. The `FdeSemantics` knobs are untouched; the change is keying,
  upstream of every solve, so the mutation suite over the semantics stays valid.

## 5. Identity — handles and finding identity (the interface/KB joint)

This is where the interface and the KB constrain each other (the co-design's hinge;
the KB side is KB-CODESIGN §2):

```python
ClaimHandle = NewType("ClaimHandle", str)   # 12 hex chars

def claim_handle(scrubbed_text: str, prov: ClaimProvenance) -> ClaimHandle:
    """sha256 over (scrubbed sent_text, subj_key, pred, obj_key, negated,
    session_id, line_index, unit_index) — first 12 hex chars."""

@dataclass(frozen=True)
class FindingIdentity:
    rule: str
    handle_a: ClaimHandle    # invariant: handle_a < handle_b (sorted — unordered pair)
    handle_b: ClaimHandle
```

- **One identity system.** The ASP engine's claim id (index into the claim list), the
  KB row, the finding's grounding, and any injected citation all resolve to the same
  handle. `FindingIdentity` *is* the HOOK-DESIGN amendment's ruling made a type:
  finding identity = its claim-pair identities, so a persisting contradiction is one
  stored finding re-observed (a counter bump, KB-CODESIGN §3), never re-injected per
  turn.
- **Handle length.** 12 hex chars, not the dossier's floated 8. The honest arithmetic
  (birthday bound p ≈ n²/2^(b+1)): at 32 bits (8 hex), 10⁵ claims already gives
  p ≈ 0.7 and 10⁶ claims makes collisions near-certain (~10² expected) — a silent
  identity merge, the worst failure for an audit key. At 48 bits (12 hex), 10⁶ claims
  gives p ≈ 2×10⁻³ — rare, not impossible. The load-bearing guarantee is therefore
  NOT the width: it is the KB's write-time uniqueness check, under which a collision
  is a **loud refusal, never a merge** (ADR-0002; KB-CODESIGN §2). The width only
  sets how often that refusal is ever seen; 12 hex keeps it out of normal operation
  at this project's horizon while staying short enough for handle+gloss citation.
- **Handles are citations, not content** (DESIGN §4): anything injected into a session
  is handle **+ gloss**; a bare handle is never given to a model to "dereference."

## 6. New rule-ids and the seam, unchanged

The rule vocabulary grows: `R-SUP` (supersession, F1), `R-SUP-ESC` (hedge escalation
across a supersedes-chain, F1), `R-QTY` (dimensioned incompatibility, F3), `R-WHY`
(orphaned WHY, F6), `R-ORD` (precedence violation, F7). Each is:

- a member of some backend's `rules: frozenset[str]` — the Protocol member that makes
  the differential honest on intersections is doing exactly its designed job;
- covered by a Python oracle counterpart (the oracle stays the hub and the
  differential's fixed point, as `contra_detect` is today);
- emitted as a `LogicFinding` whose `value` slot carries the paraconsistent value
  where one exists (`both` for gluts) and whose `extra` carries the rule's typed
  grounding payload (e.g. `R-SUP`: the two handles + turn indices; `R-QTY`: both
  quantities, base values, τ) — `extra` is already the sanctioned open slot; the
  *required* grounding fields per rule are stated in each rule's test, which is the
  mechanical place a schema-less dict is kept honest.

`Finding.as_row()` and the `contra.finding` UNIQUE key are unchanged for the existing
rules; new rules land in the KB's finding table (KB-CODESIGN §3), which carries the
handle-pair identity natively. `contra.finding` remains the adjudication widget's wire
and receives everything routed to adjudication.

## 7. Budget and failure envelope (the hook's demands, inherited)

The interface is called from a deadline-carried, budgeted client (HOOK-DESIGN §3);
therefore, as contract, not aspiration:

- Every engine call site takes an explicit `deadline` and degrades to a **typed
  no-op** (empty findings + a loud log line), never a hang: the `contra_asp`
  subprocess timeout becomes a parameter derived from the caller's budget — replacing
  the bare `timeout=120` literal (the inventory's cancer-F note) with a value
  denominated in the caller's real budget.
- `FdeZ3Backend`'s per-pair solver construction and the ASP process-spawn are the two
  known cost axes (inventory); both are *inside* the budget envelope, and the
  standard-index re-keying (F4) runs before any solve, so dissolved gluts cost zero
  solver time.
- The `fde_z3.py:111` bare `assert` on the non-explosion invariant is elided under
  `python -O`; on this seam's next touch it becomes a `raise` (ADR-0002 hierarchy —
  a load-bearing invariant does not vanish with an interpreter flag). Noted here so
  the extension work carries it; it is a one-line fix inside increment 2's file set.
