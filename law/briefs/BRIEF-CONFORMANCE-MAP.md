# BRIEF conformance map — the apparatus against the safety-critical-logging standard

**Standing document (AC9, link-24 marriage increment 1). Updated by increments.** Maps the
apparatus's honest status against the invariants (I1–I12) and register (G/F items) of
[the safety-critical-logging BRIEF](safety-critical-logging/BRIEF.md) (its §2 defines
I1–I12; §3 defines the G/F register). This is the I12 self-disclosure the NRC hand-off
needs, and the spine that later increments extend. (Path corrected 2026-07-11: the map was
written against the source project's tree and carried its `experiments/fact-mining/...`
path; the BRIEF lives here, one directory down.)

Status vocabulary (closed): **mechanized** (a gate fires on the machine-observable trigger) ·
**instrumented-retrospective** (an instrument computes it at close, validated against known
facts) · **built-unexercised** (the mechanism exists but has never fired in anger) ·
**review-only** (enforced by human/consult judgment, no oracle) · **open** (not modeled).

<a id="the-j-boundary--the-limit-of-what-gap-detection-can-promise"></a>**The J-boundary — the limit of what gap-detection can promise.** The
[BRIEF](safety-critical-logging/BRIEF.md) (§3 preamble) sorts every logging trigger into two
kinds. **M — machine-observable**: a tool call, a file write, a status change; the harness can
see these fire, so "trigger fired but no entry exists" is a mechanically detectable defect.
**J — judgment-triggered**: the obliging event happens only in an agent's head — noticing a
hazard (G10), recognizing an assumption (F2), an HMI decision (G15), the waiver branch of F11.
For J entries there is no oracle that the trigger fired at all, so a missing entry is invisible
to gap-detection; they are backstopped by the independent check (G7) and the mother's-life
clause instead. "J-boundary" names that line between the absences a machine can detect and the
ones it cannot. Rows below marked **(J)** carry this caveat.

## The invariants (BRIEF §2)

| Inv | Property | Status | Where / basis |
|---|---|---|---|
| I1 | Contemporaneity | **DOWNGRADED 2026-07-11: mechanized at the write boundary only; VIOLATED in witnessed practice** | `ts` NOT NULL is INSERT time, not event time — runs 5, 7, and 8 all show systematic burst-backfill (rows 0.02s apart describing minutes of prior work; BACKLOG "Contemporaneity indictment", 2026-07-11). The prior "mechanized" here was the same half-fixed overclaim CAPABILITIES carried. Substrate for real detection landed same day (s23 per-invocation stamp token + hook invocation journal); the correlation/audit instrument (design/CONTEMPORANEITY-AUDIT.md Part 2) is **open**. Until it lands, I1 conformance is claimed at the write boundary and explicitly NOT at the conduct level. |
| I2 | Attributability — humans *and tools* | **mechanized (subject rows: actor + write-time stamp, e17-live) · mechanized (apparatus tools)** | subject: NOT NULL `actor` PLUS the interception stamp (e17) — a PreToolUse hook binds every ledger row to its ACTUAL invocation identity (session_id+agent_id, HMAC-verified against an apparatus-owned secret the subject role cannot read), injected at write time, not typed by the writer; so `actor` is no longer a value the writer alone controls (finding 31 closed). Apparatus tools: every marriage solver run banks a DerivationRecord {engine+version, config, EDB/program/output hashes} (F6/I8). Subject-side BUILD-tool provenance (the tools the subject uses to construct its artifact, distinct from the ledger-write identity) remains a **declared exclusion — reason:** no hook intercepts the subject's build commands, only its ledger writes; I8 subject-tool qualification is unbuilt. |
| I3 | Immutability / non-destructive correction | **mechanized + EXERCISED (subject, e17)** | append-only ledger; `supersedes`/`amends` are new linked rows. Now backed by the **append_only_integrity** close line (a standing check that every audit-spine table refuses UPDATE/DELETE every close) and, on the rulings spine, acts.ruling's append-only trigger. **e17 exercised both correction tracks organically:** `supersedes` (17→12, replacing the refused stub) and `amends` (14→2, one clause of the parse decision) — both id-is-order-clean, unprompted |
| I4 | Completeness incl. negatives | **mechanized + EXERCISED (subject, e17)** | the closed verdict vocabulary: a non-run is QUARANTINED and turns the run red, never dropped; `close_manifest` accounting. **e17 negatives visible:** the two refused inserts are id-is-order gaps (row 15 and the refused-detail stub row 12), not silent drops; the refuse-and-teach event landed a visibly-defective stub rather than nothing; on the rulings spine, **delivery_freight_integrity** + the **delivers-FK** (Inc8) make a freight-less or byte-mismatched delivery a visible RED |
| I5 | Bidirectional traceability, gap-visible | **instrumented-retrospective + EXERCISED (subject, e17)** | five typed edges id-pinned; `alias_surface`/orphan flags; the **delivers-FK** formally keys each acts.ruling delivery to the freight it carries (byte-identity trigger). **e17 exercised** `answers` (8→9 question-round-trip), `amends` (14→2), `supersedes` (17→12) organically — the richest kernel-vocabulary edge exercise in the series |
| I6 | Independence recorded separately | **mechanized + EXERCISED live (subject, e17) · mechanized (apparatus)** | subject: the F53 stamp-distinctness gate makes a review's `independence` claim true-or-refused AT WRITE TIME — a `technical`/`managerial`/`financial` claim requires the review to be written by a stamp-distinct invocation, else REFUSED-and-TAUGHT (self-review is the honest default). **EXERCISED at e17:** the subject's inflated claim was refused live (row 12 stub), the record self-repaired with a genuinely-distinct reviewer (rows 17/18, stamp `a8d15e15`) — the first live positives of a reviewer writing its own rows (`self_performed(17,18)`, all rows `stamp_verified=t`). Apparatus: the differential's two independent producers + the DTO SoD gate |
| I7 | Assumption/environment model with validity bounds | **built-unexercised (bounds) · subject now authors assumptions (e17)** | an `assumes` edge + `valid_until`/`valid_within` bounds + the ASP expiry closure (scratch-exercised). **e17: the subject authored `assumption` rows organically** (rows 4,5,6,7 — output-path, file-selection, line-handling, duplicate-column) — the `assumption` kind is now subject-exercised. But the VALIDITY BOUNDS remain **built-unexercised subject-side — reason:** no subject has authored a `valid_until`/`valid_within`-bounded assumption; e17's were plain assumptions without a validity horizon (the task had no time/environment bound to declare) |
| I8 | Tool qualification / provenance | **newly mechanized for the apparatus's own tools (scoped)** | the DerivationRecord pins {engine id + version + config + EDB/program/output hashes} to every marriage derivation; a verdict without both records is NO RESULT. Scoped honestly to the *engine layer's* tools; subject-side tool provenance **open** |
| I9 | Discharge-status honesty | **mechanized (this increment)** | the closed verdict set {AGREE, DIVERGE_BY_DESIGN, DIVERGE_DEFECT, QUARANTINED} — never a boolean, never silence; QUARANTINED/DIVERGE_DEFECT exit non-zero. The DTO attestation gate distinguishes *attested* from *pending* from *SoD-violation* |
| I10 | Rationale — the why, not just the artifact | **instrumented-retrospective / review-only** | `rationale` column; the WHY-ledger (R-WHY) precedent; DTO decompositions carry an author + attestation rationale |
| I11 | Endurance & availability (re-runnable) | **newly mechanized (this increment)** | the marriage retains the EDB + programs + atom outputs + derivation records under `experiments/fact-mining/docs/ledger-marriage/derivations/` (F16 — the actual programs stored, so the derivation is re-runnable, not asserted) |
| I12 | Scope self-disclosure | **mechanized at the substrate + at close (through e17)** | the per-target **capability manifest** (declared exclusions, never a silent empty). Extended by the **finding-36 substrate resolution**: a close resolves its db/schema/fenced-dir/session-dir from the `ledger_target` SSOT, and an UNREGISTERED substrate goes REQUIRED-ABSENT (RED), never a vacuous pass; the **gate-journal-registered** arm-time check (Inc11, finding 42) refuses arming a target whose contemporaneity registration is missing — closing the e17 gap where a skipped arming step silently rendered a mandatory line N/A |

## The register items this increment moves

| Item | BRIEF | Before | After this increment |
|---|---|---|---|
| **F6** Tool qualification & provenance | §3.2 | open — the engine layer would trust clingo/z3 without a pinned version | **mechanized (apparatus scope):** every solver run banks {engine+version, config, hashes}; a verdict without its two records is NO RESULT |
| **F16** Proof-artifact retention | §3.2 | partial — witness stack, but engine artifacts had no retention rule | **mechanized:** EDB + programs + outputs + records retained under versioned storage |
| **F2 / I7** Assumptions with validity bounds | §3.2 | open — `kind='assumption'` exists, no bounds structure | **built-unexercised:** `assumes` + bounds + expiry closure (scratch-exercised) |
| **I9** Discharge-status honesty | §2 | boolean/silent differential posture | **mechanized:** closed verdict vocabulary, quarantine-turns-red |
| **I12** Scope self-disclosure | §2 | perimeter named in consults, not the record | **mechanized at substrate:** capability manifest declared exclusions |
| **F53 / I2 / I6** Independence-attestation, subject-side | §2, §3.2 | subject `actor` self-controlled; independence a free-text claim (e16 row-7 fabrication) | **mechanized + EXERCISED (e17):** interception stamps bind each row to its true invocation (HMAC, write-time); the stamp-distinctness gate refuses+teaches an unearned independence claim; live at e17 (row 12 refused, rows 17/18 genuine SoD). Ratified laws F52/F53 (acts.ruling 28/29) |
| **F35 / I4 / I5** Ruling-spine delivery integrity | §2 | delivery↔freight held by byte-coincidence + prose | **mechanized:** `delivery_freight_integrity` close line + `delivers`-FK byte-identity trigger (row 26→25 back-filled) |
| **G7 / I6** Independent check on subject work | §3.1 | open — no subject had run an independent review | **exercised (e17) + mechanization built:** a genuinely-independent reviewer (stamp-distinct `a8d15e15`) caught a real defect (28-digit `Decimal` ceiling) the author's own verification passed; the **`review_fixpoint`** close line (Inc11 — stamp-distinct + first-contact + zero-undisposed) mechanizes the criterion and **arms e18** (gates nothing yet) |

**Honest scoping (not overclaimed) — through e17.** The e17 gains are real and subject-side: subject
row-attributability (I2) and independence-recording (I6) moved from "self-declared / built-unexercised"
to **mechanized AND exercised live** (interception stamps + the F53 refuse-and-teach gate; rows 12/17/18
are the banked specimen). G7 (independent check on subject work) is **exercised once** — one genuinely
independent review caught a real author-missed defect — with the `review_fixpoint` criterion built to
mechanize it for e18. These are N=1 specimens, not rates (consult-27-FRAME); one run is a proof of
mechanism, not a distribution.

**Every remaining item is a DECLARED EXCLUSION with its reason — no silently-open row:**
- **I8 subject build-tool provenance** — *reason:* the stamps intercept the subject's ledger WRITES, not
  the tools it builds with; a subject-tool qualification model is unbuilt (distinct from the mechanized
  engine-layer DerivationRecord).
- **I7 validity bounds, subject-side** — *reason:* the `assumes`+bounds+expiry mechanism exists and is
  scratch-exercised, but no subject has authored a time/environment-bounded assumption (no task has
  posed one).
- **G3 hazard classification / severity taxonomy** — *reason:* `kind='finding'` exists, but no severity
  vocabulary or classification gate; no subject task has posed a hazard-severity decision to model.
- **G13 competence / qualification of subject agents** — *reason:* out of scope until a multi-agent
  competence question is the lever; the stamps identify *who* wrote a row, not their qualification.
- **F14 WCET / timing guarantees** — *reason:* a decision-ledger apparatus makes no real-time claim;
  timing is out of the BRIEF surface this instrument targets.
- **(J) G10 noticed-hazard · F2 recognized-assumption · G15 HMI · F11 waiver branch** — **J-boundary**:
  judgment-triggered, no oracle that the trigger fired; backstopped by G7 (now exercised) and the
  mother's-life clause, per the J-boundary note above.

## Increment note, 2026-07-11 (worlds/runs era — post s20/s21/s22/s23, runs 5-8)

Movements since the e17-era rows above, stated compactly; the rows above are edited only
where they had become overclaims (I1):

- **I1** downgraded as marked in its row — the material correction of this increment.
- **I2/I6 strengthened and re-witnessed:** s21 (session,agent)-pair distinctness live-refused
  an inflated claim (run 5) and attested genuine independence both directions (runs 7/8);
  cross-session stamping live-witnessed (run 8, distinct stamp_session on resumed rows).
- **I4 at the exit boundary:** the clean-exit Stop gate BLOCK path live-witnessed (run 8) —
  an open work item cannot be silently walked away from. CAVEAT, witnessed same night: the
  gate is only as complete as the ledger — run 7's un-ledgered phase 2 made its clean Stop
  vacuously green (BACKLOG run-8 forensics). Intake totality (preamble point 1, full-
  commission decomposition) is the counterpart discipline; its mechanized half is open.
- **I7 subject-side:** run 8 authored 14 plain assumption rows organically (8 author-side,
  6 reviewer-filed via the antecedent audit, which caught a real arithmetic error) —
  the KIND is now well-exercised; validity BOUNDS remain built-unexercised, unchanged.
- **G7:** second live exercise (run 8's reviewer, mechanically-distinct stamps).
- **New M-trigger coverage since the map was written:** permit-to-work (write ⇒ open+claimed
  work item), delegation observer (subagent dispatch journaled + warned), stop-disposition
  warning (a stop without its `stopping:` row is taught), mutation observer (post-hoc bash
  writes), matcherless stamping (every Bash invocation). Each observer-grade item warns and
  journals rather than refuses; each has banked seen-red both polarities.
- **J-boundary motion:** design/ARTIFACT-VS-REQUIREMENTS-DETECTOR.md proposes converting the
  J-entries' silent-absence into an explicit total disposition (Register 1) plus an
  out-of-frame classifier (Register 2, costed, default off) — design filed, unbuilt.

This map states its own boundary rather than letting a partial read as whole.
