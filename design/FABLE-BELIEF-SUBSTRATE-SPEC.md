# FABLE-BELIEF-SUBSTRATE-SPEC — the typed belief substrate (kernel delta family), v1 convention + v2 deltas

<!-- doc-attest-exempt: ratified build basis, frozen 2026-07-22 (ledger row 1919, maintainer "yes go" with R1-R3 landed). Construction reads from this file as-frozen; the ADR-0017 A:B:C prose-polish runs separately against a live edition per the FABLE-PRINCIPAL-IDENTITY-SPEC build-basis precedent. Removal condition: strike when the polished live edition supersedes this as the reference copy. -->

**Status:** DRAFT FOR MAINTAINER RATIFICATION. Fable-authored, fresh-context, 2026-07-22, per
the standing rule that nobody edits `kernel/lineage/` without a Fable-authored,
maintainer-ratified spec (CLAUDE.md ORCHESTRATION). Implements the RATIFIED consult
[design/FABLE-CONSULT-EPISTEMIC-DOXASTIC-SUBSTRATE-2026-07-22.md](FABLE-CONSULT-EPISTEMIC-DOXASTIC-SUBSTRATE-2026-07-22.md)
under the maintainer's resolved decisions (ledger rows 1893–1894, 1909–1910). Nothing here is
applied to any existing world: the v2 deltas reach reality only by entering a FUTURE world's
[birth chain](../GLOSSARY.md#birth-chain) (runs are strictly linear, maintainer ruling
2026-07-11). The three genuinely open choices are collected in §10; everything else is fixed by
this spec or by the resolved Q-series and is not re-opened by the builder.

**What this document specifies, in plain words.** Seven witnessed failures share one shape: a
confident belief operated on this project's record without ever being ON the record as a belief
— so nothing could demand its search universe, nothing could ask for its witness, and nothing
could defeat it except a human catching it by eye. This spec gives beliefs a typed home in the
ledger. A belief row must say whether it claims "for all X" (and then it must enumerate where it
looked) or "there exists an X" (and then, if it claims observation, it must point at the
witness). It must say what it stands on — observation, derivation from named rows, testimony
from a named row, or bare assumption — and the derivation and testimony edges form a queryable
graph, so "five independent layers checked this" becomes a query whose answer can be *no*. Two
principals' contrary beliefs do not fight by recency: both drop into visible doubt until one is
withdrawn or outranked by evidence class. "Knowledge" is never stored — it is a derived view
(`credited_beliefs`) computed fresh, exactly as the defeat pipeline already computes credit.
The work ships in two steps: **v1**, a statement-prefix convention on ordinary rows, witnessed
on scratch chains with the same derivation rules the typed version will use; **v2**, the kernel
delta family. Per the maintainer's binding condition (row 1909/1910), v2 is recorded as a typed
ledger obligation — a `work_opened` row — at the moment v1 ships, never as prose staged inside
this document.

**Primary inputs, all read in full:** the consult above (primary);
ledger rows 1887 (the two-bias rule — the spine's provenance), 1890 (report-induced false
belief), 1893/1894 (naming), 1895 (doubt tier + warrant-directed verification), 1906
(named-consumer test), 1909 (Q-series resolution), 1910 (staged-work commission);
[CLAUDE.md](../CLAUDE.md); [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)
(incl. the 2026-07-02 closure-statement amendment and the 2026-07-22 named-consumer anecdote);
[ADR-0002](../law/adr/0002-fail-loudly.md), [ADR-0008](../law/adr/0008-classification-discipline.md),
[ADR-0011](../law/adr/0011-mechanization-discipline.md) (Rule 1 vocabulary; the 2026-07-02
negative-control/shipped-binding amendment), [ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md)
(P1/P2/P8, and the 2026-07-22 P10);
kernel idiom exemplars read as SQL: [s22](../kernel/lineage/s22-work-item-ledger.sql),
[s36](../kernel/lineage/s36-decision-grade.sql), s40/s41 (via the frozen
[build basis](FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md), the structural exemplar this spec
follows), [s43](../kernel/lineage/s43-typed-verdict-write-boundary.sql),
[s44](../kernel/lineage/s44-model-identity-attestation.sql) (the v1→typed staging precedent),
[s46](../kernel/lineage/s46-credited-views.sql), [s48](../kernel/lineage/s48-review-witness-existence.sql);
`engine/lp_registry.py` (LAYERS), `engine/lp/ledger_defeat.lp` (the three stratification laws),
`engine/ledger_edb.py` (the s44 v1 statement-parse contract this spec's v1 mirrors).

---

## 0. The resolved-decisions record (fixed; the builder and reviewers do not re-open these)

| Q | Resolution | Where |
| --- | --- | --- |
| Q1 | The kind is **`belief`** (not `claim`); "knowledge" stays prose; the derived surface is **`credited_beliefs`**. Grounds: accurate; the commission's own word; everyday reading = technical reading; `claim` collides with s22 `work_claimed` and JWT/OIDC claims. | rows 1893–1894 |
| Q2 | **ADOPTED**: the universal/existential polarity spine with typed obligations — universal ⇒ enumerated universe mandatory; observed existential ⇒ witness mandatory; testimony ⇒ source FK. | row 1909 |
| Q3 | **Paraconsistent** contest semantics: both contested beliefs demote to visible doubt; evidence-class precedence may resolve; recency never resolves between distinct principals. | row 1909 |
| Q4 | **Two-step staging** (v1 convention → v2 typed delta), WITH the binding condition: **v2 is a typed ledger obligation written at v1 ship time** — the existing s22 work-item machinery, never prose in this spec's body. The maintainer's reasoning, row 1910 verbatim in the ledger: staged stage-2s buried in ratification documents fall into oblivion. | rows 1909–1910 |
| Q5 | Review-verdict bridging is a **second increment** — out of v1/v2, staged and therefore obligation-rowed (§8.1). | row 1909 |
| Q6 | **YES** to the dispatch-grain independence delta (backflow finding 6 / access-consult D5), in scope as its own small delta (§3.5). | row 1909 |
| Q7 | The consult's mandated-site-vs-opt-in dichotomy is challenged as likely dishonest; this spec **re-derives the option space** (§4) and defaults to opt-in at the kernel. Presented as a decision point (§10 R1), not inherited. | row 1909 |

A note on row 1910's own commission: a general, first-class staged-work *type* is separately
commissioned and is **not built here**. This spec's staging uses today's s22/s28/s29 work-item
rows, with slugs and titles shaped so the rows can migrate onto that type mechanically when it
lands (§2.4).

---

## 1. The defect, named at class level (ADR-0000 Rule 2 — the two questions)

**(a) The type question.** The class in its most general form (consult §1, adopted): *an
assertion-act whose quantifier, evidence obligation, basis, and holder-relation are
unrepresentable, so every overclaim built on it is representable.* The foreclosing type:
a `belief` row cannot be constructed universal without its enumerated universe, cannot be
constructed observed-existential without a resolvable witness, cannot relay another's verdict
as its own observation (testimony demands a source FK; observation demands a witness the
relayer does not have), and cannot be credited except through derived, never-stored views whose
chains bottom out in witnessed observation or in-force non-belief rows.

**(b) The operational lapse.** Executive-side: the ledger has carried a typed-but-inert
`confidence` slot since s15 and a working defeat calculus since s44, but no kind whose
semantics is "principal P asserts proposition S on basis B" — the assertion-act hole the
2026-07-14 consult named and nothing closed. The net minted here: the write-time CHECKs and
refusal triggers of §3, their detect siblings, the `belief` judge layer, and the gates already
standing (hash coverage, kind-shape manifest) extended in the same commits.

Row 1890's specimen (report-induced false belief: every atomic claim true, the composed reading
false) is covered by composition, not by new machinery: the composed headline belief gets a
typed home (`basis='derived'`, premises = the report rows), so the false composition is
contestable and its premise closure is queryable — while belief formation inside a reader's
head stays honestly out of scope (§9).

**Confidence: high** — the diagnosis is the consult's, held there at high confidence and
grounded in seven dated specimens.

---

## 2. v1 — the statement-prefix convention (no kernel delta; witnessable immediately)

### 2.1 The grammar (fixed; the parse contract shared verbatim with every producer)

A v1 belief is an ordinary `kind='decision'` row (written through the standing write path;
`led decision ...`) whose `statement` begins with the prefix token `belief[`. Grammar, in the
s44 `model-attestation` idiom (key=value fields, hard-refused on malformation, never silently
skipped):

```
belief[<polarity>] basis=<basis> [universe={<surface>; <surface>; ...}]
    [witness=<token>[,<token>...]] [source=row:<id>]
    [premises=row:<id>[,row:<id>...]] [subject=row:<id>]
    [contests=row:<id>] [concurs=row:<id>]
    :: <proposition text, free prose, to end of statement>
```

- `<polarity>` ∈ `universal` | `existential` (closed; exact lowercase, never case-folded —
  the s44 casing posture).
- `<basis>` ∈ `observed` | `derived` | `testimony` | `assumed` (closed).
- `universe={...}`: the enumerated quantification universe — semicolon-separated named
  surfaces/axes/clauses; `row:<id>` and `artifact:<sha256-hex>` tokens inside it are
  existence-checkable; free-text surface names are legal (a universe names territory, not only
  rows). **Mandatory iff polarity is `universal`; forbidden otherwise.**
- `witness=...`: comma-separated `row:<id>` / `artifact:<hash>` tokens. **Mandatory iff
  polarity is `existential` AND basis is `observed`; forbidden on `universal`.**
- `source=row:<id>`: **mandatory iff basis is `testimony`; forbidden otherwise.**
- `premises=...`: **mandatory (non-empty) iff basis is `derived`; forbidden otherwise.**
- `subject`, `contests`, `concurs`: optional; each a single `row:<id>`. `contests`/`concurs`
  must name a row that is itself a v1 belief (prefix-carrying) or, post-v2, a `belief` row,
  authored by a different principal than the writer (§3.3's semantics, parse-checked in v1).
- `::` separates fields from the proposition. The proposition is the row's assertion content;
  it lives nowhere else (one home).

The parser lives in `engine/ledger_edb.py` (`export_belief()`, v1 arm), mirroring the s44
contract: rows whose trimmed statement starts with `belief[` are candidates; a malformed
candidate raises a typed `BeliefParseError` naming the row id and the violated obligation —
counted, never dropped (the s44 P-4/P-5 discipline). The v1 obligations are the same truth
table §3.1 freezes for v2; v1's honest weakness is that they bind at **parse time, not write
time** — a malformed v1 belief exists in the ledger and is refused only when the engine reads
it. Stated per ADR-0011 Rule 1; this is the price Q4's two-step buys its early witnessing with,
and exactly what v2 closes.

### 2.2 What v1 builds (all engine/repo-side; zero kernel objects)

1. `export_belief()` in `engine/ledger_edb.py` — the EDB producer, v1 arm now, typed-column
   arm at v2 (the s44 dual-arm precedent: both arms parse into the SAME fact families, so
   every derived rule survives the v1→v2 migration unchanged). Capability manifest per the
   F49 discipline: the belief fact families declare PRODUCED | CAPABLE | DEFERRED, never a
   bare empty result.
2. `engine/lp/ledger_belief.lp` — the ASP rules of §3.4, and their SQL floor twin
   (`engine/belief_floor.py`, the `ledger_floor.py` sibling idiom), compared bit-identically.
3. `LAYERS["belief"]` in `engine/lp_registry.py`:
   `("ledger_tnow.lp", "ledger_support.lp", "ledger_defeat.lp", "ledger_belief.lp")` — the
   defeat stack underneath because `credited_belief/1` consults `model_defeated/3` (§3.4);
   `require_layer_stack` refuses a mis-stacked invocation before grounding.
4. `./judge --layer belief` wiring via `run_layer_differential` (the "work"-layer precedent),
   with `_LAYER_FLOOR_PREDS["belief"]` naming the compared predicates (§3.4).
5. The v1 scratch witness fixtures (§7.1).

EDB fact families (shared by both arms; ids are the interchange, text stays home):

```
belief(Id).                      belief_polarity(Id, universal|existential).
belief_basis(Id, observed|derived|testimony|assumed).
belief_has_universe(Id).         belief_has_witness(Id).
belief_edge(Id, premise,  T).    belief_edge(Id, source,   T).
belief_edge(Id, contests, T).    belief_edge(Id, concurs,  T).
belief_subject(Id, T).
row_actor(Id, P).  agent_class(P, C).      % reused from export_defeat
```

### 2.3 v1 ship definition

v1 is SHIPPED when: the parser, floor, ASP rules, layer registration, and judge wiring are
committed; the §7.1 fixtures are witnessed both-polarity on scratch chains; and the §2.4
obligation rows are written. No live-world convention rows are required for shipping — the
convention is *available* from that commit; whether any site is obliged to use it is §4's
question.

### 2.4 The v2 obligation, typed at v1 ship time (the Q4 binding condition — this section is normative)

In the SAME session that ships v1 (before its ship report; the report cites the row ids), the
shipper writes to this project's ledger, using the existing s22 machinery via the shipped
verbs:

```
./led work open belief-substrate-v2 --title "belief substrate v2 (design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3): the typed kernel delta family — belief kind, nine columns, refusal triggers, derived views, judge layer belief, dispatch-grain independence delta; enters a FUTURE world's birth chain"
./led work open belief-review-bridge --title "belief substrate second increment (spec §8.1, Q5 SECOND): derive testimony-basis beliefs from review verdicts in the EDB so CLEANs enter the corroboration/shared-premise calculus"
./led work depends belief-review-bridge belief-substrate-v2
./led work open belief-doubt-tier --title "belief substrate staged item (spec §8.2, ledger row 1895): light doubt tier + warrant-directed verification queue; demotes nothing, queues warrant-checks, costs a typed reason"
./led work depends belief-doubt-tier belief-substrate-v2
```

Properties this discharges: the obligations are **typed** (s22 `work_opened` rows, kind-shape
CHECKed), **queryable** (`work_item_current` / `led work list`), **surfaced** (`./pickup`'s
open-work reading), and **close-disciplined** (s29: a `shipped` close REQUIRES a witness — the
birth-chain commit hash — so v2 cannot be hand-waved closed; `deferred`/`dropped` closes are
themselves typed, dated acts the maintainer can see). Exactly the oblivion class row 1910
names, foreclosed with machinery that already exists. When row 1910's general staged-work type
lands, these three rows migrate under that spec's rule; the slugs above are stable identities
chosen for that migration (`belief-*` prefix, one deliverable per slug, titles carrying their
spec section), and nothing else about them is bespoke.

The spec body deliberately contains **no other statement of what v2 "will" do later** — every
staged item in this document appears in §8's enumeration WITH its obligation row above.

---

## 3. v2 — the kernel delta family

Three deltas, ratified together as one family, entering one birth chain in order. Working
names below; the numeric `sNN` names are assigned from the next free numbers at build time by
directory listing (the s46 A2 collision lesson), expected s53/s54/s55 on today's head (s52).

Family-wide idiom (binding, from the exemplars): kind-CHECK widening by DROP/ADD re-issue of
`ledger_kind_check` (one home); nullable columns with **no column DEFAULT** (the s30/s41
lesson); one concern per CHECK, kind-shape CHECKs separate from value CHECKs (the s40 idiom,
for `gates/kind_shape_manifest_gate.py`'s classifier); refusals as `RAISE EXCEPTION` with
teach-text from BEFORE INSERT triggers — which, post-s43, are caught by the boundary functions
and committed as `write_refused` rows for free (no new journaling machinery); every new column
joins `compute_row_hash` in the same delta (s42's law; `gates/hash_coverage_gate.py` red/green
both polarities); `ledger_current`/`countersigned_in_force` re-issued with the new columns
appended (the s20 lesson), non-member views re-verified and enumerated in the delta header
(the s38 discipline); HISTORY analysis per mechanism; detect siblings behavior-fingerprinted,
witnessed t/f on shaped/unshaped scratch worlds.

### 3.1 Delta B1 — `sNN-belief-substrate` (kind, columns, CHECKs)

**The kind.** `belief`, twenty-sixth member of the closed vocabulary (after s44's
`model_identity_attested`, the twenty-fifth). The holder is the existing `actor` + stamp — no
new holder column (one home per fact). The proposition lives in `statement` — no second text
column. The pre-existing `confidence` column becomes the holder's own three-valued self-grade
on belief rows: carried, hash-covered since s42, and **deliberately unread by the crediting
rules** (the attestation-grade precedent: a self-grade steering credit would be
self-certification; a rule reading it is a future ratified act).

**Nine new columns** (prefix `belief_`, per the house `attest_*`/`refusal_*` pattern; all
nullable, no DEFAULTs):

| column | type | licensing (exact semantics) |
| --- | --- | --- |
| `belief_polarity` | text | mandatory on `belief`, forbidden elsewhere (two-way). Value CHECK `IN ('universal','existential')`. |
| `belief_basis` | text | mandatory on `belief`, forbidden elsewhere (two-way). Value CHECK `IN ('observed','derived','testimony','assumed')`. |
| `belief_universe` | text | belief-only (one-way kind guard); within belief: present non-empty iff `belief_polarity='universal'` (two-way coupling). The enumerated quantification universe — searched surfaces, clause lists, axes, sibling surfaces; `row:`/`artifact:` tokens existence-checked (§3.2); registry references where a registry exists ([law/STANDARDS-REGISTRY.md](../law/STANDARDS-REGISTRY.md)). |
| `belief_witness` | text | belief-only (one-way); forbidden when `belief_polarity='universal'`; mandatory non-empty when `belief_polarity='existential' AND belief_basis='observed'`; optional on other existential rows. Comma-separated `row:`/`artifact:` tokens, existence-checked. |
| `belief_source` | bigint REFERENCES ledger(id) | belief-only; within belief: present iff `belief_basis='testimony'` (two-way coupling). The source record the testimony relays. |
| `belief_premises` | bigint[] | belief-only; within belief: present with `cardinality >= 1` iff `belief_basis='derived'` (two-way coupling). Deliberately NOT the existing `enacts` column: `enacts` means "design antecedent carried into force" — a different fact; overloading it would be the false-cognate class row 1893 taught (ADR-0008). Element existence checked by trigger (arrays carry no FK). |
| `belief_subject` | bigint REFERENCES ledger(id) | belief-only, optional (one-way). The row the proposition is about, where there is one (the `regards`/`attest_row_id` idiom). |
| `belief_contests` | bigint REFERENCES ledger(id) | belief-only, optional (one-way). The challenged belief row; trigger-validated (§3.3). |
| `belief_concurs` | bigint REFERENCES ledger(id) | belief-only, optional (one-way). The concurred-with belief row; trigger-validated (§3.3). **Spec-derived addition beyond the consult's column list, flagged for ratification (§10 R3):** the corroboration view needs typed concurrence — the consult's own §3.2 rule is that no mechanism reads meaning, so "two beliefs assert the same proposition" must be a typed act by the second holder (exactly as contest is), never a statement-text match. |

CHECK spellings (the builder implements these truth tables; expressions given to fix NULL
semantics — one concern per constraint):

```sql
-- kind-shape (two-way):
belief_polarity_kind_shape:  (kind = 'belief') = (belief_polarity IS NOT NULL)
belief_basis_kind_shape:     (kind = 'belief') = (belief_basis IS NOT NULL)
-- kind guards (one-way; each of the seven optional/conditional columns):
belief_universe_kind_shape:  belief_universe  IS NULL OR kind = 'belief'   -- likewise
    belief_witness / belief_source / belief_premises / belief_subject /
    belief_contests / belief_concurs
-- value vocabularies:
belief_polarity_check: belief_polarity IS NULL OR belief_polarity IN ('universal','existential')
belief_basis_check:    belief_basis    IS NULL OR belief_basis IN
                           ('observed','derived','testimony','assumed')
-- polarity couplings (NULL-polarity rows, i.e. every non-belief row, pass vacuously —
-- the one-way kind guards above carry the forbidden-elsewhere half):
belief_universe_coupling:
    (belief_polarity IS DISTINCT FROM 'universal'
       OR (belief_universe IS NOT NULL AND btrim(belief_universe) <> ''))
    AND (belief_polarity IS DISTINCT FROM 'existential' OR belief_universe IS NULL)
belief_witness_universal_forbidden:
    belief_polarity IS DISTINCT FROM 'universal' OR belief_witness IS NULL
belief_witness_observed_mandatory:
    NOT (belief_polarity = 'existential' AND belief_basis = 'observed')
       OR (belief_witness IS NOT NULL AND btrim(belief_witness) <> '')
-- basis couplings (two-way inside belief):
belief_source_coupling:
    (belief_basis IS DISTINCT FROM 'testimony' OR belief_source IS NOT NULL)
    AND (belief_source IS NULL OR belief_basis = 'testimony')
belief_premises_coupling:
    (belief_basis IS DISTINCT FROM 'derived'
       OR (belief_premises IS NOT NULL AND cardinality(belief_premises) >= 1))
    AND (belief_premises IS NULL OR belief_basis = 'derived')
```

Mixed beliefs ("all X except this one Y") decompose into one universal plus one existential
row; the CLI verb's usage text says so (the consult's own teach obligation).

**What is unrepresentable by construction** (stronger than any refusal, ADR-0000 Rule 1):
relaying another's verdict as one's own observation — the relay is `testimony` with a
mandatory source FK, and `observed` demands a witness the relayer does not have. Finding 6's
laundering path closes at the type layer.

### 3.2 Delta B1 — the refusal triggers (all additive; s43-journaled for free)

Two new single-purpose BEFORE INSERT triggers beside the existing `validate_*` family (the
s48/s43 idiom — never folded into `validate_work_item`'s dispatcher; orthogonal concerns):

**`validate_belief_evidence`** — token existence on `belief_witness` and `belief_universe`:
every `row:<digits>` token must name an existing ledger row (the s48 extraction/verification
mechanism, reused); every `artifact:<64-hex>` token must resolve in the s51 artifact store
(the s52 mechanism, reused). Teach-texts, fixed in substance (builder may adjust formatting,
not content):

- universal without universe is already foreclosed by CHECK; the trigger's universe-token leg
  teaches on a dangling token: *"belief policy: universe token % names no existing row/artifact
  — an enumerated universe is the claim's own evidence (ledger row 1887, rule 1: the surface
  list derives from where the system PRODUCES artifacts of that kind, not from where the
  auditor happens to stand); cite rows/artifacts that exist, or name the surface in prose."*
- dangling witness token: *"belief policy: witness token % resolves to nothing — a finding
  without its witness is treated exactly as ADR-0005 Rule 9 treats a verdict without its
  artifact: as nothing. Record the evidence first (led artifact put / the witnessed row), then
  the belief."*
- (The CHECK-level refusals of §3.1 need no trigger; their SQLSTATE-23xxx aborts are caught
  and journaled by the s43 boundary like any constraint refusal, and the CLI verb fronts them
  with usage teach-text.)

**`validate_belief_edges`** — cross-row semantics the CHECKs cannot see:

1. every `belief_premises` element names an existing ledger row (existence only; in-force-ness
   is a READ-time judgment — §3.4 — because history legitimately grounds beliefs and the
   credit view, not the write path, is where foundering belongs);
2. `belief_contests` target: must exist, be `kind='belief'`, be unsuperseded at write time,
   and carry a DIFFERENT `actor` than the new row resolves to. Teach-text: *"belief policy:
   contest is the cross-principal doubt act — you cannot contest your own belief (revise it
   instead: supersede it with your new position, s31). A contest against row % by its own
   holder is a revision wearing a challenge's clothes."* And for a superseded target:
   *"row % is no longer in force; contesting settled history defeats nothing (the record beats
   memory — contest the current belief, or write your own)."*
3. `belief_concurs` target: same existence/kind/unsuperseded tests; same different-actor test
   (teach: self-concurrence is not corroboration — s17's honesty, one edge over);
4. supersession discipline on belief targets (the s45 same-kind identity-continuity pattern +
   Q3's no-recency-between-principals rule, enforced rather than assumed): a row whose
   `supersedes` names a `belief` row is refused unless (i) it is itself `kind='belief'` AND
   (ii) its resolved actor equals the target's actor. Teach-text: *"belief policy: a belief is
   revised only by its own holder (supersession = self-revision, s31); another principal's
   contrary position is a CONTEST — write your own belief with belief_contests=% and both
   enter visible doubt until resolved by evidence class or withdrawal (Q3, paraconsistent;
   recency never decides between principals)."* This is an additive refusal on a previously
   silent path; its blast radius is analyzed in HISTORY (no pre-existing row can name a
   `belief` target — the kind is born here — so the constraint is vacuous on every
   pre-existing world position).

**Honestly review-only, declared now (ADR-0011 Rule 1):** whether an enumerated universe is
the *right* universe (a lazy universe is representable — the type makes it visible and
contestable, not impossible); whether a proposition's prose strengthens its source's
vocabulary (the tamper-evident→tamperproof class); whether a `concurs` edge really asserts the
same proposition. No mechanism reads meaning; the substrate forces the material for that
review onto the record.

**Bookkeeping in the same delta:** kind CHECK re-issue (+`belief`); `compute_row_hash`
re-issued +9 columns in catalog ordinal order (s42's law; both-polarity gate witness);
`ledger_current` / `countersigned_in_force` re-issued +9 appended (s20; non-members
re-verified and enumerated); `gates/kind_shape_manifest_gate.py` manifest +9 rows (the
FORBIDDEN/conditional idioms already exist in its classifier since s43 — the builder verifies
the coupling-CHECK shapes classify, extending the classifier in the same commit if not, never
leaving a CHECK silently unparsed); `gates/ledger_reader_allowlist.py` unchanged (no new raw
readers — §3.4 views factor through `ledger_current`); CLI verb `led belief` (flags mirroring
the columns; every shared-loop channel honored or loudly refused, the Axis-1 discipline;
usage text carries the decomposition rule and the polarity/basis truth table).

### 3.3 Contest, concurrence, revision — the semantics (Q3, fixed)

- **Revision** = supersession by the holder (unchanged s31: uniform retraction,
  reinstatement-free; new position = new row). Enforced same-kind, same-holder (§3.2 item 4).
- **Contest** = a belief row carrying `belief_contests` → both the challenger and the target
  are demoted to visible doubt: both appear in `contested_beliefs`, both leave
  `credited_beliefs`, until (i) one is superseded by its holder, or (ii) evidence-class
  precedence resolves. The maintainer's AC-1 challenge becomes: write a contesting belief
  citing the uncovered surface; the SILENT verdict is un-credited loudly before anyone
  adjudicates.
- **Evidence-class precedence** (closed, small, applied only to resolve a contest, only when
  the bases differ): `observed` > `derived` > `testimony` > `assumed`. On strict inequality
  the higher-basis belief is the contest's resolved survivor (it returns to credit; the
  lower stays demoted until superseded); on a tie nothing resolves — both stay in doubt.
  **Recency never resolves a contest between distinct principals** (the record beats memory);
  recency governs only self-revision, which is supersession anyway.
- **Concurrence** = a belief row carrying `belief_concurs`: a typed statement by a
  SoD-distinct holder that it asserts the same proposition as the target. Feeds
  `corroboration` and `shared_premise`; grants nothing by itself.

### 3.4 Delta B2 — `sNN-belief-views` (derived views + the judge layer; view-only, zero columns — the s46 shape)

All views `security_invoker`, SELECT to `:role`, factoring through `ledger_current` (the s31
current-truth discipline; no raw-`ledger` leg, no allowlist entry needed). Each view names its
consumer (row 1906 — stated inline; a view with no honest consumer was pruned, see §8.4):

1. **`belief_current`** — in-force belief rows with their typed columns. *Consumer:* the other
   views (base), `led`/`pickup` operator reads, the SPA read surface.
2. **`contested_beliefs`** — one row per contest edge between two in-force beliefs:
   `(belief_id, contested_by, contest_basis, target_basis, resolved_survivor NULLABLE)`.
   Cause always visible — a consumer that hides the contesting edge implements a censored
   record (the s46 auditability-wall rule, restated here as binding). *Consumer:* the operator
   adjudicating doubt (pickup/audit reads); `credited_beliefs`.
3. **`credited_beliefs`** — the substrate's derived "what the project currently credits"
   surface, never stored: in-force `belief` rows that are (i) not demoted by an unresolved
   contest (a resolved survivor re-enters), and (ii) **well-founded**: the recursive closure
   over `premise` and `source` edges reaches only nodes that are — an in-force belief with
   `basis='observed'` (witness existence-checked at write), or an in-force non-belief ledger
   row not defeated in derived reads (`model_defeated` composes here: a defeated premise or
   witness row un-founds the beliefs standing on it, with neither calculus knowing the
   other's internals — the chain-in-force test does the composition); every intermediate
   belief on the chain itself in force and uncontested. `basis='assumed'` beliefs are
   recorded, defeasible, and **never credited** — an assumption's consumer is its future
   defeat (the row-1852 class: a counterexample must find something to defeat), not credit.
   *Consumer:* warrant-directed verification (row 1895's ranked queue, staged §8.2, reads
   this surface when it lands); operator reads; the ratification-question surface ("what does
   the record currently credit about X").
4. **`corroboration`** — per credited belief, the derived witness-diversity grade, closed
   vocabulary `uncorroborated | corroborated-same-class | corroborated-cross-class`, computed
   from concurrence-connected, SoD-distinct, in-force beliefs joined to `agent_class` (human
   principals are a class). Two fresh same-class reviewers agreeing can never read
   `cross-class` — the attestation incident's manufactured confidence becomes a grade the
   record cannot overstate. Reported, gating nothing (the attestation-grade precedent).
   *Consumer:* the A:B:C loop's escalation judgment and audit briefs (how much is this CLEAN
   worth); the future doubt tier's warrant ranking.
5. **`shared_premise`** — for concurrence-connected belief sets: the common ancestors of
   their premise/source closures (`(belief_a, belief_b, shared_ancestor)`). "Five independent
   layers" becomes a query whose answer can be *no*. Transitive closure is the ASP layer's
   home ground — this is the deductive engine doing the work the project exists for.
   *Consumer:* independence audits (the ADR-0000 Revisit-#4 class); ADR-0014 second-opinion
   dispatch decisions (is this reviewer actually out-of-frame).

**The judge layer.** `--layer belief`: ASP producer `engine/lp/ledger_belief.lp` stacked per
`LAYERS["belief"]` (§2.2), SQL floor `engine/belief_floor.py`; compared bit-identically via
`run_layer_differential`; `_LAYER_FLOOR_PREDS["belief"]` = `contested_belief/2`,
`contest_resolved/2`, `credited_belief/1`, `corroboration_grade/2`, `shared_ancestor/3`.
The `ledger_defeat.lp` stratification laws bind verbatim: every in-force test is
`not superseded/1` (never `credited_belief/1` over the machinery's own inputs); machinery
inputs are quantified over RAW history in both producers where exclusion domains apply (the
s50 lesson — specifically, the defeat-input exclusion the belief layer inherits by stacking);
belief credit composes BESIDE `in_force/1`, never into it — `in_force/1` stays
supersession-only permanently.

### 3.5 Delta B3 — `sNN-dispatch-grain-independence` (Q6, in scope; the smallest delta of the family)

The class (backflow finding 6 / access-consult D5): stamp distinctness is grained at
(session, agent), so a genuinely isolated dispatch's verdict, relayed by the orchestrator's
own writing invocation, is representable only as `self-review` plus prose — honest but lossy
to any reader of the `independence` column alone.

**Mechanism chosen: one additive vocabulary member.** `review_detail.independence` gains
`disclosed-isolated-dispatch` (CHECK re-issued five-member). Semantics: an honest
*disclosure* — "this verdict was produced by an isolated dispatch and is relayed by its
dispatcher's invocation" — NOT an independence *claim*: `validate_independence` treats it
exactly as `self-review` (no stamp-distinctness gate, because the writing invocation is
genuinely the dispatcher's), and no crediting rule reads it in v1. It records strictly more
truth than `self-review` while claiming nothing a stamp cannot witness.

**Alternative considered and rejected, on the record:** dispatch-id-keyed stamp distinctness
(treating a dispatch id as a third stamp component). Rejected because no server-witnessed
dispatch-id channel exists for a non-writing subagent — the id would be dispatcher-asserted,
a client-claimed identity doing independence duty, precisely the lying-signature shape
s17/s21 exist to refuse. If the hooks layer ever mints a witnessed per-dispatch token (an s23
sibling), promotion from disclosure to claim is a future amendment with a real witness behind
it; named, not built.

Composition with the substrate (why Q6 rides this family): once beliefs exist, the relayed
verdict's *content* travels as `basis='testimony', source=<the review row>`, and the source
row's own independence column now says `disclosed-isolated-dispatch` instead of
underclaiming `self-review` — the two deltas jointly make the relay representable end to end.
Fail-safe shape: adds one vocabulary member, relaxes nothing (the new value passes through
the same no-gate path `self-review` always had); routed under this spec's ratification
regardless, because it mints vocabulary.

### 3.6 Composition with existing machinery (stated precisely)

- **s43 write boundary:** belief rows enter via `kernel.ledger_write` (payload keys are
  column names; `belief_premises` rides jsonb array → bigint[]); every §3.1/§3.2 refusal
  journals as a committed `write_refused` row with teach-text. No new write path, no new
  journaling.
- **s26/s42 hash chain:** +9 columns in `compute_row_hash`, same delta; coverage gate is the
  net (both polarities).
- **s31 supersession:** unchanged and load-bearing — revision IS supersession; all views are
  current-truth readers; no history reader is proposed (none has a named consumer — §8.4).
- **s44/defeat:** untouched. Model-identity defeat governs rows; belief contest governs
  propositions; they compose through the chain-in-force test (§3.4 item 3) with neither
  knowing the other's internals.
- **s17/s21 review machinery:** untouched except B3's additive vocabulary member. The review
  bridge is the staged second increment (§8.1).
- **s36 graded-token idiom:** if a deployment ever wants a corroboration grade to GATE an
  act, the kernel keeps storing tokens and `apparatus.json` gives them force — no kernel
  change reserved, named as the layering.
- **s48/s51/s52 evidence custody:** the witness/universe token checks reuse those mechanisms
  verbatim; a belief's witness can point at bytes that cannot silently change.
- **Idris model:** `design/Autoharn.idr` parity per the standing obligation discipline — the
  build closes the whole outstanding lag through this family or the freshness gate stays
  honest about the remainder (the s40 Axis-A-16 posture).

---

## 4. Q7 re-derived — where does the obligation to record beliefs attach?

The consult's Q7 offered "one mandated site vs fully opt-in." The maintainer challenged the
dichotomy as likely dishonest (row 1909), and on re-derivation he is right: the real design
axis is not *whether* to mandate but **where an obligation to write belief rows can attach**.
The option space, enumerated:

| # | Shape | Assessment |
| --- | --- | --- |
| O1 | **Fully opt-in** — beliefs written when a principal chooses | Zero bureaucracy; but every §1 specimen was a site where nobody chose. Honest floor, not a whole answer. |
| O2 | **Default-on with per-act-type opt-out** (deployment policy: every audit verdict / close / attestation must be belief-shaped unless opted out) | Inverts the burden project-wide; the certification-bureaucracy shape the quality-bar rulings reject — a substrate everyone must feed on every judgment. Rejected as default. |
| O3 | **Kernel coupling to gated act-kinds** (e.g. a strict `work_closed` refuses without a cited credited belief) | Strongest surface, wrong first move: it makes credit load-bearing before the calculus has field history, and its refusals would gate acts whose writers never minted beliefs — a flag-day. Named as the future escalation once §8.1's bridge exists and credit has been lived with; not built. |
| O4 | **Per-role obligations via s41 bindings** (a role binding, e.g. `auditor`, carries the duty that its verdicts land as beliefs; which roles, per deployment, via the s36 apparatus layering) | Well-shaped middle path — typed, deployment-configurable, no kernel change beyond reading machinery that exists. But it needs an enforcement consumer (something that checks the duty) that does not exist yet; minting the duty record before its checker fails the named-consumer test today. Named as the natural first escalation. |
| O5 | **One mandated kernel site** (the consult's scheduler-model suggestion) | The dishonest narrowness the maintainer flagged: it picks one site by salience, not by type. Subsumed by O3/O4 done properly. Rejected. |
| O6 | **Instrument-carried mandate** — audit briefs, conformance instruments, and A:B:C worker briefs require verdicts in belief shape (v1 grammar / v2 rows), per ADR-0000's own 2026-07-02 clause: "where a workflow instrument carries a claim schema, the closure statement's three parts are required fields, not prose" | The obligation attaches where the witnessed failures actually lived (the two-bias audit was a briefed instrument run; the CLEANs were briefed reviews), costs nothing kernel-side, and binds at dispatch time — the orchestrator writes the brief, so the mandate has an existing enforcement point (the brief author + the conformance instrument). |

**Default adopted by this spec (pending §10 R1): O1 at the kernel + O6 at the instrument
layer.** The kernel mandates nothing; audit-class and review-class BRIEFS authored in this
project require their absence/coverage/satisfaction verdicts to be recorded in belief shape
(v1 grammar until v2 lands). O4 and O3 are the named escalation ladder, in that order, each a
future ratified act with its own consumer. This is presented as a decision point, not
inherited: the maintainer may prefer O6 to be law-side (a dated ADR amendment) rather than
practice-side, or may want O4 pulled forward.

---

## 5. Enforcement-surface declarations (ADR-0011 Rule 1, per element)

| Element | Surface |
| --- | --- |
| Polarity/basis vocabularies; kind-shape + coupling CHECKs (§3.1) | **write-time data constraint** |
| Witness/universe token existence; edge validation; supersession discipline (§3.2) | **write-time data constraint** (trigger; refusals journaled via s43) |
| v1 grammar obligations (§2.1) | **run-time invariant** of the engine (parse-time typed refusal) — honestly WEAKER than write-time, named; closed by v2 |
| Derived views' correctness (§3.4) | **test/CI gate** — the SQL/ASP differential (`./judge --layer belief`, AGREE required), plus the seen-red fixtures |
| Hash coverage of new columns | **test/CI gate** (`gates/hash_coverage_gate.py`, both polarities) |
| Kind-shape manifest totality | **test/CI gate** (`gates/kind_shape_manifest_gate.py`) |
| Layer stack completeness | **construction/import-time** (`require_layer_stack` refuses before grounding) |
| Universe *rightness*; paraphrase-strengthening; concurrence honesty | **review-only** — declared, with the §8.2 doubt tier as the named future mechanization trigger |
| §2.4 obligation rows' eventual discharge | **write-time data constraint** (s29: shipped-close requires witness) + **review-only** for choosing to close |
| O6 instrument mandate (§4, if ratified) | **review-only** at brief authoring; the conformance instrument is the named mechanization trigger on recurrence |

## 6. Closure statement (ADR-0000 Rule 2(a), 2026-07-02 form)

**Invariant:** every assertion-act recorded as a belief carries a typed quantifier polarity
with that polarity's evidence obligation (universal ⇒ enumerated universe; observed
existential ⇒ resolvable witness), a typed basis with that basis's edge obligation (testimony
⇒ source FK; derived ⇒ non-empty premise set), is revisable only by its own holder through
uniform supersession, is contestable only cross-principal through a typed edge that demotes
both parties to visible doubt resolved by evidence class and never by recency, and is
creditable only through derived, never-stored views whose chains bottom out in witnessed
observation or in-force, undefeated non-belief rows.

**Quantification universe, enumerated:**

- *Axes:* holder (any registered principal, human or model, the maintainer included);
  polarity (universal | existential — total for assertion-acts; mixed beliefs decompose;
  normative/preference content excluded by construction — those are decisions); basis
  (observed | derived | testimony | assumed — instrument-mediated observation folds into
  observed-with-artifact-witness, named as folded); lifecycle (assert → supersede | contest |
  concur | credit | un-found); time (all views current-truth; **no as-of variant — named not
  covered**, pruned by the named-consumer test, §8.4; the existing `asof-export` surface is
  the natural later home if a consumer appears).
- *Sibling surfaces the same shape occurs on, disposed one by one:* review verdicts (staged
  second increment, obligation-rowed — §8.1/`belief-review-bridge`); s44 attestations
  (already typed; untouched); work-item close completion claims (a natural later consumer of
  `belief_universe` — named not covered); operator reports (remain prose; beliefs are the
  typed extract, entered by verb, never parsed from prose — §8.3); reader-side composed
  beliefs from honest reports (row 1890 — representable as derived beliefs, formation itself
  out of scope, §9); orchestrator operating assumptions (recordable as `basis='assumed'`,
  never credited; obligation to record governed by §4's answer).
- *Write surfaces:* the s43 boundary functions (covered — refusals journaled);
  owner/superuser direct DML (named not covered — the standing s26..s52 trust bound);
  pre-v2 v1 convention rows (covered at parse time only, named honestly, closed by v2).
- *Denomination:* bounds are closed vocabularies and existence-checked tokens, never numbers
  — evidence standing in the four-member basis order, corroboration in the three-member
  diversity vocabulary computed from `agent_class` (never witness COUNT — the attestation
  incident's exact lesson), independence disclosure in the review vocabulary. The one scalar
  (`confidence`) is pre-existing, three-valued, and read by no rule. Nothing here is
  denominated in a proxy unit; stated so the check is seen discharged, not skipped.

**Presumed too narrow, checked outward:** the polarity dichotomy was checked against the
consult's seven specimens plus row 1890's eighth (each classifies or decomposes); against
decisions (excluded, preference-acts) and reviews/attestations (classify as
universal-over-method / existential-about-a-row — the staged bridge's own typing). Named
residue, excluded with reasons in §8.3: probabilistic and temporal ("X until Y") propositions
do not classify cleanly.

## 7. Witness plan (per element; reported WITNESSED / REFUSED-AS-EXPECTED / UNEXERCISED per the standing contract)

**Shipped binding (ADR-0011's 2026-07-02 amendment, both legs mandatory):** every v2 fixture
writes through the s43 **boundary functions** — the shipped default write path — never a raw
INSERT; every gate is seen RED on the defect shape before its green is credited.

**7.1 v1 (scratch chains, engine-side):** a fixture corpus carrying — a well-formed row of
each polarity×basis cell that is legal (6 legal cells; the 2 illegal cells below); malformed
rows for each obligation: `universal` without `universe`, `existential observed` without
`witness`, `testimony` without `source`, `derived` without `premises`, dangling `row:` token,
self-contest, contest of a superseded target → each a typed `BeliefParseError` naming row and
obligation (REFUSED-AS-EXPECTED); a contest pair → both demoted in both producers; an
observed-vs-testimony contest → `contest_resolved` for the observed side; a three-holder
concurrence set spanning two agent classes → `corroboration_grade` reaches exactly
`corroborated-cross-class`, and a same-class pair reaches exactly `corroborated-same-class`
never higher; a five-belief derivation chain sharing one ancestor → `shared_ancestor`
non-empty (the five-layers query, seen answering *no independence*); the full differential in
AGREE (`./judge --layer belief` on the scratch target). Negative control for the layer
machinery: an incomplete stack list → `RegistryError` before grounding.

**7.2 v2 delta B1/B2 (scratch schema pairs in the toy db, full chain s15..s52 + family):**
each §3.1 CHECK and §3.2 trigger witnessed both polarities (illegal refused with taught text
AND journaled as `write_refused` through the boundary; legal sibling passes); hash-coverage
gate red on a columns-without-re-issue scratch, green on the head; kind-shape manifest green
with the +9 rows, red with one deliberately withheld (negative control); `ledger_current`
returns the new columns on fixture rows; supersession discipline: holder-revision passes,
cross-principal supersession refused, non-belief kind superseding a belief refused; the
defeat composition leg: a fixture where a belief's premise row is model-defeated →
the belief leaves `credited_beliefs` in BOTH producers, in AGREE; detect siblings t on the
family-shaped scratch, f on an s52-head scratch (both polarities, the s29/s30 precedent).

**7.3 v2 delta B3:** `disclosed-isolated-dispatch` accepted without a stamp gate
(the disclosure leg); `technical` claim under same-invocation stamps still refused
byte-identically (the untouched-gate leg, the re-issue's negative control); the five-member
CHECK refuses a sixth value.

**7.4 Obligation rows (§2.4):** witnessed at v1 ship by `led work list` output quoted in the
ship report (the rows exist, open, dependency-edged) — and the ship report cites their ids.

## 8. Deliberate exclusions — each staged item obligation-rowed, each dead exclusion reasoned

**8.1 Review-verdict bridging (Q5, SECOND increment; obligation `belief-review-bridge`,
§2.4).** Deriving testimony-basis beliefs from `attest`/`refuse` review rows in the EDB, so
CLEANs enter corroboration/shared-premise (a CLEAN is a universal claim over the method
actually run — specimens 1.2/1.6 become fully representable). Held back because it doubles
the first increment's blast radius across the review machinery; staged with a typed
obligation, not prose.

**8.2 The doubt tier + warrant-directed verification (row 1895; obligation
`belief-doubt-tier`, §2.4).** DECIDED: staged BEHIND v2, not in it. Reasoning on the record:
the doubt row's consumer is the ranked verification queue (warrant-directed verification —
staleness, testimony depth, same-class-only corroboration, universe-vs-consumption mismatch,
claimant-is-beneficiary), and that queue does not exist; minting the kind before its consumer
fails the named-consumer test (row 1906) on this spec's own design. v2 deliberately ships the
warrant *columns* the ranking will read (universe, basis, source, corroboration), so the
staged tier arrives on a substrate already carrying its inputs. The Goodhart guard (doubt
costs its author a typed reason naming a warrant column) is recorded here as the staged
design's fixed point.

**8.3 Excluded outright, no obligation (consult §6, adopted with this spec's confirmations):**
numeric degrees of belief (floats fight the closed-vocabulary discipline, the ASP layer, and
honesty — a 0.87 is a claim with no witness; also forecloses `belief`'s one bad connotation,
row 1894); modeling any principal's future assertions (authority does not interpolate);
nested doxastic logic beyond the one testimony edge; reinstatement on contest resolution
(s31's named future fork); prose harvesting (beliefs enter verb-coupled or not at all — a
harvested belief is a hand-maintained sentence wearing a schema); retroactive backfill (runs
are linear; old rows are dust); probabilistic/temporal propositions (do not classify under
the polarity dichotomy; excluded, named).

**8.4 Pruned by the named-consumer test (row 1906), stated as the rule requires:** an
**as-of belief view** (no nameable consumer; the axis is named not-covered in §6); a
**belief_history forensic view** (no consumer — if a study ever needs one it enters s31's
reader allowlist with a reason, per that delta's own discipline); a **stored warrant-score
column** (its consumer is the unbuilt doubt tier — the record waits for its consumer rather
than shipping ahead of it). Each of these was in early drafts of this spec and was deleted by
the test, which is the test working.

## 9. Honest limits

- The substrate types the *record* of belief, not belief itself: a principal can decline to
  record, record lazily, or enumerate a convenient universe. What the type buys is that these
  failures become visible and contestable on the row, not impossible (§3.2's review-only
  declaration). Row 1890's deepest half — belief formed in a reader's head from honest
  text — is representable only when someone writes it down; formation is not mechanizable.
- Contest/concurrence edges depend on principals noticing each other's beliefs; nothing
  auto-detects contrariety (no mechanism reads meaning — deliberate).
- Evidence-class precedence ranks bases, not quality within a basis: a weak observation
  outranks a strong derivation. Closed-vocabulary honesty; the doubt tier (§8.2) is the named
  future refinement, and the corroboration grade is the compensating signal in v2.
- The v1 window's obligations are parse-time; a malformed v1 belief sits in the ledger until
  read. Named, priced into Q4, closed by v2.
- Superuser/schema-owner direct DML bypasses everything — the standing s26..s52 trust bound.
- In a solo world, beliefs, contests, and concurrences are all written by machinery one
  operator controls: complete and attributed, not adversarially independent (s17's honesty).
- `disclosed-isolated-dispatch` is a disclosure, not a witnessed claim; promotion awaits a
  server-witnessed dispatch token that does not exist (§3.5).

## 10. Ratification questions (only where a genuine choice remains; the Q-series is resolved and not re-opened)

- **R1 — Q7's landing (§4).** Adopt O1+O6 (kernel opt-in; audit/review-class briefs require
  belief-shaped verdicts), with O4→O3 as the named escalation ladder? Sub-choice: O6 as
  practice (brief templates, this spec's default) or as law (a dated ADR amendment). *(adopt
  default | adopt with O6-as-law | pull O4 forward | opt-in only, no instrument mandate)*
- **R2 — the cross-principal supersession refusal (§3.2 item 4).** Spec-derived (the consult
  implied it via Q3 but never made it a refusal): a belief is superseded only by its holder,
  same kind; everyone else contests. The alternative — allowing a maintainer-class principal
  to retract another's belief directly — is rejected by this spec as recency-between-
  principals wearing authority's clothes, but the maintainer may want an authority escape
  hatch on the record. *(refuse, as specified | refuse with a maintainer-principal exception)*
- **R3 — the `belief_concurs` column (§3.1).** Spec-derived beyond the consult's column list,
  required so corroboration is computed from typed acts rather than statement-text matching.
  The lean alternative (drop it; corroboration by exact-normalized-statement match in the
  EDB) is cheaper and worse (paraphrase breaks it silently; ADR-0008). *(build, as specified
  | drop and text-match | drop corroboration from v2 entirely)*

## 11. Executor guidance

Sonnet executes v1 and, absent a contrary ruling at ratification, the v2 family, from this
spec once ratified (the standing delegation contract; the s40/s41 Fable-only ruling was
scoped to that family alone). Disregard any instructions to economize on time. Where this
spec fixes a choice (column set, CHECK truth tables, teach-text substance, view semantics,
layer stack, the B3 mechanism, slugs and titles of §2.4), the builder does not re-open it;
where the builder finds this spec wrong in the field, the disposition is ADR-0013's
renegotiation upward at the moment of discovery — never silent narrowing. Delta headers carry
the full house apparatus (WHY, PREREQUISITE, HISTORY per mechanism, closure-statement slice,
fail-safe classification — this family is within the class-ratified fail-safe SHAPE (adds
kinds, refusals, vocabulary, views; relaxes nothing) but routes on THIS spec's ratification,
never claimed under the class: it mints vocabulary the whole project will reason in, which is
exactly what ratification bandwidth is reserved for —, LIMITS, VALIDATE/REAL). Claims in the
build report per item: WITNESSED (with observed output), REFUSED-AS-EXPECTED, or UNEXERCISED
with the concrete blocker.

**Per-section confidence:** §1–§3.1 high (direct execution of resolved decisions on the
established idiom); §3.2 high, except the cross-principal supersession refusal (medium-high;
flagged as R2); §3.4 high on view semantics, medium on the exact floor-predicate grain (the
builder may split predicates for comparability without changing semantics, reporting the
split); §3.5 high on the disclosure value, medium on whether a witnessed dispatch token ever
arrives to promote it; §4 medium-high (a re-derivation, honestly a judgment — hence R1);
§6–§8 high.

---

*Fable-authored spec, 2026-07-22, fresh context. Not committed by its author (read-only
commission bound); ratification, and every act that follows it, is the maintainer's.*
