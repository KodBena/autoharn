#!/usr/bin/env python
"""impedance.lib.scipy_lib — the scipy adapter (host-family capabilities over numpy carriers).

scipy does NOT own an array type or a device: it computes on numpy host arrays. So its adapter is
deliberately NOT a full `LibAdapter` (it declares no library tag, no device model, no bridge of
its own). It is a CAPABILITY SURFACE over the host carrier `Tensor[Numpy, Host, D, S]` — a clean
demonstration that not every library needs the whole seam: a library that shares another's memory
model plugs in as capabilities over that library's carrier. The capability seam still holds — a
scipy op the surface does not provide is `[attr-defined]`, and its inputs/outputs are dtype/shape
pinned on the host carrier.

Every body is one real `scipy.special.*` call on the underlying numpy array; the result is held to
the carrier's `F32` tag honestly (scipy's special functions compute in float64, so the value is
downcast back to float32, exactly as a hand-written host path would have to).

HOST-SIDE. Imports scipy + numpy; operates entirely within the host carrier.
"""

from __future__ import annotations

from typing import Any, Final, TypeVar, cast

import numpy as np
from scipy import special as _special

from impedance.dtype import DType, F32
from impedance.host import Host, Numpy
from impedance.shape import ShapeKind
from impedance.tensor import Tensor, _unwrap, _wrap

_S = TypeVar("_S", bound=ShapeKind)
_D = TypeVar("_D", bound=DType)
_NDArr = np.ndarray[Any, np.dtype[Any]]


def _arr(t: Tensor[Any, Any, Any, Any]) -> _NDArr:
    return cast(_NDArr, _unwrap(t))


class ScipyAdapter:
    """scipy capabilities over the numpy host carrier. No lib tag / no device / no bridge — it
    borrows numpy's. The capability surface IS the scipy ops it exposes."""

    def softmax(self, x: Tensor[Numpy, Host, F32, _S], *, axis: int) -> Tensor[Numpy, Host, F32, _S]:
        out: _NDArr = _special.softmax(_arr(x), axis=axis).astype(np.float32)
        return _wrap(out)

    def logsumexp(self, x: Tensor[Numpy, Host, F32, _S], *, axis: int) -> Tensor[Numpy, Host, F32, _S]:
        out: _NDArr = np.asarray(_special.logsumexp(_arr(x), axis=axis)).astype(np.float32)
        return _wrap(out)


scipy: Final = ScipyAdapter()  # the singleton the demo imports as `scipy`
