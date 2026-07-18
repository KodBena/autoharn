# 10 — Relevance & Substructural Logics — Fair Trial (first pass)

> Part of the autoharn **logic fair-trials** (the corrected, frontier-creed pass). Coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**. The honest status of every verdict here is **undecided-until-the-experiment-runs** — see [README](README.md) and [AUDIT.md](AUDIT.md).

> **Audit verdict:** `deflated = False` · 3 defect(s) noted · **not rewritten** (the hardening pass was a no-op).
>
> ⚠️ **Mechanical re-check flags this as a possible false-negative**: the auditor marked it `deflated=false`, yet 1 of its own defects cite reducible-only / concession tells.

## Relevance & Substructural Logics — Fair Trial

The bet: dropping structural rules makes two of autoharn's ledger disciplines *structural facts of derivation* rather than per-query conventions — relevance (no weakening) forbids a perf-claim that **uses no evidence**; linear (no contraction) forbids one reading **substantiating more than one claim**. The trial asks whether that buys a defect class a standing SQL `_violations` view cannot, today, in installed SWI-Prolog `library(chr)`.

## Maximal ambition

The frontier claim is a **conservation law over the entire Provenance Ledger**: *substantiation is conserved like charge* — each stored reading can discharge at most one perf-claim, no claim discharges without consuming a reading, and a contradiction between advisories is tagged rather than allowed to "substantiate" everything. Classical tools cannot state this as one invariant. Z3 is monotone and explosive: assert two conflicting advisories and it returns `unsat`, then refuses to reason about the *clean* rows at all — useless as a CI gate over a ledger that is *expected* to carry conflicting findings mid-supersession. SQL is set-based and structural-rule-blind: a `JOIN` *is* contraction (one row feeds many), a `LEFT JOIN` *is* weakening. Substructural logic lets autoharn maintain a single object — a multiset of evidence tokens — under which "every `"12x"` claim is backed by a distinct, actually-consumed reading" is true by the *shape* of the rewrite rule, for all claim shapes at once, not re-litigated per query. That is the ledger's intended physics expressed as inference: evidence is a finite resource, and the gate proves it is neither fabricated (weakening) nor double-spent (contraction).

## The expressiveness gap (precise, not hand-wavy)

I will be exact about where the gap is real and where it is not. **Decidability:** no gain — both the CHR rewrite and the SQL antijoin are decidable and cheap. **Semantics/clarity:** the gap is genuine. SQL's default relational operators *implement contraction and weakening as their normal behavior*. Demonstrated, runnable: two claims `c3,c4` both citing reading `r3`:

```sql
SELECT claim.c FROM claim JOIN reading USING(r);   -- returns BOTH c3 and c4
```

One reading silently substantiated two claims. To get linear behaviour SQL must *opt out* every time — `ROW_NUMBER() OVER (PARTITION BY r)`, antijoins, a `COUNT` side-constraint — and that discipline is invisible in the schema; an LLM-authored query that forgets it passes the gate. The substructural encoding *cannot* express the wrong thing without changing the connective:

```prolog
claim(C, R), reading(R) <=> used(C).   % consume the reading (linear: no contraction)
claim(C, _)             <=> unsubstantiated(C).  % no reading left (relevance: no weakening)
```

Run on the same data (verified in SWI 9.3.31): `used(c3)`, `unsubstantiated(c4)` — exactly one substantiation per reading. **Honest verdict on the gap:** SQL *can* compute any single instance correctly; what it cannot do is make single-use a *standing structural guarantee* that holds across every query without per-query vigilance. That is a clarity/semantics gap, not a power gap — and whether that clarity is load-bearing is precisely what the trial must decide, not assume.

## The falsifiable experiment (the trial)

**Setup.** Take the real Pillar-2 ledger: a `reading` store and a `perf_claim` store whose rows cite a reading id, plus an `advisory` store with two conflicting findings on one subject. Seed three defects: a claim citing no reading (weakening), two claims citing one reading (contraction/double-spend), and a contradictory advisory pair.

**Encoding.** The CHR rules above for substantiation; FDE `CASE` for the advisory pair. The gate question: *is any reading consumed by >1 claim, or any claim unsubstantiated?* — answered by the residual `unsubstantiated/1` constraints in the store.

**Success criterion.** The CHR gate flags `c4` as `unsubstantiated` on the double-spend **and** the naive default `JOIN` gate passes both `c3,c4` — establishing the substructural gate catches a defect class the *idiomatic* SQL gate misses, while FDE keeps evaluating clean rows instead of returning `unsat`.

**KILL CONDITION (non-negotiable).** Retire this logic as a gate if a *single, unmodified* Postgres view —

```sql
CREATE VIEW claim_violations AS
  SELECT c,'double_spend' FROM perf_claim GROUP BY r HAVING count(*)>1
  UNION ALL
  SELECT c,'no_evidence' FROM perf_claim p WHERE NOT EXISTS
    (SELECT 1 FROM reading rd WHERE rd.r=p.r);
```

— catches **every** weakening/contraction defect across **all** claim shapes with no per-claim-type editing and no extra reviewer vigilance. If that view matches CHR's coverage generically, the substructural insight is conceptual-only and SQL is the enforcement. (My current read: the view above already closes most of it; the open question is whether multi-reading / partial-consumption claims expose a shape it cannot express without per-shape rewriting.)

## Neutralizing false authority (verification scaffolding)

The central research problem is sharp and I hit it live: CHR's store is **global across goals** — my second run leaked `used(c1)` into later cases until isolated. An LLM that forgets fresh-store-per-evaluation ships a gate that "proves" stale results. False authority is therefore an engineering target, solved with:

- **Mutation fixtures (the meta-sweep).** Golden ledgers plus *mutants* of the encoding: swap linear `<=>` for kept-`\`, or write `!reading` (reusable). Every mutation must flip at least one fixture fail→pass; a mutation no fixture catches proves the suite — not the logic — is inadequate.
- **Differential check.** Run each ledger through CHR *and* the SQL antijoin reference; the substantiated sets must be identical. Disagreement surfaces the encoding bug instead of trusting either.
- **Bounded model cross-check.** Enumerate all ledgers up to N readings/claims; assert CHR ≡ SQL reference for every one.
- **Back-translation.** Encoding → one English sentence ("each reading substantiates ≤1 claim; an unmatched claim is unsubstantiated") → maintainer reviews the sentence, not the Prolog.
- **Justification-carrying output.** Dump the consumed-resource trace (reading r3 → claim c3) and store it as a Pillar-2 reading-with-provenance `{commit,tree,session_id}` — the proof is itself an auditable, supersedable ledger row, never an unexecuted assertion.

## Verdict: phoenix or ash — and how we'll know

**Undecided-until-trial, leaning phoenix-as-CHR-gate for the single double-spend/no-evidence defect class.** The semantic gap is real and runnable; what is unproven is that it survives a *disciplined* SQL view. The one experiment that settles it: the contraction gate above versus the standing `claim_violations` view, on real multi-reading claim shapes. **Flips to phoenix** if a claim shape exists that the multiset semantics rejects generically but the SQL view can only catch with per-shape rewriting (its structural guarantee then earns the frontier). **Flips to ash** if the view matches coverage with zero per-query vigilance — then the logic is the *explanation* of the ledger's physics and SQL is the enforcement, recorded as a failed-experiment retirement, not a familiarity argument.


---
*Verbatim first-pass output of the fair-trials workflow (run `wwr77eg5b`, claude-opus-4-8[1m]), 2026-06-27. The Witness — preserved un-corrected; read with the audit verdict above.*
