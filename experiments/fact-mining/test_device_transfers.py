#!/usr/bin/env python
"""Single-homed device-transfer gate for the fact-mining daemon (pure `ast`).

Discipline ported from chocofarm's tests/test_no_gratuitous_transfers.py — but
SCALED DOWN deliberately (see "Proportionality" below). The property: every
CPU<->GPU boundary op (torch device placement / dtype casts, spaCy GPU enable,
maverick GPU placement) lives in ONE auditable home — `nlp_server.py` — and
carries an inline `# host-device-boundary: <reason>` marker. A device op that
appears in any other module, or in nlp_server.py without the marker, reds here.

Why this matters: scattered/unannotated device transfers are how redundant
host<->device crossings creep in unnoticed. Single-homing them makes the whole
device edge reviewable in one file and one grep.

Proportionality (the chocofarm ratchet was NOT ported, on purpose): chocofarm
guards a measured hot path across many modules with a ~500-line checker + a
monotonic JSON baseline + a device-signal heuristic. Here the entire torch
device boundary is THREE sites in ONE function (`Server.coref` / `__init__`), so
a baseline ratchet and a false-positive heuristic would be ceremony. Falsifiable
kill-condition for that choice: if device ops ever legitimately spread beyond
nlp_server.py, replace this positive assertion with chocofarm's baseline ratchet.

Vendored third-party code (maverick, spaCy) is OUT OF SCOPE — its internal
`.to(device)` / `.cpu()` transfers are ones we can neither annotate nor fix, and
baselining them would be exactly the cargo-cult net chocofarm warns against.

Runs under `pytest`, or standalone: `python test_device_transfers.py`.
"""

from __future__ import annotations

import ast
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SINGLE_HOME = "nlp_server.py"            # the only module allowed device ops
MARKER = "# host-device-boundary:"       # inline opt-in, same convention as chocofarm
SCANNED = ["extract.py", "load_facts.py", "nlp_cache.py",
           "nlp_client.py", "nlp_server.py", "resolve.py"]

# Closed token set — the torch/spaCy device-edge ops actually reachable in this
# code. Method calls (`x.to(...)`, `m.float()`, ...) and the bare GPU-enable
# calls. Deliberately name-based and conservative; no device-signal heuristic.
DEVICE_METHODS = {"to", "cuda", "cpu", "half", "float", "autocast"}
DEVICE_FUNCS = {"require_gpu", "prefer_gpu"}


class _DeviceVisitor(ast.NodeVisitor):
    def __init__(self, relpath: str):
        self.relpath = relpath
        self.found: list[tuple[str, int, str]] = []  # (relpath, lineno, token)

    def visit_Call(self, node: ast.Call):
        f = node.func
        # `x.to(...)`, `m.float()`, AND `spacy.require_gpu()` are all attribute calls
        if isinstance(f, ast.Attribute) and f.attr in (DEVICE_METHODS | DEVICE_FUNCS):
            self.found.append((self.relpath, node.lineno, f".{f.attr}()"))
        # bare `require_gpu()` (e.g. `from spacy import require_gpu`)
        elif isinstance(f, ast.Name) and f.id in DEVICE_FUNCS:
            self.found.append((self.relpath, node.lineno, f"{f.id}()"))
        elif _is_maverick_device_ctor(node):
            self.found.append((self.relpath, node.lineno, "Maverick(device=...)"))
        self.generic_visit(node)


def _is_maverick_device_ctor(node: ast.Call) -> bool:
    name = node.func.id if isinstance(node.func, ast.Name) else (
        node.func.attr if isinstance(node.func, ast.Attribute) else None)
    return name == "Maverick" and any(k.arg == "device" for k in node.keywords)


def find_device_ops(src: str, relpath: str) -> list[tuple[str, int, str]]:
    v = _DeviceVisitor(relpath)
    v.visit(ast.parse(src))
    return v.found


def is_sanctioned(hit: tuple[str, int, str], src_lines: list[str]) -> bool:
    """A device op is allowed iff it is in SINGLE_HOME and its line carries MARKER."""
    relpath, lineno, _ = hit
    if relpath != SINGLE_HOME:
        return False
    return MARKER in src_lines[lineno - 1]


def _scan_real_tree() -> list[str]:
    violations = []
    for name in SCANNED:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            continue
        src = open(path, encoding="utf-8").read()
        lines = src.splitlines()
        for hit in find_device_ops(src, name):
            if not is_sanctioned(hit, lines):
                relpath, lineno, token = hit
                why = ("not in nlp_server.py" if relpath != SINGLE_HOME
                       else "missing inline `# host-device-boundary:` marker")
                violations.append(f"{relpath}:{lineno} {token} — {why}")
    return violations


# ===================================================================== the gate
def test_device_ops_are_single_homed_and_marked():
    """Every device-edge op in our code is in nlp_server.py with a boundary marker."""
    violations = _scan_real_tree()
    assert not violations, (
        "un-single-homed / unmarked device transfer(s) — move to nlp_server.py and "
        "add an inline `# host-device-boundary: <reason>`:\n  " + "\n  ".join(violations))


# ============================================================ mutation self-checks
def test_unmarked_device_op_is_caught():
    """NEGATIVE proof: an unmarked `.cuda()` even in nlp_server.py is NOT sanctioned."""
    src = "def f(x):\n    return x.cuda()\n"
    hit = find_device_ops(src, SINGLE_HOME)[0]
    assert not is_sanctioned(hit, src.splitlines())


def test_marked_device_op_passes_only_in_single_home():
    """The marker sanctions a hit in nlp_server.py; the SAME line elsewhere does not."""
    line = "    y = x.to('cuda')  # host-device-boundary: the one staging point\n"
    src = "def f(x):\n" + line
    hit = find_device_ops(src, SINGLE_HOME)[0]
    assert is_sanctioned(hit, src.splitlines()), "marker in nlp_server.py must pass"
    other = find_device_ops(src, "resolve.py")[0]
    assert not is_sanctioned(other, src.splitlines()), "device op outside the home must fail"


def test_bare_builtin_float_is_not_a_device_op():
    """Vacuity guard: builtin `float(x)` (a Name call) is NOT flagged; only `.float()`."""
    assert find_device_ops("def f(x):\n    return float(x)\n", "resolve.py") == []
    assert find_device_ops("def f(x):\n    return x.float()\n", "resolve.py")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("\nreal-tree device ops:")
    for n in SCANNED:
        p = os.path.join(HERE, n)
        if os.path.exists(p):
            s = open(p, encoding="utf-8").read()
            for h in find_device_ops(s, n):
                print(f"  {h[0]}:{h[1]} {h[2]}  [{'ok' if is_sanctioned(h, s.splitlines()) else 'VIOLATION'}]")
