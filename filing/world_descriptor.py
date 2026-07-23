#!/usr/bin/env python3
"""world_descriptor -- the ONE home for the multiplexer registry descriptor's SHAPE (design/
FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md §4, ledger rows 1151-1183).

SCOPE, named explicitly (this build's own honest boundary, not silently narrowed): this module
provides the descriptor SHAPE and a write/scan pair, tested against a scratch registry directory
(seen-red/world-descriptor-registry/run_fixtures.py -- write/scan round-trip, re-write-overwrites,
malformed-world-name refusal, malformed-registry-entry refusal, empty-registry-dir scan). It is
DELIBERATELY NOT wired into
`bootstrap/new-project.sh`'s own birth sequence in this build -- that script is a 1200+-line,
heavily load-bearing scaffold every existing world/fixture depends on, and wiring a new write
into its birth sequence is a genuinely separate, larger change than this module's own shape;
rushing it here risks a half-tested edit to code many other things assume is stable. Named as a
follow-on, not silently skipped (CLAUDE.md's hazard-fixing duty: flag loudly rather than route
around). Likewise this build does NOT perform the host-level hub consolidation the spec's §4
describes (retiring this host's standing 8433/8422 boundary_service processes into one) -- that
is a live-infrastructure change touching services OTHER concurrent sessions on this host may
depend on right now, a load-bearing judgment call this build routes to the maintainer rather
than executing unilaterally (see the umbrella build's own completion report).

DESCRIPTOR SHAPE (spec §4: "world name, host, boundary URL, epoch, capabilities, protocol
version, the named-empty identity slots"). `s41_key_binding_slot` is the ONE named-empty slot
this build's row-1162 discipline calls for -- present, always null in v1, never designing or
foreclosing the future human-only key-binding tier s41 already models at the kernel layer
(kernel/lineage/s41-principal-bindings-and-relations.sql); a future build fills it in, this one
only refuses to pretend it doesn't exist.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import is top-of-file. No bare types in
new Python (ledger row 1105): every function signature below carries its return-type annotation.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

# The SAME wire-protocol version constant this build's client/service pair use (serving/
# boundary_models.py's WIRE_PROTOCOL_VERSION, serving/boundary_cli_client.py's disclosed
# duplicate) -- a THIRD disclosed duplicate here, same convention, same reason: this module has
# no business importing serving/boundary_models.py's pydantic dependency just to read one
# version string. Kept in sync by hand; a drift-detection fixture is this build's own tripwire.
DESCRIPTOR_WIRE_PROTOCOL_VERSION = "1"

_WORLD_NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")  # same alphabet as boundary-multiplex.toml's
                                                     # own deployment-name rule (boundary_
                                                     # multiplex_config.py's _DEPLOYMENT_NAME_RE)


class DescriptorError(Exception):
    """Raised, never swallowed: a descriptor could not be written (bad world name, unwritable
    registry directory) or a registry directory entry could not be parsed (not JSON, not an
    object, missing a required key) -- ADR-0002 rung 1, construction-time refusal."""


@dataclass(frozen=True)
class WorldDescriptor:
    """One world's registration in the multiplexer's registry directory (spec §4). Written once
    at birth (a follow-on wires this into `bootstrap/new-project.sh`, see module docstring);
    read by the multiplexer to pick up new worlds without hand-edited config."""

    world: str                       # the deployment/schema name (boundary-multiplex.toml's
                                      # own [deployments.NAME] key)
    host: str                        # the Postgres host this world's ledger lives on
    boundary_url: str                # this world's own served boundary base URL (no /d/ segment)
    boundary_deployment: str         # the /d/{name} path segment
    epoch: int                       # this world's migration_epoch (kern.migration_epoch.epoch),
                                      # 0 for a freshly-scaffolded world with no prior epoch bump
    protocol_version: str = DESCRIPTOR_WIRE_PROTOCOL_VERSION
    authn_mode: str = "single-operator"       # row-1162 named-empty-slot discipline (spec §3)
    s41_key_binding_slot: str | None = None   # NAMED, always None in v1 -- see module docstring

    def __post_init__(self) -> None:
        if not _WORLD_NAME_RE.match(self.world):
            raise DescriptorError(
                f"world name {self.world!r} does not match {_WORLD_NAME_RE.pattern!r} -- refused "
                f"at construction (the same alphabet boundary-multiplex.toml's own deployment "
                f"names are held to).")


def write_descriptor(registry_dir: str | Path, descriptor: WorldDescriptor) -> Path:
    """Writes `<registry_dir>/<world>.json`, creating `registry_dir` if absent. Overwrites any
    existing descriptor for the same world name (birth is idempotent by world name -- a re-run
    of the same world's birth act re-declares the same facts, never silently merges with a
    stale prior write)."""
    reg = Path(registry_dir)
    reg.mkdir(parents=True, exist_ok=True)
    path = reg / f"{descriptor.world}.json"
    path.write_text(json.dumps(asdict(descriptor), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def scan_registry(registry_dir: str | Path) -> list[WorldDescriptor]:
    """Reads every `*.json` descriptor in `registry_dir`, sorted by world name. Raises
    `DescriptorError` naming the offending file on any entry that fails to parse -- a
    multiplexer refuses to silently skip a malformed registration (ADR-0002)."""
    reg = Path(registry_dir)
    if not reg.is_dir():
        return []
    out: list[WorldDescriptor] = []
    for path in sorted(reg.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            raise DescriptorError(f"registry entry {path} could not be read as JSON "
                                   f"({e.__class__.__name__}: {e})") from e
        if not isinstance(raw, dict):
            raise DescriptorError(f"registry entry {path} is not a JSON object")
        try:
            out.append(WorldDescriptor(**raw))
        except TypeError as e:
            raise DescriptorError(f"registry entry {path} has an unrecognized shape "
                                   f"({e.__class__.__name__}: {e})") from e
    return sorted(out, key=lambda d: d.world)
