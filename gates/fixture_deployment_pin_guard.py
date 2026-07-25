#!/usr/bin/env python3
"""fixture_deployment_pin_guard.py — mechanical sweep for ledger work item
fixture-scratch-pinning-guard (row 1249, generalizing beyond `serve_existing_world`'s own
tempdir/repo-disjoint refusal in seen-red/boundary-service/run_fixtures.py).

THE LEAK THIS GUARDS AGAINST (ledger rows 1237-1244, marked garbage by row 1248): a seen-red
fixture resolved a REAL project's deployment.json and stood a served `led` against the LIVE
kernel, writing 8 garbage rows into it. `serve_existing_world` was fixed to refuse a
deployment.json that is not scratch-rooted-and-repo-disjoint — but that guard only covers ONE
call site. Nothing structurally stops a DIFFERENT fixture, or a later edit to an existing one,
from reaching the same live kernel by a different door:

  (a) invoking one of this CHECKOUT'S OWN operator verbs directly (`REPO / "led"`, or an
      f-string/`str()`-join spelling the same path) instead of a scaffolded copy under a temp
      dir. This checkout's root-level verb shims (e.g. `./led`) resolve their own deployment
      purely from `dirname($0)` — see `libexec/autoharn/led`'s own `HERE="$(cd "$(dirname
      "$0")/../.." && pwd)"` line — so invoking THIS repo's own `led` (as opposed to a
      scaffolded `<scratch-dest>/led`, itself a self-pinning shim written by
      `bootstrap/new-project.sh` / `bootstrap/track-work.sh` / `bootstrap/freeze-at-stamp.sh`,
      each computing its OWN `HERE` from its own location) resolves against THIS repo's
      deployment.json regardless of any environment variable the caller sets — the shim never
      reads an inherited override at all for its own HERE computation.
  (b) mutating `os.environ["PICKUP_DEPLOYMENT"]` directly (as opposed to building a per-call
      `env` dict and passing it via a subprocess call's own `env=` keyword) — a global mutation
      outlives the one call it was meant for and leaks into every OTHER subprocess this same
      fixture process spawns afterward, including an unrelated psql/git/whatever call that
      never meant to carry it — "env pinned per-subprocess, never inherited" (the item's own
      words) is exactly the discipline a direct `os.environ[...] =` assignment violates.

THE SHARED CONVENTION THIS GATE ENFORCES (builder's stated choice, ledger row 1249's own
"candidate shapes, builder picks with review"): this codebase already has TWO structurally-safe
patterns for a fixture to resolve its own scratch deployment —
  1. the self-pinning generated shim (`bootstrap/new-project.sh` et al. write `<dest>/led` etc.,
     each computing PICKUP_DEPLOYMENT from ITS OWN path, never inherited) — a fixture that only
     ever invokes `<scratch-dest>/<verb>` is safe by construction, no matter what env it runs
     under;
  2. `serve_existing_world`'s explicit tempdir-and-repo-disjoint refusal on the deployment.json
     path it stands a real boundary_service against.
Building a THIRD parallel helper would just be one more thing to keep in sync (this project's
own recurring lesson, e.g. bootstrap/shim-verbs.sh's own header); the gap ledger row 1249 names
is not that a safe path is missing, it is that NOTHING MECHANICALLY VERIFIES every fixture only
ever uses one of the two safe paths above. This gate is that mechanical verification — a
grep/AST-based CENSUS gate (gates/no_lazy_imports.py's own family and instrument choice, the
same "honest about its limits" precedent gates/deep_walk_recursion_guard.py's own docstring
sets), not a semantic dataflow prover.

WHAT THIS DOES NOT CLAIM (named, not silently implied):
  - This is a NAME-LIST/pattern census over each fixture file's OWN top-of-file `REPO = ...` /
    `AUTOHARN_ROOT = ...` / `EXEC_ROOT = ...` binding convention (already uniform across every
    existing seen-red driver — see this gate's own `_repo_like_or_default()`), not a full
    call-graph or alias-resolution pass. A REPO-rooted verb path reached only through an
    intermediate wrapper function, or bound under a name this gate does not recognize, is
    invisible to it — the same blind spot gates/deep_walk_recursion_guard.py's own docstring
    names for its wrapper-indirection gap.
  - The verb-name vocabulary comes from `bootstrap/shim-verbs.sh`'s own `SHIM_VERBS_ALL`
    (sourced live, never hand-duplicated — this project's own "one mechanism, not four that
    drift" lesson, that file's own header) — if a fixture invokes a verb under some OTHER name
    not in that set (a typo'd or since-renamed shim), this gate does not know to look for it.
  - `os.environ["PICKUP_DEPLOYMENT"] = ...` is refused UNCONDITIONALLY, everywhere in the
    scanned tree, on the theory that a fixture never has a legitimate reason to mutate its own
    process-global environment for this one variable — every existing fixture already achieves
    the same effect safely via a local `env = {**os.environ, "PICKUP_DEPLOYMENT": ...}` dict
    passed to one subprocess call's own `env=` kwarg. If a future fixture has a genuinely new
    reason to need the global mutation, that is a call for the maintainer/reviewer, not a
    silent pass.
  - A fourth kind of leak — a fixture that never touches REPO/env at all but simply forgets to
    scaffold its own scratch deployment.json and instead reads whatever deployment.json happens
    to sit in `os.getcwd()` at fixture-run time — is NOT detected here; that shape is exactly
    what `serve_existing_world`'s own tempdir-and-repo-disjoint refusal already closes at the
    one call site that stands a real boundary against a path (this gate's complement, not its
    duplicate).

SCOPE: seen-red/**/*.py, instruments/**/*.py, kernel/fixtures/**/*.py — the fixture/instrument
tree that seen-red's own README and gates/fixture_census.py already treat as this project's
led-exercising fixture corpus. Submodules (tools/*) are NOT scanned — each vendors its own gate
discipline (tools/autoharn-panel's tests are that submodule's own review surface, not this
repo's).

Exit 0 (clean) when no scanned file matches either anti-pattern. Exit 1, naming every offending
line, otherwise.

Usage:
    python3 gates/fixture_deployment_pin_guard.py [path ...]
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("seen-red", "instruments", "kernel/fixtures")
REPO_LIKE_NAMES = {"REPO", "AUTOHARN_ROOT", "EXEC_ROOT"}


def _shim_verb_names() -> set[str]:
    """The verb census, sourced LIVE from bootstrap/shim-verbs.sh's own SHIM_VERBS_ALL — never
    hand-duplicated (that file's own header names three prior scripts that drifted exactly this
    way)."""
    out = subprocess.run(
        ["sh", "-c", f". {REPO / 'bootstrap' / 'shim-verbs.sh'} && printf '%s' \"$SHIM_VERBS_ALL\""],
        capture_output=True, text=True, check=True)
    return set(out.stdout.split())


def _iter_target_files() -> list[Path]:
    files: list[Path] = []
    for d in SCAN_DIRS:
        base = REPO / d
        if base.is_dir():
            files.extend(sorted(base.rglob("*.py")))
    return files


def _read_source(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _repo_join_targets(tree: ast.Module) -> set[str]:
    """Which top-level names are bound to a REPO-like Path in this module (the census; see the
    module docstring's named blind spot)."""
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id in REPO_LIKE_NAMES:
            bound.add(node.targets[0].id)
    return bound


def _repo_like_or_default(tree: ast.Module) -> set[str]:
    found = _repo_join_targets(tree)
    return found or set(REPO_LIKE_NAMES)


def _const_str(node: ast.expr | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _names_repo_verb_join(node: ast.expr, repo_names: set[str], verb_names: set[str]) -> str | None:
    """True (returns the offending verb) if `node` is `<REPO-like> / "<verb>"` (or
    `<REPO-like> / "legacy" / "<verb>"`), optionally wrapped in `str(...)` (an argv element is
    almost always `str(REPO / "led")`, never the bare Path object — subprocess itself accepts
    either, but every real fixture in this tree spells the str() explicitly), or an f-string
    embedding a REPO-like name immediately followed by `/<verb>` text, or
    `str(<REPO-like>) + "/<verb>"`."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "str" \
            and len(node.args) == 1:
        node = node.args[0]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        right = _const_str(node.right)
        if right and right in verb_names:
            left = node.left
            if isinstance(left, ast.Name) and left.id in repo_names:
                return right
            if isinstance(left, ast.BinOp) and isinstance(left.op, ast.Div):
                mid = _const_str(left.right)
                if mid == "legacy" and isinstance(left.left, ast.Name) and left.left.id in repo_names:
                    return right
        return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = node.left, node.right
        right_s = _const_str(right)
        if right_s and isinstance(left, ast.Call) and isinstance(left.func, ast.Name) \
                and left.func.id == "str" and len(left.args) == 1 \
                and isinstance(left.args[0], ast.Name) and left.args[0].id in repo_names:
            tail = right_s.strip("/")
            for v in verb_names:
                if tail == v or tail.endswith(f"legacy/{v}"):
                    return v
        return None
    if isinstance(node, ast.JoinedStr):
        for i, part in enumerate(node.values):
            if isinstance(part, ast.FormattedValue) and isinstance(part.value, ast.Name) \
                    and part.value.id in repo_names and i + 1 < len(node.values):
                nxt = node.values[i + 1]
                if isinstance(nxt, ast.Constant) and isinstance(nxt.value, str):
                    tail = nxt.value.lstrip("/")
                    for v in verb_names:
                        if tail == v or tail.startswith(f"{v}/") or tail.startswith(f"{v} ") \
                                or tail.startswith(f"legacy/{v}"):
                            return v
        return None
    return None


def _is_environ_pickup_deployment_mutation(node: ast.Assign) -> bool:
    """`os.environ["PICKUP_DEPLOYMENT"] = ...` — a global, never-per-subprocess mutation of the
    pin variable."""
    if len(node.targets) != 1:
        return False
    t = node.targets[0]
    if not isinstance(t, ast.Subscript):
        return False
    key = _const_str(t.slice)
    if key != "PICKUP_DEPLOYMENT":
        return False
    val = t.value
    return isinstance(val, ast.Attribute) and val.attr == "environ" \
        and isinstance(val.value, ast.Name) and val.value.id == "os"


SUBPROCESS_CALL_ATTRS = {"run", "Popen", "check_call", "check_output", "call"}


def _is_subprocess_call(node: ast.Call) -> bool:
    f = node.func
    if isinstance(f, ast.Attribute) and f.attr in SUBPROCESS_CALL_ATTRS:
        return True
    if isinstance(f, ast.Name) and f.id in SUBPROCESS_CALL_ATTRS:
        return True
    return False


def violations_in(path: Path, verb_names: set[str]) -> list[str]:
    src = _read_source(path)
    if src is None:
        return []
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        return []
    repo_names = _repo_like_or_default(tree)
    out: list[str] = []
    display = str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)

    # CHECK 1: a subprocess call's argv contains a REPO-rooted verb path — this checkout's OWN
    # operator verb, never a scaffolded scratch copy (see module docstring, leak class (a)).
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_subprocess_call(node) and node.args:
            argv = node.args[0]
            if isinstance(argv, (ast.List, ast.Tuple)) and argv.elts:
                for elt in argv.elts:
                    verb = _names_repo_verb_join(elt, repo_names, verb_names)
                    if verb:
                        out.append(
                            f"{display}:{node.lineno}: subprocess call invokes THIS CHECKOUT'S "
                            f"OWN `{verb}` (a REPO-rooted path) instead of a scaffolded scratch "
                            f"copy — this repo's own root-level verb shims resolve their "
                            f"deployment from their own file location, never from a caller's "
                            f"env override (fixture-scratch-pinning-guard, ledger row 1249; the "
                            f"row-1237-1244/1248 leak class)")

    # CHECK 2: os.environ["PICKUP_DEPLOYMENT"] = ... — a global mutation, never per-subprocess.
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and _is_environ_pickup_deployment_mutation(node):
            out.append(
                f"{display}:{node.lineno}: `os.environ[\"PICKUP_DEPLOYMENT\"] = ...` mutates "
                f"the PROCESS-GLOBAL environment instead of pinning per-subprocess (build a "
                f"local `env = {{**os.environ, \"PICKUP_DEPLOYMENT\": ...}}` dict and pass it "
                f"via each subprocess call's own `env=` kwarg instead — fixture-scratch-pinning-"
                f"guard, ledger row 1249: \"env pinned per-subprocess, never inherited\")")

    return out


def main(argv: list[str]) -> int:
    verb_names = _shim_verb_names()
    if argv:
        targets = [Path(a).resolve() for a in argv]
    else:
        targets = _iter_target_files()
    bad: list[str] = []
    for t in targets:
        bad.extend(violations_in(t, verb_names))
    if bad:
        print(f"FIXTURE DEPLOYMENT PIN GUARD VIOLATIONS ({len(bad)}) — "
              f"fixture-scratch-pinning-guard (ledger row 1249):")
        print("\n".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
