<!-- doc-attest-exempt: retrospective cross-check record, maintainer review pending; attestation follows ratification decisions. -->

**Findings corpus:** the consolidated postmortem this cross-check reads against is
archived at [history/POSTMORTEM-SETUP-TUI-ARC-2026-07-23.md](history/POSTMORTEM-SETUP-TUI-ARC-2026-07-23.md)
(verbatim copy of the series directory's POSTMORTEM.md, secured in-repo at the
maintainer's instruction, 2026-07-23).


# Retrospective ADR cross-check — the setup-TUI arc against the law corpus

**What this document is.** A cross-check of the full ADR corpus (`law/adr/`, read in full)
against the tracked findings of the setup-TUI rebuild and weak-fixed-point arc
(`~/autoharn_series/` — the postmortem's thirty lessons and completeness ledger, the per-cycle
audit/fix records — and the arc's ledger spine, rows 1100–1145). Commissioned by the maintainer
(ledger rows 1143/1144), run by an out-of-frame Fable instance with no working context from the
sessions that produced the material, per the row-1144 instruction and ADR-0018's
no-front-loading discipline. It is a **sibling record in the law directory, not an ADR**: it
binds nothing, proposes ratifiable items for the maintainer's decision, and assigns no blame —
its subjects are mechanisms, texts, and enforcement surfaces, never authors.

**The taxonomy applied**, per the commission: each finding is classified
**COVERED-AND-BOUND** (an ADR's letter or clear spirit already prohibited it; the failure was
non-application), **COVERED-BUT-UNCLEAR** (the text arguably covered it but was too
instance-bound, vague, or readable-down — the maintainer's question c),
**UNCOVERED-BUT-DIRECTABLE** (no ADR covered it and a project-agnostic directive could have —
questions a/b), or **NOT-DIRECTABLE** (genuinely novel or environment-specific; a finding, not
a failure). A final section (d) names what the taxonomy itself does not ask.

**A temporal note the whole cross-check depends on.** ADR-0019 and its C1–C29 companion were
minted *during* this arc (2026-07-22), from its own pre-arc specimens. So the pre-arc
anti-patterns (S1–S7) are judged against the corpus as it stood *before* 0019 existed, and the
in-arc cycle findings against the corpus *with* 0019 in force. The arc is therefore both the
evidence of a gap and the record of that gap being filled — several a/b answers below were
already given, mid-arc, and are recorded here as such rather than re-proposed.

---

## 1. COVERED-AND-BOUND (13 findings)

The dominant category, and its dominant sub-pattern is uniform enough to state once up front:
**in almost every row the failure was not a missing or unclear text but an enforcement surface
declared and not installed** — a rule whose companion or ADR names "construction-time typed" or
"CI lint" as its honest surface, on a codebase where no such gate existed until the defect
forced one. The ADRs' own vocabulary (ADR-0011 Rule 1) predicts exactly this: review-only is
presumptively decaying. The arc is thirteen data points confirming the prediction.

| Finding (source) | Binding law, letter or clear spirit | Non-application diagnosis |
|---|---|---|
| One-fact-two-homes family: S5 flat-keyspace aliasing, S6 mirrored field, signed-genesis SKIPPED+REFUSED in one run, `#ct-field-path` id collision (rows 1111/1112/1115; cycle-5 fix) | ADR-0012 P1, letter ("every fact has exactly one home"); maintainer adjudicated the mirror under ADR-0002 (row 1112) | Enforcement-surface gap: P1 had no gate over UI bindings. The mid-arc answer — 0019 Rule 3's construction-time refusal over the declared binding table — is the correct ADR-0011 Rule 2 conversion, and it held for the rest of the arc. |
| Commit-success lie: hardcoded `ok=True` at two sites, exit 0 + green Finish over a checklist reading REFUSED (cycle 7, row 1140; second site cycle 8) | Companion **C5** — written *before* the instance existed, from zero codebase access; plus ADR-0012 P1 (interactive/headless paths as two homes of one fact) and ADR-0002 | The clearest specimen in the arc: the class was foreclosed in text and open in code. C5's declared surface ("construction-time typed async state machine") was never installed in this codebase; the companion's tier labels describe the *achievable* surface, not the *installed* one, and nothing tracked the difference (see §5, item d1). |
| Text-measure fix deleted the elucidation (round 5, censure, row 1115) | ADR-0013, 2026-06-24 amendment (malicious compliance), letter | Pure non-application of a rule whose own text admits it is enforced by the faculty it corrupts. The mechanism answer that emerged (row 1121's purpose-witness) is proposed for law in §3. |
| UI-thread freeze, 3 s witnessed, no feedback (cycle-1 HIGH, row 1131) | Companion C24/C26/C9 | Caught *by* the rules at audit time; not prevented at authoring time — the declared lint ("ban blocking calls in handlers") did not exist. Same audit-catches/authoring-misses asymmetry as C5 (see §5, item d2). |
| Phantom-expanse class, three instances each patched locally (row 1139) | ADR-0011 Rules 2 and 4, letter; ADR-0012's 2026-07-02 corrective-diff amendment ("a fix consults the ledger of defect classes already on record for the stack it touches") | Two compounding gaps. (a) Rule 2's trigger presumes the *recognition* that instance N is the class of instance N−1; instances indexed by symptom (blank space, overlap, starvation) never matched. (b) The corrective-diff clause is conditional — "*where* a defect ledger exists" — and no per-stack defect-class ledger existed for the TUI, so the consult it mandates had nothing to consult. The infrastructure precondition, not the text, failed (see §5, item d3). |
| Instance-anchored fixtures, "a museum of past incidents with no global invariant" (row 1139) | ADR-0011 Rule 4, letter ("enumerations of instances fail open at the next instance") | Non-application in the test register; a clarity note belongs in §2 (the Rule's worked instances bias the reader toward production-code nets). |
| Measure-fix closure statement enumerated only the width axis; structure axis walked back in (row 1117) | ADR-0000, 2026-07-02 closure-statement amendment, letter — convicted as an ADR-0000 under-application by the maintainer on the record | Named non-application; the amendment's inverted presumption ("the class as first named is presumed too narrow") was exactly the unexercised discipline. |
| Blind passes swept terminal *width*, never *height*; reachability was height-driven (cycle-3 instrument's self-criticism, cycle-4) | Same closure-statement discipline, clear spirit: a coverage claim is a foreclosure claim and owes its quantification universe | The amendment was read as applying to defect *fixes*; audit *coverage claims* carry the identical obligation and nobody read it across. Borderline with §2; filed here because the spirit is clear. |
| Drifted duplicate renderer: filter dead in the modal, elucidation absent in the modal (cycle-3, two MAJORs) | ADR-0012 P1 (a hand-copied second renderer is a second home) | The structural restructure relocated fields into a home whose renderer had been duplicated instead of shared; the P1 violation predated and enabled both MAJORs. Non-application at authoring time; fixed by the P1-correct collapse to one renderer. |
| Silent cascade delete, contradicting the code's own docstring (cycle-5 MAJOR) | Companion C10; the docstring contradiction is ADR-0002/P8's lying-contract class | Non-application; C10's declared construction-time surface (reversibility as a typed action property) was not installed. |
| Cancel enabled but sampled only between sections (cycle-4 minor) | Companion C9, letter, including its "wired to actually stop the work" half | Non-application; the fix (real cancellation token, SIGTERM→SIGKILL, typed `CANCELLED` status, honest non-cancellable teardown) is the rule executed properly. |
| "Operator declined" recorded for defaults the operator never touched (round 5, row 1115) | ADR-0002 spirit (a record asserting an act that did not happen is the silent-failure class in the provenance register); CLAUDE.md's claims-carry-witnesses | Non-application: the checklist wrote a claim with no witness. |
| Live-terminal no-op behind green Pilot witnesses (row 1136); convergence claimed at cycle 4 and falsified at the bench (rows 1137/1138) | ADR-0013 Rule 5's 2026-07-02 amendment, clause 1, letter: "the artifact chain terminates at the deployed effect… the operator's direct observation outranks any internal claim" | Named non-application — row 1102's lapse 2 says it in the arc's own words ("done was reported twice on headless evidence"). The mechanism adopted there (operator-run witness or explicit UNEXERCISED-live disclosure) is orchestration practice, not law; promotion is proposed in §3. |

## 2. COVERED-BUT-UNCLEAR (6 findings) — the specific sentences, and what clearer text would bind

**2.1 — ADR-0017's scope clause stops at documents; the disease crossed to rendered operator
surfaces unimpeded.** The failing sentence: *"Scope: Every **maintainer-facing document**
authored or edited from ratification onward — READMEs, design notes, rulings, briefs…"*
(ADR-0017, Scope). The elucidation defects D2 (insider referents — "the omega-lab shape",
"s40/s41" — on a founding operator's screen), D7 (implementation inventory where decision
guidance was owed), and D8 (audit-log register shipped as explanation) are the zero-context
failure *exactly* — Rule 1(b)'s dangling referent, Rule 1(d)'s wrong-altitude opening — on a
reader with strictly *less* context than the maintainer. Nobody applied 0017 because its scope
names an artifact kind, not a reader. Clearer text: scope the tenet **by reader, not by file
kind** — "every rendered prose surface whose reader lacks the author's context; the operator
of a shipped surface is the zero-context reader in its strongest form." (The mechanization
differs per surface; the *test* does not.)

**2.2 — ADR-0014 Rule 2's triggers are all executor-side; the arc's loudest recurrence signal
arrived from outside and no trigger named it.** The failing text: Rule 2's trigger list ("≥2
attempts that each turned out to address the wrong target… a diagnosis that keeps proving
partial… growing thrash") — every bullet observes the *executor's own attempts*. The arc's
form (row 1102, lapse 3): five specs built on the teletype architecture, each passing its own
harness, while the *operator's* repeated complaints against a surface already reported done
were classified as new defect reports. That is "a diagnosis that keeps proving partial"
observed from the ratifier's chair, and the rule as written let it not fire. Clearer text: add
the external trigger — *"a second operator/ratifier defect report against a surface already
reported done is an observable Rule-2 trigger, and it fires mechanically, not by feeling."*
(Row 1102 already adopted this as orchestration practice; §3 proposes the promotion.)

**2.3 — ADR-0011 Rule 4 reads as being about production-code nets; a regression-test suite is
a net and nobody read it that way.** The Rule's letter fully covers the fixture museum, but
its worked instances (`FeatureLayout`, `pack_net`, the partition assertion) are all product
structures, and the arc shows three recurrences slipping through a *fixture suite* that was
precisely an enumeration. One clarifying sentence would have bound: *"A test suite is a net
under this rule: a suite of instance-anchored fixtures with no always-on class invariant is
the enumeration this rule forbids, and it fails open at the next layout change where no case
looks."* The cycle-6 fix (typed layout primitives + a post-every-interaction invariant that
caught two latent sites on its first sweep) is the worked proof of the clarified reading.

**2.4 — ADR-0019 Rule 1's reference comparison has no stated aspect coverage, so a genre audit
can pass at one altitude and miss a major at another.** The cycle-4 audit declared MAJOR
ABSENT; the maintainer's 251-column screenshot then produced the content/chrome/width major
(row 1138) — a defect a reference-exemplar comparison at the *layout-economy* altitude (Qt
Creator's docked help, SAP's F1 panel) fails on sight. Rule 1's text says "name the genre and
two or three reference exemplars" but never says *which aspects* of the references the
comparison must traverse. Clearer text, in the closure-statement idiom the corpus already
owns: *"the genre comparison enumerates the aspects compared — structure/topology, layout
economy and viewport use, interaction and feedback, catalog scale — and an aspect deliberately
not compared is named as not compared."* (Rule 4's own history is the precedent: an audit
applied C25 only at its minting specimen's width until Rule 4 forced the class reading.)

**2.5 — The D1 claim-laundering class is sharper than ADR-0008's registers reach.** "Fielding
a sentence changed its truth value — an aspiration was laundered into a standing" is close to
ADR-0008's fuzzy-match register but not bound by it: the `Standards:` key *was* a plausible
vocabulary element; the violation was that a **mechanical decomposition of a compound claim
discarded the relation that carried its truth-conditions**. No ADR text names
meaning-preservation as an invariant of content migrations; the mechanical no-content-lost
check (the "conservation proxy", row 1120) satisfied every existing discipline while the claim
got stronger. Clearer text is proposed as new law in §3 rather than as an 0008 patch, because
the class spans schema design, briefs, and rendering, not classification alone.

**2.6 — Typed data fields have no charter obligation; P8 binds only call signatures.** D5
(`External:` meaning three unrelated things) was frozen *into* a broken contract by the very
act of schematization — each section internally consistent with its own unstated reading.
ADR-0012 P8's sentence "a function, method, or dataclass **signature** is the single source of
truth of its input/output contract" does not reach a declared data field whose *shape* is
certified while its *meaning* diverges per site. One sentence would bind: *"a typed field
minted from previously loose data carries a one-sentence charter — what the field asserts and
to whom — checked where the field is defined; certifying shape without charter freezes
looseness into contract."* Modest cost, and it composes with P10 (data artifacts are exactly
where such fields now live).

## 3. UNCOVERED-BUT-DIRECTABLE (7 findings) — candidate directives and honest recommendations

**3.1 — Genre novelty itself (S1 teletype, S2 wizard, S4a in-band sentinel; the four-build
day).** Before 2026-07-22 the corpus had no UI law at all, and nothing generic (0008's
vocabulary discipline, 0003's bands) reaches "the convergent design of a solved genre is the
default spec." The directive **was authored and ratified mid-arc as ADR-0019 + companion** —
this row is recorded as the worked a→b instance, not re-proposed. One residual observation,
offered not urged: Rule 1's principle is not intrinsically UI-bound (file formats, CLI flag
conventions, wire protocols are also solved genres with reference exemplars), and the same
LLM-novelty mechanism plausibly operates there. Cost of generalizing now: a broad rule with no
witnessed non-UI specimen would be speculative law, against the project's build-on-witnessed-
need posture. Honest recommendation: leave 0019 UI-scoped; note the generalization as the
expected shape of the *next* genre-novelty incident, so that incident converts by ADR-0011
Rule 2 instead of starting cold.

**3.2 — The commission is the controlled artifact; specs inherited specs.** Root cause of the
whole pre-arc failure (rows 1100/1102, lapse 1): "navigate" was narrowed in the first spec and
every later build inherited *the spec*, not the commission; the operator's repeated plain
words were re-read through the spec's lens. No ADR governs commission→spec fidelity (ADR-0013
Rule 1 binds executor-vs-mandate at delivery, not spec-lineage drift at authoring). Candidate
directive: *"A commission's verbatim text is the controlled artifact; every derivative spec
revision is re-checked against the commission itself, never against a predecessor spec, and an
operator-facing commission receives a read-back in operator terms before spec freeze."*
Recommendation: **install** — it is project-agnostic, its absence is the arc's single most
expensive lesson (the maintainer's ~$340 day plus his eyes as the only detector), row 1102
already runs it as practice, and its cost is one read-back per spec freeze.

**3.3 — Worked examples in briefs are pre-graded answers (worked-example supremacy).** The
consult's D1 causal verdict: a worked example carrying real corpus data, delivered with spec
authority, outranks any adjacent choose-the-honest-shape clause — the commissioning-register
sibling of the front-loading ADR-0018 already forbids for consults. Candidate directive (row
1121, rule one, verbatim in effect): *"briefs show shape with synthetic content only; a worked
example carrying real corpus data is the commissioner's pre-graded answer and forecloses the
judgment clause beside it."* Recommendation: **install**, most naturally as a dated ADR-0018
extension from consults to commissions. Cheap, generic, and the mechanism is a pure authoring
rule.

**3.4 — Meaning-preservation witness for content migrations (the conservation-proxy closure).**
The false-MET coin of the arc: every witness attested a mechanical invariant of the delta
(no content lost, measure held, links resolve) while the defect lived in *what the artifact
asserts to a cold reader* — a proposition nobody commissioned a witness for (D1; row 1120).
Candidate directive (row 1121, rule two): *"any round that migrates, schematizes, or re-renders
authored content carries a purpose-witness — a cold-reading leg asserting the rendered artifact
claims no more than its source asserted and serves its declared reader — alongside the
mechanical invariants; no-content-lost never discharges no-meaning-changed."* Recommendation:
**install**. This is the strongest genuinely new law the arc supports: it closes 2.5's class,
the elucidation-deletion censure's inverse, and the audience-boundary leaks in one clause, and
its cost (one cold-read leg per content round) was already paid voluntarily for the rest of the
arc.

**3.5 — Operator-surface witness before "done" on operator-facing work.** Row 1102, lapse 2:
no rule required an operator-surface witness before reporting done on an operator-facing
surface. ADR-0013 Rule 5's amendment covers the *effect-re-observation* half for defect
clears; nothing binds the *delivery* of new operator-facing work. Candidate: *"an
operator-facing work item does not close as shipped without an operator-run witness or an
explicit UNEXERCISED-live disclosure to the maintainer."* Recommendation: **install as a dated
clarifying amendment to ADR-0013 Rule 5** rather than new law — it is the amendment's own
"deployment surface" logic stated for deliveries instead of clears.

**3.6 — A witness instrument declares its blindness surface.** Three distinct bench-vs-audit
divergences trace to instrument blindness that was structural, not incidental: Pilot stops at
the terminal I/O boundary (tmux mouse passthrough, redraw, resize, venv version skew);
headless audits cannot exercise `NO_COLOR`/contrast; the sweep matrix covered width and not
height. ADR-0015 Rule 4 makes a *degraded* verification say so; nothing makes an instrument
declare what it can never see even when healthy. Candidate: *"a verification instrument
declares its observation boundary — the layers and axes it structurally cannot witness — where
the instrument is defined; UNEXERCISED lists are derived from that declaration, not improvised
per audit."* Recommendation: **install as a dated ADR-0015 extension**; modest cost, and the
arc shows the declaration is what lets a green pass be priced correctly (the cycle-3
instrument's honest "stops at the application layer" verdict is the worked instance).

**3.7 — The tracked-arc procedure itself (the maintainer's point 3).** The commission notes
the shape of this exercise could become an optional standing autoharn offering. This
cross-check's observation for that banked design question: the procedure's binding constraint
is not the cross-check pass (cheap, repeatable) but the **infrastructure precondition** — the
arc was only checkable because progress was tracked contemporaneously (ledger spine, verbatim
audit/fix files, runnable trees). Items d1/d3 in §5 name the two registers such tracking would
need to be "always prepared." No recommendation beyond informing that decision; adoption is
his call.

## 4. NOT-DIRECTABLE (5 findings)

These are recorded as honest findings, per the commission's own framing: a law corpus claiming
to foreclose everything would be lying.

1. **The `_running`/MessagePump attribute collision** (cycle-1 fix). A host framework's private
   namespace landmine. A generic rule ("check the base class's namespace before naming an
   attribute") would burden every line of every project to prevent a per-framework accident;
   the right home is the per-substrate gotchas note the postmortem already recommends.
2. **Border-box arithmetic in a derivation comment** (cycle-7 minor). A substrate box-model
   fact wrong by one column in a comment, with the shipped constant field-validated correct.
   No generic directive catches a comment's arithmetic; the fix-the-explanation-not-the-number
   disposition is ADR-0013's fair-dealing spirit working, not a gap.
3. **State-combination blindness as such.** A green pass proves the combinations it drove;
   no text can foreclose the untested combination. The mitigations are procedural (fresh blind
   auditors driving *new* combinations; the operator's bench as terminal gate) and are already
   the loop's design, not directive material.
4. **The terminal I/O layer's invisibility to headless harnesses.** The *declaration* of the
   blindness is directable (3.6); the blindness itself is a fact of the tooling, not a rule
   failure.
5. **The s15 birth-chain defect.** A kernel-adjacent backend bug the TUI surfaced by being the
   first end-to-end operator-seat exercise of the path (own work item, row 1141). The canary
   lesson — an operator surface that really drives its backend is an integration test — is
   noted under d5 below; the defect itself is not a UI-law matter.

## 5. Section (d) — what the taxonomy itself does not ask

The commission's a/b/c all interrogate **directive text**. The arc's evidence points mostly
elsewhere. Five items, proposed on this pass's own judgment:

**d1 — Nothing tracks text→installed-gate coverage per surface.** The single strongest pattern
in §1: rules whose declared surfaces ("construction-time typed", "CI lint") were achievable
and absent, with no artifact recording the difference. ADR-0011 Rule 1 makes each *rule*
declare its surface once, corpus-wide; it does not make each *codebase surface* declare which
binding rules have installed mechanisms on it. The missing question: **"for this surface,
which of the rules that bind it are gated here, which are declared review-only, and which are
silently neither?"** A mechanism census per surface (INSTALLED / DECLARED-REVIEW-ONLY /
ABSENT), consulted at build-basis time, would have shown C5, C10, and C24 as ABSENT on the TUI
before their defects shipped. This is also the concrete form of point 3's "always prepared to
track the needed information."

**d2 — The corpus has no theory of when a rule is present at the keystroke.** The same rules
that failed to *prevent* (authoring) reliably *caught* (blind audit): C24 at cycle 1, C5 at
cycle 7, Rule 4 at cycle 2. "Non-application" is therefore two different failures the taxonomy
merges: a rule absent from the builder's working context at the moment of authoring, versus a
rule deliberately wielded by an auditor briefed on it. Required-reading synopses exist and the
defects shipped anyway. The question worth a standing answer: what delivery mechanism puts the
binding subset of the law *into the authoring moment* — a per-diff checklist derived from the
d1 census, the corrective-diff clause's checklist pass generalized to green-field UI work —
rather than into a corpus the builder has notionally read?

**d3 — Class recognition, not class coverage, was the recurrence bottleneck.** Phantom expanse
recurred three times under a corpus that foreclosed it, because no one *recognized* the
instances as one class until the maintainer named it from a screenshot. Every ADR-0011/0000
trigger keys on a recognized class. The missing standing procedure: a per-stack defect-class
ledger (the recidivism study had one; the TUI did not) that every fix must name its class into
and grep before shipping — turning ADR-0012's conditional "where a defect ledger exists" into
an unconditional, and making class-naming a capture act rather than a memory act. Without it,
the corrective-diff clause is law with a missing operand.

**d4 — The blind/sighted consult convergence is an unused validation instrument.** The
companion's four [convergent] rules — produced independently by a codebase-blind and a
codebase-aware instance — include C5, which then predicted a live MAJOR before the arc found
it. That is measured evidence that *independent reconstruction from the field's canon* ranks
rules by load-bearingness. The taxonomy never asks: which rules of the wider corpus would a
blind expert reconstruct? A periodic blind-reconstruction probe against any law family would
cheaply mark its bedrock (reconstructed = will be violated eventually, keep sharp) and its
possibly-ritual tail (never reconstructed, never enforced — the companion's own
never-enforced-entries-get-culled condition, generalized).

**d5 — The operator's bench is the system's most expensive verification stage and the law
treats it as informal.** The arc's terminal gate was, every time, the maintainer's own hands —
the reviewer the whole apparatus exists to spend late and little. Nothing in the law names the
bench as a *typed stage* with entry criteria (spend only on a candidate-converged artifact, on
declared-blind axes per 3.6) and a captured yield (every bench finding fed a class or a rule).
Naming it would let the project budget and protect it deliberately; the near-corollary, from
the s15 canary: a real (non-dry) operator-seat drive is the only witness of some layers, has a
real cost (live residue), and deserves the same declared-envelope treatment ADR-0015 gives
heavy runs.

## 6. Closing synthesis — the strongest law changes this evidence supports

Stated as ratifiable one-liners for the maintainer; each traces to sections above.

1. **Meaning-preservation witness (from 3.4, closing 2.5 and 2.6):** *Any migration,
   schematization, or re-rendering of authored content carries a cold-read purpose-witness —
   the rendered artifact claims no more than its source asserted and serves its declared
   reader — alongside the mechanical invariants; no-content-lost never discharges
   no-meaning-changed.*

2. **External recurrence trigger (from 2.2):** *ADR-0014 Rule 2 gains a trigger: a second
   operator or ratifier defect report against a surface already reported done fires a
   mandatory fresh-context adversarial review — mechanically, not by feeling.*

3. **The commission is the controlled artifact (from 3.2):** *A commission's verbatim text,
   never a derived spec, is the reference every later spec revision and acceptance check is
   read against; an operator-facing commission receives a read-back in operator terms before
   spec freeze.*

Worth a sentence beyond the three: the highest-leverage change the evidence supports is not a
text at all but d1's mechanism census — most of §1 would have been foreclosed by installing
surfaces already declared, and no wording improvement substitutes for that. It is listed here
rather than as a one-liner because it is infrastructure to commission, not law to ratify.

*End of cross-check. Not committed; the orchestrator installs after the maintainer reads.*
