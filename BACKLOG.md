# autoharn — informal backlog

Provisional and informal. This file exists because the structured work-log store (#3 — the SQL SSOT for
work status) does not exist yet. When it does, these items migrate there and this file retires. Until then:
a plain, append-friendly list of live threads, so nothing is lost to memory.

---

## Design principles to hold (rationale, not tasks)

- **Forward-compatibility / composability is a first-class design constraint.** We will not get any
  taxonomy exhaustive on the first try — we are not even sure what "exhaustive" means for some of these
  yet — so every schema must evolve **additively**: new study designs, capability kinds, obligations, and
  measurement/analysis dimensions can be added **without breaking existing data or downstream consumers**.
  Concretely:
  - `jsonb` escape-hatches for not-yet-modelled structure (e.g. `reading.config`);
  - closed-vocabulary enums that are only ever **widened**, never narrowed (ADR-0008 stays MECE by adding
    cells, not by re-bucketing);
  - generic dimensions (`project_id`, and — if it earns its place — a unit/subject-of-observation
    dimension) over baked-in assumptions;
  - schema-per-store namespacing (`core` / `research` / `registry` / `work`) so stores **compose** rather
    than entangle.
  Rationale: forward-compatibility is the generic justification for composable software, and it is far
  cheaper to leave the seam than to retrofit it. *(Shoehorned in deliberately, per the maintainer.)*

---

## Conundrums

Open problems with no known mechanism yet — the things that, left unsolved, cap what the project can
deliver. Listed so they aren't forgotten; each wants an ADR-0011 mechanism we don't have.

### C1 — Detecting laziness-informed judgements (the "do-less" ambiguity)

**The problem.** An LLM's recommendation to do LESS — defer, omit, "leave a seam", "keep it minimal", "out
of scope" — is surface-indistinguishable from genuinely-informed restraint. Every time one appears, the
maintainer must ask: informed judgement, or laziness wearing discipline's clothes? For LLM-leveraged
workflows this is pervasive and first-class: unexamined, it silently lowers the ceiling on everything. It is
the same shape as the deflation cascade (the auditor that acquitted) and SPEC-ADEQ (the adequacy of a
judgement can't be checked from inside the LLM layer).

**Discriminator (proposed, partial).** Laziness = UNDIFFERENTIATED minimisation justified by an
UNFALSIFIABLE discipline-word ("minimal", "proportionate", "enough"). Informed restraint = DIFFERENTIATED
calls under a FALSIFIABLE criterion that sometimes points toward MORE. Test: does the "do-less" set come
with a "do-MORE-here" set under the same stated criterion? *Worked example:* the 2026-06-28 taxonomy second
opinion passes — it pulled `observed_at` out to must-fix-now *because deferring is lossy* (a checkable
property); laziness would have flattened to "defer all". Its soft spot is the scope call ("don't build
study-design machinery") — defensible judgement, not a falsifiable property: the human-judgement residual.

**Seed mechanism (what we have).** The hack-rationalization-detector: force every "do-less" to expose (a)
the more-general fix it set aside and (b) a CONCRETE COST that justified setting it aside — a discipline-word
is not a cost. A judgement naming no concrete cost is presumptively lazy.

**Open (no ADR-0011 mechanism yet).** Generalise from code-fixes to ALL judgements: every defer/omit carries
`{criterion, evidence, kill-condition}` as structured data a gate can check. The hard part: keep the
detector MECHANICAL or human-rooted — an LLM judging an LLM's laziness shares the bias and deflates (proven
this session). Likely partially-mechanisable (raise the cost of a lazy judgement by forcing a falsifiable
discriminator), with an irreducible human residual on adequacy.

### C2 (no comment, behold)
```
● That's a genuinely strong, skeptical review — and it sharpens your instinct rather than just agreeing. Let me read the current daemon lines so I can add the ACL markers precisely, then build the gate:

  Read 1 file

● The second opinion's verdict is clear and I'll act on the uncontroversial parts now: keep fp32 (reject .half()), add the single-homed-boundary markers, fix the silent-degradation flag (make a failed cast fatal, not swallowed), and build
  a proportionate gate. Let me apply the daemon changes:

● Now the gate itself — a proportionate, pure-AST single-homing check (no baseline ratchet, per the second opinion's "port the discipline, not the machinery"):

```
1. Proportionate under what model?
2. How does one reason with NLP + logic tools when the claude sentences are staccato? It's simply not sufficient to rely on single sentence analyses. The first example even implies so many things that need scruty
    * "your instinct" (what is my instinct)
    * "sharpens" (why?)
    * "the second opinion's verdict is clear" (what is the verdict)
    * "will act on uncontroversial parts" (what is uncontroversial, why, and according to whom?)
    * "that's a genuinely strong, skeptical review" (and if it weren't, would you notice? what standards do you hold when you assert this?)
---

## Research-ledger taxonomy — second-opinion findings (ADR-0014, 2026-06-28)

Verdict: keep the EPISTEMIC core verbatim (measurement⊥interpretation, immutable readings, derived
confirmation, growing warrant). Fix the over-claim + one lossy trap; leave cheap additive seams; do NOT
build empirical-study-design machinery into autoharn (consumer concern — confirms the maintainer's instinct).

**MUST-FIX-NOW**
- `observed_at` (lossy if deferred): no column for WHEN an observation occurred; `created_at` is
  trigger-locked to ingest time, so v0-era data can never recover observation time. Add nullable
  writer-supplied `observed_at`; keep `created_at` as the ingest/ordering clock; exempt it from the trigger.
- Honest scope/name: the header claims a generic "research/measurement ledger" but delivers a
  software-benchmark-run provenance ledger — the label is wider than the thing (ADR-0008 over-claim; the
  false-authority pattern at the naming level). Retitle/scope honestly; arbitrary study design = out of scope.

**LEAVE-A-SEAM-NOW (cheap, additive)**
- non-numeric outcomes: `value` nullable + `value_text`/`value_json` (findings are often contrasts: A>B, pass/fail, rank).
- `reading.git_commit` nullable (provenance, not identity) so non-software data needn't forge one.
- unit/**subject-of-observation** identity: nullable `subject_id` (the panel/longitudinal seam).
- **finding → set of readings** (hardest to undo): future `research.finding_evidence(finding_id, reading_id, role)`
  join. *Lead's pushback on the reviewer:* keep `finding.reading_id` as a NOT-NULL **primary** reading + add
  the join for additional evidence, rather than nullable-now (avoids evidence-less findings). Maintainer decides.
- `instrument.kind` non-MECE (harness⊂script; survey/sensor/sim/human absent) — note now so it isn't read as
  authoritative; split into orthogonal **modality** × **role** axes later.

**FINE-AS-IS / later (additive):** `qualification`/`status` enums; the epistemic core; omit panel/RCT machinery;
later entities — study/experiment grouping, analysis/transformation, dataset.

---

## Deferred increments — research ledger

- **increment 2:** `research.reproduction` + the reproducer service ⇒ add the **INDEP** conjunct to the
  `finding_confirmed` warrant.
- **increment 2:** `research.prereg` (+ conclusion) ⇒ add the **criterion-before-result (RECORD)** conjunct.
- **AUTH:** who may write / qualify (a write-authority model) — not yet modelled.
- DB-stamp `finding`/`instrument` `created_at` if their ordering ever becomes load-bearing.
- Decide read-vs-apply-vs-commit path for `001_research_ledger.sql` (validate against a *scratch* Postgres
  first; it has not been executed).

---

## Stores & services to build

- **store #2 — capability registry** (toolset availability / schema / registration): pull-not-push;
  `probe_cmd`/`derive_cmd` not literals; the `proves` column as the eliciting mechanism. The reproducer is
  a registered, qualified capability here.
- **store #3 — structured work-log / backlog** (port omega `work-status`; + `project_id`/`session_id`) —
  *this file's successor and SSOT.*
- **the reproducer service** (clone → rewind → rebuild → rerun; qualified; the independent verifier that
  gates confirmation). Itself a registered capability; leaves the seam for SLSA/in-toto attestation.

---

## Doc / tooling

- **Abbreviation attribution + scope** in the doc-legibility gate: a term carries an *origin* and a
  *scope*; a project-scoped term used out of scope is a violation. (Would have caught `tlab_*` in autoharn.)
- **Check the survey render scripts into the repo.** `KEY.md` is generated by an ephemeral scratch script
  that would clobber edits on re-run — a COHERE / reproducibility smell.
- **Run every new subsystem design against the 19 obligations** before building (the checklist mechanism;
  it is the doc, not a gate, until wired).
- Decide the **agent-push policy** enforcement: keep as remembered convention, or wire a settings.json hook
  (background agents commit-only; humans push `main`).

## Research threads

- **Investigate "attitude logic."** Is there a named formalism under this term — logics of
  *propositional attitudes* (belief / desire / intention; doxastic / epistemic / BDI) — and should
  this project address it? Directly germane to the real goal: interrogating an AI collaborator's
  *epistemic state* is reasoning over its attitudes toward propositions (what it believes, hedges,
  intends, defers). Map it against the obligations-formalisms survey. [maintainer request, 2026-06-29]
