<!-- doc-attest-exempt: DRAFT pinned pre-ratification 2026-07-18 (Fable freeze plan, ledger row 1455). Pinned as delivered by the fresh-context author, before any maintainer ruling on its reserved questions; ADR-0017 attestation deferred until content stabilizes post-ruling. -->

# FABLE-DEFEASIBILITY-ENVELOPE — the defeasibility envelope for attestation-based defeat of ledger-derived conclusions

**Status:** DESIGN NOTE, non-binding, Fable-authored fresh-context 2026-07-18, commissioned
by the maintainer's sidenote (ledger row 1467), explicitly awaiting a future commissioning
act before anything is built. Nothing in this document is a spec, a delta, or an instruction
to a builder; it is the banked record of an envelope the maintainer ruled "should never be
lost to oblivion when working on these matters." Cost attribution: ledger estimate row 1468,
slug `defeasibility-envelope-note`.

**What this document is, in plain words.** The project keeps its decisions in an append-only
Postgres ledger; "what is currently true" is never stored, it is *derived* — by SQL views
(`ledger_current` and its consumers) and, independently, by an ASP logic program
(`engine/lp/ledger_tnow.lp`) over the same exported facts, with the two producers required to
agree bit-identically (`./judge`). A separate design, the OTel sentry
([design/FABLE-OTEL-SENTRY-SPEC.md](../../design/FABLE-OTEL-SENTRY-SPEC.md)), will write *model-identity
attestations* into the ledger: rows asserting, at a declared confidence grade, which model
actually served the session that wrote some other row. The maintainer's sidenote asks the
natural next question: if such an attestation shows a row was written under a mis-declared
model, can the row be *defeated* — treated as no longer in force — and can the whole defeat
machinery be governed by nothing more than an ordinary, retractable ledger row granting trust
to the attester? This note maps that envelope: the rule construction, the cascade question,
the stratification discipline, and the corners nobody had yet named.

**Primary inputs, all read in full:** [CLAUDE.md](../../CLAUDE.md);
[ADR-0000](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md),
[ADR-0011](../../law/adr/0011-mechanization-discipline.md),
[ADR-0012](../../law/adr/0012-compositional-and-structural-hygiene.md),
[ADR-0013](../../law/adr/0013-execution-integrity.md),
[ADR-0014](../../law/adr/0014-executor-second-opinion.md),
[ADR-0017](../../law/adr/0017-the-zero-context-reader.md),
[ADR-0018](../../law/adr/0018-consults-are-not-front-loaded.md);
[engine/ledger_edb.py](../../engine/ledger_edb.py) and the `engine/lp/` programs (esp.
[ledger_tnow.lp](../../engine/lp/ledger_tnow.lp),
[ledger_support.lp](../../engine/lp/ledger_support.lp),
[closure.lp](../../engine/lp/closure.lp)) plus
[engine/ledger_differential.py](../../engine/ledger_differential.py);
[kernel/lineage/s30-typed-dependency-edges.sql](../../kernel/lineage/s30-typed-dependency-edges.sql),
[s31-supersession-uniform-retraction.sql](../../kernel/lineage/s31-supersession-uniform-retraction.sql),
[s41-principal-bindings-and-relations.sql](../../kernel/lineage/s41-principal-bindings-and-relations.sql);
[design/FABLE-OTEL-SENTRY-SPEC.md](../../design/FABLE-OTEL-SENTRY-SPEC.md) as revised (the v0/v1/v2
attestation layers a defeat rule would consume); the resurrection-trap precedent in
[design/FABLE-RESERVED-DESIGNS-2026-07-18.md](../../design/FABLE-RESERVED-DESIGNS-2026-07-18.md) §1.3.

## 0. Provenance — the commissioning sidenote, verbatim

Ledger row 1467 (decision, 2026-07-18) records the maintainer's sidenote that commissions
this note, quoted in full so the question this document answers cannot drift:

> *"it struck me that by the time all is said and done, we should have an easy way to
> implement revocation of decisions based on model? For example, I could deliver full
> athentication authority (in principle) to the OTel sentry, and introduce something like a
> rule that any row with a mis-declared model is automatically invalid, even after the fact?
> What is the envelope here, I wonder? And for that matter, conditional-defeasible reasoning
> -- say, if I weaken the full authentication authority to defeat all mismatched rows as long
> as I trust its competence to scrute the mismatch? (Actually, it should fall out implicitly
> just by defeating the original decision to trust it, I guess)"*

The same row records his scoping of this note: two premises he rules obvious (stated briefly
in §1 below for the zero-context reader, nothing more), and the substance — the defeat-rule
construction with its implicit lapse, the cascade policy over typed dependency edges, the
stratification discipline, and whatever else belongs in the envelope — carried in full,
because it "needs to be kept in mind and should never be lost to oblivion when working on
these matters."

## 1. The two obvious premises, stated once for the zero-context reader

**P1 — records are never invalid; defeat is a derivation-layer property only.** The ledger is
append-only by trigger for every role including the schema owner; a row, once written, is
permanent history. "Defeat" therefore can never mean deleting, editing, or marking-invalid a
record — it means the *derivation layer* (the in-force views, the T_now program, and any
reasoning built on them) excludes or discounts the row when computing current truth, exactly
as supersession already works: a superseded row is fully present in history, absent from
`ledger_current`. A model-based defeat is one more reason the derivation may exclude a row;
it changes what is *concluded*, never what is *recorded*.

**P2 — evidence grade conditions defeat force.** An attestation row is itself ledger-grade
(attributed, hash-chained, supersedable), but the OTel evidence it rests on is
diagnostics-tier by standing maintainer ruling (guarantees rest on the hook/action surface
only; session internals are diagnostics — the sentry spec's §7 rebuttals R1–R7 spell out
why). So a defeat rule keys on the attestation's *declared* grade (the sentry's closed
vocabulary `exact-command | turn-bracketed | session-scoped | ambiguous`), and a defeat whose
consequences are heavy — one that would unseat a ratification or a work-close — additionally
wants a human countersignature on the attestation before it fires, per the same ruling's
logic: the heavier the load, the less it may rest on a diagnostics-tier correlation alone.

## 2. The machinery the defeat rule would live in (what actually exists)

For a reader who has not opened the engine: `engine/ledger_edb.py` exports the ledger as
typed facts — today exactly `entry(Id,Ts,Kind,Concern,Status,Confidence)`, `supersedes(A,B)`,
`enacts(E,D)`, `amends(A,T)`, `answers(A,Q)`, plus a separate work-item family — with every
family the target cannot produce printed as a declared exclusion, never silently empty.
`engine/lp/ledger_tnow.lp` derives current truth from those facts: `sup_star/2` is the
transitive supersession closure, `superseded(Y) :- sup_star(_,Y)`, and
`in_force(Id) :- entry(Id,_,_,_,_,_), not superseded(Id)` — one negation-as-failure step over
a monotone closure. Everything else (`answered/1`, `question_open/1`, `clause_defeat/2`,
`stale_enactment_row/2`) is built on those. The SQL twin (`engine/ledger_floor.py` plus the
kernel's `ledger_current`-factored views, s31) computes the same judgments independently, and
`./judge` (`engine/ledger_differential.py`) requires bit-identical agreement — the closed
verdicts AGREE / DIVERGE_BY_DESIGN / DIVERGE_DEFECT / QUARANTINED, with any undeclared
divergence red.

Two existing constructions matter for everything below, because the defeat rule is a
composition of their shapes, not a new invention:

- **In-force-conditioned derivation** is already the house idiom. `answered(Q) :-
  answers(A,Q), not superseded(A)` — a question is answered only by an answer still in force,
  so retracting the answer reopens the question with zero cleanup (the F-A fix recorded in
  `ledger_tnow.lp`'s own header). `affirmed(F,D) :- affirms(R,F,D), not superseded(R), not
  affirm_sod_violation(R)` in `ledger_support.lp` — an affirmation discharges only while the
  affirming row itself stands.
- **Flag-then-discharge over the support graph** is already built.
  `ledger_support.lp` computes `exposure(F,D)`: an in-force row F whose transitive support
  chain (`enacts`/`answers`/`assumes` edges) reaches a defeated antecedent D — a *flag* about
  the support graph, deliberately never a verdict about F's truth — dischargeable only by an
  explicit, actor-attributed, separation-of-duties-gated affirmation act.

## 3. The defeat-rule construction, and the implicit lapse (the sidenote's spine)

### 3.1 The three rows

The construction needs exactly three kinds of fact, all ordinary ledger rows:

1. **The target row R** — any row (a decision, a ratification, a work-close) written by some
   session.
2. **The attestation row A** — the sentry's mismatch attestation about R: in the v2 typed
   kind, a `model_identity_attested` row with `attest_row_id = R`, `attest_verdict =
   'mismatch'`, and a declared `attest_grade`; in v1, a `verification` row carrying the same
   fields in the fixed statement convention.
3. **The trust grant G** — the maintainer's decision to empower the attester, which under
   s41 already has a typed home: a `principal_competence_granted` row (subject = the sentry's
   principal, activity e.g. `model-identity-attestation`, band and basis as granted), in
   force while unsuperseded and `principal_binding_active`. Nothing new needs minting for the
   grant to exist; s41 built it recordable-not-gating, and a defeat rule would be precisely
   the first (future, ratified) consumer that makes it gating.

### 3.2 The rule shape, against the engine's actual vocabulary

In the T_now program's own idiom, the rule the sidenote describes is:

```
% GAP-marked predicates do not exist in today's EDB export -- see §3.3.
model_defeated(R) :-
    mismatch_attest(A, R, Grade),        % GAP: attestation fact family
    not superseded(A),                   % the attestation itself still in force
    row_actor(A, P),                     % GAP in the standing export (see §3.3)
    trust_grant(G, P, Grade),            % GAP: grant family, grade-conditioned
    not superseded(G).                   % the grant still in force -- THE LAPSE HINGE

credited(R) :- in_force(R), not model_defeated(R).
```

and its SQL twin is the same judgment as a `ledger_current`-factored view (a `NOT EXISTS`
over in-force mismatch attestations joined to in-force grants), per the s31 reader
discipline. The derived-view layer (`credited`, or whatever the ratifying spec names it)
sits *beside* `in_force`, not inside it: supersession stays the one whole-row retraction
mechanism (s31's ratified semantics), and model-defeat is a further, separately-named
discount a consumer opts into — mirroring exactly how `countersigned_in_force` narrows
`ledger_current` without replacing it.

### 3.3 The maintainer's intuition, confirmed against the real derivation

His parenthetical — *"it should fall out implicitly just by defeating the original decision
to trust it, I guess"* — is **confirmed, not merely plausible**, and the confirmation is
mechanical: because the rule body carries `not superseded(G)`, the grant's in-force status is
re-evaluated on *every* derivation pass (ASP grounds the whole program fresh; the SQL view
re-runs its join fresh). Superseding G — or, in the s41 idiom, writing the superseding
`active = false` withdrawal row — makes `not superseded(G)` fail for every attestation that
leaned on it, so every `model_defeated(R)` atom that rested on G vanishes on the next pass,
with zero per-row cleanup, no cascade bookkeeping, and no stored verdict anywhere to go
stale. This is not a new property the defeat rule would introduce; it is the property the
engine already exhibits in `answered/1` (retract the answer, the question reopens) and
`affirmed/2` (supersede the affirmation, the exposure resurfaces). The design's spine is
sound because it is the house's existing spine.

The *conditional* weakening he describes ("defeat all mismatched rows as long as I trust its
competence to scrute the mismatch") is the same construction with the grant carrying the
condition: the rule joins on `trust_grant(G, P, Grade)` where the grant's scope names which
attestation grades it empowers. Weakening full authority to grade-conditioned authority is
then *superseding one grant row with another* — no rule change at all.

### 3.4 The vocabulary gaps, named honestly (do not build from this note; a spec enumerates)

The rule above cannot be grounded today. The concrete gaps, each a fact the engine's export
does not carry:

- **No attestation family.** `ledger_edb.py` exports no attestation facts. The v2 typed kind
  (`model_identity_attested`, spec §8) would export cleanly as a new capability-gated family
  (the columns are typed); the v1 convention rows would require parsing the statement text —
  convention-not-type, cancer G — which is itself an argument that a defeat rule should wait
  for (or motivate) the s44 world.
- **No actor on `entry/6`.** The exported entry fact is `(id, ts, kind, concern, status,
  confidence)` — no actor. The rule needs `row_actor(A,P)` to connect the attestation to the
  granted principal. `ledger_support.lp` already names `row_actor/2` as a scratch-only
  stand-in EDB fact ("from the ledger `actor` column"), so the shape has precedent; the
  standing export simply does not emit it yet.
- **No grant family.** The kernel-shape families (`obliged`, `acts_for`, `agent_class`,
  `regards`, review facts) are declared in `ledger_edb.py` as capable-but-DEFERRED — never
  emitted, `require()` refusing loudly — and the s41 competence-grant columns are not in the
  family vocabulary at all. A `trust_grant`/`competence` family is a new export.
- **The grade lattice does not exist.** The attestation grades are a closed vocabulary
  (good), but the s41 competence *band* is ratified free text, a placeholder architecture by
  the maintainer's own loud note (§9(g)). A grade-conditioned defeat rule needs an *ordered*
  comparison ("empowered at grade ≥ X"), which free text cannot support. Closing the band
  vocabulary is therefore a prerequisite of conditional defeat — a fact that should feed the
  already-deferred band-vocabulary decision when it is taken.
- **Countersignature facts (for P2's heavy grades)** exist on the SQL side
  (`review_detail`, `countersigned_in_force`, `discharging_attest`) but their EDB families
  are in the same DEFERRED set. A defeat rule conditioned on "attestation countersigned by a
  human" needs them emitted, plus `agent_class`.

None of these is deep; all are additive export work plus the s44 kind. They are listed so
the future spec inherits an enumerated bill of materials instead of rediscovering each gap
as a DIVERGE_DEFECT.

## 4. Cascade policy — the reserved decision, framed in full

The defeat rule of §3 defeats *the mis-declared row itself*. The hard question is
downstream: when the defeated row is one other rows depend on — a ratification written under
a mis-declared model that later work `enacts`; a `work_closed` row whose close unblocked a
dependent item's strict close; a countersigning `review` row — what does the defeat do to
the dependents?

### 4.1 What the edge vocabulary can and cannot say today

The record carries several distinct edge families, and they do not mean the same thing:

- `supersedes` — replacement lineage (whole-row defeat; the one retraction mechanism, s31).
- `enacts`, `answers`, `amends`, `regards`, `refs` — support, resolution, clause-challenge,
  judgment-about, and free citation respectively; `ledger_support.lp` already classifies
  which of these are *support* edges (enacts, answers, assumes) and which deliberately are
  not (amends is challenge; regards is judgment-about; refs is untyped citation).
- s30's `edge_type` on `work_depends_on` rows — the only *typed* dependency vocabulary in
  the kernel, exactly two values: `blocks-close` (load-bearing: the strict-close AND-tree
  conjoins only these) and `informs` (context; never gates), with `supersedes` actively
  refused as an edge-type value because row supersession already has its one home.

So the honest statement of expressive power: **the s30 vocabulary can carry a
defeat-transmission distinction today only for work-item dependency edges** — "blocks-close
transmits, informs does not" is a coherent, already-typed reading — while the general ledger
edges (enacts/answers) carry no per-edge type at all; their transmission semantics would be
per-*family*, not per-edge, unless a future delta types them (which s30's own reserved-word
discipline suggests doing as a new column, never by overloading).

### 4.2 The coherent policy points, each with its failure mode

1. **No cascade.** Defeat stops at the mis-declared row; dependents stand untouched.
   *Failure mode:* under-delivery of the intent — a ratification is defeated and every act
   ratified under it continues to read as cleanly derived from an in-force antecedent's
   conclusion, which is precisely the censored-record shape the engine's
   `stale_enactment_row` judgment exists to expose for supersession. The defeat would be
   quieter than the supersession it imitates.
2. **One-hop over typed edges.** Direct dependents (rows whose `enacts`/`answers`/
   `blocks-close` edge lands on the defeated row) are defeated; depth ≥ 2 untouched.
   *Failure mode:* arbitrary — the depth-1 boundary answers no principled question, and
   `ledger_support.lp`'s own header records the lesson already paid for: "the harness
   detects dependents of an invalidated row ONE HOP OUT only; depth ≥ 2 was dark," which is
   the gap the transitive support closure was built to close. Re-minting a one-hop rule
   would re-open a closed defect class.
3. **Typed-edge-selective transitive defeat.** Defeat propagates transitively but only
   along edges typed as load-bearing (`blocks-close`; plausibly `enacts` as a family), never
   along `informs`/`refs`/`regards`. *Failure mode:* the pole's danger, moderated but not
   removed — one `exact-command` attestation on an early, load-bearing row can unravel a
   world's derived history in a single pass, with the blast radius decided by graph shape
   rather than by anyone's judgment; and today's edge typing is too sparse to carry it
   (§4.1), so most propagation decisions would silently fall to the untyped per-family
   default.
4. **Unbounded transitive defeat over all support edges.** *Failure mode:* the full
   one-attestation-unravels-history hazard, plus a semantic error: defeat of a support
   *antecedent* does not actually falsify the dependent — the dependent's work may stand on
   its own merits — so hard transitive defeat overclaims, exactly the overclaim
   `ledger_support.lp` §1.2 forbids its own vocabulary ("`exposure` is a statement about the
   SUPPORT GRAPH, never about the dependent's truth").
5. **Transitive exposure, human-discharged (the house's existing shape).** The defeated row
   is hard-defeated (§3); its transitive dependents are *flagged* — the existing
   `exposure(F,D)` machinery, fed by model-defeat as one more defeat source beside
   supersession — and each flag is discharged only by an explicit, SoD-gated affirmation
   act by a clean principal, or escalated into a real supersession of the dependent.
   *Failure mode:* human latency — a large blast radius becomes a large review queue, and
   until worked through, the record shows flags rather than conclusions. (This is arguably
   the honest state of knowledge: after learning the antecedent's provenance was false,
   "each dependent needs re-examination" *is* the truth.)

### 4.3 The countersign interaction

Does a surviving countersign by a clean principal shield a defeated row's conclusion? The
house precedent answers more precisely than yes/no: **a countersign made before the
attestation does not shield, and a fresh one made after it does.** `ledger_support.lp`'s
attestation-currency rule is explicit that an affirmation is keyed to the specific
antecedent-defeat it examined — "a fresh defeat X ≠ D raises fresh exposure the old
affirmation does NOT cover" — and the reasoning transfers whole: the pre-defeat
countersigner reviewed the row believing its declared provenance, so their attestation is
evidence about content under a premise the mismatch has since falsified; it cannot
retroactively become evidence about the falsified premise. A *post-defeat* affirmation by a
clean, stamp-distinct principal ("re-examined in light of the model mismatch; the conclusion
survives") is exactly the discharge act policy 5 is built from. Under policies 2–4 the same
question becomes "does a countersign block propagation," which smuggles a shield semantics
into a row that never claimed it — a further reason those policies sit less well in this
record than policy 5.

### 4.4 The reserved decision

This note's inclination, offered with its honest alternative rather than as a default: policy
5 (hard defeat of the attested row; transitive *exposure* of dependents over the existing
support closure; discharge by SoD-gated affirmation) — because it reuses machinery that
exists and is witnessed, states exactly what is known and no more, and gives the countersign
question the answer §4.3 shows the record already implies. The honest alternative is policy
3 for the `blocks-close` subgraph specifically, where the AND-tree semantics ("this close is
valid only if that one was") genuinely does transmit invalidity in a way prose support does
not — a hybrid (5 generally, 3 on `blocks-close`) is coherent and may be what the work-item
layer wants.

**Reserved for the maintainer, one enumerated-answerable sentence:** *When a
model-defeated row has dependents, shall defeat (a) stop at the attested row, (b) propagate
one hop over typed edges, (c) propagate transitively over load-bearing edge types only, (d)
propagate transitively over all support edges, or (e) hard-defeat the attested row and
transitively FLAG dependents for SoD-gated human discharge — with (e), optionally hybridized
with (c) on the blocks-close subgraph, being this note's recommendation?*

## 5. Stratification — the discipline that must never be lost (the sidenote's core case)

The hazard: the defeat machinery must not be able to eat itself. Concretely, the sentry's
attestations must not defeat the trust grant that empowers the sentry, an attestation must
not attest itself (or a sibling attestation) into or out of force, and no rule may create a
loop in which whether R is defeated depends on whether R is defeated.

**How the engine as it exists handles this.** Today's programs are stratified by
construction: the only negation-as-failure in the core sits at one seam (`not superseded(X)`
over the monotone `sup_star` closure), `ledger_support.lp` confines its one further NAF step
to the discharge join and says so in its header (§1.5), and the append-only ledger's
earlier-target validation makes every edge strictly backward in row id, so the closures
terminate. Clingo would *accept* a non-stratified program (stable-model semantics tolerates
recursion through negation), but it would answer with multiple answer sets or none — and the
SQL floor, whose recursive CTEs are monotone-only, could express no twin for it. So in this
codebase, an unstratified defeat rule does not fail subtly at the semantics layer; it fails
loudly at the differential: no SQL twin exists, and the judge goes DIVERGE_DEFECT or
QUARANTINED. The AGREE discipline is, structurally, a stratification enforcement mechanism —
a fact worth stating because it means the guard is mechanized, not prose.

**The discipline for a future rule author, stated as three rules:**

1. **Defeat rules consume the supersession layer, never their own layer.** Every in-force
   test inside a defeat rule's body — on the attestation, on the grant — is `not
   superseded(X)` (layer 0), never `credited(X)` or `not model_defeated(X)` (layer 1).
   The moment an attestation's power to defeat depends on the attestation itself being
   undefeated, `model_defeated` recurses through its own negation and stratification is
   gone. An attestation or a grant leaves force by *supersession only* — which is also
   s31's ratified semantics ("no kind carries its own defeat semantics"), so this rule is
   the existing law read forward, not a new constraint.
2. **The defeat machinery's own input kinds are outside its target domain.** The rule never
   fires on rows of the kinds it consumes: not on attestation rows, not on trust-grant
   (competence) rows. The sentry spec already carries the operational half (the sentry never
   attests its own rows, §6); this is the derivation-side half, and it is what makes "the
   sentry defeats its own trust grant" unrepresentable rather than merely forbidden. If the
   maintainer ever wants an attester's attestations challengeable, the sanctioned route is
   the one that already exists for every row: supersede the attestation, or supersede the
   grant — acts by a *different* authority, on the record.
3. **New defeat sources join `exposure`'s source set, not `in_force`'s definition.**
   `in_force/1` (and its SQL twin `ledger_current`) stays supersession-only, permanently;
   model-defeat and any future defeat source compose *beside* it as separately-named
   judgments (`credited`, exposure-feeding), the way `countersigned_in_force` and
   `exposure/2` already do. This keeps layer 0 a fixed point every producer agrees on, and
   keeps every added defeat source a strictly additive stratum on top — which is also what
   keeps each addition inside the class-ratifiable fail-safe shape (a new derived view,
   nothing existing relaxed).

## 6. Defeat-of-defeat — resurrection semantics, and the trap to not walk into

Supersede the mismatch attestation A, and on the next derivation pass `not superseded(A)`
fails, `model_defeated(R)` vanishes, and R reads as credited again. **Resurrection on
supersession of the defeater is the implicit semantics of the §3 construction** — and for
the case "the attestation was *wrong*" it is exactly right: a false accusation withdrawn
should leave no residue, and under P1 the whole episode stays in history.

The trap is the *other* case, and the reserved-designs note's resurrection-trap precedent
(§1.3 there: an unbind that silently resurrects the next-oldest role declaration, re-binding
the role to a principal nobody chose) names its shape: **a retraction whose side effect
silently promotes a state nobody affirmed.** Here: the attestation is withdrawn not because
it was wrong but because it was, say, coarse-graded — and its supersession silently
re-credits a row that is still under suspicion, with no one having decided that. Two
disciplines close the trap without any new semantics:

- The sanctioned correction idiom is *supersede-and-replace* (the sentry spec's own §6
  hygiene: "a corrected attestation supersedes its predecessor") — a replacement mismatch
  row keeps the defeat continuous; a bare retraction is the "accusation withdrawn" case and
  *should* resurrect.
- Resurrection is *surfaced, never silent*: a derived view — mirror of s31's
  `orphaned_by_retraction` member, e.g. `resurrected_by_retraction` — listing rows whose
  defeat lapsed because their defeater (attestation or grant) was superseded without
  replacement, so the operator sees every implicit re-crediting the lapse mechanics produce.
  This applies with full force to the grant-lapse case of §3.3: superseding a trust grant
  re-credits *every* row that grant's attestations defeated, at once — precisely the "easy
  way" the maintainer wants, and precisely the event that must land in a view, not pass in
  silence.

## 7. Temporal semantics — defeat at T_now versus as-of reconstruction

The T_now derivation is deliberately atemporal-over-the-current-record: it answers "given
everything on the record now, what stands," and defeat as constructed in §3 inherits that —
it is a property of the asking-time derivation, not a stored interval. The engine already
carries the one genuinely temporal defeat predicate, and it shows the sound pattern:
`defeated_asof(D,E) :- sup_star(X,D), entry(E,_,_,_,_,_), X < E` (`ledger_tnow.lp`) — "was D
already defeated when E cited it," keyed on row *id*, which is the record's one sound total
order (id-is-the-order, never ts). A model-defeat as-of judgment, if ever wanted, is the
same shape: an attestation and a grant both with id < E defeat R as of E. Cheap, sound, and
id-denominated.

`./led work asof <ts>`, by contrast, is a *raw event replay* — its own output says so
("asof is a RAW event-reconstruction (open/claimed/closed only)"): it filters work events to
`ts <= T` and replays them, consulting neither supersession nor any derived discharge logic.
So the honest answer to "what does `led work asof` show for a defeated interval" is:
**exactly what the events up to T said, with no defeat (and no supersession) applied — by
design, and its stderr note already teaches this.** The envelope point to keep: there are
two distinct as-of questions — "what had been *recorded* by T" (raw replay; `led work asof`)
and "what would the derivation have *concluded* at T" (the `defeated_asof` id-bounded
construction) — and any future defeat-aware temporal surface must say which it answers,
because conflating them is how a reader comes to believe a defeat was retroactively edited
into history, the exact misreading P1 exists to foreclose. "Even after the fact" in the
sidenote is thereby given its precise meaning: the defeat changes every *conclusion drawn
after* the attestation lands, and no *record or replay of* what was concluded before.

## 8. The judge differential — every defeat rule lands on both sides or the run goes red

The engine's trust criterion is two independent producers over one EDB in bit-identical
agreement: `ledger_tnow.lp` (ASP) versus `ledger_floor.py`/the kernel views (SQL),
differentialed by `./judge` with any undeclared divergence DIVERGE_DEFECT (red). A defeat
rule added to one side only makes every subsequent comparison of the affected judgments
diverge — so the AGREE discipline *forces* each defeat-rule addition to ship as a pair (the
ASP stratum and its SQL view twin) plus the new EDB families of §3.4, witnessed in AGREE on
a fixture carrying both polarities (a defeated row, a lapsed grant, a resurrected row)
before trust. This is the same bill every kernel delta already pays (s31's ENGINE closure
leg is the worked precedent), and §5's observation gives it a second job: what SQL's
monotone recursion cannot express, the pairing requirement excludes — the differential is
the mechanized guard on the stratification discipline.

On authority: neither producer is the authority over the other — the *agreement* is the
authority, and a disagreement means the encoding is untrusted, not that one side wins
(DIVERGE_BY_DESIGN exists as a declared-lens escape and is deliberately empty this
increment). Operationally, the kernel's SQL views are what the CLI and any future gating
consumer actually read, so a defeat rule *takes effect* through the SQL side — one more
reason the SQL twin is never the deferred half of the pair.

## 9. The serving surface — how a computed defeat reaches an operator's screen

*(Provenance: maintainer addendum to this same commission, mid-flight 2026-07-18, verbatim:
"If this is all out of reach, ergonomically speaking, for SQL, why don't we have a single
surface to access the ledger like a standing daemon? As far as I know, autoharn-panel writes
SQL directly which is just bad. What I would want from the SPA is to never even display
over-ruled ledger rows (including computed-overruled, not just pointwise -- that is to say,
the clingo layer should be able to invalidate wholesale all rows written e.g. by a model
claiming to be someone else, without having to add a supersedes row to every row it authored,
right?)" — the "autoharn-panel" he names is the ledger-viewer SPA, whose design lives in its
own repository per [design/FABLE-SPA-FEATURE-SPEC.md](../../design/FABLE-SPA-FEATURE-SPEC.md)'s pointer;
this section reasons from his characterization of its access path without re-verifying that
repository.)*

### 9.1 The wholesale point, confirmed — one derivation, already given

His "right?" is right, and it is not a new derivation — it is exactly §3's construction read
at class width. Derivation-layer defeat is *class-quantified by construction*: the rule
`model_defeated(R) :- mismatch_attest(A,R,_), not superseded(A), ...` fires once per row the
attestation set covers, and a sentry attesting "every row this session wrote carried a
mis-declared model" produces one attestation per row *by the attesting verb's own batch run*
— or, with a session-scoped attestation shape, literally one row covering the class — with
**zero `supersedes` rows written anywhere**: no per-row retraction act exists or is needed,
because defeat is computed at read time from the attestation + grant, never stored per
victim (P1). That is the same zero-cleanup property §3.3 confirmed for the lapse direction,
here run forward: one act in, the whole class's derived status out, recomputed fresh every
pass. The only caveat worth carrying: `supersedes` remains the one *retraction* mechanism
(s31) — computed defeat discounts rows in derived views; it never substitutes for a
supersession where the maintainer actually wants the record's replacement lineage to say so.

### 9.2 The write half is already answered; the open question is reads

The "single surface" wish splits cleanly. For *writes*, the ratified s42/s43 family
([design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md](../../design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md),
commit `3277461`) already closes raw SQL structurally for every post-s43 world: `INSERT` on
`ledger` is revoked from the granted role and every write enters through the boundary
functions, with a malformed attempt recorded as a typed `write_refused` row. A daemon adds
nothing to that half. The serving question is therefore entirely about **reads**: today the
in-force truth lives in SQL views any client queries directly, the ASP layer runs only when
the differential runs, and a defeat stratum per §8 must exist on both sides — so the real
architecture question is *which producer's output a display client consumes, through what*.

### 9.3 The read architectures, enumerated with honest costs

- **(a) A standing read daemon.** One long-lived service recomputes the composed derivation
  (SQL views + defeat stratum; optionally grounding the ASP side too) on ledger change
  (Postgres `LISTEN/NOTIFY` on the append is the natural trigger) and serves the credited
  set over one read API — the SPA's only source. *Gains:* one surface, always-current,
  ASP-expressible judgments servable even where SQL is awkward. *Honest costs:* a new
  standing process with the availability problem (daemon down = no reads, or stale reads —
  which failure mode must be chosen and said); and the authority implication is real and of
  the same class as the sentry's: a process that decides what every operator *sees* is a
  high-authority surface — a compromised or buggy daemon can hide rows the record contains —
  so it wants the sentry's own treatment: a registered principal (class `tool`), a declared
  purpose, and its output auditable against the kernel views it summarizes (the differential
  as auditor, below). Note the asymmetry with the action-stream ruling: the daemon serves
  *display*, not guarantees, so it is permissible tier-wise — but "what the operator saw" is
  itself evidentially significant, which is why hiding must be structurally impossible
  (§9.4).
- **(b) Engine-materialized defeat facts.** The ASP pass (or the shared defeat computation)
  writes its derived `model_defeated(R,A,G)` set into a derived table — outside the
  append-only ledger, a cache not a record — which the SQL views join; clients keep reading
  SQL. *Gains:* no new serving process, the existing psql/view read surface survives, SQL
  clients get ASP-grade judgments. *Honest costs:* staleness between passes (a defeat
  computed at pass N is invisible until someone triggers pass N+1 — who triggers, on what
  event, is the design's load-bearing hole), and a *stored* derived verdict is exactly the
  shape the pairing-RCA invariant warns against ("never write a fact a read-time derivation
  can supply for free") — tolerable only if the table is explicitly a rebuildable cache with
  its generating pass's EDB hash stamped on it, so a stale cache is detectable as stale
  rather than trusted as truth.
- **(c) The null option, stated for completeness: SQL-native defeat, no daemon.** §3's rule
  *is* expressible as an ordinary SQL view (a join over in-force attestations and grants —
  stratified defeat is exactly what monotone SQL can say, §5/§8), so the SPA could simply
  read a `credited_current` view exactly as it reads `ledger_current` today. *Gains:*
  nothing new to run, nothing new to trust, the smallest change. *Honest cost:* it answers
  only the defeat question, not the maintainer's broader single-surface/ergonomics wish —
  and any *future* judgment that genuinely exceeds SQL's reach (none in this envelope does,
  by §5's own discipline) would force the (a)/(b) choice then, with live evidence in hand.

Under every option the `./judge` differential is the auditor of the serving shape: for (a),
the daemon's served set is differentialed against the kernel views (a serving divergence is
a red verdict, not a UI bug); for (b), the materialized table is compared against a fresh
recomputation (staleness surfaces as DIVERGE, the cache's EDB-hash stamp making
QUARANTINED-vs-stale decidable); for (c) it is the existing SQL/ASP pairing unchanged. The
AGREE discipline thus does for the read surface what s43 does for the write surface: the
single-surface property is enforced by comparison, not by hoping every client behaves.

### 9.4 The SPA display contract — the auditability wall, binding

In-force-only (credited-only) is the correct *default* view: that is the ergonomic half of
the wish and it is right. But the standing ruling — ergonomics only with auditability held
constant — makes the second half binding: defeated and overruled rows, pointwise *and*
computed, must remain **reachable** in an explicit history mode, displayed as
defeated-with-cause (§10's flag-and-journal item: which attestation, which grant, what
grade). "Never even display" is satisfied by the default; a display layer that made defeated
history *unreachable* would be the dishonest version of the wish — a censored record worn as
a clean one, the exact shape P1 exists to foreclose — and no serving architecture in §9.3 is
licensed to implement it.

### 9.5 The reserved decision

This note's inclination, with its honest alternative: **(c) now, (b) only when a measured
staleness-free trigger design exists, (a) only if a post-envelope judgment genuinely exceeds
SQL** — because every defeat judgment in this envelope is stratified and therefore
SQL-expressible (§5), the smallest trusted surface is the one already differentialed, and
minting a standing high-authority serving daemon ahead of a judgment that needs it would be
ceremony ahead of substance (the §11-RD-1 lesson from the sentry spec, same shape). The
honest alternative: if the maintainer's single-surface wish is itself the requirement — one
API, no direct psql from any display client, ever — then (a) is the only option that
delivers it, and it should arrive with the sentry-class principal treatment and the
served-vs-kernel differential from day one.

**Reserved for the maintainer, one enumerated-answerable sentence:** *Shall the defeat-aware
read surface be (a) a standing daemon serving the credited set as the single read API
(sentry-class principal + served-vs-kernel differential mandatory), (b) engine-materialized
defeat facts joined by the existing SQL views (rebuildable cache, EDB-hash-stamped,
recomputation trigger to be designed), or (c) an ordinary `credited`-style SQL view read the
way `ledger_current` is today — this note recommending (c) now with (b)/(a) as
evidence-triggered escalations?*

## 10. Further envelope items (the commission's "and beyond")

- **Conflicting attestations.** Two in-force attestations on one row, one `match` and one
  `mismatch` (two attesters, or one attester across grades): the §3 rule as written lets the
  mismatch defeat regardless — defensible (fail-safe: suspicion wins) but it should be a
  *decision*, not an accident, and the conflict should be flagged either way. The engine has
  the exact idiom: `condition2_individuation(T)` fires on ≥ 2 in-force amends over one
  target; the mirror (≥ 2 in-force attestations disagreeing over one row) is one rule.
- **Absence never defeats.** The sentry's R1 (emission is env-controlled; absence of
  telemetry proves nothing) must bind the defeat layer absolutely: no rule may ever defeat,
  discount, or flag a row for *lacking* an attestation. Only a positive in-force mismatch
  attestation defeats. Stated here because a future "coverage-gating" idea — treating
  unattested rows as suspect — would invert the fail-safe polarity of the whole design and
  hand any adversary a defeat-by-silence lever (unset the env var, defeat the world).
- **Defeat is shown with its derivation, never resolved away.** `ledger_tnow.lp`'s
  `launder/3` banks the lesson: auto-rewriting an edge to the "resolved" head produces a
  coherent, false record; the only evidence-preserving move is flag-and-journal. A defeated
  row is therefore always displayed *as* defeated-with-cause (which attestation, which
  grant, what grade) — a `model_defeated(R)` bare atom is under-specified; the shown
  judgment should carry A and G (`model_defeated(R,A,G)`), so every conclusion downstream of
  a defeat can cite its warrant, and `./led show R` can teach it.
- **The grade lattice is a prerequisite, restated as a dependency.** Conditional defeat
  (§3.3) and P2's heavy-grade countersign requirement both need ordered, closed vocabularies
  on the grant side; the s41 band placeholder is the one place the envelope genuinely blocks
  on an open maintainer decision that predates it. Named so the band-vocabulary decision,
  when taken, is taken knowing this consumer exists.
- **Hash chain and refusal recording, untouched.** Defeat writes nothing, so the s26/s42
  chain is unaffected; in an s43+ world a malformed attestation write is itself a recorded
  `write_refused` row — the defeat machinery's failures become audit records for free, a
  composition worth preserving in any build.

## 11. The reserved decisions, enumerated

1. **Cascade (§4.4):** the five-option (a)–(e) sentence there, with (e) [+ optional (c) on
   `blocks-close`] as this note's recommendation.
2. **Serving surface (§9.5):** the three-option (a)–(c) sentence there, with (c)-now as this
   note's recommendation.
3. **Conflicting attestations (§10):** *Shall an in-force `mismatch` attestation defeat a
   row even while an in-force `match` attestation on the same row stands (yes — fail-safe,
   with the conflict flagged), or shall conflict suspend defeat pending human disposition
   (no)?*
4. **Heavy-grade countersign threshold (P2, §10):** *Which target-row kinds (ratifications /
   decision-grade rows / work-closes / all) require a human-countersigned attestation before
   defeat fires, rather than an uncountersigned one?*

Everything else in this note is either confirmed against existing machinery (§3's
construction and lapse, §5's discipline, §6's resurrection mechanics, §7's temporal split,
§8's pairing duty, §9.1's wholesale-defeat confirmation) or an enumerated gap (§3.4) — none of it is buildable from this note
alone, and all of it awaits the future commissioning act the status line names.

## Interaction projection — 2026-07-18: the three reserved designs through this envelope

*(Dated append per ADR-0005 Rule 8, same day as the body; the pin marker above stands. This
section is a maintainer-commissioned consultation (cost attribution: ledger estimate row
1479) on the interaction between this envelope and
[design/FABLE-RESERVED-DESIGNS-2026-07-18.md](../../design/FABLE-RESERVED-DESIGNS-2026-07-18.md) — the
banked design notes on three deferred principal-surface designs: §1 a sanctioned db_role
unbind back to undeclared standing, §2 a lift for suspension with revocation terminal by
type, §3 the deployment-declared competence-band lattice. His framing, verbatim in
substance: project the reserved designs into the envelope and "shave off the residue to
figure out what needs to be done, since the defeasibility layer is authoritative going
forward regardless." The projection direction is therefore fixed: the reserved designs are
read THROUGH this envelope's constructions, and on any conflict this envelope governs. The
reserved-designs note itself is pinned and is NOT edited by this pass — every finding
against it below is input to the maintainer's ruling on its three ratification questions
(cited here as its Q1/Q2/Q3, the closing questions of its §1.5/§2.5/§3.6), never a change
applied to it. Its text was re-read in full as it stands at sha256
`9f6daa0d3b0967d550e6fbe003da0b6e1bb5908867f1c41467ddbe1ddb5e1d23`.)*

Each residue item below states the interaction in one zero-context paragraph and classifies
it: **(a)** already consistent — the two documents compose with no action; **(b)** a gap
needing future design — an obligation on a named future spec; **(c)** a genuine conflict —
with what the envelope-governs ruling implies for the reserved design. The projection found
no (c)-class conflict that survives inspection; it found one place where the envelope's own
§3.2 text is sharpened by the projection (I1 — recorded as an honest correction, not
softened into a mere "gap"), several real gaps, and several coherent write-time/read-time
disagreements that must stay *named* or they will someday be "fixed" into defects.

### I1 — The active-flag idiom sharpens this envelope's in-force test: `not superseded` is no longer the whole of "in force" — **(b), and a correction to §3.2's letter**

The reserved designs' shared mechanism (§1/§2 there) extends s41's identity/value-split
retraction: a binding or standing is withdrawn by a superseding same-kind row with
`principal_binding_active = false`, so a retraction chain's **terminal row is unsuperseded
but inactive** — s41 D-5's own words: "unsuperseded alone is NO LONGER sufficient." This
envelope's defeat rule (§3.2) tests the trust grant's force as `not superseded(G)` alone,
which is correct for the row the withdrawal superseded but would mis-read the *withdrawal
row itself* as an in-force grant if the grant EDB family were exported naively per-row from
the kind. The projection therefore sharpens §3.4's grant-family gap into a precise
obligation: the exported `trust_grant/…` family must carry (or the exporter must filter on)
the active flag, and the ASP in-force test for any active-flag kind is the **two-conjunct**
"governing and active" — mirroring exactly the reserved designs' own resurrection-proof
view semantics (their §1.3 step 3) and s41 D-5's filter. §3.3's lapse confirmation is
unchanged in substance (a withdrawal still lapses every dependent defeat on the next pass —
via the supersession of G *plus* the inactive terminal row matching nothing); what is
corrected is the letter of the rule body. Spirit intact, letter sharpened; recorded rather
than silently absorbed.

### I2 — The second in-force notion needs one ASP home and extends the judge pairing duty — **(b)**

Generalizing I1: after any of the reserved designs ship, the record carries **two distinct
in-force notions** — whole-row force (unsuperseded; one home per producer, s31's ratified
invariant) and *binding/standing* force (governing row of its chain AND active; SQL home =
the D-5 views and the reserved designs' re-issued `principal_role`/`principal_standing`
filters). The ASP side has no home for the second notion at all today (the kernel-shape
families are declared-DEFERRED in `ledger_edb.py`, never emitted). Before any defeat rule
consumes grants — and before the judge differential ever covers principal machinery — the
envelope's successor spec must mint the ASP twin of "governing and active" as ONE predicate
(one home, ADR-0012 P1), and §8's pairing duty extends to it verbatim: a defeat stratum
whose SQL side reads the D-5 filter while its ASP side reads bare unsuperseded rows goes
DIVERGE_DEFECT on the first withdrawn grant. This is an obligation on the envelope's own
successors, triggered by (not conditional on) any yes to the reserved designs' Q1/Q2.

### I3 — §1's unbind and this envelope are the two halves of one incident response, forward and backward — **(a), with a naming duty**

The unbind (their §1) is deliberately forward-only: after it commits, NULL-actor writes
under the role refuse; rows written under the declaration *before* the unbind remain
attributed to the outgoing principal forever (append-only law; their §1.3 step 5 even
attributes the unbind row itself to the outgoing principal, correctly). So when the reason
for unbinding is "this connection was speaking for the wrong identity," the unbind fixes
the future and touches nothing about the past — and the backward half is exactly this
envelope: a sentry-grade attestation defeating (discounting in derived views) the
misattributed rows, at a declared grade, with the record intact (P1). Neither document
currently says the two compose; they do, cleanly, with zero mechanism change. What needs
doing is naming only: the future unbind spec's operational guidance should point at the
defeat layer as the sanctioned backward-looking correction, so an operator does not reach
for the one thing both documents forbid (retro-editing attribution).

### I4 — The resurrection-proof view semantics and this envelope's §6 are the same discipline, independently derived — **(a)**

Their §1.3 step 3 forecloses the resurrection trap structurally (governing row = latest
unsuperseded regardless of flag; emit only if active — an unbind can never silently re-bind
the role to a stale older declaration), and it composes correctly with s31's
reinstatement-free supersession: superseding the unbind row does not un-name its victim, so
the only path back to bound is a fresh, explicit, active declaration. That is this
envelope's §6 discipline (retraction whose side effect silently promotes a state nobody
affirmed is the trap; sanctioned correction is supersede-and-replace) arrived at from the
other side, and where §6 must settle for *surfacing* implicit resurrection (a derived view,
because attestation-lapse resurrection is sometimes the intended semantics), the binding
views can and do foreclose it *structurally* (resurrection of a stale binding is never
intended). Different strengths at the right places; no action.

### I5 — Suspension does not touch defeat force: the grant, not the standing, is the lever — **(b), a rule the defeat spec must state; mild input to Q2**

Suspending a principal (their §2) blocks its *writes*; it supersedes nothing and withdraws
nothing. So a suspended attester's past attestations, and the still-in-force trust grant
empowering them, continue to defeat rows — and lifting the suspension changes nothing in
the defeat layer, because the defeat rule never consulted standing. This is the correct
default and this projection recommends keeping it deliberate: the sanctioned levers over
defeat force are the *grant* (withdraw it → every dependent defeat lapses, §3.3) and the
*attestation* (supersede it → targeted resurrection, §6); making defeat additionally
consult lifecycle standing would add a standing fact family to the rule body — stratified
and therefore *permissible* (standing derives from lifecycle events + supersession + active
flag, no defeat involvement — discipline rule 1 is satisfiable), but it multiplies the
in-force notions inside one rule and buys nothing the grant lever does not already provide.
The defeat spec must state this as a decided rule either way, or the first author who
notices "suspended sentry still defeating" will patch it ad hoc. The Q2 input: see I7 for
why the lift design *helps* the defeat layer regardless of how this rule lands.

### I6 — Write-time standing and read-time credit can disagree observably, and the disagreement is coherent-and-named — **(a), with a naming duty**

The commission's explicit boundary question, answered for the suspension case: after their
§2 ships, an operator can observe simultaneously that principal P's new writes are refused
(kernel, write time) while every past row P wrote reads as credited (derivation, read
time). This is not incoherence; the two layers answer different questions — "may P act
now?" versus "does row R stand?" — and P1 requires exactly this: standing changes are
forward-only write gating, never a judgment on recorded rows, and past rows lose credit
only by *positive* defeat (an in-force mismatch attestation) or supersession, never by
their author's later standing. The mirror disagreement is equally coherent: a defeated
row's author keeps writing freely (defeat never gates anyone's future writes — the
recordable-not-gating posture). Incoherent disagreement would arise only from crossing the
streams — a write-time mechanism storing a read-time verdict (the pairing-RCA invariant
already forbids stored verdicts) or a defeat rule refusing writes (the envelope's own
posture forbids gating). Both documents must keep this asymmetry *named*, because unnamed
it reads as a bug: "why is the suspended principal's work still credited?" has a one-line
answer only if the record carries it.

### I7 — The lift design materially stabilizes the defeat layer; succession-only would churn it — **(a), and an argument FOR Q2's yes**

Project the case where the *sentry's own* principal comes under investigation (its
attestations look buggy): the sanctioned response chain under this envelope is suspend the
sentry (stop new attestations — write time), then either supersede specific attestations
(targeted resurrection) or supersede the grant (wholesale lapse). Under today's
succession-only posture, clearing the sentry afterward requires a *successor principal* —
new registration, new grant — which lapses every defeat the old grant carried (mass
resurrection of every mismatched row, §6's surfacing view lighting up wholesale) and
re-derives it only after re-attestation under the new identity. Under their §2's lift, the
identity, the grant, and every standing defeat survive the investigation intact: suspension
becomes exactly the reversible precaution their plain-words preamble wants, *and* the
defeat layer sees zero churn. This is a concrete, envelope-side benefit of the lift design
that the reserved-designs note could not have named (it predates the envelope's
authoritativeness) — flagged as ruling input for Q2.

### I8 — The band lattice is the envelope's named prerequisite, arriving in a consumable shape — with one missing piece: the grade↔band mapping — **(b), direct input to Q3**

This envelope named the s41 free-text band a hard prerequisite gap for conditional defeat
(§3.4, §10): "empowered at grade ≥ X" needs an ordered comparison free text cannot supply.
Their §3.3 answers with the right architecture class — `competence_band_defined` events
carrying an integer rank, deployment-owned membership, kernel-computable order — and the
projection confirms the fit: an in-force band-definition family exports as a
`band_rank(Band,Rank)` EDB fact (subject to I1/I2's two-conjunct in-force test — band
definitions are themselves active-flag-retractable in the sketch), and the rank comparison
is monotone, so both producers can carry it and §8's pairing holds. The missing piece
neither document owns: the sidenote's conditional defeat joins **two different lattices** —
the *attestation-confidence* grades (the sentry's closed `exact-command …ambiguous`
vocabulary, kernel-structural per the s44 authoring) and the *competence* bands
(deployment-declared). "Trust its competence to scrute the mismatch" means the defeat rule
needs a declared mapping point: which band suffices to empower defeat at which attestation
grade (plausibly itself an `activity_band_required`-shaped declared event, their §3.3 layer
3, with activity = `model-identity-attestation` — the shape exists; the join is undesigned).
Q3 input: the band ruling should be taken knowing this envelope is a concrete consumer
needing the rank *and* this mapping point.

### I9 — Band-definition withdrawal with extant grants: the lapse spine answers it, the surfacing duty binds it — **(b), input to Q3's eventual spec**

Their §3.3 layer 2 validates grants against in-force band definitions at *write* time. A
definition later withdrawn (active-flag supersession, per the sketch's own idiom) leaves
already-written grants citing a band with no in-force definition — valid at write time,
dangling at read time; the sketch does not say what a reader then concludes. The
envelope-governs answer follows the §3.3/§6 spine: the grant's *rank* lapses with the
definition (the derivation can no longer order it), so every grade-conditioned defeat
resting on that grant's rank stops firing on the next pass — implicit lapse, fail-safe
direction (defeat force shrinks, never silently grows) — and the dangling state is
*surfaced, never silent* (a violations-view member in the `orphaned_by_retraction` /
`resurrected_by_retraction` family: grants-citing-a-withdrawn-band, plus the defeats that
lapsed with them). The future band spec must state this; the answer shape is already
governed here.

### I10 — Both documents' countersign questions converge on one deferred EDB prerequisite — **(b), consolidated bill-of-materials item**

Their §1.4/§2.4 leave open whether unbind and lift want a countersign ceremony
(governance-act attestation by a second principal); this envelope's P2 requires
human-countersigned attestations before heavy-grade defeats fire. Different countersigns —
one blesses a governance *act*, the other strengthens *evidence* — but one machinery
(review rows, `review_detail`, the review-gap debt views) and one shared gap: the
countersign/review fact families are in `ledger_edb.py`'s declared-DEFERRED set, never
emitted, and `entry/6` carries no actor (§3.4). Whichever future spec arrives first — the
reserved designs' or the envelope's successor — pays the same export bill; it should be
paid once, as one enumerated family addition (actor emission, review/countersign facts,
`agent_class`), not twice ad hoc. Consolidated here so neither spec rediscovers the other's
half.

### I11 — Dust-world boundaries: re-grants at birth, defeats per world — **(a)**

Their §3.4 dissolves the band-migration question under runs-are-linear: a new world re-
grants still-believed competences as fresh events citing the prior world's record. The
envelope side composes identically and needs no more: attestations, grants, and therefore
defeats are per-world facts (the EDB is exported per target; a prior world's defeats are
read-only evidence like everything else in it), so a re-granted trust grant in a new world
carries defeat force only over that world's attestations — no cross-world defeat exists to
migrate, and none should. Consistent by construction; recorded so nobody invents
cross-world defeat transport to "fix" it.

### What needs to be done (the shave, summarized with owners)

**Input to the maintainer's ruling on the reserved designs' three questions (no document
edits; carried by this section):**
- *Q1 (unbind):* I3 — the unbind is the forward half of an incident response whose backward
  half is this envelope's defeat layer; the composition is clean and argues no change to
  the design, only that its eventual spec name the pairing.
- *Q2 (suspension lift):* I7 — the lift materially stabilizes the defeat layer (identity,
  grant, and standing defeats survive an investigation; succession-only forces mass
  defeat-lapse churn) — an envelope-side argument *for* yes; plus I5's note that lift/
  suspend deliberately do not touch defeat force.
- *Q3 (band lattice):* I8 and I9 — the architecture class fits the envelope's prerequisite
  exactly; the eventual spec must add the attestation-grade↔band mapping point and the
  definition-withdrawal semantics (lapse + surface), both answer-shapes already governed
  here.

**Obligations on this envelope's own successor spec (future-spec debt, not buildable from
this note):**
- I1 — the grant (and any active-flag) EDB family carries the active flag; the defeat
  rule's in-force test on such kinds is two-conjunct (governing AND active), sharpening
  §3.2's letter.
- I2 — one ASP home for the second in-force notion, and §8's judge-pairing duty extended
  to it before any defeat rule consumes grants.
- I5 — a decided rule that lifecycle standing does not condition defeat force (the grant is
  the lever), or a deliberate ruling otherwise.
- I8 — the grade↔band mapping join, once Q3's spec exists.
- I10 — the consolidated EDB export bill (actor on entries, review/countersign families,
  `agent_class`), paid once.

**Nothing to do (consistent, kept named so they are not "fixed" into defects):** I3's and
I6's coherent write-time/read-time asymmetries; I4's independently-derived resurrection
discipline; I7's composition; I11's dust-world boundary. No (c)-class conflict was found:
nowhere does a reserved design's mechanism contradict an envelope construction — the one
letter-level collision (I1) lands on this envelope's own text and is corrected here, which
is what "the defeasibility layer is authoritative going forward" costs the layer itself
when the projection runs both ways honestly.

## License

Public Domain (The Unlicense).
