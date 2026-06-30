#!/usr/bin/env python
"""impedance.lib.numpy_lib — the HOST adapter (numpy), and the interchange authority.

numpy is THE host SSOT: its carrier `Tensor[Numpy, Host, D, S]` is the neutral host buffer every
cross-library bridge passes through (see `host.py`). So this adapter's `export_host`/`import_host`
are (near-)identities — a numpy host array is already the interchange form. The interesting
adapters are the device ones (torch, jax), which transfer to/from THIS one.

The adapter is a pure interpreter object (no mutable state): a singleton `numpy` the demo imports
as `host`. Every capability body is ONE native numpy call wrapped `unwrap -> np.* -> _wrap`; we
add no math.

HOST-SIDE. Imports numpy (its one library); brands numpy arrays with the core `Numpy`/`Host` tags.
"""

from __future__ import annotations

from typing import Any, Final, TypeVar, cast

import numpy as np

from impedance.adapter import LibAdapter
from impedance.dtype import BoolT, DType, F32, F64, I32, I64
from impedance.host import Host, Numpy
from impedance.shape import Dyn, ShapeKind
from impedance.tensor import Tensor, _unwrap, _wrap

_NDArr = np.ndarray[Any, np.dtype[Any]]

_D = TypeVar("_D", bound=DType)
_D2 = TypeVar("_D2", bound=DType)
_S = TypeVar("_S", bound=ShapeKind)
_Dev = TypeVar("_Dev")  # device-PRESERVING (cast keeps residence; never forges it)
# numpy's device family is the single host residence `Host`; the device ops bound their target to
# it, so a numpy tensor cannot be typed onto a torch/jax device (the device model is closed —
# `numpy.to_device(x, TorchCUDA)` is a mypy [type-var], not a silent relabel onto a foreign tag).
_HDev = TypeVar("_HDev", bound=Host)

# the dtype model: which core tags numpy realizes, and to which numpy dtype.
_NP_DTYPE: Final[dict[type[DType], np.dtype[Any]]] = {
    F32: np.dtype(np.float32),
    F64: np.dtype(np.float64),
    I32: np.dtype(np.int32),
    I64: np.dtype(np.int64),
    BoolT: np.dtype(np.bool_),
}


def _arr(t: Tensor[Any, Any, Any, Any]) -> _NDArr:
    """Narrow the carrier's backing object to the numpy array this adapter knows it is."""
    return cast(_NDArr, _unwrap(t))


class NumpyAdapter:
    """The numpy adapter — satisfies `LibAdapter[Numpy, Host, Host]` structurally. Lib tag `Numpy`,
    sole device `Host` (which is also its device-family bound), shape kind `Dyn`. The host
    interchange authority."""

    # ---- (i) device model: numpy has exactly one device, Host ------------------------------
    HOST_DEVICE: type[Host] = Host

    def to_device(self, x: Tensor[Numpy, Any, _D, _S], dev: type[_HDev]) -> Tensor[Numpy, _HDev, _D, _S]:
        # numpy is host-only: there is nothing to transfer, and the target is BOUND to Host, so
        # this cannot relabel a numpy tensor onto a foreign device. The "transfer" is a re-brand
        # to Host (the value never moves); numpy's real residence is always Host.
        return _wrap(_arr(x))

    # ---- (ii) dtype model ------------------------------------------------------------------
    def supports_dtype(self, dt: type[DType]) -> bool:
        return dt in _NP_DTYPE

    def cast(self, x: Tensor[Numpy, _Dev, Any, _S], dt: type[_D2]) -> Tensor[Numpy, _Dev, _D2, _S]:
        # the ONLY in-library dtype change (the carrier has no `.astype`).
        return _wrap(_arr(x).astype(_NP_DTYPE[dt]))

    # ---- (iii) shape model -----------------------------------------------------------------
    def shape_kind(self) -> type[ShapeKind]:
        return Dyn

    # ---- (iv) entry/exit brands + bridge spine ---------------------------------------------
    def brand(self, raw: object, *, dev: type[_HDev], dt: type[_D2]) -> Tensor[Numpy, _HDev, _D2, Dyn]:
        """Brand a raw `np.ndarray` as a host tensor — `dev` is bound to `Host` (numpy's only
        residence; a foreign device tag is a mypy [type-var]), and the actual dtype is read and
        VERIFIED against the claimed `dt`, raising on mismatch (a construction-time assertion)."""
        arr = cast(_NDArr, raw)
        if dev is not Host:
            raise TypeError(f"numpy is host-only: brand dev must be Host, got {dev!r}")
        want = _NP_DTYPE[dt]
        if arr.dtype != want:
            raise TypeError(
                f"numpy.brand: raw array dtype {arr.dtype} contradicts the claimed dtype tag "
                f"{dt.__name__} ({want}). The brand asserts the runtime dtype; cast explicitly "
                f"with numpy.cast(...) to change it.")
        return _wrap(arr)

    def unwrap(self, x: Tensor[Numpy, Any, Any, Any]) -> object:
        return _arr(x)

    def export_host(self, x: Tensor[Numpy, Host, _D, _S]) -> Tensor[Numpy, Host, _D, _S]:
        # numpy IS the host: the interchange form is the value itself (a fresh brand, no copy).
        return _wrap(_arr(x))

    def import_host(self, b: Tensor[Numpy, Host, _D, _S]) -> Tensor[Numpy, Host, _D, _S]:
        return _wrap(_arr(b))

    # ============================ capability surface (per-library; not standardized) =========
    def add(self, a: Tensor[Numpy, Host, _D, _S], b: Tensor[Numpy, Host, _D, _S]) -> Tensor[Numpy, Host, _D, _S]:
        return _wrap(_arr(a) + _arr(b))

    def mul(self, a: Tensor[Numpy, Host, _D, _S], b: Tensor[Numpy, Host, _D, _S]) -> Tensor[Numpy, Host, _D, _S]:
        return _wrap(_arr(a) * _arr(b))

    def matmul(self, a: Tensor[Numpy, Host, F32, _S], b: Tensor[Numpy, Host, F32, _S]) -> Tensor[Numpy, Host, F32, _S]:
        return _wrap(np.matmul(_arr(a), _arr(b)))

    def relu(self, a: Tensor[Numpy, Host, F32, _S]) -> Tensor[Numpy, Host, F32, _S]:
        return _wrap(np.maximum(_arr(a), np.float32(0.0)))

    def sum(self, a: Tensor[Numpy, Host, F32, _S], *, axis: int) -> Tensor[Numpy, Host, F32, _S]:
        return _wrap(np.sum(_arr(a), axis=axis))


numpy: Final = NumpyAdapter()  # the singleton the demo imports as `host`

# Force mypy to verify the standardized seam is satisfied (a structural Protocol conformance
# gate — if a seam method drifts, this assignment fails `mypy --strict`). Device family: Host.
_seam_check: LibAdapter[Numpy, Host, Host] = numpy
