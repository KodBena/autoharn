# ADR-0002: Fail Loudly

*In plain words first: this is the project's fail-loudly tenet. When code hits a bad
config, an unexpected shape, a timeout, or any other deviation from what it expects, the
rule is to say so clearly — raise, fail a build or test, log visibly — rather than quietly
limping on, guessing, or hiding the problem behind a plausible-looking default. It binds
every module in a hosting project that could otherwise let such a failure pass silently.*

> *Refactored for cross-project portability on 2026-07-13 under
> [`design/MAINT-ADR-PORTABILITY-SPEC.md`](../../design/MAINT-ADR-PORTABILITY-SPEC.md)
> (tracker `adr-portability-refactor`, maintainer-ratified 2026-07-13). The pre-refactor
> text stands verbatim at commit `ff691bb9bc430ad497d74ff82d580f758a969f99`; extracted
> records live under [`history/`](history/) (each **Extraction Pointer** — a bolded
> "Extracted record" blockquote below, the pointer-with-summary convention
> [history/README.md](history/README.md) defines — names its own
> destination file) and are not retro-edited. Dated amendments below are preserved
> verbatim from the original. The
> Genre and Scope fields below are re-instanced generically at this same act (spec §4); the
> pre-refactor wording (which named this project's own filing path and package) is the git
> history at the commit above, not silently lost. The Provenance field, by contrast, is a
> preserved dated record the spec forbids rewording, so it keeps two source-project proper
> names; for the zero-context reader (the field is frozen, positional reference is safe):
> the first project it names is the ancestor whose ADR corpus this tenet was transferred
> from, not otherwise referenced here; the second is the source project the original
> instance list was re-derived against — the same project this ADR's `history/`
> extractions describe. The artifacts the field names in passing (an "AZ stack", an
> "hp registry", "env/scenario seams") are that source project's subsystems, a shorthand
> a reader of this corpus is not expected to know — where they recur in the preserved
> prose below, read them as the source-project instances the Context's extracted record
> summarizes.*

- **Status:** Accepted
- **Genre:** Tenet (cross-cutting principle) — as distinct from ADR-0001,
  which was a specific technical decision. Tenets guide future decisions;
  decisions resolve specific questions. Both are filed under `law/adr/`
  for single-location retrieval.
- **Date:** 2026-06-15
- **Provenance:** Transferred from the LengYue ADR corpus (this project forks
  that corpus's authoring discipline). The tenet is universal and transfers
  wholesale; the instance list is re-derived against [chocofarm](../../GLOSSARY.md#omega-and-chocofarm)'s real
  surfaces (the env/scenario seams, the parallel executor, the hp registry,
  the AZ — AlphaZero-style search/training — stack). chocofarm's code **already cites this ADR by number** — 16+
  `ADR-0002` invocations across seven modules and the tests — so this
  document is the registry those citations point at. It must exist and match
  their intent. (Before this ADR existed, the 2026-06-15 audit named those
  citations "a binding convention with no definition"; this ADR closes that
  gap.)
- **Scope:** Codebase-wide — every module in the hosting project that
  surfaces a deviation through a loud channel is an instance. The source
  project's own instance list (an env's config validation, a parallel
  executor's bounded-drain refusal, a hyperparameter registry's
  restart-only-field drift refusal (the same instance the Context's extracted
  record below describes), a weights loader's shape checks, a precision guard)
  is preserved in the Context's extracted record below; an adopting project
  re-derives its own instance list against its real surfaces, the same move
  [ADR-0009](0009-performance-investigation-discipline.md) models for this corpus.

## Context

During the buildup of this project, many small and large decisions have
shared one hidden dependency: they each resolve an ambiguity between "try to
handle this anomaly gracefully" and "make the anomaly visible and stop." In
every such case the project has chosen visibility, and has been better off
for it. The pattern has enough weight to be worth naming, so future decisions
don't have to re-derive it.

> **Extracted record — the six fail-loud examples**
> *(moved verbatim to [history/0002-chocofarm-fail-loud-substrate.md](history/0002-chocofarm-fail-loud-substrate.md))*:
> six dated decisions from this tenet's source project each turned a potential silent
> failure into a loud one at a specific point in the hierarchy below — a permanent
> parallel-worker deadlock converted to a diagnosable exception naming the phase/run/
> iteration; a hyperparameter registry refusing a drifted restart-only field by name
> rather than running on an invalid config; an environment's config validation raising
> on a malformed shape/range instead of silently truncating; a weights loader failing at
> load on a dimension mismatch instead of deep in the first forward pass; an unrecognised
> precision request raising instead of silently falling back; and a bounded-state
> enumeration aborting loudly rather than hanging or exhausting memory. Each instance
> names the module it lives in and the loudness level it fired at — the corpus's own
> worked proof that the hierarchy below is not aspirational. The shorthand instance
> names that recur in the hierarchy and rules below (the shape checks at load, the
> registry strict decode, the drain RuntimeError, the wedge diagnostics (a "wedge" is a
> stuck/deadlocked worker process; the diagnostic dumps its state), the
> live-compute fallback, and rung 2's jax/numpy bit-equivalence and scenario-validation
> tests) are these same source-project instances, preserved as the
> original text's worked anchors.

The common thread: **when the system has a choice between "recover quietly"
and "fail audibly," prefer audibly.** Silent failures accumulate into debt
that is discovered late — often as a wrong number in a research result, or a
corrupted checkpoint, or a metric that silently misreports.

## Decision

**We adopt "Fail Loudly" as a codebase-wide tenet.** When the system
encounters a condition that deviates from its stated invariants — unexpected
shapes, timeouts, config drift, missing resources, failed transport,
violated numerical assumptions — it surfaces the deviation through the
loudest appropriate channel, not papers over it.

### The hierarchy of loudness

Loudness is not binary. From strongest to weakest:

1. **Import/construction-time error** (the program refuses to start with a
   bad config). This is the strongest rung: the anomaly never reaches a run. It is
   preferred where the invariant is knowable at setup — the AZ (AlphaZero-style
   search/training) stack's shape checks at load, the dtype guard.
2. **Test/build-time error** (a test fails). This rung is nearly as strong for
   runtime paths whose invariants the type system can't capture — the jax/numpy
   bit-equivalence test, the scenario validation tests.
3. **Runtime exception** (raises and halts the current operation). This rung is
   strong: it breaks the offending path clearly rather than continuing in an
   undefined state — the parallel-drain RuntimeError, the env config `ValueError`s,
   the registry refusals.
4. **Logged warning / surfaced diagnostic** (faulthandler dump, a named
   log line). This rung is visible to whoever runs or inspects the process, and it
   is appropriate for "this shouldn't happen, but the run can continue" — the worker
   faulthandler + SIGUSR1 wedge diagnostics (a "wedge" is a stuck/deadlocked process;
   the diagnostic dumps its state rather than aborting it outright).
5. **Silent fallback or default.** This is the lowest rung. It is appropriate only
   when the fallback genuinely is the right answer (e.g. `env.d`'s live-compute
   fallback for a coord pair absent from the precomputed table — the
   fallback is bit-identical to the table, so it is not a coercion).

*(Amended 2026-07-13 — see the dated Amendment below: a rung named
**build/compile-time error**, ranking immediately below rung 1 and immediately
above rung 2, was added to this hierarchy per §7 C8's adjudicated
resolution.)*

The tenet: **reach for the strongest level that fits the anomaly, not the
weakest that's expedient.**

### Concrete rules

The tenet above cashes out as six checkable rules:

1. **No automatic retry / silent fallback for operations that could
   indicate a genuine problem.** Timeouts, failed transport, a config the
   process could not validate: surface them. (Transient socket-level
   behavior bounded by an explicit timeout is not "automatic retry" in this
   sense; it is the bound that makes a stall loud.)
2. **Validate at boundaries; do not coerce.** The hp registry strict-decodes
   the config blob and refuses a malformed one rather than filling missing
   fields with defaults; the source project's env validators likewise raise
   on wrong-length or out-of-range config rather than truncating (the
   specific validators are named in the extracted record the Context's
   Extraction Pointer above links). A boundary translates and checks; it
   does not guess.
3. **Sentinel-return-instead-of-raise is a red flag** and requires
   justification. Prefer raising, or a value whose "absent" case is
   distinguishable from a legitimate empty result. A silently-returned wrong
   number is the worst case on a research codebase, because it surfaces as a
   plausible result.
4. **A config field that the receiver cannot honor must not be silently
   accepted.** The source project's audit — the same 2026-06-15 architectural audit named
   in Provenance above, here examined for code-level lying signatures rather than citation
   hygiene — found three "lying signatures" —
   functions whose accepted parameters the body silently ignored (the three
   specific signatures are preserved in the extracted record the Context's
   Extraction Pointer above links) —
   the same failure in the parameter register: a seam that looks configured
   but is dead. Honor it or delete it (this is the subject of
   [ADR-0011](0011-mechanization-discipline.md) Rule 6's lineage and of the
   source audit's lying-signature finding, preserved in the extracted record
   the Context's Extraction Pointer above links).
5. **No silent state-mutation that breaks an invariant.** The float32 cache
   coherence ([ADR-0001](0001-immutability-and-copy-on-write.md)) is a
   fail-loud-adjacent invariant: a rebind keeps
   the cache honest; an in-place mutation that didn't bump the signature
   would silently serve stale weights, which is exactly the silent failure
   this tenet forbids.
6. **A derived value frozen as a literal that feeds a result is a latent
   silent failure.** A quantity that is *derived* from a live source must be
   computed at its point of use, never hand-copied as a literal that can
   drift from that source — and a test that pins the frozen literal
   compounds the failure by *forbidding* the legitimate retune that should
   update it.

> **Extracted record — the reference-rate drift trace**
> *(moved verbatim to [history/0002-chocofarm-fail-loud-substrate.md](history/0002-chocofarm-fail-loud-substrate.md))*:
> the source project's audit found exactly this drift already live between two
> hardcoded copies of one derived rate, one of them a numerical input to a provable
> bound — a concrete case of "latent, not yet realized" turning real.

### What counts as "loud enough"

A deviation is surfaced loudly enough when a developer running the code, or
an operator inspecting it, sees that something went wrong (a raised
exception, a failed test, a named log line, a refusal to proceed), or when
the anomaly is recorded retrievably. It is **not** loud enough when the
system guesses what the caller "probably meant," retries invisibly, returns
a sentinel indistinguishable from a legitimate result, or logs a warning
nobody will see.

## Consequences

### Positive

- **Failures surface on the timescale of development, not of a wrong
  result.** A shape mismatch that raises at load costs minutes; the same
  mismatch surfacing weeks later as "the residual block was never trained"
  costs a research direction.
- **The codebase becomes self-documenting about its invariants.** Every
  fail-loud raise, every strict decode, every shape check is a tiny record
  of what the code expects. The 16+ `ADR-0002` citations are lane markings.
- **The parallel substrate's correctness story is honest.** Because the
  source project's deadlock path fails loud, its test suite can assert the
  abort fires — a smaller but truthful guarantee than a silent hang would
  allow.

### Negative

- **Slightly more verbose code.** A function that raises on malformed input
  is longer than one that returns a default. The justifying comments are
  lines that wouldn't exist without the tenet.
- **The tenet is a policy, not (mostly) a mechanism.** A lazy bare `except:`
  will run fine; only review catches it. *Partially mechanized:* the source
  project's config validation, registry strict decode, load-time shape
  checks, and precision guard (the Context's extracted record enumerates
  them) are tests/raises at `error`-equivalent strength; the
  judgment calls (is this fallback honest? is this sentinel justified?)
  remain review's. [ADR-0011](0011-mechanization-discipline.md)
  (mechanization discipline) is where the enforcement-surface declaration
  for each rule lives.

### Neutral

- **The tenet does not prescribe implementation details.** It says "fail
  loud"; it doesn't say "always raise." The right mechanism depends on the
  level in the loudness hierarchy that fits — a construction-time raise for a
  config error, a faulthandler dump for a wedge diagnostic.

## Exceptions

Some places deliberately do not fail loud. Documented so the tenet isn't
misapplied.

### Bit-identical structural fallbacks

A live-compute fallback that is provably bit-identical to a precomputed lookup — because
both were built from the same inputs and the same formula — is not a coercion; it keeps the
contract total without ever hiding a wrong answer. Rule of thumb: **a fallback that provably
returns the same value as the primary path is not a silent failure.**

> **Extracted record — the distance-table instance**
> *(moved verbatim to [history/0002-chocofarm-fail-loud-substrate.md](history/0002-chocofarm-fail-loud-substrate.md))*:
> the source project's worked case is a distance-table lookup that falls back to a live
> recompute using the identical formula the table was built from.

### Idempotent / no-op-when-already-done operations

A teardown that runs twice, a registry-seeding step that no-ops when its target already
exists (a resume flag re-binding rather than clobbering operator overrides), a cache
rebuild skipped when the signature is unchanged — these are idempotence guarantees, not
failures. Rule of thumb: **idempotence is not silent failure; it is an invariant being
preserved.**

> **Extracted record — the registry-seeding instance**
> *(moved verbatim to [history/0002-chocofarm-fail-loud-substrate.md](history/0002-chocofarm-fail-loud-substrate.md))*:
> the source project's registry-seeding step no-ops when its blob already exists, and its
> resume flag re-binds rather than clobbering operator overrides.

### Bounded, scheduled-for-removal compat shims

A defensive fallback during a bounded transition is acceptable **if** the alternative
would produce a failure the operator cannot action, and **if** it is commented as bounded
and scheduled.

> **Extracted record — the core-pinning fail-soft instance**
> *(moved verbatim to [history/0002-chocofarm-fail-loud-substrate.md](history/0002-chocofarm-fail-loud-substrate.md))*:
> the source project's worker core-pinning fails soft to a default index while its
> process-name-scraping approach is replaced — the source audit flags this specific
> instance as a band-aid to remove, not a permanent exception, not an example of the
> exception being misused generally.

## What this tenet does NOT mean

- **Not "crash on any anomaly."** A missing optional field is not
  crash-worthy; a missing required field might be.
- **Not "refuse to handle edge cases."** Edge cases get handled — visibly,
  not silently.
- **Not "spam the logs."** The loudness hierarchy is graded; most anomalies
  are developer/operator-level, not result-level.
- **Not "fail on a bounded transient."** A socket op bounded by an explicit
  timeout that succeeds on its budget is not a failure at our layer.

## Revisit when…

1. **A rule of this tenet gains a mechanical guard** (a lint, a CI gate, a
   schema constraint). Record the mechanization here by dated append — the
   enforcement level is part of a rule's meaning (ADR-0011 Rule 1). The hp
   registry's strict-decode constraints are the first such instance.
2. **A new surface emerges where silent fallback genuinely is the right
   answer.** Add it to Exceptions alongside the three captured here.
3. **A structured error/telemetry layer is adopted** for the training runs.
   The loudness hierarchy may gain a level between log-line and raise, and
   the rules may need updating.

## Related

- **[ADR-0001](0001-immutability-and-copy-on-write.md) (immutability and
  copy-on-write).** The copy-on-write seams and the rebind-not-mutate cache
  invariant are applications of this tenet — they raise at boundaries and
  keep a coherence invariant that, if violated silently, is exactly the
  failure this tenet forbids.
- **[ADR-0004](0004-minimal-touch-edits-to-partially-visible-files.md)
  (minimal-touch).** The authoring-side counterpart: ADR-0002 says "fail
  audibly at runtime"; ADR-0004 says "don't introduce changes a later run
  will be the first to discover."
- **[ADR-0008](0008-classification-discipline.md) (classification discipline).**
  The proactive sibling, same failure family, different intervention point: this
  tenet's loudness hierarchy above is the **reactive** register — it surfaces a
  deviation once it has already occurred; ADR-0008's positive register (refuse a fuzzy
  vocabulary match) and negative register (refuse a fabricated category) are the
  **proactive** register — they refuse the deviation before it forms. ADR-0008's
  substitution test (calibrate severity to the worst-case surface, not the observed
  cost) is the classification-time counterpart of this tenet's Rule 3 (don't
  sentinel-return a plausible-looking wrong answer): both refuse to let the
  cheapest-looking instance of a failure shape set the bar for how seriously it is
  treated.
- **[ADR-0009](0009-performance-investigation-discipline.md) (performance
  investigation discipline).** The per-domain instance for perf claims — an
  unsubstantiated "faster" is the silent failure this tenet names, in the
  perf-claim register.
- **ADR-0002 applies to documentation consumption.** The root `CLAUDE.md`
  records the gravest sin against this tenet for an LLM collaborator: citing
  a document one has not read in full. Surfacing the gap audibly is the only
  correct move.

## Amendments

### Amendment — 2026-07-13: the loudness hierarchy gains a build/compile-time rung (§7 C8)

*(Dated append per [ADR-0005](0005-documentation-discipline.md) (documentation discipline)
Rule 8, executed under
[`design/MAINT-ADR-PORTABILITY-SPEC.md`](../../design/MAINT-ADR-PORTABILITY-SPEC.md) §7 C8 —
that linked section records the maintainer's 2026-07-13 adjudication (in the project's own
internal decision record, cited there as "ledger row 403"; this document does not depend on
that internal record resolving, only on the linked spec section, which states the outcome in
full): the spec's PROPOSED resolution stands as the default. This is the companion half of
the same contradiction's resolution
to [ADR-0011](0011-mechanization-discipline.md)'s
[2026-07-13 vocabulary amendment](0011-mechanization-discipline.md#amendment--2026-07-13-rule-1s-enforcement-vocabulary-gains-a-buildcompile-time-member-7-c8):
that amendment executed the ADR-0011 half of the same finding and explicitly routed this
half back for separate dispatch, because its own work package's commission touched only
ADR-0011 and its history/ files — naming the gap rather than silently leaving it undone or
duplicating the other document's work. Provenance of the finding: the spec's full-corpus
contradiction read found that [ADR-0012](0012-compositional-and-structural-hygiene.md) —
whose Decision section states its rules as nine numbered principles labeled P1 through P9,
the "P" labels this Amendment cites — ranks, in
[P7 (cross-language wire discipline)](0012-compositional-and-structural-hygiene.md#p7--cross-language-wire-discipline-the-new-material),
"generate-or-compile-from-one-source > **build-time lint** > runtime parity", and asserts,
in rule 5 of
[P9 (functional core, imperative shell)](0012-compositional-and-structural-hygiene.md#p9--functional-core-imperative-shell-the-compiled-component-contract),
"**compile-time** > runtime in
the loudness hierarchy P5 defers to" (P5 is 0012's "fail loud; remove the root cause"
principle) — but neither build-time-lint nor compile-time was
nameable as a rung of the hierarchy above, which named only "Test/build-time error (a test
fails)" at its second position: this corpus's most-cited structural tenet was enforcing at
a level its own loudness hierarchy could not name.)*

The hierarchy above gains a rung, **build/compile-time error**, ranking immediately below
rung 1 (import/construction-time) and immediately above the existing rung 2 (test/build-time
error): a check that fails the build itself, before the artifact exists to run or test at
all — a build-time lint that fails on a cross-language format disagreement (ADR-0012 P7), a
`constexpr`/`consteval` assertion, a `[[nodiscard]]` return treated as a compile error
(ADR-0012 P9 rule 5), or a codegen step that would not compile if its one source and its
generated output disagreed. It out-ranks the existing rung 2's "a test fails": a
build/compile-time failure forecloses the defective artifact from ever being produced,
where a test/CI gate catches it only after the artifact already exists and the suite runs
against it — the same ordering [ADR-0011](0011-mechanization-discipline.md)'s companion
amendment gives its own enforcement-surface vocabulary.

This is a **fail-safe, additive class-ratified delta** in the sense of
[CLAUDE.md](../../CLAUDE.md)'s "class-ratified fail-safe deltas" ruling: it only *adds* a
rung to the hierarchy, relaxing no existing rung and weakening no existing rule — every
prior citation of rung 1 ("Import/construction-time error") or the existing rung 2
("Test/build-time error") remains exactly as strong as it was. Per [ADR-0005](0005-documentation-discipline.md) Rule 8, the
numbered hierarchy in the Decision section above is not retro-edited to insert or renumber
an entry; this Amendment names the new rung's rank by relation to the existing two instead.
A rule that already declared rung 1 or the existing rung 2 is unaffected; a check whose true
enforcement was always build/compile-time (ADR-0012 P7's build-time lint, P9's
`[[nodiscard]]`) now has the honest word for it in this tenet's own hierarchy, closing the
naming gap C8 found rather than inventing new obligation.

*Enforcement surface: this amendment is itself review-only — it is a vocabulary-naming act,
not a new check. The gap it closes (a hierarchy citing a level it could not name) is closed
by naming, not by adding machinery.*

## License

Public Domain (The Unlicense).

<!-- doc-attest-exempt: mechanical, content-preserving edit (usability review, ledger row 1180, 2026-07-23, finding 16) -- the single existing word "chocofarm" at its first plain-text mention in this file was wrapped in a markdown link to GLOSSARY.md#omega-and-chocofarm (the Stand-Alone Principle's own first-use-link requirement, GLOSSARY.md#stand-alone-principle, applied here for the first time). No other character in this file changed; the rule content this ADR states is untouched. This mechanical class of edit is authorized by the maintainer's vested-judgment commission for this round (ledger row 1180), not a semantic change to law/ requiring further ceremony. Removal condition: strike this marker and run the real A:B:C loop next time this file is touched for its actual rule content, not just a link wrap. -->
