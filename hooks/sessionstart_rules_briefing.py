#!/usr/bin/env python3
"""sessionstart_rules_briefing -- the SessionStart transport for `led briefing`
(bootstrap/templates/led.tmpl), the fresh-agent rules briefing verb.

MOTIVATION: a fresh agent presently discovers this project's three sharpest house rules (the
ledger change-gate, the flag-order asymmetry, the same-actor countersign refusal) only by
tripping them -- each is a REFUSAL with teach-text, but the teach-text arrives only after the
agent has already spent a turn on the wrong shape. `led briefing` (bootstrap/templates/led.tmpl)
is the single source of truth for that briefing's TEXT; this hook is a THIN TRANSPORT that resolves
the deployment, invokes the world's own `./led briefing`, and emits its stdout as SessionStart
additionalContext -- it contains NO copy of the briefing text itself (ADR-0012 P1: one fact, one
home). If the briefing verb's wording ever changes, this hook's output changes with it, for free,
because it never re-authors what the verb already says.

MATCHER GUIDANCE FOR ADOPTERS -- wire this hook on `startup|compact|resume`, not `compact|resume`
alone (the narrower matcher hooks/sessionstart_durable_decisions.py deliberately uses for ITS OWN,
different reason -- that hook's job is RE-injecting a decision already lost to a specific witnessed
failure surface, compaction, and `startup` is explicitly left to `./pickup` per the resumption
doctrine instead). This hook's job is different: a rules briefing is generically useful at the
START of any session an agent did not just live through, not only after a compaction blows away
context that was there a moment ago. Compaction loses the briefing too -- an agent that read it at
turn 1 and then compacted at turn 400 has, functionally, never read it from the fresh context's own
point of view -- so `compact` and `resume` are included alongside `startup` rather than treated as
`./pickup`'s exclusive territory. The concrete settings.json fragment (this project's own absolute-
path idiom, following the hooks/sessionstart_durable_decisions.py precedent) lives in
orchlog.d/rules-briefing.md, verbatim, so an adopter can copy it rather than re-derive it.

WIRING / UNWIRED POSTURE (the SAME posture hooks/sessionstart_durable_decisions.py already
establishes, re-derived independently here per that hook's own precedent -- not imported, because
each hook is its own short-lived process and this project's standing convention is a per-process
copy reconciled by mechanical scan, not a shared runtime import across independent hooks; see
filing/apparatus_registry.py's own docstring "WHY A DERIVED REGISTRY, NOT A HAND-MAINTAINED LIST"):
this hook is WIRED for a session iff SUBJECT_ROOT is either an explicit `LEDGER_DEPLOYMENT` env var
OR derived from a located `<cwd>/deployment.json`, AND the resolved deployment record loads
cleanly, AND that deployment's own directory carries a `led` executable. Any other session (a bare
autoharn checkout with no deployment.json, a pre-existing world that predates this hook's rollout
and was never re-wired) is UNWIRED and this hook emits nothing and exits 0 -- zero interference, by
construction, for every session that has not opted in.

FAILURE POSTURE (never block, never silent): a missing/malformed deployment.json, a missing `led`
executable, a `led briefing` that exits non-zero, times out, or raises anywhere in this pipeline
produces exactly ONE line of additionalContext naming that the briefing was unavailable and why --
never a blocked session, never a silent skip. This is a WEAKER failure posture than
hooks/sessionstart_durable_decisions.py's own "print nothing, exit 0" for a genuinely-unwired
session, and identical to that hook's own "FAILS OPEN" branch for a WIRED-but-broken one: the
distinction that matters is unwired (opted out; silence is correct) vs wired-but-broken (opted in;
silence would hide a real gap from the operator, so this hook says so instead).

Stdlib only, top-of-file imports (the lazy-import gate, gates/no_lazy_imports.py, applies).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)  # hooks/ -> autoharn root
sys.path.insert(0, os.path.join(_REPO_ROOT, "filing"))
import deployment_record  # noqa: E402  (filing/deployment_record.py, the ONE home for the shape)

_TIMEOUT_SECONDS = 15


def _find_deployment_path(data: dict) -> str | None:
    """Locate this project's deployment.json: an explicit LEDGER_DEPLOYMENT override first, else
    `<cwd>/deployment.json` using the hook input's own `cwd` field -- the IDENTICAL convention
    hooks/sessionstart_durable_decisions.py's own _find_deployment_path() already uses. Returns
    None -- never raises -- when neither resolves to an existing file."""
    explicit = os.environ.get("LEDGER_DEPLOYMENT", "")
    if explicit:
        return explicit
    cwd = data.get("cwd") or os.getcwd()
    candidate = os.path.join(cwd, "deployment.json")
    return candidate if os.path.isfile(candidate) else None


def _load_deployment_quiet(path: str) -> deployment_record.DeploymentRecord | None:
    """Best-effort deployment.json load. Never raises."""
    try:
        return deployment_record.load_deployment(path)
    except deployment_record.DeploymentError:
        return None


def _emit(context: str) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                              "additionalContext": context}}))


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # unparseable input -- nothing this hook can act on; allow (never the failure surface)

    dep_path = _find_deployment_path(data)
    if not dep_path:
        return 0  # unwired session -- zero interference, by design (module docstring)
    dep = _load_deployment_quiet(dep_path)
    if dep is None:
        return 0  # unwired/malformed deployment.json -- same zero-interference posture

    # The world's own `./led` -- a shim that execs the AUTOHARN CHECKOUT'S OWN
    # bootstrap/templates/led.tmpl, resolved by convention (bootstrap/new-project.sh's own shim
    # template) to live next to deployment.json in the world root. Same resolution point as
    # decomposition-review-status's own `world_root` inside led.tmpl itself: the directory
    # deployment.json was actually found in, not a second hand-derived notion of "world root".
    world_root = os.path.dirname(dep_path)
    led_path = os.path.join(world_root, "led")

    if not os.path.isfile(led_path):
        _emit(f"[sessionstart_rules_briefing] BRIEFING UNAVAILABLE: no `led` executable found at "
              f"{led_path} -- this deployment's world root carries no scaffolded ./led shim. "
              f"Run `./led briefing` by hand once the world is fully scaffolded.")
        return 0

    try:
        out = subprocess.run(
            [led_path, "briefing"],
            capture_output=True, text=True, timeout=_TIMEOUT_SECONDS, cwd=world_root,
        )
    except Exception as e:  # noqa: BLE001 -- FAILS OPEN posture (module docstring): a context-
        # hydration aid must never block session start, whatever the underlying cause (led missing
        # execute permission, a timeout, a launch failure).
        _emit(f"[sessionstart_rules_briefing] BRIEFING UNAVAILABLE ({type(e).__name__}): {e} -- "
              f"`{led_path} briefing` did not run. Run `./led briefing` by hand to see it now.")
        return 0

    if out.returncode != 0:
        detail = (out.stderr or out.stdout or "no output").strip().splitlines()[-1:] or ["(none)"]
        _emit(f"[sessionstart_rules_briefing] BRIEFING UNAVAILABLE: `led briefing` exited "
              f"{out.returncode} -- {detail[0]}. Run `./led briefing` by hand to see the full error.")
        return 0

    text = out.stdout.strip()
    if not text:
        _emit("[sessionstart_rules_briefing] BRIEFING UNAVAILABLE: `led briefing` ran cleanly but "
              "printed nothing. Run `./led briefing` by hand to investigate.")
        return 0

    _emit(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
