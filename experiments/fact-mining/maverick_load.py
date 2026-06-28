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
    """The specific classes maverick's omegaconf/Lightning checkpoint pickles.

    Allowlisting exactly these keeps `weights_only=True` (no arbitrary-code path).
    If the host load fails with `Unsupported global: X`, X is a new known-safe data
    class the checkpoint added — add it HERE, with intent; never fall back to
    trusting the whole file. Resolved tolerantly so an omegaconf version skew can't
    crash the helper itself.
    """
    import collections
    import typing

    allow = [typing.Any, collections.defaultdict, collections.OrderedDict]
    wanted = {
        "omegaconf": ["DictConfig", "ListConfig"],
        "omegaconf.base": ["ContainerMetadata", "Metadata"],
        "omegaconf.nodes": ["AnyNode", "ValueNode", "InterpolationResultNode"],
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
    return allow


@contextlib.contextmanager
def safe_maverick_load():
    """Construct `Maverick(...)` inside this block. Loads the trusted checkpoint
    under `weights_only=True` with an explicit allowlist of its omegaconf/stdlib
    globals — NO arbitrary-code-execution exposure. Fails loud on any global not in
    the allowlist (extend `_maverick_safe_globals` when that happens)."""
    import torch

    with torch.serialization.safe_globals(_maverick_safe_globals()):
        yield
