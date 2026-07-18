#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T20:34:11Z
#   last-change: 2026-07-18T20:40:23Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""role_charter.py -- register/show/amend a role's CHARTER (the static half of
design/FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md's "two halves"). Commission: ledger row 1663.

WHAT A "CHARTER" IS, per the governing spec: a per-role markdown file (typically
`roles/<role>/CHARTER.md` in a scaffolded world) that binds only when REGISTERED -- a
`decision` ledger row naming the role's principal, the file's repo-relative path, and its
sha256. The ledger is the authority on which charter text is in force; a drifting loose file
with no registration row is UNREGISTERED, and this tool says so.

CONVENTION, NOT A KERNEL KIND (spec's own "Honest limits" section, by design -- the ADR-0011
conversion is deferred until the convention is witnessed recurring): a registration is an
ordinary `kind=decision` ledger row whose statement follows one fixed, parseable shape:

    role-charter registered: role=<role> path=<repo-relative-path> sha256=<64-hex-digest>

`amend` writes a NEW row of the identical shape with `--supersedes <old-row-id>` -- the
ledger's own uniform-retraction mechanism (s31) is what makes the old registration drop out
of `ledger_current`, exactly like any other superseded row. `register`/`amend`/`show` all
find "the in-force registration for <role>" by scanning `led current <N>` (already
supersedes-filtered server-side) for a decision row whose statement matches the shape above
and whose role field equals <role> -- never a second, hand-rolled supersession filter.

NO RAW SQL ANYWHERE: every read and write in this file is a subprocess call to `led` (or
`--led <path>`'s override) -- `led current`, `led show`, `led decision`. This is the CLI-side
derivation the spec commissions ("everything here is CLI-side derivation over objects that
already exist"); the write surface is `led`, never a direct psql connection.

HASH IS ALWAYS COMPUTED HERE, NEVER CALLER-SUPPLIED: `register`/`amend` read the file's
on-disk bytes themselves and compute sha256 -- a caller cannot assert a hash that does not
match what is actually on disk (the exact class of bug ADR-0002 exists to foreclose).

JUDGMENT CALLS THIS TOOL MAKES WHERE THE SPEC IS SILENT ON MECHANICS (documented here per
CLAUDE.md's "no hazard routed around silently" standard, mirroring tools/workflow_compile.py's
own J-notes convention):

  JC1. SCAN DEPTH. `led current <N>`/`led --recent <N>` return only the last N rows -- there
       is no `led` verb that filters ledger rows by kind or statement server-side. This tool
       therefore scans a caller-configurable `--scan-limit` (default 100000, effectively "all
       rows" for any world this spec's witnesses or a real deployment are expected to reach)
       and states this bound explicitly in its own `--help` text -- a charter registered
       further back than --scan-limit rows ago would read as UNREGISTERED, an honest,
       documented limit rather than a silent one.
  JC2. PATH STORAGE. "repo-relative path" is stored exactly as the caller typed it (relative
       to the caller's own CWD when invoked, matching every other path-shaped convention `led`
       itself already uses -- e.g. --evidence) -- this tool does not second-guess or rewrite a
       caller-supplied path against some inferred repo root, because a role's charter may live
       in a scaffolded WORLD's own tree, never assumed to be this autoharn checkout's tree.
  JC3. PRE-REGISTRATION PRINCIPAL CHECK. "refusing an unregistered principal with teaching"
       (spec, `register`) is read as: the ROLE NAME must already be a registered `led`
       principal (`led register-principal`) before a charter can bind to it -- checked by the
       same `led current <N>` scan, looking for a `principal_registered` event naming <role>.
       A charter for a principal that does not exist would bind to nothing.
  JC4. DOUBLE-REGISTRATION REFUSAL. `register` on a role that already carries an in-force
       registration is REFUSED, teaching `amend` instead -- not stated verbatim by the spec,
       but the same posture every other `led` registration verb in this project takes
       (`register-principal`'s own duplicate refusal), and silently allowing two live
       `register` rows to coexist would be exactly the kind of ambiguity `show`'s DRIFT check
       exists to avoid, moved earlier to write time.

Usage:
    python3 tools/role_charter.py register <role> <path> [--led PATH] [--scan-limit N]
    python3 tools/role_charter.py show <role>           [--led PATH] [--scan-limit N]
    python3 tools/role_charter.py amend <role> <path>   [--led PATH] [--scan-limit N]

--led defaults to "./led" (the SERVED boundary shim) -- every operation this tool performs
(`led current`, `led show`, `led decision [--supersedes]`) rides bootstrap/templates/led.tmpl's
own documented COVERED surface; no work-family verb is needed here, unlike tools/role_brief.py.
LED_ACTOR (the existing `led` env-var convention) is honored by ordinary subprocess env
inheritance -- this tool adds no second actor-selection flag.

Exit 0 on success. Exit 1 on a REFUSED condition (this tool's own, or `led`'s, relayed
verbatim). Exit 2 on a local usage error. Lazy imports banned; stdlib only.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_LED = "./led"
DEFAULT_SCAN_LIMIT = 100000

STATEMENT_RE = re.compile(
    r"^role-charter registered: role=(?P<role>\S+) path=(?P<path>.+) sha256=(?P<sha256>[0-9a-f]{64})$"
)
PRINCIPAL_REGISTERED_RE = re.compile(r"^principal '([^']+)' registered")
ROW_WRITTEN_RE = re.compile(r"row\s+(\d+)\s+written")


class CharterError(Exception):
    """Raised with a message explaining exactly why this tool refused."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def statement_for(role: str, path: str, digest: str) -> str:
    return f"role-charter registered: role={role} path={path} sha256={digest}"


def run_led(led: str, args: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run([led] + args, capture_output=True, text=True)
    except OSError as exc:
        # '{led}' does not exist / is not executable -- an ordinary, expected-shape failure
        # (a wrong --led path), not a crash: converted to the same (rc, out, err) shape every
        # caller here already handles, never an uncaught traceback.
        return 127, "", f"could not execute '{led}': {exc}"
    return proc.returncode, proc.stdout, proc.stderr


def parse_current_line(line: str) -> tuple[int, str, str, str] | None:
    """One line of `led current <N>` output: id|kind|statement|actor_name (psql -tA, default
    '|' field separator, matching the SELECT list in bootstrap/templates/legacy-led.tmpl's own
    `current` branch)."""
    parts = line.split("|")
    if len(parts) < 4:
        return None
    rid_s, kind, statement, actor_name = parts[0], parts[1], parts[2], "|".join(parts[3:])
    if not rid_s.isdigit():
        return None
    return int(rid_s), kind, statement, actor_name


def find_current_registrations(led: str, role: str, scan_limit: int) -> list[dict]:
    """Every IN-FORCE (ledger_current-filtered, i.e. already supersession-resolved server-side)
    decision row registering a charter for <role>, newest first. Normally at most one -- more
    than one is a real, loudly-reported anomaly (JC4's own hand-written-row caveat; the spec's
    "Honest limits" section names exactly this as uncaught at write time for a hand-authored
    row)."""
    rc, out, err = run_led(led, ["current", str(scan_limit)])
    if rc != 0:
        raise CharterError(f"'{led} current {scan_limit}' failed:\n{err.strip() or out.strip()}")
    found = []
    for line in out.splitlines():
        parsed = parse_current_line(line)
        if not parsed:
            continue
        rid, kind, statement, actor_name = parsed
        if kind != "decision":
            continue
        m = STATEMENT_RE.match(statement)
        if not m or m.group("role") != role:
            continue
        found.append({"id": rid, "role": role, "path": m.group("path"),
                       "sha256": m.group("sha256"), "written_by": actor_name})
    return found


def principal_is_registered(led: str, role: str, scan_limit: int) -> bool:
    rc, out, err = run_led(led, ["current", str(scan_limit)])
    if rc != 0:
        raise CharterError(f"'{led} current {scan_limit}' failed:\n{err.strip() or out.strip()}")
    for line in out.splitlines():
        parsed = parse_current_line(line)
        if not parsed:
            continue
        _rid, kind, statement, _actor = parsed
        if kind != "principal_registered":
            continue
        m = PRINCIPAL_REGISTERED_RE.match(statement)
        if m and m.group(1) == role:
            return True
    return False


def resolve_current_registration(led: str, role: str, scan_limit: int) -> dict | None:
    found = find_current_registrations(led, role, scan_limit)
    if not found:
        return None
    if len(found) > 1:
        ids = ", ".join(str(f["id"]) for f in found)
        print(
            f"role_charter: WARNING -- role '{role}' carries {len(found)} SIMULTANEOUSLY "
            f"in-force charter registration rows ({ids}) -- this should not happen through this "
            f"tool's own register/amend path (register refuses a duplicate; amend supersedes the "
            f"prior one), so this is either a hand-written registration row (spec's own disclosed "
            f"limit: a malformed hand-written registration is caught by `show`'s hash check, not "
            f"refused at write time) or two independent `register` calls raced. Treating the "
            f"HIGHEST row id ({max(f['id'] for f in found)}) as authoritative -- inspect the "
            f"others with `led show <id>` and retract the wrong one with a superseding row.",
            file=sys.stderr,
        )
    return max(found, key=lambda f: f["id"])


def cmd_register(role: str, path_str: str, led: str, scan_limit: int) -> int:
    path = Path(path_str)
    if not path.is_file():
        raise CharterError(
            f"'{path_str}' does not exist or is not a regular file -- nothing to register."
        )
    if not principal_is_registered(led, role, scan_limit):
        raise CharterError(
            f"principal '{role}' is not a registered `led` principal -- a charter cannot bind "
            f"to a principal that does not exist. Register it first:\n"
            f"  {led} register-principal {role} <human|model|subagent|tool> --purpose \"...\""
        )
    existing = resolve_current_registration(led, role, scan_limit)
    if existing:
        raise CharterError(
            f"role '{role}' already carries an in-force charter registration (row "
            f"{existing['id']}, path={existing['path']}). Use 'amend' to supersede it, not "
            f"'register' again:\n"
            f"  python3 tools/role_charter.py amend {role} <new-path>"
        )
    digest = sha256_file(path)
    stmt = statement_for(role, path_str, digest)
    rc, out, err = run_led(led, ["decision", stmt])
    if rc != 0:
        raise CharterError(f"{led} refused the registration write:\n{err.strip() or out.strip()}")
    m = ROW_WRITTEN_RE.search(out)
    row_id = m.group(1) if m else "?"
    print(f"role_charter: registered -- role '{role}' -> charter row {row_id}")
    print(f"  path:   {path_str}")
    print(f"  sha256: {digest}")
    print(out.strip())
    return 0


def cmd_show(role: str, led: str, scan_limit: int) -> int:
    reg = resolve_current_registration(led, role, scan_limit)
    if not reg:
        raise CharterError(
            f"role '{role}' has no registered charter (scanned the last {scan_limit} "
            f"ledger_current rows; see this tool's own JC1 note if the real registration is "
            f"older than that). Register one:\n"
            f"  python3 tools/role_charter.py register {role} <path>"
        )
    print(f"role '{role}': IN-FORCE charter registration, row {reg['id']} "
          f"(written by '{reg['written_by']}')")
    print(f"  path:   {reg['path']}")
    print(f"  sha256: {reg['sha256']}")
    rc, out, err = run_led(led, ["show", str(reg["id"])])
    if rc == 0:
        print("-- full ledger row --")
        print(out.strip())
    else:
        print(f"role_charter: NOTE -- '{led} show {reg['id']}' failed to re-fetch the full row "
              f"(non-fatal, the registration above is still authoritative):\n{err.strip()}",
              file=sys.stderr)
    on_disk = Path(reg["path"])
    if not on_disk.is_file():
        print(
            f"role_charter: DRIFT -- the registered path '{reg['path']}' does not exist on disk "
            f"right now (relative to CWD {Path.cwd()}) -- cannot verify the hash. This is a loud "
            f"warning, not a refusal (per the governing spec: 'a mismatch is a loud DRIFT "
            f"warning, not an error')."
        )
        return 0
    current_digest = sha256_file(on_disk)
    if current_digest != reg["sha256"]:
        print(
            f"role_charter: DRIFT -- on-disk bytes of '{reg['path']}' no longer match the "
            f"registered hash.\n"
            f"  registered sha256: {reg['sha256']}\n"
            f"  on-disk    sha256: {current_digest}\n"
            f"  Not a refusal -- the registered text is still what the ledger says is IN FORCE; "
            f"`amend` to bind the new bytes, or restore the file to match the registered hash."
        )
    else:
        print(f"role_charter: OK -- on-disk bytes match the registered hash ({current_digest}).")
    return 0


def cmd_amend(role: str, path_str: str, led: str, scan_limit: int) -> int:
    existing = resolve_current_registration(led, role, scan_limit)
    if not existing:
        raise CharterError(
            f"role '{role}' has no in-force charter registration to amend. Use 'register' "
            f"instead:\n  python3 tools/role_charter.py register {role} {path_str}"
        )
    path = Path(path_str)
    if not path.is_file():
        raise CharterError(
            f"'{path_str}' does not exist or is not a regular file -- nothing to amend to."
        )
    digest = sha256_file(path)
    stmt = statement_for(role, path_str, digest)
    # led's flag/statement ORDER IS ASYMMETRIC (ledger item led-refs-flag-order-parser-bug,
    # BACKLOG autoharn1 rows 1053/1054): flags are consumed by the top-of-file parser BEFORE the
    # variadic <kind> <statement...> capture begins, so --supersedes must precede "decision",
    # never follow the statement -- a trailing flag is silently swallowed into statement prose.
    rc, out, err = run_led(led, ["--supersedes", str(existing["id"]), "decision", stmt])
    if rc != 0:
        raise CharterError(f"{led} refused the amendment write:\n{err.strip() or out.strip()}")
    m = ROW_WRITTEN_RE.search(out)
    row_id = m.group(1) if m else "?"
    print(f"role_charter: amended -- role '{role}' -> charter row {row_id} "
          f"(supersedes row {existing['id']})")
    print(f"  old path:   {existing['path']}")
    print(f"  old sha256: {existing['sha256']}")
    print(f"  new path:   {path_str}")
    print(f"  new sha256: {digest}")
    print(out.strip())
    return 0


def usage(msg: str | None = None) -> int:
    if msg:
        print(f"role_charter: {msg}", file=sys.stderr)
    print(
        "usage: python3 tools/role_charter.py register <role> <path> [--led PATH] "
        "[--scan-limit N]\n"
        "       python3 tools/role_charter.py show <role>           [--led PATH] "
        "[--scan-limit N]\n"
        "       python3 tools/role_charter.py amend <role> <path>   [--led PATH] "
        "[--scan-limit N]",
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
        if sub == "register":
            if len(positional) != 2:
                return usage("'register' takes exactly <role> <path>")
            return cmd_register(positional[0], positional[1], led, scan_limit)
        elif sub == "show":
            if len(positional) != 1:
                return usage("'show' takes exactly <role>")
            return cmd_show(positional[0], led, scan_limit)
        elif sub == "amend":
            if len(positional) != 2:
                return usage("'amend' takes exactly <role> <path>")
            return cmd_amend(positional[0], positional[1], led, scan_limit)
        else:
            return usage(f"unrecognized subcommand '{sub}'")
    except CharterError as exc:
        print(f"role_charter: REFUSED -- {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
