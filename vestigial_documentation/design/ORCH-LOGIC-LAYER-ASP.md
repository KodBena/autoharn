# The ASP logic layer — paraconsistent, differential-gated contradiction logic

Audience: orchestrator

> First real wiring of the project's *"facts in many logics"* thread to an actual
> solver. Until now that thread was prose (`docs/research/`, 2026-06-27) + SQL views;
> this is the first logic-**encoding** code. It is **additive and reversible**: the
> Python oracle (`contra_detect.py`) and the SQL substrate (`schema.sql`) are
> UNCHANGED. Rewind is `git revert` of the new files.

## What it is

Three files, over the SAME `FactBundle`/`Claim`s the Python detector already consumes:

| file | role |
|---|---|
| `logic_layer.lp` | the three rules as declarative clauses; derives **paraconsistent values**, not classical rejects |
| `logic_repair.lp` | minimal-repair / blame as a `#minimize` (the one ASP-over-SQL search) |
| `contra_asp.py` | the subprocess driver (clingo **CLI**, JSON output) + the differential gate + EDB export |
| `test_contra_asp.py` | the encoding-trust gate: golden + mutation + differential |

The Python `clingo` binding is **not** in the venv (only the system CLI 5.8.0 is —
confirmed in `B-autoharn-fit.md` s.0), so the solver is driven by **subprocess**
(`clingo logic_layer.lp - --outf=2`, JSON parsed). No heavy deps were pip-installed.

### The shared EDB (the allowlist moves out of code into DATA)

`contra_asp.edb_from_claims` exports, from the identical `Claim` list:

```prolog
assertion(Id, SubjKey, Pred, ObjKey, Pol).   % Pol = pos | neg   (the `negated` seam)
functional(Pred).                            % the FUNCTIONAL_PREDS allowlist, AS DATA
number(Id, CanonStr).                        % the transparent parse, only when parseable
multi_valued(SubjKey, Pred).                 % defeater seam (default: empty)
```

`Id` is the claim's index in `claims_from_bundle(bundle)` — a stable shared identity
the differential maps back through, so **neither side re-derives the other's claim
text**. The ASP side emits findings as integer-id pairs only; no text crosses the
wire. Crucially, the Python `FUNCTIONAL_PREDS` frozenset is now an **auditable,
retractable EDB fact** (`functional/1`) rather than a hard-coded constant — an
improvement the research explicitly calls for.

## The CONSIST obligation

This discharges **[CONSIST]** — *"contradictions are quarantined; no ex-falso, no
silent side-picking"* (`01-obligation-taxonomy.md` s.10). The defining move, from
`25-paraconsistent-manyvalued.md` and the FDE/Belnap four-valued tradition: a
contradiction is a **first-class inspectable value carried on the atom**, not a `:- `
integrity constraint that detonates (ex contradictione quodlibet). `logic_layer.lp`
emits `truth(S,P,O,both)` for an R-NEG glut — *contained and queryable* — and stays
SATISFIABLE; a classical encoding asserting `p` and `¬p` as one Boolean would be
UNSAT and any downstream `(=> false …)` would pass vacuously, the exact lethal
failure FDE removes.

## Three rules, three logics

| rule | EDB seam | derived value | logic |
|---|---|---|---|
| **R-NEG** | `pos`/`neg` polarity | `truth(S,P,O,both)` + `finding(neg,A,B)` | paraconsistent glut (FDE/LP `Both`, designated) |
| **R-FUNC** | `functional/1`, `multi_valued/2` | `conflict_func(S,P)` + `finding(func,A,B)` | **defeasible** / non-monotonic (default `not exception`) |
| **R-NUM** | `number/2` | `finding(num,A,B)` | disequality over canonical parsed values |

R-NUM honesty: the parse happens once in Python (`contra_detect.parse_number`,
already audited) and the canonical value is shipped as a term; clingo does the
**disequality** — faithful to the Python rule, which is itself disequality, **not**
magnitude arithmetic. True magnitude/tolerance reasoning (`>`, approx-equal, unit
coercion) would need `clingcon` or the **Z3 two-bit encoding** of doc 25; that is
honestly future work, not claimed here.

## The differential result — does clingo match the Python oracle?

**Yes, exactly.** The comparison key is `(rule, subj_key, pred, sorted pair of
_claim_text)` — precisely the tuple `find_contradictions()` dedups on — so A/B
ordering and the reverse-pair dedup cannot cause a false divergence. clingo decides
*which pairs are findings* (the logic); Python supplies the *surfaces* (the data).

```
synthetic fixture : |asp|=3  |py|=3   only_asp=∅  only_py=∅   PASS
rfc791.txt (386 c): |asp|=124 |py|=124 only_asp=∅ only_py=∅   PASS   (R-FUNC×142-raw, R-NUM×22)
rfc2616.txt (425 c): |asp|=39 |py|=39  only_asp=∅ only_py=∅   PASS
rfc793.txt (370 c): |asp|=44 |py|=44  only_asp=∅ only_py=∅   PASS
```

(Raw ASP id-pair count can exceed the Python count when duplicate sentences yield
duplicate-text pairs; both sides collapse them under the signature, and the
**signature sets are identical** — the differential is over the deduped sets, exactly
Python's `emit()` semantics.) The real-doc gates are **non-vacuous**: the RFCs
genuinely contain contradictions, so this is not an empty==empty pass.

## The mutation result — did every mutant get caught?

**Yes — all 5 load-bearing mutants flip the verdict** on the fixture (`a surviving
mutant = a dead clause`):

| mutation | effect when flipped |
|---|---|
| R-NEG polarity `neg → pos` | R-NEG self-joins positives; loses the real Socrates glut |
| R-FUNC object `!=  → ==` | fires only on equal objects; loses the capital finding |
| R-FUNC defeater `not exception → exception` | body never satisfiable; loses the capital finding |
| R-FUNC allowlist (drop `functional/1`) | fires on `visit` too; the Marie decoy lights up |
| R-NUM value `!=  → ==` | fires on equal numbers; the `shelf/three` decoy lights up, committee lost |

Honesty: `A < B` is **deliberately excluded** from the mutation set. Flipping it to
`A != B` or `A <= B` is dedup-equivalent under the signature set (it is an
efficiency/anti-double-count nicety, not a load-bearing discriminator), so it would
*survive* — and a surviving mutant dressed up as "caught" would be exactly the
green-tuxedo-on-a-bug failure this gate exists to prevent. It is named and excluded,
not hidden.

## Where ASP earns its keep over SQL (the honest claim)

R-NEG is **already the cheap SQL floor** — `mining.contradiction` is R-NEG in a view,
and `B-autoharn-fit.md` (N14) shows most of this is a "SQL-schema-plus-views job"
where exotic logic is net-negative. So we do **not** claim ASP beats SQL on R-NEG. The
genuine, demonstrated win is **R-FUNC's defeasibility** (N15 — *"this is where logic
earns keep"*):

1. **Allowlist-as-data.** `functional/1` is a retractable EDB fact, not code. The
   mutation test proves it is load-bearing (drop it and the Marie decoy fires).
2. **Recursion-through-negation.** `not exception(S,P)` is a default with an
   exception. `test_defeasible_func_…` injects **one** fact —
   `multi_valued("capital","be").` — and the R-FUNC capital finding **non-monotonically
   retracts**, *with no program edit*, while R-NEG and R-NUM stay. This is the
   ADR-amendment-supersession shape; a SQL view cannot express it declaratively.
3. **Minimal-repair / blame.** `logic_repair.lp` is a `#minimize` over a guessed
   `retract/1` set: the smallest set of assertions whose removal restores
   functionality. On the fixture it retracts **exactly one** of the conflicting
   capital pair. Subset-optimization under a constraint is something a SQL view
   **provably cannot rank** (`B-autoharn-fit.md` s.4: clingo's unique claim).

## How it extends

- **More functional predicates / per-subject exceptions** — add `functional/…` or
  `multi_valued/…` EDB facts; no program change, no recompile.
- **Priorities / norm precedence** — the `03-asp.md` AUTH pattern (defaults-with-
  exceptions + integrity constraints) drops straight onto this EDB.
- **R-NUM magnitude** — swap the disequality for `clingcon` integer constraints or
  the Z3 two-bit FDE arithmetic of doc 25 when tolerance/ordering becomes load-bearing.
- **s(CASP) justification trees** — for per-finding PROV/RECORD provenance (a
  justification per query rather than whole-model enumeration), the `03-asp.md`
  bridge.

## The discipline this answers (and its honest ceiling)

The encoding is the *least-reviewed, highest-authority* artifact: a mis-encoded logic
layer fails **silently**, green. `test_contra_asp.py` is the qualification — golden
fixtures + mutation + a differential gate against an independent oracle (ADR-0000 /
INDEP: a check that does not share the producer's bias). Per `B-autoharn-fit.md` s.5
the honest ceiling holds: this certifies a **class** of mis-encoding, once fixtured,
is never seen again — not that unseen inputs are sound. The differential is trustworthy
to exactly the extent the Python oracle is; it surfaces *divergence*, which is where
an encoding bug lives.

---
*References: `docs/research/2026-06-27-obligations-formalisms-survey/formal-systems/`
{`03-asp.md`, `25-paraconsistent-manyvalued.md`, `01-obligation-taxonomy.md`};
`docs/research/2026-06-27-logic-investigation/B-autoharn-fit.md` (N15);
in-repo `docs/adr/` ADR-0000 / 0002 / 0009 / 0012 / 0013.*
