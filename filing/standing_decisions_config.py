# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-16T02:33:06Z
#   last-change: 2026-07-16T04:23:35Z
#   contributors: 9a17b6b9/main
# <<< PROVENANCE-STAMP <<<

"""standing_decisions_config -- the ONE home for reading `apparatus.json`'s
`mechanisms.standing_decisions` shape (design/FABLE-GRADED-DECISIONS-SPEC.md element 4: "the hook
and pickup both read this; the kernel knows nothing of it"). ADR-0012 P1 (one home per mechanism):
before this module, resolving/validating this shape would have been hand-copied into
`hooks/sessionstart_durable_decisions.py` AND `bootstrap/templates/pickup.tmpl` -- two readers of
the identical config shape, exactly the drift class this project's own `filing/
deployment_record.py` docstring warns against ("N places... a shape change has one edit site,
never two hand-synced copies drifting apart"). Both readers import THIS module instead.

SHAPE: `{"grades": [<word>, ...], "byte_cap": <positive int>, "max_items": <positive int, or
null/absent>}`, all keys optional -- an absent or malformed entry degrades to the documented
default (`grades=["durable"]`, `byte_cap=4000`, `max_items=None` i.e. no count limit, byte cap
alone governs -- exactly the behavior every deployment had before this key existed) with a stderr
WARNING (never a silently widened/narrowed grade set, never a silently invented count cap),
mirroring `hooks/stop_clean_exit.py`'s own `_resolve_mode()` validation posture applied to this
shape instead. The kernel (`kernel/lineage/s36-decision-grade.sql`) enforces no vocabulary on
`decision_grade` -- this module is deployment POLICY, read here and nowhere else.

`max_items`, WHEN SET, is a second, independent guard alongside `byte_cap` -- both apply, oldest-
first (`ORDER BY id`) selection preserved either way, and whichever limit bites first truncates
the injected block (a caller does not need to choose one or the other; it applies both, in
whatever order is convenient, since a row excluded by either guard is excluded).

NAMED CHOICE -- `resolve_standing_decisions_config()` below takes the ALREADY-EXTRACTED `entry`
dict (`apparatus["mechanisms"]["standing_decisions"]`), not the whole `apparatus` dict. This is
deliberate, not an arbitrary signature: `filing/apparatus_registry.py`'s `known_mechanisms()`
mechanically DERIVES the set of recognized apparatus.json mechanism keys by grep-pattern-scanning
`hooks/*.py` and `bootstrap/templates/*.tmpl` ONLY (never `filing/*.py`) for one of three literal
shapes, the simplest being `mechs.get("<name>")` at the call site. If the `mechs.get(...)` lookup
itself lived in here instead, `standing_decisions` would be INVISIBLE to that registry (this
module is never scanned) and `gates/apparatus_unknown_keys.py` would flag every deployment's own
`mechanisms.standing_decisions` entry as an unrecognized typo -- a self-inflicted false positive.
So each caller (`hooks/sessionstart_durable_decisions.py`, `bootstrap/templates/pickup.tmpl`) does
its OWN `mechs.get("standing_decisions")` extraction, in its own scanned file, satisfying the
registry's mechanical derivation -- then hands the extracted `entry` here for the shared
defaulting/validation logic, which stays ONE home (ADR-0012 P1) for the part that actually drifts.

Stdlib-only, top-of-file imports (the lazy-import gate, gates/no_lazy_imports.py, applies).
"""
from __future__ import annotations

import sys

DEFAULT_GRADES: tuple[str, ...] = ("durable",)
DEFAULT_BYTE_CAP = 4000
DEFAULT_MAX_ITEMS = None  # absent/null = no count limit -- byte cap alone governs (today's behavior)


def resolve_standing_decisions_config(entry: dict | None) -> tuple[list[str], int, int | None]:
    """`entry` = `apparatus["mechanisms"]["standing_decisions"]` (the caller's own extraction --
    see module docstring NAMED CHOICE) -> (grades, byte_cap, max_items), defaulted/validated. Never
    raises -- a malformed entry degrades to the default, loudly, on stderr. `max_items` is `None`
    when absent/null/malformed (no count limit -- byte cap alone governs, unchanged from before
    this key existed), else a validated positive int."""
    if not isinstance(entry, dict):
        return list(DEFAULT_GRADES), DEFAULT_BYTE_CAP, DEFAULT_MAX_ITEMS

    raw_grades = entry.get("grades", list(DEFAULT_GRADES))
    if isinstance(raw_grades, list) and raw_grades and all(isinstance(g, str) and g for g in raw_grades):
        grades = raw_grades
    else:
        print(f"[apparatus] WARNING: mechanisms.standing_decisions.grades={raw_grades!r} is not a "
              f"non-empty list of non-empty strings -- falling back to {list(DEFAULT_GRADES)!r}.",
              file=sys.stderr)
        grades = list(DEFAULT_GRADES)

    raw_cap = entry.get("byte_cap", DEFAULT_BYTE_CAP)
    if isinstance(raw_cap, int) and not isinstance(raw_cap, bool) and raw_cap > 0:
        byte_cap = raw_cap
    else:
        print(f"[apparatus] WARNING: mechanisms.standing_decisions.byte_cap={raw_cap!r} is not a "
              f"positive integer -- falling back to {DEFAULT_BYTE_CAP}.", file=sys.stderr)
        byte_cap = DEFAULT_BYTE_CAP

    raw_max_items = entry.get("max_items", DEFAULT_MAX_ITEMS)
    if raw_max_items is None:
        max_items = None
    elif isinstance(raw_max_items, int) and not isinstance(raw_max_items, bool) and raw_max_items > 0:
        max_items = raw_max_items
    else:
        print(f"[apparatus] WARNING: mechanisms.standing_decisions.max_items={raw_max_items!r} is "
              f"not a positive integer or null -- falling back to {DEFAULT_MAX_ITEMS!r} (no count "
              f"limit; byte_cap alone governs).", file=sys.stderr)
        max_items = DEFAULT_MAX_ITEMS

    return grades, byte_cap, max_items
