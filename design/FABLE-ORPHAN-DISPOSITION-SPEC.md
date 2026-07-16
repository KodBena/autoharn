# FABLE-ORPHAN-DISPOSITION-SPEC — every violations-view member gets an answering act

This spec fixes a witnessed trap in the work-item layer: some members of the
`work_item_violations` view (this project's registry of governance defects on work
items, which the Stop hook (`hooks/stop_clean_exit.py`, the gate that blocks a
session from ending on open debt) and `distance-to-clean` (the repo-root
debt-count verb) count as blocking debt) have NO
act that can ever answer them — the debt is permanent by construction, and the only
way out today is destructive (retracting the historical fact itself) or the
stop-gate's last-resort fail-open. This spec closes the whole class: every
violations member becomes answerable by a typed, reviewed, validity-bounded
disposition act — debt until answered, record forever. It is written for the
maintainer (ratified, see Status) and the Sonnet builder (to implement).

Status: v3, RATIFIED 2026-07-16 (amendment ratified same day). v2's Element 3 bound
disposition validity to the target row's own currency; the final review witnessed
that this makes a violation on a superseded target row permanently unanswerable —
eternal debt via the `led` CLI's own recommended repair. The fix semantics were
consulted under [ADR-0018](../law/adr/0018-consults-are-not-front-loaded.md)
(record banked verbatim:
[ORCH-CONSULT-DEBT-SEMANTICS-2026-07-16.md](ORCH-CONSULT-DEBT-SEMANTICS-2026-07-16.md))
and ratified by the maintainer: THE DEBT PROJECTION QUANTIFIES OVER IN-FORCE ROWS
ONLY; THE RECORD PROJECTION QUANTIFIES OVER EVERYTHING, FOREVER. Elements 1 and 3
and the Closure below carry the amended text.
Prior status line: v2, RATIFIED 2026-07-16. v1 (same day) was reviewed under
[ADR-0014](../law/adr/0014-executor-second-opinion.md) by a fresh-context [Fable](../GLOSSARY.md#post-fable-law) (the maintainer's
primary AI-collaborator authoring model)
instance — consultation record banked verbatim at
[ORCH-ADR14-ORPHAN-DISPOSITION-CONSULT-2026-07-16.md](ORCH-ADR14-ORPHAN-DISPOSITION-CONSULT-2026-07-16.md)
— with verdict RATIFY-WITH-AMENDMENTS: the mechanism was upheld, v1's closure claim
was refuted with a live witness (see Provenance), and six amendments (A1–A6) were
enumerated. The consult's first amendment (its "A1") posed a fork — generalize the new act to
answer any violations member, or keep it orphan-specific — and the maintainer
ratified the generalized form; the maintainer also ratified the consult's proposed
sibling narrowing of `dependency_cycle`. The remaining amendments (its A2–A6) are
incorporated below. The
authoring-side lesson is recorded in the consult document; this spec is the
post-review text.

## Provenance — two witnessed traps, not one

In the panel (the `autoharn-panel` deployment at
`~/w/vdc/1/experience/autoharn-panel`, a downstream adoption of this harness), the
orchestrator superseded a composite parent work item to repair a mis-encoded refs
column; under
[s31's uniform retraction](../kernel/lineage/s31-supersession-uniform-retraction.sql)
the parent's slug burned and the five children's surviving parent-edges became
`orphaned_by_retraction` violations — three children already closed, so no re-issue
is possible for them — permanent debt, and the session can stop only through the
stop-gate's fail-open circuit breaker (its loud last-resort valve after three
identical blocked attempts).

The ADR-0014 consult then witnessed a SECOND permanent-debt path on a scratch
world: a `work_depends_on` self-edge of the default `informs` type is accepted at
construction (cycle refusal applies to `blocks-close` only) and surfaces as a
`dependency_cycle` violation that persists even after the edge is retracted (the
view's dependency arm reads raw history by design). v1 of this spec claimed orphans
were the only undischargeable member; that claim was false, and its falseness is
why this spec now closes the CLASS, not the specimen.

## The principle

The house calculus already has the right shape everywhere else: a question is debt
until answered; a deferred review is debt until countersigned; then each becomes
record. Violations were the one debt source with no answering act. This spec gives
them one — without touching retraction semantics: nothing here un-burns a slug,
revives a retracted row, or edits history. A disposition answers the question "what
became of this defect?" in a new, linked, attributable row — the append-only
correction discipline of
[the safety-critical-logging BRIEF](../law/briefs/safety-critical-logging/BRIEF.md)'s
invariant I3, with I7's validity bounds built in (element 3).

## Elements

### 1. Kernel delta `s37-violation-disposition` (ratification: granted, see Status)

- New ledger kind `work_violation_disposition`, written only by the `led` CLI
  (element 4), carrying: a stable key identifying the violations-view member it
  answers (the member class + the violating act's ledger id — following the
  existing per-kind column conventions that the kind-shape manifest gate,
  `gates/kind_shape_manifest_gate.py`, polices), a typed resolution — `reissued` (a successor
  act exists; the row cites it via the witness column) or `retired` (the defect is
  moot, with the basis stated) — and a free-text basis.
- Validation: the answered target must be an in-force `work_item_violations`
  member at write time, established by RE-DERIVING the member predicate for the
  given id — never by parsing the view's display text. Refused otherwise, with a
  teach-text.
- Uniqueness is IN-FORCE-SCOPED (consult A3): a second disposition is refused only
  while a prior one is in force; superseding a wrong disposition (the ordinary s31
  path — dispositions are themselves supersedable) reopens the slot. A raw-history
  uniqueness read would re-mint the very trap this spec removes, one level up.
- Review discipline (consult A5): a disposition removes stop-gate debt, so it
  carries the same witnessed-or-deferred posture as `work_closed` — deferred lands
  in the existing review-gap path and is countersignable there. No new review
  mechanism; the existing column discipline extended to one new kind.
- `work_item_violations` becomes the DEBT projection, and (v3 amendment) debt
  quantifies over in-force rows only. Every member class declares its TARGET
  TYPING — row-targeted (the defect inheres in one ledger row: the orphan
  sub-cases, `shipped_without_witness`, `depends_on_unknown_slug`,
  `dangling_parent`, `closed_but_tree_defeated`) or slug-targeted (the defect
  inheres in a configuration, the slug's `work_opened` row serving as handle:
  `duplicate_open`, `dependency_cycle`, `parent_cycle`, `blocks_close_cycle`) —
  and a member is debt only while its target row is in force. Retracting the
  target row IS the answering act: the member lapses in the same read, no
  disposition needed. A member whose target is in force drops out only while an
  in-force disposition answers it and that disposition's basis holds (element 3).
  Companion view `work_violation_history` — the RECORD projection named in the
  ratification above — keeps every raw, unfiltered arm forever
  and additionally surfaces, per lapsed member, the superseding row that answered
  it — every defect's fate is attributable on the record: a disposition, a
  retraction, or open debt. The new view needs its GRANT and its
  `gates/ledger_reader_allowlist.py` classification; `work_item_violations`'
  allowlist entry retypes to current-truth-factored, with the raw structural
  reads living wholly in the history view's declared-history entry.
- Sibling narrowing, RATIFIED: the view's `dependency_cycle` member narrows to
  `blocks-close` edges only. Blocks-close cycles are already refused at
  construction, so the member becomes properly vacuous (defense-in-depth); an
  `informs` cycle becomes a legal non-event, matching informs' advisory-only
  semantics (an informs edge never gates anything, so mutual citation is
  legitimate, not a defect).
- Header: `HISTORY: safe`, grounds stated per the
  [migration header convention](MAINT-MIGRATION-ACCOMMODATIONS-SPEC.md): additive
  kind + validator, two view re-issues, no existing rows touched. The delta ships
  with a `.detect.sql` sibling file — the per-delta verification convention
  documented in `bootstrap/migrate_core.py`'s module docstring, by which `./migrate`
  detects whether a world already carries a delta — and that detect must fingerprint
  BEHAVIOR or CATALOG SHAPE across the whole schema, never which named object
  carries a marker string (a ledgered rule from the 2026-07-16 detect-drift
  incident, in which two detects pinned to named function bodies went false-negative
  after refactors moved their marker text, and `./migrate` planned a wrong
  re-application as a result; the rule is restated in the s29/s30 detect siblings'
  own headers).

### 2. Engine twin, same delta (consult A2 — mandatory, not optional)

`engine/lp/work_items.lp` mirrors the violations arms and `engine/ledger_floor.py`
twins them; narrowing the SQL members without the matching `.lp` and floor changes
breaks the SQL/ASP differential — this project's standing drift detector, and the
deductive layer is the project's point. s37 ships its engine companion in the same
change, exactly as s31 did, and `./judge` (the repo-root verb that runs the SQL/ASP differential and reports AGREE
when both layers derive identical facts) must read AGREE on a scratch world
exercising: an answered orphan (drops from both), an unanswered one (present in
both), and an informs cycle (absent from both post-narrowing).

### 3. Validity-bounded dispositions (consult A4 — BRIEF I7 made mechanical; v3-corrected)

A disposition whose basis lapses must stop answering, automatically, in the same
read — where the basis is a NAMED, GENUINELY RESURRECTABLE condition: `retired` on
a settled child answers only while that child's close stands (a later supersession
of the close revives the child, and the orphan debt resurfaces — work items are
resurrectable); `reissued` answers only while the cited successor row is in force.
The v2 text additionally required the disposition's TARGET row to remain current —
the final review witnessed that this inverts I7 for row targets: under s31's
reinstatement-free retraction, "target retracted" is a permanent condition, so a
bound conditioned on un-retraction is not a bound but eternal debt. v3 removes it:
a disposition whose target row is later retracted becomes MOOT (its member already
lapsed per element 1), never defeated. This is one join in the debt view, not a
procedure.

### 4. CLI: `led work resolve-violation`

The command is `led work resolve-violation <violating-act-id> <reissued|retired>
"<basis>" (--review-witness <ref> | --review-deferred) [--witness <successor-ref>]`.
It is parsed in its own arg loop with the refuse-unknown-flags idiom, and refuses
with teach-texts on: a pre-s37 world (live catalog check), an id that is not
currently an in-force violation member, and a target already answered by an
in-force disposition. `reissued` without `--witness` warns (the successor citation
is the row's whole value) but is not refused — the kernel cannot verify successor
equivalence, and pretending otherwise would be a lying signature.

### 5. Cascade convenience: `led work supersede-cascade`

The consult refuted subtree re-issue as the PRIMITIVE (a subtree is not closed
under reference, and settled reviews cannot be honestly re-issued — a re-issued
review row would forge the reviewer's agency) but endorsed it as the CLI
convenience for live descendants. This verb: supersedes a work item's open row,
re-opens each surviving OPEN descendant under a new slug citing its predecessor,
re-issues their claims/edges, and writes each resulting orphan's `reissued`
disposition citing the successor — one witnessed act per step, every row ordinary
and attributable, all built ON the primitive. CLOSED descendants stay put; their
orphaned parent-edges get `retired` dispositions (validity-bounded per element 3,
so a later defeat of such a close automatically resurfaces the debt). Known,
accepted limit: repaired-tree topology for settled children is auditable through
disposition rows and refs but not walkable by `work_item_descendants`; if
rollup-walkability over repaired trees ever matters, that is a separate spec.

### 6. Teach-texts that close the loop (consult A6)

- `led work violations` output gains, per row, the discharge path
  (`led work resolve-violation ...`), the same way the stop-gate's debt lines name
  theirs.
- `hooks/stop_clean_exit.py`'s violations else-branch (~line 660) currently calls
  legal-and-surfaced orphan rows a "kernel/trigger anomaly; escalate" — wrong and
  misleading; it is rewritten to name the disposition path.
- The `work open --supersedes` advisory (added 2026-07-16) gains one sentence
  pointing at `resolve-violation` and `supersede-cascade` for the aftermath.
- Reissue recursion, named plainly: dispositioning an orphaned OPEN child as
  `reissued` entails re-opening it under a new slug, which orphans that child's
  own surviving claims/edges one level down. The mechanism is closed under this
  recursion — each new orphan is dispositionable, and the cascade verb walks it —
  but builders and operators should expect the intermediate states.

## What this spec does NOT do

It does not make retraction reversible, does not revive burned slugs, does not
auto-disposition anything (every disposition is a deliberate, reviewed act with a
basis), and does not exempt violations from surfacing — every defect still appears
as debt until an attributable act answers it, and lapses back into debt if the
answer's basis is defeated. The trap is removed; the discipline is strengthened.

## Closure (v3 posture)

v1 quantified over enumerated specimens and was refuted by a second specimen. v2
quantified over "every member has the disposition act" and was refuted by the
retracted-target case — the disposition existed but could never answer. v3 states
the invariant the consulted literature grounds: every `work_item_violations`
member has, at every moment, at least one REACHABLE answering act — a disposition
while its target row is in force, the target's own retraction otherwise. The state
"debt with no possible answering act" is unrepresentable because the debt
predicate and the answer predicate quantify over the same world (`ledger_current`,
the kernel view returning only non-superseded rows — current truth)
— the v2 defect was precisely a mixed-timeline predicate, membership read from raw
history while answers read from current truth. A future delta adding a violations
member must declare its target typing (row- or slug-targeted) and, if it names a
resurrectable basis condition for element 3, name it explicitly. The residual
defense-in-depth members (construction-refused, vacuous in ordinary operation)
inherit the same invariant by the same construction.
