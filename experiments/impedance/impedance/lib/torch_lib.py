#!/usr/bin/env python
"""impedance.lib.torch_lib — the torch adapter (device model: cpu / cuda).

Library tag `Torch`; device family `TorchCPU` / `TorchCUDA` (subclasses of `TorchDevice`);
HOST-side device `TorchCPU`; shape kind `Dyn`. The seam ops are REAL transfers/casts — not
relabels: `export_host` is `t.detach().cpu().numpy()`, `import_host` is `torch.from_numpy(...)`,
`to_device` is `t.to(...)`, `cast` is `t.to(dtype)`. Every capability body is one native
`torch.*` call.

This is the canonical "device library": its `export_host` REQUIRES the tensor be on `TorchCPU`
(the host-side device), so handing a `TorchCUDA` tensor to the host bridge is a mypy `[arg-type]`
— the device transfer is forced into the open. A real `.cpu().numpy()` actually moves the bytes.

HOST-XOR-DEVICE boundary: this file imports torch AND numpy (it IS the torch<->host crossing —
its export/import are exactly the marked transfer). It is the one sanctioned boundary module.
"""

from __future__ import annotations

from typing import Any, Final, TypeVar, cast

import numpy as np
import torch as _torch

from impedance.adapter import LibAdapter
from impedance.dtype import BoolT, DType, F32, F64, I32, I64
from impedance.host import Host, Numpy
from impedance.shape import Dyn, ShapeKind
from impedance.tensor import Tensor, _unwrap, _wrap

_D = TypeVar("_D", bound=DType)
_D2 = TypeVar("_D2", bound=DType)
_S = TypeVar("_S", bound=ShapeKind)
_Dev = TypeVar("_Dev")  # device-PRESERVING (cast keeps residence; never forges it)
_NDArr = np.ndarray[Any, np.dtype[Any]]


# ------------------------------------------------------------------- the torch device family
class TorchDevice:
    """Phantom base of torch's device model — the bound of the `*Device` family this adapter
    declares. Never instantiated. The device-crossing ops (`to_device`/`brand`) bound their
    target to this class, so torch residence tags are EXACTLY its subclasses and no foreign
    (jax/numpy) device tag can be typed onto a torch tensor — the device model is closed."""

    __slots__ = ()


# the bound device-family var: a torch tensor's residence is a `TorchDevice` and nothing else.
# This is what forecloses the forge `torch.to_device(x, JaxGPU)` / `torch.brand(raw, dev=JaxCPU)`
# — a non-TorchDevice target is a mypy `[type-var]`, not a disclosed construction-open residue.
_TDev = TypeVar("_TDev", bound=TorchDevice)


class TorchCPU(TorchDevice):
    """Phantom tag: a torch tensor resident in host (CPU) memory — torch's HOST-side device."""

    __slots__ = ()


class TorchCUDA(TorchDevice):
    """Phantom tag: a torch tensor resident on a CUDA device — NOT host-reachable without a
    marked `.cpu()` transfer."""

    __slots__ = ()


class Torch:
    """Library tag: torch. A marker class, unrelated to `Numpy`/`Jax`/… — so a `Tensor[Torch,…]`
    is not assignable to a `Tensor[Jax,…]` (the lib seam)."""


_TORCH_DTYPE: Final[dict[type[DType], _torch.dtype]] = {
    F32: _torch.float32,
    F64: _torch.float64,
    I32: _torch.int32,
    I64: _torch.int64,
    BoolT: _torch.bool,
}
_TORCH_DEV: Final[dict[type[Any], str]] = {TorchCPU: "cpu", TorchCUDA: "cuda"}


def _t(x: Tensor[Any, Any, Any, Any]) -> _torch.Tensor:
    """Narrow the carrier's backing object to the torch tensor this adapter knows it is."""
    return cast(_torch.Tensor, _unwrap(x))


class TorchAdapter:
    """The torch adapter — satisfies `LibAdapter[Torch, TorchCPU, TorchDevice]` structurally
    (lib tag `Torch`, host-side device `TorchCPU`, device family `TorchDevice`)."""

    HOST_DEVICE: type[TorchCPU] = TorchCPU

    # ---- (i) device model: the REAL in-library transfer (`.to(device)`); target bound to the
    #          torch device family, so a foreign device tag is a mypy [type-var] (D1 closed) ----
    def to_device(self, x: Tensor[Torch, Any, _D, _S], dev: type[_TDev]) -> Tensor[Torch, _TDev, _D, _S]:
        return _wrap(_t(x).to(_TORCH_DEV[dev]))

    # ---- (ii) dtype model: the REAL cast (`.to(dtype)`) ------------------------------------
    def supports_dtype(self, dt: type[DType]) -> bool:
        return dt in _TORCH_DTYPE

    def cast(self, x: Tensor[Torch, _Dev, Any, _S], dt: type[_D2]) -> Tensor[Torch, _Dev, _D2, _S]:
        return _wrap(_t(x).to(_TORCH_DTYPE[dt]))

    # ---- (iii) shape model -----------------------------------------------------------------
    def shape_kind(self) -> type[ShapeKind]:
        return Dyn

    # ---- (iv) entry/exit brands + bridge spine ---------------------------------------------
    def brand(self, raw: object, *, dev: type[_TDev], dt: type[_D2]) -> Tensor[Torch, _TDev, _D2, Dyn]:
        """Brand a raw `torch.Tensor` — `dev` is bound to `TorchDevice` (so a torch object cannot
        be branded onto a jax device — entry is closed too), and the ACTUAL device and dtype are
        read and VERIFIED against the claimed `dev`/`dt`, raising on mismatch (a construction-time
        assertion; a raw tensor carries no static residence/dtype a type could read)."""
        t = cast(_torch.Tensor, raw)
        want_dev = _TORCH_DEV[dev]
        if t.device.type != want_dev:
            raise TypeError(
                f"torch.brand: raw tensor is on device '{t.device.type}' but the claimed device "
                f"tag is {dev.__name__} ('{want_dev}'). Move it with torch.to_device(...) before "
                f"branding, or brand it with the correct device tag.")
        want_dt = _TORCH_DTYPE[dt]
        if t.dtype != want_dt:
            raise TypeError(
                f"torch.brand: raw tensor dtype {t.dtype} contradicts the claimed dtype tag "
                f"{dt.__name__} ({want_dt}). Cast explicitly with torch.cast(...) to change it.")
        return _wrap(t)

    def unwrap(self, x: Tensor[Torch, Any, Any, Any]) -> object:
        return _t(x)

    def export_host(self, x: Tensor[Torch, TorchCPU, _D, _S]) -> Tensor[Numpy, Host, _D, _S]:
        # the REAL transfer: detach from autograd, ensure host residence, hand a numpy view to
        # the interchange. `x` is REQUIRED to be on TorchCPU (the type), so a CUDA tensor cannot
        # reach here without an explicit torch.to_device(x, TorchCPU) first.
        arr: _NDArr = _t(x).detach().cpu().numpy()
        return _wrap(arr)

    def import_host(self, b: Tensor[Numpy, Host, _D, _S]) -> Tensor[Torch, TorchCPU, _D, _S]:
        # the REAL transfer the other way: adopt the host numpy buffer as a CPU torch tensor.
        return _wrap(_torch.from_numpy(cast(_NDArr, _unwrap(b))))

    # ============================ capability surface (per-library) ===========================
    def matmul(self, a: Tensor[Torch, _Dev, F32, _S], b: Tensor[Torch, _Dev, F32, _S]) -> Tensor[Torch, _Dev, F32, _S]:
        # device-pinned across operands (co-residence): a cpu @ cuda matmul is a mypy [arg-type].
        return _wrap(_torch.matmul(_t(a), _t(b)))

    def relu(self, a: Tensor[Torch, _Dev, F32, _S]) -> Tensor[Torch, _Dev, F32, _S]:
        return _wrap(_torch.relu(_t(a)))

    def add(self, a: Tensor[Torch, _Dev, _D, _S], b: Tensor[Torch, _Dev, _D, _S]) -> Tensor[Torch, _Dev, _D, _S]:
        return _wrap(_t(a) + _t(b))


torch: Final = TorchAdapter()  # the singleton the demo imports as `torch`

# structural Protocol conformance gate: device family is TorchDevice (the third param).
_seam_check: LibAdapter[Torch, TorchCPU, TorchDevice] = torch
