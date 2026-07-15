# Adversarial review — engine-frontier-semantics-SEED.md (resumption-damage + soundness)

**Target:** `consults/engine-frontier-semantics-SEED.md`, commit `6a584b8` (2026-07-07 19:13:03 +0200),
sha256 `6600076e4354003b1dce46c57d9a64a805e2d46358f10f5139d95afbf699da73` — both verified before reading.
**Commission:** maintainer double-check of a seed authored by an agent terminated mid-run by a server
error and resumed; attack lines fixed by the brief. Rigor bar: the safety-critical-logging BRIEF's.

**MODEL-SERVED (self-report):** claude-fable-5 — per this session's own system context ("The exact
model ID is claude-fable-5"). Per the provenance-honesty rule I have no introspective channel that
could detect a silent substitution; no degradation event was observed this invocation. Note the
common-mode caveat the seed itself carries (§8.8): this review shares the model family of the seed,
the panel, and the critic; it is not the non-Fable review the record still invites.

**Record basis (read in full this invocation):** the target; `consults/engine-design-SEED.md`;
`consults/engine-panel/refute-semantics.md`; `consults/engine-panel/critic-completeness.md`;
`consults/engine-increment-0-unification.md`; `LEDGER-LOGIC-MARRIAGE.md` (body + Appendix A);
BRIEF §3 (G5 row + trigger-class preamble, §4 structural points); consult 17 (§5 and §6 in full,
plus its header); `harness/e13-build/s13-schema.sql`; `harness/e17-build/s17-stamp-mechanism.sql`
+ `stamp_intercept.py`; `POST-FABLE-OPERATING-BRIEF.md` (owner partition + engine sections);
`claude_harness/db/harness/003_acts_stream.sql`; `tools/act_stream/contract.py` +
`claude_code_adapter.py` (attribution mechanics). Database verification (rulings 28/29/41/42/43/110
verbatim; acts.stream/acts.act live shape, counts, kind distribution; id-is-order ruling search)
was delegated to a Sonnet relay per the standing SQL carve-out — two read-only passes, results
quoted below where load-bearing. No other subagents.

---

## Verdict per attack line

### 1. Shared-sequence total order under concurrent writers — CONFIRMED-SOUND core; two FLAWS in the by-construction support

**The core claim holds.** `nextval` on a `CACHE 1 NO CYCLE` sequence is atomic, non-transactional,
never rolled back; the allocation events form a true real-time total order across connections. The
seed phrases its claims on allocation order, not commit/visibility order, and that phrasing is the
correct one. The direction-of-error analysis (§2.3 support 2) is sound: a false DISCHARGED requires
the approval's INSERT statement to have executed before the implementation request act was even
allocated — the assertion event genuinely preceded the implementation — so residual error falls on
the flag-more side. The pre-registered allocation-to-commit residual is the right *classification*
(ACTIVE-adversary shape, out of the standing threat-model scope, pre-registered as a JudgmentSpec
assumption rather than silently absorbed — exactly the sanctioned vehicle). The prefix-stability
witness correctly catches the turn-time half: an approval materializing below an already-banked
frontier QUARANTINEs the judgments banked there.

**FLAW F1 — "the id arrives from the table default" is not a construction guarantee.** A `DEFAULT`
is overridable: the subject role holds `GRANT INSERT ON <ledger>` (whole-row — s13 precedent,
`s13-schema.sql:450`), so an INSERT supplying an explicit `id` bypasses `nextval` entirely. Under
the shared domain this is worse than today: every id consumed by an *act* allocation is a free PK
value in the *ledger* table, so an explicit-id write can plant an "approval" arbitrarily early in
the total order. The census (§2.5) does catch the collision after the fact ("exactly one of
{ledger, act_live, refusal journal}" — a planted row makes two homes → QUARANTINED), which is
tripwire-consistent; but (a) a squat on a *not-yet-allocated* id above the frontier is outside the
census as written (the check runs allocated→accounted, never row-id→allocated), and (b) when the
sequence later reaches a squatted id, an **innocent** default-path write is refused by the PK
collision — an unratified write-refusal path §6's enumeration misses (see attack 3). The fix costs
one line and makes the claim literally by-construction: the write-boundary trigger assigns
`NEW.id := nextval('kernel.event_seq')` unconditionally (the `set_stamp` idiom — derived, never
writer-supplied), or the INSERT grant is column-scoped to exclude `id`; add the census's converse
direction and a squatted-id negative control to §7.

**FLAW F2 — the residual's within-session closure has a hole, and its invalidating condition has no
observer.** §2.3 closes the window intra-session by seriality: "the psql call returned before the
next tool fired ⟹ committed." Background tool execution (`run_in_background` Bash — a first-class
harness feature) breaks that premise *without* an adversarial posture: a backgrounded psql can hold
a multi-statement transaction spanning a ledger INSERT open across subsequent foreground tool
calls. The pre-registered assumption ("short autocommit ledger writes"; invalidating condition:
"any observed multi-statement transaction spanning a ledger insert") covers this verbally — but
names no mechanism by which the condition would ever be *observed*. Neither declared tripwire
reaches it: the ts-skew tripwire cannot (Postgres `now()` is transaction-start time, so ts-order
tracks allocation order, not commit order — no inversion appears), and prefix-stability only fires
when a judgment was banked inside the window. A cheap mechanical observer exists and should be
named in the spike: enable `track_commit_timestamp` on the scratch lineage and add a census line
comparing `pg_xact_commit_timestamp(xmin)` against `ts` per ledger row — a commit lag beyond a
declared bound IS the invalidating condition, observed. One wording strengthening in the same
clause: the residual is more than "orderable as DISCHARGED while not yet durable" — an open
transaction retains a commit-or-rollback *option*, i.e. the approval remains revocable after
watching the implementation. The classification (ACTIVE shape, out of scope, pre-registered)
survives at full strength; the assumption row should carry the stronger reading so the maintainer
prices what is actually being assumed.

With F1+F2 repaired, the pre-registration is sufficient and no false-order hazard remains hidden
within the declared threat-model scope.

### 2. Historical witnessed-anchor partial order — FLAW on w1's computability; w2 needs its substrate stated; w3 CONFIRMED; the grading scaffold itself is honest

- **w3 (delegation-bracketed) — CONFIRMED against the record.** `delegation_spawn`/
  `delegation_return` are members of the closed act-kind vocabulary (`003_acts_stream.sql`,
  `contract.py`) and exist live: 7 spawn/return pairs in the imported corpus, paired in every
  stream that has them.
- **w2 (echo-witnessed) — sound but under-specified.** `acts.act` carries `payload_sha256`
  (always) and a 280-char bounded `payload_excerpt`; the raw payload lives in the committed
  ephemera. So the "exact-match predicate over the result act's payload" is computable only as a
  **two-substrate check**: read the payload from the persisted transcript, pin it to the act row
  via `payload_sha256`, then match the row id. That is mechanical and honest — but the seed names
  `acts.act` shapes and never states that the predicate's text substrate is outside Postgres.
  State it; the critic's I1 window then visibly bounds w2 for anything whose ephemera snapshot
  postdates the acts.
- **w1 (stamp-witnessed) — FLAW F3: the join key does not exist in the record shapes named.** The
  stamp tuple is `(stamp_session, stamp_agent)` where `stamp_agent` is the hook's `agent_id` — a
  subagent **UUID**, or `"main"` (`stamp_intercept.py:79`). The acts substrate's invocation
  identity is `actor ∈ {'main', 'sub:<label>'}` where the label is the vendor `description`/
  `agentType` — **not the agent UUID** (`claude_code_adapter.py:210-222`); no acts.act column
  carries the UUID, and the UUID↔label mapping lives only in the ephemera `agent-*.meta.json`
  files. So w1's "mechanical predicate over record content" is not computable over the named
  Postgres shapes for any subagent-written row: 'main' rows match trivially, subagent rows cannot
  match at all. Repair (cheap, and it belongs on FS1/FS3 as a named obligation): the importer
  persists the invocation identity (agent id + session id) onto acts rows — which is precisely
  what §2.1 already specifies for `act_live` going forward; the E2 grading is honest only once the
  import carries the same tuple backward.
- The epoch structure, manifest carriage (A.2 idiom), ORDER-UNDECIDED as a first-class derived
  verdict, and the refusal to assert decidedness ahead of the spike are all sound and correctly
  graded. The corpus-state misstatement that undercuts §4's honesty item (i) is filed under
  attack 4 (RD1), where it belongs.

### 3. Ruling 42 / tripwire-not-authentication — CONFIRMED-SOUND (two enumeration gaps, amendment-level)

Ruling 42 was re-verified verbatim against `acts.ruling` (binding; watch-only default; four-part
per-judgment promotion protocol; e17 template). The designed path is clean: `nextval` cannot refuse;
the journaler inherits `stamp_intercept.py`'s degrade-not-block clause; `act_live` adds no trigger
to any subject table; the DDL swap (default-nextval for bigserial) alters no rejecting constraint;
every G5-class verdict is a watch-only Family E flag routed per F28; the D13 lift is scoped to
ORDER-TOTAL-basis judgments only. The bypass semantics (§2.4) carry s17's declared posture
faithfully — tripwire, never authentication; detect-and-quarantine, never gate.

Two gaps in §6's enumeration, both misconfiguration hazards rather than designed surfaces, both
belonging in §7's negative controls: (i) domain membership requires the subject role's `USAGE`
grant on `kernel.event_seq` (the s13 precedent granted the per-table sequence); an omitted grant
refuses every subject write at adoption — the fixture-suite criterion (§7.6) catches this only if
the fixtures run *as the subject role*, which should be said; (ii) F1's squatted-id PK collision is
a reachable refusal of an innocent write outside ruling 42's protocol until F1 is foreclosed.

### 4. Resumption-damage sweep — RESUMPTION-DAMAGE: one material instance, one wording instance; the rest of the fabric checks clean

- **RD1 (material, three locations): "one imported stream, 735 acts" is false — the record holds
  FOUR imported streams.** Live: `acts.stream` = 4 rows (run_ids **e15, e16, e17, e18**);
  `acts.act` ids 1–331 / 332–395 / 396–612 / 613–735 — dense 1..735 across the four. The act
  total (735) is exact, which proves all four streams existed at verification time: the count was
  carried, the stream cardinality was not — a half-carried live verification, the precise
  resumption-damage class, in a claim marked "Verified live." Locations: the record-basis header
  (line ~30), §4 honesty item (i) ("acts.act holds ONE imported stream today (735 acts)"), FS1
  ("one stream imported"). Direction of error: pessimistic — it *understates* the imported corpus;
  in particular the E2-era records (e17, e18 — the stamped experiments) are already in Postgres,
  so E2 bracket claims and §7 criterion 3's total-vs-anchored differential have substrate today,
  and FS1's backlog is the pre-e15 corpus, not "everything but one stream." No soundness argument
  leans on the wrong count; the record basis and FS1's premise must still be corrected.
- **RD2 (wording, twice): "ratified ordering laws."** §0 ("satisfying both ratified ordering
  laws") and §2.3 ("The ratified laws are upgraded, not repealed") contradict the seed's own
  header, which states precisely — and the DB confirms (zero `acts.ruling` rows match the
  id-is-order law; the relay's search) — that the ordering laws' ratification depth is
  FIND/consult, a census row, not a RULING citation. The header's precision reads post-resumption;
  the body's "ratified" reads pre-. Under D15/D16 the word is load-bearing (RULING-depth is what
  gate-feeding judgments require); amend both to "settled (FIND/consult-depth)". Harmless today
  only because every proposed verdict is flag-only (≥ FIND suffices).
- **Checked and clean:** "ruling 110 §2" resolves to ruling 110's numbered item 2 (the D17
  refusal-capture ruling), which pre-registers verbatim "innocent id gaps (crashes, sequence
  caching, other aborted inserts) may QUARANTINE and cost adjudication time" — the seed's census
  claim (§2.5) cites it accurately, and the census genuinely shrinks that class (and the CACHE-1
  pin retires the "sequence caching" cause). D6/D13/D22 are quoted faithfully from inc-0 as
  ratified by ruling 110 (verified binding). Refute-semantics flaw 3 and critic §2 bullet 5 are
  characterized accurately. The G5 row is quoted verbatim from BRIEF §3.1, including "before it is
  applied," and the minimum-constituent-act-id rule matches its conservative reading. The builder
  trap is true as stated: live `acts.act.id` is `GENERATED ALWAYS AS IDENTITY`, which cannot share
  a sequence — the `DEFAULT nextval` form is genuinely required. Every §2.1 exclusion re-surfaces
  in §8/§9 with an owner (FS4, FS8); no constraint named early is dropped late; the elevate/build
  split honors the post-Fable owner partition.
- **Note, not damage:** "consult 17 §5.3" for the ordering correction is a project-wide inherited
  mislabel — the correction actually lives in consult 17 §5.1 ("Correct before use," the 41 ms /
  same-second rows-24/26 defect) and its header; §5.3 is "The default-theory framing." The
  mislabel originates in consult 17's own §6.2 cross-reference and is propagated by
  `s13-schema.sql` and marriage §3 rule 2; the seed copies the record's convention, and the cited
  *substance* is verified true. A one-line record correction is owed somewhere central, not here.

### 5. OrderDomain / type-guard ("cross-domain id comparison unconstructible") — FLAW: aspiration labeled as construction for the lanes that matter

The claim holds only at a typed host-language boundary (a Python OrderDomain-tagged id whose
comparison constructor demands domain comparability — buildable, real ADR-0000 foreclosure). But in
the implementation shape the record actually sketches — ids exported to the EDB as bare integers
(`ledger_edb.py` idiom: `entry(Id, …)`, acts facts), rules in `.lp`/SQL text — **nothing forecloses
a rule author writing `Id1 < Id2` across domains**; ASP and SQL will ground and evaluate it without
complaint. The shared sequence sharpens the hazard: post-adoption, ledger and act ids share one
integer space while the deliberately-excluded streams (judgment store, refusal journal, historical
schemas, `acts.ruling`) remain bare bigints from disjoint counters — a raw comparison against those
is exactly the garbage the guard exists to prevent, and it is one keystroke away in solver text.
"Unconstructible, not reviewed-for" is therefore an overclaim in precisely the shape the record has
already banked a lesson about (refute-architecture on P3: stop advertising a review-shaped guard as
mechanical). Repair, either arm honest: (i) route *all* cross-stream order through one derived
relation produced by the guarded constructor, export ids to the EDB as domain-tagged terms, and add
a rule-text lint (the INC 3 class checker's sibling) that REDs any raw id comparison across
stream-sorted variables — making the guard mechanical where it cannot be type-level; or (ii)
restate the guarantee as "unconstructible at the typed boundary; mechanically linted in solver
text," and register the lint as owned work on FS3. As written, the seed's §10 "settled — build
against it" line hands a builder a guarantee the sketched substrate does not deliver.

---

## Salvage — what survives attack and is load-bearing

1. **The dissolution itself:** one apparatus-owned `CACHE 1 NO CYCLE` sequence under the ledger
   and `act_live`, claims phrased on allocation order — the sound, constructive answer to
   refute-semantics flaw 3, forward from adoption. (With F1 repaired it is by-construction in the
   full sense the seed claims.)
2. **Hook-independence of ledger ordering** (§2.2): ordering from the table default, witnessing
   from the hook — hook death degrades witness grade, never order. The design's best property.
3. **The bracket invariant** `id(request) < id(row) < id(result)` for hook-observed writes, and
   its use as the total-vs-anchored differential on the overlap (§7.3).
4. **The F10-shaped direction-of-error argument:** errors fall flag-more, never license-more.
5. **The three-valued order relation with a declared basis** (ORDER-TOTAL / ORDER-ANCHORED(grade) /
   ORDER-UNDECIDED as a derived, first-class verdict) — the honest vocabulary the BRIEF's bar
   demands; w3 verified real in the record, w2 real once its substrate is stated.
6. **The epoch structure** (E0–E3) with manifest-carried order basis per target — refusal over
   silent guess, the A.2 idiom correctly generalized.
7. **Membership exclusions as prime-surface engineering** (§2.1) and the pre-registered id-gap
   self-information channel (§2.6) routed into OQ13 — the e12 discipline applied forward.
8. **The domain census** (§2.5) as a genuine strengthening of D17/ruling-110-item-2, shrinking the
   pre-registered innocent-gap adjudication class (needs its converse direction, per F1).
9. **D6 non-collapse** — all four reasons hold; comparability as registered data
   (`order_domain_member` with `member_since_id`) is the right retrofit story.
10. **The prefix-stability witness** (§5) — the allocation-vs-visibility tripwire that makes the
    turn-time half of the residual loud; a real answer to OQ14's frontier half.
11. **Ruling-42 cleanliness of the designed path** and the scoped D13 lift (ORDER-TOTAL turn-time
    only; anchored stays close-time).
12. **The spike protocol** (§7) — negative controls seen red, measurements-propose-maintainer-
    ratifies, adopt/abandon as ruling basis not substitute. Add the three new negative controls
    named above (squatted id, commit-lag observer, subject-role grant check).
13. **Scope honesty throughout:** pairing severed from ordering (FS2), retroactivity to the
    maintainer (FS5), decidedness left empirical per the N=1 posture, the common-mode disclosure.

## Amendments required (the SOUND-WITH-AMENDMENTS list)

- **A1 (F1):** trigger-assigned id (or column-scoped INSERT grant) on every domain member; census
  gains the row-id→allocated direction; squatted-id negative control in §7.
- **A2 (F2):** name the commit-window observer (`track_commit_timestamp` +
  `pg_xact_commit_timestamp(xmin)` census line) as the assumption's invalidating-condition
  detector; name background execution as an innocent seriality break; strengthen the residual's
  wording to the commit-or-rollback option.
- **A3 (F3):** FS1/FS3 carry the w1 join-key obligation — the importer persists (agent id,
  session id) onto historical acts, mirroring §2.1's `act_live` columns; w2's two-substrate
  predicate (ephemera payload pinned by `payload_sha256`) stated explicitly.
- **A4 (RD1):** correct the corpus state in the header, §4(i), and FS1 — four streams (e15–e18),
  735 acts, E2-era records already imported; re-scope FS1 to the pre-e15 backlog.
- **A5 (F4):** restate the cross-domain guard honestly and register the rule-text lint (or
  domain-tagged EDB id terms) as owned work.
- **A6 (RD2):** "ratified ordering laws" → "settled ordering laws (FIND/consult depth)" in §0 and
  §2.3.
- **A7:** subject-role `USAGE` grant on `kernel.event_seq` in the adoption DDL; §7.6 fixtures run
  as the subject role.

None of the amendments reopens the design's architecture; all are foreclosures or honesty
restatements the seed's own disciplines (ADR-0000 construction, P3's non-mechanical lesson, the
e12/threat-model pre-registration vehicle) already demand.

## Overall verdict

**SOUND-WITH-AMENDMENTS(A1–A7)** — the acts_live dissolution, the forward total-order mechanism,
the anchored-partial-order/epoch semantics, and the ruling-42 posture all survive adversarial
review; four flaws (F1 id-source, F2 unobservable invalidating condition, F3 w1 join key, F4
type-guard overclaim) and two resumption-damage instances (RD1 "one imported stream" — material,
corpus-state; RD2 "ratified" depth wording) require the listed amendments before the seed's §10
"build against it" line is fully earned.

---

*Files modified: this one only. Sub-agents: one Sonnet SQL relay (two read-only passes), per the
standing carve-out; no others. psql not touched directly by this session.*

---

## Appendix — 2026-07-07, evidence-provenance addendum (dated append; the body above is not retro-edited)

The SQL relay's **second pass** (the follow-up carrying the stream run_ids, the per-stream id
ranges, the per-stream kind pairing, and the ruling-gap id) completed, but its reply to this
session **failed to deliver** through the harness channel — the relay's own transcript records
`SendMessage` failing with "No agent named 'general-purpose' is reachable" and ends with an
explicit delivery caveat ("relay of the above falls to the caller"). The maintainer supplied the
relay's full rendered output out-of-band at `/tmp/x` (sha256
`34db05b5216623660e3a83ae99fef43bf15d0ac8159101dffc4b7c413038d55c`) after the body above was
committed at `c48f9a8`.

Both passes are now re-verified against the **authoritative persisted transcript**, snapshotted
whole-session per the auditability rule:
`claude_harness/docs/claude-ephemera/session-7be3443d/-home-bork-w-vdc-1-claude-harness/subagents/agent-a13df52a6c58cdaa2.jsonl`
(sha256 `8687d5f405a210977f672b047782dfbe56785d3fa8e22f8174968ba29d309bd0`, 123029 bytes,
manifest-pinned in that snapshot's `MANIFEST.json`). Every live-record figure the body cites is
confirmed verbatim against it:

- `acts.stream` = 4 rows: run_ids **e15, e16, e17, e18** (created 2026-07-07 00:36 / 03:22 /
  13:27 / 17:26 +02 — all before the seed's 19:13 commit, closing the residual timing question:
  the four streams demonstrably predate the seed's "Verified live" claim);
- `acts.act` id blocks **1–331 / 332–395 / 396–612 / 613–735**, dense 1..735, non-interleaved
  (RD1 stands exactly as stated);
- per-stream kind pairing: tool_call = tool_result and spawn = return in every stream; e16 has no
  delegation rows (w3 substrate: streams 1, 3, 4);
- the single `acts.ruling` id gap is **36** (count 111, max 112).

Provenance honesty, stated plainly: the body was committed citing the second pass while its
delivery to this session had failed in the harness channel; the citation is now record-observed
(F42/F46) via the persisted, checksummed transcript above. No figure changed; no verdict changes.
RD1, the flaw set (F1–F4), the amendment list (A1–A7), and the overall
**SOUND-WITH-AMENDMENTS(A1–A7)** verdict all stand unamended.
