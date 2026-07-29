#!/usr/bin/env python3
"""seen-red/ac-boundary-scope-filter/run_fixtures.py -- both-polarity witness for the boundary
scope filter (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §1b/§1c/§2/§4, work item
ac-boundary-scope-filter, ledger rows 639/812/814): serving/boundary_scope_filter.py, wired into
serving/boundary_service.py's `_json_read_response`.

REUSE, NOT RE-DERIVATION (ADR-0012 P1): this file loads TWO existing sibling fixture modules by
file path (the SAME trick `seen-red/ac-read-identity/run_fixtures.py` already established) --
`seen-red/s70-scope-binding/run_fixtures.py` (`s70fx`) for `CHAIN_S70`/`scaffold_classic`/
`bw_call`/`birth_via_boundary`/`register`/`psql_tuples`/`teardown` (the proven s70-headed
scaffold+kernel-write sequence), and `seen-red/boundary-service/run_fixtures.py` (`bs_fixtures`)
for `write_scratch_multiplex_config`/`start_server`/`wait_health`/`stop_server`/`http_get`/
`http_post_headers`/`CHAIN_B` (the proven HTTP-serving harness, and a pre-s70 world for the
capability-absent/regression leg). Neither sibling starts an HTTP server AND applies s70 at
once; this file is the first to combine them.

WHAT IS WITNESSED (this work item's own commission, both polarities, scratch, red first):
  - kind-class exclusion, all three disclosure tiers (marked/hash_stub/full) on a live scoped
    minted-principal GET, against a real HTTP server.
  - the SAME read, unscoped (a different, never-bound principal, and anonymous), byte-identical
    to a pre-s70 baseline world's own unfiltered response.
  - rows-family exclusion (an explicit row id) and work-item-lineage exclusion (an exact
    work_slug), each on the view/route that actually carries that column.
  - the read journal carries a typed redaction summary (family/value/disclosure_mode/count),
    never row content, alongside the ordinary identity/row_count fields §1a already writes.
  - GET /rows/{id} under a `full`-tier exclusion answers the SAME 404 shape as a genuinely
    absent row -- existence itself withheld.
  - an unarmed world (no scope ever bound) serves every exercised route BYTE-IDENTICALLY
    whether `cfg`/`view` are threaded through `_json_read_response` or not -- the regression
    bar this work item's own commission states verbatim.
  - `/meta`/`/health` advertise `s70_scope_filter` truthfully: true on the s70-headed world,
    false on a pre-s70 world (`bs_fixtures.CHAIN_B`).
  - the disclosure-mode default (a scope binding with no explicit tier reads as `marked`, this
    module's own documented choice) and the unknown-exclusion-family loud refusal, exercised
    directly against `boundary_scope_filter.apply_scope` in-process (no live substrate needed
    for a pure-function contract) -- alongside the thread-family match, exercised the SAME way
    since wiring a live missive thread through s58/s59 substrate is a heavier rig than a single
    exclusion-family's row-matching contract needs; DISCLOSED here as a lighter-weight witness
    for that one family, not a silent skip.
  - SSE ids-only: witnessed BY INSPECTION, not a live connection -- `events()`'s own route body
    (serving/boundary_service.py) contains no row-serialization call of any kind (spec's own
    words, quoted in that route's docstring: "no row payloads ... no kernel trigger"), so no
    code path exists for scoped-out content to reach it regardless of this build; unchanged by
    this build, so a live SSE leg would be testing a route this work item never touched.

FIX ROUND (adjudication row 889, closing a fresh-context review's BLOCKS on commit 4cf16621) --
three additional legs, plus a disclosed timing measurement:
  - leg6b, THE CRITICAL's own red: armed + allow-list (scope_surfaces set) + EMPTY exclusions --
    a surface NOT in the allow-list must be REFUSED wholesale (every row redacted as
    surface-not-granted), not silently served -- this is the exact shape the pre-fix
    `apply_scope` treated as a no-op (fetched scope_surfaces, never consulted it). A control
    leg on the SAME principal's GRANTED surface stays fully unredacted.
  - leg6c: armed with scope_surfaces NULL (no allow-list at all, no exclusions either -- a bare
    arming row) denies EVERY filtered route entirely -- the ASP-twin spec's own fail-closed
    arming rule (`scope_armed(P) :- scope_binding_row(P)`, `may_read_surface(P,S) :-
    scope_bound(P,S)`) applied literally: armed-with-no-surfaces derives no may_read_surface at
    all, never "everything" (a real, disclosed behavior change from the pre-fix-round build --
    legs 2-6 above now bind scope_surfaces explicitly so they keep demonstrating row-level
    exclusion rather than being swallowed by this denial).
  - leg6d: the full-tier withheld 404 for GET /rows/{id} renders the EXACT SAME `{"detail": "no
    row {id}"}` template row_by_id's own genuine-absence branch uses for that id -- verified by
    literal string equality, not merely status-code equality, and cross-checked against a
    genuinely nonexistent id rendering the identical template shape.
  - leg6e: DISCLOSED, not asserted -- the hot-path cost this filter adds for an unscoped minted
    caller (median of 30 requests, anonymous vs. minted-unscoped) and the scope-resolution
    TIMING asymmetry between a genuinely-absent and a full-tier-excluded GET /rows/{id} (bodies
    already proven byte-identical by leg6d; the wall-clock delta is a real residual, printed and
    recorded in boundary_scope_filter.py's own module docstring, never silently left unmeasured
    and never masked with a sleep).

Usage: python3 seen-red/ac-boundary-scope-filter/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
S70FX = REPO / "seen-red" / "s70-scope-binding" / "run_fixtures.py"
BS_FIXTURES = REPO / "seen-red" / "boundary-service" / "run_fixtures.py"

os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "serving"))
sys.path.insert(0, str(REPO / "bootstrap"))
import boundary_read_journal  # noqa: E402
import boundary_scope_filter  # noqa: E402  (this build's own new module -- unit legs call it directly)

_spec70 = importlib.util.spec_from_file_location("s70_scope_binding_fixtures_acbsf", S70FX)
assert _spec70 is not None and _spec70.loader is not None
s70fx = importlib.util.module_from_spec(_spec70)
sys.modules["s70_scope_binding_fixtures_acbsf"] = s70fx
_spec70.loader.exec_module(s70fx)

_specbs = importlib.util.spec_from_file_location("boundary_service_fixtures_acbsf", BS_FIXTURES)
assert _specbs is not None and _specbs.loader is not None
bs_fixtures = importlib.util.module_from_spec(_specbs)
sys.modules["boundary_service_fixtures_acbsf"] = bs_fixtures
_specbs.loader.exec_module(bs_fixtures)

assert s70fx.PGHOST == bs_fixtures.PGHOST and s70fx.PGDB == bs_fixtures.PGDB, (
    "the two sibling fixture modules must agree on which live db they target")

RUN_SUFFIX = str(os.getpid())
check = s70fx.check


def read_journal_lines(world_dir: Path) -> list[dict]:
    path = boundary_read_journal.journal_path(world_dir)
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def main() -> int:  # noqa: C901
    failures: list[str] = []
    procs: list = []
    world_main = f"acsfw{RUN_SUFFIX}"
    world_pre = f"acsfp{RUN_SUFFIX}"
    s70fx.teardown(world_main)
    s70fx.teardown(world_pre)
    try:
        # =================================================================================
        # UNIT LEGS (boundary_scope_filter.apply_scope, no live server needed): the
        # disclosure-mode default, the thread-family match, and the unknown-family loud
        # refusal -- see this module's own docstring for why these three ride in-process.
        # =================================================================================
        print("=== unit-disclosure-default-marked-when-null ===")

        class _FakeCfg:
            schema = "unused"

        def _fake_query(cfg, sql, extra_v=None):
            # fix round (row 889): scope_surfaces must now name the surface being read, or the
            # fail-closed allow-list gate denies the WHOLE surface before row-level exclusion
            # is even consulted (module docstring, "SURFACE ALLOW-LIST ENFORCEMENT") -- this
            # unit leg means to exercise the disclosure-mode default on a row-level exclusion,
            # so it grants the one surface it reads.
            return {"scope_surfaces": ["ledger_current"],
                    "scope_exclusions": [{"family": "kind-class", "value": "finding"}],
                    "scope_disclosure_mode": None}

        def _fake_regclass_exists(cfg, name):
            return True

        rows_in = [{"id": 1, "kind": "note"}, {"id": 2, "kind": "finding"}]
        result = boundary_scope_filter.apply_scope(
            rows_in, cfg=_FakeCfg(), view="ledger_current", id_field="id",
            resolution_case="minted", principal="7",
            query_json_fn=_fake_query, regclass_exists_fn=_fake_regclass_exists)
        check("unit-disclosure-default-marked-when-null",
              result.content == [{"id": 1, "kind": "note"},
                                  {"id": 2, "redacted": True,
                                   "scope": {"family": "kind-class", "value": "finding"}}],
              f"a scope binding with scope_disclosure_mode=None redacts as 'marked' (the "
              f"MOST-disclosing default) -- got {result.content!r}", failures)

        print("=== unit-thread-family-match ===")

        def _fake_query_thread(cfg, sql, extra_v=None):
            return {"scope_surfaces": ["missive_outbound"],
                    "scope_exclusions": [{"family": "thread", "value": "t-secret"}],
                    "scope_disclosure_mode": "full"}

        rows_thread = [{"id": 1, "missive_thread": "t-public"},
                       {"id": 2, "missive_thread": "t-secret"}]
        result_thread = boundary_scope_filter.apply_scope(
            rows_thread, cfg=_FakeCfg(), view="missive_outbound", id_field="id",
            resolution_case="minted", principal="7",
            query_json_fn=_fake_query_thread, regclass_exists_fn=_fake_regclass_exists)
        check("unit-thread-family-match-full-tier-drops-row",
              result_thread.content == [{"id": 1, "missive_thread": "t-public"}],
              f"a 'thread' exclusion under full disclosure drops the matching row entirely, no "
              f"marker -- got {result_thread.content!r}", failures)
        check("unit-thread-family-redaction-tally",
              result_thread.redactions == [{"family": "thread", "value": "t-secret",
                                             "disclosure_mode": "full", "count": 1}],
              f"the redaction summary names family/value/disclosure_mode/count, never row "
              f"content -- got {result_thread.redactions!r}", failures)

        print("=== unit-unknown-family-loud-refusal ===")

        def _fake_query_bad(cfg, sql, extra_v=None):
            return {"scope_surfaces": ["ledger_current"],
                    "scope_exclusions": [{"family": "not-a-real-family", "value": "x"}],
                    "scope_disclosure_mode": "marked"}

        threw = False
        try:
            boundary_scope_filter.apply_scope(
                [{"id": 1, "kind": "note"}], cfg=_FakeCfg(), view="ledger_current", id_field="id",
                resolution_case="minted", principal="7",
                query_json_fn=_fake_query_bad, regclass_exists_fn=_fake_regclass_exists)
        except ValueError:
            threw = True
        check("unit-unknown-family-loud-refusal",
              threw,
              "an exclusion entry naming a family outside the closed vocabulary raises loudly "
              "rather than silently passing rows through unfiltered (this should be impossible "
              "past the kernel's own scope_exclusions_shape_ok CHECK, but the row-matcher does "
              "not trust that silently)", failures)

        print("=== unit-vendor-and-anonymous-never-scoped ===")
        for case in ("vendor", "anonymous"):
            r = boundary_scope_filter.apply_scope(
                [{"id": 1, "kind": "finding"}], cfg=_FakeCfg(), view="ledger_current",
                id_field="id", resolution_case=case, principal=None,
                query_json_fn=_fake_query, regclass_exists_fn=_fake_regclass_exists)
            check(f"unit-{case}-passthrough-unchanged",
                  r.content == [{"id": 1, "kind": "finding"}] and r.redactions == [],
                  f"resolution_case={case!r} always passes through unchanged (no principal id "
                  f"this layer can safely bind a scope query to) -- got {r.content!r}", failures)

        print("=== unit-surface-not-granted-denies-whole-route (THE CRITICAL, in-process) ===")

        def _fake_query_allowlist_only(cfg, sql, extra_v=None):
            # armed, grants ONLY "work_item_current", excludes nothing -- the pre-fix build
            # treated an empty `scope_exclusions` as a total no-op regardless of
            # `scope_surfaces`; the fix must deny "ledger_current" wholesale here instead.
            return {"scope_surfaces": ["work_item_current"],
                    "scope_exclusions": None,
                    "scope_disclosure_mode": "marked"}

        result_denied = boundary_scope_filter.apply_scope(
            [{"id": 1, "kind": "note"}, {"id": 2, "kind": "finding"}],
            cfg=_FakeCfg(), view="ledger_current", id_field="id",
            resolution_case="minted", principal="7",
            query_json_fn=_fake_query_allowlist_only, regclass_exists_fn=_fake_regclass_exists)
        check("unit-surface-not-granted-denies-whole-route",
              result_denied.content == [
                  {"id": 1, "redacted": True,
                   "scope": {"family": "surface-not-granted", "value": "ledger_current"}},
                  {"id": 2, "redacted": True,
                   "scope": {"family": "surface-not-granted", "value": "ledger_current"}}]
              and result_denied.redactions == [
                  {"family": "surface-not-granted", "value": "ledger_current",
                   "disclosure_mode": "marked", "count": 2}],
              f"an allow-list binding that never granted 'ledger_current' must deny EVERY row "
              f"on that surface, not silently no-op past an empty scope_exclusions -- got "
              f"content={result_denied.content!r} redactions={result_denied.redactions!r}",
              failures)

        def _fake_query_granted(cfg, sql, extra_v=None):
            return {"scope_surfaces": ["ledger_current"],
                    "scope_exclusions": None,
                    "scope_disclosure_mode": "marked"}

        result_granted = boundary_scope_filter.apply_scope(
            [{"id": 1, "kind": "note"}], cfg=_FakeCfg(), view="ledger_current", id_field="id",
            resolution_case="minted", principal="7",
            query_json_fn=_fake_query_granted, regclass_exists_fn=_fake_regclass_exists)
        check("unit-surface-granted-no-exclusions-unrestricted-control",
              result_granted.content == [{"id": 1, "kind": "note"}]
              and result_granted.redactions == [],
              f"the SAME shape but WITH the surface granted must stay fully unredacted -- got "
              f"{result_granted.content!r}", failures)

        # =================================================================================
        # LIVE HTTP LEGS: an s70-headed scratch world, served over a real boundary_service.
        # =================================================================================
        print(f"== scaffolding s70-headed world {world_main} (chain ends {s70fx.CHAIN_S70[-1]}) ==")
        wm = s70fx.scaffold_classic(world_main, s70fx.CHAIN_S70)
        world_dir = wm.parent
        author = s70fx.birth_via_boundary(world_main)
        reviewer = s70fx.register(world_main, author, "reviewer")
        outsider = s70fx.register(world_main, author, "outsider")

        # A findings-shaped row (kind-class target) and an ordinary note (control), both
        # authored so a real ledger row exists for each.
        v_finding = s70fx.bw_call(world_main, "ledger_write", {
            "kind": "finding", "statement": "ac-boundary-scope-filter: the excluded finding",
            "actor": author})
        v_note = s70fx.bw_call(world_main, "ledger_write", {
            "kind": "note", "statement": "ac-boundary-scope-filter: the visible note",
            "actor": author})
        assert v_finding["disposition"] == "accepted" and v_note["disposition"] == "accepted"
        finding_id = v_finding["row_id"]

        # A work item, for the work-item-lineage family.
        v_work = s70fx.bw_call(world_main, "ledger_write", {
            "kind": "work_opened", "work_slug": "acbsf-excluded-item",
            "work_title": "ac-boundary-scope-filter excluded work item",
            "statement": "ac-boundary-scope-filter: excluded work item", "actor": author})
        assert v_work["disposition"] == "accepted"

        cfg = bs_fixtures.write_scratch_multiplex_config(world_dir, world_main)
        proc, port = bs_fixtures.start_server(cfg)
        procs.append(proc)
        base = f"http://127.0.0.1:{port}/d/{world_main}"
        assert bs_fixtures.wait_health(base), "server never became healthy"

        reviewer_headers = {"X-Autoharn-Minted-Principal": str(reviewer)}
        outsider_headers = {"X-Autoharn-Minted-Principal": str(outsider)}

        def _get_headers(base_url, headers, path="/rows/current"):
            req = urllib.request.Request(f"{base_url}{path}", headers=headers, method="GET")
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.status, json.loads(resp.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read())

        # -----------------------------------------------------------------------------------
        # LEG 1: UNARMED-WORLD-BYTE-IDENTICAL -- before any scope is bound, reviewer's own
        # GET /rows/current is byte-identical to anonymous's own (the fail-safe regression
        # bar this work item's own commission states verbatim).
        # -----------------------------------------------------------------------------------
        print("=== leg1-unarmed-world-byte-identical ===")
        st_anon0, body_anon0 = bs_fixtures.http_get(f"{base}/rows/current")
        st_rev0, body_rev0 = _get_headers(base, reviewer_headers)
        check("leg1-unarmed-world-byte-identical",
              st_anon0 == 200 and st_rev0 == 200 and body_anon0 == body_rev0
              and any(r.get("kind") == "finding" for r in body_anon0),
              f"before any scope bind, reviewer's own read == anonymous's own read "
              f"(equal={body_anon0 == body_rev0}); status anon={st_anon0} reviewer={st_rev0}",
              failures)

        # -----------------------------------------------------------------------------------
        # LEG 2: KIND-CLASS EXCLUSION, marked tier.
        # -----------------------------------------------------------------------------------
        print("=== leg2-kind-class-exclusion-marked ===")
        v_bind_marked = s70fx.bw_call(world_main, "ledger_write", {
            "kind": "principal_scope_bound", "statement": "reviewer scoped: exclude findings",
            "actor": author, "principal_subject": reviewer, "principal_binding_active": "true",
            # fix round (adjudication row 889): scope_surfaces is now REQUIRED to grant this
            # reviewer's own reads of /rows/current -- see boundary_scope_filter's own module
            # docstring, "SURFACE ALLOW-LIST ENFORCEMENT": a binding with scope_surfaces left
            # NULL is armed-with-nothing-granted and now reads NOTHING at all (leg-b below
            # exercises exactly that state); this binding's OWN intent is "grant ledger_current,
            # exclude findings within it", so it must say so.
            "scope_surfaces": ["ledger_current"],
            "scope_exclusions": [{"family": "kind-class", "value": "finding"}],
            "scope_disclosure_mode": "marked"})
        assert v_bind_marked["disposition"] == "accepted", v_bind_marked
        st_rev1, body_rev1 = _get_headers(base, reviewer_headers)
        finding_row_rev1 = next((r for r in body_rev1 if r.get("id") == finding_id), None)
        note_row_rev1 = next((r for r in body_rev1
                               if r.get("statement", "").endswith("the visible note")), None)
        check("leg2-marked-tier-redacts-content-keeps-marker",
              st_rev1 == 200 and finding_row_rev1 is not None
              and finding_row_rev1.get("redacted") is True
              and finding_row_rev1.get("scope") == {"family": "kind-class", "value": "finding"}
              and "statement" not in finding_row_rev1
              and note_row_rev1 is not None and note_row_rev1.get("redacted") is None,
              f"reviewer's own read: finding row={finding_row_rev1!r} note row present unredacted="
              f"{note_row_rev1 is not None and 'redacted' not in note_row_rev1}", failures)
        st_out1, body_out1 = _get_headers(base, outsider_headers)
        # Compared against a FRESH anonymous read taken now, not `body_anon0` (which was
        # captured before the scope-bind write above -- and a principal_scope_bound row is
        # itself a new ledger row, so the pre-bind baseline is stale by construction, not a
        # sign of any scoping leak).
        st_anon1, body_anon1 = bs_fixtures.http_get(f"{base}/rows/current")
        check("leg2-unscoped-outsider-sees-content-unchanged",
              st_out1 == 200 and body_out1 == body_anon1,
              f"outsider (no scope bound) reads byte-identically to a fresh, unscoped "
              f"anonymous read taken at the same point -- equal={body_out1 == body_anon1}",
              failures)

        # -----------------------------------------------------------------------------------
        # LEG 3: hash_stub tier -- content withheld, row_hash disclosed and verifiable.
        # -----------------------------------------------------------------------------------
        print("=== leg3-hash-stub-tier ===")
        v_bind_hash = s70fx.bw_call(world_main, "ledger_write", {
            "kind": "principal_scope_bound", "statement": "reviewer rebound: hash_stub",
            "supersedes": v_bind_marked["row_id"],
            "actor": author, "principal_subject": reviewer, "principal_binding_active": "true",
            "scope_surfaces": ["ledger_current"],
            "scope_exclusions": [{"family": "kind-class", "value": "finding"}],
            "scope_disclosure_mode": "hash_stub"})
        assert v_bind_hash["disposition"] == "accepted", v_bind_hash
        st_rev2, body_rev2 = _get_headers(base, reviewer_headers)
        finding_row_rev2 = next((r for r in body_rev2 if r.get("id") == finding_id), None)
        real_finding = next(r for r in body_anon0 if r.get("id") == finding_id)
        check("leg3-hash-stub-content-withheld-hash-verifiable",
              finding_row_rev2 is not None and finding_row_rev2.get("redacted") is True
              and "statement" not in finding_row_rev2
              and finding_row_rev2.get("row_hash") == real_finding.get("row_hash")
              and finding_row_rev2.get("row_hash") is not None,
              f"hash_stub marker={finding_row_rev2!r}; real row_hash={real_finding.get('row_hash')!r}",
              failures)

        # -----------------------------------------------------------------------------------
        # LEG 4: full tier -- the row does not cross at all (list route: absent; single-row
        # route: the SAME 404 shape as genuinely-absent).
        # -----------------------------------------------------------------------------------
        print("=== leg4-full-tier ===")
        v_bind_full = s70fx.bw_call(world_main, "ledger_write", {
            "kind": "principal_scope_bound", "statement": "reviewer rebound: full",
            "supersedes": v_bind_hash["row_id"],
            "actor": author, "principal_subject": reviewer, "principal_binding_active": "true",
            # This binding is read via BOTH /rows/current (view="ledger_current") and
            # /rows/{finding_id} (view="ledger") below -- both surfaces must be granted or the
            # single-row leg would 404 for "surface not granted" rather than for the full-tier
            # exclusion this leg means to exercise (leg-d relies on this being the SAME reason).
            "scope_surfaces": ["ledger_current", "ledger"],
            "scope_exclusions": [{"family": "kind-class", "value": "finding"}],
            "scope_disclosure_mode": "full"})
        assert v_bind_full["disposition"] == "accepted", v_bind_full
        st_rev3, body_rev3 = _get_headers(base, reviewer_headers)
        st_anon2, body_anon2 = bs_fixtures.http_get(f"{base}/rows/current")
        finding_present = any(r.get("id") == finding_id for r in body_rev3)
        check("leg4-full-tier-list-route-row-absent-no-marker",
              st_rev3 == 200 and st_anon2 == 200 and not finding_present
              and len(body_rev3) == len(body_anon2) - 1,
              f"full-tier: finding present in reviewer's list={finding_present}; "
              f"scope-relative count reviewer={len(body_rev3)} vs a fresh unscoped read taken "
              f"at the same point={len(body_anon2)} (must differ by exactly 1, the excluded row)",
              failures)
        st_single, body_single = _get_headers(
            base, reviewer_headers, path=f"/rows/{finding_id}")
        check("leg4-full-tier-single-row-route-404s",
              st_single == 404,
              f"GET /rows/{{id}} for a full-tier-excluded row -- status={st_single} "
              f"body={body_single}", failures)

        # -----------------------------------------------------------------------------------
        # LEG 5: rows-family exclusion (an explicit id set) -- unbind, rebind on a fresh
        # principal with a 'rows' exclusion naming the note's own id.
        # -----------------------------------------------------------------------------------
        print("=== leg5-rows-family-exclusion ===")
        note_id = next(r["id"] for r in body_anon0
                        if r.get("statement", "").endswith("the visible note"))
        second_reviewer = s70fx.register(world_main, author, "second-reviewer")
        v_bind_rows = s70fx.bw_call(world_main, "ledger_write", {
            "kind": "principal_scope_bound", "statement": "second-reviewer scoped: exclude one row",
            "actor": author, "principal_subject": second_reviewer,
            "principal_binding_active": "true",
            "scope_surfaces": ["ledger_current"],
            "scope_exclusions": [{"family": "rows", "value": [note_id]}],
            "scope_disclosure_mode": "marked"})
        assert v_bind_rows["disposition"] == "accepted", v_bind_rows
        st_rev4, body_rev4 = _get_headers(base, {"X-Autoharn-Minted-Principal": str(second_reviewer)})
        note_row_rev4 = next((r for r in body_rev4 if r.get("id") == note_id), None)
        finding_row_rev4 = next((r for r in body_rev4 if r.get("id") == finding_id), None)
        check("leg5-rows-family-excludes-only-named-id",
              note_row_rev4 is not None and note_row_rev4.get("redacted") is True
              and finding_row_rev4 is not None and "redacted" not in finding_row_rev4,
              f"note (named row) redacted={note_row_rev4}; finding (not named) untouched="
              f"{finding_row_rev4 is not None and 'redacted' not in finding_row_rev4}", failures)

        # -----------------------------------------------------------------------------------
        # LEG 6: work-item-lineage exclusion on GET /work/items.
        # -----------------------------------------------------------------------------------
        print("=== leg6-work-item-lineage-exclusion ===")
        third_reviewer = s70fx.register(world_main, author, "third-reviewer")
        v_bind_work = s70fx.bw_call(world_main, "ledger_write", {
            "kind": "principal_scope_bound", "statement": "third-reviewer scoped: exclude one work item",
            "actor": author, "principal_subject": third_reviewer,
            "principal_binding_active": "true",
            "scope_surfaces": ["work_item_current"],
            "scope_exclusions": [{"family": "work-item-lineage", "value": "acbsf-excluded-item"}],
            "scope_disclosure_mode": "marked"})
        assert v_bind_work["disposition"] == "accepted", v_bind_work
        st_wi, body_wi = _get_headers(
            base, {"X-Autoharn-Minted-Principal": str(third_reviewer)}, path="/work/items")
        wi_row = next((r for r in body_wi if r.get("slug") == "acbsf-excluded-item"), None)
        check("leg6-work-item-lineage-excludes-named-slug",
              st_wi == 200 and wi_row is not None and wi_row.get("redacted") is True
              and wi_row.get("scope") == {"family": "work-item-lineage",
                                           "value": "acbsf-excluded-item"},
              f"GET /work/items for third-reviewer: excluded item row={wi_row!r}", failures)

        # -----------------------------------------------------------------------------------
        # LEG 6b (fix round, adjudication row 889 -- THE CRITICAL): armed + allow-list +
        # EMPTY exclusions -- a non-listed surface must be REFUSED, not silently served. This
        # is the exact shape commit 4cf16621's review found leaking (scope_surfaces fetched,
        # never enforced): a binding that grants ONLY "work_item_current" and excludes
        # NOTHING must still deny "ledger_current" entirely to that same principal.
        # -----------------------------------------------------------------------------------
        print("=== leg6b-surface-allow-list-denies-non-listed-surface (THE CRITICAL) ===")
        fourth_reviewer = s70fx.register(world_main, author, "fourth-reviewer")
        v_bind_allowlist = s70fx.bw_call(world_main, "ledger_write", {
            "kind": "principal_scope_bound",
            "statement": "fourth-reviewer scoped: allow-list only, no row exclusions",
            "actor": author, "principal_subject": fourth_reviewer,
            "principal_binding_active": "true",
            "scope_surfaces": ["work_item_current"],
            "scope_disclosure_mode": "marked"})
        assert v_bind_allowlist["disposition"] == "accepted", v_bind_allowlist
        fourth_headers = {"X-Autoharn-Minted-Principal": str(fourth_reviewer)}
        # Fresh anonymous baseline taken NOW (not body_anon0, which predates every scope-bind/
        # work-item write since -- a stale count would falsely look like leakage/shrinkage).
        st_anon_now6b, body_anon_now6b = bs_fixtures.http_get(f"{base}/rows/current")
        st_deny, body_deny = _get_headers(base, fourth_headers, path="/rows/current")
        check("leg6b-non-listed-surface-fully-redacted",
              st_deny == 200 and st_anon_now6b == 200
              and isinstance(body_deny, list) and len(body_deny) == len(body_anon_now6b)
              and all(r.get("redacted") is True for r in body_deny)
              and all("statement" not in r for r in body_deny)
              and all(r.get("scope") == {"family": "surface-not-granted", "value": "ledger_current"}
                      for r in body_deny),
              f"fourth-reviewer (granted ONLY work_item_current, no exclusions) reads "
              f"/rows/current (ledger_current, NOT granted) -- every row must be redacted as "
              f"surface-not-granted, none may carry its own statement text; got "
              f"{body_deny[:2]!r}{'...' if len(body_deny) > 2 else ''}", failures)
        st_allow, body_allow = _get_headers(base, fourth_headers, path="/work/items")
        check("leg6b-listed-surface-unrestricted-control",
              st_allow == 200 and isinstance(body_allow, list)
              and all("redacted" not in r for r in body_allow) and len(body_allow) >= 1,
              f"the SAME fourth-reviewer's read of work_item_current (granted, no exclusions) "
              f"stays fully unredacted -- got {body_allow!r}", failures)

        # -----------------------------------------------------------------------------------
        # LEG 6c (fix round, adjudication row 889): armed + NULL scope_surfaces (no allow-list
        # bound at all, no exclusions either -- a bare arming row) -- filtered routes must
        # serve NOTHING for that principal, the fail-closed default (design/
        # FABLE-ENGINE-ENTITLEMENT-SCOPE-ASP-TWIN-SPEC.md sec1c: "armed-with-no-surfaces
        # derives no may_read_surface at all"), never the pre-fix no-op that would have let an
        # empty-looking binding read everything.
        # -----------------------------------------------------------------------------------
        print("=== leg6c-armed-with-null-scope-surfaces-denies-everything ===")
        fifth_reviewer = s70fx.register(world_main, author, "fifth-reviewer")
        v_bind_bare = s70fx.bw_call(world_main, "ledger_write", {
            "kind": "principal_scope_bound",
            "statement": "fifth-reviewer scoped: bare arming, no surfaces, no exclusions",
            "actor": author, "principal_subject": fifth_reviewer,
            "principal_binding_active": "true"})
        assert v_bind_bare["disposition"] == "accepted", v_bind_bare
        fifth_headers = {"X-Autoharn-Minted-Principal": str(fifth_reviewer)}
        st_anon_now6c, body_anon_now6c = bs_fixtures.http_get(f"{base}/rows/current")
        st_bare, body_bare = _get_headers(base, fifth_headers, path="/rows/current")
        check("leg6c-bare-arming-denies-every-route",
              st_bare == 200 and st_anon_now6c == 200
              and isinstance(body_bare, list) and len(body_bare) == len(body_anon_now6c)
              and all(r.get("redacted") is True for r in body_bare)
              and all("statement" not in r for r in body_bare),
              f"fifth-reviewer (armed, NULL scope_surfaces, no exclusions) reads /rows/current "
              f"-- every row must be redacted, none may leak its own statement text; got "
              f"{body_bare[:2]!r}{'...' if len(body_bare) > 2 else ''}", failures)

        # -----------------------------------------------------------------------------------
        # LEG 6d (fix round, adjudication row 889, MODERATE): the full-tier withheld body for
        # GET /rows/{finding_id} (reviewer, v_bind_full above) must be BYTE-IDENTICAL to this
        # SAME route's own genuine-absence body for the SAME id -- not merely the same STATUS
        # code. `row_by_id`'s own genuine-absence branch renders `f"no row {row_id}"` for a
        # truly nonexistent id; verified here by exact string equality against that literal
        # template for the EXCLUDED id, and independently against a genuinely nonexistent id.
        # -----------------------------------------------------------------------------------
        print("=== leg6d-full-tier-404-byte-identical-to-genuine-absence ===")
        check("leg6d-full-tier-body-matches-genuine-absence-template",
              st_single == 404 and body_single == {"detail": f"no row {finding_id}"},
              f"GET /rows/{{finding_id}} under full-tier exclusion must render EXACTLY "
              f"row_by_id's own genuine-absence template for this id -- got {body_single!r}",
              failures)
        genuinely_missing_id = 999_999_999
        st_missing, body_missing = _get_headers(
            base, reviewer_headers, path=f"/rows/{genuinely_missing_id}")
        check("leg6d-genuine-absence-same-template-different-id",
              st_missing == 404
              and body_missing == {"detail": f"no row {genuinely_missing_id}"},
              f"a genuinely nonexistent id renders the SAME template (proving both code paths "
              f"share the one absence-message shape, never a scope-specific dialect) -- got "
              f"{body_missing!r}", failures)
        check("leg6d-bodies-share-shape-differ-only-by-id",
              set(body_single.keys()) == set(body_missing.keys()) == {"detail"},
              f"both bodies carry EXACTLY the {{'detail': ...}} shape, no extra scope-leaking "
              f"field on either side -- single={body_single!r} missing={body_missing!r}",
              failures)

        # -----------------------------------------------------------------------------------
        # LEG 6e (MINOR, fix round row 889; disclosed timing measurement, house precedent
        # shape -- "measured, not asserted"): the hot-path cost of this filter for a minted
        # caller this module ultimately passes through UNCHANGED (outsider: minted, never
        # bound -- the common case), and the disclosed timing asymmetry between a genuinely-
        # absent GET /rows/{id} and a full-tier-excluded EXISTING row's GET /rows/{id} (both
        # now byte-identical in BODY, per leg6d, but not necessarily in wall-clock time -- see
        # boundary_scope_filter's own module docstring, "DISCLOSED RESIDUAL"). 30 requests
        # each, median wall-clock delta; printed, never asserted against a fixed threshold
        # (a hot-path timing number is diagnostic, not a pass/fail gate -- CLAUDE.md's own
        # "estimates are hazard detection" posture, not an economizing one).
        # -----------------------------------------------------------------------------------
        print("=== leg6e-timing-measurement (disclosed, not asserted) ===")
        _TIMING_N = 30

        def _median_ms(fn) -> float:
            samples = []
            for _ in range(_TIMING_N):
                t0 = time.monotonic()
                fn()
                samples.append((time.monotonic() - t0) * 1000.0)
            samples.sort()
            return samples[len(samples) // 2]

        anon_ms = _median_ms(lambda: bs_fixtures.http_get(f"{base}/rows/current"))
        outsider_ms = _median_ms(lambda: _get_headers(base, outsider_headers))
        hotpath_overhead_pct = (
            ((outsider_ms - anon_ms) / anon_ms * 100.0) if anon_ms > 0 else float("nan"))
        print(f"MEASURED hot-path cost: anonymous median={anon_ms:.3f}ms "
              f"outsider(minted,unscoped) median={outsider_ms:.3f}ms "
              f"overhead={hotpath_overhead_pct:+.1f}% "
              f"(disclosed in boundary_scope_filter.py's own module docstring; N={_TIMING_N})")

        missing_ms = _median_ms(
            lambda: _get_headers(base, reviewer_headers, path=f"/rows/{genuinely_missing_id}"))
        excluded_ms = _median_ms(
            lambda: _get_headers(base, reviewer_headers, path=f"/rows/{finding_id}"))
        timing_delta_ms = excluded_ms - missing_ms
        print(f"MEASURED scope-resolution timing asymmetry: genuinely-absent median="
              f"{missing_ms:.3f}ms full-tier-excluded median={excluded_ms:.3f}ms "
              f"delta={timing_delta_ms:+.3f}ms (disclosed in boundary_scope_filter.py's own "
              f"module docstring and this fix round's report, body already verified "
              f"byte-identical by leg6d -- this is a TIME, not a content, residual)")

        # -----------------------------------------------------------------------------------
        # LEG 7: the read journal carries a typed redaction summary, never row content.
        # -----------------------------------------------------------------------------------
        print("=== leg7-read-journal-typed-redaction-summary ===")
        lines = read_journal_lines(world_dir)
        rows_current_lines = [
            l for l in lines
            if l.get("route") == f"/d/{world_main}/rows/current"
            and l.get("identity", {}).get("principal") == str(reviewer)
        ]
        with_redactions = [l for l in rows_current_lines if l.get("redactions")]
        raw_journal_text = boundary_read_journal.journal_path(world_dir).read_text(encoding="utf-8")
        check("leg7-journal-carries-typed-redaction-summary",
              bool(with_redactions)
              and any(any(r.get("family") == "kind-class" and r.get("value") == "finding"
                          for r in l["redactions"]) for l in with_redactions),
              f"reviewer's own /rows/current journal lines carrying redactions: {with_redactions}",
              failures)
        check("leg7-journal-never-carries-excluded-statement-text",
              "the excluded finding" not in raw_journal_text,
              "the excluded finding row's own statement text must never appear in the read "
              "journal (redactions are family/value/disclosure_mode/count summaries only)",
              failures)

        # -----------------------------------------------------------------------------------
        # LEG 8: /meta advertises s70_scope_filter=true on this s70-headed world.
        # -----------------------------------------------------------------------------------
        print("=== leg8-meta-advertises-s70-scope-filter-true ===")
        st_meta, body_meta = bs_fixtures.http_get(f"{base}/health")
        check("leg8-meta-advertises-s70-scope-filter-true",
              st_meta == 200 and isinstance(body_meta, dict)
              and body_meta.get("capabilities", {}).get("s70_scope_filter") is True,
              f"GET /health capabilities.s70_scope_filter={body_meta.get('capabilities', {}).get('s70_scope_filter') if isinstance(body_meta, dict) else '?'}",
              failures)

        bs_fixtures.stop_server(proc)
        procs.remove(proc)

        # =================================================================================
        # PRE-S70 WORLD: /meta advertises s70_scope_filter=false, and every route byte-
        # identical to this build's own pre-filter behavior (no principal_scopes object at
        # all -- apply_scope's own capability-absent passthrough).
        # =================================================================================
        print(f"== scaffolding pre-s70 world {world_pre} (chain ends {bs_fixtures.CHAIN_B[-1]}) ==")
        wp = bs_fixtures.scaffold_classic(world_pre, bs_fixtures.CHAIN_B)
        author_pre, _svc_pre = bs_fixtures.birth_via_boundary(world_pre)
        cfg_pre = bs_fixtures.write_scratch_multiplex_config(wp.parent, world_pre)
        proc_pre, port_pre = bs_fixtures.start_server(cfg_pre)
        procs.append(proc_pre)
        base_pre = f"http://127.0.0.1:{port_pre}/d/{world_pre}"
        assert bs_fixtures.wait_health(base_pre), "pre-s70 server never became healthy"

        st_meta_pre, body_meta_pre = bs_fixtures.http_get(f"{base_pre}/health")
        check("leg9-pre-s70-meta-advertises-false",
              st_meta_pre == 200 and isinstance(body_meta_pre, dict)
              and body_meta_pre.get("capabilities", {}).get("s70_scope_filter") is False,
              f"pre-s70 world GET /health capabilities.s70_scope_filter="
              f"{body_meta_pre.get('capabilities', {}).get('s70_scope_filter') if isinstance(body_meta_pre, dict) else '?'}",
              failures)
        st_pre_anon, body_pre_anon = bs_fixtures.http_get(f"{base_pre}/rows/current")
        st_pre_minted, body_pre_minted = _get_headers(
            base_pre, {"X-Autoharn-Minted-Principal": str(author_pre)})
        check("leg9-pre-s70-world-byte-identical-regardless-of-identity",
              st_pre_anon == 200 and st_pre_minted == 200 and body_pre_anon == body_pre_minted,
              f"a pre-s70 world (no principal_scopes object at all) serves byte-identically "
              f"whether the caller is anonymous or minted -- equal={body_pre_anon == body_pre_minted}",
              failures)

        bs_fixtures.stop_server(proc_pre)
        procs.remove(proc_pre)

    finally:
        for p in procs:
            try:
                bs_fixtures.stop_server(p)
            except Exception:
                pass
        s70fx.teardown(world_main)
        s70fx.teardown(world_pre)

    print(f"\n{'ALL GREEN' if not failures else f'{len(failures)} FAILURE(S): ' + ', '.join(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
