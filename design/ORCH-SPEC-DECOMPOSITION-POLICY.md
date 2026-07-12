# ORCH-SPEC-DECOMPOSITION-POLICY — task-management obligations as declared policy

Audience: orchestrator (design spec; implementation stages are Sonnet-executable per §8).
Status: Fable-authored 2026-07-12, from the maintainer's departure ask of the same day
(on the record in this repository's tracker ledger, work item `decomposition-policy-spec`
— run `./led show <id>` or `./led --recent` at the repository root to read it): encode
task-management obligations — task-splitting criteria in particular — so the commissioner
does not micromanage decomposition per commission; do it flexibly, and in support of
regulatory commitments. This spec shares two structures with its siblings and says so
rather than redefining them: the deontic register (deontic: the vocabulary of permission
and obligation) of [ORCH-SPEC-RESOURCE-ACCOUNTING.md](ORCH-SPEC-RESOURCE-ACCOUNTING.md)
§3, and the fill-once-derive-declarations pattern of
[USER-BLESSED-TABLE-TEMPLATE.md](USER-BLESSED-TABLE-TEMPLATE.md).

## 1. The problem — six hand-written points, every time

Run 12's commission (its world ledger, row 1) carries six numbered process points the
maintainer typed by hand: decompose into one ledger row per subtask; assign a review
obligation for the decomposition; countersign via a distinct reviewer principal;
planning complete only when review-gap and question-status are empty; register
acceptance criteria before implementing; completion claims require commits. Every one of
those is a standing conviction about how tasks are managed, none is specific to terminal
colors, and all six had to ride the commission text because there is no declared place
for them — the same missing-registry shape
[ORCH-SPEC-RESOURCE-REGISTRY.md](ORCH-SPEC-RESOURCE-REGISTRY.md) §1 diagnosed for tools.
Two witnessed costs follow. First, micromanagement: the commissioner re-types (and may
re-type inconsistently, or forget) his own policy per ask. Second, drift with no
anchor: run 12's agent began executing task 1 roughly 2.5 minutes before the
decomposition countersign landed — a violation of the commission's own point 4 that
nothing could block on, because the point existed only as prose in one row (tracker item
`decomposition-review-blocker` carries the full specimen and the write-time fix).

## 2. The shape — policy criteria as declared ledger rows

A deployment declares its task-management policy the way it declares resources: rows on
its own ledger, written once at adoption (seeded from a template file the maintainer
edits, exactly the blessed-table pattern), pulled by every session at the same choke
point as everything else (`./pickup`), and cited by the preamble instead of restated by
each commission. Version 1 is a statement-prefix convention on `decision` rows — no
kernel change, mirroring the registry's stage 1:

```
task-policy: <CRITERION-NAME> | <MODALITY> | <STATEMENT> | <EVIDENCE-SHAPE>
```

- CRITERION-NAME — a stable slug the reviewer and the audit cite (e.g.
  `acceptance-criterion-first`).
- MODALITY — `must` | `should` | `may` | `must-not`, the same four-place register the
  accounting spec's §3 established for resource tiers; one register across the harness,
  never a second vocabulary.
- STATEMENT — the criterion in one or two sentences, written to the zero-context reader.
- EVIDENCE-SHAPE — what discharges or violates it: the name of a typed check (an audit
  family, a kernel constraint, a gate) where one exists, or the literal word
  `reviewer-judgment` where none can — the honesty of §4 depends on this field never
  pretending.

Intake validation reuses the machinery the `resource:` grammar got on 2026-07-12
(whitespace-normalized field-count refusal in `bootstrap/templates/led.tmpl`, teach-text
naming the grammar, nothing written on refusal); `./pickup` gains a TASK-POLICY section
with the same one-row-one-line parsing discipline. Superseding a criterion is the
ordinary supersedes edge — policy rows are ledger rows and enjoy the same append-only
history, which is itself the regulatory feature: an auditor can read WHEN a criterion
entered force and what work predates it.

## 3. The starter criteria — worked examples with provenance

Marked EXAMPLES exactly as the blessed-table marks its residents: these are THIS
maintainer's convictions, harvested from paid history; an adopter substitutes their own.
Each names its provenance and its honest policing status at authoring time:

| Criterion | Modality | Evidence shape | Provenance |
|---|---|---|---|
| `decomposition-cites-commission` | must | audit family F3 (preamble-ordering, live) | run 11 violated it; the contemporaneity audit's Part 3 ([ORCH-CONTEMPORANEITY-PART3-SPEC.md](ORCH-CONTEMPORANEITY-PART3-SPEC.md), "Part 3" below) caught it retroactively |
| `decomposition-reviewed-before-execution` | must | the change-gate extension (tracker `decomposition-review-blocker`) | run 12's 2.5-minute overlap |
| `acceptance-criterion-first` | must | orderable audit family (buildable; Part 3 conventions) | run 12 commission point 5; witnessed honored there |
| `completion-carries-witness` | must | kernel: [s22](../kernel/lineage/s22-work-item-ledger.sql) (the work-item-ledger lineage step) refuses shipped-without-witness at INSERT | the omega-era defect the kernel already forecloses |
| `explicit-dependency-edges` | should | orderable audit family (buildable; Part 3 conventions, same shape as `acceptance-criterion-first` above) — `work_depends_on` rows (a `led work depends <slug> <on-slug>` row, [bootstrap/templates/led.tmpl](../bootstrap/templates/led.tmpl)) exist where sequencing is claimed, but the checker that reads them is §8 Stage C's still-to-build work, not live yet | run 12 declared both its edges; the stage-2 ordering checker is designed to consume them once built |
| `one-acceptance-criterion-per-task` | should | reviewer-judgment | splitting criterion, §5 |
| `grain-follows-commission-text` | should | reviewer-judgment | run 11 retrospective: its decomposition tracked the maintainer's own sentence structure, and that was judged a virtue |
| `task-closeable-in-one-session` | should | reviewer-judgment | resumption doctrine: a task spanning sessions must survive on ledger state alone |
| `estimate-before-execution` | should | reviewer-judgment (the same orderable-audit-family shape as `acceptance-criterion-first` above — a task's `estimate:` row precedes its first `work_claimed` row, a `led work claim <slug>` row, [bootstrap/templates/led.tmpl](../bootstrap/templates/led.tmpl) — is buildable but unbuilt as of this row) | tracker item `cost-estimation-retro`, 2026-07-12: estimates are ledgered for operational-efficiency retrospectives ONLY, never cost policing (the maintainer's own invariant, stated twice at commissioning) — see [design/USER-RETROSPECTIVE-RECIPE.md](USER-RETROSPECTIVE-RECIPE.md) §6 for the grammar and the estimate-vs-actual comparison this criterion's discipline feeds |

## 4. Policing, derived — the same honesty as the accounting spec

Per criterion, the surfaced policing status is DERIVED from the EVIDENCE-SHAPE field and
the deployment's actual state, never self-declared: `POLICED (kernel)` when a constraint
refuses at insert; `POLICED (gate)` when a write-time hook denies; `POLICED (audit)`
when a live family flags; `REVIEWER-JUDGMENT` when the shape says so; `DECLARED-ONLY`
when the named check does not exist in this deployment yet. The table in §3 is honest at
authoring time, named by slug rather than left as an unverifiable count: **one** criterion
is already fully policed by shipped machinery (`decomposition-cites-commission`, audit
family F3, live); **one** is policed at kernel grade (`completion-carries-witness`, s22's
INSERT-time constraint); **one** is gated pending the blocker's merge
(`decomposition-reviewed-before-execution`); and **six** rest on reviewer judgment today —
two of them (`acceptance-criterion-first`, `explicit-dependency-edges`) because their named
orderable-audit-family check is buildable per §8 Stage C but not yet built (honestly
`DECLARED-ONLY`, not yet `POLICED (audit)`, despite `explicit-dependency-edges`'s own row
naming a "stage-2 ordering checker" — that checker is designed, not live, until Stage C
ships), and four (`one-acceptance-criterion-per-task`, `grain-follows-commission-text`,
`task-closeable-in-one-session`, `estimate-before-execution`, the last added 2026-07-12) by
design, their EVIDENCE-SHAPE field naming `reviewer-judgment` outright — a distribution the
maintainer's standing proviso (the 2026-07-12
amendments to [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)
and [ADR-0013](../law/adr/0013-execution-stamina-and-structural-completeness.md))
already governs: the text binds even where no machine checks it.

## 5. Splitting criteria — the maintainer's specific ask

When must a proposed task split? Version 1 offers three reviewer-checkable criteria (the
register makes them `should` — a reviewer who accepts a violation records why, the same
why-not escape valve the registry's blessed tier uses):

- **One acceptance criterion per task.** A task whose completion needs two unrelated
  acceptance criteria is two tasks. Crisp, teachable, and checkable against the
  registered criteria rows themselves.
- **One boundary per task.** A task spanning heterogeneous surfaces at once (the
  standing example from [CLAUDE.md](../CLAUDE.md)'s ORCHESTRATION: SQL schema plus the
  Python consuming it) either splits along the boundary or is explicitly justified —
  this is the same line the delegation contract already draws for model routing, reused
  as a decomposition criterion rather than invented fresh.
- **Independently witnessable completion.** If the completion evidence would be two
  artifacts with no common witness (a commit here, an unrelated service state there),
  the task splits so each close carries one checkable witness — s22's
  shipped-requires-witness constraint then polices each half at kernel grade.

The flexibility the maintainer asked for lives in the register, not in softening the
criteria: a deployment that wants hard splitting rules declares them `must` and builds
the audit family; one that trusts its reviewers declares `should` and the countersign
trail (§6) carries the record. The criteria are data, not code — changing policy is a
ledger act, not a harness release.

## 6. The reviewer's brief and the countersign trail

The decomposition countersign (mandatory-by-gate once `decomposition-review-blocker`
merges) checks the decomposition AGAINST THE DECLARED POLICY, not against taste: the
reviewer's brief is the TASK-POLICY section, and each countersign row cites the
criterion slugs it checked (`checked: acceptance-criterion-first,
one-boundary-per-task, ...` in the review statement). That citation line is what turns
reviewer judgment into a regulatory trail: an auditor reads which criteria were examined
for which decomposition, mechanically greppable, without pretending the judgment itself
was mechanical. A countersign that cites no criteria is exactly what the content-free
review audit (tracker item `content-free-review-audit`, run 12's "test"-row specimen)
exists to flag.

## 7. The regulatory connection — declared transition criteria

The planning-to-execution boundary this spec types is the shape regulated industries
call transition criteria (the maintainer's 2026-07-11 connection): a phase may not begin
until declared entry criteria are checked, with evidence, by someone accountable. The
mapping is direct — the policy rows are the declared criteria; the gate and audit
families are the mechanical checks; the criterion-citing countersign is the accountable
sign-off; the append-only ledger is the record a regulator reads. What this spec does
NOT claim: that conformance to declared policy makes a decomposition GOOD. A
conformant-but-foolish split passes every mechanical check; the reviewer's judgment
stays load-bearing, and §4's honesty labels exist precisely so no one mistakes the
checked criteria for the whole of quality.

## 8. Implementation routing (all stages Sonnet-executable from this spec)

- **Stage A — grammar + pull**: `task-policy:` intake validation in led.tmpl (clone the
  `resource:` validator's structure), pickup TASK-POLICY section, the template file
  (USER- audience, blessed-table style) with §3's starter set, preamble pointer
  replacing hand-written commission points. Proven both polarities (a malformed statement
  refused, a well-formed one accepted) with fixtures banked under [`seen-red/`](../GLOSSARY.md#seen-red)
  and registered in [`gates/fixture_census.py`](../gates/fixture_census.py)'s registry — the
  same discipline `bootstrap/templates/led.tmpl`'s existing `resource:` validator already
  carries.
- **Stage B — the countersign convention**: reviewer-brief text in the scaffold
  preamble/CLAUDE.md template teaching criterion-citing countersigns; the
  decomposition-review blocker's teach-text updated to name the policy section.
- **Stage C — audit families for the orderable criteria**: `acceptance-criterion-first`
  (a task's acceptance-criteria row precedes its first implementation row — Part 3's
  cross-clock conventions apply) and `explicit-dependency-edges`; **marriage-grade** — an
  independent SQL floor plus the ASP deductive-engine verdict, with the two required to
  AGREE (the phrase [design/ORCH-SPEC-RESOURCE-ACCOUNTING.md](ORCH-SPEC-RESOURCE-ACCOUNTING.md)
  §5 uses for the identical pairing) — proven both polarities and registered in
  [`gates/fixture_census.py`](../gates/fixture_census.py)'s registry, same as Stage A.
- **s27-adjacent deferral**: typed policy columns ride the same future kernel lineage
  step (s27, the deferred `resource` kernel kind both
  [ORCH-SPEC-RESOURCE-REGISTRY.md](ORCH-SPEC-RESOURCE-REGISTRY.md) §2 and the accounting
  spec stage their columns on), on the same columns-earn-their-place principle.

## Closure statement (in the spirit of [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)'s closure discipline — the universe-and-deliberate-absences parts; its denomination-check field concerns defect-class foreclosures and does not apply to a design scope)

The universe is the maintainer's departure ask: encode task-management obligations,
splitting criteria named, flexibly, supporting regulatory commitments. Encoding is
closed by §2 (declared rows, one shared register); splitting specifically by §5's three
criteria; flexibility by the register-plus-supersedes design (§2, §5); the regulatory
commitment by §6's citation trail and §7's transition-criteria mapping with its honesty
boundary. Deliberately absent, named where they fall: a claim that policy conformance
equals decomposition quality (§7); mechanization of judgment criteria (§4); kernel
columns before witnessed need (§8). The commission's six hand-written points each land
in a declared home (§1 ↔ §3's table); no seventh obligation is created by this document.
