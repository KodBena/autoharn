#!/usr/bin/env python3
"""tools/setup_tui/destination.py -- design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md: the ONE
Port that answers "what is this directory's relationship to autoharn" (ADR-0012 P2). Before this
module the question was answered five different, disagreeing ways across screens.py and
bootstrap/new-project.sh (spec §1(a)): `screen_fork_target` refused any existing path outright,
`screen_birth` trusted `state["dest"]` unchecked, `screen_principals_authority` /
`screen_signed_genesis` / `screen_boundary` each hand-rolled their own `isdir`/`isfile` probe, and
new-project.sh `mkdir -p`s and merges into any occupied directory that lacks `deployment.json`.
This module is the closed classification every one of those sites now calls instead of
re-implementing (ADR-0000 Rule 2a): `classify_destination(path) -> DestinationState`.

THE SENTINEL (spec §2). Birth writes `<dest>/.autoharn-world.json` (new-project.sh, at the same
point it writes deployment.json) -- content `{"world", "run", "born", "autoharn_commit",
"schema"}`. It is the DECLARED marker; `deployment.json` + `legacy/led` remain the BEHAVIORAL
evidence a birth actually completed. `SENTINEL_NAME`/`SENTINEL_SCHEMA` below are the one place
that shape is named (ADR-0012 P1) -- new-project.sh's Python heredoc writer and this module's own
reader both import nothing from each other (shell can't import Python), so the two are kept in
sync by naming the same two constants in both places and by this module's docstring pointing at
the other (§3's cross-language floor, ADR-0012 P7: the Python classifier is the authority, the
shell reproduction says so in its own comment, drift is caught by the parity fixture, not by
codegen -- codegen would be disproportionate for three JSON keys and a marker check).

CLASSIFICATION RULES (spec §2, restated as code below):
  - absent path, or an EMPTY directory -> FRESH.
  - sentinel present + parseable + deployment.json + legacy/led all present -> AUTOHARN_COMPLETE,
    UNLESS the sentinel's own `world` contradicts deployment.json's own `name` (a hand-edited or
    drifted pair) -- that reads AUTOHARN_PARTIAL instead, never silently coerced to either
    reading (ADR-0002 rule 2: validate, don't guess which one is "right").
  - sentinel present but UNPARSEABLE is itself partial-birth evidence (a write that started and
    did not finish cleanly) -- AUTOHARN_PARTIAL, regardless of what else is present.
  - no sentinel, but deployment.json + legacy/led both present -> AUTOHARN_COMPLETE via
    BEHAVIORAL evidence alone (a world born before this spec existed; no retro-stamping runs are
    linear, ADR-0011 Rule 4 / CLAUDE.md's "runs are strictly linear" ruling).
  - any OTHER non-empty combination of {sentinel, deployment.json, legacy/led} -> AUTOHARN_PARTIAL,
    `evidence` names what is present and what is missing.
  - non-empty, none of the three markers -> FOREIGN, `evidence` samples up to 5 directory entries.

AMBIGUITY RESOLVED, NAMED (builder brief: "report, don't silently choose big"). The spec's sentinel
content names a `world` field and says a sentinel "contradicts deployment.json (different world
name)" is AUTOHARN_PARTIAL -- but `deployment.json` (filing/deployment_record.py) has no `world`
field, only `name` (the scaffold's own `--name`, default the dest-dir basename). This module
resolves the comparison as `sentinel["world"]` vs `DeploymentRecord.name`: new-project.sh (below,
and this module's sibling shell reproduction) writes the sentinel's `world` field as the SAME value
it writes into deployment.json's `name` field (`--new-world <world>` mode: `NAME` defaults to
`$NEW_WORLD` when `--name` is not given explicitly, and GLOSSARY.md's own `run`/`world` entry says
a world IS named for its run -- e.g. `run5` -- so the two fields denote the same fact at birth
time). The two can only drift apart from a LATER hand-edit or a `--force` re-scaffold under a
different `--name` against the same directory -- exactly the drift this branch exists to catch,
never coerced to either side. `run` is written as the same `--new-world` value (empty string for a
classic `--schema/--kern/--role` scaffold, which has no world/run concept at all -- GLOSSARY.md:
"worlds are numbered runs"; a classic scaffold is neither).

PURITY (spec §4): every function below is a READ-ONLY probe -- `Path.exists`/`is_dir`/`is_file`/
`iterdir`/`read_text` and `json.loads`, never a write. It is decision-phase legal under
design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md (the same class as the existing preflight probes in
tools/setup_tui/probes.py); `gates/setup_tui_purity_gate.py`'s AST walk flags writing-mode `open()`
calls and the mutation-verb `os.*` set, neither of which this module uses, so it stays clean with
no exemption-table change (constraint per the builder brief).

Stdlib + filing/deployment_record.py only, top-of-file imports (the lazy-import gate,
gates/no_lazy_imports.py, applies).
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

_FILING = str(Path(__file__).resolve().parents[2] / "filing")
if _FILING not in sys.path:
    sys.path.insert(0, _FILING)
import deployment_record  # filing/deployment_record.py -- the one home for deployment.json's shape

from tools.setup_tui.commit_executor import JOURNAL_FILENAME  # the wizard's OWN pre-birth
# scratch artifact -- see _IGNORED_ENTRIES below for why this classifier must know its name.

# The sentinel's own shape (spec §2) -- named ONCE here; new-project.sh's Python heredoc writer
# imports this module directly (it already runs `sys.path.insert(0, ".../filing")` for
# deployment_record, the identical shape) rather than re-typing the two constants.
SENTINEL_NAME = ".autoharn-world.json"
SENTINEL_SCHEMA = 1

_LEGACY_LED_REL = ("legacy", "led")

# LIVE HAZARD FOUND AND CLOSED DURING THIS BUILD (seen-red/setup-tui-dry-run-parity's own live
# WDR1 run against real Postgres): design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md's commit boundary
# (`commit_executor.execute`) `os.makedirs(dest, exist_ok=True)`s the destination and opens its
# own commit journal (JOURNAL_FILENAME) INSIDE `dest` BEFORE the first plan entry -- normally
# `screen_birth`'s own `new-project.sh --new-world` call -- ever runs. Without this exclusion, a
# perfectly ordinary birth into a genuinely-fresh destination would classify FOREIGN the instant
# new-project.sh's own shell-side gate ran (a non-empty dir with no autoharn markers -- the
# journal is neither the sentinel, deployment.json, nor legacy/led), REFUSING every live birth
# through the pure-core flow. The journal is wizard-owned bookkeeping, not foreign content and
# not birth evidence -- ignored here for the emptiness/occupancy question only; it plays no part
# in the sentinel/deployment.json/legacy-led marker checks below, which are unaffected.
_IGNORED_ENTRIES = frozenset({JOURNAL_FILENAME})


class DestKind(Enum):
    FRESH = "fresh"                         # absent, or an empty directory
    AUTOHARN_COMPLETE = "autoharn-complete"  # sentinel + deployment.json + legacy/led all present and consistent
    AUTOHARN_PARTIAL = "autoharn-partial"    # some birth evidence present, not all -- an interrupted birth
    FOREIGN = "foreign"                      # non-empty, no autoharn birth evidence


@dataclass(frozen=True)
class DestinationState:
    kind: DestKind
    evidence: tuple[str, ...]   # the observed facts the kind was derived from, for teaching copy


def _read_sentinel(sentinel_path: Path) -> tuple[bool, str | None, str | None]:
    """Returns (parseable, world, error). `world` is the sentinel's own `world` field (may be
    absent/None even on a parseable sentinel); `error` is set only when parsing failed."""
    try:
        data = json.loads(sentinel_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return False, None, str(exc)
    if not isinstance(data, dict):
        return False, None, f"sentinel top level is {type(data).__name__}, not an object"
    return True, data.get("world"), None


def _deployment_name(deployment_path: Path) -> str | None:
    """The deployment.json `name` field, or None if the file is absent/unreadable/malformed --
    unreadable/malformed still counts as the marker being PRESENT for classification purposes
    (a file exists, it just does not parse cleanly), matching this module's sentinel handling."""
    try:
        return deployment_record.load_deployment(deployment_path).name
    except deployment_record.DeploymentError:
        return None


def classify_destination(path: str | os.PathLike) -> DestinationState:
    """The one Port (spec §3): every consumer screen and new-project.sh's own shell reproduction
    calls this instead of re-implementing an isdir/isfile probe. Never writes; see module
    docstring's PURITY section."""
    p = Path(path)
    if not p.exists():
        return DestinationState(DestKind.FRESH, ("path does not exist",))
    if not p.is_dir():
        return DestinationState(DestKind.FOREIGN, (f"'{p}' exists and is not a directory",))
    try:
        entries = sorted(e.name for e in p.iterdir())
    except OSError as exc:
        return DestinationState(DestKind.FOREIGN, (f"could not list '{p}': {exc}",))
    real_entries = [e for e in entries if e not in _IGNORED_ENTRIES]
    if not real_entries:
        return DestinationState(DestKind.FRESH, ("empty directory (or wizard scratch only)",))

    sentinel_path = p / SENTINEL_NAME
    deployment_path = p / "deployment.json"
    legacy_led_path = p.joinpath(*_LEGACY_LED_REL)

    sentinel_present = sentinel_path.is_file()
    deployment_present = deployment_path.is_file()
    legacy_led_present = legacy_led_path.is_file()

    if sentinel_present:
        sentinel_ok, sentinel_world, sentinel_err = _read_sentinel(sentinel_path)
        if not sentinel_ok:
            return DestinationState(DestKind.AUTOHARN_PARTIAL, (
                f"sentinel present but unparseable: {sentinel_err}",
                f"deployment.json {'present' if deployment_present else 'missing'}",
                f"legacy/led {'present' if legacy_led_present else 'missing'}",
            ))
        if deployment_present and legacy_led_present:
            deployment_name = _deployment_name(deployment_path)
            if sentinel_world and deployment_name and sentinel_world != deployment_name:
                return DestinationState(DestKind.AUTOHARN_PARTIAL, (
                    f"sentinel world={sentinel_world!r} contradicts deployment.json "
                    f"name={deployment_name!r}",
                    "sentinel present", "deployment.json present", "legacy/led present",
                ))
            return DestinationState(DestKind.AUTOHARN_COMPLETE, (
                "sentinel present", "deployment.json present", "legacy/led present",
            ))
    elif deployment_present and legacy_led_present:
        # Pre-sentinel legacy world (spec §2): born before this spec existed, no retro-stamping.
        return DestinationState(DestKind.AUTOHARN_COMPLETE, (
            "no sentinel (pre-sentinel legacy world)",
            "deployment.json present", "legacy/led present",
        ))

    present_count = sum([sentinel_present, deployment_present, legacy_led_present])
    if present_count > 0:
        present = [n for n, ok in (("sentinel", sentinel_present),
                                    ("deployment.json", deployment_present),
                                    ("legacy/led", legacy_led_present)) if ok]
        missing = [n for n, ok in (("sentinel", sentinel_present),
                                    ("deployment.json", deployment_present),
                                    ("legacy/led", legacy_led_present)) if not ok]
        return DestinationState(DestKind.AUTOHARN_PARTIAL, (
            f"present: {', '.join(present)}", f"missing: {', '.join(missing)}",
        ))

    sample = real_entries[:5]
    more = f" (+{len(real_entries) - 5} more)" if len(real_entries) > 5 else ""
    return DestinationState(DestKind.FOREIGN, (
        "non-empty, no autoharn birth evidence", f"sample: {sample}{more}",
    ))
