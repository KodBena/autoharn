<!-- doc-attest-exempt: consult deliverable, maintainer review pending. -->

# CONSULT — Cross-world communication as a kernel-and-boundary mechanism

**What this is.** An independent Fable consult (ADR-0018 posture: witnessed problem,
evidence, and law only — no commissioner designs received), commissioned 2026-07-23,
answering: how do this ecosystem's separately-governed worlds communicate first-class,
given that they have already invented file-based protocols for it twice
(`/home/bork/w/omega/docs/dispatch/` and the `DIRECTIVE_FROM_AUTOHARN.md` /
`AUTOHARN_BACKFLOW.md` pair), with witnessed failure modes: hand-carried delivery,
unledgered content, staleness within a day, no delivery/read semantics beyond
convention, and perspective-relative direction words that invert meaning by reader.

**What it proposes, in one paragraph.** A travelling record called a **missive**: a
typed, versioned envelope naming its two parties (author world, addressee world),
carrying its body verbatim, and citing its author-side ledger row by a
content-pinning token. Missives are ledger rows on both sides — a `missive_sent`
event in the author's ledger, a `missive_received` event in the addressee's — moved
by **receiver-pull over the existing boundary service** (each world's courier reads
the counterpart's served outbound view and writes the receipt through its *own*
world's s43 write boundary; no world ever writes into another world's ledger).
Lifecycle states are typed events replacing filename conventions; acknowledgment is
a missive travelling back; staleness is supersession made visible; and a foreign
claim enters local reasoning only as the belief substrate's `testimony`-basis
belief citing the receipt row — never as a local fact, never as a local obligation
without a local ratification act. The courier principal is kernel-scoped so that
"foreign content auto-becomes local obligation" is unrepresentable, not merely
forbidden.

Everything below is design, not built mechanism; kernel deltas named here are
proposals for a future lineage family entering a future world's birth chain
(runs-are-strictly-linear, 2026-07-11 — nothing here patches an existing world).

---

## 0. The evidence, as read

The two witnessed protocols were read before designing (per commission):

- **omega `docs/dispatch/`** — fifteen files. Names encode sender→receiver direction
  (`frontend-to-backend-…`, `proxy-to-frontend-…`), lifecycle
  (`…-shipped.md`, `…-consumed.md`, `…-status.md`, `…-clarifications.md`), and arcs
  (`…-arc1-…`, `…-arc2-…`). Bodies carry structured headers (Date / From / To /
  Type / Status), verbatim wire-shape contracts both sides declare binding,
  acknowledgment by counter-file, and — witnessed inside
  `proxy-to-frontend-learned-vf.md` itself — a "Status: Open" header that outlived
  both ships until a dated in-place edit corrected it, plus in-place revisions that
  left the document self-contradictory (the subject of the entire
  `frontend-to-proxy-learned-vf-clarifications.md` file).
- **`DIRECTIVE_FROM_AUTOHARN.md` / `AUTOHARN_BACKFLOW.md`** — a directive channel
  one way, a findings channel the other. Field-proven maintenance discipline
  (items removed when confirmed fixed upstream, each removal independently
  re-verified against source); explicit acknowledgment-of-read expectations ("that
  file is the contract negotiation channel, and it is read"); and documented pain:
  the upstream side cannot edit the file while downstream sessions run, content is
  invisible to either world's ledger, and the directive went stale against upstream
  refactors within a day.

The failure classes, stated generally: **(F1)** delivery is a human act with no
record; **(F2)** the content lives outside both append-only substrates, so the
audit story each world tells about itself has a hole exactly where the worlds
touch; **(F3)** a shared mutable file has no supersession — staleness is silent;
**(F4)** "delivered/read/consumed" are conventions a counter-file may or may not
witness; **(F5)** direction words (`backflow`, `inbound`, `From/To` in a filename)
are perspective-relative and invert by reader.

## 1. What the file protocols got RIGHT — preserved by design

These are field-proven and are carried into the mechanism, not reinvented:

1. **Acknowledgment as a first-class reciprocal act** (omega's `-consumed.md`
   counter-files; BACKFLOW's "it is read"). Preserved as a typed acknowledgment
   missive travelling back — the author's ledger ends up holding the addressee's
   receipt, bilaterally auditable.
2. **The maintenance discipline: the working set shrinks as items resolve**
   (BACKFLOW's remove-when-fixed rule). Preserved — but as a *derived view* over
   append-only rows (open threads = threads without a closing disposition), never
   as manual deletion. The ledger keeps history; the view keeps the working set
   small. The discipline stops being memory-dependent.
3. **Threading and arcs** (omega's `arc1`/`arc2`, clarification files answering a
   named dispatch). Preserved as thread identifiers plus explicit responds-to
   edges.
4. **Verbatim contracts, not paraphrase** ("The body of this document is binding";
   the standing commissions-verbatim rule). Preserved: a missive body travels
   byte-for-byte and is hash-pinned; the mechanism never summarizes in transit
   (§5 on ADR-0020).
5. **Statements of what changed and what is required, with pointers rather than
   duplicated content** (the DIRECTIVE's "where the information lives" section).
   Preserved as the token currency: a missive cites artifacts and rows by
   resolvable tokens instead of restating them (ADR-0012 P1 across worlds).
6. **The explicit "Type:" field** on omega dispatches (proposal / status /
   clarification / consumed). Preserved as a closed speech-act vocabulary (§3),
   per ADR-0008: distinct communicative acts are distinct kinds of thing, never
   fuzzy-matched into one.

## 2. Vocabulary and the naming discipline

**The travelling record is a `missive`.** The word is chosen against the obvious
candidate "dispatch" deliberately: `dispatch` already means work-dispatch in this
project (s55 `dispatch-grain-independence`, the delegation contract's dispatching
of agents), and overloading it would be an ADR-0008 fuzzy match. A missive is a
written message from a named party to a named party; nothing else in the corpus
uses the word.

**Named parties, never directions.** A missive names `author_world` and
`addressee_world` — role nouns bound to world names, stable under every reader.
The recorded maintainer observation governs: direction words (`inbound`,
`outbound`, `backflow`, `from/to` as filename position) belong only in
perspective-anchored records, and even there this design avoids them: a world's
own ledger rows also carry both party names explicitly, with the perspective
recoverable from the row's kind (`missive_sent` ⇒ author is the local world;
`missive_received` ⇒ addressee is the local world) rather than from a direction
word. A zero-context reader (ADR-0017) of either ledger can reconstruct who said
what to whom without knowing which world's ledger they are reading.

**World names are the party identifiers.** The boundary service's deployment
names (`/d/{deployment}/…`) are the existing one-home naming surface for worlds;
the missive layer reuses them rather than minting a second registry (P1). A
missive's party fields carry deployment names. The mapping from world name to
boundary base URL is transport configuration (§7), not part of the record.

**Cross-world references are tokens, never foreign keys.** A local ledger cannot
FK into a foreign ledger, and must not pretend to. The token currency extends the
existing `row:<id>` / `artifact:<64hex>` forms (s48/s51/s52) with a world-qualified,
content-pinned form:

```
xrow:<world>:<row_id>:<row_hash>
```

— the author world's name, the row id in that world's ledger, and that row's s26
hash-chain `row_hash`. The hash makes the citation tamper-evident and
version-exact: a token cites *one immutable historical row*, never "whatever that
row says now" (there is no "now" — rows are append-only). This is the mechanism's
answer to F3 at the reference layer: a stale citation is impossible because a
citation names a frozen thing; *supersession* of the cited thing is a separate,
visible event (§9).

## 3. The travelling record: what a missive IS

A missive is **typed and enveloped; not signed in v1** (the honest disposition of
each, below). The envelope is the JSON object that crosses the wire; its fields
are exactly the columns of the ledger rows on both sides (one shape, one home —
no separate wire codec to drift, P7):

| Field | Type | Meaning |
| --- | --- | --- |
| `missive_protocol` | int | Envelope version. v1 = 1. A receiver refuses (typed refusal, not silent coercion) a version it does not implement. |
| `missive_author_world` | text | Deployment name of the authoring world. |
| `missive_addressee_world` | text | Deployment name of the addressed world. |
| `missive_thread` | text | Thread id, minted by the thread's opening author as `<author_world>/<slug>` — globally unique because prefixed by the minting world, with no coordination (one home per name). |
| `missive_seq` | int | Author-local sequence within the thread: the Nth missive *this author* has contributed to this thread. `(author_world, thread, seq)` is the missive's global identity and the deduplication key. Ordering across the two authors is causal (via `responds_to`), never by a shared counter — two ledgers share no sequence. |
| `missive_act` | text | Closed speech-act vocabulary, §3.1. |
| `missive_responds_to` | text | Optional `xrow:` token naming the counterpart missive this one answers (the omega clarification/consumed pattern, typed). |
| `missive_provenance` | text | The `xrow:` token of the author-side `missive_sent` row. Filled by the author; it is how the addressee's record cites the authoritative original. |
| `statement` | text | The body, **verbatim**. For bodies beyond the ledger's statement bounds, the body is an artifact (`artifact:<64hex>`, s51 store) and the statement carries the token plus a one-line synopsis-free label ("body in artifact:…" — no paraphrase, so no ADR-0020 witness is owed for transport). |
| `missive_cites` | text | Optional comma-separated `xrow:`/`artifact:` tokens for referenced material (the DIRECTIVE's "where the information lives," typed). |

### 3.1 The speech-act vocabulary (closed, small)

Per ADR-0008, the acts are distinct because their lifecycle obligations differ —
this is not taxonomy for its own sake; each act's consumer is named (the
named-consumer test, ledger row 1906):

- **`assertion`** — the author states something it holds true (a finding, a
  contract shape, a capability description). Consumer: the addressee's
  belief-substrate entry (§5) and any local decision citing it.
- **`request`** — the author asks the addressee to do or answer something (the
  DIRECTIVE's requirements; BACKFLOW's asks). Carries no cross-world authority
  (§6). Consumer: the addressee's ratification decision (open thread until
  disposed).
- **`response`** — answers a `request` (must carry `responds_to`). Consumer: the
  requesting world's open-thread view, which it closes.
- **`acknowledgment`** — typed receipt/disposition notice (must carry
  `responds_to`). Consumer: the author's delivery audit (§8).
- **`withdrawal`** — the author retracts or supersedes an earlier missive of its
  own (must carry `responds_to` naming it). Consumer: the addressee's staleness
  view (§9).

Nothing else. An act that fits none of these is a vocabulary-revision question
(ADR-0008 positive register), not a closest-fit.

### 3.2 Typed? Enveloped? Signed? — dispositions

- **Typed: yes.** Every field above is a kernel column with kind-shape and value
  CHECKs in the house idiom (§4). A malformed missive is unrepresentable at
  construction in either ledger, and its attempt is a recorded refusal (s43, for
  free).
- **Enveloped: yes**, but the envelope is the row shape — there is no second
  serialization contract to drift from the first (P7's two-writers cancer,
  foreclosed by construction: the wire object's keys *are* ledger column names,
  exactly the `kernel.ledger_write(jsonb)` payload convention s43 already fixed).
- **Signed: no, in v1 — stated, not smuggled.** The standing crypto deferral
  governs the ceremony; s41's `principal_key_bound` is the empty slot if a future
  ratification wants missive signing, and nothing in this design forecloses it
  (the provenance token field is where a signature would ride). v1 authenticity
  rests on the transport's shape instead: under receiver-pull (§7), the addressee
  *fetched* the missive from the author's own boundary service — provenance is
  the fetch act, witnessed by the courier's own receipt row. That is honest for
  the current single-host, single-operator deployment; its ceiling is named in
  §11.

## 4. The kernel shape (both sides of the boundary)

A future lineage family (two deltas in the s40/s41 idiom; numbers assigned at
authoring time, not claimed here) adds, to every world that carries it:

### 4.1 Kinds

Three new members of the closed kind vocabulary:

- **`missive_sent`** — the author-side event: this world addressed this missive to
  that world. Actor: the authoring principal (a real local principal — the
  orchestrator, the maintainer's CLI identity — never a shared "comms" account;
  authorship is attributable). Consumer: the outbound serving view (§7), the
  author's own audit, and the addressee's provenance token.
- **`missive_received`** — the addressee-side event: these bytes arrived from that
  world. Actor: the local **courier** principal (§4.3). Consumer: the local
  orchestrator via `./pickup` (undisposed missives are surfaced), and the belief
  substrate as the one sanctioned `belief_source` for cross-world testimony (§5).
- **`missive_disposed`** — the addressee-side lifecycle event closing a received
  missive: `regards` the receipt row; disposition in a closed vocabulary
  (§8). Actor: a local *deciding* principal — deliberately NOT the courier (§4.3
  makes this structural). Consumer: the open-missives view it removes the item
  from, and the acknowledgment missive that carries the disposition back.

### 4.2 Columns

The envelope fields of §3 as `missive_`-prefixed nullable no-DEFAULT columns with
two-way kind-shape CHECKs (mandatory on the missive kinds, forbidden elsewhere —
the s40/s53 idiom), value CHECKs for the closed vocabularies, and coupling CHECKs
(`responds_to` mandatory on response/acknowledgment/withdrawal acts, in the s53
coupling-CHECK spelling). All appended to `compute_row_hash` and the two
column-complete views per s42's law. Refusal triggers in the single-purpose
`validate_*` family:

- **`validate_missive_identity`** — on `missive_sent`: author_world must equal
  the local world's name; on `missive_received`: addressee_world must equal it
  (the local world name is a birth-time kernel setting the scaffold writes — one
  home). A world cannot record itself sending another world's missive, or
  receiving one not addressed to it.
- **`validate_missive_dedup`** — on `missive_received`: refuse a second receipt
  of the same `(author_world, thread, seq)`. This converts the transport's
  at-least-once delivery into exactly-once *recording*, and the duplicate attempt
  is itself a journaled `write_refused` row (s43) — re-delivery is visible, not
  silent.
- **`validate_missive_tokens`** — `xrow:` tokens are shape-checked (world name
  syntax, digits, 64-hex); local `row:`/`artifact:` tokens are existence-checked
  (the s48/s52 mechanism verbatim). An `xrow:` token's *existence* in the foreign
  ledger is deliberately NOT checked at write time — the kernel of one world
  never reaches into another's (isolation is founding); cross-ledger token
  verification is a read-time/audit act over the boundary (§10), named as the
  weaker surface it is.
- **`validate_missive_courier_scope`** — see §4.3.

### 4.3 The courier principal (the authority boundary made structural)

Each world's birth registers a **`courier`** principal (agent_class `tool`, the
`write-boundary` precedent, purpose text fixed by the spec). The courier is the
identity under which arrivals are recorded, and it is *scope-limited in the
kernel*: `validate_missive_courier_scope` refuses any ledger write whose resolved
actor is the courier and whose kind is not in
`{missive_received, missive_disposed?}` — recommendation: **`missive_received`
only**, with dispositions reserved to deciding principals (Q3 adjudicates).

This is the load-bearing type of the whole design (ADR-0000 Rule 2(a)): the
defect class is *a foreign world's content binding local obligations without a
local decision*. The foreclosing type is not a policy telling agents to be
careful; it is a principal that physically cannot write `work_opened`,
`decision`, `commission`, `obligation`, or any other authority-bearing kind. The
only path from "missive arrived" to "local work exists" runs through a local,
non-courier principal writing local rows that cite the receipt — a ratification
act, attributable, countersignable, and gated by everything the kernel already
gates.

## 5. Epistemics of foreign claims — the belief substrate, judged honestly

The commission asks for an honest judgment of whether s53/s54 is purpose-built
for this. The answer is: **yes for claims, with one crediting caveat to
adjudicate; no for requests — and the distinction matters.**

**Where it fits exactly.** A claim arriving from another world is epistemically
testimony, and s53 already types testimony: a local principal who wants to reason
from the foreign claim writes `kind='belief'`, `belief_basis='testimony'`,
`belief_source = <the missive_received row>`. Every property wanted here is
already enforced or derived:

- The receipt row is the *only* honest `belief_source` for cross-world testimony,
  and it is a local, in-force, courier-attributed fact — "these bytes arrived
  from A" is locally witnessable; the claim's *truth* is not asserted by receipt.
  The two facts (arrival; content-is-true) have separate homes and separate
  kinds, exactly ADR-0008's edge between distinct facts.
- s54's evidence-class precedence (`observed > derived > testimony > assumed`)
  means a foreign claim, even credited, is *defeated by any contesting local
  observation* — the epistemics of "another world said so" are subordinated to
  local evidence by the already-ratified calculus, with no new mechanism.
- Contest/concur, holder-only revision, and the SoD rules compose unchanged: two
  local principals may disagree about a foreign claim in visible doubt.
- s54's `shared_premise` makes "these two beliefs both bottom out in the same
  foreign missive" a query — independence audits see through the boundary.

**The crediting caveat (surfaced, not absorbed).** Under s54's `credited_beliefs`,
a testimony belief is well-founded iff its source is grounded, and *any* in-force,
non-defeated non-belief row is grounded — including a missive receipt. So a
testimony belief citing a receipt row is **credited immediately**, at testimony
rank, with zero local corroboration. That is arguably the designed behavior
(testimony is credited-but-lowest, and `corroboration` reports its diversity
grade without gating), but it means a foreign world's bare assertion enters the
local credit surface the moment one local principal relays it. Whether cross-world
testimony should instead sit uncredited until corroborated or locally verified is
a genuine policy fork this consult does not own — Q5 below.

**Where it does not fit — requests.** A `request` missive is not a proposition
and must not be shoehorned into a belief (ADR-0008: a directive fuzzy-matched
into an assertion would classify an ask as a truth-claim). Requests live entirely
in the missive lifecycle: received → disposed (accepted/declined/escalated), with
acceptance expressed as ordinary local work/decision rows citing the receipt.
The belief substrate is the epistemics of foreign *claims*; the missive lifecycle
is the pragmatics of foreign *asks*. Two vocabularies, two homes.

**ADR-0020, applied.** Transport is designed to be witness-free by never
transforming: the body crosses verbatim, hash-pinned end to end (`row_hash` in
the provenance token; `artifact:` content addressing for large bodies). The
moment any local principal *summarizes, extracts, or re-renders* foreign content
— a synopsis in a decision row, a "what upstream requires" digest — that is a
transformation in ADR-0020's scope and owes the cold-read meaning-preservation
witness. The mechanism cannot check semantic fidelity of paraphrases; it can and
does make the verbatim original always one token away, so every witness has its
source at hand. Stated per ADR-0011 Rule 1: transport fidelity is mechanical;
paraphrase fidelity is the ADR-0020 witness, review-grade.

## 6. The authority boundary (the binding constraint, discharged)

The maintainer's constraint: authority never crosses world boundaries; a foreign
world's records cannot bind local obligations without local ratification. The
design discharges it at four layers, strongest first:

1. **Privilege:** no world holds any credential in another world's database or
   write boundary. Under receiver-pull (§7), world B's courier only ever *reads*
   A's boundary and *writes B's own*. There is no cross-world write path to
   misuse.
2. **Type:** the courier's kind-allowlist (§4.3) makes arrival-recording the only
   thing arrival can do. No missive content, however imperative its prose, can
   become a local work item, decision, or obligation except through a non-courier
   local principal's own attributable write.
3. **Vocabulary:** `request` is the strongest act the envelope can carry. There
   is no `directive` act and no `obligation` act in the travelling vocabulary —
   deliberately unrepresentable, so the DIRECTIVE file's *primus inter pares*
   letter becomes, in this mechanism, a `request` thread whose binding force is
   whatever the receiving world's own ratification gives it. (The real-world
   authority relation — the maintainer directing both worlds — is carried by the
   maintainer ratifying on both sides, where it always actually lived.)
4. **Record:** the ratification act itself is ordinary ledgered work, so "who
   accepted this foreign ask, when, on what grounds" is a query, not an
   archaeology.

## 7. Delivery over the existing transport

**Transport = receiver-pull over the boundary multiplexer.** The boundary service
already serves every world at `/d/{deployment}/…` from one process. Two additions:

- **A served view, `missive_outbound`** (author-side, security_invoker, the s54
  view discipline): in-force `missive_sent` rows, filterable by
  `addressee_world`, minus those for which a matching `acknowledgment` receipt
  exists locally. Served through the existing `GET /d/{d}/views/{view}` route —
  zero new route machinery.
- **The courier verb** (a repo-root-standard scripted verb, per the
  self-application rule — never prose steps): for each configured counterpart,
  read `GET /d/<counterpart>/views/missive_outbound?addressee=<self>`, and for
  each new missive write `missive_received` through the *local* world's
  `POST /d/<self>/write/ledger` (the s43 boundary; the courier's actor). Then
  author the `acknowledgment` missive per §8. Idempotent by construction: the
  dedup trigger refuses re-receipt, and the refusal verdict is the courier's
  signal to advance.

**Delivery semantics, defined (F1/F4 closed):** *delivered* ≙ the
`missive_received` row exists in the addressee's ledger; *acknowledged* ≙ the
author's ledger holds the receipt of the addressee's `acknowledgment` missive;
*consumed/declined* ≙ the disposition carried by that acknowledgment. Every state
is a hash-chained row in the ledger of the world whose act it records; delivery
stops being a claim and becomes a bilateral, independently auditable pair of
records. At-least-once transport + refuse-duplicate recording = exactly-once
semantics, with the duplicate attempts themselves journaled (s43) rather than
silently dropped.

**Polling, honestly.** Pull has no push latency guarantees; a world learns of a
missive when its courier next runs. Recommended integration: `./pickup` runs (or
reports the staleness of) the courier pass, so hydration and mail collection are
one habit. The ceiling — a world that never polls never learns — is mechanism-
irreducible and named in §11. (An SSE/watermark push surface is already filed as
a boundary gap by the panel world; if it lands, the courier gains a trigger, but
pull remains the correctness story.)

**What multi-host later adds (named, not designed):** today both worlds' boundary
services are reachable on one host, and world-name → base-URL is a small config
map for the courier. Multi-host changes only that map's values plus transport
authenticity/confidentiality (TLS, allowlists) — a perimeter concern that is
explicitly not designed here. Nothing in the record shapes, lifecycle, or
epistemics changes with the transport, which is the point of separating the
serialization contract from the transport mechanism (P7).

## 8. Lifecycle and threading (typed events replacing filenames)

The omega filename lifecycle maps one-to-one onto typed events:

| File convention (witnessed) | Typed replacement | Whose ledger |
| --- | --- | --- |
| authoring the dispatch file | `missive_sent` | author |
| (hand-carry; no record) | courier pull + `missive_received` | addressee |
| `…-consumed.md` counter-file | `missive_disposed` (regards the receipt) + `acknowledgment` missive back | addressee, then author receives it |
| `…-status.md` in-place edits | further `assertion`/`response` missives in the thread | either |
| `…-clarifications.md` | `request` missive with `responds_to` | either |
| BACKFLOW item removal on fix | disposition closing the thread; open set is a view | addressee |

**Disposition vocabulary** (closed; on `missive_disposed`):
`consumed` (read and acted on / accepted), `declined` (read and refused, grounds
in the row), `superseded-unread` (a `withdrawal` or same-thread successor arrived
before disposition — the staleness case, §9), `escalated` (routed to the
maintainer's decision queue). Each disposition's consumer: the author world's
open-thread audit, via the acknowledgment.

**Threading:** `missive_thread` groups; `missive_responds_to` gives the causal
edge (typed, cross-world, hash-pinned). Arcs are threads. A thread is *open* for
a world while it holds an undisposed receipt in it, or an unacknowledged sent
missive; "open threads" is a derived view on each side, and — preserving the
BACKFLOW discipline — it is the *working set* an orchestrator reads, while the
full history stays queryable beneath it. No total order across the two authors is
minted (two ledgers share no clock or counter); causal order via `responds_to` is
the honest orderable structure, stated rather than papered over.

## 9. Staleness and supersession (F3 closed)

Two distinct staleness problems, two mechanisms:

1. **The travelling record goes stale upstream** (the DIRECTIVE's witnessed
   within-a-day case). An author revising its position writes a new missive in
   the thread — either a successor (`assertion`/`request` with `responds_to`
   naming its own earlier missive) or an explicit `withdrawal`. Kernel-side, the
   author's own `missive_sent` row is revised only by its holder via s31
   supersession, and a CLI/spec rule couples that supersession to authoring the
   withdrawal missive (recommendation: trigger-enforced — superseding a
   `missive_sent` row is refused unless the superseding row is itself the
   successor missive in the same thread; the s45/s53 same-kind supersession
   discipline, one more branch). The addressee's staleness view then shows: any
   undisposed receipt whose thread holds a later-received withdrawal/successor —
   surfaced by `./pickup` before an agent acts on the stale one. The receiving
   world *knows* a received directive was superseded upstream the same way it
   knows anything: a typed row arrived saying so, and the view composes the two.
2. **The citation cannot go stale, by construction.** `xrow:` tokens pin content
   by hash (§2); there is no shared mutable file to drift. What the file
   protocols experienced as silent staleness becomes, here, either a visible
   withdrawal event or nothing at all — the author's silence is itself honest
   (the record it sent stands as its last word, timestamped).

What this does NOT solve: an author world that changes course and *never sends
the withdrawal*. No mechanism in the addressee can detect an event the author
never recorded. The mitigation is authorial discipline plus the audit query "sent
missives whose cited local rows have since been superseded" (a cheap author-side
view flagging candidate withdrawals — recommended, advisory). Named ceiling, §11.

## 10. Read surface, integration, and audit

- **Views** (per-world, the s54 display-surface discipline; the engine/ASP layer
  may later mirror them, not designed here): `missive_open_threads`,
  `missive_undisposed` (receipts awaiting disposition — the pickup surface),
  `missive_stale` (§9), `missive_outbound` (§7, also the served one),
  `missive_delivery_audit` (sent missives with/without acknowledged receipts —
  the author-side delivery ledger). Every view names its consumer above; a view
  without one was not proposed (row 1906).
- **`./pickup`** surfaces `missive_undisposed` and `missive_stale` counts — mail
  is part of hydration, so the resumption doctrine covers cross-world state
  without context replay.
- **Cross-ledger audit:** because both sides are hash-chained rows citing each
  other by `(id, row_hash)` tokens, an auditor with read access to both
  boundaries can mechanically verify the bilateral record: every receipt's
  provenance token resolves to a real author-side row with a matching hash, and
  every acknowledged send has its addressee-side counterpart. Recommended as an
  `audit` verb leg, advisory-grade, run on demand — not a per-write check (write
  paths never reach into foreign ledgers, §4.2).
- **Retirement of the file protocols:** once the first live missive exchange is
  witnessed end-to-end, `DIRECTIVE_FROM_AUTOHARN.md` / `AUTOHARN_BACKFLOW.md`
  freeze (point-in-time records; ADR-0005 Rule 8) and new traffic goes through
  the mechanism; a ritual channel kept alive beside a working typed one is
  exactly what the named-consumer test deletes. Timing is Q6.

## 11. Honest ceilings (what mechanism cannot reach)

1. **Poll liveness.** Pull transport cannot make a world read its mail; an
   unrun courier is an unread mailbox. Mitigated by pickup integration; not
   closed.
2. **The unsent withdrawal.** An author that changes course silently leaves the
   addressee holding an honest record of a stale position (§9). Advisory
   author-side flagging only.
3. **Paraphrase fidelity.** The mechanism guarantees the verbatim original is
   always resolvable; it cannot check that a local summary of it preserved
   meaning. That is ADR-0020's witness, review-grade, owed by whoever
   transforms.
4. **Out-of-band channels.** Nothing stops two worlds' agents from inventing a
   third file protocol tomorrow. The mechanism competes by being cheaper than a
   file (one verb, one row) and by pickup surfacing what files never could;
   constitutional prohibition of ad-hoc files is possible but not proposed here
   (it would be prose, not type — the wrong surface).
5. **Transport authenticity under multi-host.** v1's fetch-is-provenance argument
   holds for the current single-host deployment; a hostile network invalidates
   it. The upgrade slot (signing via s41 key bindings; TLS at the boundary) is
   named and empty, per the standing crypto posture.
6. **Semantic authority.** The kernel can make foreign asks non-binding; it
   cannot make a local ratifier *judicious* about accepting them. Ratification
   quality is governance, carried by the existing decision/countersign machinery.

## 12. Closure statement (ADR-0000 Rule 2(a), 2026-07-02 form)

Claimed class, in its most general form: *cross-world communication whose
delivery, content, lifecycle, or provenance is unrecorded in the communicating
worlds' own audit substrates, or whose meaning depends on the reader's
perspective.*

- **Invariant:** in worlds carrying this family and communicating through it,
  every cross-world communicative act is a typed, hash-chained, attributed ledger
  row in the acting world's own ledger; every travelling record names both
  parties by stable world names and pins its provenance by content hash; every
  lifecycle transition (sent, received, disposed, acknowledged, withdrawn) is a
  typed event; a duplicate delivery, a malformed envelope, an unauthorized
  courier write, and a foreign-content write of any authority-bearing kind are
  each refused at construction with the refusal itself recorded (s43); and no
  world holds write access of any form into another world's substrate.
- **Quantification universe:** communicative acts — the five-act vocabulary of
  §3.1, closed (a sixth act is a vocabulary revision, not a fit); lifecycle
  states — the omega filename states and the BACKFLOW disciplines, each mapped in
  §8's table; parties — worlds named in the boundary config (worlds outside it
  are unreachable by construction); reference forms — `row:`, `artifact:`,
  `xrow:` (no fourth form); write surfaces — the s43 boundary only (raw-owner
  DML remains the standing s26+ trust bound, named); **deliberately not
  covered:** communication outside the mechanism (ceiling 4), foreign-token
  existence at write time (§4.2, audit-grade instead), poll liveness (ceiling 1),
  the unsent withdrawal (ceiling 2), paraphrase fidelity (ceiling 3), transport
  authenticity beyond the current single-host shape (ceiling 5), and the
  engine/ASP mirror of the missive views (future work, not smuggled).
- **Denomination:** identity in `(author_world, thread, seq)` — world names from
  the one existing registry, never a second naming home; content in bytes pinned
  by SHA-256 row-hash/artifact-hash, never a summary or a mtime; delivery in row
  existence in the addressee's ledger, never in a transport's return code;
  staleness in typed withdrawal/successor events, never in wall-clock age. No
  bound or key in this design is a bare round literal.

## 13. Open questions for the maintainer (each a ratifiable choice)

1. **Transport: receiver-pull via existing boundary reads (recommended) vs a
   dedicated relay service.** Pull reuses served views and keeps zero cross-world
   credentials; cost: polling latency and a courier that must be run (per-world
   config of counterpart URLs). A relay centralizes scheduling but mints a new
   trusted component holding read access to every world.
2. **Ratification routing for the kernel family.** Additive kinds + refusals in
   shape, but it mints ecosystem-wide vocabulary — recommend the s53 precedent:
   full Fable-spec + maintainer ratification, not the class-ratified fail-safe
   lane. Cost: your ratification bandwidth on one more family.
3. **Courier scope: `missive_received` only (recommended) vs also
   `missive_disposed`.** Narrow scope forces every disposition to a deciding
   principal — cleanest authority story; cost: even trivial `superseded-unread`
   housekeeping needs a non-courier actor, slightly more friction per stale item.
4. **May a received `request` ever auto-open local work?** Recommend: never — 
   local ratification always, even for the maintainer's own cross-world
   directives (he ratifies on the receiving side, preserving one rule with no
   exception ceremony). Cost: one extra local act of latency on every
   cross-world ask, including his own.
5. **Crediting of cross-world testimony (the §5 caveat).** Recommend: keep s54
   as ratified (testimony credited at testimony rank immediately; corroboration
   reported, gating nothing) and revisit only on a witnessed overclaim incident.
   Cost: a foreign world's bare assertion, once relayed by one local principal,
   stands credited (lowest rank) with zero corroboration. The alternative — an
   uncredited-until-corroborated rule for beliefs whose source is a missive
   receipt — is a one-branch change to `credited_beliefs`, but it makes
   cross-world testimony weaker than same-world testimony by fiat, which the
   ratified spec did not distinguish.
6. **File-protocol retirement timing.** Recommend: run the mechanism parallel to
   DIRECTIVE/BACKFLOW until one full thread (request → response → disposition →
   acknowledgment) is witnessed live end-to-end, then freeze the files and route
   all new traffic through missives. Cost: a bounded dual-channel window in which
   the two can disagree; the witnessed-exchange gate bounds it.
7. **Enforced withdrawal coupling (§9): trigger-refused supersession of
   `missive_sent` outside a same-thread successor (recommended) vs CLI-side
   convention.** Trigger cost: one more branch in the supersession validator and
   one more thing to scratch-witness; convention cost: the staleness class this
   whole design exists to close stays open at its author-side root.

— Fable consult, 2026-07-23. Independent per ADR-0018; the commissioners' own
candidate designs, if any, were not seen and should be weighed against this as a
second derivation, not merged into it silently.
