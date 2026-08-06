#!/usr/bin/env python3
"""seen-red/boundary-read-surface/run_fixtures.py -- WR1-WR6, design/
FABLE-BOUNDARY-READ-SURFACE-SPEC.md §"Witnesses" (ratified ledger decision row 1652, amending
design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md, ledger row 1631); WR6 added under ledger
rows 153/154 (view-registry-decomposition-views / rows-bulk-superseded-read). Real infra, no
mocks: a CLASSIC-scaffolded world through the full kernel/lineage chain (s15..s59 -- CHAIN_FULL's
own comment below has the full history of the pre-existing s58/s59 gap this build closed, and
why s59 rather than the true s68 lineage head), so every one of `VIEW_REGISTRY`'s members is a
genuinely present relation, not merely a capability_absent leg --
WR1's "per view, not umbrella" bar needs a world where every view actually exists), a real
`serving.boundary_service` uvicorn subprocess bound to loopback.

REUSE, NOT RE-DERIVATION (ADR-0012 P1): every scaffolding helper below (`scaffold_classic`,
`birth_via_boundary`, `teardown`, `psql_tuples`, `psql_raw`, `sh`, `check`, `free_port`,
`start_server`, `wait_health`, `http_get`, `http_post`, `write_scratch_multiplex_config`,
`write_scratch_deployment`, `stop_server`, `RUN_SUFFIX`, `CHAIN_B`, `PGHOST`, `PGDB`) is IMPORTED
from `seen-red/boundary-service/run_fixtures.py`, the SAME pattern `seen-red/boundary-multiplex/
run_fixtures.py` already established for its own WM1-WM4 -- this file adds ONLY what the read-
surface amendment needs: the extended CHAIN_FULL (through s50), a small birthing sequence that
populates each allowlisted view with at least one row (so WR1 is never a vacuous empty-vs-empty
pass except where noted), and the five witnesses themselves.

WORLD: one CLASSIC s50-headed world, birthed through the boundary (WORLD B's own s40/s43 ceremony)
plus one small fixture-birthing pass over the boundary's OWN write routes (never a raw INSERT --
this fixture is itself a served-boundary consumer, proving the write path as a side effect).

Usage: python3 seen-red/boundary-read-surface/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SIBLING = REPO / "seen-red" / "boundary-service" / "run_fixtures.py"
# The LEGACY (direct-psql) original -- WR3's whole point is comparing the SERVED /rows/asof
# route against this tool's own independent read, so this must NOT resolve to the now-rebased
# bootstrap/templates/asof-export.tmpl (the served client this same suite is testing).
ASOF_EXPORT_TMPL = REPO / "bootstrap" / "templates" / "legacy-asof-export.tmpl"

sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "serving"))
sys.path.insert(0, str(REPO / "bootstrap"))
import deployment_record  # noqa: E402  (boundary_service's own import chain expects filing/ on sys.path first)
import boundary_service  # noqa: E402  (VIEW_REGISTRY -- the ONE enumeration authority, never re-typed here)
import boundary_cli_client  # noqa: E402  (round-3 fix, ledger rows 153/154: the PRODUCTION pagination walker -- walk_paginated below delegates to it rather than re-deriving a second one)
import migrate_core  # noqa: E402  (bootstrap/migrate_core.py -- the SAME manifest _lineage_head reuses, for WR4's ground truth)

import os
# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

# The sibling module is loaded by FILE PATH (hyphenated directory names are not valid Python
# package components), under its own distinct module name -- the same trick seen-red/
# boundary-multiplex/run_fixtures.py already uses for the identical reason.
_spec = importlib.util.spec_from_file_location("boundary_service_fixtures", SIBLING)
assert _spec is not None and _spec.loader is not None
bs_fixtures = importlib.util.module_from_spec(_spec)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_spec.loader.exec_module(bs_fixtures)

# asof-export.tmpl is loaded the SAME way -- WR3 needs its `ledger_asof_rows` function called
# DIRECTLY (not via stdout-parsing a CLI invocation), so the served /rows/asof/{ts} route's own
# output can be compared against the legacy tool's own row-set, byte-for-byte, without a fragile
# text-format round trip.
_aspec = importlib.util.spec_from_file_location(
    "asof_export_tmpl", ASOF_EXPORT_TMPL,
    loader=importlib.machinery.SourceFileLoader("asof_export_tmpl", str(ASOF_EXPORT_TMPL)))
assert _aspec is not None and _aspec.loader is not None
asof_export = importlib.util.module_from_spec(_aspec)
sys.modules["asof_export_tmpl"] = asof_export
_aspec.loader.exec_module(asof_export)

RUN_SUFFIX = bs_fixtures.RUN_SUFFIX
CHAIN_B = bs_fixtures.CHAIN_B
PGHOST, PGDB = bs_fixtures.PGHOST, bs_fixtures.PGDB
check = bs_fixtures.check

# The full kernel/lineage chain through s59 -- every VIEW_REGISTRY member is a genuinely present
# relation on this chain (s44 model_attestations, s46 credited_current/model_defeated_rows, s36
# standing_decisions -- none of which CHAIN_B alone, s43-headed, carries; s56's
# reservations_outstanding/review_verdicts are two more; s59's SIX missive_* views are the newest
# before this build's own five). PRE-EXISTING HAZARD FOUND AND FIXED IN REACH (CLAUDE.md's
# engineering-responsibility rule -- this exact CHAIN_FULL constant and this exact WR1 loop are
# already being touched by this build's own birth_fixture_rows/WR6 additions): this constant used
# to stop at s57, one short of s58/s59 (design/FABLE-MISSIVES-KERNEL-SPEC.md, ledger row 1263) --
# the missive_* views had been added to VIEW_REGISTRY under that spec WITHOUT ever extending this
# fixture's own chain, so WR1's per-view loop 500'd (a bare `relation ... does not exist`, not a
# typed refusal) the moment it reached any missive_* member, on the UNMODIFIED baseline, before
# this build's own five-view addition ever ran -- witnessed live (both files stashed back to
# HEAD, re-run, same failure) rather than assumed. STOPPED at s59, not carried further to the
# true s68 lineage head, on the SAME no-retroactive-sweep grounds ADR-0000's Neutral clause
# names: s61 (design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md) adds a `key_binding_possession_ref`
# requirement to `principal_key_bound` this fixture's own possession-proof-free birth cannot
# satisfy without a whole signature ceremony unrelated to this commission's own two work items --
# witnessed live too (chain extended to s68, SAME birth ceremony, refused: "must name a
# key_binding_possession_ref"). `_current_head_and_missing` detects the lineage head PER WORLD
# (bootstrap/migrate_core.py), not against a hardcoded repo-wide constant, so WR4's served-vs-
# actual comparison stays internally consistent at s59 -- stopping here does not make WR4 dishonest,
# it just means this fixture's own world is not (and was never, even at s57) claiming to be the
# repo's bleeding-edge head, only a genuinely self-consistent one.
CHAIN_FULL = CHAIN_B + [
    "s44-model-identity-attestation.sql", "s45-standing-lifecycle.sql",
    "s46-credited-views.sql", "s47-claim-on-closed-refusal.sql",
    "s48-review-witness-existence.sql", "s49-journaler-overflow-guard.sql",
    "s50-defeat-input-raw-domain.sql", "s51-artifact-store.sql",
    "s52-artifact-witness-check.sql", "s53-belief-substrate.sql",
    "s54-belief-views.sql", "s55-dispatch-grain-independence.sql",
    "s56-reservation-residue.sql", "s57-obligation-revocation-event.sql",
    "s58-missive-substrate.sql", "s59-missive-views.sql",
]

# MODERATE finding, fix round (ledger rows 153/154, coordinator fresh-context review of commit
# 6a104c0): CHAIN_FULL above stops at s59 for a DOCUMENTED reason (s61's key_binding_possession_
# ref requirement blocks THIS FILE's own birth_fixture_rows ceremony -- see CHAIN_FULL's own
# comment). That means the MAIN wrfx world's WR1 pass validates countersigned_in_force's PRE-s68
# shape (s67-headed, missing the two refusal-disposition columns kernel/lineage/
# s68-typed-absence-dispositions.sql appends), not the true, current shape ledger row 153's own
# build actually shipped. CHAIN_S68 is a SEPARATE chain, for a SEPARATE, minimal world (WR7
# below) that reaches the true head WITHOUT the s61 blocker: it never attempts a
# principal_key_bound act (the ONE act s61 constrains), so the blocker simply never fires.
CHAIN_S68 = CHAIN_FULL + [
    "s60-entitlement-enforcement.sql", "s61-signature-symmetry-and-key-binding.sql",
    "s62-delegation-lifecycle-gating.sql", "s63-supersession-body-restoration.sql",
    "s64-principal-stamps-delegation-conditions.sql", "s65-refusal-attempted-kind.sql",
    "s66-forged-stamp-journal-totality.sql", "s67-refusal-digest-bound.sql",
    "s68-typed-absence-dispositions.sql",
]


def write_scratch_multiplex_config_enforce(tmpdir: Path, world: str) -> Path:
    """WR13 (row 173): the SAME single-deployment TOML shape `write_scratch_multiplex_config`
    (imported from the boundary-service sibling) writes, plus the ONE additional top-level key
    `identity_enforcement = "enforce"` -- a separate helper rather than parameterizing the
    shared one (that function is the boundary-service suite's OWN home, reused unchanged by
    every other suite; adding an enforce-only knob there for one caller here would be exactly
    the "second, drifting copy" ADR-0012 P1 warns against in the other direction -- this local
    helper is the smaller, more honest duplication of the ONE line that differs, matching this
    file's own `birth_via_boundary_full`'s stated precedent for the identical tradeoff)."""
    path = tmpdir / f"{world}-boundary-multiplex-enforce.toml"
    path.write_text(
        f'identity_enforcement = "enforce"\n'
        f'[deployments.{world}]\n'
        f'pghost = "{PGHOST}"\n'
        f'pgdatabase = "{PGDB}"\n'
        f'pguser = "{world}_rw"\n'
        f'pgschema = "{world}"\n'
        f'pgkern = "{world}_kernel"\n',
        encoding="utf-8")
    return path


def birth_via_boundary_full(world: str) -> tuple[int, int]:
    """`seen-red/boundary-service/run_fixtures.py`'s own `birth_via_boundary` targets CHAIN_B
    (s43-headed) -- its `principal_standing_declared` payloads carry no `principal_binding_active`
    key, which is FINE pre-s45 (the column/CHECK does not exist yet) but REFUSED post-s45 (s45's
    own `principal_binding_active_kind_shape` CHECK requires the flag on that kind). This world
    is CHAIN_FULL (through s50, s45 included), so this is a LOCAL variant, not a re-derivation of
    the whole ceremony (ADR-0012 P1 still holds for everything ELSE -- `bw_call`/`psql_tuples`
    are reused unchanged) -- the ONE line that differs is named here rather than patching the
    shared sibling module (which other suites still exercise against CHAIN_B, pre-s45, where the
    extra key would be premature)."""
    S, K = world, f"{world}_kernel"
    bw_call = bs_fixtures.bw_call
    psql_tuples = bs_fixtures.psql_tuples
    author = int(psql_tuples(f"SELECT id FROM {K}.principal WHERE name='author';"))
    login_role = psql_tuples("SELECT session_user;")
    for fn, payload in [
        ("ledger_write", {"kind": "principal_registered",
                          "statement": "author registered (fixture genesis exception)",
                          "actor": author, "principal_subject": author,
                          "principal_purpose": "fixture connection principal"}),
        ("ledger_write", {"kind": "principal_standing_declared",
                          "statement": f"role {world}_rw -> author", "actor": author,
                          "principal_subject": author, "principal_db_role": f"{world}_rw",
                          "principal_binding_active": True}),
        ("ledger_write", {"kind": "principal_standing_declared",
                          "statement": f"login role {login_role} -> author (dual declaration)",
                          "actor": author, "principal_subject": author,
                          "principal_db_role": login_role, "principal_binding_active": True}),
        ("registration_write", {"name": "write-boundary", "agent_class": "tool",
                                "actor": author,
                                "purpose": "the kernel write boundary's own recording "
                                           "identity (s43 fixture birth)"}),
        ("registration_write", {"name": "boundary-service", "agent_class": "tool",
                                "actor": author,
                                "purpose": "the FastAPI outer boundary Port's own registered "
                                           "principal (design/FABLE-LEDGER-BOUNDARY-SERVICE-"
                                           "SPEC.md §4 -- fixture-birth ceremony)"}),
    ]:
        v = bw_call(world, fn, payload)
        if v["disposition"] != "accepted":
            raise RuntimeError(f"birth act refused: {v}")
    boundary_service_id = int(psql_tuples(f"SELECT id FROM {K}.principal WHERE name='boundary-service';"))
    return author, boundary_service_id


def canon(row: dict) -> str:
    # Ledger rows 153/154 fix round: `_page_tie` is a BOUNDARY-ADDED synthetic field (this
    # route's own composite-keyset tiebreaker, never a kernel/view column) -- stripped here so
    # every row_set_equal call in this file compares REAL row content uniformly, whether the
    # served side came from a unique-key view (never carries the field) or a non-unique one
    # (always does, post-fix). Excluding it here, once, is more honest than special-casing every
    # call site that happens to touch a non-unique-key view.
    return json.dumps({k: v for k, v in row.items() if k != "_page_tie"}, sort_keys=True)


def row_set_equal(a: list, b: list) -> bool:
    return sorted(canon(r) for r in a) == sorted(canon(r) for r in b)


def direct_view_rows(world: str, view: str) -> list:
    # Row 203: `work_role_census` names no stored relation (`boundary_service._view_from_clause`'s
    # own docstring) -- `FROM {world}.{view}` would 404 against a relation that was never
    # supposed to exist. The independent "direct" ground truth for a SERVING-SIDE derived view is
    # the SAME SELECT text the served route itself runs (`_role_census_sql`), executed here
    # directly rather than through the served route's own pagination wrapper -- still an
    # independent check of THIS ROUTE's pagination/JSON-shaping code, which is WR1's own actual
    # subject; it is not independent of the query TEXT itself (there is no second, independently-
    # authored ground truth for a view this build itself defines) -- named honestly here rather
    # than silently presented as equivalent to the stored-relation case.
    from_clause = (f"({boundary_service._role_census_sql(world)}) t"
                   if view in boundary_service._ROLE_CENSUS_DERIVED_VIEWS
                   else f"{world}.{view} t")
    out = bs_fixtures.psql_tuples(
        f"SET ROLE {world}_rw; "
        f"SELECT coalesce(jsonb_agg(t), '[]'::jsonb)::text FROM {from_clause};")
    return json.loads(out)


def birth_fixture_rows(base: str, world: str, author: int) -> dict[str, int]:
    """Populates every VIEW_REGISTRY member with at least one row, through the boundary's OWN
    write routes (never a raw INSERT -- this fixture is itself a served-boundary consumer).
    `credited_current`/`model_defeated_rows` are DELIBERATELY LEFT EMPTY (both sides of WR1's
    comparison are then the empty set, still a valid -- if less rigorous -- equality proof):
    populating a genuine `model_defeated_rows` member needs a `principal_competence_granted`
    row with `principal_binding_active` in force, whose exact trigger-derived shape is s41/s45
    machinery well outside this amendment's own scope to re-derive here; named rather than
    silently assumed.

    Returns a small dict of row ids the WR6 (ledger row 154) witnesses below need: the
    `superseded_row_id` this function already retracts in place while populating
    work_item_violations (the SAME act, not a second one minted for WR6's own sake -- ADR-0012
    P1) and the `superseding_row_id` that retracted it."""
    def w(payload: dict) -> dict:
        status, body = bs_fixtures.http_post(f"{base}/write/ledger", payload)
        if status != 200 or body.get("disposition") != "accepted":
            raise RuntimeError(f"fixture birth write refused/failed: status={status} body={body} payload={payload}")
        return body

    # question_status: any 'question'-kind row.
    w({"kind": "question", "statement": f"WR fixture question {RUN_SUFFIX}", "actor": author})

    # A second principal, registered up front -- needed both for review_stamp_distinctness
    # (segregation of duties: a row's own author may not countersign it, so the review below
    # needs a DISTINCT reviewing actor) and for review_gap (an obliged actor's own unreviewed row).
    status, reg = bs_fixtures.http_post(f"{base}/write/registration", {
        "name": f"wrfx-reviewer-{RUN_SUFFIX}", "agent_class": "tool", "actor": author,
        "purpose": "WR fixture reviewer principal"})
    if status != 200 or reg.get("disposition") != "accepted":
        raise RuntimeError(f"fixture registration refused: status={status} body={reg}")
    reviewer_id = int(bs_fixtures.psql_tuples(
        f"SET ROLE {world}_rw; SELECT id FROM {world}_kernel.principal "
        f"WHERE name = 'wrfx-reviewer-{RUN_SUFFIX}';"))

    # review_stamp_distinctness: any review row (regardless of verdict) -- the view just joins a
    # kind='review' row to its own regards row, no independence/stamp requirement of its own.
    # Segregation-of-duties (I6) still requires a DISTINCT actor from the regarded row's own
    # author, unconditionally -- so this uses `reviewer_id`, not `author`. 'self-review'
    # independence is chosen only to avoid the SEPARATE stamp-verification requirement
    # ('technical'/'managerial'/'financial' each need a session-stamped invocation this
    # fixture, a plain HTTP client, cannot produce) -- named, not worked around.
    note = w({"kind": "note", "statement": f"WR fixture note {RUN_SUFFIX}", "actor": author})
    status, rv = bs_fixtures.http_post(f"{base}/write/review", {
        "regards": note["row_id"], "statement": "fixture review", "verdict": "attest",
        "independence": "self-review", "basis": "fixture", "actor": reviewer_id})
    if status != 200 or rv.get("disposition") != "accepted":
        raise RuntimeError(f"fixture review write refused: status={status} body={rv}")

    # review_gap: the obligated reviewer writes a row nobody else reviews.
    status, ob = bs_fixtures.http_post(f"{base}/write/obligation", {
        "scope": f"wrfx-scope-{RUN_SUFFIX}", "assigned_by": author, "obliges_actor": reviewer_id})
    if status != 200 or ob.get("disposition") != "accepted":
        raise RuntimeError(f"fixture obligation refused: status={status} body={ob}")
    w({"kind": "note", "statement": f"WR fixture obliged-actor note {RUN_SUFFIX}", "actor": reviewer_id})

    # standing_decisions: a decision row carrying decision_grade.
    w({"kind": "decision", "statement": f"WR fixture decision {RUN_SUFFIX}", "actor": author,
       "decision_grade": "durable"})

    # work_item_violations (orphaned_by_retraction) + work_item_current: open, claim, then
    # RETRACT the opening act (supersede it with an unrelated row -- work_opened carries none of
    # s45's own same-kind supersession restriction, that applies only to the three standing-
    # lifecycle kinds) -- the surviving work_claimed row now cites a slug with no in-force
    # opening. NOT dup_open/shipped_without_witness: both are foreclosed at WRITE TIME on this
    # kernel head (s39's "one opening act per slug ever" refusal; a `work_shipped_requires_
    # witness` CHECK) -- each view member is now defensive/unreachable dead code over an
    # ordinary write, not a live path; orphaned_by_retraction is the one live member left.
    viol_slug = f"wrfx-viol-{RUN_SUFFIX}"
    opened = w({"kind": "work_opened", "statement": "WR fixture violation open", "actor": author,
                "work_slug": viol_slug, "work_title": "WR fixture violation"})
    w({"kind": "work_claimed", "statement": "WR fixture violation claim", "actor": author,
       "work_slug": viol_slug})
    retraction = w({"kind": "note", "statement": "WR fixture retracting the opening act",
                    "actor": author, "supersedes": opened["row_id"]})

    # work_review_gap: a work item closed with work_review_disposition='deferred', undischarged.
    wr_slug = f"wrfx-deferred-{RUN_SUFFIX}"
    w({"kind": "work_opened", "statement": "WR fixture deferred open", "actor": author,
       "work_slug": wr_slug, "work_title": "WR fixture deferred"})
    w({"kind": "work_closed", "statement": "WR fixture deferred close", "actor": author,
       "work_slug": wr_slug, "work_resolution": "shipped", "work_witness": "wrfx witness text",
       "work_review_disposition": "deferred"})

    # countersign_obligation: the SAME obligation row birthed for review_gap above already
    # populates this (it is the TABLE review_gap's own FK target) -- no separate act needed.

    # model_attestations: one model_identity_attested row (verdict='match').
    w({"kind": "model_identity_attested", "statement": "WR fixture attestation",
       "actor": author, "attest_row_id": note["row_id"], "attest_model": "wrfx-model",
       "attest_grade": "exact-command", "attest_verdict": "match",
       "attest_expected": "wrfx-model", "attest_session": f"wrfx-session-{RUN_SUFFIX}",
       "attest_basis": "fixture"})

    # principal_relations/principal_role_bindings/principal_keys/principal_competences (legacy-
    # led-retirement inventory pass, ledger row 1149 -- the fourth VIEW_REGISTRY growth, see that
    # dict's own comment): one in-force row each, via the SAME generic /write/ledger surface
    # `led principal *`'s served port now targets -- exactly the shape s41's own D-5 views
    # project off `principal_relation_asserted`/`principal_role_bound`/`principal_key_bound`/
    # `principal_competence_granted`, `principal_binding_active=true`. `reviewer_id` (already
    # registered above for review_stamp_distinctness/review_gap) is the second endpoint/subject.
    w({"kind": "principal_relation_asserted", "statement": "WR fixture relation asserted",
       "actor": author, "principal_subject": author, "principal_object": reviewer_id,
       "principal_relation": "acts-for", "principal_binding_active": True})
    w({"kind": "principal_role_bound", "statement": "WR fixture role bound", "actor": author,
       "principal_subject": reviewer_id, "principal_role_name": f"wrfx-role-{RUN_SUFFIX}",
       "principal_binding_active": True})
    # principal_keys (s41 D-3): key bindings are refused for a non-human subject (agent_class
    # 'model'/'subagent'/'tool') -- ledger policy, a key attests a human's own act. A dedicated
    # human-class principal is registered here just for this one row.
    status, reg_h = bs_fixtures.http_post(f"{base}/write/registration", {
        "name": f"wrfx-human-{RUN_SUFFIX}", "agent_class": "human", "actor": author,
        "purpose": "WR fixture human principal (principal_keys needs a human subject)"})
    if status != 200 or reg_h.get("disposition") != "accepted":
        raise RuntimeError(f"fixture human registration refused: status={status} body={reg_h}")
    human_id = int(bs_fixtures.psql_tuples(
        f"SET ROLE {world}_rw; SELECT id FROM {world}_kernel.principal "
        f"WHERE name = 'wrfx-human-{RUN_SUFFIX}';"))
    w({"kind": "principal_key_bound", "statement": "WR fixture key bound", "actor": author,
       "principal_subject": human_id,
       "principal_key_fingerprint": "0" * 40, "principal_binding_active": True})
    w({"kind": "principal_competence_granted", "statement": "WR fixture competence granted",
       "actor": author, "principal_subject": reviewer_id,
       "principal_competence_activity": f"wrfx-activity-{RUN_SUFFIX}",
       "principal_competence_band": "wrfx-band", "principal_competence_basis": "wrfx-basis",
       "principal_binding_active": True})

    # work_edge_blocks_close/work_violation_history/work_bookkeeping_closes/discharging_attest/
    # countersigned_in_force (ledger rows 153/154, the sixth VIEW_REGISTRY growth -- see that
    # dict's own comment in serving/boundary_service.py). Four of the five new members are
    # already populated for FREE by acts birthed above, named here rather than silently assumed
    # (ADR-0000's closure-statement discipline): discharging_attest/countersigned_in_force by
    # the review_stamp_distinctness 'attest' write on `note` above (kind=review, verdict=attest,
    # regards=note -- exactly discharging_attest's own predicate, and `note` itself is the row
    # countersigned_in_force then serves); work_violation_history by the SAME orphaned_by_
    # retraction act that already populates work_item_violations above (one raw_violations CTE
    # feeds both readers). work_bookkeeping_closes is the one genuinely NEW act: a work item
    # opened then closed with work_review_disposition='bookkeeping' and a commit-shaped
    # work_review_ref (kernel/lineage/s38-bookkeeping-close.sql's own CHECK shape,
    # ^commit:[0-9a-f]{7,40}$).
    bk_slug = f"wrfx-bookkeeping-{RUN_SUFFIX}"
    w({"kind": "work_opened", "statement": "WR fixture bookkeeping open", "actor": author,
       "work_slug": bk_slug, "work_title": "WR fixture bookkeeping"})
    w({"kind": "work_closed", "statement": "WR fixture bookkeeping close", "actor": author,
       "work_slug": bk_slug, "work_resolution": "shipped", "work_witness": "wrfx witness text",
       "work_review_disposition": "bookkeeping", "work_review_ref": "commit:" + "a" * 7})

    # work_edge_blocks_close: a work_depends_on row with edge_type='blocks-close' -- the one
    # member of the five with no free ride off an act above (every prior work_depends_on-shaped
    # act in this file is a plain dependency, not this edge_type).
    bc_dependent = f"wrfx-bc-dependent-{RUN_SUFFIX}"
    bc_antecedent = f"wrfx-bc-antecedent-{RUN_SUFFIX}"
    w({"kind": "work_opened", "statement": "WR fixture blocks-close antecedent", "actor": author,
       "work_slug": bc_antecedent, "work_title": "WR fixture blocks-close antecedent"})
    w({"kind": "work_opened", "statement": "WR fixture blocks-close dependent", "actor": author,
       "work_slug": bc_dependent, "work_title": "WR fixture blocks-close dependent"})
    w({"kind": "work_depends_on", "statement": "WR fixture blocks-close edge", "actor": author,
       "work_slug": bc_dependent, "work_depends_on": bc_antecedent, "edge_type": "blocks-close"})

    return {"superseded_row_id": opened["row_id"], "superseding_row_id": retraction["row_id"]}


def birth_duplicate_key_probes(base: str, world: str, author: int) -> dict[str, object]:
    """Ledger rows 153/154, fix round (coordinator fresh-context review of commit 6a104c0,
    CRITICAL finding): constructs a genuine DUPLICATE key value on FIVE non-unique-key
    VIEW_REGISTRY members, so WR8 below can prove the composite-tiebreaker fix actually closes
    the silent-pagination-loss class rather than merely asserting it does on an accidentally-
    clean fixture. Returns the (view name -> repeated key value) map WR8 walks.

    discharging_attest.regards_id: TWO distinct reviewers both attest the SAME row.
    work_violation_history.slug / work_item_violations.slug: ONE slug carrying TWO surviving
    orphaned_by_retraction sub-forms (a work_claimed AND a work_closed, both citing the same
    retracted opening act) -- reuses this file's own existing viol_slug construction one step
    further rather than re-deriving a second recipe.
    model_defeated_rows.attest_id: ONE model_identity_attested (verdict=mismatch) row whose
    actor holds TWO separate, both-in-force model-identity-attestation competence grants -- the
    JOIN fans the one attestation out across both grants.
    review_gap.id: ONE undischarged row by an actor obliged under TWO distinct scopes at once.
    work_review_gap.slug: ONE slug carrying a deferred work_closed AND a deferred
    work_violation_disposition targeting a different row on the same slug.
    """
    def w(payload: dict) -> dict:
        status, body = bs_fixtures.http_post(f"{base}/write/ledger", payload)
        if status != 200 or body.get("disposition") != "accepted":
            raise RuntimeError(f"dup-probe birth write refused/failed: status={status} body={body} payload={payload}")
        return body

    def register(name: str, agent_class: str = "tool") -> int:
        status, reg = bs_fixtures.http_post(f"{base}/write/registration", {
            "name": name, "agent_class": agent_class, "actor": author,
            "purpose": f"dup-probe fixture principal {name}"})
        if status != 200 or reg.get("disposition") != "accepted":
            raise RuntimeError(f"dup-probe registration refused: status={status} body={reg}")
        return int(bs_fixtures.psql_tuples(
            f"SET ROLE {world}_rw; SELECT id FROM {world}_kernel.principal WHERE name = '{name}';"))

    # ---- discharging_attest: two distinct reviewers, one attested row ----
    dup_note = w({"kind": "note", "statement": f"dup-probe note {RUN_SUFFIX}", "actor": author})
    rev_a = register(f"dupfx-rev-a-{RUN_SUFFIX}")
    rev_b = register(f"dupfx-rev-b-{RUN_SUFFIX}")
    for rid in (rev_a, rev_b):
        status, rv = bs_fixtures.http_post(f"{base}/write/review", {
            "regards": dup_note["row_id"], "statement": "dup-probe attest", "verdict": "attest",
            "independence": "self-review", "basis": "dup-probe fixture", "actor": rid})
        if status != 200 or rv.get("disposition") != "accepted":
            raise RuntimeError(f"dup-probe review refused: status={status} body={rv}")

    # ---- work_violation_history / work_item_violations: one slug, two orphaned_by_retraction
    # sub-forms (a surviving work_claimed AND a surviving work_closed) ----
    dv_slug = f"dupfx-viol-{RUN_SUFFIX}"
    dv_opened = w({"kind": "work_opened", "statement": "dup-probe viol open", "actor": author,
                   "work_slug": dv_slug, "work_title": "dup-probe viol"})
    w({"kind": "work_claimed", "statement": "dup-probe viol claim", "actor": author,
       "work_slug": dv_slug})
    w({"kind": "work_closed", "statement": "dup-probe viol close", "actor": author,
       "work_slug": dv_slug, "work_resolution": "shipped", "work_witness": "dup-probe witness",
       "work_review_disposition": "deferred"})
    w({"kind": "note", "statement": "dup-probe retracting the viol opening act", "actor": author,
       "supersedes": dv_opened["row_id"]})

    # ---- model_defeated_rows: one actor, two in-force model-identity-attestation grants,
    # one mismatch attestation by that actor ----
    dm_actor = register(f"dupfx-modelactor-{RUN_SUFFIX}", agent_class="model")
    w({"kind": "principal_competence_granted", "statement": "dup-probe grant 1", "actor": author,
       "principal_subject": dm_actor, "principal_competence_activity": "model-identity-attestation",
       "principal_competence_band": "dupfx-band-1", "principal_competence_basis": "dup-probe fixture",
       "principal_binding_active": True})
    w({"kind": "principal_competence_granted", "statement": "dup-probe grant 2", "actor": author,
       "principal_subject": dm_actor, "principal_competence_activity": "model-identity-attestation",
       "principal_competence_band": "dupfx-band-2", "principal_competence_basis": "dup-probe fixture",
       "principal_binding_active": True})
    dm_target = w({"kind": "note", "statement": "dup-probe attested-row target", "actor": author})
    dm_attest = w({"kind": "model_identity_attested", "statement": "dup-probe mismatch attest",
                   "actor": dm_actor, "attest_row_id": dm_target["row_id"],
                   "attest_model": "dupfx-model", "attest_grade": "exact-command",
                   "attest_verdict": "mismatch", "attest_expected": "some-other-model",
                   "attest_session": f"dupfx-session-{RUN_SUFFIX}", "attest_basis": "dup-probe fixture"})

    # ---- review_gap: one actor obliged under two distinct scopes, one unreviewed note ----
    dg_actor = register(f"dupfx-obliged-{RUN_SUFFIX}")
    for scope_suffix in ("a", "b"):
        status, ob = bs_fixtures.http_post(f"{base}/write/obligation", {
            "scope": f"dupfx-scope-{scope_suffix}-{RUN_SUFFIX}", "assigned_by": author,
            "obliges_actor": dg_actor})
        if status != 200 or ob.get("disposition") != "accepted":
            raise RuntimeError(f"dup-probe obligation refused: status={status} body={ob}")
    dg_note = w({"kind": "note", "statement": "dup-probe obliged-actor note", "actor": dg_actor})

    # ---- work_review_gap: one slug, a deferred work_closed PLUS a deferred
    # work_violation_disposition targeting a different row on the same slug ----
    wg_slug = f"dupfx-wrg-{RUN_SUFFIX}"
    w({"kind": "work_opened", "statement": "dup-probe wrg open", "actor": author,
       "work_slug": wg_slug, "work_title": "dup-probe wrg"})
    wg_dep_edge = w({"kind": "work_depends_on", "statement": "dup-probe wrg dep edge",
                     "actor": author, "work_slug": wg_slug,
                     "work_depends_on": f"dupfx-wrg-nonexistent-{RUN_SUFFIX}"})
    w({"kind": "work_closed", "statement": "dup-probe wrg close", "actor": author,
       "work_slug": wg_slug, "work_resolution": "shipped", "work_witness": "dup-probe witness",
       "work_review_disposition": "deferred"})
    w({"kind": "work_violation_disposition", "statement": "dup-probe wrg viol-disp",
       "actor": author, "work_violation_class": "depends_on_unknown_slug",
       "work_violation_target_id": wg_dep_edge["row_id"], "work_resolution": "retired",
       "rationale": "dup-probe: retiring the depends_on_unknown_slug violation as a probe leg",
       "work_review_disposition": "deferred"})

    return {
        "discharging_attest_regards_id": dup_note["row_id"],
        "work_violation_history_slug": dv_slug,
        "work_item_violations_slug": dv_slug,
        "model_defeated_rows_attest_id": dm_attest["row_id"],
        "review_gap_id": dg_note["row_id"],
        "work_review_gap_slug": wg_slug,
    }


def walk_paginated(base: str, view: str, key_col: str, key_kind: str, limit: int = 1) -> list[dict]:
    """Round-3 fix (ledger rows 153/154, coordinator's THIRD fresh-context re-review): this used
    to be a SECOND, hand-rolled keyset walker living only in this fixture -- the round-3 finding
    is exactly that a second implementation of "walk every page" can silently drift from the
    real one (`serving/boundary_cli_client.py`'s `get_all_rows`, the ACTUAL function
    `led.tmpl`/`pickup.tmpl` call in production, which had NOT been taught the round-1/2
    `after_tie` contract even though this fixture's own former hand-rolled copy had). Rather than
    fix this fixture's copy a second time and leave two walkers that can diverge again (round-4
    review's own stated first question), this is now a THIN pass-through to the production
    walker itself -- `key_col` is accepted only to preserve this function's existing call-site
    signature across WR8/WR9 (every caller still filters/groups served rows by their own
    `key_col` value after the walk returns); the production walker derives its OWN id/slug field
    name internally, from the SAME `_ID_FIELD_OVERRIDE`/`_SLUG_FIELD_OVERRIDE` dicts this whole
    fix round audited and repaired, never re-derived here a second time (ADR-0012 P1)."""
    return boundary_cli_client.get_all_rows(base, f"/views/{view}", cursor=f"after_{key_kind}",
                                             limit=limit)


def get_all_rows_bounded(base: str, view: str, limit: int, timeout_s: float = 30.0,
                          cursor: str = "after_id") -> list[dict]:
    """Round-3 fix (ledger rows 153/154): calls the REAL, production `boundary_cli_client.
    get_all_rows` -- not this fixture's own in-process import, a genuinely SEPARATE Python
    process -- wall-clock-bounded by `timeout_s`. Two reasons this runs out-of-process rather
    than simply calling the function directly: (1) it is the SAME mechanism this fix round's
    own one-time RED verification uses to reproduce the reviewer's exact infinite-loop finding
    against the round-1/2 (pre-round-3) client with a real subprocess timeout standing in for
    "the reviewer eventually killed it" (banked in red.txt, not run here); (2) as a STANDING
    safety net, a permanent fixture leg that calls a pagination walker in-process would hang the
    ENTIRE suite forever if a future change ever reintroduced the bug this round fixes --
    out-of-process with a timeout means a regression fails FAST and namely ("exceeded the time
    budget, likely an infinite pagination loop"), never silently wedges CI. Raises
    `subprocess.TimeoutExpired` on a genuine hang (the caller decides what that means -- a
    round-3-era caller treats it as a FAILURE; the one-time RED verification treats it as
    confirmation)."""
    script = (
        "import sys; sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2]); "
        "import deployment_record, boundary_cli_client, json; "
        "rows = boundary_cli_client.get_all_rows(sys.argv[3], sys.argv[4], "
        "cursor=sys.argv[6], limit=int(sys.argv[5])); "
        "print(json.dumps(rows))"
    )
    cp = subprocess.run(
        [sys.executable, "-c", script, str(REPO / "filing"), str(REPO / "serving"),
         base, f"/views/{view}", str(limit), cursor],
        capture_output=True, text=True, timeout=timeout_s)
    if cp.returncode != 0:
        raise RuntimeError(f"get_all_rows_bounded subprocess failed: rc={cp.returncode} "
                           f"stdout={cp.stdout[-2000:]!r} stderr={cp.stderr[-2000:]!r}")
    return json.loads(cp.stdout.strip().splitlines()[-1])


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    procs: list = []
    world = f"wrfx{RUN_SUFFIX}"
    bs_fixtures.teardown(world)
    try:
        print(f"== scaffolding classic world {world} (chain ends {CHAIN_FULL[-1]}) ==")
        wdir = bs_fixtures.scaffold_classic(world, CHAIN_FULL)
        tmps.append(wdir.parent)
        author, _svc = birth_via_boundary_full(world)
        dep_path = bs_fixtures.write_scratch_deployment(wdir.parent, world)
        cfg_path = bs_fixtures.write_scratch_multiplex_config(wdir.parent, world)
        proc, port = bs_fixtures.start_server(cfg_path)
        procs.append(proc)
        base = f"http://127.0.0.1:{port}/d/{world}"
        up = bs_fixtures.wait_health(base)
        check("setup-server-healthy", up, f"GET /d/{world}/health up={up}", failures)
        if not up:
            raise RuntimeError("server never became healthy -- aborting the rest of the suite")

        ts_before = bs_fixtures.psql_tuples("SELECT now()::text;")
        time.sleep(0.05)
        birth_ids = birth_fixture_rows(base, world, author)
        time.sleep(0.05)
        ts_mid = bs_fixtures.psql_tuples("SELECT now()::text;")
        time.sleep(0.05)
        # A row written AFTER ts_mid, so WR3's as-of-at-ts_mid read has something real to EXCLUDE
        # (proving the equality below is not a vacuous both-sides-identical-to-"now" pass).
        status, post_mid = bs_fixtures.http_post(f"{base}/write/ledger", {
            "kind": "note", "statement": f"WR fixture post-mid note {RUN_SUFFIX}", "actor": author})
        if status != 200 or post_mid.get("disposition") != "accepted":
            raise RuntimeError(f"post-ts_mid fixture write refused: status={status} body={post_mid}")

        # ==================== WR1: per-view row-set equality (per view, not umbrella) ====================
        print("== WR1: per-view row-set equality, served vs direct ==")
        for view in sorted(boundary_service.VIEW_REGISTRY):
            status, served = bs_fixtures.http_get(f"{base}/views/{view}?limit=1000")
            direct = direct_view_rows(world, view)
            ok = (status == 200 and isinstance(served, list) and row_set_equal(served, direct))
            check(f"wr1-view-{view}",
                  ok,
                  f"status={status} served_n={len(served) if isinstance(served, list) else '?'} "
                  f"direct_n={len(direct)} row_sets_equal={ok}"
                  + ("" if direct else "  (NOTE: empty on this world -- see birth_fixture_rows' "
                                        "own docstring for credited_current/model_defeated_rows)"),
                  failures)

        # ==================== WR2: unknown view -> typed 404, nothing queried ====================
        print("== WR2: unknown view name -> typed 404 ==")
        status, body = bs_fixtures.http_get(f"{base}/views/does-not-exist-{RUN_SUFFIX}")
        known = sorted(boundary_service.VIEW_REGISTRY)
        check("wr2-unknown-view-typed-404",
              status == 404 and isinstance(body, dict)
              and body.get("disposition") == "unknown_view"
              and sorted(body.get("known", [])) == known,
              f"status={status} body={body} (expected known={known})", failures)

        # ==================== WR3: as-of equality vs asof-export read; malformed ts -> 422 ========
        print("== WR3: as-of reconstruction equality vs the legacy asof-export.tmpl read ==")
        dep = deployment_record.load_deployment(dep_path)
        legacy_rows, legacy_err = asof_export.ledger_asof_rows(dep, ts_mid)
        status, served_rows = bs_fixtures.http_get(
            f"{base}/rows/asof/{ts_mid.replace(' ', 'T').replace('+', '%2B')}?limit=1000")
        legacy_ids = sorted(r["id"] for r in legacy_rows) if legacy_err is None else None
        served_ids = sorted(r["id"] for r in served_rows) if isinstance(served_rows, list) else None
        # actor_name is asof-export.tmpl's OWN CLI-side enrichment (a LEFT JOIN it does itself,
        # not a kernel-view fact) -- stripped from the legacy side before the row-set compare so
        # both sides carry the SAME (raw ledger column) shape the served route actually returns
        # (see rows_asof's own comment in serving/boundary_service.py for why actor_name is not
        # served).
        legacy_stripped = [{k: v for k, v in r.items() if k != "actor_name"} for r in legacy_rows] if legacy_err is None else []
        ok_equal = (legacy_err is None and status == 200 and isinstance(served_rows, list)
                    and row_set_equal(served_rows, legacy_stripped))
        # A non-vacuous proof: the post-mid row must be excluded from BOTH readings.
        post_mid_excluded = (legacy_ids is not None and post_mid["row_id"] not in legacy_ids
                              and served_ids is not None and post_mid["row_id"] not in served_ids)
        check("wr3-asof-equality-vs-legacy-nonvacuous",
              ok_equal and post_mid_excluded,
              f"legacy_err={legacy_err} status={status} legacy_n={len(legacy_rows) if legacy_err is None else '?'} "
              f"served_n={len(served_rows) if isinstance(served_rows, list) else '?'} "
              f"row_sets_equal={ok_equal} post_mid_row_id={post_mid['row_id']} "
              f"excluded_from_both={post_mid_excluded}",
              failures)

        status_bad, body_bad = bs_fixtures.http_get(f"{base}/rows/asof/not-a-timestamp")
        check("wr3-malformed-ts-typed-422-pre-kernel",
              status_bad == 422 and isinstance(body_bad, dict) and "detail" in body_bad,
              f"status={status_bad} body={body_bad}", failures)

        # ==================== WR4: /meta matches reality =========================================
        print("== WR4: GET /meta matches reality (view list + lineage head) ==")
        status, meta = bs_fixtures.http_get(f"{base}/meta")
        manifest = migrate_core._manifest()
        detects = migrate_core._require_detect_files(manifest)
        actual_head, _missing = migrate_core._current_head_and_missing(dep, world, f"{world}_kernel", manifest, detects)
        actual_head_stem = actual_head[:-4] if actual_head and actual_head.endswith(".sql") else actual_head
        check("wr4-meta-view-list-equals-allowlist",
              status == 200 and isinstance(meta, dict)
              and sorted(meta.get("known_views", [])) == sorted(boundary_service.VIEW_REGISTRY),
              f"status={status} known_views={meta.get('known_views') if isinstance(meta, dict) else meta}",
              failures)
        check("wr4-meta-lineage-head-equals-actual",
              isinstance(meta, dict) and meta.get("lineage_head") == actual_head_stem,
              f"served lineage_head={meta.get('lineage_head') if isinstance(meta, dict) else meta!r} "
              f"actual (migrate_core._current_head_and_missing)={actual_head_stem!r}",
              failures)
        check("wr4-meta-boundary-version-present",
              isinstance(meta, dict) and isinstance(meta.get("boundary_version"), str)
              and meta.get("boundary_version") == boundary_service.BOUNDARY_SERVICE_VERSION,
              f"boundary_version={meta.get('boundary_version') if isinstance(meta, dict) else meta}",
              failures)

        # ==================== WR5: admission discipline unchanged on a /views/ route =============
        # design/BRIEF-A1-INFLIGHT-CAP-AND-WOULD-PRODUCE-2026-08-04.md item 1 retired
        # compute_per_deployment_limit's `max(4, MAX_INFLIGHT_KERNEL_CALLS // len(deployments))`
        # formula (shipped default is now a flat 32, deployment-count-independent, and >= the
        # global MAX_INFLIGHT_KERNEL_CALLS=24 -- see seen-red/boundary-multiplex/run_fixtures.py's
        # WM-INFLIGHT-DEFAULT for that polarity). This leg needs `deployment_saturated` to
        # actually fire (its own point, "still fires on a /views/ route"), which the default can
        # structurally never produce (the per-deployment gate cannot bind before the smaller
        # global one does) -- so this config now explicitly OVERRIDES `max_inflight_per_deployment`
        # to 12, the SAME value the retired formula used to produce for two deployments, matching
        # seen-red/boundary-multiplex/run_fixtures.py's own WM4 fix for the identical reason.
        print("== WR5: per-deployment saturation still fires on a /views/ route (WM4 method) ==")
        world_stalled = f"wrfxstall{RUN_SUFFIX}"
        tmp_cfg5 = Path(tempfile.mkdtemp(prefix="wr5-cfg-"))
        tmps.append(tmp_cfg5)
        expected_per_dep_limit = 12
        cfg5 = tmp_cfg5 / "boundary-multiplex.toml"
        cfg5.write_text(
            f'max_inflight_per_deployment = {expected_per_dep_limit}\n\n'
            f'[deployments.{world}]\n'
            f'pghost = "{PGHOST}"\npgdatabase = "{PGDB}"\n'
            f'pguser = "{world}_rw"\npgschema = "{world}"\npgkern = "{world}_kernel"\n\n'
            f'[deployments.{world_stalled}]\n'
            f'pghost = "{bs_fixtures.UNROUTABLE_HOST}"\npgdatabase = "{PGDB}"\n'
            f'pguser = "{world_stalled}_rw"\npgschema = "{world_stalled}"\n'
            f'pgkern = "{world_stalled}_kernel"\n',
            encoding="utf-8")
        proc5, port5 = bs_fixtures.start_server(cfg5)
        procs.append(proc5)
        base5 = f"http://127.0.0.1:{port5}"
        up5 = bs_fixtures.wait_health(f"{base5}/d/{world}")
        BURST_N = 24
        results: list[tuple[int, int | None, dict | None]] = []
        lock = threading.Lock()

        def _burst_one(idx: int) -> None:
            try:
                st, bd = bs_fixtures.http_get(
                    f"{base5}/d/{world_stalled}/views/work_item_current?limit=1")
            except (urllib.error.URLError, OSError, ValueError) as e:
                st, bd = None, {"client_side_error": str(e)}
            with lock:
                results.append((idx, st, bd))

        threads = [threading.Thread(target=_burst_one, args=(i,)) for i in range(BURST_N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)
        dep_saturated = [r for r in results if r[1] == 503 and isinstance(r[2], dict)
                          and r[2].get("disposition") == "deployment_saturated"
                          and r[2].get("deployment") == world_stalled]
        expected_excess = BURST_N - expected_per_dep_limit
        check("wr5-views-route-admission-gate-fires",
              up5 and len(results) == BURST_N and len(dep_saturated) >= expected_excess
              and all(r[2].get("inflight_limit") == expected_per_dep_limit for r in dep_saturated),
              f"server_up={up5} burst_n={BURST_N} expected_per_dep_limit={expected_per_dep_limit} "
              f"deployment_saturated={len(dep_saturated)} (expected >= {expected_excess}) "
              f"statuses={sorted({r[1] for r in results})}",
              failures)

        # ==================== WR6: bulk superseded read (ledger row 154) ========================
        print("== WR6: GET /rows/current -- include_superseded opt-in, default unchanged ==")
        superseded_id = birth_ids["superseded_row_id"]
        superseding_id = birth_ids["superseding_row_id"]

        # WR6a: the DEFAULT (param omitted) is byte-identical to the pre-this-build response --
        # compared against a fresh direct read of `ledger_current` (the SAME ground-truth
        # comparison WR1 already uses one route over), and the superseded row must be ABSENT
        # (ledger_current's own structural exclusion, unchanged) with no `is_current` field
        # anywhere in the response (the byte-identical-shape half of the claim, not just the
        # row-set half).
        status_a, served_a = bs_fixtures.http_get(f"{base}/rows/current?limit=1000")
        direct_current = direct_view_rows(world, "ledger_current")
        served_ids_a = {r["id"] for r in served_a} if isinstance(served_a, list) else set()
        no_is_current_field = (isinstance(served_a, list)
                                and all("is_current" not in r for r in served_a))
        check("wr6a-default-byte-identical-no-marking-field",
              status_a == 200 and isinstance(served_a, list)
              and row_set_equal(served_a, direct_current)
              and superseded_id not in served_ids_a
              and no_is_current_field,
              f"status={status_a} served_n={len(served_a) if isinstance(served_a, list) else '?'} "
              f"direct_n={len(direct_current)} row_sets_equal="
              f"{row_set_equal(served_a, direct_current) if isinstance(served_a, list) else '?'} "
              f"superseded_id={superseded_id} present={superseded_id in served_ids_a} "
              f"no_is_current_field={no_is_current_field}",
              failures)

        # WR6a': explicit include_superseded=false is the SAME default -- not merely "omitted"
        # takes the fast path while a typed "false" takes some other path (the parser's own
        # closed vocabulary treats both identically, per _strict_bool_flag's own docstring).
        status_a2, served_a2 = bs_fixtures.http_get(f"{base}/rows/current?limit=1000&include_superseded=false")
        check("wr6a-explicit-false-identical-to-omitted",
              status_a2 == 200 and isinstance(served_a2, list) and row_set_equal(served_a2, served_a),
              f"status={status_a2} row_sets_equal_to_omitted="
              f"{row_set_equal(served_a2, served_a) if isinstance(served_a2, list) else '?'}",
              failures)

        # WR6b: include_superseded=true -- the superseded row is now PRESENT, marked
        # is_current=false; the row that superseded it (never itself superseded) is present,
        # marked is_current=true; every row's marking agrees with a ground-truth EXISTS query
        # (the SAME predicate the served route computes, checked independently here rather than
        # trusting the served value against itself).
        status_b, served_b = bs_fixtures.http_get(f"{base}/rows/current?limit=1000&include_superseded=true")
        by_id = {r["id"]: r for r in served_b} if isinstance(served_b, list) else {}
        superseded_row = by_id.get(superseded_id)
        superseding_row = by_id.get(superseding_id)
        ground_truth_superseded_current = bs_fixtures.psql_tuples(
            f"SET ROLE {world}_rw; SELECT CASE WHEN NOT EXISTS (SELECT 1 FROM {world}.ledger s "
            f"WHERE s.supersedes = {superseded_id}) THEN 'true' ELSE 'false' END;")
        marking_matches_ground_truth = (
            superseded_row is not None
            and str(superseded_row.get("is_current")).lower()
            == ground_truth_superseded_current.lower())
        check("wr6b-include-superseded-true-marks-both-legibly",
              status_b == 200 and superseded_row is not None and superseding_row is not None
              and superseded_row.get("is_current") is False
              and superseding_row.get("is_current") is True
              and marking_matches_ground_truth,
              f"status={status_b} superseded_row={superseded_row} superseding_row={superseding_row} "
              f"ground_truth_superseded_current={ground_truth_superseded_current!r} "
              f"marking_matches_ground_truth={marking_matches_ground_truth}",
              failures)

        # WR6c: the strict-parse refusal -- anything but "true"/"false"/omitted is a typed 422,
        # never a silent default (commission text, verbatim). Two illegal spellings a LENIENT
        # bool-query-param coercion would happily accept ("1", "TRUE") both refuse here.
        for illegal in ("1", "TRUE", "yes"):
            status_c, body_c = bs_fixtures.http_get(
                f"{base}/rows/current?include_superseded={illegal}")
            check(f"wr6c-strict-parse-refusal-{illegal}",
                  status_c == 422 and isinstance(body_c, dict) and "detail" in body_c
                  and "include_superseded" in body_c["detail"],
                  f"status={status_c} body={body_c}", failures)

        # ==================== WR8: CRITICAL fix (ledger rows 153/154, coordinator fresh-context
        # review of commit 6a104c0) -- non-unique-key views paginate WITHOUT silent loss =========
        print("== WR8: composite-tiebreaker fix -- non-unique key pagination, limit=1, no loss ==")
        dup_ids = birth_duplicate_key_probes(base, world, author)

        # WR8a: a UNIQUE-key view's served response stays BYTE-IDENTICAL (no `_page_tie` field,
        # same row set as before the fix round) -- the reviewer's own constraint (1).
        status_u1, served_u1 = bs_fixtures.http_get(f"{base}/views/work_item_current?limit=1000")
        direct_u = direct_view_rows(world, "work_item_current")
        no_tie_field = isinstance(served_u1, list) and all("_page_tie" not in r for r in served_u1)
        check("wr8a-unique-view-byte-identical",
              status_u1 == 200 and isinstance(served_u1, list)
              and row_set_equal(served_u1, direct_u) and no_tie_field,
              f"status={status_u1} served_n={len(served_u1) if isinstance(served_u1, list) else '?'} "
              f"direct_n={len(direct_u)} no_page_tie_field={no_tie_field}",
              failures)
        status_u2, body_u2 = bs_fixtures.http_get(
            f"{base}/views/work_item_current?after_tie=" + "0" * 32)
        check("wr8a-after-tie-refused-on-unique-view",
              status_u2 == 422 and isinstance(body_u2, dict) and "detail" in body_u2
              and "after_tie" in body_u2["detail"],
              f"status={status_u2} body={body_u2}", failures)

        # WR8b: SIX non-unique members (the reviewer's own two named instances, this build's two
        # new instances, and the two further instances this fix round's own closure-statement
        # audit found and empirically confirmed -- review_gap, work_review_gap), each carrying a
        # REAL duplicate key value. limit=1 keyset walk; paginated total must equal direct total
        # (the reviewer's own bar), and the duplicate value's own row COUNT must match too (not
        # merely the totals, which could coincidentally agree while the WRONG rows were served).
        NONUNIQUE_LEGS = [
            ("discharging_attest", "regards_id", "id", dup_ids["discharging_attest_regards_id"]),
            ("work_violation_history", "slug", "slug", dup_ids["work_violation_history_slug"]),
            ("work_item_violations", "slug", "slug", dup_ids["work_item_violations_slug"]),
            ("model_defeated_rows", "attest_id", "id", dup_ids["model_defeated_rows_attest_id"]),
            ("review_gap", "id", "id", dup_ids["review_gap_id"]),
            ("work_review_gap", "slug", "slug", dup_ids["work_review_gap_slug"]),
        ]
        for view, key_col, key_kind, dup_value in NONUNIQUE_LEGS:
            direct = direct_view_rows(world, view)
            dup_count_direct = sum(1 for r in direct if r[key_col] == dup_value)
            paginated = walk_paginated(base, view, key_col, key_kind, limit=1)
            dup_count_paginated = sum(1 for r in paginated if r[key_col] == dup_value)
            stripped = [{k: v for k, v in r.items() if k != "_page_tie"} for r in paginated]
            ok = (dup_count_direct >= 2 and len(paginated) == len(direct)
                  and dup_count_paginated == dup_count_direct
                  and row_set_equal(stripped, direct))
            check(f"wr8b-{view}-lossless-limit1-walk",
                  ok,
                  f"dup_value={dup_value!r} dup_count_direct={dup_count_direct} "
                  f"direct_total={len(direct)} paginated_total={len(paginated)} "
                  f"dup_count_paginated={dup_count_paginated} row_sets_equal="
                  f"{row_set_equal(stripped, direct)}",
                  failures)

        # ==================== WR9: round-2 CRITICAL-adjacent finding (ledger rows 153/154,
        # coordinator's SECOND fresh-context re-review) -- byte-identical rows within a
        # non-unique-key group are REACHABLE UNDER ORDINARY USE (the same reviewer double-
        # attesting the same row; nothing in the kernel refuses a repeat attest), not dormant.
        # See _nonunique_tie_group_sql's own docstring (serving/boundary_service.py) for the
        # full analysis this witness proves out empirically. ==================================
        print("== WR9: byte-identical rows within a tie group -- atomic-group fix ==")

        def attest_note(regards_row_id: int, reviewer_id: int) -> dict:
            status, rv = bs_fixtures.http_post(f"{base}/write/review", {
                "regards": regards_row_id, "statement": "wr9 repeat attest", "verdict": "attest",
                "independence": "self-review", "basis": "wr9 fixture", "actor": reviewer_id})
            if status != 200 or rv.get("disposition") != "accepted":
                raise RuntimeError(f"wr9 review refused: status={status} body={rv}")
            return rv

        def fresh_note_and_reviewer(tag: str) -> tuple[int, int]:
            status, note = bs_fixtures.http_post(f"{base}/write/ledger", {
                "kind": "note", "statement": f"wr9 {tag} note {RUN_SUFFIX}", "actor": author})
            if status != 200 or note.get("disposition") != "accepted":
                raise RuntimeError(f"wr9 note refused: status={status} body={note}")
            status, reg = bs_fixtures.http_post(f"{base}/write/registration", {
                "name": f"wr9-{tag}-{RUN_SUFFIX}", "agent_class": "tool", "actor": author,
                "purpose": f"wr9 {tag} reviewer principal"})
            if status != 200 or reg.get("disposition") != "accepted":
                raise RuntimeError(f"wr9 registration refused: status={status} body={reg}")
            rid = int(bs_fixtures.psql_tuples(
                f"SET ROLE {world}_rw; SELECT id FROM {world}_kernel.principal "
                f"WHERE name = 'wr9-{tag}-{RUN_SUFFIX}';"))
            return int(note["row_id"]), rid

        # ---- WR9a: the reviewer's OWN exact reproduction -- one reviewer attests the SAME row
        # TWICE. discharging_attest's own column list is (regards_id, reviewer) ONLY, so two
        # attests by the same reviewer on the same row are byte-identical BY CONSTRUCTION (no
        # need to also match statement/basis text -- those columns are not even projected).
        note_a, reviewer_a = fresh_note_and_reviewer("wr9a")
        attest_note(note_a, reviewer_a)
        attest_note(note_a, reviewer_a)
        direct_a = direct_view_rows(world, "discharging_attest")
        twins_a = [r for r in direct_a if r["regards_id"] == note_a]
        paginated_a = walk_paginated(base, "discharging_attest", "regards_id", "id", limit=1)
        twins_paginated_a = [r for r in paginated_a if r["regards_id"] == note_a]
        check("wr9a-double-attest-both-rows-served",
              len(twins_a) == 2 and len(paginated_a) == len(direct_a)
              and len(twins_paginated_a) == 2
              and row_set_equal(twins_paginated_a, twins_a),
              f"note_a={note_a} direct_twins={len(twins_a)} paginated_twins="
              f"{len(twins_paginated_a)} direct_total={len(direct_a)} "
              f"paginated_total={len(paginated_a)} multiset_equal="
              f"{row_set_equal(twins_paginated_a, twins_a)}",
              failures)

        # ---- WR9b: three byte-identical rows (not just two) -- the atomic-group fix must not
        # be a two-only special case.
        note_b, reviewer_b = fresh_note_and_reviewer("wr9b")
        attest_note(note_b, reviewer_b)
        attest_note(note_b, reviewer_b)
        attest_note(note_b, reviewer_b)
        direct_b = direct_view_rows(world, "discharging_attest")
        triplets_b = [r for r in direct_b if r["regards_id"] == note_b]
        paginated_b = walk_paginated(base, "discharging_attest", "regards_id", "id", limit=1)
        triplets_paginated_b = [r for r in paginated_b if r["regards_id"] == note_b]
        check("wr9b-triple-identical-rows-all-served",
              len(triplets_b) == 3 and len(paginated_b) == len(direct_b)
              and len(triplets_paginated_b) == 3
              and row_set_equal(triplets_paginated_b, triplets_b),
              f"note_b={note_b} direct_triplets={len(triplets_b)} paginated_triplets="
              f"{len(triplets_paginated_b)} direct_total={len(direct_b)} "
              f"paginated_total={len(paginated_b)} multiset_equal="
              f"{row_set_equal(triplets_paginated_b, triplets_b)}",
              failures)

        # ---- WR9c: the mid-walk append case, constructed so the append lands on a group the
        # cursor has NOT YET REACHED (never on one already passed -- that is the SAME
        # pre-existing, already-disclosed "behind the cursor" residual A11 already names, not
        # what this leg tests). note_y (attested ONCE) sorts BEFORE note_x (created after it,
        # so its own ledger id -- discharging_attest's own key column -- is numerically
        # greater); walk reaches note_y's own singleton group FIRST, THEN -- between that page
        # response and the next request -- note_x is attested TWICE (a brand-new, two-member
        # group, entirely unwritten when the walk started), and the immediately following page
        # request must serve BOTH note_x rows together, in one page, with no drop.
        note_y, reviewer_y = fresh_note_and_reviewer("wr9c-y")
        attest_note(note_y, reviewer_y)
        status_p1, page1 = bs_fixtures.http_get(
            f"{base}/views/discharging_attest?limit=1&after_id={note_y - 1}")
        if status_p1 != 200 or not isinstance(page1, list) or len(page1) != 1 \
           or page1[0]["regards_id"] != note_y:
            raise RuntimeError(
                f"wr9c setup failed to isolate note_y's own page: status={status_p1} "
                f"page={page1} note_y={note_y}")
        cursor_id, cursor_tie = page1[0]["regards_id"], page1[0].get("_page_tie", "")
        # THE APPEND -- happens HERE, between the request that served note_y's page and the
        # request that will serve note_x's page below. note_x does not exist in ANY form yet.
        note_x, reviewer_x = fresh_note_and_reviewer("wr9c-x")
        attest_note(note_x, reviewer_x)
        attest_note(note_x, reviewer_x)
        status_p2, page2 = bs_fixtures.http_get(
            f"{base}/views/discharging_attest?limit=1&after_id={cursor_id}&after_tie={cursor_tie}")
        check("wr9c-mid-walk-append-not-yet-reached-group-served-whole",
              status_p2 == 200 and isinstance(page2, list) and len(page2) == 2
              and all(r["regards_id"] == note_x for r in page2)
              and row_set_equal(page2, [r for r in direct_view_rows(world, "discharging_attest")
                                          if r["regards_id"] == note_x]),
              f"status={status_p2} page2_n={len(page2) if isinstance(page2, list) else '?'} "
              f"page2={page2} note_x={note_x}",
              failures)

        # ==================== WR10: round-3 CRITICAL finding (ledger rows 153/154, coordinator's
        # THIRD fresh-context re-review) -- the REAL, production `boundary_cli_client.
        # get_all_rows` (not this fixture's own walker) against `review_gap`, the view the
        # reviewer's own reproduction used (a view `led.tmpl`/`pickup.tmpl` genuinely walk), at
        # `limit=1`, over a genuine duplicate key (`dup_ids["review_gap_id"]`, born in WR8 above)
        # -- exactly the reviewer's own repro shape. Wall-clock-bounded (get_all_rows_bounded) so
        # a regression fails fast rather than hanging this whole suite. ======================
        print("== WR10: the REAL production client (get_all_rows) -- the reviewer's own repro ==")
        direct_rg = direct_view_rows(world, "review_gap")
        rg_dup_id = dup_ids["review_gap_id"]
        rg_dup_count_direct = sum(1 for r in direct_rg if r["id"] == rg_dup_id)
        try:
            paginated_rg = get_all_rows_bounded(base, "review_gap", limit=1, timeout_s=30.0)
            rg_timed_out = False
        except subprocess.TimeoutExpired:
            paginated_rg = []
            rg_timed_out = True
        rg_dup_count_paginated = sum(1 for r in paginated_rg if r.get("id") == rg_dup_id)
        check("wr10-real-client-review-gap-limit1-no-hang-no-loss",
              not rg_timed_out and rg_dup_count_direct >= 2
              and len(paginated_rg) == len(direct_rg)
              and rg_dup_count_paginated == rg_dup_count_direct
              and row_set_equal([{k: v for k, v in r.items() if k != "_page_tie"}
                                  for r in paginated_rg], direct_rg),
              f"timed_out={rg_timed_out} dup_id={rg_dup_id} dup_count_direct={rg_dup_count_direct} "
              f"direct_total={len(direct_rg)} paginated_total={len(paginated_rg)} "
              f"dup_count_paginated={rg_dup_count_paginated}",
              failures)

        # ==================== WR11: below-the-hang-threshold duplicate accumulation -- the
        # reviewer's own second framing ("below the hang threshold it silently accumulates
        # duplicate rows"). Same review_gap duplicate, but at a REALISTIC limit (1000, the SAME
        # default get_all_rows/led.tmpl/pickup.tmpl actually use) -- a group smaller than `limit`
        # never trips the pre-round-3 client's own `len(page) < limit` termination test on its
        # FIRST encounter, but a pre-round-3 client would still re-fetch (and thus double-count)
        # that exact group on the NEXT page (after_tie was never sent, so the server's own
        # default `""` re-admits it) before finally terminating on the SHORTER page that follows
        # -- silent duplication, not a hang. Verified GONE on the current (fixed) client. =======
        print("== WR11: below-hang-threshold duplicate accumulation -- gone ==")
        paginated_rg_1000 = get_all_rows_bounded(base, "review_gap", limit=1000, timeout_s=30.0)
        rg_dup_count_1000 = sum(1 for r in paginated_rg_1000 if r.get("id") == rg_dup_id)
        check("wr11-realistic-limit-no-duplicate-accumulation",
              len(paginated_rg_1000) == len(direct_rg)
              and rg_dup_count_1000 == rg_dup_count_direct
              and row_set_equal([{k: v for k, v in r.items() if k != "_page_tie"}
                                  for r in paginated_rg_1000], direct_rg),
              f"direct_total={len(direct_rg)} paginated_total={len(paginated_rg_1000)} "
              f"dup_count_direct={rg_dup_count_direct} dup_count_paginated={rg_dup_count_1000}",
              failures)

        # ==================== WR12: unique-key walk byte-identical via the REAL client; the 409
        # status + /meta field the reviewer's own recommendation folds in (ledger rows 153/154).
        print("== WR12: real-client unique-key walk; tie_group_too_large 409; /meta field ==")
        direct_wic = direct_view_rows(world, "work_item_current")
        paginated_wic = get_all_rows_bounded(base, "work_item_current", limit=1000, timeout_s=30.0,
                                             cursor="after_slug")
        check("wr12a-real-client-unique-key-view-byte-identical",
              len(paginated_wic) == len(direct_wic)
              and row_set_equal(paginated_wic, direct_wic)
              and all("_page_tie" not in r for r in paginated_wic),
              f"direct_total={len(direct_wic)} paginated_total={len(paginated_wic)} "
              f"no_page_tie_field={all('_page_tie' not in r for r in paginated_wic)}",
              failures)

        status_meta, meta_body = bs_fixtures.http_get(f"{base}/meta")
        check("wr12b-meta-advertises-max-tie-group-extra-rows",
              status_meta == 200 and isinstance(meta_body, dict)
              and meta_body.get("max_tie_group_extra_rows") == boundary_service.MAX_TIE_GROUP_EXTRA_ROWS,
              f"status={status_meta} max_tie_group_extra_rows="
              f"{meta_body.get('max_tie_group_extra_rows') if isinstance(meta_body, dict) else meta_body} "
              f"(expected {boundary_service.MAX_TIE_GROUP_EXTRA_ROWS})",
              failures)

        # A tie_group_too_large 409 is NOT forced live here (it would need
        # MAX_TIE_GROUP_EXTRA_ROWS+1 -- 1001 -- byte-identical rows born through real writes,
        # disproportionate to construct in a fixture birth pass); `_tie_group_too_large`'s own
        # status/disposition/message shape is asserted directly instead (unit-level, not a
        # live network round trip) -- an HONEST distinction from a live-fired witness, named
        # rather than silently presented as equivalent.
        tgl_response = boundary_service._tie_group_too_large("some_view", 5)
        check("wr12c-tie-group-too-large-shape-is-409-not-500",
              tgl_response.status_code == 409
              and json.loads(bytes(tgl_response.body)).get("disposition") == "tie_group_too_large",
              f"status_code={tgl_response.status_code} "
              f"body={json.loads(bytes(tgl_response.body))}",
              failures)

        # ==================== WR7: MODERATE finding (ledger rows 153/154) -- countersigned_in_
        # force's TRUE s68 shape, a separate minimal world (the s61 blocker skipped by construction,
        # never attempting the one act -- principal_key_bound -- s61 constrains) =================
        print("== WR7: countersigned_in_force at the TRUE s68 lineage head (separate world) ==")
        world7 = f"wrfxs68{RUN_SUFFIX}"
        bs_fixtures.teardown(world7)
        wdir7 = bs_fixtures.scaffold_classic(world7, CHAIN_S68)
        tmps.append(wdir7.parent)
        author7, _svc7 = birth_via_boundary_full(world7)
        cfg_path7 = bs_fixtures.write_scratch_multiplex_config(wdir7.parent, world7)
        proc7, port7 = bs_fixtures.start_server(cfg_path7)
        procs.append(proc7)
        base7 = f"http://127.0.0.1:{port7}/d/{world7}"
        up7 = bs_fixtures.wait_health(base7)
        check("wr7-setup-server-healthy", up7, f"GET /d/{world7}/health up={up7}", failures)
        if up7:
            def w7(payload: dict) -> dict:
                status, body = bs_fixtures.http_post(f"{base7}/write/ledger", payload)
                if status != 200 or body.get("disposition") != "accepted":
                    raise RuntimeError(f"wr7 birth write refused: status={status} body={body}")
                return body
            status, reg7 = bs_fixtures.http_post(f"{base7}/write/registration", {
                "name": f"wr7-reviewer-{RUN_SUFFIX}", "agent_class": "tool", "actor": author7,
                "purpose": "WR7 reviewer principal (s68 shape witness)"})
            if status != 200 or reg7.get("disposition") != "accepted":
                raise RuntimeError(f"wr7 registration refused: status={status} body={reg7}")
            reviewer7 = int(bs_fixtures.psql_tuples(
                f"SET ROLE {world7}_rw; SELECT id FROM {world7}_kernel.principal "
                f"WHERE name = 'wr7-reviewer-{RUN_SUFFIX}';"))
            note7 = w7({"kind": "note", "statement": f"WR7 fixture note {RUN_SUFFIX}", "actor": author7})
            status, rv7 = bs_fixtures.http_post(f"{base7}/write/review", {
                "regards": note7["row_id"], "statement": "WR7 fixture review", "verdict": "attest",
                "independence": "self-review", "basis": "WR7 fixture", "actor": reviewer7})
            if status != 200 or rv7.get("disposition") != "accepted":
                raise RuntimeError(f"wr7 review refused: status={status} body={rv7}")

            status_c7, served_c7 = bs_fixtures.http_get(f"{base7}/views/countersigned_in_force?limit=1000")
            direct_c7 = direct_view_rows(world7, "countersigned_in_force")
            has_s68_cols = (isinstance(served_c7, list) and len(served_c7) > 0
                             and "refusal_attempted_kind_disposition" in served_c7[0]
                             and "refusal_attempted_actor_disposition" in served_c7[0])
            check("wr7-countersigned-in-force-true-s68-shape",
                  status_c7 == 200 and isinstance(served_c7, list)
                  and row_set_equal(served_c7, direct_c7) and has_s68_cols,
                  f"status={status_c7} served_n={len(served_c7) if isinstance(served_c7, list) else '?'} "
                  f"direct_n={len(direct_c7)} has_s68_cols={has_s68_cols}",
                  failures)
        else:
            check("wr7-countersigned-in-force-true-s68-shape", False,
                  "UNEXERCISED: WR7's own s68-headed world never became healthy", failures)

        # ==================== WR14 (row 203, boundary-role-census-view): the approved role
        # census read -- an open item, a RECLAIM (claim-over-a-live-claim by a distinct actor,
        # the handoff/steal shape IDENTITY-AND-AUTHORITY.md's role-assignment section names), a
        # close, and TWO reviews (one attest, one refuse) regarding the close row ====================
        print("== WR14: role-census view -- opener/claimants/claimant-of-record/closer/"
              "reviewers, reclaim visible ==")
        slug14 = f"wr14-census-{RUN_SUFFIX}"

        def w14(payload: dict) -> dict:
            status, body = bs_fixtures.http_post(f"{base}/write/ledger", payload)
            if status != 200 or body.get("disposition") != "accepted":
                raise RuntimeError(f"wr14 birth write refused: status={status} body={body}")
            return body

        status, reg14a = bs_fixtures.http_post(f"{base}/write/registration", {
            "name": f"wr14-claimant2-{RUN_SUFFIX}", "agent_class": "tool", "actor": author,
            "purpose": "WR14 second claimant (reclaim-by-distinct-actor witness)"})
        status, reg14b = bs_fixtures.http_post(f"{base}/write/registration", {
            "name": f"wr14-reviewer-a-{RUN_SUFFIX}", "agent_class": "tool", "actor": author,
            "purpose": "WR14 first reviewer"})
        status, reg14c = bs_fixtures.http_post(f"{base}/write/registration", {
            "name": f"wr14-reviewer-b-{RUN_SUFFIX}", "agent_class": "tool", "actor": author,
            "purpose": "WR14 second reviewer"})
        claimant2 = int(bs_fixtures.psql_tuples(
            f"SELECT id FROM {world}_kernel.principal WHERE name = 'wr14-claimant2-{RUN_SUFFIX}';"))
        reviewer_a = int(bs_fixtures.psql_tuples(
            f"SELECT id FROM {world}_kernel.principal WHERE name = 'wr14-reviewer-a-{RUN_SUFFIX}';"))
        reviewer_b = int(bs_fixtures.psql_tuples(
            f"SELECT id FROM {world}_kernel.principal WHERE name = 'wr14-reviewer-b-{RUN_SUFFIX}';"))

        w14({"kind": "work_opened", "statement": "WR14 fixture item", "actor": author,
             "work_slug": slug14, "work_title": "WR14 fixture item"})
        w14({"kind": "work_claimed", "statement": "WR14 first claim (author)", "actor": author,
             "work_slug": slug14})
        # The RECLAIM: a claim over the live claim above, by a DISTINCT actor -- IDENTITY-AND-
        # AUTHORITY.md's own words, verbatim: "that claim-over-a-live-claim by a distinct actor
        # IS the handoff's entire record ... the same shape is also what a claim-steal would
        # look like" -- exactly the transition `any_reclaim_by_distinct_actor`/
        # `is_reclaim_by_distinct_actor` exist to make visible by inspection.
        w14({"kind": "work_claimed", "statement": "WR14 reclaim (distinct actor)",
             "actor": claimant2, "work_slug": slug14})
        close14 = w14({"kind": "work_closed", "statement": "WR14 close by claimant of record",
                       "actor": claimant2, "work_slug": slug14,
                       "work_resolution": "shipped", "work_witness": "commit:0000000",
                       "work_review_disposition": "deferred"})
        status, rv14a = bs_fixtures.http_post(f"{base}/write/review", {
            "regards": close14["row_id"], "statement": "WR14 review A (attest)",
            "verdict": "attest", "independence": "self-review", "basis": "WR14 fixture",
            "actor": reviewer_a})
        status, rv14b = bs_fixtures.http_post(f"{base}/write/review", {
            "regards": close14["row_id"], "statement": "WR14 review B (refuse)",
            "verdict": "refuse", "independence": "self-review", "basis": "WR14 fixture",
            "actor": reviewer_b})
        if rv14a.get("disposition") != "accepted" or rv14b.get("disposition") != "accepted":
            raise RuntimeError(f"wr14 review refused: a={rv14a} b={rv14b}")

        status_c14, served14 = bs_fixtures.http_get(f"{base}/views/work_role_census?limit=1000")
        row14 = None
        if status_c14 == 200 and isinstance(served14, list):
            for r in served14:
                if r.get("slug") == slug14:
                    row14 = r
                    break
        check("wr14-role-census-opener-and-closer",
              row14 is not None and row14.get("opener") == author and row14.get("closer") == claimant2,
              f"status={status_c14} row={row14}", failures)
        claimants14 = row14.get("claimants") if row14 else None
        check("wr14-role-census-claimants-in-order-with-reclaim-flag",
              isinstance(claimants14, list) and len(claimants14) == 2
              and claimants14[0].get("claimant") == author
              and claimants14[0].get("is_reclaim_by_distinct_actor") is False
              and claimants14[1].get("claimant") == claimant2
              and claimants14[1].get("is_reclaim_by_distinct_actor") is True,
              f"claimants={claimants14}", failures)
        check("wr14-role-census-claimant-of-record-and-any-reclaim-flag",
              row14 is not None and row14.get("claimant_of_record") == claimant2
              and row14.get("any_reclaim_by_distinct_actor") is True,
              f"row={row14}", failures)
        reviewers14 = row14.get("reviewers") if row14 else None
        reviewer_ids14 = sorted(r.get("reviewer") for r in reviewers14) if isinstance(reviewers14, list) else None
        verdicts14 = sorted(r.get("verdict") for r in reviewers14) if isinstance(reviewers14, list) else None
        grades14 = [r.get("discharge_grade") for r in reviewers14] if isinstance(reviewers14, list) else None
        check("wr14-role-census-two-reviewers-with-kernel-computed-grades",
              isinstance(reviewers14, list) and len(reviewers14) == 2
              and reviewer_ids14 == sorted([reviewer_a, reviewer_b])
              and verdicts14 == ["attest", "refuse"]
              and all(g is not None for g in (grades14 or [])),
              f"reviewers={reviewers14}", failures)

        # ==================== WR13 (row 173, boundary-capability-manifest): the extended
        # CapabilityManifest + identity_enforcement posture, BOTH POLARITIES ====================
        # ABSENT polarity: WORLD (this file's own main `world`, CHAIN_FULL -- through s59, one
        # short of s60/s61/s64) already proves s58_missives True (s59's own missive_open_threads
        # ships on this chain) while s60_entitlement/s61_signatures/s64_delegation read False --
        # a genuinely mixed manifest, not a vacuous all-True or all-False reading.
        print("== WR13: capability manifest (s58/s60/s61/s64) + identity_enforcement posture ==")
        status_h1, health1 = bs_fixtures.http_get(f"{base}/health")
        caps1 = health1.get("capabilities", {}) if isinstance(health1, dict) else {}
        check("wr13-capability-manifest-absent-polarity-on-chain-full",
              status_h1 == 200 and caps1.get("s58_missives") is True
              and caps1.get("s60_entitlement") is False
              and caps1.get("s61_signatures") is False
              and caps1.get("s64_delegation") is False,
              f"status={status_h1} capabilities={caps1}", failures)
        check("wr13-identity-enforcement-default-grace",
              status_h1 == 200 and health1.get("identity_enforcement") == "grace",
              f"status={status_h1} identity_enforcement={health1.get('identity_enforcement')!r} "
              f"(scratch multiplex config never sets the key -- DEFAULT_IDENTITY_ENFORCEMENT "
              f"applies)", failures)

        # PRESENT polarity: WR7's own world (CHAIN_S68 -- through s68, so s60/s61/s64 ALL
        # applied) reused here rather than re-birthed -- ADR-0012 P1, the same world already
        # proved healthy above. A SECOND server process against the SAME schema, config-only
        # different (identity_enforcement="enforce"), proves the posture is read from config,
        # never from schema shape.
        if up7:
            cfg_path7_enforce = write_scratch_multiplex_config_enforce(wdir7.parent, world7)
            proc7b, port7b = bs_fixtures.start_server(cfg_path7_enforce)
            procs.append(proc7b)
            base7b = f"http://127.0.0.1:{port7b}/d/{world7}"
            up7b = bs_fixtures.wait_health(base7b)
            status_h2, health2 = bs_fixtures.http_get(f"{base7b}/health") if up7b else (0, {})
            caps2 = health2.get("capabilities", {}) if isinstance(health2, dict) else {}
            check("wr13-capability-manifest-present-polarity-on-chain-s68",
                  up7b and status_h2 == 200 and caps2.get("s58_missives") is True
                  and caps2.get("s60_entitlement") is True
                  and caps2.get("s61_signatures") is True
                  and caps2.get("s64_delegation") is True,
                  f"up7b={up7b} status={status_h2} capabilities={caps2}", failures)
            check("wr13-identity-enforcement-enforce-when-configured",
                  up7b and status_h2 == 200 and health2.get("identity_enforcement") == "enforce",
                  f"up7b={up7b} status={status_h2} "
                  f"identity_enforcement={health2.get('identity_enforcement')!r} (this deployment's "
                  f"own multiplex TOML carries identity_enforcement = \"enforce\")", failures)
            # The 2026-07-27-dated panel missive's own known consumer, named in this commission
            # verbatim: capabilities.s43_boundary must stay byte-unchanged by this additive build.
            check("wr13-known-consumer-s43-boundary-byte-unchanged",
                  up7b and status_h2 == 200 and caps2.get("s43_boundary") is True,
                  f"up7b={up7b} status={status_h2} s43_boundary={caps2.get('s43_boundary')}",
                  failures)
        else:
            for name in ("wr13-capability-manifest-present-polarity-on-chain-s68",
                         "wr13-identity-enforcement-enforce-when-configured",
                         "wr13-known-consumer-s43-boundary-byte-unchanged"):
                check(name, False, "UNEXERCISED: WR7's own s68-headed world never became healthy",
                      failures)

    finally:
        for p in procs:
            bs_fixtures.stop_server(p)
        bs_fixtures.teardown(world)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    print()
    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL WR CHECKS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
