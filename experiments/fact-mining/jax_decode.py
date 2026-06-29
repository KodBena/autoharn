#!/usr/bin/env python
"""maverick-coref DECODE TAIL as a pure JAX functional core (ADR-0012 P9).

HONEST FILENAME (test_import_xor.py contract): this file's name advertises the
`jax` device framework, so it promises to be DEVICE-ONLY. It imports `jax` +
stdlib and NEVER `numpy`. The XOR-gate rejects a `jax_*`-named file that imports
numpy *regardless* of BOUNDARY_FILES — so the promise is mechanically enforced,
not merely asserted. Everything here is total over `jax.Array`.

SCOPE — Stage 1a, the post-encoder decode math only. We do NOT touch the torch
encoder. Inputs are the encoder's `last_hidden_state` (already a device array),
the model's learned decode-tail weights (a pytree of jax arrays), plus the
candidate-span / category machinery prepared by the imperative shell
(`coref_host_shell.py`). We mirror, line-for-line, maverick 1.0.7:

  maverick/models/model_mes.py
    - eos_mention_extraction        (~129): start classifier, the s2e SWAP, the
                                            sigmoid(x)>0.5 == x>0 keep decisions
    - _calc_coref_logits            (~257): the 4-term bilinear antecedent score
    - transpose_for_scores          (~252)
    - mes_span_clustering           (~230): per-category mask * tril * diag-zero,
                                            sum over categories
    - create_mention_to_antecedent_singletons (~297): no_ant column + argmax

WHY THREE jit-functions AND NOT ONE MONOLITH. maverick's tail interleaves
`torch.nonzero` (start selection, span selection, antecedent gather) between the
dense steps. `nonzero` has a DATA-DEPENDENT output shape, which jax cannot trace
inside a single `jit`. So the irreducibly dynamic / sequential glue (the
`nonzero`s, the union-find) lives in the host shell, and the dense math is
exposed here as three jit-able stages over fixed-shape arrays (recompiled per
document shape — that is the per-document MEMORY BUDGET; we never build one
unbounded B*S batch). Each stage is pure and side-effect free.

THE sigmoid>0.5 IDENTITY. maverick thresholds with `torch.sigmoid(x) > 0.5`.
sigmoid is strictly monotone with sigmoid(0)=0.5, so `sigmoid(x) > 0.5 <=> x > 0`
*exactly* (no float reconstruction of sigmoid, no 0.5 round-trip). We use `x > 0`
everywhere a maverick line says `sigmoid(...) > 0.5`. This is the load-bearing
discrete decision and it is kept on-device here.

TWO-TIER EQUIVALENCE (ADR-0009). The float logits are NOT required to match
torch bit-for-bit (different matmul / GELU / LayerNorm kernels). The DISCRETE
cluster SETS are the logic invariant and MUST match. The residual risk is a
logit sitting within float-reconstruction epsilon of a decision boundary (the
`> 0` threshold, or an argmax near-tie); test_jax_decode_fidelity.py is the
falsifier the human runs.

NOTE on the no_ant trick & argmax safety (mirrors maverick exactly): after
`tril().fill_diagonal_(0)` the summed matrix has the real antecedent logits at
columns j<i and structural ZEROS at columns j>=i. `no_ant in {0,1}` is appended
as the last (K-th) column. Argmax over the K+1 columns:
  * if some antecedent logit > 0  -> no_ant==0 and that positive logit (>0) wins
  * if all antecedent logits <= 0 -> no_ant==1 wins over every 0 / negative
so the argmax is always either a valid antecedent column j<i with a strictly
positive logit, or the no_ant column (index K) meaning "no antecedent". A
structural-zero column can never be the strict argmax. Ties between equal logits
resolve to the FIRST index in both `jnp.argmax` and `torch.argmax` in practice
(torch's tie rule is technically unspecified — see the fidelity report).
"""

from __future__ import annotations

import jax
import jax.numpy as jnp

# ---------------------------------------------------------------- constants
# len(CATEGORIES)+1 in maverick/common/constants.py (6 categories + 1 "ALL").
NUM_CATS: int = 7
LAYER_NORM_EPS: float = 1e-5  # torch.nn.LayerNorm default eps


# ----------------------------------------------------- elementwise sub-layers
def _layer_norm(x: jax.Array, weight: jax.Array, bias: jax.Array) -> jax.Array:
    """torch.nn.LayerNorm over the last axis (population/biased variance)."""
    mu = jnp.mean(x, axis=-1, keepdims=True)
    var = jnp.mean(jnp.square(x - mu), axis=-1, keepdims=True)  # unbiased=False
    xhat = (x - mu) * jax.lax.rsqrt(var + LAYER_NORM_EPS)
    return xhat * weight + bias


def _fc(params: dict, prefix: str, x: jax.Array) -> jax.Array:
    """maverick.common.util.FullyConnectedLayer in EVAL mode (dropout == identity):

        dense1 -> (dropout=id) -> GELU(exact erf) -> LayerNorm -> dense

    torch.nn.GELU() defaults to the exact (erf) form, so we pass
    approximate=False; the jax default (tanh approx) would NOT match torch.
    torch.nn.Linear stores weight as [out, in] and computes x @ W.T + b.
    """
    w1 = params[prefix + ".dense1.weight"]
    b1 = params[prefix + ".dense1.bias"]
    lnw = params[prefix + ".layer_norm.weight"]
    lnb = params[prefix + ".layer_norm.bias"]
    w2 = params[prefix + ".dense.weight"]
    b2 = params[prefix + ".dense.bias"]

    h = x @ w1.T + b1
    h = jax.nn.gelu(h, approximate=False)  # exact erf GELU == torch.nn.GELU()
    h = _layer_norm(h, lnw, lnb)
    return h @ w2.T + b2


def _transpose_for_scores(x: jax.Array) -> jax.Array:
    """maverick.transpose_for_scores, batch dim dropped.

    [K, NUM_CATS*TH] -> [K, NUM_CATS, TH] -> [NUM_CATS, K, TH]  (the 'nkf' layout).
    """
    k = x.shape[0]
    th = x.shape[-1] // NUM_CATS
    x = x.reshape(k, NUM_CATS, th)
    return jnp.transpose(x, (1, 0, 2))


# ------------------------------------------------------------- jit STAGE 1
@jax.jit
def mention_start_keep(params: dict, lhs: jax.Array) -> jax.Array:
    """STAGE 1 — mirrors eos_mention_extraction start logits + keep decision.

    `start_logits = start_token_classifier(lhs).squeeze(-1)`  then
    `(sigmoid(start_logits) > 0.5)` == `start_logits > 0`.

    Returns a boolean keep-mask over the S sequence positions. The shell does the
    `nonzero` (data-dependent shape) to turn this into candidate start indices.
    """
    start_logits = _fc(params, "start_token_classifier", lhs)[..., 0]  # [S]
    return start_logits > 0.0


# ------------------------------------------------------------- jit STAGE 2
@jax.jit
def span_mention_keep(
    params: dict,
    lhs: jax.Array,
    possible_start_idxs: jax.Array,
    possible_end_idxs: jax.Array,
) -> jax.Array:
    """STAGE 2 — mirrors eos_mention_extraction span (start,end) classifier.

    CRITICAL — reproduce maverick's SWAP exactly (model_mes.py:168-169):
        starts_hidden_states = lhs[possible_end_idxs]    # fed to START repr layer
        ends_hidden_states   = lhs[possible_start_idxs]  # fed to END   repr layer
    This swap is load-bearing learned behaviour (the model was trained with it),
    NOT a bug to fix. Then:
        s2e = cat(start_token_representation(starts_hidden),
                  end_token_representation(ends_hidden), dim=-1)
        s2e_logits = start_end_classifier(s2e).squeeze(-1)
        keep = sigmoid(s2e_logits) > 0.5  == s2e_logits > 0

    Returns a boolean keep-mask over the P candidate (start,end) pairs.
    """
    starts_hidden = lhs[possible_end_idxs]    # SWAP (maverick:168)
    ends_hidden = lhs[possible_start_idxs]     # SWAP (maverick:169)
    s2e = jnp.concatenate(
        (
            _fc(params, "start_token_representation", starts_hidden),
            _fc(params, "end_token_representation", ends_hidden),
        ),
        axis=-1,
    )
    s2e_logits = _fc(params, "start_end_classifier", s2e)[..., 0]  # [P]
    return s2e_logits > 0.0


# --------------------------------------------------- bilinear antecedent score
def _bilinear_coref(
    S: jax.Array, E: jax.Array,
    Wss: jax.Array, Wse: jax.Array, Wes: jax.Array, Wee: jax.Array,
    Bss: jax.Array, Bse: jax.Array, Bes: jax.Array, Bee: jax.Array,
) -> jax.Array:
    """The 4-term biaffine antecedent score, CONSOLIDATED to one einsum (+ one bias).

    The literal maverick form is four bilinear einsums and four bias einsums:
        S·Wss·S + E·Wee·E + S·Wse·E + E·Wes·S
        (+ S·Bss + E·Bee + E·Bse + S·Bes,  each broadcast over the antecedent column)
    Stack X = [S ; E] on the feature axis and the 2x2 weight block
        Wblock = [[Wss, Wse], [Wes, Wee]]
    and X·Wblock·X expands to EXACTLY those four terms, so the four matmul-einsums become
    ONE over [n, K, 2f]; likewise the four biases become X·[Bss+Bes ; Bee+Bse]. Fewer GPU
    kernels -> less XLA dispatch (the decode is dispatch-bound at these sizes). This is a
    MATHEMATICAL IDENTITY — test_bilinear_consolidation.py is its guest falsifier; the float
    reduction order differs from the literal-4 form by ~1e-6, within the cluster-decision-
    robust tier (ADR-0009 two-tier), and the host --coref-verify confirms the discrete
    cluster SETS are unchanged end to end.
    """
    X = jnp.concatenate((S, E), axis=-1)                          # [n, K, 2f]
    Wblock = jnp.concatenate(
        (jnp.concatenate((Wss, Wse), axis=-1),                   # [n, f, 2f]  (the S row of the block)
         jnp.concatenate((Wes, Wee), axis=-1)),                  # [n, f, 2f]  (the E row of the block)
        axis=-2,
    )                                                            # [n, 2f, 2f]
    logits = jnp.einsum("nkf, nfg, nlg -> nkl", X, Wblock, X)    # the 4 bilinear terms, one einsum
    Bstack = jnp.concatenate((Bss + Bes, Bee + Bse), axis=-1)    # [n, 2f]
    biases = jnp.einsum("nkf, nf -> nk", X, Bstack)[:, None, :]  # the 4 bias terms, one einsum
    return logits + biases                                       # [n, K, K]


def _calc_coref_logits(
    params: dict, start_reps: jax.Array, end_reps: jax.Array
) -> jax.Array:
    """maverick._calc_coref_logits (4-term biaffine), batch dim dropped, consolidated via
    `_bilinear_coref`. The bias tensor pairing is maverick's, reproduced as-is
    (s2s-bias <- starts, e2e-bias <- ends, s2e-bias <- ends, e2s-bias <- starts)."""
    S = _transpose_for_scores(_fc(params, "coref_start_all_mlps", start_reps))  # [n,K,f]
    E = _transpose_for_scores(_fc(params, "coref_end_all_mlps", end_reps))      # [n,K,f]
    return _bilinear_coref(
        S, E,
        params["antecedent_s2s_all_weights"], params["antecedent_s2e_all_weights"],
        params["antecedent_e2s_all_weights"], params["antecedent_e2e_all_weights"],
        params["antecedent_s2s_all_biases"], params["antecedent_s2e_all_biases"],
        params["antecedent_e2s_all_biases"], params["antecedent_e2e_all_biases"],
    )


# ------------------------------------------------------------- jit STAGE 3
@jax.jit
def coref_decode(
    params: dict,
    start_reps: jax.Array,
    end_reps: jax.Array,
    categories_masks: jax.Array,
) -> jax.Array:
    """STAGE 3 — mirrors mes_span_clustering + create_mention_to_antecedent_singletons
    up to and INCLUDING the argmax antecedent decode.

    start_reps/end_reps : [K, TH]  (the gathered per-mention start/end hidden states)
    categories_masks    : [NUM_CATS, K, K] int  (prepared host-side; see shell)

    Returns max_antecedents : int32[K].  Value in [0, K-1] = chosen antecedent
    column (always j<i); value == K = the no_ant column = "no antecedent".

    Steps (maverick line refs):
      coref = _calc_coref_logits(...) * categories_masks           (mes:235-236)
      per category: tril().fill_diagonal_(0)  == keep strict lower  (mes:239)
      coref = coref.sum(over categories)                            (mes:245)
      no_ant = 1 - (sum_j[coref>0] > 0)         (sigmoid>0.5 == >0)  (mes:308)
      coref_aug = concat([coref, no_ant[:,None]], -1)               (mes:310)
      max_antecedents = argmax(coref_aug, -1)                       (mes:314)
    """
    coref = _calc_coref_logits(params, start_reps, end_reps)  # [n, K, K]
    coref = coref * categories_masks                          # per-category gate

    k = coref.shape[-1]
    strict_lower = jnp.tril(jnp.ones((k, k), dtype=coref.dtype), k=-1)  # i>j
    coref = coref * strict_lower[None, :, :]                  # tril + diag-zero

    coref = jnp.sum(coref, axis=0)                            # [K, K] sum over cats

    # no_ant: 1 if row i has NO antecedent column with logit > 0, else 0.
    has_ant = jnp.any(coref > 0.0, axis=-1)                   # sigmoid>0.5 == >0
    no_ant = (1.0 - has_ant.astype(coref.dtype))[:, None]     # [K, 1]

    coref_aug = jnp.concatenate((coref, no_ant), axis=-1)     # [K, K+1]
    return jnp.argmax(coref_aug, axis=-1).astype(jnp.int32)   # [K]
