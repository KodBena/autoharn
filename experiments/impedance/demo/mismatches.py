#!/usr/bin/env python
"""demo/mismatches.py — FIVE deliberate cross-library impedances that DO NOT BUILD.

This file is a NEGATIVE fixture: it is NOT part of the clean `mypy --strict` gate (mypy.ini
excludes it). `tests/test_mismatches_dont_typecheck.py` runs mypy on this file ALONE and asserts
each crossing emits its predicted error code — the closure claim is a TEST, not prose (ADR-0011
Rule 1 / ADR-0009 Rule 5: verify the artifact). Every illegal line is tagged `# EXPECT[<code>]` and
the test checks that exact code fires on that line.

The seams, each at a LIBRARY CROSSING:
  (a) device       — a CUDA torch tensor handed to the host bridge, unmarked          -> [arg-type]
  (b) lib          — a torch tensor handed to a jax op, skipping the bridge           -> [arg-type]
  (c) dtype        — float64 where float32 is required                                 -> [arg-type]
  (d) shape        — a non-pow2 / raw-int kernel dimension                             -> [arg-type]
  (e) capability   — an op the lowerable adapter does not provide                      -> [attr-defined]
  (f) device-MODEL — a torch tensor TYPED onto a jax device via to_device (the forge)  -> [type-var]
  (g) device-MODEL — a torch object BRANDED onto a jax device (the forge, at entry)     -> [type-var]
  (h) co-residence — a cpu @ cuda op WITHIN one library (the in-flow device pinning)    -> [misc]

(f)/(g) lock in the D1 fix: the device-residence tag is NOT forgeable — `to_device`/`brand` bound
their target to the library's own device family (`DevBase`), so a foreign device tag is a
`[type-var]`, the device MODEL closed by construction (not disclosed residue). (h) demonstrates the
in-library co-residence pinning the critique flagged as untested: it blocks correctly, but mypy
reports it as the cryptic `[misc] Cannot infer _Dev` (a symmetric invariant-TypeVar conflict mypy
cannot attribute to one operand) rather than a clean `[arg-type]` — honestly named here and in the
README, not papered over. The PRIMARY device closure (the host crossing, case (a)) reads cleanly.

A residual — the entry BRAND raising at runtime when a raw tensor's actual device/dtype
contradicts the claimed brand — is a construction-raise, not a type error, so it is demonstrated
by tests/test_brand_raises.py (run, not type-checked), honestly per DESIGN.md §2.1/§2.4.

The four phantom-typed "source" helpers below have `...` bodies: this file is only ever
type-checked, never executed, so they exist purely to hand the crossings a value of the right type.
"""

from __future__ import annotations

from impedance.dtype import F32, F64, I32
from impedance.lib import jax, jax_lower, torch
from impedance.lib.jax_lib import Jax, JaxCPU, JaxGPU
from impedance.lib.jax_lower_lib import JaxLower
from impedance.lib.torch_lib import Torch, TorchCPU, TorchCUDA
from impedance.shape import Dyn, Pow2
from impedance.tensor import Tensor


def _torch_cpu() -> Tensor[Torch, TorchCPU, F32, Dyn]: raise NotImplementedError
def _torch_cuda() -> Tensor[Torch, TorchCUDA, F32, Dyn]: raise NotImplementedError
def _jax_f32() -> Tensor[Jax, JaxCPU, F32, Dyn]: raise NotImplementedError
def _jax_f64() -> Tensor[Jax, JaxCPU, F64, Dyn]: raise NotImplementedError
def _jaxlower_f32() -> Tensor[JaxLower, JaxCPU, F32, Pow2]: raise NotImplementedError


# (a) DEVICE: export_host REQUIRES the tensor be on TorchCPU (the host-side device). A CUDA
#     tensor handed to the host bridge unmarked does not unify — you must torch.to_device(x,
#     TorchCPU) (the real .cpu()) first. The device move is forced into the open, in the types.
torch.export_host(_torch_cuda())  # EXPECT[arg-type]

# (b) LIB: a torch-tagged tensor handed to a jax op, skipping the host bridge. Torch is not Jax;
#     there IS no cross-library op — the only path is bridge(torch, jax, ...). Inexpressible.
jax.matmul(_torch_cpu(), _jax_f32())  # EXPECT[arg-type]

# (c) DTYPE: jax.matmul pins F32; passing F64 is a silent coercion the seam forbids. The ONLY
#     dtype change is the explicit jax.cast(x, F32) — the carrier exposes no .astype.
jax.matmul(_jax_f64(), _jax_f64())  # EXPECT[arg-type]

# (d) SHAPE: the lowerable adapter declares its shape model as Pow2 — its constructors take
#     Pow2Dim dims (branded by pow2(), which validates). A raw int 127 (the classic 2S-1 trap)
#     is not a Pow2Dim. Pass pow2(128) instead; 127 cannot be branded (pow2() raises at runtime).
jax_lower.zeros(127, 8, F32)  # EXPECT[arg-type]

# (e) CAPABILITY: the lowerable-jax adapter's capability set excludes gather (its surface is the
#     band/onehot/select replacement). `gather` simply does not exist on it — the GENERAL jax
#     adapter has it, this one does not. The capability seam is an [attr-defined].
jax_lower.gather(_jaxlower_f32())  # EXPECT[attr-defined]

# (f) DEVICE-MODEL FORGE (to_device): the device-residence tag is NOT forgeable. `to_device`'s
#     target is bound to the torch device family (TorchDevice), so typing a torch tensor as resident
#     on a JAX GPU is unconstructable — not a disclosed construction-open residue. (The D1 fix.)
torch.to_device(_torch_cpu(), JaxGPU)  # EXPECT[type-var]

# (g) DEVICE-MODEL FORGE (brand): the same closure at ENTRY — a torch object cannot be branded onto
#     a jax device. `brand`'s `dev` is bound to TorchDevice, so a foreign device tag is [type-var].
torch.brand(object(), dev=JaxCPU, dt=F32)  # EXPECT[type-var]

# (h) IN-LIBRARY CO-RESIDENCE: a cpu @ cuda op within torch. matmul pins `_Dev` across operands, so
#     the two residences cannot unify. It BLOCKS — but mypy reports a symmetric invariant-TypeVar
#     conflict it cannot attribute to one operand as the cryptic [misc] "Cannot infer _Dev", not a
#     clean [arg-type]. Honestly named (the worse-reading device case the critique flagged untested).
torch.matmul(_torch_cpu(), _torch_cuda())  # EXPECT[misc]
