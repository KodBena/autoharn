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
    """The specific, audited PURE-DATA classes maverick's omegaconf/Lightning
    checkpoint pickles. Allowlisting exactly these keeps `weights_only=True` — no
    arbitrary-code path.

    The complete set is NOT discovered by host whack-a-mole (that is the ADR-0013
    grind the ADR-0014 review rejected). Run `enumerate_ckpt_globals.py` ONCE on the
    host: it statically reads every global the checkpoint references, with zero
    execution. Audit its "MUST allowlist" bucket per the rule in that file's header
    (pure data → allow; callable-with-side-effects → REFUSE, the file is hostile),
    and freeze that set here. A future `Unsupported global: X` is then not a thing
    to append blindly — it means the file changed: re-run the enumerator, re-audit.

    The builtins below are pure-data callables omegaconf names as rebuild functions
    (`dict(...)`, `tuple(...)`); they cannot execute attacker code regardless of
    args. omegaconf classes are resolved tolerantly against version skew.
    """
    import collections
    import typing

    allow = [typing.Any, collections.defaultdict, collections.OrderedDict,
             dict, list, tuple, set, frozenset]
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
