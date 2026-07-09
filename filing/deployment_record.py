#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T11:06:10Z
#   last-change: 2026-07-09T11:06:10Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

"""deployment_record -- the ONE home for a project instance's `deployment.json` SHAPE
(design/OPUS-READINESS.md move 1; ADR-0012 P1). A deployment record is the machine-readable
answer to "where does THIS project's ledger live": db, host, schema, kern, role -- the same
(db, schema, kern) triple `engine/targets.py`'s `TargetInfo` already owns for the apparatus's
own curated targets, plus the two fields a SCAFFOLDED instance needs that the apparatus
registry does not carry: `host` (a scaffolded instance is not presumed to share autoharn's own
default postgres host) and `role` (the granted subject role the instance's `led`/`judge`/hooks
connect as -- the field `instruments/ledger_target.py` already keeps instrument-local because
`engine/targets.py`'s `TargetInfo` deliberately does not carry it).

WHY THIS IS THE ONE HOME, NOT A SECOND READER (ADR-0012 P1/P7 applied within one language):
before this module, the names a deployment needs (db/schema/kern/role/host) were re-authored in
N places -- engine's `_SPECIAL` dicts, a `kernel.principal` literal, `led`'s bash defaults,
`settings.json`'s baked env, the WALKTHROUGH's `-v` vars (design/OPUS-READINESS.md's friction
finding). This module is the single parser+validator of the JSON shape; `engine/targets.py`
(move 1's THIRD resolution source) and `bootstrap/new-project.sh` (move 2's scaffold, both the
emission and the template-substitution sides) both import THIS module rather than each growing
its own JSON reader -- so a shape change (a renamed field, a new required key) has one edit site,
never two hand-synced copies drifting apart the way the friction finding describes.

SCOPE, HONESTLY NAMED. This module owns the RECORD'S SHAPE (validate/load/write) only. It does
NOT wire any hook or `led` to read the record live -- that rewiring is explicitly deferred (a live
session reads `hooks/pretooluse_change_gate.py` and `led` per-event right now; OPUS-READINESS
move 1 names the hook/led rewiring as future work). `engine/targets.py`'s `resolve()` is the one
CONSUMER wired in this increment (a build-time/CLI resolution path, not a live hook).

Closure statement (ADR-0000 Rule 2a):
  - invariant: a deployment record's shape is validated in exactly one place; a missing,
    malformed, or incomplete record is refused LOUDLY (ADR-0002) -- never silently defaulted,
    never partially trusted (e.g. accepting three of five fields and leaving the rest `None` for
    a caller to NoneType-crash on downstream).
  - quantification universe: axes = {file absent, unparseable JSON, non-object JSON, missing
    required field, a required field present but not a non-empty string}. Every axis raises
    `DeploymentError` naming which axis fired and the offending path -- a caller cannot mistake
    a malformed record for a valid-but-empty one.
  - denomination: the five required fields (`db`, `host`, `schema`, `kern`, `role`) are named
    exactly once, in `_REQUIRED_FIELDS` below; nothing downstream re-types the list.

Stdlib-only, top-of-file imports (the lazy-import gate, gates/no_lazy_imports.py, applies).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

# The five required fields, in the ONE place they are named (P1). `db`/`schema`/`kern` mirror
# `engine/targets.py`'s `TargetInfo` exactly (same names, same meaning); `role` and `host` are the
# two fields a scaffolded instance needs that the apparatus's own curated-target registry does not
# carry (see module docstring).
_REQUIRED_FIELDS: tuple[str, ...] = ("db", "host", "schema", "kern", "role")


class DeploymentError(Exception):
    """A deployment.json is missing, unreadable, unparseable, or missing/malformed a required
    field. Raised, never swallowed -- a caller that cannot resolve where its ledger lives must
    stop loudly (ADR-0002), not fall back to a guess."""


@dataclass(frozen=True)
class DeploymentRecord:
    """Where a scaffolded project's ledger lives, end to end: database, host, ledger schema,
    kernel schema, and the granted subject role its tools connect as. Mirrors `engine/targets.py`'s
    `TargetInfo(db, schema, kern)` plus `host` and `role` (see module docstring for why those two
    live here and not there)."""
    db: str
    host: str
    schema: str
    kern: str
    role: str


def load_deployment(path: str | Path) -> DeploymentRecord:
    """Load and validate a deployment.json. Raises `DeploymentError` (never returns a partial or
    guessed record) on: a missing file, unreadable/non-UTF-8 bytes, invalid JSON, a JSON value that
    is not an object, a missing required field, or a required field that is not a non-empty string.
    Extra keys beyond the five required ones are accepted and ignored (a forward-compatible record
    a future consumer adds a field to does not break this loader)."""
    p = Path(path)
    if not p.is_file():
        raise DeploymentError(
            f"deployment record not found at {p} -- a project with no deployment record is refused, "
            f"never silently un-resolved. Write one (deployment_record.write_deployment) or point "
            f"LEDGER_DEPLOYMENT at the right path.")
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        raise DeploymentError(f"deployment record at {p} could not be read ({e.__class__.__name__}: {e})") from e
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as e:
        raise DeploymentError(f"deployment record at {p} is not valid JSON ({e.__class__.__name__}: {e})") from e
    if not isinstance(raw, dict):
        raise DeploymentError(
            f"deployment record at {p} must be a JSON object with keys {_REQUIRED_FIELDS}, "
            f"got a {type(raw).__name__}")
    missing = [f for f in _REQUIRED_FIELDS if f not in raw]
    if missing:
        raise DeploymentError(
            f"deployment record at {p} is missing required field(s): {', '.join(missing)} "
            f"(needs all of {_REQUIRED_FIELDS})")
    bad = [f for f in _REQUIRED_FIELDS if not isinstance(raw[f], str) or not raw[f]]
    if bad:
        raise DeploymentError(
            f"deployment record at {p} has non-string or empty value(s) for: {', '.join(bad)} "
            f"(every field must be a non-empty string)")
    return DeploymentRecord(db=raw["db"], host=raw["host"], schema=raw["schema"],
                             kern=raw["kern"], role=raw["role"])


def write_deployment(path: str | Path, record: DeploymentRecord) -> None:
    """Emit a deployment.json for `record` (the scaffold's emission side, move 2). Writes exactly
    the five required fields, pretty-printed, newline-terminated -- the same shape `load_deployment`
    requires, so a record this function writes always round-trips through `load_deployment`
    unchanged (the property a hand-authored second writer could not guarantee)."""
    p = Path(path)
    p.write_text(json.dumps(asdict(record), indent=2, sort_keys=True) + "\n", encoding="utf-8")
