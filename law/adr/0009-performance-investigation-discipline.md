# ADR-0009: Performance Investigation Discipline

<!-- doc-attest-exempt: doc-tree relocation mechanical edit (work item doc-tree-reorg-user-guide, ledger row 1620, 2026-07-18) -- relative link path(s) repointed to a sibling file's new location after a git-mv relocation elsewhere in the tree; no prose rewrite, same disposition as the v1.1.2 release-cut's own markers (commit 543a389). Removal condition: strike this marker and run the real A:B:C loop next time this file is touched for content, not just link repair. -->


- **Status:** Accepted
- **Genre:** Tenet (cross-cutting authoring discipline). Sibling of ADR-0008: same shape of
  unsubstantiated-claim failure, different domain — classification discipline forbids fuzzy
  vocabulary-fit; this tenet forbids unsubstantiated perf-fit ("this is faster," "this
  regressed," "no change," "behaviorally equivalent") against the closed vocabulary of perf
  and equivalence claims.
- **Date:** 2026-06-15 (original); re-instanced for autoharn 2026-07-12; refactored for
  portability 2026-07-13 (below).
- **Provenance:** The tenet is universal: a perf claim is honest only when its investigation
  is captured and reproducible. It has now transferred twice across hot-path substrates — a
  browser-tooling project's DevTools/profiler surface, then a numpy/JAX/ML search hot path —
  and each time only the **tool surface and metric vocabulary** changed, never the rule. See
  the Extracted records below for the two prior substrates' full detail, kept as dated
  evidence.
- **Scope:** All authoring work that asserts a performance or equivalence property — a
  speedup, a regression, a null result, or "the optimized path matches the baseline" — across
  a project's own experiment/investigation surface, and any perf or equivalence claim recorded
  in a project's research/decision record. Applies to any commit, tracker entry, or PR that
  lands a change to that surface and asserts it is faster, regressed, unchanged, or
  behaviorally/logically equivalent. A hosting deployment's own experiment surface — which
  files, which harnesses, which store — is named in its own **Instance bindings** section
  below, not here.

*Refactored for cross-project portability on 2026-07-13 under
[`design/MAINT-ADR-PORTABILITY-SPEC.md`](../../design/MAINT-ADR-PORTABILITY-SPEC.md)
(tracker `adr-portability-refactor`, maintainer-ratified
2026-07-13). The pre-refactor text stands verbatim at commit `ff691bb`; extracted records live
in [`history/0009-chocofarm-perf-discipline.md`](history/0009-chocofarm-perf-discipline.md) and
[`history/0009-autoharn-reinstancement-2026-07-12.md`](history/0009-autoharn-reinstancement-2026-07-12.md)
and are not retro-edited. This ADR is the corpus's own precedent for the whole refactor: its
2026-07-12 amendment already declared the prior body "illustrative history now, not this
project's binding surface" (preserved in the second history file above) — this pass completes
that declaration by physically relocating the prose the amendment had already disowned, and
rebuilding the document below from its spine, its generic two-tier calibration, and the
amendment's content as a first-class Instance-bindings section, in the shape
[ADR-0017](0017-the-zero-context-reader.md) already models (a portable core, a
non-portable "Instance bindings" section an adopter replaces wholesale).*

## Context

A perf-property or equivalence claim is a **closed-vocabulary claim** exactly in ADR-0008's
sense: "faster," "regressed," "no change," and "behaviorally equivalent" are not adjectives —
they are assertions against a specific, checkable bar, and the claim is honest only when its
substantiation is attached. Three failure modes recur wherever this tenet is missing:

- **A perf claim without a captured before/after.** "The optimized path is faster" with no
  timing evidence attached is the closest-match-selection failure ADR-0008's positive register
  forbids — a defensible-looking classification picked without verification.
- **An "equivalent" claim without the equivalence evidence.** "The optimized path matches" with
  no equivalence-harness result attached is the same failure in the equivalence register: a
  silent divergence an unrun check would miss.
- **Per-investigation tool re-derivation.** Each ad-hoc perf check re-deriving its own timing
  scaffolding and its own scenario. The cost compounds and comparability across investigations
  drops; a shared harness and a shared metric vocabulary exist precisely to prevent this.

The structural root is the one ADR-0002 names at the runtime level and ADR-0008 names at the
classification level: when a closed-vocabulary claim is made, it is honest only when its
substantiation is attached. This tenet is that root applied to the perf/equivalence register.
(The dated, first-person evidence this rule generalizes from — a two-tier bit-vs-behavioral
bar proven out on a real ML search hot path, and the specific failure modes it caught — is
preserved in full at the Extracted records below, not restated here.)

## Decision

We adopt **Performance Investigation Discipline** as a codebase-wide tenet. A perf-property or
equivalence claim — speedup, regression, null result, or "matches the baseline" — is honest
only when the investigation behind it is captured in a form the next reader can reproduce.

### Triggers — when to capture

1. **Before claiming a speedup landed.** A perf write-up or PR that asserts a hot-path change
   made something faster attaches the before/after numbers from a per-component timing harness
   (run on a representative, captured state) or a pinned end-to-end capture. Without the pair,
   the claim reduces to author intuition.
2. **Before claiming the optimized path is equivalent to the baseline.** A claim of "equivalent"
   attaches the equivalence evidence appropriate to the quantity's kind (see Calibration):
   exact assertion for a logic invariant, statistical-indistinguishability evidence for a
   float-/noise-sensitive numeric. "Equivalent" is a claim against the equivalence vocabulary
   and needs the same substantiation a speedup does.
3. **Before/after a structural refactor of a hot path.** A baseline capture before the refactor
   lands gives a reference point if a felt or measured regression surfaces later.

### Tools — what the discipline requires, generically

The discipline requires three kinds of capability, named generically here; a hosting
deployment's concrete tool names live in its own Instance-bindings section:

- **A per-component (or per-claim) timing/measurement harness**, run against a representative,
  reproducible input or scenario — so a speedup claim is validated one component at a time,
  before/after, and is never an artifact of end-to-end noise.
- **An equivalence-checking mechanism** appropriate to the domain: a numeric domain needs a
  statistical or tolerance-bounded comparator; a discrete/symbolic domain needs an exact
  comparator (see Calibration).
- **A reproducible input/scenario corpus** the measurements run against, so a capture does not
  depend on ambient run state and a later investigator can rerun it.

### Metric vocabulary

A canonical metric set lets investigations compare across time. At minimum, a project names:

- **A per-component or per-claim measurement comparable** (wall time, a rate, a cost) — the
  speedup comparable.
- **A behavioral-equivalence comparable** — a statistic (a rate, a mean, a distribution) with
  its measured uncertainty (standard error, confidence interval, or equivalent), reported so
  "indistinguishable" is a number, not an eyeball.
- **A bit-exact comparable, for logic invariants** — asserted exactly, never given a
  tolerance, and kept categorically distinct from the behavioral comparable above (see
  Calibration).

Additions to the vocabulary go here, in a project's own instance section, not scattered across
per-investigation write-ups.

### Acceptance criteria for perf/equivalence-claimed changes

- **Speedup claims** attach before/after numbers under the same reproducible scenario (same
  input corpus, same configuration, same seeds where applicable).
- **Equivalence claims** attach the two-tier evidence Calibration requires: the exact
  invariant check *and* the statistical/behavioral evidence, or a tighter bit-near-identity
  test where one is legitimately achievable.
- **Refactor PRs touching the hot path** attach the pre-refactor baseline.

The absence of substantiation does not block a change from landing — perf work proceeds at the
author's judgment — but the write-up **states the absence explicitly** rather than carrying an
unsubstantiated claim. The honest shape: *"defensively sound but not substantiated by a bench
pair; the speculative win is X, the cost is Y."* This is the loudly-marked unsubstantiated case
(parallel to ADR-0008's deliberately-imprecise tags), not a fuzzy-fit claim against the closed
vocabulary.

## Calibration on the two-tier bar

The bit-vs-behavioral distinction is the generic, portable calibration and must not collapse
in either direction:

- A **logic invariant** (a discrete/symbolic fact — "this set is exactly empty," "these two
  independently-derived verdicts agree") is a bit fact; asserting it with a tolerance is a
  category error — it is exact or it is a bug.
- A **numeric result** (a rate, a float-computed value, a measurement subject to noise) is a
  behavioral fact; asserting it bit-exactly is a category error in the other direction —
  legitimate re-implementation, re-ordering, or numeric-precision changes *will* move the
  value, so the honest bar is statistical indistinguishability within a reported uncertainty
  bound.

Confusing the two is the failure: pinning a noise-sensitive quantity bit-exactly forbids a
legitimate optimization — the ADR-0008 "fossil" failure in the perf register (a stale,
over-precise claim frozen against evidence that has since moved on) paired with its "fuzzy"
sibling (an imprecise claim picked without verification) — while relaxing a logic invariant to
a tolerance admits a real bug. The discipline is to apply the bar the quantity's *kind*
demands, never the bar that is merely convenient.

## Consequences

### Positive

- **Perf and equivalence claims are legible across time.** A write-up backed by a measurement
  reference is one a future investigator can extend; an unbacked claim is a dead end they
  must re-derive.
- **Substantiation cost is paid up-front.** Capturing the measurement during the work is
  cheaper than reconstructing the scenario later — composes with ADR-0005's author-as-you-decide.

### Negative

- **Per-claim authoring overhead.** Each perf/equivalence assertion carries "is this
  substantiated?" The answer must be "yes, evidence attached" or "no, explicitly marked
  unsubstantiated."
- **Discipline is policy, not mechanism.** No automated check verifies that a write-up's perf
  claim is backed by a referenced measurement (ADR-0011 Rule 1: a declared review-only
  surface; a scanner that flags perf/equivalence claim words — "faster," "regressed,"
  "equivalent" — lacking an attached measurement reference would be the mechanization trigger).
- **The behavioral bar needs enough samples to be meaningful.** A single noisy reading is not
  a substantiation; the sample size floor is a per-deployment instance decision.

### Neutral

- **No retroactive sweep.** Existing write-ups whose claims lack full evidence are not
  targeted for rewrite (ADR-0004's incremental-retrofit posture). The discipline operates at
  the moment of new authoring.
- **No mandate on a fixed benchmark suite.** New investigation classes may need new
  measurement tools; the tenet names the vocabulary and the requirement, not a frozen suite.

## Exceptions

### Structural-by-inspection wins

A change whose perf effect is provable by inspection — an asymptotic-complexity reduction at a
hot path, a redundant pass removed — does not require a measured pair. The structural argument
substantiates the claim; the write-up still names the argument. This parallels ADR-0002's
structurally-provable exception.

### Exploratory observations

A write-up may include exploratory perf observations made during investigation without
elevating them to the authoritative register ("I noticed X; needs a measurement before it's
load-bearing"). The discipline applies to the authoritative register, not the exploratory.

## Revisit when…

1. **A specific rule introduces its own failure mode.** Flag as the revisit trigger.
2. **A hosting deployment's hot path or tool surface changes.** The Instance-bindings section
   updates by dated amendment there; the tenet's spine and Calibration survive the
   substitution unchanged — as they already have, twice (see the Extracted records below).
3. **The metric vocabulary stops covering the perf-relevant axes.** A new investigation class
   that the existing metric set doesn't fit warrants extending the vocabulary in the instance
   section, not in a per-investigation write-up.
4. **A check can mechanize the substantiation requirement.** A scanner that verifies a
   perf-claim write-up references a measurement would partially mechanize the discipline
   (ADR-0011 Rule 1's enforcement-surface trigger).

## Related

- **ADR-0002 (fail loudly).** The reactive ancestor. An unsubstantiated perf or equivalence
  claim is the silent-failure shape ADR-0002 names, in the write-up authoring register.
- **ADR-0005 (documentation discipline).** Perf write-ups are documentation events;
  author-as-you-decide (Rule 6) is the temporal posture this tenet relies on for capturing the
  measurement during the investigation, not after.
- **ADR-0008 (classification discipline).** The proactive sibling. "Faster" / "regression" /
  "equivalent" are closed-vocabulary claims; substantiation is the vocabulary-fit verification
  ADR-0008 implies for the perf register.
- **ADR-0010 (this corpus's UI/render-locality-adjacent entry, where applicable).** A project
  with no UI hot path has no applicability there; this tenet is the nearest perf concern for
  such a project either way.
- **ADR-0012 P6 (substantiate equivalence/perf claims).** Composes directly and imports this
  tenet's two-tier bar wholesale rather than redefining it.

## Instance bindings (autoharn) — the non-portable section

Everything above is project-neutral. This section is autoharn's binding of the tenet to its
own machinery, re-instanced 2026-07-12 (maintainer-approved) and restated here as first-class
prose rather than a dated bracket-edit, per this refactor's own template; an adopting project
replaces this section wholesale with its own.

Autoharn does not have a machine-learning hot path to benchmark. Its experiment surface is (1)
a "kernel" — this project's append-only governance ledger and its Postgres schema, extended
over time by dated, versioned changes called a "lineage," each change a "delta," each delta's
application to a fresh copy of the schema an "apply" — whose apply time is a measurable perf
quantity; and (2) `./judge`, a check that computes the same verdict two independent ways (once
via the clingo/ASP logic engine, once via a plain SQL query) and compares them — an
equivalence claim in the sense this ADR disciplines.

- **Equivalence tool — `./judge` (the ASP/SQL differential).** This is autoharn's
  equivalence-harness analog and its two-tier bar reborn: every ledger verdict is derived
  independently via ASP (clingo) *and* SQL, and the two must agree. `AGREE` is the bit-exact
  tier (a discrete/symbolic verdict — no floating-point noise to tolerate, so agreement is
  exact or it is a defect, exactly Calibration's "logic invariant" case). `DIVERGE_BY_DESIGN`
  is a documented, expected divergence (the closed-form analog of a tolerance-banded
  behavioral case: named and substantiated, not silently accepted). `DIVERGE_DEFECT` /
  `QUARANTINED` are typed escalation events — a fixed, named category rather than free-text
  prose — meaning a real bug or an unsafe input, either way never silently patched around
  (composes with `engine/contemp_differential.py`'s QUARANTINE guard and, per Calibration,
  never relaxed to a tolerance). Diagnosis walkthrough:
  [`engine/docs/JUDGE-READING.md`](../../user-guide/JUDGE-READING.md).
- **Investigation-capture tool — `filing/record_reading.py` writing to
  [`stores/001_research_ledger.sql`](../../stores/001_research_ledger.sql).** Autoharn's
  captured-investigation-DB: a measurement
  (`research.reading`, immutable, frozen at write) is distinct from an interpretation drawn
  from it (`research.finding`, supersedable, `status ∈ {provisional, retracted}`) — the
  measured-vs-interpreted separation this tenet's honesty depends on, made structural.
  `research.finding_confirmed` derives confirmation from three conditions at once: a clean
  git tree, a qualified instrument (`research.instrument.qualification = 'qualified'` — a
  status a human sets, not a default), and a real session — never a writable field, so
  "confirmed" cannot be asserted, only earned.
- **No per-component before/after timing harness is built for autoharn's own hot paths**
  (kernel-lineage delta-apply time, `./audit` wall time, or the cost of scaffolding a "world" —
  this project's term for one isolated project habitat the harness sets up, "scaffold" being
  the act of setting one up) as of this writing. Per this ADR's own Exceptions ("Exploratory
  observations") and Acceptance criteria
  ("the absence of substantiation does not block a change... but states the absence
  explicitly"), a perf claim about autoharn's own hot paths is honest today only as an
  explicitly-marked exploratory observation — and per this project's standing prudential
  posture (a ledger work-item named `prudential-filed-candidates`: "build on witnessed
  need... not speculatively"), a dedicated timing harness is built when a real perf claim
  first needs one, not spun up now on spec.
- **Metric vocabulary, autoharn register.** Autoharn's own metric vocabulary consists of:
  verdict counts (`AGREE` / `DIVERGE_BY_DESIGN` /
  `DIVERGE_DEFECT` / `QUARANTINED` tallies from `./judge` — the equivalence comparable);
  contemporaneity verdict counts (the four verdicts `./audit` — this project's check that a
  ledger row was recorded close in time to the act it describes — can assign to a row:
  `CONTEMPORANEOUS`, `BATCHED_DECLARED`, `LATE_DECLARED`, `BACKFILL_SUSPECT`, a timeliness
  comparable with no upstream analog); and `value` / `stderr` / `n` recorded via
  `research.reading` (the behavioral comparable for a repeated, noisy measurement).

*Enforcement surface: review-only, same as the rest of this tenet — this section maps
vocabulary and tools; it mints no new mechanism (ADR-0011 Rule 1).*

## Extracted records

> **Extracted record — the chocofarm-era substrate (Context, Decision detail, Consequences,
> Exceptions, Revisit-when, Related, and the 2026-06-24 throughput-lab amendment)**
> *(moved verbatim to
> [`history/0009-chocofarm-perf-discipline.md`](history/0009-chocofarm-perf-discipline.md))*:
> this tenet transferred twice before autoharn — first from a browser-tooling project's
> DevTools/profiler surface, then onto a numpy/JAX/numba AlphaZero search codebase, whose bench
> harnesses (per-component timing, a behavioral-equivalence check, a forward bit-near-identity
> test) are the worked proof that the two-tier bit-vs-behavioral bar holds up on a real ML hot
> path. The failure modes it caught there — an unsubstantiated speedup claim, an unsubstantiated
> equivalence claim, and per-investigation tool re-derivation — are exactly the three this
> document's Context still names, now stated generically. A later amendment extended the same
> discipline onto a C++ transport-throughput testbed and added a captured-investigation
> Postgres store distinguishing an immutable reading from a supersedable finding — the same
> measured-vs-interpreted split autoharn's own Instance bindings above independently reaches for
> its research ledger.

> **Extracted record — the 2026-07-12 autoharn re-instancing amendment**
> *(moved verbatim to
> [`history/0009-autoharn-reinstancement-2026-07-12.md`](history/0009-autoharn-reinstancement-2026-07-12.md))*:
> the dated record of the maintainer-approved act that first re-instanced this ADR's Scope and
> Provenance from its prior substrate onto autoharn's own experiment surface (`./judge`, the
> research ledger), by an in-situ bracket-edit rather than the wholesale rewrite this refactor
> now performs. Its content is not superseded — it is the same mapping now stated as first-class
> prose in the Instance-bindings section above; this record is kept as the frozen evidence of
> when and how that re-instancing happened.

## License

Public Domain (The Unlicense).
