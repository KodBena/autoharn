# The Ledger–Logic Marriage — the epistemic ledger as the deductive substrate (design)

**Status:** design for maintainer review. No code yet; increments cut in §9.
**Provenance:** Fable 5, main-loop session `7be3443d`, 2026-07-06 — commissioned by the
maintainer ("marry the current SQL schema with the epistemic inference and the polymorphic
logic substrates"). Record basis at the end. Model-provenance note: authored on Fable
throughout; no degradation event observed this session.

---

## 0. The thesis, in one line

The epistemic-operator ledger (the s13+ kernel lineage) is the claim substrate the logic
layer has been missing, and the logic-backend seam is the engine discipline the ledger's
instruments have been re-inventing one Python script at a time — marry them: **one typed
EDB export from the ledger, the `LogicBackend` seam instantiated over it, every derived
judgment assigned to the engine whose semantics it actually has, differential-gated
against the SQL floor on banked ground truth.**

(**EDB** = extensional database, the fact base a logic program reasons over. **ASP** =
answer-set programming, clingo's paradigm. **SMT** = satisfiability modulo theories, z3's.
**FDE** = first-degree entailment, the four-valued paraconsistent logic of the z3 lane.
**KB** = knowledge base. **DTO** = decompose-then-overrule — the **adopted** clause-defeat
direction (maintainer ruling 2026-07-06, `deliberations/clause-defeat-decompose-then-
overrule.md`, overruling consult 19 on this topic; burden inverted per the frontier creed —
DTO is retirable only by a machine-checked proof of logical unsoundness, never by an
ergonomics or absence-of-lab-data argument). Its detailed shape (`decomposes` + group
identity + faithfulness/MECE attestation + inbound re-key) is deferred to the codified
recognition conditions; `amends` is the interim and *permanent* quote-and-strike track.
**SoD** = segregation of duties.)

## 1. The two sides, as they stand

**Side A — the epistemic ledger** (`~/w/vdc/1/epistemic-operator/`, harness DB lineage
`s13+`, schema `harness/e13-build/s13-schema.sql`). An append-only, write-boundary-typed
record of an AI collaborator's epistemic acts: `kind` (9 speech-act values), `statement /
rationale / evidence / confidence`, and five typed edges — `supersedes` (whole-row
defeat), `amends`+`amends_scope` (clause-level defeat by verbatim quotation), `answers`
(resolution), `enacts bigint[]` (ticket), `regards` (attestation, SoD-checked) — plus a
NOT NULL `actor` attributed from the connecting role via `kernel.principal`. Fourteen
experiments and 46 findings have battle-tested it; its semantics are settled law:

- **The two-theory split** (consult 11 §4): the stored record is `T_event`, a monotone
  theory of timestamped assertions, sound as *history* by construction; "currently valid"
  is `T_now`, a non-monotone theory **derived** by closure over defeater edges, never
  stored. Unsoundness is a *consumer* property — a consumer is unsound exactly when it
  reads `T_event` as if it were `T_now` (the e9 gate did; rows 25/27 were the live proof).
- **The consumer laws:** flag-never-auto-resolve (F28 — auto-resolve *launders* aliases
  into coherent-looking falsehood, proven executably); label-indifference (F26 — any
  mechanism cost keyed on a self-declared label corrupts that label as a measurement);
  invariant keying (F33); no edge/kind without a consumer (ADR-0008); citation currency
  must be *record-observed at the moment of citation* (F42/F46 — memory-grounded
  correctness fails closed only by luck).
- **The instruments** (`instruments/`): soundness closure, stale-enactment debt,
  review-queue, observed-currency, cite-check, coverage-audit, contemporaneity — all
  retrospective today, all validated against independently-known facts, several already
  *written in ASP* alongside SQL.

**Side B — the polymorphic logic substrate** (`experiments/fact-mining/`). A pluggable
engine seam over an NLP-extracted claim substrate:

- `logic_backend.py` — the **`LogicBackend` Protocol** (name, rules, `analyze(claims)`)
  plus the **mechanical cross-engine differential** (set-equality of finding signatures;
  the fair-trials deflation lesson: the correctness gate is set equality, never a model's
  judgment), with the Python oracle liftable as just another backend.
- Two adapters on two engines proving the seam: `contra_asp.AspBackend` (clingo
  subprocess; defeasible R-FUNC via `not exception`, minimal-repair `#minimize`) and
  `fde_z3.FdeZ3Backend` (z3 two-bit Belnap encoding; the contradiction as a contained,
  queryable `both` value, non-explosive where classical logic detonates).
- The **encoding-trust discipline** (`LOGIC-LAYER-ASP.md`): golden fixtures + mutation
  tests (every load-bearing clause must flip a verdict; honest exclusions named, not
  dressed up) + differential against an independent oracle.
- `kb_ledger.py` — content-hash claim identity (`ClaimHandle`), finding identity as the
  unordered claim-pair (`FindingIdentity`: a persisting finding is one stored row
  re-observed, never re-injected), and the Python-authority / generated-DDL / live-parity
  discipline (`kb_migrate`, `test_kb_schema_parity`).
- `kb_why.py` + `why_layer.lp` — **the worked precedent for this whole design**: ledger-
  shaped rows (`kb.mandate` / `kb.why_event`), a SQL `NOT EXISTS` floor, an ASP second
  producer that earns its keep on the open defeater set, differential-gated on the
  defeater-free floor. The marriage below is that pattern, promoted from one rule (R-WHY)
  to the whole epistemic record.

## 2. Why this marriage, and why now — the dud's lesson answered

The NLP↔logic interface work ended in a dud, and two independent consults agreed the
failure was **goal non-specificity, not the NLP**. The trial-series post-mortem
(`HOOK-DESIGN.md` §4b) says precisely what was missing from the prose-claim substrate:
typed entities, **temporal state-change / belief-revision modeling** ("was X, now fixed"
narratives dominated the false positives — *belief revision to model, not contradiction to
flag*), assertion mood, and role stratification.

Read that list against Side A. The ledger has every missing item **first-class and
write-boundary-enforced**: belief revision is `supersedes`/`amends` (the AGM-shaped
supersession chain the post-mortem asked for, as typed edges with validated targets);
assertion mood is `kind` + `status` + `confidence`; attribution is `actor` from the
connection, not a parse; and there is no extraction noise at all, because the subject
*authors* the claims into a typed schema instead of our mining them out of prose. The
substrate problem that killed the interface work does not exist on this substrate.

Symmetrically, the ledger side supplies what the logic layer lacked: **specific goals.**
Consult 11 §4.1 enumerates the actual judgment set (gate unlock, audit walk, currency,
citation, instrument readouts), and the schema's new consumers add more (countersigned-in-
force, question resolution, review gap, clause-defeat closure, the k-parameterized
independence checks). Each is a concrete, consumer-owned judgment with banked ground
truth. "Deduce something interesting from these claims" — the dud's implicit goal — is
replaced by "derive exactly these judgments, and prove the derivation against the record."

And the maintainer's framing stands as the headline: the audit/ledger work has produced a
**structured, battle-tested knowledge base** — 14 experiments of adversarially-verified
rows, edges, and defect fixtures — which is a strictly better foundation for deductive
workflows than any corpus this project has mined.

## 3. The substrate: the ledger-graph EDB (one home)

A new module, **`ledger_edb.py`** (fact-mining side), is the single home for "what the
ledger looks like to a logic engine" — the analog of `contra_asp.edb_from_claims`, ADR-0012
P1 applied. It exports, from any kernel-lineage session schema (and degrading gracefully on
the closed historical schemas, exactly as the amends-aware instruments already do):

```
entry(Id, Ts, Kind, Concern, Status, Confidence).
actor(Id, PrincipalId).            acts_for(P, Q).          agent_class(P, Class).
supersedes(A, B).                  answers(A, Q).           regards(R, T).
amends(A, B).                      amends_scope_len(A, N).  % the quotation itself stays SQL-side
enacts(E, D).                      % element-wise from the array
review_verdict(R, V).              review_independence(R, I).
obliged(Scope, AssignedBy, ObligesActor).
```

Three design rules, each inherited from settled law:

1. **Ids are the interchange; text stays home.** As in the contra EDB, no statement text
   crosses the wire — engines reason over identities and edges; the SQL side owns text
   (quotation checks live in the write-boundary triggers where they already are). This
   also keeps engine inputs light and keeps trigger-dense prose out of solver files.
2. **`id` is the order, never `ts`** (consult 17 §5.3: same-second and 41 ms neighbours
   exist in the record; the single sequence is the sound total order). Every "earlier"
   in every rule keys on id.
3. **The export is derived from the schema authority, not hand-synced.** §6 proposes the
   kb_ledger-style parity discipline for the kernel contract; until then, a parity test
   pins `ledger_edb` column expectations against the live `s13+` schema the same way
   `test_kb_schema_parity` pins `kb.*`.

Acyclicity comes free: append-only + earlier-target validation makes every edge strictly
backward in id, so all closures terminate by construction (consult 11 §4.2's "pleasant
consequence" — the discipline that makes validity derived also makes derivation
well-founded).

## 4. Assign, don't compete: judgments × engines

The logic-frame law is *assignment*: each judgment goes to the engine whose native
semantics it has, with the SQL floor kept wherever SQL is that engine. Nothing competes;
everything above the floor is differential-gated against it where they overlap.

| Judgment (consumer) | Semantics | Engine assigned | Floor / gate |
|---|---|---|---|
| History integrity, edge resolution, orphan detection, traceability walks (audit walk J2) | monotone closure | **SQL** (recursive views) — this *is* SQL's home turf | — (it is the floor) |
| `T_now`: in-force, head-resolution, answered-status, countersigned-in-force, stale-enactment debt, clause-defeat closure with moot/withdrawn defeaters | **non-monotone** (defaults + exceptions, closure over defeaters) | **ASP** (clingo) — default negation is the exact shape; the soundness/`why_layer` precedents | differential vs the SQL views on the defeater-free floor; divergence *by design* only where a defeater fires, and there ASP's verdict is the honest one |
| Independence / SoD phase structure (k-parameterized principals, review_gap under delegation), minimal-repair blame ("smallest retraction restoring soundness") | combinatorial choice + optimization | **ASP** (`#minimize`; the Core-A encoding of consult 17 §5.2, grown into a standing instrument) | fixture-pinned phase table (k=1 UNSAT → k=2 SAT; SoD at 3; financial at 2 orgs) |
| Quantities in evidence (R-NUM magnitude, tolerance, unit coercion), unsat-core explanations ("*which* obligations jointly conflict") | arithmetic + theory reasoning | **SMT** (z3; `qty_z3` / `unsat_core_z3` lanes exist) | cross-engine differential vs ASP on shared rules, per the seam's `shared_rules` honesty |
| The **aspectual state** (F44): a held row whose clause is defeated while the row stands | paraconsistent value | **FDE lens** (z3 two-bit) — *report-side only*: the row is `both` (in force as a row, false in a clause) — a contained, queryable value for the review queue, honest where a boolean must lie | the kernel closure (see the hard rule below) |
| Reference *truth* (does the cited row's content match the citing intent), MECE-of-meaning, J-triggered noticing | judgment | **review** (human/consult) — F20/F27 residue; no engine claims it | flags route it; nothing mechanical adjudicates it |

**One hard rule: the kernel's derived validity stays two-valued and row-granular — which
is a property DTO itself preserves, not an argument against it.** Fragments are rows;
under DTO the closure never needs a third truth value (consult 19 §1.3, the part that
survives the overruling). The displacement theorem's "false alarms" are, per the
maintainer's ruling, **conservative re-key debt, not unsoundness**: a flag on an inbound
row-granular citation of a decomposed target is *true information* — the citation has
become ambiguous between a defeated and a surviving fragment, and forcing the re-key makes
the record say which. The engine layer is therefore built **DTO-ready**: the `T_now`
closure semantics are written to accept `decomposes`/group edges the day they land (as
design, not built — mirroring the deliberation's own `clause_defeat_moot` extension
posture), so the DTO build arrives as new EDB facts, never a semantics rewrite. The FDE
lens (§9.5) is explicitly **interim**: it renders the aspectual glut on the pre-DTO
record; each case it covers is superseded by first-class fragments as they arrive. It
never feeds a gate and never alters `T_now` — a paraconsistent value is something a
consumer can *see and route on*, not a third truth value in the law.

**Deontic scoping, restated honestly.** `logic_backend.py` keeps obligation-*execution*
off the menu, and this design honors that: deriving normative *status* (this obliged row
lacks a live independent attestation — `review_gap`) is in scope, because it is closure
over recorded facts; prescribing *action* ("the agent must now obtain a review") stays out.
The line runs exactly where the schema's own design put it: obligations are other-assigned
rows, violations are flags, and nothing in the engine layer ever becomes an enforcement
surface keyed on a self-declared label (F26).

## 5. The trust discipline transfers — and the fixtures are already paid for

Every encoding lands under the `LOGIC-LAYER-ASP.md` qualification bar: golden fixtures +
mutation set + differential vs an independent producer. The marriage's windfall is that
the golden fixtures are **already banked as adjudicated defects** — evidence someone
already paid for:

- rows 25/27 (e9): `gate_ok ∧ ¬sound_ok` — the unsound-derivation fixture;
- the launder proof (auto-resolve rewrites 25/27→22, coherent and false) — the negative
  control for any resolution rule;
- row 31→27 (e12, F42): the derived-id miscite — the observed-currency fixture, with the
  kind-luck near-miss as its mutation;
- event 61 (F45): the coincidental-basename unlock — the gate-integrity fixture;
- row 5-vs-29 (F44) plus e10 r28 and e11 17→4: the aspectual triple — the amends/FDE-lens
  fixtures, and the `amends`-accumulation detector's synthetic red case;
- the four-arm reproduction targets: every instrument must reproduce the banked s9–s14
  numbers bit-identically before any new engine output is trusted (the standing
  instruments' own acceptance discipline, inherited unchanged).

A gate never seen red is a claim, not a net (ADR-0011): each fixture ships with its
mutation that must flip the verdict, and honest exclusions are named as exclusions.

## 6. What Side B donates back to the schema

Three targeted adoptions, none touching the subject-facing write contract:

1. **`FindingIdentity` semantics for the review queue.** Today's review-queue output is
   recomputed per run; adopting the unordered-pair content identity makes findings
   durable and idempotent — a persisting flag is one stored finding re-observed, never
   re-injected (KB-CODESIGN §3). This is also the precondition for a *live* queue (§7):
   without identity, a hook would re-nag every turn.
2. **`ClaimHandle`-style content-hash identity for cross-session accumulation.** Serial
   ids are per-session; the moment ledger-derived findings accumulate into the durable KB
   (the hook's L2), rows need a session-independent identity: hash of (session, id,
   statement-hash) — cheap, stable, and it preserves the id-is-order law inside a session
   while giving the KB a collision-safe key across them.
3. **The authority/parity discipline for the kernel contract (offered, not imposed).**
   `s13-schema.sql` is handwritten; the fact-mining side generates DDL from a Python
   authority module and pins the live DB with a parity test. The kernel lineage deserves
   the same: one authority for the column/enum/edge contract, from which the schema file,
   `ledger_edb.py`, and the parity test all derive. The epistemic-operator repo owns the
   decision (it is their apparatus); until adopted, the §3 parity test carries the
   cross-repo fact honestly from this side.

## 7. The hook, re-founded — instruments become rungs

`HOOK-DESIGN.md`'s interrogation ladder stalled because its L1 payload (surface rules over
mined prose) was ~100 % noise. The marriage re-founds the ladder on the ledger substrate,
where the payload is the already-validated instrument set run *contemporaneously* instead
of at close:

- **L1′ — self-consistency over the ledger.** The soundness closure + question-status +
  amends-accumulation detector over the session's own rows. Zero extraction noise by
  construction; findings are typed, grounded in row ids, and adjudicable.
- **L2′ — currency and debt, live.** Observed-currency (is the row you just cited one you
  have record-observed since it last changed? — F42/F46 as a warning, not a gate) and
  stale-enactment debt (the design row your current file work stands on was defeated N
  minutes ago) surfaced *while the work is in progress*. This is the project's stated
  purpose — supply the information the collaborator needs to do the right thing — with
  the one payload the trial series proved has substance.
- **L3′ — engine interrogation.** The §4 assignments behind the seam: the hook's contract
  stays exactly what HOOK-DESIGN promised L3 ("a claim set with provenance in, findings
  with grounding out"); the claim set is now ledger-shaped.

Hook shell disciplines carry unchanged: time-budgeted, degrade-not-block, cursor-
incremental, findings stored durably (via §6.1 identity) with injection gated by novelty.
The witness plan is HOOK-DESIGN §6's, with the planted-contradiction fixture replaced by a
planted ledger defect (a synthetic stale-antecedent edit in a scratch session — the
banked-fixture idiom). Dogfood target: this repo's own sessions, per the standing
maintainer note.

## 8. Deliberately not done

- **No new kinds or edges minted here.** The marriage consumes the s13+ vocabulary as
  shipped; `discharges` stays undefined (2-for-1-against). DTO is *not* speculative
  structure — the decision is made and the direction is law; only its shape build waits
  on the codified recognition conditions, and this design's obligation to it is
  DTO-readiness (§4), not abstention.
- **No harness demand argued from lab data.** The standing rule (durable, 2026-07-06)
  binds every increment here: what the substrate must support is answered by the
  safety-critical-logging BRIEF, never by what our own runs happen to have exercised.
  Absence in fourteen experiments is a censored record, not evidence of no demand.
- **No kernel truth-value change** (§4 hard rule). FDE is a lens, never law.
- **No enforcement from the engine layer.** Everything derived is flag-and-journal into
  the review queue (F28); the only deny surfaces remain the write-boundary triggers and
  the change gate, which are not this design's to touch.
  **[AMENDED BY RECORDED RULING — acts.ruling id 42, human:maintainer, 2026-07-07
  (Option B of consults/engine-panel/DECISION-BRIEF-deny-surface.md, epistemic-operator):
  watch-only remains the DEFAULT, exactly as this line states — but a specific engine
  judgment MAY be promoted to a write-time refusal with, per judgment: a captured
  specimen, proven verdict-equivalence at the same frontier, a teaching message naming
  the honest alternative, and an individual maintainer ratification. The e17 stamp gate
  is the template. The line above is retained verbatim as the default it now names; the
  redraw is this recorded amendment, never a silent edit.]**
- **No re-litigation of the NLP lane.** Prose extraction (GLiNER, mood, coref) continues
  as its own thread; when it matures, its claims join as *another substrate behind the
  same seam* — the marriage neither depends on it nor blocks it.
- **No reading of `epistemic-operator` as a writable dependency.** Closed session schemas
  are evidence (read-only forever); the lineage ledger is append-only; every cross-repo
  fact this side relies on is pinned by a parity test, not assumed.

## 9. Increments (each with a checkable acceptance target)

1. **`ledger_edb.py` + the ASP `T_now` program + the differential.** Export s10–s14;
   derive in-force / unsound-derivation / stale-debt / question-status in ASP; gate
   against the SQL views and the banked instrument numbers (bit-identical on the
   defeater-free floor; the five §5 fixtures reproduced, mutations flip).
2. **Review-queue identity** (§6.1): durable `FindingIdentity`-keyed findings table;
   re-running the queue on an unchanged record inserts zero rows; the e12 flag set
   reproduces as exactly 8 stored findings.
3. **Core-A standing instrument + z3 unsat-core lane:** the k-phase table pinned as a
   fixture; `review_gap` conflicts explained by minimal cores; cross-engine differential
   on the shared rules.
4. **Hook increment 1′** (= HOOK-DESIGN §7 re-founded): Stop-hook shell + L1′/L2′ payload
   + witnesses (planted ledger defect found; daemons-down no-op; idempotency via
   increment 2), dogfooded on this repo's sessions.
5. **FDE aspectual lens** (report-side, interim): the F44 triple rendered as `both`-valued
   review items on the pre-DTO record; superseded per-case by first-class fragments.
   Explicitly last — and explicitly a stopgap: DTO is the destination (§4), the lens is
   what honesty looks like until the shape build's recognition conditions fire.

## 10. Risks and confounds, named

- **Cross-repo coupling.** The marriage spans two repos with different owners-of-record
  (apparatus vs harness). Mitigation is §3.3/§6.3's parity pinning plus the read-only
  posture; the honest residue is that a kernel schema change lands here as a red parity
  test, not automatically.
- **Solver-file trigger hazard.** Model-checking-adjacent text is a suspected safety-flag
  trigger for Fable sessions (unconfirmed mechanism; one degraded consult observed). The
  §3 ids-not-text rule keeps engine inputs semantically thin, and encodings live in
  dedicated files a session need not open to *use* — but the hazard is environmental and
  cannot be engineered away from this side. Pre-registered as an operational assumption.
- **The ledger substrate is honest but not complete** (I12): it captures what the
  collaborator ledgers, under the gate's coverage; conduct outside the perimeter (F38)
  and J-triggered omissions are invisible to every engine here. The marriage inherits the
  apparatus's stated coverage boundary; it does not extend it.
- **N remains small.** The fixtures are adjudicated but few; engine agreement on them is
  qualification, not proof of soundness on unseen records — the standing `LOGIC-LAYER`
  ceiling, restated because it binds here too.

---

*Record basis: epistemic-operator odd links 1–19 in full (consults 1, 3 = Opus; 5–19 =
Fable) including the consult-19 clarification and second addenda; `s13-schema.sql` at the
SQL level; `instruments/README.md`; FINDINGS.md (F1–F46 as excerpted in the consults and
the head of the file); RATIFICATION.md; the safety-critical-logging BRIEF in full;
fact-mining: `logic_backend.py` in full, `LOGIC-LAYER-ASP.md`, `LOGIC-LAYER-SEAM.md`,
`HOOK-DESIGN.md` (incl. the §4b trial-series conclusion), `kb_ledger.py` / `kb_why.py` /
`why_layer.lp` headers, `README.md`. Deliberately not read: `instruments/*.lp`
(operator-side solver files; flag-hazard avoidance per maintainer steer), `tainted/`,
`consults/e15-design-consult-21.md` (not yet part of the record I am cleared for). psql
not touched for this document; no sub-agents; no file modified but this one.*

---

## Appendix A — 2026-07-06, increment 1 as built (link 24; dated append per ADR-0005 Rule 8)

*This document is a point-in-time design record and is NOT retro-edited. This appendix records
where the build (link-24 consult `consults/marriage-i1-build-consult-24.md`) corrected or advanced
the body, per the link-23 critical read and the maintainer scheduling ruling. The body's spine
(§0–§2 thesis, §4 assign-don't-compete, §5 fixtures, §8 restraint) held and was built as written.*

**A.1 Record shape — the body's §3/§9.1 were stale (link-23 §2.2, verified live).** The body's §3
EDB signature was keyed to the kernel-lineage schema and its §9.1 said "export s10–s14." Ground
truth: the e14 record of record is **`nla.public.ledger` (55 rows)** — actor a *text* role, **NO
`regards`, NO `kernel.principal`**; `epistemic.s14` is a 2-row skeleton, `s13` a 2-row kernel-shape
skeleton. Built to THIS: `ledger_edb.py` resolves targets by name via a mirror of the operator SSOT
`instruments/ledger_target.py` (parity-pinned, not imported), and exports over **s10–s13 AND nla**.

**A.2 Capability-driven EDB with LOUD declared exclusions (the F49 fix, new first-class
requirement).** The body's "degrades gracefully on closed schemas" is exactly the vacuous-pass F49
names. As built, the EDB carries a **per-target capability manifest**: every fact family the target
cannot produce (`regards`, `review_*`, `obliged`, `acts_for`, `agent_class` on nla/lean lineages;
`amends`/`answers` on pre-e13 schemas) is a **declared exclusion with its reason**, and a caller
requesting an absent capability is refused loudly — never a silent empty (I12 at the substrate).

**A.3 Id-is-order, enforced (§3 rule 2, sharpened).** The T_now program keys *every* precedence on
the integer id, never ts; a same-second-neighbour fixture proves the sort key. `ts` is carried only
for display and I7 temporal bounds. It reproduces the ts-based banked instrument numbers because on
the append-only record id-order and ts-order coincide; where they could diverge (same second) id is
the sound one.

**A.4 Self-compliance built in (link-23 §2.2(iv), the biggest lack — now closed for the apparatus).**
Every marriage solver run banks a **DerivationRecord** {engine+version, config, EDB/program/output
hashes}; a verdict without both records is NO RESULT; programs+EDB+outputs are retained (F6/F16/I8).
Scoped honestly to the engine layer's *own* tools; subject-side tool provenance stays open.

**A.5 Closed differential vocabulary (link-23 §2.2(v)).** Verdicts are drawn from
{AGREE, DIVERGE_BY_DESIGN, DIVERGE_DEFECT, QUARANTINED}; a non-run is QUARANTINED and turns the run
red; registered as a declared observer line in `close_manifest` (AC7). The differential's two
producers are genuinely independent — a Postgres recursive CTE (`ledger_floor.py`) and clingo
(`ledger_tnow.lp`) — and agree bit-identically (output hashes equal) on all five banked targets.

**A.6 DTO worked out IN FULL here (§4 posture superseded by the scheduling ruling 2026-07-06).**
The body treats DTO as DTO-*readiness* (design-not-build) pending codified recognition conditions.
The maintainer's **scheduling ruling** struck the trigger-gating: this increment IS the "future
cycle." Built: the full §1.5 shape — `decomposes` edge + group identity + faithfulness/MECE
attestation gate (SoD-distinct attester) + one inbound-edge re-key + the `clause_defeat_moot_dto`
extension — apparatus-authored on a scratch lineage, with the ASP closures (`ledger_dto.lp`) as the
consumer. Acceptance completes on **labeled synthetic principals** (maintainer refinement
2026-07-06); a distinctly-labeled authentic maintainer attestation slot is reserved, non-blocking.

**A.7 I7 folded in (§9.1 "assumptions with validity bounds", was deferred "no consumer").** Built:
an `assumes` edge + `valid_until`/`valid_within` bounds + an ASP expiry closure — an assumption past
its bound is loudly not-in-force and any scope resting on it is flagged. The engine layer is the
consumer that arrived.

**A.8 A hazard surfaced and fixed in passing (mother's-life bar).** clingo emits *valid JSON with an
empty model* on a grounding error, so the shared `clingo_run` returns `[]` rather than raising — a
broken program would bank an empty-atom "result" as if it were a derivation (the F49 silent-non-run,
inside the engine). `ledger_differential.run_asp` quarantines an empty derivation over a non-empty
EDB. Flagged for the shared runner (a `clingo_run`-level UNKNOWN/error raise is the durable fix; not
made here to avoid a cross-consumer blast radius — filed for a future touch).
