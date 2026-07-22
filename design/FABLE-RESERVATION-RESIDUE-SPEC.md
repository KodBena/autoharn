# FABLE-RESERVATION-RESIDUE-SPEC — attest_with_reservations discharges, the reservation becomes tracked residue

<!-- doc-attest-exempt: commissioned build basis, frozen 2026-07-22 (maintainer ratification
below). Construction reads from this file as-frozen; A:B:C prose-polish runs separately
against a live edition per the build-basis precedent. Removal condition: strike when a
polished live edition supersedes this. -->

- **Status:** Fable-authored, maintainer-ratified 2026-07-22 ("Kernel semantics change
  approved as a matter of course. If the kernel is wrong, it would be pointless. Let's
  do it."), against autoharn2 ledger rows 1093–1095.
- **Provenance:** the experience2 backflow finding (AUTOHARN_BACKFLOW.md 2026-07-22,
  "work_review_gap discharge inconsistency"): a genuinely-performed, distinct-actor,
  reservation-carrying countersign left its work item surfaced as open,
  indistinguishable from an item nobody reviewed, and created live pressure to
  fabricate a clean `attest` to satisfy the gate (resisted, disclosed). Verdict storage
  was verified sound (experience2 review_detail rows 116–119 read live); the defect is
  semantic and uniform.
- **Industry basis (informing, not authority):** formal-inspection regimes (Fagan,
  IEEE 1028; the shapes DO-178C / ISO 26262 / NRC licensing reviews expect) close the
  review event on an accept-with-rework verdict and track each reservation to its own
  independent closure. The reviewer's verdict is final; the system, not trust, carries
  the residue.

## 1. The defect class and its closure statement (ADR-0000 Rule 2(a), 2026-07-02 form)

**Invariant:** everywhere the kernel asks "has row R been discharged by an
un-superseded distinct-actor review," a review whose verdict is
`attest_with_reservations` answers YES exactly as `attest` does, and every such
reservation additionally appears on exactly one derived surface
(`reservations_outstanding`) until it is itself dispositioned. `refuse` continues to
answer NO everywhere. No consumer may ever again distinguish the two attesting
verdicts by hand-copying a verdict filter (that is s32's F6 class, already foreclosed
by the single home).

**Quantification universe.** The verdict filter has ONE home:
`discharging_attest` (s32 Element 2). Its consumers — enumerated from
`grep -l discharging_attest kernel/lineage/*.sql`, and each to be re-verified by the
builder against the CURRENT (latest re-issued) definition, not the historical one —
are: the four s32 re-issues (`review_gap`, `countersigned_in_force`,
`work_review_gap`, `work_item_strict_blockers`), s33 composite discharge, s36
decision grade, s37 violation disposition, and the uses in s40, s41, s43, s44, s53.
All of them acquire the widened semantics through the single home; the builder
confirms none carries its own additional `verdict = 'attest'` predicate (if one does,
that is an F6 recurrence to fix in this same delta, loudly noted).
**Named as not covered:** (i) the `refuse` verdict gets no residue surface of its own
(a refusal already blocks discharge loudly; a refuse-residue view is a separate
question, filed not built); (ii) historical worlds already migrated see their CURRENT
derived views re-graded (see HISTORY note §5) — past ledger prose that narrated "gap
open" remains as written, append-only; (iii) the SPA/panel presentation of the new
view is the panel deployment's own work, not this delta's.

**Denomination check:** no numeric bounds exist in this delta; the only "currency" is
the verdict domain itself, and the widened filter is denominated in exactly the
existing CHECK-constrained values (`attest`, `attest_with_reservations`, `refuse`) —
no new values, no string matching outside the constrained domain.

## 2. Kernel delta — one new lineage file, `s56-reservation-residue.sql`

Frozen records are never edited (ADR-0005 Rule 8); everything below is
`CREATE OR REPLACE` / additive in the new file.

- **Element 1 — `discharging_attest` widened in place.** Re-issued with
  `d.verdict IN ('attest','attest_with_reservations')`, its COMMENT amended to state
  the s56 semantics and cite this spec. The name is kept: renaming would force
  re-issuing every consumer for zero semantic gain; the view's identity is "the
  attest-family discharge edge," and the comment says so explicitly.
- **Element 2 — `reservations_outstanding` (new view, additive).** One row per
  un-superseded `review` row with `review_detail.verdict =
  'attest_with_reservations'` that has not been dispositioned. Columns:
  `review_id`, `regards` (the row the review regarded), `reviewer` (actor),
  `basis` (the reservation prose — the load-bearing content). **Disposition, existing
  vocabulary only, no new kinds:** a reservation leaves the view when (a) the review
  row is superseded (the existing uniform-retraction path), OR (b) an un-superseded
  `review` row REGARDING THE RESERVATION REVIEW ITSELF (`r2.regards = review_id`)
  carries verdict `attest` — "reservation dispositioned," by any actor including the
  original reviewer withdrawing their own concern. `security_invoker = true`,
  `GRANT SELECT` to `:role`, COMMENT stating all of the above.
- **Element 3 — the fabrication-pressure note on the record.** The file header names
  the experience2 specimen and ADR-0002's ground: a gate that surfaces a
  reviewed-with-concerns item identically to an unreviewed one rewards fabricating a
  clean verdict; this delta removes the reward and preserves the concern.

## 3. Serving delta (boundary service, closes ledger row 1095's second half)

- Add `reservations_outstanding` to `serving/boundary_service.py`'s VIEW_REGISTRY so
  `GET /d/{deployment}/views/reservations_outstanding` serves it.
- **`review_verdicts` (new kernel view, additive, also in s56 and VIEW_REGISTRY):**
  the general review-legibility surface — every `review` row joined with its
  `review_detail` (`review_id, regards, reviewer, verdict, independence, basis,
  antecedent, superseded` boolean). This is the read path whose absence forced
  experience2 to inspect the wrong column (`attest_verdict`, the s44 model-identity
  field) and mis-diagnose a storage bug.

## 4. Documentation delta

- `design/USER-RECIPES-FAQ.md`: a short recipe-adjacent note stating the s56
  semantics plainly: a reservation-carrying countersign DOES discharge the review
  gap; the reservation lands in `reservations_outstanding` and stays there until
  dispositioned (supersede the review, or attest-review the review row itself).
- `led.tmpl` / legacy-led comment text that says "discharge example: ./led review
  <close-row-id> attest ..." gains one sentence naming the reservations path — the
  undocumented-rule gap row 1094 names.
- GLOSSARY.md: `reservations_outstanding` one-liner if the glossary carries view
  entries of this kind (builder checks the house idiom; if views aren't glossed
  there, skip and say so).

## 5. Migration / HISTORY note

`-- HISTORY: safe` — the delta touches derived views only; zero stored rows change,
no data rewrite, no re-denomination. The stated, intended effect on an existing
world's CURRENT displays: previously-stuck reservation-countersigned items discharge
(experience2 rows 111/113 are the known specimens), and their reservations surface in
`reservations_outstanding` until dispositioned. That re-grading IS the ratified
purpose, stated in the header rather than discovered.

## 6. Witness plan

- **Scratch-schema witness, both polarities**, per the standing ceremony for
  maintainer-ratified kernel deltas: (i) fresh scratch world through s56; (ii) a
  deferred close countersigned `attest` discharges (unchanged behavior); (iii) a
  deferred close countersigned `attest_with_reservations` discharges AND appears in
  `reservations_outstanding` (red first against a pre-s56 scratch: same act leaves
  the gap open — the defect reproduced, then foreclosed); (iv) `refuse` does not
  discharge and does not appear in the residue view; (v) disposition leg (b): an
  attest review regarding the reservation review clears it from the view; (vi)
  supersession leg (a) likewise; (vii) `review_verdicts` returns the verdict for
  every case above, superseded flag correct.
- **Fixture** `seen-red/reservation-residue/run_fixtures.py` mechanizing the above;
  registered in `gates/fixture_census.py`.
- All gates green; ./migrate accepts the manifest with the HISTORY header.
