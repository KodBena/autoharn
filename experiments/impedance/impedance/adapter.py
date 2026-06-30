#!/usr/bin/env python
"""impedance.adapter — THE STANDARDIZED ADAPTER SEAM (so adding a library is JUST writing one).

The adapter surface splits into TWO layers, and the split IS the answer to "the location/shape
of the adapter interface is standardized while every library is different":

  * The SEAM PROTOCOL (`LibAdapter`, here) — STANDARDIZED, identical for every library. It
    carries the *device model* (`HOST_DEVICE` + `to_device`), the *dtype model*
    (`supports_dtype` + `cast`), the *shape model* (`shape_kind`), and the *entry/exit brands +
    bridge spine* (`brand`/`unwrap`/`export_host`/`import_host`). It is a `typing.Protocol` (a
    structural typeclass) so an adapter satisfies it BY SHAPE, not by inheritance. Writing one
    class with these members is ALL that "adding a library" requires.

  * The CAPABILITY SURFACE — PER-LIBRARY, genuinely different, and deliberately NOT here. The
    math combinators (`add`/`matmul`/`relu`/`softmax`/`gather`/…) live on the concrete adapter
    class. This is the capability seam: capability sets DIFFER by adapter, and a missing
    capability is a mypy `[attr-defined]` (using an op the target adapter does not provide is
    unconstructable). The adapter DECLARES its capability set by *being a class whose methods
    are exactly its capabilities*.

Note what the Protocol pins and what it leaves open:
  - it pins the SHAPE OF EVERY CROSSING (`to_device`/`cast`/`brand`/`export_host`/`import_host`)
    so cross-library/-device/-dtype moves have ONE identical shape regardless of library — learn
    the seam once, it is the same for torch as for jax;
  - it pins LIB-MONOMORPHISM: every method's input and output carry `Lib`, so an adapter cannot
    even be WRITTEN to accept another library's tensor in a seam op;
  - it pins the DEVICE MODEL to the library's OWN device family via the third Protocol parameter
    `DevBase`: `to_device`/`brand` accept only `type[DevBase]`, so the device-residence tag is
    NOT FORGEABLE — a torch tensor cannot be typed onto a jax device (`torch.to_device(x, JaxGPU)`
    / `torch.brand(raw, dev=JaxCPU, …)` are mypy `[type-var]`). The device crossing is closed by
    construction, not asserted by prose; a concrete adapter narrows the family to ITS base (e.g.
    `_TDev = TypeVar(bound=TorchDevice)`) and the bound flows from this one parameter;
  - it pins DTYPE/SHAPE PRESERVATION across `export_host`/`import_host` (same `D`, same `S`),
    closing the dtype seam across the bridge by construction;
  - it does NOT enumerate capabilities — those are the concrete adapter's own methods.

LIBRARY-AGNOSTIC. Imports the core tags only; NO numerical library.
"""

from __future__ import annotations

from typing import Any, Protocol, TypeVar

from impedance.dtype import DType
from impedance.host import Host, Numpy
from impedance.shape import Dyn, ShapeKind
from impedance.tensor import Tensor

Lib = TypeVar("Lib")  # this adapter's library tag
HDev = TypeVar("HDev")  # this adapter's HOST-side device tag (the one the bridge crosses)
DevBase = TypeVar("DevBase")  # this adapter's DEVICE-FAMILY base (the bound on every device tag)

# method-level generics (free in the Protocol methods below)
_Dev = TypeVar("_Dev")  # a device-PRESERVING var (cast keeps residence; it never forges it)
_D = TypeVar("_D", bound=DType)
_D2 = TypeVar("_D2", bound=DType)
_S = TypeVar("_S", bound=ShapeKind)


class LibAdapter(Protocol[Lib, HDev, DevBase]):
    """The STANDARDIZED seam every library plugs into. Implement this — the four seam
    descriptors + the entry/exit/bridge ops — and you have an adapter. The capability
    combinators live on the concrete adapter class, NOT here (they differ per library).

    Parametrized by `Lib` (the library tag), `HDev` (the host-side device the bridge crosses),
    and `DevBase` (the library's device-family base — the bound on which device tags the device
    crossing ops accept). `DevBase` is what makes the device MODEL closed, not just device
    co-residence: a library's residence tags are exactly the subclasses of its `DevBase`, and
    `to_device`/`brand` refuse any other library's device tag at the type layer."""

    # ---- (i) DEVICE MODEL -------------------------------------------------------------------
    # The library's device family is the set of subclasses of its `DevBase`; `HOST_DEVICE` names
    # the one member `export_host`/`import_host` cross. `to_device` is the marked, in-library
    # transfer (the real `.cpu()`/`.to(...)`); it PINS `Lib` AND bounds its target to `DevBase`,
    # so you cannot move a torch tensor to a jax device (that is a *bridge*, not a transfer) NOR
    # type one as resident there — a foreign device tag is a mypy `[type-var]`. The forge the
    # critique named (a torch tensor typed onto a JaxGPU) is unconstructable, not disclosed.
    HOST_DEVICE: type[HDev]

    def to_device(self, x: Tensor[Lib, Any, _D, _S], dev: type[DevBase]) -> Tensor[Lib, DevBase, _D, _S]:
        ...

    # ---- (ii) DTYPE MODEL -------------------------------------------------------------------
    # `supports_dtype` is the declared dtype set; `cast` is the ONLY in-library D-change (the
    # named, diff-visible, single-home dtype event — the carrier exposes no `.astype`).
    def supports_dtype(self, dt: type[DType]) -> bool:
        ...

    def cast(self, x: Tensor[Lib, _Dev, Any, _S], dt: type[_D2]) -> Tensor[Lib, _Dev, _D2, _S]:
        ...

    # ---- (iii) SHAPE MODEL ------------------------------------------------------------------
    # The adapter's shape kind (`Dyn` or `Pow2` …). A `Pow2`-declaring adapter's constructors
    # take `Pow2` tensors / `Pow2Dim` dims; a `Dyn` adapter brands `Dyn`.
    def shape_kind(self) -> type[ShapeKind]:
        ...

    # ---- (iv) ENTRY/EXIT BRANDS + THE BRIDGE SPINE (the seam-crossing ops) -------------------
    # `brand`: raw native object -> ACL (the single host->ACL entry). Its `dev` is bounded to
    # `DevBase` (the device-model closure also covers entry — a torch object cannot be branded
    # onto a jax device), and it reads the object's runtime device/dtype and VERIFIES, raising
    # on mismatch — a construction-time assertion, honest, for the runtime FACT a type can't read.
    def brand(self, raw: object, *, dev: type[DevBase], dt: type[_D2]) -> Tensor[Lib, DevBase, _D2, Dyn]:
        ...

    # `unwrap`: ACL -> raw native object, at the exit boundary (the inverse of `brand`).
    def unwrap(self, x: Tensor[Lib, Any, Any, Any]) -> object:
        ...

    # the two host-crossing ops (the bridge spine — see host.py). They PRESERVE `D` and `S`.
    def export_host(self, x: Tensor[Lib, HDev, _D, _S]) -> Tensor[Numpy, Host, _D, _S]:
        ...

    def import_host(self, b: Tensor[Numpy, Host, _D, _S]) -> Tensor[Lib, HDev, _D, _S]:
        ...
