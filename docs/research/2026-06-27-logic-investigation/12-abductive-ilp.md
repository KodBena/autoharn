# 12 — Abductive Reasoning & Inductive Logic Programming

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../../GLOSSARY.md)**.

Two complementary "backward" logics: **abduction** infers the most plausible *causes/hypotheses* that would explain an observation given a theory; **ILP** infers the *general rule* (a logic program) that covers positive examples and excludes negatives. Deduction goes premises→conclusion; abduction goes conclusion→best premise; induction goes examples→rule.

## Primer

You know Z3 answers "is this set of constraints satisfiable, and give me a model." Abduction flips the question: *I observe O; my theory T can't currently derive it; which extra ground facts A (drawn from a declared "abducible" set, kept minimal and consistent) would make T ∧ A ⊨ O?* In ASP (clingo) you encode this as a `{abducibles}` choice plus `:- not observation` and a `#minimize` — the answer set *is* the hypothesis. ILP is the learning sibling: you give positive/negative examples plus background facts and a **bias** (which predicates/arities may appear in a rule head/body), and the engine searches the hypothesis space for the smallest program that entails all `pos` and no `neg`. The intuition for "right tool": reach for abduction when you have a *partial causal theory* and want ranked explanations of a surprise; reach for ILP when you keep hand-writing the same `_violations` rule from examples and want the rule *synthesized and generalized* instead.

## Applicability to autoharn

**1. Hypothesis generation to explain a regression (abduction) — fit: HIGH.** This is named explicitly under cross-cutting shapes. A perf-claim token flips from "matches baseline" to "regression"; autoharn has a theory of candidate causes (dirty tree, dependency bump, env drift, GC). Abduction returns the *minimal consistent* cause-set, not just "UNSAT." In clingo:

```prolog
cause(dirty_tree). cause(dep_bump). cause(env_drift).
{ holds(C) : cause(C) }.                       % abducibles
regression :- holds(dirty_tree).
regression :- holds(dep_bump), touched(solver_lib).
touched(solver_lib).                            % background reading
:- not regression.                             % must explain the observation
#minimize { 1,C : holds(C) }.                  % Occam: fewest causes
```

Answer sets enumerate ranked explanations. **Beats Z3**: Z3 gives *a* satisfying model with no minimality/enumeration-of-all-explanations story; ASP's `#minimize` + multi-model output is purpose-built for parsimonious abduction. **Beats a Python script**: the script would hard-code an if/else cause tree (a Rule-4 violation — enumerating instances); the ASP theory keys on the *structure* of causation.

**2. Learning `_violations` rules from examples (ILP) — fit: HIGH→MED.** Pillar 3 demands gates that key on the *class* of a defect (Rule 4), never an enumeration. Today the maintainer hand-writes each `WITH RECURSIVE` gate. ILP lets you *induce* the gate from labelled good/bad rows. Popper bias + examples:

```prolog
% bias.pl
head_pred(bad_finding,1).
body_pred(perf_token,1). body_pred(no_reading,1). body_pred(dirty,1).
% examples.pl
pos(bad_finding(f12)).  neg(bad_finding(f07)).
% bk.pl
perf_token(f12). no_reading(f12). dirty(f07).
```

Popper synthesizes `bad_finding(X):- perf_token(X), no_reading(X).` — exactly the "every perf-claim token references a stored reading" invariant, *learned* rather than dictated, and generalizing to unseen rows. **Beats SQL**: you don't yet know the predicate; SQL can only *check* a rule you already wrote. **Honest caveat**: ILP shines when you have many clean labelled examples; with 3 findings it's overkill — MED until the ledger is populous. Treat induced rules as *provisional* (status lifecycle) pending maintainer blessing.

**3. Capability classification discipline (Pillar 1) — fit: MED.** "lib xor solver xor service xor venv xor script" is a closed-world mutual-exclusion that ASP states natively (`:- is_a(C,solver), is_a(C,lib).` + a choice rule forcing exactly one). But this is equally well a SQL `CHECK`/Z3 boolean — abduction/ILP only earn their keep here if you want to *learn* the classifier from feature examples. Forced fit; prefer the simpler tool unless eliciting from examples.

**4. Statistical-hunch-vs-provable-truth bridge — fit: MED.** ILP's extensions (probabilistic ILP / abduction over weighted rules) sit exactly on the maintainer's axis, but the mature ASP/Popper stack is crisp-logic; probabilistic variants (ProbLog) are a separate engine. Honest: this need is better served by the probabilistic-logic expert; note the handoff.

Non-fits: append-only SUPERSEDES chains, pre-registration temporality, and {commit,tree,session_id} provenance are *recording/temporal* concerns — Datalog/Postgres and the modal-logic layer own them. Abduction/ILP consume those facts; they don't store them.

## Software to leverage

| tool | role | license | language / bindings | install cost | maturity | LLM-friendliness |
|---|---|---|---|---|---|---|
| **clingo / Potassco** | ASP solver for abduction (choice + `#minimize` + multi-model) | MIT | C++; first-class Python `import clingo` + CLI | **already installed** (5.8.0; py-binding pip) | very mature, active | high — declarative, small files, well-documented |
| **Popper** | modern ILP (learning-from-failures) | MIT | Python CLI (`uv run popper.py`); needs SWI-Prolog + clingo | pip/git; deps present (swipl 9.3.31, clingo 5.8.0) | active research-grade | high — separate `bias/bk/examples` files map cleanly to prompts |
| **Aleph** | classic Progol-style ILP, inverse entailment | permissive (academic/Artistic-style) | SWI-Prolog pack (`pack_install(aleph)`) | pip-free, one pack cmd; swipl present | mature, stable, less active | med — Prolog-heavy, mode declarations terse |
| **ProbLog** | probabilistic ILP/abduction (the hunch↔truth axis) | Apache-2.0 | Python `pip install problog` | pip (light) | mature | med-high |

Local check: `swipl 9.3.31`, `clingo 5.8.0` both present; only the Python `clingo` wheel and Popper/Aleph packs need pulling (all light, none heavy/compile).

## Limits & honest take

- **False-authority is the headline risk.** An LLM that mis-states the abducible set or a Popper mode bias gets a *syntactically valid answer set / a clean induced clause that is confidently wrong* — the model "proves" a regression cause that's an artifact of an omitted abducible. Mitigation: the encoding (theory + bias) must itself be a reviewed, version-pinned artifact carrying `{commit,session_id}`, and induced rules enter as **provisional**, never auto-promoted to a CI gate.
- **ILP needs data.** With a near-empty ledger it overfits or finds nothing; it's a *later-stage* mechanism. Don't sell it before the provenance ledger has dozens of labelled rows.
- **Hype vs substance:** abduction is genuinely substantive for *ranked* regression explanations (beats Z3's single model); ILP for *synthesizing* Rule-4-class gates. But classification discipline and provenance recording are NOT ILP problems — forcing them there adds a fragile second engine for what SQL/Datalog does plainly.
- **Non-determinism:** multiple minimal abductive explanations coexist — feature, not bug (matches the paraconsistent "suspect/unknown" shape), but the gate must treat "≥1 explanation" as *suspect*, not *confirmed*.

## References & learning

- **Cropper & Dumančić, "Inductive Logic Programming at 30: a new introduction" (JAIR 2022)** — the modern survey; teaches the learning-from-failures framing behind Popper.
- **Popper README + "Learning programs by learning from failures" (MLJ 2021)** — the exact `bias/bk/examples` file format you'd hand an LLM to generate.
- **Potassco clingo guide (potassco.org/guide)** — how to write the choice-rule + `#minimize` abduction pattern that runs on the already-installed solver.
- **Kakas, Kowalski & Toni, "Abductive Logic Programming" (1992 survey)** — the foundational "abducibles + integrity constraints" model autoharn's regression-explainer should follow.

Sources: [Popper](https://github.com/logic-and-learning-lab/Popper), [clingo](https://github.com/potassco/clingo), [ILP@30](https://link.springer.com/article/10.1007/s10994-020-05934-z), [Aleph pack](https://swi-prolog.discourse.group/t/popper-inductive-logic-programming-ilp-and-my-popper-page/3929)


---
*Verbatim output of the `autoharn-logics-investigation` workflow (run `wf_6be06f87-68d`, model claude-opus-4-8[1m]), 2026-06-27 — one expert agent per logic family, grounded in autoharn. The maintainer should treat engine version/license claims as agent-reported (web-checked where noted), worth a confirm before install.*
