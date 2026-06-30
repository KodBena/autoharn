#!/usr/bin/env python
"""distill.test_distill — the GUEST proof of the QAT machinery (ADR-0009/0013).

All on the synthetic fixture (`lab_measure.synthetic_deberta` teacher, `lab_corpus`
batches), CPU jax, no download. These prove the MECHANISM; the production number is the
host run (DESIGN §9). Run:
    python -m pytest -q nla_lab/distill/test_distill.py    (from fact-mining/, CPU jax)
or standalone for the loss curve + QAT-vs-PTQ numbers:
    python -m nla_lab.distill.test_distill

The five rungs (DESIGN §8):
  1. the STE passes a real gradient (‖g‖ > 0) AND a step changes the shadow;
  2. the NEGATIVE CONTROL — the round-1 kernel WITHOUT the STE yields ~0 gradient
     (proving the STE is load-bearing — the test that would catch a silently-flat loop);
  3. the loss DECREASES over training steps (reported, not faked);
  4. the whole point: e_qat = w4a16(distilled) error  <  e_ptq = w4a16(teacher) error,
     both scored against the SAME frozen teacher lhs (a cross-weights comparison);
  5. host-XOR-device + gates (asserted by test_import_xor.py / mypy, run separately).
"""

from __future__ import annotations

import jax
import jax.numpy as jnp

from nla_lab import lab_corpus, lab_measure
from nla_lab.distill import ste, train

jax.config.update("jax_platform_name", "cpu")  # type: ignore[no-untyped-call]  # jax.config is untyped

# a small but architecture-faithful fixture (same shape lab_measure self-tests use).
_CFG = lab_measure.synthetic_cfg()
_VOCAB, _INTER = 100, 64
_BATCH, _SEQ = 4, 64   # seq_bucket must be a shape_buckets.ENCODE_LEN_BUCKETS rung (min 64)
#: GUEST fixture stress: the synthetic teacher's weights are tiny (~0.02), so int4 quant
#: barely hurts (PTQ ~9e-4) and the loss is ~1e-6 — too small to show a convincing
#: decrease. Scale ×10 puts the fixture in a genuinely-lossy regime (PTQ ~0.10, the order
#: of the real maverick w4a16 floor ~0.474). The real weights already live there.
_WSCALE = 10.0


def _fixture() -> tuple[dict[str, jax.Array], jax.Array, jax.Array]:
    teacher = lab_measure.synthetic_deberta(_CFG, _VOCAB, _INTER, seed=0)
    teacher = ste.scale_linear_weights(teacher, _WSCALE)
    ids_rows, mask_rows = lab_corpus.make_batch(_BATCH, _SEQ, _VOCAB, seed=1)
    ids, mask = lab_measure.lift_batch(ids_rows, mask_rows)
    return teacher, ids, mask


def test_ste_passes_gradient_and_step_moves_shadow() -> None:
    """Rung 1: ‖g‖ through the STE is strictly > 0, and one AdamW step CHANGES the
    quantized Linear shadow weights."""
    teacher, ids, mask = _fixture()
    trainable, frozen = ste.split_shadow(teacher, train_nonquant=False)
    target = ste.teacher_lhs(teacher, ids, mask, _CFG)

    g = ste.ste_grad_norm(trainable, frozen, ids, mask, target, _CFG, ste.GROUP_SIZE)
    assert g > 0.0, f"STE gradient norm is {g} — the gradient is NOT flowing (cardinal sin)"

    from nla_lab.distill import optim
    opt = optim.make_adamw(1e-3)
    opt_state = optim.init_state(opt, trainable)
    step = ste.make_train_step(opt, _CFG, ste.GROUP_SIZE)
    new_trainable, _, _ = step(trainable, opt_state, frozen, ids, mask, target)

    moved = max(float(jnp.max(jnp.abs(new_trainable[k] - trainable[k]))) for k in trainable)
    assert moved > 0.0, "a training step did NOT change any shadow weight"


def test_negative_control_round_kills_gradient() -> None:
    """Rung 2 (the test that would catch a silently-flat loop): the round-1 kernel WITHOUT
    the STE reaches almost NO weights — its only differentiable path is the per-group
    absmax SCALE, so its gradient is nonzero on a few % of entries (the per-group max),
    structurally insufficient for QAT. The STE reaches ~every weight (dense). DENSITY, not
    norm, is the honest metric: with data-dependent absmax scaling the no-STE *norm* is
    small-but-nonzero (the scale leak), but its *density* collapses — proving the STE is
    what carries the QAT gradient."""
    teacher, ids, mask = _fixture()
    trainable, frozen = ste.split_shadow(teacher, train_nonquant=False)
    target = ste.teacher_lhs(teacher, ids, mask, _CFG)

    d_ste = ste.ste_grad_density(trainable, frozen, ids, mask, target, _CFG, ste.GROUP_SIZE)
    d_none = ste.negative_control_grad_density(
        trainable, frozen, ids, mask, target, _CFG, ste.GROUP_SIZE)
    assert d_ste > 0.90, f"STE gradient is not dense ({d_ste:.3f}) — the STE is not reaching the weights"
    assert d_none < 0.10, (
        f"no-STE gradient density {d_none:.3f} is not collapsed — the round-1 kernel should "
        f"reach only the per-group absmax elements; if it reaches more, the STE is not "
        f"what is load-bearing")
    assert d_ste > 10.0 * max(d_none, 1e-9), (
        f"STE density {d_ste:.3f} is not >> no-STE density {d_none:.3f}")


def test_loss_decreases_and_qat_beats_ptq() -> None:
    """Rungs 3 + 4: the loss decreases over a few hundred steps AND the QAT student's
    feature error drops below the PTQ round-1 baseline on the fixture (the convergence
    that justifies the whole lever). A non-decreasing loss or e_qat >= e_ptq is a REAL
    finding — this test reports it, it does not fake convergence."""
    res = train.distill(
        teacher_npz=None, corpus_path=None,
        epochs=60, lr=2e-3, batch=_BATCH, seq_bucket=_SEQ,
        n_batches=8, seed=0, log_every=20, fixture_weight_scale=_WSCALE, verbose=False)
    assert len(res.loss_curve) >= 6, "too few logged losses to judge a trend"
    # robust to the per-batch SGD noise (8 cycled batches): compare windowed means, not
    # two noisy endpoints. The TREND must be down (the loss genuinely decreases).
    head = sum(res.loss_curve[:3]) / 3.0
    tail = sum(res.loss_curve[-3:]) / 3.0
    assert tail < head, (
        f"loss did NOT decrease in trend: head-mean={head:.6f} tail-mean={tail:.6f} "
        f"(curve={[round(v, 6) for v in res.loss_curve]}) — REAL finding, reported not faked")
    assert res.e_qat[1] < res.e_ptq[1], (
        f"QAT did NOT beat PTQ on mean|Δ|: e_ptq={res.e_ptq} e_qat={res.e_qat} — REAL finding")


def _report() -> None:
    """Standalone: print the loss curve + the QAT-vs-PTQ numbers (the deliverable)."""
    res = train.distill(
        teacher_npz=None, corpus_path=None,
        epochs=60, lr=2e-3, batch=_BATCH, seq_bucket=_SEQ,
        n_batches=8, seed=0, log_every=20, fixture_weight_scale=_WSCALE, verbose=True)
    print("\n=== loss curve (every 20 steps; ×10 lossy-quant fixture) ===")
    print("  " + "  ".join(f"{v:.5f}" for v in res.loss_curve))
    print("\n=== QAT vs PTQ feature error (mean|Δ| / max|Δ| vs frozen teacher, held-out batch) ===")
    print(f"  e_ptq  (round-1 w4a16 of teacher):  mean={res.e_ptq[1]:.6f}  max={res.e_ptq[0]:.6f}")
    print(f"  e_qat  (w4a16 of distilled shadow): mean={res.e_qat[1]:.6f}  max={res.e_qat[0]:.6f}")
    print(f"  QAT beats PTQ (mean|Δ|): {res.qat_beats_ptq}  "
          f"(improvement {100.0 * (1 - res.e_qat[1] / max(res.e_ptq[1], 1e-30)):.1f}%)")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    _report()
