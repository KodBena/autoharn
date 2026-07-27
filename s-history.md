# s-history.md — what "s" means and what each `sNN` kernel delta did

This document answers two questions a reader of [`kernel/lineage/`](kernel/lineage/) hits
immediately and that no single file used to answer in one place: what does the `s` in
`sNN-schema.sql` / `sNN-<name>.sql` stand for, and — one line to one short paragraph each —
what did every delta from `s15` to the current lineage head actually add or change? It is a
narrative companion to [`kernel/lineage/README.md`](kernel/lineage/README.md) (the operational
apply-order document), not a replacement for it, and it is **not** the source of truth for
apply order — see "Staying current," below, for why.

## What "s" stands for

**Working reading (not confirmed verbatim on the record): `s` = "schema."** Every delta file in
this lineage is named `sNN-schema.sql` (the standalone generations, `s10` through `s15`) or
`sNN-<description>.sql` (the additive deltas from `s17` onward) — the letter is the literal
first word of the original file-naming convention, "schema." This reading is corroborated by
the fact that the prefix already existed, unchanged, in the predecessor codebase this project
was consolidated from: the commit that first migrated this lineage into this repository
(`ecbc2a3`, "consolidation: stores + kernel lineage (Step 5)") shows the files arriving already
named `sNN-schema.sql`, and cross-references inside this repository's own documentation
([`tools/experiments/results/table_broadcast.out.txt`](tools/experiments/results/table_broadcast.out.txt):617-628;
[`judgment/engine/engine-frontier-semantics-SEED.md`](judgment/engine/engine-frontier-semantics-SEED.md):24-25)
point at the predecessor repository's own paths, e.g.
`epistemic-operator/harness/e13-build/s13-schema.sql`. In the predecessor repository the
numbering wrapping each schema file (`sNN`) was **already independent of** the experiment/build
directory numbering that contained it (`eNN-build/`) — for example
[`provenance/migration_manifest.tsv`](provenance/migration_manifest.tsv):309-310 records
`harness/e10-build/s11-schema.sql` and
`harness/e11-build/s12-schema.sql`, an off-by-one mismatch between the two numbering families
that only makes sense if `s` names the SCHEMA GENERATION, a sequence of its own, not the
experiment/build (`e`) that happened to introduce it.

**A second, weaker candidate reading exists and is disclosed rather than suppressed:**
`kernel/lineage/s15-schema.sql`'s own header opens "s15 — the SUBJECT decision-ledger kernel"
and [`provenance/LAYOUT.md`](provenance/LAYOUT.md):32 glosses `kernel` itself as "the subject-side decision-ledger
schema family (s10…s18)" — so a reader could plausibly guess `s` = "subject" (the kernel
governs the **subject** under study, as opposed to the harness/operator apparatus around it).
Weighed against the "schema" reading, this is weaker for two reasons: (1) `s15-schema.sql`'s
own header explicitly calls `s15` "the OPERATOR-side name ONLY; it appears in NO
subject-visible byte" — the ordinal itself is described as apparatus/operator naming, not a
subject-facing label, which cuts against reading the letter as an abbreviation of "subject";
and (2) no commit message, README, or design document this search covered states the expansion
in so many words ("s stands for X") for either candidate. **The expansion is not on the
record; the working reading adopted here is "schema," on the strength of the literal filename
convention and the independent e/s numbering found in the predecessor repository's own
manifest — an honest unknown, not a confirmed fact.**

## Per-delta synopsis, `s15` through the current lineage head

Each entry below is sourced from that delta file's own header comment (DOC-SOURCED), compressed
to plain words. `ls kernel/lineage/s*.sql` is the authoritative roster of what exists; this list
was checked against it directly rather than assumed. Every synopsis links to its file. The
pre-`s15` standalone generations (`s10`–`s14`, plus the `s13` remediation file) are deliberately
outside this synopsis's frame — superseded whole-kernel snapshots, not chain deltas; see
[`kernel/lineage/README.md`](kernel/lineage/README.md) for their coverage.

### The `s15`/`s17`/`s18` base and its one-shot apply script

- **[`s15-schema.sql`](kernel/lineage/s15-schema.sql)** — the current STANDALONE generation: the
  `s13` kernel unchanged in semantics, plus one ratified addition this delta's own header calls
  "Ruling A" (its name for the decision, not linked or defined anywhere else in this
  repository's tracked history) — a typed `antecedent` column on `review_detail` so an
  affirmation-as-review gets its own typed place instead of being carried in prose. Deployed
  into a freshly isolated, opaquely-named database so a role connected to it cannot read the
  surrounding apparatus catalog.
- **[`s17-stamp-mechanism.sql`](kernel/lineage/s17-stamp-mechanism.sql)** — an additive delta on
  top of `s15` adding **interception-stamped row provenance**: every write is bound to the
  actual invoking session/agent identity (an HMAC injected by a tool-interception hook, not
  typed by the writer), closing the gap where a writer-supplied `actor` field alone let one
  context register a second "reviewer" [principal](GLOSSARY.md#principal) (the kernel's
  registered identity/actor concept — see the glossary entry) and countersign its own work.
- **[`s17-independence-vocabulary.sql`](kernel/lineage/s17-independence-vocabulary.sql)** —
  lands the same day as the delta above: adds `self-review` as an honest value of the
  `independence` column, and makes the independence-CLAIMING values (`technical`/`managerial`/
  `financial`) require a stamp-DISTINCT invocation once stamps exist — landing the vocabulary
  and the distinctness gate in the same stroke.
- **[`s18-criterion-principals.sql`](kernel/lineage/s18-criterion-principals.sql)** — adds two
  genuinely distinct, INSERT-only criterion-reviewer principals (no `SELECT` on the unit
  ledger — the study-harness's own review-record table, distinct from the kernel's main
  ledger) so a first-contact review of a final artifact is enforced by database privilege, not
  by an honor system. This is the project's own study-harness apparatus, not part of the kernel
  a downstream user stands up — `high_watermark_1.sql` (below) deliberately excludes it.
- **[`high_watermark_1.sql`](kernel/lineage/high_watermark_1.sql)** — a convenience apply
  script only, owning no DDL of its own: it `\ir`-chains `s15 → s17-stamp-mechanism →
  s17-independence-vocabulary → s19` (deliberately skipping `s18`, the study apparatus above).
  It is the s19-era BASE, not "the current kernel" — a later delta lands as a new `sNN` file
  plus, in principle, a new `high_watermark_N.sql` (none has been cut since).

**There is no `s16`.** No file, commit, or cross-reference in this repository's history names
one; [GLOSSARY.md's own "birth chain" entry](GLOSSARY.md#birth-chain) already states this
plainly, and the numbering simply resumes at `s17`.

### `s19` – `s39`: foundational refusals, work-item tracking, and the tamper-evident chain

- **[`s19-trigger-search-path.sql`](kernel/lineage/s19-trigger-search-path.sql)** — forecloses a
  class of three findings (16, 37, 45 — this delta's own internal numbering for prior review
  findings that motivated it; not otherwise indexed in this repository's tracked history):
  `s15`'s `set_actor()` trigger read the kernel schema via
  a hardcoded literal `kernel.` instead of the parameterized schema, so any deployment whose
  kernel schema is not literally named `kernel` silently failed to attribute writes. Fixed
  structurally (every trigger/function now resolves kernel objects via `search_path`), not
  patched case by case.
- **[`s20-obligation-grants-and-view-refresh.sql`](kernel/lineage/s20-obligation-grants-and-view-refresh.sql)**
  — closes two defects found by a full-surface exercise: the subject was never granted access
  to the `countersign_obligation` table its own design says it should reach for, and two
  `SELECT l.*`-style views had gone stale because Postgres freezes a view's column list at
  `CREATE` time, so `s17`'s new stamp columns never reached them.
- **[`s21-session-aware-distinctness.sql`](kernel/lineage/s21-session-aware-distinctness.sql)**
  — fixes independence-checking being session-blind: two DIFFERENT interactive sessions' main
  threads were indistinguishable by `stamp_agent` alone, so a genuinely independent second-
  session review could be wrongly refused as "same invocation." Distinctness is now keyed on
  the PAIR `(stamp_session, stamp_agent)`.
- **[`s22-work-item-ledger.sql`](kernel/lineage/s22-work-item-ledger.sql)** — makes work-item
  state a ledger-derived fact instead of a manually tracked chore: five new columns plus four
  new `kind` values (`work_opened`/`work_claimed`/`work_depends_on`/`work_closed`) on the
  existing ledger table, with derived state living only in new views — no new base table.
- **[`s23-per-invocation-stamp-token.sql`](kernel/lineage/s23-per-invocation-stamp-token.sql)**
  — adds a sixth stamp column, `stamp_invocation`, a per-Bash-invocation UUID correlating a
  ledger row to the actual tool call that wrote it, closing the gap where nothing distinguished
  honest rapid-fire writes from a batch backfill after the fact. Capture-only: it feeds no
  verification logic itself.
- **[`s24-declared-event-time.sql`](kernel/lineage/s24-declared-event-time.sql)** — adds a
  nullable `event_declared_ts` column any writer may optionally set, distinct from the
  database's own insert time, so a genuinely late entry can be legally DECLARED as such (the
  paper-trail convention of the late-entry design), rather than looking indistinguishable from
  undeclared backfill.
- **[`s25-commission-kind.sql`](kernel/lineage/s25-commission-kind.sql)** — adds `'commission'`
  to the ledger's `kind` vocabulary, so the verbatim task text a session receives can be written
  as its own first-class, append-only row and later cited by whatever work it produced, instead
  of surviving only as reviewer paraphrase.
- **[`s26-row-hash-chain.sql`](kernel/lineage/s26-row-hash-chain.sql)** — the kernel half of the
  anchored ledger: every row's `row_hash` commits to its own content and to the immediately
  preceding row's hash, so retroactively altering, deleting, or reordering any historical row is
  detectable by anyone who re-walks the chain, without trusting the database itself.
- **[`s27-chain-high-water.sql`](kernel/lineage/s27-chain-high-water.sql)** — closes a gap `s26`
  itself is structurally blind to: deleting the highest-id row leaves the chain looking intact
  (a "truncation attack" in the tamper-evident-log literature). Adds a monotonic witness of how
  far the chain has reached, held outside the audited table, so a truncation cannot roll it
  back unnoticed.
- **[`s28-work-parent-edge.sql`](kernel/lineage/s28-work-parent-edge.sql)** — adds a typed
  parent-item edge (`work_parent`, naming the antecedent by slug) so task decomposition, until
  now expressible only as free-text `--refs` prose, becomes a real structure a rollup can join
  against.
- **[`s29-obligation-item-key-and-typed-close.sql`](kernel/lineage/s29-obligation-item-key-and-typed-close.sql)**
  — re-keys review obligations by WORK ITEM instead of by actor, adds a typed close mechanism,
  and guarantees an obligation tree — closing three witnessed failure modes where actor-keyed
  debt survived a close, a second identity distinct in id but not independence was invented to
  discharge it, or an agent, blocked by the debt, escalated to deleting obligation rows outright.
- **[`s30-typed-dependency-edges.sql`](kernel/lineage/s30-typed-dependency-edges.sql)** — types
  the `work_depends_on` edge with an `edge_type` (initially `blocks-close`), letting a
  dependency edge carry a real semantic beyond bare "informs" citation.
- **[`s31-supersession-uniform-retraction.sql`](kernel/lineage/s31-supersession-uniform-retraction.sql)**
  — re-issues four current-truth readers that had been reading raw `ledger` instead of the
  kernel's own "un-superseded reading" home (`ledger_current`), a pure refactor with witnessed
  output equality.
- **[`s32-edge-views-single-home.sql`](kernel/lineage/s32-edge-views-single-home.sql)** — a
  further pure refactor: named edge/discharge views become the ONE home for a morphism that had
  been hand-re-instantiated, with prose-only coherence, in every prior delta that touched it.
- **[`s33-composite-discharge.sql`](kernel/lineage/s33-composite-discharge.sql)** — adds an
  opt-in `work_discharge` column so a parent work item whose entire deliverable IS its children
  can close automatically instead of requiring a hand-written close that restates what the
  ledger already knows.
- **[`s34-computed-grade-refusal.sql`](kernel/lineage/s34-computed-grade-refusal.sql)** — adds
  one refusal: a writer can no longer supply `discharge_grade` directly; it must be computed,
  closing a gap where the column was documented as computed-only but nothing actually enforced
  that.
- **[`s35-validation-decomposition.sql`](kernel/lineage/s35-validation-decomposition.sql)** — a
  pure refactor of the single accreting `validate_work_item()` trigger function into a
  dispatcher plus four leaves, so future deltas extend one small leaf instead of re-copying an
  ever-growing monolith by hand.
- **[`s36-decision-grade.sql`](kernel/lineage/s36-decision-grade.sql)** — adds a nullable
  `decision_grade` column (and one derived view) so a standing decision can carry a graded
  quality mark that survives context loss, without touching any existing row.
- **[`s37-violation-disposition.sql`](kernel/lineage/s37-violation-disposition.sql)** — adds a
  typed way to dispose of a named violation (rather than letting it sit as eternal debt), and
  its v3 amendment fixes a mixed-timeline bug: the debt-facing projection now quantifies over
  in-force rows only, while the historical-record projection quantifies over everything, forever.
- **[`s38-bookkeeping-close.sql`](kernel/lineage/s38-bookkeeping-close.sql)** — adds a third,
  machine-verified way to close a work item's review requirement: a git-commit witness, checked
  for existence at construction time, as a judgment-free escape hatch whose use is permanently
  auditable via a new record view.
- **[`s39-blocks-start.sql`](kernel/lineage/s39-blocks-start.sql)** — the maintainer's own
  commission: a third dependency-edge value, `blocks-start`, plus a claim-time refusal, so a
  work item cannot be opened/claimed until its named precondition is actually met — structurally
  foreclosing dependency violations rather than relying on an agent noticing them.

### `s40` – `s50`: principal identity, hash coverage, and refusal recording

- **[`s40-principal-identity-events.sql`](kernel/lineage/s40-principal-identity-events.sql)** —
  makes identity itself a typed, append-only ledger fact: registration, standing, and two more
  event kinds, deriving `principal_standing` and converting `principal_role` from a table into
  a view over those events, so no identity-adjacent fact can be silently mutated in place.
- **[`s41-principal-bindings-and-relations.sql`](kernel/lineage/s41-principal-bindings-and-relations.sql)**
  — the second half of the same family: typed bindings a registered identity can carry (role
  binds, cryptographic key-binding slots, competence grants, and typed relations to other
  principals such as `acts-for`, one principal authorizing another to act in its stead, and
  `dispatched-by`, one principal marking another as the one who dispatched it), all retracted
  uniformly through `s31`'s own supersession mechanism rather than a second retraction shape.
- **[`s42-row-hash-full-coverage.sql`](kernel/lineage/s42-row-hash-full-coverage.sql)** —
  re-issues `compute_row_hash` so the tamper-evidence chain serializes EVERY ledger column
  except the hash itself, closing a gap where 22 columns added since `s26` sat outside the
  chain's own coverage.
- **[`s43-typed-verdict-write-boundary.sql`](kernel/lineage/s43-typed-verdict-write-boundary.sql)**
  — a structural rework: direct `INSERT` is revoked entirely, and four `SECURITY DEFINER`
  functions become the only write path, so that a refused write — previously a plain aborted
  transaction with no trace — is itself journaled as a committed, typed `write_refused` row.
- **[`s44-model-identity-attestation.sql`](kernel/lineage/s44-model-identity-attestation.sql)**
  — adds a typed way to attest which model actually served a given session (closed grade/
  verdict vocabularies, a self-referencing existence check), feeding the OpenTelemetry
  (OTel)-based sentry that watches for one model silently substituting for another mid-session.
- **[`s46-credited-views.sql`](kernel/lineage/s46-credited-views.sql)** — adds a display layer
  (`model_defeated_rows`, `credited_current`) surfacing which rows the
  [defeat calculus](GLOSSARY.md#model-defeated) treats
  as discredited, purely additive derived views.
- **[`s47-claim-on-closed-refusal.sql`](kernel/lineage/s47-claim-on-closed-refusal.sql)** —
  one new refusal: a work item cannot be claimed once its slug already carries an in-force
  close, a precondition `s39` never asked because it was never on that delta's own commission.
- **[`s48-review-witness-existence.sql`](kernel/lineage/s48-review-witness-existence.sql)** —
  a `row:<id>` review-witness citation on a close is now checked for existence at write time,
  instead of being free text that could name a row that never existed.
- **[`s49-journaler-overflow-guard.sql`](kernel/lineage/s49-journaler-overflow-guard.sql)** —
  fixes the refusal-recorder itself being defeatable: an over-sized numeral in an attempted
  actor string used to abort the write-refusal journaling that was supposed to record it; now
  it journals with a NULL attempted-id instead of aborting.
- **[`s50-defeat-input-raw-domain.sql`](kernel/lineage/s50-defeat-input-raw-domain.sql)** —
  re-points `s46`'s defeat-input exclusion to read raw history instead of `ledger_current`,
  matching the domain the ASP (Answer Set Programming, the clingo-based logic layer)/SQL
  defeat-calculus engine itself already used, closing a named
  (not silently discovered) divergence between the kernel view and the engine.

*(`s45-standing-lifecycle.sql` sits between `s44` and `s46` in the applied chain; it licenses
`principal_binding_active` on standing-declaration/suspension events and re-issues the standing
functions with an in-force filter so a suspension lift is observable — see
[`kernel/lineage/s45-standing-lifecycle.sql`](kernel/lineage/s45-standing-lifecycle.sql)'s own
header for the full account.)*

### `s51` – `s59`: artifact custody and the belief/missive substrates

- **[`s51-artifact-store.sql`](kernel/lineage/s51-artifact-store.sql)** — adds
  content-addressed, append-only custody (`kernel.artifact`) for bytes a ledger row's
  evidentiary force relies on (charters, commission texts, ratified specs), so the database
  becomes primary custody for the project's own essential records instead of merely hashing an
  external referent it does not hold.
- **[`s52-artifact-witness-check.sql`](kernel/lineage/s52-artifact-witness-check.sql)** —
  extends `s48`'s existence check to the `artifact:<hash>` witness form, so a close can no
  longer cite bytes the store never actually received.
- **[`s53-belief-substrate.sql`](kernel/lineage/s53-belief-substrate.sql)** — adds a typed
  `belief` kind: an assertion-act with a typed quantifier, evidence obligation, basis, and
  holder-relation, so a confident claim can be represented ON the record as a belief instead of
  operating on the project invisibly.
- **[`s54-belief-views.sql`](kernel/lineage/s54-belief-views.sql)** — the read surface for the
  belief substrate above: what currently stands as belief, contested beliefs, credited beliefs,
  corroboration, and shared premises — all computed fresh, nothing additionally stored.
- **[`s55-dispatch-grain-independence.sql`](kernel/lineage/s55-dispatch-grain-independence.sql)**
  — adds one more honest independence value, `disclosed-isolated-dispatch`, for the case where
  an isolated sub-dispatch's verdict is relayed by the orchestrator's own writing invocation —
  previously representable only as lossy `self-review` plus prose.
- **[`s56-reservation-residue.sql`](kernel/lineage/s56-reservation-residue.sql)** — widens the
  discharge view to also recognize a "reviewed with reservations" verdict, closing a gap where a
  genuinely performed, distinct-actor review that disclosed concerns looked identical to an item
  nobody reviewed at all.
- **[`s57-obligation-revocation-event.sql`](kernel/lineage/s57-obligation-revocation-event.sql)**
  — replaces the kernel's last raw, privilege-gated `DELETE` (revoking an obligation) with a
  typed, auditable event, so a revocation leaves a record instead of leaving no trace at all.
- **[`s58-missive-substrate.sql`](kernel/lineage/s58-missive-substrate.sql)** — adds a typed
  inter-world/inter-principal messaging substrate (`missive_sent`/`missive_received`/
  `missive_disposed`, ten typed envelope columns, a one-row `kernel.world_identity` table) — the
  wire envelope itself becomes the row shape rather than opaque payload prose.
- **[`s59-missive-views.sql`](kernel/lineage/s59-missive-views.sql)** — the read surface for the
  missive substrate above: six new views (outbound, receipts, undisposed, stale, delivery audit,
  open threads).

### `s60` – `s67`: entitlement, signatures, delegation, and journal totality

- **[`s60-entitlement-enforcement.sql`](kernel/lineage/s60-entitlement-enforcement.sql)** —
  adds the kernel's first true authorization layer: an `entitlement_act_class` column and a new
  trigger member that refuses an act unless the writer's own role/delegation chain roots at
  **genesis** (this delta's own term for the world's first-ever registered principal, the one
  identity every delegation chain must trace back to) for that act's class — fail-safe-additive,
  only new refusals.
- **[`s61-signature-symmetry-and-key-binding.sql`](kernel/lineage/s61-signature-symmetry-and-key-binding.sql)**
  — adds signed-commission/signature event kinds, symmetric signed-supersession, and
  proof-of-possession verification against `s41`'s key-binding slot, so a signature can be
  checked, not merely recorded.
- **[`s62-delegation-lifecycle-gating.sql`](kernel/lineage/s62-delegation-lifecycle-gating.sql)**
  — closes a self-servable-chain hole `s60` itself left open and its own remedy text
  inadvertently taught: asserting or superseding an `acts-for` delegation edge is now itself an
  authority-bearing act requiring a chain to genesis, so a principal refused for lacking
  authority can no longer simply write themselves a new delegation edge and retry.
- **[`s63-supersession-body-restoration.sql`](kernel/lineage/s63-supersession-body-restoration.sql)**
  — repairs an authoring accident: `s61`'s re-issue of a shared trigger function cited a stale
  base and silently deleted four refusal branches `s53`/`s58` had put there; this delta restores
  them verbatim, returning the kernel to what was already ratified (no new permission).
- **[`s64-principal-stamps-delegation-conditions.sql`](kernel/lineage/s64-principal-stamps-delegation-conditions.sql)**
  — adds conditions a delegation edge can carry (redelegation depth, mandatory countersign,
  expiry, scope) and closes a hazard found while building this: `dispatched-by` edges had been
  entirely ungated by entitlement until this same delta widened the enforcement functions to
  cover them too.
- **[`s65-refusal-attempted-kind.sql`](kernel/lineage/s65-refusal-attempted-kind.sql)** — adds
  `refusal_attempted_kind`, extracting the refused payload's own `kind` token (bounded at 256
  bytes) into the refusal journal, so a refused write's own attempted vocabulary member is
  legible without a multi-agent interrogation to reconstruct it (this bullet, and the two below,
  fill a gap this file's own directory listing left when `s65` first landed — this document's
  own "Staying current" warning below applies).
- **[`s66-forged-stamp-journal-totality.sql`](kernel/lineage/s66-forged-stamp-journal-totality.sql)**
  — closes a witnessed escape: a structurally-complete-but-cryptographically-wrong vendor stamp
  used to raise as an unhandled error instead of returning a typed refusal (the journaler's own
  INSERT re-fired `set_stamp` on the same forged session GUCs — the Postgres config variables
  the tool interception injects to carry the stamp — and the second raise escaped the boundary
  function's own exception handler with no refusal ever recorded). `set_stamp` gains one
  guard: the journaler's own `write_refused` row records `stamp_verified := false` instead
  of raising a second time — every other kind's
  behavior, including the raise text, stays byte-identical.
- **[`s67-refusal-digest-bound.sql`](kernel/lineage/s67-refusal-digest-bound.sql)** — bounds the
  refusal journal's own payload digest at 1,048,576 bytes (the `s51` `artifact_too_large`
  figure): a direct-psql caller bypassing the service's own body-size cap could otherwise make
  the journaler digest an unbounded payload on every refusal; over the bound,
  `refusal_payload_digest` records NULL (a grep handle lost, never the refusal record itself,
  which journals in full regardless of payload size) — the same one-way "legitimately NULL
  beyond a named bound" idiom `s65` already uses for `refusal_attempted_kind`.

## Birth-selection: does choosing scaffold capabilities prune this chain?

**No. Verified: the full chain always applies; [the scaffold](GLOSSARY.md#the-scaffold)'s
options shape only the surrounding birth ACTS, never which `sNN` deltas a new
[world](GLOSSARY.md#world)'s kernel carries.**

- [`bootstrap/new-project.sh`](bootstrap/new-project.sh) computes a single boolean,
  `FULL_LINEAGE`, set to `1` for BOTH `--new-world` and `--profile tracker`
  ([`bootstrap/new-project.sh`](bootstrap/new-project.sh):478-480: `FULL_LINEAGE=0`;
  `[ -n "$NEW_WORLD" ] && FULL_LINEAGE=1`; `[ "$PROFILE" = "tracker" ] && FULL_LINEAGE=1`). Every
  other flag the script accepts (`--schema`/`--kern`/`--role` overrides, `--governed`, `--force`,
  `--pin`) is orthogonal to this boolean — none of them appears in its computation.
- When `FULL_LINEAGE` is 1, the script's own `LINEAGE_CHAIN` variable is set to ONE fixed
  string ([`bootstrap/new-project.sh`](bootstrap/new-project.sh):506) enumerating `s15` through
  the current head (`s67` as of this writing) — the identical list regardless of which
  `--new-world` name, `--profile tracker` name, or any feature checkbox was chosen. There is no
  conditional branch inside that assignment keyed on any user-selected option.
- Precision added 2026-07-27 (content-review finding): `LINEAGE_CHAIN` is the hand-authored
  NARRATIVE of the chain, used for the printed provenance header — the code that actually
  decides which files apply is a separate, GENERATED loop
  ([`bootstrap/new-project.sh`](bootstrap/new-project.sh) ~lines 888-935, "THE APPLY LIST IS
  GENERATED, not hand-typed") that globs `kernel/lineage/s[0-9]*-*.sql` live, unconditioned
  on any option. The two are mechanically held together by
  [`gates/lineage_chain_coverage.py`](gates/lineage_chain_coverage.py), which fails the
  commit if the narrative and the directory diverge — so quoting either is safe, and the
  no-selection conclusion above rests on the generated loop, not the narrative string.
- The scaffold's separate, declarative **feature manifest** (`features.json`, produced by
  [`tools/setup_tui/steps_features.py`](tools/setup_tui/steps_features.py)) governs five
  unrelated axes — `portable_adrs`, `vendored_skills`, `panel_extension`, `makespan_tier`,
  `principal_set` — none of which is a kernel delta or touches which `sNN` files apply
  ([`tools/setup_tui/steps_features.py`](tools/setup_tui/steps_features.py):39-66, each field's
  own docstring names its effect: which docs get vendored, whether a panel submodule gets
  cloned, a declarative resource-tier note, and which EXTRA principals get registered on top of
  the **birth acts** below — the concrete rows/ceremonies a scaffold run writes at world-birth
  time, e.g. principal registration, standing declarations, role binds — never a delta
  selection).
- The one CONDITIONAL this search found is not a capability toggle at all: it is a **defensive
  runtime check**, inside the birth sequence (the ordered set of birth acts a scaffold run
  performs), for whether the schema actually being scaffolded carries `s60`.
  [`bootstrap/new-project.sh`](bootstrap/new-project.sh):1159 runs
  `SELECT count(*) FROM information_schema.columns WHERE ... column_name =
  'entitlement_act_class'` (the marker column `s60` adds) and, if absent, prints `"s60 birth
  sequence SKIPPED"` ([`bootstrap/new-project.sh`](bootstrap/new-project.sh):1162) and omits the
  two OPTIONAL role-bind/entitlement-config birth acts that only make sense once `s60` exists.
  This is a guard against the script being pointed at a schema whose lineage predates `s60`
  (e.g. an older `--schema`/`--kern`/`--role` override reused against a pre-`s60` deployment) —
  it does not prune `s60` from a fresh `--new-world`/`--profile tracker` run's own
  `LINEAGE_CHAIN`, which unconditionally includes it.
- The classic mode (neither `--new-world` nor `--profile tracker` given) applies **no kernel
  lineage at all** — `LINEAGE_CHAIN` is set to the literal string `"NOT applied by this scaffold
  run"` ([`bootstrap/new-project.sh`](bootstrap/new-project.sh):531), and the operator is told to
  apply a lineage to an existing schema by hand. This is not a partial-selection mode either: it
  is the direct, classic `--schema`/`--kern`/`--role` path onto a pre-existing kernel, orthogonal
  to the capability-selection question.

**In one sentence: every scaffold option shapes WHAT GETS WRITTEN AT BIRTH (which principals
are pre-registered, which docs are vendored, which optional birth-time role-bind/config acts
run) — none of them prunes or selects which `sNN` kernel deltas the new world's schema carries;
that chain is one fixed list, applied in full, every time a governed world is born.**

## Staying current (a warning this document does not want to repeat)

[`kernel/lineage/README.md`](kernel/lineage/README.md) already records, twice, that a
hand-copied enumeration of the lineage chain drifted stale within one day of being written.
This document is a **narrative, point-in-time synopsis** — useful for understanding what each
delta did and why, not for determining what a fresh world's kernel currently contains. For that
question, the living source is always the directory itself (`ls kernel/lineage/s*.sql` — the
generated apply loop in [`bootstrap/new-project.sh`](bootstrap/new-project.sh) globs exactly
this, and its hand-authored `LINEAGE_CHAIN` narrative is gate-held to match it). A
future delta should be added here as its own bullet in the appropriate range (opening a new
range heading once a decade's worth accumulates), never by silently letting this file fall
behind — but if it does fall behind, the file to trust is the one named in this paragraph, not
this one.
