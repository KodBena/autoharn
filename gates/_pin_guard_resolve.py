#!/usr/bin/env python3
"""_pin_guard_resolve.py -- pure-AST verb-path resolution helpers for
gates/fixture_deployment_pin_guard.py (ledger row 1249). No I/O, no printing, no subprocess calls
of its own -- every function here takes an already-parsed `ast.Module` (or a piece of one) and
returns a resolution, never a verdict string; `fixture_deployment_pin_guard.py` owns all message
text and orchestration, this module owns only "what does this expression spell" (a repo-verb path,
or not). Per-Name binding/event bookkeeping and argv-Name provability (`NameFacts`/
`analyze_names`/`resolve_tracked_names`/`argv_provenance`) moved to `_pin_guard_argv.py` in
fix-round 4 to keep this file under ADR-0007's 400-line ceiling once that round's findings added
real code, not just prose; the census sweep those findings needed lives in `_pin_guard_census.py`.
See `gates/fixture_deployment_pin_guard.py`'s own POSTURE section for the full round-by-round
narrative.

FIX-ROUND 4 additions to THIS file (finding 7, inline-literal element misses -- verb-DETECTION
fixes, not blind refusals):
  - `names_repo_verb_join`'s JoinedStr (f-string) branch now unwraps a `str(REPO)` call inside a
    `FormattedValue` the same way every other shape here already unwraps `str(...)` -- an f-string
    spelling `f"{str(REPO)}/led"` used to be invisible (only a bare `{REPO}` was recognized).
  - `_peel_join_chain`'s RIGHTMOST (tail) hop -- the one closest to the verb name in a `/`-BinOp
    chain -- now also accepts an `IfExp` (`REPO / (a if flag else "led")`) or a `+`-concat of two
    constants (`REPO / ("le" + "d")`) instead of only a bare string constant; every candidate tail
    string is tried against the verb roster. Earlier (non-tail) hops are unaffected -- still plain
    constants only, since a repo-verb path's DIRECTORY segments (`legacy/`, `libexec/autoharn/`)
    are never spelled conditionally in this corpus (measured, see the gate's own MEASUREMENT
    table) and widening every hop would cost combinatorial complexity for zero observed benefit.
  - `bare_verb_literal` (new): a bare string constant argv[0] -- `"led"`, `"./led"`, `"/led"` --
    naming this repo's own verb roster WITHOUT any `REPO`-path join at all (finding 4: the leak
    class's most literal spelling, invisible to every prior round because every prior round only
    ever looked for a REPO-rooted PATH, never a bare verb NAME relying on `cwd`/`PATH` resolution).
    Deliberately does NOT try to prove or disprove `cwd` -- see the gate's own POSTURE section for
    why, and for the one real, legitimate collision this measured against the real tree (a
    scaffolded-scratch-destination `cwd`, waived at its two call sites, not redesigned around)."""
from __future__ import annotations

import ast
import re

REPO_LIKE_NAMES = {"REPO", "AUTOHARN_ROOT", "EXEC_ROOT", "REPO_ROOT"}


def _const_str(node: ast.expr | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _unwrap_str_call(node: ast.expr) -> ast.expr:  # `str(X)` -> `X`
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "str" \
            and len(node.args) == 1:
        return node.args[0]
    return node


def _const_str_candidates(node: ast.expr | None) -> list[str] | None:
    """Every string this expression could statically resolve to: a plain constant (one
    candidate), an `IfExp` (both branches' candidates, recursively), or a `+`-concat of two plain
    constants (one candidate: their join) -- finding 7's IfExp/concat tail fix. None if `node`
    resolves to no string at all (an opaque expression, e.g. a Name or Call)."""
    s = _const_str(node)
    if s is not None:
        return [s]
    if isinstance(node, ast.IfExp):
        body = _const_str_candidates(node.body)
        orelse = _const_str_candidates(node.orelse)
        if body is None and orelse is None:
            return None
        return (body or []) + (orelse or [])
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _const_str(node.left), _const_str(node.right)
        if left is not None and right is not None:
            return [left + right]
    return None


def repo_join_targets(tree: ast.Module) -> set[str]:  # top-level names bound to a REPO-like Path
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id in REPO_LIKE_NAMES:
            bound.add(node.targets[0].id)
    return bound


def repo_like_or_default(tree: ast.Module) -> set[str]:
    return repo_join_targets(tree) or set(REPO_LIKE_NAMES)


def _peel_join_chain(node: ast.expr, repo_names: set[str]) -> list[list[str]] | None:
    """Peels a `<expr> / "<component>"` BinOp chain to its ordered components iff the base is a
    bare Name in `repo_names`; every hop except the TAIL (rightmost, closest to the verb name)
    must be a plain string constant, the tail may resolve to several candidate strings (finding
    7). Returns a list of PER-HOP candidate lists (each non-tail hop a singleton), or None if the
    base doesn't match or any non-tail hop isn't a plain constant."""
    hops: list[list[str]] = []
    cur = node
    is_tail = True  # the first hop peeled is the rightmost/tail-most segment
    while isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.Div):
        if is_tail:
            candidates = _const_str_candidates(cur.right)
            is_tail = False
        else:
            single = _const_str(cur.right)
            candidates = [single] if single is not None else None
        if candidates is None:
            return None
        hops.append(candidates)
        cur = cur.left
    if isinstance(cur, ast.Name) and cur.id in repo_names:
        hops.reverse()
        return hops
    return None


def _wrap_hops(parts: list[str] | None) -> list[list[str]] | None:
    """Adapts the flat `list[str]` shape `_os_path_join_parts`/`_joinpath_parts` return (every hop
    a single plain constant, no IfExp/concat tail there -- `os.path.join`/`.joinpath` calls are
    not observed to spell a verb conditionally anywhere in this corpus) to the per-hop
    candidate-list shape `_verb_from_join_parts` expects."""
    return None if parts is None else [[p] for p in parts]


def _verb_from_join_parts(hops: list[list[str]] | None, shim_verbs: set[str],
                           libexec_verbs: set[str]) -> str | None:
    """Which operator-verb shape `hops` spells: `<verb>`/`legacy/<verb>` (vs `shim_verbs`) or
    `libexec/autoharn/<verb>` (vs `libexec_verbs`) -- None otherwise (e.g. the SAFE `.tmpl` shape,
    or `hops is None`). Tries every candidate string at each hop position (finding 7: usually only
    the last hop has more than one candidate)."""
    if hops is None:
        return None
    if len(hops) == 1:
        for c in hops[0]:
            if c in shim_verbs:
                return c
        return None
    if len(hops) == 2:
        if hops[0] == ["legacy"]:
            for c in hops[1]:
                if c in shim_verbs:
                    return c
        return None
    if len(hops) == 3 and hops[0] == ["libexec"] and hops[1] == ["autoharn"]:
        for c in hops[2]:
            if c in libexec_verbs:
                return c
        return None
    return None


def _os_path_join_parts(node: ast.Call, repo_names: set[str]) -> list[str] | None:
    """`os.path.join(REPO, "a", "b")` (or `os.path.join(str(REPO), ...)`) -> `["a","b"]`; None if not that shape."""
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
    """`REPO.joinpath("a", "b")` (or `str(REPO).joinpath(...)`) -> `["a","b"]`; None otherwise."""
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
            if isinstance(part, ast.FormattedValue):
                inner = _unwrap_str_call(part.value)  # f"{str(REPO)}/..." (finding 7a)
                if isinstance(inner, ast.Name) and inner.id in repo_names and i + 1 < len(node.values):
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
        return _verb_from_join_parts(_wrap_hops(_os_path_join_parts(node, repo_names)),
                                      shim_verbs, libexec_verbs) \
            or _verb_from_join_parts(_wrap_hops(_joinpath_parts(node, repo_names)),
                                      shim_verbs, libexec_verbs)
    return None


def verb_path_bindings(tree: ast.Module, repo_names: set[str], shim_verbs: set[str],
                        libexec_verbs: set[str]) -> dict[str, str]:
    """Name -> verb per top-level `NAME = <repo-verb-join-expr>` binding (the DOMINANT
    convention: LED_TMPL/ATTEST_TAGS/AUTOHARN). Deliberately NOT keyed to the defining Assign
    node -- callers check waivers only at the USE site, never a constant's binding line."""
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
    (the caller waives at the USE site, never the binding)."""
    direct = names_repo_verb_join(elt, repo_names, shim_verbs, libexec_verbs)
    if direct:
        return direct
    unwrapped = _unwrap_str_call(elt)
    if isinstance(unwrapped, ast.Name) and unwrapped.id in verb_bindings:
        return verb_bindings[unwrapped.id]
    return None


_BARE_VERB_RE_CACHE: dict[frozenset[str], "re.Pattern[str]"] = {}


def bare_verb_literal(elt: ast.expr, position: int, shim_verbs: set[str]) -> str | None:
    """Finding 4: a BARE string constant argv[0] -- `"led"`, `"./led"`, `"/led"` -- spelling one
    of this repo's own root-level verb shims (or the `autoharn` dispatcher) with NO `REPO`-path
    join anywhere in sight. Only checked at `position == 0` (a verb name appearing elsewhere in an
    argv is an ordinary subcommand argument, not a callee) and only against `shim_verbs` (the
    root-shim/dispatcher roster -- `libexec/autoharn/<verb>` is never invoked bare, only via its
    full repo-rooted path, so `libexec_verbs` is not part of this check). Deliberately does NOT
    look at a `cwd=` kwarg on the enclosing call -- see the gate's own POSTURE section for why."""
    if position != 0 or not isinstance(elt, ast.Constant) or not isinstance(elt.value, str):
        return None
    key = frozenset(shim_verbs)
    pattern = _BARE_VERB_RE_CACHE.get(key)
    if pattern is None:
        alts = "|".join(re.escape(v) for v in shim_verbs)
        pattern = re.compile(rf"\.?/?({alts})$") if alts else re.compile(r"(?!)")
        _BARE_VERB_RE_CACHE[key] = pattern
    m = pattern.fullmatch(elt.value)
    return m.group(1) if m else None


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
