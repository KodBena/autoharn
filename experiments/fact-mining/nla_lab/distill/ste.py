#!/usr/bin/env python
"""distill.ste — the DEVICE-side QAT core: STE fake-quant + student forward + loss.

WHAT THIS OWNS (ADR-0012 P1: the three things that do not exist elsewhere). The
teacher forward is `jax_deberta.encode` (reused verbatim); the student's fake-quant
*value* is the round-1 int4 kernel `w4a16_weightonly._quantize_dequantize_int4`
(reused verbatim — the int4 math has exactly ONE home); the deployed PTQ baseline is
`w4a16_weightonly._quantize_params` (reused verbatim). This module adds exactly:
  1. the STE gradient routing (`fake_quant_int4_ste`),
  2. the feature-distillation loss (`feature_loss`),
  3. the device train step (`make_train_step`) + the cross-weights eval (`ptq_qat_errors`).

THE CARDINAL SIN (ADR-0013) this file exists to avoid: a training loop that silently
does not learn because the gradient is zeroed by `jnp.round`. The STE below routes a
real, identity gradient to the full-precision shadow; `negative_control_grad_norm`
PROVES, on the artifact, that without the STE the gradient collapses to ~0 — so the
STE is demonstrably load-bearing, not decoration.

HOST-XOR-DEVICE (test_import_xor.py / ADR-0012 P9). Imports `jax`/`jax.numpy` +
neutrally-named `jax_deberta` + the round-1 quant kernels; NEVER numpy. Neutral
filename, so device-only is XOR-clean (same posture as `lab_measure.py` and every
variant). The npz read/write is NOT here — it is the declared boundary the host
`train.py` drives through the one codec.
"""

from __future__ import annotations

from typing import Callable

import jax
import jax.numpy as jnp

import jax_deberta
from nla_lab.variants.w4a16_weightonly import (
    _GROUP_SIZE,
    _LINEAR_PROJ_INFIXES,
    _quantize_dequantize_int4,
    _quantize_params,
)

Params = dict[str, jax.Array]

#: re-export the round-1 group size so the host driver and the deployed kernel agree on
#: ONE default (no second constant; ADR-0012 P1).
GROUP_SIZE = _GROUP_SIZE


# --------------------------------------------------------------- the seam selector
def _is_linear_weight(k: str, v: jax.Array) -> bool:
    """The EXACT W4A16 seam selector reused from `w4a16_weightonly._quantize_params`:
    a 2-D `.weight` whose key contains a Linear-projection infix. Selecting it HERE the
    same way the PTQ variant does keeps the quantized-weight set identical between the
    QAT student and the deployed kernel — the student trains precisely the weights the
    inference path will round (no drift between what is trained and what is quantized)."""
    return k.endswith(".weight") and v.ndim == 2 and any(
        infix in k for infix in _LINEAR_PROJ_INFIXES)


# ------------------------------------------------------- the straight-through estimator
def fake_quant_int4_ste(w: jax.Array, group_size: int = _GROUP_SIZE) -> jax.Array:
    """W4 fake-quant with a straight-through estimator (the ONLY new gradient mechanism).

    forward  : == _quantize_dequantize_int4(w)   (the round-1 dequantized weight, bit-for-bit)
    backward : d/dw == 1  (identity) — the gradient reaches the full-precision shadow `w`.

    Why the naive kernel kills the gradient: `_quantize_dequantize_int4` computes
    `clip(round(w/scale))*scale`; `jnp.round` is piecewise-constant so `d/dw == 0` almost
    everywhere — `jax.grad` through it returns a ZERO gradient (the flat-loss failure).
    The STE seals the round inside `stop_gradient` and routes the gradient through the
    `+ w` identity path:
        w + stop_gradient(dq - w)
        forward  = w + (dq - w) = dq                      (value unchanged: == dq)
        backward = 1 + 0 = 1                              (gradient flows to w)

    Plain (identity) STE is the correct STE here, NOT the clipped variant: the round-1
    kernel scales per group by `absmax/7`, so `|w/scale| <= 7` by construction and the
    `clip(-8,7)` essentially never saturates — there are no out-of-range weights whose
    gradient a clipped STE would need to zero. The fp16 dequant inside the kernel does not
    block the gradient: `dq` is cast back to fp32 before `dq - w`, and the gradient
    traverses only `+ w` (fp32), never the fp16 cast."""
    dq = _quantize_dequantize_int4(w, group_size)         # non-differentiable (round)
    return w + jax.lax.stop_gradient(dq - w)              # fwd == dq, bwd == identity


# ----------------------------------------------------------------- shadow partition
def split_shadow(shadow: Params, train_nonquant: bool) -> tuple[Params, Params]:
    """Partition the shadow into (trainable, frozen). The QAT lever trains the Linear
    weights that get quantized; the rest (biases, LayerNorm gains, embeddings) is frozen
    to the teacher by default (`train_nonquant=False`) — that keeps the student close to
    the teacher and shrinks the trainable set to exactly the quantization-sensitive
    weights. `train_nonquant=True` also trains the non-quantized params (still NOT
    fake-quantized in the forward — they are trained at full precision)."""
    trainable: Params = {}
    frozen: Params = {}
    for k, v in shadow.items():
        if _is_linear_weight(k, v) or train_nonquant:
            trainable[k] = v
        else:
            frozen[k] = v
    return trainable, frozen


def scale_linear_weights(params: Params, factor: float) -> Params:
    """Multiply every Linear `.weight` by `factor` (all else unchanged). A GUEST fixture
    STRESS knob (no effect on the real host npz path): the synthetic teacher's weights are
    small-scaled (~0.02) so int4 quant barely hurts (PTQ error ~9e-4) and the loss sits at
    ~1e-6 — too small to show a convincing decrease. Scaling the Linear weights up puts the
    fixture in a genuinely-lossy quant regime (factor 10 -> PTQ error ~0.10, the order of
    the real maverick w4a16 floor ~0.474), so the QAT lever has real room and the loss
    decrease is visible. The REAL maverick weights already live in that regime; this knob
    only exists to stop the toy fixture from understating the effect."""
    return {k: (v * jnp.float32(factor) if _is_linear_weight(k, v) else v)
            for k, v in params.items()}


def assemble_student(trainable: Params, frozen: Params, group_size: int) -> Params:
    """The full param dict the student forward consumes: every Linear `.weight` is
    fake-quantized (STE) FRESH from its CURRENT shadow value; everything else passes
    through. Re-deriving the quantized weights every forward (NOT memoized — the opposite
    of the PTQ variant's R1-C prep cache) is non-negotiable: the gradient must reach the
    *current* shadow each step."""
    full: Params = dict(frozen)
    for k, v in trainable.items():
        full[k] = fake_quant_int4_ste(v, group_size) if _is_linear_weight(k, v) else v
    return full


# ---------------------------------------------------------------------- the loss
def feature_loss(
    trainable: Params,
    frozen: Params,
    ids: jax.Array,
    mask: jax.Array,
    teacher_lhs: jax.Array,
    cfg: jax_deberta.DebertaCfg,
    group_size: int,
) -> jax.Array:
    """Feature-distillation MSE over REAL tokens (no labels; the teacher lhs is the
    target). The squared form of `lab_measure.fidelity_delta`'s convention (mask==1
    positions, normalized by `n_real * H`). `trainable` is argnum 0 — the ONLY thing
    `jax.grad` differentiates; `teacher_lhs` is `stop_gradient`-ed so no gradient can
    leak into the (frozen) teacher even by accident."""
    student = jax_deberta.encode(
        assemble_student(trainable, frozen, group_size), ids, mask, cfg)
    diff2 = jnp.square(student - jax.lax.stop_gradient(teacher_lhs))
    m = mask.astype(diff2.dtype)[:, :, None]
    denom = jnp.maximum(jnp.sum(m) * student.shape[-1], 1.0)
    return jnp.sum(diff2 * m) / denom


def teacher_lhs(params: Params, ids: jax.Array, mask: jax.Array,
                cfg: jax_deberta.DebertaCfg) -> jax.Array:
    """The frozen full-precision target: `jax_deberta.encode` on the teacher params.
    Materialized by the caller; `stop_gradient`-ed at the loss site so it is a constant."""
    return jax_deberta.encode(params, ids, mask, cfg)  # type: ignore[no-any-return]


# ---------------------------------------------------------- the device train step
def make_train_step(
    opt: object,
    cfg: jax_deberta.DebertaCfg,
    group_size: int,
    remat: bool = False,
) -> Callable[..., tuple[Params, object, jax.Array]]:
    """Build the jitted device step closing over the (static) optimizer, cfg, and
    group_size. `jax.value_and_grad` differentiates w.r.t. `trainable` (argnum 0) only;
    the STE makes the Linear-weight gradients NONZERO. Returns `(trainable, opt_state,
    loss)`. `opt` is an optax GradientTransformation (typed `object` to keep this file's
    annotations device-clean; optax is untyped behind its named mypy skip).

    `remat=True` wraps the differentiated forward in `jax.checkpoint`: the student+teacher
    activations are recomputed in the backward pass instead of being held — a real
    compute-for-memory trade for the 24-layer host forward on the 2080Ti (the loss holds
    TWO forwards' activations: student + the teacher target). The guest 2-layer fixture
    does not need it (default False); the host run flags it on if OOM."""
    import optax  # device-side optimizer lib (gate-neutral; this file already imports jax)

    # cfg (argnum 5) and group_size (argnum 6) are static (non-array) — kept out of the
    # remat's recompute as compile-time constants.
    loss_fn = (jax.checkpoint(feature_loss, static_argnums=(5, 6))
               if remat else feature_loss)

    @jax.jit
    def step(trainable: Params, opt_state: object, frozen: Params,
             ids: jax.Array, mask: jax.Array, target: jax.Array
             ) -> tuple[Params, object, jax.Array]:
        loss, grads = jax.value_and_grad(loss_fn)(
            trainable, frozen, ids, mask, target, cfg, group_size)
        updates, opt_state = opt.update(grads, opt_state, trainable)  # type: ignore[attr-defined]
        trainable = optax.apply_updates(trainable, updates)
        return trainable, opt_state, loss

    return step


# ------------------------------------------------- the anti-cardinal-sin diagnostics
def _leaf_l2(tree: Params) -> float:
    """L2 norm over all leaves of a param tree (a scalar diagnostic)."""
    sq = jnp.asarray(0.0)
    for v in tree.values():
        sq = sq + jnp.sum(jnp.square(v.astype(jnp.float32)))
    return float(jnp.sqrt(sq))


def _leaf_density(tree: Params, tol: float = 1e-12) -> float:
    """Fraction of leaf ENTRIES whose magnitude exceeds `tol` — how DENSE the gradient is.
    This is the meaningful negative-control metric (not the norm): the STE makes the
    gradient reach EVERY weight (dense ~1.0); the round-1 kernel reaches almost none."""
    nz = 0
    tot = 0
    for v in tree.values():
        nz += int(jnp.sum(jnp.abs(v) > tol))
        tot += int(v.size)
    return nz / max(tot, 1)


def _no_ste_grad(
    trainable: Params, frozen: Params, ids: jax.Array, mask: jax.Array,
    target: jax.Array, cfg: jax_deberta.DebertaCfg, group_size: int,
) -> Params:
    """grad of the SAME feature loss but with the round-1 kernel wired into the forward
    WITHOUT the STE wrapper (plain `_quantize_dequantize_int4`) — the NEGATIVE CONTROL."""
    def loss_no_ste(tr: Params) -> jax.Array:
        full: Params = dict(frozen)
        for k, v in tr.items():
            full[k] = (_quantize_dequantize_int4(v, group_size)
                       if _is_linear_weight(k, v) else v)
        student = jax_deberta.encode(full, ids, mask, cfg)
        diff2 = jnp.square(student - jax.lax.stop_gradient(target))
        m = mask.astype(diff2.dtype)[:, :, None]
        return jnp.sum(diff2 * m) / jnp.maximum(jnp.sum(m) * student.shape[-1], 1.0)

    return jax.grad(loss_no_ste)(trainable)  # type: ignore[no-any-return]


def ste_grad_norm(
    trainable: Params, frozen: Params, ids: jax.Array, mask: jax.Array,
    target: jax.Array, cfg: jax_deberta.DebertaCfg, group_size: int,
) -> float:
    """‖grad‖ of the feature loss w.r.t. the trainable Linear weights, THROUGH the STE.
    The anti-cardinal-sin test asserts this is strictly > 0 (the gradient flows)."""
    return _leaf_l2(jax.grad(feature_loss)(
        trainable, frozen, ids, mask, target, cfg, group_size))


def ste_grad_density(
    trainable: Params, frozen: Params, ids: jax.Array, mask: jax.Array,
    target: jax.Array, cfg: jax_deberta.DebertaCfg, group_size: int,
) -> float:
    """Fraction of Linear-weight entries the STE gradient reaches (~1.0: DENSE). The STE
    routes an identity gradient to every weight."""
    return _leaf_density(jax.grad(feature_loss)(
        trainable, frozen, ids, mask, target, cfg, group_size))


def negative_control_grad_norm(
    trainable: Params, frozen: Params, ids: jax.Array, mask: jax.Array,
    target: jax.Array, cfg: jax_deberta.DebertaCfg, group_size: int,
) -> float:
    """The NEGATIVE CONTROL norm (ADR-0013): grad through the round-1 kernel WITHOUT the
    STE. The `jnp.round` kills the dominant gradient path; a SMALL residual leaks through
    the data-dependent absmax SCALE (`jnp.max` is differentiable at the per-group max),
    so this is not identically zero — but see `negative_control_grad_density`: that leak
    reaches only the per-group max elements, ~a few %, structurally insufficient for QAT."""
    return _leaf_l2(_no_ste_grad(
        trainable, frozen, ids, mask, target, cfg, group_size))


def negative_control_grad_density(
    trainable: Params, frozen: Params, ids: jax.Array, mask: jax.Array,
    target: jax.Array, cfg: jax_deberta.DebertaCfg, group_size: int,
) -> float:
    """The NEGATIVE CONTROL density — the test that would catch a silently-flat loop. The
    round-1 kernel's only differentiable path is the per-group `absmax` scale, so its
    gradient is nonzero on ONLY the per-group max elements (a few %), NOT the full weight.
    The STE (density ~1.0) is therefore demonstrably what carries the QAT gradient: the
    round kills it for ~every weight; the STE restores it densely."""
    return _leaf_density(_no_ste_grad(
        trainable, frozen, ids, mask, target, cfg, group_size))


# --------------------------------------------- the cross-weights eval (rung 4, the point)
def ptq_qat_errors(
    teacher_params: Params,
    distilled_shadow: Params,
    ids: jax.Array,
    mask: jax.Array,
    cfg: jax_deberta.DebertaCfg,
    group_size: int,
) -> tuple[tuple[float, float], tuple[float, float], jax.Array]:
    """The whole point, MEASURED (ADR-0009 §8 rung 4). Against the FROZEN full-precision
    teacher lhs, score TWO deployed-PTQ students with the SAME round-1 int4 kernel:
      * e_ptq = fidelity_delta( encode(PTQ(teacher_params)),    teacher_lhs )
      * e_qat = fidelity_delta( encode(PTQ(distilled_shadow)),  teacher_lhs )
    Both use `w4a16_weightonly._quantize_params` (the deployed PTQ kernel, NO STE — the
    STE is a training-time gradient device only; at inference the same int4 kernel rounds
    the trained-to-be-robust shadow). Returns `((max,mean)_ptq, (max,mean)_qat, teacher_lhs)`.
    This is a CROSS-WEIGHTS comparison (both quantized, both scored against the same
    teacher) the standing bench's per-params fidelity does not do — so the distill module
    owns this number. Returns `(max,mean)` exactly as `lab_measure.fidelity_delta`."""
    from nla_lab.lab_measure import fidelity_delta

    target = jax_deberta.encode(teacher_params, ids, mask, cfg)
    ptq_lhs = jax_deberta.encode(_quantize_params(teacher_params, group_size), ids, mask, cfg)
    qat_lhs = jax_deberta.encode(_quantize_params(distilled_shadow, group_size), ids, mask, cfg)
    e_ptq = fidelity_delta(ptq_lhs, target, mask)
    e_qat = fidelity_delta(qat_lhs, target, mask)
    return e_ptq, e_qat, target
