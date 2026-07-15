# Engine cross-session obligations + law epochs — SEED (critic mandates 3 & 5, worked as one design)

**Status: SEED, for maintainer review.** This is the elevate-only-on-Fable pair the
inc-0 OPEN-QUESTIONS register carries as **OQ1** (cross-session obligations) and **OQ2**
(law epochs / retroactivity), owned together because they interact: an obligation's
governing law can change between the session that records it and the session that
discharges it (§5 works the composed case). This seed settles the representation and the
verdict semantics; the maintainer settles every retroactivity scope (OQ2's ruling half
stays his, §3.4); registry minting and builds are increment-sequenced content work
(§8/§9). Nothing here lifts D13, denies a write, or mints a kind/edge/enum — proposals
for minting are marked as proposals. Anchoring this file into `acts.ruling` is the main
loop's act, not this document's.

**MODEL-SERVED (self-report):** claude-fable-5 — per this session's own system context
("You are powered by the model named Fable 5. The exact model ID is claude-fable-5").
Per the provenance-honesty rule I have no introspective channel that could detect a
silent mid-run substitution; no degradation event was observed this invocation. The
common-mode caveat binds identically here: this seed shares the model family of the
panel, the critic, inc-0, and the frontier seed; the standing invitation of a non-Fable
review of engine seeds applies to this one.

**Record basis (read in full this invocation):** `consults/engine-design-SEED.md`
(mandates 3 and 5; the binding-amendments section as LAW);
`consults/engine-panel/critic-completeness.md` (§3 cross-session + law-register bullets,
§2, §4); `consults/engine-panel/design-semantics.md` (families table §2, §2.1, the
deontic architecture, law-register point 3); `consults/engine-panel/design-architecture.md`
(the partitioning law, §135); `consults/engine-increment-0-unification.md` (D1–D22, OQ
register); `claude_harness/experiments/fact-mining/docs/safety-critical-logging-standards/BRIEF.md`
(G5, F2/I7, F4/F5 discharge, §3 trigger classes, §4); `LEDGER-LOGIC-MARRIAGE.md`
(§4 deontic scoping, §6 donations, §8); `consults/engine-frontier-semantics-SEED.md`
**including Addendum B** (A1–A7 applied; D13 in force) and
`consults/engine-frontier-semantics-SEED-review.md` (verdict + Addendum A);
`POST-FABLE-OPERATING-BRIEF.md`; `claude_harness/db/harness/005_findings_ledger.sql`
(the `finding_open` view, read at source). Live DB verification was delegated to one
Sonnet SQL relay per the standing carve-out (read-only): rulings **28, 29, 42, 43, 110**
verified `binding`/`human:maintainer`; apparatus anchors **111–115** observed
(frontier seed pre-registration 111, assurance-arguments 112, review 113/114, seed
post-Addendum-B 115, supersedes-chained); `acts.ruling` max id was **114 → 115 during
the relay's run** (another session filed 115 mid-battery — reported as observed, not
reconciled); `acts.stream` = 4 rows (e15–e18), `acts.act` dense 1–735;
`harness.finding` + `harness.finding_disposition` + `finding_open` view and
`lab.countersign_obligation` shapes confirmed against the live DB.

**Plain-language summary for the maintainer.** Two gaps, one design. First: the rules
this record lives by say an approval must exist before the change it licenses, and an
assigned obligation must eventually be discharged — but approval and discharge routinely
happen in *different working sessions*, and the engine as designed only ever looks at
one session at a time, so it could never see a discharge that arrives next week. The fix
is not to keep a running "open obligations" list (a stored list of what is *currently*
open is exactly the kind of stale furniture this project has banned once already); it is
to store only the permanent events — "obligation recorded", "discharge recorded",
"waiver recorded" — and have the engine re-answer "what is still open?" freshly each
time, from those events, the same way the findings ledger already answers "which
findings are still open" today. Second: when you ratify a new law, the old record could
not have obeyed it — pre-stamp records cannot carry stamps. So every law gets an
explicit "in force from here" line drawn in the record's own coordinates, old records
get the honest verdict "predates this law" (never a fake pass, never a retroactive
fail), and re-judging old records under a new law happens only when you explicitly say
so, as *new* judgments appended next to the old ones — nothing is ever rewritten. Third,
the loop-stability worry: one of your rulings can flip verdicts that other pending flags
were born from. The rule: the flip never silently closes those flags — they get a
visible "the ground under this flag moved" note and wait for a human, and the engine
never re-derives in an endless loop because each round needs a new human act to feed it.

---

## 0. Decisions up front

- **[OE-D1]** The grounding unit for cross-session Family E judgments is the
  **obligation lifecycle unit** — the bounded, identity-keyed event set of one
  obligation — not the session, not the lifetime record, and never a stored
  open-obligation state. (§2.1; the partitioning-law amendment this requires is
  surfaced, not folded in — §2.4.)
- **[OE-D2]** No new identity scheme. Obligations key on the **D8 FindingIdentity**
  exactly as ratified; the obligations index is a monotone event index at the KB layer
  (marriage §6.2's donation), with **no status column anywhere**. (§2.2)
- **[OE-D3]** Discharge in session N+k joins the obligation from session N by
  **recorded reference only** (id/edge within a lineage; explicit imported-reference
  act across lineages) — no fuzzy matching, ever. (§2.3)
- **[OE-D4]** A law's temporal scope is a **LawEra register row** whose `effective_from`
  is a **banked Frontier vector** (D6 shape), anchored at the ratifying ruling id —
  which makes "record predates law" a per-stream id comparison, needing no cross-stream
  order at all. (§3.1)
- **[OE-D5]** Pre-law records get a new S2 derivation-status member,
  **`PRELAW(law_ref, boundary)`** — distinct from `EXCLUDED(manifest-reason)`, because
  an absent law era and an absent fact family are different epistemic states and the
  record has a specimen where they coincide on one row and must still read apart. (§3.2)
- **[OE-D6]** Retroactivity is **a ruling, never an inference**; the engine's default is
  prospective-only. A declared-retro re-judgment is a **new judgment at a new
  Frontier** — D8's law-in-the-identity forecloses the rewrite by construction. (§3.3–3.4)
- **[OE-D7]** The churn rule: ruling-driven re-derivation is a **scheduled close-time
  sweep**; a flipped generating verdict **annotates** its pending flags and never closes
  them; the loop is well-founded because no derivation consumes its own same-frontier
  output and every new cycle requires a new human act. (§4)

## 1. Why one design: the interaction, stated

An obligation is recorded in session N under law L1; L1 is superseded by L2 (or a new
law ratifies) before session N+k records the discharge. Judging that discharge needs
*both* mandates at once: the cross-session join (which obligation is this discharge
for?) and the epoch question (under which law is discharge judged, and what do the
pre-change records get?). Designed separately, the two produce exactly the drift the
critic's §1 warned about — two vocabularies for one boundary. §5 works the composed
case; everything before it builds the two halves so that §5 needs no new machinery.

## 2. Mandate 3 — cross-session obligations (OQ1)

### 2.1 The grounding unit — decided, and the alternatives retired

Three candidates were on the table (critic §3, seed mandate 3, the brief's own list):

**(a) Open-obligation carry-over state — REJECTED.** A stored "open obligations" table
is a materialized T_now fact: "open" *means* "recorded ∧ not discharged as of now",
which is a nonmonotone verdict, and storing it re-creates the e9 furniture in the exact
shape D12 exists to forbid ("no class-C validity fact is ever materialized" — the
architecture design's own §12 line, upheld by inc-0). It is also two homes for one truth
(the obligation row and its carried status), the cancer the one-registry decision (D1)
exists to forbid. The kernel of truth in (a) — that lookups should be cheap — is an
*efficiency* concern, and if it ever bites it is answered by the already-planned
monotone-cache machinery under `cache_integrity` discipline (inc-0 "beyond INC 5"),
never by making a cache the authority.

**(b) Whole-lifecycle grounding — REJECTED.** Grounding the engine over all sessions of
a lifetime is the "one giant atom base" the partitioning law structurally caps. n grows
without bound; the cap is the law's load-bearing property and survives this design.

**(c) The obligation lifecycle unit — ADOPTED [OE-D1].** For a Family E judgment about
obligation *o* at Frontier F, the grounding unit is:

```
ObligationUnit(o, F) ::=
    { the obliging row(s) of o }                                  -- monotone
  ∪ { every recorded act ≤ F reachable from o via the declared    -- monotone
      discharge-relevant reference set (§2.3): attestations,
      answers, waivers, imported-obligation references }
  ∪ { the LawEra rows for o's law_key (§3.1) }                    -- monotone
```

The unit is **bounded per obligation** (it grows only with acts *about that
obligation*), so the derivation's EDB is smaller than a session's, not larger — the
partitioning law's spirit (bounded grounding, no giant atom base) is not merely
preserved but tightened. The nonmonotone closure (discharge status at F) runs over this
unit, strict and stratified as everywhere else (semantics §3.1); the enumeration of
units for a horizon derivation (§2.5) is itself monotone (obligation-recorded events up
to F).

**The live precedent, cited because it is already in production:** the general findings
ledger (`db/harness/005_findings_ledger.sql`) stores findings and disposition acts as
two append-only tables and derives OPEN as a view — `finding_open` = "no disposition row
exists" — with the file's own honesty header stating "a finding is OPEN **iff**
finding_open lists it; only a disposition act closes it (F28)". That is this design at
apparatus scale, running today. The engine's obligations semantics generalizes the
worked shape rather than inventing a new one. (`lab.countersign_obligation` — PK scope,
`assigned_by <> obliges_actor` CHECK — is likewise the recorded other-assigned
obligation shape of the deontic architecture, live in the lab schema.)

### 2.2 Representation: D8 identity + a monotone event spine, no status column [OE-D2]

The critic's third option ("an obligations register keyed cross-session") is adopted
**only as identity and events**, never as status:

- **Identity:** an obligation's cross-session key is its **D8 FindingIdentity**,
  unmodified: `hash(substrate_id, family E, subject_ref = typed row-ref of the obliging
  row, law_ref, discriminator = onset Frontier)`. `substrate_id` already carries the
  session-independent target identity via the `ledger_target` SSOT (the marriage §6.2
  donation, ratified into D8). Minting a second identity scheme for obligations would
  re-create the three-incompatible-schemes disease the critic's §2 caught; this seed
  mints none.
- **The event spine:** the KB accumulation layer (marriage §6.2, the layer the critic
  correctly noted "stores findings, not open-obligation state") gains obligation
  **events** as its rows for Family E: obligation-recorded, discharge-claim-recorded,
  waiver-recorded, imported-reference-recorded — each a monotone T_event fact carrying
  (identity, lineage, row id, session attribution, Frontier observed at). `first_seen`/
  `last_seen`/`seen_count` semantics carry over from `kb.finding` unchanged.
- **No status column.** UNDISCHARGED/DISCHARGED is derived at a Frontier, every time,
  and banked only as T_event derivation facts under D12: the consumer view forces the
  STALE presentation, the store takes no subject grants, and the judgment store remains
  a registered stream in the Frontier vector. A reader can not commit the e9 sin without
  bypassing the view.

### 2.3 The mechanical discharge join, session N → session N+k [OE-D3]

**Within one lineage (the common case).** The lineage's ledger is one durable table
across all its sessions, and its id order is total across them (post-adoption of the
frontier seed, `kernel.event_seq` is *per lineage and persistent* — FS6's observation
that the shared sequence already extends total order across sessions; this seed supplies
the representation half FS6 explicitly left to OQ1). So the join is a plain recorded
reference: the discharging act (attestation, answer, waiver) carries an edge to the
obliging row's id, exactly as e17's rows 12/17/18 already derive {REFUSED-AND-TAUGHT,
DISCHARGED} from the record alone — the session boundary between recording and
discharging is **provenance on the rows, not an obstacle to the join**. The Family E
derivation at Frontier F grounds ObligationUnit(o, F) and derives the S1 verdict
({DISCHARGED(by), UNDISCHARGED, REFUSED-AND-TAUGHT, WAIVED(row)} as registered).

**The G5 "precedes" half composes, it is not duplicated.** G5 needs *order* (approval
before implementation) on top of *reference*. Order is the frontier seed's delivered
relation — ORDER-TOTAL within the shared domain from adoption forward (and across
sessions of one lineage, per the persistent sequence), ORDER-ANCHORED(grade)/
ORDER-UNDECIDED for the historical corpus — used here as ratified-as-amended
(Addendum B; D13 still confines cross-stream judgments to close-time until ADOPT).
*Pairing* (which acts constitute "the implementation" of which change request) remains
FS2, owned elsewhere; a full G5 derivation is **pairing × order × this representation**,
and this seed delivers exactly the third factor plus the composition statement.

**Across lineages (s13-era obligation, s17-era discharge, DTO-era future).** No silent
join exists or should: schema lineages are closed worlds (read-only forever), and a
fuzzy content match across them is the plausibility-matching this record bans everywhere
(the frontier seed's witnessed-anchor rule, applied to reference). The join is an
**imported-obligation reference act**: a recorded row in the new lineage citing the
obligation's D8 identity plus its origin (lineage, row id, content hash). Resolution of
that reference is mechanical; an unresolvable one is Family F `UNRESOLVED-POINTER` —
already in the vocabulary. A lineage boundary is thus epoch-shaped for obligations too
(the same move as the frontier seed's order epochs), and the carriage act is REKEY-debt
work of the OQ20 kind: explicit, recorded, priced — never assumed.

**Vocabulary honesty:** the kernel currently mints no `discharges` edge (marriage §8:
"2-for-1-against", deliberately undefined), and the e17-deferred kernel
discharge/obligation-gate vocabulary work is still owed (post-Fable brief, pipeline
state). This seed therefore specifies the join **semantics** against whatever reference
vocabulary the maintainer ratifies, and registers the minting as owned work (§8 OE-O4).
Nothing here writes the subject-facing contract.

### 2.4 The two laws, honored — and one amendment surfaced

**Never-stored-T_now (D12, architecture §12):** discharged by construction — §2.2 stores
only monotone events; every status is derived at a Frontier and banked as a T_event fact
about a derivation; the STALE-forcing consumer view and the no-subject-grants posture
carry over verbatim. "OPEN" exists nowhere as a stored value in this design.

**The session-partitioning law (architecture §135: "T_now judgments never span sessions;
the engine grounds a session, not a life") — honored in spirit, amended in letter, and
the divergence is surfaced rather than folded in** (the CLAUDE.md letter-vs-spirit rule,
applied to our own law). A cross-session discharge closure *is* a T_now-class judgment
whose facts span sessions, so the letter cannot stand unmodified against the BRIEF —
and the BRIEF is authoritative on scope (standing rule; the critic's §3 bullet says
exactly this). The amendment this seed proposes:

> The grounding unit is **declared per judgment family** in the registry: the session
> for record-local families (A–D as scheduled today); the **obligation lifecycle unit**
> (§2.1) for cross-session Family E; close-time cross-stream units per D13 for Family
> F/B. The law's load-bearing content — every grounding unit is bounded, and no
> derivation ever grounds "a life" as one atom base — is retained as the invariant the
> registry's `grounding_unit` field is checked against.

Ratification depth, stated per D15/D16 discipline: the partitioning law is
panel-design-depth (no `acts.ruling` row files it; it is not in the seed's binding
amendments), so this amendment needs no ruling to *draft* — but it lands in the
registry, so it reaches the maintainer through the same scan that ratifies registry
content, and this section is written to be found by that scan.

### 2.5 The obligation-horizon close line

Every close derives, from the event spine at the close Frontier: **per substrate, the
obligations whose status derives UNDISCHARGED, with age** (Frontier-distance since
onset, not wall-clock). Ships watch-only on the face of the close, exactly like the
`review_queue_debt` line INC 1 just landed (same posture: the RED threshold is a later
maintainer ruling under D18; the *visibility* is not optional). Scope honesty on the
line itself (I12): it covers obligations recorded on covered substrates within covered
law eras — the count is a floor, never a completeness claim; J-triggered obligations
that never entered the record are invisible to it by the BRIEF's own trigger-class
scoping (§3 preamble), inherited not extended.

Validity-bounded obligations (I7/F2: an assumption or obligation row carrying
`valid_until`) leave the horizon by the C_t machinery as ratified: the crossed bound is
the identity discriminator (D7), and the crossing yields exactly one
**EXPIRED-UNDISCHARGED routed flag** (proposed member, §8 OE-O1) — an obligation is
never silently aged out; a human disposes of the expiry.

## 3. Mandate 5 — law epochs (OQ2)

### 3.1 The LawEra register: effective-from is a Frontier, anchored at the ruling [OE-D4]

One append-only register, generated from the authority module like everything under D1,
keyed on **namespaced law keys** (D15):

```
law_era(law_key,                 -- RULING:n / FIND:Fn / BRIEF:Gn|Fn|In / ADR:n
        effective_from,          -- a Frontier VECTOR (D6): {stream → id}, + pinned clock
        boundary_basis,          -- RULING-ANCHORED(id) | CENSUS-DECLARED | MAINTAINER-DECLARED
        retro_scope,             -- NONE (default) | DECLARED(span, RULING:id)
        supersedes)              -- era chaining when a successor law ratifies
```

- **The boundary is a banked Frontier, never a timestamp and never a cross-stream
  guess.** At ratification, the anchoring act records the governed streams' frontiers
  (a one-field extension of the existing anchor idiom — §8 OE-O9). This buys the design
  its cleanest property: *"record r predates law L"* reduces to `r.id ≤
  effective_from.streams[r.stream]` — a **within-stream id comparison**, fully inside
  the settled id-is-order law, requiring none of the cross-stream machinery and none of
  `acts.ruling`'s excluded-from-domain status (frontier seed §2.1). Streams absent from
  the boundary vector (a lineage created after ratification) are wholly post-law — the
  `member_since` idiom from the OrderDomain registry, reused.
- **Pre-mechanism laws** (everything ratified before this register exists, and every
  FIND/BRIEF/ADR-depth law that has no ruling row) get their boundary **declared at the
  INC 1 census** with `boundary_basis` recording how — the census already carries
  ratification depth per D15/D16; this adds the temporal dimension it lacks. Where a
  boundary is genuinely undeclarable, the era lookup returns **ERA-UNDECIDED** for the
  affected span — the same three-valued honesty as the order relation (IN-ERA /
  PRE-ERA / ERA-UNDECIDED), and never a guess.
- **Norm-force vs derivability-onset, kept apart.** The register records when the
  apparatus became able to *hold records to* the law — the derivability onset. Whether
  the norm morally bound earlier conduct is not the engine's question: that is a
  retro-scope ruling (§3.4) or Family H review residue. The engine's claim stays modest
  on purpose.
- **Supersession chains eras.** A successor law's ratification closes the predecessor's
  era at the successor's `effective_from` and opens its own. Judgments banked under the
  predecessor remain lawful history (their DerivationRecords pin the law version used —
  I3 for judgments, semantics point 3), and STALE-LAW (Family G) routes them for
  re-derivation under §4's schedule.
- **Completeness is checked, not hoped:** a binding `acts.ruling` row with no era row is
  RED — the same rulings-stream parity the INC 1 census already runs, extended one
  column.

### 3.2 The PRELAW verdict — and why it is not EXCLUDED [OE-D5]

Proposed S2 derivation-status member (registry-minted under D4 mechanics at content
increments, not minted here):

> **`PRELAW(law_ref, boundary)`** — the derivation ran, established from the era
> register that the judgment's subject wholly predates the law's effective-from, and
> honestly reports inapplicability. S4 rendering: a **listed inapplicability line**
> ("N pre-law records under LAW-KEY"), never RED, never silently OK.

Kept distinct from `EXCLUDED(manifest-reason)` because they answer different questions:
the capability manifest answers *"can this substrate express the facts this judgment
needs?"* (per-stream, per-fact-family — the A.2 refuse-loudly idiom); the era register
answers *"was this law in force over this span?"* (per-law, Frontier-bounded). The
record supplies the specimen where the two coincide and must still read apart:
**stamp-distinctness (F53, ruling 29) over an s13-era record.** That record is *both*
pre-law (F53 ratified 2026-07-07, at e17) *and* stamp-incapable (the s13 schema has no
stamp columns). A stamp-*verification* judgment over it is `EXCLUDED(no stamp facts)`;
the F53 *law* judgment over its conduct is `PRELAW(RULING:29, …)`. Collapsing the two
would let a capability gap masquerade as legal inapplicability or vice versa — the
distinction is one row's worth of vocabulary and it forecloses that conflation for good.
A subject whose record span **straddles** the boundary gets a third honest status,
**`STRADDLES-ERA(law_ref, boundary)`**, routed for adjudication (default: judge the
post-boundary portion where the family's subject type makes it separable; else the flag
waits for a human) — proposed alongside PRELAW, same minting path.

The composition rule for every derivation's preflight is then two orthogonal lookups,
neither substituting for the other: manifest (else EXCLUDED) × era (else PRELAW /
STRADDLES-ERA / ERA-UNDECIDED). The close face renders the two lines apart.

### 3.3 Re-judgment semantics: a new judgment at a new Frontier, never a rewrite [OE-D6]

When re-judgment of pre-law records is licensed (only by §3.4's ruling), the mechanics
are already fully paid for by ratified law — this section adds no machinery, it states
the composition:

1. The re-derivation runs at a **new Frontier** (which now includes the retro-scope
   ruling itself in the rulings stream and the era row), producing **new T_event
   judgment rows** with fresh DerivationRecords citing the new `law_ref`.
2. The prior judgments are **untouched history**: their DerivationRecords pinned the law
   they lawfully used; prefix-determinedness means nothing below the old Frontier
   changes; append-only means nothing *can* be rewritten.
3. **D8 forecloses the collision by construction:** `law_ref` is identity-bearing ("two
   truths under two laws are two findings"), so the retro-judgment has a *different
   FindingIdentity* than the original-era judgment. Both persist; a reader sees the
   transition instead of a silent replacement. This is the design's quiet win: the
   rewrite hazard the critic asked about was already unconstructible the day D8
   ratified — this seed's contribution is noticing it and pinning fixtures to it (§6).
4. The era basis and boundary ride in the DerivationRecord as **provenance** (like the
   observation Frontier in D8 — provenance, never identity).

### 3.4 Retroactivity is a ruling, never an inference

The engine's default for every law is **prospective-only** (`retro_scope = NONE`). No
mechanism in this design derives retroactive applicability from a law's text, its
FINDINGS lineage, or its "obviousness" — a retro scope exists exactly when a
maintainer ruling declares it, span-explicit, and the era row carries that ruling's id.
This keeps OQ2's ruling half where inc-0 already placed it (owner: maintainer) and keeps
the engine out of the one judgment it must never make on its own: how far a new norm
reaches into old conduct. The interface obligation is this seed's §0 summary plus, at
each ratification, a one-line option set ("prospective only — recommended default /
retro to span S because …") per the maintainer-interface rules.

## 4. The churn rule — loop stability under rulings [OE-D7]

The loop the critic named: engine output → flag → review queue → ruling (appended fact)
→ EDB grows → derivation flips verdicts → some *other* pending flags' generating
verdicts no longer derive. The rule set:

1. **Well-foundedness first.** No derivation consumes its own same-frontier output: a
   derivation's Frontier — including its judgment-store component, per D12(iii) — is
   captured strictly below the ids it will write. Every derivation is therefore a pure
   function of a strict prefix (stratified, unique model, pinned clock), and the
   engine⟷queue⟷ruling loop **cannot cycle without a new human act between rounds**.
   Churn is work, never divergence.
2. **Rulings are consumed on schedule, not on impact.** A ruling/adjudication enters as
   an appended fact; re-derivation of affected judgments (STALE-LAW-flagged, or
   adjudication-touched) happens in a **close-time sweep**, never an eager cascade at
   ruling-commit. This keeps the maintainer's act cheap (filing a ruling never triggers
   a compute storm), makes churn *countable* (one sweep per close, its size a measured
   number under D18's measurements-propose discipline), and changes no verdict's value —
   only its arrival time, which the STALE presentation already renders honestly.
3. **A flip is an append.** The re-derived verdict is a new T_event judgment row at the
   new Frontier — same FindingIdentity where the law is unchanged (a nonmonotone family
   flipping across frontiers is the record defeating, legal; D10's functionality
   invariant is per-Frontier and untouched), a new identity where the law changed
   (§3.3).
4. **Pending flags are annotated, never auto-closed.** A pending flag whose generating
   verdict no longer derives at the current Frontier gains a derived, append-only
   annotation — `generating-verdict-superseded(old_frontier, new_frontier)` — and
   **stays open until a human disposition** (which the annotation makes cheap: a batch
   disposition citing the flip is legitimate *because a human filed it*). Auto-closing
   here would be F28's auto-resolve one level up; the launder proof is the standing
   negative control, and §6 pins a fixture to it. This is the SUPERSEDED-blocks-green
   idiom (Expectation ledger, D2) applied to the queue.
5. **Flip-flop is rendered, not absorbed.** A FindingIdentity whose verdict flips ≥ k
   times across ruling-driven sweeps raises a Family G **verdict-instability flag** (k
   is a later maintainer threshold; the flag ships with visibility-first posture like
   every debt line). Human-driven oscillation — ruling A flips, ruling B flips back —
   is possible by design (rulings are sovereign); the engine's duty is to make the
   oscillation *visible as a chain*, each link a recorded act.
6. **Recurrence stays distinguishable.** New flags born from a sweep carry new onset
   Frontiers (D8's discriminator), so re-derivation churn can never be confused with a
   defect recurring — the identity quartet fixtures from INC 2 already hold this line.

The remainder of OQ9 — *where* an adjudication lands (`experiments/adjudicate/` wiring,
its id/Frontier semantics) — is deliberately not settled here; this section settles
exactly the churn/stability rule the mandate named, and OQ9 keeps its owner for the
rest (§8 OE-O10).

## 5. The interaction, worked: an obligation across a law-epoch boundary

Obligation *o* recorded in session N under L1; L2 supersedes L1; discharge act arrives
in session N+k. **The governing law of a discharge derivation is the law in force at
the derivation's Frontier** — T_now over the era register, which is exactly the
semantics design's point 3 ("law currency is a T_now judgment") composed with §3.1 —
with o's birth law carried as provenance in the unit. The cases:

- **L2 tightens discharge conditions.** The N+k derivation grounds ObligationUnit(o, F)
  with the era rows, derives under L2, and its judgment carries `law_ref = L2` — a new
  FindingIdentity relative to any L1-era judgment of o. If o was DISCHARGED under L1 and
  derives UNDISCHARGED under L2, both judgments stand, the transition is visible, the
  horizon line counts o again, and whether L1-era *conduct* is re-judged is solely §3.4's
  retro question. No retro ruling → the L1-era judgment is history with a STALE-LAW
  route; the *current* status honestly reflects current law.
- **L1 is repealed without successor.** o's Family E judgment for that law-key ends with
  the era. o leaves the horizon via an **ERA-CLOSED(RULING:id) routed flag** — never a
  silent drop and never an auto-discharge; a human disposes (the disposition may well be
  "moot, era closed" — but a human files it, per F28).
- **The obligation-shaped law postdates the facts.** L ratifies between o's recording
  and its discharge: the recording-time conduct is PRELAW under L; the discharge-time
  conduct is post-boundary and judgeable; a judgment whose subject spans both is
  STRADDLES-ERA (§3.2) with the separable-portion default. The horizon derivation under
  L simply begins at L's boundary — pre-law sessions generate no retroactive noise.

One composed rule falls out and is stated as the section's product: **an obligation's
identity is born once (D8, onset-discriminated) and survives law change; its *status* is
always (unit × era × frontier)-derived; and no combination of law change, session
boundary, or lineage boundary ever mutates a banked row.** Every transition is an
append with a human act somewhere in its provenance chain.

## 6. Fixtures and acceptance (both-polarity, ADR-0011 — pinned now, built at content increments)

1. **Cross-session discharge:** obligation row in scratch session A, discharging
   reference in scratch session B, same lineage → DISCHARGED(by) derives at B's close
   from the record alone; mutation: reference removed → UNDISCHARGED and the horizon
   line counts it.
2. **Idempotence across sessions:** the e17 specimen (rows 12/17/18 →
   {REFUSED-AND-TAUGHT, DISCHARGED, DISCHARGED}) re-derived at a later session's
   Frontier → zero new rows (same identities; the D8 refactor fixture's cross-session
   sibling).
3. **PRELAW vs EXCLUDED, one record:** F53 judgment over an s13-era row →
   `PRELAW(RULING:29, boundary)`; stamp-verification judgment over the same row →
   `EXCLUDED(no stamp facts)`; the close face shows the two lines apart. Mutation: era
   row deleted → the F53 judgment goes ERA-UNDECIDED, never silently EXCLUDED.
4. **Retro re-judgment is an append:** synthetic ruling with declared retro span → new
   judgments at a new Frontier under the new law_ref; the prior era's DerivationRecords
   byte-identical (git-verified); both identities present in the store; D10 green.
5. **The churn negative control (launder-class):** an adjudication flips a verdict that
   generated a pending flag → the flag is annotated and **still open**; with the
   annotation logic synthetically set to auto-close → the fixture is RED. The gate is
   not counted until this red is seen.
6. **Flip-flop rendering:** two opposing synthetic rulings on one identity → the
   instability flag raises with the chain cited.
7. **Era close:** synthetic repeal → the open obligation exits the horizon *only*
   through an ERA-CLOSED routed flag; with the flag suppressed → RED.
8. **Straddle:** a subject span across a boundary → STRADDLES-ERA routed; the separable
   case derives the post-boundary portion and says so.

## 7. Honest limits

1. **Pairing is not solved here.** The obligation-to-discharge *reference* join is
   delivered; which acts constitute "the implementation" of a change request (G5's other
   factor) remains FS2. A full G5 derivation waits on pairing × order × this seed.
2. **The reference vocabulary is not minted.** The kernel has no `discharges` edge and
   the e17-deferred discharge/obligation vocabulary work is owed; §2.3's semantics bind
   whatever the maintainer ratifies. Until then, Family E cross-session discharge
   derives only where existing edges/stamps already carry the reference (as in e17).
3. **Cross-lineage carriage is priced, not free.** Imported-obligation references are
   explicit recorded acts; obligations nobody re-keys at a lineage boundary go
   UNRESOLVED-POINTER/UNDISCHARGED on the horizon — the honest state, and a real
   operational cost the maintainer should see coming.
4. **Era boundaries for pre-mechanism laws are declarations.** Basis-graded and
   census-carried, but declarations; some spans stay ERA-UNDECIDED forever, and the
   engine says so rather than guessing.
5. **Retroactivity rulings are unbounded human work.** Every retro scope is a per-law
   maintainer act; this design makes each cheap to state, not unnecessary.
6. **The trusted clock stays open (OQ8).** Validity-bound expiry (§2.5) inherits it:
   pinned `now` makes expiry replayable, not the clock trustworthy.
7. **Horizon coverage is a floor.** Covered substrates, covered eras, M-triggered
   records only; J-triggered obligations that never entered the record are invisible
   (BRIEF §3 scoping, inherited not extended — F38's perimeter unmoved).
8. **Churn volume is empirical.** Sweep sizes and flip counts are measured under the
   N=1 posture (design lessons, not samples); nothing here asserts a number (D18).
9. **Common mode.** Same model family as the panel, the critic, inc-0, and the frontier
   seed; the standing invitation of a non-Fable review applies here identically.

## 8. Open items, with owner classes

| # | Item | Why open | Owner |
|---|---|---|---|
| OE-O1 | Registry minting: Family E cross-session members (EXPIRED-UNDISCHARGED, ERA-CLOSED flags), S2 members PRELAW / STRADDLES-ERA / ERA-UNDECIDED, S4 inapplicability rendering — under D4 generator mechanics | §2.5, §3.2 proposals | stand-in, at content increments |
| OE-O2 | LawEra register build + the census's temporal extension (boundary column, rulings-parity line) | §3.1 | stand-in (build) + maintainer (each CENSUS-DECLARED / MAINTAINER-DECLARED boundary) |
| OE-O3 | Retro-scope rulings per law (= OQ2's ruling half; FS5's instantiation for order epochs is one of them) | §3.4 | maintainer |
| OE-O4 | Discharge/obligation reference vocabulary minting (the e17-deferred kernel work; subject-facing write contract) | §2.3 | Fable (design) + maintainer (ratification) |
| OE-O5 | G5 pairing semantics | §2.3; = FS2 unchanged | Fable (design) + stand-in (build) |
| OE-O6 | Horizon-line thresholds and age buckets (visibility ships without them) | §2.5; D18 | maintainer |
| OE-O7 | Imported-obligation reference act shape + REKEY-debt interplay at lineage/DTO boundaries | §2.3; OQ20-adjacent | Fable |
| OE-O8 | Verdict-instability threshold k (the flag itself is stand-in work) | §4.5 | maintainer (k) + stand-in (flag) |
| OE-O9 | Anchor-idiom extension: ratification anchors carry the governed streams' frontier vector | §3.1 | stand-in (small build) |
| OE-O10 | Adjudication-loop wiring remainder (where a ruling lands; `experiments/adjudicate/` surface; id/Frontier semantics of a landed ruling) | §4 scope line; = OQ9 minus the churn rule | Fable (design) + stand-in (wire-up) |
| OE-O11 | Partitioning-law amendment lands in the registry (`grounding_unit` field + its boundedness check) and reaches the maintainer's registry scan | §2.4 | stand-in (field) + maintainer (scan) |

## 9. Elevate/build split

**Settled by this seed (build against it):** the grounding-unit decision and
ObligationUnit shape (§2.1); D8-keyed event-spine representation, no status column
(§2.2); within-lineage and cross-lineage join semantics (§2.3); the horizon line's
derivation and posture (§2.5); the LawEra register shape and Frontier-boundary
semantics (§3.1); the PRELAW/STRADDLES-ERA/ERA-UNDECIDED verdict design and its
EXCLUDED-distinctness (§3.2); re-judgment-as-append composition (§3.3); the
prospective-only default (§3.4); the churn rule complete (§4); the composed
obligation-across-epochs rule (§5); the fixture set (§6).
**Elevate-only-on-Fable:** OE-O4 vocabulary design, OE-O7, OE-O10's design half, any
`.lp` authoring the builds require (OQ21 stands).
**Maintainer:** every retro-scope ruling (OE-O3), era-boundary declarations (OE-O2),
thresholds (OE-O6, OE-O8), the vocabulary ratification (OE-O4), the §2.4 amendment at
the registry scan (OE-O11).
**Stand-in:** everything in OE-O1/O2/O5/O8/O9/O10/O11 marked so, strictly after its INC
predecessors per ruling 110 §5 — this seed changes no increment order; it is banked
design input so OQ1/OQ2 stop being the unrepresentable holes the critic filed them as.

---

*No files modified but this one. Sub-agents: one Sonnet SQL relay, read-only, for the
ruling/anchor/schema verifications cited in the record basis; no others. psql not
touched directly by this session. Anchoring this file's sha256 into `acts.ruling` is
the main loop's act.*
