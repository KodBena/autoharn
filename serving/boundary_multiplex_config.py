#!/usr/bin/env python3
"""boundary_multiplex_config -- the ONE home for the boundary-multiplex TOML config's SHAPE
(design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md §3; ledger decision row 1631, ratifying
the spec WITH its §8 defaults: TOML, mandatory `/d/{name}` discriminator even for one
deployment, global+per-deployment admission bounds, `./legacy/` retirement left open).

WHAT THIS FILE OWNS (ADR-0012 P1 -- one home, not a second reader): parsing and validating
`boundary-multiplex.toml`'s WHOLE shape before `serving/boundary_service.py` ever binds a
socket (spec §3: "the WHOLE file validates before the socket binds -- unknown keys anywhere
refuse startup by name; a missing required key refuses by name; zero deployments refuses").
Per-deployment reachability is deliberately NOT probed here (spec §3's own words: "startup
validates the config's shape, not the world's health") -- an unreachable deployment's kernel
stays a per-REQUEST typed 503 `infra_failure`, exactly as the single-deployment service always
behaved.

SHAPE, one flagged choice named on the record (ADR-0000 2(a) "smallest honest choice, flagged
loudly" -- the spec's own §3 example TOML names only `pghost`/`pgdatabase`/`pguser` per
deployment, omitting `schema`/`kern` even though `serving/boundary_service.py`'s
`BoundaryConfig` requires both to run a single kernel query. The example is illustrative, not
a closed key enumeration (the spec's prose never states "these three keys are the complete
set"), and this module cannot invent a schema/kern naming convention from the deployment name
without silently presuming every operator names their ledger schema after the TOML table key
-- exactly the kind of guessed default ADR-0002 forbids. The smallest honest resolution: two
more `pg`-prefixed keys, `pgschema`/`pgkern`, required alongside the spec's three -- named
here, once, so the choice is auditable rather than buried in a validator's literal set.)

```toml
[deployments.autoharn1]
pghost = "192.168.122.1"
pgdatabase = "autoharn1"
pguser = "led_writer"
pgschema = "autoharn1"
pgkern = "autoharn1_kernel"
```

Every value maps onto `filing/deployment_record.py`'s `DeploymentRecord` -- the SAME shape
`serving/boundary_service.py`'s single-deployment predecessor already validated identifiers
against (`BoundaryConfig.__init__`'s `_IDENT_RE` check on `schema`/`kern`/`role`, construction
time, ADR-0002 rung 1) -- this module reuses that record type rather than inventing a second
one (P1 again): `pghost` -> `host`, `pgdatabase` -> `db`, `pguser` -> `role`, `pgschema` ->
`schema`, `pgkern` -> `kern`; the TOML table key itself becomes `DeploymentRecord.name` (never
optional here -- every multiplexed deployment IS named, by construction).

Deployment names: `[a-z0-9-]{1,64}` (spec §2), refused at config load otherwise -- the name is
an operator LABEL, never interpolated into SQL (it only ever selects a dict entry; the entry's
own fields carry the connection facts, and THOSE still pass through `BoundaryConfig`'s own
identifier check downstream).

`tomllib` is Python 3.11+ stdlib (no new dependency; matches this project's existing "no new
system packages" convention for `serving/`).

LOG LEVEL (design/FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md §2, "Config"): one new OPTIONAL
top-level key, `log_level` -- a string, validated against `boundary_diagnostic_log.LEVELS` (the
ONE home for the valid-level set, ADR-0012 P1: this module imports it rather than carrying a
second copy that could drift). Absent entirely -> `boundary_diagnostic_log.DEFAULT_LEVEL`
("INFO") -- an existing `boundary-multiplex.toml`, authored before this key existed, still
validates unchanged (ADR-0004: this addition does not retroactively demand every existing
config be touched). An unrecognized value is refused loudly, by name, in the SAME whole-file
validation pass every other axis of this file already goes through -- before the socket ever
binds (spec §3's own "the WHOLE file validates before the socket binds", extended to the one
new key rather than carving out an exception for it).

IDENTITY_ENFORCEMENT (design/FABLE-DISPATCH-MECHANICS-SPEC.md §3, ledger row 1471 sub-item 4c):
one new OPTIONAL top-level key, `identity_enforcement` -- "grace" (default) or "enforce", the
anonymous-authority-bearing-write refusal's own posture. Same whole-file validation pass,
same before-the-socket-binds discipline, same import-the-vocabulary-don't-duplicate-it
relationship this module already has with `boundary_diagnostic_log.LEVELS` for `log_level`.

PER-DEPLOYMENT IDENTITY_ENFORCEMENT OVERRIDE (work item identity-enforcement-split-flip, ledger
row 619's adjudication): a `[deployments.NAME]` table MAY ALSO carry its own `identity_enforcement`
key -- same closed vocabulary, same validation -- overriding the top-level default for THAT
deployment only. The top-level key stays exactly what it was: the hub-wide default, consulted by
any deployment that does not carry its own override (absent top-level AND absent per-deployment
= "grace" = today's behavior, byte-identical -- this addition is purely ADDITIVE). An invalid
value at EITHER location refuses loudly at config validation, before the socket ever binds,
naming both valid values and both key locations a posture can be set at (a single constructing
home, `IdentityEnforcementPosture.parse` below, so the teach-text is identical regardless of
which of the two sites got it wrong -- CLAUDE.md/ledger row 26, "no bare types": every value gets
a named type with a single constructing home enforcing its contract). `_load_and_validate`
returns the fully-resolved EFFECTIVE posture per deployment (top-level default already folded
in) so `serving/boundary_service.py` never re-derives the "override or default" merge itself
(ADR-0012 P1).

SSE TUNABLES (design/FABLE-BOUNDARY-SSE-EVENTS-SPEC.md §1 items 1/4, work item
boundary-sse-events, ledger row 169): two new OPTIONAL top-level keys, same whole-file
validation pass, same before-the-socket-binds discipline. `sse_poll_interval_secs` -- how often
the shared per-deployment head-watcher polls `max(id)` (a positive number of seconds; the spec
names 2 as the default). `max_sse_clients` -- the SEPARATE, hub-wide bound on concurrently open
`GET /d/{deployment}/events` connections (the spec's own words: "NEVER the 24-slot inflight
gate"; a positive integer, the spec names 16 as the default). Both are process-wide (one hub,
not per-deployment -- the spec's own "per hub" phrasing for `MAX_SSE_CLIENTS`), exactly like
`log_level`/`identity_enforcement` above.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import is top-of-file.
"""
from __future__ import annotations

import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

# filing/ needs its own explicit sys.path entry (not a package-relative import) -- the same
# reason `serving/boundary_service.py`'s own module docstring gives for its identical insert:
# this module may be imported either as `serving.boundary_multiplex_config` (repo root on
# sys.path[0]) or run/imported with `serving/` itself as the working import root, and neither
# form puts `filing/` on sys.path automatically.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "filing"))
import deployment_record  # noqa: E402
import boundary_diagnostic_log  # noqa: E402  (serving/boundary_diagnostic_log.py -- the ONE home for LEVELS/DEFAULT_LEVEL, ADR-0012 P1)

# Deployment names are operator LABELS (spec §2): [a-z0-9-]{1,64}, refused at load otherwise.
# CROSS-REFERENCE (work item setup-tui-worldname-boundary-allowlist, row 1317 arc): this pattern
# is one leg of an intersection two OTHER call sites independently derive and enforce upstream of
# ever reaching this file -- tools/setup_tui/idtypes.py's `WorldName` (the TUI's Birth screen
# entry gate) and bootstrap/new-project.sh's `--profile tracker` `--name` check (its own inline
# comment cites this same pattern). If this regex ever changes, both of those homes' own copies
# need the same change -- there is no shared importable home across the Python/shell boundary.
_DEPLOYMENT_NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")

# The five keys a `[deployments.NAME]` table MUST carry -- named ONCE (ADR-0012 P1), not
# re-derived at each validation call site. See the module docstring's flagged choice for why
# `pgschema`/`pgkern` join the spec's own three-key example.
_REQUIRED_ENTRY_KEYS: frozenset[str] = frozenset({"pghost", "pgdatabase", "pguser", "pgschema", "pgkern"})

# The keys a `[deployments.NAME]` table MAY carry in addition to the required five -- named ONCE
# (ADR-0012 P1), same reasoning. `identity_enforcement` is the per-deployment override (see the
# module docstring's PER-DEPLOYMENT IDENTITY_ENFORCEMENT OVERRIDE section) -- absent means "no
# override, inherit the top-level default", never a third posture value.
_OPTIONAL_ENTRY_KEYS: frozenset[str] = frozenset({"identity_enforcement"})
_ALL_ENTRY_KEYS: frozenset[str] = _REQUIRED_ENTRY_KEYS | _OPTIONAL_ENTRY_KEYS

# The ONLY top-level keys this file recognizes, as of the SSE-events spec's `sse_poll_interval_secs`/
# `max_sse_clients` addition -- named ONCE (ADR-0012 P1), consulted by
# `load_multiplex_config`'s own unknown-top-level-key check below rather than an inline literal
# `{"deployments"}` set.
_TOP_LEVEL_KEYS: frozenset[str] = frozenset({
    "deployments", "log_level", "identity_enforcement",
    "sse_poll_interval_secs", "max_sse_clients",
})

# IDENTITY_ENFORCEMENT (design/FABLE-DISPATCH-MECHANICS-SPEC.md §3, ledger row 1471 sub-item 4c,
# "rung (a)"): the anonymous-write refusal's own posture, a two-member closed vocabulary --
# "grace" (accepts an anonymous authority-bearing write unchanged, byte-identical -- the
# DEFAULT, so the operator surface is never broken mid-migration) or "enforce" (refuses an
# anonymous authority-bearing write with a typed, teaching disposition). Named here, once
# (ADR-0012 P1), so `serving/boundary_service.py` imports the vocabulary rather than carrying a
# second copy that could drift -- the same relationship this module already has with
# `boundary_diagnostic_log.LEVELS`.
IDENTITY_ENFORCEMENT_POSTURES: frozenset[str] = frozenset({"grace", "enforce"})
DEFAULT_IDENTITY_ENFORCEMENT = "grace"


@dataclass(frozen=True)
class IdentityEnforcementPosture:
    """The identity_enforcement posture value -- CLAUDE.md/ledger row 26 ("no bare types: every
    value gets a named type with a single constructing home enforcing its contract"). Construct
    ONLY via `.parse()` below (never `IdentityEnforcementPosture(raw)` directly from outside this
    module) -- the ONE site, used identically for the top-level hub default and for a
    `[deployments.NAME]` override, so an invalid value at either location is refused with the
    SAME teach-text. `__post_init__` still guards direct construction (e.g. `.default()` below,
    or a test constructing one in-process) so no path can ever produce a value outside the closed
    vocabulary, matching `deployment_record.DeploymentRecord`'s own `__post_init__`-guards-every-
    construction-path idiom."""
    value: str

    def __post_init__(self) -> None:
        if self.value not in IDENTITY_ENFORCEMENT_POSTURES:
            raise ValueError(
                f"IdentityEnforcementPosture: {self.value!r} is not one of "
                f"{sorted(IDENTITY_ENFORCEMENT_POSTURES)}")

    @property
    def enforces(self) -> bool:
        """True iff this posture refuses an anonymous authority-bearing write."""
        return self.value == "enforce"

    @classmethod
    def default(cls) -> "IdentityEnforcementPosture":
        return cls(DEFAULT_IDENTITY_ENFORCEMENT)

    @classmethod
    def parse(cls, raw: object, *, where: str, path: Path) -> "IdentityEnforcementPosture":
        """Validate `raw` against the closed vocabulary, raising `MultiplexConfigError` naming
        BOTH valid values and BOTH key locations a posture can be set at (the top-level hub
        default, or a `[deployments.NAME]` override) -- so an operator who gets it wrong at
        either site sees the same teach-text and knows where else to look."""
        if not isinstance(raw, str) or raw not in IDENTITY_ENFORCEMENT_POSTURES:
            raise MultiplexConfigError(
                f"boundary-multiplex config at {path}: {where} = {raw!r} is not one of "
                f"{sorted(IDENTITY_ENFORCEMENT_POSTURES)} (design/"
                f"FABLE-DISPATCH-MECHANICS-SPEC.md §3 -- unknown values refuse loudly, before "
                f"the socket ever binds). identity_enforcement may be set at the TOP LEVEL (the "
                f"hub-wide default, applying to every deployment that does not override it; "
                f"omit the key entirely for the default, {DEFAULT_IDENTITY_ENFORCEMENT!r}) and/"
                f"or inside a [deployments.NAME] table (overriding the default for that "
                f"deployment only; omit the key entirely to inherit the top-level default) -- "
                f"both locations accept only {sorted(IDENTITY_ENFORCEMENT_POSTURES)}.")
        return cls(raw)

# SSE TUNABLES (design/FABLE-BOUNDARY-SSE-EVENTS-SPEC.md §1 items 1/4): defaults named ONCE
# (ADR-0012 P1) -- serving/boundary_service.py imports these rather than carrying a second
# literal copy, the same relationship this module already has with `IDENTITY_ENFORCEMENT_
# POSTURES`/`DEFAULT_IDENTITY_ENFORCEMENT` above.
DEFAULT_SSE_POLL_INTERVAL_SECS = 2.0
DEFAULT_MAX_SSE_CLIENTS = 16
# Sanity ceilings, not operational tuning advice -- a value outside these is almost certainly a
# typo (a poll interval of days, or a client cap in the millions), refused loudly at load time
# rather than silently accepted and only discovered as a surprise in production (ADR-0002).
_MAX_SSE_POLL_INTERVAL_SECS = 3600.0
_MAX_SSE_CLIENTS_CEILING = 100_000


class MultiplexConfigError(Exception):
    """The config file is absent, unreadable, unparseable as TOML, not a table, carries an
    unknown top-level key, is missing the `deployments` key, carries zero deployments, or one
    `[deployments.NAME]` entry is malformed (bad name, wrong shape, unknown/missing/empty
    key). Raised, never swallowed -- construction-time refusal, ADR-0002 rung 1: the anomaly
    is caught BEFORE the socket ever binds (spec §3, verbatim)."""


def load_multiplex_config(path: str | Path) -> dict[str, deployment_record.DeploymentRecord]:
    """Load and validate `boundary-multiplex.toml`'s WHOLE shape in one pass; returns a dict of
    deployment name -> `DeploymentRecord`. Never returns a partial config on any defect (every
    axis below raises `MultiplexConfigError` naming exactly what is wrong, before any entry's
    identifiers even reach `BoundaryConfig`'s own downstream check).

    Thin wrapper over `_load_and_validate` (ADR-0012 P1: ONE validation pass, one home) that
    discards the `log_level` half of the result -- kept byte-for-byte backward compatible for
    every EXISTING caller (this project's own fixture bank calls this exact name); a caller
    that also needs the resolved log level (`serving/boundary_service.py`'s own `main()`) calls
    `load_multiplex_config_with_log_level` instead, rather than this file growing a second,
    diverging validation path."""
    deployments, _log_level, _identity_enforcement, _poll, _max_clients, _by_dep = _load_and_validate(path)
    return deployments


def load_multiplex_config_with_log_level(
    path: str | Path,
) -> tuple[dict[str, deployment_record.DeploymentRecord], str]:
    """The diagnostic-logging spec's own entry point (design/
    FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md §2, "Config") -- SAME single validation pass as
    `load_multiplex_config` above (never a second, independent parse of the same file), also
    returning the resolved `log_level` (already validated against
    `boundary_diagnostic_log.LEVELS`, defaulted to `boundary_diagnostic_log.DEFAULT_LEVEL` when
    the TOML omits the key entirely). Kept byte-for-byte backward compatible (discards the
    dispatch-mechanics spec's `identity_enforcement` half, and the SSE spec's two tunables) for
    every EXISTING caller; a caller that needs more calls `load_multiplex_config_with_diagnostics`
    or `load_multiplex_config_with_sse` instead."""
    deployments, log_level, _identity_enforcement, _poll, _max_clients, _by_dep = _load_and_validate(path)
    return deployments, log_level


def load_multiplex_config_with_diagnostics(
    path: str | Path,
) -> tuple[dict[str, deployment_record.DeploymentRecord], str, str]:
    """design/FABLE-DISPATCH-MECHANICS-SPEC.md §3's own entry point -- SAME single validation
    pass as the two loaders above (never a second, independent parse of the same file), also
    returning the resolved `identity_enforcement` posture (already validated against
    `IDENTITY_ENFORCEMENT_POSTURES`, defaulted to `DEFAULT_IDENTITY_ENFORCEMENT` -- "grace" --
    when the TOML omits the key entirely). Kept byte-for-byte backward compatible (discards the
    SSE spec's two tunables) for every EXISTING caller; `serving/boundary_service.py`'s `main()`
    now calls `load_multiplex_config_with_sse` instead (superseding its prior call to this
    function), which also needs those."""
    deployments, log_level, identity_enforcement, _poll, _max_clients, _by_dep = _load_and_validate(path)
    return deployments, log_level, identity_enforcement


def load_multiplex_config_with_sse(
    path: str | Path,
) -> tuple[dict[str, deployment_record.DeploymentRecord], str, str, float, int]:
    """design/FABLE-BOUNDARY-SSE-EVENTS-SPEC.md's own entry point -- SAME single validation pass
    as the loaders above (never a second, independent parse of the same file), also returning the
    resolved `sse_poll_interval_secs`/`max_sse_clients` (already validated, defaulted to
    `DEFAULT_SSE_POLL_INTERVAL_SECS`/`DEFAULT_MAX_SSE_CLIENTS` when the TOML omits either key
    entirely). Kept byte-for-byte backward compatible (discards the per-deployment
    identity_enforcement override dict) for every EXISTING caller; `serving/boundary_service.py`'s
    `main()` now calls `load_multiplex_config_with_deployment_identity` instead (superseding its
    prior call to this function), which also needs that."""
    deployments, log_level, identity_enforcement, poll, max_clients, _by_dep = _load_and_validate(path)
    return deployments, log_level, identity_enforcement, poll, max_clients


def load_multiplex_config_with_deployment_identity(
    path: str | Path,
) -> tuple[dict[str, deployment_record.DeploymentRecord], str, str, float, int,
           dict[str, "IdentityEnforcementPosture"]]:
    """Work item identity-enforcement-split-flip (ledger row 619's adjudication) -- the RICHEST
    entry point, SAME single validation pass as every loader above (never a second, independent
    parse of the same file), also returning the fully-RESOLVED per-deployment
    `identity_enforcement` posture: a `dict[str, IdentityEnforcementPosture]` keyed by every
    deployment name in `deployments`, with the top-level default already folded in for any
    deployment that carries no `[deployments.NAME].identity_enforcement` override of its own.
    `serving/boundary_service.py`'s `main()` calls this one now (superseding its prior call to
    `load_multiplex_config_with_sse`) so the "override or inherit the default" merge happens in
    exactly ONE place (ADR-0012 P1), never re-derived at the request-handling layer."""
    return _load_and_validate(path)


def _load_and_validate(
    path: str | Path,
) -> tuple[dict[str, deployment_record.DeploymentRecord], str, str, float, int,
           dict[str, "IdentityEnforcementPosture"]]:
    """The ONE home (ADR-0012 P1) every public loader above routes through -- every validation
    axis (unknown top-level key, missing/unknown/malformed `deployments` entry, an
    unrecognized `log_level`/`identity_enforcement`/`sse_poll_interval_secs`/`max_sse_clients`
    value, at the top level OR inside a `[deployments.NAME]` table) runs in this SAME whole-file
    pass, before any public function returns anything, matching spec §3's "the WHOLE file
    validates before the socket binds" applied to each new key exactly as it already applies to
    every existing one. The sixth return element is the fully-resolved, per-deployment
    `identity_enforcement` posture -- one `IdentityEnforcementPosture` per deployment name, the
    top-level default already folded in for any deployment with no override of its own (row 619's
    adjudication)."""
    p = Path(path)
    if not p.is_file():
        raise MultiplexConfigError(
            f"boundary-multiplex config not found at {p} -- a multiplexed service refuses to "
            f"start without one explicit, operator-authored config file (spec §3: 'no "
            f"search-path magic, no defaults file'). Pass --config <path>.")
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        raise MultiplexConfigError(
            f"boundary-multiplex config at {p} could not be read ({e.__class__.__name__}: {e})") from e
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise MultiplexConfigError(f"boundary-multiplex config at {p} is not valid TOML ({e})") from e

    unknown_top = sorted(set(raw) - _TOP_LEVEL_KEYS)
    if unknown_top:
        raise MultiplexConfigError(
            f"boundary-multiplex config at {p} has unknown top-level key(s) {unknown_top} -- "
            f"the only recognized top-level keys are {sorted(_TOP_LEVEL_KEYS)} (spec §3, "
            f"extended by design/FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md §2's 'log_level'). "
            f"Refused before the socket ever binds.")

    log_level = raw.get("log_level", boundary_diagnostic_log.DEFAULT_LEVEL)
    if not isinstance(log_level, str) or log_level not in boundary_diagnostic_log.LEVELS:
        raise MultiplexConfigError(
            f"boundary-multiplex config at {p}: 'log_level' = {log_level!r} is not one of "
            f"{sorted(boundary_diagnostic_log.LEVELS)} (design/"
            f"FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md §2 -- unknown values refuse loudly, "
            f"before the socket ever binds; omit the key entirely for the default, "
            f"{boundary_diagnostic_log.DEFAULT_LEVEL!r}).")

    default_identity_enforcement = IdentityEnforcementPosture.parse(
        raw.get("identity_enforcement", DEFAULT_IDENTITY_ENFORCEMENT),
        where="'identity_enforcement' (top-level)", path=p)
    identity_enforcement = default_identity_enforcement.value  # kept as a bare str ONLY for the
    # four existing public loaders below, which return the hub-wide default as a plain string
    # (byte-for-byte compatible with every caller that existed before this build); the NEW richest
    # loader, `load_multiplex_config_with_deployment_identity`, returns the typed per-deployment
    # dict instead.

    # SSE TUNABLES (design/FABLE-BOUNDARY-SSE-EVENTS-SPEC.md §1 items 1/4): same whole-file
    # validation pass, same before-the-socket-binds discipline as log_level/identity_enforcement
    # immediately above. `bool` is excluded explicitly (Python's `bool` is an `int` subclass --
    # `True`/`False` would otherwise silently pass an `isinstance(..., int)` check as 1/0).
    sse_poll_interval_secs = raw.get("sse_poll_interval_secs", DEFAULT_SSE_POLL_INTERVAL_SECS)
    if (isinstance(sse_poll_interval_secs, bool)
            or not isinstance(sse_poll_interval_secs, (int, float))
            or not (0 < sse_poll_interval_secs <= _MAX_SSE_POLL_INTERVAL_SECS)):
        raise MultiplexConfigError(
            f"boundary-multiplex config at {p}: 'sse_poll_interval_secs' = "
            f"{sse_poll_interval_secs!r} is not a number in (0, {_MAX_SSE_POLL_INTERVAL_SECS}] "
            f"(design/FABLE-BOUNDARY-SSE-EVENTS-SPEC.md §1 item 1 -- unknown/out-of-domain "
            f"values refuse loudly, before the socket ever binds; omit the key entirely for "
            f"the default, {DEFAULT_SSE_POLL_INTERVAL_SECS!r}).")
    sse_poll_interval_secs = float(sse_poll_interval_secs)

    max_sse_clients = raw.get("max_sse_clients", DEFAULT_MAX_SSE_CLIENTS)
    if (isinstance(max_sse_clients, bool)
            or not isinstance(max_sse_clients, int)
            or not (1 <= max_sse_clients <= _MAX_SSE_CLIENTS_CEILING)):
        raise MultiplexConfigError(
            f"boundary-multiplex config at {p}: 'max_sse_clients' = {max_sse_clients!r} is not "
            f"an integer in [1, {_MAX_SSE_CLIENTS_CEILING}] (design/"
            f"FABLE-BOUNDARY-SSE-EVENTS-SPEC.md §1 item 4 -- unknown/out-of-domain values "
            f"refuse loudly, before the socket ever binds; omit the key entirely for the "
            f"default, {DEFAULT_MAX_SSE_CLIENTS!r}).")

    if "deployments" not in raw:
        raise MultiplexConfigError(
            f"boundary-multiplex config at {p} is missing the required top-level key "
            f"'deployments' -- at least one [deployments.NAME] table is required (spec §3).")
    deployments_raw = raw["deployments"]
    if not isinstance(deployments_raw, dict):
        raise MultiplexConfigError(
            f"boundary-multiplex config at {p}: 'deployments' must be a TOML table of "
            f"[deployments.NAME] entries, got {type(deployments_raw).__name__}")
    if not deployments_raw:
        raise MultiplexConfigError(
            f"boundary-multiplex config at {p} configures ZERO deployments -- refused (spec "
            f"§3: 'zero deployments refuses'). A single-deployment config is the degenerate, "
            f"expected common case, but it still needs exactly one [deployments.NAME] table.")

    result: dict[str, deployment_record.DeploymentRecord] = {}
    identity_enforcement_by_deployment: dict[str, IdentityEnforcementPosture] = {}
    for name, entry in deployments_raw.items():
        if not _DEPLOYMENT_NAME_RE.match(name):
            raise MultiplexConfigError(
                f"boundary-multiplex config at {p}: deployment name {name!r} does not match "
                f"{_DEPLOYMENT_NAME_RE.pattern} (spec §2 -- deployment names are "
                f"[a-z0-9-]{{1,64}})")
        if not isinstance(entry, dict):
            raise MultiplexConfigError(
                f"boundary-multiplex config at {p}: [deployments.{name}] must be a table, "
                f"got {type(entry).__name__}")
        unknown = sorted(set(entry) - _ALL_ENTRY_KEYS)
        if unknown:
            raise MultiplexConfigError(
                f"boundary-multiplex config at {p}: [deployments.{name}] has unknown key(s) "
                f"{unknown} -- only {sorted(_ALL_ENTRY_KEYS)} are recognized (spec §3: "
                f"'unknown keys anywhere refuse startup by name').")
        missing = sorted(_REQUIRED_ENTRY_KEYS - set(entry))
        if missing:
            raise MultiplexConfigError(
                f"boundary-multiplex config at {p}: [deployments.{name}] is missing required "
                f"key(s) {missing} (spec §3: 'a missing required key refuses by name').")
        bad = sorted(k for k in _REQUIRED_ENTRY_KEYS
                     if not isinstance(entry[k], str) or not entry[k])
        if bad:
            raise MultiplexConfigError(
                f"boundary-multiplex config at {p}: [deployments.{name}] has non-string or "
                f"empty value(s) for key(s) {bad} -- every value must be a non-empty string.")
        result[name] = deployment_record.DeploymentRecord(
            db=entry["pgdatabase"], host=entry["pghost"], schema=entry["pgschema"],
            kern=entry["pgkern"], role=entry["pguser"], name=name)
        # PER-DEPLOYMENT IDENTITY_ENFORCEMENT OVERRIDE (row 619's adjudication): present ->
        # validate through the SAME constructing home as the top-level key, naming this exact
        # [deployments.NAME] location on refusal; absent -> inherit the top-level default
        # resolved above (byte-identical to today when no [deployments.NAME] table ever sets
        # this key, the regression leg's own requirement).
        if "identity_enforcement" in entry:
            identity_enforcement_by_deployment[name] = IdentityEnforcementPosture.parse(
                entry["identity_enforcement"],
                where=f"[deployments.{name}].identity_enforcement", path=p)
        else:
            identity_enforcement_by_deployment[name] = default_identity_enforcement
    return (result, log_level, identity_enforcement, sse_poll_interval_secs, max_sse_clients,
            identity_enforcement_by_deployment)
