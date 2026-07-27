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

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import is top-of-file.
"""
from __future__ import annotations

import re
import sys
import tomllib
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

# The five keys a `[deployments.NAME]` table may carry -- named ONCE (ADR-0012 P1), not
# re-derived at each validation call site. See the module docstring's flagged choice for why
# `pgschema`/`pgkern` join the spec's own three-key example.
_REQUIRED_ENTRY_KEYS: frozenset[str] = frozenset({"pghost", "pgdatabase", "pguser", "pgschema", "pgkern"})

# The ONLY two top-level keys this file recognizes, as of the diagnostic-logging spec's
# `log_level` addition -- named ONCE (ADR-0012 P1), consulted by `load_multiplex_config`'s own
# unknown-top-level-key check below rather than an inline literal `{"deployments"}` set.
_TOP_LEVEL_KEYS: frozenset[str] = frozenset({"deployments", "log_level"})


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
    deployments, _log_level = _load_and_validate(path)
    return deployments


def load_multiplex_config_with_log_level(
    path: str | Path,
) -> tuple[dict[str, deployment_record.DeploymentRecord], str]:
    """The diagnostic-logging spec's own entry point (design/
    FABLE-SERVING-DIAGNOSTIC-LOGGING-SPEC.md §2, "Config") -- SAME single validation pass as
    `load_multiplex_config` above (never a second, independent parse of the same file), also
    returning the resolved `log_level` (already validated against
    `boundary_diagnostic_log.LEVELS`, defaulted to `boundary_diagnostic_log.DEFAULT_LEVEL` when
    the TOML omits the key entirely)."""
    return _load_and_validate(path)


def _load_and_validate(
    path: str | Path,
) -> tuple[dict[str, deployment_record.DeploymentRecord], str]:
    """The ONE home (ADR-0012 P1) both public loaders above route through -- every validation
    axis (unknown top-level key, missing/unknown/malformed `deployments` entry, an
    unrecognized `log_level` value) runs in this SAME whole-file pass, before either public
    function returns anything, matching spec §3's "the WHOLE file validates before the socket
    binds" applied to the new key exactly as it already applies to every existing one."""
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
        unknown = sorted(set(entry) - _REQUIRED_ENTRY_KEYS)
        if unknown:
            raise MultiplexConfigError(
                f"boundary-multiplex config at {p}: [deployments.{name}] has unknown key(s) "
                f"{unknown} -- only {sorted(_REQUIRED_ENTRY_KEYS)} are recognized (spec §3: "
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
    return result, log_level
