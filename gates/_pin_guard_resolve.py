#!/usr/bin/env python3
"""_pin_guard_resolve.py -- pure-AST binding/argv resolution helpers for
gates/fixture_deployment_pin_guard.py (split out, ledger row 1249 fix-round 2, fresh-context
strengthened-tier review that BLOCKED 26c7c48). No I/O, no printing, no subprocess calls of its
own -- every function here takes an already-parsed `ast.Module` (or a piece of one) and returns a
resolution, never a verdict string; `fixture_deployment_pin_guard.py` owns all message text and
orchestration, this module owns only "what does this expression spell".

FIX-ROUND-2 CONTENT (per-finding, matched to the blocking verdict):
  - Finding 1 (waiver-blanket, THE BLOCKER): `_resolve_verb_element` no longer returns a
    binding's `Assign` node as a waiver-checkable span -- it returns only the resolved verb
    name. The caller (fixture_deployment_pin_guard.py) checks the waiver token ONLY against the
    enclosing Call's own line span, never a constant's binding line, so one waiver on
    `AUTOHARN = REPO / "autoharn"` no longer blankets every later use of AUTOHARN.
  - Finding 2 + 4 (post-binding argv mutation / append-built-from-empty-list): `_ListState` +
    `simulate_list_states` replay, in source-line order, every literal (re)binding,
    `.append`/`.insert`/`.extend`, subscript-assignment, `del`, and `+=` this module can see for
    each top-level Name, producing a best-known final element list. A mutation this cannot
    prove safe (dynamic index, non-literal extend/insert, non-list augassign) marks the name
    OPAQUE -- but only a name that was ever "sensitive" (carried a repo-verb-resolvable element
    at some point) surfaces as a flagged call; an opaque-but-never-sensitive name (an ordinary
    git/psql argv list with a dynamic flag) is silently out of scope, same as it always was.
  - Finding 3 (os.path.join / PurePath.joinpath): `_names_repo_verb_join` recognizes
    `os.path.join(REPO, "led")` (and the `str(REPO)` variant) and `REPO.joinpath("led")` as the
    same verb-path shape as the `REPO / "led"` BinOp/f-string forms it already covered.

WHAT THIS MODULE STILL DOES NOT CLAIM (unchanged blind spots from the prior round, restated
here since this is now where the resolution logic lives):
  - Only ONE hop of Name-binding indirection is resolved for the verb-path CONSTANT convention
    (`_verb_path_bindings`); a constant imported from another module (`from helper import LED`)
    is invisible -- this gate is a single-file AST census, not a cross-module resolver, and
    stops at the file boundary by construction.
  - `simulate_list_states` is LINE-ORDER ONLY, not control-flow aware: an `if`/`else` or a loop
    body is read as though every branch always executed in textual order. This can both over-
    and under-approximate a list's true runtime contents; it is a census heuristic over a
    fixture corpus of straight-line scripts, not a symbolic executor. A name only becomes
    "opaque" (unproven) when this module cannot follow a mutation at all -- it never silently
    trusts a stale, pre-mutation snapshot (the finding-2 defect), which is the property that
    matters for this gate's purpose.
"""
from __future__ import annotations

import ast

REPO_LIKE_NAMES = {"REPO", "AUTOHARN_ROOT", "EXEC_ROOT", "REPO_ROOT"}


def _const_str(node: ast.expr | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _const_int(node: ast.expr | None) -> int | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, int) \
            and not isinstance(node.value, bool):
        return node.value
    return None


def _unwrap_str_call(node: ast.expr) -> ast.expr:  # `str(X)` -> `X`
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "str" \
            and len(node.args) == 1:
        return node.args[0]
    return node


def repo_join_targets(tree: ast.Module) -> set[str]:  # top-level names bound to a REPO-like Path
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id in REPO_LIKE_NAMES:
            bound.add(node.targets[0].id)
    return bound


def repo_like_or_default(tree: ast.Module) -> set[str]:
    return repo_join_targets(tree) or set(REPO_LIKE_NAMES)


def _peel_join_chain(node: ast.expr, repo_names: set[str]) -> list[str] | None:
    """Peels a `<expr> / "<component>"` BinOp chain to its ordered components iff the base is a bare Name in `repo_names` and every right side is a string constant; None otherwise."""
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.Div):
        right = _const_str(cur.right)
        if right is None:
            return None
        parts.append(right)
        cur = cur.left
    if isinstance(cur, ast.Name) and cur.id in repo_names:
        parts.reverse()
        return parts
    return None


def _verb_from_join_parts(parts: list[str] | None, shim_verbs: set[str], libexec_verbs: set[str]
                           ) -> str | None:
    """Which operator-verb shape `parts` spells: `<verb>`/`legacy/<verb>` (vs `shim_verbs`) or `libexec/autoharn/<verb>` (vs `libexec_verbs`) -- None otherwise (e.g. the SAFE `.tmpl` shape, or `parts is None`)."""
    if parts is None:
        return None
    if len(parts) == 1 and parts[0] in shim_verbs:
        return parts[0]
    if len(parts) == 2 and parts[0] == "legacy" and parts[1] in shim_verbs:
        return parts[1]
    if len(parts) == 3 and parts[0] == "libexec" and parts[1] == "autoharn" and parts[2] in libexec_verbs:
        return parts[2]
    return None


def _os_path_join_parts(node: ast.Call, repo_names: set[str]) -> list[str] | None:
    """`os.path.join(REPO, "a", "b")` (or `os.path.join(str(REPO), ...)`) -> `["a","b"]`; None if not that shape (finding 3)."""
    f = node.func
    if not (isinstance(f, ast.Attribute) and f.attr == "join"
            and isinstance(f.value, ast.Attribute) and f.value.attr == "path"
            and isinstance(f.value.value, ast.Name) and f.value.value.id == "os"):
        return None
    if not node.args:
        return None
    base = _unwrap_str_call(node.args[0])
    if not (isinstance(base, ast.Name) and base.id in repo_names):
        return None
    parts = [_const_str(a) for a in node.args[1:]]
    return parts if parts and all(p is not None for p in parts) else None  # type: ignore[return-value]


def _joinpath_parts(node: ast.Call, repo_names: set[str]) -> list[str] | None:
    """`REPO.joinpath("a", "b")` (or `str(REPO).joinpath(...)`) -> `["a","b"]`; None otherwise (finding 3)."""
    f = node.func
    if not (isinstance(f, ast.Attribute) and f.attr == "joinpath"):
        return None
    base = _unwrap_str_call(f.value)
    if not (isinstance(base, ast.Name) and base.id in repo_names) or not node.args:
        return None
    parts = [_const_str(a) for a in node.args]
    return parts if parts and all(p is not None for p in parts) else None  # type: ignore[return-value]


def names_repo_verb_join(node: ast.expr, repo_names: set[str], shim_verbs: set[str],
                          libexec_verbs: set[str]) -> str | None:
    """The offending verb if `node` spells one of this repo's operator-verb paths: `/`-BinOp
    chain, f-string, `+`-concat, `os.path.join(...)`, or `.joinpath(...)` -- optionally
    `str(...)`-wrapped."""
    node = _unwrap_str_call(node)
    all_verbs = shim_verbs | libexec_verbs
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _verb_from_join_parts(_peel_join_chain(node, repo_names), shim_verbs, libexec_verbs)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = node.left, node.right
        right_s = _const_str(right)
        if right_s and isinstance(left, ast.Call) and isinstance(left.func, ast.Name) \
                and left.func.id == "str" and len(left.args) == 1 \
                and isinstance(left.args[0], ast.Name) and left.args[0].id in repo_names:
            tail = right_s.strip("/")
            for v in all_verbs:
                if (v in shim_verbs and (tail == v or tail.endswith(f"legacy/{v}"))) \
                        or (v in libexec_verbs and tail.endswith(f"libexec/autoharn/{v}")):
                    return v
        return None
    if isinstance(node, ast.JoinedStr):
        for i, part in enumerate(node.values):
            if isinstance(part, ast.FormattedValue) and isinstance(part.value, ast.Name) \
                    and part.value.id in repo_names and i + 1 < len(node.values):
                nxt = node.values[i + 1]
                if isinstance(nxt, ast.Constant) and isinstance(nxt.value, str):
                    tail = nxt.value.lstrip("/")
                    for v in all_verbs:
                        if v in shim_verbs and (tail == v or tail.startswith(f"{v}/")
                                                 or tail.startswith(f"{v} ")
                                                 or tail.startswith(f"legacy/{v}")):
                            return v
                        if v in libexec_verbs and tail.startswith(f"libexec/autoharn/{v}"):
                            return v
        return None
    if isinstance(node, ast.Call):
        return _verb_from_join_parts(_os_path_join_parts(node, repo_names), shim_verbs, libexec_verbs) \
            or _verb_from_join_parts(_joinpath_parts(node, repo_names), shim_verbs, libexec_verbs)
    return None


def verb_path_bindings(tree: ast.Module, repo_names: set[str], shim_verbs: set[str],
                        libexec_verbs: set[str]) -> dict[str, str]:
    """Name -> verb per top-level `NAME = <repo-verb-join-expr>` binding (the DOMINANT
    convention: LED_TMPL/ATTEST_TAGS/AUTOHARN). Deliberately NOT keyed to the defining Assign
    node (finding 1: that was the waiver-blanket bug) -- callers check waivers only at the USE
    site."""
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            verb = names_repo_verb_join(node.value, repo_names, shim_verbs, libexec_verbs)
            if verb:
                out[node.targets[0].id] = verb
    return out


def resolve_verb_element(elt: ast.expr, repo_names: set[str], shim_verbs: set[str],
                          libexec_verbs: set[str], verb_bindings: dict[str, str]) -> str | None:
    """Whether `elt` names this repo's own operator-verb path, direct or one hop of the
    module-constant convention. Returns the verb name only -- never a waiver-checkable node
    (finding 1: the caller waives at the USE site, never the binding)."""
    direct = names_repo_verb_join(elt, repo_names, shim_verbs, libexec_verbs)
    if direct:
        return direct
    unwrapped = _unwrap_str_call(elt)
    if isinstance(unwrapped, ast.Name) and unwrapped.id in verb_bindings:
        return verb_bindings[unwrapped.id]
    return None


def dispatcher_invocation_is_safe(elts: list[ast.expr], i: int, libexec_verbs: set[str]) -> bool:
    """Safe by the dispatcher's OWN branching: bare `autoharn`, `--help`/`-h`/`help` (returns
    before LIBEXEC), `service` (env-parameterized libexec/autoharn-service), or any non-relocated
    constant (refused before touching anything). Only a REAL verb constant, or a non-constant
    (a loop variable), is dangerous -- fail-safe: unknown stays flagged."""
    if i + 1 >= len(elts):
        return True
    s = _const_str(elts[i + 1])
    if s is None:
        return False
    if s in {"--help", "-h", "help", "service"}:
        return True
    return s not in libexec_verbs


class ListState:
    """Best-known state of a top-level Name bound to a List/Tuple, as of the LAST simulated
    mutation this module could follow. `elts is None` iff `opaque` -- a mutation happened that
    this module cannot prove the effect of (dynamic index, non-literal extend/insert, non-list
    `+=`)."""
    __slots__ = ("elts", "opaque", "sensitive")

    def __init__(self) -> None:
        self.elts: list[ast.expr] = []
        self.opaque = False
        self.sensitive = False  # ever carried a repo-verb-resolvable element


def _is_sensitive_elt(elt: ast.expr, repo_names: set[str], shim_verbs: set[str],
                       libexec_verbs: set[str], verb_bindings: dict[str, str]) -> bool:
    return resolve_verb_element(elt, repo_names, shim_verbs, libexec_verbs, verb_bindings) is not None


def simulate_list_states(tree: ast.Module, repo_names: set[str], shim_verbs: set[str],
                          libexec_verbs: set[str], verb_bindings: dict[str, str]
                          ) -> dict[str, ListState]:
    """Replays, in (lineno, col_offset) order, every top-level literal (re)binding,
    `.append`/`.insert`/`.extend`, subscript-assignment, `del`, and `+=` this module can follow
    for each Name, to approximate its FINAL element list (finding 2/4: a stale, pre-mutation
    snapshot is exactly the escape the prior round shipped). LINE-ORDER ONLY, no control-flow
    awareness -- see module docstring. A name that becomes opaque without ever being
    `sensitive` is DROPPED (not returned) -- an ordinary argv list this gate has no repo-verb
    interest in stays silent, same as before this fix."""
    events: list[tuple[int, int, str, str, object]] = []
    for node in ast.walk(tree):
        ln = getattr(node, "lineno", 0)
        col = getattr(node, "col_offset", 0)
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Name):
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    events.append((ln, col, "bind", t.id, list(node.value.elts)))
                else:
                    events.append((ln, col, "unbind", t.id, None))
            elif isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name):
                idx = _const_int(t.slice)
                events.append((ln, col, "sub_set" if idx is not None else "opaque",
                               t.value.id, (idx, node.value)))
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name) \
                and isinstance(node.op, ast.Add):
            if isinstance(node.value, (ast.List, ast.Tuple)):
                events.append((ln, col, "extend", node.target.id, list(node.value.elts)))
            else:
                events.append((ln, col, "opaque", node.target.id, None))
        elif isinstance(node, ast.Delete):
            for t in node.targets:
                if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name):
                    idx = _const_int(t.slice)
                    events.append((ln, col, "del" if idx is not None else "opaque", t.value.id, idx))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and isinstance(node.func.value, ast.Name) \
                and node.func.attr in ("append", "insert", "extend"):
            name = node.func.value.id
            if node.func.attr == "append" and node.args:
                events.append((ln, col, "append", name, node.args[0]))
            elif node.func.attr == "extend" and node.args:
                arg0 = node.args[0]
                if isinstance(arg0, (ast.List, ast.Tuple)):
                    events.append((ln, col, "extend", name, list(arg0.elts)))
                else:
                    events.append((ln, col, "opaque", name, None))
            elif node.func.attr == "insert" and len(node.args) >= 2:
                idx = _const_int(node.args[0])
                events.append((ln, col, "insert" if idx is not None else "opaque",
                                name, (idx, node.args[1])))
    events.sort(key=lambda e: (e[0], e[1]))

    states: dict[str, ListState] = {}

    def _mark_sensitive(name: str, elt: ast.expr) -> None:
        if name in states and _is_sensitive_elt(elt, repo_names, shim_verbs, libexec_verbs, verb_bindings):
            states[name].sensitive = True

    for ln, col, kind, name, payload in events:
        if kind == "bind":
            st = ListState()
            st.elts = list(payload)  # type: ignore[arg-type]
            states[name] = st
            for e in st.elts:
                _mark_sensitive(name, e)
        elif kind == "unbind":
            states.pop(name, None)
        elif kind == "opaque":
            states.setdefault(name, ListState()).opaque = True
            states[name].elts = []
        elif kind == "append":
            st = states.get(name)
            if st is not None and not st.opaque:
                st.elts.append(payload)  # type: ignore[arg-type]
                _mark_sensitive(name, payload)  # type: ignore[arg-type]
        elif kind == "extend":
            st = states.get(name)
            if st is not None and not st.opaque:
                st.elts.extend(payload)  # type: ignore[arg-type]
                for e in payload:  # type: ignore[union-attr]
                    _mark_sensitive(name, e)
        elif kind == "insert":
            st = states.get(name)
            idx, val = payload  # type: ignore[misc]
            if st is not None and not st.opaque and 0 <= idx <= len(st.elts):
                st.elts.insert(idx, val)
                _mark_sensitive(name, val)
        elif kind == "sub_set":
            st = states.get(name)
            idx, val = payload  # type: ignore[misc]
            if st is not None and not st.opaque and 0 <= idx < len(st.elts):
                st.elts[idx] = val
                _mark_sensitive(name, val)
            elif st is not None:
                st.opaque = True
                st.elts = []
        elif kind == "del":
            st = states.get(name)
            idx = payload
            if st is not None and not st.opaque and isinstance(idx, int) and 0 <= idx < len(st.elts):
                del st.elts[idx]
            elif st is not None:
                st.opaque = True
                st.elts = []

    return {name: st for name, st in states.items() if not st.opaque or st.sensitive}


def argv_elements(arg: ast.expr, list_states: dict[str, ListState]) -> tuple[list[ast.expr] | None, bool]:
    """`(elements, opaque_sensitive)` for one Call argument. `opaque_sensitive` True means: this
    was a repo-verb-bearing argv list at some point and was later mutated in a way this module
    cannot statically verify -- the caller should refuse it directly rather than trust stale
    elements (finding 2/4). Otherwise `elements` is the inline List/Tuple, the tracked Name's
    best-known contents, or None if `arg` isn't a list-ish expression this module tracks."""
    if isinstance(arg, (ast.List, ast.Tuple)):
        return list(arg.elts), False
    if isinstance(arg, ast.Name) and arg.id in list_states:
        st = list_states[arg.id]
        if st.opaque:
            return None, True
        return st.elts, False
    return None, False
