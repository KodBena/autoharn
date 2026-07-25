#!/usr/bin/env python3
"""_pin_guard_census.py -- CENSUS FAIL-CLOSED sweep for gates/fixture_deployment_pin_guard.py
(ledger row 1249, fix-round 4; see that file's own POSTURE section for the round's full
narrative). Split out from `_pin_guard_argv.py` to keep every file under ADR-0007's 400-line
ceiling once this round's real code (not just prose) landed.

THE RULE THIS MODULE IMPLEMENTS (round 4, rule A): `_pin_guard_argv.py`'s `analyze_names` only
ever modeled a handful of binding shapes precisely (plain `NAME = <list-literal-or-other>`, a
single Subscript-assign, AugAssign, Delete, and a handful of list-mutator method calls). Every
OTHER assignment-like binding construct in the language was invisible: no facts entry was ever
created for the names such a construct binds, so a verb path smuggled in through one of these
shapes was never even a candidate for flagging (lap-4 findings 1-3, witnessed four times running
across this arc): chained assign (`x = y = [...]`), tuple/list-unpacking (`a, b = ...`, including
a plain swap `a, b = b, a`), a `for` target, a walrus (`:=`), a `with ... as`, an `except ... as`,
an annotated assign, and a comprehension's own loop target.

This module sweeps every one of those shapes and, for every Name it binds, ALWAYS marks it
disqualified (`event_count += 1`, plus the construct's own name recorded in `kinds` so a refusal
can name it) and captures whatever the construct's right-hand side/iterable/context-expression
spells as a payload element -- never leaving a name silently untouched the way it used to be. A
name touched by one of these shapes can still turn out completely innocuous (an ordinary loop
variable that never carries a verb path) -- that stays unflagged, same as any other name that is
never sensitive -- but it is never again SKIPPED for lack of a facts entry. "Unknown never means
invisible; unknown means unproven" (round 4's own words).

Also carries the two dynamic-mutator shapes from finding 5 (`getattr(cmd, "append")(...)` and
`globals()["cmd"].append(...)`) -- neither is the `Name.method(...)` Attribute-Call shape
`analyze_names`'s own mutator sweep expects, so both were completely invisible: the first used to
fire some OTHER generic event against `cmd` (from the bare-Name-argument sweep) but never
recorded the appended element itself, silently dropping a never-otherwise-sensitive element before
the provable/unproven branch ever got to look at it; the second recorded no event on any tracked
Name at all (there is no `Name` node spelling `cmd` at the mutation site). Same treatment:
contaminate + capture, this time keyed by the string literal naming the global (which lines up
with that name's own module-level facts entry, tracked separately by `analyze_names`' first pass).

Every function here takes the already-parsed tree and a `get: GetFacts` accessor -- the exact
closure `analyze_names` builds over its own `facts` dict, passed in rather than duplicated -- so
this module carries no facts store of its own and no knowledge of union-find/provability (that
stays `_pin_guard_argv.py`'s job)."""
from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:  # exempt from the lazy-import ban (zero runtime cost); avoids the real circular
    from _pin_guard_argv import NameFacts  # import -- _pin_guard_argv imports this module's sweeps.

GetFacts = Callable[[str], "NameFacts"]

_LIST_MUTATOR_METHODS = ("append", "insert", "extend", "remove", "pop", "sort", "reverse", "clear")


def _names_in_target(target: ast.expr) -> list[str]:
    """Every bare Name id bound anywhere inside `target`, recursing through Tuple/List/Starred
    (tuple/list-unpacking, including a swap `a, b = b, a`) -- a Subscript/Attribute target binds
    no NEW Name of its own and contributes nothing here (it mutates a container/object, already
    tracked by `analyze_names`' own Subscript-assign case)."""
    names: list[str] = []
    if isinstance(target, ast.Name):
        names.append(target.id)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            names.extend(_names_in_target(elt))
    elif isinstance(target, ast.Starred):
        names.extend(_names_in_target(target.value))
    return names


def _contaminate(get: GetFacts, names: list[str], value: ast.expr | None, kind: str) -> None:
    """Mark every name in `names` disqualified (event + `kind` recorded) and, when `value` is
    given, capture its constituent candidate expression(s) -- the whole element list if `value`
    is itself a List/Tuple, else `value` alone as one candidate. A candidate that is itself a bare
    Name (other than the target being contaminated) is recorded as an ALIAS, not a payload
    element -- this is what makes a tuple-swap (`a, b = b, a`) sound: `a`'s own analysis must
    account for `a` now possibly holding whatever `b` could hold, which plain payload-copying
    cannot express (a Name isn't itself a verb-shaped expression `resolve_verb_element` would ever
    match) but the union-find alias step in `resolve_tracked_names` can. Every other candidate
    (a literal, a `str(REPO / ...)` call, ...) is captured as an ordinary payload element, exactly
    as before."""
    for name in names:
        f = get(name)
        f.event_count += 1
        f.kinds.add(kind)
        if value is None:
            continue
        candidates = value.elts if isinstance(value, (ast.List, ast.Tuple)) else [value]
        for c in candidates:
            if isinstance(c, ast.Name) and c.id != name:
                f.alias_of.add(c.id)
            else:
                f.payload_elts.append(c)


def sweep_binding_constructs(tree: ast.Module, get: GetFacts) -> None:
    """Findings 1-3: chained assign, tuple/list-unpack (incl. swap), for-target, walrus, with-as,
    except-as, annotated-assign, comprehension target -- each contaminates every Name it binds."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if len(node.targets) > 1:  # chained: x = y = [...]
                for t in node.targets:
                    _contaminate(get, _names_in_target(t), node.value, "chained-assign")
            else:
                t = node.targets[0]
                if isinstance(t, (ast.Tuple, ast.List)):  # a, b = ...  (incl. a, b = b, a)
                    _contaminate(get, _names_in_target(t), node.value, "tuple-unpack")
                # plain Name / Subscript(Name) targets: analyze_names' own first pass handles those.
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            _contaminate(get, _names_in_target(node.target), node.value, "annotated-assign")
        elif isinstance(node, ast.NamedExpr):  # walrus: (cmd := [...])
            _contaminate(get, _names_in_target(node.target), node.value, "walrus")
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            _contaminate(get, _names_in_target(node.target), node.iter, "for-target")
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars is not None:
                    _contaminate(get, _names_in_target(item.optional_vars), item.context_expr,
                                 "with-as")
        elif isinstance(node, ast.ExceptHandler) and node.name:
            _contaminate(get, [node.name], None, "except-as")
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            for gen in node.generators:
                _contaminate(get, _names_in_target(gen.target), gen.iter, "comprehension-target")


def _mutator_method_from_getattr(node: ast.Call) -> tuple[str, str] | None:
    """`getattr(cmd, "append")(...)` -> `("cmd", "append")` iff the method named is one of the
    list-mutator methods; None otherwise (finding 5, the generic-event-no-payload half)."""
    f = node.func
    if not (isinstance(f, ast.Call) and isinstance(f.func, ast.Name) and f.func.id == "getattr"
            and len(f.args) >= 2 and isinstance(f.args[0], ast.Name)):
        return None
    method = f.args[1].value if isinstance(f.args[1], ast.Constant) \
        and isinstance(f.args[1].value, str) else None
    if method not in _LIST_MUTATOR_METHODS:
        return None
    return f.args[0].id, method


def _mutator_method_from_globals(node: ast.Call) -> tuple[str, str] | None:
    """`globals()["cmd"].append(...)` -> `("cmd", "append")` -- finding 5's zero-event half: no
    Name node spells `cmd` anywhere at the mutation site, so it needs its own detection, keyed by
    the string literal (lining up with `cmd`'s own module-level facts entry, if any)."""
    f = node.func
    if not (isinstance(f, ast.Attribute) and f.attr in _LIST_MUTATOR_METHODS):
        return None
    base = f.value
    if not (isinstance(base, ast.Subscript) and isinstance(base.value, ast.Call)
            and isinstance(base.value.func, ast.Name) and base.value.func.id == "globals"):
        return None
    key = base.slice
    name = key.value if isinstance(key, ast.Constant) and isinstance(key.value, str) else None
    return (name, f.attr) if name else None


def sweep_dynamic_mutators(tree: ast.Module, get: GetFacts) -> None:
    """Finding 5: `getattr(cmd, "append")(...)` and `globals()["cmd"].append(...)` -- neither is
    the `Name.method(...)` Attribute-Call shape `analyze_names`'s own mutator sweep recognizes."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        hit = _mutator_method_from_getattr(node) or _mutator_method_from_globals(node)
        if hit is None:
            continue
        name, method = hit
        f = get(name)
        f.event_count += 1
        f.kinds.add("dynamic-mutator")
        if method == "append" and node.args:
            f.payload_elts.append(node.args[0])
        elif method == "insert" and len(node.args) >= 2:
            f.payload_elts.append(node.args[1])
        elif method == "extend" and node.args:
            arg0 = node.args[0]
            if isinstance(arg0, (ast.List, ast.Tuple)):
                f.payload_elts.extend(arg0.elts)
            else:
                f.payload_elts.append(arg0)
        # remove/pop/sort/reverse/clear: no reconstructible payload, same as analyze_names' own
        # mutator sweep -- the event_count bump above is what matters.
