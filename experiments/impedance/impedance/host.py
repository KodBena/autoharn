#!/usr/bin/env python
"""impedance.host — the single host interchange + the bridge spine (why adding a library is O(1)).

The naive cross-library design writes a bridge per ordered pair — O(n²), and adding a library
means writing n new bridges, breaking the "ONE adapter" promise. We refuse it. Every crossing
routes through a SINGLE canonical host interchange: the host carrier

    HostBuffer[D, S] := Tensor[Numpy, Host, D, S]

**numpy is the host adapter** — the natural, honest choice (numpy is *the* host SSOT). Each
adapter provides exactly TWO host-crossing operations, naming only itself and the host:

    export_host(x: Tensor[L, HostDev_L, D, S]) -> HostBuffer[D, S]   # pull L's value to host
    import_host(b: HostBuffer[D, S])            -> Tensor[L, HostDev_L, D, S]  # push host -> L

A cross-library move A -> B is then `B.import_host(A.export_host(x))` — composed from each
adapter's OWN two ops (the `bridge` below). Adding library X requires only X's
`export_host`/`import_host`; NO edit to any other adapter, NO pairwise matrix. Both ops PRESERVE
`D` and `S` in their signatures, so a bridge CANNOT silently change dtype or shape — the dtype
seam survives the crossing for free.

`Numpy` and `Host` are CORE marker tags (pure python, no numpy import), so this module — and
the adapter Protocol that references `Tensor[Numpy, Host, D, S]` — stay library-agnostic. The
numpy ADAPTER (`lib/numpy_lib.py`) imports numpy and brands its arrays with these core tags.

LIBRARY-AGNOSTIC. Imports NO numerical library (the `LibAdapter` reference is type-checking-only).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from impedance.dtype import DType
from impedance.shape import ShapeKind
from impedance.tensor import Tensor

if TYPE_CHECKING:  # bridge() is generic over LibAdapter at TYPE-CHECK time; at runtime it only
    # calls two methods, so the import is type-checking-only and there is NO runtime cycle
    # (adapter.py imports the Numpy/Host tags from here at runtime; we never import it back).
    from impedance.adapter import LibAdapter


# ---------------------------------------------------------------------- the host interchange tags
class Numpy:
    """Library tag: numpy — THE host interchange authority. The neutral library every bridge
    passes through. A core marker class (no numpy import); the numpy adapter brands with it."""


class Host:
    """Device tag: the neutral host (CPU main memory) — numpy's only residence. The one device
    `export_host`/`import_host` cross to/from."""


_D = TypeVar("_D", bound=DType)
_S = TypeVar("_S", bound=ShapeKind)

# The host interchange carrier: an opaque numpy-tagged, host-resident `Tensor`. It is a TYPED
# BRAND, not a raw `np.ndarray`, so it cannot leak back into a device adapter except through that
# adapter's `import_host`. (Zero-copy via dlpack is an adapter implementation detail behind the
# same two-op interface — the interface is the contract, the codec is private.)
HostBuffer = Tensor[Numpy, Host, _D, _S]


# ----------------------------------------------------------------------------- the bridge spine
_L1 = TypeVar("_L1")
_L2 = TypeVar("_L2")
_H1 = TypeVar("_H1")
_H2 = TypeVar("_H2")
_B1 = TypeVar("_B1")  # src adapter's device-family base (unused by the bridge, free)
_B2 = TypeVar("_B2")  # dst adapter's device-family base (unused by the bridge, free)
_Db = TypeVar("_Db", bound=DType)
_Sb = TypeVar("_Sb", bound=ShapeKind)


def bridge(
    src: "LibAdapter[_L1, _H1, _B1]",
    dst: "LibAdapter[_L2, _H2, _B2]",
    x: Tensor[_L1, _H1, _Db, _Sb],
) -> Tensor[_L2, _H2, _Db, _Sb]:
    """The cross-library move A -> B, composed from each adapter's OWN two host-crossing ops:
    `dst.import_host(src.export_host(x))`. The ONE place a cross-`L` handoff happens, and it is
    explicit, named, diff-visible, and dtype/shape-PRESERVING (the `_Db`/`_Sb` survive). `x`
    must already be on `src`'s host-side device `_H1` (that is `src.export_host`'s requirement —
    a device value must be `to_device`'d to the host side FIRST), so an un-transferred device
    crossing is unconstructable. Adding a new library needs zero edits here."""
    return dst.import_host(src.export_host(x))
