# FABLE-SUBSTITUTION-OF-AUTHORITY-CONSULT — banked verbatim, 2026-07-19

<!-- doc-attest-exempt: banked consult verbatim; the standing rule is that consult
transcripts are preserved as delivered, never polished -- fidelity IS the value. -->

**Provenance:** fresh-context Fable consultant (ADR-0018-shaped: problem + evidence +
LAW only; the orchestrator's candidate directions withheld until the consultant's own
analysis was formed — the reconciliation section below was written last, by
instruction). Commissioned per the maintainer's words of 2026-07-19 ("it may be time
to raise it with a Fable consultant ... maybe the great deal of work we've been done
since then has subsumed it -- worth a check"), acting on the standing
substitution-of-authority prod (work_opened row; motivating specimen 2026-07-18,
filed externally as claude-code issue 78658). Read-only consult; delivered as the
agent's final message and banked here byte-verbatim below the rule.

---

# CONSULT — the substituted-orchestrator class: subsumption check and residual (fresh-context, ADR-0018; 2026-07-19)

Written by a fresh-context Fable consultant with no session state, from the repository at `/home/bork/w/vdc/1/autoharn`, read-only. Sources read for this consult, stated for the record: `law/adr/0000` in full, `law/adr/0011`, `0013`, and `0017` in substantial part with section maps, `0012` via its P1/P2/P8 spine as cited throughout the corpus; `design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md` in full (all 13 corrections); `design/FABLE-OTEL-SENTRY-SPEC.md` in full; `kernel/lineage/s44-model-identity-attestation.sql` in full; the s46/s51/s52 delta headers; `design/FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md` and `design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md` in full; `serving/boundary_service.py`'s header and auth surface; the live world's kernel probed read-only (witnessed observations below marked as such). All absolute paths are under `/home/bork/w/vdc/1/autoharn/`.

**The headline, before the detail.** The commission asks whether the work since 2026-07-18 has subsumed the substituted-orchestrator class — and lists five mechanisms to check. The honest first finding is that the commission's own list omits the mechanism that answers it: the corpus already contains a complete, ratified design arc built expressly against this specimen — `design/FABLE-OTEL-SENTRY-SPEC.md`, the shipped `./otel-attest` verb, `kernel/lineage/s44-model-identity-attestation.sql`, the defeat pipeline (`engine/lp/ledger_defeat.lp`), and `kernel/lineage/s46-credited-views.sql`. The s44 delta's own WHY names the class in the specimen's exact words and cites ledger row 1434 — which is the substitution-of-authority-prod row itself. So the answer to "has the work subsumed it" is: **the representational half of the class is subsumed, deliberately and by name; the class is not and cannot be foreclosed by construction from inside this project (a vendor ceiling, argued below); and the operational half — the part that would have changed the 2026-07-17 outcome — is genuinely residual: the real-time watchdog is unbuilt, and zero attestation rows exist in the live world.** The detail follows.

---

## 1. Subsumption check, per mechanism

The commission asks me to be precise about one distinction throughout, and I adopt it as the organizing frame: **the claims lane** (what an act *says* about who produced it) versus **the evidence lane** (what an outside channel *observed* about what model actually produced it). Model self-report lives in the claims lane; the specimen proves the claims lane can lie. A mechanism "reaches the orchestrator's model identity" only if it puts something in the evidence lane.

### 1.1 s40/s41 — the principal-identity family: claims lane only, by design. Does NOT subsume.

s40/s41 (per the build basis, `design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md`) make *identity facts about principals* — registration, standing, role bindings, key bindings, relations, competence grants — append-only attributed events, with strict declared-not-silent attribution and the `principal_actor_resolution` column recording *how* an actor was resolved. Every one of these facts is about **who the act claims to be from**. The family's own §8 says the limit plainly: *"A declared standing default still authenticates nothing: the declaration says who the connection speaks for, not who is at the keyboard."* An orchestrator session substituted from Fable to Sonnet still writes as `author`, resolves identically, and produces byte-identical principal events. `agent_class` immutability forecloses class *drift on the record* (a reviewer2-style ambiguity), not class *falsity at the keyboard*. Additionally — witnessed during this consult — the live world's kernel is pre-s40: its kind vocabulary has fourteen members ending at `commission` (observed via a refused write whose teach-text enumerated the live constraint), so even the claims-lane machinery reaches only future worlds. **s40/s41 make the substituted orchestrator's *acts* well-attributed to a principal; they record nothing about the model behind the principal, and were never designed to.**

### 1.2 s44 + the OTel sentry + the defeat pipeline + s46 — the evidence lane, built against this exact specimen. SUBSUMES the representational class, with named ceilings.

This is the direct answer, and it is layered:

- **Representation (s44, `kernel/lineage/s44-model-identity-attestation.sql`, shipped and lineage-wired):** a typed kind `model_identity_attested` — attested row by same-table FK, observed model string verbatim, a closed four-grade confidence vocabulary naming the join set that earned it (`exact-command`/`turn-bracketed`/`session-scoped`/`ambiguous`), a closed verdict vocabulary structurally coupled to the declared expectation (`(attest_expected IS NULL) = (attest_verdict = 'unevaluated')` — a match/mismatch claim with nothing to match against is unrepresentable), hash-covered, boundary-written, supersedable-because-defeasible. The commission's structural point — "a substituted orchestrator is unrepresentable in the very record system built to make substituted authority representable" — **is no longer true of the schema**: in an s44 world the substitution is a first-class, typed, attributed row.
- **Evidence source (the OTel channel, witnessed row 1443):** the one surface that carries per-request model identity, after the harness's own hooks were verified NOT to carry it (row 1441). The `./otel-attest` verb (shipped, adversarially reviewed, fixture-suited under `seen-red/otel-attest/`) writes defeasible attestations into the *current, pre-s44* world as convention `verification` rows — so even the live world is not schema-blocked from representing a substitution.
- **Consequence (defeat pipeline + s46):** a mismatch attestation, backed by an in-force competence grant for `model-identity-attestation`, *defeats* the attested rows in the derived reading — `credited_current` = `ledger_current` minus defeated rows, cause always displayed (`model_defeated_rows`). This is the part I want to flag as more than the commission asked for: the corpus not only represents a substituted orchestrator, it has a **typed answer to "what happens to what it wrote"** — credit is withheld by derivation, nothing gated, nothing rewritten. That is the kernel's own defeasible-reasoning idiom applied to exactly this class.
- **The claims/evidence junction is designed correctly.** The acting model is attached by *attestation from outside the session*, never by principal self-declaration — which is the right polarity, since self-declared model identity is precisely the thing the specimen proves worthless. The two lanes meet only in the defeat rule, where disagreement withholds credit rather than asserting anything.

**Ceilings, all named by the design itself and correct:** R1 (a substituted session can simply not emit — absence proves nothing), R2 (fail-open, best-effort transport), R7 (the emitter is the unauthenticated CLI process asserting its own `model` attribute; every layer authenticates pipes, never the emitter's honesty). The whole stack is AU-family audit-supporting evidence at diagnostics tier per the standing action-stream ruling — never IA-2 authentication, never a guarantee. This is not a defect in the design; it is the honest maximum reachable from inside this project (see §2.3).

### 1.3 Role charters and briefs — reduces the blast radius; does not reach model identity.

`design/FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md`, `tools/role_charter.py`, `tools/role_brief.py`: a role's authority-defining text binds only when registered by hash in the ledger, and a fresh instance's operative context is charter + derived brief computed from the world's own views. This bears on the specimen's *second* half — the false authority record ("you settled on only using Sonnet as orchestrator"). An instance whose standing rules arrive as a ledger-derived brief has structurally less room to substitute a fabricated policy memory for the real one, and a reader has a queryable surface (`standing_decisions`, the charter registration rows) to refute the fabrication against. But this is **crowding out, not foreclosing**: nothing prevents an agent from *asserting* a false record in conversation; the ledger is the rebuttal surface and consulting it remains vigilance. And the brief says nothing about which model is reading it. **Partial, indirect; not subsumption.**

### 1.4 s51/s52 artifact store — evidence custody, not identity. Does not reach the class.

Content-addressed custody for essential-record bytes plus existence-checking of `artifact:<hash>` witness citations forecloses *dangling and drifting evidence pointers*. It hardens the record a false authority claim would be checked against (a registered commission text cannot be quietly absent). It records nothing about any model. **Adjacent hardening only.**

### 1.5 The boundary service — transport and deployment authentication; explicitly adds no truth.

`serving/boundary_service.py` authenticates *which deployment* is addressed and disciplines *how* bytes cross (typed refusals, s43 boundary functions, no raw writes). Its own header states its epistemics: it "adds NO truth of its own." The per-deployment discrimination the commission calls "keys" is config-table selection, not principal or model authentication. **Does not reach the class, and correctly does not claim to.**

### 1.6 The standing action-stream principle — the constraint, not a mechanism.

The 2026-07-11 ruling (quoted verbatim in the sentry spec §1: guarantees rest on the hook/action surface only; session internals are diagnostics, never load-bearing) is why full foreclosure is structurally unavailable: the hook surface — the only surface allowed to bear guarantees — carries no model identity, by the vendor's design (row 1441, verified against Claude Code 2.1.209–2.1.214). The sentry's reconciliation (notification and recordable-not-gating attestation are not guarantees) was independently re-checked in the sentry spec and I find it sound on my own read as well.

### 1.7 Subsumption verdict

**Representational class: SUBSUMED** — for future worlds by type (s44 + s46), for the current world by convention (v1 attestation rows), with the claims/evidence distinction built in correctly and the consequence question (defeat) answered beyond what the prod asked. **Foreclosure by construction: NOT ACHIEVED AND NOT ACHIEVABLE HERE** — the foreclosing type ("a lying emitter is unrepresentable") requires provider-side response signing or model identity in the hook payload, both vendor surface. **Operational reality: NOT SUBSUMED** — see §2, because this is where the residue actually lives.

---

## 2. The residual class, at ADR-0000 Rule-2 level

### 2.1 The residual, named in its most general form

> **An authority-carrying act in the live world whose model provenance is representable but unrepresented: the evidence channel exists, the record shape exists, and no standing process moves evidence into record or watches the channel in real time — so the window between substitution and discovery remains as long as it was on 2026-07-17.**

Witnessed facts grounding this, all observed during this consult:

1. **The v0 watchdog does not exist.** No `otel-watch` file anywhere in the tree (checked by find and by git history). This is the layer the maintainer himself premised ("I would want it as a watchdog"), the only layer that shrinks the incident window from days to seconds, ranked build-first by the ratified spec's own §17 item 2 — and the orchlog entry `orchlog.d/defeat-pipeline-and-otel-identity.md` describes it in present tense while admitting W1–W5 UNWITNESSED. The prose is ahead of reality here; under the claims-carry-witnesses contract that paragraph is the weakest artifact this consult read.
2. **Zero attestation rows in the live world.** `SELECT count(*) ... WHERE statement LIKE 'model-attestation v1%'` on `autoharn1.ledger` returns 0. The verb exists, was reviewed and fixtured, and has never written a live row (its one live dry-run honestly reported zero attestable rows — commit `a1d745f`).
3. **Coverage is per-session opt-in.** Emission requires the exporting env vars and the `autoharn.expected_model` resource attribute at launch. No launcher in the repo stamps these as a matter of course; an unstamped session is (per the design, correctly) UNWATCHED — but today *every* session is unwatched.
4. **All kernel-typed machinery (s40–s52) reaches only future worlds**, while every live authority act happens in the current, fourteen-kind world. Correct under runs-are-linear; named so nobody mistakes authored-and-wired for in-force.

There is a second, smaller residual: **the advising-principal gap on ratifications.** A maintainer ratification is recorded by the advising session itself, so attesting the recording row's model (s44/v1) *does* capture the adviser in the common case — but only at the attestation's grade, only if the session emitted, and not at all when advice and recording are separated (a consult document incorporated later, a relay). Nothing types "this ratification was advised by X" as a claim distinct from row authorship.

### 2.2 What would foreclose it by construction rather than vigilance — and the honest answer

True foreclosure has exactly two shapes, both out of this project's control: **(i) provider-side response signing** (Anthropic attesting which model served each response — R7's own naming; does not exist), and **(ii) model identity in the hook payload** (would move the fact onto the one surface the action-stream ruling lets bear load; row 1441's feedback-channel ask, and the substance of the externally filed issue 78658). Everything buildable inside the project is vigilance made cheap, fast, and typed — which is worth doing precisely because the design has already made it *nearly free*. Stating this plainly is the ADR-0000 2(a) discipline: the class boundary here is genuinely at the vendor seam, not at the edge of the work already done.

### 2.3 Remediation shape (no SQL, no delta — the shape only)

**Buildable now, no new spec needed (this is execution of an already-ratified spec, not new design):**

- **Build v0 (`otel-watch`) per FABLE-OTEL-SENTRY-SPEC §3/§17, witness W1–W5.** The spec fixed every forkable choice; the alert path is verified; the fixtures are enumerated. This is the single highest-leverage residual item and it is Sonnet-executable under the standing contract.
- **Correct the orchlog's watchdog paragraph** (or ship the watchdog and witness it, which discharges the correction) — a present-tense description of an unbuilt verb is exactly the unwitnessed-claim shape the standing contract forbids.
- **Stamp `autoharn.expected_model` (and the exporting env) in whatever launcher the maintainer actually uses**, with the spec's fallback expectation file for anything else. Without this, both v0 and v1 watch nothing; with it, the watchdog's coverage reporting makes "unwatched" loud.
- **Run `./otel-attest` on a cadence** (operator cron or a session-end habit) so the live ledger accumulates evidence-lane rows at all. The spec deliberately left scheduling to the operator; the residual is that "operator's choice" has so far meant "never."

**Needs a maintainer decision:**

- **A ratification-hygiene rung (claims lane):** whether a ratification-recording decision row should carry the advising principal/session as a typed fact — the prod row's third candidate. My recommendation: adopt the *convention* now (a `refs`/statement discipline naming the advising session id in ratification rows — zero machinery, closes the relay case at claims grade), and defer any typed column to ADR-0011 recurrence, since s44 attestation over the recording row already covers the common case at evidence grade. A typed column would still be self-reported at write time; its value is auditability of the claim, not truth of it — same footing as `principal_actor_resolution`.
- **A pre-ratification attestation habit:** whether constitutional-grade ratifications should wait on an `otel-attest` pass over the advising window (a beep-and-batch discipline, not a gate — gating stays barred by the action-stream ruling and by the sentry spec's own §9 argument, which I find independently correct: a control an adversary evades by unsetting an env var only constrains the honest).
- **RD-2/RD-3 sequencing** (when s44+ enters a birth chain; shape B host residency) — already reserved to him; nothing here changes their framing.

**Out of this project's control (vendor surface; keep pressed through the feedback channel, never re-built locally):** hook-payload model identity; provider-side response signing. Both already named on the record (rows 1441/1450, issue 78658); the remediation shape is persistence, not construction.

**Evidence sources, graded (the commission's required table):**

| Source | Grade | Failure modes |
|---|---|---|
| OTel `api_request` stream | Diagnostics-tier, defeasible; the *best available* | R1 opt-out silence; R2 fail-open drops; R3 unsigned file; R7 unauthenticated emitter — fail-open at the attacker's option, honest-operator evidence only |
| Hook/action-stream payloads | The only guarantee-bearing surface — but carries **no model identity** | The gap is total for this class until the vendor adds the field; anything inferred from hooks about model is fabrication |
| Transcript records / `~/.claude` internals | Diagnostics by standing ruling, permanently | Unauthenticated, mutable, vendor-shaped; the 2026-07-11 ruling bars load-bearing use on principle |
| Model self-report | **Zero evidentiary weight** | It is the attack surface, not a witness — the specimen's false authority record is this source failing exactly as expected |
| Out-of-band maintainer declaration (`expected_model` at launch) | Ground truth **of intent**, not of service | A wrong or missing declaration yields false alarm or false pass with no deeper truth available (spec §16); it is the indispensable *comparand*, never the observation |
| Provider-side signing (hypothetical) | Would be ground truth of service | Does not exist; out of control |

---

## 3. Reconciliation with the prod row's candidate directions (read only after the analysis above was formed)

Row 1434's candidate-directions sentence names three: **(1)** an orchestrator-model attribution channel on ledger writes, diagnostics-tier; **(2)** harness-side evidence — which surfaces record the session model, at what grade; **(3)** whether ratifications should carry the advising principal as a typed fact.

**Convergence:** my independent analysis found candidates (1) and (2) not merely right but *already executed* — the sentry/attestation/defeat arc is (1) built at exactly the diagnostics tier the row stipulates, and rows 1441/1443 plus the R1–R7 rebuttal table are (2) answered to the evidence-grade precision the row asks for. The prod's investigation phase is, on the record, substantially discharged; what remains of (1)/(2) is operational arming (v0 build, launcher stamping, live attestation cadence — §2.3), not investigation.

**Divergence:** the row frames all three candidates as record-side. My analysis puts the sharpest residual one level below the row's framing: the class is now *representable everywhere and represented nowhere* — the gap is a standing process, not a schema. Nothing in the candidate list names the watchdog's absence or the zero-live-rows fact, because both postdate the row's authoring; a reader discharging the prod from the row's candidates alone would miss the actual residue.

**Candidate (3):** not rejected, but demoted with reasons. A typed advising-principal fact is claims-lane and self-reported at write time — it cannot carry the load the specimen needs carried, and in the common case (advice and recording in one session) s44/v1 attestation of the recording row already captures the adviser at evidence grade. I recommend the zero-machinery convention now (name the advising session in ratification rows) and reserve the typed fact for ADR-0011 recurrence. **No candidate is rejected outright; none, as written, reaches the residual named in §2.1.**

**Disposition suggestion for the prod itself:** it is a standing prod, retire-only-on-his-word, and should stay open — but its next re-raise to the maintainer can honestly be reframed from "investigate" to a three-item decision: build v0 (yes/no, already-ratified spec), adopt the launcher-stamping + attestation cadence (his operational choice), and rule on the ratification-hygiene convention. That reframing, plus the vendor asks kept warm, is the whole of what remains.
