# WORK-ITEM LAYER — decision memo (deliberately NOT a spec)

Audience: orchestrator

Status: DESIGN MEMO, Fable-authored (session be693afb, 2026-07-09). This maps the decision
space and names a leading candidate; it does NOT freeze a schema. The shape must be informed
by run-2/run-3 evidence (what agents actually do when decomposing under governance), and the
standing instruction holds: **do not let anyone freeze this early** — a work-item schema
frozen before the runs is a guess wearing a spec's clothes. Whoever picks this up: gather the
evidence listed at the end, then write the spec under whatever authoring regime is then in
force (CLAUDE.md ORCHESTRATION).

## The gap this fills (witnessed, not hypothetical)

Three observations from the toy pilot created this item:
1. The maintainer's direct question — "is my task automatically tracked, or is it a manual
   chore?" — currently answers: manual chore. The ledger records ACTS (enacts/answers/
   supersedes/...), not WORK STATE; "what is open and who is on it" is reconstructible only
   by reading the ledger like a historian.
2. Run 1's drift: a completion claim with nothing committed. The conformance instrument
   (design/CONFORMANCE-INSTRUMENT.md) now catches claim/artifact mismatch per commission —
   but a commission is per-dispatch; nothing tracks work across dispatches.
3. AUTOMATION-ENVELOPE.md names "work-item layer" as gap 2 of 7: hierarchical decomposition
   needs somewhere for the hierarchy to live that is not a chat transcript.

## The two donors

**Donor A — omega work-status** (`/home/bork/w/omega/tools/work-status/schema.sql`, read
2026-07-09; re-observe before citing, per checklist item 6). Proven shapes worth stealing:
- The state-shape CHECK: `open ⇒ disposition, no resolution; closed ⇒ resolution + close
  date, no disposition`. This is the type answer to "what states exist" — one within-row
  invariant, unrepresentable illegal states.
- `shipped-without-ship-ref` violation: a `shipped` resolution without a pr/commit/worklog
  ref is a violation ROW. This is run 1's uncommitted-deliverable lesson, independently
  evolved in another repo — convergent design is strong evidence the invariant is real.
- Recursive-CTE cycle detection over deps/parents as a violations VIEW (fail-loud, CI-gated).
- Closed-but-amendable enums as CHECK lists; amendment is a deliberate edit, never coercion.

**Donor B — this repo's own vocabulary**: the ledger's typed edges (enacts, answers,
supersedes, regards, evidence), countersign_obligation/review_gap (obligation tracking
already exists for ONE kind of work — reviews), and the commission instrument's scope items
(item_id + mandate + witness_type — a work item at dispatch granularity, already ratified).

## Decision axis 1 — storage locus (the load-bearing choice)

**(1) Acts in the ledger, state derived.** Work-item events (opened, claimed, decomposed-
into, closed-with-resolution) are ledger rows with typed edges; "current state" is a VIEW
(latest act per item), exactly the ledger_current pattern. Pros: one SSOT (ADR-0012 P1), the
append-only trail IS the audit (omega needed a hand-rolled audit_log; the ledger gets it for
free), obligations/countersigns compose directly (a work item can carry a review obligation
with no new machinery). Cons: kernel lineage change (new edge types or a discipline for
`regards`), and the kernel is the most ceremony-guarded surface in the project.

**(2) Sibling mutable store, omega-style.** Port items/deps/refs verbatim next to the
kernel schema. Pros: proven DDL, zero kernel change, mutable ergonomics. Cons: a SECOND
source of truth about acts the ledger also sees (the SSOT breach ADR-0012 P1 exists to
refuse); duplicates audit; its "closed" and the ledger's "answered" WILL drift apart
(same-spelling vocabulary drift — the failure catalog's named specimen).

**(3) No storage — a pure view over existing edges.** `pickup` already derives OPEN-
QUESTIONS/REVIEW-DEBT fresh each time. Pros: nothing to freeze. Cons: no deps graph, no
decomposition hierarchy, no tier/label vocabulary — it answers "what is unresolved", not
"what is the work breakdown".

**Leading candidate: (1) with (3) as the read surface** — events in the ledger, status and
violations as derived views, omega's CHECK/violation logic ported into the view layer rather
than into a second table universe. (2) is named here so its rejection is on the record, not
silent. This is a CANDIDATE, not a decision: axis 1 is exactly where run-2 evidence bears.

## Decision axis 2 — one work vocabulary or two

Commission scope items and work items overlap ("a mandated unit with a witness"). If they
stay separate vocabularies, expect drift. Candidate: a commission's scope items ARE work
items at dispatch granularity — the commission instrument writes them, the work-item layer
gives them identity across dispatches (an item UNEXERCISED in commission N is the same item
re-scoped in commission N+1). If this holds, the work-item layer's spec should be written as
an AMENDMENT to the conformance instrument, not a rival.

## Decision axis 3 — the engine's stake (the raison d'être check)

Everything cross-row that omega's violations view computes is ASP-native and richer there:
deps cycles, transitive blocking ("item X is open but everything it depends on is closed —
why is it not in progress?"), obligation propagation (a decomposed item's review obligation
distributing over its children), shipped-without-witness. The SQL-floor differential pattern
applies verbatim: port omega's violations view as the floor, write the .lp layer above it,
run AGREE/DIVERGE. A work-item layer that the engine cannot reason over fails the standing
bar ("without a deductive engine, I might as well rm -rf /") — this axis is a constraint on
axis 1, and it favors candidate (1): ledger-resident events are already in the engine's EDB
reach.

## What ports verbatim, what dies at the door

Ports: the state-shape invariant (as view logic or trigger), shipped-without-ship-ref (as
"closed-without-witness"), cycle detection (to the engine), closed-but-amendable enums.
Dies: audit_log + record_audit + table_asof (the ledger is the audit; a second trail is the
SSOT breach again); `extra jsonb` forward-compat (the ledger's answer to unknown vocabulary
is a typed refusal, not a junk drawer); DROP-and-recreate re-runnability (lineage deltas,
never drops).

## Evidence runs 2/3 must produce before a spec is written

1. Does a governed agent, told to decompose, produce a HIERARCHY (parent/child) or a
   SEQUENCE (deps chain)? The schema differs. (Run-2 prompt already mandates decomposition.)
2. Do obligations want item granularity (countersign per work item) or dispatch granularity
   (per commission)? Watch where review_gap friction actually appears.
3. What does the operator ASK the ledger between sessions? (`pickup`'s access log, informally
   — his real questions are the view's requirements.)
4. Does any state change other than open→closed occur in practice? If disposition churn is
   real, candidate (1)'s event volume is fine; if not, even less schema is needed.
5. Where does the run's commission drift first — that is where item identity across
   dispatches earns its keep, or doesn't.

## Cost note

Candidate (1) touches kernel lineage ⇒ under current rules it is a Fable-authored or
succession-ceremony spec plus scratch witness — the most expensive authoring path in the
project. That cost is real and is a legitimate reason to let the evidence, not enthusiasm,
decide whether the layer is needed at all. Doing nothing remains a admissible outcome: the
four verbs + commissions may prove sufficient for the project's actual scale.
