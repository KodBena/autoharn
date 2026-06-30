#!/usr/bin/env python
"""distill.train — the HOST loop driver + CLI for QAT feature-distillation.

Orchestration only (numpy-free, jax-free AST). The per-step device math is `distill.ste`
(jitted), the optimizer is `distill.optim`, the data plan is `distill.data`; this file
owns the epoch loop, the teacher-target precompute, the loss logging, the checkpoint
cadence, and the CLI — exactly as `bench.py` owns the sweep while `lab_measure` owns the
device math. Device arrays (params, lifted batches, opt_state, the loss) are held
OPAQUELY as `object` handles and routed through the device modules by name; the only
device->host reads are the scalar loss/fidelity numbers (the legitimate boundary, like
`lab_measure`'s scalar returns).

THE TWO REGIMES (ADR-0009, named explicitly):
  * Inference path = bit-near-identity (`exact_reference`, `--coref-verify`): the SAME
    weights reproduced exactly.
  * THIS (QAT student) = trained-P6 AGGREGATE-BEHAVIORAL only: different numbers, a
    learned approximation. Its claim is `mean|Δ|/max|Δ|` dropping BELOW the PTQ floor,
    never `== 0`. The student improves the number *within* the AGGREGATE_BEHAVIORAL tier;
    it does not upgrade the tier.

HOST RUN (real maverick teacher + real corpus):
    python -m nla_lab.distill.train \
        --teacher-npz fixtures/deberta_maverick.npz \
        --corpus <diverse multi-book text> --bits 4 --group-size 64 \
        --epochs E --lr lr --batch B --seq-bucket S \
        --train-nonquant=false --remat=true \
        --out fixtures/deberta_maverick_w4_distilled.npz
The artifact `fixtures/deberta_maverick_w4_distilled.npz` is the trained fp32 SHADOW,
written by the ONE codec `export_deberta_maverick.save_npz` (no second npz format); the
bench loads it via `--weights-npz`, where the same int4 kernel PTQ-quantizes the
trained-to-be-robust weights.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import cast

from nla_lab import lab_measure
from nla_lab.distill import data, optim, ste


@dataclass(frozen=True)
class DistillResult:
    """The MEASURED outcome (ADR-0009 — every number is produced here, not asserted in a
    doc). `loss_curve` is the per-logged-step training loss; `e_ptq`/`e_qat` are the
    cross-weights `(max|Δ|, mean|Δ|)` against the frozen teacher; `qat_beats_ptq` is the
    honest verdict on the eval batch."""
    loss_curve: list[float]
    e_ptq: tuple[float, float]
    e_qat: tuple[float, float]
    qat_beats_ptq: bool
    n_steps: int


def _load_teacher(
    teacher_npz: str | None, seed: int,
) -> tuple[dict[str, object], object, int, str]:
    """Return `(teacher_params, cfg, vocab, tokenizer_name)`. REUSES the daemon's EXACT
    load path for the real npz (no re-authored read) — `coref_decode_server.load_deberta_npz`
    (host numpy wire seam) -> `coref_host_shell.{build_deberta_cfg,validate_deberta_load,
    lift_deberta_params}` (the jax home), mirroring `bench.load_fixture`. With no npz it is
    the synthetic guest fixture (CPU jax, no download)."""
    if teacher_npz is not None:
        import coref_decode_server
        import coref_host_shell
        host_w, cfg_fields, tok = coref_decode_server.load_deberta_npz(teacher_npz)
        cfg = coref_host_shell.build_deberta_cfg(cfg_fields)
        coref_host_shell.validate_deberta_load(host_w, cfg)
        params = coref_host_shell.lift_deberta_params(host_w)
        vocab = int(params["embeddings.word_embeddings.weight"].shape[0])
        # the host holds device-array params OPAQUELY (object handles), exactly as
        # bench.load_fixture casts the npz/synthetic params to the host's object view.
        return cast("dict[str, object]", params), cfg, vocab, tok
    cfg = lab_measure.synthetic_cfg()
    vocab, intermediate = 100, 64
    params = lab_measure.synthetic_deberta(cfg, vocab, intermediate, seed)
    return cast("dict[str, object]", params), cfg, vocab, "synthetic"


def distill(
    teacher_npz: str | None = None,
    corpus_path: str | None = None,
    *,
    group_size: int = ste.GROUP_SIZE,
    epochs: int = 1,
    lr: float = 1e-3,
    weight_decay: float = 0.0,
    batch: int = 4,
    seq_bucket: int = 64,
    n_batches: int = 8,
    train_nonquant: bool = False,
    remat: bool = False,
    seed: int = 0,
    log_every: int = 10,
    out_path: str | None = None,
    fixture_weight_scale: float = 1.0,
    verbose: bool = True,
) -> DistillResult:
    """Run the feature-distillation loop and return the MEASURED result.

    Loop: load the frozen teacher; init the shadow AT the teacher weights; precompute the
    teacher lhs target per batch ONCE (constant across epochs); for each epoch x batch,
    run the jitted device step (STE grad -> AdamW update); log the loss; finally run the
    cross-weights PTQ-vs-QAT eval on a held-out batch and (optionally) write the trained
    shadow npz. NO faked convergence — the loss curve and the eval numbers are whatever
    the run measures."""
    teacher, cfg, vocab, tok = _load_teacher(teacher_npz, seed)
    if teacher_npz is None and fixture_weight_scale != 1.0:
        # GUEST-only fixture stress (no effect on the real npz path): put the toy fixture
        # in a genuinely-lossy quant regime so the QAT lever has real room (see
        # ste.scale_linear_weights). The real maverick weights already live there.
        teacher = cast("dict[str, object]",
                       ste.scale_linear_weights(teacher, fixture_weight_scale))  # type: ignore[arg-type]

    # the shadow starts AT the teacher weights (the student is initialized to the teacher,
    # then learns to be quantization-robust). split into trainable (the quantized Linear
    # shadows) vs frozen (everything else, pinned to the teacher unless --train-nonquant).
    trainable, frozen = ste.split_shadow(teacher, train_nonquant)  # type: ignore[arg-type]

    # data plan: guest synthetic (reproducible) or the host text corpus (real spm tokens).
    if corpus_path is not None:
        plan = data.text_corpus_plan(corpus_path, tok, batch, seq_bucket)
    else:
        plan = data.synthetic_plan(n_batches, batch, seq_bucket, vocab, seed)

    # precompute the FROZEN teacher target per batch ONCE (constant across epochs). The
    # lifted device arrays are held opaquely (object) — the host routes them back to the
    # device step without inspecting them.
    lifted: list[tuple[object, object, object]] = []
    for ids_rows, mask_rows in plan:
        p_ids, p_mask = lab_measure.lift_batch(ids_rows, mask_rows)
        p_target = ste.teacher_lhs(teacher, p_ids, p_mask, cfg)  # type: ignore[arg-type]
        lifted.append((p_ids, p_mask, p_target))

    opt = optim.make_adamw(lr, weight_decay=weight_decay)
    opt_state: object = optim.init_state(opt, trainable)
    step = ste.make_train_step(opt, cfg, group_size, remat=remat)

    loss_curve: list[float] = []
    n_steps = 0
    for epoch in range(epochs):
        for b_ids, b_mask, b_target in lifted:
            trainable, opt_state, loss = step(
                trainable, opt_state, frozen, b_ids, b_mask, b_target)
            if n_steps % max(1, log_every) == 0:
                lv = float(loss)  # device->host scalar read (the legitimate boundary)
                loss_curve.append(lv)
                if verbose:
                    print(f"  epoch {epoch} step {n_steps:5d}  loss {lv:.6f}", flush=True)
            n_steps += 1

    # ---- the cross-weights eval (ADR-0009 §8 rung 4): PTQ(teacher) vs PTQ(distilled),
    #      both scored against the frozen teacher lhs, on a HELD-OUT batch (seed+9999 so
    #      it is not a training batch — an honest generalization read, not train error).
    distilled = {**frozen, **trainable}
    if corpus_path is not None:
        eval_ids_rows, eval_mask_rows = plan[-1]  # last real batch as the eval slice
    else:
        eval_ids_rows, eval_mask_rows = data.synthetic_plan(
            1, batch, seq_bucket, vocab, seed + 9999)[0]
    e_ids, e_mask = lab_measure.lift_batch(eval_ids_rows, eval_mask_rows)
    e_ptq, e_qat, _ = ste.ptq_qat_errors(
        teacher, distilled, e_ids, e_mask, cfg, group_size)  # type: ignore[arg-type]
    qat_beats_ptq = e_qat[1] < e_ptq[1]   # compare mean|Δ| (the headline aggregate)

    if verbose:
        print(f"  PTQ  (round-1 w4a16 of teacher):   max|Δ|={e_ptq[0]:.6f}  mean|Δ|={e_ptq[1]:.6f}")
        print(f"  QAT  (w4a16 of distilled shadow):  max|Δ|={e_qat[0]:.6f}  mean|Δ|={e_qat[1]:.6f}")
        print(f"  QAT beats PTQ (mean|Δ|): {qat_beats_ptq}", flush=True)

    if out_path is not None:
        # the trained fp32 SHADOW, written by the ONE codec (no second npz format). At
        # inference the same int4 kernel PTQ-quantizes these trained-to-be-robust weights.
        import export_deberta_maverick
        n = export_deberta_maverick.save_npz(out_path, distilled, cfg, tok)
        if verbose:
            print(f"  wrote {out_path} ({n} weight tensors)", flush=True)

    return DistillResult(
        loss_curve=loss_curve, e_ptq=e_ptq, e_qat=e_qat,
        qat_beats_ptq=qat_beats_ptq, n_steps=n_steps)


def _bool(s: str) -> bool:
    return s.strip().lower() in ("1", "true", "yes", "on")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="QAT feature-distillation of a W4 DeBERTa student.")
    ap.add_argument("--teacher-npz", default=None,
                    help="maverick teacher export (fixtures/deberta_maverick.npz); omit for the synthetic guest fixture.")
    ap.add_argument("--corpus", default=None,
                    help="text corpus (one doc/paragraph per line); omit for the synthetic guest plan.")
    ap.add_argument("--bits", type=int, default=4, help="weight bits (only 4 implemented — the clear need).")
    ap.add_argument("--group-size", type=int, default=ste.GROUP_SIZE)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--weight-decay", type=float, default=0.0)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--seq-bucket", type=int, default=64)
    ap.add_argument("--n-batches", type=int, default=8, help="synthetic-plan batch count (guest only).")
    ap.add_argument("--train-nonquant", type=_bool, default=False,
                    help="also train the non-quantized params (default: train only the quantized Linear shadows — the QAT lever).")
    ap.add_argument("--remat", type=_bool, default=False, help="jax.checkpoint the forward (host memory trade).")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--log-every", type=int, default=10)
    ap.add_argument("--fixture-weight-scale", type=float, default=1.0,
                    help="GUEST-only: scale the synthetic teacher Linear weights into a lossy-quant regime (no effect with --teacher-npz).")
    ap.add_argument("--out", default=None, help="output distilled-shadow npz path.")
    args = ap.parse_args(argv)

    if args.bits != 4:
        raise SystemExit(f"--bits {args.bits} not implemented; only W4 (the clear need) is built.")

    res = distill(
        teacher_npz=args.teacher_npz, corpus_path=args.corpus,
        group_size=args.group_size, epochs=args.epochs, lr=args.lr,
        weight_decay=args.weight_decay, batch=args.batch, seq_bucket=args.seq_bucket,
        n_batches=args.n_batches, train_nonquant=args.train_nonquant, remat=args.remat,
        seed=args.seed, log_every=args.log_every, out_path=args.out,
        fixture_weight_scale=args.fixture_weight_scale, verbose=True)
    print(f"\nDONE: {res.n_steps} steps | QAT beats PTQ (mean|Δ|): {res.qat_beats_ptq} | "
          f"e_ptq(mean)={res.e_ptq[1]:.6f} e_qat(mean)={res.e_qat[1]:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
