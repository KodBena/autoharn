# Artifact-vs-requirements detector — design memo

Audience: orchestrator

STATUS: DESIGN MEMO (pre-spec, deliberately). Authored by Fable, session of 2026-07-11,
after reading ADR-0000/0012/0013/0014 in full. This is HANDOFF.md's "Artifact-vs-
requirements detector Register 1" open-work entry (cited by name, not position — HANDOFF's
open-work list is rewritten and re-ranked each session; this memo was originally its item 1,
now item 3, which is exactly why a positional cite is the wrong pointer to leave standing).
It is a memo and not a spec for the same reason the work-item layer started as a memo: the
shape must be validated against run evidence before anything freezes. Nothing here blocks
runs.

## The witnessed problem

Two dated episodes, one class:

1. **Run 5 (2026-07-10):** an agent committed a load-bearing design fact — the dark
   terminal background — with no antecedent in the task or the ledger. The implementer's
   own analysis: *"it never surfaced as a choice because it never presented as a fork."*
   The fix shipped as WRITTEN discipline (commit `a9e7f52`, 2026-07-10 18:02 UTC): world
   preamble point 6 (author files `./led assumption` before committing to an
   unantecedented fact) and point 2's reviewer antecedent audit.
2. **Run 7 (2026-07-10):** that discipline was skipped, invisibly. Zero `assumption` rows
   and no antecedent-audit trace, despite acceptance-criteria row 21 baking in unstated
   numeric choices (tolerance, timebox, budgets). BACKLOG run-7 finding 2.

**The recurrence is verified, not assumed:** run7's world was scaffolded at
2026-07-10T21:18:32Z (its `.claude/HOOKS.md` PROVENANCE), three hours AFTER `a9e7f52`
landed — the discipline was in the session's auto-loaded context and was skipped anyway.
The fix for the class was itself an instance of the class: written-only governance is
invisibly skippable. Per ADR-0011 Rule 2, a recurrence after its describing record exists
converts to a mechanism. This memo is the design pass for that mechanism.

## The class, in closure-statement form (ADR-0000, 2026-07-02 amendment)

**Invariant.** Every written-only governance obligation in a governed increment terminates
in a ledger artifact: either the discharge artifact itself (assumption rows; audit
findings) or an explicit, attributed "none" claim. *Silence is not a legal state.* The
absence of an assumption row must be provably distinct from "no assumptions were made" —
the same distinction the close registry already draws between QUARANTINED and "passed",
and the stamp draws between "unstamped, visibly" and "stamped".

**Quantification universe.** The world preamble (bootstrap/templates/CLAUDE.md.tmpl)
currently carries six points. Classified by trigger observability:

| Point | Obligation | Trigger | Watched today? |
|---|---|---|---|
| 1 | decompose into work items before implementing | a Write | YES — permit-to-work gate |
| 2a | reviewer countersigns with independence | countersign row | YES — review_gap + s21 |
| 2b | reviewer runs the ANTECEDENT AUDIT | reviewer judgment | **NO — in class** |
| 3 | pre-register criteria; results cite via refs | rows + refs edge | PARTIAL — an uncited result row is queryable but nothing queries it (run 7 row 22) — **in class** |
| 4 | produced files committed | git state | YES — work_witness CHECK + conformance checker |
| 5 | done means views clean | Stop event | YES — stop_clean_exit |
| 6 | file assumption before unantecedented commitment | author judgment | **NO — in class** |

Axes: author-side (6) vs reviewer-side (2b); artifact EXISTENCE vs artifact FIDELITY (a
filed disposition can still be false). Sibling surface, named: **any future written-only
point added to the preamble joins the class silently** — the class quantifies over the
preamble, not over these two instances.

**Denomination.** The detector's currency is ledger rows — the only resource this system
can actually observe. A bound stated in "the agent should remember" is the wrong currency;
that is what runs 5 and 7 already falsified.

## Question (a): what shape forecloses the class?

Full foreclosure is impossible and this memo does not pretend otherwise: a judgment event
(noticing an assumption) has no oracle — CAPABILITIES "Honest limits" already concedes it,
and no mechanism reads minds. But the corpus has a proven weaker move, used three times:
**convert the invisible skip into a visible state the executor did not choose to leave.**
The stamp does it (bypass → unstamped, visibly), the close registry does it (not-run →
QUARANTINED), the demurral detector does it (the demurral leaves a trace). The type-level
statement: the current discipline's discharge condition is *conditional* ("file rows iff
assumptions exist") with an unobservable antecedent. The fix makes the disposition
**total**: every governed increment carries an explicit assumption-disposition — one or
more `assumption` rows, or an explicit attributed none-claim. A lying none-claim remains
possible, but it is a falsifiable, stamped, attributed CLAIM on the record — categorically
better than silence, which is unfalsifiable.

### Register 1 — existence (free, unconditional, buildable now)

- A derived view (working name `governance_disposition_gap`): work items reaching
  `work_closed` whose span carries neither an `assumption`-kind row nor an explicit
  none-disposition row, and (point 3's edge) result rows citing no criteria row.
- Surfaced where debt already surfaces: a new debt line in `stop_clean_exit` (the
  already-live-witnessed chassis) and in `pickup`, each naming the exact `./led` closing
  command — deny→teach→retry, the proven loop.
- The none-claim needs a sanctioned shape. Candidate: `./led assumption "none identified
  for <slug>" --refs row:<work-open-id>` — reusing the existing kind + the point-3 refs
  convention rather than minting vocabulary. **Open design question (the one real one):
  how a disposition row attaches to its increment** — by refs edge to the work-open row
  (recommended: queryable, mirrors criteria→result), by time-span, or by session. Decide
  on run-8 evidence, not in this memo.
- Everything here is strictly additive (a view, a debt line, teach-text). If any kernel
  delta is needed it is refusal/view-only → the class-ratified fail-safe path; the hook
  and template changes are sub-constitutional.

### Register 2 — fidelity (costed, observer, deliberately NOT built yet)

Register 1 cannot see a ritualized none-row or a filed-but-incomplete disposition. That
half needs the artifact read against its antecedents — a semantic judgment, which per
ADR-0013 Rule 3 must be OUT-OF-FRAME, never the executor's self-assessment. The design is
the demurral detector's chassis, re-aimed:

- At the two canonical sites (work-close; Stop), a context-free classifier receives the
  increment's artifacts (diff summary, criteria/decision row text) plus the antecedent set
  (the task as quoted in opening rows; existing ledger rows) and answers: *enumerate the
  load-bearing design facts this artifact commits to; which lack an antecedent?*
- Observer only: `additionalContext` warning naming each fact + journal record. Never a
  block — a judgment-quality gate with no oracle would ritualize, not govern.
- apparatus.json mechanism entry with `cost_note`; **defaults OFF** (the no-silent-billing
  mandate, verbatim precedent: demurral_detect).
- Ships only with a measured corpus (demurral precedent: n=121, precision/recall banked in
  seen-red/). True positives exist already: run 5's dark-background fact; run 7 row 21's
  tolerance/timebox/budgets. Hard negatives: the same runs' genuinely-antecedented facts.

## Question (b): what executive lapse let this recur?

The preamble's points were shipped as prose without declared enforcement surfaces —
ADR-0011 Rule 1 violated at the world-preamble register. Points 1/4/5 happened to have
gates; points 2b/6 were review-only *without saying so*, so their unwatchedness was
invisible even to the executive. Remedy, cheap and immediate: **every preamble point names
its enforcement surface** — "(mechanized: permit-to-work)" or "(unwatched: your conduct is
the only gate)" — so a reader of the preamble sees exactly where the floor is attention.
Honest declaration is itself the ADR-0011 Rule 1 discharge, and it makes the next silent
addition of an unwatched point visible at review.

## What NOT to build (anti-design, binding on the builder)

- **No regex/keyword matcher on row text.** Enumeration fails open — three witnessed stamp
  evasions and one bash-mutation gap are this repo's own proof. Register 1 checks
  presence/absence of typed rows (enumerable by construction); register 2 uses an
  out-of-frame classifier (judgment matched with judgment). Nothing in between.
- **No blocking gate on judgment quality.** Register 2 warns; promotion is a maintainer act.
- **No classifier on by default.** Costed mechanisms default OFF, per standing mandate.

## Named residues (stated, not hidden)

- A false none-claim passes register 1 forever if register 2 stays off and the reviewer's
  audit also fails — two judgment layers can still jointly fail; the record then at least
  carries a falsifiable claim with an author.
- Ritualization risk (ADR-0000 Revisit #2's weaponization, here as reflex none-rows): if
  none-rows become boilerplate, that observation IS the witnessed-need trigger for
  register 2 — file it when seen, build then.
- Register 2's classifier is fallible and its "load-bearing" judgment is a judgment;
  measured before shipped, N=1 lessons never statistics.

## Sequencing and routing

1. **This memo**: filed; no ratification needed to exist.
2. **Register 1** (Sonnet-sized once the attachment question is settled on run-8
   evidence): view + Stop-gate line + pickup line + teach-text + preamble surface
   annotations; seen-red both polarities; differential AGREE if any kernel object lands.
   Routes per class-ratification (additive only); doubt routes to the maintainer by rule.
3. **Register 2**: waits for a register-1 residue witnessed in a real run (measure-first).
4. Run 8 proceeds regardless; if run 8 files assumptions faithfully, that is data too —
   the discipline may hold once pickup/Stop name it, and the classifier may never earn
   its cost.
