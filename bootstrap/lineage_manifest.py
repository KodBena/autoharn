#!/usr/bin/env python3
"""bootstrap/lineage_manifest.py -- the ONE shared home (ADR-0012 P1) for "which
kernel/lineage/sNN-<slug>.sql delta basenames does bootstrap/new-project.sh's --new-world glob
loop select, and in what order". This is the MATCHING RULE (regex shape, N >= MIN_N threshold,
companion-suffix exclusion, numeric sort) that new-project.sh's own bash loop implements and
gates/lineage_chain_coverage.py polices, from the source-text side, against that same shell --
re-implemented here ONCE so this project's two Python consumers stop authoring their own copies.

WHY THIS EXISTS (migrate-manifest-glob-drift, GxP survey 3 H2, HIGH, fail-dangerous): before this
module, bootstrap/migrate_core.py's `_manifest()` regex-scanned new-project.sh's OLD hand-typed
`psql -f "kernel/lineage/<file>.sql"` invocation lines for the ordered delta list. That invocation
shape stopped existing when new-project.sh's apply list became a live glob loop over the
directory (ledger rows 1392/1393/1399, work item lineage-chain-lags-directory) -- migrate_core's
regex kept matching SYNTACTICALLY (it still found one line: the literal, still-present
`high_watermark_1.sql` `-f` flag) but silently produced a ONE-ENTRY manifest instead of refusing.
Every downstream reader of that manifest inherited the false-clean answer: serving/
boundary_service.py's `_lineage_head` reported "high_watermark_1" as the lineage head for every
world regardless of true generation, and migrate_core's own `_current_head_and_missing` found
nothing missing and printed "already at the lineage head", exit 0, with ~50 deltas unapplied.
gates/lineage_chain_coverage.py was rewritten for the new glob-loop shape at the time of that
fix-round (row 1399); migrate_core.py was the missed second consumer. This module gives both
Python consumers ONE shared derivation, so they cannot drift apart from each other again --
though each still supplies its OWN candidate source (see `disk_lineage_deltas` vs
`git_tracked_lineage_deltas` below), because the two ask genuinely different questions (see each
function's own docstring).

WHAT THIS MODULE DOES NOT OWN: bootstrap/new-project.sh's own shell loop stays authoritative for
ITSELF (CLAUDE.md orchestration ruling: "the shell stays authoritative for itself") -- nothing
here is imported by the shell, and nothing here runs it. This module re-implements the SAME
selection rule in Python; gates/lineage_chain_coverage.py's own GENERATOR_ANCHORS block (source-
text anchor checks against new-project.sh, unchanged by this fix) is what actually proves the
shell's own bytes still match this rule's shape (glob root, exclusion arms, threshold comparison,
apply wiring) -- catching drift in the OTHER direction (shell changed, this module's rule silently
didn't) that this module cannot see by construction, since it never reads new-project.sh's bytes.

SELECTION RULE (mirrors new-project.sh's `for _lf in "$AUTOHARN_ROOT"/kernel/lineage/s[0-9]*-*.sql`
loop body exactly): a basename is selected iff it matches `sNN-<slug>.sql` -- exactly one dot
before the final `.sql` (a `.detect.sql`/`.verify.sql`/`.accommodate.sql`/`.accommodate.verify.sql`
companion carries a second dot and is excluded by the regex's own shape, never a separate suffix
check -- identical in effect to new-project.sh's explicit `case` exclusion arm and to gates/
lineage_chain_coverage.py's own DELTA_RE, now this module's one authored copy of that pattern) --
with numeric N >= MIN_N. Duplicates (should never occur: git and the filesystem each hold at most
one file per basename) are defensively de-duplicated, first occurrence wins. Sort is NUMERIC by N
(the s9-vs-s10 lexical-sort class bug avoided), matching new-project.sh's own `sort -t: -k1,1n`.

HIGH_WATERMARK is applied FIRST by new-project.sh's own `_apply_lineage_deltas` (the fixed,
leading `-f "$AUTOHARN_ROOT/kernel/lineage/high_watermark_1.sql"` on the psql invocation, placed
BEFORE the generated `"$@"` s20+ argument list) -- `apply_order()` below reproduces that exact
placement; it is never folded into the N >= MIN_N selection above (high_watermark_1.sql predates
the `sNN-` naming convention entirely and is matched by neither the shell's glob nor this
module's DELTA_RE).

Stdlib-only, top-of-file imports (gates/no_lazy_imports.py's ban on runtime-deferred imports).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_GATES_DIR = Path(__file__).resolve().parent.parent / "gates"
sys.path.insert(0, str(_GATES_DIR))
from _staged_read import run_git  # noqa: E402  (gates/_staged_read.py, shared git-subprocess primitive, ADR-0012 P1)

# The exact matching shape new-project.sh's glob loop body implements -- identical regex to
# gates/lineage_chain_coverage.py's own (former) DELTA_RE, which now imports this one.
DELTA_RE = re.compile(r"^s(\d+)-[A-Za-z0-9_-]+\.sql$")

# Must equal new-project.sh's own `_LINEAGE_APPLY_MIN_N=20` constant -- gates/
# lineage_chain_coverage.py's generator_contract_violations() cross-checks the shell's literal
# constant against this same value (imported from here), so this module's MIN_N and that check
# can never silently drift apart -- both claim to describe the SAME shell loop from different
# angles (this module: the selection rule Python re-implements; that gate: proof the shell's own
# text still matches this shape).
MIN_N = 20

HIGH_WATERMARK = "high_watermark_1.sql"


def select_lineage_deltas(basenames, min_n: int = MIN_N) -> list[str]:
    """Filter+sort an iterable of candidate basenames per the SELECTION RULE above. Pure function
    -- no filesystem/git access of its own; callers supply candidate basenames from whichever
    source matches the question THEY are asking (see `disk_lineage_deltas` and
    `git_tracked_lineage_deltas` below for this module's own two sources)."""
    seen: set[str] = set()
    numbered: list[tuple[int, str]] = []
    for base in basenames:
        m = DELTA_RE.match(base)
        if not m:
            continue
        n = int(m.group(1))
        if n < min_n:
            continue
        if base in seen:
            continue
        seen.add(base)
        numbered.append((n, base))
    numbered.sort(key=lambda t: t[0])
    return [base for _, base in numbered]


def apply_order(deltas: list[str]) -> list[str]:
    """Prepend HIGH_WATERMARK -- new-project.sh's own psql invocation applies it FIRST, before
    the generated s20+ argument list (see that script's `_apply_lineage_deltas`). `deltas` is
    expected to already be in the SELECTION RULE's numeric-N order (both this module's own
    producers already return it that way)."""
    return [HIGH_WATERMARK, *deltas]


def disk_lineage_deltas(lineage_dir: Path, min_n: int = MIN_N) -> list[str]:
    """The SAME candidate source new-project.sh's own shell glob reads at birth time: whatever
    `sNN-*.sql` files sit in `lineage_dir` on disk RIGHT NOW. Deliberately a directory listing,
    not `git ls-files` -- a bash glob does not consult git, so an uncommitted-but-staged (or even
    fully untracked) delta file a birth would still pick up must not be invisible here. This is
    the source bootstrap/migrate_core.py's `_manifest()` uses: "what would a fresh birth actually
    apply if it ran right now" is the question migrate needs answered, matching new-project.sh's
    own runtime behavior exactly rather than the (deliberately different) tracked-only view
    below."""
    return select_lineage_deltas(
        (p.name for p in lineage_dir.glob("s[0-9]*-*.sql")), min_n=min_n)


def git_tracked_lineage_deltas(repo_root: Path, min_n: int = MIN_N) -> list[str]:
    """The TRACKED-only view (`git ls-files`, routed through gates/_staged_read.py's `run_git`
    for its GIT_DIR-stripped-env robustness, ADR-0012 P1 -- no second git subprocess wrapper
    authored here). This is gates/lineage_chain_coverage.py's own question ("what has this COMMIT
    actually shipped", the narrative-coverage check's quantification universe), and also
    migrate_core.py's plausibility-floor cross-check: a disk listing (`disk_lineage_deltas`) that
    comes back SHORTER than the tracked set is a broken/incomplete checkout (a submodule not
    updated, a partial extraction), not a legitimately smaller lineage -- see migrate_core.py's
    own `_manifest()` docstring for how that floor is applied and why."""
    r = run_git(["-C", str(repo_root), "ls-files", "kernel/lineage/"],
                capture_output=True, text=True, check=True)
    basenames = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        basenames.append(Path(line).name)
    return select_lineage_deltas(basenames, min_n=min_n)
