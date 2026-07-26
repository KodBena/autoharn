#!/usr/bin/env python3
"""kind_shape_manifest_gate -- MANIFEST + GATE for the kernel ledger's kind-scoped shape
invariants (ledger item `kind-shape-manifest-gate`, per
vestigial_documentation/design/ORCH-CATEGORICAL-REFACTOR-CONSULT-2026-07-15.md finding F5 / plan step 6).

WHAT THIS IS. `kernel/lineage/*.sql` re-authors, by hand, per delta, the correlation between
`ledger.kind` and a payload column that only means something for that kind (F5: "the ledger row
as a sum type over kinds"). Ten-plus such CHECKs exist today, split between a TWO-WAY iff
(`(kind = 'X') = (col IS NOT NULL)`, s22's `work_slug_kind_shape`/`work_title_kind_shape`/
`work_resolution_kind_shape`) and a ONE-WAY implication (`col IS NULL OR kind = 'X'`, s22's
`work_witness_kind_shape`, s28's `work_parent_kind_shape`, s30's `edge_type_kind_shape`). The
split is NOT accidental -- s28's own header names "nullable-legal-roots" (a root item legitimately
has kind='work_opened' with work_parent NULL, so the correlation cannot be an iff), and s30's own
header names append-only history (a two-way CHECK would fail ADD CONSTRAINT's whole-table
validation against pre-existing rows a backfill can never touch). F5's own verdict: "do not
uniformize the shapes; state the (kind, column, arity) table once as a manifest and gate the
catalog against it."

TWO COLUMNS ARE LICENSED BUT NOT CHECK-ENFORCED (a real wrinkle this sweep found, named rather
than smoothed over -- CLAUDE.md's hazard-flagging duty): `regards` (s15) and
`work_review_disposition` (s29, the sec-10 epoch amendment) are BOTH genuinely kind-scoped
two-way correlations that CANNOT be expressed as a plain CHECK -- `regards` because
`validate_review()` must look up an EARLIER row's actor (a self-referencing lookup no CHECK can
perform), `work_review_disposition` because its correlation became EPOCH-GATED and a CHECK cannot
consult `migration_epoch`, a different table. Both are enforced by a BEFORE INSERT trigger
instead. The manifest below records this as a distinct `mechanism` value ("trigger") rather than
silently dropping the columns or silently demanding a CHECK that cannot exist -- the variance is
load-bearing, per F5, and this is another instance of it, one level down from arity.

MANIFEST SCOPE: `kernel/lineage/ledger`'s columns only. `review_detail` carries CHECKs of its own
(`discharge_grade_check`, `review_detail_independence_check`, `review_detail_verdict_check`) but
that table has no `kind` column -- nothing on it is "kind-scoped" in F5's sense, confirmed by
reading `kernel/lineage/s13-schema.sql`'s `review_detail` DDL and s29's `discharge_grade` add.
Every OTHER ledger column not appearing in MANIFEST below is CORE (structural, present or legal
on every row regardless of `kind` -- id/ts/session/kind/statement/... /row_hash, see
CORE_COLUMNS) -- `amends`/`amends_scope`/`answers` were checked against their own write-boundary
triggers (`validate_amends`/`validate_answers` in s15-schema.sql) and confirmed NOT kind-scoped
(any kind may amend or answer; the constraint is "must resolve to an earlier own-session row",
never a kind test).

CLOSURE STATEMENT (ADR-0000 Rule 2a):
  - INVARIANT: every ledger column that is NOT in CORE_COLUMNS carries EXACTLY its MANIFEST-
    declared (kinds, arity, mechanism) shape in the live catalog (for mechanism="CHECK": a
    `pg_constraint` CHECK definition that parses to that exact (column, kinds, arity); for
    mechanism="trigger": NO catalog CHECK ties the column to `kind` at all -- the correlation
    lives only in the named trigger function, exactly as documented). A column carrying neither
    a matching CHECK nor a MANIFEST "trigger" declaration is an UNLICENSED PAYLOAD COLUMN,
    refused.
  - QUANTIFICATION UNIVERSE: every column of `<schema>.ledger` in a live catalog produced by
    applying the FULL current birth chain (`high_watermark_1.sql` through
    `s37-violation-disposition.sql`, `bootstrap/new-project.sh`'s own `LINEAGE_CHAIN` order,
    mirroring how `gates/ledger_reader_allowlist.py`'s own CHAIN was extended in this same
    branch) -- not a fixture, not memory of an earlier sweep. STALENESS NOTE: this gate's CHAIN
    stopped at s30 from s30's own delta onward -- s31 through s36 never reached it either, only
    surfaced when s37 (which widens two ALREADY-MANIFESTed columns, work_resolution and
    work_review_ref, to also license its own new kind) made the gap visible. Extended through
    the FULL chain to s37 here, not merely the s37 hop, closing the whole gap at once. Every
    kind-mentioning CHECK on `ledger` is
    parsed generically (regex over `pg_get_constraintdef` output, not a name allowlist), so a
    NEW kind-shape CHECK a future delta adds is caught by this gate on its own shape, not only by
    name collision with something already in MANIFEST. Sibling surface swept and confirmed empty:
    no OTHER table in the chain (`kernel.principal`, `kernel.principal_role`,
    `countersign_obligation`, `kernel.stamp_secret`, `kernel.migration_epoch`,
    `kernel.chain_genesis`, `kernel.chain_high_water`) carries a `kind` column at all.
  - DENOMINATION: the resource is "a (column, catalog-shape) pair", never a proxy (not a
    constraint count, not a table size) -- one violation named per column.

NOT IN SCOPE (deliberately, named per F5's "the variance is load-bearing" instruction, never
silently uniformized): the DEFAULT-then-CHECK ordering inside `validate_work_item()` (plan step
7's own concern); the .lp engine side's kind-tagged predicates (plan step 4/8, a different
producer); WHICH kind values are legal at all (`ledger_kind_check` -- a vocabulary CHECK, not a
shape CHECK, carries no `IS NULL`/`IS NOT NULL` correlate and is correctly parsed-and-skipped by
`_classify_kind_shape` below); WHICH VALUES a column may take PER KIND, once that column's own
(kind, arity) shape is already MANIFEST-declared (s37's `work_resolution_check`, witnessed live
when the CHAIN below was extended through s37: it widens to `work_resolution IS NULL OR (kind =
'work_closed' AND work_resolution = ANY(...)) OR (kind = 'work_violation_disposition' AND
work_resolution = ANY(...))` -- a VALUE-VOCABULARY CHECK partitioned by kind, one level below the
(kind, column, arity) SHAPE `work_resolution_kind_shape` already covers for the SAME column, not
a second, competing shape declaration for it. Recognized and skipped generically by
`classify_kind_shape` below via `_VOCAB_PARTITION_RE` -- matched on the CHECK's own textual shape
(a `kind = '<literal>'` branch AND-combined with a `col = ANY(...)` membership test), never by
constraint name, so a future column's own kind-partitioned vocabulary CHECK is caught by the same
generic test).

IN SCOPE, a THIRD manifest (added by the s38 fixpoint-review repair, 2026-07-17, alongside
MANIFEST and CORE_COLUMNS above): PARTIAL-VALUE kind-shape CHECKs, the idiom `<col> IS DISTINCT
FROM '<literal>' OR kind = '<K>'` (s38's `work_review_bookkeeping_kind_shape`, the first live
instance). This is genuinely a (kind, column)-correlation in F5's sense -- it answers "which kind
is this ONE value of the column legal on" -- but at single-value granularity below a whole-column
(kind, arity) SHAPE row, so it is tracked in its OWN manifest, `VALUE_PARTITION_MANIFEST`, keyed by
(column, value), never folded into MANIFEST_BY_COLUMN (which is one-shape-per-column and may
already hold a DIFFERENT, whole-column row for the same column, exactly the `work_review_
disposition` case: mechanism=trigger, two-way, over BOTH its licensed kinds, layered under by this
narrower CHECK for one of its three vocabulary values). Matched generically by `_PARTIAL_VALUE_RE`
on the CHECK's own textual shape, never by constraint name, so a NEW, unlicensed PARTIAL-VALUE
CHECK a future delta adds on a different (column, value) pair is caught by the same test and
refused as an unlicensed payload column unless a corresponding VALUE_PARTITION_MANIFEST row is
added alongside it.

USAGE:
  python3 gates/kind_shape_manifest_gate.py                 # scratch apply, assert, teardown
  python3 gates/kind_shape_manifest_gate.py --keep-scratch   # leave the scratch schema (debug)
  python3 gates/kind_shape_manifest_gate.py --inject-column NAME
      # after the real chain applies, ALSO `ALTER TABLE ledger ADD COLUMN NAME text` (no CHECK)
      # before asserting -- the seen-red negative control (a payload-like column with no
      # licensing CHECK and no MANIFEST entry). Never used by the plain gate invocation.

Exit codes: 0 clean, 1 violations (listed), 2 usage/psql/IO error.
Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "filing"))
import deployment_record  # noqa: E402  (filing/deployment_record.py, the ONE home for the
                           # closed-alphabet SQL-identifier check reused below -- ADR-0012 P1,
                           # never a second regex grown here)

LINEAGE = REPO / "kernel" / "lineage"

PGHOST = "192.168.122.1"
PGDB = "toy"

# The full current birth chain, in bootstrap/new-project.sh's own LINEAGE_CHAIN order --
# high_watermark_1.sql itself \ir-chains s15 -> s17(stamp) -> s17(independence) -> s19 (its own
# header, "DELIBERATELY EXCLUDED: s18" -- s18 is Study-mode apparatus, not kernel).
CHAIN = [
    "high_watermark_1.sql",
    "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql",
    "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql",
    "s24-declared-event-time.sql",
    "s25-commission-kind.sql",
    "s26-row-hash-chain.sql",
    "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql",
    "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql",
    "s31-supersession-uniform-retraction.sql",
    "s32-edge-views-single-home.sql",
    "s33-composite-discharge.sql",
    "s34-computed-grade-refusal.sql",
    "s35-validation-decomposition.sql",
    "s36-decision-grade.sql",
    "s37-violation-disposition.sql",
    "s38-bookkeeping-close.sql",
    "s39-blocks-start.sql",
    "s40-principal-identity-events.sql",
    "s41-principal-bindings-and-relations.sql",
    "s42-row-hash-full-coverage.sql",
    "s43-typed-verdict-write-boundary.sql",
    "s45-standing-lifecycle.sql",
    "s44-model-identity-attestation.sql",
    "s46-credited-views.sql",
    "s47-claim-on-closed-refusal.sql",
    "s48-review-witness-existence.sql",
    "s49-journaler-overflow-guard.sql",
    "s50-defeat-input-raw-domain.sql",
    "s51-artifact-store.sql",
    "s52-artifact-witness-check.sql",
    "s53-belief-substrate.sql",
    "s54-belief-views.sql",
    "s55-dispatch-grain-independence.sql",
    "s56-reservation-residue.sql",
    "s57-obligation-revocation-event.sql",
    "s58-missive-substrate.sql",
    "s59-missive-views.sql",
    "s60-entitlement-enforcement.sql",
    "s61-signature-symmetry-and-key-binding.sql",
]
# s58 (kernel/lineage/s58-missive-substrate.sql, design/FABLE-MISSIVES-KERNEL-SPEC.md, maintainer-
# ratified ledger row 1263) extends this SAME gate's scratch CHAIN and ships TEN new kind-scoped
# columns plus TWO genuinely new kind-shape idioms this codebase had none of before -- found live
# running this gate against the extended chain, not assumed from the spec's own text (the spec's
# own anticipated classifier edit -- for the TWO-MEMBER-KIND-SET two-way idiom,
# `(kind IN ('missive_sent','missive_received')) = (col IS NOT NULL)` -- turned out UNNECESSARY:
# Postgres canonicalizes `kind IN (a,b)` to `kind = ANY (ARRAY[...])`, already read by
# _KIND_ANY_RE, and _TWO_WAY_RE is a bare unanchored substring search, so the six two-way
# missive_* columns over the two-member kind-set classify cleanly with ZERO classifier edits,
# disclosed here rather than silently carried out anyway):
#   * MANDATORY-ON-KIND (`kind <> 'K' OR col IS NOT NULL` -- the mirror image of s43's own
#     FORBIDDEN-ON-KIND, `col IS NULL OR kind <> 'K'`): missive_disposition_mandatory_on_disposed.
#     New regex (_MANDATORY_ON_KIND_RE), new manifest (MANDATORY_ON_KIND_MANIFEST), checked in the
#     same early position as FORBIDDEN-ON-KIND (both share the "kind <>" prefix _extract_kinds
#     cannot read, and _ONE_WAY_A_RE would otherwise half-match "col IS NOT NULL" as if it were
#     "col IS NULL").
#   * KIND-OR-VALUE-PERMITTED (`col IS NULL OR kind = 'K' OR other_col = 'V'` -- a THREE-way
#     disjunction this codebase had no idiom for: the value is permitted on a WHOLE kind OR on one
#     VALUE of a different, already kind-scoped column): missive_disposition_allowed_homes. New
#     regex (_KIND_OR_VALUE_RE), new manifest (KIND_OR_VALUE_MANIFEST), checked in the same early
#     position (its own "(col IS NULL) OR (kind" prefix is the SAME false-match hazard
#     _ONE_WAY_A_RE poses for MANDATORY-ON-KIND, one level over).
# missive_disposition therefore carries THREE catalog CHECKs classified across three DIFFERENT
# manifests (MANDATORY_ON_KIND_MANIFEST, KIND_OR_VALUE_MANIFEST, plus its ordinary value-vocabulary
# CHECK, out of scope by the classifier's own first test) -- no MANIFEST_BY_COLUMN row of its own
# (that slot is one-shape-per-column; this column's shape is the compound of the two new idioms,
# not a single whole-column iff/implication). The nine OTHER missive_* columns (missive_protocol,
# missive_author_world, missive_addressee_world, missive_thread, missive_seq, missive_act --
# two-way over the two-member kind-set; missive_responds_to, missive_cites -- one-way over the
# same set; missive_provenance -- two-way over missive_received ALONE, spec §13 item 1) are new
# ordinary MANIFEST_BY_COLUMN rows below, GENERATED like s53's _BELIEF_COLS. s59 (kernel/lineage/
# s59-missive-views.sql) ships view-only, zero new columns/kinds/CHECKs -- verified live, no
# MANIFEST change of any kind.
# AMENDMENT 1 (design/FABLE-MISSIVES-KERNEL-SPEC.md, 2026-07-25, maintainer-ratified "yes to the
# column") adds an ELEVENTH missive_* column, missive_regards -- missive_disposed's subject,
# moved OFF the pre-existing `regards` column (this delta ORIGINALLY reused `regards`, which
# s15's validate_review trigger-locks to kind='review' ONLY, refusing every missive_disposed
# write live -- the build's own primary finding, round 1; MANDATORY_ON_KIND_MANIFEST's
# (regards, missive_disposed) row, which documented that conflict, is REMOVED by the amendment,
# below). missive_regards is an ORDINARY two-way iff (MANIFEST_BY_COLUMN, mechanism=CHECK) --
# simpler than the MANDATORY-ON-KIND/FORBIDDEN-ON-KIND idiom pair used for missive_disposition's
# own compound shape, and sufficient here: "forbidden on every kind except missive_disposed,
# mandatory there" IS a two-way iff by construction, no new idiom owed.
# s50-52/s54/s55/s56: no MANIFEST change. s53 (v2 B1): nine `belief` columns below; five coupling
# CHECKs are off VALUES not `kind`, no entry owed. s57 (row 1150): two columns below.
# s46/s47/s48/s49 each extend this SAME gate's scratch CHAIN and each ship ZERO new columns/kinds
# -- s46's two views, s47's re-issued validate_work_item_claim, s48's new validate_review_witness_
# existence trigger, and s49's local-exception-handler edit to kernel.journal_write_refusal all
# read/touch only EXISTING columns via ledger_current or row-addressed lookups -- no MANIFEST/
# VALUE_PARTITION_MANIFEST/FORBIDDEN_ON_KIND_MANIFEST edit for any of the four, verified live by
# running this gate against each extended chain and reading the SAME seven MANIFEST rows (s44's)
# as the only change, never an eighth.
# s44 (design/FABLE-OTEL-SENTRY-SPEC.md §8) extends this SAME gate's scratch CHAIN and ships
# SEVEN new kind-scoped columns for model_identity_attested (six two-way, one one-way --
# attest_expected legitimately NULL when no expectation declared), each a new MANIFEST row
# below. Re-issued ledger_kind_check/compute_row_hash/ledger_current/countersigned_in_force are
# invisible to this gate's classifier by construction. NOTE ON CHAIN ORDER: this gate's CHAIN is
# a scratch-apply order, not the real birth chain's numbering -- s44/s46 apply immediately after
# s45 (the real lineage head at their authoring time, "THE HEAD-BODY RULE").
# s45 (kernel/lineage/s45-standing-lifecycle.sql, ratified spec design/FABLE-STANDING-
# LIFECYCLE-SPEC.md, maintainer batch ratification ledger row 1481) extends this SAME gate's
# scratch CHAIN and ships NO new column and NO new kind -- its one MANIFEST-relevant act is a
# ROW UPDATE: principal_binding_active_kind_shape (already MANIFESTed above, s41) is RE-ISSUED
# widening its licensed kinds tuple from the four s41 binding kinds to six, adding
# principal_standing_declared and principal_suspended (principal_revoked deliberately absent --
# that absence is s45's ratified "terminal by type"). This is an EDIT to the existing MANIFEST
# row's kinds field, not a new row -- verified live by running this gate against the extended
# chain and confirming zero UNLICENSED/MISMATCHED findings with the widened tuple in place.
# s43 (kernel/lineage/s43-typed-verdict-write-boundary.sql, the ratified s42/s43 family's
# second delta) extends this SAME gate's scratch CHAIN and ships SIX new kind-scoped columns
# for the new write_refused kind (five two-way, one one-way -- refusal_attempted_actor is
# legitimately NULL when the attempt was unattributable), each a new MANIFEST row below, plus
# a NEW kind-shape IDIOM this codebase had none of before: FORBIDDEN-ON-KIND
# (`(<core-col> IS NULL) OR (kind <> '<K>')` -- s43's write_refused_unretractable, the
# ratified R6: a CORE column, supersedes, FORBIDDEN on exactly one kind, so a refusal row can
# never carry a retraction pointer). That idiom gets its own classifier branch
# (_FORBIDDEN_ON_KIND_RE, matched on shape, never constraint name -- checked BEFORE the
# generic one-way regexes, whose _ONE_WAY_A_RE would otherwise half-match it and then land
# UNPARSEABLE on the kind-negation) and its own manifest (FORBIDDEN_ON_KIND_MANIFEST, keyed
# (column, kind) -- NOT folded into MANIFEST_BY_COLUMN, whose one-shape-per-column slot is for
# PAYLOAD columns; supersedes stays a CORE column, additionally forbidden on one kind). s43's
# five value CHECKs (sqlstate/digest shape regexes, message/role non-emptiness, the closed
# surface vocabulary) carry no kind test and are correctly out of scope by the classifier's
# first test. The R6 substance trigger (validate_supersession_target) is a trigger, not a
# CHECK -- outside this gate's constraint universe, gated by ledger_reader_allowlist instead.
# s42 (kernel/lineage/s42-row-hash-full-coverage.sql) extends this SAME gate's scratch CHAIN.
# It ships NO new column, NO new kind, and NO new CHECK of any shape (its one act is the
# compute_row_hash re-issue to full-row serialization coverage -- a function body, invisible to
# this gate's constraint classifier by construction), so no MANIFEST/VALUE_PARTITION_MANIFEST/
# CORE_COLUMNS change -- verified live by running this gate against the extended chain and
# reading it clean with the same row counts as at the s41 head.
# s40 (kernel/lineage/s40-principal-identity-events.sql, design/FABLE-PRINCIPAL-IDENTITY-SPEC-
# BUILD-BASIS.md) extends this SAME gate's scratch CHAIN and ships THREE new whole-column
# kind-shape CHECKs, all two-way (the kinds are born in that same delta, so ADD CONSTRAINT
# validates vacuously -- no grandfathering reason for one-way, basis C5): principal_subject
# (over the four s40 identity-event kinds; s41 re-issues the SAME constraint widened to its own
# four binding/relation kinds -- one home, never a second patching constraint), principal_purpose
# (principal_registered only), principal_db_role (principal_standing_declared only). Its FOURTH
# column, principal_actor_resolution, is KIND-AGNOSTIC BY RATIFIED DESIGN (basis §9(f): every
# row of any kind carries the actor-resolution mark from s40 onward, NULL only on pre-s40
# history) -- a CORE column in this gate's vocabulary, added to CORE_COLUMNS below; its value
# CHECK (principal_actor_resolution_check) and principal_purpose's non-emptiness CHECK
# (principal_purpose_nonempty) mention no `kind` and are correctly out of this manifest's scope
# by the classifier's own first test. s40 also converts kernel.principal_role from table to
# VIEW -- the module docstring's sibling-surface sweep stands (still no `kind` column anywhere
# outside `ledger`; a view has no CHECK constraints at all).
# s39 (kernel/lineage/s39-blocks-start.sql) extends this SAME gate's scratch CHAIN so its re-issued
# objects are exercised by the scratch apply below. It ships NO new (kind, column, arity) MANIFEST
# row and NO new PARTIAL-VALUE VALUE_PARTITION_MANIFEST row: edge_type_check (the one CHECK it
# widens) carries no `kind` test at all (a flat vocabulary CHECK, s30's own shape, out of this
# gate's scope exactly like work_review_disposition_check) and edge_type_kind_shape (the SEPARATE
# CHECK that scopes the column to kind='work_depends_on' at all, s30's own existing MANIFEST row)
# is UNTOUCHED -- blocks-start rides the SAME column, the SAME one-way kind-scoping, no widening of
# ANY (kind, column, arity) correlation. Verified live by running this gate against the extended
# chain: it reports clean with the SAME 16 MANIFEST rows checked as before this delta, confirming
# no new payload column and no widened kind-shape CHECK slipped in undeclared.
# s38 (kernel/lineage/s38-bookkeeping-close.sql, design/FABLE-BOOKKEEPING-CLOSE-SPEC.md) extends
# this SAME gate's scratch CHAIN so its re-issued objects (validate_work_item_close) are exercised
# by the scratch apply below. It ships THREE new CHECKs, all named here (fresh reviewer finding,
# 2026-07-17: an earlier version of this comment reasoned about only two of the three -- corrected):
#   1. work_review_disposition_check (widened to admit 'bookkeeping') carries no `kind` test at
#      all (a flat vocabulary CHECK, `kind` never appears in its definition), so
#      `classify_kind_shape` returns None for it (out of scope, same as before this delta).
#   2. work_review_bookkeeping_requires_commit_ref ALSO carries no `kind` test (its predicate is
#      `work_review_disposition IS DISTINCT FROM 'bookkeeping' OR work_review_ref ~ '...'`, a
#      value-shape correlation between two ALREADY-payload columns, never a kind correlation), so
#      it too is correctly out of this manifest's (kind, column, arity) scope -- no MANIFEST row
#      needed.
#   3. work_review_bookkeeping_kind_shape ( `work_review_disposition IS DISTINCT FROM 'bookkeeping'
#      OR kind = 'work_closed'` ) is a GENUINE (kind, column)-correlation: it confines the single
#      value 'bookkeeping' of work_review_disposition to kind='work_closed' alone (the reviewer-
#      caught gap fix, s38's own header on the constraint). This is NOT the same shape as #2 (that
#      one correlates two payload columns with no `kind` test at all) and it is NOT
#      _VOCAB_PARTITION_RE's "which values legal per kind" concern either (that regex matches a
#      `kind = '<literal>' AND col = ANY(...)` membership test, a DIFFERENT-column-values-per-kind
#      question; this CHECK asks "which kind is this ONE value of the column legal on", the same
#      question `classify_kind_shape`'s two-way/one-way regexes answer for a whole column, just at
#      single-value granularity). It was, before this fix, silently swallowed by the entry filter
#      just below (`"IS NULL" not in defn and "IS NOT NULL" not in defn`) because it is phrased
#      with `IS DISTINCT FROM`, not `IS NULL`/`IS NOT NULL` -- caught live by re-running this gate
#      against the extended chain and finding it reported clean with only 15 MANIFEST rows
#      checked, never surfacing the third CHECK at all. Fixed by recognizing the idiom generically
#      (`_PARTIAL_VALUE_RE`, matched on shape, never on constraint name) as its own classification,
#      PARTIAL-VALUE, with its own manifest (`VALUE_PARTITION_MANIFEST`) below -- not folded into
#      the whole-column MANIFEST/MANIFEST_BY_COLUMN, because `work_review_disposition` ALREADY
#      holds a MANIFEST_BY_COLUMN row (mechanism=trigger, two-way, over the WHOLE column across
#      both its licensed kinds) and a value-scoped CHECK for one of its three vocabulary values is
#      an additional, narrower correlation layered on top, not a competing or replacing shape for
#      the same (column) key -- forcing it into the single-shape-per-column MANIFEST_BY_COLUMN slot
#      would false-positive a "mechanism drifted from trigger to CHECK" violation against the
#      column's own already-correct trigger-mechanism row.
# Extended through the FULL chain to s37 (not merely an s37-only hop) so the QUANTIFICATION
# UNIVERSE is the live chain in full, matching `gates/ledger_reader_allowlist.py`'s own extension
# in this same branch -- and this extension's own first scratch-witness attempt (this file's own
# "caught live" lesson, same as every sNN delta's header before it) surfaced that s31/s32/s34/s35
# ship no new kind-shape CHECK of their own, but s33 AND s36 do, alongside s37: s33
# (kernel/lineage/s33-composite-discharge.sql) adds `work_discharge` (one-way, kind='work_opened'
# -- declared at OPEN time whether the item is composite, s33 Element 1) and s36
# (kernel/lineage/s36-decision-grade.sql) adds `decision_grade` (one-way, kind='decision', s36
# Element/CLOSURE STATEMENT) -- both NEW MANIFEST rows below, found the same way the s37 columns
# were: by running THIS gate against the extended chain and reading its own UNLICENSED PAYLOAD
# COLUMN violations, not by re-reading every intervening header speculatively. s37
# (kernel/lineage/s37-violation-disposition.sql) is the delta that ALSO needs new MANIFEST rows:
# a new kind (`work_violation_disposition`), three new columns (work_violation_class,
# work_violation_target_id, work_violation_witness), and TWO existing MANIFEST rows
# (work_resolution, work_review_ref) whose CHECKs widen to also license the new kind -- see
# MANIFEST below.

# ================================================================================================
# THE MANIFEST -- the ONE declared table (ADR-0011 Rule 4: a net over the class, never an
# enumeration hand-copied per reader). Per F5: the (kind, column, arity) correlation, PLUS the
# `mechanism` field this sweep found is also load-bearing variance (CHECK vs trigger), PLUS a
# `reason` naming WHY every one-way or trigger-mechanism row is not a two-way CHECK -- filed, not
# silently uniformized (ADR-0000 Rule 2a's "an axis deliberately not covered is named as not
# covered" applied one level down, to enforcement mechanism rather than input axis).
# ================================================================================================
MANIFEST = [
    dict(column="work_slug", kinds=("work_opened", "work_claimed", "work_depends_on", "work_closed"),
         arity="two-way", mechanism="CHECK", constraint="work_slug_kind_shape",
         defining_delta="s22-work-item-ledger.sql", reason=None),
    dict(column="work_title", kinds=("work_opened",),
         arity="two-way", mechanism="CHECK", constraint="work_title_kind_shape",
         defining_delta="s22-work-item-ledger.sql", reason=None),
    dict(column="work_depends_on", kinds=("work_depends_on",),
         arity="two-way", mechanism="CHECK", constraint="work_depends_on_kind_shape",
         defining_delta="s22-work-item-ledger.sql", reason=None),
    dict(column="work_resolution", kinds=("work_closed", "work_violation_disposition"),
         arity="two-way", mechanism="CHECK", constraint="work_resolution_kind_shape",
         defining_delta="s22-work-item-ledger.sql "
                         "(kinds widened by s37-violation-disposition.sql)",
         reason="s37 widens the iff to license work_violation_disposition too -- disposition rows "
                "carry work_resolution='reissued'|'retired', a vocabulary disjoint from "
                "work_closed's own four values (see work_resolution_check, a SEPARATE "
                "kind-partitioned VALUE-VOCABULARY CHECK on the same column, out of this "
                "manifest's (kind,arity)-SHAPE scope -- module docstring's NOT IN SCOPE section)."),
    dict(column="work_witness", kinds=("work_closed",),
         arity="one-way", mechanism="CHECK", constraint="work_witness_kind_shape",
         defining_delta="s22-work-item-ledger.sql",
         reason="not every work_closed row carries a witness -- only a 'shipped' resolution "
                "requires one (work_shipped_requires_witness); one-way forecloses work_witness "
                "appearing on a NON-work_closed row, it does not demand one on every work_closed "
                "row."),
    dict(column="work_parent", kinds=("work_opened",),
         arity="one-way", mechanism="CHECK", constraint="work_parent_kind_shape",
         defining_delta="s28-work-parent-edge.sql",
         reason="nullable-legal-roots (s28 header, verbatim): a root item legitimately has "
                "kind='work_opened' with work_parent NULL, so the correlation is NOT an iff."),
    dict(column="work_review_ref", kinds=("work_closed", "work_violation_disposition"),
         arity="one-way", mechanism="CHECK", constraint="work_review_ref_kind_shape",
         defining_delta="s29-obligation-item-key-and-typed-close.sql "
                         "(kinds widened by s37-violation-disposition.sql)",
         reason="mirrors work_witness one column over: only a 'witnessed' disposition "
                "(work_review_witnessed_requires_ref) requires a ref; a 'deferred' work_closed "
                "row legitimately has NULL. s37 widens the one-way implication to also license "
                "work_violation_disposition rows, which carry the SAME witnessed/deferred "
                "discipline (its own header, verbatim)."),
    dict(column="work_strict_close", kinds=("work_closed",),
         arity="one-way", mechanism="CHECK", constraint="work_strict_close_kind_shape",
         defining_delta="s29-obligation-item-key-and-typed-close.sql",
         reason="NULL/false = non-strict is a legal posture on ANY work_closed row (s29: "
                "'the spec's own declared posture, not a universal mandate'); one-way forecloses "
                "work_strict_close appearing on a non-work_closed row only."),
    dict(column="edge_type", kinds=("work_depends_on",),
         arity="one-way", mechanism="CHECK", constraint="edge_type_kind_shape",
         defining_delta="s30-typed-dependency-edges.sql",
         reason="append-only history forces this (s30 header, verbatim): a legacy "
                "work_depends_on row predates this column and can never be backfilled (no "
                "UPDATE, append-only) -- a two-way iff would fail ADD CONSTRAINT's whole-table "
                "validation on any world with pre-existing rows."),
    dict(column="work_discharge", kinds=("work_opened",),
         arity="one-way", mechanism="CHECK", constraint="work_discharge_kind_shape",
         defining_delta="s33-composite-discharge.sql",
         reason="declared at OPEN time whether the item is composite (s33 Element 1, 'every "
                "non-composite item is legally work_discharge IS NULL') -- lives on the item's "
                "OWN opening row, not its close row, so the one licensed kind is work_opened; "
                "one-way forecloses it appearing on a non-work_opened row only, not every "
                "work_opened row carries it."),
    dict(column="decision_grade", kinds=("decision",),
         arity="one-way", mechanism="CHECK", constraint="decision_grade_kind_shape",
         defining_delta="s36-decision-grade.sql",
         reason="nullable, legal only on kind='decision' rows, no enum/CHECK on the value itself "
                "(s36 header, verbatim: 'the kernel stores a word; which words matter is "
                "deployment policy') -- one-way forecloses it appearing on a non-decision row, "
                "it does not demand one on every decision row."),
    dict(column="work_violation_class", kinds=("work_violation_disposition",),
         arity="two-way", mechanism="CHECK", constraint="work_violation_class_kind_shape",
         defining_delta="s37-violation-disposition.sql",
         reason="which work_item_violations arm (e.g. orphaned_by_retraction, dependency_cycle) "
                "the disposition answers -- legal and REQUIRED exactly on the new kind, an iff "
                "like work_slug/work_title/work_depends_on/work_resolution."),
    dict(column="work_violation_target_id", kinds=("work_violation_disposition",),
         arity="two-way", mechanism="CHECK", constraint="work_violation_target_id_kind_shape",
         defining_delta="s37-violation-disposition.sql",
         reason="the answered violations-view row's target_id (the violating act's own row id, "
                "or the slug's own work_opened row id for the five slug-keyed arms) -- legal and "
                "REQUIRED exactly on the new kind, same iff shape as work_violation_class."),
    dict(column="work_violation_witness", kinds=("work_violation_disposition",),
         arity="one-way", mechanism="CHECK", constraint="work_violation_witness_kind_shape",
         defining_delta="s37-violation-disposition.sql",
         reason="for work_resolution='reissued', the cited successor row id -- NULLABLE even "
                "when reissued (s37 element 4: warns, never refused; the kernel cannot verify "
                "successor equivalence), so one-way forecloses it appearing on a NON-"
                "work_violation_disposition row only, mirroring work_witness/work_violation_"
                "witness's own sibling shapes one column over."),
    dict(column="regards", kinds=("review",),
         arity="two-way", mechanism="trigger", constraint=None,
         defining_delta="s15-schema.sql",
         reason="cannot be a plain CHECK: validate_review() must look up an EARLIER row's actor "
                "(self-referencing lookup) to enforce segregation-of-duties -- a CHECK cannot "
                "express that. Logically two-way (kind='review' iff regards IS NOT NULL): the "
                "trigger's first IF raises when kind='review' AND regards IS NULL, its ELSIF "
                "raises when kind<>'review' AND regards IS NOT NULL."),
    dict(column="principal_subject",
         kinds=("principal_registered", "principal_suspended", "principal_revoked",
                "principal_standing_declared",
                "principal_relation_asserted", "principal_role_bound", "principal_key_bound",
                "principal_competence_granted"),
         arity="two-way", mechanism="CHECK", constraint="principal_subject_kind_shape",
         defining_delta="s40-principal-identity-events.sql",
         reason="the principal an identity/binding event is ABOUT (distinct from actor) -- "
                "mandatory on every principal_* kind, forbidden elsewhere; two-way is safe "
                "because every licensed kind is born in the same family (vacuous ADD CONSTRAINT "
                "validation). ONE constraint, re-issued wider by s41 (never patched by a second "
                "constraint) -- this row tracks the re-issued, eight-kind head shape."),
    dict(column="principal_purpose", kinds=("principal_registered",),
         arity="two-way", mechanism="CHECK", constraint="principal_purpose_kind_shape",
         defining_delta="s40-principal-identity-events.sql",
         reason="AC-2's stated-purpose registration field: mandatory (non-empty via the "
                "separate, kind-free principal_purpose_nonempty value CHECK) on "
                "principal_registered, NULL on every other kind -- two-way per the basis's C5 "
                "(the kind is born in the same delta; there was never a grandfathering reason "
                "for one-way)."),
    dict(column="principal_db_role", kinds=("principal_standing_declared",),
         arity="two-way", mechanism="CHECK", constraint="principal_db_role_kind_shape",
         defining_delta="s40-principal-identity-events.sql",
         reason="the database role a standing declaration binds -- mandatory on exactly that "
                "kind, forbidden elsewhere (two-way, same vacuous-validation ground as its two "
                "sibling s40 columns)."),
    dict(column="principal_binding_active",
         kinds=("principal_relation_asserted", "principal_role_bound", "principal_key_bound",
                "principal_competence_granted",
                "principal_standing_declared", "principal_suspended"),
         arity="two-way", mechanism="CHECK", constraint="principal_binding_active_kind_shape",
         defining_delta="s41-principal-bindings-and-relations.sql "
                         "(kinds widened to six by s45-standing-lifecycle.sql)",
         reason="the identity/value discriminator, now of SIX kinds (true = assertion, "
                "false = retraction restating identity fields only) -- mandatory via this CHECK "
                "on exactly those kinds, never a column-level NOT NULL (basis C10); vacuous "
                "validation, each kind's licensing born in the delta that licenses it. s45 "
                "(kernel/lineage/s45-standing-lifecycle.sql, ratified spec design/FABLE-"
                "STANDING-LIFECYCLE-SPEC.md) widens the four s41 binding kinds to six, adding "
                "principal_standing_declared (false = an unbind, restating BOTH principal_"
                "db_role and principal_subject) and principal_suspended (false = a lift, "
                "restating principal_subject) -- ONE re-issue of this same CHECK, never a "
                "second patching constraint (ADR-0012 P1, the principal_subject_kind_shape "
                "precedent). principal_revoked is DELIBERATELY ABSENT -- that absence IS s45's "
                "ratified 'terminal by type'. Its inactive-needs-supersedes and mandatory-iff-"
                "active companions carry no kind test (value CHECKs, out of scope by the "
                "classifier's first test)."),
    dict(column="principal_object", kinds=("principal_relation_asserted",),
         arity="two-way", mechanism="CHECK", constraint="principal_object_kind_shape",
         defining_delta="s41-principal-bindings-and-relations.sql",
         reason="a relation's far endpoint (identity field, mandatory active or not)."),
    dict(column="principal_relation", kinds=("principal_relation_asserted",),
         arity="two-way", mechanism="CHECK", constraint="principal_relation_kind_shape",
         defining_delta="s41-principal-bindings-and-relations.sql",
         reason="the typed relation (identity field); its closed four-value vocabulary and the "
                "same-natural-person canonical-order closure are separate kind-free CHECKs "
                "(principal_relation_check, principal_snp_canonical_order)."),
    dict(column="principal_role_name", kinds=("principal_role_bound", "entitlement_class_configured"),
         arity="two-way", mechanism="CHECK", constraint="principal_role_name_kind_shape",
         defining_delta="s41-principal-bindings-and-relations.sql "
                         "(kinds widened by s60-entitlement-enforcement.sql)",
         reason="identity field, mandatory active or not. FREE non-empty text by RATIFIED "
                "ruling (basis §9(c)/C13, witnessed rows 1432/1433): role naming is "
                "organizational configuration -- deliberately NO value vocabulary CHECK exists "
                "for this column, only non-emptiness. s60 widens the iff to license "
                "entitlement_class_configured too -- REUSED, never a second 'role name' column "
                "(ADR-0012 P1): a configuration row's required-role value shares the SAME "
                "free-text vocabulary a binding row's bound-role value uses."),
    dict(column="principal_key_fingerprint",
         kinds=("principal_key_bound", "commission_signature_verified",
                "principal_key_possession_verified"),
         arity="two-way", mechanism="CHECK", constraint="principal_key_fingerprint_kind_shape",
         defining_delta="s41-principal-bindings-and-relations.sql "
                         "(kinds widened to three by s61-signature-symmetry-and-key-binding.sql)",
         reason="identity field; the OpenPGP v4 shape is a separate kind-free value CHECK "
                "(principal_key_fingerprint_shape); the human-subject-only rule is D-3's "
                "trigger, not a CHECK (cross-table lookup). s61 widens the iff to license "
                "commission_signature_verified (the signing key that produced a VERIFIED "
                "signature) and principal_key_possession_verified (the fingerprint whose "
                "possession was proven) -- REUSED, never a second fingerprint column "
                "(ADR-0012 P1)."),
    dict(column="signature_attests_row", kinds=("commission_signature_verified",),
         arity="two-way", mechanism="CHECK", constraint="signature_attests_row_kind_shape",
         defining_delta="s61-signature-symmetry-and-key-binding.sql",
         reason="identity field: the commission row (kind=commission) this attestation regards "
                "-- a genuine FK to ledger(id), existence kernel-enforced by the REFERENCES "
                "clause itself; the target-kind check (must be 'commission') is a trigger "
                "(validate_signature_witness), not a CHECK, since it needs a cross-row lookup."),
    dict(column="signature_grade", kinds=("commission_signature_verified",),
         arity="two-way", mechanism="CHECK", constraint="signature_grade_kind_shape",
         defining_delta="s61-signature-symmetry-and-key-binding.sql",
         reason="value field: which vocabulary the attested VERIFIED verdict earned "
                "(binding-verified | directory-verified) -- design/"
                "FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §2 item 2's grade, banked permanently. "
                "The closed two-member vocabulary is a separate kind-free value CHECK "
                "(signature_grade_vocabulary)."),
    dict(column="key_binding_possession_ref", kinds=("principal_key_bound",),
         arity="two-way", mechanism="CHECK", constraint="key_binding_possession_ref_kind_shape",
         defining_delta="s61-signature-symmetry-and-key-binding.sql",
         reason="mandatory-iff-a-FRESH-bind (principal_binding_active IS TRUE), forbidden "
                "otherwise (retraction or any other kind) -- a genuine FK to ledger(id) naming "
                "the principal_key_possession_verified row (item 3) proving possession of the "
                "fingerprint being bound. The target-kind-and-fingerprint-match check is a "
                "trigger (validate_principal_binding, re-issued), not a CHECK (cross-row "
                "lookup); IS TRUE is used throughout to keep every other kind's NULL "
                "principal_binding_active out of three-valued-logic trouble (the s41 D-1 "
                "idiom)."),
    dict(column="principal_competence_activity", kinds=("principal_competence_granted",),
         arity="two-way", mechanism="CHECK",
         constraint="principal_competence_activity_kind_shape",
         defining_delta="s41-principal-bindings-and-relations.sql",
         reason="G13's activity: the grant's IDENTITY field, mandatory on every grant row "
                "active or not (a withdrawal must say which activity)."),
    dict(column="principal_competence_band", kinds=("principal_competence_granted",),
         arity="one-way", mechanism="CHECK", constraint="principal_competence_band_kind_shape",
         defining_delta="s41-principal-bindings-and-relations.sql",
         reason="G13's band: a VALUE field, NULL on a withdrawal row of its own kind -- so the "
                "kind correlation cannot be an iff; the mandatory-iff-active rule is the "
                "kind-free principal_competence_band_iff_active CHECK (guarded via the activity "
                "column, non-NULL exactly on this kind). Free text v1 by RATIFIED PLACEHOLDER "
                "(basis §9(g) loud note)."),
    dict(column="principal_competence_basis", kinds=("principal_competence_granted",),
         arity="one-way", mechanism="CHECK", constraint="principal_competence_basis_kind_shape",
         defining_delta="s41-principal-bindings-and-relations.sql",
         reason="G13's basis: same VALUE-field shape as band, one column over."),
    dict(column="refusal_sqlstate", kinds=("write_refused",),
         arity="two-way", mechanism="CHECK", constraint="refusal_sqlstate_kind_shape",
         defining_delta="s43-typed-verdict-write-boundary.sql",
         reason="the refused attempt's SQLSTATE -- mandatory on every write_refused row "
                "(the kind is born in the same delta; vacuous ADD CONSTRAINT validation), "
                "forbidden elsewhere; its ^[0-9A-Z]{5}$ shape is the separate kind-free "
                "refusal_sqlstate_shape value CHECK."),
    dict(column="refusal_message", kinds=("write_refused",),
         arity="two-way", mechanism="CHECK", constraint="refusal_message_kind_shape",
         defining_delta="s43-typed-verdict-write-boundary.sql",
         reason="the refusal's teach-text verbatim (kernel-authored prose; the refused "
                "payload itself is digest-only, R4) -- mandatory on the kind, forbidden "
                "elsewhere; non-emptiness is the separate refusal_message_nonempty value "
                "CHECK."),
    dict(column="refusal_surface", kinds=("write_refused",),
         arity="two-way", mechanism="CHECK", constraint="refusal_surface_kind_shape",
         defining_delta="s43-typed-verdict-write-boundary.sql",
         reason="WHICH boundary function caught it -- mandatory; the closed "
                "ledger/review/registration/obligation vocabulary is the separate kind-free "
                "refusal_surface_check (kernel-structural: it enumerates the boundary "
                "functions themselves)."),
    dict(column="refusal_payload_digest", kinds=("write_refused",),
         arity="two-way", mechanism="CHECK", constraint="refusal_payload_digest_kind_shape",
         defining_delta="s43-typed-verdict-write-boundary.sql",
         reason="SHA-256 of the refused payload's canonical text (digest, never verbatim -- "
                "R4, ratified) -- mandatory; the 64-hex shape is the separate "
                "refusal_payload_digest_shape value CHECK."),
    dict(column="refusal_attempted_actor", kinds=("write_refused",),
         arity="one-way", mechanism="CHECK", constraint="refusal_attempted_actor_kind_shape",
         defining_delta="s43-typed-verdict-write-boundary.sql",
         reason="the ATTEMPTED principal when it resolved to a registered id -- legitimately "
                "NULL when the attempt was unattributable (an unknown/unresolvable identity "
                "is exactly a case the record must still represent), so the correlation "
                "cannot be an iff; one-way forecloses it appearing on a non-write_refused "
                "row only. FK to kernel.principal."),
    dict(column="refusal_attempted_role", kinds=("write_refused",),
         arity="two-way", mechanism="CHECK", constraint="refusal_attempted_role_kind_shape",
         defining_delta="s43-typed-verdict-write-boundary.sql",
         reason="session_user at the attempt -- ALWAYS known (server-witnessed), so "
                "mandatory even when the attempted principal is not resolvable; "
                "non-emptiness is the separate refusal_attempted_role_nonempty value CHECK."),
    dict(column="work_review_disposition", kinds=("work_closed", "work_violation_disposition"),
         arity="two-way", mechanism="trigger", constraint=None,
         defining_delta="s29-obligation-item-key-and-typed-close.sql (sec-10 epoch amendment; "
                         "kinds widened by s37-violation-disposition.sql)",
         reason="WAS a table CHECK (work_review_disposition_kind_shape) until the sec-10 "
                "amendment made the two-way correlation EPOCH-GATED (grandfathers pre-amendment "
                "rows) -- a CHECK cannot consult migration_epoch, a different table, so the "
                "correlation moved into validate_work_item()'s trigger clause. The old CHECK's "
                "DROP CONSTRAINT IF EXISTS is kept in s29 as idempotent cleanup, never re-added. "
                "s37's validate_work_item_disposition() applies the SAME "
                "IS NULL-raises-refusal check to work_violation_disposition rows (its own line "
                "'r.work_review_disposition IS NULL THEN RAISE...') -- kinds widened here to "
                "record that, though (per this row's own mechanism=trigger) no catalog CHECK "
                "verifies it; the trigger source is the actual enforcement, same as before."),
    dict(column="attest_row_id", kinds=("model_identity_attested",),
         arity="two-way", mechanism="CHECK", constraint="attest_row_id_kind_shape",
         defining_delta="s44-model-identity-attestation.sql",
         reason="the ATTESTED row -- mandatory on every model_identity_attested row (the kind "
                "is born in the same delta; vacuous ADD CONSTRAINT validation), forbidden "
                "elsewhere; self-referencing FK to ledger(id) makes the target's existence "
                "structural."),
    dict(column="attest_model", kinds=("model_identity_attested",),
         arity="two-way", mechanism="CHECK", constraint="attest_model_kind_shape",
         defining_delta="s44-model-identity-attestation.sql",
         reason="the observed model string, verbatim from the OTel event -- mandatory; "
                "non-emptiness is the separate attest_model_nonempty value CHECK."),
    dict(column="attest_grade", kinds=("model_identity_attested",),
         arity="two-way", mechanism="CHECK", constraint="attest_grade_kind_shape",
         defining_delta="s44-model-identity-attestation.sql",
         reason="the closed join-set confidence grade -- mandatory; its four-member vocabulary "
                "(exact-command/turn-bracketed/session-scoped/ambiguous) is the separate "
                "kind-free attest_grade_check value CHECK -- kernel-structural (it enumerates "
                "this design's own join algebra, like s43's refusal_surface)."),
    dict(column="attest_verdict", kinds=("model_identity_attested",),
         arity="two-way", mechanism="CHECK", constraint="attest_verdict_kind_shape",
         defining_delta="s44-model-identity-attestation.sql",
         reason="the closed verdict (match/mismatch/unevaluated, lowercase) -- mandatory; its "
                "vocabulary is the separate attest_verdict_check value CHECK; structurally "
                "coupled to attest_expected by the separate kind-free "
                "attest_expected_verdict_coupling CHECK."),
    dict(column="attest_expected", kinds=("model_identity_attested",),
         arity="one-way", mechanism="CHECK", constraint="attest_expected_kind_shape",
         defining_delta="s44-model-identity-attestation.sql",
         reason="the declared expected model -- legitimately NULL when the session declared "
                "none, so the correlation cannot be an iff; one-way forecloses it appearing on "
                "a non-model_identity_attested row only. Non-emptiness when present is the "
                "separate attest_expected_nonempty value CHECK; the expected/verdict coupling "
                "is the separate attest_expected_verdict_coupling CHECK, out of THIS "
                "manifest's (kind,column,arity) scope by the classifier's own first test (it "
                "carries no bare IS NULL/IS NOT NULL correlate to kind alone)."),
    dict(column="attest_session", kinds=("model_identity_attested",),
         arity="two-way", mechanism="CHECK", constraint="attest_session_kind_shape",
         defining_delta="s44-model-identity-attestation.sql",
         reason="the OTel session.id -- mandatory; non-emptiness is the separate "
                "attest_session_nonempty value CHECK."),
    dict(column="attest_basis", kinds=("model_identity_attested",),
         arity="two-way", mechanism="CHECK", constraint="attest_basis_kind_shape",
         defining_delta="s44-model-identity-attestation.sql",
         reason="the comma-separated join keys used -- mandatory; non-emptiness is the "
                "separate attest_basis_nonempty value CHECK."),
]
# s53 v2 B1: nine `belief`-only columns, GENERATED (not hand-repeated dicts, ADR-0012 P1 SSOT).
_BELIEF_COLS = (
    ("belief_polarity", "two-way", "universal|existential; vocabulary is belief_polarity_check."),
    ("belief_basis", "two-way", "observed|derived|testimony|assumed; vocabulary is belief_basis_check."),
    ("belief_universe", "one-way", "presence governed by belief_universe_coupling (off polarity's VALUE)."),
    ("belief_witness", "one-way", "presence governed by belief_witness_universal_forbidden/observed_mandatory."),
    ("belief_source", "one-way", "presence governed by belief_source_coupling. Self-FK to ledger(id)."),
    ("belief_premises", "one-way", "presence/cardinality via belief_premises_coupling. bigint[], no FK."),
    ("belief_subject", "one-way", "optional, the regards/attest_row_id idiom. Self-FK to ledger(id)."),
    ("belief_contests", "one-way", "optional. Self-FK for existence; rest enforced by validate_belief_edges."),
    ("belief_concurs", "one-way", "optional. Same shape as belief_contests one column over."),
)
for _col, _arity, _reason in _BELIEF_COLS:
    MANIFEST.append(dict(column=_col, kinds=("belief",), arity=_arity, mechanism="CHECK",
                         constraint=f"{_col}_kind_shape", defining_delta="s53-belief-substrate.sql", reason=_reason))
# s56: view-only, no MANIFEST row. s57 (row 1150): two new obligation_revoked-only columns.
for _col in ("obligation_revoked_scope", "obligation_revoke_reason"):
    MANIFEST.append(dict(column=_col, kinds=("obligation_revoked",), arity="two-way", mechanism="CHECK",
                         constraint=f"{_col}_kind_shape", defining_delta="s57-obligation-revocation-event.sql",
                         reason="mandatory, non-empty (s57)."))
# s58: nine ordinary missive_* columns (GENERATED, ADR-0012 P1 SSOT -- the s53 _BELIEF_COLS
# precedent). Six two-way over the two-member envelope kind-set; two one-way over the same set;
# missive_provenance two-way over missive_received ALONE (spec §13 item 1 -- FORBIDDEN on
# missive_sent, a row cannot carry its own row_hash).
_MISSIVE_ENVELOPE_KINDS = ("missive_sent", "missive_received")
_MISSIVE_COLS = (
    ("missive_protocol", "two-way", _MISSIVE_ENVELOPE_KINDS, "= 1 (v1 closed); missive_protocol_check."),
    ("missive_author_world", "two-way", _MISSIVE_ENVELOPE_KINDS, "sending world; self-missive refused by missive_self_missive_refused."),
    ("missive_addressee_world", "two-way", _MISSIVE_ENVELOPE_KINDS, "receiving world."),
    ("missive_thread", "two-way", _MISSIVE_ENVELOPE_KINDS, "<minting_world>/<slug>; missive_thread_shape."),
    ("missive_seq", "two-way", _MISSIVE_ENVELOPE_KINDS, "author-local sequence, >= 1; missive_seq_check."),
    ("missive_act", "two-way", _MISSIVE_ENVELOPE_KINDS, "the closed five-act vocabulary; missive_act_check."),
    ("missive_responds_to", "one-way", _MISSIVE_ENVELOPE_KINDS, "mandatory on response/ack/withdrawal via missive_responds_to_coupling (spelled off VALUE, not kind)."),
    ("missive_cites", "one-way", _MISSIVE_ENVELOPE_KINDS, "non-empty when present via missive_cites_nonempty; token shape/existence via validate_missive_tokens."),
)
for _col, _arity, _kinds, _reason in _MISSIVE_COLS:
    MANIFEST.append(dict(column=_col, kinds=_kinds, arity=_arity, mechanism="CHECK",
                         constraint=f"{_col}_kind_shape", defining_delta="s58-missive-substrate.sql", reason=_reason))
MANIFEST.append(dict(column="missive_provenance", kinds=("missive_received",), arity="two-way",
                     mechanism="CHECK", constraint="missive_provenance_kind_shape",
                     defining_delta="s58-missive-substrate.sql",
                     reason="two-way over missive_received ALONE (spec §13 item 1): the "
                            "author-side token is MINTED by s59's missive_outbound view at serve "
                            "time, never stored on missive_sent -- a row cannot carry its own "
                            "row_hash."))
# AMENDMENT 1 (2026-07-25, "yes to the column"): missive_regards, a NEW dedicated column --
# missive_disposed's subject, moved OFF the pre-existing `regards` column (trigger-locked by
# s15's validate_review to kind='review' ONLY, witnessed live to refuse every missive_disposed
# write when reused there -- the build's own primary finding, round 1). Ordinary two-way iff:
# FORBIDDEN on every kind except missive_disposed, MANDATORY there -- `regards` and
# validate_review are UNTOUCHED (see this file's own note above, where the conflicted
# MANDATORY_ON_KIND_MANIFEST row for (regards, missive_disposed) was REMOVED).
MANIFEST.append(dict(column="missive_regards", kinds=("missive_disposed",), arity="two-way",
                     mechanism="CHECK", constraint="missive_regards_kind_shape",
                     defining_delta="s58-missive-substrate.sql",
                     reason="the missive_received row a missive_disposed event regards -- "
                            "mandatory on exactly that kind, forbidden elsewhere. Self-FK to "
                            "ledger(id) for structural existence; the KIND correlation (must be "
                            "missive_received) is validate_missive_regards' own cross-row check, "
                            "AMENDMENT 1's dedicated trigger."))
MANIFEST.append(dict(column="entitlement_act_class", kinds=("entitlement_class_configured",),
                     arity="two-way", mechanism="CHECK",
                     constraint="entitlement_act_class_kind_shape",
                     defining_delta="s60-entitlement-enforcement.sql",
                     reason="identity field, mandatory on the one kind that carries it, "
                            "forbidden elsewhere. Free text, no enum -- the kernel-computed "
                            "vocabulary of act-class strings a configuration row can USEFULLY "
                            "match lives in entitlement_act_class_of(), not a value CHECK (the "
                            "s36 decision_grade free-text-token precedent, one axis over)."))
MANIFEST_BY_COLUMN = {row["column"]: row for row in MANIFEST}
assert len(MANIFEST_BY_COLUMN) == len(MANIFEST), "duplicate column in MANIFEST -- SSOT violated"

# ================================================================================================
# VALUE_PARTITION_MANIFEST -- a SECOND, narrower manifest for PARTIAL-VALUE kind-shape CHECKs (see
# module docstring's "IN SCOPE, a THIRD manifest" paragraph). Keyed by (column, value), never
# folded into MANIFEST_BY_COLUMN: a column may already hold a whole-column MANIFEST row (e.g.
# work_review_disposition's own trigger-mechanism, two-way row above) AND separately carry a
# CHECK-enforced correlation for just ONE of its vocabulary values -- two different, non-competing
# concerns at two different granularities, not a second declaration of the same shape.
# ================================================================================================
VALUE_PARTITION_MANIFEST = [
    dict(column="work_review_disposition", value="bookkeeping", kinds=("work_closed",),
         mechanism="CHECK", constraint="work_review_bookkeeping_kind_shape",
         defining_delta="s38-bookkeeping-close.sql",
         reason="reviewer-caught gap (s38's own header on the constraint, verbatim): "
                "work_review_disposition is shared with work_violation_disposition rows (s37) via "
                "its OWN whole-column MANIFEST row above (mechanism=trigger, kinds=(work_closed, "
                "work_violation_disposition)) -- without this CHECK, 'bookkeeping' would be "
                "constructible on a work_violation_disposition row too, invisible to "
                "work_bookkeeping_closes (WHERE kind = 'work_closed') and contradicting this "
                "delta's own closure statement ('the bookkeeping fact rides the EXISTING "
                "work_closed kind's own columns'). Mirrors work_review_ref_kind_shape (s37) one "
                "column over: one-way, licenses 'bookkeeping' on kind = 'work_closed' alone."),
]
VALUE_PARTITION_BY_KEY = {(row["column"], row["value"]): row for row in VALUE_PARTITION_MANIFEST}
assert len(VALUE_PARTITION_BY_KEY) == len(VALUE_PARTITION_MANIFEST), \
    "duplicate (column, value) in VALUE_PARTITION_MANIFEST -- SSOT violated"

# ================================================================================================
# FORBIDDEN_ON_KIND_MANIFEST -- a FOURTH manifest, for FORBIDDEN-ON-KIND CHECKs (see the
# _FORBIDDEN_ON_KIND_RE comment above): a column forbidden on exactly one kind, legal
# elsewhere. Keyed (column, kind). First instance: s43's ratified R6.
# ================================================================================================
FORBIDDEN_ON_KIND_MANIFEST = [
    dict(column="supersedes", kind="write_refused",
         mechanism="CHECK", constraint="write_refused_unretractable",
         defining_delta="s43-typed-verdict-write-boundary.sql",
         reason="R6, RATIFIED (ledger row 1460): a write_refused row is UNRETRACTABLE -- it "
                "records a historical fact about a refused attempt and asserts nothing "
                "retractable, so it may never CARRY a supersedes pointer (this CHECK) and no "
                "later row may NAME it as a supersession target (the companion "
                "validate_supersession_target trigger, which a same-row CHECK cannot express "
                "-- the s43 delta's own surfaced letter/spirit note). A deliberate, ratified "
                "divergence from s31's supersession uniformity."),
]
FORBIDDEN_BY_KEY = {(row["column"], row["kind"]): row for row in FORBIDDEN_ON_KIND_MANIFEST}
assert len(FORBIDDEN_BY_KEY) == len(FORBIDDEN_ON_KIND_MANIFEST), \
    "duplicate (column, kind) in FORBIDDEN_ON_KIND_MANIFEST -- SSOT violated"

# ================================================================================================
# CROSS_COLUMN_COUPLING_MANIFEST -- a FIFTH manifest, for CROSS-COLUMN KIND-SCOPED COUPLING
# CHECKs (see the _CROSS_COLUMN_COUPLING_RE comment above): two ALREADY kind-scoped payload
# columns whose PRESENCE (not value) is structurally coupled to each other, gated by one kind.
# Keyed by constraint name (not by either column alone -- both already hold their own
# MANIFEST_BY_COLUMN row; this manifest tracks the ADDITIONAL relation between them). First
# instance: s44's attest_expected_verdict_coupling.
# ================================================================================================
CROSS_COLUMN_COUPLING_MANIFEST = [
    dict(constraint="attest_expected_verdict_coupling", kind="model_identity_attested",
         col_a="attest_expected", col_b="attest_verdict", coupled_value="unevaluated",
         defining_delta="s44-model-identity-attestation.sql",
         reason="design/FABLE-OTEL-SENTRY-SPEC.md §8.2's fixed structural rule: "
                "(attest_expected IS NULL) = (attest_verdict = 'unevaluated') -- an unevaluated "
                "verdict with a declared expectation, or a match/mismatch claim with nothing to "
                "match against, is unrepresentable."),
]
CROSS_COLUMN_BY_CONNAME = {row["constraint"]: row for row in CROSS_COLUMN_COUPLING_MANIFEST}
assert len(CROSS_COLUMN_BY_CONNAME) == len(CROSS_COLUMN_COUPLING_MANIFEST), \
    "duplicate constraint in CROSS_COLUMN_COUPLING_MANIFEST -- SSOT violated"

# ================================================================================================
# MANDATORY_ON_KIND_MANIFEST -- a SIXTH manifest (see the _MANDATORY_ON_KIND_RE comment above):
# `kind <> 'K' OR col IS NOT NULL` -- a column MANDATORY on exactly one kind (the mirror image of
# FORBIDDEN-ON-KIND, which forbids rather than requires). Keyed (column, kind). First instance:
# s58's missive_disposition_mandatory_on_disposed.
# ================================================================================================
MANDATORY_ON_KIND_MANIFEST = [
    dict(column="missive_disposition", kind="missive_disposed",
         mechanism="CHECK", constraint="missive_disposition_mandatory_on_disposed",
         defining_delta="s58-missive-substrate.sql",
         reason="design/FABLE-MISSIVES-KERNEL-SPEC.md §2.3 note 2: the disposition event must "
                "carry a typed disposition -- mandatory on kind=missive_disposed. missive_"
                "disposition is ALSO legal (not mandatory) on an acknowledgment missive_sent row "
                "(missive_disposition_allowed_homes/KIND_OR_VALUE_MANIFEST below) and mandatory "
                "there too (missive_disposition_mandatory_on_ack, spelled off missive_act's VALUE, "
                "out of this manifest's scope by the classifier's first test -- no `kind` literal)."),
]
# AMENDMENT 1 (design/FABLE-MISSIVES-KERNEL-SPEC.md, 2026-07-25, maintainer-ratified "yes to the
# column") REMOVES the (regards, missive_disposed) row this manifest ORIGINALLY carried here --
# that row documented a genuine, witnessed-live conflict (regards is trigger-locked by s15's
# validate_review to kind='review' ONLY, refusing any non-review row naming it; a spec-literal
# build could never write a missive_disposed row). The amendment moves missive_disposed's
# subject to a NEW dedicated column, missive_regards -- regards and validate_review are
# UNTOUCHED, so no MANDATORY-ON-KIND (nor any other) fact about `regards` is added by s58/s59
# anymore; the conflict this row recorded no longer exists to record. missive_regards' own
# kind-shape correlation is an ORDINARY two-way iff (below, MANIFEST_BY_COLUMN, mechanism=CHECK)
# -- simpler than the MANDATORY-ON-KIND/FORBIDDEN-ON-KIND idiom pair, and sufficient: "FORBIDDEN
# on every kind except missive_disposed, MANDATORY there" IS a two-way iff by construction.
MANDATORY_ON_KIND_BY_KEY = {(row["column"], row["kind"]): row for row in MANDATORY_ON_KIND_MANIFEST}
assert len(MANDATORY_ON_KIND_BY_KEY) == len(MANDATORY_ON_KIND_MANIFEST), \
    "duplicate (column, kind) in MANDATORY_ON_KIND_MANIFEST -- SSOT violated"

# ================================================================================================
# KIND_OR_VALUE_MANIFEST -- a SEVENTH manifest (see the _KIND_OR_VALUE_RE comment above):
# `col IS NULL OR kind = 'K' OR other_col = 'V'` -- a value permitted on a WHOLE kind OR on one
# VALUE of a different, already kind-scoped column. Keyed by constraint name (both columns
# involved may already hold their own manifest rows; this tracks the ADDITIONAL three-way
# permission, not a competing shape for either alone). First instance: s58's
# missive_disposition_allowed_homes.
# ================================================================================================
KIND_OR_VALUE_MANIFEST = [
    dict(constraint="missive_disposition_allowed_homes", column="missive_disposition",
         kind="missive_disposed", other_column="missive_act", other_value="acknowledgment",
         defining_delta="s58-missive-substrate.sql",
         reason="design/FABLE-MISSIVES-KERNEL-SPEC.md §2.3 note 2: missive_disposition is legal "
                "on the disposition event (kind=missive_disposed) and on the acknowledgment "
                "missive_sent row (missive_act=acknowledgment) -- nowhere else. The value crosses "
                "TYPED in the acknowledgment, never prose-only (ADR-0008/ADR-0020)."),
]
KIND_OR_VALUE_BY_CONNAME = {row["constraint"]: row for row in KIND_OR_VALUE_MANIFEST}
assert len(KIND_OR_VALUE_BY_CONNAME) == len(KIND_OR_VALUE_MANIFEST), \
    "duplicate constraint in KIND_OR_VALUE_MANIFEST -- SSOT violated"

# CORE_COLUMNS: every OTHER live ledger column, confirmed NOT kind-scoped (see module docstring's
# "MANIFEST SCOPE" paragraph for how amends/amends_scope/answers were checked). A column that is
# neither in MANIFEST nor here is, by construction, an unlicensed payload column.
CORE_COLUMNS = frozenset({
    "id", "ts", "session", "kind", "statement", "rationale", "status", "evidence", "confidence",
    "supersedes", "refs", "concern", "enacts", "actor", "amends", "amends_scope", "answers",
    "stamp_session", "stamp_agent", "stamp_ts", "stamp_hmac", "stamp_verified",
    "stamp_invocation", "event_declared_ts", "row_hash",
    # s40: the actor-resolution mark is kind-agnostic by ratified design (basis §9(f)) -- every
    # row of any kind carries 'explicit'/'declared-default' from s40 onward (set_actor's own
    # assignment), NULL only on pre-s40 history. Its value CHECK carries no kind test.
    "principal_actor_resolution",
    # s61: signature_symmetry_witness is licensed on EVERY kind by design (Element 1's own
    # note) -- no kind-shape CHECK exists for it, mirroring `refs`' own structural/universal
    # standing above; its ONLY constraint is a target-KIND check (the row it names must be
    # commission_signature_verified), enforced by a trigger (validate_signature_witness), not a
    # CHECK on the CARRYING row's own kind.
    "signature_symmetry_witness",
})


# ================================================================================================
# THE GATE
# ================================================================================================

def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def _psql(schema_vars: dict[str, str], sql: str) -> subprocess.CompletedProcess:
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-tAq"]
    for k, v in schema_vars.items():
        args += ["-v", f"{k}={v}"]
    args += ["-c", sql]
    return sh(args)


def teardown(schema: str, kern: str, role: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE; "
        f"DROP OWNED BY {role};"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {role};"])


def apply_chain(schema: str, kern: str, role: str) -> None:
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for f in CHAIN:
        args += ["-f", str(LINEAGE / f)]
    cp = sh(args)
    if cp.returncode != 0:
        raise RuntimeError(f"chain apply FAILED:\n{cp.stdout[-2000:]}\n{cp.stderr[-2000:]}")


def catalog_columns(schema: str) -> list[str]:
    cp = _psql({}, f"SELECT column_name FROM information_schema.columns "
                    f"WHERE table_schema = '{schema}' AND table_name = 'ledger' "
                    f"ORDER BY ordinal_position;")
    if cp.returncode != 0:
        raise RuntimeError(f"catalog_columns FAILED: {cp.stderr}")
    return [ln.strip() for ln in cp.stdout.splitlines() if ln.strip()]


def catalog_check_defs(schema: str) -> dict[str, str]:
    """{conname: pg_get_constraintdef(...)} for every CHECK constraint on <schema>.ledger."""
    cp = _psql({}, f"""
        SELECT c.conname || chr(31) || pg_get_constraintdef(c.oid)
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = '{schema}' AND t.relname = 'ledger' AND c.contype = 'c';
    """)
    if cp.returncode != 0:
        raise RuntimeError(f"catalog_check_defs FAILED: {cp.stderr}")
    out = {}
    for ln in cp.stdout.splitlines():
        if not ln.strip():
            continue
        name, defn = ln.split(chr(31), 1)
        out[name] = defn
    return out


_KIND_EQ_RE = re.compile(r"kind = '([^']+)'")
_KIND_ANY_RE = re.compile(r"kind = ANY \(ARRAY\[([^\]]+)\]\)")
_ARRAY_ELEM_RE = re.compile(r"'([^']+)'")
_TWO_WAY_RE = re.compile(r"= \((\w+) IS NOT NULL\)")
_ONE_WAY_A_RE = re.compile(r"\((\w+) IS NULL\) OR \(kind")   # col IS NULL OR kind = ...
_ONE_WAY_B_RE = re.compile(r"kind[^()]*\)\)?\) OR \((\w+) IS NULL\)")  # kind = ... OR col IS NULL
# s37's work_resolution_check, witnessed live once the CHAIN below was extended through s37: a
# VALUE-VOCABULARY CHECK partitioned by kind (`col IS NULL OR (kind = 'K1' AND col = ANY(vals1))
# OR (kind = 'K2' AND col = ANY(vals2))`) -- matched generically on shape (a `kind = '<literal>'`
# branch AND-combined with a `col = ANY(...)` membership test on the SAME check), never by
# constraint name. See module docstring's NOT IN SCOPE section for why this is a distinct concern
# from the (kind, column, arity) SHAPE the two regexes above classify, not a competing shape for
# the same column.
_VOCAB_PARTITION_RE = re.compile(r"\(kind = '[^']+'[^()]*\)\s+AND\s+\(\w+ = ANY")
# s38's work_review_bookkeeping_kind_shape, witnessed live once the CHAIN below was extended
# through s38 (fresh reviewer finding, 2026-07-17): a PARTIAL-VALUE kind-shape CHECK, `<col> IS
# DISTINCT FROM '<literal>' OR kind = '<K>'` -- one-way, single-value granularity ("this ONE value
# of col is confined to kind K"), a genuine (kind, column)-correlation this codebase had no idiom
# for before s38. Matched generically on shape, never by constraint name, so a NEW PARTIAL-VALUE
# CHECK a future delta adds on a different (column, value) pair is caught the same way. See module
# docstring's "IN SCOPE, a THIRD manifest" paragraph and VALUE_PARTITION_MANIFEST below -- tracked
# in its OWN manifest, not folded into MANIFEST/MANIFEST_BY_COLUMN (see that manifest's own header
# comment for why: a column may already hold a whole-column MANIFEST row at a DIFFERENT
# granularity, exactly work_review_disposition's own case).
_PARTIAL_VALUE_RE = re.compile(r"(\w+) IS DISTINCT FROM '([^']+)'(?:::\w+)?\)\s*OR\s*\(kind")
# s43's write_refused_unretractable, witnessed live once the CHAIN was extended through s43:
# the FORBIDDEN-ON-KIND idiom, `(<col> IS NULL) OR (kind <> '<K>')` -- a column (possibly a
# CORE one: s43's instance is `supersedes`, the ratified R6) FORBIDDEN on exactly one kind,
# legal everywhere else. Matched generically on shape, never by constraint name, and checked
# BEFORE the generic one-way regexes below (whose _ONE_WAY_A_RE half-matches this text and
# would then land it UNPARSEABLE on the kind-NEGATION _extract_kinds cannot read). Tracked in
# its OWN manifest, FORBIDDEN_ON_KIND_MANIFEST, keyed (column, kind) -- never folded into
# MANIFEST_BY_COLUMN (one-shape-per-PAYLOAD-column; a core column's forbidden-kind is an
# additional, orthogonal correlation, exactly as VALUE_PARTITION_MANIFEST layers under a
# whole-column row).
_FORBIDDEN_ON_KIND_RE = re.compile(r"\((\w+) IS NULL\)\s*OR\s*\(kind <> '([^']+)'")
# s44's attest_expected_verdict_coupling, the FIFTH idiom this codebase's kind-shape CHECKs use
# (found authoring s44, kernel/lineage/s44-model-identity-attestation.sql): CROSS-COLUMN
# KIND-SCOPED COUPLING, `kind <> '<K>' OR ((<colA> IS NULL) = (<colB> = '<literal>'))` -- a
# same-kind structural coupling between TWO already-kind-scoped payload columns (contrast
# FORBIDDEN-ON-KIND, which relates ONE column's nullability to a kind-NEGATION; contrast
# PARTIAL-VALUE, which relates one column's ONE value to a kind; this idiom relates two
# columns' presence to EACH OTHER, gated by kind). Matched generically on shape, never by
# constraint name, and checked in the SAME early position as FORBIDDEN-ON-KIND (its own
# "kind <> " prefix would otherwise be unreadable by `_extract_kinds`, which reads only
# `kind = '...'`, landing it UNPARSEABLE). Tracked in its OWN manifest,
# CROSS_COLUMN_COUPLING_MANIFEST, keyed by constraint name -- both columns it couples are
# ALREADY licensed by their own individual MANIFEST_BY_COLUMN rows (attest_expected,
# attest_verdict); this manifest tracks the ADDITIONAL cross-column invariant, not a
# competing shape declaration for either column alone.
_CROSS_COLUMN_COUPLING_RE = re.compile(
    r"kind <> '([^']+)'(?:::\w+)?\)\s*OR\s*\(\((\w+) IS NULL\)\s*=\s*\((\w+) = '([^']+)'")
# s58's missive_disposition_mandatory_on_disposed, the SIXTH idiom (found authoring s58,
# kernel/lineage/s58-missive-substrate.sql): MANDATORY-ON-KIND, `kind <> '<K>' OR
# (<col> IS NOT NULL)` -- the mirror image of FORBIDDEN-ON-KIND (which negates the column;
# this negates the kind). Checked in the same early position as FORBIDDEN-ON-KIND/CROSS-COLUMN-
# COUPLING (its own "kind <>" prefix is the same _extract_kinds blind spot). Tracked in its own
# manifest, MANDATORY_ON_KIND_MANIFEST, keyed (column, kind).
_MANDATORY_ON_KIND_RE = re.compile(
    r"kind <> '([^']+)'(?:::\w+)?\)\s*OR\s*\((\w+) IS NOT NULL\)")
# s58's missive_disposition_allowed_homes, the SEVENTH idiom: KIND-OR-VALUE-PERMITTED,
# `(<col> IS NULL) OR (kind = '<K>') OR (<other_col> = '<V>')` -- a THREE-way disjunction: the
# value is permitted on a WHOLE kind OR on one VALUE of a DIFFERENT, already kind-scoped column.
# Checked in the same early position (shares FORBIDDEN-ON-KIND's/MANDATORY-ON-KIND's "(col IS
# NULL) OR (kind" false-match hazard against _ONE_WAY_A_RE). Tracked in its own manifest,
# KIND_OR_VALUE_MANIFEST, keyed by constraint name.
_KIND_OR_VALUE_RE = re.compile(
    r"\((\w+) IS NULL\)\s*OR\s*\(kind = '([^']+)'(?:::\w+)?\)\s*OR\s*\((\w+) = '([^']+)'(?:::\w+)?\)")


def _extract_kinds(defn: str) -> tuple[str, ...]:
    m = _KIND_ANY_RE.search(defn)
    if m:
        return tuple(_ARRAY_ELEM_RE.findall(m.group(1)))
    return tuple(_KIND_EQ_RE.findall(defn))


def classify_kind_shape(conname: str, defn: str):
    """Parse a single CHECK constraint definition. Returns None if it does not mention `kind` at
    all (an ordinary vocabulary/business-rule CHECK, out of this manifest's scope). Returns
    ("UNPARSEABLE", conname, defn) if it mentions `kind` but matches neither the two-way nor the
    one-way whole-column shape, nor the PARTIAL-VALUE single-value shape, this codebase's
    kind-shape CHECKs use (a NEW shape a future delta introduced, refused loudly rather than
    silently skipped -- ADR-0002). Returns ("PARTIAL-VALUE", column, value, kinds, conname) for
    the single-value idiom (see _PARTIAL_VALUE_RE above). Otherwise returns
    (column, kinds, arity)."""
    if "kind" not in defn:
        return None
    m_kv = _KIND_OR_VALUE_RE.search(defn)
    if m_kv:
        # checked FIRST, ahead of FORBIDDEN-ON-KIND/MANDATORY-ON-KIND/_ONE_WAY_A_RE: its own
        # "(col IS NULL) OR (kind" prefix is the identical false-match hazard those pose for each
        # other, and it is the MOST specific of the three shapes (three captured groups) so it
        # must win the match before a shorter idiom's regex partially consumes the same text.
        col, kind, other_col, other_val = m_kv.group(1), m_kv.group(2), m_kv.group(3), m_kv.group(4)
        if "kind" in (col, other_col):
            return ("UNPARSEABLE", conname, defn)
        return ("KIND-OR-VALUE", col, kind, other_col, other_val, conname)
    m_mk = _MANDATORY_ON_KIND_RE.search(defn)
    if m_mk:
        kind, col = m_mk.group(1), m_mk.group(2)
        if col == "kind":
            return ("UNPARSEABLE", conname, defn)
        return ("MANDATORY-ON-KIND", col, kind, conname)
    m_fk = _FORBIDDEN_ON_KIND_RE.search(defn)
    if m_fk:
        # checked FIRST: this idiom carries "IS NULL" and a bare `(col IS NULL) OR (kind`
        # prefix, so _ONE_WAY_A_RE would half-match it and _extract_kinds (which reads only
        # `kind = '...'`, never `kind <> '...'`) would then return empty -- UNPARSEABLE. A
        # dedicated branch, matched on the kind-NEGATION shape (s43's
        # write_refused_unretractable, the first instance).
        col, forbidden_kind = m_fk.group(1), m_fk.group(2)
        if col == "kind":
            return ("UNPARSEABLE", conname, defn)
        return ("FORBIDDEN-ON-KIND", col, forbidden_kind, conname)
    m_cc = _CROSS_COLUMN_COUPLING_RE.search(defn)
    if m_cc:
        # checked in the same early position as FORBIDDEN-ON-KIND, for the same reason: its
        # "kind <> '<K>'" prefix is unreadable by `_extract_kinds` (which reads only
        # `kind = '...'`), so leaving it to the generic path would land it UNPARSEABLE.
        kind, col_a, col_b, literal = m_cc.group(1), m_cc.group(2), m_cc.group(3), m_cc.group(4)
        if "kind" in (col_a, col_b):
            return ("UNPARSEABLE", conname, defn)
        return ("CROSS-COLUMN-COUPLING", kind, col_a, col_b, literal, conname)
    m_pv = _PARTIAL_VALUE_RE.search(defn)
    if m_pv:
        # checked BEFORE the "IS NULL"/"IS NOT NULL" entry filter below: this idiom is phrased
        # with `IS DISTINCT FROM`, never `IS NULL`/`IS NOT NULL`, so it would otherwise be
        # silently swallowed by that filter exactly as work_review_bookkeeping_kind_shape was
        # (the fresh reviewer finding this fix repairs, 2026-07-17).
        col, literal = m_pv.group(1), m_pv.group(2)
        kinds = _extract_kinds(defn)
        if col == "kind" or not kinds:
            # degenerate/unrecognized variant of the idiom -- refuse loudly rather than guess.
            return ("UNPARSEABLE", conname, defn)
        return ("PARTIAL-VALUE", col, literal, kinds, conname)
    if "IS NULL" not in defn and "IS NOT NULL" not in defn:
        # a pure kind-VOCABULARY CHECK (e.g. ledger_kind_check's `kind = ANY (ARRAY[...])`) --
        # constrains kind's own legal values, correlates it with no OTHER column's nullability,
        # so it is not a "shape" CHECK in F5's sense at all. Out of this manifest's scope.
        return None
    if _VOCAB_PARTITION_RE.search(defn):
        # a VALUE-VOCABULARY CHECK partitioned by kind (s37's work_resolution_check) -- carries
        # its own nullable-escape disjunct ("col IS NULL OR ...") so it does NOT skip on the
        # branch above, but its per-branch AND-combination of a `kind = '<literal>'` test with a
        # `col = ANY(...)` membership test means it constrains WHICH VALUES are legal per kind,
        # not WHETHER the column may be non-NULL per kind -- a different concern from the (kind,
        # column, arity) SHAPE this manifest tracks, one level below a shape this same column
        # already carries its own MANIFEST row for. Out of this manifest's scope (module
        # docstring's NOT IN SCOPE section); never silently dropped, matched generically.
        return None
    kinds = _extract_kinds(defn)
    if not kinds:
        # mentions the bare word "kind" with no `kind = ...` / `kind = ANY(...)` predicate at
        # all -- not a shape CHECK this manifest's vocabulary covers (none exist today; refused
        # loudly rather than silently treated as core).
        return ("UNPARSEABLE", conname, defn)
    m2 = _TWO_WAY_RE.search(defn)
    if m2 and m2.group(1) != "kind":
        return (m2.group(1), kinds, "two-way")
    m1a = _ONE_WAY_A_RE.search(defn)
    if m1a:
        return (m1a.group(1), kinds, "one-way")
    m1b = _ONE_WAY_B_RE.search(defn)
    if m1b:
        return (m1b.group(1), kinds, "one-way")
    return ("UNPARSEABLE", conname, defn)


def assert_manifest(schema: str) -> list[str]:
    """The core check, independent of scratch-schema lifecycle (unit-testable). Returns a list
    of violation strings; empty means clean."""
    violations: list[str] = []
    columns = set(catalog_columns(schema))
    check_defs = catalog_check_defs(schema)

    # 1. classify every CHECK constraint that mentions `kind`
    catalog_shapes: dict[str, tuple] = {}   # column -> (kinds, arity, conname)
    partial_value_shapes: dict[tuple[str, str], tuple] = {}   # (column, value) -> (kinds, conname)
    forbidden_shapes: dict[tuple[str, str], str] = {}   # (column, kind) -> conname
    cross_column_shapes: dict[str, tuple] = {}   # conname -> (kind, col_a, col_b, literal)
    mandatory_on_kind_shapes: dict[tuple[str, str], str] = {}   # (column, kind) -> conname
    kind_or_value_shapes: dict[str, tuple] = {}   # conname -> (col, kind, other_col, other_val)
    for conname, defn in check_defs.items():
        parsed = classify_kind_shape(conname, defn)
        if parsed is None:
            continue
        if parsed[0] == "MANDATORY-ON-KIND":
            _, col, mkind, _conname = parsed
            key = (col, mkind)
            if key in mandatory_on_kind_shapes:
                violations.append(
                    f"(column, kind) {key!r} carries MULTIPLE MANDATORY-ON-KIND CHECKs "
                    f"({mandatory_on_kind_shapes[key]!r} and {conname!r}) -- one home only.")
                continue
            mandatory_on_kind_shapes[key] = conname
            continue
        if parsed[0] == "KIND-OR-VALUE":
            _, col, kv_kind, other_col, other_val, _conname = parsed
            kind_or_value_shapes[conname] = (col, kv_kind, other_col, other_val)
            continue
        if parsed[0] == "FORBIDDEN-ON-KIND":
            _, col, fkind, _conname = parsed
            key = (col, fkind)
            if key in forbidden_shapes:
                violations.append(
                    f"(column, kind) {key!r} carries MULTIPLE FORBIDDEN-ON-KIND CHECKs "
                    f"({forbidden_shapes[key]!r} and {conname!r}) -- one home only.")
                continue
            forbidden_shapes[key] = conname
            continue
        if parsed[0] == "CROSS-COLUMN-COUPLING":
            _, kind, col_a, col_b, literal, _conname = parsed
            cross_column_shapes[conname] = (kind, col_a, col_b, literal)
            continue
        if parsed[0] == "UNPARSEABLE":
            violations.append(
                f"UNPARSEABLE kind-mentioning CHECK {parsed[1]!r} ({parsed[2]!r}) -- this "
                f"gate's classifier recognizes only the seven shapes MANIFEST/"
                f"VALUE_PARTITION_MANIFEST/FORBIDDEN_ON_KIND_MANIFEST/"
                f"CROSS_COLUMN_COUPLING_MANIFEST/MANDATORY_ON_KIND_MANIFEST/"
                f"KIND_OR_VALUE_MANIFEST declare (two-way iff, one-way implication, "
                f"PARTIAL-VALUE single-value implication, FORBIDDEN-ON-KIND, "
                f"CROSS-COLUMN-COUPLING, MANDATORY-ON-KIND, KIND-OR-VALUE-PERMITTED). Either "
                f"this is a NEW kind-shape idiom (extend classify_kind_shape and the relevant "
                f"manifest together) or it is not truly kind-scoped (rename it off 'kind' to "
                f"stop tripping this gate).")
            continue
        if parsed[0] == "PARTIAL-VALUE":
            _, col, literal, kinds, _conname = parsed
            key = (col, literal)
            if key in partial_value_shapes:
                violations.append(
                    f"(column, value) {key!r} carries MULTIPLE PARTIAL-VALUE kind-shape CHECKs "
                    f"({partial_value_shapes[key][1]!r} and {conname!r}) -- one home only.")
                continue
            partial_value_shapes[key] = (kinds, conname)
            continue
        col, kinds, arity = parsed
        if col in catalog_shapes:
            violations.append(f"column {col!r} carries MULTIPLE kind-shape CHECKs "
                               f"({catalog_shapes[col][2]!r} and {conname!r}) -- one home only.")
            continue
        catalog_shapes[col] = (kinds, arity, conname)

    # 2. every catalog kind-shape CHECK must match its MANIFEST row exactly
    for col, (kinds, arity, conname) in catalog_shapes.items():
        row = MANIFEST_BY_COLUMN.get(col)
        if row is None:
            violations.append(
                f"UNLICENSED PAYLOAD COLUMN {col!r}: catalog CHECK {conname!r} ties it to "
                f"kind, but no MANIFEST row declares it. Add it to MANIFEST in "
                f"gates/kind_shape_manifest_gate.py (kind(s)={kinds}, arity={arity!r}), or "
                f"remove the column/constraint if it should not exist.")
            continue
        if row["mechanism"] != "CHECK":
            violations.append(
                f"column {col!r}: MANIFEST declares mechanism={row['mechanism']!r} but the "
                f"catalog carries a CHECK ({conname!r}) -- shape drifted from its licensed "
                f"mechanism.")
            continue
        if row["arity"] != arity:
            violations.append(
                f"column {col!r}: MANIFEST declares arity={row['arity']!r}, catalog CHECK "
                f"{conname!r} is {arity!r} -- shape drifted.")
        if set(row["kinds"]) != set(kinds):
            violations.append(
                f"column {col!r}: MANIFEST declares kinds={row['kinds']}, catalog CHECK "
                f"{conname!r} covers kinds={kinds} -- shape drifted.")

    # 3. every MANIFEST row must exist in the catalog, one way or the other
    for row in MANIFEST:
        col = row["column"]
        if row["mechanism"] == "CHECK":
            if col not in catalog_shapes:
                violations.append(
                    f"MANIFEST row for column {col!r} declares mechanism=CHECK "
                    f"(constraint={row['constraint']!r}) but no such CHECK exists in the live "
                    f"catalog -- stale manifest row or a dropped constraint.")
        elif row["mechanism"] == "trigger":
            if col in catalog_shapes:
                violations.append(
                    f"MANIFEST row for column {col!r} declares mechanism=trigger but the "
                    f"catalog NOW carries a kind-shape CHECK on it too -- update MANIFEST to "
                    f"mechanism=CHECK (and record the new constraint name) or explain the "
                    f"redundancy.")
        else:
            violations.append(f"MANIFEST row for column {col!r} declares an unrecognized "
                               f"mechanism {row['mechanism']!r}.")

    # 2b. every catalog PARTIAL-VALUE CHECK must match its VALUE_PARTITION_MANIFEST row exactly
    for (col, literal), (kinds, conname) in partial_value_shapes.items():
        row = VALUE_PARTITION_BY_KEY.get((col, literal))
        if row is None:
            violations.append(
                f"UNLICENSED PAYLOAD COLUMN {col!r} value {literal!r}: catalog CHECK {conname!r} "
                f"ties this ONE value to kind, but no VALUE_PARTITION_MANIFEST row declares it. "
                f"Add it to VALUE_PARTITION_MANIFEST in gates/kind_shape_manifest_gate.py "
                f"(kind(s)={kinds}), or remove the column/constraint if it should not exist.")
            continue
        if row["mechanism"] != "CHECK":
            violations.append(
                f"column {col!r} value {literal!r}: VALUE_PARTITION_MANIFEST declares "
                f"mechanism={row['mechanism']!r} but the catalog carries a CHECK ({conname!r}) -- "
                f"shape drifted from its licensed mechanism.")
            continue
        if set(row["kinds"]) != set(kinds):
            violations.append(
                f"column {col!r} value {literal!r}: VALUE_PARTITION_MANIFEST declares "
                f"kinds={row['kinds']}, catalog CHECK {conname!r} covers kinds={kinds} -- shape "
                f"drifted.")

    # 3b. every VALUE_PARTITION_MANIFEST row must exist in the catalog
    for row in VALUE_PARTITION_MANIFEST:
        key = (row["column"], row["value"])
        if row["mechanism"] == "CHECK" and key not in partial_value_shapes:
            violations.append(
                f"VALUE_PARTITION_MANIFEST row for column {row['column']!r} value "
                f"{row['value']!r} declares mechanism=CHECK (constraint={row['constraint']!r}) "
                f"but no such CHECK exists in the live catalog -- stale manifest row or a dropped "
                f"constraint.")

    # 2c. every catalog FORBIDDEN-ON-KIND CHECK must match its FORBIDDEN_ON_KIND_MANIFEST row
    for (col, fkind), conname in forbidden_shapes.items():
        row = FORBIDDEN_BY_KEY.get((col, fkind))
        if row is None:
            violations.append(
                f"UNLICENSED FORBIDDEN-ON-KIND CHECK {conname!r}: column {col!r} is forbidden "
                f"on kind {fkind!r} by the catalog, but no FORBIDDEN_ON_KIND_MANIFEST row "
                f"declares it. Add it to FORBIDDEN_ON_KIND_MANIFEST in "
                f"gates/kind_shape_manifest_gate.py with its reason, or remove the constraint "
                f"if it should not exist.")
    # 3c. every FORBIDDEN_ON_KIND_MANIFEST row must exist in the catalog
    for row in FORBIDDEN_ON_KIND_MANIFEST:
        key = (row["column"], row["kind"])
        if row["mechanism"] == "CHECK" and key not in forbidden_shapes:
            violations.append(
                f"FORBIDDEN_ON_KIND_MANIFEST row for column {row['column']!r} kind "
                f"{row['kind']!r} declares mechanism=CHECK (constraint={row['constraint']!r}) "
                f"but no such CHECK exists in the live catalog -- stale manifest row or a "
                f"dropped constraint.")

    # 2d. every catalog CROSS-COLUMN-COUPLING CHECK must match its
    #     CROSS_COLUMN_COUPLING_MANIFEST row exactly
    for conname, (kind, col_a, col_b, literal) in cross_column_shapes.items():
        row = CROSS_COLUMN_BY_CONNAME.get(conname)
        if row is None:
            violations.append(
                f"UNLICENSED CROSS-COLUMN-COUPLING CHECK {conname!r}: couples {col_a!r} and "
                f"{col_b!r} (kind {kind!r}, literal {literal!r}) by the catalog, but no "
                f"CROSS_COLUMN_COUPLING_MANIFEST row declares it. Add it to "
                f"CROSS_COLUMN_COUPLING_MANIFEST in gates/kind_shape_manifest_gate.py with its "
                f"reason, or remove the constraint if it should not exist.")
            continue
        if (row["kind"], row["col_a"], row["col_b"], row["coupled_value"]) != (kind, col_a, col_b, literal):
            violations.append(
                f"CROSS-COLUMN-COUPLING CHECK {conname!r}: catalog shape (kind={kind!r}, "
                f"col_a={col_a!r}, col_b={col_b!r}, literal={literal!r}) disagrees with "
                f"CROSS_COLUMN_COUPLING_MANIFEST's declared "
                f"(kind={row['kind']!r}, col_a={row['col_a']!r}, col_b={row['col_b']!r}, "
                f"coupled_value={row['coupled_value']!r}) -- shape drifted.")
    # 3d. every CROSS_COLUMN_COUPLING_MANIFEST row must exist in the catalog
    for row in CROSS_COLUMN_COUPLING_MANIFEST:
        if row["constraint"] not in cross_column_shapes:
            violations.append(
                f"CROSS_COLUMN_COUPLING_MANIFEST row for constraint {row['constraint']!r} "
                f"declares a CROSS-COLUMN-COUPLING CHECK but no such CHECK exists in the live "
                f"catalog -- stale manifest row or a dropped constraint.")

    # 2e. every catalog MANDATORY-ON-KIND CHECK must match its MANDATORY_ON_KIND_MANIFEST row
    for (col, mkind), conname in mandatory_on_kind_shapes.items():
        row = MANDATORY_ON_KIND_BY_KEY.get((col, mkind))
        if row is None:
            violations.append(
                f"UNLICENSED MANDATORY-ON-KIND CHECK {conname!r}: column {col!r} is mandatory "
                f"on kind {mkind!r} by the catalog, but no MANDATORY_ON_KIND_MANIFEST row "
                f"declares it. Add it to MANDATORY_ON_KIND_MANIFEST in "
                f"gates/kind_shape_manifest_gate.py with its reason, or remove the constraint "
                f"if it should not exist.")
    # 3e. every MANDATORY_ON_KIND_MANIFEST row must exist in the catalog
    for row in MANDATORY_ON_KIND_MANIFEST:
        key = (row["column"], row["kind"])
        if row["mechanism"] == "CHECK" and key not in mandatory_on_kind_shapes:
            violations.append(
                f"MANDATORY_ON_KIND_MANIFEST row for column {row['column']!r} kind "
                f"{row['kind']!r} declares mechanism=CHECK (constraint={row['constraint']!r}) "
                f"but no such CHECK exists in the live catalog -- stale manifest row or a "
                f"dropped constraint.")

    # 2f. every catalog KIND-OR-VALUE CHECK must match its KIND_OR_VALUE_MANIFEST row exactly
    for conname, (col, kv_kind, other_col, other_val) in kind_or_value_shapes.items():
        row = KIND_OR_VALUE_BY_CONNAME.get(conname)
        if row is None:
            violations.append(
                f"UNLICENSED KIND-OR-VALUE-PERMITTED CHECK {conname!r}: column {col!r} permitted "
                f"on kind {kv_kind!r} OR {other_col!r}={other_val!r} by the catalog, but no "
                f"KIND_OR_VALUE_MANIFEST row declares it. Add it with its reason, or remove the "
                f"constraint if it should not exist.")
            continue
        if (row["column"], row["kind"], row["other_column"], row["other_value"]) != (col, kv_kind, other_col, other_val):
            violations.append(
                f"KIND-OR-VALUE-PERMITTED CHECK {conname!r}: catalog shape disagrees with "
                f"KIND_OR_VALUE_MANIFEST's declared shape -- drifted.")
    # 3f. every KIND_OR_VALUE_MANIFEST row must exist in the catalog
    for row in KIND_OR_VALUE_MANIFEST:
        if row["constraint"] not in kind_or_value_shapes:
            violations.append(
                f"KIND_OR_VALUE_MANIFEST row for constraint {row['constraint']!r} declares a "
                f"KIND-OR-VALUE-PERMITTED CHECK but no such CHECK exists in the live catalog -- "
                f"stale manifest row or a dropped constraint.")

    # 4. every payload-like (non-core) column must be licensed, whether or not it carries a
    #    catalog CHECK -- this is what catches a column with NO CHECK at all (the seen-red case:
    #    mechanism="CHECK"-shaped hazard that never got its CHECK written).
    # s58's missive_disposition carries NO MANIFEST_BY_COLUMN row of its own (its shape is the
    # COMPOUND of two new manifests, MANDATORY_ON_KIND_MANIFEST + KIND_OR_VALUE_MANIFEST -- see
    # this file's own CHAIN-section comment on s58) -- columns fully licensed via either of those
    # two manifests are exempted from the bare MANIFEST_BY_COLUMN test here, the same way a
    # FORBIDDEN_ON_KIND_MANIFEST-only column (none exist today; supersedes is also CORE) would be.
    _mandatory_only_cols = {row["column"] for row in MANDATORY_ON_KIND_MANIFEST}
    _kind_or_value_cols = {row["column"] for row in KIND_OR_VALUE_MANIFEST}
    for col in columns:
        if (col in CORE_COLUMNS or col in MANIFEST_BY_COLUMN
                or col in _mandatory_only_cols or col in _kind_or_value_cols):
            continue
        violations.append(
            f"UNLICENSED PAYLOAD COLUMN {col!r}: not in CORE_COLUMNS (structural/universal) and "
            f"not in MANIFEST (kind-scoped payload) -- an unlicensed column. Discharge paths: "
            f"(a) add a MANIFEST row naming its (kind(s), arity, mechanism, reason) if it is "
            f"genuinely kind-scoped payload, or (b) remove the column if it should not exist.")

    return violations


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-scratch", action="store_true",
                     help="leave the scratch schema/kernel/role standing (debug only)")
    ap.add_argument("--inject-column", default=None,
                     help="seen-red negative control: after the real chain applies, add this "
                          "column (no CHECK) before asserting -- must be REFUSED")
    a = ap.parse_args(argv)

    if a.inject_column is not None:
        # ADR-0012 interpreter-boundary amendment: --inject-column is spliced directly into
        # `ALTER TABLE ... ADD COLUMN` SQL text below (an f-string, no bound carrier for a
        # column-name literal) -- validated to the same closed alphabet
        # filing/deployment_record.py's schema/kern/role fields already are, refused here at the
        # argparse boundary before any SQL is built, never coerced/escaped into a plausible name.
        try:
            deployment_record.validate_sql_identifier("--inject-column", a.inject_column)
        except deployment_record.DeploymentError as e:
            print(f"kind-shape-manifest-gate: REFUSED -- {e}")
            return 2

    suffix = "kbmg"
    schema, kern, role = f"{suffix}_scratch", f"{suffix}_scratch_kernel", f"{suffix}_scratch_rw"
    teardown(schema, kern, role)   # pre-clean: never trust residue from a prior interrupted run
    try:
        apply_chain(schema, kern, role)
        if a.inject_column:
            cp = _psql({}, f"ALTER TABLE {schema}.ledger ADD COLUMN {a.inject_column} text;")
            if cp.returncode != 0:
                print(f"kind-shape-manifest-gate: --inject-column FAILED: {cp.stderr}")
                return 2
        violations = assert_manifest(schema)
    except RuntimeError as exc:
        print(f"kind-shape-manifest-gate: SCRATCH APPLY ERROR -- {exc}")
        return 2
    finally:
        if not a.keep_scratch:
            teardown(schema, kern, role)
        else:
            print(f"kind-shape-manifest-gate: --keep-scratch -- schema={schema} kern={kern} "
                  f"role={role} left standing, teardown it yourself when done")

    if violations:
        print(f"kind-shape-manifest-gate: {len(violations)} violation(s):\n")
        for v in violations:
            print(f"  !! {v}")
        return 1
    print(f"kind-shape-manifest-gate: clean -- {len(MANIFEST)} MANIFEST row(s) + "
          f"{len(VALUE_PARTITION_MANIFEST)} VALUE_PARTITION_MANIFEST row(s) + "
          f"{len(FORBIDDEN_ON_KIND_MANIFEST)} FORBIDDEN_ON_KIND_MANIFEST row(s) + "
          f"{len(CROSS_COLUMN_COUPLING_MANIFEST)} CROSS_COLUMN_COUPLING_MANIFEST row(s) match "
          f"the live catalog exactly, {len(CORE_COLUMNS)} core column(s) accounted for, no "
          f"unlicensed payload column. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
