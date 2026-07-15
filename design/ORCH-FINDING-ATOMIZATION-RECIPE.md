# Finding atomization — split narrative findings into atomic units before classifying them

<!-- doc-attest-exempt: v1.1.3 release-cut mechanical edit (de-linked dangling references into paths excluded from this public cut -- observatory/, research/foundational-map/, design/MAINT-PG-HBA-HARDENING.md -- plain-text citation, no prose rewrite), same disposition as the v1.0/v1.1/v1.1.1/v1.1.2 cuts' own markers on their touched files. Removal condition: strike this marker and run the real A:B:C loop next time this file is touched for content, not just link repair. -->

Audience: anyone running a diagnostic or audit pass that produces a list of findings destined
for classification — a defensive code audit turning up a batch of bugs to triage and fix, a
document or process review sorting observations into categories, or a taxonomy of work items
this repository's own `./led` (this repository's own append-only work-item tracker) will consume.
The method below is use-case-agnostic: it reads the same whether "finding" means a bug an
auditor found in a codebase or an observation a reviewer found in a document. This page answers
one question: **how do you keep "does every finding have a category, and does no finding sit in
two categories" a cheap, mechanical check instead of a recurring manual sweep?** The answer is a
two-stage method: atomize narrative findings into single-actionable-unit atoms first, check
coverage and exclusivity over the atoms mechanically, then re-cluster the atoms into
fix-authorship blocks second. Read this before triaging a batch of findings from a code audit,
a review, or any other diagnostic pass, or if a classification pass keeps needing a fresh manual
sweep to confirm it is complete and non-overlapping.

**Provenance and adjudication.** This recipe is harvested from a document authored inside the
`ent` deployment (`/home/bork/ent`, a separate downstream project this repository's own harness
scaffolds and observes — read-only from this repository's side, never written to), dated
2026-07-13 and titled `FINDING-ATOMIZATION.md`, written during a defensive code audit (a security/
correctness sweep producing bug findings, not a research or documentation pass). The commissioning
ask required this repository's own corpus to be cross-checked before serving anything, so the
source is not merely copied: the "Adjudication" section immediately below is that cross-check, run
against this repository's own law and design corpus, and it reaches an independent verdict rather
than assuming the source document's framing is correct. The method itself is rewritten here for
legibility — the source document's own author described it as convoluted — with its substance
preserved; nothing in the "The method" section below is invented, only re-expressed.

## Adjudication: genuinely new, with two named relatives

Three homes in this corpus were checked as candidates for "this is already covered here," and
none of them state the atomize-then-classify staging this recipe describes:

- **[ADR-0008 (classification discipline)](../law/adr/0008-classification-discipline.md).**
  ADR-0008 governs whether a *value chosen from a vocabulary* honestly fits (refuse a fuzzy
  match; refuse to fabricate a category under ambiguity). It says nothing about the *shape of
  the things being classified* — it has no notion that a "finding" arriving from a narrative
  audit pass might bundle several unrelated actionable units (several distinct bugs described as
  one observation), and no coverage/exclusivity check of its own. ADR-0008 is the correct
  discipline for choosing which category an atomic unit belongs to; it does not tell you how to
  get atomic units in the first place. Adjacent, not covering.
- **[ORCH-SPEC-DECOMPOSITION-POLICY.md](ORCH-SPEC-DECOMPOSITION-POLICY.md) and
  [ORCH-SPEC-TASK-TAXONOMY.md](ORCH-SPEC-TASK-TAXONOMY.md).** These specs govern splitting a
  *work item* for *execution assignment* — one acceptance criterion per task, one boundary per
  task, independently witnessable completion — and a declared taxonomy for policing which agent
  may touch which files. They assume the set of tasks already exists; they say nothing about how
  to derive that set from a batch of narrative findings, and nothing about a provenance graph or
  a mechanical partition check over the input findings themselves. Adjacent (both are about
  splitting work into checkable units), not covering.
- **[design/ORCH-COSIGN-CONVENTION-CROSSCHECK.md](ORCH-COSIGN-CONVENTION-CROSSCHECK.md)** and
  **observatory/ent/cycle-003.md (internal audit record, not part of this public release)** were checked as the nearest
  prior art from the same `ent` deployment and the same week: cycle-003 records a concrete episode
  this recipe's method would apply to directly (93 findings from a prior audit pass, reduced by
  hand into a 23-task taxonomy over several review rounds — see its §6 "CYCLE NARRATIVE"), but
  neither document names atomization, a provenance graph, or a two-grain atoms-then-blocks
  pipeline anywhere in its own text. The cosign crosscheck's own METHOD CANDIDATE was a different
  convention (an iterate-to-approval review loop) and was separately adjudicated already-covered;
  it is unrelated to this one beyond sharing a source deployment and a document shape to imitate.

What the corpus DOES already contain, and what this recipe explicitly composes with rather than
restates, are two structural relatives — the first of which is first-class, not incidental:

- **[ADR-0000 (type-driven design)](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md),
  Rule 2(a) and its 2026-07-02 amendment — the closest relative in the corpus.** Rule 2(a)
  requires that when a defect is identified, the first move is to name the failure in its most
  general form and ask what type or typing discipline would make the whole class unrepresentable
  — never to patch the one instance in view. Its 2026-07-02 amendment sharpens this into a
  **closure statement** with three named parts (the invariant; the quantification universe,
  enumerated, with deliberate omissions named; the denomination check) and inverts the
  presumption: a newly-named class is presumed too narrow and is checked outward — against every
  sibling axis and every sibling surface — before its fix is authored. This recipe's **block**
  grain (Stage 2 below) is exactly ADR-0000 Rule 2(a) applied one level further than code: instead
  of clustering *lines of code* under one type, it clusters *already-atomized findings* under one
  shared invariant, and authors ONE typed fix that forecloses the whole class — consolidating
  what would otherwise be N separate instance-by-instance patches into the single durable
  protection ADR-0000 already demands for any defect. Read narrowly, ADR-0000 already requires
  this shape for a single bug once its class is named; this recipe's contribution is the
  bookkeeping layer *underneath* that requirement — how to get from a raw batch of narrative
  findings to well-formed, coverage-checked, non-overlapping classes in the first place, so that
  ADR-0000's per-class typed-fix discipline has honest classes to apply to. That bookkeeping layer
  — atomization, the provenance graph, the mechanical partition check — is not stated anywhere in
  ADR-0000's own text, which is why the verdict below stays genuinely new rather than
  already-covered: ADR-0000 is the reason the block grain looks the way it does, not a document
  that already describes this recipe.
- **[ADR-0011 (mechanization discipline)](../law/adr/0011-mechanization-discipline.md), Rule 2 and
  Rule 4.** ADR-0011's whole thesis — a recurring verification converts to a mechanism that
  quantifies over the class, not an instance-by-instance manual check — is the general principle
  this recipe's atom-grain partition check is one instance of. ADR-0011 is the parent principle;
  it does not itself describe findings, atomization, or provenance graphs, so it does not cover
  this recipe either.

**Verdict: genuinely new.** No existing document states the atomize-before-classify staging, the
graph-shaped provenance/apply-order representation, or the two-grain atoms/blocks split — even
after re-reading ADR-0000 specifically for this question, at the maintainer's request, with the
"is the block grain just ADR-0000 2(a) already?" framing held directly in view. ADR-0000 supplies
the *reason* the block grain must cluster on a shared invariant and author one typed fix rather
than patching instances; it does not supply the *staged pipeline* (atomize → mechanically check →
recluster) this recipe adds underneath that requirement. It is served below as its own recipe,
composing with ADR-0000 and ADR-0011 rather than duplicating either.

## The method

### The problem this solves

A diagnostic or audit pass — a defensive code audit, a security sweep, a code review, an
architecture review — naturally produces *narrative* findings: an auditor notices a pattern
spanning several call sites or several distinct bugs and writes it up as one finding, because
that is how attention works, not because the underlying defects are actually entangled.
Classify those narrative findings directly — sort them into severity bands, bug classes, or
fix-owner buckets — and the categories stop being mutually exclusive: one finding legitimately
belongs to two classes at once, not because the classification is wrong, but because the finding
itself was never a single actionable unit (it was really two bugs described in one paragraph).
Every later review of the classification then has to re-check the whole set for gaps and
duplicates by hand, from scratch, because "did we cover every bug" and "does nothing overlap"
cannot be checked mechanically over units that are still bundles. Cycle-003's 93-finding batch
(cited above) is the concrete shape: a prior audit pass's raw findings had to be manually reduced
to a 23-task taxonomy over several review rounds before anyone could check the result for gaps.

### Stage 1 — atomize before classifying, and keep the provenance link

Before any finding is sorted into a category, split every narrative finding into its constituent
parts, at the granularity of one distinct actionable unit each — one bug, one call site, one
concrete defect. Record, for every atomic unit, a provenance link back to the observation it came
from — never leave that lineage implicit. Once every unit is atomic, the mapping from units to
categories becomes a strict partition by construction: each atomic unit belongs to exactly one
category, and "did we cover everything" / "does nothing overlap" degrade from a judgment-heavy
manual sweep into a one-line, deterministic set-equality-and-pairwise-disjointness check over the
unit dictionary.

This is the general mechanization principle from ADR-0011 (a recurring verification converts to a
cheap gate instead of repeated manual labor) applied one level up — to the bookkeeping of the
classification process itself, not to the underlying bugs the findings are about.

### Represent provenance and apply-order as a graph, not a list or a tree, from the start

Model both the provenance lineage (which observation(s) an atomic unit came from) and the
apply-order relation among the eventual fix-authorship blocks (below) as a graph from the
outset — a list or a tree is just the shape that representation happens to take when a given
unit's lineage or ordering happens to be simple, not a different structure earned by a different
case. Two situations make the generality earn its keep rather than sit unused:

- **Multi-parent provenance.** Whenever atomization runs as more than one pass — a second sweep
  independently rediscovers a bug a first sweep already atomized, and the two are later merged —
  that unit's lineage genuinely has more than one parent. A list or a tree cannot represent that
  without a special case; a graph represents it because it was graph-shaped from the start.
- **Apply-order among blocks.** When two fix-authorship blocks' patches touch overlapping code,
  read that overlap **first** as a signal that the shared ground implies a shared invariant and
  therefore a mis-cut classification boundary — the same reflex ADR-0000 already requires for
  any defect, applied here to the classification itself, before assuming it is merely a scheduling
  conflict. Only a dependency that survives that check — a genuine ordering fact between two
  blocks of confirmed-distinct classes — is recorded as an edge and topologically resolved before
  either block's patch is applied. A **cycle** in that graph is the identical signal in its
  sharpest form, not a separate or exceptional trigger: it still means a boundary was cut wrong,
  and remains a prompt to revisit the classification, never a scheduling problem to force through
  with an arbitrary tie-break.

### Stage 2 — reconstitute atoms into blocks; author fixes at the block grain, not the atomic grain

Atomization is not, by itself, the grain to author fixes against: the same underlying invariant
typically recurs across many separate atomic bugs, and fixing each one in isolation forfeits the
class-level foreclosure a durable fix requires — exactly ADR-0000 Rule 2(a)'s own instance-vs-class
distinction, and ADR-0011 Rule 4's "a net quantifies over the class, not the instance," both
applied here to grouping findings rather than grouping code paths. So the flat,
mechanically-verified atomic dictionary from Stage 1 gets clustered once more, upward, into
**blocks**: atomic units sharing an explicitly-stated invariant — named together with the specific
inputs it must range over and the concrete quantity its bound is derived from, never by mere
surface resemblance — become one block, and each block is the actual unit of independent
fix-authorship: one general design, one typed fix that forecloses the whole class, one
independently reviewable change. This is ADR-0000's closure-statement discipline (the invariant,
the quantification universe, the denomination check) doing the same job it always does — deciding
what a single typed fix must cover — with its input widened from "one code defect" to "a whole
cluster of already-atomized findings that share one root cause."

Each block's boundary, as first drawn, is presumed too narrow and checked outward — against
sibling inputs and sibling call sites the same invariant would also plausibly cover — before its
fix is authored, exactly as ADR-0000 already requires for any newly-named defect class.

**The two grains are not substitutes for each other; both are load-bearing.** The atomic grain is
what keeps coverage and exclusivity mechanically checkable (Stage 1). The block grain is what
keeps every fix scoped to the real defect class rather than patched bug-by-bug (Stage 2). Skip
Stage 1 and classification review reverts to a manual sweep every time. Skip Stage 2 and every fix
repeats itself once per atom that shares its invariant — the exact instance-patching ADR-0000
already forbids, arrived at here by omitting the reclustering step rather than by ignoring
ADR-0000 directly.

### Enforcement surfaces, named honestly

Following the enforcement-surface vocabulary
[ADR-0011 Rule 1](../law/adr/0011-mechanization-discipline.md) already declares for this corpus:

- **The partition/coverage/exclusivity check (Stage 1)** is a construction-time or CI gate: a
  set-equality and pairwise-disjointness test over the atomic-unit dictionary against the
  category assignment.
- **The provenance link and any apply-order edge** are a write-time constraint wherever the store
  carrying them has a schema to enforce one (a ledger row, a typed record) — not a convention left
  to a comment.
- **Whether the atomization itself was done correctly, whether a given category or block is a
  genuinely coherent grouping rather than a stretched label, and whether a block's invariant is
  real** all stay **review-only**, and are named as such rather than silently assumed to be
  covered by the mechanical checks above — exactly ADR-0011 Rule 1's honesty obligation. If one of
  these review-only judgments is later found to recur as a systematic failure, that specific
  recurrence is the trigger to convert it into its own gate (ADR-0011 Rule 2); it is not converted
  pre-emptively on the strength of this recipe alone.

## Related

- [law/adr/0000-the-alpha-and-the-omega-type-driven-design.md](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) —
  Rule 2(a)'s two-question reflex and its 2026-07-02 closure-statement amendment (invariant,
  quantification universe, denomination check; the presumption that a named class is too narrow
  until checked outward). Stage 2's block-clustering discipline is ADR-0000 Rule 2(a) applied one
  level further than code — clustering already-atomized findings under one shared invariant and
  authoring one typed fix, rather than clustering lines of code under one type. This is this
  recipe's closest relative in the corpus (see the Adjudication section above for why it does not
  make the recipe already-covered).
- [law/adr/0011-mechanization-discipline.md](../law/adr/0011-mechanization-discipline.md) — Rule 1's
  enforcement-surface vocabulary (reused above), Rule 2 (recurrence converts to mechanism, not more
  prose), and Rule 4 (a net quantifies over the class, not the instance) — the general principle
  Stage 1's partition check is one instance of.
- [law/adr/0008-classification-discipline.md](../law/adr/0008-classification-discipline.md) — the
  discipline that governs whether an *already-atomic* unit's chosen category is an honest fit;
  this recipe is upstream of it (atomize first, then apply ADR-0008 to each atom).
- [design/ORCH-SPEC-DECOMPOSITION-POLICY.md](ORCH-SPEC-DECOMPOSITION-POLICY.md) and
  [design/ORCH-SPEC-TASK-TAXONOMY.md](ORCH-SPEC-TASK-TAXONOMY.md) — the sibling disciplines for
  splitting an already-derived task set for execution and policing which agent may touch which
  file; adjacent to, and downstream of, this recipe's Stage 2 blocks once they exist as work items.
- [design/ORCH-COSIGN-CONVENTION-CROSSCHECK.md](ORCH-COSIGN-CONVENTION-CROSSCHECK.md) — the shape
  precedent this document's own "Adjudication" section follows (cross-check named candidate homes,
  state a verdict, name what the verdict does and does not claim), from the same source deployment
  and the same week, adjudicating a different, unrelated method candidate.
- observatory/ent/cycle-003.md (internal audit record, not part of this public release) §6 — the concrete 93-findings/
  23-task episode this recipe's method would apply to directly, cited above as the motivating
  scenario rather than as a prior statement of the method (it is not one).

## What this recipe does NOT claim

- **Not a claim that atomization is free.** Splitting narrative findings into atomic units and
  recording provenance is authoring work, done once per finding, traded against a mechanical check
  that then runs for free on every subsequent review. The trade is the point; it is not costless.
- **Not a mandate to atomize every finding regardless of scale.** A single, genuinely atomic
  finding — one bug, cleanly stated — needs no splitting; the method targets narrative findings
  that already bundle more than one actionable unit.
- **Not a substitute for ADR-0008.** This recipe governs getting to atomic units and honest
  fix-authorship blocks; which category an atomic unit belongs to, and whether that category
  itself is a fabricated or fuzzy fit, is still ADR-0008's discipline, applied per atom.
- **Not a substitute for ADR-0000, and not a re-derivation of it.** ADR-0000 already requires that
  a named defect class be foreclosed by one typed fix, checked outward against siblings, stated as
  a closure statement. This recipe does not restate or replace that requirement; it supplies the
  staged bookkeeping (atomize, mechanically partition-check, recluster) that gets a raw batch of
  narrative findings into the well-formed classes ADR-0000's per-class discipline then applies to.
- **Not self-certifying.** Per ADR-0011 Rule 1, this recipe names its own weakest points plainly:
  whether the atomization was done correctly and whether a block's invariant is real are
  review-only, not mechanized, and are not claimed to be anything stronger.
