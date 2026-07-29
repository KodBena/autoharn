#!/usr/bin/env python3
"""dispatch_scope -- dispatch-time scope minting's own typed-value SSOT (design/
FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §1b/§3/§5 item 4, ledger rows 639/815),
factored out of tools/dispatch_mechanics.py (ADR-0007's 400-line ceiling -- a brand-new file is
refused outright over it, not ratcheted; this split keeps dispatch_mechanics.py under the
ceiling by giving the scope-value machinery its own single-purpose home, ADR-0012 P1's "split so
each file's own footprint is honest" reflex, not code golf).

Mirrors bootstrap/templates/led.tmpl's own per-write-surface dataclass idiom (frozen,
`__post_init__` enforces the contract, a `.fields()`/`as_json_obj()` method emits the wire
shape) one hop earlier than kernel/lineage/s70-scope-binding.sql's own CHECKs
(`scope_exclusions_shape_ok`, `scope_disclosure_mode_vocabulary`) -- defense in depth, never
looser or stricter than those CHECKs, which still run and still win if this mirror ever drifts
(the kernel is always the true authority; this SSOT exists so a caller cannot even CONSTRUCT an
out-of-vocabulary value, the same guarantee `RelationPayload`/`KeyBindingPayload` already give
their own callers -- the no-bare-types rule, ledger row 1105).

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import is top-of-file.
"""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent  # repo root (tools/ is one level under it)
sys.path.insert(0, str(_HERE / "serving"))
import boundary_cli_client as bcc  # noqa: E402

SCOPE_EXCLUSION_FAMILIES = ("kind-class", "thread", "work-item-lineage", "rows")
SCOPE_DISCLOSURE_MODES = ("marked", "hash_stub", "full")
SCOPE_DISCLOSURE_MODE_DEFAULT = "marked"


@dataclasses.dataclass(frozen=True)
class ScopeExclusion:
    """One `{family, value}` member of a `principal_scope_bound` row's `scope_exclusions` array
    (kernel/lineage/s70-scope-binding.sql's `scope_exclusions_shape_ok`). Contract, enforced
    HERE: `family` is one of the kernel's own closed four-member vocabulary
    (`SCOPE_EXCLUSION_FAMILIES`); `value` is a non-empty string for `kind-class`/`thread`/
    `work-item-lineage` (a kind name, missive thread id, or work-item slug -- the ledger's OWN
    vocabulary, spec §4 denomination check) or a non-empty tuple of non-negative row ids for
    `rows` (an explicit, enumerated SET, never an offset/threshold computed over them -- the
    SAME denomination check, its rarer explicit-id escape hatch)."""
    family: str
    value: str | tuple[int, ...]

    def __post_init__(self) -> None:
        if self.family not in SCOPE_EXCLUSION_FAMILIES:
            raise ValueError(
                f"'{self.family}' is not a scope-exclusion family (closed vocabulary: "
                f"{', '.join(SCOPE_EXCLUSION_FAMILIES)} -- kernel/lineage/"
                f"s70-scope-binding.sql's scope_exclusions_shape_ok)")
        if self.family == "rows":
            if not isinstance(self.value, tuple) or not self.value:
                raise ValueError(
                    "the 'rows' exclusion family needs a non-empty, comma-separated list of "
                    "ledger row ids -- an explicit enumerated SET, never an offset/threshold "
                    "(design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §4)")
            if any((not isinstance(v, int)) or isinstance(v, bool) or v < 0 for v in self.value):
                raise ValueError("the 'rows' exclusion family's ids must all be non-negative integers")
        else:
            if not isinstance(self.value, str) or not self.value.strip():
                raise ValueError(
                    f"the '{self.family}' exclusion family needs a non-empty string value (a "
                    f"kind name, missive thread id, or work-item slug -- the ledger's own "
                    f"vocabulary, design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §4)")

    def as_json_obj(self) -> dict:
        if self.family == "rows":
            return {"family": self.family, "value": list(self.value)}
        return {"family": self.family, "value": self.value}


@dataclasses.dataclass(frozen=True)
class ScopeBindingSpec:
    """A dispatch-time `--scope-*` request's typed shape (design/FABLE-ACCESS-CONTROL-AND-
    INFORMATION-FLOW-SPEC.md §5 item 4). The three `principal_scope_bound` payload columns
    kernel/lineage/s70-scope-binding.sql Element 2 licenses, each optional even when this spec
    itself is present (that Element's own header: "additive, nullable" -- a binding naming only
    a disclosure mode, with no surfaces/exclusions, is a legal degenerate row) -- constructed
    ONLY when `cmd_mint` sees at least one `--scope-*` flag; no flag at all means `mint` never
    builds one, leaving the pre-existing no-scope dispatch behavior byte-identical."""
    surfaces: tuple[str, ...] = ()
    exclusions: tuple[ScopeExclusion, ...] = ()
    disclosure_mode: str = SCOPE_DISCLOSURE_MODE_DEFAULT

    def __post_init__(self) -> None:
        if self.disclosure_mode not in SCOPE_DISCLOSURE_MODES:
            raise ValueError(
                f"'{self.disclosure_mode}' is not a disclosure mode (closed vocabulary: "
                f"{', '.join(SCOPE_DISCLOSURE_MODES)} -- kernel/lineage/"
                f"s70-scope-binding.sql's scope_disclosure_mode_vocabulary)")
        for s in self.surfaces:
            if not isinstance(s, str) or not s.strip():
                raise ValueError("a --scope-surface value must be a non-empty string (a "
                                  "registry view/route name)")

    def fields(self) -> dict:
        out: dict = {"scope_disclosure_mode": self.disclosure_mode}
        if self.surfaces:
            out["scope_surfaces"] = list(self.surfaces)
        if self.exclusions:
            out["scope_exclusions"] = [e.as_json_obj() for e in self.exclusions]
        return out


def parse_scope_rows(raw: str) -> tuple[int, ...]:
    """`--scope-exclude rows:<id>[,<id>...]`'s own value parse -- a comma-separated list of
    non-negative integers, refused (ValueError, caught by the caller) on anything else, before
    `ScopeExclusion.__post_init__` even runs (fail loud at the earliest possible point, matching
    `cmd_mint`'s own existing `--depth`/commission-id integer parses)."""
    parts = [p for p in raw.split(",") if p]
    if not parts:
        raise ValueError("--scope-exclude rows:... needs at least one row id")
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        raise ValueError(f"--scope-exclude rows:{raw!r} is not a comma-separated list of integers")


def extract_scope_flags(argv: list[str]) -> tuple[list[str], ScopeBindingSpec | None]:
    """Pulls every `--scope-surface`/`--scope-exclude`/`--scope-disclosure-mode` flag out of
    `argv`, returning `(residual, spec)`: `residual` is `argv` with those flags/values removed
    (every other flag/positional untouched, in order) so a caller's OWN flag loop (e.g.
    `dispatch_mechanics.cmd_mint`) never has to know these flags exist; `spec` is the constructed
    `ScopeBindingSpec`, or `None` if no `--scope-*` flag was present at all (the fail-safe-
    additive contract: an unarmed `mint` builds no `principal_scope_bound` row, byte-identical to
    before this delta). Raises `ValueError` (caught by the caller, which knows its own `PROG`
    prefix for the teach-text) on any malformed flag/value -- this module stays the ONE
    constructing site regardless of which CLI surface calls it (no-bare-types SSOT, row 1105)."""
    residual: list[str] = []
    surfaces: list[str] = []
    exclusions: list[ScopeExclusion] = []
    disclosure_mode = SCOPE_DISCLOSURE_MODE_DEFAULT
    requested = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--scope-surface":
            if i + 1 >= len(argv):
                raise ValueError("--scope-surface requires a value")
            surfaces.append(argv[i + 1])
            requested = True
            i += 2
        elif a == "--scope-exclude":
            if i + 1 >= len(argv):
                raise ValueError(
                    f"--scope-exclude requires a <family>:<value> argument (closed family "
                    f"vocabulary: {', '.join(SCOPE_EXCLUSION_FAMILIES)})")
            raw = argv[i + 1]
            family, sep, value_raw = raw.partition(":")
            if not sep:
                raise ValueError(
                    f"--scope-exclude value {raw!r} is not '<family>:<value>' shaped (closed "
                    f"family vocabulary: {', '.join(SCOPE_EXCLUSION_FAMILIES)})")
            value: str | tuple[int, ...] = parse_scope_rows(value_raw) if family == "rows" else value_raw
            exclusions.append(ScopeExclusion(family, value))
            requested = True
            i += 2
        elif a == "--scope-disclosure-mode":
            if i + 1 >= len(argv):
                raise ValueError("--scope-disclosure-mode requires a value")
            disclosure_mode = argv[i + 1]
            requested = True
            i += 2
        else:
            residual.append(a)
            i += 1
    if not requested:
        return residual, None
    return residual, ScopeBindingSpec(
        surfaces=tuple(surfaces), exclusions=tuple(exclusions), disclosure_mode=disclosure_mode)


def bind_scope(cfg: bcc.ServedConfig, prog: str, dispatcher_id: int, delegate_id: int,
               name: str, scope_spec: ScopeBindingSpec) -> int:
    """Step 3 of `dispatch mint` (OPTIONAL -- called only when `extract_scope_flags` returned a
    non-`None` spec): binds a `principal_scope_bound` row to the freshly minted delegate, same
    `POST /write/ledger` surface, same actor, as `cmd_mint`'s own dispatched-by-edge write.
    Returns the process exit code (0 accepted, matching `boundary_cli_client.write_and_report`'s
    own convention) -- a caller seeing non-zero must NOT emit the delegate's stamp material (the
    delegate would hold the OPEN scope, not the restricted one the operator asked for)."""
    scope_payload: dict = {
        "kind": "principal_scope_bound",
        "statement": f"scope bound for principal '{name}' (id {delegate_id}) -- "
                     f"surfaces={list(scope_spec.surfaces) or 'none'}, "
                     f"exclusions={len(scope_spec.exclusions)}, "
                     f"disclosure_mode={scope_spec.disclosure_mode}",
        "principal_subject": delegate_id,
        "principal_binding_active": True,
        "actor": dispatcher_id,
        **scope_spec.fields(),
    }
    rc = bcc.write_and_report(cfg.base, "ledger", scope_payload)
    if rc != 0:
        print(f"{prog} mint: the delegate principal '{name}' (id {delegate_id}) IS now "
              f"registered and dispatched, but the REQUESTED scope binding was REFUSED (above) "
              f"-- it currently holds the OPEN scope (every surface, no exclusions), NOT the "
              f"restricted scope you asked for. Do not emit its stamp material to a child "
              f"session until this is resolved (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-"
              f"FLOW-SPEC.md §1b's fail-safe default cuts the OTHER way from what you intended "
              f"here).", file=sys.stderr)
    return rc
