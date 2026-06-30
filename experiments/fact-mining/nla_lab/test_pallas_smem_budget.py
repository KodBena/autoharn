#!/usr/bin/env python
"""nla_lab — the GUEST-PROVABLE gate for the Pallas disentangled-flash sm_75 fix.

The host run on the 2080Ti (sm_75) compile-FAILED with `ValueError: Mosaic GPU kernel
exceeds available shared memory: smem_bytes`. Two root causes, both turned into things
the CPU guest CAN prove (ADR-0009 guest/host split; ADR-0000 "tiles exceed SMEM" made a
CAUGHT arithmetic error, not a host surprise):

  1. The SMEM BUDGET is a DERIVED arithmetic claim (`_pallas_disent_attention.smem_bytes`):
     the chosen tiles (block 32) fit Turing's 48 KiB default; block 64 / num_stages 2 /
     the broken `[block, 2span]` residence are CAUGHT here, never on the host.
  2. The RETILING is fidelity-NEUTRAL: moving the position buffers from `[block, 2span]`
     SRAM staging to an global-memory-resident per-tile gather, and pinning the Triton backend, do
     NOT change the math — the EXACT ~1e-5 fold of §2 is preserved, RE-MEASURED in
     interpret mode vs `exact_reference` at several (B, S) including multi-tile.

What the guest CANNOT prove (HOST gate, NOT asserted here): that Pallas-Triton actually
COMPILES + RUNS the fp32 kernel on sm_75 with these tiles and the OOM cell goes green.
The guest is CPU jax with no CUDA jaxlib — interpret mode exercises the kernel LOGIC, not
the Triton lowering of the global memory gather (honest: the gather's lowering is host-gate-selected;
the banded-`2span`-slice fallback is recorded in the kernel module if it does not lower).

Run:  python -m pytest -q nla_lab/test_pallas_smem_budget.py   (from fact-mining/, CPU jax)
"""

from __future__ import annotations

import jax

import jax_deberta
from nla_lab import lab_corpus, lab_measure
from nla_lab.registry import load_all, make
from nla_lab.variants._pallas_disent_attention import (
    TURING_SMEM_BUDGET_BYTES,
    TURING_SMEM_CARVEOUT_MAX_BYTES,
    smem_bytes,
)

jax.config.update("jax_platform_name", "cpu")  # type: ignore[no-untyped-call]  # jax.config is untyped

# DeBERTa-v3 device dims the budget is sized against: head_size=64, fp32.
_D: int = 64


# ============================================================ root cause #2: SMEM budget
def test_chosen_tiles_fit_turing_default() -> None:
    """SHIPPED config (block 32, num_stages 1, global-memory-gather residence) -> 45312 bytes
    (44.25 KB) <= the conservative 48 KiB static-default SMEM cap, with ~3.8 KB headroom.
    This is the arithmetic that makes the host's `exceeds available shared memory` a CAUGHT
    error: when this passes, the tiles PROVABLY fit (smem_bytes is a conservative upper bound)."""
    assert smem_bytes(32, 32, d=_D, num_stages=1) == 45312
    assert smem_bytes(32, 32, d=_D, num_stages=1) <= TURING_SMEM_BUDGET_BYTES   # 48 KiB
    assert smem_bytes(32, 32, d=_D, num_stages=1) <= TURING_SMEM_CARVEOUT_MAX_BYTES  # 64 KiB


def test_num_stages_2_is_caught() -> None:
    """The autotune knob the gate FENCES: num_stages=2 at block 32 is 73984 bytes, which
    re-overflows even the 64 KiB carveout -> admissible ONLY behind a host profile, never
    the guaranteed-fit default. Caught here, not rediscovered on the host."""
    assert smem_bytes(32, 32, d=_D, num_stages=2) == 73984
    assert smem_bytes(32, 32, d=_D, num_stages=2) > TURING_SMEM_CARVEOUT_MAX_BYTES


def test_block64_is_caught() -> None:
    """block 64 (square 115200, and 64x32 = 74240) overflows even the 64 KiB carveout ->
    NOT shipped; block 32 is the Turing answer, and the gate PROVES the exclusion."""
    assert smem_bytes(64, 64, d=_D, num_stages=1) == 115200
    assert smem_bytes(64, 64, d=_D, num_stages=1) > TURING_SMEM_CARVEOUT_MAX_BYTES
    assert smem_bytes(64, 32, d=_D, num_stages=1) == 74240
    assert smem_bytes(64, 32, d=_D, num_stages=1) > TURING_SMEM_CARVEOUT_MAX_BYTES


def test_broken_2span_residence_is_caught() -> None:
    """The host's ACTUAL failure mode reproduced as arithmetic: the old `[block, 2span]`
    SRAM staging at block 128, span 256 is 721920 bytes (705 KB) -> 11x the 64 KiB max.
    `pos_resident_2span>0` selects that broken residence model; it must be CAUGHT, proving
    the shipped gather residence (pos_resident_2span=0) is what removed the overflow."""
    assert smem_bytes(128, 128, d=_D, pos_resident_2span=256) == 721920
    assert smem_bytes(128, 128, d=_D, pos_resident_2span=256) > TURING_SMEM_CARVEOUT_MAX_BYTES
    # the SAME tiles with the gather residence (the fix) are vastly smaller (still > budget
    # at block 128, but the [block,2span] term is gone) -> the residence change is the lever.
    assert smem_bytes(128, 128, d=_D, pos_resident_2span=0) < \
        smem_bytes(128, 128, d=_D, pos_resident_2span=256)


# ===================================================== root cause #2: retiling is EXACT
def _fidelity_at(batch: int, seq: int) -> tuple[float, float]:
    """Run PallasFlashAttention (interpret) and exact_reference on the SAME synthetic
    DeBERTa + seeded corpus; return (max|Δ|, mean|Δ|) over REAL tokens. `seq>32` spans
    multiple block-32 q/k tiles (the multi-tile online-softmax path)."""
    load_all()
    cfg = lab_measure.synthetic_cfg()
    params = lab_measure.synthetic_deberta(cfg, vocab=100, intermediate=64, seed=0)
    ids, mask = lab_measure.lift_batch(*lab_corpus.make_batch(batch, seq, vocab=100, seed=0))
    pallas = lab_measure.run_lhs(make("pallas_flash_attention"), params, ids, mask, cfg)
    ref = lab_measure.run_lhs(make("exact_reference"), params, ids, mask, cfg)
    return lab_measure.fidelity_delta(pallas, ref, mask)


def test_retiling_preserves_exact_fidelity() -> None:
    """The EXACT-tier (~1e-5) claim, RE-MEASURED after the retiling (ADR-0009 MEASURED).
    The Pallas kernel computes the same per-element disentangled score as the dense
    reference, differing only in softmax REDUCTION ORDER (online vs one-shot) — the backend
    pin and the global-memory-gather residence change NOTHING about the math, so the fold stays exact.
    Covered at single-tile (seq<=32) AND multi-tile (seq=64, 96 -> 2 and 3 block-32 tiles)."""
    for batch, seq in [(1, 16), (1, 32), (2, 64), (1, 96)]:
        max_abs, mean_abs = _fidelity_at(batch, seq)
        assert max_abs <= 1e-5, f"(B={batch},S={seq}) max|Δ|={max_abs} exceeds the EXACT 1e-5 tier"
        assert mean_abs <= 1e-5


def test_multitile_actually_exercises_multiple_tiles() -> None:
    """Guard that the multi-tile fidelity case is non-vacuous: with _TILE_TARGET=32, seq=64
    forces block=32 and >1 q/k tiles (the online-softmax rescale path), so the EXACT result
    is a real test of the recurrence, not a single-tile degenerate."""
    from nla_lab.variants import pallas_flash_attention as pfa
    assert pfa._TILE_TARGET == 32
    seq = 64
    block = min(pfa._TILE_TARGET, seq)
    assert seq // block >= 2, "seq=64 must span >=2 block-32 tiles for the multi-tile path"


if __name__ == "__main__":
    for _n, _fn in sorted(globals().items()):
        if _n.startswith("test_") and callable(_fn):
            _fn()
            print(f"PASS {_n}")
