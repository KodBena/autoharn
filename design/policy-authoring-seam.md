# The policy-authoring seam — ephemeral workflows under durable law (Fable, session 7be3443d, 2026-07-07, withdrawal hours)

Companion to the work-unit-authorization BACKLOG item (the may/3 ASP design). That item
settled WHERE policy lives (derived judgments over a versioned, sha-anchored rules file).
This note settles HOW policies get AUTHORED — the maintainer's question: the substrate is
right but arcane; how do flexible/ephemeral/throwaway workflow constraints get expressed
without either watering down the rigor or requiring every author to write raw ASP?
Options considered: (1) documentation, (2) bespoke DSL, (3) LLM encodes on the fly,
(4) admixture. The recommendation is a structured admixture; each ingredient below.

## The governing observation

The friction budget is a SAFETY parameter, not a convenience one: if instantiating a
compliant one-off policy costs more than routing around the system, people route around
it, and the record stops reflecting reality — the censored-record failure produced by UX.
So the design goal is: the COMMON case costs seconds, the NOVEL case costs exactly its
novelty, and no case is allowed to cost zero verification.

## 1. A ratified pattern library, not a rulebook (the core)

The recurring constraint shapes are few and already specimen-proven in this project's own
history: SoD (reviewer ≠ author — row 7's class), delegate-without-execute (finder may
spawn a fixer, may not fix), scope-disjoint parallelism (parallel_safe via declared
file/db scopes), review-before-merge, attestation-before-eviction (DTO §1.5),
stamp-distinct independence. Each becomes a PARAMETERIZED ASP TEMPLATE ratified at
foreclosure grade: template text + its positive AND negative control fixtures (specimen
acts that MUST be admitted and MUST be refused — seen-red applied to policy) + a one-line
teaching description. A pattern without banked controls is prose, not policy — the same
line the foreclosure ledger draws for gates.

## 2. Instantiation is DATA, not a language (option 2, dissolved)

The bespoke-DSL trap: a second syntax whose compiler is a new unverified seam, whose
semantics drift from the ASP it targets, and which ossifies at yesterday's patterns —
heavy cost, standing maintenance, and it re-introduces the translation gap the project
exists to close. But observe what a DSL invocation would actually SAY: "pattern X with
parameters Y over scope Z." That is a ROW, not a sentence. So instantiation is an INSERT:

    policy_instance(instance_id, pattern_id, params_json, unit_scope, expiry)

- Ephemeral = run-scoped or TTL'd rows; the policy dies with the run.
- Auditable for free: the instantiation is itself a ledgered act with an actor.
- No compiler: the ASP layer joins policy_instance against the ratified templates —
  grounding, not translation. The single semantic SSOT stays ASP.
- Composable: a workflow's policy is a SET of instance rows; conflicts between instances
  are themselves derivable judgments (the engine can say "instances 3 and 7 cannot both
  hold over unit U" — policy contradictions surface the same way spec contradictions do).

## 3. The LLM authors only the novel remainder, gated (option 3, fenced)

For constraints no pattern covers, the LLM writes raw ASP — but LLM-authored policy is a
CLAIM, and claims need acts. The gate, mandatory and mechanical:

- Every novel rule ships with PRE-REGISTERED CONTROL CASES, both polarities: acts it must
  admit, acts it must refuse. Rule + controls are sha-anchored together (acts.ruling);
  controls run green/red in a fixture before the policy arms. An unproven rule never
  gates a live run.
- High-stakes novel rules additionally get the ADVERSARIAL PRE-TEST (the e16 §1.4
  machinery, reused verbatim): N fresh finder contexts prompted "find an act sequence
  this policy admits that violates the stated intent — argue the strongest case," banked
  transcripts, iterate until N consecutive failures. The policy analog of the level-field
  proof.
- PROMOTION PATH (measure-once-then-mechanize, applied to policy): a novel rule that
  recurs across runs is a pattern the library is missing — ratify it in (template +
  controls + docs) so its next use is a row, not authorship. The library grows by
  specimen, exactly like the foreclosure catalog.

## 4. Documentation is the floor, not the answer (option 1, scoped)

ASP stays the single place semantics live, so it must be READABLE: each template's file
carries its teaching description, its controls double as executable examples, and the
doc-legibility gate covers the pattern docs. But documentation prevents no mis-encoding;
it is the floor under options 2/3, never the mechanism.

## The worked silly example ("Mr. Bigwig visits; demonstrate at highest rigor")

A ceremonial one-off is the EASY case under this design, not a special one: compose
existing patterns at maximum strictness — instance rows for SoD-everywhere,
stamp-distinct independence required, review-before-merge, full acts differential at
close — in seconds, because every ingredient is ratified. Any genuinely bespoke flourish
("the visitor's name appears as a co-observer on the close manifest") is one novel rule +
two control cases, LLM-drafted, fixture-proven, sha-anchored, minutes. The whole policy
set expires with the demo run. And the deep property: EPHEMERAL POLICY, DURABLE AUDIT —
the instance rows, anchors, controls, and every act they governed persist, so the
throwaway demo is exactly as auditable as production. Which is, presumably, the point of
demonstrating to Mr. Bigwig at all: the rigor IS the feather-polish, at no marginal cost,
because it is the default.

## What this deliberately does not do

No new syntax, no compiler, no per-policy migrations, no trusted-LLM policy authorship,
no free-form ASP as the common path. The flexibility lives in composition and parameters
(cheap, checkable); the trust lives in ratified templates and banked controls (slow,
deliberate); the LLM sits exactly where this project always puts it — at the flexible
seam, generating claims the machinery verifies.
