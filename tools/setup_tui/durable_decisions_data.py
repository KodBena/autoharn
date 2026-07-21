#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-21T22:56:29Z
#   last-change: 2026-07-21T22:56:29Z
#   contributors: 43f77bff/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/durable_decisions_data.py -- the DATA half of the durable-decisions catalog,
split out of tools/setup_tui/durable_decisions.py under law/adr/0012's 2026-07-22 Amendment (P10
-- "data is not code"), phase 1 of design/FABLE-SETUP-TUI-FIELD-STRATEGY.md Track 2.2. This
module is the declared data artifact P10 calls for: typed literals, ZERO functions, ZERO logic --
a writing/content edit to a decision's `rule`/`why`/`hydrates`/`claude_md` prose lands here and
ONLY here, never mixed with a review of durable_decisions.py's CLAUDE.md-compilation logic.

Content, not structure: `RAW_CATALOG` carries every field durable_decisions.DurableDecision needs
(slug/rule/why/hydrates/claude_md), in the SAME order the original CATALOG list held them --
order is load-bearing here (spec §3's numbered curation history, kept below as per-entry
comments) even though CATALOG itself is consulted by slug, not position.
durable_decisions.py constructs the typed `CATALOG: list[DurableDecision]` from this list at
import time (one line, pure wiring -- never a parse, never a runtime file read); the
DurableDecision dataclass DEFINITION stays in durable_decisions.py per this build's own
commission (dataclass definitions are logic-side contracts, not data).

The per-entry curation comments (numbered 1-13, citing the genericity critique row 1722 and each
entry's own mining/rewrite history) are MOVED HERE VERBATIM, unlike the CATALOG-level "Initial
catalog" preamble (the editorial-methodology overview), which stays in durable_decisions.py next
to the CATALOG construction line -- the preamble is commentary ABOUT the split (why this shape,
how it was curated as a whole), the per-entry comments are commentary ABOUT one entry's content,
so they travel with that entry into the data artifact.

Chosen form (P10's own "choose deliberately" instruction): a data-only Python module, not JSON/
TOML -- same reasoning as feature_facts_data.py's own docstring: every field cites ledger rows,
spec paths, and code paths BY NAME, which a JSON editor lets drift silently (a mistyped key is a
silent no-op) where a Python dict-literal key typo is a TypeError at import time (P8's
fail-loud-signature bar). Zero imports, zero functions -- pure literal data, importable standalone,
no dependency on durable_decisions.py (no import-order fragility). durable_decisions.py is this
module's only intended importer.

Content is UNCHANGED from durable_decisions.py's prior CATALOG literal -- this is a pure
relocation (program-text moved, not rewritten); see the commit message for how this was verified
(an AST-level extraction of each field's original source segment plus its preceding curation
comment, not hand-retyped).

Lazy imports are banned (CLAUDE.md, 2026-07-02) -- moot here (zero imports), stated for the
convention's sake.
"""
from __future__ import annotations

RAW_CATALOG: list[dict[str, str]] = [
    # 1. Maintainer-named anchor (row 1714). Substance corrected per row 1716 (the panel's actual
    # cosigned-decomposition mandate, read from its CLAUDE.md points 2-3 + RESOURCES row
    # id=1178), then REWRITTEN into stranger-portable voice per the genericity critique (row
    # 1722, design/SONNET-CATALOG-GENERICITY-CRITIQUE-2026-07-19.md, entry #1: BESPOKE/
    # GENERALIZABLE -- the prior text cited a sibling deployment by name and a hook a fresh world
    # does not necessarily contain). The critique's own suggested rewrite dropped the panel's
    # "resource-conflict, or quota constraints" trigger breadth (RESOURCES row id=1178's mandated
    # tier fires on dependency, precedence, resource-conflict, OR quota constraints -- not
    # dependency alone); restored here in generic voice ("or resource conflicts") rather than
    # silently narrowing the mandate's scope. `why` citations kept exactly as banked -- the
    # citations are the evidence and stay local; only the rule/claude_md voice changed.
    {
        "slug": "makespan-scheduling-by-mandate",
        "rule": "For any commission spanning 3+ work items with dependencies, precedence "
             "constraints, or resource conflicts, sequence them with a constraint-based "
             "scheduler rather than ad hoc ordering. Require a high-stakes task's decomposition "
             "and close to be cosigned by a principal distinct from the one who did the work -- "
             "treat an undischarged cosign as a hard block on further edits, never backloggable "
             "debt.",
        "why": "maintainer directive 2026-07-14 (user-guide/USER-RECIPES-FAQ.md 'Workflow "
            "patterns'); ledger row 1714 (this catalog's own commission) and row 1716 (the "
            "maintainer's correction: 'it's mandate is a robust specification (well, softly so) "
            "in autoharn-panel, in that it requires cosigned decomposition of the task'); the "
            "panel's actual mandate text, read live and read-only from "
            "/home/bork/w/vdc/1/experience/autoharn-panel/CLAUDE.md points 2-3 ('A mandated-"
            "tier task carries a review obligation by convention: its work item's close is "
            "countersigned by a distinct principal ... hooks/pretooluse_change_gate.py's "
            "decomposition_review mechanism makes this a BLOCKER, not backloggable debt') and "
            "its RESOURCES table row for makespan-scheduler (ledger row id=1178 there, tier "
            "text: 'mandated: driving execution of three or more claimed/claimable work items "
            "under dependency, precedence, resource-conflict, or quota constraints'); rule text "
            "rewritten per row 1722's genericity critique, entry #1.",
        "hydrates": "Durable decision adopted at world birth (makespan-scheduling-by-mandate, catalog "
            "tools/setup_tui/durable_decisions.py, why: ledger rows 1714/1716/1722 + "
            "autoharn-panel/CLAUDE.md points 2-3 and its RESOURCES table row id=1178): for any "
            "commission spanning 3+ work items with dependencies, precedence constraints, or "
            "resource conflicts, sequence them with a constraint-based scheduler rather than ad "
            "hoc ordering; require a high-stakes task's decomposition and close to be cosigned "
            "by a principal distinct from the one who did the work, treating an undischarged "
            "cosign as a hard block on further edits, never backloggable debt.",
        "claude_md": "- **Constraint-scheduled, cosigned decomposition** -- for any commission spanning "
            "3+ work items with dependencies, precedence constraints, or resource conflicts, "
            "sequence them with a constraint-based scheduler (this harness ships one: "
            "`tools/makespan-scheduler/`, CP-SAT via OR-Tools) rather than ad hoc ordering. "
            "Require a high-stakes task's decomposition and close to be cosigned by a principal "
            "distinct from the one who did the work -- treat an undischarged cosign as a hard "
            "block on further edits, never backloggable debt. Full treatment: "
            "user-guide/USER-RECIPES-FAQ.md 'Workflow patterns', "
            "design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md.",
    },
    # 2. Maintainer-named anchor (row 1714).
    {
        "slug": "drift-backstops",
        "rule": "The orchestrator is softly obligated to follow the FAQ's drift-backstop method "
             "(user-guide/USER-RECIPES-FAQ.md, 'Drift backstops') for anything that goes "
             "quietly stale: name the authority/dependent pair, derive both sides mechanically, "
             "compare with a comparator that quantifies over the class, refuse loud (refresh "
             "or declare), backstop the backstop with a seen-red proof and a fixture-census "
             "registration.",
        "why": "the FAQ section's own fourteen-instance evidence base (user-guide/"
            "USER-RECIPES-FAQ.md 'Drift backstops', citing ADR-0011's Context: 'a design "
            "document that quietly goes stale while the code it describes moves on, a "
            "duplicated fact whose two copies drift apart one edit at a time').",
        "hydrates": "Durable decision adopted at world birth (drift-backstops, catalog "
            "tools/setup_tui/durable_decisions.py, why: user-guide/USER-RECIPES-FAQ.md 'Drift "
            "backstops', fourteen-instance evidence base): the orchestrator is softly "
            "obligated to follow the FAQ's five-move drift-backstop method for anything that "
            "goes quietly stale.",
        "claude_md": "- **Drift backstops (soft obligation)** -- for anything that goes quietly stale "
            "(docs from code, a hash function from a table's columns, a config from the "
            "mechanisms it configures), follow the five-move method in "
            "user-guide/USER-RECIPES-FAQ.md 'Drift backstops': name the pair, derive both "
            "sides mechanically, compare with a comparator quantifying over the class, refuse "
            "loud (refresh or declare), backstop the backstop.",
    },
    # 3. Mined, this repo's ledger: single-branch authoring.
    {
        "slug": "single-branch-authoring",
        "rule": "Content is authored on the single working branch ONLY; a cut/release branch is a "
             "pure derivation (projection), never a place an edit originates. An edit made "
             "inside a cut is the defect to make unrepresentable, not a convenience.",
        "why": "ledger row 1033 (this repo, maintainer ruling 2026-07-15): 'ONE branch, full "
            "stop. Worktrees fine; branches are the transaction-paradigm violation witnessed "
            "today (v1.1 cut-only README/USER-CONFIGURATION edits authored in the cut worktree, "
            "never backported to next, silently re-deleted by the v1.1.2 cut from next).'",
        "hydrates": "Durable decision adopted at world birth (single-branch-authoring, catalog "
            "tools/setup_tui/durable_decisions.py, why: ledger row 1033): content is authored "
            "on the single working branch ONLY; a cut/release branch is a pure derivation, "
            "never a place an edit originates -- witnessed specimen: v1.1 cut-only edits "
            "authored in a cut worktree were silently re-deleted by the next cut.",
        "claude_md": "- **Single-branch authoring** -- content is authored on the single working branch "
            "ONLY; a cut/release branch is a pure derivation (projection), never a place an "
            "edit originates (ledger row 1033: cut-only edits were silently re-deleted by the "
            "next cut).",
    },
    # 4. Mined, this repo's ledger: tagging discipline.
    {
        "slug": "tags-are-serious-business",
        "rule": "Public main stays continuously up to date via routinely pushed, UNTAGGED cuts. "
             "Tagging is serious business -- a deliberate release act, never done between "
             "feature sets.",
        "why": "ledger row 1027 (this repo, maintainer ruling 2026-07-15): 'public origin/main "
            "stays continuously up-to-date -- cut commits pushed routinely, UNTAGGED. Tagging "
            "is serious business, a deliberate release act, never done between feature sets.'",
        "hydrates": "Durable decision adopted at world birth (tags-are-serious-business, catalog "
            "tools/setup_tui/durable_decisions.py, why: ledger row 1027): public main stays "
            "continuously up to date via routinely pushed, UNTAGGED cuts; tagging is a "
            "deliberate release act, never done between feature sets.",
        "claude_md": "- **Tags are serious business** -- push public main often, UNTAGGED; a tag is a "
            "deliberate release act, never done between feature sets (ledger row 1027).",
    },
    # 5. Mined, this repo's ledger: the obligate-amplification footgun (already cited by this
    # spec's own §3 as the reason v1 writes no kernel obligate rows -- promoted from the prior
    # PROPOSED shape into the real catalog once the maintainer widened its scope, then REWRITTEN
    # into stranger-portable voice per the genericity critique (row 1722, entry #5:
    # GENERALIZABLE -- the prior text outsourced its own substance to "led.tmpl's own... note"
    # instead of stating the warning inline). `why` kept exactly as banked.
    {
        "slug": "obligate-amplification-caution",
        "rule": "Before writing any obligation row into the ledger, know that over-catch review "
             "triggers are retroactive with no time bound, and that an obliged actor's own "
             "later actions can count as new debt against themselves. Always discharge review "
             "obligations under a different principal than the one who is obliged.",
        "why": "ledger row 1640 (this repo, 2026-07-18, autoharn-panel world/older lineage): the "
            "obligate footgun's third witnessed occurrence -- 1225 pre-existing rows flagged as "
            "debt, then 1225->1228 amplification when the obliged actor's own dispositions "
            "counted as new debt; rule text rewritten per row 1722's genericity critique, "
            "entry #5.",
        "hydrates": "Durable decision adopted at world birth (obligate-amplification-caution, catalog "
            "tools/setup_tui/durable_decisions.py, why: ledger rows 1640/1722): before writing "
            "any obligation row into the ledger, know that over-catch review triggers are "
            "retroactive with no time bound, and that an obliged actor's own later actions can "
            "count as new debt against themselves -- always discharge review obligations under "
            "a different principal than the one who is obliged.",
        "claude_md": "- **Obligation-trigger caution** -- before writing any obligation row into the "
            "ledger, know that over-catch review triggers are retroactive with no time bound, "
            "and that an obliged actor's own later actions can count as new debt against "
            "themselves. Always discharge review obligations under a different principal than "
            "the one who is obliged (ledger row 1640).",
    },
    # 6. Mined, this repo's ledger: the setup surface is a maintained surface.
    #
    # CUT per the genericity critique (row 1722, design/SONNET-CATALOG-GENERICITY-CRITIQUE-
    # 2026-07-19.md, entry #6: BESPOKE): this rule is addressed to autoharn's own core
    # contributors, not to an adopter deploying a world to govern an unrelated project -- a
    # stranger never touches tools/setup_tui, new-project.sh, or teardown-world.sh, so hydrating
    # it into their world's CLAUDE.md would be a memo with no purchase for its reader. It stays
    # an internal contributor rule (ledger row 1700), not a hydration option; the catalog's
    # admission criterion (a witnessed painful specimen) was met, but genericity was not, and the
    # critique's verdict is adopted wholesale (ledger row 1722). See git history for the retired
    # entry's full prior text if it is ever wanted back for an internal-only surface.
    #
    # 7. Mined, this repo's ledger: doc currency at the seam. REWRITTEN per the genericity
    # critique (row 1722, entry #7: GENERALIZABLE -- the prior text's "orchlog.d note for a
    # capability" clause named a project-specific artifact with no gloss). `why` kept as banked.
    {
        "slug": "doc-currency-at-the-seam",
        "rule": "Every merge that changes user-facing behavior includes its documentation update "
             "(or a named, tracked deferral with a reason) in the same unit of work. A merge "
             "silent on docs for a behavior change is itself a defect.",
        "why": "ledger row 1699 (this repo, maintainer-directed 2026-07-19): 'we need durable "
            "decisions so to reduce the vigilance burden of remembering after new features have "
            "been added' -- precedent: the 2026-07-18 Block D merge landed undocumented and "
            "needed a dedicated catch-up pass (rows 1652-1661 vs 1667); rule text rewritten per "
            "row 1722's genericity critique, entry #7.",
        "hydrates": "Durable decision adopted at world birth (doc-currency-at-the-seam, catalog "
            "tools/setup_tui/durable_decisions.py, why: ledger rows 1699/1722): every merge "
            "that changes user-facing behavior includes its documentation update, or a named, "
            "tracked deferral with a reason, in the same unit of work; a merge silent on docs "
            "for a behavior change is itself a defect.",
        "claude_md": "- **Doc currency at the seam** -- every merge that changes user-facing behavior "
            "includes its documentation update (or a named, tracked deferral with a reason) in "
            "the same unit of work. A merge silent on docs for a behavior change is itself a "
            "defect (ledger row 1699).",
    },
    # 8. Mined, this repo's ledger: concurrent builders need isolation.
    {
        "slug": "concurrent-builders-need-isolation",
        "rule": "Overlapping-surface commissions get worktree isolation or serial dispatch, never "
             "a shared checkout -- a concurrent sibling's uncommitted hunk in a shared working "
             "tree can be swept into another builder's commit by an ordinary `git add` of a "
             "declared path.",
        "why": "ledger row 1502 (this repo, s45 adversarial review adjudication): commit 94f5b7a "
            "bundled a fixture_census registry row for defeat-pipeline before those files "
            "existed, making the census gate RED on a clean checkout -- cause: 'shared-checkout "
            "concurrency, not builder invention: the pipeline builder's uncommitted hunk in the "
            "SHARED gates/fixture_census.py was swept by s45's git add of its own declared "
            "path.'",
        "hydrates": "Durable decision adopted at world birth (concurrent-builders-need-isolation, "
            "catalog tools/setup_tui/durable_decisions.py, why: ledger row 1502): "
            "overlapping-surface commissions get worktree isolation or serial dispatch, never a "
            "shared checkout -- witnessed scope-bleed: a concurrent builder's uncommitted hunk "
            "in a shared file was swept into another builder's commit.",
        "claude_md": "- **Concurrent builders need isolation** -- overlapping-surface commissions get "
            "worktree isolation or serial dispatch, never a shared checkout (ledger row 1502: "
            "a concurrent builder's uncommitted hunk in a shared file was swept into another "
            "builder's commit, making a census gate falsely RED).",
    },
    # 9. Mined, this repo's ledger/CLAUDE.md: runs are strictly linear. REWRITTEN per the
    # genericity critique (row 1722, entry #9: GENERALIZABLE -- generic content, bespoke
    # vocabulary: "run"/"world"/"birth chain" used with no inline gloss). `why` kept as banked.
    {
        "slug": "runs-are-strictly-linear",
        "rule": "Once a deployment's evidence is recorded, treat it as immutable history -- never "
             "patch, refresh, or apply deltas to it after the fact. A needed change is realized "
             "only in the next deployment you create.",
        "why": "maintainer ruling 2026-07-11 (this repo's own CLAUDE.md, ORCHESTRATION section): "
            "the apply-to-existing-world clause and bootstrap/apply-delta.sh's typed-"
            "confirmation ceremony were retired after being witnessed producing cargo-cult "
            "sysadmin work; the run-2 world was itself broken at birth by an unscripted "
            "scaffold-to-/tmp + hand-mv gap; rule text rewritten per row 1722's genericity "
            "critique, entry #9.",
        "hydrates": "Durable decision adopted at world birth (runs-are-strictly-linear, catalog "
            "tools/setup_tui/durable_decisions.py, why: maintainer ruling 2026-07-11 + ledger "
            "row 1722): once a deployment's evidence is recorded, treat it as immutable history "
            "-- never patch, refresh, or apply deltas to it after the fact; a needed change is "
            "realized only in the next deployment you create.",
        "claude_md": "- **Deployments are immutable history once recorded** -- once a deployment's "
            "evidence is recorded, treat it as immutable history: never patch, refresh, or "
            "apply deltas to it after the fact. A needed change is realized only in the next "
            "deployment you create (maintainer ruling 2026-07-11).",
    },
    # 10. Mined, autoharn-panel LIVE deployment CLAUDE.md point 1: decomposition granularity.
    {
        "slug": "decomposition-to-unit-of-independent-resumption",
        "rule": "Decompose a commission into ledgered work items to the UNIT OF INDEPENDENT "
             "RESUMPTION -- not below it and not above it, and no numeric rule (a fixed item- "
             "or file-count target is cargo-cultable and wrong as often as right). Judge "
             "granularity by one question: could a fresh session pick up this slug alone and "
             "know what to build and how to tell it's done?",
        "why": "autoharn-panel CLAUDE.md point 1, read live and read-only from "
            "/home/bork/w/vdc/1/experience/autoharn-panel/CLAUDE.md: 'An increment left out of "
            "the ledger does not exist: resumption cannot see it ... (run-8 finding, "
            "2026-07-11).' Too fine 'adds ledger ceremony with no resumability gain (run10: "
            "three items that collapsed to one file and one commit)'; too coarse 'hides a seam "
            "a successor could have picked up separately (design/ORCH-RETROSPECTIVE-RUN10.md, "
            "Finding 2)' -- both directions independently witnessed against the SAME project.",
        "hydrates": "Durable decision adopted at world birth (decomposition-to-unit-of-independent-"
            "resumption, catalog tools/setup_tui/durable_decisions.py, why: autoharn-panel "
            "CLAUDE.md point 1, run-8 finding 2026-07-11 and ORCH-RETROSPECTIVE-RUN10.md "
            "Finding 2): decompose a commission to the UNIT OF INDEPENDENT RESUMPTION -- no "
            "numeric item/file-count rule; judge by whether a fresh session could pick up the "
            "slug alone and know what to build and how to tell it's done.",
        "claude_md": "- **Decompose to the unit of independent resumption** -- not below it, not above "
            "it, no numeric item/file-count rule (a fixed target is cargo-cultable and wrong as "
            "often as right). Judge by one question: could a fresh session pick up this slug "
            "alone and know what to build and how to tell it's done? (autoharn-panel prior art, "
            "CLAUDE.md point 1: too fine adds ledger ceremony with no resumability gain, run10; "
            "too coarse hides a seam a successor could have picked up separately, run-8.)",
    },
    # 11-13. WIRED per the genericity critique's own closing judgment (row 1722, design/
    # SONNET-CATALOG-GENERICITY-CRITIQUE-2026-07-19.md): three candidates the critique flagged as
    # more portable than several entries that DID make the original cut, written in generic
    # voice from the start (never mined-then-translated).
    #
    # 11. The critique's own top pick ("conspicuously missing... the single most generic, most
    # load-bearing durable decision the harness embodies"): the WITNESSED/REFUSED-AS-EXPECTED/
    # UNEXERCISED claims taxonomy, already project-agnostic in this repo's own CLAUDE.md.
    {
        "slug": "claims-carry-witnesses",
        "rule": "Every claim in a report states its evidentiary status per item: WITNESSED (with "
             "the observed output), REFUSED-AS-EXPECTED (a refusal that was the correct "
             "outcome), or UNEXERCISED (with the concrete blocker that stopped you). Docs follow "
             "the same rule -- an example carries real output or an UNWITNESSED mark. No "
             "umbrella claims covering multiple items at once.",
        "why": "this repo's own CLAUDE.md ORCHESTRATION section (already written project-"
            "agnostically, no translation needed): 'Claims carry witnesses. A report states, "
            "per item: WITNESSED (with observed output), REFUSED-AS-EXPECTED, or UNEXERCISED "
            "with the concrete blocker. Docs follow the same rule (an example carries real "
            "output or an UNWITNESSED mark). No umbrella claims.' Wired per row 1722's "
            "genericity critique, which named this taxonomy the catalog's most conspicuous gap.",
        "hydrates": "Durable decision adopted at world birth (claims-carry-witnesses, catalog "
            "tools/setup_tui/durable_decisions.py, why: this repo's own CLAUDE.md ORCHESTRATION "
            "section + ledger row 1722): every claim in a report states its evidentiary status "
            "per item -- WITNESSED (observed output), REFUSED-AS-EXPECTED, or UNEXERCISED (the "
            "concrete blocker); docs follow the same rule; no umbrella claims.",
        "claude_md": "- **Claims carry witnesses** -- every claim in a report states its evidentiary "
            "status per item: WITNESSED (with the observed output), REFUSED-AS-EXPECTED (a "
            "refusal that was the correct outcome), or UNEXERCISED (with the concrete blocker). "
            "Docs follow the same rule -- an example carries real output or an UNWITNESSED "
            "mark. No umbrella claims covering multiple items at once.",
    },
    # 12. Anti-anchoring-bias principle for how a review prompt is written.
    {
        "slug": "unanchored-review-briefs",
        "rule": "A review brief hands the reviewer the artifact, the spec, the law, and a refute "
             "posture -- never a pre-identified list of suspected defects. A reviewer told "
             "where to look is confirming a hypothesis, not discovering one; the finding is "
             "only as independent as the brief that produced it.",
        "why": "ledger row 1278 (this repo): 's37 verdict round dispatched UNANCHORED per row "
            "1276's standing rule: a FRESH reviewer instance..., given the cumulative diff, the "
            "spec, the LAW, and the refute posture; no suspect lists from anyone.' Flagged by "
            "row 1722's genericity critique as more portable than several entries that made the "
            "original cut.",
        "hydrates": "Durable decision adopted at world birth (unanchored-review-briefs, catalog "
            "tools/setup_tui/durable_decisions.py, why: ledger row 1278): a review brief hands "
            "the reviewer the artifact, the spec, the law, and a refute posture -- never a "
            "pre-identified suspect list; a reviewer told where to look is confirming a "
            "hypothesis, not discovering one.",
        "claude_md": "- **Unanchored review briefs** -- a review brief hands the reviewer the artifact, "
            "the spec, the law, and a refute posture, never a pre-identified list of suspected "
            "defects. A reviewer told where to look is confirming a hypothesis, not discovering "
            "one; the finding is only as independent as the brief that produced it (ledger row "
            "1278).",
    },
    # 13. Routine independent review for delegated work, mandatory for core/critical-path
    # changes -- generalized from "kernel-touching" per the critique's own suggested
    # substitution (a one-word swap from this project's specific tiering to a portable one).
    {
        "slug": "fresh-context-review-for-delegated-work",
        "rule": "Delegated work gets a routine, fresh-context, independent review before "
             "acceptance; a change touching the project's sensitive core or critical path makes "
             "that review MANDATORY, not optional. The reviewer works from the ratified spec, "
             "the diff, and the witness harness -- never the delegate's own self-report -- and "
             "derives its own verdict from artifact-vs-spec, checking specifically for silent "
             "narrowing, improvisation, or malicious compliance.",
        "why": "ledger row 1492 (this repo, maintainer ruling 2026-07-19): 'all Sonnet builds "
            "(especially those invading into the kernel) need... a review (also Sonnet)... "
            "ADOPTED AS STANDING: every Sonnet build -- with kernel-touching builds mandatory, "
            "others by default -- receives a FRESH-CONTEXT ADVERSARIAL REVIEW before acceptance "
            "... the reviewer receives the ratified build basis, the commit diff, the banked "
            "witness harness, and the LAW -- NEVER the builder's own report.' Generalized from "
            "\"kernel-touching\" to \"the project's sensitive core or critical path\" per row "
            "1722's genericity critique (a one-word-class substitution, not a content change).",
        "hydrates": "Durable decision adopted at world birth (fresh-context-review-for-delegated-work, "
            "catalog tools/setup_tui/durable_decisions.py, why: ledger rows 1492/1722): "
            "delegated work gets a routine, fresh-context, independent review before "
            "acceptance; a change touching the project's sensitive core or critical path makes "
            "that review MANDATORY; the reviewer works from the ratified spec, the diff, and "
            "the witness harness, never the delegate's own self-report, checking for silent "
            "narrowing, improvisation, or malicious compliance.",
        "claude_md": "- **Fresh-context review for delegated work** -- delegated work gets a routine, "
            "fresh-context, independent review before acceptance; a change touching the "
            "project's sensitive core or critical path makes that review MANDATORY, not "
            "optional. The reviewer works from the ratified spec, the diff, and the witness "
            "harness -- never the delegate's own self-report -- checking specifically for "
            "silent narrowing, improvisation, or malicious compliance (ledger row 1492).",
    },
]
