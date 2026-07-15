# BUILD-PLAN — phased increments and the experiments ledger (2026-07-02)

Companion to `DESIGN.md` / `INTERFACE.md` / `KB-CODESIGN.md`. Each increment is cut to
be buildable by an Opus-tier agent against the existing stack (model-tiering: drudgery
to Opus/Sonnet; the deductive-engine main loop stays Fable's), ends on a deployment
surface, and carries witnesses at the strongest surface currently deployable
(ADR-0013's 2026-07-02 amendment). Honest scope of "effect-level" here: through
increment 4 the re-observed effects are the measured residue and the adjudication
wire — the trial surface where the complaints were produced. The purpose's ultimate
effect (a hook changing a collaborator's behavior in-session) first becomes
observable at increment 5, when the payload has earned the shell. Every gate obeys ADR-0011's 2026-07-02 legs: negative control (seen red
first) and shipped binding (the default path, not a convenient seam).

**The deployment surface, named honestly.** The hook shell remains unbuilt by ruling
(HOOK-DESIGN §4b: the payload earns the shell). Until it exists, the deployment
surface is the one the trial series already runs on real transcripts: the
`hook_trial.py` driver over both corpora (the pinned 222-universe subagent corpus +
the live main-session corpus), with findings landed in `contra.finding` for the
adjudication widget — the consumer of record. An effect first observed there (the
54-survivor residue; the zero-recall known positive) is re-observed there.

---

## Increment 1 — attack the residue, move the recall needle (Opus-buildable)

**Scope: three levers, all behind the extension law (None ⇒ control arm, pinned).**
(A pre-work docstring fix planned against the inventory's `logic_backend.py:40`
hazard was struck after fresh verification: the shipped file already states the true
dependency posture — the hazard is remediated. Recorded so the strike is visible,
not silent.)

1. **Same-sentence shred foreclosure.** A claim pair with `span_a == span_b` (one
   sentence shredded into two claims) joins no rule. This is an extraction-side
   defect the GLiNER report names "better foreclosed upstream"; foreclosing at the
   pair-join is the honest v1 (upstream extractor surgery is a bigger blast radius,
   filed, not smuggled). Kills 28/54 survivors mechanically.
2. **Interrogative/mention mood gate v0** (INTERFACE §2): parse-feature classifier
   (`?`-final / aux-inversion → INTERROGATIVE; quotation-coverage → MENTION), the
   universe guard, detection-vs-presentation preserved (excluded claims stored, not
   joined). Targets the 8 mood/mention survivors; E-1 decides whether the guard gates
   or only annotates.
3. **The dimensioned-quantity lane, `R-QTY`** (INTERFACE §4): `parse_quantity` +
   the `Dimension` table + the Python oracle predicate + the Z3 encoding +
   `cross_engine_differential` wiring. `parse_quantity` reads the unit token from
   the sentence surface (verified present for the known positive: "874 MB" /
   "2.9 GB"); GLiNER corroborates, never gates (DESIGN F3). **This is the lever
   singled out by the commissioning:** it is the only designed mechanism that can
   reach the 874 MB / 2.9 GB pair — the sole known-live positive, at zero recall in
   every measured arm, unreachable by any subject-keyed rule because the two
   statements' subjects never share a key. Stated with the tension DESIGN F3 names:
   a subject-derived regime key re-inherits that same non-sharing and misses the
   pair; only the dimension-weighted configuration reaches it, at an unmeasured
   noise cost. The increment therefore runs E-2 **inside** itself: both join
   configurations, the known positive as the recall probe, the kill condition as
   the noise probe. Everything else in the plan is precision; this is the one
   recall instrument, and what it delivers is the measurement that decides the
   join key — not a pre-asserted recall result.

**Deployment + witnesses (effect-level, each with its negative control):**

- **W1 (recall, the headline — a measurement, not a promised result):** E-2 run on
  the live main-session corpus, both join configurations. Reported: does the known
  positive join in each configuration, and at what candidate volume. The honest
  possible outcomes are (a) the pair joins under a configuration that also passes
  W3 — the needle moved; (b) it joins only under the noisy configuration — the
  regime key is the named next lever, with data; (c) it fails to join at all —
  the extraction of one of the two statements is the defect, localized. Each
  outcome is a deliverable; only (a) is a recall win. Negative control: dimension
  lane off ⇒ the pair is absent and the control arm reproduces bit-identical.
- **W2 (precision):** trial rerun (schema `hook_trial/v5`), both corpora: the
  54-survivor set shrinks with **every removal attributed to its lever** in the
  per-finding dispositions (the established hand-read discipline), and the control
  arms reproduce bit-identical (the standing definition-of-done gate).
- **W3 (noise geometry of the new lane):** R-QTY's candidate volume per corpus is
  *measured and reported* — this is experiment E-2 running inside the increment.
  Kill condition, stated up front: if dimension-join yields > 5 candidates per
  main-session universe at 0 real beyond the known positive, the lane ships
  detection-only (stored, never injected) until the regime key is strengthened.
- **W4 (adjudication wire):** v5 candidates land in `contra.finding`; the widget
  renders them (the consumer-of-record path exercised, not assumed).
- **Gates:** GOLDEN fixtures per DESIGN §3 (the survivors as fixtures; the planted
  contradiction fixture must keep firing); MUTATION on the dimension/τ tables and the
  mood guard; DIFFERENTIAL oracle-vs-Z3 for R-QTY; all new code `mypy --strict`;
  `tools/no_lazy_imports.py` zero violations.

**Out of scope, explicitly:** the hook shell; KB writes; ASP changes; GLiNER label
changes; any extractor surgery beyond the pair-join foreclosure; any blocking
disposition.

## Increment 2 — temporal supersession (`R-SUP`, F1)

`ClaimContext.provenance.turn_index` through the trial driver; `at/2` +
`supersedes/2` EDB in `contra_asp.edb_from_claims`; the R-SUP default in
`logic_layer.lp` (+ mutation coverage); the Python oracle counterpart; the
`fde_z3.py:111` assert→raise fix rides along (INTERFACE §7). Witnesses: the 3
temporal survivors and the six catalogued main-session temporal duplicates convert
from R-NEG noise to R-SUP records on the v6 rerun; R-NEG main-session density drops
measurably; negative control: no ordering facts ⇒ bit-identical R-NEG control.
`R-SUP-ESC` ships as the SQL-view floor (hedge columns required — the Hedge v0
marker list is part of this increment).

## Increment 3 — the KB ledger + stratified universes (F5, identity, L2's substrate)

The `kb` schema (KB-CODESIGN §3) + the schema-parity gate (shipped with the DDL, seen
red on a mutated enum first); `ClaimHandle`/`FindingIdentity`; the scrub-before-hash
ingress (`_SCRUB` promoted to a shared home); `ClaimUniverse` with construction-time
refusals; the trial driver writes the ledger (idempotency witness: re-run ⇒ zero new
rows, `seen_count` bumps). The L2 cross-check (session claims × current-belief view)
becomes runnable here. Cross-role universes stay gated on E-1's mood verdict, as ruled.

## Increment 4 — the WHY-ledger, ordering, and unsat-core (F6, F7, concern 3)

`kb.mandate`/`kb.why_event` + `kb.why_orphaned` view + the R-WHY ASP rule
(differential vs the view; the impedance arc as the golden fixture, including the
retirement-with-witness retraction). The work-unit/discharge tables **iff ratified**
(KB-CODESIGN §5), with R-ORD over the hook's own mechanical events first.
Z3 `unsat_core()` over typed substrates — first target: venv version collisions
(concern 3's own example; the constraint rows are derivable from `pip freeze` +
requirement specs mechanically), second: `AdvertisedLimits` axes vs a client plan.
Never over prose ADRs (ruled caveat).

## Increment 5 — supply (F9) + the standing-experiment tail

Typed-key retrieval over the KB's supply indexes + the salience gate (novelty vs
stored findings); handle+gloss injection format; the F4 calibration routing
(unresolved gluts → `kb.calibration`). E-3 (handle A/B) and E-6 (abductive supply)
run here if their prerequisites earned it. This increment is the first one whose
deployment surface *should* be the hook shell itself — by then the payload has
either earned it on the trial surface or the plan stops, which is the honest exit
the sequencing ruling built in.

---

## The experiments ledger (decisions by experiment, each with a kill condition)

| id | question | method | kill condition |
|---|---|---|---|
| E-1 | Does parse-feature mood typing reach gating precision? | hand-label ~200 units across both corpora; measure v0 | INTERROGATIVE+MENTION precision < 0.9 ⇒ annotate-only, no gating |
| E-2 | R-QTY join key: which configuration (subject-derived regime key vs dimension-only) reaches the known positive at acceptable noise? | inside increment 1 (W1+W3): both configurations, recall probe + noise probe | > 5 candidates/universe at 0 real beyond the plant ⇒ that configuration ships detection-only |
| E-3 | handle+gloss vs inline content in injected context | A/B on token cost + downstream task fidelity (dossier §5's own framing) | neither asserted until measured |
| E-4 | Can mandate/WHY rows be extracted from prose at all? | seed from authored rows; attempt extraction on the impedance sessions; compare | precision < authored-row quality ⇒ authored-only stands |
| E-5 | CLP(FD) vs clingo when ordering acquires numeric domains | first real scheduling need encoded in both (SWI CLP(FD) is on host); compare legibility + latency | decided by the comparison, recorded in DESIGN §3-F7 |
| E-6 | Abductive supply (what missing fact makes the plan sound?) | the research corpus's specified abductive-ASP experiment, on KB-era data | no candidate quality over typed retrieval ⇒ retrieval stands |

## Standing constraints on every increment

- Sub-agent tiering per the standing directive: increments are Opus commissions;
  auditors Opus/Sonnet; never Fable.
- Background/workflow agents commit locally, never push; ephemera persisted via
  `tools/persist_claude_ephemera.py` after workflow activity.
- Budgets: every engine call deadline-carried (INTERFACE §7); enrichment cost
  (~105–110 ms/sentence measured) budgeted per corpus sweep as increment 1's runs
  already had to (the 883 s / 798 s coverage-first precedent, declared, not hidden).
- Substrate discipline (ADR-0015): trial sweeps declare envelopes; heavy runs staged
  to disk, never tmpfs.
