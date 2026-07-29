#!/usr/bin/env python3
r"""lineage_chain_coverage — mechanizes the class behind work item lineage-chain-lags-directory
(ledger rows 1392/1393): bootstrap/new-project.sh's --new-world birth carries TWO hand-authored
homes for "which kernel/lineage/sNN deltas does a fresh world get" -- (1) the psql `-f` apply
mechanism (the behavioral home), and (2) the LINEAGE_CHAIN narrative string baked into the
world's PROVENANCE header (the documentary home). Nothing before this gate forced those two
homes, or the tracked kernel/lineage/ directory itself, to agree -- the s58/s59/s60 gap (three
authored, scratch-witnessed deltas silently absent from both homes for a full day-plus after
their own merges) is exactly what an agreeing-by-luck pair of hand lists eventually does.

FIX-ROUND REWORK (ledger row 1399, the orchestrator's ratified design for the CLEARED-BUT-
MODERATE-SILENT review's two moderates): home (1), the apply side, is no longer a hand-typed
`-f` list this gate regex-scans -- bootstrap/new-project.sh now GENERATES it, live, from a bash
loop over kernel/lineage/ itself (see that file's own comment immediately above the loop). Home
(2), the LINEAGE_CHAIN narrative, stays hand-authored prose with per-delta ledger citations --
no generator can write it -- and this gate still holds it to the directory by the SAME anchored
scan as before. Since home (1) is no longer literal filenames in text, this gate's apply-side
check changed SHAPE: it no longer asks "is filename X named in the -f list" (the question a
commented-out decoy line could answer YES to, the reviewer's witnessed false-green, F1) -- it
asks "does the generator's source-level CONTRACT still hold": is the generation loop present,
unaltered in its load-bearing lines (glob root, threshold comparison, companion-file exclusion,
and the wiring that actually feeds the generated list to psql), and does its threshold constant
still equal the N>=20 boundary this gate independently asserts as law (the same boundary the
narrative side already enforces). Every one of those checks is an ANCHORED match against a
specific, known line's literal text (stripped leading whitespace required to be the line's own
first characters) -- never a bare substring/whole-file scan -- so a decoy comment (`# for _lf
in ...`) cannot satisfy it: a commented line starts with `#`, not the anchor's required prefix,
and fails every one of these checks exactly as it would fail to satisfy a real interpreter.

NAMING SPACE (verified at authoring time, kernel/lineage/ directory read in full): the directory
holds THREE families of file --
  1. sNN-<slug>.sql  -- an applied kernel DELTA. This gate's subject. One dot before `.sql`.
  2. sNN-<slug>.detect.sql / .verify.sql / .accommodate.sql / .accommodate.verify.sql -- a
     delta's own companion query (a fixture harness reads these directly by full name; they are
     never separately `-f`-applied by the scaffold and never separately named in the narrative --
     the OWNING sNN-<slug>.sql file's own coverage stands in for them). Recognized and excluded
     by the "more than one dot before .sql" shape below, never silently miscounted as a missing
     delta.
  3. Non-sNN files (high_watermark_1.sql, high_watermark_1.detect.sql, nla-schema.sql, s10-s14/
     s17-s19-*.sql, README.md) -- pre-sNN-convention or non-delta files. high_watermark_1.sql IS
     applied by the scaffold (the fixed leading `-f`, outside the generated loop) but is
     deliberately OUT of this gate's quantification universe: it predates the `sNN-` naming
     convention this gate polices, and the ledger commission's own words scope the mechanization
     to "every kernel/lineage/sNN-*.sql tracked file". s10-s14 and s17-s19 are also out of THIS
     gate's universe, for a DIFFERENT and CORRECTED reason from an earlier draft of this docstring
     (fix-round finding 3, re-verified 2026-07-26 against kernel/lineage/high_watermark_1.sql's
     own header): there is no separate earlier scaffold stage that applies them. s15/s17/s19
     arrive TRANSITIVELY via high_watermark_1.sql's own `\ir` chain (that file's header: "\ir
     s15-schema.sql", "\ir s17-stamp-mechanism.sql", "\ir s17-independence-vocabulary.sql", "\ir
     s19-trigger-search-path.sql"); s18-criterion-principals.sql is excluded there BY NAME as
     Study-mode-only apparatus, not part of the kernel a downstream user stands up (that file's
     own "DELIBERATELY EXCLUDED" note); s10-s14 are dead/superseded pre-consolidation schema
     iterations, applied by nothing in the current scaffold at all. All of s10-s19 are therefore
     out of this gate's universe because they are not separately-generated/-narrated sNN deltas
     of the consolidated loop this gate polices -- not because some other scaffold stage owns
     them.

CLOSURE STATEMENT (ADR-0000 Rule 2a) -- stated per HOME, since the two homes are now checked by
structurally different mechanisms and claim different things:
  - NARRATIVE HOME (unchanged in shape from the prior build):
    INVARIANT: for every git-tracked kernel/lineage/sNN-<slug>.sql delta file whose numeric N is
    >= MIN_N, the literal string "kernel/lineage/sNN-<slug>.sql" appears at least once inside the
    LINEAGE_CHAIN="..." assignment line in bootstrap/new-project.sh's `--new-world` branch.
    QUANTIFICATION UNIVERSE: every file under kernel/lineage/ matching `^s(\d+)-.+\.sql$` with
    exactly one `.` (excluding `.detect.sql`/`.verify.sql`/`.accommodate.sql`/
    `.accommodate.verify.sql` companions) and N >= MIN_N, as returned by `git ls-files
    kernel/lineage/`. This is a precise, textual claim: the string is proven present or proven
    absent, no inference.
  - GENERATOR-CONTRACT HOME (the reworked apply-side check -- NOT the same shape of claim):
    INVARIANT: bootstrap/new-project.sh contains ALL of the following, each matched by its own
    anchored regex requiring the match to BE the (whitespace-stripped) line, never merely occur
    inside it: (a) the delta-glob loop header iterating `kernel/lineage/s[0-9]*-*.sql` -- the
    unnarrowed glob that would enumerate every sNN file, no digit-range restriction; (b) the
    four-suffix companion-file exclusion case arm, byte-identical to the one guarding this gate's
    own DELTA_RE semantics; (c) the `-ge`-against-`_LINEAGE_APPLY_MIN_N` threshold comparison
    that actually gates inclusion; (d) the `_apply_lineage_deltas` function definition, its bare
    invocation, and its `"$@"` psql wiring -- proof the generated argument list is fed to psql,
    not computed and discarded; AND that the scaffold's own `_LINEAGE_APPLY_MIN_N=<N>` constant
    equals MIN_N below (this gate's own asserted law for where the consolidated loop begins,
    justified in NAMING SPACE above and unchanged from the prior build's own threshold).
    WHAT THIS PROVES: the generator's load-bearing STRUCTURE is present and un-narrowed, and its
    threshold agrees with this gate's independently-asserted law. WHAT THIS DOES NOT PROVE (the
    honest edge, disclosed rather than hidden): this is a source-level contract check, not an
    execution of the shell -- it does not run the loop and does not verify runtime behavior (a
    change to unlisted logic, e.g. a `continue` inserted elsewhere in the loop body, or a
    directory-root substitution NOT on one of the anchored lines, is outside what these anchors
    catch). This is the same class of edge every static-analysis contract check in this project
    accepts and states rather than hides (compare the narrative-side's own textual-presence-only
    claim, which likewise proves nothing about what actually gets APPLIED at runtime -- text
    presence, not execution, is what either half of this gate can ever certify).
  - DENOMINATION: the narrative home reports one violation per missing delta (as before). The
    generator-contract home reports one violation per broken/missing anchor, plus one (if
    triggered) for a threshold-constant mismatch -- never collapsed into a vaguer summary line.

READ MODE: bootstrap/new-project.sh is read via gates/_staged_read.py's shared primitive (STAGED
bytes by default, `--tree` forces the working-tree read) -- the same gates-staged-vs-tree-
blindness discipline (ledger row 1234) every other content-checking gate in this chain follows:
a commit that stages a new kernel/lineage/sNN file but leaves new-project.sh's wiring unstaged
(or reverts it in the tree after staging a broken version) must be judged on what the COMMIT
itself would carry, not on whatever bytes happen to sit in the tree at gate-run time. The
DIRECTORY LISTING (which sNN files exist) is read via `git ls-files` -- the tracked set, not an
`os.listdir` sweep -- so an untracked scratch file never manufactures a false violation and a
file staged for deletion is not still counted as present (ADR-0012 P1: one authoritative source,
never a disk-shape heuristic).

Exit 0 clean; exit 1 listing every gap/broken-anchor, teaching the exact place(s) in
bootstrap/new-project.sh a fix needs to touch.
Lazy imports are banned.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _staged_read import read_source_text  # noqa: E402  (gates/_staged_read.py, shared home)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bootstrap"))
from lineage_manifest import (  # noqa: E402  (bootstrap/lineage_manifest.py, shared home)
    DELTA_RE, MIN_N, git_tracked_lineage_deltas,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAFFOLD = os.path.join(ROOT, "bootstrap", "new-project.sh")

# DELTA_RE (a plain delta file: sNN-<slug>.sql, exactly one dot -- companions like .detect.sql
# have a second dot before the final .sql and are excluded by requiring no further '.' in <slug>)
# and MIN_N (the consolidated apply loop this gate polices starts at s20 -- s10-s14/s17-s19 are
# pre-consolidation / transitively-applied-elsewhere, see NAMING SPACE) are now imported from
# bootstrap/lineage_manifest.py -- the ONE shared home for this selection rule (migrate_core.py's
# `_manifest()` imports the same constants; migrate-manifest-glob-drift fix, work item 430,
# closed the two independently-drifting copies this gate's own docstring above already warns
# against). MIN_N is still cross-checked below against the scaffold's own `_LINEAGE_APPLY_MIN_N`
# threshold CONSTANT in the shell text -- that check is about the SHELL agreeing with this
# module's law, not about two Python copies agreeing with each other, and stays unchanged.

# Principled exclusions -- see the module docstring's NAMING SPACE section. Keyed by basename.
EXCLUDE_FILES: set[str] = set()

# --- Generator-contract anchors (bootstrap/new-project.sh's generation loop) ------------------
# Each entry: (label, compiled anchored regex). re.MULTILINE, `^\s*` allows leading indentation
# but the match must otherwise BEGIN the line -- a line commented out with a leading `#` cannot
# satisfy any of these (the exact false-green vector F1 witnessed against the prior hand-typed
# `-f` scan; this shape structurally cannot repeat it, since `#...` never matches `^\s*for `,
# `^\s*_LINEAGE_APPLY_MIN_N=`, etc.).
GENERATOR_ANCHORS: list[tuple[str, re.Pattern[str]]] = [
    ("delta-glob loop header (unnarrowed kernel/lineage/s[0-9]*-*.sql)",
     re.compile(r'^\s*for _lf in "\$AUTOHARN_ROOT"/kernel/lineage/s\[0-9\]\*-\*\.sql; do\s*$',
                re.MULTILINE)),
    ("companion-file exclusion case arm (4 suffixes)",
     re.compile(r'^\s*\*\.detect\.sql\|\*\.verify\.sql\|\*\.accommodate\.sql'
                r'\|\*\.accommodate\.verify\.sql\)\s*continue\s*;;\s*$', re.MULTILINE)),
    ("threshold comparison (-ge against the threshold constant)",
     re.compile(r'^\s*\[ "\$_ln" -ge "\$_LINEAGE_APPLY_MIN_N" \] \|\| continue\s*$',
                re.MULTILINE)),
    ("apply-function definition (_apply_lineage_deltas)",
     re.compile(r'^\s*_apply_lineage_deltas\(\) \{\s*$', re.MULTILINE)),
    ("apply-function invocation (bare call, not merely defined)",
     re.compile(r'^\s*_apply_lineage_deltas\s*$', re.MULTILINE)),
    ("generated args wired to psql (trailing \"$@\")",
     re.compile(r'^\s*"\$@"\s*$', re.MULTILINE)),
]

THRESHOLD_CONST_RE = re.compile(r'^\s*_LINEAGE_APPLY_MIN_N=(\d+)\s*$', re.MULTILINE)


def tracked_lineage_deltas() -> list[str]:
    """Every git-tracked kernel/lineage/sNN-<slug>.sql delta basename (N >= MIN_N), sorted by N.
    The enumeration+filter+sort itself is bootstrap/lineage_manifest.py's shared
    `git_tracked_lineage_deltas()` (routed through `_staged_read.run_git`, not a bare subprocess
    call, for the same GIT_DIR-inheritance robustness every other converted gate in this chain
    shares); EXCLUDE_FILES stays this gate's own extension point, applied as a post-filter."""
    deltas = git_tracked_lineage_deltas(Path(ROOT), min_n=MIN_N)
    return [b for b in deltas if b not in EXCLUDE_FILES]


def narrative_files(text: str) -> set[str]:
    """Basenames named inside the LINEAGE_CHAIN="..." assignment (the --new-world branch) --
    isolated by locating that one (very long) assignment line and scanning only its own text, so
    a file mentioned merely in an unrelated comment elsewhere in the script is never miscounted
    as narrative coverage. Unchanged from the prior build -- this home stays hand-authored prose,
    per row 1399's ratified design, and this scan's shape was never the F1 finding's subject."""
    m = re.search(r'^\s*LINEAGE_CHAIN="s15 ->.*$', text, re.MULTILINE)
    if not m:
        return set()
    line = m.group(0)
    return set(re.findall(r'kernel/lineage/([A-Za-z0-9_.-]+\.sql)', line))


def generator_contract_violations(text: str) -> list[str]:
    """Verify the GENERATOR's own source-level contract (see module docstring's closure
    statement) rather than scanning for literal filenames -- there is no more literal `-f`
    filename list to scan; the apply side is now a runtime-generated loop. Returns one message
    per broken/missing anchor or threshold mismatch; empty list means the contract holds."""
    violations: list[str] = []

    for label, pattern in GENERATOR_ANCHORS:
        if not pattern.search(text):
            violations.append(
                f"generator-contract anchor MISSING or altered: {label} -- expected an exact "
                f"(un-commented) line matching this shape in bootstrap/new-project.sh's "
                f"apply-loop block; the psql -f apply mechanism cannot be confirmed intact.")

    m = THRESHOLD_CONST_RE.search(text)
    if m is None:
        violations.append(
            "generator-contract anchor MISSING: the _LINEAGE_APPLY_MIN_N=<N> threshold constant "
            "assignment line was not found (un-commented) -- cannot confirm which deltas the "
            "generator would include.")
    else:
        scaffold_min_n = int(m.group(1))
        if scaffold_min_n != MIN_N:
            violations.append(
                f"generator-contract threshold MISMATCH: bootstrap/new-project.sh's "
                f"_LINEAGE_APPLY_MIN_N={scaffold_min_n} does not equal this gate's own asserted "
                f"law MIN_N={MIN_N} (see module docstring's NAMING SPACE) -- deltas with "
                f"{min(scaffold_min_n, MIN_N)} <= N < {max(scaffold_min_n, MIN_N)} would be "
                f"silently {'excluded from' if scaffold_min_n > MIN_N else 'included in'} a "
                f"fresh --new-world birth's apply set relative to this gate's law.")

    return violations


def main() -> int:
    use_tree = "--tree" in sys.argv[1:]
    deltas = tracked_lineage_deltas()
    text = read_source_text(Path(SCAFFOLD), use_tree=use_tree)
    narrated = narrative_files(text)
    contract_violations = generator_contract_violations(text)

    missing_narrative = [d for d in deltas if d not in narrated]

    print(f"lineage-chain-coverage: {len(deltas)} tracked kernel/lineage/sNN-*.sql delta(s) "
          f"(N >= {MIN_N}) checked against bootstrap/new-project.sh's generated apply loop "
          f"contract and LINEAGE_CHAIN narrative.")

    if not contract_violations and not missing_narrative:
        print("lineage-chain-coverage: clean ✓")
        return 0

    if contract_violations:
        print(f"\n  {len(contract_violations)} generator-contract violation(s) "
              f"(the psql apply mechanism's own source-level contract, see module docstring):")
        for v in contract_violations:
            print(f"    !! {v}")
    if missing_narrative:
        print(f"\n  {len(missing_narrative)} delta(s) MISSING from the LINEAGE_CHAIN narrative "
              f"string (a fresh world's own PROVENANCE header would misreport its birth chain):")
        for d in missing_narrative:
            print(f"    !! kernel/lineage/{d}")

    print(f"\nlineage-chain-coverage: fix the generator loop's altered/missing line(s) named "
          f"above (bootstrap/new-project.sh, the block starting \"THE APPLY LIST IS GENERATED\") "
          f"and/or add each missing file's own 'kernel/lineage/<file>' mention (arrow entry + "
          f"\"via\" file list + a per-delta prose bullet in the established voice) to the "
          f"LINEAGE_CHAIN=\"...\" assignment, both in bootstrap/new-project.sh.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
