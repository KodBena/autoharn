#!/usr/bin/env python3
r"""lineage_reissue_lineage -- a mechanical DETECTOR for the class behind the s61 defect (ledger
row 1430, s63's own commission, design/FABLE-S63-SUPERSESSION-BODY-RESTORATION-SPEC.md §3; see
ENFORCEMENT STATUS below for what "mechanical" does and does not mean here): a
`kernel/lineage/sNN-*.sql` delta that RE-ISSUES (`CREATE OR REPLACE FUNCTION`) a function some
EARLIER delta already defined, but names the WRONG prior re-issue as its base -- silently
dropping every branch the true immediately-prior re-issue had added since. s61 Element 7
re-issued `validate_supersession_target` claiming "Base body = s45's (UNCHANGED by s60)" when
the actual immediately-prior re-issue was s58 Element 5 (s53 and s58 both landed between s45 and
s61) -- so s61's `CREATE OR REPLACE` silently deleted s53's belief branch and all three of s58's
missive branches while adding its own (correct, wanted) symmetry block. The claim was never
FALSE in the sense of citing a nonexistent file -- s45 is real and IS an ancestor -- it was
STALE: the wrong ancestor, two re-issues behind the true one.

THE INVARIANT (ADR-0000 Rule 2a closure statement, part 1): for every function name F defined by
`CREATE (OR REPLACE) FUNCTION :"schema".F` more than once across the tracked
`kernel/lineage/sNN-<slug>.sql` delta files (in numeric order), every re-issue AFTER THE FIRST
must name the immediately-prior re-issue's own delta number in its own header comment -- the
comment block directly attached to that specific `CREATE OR REPLACE` statement, never a bare
whole-file scan (see HEADER-BLOCK EXTRACTION below for why: a whole-file scan would have passed
s61's own defect).

QUANTIFICATION UNIVERSE (ADR-0000 Rule 2a closure statement, part 2): every function name
defined via `CREATE (OR REPLACE) FUNCTION :"schema".<name>` in more than one tracked
`kernel/lineage/s(\d+)-[A-Za-z0-9_-]+\.sql` delta file with N >= MIN_N (the same DELTA_RE shape
gates/lineage_chain_coverage.py already polices; its own four-suffix companion exclusion applies
here identically -- a `.detect.sql` fixture query is never itself a re-issue). Argument lists /
overload signatures are NOT distinguished -- this gate keys on the bare function NAME, the same
granularity the s61 defect itself occurred at (a same-name re-issue is always a full body
replacement in this codebase's own house idiom: ADR-0012 P1, "one home", means a function is
never overloaded to carry two live bodies side by side here).

MIN_N = 43 -- NAMED, not silent (ADR-0000's Rule-2(a) sharpening: a deliberately-uncovered axis
is disclosed, never left an invisible gap). Verified empirically against this gate's own first
run (--tree, pre-s63): every re-issue below s43 that this gate's mechanism would otherwise flag
(s19/set_actor citing s15; s21/validate_amends, validate_answers, validate_review, all citing
s15; s21/validate_independence citing s17; s29/validate_independence citing s21;
s42/compute_row_hash citing s26) predates the per-object base-citation discipline entirely --
none of their own files, checked by hand, name their true prior re-issue anywhere, including in
the file's own opening banner. The discipline itself is NAMED first at s43 (kernel/lineage/
s43-typed-verdict-write-boundary.sql's own PREREQUISITE paragraph, "matching every prior
PREREQUISITE precedent") and formalized as THE HEAD-BODY RULE at s45 ("spec §2, the builder's own
most important standing instruction... For EVERY object this delta re-issues, the base body is
the LINEAGE HEAD's declaration at build time") -- s43 is this gate's own asserted law for where
detection begins, matching lineage_chain_coverage.py's own MIN_N precedent (a threshold below
which a hand-authored convention this gate wants to check did not yet exist to violate). A
retroactive citation-repair sweep of the pre-s43 files is explicitly NOT
this gate's job (ADR-0000: "no retroactive sweep... not a license to roam the tree re-typing
existing code" / ADR-0005 Rule 8: frozen records are not retro-edited) -- filed here as a named,
disclosed gap, not silently patched over.

HEADER-BLOCK EXTRACTION (the mechanism, anchored, never a bare whole-file substring scan -- see
THE INVARIANT above for why a whole-file scan was rejected): a re-issue's citation is searched in
the UNION of two bounded windows, never the whole file.
  (1) THE LOCAL ELEMENT WINDOW: walking BACKWARD from the `CREATE (OR REPLACE) FUNCTION` line,
      collect contiguous `--`-prefixed comment lines, stopping (inclusive) at the first line
      matching `^--\s*ELEMENT\s+\d+\b` (this project's own established per-object header marker
      -- s43/s45/s53/s58/s61 all open their validate_supersession_target re-issues with exactly
      this shape) or at a `MAX_WINDOW`-line cap, whichever comes first; a non-comment, non-blank
      line stops the walk WITHOUT being included (the block's true top). Walking through an
      ELEMENT marker into the PRIOR element's own prose would let that prior element's citations
      leak in and manufacture a false pass, so the marker line itself is the hard stop.
  (2) THE FILE-OPENING WINDOW: the file's own leading comment banner, line 1 through the first
      non-comment line (the ADR-0006 header convention every lineage file already carries; the
      PREREQUISITE/HEAD-BODY-RULE paragraph a delta's own citation of its dependency typically
      lives in, e.g. s62's Element 2 re-issue of validate_entitlement names "s60's trigger body"
      only in this opening banner, never inside its own local Element 2 block -- window (1) alone
      would have false-flagged a correct citation there).

DENOMINATION: one violation per re-issue whose header block does not contain its true
immediately-prior re-issue's delta number as a whole-word token (`\bsN\b` -- a word-boundary
match, so "s58" matches inside "s58-missive-substrate.sql" and inside bare "s58" prose alike,
and does NOT false-match "s580" or "s5" against a true prior of "s58"/"s5" respectively).

CHECK 2 -- PRIOR-BODY HASH BINDING (spec §3 item 2, amendment maintainer-approved 2026-07-26):
citation alone (check 1) proves a re-issue NAMES a file; it does not prove the re-issue's body
actually descends from THAT file's CURRENT text -- s61's own defect would still have passed a
citation-only check that merely required "some sNN token present" without also requiring it be
the TRUE prior. Check 2 closes that: each checked re-issue must additionally carry a line of the
shape `-- prior-body-sha256: <hex> (<file>)` inside its combined citation window (same two
windows as check 1). The gate independently determines the TRUE immediately-prior re-issue from
its own occurrence ordering (never merely trusting the parenthetical filename the author wrote),
extracts THAT prior occurrence's full `CREATE (OR REPLACE) FUNCTION ... $tag$...$tag$;` statement
text from the cited file (mechanical: anchored on the function name via the same CREATE_FN_RE
already used to locate the occurrence, and on the dollar-quote delimiter pair -- see
`extract_function_body` below), hashes it (sha256, UTF-8, the exact multi-line text as it
appears in the file, `\n`-joined, no re-formatting), and compares against the declared hex.
A stale base is thereby unrepresentable, not merely un-citable: s45's body does not hash to the
same digest as s58's, so a re-issue that names the right file in prose but pastes a hash from the
wrong (or no) prior fails exactly where check 1 alone would have passed it. **A definer file the
extractor cannot parse (no dollar-quote pair found, or the closing tag never recurs) is a GATE
FAILURE, never a silent skip** -- reported as its own violation category, per spec §3 item 2's
explicit instruction.

MIN_N_HASH = 63 -- check 2's OWN threshold, separate from check 1's MIN_N=43, NAMED for the same
reason (ADR-0000 Rule 2a: a deliberately-uncovered axis is disclosed, not silently gapped). The
`-- prior-body-sha256:` line is a brand-new convention this very spec amendment invents (spec §3
item 2, maintainer-approved 2026-07-26) -- verified empirically: every tracked re-issue at N in
[43, 62] fails check 2 purely because the convention did not exist when authored (their check-1
citations are already clean). The spec's own words settle where checking starts: "s63 itself is
the first conforming instance." Retroactively demanding the line from s43-s62 would be the same
retroactive sweep ADR-0000/ADR-0005 Rule 8 reject, applied to check 2 as MIN_N=43 applies it to
check 1.

GRANDFATHER WAIVER (spec §3, explicit and dated, BOTH checks): s61 Element 7's own header is
EXEMPTED here by name -- the defect is already on the permanent record (ledger row 1430, this
gate's own commission) and rewriting a frozen kernel/lineage/ file's prose to retroactively fix
its own citation (or retroactively insert a hash line it never carried) is not the remedy
(ADR-0005 Rule 8: frozen records are not retro-edited); s63
(kernel/lineage/s63-supersession-body-restoration.sql) restores the dropped branches going
forward instead, and is itself the FIRST conforming instance of both checks (spec §3, last
paragraph). A waiver entry is dated and cites the ledger row it grandfathers; it is not a silent
exclusion (ADR-0000's Rule-2(a) sharpening: a named exclusion, not a silent one).

READ MODE: every file is read via gates/_staged_read.py's shared STAGED-bytes primitive (the
same gates-staged-vs-tree-blindness discipline every other content-checking gate in this chain
follows, ledger row 1234); `--tree` forces the working-tree read. The tracked file SET comes from
`git ls-files kernel/lineage/` (the same primitive gates/lineage_chain_coverage.py uses), never an
`os.listdir` sweep, so an untracked scratch file can never manufacture a false violation.

ENFORCEMENT STATUS (stated honestly, no umbrella claim): this gate DETECTS the class when it is
RUN -- it is not, as of this commit, wired into hooks/pre-commit or any other invocation site, so
nothing runs it automatically today. Wiring it into a standing enforcement surface is a
maintainer-batch hooks/ change, tracked separately from this delta (the standing rule against
touching hooks/ during a live session applies here the same as everywhere else in this repo).

Exit 0 clean; exit 1 listing every mis-cited re-issue, teaching the exact file and function.
Lazy imports are banned.
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _staged_read import read_source_text, run_git  # noqa: E402  (gates/_staged_read.py, shared home)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINEAGE_DIR = os.path.join(ROOT, "kernel", "lineage")

# Same shape as gates/lineage_chain_coverage.py's own DELTA_RE -- a plain top-level delta file,
# exactly one dot before .sql (companions have a second dot and are excluded below by the same
# four-suffix case check that gate uses).
DELTA_RE = re.compile(r"^s(\d+)-[A-Za-z0-9_-]+\.sql$")
COMPANION_SUFFIXES = (".detect.sql", ".verify.sql", ".accommodate.sql", ".accommodate.verify.sql")

CREATE_FN_RE = re.compile(r'^CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+:"schema"\.([A-Za-z_][A-Za-z0-9_]*)\s*\(',
                           re.IGNORECASE)
ELEMENT_MARKER_RE = re.compile(r'^--\s*ELEMENT\s+\d+\b')
COMMENT_LINE_RE = re.compile(r'^--')
DOLLAR_OPEN_RE = re.compile(r'AS\s*(\$[A-Za-z_]*\$)', re.IGNORECASE)
PRIOR_HASH_RE = re.compile(r'^--\s*prior-body-sha256:\s*([0-9a-fA-F]{64})\s*\(([^)]+)\)\s*$',
                            re.MULTILINE)

MAX_WINDOW = 40  # lines walked backward before giving up on finding an ELEMENT marker boundary.
TAG_SCAN_WINDOW = 8  # lines forward from a CREATE line to find its "AS $tag$" opening delimiter.

# The base-citation discipline's own start -- see module docstring's MIN_N paragraph for the
# empirical verification and the two named-precedent citations (s43's PREREQUISITE paragraph,
# s45's HEAD-BODY RULE) this threshold rests on.
MIN_N = 43

# The prior-body-hash-binding discipline's own (separate, later) start -- see module docstring's
# MIN_N_HASH paragraph. The convention is invented by this spec amendment; s63 is its first
# conforming instance, so nothing before s63 is asked to carry it.
MIN_N_HASH = 63

# Dated, named waivers -- see module docstring's GRANDFATHER WAIVER. Keyed by
# (function_name, re-issuing file's basename). Never a bare filename exclusion: a waiver names
# the function too, so a DIFFERENT function re-issued later in the same file is still checked.
WAIVERS: dict[tuple[str, str], str] = {
    ("validate_supersession_target", "s61-signature-symmetry-and-key-binding.sql"):
        "2026-07-26, ledger row 1430 (the witnessed finding this gate's own commission, "
        "design/FABLE-S63-SUPERSESSION-BODY-RESTORATION-SPEC.md, restores) -- s61 Element 7's "
        "header claims 'Base body = s45's (UNCHANGED by s60)', the true immediately-prior "
        "re-issue being s58 Element 5. Frozen kernel/lineage/ prose is not retro-edited (ADR-0005 "
        "Rule 8); kernel/lineage/s63-supersession-body-restoration.sql restores the dropped "
        "branches going forward instead. Grandfathered, not silently excluded.",
}


def tracked_lineage_deltas() -> list[str]:
    """Every git-tracked kernel/lineage/sNN-<slug>.sql delta basename, numeric order, no lower
    N bound (see module docstring's QUANTIFICATION UNIVERSE)."""
    r = run_git(["-C", ROOT, "ls-files", "kernel/lineage/"], capture_output=True, text=True, check=True)
    out = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        base = os.path.basename(line)
        m = DELTA_RE.match(base)
        if not m:
            continue
        if base.endswith(COMPANION_SUFFIXES):
            continue
        out.append(base)
    out.sort(key=lambda b: int(DELTA_RE.match(b).group(1)))
    return out


def _file_opening_window(lines: list[str]) -> str:
    """Window (2) -- the file's own leading comment banner, line 1 through the first non-comment
    line (see module docstring's HEADER-BLOCK EXTRACTION). Computed once per file (it does not
    depend on which CREATE line is being checked)."""
    block_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            block_lines.append(stripped)
            continue
        if not COMMENT_LINE_RE.match(stripped):
            break
        block_lines.append(stripped)
    return "\n".join(block_lines)


def function_occurrences(text: str) -> list[tuple[str, int, str]]:
    """Every (function_name, 0-based line index of the CREATE line, combined-window citation
    text) triple for this one file's own CREATE (OR REPLACE) FUNCTION :"schema".<name>
    statements -- window (1) local-Element plus window (2) file-opening, concatenated (see
    module docstring's HEADER-BLOCK EXTRACTION)."""
    lines = text.splitlines()
    opening_window = _file_opening_window(lines)
    out = []
    for i, line in enumerate(lines):
        m = CREATE_FN_RE.match(line.strip())
        if not m:
            continue
        fname = m.group(1)
        block_lines: list[str] = []
        j = i - 1
        steps = 0
        while j >= 0 and steps < MAX_WINDOW:
            candidate = lines[j]
            stripped = candidate.strip()
            if not COMMENT_LINE_RE.match(stripped):
                break  # non-comment line: the block's true top is right below this, not included.
            block_lines.append(stripped)
            if ELEMENT_MARKER_RE.match(stripped):
                break  # inclusive stop: this element's own marker line, never the prior element's.
            j -= 1
            steps += 1
        block_lines.reverse()
        local_window = "\n".join(block_lines)
        out.append((fname, i, local_window + "\n" + opening_window))
    return out


def extract_function_body(lines: list[str], create_idx: int) -> str | None:
    """The mechanical extraction check 2 needs (module docstring, CHECK 2): the exact
    `CREATE (OR REPLACE) FUNCTION ... AS $tag$ ... $tag$;` statement text starting at
    `lines[create_idx]`, as a single `\\n`-joined string spanning every line from the CREATE
    line through the line carrying the closing `$tag$;`, INCLUSIVE. Returns None when no
    dollar-quote opening delimiter is found within TAG_SCAN_WINDOW lines, or when the opening
    tag never recurs as a closing `$tag$;` anywhere below it -- an UNPARSEABLE definer, which
    the caller must treat as a gate FAILURE, never a skip (spec §3 item 2)."""
    tag = None
    open_idx = None
    for i in range(create_idx, min(create_idx + TAG_SCAN_WINDOW, len(lines))):
        m = DOLLAR_OPEN_RE.search(lines[i])
        if m:
            tag = m.group(1)
            open_idx = i
            break
    if tag is None:
        return None
    close_re = re.compile(re.escape(tag) + r';')
    for j in range(open_idx, len(lines)):
        # The opening line itself: only a closing match AFTER the opening occurrence counts (a
        # degenerate same-line open+close is vanishingly unlikely in this codebase's own house
        # idiom -- every re-issue's body spans many lines -- but checked correctly rather than
        # assumed away).
        line = lines[j]
        search_from = line.find(tag) + len(tag) if j == open_idx else 0
        if close_re.search(line[search_from:]):
            return "\n".join(lines[create_idx:j + 1])
    return None


def main() -> int:
    use_tree = "--tree" in sys.argv[1:]
    deltas = tracked_lineage_deltas()

    # file basename -> its own line list (cached once, re-used both for occurrence scanning and
    # for check 2's body extraction against whichever prior file a later delta cites).
    lines_by_base: dict[str, list[str]] = {}
    # function_name -> list of (delta_number, basename, header_block_text, create_line_idx), in
    # file numeric order. Every tracked delta contributes regardless of N -- MIN_N gates which
    # re-issue gets CHECKED (below), never which occurrences count toward identifying the true
    # immediately-prior re-issue (a checked re-issue whose true prior sits below MIN_N, e.g. a
    # future s6x re-issuing something s43 first defined, must still be checked against that real
    # prior, not against a fabricated later one).
    by_function: dict[str, list[tuple[int, str, str, int]]] = {}
    for base in deltas:
        n = int(DELTA_RE.match(base).group(1))
        text = read_source_text(Path(os.path.join(LINEAGE_DIR, base)), use_tree=use_tree)
        lines_by_base[base] = text.splitlines()
        for fname, line_idx, block in function_occurrences(text):
            by_function.setdefault(fname, []).append((n, base, block, line_idx))

    violations: list[str] = []
    checked_reissues = 0
    waived: list[str] = []
    multiply_defined = {f: v for f, v in by_function.items() if len(v) > 1}

    for fname, occurrences in sorted(multiply_defined.items()):
        # Occurrences already arrive in ascending-N file order (deltas is numerically sorted and
        # each file contributes its own occurrences in file order) -- no re-sort needed, and a
        # re-sort would risk silently reordering same-N occurrences (never happens today, since
        # DELTA_RE guarantees one N per basename, but stated rather than assumed).
        for idx in range(1, len(occurrences)):
            prior_n, prior_base, _prior_block, prior_line_idx = occurrences[idx - 1]
            this_n, this_base, block, _this_line_idx = occurrences[idx]
            if this_n < MIN_N:
                continue  # below the base-citation discipline's own start -- see MIN_N docstring.
            checked_reissues += 1
            waiver_key = (fname, this_base)
            if waiver_key in WAIVERS:
                waived.append(f"{fname} in kernel/lineage/{this_base} (waived: {WAIVERS[waiver_key]})")
                continue

            # CHECK 1 -- citation.
            token = re.compile(r'\bs' + str(prior_n) + r'\b')
            if not token.search(block):
                violations.append(
                    f"[citation] kernel/lineage/{this_base} re-issues `{fname}` but its own "
                    f"header block does not name s{prior_n} (kernel/lineage/{prior_base}), the "
                    f"true immediately-prior re-issue -- the false-stale-base class (s61 "
                    f"Element 7, ledger row 1430). Header block scanned:\n"
                    + "\n".join(f"        {l}" for l in block.splitlines()))

            # CHECK 2 -- prior-body hash binding (spec §3 item 2). Own threshold, MIN_N_HASH --
            # see module docstring; nothing before s63 carries (or is asked to carry) this line.
            if this_n < MIN_N_HASH:
                continue
            hash_matches = list(PRIOR_HASH_RE.finditer(block))
            if not hash_matches:
                violations.append(
                    f"[hash-missing] kernel/lineage/{this_base} re-issues `{fname}` but carries "
                    f"no `-- prior-body-sha256: <hex> (<file>)` line in its citation window -- "
                    f"required for every checked re-issue (spec §3 item 2).")
                continue
            declared_hex, declared_file = hash_matches[0].group(1).lower(), hash_matches[0].group(2).strip()
            if os.path.basename(declared_file) != prior_base:
                violations.append(
                    f"[hash-filename-mismatch] kernel/lineage/{this_base}'s prior-body-sha256 "
                    f"line names '{declared_file}' but the true immediately-prior re-issue of "
                    f"`{fname}` is kernel/lineage/{prior_base}.")
                continue
            prior_body = extract_function_body(lines_by_base[prior_base], prior_line_idx)
            if prior_body is None:
                violations.append(
                    f"[unparseable-definer] GATE FAILURE (spec §3 item 2 -- never a skip): "
                    f"kernel/lineage/{prior_base}'s own `CREATE (OR REPLACE) FUNCTION {fname}` "
                    f"statement (line {prior_line_idx + 1}) could not be mechanically extracted "
                    f"(no dollar-quote open/close pair found) -- kernel/lineage/{this_base}'s "
                    f"declared prior-body-sha256 cannot be verified against it.")
                continue
            recomputed_hex = hashlib.sha256(prior_body.encode("utf-8")).hexdigest()
            if recomputed_hex != declared_hex:
                violations.append(
                    f"[hash-mismatch] kernel/lineage/{this_base}'s declared prior-body-sha256 "
                    f"({declared_hex}) does not match the recomputed hash of kernel/lineage/"
                    f"{prior_base}'s own `{fname}` body ({recomputed_hex}) -- a stale or "
                    f"fabricated base, unrepresentable per spec §3 item 2.")

    print(f"lineage-reissue-lineage: {len(multiply_defined)} multiply-defined function(s) across "
          f"{len(deltas)} tracked kernel/lineage/sNN-*.sql delta(s); {checked_reissues} re-issue(s) "
          f"checked for a correctly-cited AND hash-bound immediately-prior base.")
    if waived:
        print(f"  {len(waived)} waived (grandfathered, named and dated, BOTH checks -- see module "
              f"docstring):")
        for w in waived:
            print(f"    ~~ {w}")

    if not violations:
        print("lineage-reissue-lineage: clean ✓")
        return 0

    print(f"\n  {len(violations)} violation(s):")
    for v in violations:
        print(f"    !! {v}")
    print("\nlineage-reissue-lineage: [citation] fix the re-issue's header-block citation to name "
          "its TRUE immediately-prior re-issue; [hash-missing]/[hash-mismatch] add or correct the "
          "`-- prior-body-sha256: <hex> (<file>)` line (recompute via this gate's own "
          "extract_function_body against the true prior); [hash-filename-mismatch] point the "
          "parenthetical filename at the true prior; [unparseable-definer] is a gate failure in "
          "the CITED file itself, not the re-issue -- fix that file's dollar-quote delimiters. Or, "
          "if the file is frozen history and the fix is a forward-restoring delta instead (the "
          "s63 precedent), add a dated, named waiver entry to this gate's own WAIVERS dict.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
