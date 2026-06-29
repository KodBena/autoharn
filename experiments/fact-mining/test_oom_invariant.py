#!/usr/bin/env python
"""THE NEVER-OOM INVARIANT (ADR-0000 — foreclose the OOM CLASS, not an instance).

The batched jax-unified encode OOMed on ~96 paragraphs (`RESOURCE_EXHAUSTED ... jit_*`)
because the chunker bounded the LINEAR padded footprint B*max_S against a GUESSED constant
(8192 "padded tokens"), while a deberta-v3 forward's peak is DOMINATED by the QUADRATIC
disentangled-attention scores [B, num_heads, S, S]. A linear bound cannot see a quadratic
peak, so it could only ever fix the one input that happened to fail.

This file is the guest-provable proof that the replacement (`shape_buckets.peak_variable_bytes`
+ `chunk_by_vram` / `encode_batch_chunks`) makes the OOM class UNREPRESENTABLE — every chunk's
DERIVED peak is <= the free arena, over a spread of doc-length distributions INCLUDING
pathological ones — AND that the model is a CONSERVATIVE upper bound (over-estimate, never
under). Crucially, the same property test, run against the OLD linear chunker, FAILS (it packs
a quadratic over-budget chunk) — the defect is reproduced and the fix closes it.

Framework-free: pure `shape_buckets` arithmetic + python, so it runs on the guest in
milliseconds without jax/torch. The GPU OOM-NOT-happening on the full book is the host's to
confirm (the model + the chunker are proven here; only the exact constants are host-profilable).

Run:  python -m pytest test_oom_invariant.py -q
"""

from __future__ import annotations

import pytest

import shape_buckets as SB


# ----------------------------------------------------------- realistic memory models
def _v3_large_mm() -> SB.MemModel:
    """deberta-v3-large architecture (num_heads=16, hidden=1024, intermediate=4096,
    pos_ebd_size=256) with the SHIPPED conservative co-residency multiples — the model the
    daemon actually runs."""
    return SB.MemModel(num_heads=16, hidden=1024, intermediate=4096, pos_ebd_size=256)


# The 2080Ti / mem_fraction=0.3 scenario, DERIVED exactly as coref_host_shell.available_vram_bytes
# derives it from the live arena, but with the card's numbers spelled out so the gate is
# self-contained (the host run confirms the live values match).
_CARD_TOTAL = 11811160064               # 2080Ti, 11 GiB
_ARENA = int(0.30 * _CARD_TOTAL)        # XLA_PYTHON_CLIENT_MEM_FRACTION=0.3
_WEIGHTS = 1_740_000_000                # deberta-v3-large (~435M params * 4B) + small decode
_AVAIL_2080TI = _ARENA - _WEIGHTS - SB.headroom_bytes(_ARENA)


# --------------------------------------------- the OLD linear chunker (the reproduced defect)
def _linear_chunker(lengths, max_padded_tokens, max_docs):
    """A faithful copy of the REPLACED `chunk_by_token_budget` — the linear B*max_S budget.
    Present ONLY so the property test can demonstrate it VIOLATES the never-OOM invariant
    (packs a chunk whose true quadratic peak exceeds the arena). This is the code the fix
    removed; it must FAIL the invariant the new chunker satisfies."""
    chunks, cur, cur_max = [], [], 0
    for i, n in enumerate(lengths):
        cand_max = n if n > cur_max else cur_max
        cand_cells = cand_max * (len(cur) + 1)
        if cur and (len(cur) >= max_docs or cand_cells > max_padded_tokens):
            chunks.append(cur)
            cur, cur_max = [i], n
        else:
            cur.append(i)
            cur_max = cand_max
    if cur:
        chunks.append(cur)
    return chunks


def _worst_chunk_peak(chunks, lengths, mm):
    return max(
        (SB.peak_variable_bytes(mm, len(ch), max(lengths[j] for j in ch)) for ch in chunks),
        default=0)


# ===================================================== (a) THE NEVER-OOM INVARIANT (headline)
# Distributions that EVERY doc fits at B=1 under _AVAIL_2080TI (max real length 1024), so the
# chunker never has to raise — the question is purely whether it keeps EVERY chunk within the
# arena. The single-huge-doc (raise) case is the separate gate below.
_PATHOLOGICAL = [
    pytest.param([128] * 96, id="the-defect-96x128"),          # the reproduced OOM workload
    pytest.param([1024] * 20, id="many-max-fittable-1024"),    # all at the largest B=1-fittable rung
    pytest.param([512] * 50, id="many-512"),
    pytest.param([900] * 8 + [40] * 80, id="mixed-large-and-tiny"),
    pytest.param([64, 1024, 64, 1024, 64, 1024] * 6, id="alternating-tiny-large"),
    pytest.param([i % 1024 + 1 for i in range(200)], id="ramp-1..1024"),
    pytest.param([1] * 500, id="500-singletons"),
]


@pytest.mark.parametrize("lengths", _PATHOLOGICAL)
def test_chunk_by_vram_never_exceeds_available(lengths):
    """EVERY chunk the VRAM chunker emits provably fits the free arena (the never-OOM
    invariant) — and order/coverage are preserved, no doc dropped."""
    mm = _v3_large_mm()
    chunks = SB.chunk_by_vram(lengths, mm, _AVAIL_2080TI, SB.ENCODE_MAX_DOCS)
    flat = [i for ch in chunks for i in ch]
    assert flat == list(range(len(lengths))), "order/coverage broken"
    for ch in chunks:
        s_max = max(lengths[j] for j in ch)
        peak = SB.peak_variable_bytes(mm, len(ch), s_max)
        assert peak <= _AVAIL_2080TI, (
            f"chunk {ch[:3]}… (B={len(ch)}, S={s_max}) peak {peak} > available {_AVAIL_2080TI}")
        assert len(ch) <= SB.ENCODE_MAX_DOCS


def test_linear_budget_FAILS_the_never_oom_invariant():
    """The defect, reproduced: the OLD linear chunker (8192-token budget) packs a chunk whose
    TRUE quadratic peak BLOWS PAST the arena — i.e. it would OOM. This is the test that must
    fail on the pre-fix code and pass (the violation is real) here, proving the linear bound was
    structurally unsafe, not merely mis-tuned."""
    mm = _v3_large_mm()
    lengths = [128] * 96  # the reproduced workload
    linear = _linear_chunker(lengths, 8192, SB.ENCODE_MAX_DOCS)
    vram = SB.chunk_by_vram(lengths, mm, _AVAIL_2080TI, SB.ENCODE_MAX_DOCS)
    linear_peak = _worst_chunk_peak(linear, lengths, mm)
    vram_peak = _worst_chunk_peak(vram, lengths, mm)
    assert linear_peak > _AVAIL_2080TI, (
        "linear budget did NOT overflow — fixture too weak to reproduce the OOM")
    assert vram_peak <= _AVAIL_2080TI, "the VRAM chunker must keep every chunk within the arena"
    # the linear budget over-commits by a large multiple — this is the silent OOM it caused.
    assert linear_peak > 1.5 * _AVAIL_2080TI
    print(f"\n[never-OOM] 96x128: linear worst-chunk peak={linear_peak/2**30:.2f} GiB "
          f"(> arena {_AVAIL_2080TI/2**30:.2f} GiB -> OOM); vram worst-chunk peak="
          f"{vram_peak/2**30:.2f} GiB (fits).")


# ===================================================== (b) the model is a CONSERVATIVE UPPER bound
@pytest.mark.parametrize("S", [16, 64, 128, 256, 512, 1024, 2048])
@pytest.mark.parametrize("B", [1, 2, 8, 32])
def test_peak_dominates_the_real_materialized_buffers(S, B):
    """The model's peak is >= each dominant tensor the forward MUST materialise — so it cannot
    UNDER-estimate the real peak (the only failure the invariant forbids). It bounds, at least:
    one [B,H,S,S] attention-score buffer, one [B,S,hidden] activation, one [B,S,intermediate]
    FFN buffer, AND one [B*H,S,2*pos_ebd_size] disentangled intermediate — each multiplied by a
    co-residency count >= 1, so the model >= each real buffer by construction. (That the COUNTS
    over-estimate co-residency is the reasoned argument in peak_variable_bytes' docstring; the
    host run profiles the exact constants.)"""
    mm = _v3_large_mm()
    b4 = mm.bytes_per_elem
    peak = SB.peak_variable_bytes(mm, B, S)
    one_score = B * mm.num_heads * S * S * b4
    one_act = B * S * mm.hidden * b4
    one_ffn = B * S * mm.intermediate * b4
    one_disent = B * mm.num_heads * S * (2 * mm.pos_ebd_size) * b4
    assert peak >= one_score, "model under-counts the [B,H,S,S] attention scores"
    assert peak >= one_score + one_act + one_ffn + one_disent, (
        "model must dominate the SUM of one of each dominant buffer (it holds several of each)")
    # and the quadratic term really is the asymptotically dominant one (the linear budget's blind
    # spot): at the largest length it exceeds the entire linear contribution.
    if S >= 512:
        quad = mm.k_quad * B * mm.num_heads * S * S * b4
        lin = B * S * (mm.a_hidden * mm.hidden + mm.a_inter * mm.intermediate) * b4
        assert quad > lin, "the quadratic term should dominate at large S"


def test_peak_is_exactly_linear_in_B():
    """peak_variable_bytes(mm, B, S) == B * peak_variable_bytes(mm, 1, S) EXACTLY — the property
    `max_batch_for_length` relies on to solve the inequality for B in O(1)."""
    mm = _v3_large_mm()
    for S in (1, 17, 128, 1024, 2048):
        base = SB.peak_variable_bytes(mm, 1, S)
        for B in (1, 2, 3, 7, 16, 64):
            assert SB.peak_variable_bytes(mm, B, S) == B * base, f"non-linear in B at S={S}, B={B}"


def test_max_batch_for_length_is_the_largest_fitting_B():
    """max_batch_for_length returns the largest B with peak(B,S) <= available, and that B+1 does
    NOT fit (the cap is tight, not merely safe) — and 0 exactly when even B=1 overflows."""
    mm = _v3_large_mm()
    for S in (64, 256, 512, 1024, 2048):
        for avail in (10**6, 10**8, _AVAIL_2080TI, 10**10):
            cap = SB.max_batch_for_length(mm, S, avail)
            assert cap >= 0
            if cap >= 1:
                assert SB.peak_variable_bytes(mm, cap, S) <= avail
            assert SB.peak_variable_bytes(mm, cap + 1, S) > avail, "cap is not the largest fitting B"
            assert (cap == 0) == (SB.peak_variable_bytes(mm, 1, S) > avail)


# ===================================================== (c) the single-huge-doc gate (loud, bounded)
def test_single_huge_doc_raises_bounded_not_oom():
    """A doc too big even at B=1 raises a CLEAR, BOUNDED DocTooLargeError carrying (tokens,
    needed, available) — NEVER a silent drop and NEVER a raw RESOURCE_EXHAUSTED. On the 2080Ti
    at mem_fraction=0.3 the 2048 rung is exactly such a doc (see the card gate below)."""
    mm = _v3_large_mm()
    huge = 2048
    assert SB.peak_variable_bytes(mm, 1, huge) > _AVAIL_2080TI  # premise: it really doesn't fit
    with pytest.raises(SB.DocTooLargeError) as ei:
        SB.chunk_by_vram([40, huge, 40], mm, _AVAIL_2080TI, SB.ENCODE_MAX_DOCS)
    assert ei.value.seq_len == huge
    assert ei.value.needed_bytes == SB.peak_variable_bytes(mm, 1, huge)
    assert ei.value.available_bytes == _AVAIL_2080TI
    assert "raise XLA_PYTHON_CLIENT_MEM_FRACTION" in str(ei.value)  # actionable remediation
    # the jax path (encode_batch_chunks on a uniform group) raises the SAME bounded error.
    with pytest.raises(SB.DocTooLargeError):
        SB.encode_batch_chunks([0, 1, 2], huge, mm, _AVAIL_2080TI)


def test_card_fit_profile_2080ti():
    """Document (and pin) what fits on the 2080Ti at mem_fraction=0.3 under the conservative
    model: rungs up to 1024 fit at B=1; the 2048 rung does NOT (it is the single-huge-doc case
    that fails LOUD). This makes the boundary explicit rather than discovered via an OOM, and is
    the value the host run's live arena query should corroborate."""
    mm = _v3_large_mm()
    fits = {S: SB.peak_variable_bytes(mm, 1, S) <= _AVAIL_2080TI
            for S in SB.ENCODE_LEN_BUCKETS}
    assert fits == {64: True, 128: True, 256: True, 512: True, 1024: True, 2048: False}, fits
    # the largest fittable rung admits a batch > 1 at the small end (so batching still pays off).
    assert SB.max_batch_for_length(mm, 64, _AVAIL_2080TI) >= 8
    assert SB.max_batch_for_length(mm, 1024, _AVAIL_2080TI) == 1
    print(f"\n[card fit 2080Ti@0.3] arena={_ARENA/2**30:.2f} GiB, weights={_WEIGHTS/2**30:.2f} "
          f"GiB, available={_AVAIL_2080TI/2**30:.2f} GiB; fittable rungs (B=1): "
          f"{[S for S, ok in fits.items() if ok]}; B(64)="
          f"{SB.max_batch_for_length(mm, 64, _AVAIL_2080TI)}.")


# ===================================================== (d) the jax B-ladder path stays within VRAM
@pytest.mark.parametrize("s_bucket", [64, 128, 256, 512, 1024])
@pytest.mark.parametrize("avail", [3 * 10**8, 10**9, _AVAIL_2080TI, 4 * 10**9])
def test_encode_batch_chunks_within_vram_and_on_ladder(s_bucket, avail):
    """The jax bucket-group path: the B chosen keeps peak(B, s_bucket) <= available for EVERY
    chunk AND is a fixed B-ladder rung (the compile bound). Skips the (s_bucket, avail) pairs
    where even B=1 doesn't fit — those correctly raise DocTooLargeError (covered above)."""
    mm = _v3_large_mm()
    if SB.peak_variable_bytes(mm, 1, s_bucket) > avail:
        with pytest.raises(SB.DocTooLargeError):
            SB.encode_batch_chunks(list(range(10)), s_bucket, mm, avail)
        return
    group = list(range(37))  # forces remainder chunks under most B
    chunks, b = SB.encode_batch_chunks(group, s_bucket, mm, avail)
    assert b in SB.ENCODE_BATCH_BUCKETS, f"B={b} not on the ladder"
    assert SB.peak_variable_bytes(mm, b, s_bucket) <= avail, "B-padded forward exceeds the arena"
    flat = [i for ch in chunks for i in ch]
    assert flat == group, "order/coverage broken in the B-ladder chunking"
    assert all(len(ch) <= b for ch in chunks)


# ===================================================== (e) the RETAINED-OUTPUT OOM class (FINDING 1)
# The per-forward budget proves forward_peak(chunk) <= available, but a consumer that decodes
# only AFTER encoding every doc holds EVERY [S_i, hidden] lhs slice co-resident on the SAME
# arena — an O(total docs) term the forward budget omits. These gates prove (i) the unreserved
# budget UNDER-counts the true co-resident peak on a book-scale corpus (the second OOM class,
# reproduced), and (ii) the two foreclosure tactics close it: reserving the retained sum
# (torch reference path) and bounding retention to one chunk (the streaming jax path).
def _retained(mm, lengths):
    return SB.retained_lhs_bytes(mm, lengths)


def test_retained_lhs_bytes_is_the_unpadded_slice_sum():
    """retained_lhs_bytes == Σ S_i * hidden * 4B — each doc's UNPADDED [S_i, hidden] fp32 lhs."""
    mm = _v3_large_mm()
    for lengths in ([], [10], [128] * 96, [1, 2, 3, 512]):
        expect = sum(lengths) * mm.hidden * mm.bytes_per_elem
        assert _retained(mm, lengths) == expect
    # linear in total tokens (a book's worth is GiB): 1000x512 retains ~2 GiB on v3-large.
    assert _retained(mm, [512] * 1000) == 1000 * 512 * 1024 * 4


def test_unreserved_budget_UNDERcounts_the_retained_accumulation():
    """THE SECOND OOM class, reproduced (the analog of test_linear_budget_FAILS_*): chunking
    against the RAW per-forward budget passes every chunk (each forward fits), yet on a
    book-scale corpus the retained slices ALONE + a later in-budget forward exceed the arena —
    a co-resident OOM the per-forward bound is blind to. This MUST hold on the un-reserved
    budget (so the gate is non-vacuous) and is exactly what the reservation/streaming close."""
    mm = _v3_large_mm()
    lengths = [512] * 1000  # a book chapter's worth of paragraphs (the defect was 96)
    raw_chunks = SB.chunk_by_vram(lengths, mm, _AVAIL_2080TI, SB.ENCODE_MAX_DOCS)
    worst_forward = _worst_chunk_peak(raw_chunks, lengths, mm)
    retained = _retained(mm, lengths)
    assert worst_forward <= _AVAIL_2080TI, "premise: each forward alone fits the per-forward budget"
    assert worst_forward + retained > _AVAIL_2080TI, (
        "fixture too weak: retained accumulation did not exceed the arena — strengthen the book")
    print(f"\n[retained OOM] 1000x512: each forward fits ({worst_forward/2**30:.2f} GiB) but "
          f"+Σretained ({retained/2**30:.2f} GiB) = {(worst_forward+retained)/2**30:.2f} GiB "
          f"> arena {_AVAIL_2080TI/2**30:.2f} GiB -> co-resident OOM the per-forward bound missed.")


@pytest.mark.parametrize("lengths", _PATHOLOGICAL)
def test_reserved_budget_holds_forward_PLUS_retained(lengths):
    """The torch-path foreclosure: chunking against forward_budget_after_retained guarantees the
    TRUE co-resident peak — every chunk's forward PLUS all retained slices — fits the arena."""
    mm = _v3_large_mm()
    retained = _retained(mm, lengths)
    if retained >= _AVAIL_2080TI:
        with pytest.raises(SB.RetainedTooLargeError):
            SB.forward_budget_after_retained(_AVAIL_2080TI, mm, lengths)
        return
    reserved = SB.forward_budget_after_retained(_AVAIL_2080TI, mm, lengths)
    chunks = SB.chunk_by_vram(lengths, mm, reserved, SB.ENCODE_MAX_DOCS)
    for ch in chunks:
        forward = SB.peak_variable_bytes(mm, len(ch), max(lengths[j] for j in ch))
        assert forward + retained <= _AVAIL_2080TI, (
            f"co-resident peak forward {forward} + retained {retained} > arena {_AVAIL_2080TI}")


def test_retained_too_large_is_loud_and_bounded():
    """When the retained set alone leaves no room for a forward, forward_budget_after_retained
    raises a CLEAR, BOUNDED RetainedTooLargeError (carrying n_docs / retained / available and an
    actionable remediation) — NEVER a non-positive budget that mis-reports as a per-doc error,
    and NEVER a raw RESOURCE_EXHAUSTED."""
    mm = _v3_large_mm()
    book = [512] * 4000  # ~8 GiB of slices on v3-large, far past the ~1 GiB 2080Ti arena
    assert _retained(mm, book) > _AVAIL_2080TI
    with pytest.raises(SB.RetainedTooLargeError) as ei:
        SB.forward_budget_after_retained(_AVAIL_2080TI, mm, book)
    assert ei.value.n_docs == 4000
    assert ei.value.retained_bytes == _retained(mm, book)
    assert ei.value.available_bytes == _AVAIL_2080TI
    assert "STREAMING jax-unified" in str(ei.value)  # points at the capacity-preserving path
    # a small corpus is unaffected — the reservation is transparent when slices are tiny.
    small = [128] * 96  # the original defect workload: ~48 MiB retained, trivially fits
    assert SB.forward_budget_after_retained(_AVAIL_2080TI, mm, small) > 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", "-s"]))
