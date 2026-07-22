"""deployment_resolve -- the ONE home for CWD-FIRST `deployment.json` resolution, shared by every
`tools/` script an adopting-project operator is expected to invoke DIRECTLY, e.g.
`python3 /path/to/autoharn/tools/regrade_decisions.py` run FROM the operator's own project
directory (ledger item `deployment-resolution-cwd-first`). This is NOT the scaffolded
`led`/`judge`/`pickup` shims' own resolution -- those already resolve relative to the shim's OWN
directory (`bootstrap/templates/led.tmpl`'s `HERE`), which for a scaffolded project always equals
the project root itself; they never had this bug.

THE DEFECT THIS CLOSES. `tools/regrade_decisions.py` and `tools/export_precedence.py` (the idiom's
original source -- both copy-pasted the same `_load_deployment()` body) each had a no-env fallback
of `<this-tool's-own-checkout-root>/deployment.json`. Witnessed 2026-07-16: the maintainer ran
`python3 ../autoharn/tools/regrade_decisions.py` FROM their adopting project (which has its OWN
`deployment.json` at its root -- the primary, documented use case, both tools' own OPERATOR
WALKTHROUGH / USAGE sections say "cd <your-deployment-directory>" first) and was refused with a
path INTO THE AUTOHARN CHECKOUT, not their own project -- the wrong-repo-keying class (cf. the
`link_integrity --repo` fix). The tool's own source location has nothing to do with where the
CALLER's project lives; keying the fallback off `__file__` instead of the caller's cwd was the bug.

RESOLUTION ORDER (env overrides keep ABSOLUTE priority, unchanged from before this fix):
  1. `PICKUP_DEPLOYMENT` env var (the scaffolded-shim mechanism)
  2. `LEDGER_DEPLOYMENT` env var (`engine/targets.py`'s own override)
  3. `$PWD/deployment.json` -- the caller's OWN current directory (NEW: this is the fix). The
     primary use case: an operator `cd`s into their own project (which holds its own `./led` and
     `deployment.json`, the scaffold's own layout) and runs the tool by path.
  4. `<repo_root>/deployment.json` -- this tool's OWN checkout root, preserved unchanged so running
     a tool directly against autoharn's own dev deployment (from within the autoharn checkout, cwd
     == repo_root) keeps working exactly as it always did.

Neither (3) nor (4) existing is refused LOUDLY, naming BOTH searched paths plus both env-var
escapes -- never a guess, never an unhandled stack trace (ADR-0002; a zero-context operator must
be able to self-serve from the refusal text alone). A `deployment.json` that DOES exist at (3) but
fails to parse/validate raises immediately (via `deployment_record.DeploymentError`) -- it is never
silently skipped in favor of falling through to (4); an existing-but-broken record in the caller's
own cwd is a fact to fix, not a signal to look elsewhere.

Stdlib-only, top-of-file imports (the lazy-import gate, gates/no_lazy_imports.py, applies).
"""
from __future__ import annotations

import os
from pathlib import Path

import deployment_record  # filing/deployment_record.py, the ONE home for the deployment.json shape -- both live in filing/, no sys.path hop needed


def resolve_deployment(repo_root: Path) -> tuple[deployment_record.DeploymentRecord, Path]:
    """Resolve and load this tool's deployment.json, cwd-first (see module docstring for the full
    order and rationale). `repo_root` is the CALLING tool's own checkout root (its `_REPO_ROOT`),
    used only as fallback source (4) and in the refusal text -- never as the primary source.

    Returns `(record, resolved_path)`. Raises `deployment_record.DeploymentError` (never returns a
    partial/guessed record) if nothing resolves, or if a resolved path exists but fails to load."""
    env_path = os.environ.get("PICKUP_DEPLOYMENT") or os.environ.get("LEDGER_DEPLOYMENT")
    if env_path:
        resolved = Path(env_path).resolve()
        return deployment_record.load_deployment(str(resolved)), resolved

    cwd_candidate = (Path.cwd() / "deployment.json").resolve()
    if cwd_candidate.is_file():
        return deployment_record.load_deployment(str(cwd_candidate)), cwd_candidate

    repo_candidate = (Path(repo_root) / "deployment.json").resolve()
    if repo_candidate.is_file():
        return deployment_record.load_deployment(str(repo_candidate)), repo_candidate

    raise deployment_record.DeploymentError(
        f"no deployment record found -- searched {cwd_candidate} (this directory, i.e. your "
        f"current working directory) and {repo_candidate} (this tool's own checkout root). Run "
        f"this tool from your OWN project's directory (the one holding your './led' and its "
        f"'deployment.json', the scaffold's own layout), or point it at the right file with "
        f"PICKUP_DEPLOYMENT=/path/to/deployment.json or LEDGER_DEPLOYMENT=/path/to/deployment.json.")
