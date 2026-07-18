subject: c3301e5
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

Three commits landed together as one operator-visible arc: the model watchdog and the
`./otel-attest` verb (`e2ce003`, `a1d745f`, `c3301e5`) and the model-defeat pipeline
(`fcc7744`, `45b7524`). Read together, they are the answer to "if a session's serving model
gets silently substituted, how would I ever know, and what happens to what it wrote?" Specs:
[design/FABLE-OTEL-SENTRY-SPEC.md](../design/FABLE-OTEL-SENTRY-SPEC.md) (including its dated
A1/A2 amendments) and
[design/FABLE-DEFEAT-PIPELINE-SPEC.md](../design/FABLE-DEFEAT-PIPELINE-SPEC.md) (including its
dated A1 amendment).

## The watchdog beeps in real time

A small always-on process (`otel-watch`, per the sentry spec §3) tails the local OTel
collector's export and compares each request's observed `model` against the session's declared
expected model; on a mismatch it fires the operator's existing mail-notification script — the
same one that already makes the maintainer's phone beep on every turn completion — so a
substitution surfaces within seconds, not at the next audit. It writes nothing to the ledger and
registers no principal: this is notification, not evidence. A session with no declared
expectation is reported as *unwatched*, loudly, so silence is never mistaken for "watched and
clean." **This verb's build was not exercised for this note** — the delivered arc's witnessed
legs are `./otel-attest` and the engine-side defeat pipeline; the watchdog's own witness plan
(sentry spec §14, items W1–W5) is UNWITNESSED here.

## `./otel-attest` writes post-hoc attestations, graded

`./otel-attest` is a batch verb, not a daemon: it reads the collector's export and a world's
ledger, both read-only, and writes one defeasible `verification` row per attributable ledger
row, naming which model actually served it. Every attestation is written at one of **four
closed confidence grades**, each naming the strength of the join that earned it (sentry spec
§6):

- **`exact-command`** — the row's own `led` invocation is tied to one specific, bracketing
  `api_request` event.
- **`turn-bracketed`** — command-level detail is unavailable, but every non-utility request in
  the row's turn window agrees on one model.
- **`session-scoped`** — bracketing is ambiguous, but every non-utility request in the whole
  session's covering window still names one model.
- **`ambiguous`** — the window shows more than one non-utility model, or a load-bearing join
  failed. **As of the sentry spec's A1 amendment (2026-07-18, adjudication ledger row 1505),
  an `ambiguous` attestation always writes `model=unresolved`** — a fixed sentinel, never a
  fabricated single model and never an invented multi-model packing of the field. The
  conflicting models are named instead in the row's `basis=` field. The verdict is decided by
  what the ambiguity still proves: if every candidate model in the window contradicts the
  declared expectation, that is still `verdict=MISMATCH` (the culprit is unclear, but the
  substitution is not); if at least one candidate matches, nothing is proven and the verdict is
  `unevaluated`; an ambiguous row is never written `match` — ambiguity cannot clear a row.
  Two carve-outs from the spec's A1 addendum close the rule's edge cases: an **empty**
  candidate set (ambiguity via join failure, no non-utility `api_request` in evidence at all)
  is `unevaluated`, never a vacuous MISMATCH-over-nothing (absence of telemetry proves
  nothing); and `expected=undeclared` is likewise `unevaluated` — with no declared
  expectation there is nothing to contradict.

No attestation is written at all when no correlated telemetry exists for a row — absence of
events is never treated as evidence of anything, in either direction.

**Why this needed a fix pass before it shipped.** The first build of `./otel-attest` was
adversarially reviewed (ledger row 1505) and found to silently fold every `ambiguous` case into
the write-nothing path — directly contradicting the spec's own "never silently upgraded, never
silently dropped" rule for exactly the case the spec calls "the substitution-relevant case par
excellence." The verb was held out of service until the fix landed (commit `c3301e5`); it is
back in service now, with the `model=unresolved` behavior above as the fixed shape, and with
write-time field hygiene added (a `|` or newline inside an unauthenticated model string used to
be able to corrupt the row's later parse — it now refuses at write time instead, per the
sentry spec's A2 amendment).

## A MISMATCH or ambiguous attestation surfaces as a finding row

Every attestation whose verdict is `MISMATCH` — and, per the A1 amendment above, every
`ambiguous` attestation whose verdict resolves to `MISMATCH` — additionally writes a companion
`finding` ledger row, so it surfaces in ordinary review flow instead of hiding in attestation
bulk. (An ambiguous row whose verdict is `MISMATCH` writes exactly one finding, not two.)

## `./judge --layer defeat` derives credit, and QUARANTINEs loudly on a pre-s41 world

The defeat pipeline (`fcc7744`, review-fixed by `45b7524` per adjudication ledger row 1506) is
the machinery that turns a MISMATCH attestation into a consequence: a ledger row backed by an
unsuperseded mismatch attestation, written by a principal holding an unsuperseded, active
competence grant for `model-identity-attestation`, is excluded from the `credited` reading —
computed fresh on every derivation pass by two independent producers (a SQL twin and an ASP
program) required to agree bit-for-bit. Nothing is edited, nothing is deleted; a defeated row
stays fully visible in raw history and in an explicit history view, always shown with its
cause (which attestation, which grant).

**This machinery needs typed competence grants (s41) to exist at all, and the current live
world predates s41.** Run read-only, against this repository's own live world, today
(2026-07-18):

```
$ ./judge --layer defeat
```
```
# marriage differential -- layer='defeat'
#   closed verdict vocabulary: ['AGREE', 'DIVERGE_BY_DESIGN', 'DIVERGE_DEFECT', 'QUARANTINED']; RED = ['DIVERGE_DEFECT', 'QUARANTINED']

  [!! ] autoharn1 QUARANTINED        asp=0 sql=0 atoms; Δasp=[] Δsql=[]
          asp QUARANTINED: EDB export failed: CapabilityError: target 'autoharn1' did not emit trust_grant/n (capability absent): no principal_binding_active/principal_competence_activity columns on this schema (pre-s41 lineage) -- capability absent, not record-empty. A silent empty here would be the F49 vacuous-pass; refusing loudly.
          sql QUARANTINED: EDB export failed: CapabilityError: target 'autoharn1' did not emit trust_grant/n (capability absent): no principal_binding_active/principal_competence_activity columns on this schema (pre-s41 lineage) -- capability absent, not record-empty. A silent empty here would be the F49 vacuous-pass; refusing loudly.

# DIFFERENTIAL RED -- a target diverged/quarantined (NO RESULT)
```

**This is the correct, disclosed shape, not a bug.** Both producers refuse loudly with the same
named reason instead of silently reading an empty derivation as "nothing defeated" — the
class of mistake the defeat spec calls the F49 vacuous-pass, foreclosed on purpose. A world
whose birth chain carries s41 or later derives real results; this world does not, and the
pipeline says so instead of guessing. Standing (suspended/revoked) is deliberately never a
defeat input — a suspended or revoked principal's *past* attestations, under a still-in-force
grant, keep defeating exactly as before (ledger row 1481's ratified rule, restated in
[orchlog.d/s45-standing-lifecycle.md](s45-standing-lifecycle.md)).

## Honest limits, carried forward

- **The ceiling, permanently:** nothing here authenticates which model actually served a
  request. Every layer — the watchdog, the attestation grades, the defeat pipeline — is
  AU-family audit-supporting evidence over an unauthenticated OTel stream, never IA-2
  authentication. A dishonest or silent session is observed as nothing and defeats nothing;
  absence proves nothing, permanently.
- **The watchdog fails silent** on its own death or a mail failure; a `--heartbeat` option is
  the operator's opt-in against that, not a default.
- **The typed kernel form (s44) and its credited-read views (a future `s46-credited-views.sql`
  in the defeat-pipeline sense — a different, later delta from the standing-lifecycle s45 named
  above) are authored but not yet in any birth chain**; until an s44+ world exists, the engine
  floor above is the only credited computation, and `./otel-attest`'s rows are ordinary
  `verification` rows outside the s42 hash chain's full coverage in a pre-s42 world.
- **A malformed attestation row is a denial-of-derivation until corrected**: the defeat
  pipeline's parsers refuse loudly on a malformed `v1` attestation rather than skip it, which is
  deliberate (fail loud beats skip silent) but means one bad row halts derivation for its whole
  target until superseded.
