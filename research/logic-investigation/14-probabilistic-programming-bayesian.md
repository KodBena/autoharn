# 14 — Probabilistic Programming & Formal Bayesian Frameworks

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../../GLOSSARY.md)**.

Probabilistic programming languages (PPLs) let you write a generative model as code and hand it to an inference engine that returns a full *posterior distribution* over the unknowns — the machinery autoharn needs to turn "12x" into a defensible, uncertainty-quantified claim rather than a point estimate masquerading as fact.

## Primer

A PPL is two halves. You write a *generative model* — "this is how the noisy readings were produced from latent parameters" — and an *inference engine* (MCMC like NUTS, or variational inference) runs it backwards to give you `p(parameters | data)`, the **posterior**. You never get a single number; you get a distribution you can summarize with a **credible interval** ("95% probability the true speedup is in [9.1, 13.4]").

The conceptual jump from Z3: Z3 answers *deduction* — "is this provably true given the axioms?" — and returns SAT/UNSAT. Bayesian inference answers *induction under noise* — "how credible is this, given finite, jittery measurements?" — and returns a probability mass. Z3 cannot tell you a benchmark regressed because regression is not a logical entailment of two noisy timings; it is a statistical inference. Reach for a PPL exactly when your evidence is noisy measurements and you must attach honest uncertainty to a verdict — which is most of P2's perf-claim surface.

## Applicability to autoharn

**Posterior over a perf-claim — fit: HIGH.** Every perf-token ("matches baseline", "regression") must reference a stored reading. A bare ratio of two means hides the variance. Model it:

```python
import numpyro, numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS
import jax.numpy as jnp

def speedup_model(base, new):
    mu_b = numpyro.sample("mu_b", dist.LogNormal(0., 2.))
    mu_n = numpyro.sample("mu_n", dist.LogNormal(0., 2.))
    s    = numpyro.sample("s", dist.HalfNormal(1.))
    numpyro.sample("ob", dist.LogNormal(jnp.log(mu_b), s), obs=base)
    numpyro.sample("on", dist.LogNormal(jnp.log(mu_n), s), obs=new)
    numpyro.deterministic("speedup", mu_b / mu_n)   # posterior over the claim
```

The posterior `speedup` gives a credible interval, not "12x". P2 then stores: "speedup 11.8x, 94% CI [9.4, 14.1]". If that CI straddles 1.0, "regression" is *unsubstantiated by construction*. This beats a t-test because the t-test gives a p-value on a null you don't care about; the posterior gives the quantity in the ledger (the speedup itself) with direct probability statements an auditor can read.

**Bayesian change-point detection — fit: HIGH.** P2 wants *attribution*: which commit regressed. Put a prior over the change index and let the data locate it.

```python
def changepoint(y, n):
    tau = numpyro.sample("tau", dist.DiscreteUniform(0, n-1))   # WHERE
    m1  = numpyro.sample("m1", dist.Normal(y.mean(), 5.))
    m2  = numpyro.sample("m2", dist.Normal(y.mean(), 5.))
    s   = numpyro.sample("s", dist.HalfNormal(2.))
    mu  = jnp.where(jnp.arange(n) < tau, m1, m2)
    numpyro.sample("obs", dist.Normal(mu, s), obs=y)
```

The posterior over `tau` *is* the statistical attribution — "87% mass on commit 142–144" — far stronger than eyeballing a graph, and honest when the regression is gradual (the posterior spreads, refusing false precision).

**Bayesian model comparison (WAIC/LOO) — fit: MED-HIGH.** When the ledger holds competing explanations of a regression (GC pause vs. cache miss vs. real algorithmic cost), encode each as a model and let `arviz.compare({...}, ic="loo")` rank them by out-of-sample predictive fit. This is "deductive maintenance" of hypotheses done statistically: the data, not the loudest commit message, selects the supersedes-chain winner. Bayes factors are sharper but prior-sensitive; LOO is the safer default.

**Calibration / posterior predictive checks — fit: HIGH.** The audit that an interpretation isn't overconfident: simulate replicated data from the posterior and check the real readings fall inside their predictive band (`az.plot_ppc`, or a coverage statistic). A model whose 90% intervals contain the truth only 60% of the time is *not allowed* to promote its claim to "confirmed". This is P3's spirit applied to inference itself.

**Honest overkill flag:** a clean 100x with tight, non-overlapping variance needs no posterior — report the point estimate and the raw readings. Bayesian machinery earns its cost only when the signal is comparable to the noise, i.e. exactly when humans (and LLMs) are tempted to over-claim.

## Software to leverage

None are installed in `generic` (only `jax 0.10.1`, which NumPyro rides on — so NumPyro is the cheapest add). All versions/licenses web-verified June 2026.

| tool | role | license | language / bindings | install cost | maturity | LLM-friendliness |
|---|---|---|---|---|---|---|
| PyMC 6.0.1 | full Bayesian modeling, NUTS+VI | Apache-2.0 | Python (PyTensor) | `pip`, heavy deps | very high | high — huge corpus |
| NumPyro 0.21.0 | fast NUTS on JAX | Apache-2.0 | Python (JAX) | `pip`, **JAX already present** | high | high |
| Pyro ~1.9 | deep/structured VI | Apache-2.0 | Python (PyTorch) | `pip` + torch (large) | high | med-high |
| Stan / CmdStanPy ~1.2 | gold-standard HMC | BSD-3 / BSD-3 | Stan DSL via Python | **C++ toolchain compile** | very high | med (separate DSL) |
| ArviZ 0.23.x | diagnostics, LOO/WAIC, PPC | Apache-2.0 | Python | `pip`, light | high | high |
| pgmpy 1.1.0 | discrete Bayesian networks, exact inference | MIT | Python | `pip` | high | high |
| pomegranate 1.1.x | fast BNs/HMMs/mixtures | MIT | Python (PyTorch) | `pip` + torch | med | med |

Recommendation for autoharn: **NumPyro + ArviZ** (lightest given JAX is installed; ArviZ is the cross-engine diagnostics layer regardless of which sampler you pick). Reach for **pgmpy** only if you model *discrete* causal structure (exact, queryable inference fits the auditability ethos). Avoid Stan unless you accept a C++ build step in CI.

## Limits & honest take

Bayesian inference does **not** help where autoharn needs *deduction*: an invariant either holds or it doesn't — that's Z3/P3 territory, not a posterior. It adds nothing to clean, high-SNR benchmarks. The substance-over-hype failure modes are sharp:

- **A posterior is only as honest as the model + priors.** An LLM can quietly choose a convenient prior — a tight `Normal(0, 0.1)` — and manufacture a narrow credible interval that *looks* rigorous. This is the false-authority risk wearing a credible interval: it is more dangerous than a bare "12x" because the interval signals false diligence. Mitigation: priors must be pre-registered in P2 *before* seeing the data, exactly like the criterion-before-result rule, and a prior-sensitivity check (re-run with a wider prior) should be a stored reading.
- **Convergence must be gated.** An un-converged MCMC run returns garbage that *looks* like a posterior. R-hat > 1.01, low effective sample size, or divergences mean the "posterior" is noise. This belongs in a `*_violations` gate: no inference reading is admissible to the ledger unless `r_hat ≤ 1.01 and ess > 400 and divergences == 0`. A DIRTY (non-converged) run must never be promoted to "confirmed".
- **LOO/Bayes factors can be gamed** by model-space choice; report the full comparison set, not just the winner.

The intellectually honest stance: Bayesian machinery converts overconfidence from *invisible* to *auditable*, but only if the priors and convergence diagnostics are themselves first-class, pre-registered ledger entries. Used loosely, it launders hunches into credible-looking intervals — the opposite of what autoharn wants.

## References & learning

- **McElreath, *Statistical Rethinking* (2nd ed.)** — teaches the generative-model-first mindset and prior reasoning from scratch; the best on-ramp for a Z3-literate engineer.
- **Gelman et al., *Bayesian Data Analysis* 3** — the rigorous reference for posterior predictive checks and model comparison (the P2 audit primitives).
- **PyMC docs / example gallery (pymc.io)** — copy-paste change-point and A/B-speedup notebooks mapping directly onto the worked examples above.
- **Vehtari, Gelman & Gabry, "Practical Bayesian model evaluation using LOO" (and the ArviZ diagnostics guide)** — the canonical treatment of LOO/WAIC and the R-hat/ESS gates you must enforce.

Sources: [PyMC PyPI](https://pypi.org/project/pymc/), [NumPyro releases](https://github.com/pyro-ppl/numpyro/releases), [ArviZ docs](https://python.arviz.org/en/stable/), [pgmpy](https://github.com/pgmpy/pgmpy), [pomegranate PyPI](https://pypi.org/project/pomegranate/)


---
*Hand-commissioned complement to report 13 (statistical-relational), authored by a separate single-agent run (`wf_6e4d1fb1-3ae`), model claude-opus-4-8[1m], 2026-06-27 — scoped to probabilistic programming / Bayesian inference so it complements rather than duplicates report 13.*
