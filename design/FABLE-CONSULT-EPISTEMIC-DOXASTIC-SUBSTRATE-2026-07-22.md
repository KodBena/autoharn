# FABLE CONSULT — a typed epistemic-doxastic substrate for the ledger (knowledge-and-belief:
doxastic = of belief, epistemic = of knowledge; 2026-07-22)

**What this document is.** This document is a dated, fresh-context Fable consult, commissioned by the
maintainer 2026-07-21 (ledger row 1888, kind=commission, verbatim: *"Commissioning a ledger
entry now which will be implemented right away: typed epistemic-doxastic substrate in the
ledger so that we can track beliefs and knowledge. Have a Fable consult take a look at the
collective failure modes and suggest a shape for it."*). Dispatched under
[ADR-0018](../law/adr/0018-consults-are-not-front-loaded.md): this
consult received the witnessed problem, its evidence, and the law — no candidate answers.
Nothing here binds anyone; a kernel delta reaches reality only via a Fable-authored,
maintainer-ratified spec entering a future [world](../GLOSSARY.md#world)'s
[birth chain](../GLOSSARY.md#birth-chain) (runs are strictly linear).
This document is input to that spec, not the spec.

**How to read it.** §1 derives what the witnessed failure modes actually demand — the
[ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) Rule 2(a) question
("what type would make this class unrepresentable, or at least
loud?") applied to collective epistemics. §2 surveys what the kernel already represents and
what is genuinely absent. §3 proposes the shape. §4 states composition with the existing
machinery. §5 is this consult's own closure statement. §6 names deliberate exclusions.
§7 ends with the maintainer's decision points as separable prepared questions. Confidence
levels are stated per position; where a position is a judgment call rather than a
derivation, it says so.

**One correction to the commission's surroundings, up front ([ADR-0008](../law/adr/0008-classification-discipline.md) honesty).** The
dispatch referred to "the claims-lane vocabulary wherever it is defined." It is defined
nowhere: no `lane` vocabulary exists in `kernel/lineage/` or [`GLOSSARY.md`](../GLOSSARY.md) (the only
occurrence of the word, `s38-bookkeeping-close.sql` — sNN tokens name the kernel's numbered
lineage deltas, `kernel/lineage/sNN-*.sql`, and that gloss covers every bare sNN token in this
document from here on — uses it colloquially for a
delta-ratification class). The machinery that phrase most plausibly gestures at is the
review/attestation family (`review` + `review_detail` + `regards`; s44
`model_identity_attested`), and this consult composes with that. Flagged rather than
silently resolved, per ADR-0008 Rule 3.

---

## 1. What the failure modes demand

The seven witnessed records share one structure: **a confident belief operated on the
record without ever being ON the record as a belief** — so nothing could type-check its
basis, nothing could demand its quantification universe, and nothing could defeat it except
a human catching it by eye. Each specimen, and the distinction that would have made it
unrepresentable or loud:

### 1.1 The two-bias audit failure (rows 1884–1887; [design/AUDIT-AC-IA-POSTURE-2026-07-21.md](AUDIT-AC-IA-POSTURE-2026-07-21.md))

An auditor's absence-verdicts (AC-1/IA-1 "SILENT", from a repo-only search when the
artifact is born per-deployment) and satisfaction-verdicts (4 of 6 MET-BY-MECHANISM failing
their own control statements; "tamper-evident" strengthened to "tamperproof" in transit)
were both wrong the same day, from the one root row 1887 names: *"evidence-first reasoning,
where what-I-found determines both what-exists and what-suffices."*

Row 1887's own three rules are already the type demand, stated as prose:

- **An absence verdict is a universal claim, and a universal claim without an explicitly
  enumerated search universe is not a claim.** Had "AC-1 is SILENT" been forced to carry
  *searched surfaces: {repo tree, scaffold sources}* as a typed field, the METHOD GAP (the
  born-world artifact surface missing from the list) would have been visible in the row
  itself — contestable by pointing at an unenumerated surface, rather than caught by a
  maintainer who happened to remember a field-test birth. This is ADR-0000 Rule 2(a)'s
  closure-statement quantification universe, applied to verdicts instead of fixes.
- **A satisfaction verdict is a universal claim over the requirement's own clauses** — the
  universe is the clause list of the requirement's full statement, walked before any
  mechanism is examined. Same field, different universe.
- The correction arrived only via maintainer challenge plus an independent re-derivation
  (row 1885, [ADR-0014](../law/adr/0014-executor-second-opinion.md) invoked). The substrate must make *challenge* a typed act — a
  contrary record that visibly contests the verdict — not a conversational event.

**Demand 1: claims are typed by quantifier polarity, and each polarity carries a mandatory
evidence obligation — a universal claim carries its enumerated universe; an existential
claim carries its witness.** (Confidence: high. This is the sharpest single derivation in
the evidence; row 1887 wrote the rule, this consult only types it.)

### 1.2 The attestation incident (decision row 293; [ORCH-ABC-AUDIT-LOOP-RECIPE.md](../user-guide/ORCH-ABC-AUDIT-LOOP-RECIPE.md))

Two independent fresh reviewers attested a document CLEAN, twice; six defects stood, all
caught by the maintainer by eye. The diagnosis's deep factor: *dialect blindness* —
same-family reviewers auto-resolve same-family idiom; the maintainer was the only
different-priors reader in the loop.

The collective belief "the document is clean" was high-confidence and false, and the
confidence was manufactured by counting agreeing witnesses without typing *what kind* of
witnesses they were. Two Sonnet-class fresh forks are SoD-distinct (SoD: separation of
duties — s21 would credit them) but epistemically correlated: they share priors, so their
agreement is weak corroboration.

**Demand 2: corroboration is graded by witness diversity, not witness count.** Agreement
between same-class witnesses must be typed differently from agreement across classes
(model-class vs model-class vs human). The EDB (extensional database — the fact base for
ASP, Answer Set Programming, the clingo logic-programming layer) already carries
`agent_class/2`; nothing reads it for this. (Confidence: high on the demand;
medium on how far to mechanize the
grading in v1.)

### 1.3 The what-did-we-miss RCA (ADR-0000 Revisit #4)

Five independent verification layers each inherited one silent omission — *"the
conformance map inherited the founding brief's silence, the checker inherited the map's,
the review panels inherited the corpus's."* Each layer's "checked" was a coverage belief no
layer actually held first-person: each was **testimony wearing the costume of
verification**, and nothing in any layer's record distinguished "I verified X against the
territory" from "I verified X against the layer above me."

**Demand 3: a claim's basis is typed — first-person observation, derivation from named
premises, testimony from a named source, or assumption — and derivation/testimony edges
form a queryable DAG.** With premise edges, "five independent layers" becomes a *computed,
refutable* predicate (do their premise closures share an ancestor?) instead of an asserted
one. Five layers all descending from the founding brief would have shown a shared root on a
one-line query. (Confidence: high. This is the TMS (Truth Maintenance System) insight the
[2026-07-14 philosophical consult](PHIL-DEFEASIBLE-DECISIONS-AND-HYDRATED-DOCS.md) noted the
ledger has already paid the infrastructure cost for.)

### 1.4 The recidivism study (ADR-0000, 2026-07-02 amendment)

*"The class gets named at exactly the scope of the fix the executor has already built"* —
belief shaped by commitment. The amendment's answer (the closure statement with invariant,
universe, denomination) is already the right type; what the ledger lacks is a **home** for
it: the closure statement is today prose inside a report, not a field a gate can require.
The amendment itself anticipates this: *"where a workflow instrument carries a claim
schema, the closure statement's three parts are required fields, not prose."*

**Demand 4: the universe field of Demand 1 IS the closure statement's quantification
universe, given a typed home — and a claim authored by the artifact's own builder is typed
as self-report** (the s17 `self-review` distinction, extended from reviews to claims), so
the presumption "the class as first named is too narrow" can attach to the right rows.
(Confidence: high.)

### 1.5 The relayed-verdict refusal (downstream world's AUTOHARN_BACKFLOW.md, finding 6 —
AUTOHARN_BACKFLOW.md lives outside this repository, in a downstream deployment's working
tree, so it is not linked here)

The kernel correctly refused to credit an orchestrator's transcription of a subagent's
verdict as independent — testimony vs first-person is already a live kernel distinction
(s17/s21). But the grain is session+agent, so a *genuinely* isolated subagent's first-person
verdict is unrepresentable as anything but `self-review` plus prose disclosure — honest but
lossy: *"understates the review's real independence to any later reader who only reads the
`independence` column."*

**Demand 5: testimony is a first-class basis with a typed source, so a relayed verdict is
recordable AS a relay** — `basis=testimony, source=<the subagent's own record>` — neither
laundered into first-person independence nor flattened into self-review. The independence
question then becomes a property of the *source*, queryable, instead of a property the
relaying writer must either overclaim or forfeit. (Confidence: high on the typing; the
dispatch-identity plumbing that would let the source row itself claim isolation is a
separate, smaller decision — §7 Q6.)

### 1.6 The five A:B:C escalations of 2026-07-21 (rows 1854 context)

Fresh reviewers still finding 3–13 defects per document at the round cap. Reviewer verdicts
are **bounded evidence**: a CLEAN is "I found nothing under this method in this round,"
which is a universal claim over a method-bounded universe — never ground truth. The recipe
already treats it so operationally (round caps, typed escalation); the record does not: an
attestation row reads the same whether it was round 1 of an easy document or the capped end
of a defect stream.

**Demand 6: same as Demands 1+2 applied to reviews — a CLEAN verdict is a universal claim
whose universe is the method actually run, and its credit is bounded by witness diversity.**
No new machinery beyond §1.1–1.2; this specimen confirms the shape generalizes.
(Confidence: high.)

### 1.7 The worktree-isolation snag (row 1852)

The orchestrator's resource model ("touched files are the only conflict surface") was
confidently too narrow, and it existed *nowhere as a record* — it was an operating
assumption whose first appearance in the ledger is its own post-mortem. Nothing could
defeat a belief that was never asserted.

**Demand 7 (the modest one): operating assumptions can be *recorded* as beliefs with
basis=assumed and a stated universe, so a witnessed counterexample defeats something
instead of nothing.** This is the weakest demand — mandating it for every orchestrator
model would be paperwork, not mechanism (the no-certification-bureaucracy bound). Proposed
as opt-in, with one mandated site at most (§7 Q7). (Confidence: medium.)

### The common type, in one sentence

Every specimen is a failure to represent one or more of: **the quantifier** (universal vs
existential, with its universe or witness), **the basis** (observed / derived / testimony /
assumed, with its edges), **the holder's relation to the subject** (self-report vs outside
witness — exists for reviews, absent for beliefs), and **the witness-diversity of
corroboration**. Had these been typed, specimens 1.1/1.3/1.4/1.6 become write-time-loud or
query-time-refutable, 1.5 becomes representable, 1.2 becomes a derived grade instead of a
false collective confidence, and 1.7 becomes defeasible. None requires representing degrees
of belief numerically, and none requires modeling anyone's mind.

---

## 2. What the kernel already represents vs what is genuinely absent

Already present (the substrate must compose with, not duplicate):

- **The doxastic event store and its defeat discipline.** The ledger is `T_event`; current
  truth is derived (`ledger_current`, ASP `in_force/1`); supersession is uniform retraction,
  reinstatement-free (s31), with a hard reader-type discipline (current-truth readers factor
  through `ledger_current`; history readers are allowlisted). "The ledger is built for
  defeasible reasoning" is not aspiration — it is s31 + `engine/lp/ledger_tnow.lp`.
- **A working defeat calculus for one proposition family.** s44 + the defeat pipeline:
  graded testimony (`attest_grade`) by an empowered principal (`trust_grant`) defeats a row
  in derived reads only (`model_defeated`, `credited`), computed fresh by two independent
  producers compared bit-identically (`./judge --layer defeat`), with transitive exposure
  flagging and SoD-distinct discharge. This is precisely a doxastic-defeat mechanism —
  scoped today to exactly one proposition ("this row was written by the model it claims").
- **Testimony-vs-first-person, at coarse grain.** s17's independence vocabulary +
  s17/s21 stamp distinctness: `self-review` vs claimed-independence, refused unless the
  stamps prove distinct invocations.
- **A typed, inert confidence slot.** `confidence IN ('low','medium','high')` on every row,
  exported to ASP as `entry/6`'s sixth argument, consumed by no rule. Empty on every
  evidence row this consult examined.
- **The graded-token idiom.** s36: kernel stores an uninterpreted typed token
  (`decision_grade`), deployment policy gives it meaning. The established layering split
  for any grading this substrate needs.
- **Evidence custody.** s26/s42 hash chain; s48 witness-token existence checks
  (`row:<id>`); s51/s52 content-addressed artifact store (`artifact:<hash>`). A belief's
  witness can already point at bytes that cannot silently change.
- **The write path.** s43's typed-verdict write boundary: a refusal is committed evidence
  (`write_refused`), never an aborting exception. New refusals land here for free.

Genuinely absent — the four holes the specimens fell through:

1. **No kind whose semantics is "principal P asserts proposition S on basis B."** Reviews
   assert verdicts *about rows*; attestations assert one fixed proposition; decisions
   record rulings (speech acts of authority, not of belief — the 2026-07-14 consult's
   preference-act/assertion-act split, which this substrate finally gives a typed home:
   assertion-acts become beliefs, preference-acts stay decisions).
2. **No quantifier polarity, hence no universe obligation anywhere.** Nothing in the schema
   can distinguish "X exists (here it is)" from "no X exists (here is where I looked)".
3. **No premise/testimony edges**, hence independence-of-verification is asserted, never
   computed. (`regards` relates a review to its target, not a belief to its grounds.)
4. **No witness-diversity accounting.** `agent_class` reaches the EDB and stops.

---

## 3. The proposed shape

### 3.0 The stance (the one-sentence design)

**Belief is a stored, typed speech act; knowledge is a derived, never-stored judgment over
beliefs.** This is `measurement ⊥ interpretation` applied to epistemics, the same move the
defeat pipeline already made ("computed fresh, nothing stored"), and the same move `T_now`
makes over `T_event`. A stored "knowledge" bit would be a second writer of a derivable
truth — cancer B. (Confidence: high; this is the position I hold most firmly in this
consult.)

### 3.1 The kind: `belief`

One new ledger kind, `belief` (26th member of the closed kind vocabulary), following the
s44 idiom: typed columns with two-way kind-shape CHECKs, written through the existing s43
boundary, hash-covered (the new columns join `compute_row_hash`; `gates/hash_coverage_gate.py`
keeps totality checked).

*Naming.* The kind is named `belief` — maintainer-delegated resolution, 2026-07-22, ledger
rows 1893–1894, superseding this consult's own lean toward `claim`; the full history and
reasoning are recorded once, at §7 Q1, not repeated here. The *holder* is the existing
`actor` + stamp; no new holder column (one home per fact).

Columns (prefix `belief_`, per the `attest_*`/`refusal_*` house pattern):

| column | type / domain | obligation |
| --- | --- | --- |
| `belief_polarity` | closed CHECK: `universal` \| `existential` | mandatory (two-way kind-shape CHECK) |
| `belief_universe` | text: the enumerated quantification universe — searched surfaces, clause list, axes, sibling surfaces; `row:<id>` / `artifact:<hash>` tokens existence-checked (s48 pattern), including registry references where a registry exists ([law/STANDARDS-REGISTRY.md](../law/STANDARDS-REGISTRY.md)) | mandatory iff `polarity='universal'` (two-way coupling CHECK) |
| `belief_witness` | text: witness tokens (`row:<id>` / `artifact:<hash>`), existence-checked | mandatory iff `polarity='existential'` AND `basis='observed'` |
| `belief_basis` | closed CHECK: `observed` \| `derived` \| `testimony` \| `assumed` | mandatory |
| `belief_source` | bigint FK → ledger(id): the source record a testimony relays | mandatory iff `basis='testimony'` (two-way) |
| `belief_premises` | bigint[]: the rows this belief is derived from (the `enacts` idiom: the kernel's existing bigint[] column naming the earlier design-antecedent row(s) a row carries into force) | mandatory non-empty iff `basis='derived'` |
| `belief_subject` | bigint FK → ledger(id), nullable: the row the proposition is about, where there is one (the `regards`/`attest_row_id` idiom) | optional |

The proposition itself lives in `statement` (one home; no second text column). The existing
`confidence` column is finally load-bearing here as the holder's own three-valued
self-grade — and, following the attestation-grade precedent, **deliberately unread by the
crediting rules in v1** (a self-grade steering credit would be self-certification;
direction-only until a ratified rule reads it).

*Why the polarity dichotomy is the core.* Row 1887's two biases are the two constructors of
this type, each with its mandatory evidence field. An absence/coverage/satisfaction verdict
is `universal` and **cannot be written without its universe** — the two-bias failure and the
five-layer failure become write-time refusals, not audit-time luck. A presence/finding
verdict is `existential` and cannot claim `observed` without a resolvable witness — the
"WITNESSED (with observed output)" contract of CLAUDE.md, typed. The dichotomy is total for
assertion-acts (a proposition either quantifies over a stated domain or exhibits an
instance); what it does not cover is normative/preference content, which is excluded by
construction — those are decisions (§6). (Confidence: high on the dichotomy; the honest
residual is mixed beliefs — "all X except this one Y" — which decompose into one universal
plus one existential row, and the teach-text should say so.)

### 3.2 The refusals (all fail-safe additive, s43-committed, refuse-and-teach)

1. `universal` without `belief_universe` → refused. Teach-text carries row 1887 rule 1
   verbatim: the surface list derives from *where the system produces artifacts of that
   kind*, not from where the auditor happens to stand.
2. `existential`+`observed` without a resolvable `belief_witness` → refused (teach: a
   finding without its witness "is treated exactly as [ADR-0005](../law/adr/0005-documentation-discipline.md) Rule 9 treats a verdict
   without its artifact: as nothing").
3. `testimony` without `belief_source`, or `derived` without `belief_premises` → refused.
4. Witness/universe row-tokens that cite nonexistent rows → refused (s48 mechanism reused).
5. What is **unrepresentable by construction** (stronger than any refusal): relaying
   another's verdict as one's own observation — the relay is `testimony` with a mandatory
   source, and `observed` demands a witness the relayer does not have. Finding 6's
   laundering path is closed at the type layer.

What stays honestly review-only, declared per [ADR-0011](../law/adr/0011-mechanization-discipline.md) Rule 1: whether an enumerated
universe is the *right* universe (a lazy universe is representable — the type makes it
visible and contestable, not impossible), and whether a paraphrase strengthens its source's
vocabulary. No mechanism reads meaning; the substrate's job is to force the material for
that review onto the record.

### 3.3 Revision, contest, defeat

- **Revision** = supersession by the holder, unchanged s31 semantics: uniform retraction,
  reinstatement-free, new position = new row. Same-kind identity-continuous supersession
  discipline (the s45 pattern) applies: a `belief` is superseded by a `belief`.
- **Contest** (the new derived state, and this consult's answer to "how does defeat work
  for beliefs"): two in-force beliefs by SoD-distinct principals whose statements are
  registered as contrary (a typed `contests` relation — proposed as reuse of the existing
  `amends`-style targeted edge on the contesting belief: `belief_contests bigint FK`, set by
  the challenger) put **both** beliefs into a derived `contested_beliefs` view, and both are
  excluded from crediting until one is superseded or a belief of higher evidential standing
  (below) resolves it. This is the house's own `suspect`/paraconsistency idiom: a
  contradiction does not explode and does not silently pick a winner by recency — it
  demotes both to visible, blocking doubt. The maintainer's AC-1 challenge becomes: write a
  contesting belief citing the uncovered surface; the SILENT verdict is instantly
  un-credited, loudly, before anyone adjudicates. (Confidence: medium-high. The alternative
  — extending the empowered-defeater calculus so a trust-granted principal's contrary belief
  *defeats* rather than contests — is cleaner where a ground-truth hierarchy exists
  (instruments over testimony) but imports the grant-management machinery for every
  proposition family on day one. Offered as §7 Q3.)
- **Defeat by evidence class, not by recency.** Within a contest, a belief whose basis is
  `observed` with a resolvable witness outranks `derived` outranks `testimony` outranks
  `assumed` — a small, closed precedence the ASP layer applies to *resolve* a contest only
  when the bases differ, never when they tie. Recency never resolves a contest between
  distinct principals (the 2026-07-14 consult's assertion-act rule: the record beats
  memory; a newer confident assertion is not better evidence). Recency governs only
  self-revision, which is supersession anyway.

### 3.4 Knowledge: the derived views (never stored)

Current-truth readers, all factoring through `ledger_current` (s31 discipline), each with
an ASP twin and a SQL floor twin registered as a new `./judge` layer (`--layer belief`),
compared bit-identically, both-polarity witnessed on a scratch schema before any
ratification — the full s46/s50 discipline, including the s50 lesson (any
machinery-input exclusion domain quantified over raw history in both producers):

- **`belief_current`** — in-force beliefs (the trivial base view).
- **`contested_beliefs`** — §3.3's mutual-doubt surface, with both row ids and the
  contesting edge (cause always visible; a consumer that hides it implements a censored
  record, per the credited-view display contract).
- **`credited_beliefs`** — in-force, uncontested, well-founded beliefs: the basis chain
  bottoms out in `observed`-with-witness or in an in-force non-belief ledger row; every
  chain edge in force. This is the substrate's "knowledge" surface, and the honest name for
  what it computes is *credited belief* — defeasible, revisable, exactly not
  Platonic knowledge. Whether the operator verbs may present it under the commission's
  word "knowledge" is a naming decision the maintainer owns (§7 Q1); this consult's
  position is that `credited` is the word that survives ADR-0008 and "knowledge" belongs in
  prose ("what the project currently credits as known"), not in a view name.
- **`corroboration`** — per credited belief, the derived witness-diversity grade, closed
  vocabulary: `uncorroborated` | `corroborated-same-class` | `corroborated-cross-class`,
  computed from SoD-distinct concurring beliefs joined to `agent_class` (human principals
  are a class). Two fresh Sonnet Bs agreeing reaches `corroborated-same-class` and can
  never reach `cross-class` — the attestation incident's false collective confidence
  becomes a grade the record cannot overstate. Deliberately a *reported* grade, gating
  nothing in v1 (the attestation-grade precedent: carried, unread by defeat).
- **`shared_premise`** — for any set of beliefs asserting the same proposition: the common
  ancestors of their premise/testimony closures. "Five independent layers" is henceforth a
  query whose answer can be *no* — the transitive closure is ASP's home ground and the
  clearest single payoff of wiring this substrate into the deductive engine, which the
  standing maintainer position says is the point of the project.

### 3.5 Staging

Two-step, mirroring the attestation family's own v1-statement-convention → s44-typed path
(the defeat EDB already parses both arms):

- **v1 (no kernel delta, witnessable immediately):** a statement-prefix convention on
  `kind=decision` rows — `belief[universal|existential] basis=<...> universe=(...)
  witness=(...) source=row:<id> :: <proposition>` — with the EDB parser and the derived
  views' engine-floor forms built against it, both-polarity witnessed on scratch chains.
  This proves the derivation rules and the vocabulary against live use before any type is
  frozen, at the cost that v1 obligations are parse-time, not write-time.
- **v2 (the typed delta, next world's birth chain):** the `belief` kind and columns of
  §3.1–3.2, refusals at the s43 boundary, views in kernel, `--layer belief` in
  `engine/lp_registry.py` `LAYERS`. Kind + refusals + derived views is within the
  class-ratified fail-safe *shape* (the standing ruling in
  [CLAUDE.md](../CLAUDE.md)'s ORCHESTRATION section: a kernel delta that only ADDS
  refusals, vocabulary, or derived views — nothing existing relaxed or changed — and that
  arrives witnessed on a scratch schema on both polarities enters the birth chain without a
  per-delta maintainer question), but this delta should route to the maintainer as a
  ratified spec regardless: it mints vocabulary the whole project will reason in, which is
  exactly what his ratification bandwidth is reserved for.

---

## 4. Composition with the existing machinery (stated precisely)

- **s43 write boundary:** beliefs enter via `kernel.ledger_write`; every §3.2 refusal is a
  committed `write_refused` row with teach-text. No new write path.
- **s26/s42 hash chain:** new columns join `compute_row_hash`; the coverage gate's totality
  check is the net.
- **s31 supersession:** unchanged and load-bearing — belief revision *is* supersession; all
  §3.4 views are declared current-truth readers factoring through `ledger_current`; the one
  history reader (`shared_premise` needs in-force edges only, so none is proposed) —
  if a forensic variant is later wanted it goes on s31's allowlist with a reason.
- **s17/s21 independence + review machinery:** untouched in v1. The bridge — deriving a
  testimony-basis belief in the EDB from every `attest`/`refuse` review so reviewer verdicts
  enter the corroboration/premise calculus — is designed but held back as §7 Q5, because it
  doubles the blast radius of the first increment. Finding 6's dispatch-grain fix
  (an independence value shaped like `disclosed-isolated-dispatch`, or dispatch-id keying
  of stamp distinctness) is a separate small delta the substrate makes *worth having*
  (testimony rows want sources whose isolation is itself typed) but does not require —
  §7 Q6.
- **s36 graded-decisions idiom:** if any grade beyond the closed vocabularies here ever
  wants policy meaning (e.g. which corroboration grade a given deployment demands before
  acting), it follows s36: kernel stores the token, `apparatus.json` gives it force.
- **s44/defeat pipeline:** untouched. Model-identity defeat continues to govern *rows*;
  belief contest governs *propositions*. A defeated row that is some belief's witness or
  premise un-founds that belief in `credited_beliefs` automatically (the chain-in-force
  test), which composes the two calculi without either knowing the other's internals.
- **ASP layer:** new EDB families (belief/…, `belief_edge/3` for premises/source/contests),
  capability-gated per the existing `require()` discipline ([FINDINGS.md](../FINDINGS.md)'s
  F49: a fact family must declare PRODUCED \| CAPABLE \| DEFERRED rather than return a bare
  empty result, because a silent empty is indistinguishable from a verified "none exist" and
  the F49 incident was exactly that confusion reaching a mandatory close check); one new
  `LAYERS` entry; `AGREE`/`DIVERGE_*`/`QUARANTINED` vocabulary unchanged.
  The stratification laws of `ledger_defeat.lp` (in-force tests only via `not
  superseded/1`; machinery inputs outside the target domain; derived surfaces compose
  beside `in_force`, never into it) bind the new rules verbatim.

---

## 5. This consult's closure statement (ADR-0000 Rule 2(a), self-applied)

**Invariant:** every assertion-act on the ledger carries a typed quantifier polarity with
its polarity's evidence obligation, a typed basis with its basis's edge obligation, and is
creditable only via derived, never-stored views.

**Quantification universe, enumerated:**
- *Axes:* holder (any registered principal, human or model — the maintainer's
  assertion-acts included); polarity (universal | existential — total for assertion-acts;
  mixed beliefs decompose; normative content excluded by construction); basis (observed |
  derived | testimony | assumed — the residual axis is instrument-mediated observation,
  which v1 folds into `observed`-with-artifact-witness and names here as folded, not
  covered separately); lifecycle (assert → supersede | contest | credit | un-found);
  time (all views current-truth; no as-of variant in v1 — named not covered; the existing
  `asof-export` surface is the natural later home).
- *Sibling surfaces the same shape occurs on:* reviews (§7 Q5 — bridged later, not in v1),
  s44 attestations (already typed; untouched), work-item closes' completion claims
  ([ADR-0013](../law/adr/0013-execution-integrity.md)'s own, pre-existing term for a different mechanism — a natural later consumer of
  `belief_universe`, named not covered in v1), operator reports (remain prose; beliefs are
  the typed extract, entered by verb, never parsed from prose — §6).
- *Denomination:* the substrate's "bounds" are closed vocabularies and existence-checked
  tokens, not numbers; the one scalar (`confidence`) is pre-existing, three-valued, and
  unread by rules. Nothing here is denominated in a proxy unit because nothing here is
  denominated at all — stated so the check is seen to be discharged, not skipped.

**Presumed too narrow, checked outward:** the polarity dichotomy was checked against the
seven specimens (each classifies), against decisions (excluded as preference-acts), and
against reviews/attestations (classify as universal-over-method and
existential-about-a-row respectively). The named residue: probabilistic and temporal
("X until Y") propositions do not classify cleanly and are excluded (§6).

---

## 6. Deliberately excluded, and why

- **Numeric degrees of belief / Bayesian machinery.** Floats fight the closed-vocabulary
  discipline, the ASP layer, and honesty (a 0.87 is a claim with no witness). The
  three-valued `confidence` plus derived corroboration grades carry what the evidence
  showed is actually needed.
- **Modeling the maintainer (or anyone) — projection.** The 2026-07-14 consult's Claim B
  rejection stands (Claim A: what the maintainer has ruled, currently valid under defeat,
  should be a formal queryable theory — banked, already the project; Claim B: the
  orchestrator may derive rulings the maintainer never made and act on them in his absence —
  rejected): authority does not interpolate. This substrate stores what principals
  *asserted*, never what they *would* assert.
- **Nested doxastic logic** (beliefs about beliefs beyond the one testimony edge; KD45 and
  kin). No specimen demanded it; ADR-0008 forbids fabricating the category ahead of need.
- **Reinstatement on contest resolution.** s31's named future fork; resolution here is
  always supersession or evidence-class precedence, never revival.
- **Prose harvesting.** No parser extracts beliefs from reports; beliefs enter verb-coupled
  or not at all (the staleness-is-conserved criterion — a harvested belief is a
  hand-maintained sentence wearing a schema).
- **Retroactive backfill** of historical rows into beliefs. Runs are linear; old worlds and
  old rows are dust and settled evidence.
- **Mandatory belief-recording for orchestrator operations** beyond whatever single site
  Q7 ratifies. A substrate everyone must feed on every judgment is certification
  bureaucracy; a substrate available at the moments the failure modes actually recur is a
  mechanism.

---

## 7. The maintainer's decision points (separable; each standing alone)

**Q1 — Naming: RESOLVED (maintainer-delegated, 2026-07-22, ledger rows 1893–1894).** The
consult originally proposed `claim`; renamed by maintainer-delegated resolution, rows
1893–1894, to `belief`. The maintainer delegated the naming choice rather than deciding it
directly, citing a real incident in this project where an implementer misread a field named
`domain` as a web domain name — a live specimen of the false-cognate risk this decision was
weighed against. The orchestrator chose `belief` on four grounds: it is accurate — the §3.0
stance ("belief is a stored, typed speech act; knowledge is a derived, never-stored judgment
over beliefs") becomes self-labeling instead of fighting the name of its own kind; it is the
commission's own word (row 1888, verbatim: "so that we can track beliefs and knowledge"); its
everyday reading IS the technical reading, where `claim`'s everyday reading (a bare assertion)
sits close to but not identical with the act-of-asserting-under-a-basis this kind actually
records; and `claim` carries two live collisions this project's own implementers are primed
to trip on — the kernel's own s22 `work_claimed` possession sense (a principal claiming a
work item, not asserting a proposition), and the JWT/OIDC identity-claims sense, exactly the
kind of false cognate an access-control-adjacent implementer reaches for first. Checked
residual: `belief`'s own natural misreading is the Bayesian degrees-of-belief connotation, but
that is foreclosed by this consult's own explicit no-numeric-degrees exclusion (§6) — the
misreading has nowhere to land in the actual schema. The consult's own lean is recorded for
the history: it favored `claim` + `credited`, "knowledge" in prose only. Only the naming half
is superseded by this resolution; the "knowledge"-stays-prose half stands unchanged —
`credited` (now `credited belief`, §3.4) is still the word that survives ADR-0008, and
"knowledge" still belongs in prose, not in a view name. *(resolved: belief + credited,
knowledge in prose only)*

**Q2 — The core type.** Adopt the universal/existential polarity with mandatory
universe/witness respectively as the substrate's spine (§3.1–3.2)? This is the load-bearing
decision; everything else is adjustable around it. *(yes | no, propose differently)*

**Q3 — Contest semantics.** Paraconsistent mutual demotion (both contested beliefs blocked
from credit until superseded or resolved by evidence-class precedence — consult's lean), vs
extending the empowered-defeater/trust-grant calculus to beliefs (a granted challenger's
contrary belief defeats outright). *(paraconsistent | empowered-defeat | hybrid-later)*

**Q4 — Staging.** v1 statement-prefix convention witnessed on scratch chains first, typed
delta in the next world's birth chain after (consult's lean), vs typed delta directly.
*(two-step | direct)*

**Q5 — The review bridge.** Derive testimony-beliefs from review verdicts in the EDB so
CLEANs enter the corroboration/shared-premise calculus (makes specimens 1.2/1.6 fully
representable) — in the first increment, or as a named second increment once the belief
layer is witnessed? Consult's lean: second increment. *(first | second)*

**Q6 — The dispatch-grain independence fix** (backflow finding 6): commission the small
separate delta (a `disclosed-isolated-dispatch` independence value, or dispatch-id-keyed
stamp distinctness) alongside this substrate? Independent of Q1–Q5. *(yes | later | no)*

**Q7 — Operating assumptions.** Mandate belief rows for exactly one orchestrator site — the
scheduler's resource/conflict model (the row-1852 class), so its next too-narrow universe
is a defeasible record — or keep assumption-beliefs fully opt-in? *(one mandated site |
opt-in only)*

---

*Point-in-time consult record, 2026-07-22. Not committed by its author (consult bound);
superseded by any maintainer word and by the Fable spec that would follow ratification.*
