# Code-review findings ledger — schema and roles

<!-- doc-attest-exempt: schema convention note authored 2026-07-27 with the ledger file
it defines (maintainer direction, ledger row records the commission); the +A:B:C loop
runs when this is promoted into user-guide material, not on the convention note.
Removal condition: that promotion, or supersession by a typed-findings mechanism. -->

This file defines `attestations/code-review-findings.jsonl` — the append-only ledger of
defects discovered in CODE by any role, the code-side sibling of
`doc-legibility-attestations.jsonl`. The maintainer directed it 2026-07-27 after the
documentation pre-review's mined checklist proved out: the same move needs a findings
corpus first, and this file is where that corpus accumulates. **Forward-only by his
explicit ruling** — no git-log back-mining; the ledger starts at its creation date,
seeded with the findings of that same day's reviews (still on hand, not excavated).

## Named consumers (per the named-consumer test, ADR-0000's 2026-07-22 anecdote)

1. **The future mining pass**: once the corpus is big enough, one model pass recovers
   the common CODE-flaw classes, producing the code-review pre-review checklist — the
   +A:B:C move applied to code review. Until mined, `class` values are free-form
   descriptive slugs; the mining clusters them empirically, exactly as the doc corpus
   was mined.
2. **Per-role efficiency**: which role discovers what (and what only a gate catches)
   informs where review tokens and new gates are worth buying. This consumer is why
   `discovered_by` is mandatory.

## Record shape (one JSON object per line, append-only)

    {"ts": "<ISO-8601>",
     "commit": "<sha reviewed or built>",
     "surface": "<repo area: kernel|engine|serving|gates|fixtures|bootstrap|docs-adjacent-code|...>",
     "grade": "CRITICAL|MODERATE|MINOR",
     "class": "<free-form descriptive slug until mined>",
     "summary": "<one sentence>",
     "file": "<path[:line] where known>",
     "discovered_by": "<role, see vocabulary>",
     "review_tier": "standard|strengthened|none",
     "disposition": "fixed-at-merge|fixed-in-branch|deferred-filed|accepted-disclosed",
     "refs": "<ledger rows / commits grounding it>"}

## Role vocabulary (`discovered_by`) — the operational roles this project runs

- `builder` — the commissioned implementer (including its own sub-workers).
- `builder-self` — the builder catching its own hazard and confessing it in-report.
- `fresh-context-reviewer` — the adversarial refute-posture reviewer of a commit.
- `attestor-B` — the blind legibility attestor of the ADR-0017 loop (doc-side; appears
  here only when a B round catches a CODE defect in passing).
- `pre-reviewer-A` — the +A:B:C A-side find-and-fix pass.
- `diagnostician` — a read-only investigation commission (triage, verification).
- `verifier` — an independent refute-posture verification of a relayed claim.
- `orchestrator` — the coordinating session (Fable) noticing in passing.
- `maintainer` — the human.
- `gate:<name>` — a MECHANICAL discovery (e.g. `gate:kernel_function_census`). First-
  class deliberately: the mechanical-vs-role split is half of consumer 2's question.

Roles are operational conventions, not kernel objects; the ledger's principal/identity
substrate is a separate, kernel-typed concept
([GLOSSARY.md#principal](../GLOSSARY.md#principal)). A user-guide sidenote documenting
the role vocabulary for adopters is queued (maintainer's "maybe worth an addition",
same ruling) and should cite this section rather than duplicate it.

## Writing discipline

The ORCHESTRATOR transcribes findings at review-close/merge time from the review and
build reports — reviewer contracts are unchanged (their reports already carry
grade/file/evidence; this ledger is the structured shadow of what they state in prose).
A finding a report disclosed but this ledger missed is a transcription gap, not a
hidden defect — the reports and ledger rows stay the evidentiary source; this file is
the MINABLE view. Merge conflicts across worktrees resolve by union (append-only JSONL,
same convention as the sibling ledgers).
