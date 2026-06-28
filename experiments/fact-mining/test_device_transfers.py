#!/usr/bin/env python
"""Single-homed device-transfer gate for the fact-mining daemon (pure `ast`).

Discipline ported from chocofarm's tests/test_no_gratuitous_transfers.py — but
SCALED DOWN deliberately (see "Proportionality" below). The property: every
CPU<->GPU boundary op lives in a DECLARED home and carries an inline
`# host-device-boundary: <reason>` marker. A device op that appears in any other
module, or in a home without the marker, reds here.

TWO framework edges, ONE home EACH (not one global home). The codebase now has
two distinct device edges and the gate single-homes each to its own file:

  * torch / spaCy / maverick GPU placement+casts -> `nlp_server.py`
  * jax host<->device pulls & lifts            -> `coref_host_shell.py`

`coref_host_shell.py` is the ADR-0012 P7 imperative boundary for the jax decode
pipeline: it legitimately pulls device results to the host (`jax.device_get`) and
lifts host index/mask lists back onto the device (`jnp.asarray(<host data>)`).
Those crossings are SANCTIONED, but only here and only when marked — exactly the
same contract the torch edge has in nlp_server.py. (History: an earlier version of
this gate recognized only the torch/spaCy vocabulary, so every jax crossing in the
shell was INVISIBLE to it — a vacuous "ok". The jax transfer ops below close that
gap so the "every CPU<->GPU op lives in an auditable home" invariant holds for the
jax half too.)

Why this matters: scattered/unannotated device transfers are how redundant
host<->device crossings creep in unnoticed. Single-homing them makes each device
edge reviewable in one file and one grep — and makes a `jax.device_get` migrating
out of the shell into extract.py/resolve.py a RED, not a silent escape.

Proportionality (the chocofarm ratchet was NOT ported, on purpose): chocofarm
guards a measured hot path across many modules with a ~500-line checker + a
monotonic JSON baseline + a device-signal heuristic. Here each edge is a handful
of sites in ONE function, so a baseline ratchet and a false-positive heuristic
would be ceremony. Falsifiable kill-condition for that choice: if device ops ever
legitimately spread beyond these homes, replace this positive assertion with
chocofarm's baseline ratchet.

Vendored third-party code (maverick, spaCy) is OUT OF SCOPE — its internal
`.to(device)` / `.cpu()` transfers are ones we can neither annotate nor fix, and
baselining them would be exactly the cargo-cult net chocofarm warns against.

Runs under `pytest`, or standalone: `python test_device_transfers.py`.
"""

from __future__ import annotations

import ast
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MARKER = "# host-device-boundary:"       # inline opt-in, same convention as chocofarm

# Each framework's device edge is sanctioned iff it appears in its framework's home
# AND carries MARKER. MANDATE: ONE jax home — two is a drift hazard. coref_host_shell.py
# is the single jax host<->device home; the ZMQ wire seam (coref_decode_server.py)
# delegates its lifts here (coref_host_shell.lift_params / decode_document_host) and
# stays host-only, so it authors no jax device op and needs no home of its own.
HOMES = {
    "torch": frozenset({"nlp_server.py"}),         # torch / spaCy / maverick GPU placement+casts
    "jax": frozenset({"coref_host_shell.py"}),     # the SINGLE jax host<->device home (ADR-0012 P7)
}
SCANNED = ["extract.py", "load_facts.py", "nlp_cache.py",
           "nlp_client.py", "nlp_server.py", "resolve.py",
           "jax_decode.py", "coref_host_shell.py", "maverick_load.py",
           "coref_decode_server.py", "coref_decode_client.py",
           "coref_decode_inputs.py"]

# Closed token sets — the device-edge ops actually reachable in this code.
# Deliberately name-based and conservative; no device-signal heuristic.
# torch / spaCy: method calls (`x.to(...)`, `m.float()`, ...) + bare GPU-enable.
TORCH_METHODS = {"to", "cuda", "cpu", "half", "float", "autocast"}
TORCH_FUNCS = {"require_gpu", "prefer_gpu"}
# jax host<->device transfers. device_get/device_put/block_until_ready cross the
# edge unconditionally; asarray/array/from_dlpack cross it when lifting HOST data
# (the only way they appear in our shell). A `jnp.asarray` on an already-device
# array would be a harmless false positive — in our tree every one is a real
# host->device lift, so flagging+marking it is correct.
JAX_TRANSFERS = {"device_get", "device_put", "block_until_ready",
                 "asarray", "array", "from_dlpack"}

# (relpath, lineno, token, framework)
Hit = "tuple[str, int, str, str]"


class _DeviceVisitor(ast.NodeVisitor):
    def __init__(self, relpath: str):
        self.relpath = relpath
        self.found: list[tuple[str, int, str, str]] = []

    def visit_Call(self, node: ast.Call):
        f = node.func
        if isinstance(f, ast.Attribute):
            # `x.to(...)`, `m.float()`, `spacy.require_gpu()`  -> torch/spaCy edge
            if f.attr in (TORCH_METHODS | TORCH_FUNCS):
                self.found.append((self.relpath, node.lineno, f".{f.attr}()", "torch"))
            # `jax.device_get(...)`, `jnp.asarray(<host>)`, ...  -> jax edge
            elif f.attr in JAX_TRANSFERS:
                self.found.append((self.relpath, node.lineno, f".{f.attr}()", "jax"))
        elif isinstance(f, ast.Name) and f.id in TORCH_FUNCS:
            # bare `require_gpu()` (e.g. `from spacy import require_gpu`)
            self.found.append((self.relpath, node.lineno, f"{f.id}()", "torch"))
        elif _is_maverick_device_ctor(node):
            self.found.append((self.relpath, node.lineno, "Maverick(device=...)", "torch"))
        self.generic_visit(node)


def _is_maverick_device_ctor(node: ast.Call) -> bool:
    name = node.func.id if isinstance(node.func, ast.Name) else (
        node.func.attr if isinstance(node.func, ast.Attribute) else None)
    return name == "Maverick" and any(k.arg == "device" for k in node.keywords)


def find_device_ops(src: str, relpath: str) -> list[tuple[str, int, str, str]]:
    v = _DeviceVisitor(relpath)
    v.visit(ast.parse(src))
    return v.found


def is_sanctioned(hit: tuple[str, int, str, str], src_lines: list[str]) -> bool:
    """A device op is allowed iff it is in ONE of its framework's homes and carries
    MARKER."""
    relpath, lineno, _, framework = hit
    if relpath not in HOMES.get(framework, frozenset()):
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
                relpath, lineno, token, framework = hit
                homes = HOMES.get(framework, frozenset())
                why = (f"not in {framework} home(s) {sorted(homes)}"
                       if relpath not in homes
                       else "missing inline `# host-device-boundary:` marker")
                violations.append(f"{relpath}:{lineno} {token} [{framework}] — {why}")
    return violations


# ===================================================================== the gate
def test_device_ops_are_single_homed_and_marked():
    """Every device-edge op in our code is in its framework's home with a marker."""
    violations = _scan_real_tree()
    assert not violations, (
        "un-single-homed / unmarked device transfer(s) — move to the framework's "
        "home (torch->nlp_server.py, jax->coref_host_shell.py) and add an inline "
        "`# host-device-boundary: <reason>`:\n  " + "\n  ".join(violations))


# ============================================================ mutation self-checks
def test_unmarked_device_op_is_caught():
    """NEGATIVE proof: an unmarked `.cuda()` even in its home is NOT sanctioned."""
    src = "def f(x):\n    return x.cuda()\n"
    hit = find_device_ops(src, "nlp_server.py")[0]
    assert not is_sanctioned(hit, src.splitlines())


def test_marked_device_op_passes_only_in_single_home():
    """The marker sanctions a hit in the framework home; the SAME line elsewhere does not."""
    line = "    y = x.to('cuda')  # host-device-boundary: the one staging point\n"
    src = "def f(x):\n" + line
    hit = find_device_ops(src, "nlp_server.py")[0]
    assert is_sanctioned(hit, src.splitlines()), "marker in nlp_server.py must pass"
    other = find_device_ops(src, "resolve.py")[0]
    assert not is_sanctioned(other, src.splitlines()), "device op outside the home must fail"


def test_jax_transfer_is_recognized_and_homed():
    """The jax edge is NOT invisible: `jax.device_get` / `jnp.asarray` are device ops,
    sanctioned only in the jax home (coref_host_shell.py) AND only when marked."""
    pull = "    r = jax.device_get(x)  # host-device-boundary: device->host pull\n"
    src = "def f(x):\n" + pull
    hit = find_device_ops(src, "coref_host_shell.py")[0]
    assert hit[3] == "jax" and hit[2] == ".device_get()"
    assert is_sanctioned(hit, src.splitlines()), "marked jax pull in the jax home must pass"
    # unmarked jax pull in the home -> caught
    bare = find_device_ops("def f(x):\n    return jax.device_get(x)\n", "coref_host_shell.py")[0]
    assert not is_sanctioned(bare, "def f(x):\n    return jax.device_get(x)\n".splitlines())
    # a jax pull in the TORCH home (or any non-jax file) is not sanctioned
    lift = "    a = jnp.asarray(p)  # host-device-boundary: lift host list\n"
    nshome = find_device_ops("def f(p):\n" + lift, "nlp_server.py")[0]
    assert nshome[3] == "jax"
    assert not is_sanctioned(nshome, ("def f(p):\n" + lift).splitlines()), \
        "jax transfer in the torch home is not its home -> must fail"


def test_jax_has_a_single_home_and_wire_seam_is_not_one():
    """MANDATE: ONE jax home (coref_host_shell.py) — two is a drift hazard. A marked
    jax lift is sanctioned in the home; the SAME marked lift in the ZMQ wire seam
    (coref_decode_server.py) is NOT — the seam must DELEGATE its lifts to the shell,
    not become a second home. Any other non-home file is likewise rejected."""
    lift = "    a = jnp.asarray(p)  # host-device-boundary: lift host array\n"
    src = "def f(p):\n" + lift
    # the single jax home accepts a marked lift
    shell_hit = find_device_ops(src, "coref_host_shell.py")[0]
    assert shell_hit[3] == "jax" and shell_hit[2] == ".asarray()"
    assert is_sanctioned(shell_hit, src.splitlines()), "marked jax lift in the jax home must pass"
    # the wire seam is NOT a jax home -> the same lift there must FAIL (delegate instead)
    seam_hit = find_device_ops(src, "coref_decode_server.py")[0]
    assert not is_sanctioned(seam_hit, src.splitlines()), \
        "a jax lift in the wire seam must fail — single home; delegate to the shell"
    # any other non-home file likewise (no scatter)
    stray = find_device_ops(src, "extract.py")[0]
    assert not is_sanctioned(stray, src.splitlines())
    # unmarked in the home -> still caught
    bare = "def f(p):\n    return jnp.asarray(p)\n"
    bhit = find_device_ops(bare, "coref_host_shell.py")[0]
    assert not is_sanctioned(bhit, bare.splitlines())


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
                print(f"  {h[0]}:{h[1]} {h[2]} [{h[3]}]  "
                      f"[{'ok' if is_sanctioned(h, s.splitlines()) else 'VIOLATION'}]")
