#!/usr/bin/env python3
"""apparatus_unknown_keys — the class-not-instance sweep for BACKLOG "Configuration-surface
survey, adopter's eyes" (2026-07-11) gap 1: a typo'd mechanism NAME in an `apparatus.json` is
silently ignored today — every hook validates its OWN mechanism's `mode` value loudly (unknown
mode -> stderr WARNING, never widens permission), but nothing sweeps the *keys* themselves, so
`"doc_shapse_gate": {"mode": "enforce"}` (a typo) configures nothing and warns no one. Fail-open,
named in the survey as "the shape this project distrusts most."

WHAT THIS CHECKS. Every key under `apparatus["mechanisms"]` in a given `apparatus.json` (or a
world directory carrying one at `<dir>/.claude/apparatus.json`) against
`filing/apparatus_registry.py`'s `known_mechanisms()` — a set DERIVED from `hooks/*.py`'s,
`bootstrap/templates/*.tmpl`'s, AND `tools/*.py`'s own source (widened 2026-07-12 to cover the
first apparatus-reading file that is not a hook, widened again 2026-07-18 for `tools/` — see that
module's own docstring, "WHERE IT SCANS"), never a hand-typed
second list (see that module's docstring for why: a hand list had ALREADY drifted once, silently,
before this gate existed — `bash_completion` was a real, wired-in mechanism absent from both the
shipped template and its own documentation). A key not in that derived set is reported, with
`filing.apparatus_registry.teach_text`'s exact wording naming the bad key(s) and the full valid set.

WHAT THIS DELIBERATELY DOES NOT CHECK: mode VALUES (`"off"`/`"observe"`/`"enforce"`) — each
mechanism's own hook already validates its own mode loudly at read time (every `hooks/*.py`'s
`_resolve_mode`); duplicating that here would be a second, divergent copy of a check that already
works. This gate is the ONE thing that check structurally cannot do: see the keys the mode-reader
never looks at, because it only ever asks for its own.

SCOPE: this gate's target is any `apparatus.json` FILE, named explicitly — this repo's own
shipped default (`bootstrap/templates/apparatus.json`, the adopter-facing surface every scaffold
starts from) in REPORT mode by default, or any world's live `.claude/apparatus.json` given
explicitly in GATE mode (an operator or a future `distance-to-clean`-style periodic check
pointing this gate at a real deployment — e.g. `python3 gates/apparatus_unknown_keys.py
/home/bork/w/vdc/1/run11`). This gate does not go looking for worlds on its own: which
directories are "worlds" is not this repo's business to know (an adopter's worlds live wherever
they choose, per the library framing user-guide/USER-CONFIGURATION.md states), so every target is named on the
command line or defaults to the one file this repo genuinely owns.

MODES (mirrors gates/doc_shapes.py's own two-mode split):
  - `python3 gates/apparatus_unknown_keys.py` — REPORT mode: sweeps this repo's own
    `bootstrap/templates/apparatus.json` (the shipped default every adopter's first scaffold
    starts from). Always exits 0 — the shipped template is checked here for visibility; a live
    world's own file needs an explicit target (see GATE mode) since this repo cannot enumerate
    worlds it does not own.
  - `python3 gates/apparatus_unknown_keys.py TARGET [TARGET...]` — GATE mode: each TARGET is
    either a path directly to an `apparatus.json` file, or a directory containing
    `.claude/apparatus.json` (a world root, or a scaffolded project root). Exit 1 listing every
    unknown key found in any target, exit 0 clean. A TARGET that resolves to no readable
    `apparatus.json` at all is reported and treated as a usage error (exit 2) — a typo'd PATH is
    a different, louder failure than a typo'd KEY, and this gate does not conflate the two.

Exit codes: 0 clean (gate) / always (report) except a resolution error, 1 gate-mode violations,
2 usage/target-resolution error. Lazy imports are banned (CLAUDE.md, 2026-07-02): everything
below imports at module load.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "filing"))
import apparatus_registry  # noqa: E402  (filing/apparatus_registry.py, the ONE home for the registry)

DEFAULT_REPORT_TARGET = REPO_ROOT / "bootstrap" / "templates" / "apparatus.json"


def _resolve_apparatus_path(target: str) -> Path | None:
    """A TARGET is either a direct path to an apparatus.json file, or a directory carrying one at
    `<dir>/.claude/apparatus.json`. Returns None (never raises) if neither resolves to an
    existing file — the caller reports that as a distinct, louder failure (see module docstring)."""
    p = Path(target)
    if not p.is_absolute():
        p = Path.cwd() / p
    if p.is_file():
        return p
    candidate = p / ".claude" / "apparatus.json"
    if candidate.is_file():
        return candidate
    return None


def _load_apparatus(path: Path) -> dict | None:
    """Best-effort load — returns None on any read/parse failure rather than raising, so the
    caller can report a clean 'could not parse' message instead of a traceback; this gate cares
    about mechanism-key hygiene, not about being the canonical apparatus.json validator (that is
    each hook's own `_load_apparatus_quiet`, deliberately mirrored here at arm's length)."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"apparatus_unknown_keys: could not read/parse {path}: {e}", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        print(f"apparatus_unknown_keys: {path} is not a JSON object", file=sys.stderr)
        return None
    return data


def check_target(target: str, known: frozenset[str]) -> tuple[list[str], bool]:
    """Returns (findings, resolved) for one TARGET. `resolved=False` means the target named no
    readable apparatus.json at all (a usage error, distinct from a clean sweep with zero
    findings)."""
    path = _resolve_apparatus_path(target)
    if path is None:
        return ([f"{target}: no apparatus.json found (checked as a direct file path and as "
                  f"<dir>/.claude/apparatus.json)"], False)
    data = _load_apparatus(path)
    if data is None:
        return ([f"{target}: apparatus.json present but unreadable/malformed — see stderr"], False)
    unknown = apparatus_registry.unknown_mechanism_keys(data, known)
    if not unknown:
        return ([], True)
    return ([apparatus_registry.teach_text(unknown, known, source=str(path))], True)


def main(argv: list[str]) -> int:
    known = apparatus_registry.known_mechanisms()
    print(f"apparatus_unknown_keys: known mechanism set ({len(known)}, derived from "
          f"hooks/*.py + bootstrap/templates/*.tmpl + tools/*.py): {sorted(known)}")

    gate_mode = bool(argv)
    targets = argv if gate_mode else [str(DEFAULT_REPORT_TARGET)]

    all_findings: list[str] = []
    resolution_errors: list[str] = []
    for t in targets:
        findings, resolved = check_target(t, known)
        if not resolved:
            resolution_errors.extend(findings)
        else:
            all_findings.extend(findings)

    mode_word = "gate" if gate_mode else "report"
    if resolution_errors:
        print(f"apparatus_unknown_keys ({mode_word} mode): {len(resolution_errors)} target(s) "
              f"could not be resolved:")
        for e in resolution_errors:
            print(f"  {e}")
        return 2

    if all_findings:
        print(f"apparatus_unknown_keys ({mode_word} mode): {len(all_findings)} target(s) with "
              f"unrecognized mechanism key(s):")
        for f in all_findings:
            print(f"  {f}")
        if not gate_mode:
            return 0  # report mode never fails — see module docstring
        return 1

    print(f"apparatus_unknown_keys ({mode_word} mode): clean — {len(targets)} target(s), "
          f"0 unrecognized mechanism key(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
