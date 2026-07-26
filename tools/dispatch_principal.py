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
    python3 tools/dispatch_principal.py check <name>    [--led PATH] [--scan-limit N] [--json]

Both subcommands REFUSE first, before touching `led` at all, on any `<name>` containing a
character outside `[A-Za-z0-9_-]` -- see `validate_name_charset`'s docstring.

`preamble <name>`: if `<name>` is a registered, non-suspended-looking principal (see "Honest
limits" below), prints the ready-to-paste `export LED_ACTOR=<name>` line for the dispatch
preamble/brief and exits 0. If `<name>` is NOT registered, prints nothing on stdout, REFUSES on
stderr, and teaches the exact `./led register-principal <name> subagent --purpose "..."` command
to run first -- exit 1. This mirrors (and is a thin preflight in front of) `led`'s own
`_resolve_actor` refusal shape, so a caller who skips this check and dispatches anyway hits the
IDENTICAL refusal at write time, never a laxer or stricter one (defense in depth, not a second
authority).

`check <name>`: same registration test, machine-readable (`REGISTERED`/`NOT-REGISTERED: repr(name)`
on stdout by default, or one `{"name": ..., "registered": true|false}` JSON object with `--json`
-- see `cmd_check`'s own docstring for the quoting rule, finding 4 this fix round), exit 0/1 --
for a caller that wants the fact without the formatted preamble line (e.g. a batch pre-flight
over several builder names before a wave of dispatches, or a brief-generator parsing `--json`).

Honest limits: this tool tests REGISTRATION only (a `principal_registered` event exists for
`<name>`) -- an ANALOGOUS, BOUNDED APPROXIMATION of the test `led`'s own `_resolve_actor`
performs server-side, not the identical test (finding 3, this fix round's review; see
`principal_is_registered`'s own docstring below for exactly where and at what scale the two can
diverge). It does NOT check suspended/revoked standing (that is a live kernel fact `led`'s
`set_actor` trigger enforces at write time regardless of what this preflight says; a name that
was registered and later suspended still passes THIS check and then correctly refuses at the
real write -- this tool never duplicates that live-standing computation, per ADR-0012 P1, one
home for that fact and it is the kernel's).

NAME CHARSET (finding 1, this fix round's review): `preamble`/`check` both refuse, loudly, any
`<name>` containing a character outside `[A-Za-z0-9_-]` BEFORE doing anything else -- see
`_validate_name_charset`'s own docstring for why refusal, not only quoting, is the fix.

PER-BUILDER PRINCIPAL ACCUMULATION (finding 2, this fix round's review): every successful
`./led register-principal builder-<slug> subagent` this convention drives is an append-only
ledger write, forever -- there is no retirement/supersession step in this convention or this
tool, and this tool never invents one. When a dispatched builder's work item is done and an
orchestrator wants that principal off its own routine attention, the SEAM is the standing
lifecycle machinery `kernel/lineage/s45-standing-lifecycle.sql` already ships:
`./led principal suspend builder-<slug> "<reason>"` -- the same typed standing event that
retires any other principal, not a new mechanism minted here. This tool does not call it,
automatically or otherwise; registering AND suspending both stay the orchestrator's own
deliberate acts.

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

import json
import re
import shlex
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

# finding 1, this fix round's review: every naming convention this project actually uses for a
# principal (`builder-<work-item-slug>`, `author`, `reviewer`, `commissioner`) already fits this
# charset. A name that needs anything outside it to survive a shell round-trip is, in every
# observed case, an accident -- a typo, a pasted work-item title with a space in it, or a
# shell-injection attempt (`builder$(touch PWNED)`) riding an unquoted `export LED_ACTOR=<name>`
# preamble line straight into whatever shell pastes and evals it. Refusing here closes the
# mistake CLASS at its source, at the one point every caller of this tool passes through, rather
# than trusting every future caller to quote correctly.
NAME_CHARSET_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class DispatchPrincipalError(Exception):
    """Raised with a message explaining exactly why this tool refused."""


def validate_name_charset(name: str) -> None:
    """REFUSE loudly, before anything else runs, on any `name` containing a character outside
    `[A-Za-z0-9_-]` (finding 1, this fix round's review: `cmd_preamble` used to print
    `export LED_ACTOR={name}` UNQUOTED, and `led register-principal` applies zero charset
    validation of its own -- so a name like `builder$(touch PWNED)` produced a paste-line that
    executed the embedded command the instant a caller pasted and eval'd it).

    CHOICE MADE, STATED (the review asked for it explicitly): refusing on charset is the actual
    class-closer here, not `shlex.quote` alone. `shlex.quote` makes an arbitrary string SAFE to
    paste into a shell; it does not make it a SENSIBLE principal name, and a name that needs
    quoting to survive a shell round-trip is, in every naming convention this project actually
    uses, already a mistake -- so refusing teaches the caller to fix the real problem (a typo, a
    pasted title with a space, an injection attempt) instead of silently shipping a quoted but
    still-wrong name into the ledger. `cmd_preamble` below ALSO calls `shlex.quote` on top of
    this refusal, belt-and-suspenders: defense in depth, not a substitute -- if some future
    caller of `principal_is_registered`/`cmd_preamble` were ever reached without going through
    this check first, the printed line would still be safe to eval, just refused-on-purpose
    first here for every path that goes through `preamble`/`check` as documented."""
    if not NAME_CHARSET_RE.match(name):
        raise DispatchPrincipalError(
            f"{name!r} is not a valid principal name -- only letters, digits, '_', and '-' are "
            f"accepted (this fix round's review, finding 1: an unconstrained name that reaches "
            f"an `export LED_ACTOR=<name>` paste line is a shell-injection hazard even when "
            f"quoted, and is almost always an accident besides). Pick a name matching "
            f"[A-Za-z0-9_-]+, e.g. builder-<work-item-slug>."
        )


def run_led(led: str, args: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run([led] + args, capture_output=True, text=True)
    except OSError as exc:
        return 127, "", f"could not execute '{led}': {exc}"
    return proc.returncode, proc.stdout, proc.stderr


def parse_current_line(led_cmd_label: str, line: str) -> tuple[int, str, str]:
    return _parse_current_line(DispatchPrincipalError, led_cmd_label, line)


def principal_is_registered(led: str, name: str, scan_limit: int) -> bool:
    """An ANALOGOUS, BOUNDED APPROXIMATION of the test `led`'s own `_resolve_actor` performs
    server-side (finding 3, this fix round's review corrected the module docstring's earlier
    overclaim that this was "the SAME test") -- both ask "does a `principal_registered` event
    naming `name` exist", but `_resolve_actor` answers it against `GET /standing/principals`, a
    served, indexed, UNBOUNDED view of the registry, while this function answers it by scanning
    at most the most recent `scan_limit` (default 100000) rows of `led current N` client-side
    and regex-matching each `principal_registered` statement's own printed text -- the same
    bounded-scan idiom `tools/role_charter.py`'s own `principal_is_registered` already uses.
    The two views can diverge exactly at scale: a registration event older than the scan window
    on a ledger with more than `scan_limit` rows would read NOT-REGISTERED here while `led`'s
    own indexed lookup still finds it and writes correctly -- a false-refusal on this preflight,
    never a false-pass, and never load-bearing for correctness (the real write at `led` still
    gets the right answer either way; see this module's own docstring, "Honest limits"). Not
    factored into `served_shapes.py` alongside role_charter's sibling copy: the two tools' scan
    TARGETS differ (`role -> principal` here vs `role -> role` there) on the same served text
    shape, and factoring the one-line loop out would trade a real, small duplication for an
    indirection protecting no remaining shared logic."""
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
    validate_name_charset(name)
    if not principal_is_registered(led, name, scan_limit):
        raise DispatchPrincipalError(
            f"'{name}' is not a registered `led` principal -- a dispatch preamble cannot export "
            f"LED_ACTOR={name} for a name the s41 registry does not know (the exact refusal "
            f"`led` itself would give at write time, caught here BEFORE the builder's turn is "
            f"spent on it). Register it first:\n"
            f"  {led} register-principal {name} subagent --purpose \"<why this builder gets its own identity>\""
        )
    # finding 1, belt-and-suspenders: `validate_name_charset` above already refused anything
    # outside [A-Za-z0-9_-], so `shlex.quote` is a no-op on every name that reaches this line --
    # kept anyway so this printed line is independently safe to eval even if that refusal is
    # ever loosened or bypassed by a future caller of this function.
    print(f"export LED_ACTOR={shlex.quote(name)}")
    return 0


def cmd_check(name: str, led: str, scan_limit: int, json_output: bool) -> int:
    """MACHINE-READABLE QUOTING RULE (finding 4, this fix round's review): the plain-text mode's
    old `'{name}'` interpolation had no quoting rule at all -- a name containing a literal `'`
    would break any parser splitting on it. Two rules now apply, and a caller gets to pick:
    `--json` emits one JSON object (`json.dumps`, which escapes correctly by construction --
    the rigorous choice for a brief-generator or any other real parser); the default plain-text
    mode uses Python `repr()` instead of hand-rolled quotes, which is unambiguous and
    round-trips through `ast.literal_eval` for a caller that insists on text. Either way, `name`
    itself is charset-validated before either code path runs, so in practice neither ever sees
    a quote character -- both are kept rigorous anyway rather than resting on that as the only
    protection (defense in depth, same posture as the shlex.quote() in cmd_preamble)."""
    validate_name_charset(name)
    registered = principal_is_registered(led, name, scan_limit)
    if json_output:
        print(json.dumps({"name": name, "registered": registered}))
    else:
        status = "REGISTERED" if registered else "NOT-REGISTERED"
        print(f"{status}: {name!r}")
    return 0 if registered else 1


def usage(msg: str | None = None) -> int:
    if msg:
        print(f"dispatch_principal: {msg}", file=sys.stderr)
    print(
        "usage: python3 tools/dispatch_principal.py preamble <name> [--led PATH] [--scan-limit N]\n"
        "       python3 tools/dispatch_principal.py check <name>    [--led PATH] [--scan-limit N] [--json]",
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
    json_output = False
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
        elif a == "--json":
            json_output = True
            i += 1
        else:
            positional.append(a)
            i += 1

    if json_output and sub != "check":
        return usage("--json is only meaningful for 'check'")

    try:
        if sub == "preamble":
            if len(positional) != 1:
                return usage("'preamble' takes exactly <name>")
            return cmd_preamble(positional[0], led, scan_limit)
        elif sub == "check":
            if len(positional) != 1:
                return usage("'check' takes exactly <name>")
            return cmd_check(positional[0], led, scan_limit, json_output)
        else:
            return usage(f"unrecognized subcommand '{sub}'")
    except DispatchPrincipalError as exc:
        print(f"dispatch_principal: REFUSED -- {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
