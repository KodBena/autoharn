#!/usr/bin/env python
"""tests/test_pipeline_parity.py — the mediated pipeline computes what the raw one does.

ADR-0009 / P6 two-tier bar: the mediated `score` (the type-safe ACL crossing torch->numpy/scipy->
jax_lower->jax, FIVE libraries) computes BIT-IDENTICALLY to the raw `raw_score` (the unmediated
native-call mess) on a fixed fixture — every step is the same op in the same order, all float32, so
the bar is `==`. And the REAL transfers are exercised: `torch.export_host` actually runs
`.cpu().numpy()` (a torch tensor becomes a numpy array), the `bridge(...)` round-trips host, and the
jax `import_host` actually runs `jnp.asarray` — data moves, not relabels. The mediated pipeline
ROUTES THROUGH `jax_lower` (the centerpiece adapter): external host data enters it via the checked
`as_pow2` promotion, proving it composes through the bridge (the D2 fix), not only in isolation.
"""

from __future__ import annotations

import numpy as np
import torch as _torch

from demo.pipeline import score
from demo.raw_pipeline import raw_score
from impedance.dtype import F32
from impedance.lib import jax, numpy as host, torch
from impedance.lib.torch_lib import TorchCPU


def test_mediated_equals_raw() -> None:
    rng = np.random.default_rng(7)
    w_np = rng.standard_normal((4, 8)).astype(np.float32)
    h_np = rng.standard_normal((8, 4)).astype(np.float32)

    # raw native-call pipeline
    raw = np.asarray(raw_score(_torch.from_numpy(w_np), _torch.from_numpy(h_np)))

    # mediated ACL pipeline (same data, branded at entry)
    w = torch.brand(_torch.from_numpy(w_np), dev=TorchCPU, dt=F32)
    h = torch.brand(_torch.from_numpy(h_np), dev=TorchCPU, dt=F32)
    med = np.asarray(jax.unwrap(score(w, h)))

    np.testing.assert_array_equal(med, raw)


def test_export_host_is_a_real_transfer() -> None:
    # a torch tensor crossing the host bridge actually becomes a numpy array (not a relabel).
    t = torch.brand(_torch.ones((2, 3), dtype=_torch.float32), dev=TorchCPU, dt=F32)
    assert isinstance(torch.unwrap(t), _torch.Tensor)
    hb = torch.export_host(torch.relu(t))
    assert isinstance(host.unwrap(hb), np.ndarray)
    # ...and crossing into jax actually becomes a jax array.
    yj = jax.import_host(hb)
    assert "jax" in type(jax.unwrap(yj)).__module__.lower() or hasattr(jax.unwrap(yj), "device")
