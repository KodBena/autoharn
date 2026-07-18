#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T20:19:45Z
#   last-change: 2026-07-18T01:55:12Z
#   contributors: a857c93d/main, 9a17b6b9/main, ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""kind_shape_manifest_gate -- MANIFEST + GATE for the kernel ledger's kind-scoped shape
invariants (ledger item `kind-shape-manifest-gate`, per
design/ORCH-CATEGORICAL-REFACTOR-CONSULT-2026-07-15.md finding F5 / plan step 6).

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
]
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
                "principal_competence_granted"),
         arity="two-way", mechanism="CHECK", constraint="principal_binding_active_kind_shape",
         defining_delta="s41-principal-bindings-and-relations.sql",
         reason="the identity/value discriminator of the four binding kinds (true = assertion, "
                "false = retraction restating identity fields only) -- mandatory via this CHECK "
                "on exactly the four s41 kinds, never a column-level NOT NULL (basis C10); "
                "vacuous validation, kinds born in the same delta. Its inactive-needs-supersedes "
                "and mandatory-iff-active companions carry no kind test (value CHECKs, out of "
                "scope by the classifier's first test)."),
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
    dict(column="principal_role_name", kinds=("principal_role_bound",),
         arity="two-way", mechanism="CHECK", constraint="principal_role_name_kind_shape",
         defining_delta="s41-principal-bindings-and-relations.sql",
         reason="identity field, mandatory active or not. FREE non-empty text by RATIFIED "
                "ruling (basis §9(c)/C13, witnessed rows 1432/1433): role naming is "
                "organizational configuration -- deliberately NO value vocabulary CHECK exists "
                "for this column, only non-emptiness."),
    dict(column="principal_key_fingerprint", kinds=("principal_key_bound",),
         arity="two-way", mechanism="CHECK", constraint="principal_key_fingerprint_kind_shape",
         defining_delta="s41-principal-bindings-and-relations.sql",
         reason="identity field; the OpenPGP v4 shape is a separate kind-free value CHECK "
                "(principal_key_fingerprint_shape); the human-subject-only rule is D-3's "
                "trigger, not a CHECK (cross-table lookup)."),
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
]
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
    for conname, defn in check_defs.items():
        parsed = classify_kind_shape(conname, defn)
        if parsed is None:
            continue
        if parsed[0] == "UNPARSEABLE":
            violations.append(
                f"UNPARSEABLE kind-mentioning CHECK {parsed[1]!r} ({parsed[2]!r}) -- this "
                f"gate's classifier recognizes only the three shapes MANIFEST/"
                f"VALUE_PARTITION_MANIFEST declare (two-way iff, one-way implication, "
                f"PARTIAL-VALUE single-value implication). Either this is a NEW kind-shape idiom "
                f"(extend classify_kind_shape and the relevant manifest together) or it is not "
                f"truly kind-scoped (rename it off 'kind' to stop tripping this gate).")
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

    # 4. every payload-like (non-core) column must be licensed, whether or not it carries a
    #    catalog CHECK -- this is what catches a column with NO CHECK at all (the seen-red case:
    #    mechanism="CHECK"-shaped hazard that never got its CHECK written).
    for col in columns:
        if col in CORE_COLUMNS or col in MANIFEST_BY_COLUMN:
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
          f"{len(VALUE_PARTITION_MANIFEST)} VALUE_PARTITION_MANIFEST row(s) match the live "
          f"catalog exactly, {len(CORE_COLUMNS)} core column(s) accounted for, no unlicensed "
          f"payload column. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
