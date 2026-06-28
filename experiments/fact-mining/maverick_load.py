#!/usr/bin/env python
"""Single source of truth for safely loading the maverick-coref checkpoint (ADR-0012 P1).

maverick's official checkpoint is a PyTorch-Lightning/OmegaConf pickle; PyTorch
>=2.6 defaults `torch.load(weights_only=True)` and refuses its `omegaconf.*`
globals. There are two ways to load it:

  * `weights_only=False` — trusts the WHOLE file, i.e. arbitrary code execution on
    unpickle. Rejected: "trusted source" is not a type, and a blanket escape hatch
    is exactly the unrepresentable-safety ADR-0000 says to design out.
  * allowlist the SPECIFIC, known-safe data classes the checkpoint stores and keep
    `weights_only=True`. An UNEXPECTED global then still fails loud (ADR-0002). This
    is the one we use.

Every `Maverick(...)` construction site wraps itself in `safe_maverick_load()` —
ONE home so no site can forget it (an agent already shipped a load site that did,
dying on the host). This module owns ONLY the load policy; device placement
(`Maverick(device=...)`) and the fp32 cast stay in the CALLER, so torch device ops
remain single-homed for the device-transfer gate.
"""
from __future__ import annotations

import contextlib
import importlib


def _maverick_safe_globals():
    """FROZEN, audited allowlist — NOT discovered by host whack-a-mole (the ADR-0013
    grind the ADR-0014 review rejected). Source of truth: `enumerate_ckpt_globals.py`
    run on weights.ckpt (snapshot 087a90f0...) statically reported EXACTLY these 10
    globals, with zero execution. Each was audited per that file's rule — all are
    pure-data types or torch's own tensor-rebuild primitives; NONE is a
    callable-with-side-effects — so the set is safe under `weights_only=True`.

    A future `Unsupported global: X` is NOT a thing to append blindly: it means the
    file changed — re-run the enumerator and re-audit the delta (pure-data → allow;
    callable-with-side-effects → REFUSE, the file is hostile). Resolved tolerantly so
    a version skew can't crash the helper.

    Audited (10): builtins.dict (the ckpt names it __builtin__.dict; torch's compat
    mapping resolves it), collections.OrderedDict/defaultdict, typing.Any, omegaconf
    {DictConfig, base.ContainerMetadata, base.Metadata, nodes.AnyNode}, torch
    {FloatStorage, _utils._rebuild_tensor_v2}.
    """
    import collections
    import typing

    allow = [dict, typing.Any, collections.OrderedDict, collections.defaultdict]
    # omegaconf config nodes (pure data; resolution is lazy → inert at unpickle)
    wanted = {
        "omegaconf": ["DictConfig", "ListConfig"],   # ListConfig: defensive, pure-data
        "omegaconf.base": ["ContainerMetadata", "Metadata"],
        "omegaconf.nodes": ["AnyNode"],
    }
    for mod_name, names in wanted.items():
        try:
            mod = importlib.import_module(mod_name)
        except ImportError:
            continue
        for n in names:
            obj = getattr(mod, n, None)
            if obj is not None:
                allow.append(obj)
    # torch's own rebuild primitives — torch trusts these (usually already in its
    # default weights_only set; added explicitly so the load is provably one-shot).
    try:
        import torch
        for dotted in ("FloatStorage", "_utils._rebuild_tensor_v2"):
            obj = torch
            for part in dotted.split("."):
                obj = getattr(obj, part, None)
                if obj is None:
                    break
            if obj is not None:
                allow.append(obj)
    except ImportError:
        pass
    return allow


@contextlib.contextmanager
def safe_maverick_load():
    """Construct `Maverick(...)` inside this block. Loads the trusted checkpoint
    under `weights_only=True` with an explicit allowlist of its audited pure-data
    globals — NO arbitrary-code-execution exposure. Fails loud on any global not in
    the allowlist.

    Belt-and-suspenders (the ADR-0014 review's caveat): the allowlist only protects
    a load that actually runs `weights_only=True`. A PyTorch-Lightning version that
    passed `weights_only=False` to its internal `torch.load` would silently disable
    all protection. So we also guard `torch.load` for the duration: an attempt to
    load with `weights_only=False` RAISES rather than silently opening the
    arbitrary-exec path."""
    import torch

    orig_load = torch.load

    def _guarded_load(*a, **k):
        if k.get("weights_only") is False:
            raise RuntimeError(
                "maverick checkpoint load attempted weights_only=False (the "
                "arbitrary-code-execution path) — refusing. The safe path is "
                "weights_only=True + the audited safe_globals allowlist.")
        k.setdefault("weights_only", True)
        return orig_load(*a, **k)

    torch.load = _guarded_load
    try:
        with torch.serialization.safe_globals(_maverick_safe_globals()):
            yield
    finally:
        torch.load = orig_load
