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

SECOND RESIDUAL (reviewer-demonstrated, closed here): the FIRST check above only names
`RecursionError` literally -- so the nearest natural bypass, a deep-walk site wrapped in
`except RuntimeError` (RecursionError's OWN SUPERCLASS, so it catches RecursionError by
inheritance without ever spelling the name), or the wider `except Exception`/
`except BaseException`/bare `except:`, sailed through clean. This gate now ALSO refuses any
except-clause, attached to a `try` whose body calls a censused deep-walk site (`_guard_recursion`
itself, `_iter_strings`, `_representability_axis_failure`, or a direct `json.loads`/`json.dumps`
call), whose type expression names `RuntimeError`, `Exception`, or `BaseException` -- or is a
bare `except:` -- unless that except line itself carries the
`# deep-walk-recursion-guard-superclass-reviewed: <reason>` waiver comment (this file's own
`WAIVER_TOKEN`; no such waiver exists in the shipped module today, so the check is unconditional
there).

WHAT THIS DOES NOT CLAIM (named, not silently implied): this is a grep/AST-based CENSUS gate
(gates/no_lazy_imports.py's own family and instrument choice), not a semantic recursion-safety
prover. Named gaps that remain even after the superclass-catch closure above:
  - A fourth site that recurses over caller-controlled data with NO except clause at all --
    an uncaught crash rather than a routed-around guard -- is a different, pre-existing defect
    class (an unhandled RecursionError bare 500) this gate does not detect.
  - The deep-walk-site census (what counts as "a try wrapping a traversal call") is itself a
    NAME LIST (`DEEP_WALK_CALL_NAMES` below plus the `json.loads`/`json.dumps` special case),
    not a call-graph / alias analysis -- a traversal reached only through an intermediate
    wrapper function this gate does not know the name of is invisible to it, same as any
    AST-census gate's blind spot for indirection.
  - The waiver token is a textual escape hatch, checked for PRESENCE only (like
    gates/doc_attestation_presence.py's own `doc-attest-exempt:` token) -- it does not
    (cannot) judge whether the stated reason is actually sound.
  - KNOWN SILENT GAP (named here deliberately, not fixed -- reviewer-demonstrated 2026-07-23):
    an ALIASED exception name -- `E = RuntimeError` at module scope, then `except E:` around a
    deep-walk call -- passes this gate silently. `_names_superclass_evasion` matches
    `ast.Name`/`ast.Attribute`/`ast.Tuple` shapes textually; it does not trace assignment to
    resolve `E` back to `RuntimeError`. Closing this needs scope-tracking (a name-binding pass
    over the module, at minimum), which is out of proportion for a census gate of this size --
    the same size-of-instrument judgment that already governs the wrapper-indirection gap
    above. Loud-and-honest rather than silently claiming more than this gate can check.

READ MODE (reviewer-demonstrated gap closed 2026-07-23, Finding A): pre-commit's contract is
about what the COMMIT will embed, not whatever happens to sit in the working tree at gate-run
time. By default (no `--tree` flag) this gate reads the STAGED bytes of the target file --
`git -C <its-directory> show :./<its-name>`, which resolves against whichever git work tree the
target actually lives in -- falling back to the working-tree file only when the path is not
staged at all (untracked, not inside any git work tree, or a fixture's tempfile in /tmp). This
closes the silent-pass shape: inject a violating `except` into
serving/boundary_service.py, `git add` it, then restore the clean file in the working tree
WITHOUT re-staging -- a tree-reading gate passes on the clean bytes while the staged (about to
be committed) bytes still carry the violation. Pass `--tree` to force reading the WORKING TREE
file directly instead, unconditionally, bypassing git entirely -- the mode the seen-red fixture
below uses, since its synthetic specimens are throwaway tempfiles that were never staged into
(and in general are not even inside) this repository's git index.

What it DOES mechanically guarantee: if a site in this file catches RecursionError at all, it
does so through the one shared helper, never through a second, independently-authored net --
whether that second net names `RecursionError` directly or reaches it by catching one of its
superclasses. And the verdict is over the bytes the commit will actually embed, not merely
whatever the working tree happens to hold when the gate runs.

Exit 0 (clean) when `_guard_recursion` exists, itself contains an `except ... RecursionError
...` clause, no OTHER such clause exists anywhere else in the file, AND no unwaived
superclass-catch (`RuntimeError`/`Exception`/`BaseException`/bare, spelled as a bare name OR
attribute-qualified like `builtins.RuntimeError`) wraps a censused deep-walk call. Exit 1,
naming every offending line, otherwise.

Usage:
    python3 gates/deep_walk_recursion_guard.py [--tree] [path-to-boundary_service.py]
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = REPO / "serving" / "boundary_service.py"
GUARD_HELPER_NAME = "_guard_recursion"

# The deep-walk-site census for the superclass-catch check below: a NAME LIST (this gate's own
# admitted blind spot -- see the module docstring's named-gaps list), not a call-graph analysis.
# `_guard_recursion` itself is included because the reviewer's demonstrated evasion wraps the
# CALL SITE (`_guard_recursion(json.loads, ...)`, `_guard_recursion(_iter_strings, ...)`, etc.)
# in its OWN broader except clause rather than adding a new site inside the helper.
DEEP_WALK_CALL_NAMES = {GUARD_HELPER_NAME, "_iter_strings", "_representability_axis_failure"}
# json.loads/json.dumps are also censused directly (an open-coded call that never even reaches
# _guard_recursion -- the other half of the reviewer's demonstrated bypass shape).
JSON_ATTR_NAMES = {"loads", "dumps"}

SUPERCLASS_NAMES = {"RuntimeError", "Exception", "BaseException"}
WAIVER_TOKEN = "deep-walk-recursion-guard-superclass-reviewed:"


def _names_recursion_error(node: ast.expr) -> bool:
    """True if an except-clause type expression names RecursionError -- a bare `Name`, or any
    element of a `Tuple` of exception types (`except (ValueError, RecursionError)`)."""
    if isinstance(node, ast.Name):
        return node.id == "RecursionError"
    if isinstance(node, ast.Tuple):
        return any(_names_recursion_error(e) for e in node.elts)
    return False


def _names_superclass_evasion(node: ast.expr | None) -> bool:
    """True if an except-clause type expression names one of RecursionError's OWN superclasses
    (`RuntimeError`, `Exception`, `BaseException`) -- the nearest natural bypass of the
    RecursionError-specific check above, since catching a superclass catches RecursionError by
    inheritance without ever spelling its name. `node is None` is a bare `except:`, the widest
    form of the same evasion. Also matches the ATTRIBUTE-QUALIFIED spelling
    (`except builtins.RuntimeError:`) by its trailing `.attr` -- cheap and sound, since none of
    SUPERCLASS_NAMES has a same-named-but-different meaning anywhere reachable as an attribute
    in this module (reviewer-demonstrated evasion, Finding B, 2026-07-23). The ALIASED-name form
    (`E = RuntimeError` then `except E:`) is a DIFFERENT, NOT closed here, gap -- see the module
    docstring's named KNOWN SILENT GAP; that needs scope/assignment tracking, out of proportion
    for a census gate."""
    if node is None:
        return True
    if isinstance(node, ast.Name):
        return node.id in SUPERCLASS_NAMES
    if isinstance(node, ast.Attribute):
        return node.attr in SUPERCLASS_NAMES
    if isinstance(node, ast.Tuple):
        return any(_names_superclass_evasion(e) for e in node.elts)
    return False


def _is_deep_walk_call(node: ast.AST) -> bool:
    """True if `node` is a Call to a censused deep-walk site: `_guard_recursion`/`_iter_strings`/
    `_representability_axis_failure` by name, or a direct `json.loads`/`json.dumps` attribute
    call."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in DEEP_WALK_CALL_NAMES
    if isinstance(func, ast.Attribute):
        return (func.attr in JSON_ATTR_NAMES
                and isinstance(func.value, ast.Name) and func.value.id == "json")
    return False


def _try_wraps_deep_walk_call(try_node: ast.Try) -> bool:
    """True if `try_node`'s own body (not its handlers/orelse/finally) calls a censused
    deep-walk site anywhere in its descendants."""
    for stmt in try_node.body:
        for sub in ast.walk(stmt):
            if _is_deep_walk_call(sub):
                return True
    return False


def _handler_has_waiver(handler: ast.ExceptHandler, lines: list[str]) -> bool:
    """The waiver is a textual token (checked for PRESENCE only, like
    gates/doc_attestation_presence.py's `doc-attest-exempt:`) searched from the `except` line
    through the line before the handler body's first statement -- NOT the `except` line alone.
    `ExceptHandler.lineno` is the `except` keyword's own line; a MULTI-LINE except-clause type
    expression (e.g. a long tuple, or a parenthesized type wrapped across lines) puts the
    waiver comment a reviewer naturally writes right before the colon on a line the old
    single-line check never looked at, over-refusing a genuinely-waived clause (Finding C,
    2026-07-23). Scanning through `body[0].lineno - 1` (inclusive) is safe in the fail-safe
    direction only -- it can never make an UNWAIVED clause pass, since the waiver token is
    still required to be textually present somewhere in that span."""
    start = handler.lineno
    end = handler.body[0].lineno - 1 if handler.body else start
    if end < start:
        end = start
    for lineno in range(start, end + 1):
        if 1 <= lineno <= len(lines) and WAIVER_TOKEN in lines[lineno - 1]:
            return True
    return False


def _read_staged_bytes(path: Path) -> str | None:
    """The STAGED content of `path` as `git show :./<name>` would print it -- the bytes the next
    commit will actually embed, per the index, regardless of whatever the working tree currently
    holds. Resolved via `git -C <path.parent> show :./<path.name>` -- the `:./<name>` pathspec is
    relative to `-C`'s cwd, so this finds the RIGHT repository for `path` (whichever one it
    actually lives in) rather than assuming it is always this gate's own repo -- load-bearing
    for the fixture below, which stages its reproduction in a throwaway git repo, not this one.
    Returns None (never raises) when `path`'s directory is not inside a git work tree at all or
    the path is not tracked/staged there -- callers fall back to the working-tree file in those
    cases. (If the `git` executable itself is absent from PATH, subprocess.run raises
    FileNotFoundError and the gate crashes loudly -- unreachable in the pre-commit context,
    which only ever runs under git, and deliberately not papered over here.)"""
    result = subprocess.run(
        ["git", "-C", str(path.parent), "show", f":./{path.name}"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def _read_source(path: Path, use_tree: bool) -> str:
    """The source text this gate should judge. Pre-commit's contract is about what the COMMIT
    will embed -- the STAGED bytes (`git show :./<name>`), not whatever the working tree happens
    to hold when the gate runs (Finding A, 2026-07-23): `git add` a violating change, then
    restore the clean file in the tree WITHOUT re-staging, and a tree-reading gate passes on the
    clean bytes while the staged (about-to-be-committed) bytes still carry the violation. So by
    default this reads the staged bytes, falling back to the working-tree file only when the
    path is not staged at all (untracked, not inside any git work tree, or `git` unavailable --
    e.g. a fixture's tempfile in /tmp). `use_tree=True` (the gate's `--tree` flag) forces the
    working-tree read unconditionally, bypassing git entirely -- the mode manual/fixture use
    wants when pointing this gate at a synthetic file that was never staged."""
    if not use_tree:
        staged = _read_staged_bytes(path)
        if staged is not None:
            return staged
    return path.read_text(encoding="utf-8")


def violations_in(path: Path, base: Path = REPO, use_tree: bool = False) -> list[str]:
    source = _read_source(path, use_tree)
    try:
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as e:
        return [f"{path}:0: UNPARSEABLE ({e.__class__.__name__}) — gate cannot certify this file"]

    try:
        display = path.relative_to(base)
    except ValueError:
        display = path

    lines = source.splitlines()

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

    # Superclass-catch evasion (reviewer-demonstrated): a try wrapping a censused deep-walk
    # call, caught by RecursionError's OWN SUPERCLASS (RuntimeError/Exception/BaseException) or
    # a bare `except:`, catches RecursionError by inheritance without ever spelling the name --
    # the nearest natural bypass of the RecursionError-literal check above. Scoped to ONLY the
    # try statements whose body calls a censused deep-walk site (`_try_wraps_deep_walk_call`),
    # never every Exception catch in the file, to keep the false-positive rate at the same
    # discipline as the check above.
    for node in ast.walk(tree):
        if isinstance(node, ast.Try) and _try_wraps_deep_walk_call(node):
            for handler in node.handlers:
                if _names_superclass_evasion(handler.type) and not _handler_has_waiver(handler, lines):
                    caught = "bare `except:`" if handler.type is None else \
                        f"`except {ast.unparse(handler.type)}`"
                    out.append(
                        f"{display}:{handler.lineno}: {caught} wraps a deep-walk call -- "
                        f"catching RuntimeError catches RecursionError by inheritance -- name "
                        f"RecursionError and route through {GUARD_HELPER_NAME}, or annotate why "
                        f"not (# {WAIVER_TOKEN} <reason> on the except line)")

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
    argv = sys.argv[1:]
    use_tree = "--tree" in argv
    argv = [a for a in argv if a != "--tree"]
    target = Path(argv[0]).resolve() if argv else DEFAULT_TARGET
    bad = violations_in(target, use_tree=use_tree)
    if bad:
        print(f"DEEP-WALK RECURSION GUARD VIOLATIONS ({len(bad)}) — "
              f"boundary-recursion-net-single-invariant (ledger row 1628):")
        print("\n".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
