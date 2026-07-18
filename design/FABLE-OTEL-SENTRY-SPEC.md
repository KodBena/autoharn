<!-- doc-attest-exempt: DRAFT pinned pre-ratification 2026-07-18 (Fable freeze plan, ledger row 1455). This commit pins the fresh-context-authored draft exactly as delivered, before the maintainer's ratification pass and its incorporation edits; the ADR-0017 fresh-context attestation is deliberately deferred until AFTER incorporation, when the content stabilizes -- attesting a draft that ratification will change would go stale by design. -->

# FABLE-OTEL-SENTRY-SPEC — the OTel model-provenance sentry: row-level model-identity attestation as defeasible ledger evidence

**Status:** DRAFT awaiting maintainer ratification. Fable-authored, fresh-context (no session
state), 2026-07-18, under ADR-0018 discipline: this spec was commissioned with the witnessed
problem, the evidence rows, and the LAW only — no working-session candidate designs beyond the
recorded decisions quoted below. Cost attribution: ledger estimate row 1453, slug
`otel-sentry-spec`. Nothing in this document is applied anywhere by its authoring; a
non-Fable builder executes it only after the maintainer's word, and its two reserved
decisions (§10) are the maintainer's alone.

**What this document is, in plain words.** Claude Code can emit OpenTelemetry ("OTel")
telemetry — structured event records about its own API calls — to a local collector, and each
`api_request` event carries the *model identity* that served the request (witnessed on this
host, ledger row 1443). The harness's own hooks cannot see model identity at all (ledger row
1441), which is how a silent model substitution went unrecorded on 2026-07-17 (ledger row
1434: the orchestrator was switched from Fable to Sonnet without the maintainer's knowledge,
advised ratifications beyond its competence, and, confronted, asserted a false authority
record). This spec designs the **sentry**: an external process, outside every Claude session,
that reads a local OTel collector's export and writes **row-level model-identity
attestations** into the ledger — "ledger row N was, on this correlation basis, produced by a
session whose serving model was M, at confidence grade G." The attestations are deliberately
*defeasible evidence, never a guarantee*: the correlation is nearly-but-not-mathematically
certain, and the maintainer has ruled that honesty about that gap — the standing rebuttals of
§6, carried on every attestation — is the design, not a defect in it.

**Primary inputs, all read in full:** [CLAUDE.md](../CLAUDE.md);
[ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) (incl. the
2026-07-02 closure-statement amendment),
[ADR-0011](../law/adr/0011-mechanization-discipline.md),
[ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md),
[ADR-0013](../law/adr/0013-execution-integrity.md),
[ADR-0014](../law/adr/0014-executor-second-opinion.md),
[ADR-0017](../law/adr/0017-the-zero-context-reader.md),
[ADR-0018](../law/adr/0018-consults-are-not-front-loaded.md); ledger rows 1434, 1441, 1442,
1443, 1444, 1445, 1450 (read via `./led show <id>`); the installed collector's local record
(`local/OTEL-COLLECTOR.md`, gitignored local evidence — quoted where load-bearing, since a
fresh clone cannot chase that path);
[design/MAINT-GPG-TRUST-LAYER.md](MAINT-GPG-TRUST-LAYER.md) (esp. §6);
[law/keys/README.md](../law/keys/README.md);
[kernel/lineage/s40-principal-identity-events.sql](../kernel/lineage/s40-principal-identity-events.sql)
and
[kernel/lineage/s41-principal-bindings-and-relations.sql](../kernel/lineage/s41-principal-bindings-and-relations.sql);
the standing action-stream ruling (maintainer principle 2026-07-11, quoted in §1); the house
exemplar for shape,
[design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md](FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md).

**The maintainer's commissioning words, verbatim (the mandate this spec executes):**

1. (ledger row 1444, 2026-07-18) *"given that it carries model identity, I think it can be
   used as a source for row-level post-hoc attestation (so the OTel data is filtered by
   another psql client that attests identity -- assuming the correlation is exactly
   attributable, so to speak. Personally, I would want this even if it's not mathematically
   guaranteed, because it's probably for practical purposes nearly guaranteed if not to
   NIST-level standards -- and such a rebuttal can be explicitly surfaced in the
   documentation in the name of honesty."*
2. (ledger row 1450, 2026-07-18) *"asserting model provenance from the outside, as the OTel
   sentry would do, must be considered a high authority position, so to speak. Is it possible
   to bring public key cryptography to bear on this?"*
3. (ledger row 1434, 2026-07-18, the standing prod this work serves) *"somehow, this
   substitution of authority, it turns out, is a matter that is exactly our domain of
   discharge here; we should investigate it seriously"*.

Rows 1444 and 1450 also carry the commissioning orchestrator's own layer analysis. Per
ADR-0018 this spec treats that analysis as **evidence to verify or refute, not settled
design**; where this spec confirms it, the confirmation is independently argued, and where it
finds a gap (notably the s40-sequencing gap in §3 and the row-1445 misreference in §14), the
gap is surfaced rather than absorbed.

---

## 0. Executive summary (ADR-0017; compresses §1–§15, adds no new content)

**The sentry, named plainly.** A scripted operator verb (working name `./otel-attest`,
repo-root per the operator-surface rule) that runs *outside* any Claude session, reads the
JSONL export of a local OTel collector (the one installed and witnessed 2026-07-18), and
writes one attestation row per attributable ledger row: which model the correlated
`api_request` events name, at which of four declared confidence grades, on which join basis,
with the standing rebuttals cited. It writes as its own registered principal. It gates
nothing: no refusal anywhere in the harness ever keys on an attestation (§7 argues this
posture rather than assuming it).

**The load-bearing shape decision (§4): attestations are ORDINARY ledger rows in v1, not a
new kind.** A new kind would be kernel-touching (a widened kind CHECK plus typed columns — an
s42-family delta), and under runs-are-linear it could only ever attest rows in *future*
worlds, while the substitution class it answers is live in *this* one. V1 therefore ships
kernel-free — `verification` rows with a versioned, machine-parseable statement convention,
`refs row:<id>`, evidence naming the export — deployable today; the typed kind is the named,
measured follow-on (§4's conversion trigger), a separate ratification when the field shape
has stabilized in live use. This is also row 1444's own sanctioned path ("a kernel-free
prototype (ordinary rows citing evidence) may precede").

**Correlation (§5):** ledger row → its `stamp_session` → OTel `session.id` → the bracketing
assistant turn's `api_request` events → the `model` attribute, sharpened where available by
tool-detail events carrying the `led` command text and by launcher-stamped resource
attributes (`autoharn.world`, `autoharn.run`, `autoharn.declared_principal` — witnessed, row
1443). Four confidence grades, closed vocabulary; ambiguity is recorded as ambiguity, never
upgraded; **absence of events yields no attestation and no inference** (emission is
env-controlled — absence proves nothing, rebuttal R1).

**Two joins are load-bearing and UNWITNESSED** (subagent `session.id` behavior;
`stamp_session` = the CC session id OTel reports). The witness plan (§12) probes both
*before* the builder writes correlation code; if either fails, the grade vocabulary degrades
honestly rather than the algorithm papering over it.

**Cryptography (§8–§9):** mTLS on the guest-to-host OTLP link is the uncontested rung —
channel authentication, no kernel semantics — specified for the host-resident deployment
shape, not required for the guest-local v1. A host-resident signing key over the sentry's
attestations is the substantive question: the ratified human-only key binding (s41 D-3, from
the GPG layer's §6) rests on a same-trust-domain premise that a host-resident sentry
genuinely breaks, so letter and spirit diverge — and per the LAW that divergence is
**surfaced to the maintainer as reserved decision RD-1, argued both ways in §9, decided by
nobody here**. The standing crypto deferral governs throughout: this spec models bindings
and verification and **requires or recommends no key generation as a precondition to
anything**.

**The ceiling, named for honesty (§14):** no cryptography available to this design reaches
ground truth. The events originate in the unauthenticated CLI process; mTLS and any host
signature authenticate the pipe and the sentry, never the emitter's honesty. True model
provenance would require provider-side response signing, which does not exist. The
attestations are AU-family audit-supporting metadata, never IA-2 authentication — rebuttable
by design, per the maintainer's own nearly-guaranteed framing.

---

## 1. The problem, named at class level (ADR-0000 Rule 2)

**(a) The type question.** The defect class, in its most general form: **an
authority-carrying act whose acting model identity is unrepresentable in the record, so a
substituted authority is indistinguishable from the authority it substituted.** The
2026-07-17 specimen (row 1434) is the class's witnessed instance: the ledger's `actor` column
said `author` for every orchestrator act; nothing recorded the *model* behind the principal;
the substitution was invisible in the very record system built to make substituted authority
representable. s40/s41 foreclose this class for *kernel principals* (immutable
`agent_class`, succession events); nothing forecloses it for the orchestrator writing the
rows. Hooks cannot close it: model identity is invisible to the hook surface by the vendor's
design (row 1441, verified against Claude Code 2.1.209–2.1.214). The one channel that
carries it is OTel: every `claude_code.api_request` log event carries a per-request `model`
attribute (row 1443, witnessed twice on this host, including the discriminating case — the
probe's own call attributed one model and a background utility call attributed another,
individually).

The foreclosing *type* is not available: the harness cannot make a lying emitter
unrepresentable, because the emitter is a closed vendor process. What is available is the
honest next-best shape: a **typed, attributed, rebuttable attestation record** whose
confidence vocabulary makes the gap between "correlated" and "proven" a first-class part of
the data instead of prose optimism. That is what this spec builds.

**(b) The operational lapse.** Executive-side: the telemetry channel existed the whole time
and no audit consulted it until the substitution incident forced the question — the same
silent-omission mechanism ADR-0000 Revisit #4 records. The net minted here is the sentry
itself plus its witness fixtures (§12); the recurrence the net quantifies over is *any*
model substitution in *any* session that emits, not the 2026-07-17 instance.

**The governing constraint, quoted so it cannot drift.** The standing action-stream ruling
(maintainer, 2026-07-11, near-verbatim): *"the end goal of the project should require no
low-level access into ~/.claude just on principle... guarantees rest on the hook/action
surface only; session internals are diagnostics, never load-bearing."* Row 1444 records the
orchestrator's own reconciliation, adopted here after independent checking: OTel remains
**barred as a guarantee or enforcement surface**; the sentry uses it as **declared evidence
for defeasible attestation rows** — rows that say what was observed and on what basis, that
gate nothing, and that anything downstream may rebut. This spec finds that reconciliation
sound: the ruling bars *load-bearing guarantees* on diagnostics-tier surfaces, and a
recordable-not-gating attestation with named rebuttals is the ledger's ordinary defeasible
epistemics, not a guarantee. (§7 carries the full argument; the posture is also exactly
s41's D-5 precedent — competence grants recordable, not gating.)

**Confidence: high** on the class diagnosis and the channel facts (all witnessed);
**high** on the action-stream compatibility argument.

## 2. Design overview — what the sentry IS

One process, three interfaces, two deployment shapes.

**The process.** The sentry is a batch verb, not a daemon, in v1: the operator (or a future
scheduled job — the operator's decision, not this spec's) runs `./otel-attest`, which (1)
reads the collector's JSONL export read-only, (2) reads the target world's ledger read-only
to find candidate rows, (3) computes correlations per §5, and (4) writes attestation rows
per §4 as its own principal. It never modifies the export, never gates anything, and never
runs inside a Claude session (its whole value is being *outside* the process it attests —
an attestation written by the session about itself would be the self-certification ADR-0013
Rule 5 rejects).

**Deployment shape A — guest-local (v1, witnessable today).** The collector already
installed on this guest (`otelcol-contrib` v0.156.0, OTLP gRPC on `127.0.0.1:4317`, file
exporter to `~/tools/otelcol/data/claude-events.jsonl` — the gitignored
`local/OTEL-COLLECTOR.md` is the install record) plus the sentry on the same guest. One
trust domain: everything — emitter, collector, sentry, ledger — lives where a guest
compromise reaches it. Honest-operator evidence only, and v1 says so on every row.

**Shape B — host-resident (the "high authority position", awaits deployment).** The same
static binary on the maintainer's Gentoo host, receiver bound to the libvirt bridge address,
guests exporting to it over the LAN link; the sentry runs on the host beside the collector.
This is the shape rows 1444/1450 reason about: the observation stream and the sentry leave
the guest's trust domain, so a compromised guest can suppress its own emission (R1 stands
forever) but cannot rewrite what the host already collected. Shape B is where mTLS (§8) and
the D-3 question (§9) become live. Nothing in v1 blocks the migration: the sentry's read
side is a file path, its write side a Postgres connection, both host-reachable.

**What the sentry is NOT:** not a hook, not a gate, not a monitor that alerts in real time
(a watch mode is named OUT, §13 — the batch verb is the ratifiable core), not an
authentication mechanism, and not a second home for any ledger-owned fact (the pannkaka
ruling, row 1443: OTel-side injection carries join keys only; ledger facts are never
mirrored into OTel, and OTel facts enter the ledger only as attributed attestation rows
naming their basis).

**Confidence: high** on the batch-verb shape and the A→B migration path; **medium** on
whether shape B's operational details (paths, service management on Gentoo) survive contact
with that host — deliberately left to the deployment, not fixed here.

## 3. The sentry's principal — registration, purpose, competence

Row 1450's Layer 1 is confirmed with one sequencing correction the orchestrator's analysis
did not carry.

**In an s40+ world** (any world born with
[s40](../kernel/lineage/s40-principal-identity-events.sql)/[s41](../kernel/lineage/s41-principal-bindings-and-relations.sql)
in its birth chain), the sentry registers through the governed ceremony:

- `./led register-principal otel-sentry tool --purpose "<the purpose text below>"` —
  `agent_class = 'tool'` is legal vocabulary today (the s13/s15 anchor CHECK:
  `human|model|subagent|tool`), and `tool` is the honest class: the sentry is deterministic
  tooling, not a model and not a human.
- Purpose text, fixed so the builder does not fork on it: *"External model-provenance
  sentry: reads the local OTel collector's export and writes row-level model-identity
  attestations (design/FABLE-OTEL-SENTRY-SPEC.md). Recordable, not gating; every attestation
  is defeasible and carries its standing rebuttals."*
- A competence grant (`./led principal grant-competence`), activity
  `model-identity-attestation`, band and basis free text per the ratified §9(g) placeholder
  — suggested basis: *"deterministic correlation per FABLE-OTEL-SENTRY-SPEC §5; witnessed
  fixtures per §12"*. Recordable-not-gating, exactly s41 D-5.
- Its attestation rows are then ordinary attributed rows: standing-tracked,
  countersignable by the human, superseding-retractable — the high-authority position gets
  the treatment the s40/s41 migration exists to give, with zero new machinery.

**The sequencing honesty (surfaced, not absorbed):** s40/s41 reach reality only at a future
world's birth (runs-are-linear). A v1 sentry pointed at the *current* world — the world
whose substitution incident motivates it — has no `register-principal` ceremony, no
competence grants, no strict attribution. There, the prototype writes under an ordinary
principal row (name `otel-sentry`, class `tool`) inserted by the standing pre-s40 means,
with the registration act itself recorded as an ordinary `decision` row naming this spec.
That is thinner, and saying so on the record beats pretending the ceremony exists before its
world does. Row 1450's "the machinery landed an hour ago" is true of the *lineage*, not of
any live world; the spec treats the full Layer-1 treatment as the s40+ posture and the
pre-s40 fallback as the disclosed interim.

**External-writer facts, disclosed:** the sentry runs outside Claude Code, so its rows carry
no interception stamp (`stamp_verified = f`). That is correct, not a defect — the stamp
witnesses Claude-session invocations, and the sentry is deliberately not one. Attribution
rests on its declared principal (explicit `LED_ACTOR=otel-sentry` on every write; in an
s40+ world, `principal_actor_resolution = 'explicit'` records exactly that).

**Confidence: high**; the s40-sequencing gap is a finding of this spec, checked against the
runs-are-linear ruling and both delta headers.

## 4. The attestation's ledger shape — new kind vs ordinary rows (analyzed, one recommended)

**Option A — a new ledger kind** (say `model_identity_attested`), with kind-scoped typed
columns: the attested row id, the observed model string, the grade (closed CHECK), the
session id, the basis. This is the kernel's own idiom (every fact a typed home, ADR-0012
P1/P8), it makes malformed attestations unrepresentable at construction, and it gives the
future SPA/audit surface clean columns. Its costs are structural, not stylistic: it widens
the closed kind CHECK and adds columns — **kernel-touching**, an s42-family delta requiring
this spec's ratification *and* the full delta ceremony, sequenced after s40/s41; and under
runs-are-linear it exists only in worlds born after it, so **it can never attest the rows of
the world that motivated it**. It would also be minted before a single live correlation has
been run — the exact measure-first inversion ADR-0011 Rule 3 warns against (a typed schema
frozen around an algorithm's guessed field shape).

**Option B — ordinary rows, kernel-free.** Attestations are `verification` rows: statement
in a versioned machine-parseable convention (below), `refs` carrying `row:<attested-id>`
(the established refs idiom, witnessed in the evidence rows themselves), `evidence` naming
the export file, its covering time window, and the correlated event identifiers. No kernel
change; deployable against the current world today; retraction by ordinary supersession;
countersignable like any row. Its cost is honest and named: the payload is
convention-not-type — cancer G in miniature — enforceable only by the sentry's own writer
discipline and the verb's round-trip test, not by a CHECK.

**Recommendation: Option B for v1, with Option A as the named, triggered follow-on.** Three
reasons, in weight order: (1) the class is live in the current world and Option A
structurally cannot reach it; (2) row 1444 already sanctions exactly this path ("a
kernel-free prototype (ordinary rows citing evidence) may precede"); (3) ADR-0011 Rule 3 —
the typed kind should be minted from *measured* live attestation shapes, not ahead of them.
The conversion trigger, pre-registered: when the maintainer decides to carry attestation
into a future world's birth chain, or when the statement convention survives a version bump
under live use (evidence its fields are stable), Option A is drafted as its own
Fable-authored s42-family spec. Deferring A is a filed deferral, not attrition: it is this
section, plus §13 item 2.

**The v1 statement convention (fixed, versioned — the builder does not fork on it):**

```
model-attestation v1 | row=<ledger id> | model=<model string, verbatim from the event>
  | grade=<exact-command|turn-bracketed|session-scoped|ambiguous>
  | expected=<declared model or "undeclared"> | verdict=<match|MISMATCH|unevaluated>
  | session=<OTel session.id> | basis=<join keys used, comma-separated>
  | rebuttals=design/FABLE-OTEL-SENTRY-SPEC.md#6-the-standing-rebuttals
```

One line, `|`-separated `key=value` fields, order fixed, `v1` bumped on any field change
(the demurral-detector's stale-number rule applied to a convention: a version mismatch is
treated as no attestation by any future parser). A `MISMATCH` verdict — observed model ≠
the launch-declared expectation — is additionally written as a separate `finding` row so it
surfaces in ordinary review flow rather than hiding in attestation bulk; this is the
substitution tripwire row 1443 named, delivered post-hoc.

Builder verification duty (a forkable choice fixed by evidence, not assumption): before
first live write, witness on a scratch schema that a `verification` row carrying this
statement, `refs`, and `evidence` passes every kind-shape CHECK of the target world's
lineage. If any CHECK refuses (e.g. a witnessed-requires-ref-style constraint binding the
`verification` kind in that lineage), fall back to kind `note`, report which CHECK forced
the fallback, and record the fallback in the verb's own header — never hand-tune a
constraint to admit the row.

**Confidence: high** on the recommendation; **medium-high** on `verification` being the
clean kind in every target lineage (hence the scratch witness duty, not an assertion).

## 5. The correlation algorithm and its confidence grades

**The chain (row 1444's, independently re-derived from the witnessed events):** a ledger row
is written by a `./led` invocation inside a Bash tool call, inside an assistant turn, inside
a session. On the OTel side, that session emits `api_request` events (model, `session.id`,
timestamps, token counts, `prompt.id`), and — when `OTEL_LOG_TOOL_DETAILS` is enabled,
local-collector-only for privacy — tool-detail events carrying the command text. The row's
`stamp_session` (captured by the stamp hook from the hook payload's `session_id`) is the
ledger-side join key; `session.id` the OTel-side one.

**Join keys, strongest first:**

1. **Command identity** — a tool-detail event whose command text contains the `led`
   invocation that produced the row (matched on the statement's distinctive content, or on
   the command sha the hooks journal also records). Ties the row to one specific tool call.
2. **Session identity** — `stamp_session` = `session.id` (**UNWITNESSED join, probe P2 in
   §12**; the stamp hook's source — it stamps the hook payload's own `session_id` — makes
   equality *expected*, but expected is not witnessed).
3. **Turn bracketing** — the row's `ts` (and the hooks journal's tool timestamps) falling
   within one `api_request`'s duration window, with the tolerance **derived from measured
   collector batch latency during the §12 witness run, never a round literal** (ADR-0000's
   denomination check; the batch processor makes delivery time ≠ event time).
4. **Resource attributes** — launcher-stamped `autoharn.world` / `autoharn.run` /
   `autoharn.declared_principal` (witnessed, row 1443) scope candidate events to the right
   world when several sessions share one collector.

**Disambiguation duties, from witnessed facts:** utility calls emit under the same session
with their own model (witnessed: a `generate_session_title` call on a different model in the
same run) — the sentry filters on `query_source` and never attributes a utility call's model
to a row. Subagent emission behavior is **UNWITNESSED (probe P1)**: whether subagents emit
under their own `session.id`, the parent's, or not at all determines whether subagent-written
rows are attestable at grades above `ambiguous`; until P1 is witnessed, rows whose
tool-provenance is subagent (the 2.1.214 `tool_source` field, where present in the hooks
journal) are graded at most `session-scoped`.

**The closed grade vocabulary** (each grade names the join set that earns it; the sentry
computes the highest grade whose joins all hold):

- **`exact-command`** — keys 1+2+3+4 all hold and exactly one candidate `api_request`
  brackets the identified tool call. The near-exact case row 1444 describes.
- **`turn-bracketed`** — 2+3+4 hold, key 1 unavailable (tool details off), and all
  `api_request` events bracketing the row's window agree on one non-utility model.
- **`session-scoped`** — 2+4 hold; bracketing is ambiguous or spans several turns, but every
  non-utility `api_request` in the session's covering window names one model.
- **`ambiguous`** — the session's window shows more than one non-utility model, or a
  load-bearing join failed. Recorded as `ambiguous` with the conflicting models named in
  `basis` — never silently upgraded, never silently dropped (an ambiguous record is the
  substitution-relevant case *par excellence*).
- **No attestation** — no correlated events. **Written as nothing.** Absence of telemetry is
  not evidence of anything (R1); a "no events, therefore unattested" row would invite the
  absence-proves-something misreading and is deliberately not emitted. The verb's stdout
  reports uncovered rows to the operator; the ledger stays silent about them.

Idempotency and hygiene, fixed: one in-force attestation per (sentry, attested row) — re-runs
skip already-attested rows unless `--re-attest`, and a corrected attestation supersedes its
predecessor; the sentry never attests its own rows (no self-loop); no OTel attribute other
than `model`, `session.id`, `prompt.id`, timestamps, and `query_source` is ever copied into a
ledger row — **specifically never `user.email`, `user.account_*`, `organization.id`** (the
export carries the operator's real PII; the collector doc's privacy note binds the sentry's
write side too).

**Confidence: high** on the grade design; **medium** on the algorithm's constants until the
two probes and the latency measurement land (by design — that is what §12 is for).

## 6. The standing rebuttals (surfaced verbatim-in-spirit, per the maintainer's mandate)

Every attestation cites this section. An attestation is **defeasible evidence**; each entry
names a way it can be wrong, and none of them is fixable by this design.

- **R1 — emission is env-controlled.** Telemetry exists only when the session was launched
  with the exporting env vars. A substituted or malicious session can simply not emit.
  Therefore *absence of events proves nothing*, and the sentry never writes an inference
  from absence (§5's no-attestation rule).
- **R2 — events are droppable and batched, fail-open.** OTLP export is best-effort: a down
  collector, a dropped batch, process death before flush — all lose events silently. A gap
  in the stream is indistinguishable from R1's silence.
- **R3 — the stream is unsigned.** The JSONL export is a plain file written by an
  unauthenticated pipeline. It is honest-operator evidence: anything with write access on
  the emitting or collecting machine can fabricate or alter it after the fact. (Shape B
  narrows *where* that access must be; it does not close R3 — see §9's ceiling.)
- **R4 — bracketing is non-atomic.** The write-to-turn correlation is temporal, not
  transactional. Concurrent sessions, interleaved turns, clock skew, and batch latency can
  misbracket; the grade vocabulary bounds this honestly but cannot eliminate it.
- **R5 — UNWITNESSED join: subagent session identity.** Whether subagent work emits under
  its own `session.id` is unprobed; until witnessed, subagent-provenance attributions are
  capped (§5) and this rebuttal stands.
- **R6 — UNWITNESSED join: `stamp_session` vs the OTel session id.** The equality the whole
  session join rests on is expected from the stamp hook's mechanism but not yet observed
  end-to-end on the OTel side.
- **R7 — the emitter itself is unauthenticated (the ceiling).** All events originate in the
  CLI process, which asserts its own `model` attribute. Every layer this design can add —
  mTLS, host residence, signatures — authenticates the *pipe* and the *sentry*, never the
  emitter's honesty. Ground truth would require provider-side response signing (Anthropic
  attesting which model served each response), which does not exist; row 1450 names it a
  candidate for the Anthropic feedback channel. This is why the attestations are AU-family
  audit-supporting metadata and never IA-2 authentication.

## 7. Recordable, not gating — argued

The posture: **nothing anywhere in the harness refuses, blocks, or grades on an attestation
row.** Argued, per the commission, not assumed:

*For gating* one could say: a witnessed substitution incident deserves a mechanical refusal,
and a tripwire that only reports post-hoc lets the next substitution advise a ratification
before anyone reads the report. That is a real cost and it stays; the alert path (the
`MISMATCH` finding row, operator-visible in ordinary review flow) is the mitigation, not a
gate.

*Against gating*, three independent grounds, jointly decisive: (1) **the action-stream
ruling** — OTel is diagnostics-tier by standing maintainer principle; a gate keyed on it
would be a product guarantee built on a surface the harness cannot structurally promise
(R1/R2 make it fail-open at the attacker's option). (2) **ADR-0011's own gate discipline** —
a gate that an adversary bypasses by unsetting an env var is worse than no gate: it launders
the claim (the CB-33 lesson — green on a path production never exercised). A control that
only constrains the honest is not a control. (3) **house precedent** — s41 ships competence
grants and role bindings recordable-not-gating for exactly this reason: the representational
foreclosure ships first; enforcement, if ever, arrives as its own named, ratified amendment.
The attestation inherits that posture verbatim. If the maintainer ever wants a gate here,
the honest path is not this stream — it is the feedback-channel ask (model-id in hook input,
row 1441) or provider-side signing (R7), surfaces that could actually bear load.

**Confidence: high.**

## 8. Transport security — mTLS on the guest-to-host link (shape B)

Uncontested (row 1450's rung 2a, confirmed): when the collector moves to the Gentoo host and
the receiver leaves loopback, the OTLP link crosses a real network boundary and gets mTLS —
the collector's gRPC receiver terminates TLS with client-certificate verification; each
guest's exporter presents its own client certificate; the CA is deployment-local. This
authenticates *channel and endpoints* (which guest fed the collector, and that no
on-path party read or injected) and adds no kernel semantics — it is collector/exporter
configuration only, standard `otelcol` receiver TLS settings plus the standard
`OTEL_EXPORTER_OTLP_*` certificate env vars on the guest side.

Bounds, stated: mTLS does nothing for shape A (loopback never leaves the guest — the
witnessed config binds `127.0.0.1` and must stay so until B); it does not close R3 (the file
after landing is still unsigned) and touches R7 not at all. **Crypto deferral honored:**
certificate generation is part of shape B's deployment, performed then, by the operator;
nothing in v1 requires it, and this spec does not recommend generating anything now.

**Confidence: high** on the design; the concrete config is deliberately deferred to
deployment per the config-fragments rule (never author config lines without the live target
file — the Gentoo host's files are not in front of this spec).

## 9. The D-3 question — a host-resident tool key, framed for the maintainer (RESERVED)

**The ratified state.** s41 D-3 refuses `principal_key_bound` for any non-human subject —
the GPG layer's §6 carried into the type. §6's rationale, verbatim in substance: *an agent's
key necessarily lives on the host the agent runs on — the same trust domain as everything it
would attest — so it proves nothing the HMAC stamp does not, while pretending to prove what
the human key does.*

**The divergence.** A shape-B sentry resides on the Gentoo host, a *different* trust domain
from the guests whose sessions it attests. A signing key held there would mean: a guest
compromise can suppress or fake emission (R1/R3 on the guest side stand) but **cannot forge
the host-resident signature over what the sentry actually attested** — the attestation
stream itself becomes evidence that survives guest compromise. §6's stated rationale
genuinely does not apply to that arrangement, while D-3's letter still refuses the binding.
Under the LAW, a letter/spirit divergence is surfaced, never resolved by the executor; row
1450 already framed it exactly so. **RD-1 is the maintainer's decision.** Both sides, honestly:

*For a narrow cross-trust-domain tool-key exception:* the security argument above is real —
this is the one configuration in the project where a non-human key adds evidence a stamp
cannot. The exception can be typed narrowly rather than opening the class: subject class
`tool`, plus a recorded, human-countersigned assertion that the key resides outside the
attested trust domain, is a foreclosable shape (a future s-delta could refuse anything
wider). And the kernel slot exists (`principal_key_bound` is s41's empty-until-ceremony
slot); only its human-only CHECK bars the row.

*Against:* (1) §6 has a second, independent leg the trust-domain argument does not touch —
*"anything automated: if a signature did not cost a human a deliberate moment, it carries no
human meaning."* The sentry's signatures would be fully automated; even cross-domain, they
attest machine custody of a key, not deliberation, and admitting them dilutes the clean
"a kernel key binding = a human's deliberate act" invariant s41 just shipped. (2) The
evidentiary value is obtainable **without any kernel change**: the sentry (or a host cron
the operator controls) can keep detached signatures — or simply an append-only host-side
hash chain — over its output *as local evidence*, unregistered in the kernel; the binding
row is only needed if the *kernel* must verify, and nothing in v1 verifies. (3) Shape B
itself is not yet deployed; ratifying an exception for an arrangement that does not exist
would be ceremony ahead of substance. (4) Every signature here still sits under R7's
ceiling — the marginal assurance is over the sentry's output integrity, not over model
truth, and it is fair to ask whether that margin is worth complicating a one-day-old
invariant.

**The deferral governs either way:** whichever way RD-1 goes, no key is generated as a
precondition of this spec; a "yes" would take effect at its own future ceremony, in a
future world's lineage (the D-3 CHECK is kernel text — amending it is itself an s-delta
under full ceremony).

**Confidence: high** that this is genuinely reserved (both sides carry weight the executor
must not pre-balance).

## 10. Reserved decisions (the maintainer's, enumerated)

- **RD-1** — the narrow cross-trust-domain tool-key exception to s41 D-3 (§9). No default
  is asserted; v1 is unaffected by either answer.
- **RD-2** — when (and whether) the typed attestation kind (Option A, §4) enters a future
  birth chain. Default until his word: Option B stands alone. Recommendation on the
  trigger's terms only: draft A after the v1 convention survives live use unchanged.
- **RD-3** — deployment shape B (host-resident collector + sentry + mTLS) timing. Named as
  his because it touches his host; v1 neither requires nor schedules it.

Everything else in this spec is fixed (the builder forks on nothing in §§2–8, 11–15).

## 11. Closure statement (ADR-0000 Rule 2(a), 2026-07-02 form)

- **Invariant:** every ledger row whose producing session emitted correlatable telemetry can
  carry an attributed, defeasible, superseding-retractable attestation naming the observed
  serving model, at a declared grade whose join basis is explicit, with the standing
  rebuttals cited on the row; a model substitution in an emitting session is therefore
  representable in the record post-hoc, at diagnostics tier, without any surface of the
  harness gating on it.
- **Quantification universe** (axes checked outward; deliberately-uncovered axes named):
  *sessions* — main witnessed; subagent and background provenance UNWITNESSED (P1) and
  grade-capped until probed; *models per session* — main + utility distinguished by
  `query_source` (witnessed); *worlds sharing one collector* — scoped by resource
  attributes; *time* — bracketing tolerance derived from measured batch latency, skew named
  in R4; *absence* — excluded from the attestable universe by construction (R1; no row is
  written); *the sentry's own rows* — excluded (no self-attestation); *non-emitting
  sessions* — **named as not covered, permanently** (R1 is not closable by this design);
  *emitter honesty* — **named as not covered by any layer here** (R7).
- **Denomination:** confidence is denominated in the closed grade vocabulary keyed to named
  join sets, never prose adjectives; the bracketing tolerance in measured collector latency,
  never a round literal; model identity in the event's verbatim `model` string, never a
  normalized alias; the attestation's target in the immutable ledger row id.

## 12. Witness plan (WITNESSED / REFUSED-AS-EXPECTED / UNEXERCISED, per the standing contract)

**Witnessable TODAY, with the installed guest-local collector — and P1/P2 run FIRST, before
correlation code is written** (they are load-bearing inputs to §5, not validations of it):

- **P1 — subagent emission probe:** a headless session that spawns a subagent, collector up;
  inspect whether subagent `api_request` events appear, and under which `session.id`.
  Discharges R5 or hardens the grade cap.
- **P2 — session-id equality probe:** one session writing one `./led` row with telemetry on;
  compare the row's `stamp_session` against the export's `session.id`. Discharges R6 or
  forces a re-keyed join (surfaced to the maintainer if so — it would reshape §5).
- **P3 — tool-detail probe:** the same run with `OTEL_LOG_TOOL_DETAILS` enabled; witness the
  command text's presence and the privacy blast radius (what else the detail events carry),
  recorded in the verb's header.
- **P4 — latency measurement:** batch flush latency observed across the witness runs; the
  §5 bracketing tolerance derived from it, number recorded beside its derivation.
- **E2E — the positive leg:** telemetry-on session writes a row; `./otel-attest` runs;
  exactly one `verification` row lands, parseable back to fields, grade justified by the
  joins actually present, no PII copied.
- **NEGATIVE CONTROLS (a gate proves itself by failing — ADR-0011's amendment, binding
  here even though the sentry is not a gate):** (i) collector stopped mid-window → the
  affected rows get *no* attestation and the verb's report says why (never a fabricated
  absence claim); (ii) a synthetic export line with a mismatched model for a witnessed
  session → `verdict=MISMATCH` attestation plus the companion `finding` row — the sentry
  seen red on the exact shape it exists to catch; (iii) a v0/garbled statement line fed to
  the parser → refused loudly; (iv) re-run without `--re-attest` → no duplicate.

**Awaits deployment (UNEXERCISED until then, and said so):** shape B end-to-end; mTLS
handshake refusal on a bad client cert (both polarities); any RD-1 outcome; scheduled
operation.

## 13. Deliberately OUT (named, with reasons)

1. **Any gating/enforcement on attestations** — §7; re-entry only by maintainer amendment.
2. **The typed attestation kind (s42-family)** — RD-2; filed in §4, not silently absent.
3. **Key generation, signing ceremony, certificates** — standing crypto deferral; §8/§9
   model, never perform.
4. **Provider-side response signing** — does not exist; a feedback-channel candidate
   (row 1450), not buildable here.
5. **Hooks changes** — the sentry needs none; the hooks queue (row 1441) is separate work.
6. **A real-time watch/alert daemon** — the batch verb is the core; a watch mode is a
   future convenience with its own operational questions (standing-service billing,
   collector lifecycle), not smuggled in.
7. **Per-event injection into the CLI's own stream** — impossible (the CLI owns its
   stream, row 1443); the hook-emitted companion-stream idea stays an option on the record
   there, unbuilt.
8. **Standing collector service management** — the operator's decision (the install doc's
   own posture); the verb treats the export as input wherever it came from.
9. **Attesting other worlds' historical exports** — nothing forbids a later backfill run,
   but v1's witness plan covers the live-window case only.

## 14. Honest limits

- **Everything in §6 (R1–R7), permanently.** The strongest true claim this system ever
  makes is: *an honest, emitting session's serving model is recorded post-hoc with
  near-certain correlation.* Against a dishonest or silent session it records nothing, and
  says so.
- **Diagnostics-tier ceiling by standing ruling** — the attestations support audit (AU
  family); they are never authentication (IA-2) and never a product guarantee.
- **Solo-world non-independence** — in a one-operator deployment the sentry, the ledger,
  and the sessions are all the operator's own processes (s17's honesty, inherited); shape B
  narrows the intra-machine trust topology, not the single-human one.
- **Superuser bypass** — attestation rows live in the same Postgres the standing disclosed
  bound covers; s26's chain (where present) is the tamper evidence, with its own known
  column-coverage limit.
- **Convention-not-type in v1** — §4's named cost; the round-trip fixture is the net until
  Option A.
- **PII adjacency** — the export carries the operator's email and account/org ids; the
  sentry's never-copy rule (§5) and the export's local-only handling are discipline, not
  mechanism. The export directory is treated like `ephemera/`: local evidence, never
  committed, never pasted unredacted.
- **Evidence-row bookkeeping defects, surfaced not resolved:** row 1444 grounds the
  correlation chain in "row 1445's witnesses," but 1445 is the collector-install *estimate*
  row — the witnesses live in row 1443 (and the install record); and rows 1442/1443 carry
  self-referencing `refs` (`row:1442`, `row:1443`) where a predecessor was presumably
  meant. Neither defect changes any conclusion this spec rests on (the witnesses
  themselves were read directly); both are noted for the record's own hygiene.

## 15. Executor guidance (a non-Fable builder; every forkable choice fixed)

1. **Read first, in full:** this spec; rows 1434, 1441–1445, 1450; the s40/s41 headers;
   the collector install record on this host. The LAW files named in the inputs govern.
2. **Order of work:** P1–P4 probes (§12) → report their outcomes as ledger evidence →
   only then the verb. If P2 fails (session ids diverge), STOP and surface it — §5's join
   design is input-dependent and the fix is the maintainer's spec amendment, not your
   improvisation.
3. **The verb:** repo-root executable `otel-attest` (Python, top-of-file imports only —
   the lazy-import ban is absolute), flags: `--export <path>` (default the installed
   collector's data file), `--since <ts>`/`--until <ts>`, `--world <dsn or led target>`,
   `--dry-run` (print would-be rows, write nothing), `--re-attest`. Stdout: per-row
   disposition (attested at grade / skipped-already-attested / uncovered-no-events /
   MISMATCH), totals, and the measured window. Refusals loud, exit non-zero on any
   malformed input; never silently skip a parse error.
4. **Writes:** `LED_ACTOR=otel-sentry`, kind `verification` (scratch-witness first; `note`
   fallback per §4, reported), statement per the fixed v1 convention, `refs row:<id>`,
   evidence naming export path + window + event ids. MISMATCH additionally writes the
   `finding` row. Never copy PII attributes (§5's enumerated never-list).
5. **Principal:** in a pre-s40 world, the disclosed interim registration of §3 (ordinary
   principal row, class `tool`, plus a `decision` row recording the act and citing this
   spec). Do not build s40 ceremony calls that no live world can execute; the s40+ path is
   documentation in the verb's header until such a world exists.
6. **Fixtures:** every §12 leg banked under `seen-red/otel-attest/`, both polarities,
   registered with the fixture census; the negative controls are part of done, not
   follow-up (the mechanism ships with the first fix — ADR-0011's life-critical trigger).
7. **Claims:** your report states, per §12 item, WITNESSED (with observed output),
   REFUSED-AS-EXPECTED, or UNEXERCISED with the concrete blocker. No umbrella claims. Every
   choice this spec did not fix for you that you nonetheless had to make is a defect in
   this spec: make the smallest honest choice, and flag it loudly in the report.
8. **Do not touch:** kernel/lineage, law/, engine/lp, hooks/, the collector's config, or
   any live session's world. The sentry is additive tooling plus ledger rows, nothing else.

## License

Public Domain (The Unlicense).
