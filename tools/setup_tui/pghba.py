# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T21:32:47Z
#   last-change: 2026-07-19T03:36:42Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/pghba.py -- the dedicated-db path's pg_hba block generator (the substrate
screen, spec:
"generates the confined pg_hba block in the live file's own idiom -- reading the operator's real
pg_hba copy first, per the standing config-fragments rule").

The standing rule (memory: config-fragments-need-the-real-file) is never to author pg_hba lines
without reading the LIVE target file first and matching its own idiom -- order and house style
govern, not a hand-invented template. This module reads the live file the SAME way
`vestigial_documentation/design/MAINT-PG-HBA-HARDENING.md` did (`SELECT pg_read_file('pg_hba.conf')`,
witnessed there against a real cluster) via `psql`, then derives a block that matches the
existing per-database confinement idiom this cluster already uses (witnessed live, 2026-07-18,
against 192.168.122.1 db toy):

    host  <db>  <role>  <subnet-a>/32  trust
    host  <db>  <role>  <subnet-b>/32  trust
    host  all   <role>  0.0.0.0/0      reject
    local all   <role>                 reject

This module NEVER applies anything (v1 boundary: "No editing of the operator's real pg_hba in
place -- it generates the block and the diff, the operator applies"). It only reads (via a
read-only `SELECT pg_read_file`, no DDL) and prints.

INTERPRETER-BOUNDARY VALIDATION LIVES AT THE BOUNDARY FUNCTION (ledger row 1799 finding 4,
law/adr/0012's 2026-07-18 amendment): `db`/`role`/`subnets` are spliced as program text into the
pg_hba block this module generates -- a second evaluator's config text (postgresql's own
pg_hba.conf parser) -- with no bind-variable carrier available. `generate_block` below is the
actual splice site, so it is the boundary that refuses what it cannot honor (ADR-0012 P2), the
SAME `probes.pg_connect` pattern: the guard travels with every call site by construction, rather
than living only in one caller's loop (screens.py's own pre-check, kept as belt-and-braces --
see that call site's comment) where a future direct call to `generate_block`/`build_prepared_block`
bypassing screens.py would otherwise splice unvalidated text with no refusal at all."""
from __future__ import annotations

import subprocess

from tools.setup_tui import probes


class PgHbaReadError(RuntimeError):
    pass


class PgHbaValidationError(ValueError):
    """Raised by `generate_block` when `db`/`role`/`subnets` fail the closed-alphabet check
    BEFORE anything is spliced into the pg_hba block text -- never a coerced/escaped value."""


def read_live_pg_hba(host: str, probe_db: str = "postgres", timeout: float = 10.0) -> str:
    """Reads the LIVE pg_hba.conf off the cluster at `host` via `SELECT
    pg_read_file('pg_hba.conf')` -- the exact method MAINT-PG-HBA-HARDENING.md's own
    investigation used and witnessed live. `probe_db` only needs to be any database the
    connecting role can reach; it is not written to. Raises PgHbaReadError (never silently
    returns an empty/fabricated file) if the read fails -- e.g. insufficient privilege, per
    Postgres's own `pg_read_file` superuser/role requirement."""
    try:
        cp = subprocess.run(
            ["psql", "-h", host, "-d", probe_db, "-tA", "-c",
             "SELECT pg_read_file('pg_hba.conf')"],
            capture_output=True, text=True, timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PgHbaReadError(f"could not run psql to read pg_hba.conf: {exc}") from exc
    if cp.returncode != 0 or not cp.stdout.strip():
        raise PgHbaReadError(
            "could not read the live pg_hba.conf via `SELECT pg_read_file('pg_hba.conf')` "
            f"against {host}/{probe_db} (needs pg_read_all_settings or superuser, per Postgres's "
            f"own pg_read_file requirement): {cp.stderr.strip() or '(no output)'}"
        )
    return cp.stdout


def detect_idiom(live_text: str) -> dict:
    """Scans the live file's active (non-comment) lines for the per-database confinement idiom
    already in use -- column widths and whether a `local ... reject` companion line is the house
    convention -- so the generated block matches rather than invents a new style. Returns a
    dict with 'has_local_reject_lines' and 'sample_line' (the first matching `host <db> <role>
    ... trust` line found, for the operator to eyeball) or empty if the idiom could not be
    detected (never fabricated -- an empty result means the caller falls back to the block's own
    documented default shape, stated as such)."""
    sample = None
    has_local_reject = False
    for raw in live_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 5 and parts[0] == "host" and parts[-1] == "trust" and sample is None:
            sample = line
        if len(parts) >= 3 and parts[0] == "local" and parts[-1] == "reject":
            has_local_reject = True
    return {"sample_line": sample, "has_local_reject_lines": has_local_reject}


def generate_block(db: str, role: str, subnets: list[str]) -> str:
    """Generates the confined per-database block in the idiom witnessed live against
    192.168.122.1 db toy (2026-07-18): a `trust` line per subnet, then a `reject` catch-all pair
    (`host all` + `local all`) scoping the role to ONLY this database from ONLY these subnets --
    matching the existing per-role confinement style already on this cluster (e.g. the
    `toycolors_rw`/`ent_rw`/`qbx_rw` blocks in the same live file).

    Validates `db`/`role` (closed identifier alphabet) and every `subnets` token (closed CIDR
    alphabet, real-parsed) BEFORE splicing anything into the block text -- raises
    `PgHbaValidationError` naming the offending value, never a coerced/escaped substitute
    (module docstring: this is the actual splice site, so the guard lives here, travelling with
    every call site by construction)."""
    if not probes.valid_identifier(db):
        raise PgHbaValidationError(
            f"database name {db!r} contains characters outside [A-Za-z0-9_] -- refusing to "
            f"splice it into pg_hba text"
        )
    if not probes.valid_identifier(role):
        raise PgHbaValidationError(
            f"role name {role!r} contains characters outside [A-Za-z0-9_] -- refusing to "
            f"splice it into pg_hba text"
        )
    for subnet in subnets:
        if not probes.valid_subnet(subnet):
            raise PgHbaValidationError(
                f"subnet {subnet!r} is not a valid CIDR/host token -- refusing to splice it "
                f"into pg_hba text"
            )
    lines = [f"# {db}/{role} -- confined by tools/setup_tui (dedicated-db path); PREPARED, not applied"]
    for subnet in subnets:
        lines.append(f"host  {db}  {role}  {subnet}  trust")
    lines.append(f"host  all  {role}  0.0.0.0/0          reject")
    lines.append(f"local all  {role}                     reject")
    return "\n".join(lines)


def build_prepared_block(host: str, db: str, role: str, subnets: list[str],
                          probe_db: str = "postgres") -> tuple[str, str]:
    """Reads the live file, detects its idiom, and returns (block_text, disclosure_text) -- the
    disclosure names what was actually read (never invented) so an operator can see the basis
    for the generated block before deciding whether to apply it."""
    live_text = read_live_pg_hba(host, probe_db=probe_db)
    idiom = detect_idiom(live_text)
    block = generate_block(db, role, subnets)
    disclosure_lines = [
        f"Read live pg_hba.conf from {host} via `SELECT pg_read_file('pg_hba.conf')` "
        f"({len(live_text.splitlines())} lines).",
    ]
    if idiom["sample_line"]:
        disclosure_lines.append(f"Matched existing idiom, e.g.: {idiom['sample_line']}")
    else:
        disclosure_lines.append(
            "No existing 'host <db> <role> ... trust' line found to match idiom against -- "
            "using this module's own default column layout."
        )
    return block, "\n".join(disclosure_lines)
