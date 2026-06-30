#!/usr/bin/env python
"""nla_lab — the GUEST-PROVABLE gate for the Pallas disentangled-flash sm_75 fix.

The host run on the 2080Ti (sm_75) compile-FAILED with `ValueError: Mosaic GPU kernel
exceeds available shared memory: smem_bytes`. Two root causes, both turned into things
the CPU guest CAN prove (ADR-0009 guest/host split; ADR-0000 "tiles exceed SMEM" made a
CAUGHT arithmetic error, not a host surprise):

  1. The SMEM BUDGET is a DERIVED arithmetic claim (`_pallas_disent_attention.smem_bytes`):
     the band-select residence (block 32, W 64) is 53504 B — PAST the 48 KiB default but
     inside the <=64 KiB sm_75 carveout; block 64 / num_stages 2 / the broken `[block, 2span]`
     residence are CAUGHT here, never on the host.
  2. The SELECTION RE-EXPRESSION is fidelity-NEUTRAL: replacing the c2p/p2c advanced-index
     gather (the sm_75 `Unimplemented primitive ... gather` wall) with a `pl.ds(base,W)` band
     slice + one-hot comparison-sum is BIT-IDENTICAL to the gather (smoke_equiv `== 0.0`), so
     the EXACT ~1e-5 fold of §2 is preserved, RE-MEASURED in interpret mode vs `exact_reference`
     at several (B, S) including multi-tile.

What the guest CANNOT prove (HOST gate, NOT asserted here): that Pallas-Triton actually
COMPILES + RUNS the fp32 kernel on sm_75 with these tiles and the OOM cell goes green, and
that the band's `pl.ds(base,W)` lowers where the `gather` did not. The guest is CPU jax with
no CUDA jaxlib — interpret mode exercises the kernel LOGIC and lowers BOTH gather and band
(non-discriminating for the host wall). The structural argument: `pl.ds(base,W)` is the SAME
`dynamic_slice` the k-loop already lowers with `pl.dslice(kj0, block_k)`, fed a traced int32
Triton cannot tell from `kj0`; the host re-run on the 2080Ti settles it.

Run:  python -m pytest -q nla_lab/test_pallas_smem_budget.py   (from fact-mining/, CPU jax)
"""

from __future__ import annotations

import jax
import pytest

import jax_deberta
from nla_lab import lab_corpus, lab_measure
from nla_lab.registry import load_all, make
from nla_lab.variants._pallas_disent_attention import (
    TURING_SMEM_BUDGET_BYTES,
    TURING_SMEM_CARVEOUT_MAX_BYTES,
    Pow2,
    pow2,
    smem_bytes,
)

jax.config.update("jax_platform_name", "cpu")  # type: ignore[no-untyped-call]  # jax.config is untyped

# DeBERTa-v3 device dims the budget is sized against: head_size=64, fp32. Branded Pow2 — the
# kernel + smem_bytes only accept power-of-2 dims now (a raw int is a mypy error).
_D: Pow2 = pow2(64)


# ============================================================ root cause #2: SMEM budget
def test_gather_residence_baseline_fits_default() -> None:
    """The PRIOR per-tile gather residence (block 32, num_stages 1) -> 45312 bytes (44.25 KB)
    <= the conservative 48 KiB static-default SMEM cap. This is no longer the SHIPPED seam (the
    band-select below is — `gather` does not lower on sm_75 Triton), but its arithmetic stays
    the BASELINE the band's +8 KiB cost is measured against, and a conservative upper bound."""
    assert smem_bytes(pow2(32), pow2(32), d=_D, num_stages=1) == 45312
    assert smem_bytes(pow2(32), pow2(32), d=_D, num_stages=1) <= TURING_SMEM_BUDGET_BYTES   # 48 KiB
    assert smem_bytes(pow2(32), pow2(32), d=_D, num_stages=1) <= TURING_SMEM_CARVEOUT_MAX_BYTES  # 64 KiB


def test_band_select_fits_carveout_not_default() -> None:
    """SHIPPED seam: the banded-select residence (block 32, W 64, num_stages 1) -> 53504 bytes
    (52.25 KB). It pushes PAST the 48 KiB static default INTO the <=64 KiB sm_75 dynamic-SMEM
    carveout (intended — the band replaces the un-lowerable `gather` with a `pl.ds(base,W)`
    slice + one-hot sum). The +8192 B over the gather baseline is exactly the two `[block,W]`
    bands (`c2p_band` + `p2c_band`). Whether the sm_75 driver GRANTS 52.25 KiB is a HOST gate."""
    band = smem_bytes(pow2(32), pow2(32), d=_D, num_stages=1, band_w=pow2(64))
    assert band == 53504
    assert band > TURING_SMEM_BUDGET_BYTES                     # past the 48 KiB static default
    assert band <= TURING_SMEM_CARVEOUT_MAX_BYTES              # inside the 64 KiB carveout
    assert band - smem_bytes(pow2(32), pow2(32), d=_D, num_stages=1) == 8192   # +8 KiB = 2 bands


def test_band_num_stages_2_is_caught() -> None:
    """The autotune knob the band gate FENCES: num_stages=2 with the band at block 32 / W 64 is
    90368 bytes, which re-overflows even the 64 KiB carveout -> admissible ONLY behind a host
    profile, never the guaranteed-fit default. Caught here, not rediscovered on the host."""
    assert smem_bytes(pow2(32), pow2(32), d=_D, num_stages=2, band_w=pow2(64)) == 90368
    assert smem_bytes(pow2(32), pow2(32), d=_D, num_stages=2, band_w=pow2(64)) > TURING_SMEM_CARVEOUT_MAX_BYTES


def test_num_stages_2_is_caught() -> None:
    """The autotune knob the gate FENCES: num_stages=2 at block 32 is 73984 bytes, which
    re-overflows even the 64 KiB carveout -> admissible ONLY behind a host profile, never
    the guaranteed-fit default. Caught here, not rediscovered on the host."""
    assert smem_bytes(pow2(32), pow2(32), d=_D, num_stages=2) == 73984
    assert smem_bytes(pow2(32), pow2(32), d=_D, num_stages=2) > TURING_SMEM_CARVEOUT_MAX_BYTES


def test_block64_is_caught() -> None:
    """block 64 (square 115200, and 64x32 = 74240) overflows even the 64 KiB carveout ->
    NOT shipped; block 32 is the Turing answer, and the gate PROVES the exclusion."""
    assert smem_bytes(pow2(64), pow2(64), d=_D, num_stages=1) == 115200
    assert smem_bytes(pow2(64), pow2(64), d=_D, num_stages=1) > TURING_SMEM_CARVEOUT_MAX_BYTES
    assert smem_bytes(pow2(64), pow2(32), d=_D, num_stages=1) == 74240
    assert smem_bytes(pow2(64), pow2(32), d=_D, num_stages=1) > TURING_SMEM_CARVEOUT_MAX_BYTES


def test_broken_2span_residence_is_caught() -> None:
    """The host's ACTUAL failure mode reproduced as arithmetic: the old `[block, 2span]`
    SRAM staging at block 128, span 256 is 721920 bytes (705 KB) -> 11x the 64 KiB max.
    `pos_resident_2span>0` selects that broken residence model; it must be CAUGHT, proving
    the shipped gather residence (pos_resident_2span=0) is what removed the overflow."""
    assert smem_bytes(pow2(128), pow2(128), d=_D, pos_resident_2span=256) == 721920
    assert smem_bytes(pow2(128), pow2(128), d=_D, pos_resident_2span=256) > TURING_SMEM_CARVEOUT_MAX_BYTES
    # the SAME tiles with the gather residence (the fix) are vastly smaller (still > budget
    # at block 128, but the [block,2span] term is gone) -> the residence change is the lever.
    assert smem_bytes(pow2(128), pow2(128), d=_D, pos_resident_2span=0) < \
        smem_bytes(pow2(128), pow2(128), d=_D, pos_resident_2span=256)


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
    """The EXACT-tier (~1e-5) claim, RE-MEASURED after the band-select (ADR-0009 MEASURED).
    The Pallas kernel computes the same per-element disentangled score as the dense
    reference, differing only in softmax REDUCTION ORDER (online vs one-shot) — the backend
    pin and the gather->band-slice+one-hot selection change NOTHING about the math (the band
    is bit-identical to the gather, smoke_equiv `== 0.0`), so the fold stays exact.
    Covered at single-tile (seq<=32) AND multi-tile (seq=64, 128 -> 2 and 4 block-32 tiles). NB:
    seq must be a POWER OF 2 (the kernel's k/v/idx1d shapes are pow2 — the Pow2 boundary enforces
    it; the prior `seq=96` here was a latent bug interpret mode tolerated but Triton would reject)."""
    for batch, seq in [(1, 16), (1, 32), (2, 64), (1, 128)]:
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


# ============================================= ADR-0000: the power-of-2 invariant, BY TYPE
def test_pow2_brands_and_rejects_the_2s_minus_1_trap() -> None:
    """`pow2` is the ONLY source of `Pow2`; it brands a power of two and REJECTS anything else
    — a non-pow2 kernel dimension is UNCONSTRUCTABLE, not merely checked. The exact value that
    shipped to Triton, 2S-1=127 (one below the power of 2 128), raises here on the guest."""
    assert pow2(128) == 128 and pow2(32) == 32            # branding is identity on a power of 2
    for bad in (127, 0, 96, 130, 2 * 64 - 1):             # 127 = 2*64-1: the host's failing shape (127,)
        with pytest.raises(ValueError, match="power of 2"):
            pow2(bad)


def test_idx1d_length_is_a_power_of_two_per_S() -> None:
    """The fix: `_build_idx1d` returns length 2S (the natural 2S-1 padded by one inert slot), a
    power of two for every S on the ladder — so it constructs a `Pow2` at the kernel boundary
    instead of detonating Triton. The OLD natural length 2S-1 is exactly what `pow2` rejects."""
    from nla_lab.variants.pallas_flash_attention import _build_idx1d
    cfg = lab_measure.synthetic_cfg()
    for s in (64, 128, 256, 512):
        n = int(_build_idx1d(s, cfg).shape[0])
        assert n == 2 * s and pow2(n) == n                # the padded length IS a Pow2
        with pytest.raises(ValueError):                   # the natural 2S-1 would NOT be
            pow2(2 * s - 1)


if __name__ == "__main__":
    for _n, _fn in sorted(globals().items()):
        if _n.startswith("test_") and callable(_fn):
            _fn()
            print(f"PASS {_n}")
