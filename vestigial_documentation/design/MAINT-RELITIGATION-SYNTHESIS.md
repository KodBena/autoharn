# Re-litigation synthesis — the adoption question, modulo adoption evidence

Audience: maintainer

This document synthesizes the five-lens re-litigation you commissioned on 2026-07-12
(tracker rows record the commissioning; the five lens reports live in this session's
transcript and their load-bearing findings are transcribed here). The question you
posed: the prior regulator-panel assessment
([MAINT-REGULATOR-ADOPTION-ASSESSMENT.md](MAINT-REGULATOR-ADOPTION-ASSESSMENT.md))
returned "not yet" verdicts that you suspected were dominated by ONE argument — no
adoption evidence — so each lens was re-run under an arguendo assumption (years of
mature, clean, multi-project adoption) and asked what survives on design substance
alone. Five lenses ran: NRC, FAA/DO-178C, NIST, ICJ/evidentiary, and financial audit
(your mid-flight addition).

## The verdict, in one paragraph

Your suspicion is **substantially confirmed, with one honest dissent**. The panel
splits 3–2: ICJ, NIST, and financial audit return ADOPTABLE-IN-PRINCIPLE under
arguendo (financial with the qualification that this means internal-controls-grade,
not external-assurance-grade); NRC and FAA return STILL-NOT-YET, but on grounds that
are *architectural rather than calendar* — meaning even their dissents vindicate the
re-litigation, because they now name what has to *change* rather than what has to
*accumulate*. NIST's classification is the sharpest confirmation: the prior panel's
top two gaps — the inert crypto layer and the unapplied perimeter — plus two of its
recurring refrains (the unsigned git history, the N=1 evidence-volume caveat) are
adoption-state arguments that dissolve by assumption. FAA dissents on
the bias hypothesis itself, arguing the prior panel's architectural items were always
there beneath the arming complaints — a fair reading you should weigh, since it came
from the lens that read the most mechanism source.

## What survives arguendo — the convergent architectural core

Every lens, independently, landed on the same small set. None of these closes with
more runs; each is a design property.

1. **One trust domain.** Verifier, performer, custodian, and superuser are one
   identity on one host under one vendor. Invocation-distinctness — the stamp-pair
   check added at kernel lineage step s21 ([ORCH-CAPABILITIES.md](../../ORCH-CAPABILITIES.md)
   item 3) — is real and fail-safe, but it is not organizational independence — and the
   project's own trust-layer document already says so ("cannot be closed by code
   alone; the decision itself is the deliverable"). This is THE wall between
   internal-controls-grade and external-assurance-grade, and it is decision-shaped:
   a second human key-holder, or a written acceptance of the limit.
2. **No configuration index.** Live verbs read settled evidence with today's code; no
   record ties a historical DENY to the hook bytes that produced it. The remedy is
   the prior assessment's own Tier-1 item 4 (commit hash at scaffold, S-sized) — now
   finally a tracker item (`panel-cheap-fixes`).
3. **The verifier layer is fixture-proven, not qualified.** The seen-red corpus is
   genuine both-polarity integration proof (every lens credited it), but the hooks
   the whole record leans on have no unit/regression suite, and one silent fail-open
   is already on the record.
4. **The `event_declared_ts` channel.** A writer's unauthenticated self-declaration
   downgrades BACKFILL_SUSPECT to LATE_DECLARED. The verdict *string* never lies (ICJ
   credited the anti-laundering rule that a declaration can never discharge an
   ordering obligation), but the exit-code projection is lossy, and the channel is
   the ledger analog of unchecked management override.
5. **Content-blind review discharge.** The run-12 row-20 class ("test" discharging an
   obligation; run 12 is the toy-project world in Postgres schema `run12`, queryable
   read-only per the prior assessment's Method section) is now FLAGGED by the shipped
   audit family, with the honest limit that
   hollow-but-plausible prose is not catchable; ICJ sharpened it further — the
   procured-reviewer circularity (run 12 rows 88–93, a dispatch row pre-capturing its
   own id so its own creature could discharge it) has NO mechanism at all, and
   nothing distinguishes a review dispatched by a third party from one dispatched by
   the row's own author.

## New findings this panel produced (absent from the prior record)

- **Unwitnessed apparatus flips** (NIST): an agent can set a mechanism to `off`
  mid-session with no journal line, no ledger row, no refusal — in a system whose
  evidentiary basis is "hooks only." Cheap in-idiom fix; tracker item
  `apparatus-flip-witnessing`.
- **Procured-reviewer circularity** (ICJ, above) — the day's sharpest finding.
- **TOFU circularity in key distribution** (NIST): rung-1 keys live in the same repo
  the signed tags pin; out-of-band fingerprint publication is undesigned.
- **One register overclaim** (ICJ): the GPG FAQ's "absence of a stamp... proves a
  human typed it" should read "is consistent with" — negative authentication is a
  rebuttable presumption, and the stamp is a disclosed tripwire. In `panel-cheap-fixes`.
- **Untested deletion scenario** (financial): the row-hash chain's witnessed fixtures
  (kernel lineage step s26, [ORCH-CAPABILITIES.md](../../ORCH-CAPABILITIES.md) item 30)
  cover content alteration, not explicit full-row deletion with an id gap — plausibly
  caught structurally, but a hostile-examiner claim wants the fixture. In
  `panel-cheap-fixes`.

## Two prior gaps confirmed overtaken by events

Both the NRC and ICJ lenses flagged that the prior assessment is stale in two places,
in the project's favor: the "contemporaneity single-producer" complaint (Gap 5b) was
closed by the SQL-floor differential the same day the assessment was written, and the
"traceability gap-detection unbuilt" item (Gap 7) was closed by the contemporaneity
audit's Part 3 ([ORCH-CONTEMPORANEITY-PART3-SPEC.md](../../design/ORCH-CONTEMPORANEITY-PART3-SPEC.md))
family F3 — which proved itself by finding a real violation in run 11's history on
its first pass.

## What every lens credited, unprompted

The convergent "better than our usual subjects" list, worth keeping because it names
what must not be traded away in future work: closed verdict vocabularies that never
conflate unchecked with checked-clean; the marriage differential as genuine diverse
redundancy demanding bit-identical agreement; seen-red as real robustness testing;
no LLM verdict in any blocking path; and — named by all five — the self-indictment
culture: the hash collision, the verdict overload, the row-20 specimen, and the "HALF
FIXED" correction were all caught by the project's own out-of-frame audits before
"done" was claimed, and stand narrated in the artifacts rather than sanitized.

## What this asks of you

Nothing urgently. The decision-shaped item (a second trust domain, or a written
acceptance of the single-domain limit) is the standing Tier-3 question from the prior
assessment, unchanged in content but now confirmed as the single load-bearing wall by
five independent lenses — it deserves an answer at your leisure, not today. The
mechanical residue is tracked (`apparatus-flip-witnessing`, `panel-cheap-fixes`) and
Sonnet-executable. The one-line summary you asked the re-litigation to produce: **the
prior "not yet" was mostly arming and calendar; what remains is one decision and a
short list of small mechanisms, and the design substance itself was judged adoptable
in principle by the majority of a panel instructed to be hostile.**
