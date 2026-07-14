# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T23:20:41Z
#   last-change: 2026-07-14T23:20:41Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""panel.backend.config — the ONE place panel/backend resolves where its ledger lives and how
it is configured (ADR-0012 P1).

Connection facts (db/host/schema/kern/role) come ONLY from `filing/deployment_record.py` +
`instruments/pghost_resolve.py` -- reproducing their resolution order exactly, never a
hardcoded host (spec S9). Both modules live outside this package's tree (repo-root `filing/`
and `instruments/`), so this module inserts their directories onto `sys.path` -- at import
time, top-of-file, exactly as `instruments/pghost_resolve.py` itself does for
`filing/deployment_record.py` -- and imports them as ordinary top-level names (no lazy import;
gates/no_lazy_imports.py applies to this file like every other).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "filing"))
sys.path.insert(0, str(_REPO_ROOT / "instruments"))

import deployment_record  # noqa: E402 (filing/deployment_record.py -- the one home for the deployment.json shape)
import pghost_resolve  # noqa: E402 (instruments/pghost_resolve.py -- the one home for host resolution)

# The kernel's own closed vocabularies (bootstrap/templates/led.tmpl `led review` usage text,
# kernel/lineage/s15-schema.sql's `review_detail` check constraints) -- named ONCE here so the
# API layer can 400 on an unrecognized value BEFORE shelling out, per spec S3's contract. This
# does not pre-block a value the kernel itself would refuse (e.g. `managerial` in an unstamped
# deployment) -- it only blocks a value that is not even in the kernel's vocabulary at all.
VERDICTS: tuple[str, ...] = ("attest", "attest_with_reservations", "refuse")
INDEPENDENCE_VALUES: tuple[str, ...] = ("self-review", "technical", "managerial", "financial")

# Status vocabulary a manifest item's live disposition renders as (spec S3 / S7). Named once,
# read by disposition.py (the pure derivation) and app.py (the API's `status` field) alike.
STATUS_VALUES: tuple[str, ...] = ("OPEN", "WITNESSED", "PARTIAL", "COSIGNED")

# Default principal name the panel co-signs AS (spec S5). `commissioner` (already registered,
# see PanelConfig docstring) is an acceptable configured alternative -- set PANEL_MAINTAINER_PRINCIPAL
# to override without a code edit.
DEFAULT_MAINTAINER_PRINCIPAL = "maintainer"

DEFAULT_POLL_INTERVAL_SECONDS = 2.0
DEFAULT_BIND_HOST = "127.0.0.1"
DEFAULT_BIND_PORT = 8420


@dataclass(frozen=True)
class PanelConfig:
    """Everything the backend needs to connect, poll, and shell out -- resolved ONCE at
    startup (app.py), threaded through every route/read/write rather than re-resolved per
    request (ADR-0012 P1: one home for these facts, not a second read site per call)."""
    repo_root: Path
    deployment: deployment_record.DeploymentRecord
    pghost: str
    maintainer_principal: str
    poll_interval: float
    bind_host: str
    bind_port: int
    led_path: Path
    manifests_dir: Path

    @property
    def pgdb(self) -> str:
        return self.deployment.db

    @property
    def schema(self) -> str:
        return self.deployment.schema

    @property
    def kern(self) -> str:
        return self.deployment.kern

    @property
    def role(self) -> str:
        return self.deployment.role


def load_config(repo_root: Path | None = None) -> PanelConfig:
    """Resolve a `PanelConfig` exactly the way `led`/`pickup`/`judge` resolve their own
    deployment facts: `LEDGER_DEPLOYMENT` (or `<repo_root>/deployment.json`) via
    `filing/deployment_record.py`, and the connect host via
    `instruments/pghost_resolve.py.resolve_pghost` -- env vars first (this panel's own
    `PANEL_PGHOST`, then the project's standing `EPISTEMIC_PGHOST`), the deployment record's
    `host` field second, a loud refusal (SystemExit) if neither resolves. Never a hardcoded
    host anywhere in this module or its callers."""
    root = (repo_root or _REPO_ROOT).resolve()
    dep_path = Path(os.environ.get("LEDGER_DEPLOYMENT", str(root / "deployment.json")))
    deployment = deployment_record.load_deployment(dep_path)
    pghost = pghost_resolve.resolve_pghost("PANEL_PGHOST", "EPISTEMIC_PGHOST")
    maintainer_principal = os.environ.get("PANEL_MAINTAINER_PRINCIPAL", DEFAULT_MAINTAINER_PRINCIPAL)
    poll_interval = float(os.environ.get("PANEL_POLL_INTERVAL", DEFAULT_POLL_INTERVAL_SECONDS))
    bind_host = os.environ.get("PANEL_BIND_HOST", DEFAULT_BIND_HOST)
    bind_port = int(os.environ.get("PANEL_BIND_PORT", DEFAULT_BIND_PORT))
    return PanelConfig(
        repo_root=root,
        deployment=deployment,
        pghost=pghost,
        maintainer_principal=maintainer_principal,
        poll_interval=poll_interval,
        bind_host=bind_host,
        bind_port=bind_port,
        led_path=root / "led",
        manifests_dir=_HERE.parent / "manifests",
    )
