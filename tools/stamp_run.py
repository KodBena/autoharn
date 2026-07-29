#!/usr/bin/env python3
"""stamp_run -- the CLI logic behind `autoharn stamp-run -- <command...>` (work item
human-countersign-stamp-path, ledger rows 619/667/672). libexec/autoharn/stamp-run is the thin
umbrella-CLI entry point (fixture-sandbox check, then delegates here) -- ALL the actual logic
lives in this module, mirroring the established repo-root-verb split (tools/dispatch_mechanics.py
behind libexec/autoharn/dispatch, gates/fixture_sweep.py behind libexec/autoharn/fixture-sweep).

THE PROBLEM this verb answers (row 619's finding, folded into this item's scope): the write
stamp s17/s21's kernel mechanism validates is minted ONLY by hooks/stamp_intercept.py, a Claude
Code PreToolUse hook. A human operator at a bare shell, or an unattended process (a courier cron
pull), never runs inside a hook-intercepted session -- their ledger writes carry NO identity
channel at all. Under `identity_enforcement=enforce` those writes 403 as anonymous; under
`grace` they land, but `stamp_verified=false`, and s17's `validate_independence` refuses an
unverified row's independence/countersign claim regardless of posture. Row 619 named this the
blocker that must be closed before autoharn3's enforce flip (row 667's work item), or the flip
strands exactly these two flows: the maintainer's own bare-terminal countersign (witnessed
2026-07-15, the item's own origin) and every unattended courier pull.

THE FIX: mint the SAME kind of interception stamp the hook injects -- HMAC(secret,
session|agent|ts) plus a per-invocation correlation token, see tools/stamp_mint.py for the one
shared implementation of that algorithm -- and export it as the identical `app.vendor_*`
PGOPTIONS GUC set, then `os.execvpe` the wrapped command with that environment. Any psql
connection the wrapped command opens (directly, or nested inside `led`/`courier`/a served shim)
inherits the GUCs exactly as it would under the hook's own export; the kernel's `set_stamp`
trigger validates it identically -- no kernel change, no second verification path, ONE home for
the minting algorithm (tools/stamp_mint.py's own docstring names the disclosed hooks/
stamp_intercept.py two-home interim).

DEPLOYMENT RESOLUTION ("the deployment root being where deployment.json lives, never bare cwd",
ledger row 672): an explicit `LEDGER_DEPLOYMENT` env var (mirroring hooks/stamp_intercept.py's
own `_find_deployment_path` convention, and giving a scratch-world witness a way to point this
repo's own `stamp-run` at a throwaway deployment.json without touching the real one) wins; else
this repo's OWN root deployment.json (`autoharn stamp-run` is a repo-root verb, exactly like
`led`/`doctor` -- the operator's bare shell `cwd` when they type `autoharn stamp-run` is NEVER
consulted, only the fixed repo checkout or the explicit override).

SECRET RESOLUTION (ledger row 672's own spec'd order): explicit `STAMP_SECRET` env var wins;
else `<deployment root>/.claude/secrets/stamp_secret.hex` (the SAME project-convention default
hooks/stamp_intercept.py's own `_resolve_secret_path` derives).

IDENTITY FIELDS (never impersonating a harness session -- a Claude Code `session_id` is always a
UUID the hook mints; these are literal, honestly-named markers no harness session ever carries,
so a stamp minted here can NEVER collide with a genuine hook-minted stamp on either half of the
(session, agent) pair s21 reads for distinctness):
    session = $STAMP_RUN_SESSION, default "operator-terminal"
    agent   = $STAMP_RUN_AGENT,   default "operator"
Both overridable per-invocation so a distinct unattended context (e.g. a courier cron wrapper
exporting `STAMP_RUN_AGENT=courier-cron` before invoking this verb) can carry its own honestly-
named marker rather than colliding under the shared "operator" default with an interactive
bare-terminal countersign -- s21 reads the (session, agent) PAIR, so two contexts that want to be
treated as genuinely separate invocations must differ on at least one half of that pair
themselves; this module does not mint a fresh random session per call because a STABLE marker
across one sitting's several commands is the more honest shape (mirrors a harness session_id's
own "stable across many Bash calls" semantics -- the per-call granularity lives on the agent/
invocation side, not the session side).

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import stamp_mint  # noqa: E402  (tools/stamp_mint.py -- the one shared minting implementation)

PROG = "autoharn stamp-run"

_USAGE = f"usage: {PROG} -- <command> [args...]"


def _find_deployment_path() -> Path | None:
    """Resolve this invocation's deployment.json: an explicit LEDGER_DEPLOYMENT env var wins
    (same override name/convention as hooks/stamp_intercept.py's own _find_deployment_path,
    letting a scratch-world witness point this repo's stamp-run at a throwaway deployment
    record); else this repo's own root deployment.json -- never the operator's bare cwd (this
    is a repo-root verb, exactly like led/doctor, always anchored at _REPO_ROOT regardless of
    where the shell happens to be when `autoharn stamp-run` is typed)."""
    explicit = os.environ.get("LEDGER_DEPLOYMENT", "")
    if explicit:
        p = Path(explicit)
        return p if p.is_file() else None
    candidate = _REPO_ROOT / "deployment.json"
    return candidate if candidate.is_file() else None


def _resolve_secret_path(dep_path: Path | None) -> tuple[str, bool]:
    """Resolution order per ledger row 672: explicit STAMP_SECRET env var wins (returns
    explicit=True so the caller can name it in a teach-text); else the deployment root's own
    .claude/secrets/stamp_secret.hex; else ("", False) when there is no deployment root to
    derive a default from at all."""
    explicit_path = os.environ.get("STAMP_SECRET", "")
    if explicit_path:
        return explicit_path, True
    if dep_path is not None:
        return str(dep_path.parent / ".claude" / "secrets" / "stamp_secret.hex"), False
    return "", False


def _split_command(argv: list[str]) -> list[str]:
    """Everything after a leading `--` is the wrapped command; if argv does not start with `--`
    at all, the WHOLE of argv is treated as the command (this verb takes no flags of its own, so
    there is no ambiguity either way -- `--` is accepted, not required, exactly like `env --`'s
    own convention)."""
    if argv and argv[0] == "--":
        return argv[1:]
    return argv


def main(argv: list[str]) -> int:
    if argv in (["--help"], ["-h"], ["help"]):
        print(__doc__)
        print()
        print(_USAGE)
        return 0

    command = _split_command(argv)
    if not command:
        print(f"{PROG}: REFUSED -- no wrapped command given.", file=sys.stderr)
        print(_USAGE, file=sys.stderr)
        print(f"Example: {PROG} -- led work claim my-slug", file=sys.stderr)
        return 2

    dep_path = _find_deployment_path()
    if dep_path is None:
        override = os.environ.get("LEDGER_DEPLOYMENT", "")
        where = override if override else str(_REPO_ROOT / "deployment.json")
        print(f"{PROG}: REFUSED -- no deployment.json found at '{where}'.", file=sys.stderr)
        print("  This verb needs a deployment record to locate the stamp secret (its directory", file=sys.stderr)
        print("  is the 'deployment root' the STAMP_SECRET default is derived from). Fix: run", file=sys.stderr)
        print("  this from a world that has a deployment.json at its root, or set", file=sys.stderr)
        print("  LEDGER_DEPLOYMENT=/path/to/deployment.json explicitly. Nothing was touched.", file=sys.stderr)
        return 3

    secret_path, explicit = _resolve_secret_path(dep_path)
    secret = stamp_mint.load_secret(secret_path)
    if secret is None:
        howsit = "STAMP_SECRET" if explicit else "the deployment-derived default"
        print(f"{PROG}: REFUSED -- no usable stamp secret at '{secret_path}' ({howsit}).",
              file=sys.stderr)
        print("  The file is missing, unreadable, empty, or not valid hex. This mirrors", file=sys.stderr)
        print("  hooks/stamp_intercept.py's own fail-closed dangling-secret case -- refusing", file=sys.stderr)
        print("  rather than running the wrapped command unstamped. Seed the secret once (this", file=sys.stderr)
        print("  project's HOOKS.md, 'Stamp interceptor' section) if it has never been armed;", file=sys.stderr)
        print("  do NOT re-seed if it already has been (re-seeding rotates it and invalidates", file=sys.stderr)
        print("  every stamp already written under the old value). Nothing was touched.", file=sys.stderr)
        return 3

    session = os.environ.get("STAMP_RUN_SESSION", "operator-terminal")
    agent = os.environ.get("STAMP_RUN_AGENT", "operator")
    stamp = stamp_mint.mint(secret, session, agent)
    pgopts = stamp_mint.pgoptions(stamp)

    env = dict(os.environ)
    env["PGOPTIONS"] = pgopts

    try:
        os.execvpe(command[0], command, env)
    except FileNotFoundError:
        print(f"{PROG}: REFUSED -- wrapped command not found: '{command[0]}'.", file=sys.stderr)
        return 127
    except PermissionError:
        print(f"{PROG}: REFUSED -- wrapped command not executable: '{command[0]}'.", file=sys.stderr)
        return 126
    return 0  # unreachable on a successful exec (the process image is replaced)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
