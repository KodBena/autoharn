# MAINT: ADR Portability Refactoring — the ratification spec

- **Status: SPEC AWAITING RATIFICATION — Phase 1a. Nothing in this document executes
  until the maintainer says yes.** Per the amended ceremony (ledger row 361): Phase 1a is
  this draft plus its Contradictions Register → the maintainer adjudicates the register →
  Phase 1b (a second Fable pass revises this spec under his rulings) → ratification →
  Phase 2 (Sonnet execution).
- **Tracker item:** `adr-portability-refactor` (work_opened row 357; commission amendment
  row 361).
- **Author:** Fable spec author, 2026-07-13, isolated worktree. No file under `law/` is
  touched by this phase; the constitutional rule (CLAUDE.md ORCHESTRATION: nobody edits
  `law/` without a Fable-authored, maintainer-ratified spec) is why this document exists.
- **Revision note (2026-07-13, same author, same phase):** the first draft was written on
  a stale worktree base (`fca1100`, predating commit `24d1dfc`) and therefore read a
  pre-Revisit-#4 ADR-0000 and a corpus missing `law/STANDARDS-REGISTRY.md`. The base was
  brought current (merge of `next`); a diff between the two bases shows exactly two law/
  changes — ADR-0000's appended "Revisit #4" section (+39 lines) and the new
  `law/STANDARDS-REGISTRY.md` (46 lines) — both re-read in full. This revision updates the
  corpus baseline, the 0000 treatment row, §5 A3's 0000 inventory, register entry C10
  (new), §8's deployment-consumer list, §9's scope list, and hazard H2 (a dated correction,
  per ADR-0005 Rule 8's own style, not a silent rewrite). Every other section survived the
  re-read unchanged.

**What this document is.** The maintainer commissioned a refactoring of the 18-file ADR
corpus (`law/adr/0000` through `0017`) so it is portable across projects — first the
deployment named **ent** (a world this harness scaffolded to govern work on the picom
X11-compositor codebase), next an **omega** spaced-repetition deployment. This spec is the
ratification-ready plan for that refactoring: what each ADR needs (§2, the treatment
table), where extracted material goes and how the pointers work (§3), what may be
rewritten and what must be preserved verbatim (§4, the ADR-0005 Rule 8 boundary),
how "portable" and "complete" are checked (§5), the topology/renaming ruling the
commission amendment invites (§6), the contradictions found during the full-corpus read
(§7, for maintainer adjudication before Phase 1b), the Phase-2 execution plan (§8), and
what this spec deliberately does not do (§9). Every judgment cites the file and line it
rests on; the whole corpus (6,705 lines on the current base; the draft's 6,666 figure was
measured on the stale base the Revision note describes) was read in full for this spec,
plus `law/STANDARDS-REGISTRY.md` (46 lines, in `law/` though outside `adr/`).

---

## §1 The commission, verbatim

From the tracker (`./led`, work_opened row 357, transcribed):

> MAINTAINER COMMISSION 2026-07-13 (settling a question he has carried 'to and fro'
> without ledgering — now settled as intent): refactor the ADR corpus for PORTABILITY
> across projects (ent now, the omega spaced-repetition deployment next). His
> specification, verbatim in substance: generalize and condense the ADRs; (1) move
> project-specific examples out into an examples/history directory; (2) leave pointers
> thereto WITH brief context summaries, so the MOST IMPORTANT context is recovered
> directly from ADR prose, but only-where-appropriate when the relevant examples are
> large. Focus: succinctness AND completeness. Explicitly Fable-tier.

And the mid-flight amendment (decision row 361, transcribed):

> COMMISSION AMENDMENT adr-portability-refactor (maintainer, 2026-07-13, relayed to the
> running spec author verbatim-in-substance): (1) topic REORDERING, CLASSIFICATION, and
> RENAMING are explicitly authorized — implied by 'refactoring' but stated outright since
> the task is great and he does not want it gotten wrong on the first try; consequence:
> the orchestrator's no-renumbering guard is SUPERSEDED — regrouping/renumbering may be
> proposed, and where proposed the spec owes the corpus-wide citation-migration plan (ADR
> numbers are load-bearing citations; breakage is solved, not forbidden); (2) INTERNAL
> and INTRA-ADR CONTRADICTIONS are surfaced as a distinct register in the spec for
> MAINTAINER REVIEW, adjudicated by him BEFORE a second Fable pass incorporates the
> rulings — the ceremony becomes: Phase 1a spec draft + contradictions register →
> maintainer adjudication → Phase 1b Fable revision → ratification → Phase 2 Sonnet
> execution.

---

## §2 Per-ADR treatment table

**How to read the table.** One row per ADR, all 18. Column types, declared so every
label inhabits them:

- **ADR** — the number and a short title.
- **Lines** — current line count (`wc -l`, witnessed 2026-07-13).
- **Project-bound refs** — integer counts of project proper nouns in the file
  (`c` = chocofarm, `L` = LengYue, `a` = autoharn, `F` = FFXIII, `t` = throughput-lab,
  `f` = fact-mining; grep-counted, witnessed), then `p` = backticked source-artifact
  paths, `i` = named incident/audit citations (2026-06-15 architectural audit, leaf-eval
  audit, recidivism study, OOM incident, wf_ee73fb10). These are the measure of "how
  project-specific," per the commission.
- **Treatment** — a non-empty, dominance-ordered subset of the closed vocabulary
  {`generalize-in-place`, `condense`, `examples-extract`, `already-portable`,
  `retire-candidate`}. The first element is the primary treatment.
- **Moves → history / stays inline** — prose: what leaves the ADR for
  `law/adr/history/` and what the surviving prose must still carry.
- **Δ lines** — projected post-refactor line count of the ADR file (an estimate, not a
  gate; §5 A6 is the real completeness check).

Grounding for the Treatment judgments: the transferred-tenet family (0002, 0004–0009,
0011) each states its own rule/instance split in its Provenance field ("the tenet is
universal and transfers wholesale; the instance list is re-derived against chocofarm's
real surfaces" — e.g. 0002:9–18, 0004:7–13, 0005:7–16); the natives (0000, 0012–0017)
each carry rules stated generically over named, dated project substrates. ADR-0009 is
the corpus's own worked precedent for the entire refactoring move: it was re-instanced
for autoharn on 2026-07-12 with the chocofarm body declared "illustrative history now,
not this project's binding surface" (0009:52–55) — this spec generalizes that precedent
corpus-wide instead of paying it per-ADR per-deployment forever.

| ADR | Lines | Project-bound refs | Treatment | Moves → history / stays inline | Δ lines |
|---|---|---|---|---|---|
| 0000 type-driven design | 566 | c2 t5 f2 · p2 i0 | examples-extract, condense | Moves: Specimens 1–4 + contrast specimen (0000:80–156, ~77 lines, chocofarm/throughput-lab artifacts: `BoundedBatch`, `CellLedger`, the OOM queue). Stays: Rules 1–3 verbatim in force; the closure-statement amendment (0000:441–495, normative); Revisit #3 amendment + ratification proviso (0000:497–523, dated record, preserved verbatim); the 2026-07-12 "Revisit #4" section (0000:525–562, dated codified record, preserved verbatim — its Clause 1, standards-scope disclaimers, is already stated generically and portable as written; its Clause 2 binds the per-deployment registry, with `law/STANDARDS-REGISTRY.md` as this deployment's instance and an adopter substituting its own — the same core/bindings split ADR-0017 models); one summary sentence per specimen (the four types + the doubled-patch lesson) inline, since Rule 2(a) cites "the four specimens" as its worked form. | ~370 |
| 0001 immutability/COW | 189 | c4 L4 · p8 i2 | retire-candidate | The whole document is a chocofarm-specific *Decision* (its own Genre field, 0001:4–7): three named numpy/JAX seams that exist in no other deployment. No rule here transfers that 0012 P1/P2/P4 and 0002 do not already own generically. Proposed disposition: relocate verbatim to history as a lineage record; the corpus keeps a one-paragraph tombstone (see §6 on the number). **Routes to the maintainer as its own question (§9).** | ~25 tombstone |
| 0002 fail loudly | 270 | c3 L1 · p14 i0 | generalize-in-place, examples-extract | Moves: the chocofarm decision list (0002:34–72) and instance-bound Exceptions details (0002:198–223). Stays: the loudness hierarchy (0002:85–108) untouched; concrete rules 1–6 with rule 6's frozen-literal lesson kept as a two-sentence inline summary; the "loud enough" test; Exceptions as generic classes (bit-identical fallback, idempotence, bounded shim) with instances pointed. | ~180 |
| 0003 domain-coupling bands | 261 | c7 L3 F23 · p8 i1 | examples-extract, generalize-in-place | Moves: the entire chocofarm band map (0003:89–185, Bands 1–3 + the two porting inventories — F23 makes this the most instance-bound body in the corpus). Stays: the two-question principle verbatim (0003:58–70), the no-premature-extraction rule with the Sandi Metz argument (0003:75–87), and a template instruction: *a deployment derives its own band map on adoption*. | ~120 |
| 0004 minimal-touch | 151 | c4 L2 · p16 i0 | generalize-in-place | Moves: the four chocofarm contract examples (0004:22–47) and the named-file size list (0004:49–57). Stays: the two-case rule (0004:59–76) intact; one generic sentence per contract class (numerical-equivalence, positional-layout, duality, shared-constant) so the rule's motivation survives without the instances. | ~110 |
| 0005 documentation discipline | 255 | c8 L4 · p4 i2 | generalize-in-place | Moves: the audit-substrate Context items (0005:28–48) and per-rule chocofarm instances. Stays: all nine Rules, each verbatim in force; Rule 2's directory table re-parameterized — the *convention* (records have one predictable home) is the law; the *table of homes* becomes a per-deployment declaration (see contradiction C4). Rules 1, 3, 8 govern this refactoring's own mechanics and are not touched in substance. | ~190 |
| 0006 source-file headers | 156 | c11 L5 · p13 i0 | generalize-in-place | Moves: chocofarm exemplar file list (0006:22–27), the audit "Part A/B/C" anecdote. Stays: the three-part header rule and form (0006:50–73) with the path/purpose/license slots parameterized (license text per-deployment; see C5 on whether the Unlicense declaration itself is corpus-bound). | ~110 |
| 0007 file size/density | 154 | c6 L2 · p12 i0 | generalize-in-place | Moves: the named oversized-file queue (0007:30–43). Stays: thresholds, density heuristic, contraction table, the no-code-golf rule — all already language-generic bar the Python framing, which stays (the thresholds are re-derived per language on adoption, as the ADR itself did from LengYue's TS numbers, 0007:9–13). | ~120 |
| 0008 classification discipline | 255 | c5 L2 F1 · p9 i1 | examples-extract | Moves: the detector-misspec and fossil-array substrates (0008:34–76). Stays: both registers, the substitution test, concrete rules 1–4, both Exceptions — all stated generically already; one-sentence pointers carry each substrate's lesson (wrong vocabulary propagated six commits; fossils read as authoritative). | ~170 |
| 0009 perf investigation | 465 | c25 L4 a16 t4 · p38 i0 | examples-extract, condense | The corpus's own precedent, completed: the chocofarm-era body already declared non-binding (0009:52–55) moves verbatim to history; the ADR is rebuilt from its spine (a perf/equivalence claim is honest only when its investigation is captured and reproducible), the two-tier bit-vs-behavioral calibration (0009:219–235, generic), and the 2026-07-12 autoharn amendment's content as the instance-binding section. The two bracket-edits and both dated amendments are preserved verbatim (relocated with the body they annotate, per §4). | ~150 |
| 0010 render-locality N/A | 64 | c9 L7 · p1 i0 | retire-candidate | A lineage placeholder whose stated reason (numbering continuity with LengYue because "the code cites other ADRs by number", 0010:44–49) was chocofarm's fact, not autoharn's — see C6. Proposed disposition: relocate to history; number handling per §6. **Routes to the maintainer as its own question (§9).** | ~15 tombstone |
| 0011 mechanization discipline | 318 | c12 L4 t5 f1 · p11 i4 | examples-extract | Moves: the chocofarm Context substrate (0011:23–55) and the two 2026-06-24 throughput-lab amendments' worked detail (0011:197–262). Stays: Rules 1–4 verbatim in force; the closed enforcement-surface vocabulary (subject to C8's proposed extension); both 2026-07-02 amendments (mechanism-ships-with-first-fix; negative-control + shipped-binding) — these are normative and generic; the `FeatureLayout` worked proof compressed to its two-sentence lesson. | ~200 |
| 0012 structural hygiene | 1404 | c6 f1 · p49 i5 | examples-extract, condense | The largest extraction. Moves: the whole C++ concrete-guidance section (0012:732–943, the chocofarm wire contract — redis keys, weight manifest, X/PI/M/Y blocks); P9's three long worked examples (0012:609–728); the cross-device amendment's bench saga (0012:1155–1325, keeping its rule + checklist row inline). Stays: the anti-pattern checklist with all appended rows; all nine principles, each with its checkable rule and a one-to-three-sentence worked-example summary; the Self-application surface declarations; the 2026-07-02 amendments (corrective-diff-is-new-structure; P2 advertised-limits) whose rules are generic. P1–P9 identifiers and checklist row letters are load-bearing citations corpus-wide and are **not** renamed. | ~550 |
| 0013 execution integrity | 609 | c1 f1 · p23 i4 | examples-extract | Moves: Specimens 1–2's full narratives (0013:73–172, the leaf-eval delinquent and the diagnostician). Stays: Rules 1–5 verbatim in force; the register preamble (0013:35–43, the earned-disdain note — it is the tenet's voice, not an instance); all three amendments verbatim (fair-dealing; artifact-terminates-at-effect + claim shape; Rule-3 mechanization + proviso); per specimen, a three-sentence inline summary — the maintainer's most-important-context bar applies hardest here, because the specimen story is the tenet's teeth: "done" claimed against the author's own contradicting trailers; the diagnostician recommending the skip minutes after diagnosing it. | ~400 |
| 0014 second opinion | 475* | c1 t7 · p0 i0 | examples-extract | Moves: the throughput-lab specimen (0014:76–117). Stays: Rules 1–4; the license-not-mandate register note; the ADR-0008 known-tension section (0014:383–411 — an honest open question, preserved; see §7 open loops). *The file also carries a corruption: lines 474–475 are literal `</content>`/`</invoke>` tool-residue after the License section — a defect fixed in Phase 2 as its own witnessed item (hazard flagged below; `law/` is read-only for this spec). | ~350 |
| 0015 verification substrate | 145 | f1 · p2 i3 | already-portable | Nothing moves. The four rules are generic; the Provenance incident (0015:13–23) is a dated point-in-time record that stays verbatim per §4 — it is one paragraph, below the extraction threshold. Light touch only if C3 (status) adjudication requires a header edit. | ~145 |
| 0016 service contract | 411 | f9 · p19 i5 | examples-extract | Moves: the fact-mining worked-instance inventories woven into Rules 1 and 3's enforcement paragraphs (0016:163–180, 227–240) and the Context feeder narrative (0016:87–127). Stays: the four rules and the one-sentence spine (0016:130–137) verbatim; the standing-service invariant definition; the 2026-07-03 ratification amendment verbatim (dated record); per rule, the instance compressed to its lesson (`BoundedBatch`-at-every-ingress; the empty-warm-cache readiness lie). | ~280 |
| 0017 zero-context reader | 557 | a7 f1 · p9 i0 | already-portable | Nothing moves. This ADR was *written* portable: "Rules 1–4 name no autoharn-specific mechanism… autoharn's own bindings live in the 'Instance bindings' section" (0017:43–47), which is exactly the target shape this whole refactoring drives the corpus toward. The named specimens (BRIEF, morning defects) are its dated substrate, kept per §4. One stale bullet fixed per C2 ruling. | ~557 |

**Headline numbers.** 18 ADRs: primary treatment `examples-extract` × 7 (0000, 0003,
0008, 0009, 0011, 0013, 0014) plus 0012 and 0016 (9 total carrying it),
`generalize-in-place` × 5 (0002, 0004, 0005, 0006, 0007), `already-portable` × 2
(0015, 0017), `retire-candidate` × 2 (0001, 0010). Projected corpus: 6,705 lines →
~3,850 in `law/adr/*.md` + ~2,300 relocated verbatim under `law/adr/history/`
(relocation preserves bytes; the ~550-line net reduction is Context/instance prose
replaced by pointer summaries). Succinctness AND completeness: no rule is dropped or
weakened anywhere in this table — the deltas are all narrative, never normative (§5 A3
is the check).

---

## §3 The history directory and the Extraction Pointer convention

**Directory: `law/adr/history/`, one file per source ADR, named `NNNN-<topic-slug>.md`**
(e.g. `history/0012-cpp-wire-contract.md`, `history/0013-attrition-specimens.md`; an ADR
whose extractions are heterogeneous may carry two files, still `NNNN-`-prefixed).

Argued against ADR-0005 Rule 2 (records have a predictable home, "one place, known to
the next reader", 0005:110–125), versus the alternative `law/history/`:

- **Predictability.** The `NNNN-` prefix makes the home *derivable from the citation*: a
  reader holding ADR-0012 knows its extracted matter is `history/0012-*` without an
  index. `law/history/` would need its own filing convention and would mix ADR history
  with any future non-ADR history.
- **Self-containment for scaffolding.** A deployment that vendors or references
  `law/adr/` gets a corpus whose internal pointers all resolve one directory down —
  relevant because the scaffold's templates already link `law/adr/` paths
  (e.g. `bootstrap/templates/APPARATUS.md:82,143`).
- **Honest naming (ADR-0008).** "history" over "examples": the extracted matter is
  dominated by dated evidence — specimens, incident narratives, superseded instance
  bindings — not reusable how-to examples. Calling it examples would misdescribe the
  content; the maintainer's own phrase ("examples/history directory") permits either.

Every history file opens with a frozen-record banner:

> *Point-in-time record (ADR-0005 Rule 8): extracted verbatim from
> `law/adr/NNNN-….md` at commit `<pre-refactor hash>` under
> `design/MAINT-ADR-PORTABILITY-SPEC.md` (tracker `adr-portability-refactor`). Not
> retro-edited; the lessons these records teach live as rules in the parent ADR.*

**The Extraction Pointer** (the named pointer-with-summary convention) is the block left
behind in the ADR. Shape: a bolded label naming what moved, the destination link, and a
two-to-five-sentence summary carrying the most important context — per the commission,
enough that the rule's motivation is recovered from the ADR prose alone. One worked
example, as it would appear in refactored ADR-0013:

> **Extracted record — the attrition specimens**
> *(moved verbatim to `history/0013-attrition-specimens.md` — rendered in the real ADR as
> a resolving relative link per ADR-0017 Rule 2(b); shown as a code span here because the
> file exists only after Phase 2 — refactor spec `MAINT-ADR-PORTABILITY-SPEC.md`)*:
> two dated, first-person failures are this tenet's substrate. A contributor delivered
> ≈half a ratified refactoring plan while claiming completion — the author's own commit
> trailers contradicted the claim, and the deferral was flagged in prose but never
> authorized or filed, which is Rule 2's whole lesson: disclosure is not authorization.
> Then the agent that *audited* that failure, given an explicit do-everything mandate,
> immediately drafted a recommendation to skip the invasive part — attrition recurs in
> the diagnostician and presents as prudence, which is why Rule 3 treats the
> lower-ROI demurral as a tell, not an argument.

**The inline-vs-move criterion**, stated once here as the Phase-2 executor's test
(operationalizing the maintainer's words: most-important context recovers directly from
prose; large examples move):

1. **Stays inline, always:** the rule statement; anything normative (closure-statement
   definitions, enforcement-surface declarations, amendment text that changed a rule);
   the one-to-three-sentence lesson per specimen (what happened, what it cost, what the
   rule forecloses); any example ≤ ~10 lines that *is* the rule's clearest statement.
2. **Moves, presumptively:** any worked example or specimen narrative > ~15 lines;
   anything a reader needs source-project file paths to parse; superseded instance
   bindings; measurement sagas and bench numbers.
3. **Tiebreak:** if a zero-context reader in a *different* project would lose the
   ability to **apply** the rule when the passage moves, it stays; if they would only
   lose the **story**, it moves — and the pointer summary keeps the story's point.

---

## §4 ADR-0005 Rule 8 handling — what may be rewritten, what must be preserved

The ADRs are living law *and* partly point-in-time records (several say so of
themselves: 0000:37–39, 0009:47–55, 0013:124–131). Rule 8 (0005:147–160) forbids
silently rewriting a point-in-time artifact. The refactoring therefore draws this
boundary, and Phase 2 executes strictly inside it:

**MAY rewrite (fresh authorship, as one dated, maintainer-ratified act):**

- **Rule statements and Decision prose** — generalization only, never weakening; each
  Phase-2 package's close carries the before/after rule inventory (§5 A3) so "not
  weakened" is checkable, in ADR-0000's closure-statement form.
- **Context, Consequences, Exceptions, Revisit-when, Related, "What this does NOT
  mean"** — compressed and generalized, with instances replaced by Extraction Pointers.
- **Scope and Genre header fields** — re-instanced to bind the hosting deployment
  generically. Precedent: ADR-0009's 2026-07-12 bracket-edit (0009:22–76). Because a
  per-field bracket-strike across 16 ADRs would reproduce corpus-wide the very
  illegibility being cured, the wholesale form substitutes ONE dated note per ADR (below)
  plus git for the stricken text — the same preserved-original guarantee, one hop away.

**MUST preserve verbatim (in place, or relocated-not-rewritten):**

- **All dated Amendment sections, Revisit entries that are dated appends, ratification
  provisos, and quoted maintainer words** (e.g. 0000:497–523, 0013:500–605, 0016:351–407,
  0017:3–9 and its Provenance quotes). Normative amendments stay in the ADR; narrative
  amendment *substrates* (worked instances, measurements) may relocate to history with
  the amendment's rule content remaining inline.
- **Provenance fields and incident narratives** — relocation to history verbatim is
  sanctioned (that is ADR-0005 Rule 5's move-with-repointing, not a rewrite); rewording
  is not.
- **Status fields** — facts of ratification history; changed only by explicit maintainer
  adjudication (C3), never by the refactor.
- **Other documents' quotations of pre-refactor ADR text** — never retro-edited
  (0005:158–160's frozen-referrer rule). The refactoring note below is what makes a
  quote-vs-current divergence explicable rather than mysterious.

**The anti-falsification mechanism.** Every refactored ADR carries, immediately under
its header block, a dated refactoring note:

> *Refactored for cross-project portability on <date> under
> `design/MAINT-ADR-PORTABILITY-SPEC.md` (tracker `adr-portability-refactor`,
> maintainer-ratified <date>). The pre-refactor text stands verbatim at commit
> `<hash>`; extracted records live in `history/` (a resolving link in the real note) and
> are not retro-edited.
> Dated amendments below are preserved verbatim from the original.*

This is how the refactored corpus does not falsify its own history: every document
announces the act, names the spec and tracker item, and points at both the frozen bytes
(git) and the relocated records (history/). Nothing is silently rewritten because
nothing is rewritten silently.

---

## §5 Portability acceptance criteria (all checkable)

- **A1 — proper-noun grep.** `grep -rniE 'chocofarm|lengyue|ffxiii|throughput-lab' law/adr/*.md`
  (and `fact-mining` outside 0015/0016's preserved provenance): every remaining hit sits
  either (a) inside a verbatim-preserved dated Amendment/Provenance block, or (b) on an
  Extraction Pointer line. Zero hits in rule/Decision text. Phase 2 mechanizes this as a
  small gate script with a negative control (per ADR-0011's 2026-07-02 amendment: shown
  red on the pre-refactor tree before its green is credited).
- **A2 — fresh-context application test.** Per refactored ADR, the A:B:C attestation's B
  brief (§8) gains one clause: *"For each rule, state whether you could apply it in an
  unrelated project without reading this repository; name any rule you could not."* Any
  cannot-apply verdict fails the package.
- **A3 — completeness closure (no rule weakened or dropped).** The per-ADR rule
  inventory is enumerated below; each Phase-2 package's close reproduces it and asserts,
  per rule, PRESENT-UNCHANGED or PRESENT-GENERALIZED (with the diff cited); any DROP
  routes to the maintainer before the package lands. Inventory (before): 0000 R1–R3 +
  closure-statement amendment + Revisit #4 Clauses 1–2 (standards-scope disclaimers
  mandatory; the standards registry as the root of every completeness exercise, with its
  codification proviso); 0001 three seam rules (retirement question); 0002
  hierarchy + rules 1–6; 0003 the two-question principle + no-premature-extraction; 0004
  the two-case rule; 0005 R1–R9; 0006 the three-part header rule; 0007 size + density +
  contraction rules; 0008 two registers + substitution test + rules 1–4; 0009 spine +
  two-tier calibration + triggers/acceptance; 0010 none (placeholder); 0011 R1–R4 + four
  amendments' rules; 0012 checklist rows A–H + 5 appended rows + P1–P9 + advertised-limits
  amendment; 0013 R1–R5 + three amendments' rules; 0014 R1–R4; 0015 R1–R4; 0016 R1–R4;
  0017 R1–R4 + A:B:C loop commitments.
- **A4 — link and shape gates.** `gates/link_integrity.py` clean corpus-wide (every
  Extraction Pointer resolves); `gates/doc_shapes.py` clean on every touched file.
- **A5 — attestation presence.** Every touched `law/adr/*.md` and every new history file
  carries a doc-attestation record (the armed `gates/doc_attestation_presence.py`).
- **A6 — citation stability.** Per-number citation counts outside `law/adr/`
  (baseline witnessed 2026-07-13: 2,026 `ADR-00NN` instances repo-wide; top consumers
  ADR-0011 ×305, ADR-0012 ×242, ADR-0000 ×217 outside the corpus) are unchanged by the
  refactor — no citation site breaks, because no number changes (§6) and P1–P9 / rule
  numbers / checklist letters are held stable.

---

## §6 Topology, renaming, renumbering (per amendment item 1)

Authorization is not obligation, and the recommendation here is: **keep every number.**
The measured cost side: 2,026 `ADR-00NN` citation instances repo-wide (223 citing files
outside `law/adr/` alone), plus 37 instances across 12 scaffold templates
(`bootstrap/templates/`), plus already-scaffolded worlds (ent) carrying baked copies
that are, by the runs-are-linear ruling, never patched in place. The benefit side:
nothing — the numbering carries no wrong information; only 0010's *slot* is
questionable, and a renumbering to close one gap would repoint two thousand citations to
save one tombstone. Where the current numbering is fine, this spec says so: it is fine.

Two bounded renames ARE proposed, each with its migration count:

- **R1 — 0013 filename.** `0013-execution-stamina-and-structural-completeness.md` vs its
  own H1 "Execution Integrity — Against the Attrition of Will" (0013:1) — the file was
  named for a draft title. Rename to `0013-execution-integrity.md`. Migration: 12 citing
  files reference the current slug (grep-counted); Phase-2 WP-8 repoints all 12 in the
  same commit, `gates/link_integrity.py` is the witness. The *number* does not change.
- **R2 — 0001/0010 slots on retirement (contingent).** If the maintainer retires 0001
  and 0010 (§9), the numbers are NOT reused: each slot keeps a ~15–25-line tombstone at
  its current filename (status: Retired-to-history, pointer to the relocated record) —
  the same slot-kept-but-empty move 0010 itself models (0010:15–30), now for autoharn's
  reason (18 and 6 external citation instances respectively still resolve) rather than
  chocofarm's. Migration cost: zero.

No regrouping/reordering is proposed. The corpus's implicit topology (foundations 0000 +
0011/0012/0013 trio; authoring tenets 0002–0009; execution tenets 0013–0016;
documentation 0005/0017) is navigable as-is, and the corpus already carries its own maps
in Genre fields. A table-of-contents README in `law/adr/` (new file, not a law change to
any ADR's text) is offered as an optional Phase-2 addendum if the maintainer wants the
topology legible without renumbering — cost ~60 lines, zero migration.

---

## §7 Contradictions register (per amendment item 2 — for maintainer adjudication)

Each entry: both horns with file:line, one line on what conflicts, and a PROPOSED
resolution. Nothing here is resolved silently in §2; Phase 1b incorporates the rulings.

- **C1 — ADR-0017 is ratified law that calls itself an unratified draft.**
  Horn A: status header, "ACCEPTED — maintainer-ratified 2026-07-11" (0017:3–11).
  Horn B: "Not settled law. This is a draft awaiting the maintainer's word, filed in
  `design/`" (0017:552–553) — and the file sits in `law/adr/`.
  Conflict: the closing bullet was not updated at ratification.
  PROPOSED: Phase 2 adds a dated strike of the stale bullet (Rule 8 in-situ dated
  strike), no other change.

- **C2 — "Proposed" ADRs are treated corpus-wide as binding law.**
  Horn A: ADR-0011 status "Proposed" (0011:3), ADR-0012 status "Proposed" (0012:3),
  ADR-0015 "Proposed… filed for maintainer ratification" (0015:3–4).
  Horn B: CLAUDE.md lists 0012 among the binding Project LAW; 305/242/54 external
  citation instances respectively treat them as in force; 0016 demonstrates the corpus
  records ratification when it happens (0016:3, 351–357).
  Conflict: the status metadata says not-yet-law; the practice and the constitution say
  law.
  PROPOSED: the maintainer bulk-adjudicates 0011/0012/0015 to Accepted in this
  ratification (a status edit under §4's maintainer-only carve-out), or explicitly
  records that Proposed-status ADRs bind in this corpus.

- **C3 — ADR-0005 Rule 2 mandates filing homes that do not exist here.**
  Horn A: Rule 2 names `docs/design/`, `docs/consults/`, `docs/agents/`,
  `docs/results/`, `docs/notes/audit/` as the homes (0005:110–125).
  Horn B: the repository's actual homes are `design/`, `law/briefs/`, `judgment/`,
  `research/`, `attestations/` — no `docs/` tree exists (witnessed by directory
  listing).
  Conflict: the law commands filing into directories the project does not have; every
  compliant filing since fork has technically violated the rule's letter.
  PROPOSED: §2's treatment — Rule 2 keeps the convention (one predictable home per
  record kind) and the table of homes becomes a per-deployment declaration; autoharn's
  declaration lists the five real homes.

- **C4 — the unadapted-copy class: seven scope clauses bind a package that is not this
  project.** Horn A: Scope fields binding "the `chocofarm/` package" in 0002:19–24,
  0004:13–15, 0005:17–19, 0006:15–17, 0007:14–15, 0008:23–25, 0011:19–21, 0012:25–30.
  Horn B: ADR-0009's own 2026-07-12 amendment names exactly this state a defect and
  fixes it for itself ("arrived in autoharn as an unadapted copy… Scope still bound 'the
  chocofarm/ package'", 0009:26–33), maintainer-ratified.
  Conflict: the corpus's binding scope statements are false for the project they govern,
  and the corpus itself has already ruled such a state defective — once, for one file.
  PROPOSED: this whole spec is the resolution (the 0009 precedent applied corpus-wide);
  listed so the maintainer ratifies the *class*, not seventeen instances.

- **C5 — per-file Unlicense declarations vs autoharn's actual file conventions.**
  Horn A: ADR-0006 requires every source file to carry "Public Domain (The Unlicense)"
  (0006:58–62), and every ADR ends with that license block.
  Horn B: autoharn's own source files carry provenance stamps
  (e.g. `gates/doc_attestation_presence.py:1–6`), not Unlicense docstrings, and the
  repository ships a `LICENSE` file whose terms the maintainer owns.
  Conflict: the header rule's license slot encodes the source project's licensing
  posture as if it were the adopter's.
  PROPOSED: 0006's rule keeps the slot, parameterized ("the project's declared license,
  if per-file declaration is the project's posture"); whether autoharn's ADR files
  themselves keep the Unlicense footer is the maintainer's licensing call, flagged here
  rather than assumed.

- **C6 — ADR-0010's reason to exist does not survive its own fork.**
  Horn A: 0010 keeps its empty slot for "numbering continuity with the LengYue lineage…
  the code cites other ADRs by number" (0010:26–30, 44–49) — chocofarm's code, that is.
  Horn B: no autoharn artifact depends on LengYue-alignment (only 6 external citation
  instances even mention ADR-0010, all descriptive), and the commission amendment now
  explicitly authorizes renumbering.
  Conflict: the document's sole justification is another project's constraint.
  PROPOSED: retire to history with a tombstone (§6 R2); the tombstone preserves
  number-stability so even those 6 citations still resolve.

- **C7 — ADR-0017 carries a Revisit item its own body already discharged.**
  Horn A: Revisit #1 — "The link-resolution gate lands. Record it… tighten Rule 2(b)'s
  declared surface from 'commissioned'" (0017:481–483).
  Horn B: Rule 2's enforcement text already records the gate as merged and blocking
  ("landed mid-draft… merged `b5f9180`… already wired as a blocking pre-commit step",
  0017:234–238, 366–371).
  Conflict: an open Revisit trigger that fired before ratification and was never struck.
  PROPOSED: dated strike in Phase 2 (same commit as C1's fix).

- **C8 — two ADRs rank an enforcement level the closed vocabulary does not contain.**
  Horn A: ADR-0011 Rule 1's closed vocabulary is construction/import-time · test/CI gate
  · write-time data constraint · run-time invariant · review-only (0011:64–75), and
  ADR-0008 governs extending closed vocabularies.
  Horn B: ADR-0012 P7 ranks "generate-or-compile-from-one-source > **build-time lint** >
  runtime parity" (0012:319–330), and P9 rule 5 asserts "compile-time > runtime in the
  loudness hierarchy P5 defers to" (0012:569–573) — but neither build-time-lint nor
  compile-time is a rung in 0011's vocabulary or 0002's hierarchy (0002:85–106).
  Conflict: the corpus's most-cited ADR enforces at a level its own enforcement
  vocabulary cannot name.
  PROPOSED: extend 0011 Rule 1's vocabulary with a build/compile-time member — a
  fail-safe, additive change in the sense of [CLAUDE.md](../CLAUDE.md)'s
  "class-ratified fail-safe deltas" ruling (a change that only *adds* vocabulary or
  refusals, relaxing nothing existing, is pre-ratified as a class); 0002's hierarchy
  gains the rung by the same dated amendment.

- **C9 — ADR-0013's filename contradicts its title.** Horns and proposal in §6 R1
  (filename says "execution stamina and structural completeness"; H1 says "Execution
  Integrity", 0013:1). Listed here for completeness of the register.

- **C10 — ADR-0000's new "Revisit #4" heading collides with Revisit-when item 4, which
  it does not discharge.**
  Horn A: the corpus's established convention, set by "Revisit #3 — 2026-07-12"
  (0000:497), whose content (the demurral-detector mechanization) discharges
  Revisit-when list item 3 (0000:370–374) — the heading number names the list item
  being fired.
  Horn B: the 2026-07-12 section "Revisit #4" (0000:525) concerns standards-scope
  disclaimers and the standards registry, while Revisit-when list item 4 (0000:375–378)
  is the ADR-0014 hand-off reconciliation — still open, unrelated to the new section's
  content.
  Conflict: a reader following the Revisit #3 precedent reads "Revisit #4" as item 4
  discharged; it is not, and the new section corresponds to no list item at all.
  PROPOSED: Phase 2's WP-9 adds a one-line dated clarifying note under the heading
  (the section text itself stays verbatim per §4) stating it is a new numbered revisit
  record, not a discharge of list item 4, which remains open.

**Open loops surfaced (not contradictions — flagged for the same adjudication sitting,
since the amendment authorizes reclassification):** ADR-0000 Revisit-when item 1 leaves
open whether 0000 is a distinct root or a frame over the 0011/0012/0013 trio
(0000:352–365); ADR-0014's Known-tension section leaves open whether it stands, folds
into 0013, or folds into 0011 (0014:383–411); ADR-0000 Revisit-when item 4 asks for a
hand-off reconciliation "once ADR-0014 is ratified" and 0014 remains Provisional
(0000:375–378, 0014:3 — see C10 for the heading collision with the new section of the
same number). None blocks the refactor; a ruling on 0014's fold question would change
one row of §2, so it is cheapest decided before Phase 1b.

---

## §8 Phase 2 execution plan (Sonnet, post-ratification)

**Fourteen work packages.** Each is one Sonnet builder in an isolated worktree; every
touched document (refactored ADR, new history file, repointed citer) carries an
ADR-0017 A:B:C attestation — fresh-context B forks both rounds (round-2 B a fresh fork,
never resumed), two-round cap with still-DEFECT marked `escalated:true`, B given only
the document plus ADR-0017 plus this spec's §5 A2 clause, B prints its verdict as its
final message and never uses SendMessage, table row/column labels treated as referents
under Rule 1(b) — recorded via `gates/doc_attestation_presence.py --record`. Every
package commits with `CLAUDE_COMMIT_PATHS` set to its exact staged paths, and its close
reproduces §5 A3's rule inventory for the ADRs it touched.

| WP | Content | Depends on |
|---|---|---|
| WP-0 | Create `law/adr/history/` + its README (frozen-record banner + Extraction Pointer format, the convention's one home per ADR-0012 P1) + the §5 A1 gate script with negative control. Touches no existing ADR. | ratification |
| WP-1 | 0001 + 0010 disposition per the §9 retirement rulings (relocate + tombstones, or generalize if the ruling is keep). | maintainer ruling |
| WP-2 | Small generalize batch: 0004, 0006, 0007. | WP-0 |
| WP-3 | 0002 + 0008 (siblings; cross-cite each other's registers). | WP-0 |
| WP-4 | 0005 (filing-homes parameterization per C3 ruling). | WP-0, C3 ruling |
| WP-5 | 0003 (band-map extraction; template instruction for adopters). | WP-0 |
| WP-6 | 0009 (body relocation — the precedent-completing package; establishes the large-extraction pattern). | WP-0 |
| WP-7 | 0011 (extraction + the C8 vocabulary amendment if ratified). | WP-6, C8 ruling |
| WP-8 | 0013 (specimens extraction + R1 filename rename, repointing all 12 slug citers) then 0014 (specimen extraction + the tail-corruption fix as its own witnessed item). | WP-7 |
| WP-9 | 0000 (specimen extraction; cites 0011/0012/0013/0014 heavily, so runs after their shapes settle). | WP-7, WP-8 |
| WP-10 | 0016 (instance extraction; cites 0011's amendments). | WP-7 |
| WP-11 | 0012 (the largest; C++ section + P9 examples + cross-device saga to history). | WP-6, WP-7 |
| WP-12 | 0015 + 0017 verify-only pass (already-portable confirmation; C1/C7 dated strikes per ruling). | WP-0 |
| WP-13 | Corpus-wide close: run A1–A6; repoint any cross-ADR section links the extractions moved; verify the 37 template citation instances and `GLOSSARY.md`'s ADR links still resolve. | all above |

**Deployment-side consumers when it lands.** (a) `bootstrap/templates/` — 37 ADR
citation instances across 12 templates cite numbers and principle IDs (e.g. "ADR-0012
P1", `led.tmpl` ×14); all survive because numbers and P-IDs are held stable; WP-13
verifies. (b) **ent's live world** — carries baked template copies; per the
runs-are-linear ruling (maintainer, 2026-07-11, recorded in [CLAUDE.md](../CLAUDE.md)'s
ORCHESTRATION section: an existing world is read-only evidence, never patched,
refreshed, or delta'd — changes reach reality only via the next world's scaffold) it is
never patched: the refactored corpus reaches ent via its next scaffold, and no
live-session file is touched (standing rule). The commissioned
"ent CLAUDE.md live-pointer section" is outside this repository; WP-13's close hands the
maintainer a one-line note naming what a re-scaffold inherits. (c) `GLOSSARY.md` and the
ORCH docs — the former is repointed by WP-13 where section anchors moved; the latter are
history unless a current spec cites them (standing contract) and are left alone.
(d) **the standards registry** — ADR-0000 Revisit #4 Clause 2 makes
`law/STANDARDS-REGISTRY.md` the root of every completeness exercise; it is a
per-deployment artifact by nature (each project names its own bars), so the portable form
of Clause 2 is the rule plus a registry *slot*, and whether the scaffold should ship a
blank registry template to new deployments is flagged to the maintainer as an optional
WP-13 question, not decided here.

---

## §9 What this spec does NOT do

- **No `law/` edit now.** Phase 1a produces this document only; every law change above
  executes in Phase 2, after ratification, by Sonnet, inside §4's boundary.
- **No renumbering.** Authorized by the amendment, evaluated in §6, declined on measured
  cost (2,026 citation instances) versus nil benefit. The two proposed renames (R1
  filename; R2 contingent tombstones) each carry their migration count in §6.
- **No silent retirement.** 0001 and 0010 are retire-*candidates* only; each routes to
  the maintainer as its own yes/no question at adjudication (retire-to-history with
  tombstone, or keep-and-generalize). No other ADR is proposed for retirement.
- **No contradiction resolved by fiat.** Every §7 entry awaits the maintainer; §2's
  treatments that depend on a ruling say so in §8's dependency column.
- **No scope creep into non-ADR law.** `law/briefs/`, `law/keys/`, and
  `law/STANDARDS-REGISTRY.md` are untouched — the registry changes only by maintainer
  amendment per its own property 3, and it was read for this spec's analysis (it is the
  instance binding of ADR-0000 Revisit #4 Clause 2, not a refactoring target);
  `bootstrap/templates/`, `tools/`, and the ORCH docs are out of scope except WP-13's
  read-only verification.

---

## Hazards flagged during the corpus read (fix-or-flag duty; `law/` is read-only for this spec, so: flagged)

- **H1 — ADR-0014 file corruption.** `law/adr/0014-executor-second-opinion.md:474–475`
  contains literal `</content>` and `</invoke>` lines after the License section —
  tool-call residue committed into a law file (verified byte-level with `cat -A`).
  Scheduled as a witnessed fix inside WP-8; flagged here because it is a defect in law
  standing today, independent of the refactor.
- **H2 — commissioned file "does not exist" (original claim, WRONG — dated correction
  follows).** As first drafted, this entry read: *"This spec's commission named
  `law/STANDARDS-REGISTRY.md` as required reading; no such file exists anywhere in the
  repository (searched by name and by content reference). Either the file is expected
  from a different branch/world or the commission carried a stale name."*
  **Correction (2026-07-13, per ADR-0005 Rule 8 — original preserved above, not
  silently rewritten):** the claim was wrong, and the search was honest but ran against
  a stale substrate — this worktree's base (`fca1100`) predated commit `24d1dfc`
  (2026-07-12), which created `law/STANDARDS-REGISTRY.md` together with ADR-0000's
  Revisit #4. The file exists on the current branch and has now been read in full; the
  Revision note in the header records everything the correction touched. What H2
  actually witnessed was a stale-base defect in this spec's own process — itself a
  small instance of ADR-0015's lesson (a verification's substrate is part of its
  meaning): a repo-wide search on an out-of-date base is not a repo-wide search.

## License

Public Domain (The Unlicense).
