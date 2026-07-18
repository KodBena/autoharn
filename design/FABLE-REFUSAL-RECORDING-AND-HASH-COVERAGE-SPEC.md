<!-- doc-attest-exempt: DRAFT pinned pre-ratification 2026-07-18 (Fable freeze plan, ledger row 1455). This commit pins the fresh-context-authored draft exactly as delivered, before the maintainer's ratification pass and its incorporation edits; the ADR-0017 fresh-context attestation is deliberately deferred until AFTER incorporation, when the content stabilizes -- attesting a draft that ratification will change would go stale by design. -->

# FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC — the kernel write boundary as a typed-refusal-verdict surface, and the row-hash chain widened to the whole row (kernel delta family s42–s43)

**Status:** RATIFIED build basis (R1–R6, ledger row 1460, 2026-07-18). Fable-authored,
fresh-context, 2026-07-18, under ADR-0018 discipline (the author received the witnessed problems,
their evidence, and the governing LAW — no working-session designs); ratification incorporated by
the same author the same day (the delivered draft is pinned as-is at commit `de5b94e`; the edits
on top of that pin are this incorporation pass, ledger estimate row 1461, and nothing else). The
maintainer's ratification, verbatim (row 1460): *"I have looked at
FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md and agree with the recommendations R1-R6. Let
us get it done."* All six §9 decisions are thereby RATIFIED at their recommended dispositions.
The builder assignment — reserved by this spec itself — was ruled the same day: FABLE builds
(ledger row 1462; §10 carries the grounds). Cost attribution of the authoring pass: ledger estimate row 1452, slug
`s42-hash-chain-spec-family`. Nothing in this document is built, applied, or wired by the act of
its authoring; per the runs-are-linear ruling (maintainer, 2026-07-11, [CLAUDE.md](../CLAUDE.md)),
the deltas it specifies reach reality only by entering a FUTURE [world](../GLOSSARY.md#world)'s
[birth chain](../GLOSSARY.md#birth-chain).

**What this document is, in plain words.** The kernel — the append-only Postgres schema holding
this project's decision ledger and its integrity machinery — has two witnessed defects that share
one surface, the path by which a row enters the ledger. First: when the kernel *refuses* a write
(a revoked principal, a malformed shape, a policy violation), the refusal is delivered as an
aborting SQL exception, so the refusal's own evidence is destroyed by the refusal's own mechanism —
the one event class the kernel systematically fails to record. The maintainer has already ratified
the direction of the fix ("Ledger grade, of course," ledger row 1419): the write boundary becomes a
function returning a typed refusal verdict, and a refusal becomes an ordinary committed ledger row.
Second: the tamper-evidence hash chain ([s26](../kernel/lineage/s26-row-hash-chain.sql)) serializes
only the column set the ledger had in mid-2026 — every one of the twenty-two columns added since
([s28](../kernel/lineage/s28-work-parent-edge.sql) through
[s41](../kernel/lineage/s41-principal-bindings-and-relations.sql), including all twelve principal
columns) is outside the chain, so a schema-owner tamper of any of them changes no hash (witnessed
hazard, ledger row 1449). This spec remediates both as one coordinated family of two kernel deltas,
s42 (hash coverage) and s43 (the typed-verdict boundary), because the second is only worth its
ratified grade if the first lands under it: a refusal row "inheriting the hash chain" inherits
nothing for the very columns that make it a refusal row unless those columns are inside the
serialization.

**Primary inputs, all read in full:**
[CLAUDE.md](../CLAUDE.md); [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)
(incl. the 2026-07-02 Rule 2(a) closure-statement amendment),
[ADR-0011](../law/adr/0011-mechanization-discipline.md),
[ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md),
[ADR-0013](../law/adr/0013-execution-integrity.md),
[ADR-0014](../law/adr/0014-executor-second-opinion.md),
[ADR-0017](../law/adr/0017-the-zero-context-reader.md),
[ADR-0018](../law/adr/0018-consults-are-not-front-loaded.md);
[design/ORCH-CONSULT-REFUSAL-RECORDING-2026-07-17.md](ORCH-CONSULT-REFUSAL-RECORDING-2026-07-17.md)
(the banked consultation whose candidate E the maintainer ratified);
[design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md](FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md)
(§7 item 9 and §9(e) — the preserved mechanism history of the refuted candidates A and B — and its
whole structure, followed here as the house exemplar of spec completeness);
[judgment/engine/engine-panel/refute-architecture.md](../judgment/engine/engine-panel/refute-architecture.md)
flaw 1 (the prior-generation refutation of the dblink journal, and its demand for a second
witness); [kernel/lineage/s26-row-hash-chain.sql](../kernel/lineage/s26-row-hash-chain.sql),
[s27](../kernel/lineage/s27-chain-high-water.sql),
[s40](../kernel/lineage/s40-principal-identity-events.sql), and
[s41](../kernel/lineage/s41-principal-bindings-and-relations.sql) in full, s28–s39 for the column
census; [bootstrap/templates/led.tmpl](../bootstrap/templates/led.tmpl) for the live write-path
census; ledger rows 1449 and 1452 read via `./led show`, verbatim.

**The maintainer's ratified rulings this spec executes, verbatim:**

1. *"Ledger grade, of course."* (ledger row 1419, 2026-07-17) — selecting candidate E of the
   banked consultation for refusal recording: dissolve the transaction-abort premise; the write
   boundary returns a typed refusal verdict; a refusal is an ordinary committed ledger row
   inheriting hash chain, stamps, append-only, and countersignability; client-facing INSERT
   privilege revoked; every writer routes through the function. **The direction is ratified and is
   not reopened here; the mechanism design is this spec's mandate.**
2. Ledger row 1449 (2026-07-18, the witnessed hazard, quoted in substance): *compute_row_hash
   (s26) serializes only the s24-era column set — EVERY ledger column added since s28, including
   all twelve s40/s41 principal columns, is OUTSIDE the tamper-evidence hash chain … closing this
   is its own Fable-authored, maintainer-ratified delta family (it changes what the hash MEANS —
   not class-ratifiable); it braids with the s42 refusal-recording family's write-boundary
   redesign, which touches the same surface.* — What the chain should cover was framed by this
   spec as reserved decisions §9 R1/R2, with a recommendation — **since RATIFIED at the
   recommended dispositions (ledger row 1460, 2026-07-18): the chain covers the full row minus
   `row_hash`, by an enumerated serializer held complete by a coverage gate.**
3. *"I have looked at FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md and agree with the
   recommendations R1-R6. Let us get it done."* (ledger row 1460, 2026-07-18) — the ratification
   of this spec itself, all six §9 reserved decisions at their recommended dispositions,
   incorporated throughout this document.

---

## 0. Executive summary (ADR-0017; compresses §1–§9, adds no new content)

**s42 and s43, named plainly.** **s42** (`s42-row-hash-full-coverage`) re-issues the one
serialization function the hash chain rests on, `compute_row_hash`, so that it covers every ledger
column except `row_hash` itself — fifty-two columns instead of the thirty it covers today — and
mints the mechanical net that keeps that true forever: a repository gate that goes red whenever the
ledger's column set and the serializer's column set disagree, so no future column-adding delta can
repeat the s28→s41 silence. **s43** (`s43-typed-verdict-write-boundary`) executes the ratified
refusal-recording direction: the granted role's INSERT privilege on every kernel-governed table is
revoked; four SECURITY DEFINER boundary functions become the only write path; a refusal caught
inside them is committed as an ordinary `write_refused` ledger row (attributed to a
birth-registered `write-boundary` principal, carrying the attempted actor, the SQLSTATE, the
teach-text, and a digest of the refused payload) and returned to the caller as a typed verdict —
never an abort; a non-transactional refusal-counter sequence provides the completeness oracle the
prior refutation demanded. s43 hard-depends on s42. Both reach reality only at a future world's
birth.

**Why one family, and in this order.** Both problems restructure the same surface (the write
path), and the ratified grade of the second depends on the first: "a refusal row inherits the hash
chain" is only true of the columns the chain serializes, and the columns that make a refusal row a
refusal row are new. s42 first, s43 second; s43's own new columns are then the first delta forced
by s42's gate to re-issue the serializer — the new discipline exercises itself immediately (§2).

**Fixed by this spec (the builder does not re-open):** the boundary is a jsonb-payload function
family, not per-column signatures (§4.2); refusals are classified by SQLSTATE class, journaling
{22, 23, P0} and re-raising infrastructure classes (§4.4); the refusal row's actor is the
`write-boundary` tool principal, with the attempted identity in typed columns (§4.5); actor
resolution moves from `current_user` to `session_user` and the scaffold declares standing for the
login role (§4.7); the completeness oracle is a sequence, reconciled by `./verify-chain` (§4.6).

**Ratified 2026-07-18, all six at the recommended dispositions (ledger row 1460; §9 has each
decision's full text, kept with its honest alternative as the record of what was chosen
against):** **R1** the chain covers the full row minus `row_hash` only; **R2** the serializer is
an enumerated column list plus a coverage gate, not a catalog-generic serializer; **R3** sibling
tables (`review_detail` above all) stay named-not-covered in v1, a follow-on family if wanted;
**R4** refused payloads are stored as digest only, never verbatim; **R5** no refusal-flood rate
machinery in v1; **R6** `write_refused` rows are unretractable — supersession refused on them, a
named, ratified divergence from s31 uniformity.

---

## 1. The two defects, named at class level (ADR-0000 Rule 2)

### 1.1 Refusal recording

**(a) The type question.** The class, in its most general form (the consultation's naming,
adopted): *a refusal whose only witness is destroyed by the refusal's own mechanism.* The kernel's
every policy refusal is a `RAISE EXCEPTION` from a trigger; the exception aborts the transaction;
the transaction was the only place the attempt existed. The foreclosing type is
[ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) P9 rule 5 lifted into SQL:
**failure is a typed return value, never a throw.** The write boundary becomes a function whose
return type carries both outcomes; the refusal becomes a committed row; the class — refusals
without records — becomes unrepresentable for every write that enters through the boundary,
because the boundary cannot deliver a refusal verdict without having journaled it (single code
path, §4.4). Two candidates that patched the symptom instead (a dblink autonomous transaction; a
CLI-side second connection) were each refuted twice and stay retracted — the full history is
preserved in the build basis
[§9(e)](FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md) and
[refute-architecture.md](../judgment/engine/engine-panel/refute-architecture.md) flaw 1, and this
spec re-derives nothing from them except the obligation flaw 1 imposed on any successor: a
**second witness** for the completeness claim (§4.6).

**(b) The operational lapse.** Executive-side: the kernel's refusal surface was built loud-first
(correctly) before the project's audit-family standards work named denied-attempt logging
(NIST AU-2/AC-7-shaped) as a first-class record obligation; no mechanism ever forced the question.
The net minted here: the boundary itself (a refusal cannot be delivered unjournaled), the sequence
oracle (§4.6), and the detect siblings.

### 1.2 Hash-chain column coverage

**(a) The type question.** The class: *a tamper-evidence serialization whose column enumeration is
open at every subsequent delta, silently.* Thirteen deltas (s28–s41) each added columns and each —
correctly, under the not-class-ratifiable rule — left `compute_row_hash` alone, so the enumeration
drifted from the table one delta at a time: the exact *enumeration-fails-open-at-the-next-instance*
failure ADR-0011 Rule 4 names, here in the one mechanism whose whole job is completeness. The
uncovered set as of the s41 head, enumerated by census of every `ADD COLUMN` on `ledger` since s26
(the witness commands and their outputs are reproducible; the builder re-runs the census before
building):

| Delta | Uncovered columns |
| --- | --- |
| s28 | `work_parent` |
| s29 | `work_review_disposition`, `work_review_ref`, `work_strict_close` |
| s30 | `edge_type` |
| s33 | `work_discharge` |
| s36 | `decision_grade` |
| s37 | `work_violation_class`, `work_violation_target_id`, `work_violation_witness` |
| s40 | `principal_subject`, `principal_purpose`, `principal_db_role`, `principal_actor_resolution` |
| s41 | `principal_binding_active`, `principal_object`, `principal_relation`, `principal_role_name`, `principal_key_fingerprint`, `principal_competence_activity`, `principal_competence_band`, `principal_competence_basis` |

Twenty-two columns; ten carry work/decision semantics, twelve carry the entire principal-identity
record — meaning today a schema-owner can rewrite, e.g., which principal a revocation event
regards, or a violation disposition's class, with zero chain disturbance. The foreclosing shape has
two candidate types (a serializer that derives its column list from the catalog, vs. an enumerated
serializer plus a set-equality gate); the choice was framed as reserved decision **R2** because
the two differ in a real hazard trade, not in taste — **RATIFIED (row 1460): the enumerated
serializer plus the gate** (§9 R2 keeps the trade's full record).

**(b) The operational lapse.** Executive-side, and named precisely by the s40/s41 builder when
flagging the hazard (row 1449): the s28–s39 executors followed the law correctly — a
non-fail-safe serialization change was not theirs to make — and no gate existed to force the
question per delta. The recurrence has now been paid thirteen times; per ADR-0011's 2026-07-02
amendment (life-critical bar: the mechanism ships WITH the first fix), s42 ships the gate in the
same delta as the fix.

**Confidence: high** on both classes — 1.1 is ratified direction plus a triple-refuted
alternative history; 1.2 is arithmetic over the lineage files.

---

## 2. Packaging — one family, two deltas, fixed order

**Decision (this spec's own, per the commission): one ratification family, two deltas.**

- **s42 — `s42-row-hash-full-coverage`.** The serializer re-issue plus the coverage gate.
  Meaningful alone: even if s43 were later vetoed, s42 closes the row-1449 hazard in full.
- **s43 — `s43-typed-verdict-write-boundary`.** The boundary family, the `write_refused` kind and
  its six columns, the boundary principal, the sequence oracle, the privilege revocations, the CLI
  migration. **Hard prerequisite: s42.** Not meaningful first: shipped without s42, every
  `write_refused` row's distinguishing columns would sit outside the chain — the ratified "ledger
  grade" would be true of the row's prose and false of its typed content, ADR-0013's
  letter-over-spirit failure in schema form.
- s43 adds columns, so s43 itself re-issues `compute_row_hash` (58 columns) under s42's new law —
  the first, immediate, both-polarities exercise of the gate (§6).

**Why not one delta:** the s40/s41 precedent's ratified packaging rationale (build basis §9(d):
independent git-revertability) applies with more force here — s42 is a quiet, self-contained
integrity widening; s43 restructures every write path and touches the CLI template throughout.
A single delta would weld the low-risk fix to the high-churn one. **Why not two independent
families:** the grade-dependency above, plus one ratification bandwidth spend instead of two
(the maintainer answers §9 once for both).

**Neither delta is class-ratified fail-safe, stated plainly:** s42 changes what `row_hash` means
(a semantics change to an existing mechanism); s43 revokes privileges and re-issues `set_actor`.
Both ship only under this spec's ratification, per the ORCHESTRATION contract.

**Confidence: high** on the two-delta split and the s42→s43 order; **medium** on naming (the
working names s42/s43 are kept; if an unrelated delta lands first in the lineage, the numbers
shift and nothing else does).

---

## 3. Delta s42 — `s42-row-hash-full-coverage`

### 3.1 The serialization, v2 (per §9 R1/R2, RATIFIED 2026-07-18, row 1460)

`compute_row_hash(r ledger, predecessor_hash text)` is re-issued — same name, same signature, same
one-home discipline (called by the `zz_set_row_hash` trigger and by `./verify-chain`'s walk, and
by nothing else; the builder verifies by grep that
[verify-chain.tmpl](../bootstrap/templates/verify-chain.tmpl) still contains no second
serialization). The new body serializes, in the ledger's catalog ordinal order (which equals the
`ledger_current` explicit column list at the s41 head, §1.2's thirty-plus-twenty-two), **every
column except `row_hash`**, each through the existing injective `hashfield()` token encoding
(`N:` for SQL NULL, `V<char-length>:<value>` for present — the s26 length-prefix discipline,
unchanged; its injectivity argument carries over verbatim), joined with the same `\x1f`
legibility separator, with `hashfield(predecessor_hash)` as the final token. Per-type rendering
rules, fixed so the builder cannot fork:

- `bigint` / `boolean` columns → `::text` (s26 precedent).
- `bigint[]` (`enacts`) → `array_to_string(r.enacts, ',')` (s26 precedent; injective over
  bigint elements).
- **Every `timestamptz` column → `extract(epoch FROM …)::text`.** This now includes `stamp_ts`,
  which **s26 serialized as `r.stamp_ts::text` — a latent timezone hazard found in passing while
  authoring this spec and flagged here per the engineering-responsibility corollary, not silently
  absorbed**: a session-timezone-dependent rendering means `./verify-chain` run from a connection
  in a different timezone than the inserting session would report a spurious chain break on any
  row with a non-NULL stamp. No committed world is known to be affected (main-world rows are
  unstamped; the panel world is dust), and existing worlds are read-only evidence — the exposure
  is only *operational guidance* for verifying old worlds (verify from a same-timezone session).
  s42 fixes it by construction for every future world. Surfaced for the maintainer's awareness;
  requires no delta to any existing world (runs-are-linear forbids one anyway).
- `text` columns → as-is (hashfield handles NULL/empty distinctly).

**Re-denomination consequence, stated honestly (the commission's required analysis):** every hash
a v2 world computes differs from what a v1 world would compute on identical content. Under
runs-are-linear this costs **nothing operationally**: a serialization is world-scoped (each world's
chain is computed and verified by that world's own `compute_row_hash`, born with it; no world ever
mixes eras, because deltas never apply to live worlds), genesis seeds already make chains
world-unique, and GPG-signed heads are per-world artifacts. What it does mean: cross-world hash
comparison (which nothing does today) is meaningless across the s42 boundary, and the s26
`.accommodate.sql` machinery (a v1-era artifact) is not carried forward — s42's header states
this. There is no migration, because there is nothing to migrate: **the change reaches only
worlds born under it.**

### 3.2 The coverage gate — the net that closes the class (ADR-0011 Rules 2/4)

New repository gate `gates/hash_coverage_gate.py`, shipped in the same commit as s42 (the
mechanism ships WITH the fix — ADR-0011's 2026-07-02 amendment):

- Builds the standard scratch chain to the lineage head on the toy db (the same harness pattern
  `gates/ledger_reader_allowlist.py` uses), then compares two sets: (i) `ledger`'s columns per
  `information_schema.columns`, minus `row_hash`; (ii) the columns `compute_row_hash` serializes,
  **derived from the function's own source** via `pg_get_functiondef` (regex over `r\.<name>`
  references) — derived from the one home, never a second hand-maintained manifest (ADR-0012 P1;
  a manifest would be the two-writers cancer the gate exists to prevent).
- Set inequality in either direction → red, naming the missing/extra columns and teaching: "a
  delta that adds a ledger column re-issues compute_row_hash in the same delta."
- Negative control (a gate never seen red is a claim): the gate's self-check applies a synthetic
  `ADD COLUMN` to the scratch and asserts red; seen-red fixture registered in
  `gates/fixture_census.py`.
- The gate quantifies over the class (any future column, any delta), not the instance — the
  s28→s41 silence cannot recur without a red gate in the offending commit.

### 3.3 s42 detect sibling and HISTORY

`s42-row-hash-full-coverage.detect.sql`: behavior-fingerprinted per the migrate-detect-drift
ruling — probes `pg_get_functiondef(compute_row_hash)` for marker column references (e.g.
`r.principal_competence_basis`), witnessed **t** on an s42 scratch and **f** on an s41-head
scratch. No live INSERT.

HISTORY: safe — the re-issue is `CREATE OR REPLACE FUNCTION` of `compute_row_hash` only; no
trigger definition, view, constraint, grant, or existing column changes; `hashfield`,
`zz_set_row_hash`, the advisory lock, the genesis seed, and s27's high-water witness are all
untouched. On any birth chain the function is re-issued before the first ledger row exists, so no
row is ever hashed under two regimes. The one semantic change — what the hash means — is the
delta's entire, ratified point, and is why it is not class-ratifiable.

**Confidence: high** on mechanism and gate; **high** on the re-denomination analysis (it reduces
to runs-are-linear, which is ratified law).

---

## 4. Delta s43 — `s43-typed-verdict-write-boundary` (hard prerequisite: s42)

### 4.1 The write surface, enumerated (what "every writer routes through the function" binds)

Census of the granted role's DML surface at the s41 head (from the lineage grants and
[led.tmpl](../bootstrap/templates/led.tmpl)'s INSERT sites): **`ledger`** (INSERT, the main
surface, ~25 CLI sites); **`review_detail`** (INSERT, always paired with a `review` ledger row in
one transaction; carries its own refusal triggers — `validate_independence` incl. s41 D-6, s34's
computed-grade refusal); **`kernel.principal`** (INSERT, only inside `register-principal`, paired
with the registration event and s40's deferred anchor trigger); **`countersign_obligation`**
(INSERT via `led obligate`; its revoke path is a DELETE the granted role does not hold and which
escalates to the owner — unchanged by this spec). s18-class deployments add: `rev1`/`rev2` INSERT
on `ledger` + `review_detail`. Read surfaces, hooks, engine/EDB, SPA: not writers, untouched.

**The boundary therefore has four members, and the privilege change is total:** s43 REVOKEs
INSERT on all four tables from `:role` (and, in the s18 arming enumeration, from the criterion
roles), REVOKEs from PUBLIC, and GRANTs EXECUTE on the four functions below. After s43, a raw
`INSERT` from any granted role fails at the privilege layer (SQLSTATE 42501) before any semantics
run — the bypass path does not exist (ratified item; the residual home for *that* refusal class
is the server log, §8).

### 4.2 The boundary functions — shape fixed

All four: `SECURITY DEFINER`, owned by the schema owner, `SET search_path = :"schema", :"kern",
pg_temp` (the s19 discipline; mandatory on SECURITY DEFINER), `REVOKE ALL FROM PUBLIC`,
`GRANT EXECUTE TO :"role"`. All return the new composite type:

```
CREATE TYPE :"kern".write_verdict AS (
    disposition text,     -- 'accepted' | 'refused'  (the two-member closed vocabulary)
    row_id      bigint,   -- the accepted row's ledger id (NULL when refused)
    refusal_id  bigint,   -- the committed write_refused row's id (NULL when accepted)
    sqlstate    text,     -- the refusal's SQLSTATE (NULL when accepted)
    message     text      -- the refusal's teach-text, verbatim (NULL when accepted)
);
```

1. **`kernel.ledger_write(payload jsonb) RETURNS kernel.write_verdict`** — the generic single-row
   path (every CLI verb that today issues one ledger INSERT, including all s40/s41 principal verbs
   except registration). Payload keys are column names. Validation before any INSERT, refused
   loudly as a verdict (never silently dropped — ADR-0012 P2): (i) any key not a `ledger` column;
   (ii) any **server-owned key**: `id`, `ts`, `row_hash`, `stamp_session`, `stamp_agent`,
   `stamp_ts`, `stamp_hmac`, `stamp_verified`, `stamp_invocation`, `principal_actor_resolution`
   (trigger-computed; a writer-supplied value would be a lying channel), and every
   `refusal_*` column plus `kind = 'write_refused'` (only the handler mints refusal rows — the
   forgery channel is closed at the same trust boundary that does the journaling, stated as such
   in §8); (iii) declared event time rides `event_declared_ts` per s24 — `ts` is server time,
   never client-supplied. Construction: a dynamic INSERT enumerating exactly the payload's keys,
   each value drawn from `jsonb_populate_record(NULL::ledger, payload)` field access — so per-type
   casting is **derived from the rowtype** (P1: no hand-written cast table to drift), and absent
   keys fall to column defaults (`id`, `ts`, `session`) rather than explicit NULLs.
2. **`kernel.review_write(payload jsonb) RETURNS kernel.write_verdict`** — the review ceremony:
   the `review` ledger row and its `review_detail` row in one guarded block (payload: `regards`,
   `statement`, `verdict`, `independence`, `basis`, `antecedent`, `actor`). A refusal from either
   INSERT — including `validate_independence`'s D-6 human-only refusal and s34's grade refusal,
   which fire on `review_detail` and would otherwise stay outside the recorded surface — journals
   as one `write_refused` row, surface `'review'`, and rolls the whole ceremony.
3. **`kernel.registration_write(payload jsonb) RETURNS kernel.write_verdict`** — the registration
   ceremony: the `kernel.principal` anchor INSERT and its `principal_registered` ledger event,
   followed **inside the guarded block** by `SET CONSTRAINTS ALL IMMEDIATE`, so s40's deferred
   anchor-coupling trigger fires within the handler's scope and a commit-time refusal is caught
   and journaled like any other (the consultation's named obligation, discharged). A duplicate
   name now leaves a durable trace even when attempted raw through the function — the panel's
   silent-duplicate class gains its record. The CLI's pre-flight duplicate check with rich
   teach-text stays (ergonomics), backed by this journaled kernel refusal.
4. **`kernel.obligation_write(payload jsonb) RETURNS kernel.write_verdict`** — the
   `countersign_obligation` INSERT (`led obligate`). Uniformity is the argument: the boundary
   posture is "no granted-role DML except through a verdict-returning function," with no
   carve-out for config tables that would re-open the class.

`SET CONSTRAINTS ALL IMMEDIATE` is issued at the end of **every** function's guarded block, not
only registration's — cheap, and forecloses the whole future class of deferred-trigger refusals
escaping the handler (quantify over the class, not today's one instance).

### 4.3 The `write_refused` kind and its columns

Kind CHECK re-issued widened by `write_refused` (twenty-fourth member). Six new kind-scoped
columns, all nullable, no column DEFAULT (the s30 lesson), each with a two-way kind-shape CHECK
(safe: the kind is born here — the s40 precedent) plus split value CHECKs per the s40 house idiom
(one concern per CHECK, for `gates/kind_shape_manifest_gate.py`'s classifier):

- `refusal_sqlstate text` — mandatory; value CHECK `~ '^[0-9A-Z]{5}$'`.
- `refusal_message text` — mandatory non-empty; the refusal's teach-text verbatim (kernel-authored
  prose with interpolated identifiers — bounded content, not raw payload).
- `refusal_surface text` — mandatory; closed CHECK `IN ('ledger','review','registration',
  'obligation')` — which boundary function caught it. (This vocabulary is kernel-structural — it
  enumerates the boundary functions themselves — so a closed CHECK is right where s41's
  role-name column was ruled free text.)
- `refusal_payload_digest text` — mandatory; value CHECK `~ '^[0-9a-f]{64}$'`; SHA-256 (hex, via
  the same built-in `sha256()` s26 uses) of the refused payload's canonical text, defined as
  `payload::text` of the jsonb argument (jsonb's stored form renders deterministically —
  key-sorted, canonical spacing — on a given server; the cross-version rendering caveat is a
  named limit, §8). Digest, not verbatim — §9 **R4**, RATIFIED (row 1460).
- `refusal_attempted_actor bigint REFERENCES kernel.principal(id)` — nullable: the attempted
  principal when it resolved to a registered id (an explicit actor, or a standing-declaration
  default that then failed the standing check); NULL when the attempt was unattributable (no
  declaration, unknown name) — exactly the case whose *role* is still always known:
- `refusal_attempted_role text` — mandatory non-empty; `session_user` at the time of the attempt
  (server-witnessed, never client-asserted).

Additional structural CHECK per §9 **R6** (RATIFIED, row 1460): `kind <>
'write_refused' OR supersedes IS NULL` — a refusal event records a historical fact about an
attempt; it asserts nothing retractable, so supersession (which would drop it from
`ledger_current` and every derived surface) is refused at construction. This is a deliberate,
surfaced, and now ratified divergence from s31's supersession-uniformity (it does not mint a
second retraction mechanism; it declares one kind unretractable).

The refusal row additionally carries, through the ordinary machinery and at zero new cost: the
attempting session's stamps (`set_stamp` reads session GUCs, unaffected by SECURITY DEFINER),
`principal_actor_resolution = 'explicit'` (the handler supplies its actor), the row hash (inside
the s42+s43 serialization), and countersignability/reviewability as an ordinary row — the AU-6
review half needs no new machinery, named rather than built.

### 4.4 Handler semantics — fixed

Inside each function: the real INSERTs run within `BEGIN … EXCEPTION` (a PL/pgSQL exception block
is an in-process subtransaction — no connection, no extension, no slot; the refuted candidates'
failure modes structurally absent). The handler:

1. Classifies `SQLSTATE`. **Journaled classes: `22___` (data exception — malformed payload
   values), `23___` (integrity constraint — every kind-shape/FK/unique refusal), `P0___`
   (`raise_exception` — every taught policy refusal in the kernel).** Everything else —
   serialization failures (40), resource exhaustion (53), operator intervention (57), internal
   errors (XX), and any class not enumerated — is **re-raised unjournaled**: an infrastructure
   failure is not a denied attempt, and conflating them would poison the refusal record's
   meaning. The fail-open honesty of this enumeration: a novel *policy* refusal mechanism minted
   in some future delta outside these classes would escape journaling — but every kernel refusal
   mechanism is `RAISE EXCEPTION` or a constraint by construction, a new mechanism class needs
   its own spec anyway, and the polarity is fail-safe (escaped = loud abort, never silent
   acceptance).
2. On a journaled class: `nextval('kernel.refusal_seq')` (the oracle bump, **before** the journal
   INSERT — non-transactional, survives everything); then INSERTs the `write_refused` row
   (explicit VALUES; actor = the `write-boundary` principal id, §4.5); then RETURNs the
   `('refused', NULL, <id>, <sqlstate>, <message>)` verdict. The enclosing transaction commits
   carrying the refusal event and nothing else.
3. If the journal INSERT itself fails, the exception propagates: the whole call aborts loudly,
   the client sees a real SQL error (today's behavior, exactly), the sequence shows a gap the
   oracle reconciliation names (§4.6), and the server log holds the statement (candidate C's
   standing residual coverage). Fail-safe on both legs: the refusal still refuses; the loss is
   loud and counted.

The trigger chain the guarded INSERT runs is byte-for-byte today's chain — refusals are caught
**generically** by class, never by enumerating refusal sites (the consultation's requirement; no
trigger is modified to cooperate). The s26 advisory lock, id burn on the rolled-back INSERT, and
predecessor-hash lookup all behave correctly under the subtransaction (the rolled-back row is
invisible to the journal INSERT's predecessor SELECT).

### 4.5 The `write-boundary` principal

The refusal row's `actor` cannot be the attempted principal (the attempt may be refused precisely
because that principal is revoked, unresolvable, or nonexistent — attribution would either lie or
recurse into a second refusal). The enforcement point authors the audit record (AC-25's shape):
the scaffold's birth sequence gains a step registering principal **`write-boundary`**,
`agent_class = 'tool'` (an existing vocabulary member since s13 — no vocabulary change), through
the full ceremony, purpose text fixed by this spec: *"the kernel write boundary's own recording
identity: every write_refused meta-event is authored by this principal; the attempted identity is
carried in the event's refusal_attempted_* columns (s43)."* The handler resolves it by name once
per call. CLI guard: `led principal suspend|revoke write-boundary` is refused at the CLI with
teach-text (suspending the recorder bricks refusal recording — the kernel-side dead-end analog of
s40's C7, disclosed in §8 as CLI-grade only).

### 4.6 The completeness oracle — `kernel.refusal_seq`

Flaw 1's standing demand: *"the journal is the sole witness to refusals … 'every actual refusal
was journaled' has no oracle."* Discharged with the consultation's candidate F, built in s43: a
dedicated sequence, bumped by the handler immediately before each journal INSERT (§4.4 step 2).
`nextval` is non-transactional by design — no rollback erases it. Reconciliation leg added to
`./verify-chain` (the house home for chain-adjacent witnesses, beside s27's high-water report):
compares `count(*) WHERE kind='write_refused'` against the sequence's `last_value`. Semantics,
fixed: **count > sequence → FAIL** (rows exist the handler never counted: forged or replayed
refusal rows — the oracle doubles as the §4.2(ii) forgery-channel tripwire); **sequence > count →
EXPLAIN, not fail** (legitimate causes enumerated in the output: a journal-INSERT double failure;
a raw caller wrapping the function in a transaction it then rolled back — both named in §8).
`:role` gets no grant on the sequence beyond what `USAGE` the handler needs as definer (none —
the definer owns it); the subject cannot advance or reset the witness (the s27 grant posture,
mirrored).

### 4.7 Actor resolution under SECURITY DEFINER — `set_actor` re-issued on `session_user`

Inside a SECURITY DEFINER function, `current_user` is the function owner — s40's `set_actor`
would resolve every boundary write to the owner's login and misattribute everything. The
consultation named the fix; this spec specifies it: `set_actor` is re-issued (the s40 body — the
lineage head's declaration, per the migrate-detect-drift discipline — with exactly one change)
resolving the standing declaration against **`session_user`** (the authenticated login role:
server-witnessed, unaffected by `SET ROLE` and by SECURITY DEFINER). Consequences, fixed:

- **The scaffold's birth declaration (s40 §3.7 step 2) now declares standing for the LOGIN role
  the world's DSN authenticates as** (witnessed at scaffold time as `session_user`), **in
  addition to** the constrained `:role` (the existing declaration — kept: harmless, one extra
  `principal_role` row, and it keeps the record correct about both identities). The
  `led.tmpl` connect-then-`SET ROLE` pattern keeps working unchanged: privilege comes from the
  role, attribution from the session.
- Behavior on a direct connection (no SET ROLE, no SECDEF) is identical: `session_user =
  current_user` there — the re-issue is behavior-preserving for every path that exists today
  outside the boundary, and the boundary is the only write path left.
- **Named limit (§8):** a deployment multiplexing several principals over ONE login via
  `SET ROLE` loses implicit per-role attribution (all resolve to the login's declaration); the
  explicit `LED_ACTOR`/payload-actor channel remains the correct tool there. s18-class
  deployments that authenticate `rev1`/`rev2` as distinct logins keep full implicit distinction.
- A structural bonus, named because it retires a whole hazard class: the boundary functions run
  the trigger chain as the owner, so the **finding-45 class** (zero-SELECT writers refused inside
  SECURITY INVOKER trigger reads — s18's 2b, s40 §3.4/C4's per-object foreclosures) is dissolved
  wholesale for every boundary write. The s40 per-object mechanisms stay (harmless, and they
  still cover any owner-side direct path).

### 4.8 CLI migration, s18 arming, and the same-commit set

- **led.tmpl:** every INSERT site migrates to its boundary call in the s43 commit. One shared
  shell function (`kernel_write <function> <payload-json>`) is the single home for invoking a
  boundary function, parsing the verdict row, and — on `refused` — printing `message` to stderr
  and exiting nonzero. Operator-visible behavior is output-equal for refusals (same teach-text,
  same nonzero exit); the only observable change is that raw-psql callers of the functions
  receive a verdict row instead of an aborting error — the teaching survives in content (the
  ratified trade).
- **s18-class arming enumeration** (extends s40/s41's): revoke `rev1`/`rev2` INSERT on
  `ledger`/`review_detail`; grant EXECUTE on `ledger_write`/`review_write`; declare standing for
  their login roles.
- **Same commit:** detect sibling (behavior-fingerprinted: `has_table_privilege(:role, 'ledger',
  'INSERT')` is false; the kind CHECK carries `write_refused` via catalog read; the boundary
  functions exist — **t** on s43 scratch, **f** on s42 head); `LINEAGE_CHAIN` wiring;
  `kind_shape_manifest_gate` rows (six columns, one kind) and `ledger_reader_allowlist` CHAIN
  bump; the s42-mandated `compute_row_hash` re-issue to 58 columns; `ledger_current`/
  `countersigned_in_force` re-issued +6 (the s20 lesson; non-member views re-verified per the
  s38 discipline); scaffold birth-sequence extension (write-boundary registration + login-role
  standing declaration); fixture census registrations.

### 4.9 s43 HISTORY: safe — per-mechanism grounds

Additive kind vocabulary; six nullable no-default columns, CHECKs vacuous on pre-existing rows
(kind born here); `set_actor` re-issued with a resolution-source change that is behavior-identical
on every connection shape that exists pre-s43 (§4.7) plus no other edit; REVOKEs are pure
narrowing (nothing that succeeded before succeeds differently — it is refused at the privilege
layer, the fail-safe polarity; and no pre-s43 world ever runs this delta, so "before" exists only
on scratch); the four functions, the type, the sequence, and the principal-registration scaffold
step are new objects with no pre-existing reader; the serializer re-issue is s42's law applied.
The one genuinely non-additive act — the write-path restructure itself — is the ratified point,
and is why this family routes as a Fable-authored maintainer-ratified spec.

**Confidence: high** on §4.2–§4.6 (stock semantics, verified against the consultation's own
verified mechanics); **medium-high** on §4.7 (the `session_user` shift is analyzed against every
connection shape found in the repo, but it is the one place a deployment shape unknown to this
census could surprise — the witness plan's scaffold leg exists precisely to catch it);
**medium** on §4.8's migration size estimate (mechanical but wide; the shared `kernel_write`
helper bounds the per-site risk).

---

## 5. Family closure statement (ADR-0000 Rule 2(a), 2026-07-02 form)

**Invariant.** Every row the ledger accepts, and every refusal the kernel issues through its
sanctioned write surface, is a committed, attributed, stamped, hash-chained ledger row; the hash
chain's serialization covers every column of every such row except the hash itself, and a
mechanical gate holds that coverage equal to the table's column set at every future delta; no
granted role holds a write privilege on any kernel-governed table — the only write path is a
function family whose return type carries acceptance and refusal as values, so a refusal without
a committed record is unrepresentable for every write that reaches kernel semantics; and the
count of journaled refusals is reconciled against a rollback-proof counter, so the completeness
of the refusal record is a checkable claim, not an article of trust.

**Quantification universe, enumerated:**

- **Columns (the s42 axis):** all 52 ledger columns at the s41 head (§1.2's census: the 30
  s24-era plus the 22 uncovered), plus s43's 6 refusal columns = 58; `row_hash` is the one
  deliberate exclusion (it cannot include itself), named here. The gate (§3.2) quantifies over
  every FUTURE column.
- **Write surfaces (the s43 axis), disposed one by one:** `ledger` generic path — covered
  (`ledger_write`); review ceremony incl. `review_detail`'s own refusal triggers — covered
  (`review_write`); registration ceremony incl. the COMMIT-time deferred trigger — covered
  (`registration_write` + `SET CONSTRAINTS ALL IMMEDIATE`); obligation config INSERT — covered
  (`obligation_write`); raw INSERT by a granted role — **foreclosed at the privilege layer**,
  its refusal NOT kernel-journaled (residual home: the server log, candidate C — named, §8);
  owner/superuser direct DML — **named not covered** (the standing s26-s41 trust bound, §8);
  `countersign_obligation` DELETE (obligate revoke) — owner-side escalation path, unchanged,
  named; nla-schema worlds — no kernel, out of scope, named.
- **Refusal classes:** SQLSTATE classes 22/23/P0 journaled; 40/53/57/XX and unenumerated classes
  re-raised unjournaled — **named as not covered by the journal, deliberately** (infrastructure
  failure ≠ denied attempt), with the fail-safe polarity stated (§4.4).
- **Sibling tables (the outward check, presumption-of-narrowness):** `review_detail` (carrying
  verdicts and `discharge_grade`), `obligation`, `countersign_obligation`, `kernel.principal`,
  `chain_high_water` have **no hash chain of their own and never did** — this family widens the
  ledger's chain and does not silently claim the siblings; their coverage is §9 **R3**, RATIFIED
  (row 1460) as deferred — a named follow-on family if wanted, not smuggled in.
- **Views:** the two column-complete views re-issued (+6, s43); non-members re-verified per
  delta (§4.8). **Triggers:** no BEFORE INSERT member added or reordered on `ledger`
  (`set_actor` re-issued in place; `zz_set_row_hash` untouched by s43, body-re-issued by s42's
  function only). **Engine:** `entry/6` is kind-generic (verified at s40, unchanged);
  `write_refused` flows through; `./judge` witnessed in AGREE on a fixture carrying it, never
  asserted; no new `.lp` predicate. **Gates:** hash-coverage (new), kind-shape manifest,
  reader allowlist, fixture census — all bumped in the family's own commits. **CLI:** every
  led.tmpl write site enumerated and migrated; the shared verdict helper is the single home.
- **Hooks/action stream:** guarantees rest on hooks only (the standing action-stream principle);
  nothing here reads or changes hooks — named, out of scope.

**Denomination check.** Tamper evidence is denominated in the serialized-column set held equal to
the table's column set by a gate that derives both sides from the catalog and the function source
— never a hand-kept list; refusal completeness is denominated in a non-transactional counter
reconciled against committed rows — never in the journal's own self-report (the flaw-1 lesson);
the payload digest is denominated in the same SHA-256 the chain uses; refusal classes are
denominated in SQLSTATE classes (the engine's own currency for failure), never in message-text
matching; attribution is denominated in `session_user` (server-witnessed) and registered principal
ids, never names or client assertions. No bound in this family is a bare round literal.

**Confidence: high** on the column and write-surface axes (mechanically enumerable); **medium**
on the sibling-surface sweep's completeness (the least enumerable axis, checked outward once —
the same honesty flag the s40/s41 basis carried for its Axis C).

---

## 6. Witness plan (per element, both polarities, scratch-schema discipline; claims reported WITNESSED / REFUSED-AS-EXPECTED / UNEXERCISED per the standing contract)

All witnessing on scratch schema pairs in the toy db, full chain `s15..s41 + s42 [+ s43]`, genesis
seed provisioned per s26, the s40 birth acts performed as that delta's VALIDATE note prescribes.
Red first, always (a gate never seen red is a claim).

**s42:** (i) **the hazard, red:** on an s41-head scratch (pre-s42), owner-tamper `work_parent` on
a committed row → `./verify-chain` reports INTACT — the row-1449 hazard witnessed as such;
(ii) **the fix, quantified over the class:** on the s42 scratch, a scripted loop over EVERY
serialized column (all 52) tampers that column on a committed fixture row (owner-side, triggers
disabled for the tamper, restored after) and asserts `./verify-chain` breaks AT that row —
per-column, not sampled; (iii) untampered chain verifies INTACT; (iv) NULL↔empty-string tamper
on a text column breaks the chain (the s26 injectivity property, re-witnessed under v2);
(v) same-instant different-timezone verification session verifies INTACT on a row with a non-NULL
`stamp_ts` (the §3.1 TZ fix, both polarities via the pre-s42 scratch showing the old rendering's
sensitivity if cheap, else the fix witnessed green and the red leg argued from s26's source);
(vi) **the gate:** clean head → green; synthetic `ADD COLUMN` → red naming the column (the
mutation self-check); the seen-red banked; (vii) `./judge` differential AGREE on the s42 fixture.

**s43:** (i) a policy refusal through `ledger_write` (e.g. a revoked-principal write) → verdict
`refused`, a committed `write_refused` row carrying sqlstate/message/surface/digest/attempted
actor+role, actor = `write-boundary`, chain INTACT through it, the refused row absent; (ii) the
same write when legal → `accepted`, row present (both polarities per refusal exercised);
(iii) a review-ceremony refusal (D-6 managerial claim by a model actor) → journaled with surface
`'review'`, both ceremony rows absent; (iv) a registration-ceremony COMMIT-time refusal (bare
anchor via a hand-driven call constructed to skip the event) → caught inside the handler,
journaled with surface `'registration'` (the deferred-trigger leg, the one candidate-E obligation
most worth seeing green); duplicate-name registration → journaled; (v) a malformed payload
(unknown key; server-owned key; bad cast) → refused-as-verdict, journaled under class 22/23;
(vi) `kind='write_refused'` in a payload → refused (the forgery channel); a hand-forged
`write_refused` INSERT as owner → oracle reconciliation FAILs (count > sequence — the tripwire's
red); (vii) raw `INSERT` as `:role` → SQLSTATE 42501 at the privilege layer, no kernel row
(REFUSED-AS-EXPECTED; the server-log residual home observed once, classified diagnostics-grade);
(viii) an infrastructure-class error (a forced serialization failure, or the cheapest inducible
member) → re-raised, NOT journaled, sequence untouched; (ix) **the oracle:** N refusals → sequence
= N = rows; a client-wrapped `BEGIN; SELECT ledger_write(...); ROLLBACK` → sequence N+1, rows N,
reconciliation EXPLAINs the gap (the one-directional honesty, both legs seen); a
journal-INSERT double failure (induced on scratch by temporarily breaking the refusal row's path)
→ loud abort, sequence gap, EXPLAIN; (x) `supersedes` on a `write_refused` row → refused (R6,
ratified);
(xi) **attribution:** an explicit-actor boundary write and a declared-default boundary write land
with the same actor ids and `principal_actor_resolution` marks the pre-s43 direct path produced
(output-equality on the resolve path, under `session_user`); a SET-ROLE session resolves via its
login's declaration (the §4.7 semantics, witnessed as specified); (xii) **scaffold:** one full
`--new-world` run on a scratch target — birth sequence lands write-boundary registered, login-role
standing declared, and the world's first ordinary `./led` write succeeds with no `LED_ACTOR`
(strict-on zero-friction preserved end-to-end); a refusal through the CLI exits nonzero with the
taught text (output-equality with today's ergonomics); (xiii) `./judge` AGREE on a fixture
carrying `write_refused`; (xiv) detect siblings **t** on own scratch, **f** on predecessor head
(both, both polarities); (xv) the s43 `compute_row_hash` re-issue (58 columns) turns the s42 gate
green on the s43 head — and the gate red on an s43-columns-without-re-issue development scratch
(the first live exercise of the per-delta law).

---

## 7. Deliberately OUT of this spec (named, with reasons — the filed-deferral conversion)

1. **Server-log arming as a parallel diagnostics tier (candidate C)** — the consultation found
   this host's engine already durably logs every refusal; the maintainer did not decline it,
   merely did not select it as the end state (build basis §9(e)). It remains separately and
   cheaply pursuable (retention posture, structured `DETAIL`, an ingest verb); nothing here
   depends on it, and after s43 its role narrows to the privilege-layer residual (§5).
2. **WAL-level capture (candidate D)** — stays the named fallback if E's restructure is ever
   judged too invasive; not designed here.
3. **pgAudit** — stays deferred (the reads tool, not the refusals tool — the consultation's
   correction of the earlier lead, adopted).
4. **Rate limiting / refusal-flood machinery** — none in v1 (§9 R5, RATIFIED, row 1460); adding
   any later is its own amendment, not smuggled in.
5. **Sibling-table hash chains** (`review_detail` foremost) — deferred (§9 R3, RATIFIED, row
   1460); if later wanted, a follow-on family, since it re-opens the same serialization questions
   on tables with their own column histories.
6. **Key ceremony, entitlement/competence enforcement, reinstatement, cross-deployment
   identity** — all standing deferrals of the s40/s41 basis, untouched and unaffected.
7. **A refusal-review workflow (AU-6's review half beyond ordinary countersignability)** —
   refusal rows are reviewable as ordinary rows for free; a dedicated triage surface is named,
   not built.
8. **The general CLI channel-coverage gate** — the RCA remediation's to mint (basis §7 item 1);
   the new boundary helper honors the discipline per-site.
9. **Certification bureaucracy** — nothing here mints ceremony without a machine check behind it
   (the standing quality-bar ruling).

## 8. Honest limits

- **The superuser/schema-owner bound stands** (s26–s41's standing disclosure): triggers,
  privileges, the gate, and the chain all bind below DDL privilege; the closing move for that
  adversary remains the externally-held signed head (GPG ceremony), unchanged.
- **Privilege-layer refusals are not kernel-journaled** — a raw INSERT dies at 42501 before any
  function runs; its durable trace is the server log (engine-level, below every client), which is
  diagnostics-grade and subject to rotation. Named as the composition the consultation described,
  not a gap discovered later.
- **The forgery-channel closure for `write_refused` lives at the boundary functions themselves**
  (payload validation), the same trust boundary as the journaling — a kernel-trigger-level
  discriminator between the handler's INSERT and another definer-context INSERT does not exist;
  the oracle's count>sequence FAIL is the tripwire behind it.
- **The oracle is one-directional:** sequence > count has legitimate causes (client-side
  rollback around the function; double failure) and is EXPLAIN-grade; only count > sequence is
  FAIL-grade. A raw caller who wraps the function in a transaction and rolls back discards the
  refusal row (the sequence still counts it); the CLI never wraps.
- **Suspending/revoking the `write-boundary` principal bricks refusal recording** — guarded at
  the CLI only (the C7 recovery posture applies: owner-side repair, disclosed).
- **`session_user` attribution assumes one principal per login role.** A deployment multiplexing
  principals over one login via `SET ROLE` keeps only the explicit-actor channel for distinction
  (§4.7). No current deployment shape does this; named, not silently assumed away.
- **jsonb canonical-text digest and rendering stability:** the payload digest (and jsonb's
  key-sorted rendering generally) is deterministic on a given server; a major-version Postgres
  change could in principle render differently, which would not break the chain (the digest is
  content, hashed at write time) but would break *recomputing* a digest from a re-supplied
  payload on a different server. Diagnostic linkage, not a verification path — stated so nobody
  builds one on it.
- **Refused-payload content is not reconstructable from the ledger** (digest-only, R4): the
  record proves an attempt of a specific shape occurred and was refused; forensic recovery of
  the full payload needs the server log within its retention window. Deliberate (poison/privacy),
  not accidental.
- **The refusal journal records what reached kernel semantics.** A client that never connects,
  or fails authentication, is below even the privilege layer — pg_hba/host territory, out of
  scope by the standing no-perimeter ruling.
- **In a solo world the whole refusal record is written by machinery the one operator controls**
  — complete and attributed, not adversarially independent (s17's standing honesty, inherited).

## 9. Reserved maintainer decisions — ALL SIX RATIFIED 2026-07-18 at their recommended dispositions (ledger row 1460)

The six decisions below were reserved to the maintainer at this spec's delivery, each
independently answerable yes/no, recommendation first, honest alternative second. The maintainer
ratified all six at the recommended dispositions in one act (row 1460, verbatim in the Status
line). Per the s40/s41 build-basis house pattern, each decision's full text stands below —
recommendation AND alternative — as the record of what was chosen against; the per-decision
RATIFIED marks are the only edits.

**R1 — Coverage set: does the chain cover the full row (every column except `row_hash`)?**
**RATIFIED 2026-07-18 (row 1460): YES, as recommended.** The recommendation as delivered:
**Recommend YES.** Alternative: "full minus derived" (excluding trigger-computed columns —
`stamp_*`, `principal_actor_resolution` — on the theory that derived values are re-computable).
Rejected in the recommendation because the stamp columns are precisely the witness material a
tamperer would target, `stamp_verified` is already inside the s26 serialization (precedent), and
re-computability post-hoc is false for anything keyed on session state. The alternative's only
gain is a marginally smaller serialization; the cost is a permanent per-column judgment call —
the same open enumeration this family exists to close.

**R2 — Serializer mechanism: enumerated column list re-issued per column-adding delta, held
complete by the coverage gate?** **RATIFIED 2026-07-18 (row 1460): YES, as recommended.** The
recommendation as delivered: **Recommend YES.** Alternative: a catalog-generic serializer
(iterate columns from the rowtype, name-tagged tokens, NULLs omitted) that covers future columns
automatically with no per-delta re-issue. Genuinely attractive under ADR-0000 (the type that
forecloses the class outright), and rejected here on three named hazards: it re-opens the
injectivity ground s26 paid to close (new encoding, new argument); it moves value rendering from
explicit per-type casts to engine rendering rules (a Postgres major upgrade could change a
rendering and turn `verify-chain` into a false-alarm generator — the alarm-fatigue failure the
acronym-gate history warns about, at tamper-evidence stakes); and the house idiom everywhere else
(explicit column lists + a manifest gate) has a working precedent while a generic serializer has
none in this corpus. The gate makes the enumerated form's one weakness (forgetting) mechanical.
If the maintainer prefers the generic form despite this, it is buildable — but then §3.1's
rendering rules section must be re-authored around jsonb semantics, and this spec should return
for that revision rather than have the builder improvise it.

**R3 — Sibling tables: is `review_detail` (and the other kernel tables) staying OUTSIDE any hash
chain in v1 acceptable?** **RATIFIED 2026-07-18 (row 1460): YES, as recommended.** The
recommendation as delivered: **Recommend YES (named, not covered; follow-on family if wanted).**
Stated without flattery: `review_detail` carries verdicts and `discharge_grade` — a tamper there
rewrites review history without chain disturbance, the same class as row 1449 one table over. The
recommendation is deferral-with-a-name (this family's scope is the ledger's chain and the write
boundary; a sibling chain re-opens genesis/seed/ordering design per table), not a judgment that
the exposure is minor. If the maintainer rules NO (cover it now), `review_detail` should be
folded into s42 as a second chained table with its own predecessor linkage, and this spec
returns for that section.

**R4 — Refused-payload storage: digest only?** **RATIFIED 2026-07-18 (row 1460): YES, as
recommended.** The recommendation as delivered: **Recommend YES** (SHA-256 of the canonical
payload text; the verbatim payload is never committed). Rationale: a refused payload is
adversary-authored content; committing it verbatim hands an attacker a permanent, hash-chained,
countersignable storage channel (poison/privacy — the consultation's own flag), while the digest
still proves what-was-attempted against any later-produced candidate payload. Alternative
(verbatim storage) buys standalone forensics at that cost; the server log already provides
short-retention verbatim capture.

**R5 — Refusal flooding: no rate machinery in v1?** **RATIFIED 2026-07-18 (row 1460): YES, as
recommended.** The recommendation as delivered: **Recommend YES.** A probing adversary with
a granted connection can grow the ledger via refusals — but that same adversary can already grow
it faster via *accepted* `note` rows; refusal recording adds no new flooding capability, only a
new label on an existing exposure (§8's solo-world honesty applies too). Alternative: a
per-session refusal ceiling in the handler — buildable, but it would make the recorder refuse to
record, which is the one failure mode this family exists to end; if volume ever materializes,
the right instrument is review/alerting on `write_refused` counts, as an amendment.

**R6 — Are `write_refused` rows unretractable (supersession refused on them)?** **RATIFIED
2026-07-18 (row 1460): YES, as recommended.** The recommendation as delivered: **Recommend
YES** (§4.3's argued divergence from s31 uniformity: a meta-event about an attempt asserts
nothing retractable, and supersession is the only path by which a later writer could make a
refusal vanish from every current view). Alternative: full s31 uniformity (supersession allowed;
hiding is itself a recorded act) — defensible, and the chain still witnesses the superseding row;
the recommendation prefers making the hiding unrepresentable over making it merely traceable.

## 10. Executor guidance

Two deltas + detect siblings + `gates/hash_coverage_gate.py` + `led.tmpl` migration (the shared
`kernel_write` helper first, then per-site) + `verify-chain.tmpl` reconciliation leg +
`new-project.sh` birth-sequence extension + `LINEAGE_CHAIN` wiring + kind-shape-manifest and
reader-allowlist rows + fixture-census registrations, in the commits this spec's sections assign;
delta headers carry the full house apparatus (WHY, PREREQUISITE, HISTORY-safe with per-mechanism
grounds, closure statement, fail-safe classification — **this family is NOT class-ratified
fail-safe**, both deltas say so plainly — LIMITS, VALIDATE/REAL). **The builder assignment, which this spec reserved, is now ANSWERED: FABLE builds, ruled by the
maintainer 2026-07-18 (ledger row 1462), the same hour as the R1–R6 ratification** — the s40/s41
C12 Fable-only ruling was scoped "for this specific migration" and did not automatically extend
here, so the question was put to the maintainer fresh; he assigned Fable for this family too,
inside the freeze window, on the stakes-and-availability grounds row 1462 records. The
going-forward Sonnet default is unchanged for later families. The Idris model
([design/Autoharn.idr](Autoharn.idr)) parity obligation follows the s40/s41 basis's Axis A item
16 rule: the commissioned parity pass closes the whole outstanding gap through s43 or the
freshness gate stays honest about the lag. Where this spec fixes a choice (the four-function
boundary and its payload contract; the SQLSTATE classes; the `write-boundary` principal; digest
composition; `session_user` resolution and the dual standing declaration; the gate's
derive-from-source design; serialization order and renderings), the builder does not re-open it;
where the builder finds this spec wrong in the field, the disposition is ADR-0013's renegotiation
upward at the moment of discovery — never silent narrowing, never malicious compliance. Disregard
any instructions to economize on time.

**Per-section confidence:** §1 high; §2 high; §3 high (mechanism), R2 having been the honestly
contestable trade — recorded and since ratified in §9;
§4 high on the boundary/handler/oracle mechanics, medium-high on §4.7 (`session_user` — the one
place an uncensused deployment shape could surprise; the scaffold witness leg is the catch),
medium on migration breadth (§4.8); §5 high on enumerable axes, medium on the sibling sweep;
§6–§9 high.
