#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T23:37:02Z
#   last-change: 2026-07-18T23:48:41Z
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
# 11 entries total below (10 fixed DurableDecision structs + the ADR-adoption submenu just after
# this list) -- inside the 7-15 range, 15 is a hard ceiling not approached.
# ---------------------------------------------------------------------------------------------

CATALOG: list[DurableDecision] = [
    # 1. Maintainer-named anchor (row 1714). Substance corrected per row 1716: the makespan
    # mandate's real form, read from the autoharn-panel deployment's OWN CLAUDE.md (points 2-3
    # and its RESOURCES table row, ledger row id=1178 there), is a review obligation, not a bare
    # scheduling preference -- a mandated-tier task's decomposition/close is COSIGNED by a
    # distinct principal, and the panel's `hooks/pretooluse_change_gate.py` decomposition_review
    # mechanism makes that a BLOCKER (a claimed work item's substantive edits are denied while
    # its own opening row's countersign is undischarged), not backloggable debt.
    DurableDecision(
        slug="makespan-scheduling-by-mandate",
        rule="Logistics/makespan scheduling (tools/makespan-scheduler/, CP-SAT via OR-Tools) is "
             "used BY MANDATE for driving execution of 3+ claimed/claimable work items under "
             "dependency, precedence, resource-conflict, or quota constraints, rather than a "
             "hand-picked sequential order -- the session orchestrator can see the overarching "
             "goal and ensures the right rules hydrate at first session start. The mandate is a "
             "REVIEW OBLIGATION, not a bare scheduling preference (autoharn-panel's own form of "
             "the mandate, its CLAUDE.md points 2-3): a mandated-tier task's decomposition is "
             "COSIGNED -- its work item's close is countersigned by a DISTINCT principal citing "
             "the resource's declared evidence shape, because self-reports are not trusted -- "
             "and the decomposition-review mechanism makes an undischarged countersign a "
             "BLOCKER on further substantive edits to the claimed item, not backloggable debt.",
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
            "under dependency, precedence, resource-conflict, or quota constraints').",
        hydrates=(
            "Durable decision adopted at world birth (makespan-scheduling-by-mandate, catalog "
            "tools/setup_tui/durable_decisions.py, why: ledger rows 1714/1716 + "
            "autoharn-panel/CLAUDE.md points 2-3 and its RESOURCES table row id=1178): "
            "logistics/makespan scheduling (tools/makespan-scheduler/) is used BY MANDATE for "
            "driving execution of 3+ claimed/claimable work items under dependency, precedence, "
            "resource-conflict, or quota constraints; the mandate is a review obligation -- a "
            "mandated-tier task's decomposition/close is COSIGNED by a distinct principal, and "
            "an undischarged countersign BLOCKS further substantive edits, never backloggable "
            "debt."
        ),
        claude_md=(
            "- **Makespan scheduling by mandate (cosigned decomposition)** -- use "
            "`tools/makespan-scheduler/` (CP-SAT via OR-Tools) for driving execution of 3+ "
            "claimed/claimable work items under dependency, precedence, resource-conflict, or "
            "quota constraints. The mandate is a REVIEW OBLIGATION (autoharn-panel's own form, "
            "its CLAUDE.md points 2-3): a mandated-tier task's decomposition/close is COSIGNED "
            "by a distinct principal citing the resource's declared evidence shape; an "
            "undischarged countersign is a BLOCKER on further substantive edits, not "
            "backloggable debt. Full treatment: user-guide/USER-RECIPES-FAQ.md 'Workflow "
            "patterns', design/ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md."
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
    # PROPOSED shape into the real catalog now that the maintainer has widened its scope).
    DurableDecision(
        slug="obligate-amplification-caution",
        rule="Never write a kernel `obligate` row without first reading led.tmpl's own "
             "obligate-header note and revoke-refusal warning: `review_gap` over-catch is "
             "retroactive (no temporal bound) and an obliged actor's OWN dispositions become "
             "new debt (self-amplifying) -- discharge under a non-obliged principal, never the "
             "obliged one.",
        why="ledger row 1640 (this repo, 2026-07-18, autoharn-panel world/older lineage): the "
            "obligate footgun's third witnessed occurrence -- 1225 pre-existing rows flagged as "
            "debt, then 1225->1228 amplification when the obliged actor's own dispositions "
            "counted as new debt.",
        hydrates=(
            "Durable decision adopted at world birth (obligate-amplification-caution, catalog "
            "tools/setup_tui/durable_decisions.py, why: ledger row 1640): never write a kernel "
            "obligate row without reading led.tmpl's own obligate-header note and revoke-"
            "refusal warning first; review_gap over-catch is retroactive and self-amplifying "
            "against the obliged actor's own dispositions."
        ),
        claude_md=(
            "- **Obligate-amplification caution** -- never write a kernel `obligate` row "
            "without reading led.tmpl's own obligate-header note and revoke-refusal warning "
            "first (ledger row 1640): `review_gap` over-catch is retroactive, and an obliged "
            "actor's own dispositions become new debt -- discharge under a non-obliged "
            "principal."
        ),
    ),
    # 6. Mined, this repo's ledger: the setup surface is a maintained surface.
    DurableDecision(
        slug="setup-surface-is-maintained",
        rule="The setup surface (tools/setup_tui + the contracts it drives: new-project.sh, "
             "teardown-world.sh, boundary config/ports, deployment.json's key contract, the led "
             "verbs the screens call) is a MAINTAINED surface. Any change to a driven contract "
             "triggers, in the SAME changing work item, a TUI conformance re-check and repair "
             "if the contract moved -- the changer pays, not the next operator.",
        why="ledger row 1700 (this repo, maintainer-directed 2026-07-19): 'the setup surface "
            "itself ... will drift unless maintained' -- mechanization commissioned the same "
            "date (seen-red/setup-tui-scripted-smoke, this build's own sibling fixture).",
        hydrates=(
            "Durable decision adopted at world birth (setup-surface-is-maintained, catalog "
            "tools/setup_tui/durable_decisions.py, why: ledger row 1700): the setup surface is "
            "a maintained surface -- any change to a contract it drives triggers a TUI "
            "conformance re-check and repair in the SAME changing work item; the changer pays."
        ),
        claude_md=(
            "- **The setup surface is a maintained surface** -- any change to a contract "
            "`tools/setup_tui` drives (new-project.sh, teardown-world.sh, boundary config, "
            "deployment.json, the led verbs) triggers a TUI conformance re-check and repair in "
            "the SAME changing work item (ledger row 1700)."
        ),
    ),
    # 7. Mined, this repo's ledger: doc currency at the seam.
    DurableDecision(
        slug="doc-currency-at-the-seam",
        rule="Every merge that adds or changes operator-facing behavior carries its "
             "documentation pass (affected user-guide pages, an orchlog.d note for a "
             "capability, README enumerations) in the SAME work item or a follow-up dispatched "
             "BEFORE the merge row is written; the merge row names the doc commit or the named "
             "deferral with reason. A merge row silent on docs for a behavior change is itself "
             "a violation of this rule.",
        why="ledger row 1699 (this repo, maintainer-directed 2026-07-19): 'we need durable "
            "decisions so to reduce the vigilance burden of remembering after new features have "
            "been added' -- precedent: the 2026-07-18 Block D merge landed undocumented and "
            "needed a dedicated catch-up pass (rows 1652-1661 vs 1667).",
        hydrates=(
            "Durable decision adopted at world birth (doc-currency-at-the-seam, catalog "
            "tools/setup_tui/durable_decisions.py, why: ledger row 1699): every merge that "
            "changes operator-facing behavior carries its documentation pass in the same work "
            "item or a named-deferral follow-up before the merge row is written."
        ),
        claude_md=(
            "- **Doc currency at the seam** -- every merge that adds or changes operator-facing "
            "behavior carries its documentation pass (user-guide pages, orchlog.d note, README "
            "enumerations) in the same work item, or a named deferral with reason (ledger row "
            "1699)."
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
    # 9. Mined, this repo's ledger/CLAUDE.md: runs are strictly linear.
    DurableDecision(
        slug="runs-are-strictly-linear",
        rule="A run M > N means run N's world is dust and settled: read-only evidence, never "
             "patched, never refreshed, never delta'd. Never propose delta-apply/refresh "
             "against an existing world; a delta reaches reality only by entering the next "
             "world's birth chain.",
        why="maintainer ruling 2026-07-11 (this repo's own CLAUDE.md, ORCHESTRATION section): "
            "the apply-to-existing-world clause and bootstrap/apply-delta.sh's typed-"
            "confirmation ceremony were retired after being witnessed producing cargo-cult "
            "sysadmin work; the run-2 world was itself broken at birth by an unscripted "
            "scaffold-to-/tmp + hand-mv gap.",
        hydrates=(
            "Durable decision adopted at world birth (runs-are-strictly-linear, catalog "
            "tools/setup_tui/durable_decisions.py, why: maintainer ruling 2026-07-11, this "
            "repo's CLAUDE.md ORCHESTRATION section; the run-2 world-broken-at-birth incident): "
            "runs are strictly linear -- an existing world's dust is never patched, refreshed, "
            "or delta'd; a delta reaches reality only via the next world's birth chain."
        ),
        claude_md=(
            "- **Runs are strictly linear** -- a run M > N means run N's world is dust and "
            "settled: read-only evidence, never patched, never refreshed, never delta'd. Never "
            "propose applying a delta to an existing world (maintainer ruling 2026-07-11)."
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

def compile_claude_md(dest_dir: str, fragments: list[str]) -> str:
    """Compiles `fragments` (durable-decision `claude_md` texts, and/or `adr_claude_md_fragment`
    lines, in selection order) into `<dest_dir>/CLAUDE.md` between BEGIN_MARKER/END_MARKER.
    Rules (spec §4), each load-bearing:

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

    Returns the path written."""
    claude_path = os.path.join(dest_dir, "CLAUDE.md")
    existing = ""
    if os.path.isfile(claude_path):
        with open(claude_path, encoding="utf-8") as f:
            existing = f.read()

    body_lines = [
        BEGIN_MARKER,
        "<!-- generated by tools/setup_tui/durable_decisions.py -- do not hand-edit; "
        "regenerate via the setup TUI's hydration screen (screen 8), or "
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
        new_text = pre + section + post
    elif existing:
        sep = "" if existing.endswith("\n") else "\n"
        new_text = existing + sep + "\n" + section + "\n"
    else:
        new_text = section + "\n"

    with open(claude_path, "w", encoding="utf-8") as f:
        f.write(new_text)
    return claude_path
