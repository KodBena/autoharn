#!/usr/bin/env python
"""Import XOR-gate: a file is HOST xor DEVICE (pure `ast`).

ADR-0000 derivation. The maverick defect class is *host and device arrays
interleaved in one computation* (`np.nonzero(torch_tensor)`, `np.stack([cpu_tensor
,…])`, silent float64↔float32). The type that makes that class unrepresentable:
a value is EITHER a host array (numpy) OR a device array (torch/jax/cupy/tf), and
the only crossing is a named boundary op in an imperative shell — the functional
core never mixes them (ADR-0012 P9). Python can't carry that host/device
distinction in its type system, so this gate is its MECHANICAL SHADOW: it forbids
any single file from importing both a host array lib and a device array lib —
quantifying over the CLASS, not the instance (ADR-0011 Rule 4).

The escape hatch is a declared boundary: a file whose JOB is the host↔device seam
(a conversion shell) is whitelisted with a reason in `BOUNDARY_FILES` — the one
authoritative place the two meet (ADR-0012 P7), exactly as the device-transfer
gate single-homes `.to()/.cuda()`. numpy is legitimate for the irreducible
pre/post-transfer host work, but a BOUNDARY_FILES entry is a *conscious, audited*
decision: its reason must justify the mix on perf AND structural grounds, not
"convenience". Everything else is host xor device.

FILENAMES ARE HONEST. A file whose name advertises a device framework
(`jax_decode.py`, `torch_*`, …) promises to be device-only; importing numpy into
it is a lie the whitelist cannot launder. Such a file is a violation REGARDLESS
of BOUNDARY_FILES — rename it to an honest seam name, or take numpy out.

Scope: OUR files only. A vendored hot-path dep (e.g. maverick) is NOT scanned
here — per the (b)-mechanization it must instead be held to this gate or wrapped
behind a boundary shell so its internal tangle cannot leak into our composition.

Runs under pytest, or standalone: `python test_import_xor.py`.
"""

from __future__ import annotations

import ast
import os

HERE = os.path.dirname(os.path.abspath(__file__))
# The composed daemon/pipeline modules. jax_decode.py is device-NAMED: the gate
# enforces it is numpy-free regardless of BOUNDARY_FILES (honest filenames).
# coref_host_shell.py is the neutrally-named host shell; it is kept pure-python +
# jax (numpy-free) by design, so it needs no BOUNDARY_FILES entry. The host-only
# fixture scaffolding (capture_fixtures.py, test_jax_decode_fidelity.py) is NOT
# scanned — it is the fixture-I/O boundary, not part of the device pipeline.
SCANNED = ["extract.py", "load_facts.py", "nlp_cache.py",
           "nlp_client.py", "nlp_server.py", "resolve.py",
           "jax_decode.py", "coref_host_shell.py", "maverick_load.py"]

HOST = {"numpy"}
DEVICE = {"torch", "jax", "jaxlib", "cupy", "tensorflow"}
# filename tokens that ADVERTISE a device framework — such a file promises
# device-only and may not import numpy, not even via BOUNDARY_FILES.
DEVICE_NAME_TOKENS = ("jax", "torch", "cupy", "tensorflow", "cuda", "gpu")

# Declared host↔device boundary shells: {relpath: reason}. The ONLY files allowed
# to be both host and device. Empty today — add a file here only when it IS the
# typed seam (e.g. a numpy<->jax conversion module), with a one-line reason.
BOUNDARY_FILES: dict[str, str] = {}


def imported_top_modules(src: str) -> set[str]:
    """Top-level module names of every import anywhere in the file (incl. lazy
    in-function imports — a file 'includes' an import wherever it appears)."""
    mods: set[str] = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:           # skip relative imports
                mods.add(node.module.split(".")[0])
    return mods


def classify(src: str) -> tuple[set[str], set[str]]:
    mods = imported_top_modules(src)
    return mods & HOST, mods & DEVICE


def _device_named(relpath: str) -> bool:
    base = os.path.basename(relpath).lower()
    return any(tok in base for tok in DEVICE_NAME_TOKENS)


def violates(src: str, relpath: str) -> tuple[set[str], set[str]] | None:
    """Return (host_libs, device_libs) if `relpath` mixes host+device illegitimately,
    else None. A device-NAMED file mixing is always a violation (honest filenames —
    the whitelist can't launder a lying name); any other file may opt out via
    BOUNDARY_FILES."""
    host, device = classify(src)
    if not (host and device):
        return None
    if _device_named(relpath):           # honest filenames: name promises device-only
        return host, device
    if relpath not in BOUNDARY_FILES:
        return host, device
    return None


def _scan_real_tree() -> list[str]:
    out = []
    for name in SCANNED:
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            continue
        v = violates(open(p, encoding="utf-8").read(), name)
        if v:
            out.append(f"{name}: imports host {sorted(v[0])} AND device {sorted(v[1])}")
    return out


# ===================================================================== the gate
def test_no_file_is_both_host_and_device():
    """No scanned file imports both a host (numpy) and a device (torch/jax/…) lib
    unless it is a declared host↔device boundary shell in BOUNDARY_FILES."""
    violations = _scan_real_tree()
    assert not violations, (
        "import XOR-gate: file(s) mix host and device array libs — keep the "
        "functional core host-XOR-device, or declare the file a boundary shell in "
        "BOUNDARY_FILES with a reason:\n  " + "\n  ".join(violations))


# ============================================================ mutation self-checks
def test_both_is_flagged():
    assert violates("import numpy as np\nimport torch\n", "x.py")
    assert violates("def f():\n    import cupy\nimport numpy\n", "x.py")  # lazy import counts


def test_only_one_side_passes():
    assert violates("import numpy as np\n", "x.py") is None
    assert violates("import torch\nimport jax.numpy as jnp\n", "x.py") is None  # all device


def test_declared_boundary_passes_only_when_listed():
    src = "import numpy as np\nimport jax\n"
    assert violates(src, "x.py") is not None
    BOUNDARY_FILES["_probe_boundary.py"] = "test seam"
    try:
        assert violates(src, "_probe_boundary.py") is None
    finally:
        del BOUNDARY_FILES["_probe_boundary.py"]


def test_device_named_file_cannot_be_whitelisted():
    """Honest filenames: a device-named file (jax_decode.py) importing numpy is a
    violation even if someone lists it in BOUNDARY_FILES; a neutrally-named seam
    is not."""
    src = "import numpy as np\nimport jax\n"
    BOUNDARY_FILES["jax_decode.py"] = "trying to launder a dishonest name"
    try:
        assert violates(src, "jax_decode.py") is not None, "device-named file must not whitelist numpy"
    finally:
        del BOUNDARY_FILES["jax_decode.py"]
    BOUNDARY_FILES["coref_host_shell.py"] = "the one numpy<->jax seam (perf: vectorised pre-transfer pack)"
    try:
        assert violates(src, "coref_host_shell.py") is None
    finally:
        del BOUNDARY_FILES["coref_host_shell.py"]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("\nreal-tree host/device imports:")
    for n in SCANNED:
        p = os.path.join(HERE, n)
        if os.path.exists(p):
            h, d = classify(open(p, encoding="utf-8").read())
            tag = "VIOLATION" if (h and d and n not in BOUNDARY_FILES) else "ok"
            print(f"  {n:16} host={sorted(h)} device={sorted(d)}  [{tag}]")
