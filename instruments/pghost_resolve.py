#!/usr/bin/env python3
"""pghost_resolve — the ONE place instruments/ resolves which Postgres host to connect to.

Before this module, roughly a dozen instruments each carried their own
`os.environ.get("EPISTEMIC_PGHOST", "192.168.122.1")` (or a bare literal with no env override
at all) — the maintainer's own LAN host baked into the PUBLIC surface as a silent default. A
fresh checkout of this repo, with no env var set and no `deployment.json` of its own, would
silently point every instrument at someone else's machine. This closes that class: the literal
default is gone. Resolution order, all instruments alike:

  1. Whichever env var(s) the caller names (its own precedence order, e.g.
     `HARNESS_PGHOST` before `EPISTEMIC_PGHOST`) — unchanged from what each instrument already
     checked first.
  2. This deployment's own `deployment.json` (`LEDGER_DEPLOYMENT=/path/to/deployment.json` if
     set, else `<repo-root>/deployment.json`) — the same record `engine/targets.py` and
     `bootstrap/new-project.sh` already read (`filing/deployment_record.py`, the one home for
     the shape), read here for its `host` field.
  3. Neither resolves: refuse LOUDLY (ADR-0002) naming exactly what to set — never a silent
     default to any host, least of all a specific person's machine.

Preserves this deployment's own current behavior unchanged (its `deployment.json` on disk
carries `host`), while a checkout without one now gets a refusal that teaches instead of a
silent connection to a stranger's LAN box.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
sys.path.insert(0, str(_REPO_ROOT / "filing"))

import deployment_record  # noqa: E402 (filing/deployment_record.py, the ONE home for the deployment.json shape)


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
