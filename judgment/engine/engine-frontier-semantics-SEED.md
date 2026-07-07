# Engine cross-stream ordering / frontier semantics — SEED (the acts_live dissolution, worked)

**Status: SEED, for maintainer review and as the design input to INC 5's soundness memo
(D22).** This is the elevate-only-on-Fable item the engine SEED and the post-Fable brief
both reserve ("cross-stream frontier semantics (the acts_live dissolution)"). It settles
the design; the spike (INC 5) settles the evidence; the maintainer settles adoption
(D13's lift is a ratification, never an inference from this document). Produced under
ruling 110 (INC 0 ratified): D6, D13, D22 are binding law here — this document extends
them and contradicts none.

**MODEL-SERVED (self-report):** claude-fable-5 — per this session's own system context
("You are powered by the model named Fable 5. The exact model ID is claude-fable-5").
Per the provenance-honesty rule I have no introspective channel that could detect a
silent substitution; no degradation event was observed this invocation. One prior turn
of this same session ended on a server error mid-task; this resumed turn self-reports
the same model id. The caveat binds identically either way.

**Record basis (read in full this invocation):** `consults/engine-design-SEED.md`;
`consults/engine-panel/refute-semantics.md` (flaw 3 and salvage);
`consults/engine-panel/critic-completeness.md` (§2 bullet 5, §3);
`consults/engine-increment-0-unification.md`;
`claude_harness/experiments/fact-mining/docs/LEDGER-LOGIC-MARRIAGE.md` (body + Appendix A);
the BRIEF's §3 register (G5 row and trigger-class preamble); consult 17 §5.3's ordering
correction; `harness/e13-build/s13-schema.sql` (id + edge-trigger mechanics);
`harness/e17-build/s17-stamp-mechanism.sql` + `stamp_intercept.py` (the stamp anchor);
`POST-FABLE-OPERATING-BRIEF.md` (owner partition; engine sections). Verified read-only
against `acts.ruling` at authoring time: rulings **42** (deny-surface protocol), **43**
(secret retention), **110** (INC 0 ratification, D1–D22, INC 1 commission) — all
`binding`. Verified live: the `acts` schema (`acts.stream`, `acts.act` with per-table
identity ids, `(stream_id, id)` index, append-only triggers; **one imported stream, 735
acts** — the historical acts substrate is otherwise still in persisted transcripts, not
in Postgres). No `acts.ruling` row files the id-is-order law itself; its ratification
depth is FIND/consult (consult 17 §5.3, marriage §3 rule 2 + A.3, semantics §3.2) and it
is cited at that depth per D15/D16 — a census row, not a RULING citation.

**Plain-language summary for the maintainer.** Today we cannot say, from the record
alone, whether an approval written into the ledger came before or after the file edit it
was supposed to license, because the ledger and the action log are two separate numbered
lists and the wall clock is banned as an ordering source (with cause: same-second
entries exist). The fix: give both lists their numbers from ONE counter, so any two
events — a ledger write and a tool action — carry directly comparable numbers by
construction. That works fully only from adoption day forward. For everything already
recorded, the honest offer is weaker: we can often *bracket* a ledger row between the
action that wrote it and that action's result, and order through those brackets; where
the brackets don't decide a pair, the engine must say "undecided" rather than guess.

---

## 0. Verdict up front

**The critic's dissolution is sound — with a scope line that must be stated to keep it
sound.** One shared id sequence across the subject-writable ledger and an apparatus-owned
live acts journal yields a total, id-derived cross-stream order **by construction, from
adoption forward**, satisfying both ratified ordering laws (id is the order; ts never
orders the record) instead of bending either. It is *not* retroactive: no mechanism can
mint a shared sequence for records already written. For the historical corpus the
derivable object is a **partial order built from witnessed anchors** (§4), and where that
partial order is silent the sound verdict is ORDER-UNDECIDED — a first-class outcome,
never a ts fallback. The two halves are one design: the anchored partial order is also
the permanent degraded mode whenever the live journal has a coverage gap, so the forward
mechanism and the backward semantics reconcile at close instead of diverging.

## 1. The problem, precisely

G5 (BRIEF §3.1): a change to a safety-relevant artifact requires "approver identity +
timestamp predating implementation" — the load-bearing obligation of IEC 62304/820.30(i)/
SOX. Deriving its discharge status means ordering a **ledger row** (the approval) against
an **acts-stream event** (the implementation). Refute-semantics flaw 3 proved this
underivable under the design's own axioms: ids are per-stream (`s13.ledger.id` is a
`bigserial`; `acts.act.id` is a per-table identity — disjoint counters with no shared
meaning), and ts-ordering is banned with cause (consult 17 §5.3: 41 ms and same-second
neighbours in s12; marriage A.3). The seed therefore marked G5-class ordering BLOCKED;
D13 confines every ledger-vs-acts judgment (Family F, and Family B gap-detection) to
close-time until this question is ratified. Critic §2 bullet 5 named the candidate:
`acts_live` in the same Postgres could share **one id sequence** with the ledger.

## 2. The mechanism: one order domain, allocated at the table default

### 2.1 What exactly shares the sequence

One apparatus-owned sequence, `kernel.event_seq` (per lineage), with exactly two member
stream classes:

1. **The subject-writable ledger table(s) of the live lineage** — the next lineage's DDL
   declares `id bigint PRIMARY KEY DEFAULT nextval('kernel.event_seq')` in place of
   `bigserial`. Closed historical schemas are never retrofitted (read-only forever,
   marriage §8).
2. **`acts.act_live`** — a NEW apparatus-owned table (the existing `acts.act` stays
   untouched as the retrospective import target; the two are compared by acts_parity,
   never merged). Same column shape as `acts.act` minus import-specific fields, plus the
   invocation identity the hook already knows (`agent_id`, session id — the stamp's own
   binding tuple). Append-only triggers as on `acts.act`; **no subject grants** (the
   D12 posture: apparatus-owned, not a prime surface by read access).

**Deliberately excluded from the domain, with reasons:** the judgment store, the refusal
journal, engine caches — their allocation volume reflects *apparatus* activity, and since
the subject can read its own ledger ids, shared allocation would leak engine-scrutiny
volume into subject-visible id gaps: an e12-class **passive prime**. Excluded by
membership, not by review. `acts.ruling` is likewise out at spike stage (rare maintainer
acts; a mid-run gap would announce "a ruling just happened"); ordering rulings against a
run stays anchor-based (§4) pending a separate maintainer decision (§9).

**Builder trap, stated:** Postgres `GENERATED ALWAYS AS IDENTITY` columns own their
sequence and cannot share one — membership requires the `DEFAULT nextval(...)` form.
The sequence is created `CACHE 1 NO CYCLE` and a config parity check pins both settings
(a cached sequence hands out per-connection blocks and allocation order stops being
real-time order — the whole soundness claim rests on this pin).

### 2.2 The write paths

- **Ledger rows:** unchanged for the subject. The id arrives from the table default at
  INSERT — **the ordering mechanism does not depend on the interception hook at all for
  ledger writes.** A script-mediated INSERT that bypasses psql interception is unstamped
  (the standing e17 tripwire) but still correctly ordered. This is the design's key
  robustness property: hook death degrades *witnessing*, never ledger *ordering*.
- **Acts:** the interception hook journals into `acts.act_live` on its own connection,
  autocommit: the **request act at PreToolUse** (before the tool executes) and the
  **result act at PostToolUse**. Same SAFETY discipline as `stamp_intercept.py`: any
  journaling error → allow the tool unchanged (degrade-not-block); a missed act is a
  close-time parity finding, never a blocked tool.

Because PreToolUse is synchronous and the journal write is autocommit-before-tool-start,
every hook-observed ledger write acquires the **bracket invariant by construction**:
`id(request act) < id(ledger row) < id(result act)`. The spike checks it whole-run (§7).

### 2.3 What Postgres actually gives, and what the order claim rests on

`nextval` is atomic, non-transactional, and never rolled back. With CACHE 1, the sequence
of allocations is a **true real-time total order of the allocation events** across all
connections. It is NOT commit order and NOT visibility order: a transaction can allocate
id 100, and a second can allocate 101 and commit first. The design's claims are therefore
phrased on allocation order, with two supports and one declared residual:

- **Support 1 — the deontic event and its allocation coincide.** A ledger row's id is
  allocated during the INSERT statement — i.e. *during the act of asserting*. An act's
  request id is allocated at PreToolUse — *before the tool's effect*. So allocation
  order is a faithful witness of issuance order for exactly the two event classes the
  domain contains.
- **Support 2 — direction-of-error analysis (F10 shape).** For G5:
  `id(approval) < id(implementation request)` ⟹ the approval's assertion began before
  the implementation was even requested, which precedes its effect — the DISCHARGED
  direction is conservative. The VIOLATED direction (`id(act) < id(approval)`) can
  include approvals landing mid-implementation — which ARE violations per the BRIEF's
  "before it is applied". Errors fall on the flag-more side, never the license-more side.
- **Declared residual — allocation-to-commit window.** An approval allocated before but
  committed after the implementation began is orderable as DISCHARGED while not yet
  durable at implementation time. Within one session, serial tool execution closes the
  window (the psql call returned before the next tool fired ⟹ committed). Across
  concurrent sessions it is a real residual, ACTIVE-adversary shaped (holding a ledger
  write open in a multi-statement transaction), out of the standing threat-model scope —
  **pre-registered in the JudgmentSpec `assumptions[]`** ("short autocommit ledger
  writes"; invalidating condition: any observed multi-statement transaction spanning a
  ledger insert), declared on the conformance sheet, and tripwired (§5 prefix-stability,
  plus the ts-skew tripwire below), never silently absorbed.

**The ratified laws are upgraded, not repealed.** "Id is the order within a stream"
becomes the projection of "id is the order within a *domain*"; every within-stream
consequence survives verbatim. The ts ban stands untouched: ts's one sanctioned role
(comparison against an external clock) is used here only as a **tripwire** — an id-order
vs ts-order inversion beyond a declared skew bound QUARANTINEs (evidence of a broken
assumption, e.g. sequence misconfiguration), and never re-orders anything. The
same-second class that banned ts is exactly what the shared sequence decides soundly.

### 2.4 Failure semantics when the hook is bypassed (tripwire, not authentication)

Three bypass shapes, each with its detector:

- **(a) Unstamped ledger write** (script evasion, non-psql): ordered correctly anyway
  (§2.2); missing stamp is the existing e17 disposition tripwire; its G5 role is a
  degraded witness grade (§3), not a lost order.
- **(b) A single unjournaled act** (hook error, uninstrumented tool): no live id; the
  close-time transcript parse restores the act, acts_parity flags the miss, and the act's
  order is recovered at **bracket grade** between its journaled neighbours — the §4
  machinery doubling as degraded mode.
- **(c) A dead-hook window:** a coverage gap in `act_live`; the transcript reconciliation
  bounds it; cross-stream judgments whose frontiers fall inside the window are
  QUARANTINED at close (they read a prefix the record later contradicted).

### 2.5 D17 upgraded: the domain census

D17's second witness (consumed-id gap ↔ journaled refusal) becomes **total id-space
accounting**: at close, every allocated id ≤ the domain frontier must appear in exactly
one of {ledger, act_live, refusal journal}; anything else is UNACCOUNTED → QUARANTINED.
This *strengthens* ruling 110 §2: most ledger id gaps become mechanically resolvable
(they are acts allocations, looked up, done), shrinking the "innocent gap" adjudication
class the ruling pre-registered as a cost. The census is a generated close line under
D5's one aggregation authority.

### 2.6 The new prime surface, pre-registered

Post-adoption, subject-visible ledger id gaps encode counts of the subject's *own*
journaled acts — self-information, the lowest-grade prime there is, but a channel where
none existed. Recorded here per the e12 discipline, carried into the spike memo as a
reviewed item, and added to OQ13's union prime-surface audit (§9). Membership exclusions
in §2.1 are what keep it self-information only.

## 3. The derivable order-claim, typed

The engine's cross-stream order relation is three-valued with a declared **basis**:

- **ORDER-TOTAL** — both ids in one domain (§5's comparability predicate): `<` decides.
- **ORDER-ANCHORED(grade)** — decided by the transitive closure of: within-stream id
  orders ∪ witnessed anchor constraints (§4). Grades: **w1** stamp-witnessed (e17+:
  the row's stamp tuple matches the invocation whose request/result acts bracket it),
  **w2** echo-witnessed (the result act's payload contains the returned row id —
  exact-match predicate, never fuzzy), **w3** delegation-bracketed (a child stream's
  whole interval sits inside the parent's `delegation_spawn`/`delegation_return` pair —
  orders across concurrent subagent streams, which vendor per-stream order alone never
  can).
- **ORDER-UNDECIDED(interval)** — the partial order does not decide the pair; the honest
  residual verdict, carrying the bracketing interval where one exists. This is a DERIVED
  verdict (the derivation ran and honestly reports undecidability), never NOT-RUN.

An anchor is admissible only if **witnessed** — a mechanical predicate over record
content, never a plausibility match. The basis rides in the DerivationRecord (provenance,
per D8: not identity-bearing).

**Proposed Family E members for the G5 class** (proposal for the registry to mint under
INC content work, not minted here): `DISCHARGED-ORDERED(approval, first_impl_act)`,
`VIOLATED-ORDERED(act)` — a routed flag per F28, `ORDER-UNDECIDED(interval)`, plus the
D4 generator-injected `E_NOT_RUN(cause)`. Multi-act implementations key on the **minimum
constituent act id** (approval must precede the implementation's *start* — the
conservative direction; a mid-implementation approval is VIOLATED, matching the BRIEF's
"before it is applied"). The BRIEF field's letter ("timestamp predating") is satisfied in
spirit and letter: the ts is recorded content on the entry as G5 requires; the
*verification* of "predating" is id-derived, with ts as tripwire corroboration only.

**Scope line:** this seed delivers the ORDER relation. The **pairing** problem — which
acts constitute "the implementation" of which change request, across `target` matching
and sessions — is separate owned work (§9); G5 derivation composes pairing × order.
Cross-session pairing is OQ1's representation problem and stays there.

## 4. The historical corpus, honestly: epochs, not pretense

No shared sequence exists backward; the record divides into declared **order epochs**
(the law-epoch shape, OQ2), carried per-target in the capability manifest (the A.2
idiom — a caller requesting an unavailable order basis is refused loudly, never handed a
silent guess):

- **E0 — no persisted acts substrate.** Ledger-internal order only. G5-class cross-stream
  claims: **declared exclusion** (Family H row with reason), unless the maintainer's OQ2
  retroactivity ruling says otherwise.
- **E1 — persisted transcripts, pre-stamp (pre-e17).** Anchors at w2/w3 only. Bracket
  partial order derivable after import.
- **E2 — stamped records (e17+).** w1 anchors: the stamp binds row↔invocation; the
  invocation's acts bracket the row. The strongest pre-adoption grade.
- **E3 — post-adoption.** ORDER-TOTAL within the domain; anchored grades persist as the
  degraded mode (§2.4) and as the differential check on the overlap (§7).

Two honesty items that must not be papered over: (i) **the import backlog is real** —
`acts.act` holds ONE imported stream today (735 acts); every E1/E2 bracket claim waits on
transcript import for that record, which is owned work (§9), and the critic's I1 window
(acts resting on unchecksummed volatile files until snapshot) applies to everything not
yet imported; (ii) **decidedness is an empirical number** — what fraction of banked G5
pairs the anchored order actually decides is measured by the spike on real records, not
asserted here (N=1 apparatus posture: findings are design lessons, not samples).

Cross-session historical ordering: two sessions' acts streams order against each other
only through anchors into a common third stream (a shared lineage ledger, or w3
delegation brackets). Where no common stream exists, cross-session pairs are
ORDER-UNDECIDED — which is the true epistemic state of that record.

## 5. The Frontier extension — D6 stands; the vector does NOT collapse

D6 is ratified law: `Frontier = (streams: stream_id → max_id, now: PinnedClock)`. The
shared sequence does not collapse the vector to one component, for four reasons: (1)
membership is partial — historical streams, the law register, the judgment store stay
outside the domain; (2) per-stream components remain the replay index for single-stream
judgments (every banked derivation cites them); (3) visibility lag is per-writer, so
prefix soundness is checked per component; (4) capability manifests are per-stream. What
the shared sequence adds is **comparability**, registered as data:

- **OrderDomain registry** (append-only, authority-module-owned like everything in D1):
  `order_domain_member(stream_id, domain_id, member_since_id)`. Comparability of two ids
  = same domain ∧ both ≥ their streams' `member_since_id`. The adoption event is one
  registry row per member stream — which is also the retrofit story: historical rows are
  simply never members, and the epoch boundary is recorded data, not lore.
- **Type-level guard (ADR-0000 foreclosure):** the cross-stream comparison constructor
  requires domain comparability; a cross-domain id comparison is *unconstructible*, not
  reviewed-for. The blanket cross-stream ban thus becomes a typed rule with a lawful
  positive case, instead of being repealed wholesale.
- **Derived domain-frontier** for cross-stream judgments: `max` over member components —
  derived at use, never a new Frontier component (D6 untouched).
- **Prefix-stability witness** (the allocation-vs-visibility tripwire): at capture, the
  DerivationRecord banks a per-component prefix hash; the close-time pass re-hashes the
  same prefixes; a mismatch (a late-committing write materialized below a banked
  frontier) QUARANTINEs every judgment banked at that frontier. This extends the A.4
  DerivationRecord, not the Frontier type, and answers the frontier half of OQ14 —
  the rest of OQ14 (cache maintenance, racing hooks) remains open and owned.

## 6. Ruling 42: nothing here is, or feeds, a deny surface

Enumerated: sequence allocation cannot refuse a write (`nextval` always succeeds); the
journaler is degrade-not-block by the same clause as `stamp_intercept.py`; `act_live`
adds no trigger to any subject table; the DDL change (default-nextval in place of
bigserial) alters no constraint that can reject a write; every G5-class verdict is a
Family E watch-only flag routed per F28. Any future write-time G5 refusal is its own
ruling-42 promotion — captured specimen, verdict-equivalence at the same frontier,
teaching message, individual ratification — with `ruling42_ratification` non-NULL. The
D13 lift itself is scoped: upon ADOPT, only shared-domain streams, and only
**ORDER-TOTAL-basis** judgments, become schedulable at turn-time; ORDER-ANCHORED
judgments stay close-time (brackets are only complete when both ends have landed and the
transcript reconciliation has run).

## 7. The spike protocol (D22 instantiated): adopt/abandon memo criteria

Build on a scratch lineage (the INC 5 posture; ruling 110's D22: nothing consumes the
live stream before whole-run parity). The memo recommends ADOPT only if **all** hold:

1. **Content parity:** acts_parity AGREE (S3 vocabulary) between `act_live` and the
   close-time transcript parse across one full experiment.
2. **Order parity:** zero inversions between `act_live` id order and vendor per-stream
   transcript order, per stream.
3. **Bracket invariant:** zero violations of `id(request) < id(row) < id(result)` on
   every stamped ledger write in the run — the differential between the new total order
   and the anchored order on their overlap (assign-don't-compete applied to ordering).
4. **Same-second specimen:** at least one same-second cross-stream pair in the run is
   decided by the shared sequence and corroborated by its bracket — the class that
   banned ts, shown handled.
5. **Domain census clean** (§2.5) on the whole run.
6. **Kernel fixture suite green** on the scratch lineage under shared-sequence DDL
   (id gaps break no trigger, no banked fixture regresses).
7. **Negative controls seen red** (ADR-0011: no gate counts until seen red): a
   hook-bypass fixture → parity red; a synthetic late-commit → prefix-stability red; a
   CACHE>1 misconfiguration → config-parity red; a journal-suppression → census red.
8. **Prime-surface analysis recorded** (§2.6) in the memo, with the membership-exclusion
   rationale.
9. **Measurements reported, not gated:** hook journaling latency is measured and filed;
   no gating on unratified numbers (D18 — measurements propose, the maintainer ratifies).

ABANDON if **any** holds: an unexplained order inversion (2 or 3) survives
investigation; a kernel fixture regression is not attributable and fixable; the write
path acquires any deny behavior; parity is systematically unreconcilable. ADOPT is a
maintainer ratification that lifts D13 exactly as scoped in §6 and files the OrderDomain
registry rows; the memo is the ruling's basis, never its substitute.

## 8. Honest limits

1. **Not retroactive.** The dissolution is by-construction only forward; backward is the
   §4 partial order, and its decidedness on real records is unmeasured until the spike.
2. **Allocation ≠ commit.** The residual window of §2.3 is declared, assumption-carried,
   and tripwired — not eliminated.
3. **Coverage = the instrumented path.** `act_live` sees what the hook sees; the
   perimeter boundary (F38) is inherited, not extended. Bypass is a tripwire class per
   the standing threat model (the harness distrusts ledger-vs-acts, not the subject as
   sandbox adversary).
4. **Pairing is unsolved here.** Order without pairing does not yet derive G5; the
   composition is designed, the pairing half is owned elsewhere (§9).
5. **The trusted clock stays open** (OQ8). Pinning and tripwiring `now` makes replay
   exact and inversions loud; it does not make any clock trustworthy.
6. **The import backlog gates the historical half.** One stream imported today; E1/E2
   claims per record wait on that record's transcript import.
7. **Sequence as shared dependency.** One counter under both streams: negligible
   contention at this scale, but a new common-mode config surface — hence the CACHE-1
   parity pin and its negative control.
8. **This document's own common mode.** Same model family as the panel and the critic
   whose observation it works out; the standing recommendation of a non-Fable review of
   engine seeds applies to this one identically.

## 9. Open items, with owner classes

| # | Item | Why open | Owner |
|---|---|---|---|
| FS1 | Transcript import backlog: parse persisted-ephemera transcripts into `acts.act` for the banked corpus (parser qualification rides INC 5 as already planned) | §4; one stream imported | stand-in |
| FS2 | G5 pairing semantics (which acts discharge which change request; `target` matching; multi-act grouping) | §3 scope line | Fable (design) + stand-in (build) |
| FS3 | Witness predicates w1/w2/w3 as mechanical checks + their fixtures | §3; buildable against this seed | stand-in |
| FS4 | `acts.ruling` domain membership (order rulings totally vs anchor-based) | §2.1 exclusion; prime tradeoff | maintainer |
| FS5 | Retroactivity ruling for pre-E3 G5-class judgments (declared exclusion vs anchored-basis derivation per epoch) | §4; = OQ2's instantiation here | maintainer |
| FS6 | OQ1 interplay: a persistent per-lineage sequence extends total order across sessions of one lineage — the *ordering* half of cross-session obligations; the representation half (carry-over state) remains OQ1 | §4 | Fable |
| FS7 | Security-scope declaration rows for `act_live` + `kernel.event_seq` (G14; extends OQ7's list) | §2.1, critic §4 | stand-in (draft) + maintainer (declaration) |
| FS8 | OQ13 union prime audit gains the id-gap channel | §2.6 | Fable (design) + stand-in (instrument) |
| FS9 | Family E verdict members for G5 minted in the registry (per D4/D1 mechanics) | §3 proposal | stand-in, under INC content work |
| FS10 | Remaining OQ14 (cache maintenance, racing hooks) beyond the prefix-stability witness | §5 | Fable |

## 10. Elevate/build split

**Settled by this seed (build against it):** the membership set and exclusions (§2.1);
the write paths and bracket invariant (§2.2); the order-claim type and basis grades
(§3); the epoch structure and manifest carriage (§4); the OrderDomain registry,
comparability guard, and prefix-stability witness (§5); the spike criteria (§7).
**Elevate-only-on-Fable:** FS2 pairing design, FS6, FS8 design, FS10, and any `.lp`
authoring the build requires (OQ21 stands). **Maintainer:** ADOPT/ABANDON on the memo
(the D13 lift), FS4, FS5, the FS7 declaration. Per ruling 110 §5, none of this starts
before its INC predecessor's acceptance is green; this seed changes no increment order —
it is INC 5's design input, banked early so the spike is built against a settled shape.

---

*No files modified but this one. No sub-agents. psql touched read-only, solely to verify
acts.ruling rows 42/43/110 and the acts/kernel schema shapes at citation time.*

---

## Addendum B — review amendments applied (A1–A7) (2026-07-07, dated append; the body above is not retro-edited)

**Lettering:** "Addendum A" is the review's own evidence-provenance appendix, which lives
on the review file; this is the seed's first addendum, lettered B to keep the pair
unambiguous in cross-reference.

**MODEL-SERVED (self-report):** claude-fable-5 — per this session's own system context
("You are powered by the model named Fable 5. The exact model ID is claude-fable-5").
Per the provenance-honesty rule there is no introspective channel that could detect a
silent substitution; no degradation event was observed this invocation. Common-mode
caveat unchanged (§8.8): this addendum shares the model family of the seed, the panel,
the critic, and the review; the standing invitation of a non-Fable review applies to it
identically.

**Provenance of the amendments applied here:**
`consults/engine-frontier-semantics-SEED-review.md`, verdict
**SOUND-WITH-AMENDMENTS(A1–A7)** — review body at commit `c48f9a8`, its
evidence-provenance addendum at commit `530fd61`; anchored in `acts.ruling` as id **113**
(review anchor) and id **114** (post-addendum anchor, supersedes-in-currency 113) —
anchor ids discovered read-only this invocation via a Sonnet SQL relay. Target of the
review: this file at commit `6a584b8`, sha256
`6600076e4354003b1dce46c57d9a64a805e2d46358f10f5139d95afbf699da73` — unchanged between
review and this addendum (verified before appending). Method: quote-and-strike where a
banked claim was wrong; binding design changes stated as such; the body above is never
silently rewritten. Nothing below weakens any binding amendment of
`consults/engine-design-SEED.md`; in particular G5-class cross-stream ordering **remains
BLOCKED under D13** until the maintainer's ADOPT ratification — every amendment here
tightens the spike and the claims, none pre-lifts D13.

### B.0 Resumption-damage corrections (A4 = RD1, A6 = RD2) — quote-and-strike

**RD1 (material; three locations). The corpus-state claim was false.** The live record
at authoring time held **four** imported streams, not one; the act total (735) was
carried correctly, the stream cardinality was not — a half-carried live verification
inside a claim marked "Verified live", the precise resumption-damage class.

1. Record-basis header: ~~"**one imported stream, 735 acts** — the historical acts
   substrate is otherwise still in persisted transcripts, not in Postgres"~~ — STRUCK.
   Corrected fact: `acts.stream` = 4 rows (run_ids **e15, e16, e17, e18**, all created
   before this seed's commit); `acts.act` ids **dense 1–735** across the four, blocks
   1–331 / 332–395 / 396–612 / 613–735, non-interleaved. (Review addendum, re-verified
   against the persisted checksummed relay transcript.)
2. §4 honesty item (i): ~~"`acts.act` holds ONE imported stream today (735 acts); every
   E1/E2 bracket claim waits on transcript import for that record"~~ — STRUCK.
   Corrected: the E2-era stamped experiments (**e17, e18**) are already in Postgres, so
   E2 bracket claims and §7 criterion 3's total-vs-anchored differential have substrate
   **today**; what waits on import is the pre-e15 corpus only.
3. FS1: ~~"one stream imported"~~ — STRUCK. FS1 is re-scoped: the transcript-import
   backlog is the **pre-e15** persisted-ephemera corpus, not "everything but one stream".
   FS1's owner and parser-qualification rider are unchanged.

Direction of error, for the record: pessimistic (the body understated the imported
corpus); no soundness argument leaned on the wrong count. The corrections above are the
authoritative corpus statement; the three struck phrasings must not be cited.

**RD2 (wording; two locations). "Ratified" overstated the ordering laws' depth**,
contradicting this seed's own header (no `acts.ruling` row files the id-is-order law;
its depth is FIND/consult — a census row, not a RULING citation; DB-confirmed by the
review's relay). Under D15/D16 the word is load-bearing (RULING depth is what
gate-feeding judgments require); harmless today only because every verdict proposed in
§3 is flag-only (≥ FIND suffices).

1. §0: ~~"satisfying both ratified ordering laws"~~ → "satisfying both **settled
   ordering laws (FIND/consult depth)**".
2. §2.3: ~~"**The ratified laws are upgraded, not repealed.**"~~ → "**The settled laws
   (FIND/consult depth) are upgraded, not repealed.**" Every within-stream consequence
   still survives verbatim; only the claimed ratification depth changes.

*Related note carried from the review (not damage, not struck):* the header's
"consult 17 §5.3" for the ordering correction is a project-wide inherited mislabel —
the substance is verified true but lives in consult 17 §5.1; the one-line record
correction is owed somewhere central, not in this file.

### B.1 A1 (from F1) — the id source becomes trigger-assigned; binding design change

§2.2's "the id arrives from the table default" was not a construction guarantee: a
`DEFAULT` is overridable, and the subject role's whole-row INSERT grant (s13 precedent)
lets an explicit-id INSERT bypass `nextval` — under the shared domain, a way to plant a
row arbitrarily early in the total order, plus a reachable PK-collision refusal of a
later innocent write (a deny path outside §6's enumeration).

**Binding change:** on every domain-member table the write-boundary trigger assigns
`NEW.id := nextval('kernel.event_seq')` **unconditionally** (the `set_stamp` idiom —
derived, never writer-supplied). The column-scoped INSERT grant (excluding `id`) is
adopted as the secondary, belt-and-suspenders control, not the primary. Consequences,
stated: (i) "by construction" in §2.2 is now literally earned; (ii) hook-independence of
ledger ordering — the design's key robustness property — is preserved (the trigger, not
the hook, assigns); (iii) the squatted-id PK-collision refusal path is foreclosed, so
§6's enumeration is restored without a new ruling-42 item (an unconditional assignment
overrides a supplied value; it never rejects a write); (iv) the §2.5 census gains its
**converse direction** — row-id→allocated: every row id in a member table must appear in
the allocation accounting, anything else UNACCOUNTED → QUARANTINED; (v) §7's negative
controls gain a **squatted-id fixture** (explicit-id INSERT attempt → trigger override
observed, and with the trigger synthetically disabled → census red — seen red per
ADR-0011).

### B.2 A2 (from F2) — the commit-window assumption gets an observer; residual re-worded

§2.3's within-session closure ("the psql call returned before the next tool fired ⟹
committed") has an **innocent** break: background tool execution (`run_in_background`
Bash) can hold a multi-statement transaction spanning a ledger INSERT open across
subsequent foreground tools — no adversarial posture required. And the pre-registered
assumption's invalidating condition ("any observed multi-statement transaction spanning
a ledger insert") named no mechanism by which it would ever be observed: the ts-skew
tripwire cannot see it (Postgres `now()` is transaction-start time, so ts tracks
allocation, not commit) and prefix-stability fires only when a judgment was banked
inside the window.

**Binding change:** the spike lineage enables `track_commit_timestamp`, and the §2.5
census gains a line comparing `pg_xact_commit_timestamp(xmin)` against each ledger row's
`ts`; commit lag beyond a declared bound **is the invalidating condition, observed**.
§7's negative controls gain a synthetic held-open-transaction fixture (must turn this
census line red before it counts). The seriality argument is demoted from closure to
heuristic: it holds only for foreground-serial sessions and is no longer load-bearing.
**Residual re-worded (the stronger reading the assumption row must carry):** an
allocated-but-uncommitted approval is more than "not yet durable" — the open transaction
retains a **commit-or-rollback option**, i.e. the approval remains revocable after
watching the implementation land. The JudgmentSpec `assumptions[]` row carries this
wording so the maintainer prices what is actually being assumed. Classification
unchanged: ACTIVE-adversary shape, outside the standing threat-model scope,
pre-registered — never silently absorbed.

### B.3 A3 (from F3) — w1's join key honestly marked; w2's substrate stated

**w1 (stamp-witnessed) is NOT mechanically computable over the Postgres shapes the body
names, today.** The stamp tuple is `(stamp_session, stamp_agent)` with `stamp_agent` a
subagent **UUID** or `'main'`; `acts.act` carries `actor ∈ {'main', 'sub:<label>'}`
where the label is the vendor description — no UUID column exists, and the UUID↔label
mapping lives only in the ephemera `agent-*.meta.json` files. So w1 grades mechanically
for `'main'`-actor rows only; **subagent-written rows cannot be w1-graded until FS1/FS3
carry the invocation identity backward** — the importer persists (agent id, session id)
onto historical acts rows, mirroring exactly the columns §2.1 already specifies for
`act_live` going forward. FS1 and FS3 now carry this as a **named obligation**; the E2
grading claim in §4 is honest only once that import lands.

**w2 (echo-witnessed) is a two-substrate predicate, stated:** `acts.act` carries
`payload_sha256` (always) and only a bounded excerpt; the exact-match check reads the
payload from the **persisted ephemera transcript**, pins it to the act row via
`payload_sha256`, then matches the returned row id. Mechanical and honest — but the text
substrate is outside Postgres, and the critic's I1 window therefore visibly bounds w2
for any record whose ephemera snapshot postdates its acts.

### B.4 A5 (from F4) — the type-guard claim demoted; the restoration path spelled out

§5's "a cross-domain id comparison is *unconstructible*, not reviewed-for" was an
overclaim in exactly the shape the record has already banked a lesson about
(refute-architecture on P3: stop advertising a review-shaped guard as mechanical). It
holds only at a **typed host-language boundary**; in the sketched substrate — ids
exported to the EDB as bare integers, rules in `.lp`/SQL text — nothing forecloses a
rule author writing `Id1 < Id2` across domains, and the shared sequence sharpens the
hazard (member-stream ids share one integer space while excluded streams stay bare
bigints from disjoint counters).

**Demotion, binding now:** the guarantee reads **"unconstructible at the typed boundary
only; review-shaped in solver text pending the mechanisms below."** The §10 "settled —
build against it" line, as applied to the §5 guard, is scoped to the typed boundary; no
builder may treat solver-text safety as delivered.

**Which restoration arm is adopted — spelled out:** the review's arm (i), **both
mechanisms**, as owned work registered on **FS3**:
1. **Domain-tagged id terms in the EDB export** — all cross-stream order routed through
   the single derived relation produced by the guarded constructor; raw member-stream
   ids never appear as bare comparable integers in solver input;
2. **The rule-text lint** (the INC 3 class checker's sibling) that REDs any raw id
   comparison across stream-sorted variables in `.lp`/SQL text — with its own fixtures
   and a seen-red control, per FS3's existing witness-predicate mandate.

Only when both land does the §5 claim recover a "mechanical" reading — and then as
"typed at the boundary, linted in solver text", never again as bare "unconstructible".

### B.5 A7 — the adoption grant and the fixture role; binding design change

Two misconfiguration hazards the §6 enumeration missed, now designed in: (i) the
adoption DDL **includes the subject role's `USAGE` grant on `kernel.event_seq`** (the
s13 precedent granted only the per-table sequence; an omitted grant refuses every
subject write at adoption — an unratified deny path). One interplay with B.1, flagged
rather than silently resolved: with the id assigned in a trigger, whether the grant is
still exercised depends on the trigger's rights mode; the adoption DDL **pins**
invoker-rights + explicit `USAGE` grant (the review's wording) unless the maintainer
rules for `SECURITY DEFINER` at spike review — either way the negative control below
must see the failure mode red. (ii) §7.6's kernel fixture suite **runs as the subject
role** — stated, because only then can it catch the omitted grant at all. §7's negative
controls gain the **grant-omission fixture** (subject-role write with the `USAGE` grant
revoked → refusal observed → red).

### B.6 Consolidated spike-protocol delta (§7, as amended)

- §7.5 census: both directions (allocated→accounted **and** row-id→allocated, per B.1)
  plus the commit-timestamp lag line (per B.2).
- §7.6: fixture suite runs as the subject role (per B.5).
- §7.7 negative controls, three added to the four banked: squatted-id (B.1),
  synthetic held-open transaction against the commit-lag observer (B.2),
  omitted-`USAGE`-grant refusal (B.5). All seven must be seen red before they count.

### B.7 Status after amendment

All seven amendments are applied above as binding design changes or quote-and-strike
corrections; none reopens the architecture — the dissolution, the bracket invariant, the
epoch semantics, and the ruling-42 posture stand as reviewed. With A1–A7 applied, the
review's condition on §10's "build against it" line is discharged **as design text**;
what remains undischarged is everything this seed always deferred: the spike itself
(D22), the maintainer's ADOPT/ABANDON ruling and the scoped D13 lift, and the FS1/FS3
obligations B.3 and B.4 added. D13 remains in force until ratified otherwise.

---

*Addendum B modified this file only. Sub-agents: one Sonnet SQL relay, read-only, solely
to discover the review's anchor ids (113, 114) in `acts.ruling`; no others. psql not
touched directly by this session.*
