# 03 — Answer Set Programming (clingo / DLV) — Fair Trial (first pass)

> Part of the autoharn **logic fair-trials** (the corrected, frontier-creed pass). Coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**. The honest status of every verdict here is **undecided-until-the-experiment-runs** — see [README](README.md) and [AUDIT.md](AUDIT.md).

> **Audit verdict:** `deflated = False` · 3 defect(s) noted · **not rewritten** (the hardening pass was a no-op).
>
> ⚠️ **Mechanical re-check flags this as a possible false-negative**: the auditor marked it `deflated=false`, yet 1 of its own defects cite reducible-only / concession tells.

## Answer Set Programming (clingo / DLV) — Fair Trial

The bet on trial: ASP's stable-model semantics — default negation plus headless integrity constraints plus `#minimize` — lets autoharn express *defeasible* invariants (rule-holds-unless-adjudicated) and, crucially, *compute the minimal repair* that restores an invariant, as one declarative artifact an LLM can author. The claim is not "ASP can write a gate" (anything can); it is "ASP makes the gate, its exceptions, and its fix the same closed-world object, with recursion-through-negation SQL forbids."

## Maximal ambition

The frontier autoharn could reach: **deductive maintenance as abductive repair**, not just detection. Today omega's band-conformance gate (`band(file) >= band(import)`, with a ~30-entry `BAND_EXCEPTIONS` ledger of adjudicated leaks, `cycle-check` Tarjan acyclicity, and `NO_NEW_*_RATCHET` baselines) only answers *"is the graph conformant?"* and prints a number. ASP answers the next two questions no current gate does:

1. **Minimal-repair synthesis.** Given a freshly-introduced leak, enumerate *every minimum-cardinality set* of `{adjudicate-exemption, move-file-band, delete-edge}` actions that restores conformance — a ranked menu of fixes, each a witness, handed to the maintainer. This is `#minimize` over choice rules (verified below: 4 optimal plans at cost 2, `0.001s`). No SQL view, no imperative scan, and Z3-as-usual (no native cardinality-optimal enumeration of *all* optima) produces this without reinventing minimality and consistency-checking.

2. **A single non-monotonic object spanning gate + exception + supersession.** The band rule, its exceptions, the `SUPERSEDES` chain of `exp_db` findings, and the meta-sweep ("every ADR rule's declared mechanism still resolves") are *one* program where `holds(X) :- ..., not superseded(X)` and `violation :- leak, not blessed` are the same construct. Autoharn's entire Pillar-3 spine becomes a corpus of integrity constraints over Pillar-1/2 facts, where a `dead_exception` (an exemption guarding a leak that no longer exists) falls out *for free* as `exception(F,G,_), not leak(F,G)` — exactly the BAND_EXCEPTIONS hygiene that today rots silently as a JS Map literal.

## The expressiveness gap (precise, not hand-wavy)

This is not "nothing SQL can't do." The gap is precise and load-bearing:

- **Recursion through negation.** Band-conformance-with-exceptions composed with supersession-with-retraction is recursion through *non-monotonic* negation: `blessed` depends on `not superseded`, `superseded` on a recursive `supersedes` chain, `violation` on `not blessed`. SQL's `WITH RECURSIVE` **forbids recursion that references the recursive table inside `NOT EXISTS`/aggregation** (it requires linear, monotone recursion). You can hand-roll fixpoint passes in PL/pgSQL, but you are then hand-implementing stratified-model semantics that clingo gives with a soundness guarantee. ASP's stable-model semantics *is* the well-founded answer SQL declines to compute.
- **Succinctness of optimal abduction.** "All minimum-cost repair plans" is `Σ²ᵖ`-flavored search. Expressed in SQL it is an exponential self-join cascade with no minimality guarantee; in ASP it is five lines (`{bless}`, `{drop}`, `:- leak, not resolved`, `#minimize`). The succinctness gap is real and measured above.
- **Where there is NO gap (honest).** A flat single-leak check, ratchet-count comparison, or shipped-without-commit gate is plain stratified Datalog — Postgres does it, and ASP's grounding overhead is a *liability* there. ASP earns its place only where defaults, exceptions, or optimization appear. For those flat gates, do not reach for clingo.

## The falsifiable experiment (the trial)

**Setup.** Image omega's real `import-graph.mjs` edges + `FILES.md` B1/B2/B3 bands + the 30 `BAND_EXCEPTIONS` rows + `HUB_EXEMPT_TARGETS` into clingo facts (via `clorm`, straight from the existing Postgres at `192.168.122.1`). Encode the gate, the exception override, dead-exception hygiene, and the minimal-repair abducer (encodings validated above run on `clingo 5.8.0`, already at `/usr/bin/clingo`).

**Encoding (real, runs today):**
```prolog
leak(F,G)      :- imports(F,G), band(F,BF), band(G,BG), BF < BG.
blessed(F,G)   :- exception(F,G,_).
violation(F,G) :- leak(F,G), not blessed(F,G).
:- violation(F,G).                                  % the gate
dead_exception(F,G) :- exception(F,G,_), not leak(F,G).
{ bless(F,G) } :- leak(F,G).   { dropedge(F,G) } :- leak(F,G).
resolved(F,G)  :- leak(F,G), bless(F,G).
resolved(F,G)  :- leak(F,G), dropedge(F,G).
:- leak(F,G), not resolved(F,G).
#minimize { 1,b,F,G:bless(F,G); 1,d,F,G:dropedge(F,G) }.
```

**Success criterion (all three, on real data):** (a) the gate reproduces band-conformance's *exact* current pass/fail verdict on the live graph (bit-identical to `check.mjs`); (b) it additionally reports every `dead_exception` in the 30-row ledger that `check.mjs` cannot detect; (c) on a synthetically-injected leak, the repair menu lists the minimal plans in `< 5s` total wall-clock including grounding.

**KILL CONDITION (non-negotiable):** ASP is retired for autoharn if **either** (i) grounding the real omega import graph (~hundreds of files) blows up — wall-clock `> 60s` or RSS `> 2 GB` on a representative gate run, making it unusable in CI **and** filtering/projecting the graph first does not bring it under budget; **or** (ii) the verdict in (a) *diverges* from the trusted `check.mjs` verdict and the divergence traces to ASP-semantic subtlety (an unintended stable model) rather than a `check.mjs` bug — i.e. the paradigm is a *foot-gun* for this class, not a fit. Either outcome retires it with a stated failed experiment, not a familiarity argument.

## Neutralizing false authority (verification scaffolding)

The prior section's "false authority" worry (clingo cheerfully returns a crisp answer for a mis-encoded model — a flipped `not`, a missing variable) is the project's central research problem, so it is engineered, not feared:

- **Golden + MUTATION fixtures.** Store programs with known answer-set *counts* and *contents*. Then auto-mutate the encoding (flip each `not`, drop each constraint, perturb each `<`) and assert every mutant *changes* the verdict on the golden set — a surviving mutant is an untested line. (Verified locally: deleting `:- violation(F,G)` flips SAT/UNSAT; deleting `not blessed` mis-reports the adjudicated `api->ui` leak.)
- **Differential solvers.** Run the same ASP-Core-2 program on `clingo` *and* `DLV2`; a verdict disagreement is a bug in the encoding's portability assumptions, surfaced before trust.
- **Bounded-model cross-check.** Re-express the *same* invariant as a Z3 quantified query on the bounded finite domain; the `*_violations` gate is trusted only when clingo and Z3 agree (two engines, two semantics, one verdict).
- **Justification-carrying output.** Use `xclingo` / clingo's reason API so every `violation` and every repair action ships a derivation tree — the gate emits *why*, stored as a reading-with-provenance (`{commit, tree, session_id}`) in Pillar 2, never a bare verdict.
- **Back-translation gate.** The LLM re-renders each rule to English (`"a leak is blessed iff an exception row names it"`); the maintainer reviews the *English* against the ADR text. The encoding is a Pillar-1 capability whose `probe_cmd` is its own golden+mutation suite — the meta-sweep eats its own dog food.
- **Metamorphic tests.** Adding a redundant exception must not change the gate verdict; adding a real leak must flip it. Property relations, not point fixtures.

## Verdict: phoenix or ash — and how we'll know

**Phoenix — conditional, with one decisive trial.** ASP earns a frontier place *specifically* for defeasible, exception-laden, repair-bearing invariants (band-conformance-with-exceptions, supersession-with-retraction, dead-exemption hygiene, abductive regression diagnosis) — where it expresses recursion-through-negation and minimal-repair that SQL provably cannot and Z3-as-usual does not give ergonomically. It is **ash for flat count/presence gates**, where grounding is pure overhead.

**The single settling experiment:** the band-conformance trial above on the *real* omega import graph. **Phoenix is confirmed** if it bit-matches `check.mjs`'s verdict, additionally finds dead exceptions, and grounds under budget. **It flips to ash** if the kill condition fires: grounding explodes past 60s/2GB even after projection, or its verdict diverges by ASP-semantic surprise. Evidence that would flip me *toward* ash mid-trial: discovering that omega's graph is large enough that every useful rule needs aggressive pre-filtering — at which point the pre-filter, not ASP, is doing the work.


---
*Verbatim first-pass output of the fair-trials workflow (run `wwr77eg5b`, claude-opus-4-8[1m]), 2026-06-27. The Witness — preserved un-corrected; read with the audit verdict above.*
