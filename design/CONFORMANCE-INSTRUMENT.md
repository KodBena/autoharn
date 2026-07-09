# COMMISSION/CONFORMANCE INSTRUMENT — schema + acceptance criteria (Fable, 2026-07-09)

Status: DESIGN, Fable-authored schema per OPUS-READINESS move 4 ("Fable reviews its schema,
Sonnet builds it"). Ratified in principle with OPUS-READINESS (assent batch item 3,
2026-07-09). Sonnet builds the checker from this; the schema itself changes only under the
succession ceremony.

## What it is

ADR-0013 Rule 1 names the missing mechanism: "a structured commission/result-conformance
record — a checklist the result is mechanically diffed against." This instrument is that
record pair plus the differ. It converts the two failure modes the record proves —
executor narrowing (Specimen 2; Opus's known mode) and claim-without-artifact (run 1's
"task complete" with nothing committed) — from maintainer discoveries into gate refusals.

## The two artifacts

**Commission** (written BEFORE work starts; committed; the ratified scope):
```json
{
  "commission_id": "<slug>",
  "date": "<ISO>",
  "ratifier": "<who approved the scope>",
  "executor": "<model/agent tier commissioned>",
  "scope": [
    {
      "item_id": "<slug>",
      "mandate": "<one sentence, imperative>",
      "witness_type": "commit | file | ledger_row | gate_output | db_state | doc_excerpt",
      "witness_hint": "<where the evidence must appear, e.g. repo path or table>"
    }
  ],
  "out_of_scope": ["<named exclusions — silence is not exclusion>"],
  "constraints": ["<hard rules: no push, no kernel SQL, ...>"],
  "escalation": ["<typed events that end execution and route upward>"]
}
```

**Conformance report** (written by the executor at completion; the claim):
```json
{
  "commission_id": "<must match>",
  "verdicts": [
    {
      "item_id": "<must match a scope item>",
      "verdict": "WITNESSED | REFUSED_AS_EXPECTED | UNEXERCISED",
      "witness": "<commit hash / path / ledger row id / verbatim output excerpt>",
      "blocker": "<REQUIRED iff UNEXERCISED: the concrete blocker, and where it was filed>"
    }
  ],
  "extras": ["<anything delivered OUTSIDE scope — self-declared over-scope>"],
  "renegotiations": ["<scope changes requested mid-run and WHO ratified each>"]
}
```

## The checker's rules (mechanical, each one a refusal with a teaching message)

1. **Coverage**: every commission scope item has exactly one verdict. A missing item is the
   narrowing tell — refuse with the item named. An umbrella verdict over N items is N
   unverifiable claims — the item_id join makes it unrepresentable.
2. **Witness presence and type**: every WITNESSED/REFUSED verdict carries a witness matching
   the commissioned witness_type; the checker VERIFIES what it can mechanically (a commit
   hash exists in the named repo; a file exists at the path; a ledger row id exists — read
   directly, per checklist item 5) and marks the rest OPERATOR-CHECK with the exact command
   to run. A verdict whose witness fails verification is treated as no claim (ADR-0013
   2026-07-02 amendment, part 2).
3. **UNEXERCISED honesty**: requires a blocker AND a filing pointer (BACKLOG/findings). An
   unexercised item with neither is a silent gap — refuse.
4. **Scope symmetry**: extras are flagged for the ratifier (over-scope is the mirror failure,
   ADR-0013 What-it-does-NOT-mean); renegotiations must name their ratifier — "renegotiated"
   with no ratifying act is self-authorization — refuse.
5. **Completion**: the report may claim done iff every item is WITNESSED/REFUSED_AS_EXPECTED
   or honestly UNEXERCISED-and-filed. The checker's verdict vocabulary is closed:
   CONFORMANT / CONFORMANT_WITH_DEFERRALS / NONCONFORMANT(reasons[]).

## Acceptance criteria for the checker build (Sonnet-executable)

- Pure stdlib, top-level imports; loud refusals with the failing item named and the fix
  stated (the deny→teach house style); exit 0/1/2 = conformant/with-deferrals/nonconformant.
- **Seen-red fixtures shipped with it** (both-polarity discipline), including AT MINIMUM:
  (a) the run-1 drift shape — a scope item claiming WITNESSED with a witness commit that
  does not exist (the uncommitted-deliverable case) → NONCONFORMANT;
  (b) a missing item_id (narrowing) → NONCONFORMANT;
  (c) an UNEXERCISED without blocker → NONCONFORMANT;
  (d) the honest case → CONFORMANT; (e) honest deferral → CONFORMANT_WITH_DEFERRALS.
- A tiny authoring helper or template for commissions, so writing one costs minutes — an
  instrument too expensive to invoke is one that gets skipped (the census lesson).
- Wired as an OBSERVER first (a `judge`-style verb or a gate in observe mode per the
  apparatus.json assurance field); promotion to enforcing is a maintainer act.

## Boundaries, honestly named

The checker verifies claim/artifact CORRESPONDENCE, not artifact QUALITY (review does that)
and not effect-level acceptance (ADR-0013's amendment part 1 — the deployed-effect step
stays an owner's act). It also cannot verify witness_types it can't reach (a db_state
witness when the checker has no connection) — those emit OPERATOR-CHECK lines, never silent
passes (the F49 lesson: "(none)" must be provably distinct from "did not run").
