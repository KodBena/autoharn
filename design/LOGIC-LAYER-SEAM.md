# The LogicBackend seam — two engines, one NLP substrate, "add a logic = one adapter"

> The generalization of the first ASP adapter ([`LOGIC-LAYER-ASP.md`](LOGIC-LAYER-ASP.md))
> into a **standardized, pluggable logic-backend seam** over the NLP fact substrate,
> and the proof of pluggability: a SECOND adapter on a DIFFERENT engine (z3) that
> agrees with the first on the shared contradiction signature. **Additive and
> reversible** — `contra_detect.py`, `schema.sql`, `logic_layer.lp`, and the existing
> `contra_asp` entry points are UNCHANGED; rewind is `git revert` of the new files.

## The directive, in one line

Make the breadth of the
[`research/logic-fair-trials/`](../research/logic-fair-trials/)
14-logic survey **pluggable w.r.t. NLP**: every logic attaches to the SAME extracted-claim
substrate through ONE identical seam, so the choice of engine is an adapter detail,
not a pipeline rewrite. This is `experiments/impedance/`'s (a sibling chocofarm project,
not in this repo — read for the pattern, not a live path)
"**add a library = write one file**" — applied to **logics** instead of tensor libraries.

## The seam (`logic_backend.py`)

| member | role |
|---|---|
| `Claim` list (from `contra_detect.claims_from_bundle`) | the **logic-agnostic NLP interchange** — the analog of impedance's numpy-as-host carrier. Every engine consumes ONLY this; none re-parses text. |
| `LogicFinding` | the engine-neutral finding shape: the shared `signature` components **plus** the derived many-valued `value` (e.g. `"both"` for an FDE glut) — so a downstream consumer can SEE a contained glut, not just a reject. |
| `LogicBackend` (Protocol) | the STANDARDIZED seam: three members — `name`, `rules` (which rule ids this engine claims), `analyze(claims) -> [LogicFinding]`. Implement these and you have an adapter. Structural (`runtime_checkable`) — conform by SHAPE, not inheritance. |
| `cross_engine_differential` | the MECHANICAL gate: set-equality of two engines' findings on the SHARED rule set over the SAME claims. EMPTY-EMPTY == pass. |

Engine-specific knobs (the ASP `functional/1` allowlist + `multi_valued/2` defeater; the
z3 FDE semantics) are **constructor state on the concrete adapter, OFF the Protocol** —
exactly as impedance keeps a library's capability surface off `LibAdapter`. The seam pins
the *shape* of plugging in; each engine keeps its own knobs.

### Why `rules` is on the seam (honest scoping, mechanically enforced)

Not every engine covers every rule. `AspBackend.rules == {R-NEG, R-FUNC, R-NUM}`;
`FdeZ3Backend.rules == {R-NEG}`. `cross_engine_differential` runs on the **intersection**
(`shared_rules`), so an engine is never asked to answer a rule it does not claim — the
honest R-FUNC/R-NUM scoping (below) is a mechanical fact of the seam, not a hidden gap.

## The two adapters (DIFFERENT engines, ONE substrate)

| adapter | engine | paradigm | rules | the contradiction is… |
|---|---|---|---|---|
| `contra_asp.AspBackend` | **clingo / ASP** (subprocess) | stable-model + defeasible | R-NEG, R-FUNC, R-NUM | a derived `finding/3` pair (+ a `truth(…,both)` glut atom) |
| `fde_z3.FdeZ3Backend` | **z3 / SMT** (direct import) | **paraconsistent many-valued (FDE/LP)** | R-NEG | a first-class VALUE — the atom is `Both`, read from a z3 model |

`AspBackend` is a thin re-shaping of the already-differential-gated `asp_findings`
into `LogicFinding`s — the encoding (`logic_layer.lp`), EDB export, and clingo driver
are unchanged. `FdeZ3Backend` is a genuinely different engine and paradigm: it encodes
R-NEG in the Belnap-Dunn **two-bit** trick (`25-paraconsistent-manyvalued.md`, the
verified z3 encoding) — each atom carries `_t`/`_f`, the four values are T(1,0), F(0,1),
**Both(1,1)**, Neither(0,0) — and asks z3, **per source pair**, whether the pair is a
glut. The glut DECIDES the finding (no separate pos/neg gate), so the two-bit encoding
is genuinely load-bearing.

## Does FdeZ3 agree with ASP / the Python oracle? **Yes, exactly.**

Three channels — z3/FDE, clingo/ASP, and the independent Python oracle
(`contra_detect.find_contradictions`) — agree on the shared R-NEG signature, on the
synthetic fixture AND a real RFC:

```
synthetic  : fde == asp == oracle on R-NEG   (1 glut: socrate/be)   only_*=∅   PASS
rfc2616.txt: fde == asp == oracle on R-NEG   (5 R-NEG, non-vacuous)  only_*=∅   PASS
```

The comparison key is `(rule, subj_key, pred, sorted pair of claim text)` — exactly the
tuple the oracle dedups on — so A/B ordering cannot manufacture a divergence. Two
DIFFERENT solvers, one NLP interchange, identical contradiction set. That agreement IS
the pluggability proof. (rfc2616 was chosen because it genuinely contains R-NEG —
rfc791/793 have zero, so the gate is non-vacuous.)

## Mutations caught (+ the one honest exclusion)

Each mutation flips ONE load-bearing knob of the two-bit FDE encoding
(`FdeSemantics`); every mutant MUST change the fixture verdict (a surviving mutant = a
knob that did no work — the z3 analog of the ASP `.lp` text mutations):

| mutation | effect when flipped |
|---|---|
| `glut_is_both_bits` AND→OR | every asserted same-polarity pair becomes a "glut"; the decoys (capital/marie/committee/shelf) light up |
| `pos_value_t` (pos no longer told-true) | the socrate atom's `told_true` empties; the real glut is lost |
| `neg_value_f` (neg no longer told-false) | the socrate atom's `told_false` empties; the real glut is lost |
| `join_is_or` OR→AND (Belnap join) | a pos+neg pair has t-bits {1,0}; AND collapses `told_true` to 0; the real glut is lost |

**Honest exclusion (named, not dressed up as caught — the analog of the ASP `A<B`
exclusion):** the full **T↔F symmetry** (`pos_value_t=False` *and* `neg_value_f=False`
together) is a symmetric relabeling of the two bits — it maps every source's value
T↔F, so a {pos,neg} pair is still `Both` and a same-polarity pair still isn't. It
**survives** (verdict-equivalent); `test_honest_exclusion_is_genuinely_verdict_equivalent`
asserts it survives, so the exclusion is itself a test, not a claim.

## FDE's honest earns-its-keep (NOT precision)

R-NEG is **already the cheap SQL floor** (`mining.contradiction`) and the ASP/Python
R-NEG set. So `FdeZ3Backend` does **not** claim to find more than ASP — it finds the
SAME set through a different engine. Its genuine win is **non-explosion + the queryable
`both` value**, proved mechanically (`test_fde_contains_what_classical_explodes`):

```
atom = {asserted, denied}:  classical  ⊢  a ∧ ¬a   → UNSAT  (explodes; any ⇒-false passes vacuously)
                            FDE        ⊢  Both      → SAT    (contained, queryable `both`)
```

`fde_contains([True, False]) == True`: on the atom where classical EXPLODES, FDE keeps
the instance SAT and surfaces a contained `both` a consumer can route on — the exact
lethal failure FDE removes (`25-paraconsistent-manyvalued.md`).

## Deontic is deliberately OFF the menu

This seam is for **reasoning over NLP-extracted claims** —
consistency / contradiction / epistemic state, the **CONSIST** obligation. It is NOT
for deontic obligation-**execution** (duty detachment, norm precedence, contrary-to-duty
repair). Those quantify over a state machine, not a bag of claims, and live in a
different pillar (the obligations survey). A backend here answers *"do these claims
conflict, and how is the conflict contained?"* — never *"what must the agent now do?"*.

## R-FUNC / R-NUM stay ASP's (flagged future work)

`FdeZ3Backend` covers only R-NEG. R-FUNC (functional-dependency defeasibility) and
R-NUM (numeric disequality) are **not** paraconsistent-many-valued concerns; forcing
them into an FDE two-bit encoding would be unfaithful. They remain ASP's
(`rules = {R-NEG}` makes this mechanical via `shared_rules`). A faithful z3 home for
R-NUM **magnitude** reasoning (`>`, tolerance, unit coercion) is the next adapter — the
same two-bit/`QF_LRA` route `25-paraconsistent-manyvalued.md` describes — not a forced
fit here.

## How the rest of the fair-trials breadth plugs in next

The seam is engine-neutral, so each remaining logic family is **one adapter on the
`Claim` substrate**:

- **Datalog / souffle** (`01-datalog.md`) — recursive reachability over the claim graph;
  one `analyze` that runs a `.dl` program over the same EDB export.
- **Defeasible argumentation** (`04-defeasible-argumentation.md`) — an adapter that ranks
  conflicting claims by an argument framework; `rules` = its own attack-resolution tags.
- **Description logic / OWL** (`08-description-logic.md`) — consistency of the entity
  graph against an ontology; `analyze` returns unsatisfiable-class findings.
- **R-NUM magnitude in z3** — extend `FdeZ3Backend` (or a sibling) to `QF_LRA`, adding
  `R-NUM` to its `rules`; `cross_engine_differential` then gates it against ASP on R-NUM.

Each is "add a logic = one adapter on the FactBundle, any engine", differential-gated
against the oracle or a sibling engine. The mechanical cross-engine gate is the
**fair-trials deflation lesson** (`AUDIT.md`) honored: the correctness gate is set
equality, never a model's judgment.

---
*References: [`LOGIC-LAYER-ASP.md`](LOGIC-LAYER-ASP.md); `experiments/impedance/`
(`README.md`, `impedance/adapter.py` — the seam pattern); `docs/research/
2026-06-27-obligations-formalisms-survey/formal-systems/25-paraconsistent-manyvalued.md`
(the verified z3 two-bit FDE encoding); `docs/research/2026-06-27-logic-fair-trials/`
(`README.md`, `AUDIT.md` — the mechanical-gate / deflation lesson); in-repo `docs/adr/`
ADR-0000 / 0002 / 0009 / 0012 / 0013.*
