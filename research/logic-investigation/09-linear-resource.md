# 09 — Linear & Resource-aware Logic

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../GLOSSARY.md)**.

Linear logic (Girard, 1987) is a logic where propositions are *consumed* when used: a hypothesis is a finite resource, not a reusable fact. "Resource-aware" relatives — Concurrent LF, rewriting logic, Constraint Handling Rules, Petri nets — track *multisets of facts that are produced and spent*, making them the natural fit for state, ledgers, and lifecycle transitions.

## Primer

In classical/Datalog logic, once `A` is true it stays true and can fire any number of rules — perfect for autoharn's *knowledge* facts, wrong for its *resource* facts. Linear logic splits the connectives: `A ⊗ B` ("have both"), `A ⊸ B` ("spend an A, get a B"), and `!A` (the escape hatch: an unlimited, classical fact). The one idea that matters: **using a premise deletes it**. A rule `dirty_tree ⊗ benchmark ⊸ unpromotable` *consumes* the `benchmark` token so it cannot also be counted as `confirmed`. The intuition for *when* to reach for it: whenever the truth you model is a *transition of state* — a belief gets superseded, a provisional decision is overridden, a reading is committed then judged — rather than an eternal fact. If you find yourself writing SQL `UPDATE`s or `DELETE`s to keep a table "current", that mutation *is* a linear-logic step, and modeling it as one makes the consumption auditable instead of destructive.

## Applicability to autoharn

**Pillar 1 — liveness as refreshable / "REFUTED belief must be superseded, not stale" (fit: high).** This is literal resource consumption: a refutation *spends* the old liveness token. In SWI-Prolog's **CHR** (Constraint Handling Rules — committed-choice multiset rewriting, linear-logic semantics, ships in stock SWI 9.3.31):

```prolog
:- use_module(library(chr)).
:- chr_constraint live/2, refute/2, dead/2.
% refute consumes the matching live fact; cannot fire twice
refute(Cap,Sess) \ live(Cap,_) <=> dead(Cap,Sess).
```
The `\` means `refute` is kept, `live` is removed. Plain SQL would need a trigger + `UPDATE`; CHR makes the supersession a *derivation step*, so the violation gate can ask "is any `live` provably consumed-but-present?" — structurally impossible here.

**Pillar 2 — measurement SEPARATE from interpretation; perf-token must reference a stored reading (fit: high).** Model a `reading` as a *linear* resource and an `interpretation` as something that *consumes exactly one*:
```prolog
:- chr_constraint reading/3, claim/2, unsubstantiated/1.
claim(Tok,Read) , reading(Read,_,_) <=> ground(Read) | true.   % discharged
claim(Tok,none) <=> unsubstantiated(Tok).                      % honest-NULL
```
A `"12x"` claim that finds no matching `reading` cannot discharge and falls through to `unsubstantiated` — the marker becomes *forced by the logic*, not by reviewer vigilance. This beats a Python script because the linearity (one claim ⊸ one reading) is the invariant itself, not an assertion bolted on top.

**Pillar 2 — DIRTY benchmark must NOT be promoted (fit: high).** A `⊗`-consuming rule: a promotion *needs* a `clean_tree` token it can spend; a dirty tree never mints one.
```prolog
promote(Bench) , clean(Tree) , benchof(Bench,Tree) <=> confirmed(Bench).
% no clean(Tree) for a dirty tree  =>  promote() is simply stuck (suspect/unknown)
```
The "stuck" state is exactly the paraconsistent 3rd value you want: the claim coexists as un-promoted without exploding the gate.

**Cross-cutting — non-monotonic supersession of ADR amendments / provisional decisions (fit: med).** Linear consumption is a *clean* model of override: `amend ⊸` retracts the prior token rather than leaving two live decisions. CHR handles this directly; it beats Datalog/SQL, which are monotone and need bolted-on `valid_until` columns. Med, not high, only because the *append-only SUPERSEDES chain* (Pillar 2) wants the prior **kept** — so you'd model the audit trail in Postgres and use CHR only for the "what is currently live" projection.

**Pillar 3 / status lifecycle provisional→confirmed→retracted (fit: med).** Rewriting logic (Maude) expresses a lifecycle as rewrite rules `provisional => confirmed`, with its model-checker proving *no path reaches* `confirmed` from a dirty state. Stronger than SQL but heavier; med because Z3 or a CHR gate already covers most of this.

**Forced / weak fits (honest):** Linear logic does **nothing** for Pillar 1's *classification discipline* (that's a closed-vocabulary `CHECK`/Z3 enum job), for abduction/ILP, or for probabilistic "hunch vs truth". Reaching for `!`/`⊗` there is cargo-culting.

## Software to leverage

| tool | role | license | language / bindings | install cost | maturity | LLM-friendliness |
|------|------|---------|--------------------|--------------|----------|------------------|
| **CHR in SWI-Prolog** | resource rewriting for liveness/claim/promotion gates | BSD-2 (SWI) | Prolog; `library(chr)` | **none — installed** (SWI 9.3.31) | high | high — small, readable rules; LLM-writable |
| **Celf / LolliMon** | full CLF (linear ⊸, `!`, monadic concurrency); spec & proof search | GPL-3.0 | Standard ML (MLton/SML-NJ); CLI | compile-from-source (SML toolchain) | research-grade, low activity | low — niche syntax, sparse training data |
| **Maude** | rewriting logic + LTL model-check of status lifecycle | GPL-2.0 | C++; single static binary + CLI | medium (prebuilt binary; not in default apt) | high, v3.5.1 (2025) | med — clean syntax, some examples |
| **(reuse) networkx** | Petri-net reachability as a lightweight resource check | BSD | Python | **installed** | high | high |

## Limits & honest take

The biggest hazard is **false authority via mis-encoding**: linearity lives entirely in *which connective you pick*. Write `!benchmark` (reusable) where you meant `benchmark` (one-shot), and the engine cheerfully "proves" a dirty benchmark is promotable — a green, confident, *wrong* result. Because `⊗`/`!` are invisible-looking and under-represented in training data, an LLM is *more* likely to mis-place them than to write a wrong SQL `WHERE`. Mitigation: keep linear models tiny, dump the consumed-resource trace, and cross-check every "stuck/discharged" outcome against a Postgres `_violations` query — never let the linear proof be the *sole* gate. Second, the real research engines (Celf, LolliMon) are dormant academic code: powerful but a maintenance liability for a metaproject that prizes mechanisms still resolving on disk. The pragmatic truth: you almost never need *general* linear logic — you need its *consumption discipline*, and **CHR (already installed)** delivers that with the least ceremony. Maude earns its place only if you genuinely want to *model-check* the lifecycle. Treat Celf as reference reading, not infrastructure.

## References & learning

- **Girard, "Linear Logic" (TCS 1987)** — the source; teaches why `!` and `⊗` exist and what "consuming a hypothesis" means.
- **Frühwirth, *Constraint Handling Rules* (CUP, 2009)** — the practical bridge: how multiset rewriting (your real engine) realizes linear-logic semantics.
- **SWI-Prolog `library(chr)` docs** (swi-prolog.org/pldoc/man?section=chr) — copy-paste runnable rules in the syntax you'd actually ship.
- **Schack-Nielsen & Schürmann, "Celf — A Logical Framework…" (IJCAR 2008)** — what a *full* linear/concurrent LF buys you, to judge whether you ever need more than CHR.

Sources: [Celf](https://clf.github.io/celf/), [LolliMon](https://github.com/clf/lollimon), [Maude](https://maude.cs.illinois.edu/), [Maude GitHub](https://github.com/maude-lang/Maude)


---
*Verbatim output of the `autoharn-logics-investigation` workflow (run `wf_6be06f87-68d`, model claude-opus-4-8[1m]), 2026-06-27 — one expert agent per logic family, grounded in autoharn. The maintainer should treat engine version/license claims as agent-reported (web-checked where noted), worth a confirm before install.*
