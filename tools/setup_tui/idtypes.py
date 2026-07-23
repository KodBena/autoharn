#!/usr/bin/env python3
"""tools/setup_tui/idtypes.py -- checked value types for this package's own highest-stakes bare
values (maintainer's permanent rule, ledger row 1105: "no bare types: every value construction
goes through 1 SSOT that checks a contract appropriate to the value's use case"; second
correction: construction IS validation -- every contract below is enforced in `__post_init__`,
never left to a bypassable "checked by review" convention on an open constructor. An illegal
instance is UNCONSTRUCTABLE: `WorldName("bad name!")` raises the SAME way `WorldName.parse("bad "
"name!")` does, because `.parse` is now a thin normalizing wrapper (`.strip()`) around the SAME
constructor every other call site uses -- there is exactly one path to a legal instance.

SCOPE, STATED HONESTLY (this build's own judgment call -- see the build report): this module
covers the two value classes this rebuild's own new code treats as load-bearing identifiers
crossing a module boundary with a REAL, non-trivial contract of their own beyond `tools.
formwizard.ids`'s generic field/step-id/label/index/exit-code types -- a world name (spliced into
shell argv and SQL identifiers downstream) and a destination path (queued into a Plan). Free-form
prose already covered by `formwizard.ids.Label`, and already-typed dataclasses (`plan.Hole`,
`plan.Act`), are deliberately not re-wrapped here."""
from __future__ import annotations

from dataclasses import dataclass

from tools.setup_tui import probes


class WorldNameError(ValueError):
    """A candidate world name fails the same allowlist every downstream shell/SQL splice site
    already required -- raised at construction, never discovered later inside a Popen argv."""


@dataclass(frozen=True)
class WorldName:
    """A validated world name. `__post_init__` is the ONLY enforcement point -- `WorldName(raw)`
    and `WorldName.parse(raw)` both end up here; there is no unchecked path to an instance."""
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise WorldNameError("world name is required (empty string)")
        if not probes.valid_identifier(self.value):
            raise WorldNameError(
                f"world name {self.value!r} must match [A-Za-z0-9_]+ (law/adr/0012's "
                f"interpreter-boundary rule -- it is spliced into shell argv and SQL schema/"
                f"role names)")

    @staticmethod
    def parse(raw: str) -> "WorldName":
        """Normalize (strip whitespace) THEN construct -- the constructor still does the real
        checking; this is a convenience for a caller holding raw operator/config text, not a
        second validation path."""
        return WorldName(raw.strip())

    def __str__(self) -> str:
        return self.value


class DestPathError(ValueError):
    """A candidate destination path is empty or otherwise not a plausible filesystem path."""


@dataclass(frozen=True)
class DestPath:
    """A validated destination-directory path -- non-empty, no NUL byte, the minimum a caller may
    trust before queuing a Plan entry that shells `cp -a`/writes into it. (Existence/
    classification is a SEPARATE, richer question `destination.classify_destination` already
    owns -- this constructor's contract is only "a real candidate path string", not "exists" or
    "is safe to write into"; conflating the two would make this type re-implement that module
    instead of composing with it.)"""
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise DestPathError("destination directory is required (empty string)")
        if "\x00" in self.value:
            raise DestPathError("destination directory contains a NUL byte -- not a real path")

    @staticmethod
    def parse(raw: str) -> "DestPath":
        return DestPath(raw.strip())

    def __str__(self) -> str:
        return self.value
