# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T22:21:48Z
#   last-change: 2026-07-12T13:58:34Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""apparatus_registry -- the ONE source of truth for "what mechanism names does this project's
apparatus.json switchboard actually recognize" (BACKLOG "Configuration-surface survey, adopter's
eyes", 2026-07-11, gap 1: "A typo'd mechanism NAME in apparatus.json is silently ignored. Mode
VALUES are validated [...]; nothing sweeps unknown keys -- each hook reads only its own entry.
Fail-open, the shape this project distrusts most.").

WHY A DERIVED REGISTRY, NOT A HAND-MAINTAINED LIST (the commission's own instruction: "derive the
valid set from one source of truth, never a second hand-maintained list"). A hand-typed tuple of
mechanism names is exactly the kind of second list that drifts -- and it already had, silently,
before this module existed: `hooks/posttooluse_bash_completion.py` reads
`mechanisms.bash_completion` (added 2026-07-12, "Small-follow-ups commission"), but
`bootstrap/templates/APPARATUS.md`'s own "the ten mechanisms" table and
`bootstrap/templates/apparatus.json`'s shipped default both still stopped at ten -- an
undocumented eleventh mechanism, found while building this exact module (see BACKLOG's dated
entry for this commission; both docs are fixed in the same change as a hazard met in passing,
CLAUDE.md's engineering-responsibility clause). A hand list would have carried the same staleness
forward a twelfth time. So `known_mechanisms()` below does not enumerate names -- it READS
`hooks/*.py`, the actual code that will treat that name as meaningful, and extracts every
mechanism key that code demonstrably reads. The registry cannot go stale relative to the hooks
because it IS the hooks, read mechanically.

HOW EXTRACTION WORKS. Every apparatus-reading hook in this project uses one of three shapes to
name the mechanism key it owns (grep-verified against every file in hooks/ at the time this module
was written):
  1. A module-level `MECHANISM_KEY = "name"` constant, later passed to `mechs.get(MECHANISM_KEY)`
     (`posttooluse_bash_completion.py`, `pretooluse_read_observer.py`,
     `pretooluse_doc_shapes_gate.py`, `doc_legibility_critic.py`).
  2. A direct literal at the read site, `mechs.get("name")` (`demurral_detect.py`,
     `posttooluse_mutation_observer.py`, `pretooluse_delegation_observer.py`,
     `stop_clean_exit.py`, `stamp_intercept.py`).
  3. A literal passed as the second positional argument to a shared `_resolve_mode(apparatus,
     "name", default, root)` helper -- the one file owning TWO mechanisms in one process,
     `pretooluse_change_gate.py` ("change_gate" and "permit_to_work").
Three regexes, one per shape, unioned across every scanned file, is `known_mechanisms()`'s whole
implementation. A file that names its mechanism a fourth way (unlikely, but not impossible) would
go undetected here -- an honest limit, named rather than assumed away: if a future reader's key
never shows up in this registry despite genuinely being read, that is itself a class-1 recurrence
(ADR-0011 Rule 2) asking for a fourth pattern, not evidence the approach is unsound.

WHERE IT SCANS -- widened 2026-07-12 (tracker item `abc-loop-offering`; the class, not the
instance). This registry started life scanning ONLY `hooks/*.py`, because every apparatus-reading
file in the project was, at the time, a hook. `bootstrap/templates/distance-to-clean.tmpl`'s
DOC-ATTESTATION section is the first apparatus-reading file that is NOT a hook -- it lives in
`bootstrap/templates/` and reads a deployment's `.claude/apparatus.json` directly, using the SAME
`MECHANISM_KEY = "name"` shape (extraction pattern 1) as its hook siblings. Scanning only
`hooks/*.py` would have made THIS registry itself go stale on day one of that mechanism's life --
`doc_attestation` would read live in distance-to-clean.tmpl while `apparatus_unknown_keys.py` and
`pretooluse_change_gate.py`'s own sweep flagged it as an unrecognized typo, the exact false-positive
class this module exists to end (see "WHY A DERIVED REGISTRY" above -- `bash_completion` already
lived this once as a hand-list gap). The fix is the general one, not a `doc_attestation` special
case: `known_mechanisms()` now unions extraction across EVERY declared source directory
(`hooks/*.py` AND `bootstrap/templates/*.tmpl`), so the next apparatus-reading file that is not a
hook is covered automatically, by construction, without a further registry edit.

Stdlib-only, top-of-file imports (the lazy-import gate, gates/no_lazy_imports.py, applies).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO_ROOT / "hooks"
TEMPLATES_DIR = REPO_ROOT / "bootstrap" / "templates"
HOOKS_GLOB = "*.py"
TEMPLATES_GLOB = "*.tmpl"

# The three extraction patterns -- see module docstring "HOW EXTRACTION WORKS" for what each one
# is grounded in. All three name a lowercase-underscore mechanism key as their sole capture group.
_MECHANISM_KEY_ASSIGN = re.compile(r'^MECHANISM_KEY\s*=\s*"([a-z_]+)"', re.MULTILINE)
_MECHS_GET_LITERAL = re.compile(r'mechs\.get\(\s*"([a-z_]+)"\s*\)')
_RESOLVE_MODE_LITERAL = re.compile(r'_resolve_mode\(\s*apparatus\s*,\s*"([a-z_]+)"')


def known_mechanisms(hooks_dir: Path | None = None,
                      templates_dir: Path | None = None) -> frozenset[str]:
    """Every mechanism name some file under `hooks_dir` (default: this repo's own `hooks/`) or
    `templates_dir` (default: this repo's own `bootstrap/templates/`) actually reads from
    `apparatus["mechanisms"]`, derived by static extraction (see module docstring) -- never a
    hand-typed list. `hooks_dir`/`templates_dir` are independent overrides (either, both, or
    neither) kept for callers that want to scan a single source in isolation (e.g. a test
    pointing `hooks_dir` at a scratch directory while leaving `templates_dir` at this repo's
    real default) -- passing one does not disable the other. Returns an empty frozenset (never
    raises) if a source directory does not exist or holds no matching files -- a caller with a
    genuinely empty registry gets an empty set to reason about, not a crash;
    `unknown_mechanism_keys` below treats "nothing known" as "every key is unknown", which is
    the fail-loud posture this module exists to serve, not a silent no-op."""
    sources = (
        (hooks_dir if hooks_dir is not None else HOOKS_DIR, HOOKS_GLOB),
        (templates_dir if templates_dir is not None else TEMPLATES_DIR, TEMPLATES_GLOB),
    )
    found: set[str] = set()
    for d, glob_pattern in sources:
        if not d.is_dir():
            continue
        for f in sorted(d.glob(glob_pattern)):
            try:
                text = f.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for pattern in (_MECHANISM_KEY_ASSIGN, _MECHS_GET_LITERAL, _RESOLVE_MODE_LITERAL):
                found.update(m.group(1) for m in pattern.finditer(text))
    return frozenset(found)


def unknown_mechanism_keys(apparatus: dict, known: frozenset[str] | None = None) -> list[str]:
    """Every key under `apparatus["mechanisms"]` that no hook reads, per `known` (default:
    `known_mechanisms()`, i.e. this repo's own live registry). Returns a sorted list -- empty
    means clean. A non-dict `apparatus` or a non-dict/missing `mechanisms` value yields an empty
    list (nothing to sweep, not a violation of THIS check -- a malformed apparatus.json is every
    individual hook's own `_load_apparatus_quiet` degrade-to-{} concern, not this module's)."""
    if not isinstance(apparatus, dict):
        return []
    mechs = apparatus.get("mechanisms")
    if not isinstance(mechs, dict):
        return []
    reg = known if known is not None else known_mechanisms()
    return sorted(k for k in mechs if k not in reg)


def teach_text(unknown: list[str], known: frozenset[str] | None = None, *, source: str = "") -> str:
    """The loud, actionable message for a caller to print (stderr, gate output, or a hook's
    non-blocking `additionalContext`) when `unknown_mechanism_keys` finds something. Names the
    exact bad key(s), the exact valid set (so a typo is visibly a typo, not a mystery), and the
    file it came from when given -- mirrors this project's established per-mechanism MODE-value
    warning phrasing (`hooks/*.py`'s own `_resolve_mode` functions: "never widening permissions
    on a bad config value") applied one level up, to the key itself rather than its mode."""
    reg = known if known is not None else known_mechanisms()
    where = f" in {source}" if source else ""
    return (
        f"[apparatus] WARNING: unrecognized mechanism name(s) {unknown!r}{where} -- no hook in "
        f"this project reads any of these keys, so whatever is configured under them (mode, "
        f"cost_note, or anything else) has NO EFFECT, silently. The known mechanism set (derived "
        f"live from hooks/*.py, never hand-maintained) is {sorted(reg)!r}. Likely a typo of one "
        f"of those names -- fix the key and re-run; an unrecognized key is never treated as "
        f"widening any permission, but it is also never treated as configuring anything, which is "
        f"exactly the fail-open this check exists to end."
    )
