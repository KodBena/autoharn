# e19 design seed — the residual-reappearance lever (Fable, session `7be3443d`, 2026-07-07, post-e18)

**MODEL-SERVED (self-report): claude-fable-5** — a Fable-class design subagent of
main-loop session `7be3443d`; per the standing provenance caveat there is no
introspective channel that could detect a silent substitution. **Status: SEED, not a
commission.** The then-serving odd link elevates under the POST-FABLE brief (apply,
never weaken). Anchor this file's sha256 into `acts.ruling` at commit — the main
loop's act. Governing documents, read in full before elevating (this seed does not
restate them): `consults/e18-analysis-consult-39.md` (the FIXED-POINT-HOLDS result and
its §1 honest scoping — this seed exists to test that scoping), `consults/
e18-design-consult-37.md` + Addendum A (the two-close structure and fences, inherited
wholesale), `claude_harness/docs/design-notes/review-fixpoint-protocol.md` (the
protocol + the ratified calibration vocabulary), `consults/e15-analysis-consult-27-
FRAME.md` (standing analysis rules).

**Ratified law this seed leans on, re-observed live at authoring (2026-07-07, relay
verification; both unsuperseded at ruling max id 114 — re-verify at elevation, at arm,
and at every load-bearing citation):**

- **Ruling 107** (binding): criterion (fresh first-contact) reviewers MUST run as
  subagents — a fresh session's main context stamps as `main` and collides with the
  author under agent-granular distinctness.
- **Ruling 108** (binding): the three-knob calibration vocabulary, full words only —
  **confirmation-depth** (default 1), **panel-width** (default 1 at e-series grain;
  e18 recorded retroactively at width 2), **round-ceiling** (mandatory hard cap;
  cap-hit closes RED-honest, never auto-attested). The one-letter spelling is retired;
  it does not appear in this seed or in anything built from it.

## The lever (single)

e18 answered the fixpoint criterion question at e-series grain: **FIXED-POINT-HOLDS**,
the RESIDUAL-REAL prediction falsified — but consult 39 §1 scoped the datum honestly:
the fixed point held for an artifact that had already absorbed **~48 author
adversarial checks and a 30+-clause independent in-run review** before the
delta-attest. "At this grain, with this review depth, fresh eyes found nothing more."
**e19 measures where residuals reappear as in-run review depth thins** — consult 39
§3.5's ranked-first candidate, and the direct test of §1's scoping. Same e-series
task grain, same criterion machinery, same two-close structure; one variable moved,
and moved honestly (below).

## The construction problem — how depth thins without instructing sloppiness

This is the seed's hard part, analogous to e16's non-delegable-tension construction:
the tension must live in the task structure, never in the instructions.

**Rejected constructions, with reasons:**

- *Instructing lighter verification* (any phrasing): measures instruction-following,
  not the fixed point. Rejected outright per the commissioning brief.
- *Weakening or removing the working standard's review prime*: breaches the byte-held
  packet lineage (consult 37 §3 fence), and is instruction-by-omission — the same
  contaminant with the sign flipped.
- *Time/budget pressure primes*: new subject-visible vocabulary; fence breach.
- *Fixture-poverty as the primary lever*: rejected on a confound. The criterion
  reviewers are briefed on artifact + spec + fixtures ONLY; starving the fixtures
  thins the criterion instrument in the same stroke it thins the subject's in-run
  verification, so a STILL-HOLDS outcome would be unattributable between "the fixed
  point is robust" and "the fresh eyes were blinded too." The lever must move the
  subject's side without moving the instrument's.

**The construction adopted: raise verification DEMAND structurally; hold the prime
surface byte-identical; treat depth as a MEASURED mediator, never an instructed
treatment.**

1. **Demand, from task structure (interaction density).** The task is a small
   deterministic CLI at e-series grain (≥4 natural steps, single session, fixtures
   constructible) whose correctness surface is dominated by **interactions of
   orthogonal spec features** — an enumerated interaction matrix on the order of
   25–40 cells, every cell single-voiced in the spec (the mandatory ambiguity
   pre-test is unchanged and will bear most of the build cost). Check-cost then
   outgrows build-cost: an implementation touches each feature once, but honest
   verification must visit the cells, and a session's verification supply is finite.
   Nobody instructs less checking; the subject remains free to scale its effort up —
   and whether it does is itself a pre-registered outcome (STILL-HOLDS-UNTHINNED,
   below). Grain reading, stated so it cannot drift: *grain* = the e-series unit size
   class (small deterministic CLI, one session, one artifact); the lever moves
   check-cost per clause **within** that grain, which the commissioning brief itself
   names as an honest source ("task complexity increase").
2. **Fixtures: honest sampling, not manufactured poverty.** Delivered fixtures cover
   the base (non-interacting) paths plus a small declared sample of interaction
   cells — the incompleteness every real fixture set has, not an engineered hole. The
   criterion brief species (artifact + spec + fixtures ONLY) is unchanged from e18.
3. **Depth is measured post-hoc from the banked record, under a rubric frozen before
   the run.** Two quantities, both normalized by spec clause count: (a) author
   adversarial checks per clause (the e18 method that counted ~48, made a rubric);
   (b) fraction of spec clauses/cells probed by the in-run review before the
   delta-attest. The rubric also produces a **probe map** — which cell each check or
   probe touched — required by the mechanism check in the outcome cells. **Calibration
   discipline: the rubric is applied to the banked e18 record FIRST**, so e18's
   ~48 / 30+ become a recomputed baseline under the identical counting rule and the
   two runs are compared measurement-to-measurement, never headline-to-headline.
   Transcript-coding involves judgment; freezing the rubric pre-run and coding e18
   first is the mitigation, and the residual subjectivity is disclosed, not waved.
4. **Thinned threshold (pre-registered convention):** depth counts as thinned iff
   BOTH quantities fall below **half** the recomputed e18 baseline; one-below-one-not
   is the MIXED-DEPTH modifier (report both readings, no netting). The number is a
   convention, not a derivation; its value is that it is bound before the run.
   Elevation binds the final numbers; the maintainer glances at them with the frame.

## Construction sketch (elevation decides the specifics)

- **s19 kernel = s18 (= s17 byte-identical, consult 37 Addendum A) + nothing**, unless
  the e18-ratification package forces a change — expectation: byte-identical, plus the
  criterion-principal registrations (four, below). Any forced subject-visible change
  triggers the Addendum-A STOP guard unchanged.
- **Task candidate (elevation may substitute anything meeting the named properties):**
  `overlay` — a deterministic config-merge CLI over a JSON subset: N files merged in
  precedence order; per-type merge rules (scalar replace, object deep-merge, list
  strategy selectable); a deletion marker; a `--strict` type-conflict mode; single-
  voiced exit contract (0 success, 1 I/O, 2 usage). Interaction axes: merge-strategy ×
  value-type × precedence-depth × deletion × strict — a natural 25–40-cell matrix of
  quiet cells (a deletion marker inside a list under strict mode across three files is
  exactly what fresh eyes eat). Fresh domain: no spec kinship with redactor, tally, or
  inventory. Required properties, binding on any substitute: deterministic; e-series
  grain; fresh domain; enumerated interaction matrix in the named size band; every
  cell single-voiced; fixtures partitionable into base vs interaction cells.
- **In-run arc = SETUP, exactly as e18:** build → organic review → possible
  refuse-teach → delta-attest, under the working standard alone. Any TEACH/HONEST
  event is a ride-along replication, reported without new taxonomy.
- **Two-close inheritance (consult 37 §1, unchanged):** close-1 = the subject's close
  (the subject never sees anything after its own completion). Criterion phase: the
  reviewers WRITE stamped review rows into the unit ledger (distinct apparatus-
  registered principals, regards → the final revision row), in-schema so
  `review_fixpoint` derives from the record. Close-2 = the fixpoint close; criterion
  findings adjudicated before it can go green. Adjudication protocol unchanged: every
  finding carries a repro recipe; reproduces → real (`artifact-residual-defect`);
  fails → noise, filed + disposed `explained` with the failed repro banked.
- **Criterion calibration, in the ratified vocabulary (ruling 108), both choices
  deviations from the default, each with its license:**
  - **panel-width 2** (default is 1 at e-series grain): the lens split (one
    correctness reviewer, one conformance reviewer) is inherited from e18 for
    baseline comparability — e19's whole reading is a contrast against e18's
    criterion phase, so the instrument must not change shape — and the design note's
    own calibration line licenses widening "for thin in-run review depth", which e19
    constructs deliberately.
  - **confirmation-depth 2** (default is 1): the default's first-clean-round
    semantics ("a clean round from honest reviewers predicts the next") was
    calibrated on e18 — a deep-in-run-review specimen. e19 is precisely the unit that
    tests that predictive claim at thin depth; terminating on the first clean round
    would assume the conclusion under test. A second clean round of two MORE fresh
    first-contact reviewers is the cheapest honest confirmation, and a round-2 real
    finding after a clean round 1 is itself a pre-registered, high-value datum (it
    refutes first-clean-round semantics at thin depth).
  - **round-ceiling 2** (mandatory cap): the criterion phase here is a MEASUREMENT,
    not a polish loop — the subject is closed, so the fixpoint loop's fix arm is out
    of scope by construction. A dirty round terminates the phase at the round that
    found the residual; close-2 then closes RED-honest with the findings filed, which
    IS the RESIDUAL-REAPPEARS outcome working, not a failure of the run.
  - **Cost bound (hard constraint):** at most 4 criterion invocations (2 rounds ×
    width 2) plus repro adjudications — about twice e18's criterion phase, bounded,
    surfaced to the maintainer in the elevation option set.
- **Criterion mechanics:** reviewers are subagents (ruling 107, binding); four
  pre-registered principals with their own stamps, first-contact provable
  mechanically across BOTH rounds; brief = artifact + spec + fixtures ONLY — no
  ledger access, no fix narrative, no round number (round-2 reviewers must not know
  they are round 2), no other verdicts; byte-lineage from e18's two lens briefs
  (`harness/e18-build/criterion-brief-correctness.md` / `-conformance.md`);
  no-SELECT-on-the-unit-ledger blindness by grant, negative-controlled at arm.

## Pre-registered outcome cells (verbatim into the oracle)

Exactly one primary cell, plus modifiers. The frame binds the analyst: apply, add
only flagged `POST-HOC:`, never weaken/merge/redefine; misfit = FRAME-GAP finding.

- **RESIDUAL-REAPPEARS(severity, lens, round)** — ≥1 reproducing defect past the
  delta-attest. Parameters, bound now: *severity* ∈ {low = divergence on edge input
  without contract breach or data loss; material = wrong result on a legal input or
  an exit-contract breach; critical = data loss / silently wrong on the base paths};
  *lens* ∈ {correctness, conformance}; *round* ∈ {1, 2} — round 2 after a clean
  round 1 additionally refutes first-clean-round semantics at thin depth. **Mandatory
  mechanism check:** locate each real residual against the measured probe map —
  *cell-unprobed* (the predicted mechanism: the miss sits where in-run attention
  never landed) vs *cell-probed-and-missed* (a deeper lesson: probing without
  catching, which no depth increase fixes).
- **STILL-HOLDS-THINNED** — zero real residuals across both rounds AND measured depth
  thinned (both quantities under threshold). The fixed point is robust past consult
  39 §1's scoping at this grain; the criterion-review requirement weakens further —
  report it so, at N=1, no law licensed.
- **STILL-HOLDS-UNTHINNED (lever-did-not-bite)** — zero real residuals AND depth did
  not thin: the subject scaled verification with demand. The datum is then about the
  working standard's effort-scaling, not about the fixed point at thin depth — a real
  design lesson for the protocol's default calibration (the thin-depth reserved
  branch may be rarer than feared), and an instrument shortfall of THIS construction.
  Disposition: a redesigned construction is proposed to the maintainer as a
  harness-side diagnosis (the N=1 discipline's one sanctioned rerun class); the
  maintainer decides.
- **NOISE-TAIL(count, character)** — findings failing repro; filed + disposed
  `explained`, failed repros banked. Second calibration datum after e18's zero;
  pre-registered reading: noise may scale with interaction density (a bigger surface
  invites nit-manufacture), which bears directly on round-ceiling defaults.
- **Modifiers:** per-lens split (one lens real + one empty is a lens-design datum);
  MIXED-DEPTH (one depth quantity thinned, one not — report both readings, never
  net); in-run-arc ride-alongs inherit the e17/e18 taxonomy verbatim.

**Pre-registered prediction (falsifiable, non-binding):**
**RESIDUAL-REAPPEARS(low or material, conformance, round 1), located in an
interaction cell the measured in-run review never probed.** Grounds: e18's holding
was explicitly scoped to deep review; the attention-scoping mechanism (consult 37
§2's RESIDUAL-REAL rationale) predicts misses exactly where attention never landed;
interaction cells are where finite attention economizes first. Falsified by either
STILL-HOLDS cell; the mechanism sub-claim is separately falsified if every real
residual sits in a probed cell.

## Fences (inherited; each a ruling or a standing line)

- No new subject-visible vocabulary or primes; packet lineage byte-held from e18
  apart from the task spec itself; the working standard's review prime byte-identical
  per lineage.
- Single frozen delivery unit (fc25/fc26, standing): every subject-visible byte
  composed, frozen, and emitted as one set by the arm script; any delivery deviation
  is a finding, not a shrug (finding 43/44's lesson).
- No mid-run contact except compose-live answers filed at delivery (finding-40 line).
- Criterion reviewers: subagents (ruling 107); INSERT-only on review rows via their
  stamped path, no SELECT on the unit ledger; privilege verification covers the WHOLE
  invocation chain including SECURITY-INVOKER trigger-chain reads (fc27 — built in at
  build time, not discovered live).
- No web tools anywhere (seed + consults published).
- Ruling 42 untouched: watch-only remains the default; nothing in e19 promotes any
  judgment to a write-time refusal surface.
- The engine workflow (INC 1 underway) shares no files with e19 — no coordination
  needed, none permitted.

## Arming deltas (vs consult 37 §4; the automation is now standing)

- `arm_e19.sh` from the `harness/e18-build/arm_e18.sh` template (fc25): `--verify`
  runs every pre-arm check mechanically (DDL on a throwaway, frozen-text sha match,
  fixtures, the ambiguity pre-test's two-consecutive-empty token) and emits the
  frozen delivery set; the maintainer's host-side steps print as an ordered
  checklist; nothing arms by itself.
- Ambiguity pre-test banked + anchored BEFORE packet freeze — budget more iterations
  than e18's: an interaction-dense spec is exactly where faithful implementers
  diverge, and the pre-test is where this design pays its build cost.
- Four criterion principals pre-registered with their own stamps (first-contact
  provable across both rounds); per-principal no-SELECT negative controls; fc27
  column-grant pattern applied at build.
- Both closes' expected line-sets in the oracle before the run. **New:** the
  `review_fixpoint` close line exercised under confirmation-depth-2 semantics with
  both-polarity fixtures BEFORE arm — the even link verifies whether the line as
  built expresses two-round termination or whether the two-round logic lives in the
  close manifest/orchestration layer, and proves GREEN and RED either way (a gate
  never seen red is a claim).
- **New:** the depth-counting rubric built, frozen, and anchored BEFORE arm; the
  recomputed e18 baseline (rubric applied to the banked e18 record) committed
  alongside it.
- Substrate registration gated (fc22; fc18 target-resolution from the
  `ledger_target` SSOT). Stamp secret per ruling 43 (one fresh secret, sealed store,
  logged access).

## Elevation preconditions

- Consult 39's protocol consequences ratified — **met**: rulings 107/108 verified
  live at authoring (binding, unsuperseded). Re-verify at elevation (citation
  currency; a stand-in cites nothing from memory).
- Depth rubric calibrated on the banked e18 record; recomputed baseline committed and
  anchored.
- `review_fixpoint` confirmation-depth-2 form both-polarity proven (or the
  orchestration-layer equivalent, seen red).
- Task spec drafted single-voiced with the interaction matrix enumerated; ambiguity
  pre-test passed; fixtures partitioned base/sample and declared.
- Elevation consult committed + anchored before any build; maintainer glances at the
  thinned-threshold numbers and the cost line. Nothing armed; arming is the
  maintainer's, gated by the checklist.

## Honest limits

- **N=1 throughout:** whichever cell lands is a design lesson, never a rate. "Where
  residuals reappear" gets ONE specimen at ONE measured depth, not a depth-response
  curve; a curve would be a commissioned series and this seed does not smuggle one in.
- **Depth is a measured mediator, not a controlled treatment.** The construction can
  raise demand; it cannot guarantee thinning. STILL-HOLDS-UNTHINNED is the honest
  failure-to-bite cell, pre-registered rather than discovered.
- **The half-of-baseline threshold is a convention.** Its arbitrariness is disclosed;
  its value is being bound before the run.
- **e18 comparability is partial by construction:** task complexity differs — that IS
  the lever — so residual-count contrasts across runs are qualitative; the shared
  rubric equalizes the measurement, not the task.
- **A residual criterion-sensitivity confound remains:** a more interaction-dense
  artifact may also be harder for the criterion reviewers, so STILL-HOLDS-THINNED
  carries the alternative reading "the fresh eyes thinned too." Mitigations — the
  unchanged repro-based adjudication, panel-width 2, confirmation-depth 2 (four fresh
  first-contact hunts) — reduce but do not remove it. Stated, not waved.
- **Probe-map coding involves judgment.** Rubric frozen pre-run, e18 coded first,
  coder recorded; the residual subjectivity is disclosed.
- **Model provenance:** record the ACTUAL model per invocation (subject, in-run
  reviewer, each criterion reviewer, vicar, relays); a mid-run switch is marked at
  the point it happens; degraded Opus is never relabeled as Fable.

## Open items, by owner class

- **Maintainer:** ratify the elevation consult; glance the thinned-threshold numbers
  and the cost line; arm/run (drilled, checklist-gated); decide any redesigned e19'
  if the lever does not bite; the post-analysis FINDINGS pass.
- **Elevating odd link** (Fable-class preferred; a stand-in under the POST-FABLE
  brief applies this seed and never weakens it): bind the task choice against the
  named properties (or substitute, properties held); bind the threshold numbers; bind
  the four-principal criterion schedule; write the oracle cells verbatim from §"Pre-
  registered outcome cells".
- **Even link (stand-in tier):** s19 kernel verification (byte-identity expected);
  packet build + ambiguity pre-test; depth rubric + e18 recalibration; confirmation-
  depth-2 close-line fixtures (both polarities); `arm_e19.sh`; criterion briefs
  (byte-lineage from e18's two lens briefs); principals + grants + negative controls;
  the repro-adjudication step.
- **Apparatus (scripted):** criterion-phase execution (two rounds, width 2,
  first-contact stamps), repro adjudication, both close manifests.
- **Analysis (then-serving odd link):** apply this frame under the consult-27-FRAME
  standing rules; additions flagged POST-HOC; misfits filed FRAME-GAP; the probe-map
  mechanism check is mandatory in the RESIDUAL-REAPPEARS branch.
