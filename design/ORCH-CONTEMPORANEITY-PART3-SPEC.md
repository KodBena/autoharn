# Contemporaneity, Part 3 — the governance preamble's ordering obligations as one deontic/temporal ASP program (build spec)

Audience: orchestrator (this build spec calls that reader, below, "an executor" — the same role)

This document is a build specification. It tells an executor (Sonnet, per the standing
delegation contract in [CLAUDE.md](../CLAUDE.md)) exactly what to build: one ASP (Answer Set
Programming — the clingo solver's input language) logic program, its EDB (extensional
database — the typed fact base a logic program reasons over),
and an observer-grade report verb, which together turn the ordering obligations of the
governance preamble ([bootstrap/templates/CLAUDE.md.tmpl](../bootstrap/templates/CLAUDE.md.tmpl),
the twelve numbered points every scaffolded [world](../GLOSSARY.md#world) receives at birth)
from prose a session is asked to follow into verdicts a program derives from the world's own
event record. It answers one question: **which of the preamble's obligations can be checked
mechanically from the records Parts 1 and 2 of
[design/CONTEMPORANEITY-AUDIT.md](ORCH-CONTEMPORANEITY-AUDIT.md) already capture, under exactly
what temporal semantics, and with what honest verdict when a check is not decidable?**

It is written for two readers: the executor who builds from it, and the maintainer, who is
asked for no ratification here (everything below is additive and observer-grade — see §8 for
the one place a maintainer word is ever needed).

STATUS: SPEC (Fable-authored, 2026-07-12). Part 3 was named, not designed, in the Part 2
memo's own sketch (design/CONTEMPORANEITY-AUDIT.md, "Part 3 sketch"); this document is that
design pass. Sonnet executes FROM this spec; nothing here is implemented yet, and every
claim about future behavior below is UNWITNESSED by definition until the executor's own
witness protocol (§7) runs.

## 0. Reading order for the executor

Before building, read in full: [engine/lp/contemporaneity.lp](../engine/lp/contemporaneity.lp)
and [engine/contemp_edb.py](../engine/contemp_edb.py) (the substrate you extend — including
the 32-bit anchor hazard in the module docstring),
[engine/lp/ledger_tnow.lp](../engine/lp/ledger_tnow.lp) (the id-is-order law),
[engine/lp/work_items.lp](../engine/lp/work_items.lp) (the s22 EDB shapes you reuse),
[engine/contemp_thresholds.lp](../engine/contemp_thresholds.lp) (the thresholds-as-facts
discipline, with measured derivations in comments), and the preamble template itself. The
house idiom this program must match is stated in those files, not restated here: thresholds
as facts, closed verdict vocabularies, zero `:-` integrity constraints (the paraconsistent
posture — a defective record stays satisfiable and reportable, never a refusal-to-solve),
NAF (negation-as-failure) confined to named seams, `#defined` guards so empty fact families
are silence rather than grounding warnings.

## 1. Position in the settled deontic frame

The project's deontic position is settled and survived a dedicated adversarial refutation
pass ([research/LOGIC-COVERAGE-STATUS.md](../research/LOGIC-COVERAGE-STATUS.md), item 5 of
the covered set; the survey home is
[research/obligations-formalisms-survey/00-synthesis.md](../research/obligations-formalisms-survey/00-synthesis.md)):
**deontic reasoning via the Anderson reduction — an obligation is a recorded, other-assigned
fact; a violation is a derived flag; there are deliberately NO modal O/P/F operators.** The
kernel already instantiates it once (`countersign_obligation` rows → the `review_gap`
derived view; see [GLOSSARY.md](../GLOSSARY.md#obligation)).

This spec stays entirely inside that position — no divergence is claimed or needed:

- **The obligations are recorded facts, not rules baked into the program.** The preamble is
  itself the assignment record: the scaffold writes it into every world at birth, on the
  maintainer's standing authority — an other-assigned obligation in exactly the
  `countersign_obligation` sense, only assigned by the scaffold rather than by `led
  obligate`. The program receives the catalogue as an EDB fact family
  (`preamble_obligation/2`, §4), one fact per formalized point, in its own facts file the
  way thresholds already are. Adding or retiring an obligation is a facts-file edit plus its
  fixtures, never a rule rewrite.
- **Violations are derived flags** (`ob_violated/2`, §5), computed from the event record by
  the same trigger/discharge shape `review_gap` uses: obliging event present, discharging
  event absent.
- **The temporal element is ordering over recorded events, not a temporal modal logic.** The
  settled frame already covers this too (LOGIC-COVERAGE-STATUS item 6: temporal as the
  T_event/T_now split, id-is-order; the Kripke/LTL layer is a settled REJECTION there). §3
  extends the existing two-clock treatment to a two-RECORD seam; it introduces no operator,
  only relations over facts.

## 2. The obligation catalogue

The preamble has twelve numbered points. Each row below is one **atom family** this program
derives, tied to the preamble point it formalizes. "Trigger" is the event that brings the
obligation instance into existence; "discharge" is the event that satisfies it; the
violation rule is always the Anderson shape *trigger present, discharge absent* (with the
per-family qualifications given). Decidability class: **M** = fully machine-decidable from
the named EDB; **M\*** = machine-decidable with a named J-residue (a judgment-side remainder
the machine cannot see — the [conformance map's M/J
split](../law/briefs/BRIEF-CONFORMANCE-MAP.md), "The J-boundary" paragraph, governs what
that means); points with no M core at all are out of scope and dispositioned in §7, not here.

"Before"/"after" in this table means §3's relation exactly — id order within the ledger,
the invocation-window bridge across the ledger/journal seam — never a raw timestamp
comparison. Two foreign numbering systems appear in the table and must not be confused
with the F1–F12 family numbers this spec itself mints: **sNN** identifiers (s22–s25) name
[kernel lineage deltas](../GLOSSARY.md#delta-kernel-lineage-delta) — the numbered schema
records under [kernel/lineage/](../kernel/lineage/) that reach a world via the
[birth chain](../GLOSSARY.md#birth-chain), so "pre-s25" means "a world whose schema
predates that delta" — and a bare **F53**-style number cites the kernel findings register,
not a family below.

| # | Atom family (anchor) | Preamble pt | Trigger | Discharge | Class |
|---|---|---|---|---|---|
| F1 | `ob_commission_first(RowId)` | 10 | any ledger row exists | the minimum-id row has kind `commission` | M (UNDECIDABLE pre-s25: the kind does not exist in that schema's vocabulary, and the fallback the preamble's own point 10 sanctions there — record the ask in a `decision` row and say so in its text — is textually indistinguishable from any other decision) |
| F2 | `ob_verify_commission(CommissionId)` | 10 | a `commission` row exists | a `verify_commission_event` after the commission row and before the first `work_opened` row | M once EDB extension E6 exists; UNDECIDABLE(`no_verify_journal`) until then |
| F3 | `ob_decomposition_refs_commission(WorkRowId)` | 10 | a `work_opened` row exists and a `commission` row precedes it | that row carries a parsed `row:<id>` refs edge to a commission row | M (refs is free text; an unparseable refs value is UNDECIDABLE(`refs_unparsed`), never guessed) |
| F4 | `ob_decompose_before_work(ToolEventT)` | 1 | the first artifact-mutation `tool_event` | at least one `work_opened` row wholly before it | M\* (residue: whether the decomposition covers the ENTIRE commission is J — no machine knows the full increment set) |
| F5 | `ob_open_before_claim(Slug)` | 1 | a `work_claimed` row for Slug | a `work_opened` row for Slug with smaller id | M (pure id order; extends the s22 violations layer additively) |
| F6 | `ob_claim_before_close(Slug)` | 1 | a `work_closed` row for Slug | a `work_claimed` row for Slug with smaller id | M (pure id order) |
| F7 | `ob_countersign_decomposition(WorkRowId)` | 2 | a `work_opened` row exists | a `review`-kind row with larger id, before the stop event when one exists | M\* (presence+ordering only; stamp-distinctness is already refused at write time by the kernel's write-time distinctness gate (findings-register item F53), and the antecedent-audit CONTENT is J. The refined form — the review's `regards` edge landing on the decomposition — is specified but gated on E2) |
| F8 | `ob_criteria_before_work(CriteriaId)` | 3 | a `verification` row carries a parsed refs edge to row C (C is thereby identified as a pre-registered criteria row — identification is retrospective, via the preamble's own `--refs row:<id>` convention) | C wholly before the world's first artifact-mutation `tool_event` | M\* (residue: world-window granularity, not per-work-item — binding a mutation to an item is a missing record kind; see §7. The criteria→result id ordering itself is kernel-foreclosed: refs of later rows point earlier by append-only construction, so that half is VACUOUS by construction and said so, not re-derived) |
| F9 | `ob_ledger_before_delegation(DispatchT)` | 7 | a delegation dispatch event (`delegation_dispatch/1`, E4) | a `decision`-kind row wholly before the dispatch, with no OTHER dispatch between that row and this one (one fresh decision per dispatch — the preamble: "Dispatching a subagent is a `decision` row") | M\* (residue: that the decision names WHAT is delegated is content, i.e. J. The investigation half of point 7 has no dedicated trigger; its observable shape — silent work then a burst — is already Part 2's `silence`/`backfill_suspect`/LATE_DECLARED territory and is NOT re-derived here) |
| F10 | `ob_stop_disposition(StopT)` | 8 | a `stop_event` (E3) | a `decision`-kind row wholly within `[StopT − W, StopT]`, `W` = `stop_disposition_window_ms/1`, a measured threshold fact | M\* (residue: the disposition's stands/remains content is J. A session that dies without its Stop hook firing has no trigger — that absence is reported as UNDECIDABLE(`no_stop_record`) at the family level when other activity exists, never silence) |
| F11 | `ob_clean_at_stop(StopT)` | 5 | a `stop_event` | at StopT: no `question_open` (from [ledger_tnow.lp](../engine/lp/ledger_tnow.lp), loaded underneath), no s22 violation (from [work_items.lp](../engine/lp/work_items.lp)), no open review gap (re-derived from E2+E7; that arm alone is UNDECIDABLE where those extensions are absent) | M (this retrospectively re-derives what [hooks/stop_clean_exit.py](../hooks/stop_clean_exit.py) checks live — deliberate defense in depth, same posture as work_items.lp's provably-vacuous members, and the only check of this kind available on a world where that hook was off) |
| F12 | `ob_record_as_you_go(Token)` | 9 | — imported — | — imported — | M. Point 9 IS Part 2: `backfill_suspect/1` is the violation flag, `late_declared/1`/`batched_declared`/`contemporaneous` the discharge shapes. This program loads ON TOP of contemporaneity.lp and maps those atoms into §5's verdict layer; it re-derives nothing |

Two structural notes the executor must hold:

- **Every "before the first X" rule uses the immediate-successor / #min idiom over the
  finite domain**, exactly as contemporaneity.lp already does (`next_tool_event`,
  `first_tool_event_ts`) — never arithmetic adjacency, never a raw `ts` key.
- **No rule may compare the ledger's `ts` column against a journal time.** §3 says why, and
  the SQL floor (§6) is bound by the same law.

## 3. Temporal semantics — two records, two clocks, one bridge

The event record has two sides that do not share a clock:

- **The ledger side.** Ledger rows are totally ordered by the integer `id` sequence —
  id-is-order, never `ts` (the standing law of
  [ledger_tnow.lp](../engine/lp/ledger_tnow.lp): same-second and 41 ms neighbours exist; the
  id sequence is the sound total order). A row's `ts` is INSERT time on the **Postgres
  server's clock — a different host** from the world (the measured corpus lives at a
  separate DB host; see [engine/contemp_thresholds.lp](../engine/contemp_thresholds.lp)'s
  measurement header). Skew between that clock and the world's is unmeasured a priori.
- **The journal side.** Hook-written journals under the world's `.claude/logs/`
  (invocations, bash completions, mutation/change-gate/delegation observers, stop hook) all
  stamp UTC-Z wall-clock **on the one host running the session** — one clock. All journal
  times enter the EDB as millisecond integers relative to the export's single anchor
  (`ContempEdbExport.anchor_ms` — the 32-bit clingo overflow convention of
  [engine/contemp_edb.py](../engine/contemp_edb.py), which this spec extends and must not
  fork; see §4's one-anchor rule).

**The bridge — how "before" is decided across the seam.** A tokened ledger row is placed on
the journal clock through its own s23 invocation token: the row occupies the closed interval
`[invocation(Tok, Lo), invocation_completed(Tok, Hi)]` — the journaled moment its writing
command was dispatched ([hooks/stamp_intercept.py](../hooks/stamp_intercept.py) mints the
token and journals `Lo` just before the command runs) and the journaled moment that command
completed ([hooks/posttooluse_bash_completion.py](../hooks/posttooluse_bash_completion.py)
journals `Hi`). The true write happened inside that interval by construction, on the same
host clock every `tool_event` carries. So:

- ledger row **before** journal event `E` iff `Hi < T_E`;
- journal event `E` **before** ledger row iff `T_E < Lo` (sound even when `Hi` is missing);
- rows within one invocation share the interval; the id sequence refines their order;
- ledger row vs ledger row: id order, always, regardless of tokens.

**Interval semantics, not point semantics, on purpose:** a comparison is decided only when
the whole interval is on one side. Anything else is refused with a typed reason, never
guessed:

| Seam failure mode | Verdict contribution |
|---|---|
| Untokened row (pre-s23 schema, or a write that bypassed Bash interception) | UNDECIDABLE(`untokened_row`) for any cross-seam comparison involving it; pure-ledger rules (F1, F3, F5, F6, the id half of F7) are unaffected |
| No completion record for the token (crash mid-command; completion hook off) and the rule needs the upper bound | UNDECIDABLE(`open_window`). Deliberately rejected refinement: inferring an upper bound from the NEXT invocation's dispatch — unsound under backgrounded commands |
| Interval straddles the compared event | UNDECIDABLE(`window_overlap`) |
| Journal family unwired / absent for this world | the family's whole verdict is UNDECIDABLE with the capability manifest's own reason (the produced-vs-capable two-axis discipline of contemp_edb.py, unchanged — a wired-but-empty journal is a finding of zero events, never "unwired") |

**Two things never cross the seam.** (1) The ledger's `ts` never keys a cross-record
comparison — the DB host's clock against the session host's clock is exactly the unmeasured
skew the bridge exists to avoid; `ts` continues to feed Part 2's `row_delta_ms` as a
*finding* (the per-invocation skew measurement), never a premise. (2) s24's declared event
time (`row_declared/2`) never repositions a row for an ordering decision: a declaration is
an unauthenticated writer claim (s24's own header), so it may excuse lateness (Part 2's
LATE_DECLARED path, imported by F12) but a backdated declaration must not be able to
retroactively discharge an ordering obligation — that would hand every future session a
laundering channel for precisely the conduct this program audits.

## 4. The EDB — reused families and named extensions

Part 3 adds **no kernel delta**. Every fact below is read from the ledger's existing columns
or from journals that already exist on disk, except E6, which is a template-verb change.

Reused as-is (from [engine/contemp_edb.py](../engine/contemp_edb.py) /
[engine/lp/contemporaneity.lp](../engine/lp/contemporaneity.lp)): `row_tokened/4` (carries
`Kind` — F1/F9/F10's kind tests need nothing new), `row_untokened/3`, `invocation/2`,
`tool_event/2`, `row_declared/2`, and the threshold facts. Reused from the s22 layer, same
shapes as [work_items.lp](../engine/lp/work_items.lp): `work_opened/2`, `work_closed/3`,
`work_witness_present/1`, `work_depends/3`.

Named extensions — each with its concrete source:

| # | New fact family | Source (all read-only) |
|---|---|---|
| E1 | `work_claimed(Slug, RowId)` | ledger `work_slug` column where kind = `work_claimed` (the one s22 event the existing EDB does not export) |
| E2 | `row_refs_row(Id, TargetId)` and `row_regards(Id, TargetId)` | ledger `refs` (free text — parse the preamble's own `row:<id>` convention; count unparseable values as skips and emit UNDECIDABLE(`refs_unparsed`) per affected instance) and `regards` (typed bigint FK, kind=review's attestation target) |
| E3 | `stop_event(Outcome, T)` | `.claude/logs/stop_clean_exit.journal.jsonl` (already written by [hooks/stop_clean_exit.py](../hooks/stop_clean_exit.py): `ts` + closed `outcome` vocabulary) |
| E4 | `delegation_dispatch(T)`, `delegation_return(T)` | `.claude/logs/delegation_observer.journal.jsonl`, distinguishing dispatch lines from `kind:"return"` lines (a finer read of a journal the coarse `tool_event(delegation,T)` already ingests whole) |
| E5 | `invocation_completed(Token, T)` | `.claude/logs/bash_completions.jsonl` (exists since the PostToolUse completion hook landed) |
| E6 | `verify_commission_event(Verdict, T)` | **does not exist yet.** The `verify-commission` template verb ([bootstrap/templates/verify-commission.tmpl](../bootstrap/templates/verify-commission.tmpl)) currently journals nothing; the extension is one appended JSONL line (verdict + UTC-Z ts) to a world-local `.claude/logs/verify_commission.jsonl`, template-side only. Until a world carries it, F2 is UNDECIDABLE(`no_verify_journal`) — named in the manifest, never silently vacuous |
| E7 | `row_actor(Id, ActorId)`, `countersign_obliged(ActorId)` | ledger `actor` column; `countersign_obligation` table. Needed only for F11's review-gap arm (and F7's refined form); the coarse forms of both run without it |
| E8 | `preamble_obligation(F, PreamblePoint)` | a standing facts file, `engine/preamble_obligations.lp`, mirroring [contemp_thresholds.lp](../engine/contemp_thresholds.lp)'s role: the recorded obligation catalogue (§1), one fact per family F1–F12 naming the preamble point it formalizes. This is what guarantees §5's never-silence property on an empty world |
| E9 | `stop_disposition_window_ms(N)` | new threshold fact in the thresholds file, with the same measured-derivation-comment obligation the existing three facts carry (measure from [design/RETROSPECTIVE-RUN10.md](ORCH-RETROSPECTIVE-RUN10.md) / [design/RETROSPECTIVE-RUN11.md](ORCH-RETROSPECTIVE-RUN11.md) and from the ledgers+journals of the first worlds born with s23 in their birth chain, i.e. runs 9 onward; a provisional value must be derived from those measurements in the fact's own comment, never guessed round) |

**The one-anchor rule (binding).** These families are added to `contemp_edb.export()`
itself — NOT a sibling module with its own export. Two exports would mean two anchors, and
facts on different anchors compared in one program is the silent-wraparound hazard class the
module's docstring documents, one level up. The anchor minimum must be taken across ALL
families including E3–E6. Text stays home, as everywhere: no statement/title/witness prose
crosses into the EDB — kinds, ids, slugs, tokens, verdict atoms, and times only.

The program file is `engine/lp/preamble_ordering.lp`. Load order (the
[ledger_assumes.lp](../engine/lp/ledger_assumes.lp)-on-tnow precedent): it stacks on
`contemporaneity.lp` (F12's imports, the window relations) and, when the ledger EDB is also
exported, on `ledger_tnow.lp` + `work_items.lp` (F11's arms); `#defined` guards keep it
groundable standalone.

## 5. The verdict layer

The verdict layer is a closed vocabulary per obligation family — never a boolean, never
silence — organized in two strata:

**Instance stratum** (anchors per §2's table): `ob_discharged(F, Anchor)`,
`ob_violated(F, Anchor)`, `ob_undecidable(F, Anchor, Reason)` — mutually exclusive per
instance by stratified NAF over the monotone base, the contemporaneity.lp ladder idiom.
`Reason` is drawn from a CLOSED reason vocabulary: `untokened_row`, `open_window`,
`window_overlap`, `no_stop_record`, `no_verify_journal`, `refs_unparsed` (each named where
it arises in §§2–3), plus `pre_s25` (the schema predates the s25 commission kind — F1/F2/F3),
`pre_s22` (the schema predates the s22 work vocabulary, so F4–F7's work events cannot exist
on it), and `capability_absent` (the capability manifest declares the feeding journal or
column unavailable on this world — §3's last seam row). A new reason is a spec amendment,
not an ad-hoc atom.

**Family stratum** — exactly one verdict atom per catalogued family per run, loudest-first:

```
preamble_verdict(F, violated)    :- any instance of F violated.
preamble_verdict(F, undecidable) :- no violation, ≥1 instance undecidable.
preamble_verdict(F, discharged)  :- ≥1 instance, all discharged.
preamble_verdict(F, vacuous)     :- preamble_obligation(F,_), no trigger fired.
```

VACUOUS is a real verdict ("no trigger" — e.g. F9 on a session that never delegated), not a
pass and not a defect. Because `preamble_obligation/2` (E8) grounds every family even on an
empty world, the program emits twelve family verdicts always, and the Python harness treats
a missing family verdict as its own loud defect, never as clean. This forecloses by
construction the vacuous-pass class (a silent empty read as clean — findings-register item
F49), which [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)'s
closure-statement amendment and
[ADR-0015](../law/adr/0015-verification-substrate-discipline.md)'s substrate discipline
both forbid.

Base relations (the window relations, `row_refs_row`, dispatch/stop families, per-instance
atoms) are first-class `#show`n outputs — the non-foreclosure posture of every sibling
program: a consumer builds its own report without touching the rules. And as everywhere in
this corpus: these are statements about the RECORD'S SHAPE. `ob_violated` says "the
discharging record is absent from the record," an indictment of the record, not a
conviction of the conduct — adjudicating what a violation MEANS for a session is the
human/ratifier act downstream (Part 2's own non-foreclosure clause, verbatim in spirit).

## 6. Differential posture — the SQL floor pair

**The floor pair is required; no exemption is invoked.** Every derivation in §2 is
join/aggregate/NOT-EXISTS-shaped: interval placement is a join of the row's token against
two journals; "first X" is `MIN`/window functions; the immediate-successor idiom is `NOT
EXISTS` an intervening element; the verdict ladder is `CASE`. That is squarely inside SQL's
expressive floor (the [engine/ledger_floor.py](../engine/ledger_floor.py) recursive-CTE
precedent — and nothing here even needs recursion). The one recognized exemption shape in
this house — `#minimize` optimization, provably beyond a SQL view
([research/LOGIC-COVERAGE-STATUS.md](../research/LOGIC-COVERAGE-STATUS.md) item 8) — is not
used by this program, so no exemption can be argued honestly.

Consequently the marriage discipline applies whole: two independent producers over the SAME
EDB (materialized to scratch tables for the SQL side, the
[ledger_differential.py](../engine/ledger_differential.py) pattern), atom-set equality
required, the closed AGREE / DIVERGE_BY_DESIGN / DIVERGE_DEFECT / QUARANTINED vocabulary,
DerivationRecords banked for both. Part 2's core shipped single-producer under an explicit
maintainer resequencing with a filed deferral; that deferral is not precedent to repeat
silently — Part 3 ships as a pair, or its report says in its own header that it is
single-producer and why, dated. The SQL floor obeys §3's laws identically: no `ts`-vs-journal
comparison, id-is-order, interval semantics with typed refusals.

## 7. Closure statement

The universe is the preamble's twelve numbered points
([bootstrap/templates/CLAUDE.md.tmpl](../bootstrap/templates/CLAUDE.md.tmpl)), enumerated
exhaustively — each is covered, partially covered with its residue named, or out of scope
with its reason. Per [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)'s
closure-statement rule, an axis deliberately not covered is named as not covered.

**Covered (8 of 12), by family:** pt 1 → F4+F5+F6 (residue: decomposition COMPLETENESS is
J — no oracle knows the commission's true increment set; the M-core is the ordering);
pt 2 → F7 (residue: antecedent-audit content is J; write-time stamp distinctness is the
kernel's, not this program's); pt 3 → F8 (residue: world-window granularity — per-item
binding of mutations to slugs is a missing record kind, filed below; session-level
granularity inherits Part 2's own filed deferral); pt 5 → F11 (the review-gap arm
UNDECIDABLE without E2+E7 — named per world by the manifest); pt 7 → F9 (delegation leg
full; investigation leg is Part 2's silence/late-declaration machinery, imported not
re-derived); pt 8 → F10 (residue: disposition content is J); pt 9 → F12 (imported from
Part 2 wholesale); pt 10 → F1+F2+F3 (F2 gated on E6; the FORGED-OR-CORRUPT stop-and-escalate
behavior belongs to the live verb, not this retrospective auditor).

**Out of scope (4 of 12), with reasons:** pt 4 (files committed to git) — git is a third
record system with its own clock and its own integrity machinery
([design/GPG-TRUST-LAYER.md](MAINT-GPG-TRUST-LAYER.md)'s verify-chain rung); joining it into this
event stream is real design work, filed as a possible Part 4, not smuggled in. pt 6
(assumption-before-commitment) — the J-boundary's cleanest case: the trigger (recognizing
that a design fact lacks an antecedent) fires only in an agent's head; the conformance map
files it under its own F/G register as F2 **(J)** — a numbering unrelated to this spec's
F1–F12 — backstopped by that register's G7 (the independent check on subject work) and the
reviewer's antecedent audit (pt 2), not by gap-detection. A conditional M-residue (GIVEN an assumption row citing an artifact, was it
before that artifact's mutations?) founders today on refs being untyped text against journal
file paths — named as the record-kind gap it is. pt 11 (decisions name rejected
alternatives) and pt 12 (subagent numbers marked as self-reports) — content conventions
with no ordering component; prose stays home; nothing for a temporal program to check.
J-residues inside the covered points are enumerated in §2's table per family.

**Witness plan — what run evidence witnesses each rule, both polarities.** The executor's
protocol, per family F1–F11 (F12 is already witnessed under Part 2's own fixtures):
one apparatus-authored [scratch world](../GLOSSARY.md#scratch-schema) GREEN fixture (the
obligation honored: e.g. F1 commission row at min id; F9 a fresh decision row journaled
before each dispatch; F10 a decision row inside the stop window) and one RED fixture (the
same shape broken: first row a decision, a dispatch with no preceding fresh decision, a stop
with a bare ledger tail), banked under `seen-red/preamble-ordering/` with the differential
AGREE transcript, the Part 2 fixture pattern
(`seen-red/contemporaneity-audit/`) followed exactly. UNDECIDABLE needs its own polarity
witnesses for at least the three seam reasons (`untokened_row`, `open_window`,
`window_overlap`) plus one capability-absence case (a pre-E6 world exercising
`no_verify_journal`). VACUOUS is witnessed once (an empty-but-wired world emitting twelve
family verdicts, none silent). Runs 5–11's real ledgers serve as the historical negative
corpus: pre-s23 worlds must come back predominantly UNDECIDABLE on cross-seam families —
witnessed honesty, not a defect.

## 8. Implementation routing

- **Sonnet executes from this spec** (delegation contract: the spec is the Fable-authored
  artifact; engine/lp/ semantics changes require exactly this). Standard scratch ceremony:
  every rule witnessed on scratch worlds both polarities before any live-world read;
  differential AGREE before any verdict is called trustworthy; zero unwitnessed rules and
  zero unexplained differential rows at delivery.
- **Observer-grade, categorically.** The deliverable is a report someone RUNS — a
  `--preamble` mode of the existing `./audit` verb (or a sibling subcommand reading the same
  EDB export), exit 0/1 by family verdict, typed refusal on capability absence, the
  [contemp_audit.py](../engine/contemp_audit.py) harness idiom. It gates nothing: not the
  Stop hook, not pre-commit, not the change gate. Wiring any verdict into a blocking path is
  a separate maintainer question, asked with the first measured live report in hand — the
  exact posture Part 2's memo took, for the same reason (a shape-matcher armed before
  measurement produces theater, the [class-not-instance](../GLOSSARY.md#class-not-instance-net)
  lesson).
- **Deliverable files:** `engine/lp/preamble_ordering.lp`, `engine/preamble_obligations.lp`
  (E8), threshold fact E9 appended to `contemp_thresholds.lp`, extensions E1–E5/E7 in
  `engine/contemp_edb.py`, E6 in the verify-commission template, the SQL floor sibling
  beside `ledger_floor.py`, fixtures under `seen-red/preamble-ordering/`, and the audit-verb
  mode. All additive; no kernel delta; nothing in this list touches a live session's hooks
  (the standing no-live-edits rule — deliver template-side, unwired).
- **Routes to the maintainer:** only (a) any future proposal to arm a verdict as blocking,
  and (b) any discovery mid-build that a rule cannot be derived without loosening a refusal
  or adding a kernel column — doubt about which side of the fail-safe class a change falls
  on IS the routing.

## 9. Honest limits (day one, by design)

- The program audits the RECORD of conduct, not conduct: a session that front-loads
  thinking and writes well-ordered rows is indistinguishable from one that reasoned as it
  wrote — Part 2's machine-observable-events-only limit, inherited verbatim.
- Every J-residue in §2/§7 stands: content-quality of decisions, dispositions, and
  antecedent audits is reviewer territory, deliberately unclaimed here.
- Granularity is the world window, not the session or the work item, in v1 — both finer
  granularities are filed (Part 2's session-granularity deferral; the item-binding record
  kind), not silently absent.
- The obligation catalogue formalizes the preamble AS OF ITS CURRENT TEMPLATE; a world
  scaffolded from an older preamble is audited against obligations it was never assigned.
  v1 accepts this as UNDECIDABLE/VACUOUS noise on old worlds (runs are linear; old worlds
  are dust and read-only evidence anyway); if it ever matters, E8 grows a since-marker —
  filed, not built.

## Status (appended, dated per [ADR-0005](../law/adr/0005-documentation-discipline.md) Rule 8 — the spec above stands unedited)

This section records that an executor built the deliverables §8 above specified, what it found
while building them, and what it witnessed working.

**LANDED, 2026-07-12 (Sonnet, commissioned build — closes the Part-3-implementation half of the
audit-verb-completions tracker item; the orchestrator annotates the tracker itself at merge).**
Every §8 deliverable file exists: `engine/lp/preamble_ordering.lp` (F1–F12 + the verdict layer),
`engine/preamble_obligations.lp` (E8), the E9 threshold appended to `engine/contemp_thresholds.lp`,
E1–E5/E7 in `engine/contemp_edb.py`, E6 (the journal line) in
`bootstrap/templates/verify-commission.tmpl`, the SQL floor (`engine/preamble_floor.py`) beside
`engine/ledger_floor.py`, the differential runner (`engine/preamble_differential.py`, imports
`engine/ledger_differential.py`'s conventions exactly, never re-derives them), fixtures under
`seen-red/preamble-ordering/`, and the audit-verb mode (`./audit --preamble`, via
`engine/preamble_audit.py` wired into `engine/contemp_audit.py`'s own `--preamble` flag). All
additive; no kernel delta; nothing here touches a live session's hooks (delivered template-side,
unwired, per §8's own routing rule).

**TEMPLATE DRIFT CHECK (§8's own ask, "verify the enumeration against the CURRENT template"):
NONE FOUND.** `bootstrap/templates/CLAUDE.md.tmpl` still carries exactly twelve numbered points,
unchanged in count and in point-to-family mapping since this spec was authored — point 10's own
prose has grown more elaborate (spelling out the FULL/LAZY signing-mode split and the
`./verify-commission` gate in more words than the spec's own table paraphrase), but the
OBLIGATION SHAPE F1/F2/F3 formalize (commission-first, verify-it, decompositions-cite-it) is
unchanged. `engine/preamble_obligations.lp`'s own header records this check inline.

**SPEC-VS-REALITY GAP FOUND AND CLOSED IN-PASS (CLAUDE.md's engineering-responsibility
corollary — a hazard met in reach, fixed rather than routed around):** §4 lists
`work_opened/2`/`work_closed/3`/`work_witness_present/1`/`work_depends/3` under "Reused as-is
... same shapes as work_items.lp" — but no live Python module actually exported these before
this build (`work_items.lp`'s own docstring cites `engine/work_item_scratch.py`, which does not
exist as a general exporter). Built here instead, inside `engine/contemp_edb.py`'s own
`export()`, from the SAME ledger row scan PASS 1 already runs for `row_tokened`/`row_untokened`
— one extra set of SELECT columns, zero extra queries — alongside E1's own `work_claimed`
addition. Named in `contemp_edb.py`'s own docstring ("PART 3 EXTENSION" section), not silently
smuggled in as unscoped extra work.

**SCOPE REDUCTION, NAMED HONESTLY (not silently narrowed):** F11's `question_open` and
review-gap arms are UNCONDITIONALLY `UNDECIDABLE(capability_absent)` in this build whenever no
s22 violation is separately found (a real violation still wins, loudest-first — spec §5's own
priority). Wiring `question_open` would require composing THIS EDB with
`engine/ledger_edb.py`'s own SEPARATE export (`entry`/`supersedes`/`answers`, a different
denomination, no consumer for it here yet) — the spec's own text anticipates this ("when the
ledger EDB is also exported") but this build does not implement the composition; filed, not
built. The review-gap arm's own full fidelity (verdict='attest' + supersession) is the identical
gap. F7's refined form (the review's `regards` edge landing on the decomposition, gated on E2)
is similarly UNBUILT — the coarse presence+ordering form ships; E2's `row_regards/2` facts are
emitted by `contemp_edb.py` but not yet consumed by any rule, ready for that follow-on.
F5/F6's RED (VIOLATED) polarity is PROVABLY VACUOUS under normal write-time operation — s22's
own `validate_work_item()` trigger refuses (by an existence check) any `work_claimed`/
`work_closed` row for a slug with no pre-existing `work_opened` row, so a live write can never
produce the violating shape — the SAME class `engine/lp/work_items.lp`'s own
`work_duplicate_open`/`work_shipped_without_witness` members already are (that program's own
header names the precedent); UNEXERCISED via live DB, GREEN witnessed live.

**WITNESS SUMMARY (the spec's own §7 plan, `seen-red/preamble-ordering/run_fixtures.py`, ALL
GREEN as of this landing):**
- **Green+red per family F1–F11** (F12 imported wholesale, already witnessed under Part 2): this
  build used two consolidated live-DB scratch worlds (schema `preambleorder` GREEN,
  `preambleorderneg` RED, TOY db, full lineage through s25) rather than eleven separate tiny
  ones, so each family's own polarity is individually inspectable in one coherent world's own
  report. GREEN:
  F1–F10 and F12 DISCHARGED, F11 UNDECIDABLE(capability_absent) (the scope reduction above,
  not a defect). RED: F1/F2/F3/F4/F8/F9/F10/F11 VIOLATED, F7 UNDECIDABLE(untokened_row), F12
  DISCHARGED (no backfill shape in this fixture's own timing).
- **UNDECIDABLE seam reasons, all three plus capability-absence:** `untokened_row` (live, RED
  world's own untokened review row) and `window_overlap` (live, RED world's own second
  commission row, verify-event timed inside its own invocation window — an instance-level atom;
  F2's family verdict stays VIOLATED regardless, via the first commission row alone) are
  synthesized; `open_window` and `no_verify_journal` are witnessed from the REAL historical
  corpus, not synthesized (see below) — run11 predates `hooks/posttooluse_bash_completion.py`
  (E5) entirely, so every tokened row there lacks a completion record, and predates the E6
  journal entirely.
- **VACUOUS:** witnessed from the real corpus — run9 (`/home/bork/w/vdc/1/run9`, read-only,
  dust), a freshly-scaffolded, fully s23-wired world with ZERO ledger rows, emits all twelve
  family verdicts as `vacuous`, none silent.
- **Differential AGREE, quoted:** GREEN `asp=36 sql=36 atoms; Δasp=[] Δsql=[]`; RED `asp=33
  sql=33 atoms; Δasp=[] Δsql=[]`; both `--retain`ed under
  `engine/docs/ledger-marriage/derivations/preamble-ordering/`. **Negative control:** reusing the
  SAME `sql_atoms_override` seam `seen-red/contemporaneity-audit`'s own cases (p)/(q) precedent
  already uses (forging one atom into the SQL floor's own returned set, never touching either
  producer's real source) produces `DIVERGE_DEFECT`, with `Δasp` naming all 36 real GREEN atoms
  and `Δsql=['preamble_verdict(f1,FORGED)']` — the differential catches a real single-producer
  divergence.
- **Historical corpus (runs 4, 5, 6, 7, 9, 10, 11 — read-only, dust, never touched):** each one's
  own differential result is AGREE (`preamble_differential.py --root /home/bork/w/vdc/1/run<N>`). The
  distribution across these 7 worlds × 12 families (84 instances) is
  **UNDECIDABLE-heavy, reported honestly, exactly as spec §7 anticipated** ("pre-s23 worlds must
  come back predominantly UNDECIDABLE on cross-seam families — witnessed honesty, not a
  defect"): 39 vacuous, 25 undecidable, 17 discharged, 3 violated. The 3 real VIOLATED findings
  are genuine, pre-existing gaps in those worlds' own historical practice, not fixture
  artifacts: run4's F7 (no countersigning review found), run5's F6 (a work_closed row with no
  preceding claim in this build's id-order sense), run11's F3 (its four `work_opened` rows
  never `--refs` the commission row that exists in that same world, id 1) — surfaced here for
  the first time by this mechanism, never previously checked.

**EXIT-CODE COMPOSITION (§8's own "typed refusal on capability absence" ask, stated as this
build's own explicit rule — `engine/preamble_audit.py`'s docstring carries the full account):**
`--preamble` NEVER overrides a non-zero base `./audit` exit (1 BACKFILL_SUSPECT, 2 tool error, 3
N/A capability refusal) — mirrors `--differential`'s own already-shipped "first problem found
stays the reported one" rule. When the base exit is 0, `--preamble` may raise it to a NEW code,
5, reachable only through this flag, iff ≥1 family verdict is VIOLATED. UNDECIDABLE/VACUOUS
never move the exit (this is an observer per spec §8: "it gates nothing"; UNDECIDABLE is the
expected common case on this project's own pre-E1–E9 historical corpus, not a defect signal).
Witnessed live: `./audit --preamble` against run11 → exit 5 (F3 VIOLATED, base exit was 0).

**DEFERRALS, NAMED WITH CONCRETE BLOCKERS (UNEXERCISED, not silently dropped):**
- F11's `question_open`/review-gap full fidelity — blocker: the dual-EDB composition named
  above; no consumer exists yet to justify the extra anchor-composition design work this pass.
- F7's refined `regards`-edge form (E2, gated) — blocker: same as above, scope discipline; the
  coarse form is sound and shipped.

**THE SYNCHRONOUS-B REVIEW LOOP ([ADR-0017](../law/adr/0017-the-zero-context-reader.md)/
[design/ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md)) — WITNESSED, both this
section and [ORCH-CAPABILITIES.md](../ORCH-CAPABILITIES.md) item 24c, 2026-07-12.** This
Status section: B round 1 found six defects (fragments lacking a finite verb, an
under-glossed opening, and one ungrammatical clause); C repaired all six; B round 2 returned
CLEAN on all four clauses. Item 24c: B round 1 found six defects (a two-verb collision, a
mis-stated extension count, an undefined term, and two fragments); C repaired all six; B
round 2 found one residual fragment (a dangling parenthetical after an em-dash). Per the
loop's own two-round cap, that round-2 finding was fixed but the loop is recorded as
NON-CONVERGING for item 24c specifically (the honest record the recipe itself asks for,
rather than a silent third round) — routed to the maintainer/orchestrator as the escalation
event the standing delegation contract already types, not blocking this commit (B's content
judgment is advisory by ADR-0017's own constitutional constraint; the gate checks only that
a fresh-context read happened, never what it concluded).

See BACKLOG.md's dated entry beside this one for the full disposition and commit hashes, and
[ORCH-CAPABILITIES.md](../ORCH-CAPABILITIES.md) item 24c for the operator-facing summary.

## Related

- [design/CONTEMPORANEITY-AUDIT.md](ORCH-CONTEMPORANEITY-AUDIT.md) — Parts 1–2, the substrate
  and the Part 3 sketch this spec discharges.
- [design/LATE-ENTRY-AND-INTAKE-SEMANTICS.md](MAINT-LATE-ENTRY-AND-INTAKE-SEMANTICS.md) — the
  s24 declared-event-time semantics §3 constrains.
- [law/briefs/BRIEF-CONFORMANCE-MAP.md](../law/briefs/BRIEF-CONFORMANCE-MAP.md) — the M/J
  split that draws this spec's scope boundary.
- [research/LOGIC-COVERAGE-STATUS.md](../research/LOGIC-COVERAGE-STATUS.md) and
  [research/obligations-formalisms-survey/00-synthesis.md](../research/obligations-formalisms-survey/00-synthesis.md)
  — the settled deontic/temporal positions §1 stays inside.
- [law/adr/0017-the-zero-context-reader.md](../law/adr/0017-the-zero-context-reader.md) —
  the legibility discipline this document was authored and attested under.
