#!/usr/bin/env python
"""nla_lab.lower — the proof that the four interface impedances are UNCONSTRUCTABLE.

This is the acceptance gate for the lowerable kernel algebra (nla_lab/lower/DESIGN.md). It
proves, per the SETTLED design's honest closure split (§4):

  * mypy-closed (the four seams, by TYPE) — `test_mypy_*`: a non-lowerable op (gather), a
    host/device mismatch, a silent dtype coercion, and a non-pow2 dim are each a mypy ERROR
    under `--strict` (cited verbatim). The ONE residual mypy cannot close — `jnp.einsum`'s
    `Any`-typed `*operands` — is shown to SLIP mypy (honestly), and is closed elsewhere:
  * construction-raise-closed — `test_construction_raise_*`: the non-coercible carrier makes
    a raw `jnp.einsum(tile, …)` / `jnp.sum(tile)` / `tile[idx]` RAISE (the value cannot be
    built), closing einsum at the construction surface the type surface leaves open.
  * the demoted jaxpr-walk (`_triton_acl.py`) — `test_walk_*`: the rejected runtime lint is a
    defense-in-depth REGRESSION (not the ACL): the algebra kernel's jaxpr is gather-free and
    batched-`dot_general`-free, and the walk still catches a deliberate gather escape.
  * fidelity unchanged — `test_bit_identity_*`: the algebra-ported kernel is BIT-IDENTICAL
    (max|Δ| == 0) to the pristine `disent_flash_kernel` oracle under `interpret=True`, so the
    EXACT ~1e-5 fold vs `exact_reference` (test_pallas_smem_budget.py) carries over untouched.

What is NOT claimed (ADR-0009 host-only): whether surface-legal `log`/`ceil`/fp32-`pl.dot`
actually lower and run on sm_75 Turing — measured on the 2080Ti, never asserted here.

Run:  python -m pytest -q nla_lab/test_pallas_lower_algebra.py   (from fact-mining/, CPU jax)
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from typing import Any

import jax
import jax.numpy as jnp
import pytest

from nla_lab.lower import ops, pow2
from nla_lab.lower.dtype import F32
from nla_lab.lower.shape import next_pow2
from nla_lab.variants._pallas_disent_attention import (
    disent_flash_kernel,
    disent_flash_kernel_algebra,
    pallas_disentangled_attention,
)
from nla_lab.variants._triton_acl import assert_triton_lowerable, triton_kernel_violations

jax.config.update("jax_platform_name", "cpu")  # type: ignore[no-untyped-call]  # jax.config untyped

# repo root (fact-mining/) — the MYPYPATH root and the home of nla_lab/mypy.ini.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MYPY_INI = os.path.join("nla_lab", "mypy.ini")

# synthetic disentangled dims (the synthetic_cfg rung: position_buckets=16, max_rel=64, span=16).
_POSITION_BUCKETS = 16
_MAX_REL = 64
_SPAN = 16
_TWO_SPAN = 2 * _SPAN


# ====================================================================== bit-identity (fidelity)
def _synthetic_inputs(bh: int, S: int, d: int) -> dict[str, jax.Array]:
    """Seeded random q/k/v + c2p/p2c position buffers + an all-real mask for the builder."""
    keys = jax.random.split(jax.random.PRNGKey(0), 5)
    return {
        "q": jax.random.normal(keys[0], (bh, S, d), jnp.float32),
        "k_scaled": jax.random.normal(keys[1], (bh, S, d), jnp.float32),
        "v": jax.random.normal(keys[2], (bh, S, d), jnp.float32),
        "c2p_full": jax.random.normal(keys[3], (bh, S, _TWO_SPAN), jnp.float32),
        "p2c_full": jax.random.normal(keys[4], (bh, S, _TWO_SPAN), jnp.float32),
        "am_bh": jnp.ones((bh, S), jnp.float32),
    }


def _run(kernel: Any, inp: dict[str, jax.Array], block: int) -> jax.Array:
    out = pallas_disentangled_attention(
        inp["q"], inp["k_scaled"], inp["v"], inp["c2p_full"], inp["p2c_full"], inp["am_bh"],
        scale=8.0, block_q=pow2(block), block_k=pow2(block),
        position_buckets=_POSITION_BUCKETS, max_relative_positions=_MAX_REL, span=_SPAN,
        interpret=True, kernel=kernel)
    return out


def test_bit_identity_algebra_vs_oracle_kernel() -> None:
    """The PORT changed HOW the kernel is constructed (every op a `lower.ops` combinator), not
    WHAT it computes: the algebra-ported `disent_flash_kernel_algebra` and the pristine oracle
    `disent_flash_kernel` produce the EXACT same context under `interpret=True` — max|Δ| == 0,
    not ~1e-7 (it is the identical jaxpr math, folded eagerly through the carrier). Covered at
    single-tile (S=32) and multi-tile (S=64,128 -> 2 and 4 block-32 tiles, the online-softmax
    rescale path). This is the contract that carries the EXACT ~1e-5 vs exact_reference over."""
    for bh, S, d in [(2, 32, 64), (2, 64, 64), (1, 128, 64)]:
        block = min(32, S)
        inp = _synthetic_inputs(bh, S, d)
        out_alg = _run(disent_flash_kernel_algebra, inp, block)
        out_ref = _run(disent_flash_kernel, inp, block)
        max_abs = float(jnp.max(jnp.abs(out_alg - out_ref)))
        assert max_abs == 0.0, f"(bh={bh},S={S}) algebra kernel != oracle, max|Δ|={max_abs}"


# ====================================================== the demoted jaxpr-walk (defense-in-depth)
def test_walk_algebra_kernel_is_jaxpr_clean() -> None:
    """The algebra kernel's `pallas_call` body is jaxpr-clean of the measured Pallas-Triton
    walls (no `gather`, no batched `dot_general`). The walk is DEMOTED from "the ACL" to this
    regression — it tests the carrier discipline, it is not the discipline (DESIGN.md §4.lib)."""
    inp = _synthetic_inputs(2, 64, 64)
    assert_triton_lowerable(  # raises if a wall is present; the algebra kernel has none
        lambda: _run(disent_flash_kernel_algebra, inp, 32))


def test_walk_still_catches_a_deliberate_gather() -> None:
    """Positive control (the belt over the suspenders is real): a hand-built `pallas_call` whose
    body does an advanced-index GATHER is flagged by the walk — so a clean walk on the algebra
    kernel is meaningful, not vacuous."""
    from jax.experimental import pallas as pl

    def gather_kernel(x_ref: jax.Array, idx_ref: jax.Array, o_ref: jax.Array) -> None:
        x = x_ref[...]                     # load the value, then ADVANCED-INDEX it ->
        o_ref[...] = x[idx_ref[...]]       # a `gather` primitive (the sm_75 wall)

    def build() -> Any:
        x = jnp.arange(8, dtype=jnp.float32)
        idx = jnp.array([0, 2, 4, 6], dtype=jnp.int32)
        return pl.pallas_call(
            gather_kernel,
            out_shape=jax.ShapeDtypeStruct((4,), jnp.float32),  # type: ignore[no-untyped-call]
            interpret=True)(x, idx)

    cj = jax.make_jaxpr(build)()
    viol = triton_kernel_violations(cj)
    assert any("gather" in v for v in viol), f"walk failed to flag the gather: {viol}"


# ============================================ construction-raise (the einsum residual + backstop)
def test_construction_raise_einsum_slips_mypy_but_raises_at_construction() -> None:
    """`jnp.einsum(tile, …)` SLIPS mypy (jax stubs type `*operands: Any` — see
    test_mypy_einsum_slips below), so it is closed at the CONSTRUCTION surface: the carrier is
    non-coercible (no `__array__`/`__jax_array__`), so `jnp.einsum` cannot build the value — it
    raises. This is the honest closure of the batched-`dot_general` residual (DESIGN.md §4.lib)."""
    a = ops.full(pow2(8), 1.0)        # a real Tile[F32] (eager, concrete backing array)
    b = ops.full(pow2(8), 1.0)
    with pytest.raises(Exception):    # asarray(Tile) -> no __array__ -> TypeError
        jnp.einsum("i,i->", a, b)     # the batched-shared-index form, on Tiles


def test_construction_raise_raw_jnp_on_tile() -> None:
    """The carrier backstop generalizes: ANY un-wrapped `jnp`/index op on a `Tile` raises (the
    value cannot re-enter the algebra except through an `ops` combinator)."""
    t = ops.full(pow2(8), 1.0)
    # these two lines are ALSO mypy errors (the type closure — proven in test_mypy_*); here we
    # exercise the RUNTIME backstop, so the expected static errors are silenced deliberately.
    with pytest.raises(Exception):
        jnp.sum(t)                    # type: ignore[arg-type]  # Tile is not ArrayLike
    with pytest.raises(Exception):
        _ = t[0]                      # type: ignore[index]  # Tile is not indexable


# ============================ CRITICAL-1: the carrier is non-constructable; no importable token
def test_no_importable_construction_token() -> None:
    """The earlier `_PRIV` single-underscore module token was importable, which let a caller mint
    an arbitrary, dtype-LYING `Tile` mypy-clean (the holed foundation). It is GONE: there is no
    construction token to import at all."""
    import nla_lab.lower.tile as _t
    for name in ("_PRIV", "_Priv"):
        assert not hasattr(_t, name), f"a construction token {name!r} is importable again — re-holed"
    with pytest.raises(ImportError):
        # the CRITICAL-1 import path is dead; mypy ALSO flags it (attr-defined), proving the
        # token name no longer exists statically — silenced here to exercise the RUNTIME raise.
        from nla_lab.lower.tile import _PRIV  # type: ignore[attr-defined]  # noqa: F401


def test_direct_tile_construction_raises() -> None:
    """`Tile(...)` from any caller raises: `__init__` is unconditional, and the ONLY mint path
    (`_wrap`, via `object.__new__`) is package-private and token-free. The lying-Tile that
    defeated lib+dtype+the einsum backstop in one line is now unconstructable."""
    from nla_lab.lower import Tile
    with pytest.raises(TypeError, match="no public constructor"):
        Tile()                                          # mypy-clean call, runtime TypeError
    with pytest.raises(TypeError):
        Tile(jnp.zeros(4, jnp.int32))                   # type: ignore[call-arg]  # no value params


def test_mypy_lying_tile_construction_is_a_type_error(tmp_path: Any) -> None:
    """The CRITICAL-1 reproduction, now a TYPE error (not just a runtime raise): importing the
    old token is `attr-defined`, and `Tile(arr, tok)` is `call-arg` (the ctor takes no value
    params). The mypy-clean lying-Tile one-liner no longer type-checks."""
    out = _run_mypy("lie.py", """
        import jax.numpy as jnp
        from nla_lab.lower import Tile
        from nla_lab.lower.dtype import F32
        from nla_lab.lower.tile import _PRIV       # the old token: gone

        def k() -> None:
            bad: Tile[F32] = Tile(jnp.zeros(4, jnp.int32)[jnp.array([0])], _PRIV)
            print(bad)
    """, tmp_path)
    assert 'Module "nla_lab.lower.tile" has no attribute "_PRIV"' in out   # token import is dead
    assert "[call-arg]" in out                                            # Tile(arr, tok): no params


def test_mypy_object_new_slot_write_is_a_type_error(tmp_path: Any) -> None:
    """The deserialization-shaped bypass `object.__new__(Tile); t._arr = <gather>` (mypy-clean
    in the first implementation) is now a mypy `[attr-defined]` error: the backing array sits in
    a NAME-MANGLED slot, so ordinary `t._arr`/`t._Tile__arr` attribute syntax does not type-check
    (and raises AttributeError at runtime). The only mypy-clean mint left is the `_wrap` brand —
    the Pow2-symmetric construction-tier residue, recorded honestly (test_construction_tier_mint_residue)."""
    out = _run_mypy("slot.py", """
        import jax.numpy as jnp
        from typing import Any
        from nla_lab.lower import Tile

        def k() -> None:
            a: Tile[Any] = object.__new__(Tile); a._arr = jnp.zeros(4)        # ordinary attr write
            b: Tile[Any] = object.__new__(Tile); b._Tile__arr = jnp.zeros(4)  # mangled attr write
    """, tmp_path)
    assert 'has no attribute "_arr"' in out                                # ordinary slot write: dead
    assert 'has no attribute "_Tile__arr"' in out                          # mangled slot write: dead


def test_construction_tier_mint_residue_is_pow2_symmetric() -> None:
    """HONEST RESIDUE (ADR-0009, NOT papered over). Python has no enforced package-private
    visibility, so the internal `_wrap` brand is importable and CAN mint a lying Tile — exactly
    as `Pow2(127)` bypasses the validating `pow2()`. This is the design's already-accepted
    construction-tier split (the brand is not the type surface), shown symmetric here, not hidden."""
    from nla_lab.lower.shape import Pow2
    from nla_lab.lower.tile import _wrap
    assert Pow2(127) == 127                            # the shape brand bypasses pow2() validation
    lying = _wrap(jnp.zeros(4, jnp.int32))             # the carrier brand mints unchecked — same tier
    assert jax.tree_util.tree_leaves(lying) == [lying]  # still an opaque leaf (no re-entry beyond mint)


# ============================ HIGH-2: a Tile is an opaque pytree leaf; tree_map cannot rewrap
def test_tile_is_opaque_leaf_not_a_pytree() -> None:
    """`Tile` is deliberately NOT a registered pytree, so `jax.tree_util.tree_leaves(tile)`
    returns the CARRIER itself (one opaque leaf), not the backing array. The kernel carries its
    running state through `fori_loop` via `ops.fold_kt` (wrap/unwrap inside lower/), so no
    registration is needed."""
    t = ops.full(pow2(8), 1.0)
    leaves = jax.tree_util.tree_leaves(t)
    assert leaves == [t], f"Tile leaked its backing array as a pytree leaf: {leaves!r}"


def test_tree_map_cannot_rewrap_a_tile() -> None:
    """The HIGH-2 re-entry vector is closed. When `Tile` was a pytree, `tree_map(f, tile)` ran
    `f` on the backing array and REWRAPPED an arbitrary (gather/coerced) result into a valid
    `Tile` — mypy-invisible. Unregistered, `tree_map(f, tile)` calls `f(tile)` on the opaque
    carrier, which `f` cannot touch: a gather/astype `f` RAISES instead of minting a lying Tile."""
    t = ops.full(pow2(8), 1.0)
    idx = jnp.array([0, 1], dtype=jnp.int32)
    with pytest.raises(Exception):
        jax.tree_util.tree_map(lambda a: a[idx], t)         # f gets the Tile -> not indexable -> raise
    with pytest.raises(Exception):
        jax.tree_util.tree_map(lambda a: a.astype(jnp.int32), t)  # Tile has no .astype -> raise


# ====================================================== shape: the 2S-1 trap (construction-raise)
def test_pow2_rejects_the_2s_minus_1_trap() -> None:
    """`pow2()` is the only source of `Pow2`; it rejects the exact value that shipped to Triton
    (2S-1 = 127, one below the power of 2 128) — a non-pow2 dim known only at runtime is a
    construction-raise; a raw int dim is a mypy error (test_mypy_shape_nonpow2)."""
    assert next_pow2(_TWO_SPAN + 1) == 64
    for bad in (127, 0, 96, 2 * 64 - 1):
        with pytest.raises(ValueError, match="power of 2"):
            pow2(bad)


# ============================================================ mypy-closed: the four seams, by TYPE
def _run_mypy(filename: str, src: str, tmp_path: Any) -> str:
    """Type-check `src` under the SAME `--strict` config as the package gate (jax_deberta skip),
    with the repo root on MYPYPATH so `nla_lab.lower` resolves. Returns mypy's stdout."""
    p = tmp_path / filename
    p.write_text(textwrap.dedent(src))
    env = dict(os.environ, MYPYPATH=_ROOT)
    proc = subprocess.run(
        [sys.executable, "-m", "mypy", "--config-file", _MYPY_INI, "--no-error-summary", str(p)],
        cwd=_ROOT, env=env, capture_output=True, text=True)
    return proc.stdout


def test_mypy_four_impedances_are_type_errors(tmp_path: Any) -> None:
    """The load-bearing proof (ADR-0000: illegal states unrepresentable). Each of the four
    seams, written the WRONG way, is a mypy `--strict` ERROR — cited by its message. A mismatch
    is unconstructable: mypy rejects it before any host is touched."""
    out = _run_mypy("bad.py", """
        import jax
        import jax.numpy as jnp
        from nla_lab.lower import ops, Tile, Idx, pow2
        from nla_lab.lower.dtype import F32

        def k(t: Tile[F32], idx: Idx, raw: jax.Array) -> None:
            jnp.sum(t)                 # lib/gather: Tile is not ArrayLike
            _ = t[idx]                 # lib/gather: Tile is not indexable
            t.astype(jnp.int32)        # dtype: the carrier has no .astype (no silent coerce)
            ops.add(t, 1)              # device(value-flow): a host int cannot be a device Tile
            ops.band(raw, idx, idx, pow2(8), idx, pow2(8))  # device(residence): a raw host Array is not a Ref
            ops.onehot(t, pow2(64))    # dtype: an F32 tile is not an Idx (must to_i32 first)
            ops.iota(127)              # shape: a raw int is not a Pow2 (the 2S-1 trap)
    """, tmp_path)
    # lib/gather — the non-ArrayLike + non-indexable carrier closes the gather two ways:
    assert 'to "sum" has incompatible type "Tile[F32]"' in out          # jnp.sum(tile)
    assert 'Value of type "Tile[F32]" is not indexable' in out          # tile[idx]
    # dtype — no silent float->int: the carrier exposes no .astype, and F32 != Idx(I32):
    assert '"Tile[F32]" has no attribute "astype"' in out               # tile.astype(...)
    assert 'to "onehot" has incompatible type "Tile[F32]"; expected "Tile[I32]"' in out
    # device — TWO type-closed sub-axes: (a) value-flow — a host scalar cannot be a device Tile;
    # (b) residence boundary — a raw host Array cannot enter a kernel load without the ops.ref brand:
    assert 'to "add" has incompatible type "int"; expected "Tile[F32]"' in out       # (a) value-flow
    assert 'to "band" has incompatible type "Array"; expected "Ref"' in out          # (b) residence boundary
    # shape — a raw int is not a Pow2:
    assert 'to "iota" has incompatible type "int"; expected "Pow2"' in out


def test_mypy_einsum_slips(tmp_path: Any) -> None:
    """HONESTY (ADR-0009): `jnp.einsum`'s `*operands` are `Any` in jax's stubs, so an einsum on
    `Tile`s does NOT type-check as an error — it SLIPS mypy. This is stated, not hidden: einsum
    is closed at CONSTRUCTION (test_construction_raise_einsum_*), not at the type surface.
    Calling it 'type-closed' would be the unsubstantiated claim the design forbids."""
    out = _run_mypy("einsum_slip.py", """
        import jax.numpy as jnp
        from nla_lab.lower import ops, pow2

        def k() -> None:
            a = ops.full(pow2(8), 1.0)
            jnp.einsum("iw,ijw->ij", a, a)   # batched-shared-index einsum on Tiles -> NO mypy error
    """, tmp_path)
    assert "error:" not in out, f"expected einsum to slip mypy, but mypy reported:\n{out}"


def test_mypy_well_formed_kernel_ops_are_clean(tmp_path: Any) -> None:
    """The dual of the closure: the SANCTIONED combinator calls (the gather replacement, the
    explicit cast, the Pow2 dims) type-check CLEANLY — the algebra is usable, not merely
    restrictive (`ops.band`/`ops.select`/`ops.to_i32`/`ops.iota(pow2(...))` are all fine)."""
    out = _run_mypy("good.py", """
        import jax
        from nla_lab.lower import ops, Tile, Idx, pow2
        from nla_lab.lower.dtype import F32

        def k(t: Tile[F32], i: Idx, raw: jax.Array, bh: Idx, base: Idx) -> None:
            ops.rsum(t, -1)                              # reduction on a Tile (sanctioned)
            ops.to_i32(t)                                # the ONE explicit F32->I32 cast
            ops.iota(pow2(64))                           # a Pow2 dim
            ref = ops.ref(raw)                           # the ONE host-array -> device-ref brand
            ops.band(ref, bh, i, pow2(32), base, pow2(64))   # the gather replacement, on a Ref
    """, tmp_path)
    assert "error:" not in out, f"well-formed algebra ops should type-check, mypy said:\n{out}"


if __name__ == "__main__":
    import tempfile

    for _n, _fn in sorted(globals().items()):
        if _n.startswith("test_") and callable(_fn):
            if "tmp_path" in getattr(_fn, "__code__").co_varnames:
                with tempfile.TemporaryDirectory() as _d:
                    import pathlib
                    _fn(pathlib.Path(_d))
            else:
                _fn()
            print(f"PASS {_n}")
