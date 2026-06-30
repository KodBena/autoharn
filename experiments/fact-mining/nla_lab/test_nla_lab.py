#!/usr/bin/env python
"""nla_lab conformance + self-proof gate (mechanizes ADR-0013 "prove it" / B4).

This is the CONFORMANCE TEST that backs "the 8 fill only their math" with a check,
not a docstring (B4): every registered variant is a by-TYPE `EncodeVariant` with the
exact `encode` arity, the exact-reference round-trips (fidelity-vs-self == 0), the
meta-wrapper composes over any variant unchanged (A11 completeness lever), off-ladder
buckets are unconstructable (ADR-0000), and the registry is fail-loud (A5).

Run:  python -m pytest -q nla_lab/test_nla_lab.py   (from fact-mining/, CPU jax)
"""

from __future__ import annotations

import inspect

import jax

import jax_deberta
import shape_buckets
from nla_lab import bench, lab_measure
from nla_lab.contract import Decorated, EncodeBucket, EncodeVariant, FidelityTier, Regime
from nla_lab.registry import REGISTRY, load_all, make, resolve

jax.config.update("jax_platform_name", "cpu")  # type: ignore[no-untyped-call]  # jax.config is untyped


def test_self_proof() -> None:
    """The end-to-end harness proof: exact_reference round-trips, the watchdog flags
    the broken variant, every stub is not_implemented/fit_retired."""
    bench.self_test()   # raises AssertionError on any violation


def test_all_registered_conform_by_type() -> None:
    """Every registry entry is an EncodeVariant subclass, instantiable (so its abstract
    `encode` is implemented), with the EXACT 4-arg encode signature == jax_deberta.encode
    and valid declared {regime, fidelity_tier}. A non-conforming impl is unrepresentable."""
    load_all()
    assert "exact_reference" in REGISTRY
    ref_sig = list(inspect.signature(jax_deberta.encode).parameters)  # [params, input_ids, attention_mask, cfg]
    for name in REGISTRY:
        obj = make(name)                       # by-TYPE: instantiable EncodeVariant (make checks)
        assert isinstance(obj, EncodeVariant), f"{name} is not an EncodeVariant"
        params = list(inspect.signature(obj.encode).parameters)
        assert params == ref_sig, (
            f"{name}.encode params {params} != jax_deberta.encode {ref_sig}")
        assert isinstance(obj.regime, Regime)
        assert isinstance(obj.fidelity_tier, FidelityTier)
        assert obj.name == name


def test_decorated_composition_is_identity() -> None:
    """A11 completeness lever: the meta-wrapper composes over ANY variant with zero
    interface change — Decorated(ExactReference()) yields a bit-identical output. If a
    decorator could not wrap the contract uniformly, the interface would be incomplete."""
    load_all()
    cfg = lab_measure.synthetic_cfg()
    params = lab_measure.synthetic_deberta(cfg, vocab=100, intermediate=64, seed=0)
    ids, mask = lab_measure.lift_batch(*_one_batch())
    inner = make("exact_reference")
    wrapped = Decorated(inner)
    assert wrapped.name == inner.name and wrapped.regime == inner.regime
    a = lab_measure.run_lhs(inner, params, ids, mask, cfg)
    b = lab_measure.run_lhs(wrapped, params, ids, mask, cfg)
    fmax, _ = lab_measure.fidelity_delta(a, b, mask)
    assert fmax == 0.0, f"Decorated changed the output: max|Δ|={fmax}"


def test_encode_bucket_rejects_off_ladder() -> None:
    """ADR-0000: an off-ladder (batch, seq_bucket) is unconstructable (no second ladder)."""
    EncodeBucket(batch=1, seq_bucket=64)        # on-ladder: ok
    for bad in (dict(batch=3, seq_bucket=64), dict(batch=1, seq_bucket=100)):
        try:
            EncodeBucket(**bad)
            raise AssertionError(f"off-ladder bucket {bad} was constructable")
        except ValueError:
            pass


def test_registry_unknown_is_loud() -> None:
    """A5/ADR-0002: resolve refuses to guess, naming the known set."""
    load_all()
    try:
        resolve("does_not_exist")
        raise AssertionError("resolve did not raise on an unknown name")
    except KeyError as e:
        assert "exact_reference" in str(e)


def _stub_encode(self: EncodeVariant, params: object, input_ids: object,
                 attention_mask: object, cfg: object) -> object:
    """A throwaway concrete `encode` body for the dynamically-built guard fixtures."""
    return None


def test_metadata_by_type_guard_is_non_vacuous() -> None:
    """R1-G / ADR-0000: the metadata guard is by TYPE, not by convention. A CONCRETE
    EncodeVariant that omits or mis-types {regime, fidelity_tier} is UNIMPORTABLE — the
    `__init_subclass__` guard raises TypeError at class-creation. Proven non-vacuous by
    building the bad classes DYNAMICALLY (so they never exist at module import, which would
    itself fail), and confirming the two exemptions (still-abstract base, dynamic-metadata
    wrapper) and the good case are admitted."""
    # (a) a metadata-less concrete variant is unrepresentable — TypeError names the gaps.
    try:
        type("MissingMeta", (EncodeVariant,), {"name": "x_missing", "encode": _stub_encode})
        raise AssertionError("metadata-less concrete EncodeVariant was constructable")
    except TypeError as e:
        assert "regime" in str(e) and "fidelity_tier" in str(e)

    # (b) a WRONG-TYPED metadatum (a bare str where a Regime is required) is caught too.
    try:
        type("WrongType", (EncodeVariant,),
             {"name": "x_wrong", "regime": "throughput",
              "fidelity_tier": FidelityTier.EXACT, "encode": _stub_encode})
        raise AssertionError("wrong-typed regime was constructable")
    except TypeError as e:
        assert "regime" in str(e)

    # (c) a still-ABSTRACT intermediate base (no encode) is EXEMPT — declares nothing yet.
    abstract_mid = type("AbstractMid", (EncodeVariant,), {})
    assert getattr(abstract_mid, "__abstractmethods__"), "intermediate base should still be abstract"

    # (d) a `_metadata_is_dynamic` wrapper (the Decorated posture) is EXEMPT.
    type("DynamicMeta", (EncodeVariant,),
         {"_metadata_is_dynamic": True, "encode": _stub_encode})

    # (e) a fully + correctly declared concrete variant is ADMITTED and instantiable.
    good = type("GoodMeta", (EncodeVariant,),
                {"name": "x_good", "regime": Regime.BOTH,
                 "fidelity_tier": FidelityTier.EXACT, "encode": _stub_encode})
    assert good().regime is Regime.BOTH


def test_implemented_flag_marks_stub_vs_real() -> None:
    """R3-F5: the per-variant `IMPLEMENTED` flag (default False = stub) is what the
    self-proof keys off — NOT a global all-stub assumption, so one agent's fill cannot
    red the shared self-test for the others.

    POST-BAKE-OFF STATE. The portfolio is now FILLED: each variant flipped `IMPLEMENTED`
    TRUE in its OWN file (contract: "a real implementation flips it TRUE in its own
    variant file"). The protective invariant therefore inverts from the build-phase
    "still stubs" to the completion invariant asserted here — every registered portfolio
    variant is IMPLEMENTED (a variant that silently reverted to a `NotImplementedError`
    stub, or never flipped its flag, fails). The fill-state-INDEPENDENT half of the
    mechanism — that `IMPLEMENTED` is a real per-variant OPT-IN that DEFAULTS to False,
    never vacuously true — is proven directly on a fresh subclass below."""
    load_all()
    assert make("exact_reference").IMPLEMENTED is True
    portfolio = [n for n in REGISTRY if not n.startswith("_")]
    assert portfolio, "expected the portfolio variants to be registered"
    for n in portfolio:
        assert make(n).IMPLEMENTED is True, f"{n} is registered but not IMPLEMENTED (stub?)"

    # MECHANISM (fill-state independent): a concrete variant that does NOT declare
    # IMPLEMENTED inherits the contract's False default — the flag is a real opt-in
    # signal, never globally/vacuously true. The deliberately-broken `_smoke_broken`
    # fixture stays underscore-excluded from the portfolio sweep above.
    fresh = type("FreshStub", (EncodeVariant,),
                 {"name": "x_fresh_stub", "regime": Regime.BOTH,
                  "fidelity_tier": FidelityTier.EXACT, "encode": _stub_encode})
    assert fresh().IMPLEMENTED is False, "IMPLEMENTED must default to False (opt-in marker)"


def test_default_est_peak_device_bytes_reuses_the_oom_model() -> None:
    """R-MEM: the DEFAULT `est_peak_device_bytes` genuinely REUSES the one OOM memory model
    (shape_buckets) — it is NOT a re-derived second model and NOT vacuous. exact_reference (the
    dense baseline, which keeps the default) must return EXACTLY
    `shape_buckets.peak_variable_bytes(dense_deberta_mem_model(cfg), B, S)` at a sample bucket,
    and that value must be a positive (non-trivial) byte count."""
    load_all()
    cfg = lab_measure.synthetic_cfg()
    bucket = EncodeBucket(batch=2, seq_bucket=128)
    expected_mm = shape_buckets.dense_deberta_mem_model(
        cfg.num_heads, cfg.head_size, cfg.pos_ebd_size)
    expected = shape_buckets.peak_variable_bytes(expected_mm, bucket.batch, bucket.seq_bucket)
    got = make("exact_reference").est_peak_device_bytes(bucket, cfg)
    assert got == expected, f"default est {got} != OOM-model bound {expected}"
    assert got > 0, "the default est_peak_device_bytes is vacuous (<= 0)"
    # and it is exactly linear in B (the OOM model's defining property — proves it is THAT model)
    b1 = make("exact_reference").est_peak_device_bytes(
        EncodeBucket(batch=1, seq_bucket=128), cfg)
    assert got == 2 * b1, "default est is not linear in B -> not the shared peak_variable_bytes"


def test_est_peak_device_bytes_override_is_honored() -> None:
    """R-MEM: a profile-changing variant OVERRIDES the default and the override is what the
    contract returns (the dense bound is NOT silently forced). Built dynamically so it never
    pollutes the registry; proven distinct from the default at the same bucket."""
    cfg = lab_measure.synthetic_cfg()
    bucket = EncodeBucket(batch=1, seq_bucket=64)

    def _flash_like_est(self: EncodeVariant, bkt: EncodeBucket,
                        c: object) -> int:           # drops the quadratic term -> a fixed sentinel
        return 4242

    Overrider = type("Overrider", (EncodeVariant,),
                     {"name": "x_override", "regime": Regime.BOTH,
                      "fidelity_tier": FidelityTier.EXACT, "encode": _stub_encode,
                      "est_peak_device_bytes": _flash_like_est})
    inst = Overrider()
    assert inst.est_peak_device_bytes(bucket, cfg) == 4242, "override not honored"
    # the override is genuinely different from the inherited dense default (non-vacuous proof)
    assert inst.est_peak_device_bytes(bucket, cfg) != \
        make("exact_reference").est_peak_device_bytes(bucket, cfg)
    # ...and a decorator over it MIRRORS the override, not the dense default (R-MEM delegation)
    assert Decorated(inst).est_peak_device_bytes(bucket, cfg) == 4242


def test_partition_flag_defaults_true_and_is_not_in_the_required_set() -> None:
    """The `partition_is_fidelity_preserving` flag defaults TRUE (coref is per-paragraph
    independent) and, unlike {name, regime, fidelity_tier}, is NOT in the by-TYPE required set —
    a concrete variant that declares the three required metadata but OMITS this flag is still
    importable (a defaulted flag must never make an existing variant unimportable)."""
    load_all()
    assert make("exact_reference").partition_is_fidelity_preserving is True
    # a concrete variant omitting the flag still imports (guard required-set unchanged)...
    ok = type("NoPartitionFlag", (EncodeVariant,),
              {"name": "x_nopart", "regime": Regime.BOTH,
               "fidelity_tier": FidelityTier.EXACT, "encode": _stub_encode})
    assert ok().partition_is_fidelity_preserving is True  # inherits the safe default
    # ...and a False declaration (a future cross-chunk-dependent model) is carried verbatim.
    cross = type("CrossChunk", (EncodeVariant,),
                 {"name": "x_cross", "regime": Regime.BOTH,
                  "fidelity_tier": FidelityTier.EXACT, "encode": _stub_encode,
                  "partition_is_fidelity_preserving": False})
    assert cross().partition_is_fidelity_preserving is False


def _one_batch() -> tuple[list[list[int]], list[list[int]]]:
    from nla_lab import lab_corpus
    return lab_corpus.make_batch(batch=1, seq_bucket=64, vocab=100, seed=0)


if __name__ == "__main__":
    for n, fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {n}")
