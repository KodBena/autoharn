#!/usr/bin/env python3
"""dispatch_principal.py -- the mechanical half of the dispatch-principal-wiring convention
(ledger row 1356 claim). Commission: "Wire LED_ACTOR registered principals into every agent
dispatch preamble so builder identity is kernel-visible and segregation-of-duties checks run on
real principals, not the shared default author."

INVESTIGATION FINDING THIS TOOL BUILDS ON (see this fix round's ledger writeup for the full
evidence trail): the CLI/kernel layer ALREADY supports per-invocation principal attribution in
full -- `bootstrap/templates/led.tmpl`'s `_resolve_actor()` reads the `LED_ACTOR` env var,
resolves it against `GET /standing/principals` (the s41 registry), and REFUSES loudly (teaching
`./led register-principal <name> <class>`) on an unregistered name -- never a silent fallback to
the shared default ("declared-default") principal. `kernel/lineage/s40-principal-identity-
events.sql`'s `set_actor()` trigger marks every such write `principal_actor_resolution =
'explicit'`, visible in `led show`. No kernel/lineage or serving-layer change is needed or
licensed here.

THE ACTUAL GAP: nothing generates the `export LED_ACTOR=<name>` line an orchestrator's dispatch
preamble needs, and nothing checks BEFORE dispatch that the name it is about to hand a builder is
actually registered -- an orchestrator that hand-types a typo'd or never-registered name only
discovers the refusal after the builder has already spent a turn on it. This tool closes that
gap, CLI-side, the same shape `tools/role_charter.py` already established for a sibling
convention (charter registration): shells out to `./led` (or `--led PATH`), no raw SQL anywhere,
LED_ACTOR honored by ordinary subprocess env inheritance (registering a NEW principal is a real
ledger write and stays the orchestrator's own deliberate `./led register-principal` act -- this
tool never performs it on the caller's behalf).

CONVENTION THIS TOOL ASSUMES, NOT ENFORCES: a dispatched builder gets its OWN registered
principal (e.g. `builder-<work-item-slug>`, class `subagent`) distinct from the shared `author`
default -- naming is the orchestrator's call, this tool takes the name as an argument rather than
inventing a scheme, exactly like `role_charter.py` takes a caller-supplied `<role>` rather than
deriving one.

Usage:
    python3 tools/dispatch_principal.py preamble <name> [--led PATH] [--scan-limit N]
    python3 tools/dispatch_principal.py check <name>    [--led PATH] [--scan-limit N]

`preamble <name>`: if `<name>` is a registered, non-suspended-looking principal (see "Honest
limits" below), prints the ready-to-paste `export LED_ACTOR=<name>` line for the dispatch
preamble/brief and exits 0. If `<name>` is NOT registered, prints nothing on stdout, REFUSES on
stderr, and teaches the exact `./led register-principal <name> subagent --purpose "..."` command
to run first -- exit 1. This mirrors (and is a thin preflight in front of) `led`'s own
`_resolve_actor` refusal shape, so a caller who skips this check and dispatches anyway hits the
IDENTICAL refusal at write time, never a laxer or stricter one (defense in depth, not a second
authority).

`check <name>`: same registration test, machine-readable (`REGISTERED`/`NOT-REGISTERED` on
stdout), exit 0/1 -- for a caller that wants the fact without the formatted preamble line (e.g.
a batch pre-flight over several builder names before a wave of dispatches).

Honest limits: this tool tests REGISTRATION only (a `principal_registered` event exists for
`<name>`), the exact same test `led`'s own `_resolve_actor` performs -- it does NOT check
suspended/revoked standing (that is a live kernel fact `led`'s `set_actor` trigger enforces at
write time regardless of what this preflight says; a name that was registered and later
suspended still passes THIS check and then correctly refuses at the real write -- this tool never
duplicates that live-standing computation, per ADR-0012 P1, one home for that fact and it is the
kernel's).

COMPOSES-WITH, NAMED NOT BUILT: the parked `obligation-actor-type-system` item (design/
FABLE-OBLIGATION-DEPENDENT-TYPING-SPEC.md sec-3, "the typed-actor question... a later amendment
to the node predicate") is the natural next step ONCE dispatched builders carry distinct
registered principals: a future kernel delta could type WHICH principal/class may discharge
WHICH obligation. This tool is what makes that future amendment have real per-builder identities
to type against; it does not attempt the typing itself (that is Fable-spec, kernel-touching, out
of scope here).

Exit 0 on success (registered). Exit 1 on REFUSED/NOT-REGISTERED (this tool's own, or `led`'s,
relayed verbatim). Exit 2 on a local usage error. Lazy imports banned; stdlib only; no raw SQL --
every read shells out to `led current <N>`, the same served surface `role_charter.py` already
uses for its own `principal_registered` scan.
"""
from __future__ import annotations

import re
import subprocess
import sys

from served_shapes import parse_current_line as _parse_current_line

DEFAULT_LED = "./led"
DEFAULT_SCAN_LIMIT = 100000

PRINCIPAL_REGISTERED_KIND = "principal_registered"
# `led.tmpl`'s own `cmd_register_principal` statement text, `principal '<name>' registered ...`
# -- byte-identical to `tools/role_charter.py`'s own `PRINCIPAL_REGISTERED_RE` (ADR-0012 P1: one
# shape, checked the same way everywhere it matters; not re-derived here as a second regex that
# could quietly drift from that one).
PRINCIPAL_REGISTERED_RE = re.compile(r"^principal '([^']+)' registered")


class DispatchPrincipalError(Exception):
    """Raised with a message explaining exactly why this tool refused."""


def run_led(led: str, args: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run([led] + args, capture_output=True, text=True)
    except OSError as exc:
        return 127, "", f"could not execute '{led}': {exc}"
    return proc.returncode, proc.stdout, proc.stderr


def parse_current_line(led_cmd_label: str, line: str) -> tuple[int, str, str]:
    return _parse_current_line(DispatchPrincipalError, led_cmd_label, line)


def principal_is_registered(led: str, name: str, scan_limit: int) -> bool:
    """Same test `led`'s own `_resolve_actor` performs server-side (a `principal_registered`
    event naming `name` exists) -- here client-side and read-only, over the SAME `led current N`
    scan `tools/role_charter.py`'s own `principal_is_registered` already uses (identical shape,
    duplicated per-file rather than factored into `served_shapes.py`: the two tools' scan targets
    differ, `role -> principal` here vs `role -> role` there, on the SAME served text shape --
    factoring the one-line loop out would trade a real duplication for an indirection with no
    remaining shared logic to protect against drift)."""
    led_cmd_label = f"{led} current {scan_limit}"
    rc, out, err = run_led(led, ["current", str(scan_limit)])
    if rc != 0:
        raise DispatchPrincipalError(f"'{led_cmd_label}' failed:\n{err.strip() or out.strip()}")
    for line in out.splitlines():
        _rid, kind, statement = parse_current_line(led_cmd_label, line)
        if kind != PRINCIPAL_REGISTERED_KIND:
            continue
        m = PRINCIPAL_REGISTERED_RE.match(statement)
        if m and m.group(1) == name:
            return True
    return False


def cmd_preamble(name: str, led: str, scan_limit: int) -> int:
    if not principal_is_registered(led, name, scan_limit):
        raise DispatchPrincipalError(
            f"'{name}' is not a registered `led` principal -- a dispatch preamble cannot export "
            f"LED_ACTOR={name} for a name the s41 registry does not know (the exact refusal "
            f"`led` itself would give at write time, caught here BEFORE the builder's turn is "
            f"spent on it). Register it first:\n"
            f"  {led} register-principal {name} subagent --purpose \"<why this builder gets its own identity>\""
        )
    print(f"export LED_ACTOR={name}")
    return 0


def cmd_check(name: str, led: str, scan_limit: int) -> int:
    if principal_is_registered(led, name, scan_limit):
        print(f"REGISTERED: '{name}'")
        return 0
    print(f"NOT-REGISTERED: '{name}'")
    return 1


def usage(msg: str | None = None) -> int:
    if msg:
        print(f"dispatch_principal: {msg}", file=sys.stderr)
    print(
        "usage: python3 tools/dispatch_principal.py preamble <name> [--led PATH] [--scan-limit N]\n"
        "       python3 tools/dispatch_principal.py check <name>    [--led PATH] [--scan-limit N]",
        file=sys.stderr,
    )
    return 2


def main(argv: list[str]) -> int:
    if not argv:
        return usage()
    sub = argv[0]
    rest = argv[1:]
    led = DEFAULT_LED
    scan_limit = DEFAULT_SCAN_LIMIT
    positional: list[str] = []
    i = 0
    while i < len(rest):
        a = rest[i]
        if a == "--led":
            if i + 1 >= len(rest):
                return usage("--led requires a value")
            led = rest[i + 1]
            i += 2
        elif a == "--scan-limit":
            if i + 1 >= len(rest):
                return usage("--scan-limit requires a value")
            try:
                scan_limit = int(rest[i + 1])
            except ValueError:
                return usage(f"--scan-limit value '{rest[i + 1]}' is not an integer")
            i += 2
        else:
            positional.append(a)
            i += 1

    try:
        if sub == "preamble":
            if len(positional) != 1:
                return usage("'preamble' takes exactly <name>")
            return cmd_preamble(positional[0], led, scan_limit)
        elif sub == "check":
            if len(positional) != 1:
                return usage("'check' takes exactly <name>")
            return cmd_check(positional[0], led, scan_limit)
        else:
            return usage(f"unrecognized subcommand '{sub}'")
    except DispatchPrincipalError as exc:
        print(f"dispatch_principal: REFUSED -- {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
