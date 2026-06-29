#!/usr/bin/env python
"""GUEST-side proofs for THE CUT (batched encode SSOT + multi-doc decode wire).

These run WITHOUT maverick/GPU (the encode cluster-fidelity is host-only, confirmed by
`load_facts --coref-verify`). What they DO prove here, on the guest:

  1. the OOM bound exists and is correct — `shape_buckets.chunk_by_vram` caps each padded
     forward by the DERIVED quadratic-aware VRAM peak AND a doc count, preserves text order,
     never drops a doc, degrades to one-doc-per-chunk, and raises a bounded DocTooLargeError
     (never a raw OOM) for a doc too big even at B=1 (the never-OOM property itself, over
     pathological distributions, is the headline gate in test_oom_invariant.py);
  2. the multi-doc decode WIRE round-trips BIT-EXACT per doc — N docs' float32 lhs ->
     `_doc_meta`/`pack_lhs` -> raw bytes -> `unpack_lhs` == the original array, per doc;
  3. the multi-doc decode plumbing is correct end-to-end THROUGH THE REAL CLIENT AND
     SERVER CODECS (device decode stubbed, since maverick weights are host-only): a
     `decode_batch` of N docs returns N cluster-lists aligned to the request, each doc's
     lhs/maps arrive bit-exact at the (stubbed) decoder, and n==1 (the single-doc
     `decode` wrapper) is just the batch-of-1 case.

NOT proven here (host-only, flagged): that the BATCHED-encode cluster SETS equal the
SERIAL maverick reference. That needs the GPU encode + `--coref-verify`. n==1 has no
padding so the livewire single-doc oracle stays bit-exact; n>=2 padding fidelity is the
host's to confirm.

Run: python -m pytest test_batched_encode_and_multidoc_wire.py   (or python <thisfile>)
"""

from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import nlp_server  # noqa: F401  (kept: confirms the import surface still resolves after the rename)
import shape_buckets as SB
import coref_decode_client as C
import coref_decode_server as S


# ============================================================ (1) the OOM bound (VRAM-derived)
# A toy memory model with peak_variable_bytes(B, S) == B*S^2 (num_heads=k_quad=1, every other
# term zeroed, 1 byte/elem), so the chunk boundaries are hand-checkable. The REAL never-OOM
# property over pathological distributions — and that the OLD linear budget FAILS it — is the
# headline gate in test_oom_invariant.py; here we pin the chunker's contract (order, coverage,
# never-drop, degrade-to-one, and the loud single-huge-doc raise).
def _toy_mm():
    return SB.MemModel(num_heads=1, hidden=0, intermediate=0, pos_ebd_size=0,
                       bytes_per_elem=1, k_quad=1, k_disent=0, a_hidden=0, a_inter=0)


def test_chunk_by_vram_splits_and_preserves_order():
    mm = _toy_mm()
    # peak = B*S^2. available=250: [10,10]=2*100=200 ok; adding a 3rd =>3*100=300>250 -> split.
    assert SB.chunk_by_vram([10, 10, 10, 10], mm, 250, 64) == [[0, 1], [2, 3]]
    # the doc-count cap binds first when the arena is huge.
    assert SB.chunk_by_vram([1, 1, 1, 1, 1], mm, 10**18, 2) == [[0, 1], [2, 3], [4]]


def test_chunk_big_doc_fitting_alone_forms_own_chunk_never_dropped():
    mm = _toy_mm()
    # doc0 (S=100, peak@B=1 = 10000) fits ALONE at available=10000 but cannot SHARE
    # (peak@B=2,S=100 = 20000 > 10000), so it forms its own chunk and is NEVER dropped; the
    # two short docs (S=5) batch together. The safe floor: one doc per forward.
    assert SB.chunk_by_vram([100, 5, 5], mm, 10000, 64) == [[0], [1, 2]]


def test_chunk_single_huge_doc_raises_bounded_not_oom():
    mm = _toy_mm()
    # doc0 cannot fit even at B=1 (peak@B=1 = 10000 > available 5000): a LOUD, bounded
    # DocTooLargeError, NEVER a silent drop and NEVER a raw RESOURCE_EXHAUSTED.
    import pytest
    with pytest.raises(SB.DocTooLargeError) as ei:
        SB.chunk_by_vram([100, 5, 5], mm, 5000, 64)
    assert ei.value.seq_len == 100 and ei.value.available_bytes == 5000


def test_chunk_edge_cases():
    mm = _toy_mm()
    assert SB.chunk_by_vram([], mm, 8192, 64) == []
    assert SB.chunk_by_vram([7], mm, 8192, 64) == [[0]]            # n==1 fits (49 <= 8192)
    # a typical 5-paragraph request (S=120) stays in ONE forward when the arena is ample:
    # peak(5,120) = 5*120^2 = 72000 <= 80000.
    assert SB.chunk_by_vram([120] * 5, mm, 80000, SB.ENCODE_MAX_DOCS) == [[0, 1, 2, 3, 4]]


# ===================================================== (2) multi-doc wire bit-exact
def _synth_doc(rng, s, th):
    lhs = rng.standard_normal((s, th)).astype(np.float32)
    # stress float32 corners (subnormal, near-max, exact half) — JSON-decimal danger.
    lhs[0, 0] = np.float32(1e-38)
    lhs[s - 1, th - 1] = np.float32(-3.4e38)
    return {
        "lhs": lhs,
        "attention_mask": [1] * s,
        "eos_mask": [[1 if j >= i else 0 for j in range(s)] for i in range(s)],
        "tokens": [f"t{i}" for i in range(s)],
        "subtoken_map": list(range(s)),
        "new_token_map": list(range(s)),
    }


def test_multidoc_wire_lhs_roundtrip_is_bit_exact_per_doc():
    """N docs' float32 lhs -> the multi-doc codec frames -> unpack == original, per doc.
    Uses the REAL client per-doc packer (`_doc_meta`/`pack_lhs`) and the REAL server
    `unpack_lhs`, so any byte-order/contiguity/length slip surfaces here."""
    rng = np.random.default_rng(1)
    docs = [_synth_doc(rng, s, 13) for s in (37, 5, 64, 1)]
    for d in docs:
        meta, blob = C.RemoteDecode._doc_meta(d)
        back = S.unpack_lhs(meta, blob)            # the daemon's own unpack
        assert back.dtype == np.float32
        assert np.array_equal(back, d["lhs"]), "wire round-trip changed a value"
        assert back.tobytes() == d["lhs"].tobytes(), "wire round-trip changed bytes"


# =============================================== (3) end-to-end multi-doc plumbing
class _InProcessClient(C.RemoteDecode):
    """A RemoteDecode whose _roundtrip is wired straight into a DecodeServer.handle in
    THIS process — so the REAL client codec and the REAL server codec are exercised
    end-to-end with no socket and no jax/maverick (the device decode is stubbed)."""

    def __init__(self, server):
        self._server = server  # bypass __init__ (no socket)

    def _roundtrip(self, frames, timeout_ms=None):
        return self._server.handle(frames)


def _stub_server(monkeyrecord):
    """A DecodeServer with the device decode stubbed. The stub records what each doc
    delivered (lhs + maps + singletons) and returns a deterministic per-doc cluster
    that ENCODES the doc's identity (S), so alignment is checkable."""
    srv = S.DecodeServer.__new__(S.DecodeServer)
    srv.params = {}
    srv._seen_shapes = set()

    def fake_decode(params, lhs_host, attention_mask, eos_mask, tokens,
                    subtoken_map, new_token_map, singletons=False):
        s = int(lhs_host.shape[0])
        monkeyrecord.append({
            "lhs": np.array(lhs_host, copy=True), "attention_mask": attention_mask,
            "tokens": tokens, "subtoken_map": subtoken_map, "singletons": singletons,
        })
        # one cluster, one mention spanning the whole doc -> (0, S-1) identifies the doc.
        return [[(0, s - 1)]]

    S.coref_host_shell.decode_document_host = fake_decode  # patch the single device home
    return srv


def test_decode_batch_aligns_and_delivers_each_doc_bit_exact():
    record: list = []
    real = S.coref_host_shell.decode_document_host
    try:
        srv = _stub_server(record)
        client = _InProcessClient(srv)
        rng = np.random.default_rng(2)
        docs = [_synth_doc(rng, s, 9) for s in (11, 3, 47)]

        got = client.decode_batch(docs, singletons=True)

        # alignment: N docs in -> N cluster-lists out, each encoding ITS doc's S.
        assert len(got) == len(docs)
        for d, g in zip(docs, got):
            s = d["lhs"].shape[0]
            assert g == [[(0, s - 1)]], "per-doc result misaligned"
        # each doc's lhs + maps arrived bit-exact at the decoder, in order.
        assert len(record) == len(docs)
        for d, r in zip(docs, record):
            assert np.array_equal(r["lhs"], d["lhs"]), "lhs perturbed over the wire"
            assert r["attention_mask"] == d["attention_mask"]
            assert r["tokens"] == d["tokens"]
            assert r["singletons"] is True
    finally:
        S.coref_host_shell.decode_document_host = real


def test_single_doc_decode_is_batch_of_one():
    """The n==1 path: the single-doc `decode` wrapper returns ONE doc's clusters (the
    contract the existing fidelity tests rely on), via the same multi-doc codec."""
    record: list = []
    real = S.coref_host_shell.decode_document_host
    try:
        srv = _stub_server(record)
        client = _InProcessClient(srv)
        rng = np.random.default_rng(3)
        d = _synth_doc(rng, 17, 9)

        got = client.decode(
            lhs=d["lhs"], attention_mask=d["attention_mask"], eos_mask=d["eos_mask"],
            tokens=d["tokens"], subtoken_map=d["subtoken_map"],
            new_token_map=d["new_token_map"], singletons=False)

        # decode() returns ONE doc's clusters (not a list-of-docs) — batch-of-1 unwrapped.
        assert got == [[(0, 16)]]
        assert len(record) == 1
        assert np.array_equal(record[0]["lhs"], d["lhs"])
        assert record[0]["singletons"] is False
    finally:
        S.coref_host_shell.decode_document_host = real


def test_server_rejects_frame_count_mismatch():
    """FAIL LOUD (ADR-0002): a docs-vs-lhs-frame count mismatch is a protocol bug, not
    silently coerced. `handle` RAISES (the serve() loop is what turns that into an error
    reply), so a wrong frame count never half-decodes a request."""
    import json
    import pytest
    record: list = []
    real = S.coref_host_shell.decode_document_host
    try:
        srv = _stub_server(record)
        # 2 docs declared but only 1 lhs frame -> loud raise, no decode runs.
        meta = {"op": "decode", "singletons": False,
                "docs": [{"shape": [2, 2], "dtype": "float32"},
                         {"shape": [2, 2], "dtype": "float32"}]}
        blob = np.zeros((2, 2), dtype="<f4").tobytes()
        with pytest.raises(ValueError, match="lhs frame"):
            srv.handle([json.dumps(meta).encode(), blob])
        assert record == [], "no doc should decode on a malformed multi-doc request"
    finally:
        S.coref_host_shell.decode_document_host = real


def test_client_rejects_short_reply_clusters():
    """FAIL LOUD (ADR-0002/P5) on the REPLY direction too: if the daemon ever returns
    fewer doc-cluster lists than docs sent, `coref_clusters_jax_daemon` would zip-truncate
    SILENTLY. `decode_batch` must raise instead — the request frame-count is checked one
    way (server), this checks the other (client)."""
    import json
    import pytest

    class _ShortReplyClient(C.RemoteDecode):
        def __init__(self):
            pass  # no socket

        def _roundtrip(self, frames, timeout_ms=None):
            # reply with ONE cluster list regardless of how many docs were sent
            return [json.dumps({"ok": True, "clusters": [[]], "singletons": False}).encode()]

    client = _ShortReplyClient()
    rng = np.random.default_rng(4)
    docs = [_synth_doc(rng, s, 5) for s in (3, 4)]  # 2 docs sent, 1 returned
    with pytest.raises(C.RemoteError, match="doc-cluster list"):
        client.decode_batch(docs)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
