#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T11:06:10Z
#   last-change: 2026-07-18T18:21:51Z
#   contributors: be693afb/main, e4410ef6/main, ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""deployment_record -- the ONE home for a project instance's `deployment.json` SHAPE
(vestigial_documentation/design/ORCH-OPUS-READINESS.md move 1; ADR-0012 P1). A deployment record is the machine-readable
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
`settings.json`'s baked env, the WALKTHROUGH's `-v` vars (vestigial_documentation/design/ORCH-OPUS-READINESS.md's friction
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

# `name` is OPTIONAL and NOT part of "where the ledger lives" -- it is this project's own label
# (bootstrap/new-project.sh's --name, default the dest-dir basename), used live by the scaffolded
# `judge` shim as the target-name argument to autoharn's engine/ledger_differential.py (and hence
# the derivations/<name>/ banking subdirectory under autoharn's own tree -- see judge.tmpl).
# Extending the record with it (BACKLOG maintainer ruling 2026-07-11, "live verbs") is the fix this
# module's own docstring anticipates ("extra keys ... a future consumer adds a field to does not
# break this loader"): still ONE home for the shape, `_REQUIRED_FIELDS` unchanged (name is not
# required -- a record predating this field, e.g. an already-settled world's deployment.json,
# stays valid; a consumer that NEEDS `name` -- `judge` -- refuses loudly itself when it is absent,
# same posture as every other missing-fact refusal in this module).

# `boundary_url`/`boundary_deployment` are OPTIONAL, the SAME "extra field a future consumer adds"
# shape `name` above already established -- design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md
# §5: "Facts the shim needs (base URL, deployment name) live in the deployment's existing
# deployment.json, two new keys, refused-if-absent by the new shims." `boundary_url` is the served
# boundary's own base URL (e.g. "http://127.0.0.1:8420", NO trailing slash, NO `/d/{deployment}`
# segment -- that segment is `boundary_deployment` below, kept separate rather than folded into
# one combined URL so a caller never has to parse one back out of the other). `boundary_deployment`
# is the `/d/{name}` path segment THIS deployment answers under on the served side -- deliberately
# a SEPARATE field from `name` above (a served TOML config's own `[deployments.NAME]` key need not
# equal this project's own local label; reusing `name` for a second meaning would be exactly the
# lying-signature class this project's house style forbids, the same reasoning serving/README.md
# already gives for `audit_served.py`'s own `--deployment-name` vs `--deployment` split). This
# module stays the ONE home for the shape (P1): NEITHER field is added to `_REQUIRED_FIELDS` (an
# existing, non-served deployment.json -- and every OTHER consumer of this module, `led`/`judge`/
# `engine/targets.py`/every filing/ reader -- stays valid with neither key present); the REBASED
# shims (serving/boundary_cli_client.py) are the ones that refuse loudly when either is absent,
# exactly the posture `name`'s own comment describes for `judge`.


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
    name: str | None = None  # OPTIONAL -- see the comment above _REQUIRED_FIELDS for why this
                              # field exists and why it is not one of the five required ones.
    boundary_url: str | None = None          # OPTIONAL -- see the comment above _REQUIRED_FIELDS
    boundary_deployment: str | None = None   # OPTIONAL -- see the same comment


def load_deployment(path: str | Path) -> DeploymentRecord:
    """Load and validate a deployment.json. Raises `DeploymentError` (never returns a partial or
    guessed record) on: a missing file, unreadable/non-UTF-8 bytes, invalid JSON, a JSON value that
    is not an object, a missing required field, or a required field that is not a non-empty string.
    Extra keys beyond the five required ones are accepted and ignored (a forward-compatible record
    a future consumer adds a field to does not break this loader) -- EXCEPT `name`, which this
    loader knows about and validates IF PRESENT (must be a non-empty string; a record predating
    this field simply has no `name` attribute set, `None`, not an error)."""
    p = Path(path)
    if not p.is_file():
        raise DeploymentError(
            f"deployment record not found at {p} -- a project with no deployment record is refused, "
            f"never silently un-resolved. Write one (deployment_record.write_deployment) or point "
            f"this caller's deployment-path setting at the right path (e.g. engine/targets.py's "
            f"LEDGER_DEPLOYMENT, or PICKUP_DEPLOYMENT -- used by pickup, judge, and led alike).")
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
    name = raw.get("name")
    if name is not None and (not isinstance(name, str) or not name):
        raise DeploymentError(
            f"deployment record at {p} has a non-string or empty value for optional field 'name' "
            f"(omit the key entirely for 'not set', or give it a non-empty string)")
    boundary_url = raw.get("boundary_url")
    if boundary_url is not None and (not isinstance(boundary_url, str) or not boundary_url):
        raise DeploymentError(
            f"deployment record at {p} has a non-string or empty value for optional field "
            f"'boundary_url' (omit the key entirely for 'not set', or give it a non-empty string)")
    boundary_deployment = raw.get("boundary_deployment")
    if boundary_deployment is not None and (not isinstance(boundary_deployment, str) or not boundary_deployment):
        raise DeploymentError(
            f"deployment record at {p} has a non-string or empty value for optional field "
            f"'boundary_deployment' (omit the key entirely for 'not set', or give it a "
            f"non-empty string)")
    return DeploymentRecord(db=raw["db"], host=raw["host"], schema=raw["schema"],
                             kern=raw["kern"], role=raw["role"], name=name,
                             boundary_url=boundary_url, boundary_deployment=boundary_deployment)


def write_deployment(path: str | Path, record: DeploymentRecord) -> None:
    """Emit a deployment.json for `record` (the scaffold's emission side, move 2). Writes exactly
    the five required fields plus `name` (if `record.name` is set -- omitted entirely otherwise, so
    a caller not using `name` gets the exact same five-key shape as before), pretty-printed,
    newline-terminated -- the same shape `load_deployment` requires, so a record this function
    writes always round-trips through `load_deployment` unchanged (the property a hand-authored
    second writer could not guarantee)."""
    p = Path(path)
    data = asdict(record)
    for optional_field in ("name", "boundary_url", "boundary_deployment"):
        if data.get(optional_field) is None:
            data.pop(optional_field, None)
    p.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
