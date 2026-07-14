#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T23:12:44Z
#   last-change: 2026-07-14T23:12:44Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""pghost_resolve -- the ONE home for "which Postgres host does this consumer connect to,"
promoted here from instruments/pghost_resolve.py (commit 27973d1) so engine/ can reach it
without a peer-directory import: engine/ already reaches filing/ directly for
`deployment_record.py` (engine/targets.py's own file-relative `sys.path` insert), and this
module lives beside it for the identical reason -- filing/ is the established shared lower
layer both engine/ and instruments/ import from (never each other), the same relationship
engine/targets.py's own docstring states for `deployment_record.py` ("the same pattern
instruments/ledger_target.py already uses to reach this module").

Before this module (and before instruments/pghost_resolve.py, the file it was promoted from),
several instruments/ and engine/ modules each carried their own
`os.environ.get("EPISTEMIC_PGHOST", "192.168.122.1")` (or a bare literal with no env override
at all) -- the maintainer's own LAN host baked into the PUBLIC surface as a silent default. A
fresh checkout of this repo, with no env var set and no `deployment.json` of its own, would
silently point every consumer at someone else's machine. This closes that class: the literal
default is gone. Resolution order, all consumers alike:

  1. Whichever env var(s) the caller names (its own precedence order, e.g.
     `HARNESS_PGHOST` before `EPISTEMIC_PGHOST`) -- unchanged from what each consumer already
     checked first.
  2. This deployment's own `deployment.json` (`LEDGER_DEPLOYMENT=/path/to/deployment.json` if
     set, else `<repo-root>/deployment.json`) -- the same record `engine/targets.py` and
     `bootstrap/new-project.sh` already read (`filing/deployment_record.py`, the one home for
     the shape), read here for its `host` field.
  3. Neither resolves: refuse LOUDLY (ADR-0002) naming exactly what to set -- never a silent
     default to any host, least of all a specific person's machine.

Preserves this deployment's own current behavior unchanged (its `deployment.json` on disk
carries `host`), while a checkout without one now gets a refusal that teaches instead of a
silent connection to a stranger's LAN box.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import os
from pathlib import Path

import deployment_record  # filing/deployment_record.py, the ONE home for the deployment.json shape -- both live in filing/, no sys.path hop needed

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent


def resolve_pghost(*env_vars: str) -> str:
    """Resolve the Postgres host to connect to, in the precedence order documented above.
    `env_vars` are checked first-to-last (pass the caller's own existing precedence, e.g.
    `resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")`). Raises SystemExit (a loud refusal,
    never a silent default) if nothing resolves."""
    for var in env_vars:
        val = os.environ.get(var)
        if val:
            return val
    dep_path = Path(os.environ.get("LEDGER_DEPLOYMENT", str(_REPO_ROOT / "deployment.json")))
    if dep_path.is_file():
        try:
            record = deployment_record.load_deployment(dep_path)
        except deployment_record.DeploymentError as e:
            raise SystemExit(
                f"REFUSED: {dep_path} does not parse as a deployment record ({e}) -- fix it, "
                f"or set {' or '.join(env_vars) or 'EPISTEMIC_PGHOST'} instead. Never defaulting "
                f"to any host.") from None
        if record.host:
            return record.host
    names = " or ".join(env_vars) if env_vars else "EPISTEMIC_PGHOST"
    raise SystemExit(
        f"REFUSED: no Postgres host resolved -- set {names}, or point LEDGER_DEPLOYMENT at a "
        f"deployment.json (its 'host' field), or place one at {dep_path} "
        f"(copy deployment.json.example and fill in your own values; see README.md "
        f"'Configuration'). Never defaulting to any host.")
