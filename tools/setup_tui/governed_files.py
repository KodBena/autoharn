#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T02:39:43Z
#   last-change: 2026-07-19T02:39:43Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/governed_files.py -- the governed-files exposure CHOICE driver
(design/FABLE-SETUP-TUI-SPEC.md's 2026-07-19 governed-files amendment, commission ledger row
1730). ONE home (ADR-0012 P1) for the operator-facing pattern-set decision -- validation, the
teaching line, the default -- for `hooks/pretooluse_change_gate.py`'s own governed-files
contract (read at commissioning and again for this build, never edited: hooks/ stays read-only
source material this module writes FOR, per this build's scope discipline).

ONE WRITER, NOT TWO (the corrected design; see git history for the superseded first pass): this
module does NOT write `<dest>/.claude/governed_files.json` itself. `bootstrap/new-project.sh`
already owns that file unconditionally, on EVERY invocation this package makes against a
destination (screen_birth's `--new-world` birth AND screen_boundary's later classic-mode
`--force` re-scaffold both rewrite the full `.claude/` wiring) -- and it already ships the
sanctioned way to steer that write: `--governed <comma-separated-fnmatch-patterns>`
(`bootstrap/new-project.sh`'s own flag, tracker item `scaffold-governed-set-language-default`).
A first pass of this feature wrote the file directly at the fork/target screen and raced
`new-project.sh`'s own later unconditional rewrite -- silently clobbering the operator's choice
back to the bare `*.py` default on every real flow (an out-of-frame review caught this: the
"witness" fixtures for that pass only ever ran `--start-at fork-target` and stopped before birth,
so the clobber was invisible to them). The general fix is to have exactly ONE writer: this
module validates and RECORDS the operator's choice on `state["governed_patterns"]`
(tools/setup_tui/screens.py's shared flow-state dict); `screens.py` threads it into EVERY
`new-project.sh` invocation's `--governed` flag (screen_birth AND screen_boundary alike), so the
file is written once, last, by the same script that owns every other byte of `.claude/`.

THE CONTRACT, mirrored here for validation/teaching purposes only:
  * `_load_governed_patterns(cfg_path)` (hooks/pretooluse_change_gate.py) reads
    `{"patterns": [<glob>, ...]}` -- a JSON object with a `patterns` key holding a non-empty list
    of strings -- fnmatch'd against each changed path RELATIVE TO the world root. ANY other shape
    (missing file, malformed JSON, missing/empty/non-string-list `patterns`) falls back to
    `_DEFAULT_GOVERNED_PATTERNS = ["*.py"]` -- the F33 invariant default, mirrored here as
    `DEFAULT_PATTERNS` so a project that has not yet configured governance is never silently
    ungoverned. `bootstrap/new-project.sh` mirrors the SAME default independently (its own
    `cp "$TEMPLATES/governed_files.json"` fallback when `--governed` is omitted) -- this
    module's `DEFAULT_PATTERNS` is a THIRD mirror of the same fact, kept in sync by inspection
    (all three are one-line literals, `["*.py"]` / `*.py` / `{"patterns": ["*.py"]}`) rather than
    a shared import, since hooks/, bootstrap/, and tools/setup_tui/ are three different
    interpreter/process boundaries with no shared importable home today.

The commission's own witnessed specimen (verbatim): "when I started the autoharn-panel it was
set only to .py, while we needed at least .ts, .vue, .html and so on" -- `TEACHING_LINE` below
carries this forward at the point of decision (parent spec: "a teaching line carrying the
witnessed specimen").

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import here is top of file.
"""
from __future__ import annotations

import os
import re

# Mirrors hooks/pretooluse_change_gate.py's own `_DEFAULT_GOVERNED_PATTERNS` (the F33 invariant
# default) AND bootstrap/new-project.sh's own no-`--governed` fallback -- see module docstring's
# "THE CONTRACT" for why this is a third, inspected mirror rather than a shared import.
DEFAULT_PATTERNS = ["*.py"]

TEACHING_LINE = (
    "governed_files.json controls which changed files hooks/pretooluse_change_gate.py demands a "
    "ledger-row authorization for (F33: class-keyed patterns, never an enumerated file list). "
    "The witnessed specimen this screen exists to prevent recurring: the autoharn-panel "
    "deployment started with the default *.py-only pattern set and needed .ts/.vue/.html added "
    "by hand, after the fact, once the gap was already painful. Confirm the default below, or "
    "extend it now for the languages your project actually contains -- your choice is applied "
    "by bootstrap/new-project.sh's own --governed flag at birth (and re-applied at any later "
    "scaffold re-run this flow performs), the ONE place this file is ever written."
)

# Closed-alphabet validation (law/adr/0012's interpreter-boundary amendment: "a value crosses an
# interpreter boundary as DATA... where no carrier exists, a strict validation to a closed
# alphabet at the Port"). An operator-typed extension is spliced into a comma-separated
# `--governed` argv token this process passes to `new-project.sh`, which itself splices each
# pattern into the governed_files.json array a SECOND evaluator (hooks/pretooluse_change_gate.py's
# own fnmatch) later reads -- no bind-variable carrier exists at either hop, so each token is
# validated here BEFORE it is turned into a "*.<ext>" pattern and BEFORE it ever reaches argv.
_EXT_RE = re.compile(r"^\.[A-Za-z0-9]+$")


def valid_extension_token(token: str) -> bool:
    """True iff `token` is a dot followed by one or more ASCII letters/digits -- the only shape
    ever safe to turn into a `*.<ext>` fnmatch pattern and splice into a `--governed` argv token.
    Refuses anything with a wildcard, comma, path separator, quote, or other
    fnmatch/shell-meaningful character (e.g. `*`, `,`, `/`, `"`, `]`) BEFORE it ever reaches argv
    or the JSON the change gate later parses."""
    return bool(_EXT_RE.fullmatch(token.strip()))


def parse_extensions(raw: str) -> tuple[list[str], list[str]]:
    """Splits a comma-separated operator answer (e.g. ".ts, .vue,.html") into
    (valid_patterns, hostile_tokens) -- `valid_patterns` are `*.<ext>` glob strings ready to
    append to `DEFAULT_PATTERNS`; `hostile_tokens` are the raw tokens that failed the closed-
    alphabet check (the caller refuses BEFORE recording any choice if this list is non-empty --
    spec witness (b))."""
    tokens = [t.strip() for t in raw.split(",") if t.strip()]
    valid: list[str] = []
    hostile: list[str] = []
    for tok in tokens:
        if valid_extension_token(tok):
            valid.append(f"*{tok}")
        else:
            hostile.append(tok)
    return valid, hostile


def build_pattern_set(extra_raw: str) -> tuple[list[str], list[str]]:
    """(final_patterns, hostile_tokens). `final_patterns` is `DEFAULT_PATTERNS` plus any valid
    extensions from `extra_raw`, de-duplicated, order-preserving. Never appends anything if
    `hostile_tokens` is non-empty -- the caller must refuse before recording any choice in that
    case (falling back to the default, same as an explicit decline)."""
    valid, hostile = parse_extensions(extra_raw) if extra_raw.strip() else ([], [])
    if hostile:
        return DEFAULT_PATTERNS, hostile
    final = list(DEFAULT_PATTERNS)
    for pat in valid:
        if pat not in final:
            final.append(pat)
    return final, []


def governed_flag_value(patterns: list[str]) -> str:
    """The exact `--governed` argv value for `patterns` -- comma-joined, matching
    `bootstrap/new-project.sh`'s own parsing (`patterns_csv.split(",")`). ONE home for this
    join so every `new-project.sh` call site in screens.py (screen_birth, screen_boundary)
    threads the identical string, never a second hand-rolled `",".join(...)`."""
    return ",".join(patterns)


def governed_files_path(dest: str) -> str:
    """Where `new-project.sh` will write the file -- read-only display use (the checklist/
    teaching line naming the eventual path), never a path this module opens itself."""
    return os.path.join(dest, ".claude", "governed_files.json")
