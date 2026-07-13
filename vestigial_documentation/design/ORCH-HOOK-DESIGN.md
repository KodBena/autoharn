# The Guardrails Hook — design (2026-07-02)

Audience: orchestrator

**Status:** Design for maintainer review. No code yet; the first increment is cut at the end.
**Author frame:** this is the project's REAL target (the Gutenberg corpus was the PoC
substrate): a claude-code hook that interrogates an AI collaborator's epistemic state as its
work progresses, against a knowledge base, and proactively supplies the information the
collaborator needs to do the right thing. Purpose-first — the formalisms serve the
interrogation functions, not the other way around.

---

## 1. What the hook is for (the functions, in priority order)

1. **Self-consistency interrogation.** As the collaborator's turns accumulate, extract its
   prose claims and surface *candidate* contradictions against its own earlier claims —
   with grounding (rule + exact source spans + message provenance), never a verdict. The
   rfc2616 run (CONTRADICTION-DEMO.md §4) is the calibrating evidence: real-prose deductions
   are largely defeasible, and shallow extraction (subject collapse, copular `be`) is the
   dominant false-positive source. Therefore v1 output is *adjudicable candidates*, and the
   adjudication surface (experiments/adjudicate) is the consumer of record — the hook is an
   instrument, not a judge.
2. **KB cross-check.** The same claims checked against the durable knowledge base (the
   `mining` schema, and the harness DB's claim-ledger-shaped stores), so a collaborator
   asserting something the KB contradicts — or working in ignorance of something the KB
   knows — gets that surfaced *while the work is in progress*, not at review.
3. **Proactive supply.** The inversion of (2): when the collaborator's current claims touch
   entities/topics the KB holds load-bearing facts about, supply them unprompted. This is
   the function the deontic-primary frame under-served, and it is where the deduction
   engine (Fable's domain, polymorphic over Prolog/ASP/SMT) eventually lives. Deliberately
   LAST in build order: it needs (1)+(2)'s ingest spine and the KB co-design that is
   deferred pending the inventory.

## 2. The shape — a thin per-invocation client over the standing stack

```
Claude Code ──Stop hook──▶ hook_guard.py (per-invocation, time-budgeted)
                              │  cursor (mining.hook_cursor: session → byte offset)
                              ▼
                    transcript_prose (the PROSE Port — exists)
                              ▼
                    nlp_client.pipe_facts (socketless-lean; degrade-not-disappear — exists)
                              ▼                          ▼
                    standing daemons :5599/:5600   mining.* claims (provenance-stamped)
                              ▼
                    interrogation ladder L1/L2 (contra rules; later logic engines)
                              ▼
                    hook JSON out: additionalContext = adjudicable findings + supplied facts
```

Everything below the hook line already exists and is hardened: the PROSE admit-set
(`transcript_prose.py`), per-document isolation on every ingress (commits `d8bf3c9`,
`3d17478`), advertised limits + memory envelope + parse budget on the wire (verified live,
boots `e27c203dd3b1`/`482f6c8d8ff5`). The hook adds ONE new component (`hook_guard.py`) and
one small table (`mining.hook_cursor`).

**Trigger: the Stop hook** (assistant turn end). Right cadence (a turn is the natural claim
unit; PostToolUse is noise), and the transcript is quiescent at that moment. SubagentStop is
explicitly OUT of scope v1 (subagent transcripts are volume without the epistemic-state
payoff, and the ephemera snapshots already capture them for audit).

**Incremental by cursor.** The hook reads only bytes past the per-session cursor, so cost is
proportional to the new turn, not the transcript. Cursor is durable (psql, one row per
session id) — a hook that dies mid-turn re-reads a turn, and ingest is idempotent (see §4),
so the failure mode is re-work, never a hole.

## 3. The hook is itself an ingress — ADR-0016 applied to our own boundary

The hook stands on both sides of a contract, and both sides get the discipline:

- **As a client of the daemons**: it plans against `AdvertisedLimits` (plan_chunks), and a
  refused unit degrades to a counted, logged skip — the discipline is already in the client.
- **As a service to the collaborator** (Rule 4 — this is the boring plumbing where the bar
  slips): the hook must NEVER become the outage. Its failure envelope is declared:
  - **Hard wall-clock budget** (constant, declared, enforced with a deadline carried through
    every stage — the measure_vocab_growth budgeting idiom). Budget exhausted ⇒ emit what is
    finished, cursor advances only past what was ingested, loud `budget_exhausted` marker in
    the hook's own log. Graceful, never "runs forever" (maintainer ruling, 2026-07-02).
  - **Daemons down/not-ready ⇒ typed no-op** within the budget: exit 0, no context injected,
    one loud log line. The guardrail degrades; the collaborator's work proceeds. (Negative
    control in §6.)
  - **Untrusted stdin**: the hook-event JSON is decoded-validated-or-refused at entry
    (translate-and-validate; a malformed event is a logged no-op, never a crash that Claude
    Code surfaces as a hook failure).
  - v1 NEVER blocks or rewrites the collaborator's output (`decision: block` is out of
    scope until the false-positive rate is measured on adjudicated data).

## 4. Storage and the privacy ruling (RULED 2026-07-02 — option (a), durable)

> **Maintainer ruling (2026-07-02):** durable storage approved — "I have nothing to hide
> (though I do try to maintain some boundaries) … for the sake of auditability." The scrub
> boundary (secrets/DSN/token patterns) stays as the "some boundaries" mechanism; the
> publish posture already redacts what needs redacting. The other two proposals (5 s budget;
> findings to `contra.finding` from day one) stand as defaulted-accepted.
> **Sequencing ruling (same date):** before building the hook *shell*, exercise what the
> hook will execute — prove the interrogation payload worthwhile on real transcripts first.

The pre-ruling analysis, kept for the record:

`contra_app.py --ephemeral-claude` is stdout-only **by hard constraint** (secrets/PII
scrubbed, nothing to DB/file). The hook wants the opposite — a durable, growing KB of the
collaborator's claims — and that is a new privacy surface over `~/.claude` content. This is
not mine to default. Options, with my recommendation first:

- **(a) Scrub-at-ingress + store (recommended).** The prose units pass the existing
  secret/PII scrubber class (DSN/IP/token/path patterns, as in `run_ephemeral_claude`)
  before any DB write; claims store scrubbed text + provenance pointers (session id, line
  index, byte span) so the *authoritative* text stays in the transcript and the DB holds
  the derived claim. Enables functions (2)/(3). Ruling needed on: is the scrub allowlist
  sufficient for durable storage on the harness DB?
- **(b) Session-ephemeral KB.** Claims live only for the session (redis :6380 volatile-lru,
  namespaced), findings still surfaced; nothing durable. Function (1) only — (2)/(3) never
  accumulate. Safe, but permanently caps the project at self-consistency.
- **(c) Durable but local-only** (a psql schema that is never in any published snapshot;
  publish posture already redacts). Middle ground; costs an explicit redaction boundary in
  the ephemera/publish tooling.

Ingest idempotency in all options: claim identity = (session_id, line_index, unit_index,
content_hash) — re-reading a turn upserts, never duplicates (the contra.finding idempotency
idiom).

## 4b. Trial-series conclusion (2026-07-02 — three trials, one answer; the shell stays unbuilt)

The worthwhileness sequencing ruling ran its course: baseline trial (222 subagent universes,
1997 findings, 99.8 % noise), delta trial (two cheap levers cut 8×, residue still ~100 %
noise, attribution method validated), main-session substrate test (16 sessions — the
substrate is REAL: resolved hypotheses, corrections, one live human-caught contradiction;
the payload extracted none of it, ~100 % noise AND a measured recall miss — the known-live
contradiction never joined as a claim pair in any arm). Verdict: **L1-as-surface-rules is
not the path.** What the genre actually needs, in evidence order: (1) claim-extraction
quality — typed entities (the GLiNER lever) + quantity-typed R-NUM (98 % of delta residue
was digit-run grabbing); (2) temporal state-change awareness — the R-NEG surplus on main
sessions (4.5× the subagent density) is dominated by "was X, now fixed" narratives, i.e.
belief revision to MODEL, not contradiction to flag; (3) assertion-mood / use-vs-mention;
(4) ingress separation for the user stratum (harness-injected/quoted content pollutes it).
Items (2)+(3) are the logic layer's lane (AGM supersedes-chains, the mood taxonomy — the
maintainer's "must be this → nope, but *this* time I'm sure" chains live here), which makes
the NLP↔logic interface synthesis a PREREQUISITE of the hook's L1, not its L3 luxury. The
hook shell (§2) remains correct as designed and remains unbuilt until the payload earns it.

## 5. The interrogation ladder (time-budgeted depth, shallow-first)

Within the budget the hook climbs as far as it gets, emitting at every rung — the stratified
"spend the budget intelligently" discipline, not all-or-nothing:

- **L0 — ingest.** Prose units → facts → claims stored. No findings. (Always completes;
  it is the spine everything else rides.)
- **L1 — self-consistency candidates.** contra rules (R-FUNC/R-NUM as they stand) over the
  session's claim set. Findings carry rule + grounding + both provenances. Known
  false-positive causes (subject collapse, copular `be`) stay in until adjudication data
  says otherwise — the adjudication widget is where that evidence accumulates.
  **AMENDED after the 2026-07-02 trial + maintainer ruling — universes are ROLE-STRATIFIED,
  never role-excluded.** The trial's baseline mixed user and assistant prose into one
  stream, so instruction-vs-instruction collisions read as collaborator self-contradiction
  (63% of findings touched user-role prose). The ruling: contradictory *user instructions*
  are a first-class diagnostic of their own, so L1 runs three universes per session —
  (a) assistant-self (collaborator consistency), (b) user-instruction consistency (the
  maintainer contradicting his own mandates — surfaced TO the maintainer), and
  (c) cross-role (collaborator claims vs standing instructions — conduct-vs-mandate, the
  purpose statement in miniature; needs the mood work before it is honest). Detection is
  also SEPARATED from presentation: ALL findings are stored (durable, idempotent — finding
  identity = its claim-pair identities, so a persisting contradiction is ONE stored finding
  re-observed, never re-injected per turn); *injection* into the session is gated by a
  salience layer (novelty vs already-stored findings first; embedding-similarity retrieval
  against the KB is the filed second lever — cheap, but it ranks relevance, it cannot
  substitute for the mood/extraction fixes).
- **L2 — KB cross-check.** Same rules, session-claims × durable-KB (gated on the §4 ruling).
- **L3 — engine interrogation.** The defeasible machinery (ASP defaults/exceptions, the FDE
  Z3 lane) over the claim graph. Explicitly DEFERRED to the NLP↔logic interface commissioning
  (inventory-first; the mapping was deliberately killed 2026-07-02) — the hook's contract to
  it is just "a claim set with provenance in, findings with grounding out," which is the
  polymorphic seam the interface work will formalize.

## 6. Witnesses (effect-level, per ADR-0013 Rule 5 / ADR-0011)

1. **Planted-contradiction session**: a fixture transcript with known self-contradictions →
   hook surfaces exactly those candidates in `additionalContext` (the CONTRADICTION-DEMO §3
   idiom, moved to the deployment surface).
2. **Negative control — daemons down**: hook exits 0 within budget, injects nothing, logs
   loudly. (The gate must be seen red: run it once against a live stack to prove it *would*
   have found the plant — then kill the daemons and prove the no-op.)
3. **Budget control**: a pathologically long turn ingests partially, cursor advances only
   past ingested bytes, `budget_exhausted` marked, next invocation resumes losslessly.
4. **Idempotency**: re-running the hook over the same turn changes nothing (claim upsert).
5. **Live soak**: the hook enabled on THIS project's own sessions — the literal thesis,
   dogfooded. (`.claude/` "full of text we might want to test it on" — maintainer.)

## 7. First buildable increment (cut small, ends on the deployment surface)

**Increment 1 = L0 + L1 + witnesses 1/2/4**, option-(b) storage (session-ephemeral redis)
so it ships before the §4 ruling, with the storage seam typed so (a)/(c) is a backend swap,
not a redesign. Explicitly out: L2/L3, SubagentStop, any blocking disposition, GLiNER (its
entity quality feeds L1 precision later; it is a swap behind the same extraction seam).

Open maintainer rulings collected: §4 privacy (blocking for increment 2, not 1); hook budget
constant (proposal: 5s wall-clock, the empirically-warm stack serves a turn's prose in
well under 1s); whether findings also land in `contra.finding` for the adjudication widget
from day one (proposal: yes, it is the consumer of record).
