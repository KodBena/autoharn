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
covers the value classes this rebuild's own new code treats as load-bearing identifiers
crossing a module boundary with a REAL, non-trivial contract of their own beyond `tools.
formwizard.ids`'s generic field/step-id/label/index/exit-code types -- a world name (spliced into
shell argv and SQL identifiers downstream), a destination path (queued into a Plan), and (work
item setup-tui-bare-types-retrofit, ledger rows 778/789, discharging durable row 26's own clause
"if the consumer is in an existing module, the module will be rewritten as appropriate" for this
package's PRE-EXISTING bare scalars) the five Postgres-splice values every `deployment.json`/
`boundary-multiplex.toml`-writing step constructs from operator answers or a scaffolded config:
`host`, database, schema, kern-schema, and role. Free-form prose already covered by
`formwizard.ids.Label`, and already-typed dataclasses (`plan.Hole`, `plan.Act`), are deliberately
not re-wrapped here.

PG* TYPES (`PgHost`/`PgDatabase`/`PgSchema`/`PgKernSchema`/`PgRole`), ADDED THIS RETROFIT: each is
a THIN named home over ONE of `tools/setup_tui/probes.py`'s own two closed-alphabet contracts
(`valid_hostname` for `PgHost`, `valid_identifier` for the other four) -- the contract itself
still lives in `probes.py` (ADR-0012 P1, imported not copied, exactly like `WorldName` above
composes `probes.valid_identifier`'s allowlist into its own stricter intersection), this module
only owns the CONSTRUCTING HOME. Four of the five (`PgDatabase`/`PgSchema`/`PgKernSchema`/
`PgRole`) share one literal contract (`probes.valid_identifier`) but are kept as four DISTINCT
classes rather than one generic wrapper -- the same reasoning `boundary_config_values.py`'s own
docstring gives for `LogLevel`/`SsePollIntervalSecs`/`MaxSseClients` staying separate frozen
dataclasses even where a bound is shared: a named type's job is to make it a construction-time
type error to pass a role where a schema was meant, not merely to check a shared alphabet (a
`PgRole` and a `PgDatabase` holding the same string are still different mistakes to make at a
call site). Every one of these five is a THIN validating wrapper: construction is the ONLY
checkpoint (`__post_init__`, no bypassable second path), `.parse()` only normalizes
(`.strip()`) before delegating to the same constructor, and `str(instance)` unwraps back to the
plain scalar every existing call site (subprocess argv, SQL/TOML text, a `state`/`deployment.json`
dict) already expects -- construction is a validating GATE the value passes through once, not a
wrapper type threaded through the whole pipeline (matching `boundary_config_values.py`'s own
"unwrapped back to a plain scalar only once each value has passed its own gate" idiom, not a
wider rewrite of every downstream consumer's signature).

WORLDNAME'S CONTRACT IS AN INTERSECTION, NOT JUST THE SQL/SHELL ALLOWLIST (work item
setup-tui-worldname-boundary-allowlist, flagged by the track-work-retirement builder, row 1317
arc). `world` is spliced into TWO independent downstream consumers with two INCOMPATIBLE
allowlists of their own:
  1. shell argv + SQL schema/role/kern identifiers (`steps_boundary.py`'s multiplex TOML values,
     `probes.valid_identifier`'s own contract) -- `[A-Za-z0-9_]+`.
  2. the boundary service's own deployment-slug allowlist (`serving/boundary_multiplex_config.py`
     spec §2, `_DEPLOYMENT_NAME_RE`) -- `[a-z0-9-]{1,64}` -- because `steps_boundary.py` writes
     `world` straight into `boundary-multiplex.toml`'s `[deployments.{world}]` table key, and the
     boundary service refuses to even bind its socket if that key doesn't match.
Before this fix, `WorldName` enforced ONLY allowlist 1 -- so a TUI-valid name like `MyWorld`
(uppercase) or `my_world` (underscore) sailed through Birth's own entry gate, got written into
`boundary-multiplex.toml` by `steps_boundary.py`, and only broke, silently to the operator at
THAT point, when the boundary service tried to load the config and refused by name -- a
downstream failure an upstream construction-time check should have caught. `WorldName`'s
`__post_init__` now enforces the INTERSECTION of both allowlists directly: `^[a-z0-9]{1,64}$`
(lowercase letters and digits only -- allowlist 2 excludes uppercase/underscore that allowlist 1
would otherwise permit -- bounded to 64 characters, allowlist 2's own cap). This is the SAME
answer `bootstrap/new-project.sh`'s `--profile tracker` mode already worked out for its own
`--name` (see that script's own comment naming this exact incompatibility) -- `[a-z0-9]+` -- with
the 64-character cap made explicit here since it is part of the true intersection even though
that shell check's own `case` pattern does not test length (cross-referenced there).

This is the SOLE SSOT for the world-name contract (ADR-0012 P1): `steps_rehearsal_birth.py`'s
Birth screen (the TUI entry point) and `steps_boundary.py`'s own re-parse of `state["world"]`
both construct through this ONE constructor -- there is no second copy of the allowlist to drift
out of sync with the boundary service's contract if that contract itself ever changes."""
from __future__ import annotations

import re
from dataclasses import dataclass

from tools.setup_tui import probes


class WorldNameError(ValueError):
    """A candidate world name fails the intersection of every downstream allowlist it is
    spliced into (shell/SQL identifier rules AND the boundary service's own deployment-slug
    contract) -- raised at construction, never discovered later inside a Popen argv or a
    boundary-multiplex.toml the service refuses to load."""


@dataclass(frozen=True)
class WorldName:
    """A validated world name. `__post_init__` is the ONLY enforcement point -- `WorldName(raw)`
    and `WorldName.parse(raw)` both end up here; there is no unchecked path to an instance."""
    value: str

    # The intersection of allowlist 1 (`[A-Za-z0-9_]+`, `probes.valid_identifier`'s own contract
    # for shell/SQL splice sites) and allowlist 2 (`[a-z0-9-]{1,64}`, the boundary service's own
    # deployment-slug contract, `serving/boundary_multiplex_config.py`'s `_DEPLOYMENT_NAME_RE`) --
    # see this module's own docstring for the full derivation. Lowercase letters and digits only
    # (uppercase/underscore excluded by allowlist 2, hyphen excluded by allowlist 1), 1-64 chars
    # (allowlist 2's own cap).
    _CONTRACT_RE = re.compile(r"^[a-z0-9]{1,64}$")

    def __post_init__(self) -> None:
        if not self.value:
            raise WorldNameError("world name is required (empty string)")
        if not self._CONTRACT_RE.fullmatch(self.value):
            raise WorldNameError(
                f"world name {self.value!r} must match {self._CONTRACT_RE.pattern} -- lowercase "
                f"letters and digits only, 1-64 characters. This is the INTERSECTION of the "
                f"shell/SQL identifier allowlist ([A-Za-z0-9_]+, law/adr/0012's interpreter-"
                f"boundary rule) and the boundary service's own deployment-slug allowlist "
                f"([a-z0-9-]{{1,64}}, serving/boundary_multiplex_config.py spec §2) that this "
                f"world name is written into verbatim as a boundary-multiplex.toml "
                f"[deployments.{{name}}] table key (tools/setup_tui/steps_boundary.py) -- a name "
                f"outside this intersection would pass here but make the boundary service refuse "
                f"to start later, silently to this screen. Pick a name using only lowercase "
                f"letters and digits.")

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


class PgHostError(ValueError):
    """A candidate Postgres host fails `probes.valid_hostname`'s contract (letters, digits, dot,
    hyphen, underscore -- a DNS name or dotted-quad, never a bare SQL/shell identifier) -- raised
    at construction, never discovered later inside a `psql` argv or a written TOML file."""


@dataclass(frozen=True)
class PgHost:
    """A validated Postgres host (a DNS name or IP literal). Contract lives in
    `probes.valid_hostname` (ADR-0012 P1, imported not copied); this class only owns the
    constructing home. `__post_init__` is the ONLY enforcement point."""
    value: str

    def __post_init__(self) -> None:
        if not probes.valid_hostname(self.value):
            raise PgHostError(
                f"host {self.value!r} must match probes.valid_hostname's contract (letters, "
                f"digits, dot, hyphen, underscore) -- refusing to splice it into program text "
                f"(law/adr/0012's interpreter-boundary rule).")

    @staticmethod
    def parse(raw: str) -> "PgHost":
        return PgHost(raw.strip())

    def __str__(self) -> str:
        return self.value


class PgIdentifierError(ValueError):
    """A candidate Postgres identifier (database/schema/kern-schema/role name) fails
    `probes.valid_identifier`'s closed alphabet (`[A-Za-z0-9_]+`) -- raised at construction, never
    discovered later inside a SQL/shell splice site."""


def _check_pg_identifier(label: str, value: str) -> None:
    """ONE shared check, four named homes below (`PgDatabase`/`PgSchema`/`PgKernSchema`/
    `PgRole`) -- same idiom `boundary_config_values.IdentityEnforcementOverride.__post_init__`
    uses to re-run `IdentityEnforcementPosture.parse`'s own check rather than hand-copy it."""
    if not probes.valid_identifier(value):
        raise PgIdentifierError(
            f"{label} {value!r} must match [A-Za-z0-9_]+ (probes.valid_identifier's contract) -- "
            f"refusing to splice it into SQL/shell/config text (law/adr/0012's interpreter-"
            f"boundary rule).")


@dataclass(frozen=True)
class PgDatabase:
    """A validated Postgres database name. See this module's own docstring ("PG* TYPES") for why
    this is a distinct class from `PgSchema`/`PgKernSchema`/`PgRole` despite sharing one
    alphabet."""
    value: str

    def __post_init__(self) -> None:
        _check_pg_identifier("database name", self.value)

    @staticmethod
    def parse(raw: str) -> "PgDatabase":
        return PgDatabase(raw.strip())

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PgSchema:
    """A validated Postgres schema name (a world's own ledger schema, e.g. `boundary-multiplex.
    toml`'s `pgschema`). See this module's own docstring ("PG* TYPES")."""
    value: str

    def __post_init__(self) -> None:
        _check_pg_identifier("schema", self.value)

    @staticmethod
    def parse(raw: str) -> "PgSchema":
        return PgSchema(raw.strip())

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PgKernSchema:
    """A validated Postgres kernel-schema name (a world's own `<world>_kernel`-shaped schema,
    e.g. `boundary-multiplex.toml`'s `pgkern`). See this module's own docstring ("PG* TYPES")."""
    value: str

    def __post_init__(self) -> None:
        _check_pg_identifier("kern schema", self.value)

    @staticmethod
    def parse(raw: str) -> "PgKernSchema":
        return PgKernSchema(raw.strip())

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PgRole:
    """A validated Postgres role name. See this module's own docstring ("PG* TYPES")."""
    value: str

    def __post_init__(self) -> None:
        _check_pg_identifier("role", self.value)

    @staticmethod
    def parse(raw: str) -> "PgRole":
        return PgRole(raw.strip())

    def __str__(self) -> str:
        return self.value
