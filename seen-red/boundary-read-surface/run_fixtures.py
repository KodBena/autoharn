#!/usr/bin/env python3
"""seen-red/boundary-read-surface/run_fixtures.py -- WR1-WR5, design/
FABLE-BOUNDARY-READ-SURFACE-SPEC.md §"Witnesses" (ratified ledger decision row 1652, amending
design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md, ledger row 1631). Real infra, no mocks:
a CLASSIC-scaffolded world through the full kernel/lineage chain (s15..s50, so every one of
`VIEW_REGISTRY`'s eleven views is a genuinely present relation, not merely a capability_absent
leg -- WR1's "per view, not umbrella" bar needs a world where every view actually exists), a real
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
import migrate_core  # noqa: E402  (bootstrap/migrate_core.py -- the SAME manifest _lineage_head reuses, for WR4's ground truth)

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

# The full kernel/lineage chain through s57 -- every VIEW_REGISTRY member is a genuinely present
# relation on this chain (s44 model_attestations, s46 credited_current/model_defeated_rows, s36
# standing_decisions -- none of which CHAIN_B alone, s43-headed, carries; s56's
# reservations_outstanding/review_verdicts are the two newest members, closing-batch build ledger
# rows 1176/1178 -- s57 carries no view of its own but is included so this fixture's world
# genuinely sits at the current lineage head, matching WR4's meta.lineage_head expectation).
CHAIN_FULL = CHAIN_B + [
    "s44-model-identity-attestation.sql", "s45-standing-lifecycle.sql",
    "s46-credited-views.sql", "s47-claim-on-closed-refusal.sql",
    "s48-review-witness-existence.sql", "s49-journaler-overflow-guard.sql",
    "s50-defeat-input-raw-domain.sql", "s51-artifact-store.sql",
    "s52-artifact-witness-check.sql", "s53-belief-substrate.sql",
    "s54-belief-views.sql", "s55-dispatch-grain-independence.sql",
    "s56-reservation-residue.sql", "s57-obligation-revocation-event.sql",
]


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
    return json.dumps(row, sort_keys=True)


def row_set_equal(a: list, b: list) -> bool:
    return sorted(canon(r) for r in a) == sorted(canon(r) for r in b)


def direct_view_rows(world: str, view: str) -> list:
    out = bs_fixtures.psql_tuples(
        f"SET ROLE {world}_rw; "
        f"SELECT coalesce(jsonb_agg(t), '[]'::jsonb)::text FROM {world}.{view} t;")
    return json.loads(out)


def birth_fixture_rows(base: str, world: str, author: int) -> None:
    """Populates every VIEW_REGISTRY member with at least one row, through the boundary's OWN
    write routes (never a raw INSERT -- this fixture is itself a served-boundary consumer).
    `credited_current`/`model_defeated_rows` are DELIBERATELY LEFT EMPTY (both sides of WR1's
    comparison are then the empty set, still a valid -- if less rigorous -- equality proof):
    populating a genuine `model_defeated_rows` member needs a `principal_competence_granted`
    row with `principal_binding_active` in force, whose exact trigger-derived shape is s41/s45
    machinery well outside this amendment's own scope to re-derive here; named rather than
    silently assumed."""
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
    w({"kind": "note", "statement": "WR fixture retracting the opening act", "actor": author,
       "supersedes": opened["row_id"]})

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
        birth_fixture_rows(base, world, author)
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
        print("== WR5: per-deployment saturation still fires on a /views/ route (WM4 method) ==")
        world_stalled = f"wrfxstall{RUN_SUFFIX}"
        tmp_cfg5 = Path(tempfile.mkdtemp(prefix="wr5-cfg-"))
        tmps.append(tmp_cfg5)
        cfg5 = tmp_cfg5 / "boundary-multiplex.toml"
        cfg5.write_text(
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
        n_deployments5 = 2
        expected_per_dep_limit = boundary_service.compute_per_deployment_limit(n_deployments5)
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
