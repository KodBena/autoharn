#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T02:39:43Z
#   last-change: 2026-07-19T03:39:41Z
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

import json
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_CHANGE_GATE_PATH = REPO_ROOT / "hooks" / "pretooluse_change_gate.py"
BOOTSTRAP_TEMPLATE_PATH = REPO_ROOT / "bootstrap" / "templates" / "governed_files.json"

# Mirrors hooks/pretooluse_change_gate.py's own `_DEFAULT_GOVERNED_PATTERNS` (the F33 invariant
# default) AND bootstrap/new-project.sh's own no-`--governed` fallback -- see module docstring's
# "THE CONTRACT" for why this is a third, inspected mirror rather than a shared import.
DEFAULT_PATTERNS = ["*.py"]

# ---------------------------------------------------------------------------------------------
# The drift BACKSTOP the module docstring's own "kept in sync by inspection" method demands
# (ledger row 1799 finding 2): three process boundaries (hooks/, bootstrap/, tools/setup_tui/)
# with no shared importable home -- "kept in sync by inspection" alone is a claim, not a check.
# These functions READ the other two sources (hooks/ and bootstrap/ stay read-only -- module
# docstring's own scope discipline, never edited by this module) and compare their literal
# default to `DEFAULT_PATTERNS`, injectable via parameters so a fixture can feed a SYNTHETIC
# disagreeing text without touching the real files (the same injectable-comparator shape
# feature_facts.check_registry already establishes for this package's other drift backstop).
# ---------------------------------------------------------------------------------------------

_HOOKS_DEFAULT_RE = re.compile(
    r"_DEFAULT_GOVERNED_PATTERNS\s*=\s*(\[[^\]]*\])"
)


def read_hooks_default_patterns(source_text: str | None = None) -> list[str]:
    """Parses `_DEFAULT_GOVERNED_PATTERNS = [...]` out of hooks/pretooluse_change_gate.py's own
    SOURCE TEXT (never imported as a module -- hooks/ stays read-only source material this
    package writes FOR, per this build's scope discipline, and importing a hook module for its
    side effects is a hazard this function does not need to take). `source_text`, if given, is a
    SYNTHETIC stand-in for the file's contents (the fixture's red-leg injection point) --
    default `None` reads the real file. Raises ValueError if the literal cannot be found/parsed
    (never a silent empty list standing in for "I could not find it")."""
    if source_text is None:
        source_text = HOOKS_CHANGE_GATE_PATH.read_text(encoding="utf-8")
    m = _HOOKS_DEFAULT_RE.search(source_text)
    if not m:
        raise ValueError(
            f"could not find '_DEFAULT_GOVERNED_PATTERNS = [...]' in "
            f"{HOOKS_CHANGE_GATE_PATH} -- drift check has nothing to compare against"
        )
    parsed = json.loads(m.group(1).replace("'", '"'))
    if not isinstance(parsed, list) or not all(isinstance(p, str) for p in parsed):
        raise ValueError(f"parsed '_DEFAULT_GOVERNED_PATTERNS' is not a list of strings: {parsed!r}")
    return parsed


def read_bootstrap_template_default_patterns(source_text: str | None = None) -> list[str]:
    """Parses `{"patterns": [...]}` out of bootstrap/templates/governed_files.json -- the actual
    literal `bootstrap/new-project.sh` copies verbatim (`cp "$TEMPLATES/governed_files.json"`)
    when no `--governed` flag is given (module docstring's own "THE CONTRACT"). `source_text`, if
    given, is a SYNTHETIC stand-in for the file's contents (the fixture's red-leg injection
    point) -- default `None` reads the real file."""
    if source_text is None:
        source_text = BOOTSTRAP_TEMPLATE_PATH.read_text(encoding="utf-8")
    parsed = json.loads(source_text)
    patterns = parsed.get("patterns") if isinstance(parsed, dict) else None
    if not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns):
        raise ValueError(
            f"{BOOTSTRAP_TEMPLATE_PATH} does not carry a 'patterns' list of strings: {parsed!r}"
        )
    return patterns


def check_default_patterns_drift(
    local: list[str] | None = None,
    hooks_source_text: str | None = None,
    bootstrap_source_text: str | None = None,
) -> list[str]:
    """Compares `local` (default: this module's own `DEFAULT_PATTERNS`) against the two other
    mirrors, read fresh from their own source text. Returns a list of drift messages, empty iff
    all three agree. Every parameter is injectable (default `None` reads the real, live sources)
    so a fixture can feed a SYNTHETIC disagreeing copy of either external source and observe the
    red leg without touching hooks/ or bootstrap/ on disk -- those trees stay read-only, per this
    module's own scope discipline."""
    if local is None:
        local = DEFAULT_PATTERNS
    hooks_patterns = read_hooks_default_patterns(hooks_source_text)
    bootstrap_patterns = read_bootstrap_template_default_patterns(bootstrap_source_text)
    drift: list[str] = []
    if local != hooks_patterns:
        drift.append(
            f"DRIFT: tools/setup_tui/governed_files.py DEFAULT_PATTERNS={local!r} != "
            f"hooks/pretooluse_change_gate.py _DEFAULT_GOVERNED_PATTERNS={hooks_patterns!r}"
        )
    if local != bootstrap_patterns:
        drift.append(
            f"DRIFT: tools/setup_tui/governed_files.py DEFAULT_PATTERNS={local!r} != "
            f"bootstrap/templates/governed_files.json patterns={bootstrap_patterns!r}"
        )
    return drift

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
