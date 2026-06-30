#!/usr/bin/env python
"""nla_lab.lower.ops — THE combinator surface of the lowerable kernel algebra.

Every function here takes and returns `Tile` (or `Pow2`/host scalars), and its body is the
exact lowerable `jnp`/`pl` expression already proven in `_pallas_disent_attention`'s
`disent_flash_kernel`. The surface is CLOSED: it contains every Triton-lowerable op the
disentangled-flash kernel needs, and NOTHING else — no `gather`, no `take`, no `einsum`, no
`dot_general` with batch dims, no `.astype` on the carrier. That omission is the lib/dtype
closure (DESIGN.md §3/§4):

  * lib/gather    — there is no `gather`/`take` combinator; the sanctioned replacement is the
                    `band` (pl.ds slice) + `onehot` + `select` (broadcast-mul + sum) trio.
  * lib/einsum    — the only contraction is `dot` (2-D, batch-free `pl.dot`); a batched
                    `dot_general` (a shared-index einsum) is not expressible, and the
                    non-coercible carrier makes a raw `jnp.einsum(tile, …)` raise at trace.
  * dtype         — the ONLY `F32<->I32` crossings in the carrier VALUE-FLOW are `to_i32`/
                    `to_f32`; `bucket_index`'s `log`/`ceil` float result reaches an index ONLY
                    through an explicit, diff-visible `to_i32(...)` here — never a buried
                    `.astype` in the score/index math. (Two non-value-flow casts live inside a
                    single combinator each and are NOT F32<->I32 crossings: `onehot`'s bool->f32
                    that turns a comparison predicate into one-hot weights, and `store`'s cast to
                    the output ref's dtype at the kernel write boundary. Both are construction/
                    boundary, diff-visible in their combinator, not silent in the value flow.)
  * device        — a host scalar cannot be a device tile-value (`add(t, 1)` is a type error),
                    and a raw host `jax.Array` cannot enter a kernel-boundary load (`load`/`band`/
                    `store`/`load_block*` demand a `Ref`; the single host-array->device-ref
                    crossing is the explicit `ref(...)` brand). The import-XOR FILE gate enforces
                    the residence class (`jax.Array` carries no residence tag to type); see §4.device.
  * shape         — every shape-fixing dim is a `Pow2`; the 2S-1 trap is unconstructable.

"Folding" is degenerate and eager: each combinator unwraps its `Tile`(s) to the backing
`jax.Array`, calls the proven `jnp`/`pl` expression, and rewraps. Composing combinators
builds an ordinary jaxpr of only lowerable primitives, handed to `pl.pallas_call` — Pallas
lowers it and XLA fuses it. No Triton emission, no `triton.compile`, no `jax.ffi`.

HOST-XOR-DEVICE. Imports jax/jnp/pallas + jax_deberta (the bucket SSOT); never numpy. Authors
no host<->device transfer (no device_get/asarray/array): the refs it loads from are already
device-resident, and every constructor uses `jnp.zeros`/`jnp.full`/`jnp.arange`. Device-only.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

import jax
import jax.numpy as jnp
from jax.experimental import pallas as pl

import jax_deberta  # the SSOT of the log-bucket arithmetic (make_log_bucket_position); device-only

from nla_lab.lower.dtype import BoolT, DType, F32, I32
from nla_lab.lower.shape import Pow2
from nla_lab.lower.tile import Idx, Ref, Tile, _arr, _wrap

D = TypeVar("D", bound=DType)


# ============================================================ dtype dispatch (phantom -> jnp)
def _jnp_dtype(tag: type[DType]) -> Any:
    """Map a phantom dtype tag (`F32`/`I32`/`BoolT`) to its jnp dtype. The ONLY place the
    phantom tag becomes a concrete numeric dtype — the constructors' single dispatch."""
    if tag is F32:
        return jnp.float32
    if tag is I32:
        return jnp.int32
    if tag is BoolT:
        return jnp.bool_
    raise TypeError(f"not a lowerable dtype tag: {tag!r}")


# ============================================================ kernel-boundary device coordinates
# Grid program ids and the inner loop counter are DEVICE control scalars. They enter the
# algebra as 0-d `Idx` tiles through these two named lifts (analogous to `load`/`band`), so
# the rest of the kernel composes Tiles only — never a raw device scalar in the value flow.
def pid(axis: int) -> Idx:
    """The grid program id along `axis`, as a 0-d index tile (`pl.program_id`)."""
    return _wrap(pl.program_id(axis))


def as_index(x: jax.Array) -> Idx:
    """Lift a device int scalar (the `fori_loop` counter) into a 0-d `Idx`. The one boundary
    where a raw device control value enters the algebra."""
    return _wrap(x)


def ref(x: jax.Array) -> Ref:
    """Brand a `pl.pallas_call` kernel argument as a device memory `Ref` — the single, explicit,
    diff-visible host-array -> device-ref crossing (the device-seam analog of `to_i32`). The
    boundary loaders/stores (`load`/`band`/`store`/`load_block*`) demand a `Ref`, so a raw host
    `jax.Array` cannot slide into a kernel boundary un-branded: that is a mypy error. This is a
    boundary ASSERTION ("this array is a device kernel ref"), not a residence proof — `jax.Array`
    carries no residence tag; the import-XOR file gate enforces the residence class (DESIGN.md §4.device)."""
    return Ref(x)


# ============================================================ constructors (shape dims are Pow2)
def zeros(rows: Pow2, cols: Pow2, dtype: type[D]) -> Tile[D]:
    """A `[rows, cols]` zero tile of the given phantom dtype (e.g. the running numerator acc)."""
    return _wrap(jnp.zeros((rows, cols), _jnp_dtype(dtype)))


def full(rows: Pow2, value: float) -> Tile[F32]:
    """A `[rows]` float32 tile filled with `value` (e.g. the running max init = -inf)."""
    return _wrap(jnp.full((rows,), value, jnp.float32))


def full2(rows: Pow2, cols: Pow2, value: float) -> Tile[F32]:
    """A `[rows, cols]` float32 tile filled with `value` (e.g. the masked-fill `neg` tile).

    The 2-D companion of `full` — the masked-softmax select needs a `[block_q, block_k]`
    constant, which `full` (1-D) does not size. Same constructor family, one dim wider.
    """
    return _wrap(jnp.full((rows, cols), value, jnp.float32))


def iota(n: Pow2) -> Idx:
    """`[n]` index tile `[0, 1, …, n-1]` (`jnp.arange`)."""
    return _wrap(jnp.arange(n, dtype=jnp.int32))


def load(r: Ref, *dims: Pow2) -> Tile[F32]:
    """Load the leading-block tile `r[0]` at the kernel boundary (q rows, the query mask).
    `dims` are the `Pow2` shape contract of the loaded tile (documentary; the load is `r[0]`).
    `r` is a `Ref` (device-branded via `ops.ref`) — a raw host `jax.Array` is a mypy error."""
    del dims  # the Pow2 shape contract is the caller's; the body is the fixed r[0] load
    return _wrap(r[0])


def load_block(r: Ref, start: Idx, length: Pow2) -> Tile[F32]:
    """Load a 2-D `[length, d]` tile sliced at device offset `start` (`pl.ds`): the k/v key tile."""
    return _wrap(r[0, pl.ds(_arr(start), length), :])


def load_block_1d(r: Ref, start: Idx, length: Pow2) -> Tile[F32]:
    """Load a 1-D `[length]` tile sliced at device offset `start` (`pl.ds`): the key mask tile."""
    return _wrap(r[0, pl.ds(_arr(start), length)])


# ============================================================ elementwise arithmetic
def add(a: Tile[D], b: Tile[D]) -> Tile[D]:
    return _wrap(_arr(a) + _arr(b))


def sub(a: Tile[D], b: Tile[D]) -> Tile[D]:
    return _wrap(_arr(a) - _arr(b))


def mul(a: Tile[D], b: Tile[D]) -> Tile[D]:
    """Elementwise product; broadcasting allowed (interpret-checked)."""
    return _wrap(_arr(a) * _arr(b))


def div(a: Tile[D], b: Tile[D]) -> Tile[D]:
    """Elementwise quotient (the final acc / denom normalize)."""
    return _wrap(_arr(a) / _arr(b))


def mul_scalar(a: Tile[F32], s: float) -> Tile[F32]:
    """Float32 tile times a host float. F32-only by design: a generic `Tile[D]*float` would
    silently produce a float result under an `I32` brand — exactly the dtype coercion the
    seam forbids. Integer scalar arithmetic is `imul_scalar`/`iadd_scalar`."""
    return _wrap(_arr(a) * s)


def div_scalar(a: Tile[F32], s: float) -> Tile[F32]:
    """Float32 tile divided by a host float (e.g. the disentangled `(c2p+p2c)/scale`). F32-only
    for the same dtype-seam reason as `mul_scalar`."""
    return _wrap(_arr(a) / s)


def iadd_scalar(a: Idx, s: int) -> Idx:
    """Index tile plus a host int (stays `I32`): the band-base/offset index arithmetic."""
    return _wrap(_arr(a) + s)


def imul_scalar(a: Idx, s: int) -> Idx:
    """Index tile times a host int (stays `I32`): grid/loop offsets `qt*block_q`, `kt*block_k`."""
    return _wrap(_arr(a) * s)


# ============================================================ transcendental / index arithmetic
def exp(a: Tile[F32]) -> Tile[F32]:
    return _wrap(jnp.exp(_arr(a)))


def sign(a: Tile[F32]) -> Tile[F32]:
    return _wrap(jnp.sign(_arr(a)))


def abs_(a: Tile[F32]) -> Tile[F32]:
    return _wrap(jnp.abs(_arr(a)))


def log(a: Tile[F32]) -> Tile[F32]:
    """Natural log. HOST-UNVERIFIED LOWERING (sm_75): whether `jnp.log` has a Triton lowering
    rule on Turing is a host-only `lib`-axis unknown (DESIGN.md §4.dtype residual), filed not
    claimed — it is an ordinary primitive, not `gather`/batched-`dot`."""
    return _wrap(jnp.log(_arr(a)))


def ceil(a: Tile[F32]) -> Tile[F32]:
    """Ceil. HOST-UNVERIFIED LOWERING (sm_75) — see `log`."""
    return _wrap(jnp.ceil(_arr(a)))


def clip(a: Idx, lo: int, hi: int) -> Idx:
    """Clamp an index tile to `[lo, hi]` (the band base / bucket-column clamp)."""
    return _wrap(jnp.clip(_arr(a), lo, hi))


# ============================================================ compare / select
def gt(a: Tile[D], b: Tile[D]) -> Tile[BoolT]:
    return _wrap(_arr(a) > _arr(b))


def eq(a: Idx, b: Idx) -> Tile[BoolT]:
    return _wrap(_arr(a) == _arr(b))


def where(c: Tile[BoolT], a: Tile[D], b: Tile[D]) -> Tile[D]:
    return _wrap(jnp.where(_arr(c), _arr(a), _arr(b)))


# ============================================================ reductions
def rmax(a: Tile[F32], axis: int) -> Tile[F32]:
    return _wrap(jnp.max(_arr(a), axis=axis))


def rsum(a: Tile[D], axis: int) -> Tile[D]:
    return _wrap(jnp.sum(_arr(a), axis=axis))


# ============================================================ broadcasts (replace [:,None]/[None,:])
def bcast_row(a: Tile[D]) -> Tile[D]:
    """`a[:, None]` — a trailing singleton (a column vector / row-indexed broadcast)."""
    return _wrap(_arr(a)[:, None])


def bcast_col(a: Tile[D]) -> Tile[D]:
    """`a[None, :]` — a leading singleton (a row vector / col-indexed broadcast)."""
    return _wrap(_arr(a)[None, :])


# ============================================================ the ONLY contraction (lib seam)
def transpose(a: Tile[D]) -> Tile[D]:
    """2-D transpose (the `k.T` in the content `q·kᵀ`)."""
    return _wrap(_arr(a).T)


def dot(a: Tile[F32], b: Tile[F32]) -> Tile[F32]:
    """`pl.dot` — the 2-D, batch-free matmul, the ONLY contraction. There is deliberately no
    batched/einsum variant: a shared-index contraction (the Pallas-Triton `batch_dims==((),())`
    wall) is not expressible through this surface (DESIGN.md §4.lib)."""
    return _wrap(pl.dot(_arr(a), _arr(b)))


# ============================================================ the gather replacement (lib seam)
def band(r: Ref, bh: Idx, row0: Idx, rows: Pow2, base: Idx, width: Pow2) -> Tile[F32]:
    """The `pl.ds` BAND slice that replaces the c2p/p2c advanced-index gather (the sm_75
    `Unimplemented primitive ... gather` wall). `r[bh, ds(row0, rows), ds(base, width)]`:
    a `[rows, width]` contiguous band of the global-memory position buffer. No `gather`."""
    return _wrap(r[_arr(bh), pl.ds(_arr(row0), rows), pl.ds(_arr(base), width)])


def onehot(sel: Idx, width: Pow2) -> Tile[F32]:
    """`(arange(width) == sel[..., None])` as float32 — the one-hot over the band's W axis that
    selects, by comparison-sum, the gathered column. No `gather`."""
    eqs = jnp.arange(width, dtype=jnp.int32) == jnp.expand_dims(_arr(sel), -1)
    return _wrap(eqs.astype(jnp.float32))


def select(band_: Tile[F32], onehot_: Tile[F32], *, row_axis: int) -> Tile[F32]:
    """Reduce `band[row, sel]` as a BROADCAST-MULTIPLY + sum over the band's W axis — NOT
    `jnp.einsum`. The einsum form "iw,ijw->ij" shares index i across both operands AND the
    output, so jax lowers it to a BATCHED `dot_general` that Pallas-Triton asserts against
    (`batch_dims==((),())`); broadcasting the `[rows, W]` band against the `[bq, bk, W]`
    one-hot and summing W is the same value with zero `dot_general`.

    `row_axis` says which of the one-hot's two leading axes the band's row axis aligns to
    (0 for c2p — query rows; 1 for p2c — key rows); the singleton is inserted at the OTHER
    axis. A single `axis` cannot disambiguate when `block_q == block_k` (the chosen tiles!),
    so the alignment is explicit — the smallest gap filled past DESIGN.md §3's `select(…, axis)`.
    """
    expand_at = 1 if row_axis == 0 else 0
    return _wrap(jnp.sum(jnp.expand_dims(_arr(band_), expand_at) * _arr(onehot_), axis=-1))


# ============================================================ the EXPLICIT dtype casts (dtype seam)
def to_i32(x: Tile[F32]) -> Idx:
    """The ONLY `F32 -> I32` crossing in the whole package (the dtype-seam single home)."""
    return _wrap(_arr(x).astype(jnp.int32))


def to_f32(x: Idx) -> Tile[F32]:
    """The ONLY `I32 -> F32` crossing in the whole package."""
    return _wrap(_arr(x).astype(jnp.float32))


# ============================================================ the bucket column index
def bucket_index(
    rel: Idx, *, position_buckets: int, max_relative_positions: int, span: int, two_span: int,
) -> Idx:
    """The disentangled bucket COLUMN index `clip(BUCKET(rel) + span, 0, two_span-1)` as pure
    arithmetic — the in-kernel replacement for the precomputed `idx1d` gather table, expressed
    in the algebra. Reuses `jax_deberta.make_log_bucket_position` (ADR-0012 P1, the bucket's ONE
    home), so the value is byte-for-byte the retired `_bucket_index`.

    The `log`/`ceil` float result reaches the integer index through an EXPLICIT `to_i32(...)`
    — the dtype-seam single home, diff-visible here, never a buried `.astype` (the smell that
    was flagged). Elementwise on any shape: the `[block_q, block_k]` offset tile AND a 0-d
    band-base offset both flow through unchanged.
    """
    if position_buckets > 0 and max_relative_positions > 0:
        # make_log_bucket_position is sign/abs/where/log/ceil -> a FLOAT tile (the log path).
        logf: Tile[F32] = _wrap(
            jax_deberta.make_log_bucket_position(_arr(rel), position_buckets, max_relative_positions))
        idx = to_i32(logf)                      # <- THE explicit float->int (dtype seam), visible
    else:
        idx = rel                               # short-seq identity branch: already I32
    return clip(iadd_scalar(idx, span), 0, two_span - 1)


# ============================================================ the store boundary
def store(r: Ref, value: Tile[F32]) -> None:
    """Mirror of `load`: write the result tile back to the leading-block output `Ref`, cast to
    the ref's dtype (the kernel WRITE boundary — `o_ref[0] = (acc/l)`). The `.astype(r.dtype)` is
    the output-boundary cast, internal to this one combinator (DESIGN.md §4.dtype) — not a silent
    value-flow F32<->I32 crossing."""
    r[0] = _arr(value).astype(r.dtype)


# ============================================================ the bounded fold (control flow)
# The running (max, denom, numerator) carry, the kernel's `Tile` state across key tiles.
_F3 = tuple[Tile[F32], Tile[F32], Tile[F32]]


def fold_kt(n: int, init: _F3, body: Callable[[Idx, Tile[F32], Tile[F32], Tile[F32]], _F3]) -> _F3:
    """The bounded key-tile fold (the online-softmax accumulation) — the ONLY control-flow
    combinator. `body(kt, m, l, acc) -> (m, l, acc)` for `kt` in `[0, n)`, `n = cdiv(S, block_k)`.

    This is why `Tile` is NOT a jax pytree (DESIGN.md §4 / tile.py): the wrap<->unwrap stays
    INSIDE `lower/` here — the jax `fori_loop` carry is the RAW backing arrays, and `body` only
    ever sees/returns Tiles. So a `Tile` is an opaque pytree leaf everywhere else, and the
    `tree_map`-rewrap re-entry vector (HIGH-2) simply does not exist. `n`/`kt` are device control
    scalars (the fold bound and counter), not impedance math — `fori_loop` stays raw."""
    a0, b0, c0 = _arr(init[0]), _arr(init[1]), _arr(init[2])

    def _raw(i: jax.Array, carry: tuple[jax.Array, jax.Array, jax.Array]
             ) -> tuple[jax.Array, jax.Array, jax.Array]:
        ra, rb, rc = carry
        om, ol, oacc = body(_wrap(i), _wrap(ra), _wrap(rb), _wrap(rc))
        return _arr(om), _arr(ol), _arr(oacc)

    fa, fb, fc = jax.lax.fori_loop(0, n, _raw, (a0, b0, c0))
    return _wrap(fa), _wrap(fb), _wrap(fc)
