# Catalog genericity critique — banked verbatim, 2026-07-19

<!-- doc-attest-exempt: banked critique verbatim; preserved as delivered, fidelity IS the value -->

**Provenance:** fresh-context Sonnet critic, commissioned per ledger row 1718 (maintainer
verbatim there). The critic received the catalog, the spec's admission criterion, and the
genericity criterion ONLY — not the maintainer's suspicion of which entries are bespoke.
Delivered as the agent's final message; banked byte-verbatim below the rule.

---

## Genericity review — durable-decisions catalog

Ranked most-severe first (worst genericity failure to best).

---

**6. `setup-surface-is-maintained` — BESPOKE**

> "The setup surface (tools/setup_tui + the contracts it drives: new-project.sh, teardown-world.sh, boundary config/ports, deployment.json's key contract, the led verbs the screens call) is a MAINTAINED surface. Any change to a driven contract triggers, in the SAME changing work item, a TUI conformance re-check and repair if the contract moved."

This rule is not addressed to an adopter at all — it is addressed to whoever maintains autoharn's *own* setup tooling. A stranger who deploys a world to govern an unrelated project will never touch `tools/setup_tui`, `new-project.sh`, or `teardown-world.sh`; those are autoharn's own build artifacts, not something their project produces. As written this is a memo from the maintainer to autoharn's core contributors ("the changer pays, not the next operator" about *this* surface), smuggled into a catalog whose stated audience is "a complete stranger adopting this open-source harness for their own project." Zero adaptation to a stranger's world was performed. Cut candidate #1.

---

**1. `makespan-scheduling-by-mandate` — BESPOKE / GENERALIZABLE**

> "Logistics/makespan scheduling (tools/makespan-scheduler/, CP-SAT via OR-Tools) is used BY MANDATE... The mandate is a REVIEW OBLIGATION, not a bare scheduling preference (autoharn-panel's own form of the mandate, its CLAUDE.md points 2-3)... the decomposition-review mechanism makes an undischarged countersign a BLOCKER."

The operative content isn't self-contained: it tells the reader to look at how a *sibling deployment* ("autoharn-panel's own form") solved the problem, and asserts a "decomposition-review mechanism" (`hooks/pretooluse_change_gate.py`) exists that enforces the blocker — a mechanism the catalog gives no indication a fresh world actually contains. The rule reads as reportage on another project's practice rather than a portable instruction a stranger can execute. The underlying idea (constraint-scheduling for multi-item work; cosigned close for high-stakes decomposition) is sound and generalizable; the text as delivered is not.

*Rewrite:* "For any commission spanning 3+ dependent work items, sequence them with a constraint-based scheduler rather than ad hoc ordering, and require a high-stakes task's decomposition and close to be cosigned by a principal distinct from the one who did the work — treat an undischarged cosign as a hard block on further edits, never backloggable debt."

---

**9. `runs-are-strictly-linear` — GENERALIZABLE**

> "A run M > N means run N's world is dust and settled... Never propose delta-apply/refresh against an existing world; a delta reaches reality only by entering the next world's birth chain."

This states a real, portable versioning discipline (never mutate a past, already-evidenced artifact; changes flow forward only), but it is delivered entirely in undefined harness jargon — "run," "world," "birth chain" — with no gloss in the rule text itself. It is generic *content* wrapped in bespoke *vocabulary*; a stranger's CLAUDE.md gets this fragment verbatim and must already know what a "world" and a "birth chain" are (definitions live in GLOSSARY.md, not cited here).

*Rewrite:* "Once a deployment's evidence is recorded, treat it as immutable history — never patch, refresh, or apply deltas to it after the fact; a needed change is realized only in the next deployment you create."

---

**7. `doc-currency-at-the-seam` — GENERALIZABLE**

> "Every merge that adds or changes operator-facing behavior carries its documentation pass (affected user-guide pages, an orchlog.d note for a capability, README enumerations) in the SAME work item..."

The core rule ("docs travel with the change, in the same unit of work, or a named deferral") is fully portable. It is snagged by one clause — "an orchlog.d note for a capability" — a project-specific artifact convention named without explanation; a stranger has no `orchlog.d` and no idea what note it wants.

*Rewrite:* "Every merge that changes user-facing behavior includes its documentation update (or a named, tracked deferral with a reason) in the same unit of work; a merge silent on docs for a behavior change is itself a defect."

---

**5. `obligate-amplification-caution` — GENERALIZABLE**

> "Never write a kernel `obligate` row without first reading led.tmpl's own obligate-header note and revoke-refusal warning: `review_gap` over-catch is retroactive (no temporal bound) and an obliged actor's OWN dispositions become new debt (self-amplifying)."

The caution content (a specific footgun: retroactive over-catch, self-amplifying debt against the obliged actor) is precisely stated and does transfer to any world running the shared `led` kernel — but the rule outsources its own substance ("read led.tmpl's own... note") rather than stating the warning inline, and assumes the reader already knows what an `obligate` row and `review_gap` are. Workable for an adopter of *this specific harness's kernel*, but it reads as an internal cross-reference rather than free-standing guidance.

*Rewrite:* "Before writing any obligation row into the ledger, know that over-catch review triggers are retroactive with no time bound, and that an obliged actor's own later actions can count as new debt against themselves — always discharge review obligations under a different principal than the one who is obliged."

---

**8. `concurrent-builders-need-isolation` — GENERIC (borderline)**

> "Overlapping-surface commissions get worktree isolation or serial dispatch, never a shared checkout -- a concurrent sibling's uncommitted hunk in a shared working tree can be swept into another builder's commit by an ordinary `git add` of a declared path."

Pure git-concurrency hazard, fully explained in its own text ("commissions"/"builder" jargon is transparent from context — task, agent doing the task). Any team running concurrent agents/contributors against shared checkouts hits this. Portable as written.

---

**2. `drift-backstops` — GENERIC**

> "...for anything that goes quietly stale: name the authority/dependent pair, derive both sides mechanically, compare with a comparator that quantifies over the class, refuse loud (refresh or declare), backstop the backstop with a seen-red proof and a fixture-census registration."

A genuine methodology, stated as a repeatable procedure (five moves), independent of what the "quietly stale" pair actually is. It points at a specific doc (`user-guide/USER-RECIPES-FAQ.md`) for elaboration but the rule itself is self-sufficient and the shipped harness carries that FAQ into every world. Portable.

---

**3. `single-branch-authoring` — GENERIC**

> "Content is authored on the single working branch ONLY; a cut/release branch is a pure derivation (projection), never a place an edit originates."

Ordinary git-branching discipline, no project-specific nouns at all. Directly usable by any adopter.

---

**4. `tags-are-serious-business` — GENERIC**

> "Public main stays continuously up to date via routinely pushed, UNTAGGED cuts. Tagging is serious business -- a deliberate release act, never done between feature sets."

Same — plain release-engineering discipline, no entanglement.

---

**10. `decomposition-to-unit-of-independent-resumption` — GENERIC**

> "Decompose a commission into ledgered work items to the UNIT OF INDEPENDENT RESUMPTION... Judge granularity by one question: could a fresh session pick up this slug alone and know what to build and how to tell it's done?"

The best entry in the catalog for this criterion: a crisp, self-contained heuristic, immediately testable by any team doing ticket/work-item decomposition, no unexplained jargon load-bearing in the rule itself.

---

### The three unwired candidates

**(a) "review briefs are UNANCHORED, never suspect-listed"** — as gisted, this is a generic anti-anchoring-bias principle for how you write a review prompt (don't hand the reviewer a pre-identified suspect list, or their finding becomes confirmation rather than discovery). Nothing about the gist ties it to this project's tooling. **Exclusion looks wrong under genericity alone** — it reads at least as portable as several wired entries (better than #1, #6), and arguably more broadly applicable than #7/#5.

**(b) "a detect fingerprints behavior/catalog shape, never a named object"** — also gists as a portable engineering principle (detect by structural/behavioral signature, not by hardcoded identity) applicable to any codebase's drift/census-style checks. Narrower in obvious applicability than (a) (a rule about how to write detectors specifically), but nothing bespoke visible in the gist. **Exclusion is defensible but not clearly required by genericity** — it's a fine engineering guideline, just narrower-audience than the others.

**(c) "every builder task gets a fresh-context review, kernel-touching mandatory"** — the general policy (routine review for all delegated work, mandatory independent review for high-risk/critical-path changes) is a standard, portable practice (the "kernel" tier maps to any project's notion of a sensitive core). As gisted it leans on this project's own tiering ("kernel-touching") but that's a one-word substitution away from generic ("core/critical-path-touching mandatory"). **Exclusion is questionable** — this is one of the more directly reusable candidates of the three, arguably more clearly generic than the wired #1 or #6.

None of the three unwired gists show an obvious disqualifying bespoke defect; if anything the selection **passed over some of the more portable candidates while keeping the two most locally-entangled wired entries (#1, #6)**.

---

### Closing judgment

**Overall health:** mixed, not poor. Of 10 wired entries, 4 are cleanly GENERIC (#2, #3, #4, #10), 4 are GENERALIZABLE with identifiable entangling clauses (#1, #5, #7, #9), and 1 is BESPOKE outright (#6). No entry is unsalvageable — even #1 and #6 have a real generic core buried in them — but the catalog was evidently distilled by lightly editing prior-art text (this repo's ledger rows and autoharn-panel's CLAUDE.md) rather than performing the generalization the admission-criterion writeup implies. The self-reference chain in #1 ("autoharn-panel's own form... its CLAUDE.md points 2-3") and #6's flat address to autoharn's own maintainers are the tell: the mining step preserved *citations* faithfully (as instructed) but did not always translate the *rule* out of first-person-project voice into stranger-portable voice.

**Cut from an initial stranger-facing catalog:** #6 (`setup-surface-is-maintained`) outright — it has no purchase for an adopter who isn't developing autoharn's own tooling; keep it as an internal contributor note, not a hydration option. #1 needs a rewrite pass (drop the sibling-deployment citation and the presumption of an existing enforcement hook) before it belongs in front of a stranger, or should be held back pending that rewrite.

**Conspicuously missing, given what the harness itself is for:** the "claims carry witnesses" taxonomy (WITNESSED / REFUSED-AS-EXPECTED / UNEXERCISED, no umbrella claims) that sits in this project's own CLAUDE.md ORCHESTRATION section is arguably the single most generic, most load-bearing durable decision the harness embodies — an audit/governance harness's evidentiary discipline for what counts as a substantiated claim — and it isn't in the catalog at all. It would need zero translation for a stranger's world (it's already written project-agnostically) and is a more obvious candidate for "small-ish curated catalog... born of witnessed painful experience" than several of the entries that did make the cut.
