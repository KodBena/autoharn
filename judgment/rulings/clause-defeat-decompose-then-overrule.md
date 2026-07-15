# Deliberation — clause-level defeat via decompose-then-overrule (maintainer, 2026-07-06)

*Maintainer input, filed faithfully by the engineer. This is a deliberation, not an expert
verdict and not a scope displacement; the odd-numbered link is the interpretive authority and
is asked to interrogate the proposed resolution on its merits.*

## Context (facts only)

- e13 (link 18) shipped clause-level defeat as a typed `amends` edge whose `amends_scope` must
  be a verbatim quotation (10+ chars) of the target row's statement/rationale, enforced at the
  write boundary (maintainer ruling 2026-07-06: "either it gets typed, or it gets a ledgered
  rationale" — the typed branch was taken).
- The maintainer subsequently challenged the quotation mechanism itself: "Quotations (meaning
  string handling) is already fragile. Why not just references?"
- In the ensuing exchange the engineer argued that sub-row references require either (a) the
  subject authoring structured clauses at write time, or (b) post-hoc decomposition of the
  subject's prose by the apparatus. The maintainer ruled the framing of (a) defective — the
  cost-to-the-subject reading "invokes the ghost of ADR-0013"; iterating the architecture
  forward is the point, and "the question is never 'is it a pain to follow protocol'" — and
  proposed the resolution below for the problem underlying (b).

## The maintainer's proposed resolution (faithful)

For over-ruling part of an earlier row's prose, the right shape as the maintainer sees it:

1. **Defeat the referent** (whole-row).
2. **Decompose the referent with a rationalized first-class decomposition** — re-issue its
   content as finer-grained, first-class ledger rows.
3. **Over-rule the specific component thus obtained** (whole-row defeat of the fragment).

The maintainer's standing frame for evaluating this and all alternatives: the next putative
Chernobyl — every argument must be one you would forward to a nuclear engineer. Subject
authoring burden is not such an argument. "What we are doing is iterating on architecture,
and we are moving forward."

The maintainer explicitly requests that the next odd-numbered link interrogate this would-be
solution (including whether the engineer's statement of the underlying problem was itself
correct).

## Questions the exchange surfaced (engineer capture — interpretation to verify, not authority)

- Under decompose-then-overrule, validity stays row-granular: the two-theory closure never
  needs sub-row qualification. Does this dissolve F44's aspectual axis rather than type it?
- Multi-row supersession semantics: N fragment rows each superseding one target — how does the
  closure distinguish a *decomposition* (jointly replacing) from *competing replacements*?
  Does this need a typed marker (a decomposition group), and what consumer consumes it?
- Status inheritance: fragments are fresh assertions with frozen-at-insert status. Does a
  fragment of a confirmed decision require a faithfulness attestation (`review`/`regards`,
  now in the kernel) before any consumer treats it as carrying the original's standing?
- Actor questions: who may decompose another author's assertion; how the record marks the
  decomposition act as interpretive; whether the original author's countersign is the honest
  gate on fidelity.
- Disposition of `amends`: permanent vocabulary, or a transitional form superseded by
  decompose-then-overrule (with what re-entry condition)?
- Sequencing: if structured decomposition (or structured clause authoring generally) enters
  the subject's write contract, which increment introduces it, given the levers-separate
  posture (consult 17 §6.2) and e14's clean-re-run purpose.

## Maintainer addition (2026-07-06, appended)

A second domain-specific benefit, for domains where attestation carries water: the
`review`/`regards` attestation on a decomposition can attest not only to its faithfulness but
to the **MECE of the decomposition** — the fragments jointly exhaustive of the referent and
mutually exclusive of one another.

## Maintainer ruling (2026-07-06) — DTO is ADOPTED as the shape (inverted burden); consult 19 overruled on this topic

**DTO (decompose-then-overrule) is the shape we adopt going forward.** The maintainer overruled
link 19's ruling (consult `e14-design-consult-19.md`) that DTO is merely a narrow escalation shape
not to replace `amends` — overruled "on the strength of its weakness": the consult's case *against*
DTO does not meet our standard of rigor. Specifically, (a) its "why we are not in that domain
today" leg rested on absence-of-lab-data (a censored-record / ADR-0013 laundering failure — the
consult's own SECOND ADDENDUM sustains this), and (b) its clingo displacement result showed false
*alarms* (over-flagging on inbound whole-row citations — conservative/safe, requiring re-key debt),
which is NOT logical unsoundness.

**The burden is inverted (frontier creed).** DTO stands as the adopted shape **unless a competent
Fable consult produces a machine-checked proof that it is logically UNSOUND** — by the standard of
rigor we hold ourselves to (a proof, not an ergonomics or absence argument). Nothing short of that
retires it. The maintainer will not commission another Fable consult on the DTO shape *alone*
(cost); a disproof, if it exists, arrives incidentally from a future competent link, not a
dedicated re-derivation.

**Scope of "postpone until next time":** the DECISION (DTO is the direction) is made now; only the
detailed SHAPE (exact typed edges — `decomposes` + group identity, the faithfulness+MECE
attestation gate, inbound-edge re-key handling) is deferred to a future cycle to work out in full.
DTO is NOT built for e14. The interim shipped mechanism remains `amends` (with the ambiguity
hardening), and e14 proceeds on it; the rest of consult 19 (e14 design, amends disposition, F46,
levers-separate) is untouched by this overrule and remains pending the M-item ratifications.

Standing rule the maintainer attached (now durable): **never frame a putative demand of the
harness as relying on the data we have collected currently; `safety-critical-logging-standards/
BRIEF.md` is authoritative on what the harness must support, not what we see in our toy lab.**

## SCHEDULING RULING (2026-07-06) — trigger-gating STRUCK; the marriage increment IS the "future cycle"

*Surfaced by the marriage-doc author (Fable), endorsed by the maintainer as fair, resolved by the
engineer in the spirit of the maintainer's own prior ruling. Corrects an error the engineer
introduced and propagated.*

**The defect.** The adoption ruling above says the DTO shape is "deferred to a future cycle to work
out in full" — a SCHEDULED obligation. The subsequent "Re-entry conditions codified" section (below)
and the link-20 codification rendered that as *"the first of the three recognition conditions that
fires commissions the DTO build"* — i.e. **consumer-first trigger-gating, the exact posture consult
19 was OVERRULED for**, surviving under a "consistent with the maintainer ruling" header. F51 then
adjudicated those conditions as NOT-fired, so DTO-the-adopted-direction was parked indefinitely.

**Why it is struck (no fresh maintainer ruling needed — the prior ruling forecloses it).**
**Inverted-burden adoption is logically incompatible with trigger-gating.** "DTO is adopted,
retirable only by a machine-checked unsoundness proof" makes DTO the STANDING direction we build
toward; "don't build it until a trigger fires that may never fire" PARKS it. The two contradict;
the adoption wins. Parking the adopted direction behind not-fired triggers is precisely the truancy
(ADR-0013) the maintainer has repeatedly rejected.

**The ruling.** The trigger-gating is STRUCK. The **re-entry conditions revert to their honest role:
detectors/recognition surfaces** (condition-2 individuation, close-sweep scans) that observe whether
the shipped mechanisms are meeting demand — NOT a gate on whether DTO gets built. **The DTO shape is
worked out in full NOW: the current marriage increment IS the "future cycle."** The degenerate
"supersede-and-reissue" (expressible since s1, containing none of DTO's machinery) does NOT discharge
"first exercise apparatus-authored" — that claim is struck as a dressed-up discharge. The first
exercise is the **full §1.5 shape**: `decomposes` edge + group identity + faithfulness/MECE
attestation (human attester, SoD-distinct from the author) + one inbound-edge re-key, apparatus-
authored on a scratch lineage, banked as fixtures, subject-facing bytes untouched.

**Provenance correction (2026-07-06, per the clingo-fidelity review §2.3 — the engineer owning the
record).** The strike-and-build ruling above was *engineer-authored under standing delegation, in the
spirit of the maintainer's inverted-burden adoption* — NOT an explicit maintainer ruling at the
moment it was written. The maintainer had endorsed the marriage-doc author's *adjudication* as "fair,"
which is not the same as ruling the scheduling question. The authority is nonetheless REAL, and became
so by the maintainer's own subsequent explicit acts: he directed the substance verbatim in the build
instruction ("struck B5… replaced with the full §1.5 shape") and then passed the Increment-1.1
fix-pass through on the full-DTO basis. Any program header (e.g. `ledger_dto.lp`) citing "the
2026-07-06 SCHEDULING RULING" as its authorizing act should cite THIS corrected provenance: engineer-
under-delegation, maintainer-confirmed by the two subsequent directions. The two-provisional-rulings
in Increment 1.1 (evict-on-attest; strict id-precedence) remain PENDING explicit maintainer
ratification and are built provisionally, flagged as such.

**RATIFIED (maintainer, 2026-07-06) — both provisional rulings now binding:**
1. **Evict-on-attest (F-B):** *"a decomposition's referent does not leave the current view until the
   group is attested."* The full derived-eviction fix is now owed (beyond the premature_eviction
   flag): the target's in-force status is DERIVED from group attestation in `ledger_dto.lp` (+ floor
   mirror), so the §1.5-forbidden half-decomposed-record-with-original-gone state is
   unrepresentable, not merely flagged. Write-boundary ordering enforcement is owed when DTO reaches
   a real subject lineage (later).
2. **Strict id-precedence (F-D):** *"precedence keys on id with strict `<`; a row citing the row it
   supersedes names the antecedent it replaces and is sound."* This fires the deferred operator-twin
   fix: retrofit `instruments/soundness.py` (the live-psql twin, still ts-`<=`) to id-`<`, re-verify
   the five consumers byte-identical on banked records, and add an operator-twin differential
   (`soundness.lp` vs `soundness.py`) — or dedupe the keying to one home — so the two encodings can
   never silently diverge again. Remove the `HAZARD(F-D)` markers on completion.

## Re-entry conditions codified (2026-07-06, link-20 build; appended non-destructively per ADR-0005 Rule 8)

The e14 build (AC3) codifies the DTO **re-entry / recognition conditions** into the s14 lineage
schema's `validate_amends` comment (`harness/e14-build/s14-schema.sql`). Consistent with the
maintainer ruling above — **DTO is the ADOPTED shape (burden inverted); it displaces the "typed
sub-row clause model" as the named re-entry target** — these are the recognition surfaces that
commission the deferred DTO *shape* build (the DECISION to build DTO is already made; only the
detailed edges — `decomposes` + group identity + faithfulness/MECE attestation + inbound-edge
re-key — are deferred). The interim mechanism remains `amends` with the AC2 uniqueness hardening.
`amends` is NOT retired: per the two-track regulatory practice (consult 19 §2), quote-and-strike
serves clause repair, DTO serves the case where fragments must be first-class; neither retires the
other. The first of the three conditions that fires commissions the DTO build (first exercise
apparatus-authored, consult 19 §1.7):

1. a defeated clause not expressible as ONE contiguous quotation (an implication spread across
   sentences) — mechanically self-announcing (the author cannot form a valid `amends_scope`;
   escalate, never paraphrase). Close-sweep surface: `close_sweep.py` condition-1 (tee.log
   quotation-contract refusals).
2. a SECOND in-force `amends` on one target — the row's individuation is wrong; it is due
   decomposition, not a third patch. Standing detector: `soundness.py` `condition2_individuation`
   (a query over existing columns — ratified §H, ships now).
3. any edge that must cite a FRAGMENT as its target (an antecedent, an answer, an attestation, a
   partial reinstatement of defeated text) — review-recognized. Close-sweep surfaces:
   `close_sweep.py` condition-3 (scope-narrowing qualifiers / fragment-reference questions) and R3b
   (subsequent-citation fragment-reliance adjudication).

`clause_defeat_moot` (soundness.py) EXTENDS to decomposition when DTO lands — a target later
*decomposed*, not only *superseded*, moots a standing `amends` edge through the ledger's own
vocabulary (no new mechanism). Noted here as DESIGN, not built (no consumer yet — the ADR-0008
no-fabricated-structure discipline).
