<!-- doc-attest-exempt: as-delivered consult record, filed verbatim 2026-07-28
(maintainer commission: "run this all by a second Fable consult (ADR-0018-ish) ... with
web access ... This is one thing I'd like to get right, then codified once and for all";
brief CONSULT-WORK-ROLE-DOCTRINE.md, sealed two-phase shape). DISCLOSED DEVIATION: the
brief mandated Phase 1 (blind independent derivation) be written out in full before the
seal was opened; the consultant's final report carries only Phase 2, so the blind
derivation is attested by the report's own claims, not inspectable. The coordinator
weighed each correction on its argued evidence (every one cites the census, the kernel
source, or fetched prior art), not on the independence claim. Removal condition:
superseded by the maintainer's disposition of the doctrine. -->

**Provenance:** produced by a second Fable-class consultant (2026-07-28) over the
work-role doctrine (FAQ section at commit 5541e5d, census at
WORK-ROLE-PRACTICE-EVIDENCE-2026-07-28.md, the coordinator's sealed assessments). Filed
verbatim; the corrections it mandates were applied to the FAQ in the same commit family.

---

## Phase 2 — adjudication (FAQ as committed at 5541e5d, plus the sealed assessments)

### Where my derivation AGREES (adjudicated corroboration, per the disclosure above)

- **Opening as ownerless initiator's act; open backlog healthy.** Agree, and prior art is behind it (anyone files a CAPA; triage assigns).
- **Accountability rides the claim; closer-should-be-claimant; cross-identity close legitimized only as claim-first handoff.** Agree — this and the sealed Tier 1 item 1 are the same rule I derived from the ALCOA/RACI single-accountable line, and the "a cross-identity close is a handoff, and handoffs are claims" teaching text is exactly the right refusal shape.
- **Performer claims; minted-delegate attribution.** Agree — the census's all-`author` claims are the one genuine ALCOA violation in current practice, and it is correctly placed in Tier 2 (visibility, not refusal): no trigger can know a claim "should" have been a delegate's.
- **Fix-gate rules 1–4** (grade-don't-forbid self-review; refuse→superseding close; re-review regards successor; refusing-reviewer-preferred). Agree on all four, including keeping rule 4 convention — Gerrit's posture (self-approval restriction is deliberate configuration, not built-in) independently supports grade-not-forbid as the honest single-operator GxP translation.
- **Sealed Tier 3 (don't force opener≠closer, don't forbid self-review, don't mandate `review_detail` yet).** Full agreement; `review_detail`'s zero adoption in two worlds proves mandate-before-doctrine would just produce ritual rows.
- **Sealed planning points 1–3.** My Phase-1 §6 lands on the same three: doctrine recurses onto authored decompositions; composite-parent claim means "I own this tree's shape"; self-re-scoping is the live hazard, convention-plus-visibility now because a decidable refusal that spares legitimate coordinator restructuring cannot yet be stated. I add one connection worth writing into the FAQ: self-re-scoping is the work-item-level instance of ADR-0000's closure-statement finding ("the class gets named at exactly the scope of the fix the executor has already built") — citing that gives the subsection a law anchor, not just an analogy.
- **Sealed point 4 (per-resolution witness shapes).** Agree, and it is load-bearing: a flat "review/finding only" s48 tightening would refuse honest planning closes on day one.

### Where I DIVERGE, and who is right

1. **The FAQ's taxonomy verdict overstates "nothing missing" by one derived view.** The claim-steal/handoff/co-claim ambiguity (s47: multiple claims legal, last-claim-wins is a view convention) is real, but on the named-consumer test I *demote my own Phase-1 instinct*: no new ledger kind — a handoff is already fully representable (claim by incoming owner over a live claim), and the consumer ("who owned this item when?") is served by the Tier-2 role view, which can flag claim-over-live-claim-by-distinct-actor shapes mechanically. So the FAQ's "nothing missing" survives at the vocabulary level, but the section should *name* the ambiguity and its view-level resolution instead of silently rolling it into "multiple claims are legal by design."
2. **The FAQ's opener obligation is too thin.** It requires only the current-rationale (the 2026-07-23 directive). But the whole rest of the doctrine — closer attests "done as the resolution says," re-review regards the successor — presupposes something adjudicable to attest *against*. Change-control prior art puts acceptance criteria in the change request, not in the closer's head. This should be added as a SHOULD (convention, not gate): the opening statement carries a definition-of-done a zero-context closer could adjudicate (ADR-0017 applied to item text), and dependencies as typed edges rather than prose.
3. **The FAQ proposes two kernel deltas; the record supports three.** Review-regards-in-force (sealed Tier 1 item 3) is derivable straight from the census (row 431 attesting dead row 413, *twice*, caught only by self-discipline) and is the most mechanically crisp of the three: refuse a `review` whose `regards` row has an unsuperseded successor, teaching "cite the successor." I derived it independently in Phase 1. The committed FAQ describes the specimen (its rule 3) but then omits the delta from its closing proposal paragraph — an internal inconsistency: the section's own worked negative specimen is the one failure it declines to mechanize, in a shop whose law (ADR-0011 life-critical amendment) says the mechanism ships with the first fix.

### What is WRONG / OVERCLAIMED / MISSING — per-paragraph correction list

**(W1) Wrong attribution, "Who claims" paragraph.** Current text: *"and since s64 the `dispatch mint` verb that mints a delegate principal against a commission row"*. s64's own header says the opposite: *"Hooks (item 2) and dispatch mechanics (item 3, minting the principal + writing the edge + injecting the stamp) are NOT built here, per the commission's own explicit instruction"*. The verb that exists is `autoharn dispatch` (`libexec/autoharn/dispatch` → `tools/dispatch_mechanics.py`, built under design/FABLE-DISPATCH-MECHANICS-SPEC.md §3, rows 1463/1467/1468/1471), and it is **this repo's own deployment only** — its docstring states a fresh scaffolded world gets the verb only if a future scaffold-migration adds it. Replacement: *"…and the repo's own `autoharn dispatch` verb (design/FABLE-DISPATCH-MECHANICS-SPEC.md; s64 supplies the kernel side — delegation-condition columns and the scoped chain walk — while the mint verb itself is repo-local and not yet scaffolded into fresh worlds)"*. As written, a fresh-world reader would go looking for a verb their world does not have.

**(A1) Addition, "Who opens" paragraph.** After *"The opener's one obligation is that rationale, written into the opening statement."* append: *"A second obligation is convention, not gate: an item intended to be claimed carries a definition-of-done a zero-context closer could adjudicate against, and its dependencies as typed edges (`blocks-start`/`blocks-close`) rather than prose — the close-attestation and regards-the-successor rules below have nothing to bite on without it."*

**(A2) Addition, "Must the opener close it?" paragraph.** The handoff sentence should name the ambiguity it resolves: after *"then closes as themselves"*, add that a claim over a live claim by a distinct actor is the handoff's entire record — the role-census view (below/Tier 2) surfaces these so a handoff and a claim-steal are distinguishable by inspection, without minting a new ledger kind.

**(E1) Edit, fix-gate rule 3.** Keep the specimen, add the mechanization: this is the third candidate fail-safe delta, not a convention — refuse a `review` regarding a close row that has an unsuperseded successor. Then:

**(E2) Edit, closing paragraph.** *"(a) and (b) are candidate fail-safe kernel deltas"* → three candidates: (a) closer-is-claimant-of-record; (b) witness-ref shape; (c) review-regards-in-force. All strictly-additive refusals; the 2026-07-09 class ratification covers all three.

**(A3) The planning/restructuring subsection: add it, with the sealed content plus two sharpenings.** The four sealed points survive my scrutiny and should land as written, with these refinements I will own:
- *Sharpening the witness-shape enumeration (sealed point 4):* "per resolution kind" is not quite the decidable axis — `work_resolution` is shipped/superseded/dropped/deferred; "planning close" is not a resolution. The decidable enumeration is per close *shape*: for `row:` citations, legal witnesses are `review`/`finding` rows generally, **plus** `work_opened` rows of children where the closing slug has in-force parent edges to them (s28/s33 supplies the child relation); `bookkeeping` closes cite `commit:<sha>`, which s48's `row:` check never touches, so they are unaffected by construction. Stated this way the delta is fail-safe and refuses no honest close I can construct; stated as "per resolution kind" it would be unimplementable as written.
- *Closer-is-claimant's composite reading (sealed point 2):* specify it as — the shape-owner (decomposer) claims the composite parent at decomposition time; its close is then ordinary under the refusal (closer == that claimant). No special-case carve-out in the trigger is needed if the doctrine says the claim lands at decomposition time; prefer that over a bookkeeping exemption in the refusal itself, which would reopen the very hole the delta closes.
- *Law anchor for the re-scoping hazard (sealed point 3):* cite ADR-0000's 2026-07-02 closure-statement amendment — self-re-scoping is that finding operating at the work-item grain. Convention-plus-visibility now is right; a future refusal needs a decidable discriminator that does not yet exist, and saying so in the section is ADR-0011 Rule 1 honesty.

**(V1) Tier 2 view — endorse, with its consumer named in the text.** The per-item opener/claimant(s)/closer/reviewer-with-grades view passes the named-consumer test only if the FAQ names who opens it: `./pickup`-time hydration and post-hoc RCA ("who was accountable when this shipped"). Write the consumer into the section; a view "for visibility" is the demurral shape the named-consumer anecdote catches.

### Verdict on the two (now three) candidate deltas

- **Closer-is-claimant:** survives; ship with the composite reading specified as claim-at-decomposition-time, not as a trigger exemption.
- **Witness-ref shape:** survives *only* in the per-close-shape enumeration above; the flat form would refuse honest planning closes and must not ship.
- **Review-regards-in-force:** I add it; it is the crispest of the three and mechanizes the only failure the census actually watched happen twice.

All three are strictly-additive refusals under the 2026-07-09 class rule; the maintainer's disposition still governs, but I put my name on all three in the forms stated. The FAQ's overall shape is right; the corrections are W1 (a real factual error a fresh-world reader would trip on), the missing third delta, the missing planning subsection, and the three additions above.