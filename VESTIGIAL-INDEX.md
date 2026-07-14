# VESTIGIAL-INDEX

Audience: maintainer (+secondary: orchestrator)

This file is the index of every document the 2026-07-12 vestigial-doc-sweep moved out of the
working tree into `vestigial_documentation/`, mirroring each file's origin subpath (so
`design/ORCH-ARCHITECTURE.md` landed at `vestigial_documentation/design/ORCH-ARCHITECTURE.md`,
`judgment/e-series/e15-analysis-consult-27.md` at
`vestigial_documentation/judgment/e-series/e15-analysis-consult-27.md`, and so on). None of
these 47 files were deleted or edited in content — each was `git mv`'d, byte-for-byte, and the
sweep's classification record (a Sonnet classifier's verdict, adversarially checked by a
second Sonnet skeptic biased to REFUTE the verdict, both recorded under the open work item
`vestigial-doc-sweep` in this project's decision ledger — the append-only Postgres record of
tracked decisions, findings, and work items that every session reads and writes through the
`./led` command) is preserved below as one paragraph per file. The move itself was the
maintainer's own commission (a row of kind `work_opened`, ledger row id 241, 2026-07-12
evening: "the documentation hodge-podge is dealt with by REMOVAL AND CONSOLIDATION in service
of the project"), and its disposition on this exact 47-file list is the maintainer's own
adjudication (a row of kind `decision`, ledger row id 251, 2026-07-12 late evening, verbatim in
substance: *"Let's apply it... the classification as you would suggest them stand"*) — the
sweep applies as-is, with no file added or dropped from what the skeptic upheld.

**If you need one of these files back at its old path**, git remembers it as a rename, not a
deletion:

```
git log --follow -- <old-path>
```

will show its full history including everything before the move; `git show <commit>:<old-path>`
or a plain `git mv` back will restore it if you decide it should live in the working tree again.

**On the read-decay reaper the maintainer's commission also asked for:** the commission
specifies that a file in `vestigial_documentation/` unconsulted within a 200-to-1000-read
window should eventually be removed from the working tree entirely, leaving only this index
paragraph and git history as its recovery path. That count is denominated in READ EVENTS, not
wall-clock time — specifically, entries an aggregation of the `read_observer` journal (a planned
per-agent log of file-read events, counting only an agent's own reads of a file, never a
maintainer's) would produce once built. That reaper is **spec'd here in prose only — it is not
built**. No journal-aggregation tooling exists yet to count reads against these files, and no
automated removal runs. Saying so plainly, per this project's own zero-context-reader
discipline (law/adr/0017-the-zero-context-reader.md): nothing below is silently subject to
deletion today: every file this index names stays exactly where the sweep put it until that
separate, spec'd item is built and armed.

**Provenance**, repeated per entry below rather than left implicit: every verdict here is
*machine-consensus (classifier + adversarial skeptic) + maintainer-approved 2026-07-12* — a
Sonnet classification pass, a second Sonnet skeptic pass biased to keep on doubt, and the
maintainer's own explicit sign-off on the resulting list (ledger id 251). No file moved here on
a single model's unchecked say-so.

## `ORCH-DIRCLASS.md` (root) — 1 file, CONSOLIDATE

- **Old path:** `ORCH-DIRCLASS.md`. **New path:**
  `vestigial_documentation/ORCH-DIRCLASS.md`.
  This file classified every top-level directory along one axis (CORE / DOC / RESEARCH / OTHER
  — is the directory needed for a functioning autoharn, and if not, which non-essential
  category it falls in). Its content substantively dated to 2026-07-09 and carried no inbound
  citation from any current entry doc (`CLAUDE.md`, `ORCH-HANDOFF.md`,
  `ORCH-OPERATING-CARD.md`, `ORCH-CAPABILITIES.md`, `README.md`, `USER-GUIDE.md`); meanwhile
  `README.md`'s own "The tree" section already walked a fresh reader through the same
  directories for the same purpose, creating two competing "what is this directory" references
  where one would do. Rather than deleting the CORE/DOC/RESEARCH/OTHER axis outright (it is a
  real, useful distinction — e.g. it is what names `judgment/` and `law/` as straddling
  DOC-but-binding-in-spirit), the sweep folded its per-directory labels into `README.md`'s tree
  as terse bracketed tags (`[CORE]`, `[DOC]`, `[RESEARCH]`, `[OTHER]`, with straddle notes kept
  verbatim) before moving this file out — see docs/PROJECT-OVERVIEW.md's "The tree" section for
  the merged result (that section, and the rest of README.md's prior general content, moved
  there on 2026-07-14, ledger item `readme-idiots-deployment-guide`, when README.md became a
  pure git-submodule deployment guide). Provenance: machine-consensus (classifier + adversarial
  skeptic) + maintainer-approved 2026-07-12.

## `design/` — 8 files, all VESTIGIAL

- **`design/ORCH-ARCHITECTURE.md`** → `vestigial_documentation/design/ORCH-ARCHITECTURE.md`.
  The original architecture through-line document from the pre-consolidation `claude_harness`
  layout (2026-06-27), migrated wholesale into autoharn on 2026-07-07 without being rewritten;
  its internal paths and structure still point at the old tree. Vestigial because the document
  itself declares STALE at the top, the project's own link-integrity gate explicitly excludes it
  from currency checks, and a full rewrite is filed as owed-but-not-current BACKLOG work rather
  than something the project relies on today. (`gates/link_integrity.py`'s `EXCLUDE_FILES`
  exclusion for this document was updated in the same commit as this move to follow it to its
  new path.) Provenance: machine-consensus (classifier + adversarial skeptic) + maintainer-approved
  2026-07-12.

- **`design/ORCH-DEPLOYMENT-ROADMAP.md`** →
  `vestigial_documentation/design/ORCH-DEPLOYMENT-ROADMAP.md`. A 2026-07-07 deployment-readiness
  analysis for a claude-code hook backed by an NLP fact-extraction pipeline (`fact-mining/`:
  spaCy/coref/SVO parsing) feeding a human-or-LLM adjudication service (`adjudicate/`) over a
  ZMQ message bus. Vestigial because that entire substrate (fact-mining/, adjudicate/, the ZMQ
  daemon) was never built and the project pivoted instead to the ledger-plus-clingo/ASP
  architecture (kernel lineage, `engine/`, `./judge`) that exists today; nothing here is cited
  by any current spec or code — the only mention of this file anywhere is a mechanical,
  machine-written entry in `attestations/doc-legibility-attestations.jsonl` (the separate,
  append-only file this project's ADR-0017 fresh-context-review records live in, distinct from
  the decision ledger defined above), not a citation from a document a reader would consult.
  Provenance:
  machine-consensus (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

- **`design/ORCH-HOOK-DESIGN.md`** → `vestigial_documentation/design/ORCH-HOOK-DESIGN.md`. The
  earliest (2026-07-02) hook design: one "Guardrails Hook" that interrogates an AI
  collaborator's epistemic state against a knowledge base built from the Gutenberg-corpus NLP
  proof-of-concept. Vestigial because the actual `hooks/` mechanisms that shipped
  (`change_gate`, `stamp_intercept`, `mutation_observer`, `doc_shapes_gate`, etc., all catalogued
  live in `ORCH-OPERATING-CARD.md`) are a structurally different, ledger-native design that
  superseded this one; the NLP/Gutenberg substrate it depends on was never built. Provenance:
  machine-consensus (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

- **`design/ORCH-LOGIC-LAYER-ASP.md`** →
  `vestigial_documentation/design/ORCH-LOGIC-LAYER-ASP.md`. First wiring of the (abandoned)
  "facts in many logics" NLP thread to clingo ASP: `logic_layer.lp`/`logic_repair.lp`/
  `contra_asp.py` over a `contra_detect.py` claim oracle. Vestigial because none of those files
  were ever committed to the repo, and the project's actual ASP layer (`engine/lp/*.lp` driving
  `./judge`) is a structurally unrelated later design over the ledger, not this NLP-fact
  substrate. Provenance: machine-consensus (classifier + adversarial skeptic) + maintainer-approved
  2026-07-12.

- **`design/ORCH-LOGIC-LAYER-SEAM.md`** →
  `vestigial_documentation/design/ORCH-LOGIC-LAYER-SEAM.md`. Generalizes the ASP logic-layer
  adapter into a pluggable `LogicBackend` seam with a second (z3) engine, over the same
  abandoned NLP fact-substrate as `ORCH-LOGIC-LAYER-ASP.md`. Vestigial for the same reason as
  its parent doc: the substrate it builds on (`contra_detect.py`, `logic_layer.lp`) was never
  committed, and the pluggable-seam idea was not carried into the project's actual (later,
  ledger-native) ASP layer. Provenance: machine-consensus (classifier + adversarial skeptic) +
  maintainer-approved 2026-07-12.

- **`design/ORCH-SHIPPING-NORTH-STAR.md`** →
  `vestigial_documentation/design/ORCH-SHIPPING-NORTH-STAR.md`. A 2026-07-07
  packaging/shippability definition proposing a declared PRODUCT-vs-LAB file-set split across
  two interleaved repos, shipped via a `ship/MANIFEST` derived release artifact. Vestigial
  because that packaging mechanism (`ship/MANIFEST`, the two-repo product boundary) was never
  built — the project instead shipped a scaffold-a-world model (`bootstrap/new-project.sh`,
  per-world `deployment.json`) that supersedes this vision; the only mention of this file
  anywhere is the same kind of mechanical attestation-ledger entry described above (`attestations/
  doc-legibility-attestations.jsonl`), not a live citation. Provenance: machine-consensus
  (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

- **`design/ORCH-never-again-mechanism-fable-main.md`** →
  `vestigial_documentation/design/ORCH-never-again-mechanism-fable-main.md`. Fable main-loop's
  independent 2026-07-07 shape for the same 'never-again' foreclosure-debt problem as the
  consult brief above (a `forecloses(mechanism_ref, finding_id)` edge plus derived debt
  judgment), written before that blind consult and predating this repo's current architecture.
  Zero inbound references from any current doc. Superseded by
  `design/ORCH-never-again-synthesis.md`'s ratified hybrid, itself now historical since the
  target schema (`harness.finding`/close manifest) is not this repository's schema. Provenance:
  machine-consensus (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

- **`design/ORCH-policy-authoring-seam.md`** →
  `vestigial_documentation/design/ORCH-policy-authoring-seam.md`. A 2026-07-07 Fable design note
  answering how ephemeral/flexible workflow policies get authored under durable ASP-backed law
  (ratified-pattern-library + `policy_instance` rows + gated LLM-authored novel rules),
  explicitly a companion to "the work-unit-authorization BACKLOG item" from that era. Zero
  inbound references from any current spec, entry doc, or CAPABILITIES item; no `policy_instance`
  table, pattern-template mechanism, or "policy-authoring seam" vocabulary appears anywhere else
  in the current repo, indicating the design was never built and the project moved on to the
  resource-registry/taxonomy/decomposition-policy spec family instead (its actual current answer
  to the same underlying need). Provenance: machine-consensus (classifier + adversarial skeptic)
  + maintainer-approved 2026-07-12.

## `instruments/` — 1 file, VESTIGIAL

- **`instruments/README.md`** → `vestigial_documentation/instruments/README.md`. A directory
  README describing `instruments/` purely from the e6-e13 retrospective-audit era
  (`contemporaneity`/`read_currency`/`observed_currency`/`core_a`/`soundness` scripts), last
  touched 2026-07-07. It predates and does not mention the scripts (`review_fixpoint.py`,
  `conformance_check.py`) that current operational truth (`ORCH-CAPABILITIES.md`) actually
  treats as load-bearing, and its only inbound citation is an older design memo plus provenance
  bookkeeping. Vestigial: an incomplete, stale index superseded in practice by
  `ORCH-CAPABILITIES.md`'s own per-instrument description. Provenance: machine-consensus
  (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

## `judgment/` — 12 files, all VESTIGIAL

- **`judgment/POST-FABLE-OPERATING-BRIEF.md`** →
  `vestigial_documentation/judgment/POST-FABLE-OPERATING-BRIEF.md`. An operating brief Fable
  wrote 2026-07-07 for running the project without Fable-class access, covering e-series
  judgment methodology (pre-banked judgment, frame/application split, and FRAME-GAP findings —
  that predecessor era's label for a case where a judgment's frame and its application to a
  specific instance diverged). It is
  explicitly and verbatim superseded by the root `ORCH-POST-FABLE-OPERATING-BRIEF.md`
  (2026-07-09), which states its own durable judgment was ported forward and that nothing in the
  old file should be trusted beyond what the new one repeats. Vestigial: a superseded
  predecessor kept only for history. Provenance: machine-consensus (classifier + adversarial
  skeptic) + maintainer-approved 2026-07-12.

- **`judgment/e-series/e15-FINDINGS-ratification-package.md`** →
  `vestigial_documentation/judgment/e-series/e15-FINDINGS-ratification-package.md`. A
  proposed-but-never-ratified findings package from the e15 experiment, offering candidate
  F-series entries — a verdict going stale as circumstances change ("verdict-aware staleness")
  and a principal claiming a role it isn't actually performing ("claimed-vs-performing-principal")
  — with an explicit
  checklist gating their application to `FINDINGS.md`. `FINDINGS.md` shows the F52/F53 slots
  this package expected were in fact filled by a later e16 package instead — this one's
  checklist was never discharged and nothing downstream cites it. Vestigial: an abandoned draft
  in the `judgment/` history archive. Provenance: machine-consensus (classifier + adversarial
  skeptic) + maintainer-approved 2026-07-12.

- **`judgment/e-series/e15-analysis-consult-27.md`** →
  `vestigial_documentation/judgment/e-series/e15-analysis-consult-27.md`. The applied analysis
  for experimental run e15, verdicting that "the record told the truth about the work" for that
  one closed session. It is a single-run (N=1) forensic record from the pre-consolidation
  experiment series, its lessons — handling a stale attestation, and triaging a case where a
  principal claimed to have acted but the underlying act was missing ("claimed-without-act
  triage") — having
  fed forward into the current kernel/gate design rather than needing to be read directly.
  Vestigial: historical record of a settled, superseded experiment. Provenance:
  machine-consensus (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

- **`judgment/e-series/e16-FINDINGS-RATIFICATION-PACKAGE.md`** →
  `vestigial_documentation/judgment/e-series/e16-FINDINGS-RATIFICATION-PACKAGE.md`. Ratification
  package recording two findings-derived laws (F52 license-reading law, F53) from experiment
  e16, filed into an older `acts.ruling` ledger. The findings this package ratified are
  historical inputs to law that has since been superseded/absorbed by the current kernel lineage
  and CLAUDE.md ORCHESTRATION rules; nothing in the live operating surface points here for
  current guidance. Vestigial: settled ratification record from the predecessor ledger era.
  Provenance: machine-consensus (classifier + adversarial skeptic) + maintainer-approved
  2026-07-12.

- **`judgment/e-series/e17-FINDINGS-RATIFICATION-PACKAGE.md`** →
  `vestigial_documentation/judgment/e-series/e17-FINDINGS-RATIFICATION-PACKAGE.md`. Ratification
  package for the e17 experiment's five findings — an incompletely-wired review stub
  ("partial-review-stub-seam") and a batch-insert bug in the binder component
  ("binder-batch-insert-artifact"), among others — each already marked fixed or filed at the time. The fixes
  it documents (fc21-fc27 style kernel patches) are long since folded into the shipped kernel;
  the package itself is a closed-out historical record. Vestigial: superseded by the kernel
  state it describes having already reached. Provenance: machine-consensus (classifier +
  adversarial skeptic) + maintainer-approved 2026-07-12.

- **`judgment/e-series/e19-design-SEED.md`** →
  `vestigial_documentation/judgment/e-series/e19-design-SEED.md`. A design seed proposing to
  measure where defects ("residuals") reappear as in-run review depth thins — the
  "residual-reappearance lever" — as a follow-on to e18, explicitly unratified ("SEED, not a
  commission") and dependent on the now-superseded `acts.ruling` vocabulary (rulings
  107/108/110/114). It was never elevated and the live engine design has since been written
  independently in `design/ORCH-LEDGER-LOGIC-MARRIAGE.md`. Vestigial: an abandoned proposal from
  the predecessor experiment series. Provenance: machine-consensus (classifier + adversarial
  skeptic) + maintainer-approved 2026-07-12.

- **`judgment/engine/engine-assurance-arguments-SEED.md`** →
  `vestigial_documentation/judgment/engine/engine-assurance-arguments-SEED.md`. A SEED document
  arguing the conservative-abstraction and assurance-case structure for the deductive engine,
  produced by the pre-Fable-withdrawal panel process. It was never elevated to a commission and
  the engine's actual live design (the ledger-marriage doc) was authored independently
  afterward; the seed's arguments are not incorporated by reference anywhere current. Vestigial:
  superseded, unelevated design exploration. Provenance: machine-consensus (classifier +
  adversarial skeptic) + maintainer-approved 2026-07-12.

- **`judgment/engine/engine-increment-0-unification.md`** →
  `vestigial_documentation/judgment/engine/engine-increment-0-unification.md`. A unification
  pass reconciling four divergent panel designs' registries/vocabularies/verdict terms before
  any content increment was built. It addressed a coordination problem internal to the now-closed
  panel process; the project's actual unified design is `design/ORCH-LEDGER-LOGIC-MARRIAGE.md`,
  authored independently and current as of 2026-07-12. Vestigial: superseded coordination
  document from the predecessor panel process. Provenance: machine-consensus (classifier +
  adversarial skeptic) + maintainer-approved 2026-07-12.

- **`judgment/engine/engine-panel/DECISION-BRIEF-deny-surface.md`** →
  `vestigial_documentation/judgment/engine/engine-panel/DECISION-BRIEF-deny-surface.md`. A
  maintainer decision brief posing three options for whether the deductive engine may ever deny
  a write, whose chosen option (B) was ratified as `acts.ruling` id 42 and whose full resulting
  text is already carried forward verbatim inside the current, live
  `design/ORCH-LEDGER-LOGIC-MARRIAGE.md`. Because the operative content is already inlined at its
  point of use, this brief itself is provenance/history rather than something a current reader
  must consult. Vestigial, with a caveat: it is the one file in this set with a live inbound
  citation (as a provenance pointer, `design/ORCH-LEDGER-LOGIC-MARRIAGE.md:277`, citing the
  *pre-migration* `consults/engine-panel/DECISION-BRIEF-deny-surface.md` path from the
  `epistemic-operator` source repo, not a live in-repo link) — that citation is a frozen
  point-in-time provenance record of what was read at authoring time and is left verbatim per
  ADR-0017's Exceptions, rather than retro-edited to the new path. Provenance: machine-consensus
  (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

- **`judgment/engine/engine-panel/critic-completeness.md`** →
  `vestigial_documentation/judgment/engine/engine-panel/critic-completeness.md`. One of four
  "critic" passes in a July-7 nine-agent panel that designed a speculative, never-built
  "deductive judgment engine" (obligations/staleness/authorization derivation over the
  ledger+acts stream) — not the ASP/SQL judge engine that actually shipped and that
  `ORCH-CAPABILITIES.md`/`./judge` document. It is cited only by sibling SEED/increment documents
  inside the same `judgment/` archive, never by any current entry doc, spec, or capability item;
  the feature it designs was never picked up past a draft increment-0 that the panel's own
  record says is still awaiting a maintainer scan. Vestigial: history of an abandoned/stalled
  design track. Provenance: machine-consensus (classifier + adversarial skeptic) +
  maintainer-approved 2026-07-12.

- **`judgment/engine/engine-panel/design-adversarial.md`** →
  `vestigial_documentation/judgment/engine/engine-panel/design-adversarial.md`. The
  "adversarial-self-application lens" design for the same speculative
  deductive-judgment-engine panel — a threat catalog (L1-L10) for how a trust-bearing engine
  could lie, with countermeasures. Rich and well-argued but scoped to a feature track that
  stalled at draft increment-0 and is never invoked by `ORCH-CAPABILITIES.md`, `ORCH-HANDOFF.md`,
  or any current `design/` spec. Vestigial: unbuilt-design archive. Provenance: machine-consensus
  (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

- **`judgment/engine/engine-panel/refute-evaluation.md`** →
  `vestigial_documentation/judgment/engine/engine-panel/refute-evaluation.md`. Adversarial
  rebuttal of `design-evaluation.md` for the same panel. Internal-only citation network within
  `judgment/`; not reachable from any live entry doc. Vestigial. Provenance: machine-consensus
  (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

## `research/` — 25 files, all VESTIGIAL

### `research/foundational-map/` — 5 files

- **`research/foundational-map/00-synthesis.md`** →
  `vestigial_documentation/research/foundational-map/00-synthesis.md`. The integrated synthesis
  of a 2026-06-27 literature survey comparing this project's design ideas against two
  predecessor repos (chocofarm, omega) before the current consolidation — capability-registry
  and provenance-ledger design sketches that seeded (but are not) the shipped kernel/engine.
  `ORCH-DIRCLASS.md` self-declares the whole `research/` corpus, foundational-map included, as
  excludable literature survey; the one foundational-map file still cited by a live spec is a
  different numbered file in the same directory. Vestigial: pre-consolidation research whose
  conclusions landed elsewhere. Provenance: machine-consensus (classifier + adversarial skeptic)
  + maintainer-approved 2026-07-12.

- **`research/foundational-map/03-choco-typing-classification-logic.md`** →
  `vestigial_documentation/research/foundational-map/03-choco-typing-classification-logic.md`.
  A 2026-06-27 structured-output report mapping chocofarm's ADR-0000/ADR-0008 typing and
  classification-logic discipline as the philosophical seed for autoharn's LOGIC layer. It fed
  directly into `00-synthesis.md` and the harness's actual type-driven-design ADR (now
  `law/adr/0000`, which CLAUDE.md cites directly instead). Vestigial: it is pre-consolidation
  evidence-gathering whose conclusions have already been absorbed into the live law and design
  corpus; nothing in `ORCH-CAPABILITIES.md`, the verbs, or entry docs points back to it, and
  `ORCH-DIRCLASS.md` already classifies the whole `research/` corpus as excludable without
  breaking the harness. Provenance: machine-consensus (classifier + adversarial skeptic) +
  maintainer-approved 2026-07-12.

- **`research/foundational-map/09-cross-memories-and-resource-facts.md`** →
  `vestigial_documentation/research/foundational-map/09-cross-memories-and-resource-facts.md`.
  Research summary contrasting Claude memory directories against a queryable resource registry,
  motivating the harness's "Pillar 1: pull not push" design principle. Vestigial: a design-seed
  document for a decision already made and built (or shelved) elsewhere; no CAPABILITIES item,
  verb, or entry doc cites it, and it postdates nothing else in the corpus that would need it
  kept live. Provenance: machine-consensus (classifier + adversarial skeptic) +
  maintainer-approved 2026-07-12.

- **`research/foundational-map/10-choco-tool-venv-surface.md`** →
  `vestigial_documentation/research/foundational-map/10-choco-tool-venv-surface.md`.
  Hand-authored (not workflow-generated) inventory of chocofarm's tool/venv/capability surface —
  Z3/OR-Tools venv paths and a grep use-site census — gathered as Pillar-1 seed material after
  the automated reader twice failed. Vestigial: a one-time environment snapshot from 2026-06-27
  whose facts (if still needed) belong in a live venv/tooling reference, not this frozen research
  report; nothing in the current operating surface cites it. Provenance: machine-consensus
  (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

- **`research/foundational-map/README.md`** →
  `vestigial_documentation/research/foundational-map/README.md`. The directory README for
  foundational-map/, indexing the ten evidence reports (00-synthesis plus 01-10) as "the
  evidence base for the harness design." Vestigial: it is a navigation aid for a set of reports
  that are themselves superseded design-seed material with no current inbound references from
  `CAPABILITIES.md`, the verbs, or entry docs; once the reports it indexes move to
  `vestigial_documentation/`, the index has nothing left to point at operationally. Provenance:
  machine-consensus (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

### `research/logic-fair-trials/` — 4 files

- **`research/logic-fair-trials/07-paraconsistent.md`** →
  `vestigial_documentation/research/logic-fair-trials/07-paraconsistent.md`. First-pass
  fair-trial writeup on paraconsistent/many-valued logic, kept as Witness material behind an
  explicit supersession notice. Vestigial: the corrected frame lives in
  `obligations-formalisms-survey/`, the condensed verdict is already restated in
  `research/LOGIC-COVERAGE-STATUS.md`, and no operational doc points here. Provenance:
  machine-consensus (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

- **`research/logic-fair-trials/08-description-logic.md`** →
  `vestigial_documentation/research/logic-fair-trials/08-description-logic.md`. Fair-trial
  writeup on description logic/OWL applicability to autoharn's ledger. Vestigial for the same
  reason as its siblings: directory-level supersession notice, no inbound references from live
  docs, and its conclusion already condensed elsewhere. Provenance: machine-consensus
  (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

- **`research/logic-fair-trials/10-relevance-substructural.md`** →
  `vestigial_documentation/research/logic-fair-trials/10-relevance-substructural.md`. Fair-trial
  writeup on relevance/substructural logics. Vestigial: part of the superseded fair-trials pass,
  unreferenced by any entry doc, its status already summarized in
  `research/LOGIC-COVERAGE-STATUS.md`'s "investigated, not built" section. Provenance:
  machine-consensus (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

- **`research/logic-fair-trials/11-smt-fol.md`** →
  `vestigial_documentation/research/logic-fair-trials/11-smt-fol.md`. Fair-trial writeup on
  SMT/classical FOL (Z3/cvc5). Vestigial: superseded pass, and the SMT conclusion that actually
  landed (z3 unsat-core lane) is already stated as current production fact in
  `research/LOGIC-COVERAGE-STATUS.md` rather than here. Provenance: machine-consensus (classifier
  + adversarial skeptic) + maintainer-approved 2026-07-12.

### `research/logic-investigation/` — 8 files

- **`research/logic-investigation/02-prolog-clp.md`** →
  `vestigial_documentation/research/logic-investigation/02-prolog-clp.md`. First-pass
  Prolog/CLP(FD) primer and applicability writeup from the retracted investigation. Vestigial
  for the same reason as its siblings in this directory: doubly superseded, unreferenced by
  current entry docs, retained purely as historical Witness. Provenance: machine-consensus
  (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

- **`research/logic-investigation/03-asp.md`** →
  `vestigial_documentation/research/logic-investigation/03-asp.md`. A primer on Answer Set
  Programming (clingo/DLV) written as family 03 of a 13-family logic-applicability survey
  conducted 2026-06-27. Vestigial because the survey it belongs to is explicitly marked
  superseded by its own README (replaced by the fair-trials re-run) and by the later
  `research/LOGIC-COVERAGE-STATUS.md`, which flags the whole directory "retracted"; ASP's live
  operational treatment is in `engine/lp/` and `engine/docs/JUDGE-READING.md`, not here.
  Provenance: machine-consensus (classifier + adversarial skeptic) + maintainer-approved
  2026-07-12.

- **`research/logic-investigation/04-defeasible-argumentation.md`** →
  `vestigial_documentation/research/logic-investigation/04-defeasible-argumentation.md`. Family
  04 of the 13-family survey, covering defeasible reasoning and formal argumentation. Vestigial:
  the directory is self-declared superseded, and the live coverage map
  (`research/LOGIC-COVERAGE-STATUS.md`) already carries this family's settled verdict
  (argumentation rejected for the kernel) independent of this file. Provenance: machine-consensus
  (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

- **`research/logic-investigation/10-relevance-substructural.md`** →
  `vestigial_documentation/research/logic-investigation/10-relevance-substructural.md`. Family
  10 of the survey, on relevance and substructural logics. Vestigial: superseded per directory
  README along with the rest of the corpus; not cited by any current spec or entry doc.
  Provenance: machine-consensus (classifier + adversarial skeptic) + maintainer-approved
  2026-07-12.

- **`research/logic-investigation/12-abductive-ilp.md`** →
  `vestigial_documentation/research/logic-investigation/12-abductive-ilp.md`. Family 12 of the
  survey, on abductive reasoning and Inductive Logic Programming. Vestigial: superseded per
  directory README; the live coverage map already tracks this family's status (and its own
  drift) without needing this file kept live. Provenance: machine-consensus (classifier +
  adversarial skeptic) + maintainer-approved 2026-07-12.

- **`research/logic-investigation/13-probabilistic-srl.md`** →
  `vestigial_documentation/research/logic-investigation/13-probabilistic-srl.md`. Family 13 of
  the survey, on probabilistic logic and statistical-relational AI (ProbLog/PSL/MLN). Vestigial:
  superseded per directory README; its rejected verdict is already carried forward in
  `research/LOGIC-COVERAGE-STATUS.md`. Provenance: machine-consensus (classifier + adversarial
  skeptic) + maintainer-approved 2026-07-12.

- **`research/logic-investigation/14-probabilistic-programming-bayesian.md`** →
  `vestigial_documentation/research/logic-investigation/14-probabilistic-programming-bayesian.md`.
  Family 14, a hand-commissioned complement on probabilistic programming and formal Bayesian
  frameworks. Vestigial: part of the same directory the README marks superseded/corrected by the
  fair-trials re-run; not cited by any live spec. Provenance: machine-consensus (classifier +
  adversarial skeptic) + maintainer-approved 2026-07-12.

- **`research/logic-investigation/A-software-landscape.md`** →
  `vestigial_documentation/research/logic-investigation/A-software-landscape.md`. A unified
  engine catalog and install plan (versions/licenses as of June 2026) consolidating all 13
  family sections. Vestigial: superseded along with the rest of the directory per its README,
  and a dated software-version snapshot ages out regardless. Provenance: machine-consensus
  (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

### `research/nlp-logic-interface/` — 5 files

- **`research/nlp-logic-interface/BUILD-PLAN.md`** →
  `vestigial_documentation/research/nlp-logic-interface/BUILD-PLAN.md`. A phased build plan
  (2026-07-02) for an NLP-fact-to-logic-engine hook, listing six gated experiments (E-1..E-6)
  against a `hook_trial.py` driver and `contra.finding` adjudication surface. Vestigial because
  the subsystem it plans to extend (`contra_detect`/`contra_asp`/`fde_z3`/`extract.py`
  FactBundle pipeline) is not present in this repo, the plan is uncited by any current spec or
  the fresher `LOGIC-COVERAGE-STATUS.md` status map, and nothing beyond historical
  migration-manifest rename records points to it — the thread was explored and not carried
  forward. Provenance: machine-consensus (classifier + adversarial skeptic) + maintainer-approved
  2026-07-12.

- **`research/nlp-logic-interface/DESIGN.md`** →
  `vestigial_documentation/research/nlp-logic-interface/DESIGN.md`. The executive design doc
  (2026-07-02) for an NLP-to-logic interface, assigning formalisms to purpose-driven functions
  atop a described "typed spine" (FactBundle/Claim/LogicBackend). Vestigial because the codebase
  it designs against does not exist in this repo, no current spec or the fresher
  `LOGIC-COVERAGE-STATUS.md` cites it, and it self-declares as a one-time commissioned
  deliverable rather than a living spec — exploratory research whose subsystem was never built
  here. Provenance: machine-consensus (classifier + adversarial skeptic) + maintainer-approved
  2026-07-12.

- **`research/nlp-logic-interface/INTERFACE.md`** →
  `vestigial_documentation/research/nlp-logic-interface/INTERFACE.md`. The typed-contracts
  companion to `DESIGN.md`, specifying interfaces for the same unbuilt NLP-to-logic pipeline.
  Vestigial for the same reason as its sibling: it documents contracts for code that is not in
  this repo, is uncited by any current spec, CAPABILITIES, or the fresher coverage-status map,
  and represents a commissioned exploration that did not land. Provenance: machine-consensus
  (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

- **`research/nlp-logic-interface/INVENTORY.md`** →
  `vestigial_documentation/research/nlp-logic-interface/INVENTORY.md`. A file:line-cited factual
  inventory (2026-07-02) of NLP-fact/logic-layer touchpoints (`extract.py`, `contra_detect.py`),
  read-only and non-prescriptive by its own charter. Vestigial because the exact files and line
  numbers it cites do not exist in the current tree, it is uncited by any live spec or the
  fresher coverage map, and an inventory of vanished code has no forward operational value
  beyond history. Provenance: machine-consensus (classifier + adversarial skeptic) +
  maintainer-approved 2026-07-12.

- **`research/nlp-logic-interface/SYNTHESIS-INPUTS.md`** →
  `vestigial_documentation/research/nlp-logic-interface/SYNTHESIS-INPUTS.md`. The raw
  inputs/commissioning brief that `DESIGN.md` was synthesized against. Vestigial because its
  sole downstream consumer (`DESIGN.md`) is itself vestigial (unbuilt, uncited subsystem), making
  this an input to a shelved commission rather than standing reference material. Provenance:
  machine-consensus (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

### `research/obligations-formalisms-survey/formal-systems/` — 3 files

The obligation-type labels below (PROV, TRACE, CLASS, CONSIST, STRUCT, COHERE) name entries in
this project's own obligation taxonomy — what each formal system in this survey was being
assessed against — defined in
[`research/obligations-formalisms-survey/01-obligation-taxonomy.md`](research/obligations-formalisms-survey/01-obligation-taxonomy.md).

- **`research/obligations-formalisms-survey/formal-systems/01-datalog.md`** →
  `vestigial_documentation/research/obligations-formalisms-survey/formal-systems/01-datalog.md`.
  A ~90-line primer on Datalog/deductive-database theory (least-fixpoint semantics,
  stratification, PROV/TRACE relevance) with a worked example and tooling notes, part of the
  27-formalism obligations survey. Vestigial because its load-bearing conclusion (Datalog = the
  normal form behind PROV/TRACE, already running as ASP's stratified fragment) is already
  condensed into `LOGIC-COVERAGE-STATUS.md`'s covered-set list; nothing in the current build
  cites this file by path, and it is explicitly agent-reasoned/not experimentally settled
  exploratory material from a single June workflow run. Provenance: machine-consensus (classifier
  + adversarial skeptic) + maintainer-approved 2026-07-12.

- **`research/obligations-formalisms-survey/formal-systems/05-sat-cp.md`** →
  `vestigial_documentation/research/obligations-formalisms-survey/formal-systems/05-sat-cp.md`.
  Chapter on SAT/CP finite-domain solving as an exhaustiveness-proof engine for
  CLASS/CONSIST/STRUCT/TRACE obligations, with a worked example. Vestigial: exploratory survey
  material, uncited by path anywhere in current specs, its assignment already summarized in
  `LOGIC-COVERAGE-STATUS.md`'s "optimization-as-logic" entry. Provenance: machine-consensus
  (classifier + adversarial skeptic) + maintainer-approved 2026-07-12.

- **`research/obligations-formalisms-survey/formal-systems/10-description-logic.md`** →
  `vestigial_documentation/research/obligations-formalisms-survey/formal-systems/10-description-logic.md`.
  Chapter on Description Logic/OWL for CLASS/COHERE classification-and-coherence obligations via
  TBox reasoning. Vestigial: the one apparent cross-reference to "description-logic" in a
  current design doc actually points to a different, older survey (logic-fair-trials), not this
  file; this chapter itself is uncited, and the project's current status doc already keeps DL in
  "investigated, not built." Provenance: machine-consensus (classifier + adversarial skeptic) +
  maintainer-approved 2026-07-12.

## Totals

47 entries above (1 root + 8 `design/` + 1 `instruments/` + 12 `judgment/` + 25 `research/`),
matching the maintainer-adjudicated upheld list exactly — no file added, dropped, or
re-verdicted from what ledger decision id 251 ratified.
