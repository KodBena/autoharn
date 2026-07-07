# Foreclosure-debt back-fill — waiver requests (findings 1, 19, 20)

Status of the ADR-0000 never-again back-fill over every pre-existing `fixed` finding
(WORK-UNIT-foreclosure-debt.md, item 3). The mechanism (db/harness/006, `file_foreclosure.py`,
the two permanent close lines) is built, both-way fixture-proven (`006_foreclosure_debt_fixture.py`),
and the debt is being paid down with **real gates + banked seen-red** — not checkboxes.

## Discharged on real evidence (12 of 15)

Each carries a `class_foreclosure` row pointing at a registered check-line and a committed seen-red
whose sha the `foreclosure_integrity` close line re-verifies every close:

| finding | class | check-line | gate |
|---|---|---|---|
| 24, 30 | undeclared `DROP … CASCADE` | `destructive-ddl-guard` | tools/no_destructive_ddl.py |
| 6, 15 | append-only table missing its guard | `append-only-integrity` | tools/append_only_integrity.py |
| 5, 17, 23 | adapter ↔ oracle divergence | `verify-adapter` | tools/act_stream/verify_adapter.py |
| 18 | Bash-redirection write unaccounted | `bash-write-classification` | tools/act_stream/verify_bash_write.py |
| 9 | ledger-relevance re-includes message_in | `relevant-act-classification` | fact-mining/verify_relevant_act.py |
| 25 | task-notification scanned as operator input | `operator-turn-extraction` | fact-mining/verify_operator_turns.py |
| 12 | could-not-test read as tested-clean | `contemporaneity-degrade` | instruments/verify_contemporaneity_degrade.py |
| 4 | consumers green an empty substrate | `consumer-no-vacuous-pass` | instruments/verify_consumer_no_vacuous.py |

Two of these (`append-only-integrity`, and the destructive-ddl guard before it) were **hazards found in
passing** — no standing check existed for the audit-spine's tamper-evidence; the gate is new, not a
retrofit label.

## RESOLVED — maintainer rulings (2026-07-07)

All three ruled; `foreclosure_debt` is now GREEN (every fixed finding carries a class_foreclosure row),
`foreclosure_integrity` GREEN (13 non-waived intact).

- **finding 1 → WAIVED** (foreclosure id 15): per the recommended text — the authentic-attestation fence
  is a per-kernel control verified at arm-time (arm_*.sh §C); the instantiation checklist is the
  recurring never-again.
- **finding 19 → WAIVED** (foreclosure id 16): per the recommended text — the ephemera-persistence
  discipline is the recurring control; a per-finding existence-gate declined as a Goodhart checkbox.
  **Additionally**, an intent finding was filed (**finding 34**, `banked-report-ephemera-unlinked`,
  OPEN) for a *future* referential-integrity close line: every banked report citing a session id must
  have matching in-repo persisted ephemera — a real gate over the citation↔ephemera join, not a
  checkbox.
- **finding 20 → NOT waived; refiled as a foreclosure** (foreclosure id 17): option (b) taken — the
  mapping to `consumer-no-vacuous-pass` is exact (finding 20 is the lab-target instance of "a real
  close refuses a dry/empty substrate"). The class stays under mechanical watch.

The original request text is retained below for the record.

## The remaining 3 — waiver requested (a maintainer ruling, per the hybrid)

These three have **no honest standing code-gate** to point a seen-red at. Their recurring control is a
process/ADR-level discipline, not a mechanical line. The hybrid requires a maintainer `ruling_ref` to
waive — I cannot forge one, and I will not build a thin existence-gate to clear the view (the Goodhart
failure the work-unit header names). Each below states the class, why no code-gate fits, and the
recommended ruling text. File with `file_foreclosure.py waive --finding N --actor human:maintainer
--ruling "<acts.ruling id / message loc>"`.

### finding 1 — attestation-slot "reserved and untouched" asserted without verification
- **Fix of record:** e14 authentic-attestation fence + preview-mode deletion (experiment-specific).
- **Why no code-gate:** the fence lives in the e14 *kernel* substrate, which is ephemeral and
  per-experiment; there is no durable repo object to check. The recurring control is the
  **kernel-instantiation checklist** (`arm_*.sh` §C, which already verifies kernel triggers/fences at
  arm-time) — the same place `append-only-integrity`'s kernel-review_detail extension would live.
- **Recommended ruling:** *"Waived. The authentic-attestation fence is a per-kernel control verified at
  arm-time by the instantiation checklist (arm_*.sh §C); no repo-standing gate is appropriate for an
  ephemeral kernel slot. The checklist is the recurring never-again."*

### finding 19 — lab A/B variant evidence was unpersisted
- **Fix of record:** real transcripts copied into `harness/e15-build/lab/sessions/`.
- **Why no code-gate:** the never-again is "empirical evidence is persisted before it is reasoned
  about" — this is exactly the **CLAUDE.md ephemera-persistence discipline** (persist_claude_ephemera),
  an ADR-level standing control, not a per-finding gate. A path-existence gate would be a brittle
  checkbox (Goodhart), not a real catch.
- **Recommended ruling:** *"Waived under the ephemera-persistence discipline (CLAUDE.md 'persist the
  ephemera'); that discipline is the recurring control. A per-finding existence-gate is declined as a
  Goodhart checkbox."*

### finding 20 — lab close pipeline verified only via `--close-dry` (dry-run), not a real close
- **Fix of record:** ran `close_manifest` against `harness.lab`, real output banked.
- **Why no code-gate:** the never-again is "a pipeline is verified against a real target, not a
  dry-run." This is embodied in the **`close`-vs-`readiness` mode split** already foreclosed under
  finding 4 (`consumer-no-vacuous-pass`) — a real close now refuses an empty/dry substrate. Finding 20
  is the lab-target instance of that same guard; it needs no separate gate, but the mapping is a
  maintainer call.
- **Recommended ruling (either):** *(a)* *"Waived — subsumed by `consumer-no-vacuous-pass` (finding 4):
  a real close refuses a dry/empty substrate, which is the finding-20 class."* or *(b)* refile finding
  20 as a `consumer-no-vacuous-pass` foreclosure if you judge the mapping exact.

## Close-line state (after the rulings)

`foreclosure_debt` is **GREEN** — every fixed finding now carries a class_foreclosure row (10 real
foreclosures + finding 20's refile + findings 1/19 waived). `foreclosure_integrity` GREEN (13 non-waived
intact: line registered, seen-red sha matches). `append_only_integrity` GREEN.

Before the rulings it stood RED on `['1','19','20']` — that RED was the mechanism refusing to let anyone
(me included) paper over an unanswered never-again; it cleared only on genuine dispositions (2 waivers
with maintainer ruling_refs + 1 real foreclosure), never a forced checkbox.
