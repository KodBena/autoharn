<!-- doc-attest-exempt: commissioned build basis, frozen pending maintainer ratification. -->

# FABLE-MISSIVES-KERNEL-SPEC — the cross-world missive family (s58/s59), construction grade

Fable-authored 2026-07-23, OUT OF FRAME by the maintainer's instruction: a fresh instance
without the commissioning sessions' working context, converting a ratified consult into a
buildable kernel spec. **This document re-opens no design question.** Its basis:

- `design/CONSULT-FABLE-CROSS-WORLD-COMMUNICATION-2026-07-23.md` — the consult, ALL SEVEN
  adjudications adopted AS RECOMMENDED (ledger row 1157): **(Q1)** receiver-pull over the
  existing boundary multiplexer; **(Q2)** the kernel family routes as full Fable-spec +
  maintainer ratification (it mints vocabulary — the s53 precedent, NOT the class-ratified
  fail-safe lane); **(Q3)** courier principal scoped to `missive_received` ONLY; **(Q4)** a
  received `request` NEVER auto-opens local work, no exception even for the maintainer's own
  directives; **(Q5)** s54 crediting stands (foreign testimony credited immediately at
  testimony rank); **(Q6)** DIRECTIVE/BACKFLOW retire after ONE full live thread witnessed
  end-to-end, then freeze; **(Q7)** supersession-to-withdrawal coupling trigger-enforced on
  `missive_sent`.
- Ledger rows 1155/1156 (commission lineage: build-now sequencing, the two witnessed file
  protocols as the recurrence evidence) and row 1162 (single-trust-domain bound, durable:
  forward compatibility as NAMED EMPTY SLOTS, never designs; no signing in v1, the s41
  `principal_key_bound` slot named; loopback-bound single-operator deployment).
- House idiom: `kernel/lineage/s43` (write boundary), `s53`/`s54` (belief substrate + the
  multi-part-delta model), `s56`/`s57` (current head pattern: HISTORY headers, `.detect.sql`
  siblings, grants, comments); `serving/boundary_service.py` (the transport);
  law/adr/0000 (closure statements per the 2026-07-02 amendment), 0002, 0008, 0012, 0020.

Where the consult's ratified text under-determined a construction decision, the decision is
taken here and **flagged in §13** — those flags are the ratification's attention points, not
silent absorptions (ADR-0002; CLAUDE.md's surface-the-divergence rule).

Everything below is AUTHORED and SCRATCH-WITNESSED only. It reaches reality at a FUTURE
world's birth chain (runs-are-strictly-linear, 2026-07-11); nothing patches an existing
world. Sonnet executes from this spec per the standing delegation contract.

---

## 0. What is being built, in one paragraph

Two lineage deltas after the current head s57: **s58 (missive substrate)** — three new
kinds (`missive_sent`, `missive_received`, `missive_disposed`), ten `missive_`-prefixed
kind-scoped columns carrying the wire envelope (the envelope IS the row shape — one home,
no second serialization contract, ADR-0012 P7), a one-row `kernel.world_identity` table,
five new refusal triggers plus a fourth re-issue of `validate_supersession_target`, the
birth-registered `courier` principal whose kernel-enforced kind-allowlist makes
"foreign content binds local obligation" unrepresentable, and one new SECURITY DEFINER
ceremony function `kernel.missive_dispose(jsonb)`; **s59 (missive views)** — six derived
views (view-only, zero columns, zero kinds, the s54/s56 discipline), one of which
(`missive_outbound`) is the served transport feed. Plus, same commit: VIEW_REGISTRY /
WRITE_SURFACES growth in `serving/boundary_service.py`, the scripted repo-root `courier`
verb (receiver-pull over `/views`, writes through the LOCAL s43 boundary only), `./pickup`
mail counts, gates and `.detect.sql` siblings.

## 1. Delta structure and head-body bases

**Slots: s58 + s59**, split on the s53/s54 precedent (substrate delta: kinds, columns,
CHECKs, triggers, function, hash/view re-issues; views delta: view-only, hash untouched,
`compute_row_hash` untouched — the s54/s56 discipline restated in s59's own header).

**THE HEAD-BODY RULE** (the s44/s45/s53 discipline, verbatim): at authoring, the lineage
head is s57. The most recent re-issuers of the objects s58 must re-issue, verified by
directory read before authoring (the builder re-verifies at build time):

| Object | Base head text | s58 action |
| --- | --- | --- |
| `ledger_kind_check` | s57 (27 members) | re-issued widened to 30 |
| `compute_row_hash` | s57 (77 columns) | re-issued to 87 (ten appended, catalog ordinal order, before predecessor link) |
| `ledger_current` / `countersigned_in_force` | s57 | re-issued +10 appended at end (the s20 lesson) |
| `validate_supersession_target` | s53 (s43+s45+s53 blocks) | fourth re-issue: prior blocks byte-identical, missive blocks appended |
| `refusal_surface_check` | s57 (six members) | re-issued widened by `'missive_dispose'` (seventh) |

s59 re-issues nothing; it creates six new views (no pre-existing reader of any name —
verified by grep at build time, the s56 §7 discipline).

PREREQUISITES: s58 hard-requires s57 (it re-issues s57's own head texts and widens its
`refusal_surface_check`) and transitively s43 (verdict type, journaler), s51/s52 (artifact
tokens in `missive_cites`), s53 (the belief substrate §4 rides). s59 hard-requires s58
(reads the typed columns). Failure mode on a pre-head kernel: loud, at CREATE/ALTER time —
the disclosed hard-dependency posture (s56's precedent).

LINEAGE_CHAIN wiring: **NOT wired by this build** — the s56/s57 precedent. Entering
`bootstrap/new-project.sh`'s LINEAGE_CHAIN is the maintainer's act at a future world's
birth. Scratch witnessing (§11) applies the chain explicitly file-by-file, the s57
VALIDATE idiom.

## 2. s58 — the missive substrate

### 2.1 World identity: `kernel.world_identity` (one home for "which world am I")

The consult's "the local world name is a birth-time kernel setting the scaffold writes —
one home" (§4.2), made concrete. No such setting exists in the kernel today (verified:
no settings/identity table anywhere in `kernel/lineage/`); minted here:

```sql
CREATE TABLE IF NOT EXISTS :"kern".world_identity (
    one_row    boolean PRIMARY KEY DEFAULT true CHECK (one_row),  -- singleton by type
    world_name text NOT NULL CHECK (world_name ~ '^[a-z0-9-]{1,64}$')
);
REVOKE ALL ON :"kern".world_identity FROM PUBLIC;
GRANT SELECT ON :"kern".world_identity TO :"role";   -- read the identity, never write it
```

- `world_name` carries the **deployment name** — the boundary multiplexer's own
  one-home naming surface (P1: no second registry). Its CHECK is byte-identical to
  `serving/boundary_multiplex_config.py`'s `_DEPLOYMENT_NAME_RE` (`^[a-z0-9-]{1,64}$`) —
  the one existing shape authority for world names, cited in the column COMMENT.
- Written ONCE by the scaffold's birth sequence (`bootstrap/new-project.sh`, the same
  commit that wires s58 into LINEAGE_CHAIN — the maintainer's future act; the scratch
  witness seeds it by hand-scripted INSERT as the owner, exactly as genesis is seeded).
- An s58 world with an EMPTY `world_identity` refuses every missive write loudly
  (`validate_missive_identity` aborts with teach-text) — fail-safe, the s43 Element 6
  write-boundary-principal precedent (a birth step skipped is a loud abort, never a
  silent default).

### 2.2 Kinds: three, the 28th–30th members

`ledger_kind_check` re-issued (DROP+ADD, its one home) with s57's 27 members verbatim plus:

- **`missive_sent`** — author-side: this world addressed this missive to that world.
  Actor: a real local principal (orchestrator, maintainer CLI identity — never the
  courier, never a shared comms account; authorship is attributable). Consumers (row
  1906): `missive_outbound` (the transport feed), `missive_delivery_audit`, the
  addressee's provenance token.
- **`missive_received`** — addressee-side: these bytes arrived from that world. Actor:
  the local `courier` principal (§2.6), and the ONLY kind that principal can write
  (§2.5, Q3). Consumers: `missive_undisposed` (→ `./pickup`), the belief substrate as
  the one sanctioned `belief_source` for cross-world testimony (§4), `missive_receipts`
  (→ the courier's cursor/diff), `missive_stale`.
- **`missive_disposed`** — addressee-side lifecycle close: `regards` the receipt row;
  `missive_disposition` in the closed vocabulary. Actor: a local DECIDING principal —
  structurally never the courier (Q3). Consumers: `missive_undisposed` (which it removes
  the item from), the acknowledgment missive `kernel.missive_dispose` writes in the same
  guarded block (§2.7).

COMMENT ON the constraint follows the s53/s57 pattern (names this file, the consult, and
row 1157).

### 2.3 Columns: ten, `missive_`-prefixed, nullable, no DEFAULT (the s30 lesson)

The wire envelope's keys ARE these column names — `kernel.ledger_write(jsonb)`'s payload
convention, so there is no second codec to drift (P7 foreclosed by construction, the
consult §3.2's ratified disposition).

| Column | Type | Kind-shape | Value/coupling |
| --- | --- | --- | --- |
| `missive_protocol` | int | two-way on the two envelope kinds¹ | `= 1` (v1 closed — a v2 envelope is unrepresentable at construction, which IS the consult's "receiver refuses a version it does not implement" as a typed refusal; the version field itself is the named forward-compat hinge, row 1162) |
| `missive_author_world` | text | two-way¹ | `~ '^[a-z0-9-]{1,64}$'`; plus `missive_author_world IS NULL OR missive_author_world <> missive_addressee_world` (self-missives refused — no nameable consumer, row 1906; §13 item 12) |
| `missive_addressee_world` | text | two-way¹ | `~ '^[a-z0-9-]{1,64}$'` |
| `missive_thread` | text | two-way¹ | `~ '^[a-z0-9-]{1,64}/[a-z0-9._-]{1,128}$'` — `<minting_world>/<slug>`, globally unique with zero coordination (one home per name, consult §3) |
| `missive_seq` | int | two-way¹ | `>= 1` — author-local sequence; `(author_world, thread, seq)` is the missive's global identity and dedup key |
| `missive_act` | text | two-way¹ | `IN ('assertion','request','response','acknowledgment','withdrawal')` — the closed five-act vocabulary, consult §3.1; a sixth act is a vocabulary revision, never a closest fit (ADR-0008) |
| `missive_responds_to` | text | one-way (envelope kinds only) | `~ '^xrow:[a-z0-9-]{1,64}:[0-9]+:[0-9a-f]{64}$'`; coupling: `missive_act NOT IN ('response','acknowledgment','withdrawal') OR missive_responds_to IS NOT NULL` (mandatory on the three replying acts; optional on assertion/request — a successor may cite its predecessor) |
| `missive_provenance` | text | **two-way on `missive_received` ONLY** | xrow shape as above. The addressee-side citation of the authoritative author-side `missive_sent` row. FORBIDDEN on `missive_sent`: a row cannot carry its own `row_hash` (circular — the hash covers every column); the author-side token is MINTED by the `missive_outbound` view from `(world, id, row_hash)` at serve time. §13 item 1 — the one place this spec must depart from the consult's field table to be constructible at all. |
| `missive_cites` | text | one-way (envelope kinds only) | non-empty when present (`btrim <> ''`); comma-separated `row:`/`artifact:`/`xrow:` tokens, validated by `validate_missive_tokens` (§2.4) |
| `missive_disposition` | text | see below² | `IN ('consumed','declined','superseded-unread','escalated')` — the closed disposition vocabulary, consult §8 |

¹ "Two-way on the two envelope kinds" is spelled
`(kind IN ('missive_sent','missive_received')) = (col IS NOT NULL)` — a TWO-member
kind-set in a kind-shape CHECK, a mild extension of the house one-kind idiom.
`gates/kind_shape_manifest_gate.py`'s classifier is extended in the same commit to parse
it (the s43 FORBIDDEN_ON_KIND precedent: a new CHECK idiom is never left silently
unparseable).

² `missive_disposition` has three CHECKs (§13 item 7 — the disposition travels TYPED in
the acknowledgment, never as prose-only, per ADR-0008/ADR-0020):

```sql
-- mandatory on the disposition event:
CHECK (kind <> 'missive_disposed' OR missive_disposition IS NOT NULL)
-- allowed homes: the disposition event, and the acknowledgment missive that carries it back:
CHECK (missive_disposition IS NULL OR kind = 'missive_disposed' OR missive_act = 'acknowledgment')
-- mandatory on acknowledgments (spelled off the act value, vacuous elsewhere — s53 ELEMENT 3 idiom):
CHECK (missive_act IS DISTINCT FROM 'acknowledgment' OR missive_disposition IS NOT NULL)
```

Additionally, `missive_disposed` requires its subject:
`CHECK (kind <> 'missive_disposed' OR regards IS NOT NULL)` (one-way on the core column;
the cross-row fact "regards names a `missive_received` row" is trigger territory, §2.4).

Every CHECK ships split one-concern-per-CHECK (kind-shape vs value vs coupling — the
s40/s53 idiom), each with a COMMENT naming this spec and the consult section. The body
travels VERBATIM in `statement` (existing column); a body beyond ledger bounds is an
`artifact:` token in `statement` plus the token in `missive_cites` — no synopsis, so no
ADR-0020 witness is owed for transport (consult §3, §5).

### 2.4 Refusal triggers: five new single-purpose `validate_*` members

All BEFORE INSERT ON ledger, beside the existing family, never folded into a dispatcher
(ADR-0012 P1). Alphabetical firing order note: `set_actor` (s < v) fires before every
`validate_*`, so `NEW.actor` is resolved when the courier-scope trigger reads it;
`zz_set_row_hash` still fires last (the s26 mechanism, preserved — every new trigger name
sorts between).

1. **`validate_missive_identity`** — fires when `NEW.kind` is an envelope kind. Reads
   `kernel.world_identity`; empty table → loud abort with teach-text ("this world has no
   registered world identity — the s58 birth step was skipped", the s43 Element 6
   posture). `missive_sent`: `missive_author_world` must equal the local name;
   `missive_received`: `missive_addressee_world` must equal it. A world cannot record
   itself sending another world's missive or receiving one not addressed to it
   (consult §4.2, verbatim semantics).
2. **`validate_missive_dedup`** — on `missive_received`: refuse when ANY row (raw
   ledger, HISTORY-typed — a superseded receipt still blocks re-receipt) exists with
   `kind='missive_received'` and the same `(missive_author_world, missive_thread,
   missive_seq)`. Teach-text states this converts at-least-once delivery into
   exactly-once RECORDING and that the refusal is itself journaled (s43, for free — the
   duplicate attempt is a `write_refused` row, re-delivery visible, never silent). On
   `missive_sent`: refuse a second in-history `(missive_thread, missive_seq)` sent row
   (author is the local world by trigger 1) — the global identity's author-side half,
   and the floor under `kernel.missive_dispose`'s seq computation (§2.7). §13 item 5:
   the consult named received-side dedup only; the sent side is added here, additive
   refusal, fail-safe direction.
3. **`validate_missive_tokens`** — fires when `missive_cites` is non-NULL (which, by
   kind-shape, means an envelope kind — no separate kind test, the s53 pattern). Splits
   on commas; each element must match `row:`, `artifact:`, or `xrow:` shape; local
   `row:`/`artifact:` tokens are EXISTENCE-checked (the s48/s52 mechanism verbatim —
   the same regex/EXISTS bodies, cited); `xrow:` tokens are shape-checked ONLY —
   foreign-ledger existence is deliberately NOT checked at write time (isolation is
   founding; cross-ledger verification is the audit leg, §9 — the consult §4.2's named
   weaker surface). `missive_responds_to`/`missive_provenance` need no trigger work:
   their xrow shape is a value CHECK.
4. **`validate_missive_courier_scope`** — the load-bearing type of the family (consult
   §4.3; ADR-0000 Rule 2(a)). Fires on EVERY insert: resolve the `courier` principal id
   by name from `kernel.principal` (row-addressed, one SELECT; absent → no-op — a world
   with no courier has no courier to scope); if `NEW.actor = courier_id AND NEW.kind <>
   'missive_received'` → refuse, teach-text: *the courier records arrivals and nothing
   else — Q3, ratified; the only path from "missive arrived" to local work, decision,
   belief, or disposition is a non-courier local principal's own attributable write
   citing the receipt (Q4).* This forecloses the defect class — foreign content binding
   local obligations — at the type layer, not as policy: `work_opened`, `commission`,
   `decision`, `belief`, `missive_disposed`, ALL 29 non-receipt kinds are
   unrepresentable under the courier's identity.
5. **`validate_missive_disposition`** — on `missive_disposed`: `regards` must name an
   existing `missive_received` row (raw-ledger row-addressed read); refuse disposing a
   receipt whose `missive_act = 'acknowledgment'` (acknowledgments are consumed
   mechanically by `missive_delivery_audit`; dispositioning them would mint an
   ack-of-ack regress — §13 item 13); refuse when an in-force `missive_disposed`
   already regards the same receipt UNLESS `NEW.supersedes` names exactly that prior
   disposition (re-disposition = same-kind supersession, §2.5).

Triggers 2, 4, 5 and the re-issued supersession trigger read raw `ledger` by
row-addressed/history-typed reads — `gates/ledger_reader_allowlist.py` gains their
entries with reasons, same commit (the s53 ELEMENT 6(e) discipline).

### 2.5 `validate_supersession_target` — fourth re-issue (Q7, trigger-enforced)

Base: s53's head text (s43 write_refused block + s45 standing-lifecycle block + s53
belief block, all byte-identical and first — verified against s53's own body, unedited by
s54–s57). Three appended blocks; the target-row SELECT widens by `missive_thread` and
`regards`:

- **Target `missive_sent`** (Q7, the ratified letter: "superseding a `missive_sent` row
  is refused unless the superseding row is itself the successor missive in the same
  thread"): refuse unless `NEW.kind = 'missive_sent' AND NEW.missive_thread =
  target.missive_thread`. Teach-text: *an author revising its position sends the
  revision — a same-thread successor (`withdrawal`, or a successor
  `assertion`/`request` with `responds_to`) — so the supersession itself travels and
  the addressee's `missive_stale` view sees it; a silent local retraction is exactly
  the F3 staleness class this family exists to close.* No same-actor condition: the
  PARTY is the world, and any local principal may author the successor (the ratified
  text names the thread, not the principal — restated in §13 item 6's note).
- **Target `missive_received`**: refused outright. A receipt is a historical fact of
  arrival; superseding it is the one path by which delivery could be un-recorded
  (F1/F4 re-opened) and by which the dedup guarantee could be argued around. §13
  item 6 — an addition beyond the consult's text, fail-safe direction, alternative
  named there.
- **Target `missive_disposed`**: refuse unless `NEW.kind = 'missive_disposed' AND
  NEW.regards = target.regards` (re-disposition of the same receipt by a deciding
  principal — the s45 same-kind identity-continuity pattern, one more instance).

### 2.6 The `courier` principal — birth registration

The scaffold's birth sequence registers principal `courier` (agent_class `'tool'`, an
existing s13 vocabulary member — the `write-boundary` precedent exactly) through the full
`kernel.registration_write` ceremony, purpose text fixed by this spec:

> Records cross-world missive arrivals pulled over the boundary service — and can write
> nothing else (kernel-scoped: `validate_missive_courier_scope`, s58; consult §4.3, Q3
> ratified row 1157). Never a deciding identity.

CLI guard (the s43 Element 6 precedent, CLI-grade, disclosed): `led principal
suspend|revoke courier` refused at the CLI with teach-text (suspending the courier
silences mail collection; the kernel-side path remains owner repair). The courier holds
no DB role of its own — the courier VERB (§5) authenticates as the world's ordinary
granted role and supplies `actor=<courier id>` explicitly through the s43 boundary
(the explicit-actor channel, s43 Element 8's own named tool for multi-principal logins).

### 2.7 `kernel.missive_dispose(p_payload jsonb)` — the one new SECURITY DEFINER function

The disposition is a TWO-row ceremony (the typed close + the acknowledgment travelling
back) — exactly the shape `kernel.review_write` exists for; single-row missive writes
(`missive_sent`, `missive_received`, `belief`) ride the generic `kernel.ledger_write`
unchanged, the s53 precedent (missive_* payload keys pass its generic key validation with
zero edits — verified against s43's own key loop; they are ledger columns and not
server-owned). §13 item 9.

Shape discipline: byte-follows s57's `obligation_revoke` — SECURITY DEFINER, owner-owned,
`SET search_path = :schema, :kern, pg_temp` (s19), returns `kernel.write_verdict`
(reused, no new type), refusals caught by SQLSTATE class 22/23/P0 and journaled through
the ONE `kernel.journal_write_refusal` (surface `'missive_dispose'` —
`refusal_surface_check` widened by this one member, the s51/s57 pattern), infrastructure
classes re-raised unjournaled, `SET CONSTRAINTS ALL IMMEDIATE` before the accept return,
REVOKE ALL FROM PUBLIC / GRANT EXECUTE TO `:role`.

Payload keys (closed, refuse-unknown-key): `receipt` (required, bigint — the
`missive_received` row id), `disposition` (required, the closed vocabulary), `statement`
(optional — the acknowledgment's body text; when absent, generated as
`disposition: <d> of <provenance-token>` — kernel-authored, bounded, not a paraphrase of
the foreign body, so no ADR-0020 witness is owed), `actor` (optional, the standing
set_actor default otherwise — never re-derived here, ADR-0012 P1).

Guarded block, in order:

1. Refuse-before-write: `receipt` must name an in-force `missive_received` row (loud
   teach-text otherwise); its act must not be `'acknowledgment'` (§2.4 item 5's rule,
   also enforced here for the teach-text quality); duplicate disposition is left to the
   trigger (one home).
2. INSERT the `missive_disposed` row (`regards = receipt`, `missive_disposition`,
   `statement` = a kernel-generated close line, actor per payload).
3. Compute the acknowledgment envelope from the receipt row: `author_world` = local
   world (read from `world_identity`), `addressee_world` = receipt's
   `missive_author_world`, `thread` = receipt's thread, `seq` = `1 + coalesce(max
   sent seq by this world in this thread, 0)` (raw-ledger read; the sent-side dedup
   CHECK-trigger is the race floor — a concurrent same-thread disposition loses with a
   journaled typed refusal, retried by the caller, named limit), `act =
   'acknowledgment'`, `responds_to` = receipt's `missive_provenance`,
   `missive_disposition` = the disposition (typed, §2.3 note ²), `missive_protocol = 1`.
4. INSERT the acknowledgment `missive_sent` row. Same actor. The courier-scope trigger
   makes a courier-actored call to this function refuse at step 2's insert already
   (witnessed red in §11).
5. Return `('accepted', <disposition row id>, NULL, NULL, NULL)`.

Both inserts run the full trigger chain — every §2.4 refusal applies inside the guarded
block and journals as ONE `write_refused` row rolling the whole ceremony (the
review_write atomicity argument: a disposed-without-acknowledgment state is
unrepresentable through this path).

### 2.8 Same-commit set (the s53 ELEMENT 6 idiom)

(a) `compute_row_hash` re-issued to **87 columns** (ten appended in catalog ordinal
order; s42's law, gate-witnessed both polarities); (b) `ledger_current` /
`countersigned_in_force` re-issued +10 appended at end; non-member views re-verified
per the s38 discipline and the result named in the delta header; (c) kind CHECK to 30;
(d) `refusal_surface_check` to seven; (e) `gates/kind_shape_manifest_gate.py`: ten new
MANIFEST rows + the two-member-kind-set classifier extension (¹ above); (f)
`gates/ledger_reader_allowlist.py`: entries for the three raw-reading new triggers and
the re-issued supersession trigger; (g) `gates/hash_coverage_gate.py`: no manual edit
(mechanical chain derivation, verified statement carried in the header, the s53(f)
precedent); (h) `.detect.sql` siblings, behavior-fingerprinted per the
migrate-detect-drift ruling: s58 — `ledger_kind_check` definition carries
`'missive_sent'` AND column `missive_thread` exists (the s53 two-fact pattern); s59 —
view `missive_outbound` exists (the s54/s56 new-object pattern); both witnessed t/f on
both polarities; (i) fixture census bumped.

HISTORY paragraph (owed in the delta header, per-mechanism grounds, the s53 model): all
three kinds are BORN here — every kind-shape/coupling CHECK validates vacuously on
pre-existing rows; the supersession re-issue's new blocks gate on target kinds born here
— unreachable on any prior chain; `missive_dispose` and `world_identity` are new objects
with no pre-existing reader/caller; the surface widening is pure vocabulary addition;
the ten columns/two views/hash follow the standing additive arguments. NOT
class-ratified fail-safe despite the additive shape — it mints ecosystem vocabulary;
ships only under this spec's maintainer ratification (Q2, row 1157; the s53 routing
restated).

## 3. s59 — the missive views (view-only; every consumer named, row 1906)

All `security_invoker`, all reading `ledger_current` (the s31 discipline) except where a
HISTORY read is the view's own point (none here — unlike s56's `review_verdicts`, every
missive view is a current-truth working-set surface; stated in the header so the reader
allowlist question is answered before it is asked). All GRANT SELECT TO `:role`.

1. **`missive_outbound`** — THE SERVED TRANSPORT FEED. All in-force `missive_sent`
   rows, all ten envelope columns plus `statement`, plus the minted provenance token:

   ```sql
   'xrow:' || s.missive_author_world || ':' || s.id || ':' || s.row_hash AS missive_provenance
   ```

   Keyed/paginated by `id` (the append-monotonic strong cursor, `/rows/current`'s own
   guarantee class). **Deliberate divergence from the consult §7's "minus acknowledged"
   filter and "?addressee=" parameter — §13 items 3 and 4**: the feed is the full
   cursor-paged set (the courier pulls `after_id=<its own provenance high-water>`, §5),
   because (a) an ack-filtered feed either never releases acknowledgment rows (nothing
   acknowledges an acknowledgment, §2.4 item 5) or special-cases them, (b) the `/views`
   carrier deliberately supports no column filters and Q1's ground was ZERO new route
   machinery, and (c) a cursor beats provoked-refusal polling, which would poison the
   refusal journal's meaning (s43: a refusal is a denied attempt, not a polling idiom).
   The BACKFLOW working-set discipline the filter served lives in view 6 instead.
   Consumer: the counterpart world's courier.
2. **`missive_receipts`** — courier index: `id`, `missive_author_world`,
   `missive_thread`, `missive_seq`, `missive_act`, `missive_provenance`, and
   `provenance_row_id` = `split_part(missive_provenance, ':', 3)::bigint` (the
   author-side row id, parsed from the pinned token — derived, never a second home).
   In-force `missive_received` rows. Keyed by `id`. Consumer: the courier verb's
   high-water cursor and set-diff (§5) — the mechanism that makes exactly-once
   RECORDING also exactly-once ATTEMPTING in the common case, keeping the dedup
   refusal a race backstop instead of a per-run drumbeat.
3. **`missive_undisposed`** — in-force `missive_received`, `missive_act <>
   'acknowledgment'`, with no in-force `missive_disposed` regarding it. Columns: the
   receipt's id/ts/envelope/statement. Keyed by `id`. Consumer: `./pickup` (mail is
   part of hydration — the resumption doctrine covers cross-world state) and the
   deciding principal choosing dispositions.
4. **`missive_stale`** — undisposed receipts `r` for which a later in-force receipt
   `r2` exists with the same `missive_thread` and same `missive_author_world`, where
   `r2.missive_responds_to = r.missive_provenance` (a successor or withdrawal naming
   exactly the frozen thing `r` records — hash-pinned, never fuzzy thread-recency).
   Columns: the stale receipt + the superseding receipt's id and act. Keyed by `id`
   (the stale receipt's). Consumer: `./pickup` surfacing "do not act on this one" before
   an agent does (consult §9's addressee half, verbatim semantics).
5. **`missive_delivery_audit`** — author-side: in-force `missive_sent` rows with `act
   <> 'acknowledgment'`, each with `acknowledged boolean` (an in-force
   `missive_received` ack row exists whose `missive_responds_to` equals this row's
   minted token and whose `missive_author_world` = this row's addressee) and the ack's
   typed `missive_disposition` (NULL until acknowledged). The consult §7's
   *delivered/acknowledged/consumed-declined* semantics as one queryable surface; also
   where the consult's "minus acknowledged" working set lives (item 1's note).
   Keyed by `id`. Consumer: the author-side operator/orchestrator ("did they get it,
   what did they do with it") and the audit verb leg (§9).
6. **`missive_open_threads`** — one row per thread that is open for THIS world: it
   holds an undisposed non-ack receipt, or an unacknowledged non-ack sent missive
   (view 5's pending set). Columns: `missive_thread`, counts of each open reason.
   Keyed by `missive_thread` (slug-shaped keyset, the A11 discipline). Consumer: the
   orchestrator's working set — the BACKFLOW shrink-as-resolved discipline as a
   derived view over append-only rows (consult §1 item 2, preserved by design).

**VIEW_REGISTRY additions** (`serving/boundary_service.py`, the closed-allowlist growth
mechanism, sixth use — no new route, no version bump, per that dict's own stated
convention):

```python
"missive_outbound":       ("id", "id"),
"missive_receipts":       ("id", "id"),
"missive_undisposed":     ("id", "id"),
"missive_stale":          ("id", "id"),
"missive_delivery_audit": ("id", "id"),
"missive_open_threads":   ("missive_thread", "slug"),
```

**WRITE_SURFACES addition**: `"missive_dispose": "missive_dispose"` (a dict entry through
the existing `make_write_route`, the `obligation_revoke` precedent), plus a
`MissiveDisposeWriteIntFields` model (`receipt`, `actor`) in `boundary_models.py` (A5.2's
enumeration authority).

## 4. Belief-substrate integration — the exact write path (Q5 stands as ratified)

A foreign CLAIM enters local reasoning only as testimony citing the receipt (consult §5;
no kernel change required — s53's shape already carries it, verified against s53's own
coupling CHECKs). The exact act, performed by a local NON-courier principal (the
courier-scope trigger makes a courier-actored belief unrepresentable):

```
POST /d/<self>/write/ledger
{
  "kind": "belief",
  "statement": "<the proposition — quote the missive body verbatim or cite its artifact token;
                 a PARAPHRASE here owes the ADR-0020 cold-read witness, stated not waived>",
  "belief_polarity": "existential",          -- or universal, with its s53 universe obligation
  "belief_basis": "testimony",
  "belief_source": <the missive_received row id>,
  "actor": <the relaying local principal id>
}
```

- `belief_source_coupling` (s53) already enforces source⇔testimony; the FK already
  requires the receipt row to exist. The receipt is the ONLY honest source — "these
  bytes arrived from A" is the locally witnessable fact; content-truth is not asserted
  by arrival (two facts, two homes, ADR-0008).
- Under s54's ratified calculus the belief is credited IMMEDIATELY at testimony rank
  (Q5: revisit only on a witnessed overclaim incident) and is defeated by any
  contesting local observation (evidence-class precedence); `shared_premise` sees
  through the boundary. Nothing here edits s54.
- A received `request` is NEVER shoehorned into a belief (a directive is not a
  proposition — ADR-0008); requests live entirely in the §2/§3 lifecycle, and their
  acceptance is ordinary local work/decision rows citing the receipt — written by a
  deciding principal, which is Q4 discharged by the same courier-scope type.

## 5. The courier verb — scripted, receiver-pull, local-boundary-only

Repo-root executable **`courier`** (Python, top-of-file imports only, the standing
edict), per the self-application rule: never prose steps. Configuration: a
`courier.toml` beside `boundary-multiplex.toml` —

```toml
authn = "single-operator"          # the NAMED EMPTY SLOT (row 1162): any other value is
                                   # refused at load with teach-text naming the slot; a
                                   # future trust model arrives as a new protocol version
                                   # and a ratified spec, never a retrofit.
self = "worlda"                    # this world's deployment name (must equal world_identity)
self_base = "http://127.0.0.1:8400"
[counterparts]
worldb = "http://127.0.0.1:8400"   # world name -> boundary base URL (single host today;
                                   # multi-host changes only these VALUES — consult §7)
```

Per counterpart C, one pass:

1. `GET {self_base}/d/{self}/views/missive_receipts` (paginated) → the set of already
   recorded `(author_world=C, thread, seq)` and the high-water
   `max(provenance_row_id)` for C.
2. `GET {counterparts[C]}/d/{C}/views/missive_outbound?after_id=<high-water>&limit=…`
   (paginated to exhaustion). Client-side filter `missive_addressee_world == self`
   (§13 item 4) and set-diff against step 1.
3. For each new missive, in served-id order:
   `POST {self_base}/d/{self}/write/ledger` with payload = the served envelope columns
   verbatim (`kind: "missive_received"`, `statement` byte-for-byte,
   `missive_provenance` = the served minted token, `actor` = the courier principal's
   id, resolved once per run by name from `GET /d/{self}/standing/principals`). A
   `refused` verdict carrying the dedup teach-text is the race backstop — logged,
   counted, the pass continues (idempotent by construction, consult §7). Any other
   refusal, and any infra/typed-503 failure, is a LOUD nonzero exit naming the leg.
4. Report, witness-grade: per counterpart, `pulled/new/recorded/dedup-raced` counts
   with the row ids — WITNESSED lines, no umbrella claims.

The courier NEVER: writes to a foreign boundary (its only POST target is `self_base` —
zero cross-world credentials, the consult §6 layer 1), writes any non-receipt kind
(layer 2 enforces it if the script errs), dispositions, acknowledges (§13 item 2 — the
acknowledgment is `missive_dispose`'s act, authored by a deciding principal at
disposition time; the consult §7's sentence assigning it to the courier is superseded by
the ratified Q3 scope), or summarizes (ADR-0020: transport never transforms).

**`./pickup` integration** (same build): surface `missive_undisposed` and
`missive_stale` counts (and the open-thread list when nonzero), plus a staleness note
when the courier has not run this session — mail is part of hydration; the poll-liveness
ceiling stays a ceiling (consult §11.1), mitigated not closed.

## 6. Lifecycle mapping from the omega filename states (typed events replacing filenames)

The consult §8's table, fixed as the build's conformance surface:

| Witnessed file convention | Typed replacement (this spec) | Whose ledger |
| --- | --- | --- |
| authoring the dispatch file | `missive_sent` (§2.2) via `ledger_write` | author |
| hand-carry, no record | `courier` verb pull + `missive_received` (§5) | addressee |
| `…-consumed.md` counter-file | `kernel.missive_dispose` → `missive_disposed` + acknowledgment `missive_sent` (§2.7) | addressee, then author receives it |
| `…-status.md` in-place edits | further `assertion`/`response` missives in the thread | either |
| `…-clarifications.md` | `request` missive with `responds_to` | either |
| "Status: Open" outliving both ships | `missive_open_threads` / `missive_delivery_audit` — derived, never hand-edited | each side, derived |
| BACKFLOW item removal on fix | disposition closes the thread; the open set is a view (§3.6) | addressee |
| stale directive (within a day, silent) | `withdrawal`/successor supersession (Q7 trigger, §2.5) → `missive_stale` (§3.4) | author acts, addressee sees |

Retirement (Q6, ratified): DIRECTIVE_FROM_AUTOHARN.md / AUTOHARN_BACKFLOW.md run parallel
until ONE full live thread (request → response/disposition → acknowledgment) is witnessed
end-to-end on real worlds, then freeze as point-in-time records (ADR-0005 Rule 8) and all
new traffic routes through missives. The freeze is the orchestrator's operational act,
gated on the witnessed thread — named here, not performed here.

## 7. The named empty slots (row 1162) — dispositions chosen, and why

**Chosen: documented absences anchored to real, already-existing types — NOT
columns-with-vacuous-v1-constraints.** Grounds (the commission's ADR-0012-honesty
question, answered): a column no writer fills and no consumer reads fails the
named-consumer test (row 1906 — ritual, deleted not documented) and falsifies the row
shape's honest footprint (the lying-signature class, P2/P8: a slot in the type that the
system cannot honor). The forward-compatibility hinge this family actually carries is
**`missive_protocol`** — a REAL column with a real v1 CHECK (`= 1`) and a real consumer
(the construction-time version refusal). A future trust model arrives as protocol
version 2: widen the CHECK, add its columns THEN, under its own ratified spec — row
1162's own arrival rule.

- **Signing** — named slot: s41's `principal_key_bound` event kind (already in the
  vocabulary, already hash-covered) is where a missive-signing key binds; the signature
  itself would ride a v2 envelope column beside `missive_provenance` (the consult
  §3.2's own pointer). v1 authenticity is the fetch act under receiver-pull on a
  single-operator host — honest for the row-1162 trust bound; its ceiling is §12.
  Nothing in the v1 shape forecloses v2 (the token currency, the version field, and
  the s41 kind all exist).
- **Wire authn** — named slot: the `authn = "single-operator"` mandatory literal in
  `courier.toml` (§5), refused on any other value with teach-text naming this section.
  Transport authentication is a courier/boundary concern, not a row fact — placing the
  slot in the transport config keeps the one-home rule (a per-row authn column would
  duplicate a per-channel fact onto every record, P1 violated at birth).
- **The broader crypto class** stays under its standing never-re-raise posture; this
  spec adds, generates, and requires no cryptography (SHA-256 row/artifact hashes are
  the kernel's existing content-addressing, not new crypto).

## 8. Engine/ASP disposition — honest, recommended, not smuggled

**v1 does NOT model missives in the engine, and this spec recommends that.** Grounds:
(a) the missive views are operator/courier working-set surfaces whose consumers (§3) are
verbs and humans, not derivations the deductive layer arbitrates yet; (b) the epistemic
half — the part where "the deductive engine is the point" bites — enters through the
belief substrate, which ALREADY has its engine layer (`ledger_belief.lp` + the SQL
floor): a cross-world testimony belief is an ordinary typed belief row whose
`belief_source` happens to be a receipt, and flows through the existing differential
with zero edits (witnessed AGREE in §11, never asserted); (c) a missive-lifecycle ASP
layer would owe an independently-authored SQL twin (I6/ADR-0000 INDEP) — real work whose
consumer is honestly unnameable until at least one live thread exists. **Named
follow-on, gated exactly like the file-protocol retirement (one witnessed live thread):**
an `engine/lp/ledger_missive.lp` + floor pair mirroring
`missive_undisposed`/`missive_stale`/`missive_delivery_audit`, entering `./judge` as its
own layer. Until then, `./judge`'s existing layers are witnessed in AGREE on fixtures
CARRYING missive rows (kind-generic flow-through — the s43 write_refused precedent:
"entry/6 is kind-generic; witnessed, never asserted").

## 9. Follow-ons named, not designed

- The engine missive layer (§8).
- **Panel/SPA**: mail surfaces (undisposed/stale/open-threads/delivery-audit) in the
  panel deployment — that world's own concern (the s56 posture).
- **The cross-ledger audit verb leg** (consult §10): an `audit` leg that, given read
  access to both boundaries, resolves every receipt's provenance token against the
  author world's `/rows/{id}` (id and `row_hash` must match) and every acknowledged
  send against its addressee-side counterpart — advisory-grade, on demand, never a
  per-write check. Buildable entirely on existing routes; deferred with its consumer
  named (the bilateral-record auditor, first needed when two live worlds disagree).
- **Author-side candidate-withdrawal flagging** (consult §9's advisory view — "sent
  missives whose cited local rows have since been superseded"): advisory, deferred, its
  consumer the authoring orchestrator's hygiene pass.
- **Umbrella/descriptor integration** (row 1155's sequencing): the descriptor schema's
  world-identity field aligns with `kernel.world_identity` — the umbrella spec's
  concern, named so the two specs meet on one name shape (`^[a-z0-9-]{1,64}$`).

## 10. Closure statement (ADR-0000 Rule 2(a), 2026-07-02 three-part form)

Claimed class, most general form: *cross-world communication whose delivery, content,
lifecycle, or provenance is unrecorded in the communicating worlds' own audit
substrates, or whose meaning depends on the reader's perspective.*

- **INVARIANT.** In worlds carrying s58/s59 and communicating through this mechanism:
  every cross-world communicative act is a typed, hash-chained, attributed row in the
  acting world's OWN ledger; every travelling record names both parties by stable
  world names (never a direction word) and is content-pinned — the author side by its
  own `row_hash`, the addressee side by the stored `xrow` provenance token; every
  lifecycle transition (sent, received, disposed, acknowledged, withdrawn/superseded)
  is a typed event; a malformed envelope, an unimplemented protocol version, a wrong
  party name, a duplicate `(author_world, thread, seq)` on either side, a courier
  write of any non-receipt kind, a disposition of a nonexistent/foreign/acknowledgment
  receipt, and a `missive_sent` supersession outside a same-thread successor are each
  refused at construction with the refusal itself a committed `write_refused` row
  (s43, inherited); no world holds write access of any form into another world's
  substrate, and the only path from a received request to local work runs through a
  non-courier local principal's own attributable, citable write.
- **QUANTIFICATION UNIVERSE**, enumerated and disposed:
  - *Communicative acts*: the closed five (assertion, request, response,
    acknowledgment, withdrawal) — a sixth is a vocabulary revision (ADR-0008), not a
    fit. *Dispositions*: the closed four. *Kinds*: exactly three; no other kind
    carries any `missive_*` column (kind-shape CHECKs, gate-manifested).
  - *Lifecycle states*: the omega filename states and BACKFLOW disciplines, each
    mapped in §6's table — none unmapped.
  - *Parties*: worlds named in `kernel.world_identity` (self) and `courier.toml`
    (counterparts); a world outside the config is unreachable by construction;
    self-missives refused.
  - *Reference forms*: `row:`, `artifact:`, `xrow:` — no fourth form;
    `xrow` existence-at-write **deliberately not covered** (audit-grade instead,
    §2.4.3/§9 — isolation is founding).
  - *Write surfaces*: the generic `kernel.ledger_write` (sent/received/belief) and
    `kernel.missive_dispose` (the two-row ceremony) — both s43-boundary, both
    journaling; raw owner/superuser DML remains the standing s26+ trust bound, named
    not covered.
  - *Views*: six, each with a named consumer (§3); the two column-complete homes
    re-issued +10; non-members re-verified (§2.8).
  - *Triggers*: five new + one re-issued; firing-order interaction with `set_actor`
    and `zz_set_row_hash` disposed (§2.4 preamble).
  - *Deliberately not covered* (each a consult ceiling or a named deferral, never
    silent): communication outside the mechanism (ceiling 4); poll liveness (ceiling
    1 — pickup mitigates); the unsent withdrawal (ceiling 2 — advisory follow-on §9);
    paraphrase fidelity (ceiling 3 — ADR-0020's witness, owed by whoever
    transforms, restated at both transform sites §4/§5); transport authenticity
    beyond the single-trust-domain bound (ceiling 5 / row 1162 — the §7 slots); the
    engine missive layer (§8); re-disposition CLI ceremony (kernel-lawful via
    same-kind supersession, no verb in v1 — disclosed); panel presentation (§9);
    ratifier judiciousness (ceiling 6 — governance, not type).
- **DENOMINATION.** Identity in `(author_world, thread, seq)` — world names in the one
  existing deployment-name shape, never a second registry; content in SHA-256
  `row_hash`/artifact hashes the chain already uses, never a summary or an mtime;
  delivery in row existence in the addressee's ledger, never a transport return code;
  staleness in typed withdrawal/successor events pinned by hash, never wall-clock age;
  the protocol version in a closed integer CHECK, not a parsed string. No bound in
  this family is a bare round literal (the two length bounds in the thread/world
  shapes derive from the multiplex config's own `{1,64}` authority; 128 for the
  thread slug is generous identifier headroom of the same kind as
  `MAX_AFTER_SLUG_BYTES`'s stated rationale, cited not invented).

## 11. Witness plan (scratch, TOY db, both polarities per leg, red first)

Setup: two scratch schema pairs (`s58val_a`/`s58val_b` + kernels + roles) in the toy db,
each applied s15..s57 + s58 + s59 explicitly (the s57 VALIDATE idiom); genesis seed;
per world: register `write-boundary`, `courier`, and one deciding principal through the
boundary ceremonies; declare standing; INSERT `world_identity` (`worlda`/`worldb`) as
owner (the scaffold's future birth step, scripted in the fixture). One boundary-service
process, multiplex config serving both on loopback. Every claim below reports WITNESSED
with observed output / REFUSED-AS-EXPECTED / UNEXERCISED-with-blocker — no umbrella
claims.

1. **Identity & shape refusals (red first, then green).** As worlda's deciding
   principal via `POST /write/ledger`: refuse `missive_protocol=2`; refuse
   `missive_act='directive'` (unrepresentable authority vocabulary — the §6-layer-3
   witness); refuse `author_world='worldb'` on a sent row (identity); refuse
   `seq=0`; refuse a self-missive (`addressee='worlda'`); refuse an empty
   `world_identity` world (drop the row on a third scratch, witness the loud abort,
   restore). Green: `request` worlda→worldb, thread `worlda/demo-1`, seq 1 — accepted,
   verdict row id captured.
2. **Sent-side dedup.** Red: a second `(worlda/demo-1, 1)` sent row — refused,
   journaled (`write_refused` row observed, surface `ledger`). Green: seq 2.
3. **Serve.** `GET /d/worlda/views/missive_outbound` — rows present; the minted
   `xrow` token's third/fourth fields equal the row's `id`/`row_hash` (checked against
   `/rows/{id}`).
4. **Courier pull (green).** Run `./courier` for worldb: `missive_received` rows appear
   with `actor` = courier id, `statement` byte-identical, provenance stored. Re-run:
   zero new rows, zero new `write_refused` (the cursor/diff path witnessed — the
   journal stays quiet on idle re-runs).
5. **Receipt dedup (red).** Force a duplicate receipt write directly (bypassing the
   diff): refused, and the refusal IS a journaled `write_refused` row (both facts
   observed — the exactly-once-recording claim's own witness).
6. **Courier scope (red × several).** With `actor` = courier id: `work_opened` payload
   → refused (the "missive attempting to open local work" red — the structural Q4
   witness); `decision` → refused; `belief` → refused; `missive_disposed` (and a
   courier-actored `missive_dispose` call) → refused; `missive_sent` → refused. Each
   journaled. Green control: the same payloads under the deciding principal behave
   normally (where otherwise lawful).
7. **No-auto-work (the negative).** After receipt of the `request`: query worldb for
   any `work_opened`/`commission` row — none exists. (The positive path — a deciding
   principal opening work CITING the receipt — is exercised once, green, to witness
   that ratification is the working path, not merely the mandated one.)
8. **Believe.** Worldb's deciding principal writes the §4 testimony belief citing the
   receipt: accepted; appears in `credited_beliefs` at testimony basis (s54); red
   first: `belief_source` naming the receipt with `belief_basis='observed'` → refused
   by s53's coupling (the relay-as-observation lie, unrepresentable — witnessed here
   because this family is its first cross-world exercise).
9. **Dispose + acknowledge.** Red: `missive_dispose` on a nonexistent receipt; on an
   acknowledgment receipt (after step 11 produces one); a second disposition of the
   same receipt. Green: `missive_dispose(receipt, 'consumed')` → one
   `missive_disposed` + one acknowledgment `missive_sent` (typed disposition on it),
   one verdict; `missive_undisposed` empties for that receipt.
10. **Return leg.** `./courier` for worlda pulls the acknowledgment;
    `missive_delivery_audit` on worlda shows `acknowledged=true` with
    `missive_disposition='consumed'`; worlda's `missive_undisposed` does NOT list the
    ack receipt (the no-ping-pong witness); `missive_open_threads` closes the thread
    on both sides.
11. **Withdraw / stale (Q7 both polarities).** Worlda sends a second `request` (seq 3);
    worldb's courier pulls it (undisposed). Red: supersede that sent row with a plain
    `note` → refused by the Q7 block; with a `missive_sent` in a DIFFERENT thread →
    refused; supersede a `missive_received` row → refused; supersede a
    `missive_disposed` by a non-disposition → refused. Green: worlda writes
    `withdrawal` (same thread, seq 4, `responds_to` = the seq-3 token,
    `supersedes` = the seq-3 row id) → accepted. Courier runs; worldb's
    `missive_stale` lists the undisposed seq-3 receipt naming the withdrawal receipt.
    Disposition `superseded-unread` closes it (green), acknowledgment travels back.
12. **Chain and gates.** `./verify-chain` green on both worlds (87-column serializer
    correct, refusal-seq reconciliation consistent with the journaled reds above);
    `gates/hash_coverage_gate.py` green on the s58 head and RED on a
    columns-without-re-issue scratch (s42's law, both polarities);
    `kind_shape_manifest_gate` green with the new classifier arm and RED against a
    deliberately mis-declared manifest row; `.detect.sql` t on applied / f on
    s57-head scratch (both files, both polarities).
13. **SQL/ASP differential, stated honestly.** `./judge` on both fixture worlds across
    its existing layers: witnessed in AGREE with missive rows present (kind-generic
    flow-through) and with the step-8 testimony belief exercising the belief layer's
    typed arm. **No missive-specific engine layer exists in v1** — recommended-not-
    built, grounds and gate in §8; this line is the honest disposition, not a coverage
    claim.
14. **One full thread end-to-end** (steps 1→10 compose into it) is the Q6 gate's
    SCRATCH rehearsal; the LIVE witnessed thread that triggers DIRECTIVE/BACKFLOW
    freezing happens on real worlds after birth — named, not claimed here.

## 12. Honest limits (pre-registered; the consult §11 ceilings restated as this build's)

1. Poll liveness: an unrun courier is an unread mailbox — pickup surfaces it, cannot
   close it.
2. The unsent withdrawal: no addressee mechanism can see an event the author never
   recorded; advisory author-side flagging is a named follow-on (§9).
3. Paraphrase fidelity: mechanically out of reach; ADR-0020's witness is owed by
   whoever transforms (both transform sites named, §4/§5).
4. v1 authenticity = the fetch act on a single-operator host (row 1162's bound); a
   hostile network invalidates it; the upgrade slots are §7, empty by ratified choice.
5. The owner/superuser direct-DML trust bound stands (s26+); dedup, courier scope, and
   receipt-unretractability bind granted-role paths only.
6. `missive_dispose`'s seq computation can race a concurrent same-thread disposition —
   the loser gets a journaled typed refusal and retries (disclosed, not hidden).
7. Re-disposition ships kernel-lawful (same-kind supersession) but verb-less in v1;
   the second-order acknowledgment for a re-disposition is manual (disclosed).
8. Semantic authority: the kernel makes foreign asks non-binding; it cannot make a
   local ratifier judicious (ceiling 6 — governance).
9. In a solo deployment both sides' records are written by machinery one operator
   controls — complete and attributed, not adversarially independent (s17's honesty).

## 13. Construction decisions the ratified text under-determined — THE ATTENTION POINTS

Each: the decision taken, and its alternative. These are what ratification should read
closely; none re-opens a Q1–Q7 ruling.

1. **Provenance cannot be an author-side stored column.** The consult's §3 field table
   says `missive_provenance` is "filled by the author," but a row cannot contain its
   own `row_hash` (the hash covers every column — circular). Taken: the token is
   MINTED by the `missive_outbound` view from `(world, id, row_hash)` at serve time;
   the column is stored two-way on `missive_received` only. Alternative: none
   coherent within the s42 hash law; flagged because it edits the ratified table's
   letter to make it constructible.
2. **Acknowledgment authorship.** Consult §7's courier-verb paragraph has the courier
   authoring the acknowledgment; ratified Q3 scopes the courier to `missive_received`
   ONLY. Taken: the acknowledgment is written by `kernel.missive_dispose` under the
   deciding principal at disposition time (which §8 of the consult itself describes).
   Alternative: widening courier scope — contradicts Q3, not available.
3. **`missive_outbound` serves the full cursor-paged set**, not "minus acknowledged":
   an ack-filtered feed never releases acknowledgment rows (nothing acknowledges an
   acknowledgment) and invites provoked-refusal polling that would poison the s43
   journal's meaning. The "minus acknowledged" working set lives in
   `missive_delivery_audit` instead. Alternative: special-casing ack rows inside the
   served feed — more state in the transport surface for no consumer.
4. **No `?addressee=` filter parameter.** The `/views` carrier deliberately has no
   column filters, and Q1's ratified ground was zero new route machinery. Taken:
   courier-side filter + `after_id` cursor. Alternative: a filter query param on the
   views route (new route machinery).
5. **Sent-side dedup added** (consult named received-side only): `(thread, seq)`
   uniqueness on `missive_sent` — the global identity's author half, and the floor
   under the ceremony's seq computation. Additive refusal, fail-safe direction.
   Alternative: authoring discipline only.
6. **Supersession targets beyond Q7's letter**: `missive_received` refused outright
   (a receipt un-recorded re-opens F1/F4); `missive_disposed` superseded only
   same-kind/same-regards (re-disposition). Q7's own `missive_sent` block carries NO
   same-actor condition (the party is the world; any local principal may author the
   successor — the ratified sentence names the thread, not the principal).
   Alternatives: s57-style disclosed non-foreclosure for receipts/dispositions;
   holder-only supersession on sent rows.
7. **Typed disposition on acknowledgments** (`missive_disposition` allowed and
   mandatory on `missive_act='acknowledgment'`): the disposition crosses as a closed
   vocabulary value, not prose (ADR-0008: two facts not fuzzy-matched; ADR-0020: no
   transform in transit). Alternative: prose-only in the ack statement, with the
   typed fact living only addressee-side.
8. **World identity's home**: a new one-row `kernel.world_identity` table, birth-
   written, SELECT-only to the role — the consult's "birth-time kernel setting" made
   concrete. Alternative: a Postgres GUC/setting (not durable or grantable as
   cleanly) or reading `deployment.json` from triggers (a kernel fact would live
   outside the kernel).
9. **Function split**: only the two-row disposition ceremony gets a dedicated
   SECURITY DEFINER function; sent/received/belief ride the generic
   `kernel.ledger_write` (the s53 no-new-function precedent for single-row kinds).
   Alternative: dedicated `missive_send`/`missive_receive` functions — two more
   surfaces for no additional foreclosure.
10. **Named-slot dispositions** (§7): documented absences anchored to
    `missive_protocol`'s real CHECK and s41's real kind — columns-with-vacuous-
    constraints rejected under the named-consumer test. Alternative: vacuous v1
    columns (`missive_signature` etc.) — rejected, grounds in §7.
11. **Self-missives refused**; **acknowledgment receipts excluded from disposition**
    (no ack-of-ack regress) — both small closures with no consult text either way;
    each named in §2.3/§2.4 with grounds.
12. **The `authn` slot lives in `courier.toml`**, not on the row (a per-channel fact,
    one home) — row 1162's "wire protocol authn mode field" read as transport
    configuration, since the wire object IS the row shape and a per-row copy would
    violate P1 at birth. Alternative: an envelope column — rejected on the same
    ground as item 10.

---

*Fable, out of frame, 2026-07-23. Frozen pending maintainer ratification; the
orchestrator installs. The builder that executes this spec reports every §11 leg as
WITNESSED / REFUSED-AS-EXPECTED / UNEXERCISED-with-blocker, and re-verifies §1's
head-body table against the tree before authoring a line of SQL.*
