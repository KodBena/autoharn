#!/usr/bin/env python3
"""_pin_guard_argv.py -- per-Name binding/event bookkeeping and argv-Name resolution for
gates/fixture_deployment_pin_guard.py (ledger row 1249). Carries `NameFacts`/`analyze_names`/
`resolve_tracked_names`/`ArgvVerdict`/`argv_provenance` (moved verbatim out of
`_pin_guard_resolve.py` in fix-round 4 to keep every file under ADR-0007's 400-line ceiling once
this round's real findings added real code, not just prose) plus this round's own addition: a
`kinds` field on `NameFacts`/`ArgvVerdict` so an UNPROVEN verdict can name the actual construct
that contaminated it (a for-loop target, a walrus, ...), and a call out to
`_pin_guard_census.py`'s two sweeps from `analyze_names`' own pass. See
`gates/fixture_deployment_pin_guard.py`'s own POSTURE section for the round's full narrative, and
`_pin_guard_census.py`'s docstring for exactly what those two sweeps close.

THE CONTRACT (unchanged from fix-round 3): an argv is provable only in two shapes; everything
else that is ever SENSITIVE (an element resolves to one of this repo's own operator-verb paths
via `resolve_verb_element`) is UNPROVEN.
  1. A direct inline literal (List/Tuple) AT THE CALL SITE -- no Name involved.
  2. A Name bound EXACTLY ONCE to a literal List/Tuple, with ZERO other qualifying events
     anywhere in the file -- use that one binding's literal elements.
  3. Everything else sensitive: UNPROVEN, refused outright, never approximated.

Fix-round 4 widens the EVENT census (see `_pin_guard_census.py`) so a name is never silently
untouched for lack of a facts entry, but keeps the SAME sensitivity gate: a name that is never
found carrying a repo-verb element stays out of scope, unflagged, exactly as every prior round --
see `gates/fixture_deployment_pin_guard.py`'s own POSTURE section for the measured reason this
round does NOT additionally make the refusal decision sensitivity-independent at every spawn
call site (a real, measured false-positive class of ~75 files, not a hypothetical one)."""
from __future__ import annotations

import ast

from _pin_guard_census import sweep_binding_constructs, sweep_dynamic_mutators
from _pin_guard_resolve import resolve_verb_element

SUBPROCESS_CALL_ATTRS = {"run", "Popen", "check_call", "check_output", "call"}
_LIST_MUTATOR_METHODS = ("append", "insert", "extend", "remove", "pop", "sort", "reverse", "clear")


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
    List/Tuple binding, every element fed into it by a mutation, how many OTHER qualifying events
    (see module docstring) touched it, and (round 4) which CENSUS construct kinds, if any,
    contaminated it (`_pin_guard_census.py`). `alias_of` records `x = y` Name-to-Name assigns for
    `resolve_tracked_names`'s contamination step -- never "followed", only contaminates."""
    __slots__ = ("literal_bindings", "event_count", "payload_elts", "alias_of", "kinds")

    def __init__(self) -> None:
        self.literal_bindings: list[list[ast.expr]] = []
        self.event_count = 0
        self.payload_elts: list[ast.expr] = []
        self.alias_of: set[str] = set()
        self.kinds: set[str] = set()


def analyze_names(tree: ast.Module) -> dict[str, NameFacts]:
    """One scope-blind pass collecting, per top-level Name, every literal binding and every OTHER
    qualifying event (see module docstring). No line-order, no control-flow, no replay:
    provability (`resolve_tracked_names`) depends only on COUNTS and SET MEMBERSHIP here, never on
    where in the file something sits relative to something else. Round 4 adds two sweeps
    (`_pin_guard_census.py`) so a binding shape this pass does not itself model directly --
    chained assign, tuple/list-unpack, for-target, walrus, with-as, except-as, annotated-assign,
    comprehension target, `getattr(cmd, "append")(...)`, `globals()["cmd"].append(...)` -- is
    never left with NO facts entry at all (round-3's blind spot, lap-4 findings 1-3/5)."""
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

    # round 4 (rule A / finding 5): binding shapes this pass does not model directly -- see
    # _pin_guard_census.py's own docstring for exactly what each sweep closes.
    sweep_binding_constructs(tree, get)
    sweep_dynamic_mutators(tree, get)

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
    `unproven` is False, else always None -- no partial/stale fallback by construction. `kinds`
    (round 4) carries any census construct names (see `_pin_guard_census.py`) that contaminated
    this name or one of its alias-mates, for the refusal message."""
    __slots__ = ("elts", "unproven", "kinds")

    def __init__(self, elts: list[ast.expr] | None, unproven: bool, kinds: set[str]) -> None:
        self.elts = elts
        self.unproven = unproven
        self.kinds = kinds


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
        kinds: set[str] = set()
        for m in members:
            f = facts.get(m)
            if f is None:
                continue
            for binding in f.literal_bindings:
                elements.extend(binding)
            elements.extend(f.payload_elts)
            kinds |= f.kinds
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
        verdict = ArgvVerdict(elts=list(facts[members[0]].literal_bindings[0]), unproven=False,
                              kinds=kinds) \
            if provable else ArgvVerdict(elts=None, unproven=True, kinds=kinds)
        for m in members:
            out[m] = verdict

    return out


def argv_provenance(arg: ast.expr, tracked: dict[str, ArgvVerdict]
                     ) -> tuple[list[ast.expr] | None, bool, set[str]]:
    """`(elements, unproven, kinds)` for one Call argument. `unproven` True means: this name is
    repo-verb-bearing at some point in the file and this module cannot prove its argv dataflow
    safe -- the caller must refuse outright, never approximate. `kinds` names the census
    constructs (if any) that contaminated it, for the refusal message. Otherwise `elements` is the
    inline List/Tuple, a fully-provable Name's one literal binding, or None if `arg` is neither
    (an ordinary call argument, or a Name this module has no sensitive interest in)."""
    if isinstance(arg, (ast.List, ast.Tuple)):
        return list(arg.elts), False, set()
    if isinstance(arg, ast.Name) and arg.id in tracked:
        v = tracked[arg.id]
        if v.unproven:
            return None, True, v.kinds
        return v.elts, False, set()
    return None, False, set()
