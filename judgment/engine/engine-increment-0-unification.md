# Engine increment 0 — UNIFICATION (the one increment before any content)

**Status:** design for maintainer review. No code, no DDL beyond illustrative sketches.
**Commission:** the critic's structural mandate §1 (`consults/engine-panel/critic-completeness.md`):
"four designs minted four registries, four verdict vocabularies (QUARANTINED means four
subtly different things), four names for the frontier, four build orders. One authority
module, one vocabulary, one merged increment plan — before any content increment."
This document is that unification. It settles nothing the seed reserves for content
increments; §7 registers what it deliberately does not settle.

**MODEL-SERVED (self-report):** claude-fable-5 — per this session's own system context
("You are powered by the model named Fable 5. The exact model ID is claude-fable-5").
Per the model-provenance-honesty rule: I have no introspective channel that could detect
a silent mid-run substitution; no degradation event was observed this invocation. This is
the same caveat every panel document carried, and it binds this one identically.

**Record basis:** read in full this invocation: `consults/engine-design-SEED.md`; all ten
files under `consults/engine-panel/` (four designs, four refutations, critic, decision
brief); `claude_harness/docs/design-notes/deductive-engine-fable-main-shape.md`;
`claude_harness/experiments/fact-mining/docs/LEDGER-LOGIC-MARRIAGE.md` (body + Appendix A,
incl. the §8 recorded amendment citing acts.ruling id 42); ADR-0000, ADR-0012, ADR-0013,
ADR-0014 in full. Rulings 42 and 43 verified live against `acts.ruling` at authoring time
(both `binding`, `human:maintainer`, 2026-07-07) — record-observed at the moment of
citation, per F42/F46, because the evaluation refutation's flaw 1 proved what citing repo
state from memory costs.

**Rulings this document builds under (cited by id, both verified):**
- **acts.ruling 42** — deny-surface Option B: watch-only is the DEFAULT; a specific
  engine judgment may be promoted to a write-time refusal ONLY with, per judgment:
  (1) a captured real specimen; (2) proven verdict-equivalence at the same frontier;
  (3) a teaching message naming the honest alternative; (4) individual maintainer
  ratification. The e17 stamp gate is the template. Amends marriage §8 by recorded
  ruling, default retained verbatim.
- **acts.ruling 43** — stamp-secret retention: one fresh secret per run; retained in a
  sealed store; every access itself a logged event (G12); the arrangement declared in
  the conformance honesty sheet (I12).

**Binding amendments and mandates:** the seed's "Binding amendments from the refutations"
and "The critic's structural mandates" sections are LAW for this draft. None is weakened
here; where one is instantiated, the instantiation is cited back to it.

**Decision discipline:** every judgment call this document makes where two designs
conflict and neither the seed nor a ruling settles it is marked `[INC0-DECIDED: Dn]` and
indexed in §8, so the maintainer can scan the complete set.

---

## 1. ONE judgment registry (unifying four)

The four registries to unify (critic §1): the semantics design's `judgment_authority.py`
(§4.1), the architecture design's judgment registry (§3 / increment 1), the evaluation
design's expectations-ledger authority (§2), the adversarial design's
`judgment_register.py` JudgmentSpec (§2.1).

**[INC0-DECIDED: D1] One authority module, two record kinds.** The four registries are
not four copies of one thing; three of them describe judgment *classes* and one
(evaluation's) describes expected *instances*. Forcing them into one row type would be
the CellLedger category error (ADR-0000 Specimen 2). So: **one authority module**
(`judgment_registry.py`, fact-mining side, kb_ledger idiom — ADR-0012 P1, one home) that
owns **two record kinds**:

- **JudgmentSpec** — one row per judgment class (the union of the semantics /
  architecture / adversarial registries, field-justified below);
- **Expectation** — one row per expected instance on a named substrate (the evaluation
  ledger's shape, unchanged in role), carrying a **foreign key into JudgmentSpec** — an
  expectation for an unregistered judgment is unconstructible (ADR-0000 Rule 1).

From this one module are generated: the DDL for both stores, the `.lp` law constants,
the per-family verdict enums (§2), the aggregation mapping tables (§2), the close-manifest
line set, the human-readable registry document, and the parity tests that pin the live DB
against the module (the established Python-authority / generated-DDL / live-parity
discipline). Nothing else hand-authors any of these — the critic's "four hand-synced
homes for one truth" is thereby the shape this section forbids.

### 1.1 JudgmentSpec — the field union, every field justified

| Field | Needed by | Justification (cite) |
|---|---|---|
| `judgment_id` | all four | the join key everything else hangs on; minted once, no aliases (semantics §5 drift guard) |
| `family` (A–H) | semantics §2 | the eight-family taxonomy is the vocabulary's organizing register, incl. Family H (non-derivability) as first-class (semantics §2, seed survivor list) |
| `verdict_enum_ref` | semantics §1/§2, adversarial §2.1 | per-family closed enum, generated (§2); a shared boolean is the F49/I9 lie |
| `subject_ref_type` (row / row-set / edge / clause-fragment / span / stream-pair / meta) | semantics §1; refute-semantics flaw 6 | typed SubjectRef is what makes the F44 two-truths case representable (§4.2) and identity computable (§4.1) |
| `law_citations[]` (namespaced keys, §1.3) with per-citation **ratification depth** {RULING(id), FIND, BRIEF-INV, ADR} | semantics §4.1/§4.4, adversarial §2.2, main-shape commitment 4 | law-cited derivation is a pre-committed convergent commitment; ratification-depth marking is the seed's binding sequencing device (census before refusal, §5 INC 1/INC 3) |
| `engine` (SQL / ASP / SMT / FDE-lens / shell / none-router) | semantics §2, adversarial §2.1, marriage §4 | assign-don't-compete, upheld by every lens |
| `second_producer` (or declared none-with-reason) | adversarial §2.1 `floor_producer`, architecture §7 | the differential is per-judgment declared, never assumed; a declared absence is an I12 row, not a silence |
| `complexity_class` (A / B / C / C_t / D) **as checker output** (checker version + rule-text hash) | architecture §2.1; refute-architecture flaw 2 | the theorem holds, the hand classification is disqualified by specimen (`launder`); the field stores what the mechanical checker derived, and a hand-asserted class is unconstructible from INC 3 on |
| `edb_availability` / `substrate_needs[]` (capability-manifest keys) | architecture §2.2, adversarial §2.1/§2.3 | availability is orthogonal to class; EXCLUDED must be *derived* from manifests, not hand-asserted (A.2 generalized) |
| `tier_placement` (authoritative = T2; shadows listed) | architecture §1/§3 | the authority rule: lower tiers are shadows that must reconcile; a shadow that cannot be reconciled may not exist |
| `promotion_stage` (P0–P5) + per-stage evidence refs | architecture §6, semantics §6 | **[INC0-DECIDED: D2a]** the semantics "mode ceiling" and the architecture promotion stage are one axis; P0–P5 subsumes the ceiling (a judgment's ceiling *is* its current stage), so the ceiling column is dropped as a separate field with this note |
| `ruling42_ratification` (NULL, or the acts.ruling id ratifying this judgment's deny promotion) | ruling 42 | the registry is where "the only path to a deny surface" is enforced as a type: a P4 stage with a NULL ratification id is unconstructible |
| `goodhart_surface` (subject-controlled vs subject-uncontrolled input facts; where priced: the invariant witness verified) | adversarial §2.5; refute-adversarial flaw 6; refute-architecture salvage (P3) | controlledness is **not** syntactic (the refutation is right); the field records the P3 analysis and the named invariant witness — an honest review artifact, not a mechanical guarantee, and the registry row says so (refute-architecture flaw 6's repair: stop advertising P3 as mechanical) |
| `fixtures[]` + `mutations[]` (each mutation names the verdict it flips) | all four | ADR-0011: a gate never seen red is a claim; the rules × mutations completeness registry (evaluation §3.2) reads this field |
| `red_history` pinned to (judgment_id, rule-text hash, engine version) | adversarial §2.6; refute-adversarial lesser flaw | UNPROVEN-NET display needs version-pinned red history or a rewritten rule inherits a red-date it never earned |
| `teach_text_ref` + version (where compiled) | architecture P4(iv), adversarial §2.5 | frozen, versioned, specimen-tested; changing it is a versioned apparatus change |
| `assumptions[]` (each with its invalidating condition) | adversarial §2.8 (I7 row) | the engine's own assumptions carry validity bounds |
| `adjudication_slot` (bool + routing target) | semantics §2 (families D/F), critic §3 | which flags carry a defeasible human-adjudication slot, and where a ruling lands (wired to `experiments/adjudicate/` — design owed, §7 OQ9) |
| `exclusion` (reason, where family H / EXCLUDED) | semantics §2.1, adversarial §2.1 | EXCLUDED requires a manifest- or census-drawn reason; ad-hoc exclusion unconstructible |

**Dropped fields, with notes:**
- semantics §2's `Monotone?` column — subsumed by `complexity_class` (A/B/C/C_t/D is the
  same information, finer, and checker-derived; two homes for one fact is cancer B).
- semantics §2's `Strict/defeasible` column — the two-tier rule (semantics §3.5: all
  derivation strict given EDB; defeasibility lives in the data) makes this a constant
  plus the `adjudication_slot` flag; the flag is kept, the column is not.
- architecture §3's prose "syntactic justification" for the class — replaced by the
  checker-output provenance (a hand-written justification is exactly what flaw 2 caught).
- evaluation §2's `tier (1/2/3)` — belongs on Expectation rows (it grades evidence for an
  instance, not a class); kept there, not on JudgmentSpec.
- adversarial §2.1's `availability (live|close|both)` — subsumed by `tier_placement` +
  `edb_availability` (it was the same fact spelled a third way).

### 1.2 Expectation — the instance ledger (evaluation §2, adopted with its refutation's repairs)

`{expectation_id, judgment_spec_fk, substrate_id, frontier (§3), expected finding
signature or output hash, tier (1a/1b/2/3 — see D19), provenance (namespaced law key /
consult / DerivationRecord hash), apparatus_config (armed-state provenance — critic §6),
status}`. Append-only; corrections are quote-and-strike `supersedes` rows.

Two repairs bind, both already seed law:
- **No automatic re-keying ever** (seed survivor list, amending evaluation §2 per
  refute-evaluation flaw 5): an upstream-superseded provenance flips the row to
  SUPERSEDED, which **blocks green until a human re-keys**. Auto-re-key is F28's
  auto-resolve one level up; the launder proof is the standing negative control.
- **DIVERGE_BY_DESIGN registration requires independent ratification** (binding
  amendment; refute-evaluation flaw 6): the mover never licenses their own flip.
  Owner of the license: the maintainer (pilot-F7 is the specimen). The registration row
  carries the ratifier identity, and a self-ratified registration is unconstructible.

**[INC0-DECIDED: D19] Tier 1 splits into 1a and 1b** (refute-evaluation flaws 3/4):
**1a — engine-stability anchors** (the five DerivationRecords: same-day, same-author,
birth-independence caveat carried on the row) vs **1b — independently-validated
instrument numbers** (the banked s9–s14 four-arm targets, `sweep-results.txt`). 1b is the
only non-circular Tier-1 duty and is scheduled, not just enumerated (§5 INC 2).

### 1.3 Law-reference keys are namespaced

**[INC0-DECIDED: D15]** The BRIEF register (F1–F16) and FINDINGS.md (F1–F53) collide on
the F-namespace, and "F11" is load-bearing in both (refute-evaluation, lesser flaw). Law
citations everywhere in the registry use namespaced keys: `RULING:42`, `FIND:F28`,
`BRIEF:F11`, `INV:I7`, `ADR:0000`. A bare `F11` is unconstructible as a citation.

### 1.4 The registry is itself append-only, with contest records

Per the binding amendment ("an append-only regold protocol with contest records") and
the adversarial refutation's flaws 4 and 7 (the register was "the one mutable,
non-append-only artifact in an architecture whose entire creed is append-only"; goldens
had "no contest record, no approver, no supersedes chain"):

- **JudgmentSpec rows are append-only and supersedes-chained.** A spec change is a new
  row superseding the old; the old row remains citable by every banked DerivationRecord
  that lawfully used it (I3 for the registry).
- **A regold** (any change to a banked golden/fixture expectation) **is an F9-shaped
  contest record**: the red it answers, the law citation authorizing the change, the
  approver — and the approver is never the mover (same independence rule as
  DIVERGE_BY_DESIGN; D2). Nothing structurally distinguishes a law-driven regold from
  evidence-adjustment *except* this record, so the record is mandatory.
- **The meta-toolchain enters the qualification perimeter** (refute-adversarial flaw 4's
  repair): the registry loader, manifest renderer, and close invoker each get negative
  controls — never-invoked close, empty-register load, deleted-spec — as registered
  fixtures like any judgment's (§5 INC 2 acceptance).

`[INC0-DECIDED: D2]` covers the three bullets above as one decision: registry mechanics =
append-only + supersedes chains + non-mover-ratified contest records, applied uniformly
to specs, goldens, and DIVERGE_BY_DESIGN registrations.

---

## 2. ONE verdict vocabulary

The four QUARANTINED meanings on the table (critic §1): semantics' per-family non-run
member; architecture's differential/tier-line verdict; evaluation's "the check did not
run"; adversarial's DischargeStatus member distinct from NOT-RUN and TIMEOUT.

**[INC0-DECIDED: D3] Four closed strata, one QUARANTINED meaning, defined once.** The
four vocabularies were describing four *layers*, not four candidate spellings of one
layer. Named apart, each stays closed and small; the drift the semantics design warned
about ("shared spelling with divergent meaning is how drift starts", §5) is closed by
giving QUARANTINED exactly one definition and letting the other three former meanings
take their own names:

- **S1 — family verdicts.** Per-family closed enums, generated from the registry
  (semantics §1/§2 as amended). `IN-FORCE`, `DISCHARGED(by)`, `CORROBORATED`, … — one
  enum per family, no global truth lattice, no member spelled QUARANTINED.
- **S2 — derivation status** (the total map; adversarial §2.1 adopted): per
  (judgment_id, frontier), `DischargeStatus ∈ {DERIVED(verdict∈S1),
  DERIVED-EMPTY(grounding-witness), NOT-RUN(reason), TIMEOUT(budget),
  QUARANTINED(cause), EXCLUDED(manifest-reason)}`. Totality over the registry makes the
  F49 class unconstructible at close; DERIVED-EMPTY requires the per-rule grounding
  witness (binding amendment — the pilot-light atom is retired as refuted,
  refute-evaluation flaw 2; clingo warnings promoted to RED are the floor).
- **S3 — comparison verdicts** (the ratified differential vocabulary, unchanged
  spelling): `{AGREE, DIVERGE_BY_DESIGN(named-moot-or-registration),
  DIVERGE_DEFECT, QUARANTINED}` for every producer-pair and tier-pair line
  (T2-internal, tier_consistency, hook_fidelity, cache_integrity, acts_parity). An
  unnamed moot is DEFECT (architecture §7).
- **S4 — aggregation colors** (the close manifest's line vocabulary):
  `{OK, RED, REQUIRED-ABSENT, DECLARED-EXCLUSION(reason)}` plus the display marker
  `UNPROVEN-NET` (a property of a line, not a color — a wall of OKs over UNPROVEN-NETs
  looks like what it is; adversarial §2.6).

**QUARANTINED (one definition, owned by the registry module, cited by S2 and S3):**
*a derivation or comparison was attempted and produced output that must not be trusted*
— the A.8 empty-model class, a failed grounding witness, an unreconcilable shadow, a
missing refusal-journal entry. Never "didn't start" (that is NOT-RUN), never "ran out of
budget" (that is TIMEOUT). Evaluation's discharge-table QUARANTINED narrows to this same
definition; its former "did not run" reading maps to NOT-RUN.

**[INC0-DECIDED: D4] The per-family non-run member is generator-injected.** The binding
amendment demands per-family non-run members (refute-semantics flaw 1: six families
lacked one in the design's own table). Rather than trusting eight hand-written enums to
each remember it, the registry's enum generator **injects** a reserved member
`<FAMILY>_NOT_RUN(cause)` into every family enum — a family enum lacking it is
unconstructible (ADR-0000: foreclose the class, don't review for it). The member is the
projection of S2's non-DERIVED statuses into the family's verdict domain, so a consumer
that reads only the family-verdict column still cannot mistake silence for soundness.
One meaning, defined once at the S2 layer; namespaced spellings per the mint-once law.

**The closed aggregation mappings.** Cross-family aggregation happens through *declared,
generated, total* mapping tables — one row per enum member, and the parity gate fails if
any member of any stratum lacks exactly one mapping row:

- S2 → S4: `NOT-RUN | TIMEOUT | QUARANTINED → RED`; `EXCLUDED(manifest) →
  DECLARED-EXCLUSION(reason)`; `DERIVED(v) →` the family's declared S1→S4 map;
  `DERIVED-EMPTY → OK` *only with its grounding witness banked*, else QUARANTINED.
- S1 → S4: per family, declared in the registry (e.g. Family A `DEFECT(kind) → RED`;
  Family B `GAP(span) → RED at close` per D14; Family D flags → OK-with-flag-routed,
  the flag's own line carrying the count).
- S3 → S4: `DIVERGE_DEFECT | QUARANTINED → RED`; `AGREE → OK`;
  `DIVERGE_BY_DESIGN → OK, listed, with its named moot/registration`.

**[INC0-DECIDED: D5] Exactly one cross-family aggregation point.** Semantics said "the
close manifest, exactly one place"; evaluation's discharge table and adversarial's
self-conformance block are two more (critic §2, minor). Decided: the close manifest is
the one aggregation *authority*; the eval discharge table and the self-conformance block
are **generated views over the same S→S4 mapping tables** — registered consumers, not
independent aggregators. A view computing its own color mapping is a parity failure.

**No-aggregate rule inherited unchanged** (evaluation §3.1): a summary may count; every
non-green row is named in the output; "47/50 green" without the three named reds is a
forbidden output shape.

---

## 3. ONE frontier concept — with the clock pinned inside it

Four names for one concept (critic §1): semantics' *frontier*, architecture/adversarial's
*watermark*, evaluation's *as_of*, architecture's *prefix ≤ W*.

**[INC0-DECIDED: D6] The canonical concept is `Frontier`, and it is a vector plus a
pinned clock:**

```
Frontier ::= ( streams : { stream_id → max_id },   -- every stream the derivation read:
                                                   -- ledger lineage, acts, law register,
                                                   -- judgment store where consumed
               now     : PinnedClock )             -- the evaluation instant, hash-covered
```

- **The clock is a component of the type**, not an ambient input — the seed's first
  binding amendment (refute-semantics flaw 2: expiry judgments are functions of
  (frontier, now); replay breaks without it). Every DerivationRecord hash covers the
  full Frontier including `now`; a C_t derivation that did not pin its clock is NO
  RESULT. Pinning makes replay exact; it does **not** make the clock trustworthy —
  Part-11's trusted-clock obligation stays open (§7 OQ8; critic §4).
- **The vector form subsumes the frontier-pair.** A cross-stream judgment's "frontier
  pair" (semantics §3.2) is simply a Frontier over two streams. What the vector does
  *not* supply is a sound total order **between** streams — that remains blocked (seed:
  "G5-class cross-stream ordering is BLOCKED until solved"), with the critic's
  `acts_live` shared-id-sequence observation as the candidate dissolution investigated
  at §5 INC 5.
- **Alias retirement.** `watermark`, `as_of`, `prefix ≤ W` are retired to
  citation-of-prior-documents only; new code and new rows say Frontier. The *semantics*
  each alias carried survives under the one name: hook_fidelity's "re-derive over the
  prefix ≤ W" becomes "re-derive at the finding's banked Frontier" (which, carrying
  `now`, also fixes the refute-architecture lesser flaw that C_t findings were
  under-specified by W alone); evaluation's STALE display rule becomes: a verdict
  presented behind the current Frontier renders `STALE(frontier=F, current=G)` — a
  display-honesty property, never an error (evaluation §5.2, kept verbatim).
- **[INC0-DECIDED: D7] Clock and identity.** The Frontier's `now` is replay-pinning,
  not identity-bearing. For time-indexed (C_t) families, the finding's identity
  discriminator is the **crossed bound** (e.g. the `valid_until` value whose passage
  flipped IN-BOUND→EXPIRED), never the raw clock reading. This is what makes
  "re-running on an unchanged record inserts zero rows" and "a lapsed bound yields
  exactly one new EXPIRED finding" *jointly* satisfiable — the pair refute-semantics
  flaw 2(b) proved contradictory as previously specified.

**[INC0-DECIDED: D13] Cross-stream confinement is uniform.** Until the acts_live
ordering question is resolved and ratified, **every** ledger-vs-acts judgment is
close-time-bound — Family F *and* Family B's contemporaneity gap-detection (the
refutation's "same inconsistency one row up", refute-semantics flaw 3). No cross-stream
judgment is scheduled at turn-time in increments 1–5.

**[INC0-DECIDED: D14] Currency-vs-gap polarity, scoped.** F42/F46's "currency is a flag,
never a gate" is a *citation-currency* ruling and stays exactly that. The BRIEF's
"M-trigger fired and entry absent = detectable defect" (I1) keeps **defect polarity**: a
GAP verdict may turn a close RED. What it never does is deny a write — that path exists
only through ruling 42's protocol. This resolves refute-semantics flaw 7(a) without
stretching either law past its specimen.

---

## 4. ONE FindingIdentity

Three incompatible schemes (critic §2): semantics keys storage on (family, subject,
frontier) + law; evaluation content-hashes (substrate, family, row ids) with no as-of;
the marriage §6.1/§6.2 donation is the unordered claim-pair plus a session-hash for
cross-session accumulation.

### 4.1 The unified scheme

**[INC0-DECIDED: D8]**

```
FindingIdentity ::= content_hash(
    substrate_id,     -- session-independent target identity via the ledger_target SSOT
                      -- name + lineage (the marriage §6.2 cross-session donation)
    family_id,
    subject_ref,      -- CANONICAL, TYPED (§4.2): sorted row-id set | ordered edge pair |
                      -- clause-fragment token | (stream, id-range) span | stream-pair
    law_ref,          -- namespaced (§1.3): two truths under two laws are two findings
    discriminator )   -- family-declared extras, closed per family:
                      --   C_t: the crossed bound (D7)
                      --   recurrence-prone families: the ONSET Frontier — the frontier
                      --     at which this signature transitioned false→true
```

- **The observation Frontier is NOT identity-bearing** — a persisting finding is one
  stored row re-observed at a new Frontier, never re-injected (marriage §6.1, kept).
  Semantics' frontier-in-the-key is dropped *as identity* (it re-keys every persisting
  finding every derivation — the re-nag the identity exists to prevent) and kept *as
  provenance* (every observation row carries the Frontier it was observed at).
- **The onset-Frontier discriminator repairs recurrence-blindness**
  (refute-evaluation, lesser flaw: a defect that moots and recurs over the same rows was
  indistinguishable from its original). A recurrence has a new onset, hence a new
  identity; an unbroken persistence has one. The refactor fixture (rename an atom →
  zero new rows) and the recurrence fixture (moot, then same-shape re-violation → exactly
  two rows) both enter the corpus (§5 INC 2).
- **The unordered claim-pair** (marriage/kb_why) is subsumed: it is the canonical form
  of an edge-shaped `subject_ref`, not a fourth scheme.

### 4.2 The F44 two-truths-about-one-row case, represented explicitly

The banked triple (row 5 in force; its load-bearing clause defeated) must never be
halved by dedup (refute-semantics flaw 6). Representation:

- Judgment 1: family C, `subject_ref = row(5)`, verdict IN-FORCE.
- Judgment 2: family C (aspectual lens consumer), `subject_ref =
  clause_fragment(scope_token(A, B, H))` — a **different SubjectRef type**, where
  `scope_token(AmendingRow, AmendedRow, ScopeHash)` is computed SQL-side (where
  `amends_scope` text lives) and exported as an **opaque token** to the EDB.
  **[INC0-DECIDED: D9]** — this closes the refutation's "the EDB withholds the subject"
  half: the ids-not-text law holds (a hash is an id, not text on the wire), and an
  ASP-side CLAUSE-DEFEATED judgment now has a constructible, stable subject.
- The two identities differ in `subject_ref`; dedup keyed on the full identity cannot
  drop either half. Both rows persist; the FDE lens renders the pair as `both` on the
  report side exactly as before (marriage §4 hard rule untouched); DTO fragments retire
  the token per-case as they land (the token is interim by the same clause the lens is).

**[INC0-DECIDED: D10] The per-subject functionality invariant, stated.** Two conflicting
verdicts of one family for one identical `subject_ref` at one Frontier are **illegal** —
a store-level invariant, checkable, RED on violation. F44 is legal precisely because the
subjects differ. This answers the refutation's "the store admits per-subject
contradictions with no declared semantics" with a declared semantics.

---

## 5. THE merged build order — increments 1–5, with acceptance criteria

Sequencing constraints honored, each from the seed's binding list: the **law census with
ratification-depth marking BEFORE any constructor refusal** (INC 1 before INC 3); the
**mechanical class-A checker BEFORE the prefix-determinedness theorem is relied on**
(INC 3 before the INC 4 shadow that leans on class A); **acts_live as the cross-stream
ordering candidate** (INC 5); the **review-queue-debt close line early** (INC 1);
**ruling 42's protocol as the only path to any deny surface** (no new deny surface exists
anywhere in INC 1–5; the sole armed trigger remains e17's, which is the ruling's own
template instance — **[INC0-DECIDED: D21]** it is grandfathered as already individually
ratified, and every future promotion goes through the four-part protocol with its
`ruling42_ratification` field non-NULL).

Two riders that bind the whole plan:

- **Hazard within reach, flagged loudly (mother's-life bar):**
  `instruments/run-core-a.sh` shells clingo with `2>/dev/null | grep -E 'SATISFIABLE'` —
  stderr silenced entirely, and the grep matches UNSATISFIABLE too
  (refute-evaluation flaw 1(b): "a live, unfixed F49-class silent-non-run inside the
  perimeter"). This is a plank with a nail in it. Fixed in INC 1, not deferred.
- **No regression trap:** `clingo_run.py` already carries the durable grounding-error
  fix (`_SOLVED_RESULTS` incl. `OPTIMUM FOUND`, raising otherwise; regression-tested).
  Every increment builds ON that landed fix; no increment re-prescribes a SAT/UNSAT-only
  guard (refute-evaluation flaw 1(a) — executing the evaluation design's §8 as written
  would break every `opt=True` consumer).

### INC 1 — The law census + the one registry (+ the debt line)

*(Merges: semantics inc 1's census half; architecture inc 1; adversarial incs 1–2's
register/law-diff halves; evaluation §2/M2's census frame. Stand-in buildable against
this document per the seed's division of labor; the census classification itself is a
maintainer-ratified scope ruling.)*

Build: the machine-readable law census — every FINDINGS F1–F53 entry, every BRIEF G/F/I
register row, every `acts.ruling` row, the load-bearing ADR clauses — classified
`{law-demanding-mechanical-implementation | observation/non-law | judgment-residue(J)}`
with namespaced keys (D15) and ratification depth `{RULING(id), FIND, BRIEF-INV, ADR}`.
The census closes refute-adversarial flaw 2 (the register-diff gate presupposed a
machine-readable law register that did not exist) *before* any gate reads it, and its
completeness is checked against the rulings stream (a ruling row absent from the census
is RED). Then: `judgment_registry.py` populated with a JudgmentSpec row for every
existing judgment — `ledger_tnow.lp`/floor `#show`s, the instruments, every close line,
the e17 triggers — with two-way parity (an implementation with no row fails; a row with
no implementation is RED-undischarged or a declared exclusion). Registry ledger
discipline (D2) live from day one. **The review-queue-debt close line ships here**: open
and aging unadjudicated flags counted per family, on the face of every close
(refute-adversarial flaw 9 — a green close over unread flags is the dressed-up-QED at
system level; the RED threshold is a later maintainer ruling, the *visibility* is not).

**No constructor refusal in this increment** — uncited rules land as loud
QUARANTINED-apocrypha census rows, not refusals (the refusal ships INC 3, after the
census makes it satisfiable — refute-semantics flaw 5).

*Accept:* census artifact committed with every entry classified and a maintainer
ratification slot; registry two-way parity green on the whole existing surface; the F49
negative control (delete a rule file → its judgment NOT-RUN → close RED) fires; the
debt line shows the true open-flag count on the banked e12/e17 records; `run-core-a.sh`
fixed (stderr surfaced, exact-match verdict parse) with a broken-program fixture proving
it now fails loudly; e17's gate recorded at P4/P5-pending with
`ruling42_ratification = RULING:42`-template provenance.

### INC 2 — Vocabulary strata + total map + Frontier + unified identity

*(Merges: adversarial inc 1's total-map half; semantics inc 2; evaluation §2's ledger
mechanics + M1's negative controls; the identity/frontier unifications of §§3–4.)*

Build: the generated S1–S4 enums and total mapping tables (D3–D5), with the injected
per-family NOT_RUN members (D4); the DischargeStatus total map over the registry; the
Frontier type (vector + pinned clock, D6) retrofitted through DerivationRecords; the
unified FindingIdentity (D8–D10) with the judgment store keyed on it; the Expectation
ledger re-keyed, SUPERSEDED-blocks-green wired (no auto-re-key); the meta-toolchain
negative controls (D2: never-invoked close, empty-register load, deleted-spec).

*Accept:* all banked s10–s13/nla derivations reproduce bit-identically modulo the added
Frontier/law fields; frontier replay of s10 reproduces the `in_force(4)` flip at
frontier 22 and nowhere else; the identity fixture quartet is green — refactor (zero new
rows), recurrence (exactly two rows), expiry (a crossed bound yields exactly one new
EXPIRED row; an unchanged record otherwise yields zero), F44 (both truths stored, dedup
drops neither, the functionality invariant D10 passes on them and fails on a synthetic
true-duplicate); every enum member maps exactly once in the S→S4 tables (parity);
**Tier-1b discharged**: the banked s9–s14 instrument numbers and `sweep-results.txt`
targets reproduce through the current engine (the only non-circular Tier-1 duty,
scheduled here per refute-evaluation flaw 4); the three meta-toolchain negative controls
each turn a close RED.

### INC 3 — The mechanical class checker + the citation constructor + grounding witnesses

*(Merges: the refute-architecture flaw-2 repair; semantics inc 1's citing-heads half;
adversarial inc 2; the binding amendments on grounding witnesses and the census-before-
refusal sequencing.)*

Build: the syntactic class checker over rule text (A/B/C/C_t/D) whose output populates
`complexity_class` (a hand-asserted class becomes unconstructible); per-rule grounding
witnesses, with clingo's unmatched-body-predicate warnings promoted to RED as the floor
(binding amendment; the pilot light stays retired); the law-citation constructor armed:
a judgment atom with no namespaced law term is unconstructible, **gate-feeding judgments
require RULING-depth citations, flag-only judgments require ≥ FIND depth**
**[INC0-DECIDED: D16]** — the depth marking is exactly what lets the live e17 gates
(RULING:28/29-backed) and the FINDINGS-only flag rules coexist without either refusing
the apparatus's own proudest exhibits or running uncited (refute-semantics flaw 5's
repair); the register-diff gate live over the INC 1 census (undischarged ratified law →
RED; apocryphal rule → QUARANTINED; superseded citation → RED).

*Accept:* the checker classifies every registered rule; the `launder` specimen classifies
**C, not A** (the banked misclassification catch — the checker must reproduce, from rule
text alone, exactly the error the flagship author made in public); an injected apocryphal
rule QUARANTINEs; a rule citing the overruled consult-19 clause-defeat direction reds as
superseded-law; the `amends`→`amend` body-typo fixture is caught by the grounding
witness on a substrate with no banked expectations for that family (the exact case
refute-evaluation flaw 2 proved the pilot light passes); all banked outputs reproduce
byte-identically after the retrofit (the id-keying retrofit is the worked precedent for
re-encoding under a standing net).

### INC 4 — Refusal capture + tier_consistency shadow + ruling-43 secret handling

*(Merges: architecture incs 2–3's shadow/journal halves as redrafted by their refutation;
the binding amendments on refusal capture and the HMAC dilemma, the latter now settled by
ruling 43. Retrofit onto the live e17 gate first — the one production trigger enters the
discipline before any new trigger is minted.)*

The refusal-capture mechanism, **proposed** (the seed reserves the build for "ONCE its
design is ruled"; this is the design put up for that ruling — §7 OQ11):
**[INC0-DECIDED: D17]** keep `RAISE EXCEPTION` (the e17-proven teach-refusal shape,
whose legibility is what converts — a silently-skipped row read as success would violate
I4 in the opposite direction); journal the refusal from the **interception-hook layer on
its own connection** (the hook already observes the attempted payload and the error);
the **in-record second witness is the consumed-id gap** (sequence defaults are consumed
before BEFORE-trigger abort) **plus the error trace in the acts stream**; a close-time
reconciliation line requires every consumed-id gap to match a journaled refusal and
every journaled refusal to reproduce under the T2 semantics — either direction
unreconciled is QUARANTINED. Atomicity story, stated: the journal write is
outside the aborted transaction by construction (own connection), and its loss window
(hook dies between refusal and journal write) is exactly what the id-gap reconciliation
catches. Honest residue, pre-registered rather than papered: writes bypassing the
interception layer journal nothing — per the standing threat-model scope the subject is
not modeled as a sandbox adversary actively evading the instrumented path; this residual
is declared in the conformance block, not silently absorbed.

Also in this increment: the **tier_consistency** shadow line (class A ⇒ any tier
divergence is DIVERGE_DEFECT — now trustworthy because classes are checker-derived,
INC 3); the **sealed secret store per ruling 43**: per-run secret retained, every access
a logged G12 event, the whole arrangement declared (I12). This dissolves
refute-architecture flaw 3's dilemma exactly as the ruling states: the T2 shadow
re-derives stamp *verdicts* from recorded stamp facts with the kernel-only residual
declared, and full HMAC re-verification decades later is possible via a sealed-store
access that is itself an audit event.

*Accept:* maintainer ruling on D17 obtained before arming (the design ships, the arming
waits); e17 fixture replay against an armed scratch kernel populates the journal through
the hook layer; the reconciliation line is green on the banked e17 record (row-15 id gap
↔ the act-498 typo refusal; the review-detail refusal per consult 35 §0's *corrected*
mapping) and red on a synthetic false-refusal and on a synthetic journal-suppression;
the sealed store exists with its access log demonstrably capturing a read; the
conformance sheet carries the ruling-43 declaration verbatim.

### INC 5 — The acts_live spike (the cross-stream ordering candidate) + parser qualification

*(Merges: architecture inc 8; adversarial inc 3's parser-qualification half; the seed's
"the critic's acts_live shared-id-sequence observation … deserves first attention".)*

**[INC0-DECIDED: D22]** Build as a **spike with a written adopt/abandon recommendation** (the architecture
design's codegen-spike idiom, applied here): apparatus-owned `acts_live` journaling from
the interception hook into the same Postgres; the investigation's core question is the
critic's dissolution — **one shared id sequence across ledger and acts writes**, giving
a total cross-stream order by construction, which would unblock G5
(approval-precedes-implementation) and Family B gap-detection at turn-time without
ts-ordering (banned, same-second specimens standing). The soundness memo must treat:
same-sequence semantics under concurrent writers, interleaving guarantees Postgres
sequences actually give, the retrofit story for the historical corpus (which has no
shared sequence — law-epoch-shaped, §7 OQ2), and the acts_parity gate. Parser
qualification rides along: version-pinned, parity-pinned against the persisted-ephemera
transcript corpus, parse-coverage floor, **plus a discovery-completeness obligation**
(a turn-count denominator independent of both hook and parser — refute-adversarial
flaw 8's repair: parity proves old formats parse, not that new files are found).

*Accept:* acts_parity AGREE between live-journaled acts and the close-time transcript
parse across one full experiment; a synthetically truncated transcript trips the
coverage floor; a relocated-transcript fixture trips the discovery-completeness line;
the adopt/abandon memo delivered with the cross-stream ordering soundness argument —
and Family F/B cross-stream judgments **remain close-time until the maintainer ratifies
ADOPT** (D13). Nothing consumes `acts_live` before parity holds on a whole run.

**Beyond INC 5 (sequenced, not scheduled here):** the turn-time hook build (T1 — see
D11 below), monotone caches + cache_integrity, latency ledger + first budget ruling,
the codegen spike under the N−1 independence bound (binding amendment: generate at most
N−1 of N encodings; the F-A `answered` twin-blindness is the banked specimen), replay
harness, self-conformance block, M3-style shadow run. Their relative order inherits from
the panel increments they came from; none precedes its INC 1–5 prerequisites.

### Cross-design contradictions settled by this plan (the critic's §2 list)

- **What runs at turn-time — [INC0-DECIDED: D11]:** the semantics headline "the same
  program text at three schedules" is retired as false-as-stated (its own refutation's
  flaw 4; critic §2). What is one across schedules is the **semantics**; producers are
  N **registered encodings**, each with its own JudgmentSpec producer row, mutation set,
  and reconciliation line (hook_fidelity for T1, tier_consistency for T0). A T1
  SQL-over-caches evaluator is a third encoding and is accounted as one — with the
  write-time rung additionally bound by ruling 42's clause (2): **proven
  verdict-equivalence at the same frontier**, per judgment, before any refusal
  (upgrading promotion criterion (i) from budget to equivalence — binding amendment).
- **Stored judgments vs never-stored T_now — [INC0-DECIDED: D12], argued, not assumed:**
  a banked judgment row is a **T_event fact about a derivation** ("engine V derived
  verdict X at Frontier F"), monotone and historical — not a materialized "currently
  valid". The reconciliation the critic noted nobody argued: (i) no class-C verdict is
  ever stored *as current* — the store's consumer view forces the STALE presentation
  rule (§3) so a reader cannot commit the e9 sin (reading T_event as T_now) without
  bypassing the view; (ii) the store is apparatus-owned, no subject grants (no passive
  prime — the e12 discipline); (iii) the store is itself a registered stream in the
  Frontier vector, so judgments about judgments (STALE-LAW and kin) have a lawful
  substrate — closing refute-semantics flaw 5's secondary loop ("the judgment store is
  a third mutable table no family covers": it is covered as a stream, Family A applies).
- **Whether the engine feeds a deny surface:** settled by ruling 42 — watch-only
  default, per-judgment ratified promotion, e17 the template (D21). The evaluation
  design's "never a deny surface" reading and the architecture pipeline are both
  superseded exactly as far as the ruling states and no further.
- **FindingIdentity:** §4 (D8–D10).
- **Family F/B promotion preconditions:** unified by D13 + INC 5.
- **Budget ratification authority — [INC0-DECIDED: D18]:** measurements *propose*
  (evaluation's derive-from-measurement is the input), the maintainer *ratifies* every
  budget (architecture §5 protocol item 2). No budget exists that is not a ratified
  multiple of a banked measurement; none is asserted in this document.
- **Aggregation surfaces:** D5.
- **The census's epistemic label — [INC0-DECIDED: D20]:** the INC 1 census and its
  M2-style discharge are labeled an **encoding-coverage census**, never a
  detection-power claim (refute-evaluation flaw 8: the blind is porous by construction;
  rules distilled from adjudications re-deriving those adjudications is a legitimate
  encoding check and nothing more). The NRC-bar sentence is scope self-disclosure, not
  discovery capability.

---

## 6. What increment 0 inherits without restating

The load-bearing survivors stand as the seed lists them, cited not copied: the
five-plus-clock judgment type; the deontic architecture (no modal operators; discharge
status only; violation a routed flag — F28); quotational paraconsistency; DerivationRecord
+ Frontier self-citation currency; UNPROVEN-NET pinned to (judgment, rule-hash,
engine-version); the admission protocol (law + banked specimen + flipping mutation +
justified assignment + declared stage) — with the INC 3 constructor and the §1 registry
as its mechanical home; P3's verified-claim rule, honestly non-mechanical, recorded per
judgment in `goodhart_surface`. The threat catalog L1–L10 organizes the registry's
countermeasure cross-references, with "kills" demoted to "bounds" where the mechanism
bottoms out in fixture coverage (seed survivor list; refute-adversarial salvage).

---

## 7. OPEN-QUESTIONS register — what increment 0 does NOT settle

Owner classes per the seed's division of labor: **Fable** (elevate-only-on-Fable),
**stand-in** (buildable against this document + the panel files), **maintainer** (ruling).
Silence is the one forbidden state (critic §7); this register is the anti-silence.

| # | Question | Why open (cite) | Owner |
|---|---|---|---|
| OQ1 | Cross-session obligations: the BRIEF's approval-in-one-session/discharge-in-another shape is unrepresentable in every design as written; open-obligation carry-over vs lifecycle grounding units | critic §3; seed mandate 3 | Fable |
| OQ2 | Law epochs: retroactivity of newly ratified laws over pre-law records (stamp-distinctness predating stamps); the acts_live shared-sequence retrofit is the same shape for the historical corpus | critic §3; seed mandate 5; INC 5 memo input | Fable (design) + maintainer (retroactivity ruling) |
| OQ3 | F10 conservative-abstraction argument for the ids-not-text gap (which direction does the abstraction err?) | critic §4; seed mandate 7 | Fable |
| OQ4 | F12 assurance-case argument structure (green lines → honest record is an ARGUMENT, not a talisman) | critic §4; seed mandate 7 | Fable |
| OQ5 | F13/I11 decades-scale retention: judgment store, journals, expectations, **archived solver versions** (clingo-of-2026 runnable in 2046?) | critic §4 | stand-in (plan draft) + maintainer (retention ruling) |
| OQ6 | G12 beyond the sealed store: read/export/access events on the judgment store and derivations | critic §4; ruling 43 discharges only the secret's corner | stand-in |
| OQ7 | G14 explicit security-scope declaration for the engine's new surfaces (secret, journal, caches, hook, acts_live) | critic §4: assessed or declared out of scope — silence not acceptable | stand-in (draft) + maintainer (declaration) |
| OQ8 | Part-11 trusted clock: pinning `now` makes replay exact, not the clock trustworthy; time source + trust basis undeclared | critic §4; §3 above | maintainer |
| OQ9 | Adjudication-loop wiring to `experiments/adjudicate/`: where a ruling lands, its id/Frontier semantics, re-derivation churn on ruling-flipped verdicts | critic §3; §1.1 `adjudication_slot` | Fable (design); stand-in (wire-up after INC 2) |
| OQ10 | Armed-state specimen provenance and re-baselining once the engine runs live (the Expectation `apparatus_config` field is the hook; the re-baselining is owned work) | critic §3; seed mandate 6 | stand-in (field) + maintainer (re-baseline scheduling) |
| OQ11 | Ratification of the D17 refusal-capture proposal (design ships in INC 4; arming waits on the ruling) | binding amendment; seed division of labor | maintainer |
| OQ12 | May the subject query the judgment store / its own flags (pull access as a prime surface)? | critic §5 | maintainer |
| OQ13 | The union subject-facing prime surface (teach texts + injected findings + STALE presentations + interrogation payloads audited as ONE vocabulary-shaping surface) | critic §3 | Fable (design) + stand-in (instrument) |
| OQ14 | Concurrency: multi-writer frontier semantics, cache maintenance under concurrent inserts, racing hooks | critic §3 | Fable |
| OQ15 | The T1 hook build (third encoding per D11), incl. SIGKILL-survivable non-run accounting (close-time oracle of expected invocations) | refute-architecture smaller items; beyond INC 5 | Fable (design) + stand-in (build) |
| OQ16 | Codegen spike under the N−1 independence bound | binding amendment; beyond INC 5 | stand-in (spike), decision by evidence |
| OQ17 | First latency budgets (currencies + protocol stand; every number waits on a banked measurement + ruling per D18) | architecture §5; refute-architecture flaw 5 (pg_stat_statements alone cannot carry the production leg — the close-line design needs rework at build time) | stand-in (measure) + maintainer (ratify) |
| OQ18 | Marriage §7 dogfood target (this repo's own sessions) — appears in no milestone plan | critic §4 | maintainer (scheduling) |
| OQ19 | Bus factor / operational continuity: the engine's evidence, queue drain, and sealed store if the one maintainer is unavailable | critic §4 | maintainer |
| OQ20 | DTO inbound re-key judgment semantics on the live lineage (REKEY-DEBT verdicts) | semantics §8.5; marriage A.6 | Fable |
| OQ21 | Who safely authors new `.lp`/law-constant text (the marriage §10 solver-file hazard as an operational constraint on every build increment) | seed division of labor: any new `.lp` authoring is elevate-only-on-Fable | Fable + maintainer (operational rule) |

---

## 8. Decision index (every [INC0-DECIDED] in one scan)

- **D1** One authority module, two record kinds (JudgmentSpec + Expectation); the expectations ledger is a generated table of the same module, not a second authority.
- **D2** Registry mechanics: append-only, supersedes-chained specs; F9-shaped contest records for regolds; the approver is never the mover (also licenses DIVERGE_BY_DESIGN); meta-toolchain inside the qualification perimeter.
- **D2a** The semantics "mode ceiling" column is dropped as subsumed by promotion stage P0–P5.
- **D3** Four verdict strata (family / derivation-status / comparison / aggregation); QUARANTINED defined once = "attempted, output untrustworthy"; NOT-RUN and TIMEOUT are distinct statuses.
- **D4** The per-family non-run member is generator-injected; a family enum lacking it is unconstructible.
- **D5** Exactly one cross-family aggregation point (the close manifest); discharge table and self-conformance block are generated views of the same mapping tables.
- **D6** `Frontier` = per-stream max-id vector + pinned evaluation clock; watermark/as_of/prefix≤W retired to citation-only.
- **D7** For C_t families the identity discriminator is the crossed bound, never the raw clock — idempotency and expiry jointly satisfiable.
- **D8** Unified FindingIdentity = hash(substrate, family, canonical typed subject_ref, law_ref, family-declared discriminator incl. onset Frontier); observation Frontier is provenance, not identity.
- **D9** F44's clause-half gets a constructible subject: `scope_token(A,B,hash)` computed SQL-side, exported as an opaque id (ids-not-text held).
- **D10** Per-(family, subject_ref, Frontier) verdict functionality is a checkable store invariant; F44 is legal because the subjects differ.
- **D11** "Same program text at three schedules" is retired; one semantics, N registered producer encodings, each with its own registry row, mutation set, and reconciliation line; write-time additionally bound by ruling 42's verdict-equivalence clause.
- **D12** The judgment store is reconciled with never-stored-T_now: banked verdicts are T_event facts about derivations; consumer view forces STALE presentation; store is a registered stream (so judgments-about-judgments have a lawful substrate); no subject grants.
- **D13** ALL cross-stream judgments (Family F and Family B gap-detection) are close-time-bound until the acts_live ordering question is ratified.
- **D14** F42/F46 warning-polarity is scoped to citation currency; I1/M-trigger gap-detection keeps defect polarity at close; neither ever denies a write outside ruling 42's protocol.
- **D15** Law-reference keys are namespaced (RULING:/FIND:/BRIEF:/INV:/ADR:) — the F-namespace collision is unrepresentable.
- **D16** Constructor refusal arms in INC 3 (after the census); gate-feeding judgments require RULING-depth citations, flag-only require ≥ FIND depth — the live e17 gates and FINDINGS-only flags coexist lawfully.
- **D17** Refusal capture (PROPOSED for maintainer ratification, not silently decided): RAISE preserved; journaling at the interception-hook layer on its own connection; second witness = consumed-id gap + acts-stream error trace; close-time two-sided reconciliation; bypass residual pre-registered per the standing threat-model scope.
- **D18** Budgets: measurements propose, the maintainer ratifies; no number asserted anywhere in this document.
- **D19** Tier 1 splits into 1a (engine-stability anchors, birth-independence caveat carried) and 1b (independently-validated instrument numbers); 1b reproduction is scheduled work (INC 2).
- **D20** The census is labeled an encoding-coverage census, never a detection-power claim.
- **D21** The e17 stamp gate is grandfathered as ruling 42's already-ratified template instance; every other deny promotion requires its own non-NULL `ruling42_ratification`; no new deny surface exists in INC 1–5.
- **D22** acts_live is built as a spike with a written adopt/abandon recommendation; the shared-id-sequence total order is the candidate investigated first; nothing consumes the live stream before whole-run parity.

---

*No files modified but this one. No sub-agents. psql touched read-only, solely to verify
acts.ruling rows 42/43 at citation time. This document is increment 0's design record;
elevation of content increments begins at INC 1 of §5, not before.*
