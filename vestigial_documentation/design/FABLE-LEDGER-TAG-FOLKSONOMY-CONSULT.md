# Ledger tag folksonomy — fresh-context consult, banked verbatim

<!-- doc-attest-exempt: banked consult verbatim; point-in-time record, not living prose -->

Provenance: fresh-context Fable instance, 2026-07-18, commissioned to consider
SKEPTICALLY the orchestrator's closed-vocabulary-only position on a ledger tag column,
after the maintainer's challenge (near-verbatim): "Is there a structural reason we
haven't a tag column in the ledger already? ... it would seem like an easy 'last
resort' for annotating units of information ... 'doesn't look like what we currently
do' is not a good argument." The consultant read the schema, ADR-0000/0002/0008, s25,
and the engine's refs-parsing layer, and was mandated to steelman the free-tag column,
state its own recommendation, and name its falsifiers. Report verbatim below; the
maintainer's disposition ("a nice factorization") and the implementing work item are
on the ledger.

---

**Ground I read**: kernel/lineage/s15-schema.sql in full; ADR-0000 in full (including the 2026-07-02 Rule 2(a) closure-statement amendment); ADR-0002 in full; ADR-0008 in full; s25-commission-kind.sql's preamble (the one prior kind-vocabulary extension of the prose kind); the `led` template's `--refs` documentation; the clingo layer's actual consumption of `refs` (engine/lp/preamble_ordering.lp); GLOSSARY.md headings and the defeasibility note. Two facts from that reading control most of the analysis, so I state them first.

**Fact A — the ledger is append-only (s15-schema.sql lines 251-261), so a tag COLUMN cannot retro-tag.** UPDATE is refused for every role. A tag column only carries what the writer knew at insert time. But the stated motivation — hazards, lessons, recurring gotchas — is knowledge that is characteristically recognized *after* the rows it lives in were written, often sessions later ("we now see rows 212, 480, 913 are the same gotcha"). A column structurally cannot serve the use-case that motivates it.

**Fact B — the system already quantifies over an open free-text field, defensibly.** `refs` is not opaque prose the engine ignores: preamble_ordering.lp parses the `row:<id>` convention out of it (`row_refs_row/2`) and marks a present-but-unparseable refs as `ob_undecidable(..., refs_unparsed)` — parse what you can, mark the rest undecidable, never conclude from what you couldn't read. That is a witnessed, in-production pattern for honest quantification over an open vocabulary.

---

### (1) The strongest case FOR a free tag column

Argued as if I believe it:

Lore capture is a perishable act. The moment you notice "this is the third time a worktree base was stale" is the only moment the observation is cheap; any ceremony between the noticing and the recording — even a scripted, class-ratified delta — converts recording into a task, and tasks get deferred, and deferred lore lands in prose (MEMORY.md, retrospectives, commit messages) where nothing can query it. That is precisely the status quo being complained about: this project's institutional knowledge currently lives in a memory index of ~25 hand-curated bullets and in design/ archives that CLAUDE.md itself declares "history unless a current spec cites them." The complaint is real and the cause is friction.

The vocabulary-discovery argument is also real and is the project's own stated posture: the method-harvesting memory says outright "we may not know what we're looking for." A closed vocabulary is exactly the wrong instrument during the phase where the categories are unknown — you cannot enumerate a universe you haven't discovered. ADR-0008's own Exceptions section blesses the "deliberately-imprecise tag" as "an explicit refusal to classify until the case firms up, which is the discipline applied to itself." Folksonomies converging without central control is a well-attested empirical phenomenon; drift (hazard/hazards) is a cleanup cost, not a correctness cost, so long as nothing load-bearing consumes the tags — and nothing would.

And the law does not actually forbid it. ADR-0000 governs the disposition of *defects*; the closure-statement amendment governs *foreclosure claims* — claims that a class is made unrepresentable. A diagnostic annotation claims nothing and forecloses nothing. ADR-0008 explicitly scopes itself to "classifications that propagate to consumers" and says "not all classifications need ceremony." The project already maintains a recognized diagnostic tier (the action-stream memory: token accounting is "permanently diagnostic-grade"). Tags are that tier. Reading closed-enum discipline onto a non-load-bearing scratch channel is the over-typing weaponization ADR-0000's own Revisit #2 warns about: "a bespoke type for every trivial value." A type earns its place by foreclosing a class; there is no bug-class at stake in a lore tag.

### (2) The strongest case AGAINST a free tag column

Argued likewise:

The column form is refuted by Fact A before any philosophy starts: append-only means insert-time-only tagging, and the lore use-case is retrospective. This is not a matter of taste — the schema's strongest guarantee makes the column unable to do its one job. (Input class: a gotcha recognized in session N about a row written in session N-3 -> observed: no legal write can attach the tag to that row -> expected: the annotation mechanism must attach knowledge to old rows.)

Beyond that: this ledger's authority comes from every cell being either typed or explicitly downgraded. The s15 preamble states a house law in passing — "the 'no edge without a consumer' law" — and a free tag column with no view, no parse, no differential is a dead seam: it *looks* configured but nothing honors it, which is ADR-0002 Rule 4's lying-signature shape in the schema register. Worse, an unconsumed tag column will be read by future auditors as authoritative structure (ADR-0008 Context: a classification "silently propagates ... through every downstream consumer that later reads the classification as authoritative"). And once anything — a pickup query, a routing heuristic — starts consuming tags, the diagnostic fig leaf is gone and you have an untyped enum feeding decisions, exactly what every CHECK constraint in this schema exists to refuse. The one-way ratchet is the danger: diagnostic channels get promoted to load-bearing by usage, never by ratification.

Finally, the ceremony-cost premise is overstated: since the 2026-07-09 class-ratification ruling, an additive vocabulary delta needs *no maintainer question at all* — s25 added 'commission' to the kind vocabulary under exactly that path, scratch-witnessed, differential AGREE, no per-delta ask. The closed path is cheaper than the FOR case assumes.

### (3) Where the prior position's reasoning was weakest

- **The refs argument is self-refuting as stated.** It claimed simultaneously that free text cannot be honestly quantified over by the clingo layer AND that `refs` (free text) is the adequate escape hatch. Fact B shows the engine already parses and quantifies over `refs` with an undecidable-mark discipline. Either open text is quantifiable-with-honesty (so the closure argument against tags fails) or it isn't (so refs is a fig leaf). Both halves cannot stand. Input class: semi-structured token in an open text field -> observed: parsed into `row_refs_row/2`, unparsed marked `refs_unparsed` undecidable -> expected under the prior position: impossible to quantify honestly. The expectation is falsified by the repo's own engine.
- **It argued against the column form but the append-only refutation (Fact A) is the decisive one, and it never made it** — instead it reached for constitutional arguments (ADR-0000 closure statements) that don't actually bind non-load-bearing annotation. The closure-statement amendment quantifies over *defect-class foreclosure claims*; citing it against a diagnostic channel is meeting the letter of "closed universes everywhere" while missing that the law's universe is refusals and guarantees.
- **Its remedy (closed tag table + join table, new tags only by lineage delta) quietly concedes the column debate** — a join table appended to later IS retrospective annotation, i.e., tags-as-rows — but then re-imports the friction problem at the vocabulary layer without acknowledging the discovery-phase objection or ADR-0008's deliberately-imprecise-tag exception.
- **"An open vocabulary drifts" was treated as terminal.** Drift in a diagnostic channel is a visible, cheap, fixable condition (a distinct-tags view makes hazard/hazards adjacency loud; supersession — which this ledger has as a first-class edge — is a built-in folksonomy-cleanup mechanism). Drift is terminal only where a gate consumes the vocabulary.

### (4) Recommendation

**No new column — and no closed tag table yet either. Tags as ordinary ledger rows, usable today with zero schema change, plus one derived view as the consumer, plus promotion-on-recurrence.**

Concretely:

1. **Now, zero delta:** annotate by inserting a row — `kind=note` (already in the CHECK vocabulary), `refs row:<id>` pointing at the annotated row (the documented "bare reference uses refs" convention s25 itself leaned on), and a statement convention `tag:<token> — <prose>` mirroring the existing `row:<id>` idiom. This is retro-capable (Fact A satisfied), cross-session (refs has no same-session trigger, unlike enacts/amends/answers), supersedable (a wrong tag is defeated the way everything else here is), and attributed/timestamped/hash-chained for free. A `led tag <row-id> <token> <prose>` convenience verb is an operator-surface addition writing through existing channels — no kernel act.
2. **The consumer, so the seam isn't dead:** one derived view (or clingo-side EDB predicate in the refs pattern) enumerating observed tag tokens with counts and target rows — parse `tag:<token>`, mark malformed ones visibly, exactly the `refs_unparsed` discipline. This makes drift loud (ADR-0002) instead of forbidden.
3. **Promotion on recurrence, which is ADR-0011 Rule 2 verbatim:** when a tag token recurs and something wants to *consume* it mechanically, that recurrence converts to a mechanism — mint it into closed vocabulary (or a real typed structure, as s22 did when work items turned out to have genuine shape) via the class-ratified additive path, and supersede-or-migrate the folk rows. The free tier is the discovery instrument; the closed tier is where proven vocabulary retires to. The maintainer's ratification bandwidth is spent on neither.
4. **One bright line, stated at minting time:** tag rows are diagnostic-grade. The day a gate, verdict, or routing decision reads a tag token, that token must first be promoted. This is the same tier boundary the project already runs for token accounting.

Tradeoffs, plainly: tag rows are noisier than a column (one insert per tagged row — `one_row_per_insert` forbids batching); querying is parse-plus-join rather than a column equality; drift persists until a harvest pass consolidates; and the whole thing depends on the `led` verb making capture genuinely one line, because if capture stays awkward the knowledge stays in prose and nothing was gained.

### (5) What would falsify this

- **Capture friction persists**: if, three weeks in, tag rows are rare while lessons keep landing in MEMORY.md/prose, the rows-plus-convention design failed the very complaint that motivated the question — revisit toward something even lower-friction, and at that point a nullable free `tags text[]` column for *insert-time* tagging (alongside, not replacing, the retro rows) becomes defensible despite the aesthetics.
- **A consumer sneaks in**: if any load-bearing surface is found reading tag tokens without promotion, the diagnostic-tier framing was wishful and the prior position's closed-vocabulary instinct was right earlier than I credit.
- **The parse view drowns**: if malformed/near-duplicate tokens dominate the distinct-tags view and harvest passes don't converge the vocabulary, the folksonomy-converges premise fails for this population of writers (LLM sessions, not human crowds — the empirical base for folksonomy convergence is human, and that extrapolation is the least-supported step in my argument).
- **Retro-tagging turns out rare in practice**: if nearly all tagging happens at write time, Fact A's weight drops and the column-vs-rows question reopens on ergonomics alone.

Key files: /home/bork/w/vdc/1/autoharn/kernel/lineage/s15-schema.sql (append-only triggers, lines 251-261; refs convention comment), /home/bork/w/vdc/1/autoharn/engine/lp/preamble_ordering.lp (the refs_unparsed discipline, lines 146-156 and 203-221), /home/bork/w/vdc/1/autoharn/kernel/lineage/s25-commission-kind.sql (the witnessed cost of an additive vocabulary delta), /home/bork/w/vdc/1/autoharn/law/adr/0008-classification-discipline.md (the deliberately-imprecise-tag exception and the "propagates to consumers" scope limit).
