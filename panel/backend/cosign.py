# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T23:21:38Z
#   last-change: 2026-07-14T23:21:55Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""panel.backend.cosign — the ONLY write path this panel has: a subprocess wrapper around the
repo-root `./led` verb (spec S5).

No parallel write path is ever authored here (spec S3/S9): every mutation this backend performs
goes through `./led review` (co-sign) or `./led register-principal` (startup, idempotent), so
every kernel refusal, the SoD `validate_review` check, `validate_independence`'s stamp gate, and
the content-free-review tripwire fire exactly as they would from a terminal. A kernel refusal is
surfaced VERBATIM (stdout/stderr, exit code) -- this module never interprets a non-zero exit as
success, never retries past a refusal, and never fabricates a `review_id` when the subprocess
failed.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

import ledger_read
from config import INDEPENDENCE_VALUES, PanelConfig, VERDICTS


class CosignValidationError(Exception):
    """A co-sign request named a verdict/independence value outside the kernel's own closed
    vocabulary (spec S3: 400 naming the allowed values, BEFORE shelling out -- this is not the
    kernel refusing, it is refusing to even ask a grammar the kernel does not have)."""


@dataclass(frozen=True)
class LedResult:
    """The raw, unfiltered outcome of one `./led` invocation. `ok` is exit_code == 0 -- nothing
    fancier. Callers surface `stdout`/`stderr` verbatim; they never paraphrase a refusal."""
    ok: bool
    exit_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class CosignResult:
    ok: bool
    exit_code: int
    stdout: str
    stderr: str
    review_id: int | None


def _run_led(cfg: PanelConfig, args: list[str], actor: str | None) -> LedResult:
    env: dict[str, str] = {}
    env.update(os.environ)
    if actor:
        env["LED_ACTOR"] = actor
    proc = subprocess.run(
        [str(cfg.led_path), *args],
        cwd=str(cfg.repo_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return LedResult(ok=proc.returncode == 0, exit_code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


def ensure_principal_registered(cfg: PanelConfig, name: str, agent_class: str) -> LedResult:
    """`./led register-principal <name> <class>` -- idempotent (kernel ON CONFLICT DO NOTHING).
    Called at backend startup for `cfg.maintainer_principal` so the first co-sign never fails on
    an unregistered actor (spec S5)."""
    return _run_led(cfg, ["register-principal", name, agent_class], actor=None)


def cosign(cfg: PanelConfig, row_id: int, verdict: str, independence: str, basis: str) -> CosignResult:
    """Run `LED_ACTOR=<maintainer principal> ./led review <row_id> <verdict> <independence> <basis>`.
    Raises `CosignValidationError` if `verdict`/`independence` are outside the kernel's own
    vocabulary (fail fast, no subprocess spent) -- but does NOT pre-block a combination the
    kernel would refuse for a substantive reason (e.g. `managerial` with no verified stamp);
    that refusal is let through and surfaced verbatim in `stderr` with `ok=False` (spec S5)."""
    if verdict not in VERDICTS:
        raise CosignValidationError(f"verdict must be one of {VERDICTS}, got {verdict!r}")
    if independence not in INDEPENDENCE_VALUES:
        raise CosignValidationError(f"independence must be one of {INDEPENDENCE_VALUES}, got {independence!r}")
    if not basis or not basis.strip():
        raise CosignValidationError("basis (the review statement) must be a non-empty string")

    result = _run_led(cfg, ["review", str(row_id), verdict, independence, basis], actor=cfg.maintainer_principal)
    review_id: int | None = None
    if result.ok:
        review_id = _find_latest_review_id(cfg, row_id)
    return CosignResult(
        ok=result.ok,
        exit_code=result.exit_code,
        stdout=result.stdout,
        stderr=result.stderr,
        review_id=review_id,
    )


def _find_latest_review_id(cfg: PanelConfig, row_id: int) -> int | None:
    """`led review` prints no row id on success -- the review row's id is found by querying for
    it after the fact (the newest, unsuperseded `review` row against `row_id` by the configured
    maintainer principal). A tiny, honest post-hoc lookup, not a second write path: this function
    performs no INSERT, only a SELECT via `ledger_read.py`'s own connection helper."""
    return ledger_read.latest_review_id(cfg, regards=row_id, actor_name=cfg.maintainer_principal)
