#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T23:37:02Z
#   last-change: 2026-07-19T19:55:20Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/durable_decisions.py -- the durable-decisions catalog
(design/FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md §3-§4, commission ledger row 1714). ONE home
(ADR-0012 P1) for the small-ish, painful-experience-borne catalog of standing rules a fresh
world can adopt at hydration time: the hydration screen (screens.py screen_hydration) renders
FROM this module, each selection writes ONE real `led decision` row (never a kernel `obligate`
row -- see "Obligates (softly)" below), and CLAUDE.md compilation (`compile_claude_md`) reads
FROM it -- no second copy of any rule text anywhere.

Admission criterion, verbatim from the spec: "An entry without a witnessed specimen does not
enter the catalog -- 'borne out of our painful experience' is the admission criterion,
verbatim." Every CATALOG entry below carries its `why` citation for exactly that reason.

"Obligates (softly)" is defined, not vibes (spec §3): a selected entry writes decision rows and
compiles CLAUDE.md prose -- standing guidance a session reads and the record shows it adopted.
It does NOT write kernel `obligate` rows in v1: the obligate-amplification footgun (led.tmpl's
own teaching, ledger row 1640 -- a review_gap-obliged actor's own dispositions became new debt,
self-amplifying) is exactly the painful experience this catalog exists to encode, and an
idiot-proofing surface must not hand a fresh operator a loaded obligation trigger at birth.
Kernel-obligation hydration, if ever wanted, is a later maintainer-ratified extension; named out
of v1 -- nothing in this module ever calls `led obligate`.

ADR adoption (catalog item 3) is NOT a fixed CATALOG entry -- it is a submenu DERIVED from
`law/adr/*.md` at runtime (`list_adrs`), never a hand list (WD3's own bar): the operator selects
which ADRs the new world adopts, and each selection hydrates one row naming the ADR by number
and title.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import here is top of file.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from tools.setup_tui.plan import Hole, WriteAct

REPO_ROOT = Path(__file__).resolve().parents[2]
ADR_DIR = REPO_ROOT / "law" / "adr"

BEGIN_MARKER = "<!-- BEGIN COMPILED DURABLE DECISIONS (setup_tui) -->"
END_MARKER = "<!-- END COMPILED DURABLE DECISIONS (setup_tui) -->"


@dataclass(frozen=True)
class DurableDecision:
    slug: str
    rule: str
    why: str
    hydrates: str      # the exact `led decision` statement this selection writes
    claude_md: str      # the fragment compiled into the new world's CLAUDE.md


# ---------------------------------------------------------------------------------------------
# Initial catalog -- 7 to 15 entries, DISTILLED from the prior art of BOTH projects (amendment
# per commission ledger row 1716, superseding this spec's original three-plus-proposals shape;
# see design/FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md §3). Mined read-only from two evidence
# sources: this repo's own ledger (`./led show <id>`) and the autoharn-panel LIVE deployment at
# /home/bork/w/vdc/1/experience/autoharn-panel (its CLAUDE.md file, and its live Postgres ledger
# schema `experience`/`experience_kernel` on host 192.168.122.1 db toy, read via plain SELECT --
# never a write, per the never-touch-a-user-project rule). Every entry below cites its specimen
# so the maintainer can verify the distillation; the report accompanying this build lists the
# additional candidates that were mined but NOT wired in, for pruning/addition.
#
# GENERICITY PASS (ledger row 1722, adopting design/SONNET-CATALOG-GENERICITY-CRITIQUE-2026-
# 07-19.md wholesale): a fresh-context Sonnet critic reviewed this catalog against the spec's
# own "small-ish curated catalog... born of witnessed painful experience" audience (a stranger
# adopting this harness for their own project) and found the mining step had faithfully carried
# CITATIONS but not always translated the RULE text out of first-person-project voice. Applied
# here: `setup-surface-is-maintained` CUT outright (addressed to autoharn's own core
# contributors, no purchase for an adopter -- stays an internal rule, ledger row 1700, not a
# hydration option); `makespan-scheduling-by-mandate`, `obligate-amplification-caution`,
# `doc-currency-at-the-seam`, `runs-are-strictly-linear` REWRITTEN into stranger-portable voice
# (each entry below marks its own rewrite inline; `why` citations kept exactly as banked -- the
# citations are the evidence, they stay local); three entries the critique flagged as more
# portable than several that made the original cut WIRED (`claims-carry-witnesses`,
# `unanchored-review-briefs`, `fresh-context-review-for-delegated-work`), each in generic voice
# from the start.
#
# 13 entries total below (12 fixed DurableDecision structs + the ADR-adoption submenu just after
# this list) -- inside the 7-15 range, 15 is a hard ceiling not approached.
# ---------------------------------------------------------------------------------------------

CATALOG: list[DurableDecision] = [
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
    DurableDecision(
        slug="makespan-scheduling-by-mandate",
        rule="For any commission spanning 3+ work items with dependencies, precedence "
             "constraints, or resource conflicts, sequence them with a constraint-based "
             "scheduler rather than ad hoc ordering. Require a high-stakes task's decomposition "
             "and close to be cosigned by a principal distinct from the one who did the work -- "
             "treat an undischarged cosign as a hard block on further edits, never backloggable "
             "debt.",
        why="maintainer directive 2026-07-14 (user-guide/USER-RECIPES-FAQ.md 'Workflow "
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
        hydrates=(
            "Durable decision adopted at world birth (makespan-scheduling-by-mandate, catalog "
            "tools/setup_tui/durable_decisions.py, why: ledger rows 1714/1716/1722 + "
            "autoharn-panel/CLAUDE.md points 2-3 and its RESOURCES table row id=1178): for any "
            "commission spanning 3+ work items with dependencies, precedence constraints, or "
            "resource conflicts, sequence them with a constraint-based scheduler rather than ad "
            "hoc ordering; require a high-stakes task's decomposition and close to be cosigned "
            "by a principal distinct from the one who did the work, treating an undischarged "
            "cosign as a hard block on further edits, never backloggable debt."
        ),
        claude_md=(
            "- **Constraint-scheduled, cosigned decomposition** -- for any commission spanning "
            "3+ work items with dependencies, precedence constraints, or resource conflicts, "
            "sequence them with a constraint-based scheduler (this harness ships one: "
            "`tools/makespan-scheduler/`, CP-SAT via OR-Tools) rather than ad hoc ordering. "
            "Require a high-stakes task's decomposition and close to be cosigned by a principal "
            "distinct from the one who did the work -- treat an undischarged cosign as a hard "
            "block on further edits, never backloggable debt. Full treatment: "
            "user-guide/USER-RECIPES-FAQ.md 'Workflow patterns', "
            "design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md."
        ),
    ),
    # 2. Maintainer-named anchor (row 1714).
    DurableDecision(
        slug="drift-backstops",
        rule="The orchestrator is softly obligated to follow the FAQ's drift-backstop method "
             "(user-guide/USER-RECIPES-FAQ.md, 'Drift backstops') for anything that goes "
             "quietly stale: name the authority/dependent pair, derive both sides mechanically, "
             "compare with a comparator that quantifies over the class, refuse loud (refresh "
             "or declare), backstop the backstop with a seen-red proof and a fixture-census "
             "registration.",
        why="the FAQ section's own fourteen-instance evidence base (user-guide/"
            "USER-RECIPES-FAQ.md 'Drift backstops', citing ADR-0011's Context: 'a design "
            "document that quietly goes stale while the code it describes moves on, a "
            "duplicated fact whose two copies drift apart one edit at a time').",
        hydrates=(
            "Durable decision adopted at world birth (drift-backstops, catalog "
            "tools/setup_tui/durable_decisions.py, why: user-guide/USER-RECIPES-FAQ.md 'Drift "
            "backstops', fourteen-instance evidence base): the orchestrator is softly "
            "obligated to follow the FAQ's five-move drift-backstop method for anything that "
            "goes quietly stale."
        ),
        claude_md=(
            "- **Drift backstops (soft obligation)** -- for anything that goes quietly stale "
            "(docs from code, a hash function from a table's columns, a config from the "
            "mechanisms it configures), follow the five-move method in "
            "user-guide/USER-RECIPES-FAQ.md 'Drift backstops': name the pair, derive both "
            "sides mechanically, compare with a comparator quantifying over the class, refuse "
            "loud (refresh or declare), backstop the backstop."
        ),
    ),
    # 3. Mined, this repo's ledger: single-branch authoring.
    DurableDecision(
        slug="single-branch-authoring",
        rule="Content is authored on the single working branch ONLY; a cut/release branch is a "
             "pure derivation (projection), never a place an edit originates. An edit made "
             "inside a cut is the defect to make unrepresentable, not a convenience.",
        why="ledger row 1033 (this repo, maintainer ruling 2026-07-15): 'ONE branch, full "
            "stop. Worktrees fine; branches are the transaction-paradigm violation witnessed "
            "today (v1.1 cut-only README/USER-CONFIGURATION edits authored in the cut worktree, "
            "never backported to next, silently re-deleted by the v1.1.2 cut from next).'",
        hydrates=(
            "Durable decision adopted at world birth (single-branch-authoring, catalog "
            "tools/setup_tui/durable_decisions.py, why: ledger row 1033): content is authored "
            "on the single working branch ONLY; a cut/release branch is a pure derivation, "
            "never a place an edit originates -- witnessed specimen: v1.1 cut-only edits "
            "authored in a cut worktree were silently re-deleted by the next cut."
        ),
        claude_md=(
            "- **Single-branch authoring** -- content is authored on the single working branch "
            "ONLY; a cut/release branch is a pure derivation (projection), never a place an "
            "edit originates (ledger row 1033: cut-only edits were silently re-deleted by the "
            "next cut)."
        ),
    ),
    # 4. Mined, this repo's ledger: tagging discipline.
    DurableDecision(
        slug="tags-are-serious-business",
        rule="Public main stays continuously up to date via routinely pushed, UNTAGGED cuts. "
             "Tagging is serious business -- a deliberate release act, never done between "
             "feature sets.",
        why="ledger row 1027 (this repo, maintainer ruling 2026-07-15): 'public origin/main "
            "stays continuously up-to-date -- cut commits pushed routinely, UNTAGGED. Tagging "
            "is serious business, a deliberate release act, never done between feature sets.'",
        hydrates=(
            "Durable decision adopted at world birth (tags-are-serious-business, catalog "
            "tools/setup_tui/durable_decisions.py, why: ledger row 1027): public main stays "
            "continuously up to date via routinely pushed, UNTAGGED cuts; tagging is a "
            "deliberate release act, never done between feature sets."
        ),
        claude_md=(
            "- **Tags are serious business** -- push public main often, UNTAGGED; a tag is a "
            "deliberate release act, never done between feature sets (ledger row 1027)."
        ),
    ),
    # 5. Mined, this repo's ledger: the obligate-amplification footgun (already cited by this
    # spec's own §3 as the reason v1 writes no kernel obligate rows -- promoted from the prior
    # PROPOSED shape into the real catalog once the maintainer widened its scope, then REWRITTEN
    # into stranger-portable voice per the genericity critique (row 1722, entry #5:
    # GENERALIZABLE -- the prior text outsourced its own substance to "led.tmpl's own... note"
    # instead of stating the warning inline). `why` kept exactly as banked.
    DurableDecision(
        slug="obligate-amplification-caution",
        rule="Before writing any obligation row into the ledger, know that over-catch review "
             "triggers are retroactive with no time bound, and that an obliged actor's own "
             "later actions can count as new debt against themselves. Always discharge review "
             "obligations under a different principal than the one who is obliged.",
        why="ledger row 1640 (this repo, 2026-07-18, autoharn-panel world/older lineage): the "
            "obligate footgun's third witnessed occurrence -- 1225 pre-existing rows flagged as "
            "debt, then 1225->1228 amplification when the obliged actor's own dispositions "
            "counted as new debt; rule text rewritten per row 1722's genericity critique, "
            "entry #5.",
        hydrates=(
            "Durable decision adopted at world birth (obligate-amplification-caution, catalog "
            "tools/setup_tui/durable_decisions.py, why: ledger rows 1640/1722): before writing "
            "any obligation row into the ledger, know that over-catch review triggers are "
            "retroactive with no time bound, and that an obliged actor's own later actions can "
            "count as new debt against themselves -- always discharge review obligations under "
            "a different principal than the one who is obliged."
        ),
        claude_md=(
            "- **Obligation-trigger caution** -- before writing any obligation row into the "
            "ledger, know that over-catch review triggers are retroactive with no time bound, "
            "and that an obliged actor's own later actions can count as new debt against "
            "themselves. Always discharge review obligations under a different principal than "
            "the one who is obliged (ledger row 1640)."
        ),
    ),
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
    DurableDecision(
        slug="doc-currency-at-the-seam",
        rule="Every merge that changes user-facing behavior includes its documentation update "
             "(or a named, tracked deferral with a reason) in the same unit of work. A merge "
             "silent on docs for a behavior change is itself a defect.",
        why="ledger row 1699 (this repo, maintainer-directed 2026-07-19): 'we need durable "
            "decisions so to reduce the vigilance burden of remembering after new features have "
            "been added' -- precedent: the 2026-07-18 Block D merge landed undocumented and "
            "needed a dedicated catch-up pass (rows 1652-1661 vs 1667); rule text rewritten per "
            "row 1722's genericity critique, entry #7.",
        hydrates=(
            "Durable decision adopted at world birth (doc-currency-at-the-seam, catalog "
            "tools/setup_tui/durable_decisions.py, why: ledger rows 1699/1722): every merge "
            "that changes user-facing behavior includes its documentation update, or a named, "
            "tracked deferral with a reason, in the same unit of work; a merge silent on docs "
            "for a behavior change is itself a defect."
        ),
        claude_md=(
            "- **Doc currency at the seam** -- every merge that changes user-facing behavior "
            "includes its documentation update (or a named, tracked deferral with a reason) in "
            "the same unit of work. A merge silent on docs for a behavior change is itself a "
            "defect (ledger row 1699)."
        ),
    ),
    # 8. Mined, this repo's ledger: concurrent builders need isolation.
    DurableDecision(
        slug="concurrent-builders-need-isolation",
        rule="Overlapping-surface commissions get worktree isolation or serial dispatch, never "
             "a shared checkout -- a concurrent sibling's uncommitted hunk in a shared working "
             "tree can be swept into another builder's commit by an ordinary `git add` of a "
             "declared path.",
        why="ledger row 1502 (this repo, s45 adversarial review adjudication): commit 94f5b7a "
            "bundled a fixture_census registry row for defeat-pipeline before those files "
            "existed, making the census gate RED on a clean checkout -- cause: 'shared-checkout "
            "concurrency, not builder invention: the pipeline builder's uncommitted hunk in the "
            "SHARED gates/fixture_census.py was swept by s45's git add of its own declared "
            "path.'",
        hydrates=(
            "Durable decision adopted at world birth (concurrent-builders-need-isolation, "
            "catalog tools/setup_tui/durable_decisions.py, why: ledger row 1502): "
            "overlapping-surface commissions get worktree isolation or serial dispatch, never a "
            "shared checkout -- witnessed scope-bleed: a concurrent builder's uncommitted hunk "
            "in a shared file was swept into another builder's commit."
        ),
        claude_md=(
            "- **Concurrent builders need isolation** -- overlapping-surface commissions get "
            "worktree isolation or serial dispatch, never a shared checkout (ledger row 1502: "
            "a concurrent builder's uncommitted hunk in a shared file was swept into another "
            "builder's commit, making a census gate falsely RED)."
        ),
    ),
    # 9. Mined, this repo's ledger/CLAUDE.md: runs are strictly linear. REWRITTEN per the
    # genericity critique (row 1722, entry #9: GENERALIZABLE -- generic content, bespoke
    # vocabulary: "run"/"world"/"birth chain" used with no inline gloss). `why` kept as banked.
    DurableDecision(
        slug="runs-are-strictly-linear",
        rule="Once a deployment's evidence is recorded, treat it as immutable history -- never "
             "patch, refresh, or apply deltas to it after the fact. A needed change is realized "
             "only in the next deployment you create.",
        why="maintainer ruling 2026-07-11 (this repo's own CLAUDE.md, ORCHESTRATION section): "
            "the apply-to-existing-world clause and bootstrap/apply-delta.sh's typed-"
            "confirmation ceremony were retired after being witnessed producing cargo-cult "
            "sysadmin work; the run-2 world was itself broken at birth by an unscripted "
            "scaffold-to-/tmp + hand-mv gap; rule text rewritten per row 1722's genericity "
            "critique, entry #9.",
        hydrates=(
            "Durable decision adopted at world birth (runs-are-strictly-linear, catalog "
            "tools/setup_tui/durable_decisions.py, why: maintainer ruling 2026-07-11 + ledger "
            "row 1722): once a deployment's evidence is recorded, treat it as immutable history "
            "-- never patch, refresh, or apply deltas to it after the fact; a needed change is "
            "realized only in the next deployment you create."
        ),
        claude_md=(
            "- **Deployments are immutable history once recorded** -- once a deployment's "
            "evidence is recorded, treat it as immutable history: never patch, refresh, or "
            "apply deltas to it after the fact. A needed change is realized only in the next "
            "deployment you create (maintainer ruling 2026-07-11)."
        ),
    ),
    # 10. Mined, autoharn-panel LIVE deployment CLAUDE.md point 1: decomposition granularity.
    DurableDecision(
        slug="decomposition-to-unit-of-independent-resumption",
        rule="Decompose a commission into ledgered work items to the UNIT OF INDEPENDENT "
             "RESUMPTION -- not below it and not above it, and no numeric rule (a fixed item- "
             "or file-count target is cargo-cultable and wrong as often as right). Judge "
             "granularity by one question: could a fresh session pick up this slug alone and "
             "know what to build and how to tell it's done?",
        why="autoharn-panel CLAUDE.md point 1, read live and read-only from "
            "/home/bork/w/vdc/1/experience/autoharn-panel/CLAUDE.md: 'An increment left out of "
            "the ledger does not exist: resumption cannot see it ... (run-8 finding, "
            "2026-07-11).' Too fine 'adds ledger ceremony with no resumability gain (run10: "
            "three items that collapsed to one file and one commit)'; too coarse 'hides a seam "
            "a successor could have picked up separately (design/ORCH-RETROSPECTIVE-RUN10.md, "
            "Finding 2)' -- both directions independently witnessed against the SAME project.",
        hydrates=(
            "Durable decision adopted at world birth (decomposition-to-unit-of-independent-"
            "resumption, catalog tools/setup_tui/durable_decisions.py, why: autoharn-panel "
            "CLAUDE.md point 1, run-8 finding 2026-07-11 and ORCH-RETROSPECTIVE-RUN10.md "
            "Finding 2): decompose a commission to the UNIT OF INDEPENDENT RESUMPTION -- no "
            "numeric item/file-count rule; judge by whether a fresh session could pick up the "
            "slug alone and know what to build and how to tell it's done."
        ),
        claude_md=(
            "- **Decompose to the unit of independent resumption** -- not below it, not above "
            "it, no numeric item/file-count rule (a fixed target is cargo-cultable and wrong as "
            "often as right). Judge by one question: could a fresh session pick up this slug "
            "alone and know what to build and how to tell it's done? (autoharn-panel prior art, "
            "CLAUDE.md point 1: too fine adds ledger ceremony with no resumability gain, run10; "
            "too coarse hides a seam a successor could have picked up separately, run-8.)"
        ),
    ),
    # 11-13. WIRED per the genericity critique's own closing judgment (row 1722, design/
    # SONNET-CATALOG-GENERICITY-CRITIQUE-2026-07-19.md): three candidates the critique flagged as
    # more portable than several entries that DID make the original cut, written in generic
    # voice from the start (never mined-then-translated).
    #
    # 11. The critique's own top pick ("conspicuously missing... the single most generic, most
    # load-bearing durable decision the harness embodies"): the WITNESSED/REFUSED-AS-EXPECTED/
    # UNEXERCISED claims taxonomy, already project-agnostic in this repo's own CLAUDE.md.
    DurableDecision(
        slug="claims-carry-witnesses",
        rule="Every claim in a report states its evidentiary status per item: WITNESSED (with "
             "the observed output), REFUSED-AS-EXPECTED (a refusal that was the correct "
             "outcome), or UNEXERCISED (with the concrete blocker that stopped you). Docs follow "
             "the same rule -- an example carries real output or an UNWITNESSED mark. No "
             "umbrella claims covering multiple items at once.",
        why="this repo's own CLAUDE.md ORCHESTRATION section (already written project-"
            "agnostically, no translation needed): 'Claims carry witnesses. A report states, "
            "per item: WITNESSED (with observed output), REFUSED-AS-EXPECTED, or UNEXERCISED "
            "with the concrete blocker. Docs follow the same rule (an example carries real "
            "output or an UNWITNESSED mark). No umbrella claims.' Wired per row 1722's "
            "genericity critique, which named this taxonomy the catalog's most conspicuous gap.",
        hydrates=(
            "Durable decision adopted at world birth (claims-carry-witnesses, catalog "
            "tools/setup_tui/durable_decisions.py, why: this repo's own CLAUDE.md ORCHESTRATION "
            "section + ledger row 1722): every claim in a report states its evidentiary status "
            "per item -- WITNESSED (observed output), REFUSED-AS-EXPECTED, or UNEXERCISED (the "
            "concrete blocker); docs follow the same rule; no umbrella claims."
        ),
        claude_md=(
            "- **Claims carry witnesses** -- every claim in a report states its evidentiary "
            "status per item: WITNESSED (with the observed output), REFUSED-AS-EXPECTED (a "
            "refusal that was the correct outcome), or UNEXERCISED (with the concrete blocker). "
            "Docs follow the same rule -- an example carries real output or an UNWITNESSED "
            "mark. No umbrella claims covering multiple items at once."
        ),
    ),
    # 12. Anti-anchoring-bias principle for how a review prompt is written.
    DurableDecision(
        slug="unanchored-review-briefs",
        rule="A review brief hands the reviewer the artifact, the spec, the law, and a refute "
             "posture -- never a pre-identified list of suspected defects. A reviewer told "
             "where to look is confirming a hypothesis, not discovering one; the finding is "
             "only as independent as the brief that produced it.",
        why="ledger row 1278 (this repo): 's37 verdict round dispatched UNANCHORED per row "
            "1276's standing rule: a FRESH reviewer instance..., given the cumulative diff, the "
            "spec, the LAW, and the refute posture; no suspect lists from anyone.' Flagged by "
            "row 1722's genericity critique as more portable than several entries that made the "
            "original cut.",
        hydrates=(
            "Durable decision adopted at world birth (unanchored-review-briefs, catalog "
            "tools/setup_tui/durable_decisions.py, why: ledger row 1278): a review brief hands "
            "the reviewer the artifact, the spec, the law, and a refute posture -- never a "
            "pre-identified suspect list; a reviewer told where to look is confirming a "
            "hypothesis, not discovering one."
        ),
        claude_md=(
            "- **Unanchored review briefs** -- a review brief hands the reviewer the artifact, "
            "the spec, the law, and a refute posture, never a pre-identified list of suspected "
            "defects. A reviewer told where to look is confirming a hypothesis, not discovering "
            "one; the finding is only as independent as the brief that produced it (ledger row "
            "1278)."
        ),
    ),
    # 13. Routine independent review for delegated work, mandatory for core/critical-path
    # changes -- generalized from "kernel-touching" per the critique's own suggested
    # substitution (a one-word swap from this project's specific tiering to a portable one).
    DurableDecision(
        slug="fresh-context-review-for-delegated-work",
        rule="Delegated work gets a routine, fresh-context, independent review before "
             "acceptance; a change touching the project's sensitive core or critical path makes "
             "that review MANDATORY, not optional. The reviewer works from the ratified spec, "
             "the diff, and the witness harness -- never the delegate's own self-report -- and "
             "derives its own verdict from artifact-vs-spec, checking specifically for silent "
             "narrowing, improvisation, or malicious compliance.",
        why="ledger row 1492 (this repo, maintainer ruling 2026-07-19): 'all Sonnet builds "
            "(especially those invading into the kernel) need... a review (also Sonnet)... "
            "ADOPTED AS STANDING: every Sonnet build -- with kernel-touching builds mandatory, "
            "others by default -- receives a FRESH-CONTEXT ADVERSARIAL REVIEW before acceptance "
            "... the reviewer receives the ratified build basis, the commit diff, the banked "
            "witness harness, and the LAW -- NEVER the builder's own report.' Generalized from "
            "\"kernel-touching\" to \"the project's sensitive core or critical path\" per row "
            "1722's genericity critique (a one-word-class substitution, not a content change).",
        hydrates=(
            "Durable decision adopted at world birth (fresh-context-review-for-delegated-work, "
            "catalog tools/setup_tui/durable_decisions.py, why: ledger rows 1492/1722): "
            "delegated work gets a routine, fresh-context, independent review before "
            "acceptance; a change touching the project's sensitive core or critical path makes "
            "that review MANDATORY; the reviewer works from the ratified spec, the diff, and "
            "the witness harness, never the delegate's own self-report, checking for silent "
            "narrowing, improvisation, or malicious compliance."
        ),
        claude_md=(
            "- **Fresh-context review for delegated work** -- delegated work gets a routine, "
            "fresh-context, independent review before acceptance; a change touching the "
            "project's sensitive core or critical path makes that review MANDATORY, not "
            "optional. The reviewer works from the ratified spec, the diff, and the witness "
            "harness -- never the delegate's own self-report -- checking specifically for "
            "silent narrowing, improvisation, or malicious compliance (ledger row 1492)."
        ),
    ),
]

# The non-catalog hydration items that remain as-is (spec §3, "Relation to the existing screen-8
# items"): per-world facts, not durable decisions -- named here only so feature_facts.py and the
# drift fixture have one place to read the full hydration-item name set from without a second
# hand list.
NON_CATALOG_HYDRATION_ITEMS = ("fork_provenance", "role_charters")


# ---------------------------------------------------------------------------------------------
# ADR adoption submenu -- DERIVED from law/adr/*.md at runtime, never a hand list (spec §3 item
# 3, WD3's own bar).
# ---------------------------------------------------------------------------------------------

_ADR_TITLE_RE = re.compile(r"^#\s*ADR-(\d+)[:\s—-]*(.*)$")


def list_adrs() -> list[tuple[str, str, str]]:
    """(number, title, relpath-from-repo-root) for every law/adr/*.md file, sorted by number,
    read fresh from disk every call -- the mechanical derivation WD3 checks against. The title
    line is the first line in the file matching `# ADR-<digits>...` (some files carry a leading
    `<!-- doc-attest-exempt: ... -->` HTML comment before the real title line, e.g.
    law/adr/0012-compositional-and-structural-hygiene.md -- this scans every line, not just the
    first, so that comment never gets mistaken for the title)."""
    out: list[tuple[str, str, str]] = []
    for path in sorted(ADR_DIR.glob("*.md")):
        title = None
        number = None
        for line in path.read_text(encoding="utf-8").splitlines():
            m = _ADR_TITLE_RE.match(line.strip())
            if m:
                number, title = m.group(1), m.group(2).strip()
                break
        if number is None:
            # No recognizable title line -- never fabricate one; the number comes from the
            # filename's own leading digits so the ADR still appears (loud, not silently
            # dropped), with an honest "(title not found)" rather than an invented one.
            stem = path.stem
            digits = "".join(ch for ch in stem.split("-", 1)[0] if ch.isdigit())
            number = digits or stem
            title = "(title not found -- no '# ADR-<n>...' line in file)"
        out.append((number, title, str(path.relative_to(REPO_ROOT))))
    out.sort(key=lambda t: t[0])
    return out


def adr_decision_statement(number: str, title: str, relpath: str) -> str:
    return (
        f"Durable decision adopted at world birth (adr-adoption, catalog "
        f"tools/setup_tui/durable_decisions.py, submenu derived from law/adr/*.md): this world "
        f"adopts ADR-{number}: {title} ({relpath})."
    )


def adr_claude_md_fragment(number: str, title: str, relpath: str) -> str:
    return f"- adopted ADR-{number}: {title} ({relpath})"


# ---------------------------------------------------------------------------------------------
# CLAUDE.md compilation (spec §4).
# ---------------------------------------------------------------------------------------------

def compute_claude_md_text(dest_dir: str, fragments: list[str]) -> str:
    """The pure text-computation half of `compile_claude_md`'s pre-Phase-2 body: reads
    `<dest_dir>/CLAUDE.md`'s CURRENT bytes (a live read; see `hydration_claude_md_write_act`'s own
    docstring for why this is only ever called at COMMIT time, after birth has actually written
    the file) and returns the new full text. Never writes -- `hydration_claude_md_write_act`'s
    `WriteAct` is where the write happens. Rules (spec §4), each load-bearing:

      * NEVER touches bytes outside the markers -- the file is read whole, split on the marker
        pair if present, and only the middle segment is replaced; everything before BEGIN and
        after END is carried through byte-for-byte.
      * Idempotent -- calling this twice with the SAME `fragments` produces byte-identical
        output (the replace-in-place path, not an append, fires the second time).
      * On a fork-copy destination (CLAUDE.md-preservation move, screen_fork_target renames the
        fork's own CLAUDE.md to CLAUDE.project.md BEFORE this ever runs) the compiled section is
        APPENDED to the scaffold-written CLAUDE.md without disturbing CLAUDE.project.md -- this
        function only ever touches `<dest_dir>/CLAUDE.md`, never CLAUDE.project.md.
      * If CLAUDE.md does not exist yet, one is created holding only the compiled section (never
        silently skipped) -- a defensive branch for --start-at hydration reached before birth.

    This is called ONLY at commit time (never at decision time -- in the normal sequence,
    `dest_dir`/CLAUDE.md does not exist yet until birth's own plan entry has actually run, and
    reading it early would wrongly treat a not-yet-created file as "nothing to preserve").

    Numbering choice (ledger row 1790, finding 2): the compiled comment used to hard-code
    "screen 8" for hydration -- stale the moment principals-authority/signed-genesis were
    inserted ahead of it (hydration is screen 10 of 11 as of this build). screens.py is the one
    module that could derive a live screen number (its own SCREEN_NUMBER dict, built from the
    SCREENS registry's order), but screens.py is this module's OWN importer (`from
    tools.setup_tui import ... durable_decisions ...`) -- importing it back here would be
    circular. So this module does NOT carry a number at all: the comment names only the
    insertion-proof `--start-at hydration` pointer, which is correct regardless of where
    hydration sits in the flow."""
    claude_path = os.path.join(dest_dir, "CLAUDE.md")
    existing = ""
    if os.path.isfile(claude_path):
        with open(claude_path, encoding="utf-8") as f:
            existing = f.read()

    body_lines = [
        BEGIN_MARKER,
        "<!-- generated by tools/setup_tui/durable_decisions.py -- do not hand-edit; "
        "regenerate via the setup TUI's hydration screen, or "
        "`python3 -m tools.setup_tui.app --start-at hydration` -->",
        "",
        "## Durable decisions (compiled, setup_tui)",
        "",
    ]
    if fragments:
        body_lines.extend(fragments)
    else:
        body_lines.append("(none selected at hydration time)")
    body_lines.append("")
    body_lines.append(END_MARKER)
    section = "\n".join(body_lines)

    if BEGIN_MARKER in existing and END_MARKER in existing:
        pre, rest = existing.split(BEGIN_MARKER, 1)
        _mid, post = rest.split(END_MARKER, 1)
        return pre + section + post
    if existing:
        sep = "" if existing.endswith("\n") else "\n"
        return existing + sep + "\n" + section + "\n"
    return section + "\n"


def hydration_claude_md_write_act(dest_dir: str, fragments: list[str], birth_produces: str) -> WriteAct:
    """The CLAUDE.md-compilation plan act (spec §4), as a `WriteAct`. `content` is a `Hole` on
    `birth_produces` (the birth screen's own plan entry, whatever it `produces`) -- its `extract`
    IGNORES the bound value and instead calls `compute_claude_md_text` fresh, which is legitimate
    for the SAME reason `signed_genesis.discharge_write_act` does the analogous thing: the value
    this write needs to be correct (the world's CURRENT CLAUDE.md bytes) genuinely does not exist,
    and cannot be read honestly, until birth's own act -- ordered earlier in the SAME plan -- has
    actually run. `of=birth_produces` names that real ordering dependency; the extract's own
    ignoring of the bound text is the same pattern `screens.py`'s own comment on this call site
    documents, not a second, undeclared mechanism."""
    return WriteAct(
        path=os.path.join(dest_dir, "CLAUDE.md"),
        content=Hole(of=birth_produces, describe="compiled CLAUDE.md content",
                     extract=lambda _birth_output: compute_claude_md_text(dest_dir, fragments)),
    )
