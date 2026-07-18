# ORCH-CONSULT-REFUSAL-RECORDING-2026-07-17 — banked verbatim consultation record
<!-- doc-attest-exempt: point-in-time consultation record, banked verbatim per ADR-0018 practice -->

What this is: the complete, unedited output of an out-of-frame, fresh-context Fable
consultation on reserved decisions (e)/(f) of design/FABLE-PRINCIPAL-IDENTITY-SPEC.md
(durable recording of refused write attempts), commissioned by the maintainer 2026-07-17
after objecting, correctly and on independent technical grounds, to the CLI-side logging
candidate a prior orchestration pass (during an infrastructure outage) had recommended.
ADR-0018 brief: the problem, the evidence (including the maintainer's own objection,
carried as evidence to verify rather than defer to), the LAW — no candidate answer
front-loaded beyond the artifacts already in dispute. Banked verbatim; nothing below the
rule is edited. Its recommendation awaits maintainer ratification; nothing in it is
implemented by virtue of being banked.

---

# Fresh-context consultation: reserved decision (e) — durable recording of refused write attempts

Consultant: Fable (fresh context, no session state). Read in full before writing: CLAUDE.md; ADR-0000 (incl. the 2026-07-02 Rule 2(a) amendment), ADR-0011, ADR-0012, ADR-0013, ADR-0017, ADR-0018; `design/FABLE-PRINCIPAL-IDENTITY-SPEC.md` (§9(e) and its whole body); `judgment/engine/engine-panel/refute-architecture.md` (flaw 1 read directly, plus its SALVAGE section); `design/ORCH-PGAUDIT-EXPLORATION.md`; `design/ORCH-CONSULT-PRINCIPAL-SURFACE-2026-07-18.md` §1.1/§1.5 and its source list; ledger rows 1410–1414 read via `./led show`, verbatim. Live host probed read-only (witnessed outputs quoted below). No file was edited.

A note on posture, per ADR-0018: this commission necessarily hands me the failed candidates as *evidence* (they are the witnessed problem), and the commission's own question is whether that candidate set is too narrow. I treated A, B, and pgAudit as artifacts to be re-derived against, not as a menu, and derived the design space independently before comparing.

---

## 1. Is the A/B dichotomy too narrow? Yes — and the maintainer's objection is correct on independent technical grounds, not deference

**Confidence: high.**

The maintainer's stated diagnosis — a recording apparatus in the client script "can easily be circumvented just by modifying the script, providing no standards-compliant guarantee" — is not merely reasonable; it is a restatement of the oldest formal requirement in this field. NIST SP 800-53 carries it as a named control: [AC-25 (Reference Monitor)](https://csf.tools/reference/nist-sp-800-53/r4/ac/ac-25/) requires that a policy-enforcement mechanism be **tamperproof, always invoked, and small enough to analyze** — and "always invoked" exists precisely because a mechanism an adversary can route around enforces nothing. The same logic extends to audit *generation*: an audit record produced anywhere other than the enforcement point inherits the bypassability of that other place. Candidate (B) put the enforcement in the kernel and the recording in the client — splitting one security function across two trust boundaries, so the conjunction has the *weaker* boundary. Row 1413's analysis (an adversary who avoids `led` is refused but leaves zero trace, which is strictly worse than nothing on the probing-detection axis because it manufactures false confidence) is correct as written; I verified the reasoning rather than the authority, and it holds. That the original recommendation "struck the maintainer as odd" is fair: (B) was never a weaker version of the right answer — it was a category error about where the recording obligation lives.

The dichotomy is too narrow in exactly the way ADR-0000's amended Rule 2(a) predicts: **the class was named at the scope of the mechanisms already in hand.** A and B are both answers to the question "how does a write survive the rollback of the transaction it happens inside," varied along one axis (kernel-side loopback vs client-side second connection). But that question conflates two independent axes and silently forecloses a third option on a fourth:

- **Axis 1 — where capture executes** (trust boundary): client tool / kernel trigger / database engine facility / host OS. A and B sit at two points; the engine's own non-transactional facilities (server log, WAL, sequences) were absent from the enumeration, and one of them is *already running on the maintainer's host* (§3).
- **Axis 2 — what grade the record has**: ledger-grade (append-only, hash-chained, stamped, queryable — AU-9-protected in the project's own idiom) vs diagnostic-grade (the project's action-stream ruling's "diagnostics" tier). A and B both implicitly targeted ledger-grade and both failed; nobody asked whether the standards actually require ledger-grade for refusals (they do not — §3), or whether a two-tier answer is legitimate.
- **Axis 3 — whether the rollback is a fixed constraint at all.** "The recording must survive the refusal's own rollback" presumes the refusal must be an exception that aborts the enclosing transaction. That presumption is itself a design choice, and the project's own LAW argues against it: ADR-0012 P9 rule 5, in the compiled register, holds that *failure is a typed return value, never a throw* — precisely because a throw is an untyped control-flow escape whose effects (here: the destruction of the evidence of the attempt) are not part of any signature. The SQL `RAISE EXCEPTION` is the throw; §4's candidate E is the `std::expected`.

So: the dichotomy is too narrow on the artifacts alone, before any standards research — and the standards research (§3) then confirms which of the wider space the requirement actually points at.

---

## 2. Verification of the prior refutations (each checked, not inherited)

**Confidence: high.**

**(B), CLI-side:** refuted correctly, per §1. One sharpening the record does not yet contain: (B) is not even a valid *diagnostic-tier* answer, because a diagnostic that is systematically absent exactly for adversarial traffic is not a diagnostic of the thing it claims to observe — it is a selection bias with a log format.

**(A), dblink loopback:** the refute-architecture flaw 1 objections were re-checked one by one against the live host and stock Postgres semantics:

- *Undeclared new dependency* — holds, softened one notch: witnessed via `pg_available_extensions`, `dblink` and `postgres_fdw` **ship with this host's Postgres 18.4 build but are not installed** (`dblink|1.2|` with empty `installed_version`). So it is an install-and-declare, not a package hunt. Still a new trusted component inside the kernel's most safety-critical code path.
- *A connection per refusal on a latency-budgeted path* — holds. A loopback connection re-authenticates through pg_hba, consumes a connection slot, and its cost and failure modes (slot exhaustion under a probing burst — note that an adversarial flood of refusals is exactly the load profile this feature exists for) are borne at the worst possible moment. An adversary who can trigger refusals can now also exhaust connection slots *through* the refusal path: the recording mechanism becomes a denial amplifier.
- *Failure semantics* — holds, and row 1414's correction of the earlier "no silent-failure surface" overclaim is right: on double failure the hardened form degrades to today's stderr-only behavior. The completeness dilemma (journal write fails → refuse anyway → completeness gone; or → accept the write → fail-open, unthinkable here) is structural to any *remote-ish* second channel, because the second channel's failure is independent of the first's health.

Two independent refutations, generations apart, plus this third: **(A) stays retracted.** But note what flaw 1 also demanded, which the A/B framing dropped: *"the journal is the sole witness to refusals… 'every actual refusal was journaled' has no oracle."* Any successor design owes a **second witness / completeness oracle**, and none of A, B, or pgAudit provides one. §4's candidate F does, natively.

---

## 3. What the standards actually require for refused/denied attempts — and at what grade

**Confidence: high on the control landscape; medium on any specific clause wording (paraphrase-grade, consistent with the banked consult's own honesty note).**

The banked consult's §1.1 surveyed AU-10 (non-repudiation) for the identity surface. Extending it for *this* question, the commission's instinct is right that refusals live in a **different control family** than accepted acts:

- **Denied-attempt logging is an explicit, mainstream, first-class requirement — not an exotic extrapolation.** [AU-2 (Event Logging)](https://csf.tools/reference/nist-sp-800-53/r5/au/au-2/) names *failed logons and failed accesses* among its canonical event types; [AC-7](https://csf.tools/reference/nist-sp-800-53/r5/ac/ac-7/) is an entire control about unsuccessful logon attempts (limit, record, respond); [PCI DSS Req. 10 / 10.2.1.4](https://pcidssguide.com/pci-dss-requirement-10/) mandates audit-logging of *all invalid logical access attempts* precisely because probing precedes compromise ([KirkpatrickPrice on 10.2.4](https://kirkpatrickprice.com/video/pci-requirement-10-2-4-invalid-logical-access-attempts/)). A revoked principal attempting a write is this event class exactly — the failed-login analogue in §9(e) is the standards-correct framing.
- **But the required grade is audit-log grade, not non-repudiation grade.** AU-10's non-repudiation machinery (signatures, producer/reviewer identity binding) attaches to *accepted, authority-carrying acts* — approvals, releases, records. No control I found requires cryptographic non-repudiation of a *refused* attempt; what AU-9 (protection of audit information) requires is that the audit trail of such events be protected against tampering and reviewed. The asymmetry makes sense from first principles: an accepted act creates authority and needs to be unforgeable *by its author*; a refusal record is evidence *about* an adversary, who never authenticates the record anyway. The requirement's spine for refusals is: **generated always (AC-25's "always invoked" applied to audit generation), protected reasonably (AU-9), reviewed (AU-6)** — with completeness mattering more than signature strength, because the attack this control detects is the one that leaves *no* accepted record to sign.
- Consequence for the design space: a solution may legitimately be **two-tier** — capture at the enforcement point (non-negotiable), durability at whichever grade the maintainer's NRC-grade-product bar wants, with the grade *named* (the STANDARDS-REGISTRY / named-exclusion posture, ADR-0000 Revisit #4 Clause 1).

---

## 4. The real design space, enumerated, with honest trust boundaries

**Confidence: high on mechanisms C, E, F (verified against the live host or stock semantics); medium on D (host prerequisites witnessed absent).**

### C — The server log, which is already recording every refusal on this host today

The most consequential finding of this consultation is a witnessed fact, not a design: **the premise "today that refusal is loud exactly once, to stderr, then gone forever" is false at the server.** Probed read-only on the live host (2026-07-17):

```
log_min_error_statement = error      (the stock default)
logging_collector       = on
log_line_prefix         = %m [%p] role=%u db=%d from=%r app=%a
```

Stock PostgreSQL, at default settings, writes **every ERROR-level failure — including a `RAISE EXCEPTION` from a BEFORE INSERT trigger — to the durable server log, together with the full offending STATEMENT text**, prefixed here with timestamp, role, database, client address, and application name. This fires for `led`-issued and raw-`psql` writes identically, because it fires in the engine, below every client. It is not part of the transactional system, so rollback cannot un-write it. The durable record §9(e) asks for *already exists at diagnostic grade*, for every refusal the kernel has ever issued on this host, unless rotation has aged it out.

Notes on this candidate, honestly:

- **pgAudit is not the mechanism for this case, and the pgAudit lead should be re-pointed at core logging.** pgAudit's own documentation routes the errored-statement case to the standard logging facility (statements in aborted transactions are outside its session-logging guarantee; the [pgAudit README](https://github.com/pgaudit/pgaudit) is explicit that its logging is best-effort and non-transactional, and whether the *failing* DML statement itself gets a pgAudit session entry is UNVERIFIED by me — and immaterial, because core logging demonstrably covers it). pgAudit's genuine value remains what `ORCH-PGAUDIT-EXPLORATION.md` said: audit-of-*reads*. For refusals it adds an install, a restart, and no capture that `log_min_error_statement` isn't already doing. Keep it deferred.
- **Kernel-side authorship of the record's content is available cheaply**: the triggers' `RAISE EXCEPTION` can carry a structured `DETAIL`/`ERRCODE` payload (attempted actor, refusal class, target kind), so the log line's content is authored *by the enforcement point* — "always invoked" holds for generation. A batch ingester (a scripted verb, per the self-application rule) parses refusal lines into ledger rows on its own schedule.
- **Trust boundary, stated without flattery**: the log is a host file writable by root and the postgres OS user; the database superuser can lower `log_min_error_statement` or a session can `SET log_min_error_statement = panic` — actually no: it is superuser/`ALTER SYSTEM`-scoped, not ordinary-user-settable (SUSET), so an ordinary writing role **cannot** suppress its own refusal's log line; only the superuser/host owner can. Rotation ages it out (retention on this host UNVERIFIED). No hash chain, no truncation witness. Against the client-controlling adversary (the maintainer's stated threat): **sound**. Against the OS/superuser adversary: no better than the s26 header's already-disclosed bound — and the ledger itself carries the same superuser disclosure in §8. Against the well-meaning developer editing the wrong file: immune (there is no file to edit; it is engine behavior).
- Ingestion lag creates a window where the refusal is durable but not yet queryable; the record's grade is diagnostics-tier per the project's own action-stream ruling, and must be *classified* as such, exactly as the pgAudit exploration prescribed for reads.

### E — Dissolve the rollback: the write boundary becomes a typed-verdict function, and a refusal becomes an ordinary committed ledger event

This is the structurally different move the commission asked about, and it is the one ADR-0000 Rule 2(a) points at when the class is named properly. The class is not "records that survive rollback"; it is *"a refusal whose only witness is destroyed by the refusal's own mechanism."* The foreclosing type: **make the refusal a value, not an abort.**

Mechanics (all stock PL/pgSQL, verified semantics, no extension):

1. `REVOKE INSERT ON kernel.ledger FROM` the writing roles; the sole sanctioned write path becomes a kernel function/procedure (`SECURITY DEFINER`, with `set_actor`'s resolution reading `session_user` rather than `current_user` — a named, necessary adjustment).
2. Inside it, the real INSERT runs within a `BEGIN … EXCEPTION WHEN OTHERS …` block. A PL/pgSQL exception block is an in-process subtransaction: when any BEFORE-trigger refusal fires — *all* existing refusal triggers, caught generically, no enumeration — the guarded INSERT rolls back to its implicit savepoint, and the handler then INSERTs a `write_refused` meta-event (attempted actor, errcode, refusal message, a typed digest of the payload) as an ordinary ledger row, then **returns a typed refusal verdict instead of re-raising**. The enclosing transaction commits, carrying the refusal event and nothing else.
3. The refusal event is an ordinary ledger row: it inherits the hash chain, stamps, append-only triggers, countersignability, queryability — **ledger-grade for free**, by exactly the §2 argument the spec itself makes for why identity events live in the ledger ("inherit all of it for free"). No second record machinery, no second trust boundary.
4. The CLI renders the typed verdict as today's teach-text and a nonzero exit; a raw-`psql` caller invoking the function receives the verdict row — the teaching survives, in content rather than in SQLSTATE. (A variant using a procedure with internal `COMMIT` before a genuine re-`RAISE` can preserve the real-ERROR ergonomics; it constrains callers to autocommit contexts and is a spec-time choice, not a blocker.)
5. The bypass path does not exist: a raw INSERT is refused at the privilege layer before any semantics run. That privilege refusal is not semantically taught and not kernel-journaled — but it *is* captured by C (an ERROR with statement text in the server log), which is the correct residual home for it: the two candidates compose rather than compete.

Against the three standing objections that killed A: no new dependency (pure in-core PL/pgSQL); no per-refusal connection (an in-process savepoint, microseconds, no slot consumption — the denial-amplifier failure mode of A does not exist); failure semantics clean and fail-safe (if the journal INSERT itself fails, the whole transaction aborts loudly — the refusal still refuses, the loss is loud, and the failure surface is the same in-process storage engine the ledger itself lives on, not an independent channel that can be independently sick). And flaw 1's "sole witness, no oracle" objection is answerable here (see F).

Costs, named without discount: this is a real restructuring of the kernel's client-facing write surface — its own Fable-authored, maintainer-ratified spec and delta family, emphatically **not** class-ratified fail-safe (it changes how every write enters the system). Named design obligations it must discharge: the s40 deferred constraint trigger (§3.3 anchor coupling) fires at COMMIT, outside any handler's scope — the write function must `SET CONSTRAINTS ALL IMMEDIATE` within the guarded block (or the ceremony verbs must be composite) so commit-time refusals are also caught; multi-statement transactional ceremonies (registration = anchor + event) become composite kernel calls; `session_user`-based actor resolution must be re-witnessed against the s18 zero-SELECT deployment class. None of these looks structurally hard; all of them are why this is a spec, not a patch.

Two adversarial properties of E that the spec's "low volume, high audit value" assumption must be re-examined against (deliberately unresolved, §6): a probing adversary now *writes to the append-only ledger at will* (journal flooding — volume, and hash-chain growth, under adversarial control), and a refused payload's content enters the permanent record unvetted (poison-payload/privacy: store a typed digest, not the verbatim attempt — a design decision to make explicitly).

### F — The refusal-counter sequence: a native completeness oracle

PostgreSQL sequences are non-transactional by design: `nextval()` survives the rollback of the calling transaction. A dedicated `kernel.refusal_seq`, bumped by the refusal path immediately before refusing (in E's handler, or even in today's triggers immediately before `RAISE`), yields a durable, monotone, in-database *count* of refusals that no rollback erases — zero dependency, zero connection, effectively zero latency. It carries no payload, so it is not a record; it is the **second witness** flaw 1 demanded: reconciliation ("journal rows + log-ingested rows = sequence value") converts "every refusal was journaled" from an unfalsifiable claim into a checkable one. The project has already met this mechanism unawares — the burned-id gaps the panel history and the refute document both remark on are exactly this physics, currently observed as an accident rather than employed as an instrument.

### D — WAL-level capture (`pg_logical_emit_message`, non-transactional), named and ranked down for this host

Postgres does have a primitive genuinely closer to an autonomous durable write than dblink: `pg_logical_emit_message(transactional := false, …)` writes a structured message into the WAL immediately, decodable regardless of the enclosing transaction's fate — in-process, no connection, in core since 9.6. It is the honest answer to the commission's "does Postgres offer anything closer" question. But consuming it requires `wal_level = logical` (witnessed: this host runs `replica`; changing it is a restart), a logical replication slot (an operational footgun: an unconsumed slot retains WAL without bound), and an out-of-process consumer; and `test_decoding` did not appear in this host's shipped extensions (witnessed absent from `pg_available_extensions`). Capture-side it dominates A; deployment-side, on this host, it is a heavier install than either C (already on) or E (pure SQL). Ranked: legitimate, not first.

### Rejected members, for completeness

Client-side anything (B) — refuted, §1/§2. `SAVEPOINT` — wiped, as the spec says. `LISTEN/NOTIFY` — **verified unusable**: notifications are transactional and are discarded on rollback; a refused transaction's NOTIFY never fires. Temp-table staging — transactional, rolls back. Background-worker extensions (`pg_background` et al.) — dblink's dependency objection again. Logical decoding of the refused row itself — nothing to decode: a BEFORE-trigger refusal means the heap tuple never existed.

---

## 5. Recommendation (ranked; no single candidate discharges every tier alone)

**Confidence: high on the ranking's reasoning; the choice among honest tiers is genuinely the maintainer's.**

1. **Ratified end state: E** — refusal-as-typed-verdict at a privilege-enforced kernel write boundary, refusal events as ordinary ledger rows. It is the only candidate that is simultaneously always-invoked (AC-25's spirit), ledger-grade (AU-9 by inheritance rather than by new machinery), dependency-free, and connection-free — and it is the kernel's own idiom applied to itself: s40/s41 turned identity facts into append-only attributed events; E does the same for the one event class the kernel currently destroys. It also happens to be the LAW's own shape: ADR-0012 P9 rule 5's failure-as-typed-value, P2's boundary-that-refuses-what-it-cannot-honor, ADR-0000's class foreclosed by a type rather than guarded by a channel. It requires its own spec; it should not be bolted into s40/s41's ratification.
2. **Immediately, at near-zero cost: arm and classify C, and add F.** C is *already capturing* every refusal on this host; what is missing is only (a) the maintainer's awareness that it is (this consultation's witnessed finding), (b) a stated retention posture, (c) optional structured `DETAIL` in the kernel's RAISE calls (a small, arguably class-ratifiable additive delta) and a scripted batch-ingest verb, and (d) the explicit *diagnostics-tier* classification the pgAudit exploration already prescribed, so it never masquerades as the guarantee. F is a one-sequence additive delta that gives whichever journal exists its completeness oracle. C+F together plausibly satisfy the *letter* of AU-2/AC-7/PCI-shaped denied-attempt logging; E is what matches the project's own NRC-grade bar and the reference-monitor spirit.
3. **A stays retracted; B stays refuted; pgAudit stays deferred** (it is the reads tool, not the refusals tool — the §9(e) lead should be corrected to point at core `log_min_error_statement`, not pgAudit); **D stays named** as the fallback if E's restructure is ever judged too invasive and ledger-grade capture is still wanted without it.

The decision this leaves the maintainer is clean: *which tier does (e) require?* If diagnostics-grade capture reviewed on demand is enough (the standards' letter), C+F is nearly free and mostly already running. If the refusal record must sit inside the same tamper-evidence perimeter as the ledger (the project's product bar), E is the design, and it is worth its own spec cycle.

---

## 6. Deliberately not resolved, named

- **E's full semantics**: deferred-trigger capture via `SET CONSTRAINTS ALL IMMEDIATE` vs composite ceremony verbs; procedure-with-COMMIT vs function-returning-verdict (ERROR ergonomics vs transactional flexibility); `session_user` resolution under the s18 zero-SELECT deployment class. Spec-level work, not consult-level.
- **Journal flooding and poison payloads under E**: an adversary's refused attempts become durable ledger writes — rate/volume posture, digest-vs-verbatim payload storage, and what "append-only" means for a record class an adversary can grow, are open and load-bearing.
- **Whether pgAudit session-mode emits its own entry for the failing DML statement itself**: UNVERIFIED (its README routes the case to standard logging; core coverage makes the question immaterial to the recommendation, but a witness test would settle it).
- **This host's log retention/rotation settings** (only `logging_collector=on` and the prefix were probed): whether historical refusals are still on disk today is UNVERIFIED.
- **Anchoring the server log's own integrity** (shipping log segments through the GPG external-custody route, as the pgAudit exploration floated): possible upgrade path for C's grade; not designed here.
- **Whether refusal events should be countersignable/reviewable like other ledger rows under E** (AU-6's review half): named, not designed.

Sources (standards research this session): [AC-25 Reference Monitor — CSF Tools](https://csf.tools/reference/nist-sp-800-53/r4/ac/ac-25/) · [NIST glossary: reference monitor](https://csrc.nist.gov/glossary/term/reference_monitor) · [AU-2 Event Logging — CSF Tools](https://csf.tools/reference/nist-sp-800-53/r5/au/au-2/) · [AC-7 Unsuccessful Logon Attempts — CSF Tools](https://csf.tools/reference/nist-sp-800-53/r5/ac/ac-7/) · [PCI DSS Requirement 10 — PCI DSS Guide](https://pcidssguide.com/pci-dss-requirement-10/) · [PCI Req. 10.2.4 — KirkpatrickPrice](https://kirkpatrickprice.com/video/pci-requirement-10-2-4-invalid-logical-access-attempts/) · [pgAudit README — GitHub](https://github.com/pgaudit/pgaudit). Host probes: read-only `SHOW`/catalog SELECTs against the DSN in deployment.json, outputs quoted verbatim above.
