#!/usr/bin/env python
"""impedance.lib.sklearn_lib — the OPTIONAL 5th adapter (host-family, over numpy carriers).

Like scipy, scikit-learn computes on numpy host arrays — it owns no array type or device. So its
adapter is a CAPABILITY SURFACE over `Tensor[Numpy, Host, D, S]`, NOT a full `LibAdapter`. It is
the worked demonstration of the package's O(1)-per-library promise: ADDING A LIBRARY IS ADDING
ONE FILE — this one — with zero edits to the core, the host bridge, or any other adapter.

It is OPTIONAL and is deliberately NOT imported by `impedance.lib.__init__`, so `import
impedance.lib` never requires scikit-learn; a consumer imports it explicitly
(`from impedance.lib.sklearn_lib import sklearn`), and the demo does not depend on it. The
jax/jaxlib pin is therefore never at risk from this adapter.

HOST-SIDE. Imports scikit-learn + numpy; operates entirely within the host carrier.
"""

from __future__ import annotations

from typing import Any, Final, TypeVar, cast

import numpy as np
from sklearn.preprocessing import normalize as _sk_normalize

from impedance.host import Host, Numpy
from impedance.shape import ShapeKind
from impedance.tensor import Tensor, _unwrap, _wrap
from impedance.dtype import F32

_S = TypeVar("_S", bound=ShapeKind)
_NDArr = np.ndarray[Any, np.dtype[Any]]


def _arr(t: Tensor[Any, Any, Any, Any]) -> _NDArr:
    return cast(_NDArr, _unwrap(t))


class SklearnAdapter:
    """scikit-learn capabilities over the numpy host carrier (no lib tag / no device / no bridge —
    it borrows numpy's). Adding this whole library was exactly this one file."""

    def l2_normalize(self, x: Tensor[Numpy, Host, F32, _S], *, axis: int = 1) -> Tensor[Numpy, Host, F32, _S]:
        out: _NDArr = _sk_normalize(_arr(x), norm="l2", axis=axis).astype(np.float32)
        return _wrap(out)


sklearn: Final = SklearnAdapter()  # import explicitly: `from impedance.lib.sklearn_lib import sklearn`
