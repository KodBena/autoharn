#!/usr/bin/env python3
"""seen-red/ac-read-identity/run_fixtures.py -- both-polarity witness for design/
FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §1a (work item ac-read-identity, ledger rows
643/644): read-path identity resolution + read journaling, serving layer.

REUSE, NOT RE-DERIVATION (ADR-0012 P1): every scaffolding helper below (`scaffold_classic`,
`birth_via_boundary`, `write_scratch_multiplex_config`, `start_server`, `wait_health`,
`stop_server`, `psql_tuples`, `psql_raw`, `sh`, `check`, `teardown`, `CHAIN_B`, `PGHOST`,
`PGDB`, `RUN_SUFFIX`) is IMPORTED from `seen-red/boundary-service/run_fixtures.py`, loaded by
file path under its own distinct module name -- the SAME trick `seen-red/boundary-sse-events/
run_fixtures.py` already established for the identical reason (hyphenated directory names are
not valid Python package components). This file adds ONLY what §1a's own witness plan needs: a
single WORLD B (s43 head, so a real accepted write exists for the POST-unchanged leg), the
identity-header helper `http_get_headers` (the GET-with-headers sibling of the shared module's
own `http_post_headers`), the read-journal file's own reader/asserter, and the six witness legs
themselves (identity-conduit byte-identity, per-channel journal correctness, zero-row-content,
`/meta` advertisement, POST byte-unchanged, and the performance disclosure).

WORLD: ONE WORLD_B-shape world (CHAIN_B, s43 head) -- `birth_via_boundary` gives this witness a
real author principal, a real accepted-write boundary, and FIVE pre-existing ledger rows (the
birth acts themselves), which is what makes `GET /rows/current`'s own `row_count` field a
meaningful, non-vacuous assertion below (row_count == 5, not 0).

PERFORMANCE METHODOLOGY, DISCLOSED (spec: "journaling must not add a blocking write on the hot
read path in a way that measurably slows reads ... measure before/after ... report the delta"):
this witness does NOT swap production code paths and re-run the same live walk twice (that
would need a second server build with the journal call excised, e.g. via a symlinked-package
trick -- workable, but heavier and more fragile than the actual question requires). Instead it
decomposes the claim into its two real components, both MEASURED, never asserted: (1) the live
walk's own per-request wall-clock average over 1000 sequential `GET /rows/current` calls
against the real scratch server (journaling ON, the shipped configuration -- every one of
those 1000 requests already pays the psql subprocess round-trip, the dominant cost on this hot
path by construction); (2) `boundary_read_journal.append_read`'s OWN isolated per-call cost,
measured by calling it 1000 times directly, in-process, against the SAME journal file the live
walk above just wrote to -- the exact code path, isolated from HTTP/psql variance. The delta
this witness reports is (2) as a fraction of (1): if the isolated per-call write cost is a
small fraction of the walk's own per-request average, the write is not a measurable slowdown on
this hot path; if it is not small, that is exactly the finding the spec asks this witness to
surface honestly rather than paper over.

Usage: python3 seen-red/ac-read-identity/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SIBLING = REPO / "seen-red" / "boundary-service" / "run_fixtures.py"
# Ledger row 744, fix-round leg (review CLEARS with one MODERATE): world_b's own CHAIN_B
# (s43 head) carries no s51-artifact-store, so its own capability probe refuses the artifact
# routes entirely -- the fix this leg witnesses (GET /artifacts/{hash}'s content route now
# binds the read journal's row_count exactly like its .../stat sibling) needs a real,
# capability-PRESENT artifact route to exercise. Rather than re-deriving an s51-capable
# scaffold+birth sequence, this file loads seen-red/legacy-led-retirement-part-ab-boundary/
# run_fixtures.py THE SAME WAY it already loads `bs_fixtures` below -- that module already
# banks a proven CHAIN_S57 (s43 through s57, s51 included) scaffold/apply_chain/birth
# sequence tailored to that later schema shape (bs_fixtures.birth_via_boundary's own payloads
# are shaped for CHAIN_B's s43 head specifically and do NOT carry forward cleanly onto s44+'s
# added constraints -- witnessed directly: a first attempt at extending CHAIN_B in-place with
# the s44-s51 tail and reusing birth_via_boundary hit a live
# principal_binding_active_kind_shape constraint violation on the very first birth act,
# because s44/s45 tighten that constraint's shape). ADR-0012 P1: reuse the sibling's own
# working mechanism, not a hand-rolled variant of it.
ARTIFACT_SIBLING = REPO / "seen-red" / "legacy-led-retirement-part-ab-boundary" / "run_fixtures.py"

sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "serving"))
sys.path.insert(0, str(REPO / "bootstrap"))
import boundary_read_journal  # noqa: E402  (this build's own new module -- the performance leg calls it directly)

# design/FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree this
# fixture starts (gates/fixture_census.py's own marker sweep, item 5, checks for this line).
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

_spec = importlib.util.spec_from_file_location("boundary_service_fixtures_ac_read_identity", SIBLING)
assert _spec is not None and _spec.loader is not None
bs_fixtures = importlib.util.module_from_spec(_spec)
sys.modules["boundary_service_fixtures_ac_read_identity"] = bs_fixtures
_spec.loader.exec_module(bs_fixtures)

_aspec = importlib.util.spec_from_file_location(
    "legacy_led_retirement_part_ab_boundary_fixtures_ac_read_identity", ARTIFACT_SIBLING)
assert _aspec is not None and _aspec.loader is not None
llrpab_fixtures = importlib.util.module_from_spec(_aspec)
sys.modules["legacy_led_retirement_part_ab_boundary_fixtures_ac_read_identity"] = llrpab_fixtures
_aspec.loader.exec_module(llrpab_fixtures)

RUN_SUFFIX = bs_fixtures.RUN_SUFFIX
CHAIN_B = bs_fixtures.CHAIN_B
PGHOST, PGDB = bs_fixtures.PGHOST, bs_fixtures.PGDB
check = bs_fixtures.check
sh = bs_fixtures.sh
assert llrpab_fixtures.PGHOST == PGHOST and llrpab_fixtures.PGDB == PGDB, (
    "the two sibling fixture modules must agree on which live db they target")


def http_get_bytes(url: str) -> tuple[int, bytes]:
    """The raw-bytes sibling of `bs_fixtures.http_get` -- the artifact CONTENT route (unlike
    every other GET route this fixture family exercises) returns the artifact's own stored
    media_type, never a JSON envelope (serving/boundary_service.py's own `artifact_get`
    docstring), so a `json.loads` on the response body is wrong for the success leg. The 404
    miss-path DOES still return a JSON body (`_bad_artifact_hash`/the not-found branch precede
    the raw-bytes `Response` construction), so that leg still reads via `bs_fixtures.http_get`
    unchanged."""
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()

# Live infra, dynamic loopback port -- NEVER 8433/8420/8422 (this project's standing production
# ports): `bs_fixtures.free_port()` binds-then-closes an ephemeral port each call.


def http_get_headers(url: str, headers: dict[str, str]) -> tuple[int, object]:
    """The GET sibling of `bs_fixtures.http_post_headers` -- that helper only exists for POST;
    this witness's own identity-conduit legs need the identical shape on GET."""
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def read_journal_lines(world_dir: Path) -> list[dict]:
    path = boundary_read_journal.journal_path(world_dir)
    if not path.exists():
        return []
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if raw:
            lines.append(json.loads(raw))
    return lines


def main() -> int:
    failures: list[str] = []
    procs: list = []
    world_b = f"acri{RUN_SUFFIX}"
    world_c = f"acric{RUN_SUFFIX}"
    bs_fixtures.teardown(world_b)
    bs_fixtures.teardown(world_c)
    try:
        print(f"== scaffolding classic world {world_b} (chain ends {CHAIN_B[-1]}) ==")
        wb = bs_fixtures.scaffold_classic(world_b, CHAIN_B)
        world_dir = wb.parent
        author_id, svc_id = bs_fixtures.birth_via_boundary(world_b)
        # birth_via_boundary's own five accepted writes (2x principal_registered/standing +
        # one more standing declaration for the login role, plus the two registration_write
        # acts) are this world's own five pre-existing ledger rows -- the count `GET
        # /rows/current` below must echo, both in its OWN body and in the journal's row_count.
        expected_rows = int(bs_fixtures.psql_tuples(f"SELECT count(*) FROM {world_b}.ledger;"))

        cfg = bs_fixtures.write_scratch_multiplex_config(world_dir, world_b)
        proc, port = bs_fixtures.start_server(cfg)
        procs.append(proc)
        base = f"http://127.0.0.1:{port}/d/{world_b}"
        up = bs_fixtures.wait_health(base)
        if not up:
            tail = bs_fixtures.stop_server(proc)
            raise RuntimeError(f"server never became healthy: {tail[-2000:]}")

        # -----------------------------------------------------------------------------------
        # LEG 1: identity resolution is performed on every GET, and NEVER refused for
        # anonymity -- the three channels' response bodies for the SAME read are
        # byte-identical (spec §1a: "an anonymous read simply resolves to the world's open
        # scope ... byte-identical behavior").
        # -----------------------------------------------------------------------------------
        print("=== leg1-anonymous-vendor-minted-byte-identical ===")
        st_anon, body_anon = bs_fixtures.http_get(f"{base}/rows/current")
        vendor_agent = "acri-vendor-agent"
        vendor_headers = {
            "X-Autoharn-Vendor-Session": "acri-vendor-session",
            "X-Autoharn-Vendor-Agent": vendor_agent,
            "X-Autoharn-Vendor-Ts": str(int(time.time())),
            "X-Autoharn-Vendor-Hmac": os.urandom(32).hex(),
        }
        st_vendor, body_vendor = http_get_headers(f"{base}/rows/current", vendor_headers)
        st_minted, body_minted = http_get_headers(
            f"{base}/rows/current", {"X-Autoharn-Minted-Principal": str(author_id)})
        check("leg1-anonymous-vendor-minted-byte-identical",
              st_anon == 200 and st_vendor == 200 and st_minted == 200
              and body_anon == body_vendor == body_minted
              and isinstance(body_anon, list) and len(body_anon) == expected_rows,
              f"status anon={st_anon} vendor={st_vendor} minted={st_minted}; "
              f"bodies equal={body_anon == body_vendor == body_minted}; "
              f"len(body_anon)={len(body_anon) if isinstance(body_anon, list) else '?'} "
              f"expected_rows={expected_rows}",
              failures)

        # -----------------------------------------------------------------------------------
        # LEG 2: the read journal carries one line per completed GET, each attributing the
        # correct resolved identity and a bare row count -- NEVER row content.
        # -----------------------------------------------------------------------------------
        print("=== leg2-journal-per-channel-identity-and-row-count ===")
        lines = read_journal_lines(world_dir)
        rows_current_route = f"/d/{world_b}/rows/current"
        rc_lines = [l for l in lines if l.get("route") == rows_current_route]
        anon_lines = [l for l in rc_lines if l.get("identity", {}).get("channel") == "anonymous"]
        vendor_lines = [l for l in rc_lines if l.get("identity", {}).get("channel") == "vendor"]
        minted_lines = [l for l in rc_lines if l.get("identity", {}).get("channel") == "minted"]
        check("leg2-anonymous-journaled",
              bool(anon_lines) and all(l.get("row_count") == expected_rows for l in anon_lines)
              and all(l.get("deployment") == world_b for l in anon_lines),
              f"anonymous /rows/current journal lines: {anon_lines}",
              failures)
        check("leg2-vendor-stamp-journals-agent",
              bool(vendor_lines)
              and all(l.get("identity", {}).get("agent") == vendor_agent for l in vendor_lines)
              and all(l.get("row_count") == expected_rows for l in vendor_lines),
              f"vendor /rows/current journal lines: {vendor_lines}",
              failures)
        check("leg2-minted-header-journals-principal",
              bool(minted_lines)
              and all(l.get("identity", {}).get("principal") == str(author_id) for l in minted_lines)
              and all(l.get("row_count") == expected_rows for l in minted_lines),
              f"minted /rows/current journal lines: {minted_lines}",
              failures)

        # -----------------------------------------------------------------------------------
        # LEG 3: zero row content in the journal -- grep the raw file for a known statement
        # string this world's own birth acts wrote; it must never appear.
        # -----------------------------------------------------------------------------------
        print("=== leg3-journal-carries-zero-row-content ===")
        journal_raw = boundary_read_journal.journal_path(world_dir).read_text(encoding="utf-8")
        banned_snippets = [
            "author registered (fixture genesis exception)",
            f"role {world_b}_rw -> author",
            "fixture connection principal",
        ]
        found = [s for s in banned_snippets if s in journal_raw]
        check("leg3-journal-carries-zero-row-content",
              not found,
              f"journal path={boundary_read_journal.journal_path(world_dir)}; "
              f"banned row-content snippets found in journal: {found!r} (must be empty)",
              failures)

        # -----------------------------------------------------------------------------------
        # LEG 4: /meta advertises the capability additively.
        # -----------------------------------------------------------------------------------
        print("=== leg4-meta-advertises-read-identity-journal ===")
        st_meta, body_meta = bs_fixtures.http_get(f"{base}/meta")
        check("leg4-meta-advertises-read-identity-journal",
              st_meta == 200 and isinstance(body_meta, dict)
              and body_meta.get("read_identity_journal") is True,
              f"GET /meta; status={st_meta} read_identity_journal={body_meta.get('read_identity_journal') if isinstance(body_meta, dict) else '?'}",
              failures)

        # -----------------------------------------------------------------------------------
        # LEG 5: POST behavior byte-unchanged -- an ordinary accepted write still works
        # exactly as before, a minted-principal write still attributes correctly, and NEITHER
        # POST adds a journal line (the read journal is GET-only, spec §1a's own scope).
        # -----------------------------------------------------------------------------------
        print("=== leg5-post-behavior-byte-unchanged-no-journal-growth ===")
        lines_before_post = len(read_journal_lines(world_dir))
        st_post, body_post = bs_fixtures.http_post(
            f"{base}/write/ledger",
            {"kind": "decision", "statement": "ac-read-identity witness: ordinary write unchanged",
             "actor": author_id})
        st_post_minted, body_post_minted = bs_fixtures.http_post_headers(
            f"{base}/write/ledger",
            {"kind": "decision", "statement": "ac-read-identity witness: minted-attributed write"},
            {"X-Autoharn-Minted-Principal": str(author_id)})
        lines_after_post = len(read_journal_lines(world_dir))
        check("leg5-post-behavior-byte-unchanged-no-journal-growth",
              st_post == 200 and body_post.get("disposition") == "accepted"
              and st_post_minted == 200 and body_post_minted.get("disposition") == "accepted"
              and lines_after_post == lines_before_post,
              f"plain write: status={st_post} disposition={body_post.get('disposition')}; "
              f"minted write: status={st_post_minted} disposition={body_post_minted.get('disposition')}; "
              f"journal lines before={lines_before_post} after={lines_after_post} (POST must "
              f"never add a read-journal line)",
              failures)

        # -----------------------------------------------------------------------------------
        # LEG 6: performance disclosure -- see this module's own docstring, "PERFORMANCE
        # METHODOLOGY, DISCLOSED" for why this is a decomposed measurement rather than a
        # literal remove-the-feature-and-rerun A/B.
        # -----------------------------------------------------------------------------------
        print("=== leg6-performance-1000-row-walk ===")
        N = 1000
        t0 = time.monotonic()
        walk_statuses = []
        for _ in range(N):
            st, _ = bs_fixtures.http_get(f"{base}/rows/current")
            walk_statuses.append(st)
        walk_wall_s = time.monotonic() - t0
        walk_avg_ms = (walk_wall_s / N) * 1000

        t1 = time.monotonic()
        for _ in range(N):
            boundary_read_journal.append_read(
                world_dir, deployment=world_b, route=rows_current_route, view="/rows/current",
                identity={"channel": "anonymous"}, row_count=expected_rows)
        append_wall_s = time.monotonic() - t1
        append_avg_us = (append_wall_s / N) * 1_000_000

        pct_of_request = (append_avg_us / 1000) / walk_avg_ms * 100 if walk_avg_ms > 0 else float("inf")
        print(f"  1000-request live walk: total={walk_wall_s:.3f}s avg={walk_avg_ms:.3f}ms/request")
        print(f"  1000-call isolated append_read: total={append_wall_s:.3f}s avg={append_avg_us:.1f}us/call")
        print(f"  append_read cost as a fraction of one request's own wall time: {pct_of_request:.2f}%")
        check("leg6-performance-1000-row-walk",
              all(s == 200 for s in walk_statuses) and pct_of_request < 5.0,
              f"1000/1000 requests status 200: {all(s == 200 for s in walk_statuses)}; "
              f"walk avg={walk_avg_ms:.3f}ms/request; append_read avg={append_avg_us:.1f}us/call "
              f"({pct_of_request:.2f}% of one request's own wall time -- <5% threshold, i.e. "
              f"not a measurable slowdown on this hot path)",
              failures)

        bs_fixtures.stop_server(proc)
        procs.remove(proc)

        # -----------------------------------------------------------------------------------
        # LEG 7: fix-round ac-read-identity (review row 744, this fix's own leg) -- the raw
        # artifact CONTENT route (`GET /artifacts/{hash}`) now binds `bind_read_row_count`
        # exactly at the point the handler holds `row`, mirroring its `.../stat` sibling
        # (serving/boundary_service.py's `artifact_get`). A SEPARATE, s51-capable world
        # (world_c, `llrpab_fixtures.CHAIN_S57`) since world_b's own CHAIN_B stops at s43 and
        # would only ever exercise the capability_absent path, never the served-content path
        # this fix actually touches -- scaffolded and born via `llrpab_fixtures`' own proven
        # mechanism (see this file's own ARTIFACT_SIBLING comment above for why, not
        # `bs_fixtures.scaffold_classic`/`birth_via_boundary`, which are shaped for CHAIN_B's
        # s43 head and do not carry forward onto s44+'s tightened constraints).
        # -----------------------------------------------------------------------------------
        print(f"== scaffolding world {world_c} via llrpab_fixtures "
              f"(chain ends {llrpab_fixtures.CHAIN_S57[-1]}) ==")
        llrpab_fixtures.apply_chain(world_c)
        author_id_c_str, _reviewer_id_c = llrpab_fixtures.birth(world_c)
        author_id_c = int(author_id_c_str)
        tmpdir_c = Path(tempfile.mkdtemp(prefix=f"{world_c}-seenred-"))
        world_dir_c = tmpdir_c
        cfg_c = llrpab_fixtures.write_multiplex_config(tmpdir_c, world_c)
        proc_c, port_c = llrpab_fixtures.start_server(cfg_c)
        procs.append(proc_c)
        base_c = f"http://127.0.0.1:{port_c}/d/{world_c}"
        up_c = llrpab_fixtures.wait_health(f"http://127.0.0.1:{port_c}/d/{world_c}/health")
        if not up_c:
            tail = llrpab_fixtures.stop_server(proc_c)
            raise RuntimeError(f"world_c server never became healthy: {tail[-2000:]}")

        content = b"ac-read-identity leg7 fixture artifact content, review row 744.\n"
        content_hash = hashlib.sha256(content).hexdigest()
        st_put, body_put = bs_fixtures.http_post(f"{base_c}/artifacts", {
            "bytes": base64.b64encode(content).decode("ascii"),
            "media_type": "text/plain", "hash": content_hash, "actor": author_id_c})
        check("leg7-artifact-put-accepted",
              st_put == 200 and isinstance(body_put, dict)
              and body_put.get("disposition") == "accepted",
              f"status={st_put} body={body_put}", failures)

        content_route = f"/d/{world_c}/artifacts/{content_hash}"
        st_get, raw_get = http_get_bytes(f"{base_c}/artifacts/{content_hash}")
        check("leg7-served-content-byte-identical",
              st_get == 200 and raw_get == content,
              f"status={st_get} bytes-match={raw_get == content}", failures)

        lines_c = read_journal_lines(world_dir_c)
        content_lines = [l for l in lines_c if l.get("route") == content_route]
        check("leg7-served-content-journals-row-count-1",
              bool(content_lines) and all(l.get("row_count") == 1 for l in content_lines),
              f"journal lines for {content_route!r}: {content_lines}",
              failures)

        # Miss path: an unregistered hash 404s BEFORE the handler ever holds a real `row` --
        # exactly the same shape `artifact_stat`'s own 404 branch already had pre-fix (that
        # branch returns before ever calling `_json_read_response`), so the journal line this
        # produces carries `row_count: null`, unchanged by this fix -- the "correct value on
        # the miss path" the fix brief asks this leg to witness is precisely THIS null, not a
        # 0 (0 would falsely claim the handler sized an empty-but-real response).
        fake_hash = "0" * 64
        st_404, body_404 = bs_fixtures.http_get(f"{base_c}/artifacts/{fake_hash}")
        check("leg7-unregistered-hash-404",
              st_404 == 404, f"status={st_404} body={body_404}", failures)
        fake_route = f"/d/{world_c}/artifacts/{fake_hash}"
        lines_c2 = read_journal_lines(world_dir_c)
        miss_lines = [l for l in lines_c2 if l.get("route") == fake_route]
        check("leg7-miss-path-journals-row-count-null",
              bool(miss_lines) and all(l.get("row_count") is None for l in miss_lines),
              f"journal lines for {fake_route!r}: {miss_lines}",
              failures)

        llrpab_fixtures.stop_server(proc_c)
        procs.remove(proc_c)

    finally:
        for p in procs:
            try:
                bs_fixtures.stop_server(p)
            except Exception:
                pass
        bs_fixtures.teardown(world_b)
        llrpab_fixtures.teardown(world_c)

    print(f"\n{'ALL PASS' if not failures else f'{len(failures)} FAILURE(S): ' + ', '.join(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
