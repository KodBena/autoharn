#!/usr/bin/env python
"""The TYPED CONTRACT every NLA encode-variant satisfies (ADR-0000 / ADR-0012 P8).

WHY A TYPE, NOT A CONVENTION (ADR-0000). The control_lab model this ports proved
its interface "FROZEN" by a docstring and a `@runtime_checkable` Protocol — which
checks only that method *names* exist at isinstance time, never the signature, so a
variant with the wrong `encode` arity is REPRESENTABLE and only detonates deep in
the bench (the by-convention-not-by-type failure ADR-0000 names). Eight agents are
about to write eight implementations in parallel against this one file; a loose
contract here is the foundation crack the whole portfolio inherits. So the contract
is an `ABC` whose ONE abstract method has EXACTLY the signature of
`jax_deberta.encode` — a non-conforming impl is unrepresentable (it cannot be
instantiated without that method), checkable by `mypy --strict`, and PROVEN by a
registered `exact_reference` that delegates straight to `jax_deberta.encode` and
round-trips to fidelity-vs-itself == 0.

THE IMPLEMENTATION UNIT — a whole-encode swappable variant, NOT "an attention op".
The portfolio's eight candidates hook FOUR orthogonal internal seams (attention /
linear-projection / FFN / position-cache). No narrower type is common to all eight:
a "single attention op" type cannot represent a weight-quantizer (it rewrites every
`_linear`) or an FFN-replacer — adopting it would force an interface change the
moment those land (the ADR-0013 "interface the real impls force-change" failure).
The whole-encode boundary `(params, input_ids, attention_mask, cfg) -> lhs` makes a
non-conforming impl unrepresentable WHATEVER a candidate rewrites internally: it
still IS a function of those four arguments to a `last_hidden_state`. Each variant
owns its own internal decomposition; this contract fixes only the outer boundary.

HOST-XOR-DEVICE (ADR-0012 P7 / test_import_xor.py). This file imports NEITHER numpy
NOR a device lib — only stdlib + the framework-free `shape_buckets` SSOT. Annotations
referencing `jax.Array` / `jax_deberta.DebertaCfg` are strings (`from __future__
import annotations`) resolved only under `TYPE_CHECKING`, so the contract is
host-XOR-device NEUTRAL and importable by BOTH the host registry/runner AND the
device-side variant math, exactly like `spans.py` and `shape_buckets.py`.

BUCKETING IS UPSTREAM (the placement decision). A variant receives ALREADY-bucketed,
already-padded `[B, s_bucket]` arrays from the host shell (`coref_host_shell.encode_lhs`
/ `iter_encode_lhs_batched`, which own `shape_buckets.bucket_len`/`pad_to`/the OOM
B-ladder). It MUST NOT re-pad or re-bucket; it MAY read `s_bucket =
input_ids.shape[1]` as a cache key (the position-cacher needs it) but it does not own
the ladder. `EncodeBucket` below is the realized `(B, s_bucket)` pair, VALIDATED
against the `shape_buckets` ladders — never a re-typed second ladder (ADR-0012 P1).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import shape_buckets

if TYPE_CHECKING:                       # type-only: keeps this file device-free
    import jax

    import jax_deberta


# ------------------------------------------------------------------ declared axes
class Regime(str, Enum):
    """The portfolio's operative axis (NLA-OPTIMIZATION-PORTFOLIO.md §1 regime
    axiom, §10 two-lane split). A closed vocabulary — an out-of-vocabulary regime is
    unrepresentable."""
    LATENCY = "latency"        # small-batch, bandwidth/launch-bound (the hook workload)
    THROUGHPUT = "throughput"  # large-batch, compute-bound
    BOTH = "both"


class FidelityTier(str, Enum):
    """The equivalence bar the variant CLAIMS, against ADR-0009's two-tier bar.
    Bit-exactness binds NOTHING here (P6); both tiers are MEASURED, never asserted."""
    EXACT = "exact"                            # ~1e-5 reduction-order vs the reference
    # P6: the harness MEASURES encoder-lhs aggregate distance (max|Δ|/mean|Δ| over real
    # tokens, lab_measure.fidelity_delta). Cluster-set agreement is the FULLER P6
    # comparable for the coref stack and is DEFERRED until a variant feeds the decode
    # tail (DESIGN §5) — a small lhs Δ can still flip a downstream cluster, so this lane
    # is one boundary upstream of the decision that ultimately matters.
    AGGREGATE_BEHAVIORAL = "aggregate_behavioral"


@dataclass(frozen=True)
class EncodeBucket:
    """The realized `(batch, seq_bucket)` geometry of one forward — the OUT-OF-BAND
    context a variant reads at fit-time (it carries what the per-call wire omits),
    sourced FROM the `shape_buckets` SSOT ladders and validated against them so an
    off-ladder shape is unconstructable (ADR-0000: illegal states unrepresentable;
    ADR-0012 P1: no second ladder)."""
    batch: int
    seq_bucket: int

    def __post_init__(self) -> None:
        if self.seq_bucket not in shape_buckets.ENCODE_LEN_BUCKETS:
            raise ValueError(
                f"seq_bucket={self.seq_bucket} is not a rung of "
                f"shape_buckets.ENCODE_LEN_BUCKETS={shape_buckets.ENCODE_LEN_BUCKETS}; "
                "the variant receives bucketed inputs and must not invent a ladder.")
        if self.batch not in shape_buckets.ENCODE_BATCH_BUCKETS:
            raise ValueError(
                f"batch={self.batch} is not a rung of "
                f"shape_buckets.ENCODE_BATCH_BUCKETS={shape_buckets.ENCODE_BATCH_BUCKETS}.")


@dataclass(frozen=True)
class FitVerdict:
    """A variant's a-priori applicability at a bucket — the retire-by-fit gate the
    portfolio synthesis names ("retire by measurement OR a-priori on fit"; a
    retirement reason IS data, per the frontier creed). `ok=False` is a RECORDED
    portfolio decision, not an error."""
    ok: bool
    reason: str


class EncodeVariant(ABC):
    """One swappable DeBERTa-encoder implementation. A registered variant is a
    zero-arg-constructible subclass declaring its `{regime, fidelity_tier}` as class
    metadata and implementing exactly `encode`.

    THE CALL BOUNDARY (identical to `jax_deberta.encode`, jax_deberta.py:352). This
    identity is deliberate: it makes the exact-reference variant a one-line
    delegation, proves the contract is satisfiable, and means a non-conforming impl
    cannot be written. `params` read-set == `jax_deberta.param_keys(cfg)`;
    `input_ids`/`attention_mask` are int `[B, s_bucket]` ALREADY bucketed+padded by
    the host shell (masked-inert padding, shape_buckets contract); the return is
    `last_hidden_state [B, s_bucket, H]`, H = cfg.num_heads*cfg.head_size. `rel_pos`
    stays an INTERNAL detail of each variant (computed via the un-forked
    `jax_deberta.build_relative_position`), exactly as `encode` does it — so the
    contract is the 4-arg form, never the 5-arg hoisted core."""

    #: opt-out marker for the by-TYPE metadata guard (R1-G / ADR-0000). FALSE here: a
    #: concrete variant declares {name, regime, fidelity_tier} as CLASS attributes and
    #: `__init_subclass__` enforces it AT CLASS-CREATION. `Decorated` (and its subclasses)
    #: flip this TRUE because they mirror the inner variant's metadata per-INSTANCE in
    #: `__init__`, not as class attributes — so the guard skips them.
    _metadata_is_dynamic: bool = False
    #: whether `encode` is FILLED with real math vs a `NotImplementedError` stub. Defaults
    #: to stub; a real implementation flips it TRUE *in its own variant file* (R3-F5). The
    #: harness self-proof derives the expected pre-implementation set from THIS per-variant
    #: flag — never from a global "all stubs unimplemented" assumption — so one agent
    #: shipping their math does not red the shared self-test for the other seven.
    IMPLEMENTED: bool = False

    #: whether INPUT PARTITIONING (the `--batch-size` request split + the device chunker that
    #: groups paragraphs into OOM-bounded forwards) is FIDELITY-INERT for this variant — i.e.
    #: splitting the input set into independently-encoded sub-batches yields per-paragraph
    #: outputs bit-identical to encoding them together. TRUE for this whole stack: coref is
    #: PER-PARAGRAPH independent (each paragraph's clusters are computed from its OWN encode;
    #: there is no cross-paragraph attention), and masked padding is inert (shape_buckets module
    #: docstring), so the partition the host chooses for memory/throughput reasons cannot move a
    #: real token's encoder output. That inertness is the BASIS for the client's `--batch-size`
    #: knob and `shape_buckets.chunk_by_vram`/`encode_batch_chunks` being safe to apply at all.
    #: The contract CARRIES the distinction so a future CROSS-CHUNK-DEPENDENT model (a sliding-
    #: window / cross-paragraph-attention encode, where a partition boundary WOULD change a
    #: token's context) declares FALSE and the host refuses to silently re-partition it.
    #: This is DECLARED metadata, but it has a SAFE DEFAULT (True) — so, unlike
    #: {name, regime, fidelity_tier}, it is deliberately NOT in the `__init_subclass__` by-TYPE
    #: required set: a defaulted flag must never make an existing variant unimportable.
    partition_is_fidelity_preserving: bool = True

    #: registry key (each concrete variant sets it as a class attribute; the meta-
    #: wrapper `Decorated` mirrors the inner variant's at instance level — so these are
    #: plain attributes, not ClassVar, to keep both forms type-legal under mypy --strict).
    name: str
    #: which lane this variant is built for (declared, recorded by the bench).
    regime: Regime
    #: the equivalence bar it claims vs the exact reference (declared, MEASURED).
    fidelity_tier: FidelityTier

    def __init_subclass__(cls, **kwargs: object) -> None:
        """By-TYPE metadata guard (R1-G / ADR-0000: illegal states unrepresentable). A
        CONCRETE subclass that omits `name`/`regime`/`fidelity_tier`, or sets one to the
        wrong type, is UNIMPORTABLE — this raises `TypeError` at class-creation (import),
        not silently at read time deep in the bench. Two exemptions, both deliberate:
          * a still-ABSTRACT intermediate base (non-empty `__abstractmethods__`) declares
            no metadata yet, so it is skipped;
          * `Decorated` & subclasses set the three per-INSTANCE in `__init__` from the
            wrapped variant (`_metadata_is_dynamic` truthy), so they are skipped — the
            guard must not break the meta-wrapper's composition."""
        super().__init_subclass__(**kwargs)
        # SKIP a still-abstract base. NB: ABCMeta computes `cls.__abstractmethods__` AFTER
        # `__init_subclass__` runs, so it is not yet reliable here — detect abstractness
        # directly, by asking whether any inherited abstract method is STILL abstract on cls.
        abstract_names: set[str] = set()
        for base in cls.__mro__:
            abstract_names |= getattr(base, "__abstractmethods__", frozenset())
        if any(getattr(getattr(cls, n, None), "__isabstractmethod__", False)
               for n in abstract_names):
            return                       # intermediate abstract base: nothing declared yet
        if getattr(cls, "_metadata_is_dynamic", False):
            return                       # Decorated & co.: metadata mirrored per-instance
        problems: list[str] = []
        name = getattr(cls, "name", None)
        if not isinstance(name, str) or isinstance(name, Enum):
            problems.append(f"`name` must be a str class attribute (got {name!r})")
        regime = getattr(cls, "regime", None)
        if not isinstance(regime, Regime):
            problems.append(f"`regime` must be a Regime class attribute (got {regime!r})")
        tier = getattr(cls, "fidelity_tier", None)
        if not isinstance(tier, FidelityTier):
            problems.append(f"`fidelity_tier` must be a FidelityTier class attribute (got {tier!r})")
        if problems:
            raise TypeError(
                f"{cls.__module__}.{cls.__qualname__}: concrete EncodeVariant whose metadata "
                f"is not declared BY TYPE (ADR-0000) — " + "; ".join(problems) + ". Set the "
                "three as class attributes (the registered variants do), or — if you wrap "
                "another variant — set `_metadata_is_dynamic = True` like `Decorated`.")

    @abstractmethod
    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        """`(params, [B,s_bucket] ids, [B,s_bucket] mask, cfg) -> [B,s_bucket,H] lhs`.
        The whole-encode boundary; the variant's internal seam (attention / linear /
        FFN / position-cache) is its own business.

        RETURN DTYPE (R3-F6 — pinned). `encode` MUST return the SAME dtype as
        `jax_deberta.encode` / `exact_reference` — the lhs dtype the decode tail consumes.
        A quant / mixed-precision variant that computes internally in int8 / bf16 / f16
        MUST cast the `last_hidden_state` back to that reference dtype before returning; a
        silently bf16/f16 return that the decode tail rejects is a CONTRACT VIOLATION, not
        an optimization (the bench's fidelity reads it as the reference's lhs).

        PREP MEMOIZATION (R1-C — amortize on `self`). Any ONE-TIME per-variant weight
        transform (the int8/int4 pack + per-channel scales, a Monarch / low-rank `UVᵀ`
        factorization, the per-`(cfg, s_bucket)` disentangled-position memo) MUST be
        computed ONCE and cached on `self` (e.g. `self._prepared`), NEVER recomputed every
        forward. The bench pays the FIRST forward as warmup — the fidelity forward and
        `lab_measure.warm_time_seconds`'s `warmup` passes both precede the timed `repeats`
        window — so a transform memoized on first `encode` is amortized OUT of the reported
        latency. A variant that re-transforms on every forward reports a corrupted
        (inflated) latency with NO signal that it did so: the measurement silently lies. No
        `prepare` hook is mandated — first-call memoization on `self` is sufficient and the
        warmup already amortizes it."""
        raise NotImplementedError

    def fit(self, bucket: EncodeBucket) -> FitVerdict:
        """A-priori applicability at `bucket`. Default: always fits. A variant whose
        structure only pays past a crossover (Nyström `S >= crossover`; randomized
        NLA "matrices large enough for concentration") OVERRIDES this to retire
        itself loudly-and-recorded below its crossover, rather than logging a bad
        number (portfolio: retire a technique only via a failed experiment OR a
        stated structural mismatch)."""
        return FitVerdict(ok=True, reason="no fit precondition declared")

    def est_peak_device_bytes(
        self, bucket: EncodeBucket, cfg: jax_deberta.DebertaCfg
    ) -> int:
        """A CONSERVATIVE UPPER BOUND, in bytes, on this forward's peak VARIABLE (non-weight)
        DEVICE memory at `bucket` — the FOURTH benchmark dimension (alongside latency /
        throughput / fidelity), DECLARED by the variant and recorded by the bench. The same
        over-estimation discipline as the OOM model: it must NEVER under-estimate (an
        under-estimate is the OOM-class failure `shape_buckets` exists to foreclose); a larger
        figure is merely a looser-but-safe bound.

        SCOPE — DEVICE bytes only, NOT host RSS (ratified). Host RSS (parse + Python + GC) is a
        REQUEST-level cost, not a per-variant property, and stays the client's `--batch-size`
        knob; this dimension is the per-variant DEVICE-activation cost the technique actually
        moves.

        THE DEFAULT IS THE DENSE-REFERENCE COST, and it REUSES THE ONE MEMORY MODEL (ADR-0012
        P1: there is exactly ONE memory model and it lives in `shape_buckets` — this does NOT
        re-derive a second). It builds the dense deberta MemModel from `cfg` via
        `shape_buckets.dense_deberta_mem_model` (the cfg-only twin of
        `coref_host_shell.mem_model_from`) and returns
        `shape_buckets.peak_variable_bytes(mm, bucket.batch, bucket.seq_bucket)` — the very
        quadratic-dominated `[B,H,S,S]` activation bound the OOM chunker uses.

        OVERRIDE MANDATE (R-MEM). A variant whose technique CHANGES the variable-memory profile
        MUST OVERRIDE this so the estimate is NOT silently the dense bound: FlashAttention (no
        `[B,H,S,S]` materialization -> drop the quadratic term), the linear-attention variants
        (Nyström / Performer -> drop the quadratic content scores), W8A8 / W4A16 (smaller
        bytes-per-element activations), a structured/low-rank FFN (smaller `[B,S,intermediate]`
        term). The override stays a CONSERVATIVE UPPER BOUND and stays a function of
        `shape_buckets.peak_variable_bytes` / `MemModel` (a re-parameterised MemModel — fewer
        co-resident `[B,H,S,S]` buffers, a smaller `bytes_per_elem`, a smaller `intermediate`),
        NEVER a hand-rolled second memory model.

        ADDITIVE: this does NOT touch the frozen `encode` call boundary — a follow-on fills its
        `encode` math and (if profile-changing) overrides THIS, with no interface change."""
        mm = shape_buckets.dense_deberta_mem_model(
            cfg.num_heads, cfg.head_size, cfg.pos_ebd_size)
        # shape_buckets is a declared mypy stub-gap (mypy.ini skip); its int result is returned
        # as the contract's int (named relaxation, ADR-0012 P8 — mirrors exact_reference.encode).
        return shape_buckets.peak_variable_bytes(  # type: ignore[no-any-return]
            mm, bucket.batch, bucket.seq_bucket)


class Decorated(EncodeVariant):
    """A composable meta-wrapper that wraps ANY `EncodeVariant` uniformly — same
    contract in, same contract out — without the inner variant knowing (the
    control_lab `Decimate` analog, A11). It is the COMPLETENESS LEVER: if a
    `Cached`/`Quantized`/`Guarded` decorator can compose over any variant with zero
    interface change, the interface is complete; if it cannot, the interface is
    incomplete (ADR-0013). The base delegates `encode`/`fit` to the inner variant;
    a real decorator overrides `encode` to add its behavior around `inner.encode`."""

    #: metadata is mirrored from the wrapped variant per-INSTANCE (below), NOT declared as
    #: class attributes — so the by-TYPE guard (`__init_subclass__`) exempts this and every
    #: decorator subclass. Without this opt-out the guard would (wrongly) reject `Decorated`.
    _metadata_is_dynamic: bool = True

    def __init__(self, inner: EncodeVariant) -> None:
        self.inner = inner
        self.name = inner.name
        self.regime = inner.regime
        self.fidelity_tier = inner.fidelity_tier
        self.IMPLEMENTED = inner.IMPLEMENTED   # mirror the wrapped variant's stub/real state
        # mirror the wrapped variant's declared memory profile (so a decorator over a
        # profile-changing variant reports the INNER's override, not the dense default).
        self.partition_is_fidelity_preserving = inner.partition_is_fidelity_preserving

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        return self.inner.encode(params, input_ids, attention_mask, cfg)

    def fit(self, bucket: EncodeBucket) -> FitVerdict:
        return self.inner.fit(bucket)

    def est_peak_device_bytes(
        self, bucket: EncodeBucket, cfg: jax_deberta.DebertaCfg
    ) -> int:
        return self.inner.est_peak_device_bytes(bucket, cfg)
