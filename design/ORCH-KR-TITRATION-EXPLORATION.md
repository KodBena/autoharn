# Knowledge-representation titration — a design-space exploration

Audience: maintainer (primary), orchestrator (secondary)

**Status: design-space exploration, living document. This note carries NO mandatory
ratification** — it was commissioned (tracker work item `kr-titration-design-exploration`,
`./led show 266`, 2026-07-13) as an investigation the maintainer reads at leisure, not as a
spec awaiting a yes/no. Nothing below binds anyone; where a staged adoption path is sketched,
each stage is a separate future decision.

**What this document is.** The maintainer proposed an idea in two parts: (1) introduce ledger
"information packets" — discrete, typed information — and slowly titrate out prose in favor of
discrete data, such that a cheap (Haiku-tier) scanner can read the ledger in a formal
substrate, naming OWL/RDF as candidates but not prescriptions; and (2) a conjecture to be
evaluated: *extraction of discrete information from prose is nearly free exactly when
collisions occur, because a collision puts crosshairs on the specific datum that was
misinterpreted*. This document maps the design space for part (1), evaluates the conjecture in
part (2) against a worked case (the "mandated-tier" collision, three-of-three fresh readers
misreading the same datum), and ends with a recommendation and the evidence that would change
it. Per the commission, every negative verdict on a candidate is argued against this project's
actual substrate, not assumed.

**Terms used throughout** (project senses; the root [GLOSSARY.md](../GLOSSARY.md) holds the
standing vocabulary): the **ledger** is the append-only Postgres decision tracker written and
read through the `./led` verb; a **collision** is two committed artifacts telling one fact
differently; an **information packet** is the maintainer's coinage for one discrete, typed,
machine-parseable fact deposited in the ledger; **EDB** (extensional database) is the typed
fact export the deductive engine reasons over; **ASP** (answer-set programming) is the clingo
paradigm the engine's derivation programs are written in; **OWL/RDF** are the W3C
description-logic ontology language and its triple serialization; a **Haiku-tier scanner** is
a small, cheap model asked to read the record without a large context budget.

---

## 1. The worked case: what actually collided, and how it was found

The commission's worked case is the mandated-tier crack. The resource-declaration grammar
(§2.2 below) gives every declared resource a TIER field whose closed vocabulary includes
`mandated: <task-shape>`. Two same-day specs then told the *enforcement story* of that tier
differently: one spec's enforcement section says enforcement is an unbuilt later stage
(write-time enforcement out of scope by design); the other says a Stage-1 convention SHIPPED
(a mandated-shape task's work item carries a review obligation by convention, with policing
status derived per deployment). The full statement of the divergence, with both specs' section
numbers, is the tracker record: `./led show 223` (the `mandated-tier-story-reconciliation`
work item, opened 2026-07-12). This document deliberately cites the tracker rows rather than
the two specs' current text, because the reconciliation is being executed concurrently with
this investigation and the specs' text is in motion.

Three independent fresh-context probe runs then misread the same datum, each differently:

- Run 1 (Opus-graded control, `./led show 222`): the candidate conflated an adjacent shipped
  mechanism with the tier machinery and overclaimed enforcement — and the grading key itself
  was defective on the same terrain ("candidate and key failed on the same terrain, localizing
  a real corpus ambiguity").
- Run 2 (`./led show` row 258): "SECOND INDEPENDENT REPRODUCTION ... round-2 answer is
  defensible under [one spec]'s story and wrong under [the other]'s, which is exactly the
  reconciliation debt."
- Run 3 (`./led show 259`): "THIRD consecutive reproduction ... the probe's initial
  declared-only answer was nearer truth, then its own verification round 'corrected' INTO the
  overclaim."

Three observations that shape everything downstream:

**1a. The datum that collided was already half-packetized.** The tier *declaration* is a typed
field in a refusal-grade grammar (`bootstrap/templates/led.tmpl:930-931` prints the closed
TIER vocabulary in its refusal text). What collided was not the declaration but a **claim
about the system's own semantics** — "what does the system do with a `mandated` declaration?"
— which lived only in prose, in two places, differently. So the packet vocabulary the
collision class demands is not more domain declarations; it is a form for **facts about
mechanism status** (built / convention-shipped / derived-per-deployment / unbuilt).

**1b. The resolved datum existed in typed-ready form at resolution time.** Row 223's own "Fix,
minimal" clause states the resolved truth in one sentence with three clauses (grammar
validation live everywhere; mandated = review-obligation convention where the Stage-1
mechanism has run, derived per deployment; forbidden hard refusal = unbuilt). That sentence is
a packet in all but format. This is the strongest single piece of evidence for the conjecture
(§4).

**1c. A packet nobody's reading path crosses prevents nothing.** Rows 222/223 — the documented
ambiguity — sat inside probe 3's frozen ledger and went unconsulted; the probe resolved the
divergence confidently instead of surfacing it (row 259, both misses sharing that shape). A
typed row is only a fix if the surfaces readers actually check (the specs, the capabilities
document, the glossary, the `./pickup` rendering) point at it — otherwise it is a third
teller. This is the commission's "new SSOT hazard" made concrete before any design is chosen,
and §6 treats it as first-class.

The maintainer's own root-cause diagnosis is on the record (`./led show 264`): the
probe-exposed inconsistency is downstream of an
[ADR-0005](../law/adr/0005-documentation-discipline.md) Rule 1 violation — one fact, no single
owning home. Everything below is therefore evaluated as a mechanization of ADR-0005 Rule 1,
not as a new discipline beside it.

## 2. The existing substrate, read before judging

The commission requires the substrate read in full before any candidate is judged. Three
pillars exist today, plus a body of in-house prior art.

### 2.1 The deductive engine (ASP over an EDB exported from the ledger)

The engine is the project's stated raison d'être, and it already implements "a formal
substrate over the ledger" for a specific class of judgment:

- `engine/ledger_edb.py` is "the single home for 'what the ledger looks like to a logic
  engine'" (its module docstring, `engine/ledger_edb.py:8`), exporting typed fact families
  (`entry/6`, `supersedes/2`, `enacts/2`, `answers/2`, `amends/2`, and kernel-shape families)
  with **capability declarations**: a family the target cannot produce is a declared
  exclusion, never silence (`engine/ledger_edb.py:13-21`).
- ASP programs under `engine/lp/` derive judgments over that EDB — supersession/in-force
  closure (`engine/lp/ledger_tnow.lp`), decompose-then-overrule clause defeat
  (`engine/lp/ledger_dto.lp`), work-item event-graph violations (`engine/lp/work_items.lp`) —
  each paired with an independent SQL floor and differential-gated bit-identically
  (`engine/docs/JUDGE-READING.md` §1-2).
- The governing design rule: **"IDS ARE THE INTERCHANGE; TEXT STAYS HOME"**
  (`engine/ledger_edb.py:31-34`; [ORCH-LEDGER-LOGIC-MARRIAGE.md](ORCH-LEDGER-LOGIC-MARRIAGE.md)
  §3 rule 1) — no statement or rationale prose crosses into the EDB. The engine reasons over
  the record's *structure* (which row supersedes which, what answers what), never its
  *content*. Today, a fact carried inside a statement's prose is invisible to the engine.

The implication for this design: the engine is not a competitor to information packets — it is
a **ready consumer** of them. A typed statement grammar makes the statement's fields data, and
data may cross into the EDB as atoms the way `work_slug` already does (`engine/lp/work_items.lp`
header: "only the SLUG ... and a WITNESS-PRESENT boolean flag cross"). The text-stays-home rule
is not violated by packets; packets are precisely what turns text into something that no
longer needs to stay home.

### 2.2 The typed-intake grammars — the titration mechanism that already exists

Four statement kinds already carry refusal-grade grammars at the `./led` write boundary, each
with a closed field list, closed vocabularies where applicable, whitespace-normalized
validation with byte-exact persistence, refuse-before-write atomicity, teach-text naming the
grammar's one documented home, and a lockstep "coherence partner" read filter in the
`./pickup` renderer:

| kind | fields | write-side witness | read-side witness |
| --- | --- | --- | --- |
| `resource:` | NAME, CLASS, REACH, WHAT-IT-PROVES, GUIDANCE, TIER | `bootstrap/templates/led.tmpl:864-956` | `bootstrap/templates/pickup.tmpl:227,245` |
| `estimate:` | TASK-SLUG, TOOL-CALLS, SUBAGENT-SPAWNS, WALL-CLOCK, TOKEN-OOM (order-of-magnitude token estimate — not out-of-memory), BASIS | `led.tmpl:958-1059` | `pickup.tmpl:327,330` |
| `taxon:` | TAXONOMY, TAXON, PATTERNS, GLOSS | `led.tmpl:1061-1146` | `pickup.tmpl:395` |
| `interface:` | TAXONOMY, ARTIFACT-PATTERN, GLOSS | `led.tmpl:1147` onward | `pickup.tmpl:395` (same renderer) |

(The table's rows are the four grammars; each row names the statement prefix, its ordered
fields, and the file:line where the write-side validator and read-side renderer live.)

Three properties matter here. First, **each grammar is a transcription of exactly one
documented home**, never a second driftable definition (`led.tmpl:899-903`: "transcribed
VERBATIM from design/USER-BLESSED-TABLE-TEMPLATE.md ... the ONE documented home of this
grammar (a transcription, not a second, driftable definition of it — ADR-0012 P1)"). Second,
**each was minted reactively from a witnessed incident** (`resource:` from the run12
newline-shred incident, `led.tmpl:870-875`, banked in `seen-red/resource-intake-validation/red.txt`;
`estimate:` from the cost-estimation-retro item, grammar home
[USER-RETROSPECTIVE-RECIPE.md](USER-RETROSPECTIVE-RECIPE.md) §6, banked in
`seen-red/estimate-intake-validation/`; `taxon:`/`interface:` from the taxonomy-stage-a item,
banked in `seen-red/taxonomy-intake-validation/`) — the vocabulary grew where reality burned,
which is the same trigger discipline the conjecture proposes. Third, **grammar additions are
constitutionally cheap**: a new statement kind only adds refusals and vocabulary, the
fail-safe additive class [CLAUDE.md](../CLAUDE.md)'s ORCHESTRATION section pre-ratifies —
and it touches no kernel column and no `engine/lp/` semantics.

This is the commission's "existing titration mechanism hiding in plain sight," confirmed on
read: the project already titrates prose into discrete data, one witnessed incident at a
time, through exactly this path.

### 2.3 In-house prior art, and why the pre-pivot NLP substrate died

**The NLP-logic interface** (five documents, now behind the vestigial index — on mainline at
`vestigial_documentation/research/nlp-logic-interface/`, indexed in `VESTIGIAL-INDEX.md`;
quoted here from the pre-sweep tree this exploration was authored in). Its `DESIGN.md`
(2026-07-02) designed NLP extraction of claims from prose transcripts feeding logic engines.
Two of its findings bear directly on this commission, and they cut in opposite directions:

- **General extraction from prose is expensive and low-yield, measured.** The 2026-07-02 trial
  series: enrichment cut the joint noise floor 483 → 54 findings, produced 0 novel findings,
  and **0 of the 54 survivors were adjudicable candidates**; the one known-live positive was
  at zero recall in every arm (`DESIGN.md` §1). The pipeline it designed was never built in
  this repo, and the thread was not carried forward (the vestigial index's classification
  rationale for all five files).
- **Authored typed rows were its own honest fallback.** Its F6 function states: "v1's
  mandate/means-change rows are *authored* (by the maintainer or an adjudication step), not
  NLP-extracted from transcripts — extraction of 'this is a mandate with WHY = X' from prose
  is beyond the measured envelope. The function is real with authored rows" (`DESIGN.md` §3
  F6, scope-honesty clause).

So the house has already measured the two ends of the extraction spectrum: *bulk* NLP
extraction from prose failed on this genre; *authored* discrete rows worked wherever tried.
The maintainer's conjecture proposes a third point between them — authored rows whose
authoring moment is chosen by collision — which keeps exactly the part that worked and
discards exactly the part that failed. §4 evaluates it on its own terms.

**The house's prior OWL/RDF assessments.** Two independent survey passes (2026-06-27, both
carrying the caveat "agent-reasoned, not yet experimentally settled," so this document
re-derives rather than cites them as settled):

- [research/logic-investigation/08-description-logic.md](../research/logic-investigation/08-description-logic.md)
  (line 38): DL is "monotonic and open-world: it cannot *retract* an entailment when a finding
  is superseded ... a single contradiction makes the *whole* ABox inconsistent and every
  reasoner query becomes vacuously true (explosion). ... honest verdict: **do not use OWL for
  the provenance ledger.**" Its fit findings: medium-high only for closed-vocabulary
  classification, low for provenance, plus an acute false-authority risk (line 59: a
  mis-authored axiom "confidently returns the wrong classification with a 'proof'").
- The obligations-formalisms survey's DL section (on mainline at
  `vestigial_documentation/research/obligations-formalisms-survey/formal-systems/10-description-logic.md`,
  line 72) states its own kill condition: if every catch traces to a disjointness/covering
  axiom "a one-line code check encodes just as well," DL is "**ash** for autoharn: pure
  encoding tax."

Both are pre-registered house judgments this exploration must either uphold with fresh
argument or overturn with fresh argument; §3(a) does the former.

## 3. The design space

Five candidates, each assessed on: what a Haiku-tier consumer can actually do with it; the
migration path from today's prose; the writing-side cost; and the packet↔prose drift cost
during transition. Per the commission, no candidate is dismissed without engagement against
this substrate.

### (a) OWL/RDF triples as a parallel substrate, with a Haiku scanner

**The case for it, made honestly.** OWL/RDF brings W3C standardization (an adopter or
regulator could consume the record with off-the-shelf tooling — PROV-O is literally a
provenance ontology), reasoner-computed classification (subsumption lattices derived from
definitions rather than hand-written mappings), and SPARQL as a mature query surface a small
model can emit competently. If the project's vocabulary ever grows rich definitional structure
— classes whose membership is *inferred* from properties, not asserted — a DL reasoner
derives what a CHECK constraint cannot.

**The case against it, on this substrate.** Four independent grounds, each sufficient alone:

1. **Semantics mismatch at the core.** The ledger's load-bearing judgments are non-monotone:
   supersession retracts (`engine/lp/ledger_tnow.lp` header — the whole program is a
   derived-validity closure over defeat), clause-defeat is defeasible with named defeaters
   (`engine/lp/ledger_dto.lp`), and absence-with-exceptions is the standing rule shape. Base
   DL is monotone and open-world: adding an axiom can only add entailments, and an unstated
   fact is *unknown*, not false — the opposite of what "the current belief is the one nothing
   supersedes" needs. Contradictions, which are the *normal, expected* state of a record whose
   entire purpose here is to catch collisions, explode a classical ABox (the DL assertion
   store — the set of individual facts; one contradiction makes every classical entailment
   trivially true) rather than being contained and queried. The house's prior verdict (§2.3) is upheld on fresh read of the
   actual .lp programs, not inherited.
2. **A second logic substrate is a two-writers violation at architecture scale.**
   [ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) P1: every fact has one
   home; derived quantities are computed, never re-encoded. A parallel triple store must be
   populated. If a writer authors triples beside prose, that is a second hand-author of the
   same truths (cancer B — ADR-0012's own taxonomy label for a second hand-authored copy of
   one truth — across the hardest boundary to audit). If the triples are *derived*
   from ledger rows, then the ledger rows are the SSOT, the RDF is a view — legitimate, but
   then the substrate question has already been answered by option (c), and the RDF layer is
   an export format looking for a consumer.
3. **No identified consumer needs the RDF form.** A Haiku-tier scanner reading SPARQL results
   has no capability a Haiku-tier scanner reading `./pickup`'s rendered sections or
   `./led show <id>` output lacks — both are already discrete, labeled, closed-vocabulary
   text. The reasoning services (subsumption over a rich TBox — the ontology's class/relation
   definitions, the DL counterpart of the ABox's individual facts) have no current customer: the
   project's closed vocabularies (CLASS, TIER, TOKEN-OOM, verdict sets) are flat enums whose
   integrity is already refused at the write boundary — exactly the survey's kill condition
   ("a one-line code check encodes just as well") firing on inspection.
4. **False-authority risk against the assurance posture.** An LLM-authored TBox that gets one
   axiom wrong yields confidently wrong entailments with a machine-checked proof attached
   (§2.3). This project's answer to encoding trust is the two-producer differential
   (SQL floor vs ASP, bit-identical or red — `engine/docs/JUDGE-READING.md` §1); a DL lane
   would need the same discipline built from scratch to reach the house bar, a real cost with
   no identified judgment to spend it on.

**Earned verdict: no as a substrate; conditionally yes as a future derived export.** The one
scenario that revives it: an external consumer that speaks RDF materializes (regulator
tooling, PROV-O interop for an adopter with reporting duties, cross-organization exchange).
In that scenario the correct shape is a one-way derived serialization of ledger rows —
`ledger_edb.py`'s posture with a different output syntax — never a store anything writes to
directly. This is a filed trigger, not a plan.

### (b) Extending the ASP/EDB idiom: new typed row kinds → EDB fact families → ASP queries

**The case for it.** This is the one-home-compliant formal substrate: ledger rows stay the
single source of truth; `ledger_edb.py`'s capability-declaration export is the established
derivation path; the SQL-floor-plus-ASP differential is the established trust mechanism; and
the additive pattern is precedented (`engine/lp/work_items.lp` is exactly this: a new row
family, a standalone additive program, zero kernel semantic change, differential-gated). The
engine's non-monotone semantics natively fit the record (supersession of a re-minted fact is
one `supersedes` edge, already exported). And it honors the standing directive that the
deductive engine is wired into use, never routed around.

**The honest costs.** (i) Per new judgment, the house discipline demands an ASP program *and*
an independent SQL floor *and* a differential and scratch witnesses — right for load-bearing
derivations, heavy for a lookup. (ii) `engine/lp/` semantics changes require a Fable-authored,
maintainer-ratified spec (CLAUDE.md ORCHESTRATION) — additive standalone programs have a
witnessed lighter path, but it is still ceremony. (iii) Asking a Haiku-tier scanner to *write*
ASP is the encoding-trust hazard the house already named (LLM-authored encodings are on
trial); the sound shape is a library of pre-authored, differential-gated queries that a cheap
consumer *invokes with parameters*, the `./judge` pattern.

**Where it genuinely earns keep.** Only where a packet question needs *inference*: joins,
closure, or absence-detection. Two live examples the fact vocabulary of (c) would enable:
"which facts' declared owning documents have since changed content" (a drift detector — a
join between fact rows and document hashes), and "which resolved collisions deposited no
fact row" (the conjecture's own process discipline, checked by absence). Neither exists yet;
building the EDB family before a judgment needs it would be machinery without a customer.

**Earned verdict: yes, as the inference tier — deferred until a query needs inference.** The
packets themselves should not *live* here (they live in the ledger, option c); this option is
how they become reasonable-over when that day comes, and the design of (c) should keep its
fields atom-clean (slug-like handles, closed vocabularies) so the later EDB crossing is
mechanical. That forward-compatibility constraint is nearly free and is adopted into (c).

### (c) Extending the typed-intake-grammar path: more statement kinds with refusal-grade grammars

**The case for it.** The mechanism exists, is witnessed live, and already is the titration the
maintainer described (§2.2). Costs are known and small: one grammar block in `led.tmpl`
(cloned structure — the four existing blocks are structural clones of each other, by their own
comments), one `pickup.tmpl` renderer with the lockstep coherence-partner contract, one
grammar-owning SSOT document section, fixtures. Additions are in the pre-ratified fail-safe
class. The write boundary refuses malformed packets loudly with teach-text — the
refusals-that-teach house register.

**What the collision class specifically needs that no current grammar carries.** The four
existing grammars declare *domain entities*. The mandated-tier collision (§1a) was a fact
*about the system's own state* told in two prose homes. The gap is a claim-packet kind —
sketched here as a shape for discussion, not a spec:

```
fact: <HANDLE> | <VALUE> | <STATUS-VOCAB> | <OWNING-HOME> | <BORN-OF>
```

where HANDLE is a slug (the ADR-0005 Rule 1 "nominal handle" — e.g.
`mandated-tier-enforcement`), VALUE is the discrete datum, STATUS-VOCAB is drawn from a closed
mechanism-status vocabulary (the §1a lesson: `live | convention | derived-per-deployment |
unbuilt` or similar — the vocabulary is itself the design work), OWNING-HOME names the one
document section that remains the prose authority, and BORN-OF cites the collision row(s) that
minted it. Re-minting supersedes the prior row through the ledger's existing `supersedes`
machinery — history for free, current-value rendering in `./pickup` for free (the
unsuperseded-row idiom the renderer already applies). Worked against the mandated-tier case:
row 223's "Fix, minimal" sentence decomposes into two or three such rows with no residue,
which is the strongest fit evidence available without building anything.

**What a Haiku-tier consumer can do with it.** Read the `./pickup` section (labeled,
delimited, closed-vocabulary — the format was designed for exactly this consumer);
`./led show <id>` a single fact; grep the ledger for a handle. No query language, no
parser beyond splitting on `|`. This is the "formal substrate a cheap scanner can read" with
the formality located in the *grammar and closed vocabularies*, not in a serialization syntax
— which is where the mandated-tier failure says the formality was missing.

**The honest costs.** (i) Each new statement kind is real surface: grammar, renderer, doc,
fixtures, and a vocabulary to govern. Minted eagerly, this is the acronym-gate failure mode
([ADR-0017](../law/adr/0017-the-zero-context-reader.md)'s cautionary tale: a mechanism whose
output nobody reads trains everyone to ignore it). The mint trigger must stay reactive —
which is what (d) supplies. (ii) The packet↔prose drift hazard is *not* solved by the grammar;
it is solved only by the repointing discipline (§6). (iii) `led.tmpl` is a template: worlds
scaffolded before a grammar addition don't have it (runs-are-linear means they never will;
the next world does). That is the normal delta path here, not a defect, but it bounds how
fast the vocabulary propagates to existing deployments.

**Earned verdict: yes — this is the substrate.** It is the existing mechanism, the one-home
mechanism, the cheapest mechanism, and the one whose consumer (pickup / a cheap scanner /
later the EDB) already exists.

### (d) Collision-driven minting as a process, regardless of substrate

This is the conjecture as a standing rule: **every resolved collision deposits its resolved
datum as a typed row, at resolution time, and repoints the colliding tellers at it.**
Evaluated in §4; its verdict is: adopt, review-policed first, with the mechanization trigger
named. Two design notes that belong here rather than there:

- The process is substrate-independent in principle but pairs naturally with (c): a resolved
  collision's datum lands as a `fact:` row; the reconciliation edit that closes the collision
  work item is the same edit that repoints the prose.
- Its enforcement has a clean later mechanization: a resolved-collision work item's
  `work_closed` witness names the deposited fact row — checkable by the same
  absence-detection shape `engine/lp/work_items.lp` already computes for missing witnesses.
  Review-only until a recurrence earns the gate
  ([ADR-0011's](../law/adr/0011-mechanization-discipline.md) mint-on-recurrence discipline).

### (e) The remaining corners of the space, closed explicitly

Enumerated so the space is closed rather than trailed off
([ADR-0013](../law/adr/0013-execution-integrity.md)'s completeness
posture):

- **(e1) GLOSSARY.md as the packet store** (facts as glossary entries rather than ledger
  rows). Rejected on the merits: a prose file has no write-boundary grammar, no refusal, no
  supersession machinery, and concurrent-builder merge races (the very reason a wave plan
  serializes writes to [ORCH-CAPABILITIES.md](../ORCH-CAPABILITIES.md), the operator
  capabilities document — `./led show 264`). The glossary keeps its real role: a
  *pointer surface* where a human reader first looks, carrying the handle, never a second copy
  of the value.
- **(e2) A dedicated kernel table for facts** (columns instead of a statement grammar).
  Rejected for now: it buys type enforcement the grammar already provides at the boundary,
  at the price of a kernel delta (birth-chain ceremony, next-world-only) versus a template
  edit. If fact rows ever need relational integrity the grammar cannot express (foreign keys
  into resources, say), this converts from rejected to the natural Stage-2+ shape — filed,
  not buried.
- **(e3) Reviving the bulk NLP-extraction pipeline** to mine facts from the prose corpus
  wholesale. Rejected on the house's own measurements (§2.3: 483 → 54 → 0 adjudicable;
  extraction of mandate-shaped facts from prose "beyond the measured envelope"). The
  conjecture exists precisely because it replaces this pipeline's expensive search step with
  the collision as a free detector.
- **(e4) JSON-LD / SKOS / lighter RDF profiles** as a middle ground between (a) and (c).
  Same analysis as (a)'s derived-export clause: any of these is an output *serialization* of
  ledger rows, adoptable in an afternoon the day a consumer exists; none is a substrate.

## 4. The conjecture, evaluated against the worked case

**The conjecture:** extraction of discrete information from prose is nearly free exactly when
collisions occur, because a collision puts crosshairs on the specific datum that was
misinterpreted — the moment you resolve a collision you have already isolated the fact;
minting it as a typed packet at that moment costs almost nothing extra.

**Support, from the worked case.** At the moment row 223 was authored, its author had already
(i) isolated the datum ("is mandated enforced?"), (ii) enumerated every teller (two specs'
named sections, a capabilities item, a glossary entry — all listed in the row), and (iii)
drafted the resolved value in discrete clauses (§1b). Steps (i)–(iii) are the entire cost of
extraction, and the collision paid for all three. The marginal cost of *also* emitting a
grammar-shaped row is formatting plus one `./led` invocation. On this case the "nearly free"
claim holds cleanly. It also holds structurally: the four existing grammars were each minted
from a witnessed incident (§2.2), so collision-driven minting is not a new idea being tested —
it is the observed mechanism by which this project's typed vocabulary has actually grown,
now stated as a rule. And it is the law's own shape: a collision is a defect;
[ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) Rule 2 demands the
type that forecloses the class before the patch — the minted packet *is* the (a)-answer, and
the standing process *is* the (b)-mechanism.

**Two qualifications, so the conjecture is adopted with its real shape and not an inflated
one:**

1. **Nearly-free extraction is not nearly-free prevention.** The worked case's third probe run
   had the resolved knowledge *in its ledger* and never consulted it (§1c). The packet
   prevents the next misreading only when minting is coupled with **repointing** — the prose
   homes readers actually check must carry the handle, and the packet must render on the
   surfaces readers actually hydrate from (pickup). Repointing is the same work the prose
   reconciliation already does; the packet's *marginal* value over reconciled prose is
   (i) drift-resistance — a later spec edit cannot silently re-fork a fact whose value the
   spec no longer states, only points at — and (ii) machine-readability for the cheap scanner
   and, later, the engine. Those are real, but they are the honest size of the win.
2. **Collision-driven coverage is reactive by construction.** The vocabulary grows only where
   a collision already burned a reader; facts that have not yet collided stay prose. For this
   project that is a feature — it is the measured-first posture (ADR-0011 Rule 3) and the
   maintainer's own "slowly titrate" framing — but it should be said plainly: this process
   never yields a complete formal model of the corpus, and is not trying to. A completeness
   pass, if ever wanted, is a different (and per §2.3, historically unpromising) commission.

**Verdict: the conjecture is substantially correct, with the amendment that the free part is
the extraction, and the load-bearing part is the repointing.** The process rule should
therefore be stated as: *every resolved collision deposits its resolved datum as a typed row
AND repoints every colliding teller at it in the same change* — the second clause is what
makes the first one matter.

## 5. What a Haiku-tier consumer can do — the comparison, in one place

The table below summarizes §3's per-candidate analysis of the commission's consumer question;
each cell is argued in the candidate's own section above.

| question, answered per candidate | (a) OWL/RDF store | (b) EDB/ASP tier | (c) typed grammars |
| --- | --- | --- | --- |
| how does a Haiku-tier consumer look up one fact? | SPARQL SELECT (needs endpoint + syntax) | invoke a pre-authored query | read pickup section / `./led show`; trivial |
| how does it enumerate current facts? | SPARQL over latest-triples (versioning is manual in RDF) | derived view | pickup renders unsuperseded rows; supersession native |
| how does it detect a contradiction? | ABox inconsistency — but explosion, and only within modeled axioms | absence/join judgments, differential-trusted | write-boundary refusal (malformed), collision detection stays with readers/probes |
| why trust an answer it returns? | reasoner-proof, but encoding untrusted (no differential exists) | two-producer differential, the house bar | grammar refusal witnessed live; byte-exact rows |
| what does the option cost to stand up? | new store + TBox + trust machinery | spec ceremony + program pairs | one cloned template block per kind |

The reading: for lookup — which is what the collision class needs — (c) dominates. For
inference, (b) is the house-conformant tier when a customer appears. (a) adds consumer
capability only for a consumer that speaks RDF, which does not currently exist here.

## 6. The packet↔prose drift hazard, treated first-class

The design itself can mint a new SSOT violation: during titration, a fact exists as a packet
*and* in the prose that predates it. Three rules keep the transition honest, all instances of
existing law rather than new discipline:

1. **A packet is born as the owning home, or it is not born.** The minting change repoints the
   prose tellers (they state the relation and the handle, per ADR-0005 Rule 3, not a second
   copy of the value) in the same change. A packet minted without repointing is a third
   teller and makes the collision class worse — this is the §1c/§4 lesson and the hard rule.
2. **One documented grammar home per kind, transcribed not re-defined** — the discipline the
   four existing grammars already enforce on themselves (`led.tmpl:899-903`), inherited
   unchanged.
3. **The residual is declared, not hidden.** Prose that must keep stating a value for
   legibility (an ADR quoting an enforcement status as of its date; a point-in-time record)
   is exempt exactly as ADR-0017's exceptions already carve: point-in-time records are never
   retro-edited, and a dated quotation of a fact is a quotation, not a second home. Between a
   packet and a live prose restatement, the packet wins and the prose is the defect — that
   ordering should be stated in the grammar's owning doc when one is written.

No mechanized packet-vs-prose drift detector is proposed: a sound textual predicate for "this
prose re-states that packet's value" does not obviously exist (the same reason ADR-0017
declined deterministic coinage detection), so the enforcement surface is review plus the
fresh-context probes that caught the original collision class — declared honestly per
ADR-0011 Rule 1, with the §3(b) drift-join query as the mechanization candidate if the
recurrence arrives.

## 7. Recommendation, staged

Stated as stages the maintainer can adopt independently, smallest first; none is committed by
this document.

- **Stage 0 — the process rule, zero build.** Adopt §4's amended rule for resolved collisions:
  deposit the resolved datum as a typed ledger row and repoint every teller in the same
  change. Until a `fact:` grammar exists, the deposit can ride a plain `decision` row with a
  disciplined prefix (the `merge:` convention precedent,
  [ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md) §"The merge convention
  row"). The in-flight mandated-tier reconciliation is the natural first exercise.
- **Stage 1 — the `fact:` grammar.** Mint the statement kind per §3(c)'s sketch: grammar-owning
  doc section, `led.tmpl` block cloned from `taxon:`, `pickup.tmpl` renderer with the
  coherence-partner contract, fixtures. Design the STATUS vocabulary against the worked case
  first (the §1a mechanism-status axis), fields atom-clean for the later EDB crossing.
  Fail-safe additive class; Sonnet-executable against a short spec.
- **Stage 2 — the inference tier, on demand.** When a question needs a join or
  absence-detection over fact rows (the drift join; "resolved collisions with no deposit"),
  extend `ledger_edb.py` with a facts family and author the ASP/SQL pair under the standing
  differential discipline. Not before.
- **Stage 3 — external serialization, on demand.** If an RDF-speaking consumer materializes,
  emit a derived PROV-O/JSON-LD export from ledger rows. A filed trigger only.

**Evidence that would change this recommendation.** (i) If minted facts keep getting missed by
fresh readers — collisions recurring on already-packetized data — the repointing/reading-surface
design is wrong, and the investigation reopens at §6, not at the substrate choice. (ii) If the
`fact:` vocabulary accumulates rows nothing reads — the read-decay reaper (a designed,
not-yet-built mechanism from the vestigial-doc-sweep commission that counts agent read events
per file, `./led show 241` item 3) would say so once running — the titration is ceremony and
Stage 1 stops growing. (iii) If a genuine
inferred-classification need appears — membership derived from properties across interacting
axioms, not assertable by enum — the OWL verdict is re-run against the survey's own kill
condition (§2.3) as a fresh trial, since that is the one capability the chosen path cannot
grow into.

## Related

- `./led show 266` — the commission this document answers; `./led show 222`, `223`, `258`,
  `259`, `264` — the worked case's evidence chain.
- [ADR-0005](../law/adr/0005-documentation-discipline.md) Rule 1 — the failure class this
  design mechanizes; [ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) P1 —
  the one-home law the substrate choice turns on.
- [ORCH-LEDGER-LOGIC-MARRIAGE.md](ORCH-LEDGER-LOGIC-MARRIAGE.md) and
  `engine/docs/JUDGE-READING.md` — the deductive-engine idiom option (b) extends.
- `bootstrap/templates/led.tmpl` / `bootstrap/templates/pickup.tmpl` — the four live grammars
  option (c) clones.
- `vestigial_documentation/research/nlp-logic-interface/` (mainline path; behind
  `VESTIGIAL-INDEX.md`) and
  [research/logic-investigation/08-description-logic.md](../research/logic-investigation/08-description-logic.md)
  — the in-house prior art §2.3 weighs.

## License

Public Domain (The Unlicense).
