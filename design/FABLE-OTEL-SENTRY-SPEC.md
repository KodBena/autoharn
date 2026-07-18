<!-- doc-attest-exempt: DRAFT pinned pre-ratification 2026-07-18 (Fable freeze plan, ledger row 1455). This commit pins the fresh-context-authored draft exactly as delivered, before the maintainer's ratification pass and its incorporation edits; the ADR-0017 fresh-context attestation is deliberately deferred until AFTER incorporation, when the content stabilizes -- attesting a draft that ratification will change would go stale by design. -->

# FABLE-OTEL-SENTRY-SPEC — the OTel model-provenance sentry: real-time watchdog, row-level attestation, and the typed attestation kind

**Status:** DRAFT awaiting maintainer ratification. Fable-authored, fresh-context (no session
state), 2026-07-18, under ADR-0018 discipline; **REVISED same day per the maintainer's
response** (his verbatim words below; the adjudication is ledger row 1464; revision cost
attribution: ledger estimate row 1465, original authoring row 1453, slug `otel-sentry-spec`).
The revision restructures the design watchdog-first (§3), authors the typed attestation kind
in full delta grade (§8), and renumbers the reserved decisions (§12) — the maintainer's
alone. Nothing in this document is applied anywhere by its authoring; a non-Fable builder
executes it only after the maintainer's word.

**What this document is, in plain words.** Claude Code can emit OpenTelemetry ("OTel")
telemetry — structured event records about its own API calls — to a local collector, and each
`api_request` event carries the *model identity* that served the request (witnessed on this
host, ledger row 1443). The harness's own hooks cannot see model identity at all (ledger row
1441), which is how a silent model substitution went unrecorded on 2026-07-17 (ledger row
1434: the orchestrator was switched from Fable to Sonnet without the maintainer's knowledge,
advised ratifications beyond its competence, and, confronted, asserted a false authority
record). This spec designs the **sentry** as three stacked layers, cheapest and fastest
first: **v0, the watchdog** — a small always-on process that tails the collector's export and
*beeps the maintainer's phone* (through his existing mail-notification script) the moment an
observed model disagrees with the session's declared one; **v1, row-level attestation** — a
batch verb that writes defeasible model-identity attestations into the ledger, one per
attributable row, at a declared confidence grade with standing rebuttals cited; **v2, the
typed attestation kind** — the kernel-delta form of the same record, authored here in full
for a future world's birth chain. The layers stack; they do not compete. Every layer's claims
are deliberately *defeasible evidence, never a guarantee*: the correlation is
nearly-but-not-mathematically certain, and the maintainer has ruled that honesty about that
gap — the standing rebuttals of §7 — is the design, not a defect in it.

**Primary inputs, all read in full:** [CLAUDE.md](../CLAUDE.md);
[ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) (incl. the
2026-07-02 closure-statement amendment),
[ADR-0011](../law/adr/0011-mechanization-discipline.md),
[ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md),
[ADR-0013](../law/adr/0013-execution-integrity.md),
[ADR-0014](../law/adr/0014-executor-second-opinion.md),
[ADR-0017](../law/adr/0017-the-zero-context-reader.md),
[ADR-0018](../law/adr/0018-consults-are-not-front-loaded.md); ledger rows 1434, 1441, 1442,
1443, 1444, 1445, 1450, and the revision adjudication row 1464 (read via `./led show <id>`);
the installed collector's local record (`local/OTEL-COLLECTOR.md`, gitignored local evidence
— quoted where load-bearing, since a fresh clone cannot chase that path); the operator's live
notification hook (`~/.claude/settings.json`, read-only verification quoted in §3);
[design/MAINT-GPG-TRUST-LAYER.md](MAINT-GPG-TRUST-LAYER.md) (esp. §6);
[law/keys/README.md](../law/keys/README.md);
[kernel/lineage/s40-principal-identity-events.sql](../kernel/lineage/s40-principal-identity-events.sql)
and
[kernel/lineage/s41-principal-bindings-and-relations.sql](../kernel/lineage/s41-principal-bindings-and-relations.sql);
[design/FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md](FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md)
(the ratified s42/s43 family §8's delta composes with); the house exemplar for shape,
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
4. (the revision response, 2026-07-18, verbatim — this revision's own commission) *"I have
   looked over the sentry spec (not read fully) and can state that I disagree with the
   premise -- I would want it as a watchdog; I already have in ~/.claude an email notifier
   that sends an email so my cell-phone beeps each time a turn is completed, and I would want
   something like that here -- unless you can give me a reason it is making no sense.
   Meanwhile for the attestation ledger's shape, I originally proposed shape B as you can
   recall (just add rows) because I think it's the mathematically elegant way to handle
   things (where you build from axioms, or small atoms, etc -- taking what you have and
   invent interesting things), but if option A is the disciplined way, (new ledger kind), why
   wouldn't we want to do that right away? It's not going to happen after July 19th anyways
   so there's no reason to do less than what is appropriate. That is all I can say on that
   matter, but note that \*I am not really competent to judge A vs B on their principled
   merits\*."*

Rows 1444 and 1450 also carry the commissioning orchestrator's own layer analysis. Per
ADR-0018 this spec treats that analysis as **evidence to verify or refute, not settled
design**; where this spec confirms it, the confirmation is independently argued, and where it
finds a gap (notably the s40-sequencing gap in §4 and the row-1445 misreference in §16), the
gap is surfaced rather than absorbed.

---

## 0. Executive summary (ADR-0017; compresses §1–§17, adds no new content)

**Three layers, one channel.** The OTel `api_request` event stream is the only surface that
carries model identity. This spec puts three consumers on it, in build order:

- **v0 — the WATCHDOG (§3), the maintainer's premise, endorsed on merits.** A small
  always-on tail-and-compare over the collector's JSONL: each non-utility `api_request`'s
  `model` attribute is compared against the session's *declared expected model* (a
  launcher-stamped resource attribute, the mechanism already witnessed in row 1443); on
  mismatch it calls the operator's existing notification script — the same
  `notify.py` his Stop hook already runs, verified read-only in §3 — so his phone beeps
  within seconds of a substitution, not at the next audit. No principal, no ledger write, no
  kernel anything. A false alarm on a legitimate mid-session `/model` switch is accepted and
  named; silence on a real substitution is the failure the design is shaped against, which
  is why the watchdog also reports *coverage* (which sessions it is actually watching), not
  only mismatches. §3 carries the one honest paragraph the maintainer asked for: the
  watchdog is sound, and the original spec's post-hoc emphasis was inverted.
- **v1 — ROW-LEVEL ATTESTATION (§4–§7), unchanged in substance.** A batch verb
  (`./otel-attest`) that correlates ledger rows to `api_request` events and writes one
  defeasible attestation row per attributable row — ordinary `verification` rows in the
  *current* world (the kernel-free path row 1444 itself sanctioned), at four declared
  confidence grades, standing rebuttals cited on every row, gating nothing.
- **v2 — the TYPED ATTESTATION KIND (§8), authored NOW in full delta grade.** The
  disciplined form of the same record: kind `model_identity_attested`, seven kind-scoped
  columns with two-way CHECKs in the house idiom, composed onto the ratified s42/s43 family
  (it writes through the s43 boundary, and its columns enter the s42 full-coverage hash by
  that family's own gate). Authored pre-freeze because only Fable *authoring* ends
  2026-07-19 — Sonnet builds ratified specs after — so deferring the authoring would lose
  it, while the delta itself still reaches reality only at a future world's birth. The
  measure-first trade this makes is named honestly in §8.6, with its revision valve.

**The layers stack, they do not compete.** The maintainer's shape-B instinct ("just add
rows — build from small atoms") is vindicated for the world it can serve: v1 exists because
runs-are-linear means no new kind can ever attest the *current* world's rows. His "why not
the disciplined way right away" is answered by doing both: v1 for the live world, v2
authored now for every world born after it.

**Two joins are load-bearing and UNWITNESSED** (subagent `session.id` behavior;
`stamp_session` = the CC session id OTel reports). The witness plan (§14) probes both
*before* correlation code is written; the watchdog does not depend on either (it keys on
declared-expectation vs observed events, no ledger join).

**Cryptography (§10–§11):** mTLS on the guest-to-host OTLP link is the uncontested rung for
the host-resident deployment shape. A host-resident signing key over the sentry's output is
reserved decision RD-1 (§11): the ratified human-only key binding (s41 D-3) rests on a
same-trust-domain premise a host-resident sentry genuinely breaks — a letter/spirit
divergence surfaced to the maintainer, argued both ways, decided by nobody here. The
standing crypto deferral governs throughout: no key generation is required or recommended
as a precondition to anything.

**The ceiling, named for honesty (§16):** no cryptography available to this design reaches
ground truth. The events originate in the unauthenticated CLI process; every layer here
authenticates pipes and processes, never the emitter's honesty. True model provenance would
require provider-side response signing, which does not exist. Watchdog alerts and
attestations alike are AU-family audit-supporting evidence, never IA-2 authentication.

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
honest next-best pair: a **real-time tripwire** on the one channel that carries the fact
(v0 — had it been running on 2026-07-17, the 18:24Z switch would have beeped the
maintainer's phone within one request, per row 1443's own assessment), and a **typed,
attributed, rebuttable attestation record** (v1/v2) whose confidence vocabulary makes the
gap between "correlated" and "proven" a first-class part of the data instead of prose
optimism.

**(b) The operational lapse.** Executive-side: the telemetry channel existed the whole time
and no audit consulted it until the substitution incident forced the question — the same
silent-omission mechanism ADR-0000 Revisit #4 records. A second lapse belongs to this spec's
own first draft and is owned here: it led with the post-hoc layer when the incident class is
a *real-time* class — the harm of 2026-07-17 accrued in the window between switch and
discovery, and the maintainer's premise objection (his verbatim item 4) caught the
inversion. The net minted here is the watchdog plus the sentry plus their witness fixtures
(§14); the recurrence the net quantifies over is *any* model substitution in *any* session
that emits, not the 2026-07-17 instance.

**The governing constraint, quoted so it cannot drift.** The standing action-stream ruling
(maintainer, 2026-07-11, near-verbatim): *"the end goal of the project should require no
low-level access into ~/.claude just on principle... guarantees rest on the hook/action
surface only; session internals are diagnostics, never load-bearing."* Row 1444 records the
orchestrator's own reconciliation, adopted here after independent checking: OTel remains
**barred as a guarantee or enforcement surface**; the watchdog uses it for **operator
notification** (a beep is not a gate — nothing refuses, blocks, or grades on it), and the
sentry uses it as **declared evidence for defeasible attestation rows**. This spec finds
that reconciliation sound: the ruling bars *load-bearing guarantees* on diagnostics-tier
surfaces, and neither an email nor a recordable-not-gating attestation with named rebuttals
is a guarantee (§9 carries the full argument; the posture is also exactly s41's D-5
precedent — competence grants recordable, not gating).

**Confidence: high** on the class diagnosis and the channel facts (all witnessed);
**high** on the action-stream compatibility argument.

## 2. Design overview — the three layers and the two deployment shapes

**v0 — the watchdog (§3):** always-on, guest-local in its first deployment, no state beyond
a debounce set, alerts through the operator's existing mail path. Build first; it is the
cheapest layer and the only one that shrinks the incident window.

**v1 — the attestation verb (§4–§7):** a batch verb, not a daemon: the operator (or a future
scheduled job — the operator's decision, not this spec's) runs `./otel-attest`, which (1)
reads the collector's JSONL export read-only, (2) reads the target world's ledger read-only
to find candidate rows, (3) computes correlations per §6, and (4) writes attestation rows
per §5 as its own principal. It never modifies the export, never gates anything, and never
runs inside a Claude session (its whole value is being *outside* the process it attests —
an attestation written by the session about itself would be the self-certification ADR-0013
Rule 5 rejects).

**v2 — the typed kind (§8):** the s44-family delta, authored in this document, entering a
future birth chain at the maintainer's word (RD-2).

**Deployment shape A — guest-local (witnessable today).** The collector already installed on
this guest (`otelcol-contrib` v0.156.0, OTLP gRPC on `127.0.0.1:4317`, file exporter to
`~/tools/otelcol/data/claude-events.jsonl` — the gitignored `local/OTEL-COLLECTOR.md` is the
install record) plus the watchdog and sentry on the same guest. One trust domain:
everything — emitter, collector, watchdog, sentry, ledger — lives where a guest compromise
reaches it. Honest-operator evidence only, and the record says so.

**Shape B — host-resident (the "high authority position", awaits deployment).** The same
static binary on the maintainer's Gentoo host, receiver bound to the libvirt bridge address,
guests exporting to it over the LAN link; watchdog and sentry run on the host beside the
collector. This is the shape rows 1444/1450 reason about: the observation stream and its
consumers leave the guest's trust domain, so a compromised guest can suppress its own
emission (R1 stands forever) but cannot rewrite what the host already collected — and the
watchdog's alerts originate from a machine the watched session cannot touch. Shape B is
where mTLS (§10) and the D-3 question (§11) become live. Nothing in v0/v1 blocks the
migration: the read side is a file path, the alert side an executable, the write side a
Postgres connection, all host-reachable.

**What no layer is:** not a hook, not a gate, not an authentication mechanism, and not a
second home for any ledger-owned fact (the pannkaka ruling, row 1443: OTel-side injection
carries join keys only; ledger facts are never mirrored into OTel, and OTel facts enter the
ledger only as attributed attestation rows naming their basis).

**Confidence: high** on the layer stack and the A→B migration path; **medium** on shape B's
operational details (paths, service management on Gentoo) — deliberately left to the
deployment, not fixed here.

## 3. v0 — the watchdog (the maintainer's premise, endorsed and designed)

**The honest answer to "unless you can give me a reason it is making no sense."** There is
no such reason; the watchdog is sound, and the premise correction is accepted on merits, not
deference. The channel is near-real-time (the collector receives within batch-flush seconds
of each request); the comparison — observed `model` vs a declared expectation — is cheap,
deterministic, and needs none of §6's correlation machinery (no ledger join, no bracketing:
the event alone carries everything the check needs); and the alert path is already proven on
this exact host — the maintainer's phone beeps today on every turn completion through the
same script the watchdog would call. The incident class is a real-time class: the
2026-07-17 harm accrued between the switch and its discovery, exactly the window a beep
shrinks from days to seconds and a post-hoc verb does not shrink at all. The one honest
caveat is a design duty, not an objection: the watchdog inherits R1/R2 (§7) — it can only
watch sessions that *emit*, and a substituted session that silently stops emitting looks
identical to a closed one. A watchdog that reports only mismatches would therefore become
false comfort; this one also reports **coverage** (below), so the operator can see the
difference between "watched and clean" and "not watched at all." With that duty designed in,
the watchdog is the right first layer and the original draft's post-hoc emphasis was
inverted.

**The alert path, verified read-only 2026-07-18 (the operator's existing mechanism, reused
not reinvented).** The live `~/.claude/settings.json` carries exactly one Stop hook:

```json
"Stop": [ { "hooks": [ { "type": "command",
  "command": "/home/bork/w/vdc/venvs/generic/bin/python /home/bork/mailnotice/notify.py \"Task finished: $(basename \"$PWD\")\" 2>/dev/null",
  "timeout": 15, "async": true } ] } ]
```

The watchdog calls the same interpreter and script with its own subject line:

```
/home/bork/w/vdc/venvs/generic/bin/python /home/bork/mailnotice/notify.py \
  "OTEL WATCHDOG mismatch: session=<id8> expected=<model> observed=<model>"
```

No new notification infrastructure, no hooks/ changes, no edits to the operator's settings —
the watchdog is a separate process that happens to call the same script.

**The mechanism (working name `otel-watch`, repo-root verb with `--daemon`):** follow the
collector's JSONL export (`tail -F` semantics — survive rotation/truncation); parse each
OTLP batch line; for every `api_request` log record that is not a utility call (filtered on
`query_source`, the witnessed discriminator — a `generate_session_title` call legitimately
runs a different model), compare `model` against the session's expected model; on
disagreement, alert.

**The expected-model input, designed honestly (who declares it, where it lives):**

1. **Primary: launcher-declared, session-static.** The launcher that starts a watched
   session stamps `autoharn.expected_model=<model id>` into `OTEL_RESOURCE_ATTRIBUTES` —
   the exact injection mechanism already witnessed (row 1443 stamped `autoharn.world`,
   `autoharn.declared_principal`, `autoharn.run` the same way). The declaration travels
   *with the session's own events*, so the watchdog needs no side-channel registry and no
   session-id bookkeeping. It is a *declaration*, not ground truth: it says what the
   operator intended, which is precisely the thing a substitution violates.
2. **Fallback: a watchdog-side expectation file** (one line per rule: match on
   `autoharn.world` or `autoharn.declared_principal` → expected model), for sessions whose
   launcher predates the attribute. Read at startup and on SIGHUP; documented in the verb's
   header.
3. **Neither present → the session is UNWATCHED, said loudly, never silently.** The
   watchdog emits one coverage notice per such session (stdout/journal always; by mail only
   if `--alert-unwatched` is set — the operator chooses his beep budget). This is the
   coverage duty from the honest answer above: silence must be distinguishable from health.

**The `/model` mid-session switch, named (the commissioned question):** the expectation is
session-static; a legitimate operator-initiated `/model` switch mid-session will fire a
mismatch alert. **This false alarm is accepted and named for v0** — the operator who just
switched gets a beep he can dismiss in two seconds, and the asymmetry is deliberate: a
false alarm on a legitimate switch costs a glance; silence on a real substitution is the
2026-07-17 incident again. No suppression heuristic (e.g. "trust a switch the transcript
shows") is built in v0, because every such heuristic reads surfaces the watchdog cannot
authenticate and converts the cheap-and-honest design into a guessing one. If live use
proves the false-alarm rate a real burden, the revision route is a dated amendment here —
measured first (ADR-0011 Rule 3), never improvised.

**Debounce and failure posture, fixed:** one alert per (session, observed-model) pair —
repeated requests on the same wrong model do not mail-storm, but a *new* wrong model always
alerts. Mail failure or watchdog death = silence, which is R2's fail-open truth applied to
the watchdog itself; a `--heartbeat` option (one daily "watchdog alive, N sessions watched"
mail) is named as the operator's opt-in against it. The watchdog writes nothing to the
ledger, registers no principal, and holds no state beyond the debounce set and its journal
(a local logfile beside the collector's own, same privacy handling).

**Confidence: high** on soundness and the alert-path reuse (hook entry verified);
**medium-high** on the expected-model attribute surviving contact with every launcher shape
(the fallback file is the named net).

## 4. The sentry's principal — registration, purpose, competence (v1)

v0 needs no principal (it writes nothing). For v1, row 1450's Layer 1 is confirmed with one
sequencing correction the orchestrator's analysis did not carry.

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
  — suggested basis: *"deterministic correlation per FABLE-OTEL-SENTRY-SPEC §6; witnessed
  fixtures per §14"*. Recordable-not-gating, exactly s41 D-5.
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

## 5. The v1 attestation's ledger shape — ordinary rows, and why the layers stack

The original draft analyzed two shapes; the maintainer's response resolves the tension by
taking both, each for the world it can serve.

**Shape B — ordinary rows (v1, the current world).** Attestations are `verification` rows:
statement in the versioned machine-parseable convention below, `refs` carrying
`row:<attested-id>` (the established refs idiom, witnessed in the evidence rows themselves),
`evidence` naming the export file, its covering time window, and the correlated event
identifiers. No kernel change; deployable against the current world today; retraction by
ordinary supersession; countersignable like any row. This is the maintainer's own original
proposal ("just add rows"), and his elegance instinct is structurally vindicated here: under
runs-are-linear **no new kind can ever attest the rows of the world that motivated this
work** — small atoms on the existing algebra are not merely adequate for the live world,
they are the *only* thing that can serve it. Row 1444 sanctioned exactly this path ("a
kernel-free prototype (ordinary rows citing evidence) may precede"). Its cost is honest and
named: the payload is convention-not-type — cancer G in miniature — enforceable only by the
sentry's own writer discipline and the verb's round-trip fixture, not by a CHECK.

**Shape A — the typed kind (v2, every future world).** The disciplined form: typed columns,
two-way CHECKs, malformed attestations unrepresentable at construction. The original draft
deferred *authoring* it on measure-first grounds; the maintainer's "why wouldn't we want to
do that right away... it's not going to happen after July 19th anyways" — corrected and
strengthened by the freeze's actual scope (only Fable *authoring* ends at midnight
2026-07-19; Sonnet builds ratified specs after) — moves the authoring to now. §8 is that
authoring, in full delta grade; §8.6 names the measure-first trade this makes and its
revision valve. The delta still reaches reality only at a future world's birth (RD-2).

**The v1 statement convention (fixed, versioned — the builder does not fork on it):**

```
model-attestation v1 | row=<ledger id> | model=<model string, verbatim from the event>
  | grade=<exact-command|turn-bracketed|session-scoped|ambiguous>
  | expected=<declared model or "undeclared"> | verdict=<match|MISMATCH|unevaluated>
  | session=<OTel session.id> | basis=<join keys used, comma-separated>
  | rebuttals=design/FABLE-OTEL-SENTRY-SPEC.md#7-the-standing-rebuttals
```

One line, `|`-separated `key=value` fields, order fixed, `v1` bumped on any field change
(the demurral-detector's stale-number rule applied to a convention: a version mismatch is
treated as no attestation by any future parser). A `MISMATCH` verdict — observed model ≠
the launch-declared expectation — is additionally written as a separate `finding` row so it
surfaces in ordinary review flow rather than hiding in attestation bulk; this is the
post-hoc half of the substitution tripwire (the real-time half is v0's beep).

Builder verification duty (a forkable choice fixed by evidence, not assumption): before
first live write, witness on a scratch schema that a `verification` row carrying this
statement, `refs`, and `evidence` passes every kind-shape CHECK of the target world's
lineage. If any CHECK refuses (e.g. a witnessed-requires-ref-style constraint binding the
`verification` kind in that lineage), fall back to kind `note`, report which CHECK forced
the fallback, and record the fallback in the verb's own header — never hand-tune a
constraint to admit the row. The v1 field set is deliberately identical, name for name, to
§8's typed columns, so the convention *is* the typed kind flattened into one line — the
stacking made literal.

**Confidence: high**; **medium-high** on `verification` being the clean kind in every
target lineage (hence the scratch witness duty, not an assertion).

## 6. The correlation algorithm and its confidence grades (v1/v2 shared)

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
   §14**; the stamp hook's source — it stamps the hook payload's own `session_id` — makes
   equality *expected*, but expected is not witnessed).
3. **Turn bracketing** — the row's `ts` (and the hooks journal's tool timestamps) falling
   within one `api_request`'s duration window, with the tolerance **derived from measured
   collector batch latency during the §14 witness run, never a round literal** (ADR-0000's
   denomination check; the batch processor makes delivery time ≠ event time).
4. **Resource attributes** — launcher-stamped `autoharn.world` / `autoharn.run` /
   `autoharn.declared_principal` (witnessed, row 1443), plus §3's `autoharn.expected_model`
   — scoping candidate events to the right world when several sessions share one collector,
   and supplying the `expected=` field.

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
write side too, and the watchdog's journal and mail subjects the same way).

**Confidence: high** on the grade design; **medium** on the algorithm's constants until the
two probes and the latency measurement land (by design — that is what §14 is for).

## 7. The standing rebuttals (surfaced verbatim-in-spirit, per the maintainer's mandate)

Every attestation cites this section, and the watchdog's own claims sit under the same
entries (R1–R4 and R7 apply to it verbatim). An attestation or an alert is **defeasible
evidence**; each entry names a way it can be wrong, and none of them is fixable by this
design.

- **R1 — emission is env-controlled.** Telemetry exists only when the session was launched
  with the exporting env vars. A substituted or malicious session can simply not emit.
  Therefore *absence of events proves nothing*: the sentry never writes an inference from
  absence (§6's no-attestation rule), and the watchdog reports coverage so unwatched is
  never mistaken for clean (§3).
- **R2 — events are droppable and batched, fail-open.** OTLP export is best-effort: a down
  collector, a dropped batch, process death before flush — all lose events silently. A gap
  in the stream is indistinguishable from R1's silence. The watchdog itself fails silent
  (its heartbeat option is the operator's opt-in against that).
- **R3 — the stream is unsigned.** The JSONL export is a plain file written by an
  unauthenticated pipeline. It is honest-operator evidence: anything with write access on
  the emitting or collecting machine can fabricate or alter it after the fact. (Shape B
  narrows *where* that access must be; it does not close R3 — see §11's ceiling.)
- **R4 — bracketing is non-atomic.** The write-to-turn correlation is temporal, not
  transactional. Concurrent sessions, interleaved turns, clock skew, and batch latency can
  misbracket; the grade vocabulary bounds this honestly but cannot eliminate it. (The
  watchdog does no bracketing — R4 is v1/v2-only — but a legitimate `/model` switch is its
  analogous named false-positive, §3.)
- **R5 — UNWITNESSED join: subagent session identity.** Whether subagent work emits under
  its own `session.id` is unprobed; until witnessed, subagent-provenance attributions are
  capped (§6) and this rebuttal stands.
- **R6 — UNWITNESSED join: `stamp_session` vs the OTel session id.** The equality the whole
  session join rests on is expected from the stamp hook's mechanism but not yet observed
  end-to-end on the OTel side.
- **R7 — the emitter itself is unauthenticated (the ceiling).** All events originate in the
  CLI process, which asserts its own `model` attribute. Every layer this design can add —
  mTLS, host residence, signatures — authenticates the *pipe* and the *sentry*, never the
  emitter's honesty. Ground truth would require provider-side response signing (Anthropic
  attesting which model served each response), which does not exist; row 1450 names it a
  candidate for the Anthropic feedback channel. This is why everything here is AU-family
  audit-supporting metadata and never IA-2 authentication.

## 8. v2 — the typed attestation kind, authored in full (delta working name `s44-model-identity-attestation`)

Authored now at the maintainer's word ("no reason to do less than what is appropriate"),
under the corrected freeze premise: only Fable authoring ends 2026-07-19; a Sonnet builder
executes this section after ratification, on the standard scratch-schema ceremony. The
delta is **kernel-touching by definition** (a widened kind CHECK, seven new ledger columns)
and ships only under this spec's ratification — it is not class-ratifiable (new semantics,
not only new refusals). It reaches reality only at a future world's birth (runs-are-linear);
RD-2 is the maintainer's carry-it-into-a-chain decision.

### 8.1 Sequencing and family composition

Hard prerequisite chain: **s43** (and transitively s42/s41/s40), per the ratified
[s42/s43 family spec](FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md). Three composition
facts govern, each checked against that spec's text:

- **Writes route through the s43 boundary.** Post-s43, `INSERT` on `ledger` is revoked from
  the granted role (its §4.1: the privilege change is total); the sentry's writes therefore
  enter through the ledger boundary function like every other writer, and a malformed
  attestation meets a typed refusal that is itself recorded as a `write_refused` row —
  the sentry's failures become first-class audit records with zero new machinery.
- **The new columns enter the hash by the family's own gate.** s42's `compute_row_hash` v2
  serializes every column except `row_hash`, and `gates/hash_coverage_gate.py` goes red on
  any delta that adds a ledger column without re-issuing the function in the same delta
  (its §3.2 teach-text, verbatim: *"a delta that adds a ledger column re-issues
  compute_row_hash in the same delta"*). s44 therefore re-issues `compute_row_hash` with the
  seven new columns in catalog ordinal position, all `text`/`bigint` per the fixed per-type
  rules — closing, for attestations, the outside-the-hash limit v1's rows inherit from the
  s24-era serialization in pre-s42 worlds.
- **The kind CHECK re-issue is the s41→s43 idiom continued:** DROP/ADD, additive union,
  widening s43's twenty-four members by `model_identity_attested` (twenty-fifth).

### 8.2 The kind and its columns

Kind: **`model_identity_attested`**. Seven kind-scoped columns, all nullable, no column
DEFAULT (the s30 lesson), each with a **two-way** kind-shape CHECK (safe: the kind is born
in this delta — the s40 precedent; no pre-existing row can carry it, so ADD CONSTRAINT
validates vacuously), plus split value CHECKs per the s40 house idiom (one concern per
CHECK, for `gates/kind_shape_manifest_gate.py`'s classifier):

- `attest_row_id bigint REFERENCES ledger(id)` — the attested row. Mandatory (two-way).
  The FK is to the same table; the target's existence is thereby structural, not CLI-side.
- `attest_model text` — mandatory non-empty (two-way kind-shape + separate non-empty value
  CHECK); the event's `model` string **verbatim, never normalized** (§11's denomination
  discipline: identity in the emitter's own vocabulary, aliasing is a reader concern).
- `attest_grade text` — mandatory (two-way); closed value CHECK
  `IN ('exact-command','turn-bracketed','session-scoped','ambiguous')`. Closed is right
  here where s41's role names were ruled free text: the grades enumerate this design's own
  join algebra (kernel-structural, like s43's `refusal_surface`), not organizational
  naming.
- `attest_verdict text` — mandatory (two-way); closed value CHECK
  `IN ('match','mismatch','unevaluated')`.
- `attest_expected text` — nullable *within the kind* (one-way kind-shape CHECK: non-NULL
  only on this kind); non-empty when present. NULL means the session declared no expected
  model. Coupled to the verdict by a structural CHECK:
  `(attest_expected IS NULL) = (attest_verdict = 'unevaluated')` — an unevaluated verdict
  with a declared expectation, or a match/mismatch claim with nothing to match against, is
  unrepresentable.
- `attest_session text` — mandatory non-empty (two-way + value CHECK); the OTel
  `session.id`.
- `attest_basis text` — mandatory non-empty (two-way + value CHECK); the comma-separated
  join keys used (§6's vocabulary).

**Supersession: allowed, deliberately** — an attestation is a defeasible claim, retractable
and correctable by design, so s31 uniform supersession applies unchanged. This is the
argued contrast with s43's `write_refused` (whose R6 CHECK forbids supersession because a
refusal records a historical fact): the two postures differ because the two kinds' semantics
differ, and stating the contrast here is what keeps a future reviewer from "harmonizing"
them into a defect.

**Derived view** `model_attestations` (security_invoker, factoring through `ledger_current`
— the s31 reader discipline, no raw-`ledger` leg): one row per in-force attestation
(attested row id, model, grade, verdict, expected, session, attesting actor, ts, row_id),
`GRANT SELECT TO :role`. The human/SPA audit surface; display, never enforcement.

**Same-commit set,** per the house pattern: `ledger_current`/`countersigned_in_force`
re-issued with the seven columns appended at the end (the s20 lesson; column list = the s43
head's exact list + seven); `compute_row_hash` re-issued (§8.1); kind CHECK re-issued;
`gates/kind_shape_manifest_gate.py` CHAIN += s44 plus seven MANIFEST rows;
`gates/ledger_reader_allowlist.py` CHAIN += s44 (the new view expected to classify clean —
witnessed, not asserted); a `s44-*.detect.sql` sibling behavior-fingerprinted per the
migrate-detect-drift ruling; the engine leg re-verified (entry/6 is kind-generic — verified
at s40 and s41; the new kind flows through with no new `.lp` predicate, `./judge` witnessed
in AGREE on a fixture carrying it).

### 8.3 What stays CLI-side, named (the s41 precedent, not a gap silently left)

Cross-row properties the kernel's CHECK machinery cannot express without lookups: one
in-force attestation per (actor, attested row) — enforced by the verb (skip/supersede
logic, §6), a direct-psql writer could double-attest; and the no-self-attestation rule
(the target row's actor vs the attesting actor is a cross-row read) — verb-enforced. Both
are the same accepted direct-writer boundary s41 D-8 names for value-continuity, disclosed
here on the same footing. A `MISMATCH` companion `finding` row remains verb-side convention
in v2 as in v1 (a trigger minting side-effect rows would be a new kernel idiom this spec
does not open).

### 8.4 v2 witness plan (scratch-schema ceremony, both polarities, per element)

On a scratch chain built to the s43 head + s44, in the toy db: (1) every kind-shape and
value CHECK seen green on a well-formed attestation and red on each violation class
(missing target, empty model, out-of-vocabulary grade/verdict, expected/verdict decoupling,
non-kind row carrying an attest column); (2) the FK refusing a nonexistent target id; (3) a
correction superseding an attestation and `model_attestations` showing exactly the
successor; (4) `gates/hash_coverage_gate.py` green at s44 (and its synthetic-column
negative control still red); (5) a write through the s43 ledger boundary function accepted,
and a malformed one refused *with the refusal recorded* as `write_refused` — the composed
behavior witnessed, not inferred; (6) `./judge` AGREE on a fixture carrying the new kind;
(7) the detect sibling t on s44, f on the s43 head. Claims reported WITNESSED /
REFUSED-AS-EXPECTED / UNEXERCISED, per the standing contract.

### 8.5 The delta's own closure slice (ADR-0000 Rule 2(a))

- **Invariant:** in an s44 world, a model-identity attestation is representable only in the
  typed shape — target structural (FK), model verbatim, grade and verdict in closed
  vocabularies, expectation/verdict coupling structural — attributed, hash-covered,
  boundary-written, supersedable; a malformed attestation is unrepresentable at
  construction and its attempt is itself a recorded refusal event.
- **Universe:** kinds carrying each new column: exactly `model_identity_attested`
  (two-way CHECKs; `attest_expected` one-way within the kind plus the coupling CHECK);
  views: the two projection homes re-issued +7, `model_attestations` new, non-members
  re-verified per the s40/s41 lists (none does general column passthrough); triggers: none
  new (all constraints are same-row CHECKs plus the FK — deliberately trigger-free);
  hash: the seven columns inside the v2 serialization, gate-enforced; CLI-side residue:
  enumerated in §8.3, not silent.
- **Denomination:** grade in the join-set vocabulary; verdict in a three-member closed set
  coupled structurally to the expectation's presence; model identity in the emitter's
  verbatim string; the target in an immutable ledger id via FK.

### 8.6 The measure-first trade, named honestly, and its revision valve

The original draft's ground for deferring this section was ADR-0011 Rule 3: mint a typed
kind from *stabilized live shapes*, not ahead of them — a schema frozen around a guessed
field set is the measure-first inversion. That ground was real and is **traded, not
refuted**: against it stands the authoring-availability fact (Fable authoring ends
2026-07-19; the disciplined form is authored now or its authoring is lost), and the
maintainer's word — *"no reason to do less than what is appropriate"* — decides the trade.
What discipline survives the trade: the v1 convention and the v2 columns are field-for-field
identical, so v1's live operation *is* the measurement run for v2's schema; and the delta
cannot enter a birth chain before RD-2, so there is a natural window in which live v1
evidence can still reshape it cheaply. **The revision valve, fixed:** if live v1 shapes
contradict the authored kind (a field proves wrong-grained, a vocabulary member missing,
a coupling wrong), the route is a **maintainer decision plus a dated amendment to this
spec** (ADR-0005 Rule 8), the delta re-issued before any birth-chain entry — **never
builder improvisation**, and never silent divergence between the built delta and this
section's text.

**Confidence: high** on the columns/CHECKs (they transcribe §5/§6's already-designed
fields into the house idiom, and the composition facts are read from the ratified s42/s43
text); **medium** on field-set completeness against unlived use — exactly the residual the
valve exists for.

## 9. Recordable, not gating — argued (and where the watchdog sits)

The posture: **nothing anywhere in the harness refuses, blocks, or grades on an attestation
row or a watchdog alert.** The watchdog is *notification* — an email to a human is the
operator-attention channel working as designed, not an enforcement surface; the human it
beeps decides what to do, which is the decision-queue posture in miniature. For the
attestation rows, argued per the commission, not assumed:

*For gating* one could say: a witnessed substitution incident deserves a mechanical refusal,
and evidence that only reports lets the next substitution advise a ratification before
anyone reads the report. That cost is real and it is now answered at the right layer: the
*watchdog* shrinks the exposure window to seconds, without any gate — which removes most of
the remaining force of the gating argument.

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

## 10. Transport security — mTLS on the guest-to-host link (shape B)

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
nothing in v0/v1 requires it, and this spec does not recommend generating anything now.

**Confidence: high** on the design; the concrete config is deliberately deferred to
deployment per the config-fragments rule (never author config lines without the live target
file — the Gentoo host's files are not in front of this spec).

## 11. The D-3 question — a host-resident tool key, framed for the maintainer (RESERVED)

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
row is only needed if the *kernel* must verify, and nothing in v0–v2 verifies. (3) Shape B
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

## 12. Reserved decisions (the maintainer's, enumerated; renumbered at this revision)

- **RD-1** — the narrow cross-trust-domain tool-key exception to s41 D-3 (§11). No default
  is asserted; v0–v2 are unaffected by either answer.
- **RD-2** — when the s44 delta (§8, now fully authored) enters a future world's birth
  chain. Its *authoring* is discharged by this revision; its *reality* is his sequencing
  act, with §8.6's valve open until then.
- **RD-3** — deployment shape B (host-resident collector + watchdog + sentry + mTLS)
  timing. Named as his because it touches his host; v0/v1 run guest-local without it.

Everything else in this spec is fixed (the builder forks on nothing in §§2–10, 13–17). The
former draft's "RD-2: whether to author the typed kind" is resolved by the maintainer's
revision response and no longer reserved.

## 13. Closure statement (ADR-0000 Rule 2(a), 2026-07-02 form; the family view — §8.5 carries the s44 slice)

- **Invariant:** every emitting session's serving model is observable within seconds
  against its declared expectation (v0), and every ledger row whose producing session
  emitted correlatable telemetry can carry an attributed, defeasible,
  superseding-retractable attestation naming the observed serving model, at a declared
  grade whose join basis is explicit, with the standing rebuttals cited (v1; typed and
  structural in an s44 world, v2) — so a model substitution in an emitting session is
  representable in the record and surfaced to the operator, at diagnostics tier, without
  any surface of the harness gating on it.
- **Quantification universe** (axes checked outward; deliberately-uncovered axes named):
  *sessions* — main witnessed; subagent and background provenance UNWITNESSED (P1) and
  grade-capped until probed; *models per session* — main + utility distinguished by
  `query_source` (witnessed); *worlds sharing one collector* — scoped by resource
  attributes; *expectation declaration* — attribute-declared, file-fallback, or UNWATCHED
  said loudly (§3; the undeclared case is `unevaluated` in v1/v2, never guessed); *time* —
  bracketing tolerance derived from measured batch latency, skew named in R4; *legitimate
  mid-session `/model` switches* — **named as a false-positive class for v0**, accepted;
  *absence* — excluded from the attestable universe by construction (R1; no row is
  written) and distinguished from health by v0's coverage reporting; *the sentry's own
  rows* — excluded (no self-attestation); *non-emitting sessions* — **named as not
  covered, permanently** (R1 is not closable by this design); *emitter honesty* — **named
  as not covered by any layer here** (R7).
- **Denomination:** confidence in the closed grade vocabulary keyed to named join sets,
  never prose adjectives; the bracketing tolerance in measured collector latency, never a
  round literal; model identity in the event's verbatim `model` string, never a normalized
  alias; the attestation's target in the immutable ledger row id (an FK in v2); the
  watchdog's debounce keyed on (session, observed-model), never a time-window literal that
  could swallow a new wrong model.

## 14. Witness plan (WITNESSED / REFUSED-AS-EXPECTED / UNEXERCISED, per the standing contract)

**Witnessable TODAY, with the installed guest-local collector.**

*v0 watchdog (buildable and witnessable first, independent of P1/P2):*

- **W1 — mismatch fires:** a telemetry-on session launched with
  `autoharn.expected_model` deliberately set to a different model than the session runs;
  the watchdog calls `notify.py` with the mismatch subject (the mail's arrival is the
  operator-side witness; the exec of the script with the right argv is the fixture-side
  one). The watchdog seen red on the exact shape it exists to catch.
- **W2 — match stays silent:** same run, correct expectation; no alert, session counted in
  coverage.
- **W3 — unwatched is loud:** a session with no expectation declared; one coverage notice,
  no mismatch alert, never silence.
- **W4 — debounce:** repeated wrong-model requests → one alert; a second, different wrong
  model → a second alert.
- **W5 — utility-call filter:** the witnessed `generate_session_title` haiku call raises no
  alert.

*v1 sentry — P1–P4 run FIRST, before correlation code is written* (they are load-bearing
inputs to §6, not validations of it):

- **P1 — subagent emission probe:** a headless session that spawns a subagent, collector up;
  inspect whether subagent `api_request` events appear, and under which `session.id`.
  Discharges R5 or hardens the grade cap.
- **P2 — session-id equality probe:** one session writing one `./led` row with telemetry on;
  compare the row's `stamp_session` against the export's `session.id`. Discharges R6 or
  forces a re-keyed join (surfaced to the maintainer if so — it would reshape §6).
- **P3 — tool-detail probe:** the same run with `OTEL_LOG_TOOL_DETAILS` enabled; witness the
  command text's presence and the privacy blast radius (what else the detail events carry),
  recorded in the verb's header.
- **P4 — latency measurement:** batch flush latency observed across the witness runs; the
  §6 bracketing tolerance derived from it, number recorded beside its derivation.
- **E2E — the positive leg:** telemetry-on session writes a row; `./otel-attest` runs;
  exactly one `verification` row lands, parseable back to fields, grade justified by the
  joins actually present, no PII copied.
- **NEGATIVE CONTROLS (a gate proves itself by failing — ADR-0011's amendment, binding
  here even though the sentry is not a gate):** (i) collector stopped mid-window → the
  affected rows get *no* attestation and the verb's report says why (never a fabricated
  absence claim); (ii) a synthetic export line with a mismatched model for a witnessed
  session → `verdict=MISMATCH` attestation plus the companion `finding` row; (iii) a
  v0/garbled statement line fed to the parser → refused loudly; (iv) re-run without
  `--re-attest` → no duplicate.

*v2:* the scratch-schema plan of §8.4 is witnessable today on the toy db (the s42/s43
lineage files exist); its *live* operation awaits an s44 world.

**Awaits deployment (UNEXERCISED until then, and said so):** shape B end-to-end; mTLS
handshake refusal on a bad client cert (both polarities); any RD-1 outcome; scheduled/
service-managed operation of watchdog or sentry on the Gentoo host.

## 15. Deliberately OUT (named, with reasons)

1. **Any gating/enforcement on alerts or attestations** — §9; re-entry only by maintainer
   amendment.
2. **Key generation, signing ceremony, certificates** — standing crypto deferral; §10/§11
   model, never perform.
3. **Provider-side response signing** — does not exist; a feedback-channel candidate
   (row 1450), not buildable here.
4. **Hooks changes and any edit to the operator's `~/.claude` settings** — the watchdog
   *calls* the existing notifier; it changes no hook (the no-live-hooks-edits rule and the
   read-only verification in §3).
5. **A legitimate-switch suppression heuristic for v0** — named as a possible future
   amendment, measured first (§3); not built.
6. **Per-event injection into the CLI's own stream** — impossible (the CLI owns its
   stream, row 1443); the hook-emitted companion-stream idea stays an option on the record
   there, unbuilt.
7. **Standing collector service management** — the operator's decision (the install doc's
   own posture); watchdog and verb treat the export as input wherever it came from.
8. **Attesting other worlds' historical exports** — nothing forbids a later backfill run,
   but v1's witness plan covers the live-window case only.
9. **Kernel-side side-effect rows (a trigger minting the MISMATCH `finding`)** — verb-side
   convention in v1 and v2 alike (§8.3); opening a new kernel idiom is not this spec's
   mandate.

## 16. Honest limits

- **Everything in §7 (R1–R7), permanently.** The strongest true claim this system ever
  makes is: *an honest, emitting session's serving model is observed in near-real-time and
  recorded post-hoc with near-certain correlation.* Against a dishonest or silent session
  it observes nothing, records nothing, and — via v0's coverage reporting — says so.
- **The watchdog is best-effort by construction** — it fails silent (R2 applies to it);
  the heartbeat is the operator's opt-in mitigation; and its expectation input is a
  *declaration*, so a wrong declaration yields a false alarm or a false pass with no
  deeper truth available (R7).
- **Diagnostics-tier ceiling by standing ruling** — alerts and attestations support audit
  (AU family); they are never authentication (IA-2) and never a product guarantee.
- **Solo-world non-independence** — in a one-operator deployment the watchdog, sentry,
  ledger, and sessions are all the operator's own processes (s17's honesty, inherited);
  shape B narrows the intra-machine trust topology, not the single-human one.
- **Superuser bypass** — attestation rows live in the same Postgres the standing disclosed
  bound covers; the hash chain (s26 in current worlds, s42's full coverage in future ones)
  is the tamper evidence, with s26's known column-coverage limit applying to v1 rows in
  pre-s42 worlds.
- **Convention-not-type in v1** — §5's named cost; the round-trip fixture is the net until
  an s44 world exists (§8 is the typed closure, authored).
- **PII adjacency** — the export carries the operator's email and account/org ids; the
  never-copy rule (§6), the watchdog's subject-line discipline (§3), and the export's
  local-only handling are discipline, not mechanism. The export directory is treated like
  `ephemera/`: local evidence, never committed, never pasted unredacted.
- **Evidence-row bookkeeping defects, surfaced not resolved:** row 1444 grounds the
  correlation chain in "row 1445's witnesses," but 1445 is the collector-install *estimate*
  row — the witnesses live in row 1443 (and the install record); and rows 1442/1443 carry
  self-referencing `refs` (`row:1442`, `row:1443`) where a predecessor was presumably
  meant. Neither defect changes any conclusion this spec rests on (the witnesses
  themselves were read directly); both are noted for the record's own hygiene.

## 17. Executor guidance (a non-Fable builder; every forkable choice fixed)

1. **Read first, in full:** this spec; rows 1434, 1441–1445, 1450, 1464; the s40/s41
   headers; the ratified s42/s43 spec (for §8's composition); the collector install record
   on this host. The LAW files named in the inputs govern.
2. **Build order: v0 first.** The watchdog (`otel-watch`) per §3: Python, top-of-file
   imports only (the lazy-import ban is absolute), `--daemon`/`--once`, `--expectations
   <file>`, `--alert-unwatched`, `--heartbeat`. Alert exec'd exactly as §3's command line
   (argv list, no shell); journal beside the collector's own logs. Witness W1–W5 before
   calling it done; W1's fixture banks the exec'd argv.
3. **Then P1–P4 probes (§14)** → report their outcomes as ledger evidence → only then the
   v1 verb. If P2 fails (session ids diverge), STOP and surface it — §6's join design is
   input-dependent and the fix is the maintainer's spec amendment, not your improvisation.
4. **The v1 verb:** repo-root executable `otel-attest`, flags: `--export <path>` (default
   the installed collector's data file), `--since <ts>`/`--until <ts>`, `--world <dsn or
   led target>`, `--dry-run` (print would-be rows, write nothing), `--re-attest`. Stdout:
   per-row disposition (attested at grade / skipped-already-attested / uncovered-no-events
   / MISMATCH), totals, and the measured window. Refusals loud, exit non-zero on any
   malformed input; never silently skip a parse error.
5. **Writes:** `LED_ACTOR=otel-sentry`, kind `verification` (scratch-witness first; `note`
   fallback per §5, reported), statement per the fixed v1 convention, `refs row:<id>`,
   evidence naming export path + window + event ids. MISMATCH additionally writes the
   `finding` row. Never copy PII attributes (§6's enumerated never-list).
6. **Principal:** in a pre-s40 world, the disclosed interim registration of §4 (ordinary
   principal row, class `tool`, plus a `decision` row recording the act and citing this
   spec). Do not build s40 ceremony calls that no live world can execute; the s40+ path is
   documentation in the verb's header until such a world exists.
7. **v2 (only after ratification and at the maintainer's sequencing word, RD-2):** build
   `kernel/lineage/s44-model-identity-attestation.sql` + detect sibling exactly per §8 —
   §8.2's columns and CHECKs, §8.1's same-commit set, §8.4's witness plan, scratch-schema
   ceremony on the toy db, both polarities, `./judge` in AGREE. Any divergence you believe
   necessary between §8's text and buildable reality goes through §8.6's valve
   (maintainer + dated amendment), never your local judgment.
8. **Fixtures:** every §14 leg banked under `seen-red/otel-watch/` and
   `seen-red/otel-attest/` (and the s44 scratch under `seen-red/s44-model-identity-
   attestation/` when built), both polarities, registered with the fixture census; the
   negative controls are part of done, not follow-up (the mechanism ships with the first
   fix — ADR-0011's life-critical trigger).
9. **Claims:** your report states, per witness item, WITNESSED (with observed output),
   REFUSED-AS-EXPECTED, or UNEXERCISED with the concrete blocker. No umbrella claims. Every
   choice this spec did not fix for you that you nonetheless had to make is a defect in
   this spec: make the smallest honest choice, and flag it loudly in the report.
10. **Do not touch:** kernel/lineage (except the commissioned s44 files under item 7),
    law/, engine/lp, hooks/, `~/.claude/settings.json`, the collector's config, or any
    live session's world. The layers are additive tooling plus ledger rows, nothing else.

## Amendments (dated; Fable-authored; each names its trigger)

**A1 (2026-07-19) — the `ambiguous` write's value domain, fixed (completing §5; the field
set is unchanged, so `v1` stands — this is a value-domain completion, not a field change).**
Trigger: adversarial review finding F1 (adjudication ledger row 1505). The first build
silently folded every `ambiguous` session into the written-as-nothing path, contradicting
§6's explicit "never silently upgraded, never silently dropped." The root cause was this
spec's own underspecification: §5's statement shape shows a single `model=` value and never
said what an `ambiguous` attestation writes there. Fixed as follows, binding on the fix
pass and every later producer:

- **`model=unresolved`** — a closed sentinel, never a fabricated single model and never an
  invented multi-model packing of the field. The conflicting models are named in `basis=`
  (as §6 already requires), comma-separated with the join keys.
- **`verdict=` is decided by what the ambiguity still proves:** if *every* candidate
  non-utility model in the window contradicts `expected=`, the ambiguity is only about
  *which* wrong model served — that is `verdict=MISMATCH` (the substitution evidence is
  definite even though the culprit is not). If at least one candidate matches `expected=`,
  nothing is proven either way — `verdict=unevaluated`. Never `match`: ambiguity cannot
  clear a row. *(Addendum, same day, from the fix pass's surfaced gap: with an **empty**
  candidate set — grade `ambiguous` via join failure, no non-utility `api_request` in
  evidence at all — the rule above would assert MISMATCH vacuously over nothing; R1 forbids
  it. Empty candidates → `verdict=unevaluated`. Likewise `expected=undeclared` →
  `unevaluated`, matching the unambiguous path's own treatment of an undeclared
  expectation.)*
- **An `ambiguous` attestation also writes the companion `finding` row**, exactly as a
  MISMATCH does and for the same stated reason — §6 calls ambiguity "the
  substitution-relevant case *par excellence*"; letting it hide in attestation bulk
  contradicts that sentence. (A MISMATCH-verdict ambiguous row writes ONE finding, not two.)
- Downstream note, checked against the pinned parse contract: `grade=ambiguous` is already
  inside P-5's closed vocabulary; a MISMATCH-verdict ambiguous row therefore yields
  `mismatch_attest(A,R,"ambiguous")` and participates in defeat. That is the intended,
  fail-safe polarity — defeat withholds credit, it never asserts; grade-conditioned
  *discounting* of weak grades stays reserved (pipeline spec §13).

**A2 (2026-07-19) — write-time field hygiene (review finding F2, row 1505).** `model=` is
verbatim text from an **unauthenticated** emitter; a `|` inside any field value produces a
statement that parses loud-fail later (P-5), denying the whole idempotency scan — and, once
the pipeline exists, the world's entire defeat derivation — until superseded. The writer
therefore **refuses at write time**, with a diagnostic naming the offending field, any
field value containing the `|` delimiter (and any embedded newline). This is a writer
duty, not a parser relaxation: the parser's loud failure on such a row stays exactly as
pinned. Same fix pass: the parser rejects empty `model=`/`session=`/`basis=` values and
restricts `row=` to ASCII digits / segment trimming to ASCII whitespace, matching the SQL
twin's documented behavior (findings F4/F5 — producer-divergence latency, closed on the
Python side rather than waiting for the SQL side to disagree).

## License

Public Domain (The Unlicense).
