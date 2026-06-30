#!/usr/bin/env python
"""demo/raw_pipeline.py — the RAW library-call mess (the "before").

The SAME math as demo/pipeline.py, written the way it is written today: a pile of native calls
across torch / numpy / scipy / jax. It is fully `mypy --strict`-clean — and THAT is the point.
The raw libraries do not encode the (lib, device, dtype, shape) seam, so the type checker cannot
see any of the four latent ways this is one edit from being wrong:

  1. device   — `e.detach().cpu().numpy()` works only because someone remembered the manual
                `.cpu()`; hand `e` (if it were CUDA) straight to `.numpy()` and it explodes at
                runtime, not at type-check. The `if e.is_cuda` juggle is the tell.
  2. dtype    — the `.astype(np.float32)` papers over a silent float64 drift; nothing forces it,
                and dropping it (or an upstream f64) flows to the jax matmul unnoticed.
  3. lib      — `jnp.asarray(sym)` is a bare handoff; pass a torch tensor here by mistake and mypy
                shrugs (its `*args` are `Any`-ish at the boundary).
  4. shape    — no kind is carried; the kernel leg's power-of-two requirement is invisible — a
                non-pow2 extent is a runtime error far downstream, not a type error at the entry.

The mediated pipeline (pipeline.py) computes the identical value (parity-tested) but CANNOT be
written wrong in any of these four ways — and reads cleaner. That is the whole before/after.
"""

from __future__ import annotations

import jax.numpy as jnp
import numpy as np
import numpy.typing as npt
import torch
from jax import Array as JaxArray
from scipy import special


def raw_score(w: torch.Tensor, h: torch.Tensor) -> JaxArray:
    e = torch.relu(torch.matmul(w, h))
    # the manual device juggle — easy to forget, invisible to the type checker:
    if e.is_cuda:
        e = e.cpu()
    eh: npt.NDArray[np.float32] = e.detach().cpu().numpy()
    # a silent dtype coercion papering a possible float64 drift (nothing forces it):
    eh = eh.astype(np.float32)
    nh = special.softmax(eh, axis=-1).astype(np.float32)
    # the "kernel" leg, hand-inlined: symmetrize. No power-of-two guard — the kernel's shape
    # requirement lives only in the author's head, not in any type.
    sym = nh + nh.T
    yj = jnp.asarray(sym)                 # bare cross-library handoff, no dtype/device/shape guard
    return jnp.sum(jnp.matmul(yj, yj), axis=-1)


def main() -> None:
    rng = np.random.default_rng(0)
    w = torch.from_numpy(rng.standard_normal((4, 8)).astype(np.float32))
    h = torch.from_numpy(rng.standard_normal((8, 4)).astype(np.float32))
    print("raw score:", np.asarray(raw_score(w, h)))


if __name__ == "__main__":
    main()
