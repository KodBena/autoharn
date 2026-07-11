# 13 — Probabilistic Programming & Bayesian Inference (PyMC/Stan/NumPyro)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](../KEY.md)**; coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**; index → [README](../README.md).

**Key for this document.** Full reference → [KEY.md](../KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](../KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [PROG](../KEY.md#prog) | Liveness & Real-Time Progress — required events eventually occur within deadline; no deadlock or correct-but-late action |
| [AUTH](../KEY.md#auth) | Action Authorization & Norm Precedence — every effect is gated by an explicit permission; closure + norm priority resolve deterministically |
| [ATTR](../KEY.md#attr) | Agency Attribution — every change bound to an identified agent who saw-to-it and could-have-done-otherwise |
| [COMMIT](../KEY.md#commit) | Directed Commitment & Handoff — an owed obligation has a tracked lifecycle; completes atomically or is unwound; no orphan/double handoff |
| [REVISE](../KEY.md#revise) | Belief Revision & Retraction — retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational |
| [CONSIST](../KEY.md#consist) | Consistency & Contradiction Containment — contradictions are quarantined; no ex-falso, no silent side-picking |
| [CALIB](../KEY.md#calib) | Substantiated & Calibrated Claims — each claim backed by a reproducible artifact at strength matched to its kind; honest confidence |
| [CLASS](../KEY.md#class) | Honest Sharp Classification — a value lands in exactly one cell of a MECE partition (or explicit "unknown"); misfit surfaced |
| [COHERE](../KEY.md#cohere) | Single-Authority / Single-Writer Coherence — one authoritative definition per fact; one owner per mutable state; references resolve to one correct target |
| [TRACE](../KEY.md#trace) | Traceability, Coverage & Change-Impact — hazard→req→design→code→test links total & navigable; coverage measured; change-impact closed on the artifact |
| [INDEP](../KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |
| [RECORD](../KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

A probabilistic program declares a generative model and a "condition on observed data" operation; an inference engine returns the *posterior* — a full distribution over unknowns, not a point estimate. Its job in autoharn is to make the empirical, float-valued, irreducibly-uncertain claims carry a **calibrated** guarantee instead of a fabricated one.

## Primer (becoming broadly expert)

The core idea is Bayes' rule run as a compiler target: you write `p(data | θ)` (a likelihood) and `p(θ)` (a prior), and the engine computes `p(θ | data)` by Markov-chain Monte Carlo — almost always Hamiltonian Monte Carlo / NUTS (Neal; Hoffman & Gelman 2014), which uses gradients to explore high-dimensional posteriors efficiently. The two concepts that matter most are: (1) **the posterior is the deliverable** — every downstream claim ("the margin is safe," "P(exceedance) < ε") is a *functional of a distribution* with a credible interval, so over/under-confidence is representable and inspectable rather than hidden in a scalar; and (2) **convergence is not assumed, it is diagnosed** — R̂ (Gelman–Rubin), effective sample size, and divergent-transition counts are *mechanical* pass/fail gates that tell you whether the number you printed is the number the model implies. Canonical authors: Gelman et al. (*Bayesian Data Analysis*), Betancourt (HMC geometry), Talts et al. (simulation-based calibration). The intuition: this machinery exists to discharge the obligation "a quantity that is genuinely uncertain must be reported with a confidence that is *correct* — neither a bit-pinned float nor a vibe."

## Obligations it discharges

**[CALIB](../KEY.md#calib) — Substantiated & Calibrated Claims (primary assignment).** [CALIB](../KEY.md#calib)'s failure mode is "false authority": a claim wearing a proof's costume, or confidence uncorrelated with evidence, or the *wrong bar* (bit-pinning a float-sensitive numeric). A Bayesian posterior matches this exactly because its native output *is* a calibrated probabilistic statement with a stated interval — the guarantee strength is "credible interval at level α, with calibration testable by construction." For any load-bearing quantity that is a measurement, a risk, a sensor-fusion estimate, or a tail probability, this is the guarantee whose *kind* matches the quantity's kind. Where a logic invariant must be asserted exactly, you do not use this; where a float-sensitive numeric must meet a tolerance/CI, this is the discharge.

**[CLASS](../KEY.md#class) — Honest Sharp Classification (secondary).** A Bayesian classifier returns a posterior over the closed vocabulary plus mass on "none of these," giving a principled **reject-to-unknown** rule (route to `unknown` when no class clears a posterior-probability threshold) and a loud misfit signal (low max-posterior, high entropy) — directly countering "silent mis-sortation into the closest-but-wrong bucket." Guarantee strength: probabilistic, decision-theoretic.

**[INDEP](../KEY.md#indep) (supporting role only).** A posterior can serve as an *independent numeric oracle* against a producer's point estimate — the diversity is real because the inference path shares no code with the producer. But it qualifies only if its own diagnostics pass.

**Obligations it does NOT serve.** [INV](../KEY.md#inv) ("always," every reachable state) and [PROG](../KEY.md#prog) (deadline, WCET) demand exact/temporal guarantees; a posterior gives "P(violation) is small," never "violation is impossible," and must not masquerade as a barrier certificate. [AUTH](../KEY.md#auth), [ATTR](../KEY.md#attr), [COMMIT](../KEY.md#commit), [REVISE](../KEY.md#revise), [CONSIST](../KEY.md#consist), [COHERE](../KEY.md#cohere), [TRACE](../KEY.md#trace), [RECORD](../KEY.md#record) are logical/structural and outside its remit. Assign it to the *empirical* layer; never let it pretend to be the invariant layer.

## A worked encoding

Obligation: **[CALIB](../KEY.md#calib)** on a dam safety margin. Requirement: from noisy redundant piezometer readings, the probability that true pore pressure exceeds the design limit must be provably small *and* the claim must carry a calibrated interval — not a single coerced reading.

```python
import jax.numpy as jnp, numpyro, numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS

readings = jnp.array([41.2, 43.8, 42.5, 55.9])  # kPa; last sensor drifting
DESIGN_LIMIT = 50.0

def model(y):
    true_p = numpyro.sample("true_p", dist.Normal(40.0, 15.0))   # prior
    sigma  = numpyro.sample("sigma",  dist.HalfNormal(5.0))
    # Student-t likelihood: heavy tails quarantine the outlier sensor
    numpyro.sample("obs", dist.StudentT(3.0, true_p, sigma), obs=y)

mcmc = MCMC(NUTS(model), num_warmup=1000, num_samples=4000, num_chains=4)
mcmc.run(jax.random.PRNGKey(0), y=readings)
post = mcmc.get_samples()["true_p"]

p_exceed = float((post > DESIGN_LIMIT).mean())
lo, hi   = jnp.percentile(post, jnp.array([2.5, 97.5]))
# MECHANICAL gate, not an LLM judgment:
import arviz as az
rhat = float(az.rhat(az.from_numpyro(mcmc)).true_p)
assert rhat < 1.01, "non-convergence: claim VOID"
# CALIB verdict: pass iff calibrated tail prob under bound AND interval below limit
verdict = (p_exceed < 1e-3) and (hi < DESIGN_LIMIT)
```

The heavy-tailed likelihood prevents the drifting fourth sensor from dragging the estimate (a built-in CONSIST-adjacent robustness), and the `assert rhat < 1.01` is the qualification gate: a number that printed without convergence is disqualified, mirroring [CALIB](../KEY.md#calib)'s "proof costume" failure.

## Automation & tooling (the git-clone-runnable question)

Three production-grade, permissively-licensed engines, all git-clone-runnable:

- **NumPyro 0.21.0** (Apache-2.0, released May 2026) — JAX-backed, the *local* host here (JAX is in the installed stack); JIT-compiled NUTS, fastest for differentiable models.
- **PyMC 6.0.1** (Apache-2.0, May 2026) — PyTensor 3.0 backend; most ergonomic Python modeling API.
- **Stan / CmdStan 2.39.0** (BSD-3-Clause, May 2026) — the reference HMC implementation; embedded Laplace approximation new in this release.
- **ArviZ** (Apache-2.0) — the qualification layer: R̂, ESS, divergences, posterior-predictive checks, simulation-based calibration utilities, all mechanical.

No encoding-into-a-host is required — these *are* the dedicated tools. The autoharn integration is: model + data + `MCMC.run` + an ArviZ diagnostic gate that hard-fails the build on R̂ ≥ 1.01, ESS below threshold, or any divergence. The diagnostics are the DO-178C-style tool-qualification evidence for the inference itself.

## Honest leverage & kill-condition

**Load-bearing where:** every empirical/float-sensitive claim that today ships as a bare scalar with implied certainty — risk limits, sensor fusion, exceedance probabilities, dose-adjustment factors, WCET *distributions*. Here the leverage is real: the tool converts "confident wrong number" into "interval with a calibration you can test."

**Ash where:** the model is misspecified. A posterior is only as honest as its likelihood; a confidently wrong model yields confidently wrong *but calibrated-looking* intervals — [CALIB](../KEY.md#calib)'s failure mode reborn one level up. And it never delivers [INV](../KEY.md#inv)/PROG hard guarantees.

**Falsifiable experiment + KILL CONDITION.** Run **Simulation-Based Calibration** (Talts et al.): draw θ* from the prior, simulate data, re-infer, compute the rank of θ* in its posterior; over many replicates the ranks must be uniform. **Kill condition:** if SBC rank histograms deviate from uniform beyond the χ² band, *or* if the same model passes its own gate while R̂ < 1.01 yet SBC fails, the encoding is disqualified for [CALIB](../KEY.md#calib) and must not gate a safety claim — the "calibrated" label is then false advertising, exactly the thing it was assigned to prevent.

## References (edification)

- **Gelman et al., *Bayesian Data Analysis* (3rd ed.)** — the canonical text; teaches model-building, priors, and posterior-predictive checking end-to-end.
- **Talts, Betancourt, et al., "Validating Bayesian Inference Algorithms with Simulation-Based Calibration" (2018)** — teaches the *kill condition*: how to mechanically prove your inference is calibrated.
- **Betancourt, "A Conceptual Introduction to Hamiltonian Monte Carlo" (2017)** — teaches why NUTS works and how divergences diagnose untrustworthy posteriors.
- **NumPyro docs (num.pyro.ai)** — teaches the runnable API and ArviZ diagnostic gating used above.

Sources: [PyMC releases](https://github.com/pymc-devs/pymc/releases), [NumPyro PyPI](https://pypi.org/project/numpyro/), [CmdStan 2.39 release](https://blog.mc-stan.org/2026/05/19/release-of-cmdstan-2-39/).


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
