#!/usr/bin/env python
"""demo/pipeline.py — the MEDIATED cross-library pipeline (the ergonomics proof).

A distilled, honest descendant of where this project started — the spaCy/torch/numpy/jax tangle —
reduced to a clean "embed -> host-normalize -> kernel -> score" loop that crosses FIVE libraries:

    torch  ->  numpy (host interchange)  ->  scipy  ->  jax_lower (Pow2 kernel)  ->  jax

Read the body of `score`: it is a straight line. Every device transfer and dtype handoff that
happens is NAMED on the line where it happens (`export_host` = the real `.cpu().numpy()`,
`bridge(...)` = the real host round-trip, `import_host` = the real `jnp.asarray`), each crossing
is one token, and the four phantom type params are INFERRED — the verbosity lives in the adapter
definitions (written once), not in the pipeline (read often).

The `jax_lower` leg is the package's centerpiece adapter (the `nla_lab/lower` lift): external host
data enters it via the CHECKED `Dyn -> Pow2` promotion `as_pow2`, then a `Pow2`-only kernel op runs,
then the value bridges back out. The shapes are powers of two so the promotion succeeds; a non-pow2
extent would raise at the `as_pow2` boundary (the honest shape-kind entry assertion).

The seam is invisible-when-correct; a wrong crossing would not type-check (see mismatches.py).
Contrast raw_pipeline.py, which computes the same value but can be written wrong four ways and
still looks fine.

Run:  python -m demo.pipeline
"""

from __future__ import annotations

import numpy as np
import torch as _torch

from impedance.dtype import F32
from impedance.host import bridge
from impedance.lib import jax, jax_lower, numpy as host, scipy, torch
from impedance.lib.jax_lib import Jax, JaxCPU
from impedance.lib.torch_lib import Torch, TorchCPU
from impedance.shape import Dyn, Pow2
from impedance.tensor import Tensor

# the few places a signature is spelled out — short per-library carrier aliases (DESIGN §5.5).
TorchMat = Tensor[Torch, TorchCPU, F32, Dyn]
JaxPow2Vec = Tensor[Jax, JaxCPU, F32, Pow2]


def score(w: TorchMat, h: TorchMat) -> JaxPow2Vec:
    """embed (torch) -> host-normalize (scipy over the numpy host buffer) -> Pow2 kernel
    (jax_lower) -> score (jax). Five libraries, one straight line."""
    e = torch.relu(torch.matmul(w, h))            # Tensor[Torch,    TorchCPU, F32, Dyn]
    eh = torch.export_host(e)                      # Tensor[Numpy,    Host,     F32, Dyn]  (real .cpu().numpy())
    nh = scipy.softmax(eh, axis=-1)                # scipy.special.softmax over the host carrier — stays host
    kt = jax_lower.as_pow2(bridge(host, jax_lower, nh))   # Tensor[JaxLower, JaxCPU, F32, Pow2]  (checked Dyn->Pow2)
    sym = jax_lower.add(kt, jax_lower.transpose(kt))      # Tensor[JaxLower, JaxCPU, F32, Pow2]  (a Pow2 kernel op)
    yj = bridge(jax_lower, jax, sym)               # Tensor[Jax,      JaxCPU,   F32, Pow2]  (real jnp.asarray)
    return jax.sum(jax.matmul(yj, yj), axis=-1)    # Tensor[Jax,      JaxCPU,   F32, Pow2]


def main() -> None:
    rng = np.random.default_rng(0)
    w_raw = _torch.from_numpy(rng.standard_normal((4, 8)).astype(np.float32))
    h_raw = _torch.from_numpy(rng.standard_normal((8, 4)).astype(np.float32))

    w = torch.brand(w_raw, dev=TorchCPU, dt=F32)
    h = torch.brand(h_raw, dev=TorchCPU, dt=F32)

    out = score(w, h)
    print("mediated score:", np.asarray(jax.unwrap(out)))


if __name__ == "__main__":
    main()
