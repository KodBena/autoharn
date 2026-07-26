<!-- doc-attest-exempt: mined mechanical output -- regenerated wholesale by re-running
the mining pass over attestations/doc-legibility-attestations.jsonl (one Sonnet pass,
maintainer-directed 2026-07-26, ledger row records the commission); polishing this file by
hand would be overwritten by the next regeneration. Removal condition: promoted into a
ratified recipe or superseded by a typed-findings mechanism. -->

<!-- CONSUMER (named, per the named-consumer test): the A-side PRE-REVIEW of the ADR-0017
A:B:C loop. Contract, maintainer-directed 2026-07-26 (amended same day: fix, don't just
find): before dispatching any fresh-context B round, the dispatching A runs (or delegates
to a cheap model) one explicit pass over the ranked classes below AND APPLIES THE FIXES --
a find-only pass would be waste; these classes are the easiest to find and the cheapest to
repair. Everything after the pre-review is the unchanged A:B:C story. B itself stays fresh
and is NEVER shown this file (it would anchor the sweep).

TRACKING (the maintainer's efficiency-comparison consumer, named at the same ruling): each
pre-review appends one JSON line to attestations/pre-review-log.jsonl (created on first
use; same append-only convention as the attestation ledger beside it):
  {"doc": <path>, "content_sha256_before": ..., "content_sha256_after": ...,
   "model": <who swept>, "fixed": {"<class-name>": <count>, ...}, "ts": <ISO-8601>}
Efficiency then reads as a join, no new machinery: B's subsequent round-1 findings-per-
class on pre-reviewed docs (already recorded in doc-legibility-attestations.jsonl, keyed
by doc+hash) versus the corpus baseline percentages in this file -- if the pre-review
earns its keep, the top classes' share collapses in post-pre-review B rounds. -->

# Common ADR-0017 defect classes (mined from the attestation corpus)

**Purpose.** This is a pre-review checklist for anyone doing an ADR-0017 fresh-context legibility pass (the "B" role in the A:B:C loop, or any solo reviewer) on a maintainer-facing document in this repository. It was mined empirically from every finding recorded in `attestations/doc-legibility-attestations.jsonl` — the append-only ledger of ADR-0017 fresh-context legibility reviews. It does not import ADR-0017's own vocabulary as a starting taxonomy; the clusters below emerged from what the findings' `quote`/`repair` text actually says, and are cross-referenced to ADR-0017's rules only after the fact, for anyone who wants the underlying law (`law/adr/0017-the-zero-context-reader.md`).

**Method note (read before trusting the counts).** Each of 1683 findings was auto-clustered by matching phrases in its `repair` text (e.g. "gloss", "define", "resolving link", "add a verb"), then each bucket was hand-sampled (30-60 specimens per bucket) to confirm the cluster holds together and to pull verbatim quotes. This is a keyword-based sort, not an exhaustive per-finding hand read — treat the counts as good-confidence estimates, not exact tallies. A residual bucket of ~412 findings did not match any keyword rule cleanly; hand-sampling that bucket found the same classes below recurring (mostly more dangling-referent and sentence-fragment specimens the keyword pass missed, plus a handful of smaller shapes noted in the residual section) rather than a hidden large class.

---

## Ranked defect classes

### 1. Dangling referent — coined term, code, or "the X" cited without ever being defined (≈818 findings, ~49%)

**Definition.** A term of art, project-internal code (`s22`, `F53`, `C13`), coinage (`the pilot`, `world`, `the commission`), or demonstrative noun phrase (`the loop`, `the decomposition`, `this session`) is used as if the reader already knows it, with no in-document gloss and no link to where it's defined. This is ADR-0017 Rule 1(b) / Rule 2(a) — the single largest failure mode in the corpus by a wide margin.

**Specimens:**
- `bootstrap/templates/APPARATUS.md:81` — quote: *"ADR-0017's A:B:C fresh-context audit loop"* — repair: *"Spell out what A:B:C means inline (define A/B/C's roles) rather than assuming the reader already knows the notation."*
- `bootstrap/templates/APPARATUS.md:91` — quote: *"nothing in a freshly scaffolded world reads one"* — repair: *"Replace project-specific jargon 'world' with the already-established 'project' (or gloss it) since it is used bare in this document."*
- `design/ORCH-HARNESS-FAILURE-LEDGER.md:6` — quote: *"the commission (used ~10 times, never defined)"* — repair: *"Define 'the commission' explicitly at first use as the tracker row that opened this work."*

**How to spot it cheaply:** grep for backticked tokens, ALLCAPS/mixed-case short codes, and bare demonstratives (`the pilot|the commission|this session|the loop|the decomposition`) — for each hit, check whether the *same document* states what it is or links to where it's stated. Reading rule: for every proper noun or jargon token in the doc, ask "if I saw only this sentence, would I know what this refers to?"

### 2. Bare path/citation — a document or artifact is named but not rendered as a resolving link (≈139 findings, ~8%)

**Definition.** A repository artifact (BACKLOG.md, an ADR, a script) is cited as a bare filename, a prose-styled path, or a code span, instead of a markdown link the reader can actually click/resolve. This is ADR-0017 Rule 2(b) verbatim.

**Specimens:**
- `design/ABC-AUDIT-LOOP-RECIPE.md:135` — quote: *"(BACKLOG \"Two ratifications (maintainer, 2026-07-11 evening)\", ratification 1's sub-question 2: ...)"* — repair: *"Format the bare 'BACKLOG' citation as `BACKLOG.md` (or a resolvable link), consistent with the sibling reference two lines later and ADR-0017's own citation convention."*
- `design/CONTEMPORANEITY-AUDIT.md:143` — quote: *"dated per ADR-0005 Rule 8"* — repair: *"link ADR-0005 to its file"*
- `HANDOFF.md:103` — quote: *"its citing BACKLOG.md entry in the statement text"* — repair: *"Backtick or link BACKLOG.md, matching sibling references."*

**How to spot it cheaply:** `grep -n '\bBACKLOG\b\|ADR-[0-9]\{4\}\|\.md\b' <file>` then check each hit is inside `[label](path)` markdown link syntax; a bare hit outside brackets is a candidate. Reading rule: for every named document/ADR/script mentioned, try to click it — if you can't, it's a gesture, not a reference (ADR-0017's own phrase).

### 3. Sentence fragment — noun-phrase or headword chain standing in for a sentence (≈143 findings, ~8.5%)

**Definition.** A "sentence" (often a bolded lead-in, a bullet, or an opening line) has no subject-verb structure — a noun phrase, a colon-list with nothing governing it, a dangling participle, or a missing copula. This is ADR-0017 Rule 1(a) — "a noun phrase is not a paragraph."

**Specimens:**
- `HANDOFF.md:81` — quote: *"The migrated inventory (as of 2026-07-11): 9 open items"* — repair: *"Add a governing verb; the colon-list has no main verb (Rule 1a)."*
- `design/GPG-TRUST-LAYER.md:136` — quote: *"One keypair, generated once"* — repair: *"rewrite as a full sentence"*
- `user-guide/USER-ACCESS-CONTROL-GUIDE.md:837` — quote: *"**Entitlement evaluated fresh, at act time, from the same rows the write itself is about to join.**"* — repair: *"Missing linking verb; rewrite as 'Entitlement is evaluated fresh, at act time...'"*

**How to spot it cheaply:** grep for bolded lead-ins (`^\*\*[^*]+\*\*` or `- \*\*...`) followed immediately by a colon or nothing, and check each ends in a finite verb. Reading rule: read the first line under every heading and every bolded bullet lead-in out loud — does it have a subject doing a verb, or is it a headword pile?

### 4. Ungrounded structure — a table, list, or code block dropped with no lead-in prose (≈44 findings, ~2.6%)

**Definition.** A structure (table, bullet list, code fence, section) appears directly under a heading with no sentence telling the reader what it is, what its rows/items are, or why they're looking at it. ADR-0017 Rule 1(c), the "figure-caption rule."

**Specimens:**
- `design/WORK-STATUS-OFFERING.md:71` — quote: *"### One-command adoption\n\n```sh"* — repair: *"Add a lead-in sentence before the code fence (figure-caption rule, Rule 1c)."*
- `bootstrap/templates/APPARATUS.md:63` — quote: *"## The eleven mechanisms and their defaults"* — repair: *"Add one grounding sentence before the table naming what its columns are."*
- `design/MAINTAINER-DECISION-BRIEF.md:311` — quote: *"## Related"* — repair: *"Add a grounding sentence before the bare bullet list, per Rule 1(c)'s figure-caption requirement."*

**How to spot it cheaply:** grep for a heading line (`^#+ `) or table/fence marker (`^\||^```) immediately followed (next non-blank line) by another table/list/fence marker, with no prose sentence in between. Reading rule: before every table/list/code block, is there at least one sentence saying what it is and why it's here?

### 5. Positional cross-reference into a mutable document (≈27 findings, ~1.6%)

**Definition.** A citation points at a document by position ("item 18", "bullet 3", "preamble point 10") rather than by name/anchor, into a document that gets rewritten wholesale — so the reference dangles the next time that document changes. ADR-0017 Rule 2(c); frozen point-in-time records are explicitly exempt.

**Specimens:**
- `design/CONTEMPORANEITY-AUDIT.md:25` — quote: *"Permit-to-work (item 18) fixed the first."* — repair: *"name and link the host document (CAPABILITIES.md item 18)"*
- `OPERATING-CARD.md:112` — quote: *"(LAZY mode; preamble point 10)"* — repair: *"name the artifact instead of a bare position into an unnamed document"*
- `CAPABILITIES.md:14` — quote: *"the four operator verbs' current shape (`led`/`judge`/`pickup`/the scaffold)"* — repair: *"reword to state the count was accurate as of that 2026-07-10 pass and point at item 25 for the current canonical list"*

**How to spot it cheaply:** `grep -n -i 'item [0-9]\+\|point [0-9]\+\|bullet [0-9]\+\|the [a-z]* bullet'` — for each hit, check the cited document is either named+linked or is a genuinely frozen record (dated, never rewritten). Reading rule: could this citation break if someone edited the target document tomorrow without touching this one? If yes, it needs a name, not a position.

### 6. Uncited claim — "maintainer ruling"/"the commission"/"this incident" asserted with no traceable ledger row or link (≈25 findings, ~1.5%)

**Definition.** A claim of provenance or authority ("maintainer ruling", "the incident", "this ruling") is stated with no ledger row number, commit hash, or link a reader could use to verify it happened. Distinct from class 1 in that the term itself may be plain English — the defect is the missing *evidence trail*, not an undefined coinage.

**Specimens:**
- `ORCH-HANDOFF.md:28` — quote: *"maintainer ruling"* — repair: *"cite tracker ledger row 137 so the claim carries its witness"*
- `design/USER-RECIPES-FAQ.md:961` — quote: *"the same evidence bar the estimates discipline's own lapse just met"* — repair: *"Cite the incident (rows 1695/1696) instead of assuming unstated history."*
- `design/USER-RETROSPECTIVE-RECIPE.md:329` — quote: *"the maintainer's own invariant, stated twice at commissioning (tracker item `cost-estimation-retro`)"* — repair: *"Give the reader a concrete resolution path (e.g. the `./led show <id>` live-lookup convention this repo's sibling specs already use)."*

**How to spot it cheaply:** grep for `maintainer ruling|the commission|this incident|the ruling` and check each is followed (same sentence or same paragraph) by a row number, commit hash, or link. Reading rule: for every claim of "X was decided/happened", ask "how would I check that?" — if the answer is "trust me", it's a hit.

### 7. Stale or inaccurate reference — the citation resolves, but points to the wrong place or misstates its target (≈15 findings, ~0.9%)

**Definition.** Unlike class 6, the reference *is* traceable — but chasing it lands somewhere that doesn't say what the citing text claims (wrong section number, wrong ADR section, a quote attributed to a passage that doesn't contain it).

**Specimens:**
- `design/ABC-AUDIT-LOOP-RECIPE.md:120` — quote: *"ADR-0017 names the price... (its 'fresh-context audit loop' section)"* — repair: *"The quoted cost figure is from ADR-0017's Consequences section, not its fresh-context-audit-loop section; retarget the parenthetical citation to the section that actually contains the quote."*
- `design/GPG-TRUST-LAYER-FAQ.md:105` — quote: *"This tripped up this very FAQ's own witness pass (§5 below)"* — repair: *"Wrong section number; the colon-stripping content actually lives in §8, not §5."*
- `OPERATING-CARD.md:196` — quote: *'"reviewer independence"'* — repair: *"drop the quotation marks around 'reviewer independence' — it is a paraphrase, not a verbatim quote from the cited document, per a live grep of that file finding no such string"*

**How to spot it cheaply:** no reliable grep shape — this requires actually opening every cited section/quote and confirming the content matches. Reading rule: pick every explicit "§N", "Table N", or quotation-marked string in the doc and verify by opening the target that it says what's claimed.

### 8. Factual self-inconsistency — a stated number, count, or label contradicts the document's (or corpus's) own facts (≈12 findings, ~0.7%)

**Definition.** A count, quantity, or descriptive label is simply wrong against ground truth available in the same document or an easily-checked sibling (e.g., "six verbs" when the same page's own heading enumerates seven; "items 39-43" when only 39-42 exist).

**Specimens:**
- `USER-GUIDE.md:347` — quote: *"the operator-facing reference for the six verbs"* — repair: *"Change 'six' to 'seven' to match §4's own heading."*
- `ORCH-CAPABILITIES.md:46` — quote: *"added items 39-43"* — repair: *"only items 39-42 exist; count corrected"*
- `USER-GUIDE.md:138` — quote: *"**What landed where:** everything §3a's table lists..."* — repair: *"§3a's 'what landed where' is prose, not a table — replace 'table' with an accurate referent."*

**How to spot it cheaply:** grep for number words near enumerable nouns (`\b(six|seven|eight|nine|ten|[0-9]+) (verbs|items|mechanisms|rows|checks)\b`) and count the actual enumeration referenced. Reading rule: whenever a document states a count of anything, count the actual list/table/heading it's describing.

### 9. Slash-soup / telegraphic connective run (≈3 findings, ~0.2% — small but named explicitly in ADR-0017's own Context)

**Definition.** A run of proper nouns, slashes, em-dashes, and arrows stands in for the sentence that should state the claim connecting them — ADR-0017's own named specimen shape (the B-method/Event-B passage in the safety-critical-logging BRIEF).

**Specimens:**
- `design/ORCH-WORKTREE-LEDGERING.md:198` — quote: *"tools/branch_attribution.py is an observer/reporting tool with nothing to refuse, not a gate"* — repair: *"Replace the slash-soup with 'an observer-grade reporting tool'."*
- `design/ORCH-SPEC-RESOURCE-REGISTRY.md:132` — quote: *"trivial orderings need nothing; pure precedence at scale → tsort or a ten-line ASP enumeration; arithmetic or resources → Z3 / OR-Tools, ..."* — repair: *"give each escalation rung its own verb instead of an arrow"*

**How to spot it cheaply:** grep for lines with 2+ occurrences of `/`, `—`, or `→` and no lowercase conjunction/finite verb between them. Reading rule: read any line with more than one slash or arrow — is there a clause anywhere in it, or just nouns joined by punctuation?

### 10. Jargon-first opening — the document's first words are apparatus/jargon, not plain orientation (≈14 findings, ~0.8%)

**Definition.** The opening paragraph leads with metadata blocks (Audience/Status/Provenance), coined vocabulary, or a quoted artifact before stating in plain words what the document is, who it's for, and what question it answers. ADR-0017 Rule 1(d).

**Specimens:**
- `design/ORCH-SPEC-DECOMPOSITION-POLICY.md:4` — quote: *"Audience: orchestrator (design spec; implementation stages are Sonnet-executable per §8). Status: Fable-authored 2026-07-12..."* — repair: *"Open with one plain declarative sentence stating what the document is and does before the audience/status/tracker metadata, mirroring the sibling ORCH-SPEC-RESOURCE-REGISTRY.md's opening."*
- `bootstrap/QUICKSTART.md:3` — quote: *"Executed, not proofread (mandate §6). Every command below has been run from a fresh clone..."* — repair: *"Open with a plain-words statement of the document's purpose and audience before naming 'mandate §6'; gloss or link the mandate."*
- `law/adr/0009-performance-investigation-discipline.md:26` — quote: *"autoharn's perf/equivalence surface is a governance-kernel/deductive-engine one (the ASP-vs-SQL differential, kernel-lineage timing, the research ledger), not an ML hot path."* — repair: *"add a plain-words framing sentence before the jargon-dense opening"*

**How to spot it cheaply:** grep the first 10 lines of any touched document for `Audience:|Status:|Provenance:|Tracker:` — if one of these appears before any plain sentence stating what the doc is/who it's for, it's a hit. Reading rule: read only the first paragraph — can you say in one sentence what this document is and whether it concerns you, before chasing any link or acronym?

### Non-class: adjudicated-not-a-defect (≈31 findings, excluded from ranking)

These are recorded findings that a maintainer/reviewer subsequently ruled were **not** actual violations — protected point-in-time text (ADR-0005 Rule 8), house-convention exemptions, or corpus-wide adjudications. They inflate the raw finding count but are not a defect class; a pre-reviewer should recognize this shape too: if the flagged text sits inside a dated Amendment block, a frozen commission quote, or is explicitly the corpus's own quoted specimen, check ADR-0017's Exceptions section before treating it as a fresh defect.

---

## Residual / unclustered specimens (one line each, genuinely singleton or too rare to cluster)

- `PANEL-GXP-SURFACE-KICKSTART-2026-07-26.md:30` — a promised inline expansion ("ALCOA+ is expanded where §2 uses it") never actually lands in the target section — an *unfulfilled forward promise*, distinct from a stale reference because nothing was ever there.
- `law/adr/history/0008-chocofarm-classification-substrate.md:20` — a banner claims verbatim extraction while the body was actually paraphrased/restructured — a *provenance-claim contradicted by the artifact itself*.
- `ORCH-HANDOFF.md:93` — broken parallel structure across a three-way enumeration ("already-covered, genuinely-new, or divergent-surface-it") where the third arm doesn't parse like its siblings.
- `ORCH-CAPABILITIES.md:1261` — a literal self-contradiction in a heading ("scheduled but not scheduled").
- `HANDOFF.md:91` — a running tally that appears to double-count a closed item against a stated total of open items.
- `design/USER-RECIPES-FAQ.md:153` — a repair pointing at the wrong evidence block entirely (round-1 fix cited an unrelated preflight check).
- `design/FABLE-PRINCIPAL-IDENTITY-SPEC.md:53` — a citation ("amendment C13") that only exists in a sibling document, not the one making the claim.

---

## Totals

- **Total findings counted:** 1683
- **Total records read:** 418 (every line of `attestations/doc-legibility-attestations.jsonl`)
- **Findings I could not classify with confidence:** the automated keyword pass left ~412 findings in an unsorted residual bucket; hand-sampling ~90 of those confirmed the same classes above recur there (chiefly more dangling-referent and sentence-fragment specimens plus the residual singletons listed above) rather than revealing a large hidden class, but that bucket was not hand-coded finding-by-finding, so its internal split across classes 1-10 above is an estimate, not an exact count.
