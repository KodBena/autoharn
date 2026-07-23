#!/usr/bin/env python3
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

CONTENT SPLIT (law/adr/0012's 2026-07-22 Amendment, P10 -- "data is not code", design/
FABLE-SETUP-TUI-FIELD-STRATEGY.md Track 2.2, phase 1): each entry's `rule`/`why`/`hydrates`/
`claude_md` prose used to live as literal DurableDecision(...) constructor calls in THIS file --
63% of it by volume, a writing edit (correcting a citation, rewording a rule for a stranger
audience) indistinguishable in the diff from a logic edit to `compute_claude_md_text`. That
content, plus its per-entry curation comments (the numbered "mined from..."/"REWRITTEN per the
genericity critique" annotations), now lives in tools/setup_tui/durable_decisions_data.py's
`RAW_CATALOG` (a data-only module: typed literals, zero functions, zero logic) and is assembled
into the typed `CATALOG` below by one line of pure wiring. The DurableDecision dataclass
DEFINITION stays here -- the logic-side contract P10 leaves with logic, not content. This
preamble comment block (the catalog's overall curation methodology, as opposed to any one
entry's own history) stays here too, since it is commentary about the split/curation as a whole,
not about one entry's content. Every consumer's import path (`durable_decisions.CATALOG`,
`durable_decisions.DurableDecision`, `list_adrs`, `compute_claude_md_text`,
`hydration_claude_md_write_act`) is UNCHANGED.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import here is top of file.
"""
from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path

from tools.configtree import DescriptionElement, PROVENANCE_LABEL
from tools.setup_tui import content
from tools.setup_tui.plan import Hole, WriteAct

REPO_ROOT = Path(__file__).resolve().parents[2]
ADR_DIR = REPO_ROOT / "law" / "adr"

BEGIN_MARKER = "<!-- BEGIN COMPILED DURABLE DECISIONS (setup_tui) -->"
END_MARKER = "<!-- END COMPILED DURABLE DECISIONS (setup_tui) -->"


@dataclass(frozen=True)
class DurableDecision:
    """`why`/`provenance`/`maintainer_refs` SCHEMA (round 6, ledger row 1117 -- companion rule
    C13; round 7 audience-boundary split, ledger row 1119, defect D2): `why` is ONE short,
    citation-free sentence; `provenance` lists citations a FOUNDING OPERATOR could actually open
    and read (this repo's own user-guide/*, law/adr/*, or a public external link), rendered
    demoted, LAST, one `PROVENANCE_LABEL` element per path; `maintainer_refs` lists
    INTERNAL-ONLY citations (bare ledger-row numbers, autoharn-panel prior art) -- NEVER rendered
    by any widget, kept only for the maintainer's own audit trail. `rule`/`hydrates`/`claude_md`
    are unchanged: literal artifact TEXT (a ledger-decision statement, a CLAUDE.md fragment), not
    interactive elucidation."""
    slug: str
    rule: str
    why: str
    hydrates: str      # the exact `led decision` statement this selection writes
    claude_md: str      # the fragment compiled into the new world's CLAUDE.md
    provenance: tuple[str, ...] = ()
    maintainer_refs: tuple[str, ...] = ()

    def elements(self) -> "tuple[DescriptionElement, ...]":
        """The interactive elucidation rendering: `why` first (unlabeled connective prose, D7/
        D8), then each OPERATOR-relevant `provenance` path, demoted, LAST -- `maintainer_refs`
        is never read here at all. `steps_hydration.py`'s own MultiChoiceField `option_help`
        uses this instead of a bare `decision.why` string."""
        out = [self.why]
        out.extend(DescriptionElement(PROVENANCE_LABEL, p) for p in self.provenance)
        return tuple(out)


# ---------------------------------------------------------------------------------------------
# Initial catalog -- 7 to 15 entries, DISTILLED from the prior art of BOTH projects (amendment
# per commission ledger row 1716, superseding this spec's original three-plus-proposals shape;
# see design/FABLE-SETUP-TUI-FEATURE-FACTS-SPEC.md §3). Mined read-only from two evidence
# sources: this repo's own ledger (`./led show <id>`) and the autoharn-panel LIVE deployment at
# /home/bork/w/vdc/1/experience/autoharn-panel (its CLAUDE.md file, and its live Postgres ledger
# schema `experience`/`experience_kernel` on host 192.168.122.1 db toy, read via plain SELECT --
# never a write, per the never-touch-a-user-project rule). Every entry (tools/setup_tui/
# durable_decisions_data.py's RAW_CATALOG, P10 content split below) cites its specimen so the
# maintainer can verify the distillation; the report accompanying this build lists the additional
# candidates that were mined but NOT wired in, for pruning/addition.
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
# (each entry's own per-entry comment in RAW_CATALOG marks its own rewrite inline; `why`
# citations kept exactly as banked -- the citations are the evidence, they stay local); three
# entries the critique flagged as more portable than several that made the original cut WIRED
# (`claims-carry-witnesses`, `unanchored-review-briefs`, `fresh-context-review-for-delegated-
# work`), each in generic voice from the start.
#
# 14 entries total (13 fixed DurableDecision structs in RAW_CATALOG -- the 14th, row 1915's
# polychotomy-option-space-justification, added 2026-07-22 -- + the ADR-adoption submenu just
# after this construction) -- inside the 7-15 range, 15 is a hard ceiling not approached.
# ---------------------------------------------------------------------------------------------

CATALOG: list[DurableDecision] = [
    DurableDecision(**{**entry, "provenance": tuple(entry.get("provenance", ())),
                       "maintainer_refs": tuple(entry.get("maintainer_refs", ()))})
    for entry in content.DURABLE_DECISIONS
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
        if "-appendix-" in path.stem:
            # A provisional appendix (e.g. 0019-appendix-provisional-ui-proscriptions.md) is NOT
            # itself an adoptable ADR -- it shares its parent ADR's own number in its title line
            # (both start "# ADR-0019 ..."), which would otherwise mint a SECOND catalog entry
            # under the SAME ADR number (a live crash: two options claiming one identity --
            # `tools.configtree.fields.MultiChoiceField`'s own construction-time duplicate-value
            # refusal is what caught this). The maintainer adopts an appendix by adopting its
            # parent ADR; excluding it here is a named, reviewable choice, not a silent drop.
            continue
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


@dataclass(frozen=True)
class AdrSynopsisDrift:
    """One STALE synopsis -- its own `source_sha256` (recorded at authoring time) no longer
    matches the ADR file's CURRENT bytes. Named, not a bare tuple (the maintainer's standing "no
    bare types" rule, ledger row 1105) -- a stale synopsis is one distinct, checkable fact, not
    three loose strings a caller has to remember the order of."""
    number: str
    declared_sha256: str
    actual_sha256: str


class AdrSynopsisMissingError(RuntimeError):
    """A cataloged ADR (one `list_adrs()` names) has NO synopsis entry in `adr_synopses.toml` at
    all -- a construction-time refusal (ADR-0002 rule 1), never a silent gap an operator
    discovers only by noticing an unusually-terse hydration checkbox."""


def check_adr_synopsis_freshness(
    *, adrs: "list[tuple[str, str, str]] | None" = None,
    hashes: "dict[str, str] | None" = None,
    read_bytes: "object | None" = None,
) -> "tuple[list[str], list[AdrSynopsisDrift]]":
    """DRIFTABILITY (maintainer question, 2026-07-22: "the ADR-adoption catalog derives live
    from law/adr/*.md ... but adr_synopses.toml is static and already stale twice today").
    Returns `(missing, stale)`: `missing` -- ADR numbers `list_adrs()` (or an injected
    equivalent) names that have NO synopsis hash recorded at all; `stale` -- one
    `AdrSynopsisDrift` per synopsis whose OWN declared `source_sha256` no longer matches the ADR
    file's CURRENT bytes. INJECTABLE (the SAME house idiom `feature_facts.check_registry` already
    uses, seen-red/setup-tui-feature-facts-drift's own fixture: a fixture feeds a SYNTHETIC
    `adrs`/`hashes`/`read_bytes` without mutating this module's real globals, so a red leg never
    corrupts the real catalog) -- called with no arguments, it checks the REAL catalog against
    the REAL recorded hashes. NEVER RAISES itself -- the caller decides what MISSING vs STALE
    means for its own run (see `validate_adr_synopsis_freshness`, the real wired case: a
    construction-time refusal for MISSING, a loud but non-fatal warning for STALE)."""
    adrs = adrs if adrs is not None else list_adrs()
    hashes = hashes if hashes is not None else content.ADR_SYNOPSIS_HASHES
    read_bytes = read_bytes or (lambda relpath: (REPO_ROOT / relpath).read_bytes())
    missing: list[str] = []
    stale: list[AdrSynopsisDrift] = []
    for number, _title, relpath in adrs:
        declared = hashes.get(number)
        if declared is None:
            missing.append(number)
            continue
        actual = hashlib.sha256(read_bytes(relpath)).hexdigest()
        if actual != declared:
            stale.append(AdrSynopsisDrift(number=number, declared_sha256=declared,
                                           actual_sha256=actual))
    return missing, stale


def validate_adr_synopsis_freshness() -> "tuple[AdrSynopsisDrift, ...]":
    """The REAL, wired check (called once at TUI start, `tools.setup_tui.app.main`): REFUSES
    loudly (`AdrSynopsisMissingError`, naming every missing number at once, never a first-one-
    wins early exit) if any cataloged ADR has no synopsis hash recorded at all; otherwise
    returns every STALE entry for the caller to render as a loud, NON-FATAL warning naming both
    hashes -- a stale synopsis awaits a human re-derivation pass, it must not brick setup while
    that pass is pending (the maintainer's own ruling, this fix's commission)."""
    missing, stale = check_adr_synopsis_freshness()
    if missing:
        raise AdrSynopsisMissingError(
            f"tools/setup_tui/durable_decisions.py: {len(missing)} cataloged ADR(s) have NO "
            f"synopsis entry in adr_synopses.toml at all: {sorted(missing)} -- every adoptable "
            f"ADR needs an authored synopsis row (even a '(synopsis pending maintainer review)' "
            f"placeholder, stamped with its own source_sha256) before the hydration screen can "
            f"start.")
    return tuple(stale)


_ADR_SYNOPSIS_PENDING = "(synopsis pending maintainer review)"


def adr_synopsis_elements(number: str, relpath: str) -> "tuple[DescriptionElement, ...]":
    """The ADR-adoption submenu's own per-entry elucidation (maintainer round-6 addendum: "a
    pointer is not an elucidation ... helpful only to someone who already knows every ADR").
    ORIENTATION, NOT THE LAW (content.py's own `adr_synopses.toml` header note): a 1-3 sentence
    digest of what the ADR binds you to if adopted, authored by lifting/lightly trimming the
    ADR's own words -- `content.ADR_SYNOPSES` is the one home for that text (data, never
    hardcoded here). A number with no authored synopsis reads the honest pending-review marker,
    never a fabricated one. The file-path pointer is a SEPARATE, final element -- it follows the
    synopsis, it does not replace it."""
    synopsis = content.ADR_SYNOPSES.get(number, _ADR_SYNOPSIS_PENDING)
    return (DescriptionElement("Synopsis", synopsis), DescriptionElement("File", relpath))


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
