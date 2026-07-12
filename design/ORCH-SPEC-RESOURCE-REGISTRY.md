# The resource registry — Pillar 1, with obligation attachment and first-class ordering

Audience: orchestrator (secondary: maintainer — §2 tiers and §6 are his calls)

This document specifies the capability registry: how a project declares the resources
available to it (tools, solvers, services, backends), how an agent working in that
project is led to actually reach for them, and how mandated-tool disciplines are
enforced. It is written for the executor who builds from it and for the orchestrator who
stages the build. It merges two tracker items (pillar-1-resource-registry and
deontic-attachment-vocabulary) because they proved to be one design.

STATUS: Fable-authored spec, 2026-07-12, from four maintainer inputs of the same day,
each recorded as a decision row on autoharn's own root work tracker (run `./led --recent`
at the repository root to read them): the resource-declaration service; the obligation-
attachment reframe (the maintainer's answer to the review-gap scope ruling — he rejected
its binary framing in favor of a general attachment vocabulary; the superseded ruling is
[MAINT-REVIEW-GAP-SCOPE-SEMANTICS-RULING.md](MAINT-REVIEW-GAP-SCOPE-SEMANTICS-RULING.md),
and this document's §4 is what replaced it); first-class ordering constraints; and the
planning-substrate calibration. Implementation is staged for a Sonnet-class executor;
every stage is independently witnessable.

## 1. The problem (Pillar 1 of the founding design, unbuilt until now)

[GLOSSARY.md](../GLOSSARY.md) has named this since the project's first week, as
[Pillar 1](../GLOSSARY.md#pillar-1): a Capability Registry — "a queryable store the
agent pulls at point-of-need, listing every tool / service / venv / blessed method and
what each one proves, so the agent reaches for the provable tool by reflex." It was
never built. The living specimen of its absence: every recent commission file
hand-declares the QEUBO backend (a preference-optimization service this maintainer's
experiments run against), because there is nowhere structured to declare it once — and,
in the maintainer's words, "Claude typically doesn't ask" whether redis, or cvxpy, or a
SAT solver is sitting right there. The registry closes that: declaration is a ledger
act, discovery is a pickup section, and reaching-for-the-tool is a taught reflex keyed
by task shape.

## 2. Declaration — resource rows on the deployment's own ledger

A resource is declared where everything attributable lives: as a ledger row in the
deployment (world or standing project), never in an upstream autoharn file — the
maintainer's boundary-hygiene rule that autoharn is used like a library, so everything
an adopting project owns lands in that project. Version 1 uses the existing machinery
with a statement convention; a kernel schema change is deliberately deferred until the
convention shows what columns earn their place.

- Kind: `resource` — one additive vocabulary value, following exactly the precedent of
  lineage step s25, which added the `commission` kind (the sN tokens number the kernel's
  schema lineage steps; their record is kernel/lineage/README.md). Adding a vocabulary
  value is the pre-ratified fail-safe class of kernel change defined in
  [CLAUDE.md](../CLAUDE.md)'s ORCHESTRATION section (nothing existing relaxed, scratch-
  witnessed both ways), so it lands as lineage step s27 whenever stage 3 begins; until
  then, stage 1 uses `decision` rows with a `resource:` statement-prefix convention.
- Statement fields, in a fixed order the pickup view can parse: NAME; CLASS (solver |
  service | backend | binary | library); REACH (endpoint, binary path, venv, or import);
  WHAT-IT-PROVES (one clause — the eliciting hook: "feasibility → this", "auditable
  enumeration → this"); GUIDANCE (when to reach, when not); TIER (available | blessed:
  <task-shape> | mandated: <task-shape>).
- Declared by the commissioner or by the author citing the commission. The commissioner
  can sign the declaration with the commission-signing machinery — FULL mode (typed from
  his own terminal, proven by actor plus absent stamp) or SIGNED mode (a GPG detached
  signature over the text), both defined in
  [USER-GPG-TRUST-LAYER-FAQ.md](USER-GPG-TRUST-LAYER-FAQ.md) — and a mandated-tier
  declaration is commissioning-grade, so signing it is apt. Superseding a declaration is
  the ordinary supersedes edge; the registry view shows only unsuperseded rows.
- The canonical residents for this maintainer's projects, from his own enumeration:
  MIP (SCIP), cvxpy, OR-Tools, Z3, clingo (already the house engine), tsort, redis,
  and per-project backends such as QEUBO. The scaffold seeds NOTHING by default — an
  empty registry is honest; a template registry file the maintainer edits at adoption
  is the offered convenience.

## 3. The pull surface — pickup section + the eliciting preamble line

- `./pickup` gains a RESOURCES section: the unsuperseded declarations, tier-sorted,
  mandated first. A session hydrates with the resource map in the same read as the work
  items — [pull-not-push](../GLOSSARY.md#pull-not-push) satisfied at the same choke
  point everything else uses.
- The world/project preamble gains the eliciting line: "Before choosing tools for a
  task, read the RESOURCES section. If the task's shape matches a blessed or mandated
  entry, reach for that tool — or ledger one line saying why not. If you used a
  declared resource, say so in the closing row." The why-not row is the escape valve
  that keeps blessed from meaning forced; its absence under a mandated tier is what the
  countersign checks (§4).

## 4. Enforcement — the obligation-attachment vocabulary

The maintainer's reframe (see STATUS above) identified the general shape: an obligation
attaches to a PRINCIPAL (today's countersign machinery — everything a given identity
writes needs distinct eyes), or to a TASK TYPE (every task of this shape carries a
discharge obligation), or is COMMISSION-CONDITIONAL (this commission demands review of
its work). The registry's mandated tier is precisely a task-type attachment:
"hyperparameter enumeration is discharged by declarative OR-Tools code, countersigned."

- Stage 1 (convention, no kernel change): a mandated declaration names its EVIDENCE
  SHAPE — the checkable artifact that proves the discipline was followed (a committed
  declarative model file; redis keys matching a stated prefix; a DerivationRecord — the
  solver-run provenance record the engine layer banks for every solver invocation,
  pinning engine, version, config, and input/output hashes). The work item for a
  mandated-shape task carries a review obligation by convention: its close is
  countersigned by a distinct principal whose review row must cite the evidence shape,
  present or absent. Self-reports are not trusted, per the maintainer's blunt and
  witnessed reason: implementers "take undue license and lie about what they have
  done." The reviewer verifies the ARTIFACT, never the narrative.
- Stage 2 (kernel change, on witnessed need): typed attachment columns on the
  obligation table — attachment_type ∈ {principal, task_type, commission} with matching
  gap views (today's review_gap stays the principal-scoped instance, unchanged). The
  superseded ruling document is answered by this section; the general vocabulary is the
  answer to its badly-framed binary.

## 5. First-class ordering constraints (declaration, checking, discharge)

Verified current state: lineage step s22 (the work-item layer) carries pairwise depends
edges with unknown-slug and cycle checks, deliberately visible-only; nothing checks that
a close respects its dependencies; nothing expresses conditional precedence, resources,
or deadlines; nothing DERIVES a lawful order.

- Declaration: v1 keeps the existing `work depends` edge as the only kernel-touching
  form. Richer constraints (conditional precedence, mutual exclusion) are declared as
  `constraint:`-prefixed convention rows naming slugs — parseable, supersedable,
  attributable, zero schema change.
- Checking: one new ASP program — the ordering-violations checker — over the work-item
  EDB (extensional database: the fact set an ASP program reasons over, exported from
  the ledger): close-before-dependency (the verified missing check), conditional-
  precedence violations, and the existing cycle check re-derived. Visible-only first,
  judge-style closed verdicts, and a SQL floor per the marriage discipline — this
  repo's standing rule that every verdict is derived independently in ASP and in SQL
  and the two must agree bit-identically (the `./judge` verb's own standard). This is
  the ordering leg's whole stage-2 build: modest, entirely in the house idiom.
- Discharge (the escalation ladder, recorded in the blessed-table template that stage 1
  ships — §8): trivial orderings need nothing; pure precedence at scale → tsort or a
  ten-line ASP enumeration; arithmetic or resources → Z3 / OR-Tools, their outputs
  committed as the auditable schedule artifact (the maintainer's hyperparameter-
  enumeration precedent generalized).
- Forward-compatibility (the ONLY planning trace in the core, per the maintainer's
  calibration): IF a work item ever declares preconditions/effects, they are typed
  lists in structured fields, never free prose — so a future planner consumes them
  without migration. No pre/effects fields are BUILT now.

## 6. The stretch appendix — planning (the maintainer's "christmas gift")

"Christmas gift" is the maintainer's own label for this tier: wanted, wrapped, and
opened only if everything else above is done. Not built; recorded so the substrate
stays honest about what it already permits. ASP subsumes STRIPS-class planning (fluents
over steps, inertia via negation-as-failure, goals as constraints, #minimize for
shortest plans — every construct already in the house .lp corpus). If it is ever
opened: (a) retrospective plan VALIDATION — declared pre/effects plus the ledger's
executed order, checked as a lawful plan, giving a formal decomposition-completeness
answer (goal reachability from the commission); (b) plan SYNTHESIS as the ladder's top
rung; (c) hierarchical-task-network typing for the commission→task tree. The
maintainer's industry calibration stands: MIP/cvxpy/OR-Tools cover applied planning;
this appendix is research, opened last, by his explicit word.

## 7. Honest limits and refusals

- Declared task shapes, preconditions, and why-not rows are judgment-triggered — the
  J-boundary of [BRIEF-CONFORMANCE-MAP.md](../law/briefs/BRIEF-CONFORMANCE-MAP.md):
  no machine can detect that a judgment-triggered entry SHOULD have been made. The
  registry strengthens intake and review discipline; it cannot make the mind legible.
  The countersign verifies evidence shapes — artifacts — never intentions.
- No LLM judgment in any blocking path, unchanged. The eliciting line exhorts; the
  only refusals are deterministic (a mandated close without its countersigned evidence
  review is ordinary review-gap debt, enforced by machinery that already exists).
- The registry never auto-executes anything. Declaring redis does not start redis;
  REACH is an address, not an action.

## 8. Implementation routing and witness plan

Stage 1 (Sonnet, one commission): pickup RESOURCES section + preamble eliciting line +
statement conventions (resource:/constraint:) + the blessed-table template document
(the task-shape → blessed-tool table, shipped as a template the maintainer fills at
adoption; §5's escalation ladder is its ordering column) + the mandated-tier review
convention. Witness: a scratch project declares three resources across tiers; pickup
shows them; a mandated-shape work item's close without the evidence review lands as
visible review-gap debt; with it, clean.
Stage 2 (Sonnet, second commission): the ordering-violations ASP program + SQL floor +
differential, with banked [seen-red](../GLOSSARY.md#seen-red) evidence both polarities
(a manufactured close-before-dependency goes red; a lawful order passes) — a gate never
seen red is a claim, per the house rule.
Stage 3 (on witnessed need, the pre-ratified fail-safe class): the s27 `resource` kind;
obligation-attachment columns. Stage 4: the appendix, if ever, by explicit maintainer
word.

## Closure statement (per [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)'s closure form)

The universe this spec admits: resource declarations in three tiers on a deployment's
own ledger; task-shape-keyed eliciting via pickup + preamble; mandated-tier enforcement
by countersigned evidence-shape review; ordering constraints declared (depends edge +
convention rows), checked (ASP + SQL floor, visible-only), and discharged (the
tsort→ASP→Z3/OR-Tools ladder); planner-shaped typed fields as forward-compatibility
only. It refuses: upstream-file registries (the library rule above), auto-execution,
LLM-judged blocking, prose-only mandated discharges, and any planning BUILD before the
maintainer opens the appendix. Out of scope with reasons: numeric/temporal scheduling
semantics beyond the ladder's hand-off to Z3/OR-Tools (their committed artifacts are
the audit trail; their internals are not re-derived); multi-project resource federation
(no second consumer exists).
