<!-- doc-attest-exempt: BANKED INVESTIGATION pinned as delivered, fresh-context Fable 2026-07-19
     (ledger estimate row 1495, slug context-migration-consult). Banked verbatim per the house
     consult practice (design/ORCH-CONSULT-REFUSAL-RECORDING-2026-07-17.md's own banner idiom);
     an ADR-0017 attestation is deferred until a commissioning act stabilizes what, if anything,
     of this becomes operative. Nothing here is implemented by virtue of being banked. -->

# FABLE-WORLD-CONTEXT-MIGRATION-CONSULT-2026-07-19 — banked investigation: extracting context from a dust-bound world to bootstrap its successor

> **Editorial note (this pass — A:B:C documentation review, 2026-07-18, this tracker's ledger row 1518):**
> This document's own filename and body date themselves 2026-07-19; per the same-day
> correction of record, ledger row 1517 (an orchestrator date drift, one day ahead of the
> actual date, caught by an independent fresh-context reader the same morning), the actual
> authoring date is **2026-07-18**. The filename is not renamed here — ADR-0005 Rule 8 treats
> a committed handle as a frozen record, and renaming it would break every existing citation
> into this document — and the frozen consult body below (§0–§7) is not retro-edited; this
> note is the correction. (Row 1517 records the drift and its affected media as a class
> without naming this file explicitly — the connection to this document is made here, by
> this note, not by the row.) It follows the same inline-bracketed convention
> [ADR-0017](../law/adr/0017-the-zero-context-reader.md)'s own dated corrections use. **§8 and
> §9 below are this pass's addition**, commissioned separately (row 1518) to generalize the
> consult's method beyond the one project it was checked against and to add a walkthrough for
> a reader who has never seen that project; each is clearly bannered where it begins.
> Everything from the next line down to the `---` immediately before §8 is the original
> Fable-authored consult, unedited and unaffected by this note.

**Status: BANKED INVESTIGATION, non-binding, Fable-authored fresh-context 2026-07-19, awaiting a future commissioning act.** This is not a spec. It recommends, it reserves questions, and it licenses nothing — no verb, no delta, no ceremony exists because this document exists. The standing constitutional rules ([CLAUDE.md](../CLAUDE.md) ORCHESTRATION: kernel/lineage and law/ move only under a Fable-authored, maintainer-ratified spec; runs are strictly linear, maintainer ruling 2026-07-11) are untouched and this document designs strictly inside them.

**The commission, verbatim (maintainer, ledgered as this tracker's row 1494):** *"It struck me that autoharn-panel is going to need a migration path, at least to preserve context. One thing I'm thinking is that we should probably Fable-consult for an investigation into a disciplined way to extract context from **a** autoharn-managed project so that, even if the actual ledger for structural reasons can't be delivered (guarantees would be void), at least enough context can be extracted to bootstrap the new world. What do you think?"*

**What this document is, in plain words.** An autoharn-managed project lives in a *world*: an isolated database habitat holding an append-only decision ledger, plus a project directory ([GLOSSARY.md](../GLOSSARY.md#world)). Worlds are never upgraded in place across a run boundary — a successor world is born fresh on the current kernel lineage, and the old world becomes *dust*: read-only evidence, never patched ([CLAUDE.md](../CLAUDE.md), runs-are-linear ruling 2026-07-11). But a long-lived world accumulates far more than its guarantees: standing rules its sessions load at start, invented procedures, a roster of working identities, open work, a registry of blessed tools. If a successor world is born knowing none of that, the project pays to relearn it — and if the old ledger were simply transplanted, the successor would inherit rows whose integrity guarantees are void in the new habitat, which is worse than ignorance because it manufactures false confidence. This investigation answers: what accumulated context IS, class by class, witnessed against the one real long-lived deployment (autoharn-panel); which classes should cross a world boundary and in what form; how the crossing is extracted, carried, and ingested so that everything that crosses is *evidence re-asserted by an accountable principal*, never *authority transported*; and what the successor's record must say so a zero-context auditor cannot mistake the one for the other.

**Consultant posture and evidence base (ADR-0018 discipline).** Fresh context; no working-session designs or candidate answers were received. Read in full before writing: [CLAUDE.md](../CLAUDE.md); [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) (including the 2026-07-02 Rule 2(a) closure-statement amendment), [ADR-0011](../law/adr/0011-mechanization-discipline.md), [ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md), [ADR-0013](../law/adr/0013-execution-integrity.md), [ADR-0014](../law/adr/0014-executor-second-opinion.md), [ADR-0017](../law/adr/0017-the-zero-context-reader.md), [ADR-0018](../law/adr/0018-consults-are-not-front-loaded.md); the [GLOSSARY](../GLOSSARY.md) world/run/birth-chain/delta/scratch-schema/stamp/principal/obligation entries; [design/FABLE-RESERVED-DESIGNS-2026-07-18.md](FABLE-RESERVED-DESIGNS-2026-07-18.md) (whole, §3.4 load-bearing); [design/FABLE-DEFEASIBILITY-ENVELOPE-2026-07-18.md](FABLE-DEFEASIBILITY-ENVELOPE-2026-07-18.md) I11; [bootstrap/new-project.sh](../bootstrap/new-project.sh) (the birth sequence as built, through the s45 chain and the s40/s43 birth acts); the kernel lineage headers as summarized in that script's own LINEAGE_CHAIN record (s21→s45, with the s40/s41/s42/s43 characterizations verified against the delta files' presence in [kernel/lineage/](../kernel/lineage/)). Probed read-only, outputs witnessed: `./pickup` on this tracker; the autoharn-panel deployment at `~/w/vdc/1/experience/autoharn-panel` — its `deployment.json`, `.claude/HOOKS.md` lineage record, `./pickup`, `./led standing`, `./led show 1729`, `./distance-to-clean`, and direct read-only `psql` against `experience`/`experience_kernel` (row-kind census, principal roster, migrate-row history, view inventory, ledger date span). No file outside this one was written; no ledger write was made anywhere.

---

## 0. The constitutional frame, verified rather than inherited

**Confidence: high** (structural claims checked against the built artifacts; one honest boundary named at the end of this section).

The commission's framing — the ledger structurally cannot be delivered into the successor; guarantees would be void — is the design key. Per the house discipline of verifying rather than deferring, here is *why* it is true, against the built kernel:

1. **The tamper-evidence chain is per-world by construction.** `s26-row-hash-chain` seeds every world with its own genesis seed, generated at scaffold time precisely so "two worlds' row-1 hashes differ" ([bootstrap/new-project.sh](../bootstrap/new-project.sh), genesis-seed block). Every row's hash covers its predecessor's. Transplanted rows either break the successor's chain at the splice or must be re-hashed under the successor's seed — and a re-hashed row is a *new* record wearing an old record's text; its tamper-evidence attests to the transplant event, not to the original writes.
2. **Stamps do not survive the crossing.** The [stamp](../GLOSSARY.md#stamp) HMAC binds a row to the session that wrote it, under a per-world secret that is deliberately never rotated or shared (the scaffold's own never-rotate seeding posture). The successor world has a different secret; the old stamps are verifiable only against the old world's secret and kernel. A transplanted stamped row would display stamp columns the new world's verifier cannot vouch for.
3. **The s40+ lineage makes history semantically untransplantable, not just cryptographically.** From s40, every write must be attributable to a registered principal whose registration is itself a prior ledger event; from s42, `row_hash` covers every column under a new law; from s43, the *only* write path is the typed-verdict boundary functions, and refusals are themselves committed rows in a completeness-oracle sequence. Rows written in a pre-s40 world (autoharn-panel's entire record — see §0.1) were not written under any of those laws. Inserting them into an s45-kernel world would require either bypassing the write boundary (the exact act s43 exists to make impossible for the granted role) or laundering them through it as fresh writes attributed to whoever runs the import — misattribution, the disease the s40/s41 family exists to end.
4. **The precedent is already banked.** [FABLE-RESERVED-DESIGNS §3.4](FABLE-RESERVED-DESIGNS-2026-07-18.md) resolved the competence-vocabulary migration question this way: no backfill, no mapping table — still-believed facts are **re-granted as fresh attributed events whose basis cites the prior world's record**, "which is the honest shape anyway, since a competence grant is a dated belief." [FABLE-DEFEASIBILITY-ENVELOPE I11](FABLE-DEFEASIBILITY-ENVELOPE-2026-07-18.md) composes: per-world facts carry force only over per-world facts; "no cross-world defeat exists to migrate, and none should… recorded so nobody invents cross-world transport to 'fix' it." This investigation generalizes that already-ratified-in-miniature shape from competence grants to every context class.

So the frame holds: **whatever crosses is evidence, never operative record.** A re-asserted row in the successor is a *new claim by a new-world principal, owned by that principal now*, for which the dust world's record is the citable basis — exactly as a citation in a paper carries the cited work's existence, not its authority.

**One honest boundary, named rather than absorbed.** "The ledger cannot be delivered" is specifically true of delivery *across a world boundary*. It is not a claim that kernel deltas can never reach a live adopter deployment at all: autoharn-panel itself was carried in place from its s30 birth head to s39 by `bootstrap/migrate.sh` with rehearsal, live-apply, and post-apply `verify-chain` passes (witnessed: panel ledger rows 176, 396, 405, 497, 1185; the repo's `./migrate` shim and `proposals/s29-inplace-migration/` are the live machinery and its open proposal). Whether the s40+ family is in-place-migratable for an adopter is a separate engineering question this consult did not attempt to settle (it was not the commission, and the structural obstacles in point 3 above are severe: a strict-attribution regime cannot be retroactively true of 1,700 rows written without it). What this investigation asserts is narrower and firm: **when** the successor is a new world — the succession the commission poses — the record does not cross, and context does, in the disciplined form below. If a future in-place s40+ migration is ever attempted, it is its own Fable-spec'd act and nothing here pre-blesses it.

### 0.1 The motivating instance, witnessed

Autoharn-panel (`~/w/vdc/1/experience/autoharn-panel`, world `experience` on the shared toy db) is a real, dense deployment: **1,725 ledger rows** (max id 1769) written 2026-07-15 → 2026-07-17, across 14 row kinds (decision 729, review 196, work_opened 153, work_claimed 152, work_closed 145, finding 97, assumption 82, verification 69, work_depends_on 51, commission 20, snag 15, work_violation_disposition 7, note 5, question 4); **13 registered principals** spanning all four agent classes (author/model, reviewer/subagent, commissioner/human, maintainer/human, bork/human, reviewer2/model, item-countersign/subagent, cycle-countersign/subagent, orchestrator/model, fixed-point-scout/subagent, fix-implementer/subagent, generic-consultant/subagent, scout-adversary/subagent); **29 durable-graded standing decisions** (the SessionStart-loaded operative rule set); a RESOURCES registry with a mandated-tier entry (the makespan-scheduler online client, complete with a self-correcting deployment-reach history); open closure debt (`./distance-to-clean`: 1 claimed work item, 2 open questions, 5 deferred-review items, total 8); and a git tree carrying its own law/adr subset, SPEC.md, docs/consults/, scout/review prompt templates, and two backflow documents. Its kernel head is s39-era (born on s30, migrated in place — `ledger_write`/`principal_standing` absent, `decision_grade`/`row_hash` present, witnessed by catalog query), which means succession to a current-lineage world is precisely the s40+ wall of §0 point 3. Everything in §1 is drawn from this record; where the panel had no specimen of a class, that is said.

---

## 1. The taxonomy: what a lived world accumulates, and what each class does at the boundary

**Confidence: high on the class inventory (it is read off a real record, not theorized); medium on individual crossing dispositions (each is a recommendation for the maintainer's future ruling, argued but not ratified).**

Each class below states: what it is, the panel specimen, and the crossing disposition. The disposition vocabulary, used consistently: **RE-ENACT** (crosses as a typed, attributed new-world act through the kernel's own machinery — registration event, resource declaration, work open); **RE-ASSERT** (crosses as a fresh decision-kind row whose statement restates the content and whose refs cite the extract and the dust rows); **CITE-ONLY** (never becomes an operative new-world row; remains readable evidence in the dust world, citable by anything that needs it); **NEVER** (deliberately does not cross in any form, and the reason is the guarantee structure itself).

### 1.1 Identity: the principal roster — RE-ENACT

The panel's 13 principals are its working society: not just names but purposes, agent classes, and division-of-labor conventions (a dedicated `item-countersign`, a `scout-adversary`, a `generic-consultant` for one-offs). This is context of the first rank — a successor world born with only the scaffold's author/reviewer/commissioner/write-boundary four would re-derive the roster expensively. Crossing: each still-needed principal is **freshly registered through the s40 ceremony** at (or shortly after) birth, purpose restated, the registration's statement citing the dust world's roster as basis. Principal *ids* never cross (they are per-kernel surrogate keys); the s41 `succeeds` relation does **not** apply cross-world (it is a typed edge between two principals in one kernel — cross-world succession is prose-in-basis, not an edge; minting a typed cross-world edge would require the old principal to exist in the new kernel, which is the transplant this whole frame forbids — see reserved question Q5). Not every principal crosses: a roster walk at ingestion decides which identities the successor actually needs, and each *omission* is named in the ingestion record (the panel's own row-1729 procedure demands exactly this fresh-roster-walk discipline within one world; the boundary crossing inherits it).

### 1.2 Standing decisions: the operative rule set — RE-ASSERT, with per-row re-judgment

The panel's 29 durable-graded rows are the closest thing a world has to session-loaded law: execution-autonomy rules, raw-SQL prohibitions extended from writes to reads, scout-dispatch conventions, git-transaction policies for source-touching closes, rendering rules for schedules (witnessed via `./led standing`). This is the class the maintainer's "at least to preserve context" most directly names. Crossing: each still-believed standing decision is re-asserted as a fresh decision row (graded durable where the successor's kernel supports grading), statement restated *in full* — never "see old row N" alone, which would make the successor's operative law unreadable without the dust world, an [ADR-0017](../law/adr/0017-the-zero-context-reader.md) violation at the record layer — with refs citing the extract and the originating dust row. Two disciplines attach: (a) **re-assertion is re-judgment** — a rule that no longer holds is deliberately dropped, and the drop is itself recorded (a one-line ingestion note naming the dust row and why it does not cross), because a silent drop is indistinguishable from an oversight; (b) **kernel-subsumption check** — some panel-invented rules exist because the panel's s39-era kernel lacked machinery the successor's lineage now provides natively (see §1.3's specimen); re-asserting a manual emulation of a mechanism the new kernel enforces would be cargo ceremony, so each candidate is checked against the successor's lineage first and, where subsumed, crossed as "superseded by kernel: sNN" instead of re-asserted.

### 1.3 Procedures and invented practices — RE-ASSERT (a distinguished subclass of 1.2)

The panel invented governance the upstream project never wrote: the **row-1729 role-name-governance procedure** (a four-step proposal/countersign/registration-gate/ledger-only-filing protocol for minting new principal names, read in full via `./led show 1729`) and the **row-1758 cycle execution algorithm v3** (a ten-step scout/adversarial-review/decompose/implement/countersign pipeline with explicit rejected alternatives). These are the clearest proof that a deployment's context is partly *original work product* — practices with rationale, rejected-alternative records, and named exception handling — not merely configuration. They cross as re-asserted standing decisions like §1.2, with one addition each way: the **rationale and rejected alternatives cross with the rule** (a procedure stripped of its "rejected: kind=commission per proposal, because…" reasoning invites the next session to relitigate it), and the subsumption check of §1.2(b) bites hardest here — row 1729's registration-gate step, for instance, partially anticipates what the s40 registration ceremony and the reserved competence machinery do natively, so its re-assertion in an s45 world should be *reconciled with* the kernel's own ceremony, not layered on top of it blindly. Also in this class: the panel's ADR-0005-style filing-home conventions (docs/consults/ per consult; backflow files per upstream tool) — these live in git and cross with the repository (§1.9), but the *decisions establishing them* are §1.2 rows.

### 1.4 Open work: items, dependencies, claims — RE-ENACT (as fresh opens), with debt written off by name

Witnessed: 1 open+claimed item, 5 deferred-review items, 2 open questions, plus rollup families of never-estimated children. Open work crosses as **freshly opened work items** in the successor (`led work open`), titled per the panel's own unit-of-independent-resumption rule (its CLAUDE.md point 1), refs citing the dust items. What does **not** cross as-is: *claims* (a claim binds a session that is gone — items cross unclaimed), *dependency edges* (re-declared only where both endpoints crossed and the dependency is still believed), and — critically — **debt**. Review-gap debt, deferred-review flags, and violation dispositions are creatures of the dust world's obligation machinery; the successor's clean-state views must start honest at zero. A dust item that died with outstanding review debt crosses, if it crosses, as a fresh item whose *description says so* ("closed-unreviewed in the predecessor; re-verification is part of this item's scope"), or it is written off with the write-off named in the ingestion record. Debt is never silently laundered into a clean successor.

### 1.5 Open questions — RE-ENACT

The panel's two open questions (ids 1343, 1408) are addressed to the commissioner/maintainer and remain genuinely open. They cross as fresh `led ask` rows citing origin. A question the successor's context makes moot is dropped by name, like §1.2(a).

### 1.6 The resources registry — RE-ENACT, with reach re-witnessed

The panel's RESOURCES surface (blessed/mandated/forbidden tiers; the mandated makespan-scheduler entry with reach, proves, and guidance fields) is high-value context — it encodes paid-for tooling lessons. It crosses by **re-declaration** in the successor, with one hard rule the panel's own record teaches: the witnessed entry's guidance field *corrects its own earlier row's stale deployment caveat* ("NOW ACTUALLY DEPLOYED AND REACHABLE (corrects row:1150's not-yet-deployed caveat)") — reach claims decay even *within* one world. So a crossing resource declaration carries its `proves:` history as citation but its `reach:` as **UNWITNESSED until re-probed in the successor's own environment**, stated in the declaration itself. The forbidden tier crosses with its prohibitions' rationale (a prohibition whose reason is lost invites silent exceptions — the exact failure the panel's CLAUDE.md point 2 guards).

### 1.7 Competence and track record — CITE-ONLY by default; optionally RE-ENACT as competence grants

The panel record contains real reputation: 196 reviews with verdicts, an independent RCA correctly taken away from a conflicted author (standing rows 399–400), success-story rows recording when a discipline caught a real defect, retrospective findings. None of this transports as *standing* — a review verdict is a guarantee-adjacent fact whose force is the dust world's SoD machinery, and §1.4 already rules debt/discharge non-crossing; the symmetric rule holds for credit. The default is CITE-ONLY: the dust record remains queryable and anything in the successor may cite it. The *optional* stronger form, available once the reserved competence-band designs land ([FABLE-RESERVED-DESIGNS §3](FABLE-RESERVED-DESIGNS-2026-07-18.md)): still-believed competences re-granted as fresh s41 `principal_competence_granted` events whose `basis` cites the dust record — precisely §3.4's ratified-in-miniature shape, and the one place this taxonomy's crossing machinery was *already* designed before this consult existed. Whether to exercise it is reserved question Q4.

### 1.8 Estimates and actuals — CITE-ONLY, permanently

Estimate rows and their actuals are, by standing ruling, diagnostic-grade forever (the action-stream-is-evidentiary-basis principle: token/cost accounting is never guarantee-grade) and retrospective-only (the panel's ROLLUP banner restates it: "never gates, never polices"). Calibration learned in the dust world may inform a successor's estimate rows as cited prior evidence in their free text; no number crosses as operative. Nothing here needs machinery.

### 1.9 Domain artifacts: the git tree — crosses with the repository, outside this discipline's scope except for one seam

SPEC.md, the backend/frontend source, docs/consults/, prompt templates, law/adr subset, attestations — these live in git, and git's own history is their provenance; world succession does not touch them (the same project directory can simply continue, pointed at the successor world by a new `deployment.json`). The one seam this discipline owns: the tree is full of `row:N` citations into the dust ledger (both prompt-template files, the backflow docs, consult records). After succession those citations are *dust citations* and must remain resolvable as such — see §4's citation convention. No rewrite of historical documents (ADR-0005 Rule 8 / ADR-0017's point-in-time exemption); documents *touched after* succession disambiguate their row citations per §4.

### 1.10 Commissions — NEVER (the successor gets its own founding act)

The panel's 20 commission rows, including its founding ask with its s25 FULL/LAZY signing semantics, are the dust world's own charter. A commission is denominated on its world; the successor world's first commission is the succession act itself, freshly signed, citing the predecessor's founding commission as history. Transplanting a commission would transplant the one row class whose entire meaning is "this world's mandate."

### 1.11 Apparatus, secrets, and configuration — NEVER (secrets) / RE-ENACT (settings, by scaffold + explicit widening)

The stamp secret and chain genesis seed are per-world by design and never cross (§0 points 1–2). `apparatus.json` mechanism switches, the governed-files set, and hook wiring are re-established by the scaffold with the successor's own explicit flags; the dust world's settings are read as *advice* at scaffold time (e.g. the panel's doc_attestation OFF-with-reasons record, standing row 410, is exactly the kind of paid-for configuration lesson worth carrying as a §1.2 re-assertion: "observe mode produced 155 vendor-file false positives; fix the tally before arming").

### 1.12 Refusals, violations, snags, and the failure record — CITE-ONLY

The dust world's snag rows, violation dispositions, refusal history, and RCA substrates are evidence of the highest audit value and zero operative value. They stay where their chain vouches for them. The *lessons* extracted from them, where still operative, are already §1.2/§1.3 rows in the dust world and cross through those classes — the failure record itself does not.

---

## 2. The extraction discipline

**Confidence: medium-high** — the shape follows directly from the self-application law and the witnessed verbs, but no extraction has ever been performed, so this is design, not experience.

### 2.1 Extraction is the predecessor's last ledgered act, not an archaeology of dust

The single most consequential design choice, and it falls out of the timeline: at the moment succession is decided, the predecessor world is still *live* — dust status begins at the boundary, not before it. Therefore extraction should run **inside the predecessor, as its final ledgered work item**, not as an outside read of an already-settled corpse. What this buys, for free, from machinery that already exists: the extraction act is itself attributed (a registered principal ran it), stamped, hash-chained, and — where the predecessor's kernel supports it — countersignable. The extract artifact's provenance claim then reduces to "the predecessor's own chain vouches for the act that produced me," which is the strongest statement available without any new integrity machinery. An extract produced *after* settlement (the fallback, e.g. for a world that died unexpectedly) is still possible — everything below is read-only — but it forfeits this property and must say so on its face: it is an outside reading of evidence, attributed only in the *successor's* record. This asymmetry is reserved question Q1.

### 2.2 A scripted verb, because the self-application law says so — and because hand-curation alone is the known failure

The self-application ruling (CLAUDE.md 2026-07-09: "no operator procedure ships as prose steps + hand-pasted SQL/bash where a scripted, witnessed verb is possible — run 2's world was broken at birth by exactly that gap") decides the transport question before it is asked: extraction is an operator verb (working name only: `extract-context`), read-only against the ledger, joining the repo-root verb surface if commissioned. Its mechanical core is deliberately boring — the class queries already exist as views and verbs: `standing_decisions` (§1.2/§1.3), `question_status` open rows (§1.5), the `work_item_*` views for open/claimed/deferred (§1.4), the kernel `principal` roster (§1.1), the RESOURCES rows (§1.6), the founding commission and chain head for the provenance block (§2.3). What the verb must NOT attempt: the *judgment* half — which standing decisions still hold, which principals the successor needs, which rules the new kernel subsumes. That is ingestion-side re-judgment (§3), performed by an accountable principal and recorded per item. The division is exact: **extraction is mechanical and complete per class (no silent narrowing — every member of each crossing class is in the extract); curation is ingestion-side, attributed, and names every drop.** A hand-curated extract would concentrate the ADR-0013 Rule 3 hazard (scope quietly narrowed to what the extractor felt like carrying) at the one point where nobody in the successor could ever detect the omission — the class query cannot lie about membership; a person or model assembling the list by hand can, without knowing it.

### 2.3 The artifact and its integrity properties

One artifact, two registers in one file (machine-readable body, prose preamble — the ADR-0017 zero-context bar applies to it like any document):

- **Provenance block**, written by the verb, never by hand: predecessor world name, schema/kern, ledger row span and count, chain high-water id and head hash, `verify-chain` output verbatim as witnessed at extraction time, the extracting autoharn commit (the instrument-version discipline the scaffold already applies via AUTOHARN_COMMIT), timestamp, extracting principal, and — in the §2.1 in-world mode — the id of the extraction act's own ledger row.
- **Per-item records**: for every extracted item, the dust row id(s), the row kind, the verbatim statement (never a paraphrase — the commissions-verbatim censure generalizes: a paraphrased extract narrows scope invisibly), the row's own refs, and its taxonomy class per §1. No disposition field at extraction time beyond the class default: disposition is ingestion's column to fill.
- **What vouches for what, stated exactly:** the dust world's chain vouches for the *rows the extract quotes* (anyone can re-read them at the cited ids and re-run `verify-chain` against the dust schema, which remains queryable read-only forever). The extract file itself is vouched for by (a) the predecessor's ledgered extraction act citing it, in the §2.1 mode, and (b) git, once committed in the project tree. **Nothing vouches for completeness of judgment** — only for mechanical completeness per class (the verb's queries) — and the extract's preamble says so, so the artifact cannot smuggle authority: it is a certified *reading*, not a certified *truth*, and every operative consequence of it is created fresh at ingestion by someone accountable.

The known adjacent trap, named so the eventual builder avoids it: signing/attestation machinery beyond the above is **deliberately not proposed** — key generation and signing are under a standing deferral ruling, and the chain+git+ledgered-act triple already covers the provenance need without it.

---

## 3. The ingestion ceremony

**Confidence: medium** — this is the least-precedented section; the birth sequence it extends is witnessed, but no succession ingestion has ever run.

### 3.1 Ordering: birth first, unchanged; ingestion second, as the first commissioned work

The scaffold's birth sequence ([bootstrap/new-project.sh](../bootstrap/new-project.sh) --new-world: full lineage apply, secrets, the s40/s43 birth acts — author registration with the genesis exception, dual standing declarations, reviewer/commissioner/write-boundary ceremony) is **not modified**. The successor is born exactly as any world is born; succession changes nothing about birth, which keeps the scaffold's one job pure and keeps ingestion out of the un-attributable pre-first-principal window. Ingestion then runs as the successor's first real work: a work item (or small family), opened under the successor's own founding commission, whose deliverable is the re-enactment/re-assertion pass over the extract.

### 3.2 Who performs it, and under what attribution — the post-s40 answer

Every ingestion write is an ordinary attributed write through the s43 boundary; no special actor and no bypass. Concretely: the **operator** runs the scaffold and hands the extract to the first session; the **successor's orchestrating principal** (the world's author-standing principal, or a registered orchestrator per the roster it re-enacts first) performs the re-assertions, each row carrying its own actor. The ordering inside ingestion is forced by dependency: **(1) principals first** (§1.1 — later re-assertions may need to be written by, or refer to, roster identities), **(2) resources and standing decisions/procedures** (§1.6, §1.2, §1.3 — the operative context sessions will load), **(3) open work and questions** (§1.4, §1.5), **(4) optional competence grants** (§1.7, if Q4 is answered yes and the machinery exists). Each item gets one of four recorded outcomes, filling the extract's disposition column in the successor's record: RE-ENACTED (with the new row id), RE-ASSERTED (id), SUPERSEDED-BY-KERNEL (which sNN and why), or DROPPED (why). The complete disposition record — every extract item accounted for, no umbrella claims — is the ingestion item's closing witness, in exactly the WITNESSED/REFUSED/UNEXERCISED reporting discipline the orchestration contract already mandates.

### 3.3 Ceremony weight: one countersign over the batch, not per-row ritual

The runs-are-linear ruling's own coda governs the temptation here: "an operator step that is ritual rather than load-bearing is deleted, not documented." Per-row countersigning of a hundred re-assertions would be ritual. The load-bearing check is singular: *did the ingestion's judgment pass survive independent eyes* — one review, by a distinct principal, over the disposition record as a whole (with the extract beside it), attesting that drops are named, statements are verbatim-faithful, and nothing crossed as authority. That is one review row on the ingestion work item's close, riding machinery every world already has. Whether even that is required or merely recommended is the maintainer's call (reserved question Q3).

---

## 4. The honesty surface: what the successor's record must say

**Confidence: high** — this section is mostly the composition of rules that already bind (ADR-0017, the claims-carry-witnesses contract, ADR-0013's amendment on completion-claim shape).

The audit hazard succession creates is specific: a zero-context reader of the successor's ledger sees a dense day-one record — dozens of standing decisions, a full roster, declared resources — and may read it as *earned* in this world. Four obligations close that gap:

1. **Re-assertions are marked in-band, uniformly.** Every crossing row's statement carries a fixed, greppable marker phrase (settled at commissioning; e.g. a leading `re-asserted from <world>:` clause) plus refs to the extract and dust row ids. The marker is content, not metadata — it survives every view, export, and quotation. A reader who sees any one such row can find all of them.
2. **The succession itself is one loud, early row** — the successor's ingestion work item and a decision row naming: predecessor world, extract artifact and its provenance block, and the sentence that does the honest work, spelled here so no future author has to re-draft it under pressure: *"Context below is re-asserted from the predecessor's record as evidence. No guarantee transports: the predecessor's hash chain, stamps, review discharges, and refusal record vouch only for the predecessor's own rows, verifiable read-only at `<schema>`; every re-asserted row is a fresh claim owned by its new-world actor from its own timestamp forward."*
3. **Verification language stays world-scoped.** "Verified in the predecessor (dust row N)" is a legal citation; bare "verified" over a fact whose witness lives in the dust world is exactly the umbrella/unverified-claim shape ADR-0013's 2026-07-02 amendment forbids. A re-asserted verification-dependent claim is UNWITNESSED in the successor until re-witnessed there — the same rule §1.6 applies to resource reach.
4. **The paper trail points both ways.** The successor's provenance record (its HOOKS.md/CLAUDE.md PROVENANCE block, which the scaffold already writes for birth facts) names the predecessor; the predecessor's final rows (the §2.1 extraction act and a closing "succeeded-by" decision row, if the world closes in an orderly way) name the successor. Documents in the shared git tree that are touched after succession qualify their `row:N` citations with the world (`<world> row:N`); untouched historical documents stay verbatim per ADR-0005 Rule 8, with the succession row itself serving as the reader's disambiguation key (rows cited in documents dated before succession are predecessor rows).

---

## 5. What deliberately does NOT cross — the named list

**Confidence: high.** Stated as a closed enumeration so absence is a decision, not a gap (the ADR-0000 closure-statement discipline applied to a design's negative space):

- **Ledger rows as rows.** No INSERT of predecessor rows into the successor, ever, under any encoding (§0).
- **The hash chain, stamps, and their verification standing** (§0 points 1–2). They remain valid *about the dust world, in the dust world*.
- **Review discharges, countersigns, review-gap state, and all closure debt — credit and debt alike** (§1.4, §1.7). The successor's SoD ledger starts at zero in both directions.
- **Refusal/violation/snag history and commission rows** (§1.10, §1.12).
- **Secrets** — stamp secret, genesis seed (§1.11).
- **Principal ids, typed relations (`succeeds` et al.), claims, and dependency edges as edges** (§1.1, §1.4) — identities and dependencies cross only by fresh enactment.
- **Estimates/actuals as operative numbers** (§1.8).
- **Authority as such.** The residual class, named last because it is the point: nothing in the extract binds anyone in the successor until a new-world principal re-asserts it and thereby owns it. A dust rule nobody re-asserts is not "lost" — it is *readable forever and operative nowhere*, which is what settled evidence means.

---

## 6. Reserved questions for the maintainer

Each is independently answerable; none blocks another. Per the decision-queue bar these are load-bearing judgment calls, not trivia.

**Q1 — Extraction timing.** Shall extraction be defined as the predecessor world's own final ledgered act (§2.1's recommended shape, buying attributed/stamped/chained provenance from existing machinery), with the after-settlement outside read available only as a named degraded fallback for worlds that die unexpectedly?

**Q2 — The verb.** Shall a read-only extraction verb (§2.2) be commissioned onto the operator surface — a scripted, witnessed alternative to hand-curated extraction — with its mechanical scope fixed as "complete per crossing class, zero judgment"? (This is an ordinary tool build, not kernel work; Sonnet-executable under a spec.)

**Q3 — Ingestion ceremony weight.** Shall the ingestion disposition record require one countersign by a distinct principal over the whole batch (§3.3), or ride uncountersigned as ordinary attributed work? (No per-row ceremony is proposed under either answer.)

**Q4 — Track record crossing.** When the competence-band machinery exists, shall still-believed competences cross as fresh s41 grants with dust-citing basis (the [FABLE-RESERVED-DESIGNS §3.4](FABLE-RESERVED-DESIGNS-2026-07-18.md) shape), or shall track record remain CITE-ONLY permanently?

**Q5 — Typed succession record.** Is prose-in-provenance (the §4.4 two-way pointers) sufficient for world succession, or should a future kernel spec mint a typed cross-world descent record (e.g. a deployment.json field plus a dedicated first-row kind)? This consult recommends prose now — a typed record is additive and can be specced later without rework — but flags that a typed field is what would let tooling (pickup, the panel SPA) render lineage mechanically.

**Q6 — The panel's own succession.** Separately from the general discipline: when autoharn-panel actually crosses, does the maintainer want the in-place-migration question of §0's honest boundary (can s40+ reach the live panel at all?) investigated first, or is new-world succession the settled route for it? This consult takes no position beyond having named the boundary honestly.

---

## 7. Honest limits of this investigation

- **The panel was fully reachable read-only**; nothing in the commission's fallback ("reason from this tracker's ledger as stand-in") was needed. All panel claims above are witnessed against its live record as of 2026-07-19.
- **No extraction or ingestion has ever been performed**; §2 and §3 are design reasoning from witnessed machinery, not experience. The first real succession will find friction this document did not (most likely in §1.2's kernel-subsumption judgment and §3.2's ordering).
- **Row coverage is sampled, not total**: the taxonomy is grounded in the panel's full kind census, complete standing-decision set, complete principal roster, complete closure-debt surface, and targeted deep reads (rows 176, 396, 405, 497, 1185, 1729, 1758, and the pickup-surfaced standing rows) — not a read of all 1,725 rows. A class present only in unread rows would be missing here; the kind census makes that unlikely but not impossible.
- **The in-place s40+ migration feasibility question is explicitly not settled** (§0, honest boundary; Q6). The structural obstacles are stated; no migration was attempted or rehearsed.
- **Kernel delta knowledge is header-level**: s40–s45 semantics were taken from the scaffold's LINEAGE_CHAIN characterization, the reserved-designs document's DDL-verified analysis, and the glossary — not from a line-by-line read of the delta SQL. Where §0 point 3 leans on specifics (write-boundary exclusivity, hash-law change), those are the deltas' own header claims, independently corroborated by the panel-side catalog probe (functions absent there, present in the current chain).

## 8. Generalizing beyond autoharn-panel — this pass's addition (A:B:C doc review, 2026-07-18, this tracker's ledger row 1518)

**What this section is, and what it is not.** Everything above this heading (§0–§7) is the
original Fable-authored consult, banked verbatim and never retro-edited per
[ADR-0005](../law/adr/0005-documentation-discipline.md) Rule 8 (see also the editorial note at
the top of this document). This section is a later, separately-authored addition, commissioned
specifically to generalize the consult's method beyond the one project it was witnessed
against — the maintainer's own words, this tracker's ledger row 1518: *"[the migration doc]
needs an A:B:C pass that additionally attempts to generalize it and add an FAQ/Walkthrough for
people not familiar with the autoharn-panel project."* It states nothing the original consult's
own words do not already ground; where it goes further than the source text, that is flagged
explicitly as extrapolation for the maintainer to adjudicate (§8.3), never presented as the
consult's own conclusion.

### 8.1 The consult is already framed generically — the panel is its witness, not its scope

Worth surfacing because it is easy to miss on a single read: the maintainer's original
commission, quoted verbatim near the top of this document, already asks for a discipline
general to *"**a** autoharn-managed project"* (emphasis in the source quotation) — not
autoharn-panel specifically. The consult's own "Consultant posture and evidence base" paragraph
makes the matching point about its evidence, calling the panel deployment *"the one real
long-lived deployment"* it could check its reasoning against, not the boundary of what the
reasoning describes. Generalizing this document, then, is less inventing new scope than making
explicit a generality the consult already claimed for itself and grounded in the one concrete
case that existed to check it against.

The taxonomy in §1 is a case in point: every one of its twelve classes (§1.1–§1.12) is defined
by a generic kernel row kind or generic project artifact that any current-lineage
autoharn-managed project has by construction of being scaffolded from
[`bootstrap/new-project.sh`](../bootstrap/new-project.sh) — principal rows, decision rows
graded durable, work-item rows, question rows, a RESOURCES registry, commission rows,
`apparatus.json`, the git tree — never by anything panel-specific. Panel's own numbers (1,725
rows, 13 principals, 29 standing decisions, the row-1729 and row-1758 procedures) are cited
throughout §1 as *specimens of the classes*, not as the classes' definitions; a different
project would populate the same twelve slots with its own rows and, plausibly, find some slots
empty — the consult itself already names this possibility for the class it is built on: *"where
the panel had no specimen of a class, that is said"* (§0.1).

### 8.2 The four load-bearing pieces the commission named, restated for any project

The maintainer's commission named four things this generalization must abstract — the context
classes, re-assertion at birth, the extract artifact, and the guarantees-void honesty surface.
Each is already stated in generic terms in the original text; restated here without adding a
claim the source does not make:

- **The context classes (§1).** The twelve-class taxonomy and its four-way disposition
  vocabulary (RE-ENACT / RE-ASSERT / CITE-ONLY / NEVER, defined in §1's own opening paragraph)
  describe any world's accumulated context, not panel's specifically. What is project-specific
  is only the *census* — which classes are populated, and how densely — never the classes or
  the disposition logic that sorts them.
- **Re-assertion at birth (§3).** The ingestion ceremony's shape — birth left unmodified,
  ingestion running as the successor's own first commissioned work item, ordered
  principals-then-resources-then-open-work-then-competence (§3.2) — rests only on the current
  kernel lineage's machinery: the s40 registration ceremony, the s43 write boundary, and the
  founding-commission convention every scaffolded world gets. Any project born on that lineage
  gets the same ceremony shape; nothing in §3's argument depends on panel by name.
- **The extract artifact (§2).** The provenance-block-plus-per-item-records design (§2.3) and
  the mechanical-extraction / judgment-at-ingestion split (§2.2) are stated throughout over "the
  predecessor" and "the successor" — generic roles, not panel and its eventual successor by
  name. The verb itself (working name `extract-context`, §2.2) does not exist yet, for panel or
  for any other project; see §9 below for what that means for a reader who wants to try this
  today.
- **The guarantees-void honesty surface (§4).** All four obligations there (in-band
  re-assertion markers, one loud succession row, world-scoped verification language, two-way
  provenance pointers) are stated against "the successor's ledger" and "the predecessor,"
  never against panel by name, and bind identically wherever this discipline is exercised.

### 8.3 Where the consult is narrower than "any project" — named, not smoothed over

One place the original text is genuinely panel-specific, not merely panel-illustrated: §0's
argument for *why* the ledger cannot cross rests in part on the panel's kernel being pre-s40
(§0.1: *"born on s30, migrated in place… which means succession to a current-lineage world is
precisely the s40+ wall of §0 point 3"*). Of §0's four sub-arguments, points 1–2 (the per-world
hash-chain seed, the per-world stamp secret) and point 4 (the FABLE-RESERVED-DESIGNS §3.4
precedent — a general design-pattern argument for re-asserting rather than transplanting,
with no s40-timing dependency of its own) are stated as, or reduce to, structural or
design-pattern properties that hold regardless of when the predecessor was born — genuinely
general, already. Point 3 alone (the s40+ attribution regime) is argued specifically against
a *pre-s40* predecessor crossing to a *post-s40* successor, which is the panel's exact, and so
far only witnessed, situation.

**Extrapolation, flagged for the maintainer to adjudicate — not a conclusion the consult itself
draws:** neither the original text nor this addition knows whether the argument weakens for a
*successor-to-successor* crossing where both worlds are already post-s40/s41/s43 (a project
scaffolded after this lineage matured, later succeeding itself a second time). The hash-chain
and stamp arguments (points 1–2) still forbid row transplant unconditionally in that case — they
are cryptographic properties, not consequences of a regime mismatch. But point 3's specific
claim — *"rows written in a pre-s40 world… were not written under any of those laws"* — describes
a regime mismatch that would not exist between two already-post-s40 worlds, and whether that
changes anything about the *recommended disposition* per §1 class, or only removes one of
several independent reasons a NEVER disposition already held on other grounds, is not settled
by the original text and is not settled here. Flagged, not guessed.

---

## 9. FAQ / Walkthrough for a reader who has never seen autoharn-panel — this pass's addition (A:B:C doc review, 2026-07-18, this tracker's ledger row 1518)

**How to read this section.** Question-shaped entries, each answered from the material above
with a citation to the section it is grounded in. Where a command or output is shown, it is
marked either **WITNESSED** (it was actually run and produced the shown output) or
**UNWITNESSED / design-only** (the described tooling does not exist yet; the "what you type"
text is this document's own design proposal, never a transcript). Nothing in this section is
WITNESSED, because no extraction or ingestion has ever been performed against any world,
autoharn-panel included (§7: *"No extraction or ingestion has ever been performed"*) —
every entry below that shows a command or output carries the UNWITNESSED label at the
point of showing; entries that only restate the consult's own analysis carry no label,
because they show no behavior to witness. The label is never omitted where a
what-you-type/what-you-should-see format could imply a tool that does not yet exist.

**What is a "world," and why does anything need to "cross" between them?**
A world is one autoharn-managed project's isolated database habitat — its append-only decision
ledger, plus its project directory — ([GLOSSARY.md](../GLOSSARY.md#world)). Worlds are never
upgraded in place across a run boundary: when a project needs a new kernel lineage, a fresh
world is born, and the old one becomes *dust* — read-only evidence from then on
([CLAUDE.md](../CLAUDE.md), runs-are-linear ruling, quoted in this document's own opening
paragraph, "What this document is, in plain words"). A long-lived world accumulates working context — rules,
roster, procedures, open work — that the new world does not automatically have. This whole
document is about what to do with that accumulated context (§0's opening paragraph).

**Why can't the old ledger just be copied into the new world?**
Because the guarantees a ledger row carries are per-world by construction, not per-project: the
tamper-evidence hash chain is seeded fresh per world, the stamp binding a row to its writing
session is signed with a per-world secret that is deliberately never shared, and — for any
project on the current kernel lineage (s40 onward) — every write must trace to a principal
registered *in that world*, through a write boundary an ordinary session cannot bypass. Copying
rows in would either break the chain, display a stamp the new world cannot verify, or require
laundering the rows through the write boundary as if the importing session had written them
itself — a misattribution, not a migration. §0 points 1–4 work through each of these in detail,
with citations to the specific kernel-lineage deltas involved.

**So what actually gets carried over, and how?**
Nothing is copied as a row. What crosses, crosses as a *fresh, attributed act in the new
world* — a new principal registration, a new decision row, a freshly opened work item — whose
content restates the old context and whose references cite the old world's rows as the *basis*
for the new act, never as its authority. §1's twelve-class taxonomy sorts everything a world
accumulates (roster, standing rules, invented procedures, open work, resources, track record,
estimates, git tree, founding commission, configuration, failure record) into four dispositions:
**RE-ENACT** (a fresh typed act — e.g. re-registering a principal), **RE-ASSERT** (a fresh
decision row restating the content), **CITE-ONLY** (stays readable in the dust world, never
becomes an operative new-world row), or **NEVER** (does not cross in any form) — defined in
§1's opening paragraph, applied class-by-class in §1.1–§1.12, and grounded there in what
autoharn-panel — the one project this discipline has been checked against so far — actually had
of each class. §8 above explains why the classes themselves are not specific to that one
project.

**What definitely does NOT cross, no matter what?**
§5 gives the closed list: ledger rows as rows; the hash chain and stamps (valid only about the
world that made them); review discharges and closure debt, credit and debt alike (a new world's
accountability bookkeeping starts at zero); refusal, violation, and snag history; the founding
commission; secrets; principal database IDs and typed relations between them; and
estimate/actual numbers as anything but retrospective color. The residual class, and the point
of the whole document: **authority never crosses** — a rule from the old world binds nobody in
the new world until someone accountable in the new world re-asserts it and thereby owns it
themselves (§5's closing bullet).

**Is there a command I can run today to pull context out of a dying world?**
No. **UNWITNESSED — this tooling does not exist.** §2.2 names a working-name-only verb,
`extract-context`, and specifies what it would need to do (read-only, mechanically complete per
taxonomy class, zero judgment baked in), but it has not been built, has not been commissioned
onto the operator surface, and no extraction has ever been run against any world, panel
included. Building it is reserved question Q2 in §6, awaiting a maintainer decision on whether
to commission it at all.

**If it existed, what would running it look like? (Design walkthrough — UNWITNESSED throughout;
nothing below has executed.)**
Assembled from §2.2's mechanical-core description and §2.3's artifact fields — this is the
document's own design proposal for the shape a first version would take, not a transcript of a
real run, because none exists:

1. *What you would type* (working name only, per §2.2): `./extract-context > extract.json`, run
   from the predecessor world's own project directory while that world is still live — §2.1's
   argument for running extraction as the predecessor's own last ledgered act, so the extraction
   itself is attributed, stamped, and chain-covered, rather than an outside read of an
   already-dead world.
2. *What you should see* (per §2.3's stated fields — a description of intended structure, not an
   example the tooling has ever produced): a single artifact with two parts — a **provenance
   block** (predecessor world name and schema, ledger row span and count, the chain's head hash,
   a verbatim `verify-chain` output, the extracting commit, timestamp, and the extracting
   principal), and a list of **per-item records**, one per extracted row, each carrying the dust
   row's id, its row kind, its *verbatim* statement (never paraphrased — §2.3 is explicit that a
   paraphrase silently narrows scope), its own references, and which of §1's twelve taxonomy
   classes it belongs to. No disposition beyond the class default is filled in at this stage —
   that is ingestion's job, next.
3. *What ingestion would look like*: per §3, a work item opened in the *new* world under its own
   founding commission, its deliverable a re-assertion pass over the extract — principals first,
   then resources and standing decisions, then open work and questions, then, optionally,
   competence grants (§3.2's ordering). Each extracted item ends with one of four recorded
   outcomes: RE-ENACTED, RE-ASSERTED, SUPERSEDED-BY-KERNEL (naming which kernel delta subsumed
   it), or DROPPED (naming why) — filled in by an accountable principal in the new world, never
   automatically.
4. *What the new world's record would say about all this*: per §4, the succession is one loud,
   early decision row in the new world naming the predecessor, the extract, and a fixed honesty
   sentence the document spells out verbatim at §4 point 2 so no future author has to draft it
   under pressure — stating plainly that nothing below it in the ledger is a guarantee inherited
   from the old world, only a fresh claim made by a new-world actor.

**Do I need to have used autoharn-panel to follow any of this?**
No. Panel is cited throughout §0–§7 as the one deployment this discipline has actually been
checked against — a witness, not a prerequisite. §8 above works through why the method itself
does not depend on panel-specific facts; the panel numbers quoted in §0.1 and elsewhere (1,725
rows, 13 principals, and so on) are that one project's own census, offered as a worked example,
not anything your own project needs to match.

**Does this apply to my project even if it was never migrated from an older, pre-s40 world?**
Mostly, with one open point. The per-world hash-chain and stamp arguments (§0 points 1–2) apply
to any world crossing to any other world, regardless of when either was born — cryptographic
properties of the kernel, not consequences of panel's specific pre-s40 history. Whether the
*attribution-regime* argument (§0 point 3, panel's specific "written under different laws"
situation) still applies, in full or in a weaker form, to a crossing between two already-current-
lineage worlds is not settled by the original consult and not settled here — see §8.3's flagged
extrapolation.

**My old world had a rule I don't think is true anymore — do I have to carry it forward?**
No, and carrying it forward unexamined would be the wrong move. §1.2 calls this "re-assertion is
re-judgment": each candidate is checked against whether it still holds and against whether the
new kernel already provides natively what the old rule was manually emulating (the
"kernel-subsumption check"). A rule that no longer holds, or that the new kernel now does for
you, is deliberately dropped — and the drop itself is written down, with the reason, so it reads
as a decision rather than an oversight (§1.2 point (a)).

**Who is allowed to decide what crosses?**
Whoever performs the ingestion writes each re-assertion under their own attribution, through the
new world's ordinary write boundary — there is no special bypass actor (§3.2). The consult
recommends, but does not mandate as built, a single independent review over the whole batch of
disposition decisions at the end, rather than per-row ceremony (§3.3); whether even that single
review is required is left to the maintainer as reserved question Q3 (§6).

**Where do I raise a question this document doesn't answer, or ask for the missing tooling to be
built?**
§6 lists six reserved questions (Q1–Q6) the original consult explicitly leaves for the
maintainer: extraction timing, whether to build the verb, ingestion ceremony weight, whether
track record should ever cross as more than a citation, whether succession should get a typed
kernel record instead of prose pointers, and how autoharn-panel's own eventual succession should
be sequenced. Anything this generalization or FAQ raises beyond what the original text grounds
is flagged inline (§8.3) rather than folded into those six — this pass is not the commissioned
consult and does not add to its reserved-question list on its own authority.

---

## License

Public Domain (The Unlicense).
