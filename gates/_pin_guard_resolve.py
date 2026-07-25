#!/usr/bin/env python3
"""_pin_guard_resolve.py -- pure-AST binding/argv resolution helpers for
gates/fixture_deployment_pin_guard.py (split out, ledger row 1249 fix-round 2; fix-round 3
replaces the fix-round-2 replay engine with a PROVE-OR-REFUSE inversion -- see that file's own
POSTURE section for the full narrative/history). No I/O, no printing, no subprocess calls of its
own -- every function here takes an already-parsed `ast.Module` (or a piece of one) and returns a
resolution, never a verdict string; `fixture_deployment_pin_guard.py` owns all message text and
orchestration, this module owns only "what does this expression spell" and "is this argv
dataflow provable".

THE CONTRACT this module implements: an argv is provable only in two shapes; everything else that
is ever SENSITIVE (an element resolves to one of this repo's own operator-verb paths via
`resolve_verb_element`, see `resolve_tracked_names`) is UNPROVEN.
  1. A direct inline literal (List/Tuple) AT THE CALL SITE -- no Name involved, analyzed exactly
     as in prior rounds (`fixture_deployment_pin_guard.py`'s own CHECK 1 handles this shape).
  2. A Name bound EXACTLY ONCE to a literal List/Tuple, with ZERO other qualifying events (see
     `analyze_names`) anywhere in the file -- use that one binding's literal elements.
  3. Everything else sensitive: UNPROVEN, refused outright, never approximated from a partial or
     stale reconstruction.

A name that is NEVER sensitive (an ordinary git/psql argv list with a dynamic flag) stays
completely out of scope, unflagged -- same as every prior round.

"ZERO other events" is RAW and CONSERVATIVE, scope-blind by design (no control-flow, no
line-order, no replay -- there is nothing left to get the ORDER of wrong, closing round-2's
findings C/D and the round-3 commission's findings A/B; see `analyze_names`'s own docstring for
the exact event list: more-than-one literal binding, a non-literal rebind, any list-mutating
method call, any subscript/slice assignment or `del`, `+=`, an ALIAS (`x = y`, either direction --
CONTAMINATES rather than follows: if either name is ever sensitive, BOTH come back unproven), or
being passed as a bare Name argument to any call other than the argv-sink call itself (a wrapper
this module cannot see inside of is exactly the hazard, not the use site).

WHAT THIS MODULE STILL DOES NOT CLAIM:
  - Only ONE hop of Name-binding indirection is resolved for the verb-path CONSTANT convention
    (`verb_path_bindings`); a constant imported from another module (`from helper import LED`)
    is invisible -- single-file AST census, stops at the file boundary by construction.
  - A path/argv that never appears as a literal or tracked list in this file (behind a function
    parameter with no local binding, built by string formatting this module doesn't parse, held
    in a dict/attribute rather than a bare Name) has no elements to inspect and so cannot be
    judged sensitive -- stays silently out of scope, same blind spot every prior round carried.
"""
from __future__ import annotations

import ast

REPO_LIKE_NAMES = {"REPO", "AUTOHARN_ROOT", "EXEC_ROOT", "REPO_ROOT"}
SUBPROCESS_CALL_ATTRS = {"run", "Popen", "check_call", "check_output", "call"}
_LIST_MUTATOR_METHODS = ("append", "insert", "extend", "remove", "pop", "sort", "reverse", "clear")


def _const_str(node: ast.expr | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


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


def is_argv_sink_call(node: ast.Call) -> bool:
    """A call whose argv-carrying argument IS the use site CHECK 1 judges (`os.system`, or a
    `SUBPROCESS_CALL_ATTRS` name/attribute call) -- passing a tracked name INTO this kind of call
    is not an event against it; every OTHER call it's passed into counts (wrapper-indirection)."""
    f = node.func
    if isinstance(f, ast.Attribute) and f.attr == "system" and isinstance(f.value, ast.Name) \
            and f.value.id == "os":
        return True
    return (isinstance(f, ast.Attribute) and f.attr in SUBPROCESS_CALL_ATTRS) \
        or (isinstance(f, ast.Name) and f.id in SUBPROCESS_CALL_ATTRS)


class NameFacts:
    """Scope-blind facts about one top-level Name that might be an argv list: every literal
    List/Tuple binding, every element fed into it by a mutation, and how many OTHER qualifying
    events (see module docstring) touched it. `alias_of` records `x = y` Name-to-Name assigns for
    `resolve_tracked_names`'s contamination step -- never "followed", only contaminates."""
    __slots__ = ("literal_bindings", "event_count", "payload_elts", "alias_of")

    def __init__(self) -> None:
        self.literal_bindings: list[list[ast.expr]] = []
        self.event_count = 0
        self.payload_elts: list[ast.expr] = []
        self.alias_of: set[str] = set()


def analyze_names(tree: ast.Module) -> dict[str, NameFacts]:
    """One scope-blind pass collecting, per top-level Name, every literal binding and every OTHER
    qualifying event (see module docstring). No line-order, no control-flow, no replay: provability
    (`resolve_tracked_names`) depends only on COUNTS and SET MEMBERSHIP here, never on where in
    the file something sits relative to something else."""
    facts: dict[str, NameFacts] = {}

    def get(name: str) -> NameFacts:
        return facts.setdefault(name, NameFacts())

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Name):
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    get(t.id).literal_bindings.append(list(node.value.elts))
                elif isinstance(node.value, ast.Name):
                    f = get(t.id)
                    f.alias_of.add(node.value.id)
                    f.event_count += 1
                else:
                    get(t.id).event_count += 1
            elif isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name):
                f = get(t.value.id)
                f.event_count += 1
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    f.payload_elts.extend(node.value.elts)
                else:
                    f.payload_elts.append(node.value)
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            f = get(node.target.id)
            f.event_count += 1
            if isinstance(node.value, (ast.List, ast.Tuple)):
                f.payload_elts.extend(node.value.elts)
            else:
                f.payload_elts.append(node.value)
        elif isinstance(node, ast.Delete):
            for t in node.targets:
                if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name):
                    get(t.value.id).event_count += 1
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and isinstance(node.func.value, ast.Name) \
                and node.func.attr in _LIST_MUTATOR_METHODS:
            f = get(node.func.value.id)
            f.event_count += 1
            if node.func.attr == "append" and node.args:
                f.payload_elts.append(node.args[0])
            elif node.func.attr == "insert" and len(node.args) >= 2:
                f.payload_elts.append(node.args[1])
            elif node.func.attr == "extend" and node.args:
                arg0 = node.args[0]
                if isinstance(arg0, (ast.List, ast.Tuple)):
                    f.payload_elts.extend(arg0.elts)
                else:
                    f.payload_elts.append(arg0)
            # remove/pop/sort/reverse/clear: no reconstructible payload, the event_count bump
            # above is what matters -- these can delete or reorder a sensitive element in place.

    # "passed as a bare argument to a call this module cannot see inside" -- everywhere except
    # the argv-sink call itself (that call IS the use site, not a mutation of its argument).
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or is_argv_sink_call(node):
            continue
        for a in list(node.args) + [kw.value for kw in node.keywords]:
            if isinstance(a, ast.Name):
                get(a.id).event_count += 1

    return facts


class ArgvVerdict:
    """Resolution for one tracked, SENSITIVE Name: `elts` is the provable literal list when
    `unproven` is False, else always None -- no partial/stale fallback by construction."""
    __slots__ = ("elts", "unproven")

    def __init__(self, elts: list[ast.expr] | None, unproven: bool) -> None:
        self.elts = elts
        self.unproven = unproven


def resolve_tracked_names(tree: ast.Module, repo_names: set[str], shim_verbs: set[str],
                           libexec_verbs: set[str], verb_bindings: dict[str, str]
                           ) -> dict[str, ArgvVerdict]:
    """Per Name (only SENSITIVE names appear here -- see module docstring): PROVABLE (case 2)
    iff exactly one literal binding, no alias, zero other qualifying events anywhere in the file
    -- then `elts` is that one binding. Otherwise UNPROVEN. Aliasing (`x = y`) merges `x`/`y`
    into one component: if EITHER is ever sensitive, BOTH come back unproven regardless of either
    one's own local event count (closes the one-hop-alias finding)."""
    facts = analyze_names(tree)

    parent: dict[str, str] = {name: name for name in facts}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for name, f in list(facts.items()):
        for other in f.alias_of:
            if other not in parent:
                parent[other] = other
                facts.setdefault(other, NameFacts())
            union(name, other)

    components: dict[str, list[str]] = {}
    for name in parent:
        components.setdefault(find(name), []).append(name)

    out: dict[str, ArgvVerdict] = {}
    for members in components.values():
        elements: list[ast.expr] = []
        for m in members:
            f = facts.get(m)
            if f is None:
                continue
            for binding in f.literal_bindings:
                elements.extend(binding)
            elements.extend(f.payload_elts)
        sensitive = any(
            resolve_verb_element(e, repo_names, shim_verbs, libexec_verbs, verb_bindings) is not None
            for e in elements
        )
        if not sensitive:
            continue
        provable = len(members) == 1
        if provable:
            only_facts = facts[members[0]]
            provable = len(only_facts.literal_bindings) == 1 and only_facts.event_count == 0
        verdict = ArgvVerdict(elts=list(facts[members[0]].literal_bindings[0]), unproven=False) \
            if provable else ArgvVerdict(elts=None, unproven=True)
        for m in members:
            out[m] = verdict

    return out


def argv_provenance(arg: ast.expr, tracked: dict[str, ArgvVerdict]) -> tuple[list[ast.expr] | None, bool]:
    """`(elements, unproven)` for one Call argument. `unproven` True means: this name is
    repo-verb-bearing at some point in the file and this module cannot prove its argv dataflow
    safe -- the caller must refuse outright, never approximate. Otherwise `elements` is the
    inline List/Tuple, a fully-provable Name's one literal binding, or None if `arg` is neither
    (an ordinary call argument, or a Name this module has no sensitive interest in)."""
    if isinstance(arg, (ast.List, ast.Tuple)):
        return list(arg.elts), False
    if isinstance(arg, ast.Name) and arg.id in tracked:
        v = tracked[arg.id]
        if v.unproven:
            return None, True
        return v.elts, False
    return None, False
