#!/usr/bin/env python
"""impedance.lib.jax_lib — the general jax adapter (a thin, torch-free jax interpreter).

Library tag `Jax`; device family `JaxCPU` / `JaxGPU`; HOST-side device `JaxCPU`; shape kind `Dyn`.
Seam ops are REAL handoffs: `import_host` is `jnp.asarray(np_buf)`, `export_host` is
`np.asarray(jax_arr)` (a genuine device->host materialization), `to_device` is `jax.device_put`,
`cast` is `arr.astype(...)`.

This is the GENERAL jax interpreter — it DOES expose `gather` (and other non-kernel ops). Contrast
`lib/jax_lower_lib.py` (the lowerable-jax adapter, library tag `JaxLower`), whose capability set
EXCLUDES `gather`: the capability seam (§2.5) is precisely that capabilities differ by adapter, so
a `gather` legal here is a mypy `[attr-defined]` there. A second jax interpreter is a first-class,
type-distinct thing, not a fork of one file.

HOST boundary: imports jax/jnp AND numpy (it IS the jax<->host crossing). The sanctioned boundary.
"""

from __future__ import annotations

from typing import Any, Final, TypeVar, cast

import jax as _jax
import jax.numpy as jnp
import numpy as np

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


# --------------------------------------------------------------------- the jax device family
class JaxDevice:
    """Phantom base of jax's device model — the bound on jax residence tags. Never instantiated.
    The device-crossing ops bound their target to this class, so a jax tensor cannot be typed onto
    a torch/numpy device (the device model is closed, both in-flow and at entry)."""

    __slots__ = ()


class JaxCPU(JaxDevice):
    """Phantom tag: a jax array committed to a CPU device — jax's HOST-side device."""

    __slots__ = ()


class JaxGPU(JaxDevice):
    """Phantom tag: a jax array committed to a GPU device."""

    __slots__ = ()


class Jax:
    """Library tag: jax. A marker class unrelated to the other library tags (the lib seam)."""


# the bound device-family var: a jax tensor's residence is a `JaxDevice` and nothing else —
# forecloses `jax.to_device(x, TorchCUDA)` / `jax.brand(raw, dev=TorchCPU)` as mypy [type-var].
_JDev = TypeVar("_JDev", bound=JaxDevice)


_JNP_DTYPE: Final[dict[type[DType], Any]] = {
    F32: jnp.float32,
    F64: jnp.float64,
    I32: jnp.int32,
    I64: jnp.int64,
    BoolT: jnp.bool_,
}
_JAX_PLATFORM: Final[dict[type[Any], str]] = {JaxCPU: "cpu", JaxGPU: "gpu"}


def _a(x: Tensor[Any, Any, Any, Any]) -> _jax.Array:
    """Narrow the carrier's backing object to the jax array this adapter knows it is."""
    return cast(_jax.Array, _unwrap(x))


def _device(dev: type[Any]) -> _jax.Device:
    return _jax.devices(_JAX_PLATFORM[dev])[0]


class JaxAdapter:
    """The general jax adapter — satisfies `LibAdapter[Jax, JaxCPU, JaxDevice]` structurally
    (lib tag `Jax`, host-side device `JaxCPU`, device family `JaxDevice`)."""

    HOST_DEVICE: type[JaxCPU] = JaxCPU

    # ---- (i) device model: target bound to the jax device family (D1 closed) ----------------
    def to_device(self, x: Tensor[Jax, Any, _D, _S], dev: type[_JDev]) -> Tensor[Jax, _JDev, _D, _S]:
        return _wrap(_jax.device_put(_a(x), _device(dev)))

    # ---- (ii) dtype model ------------------------------------------------------------------
    def supports_dtype(self, dt: type[DType]) -> bool:
        return dt in _JNP_DTYPE

    def cast(self, x: Tensor[Jax, _Dev, Any, _S], dt: type[_D2]) -> Tensor[Jax, _Dev, _D2, _S]:
        return _wrap(_a(x).astype(_JNP_DTYPE[dt]))

    # ---- (iii) shape model -----------------------------------------------------------------
    def shape_kind(self) -> type[ShapeKind]:
        return Dyn

    # ---- (iv) entry/exit brands + bridge spine ---------------------------------------------
    def brand(self, raw: object, *, dev: type[_JDev], dt: type[_D2]) -> Tensor[Jax, _JDev, _D2, Dyn]:
        """Brand a raw `jax.Array` — `dev` is bound to `JaxDevice` (a jax object cannot be branded
        onto a torch device), and the actual dtype is VERIFIED against the claimed `dt`, raising on
        mismatch (a construction-time assertion). jax arrays carry a committed device."""
        arr = cast(_jax.Array, raw)
        want_dt = jnp.dtype(_JNP_DTYPE[dt])
        if arr.dtype != want_dt:
            raise TypeError(
                f"jax.brand: raw array dtype {arr.dtype} contradicts the claimed dtype tag "
                f"{dt.__name__} ({want_dt}). Cast explicitly with jax.cast(...) to change it.")
        return _wrap(arr)

    def unwrap(self, x: Tensor[Jax, Any, Any, Any]) -> object:
        return _a(x)

    def export_host(self, x: Tensor[Jax, JaxCPU, _D, _S]) -> Tensor[Numpy, Host, _D, _S]:
        # REAL device->host materialization (a genuine copy off the jax buffer to a numpy array).
        arr: _NDArr = np.asarray(_a(x))
        return _wrap(arr)

    def import_host(self, b: Tensor[Numpy, Host, _D, _S]) -> Tensor[Jax, JaxCPU, _D, _S]:
        # REAL host->jax handoff.
        return _wrap(jnp.asarray(cast(_NDArr, _unwrap(b))))

    # ============================ capability surface (per-library) ===========================
    def matmul(self, a: Tensor[Jax, _Dev, F32, _S], b: Tensor[Jax, _Dev, F32, _S]) -> Tensor[Jax, _Dev, F32, _S]:
        return _wrap(jnp.matmul(_a(a), _a(b)))

    def add(self, a: Tensor[Jax, _Dev, _D, _S], b: Tensor[Jax, _Dev, _D, _S]) -> Tensor[Jax, _Dev, _D, _S]:
        return _wrap(_a(a) + _a(b))

    def relu(self, a: Tensor[Jax, _Dev, F32, _S]) -> Tensor[Jax, _Dev, F32, _S]:
        return _wrap(jnp.maximum(_a(a), jnp.float32(0.0)))

    def sum(self, a: Tensor[Jax, _Dev, F32, _S], *, axis: int) -> Tensor[Jax, _Dev, F32, _S]:
        return _wrap(jnp.sum(_a(a), axis=axis))

    def gather(self, a: Tensor[Jax, _Dev, F32, _S], idx: Tensor[Jax, _Dev, I32, _S], *, axis: int) -> Tensor[Jax, _Dev, F32, _S]:
        # the GENERAL jax interpreter HAS gather (an advanced-index take). The lowerable-jax
        # adapter deliberately does NOT — that absence is the capability seam (§2.5).
        return _wrap(jnp.take(_a(a), _a(idx), axis=axis))


jax: Final = JaxAdapter()  # the singleton the demo imports as `jax`

_seam_check: LibAdapter[Jax, JaxCPU, JaxDevice] = jax
