# ADR-0011: Mechanization Discipline

- **Status:** Proposed
- **Genre:** Tenet (cross-cutting corrective-design discipline) — the eighth
  in this corpus's numbered sequence of cross-cutting tenets (ADR-0002,
  ADR-0004 through ADR-0009, and ADR-0011 through ADR-0014; the ADR files
  themselves are the only index of the sequence). Rule 1 is the enforcement
  register of the ADR-0002 / ADR-0008 / ADR-0009 unsubstantiated-claim family
  (an enforcement level is a claim about a discipline, and it must be
  declared, not implied); Rules 2–4 are corrective-design protocol adjacent
  to that family.
- **Date:** 2026-06-15 (original); refactored for portability 2026-07-13 (below).
- **Provenance:** The tenet — disciplines declare their enforcement surface; a
  recurrence converts to a mechanism, not more prose; a net quantifies over the
  class, not the instance — is universal. It has transferred once already: from
  a browser-tooling project's own RCA and lint-adoption history, onto a
  numpy/JAX/numba research codebase's own architectural audit, whose entire
  diagnosis is the second project's form of the first project's "prose
  disciplines decay, mechanisms stick." See the Extracted records below for
  both prior substrates' full detail, kept as dated evidence; a hosting
  project's own mechanism instances are re-derived as its real ones, never
  copied from either prior substrate.
- **Scope:** Corrective design and discipline authoring across a project's own
  codebase and its docs corpus — the moments when a discipline is authored or
  amended, and when a corrective responds to a recurrence. A hosting
  deployment's own package name is not load-bearing to this tenet's rules.

*This ADR was refactored for cross-project portability on 2026-07-13 under
[`design/MAINT-ADR-PORTABILITY-SPEC.md`](../../design/MAINT-ADR-PORTABILITY-SPEC.md)
(tracker `adr-portability-refactor`, maintainer-ratified 2026-07-13). The
pre-refactor text stands verbatim at commit `cce9272`; extracted records live in
[`history/0011-chocofarm-context.md`](history/0011-chocofarm-context.md) and
[`history/0011-throughput-lab-amendments.md`](history/0011-throughput-lab-amendments.md)
and are not retro-edited. This pass also executes the enforcement-vocabulary
amendment Rule 1 was missing, per this refactor's own §7 C8
(maintainer-adjudicated 2026-07-13, ledger row 403 — spec default stands): see
the dated 2026-07-13 Amendment below. Dated amendments below are preserved
verbatim from the original.*

## Context

*In plain words first: this ADR is a rule for anyone authoring or amending a project's own
rules, lints, or checks — it requires each such rule to state plainly how it will be enforced
(a raise at construction, a test, a runtime check, or "review only, for now"), and it gives the
vocabulary for saying so, so that "review-only" is a visible, challengeable choice rather than
a silent default.*

A discipline-stating rule enforced only by one contributor's attention and
memory is structurally weak against the **invisible-at-authoring,
visible-only-in-aggregate defect** — a failure shape that looks fine at each
site it is authored and shows up only once instances accumulate. Prose
disciplines decay for exactly this reason: a convention cited repeatedly with
no registry to check it against, a design document that quietly goes stale
while the code it describes moves on, a duplicated fact whose two copies drift
apart one edit at a time. The tenet+mechanism pairing — never the describing
document alone — is what arrests recurrence: a mechanism keyed on the class (a
single owned computation, a fail-loud structural check) removes the defect
where it is applied; where the discipline stays prose only, the rot returns.

> **Extracted record — the originating audit substrate and the FeatureLayout worked proof**
> *(moved verbatim to [`history/0011-chocofarm-context.md`](history/0011-chocofarm-context.md))*:
> a 2026-06-15 architectural audit of this tenet's originating codebase diagnosed the pattern
> from both directions — a convention cited sixteen times with no registry to look it up in,
> and a numeric anchor that had already drifted from its sibling copy before anyone noticed.
> Its sharpest instance was a three-writer single-source-of-truth violation (a feature-layout
> table duplicated across three files) that a reorder would have silently mislabeled;
> converting it into one owned, by-name-addressed table with a fail-loud contiguous-partition
> check is the worked proof this tenet generalizes from — the mechanism removed the hazard the
> describing audit could only name.

## Decision

We adopt **Mechanization Discipline** as a codebase-wide tenet, in four rules.

### Rule 1 — Disciplines declare their enforcement surface

Every discipline-stating rule — an ADR rule, a CLAUDE.md convention, a
docstring contract — names how it is enforced, against this vocabulary
(related explicitly to ADR-0002's loudness hierarchy; the choice among them is
part of the rule's meaning):

- **construction/import-time** (a raise at setup; a strict schema decode — the
  originating codebase's `hp` (hyperparameter) registry's `decode_config`);
- **test/CI gate** (a test at `assert` strength — the jax/numpy equivalence
  test, the scenario-validation tests, the deadlock test);
- **write-time data constraint** (a schema/dataclass invariant that refuses a
  malformed write — the same `hp` registry's `hp/schema.py`'s `check_invariants`);
- **run-time invariant** (a structural check at use — `FeatureLayout`'s
  contiguous-partition assertion; the f32-cache identity check of ADR-0001);
- **review-only**.

*(Amended 2026-07-13 — see the dated Amendment below: a sixth member,
**build/compile-time**, was added to this vocabulary per §7 C8's adjudicated
resolution.)*

Review-only is legitimate but presumptively decaying — declaring it makes that
a visible, challengeable choice. Across this corpus, the "discipline is policy,
not mechanism" Negative bullets in ADR-0003 through ADR-0009 are this rule's
pre-existing instances: each declares review-only and names the trigger that
would mechanize it.

*Neutral scoping (no retroactive sweep):* declarations bind when a discipline
is authored or amended and at corrective-design moments; existing rules
retrofit on touch (ADR-0004 / ADR-0006).

### Rule 2 — Recurrence converts to mechanism, not more prose

When a failure shape recurs after its describing record exists, the
corrective names the mechanism it pairs with the rule — at the strongest
*feasible and proportionate* surface in Rule 1's vocabulary — or carries an
explicit policy-only admission and the trigger that would change it. "Tenet +
mechanism arrests recurrence; a describing-only document does not" is the
cited rationale (the `FeatureLayout` worked proof; the originating audit's own
findings — see the Extracted record under Context), not an
unconditional build-a-gate mandate. This tenet's originating audit roadmap is
this rule's own worked register (the audit's own numbered remediation
list — see the Extracted record under Context for its substrate, and note
these three items name internal objects of that originating codebase — `env`,
its simulation-state object, and `belief`, the probability estimate `env`
tracks over hidden state — not portable vocabulary this tenet itself defines):
a duplicated numeric reference rate recurs as a drift → `BeliefRefs(env)` (one
owner, item R3 on that list); a duplicated belief-computation that a
correctness bound depends on → `env.restrict` sharing one implementation
(item R8); an identity-keyed cache tied to the wrong lifetime →
`env.slot_tables` owned on the object (item R9). Each is a mechanism the
corrective names, not a prose "be careful."

### Rule 3 — Mechanisms adopt measure-first

A mechanism is adopted against a measured baseline, not an assumed one. Before
a check goes to `error`/`assert` strength, the existing tree is measured (the
audit ran the live env to find `realizable_static = 0.08553` /
`clairvoyant = 0.14537` and so demoted a "your metric is wrong now" claim to
"latent, one value-vector change away" — measure-first caught the
overstatement). A check at full strength lands only on a zero-or-fully-triaged
baseline; the equivalence tests are the worked instance — `ABS_TOL = 1e-4` was
chosen "comfortably above the observed" float error, a measured threshold, not
a guessed one. Where a paid-for defect exists, probe-verify the net fires on
its literal shape (the audit reproduced `max|Δp| = 0.0082` to confirm the
stale-weight hazard the f32-cache invariant guards).

### Rule 4 — Nets quantify over the class, not the instance

Enumerations of instances fail open at the next instance. A net keys on a
structural slot, a name/shape predicate, or a derived-from-one-source
invariant. The originating worked instances (see the Extracted record under
Context for their substrate):

- **`FeatureLayout`** keys on the ordered block *table* (the class of feature
  blocks), so a new block is one table entry and every consumer slices by name
  — a reorder edits one structure and cannot silently mislabel. The old
  three-writer enumeration failed open at exactly the next reorder.
- **The param-registry-driven net serializer** (`parallel.py`'s
  `pack_net`/`unpack_net`) enumerates the weight set from the net's own
  `_params()`, so an optional residual block transports with no second edit
  site — derive-don't-duplicate, a net over the class of params.
- **The contiguous-partition assertion** in `FeatureLayout` quantifies over
  *every* position (no gap, no overlap), not over a list of expected blocks.

Conversely, the audit's `it + 1_000_000` version offset is the failure this
rule names — a magic disambiguator that silently breaks at iters ≥ 1e6,
because it enumerated a case rather than namespacing the class (the fix:
namespace weight keys by `(run, phase, version)`, item R14 on the same
numbered remediation list cited above).

## Self-application

This tenet binds at corrective-design moments — audit recommendations, a new
mechanism's adoption, an ADR amendment — a handful of high-attention events,
not the per-edit regime where prose decays. Its own Rule-1 declaration
**is review-only**, with the audit serving as the absence-detector. No CI sweep detects a
discipline-stating rule lacking an enforcement declaration; the originating
audit (see the Extracted record under Context) is that detector, run on
demand. The protection this tenet offers is the mechanisms it mints
(`FeatureLayout`, `BeliefRefs`, the equivalence tests), not its own prose —
the tenet expects its own prose to be exactly as weak as Rule 1 says, which is
why it names its mechanisms rather than relying on the rule text.

## Consequences

**Positive.** Enforcement levels become legible per discipline — a reader (and
a future fork author, who inherits the tree's mechanisms but not the
maintainer's memory) can distinguish mechanism-policed from memory-policed
without archaeology. Correctives stop defaulting to the measured-decaying
prose form; the audit's R-series is overwhelmingly mechanisms, not notes.

**Negative.** Per-corrective authoring overhead (the assessment +
declaration); the risk of cargo-cult mechanisms is real — a check at full
strength on an un-triaged baseline is worse than none (Rule 3 is the
counterweight). This tenet has no automated enforcement of itself; it is
review-and-audit-policed.

**Neutral.** No retroactive sweep (Rule 1's scoping clause); existing
mechanisms are not re-litigated.

## Revisit when…

1. A mechanism is retracted on false-positive economics — record the
   retraction here; Rule 3's calibration may need a rule.
2. A doc-side resolution check (does every cited path resolve?) matures — the
   advisory rung gains a member; reassess the vocabulary (this is also
   ADR-0005's Revisit #2).
3. A second instance of the class of project this corpus originated in — an
   Operations-Research or game-playing/search codebase — adopts the corpus
   (ADR-0003's own trigger, phrased there as "OR/game instance") — the
   enforcement-surface declarations are the transfer manifest; check each
   discipline's mechanism survived the re-instantiation.

## Related

- **ADR-0002 (fail loudly).** The Rule-1 vocabulary maps onto ADR-0002's
  loudness hierarchy at the enforcement level. The `FeatureLayout` partition
  check and the registry strict decode are fail-loud mechanisms.
- **ADR-0008 (classification discipline).** Rule 1's vocabulary is a closed
  vocabulary under ADR-0008's care; extending it follows the
  revise-don't-fuzzy-match discipline — the 2026-07-13 Amendment below is a
  worked instance of that discipline in force.
- **ADR-0009 (perf investigation discipline).** The sibling per-domain
  instance of the unsubstantiated-claim family; Rule 3's measured baselines
  are the enforcement-domain analog of its captured benches.
- **The originating architectural audit** (see the Extracted record under
  Context) — the worked register of Rule 2 (recurrence → mechanism); its
  worked mechanism proof anchors Rule 4's quantify-over-the-class instances;
  its measure-first deflation is Rule 3's origin.

## Amendments

> **Extracted record — the two 2026-06-24 throughput-lab amendments**
> *(moved verbatim to
> [`history/0011-throughput-lab-amendments.md`](history/0011-throughput-lab-amendments.md))*:
> two dated amendments extended this tenet onto a C++/Python transport-throughput testbed,
> both worked instances of Rule 2 (recurrence → mechanism) and Rule 4 (a net over the class).
> The first: an unreproducible "+31%" throughput reading could not be pinned to the code that
> produced it, so the measuring harness now stamps every reading with its producing commit's
> hash and clean/dirty tree state, unconditionally — a captured reading is attributable by
> construction, never by someone remembering to label it. The second: a project's own
> perf-investigation journal had been recording *interpretations* of measurements (mutable,
> frequently revised beliefs) as free-text prose indistinguishable from the *measurements*
> themselves — one retracted "+31%" belief had motivated banking a wrong default — so the
> belief layer moved into a separate, append-only, typed store (a finding supersedes a prior
> finding; it never overwrites it), structurally separating a measurement from what someone
> concluded from it.

### Amendment — 2026-07-02: Rule 2's trigger at the life-critical bar: the mechanism ships WITH the first fix

*(Provenance: the fact-mining recidivism study. Measured: across three blind
passes, prose obligations read in full recurred at a false-clear rate of
0.105 and a persistence count of 4; the classes that stayed closed are the
ones whose fix carried a mechanical gate (ZMQ_MAXMSGSIZE at bind; the
compile-count gate; `tools/no_lazy_imports.py`, which found 169 standing
violations of a prose law three read-in-full passes had left in place).)*

Rule 2 converts a recurrence to a mechanism. Its trigger — *"when a failure
shape recurs after its describing record exists"* — is calibrated for one
long-lived contributor whose memory persists between occurrences. The study
proved the regime it fails in: **serial independent executors**, each reading
the same law fresh, each granted one free recurrence before the conversion
fires — so the corpus pays a full pass per class to learn what Rule 2 already
knew. Therefore, in any codebase or component declared to a life-critical /
standing-service bar, the trigger tightens: **the mechanism is minted with
the FIRST fix.** A defect-class foreclosure is not complete until the check
that would catch its recurrence exists at the strongest
feasible-and-proportionate surface — the foreclosure test is part of the
fix's definition of done, not a later conversion awaiting a second
occurrence. A fix shipped without its net is, at this bar, the "describing
record" whose decay Rule 2 was written against.

### Amendment — 2026-07-02: Rule 3 extended: a gate proves itself by failing (negative control + shipped binding), and the enforcement machinery is in-scope code

*(Provenance: CB-33 — the study's load-bearing compile-bound/streaming gates
were green while measuring a NON-SHIPPED encode backend; the shipped default
path was never exercised, so the invariants were unverified on the artifact
actually served. And the provenance stamper — this corpus's own auditability
mechanism — corrupted files containing its marker and mis-attributed runs
before being fixed three times (`e787ccb`, `9902c18`, `5d2ef21`).)*

Rule 3's probe-verify clause gains two mandatory legs, without which a gate's
green is not evidence:

- **Negative control.** A gate is demonstrated to FAIL on the defect shape it
  guards — on the pre-fix tree, a mutated artifact, or a synthetic violation
  — before its pass is credited. A gate never seen red is a claim, not a net.
  (The corpus already runs this where it is honest: the host-device lint's
  mutation self-check; `test_wire_drift.py` leg 2. This makes it a rule.)
- **Shipped binding.** A gate exercises the configuration, backend, and code
  path **actually shipped as default** — or is parametrized over every
  shipped variant. A gate green on a seam production never touches verifies
  nothing (CB-33), and is worse than no gate: it launders the claim.

And the scope clarification the stamper history forces: **enforcement
machinery is code under this law.** Hooks, stampers, lints, CI harnesses,
workflow instruments — the mechanisms this tenet mints — obey ADR-0002 (fail
loudly, never corrupt what they touch), ADR-0000 (a defect in a gate gets the
two questions), and this Rule 3 (a gate is measured before it is trusted).
A net with holes catches nothing and reports otherwise.

### Amendment — 2026-07-13: Rule 1's enforcement vocabulary gains a build/compile-time member (§7 C8)

*(Dated append per ADR-0005 Rule 8, executed under
[`design/MAINT-ADR-PORTABILITY-SPEC.md`](../../design/MAINT-ADR-PORTABILITY-SPEC.md) §7 C8
— adjudicated by the maintainer 2026-07-13, ledger row 403: the spec's PROPOSED resolution
stands as the default. Provenance of the finding: the spec's full-corpus contradiction read
found that
[ADR-0012 (compositional and structural hygiene)](0012-compositional-and-structural-hygiene.md)
— whose nine numbered principles P1–P9 are that document's own section labels — ranks, in its
P7, "generate-or-compile-from-one-source > **build-time lint** >
runtime parity", and in its P9 rule 5 asserts "**compile-time** > runtime in the loudness hierarchy
P5 defers to" — but neither *build-time-lint* nor *compile-time* was a rung in this Rule's
vocabulary or in ADR-0002's loudness hierarchy: this corpus's most-cited structural tenet was
enforcing at a level its own enforcement vocabulary could not name.)*

Rule 1's closed vocabulary gains a sixth member:

- **build/compile-time** — a check that fails the build itself, before the artifact exists to
  run or test: a build-time lint that fails on a cross-language format disagreement (ADR-0012
  P7), a `constexpr`/`consteval` assertion, a `[[nodiscard]]` return treated as a compile
  error (ADR-0012 P9 rule 5), a codegen step that would not compile if its one source and its
  generated output disagreed. It sits strictly above **test/CI gate** in the surface a rule may
  declare, because a build-time failure forecloses the defective artifact from ever being
  produced, where a test/CI gate catches it only after the artifact exists and the suite runs.

This is a **fail-safe, additive class-ratified delta** in the sense of
[CLAUDE.md](../../CLAUDE.md)'s "class-ratified fail-safe deltas" ruling: it only *adds* a
vocabulary member, relaxing no existing rung and weakening no existing rule — every prior
declaration against the five-member vocabulary remains exactly as strong as it was. A rule
that already declared **test/CI gate** or **construction/import-time** is unaffected; a rule
whose true enforcement was always build/compile-time (ADR-0012 P7's build-time lint, P9's
`[[nodiscard]]`) now has the honest word for it, closing the naming gap C8 found rather than
inventing new obligation.

*Enforcement surface: this amendment is itself review-only — it is a vocabulary-naming act,
not a new check. The gap it closes (a rule enforcing at a level its own vocabulary could not
name) is closed by naming, not by adding machinery.*

*Companion note, scope-honest: [§7 C8](../../design/MAINT-ADR-PORTABILITY-SPEC.md) also
proposes ADR-0002's own loudness hierarchy gain the same rung "by the same dated amendment."
That companion edit to ADR-0002 is **out of this package's scope** (this work package touches
only ADR-0011 and the history/ files its own extraction creates) and is not executed here —
flagged for separate dispatch, not silently done or silently dropped.*

## License

Public Domain (The Unlicense).
