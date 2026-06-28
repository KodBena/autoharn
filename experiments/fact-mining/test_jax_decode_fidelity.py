#!/usr/bin/env python
"""HOST fidelity proof: pure-JAX decode tail == maverick, BIT-EXACT cluster sets.

ADR-0009 two-tier equivalence in action. We do NOT assert float logits match
torch. We assert the DISCRETE INVARIANT: the set of coreference clusters (as
sets of token-offset spans) produced by `coref_host_shell.decode_document`
(driving the pure `jax_decode` core) is exactly equal — order-independent,
within and across clusters — to maverick's captured `clusters_token_offsets`.

Runs on the HOST (jax installed). It is the falsifier for every assumption the
guest-side static reasoning could not execute. In the guest (no jax) this file's
import simply fails to collect; that does NOT affect the two pure-`ast` gates,
which are independent files.

This file is the fixture-I/O boundary (numpy `np.load` of host fixtures -> jax
arrays); like capture_fixtures.py it is host-only test scaffolding and is not in
the device-pipeline gates' SCANNED set.

Run: pytest test_jax_decode_fidelity.py    (or: python test_jax_decode_fidelity.py)
"""

from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

# Make the port importable however this file is invoked (pytest / python / other
# cwd) — pytest's sys.path handling differs from `python file.py` and was the
# real cause of the "skip".
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import jax
    import jax.numpy as jnp
except ModuleNotFoundError as exc:   # genuinely no jax (e.g. the guest) -> legit skip
    _HAVE_JAX = False
    _IMPORT_ERR = exc
else:
    _HAVE_JAX = True
    jax.config.update("jax_enable_x64", False)  # match torch float32 exactly
    # NOT guarded: a failure importing the port is a REAL bug, not a benign skip.
    # The old broad `except Exception: skip` masked exactly this (ADR-0002) and
    # turned a pytest import failure into a silent "host-only, skipped".
    import coref_host_shell

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")


def _load_params(path: str) -> dict:
    """weights.npz -> dict[str, jnp.float32]. Single conversion seam (np -> jax)."""
    with np.load(path) as z:
        return {k: jnp.asarray(z[k], dtype=jnp.float32) for k in z.files}


def _cluster_set(clusters) -> set:
    """Order-independent canonical form: a set of frozensets of (start,end)."""
    return {frozenset((int(s), int(e)) for s, e in cluster) for cluster in clusters}


def _cases():
    return sorted(glob.glob(os.path.join(FIXTURES, "para_*.npz")))


def _run_case(params, npz_path: str, singletons: bool = False):
    """Run the shell on one fixture at the given `singletons` flag and return
    (got_set, want_set). `want` is maverick's matching captured variant."""
    stem = npz_path[:-len(".npz")]
    with open(stem + ".json", encoding="utf-8") as fh:
        meta = json.load(fh)
    with np.load(npz_path) as z:
        lhs = jnp.asarray(z["last_hidden_state"], dtype=jnp.float32)
        attention_mask = z["attention_mask"].tolist()
        eos_mask = z["eos_mask"].tolist()  # [S][S] python ints

    got = coref_host_shell.decode_document(
        params=params,
        lhs=lhs,
        attention_mask=attention_mask,
        eos_mask=eos_mask,
        tokens=meta["tokens"],
        subtoken_map=meta["subtoken_map"],
        new_token_map=meta["new_token_map"],
        singletons=singletons,
    )
    key = "clusters_token_offsets_singletons" if singletons else "clusters_token_offsets"
    want = meta[key]
    return _cluster_set(got), _cluster_set(want)


# ===================================================================== the proof
def test_decode_tail_bit_exact_cluster_sets():
    if not _HAVE_JAX:
        import pytest
        pytest.skip(f"jax/shell unavailable (host-only test): {_IMPORT_ERR}")
    cases = _cases()
    if not cases:
        import pytest
        pytest.skip("no fixtures — run capture_fixtures.py on the host first")

    params = _load_params(os.path.join(FIXTURES, "weights.npz"))
    failures = []
    wants = []
    for npz_path in cases:
        got, want = _run_case(params, npz_path)
        wants.append(want)
        if got != want:
            name = os.path.basename(npz_path)
            failures.append(
                f"{name}: cluster sets differ\n"
                f"    only in JAX     : {sorted(map(sorted, got - want))}\n"
                f"    only in maverick: {sorted(map(sorted, want - got))}"
            )
    assert not failures, (
        "decode-tail divergence (the discrete invariant ADR-0009 protects):\n"
        + "\n".join(failures)
    )
    # NON-VACUITY GUARD: `set() == set()` passes while proving nothing. Assert the
    # fixtures actually exercise the decode — at least one paragraph yields a
    # cluster, and at least one cluster has >=2 mentions (so stage-3 antecedent
    # argmax really fired). 6 literary paragraphs always have coref; if this trips,
    # the fixture set is degenerate (regenerate over real prose), not a real pass.
    assert any(want for want in wants), (
        "VACUOUS: no maverick clusters in ANY fixture — regenerate over real prose")
    assert any(any(len(c) >= 2 for c in want) for want in wants), (
        "VACUOUS: no fixture has a >=2-mention cluster — stage-3 argmax never exercised")


def test_singleton_decode_path_matches_maverick():
    """Prove the BUG-FIXED `singletons=True` branch (coref_host_shell:~292-305),
    which the default test never executes. Compares the shell at singletons=True
    against maverick's captured singletons=True clusters, and asserts the path is
    actually exercised (>=1 singleton, i.e. a size-1 cluster, somewhere)."""
    if not _HAVE_JAX:
        import pytest
        pytest.skip(f"jax/shell unavailable (host-only test): {_IMPORT_ERR}")
    cases = _cases()
    if not cases:
        import pytest
        pytest.skip("no fixtures — run capture_fixtures.py on the host first")

    params = _load_params(os.path.join(FIXTURES, "weights.npz"))
    failures, wants = [], []
    saw_singleton_field = False
    for npz_path in cases:
        stem = npz_path[:-len(".npz")]
        with open(stem + ".json", encoding="utf-8") as fh:
            meta = json.load(fh)
        if "clusters_token_offsets_singletons" not in meta:
            continue
        saw_singleton_field = True
        got, want = _run_case(params, npz_path, singletons=True)
        wants.append(want)
        if got != want:
            name = os.path.basename(npz_path)
            failures.append(
                f"{name}: singleton cluster sets differ\n"
                f"    only in JAX     : {sorted(map(sorted, got - want))}\n"
                f"    only in maverick: {sorted(map(sorted, want - got))}"
            )
    if not saw_singleton_field:
        import pytest
        pytest.skip("fixtures predate the singleton capture — re-run capture_fixtures.py")
    assert not failures, (
        "singleton decode-tail divergence:\n" + "\n".join(failures))
    # NON-VACUITY: the singleton branch only runs if some fixture HAS a singleton
    # (a size-1 cluster). If none do, singletons=True == singletons=False and the
    # BUG-FIXED path was never exercised -> fail loud, pick prose with lone entities.
    assert any(any(len(c) == 1 for c in want) for want in wants), (
        "VACUOUS: no singleton (size-1 cluster) in any fixture — the singletons=True "
        "branch was not exercised; regenerate over prose with lone-mention entities")


if __name__ == "__main__":
    if not _HAVE_JAX:
        raise SystemExit(f"jax unavailable: {_IMPORT_ERR}")
    cases = _cases()
    if not cases:
        raise SystemExit("no fixtures — run capture_fixtures.py first")
    params = _load_params(os.path.join(FIXTURES, "weights.npz"))
    ok = True
    for sing in (False, True):
        print(f"--- singletons={sing} ---")
        for npz_path in cases:
            stem = npz_path[:-len(".npz")]
            with open(stem + ".json", encoding="utf-8") as fh:
                has_field = "clusters_token_offsets_singletons" in json.load(fh)
            if sing and not has_field:
                print("  (fixtures predate singleton capture — re-run capture_fixtures.py)")
                break
            got, want = _run_case(params, npz_path, singletons=sing)
            same = got == want
            ok = ok and same
            print(f"  {'PASS' if same else 'FAIL'} {os.path.basename(npz_path)} "
                  f"(jax={len(got)} clusters, maverick={len(want)} clusters)")
    print("ALL BIT-EXACT" if ok else "DIVERGENCE")
    raise SystemExit(0 if ok else 1)
