# The resource registry — Pillar 1, with obligation attachment and first-class ordering

<!-- doc-attest-exempt: doc-tree relocation mechanical edit (work item doc-tree-reorg-user-guide, ledger row 1620, 2026-07-18) -- relative link path(s) repointed to a sibling file's new location after a git-mv relocation elsewhere in the tree; no prose rewrite, same disposition as the v1.1.2 release-cut's own markers (commit 543a389). Removal condition: strike this marker and run the real A:B:C loop next time this file is touched for content, not just link repair. -->


Audience: orchestrator (secondary: maintainer — §2 tiers and §6 are his calls)

This document specifies the capability registry: how a project declares the resources
available to it (tools, solvers, services, backends), how an agent working in that
project is led to actually reach for them, and how mandated-tool disciplines are
enforced. It is written for the executor who builds from it and for the orchestrator who
stages the build. The project's own root work tracker (run `./led --recent` at the
repository root to read its rows) carried two open items — `pillar-1-resource-registry`
and `deontic-attachment-vocabulary` — that this document merges into one design because
they proved to be one design.

STATUS: this is a spec authored by Fable (the project's senior AI authoring model, per
[CLAUDE.md](../CLAUDE.md)'s ORCHESTRATION section), dated 2026-07-12, answering four
maintainer inputs of the same day, each recorded as a decision row on that same tracker:
it covers the resource-declaration
service; the obligation-attachment reframe (the maintainer's answer to the review-gap scope
ruling — he rejected its binary framing in favor of a general attachment vocabulary; the
superseded ruling is
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
- A declaration statement carries six fields, in a fixed order the pickup view can parse:
  NAME; CLASS (solver | service | backend | binary | library); REACH (endpoint, binary
  path, venv, or import); WHAT-IT-PROVES (one clause — the eliciting hook: "feasibility →
  this", "auditable enumeration → this"); GUIDANCE (when to reach, when not); TIER
  (available | blessed: <task-shape> | mandated: <task-shape>).
- A resource is declared by the commissioner or by the author citing the commission. The
  commissioner can sign the declaration with the commission-signing machinery — FULL mode
  (typed from his own terminal, proven by actor plus absent stamp) or SIGNED mode (a GPG
  detached signature over the text), both defined in
  [USER-GPG-TRUST-LAYER-FAQ.md](../user-guide/USER-GPG-TRUST-LAYER-FAQ.md) — and a mandated-tier
  declaration is commissioning-grade, so signing it is apt. Superseding a declaration is
  the ordinary supersedes edge; the registry view shows only unsuperseded rows.
- The canonical residents for this maintainer's projects are, from his own enumeration:
  MIP (mixed-integer programming, via the SCIP solver), cvxpy, OR-Tools, Z3, clingo (already
  the house engine), tsort, redis,
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
  done." The reviewer verifies the ARTIFACT, never the narrative. (This section is the
  authoritative build/witness record of what Stage 1 shipped; the reconciled statement of what
  "enforced" means for this tier — POLICED vs DECLARED-ONLY, how it composes with the separate,
  still-unbuilt usage-evidence deontic checker, and why it is not a refusal of the close itself —
  is owned by [ORCH-SPEC-RESOURCE-ACCOUNTING.md §4.1](ORCH-SPEC-RESOURCE-ACCOUNTING.md#41--the-mandated-tiers-enforcement-status-reconciled-dated-correction-2026-07-13-tracker-row-223),
  added 2026-07-13 to reconcile a same-day drift between the two specs, tracker row 223.)
- Stage 2 (kernel change, on witnessed need) adds typed attachment columns on the
  obligation table — attachment_type ∈ {principal, task_type, commission} — with
  matching gap views (`review_gap` — the kernel-derived view that lists every
  ledger row whose author owes a countersign and has not received one — stays today's
  principal-scoped instance, unchanged). The superseded ruling document is answered by
  this section; the general vocabulary is the answer to its badly-framed binary.

## 5. First-class ordering constraints (declaration, checking, discharge)

Verified current state: lineage step s22 (the work-item layer) carries pairwise depends
edges with unknown-slug and cycle checks, deliberately visible-only; nothing checks that
a close respects its dependencies; nothing expresses conditional precedence, resources,
or deadlines; nothing DERIVES a lawful order.

- Declaration: v1 keeps the existing `work depends` edge as the only kernel-touching
  form. Richer constraints (conditional precedence, mutual exclusion) are declared as
  `constraint:`-prefixed convention rows naming slugs — parseable, supersedable,
  attributable, zero schema change.
- Checking is done by one new ASP (Answer Set Programming, the clingo layer that is this
  project's reason to exist) program — the ordering-violations checker — over the
  work-item EDB (extensional database: the fact set an ASP program reasons over,
  exported from the ledger). It verifies close-before-dependency (the verified missing
  check), conditional-precedence violations, and it re-derives the existing cycle check.
  Discharge is checked visible-only first, with judge-style closed verdicts (a closed
  vocabulary of named outcomes — AGREE, DIVERGE_BY_DESIGN, DIVERGE_DEFECT, QUARANTINED —
  the same vocabulary the `./judge` verb already uses) and a SQL floor per the marriage
  discipline — this repo's standing rule that every verdict is derived independently in
  ASP and in SQL and the two must agree bit-identically. This is the ordering leg's
  whole stage-2 build: modest, entirely in the house idiom.
- Discharge follows the escalation ladder (recorded in the blessed-table template that
  stage 1 ships — §8): trivial orderings need nothing; pure precedence at scale escalates
  to tsort or a ten-line ASP enumeration; arithmetic or resources escalate to Z3 /
  OR-Tools, their outputs committed as the auditable schedule artifact (the maintainer's
  hyperparameter-enumeration precedent generalized).
- Forward-compatibility (the ONLY planning trace in the core, per the maintainer's
  calibration): IF a work item ever declares preconditions/effects, they are typed
  lists in structured fields, never free prose — so a future planner consumes them
  without migration. No pre/effects fields are BUILT now.

## 6. The stretch appendix — planning (the maintainer's "christmas gift")

"Christmas gift" is the maintainer's own label for this tier: wanted, wrapped, and
opened only if everything else above is done. Not built; recorded so the substrate
stays honest about what it already permits. ASP subsumes STRIPS-class planning (STRIPS: the
classical AI-planning formalism of states, actions, and goals) — fluents
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
  [J-boundary](../law/briefs/BRIEF-CONFORMANCE-MAP.md#the-j-boundary--the-limit-of-what-gap-detection-can-promise)
  (the line between the absences a machine can detect and the ones only a human judgment can
  catch) of [BRIEF-CONFORMANCE-MAP.md](../law/briefs/BRIEF-CONFORMANCE-MAP.md):
  no machine can detect that a judgment-triggered entry SHOULD have been made. The
  registry strengthens intake and review discipline; it cannot make the mind legible.
  The countersign verifies evidence shapes — artifacts — never intentions.
- No LLM judgment sits in any blocking path — this is unchanged. The eliciting line exhorts; the
  only refusals are deterministic (a mandated close without its countersigned evidence
  review is ordinary review-gap debt, enforced by machinery that already exists).
- The registry never auto-executes anything. Declaring redis does not start redis;
  REACH is an address, not an action.

## 8. Implementation routing and witness plan

Stage 1 (Sonnet, one commission) ships: pickup RESOURCES section + preamble eliciting
line + statement conventions (resource:/constraint:) + the blessed-table template
document (the task-shape → blessed-tool table, shipped as a template the maintainer
fills at adoption; §5's escalation ladder is its ordering column) + the mandated-tier
review convention. Witness: a scratch project declares three resources across tiers;
pickup shows them; a mandated-shape work item's close without the evidence review lands
as visible review-gap debt; with it, clean.
Stage 2 (Sonnet, second commission) ships: the ordering-violations ASP program + SQL
floor + differential, with banked [seen-red](../GLOSSARY.md#seen-red) evidence both
polarities (a manufactured close-before-dependency goes red; a lawful order passes) — a
gate never seen red is a claim, per the house rule.
Stage 3 (on witnessed need, the pre-ratified fail-safe class) adds: the s27 `resource`
kind; obligation-attachment columns. Stage 4 adds the appendix, if ever, by explicit maintainer
word.

**STATUS 2026-07-12: Stage 1 SHIPPED** (tracker item `registry-stage1-implementation`,
Sonnet-executed). Four things were built:

- The `./pickup` RESOURCES section (`bootstrap/templates/pickup.tmpl`), tier-sorted with
  mandated entries first and an honest empty-registry line.
- The preamble eliciting line, plus one sentence on the mandated-tier review convention, added
  as a new numbered point in `bootstrap/templates/CLAUDE.md.tmpl`.
- The `resource:`/`constraint:` statement grammars, each with a copy-paste example and the
  mechanical row-to-declaration conversion worked through, in
  [USER-BLESSED-TABLE-TEMPLATE.md](../user-guide/USER-BLESSED-TABLE-TEMPLATE.md) — the blessed-table
  template, pre-filled with this maintainer's own stack as marked worked examples, one column
  per §2 field plus the §5 escalation-ladder ordering column.
- The mandated-tier review convention itself, composing `led obligate` / `led review` /
  `review_gap` with no kernel change, including the [documented
  over-catch](../user-guide/USER-BLESSED-TABLE-TEMPLATE.md#the-mandated-tier-review-convention) (once a
  principal is obliged, `review_gap` counts every row that principal writes, not only its
  mandated-shape ones) stated plainly rather than glossed over.

GLOSSARY.md gained `mandated (tier)` and `resource declaration` entries. The whole build was
witnessed live per this section's own plan, both polarities banked at
`seen-red/resource-registry/` (registered in `gates/fixture_census.py`; scratch substrate torn
down to zero residue afterward): three resources were declared across all three tiers via real
`./led decision` calls; `./pickup` showed them tier-sorted, mandated first; a mandated-shape
work item closed with no countersigning review landed as six visible `review_gap` rows (the
over-catch above, reproduced live, not merely asserted); countersigning all six with a distinct
principal brought `review_gap` back to zero rows. Stages 3-4 remain exactly as specified above,
untouched.

**STATUS 2026-07-12: Stage 2 SHIPPED** (tracker item `registry-stage2-ordering-checker`,
Sonnet-executed). The ordering-violations checker exists: `engine/lp/ordering_violations.lp` +
`engine/ordering_obligations.lp` (the ASP program; it emits one family verdict per named check
— `ordering_verdict(close_before_dependency|conditional_precedence|dependency_cycle, discharged|
violated|undecidable|vacuous)` — never silence), `engine/ordering_edb.py` (the ASP producer's
ledger-only EDB — no journals, pure id-order, plus the `constraint:` grammar parsed into typed
facts), `engine/ordering_floor.py` (the independent SQL floor, one recursive CTE for the cycle
closure), `engine/ordering_differential.py` (the marriage differential, imports
`engine/ledger_differential.py`'s conventions wholesale), and `engine/ordering_audit.py` wired
into `./audit --ordering` (a new exit 7, reachable only through that flag, mirroring `--preamble`'s
exit 5 exactly — the "mirror the existing choice architecture" instruction, honored literally;
authored as exit 6 in its worktree branch, bumped by the integrator at the merge seam because the
`--review-gap` addendum, built in parallel, shipped first and owns 6).

This build covers only the RESIDUE left after an earlier, separate commission —
[design/ORCH-CONTEMPORANEITY-PART3-SPEC.md](ORCH-CONTEMPORANEITY-PART3-SPEC.md) ("Part 3" of
the governance-preamble ordering-obligations work, distinct from this document's own stages) —
already shipped three adjacent checks in `engine/lp/preamble_ordering.lp`: F5 (open-before-claim),
F6 (claim-before-close), and F11's dangling-dependency member. Those three are NOT duplicated
here. This program covers exactly three checks: (1)
close-before-dependency — the verified-missing check named in this section's own text above, over
the plain `work_depends` edge; (2) conditional-precedence — the already-shipped (stage 1)
`constraint: precedes <slug-1> <slug-2> [<slug-n>...]` convention row, expanded pairwise into a
chain (an executor scope decision, recorded in the program's own header, since the grammar names
N slugs without stating an N>2 semantics); (3) dependency-cycle, RE-DERIVED (this section's own
word) over the UNION of `work_depends` edges and the new `constraint_precedes` edges — a strict
superset of `work_items.lp`'s own cycle check, catching a cycle that spans BOTH edge families,
which that program structurally cannot see. `constraint: excludes` (mutual exclusion) is
RECOGNIZED (a `constraint_excludes_deferred/1` fact is emitted, visible in every report's
`counts=`) but NOT checked this pass — the tracker item's own text names only
"conditional-precedence"; filed in `BACKLOG.md`, not silently dropped. That filing is honest
about size, not merely presence: `excludes` means "may not both be open/claimed at once," an
interval-overlap question — did two spans of time overlap at all — structurally closer to
`preamble_ordering.lp`'s own two-clock-bridge/open-window machinery (that program's own name for
the logic comparing two intervals of time to decide whether one fell entirely before, entirely
after, or overlapped the other) than to `conditional_precedence`'s plain pairwise id-ordering — a real,
separate design pass, not a one-rule-block mirror of `conditional_precedence` (an earlier draft
of this section understated that cost; corrected here after an out-of-frame review — a
fresh-context reviewer, dispatched with no access to the implementer's own reasoning, run per
this project's standing hack-rationalization-check practice — caught it).

HONEST CAVEAT on the close_before_dependency/F11 partition (found by the same out-of-frame
review, disclosed rather than left implicit): F11's own coverage of a dangling antecedent is
TIME-GATED — both its rules require a `stop_event` fact, and F11 carries no
`ob_family_forced_undecidable` entry (the escape-hatch fact this program's own family uses to force
an `undecidable` verdict instead of a silent `vacuous` one when a needed precondition is simply
absent — see the `pre_s22` escape hatch described in the paragraph below for the same mechanism used
elsewhere), so on a world/session with zero `stop_event` facts F11 reads `vacuous`, not
`undecidable`. In that window (mid-session, before any Stop) a real
dangling-dependency-plus-early-close defect is visible to neither checker at the OBSERVER layer.
This is not a live-safety gap — `hooks/stop_clean_exit.py` queries `work_item_violations`
directly at every actual Stop attempt, unconditioned on any EDB `stop_event` fact, so a session
cannot actually exit with the defect present — but it is a real blind spot in the two visible-only
reports specifically, now named in `engine/lp/ordering_violations.lp`'s own header rather than
implied-covered.

Witnessed both polarities live on scratch schemas (`seen-red/registry-ordering/`, registered in
`gates/fixture_census.py`, torn down to zero residue): a GREEN schema where all three families
DISCHARGE; a RED schema where all three VIOLATE (including a genuine cross-family cycle: a
`work_depends` edge plus a `constraint: precedes` edge, in opposite directions, closing a cycle
neither edge family closes alone) plus a malformed `constraint:` row (`constraint_unparsed`) and
a well-formed `excludes` row (the deferred residue, witnessed present); a THIRD, pre-s22 schema
(lineage stops at s21) proving the `pre_s22` forced-undecidable escape hatch — all three families
read UNDECIDABLE, never silently VACUOUS, even with a `constraint:` row on record (that
convention needs no s22 column to be written at all). Every scratch differential returned AGREE
(the two independent producers' atom sets matched bit-identically — one of this project's four
closed differential verdicts: AGREE, DIVERGE_BY_DESIGN, DIVERGE_DEFECT, or QUARANTINED, the
same vocabulary `./judge` uses); a negative control (one forged SQL-floor atom, in an isolated
subprocess, never touching either producer's real source) produced DIVERGE_DEFECT (an
undeclared divergence between the two producers), caught as intended.

A retroactive read-only run (`engine/ordering_differential.py run<N> --retain`, SELECT-only, no
lineage/schema mutation) over the settled historical worlds runs 4, 5, 6, 7, 9, 10, 11
(`toy@192.168.122.1`, dust, per the runs-are-linear ruling never touched) AGREEd on every world,
with a `derivation.json` DerivationRecord pair banked per world under
`engine/docs/ledger-marriage/derivations/ordering-violations/run<N>/` (this section's own claim
now carries the same artifact-backed rigor as Part 3's identical seven-world sweep, after an
out-of-frame review found the first pass of this section asserted the sweep in prose without a
retained artifact — a real gap, fixed here, not merely disclosed). Per-world family verdicts,
quoted exactly as observed: run4 `CLOSE_BEFORE_DEPENDENCY: VACUOUS, CONDITIONAL_PRECEDENCE:
VACUOUS, DEPENDENCY_CYCLE: DISCHARGED (edges=4, cycle_members=0)`; run5/run6/run7/run9/run10 all
three families `VACUOUS` (run9 vacuous by construction — zero ledger rows, the same fresh-world
specimen Part 3's own witness plan used); run11 `CLOSE_BEFORE_DEPENDENCY: DISCHARGED
(discharged=2, violated=0), CONDITIONAL_PRECEDENCE: VACUOUS, DEPENDENCY_CYCLE: DISCHARGED
(edges=2, cycle_members=0)`. The honest finding: none of the seven carries a `constraint:` row
(the convention is new with this build, so no historical session could have used it yet — the
`conditional_precedence` family is VACUOUS on all seven, uniformly), and the two worlds with real
`work_depends` edges on record (run4, run11) never violated the newly-checked rule in their own
actual history — the "verified missing check" was genuinely missing, but this corpus's real
conduct never happened to trip it.

## Closure statement (per [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)'s closure form)

The universe this spec admits is: resource declarations in three tiers on a deployment's
own ledger; task-shape-keyed eliciting via pickup + preamble; mandated-tier enforcement
by countersigned evidence-shape review; ordering constraints declared (depends edge +
convention rows), checked (ASP + SQL floor, visible-only), and discharged (the
tsort→ASP→Z3/OR-Tools ladder); planner-shaped typed fields as forward-compatibility
only. It refuses: upstream-file registries (the library rule above), auto-execution,
LLM-judged blocking, prose-only mandated discharges, and any planning BUILD before the
maintainer opens the appendix. It leaves out of scope, with reasons: numeric/temporal
scheduling semantics beyond the ladder's hand-off to Z3/OR-Tools (their committed
artifacts are the audit trail; their internals are not re-derived); multi-project
resource federation (no second consumer exists).
