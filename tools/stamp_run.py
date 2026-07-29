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
UUID the hook mints; these are literal, honestly-named DEFAULT markers no harness session ever
carries, so a stamp minted here UNDER ITS DEFAULTS cannot collide with a genuine hook-minted
stamp on either half of the (session, agent) pair s21 reads for distinctness):
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

THE NO-COLLISION PROPERTY IS DEFAULTS-ONLY, NOT A GUARANTEE (review rows 738/740, fix round):
the paragraph above is honest about the DEFAULT markers, but `STAMP_RUN_SESSION`/
`STAMP_RUN_AGENT` are same-user-forgeable overrides by design -- nothing stops a caller from
setting either to an arbitrary string, including one that happens to match a real harness
`session_id`/`agent_id` pair. This is an s17-grade LIMIT (same "same-OS-user tripwire, not
authentication" framing hooks/stamp_intercept.py's own docstring already discloses for its
PGOPTIONS-stripping and invocation-token mechanisms), not a hole unique to this verb. Two bounds
exist, not a proof: (1) the refusal tripwire below, which catches the one case that actually
matters -- a caller already holding a genuine hook-minted stamp trying to ALSO mint one here --
regardless of what session/agent strings it would have used; (2) the mutation-observer marker
(`.claude/mutation_observer_marker`) and this project's action-stream auditing, which make an
`env -u PGOPTIONS autoharn stamp-run -- ...` evasion (stripping an inherited hook stamp before
invoking this verb specifically to dodge the tripwire below) VISIBLE on the observed command
line, even though this module has no way to refuse it outright (it cannot distinguish "PGOPTIONS
was never set" from "PGOPTIONS was unset on purpose right before this call" from inside its own
process). Disclosed, not swept under the rug.

REFUSE-WHEN-ALREADY-STAMPED (the tripwire, review rows 738/740): before minting anything, this
verb inspects its INHERITED `PGOPTIONS` for the five `-c app.vendor_*` GUCs
hooks/stamp_intercept.py's own hook injects (see `_hook_stamp_fields` below for the exact
key/shape check -- this is a shape test on the vendor_* keys, not a generic "PGOPTIONS is
already set" test, so an operator's own unrelated `-c search_path=...`-style PGOPTIONS tuning
never trips it). If present, this verb REFUSES rather than minting a second, "independent"-
looking stamp under a different (session, agent) pair: stamp-run's whole charter is the bare-
terminal/cron/unattended operator who has NO hook-minted identity at all; inside an already-
hook-intercepted session (the ordinary case for any Claude Code Bash call in a wired world) the
hook has ALREADY stamped this exact process's ambient PGOPTIONS, so routing through stamp-run
here would let one acting context mint what looks to the kernel like a second, syntactically-
distinct countersigning identity for itself -- exactly the case s21's `validate_independence`
exists to catch, and exactly the CRITICAL the fresh-context review (rows 738/740) reproduced
end-to-end. There is no legitimate in-session use of stamp-run; the hook's own stamp already IS
the caller's identity there.

UNSTAMPED-PARENT PGOPTIONS IS COMPOSED, NOT CLOBBERED (review rows 738/740): when the inherited
PGOPTIONS is non-empty but does NOT match the hook-shape check above (an operator's own
unrelated `-c ...` tuning, not a vendor stamp), this verb no longer silently overwrites it --
the wrapped command may depend on that tuning for its own psql connections. This module's own
`-c app.vendor_*` GUCs are APPENDED after the inherited options (later `-c` wins on any name
collision, and no inherited option can collide with the `app.vendor_*` namespace by construction
of the check above), so both the operator's tuning and the freshly-minted stamp reach the
wrapped command's psql connections. Composing here was chosen over a refuse-with-teach because
appending `-c` options is unconditionally safe (PGOPTIONS accepts an arbitrary sequence of them)
and never silently drops operator state, unlike the clobber this replaces.

FUTURE KERNEL SLOT, NAMED NOT BUILT (review rows 738/740): the durable fix to the identity-class
question above lives kernel-side, not here -- a `stamp_origin` discriminator column
(hook-session-minted vs bare-terminal-minted) that a future kernel-lineage delta could add so
s21's independence gate can distinguish the two identity classes structurally instead of relying
on this verb's own tripwire. Not implemented in this pass (no kernel change rides with this fix
round); named here as the slot a future birth may fill.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import stamp_mint  # noqa: E402  (tools/stamp_mint.py -- the one shared minting implementation)

PROG = "autoharn stamp-run"

_USAGE = f"usage: {PROG} -- <command> [args...]"

# The four HMAC-bearing GUCs hooks/stamp_intercept.py's own `main()` always exports together on
# its stamped-injection path (module docstring's "REFUSE-WHEN-ALREADY-STAMPED"; see that file's
# `pgopts = (f"-c app.vendor_session=..." ...)` assembly for the byte-identical key set). The
# fifth GUC that hook also exports, app.vendor_invocation, is deliberately NOT required here --
# it is a plain correlation token (s23, verification-inert), disclosed there as capture-only, so
# requiring it would make this shape check depend on a field that is not part of the hook's own
# identity claim. Requiring these four (not just one) keeps this a SHAPE test on the vendor_*
# namespace specifically, not a generic "PGOPTIONS already has something in it" test -- an
# operator's own unrelated `-c search_path=...`/`-c work_mem=...` tuning never carries any of
# these four literal key names, so it can never trip this.
_HOOK_GUC_RE = re.compile(r"-c\s+(app\.vendor_[A-Za-z_]+)=(\S*)")
_HOOK_STAMP_REQUIRED_KEYS = ("app.vendor_session", "app.vendor_agent", "app.vendor_ts", "app.vendor_hmac")


def _hook_stamp_fields(pgoptions_value: str) -> dict[str, str]:
    """Parse `-c app.vendor_KEY=value` tokens out of a PGOPTIONS string (the same flat, space-
    separated `-c key=value` shape both hooks/stamp_intercept.py and tools/stamp_mint.py's own
    `pgoptions()` emit -- this is parsing GUC-assembly syntax we control, not shell command text,
    so a simple regex over the whole string is sufficient; no shell-quoting ambiguity applies)."""
    return dict(_HOOK_GUC_RE.findall(pgoptions_value))


def _is_hook_shaped_stamp(pgoptions_value: str) -> bool:
    """True iff `pgoptions_value` carries all four HMAC-bearing `app.vendor_*` GUCs
    hooks/stamp_intercept.py's own hook always injects together, with plausible shapes (a
    decimal unix timestamp; a hex-looking HMAC digest) -- not merely their bare presence, so a
    string that happens to mention these key names without the right value shapes (vanishingly
    unlikely, but cheap to guard) does not false-positive. This is a SHAPE test, never a
    signature-verification test: it does not need -- and does not have -- the stamp secret to
    decide "this looks like a genuine hook-minted stamp", only whether it looks like one at all;
    that is enough to answer "was this process already stamped by the hook", which is the only
    question the tripwire (module docstring) needs answered."""
    if not pgoptions_value:
        return False
    fields = _hook_stamp_fields(pgoptions_value)
    if not all(k in fields for k in _HOOK_STAMP_REQUIRED_KEYS):
        return False
    if not fields["app.vendor_ts"].isdigit():
        return False
    if not re.fullmatch(r"[0-9a-fA-F]{16,}", fields["app.vendor_hmac"]):
        return False
    return bool(fields["app.vendor_session"]) and bool(fields["app.vendor_agent"])


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

    inherited_pgoptions = os.environ.get("PGOPTIONS", "")
    if _is_hook_shaped_stamp(inherited_pgoptions):
        fields = _hook_stamp_fields(inherited_pgoptions)
        print(f"{PROG}: REFUSED -- this process is already carrying a hook-minted vendor stamp.",
              file=sys.stderr)
        print(f"  Found app.vendor_session={fields.get('app.vendor_session')!r} "
              f"app.vendor_agent={fields.get('app.vendor_agent')!r} in the inherited PGOPTIONS --", file=sys.stderr)
        print("  the shape hooks/stamp_intercept.py's own PreToolUse hook injects into every Bash", file=sys.stderr)
        print("  call in a wired session. stamp-run is a bare-terminal/cron/unattended-operator", file=sys.stderr)
        print("  instrument: it mints an identity stamp for a context that has NONE. Inside a", file=sys.stderr)
        print("  governed session the hook has already stamped this exact process -- that IS the", file=sys.stderr)
        print("  caller's identity here, and minting a second, differently-named stamp on top of", file=sys.stderr)
        print("  it would let one acting context countersign its own row under what looks to the", file=sys.stderr)
        print("  kernel like an independent identity (s21's validate_independence gap this fix", file=sys.stderr)
        print("  closes -- review rows 738/740). There is no legitimate in-session use of", file=sys.stderr)
        print("  stamp-run. Nothing was touched; the wrapped command was never invoked.", file=sys.stderr)
        return 4

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
    # COMPOSE, DON'T CLOBBER (review rows 738/740): inherited_pgoptions was already checked above
    # and is, by this point, NOT hook-shaped (the hook-shaped case already refused and returned).
    # If the operator's own PGOPTIONS carries unrelated tuning (e.g. a `-c search_path=...`), the
    # wrapped command's own psql connections may depend on it -- append this verb's own stamp
    # GUCs after it rather than discarding it. Later `-c` wins on any name collision, and nothing
    # inherited here can collide with the `app.vendor_*` namespace (that's exactly what the
    # hook-shape check above already ruled out), so appending is safe in both directions.
    env["PGOPTIONS"] = f"{inherited_pgoptions} {pgopts}".strip() if inherited_pgoptions else pgopts

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
