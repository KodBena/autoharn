# FABLE-TYPED-ANNULMENT-DISPOSITION-SPEC — a typed consider-and-decline for review debt

<!-- doc-attest-exempt: commissioned spec, frozen 2026-08-06 pending maintainer ratification
(commission row 1083; provenance rows 1025/1008 and missives 1002/1003/1004/1006/1008).
Removal condition: superseded by the ratified delta's own header or the build's completion
record. -->

Fable-authored 2026-08-06. Commission: maintainer instruction 2026-08-06 (ledger row 1083).
Provenance: work item review-obligation-annulment-vocabulary (row 1025), distilling five
experience4 missives of one underlying shape, and their row-1008 correction narrowing it. The
witnessed pain: when a deferred-review obligation turned out not to warrant a review, the only
expressible discharge was `verdict=attest` with a prose disclaimer — the commissioner's own
prose discloses the misfit, and the maintainer's forwarded remark calls it an ADR-0000 smell
(a consider-and-decline shape needs a distinct mechanism, not a borrowed verdict).

## 1. What the substrate already carries (and this spec does not rebuild)

- `work_review_disposition` (s29): a mandatory two-value vocabulary on `work_closed` rows —
  `witnessed` (review evidence cited at close) or `deferred` (typed debt: the close itself
  deposits a `work_review_gap` row that survives until a distinct-actor review discharges it).
- s31 supersession reaches close rows: annulment-in-substance is representable today by
  superseding the deferred close and re-closing. The surface gaps (a verb for supersede-and-
  reclose; stop_clean_exit teach-text naming the path) are work item 1025's (a)/(b) — the B2
  build — and ride this spec's family, not this delta.

The gap this spec closes is (c): the re-close after a legitimate annulment still has only
`witnessed` or `deferred` to say — the first is a lie without evidence, the second re-mints
the very debt being annulled. The consider-and-decline act has no type.

## 2. The delta (one kernel lineage file, next free sNN; Sonnet-authored per the contract)

**Vocabulary.** `work_review_disposition` gains a third legal value, `annulled`: this close's
review obligation was considered and declined by an authority distinct from the obligor, for a
recorded reason. Existing rows untouched; existing two values unchanged (HISTORY: safe,
re-issue-wider CHECK, s39's own idiom).

**Construction-time requirements on an annulled close** (each a refusal that teaches):

1. `work_review_ref` is MANDATORY and must cite an in-force ledger row — the annulment
   authority row — whose statement carries the annulment rationale. A dangling or retracted
   citation is refused. (Typed authority, never prose-only; ADR-0008.)
2. No self-annulment: the annulment authority row's actor must be distinct from the annulled
   obligation's obligor — the actor of the superseded deferred close (or of the close row
   itself where no predecessor exists). Distinctness composes with s21 session-aware
   distinctness exactly as review countersigns do: same session + same agent cannot manufacture
   the distinction. The precise predicate is the builder's to design against the s40/s41
   identity substrate and to defend in the delta header.
3. `annulled` is legal ONLY where `deferred` would have been legal — it is a disposition of
   review debt, never a substitute for a ship witness or any other close requirement; every
   other close-time refusal binds unchanged.

**Derived truth.** `work_review_gap` treats an in-force annulled close as discharged debt (that
is the point of the type); a new single-home view lists every annulled close with its authority
row for the audit read — the two-biases guard's structural answer: annulments are never silent,
they are enumerable. Whether the violations views want a defense-in-depth member (e.g. an
annulled close whose authority row is later retracted) is the builder's judgment, stated either
way in the delta header per the LIMITS convention.

**Engine/ASP.** The builder verifies and discloses the differential surface per s39's own
ENGINE section idiom: whatever `./judge` compares must AGREE on both polarities, and anything
out of the compared-atom scope is said so explicitly, never assumed.

## 2a. Closure statement (ADR-0000 Rule 2(a) posture)

Quantification universe this spec claims closure over: the `work_review_disposition` CHECK, the
close-time validation leaf(s) that read it, `work_review_gap`, the new audit view, and the B2
verb's annul mode. Nothing else — verdicts vocabulary (s15 `attest|attest_with_reservations|
refuse`), obligation revocation, non-work review_gap, and missive acts are explicitly out of
scope and unchanged.

## 3. Ratification routing — this is NOT in the pre-ratified fail-safe class

Read plainly: `annulled` ADDS a discharge path for existing typed debt. Nothing existing is
widened for writers who don't use it, every new construction is refusal-guarded, but a
vocabulary value that lets recorded debt be discharged without a review is a relaxation under
the standing class test ("a delta that loosens any refusal ... routes to the maintainer").
Doubt about the side IS the routing. So: this delta enters the birth chain only on the
maintainer's explicit ratification of this spec — his 2026-08-06 commission ordered the spec
and its scheduling; the ratification is his separate, prepared yes/no.

## 4. Implementation schedule

On ratification: one Sonnet builder authors the delta + scratch-witnesses both polarities
(annulled close accepted with valid authority; refused on missing/dangling ref, on self-
annulment, on non-debt contexts) with the SQL/ASP differential in AGREE, wires `LINEAGE_CHAIN`
in the same commit (s37/s38/s39 precedent), and never applies to any live world (runs are
linear; it rides the next birth). The B2 surface build (supersede-and-reclose verb + teach-
text + FAQ entry) follows in the same family: the verb's annul mode writes the typed
disposition; its stop_clean_exit.py teach-text line stays gated on a hooks/ quiet window
(durable row 263). Named consumers, per the standing test: the stop-gate's clean-exit check,
work_review_gap readers, experience4's CosignPanel, and the FAQ's correcting-the-record recipe.
