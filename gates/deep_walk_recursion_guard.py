#!/usr/bin/env python3
"""deep_walk_recursion_guard.py — mechanical enforcement of ONE structurally-enforced
RecursionError invariant over serving/boundary_service.py, per ledger work item
boundary-recursion-net-single-invariant (row 1628, re-asserted from autoharn1; A13's own
independent out-of-frame review's first residual).

THE DEFECT THIS CLOSES: three deep-walk call sites in that module -- A3.2's `json.loads`
parse, A13's `json.dumps(..., allow_nan=False)` reserialize, and A7's
`_representability_axis_failure`/`_iter_strings` walk -- each grew its OWN independent
`except RecursionError` (or `except (ValueError, RecursionError)`) clause over time, sharing
only the `_classify_parse_failure` classifier by convention. Nothing structurally stopped a
FOURTH deep-walk site, added later, from either (a) open-coding its own bypassing
`except RecursionError` instead of routing through the shared helper, or (b) omitting the net
entirely. This gate mechanizes the first half: `_guard_recursion` (serving/boundary_service.py)
is now the ONE function permitted to catch `RecursionError`; this gate refuses the file if any
OTHER `except` clause in it names `RecursionError`, in a bare or tuple form.

WHAT THIS DOES NOT CLAIM (named, not silently implied): this is a grep/AST-based CENSUS gate
(gates/no_lazy_imports.py's own family and instrument choice), not a semantic recursion-safety
prover. A fourth site that recurses over caller-controlled data with NO except clause at all --
an uncaught crash rather than a routed-around guard -- is a different, pre-existing defect
class (an unhandled RecursionError bare 500) this gate does not detect. What it DOES
mechanically guarantee: if a site in this file catches RecursionError at all, it does so
through the one shared helper, never through a second, independently-authored net.

Exit 0 (clean) when `_guard_recursion` exists, itself contains an `except ... RecursionError
...` clause, and no OTHER such clause exists anywhere else in the file. Exit 1, naming every
offending line, otherwise.

Usage:
    python3 gates/deep_walk_recursion_guard.py [path-to-boundary_service.py]
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = REPO / "serving" / "boundary_service.py"
GUARD_HELPER_NAME = "_guard_recursion"


def _names_recursion_error(node: ast.expr) -> bool:
    """True if an except-clause type expression names RecursionError -- a bare `Name`, or any
    element of a `Tuple` of exception types (`except (ValueError, RecursionError)`)."""
    if isinstance(node, ast.Name):
        return node.id == "RecursionError"
    if isinstance(node, ast.Tuple):
        return any(_names_recursion_error(e) for e in node.elts)
    return False


def violations_in(path: Path, base: Path = REPO) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as e:
        return [f"{path}:0: UNPARSEABLE ({e.__class__.__name__}) — gate cannot certify this file"]

    try:
        display = path.relative_to(base)
    except ValueError:
        display = path

    # Locate `_guard_recursion`'s own line range by AST (every descendant node's lineno) --
    # never a hand-typed line number, so a reflow/rename of the file cannot desync this gate.
    guard_node: ast.FunctionDef | None = None
    guard_lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == GUARD_HELPER_NAME:
            guard_node = node
            for sub in ast.walk(node):
                lineno = getattr(sub, "lineno", None)
                if lineno is not None:
                    guard_lines.add(lineno)
            break

    out: list[str] = []
    if guard_node is None:
        out.append(f"{display}: no `{GUARD_HELPER_NAME}` helper found — the single "
                   f"guarded-traversal invariant has no home to enforce")
        return out

    # Any `except ... RecursionError ...` OUTSIDE the helper is a bypass -- a deep-walk site
    # that grew its own independent net instead of routing through `_guard_recursion`.
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is not None \
                and node.lineno not in guard_lines and _names_recursion_error(node.type):
            out.append(
                f"{display}:{node.lineno}: `except ... RecursionError ...` OUTSIDE "
                f"`{GUARD_HELPER_NAME}` — a deep-walk site bypassing the single "
                f"guarded-traversal helper (boundary-recursion-net-single-invariant, "
                f"ledger row 1628)")

    # The helper itself must still actually carry the net -- either a literal
    # `except RecursionError` / `except (..., RecursionError, ...)`, OR (this codebase's own
    # shape) an `except <param>` where <param> is a keyword-only/regular parameter whose
    # DEFAULT value is `(RecursionError,)` or bare `RecursionError` -- the dynamic-dispatch
    # form `_guard_recursion` itself uses so a caller may widen the guarded exception set
    # (e.g. also folding in ValueError at the json.loads call sites) without a second helper.
    default_recursion_params: set[str] = set()
    all_args = (guard_node.args.posonlyargs + guard_node.args.args + guard_node.args.kwonlyargs)
    all_defaults = list(guard_node.args.defaults) + list(guard_node.args.kw_defaults)
    # Positional/posonly defaults right-align to the tail of args; kwonly defaults line up
    # 1:1 with kwonlyargs. Simplify by checking EVERY (name, default) pair reachable via
    # ast.iter_fields rather than hand-aligning offsets -- walk defaults against the params
    # they could belong to and accept if ANY named parameter's default matches.
    named_defaults: dict[str, ast.expr] = {}
    pos_only_and_args = guard_node.args.posonlyargs + guard_node.args.args
    pos_defaults = guard_node.args.defaults
    if pos_defaults:
        for name, default in zip(pos_only_and_args[-len(pos_defaults):], pos_defaults):
            named_defaults[name.arg] = default
    for name, default in zip(guard_node.args.kwonlyargs, guard_node.args.kw_defaults):
        if default is not None:
            named_defaults[name.arg] = default
    for pname, default in named_defaults.items():
        if _names_recursion_error(default):
            default_recursion_params.add(pname)

    saw_guard_except = False
    for node in ast.walk(guard_node):
        if isinstance(node, ast.ExceptHandler) and node.type is not None:
            if _names_recursion_error(node.type):
                saw_guard_except = True
            elif isinstance(node.type, ast.Name) and node.type.id in default_recursion_params:
                saw_guard_except = True

    if not saw_guard_except:
        out.append(f"{display}: `{GUARD_HELPER_NAME}` itself carries no "
                   f"`except ... RecursionError ...` clause (literal or via a "
                   f"RecursionError-defaulted parameter) — the helper lost its own net")

    return out


def main() -> int:
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_TARGET
    bad = violations_in(target)
    if bad:
        print(f"DEEP-WALK RECURSION GUARD VIOLATIONS ({len(bad)}) — "
              f"boundary-recursion-net-single-invariant (ledger row 1628):")
        print("\n".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
