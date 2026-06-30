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
    self-proof keys off — NOT a global all-stub assumption. exact_reference is IMPLEMENTED;
    the seven portfolio stubs are not, until each agent flips the flag in their OWN file. So
    one agent's impl cannot red the shared self-test for the others."""
    load_all()
    assert make("exact_reference").IMPLEMENTED is True
    stubs = [n for n in REGISTRY if not n.startswith("_") and n != "exact_reference"]
    assert stubs, "expected the portfolio stubs to be registered"
    for n in stubs:
        assert make(n).IMPLEMENTED is False, f"{n} unexpectedly marked IMPLEMENTED"


def _one_batch() -> tuple[list[list[int]], list[list[int]]]:
    from nla_lab import lab_corpus
    return lab_corpus.make_batch(batch=1, seq_bucket=64, vocab=100, seed=0)


if __name__ == "__main__":
    for n, fn in sorted(globals().items()):
        if n.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {n}")
