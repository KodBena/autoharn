#!/usr/bin/env python3
"""tools/setup_tui/config_file.py -- load/validate/render a wizard config file
(design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md, ledger row 1944). This is the P10 LOGIC half; the
closed schema table it validates against lives in
`tools/setup_tui/content/config_file_data.py` (data, not code -- ADR-0012 P10).

THREE JOBS, each spec-mandated:
  1. `load_config_file(path)` -- parse TOML (stdlib `tomllib`, read-only; there is no stdlib
     TOML writer, so `render_toml` below is a small closed-format serializer for the ONE shape
     this module ever writes: flat bool/str/list_str/list_table values under named sections).
  2. `validate(doc, *, require_complete)` -- spec §2's "complete-or-refuse" / "unknown keys
     refuse loudly" rules, ALL AT ONCE (every missing/unknown key named in one refusal, never a
     first-one-wins early exit -- spec §2's own words: "naming every missing key at once").
  3. `render_toml(resolved)` -- the self-application write (spec §4): the SAME closed shape a
     config file is loaded from, rendered back out, commented, from a plain `dict[str, object]`
     of dotted keys -> values (never a second, hand-rolled format).

Every consumer of a *raw* loaded/validated `ConfigDoc` goes through `tools/setup_tui/
config_seam.py` (the SCREEN-SEAM half: turning validated config values into --from-config's
synthesized scripted answers, or --initial-config's prior-answers seed) -- this module never
touches `Ui`/screens/prompts, only the file <-> dict boundary (ADR-0012 P1: one home for the
parsing, a different one for the seam that seam-wires it into the flow).

Stdlib only (`tomllib`), top-of-file imports (the lazy-import gate applies)."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from tools.setup_tui.content.config_file_data import HEADER_KEYS, SCHEMA

CONFIG_FORMAT = 1


class ConfigError(RuntimeError):
    """A config file failed to load or validate -- the message IS the refusal text (spec §2:
    "REFUSES up front, naming every missing key at once" / "Unknown keys likewise refuse
    loudly"), never a partial/best-effort application."""


@dataclass
class ConfigDoc:
    """A loaded, but not yet SCHEMA-validated, config file -- `values` is dotted-key -> raw
    TOML value, `header` is the three top-level provenance fields (spec §1)."""
    path: str
    header: dict[str, object] = field(default_factory=dict)
    values: dict[str, object] = field(default_factory=dict)


def _flatten(raw: dict) -> tuple[dict[str, object], dict[str, object]]:
    """Splits a parsed TOML document into (header, dotted-section-values) -- `raw`'s own
    top-level scalar keys are the header (spec §1: "config_format = 1, a produced_by note, and
    the source"); every OTHER top-level key must be a `[section]` table, flattened to
    `"section.key"` -- a bare top-level key that is not a header field and not a table (e.g. a
    stray `world = "..."` -- spec §1's excluded-by-type example) is surfaced as an unknown key
    by `validate` below exactly like any other unrecognized dotted path, never specially
    swallowed."""
    header: dict[str, object] = {}
    flat: dict[str, object] = {}
    for key, val in raw.items():
        if key in HEADER_KEYS:
            header[key] = val
            continue
        if isinstance(val, dict):
            for subkey, subval in val.items():
                flat[f"{key}.{subkey}"] = subval
        else:
            # A stray top-level scalar that is not a header field -- flattened under a
            # section-less dotted path so it still shows up, named, in the unknown-key refusal
            # rather than being silently dropped.
            flat[key] = val
    return header, flat


def load_config_file(path: str | Path) -> ConfigDoc:
    """Parses `path` as TOML -- raises `ConfigError` (never a bare `tomllib` exception) on a
    missing file or a syntax error, both named with the path (ADR-0002 rule 1: fail loudly, the
    caller sees exactly what and where)."""
    p = Path(path)
    if not p.is_file():
        raise ConfigError(f"setup_tui: config file not found: {p}")
    try:
        raw = tomllib.loads(p.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"setup_tui: config file '{p}' is not valid TOML: {exc}") from exc
    header, flat = _flatten(raw)
    return ConfigDoc(path=str(p), header=header, values=flat)


# REQUIRED_FOR_FROM_CONFIG: the keys a --from-config run needs to reach a deterministic,
# zero-prompt commit with NO section silently skipped by omission (spec §2: "a config missing a
# key the flow needs REFUSES up front"). Every "*.run"/"*.configure" gate is required (the
# config must say, explicitly, whether each section is even walked -- an absent gate is not
# read as "skip", it is a missing decision); the scalar fields a section needs ONLY WHEN THAT
# SECTION IS ON are checked contextually by `validate` below, not listed here statically (a
# `substrate.db` requirement that only applies when `substrate.run = true` cannot be a flat
# always-required set without also wrongly demanding it when substrate is off).
REQUIRED_GATES = (
    "substrate.run", "rehearsal.run", "birth.run", "principals_authority.run",
    "signed_genesis.run", "boundary.configure", "observability.run", "hydration.run",
)


def validate(doc: ConfigDoc, *, require_complete: bool) -> None:
    """Spec §2/§3's two closed-form refusals, both ALWAYS enforced (loaded config text is
    never trusted further than this), `require_complete` adds the --from-config-only
    completeness checks (missing gates, missing header). Raises one `ConfigError` naming EVERY
    problem found, never the first one alone."""
    problems: list[str] = []

    unknown = sorted(k for k in doc.values if k not in SCHEMA)
    if unknown:
        problems.append(
            "unknown key(s) (not in the closed schema -- a typo, or a value that does not "
            "belong in a config file at all, e.g. 'world'/'dest' are CLI parameters, never "
            "config content): " + ", ".join(unknown)
        )

    if require_complete:
        missing_header = sorted(HEADER_KEYS - set(doc.header))
        if missing_header:
            problems.append("missing header field(s): " + ", ".join(missing_header))
        missing_gates = sorted(g for g in REQUIRED_GATES if g not in doc.values)
        if missing_gates:
            problems.append(
                "missing required decision key(s) (every section's own run/configure gate must "
                "be explicit for a --from-config run -- never defaulted): " + ", ".join(missing_gates)
            )
        # Contextual completeness: a section that is ON needs its own scalar fields present.
        problems.extend(_missing_contextual(doc))

    if problems:
        raise ConfigError(
            f"setup_tui: config file '{doc.path}' REFUSED -- " + "; ".join(problems)
        )


def _missing_contextual(doc: ConfigDoc) -> list[str]:
    v = doc.values
    out: list[str] = []
    if v.get("substrate.run") is True:
        need = ["substrate.path", "substrate.host", "substrate.db"]
        if v.get("substrate.path") == "dedicated":
            need += ["substrate.role", "substrate.subnets"]
        missing = [k for k in need if k not in v]
        if missing:
            out.append(f"substrate is on but missing: {', '.join(missing)}")
    if v.get("signed_genesis.run") is True and "signed_genesis.commission_statement" not in v:
        out.append("signed_genesis is on but missing: signed_genesis.commission_statement")
    return out


def get(doc: ConfigDoc, key: str, default: object = None) -> object:
    """Typed-enough accessor every consumer uses instead of `doc.values.get` directly (ADR-0012
    P1) -- returns `default` for an absent key (legal for --initial-config's partial configs;
    --from-config's own completeness is already enforced by `validate` before this is ever
    called for a required key)."""
    return doc.values.get(key, default)


# --------------------------------------------------------------------------------------------
# Self-application render (spec §4): the ONE writer for the shape this module reads.
# --------------------------------------------------------------------------------------------

def _render_value(val: object) -> str:
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, str):
        return '"' + val.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(val, list):
        if val and isinstance(val[0], dict):
            raise TypeError("list_table rendering goes through _render_table_array, not this")
        return "[" + ", ".join(_render_value(v) for v in val) + "]"
    raise TypeError(f"config_file.render_toml: unrenderable value type {type(val).__name__}")


def _render_table_array(name: str, rows: list[dict]) -> str:
    """TOML array-of-tables (`[[name]]`) rendering -- one block per row, each field a plain
    `key = value` line under it (the closed shape every row in `principals_authority.register`/
    `.competences`/`.relations` uses -- spec §1's "keyed decisions" applied to a repeated
    group)."""
    return "\n\n".join(
        "[[" + name + "]]\n" + "\n".join(f"{k} = {_render_value(v)}" for k, v in row.items())
        for row in rows
    )


def render_toml(resolved: dict[str, object], *, produced_by: str, source: str) -> str:
    """Renders `resolved` (dotted-key -> value, the SAME shape `ConfigDoc.values` holds) back
    out as commented TOML -- spec §4's self-save, and the same format `load_config_file`/
    `validate` read. Every key is traced to `SCHEMA` (an unknown key here is a caller defect,
    not a config-file-author typo, so this raises rather than silently emitting it)."""
    sections: dict[str, list[tuple[str, object]]] = {}
    for dotted, val in resolved.items():
        if dotted not in SCHEMA:
            raise KeyError(f"config_file.render_toml: {dotted!r} is not in SCHEMA -- caller bug")
        section, _, key = dotted.partition(".")
        sections.setdefault(section, []).append((key, val))

    lines = [
        f"config_format = {CONFIG_FORMAT}",
        f'produced_by = "{produced_by}"',
        f'source = "{source}"',
        "",
    ]
    for section, pairs in sections.items():
        scalars = [(k, v) for k, v in pairs if not (isinstance(v, list) and v and isinstance(v[0], dict))]
        tables = [(k, v) for k, v in pairs if isinstance(v, list) and v and isinstance(v[0], dict)]
        if scalars:
            lines.append(f"[{section}]")
            for k, v in scalars:
                lines.append(f"{k} = {_render_value(v)}")
            lines.append("")
        for k, rows in tables:
            lines.append(_render_table_array(f"{section}.{k}", rows))
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
