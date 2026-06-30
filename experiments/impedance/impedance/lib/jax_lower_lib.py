#!/usr/bin/env python
"""impedance.lib.jax_lower_lib — `nla_lab/lower` lifted to ONE parametric adapter (L = JaxLower).

This is the package's centerpiece lift: the committed tagless-final four-seam closure
`nla_lab/lower` (instantiated for jax/Pallas) BECOMES one adapter here, with its single implicit
library made an explicit tag `JaxLower`. The mapping is the mechanical §3.3 table:

    nla_lab/lower (one implicit interpreter)        impedance (this adapter, L = JaxLower)
    --------------------------------------------    -------------------------------------------
    Tile[D]  (carrier)                              Tensor[JaxLower, JaxCPU, D, Pow2]
    Tile non-coercible / -constructable / no-pytree kept VERBATIM on Tensor (core)
    ops.py free functions (add/dot/onehot/select/…) the CAPABILITY methods of this adapter
    the CLOSED surface (no gather/einsum/astype)    the capability set — gather ABSENT => [attr-defined]
    Pow2 shape SSOT (shape.py)                       this adapter declares shape_kind() == Pow2
    to_i32 / to_f32 (the only dtype crossings)       this adapter's `cast` (the standardized dtype op)
    Ref brand + ops.ref()                            this adapter's `brand` (the standardized entry op)

Two things this lift CLARIFIES, implicit in nla_lab/lower:
  1. "Lowerable-only" is a property of an ADAPTER, not of jax. nla_lab constrained *jax* to
     lowerable ops by hand-curating one `ops.py`; that is just ONE jax adapter (this one) whose
     capability set excludes `gather`/`einsum`. The GENERAL jax adapter (`jax_lib.py`) exposes
     `gather` — and the capability seam (§2.5) keeps a `JaxLower` tensor from wandering into it.
  2. The device seam is genuinely stronger here: nla_lab could only `Ref`-brand (stock jax.Array
     carries no residence tag); in this parametric carrier `Dev` is a real phantom, so in-flow
     residence is type-closed, the device MODEL is closed (the device-crossing ops bound their
     target to `JaxDevice`), and the brand-as-assertion honesty is confined to the entry.

COMPOSES THROUGH THE BRIDGE (`as_pow2`). The lowerable surface is `Pow2`-only, but `import_host`/
`brand` necessarily yield `Dyn` (a host buffer carries no static pow2 proof). `as_pow2` is the
checked `Dyn -> Pow2` promotion — the honest construction-raise dual of `pow2()` — so external
host data CAN enter this adapter and be used: `jax_lower.as_pow2(bridge(host, jax_lower, nh))`.
The demo (`demo/pipeline.py`) routes a real torch->host->jax_lower->jax line through it, so the
centerpiece adapter is exercised by the cross-library demo, not only its own parity test.

STANDALONE / VALUE-FIDELITY (an honest spec reconciliation, ADR-0013 Rule 2 + ADR-0000). DESIGN
§3.3 also proposes a pytest asserting value-identity to the *committed nla_lab/lower* on the
disentangled-flash fixture. That would require importing `nla_lab` + `jax_deberta` — which
violates §6's load-bearing STANDALONE extraction bar (this package must run with ZERO reference
to fact-mining internals, "its own repo on day one"). The higher-priority ratified requirement
(standalone SSOT for repo promotion) governs: this adapter reproduces the nla_lab combinator
DISCIPLINE verbatim (Pow2 dims, no gather, `cast` as the only dtype crossing, the band/onehot/
select gather-replacement), and `tests/test_jax_lower_parity.py` proves each combinator is
value-identical to its raw-`jnp` expression — the same fidelity, self-contained. "Folding" is
degenerate eager interpretation (each combinator IS its proven `jnp` expression), exactly as
nla_lab/lower §6 states; under Pallas those same expressions lower, here they run under jax.

HOST boundary: imports jax/jnp + numpy (its export/import seam). The sanctioned boundary.
"""

from __future__ import annotations

from typing import Any, Final, TypeVar, cast

import jax
import jax.numpy as jnp
import numpy as np

from impedance.adapter import LibAdapter
from impedance.dtype import BoolT, DType, F32, I32
from impedance.host import Host, Numpy
from impedance.lib.jax_lib import JaxCPU, JaxDevice
from impedance.shape import Dyn, Pow2, Pow2Dim, ShapeKind, pow2
from impedance.tensor import Tensor, _unwrap, _wrap

_D = TypeVar("_D", bound=DType)
_D2 = TypeVar("_D2", bound=DType)
_S = TypeVar("_S", bound=ShapeKind)
_Dev = TypeVar("_Dev")  # device-PRESERVING (cast keeps residence; never forges it)
# device family: this kernel interpreter resides on the jax device family (it reuses `JaxCPU`);
# the device-crossing ops bound their target to `JaxDevice`, closing the device model (D1).
_JLDev = TypeVar("_JLDev", bound=JaxDevice)
_NDArr = np.ndarray[Any, np.dtype[Any]]


class JaxLower:
    """Library tag: the LOWERABLE-jax interpreter (the nla_lab/lower algebra, parametric). A
    marker class unrelated to `Jax` — so a `JaxLower` tensor is type-distinct from a general
    `Jax` tensor, which is what keeps the lowerable surface closed."""


# this adapter is single-device (a kernel interpreter): it resides on JaxCPU (the host-side
# interpret device). It reuses `JaxCPU` from jax_lib (one home for the jax device family).
_JLB_DTYPE: Final[dict[type[DType], Any]] = {F32: jnp.float32, I32: jnp.int32, BoolT: jnp.bool_}


def _a(x: Tensor[Any, Any, Any, Any]) -> jax.Array:
    return cast(jax.Array, _unwrap(x))


# convenient phantom aliases for this adapter's carriers (all Pow2-shaped, JaxCPU-resident)
_FTile = Tensor[JaxLower, JaxCPU, F32, Pow2]
_ITile = Tensor[JaxLower, JaxCPU, I32, Pow2]
_BTile = Tensor[JaxLower, JaxCPU, BoolT, Pow2]


class JaxLowerAdapter:
    """The lowerable-jax adapter — satisfies `LibAdapter[JaxLower, JaxCPU, JaxDevice]`. Shape model
    `Pow2`. Its capability surface is the nla_lab/lower `ops` set; it has NO `gather`/`einsum`/`take`."""

    HOST_DEVICE: type[JaxCPU] = JaxCPU

    # ---- (i) device model: target bound to the jax device family (D1 closed) ----------------
    def to_device(self, x: Tensor[JaxLower, Any, _D, _S], dev: type[_JLDev]) -> Tensor[JaxLower, _JLDev, _D, _S]:
        return _wrap(jax.device_put(_a(x), jax.devices("cpu")[0]))

    # ---- (ii) dtype model: `cast` is the ONLY dtype crossing (== nla_lab to_i32/to_f32) -----
    def supports_dtype(self, dt: type[DType]) -> bool:
        return dt in _JLB_DTYPE

    def cast(self, x: Tensor[JaxLower, _Dev, Any, _S], dt: type[_D2]) -> Tensor[JaxLower, _Dev, _D2, _S]:
        return _wrap(_a(x).astype(_JLB_DTYPE[dt]))

    # ---- (iii) shape model: this adapter DECLARES Pow2 -------------------------------------
    def shape_kind(self) -> type[ShapeKind]:
        return Pow2

    # ---- (iv) entry/exit brands + bridge spine ---------------------------------------------
    def brand(self, raw: object, *, dev: type[_JLDev], dt: type[_D2]) -> Tensor[JaxLower, _JLDev, _D2, Dyn]:
        arr = cast(jax.Array, raw)
        want = jnp.dtype(_JLB_DTYPE[dt])
        if arr.dtype != want:
            raise TypeError(
                f"jax_lower.brand: raw array dtype {arr.dtype} contradicts the claimed dtype tag "
                f"{dt.__name__} ({want}).")
        return _wrap(arr)

    def unwrap(self, x: Tensor[JaxLower, Any, Any, Any]) -> object:
        return _a(x)

    def export_host(self, x: Tensor[JaxLower, JaxCPU, _D, _S]) -> Tensor[Numpy, Host, _D, _S]:
        out: _NDArr = np.asarray(_a(x))
        return _wrap(out)

    def import_host(self, b: Tensor[Numpy, Host, _D, _S]) -> Tensor[JaxLower, JaxCPU, _D, _S]:
        return _wrap(jnp.asarray(cast(_NDArr, _unwrap(b))))

    # ---- (iii.b) shape-model ENTRY: the checked Dyn -> Pow2 promotion ------------------------
    # This is the honest construction-raise DUAL of `pow2()`, and the op that lets EXTERNAL data
    # enter the lowerable adapter: `brand`/`import_host` yield `Dyn` (a host buffer's kind), but
    # every capability below demands `Pow2`. Without a promotion, no bridged value could ever be
    # used here (the D2 defect: the centerpiece adapter was bridge-isolated). `as_pow2` reads the
    # runtime shape and brands `Pow2` ONLY if every dim is a power of two (via `pow2()`, which
    # raises the 2S-1 trap otherwise) — the same posture as `brand` (assert the runtime FACT a
    # type cannot read), here for the shape-kind axis. So `jax_lower.as_pow2(bridge(host, jax_lower,
    # nh))` is the natural, type-safe entry the demo's kernel leg uses.
    def as_pow2(self, x: Tensor[JaxLower, JaxCPU, _D, Dyn]) -> Tensor[JaxLower, JaxCPU, _D, Pow2]:
        arr = _a(x)
        for d in arr.shape:
            pow2(int(d))  # raises ValueError on any non-power-of-2 dim — the honest entry assertion
        return _wrap(arr)

    # ============================ capability surface (the nla_lab/lower `ops`) ===============
    # constructors — every shape-fixing dim is a Pow2Dim (the shape seam: a raw int is [arg-type],
    # and pow2() raises on a runtime non-pow2 — e.g. the 2S-1 trap).
    def zeros(self, rows: Pow2Dim, cols: Pow2Dim, dtype: type[_D]) -> Tensor[JaxLower, JaxCPU, _D, Pow2]:
        return _wrap(jnp.zeros((rows, cols), _JLB_DTYPE[dtype]))

    def full(self, n: Pow2Dim, value: float) -> _FTile:
        return _wrap(jnp.full((n,), value, jnp.float32))

    def iota(self, n: Pow2Dim) -> _ITile:
        return _wrap(jnp.arange(n, dtype=jnp.int32))

    def ramp2(self, rows: Pow2Dim, cols: Pow2Dim) -> _FTile:
        """A deterministic `[rows, cols]` F32 tile, `ramp2[i,j] = i*cols + j` — distinct values,
        for parity-checking the gather-replacement. Built from `arange`, no gather."""
        r = jnp.arange(rows, dtype=jnp.int32)[:, None] * cols + jnp.arange(cols, dtype=jnp.int32)[None, :]
        return _wrap(r.astype(jnp.float32))

    # elementwise / arithmetic (D-preserving; the dtype seam pins D across operands)
    def add(self, a: Tensor[JaxLower, JaxCPU, _D, Pow2], b: Tensor[JaxLower, JaxCPU, _D, Pow2]) -> Tensor[JaxLower, JaxCPU, _D, Pow2]:
        return _wrap(_a(a) + _a(b))

    def sub(self, a: Tensor[JaxLower, JaxCPU, _D, Pow2], b: Tensor[JaxLower, JaxCPU, _D, Pow2]) -> Tensor[JaxLower, JaxCPU, _D, Pow2]:
        return _wrap(_a(a) - _a(b))

    def mul(self, a: Tensor[JaxLower, JaxCPU, _D, Pow2], b: Tensor[JaxLower, JaxCPU, _D, Pow2]) -> Tensor[JaxLower, JaxCPU, _D, Pow2]:
        return _wrap(_a(a) * _a(b))

    def mul_scalar(self, a: _FTile, s: float) -> _FTile:
        return _wrap(_a(a) * s)

    def mod_scalar(self, a: _ITile, m: int) -> _ITile:
        return _wrap(_a(a) % m)

    def exp(self, a: _FTile) -> _FTile:
        return _wrap(jnp.exp(_a(a)))

    def transpose(self, a: Tensor[JaxLower, JaxCPU, _D, Pow2]) -> Tensor[JaxLower, JaxCPU, _D, Pow2]:
        return _wrap(_a(a).T)

    def dot(self, a: _FTile, b: _FTile) -> _FTile:
        """The ONLY contraction — 2-D, batch-free (the lib seam: no batched dot_general/einsum)."""
        return _wrap(jnp.matmul(_a(a), _a(b)))

    # compare / select
    def gt(self, a: Tensor[JaxLower, JaxCPU, _D, Pow2], b: Tensor[JaxLower, JaxCPU, _D, Pow2]) -> _BTile:
        return _wrap(_a(a) > _a(b))

    def where(self, c: _BTile, a: Tensor[JaxLower, JaxCPU, _D, Pow2], b: Tensor[JaxLower, JaxCPU, _D, Pow2]) -> Tensor[JaxLower, JaxCPU, _D, Pow2]:
        return _wrap(jnp.where(_a(c), _a(a), _a(b)))

    # reductions
    def rmax(self, a: _FTile, *, axis: int) -> _FTile:
        return _wrap(jnp.max(_a(a), axis=axis))

    def rsum(self, a: Tensor[JaxLower, JaxCPU, _D, Pow2], *, axis: int) -> Tensor[JaxLower, JaxCPU, _D, Pow2]:
        return _wrap(jnp.sum(_a(a), axis=axis))

    # the GATHER REPLACEMENT (the nla_lab centerpiece): band + one-hot + select. NO `gather`.
    def onehot(self, sel: _ITile, width: Pow2Dim) -> _FTile:
        """`(arange(width) == sel[:, None])` as f32 — the one-hot that selects a column by
        comparison-sum. No gather."""
        eqs = jnp.arange(width, dtype=jnp.int32) == jnp.expand_dims(_a(sel), -1)
        return _wrap(eqs.astype(jnp.float32))

    def select(self, band: _FTile, onehot: _FTile, *, axis: int) -> _FTile:
        """Reduce `band[row, sel]` as a BROADCAST-MULTIPLY + sum over the band's last axis —
        NOT einsum/gather. `out[i] = band[i, sel[i]]`."""
        return _wrap(jnp.sum(_a(band) * _a(onehot), axis=axis))

    # NOTE: there is deliberately NO `gather`, `take`, `einsum`, or `.astype`-on-carrier method.
    # That ABSENCE is the lib/capability closure: `jax_lower.gather(...)` is a mypy [attr-defined].


jax_lower: Final = JaxLowerAdapter()  # the singleton the demo imports as `jax_lower`

_seam_check: LibAdapter[JaxLower, JaxCPU, JaxDevice] = jax_lower
