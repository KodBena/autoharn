# 14 — Probabilistic Programming & Formal Bayesian Frameworks — Fair Trial (first pass)

> Part of the autoharn **logic fair-trials** (the corrected, frontier-creed pass). Coined terms → root **[GLOSSARY.md](../../GLOSSARY.md)**. The honest status of every verdict here is **undecided-until-the-experiment-runs** — see [README](README.md) and [AUDIT.md](AUDIT.md).

> **Audit verdict:** `deflated = False` · 2 defect(s) noted · **not rewritten** (the hardening pass was a no-op).

## Probabilistic Programming & Formal Bayesian Frameworks — Fair Trial

The bet on trial: that a PPL lets autoharn's P2 ledger store perf-claims as *honest posteriors with auditable uncertainty* — "regression" as a probability statement an auditor can challenge — rather than point estimates masquerading as deductions, and that LLM authorship makes per-claim generative models cheap enough to be the default, not the exception.

## Maximal ambition

The frontier claim: **autoharn never again promotes a perf-token to "confirmed" without a stored posterior over the *quantity in the ledger itself***, plus a machine-checkable attribution of *which* commit moved it and *why*. Three things become possible that SQL/Z3-as-usual cannot do:

1. **Uncertainty-quantified verdicts.** Instead of `speedup = 12x`, the ledger holds `speedup posterior, 94% CI [9.4, 14.1]`. The gate logic becomes: a "regression" token whose CI straddles 1.0 is *unsubstantiated by construction* — the substantiation rule (P2) is enforced by the geometry of the posterior, not by a human eyeballing a graph.

2. **Statistical attribution as a first-class ledger artifact.** A Bayesian change-point posterior over commit index *is* the answer to "which commit regressed," and it degrades honestly: when the regression is gradual the posterior spreads and *refuses* false precision. SQL can compute a delta; it cannot say "87% mass on commits 142–144, and here is the residual mass elsewhere."

3. **Model comparison as deductive maintenance of hypotheses.** When the supersedes-chain holds competing explanations (GC pause vs. cache-miss vs. real algorithmic cost), each is a generative model; LOO/WAIC ranks them by out-of-sample predictive fit. The *data* selects the chain winner, not the loudest commit message — auditable, reproducible hypothesis maintenance.

## The expressiveness gap (precise, not hand-wavy)

A SQL view over the readings table computes summary statistics: means, variances, a Welch t-test if you hand-code it, a ratio of means. What it *provably cannot* produce is a **posterior distribution over a derived quantity** — `p(speedup | data)` where `speedup = μ_base/μ_new` — because that requires marginalizing latent parameters under a likelihood, an integral with no closed form for the lognormal-ratio case. SQL has no MCMC, no automatic differentiation, no marginalization operator. You can approximate a CI via bootstrap in SQL, painfully, but you cannot express *priors* (the criterion-before-result discipline encoded as `Normal(0,2)` on log-speedup), cannot do change-point inference (a discrete latent `τ` marginalized over all positions), and cannot do model comparison (LOO requires per-point held-out predictive density). The gap is **semantic, not just ergonomic**: SQL operates on the data you have; a PPL reasons about the *data-generating process*, which is the object an auditor actually wants to interrogate. Honest caveat: for clean, high-SNR benchmarks (100x, tight non-overlapping variance) there is genuinely nothing here SQL/a point estimate can't do — the machinery earns its cost *only* when signal ≈ noise, which is exactly when humans and LLMs over-claim.

## The falsifiable experiment (the trial)

**Setup.** Pull the real P2 readings table for one perf-claim that triggered a "regression" supersession where the maintainer was *unsure* (signal comparable to noise). Extract `base[]` and `new[]` timing arrays. Install `pip install numpyro arviz` (JAX already present).

**Encoding** (the speedup model, real NumPyro):

```python
def speedup_model(base, new):
    mu_b = numpyro.sample("mu_b", dist.LogNormal(0., 2.))
    mu_n = numpyro.sample("mu_n", dist.LogNormal(0., 2.))
    s    = numpyro.sample("s", dist.HalfNormal(1.))
    numpyro.sample("ob", dist.LogNormal(jnp.log(mu_b), s), obs=base)
    numpyro.sample("on", dist.LogNormal(jnp.log(mu_n), s), obs=new)
    numpyro.deterministic("speedup", mu_b / mu_n)

mcmc = MCMC(NUTS(speedup_model), num_warmup=1000, num_samples=2000, num_chains=4)
mcmc.run(jax.random.PRNGKey(0), base=jnp.array(base), new=jnp.array(new))
idata = az.from_numpyro(mcmc)
```

**Convergence gate** (admissibility to the ledger — a P3 `inference_violations` gate):

```python
s = az.summary(idata, var_names=["speedup"])
assert s["r_hat"].item() <= 1.01 and s["ess_bulk"].item() > 400
assert int(idata.sample_stats.diverging.sum()) == 0
ci = az.hdi(idata, var_names=["speedup"], hdi_prob=0.94)["speedup"].values
```

**Success criterion.** The posterior CI changes at least one historical verdict the maintainer agrees was wrong — e.g. a stored "regression" whose 94% CI actually straddles 1.0 (should have been "inconclusive"), confirmed correct by the maintainer on blind review of ≥10 such claims, with the posterior beating a naive ratio-of-means on ≥3.

**KILL CONDITION.** Retire this logic if, on those ≥10 real noisy claims, the posterior verdict (CI-relative-to-1.0) agrees with a one-line Welch t-test (p<0.05) decision in *every* case AND the maintainer judges the credible interval added no decision-relevant information over `mean±2·stderr`. I.e. if the posterior is always redundant with a t-test on *real autoharn data*, the expressiveness gap is real but empty here, and PPL is ash for this domain.

## Neutralizing false authority (verification scaffolding)

The central risk: an LLM picks a convenient prior (`Normal(0,0.1)`) and manufactures a narrow CI wearing false diligence — *worse* than a bare "12x". This is an engineering problem, solved by:

- **Pre-registered priors as ledger entries.** The prior is a *reading-with-provenance* committed `{commit,tree,session_id}` *before* the data is sampled — criterion-before-result applied to the model itself. A posterior whose prior post-dates the data is inadmissible.
- **Mandatory prior-sensitivity sweep.** Re-run with a deliberately wider prior (`LogNormal(0,4)`); if the CI moves materially, the verdict is prior-driven, not data-driven, and the gate blocks promotion. Stored as a paired reading.
- **Differential samplers.** Same model in NumPyro *and* PyMC; posteriors must agree within MC error. Divergence flags a coding bug, not physics.
- **Mutation fixtures.** Inject a synthetic known 1.5x shift into real readings; the posterior must recover it inside its CI. A model that misses a planted effect fails the fixture.
- **Posterior predictive checks** (`az.plot_ppc` / coverage stat): a model whose 90% intervals cover truth only 60% of the time is barred from "confirmed."
- **Back-translation.** The LLM emits the model as English ("base and new are lognormal with shared scale; speedup is their median ratio") for maintainer sign-off, stored alongside the code.

## Verdict: phoenix or ash — and how we'll know

**Undecided-until-trial, leaning phoenix — narrowly.** The expressiveness gap is real (SQL cannot produce `p(speedup|data)`), but its *value* is unproven on autoharn's actual noise profile. The single settling experiment is the one above: run the speedup+changepoint posteriors against ≥10 real maintainer-disputed perf-claims under the convergence and prior-sensitivity gates. **Flips to phoenix** if the posterior overturns ≥1 wrong historical verdict the maintainer ratifies and beats ratio-of-means on attribution. **Flips to ash** if every verdict collapses to a t-test on real data — the kill condition. No retreat to SQL: SQL cannot host this experiment at all, so it cannot be the answer; the only question is whether the posterior earns its place, decided by data.


---
*Verbatim first-pass output of the fair-trials workflow (run `wwr77eg5b`, claude-opus-4-8[1m]), 2026-06-27. The Witness — preserved un-corrected; read with the audit verdict above.*
