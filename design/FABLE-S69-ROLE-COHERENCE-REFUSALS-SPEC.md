# FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC — the work-role doctrine's three enforcement gaps close, plus the s61 teach-text rider

<!-- doc-attest-exempt: Fable-authored spec 2026-07-28, maintainer-ratified the same day
(autoharn3 ledger row 201, his disposition verbatim in that row: "1(a) as you suggest,
with the proviso ... 1(b) and 1(c) as recommended ... 5 yes, fold into s69"). The A:B:C
loop runs on the build, not the proposal text. Removal condition: superseded by the
build's merge record. -->
<!-- design-currency: status=ratified depends-on=WORK-ROLE-PRACTICE-EVIDENCE-2026-07-28.md,CONSULT-WORK-ROLE-DOCTRINE-2026-07-28.md -->

One kernel lineage delta, `kernel/lineage/s69-role-coherence-refusals.sql`, entering
the birth chain for the NEXT world (runs-are-linear; no live world changes). It
mechanizes exactly the three enforcement gaps the work-role census
([design/WORK-ROLE-PRACTICE-EVIDENCE-2026-07-28.md](WORK-ROLE-PRACTICE-EVIDENCE-2026-07-28.md)
§4) enumerated and the second-Fable consult
([design/CONSULT-WORK-ROLE-DOCTRINE-2026-07-28.md](CONSULT-WORK-ROLE-DOCTRINE-2026-07-28.md))
put its name on, in the consult's exact forms — all three strictly-additive refusals
(the 2026-07-09 class rule covers the shape; the maintainer ratified them individually
anyway) — plus one semantics-neutral teach-text re-issue that is OUTSIDE the fail-safe
class and carries its own explicit ratification (row 201 item 5).

## 0. The governing principle the maintainer attached (row 201, binding on the shape)

His words: a higher authority "can be capable of judging another actor inept … so a
claim must be able to be defeated and reclaimed" — autoharn must be capable of
handling imperfect agents. Consequence for every rule below: nothing in s69 freezes a
role assignment. A claim is defeated by a later claim (already legal, s47's
multiple-claimants design); an open item is superseded/overturned through the
existing append-only semantics. s69's refusals bind acts to the CURRENT holder of a
role, never to a historical one, so the defeat-and-reclaim path composes with them
transparently rather than fighting them.

## 1. The three refusals

1. **Closer-is-claimant-of-record.** `work_closed` (and `work_closed` written through
   any path — one home, the existing validator `validate_work_item_close`) is refused
   when the closing actor is not the item's claimant-of-record, defined as the actor
   of the LATEST in-force `work_claimed` row for the slug (the same resolution
   `work_item_current.claimant` already computes — cite it, do not re-derive a second
   definition). The teach-text names the sanctioned path in the doctrine's own words:
   a cross-identity close is a handoff, and handoffs are claims — claim first, then
   close as yourself. Explicitly NOT built: any binding to the opener, any binding to
   a historical claimant (that would foreclose the §0 reclaim), any composite-parent
   trigger carve-out — the composite reading is doctrinal (the decomposer claims the
   parent at decomposition time; its close is then ordinary under this rule; the FAQ
   section carries that convention).
2. **Witness-ref shape, per close shape.** Extend `validate_review_witness_existence`
   (s48): a `row:<id>` witness citation on a close is refused unless the cited row's
   kind is `review` or `finding`, OR the cited row is a `work_opened` row of a CHILD
   of the closing slug (an in-force parent edge from the child to the closing item —
   the planning-close carve-in; the consult's decidable enumeration, verbatim
   adopted). `commit:<sha>` citations are untouched by construction (s48's `row:`
   check never sees them). The refusal's teach-text names the legal shapes and why a
   `work_claimed` row is not evidence (the autoharn2 row-1265 specimen class).
3. **Review-regards-in-force.** A `kind='review'` row whose `regards` names a row
   that has an in-force superseder is refused, teaching "cite the successor" and
   naming the successor's id in the message (the kernel knows it — say it; a refusal
   that withholds the fix it just computed is not teaching). This mechanizes the only
   failure the census watched happen live twice (the experience4 431/435 specimen).
   Scope note, stated so the builder does not widen it: the rule keys on the REGARDED
   row being superseded — it does not touch reviews of in-force rows of any kind, and
   the s56 reservation-discharge path (a review regarding an in-force reservation
   review) is unaffected because its regarded row is in force.

## 2. The rider (row 201 item 5 — explicitly ratified, NOT fail-safe-class)

`s61-signature-symmetry-and-key-binding.sql`'s frozen refusal text instructs the
operator to run `./led …` — a surface no current world has. s69 re-issues the ONE
function carrying that text (head-body rule: cite the prior body, carry
`-- prior-body-sha256`, `gates/lineage_reissue_lineage.py` enforces both), changing
NOTHING but the printed teach-text spelling (`./led` → `./autoharn led`). Every other
line byte-identical. If the builder finds MORE frozen `./led` teach-text sites in
other lineage functions, they are listed in the report and folded in ONLY if the
maintainer's item-5 ratification plainly covers them (same defect, same fix); doubt
routes to the maintainer, not into the commit.

## 3. What s69 does NOT do

No new columns (compute_row_hash unchanged — state this and let the hash-coverage
gate prove it), no new kinds, no new views (the approved role-census view is a
separate serving-layer build, not kernel), no change to claim semantics (multiple
claims stay legal; last-claim-wins stays the view's resolution), no opener/closer
binding, no independence-vocabulary change.

## 4. Witness plan (scratch, both polarities, red first — new seen-red family, registered)

RED (pre-delta baseline, witnessed conflations): a close by a never-claimant accepted
today; a close by a superseded claimant accepted today; a `row:` witness citing a
`work_claimed` row accepted today (the 1265 shape); a review regarding a superseded
close accepted today (the 431 shape). GREEN (post-delta): each refuses with its
teach-text, and the refusals journal as s43 `write_refused` rows with the refusal
oracle reconciling; the HAPPY paths witnessed unchanged — ordinary claimant close;
claim-over-live-claim then close by the new claimant (the §0 reclaim, witnessed
end-to-end: A claims, B reclaims, B closes, accepted); a planning close citing its
child's `work_opened` row (the carve-in, both polarities: legal child accepted,
non-child `work_opened` refused); a review regarding the in-force successor accepted;
the s56 reservation-discharge path re-witnessed unaffected; the re-issued s61
function's refusal printing the corrected spelling, every other behavior
byte-identical (diff the function bodies). Chain: full newborn birth through s69;
`./judge` AGREE; `verify-chain` INTACT; all lineage/hash/census gates clean, banks
updated same commit; `LINEAGE_CHAIN` and the lineage-coverage gate extended to s69.
Autoharn.idr: extend the model's AS-OF to s69 or leave a LAGGING suffix honestly in
place — state which.

## 5. Closure statement (ADR-0000 Rule 2(a))

Quantification universe: the work-lifecycle enforcement gaps enumerated by the census
§4 as "pure convention" or defect — closer↔claimant unbound (closed by §1.1),
witness-ref shape unchecked (closed by §1.2), review-regards staleness unchecked
(closed by §1.3) — plus the one frozen teach-text defect the spelling sweep flagged
(closed by §2). Not covered, stated honestly: performer-identity fidelity (who SHOULD
have claimed) is not mechanically decidable and stays doctrine + the approved
role-census view; scope-change (re-scoping) review posture stays convention pending a
decidable discriminator (the doctrine says so); `review_detail` adoption stays
doctrine (row 201 item 2). AMENDED 2026-07-28 at the build (coordinator adjudication,
disclosed to the maintainer): the sentence that stood here — "claim-before-close
stays CLI-side ... not smuggled in" — contradicted §1.1's own letter, under which a
NEVER-claimed item has no claimant-of-record and its close is therefore refused (no
closer can equal a claimant that does not exist). The builder read §1.1 strictly and
disclosed it; the strict reading stands, because an unclaimed close is precisely the
unattributable-accountability hole the ratifying ruling targets (and the run-5
forensics' witnessed shape). Net: in-kernel claim-before-close arrives as an
ENTAILMENT of closer-is-claimant-of-record, not as a separate rule.

## License

Public Domain (The Unlicense).
