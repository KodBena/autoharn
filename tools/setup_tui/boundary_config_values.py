#!/usr/bin/env python3
"""tools/setup_tui/boundary_config_values.py -- the ONE constructing home for the five NEW
boundary-multiplex config values `steps_boundary.py` resolves from operator answers (work item
setup-tui-config-extension, fix round on review row 776, finding 1: CLAUDE.md/ledger row 26 --
"every value construction goes through one SSOT that checks a contract; no bare ints, no bare
strs"). Before this fix round, `log_level`/`identity_enforcement`/
`identity_enforcement_override`/`sse_poll_interval_secs`/`max_sse_clients` traveled from
`answers` through `state`/`config_seam.py` as bare str/float/int, checked only by ad hoc
`_validate_*` helper functions local to `steps_boundary.py` -- no single named type owned the
contract.

Two of the five (`identity_enforcement` and its per-deployment override) delegate to
`serving/boundary_multiplex_config.IdentityEnforcementPosture.parse` -- that module's own
constructing home ALREADY exists and already enforces the SAME closed vocabulary at both the
hub-wide default and the per-deployment override sites (its own docstring says so); this module
does not invent a parallel one, only re-exports it plus the thin "inherit" wrapper the override
field alone needs.

The other three (`log_level`, `sse_poll_interval_secs`, `max_sse_clients`) get new, thin, frozen
dataclasses HERE rather than in `serving/`: `serving/boundary_diagnostic_log.py` and
`serving/boundary_multiplex_config.py` already name the vocabulary/bounds
(`LEVELS`/`MAX_SSE_POLL_INTERVAL_SECS`/`MAX_SSE_CLIENTS_CEILING`) but never themselves construct
a typed wrapper -- the server side reads a raw TOML dict at load time and stays that way, out of
this fix round's scope. These three typed homes live TUI-side because their ONLY consumer is this
wizard's own answers -> resolved-value -> written-TOML-byte pipeline; the CONTRACT itself (the
vocabulary, the numeric bounds) still lives in `serving/`, imported here, never copied (ADR-0012
P1).

SECOND JOB (fix round finding 2): `IDENTITY_ENFORCEMENT_OVERRIDE_INHERIT` is the ONE shared
public home for the "no override, inherit the hub-wide default" sentinel. Before this fix round,
`config_seam.py` reached into `steps_boundary._IDENTITY_ENFORCEMENT_OVERRIDE_INHERIT` (a private
name) plus two hop-through aliases (`steps_boundary.boundary_diagnostic_log`/
`.boundary_multiplex_config`, re-exported off a module that has nothing to do with owning them).
Both `steps_boundary.py` and `config_seam.py` now import this module directly instead.

Stdlib + serving/ only, top-of-file imports (the lazy-import gate applies)."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

# Guarded (if-not-in-sys.path), matching `tools/setup_tui/destination.py`'s own cited precedent
# (the same guard `steps_boundary.py`'s own sys.path insert was fixed to use this same fix round,
# finding 3) -- an unguarded insert would grow sys.path by one duplicate entry per re-import.
_SERVING = str(Path(__file__).resolve().parents[2] / "serving")
if _SERVING not in sys.path:
    sys.path.insert(0, _SERVING)
import boundary_diagnostic_log  # noqa: E402  (serving/boundary_diagnostic_log.py -- the ONE home for LEVELS/DEFAULT_LEVEL)
import boundary_multiplex_config  # noqa: E402  (serving/boundary_multiplex_config.py -- the ONE home for the identity_enforcement/SSE vocabulary+bounds)

# Re-exported, not re-implemented (ADR-0012 P1): `serving/boundary_multiplex_config.py`'s own
# `IdentityEnforcementPosture.parse` is ALREADY the constructing home for both the hub-wide
# default and a per-deployment override -- this module's own callers reach it through this one
# name rather than importing `boundary_multiplex_config` a second time under a different alias.
IdentityEnforcementPosture = boundary_multiplex_config.IdentityEnforcementPosture

# The "no override -- inherit the hub-wide default" sentinel. PUBLIC (fix round finding 2): the
# ONE shared home both `steps_boundary.py` (constructs the field's default/choices against it)
# and `config_seam.py` (falls back to it when a state dict never reached `steps_boundary.submit`)
# import, replacing the prior private reach-through.
IDENTITY_ENFORCEMENT_OVERRIDE_INHERIT = "inherit"


@dataclass(frozen=True)
class LogLevel:
    """boundary-multiplex.toml's own `log_level` -- construct ONLY via `.parse()`/`.default()`
    (never `LogLevel(raw)` directly from outside this module); `__post_init__` still guards
    direct construction, matching `IdentityEnforcementPosture`'s own idiom
    (`serving/boundary_multiplex_config.py`)."""
    value: str

    def __post_init__(self) -> None:
        if self.value not in boundary_diagnostic_log.LEVELS:
            raise ValueError(
                f"log_level: {self.value!r} is not one of "
                f"{sorted(boundary_diagnostic_log.LEVELS, key=boundary_diagnostic_log.LEVELS.get)} "
                f"(serving/boundary_diagnostic_log.LEVELS is the one home for this vocabulary).")

    @classmethod
    def default(cls) -> "LogLevel":
        return cls(boundary_diagnostic_log.DEFAULT_LEVEL)

    @classmethod
    def parse(cls, raw: str) -> "LogLevel":
        return cls(raw)


@dataclass(frozen=True)
class SsePollIntervalSecs:
    """boundary-multiplex.toml's own `sse_poll_interval_secs` -- bounds enforced against
    `serving/boundary_multiplex_config.MAX_SSE_POLL_INTERVAL_SECS`, imported not copied (that
    module's own docstring: this bound is PUBLIC exactly so the setup TUI can import rather than
    duplicate it)."""
    value: float

    def __post_init__(self) -> None:
        if not (0 < self.value <= boundary_multiplex_config.MAX_SSE_POLL_INTERVAL_SECS):
            raise ValueError(
                f"sse_poll_interval_secs: {self.value!r} must be in "
                f"(0, {boundary_multiplex_config.MAX_SSE_POLL_INTERVAL_SECS}].")

    @classmethod
    def default(cls) -> "SsePollIntervalSecs":
        return cls(boundary_multiplex_config.DEFAULT_SSE_POLL_INTERVAL_SECS)

    @classmethod
    def parse(cls, raw: str) -> "SsePollIntervalSecs":
        try:
            value = float(raw)
        except (TypeError, ValueError):
            raise ValueError(f"sse_poll_interval_secs: {raw!r} must be a number.") from None
        return cls(value)


@dataclass(frozen=True)
class MaxSseClients:
    """boundary-multiplex.toml's own `max_sse_clients` -- bounds enforced against
    `serving/boundary_multiplex_config.MAX_SSE_CLIENTS_CEILING`, imported not copied."""
    value: int

    def __post_init__(self) -> None:
        if not (1 <= self.value <= boundary_multiplex_config.MAX_SSE_CLIENTS_CEILING):
            raise ValueError(
                f"max_sse_clients: {self.value!r} must be in "
                f"[1, {boundary_multiplex_config.MAX_SSE_CLIENTS_CEILING}].")

    @classmethod
    def default(cls) -> "MaxSseClients":
        return cls(boundary_multiplex_config.DEFAULT_MAX_SSE_CLIENTS)

    @classmethod
    def parse(cls, raw: str) -> "MaxSseClients":
        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise ValueError(f"max_sse_clients: {raw!r} must be a whole number.") from None
        return cls(value)


@dataclass(frozen=True)
class IdentityEnforcementOverride:
    """boundary-multiplex.toml's own per-deployment `identity_enforcement` override -- EITHER
    `IDENTITY_ENFORCEMENT_OVERRIDE_INHERIT` (no override; the hub-wide default applies to this
    deployment) OR a value in `boundary_multiplex_config.IDENTITY_ENFORCEMENT_POSTURES`.
    Construct ONLY via `.parse()`."""
    raw: str

    def __post_init__(self) -> None:
        if self.raw != IDENTITY_ENFORCEMENT_OVERRIDE_INHERIT:
            # Re-uses the SAME constructing home as the hub-wide default (this fix round's own
            # finding 1 instruction) purely for its validation side effect -- an out-of-vocabulary
            # override gets the IDENTICAL teach-text a bad hub-wide value would.
            IdentityEnforcementPosture.parse(
                self.raw, where="identity_enforcement override (per-deployment)",
                path=Path("<setup TUI -- boundary-multiplex.toml not yet written>"))

    @property
    def inherits(self) -> bool:
        return self.raw == IDENTITY_ENFORCEMENT_OVERRIDE_INHERIT

    @classmethod
    def default(cls) -> "IdentityEnforcementOverride":
        return cls(IDENTITY_ENFORCEMENT_OVERRIDE_INHERIT)

    @classmethod
    def parse(cls, raw: str) -> "IdentityEnforcementOverride":
        return cls(raw)
