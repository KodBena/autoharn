#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T16:01:50Z
#   last-change: 2026-07-18T16:03:13Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity witness for design/
FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md's §7 witness sketch (WM1-WM4; WM5/WM6 are the
CLI-rebase §5 witnesses and are UNEXERCISED here -- the §5 CLI rebase is a separate, not-yet-
built seam, named rather than faked, see this repo's build report). Real infra, no mocks:
CLASSIC scaffolds via `bootstrap/new-project.sh` + the s43 birth chain, plus a REAL
`serving.boundary_service` uvicorn subprocess bound to loopback, driven with `--config` against
a real `boundary-multiplex.toml`.

REUSE, NOT RE-DERIVATION (ADR-0012 P1): every scaffolding helper below
(`scaffold_classic`/`birth_via_boundary`/`teardown`/`free_port`/`stop_server`/`http_get`/
`http_post`/`sh`/`check`) is IMPORTED from the sibling `seen-red/boundary-service/run_fixtures.py`
module, not re-typed -- this file adds ONLY what multiplexing needs: a TOML config writer, a
`/d/{deployment}`-prefixed `wait_health`, and the four witnesses themselves.

WORLDS:
  WORLD MUX-A, WORLD MUX-B -- both full s43-birthed (CHAIN_B), served by ONE service process
                from ONE two-deployment TOML config: WM1 (cross-contamination probe, both
                directions), WM2 (unknown-deployment typed 404), WM4 (per-deployment admission
                bound -- MUX-A stays live and prompt while MUX-B's OWN sub-bound is driven to
                saturation via an unroutable-host lever on a THIRD, deliberately-unreachable
                deployment in the SAME config, so MUX-A/MUX-B's own kernels are never touched by
                the burst).
  (no DB)     -- WM3, three legs: unknown top-level key, missing required key, zero
                deployments -- each a construction-time startup refusal naming the defect; the
                socket never binds (no world needed at all).

Usage: python3 seen-red/boundary-multiplex/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import socket
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
PYVENV = Path.home() / "w" / "vdc" / "venvs" / "generic" / "bin" / "python"

sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "serving"))
import deployment_record  # noqa: E402  (unused directly here, but boundary_service's own import chain expects filing/ on sys.path first)
import boundary_service  # noqa: E402  (MAX_INFLIGHT_KERNEL_CALLS, compute_per_deployment_limit, PSQL_CONNECT_TIMEOUT_S -- reused constants, never a second literal)
import boundary_multiplex_config  # noqa: E402

# The sibling module is loaded by FILE PATH (not `seen-red.boundary-service.run_fixtures` --
# `seen-red`/`boundary-service` are not valid Python package names, hyphens included) under its
# own distinct module name, so importing it here never collides with this file's own identity
# even though both are literally named run_fixtures.py on disk.
_spec = importlib.util.spec_from_file_location("boundary_service_fixtures", SIBLING)
assert _spec is not None and _spec.loader is not None
bs_fixtures = importlib.util.module_from_spec(_spec)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_spec.loader.exec_module(bs_fixtures)

RUN_SUFFIX = bs_fixtures.RUN_SUFFIX
CHAIN_B = bs_fixtures.CHAIN_B
UNROUTABLE_HOST = bs_fixtures.UNROUTABLE_HOST


def write_multiplex_toml(tmpdir: Path, entries: dict[str, dict[str, str]]) -> Path:
    """`entries`: deployment name -> {pghost, pgdatabase, pguser, pgschema, pgkern}. Hand-writes
    TOML text (no library needed for WRITING -- `tomllib` is read-only stdlib) in the exact
    shape `serving/boundary_multiplex_config.py` validates."""
    lines: list[str] = []
    for name, fields in entries.items():
        lines.append(f"[deployments.{name}]")
        for k in ("pghost", "pgdatabase", "pguser", "pgschema", "pgkern"):
            lines.append(f'{k} = "{fields[k]}"')
        lines.append("")
    path = tmpdir / "boundary-multiplex.toml"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def entry_for_world(world: str) -> dict[str, str]:
    return {
        "pghost": bs_fixtures.PGHOST, "pgdatabase": bs_fixtures.PGDB,
        "pguser": f"{world}_rw", "pgschema": world, "pgkern": f"{world}_kernel",
    }


def start_multiplex_server(config_path: Path, host: str = "127.0.0.1", port: int | None = None):
    if port is None:
        port = bs_fixtures.free_port()
    args = [str(PYVENV), "-m", "serving.boundary_service",
            "--config", str(config_path), "--host", host, "--port", str(port)]
    proc = subprocess.Popen(args, cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, env=dict(os.environ))
    return proc, port


def wait_health_d(base_url: str, deployment: str, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/d/{deployment}/health", timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(0.3)
    return False


def main() -> int:
    failures: list[str] = []
    check = bs_fixtures.check
    tmps: list[Path] = []
    procs: list = []

    world_a = f"muxa{RUN_SUFFIX}"
    world_b = f"muxb{RUN_SUFFIX}"
    for w in (world_a, world_b):
        bs_fixtures.teardown(w)

    try:
        # ==================== WM3: config defects (no DB, no server world needed) ====================
        print("== WM3: startup refusal on a malformed multiplex config ==")
        tmp3 = Path(tempfile.mkdtemp(prefix="mux-wm3-"))
        tmps.append(tmp3)

        bad_top = tmp3 / "bad-top.toml"
        bad_top.write_text('unexpected_top = 1\n[deployments.a]\npghost="h"\npgdatabase="d"\n'
                            'pguser="u"\npgschema="s"\npgkern="k"\n', encoding="utf-8")
        bad_missing = tmp3 / "bad-missing.toml"
        bad_missing.write_text('[deployments.a]\npghost="h"\npgdatabase="d"\npguser="u"\n'
                                'pgschema="s"\n', encoding="utf-8")
        bad_zero = tmp3 / "bad-zero.toml"
        bad_zero.write_text('[deployments]\n', encoding="utf-8")

        for label, bad_path, needle in [
            ("unknown-top-level-key", bad_top, "unknown top-level key"),
            ("missing-required-key", bad_missing, "missing required key"),
            ("zero-deployments", bad_zero, "ZERO deployments"),
        ]:
            port_wm3 = bs_fixtures.free_port()
            proc_wm3, _ = start_multiplex_server(bad_path, port=port_wm3)
            # A construction-time config refusal exits on its OWN, fast, well before uvicorn
            # ever runs (no DB round trip, no network I/O) -- wait for the NATURAL exit rather
            # than terminate()ing immediately (a race that would kill the process mid-startup,
            # before it ever reaches the refusal code, and manufacture a false SIGTERM exit
            # code that looks like a refusal but proves nothing about it).
            try:
                out_wm3, _ = proc_wm3.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                proc_wm3.kill()
                out_wm3, _ = proc_wm3.communicate(timeout=5)
            out_wm3 = out_wm3 or ""
            # The socket must never bind: a fast connect attempt against the chosen port, AFTER
            # the process has already exited on its own, must fail (ECONNREFUSED) -- proving no
            # bind ever happened, not merely "the process later exited."
            never_bound = False
            try:
                with socket.create_connection(("127.0.0.1", port_wm3), timeout=1):
                    never_bound = False
            except OSError:
                never_bound = True
            check(f"wm3-{label}-refuses-before-bind",
                  never_bound and proc_wm3.returncode == 2 and needle.lower() in out_wm3.lower(),
                  f"port refused-to-connect={never_bound}, exit={proc_wm3.returncode}, "
                  f"stderr tail={out_wm3[-400:]!r} (expected to name {needle!r})",
                  failures)

        # ==================== WM1/WM2/WM4: the two-deployment world ====================
        print(f"== scaffolding two full s43 worlds: {world_a}, {world_b} ==")
        wa = bs_fixtures.scaffold_classic(world_a, CHAIN_B)
        tmps.append(wa.parent)
        author_a, _ = bs_fixtures.birth_via_boundary(world_a)
        wb = bs_fixtures.scaffold_classic(world_b, CHAIN_B)
        tmps.append(wb.parent)
        author_b, _ = bs_fixtures.birth_via_boundary(world_b)

        tmp_cfg = Path(tempfile.mkdtemp(prefix="mux-cfg-"))
        tmps.append(tmp_cfg)
        config_path = write_multiplex_toml(tmp_cfg, {
            world_a: entry_for_world(world_a),
            world_b: entry_for_world(world_b),
        })
        proc, port = start_multiplex_server(config_path)
        procs.append(proc)
        base = f"http://127.0.0.1:{port}"

        up_a = wait_health_d(base, world_a)
        up_b = wait_health_d(base, world_b)
        check("wm1-setup-both-deployments-healthy", up_a and up_b,
              f"GET /d/{world_a}/health up={up_a}; GET /d/{world_b}/health up={up_b}",
              failures)

        # ------------------------------ WM1: cross-contamination, both directions -------------
        marker_a = f"WM1-marker-a-{RUN_SUFFIX}"
        marker_b = f"WM1-marker-b-{RUN_SUFFIX}"
        st_wa, body_wa = bs_fixtures.http_post(
            f"{base}/d/{world_a}/write/ledger",
            {"kind": "note", "statement": marker_a, "actor": author_a})
        st_wb, body_wb = bs_fixtures.http_post(
            f"{base}/d/{world_b}/write/ledger",
            {"kind": "note", "statement": marker_b, "actor": author_b})
        check("wm1-both-writes-accepted",
              st_wa == 200 and body_wa.get("disposition") == "accepted"
              and st_wb == 200 and body_wb.get("disposition") == "accepted",
              f"write to {world_a}: status={st_wa} {body_wa}; write to {world_b}: "
              f"status={st_wb} {body_wb}", failures)

        st_ra, rows_a = bs_fixtures.http_get(f"{base}/d/{world_a}/rows/current?limit=1000")
        st_rb, rows_b = bs_fixtures.http_get(f"{base}/d/{world_b}/rows/current?limit=1000")
        a_has_marker_a = any(r.get("statement") == marker_a for r in rows_a) if isinstance(rows_a, list) else False
        a_has_marker_b = any(r.get("statement") == marker_b for r in rows_a) if isinstance(rows_a, list) else False
        b_has_marker_b = any(r.get("statement") == marker_b for r in rows_b) if isinstance(rows_b, list) else False
        b_has_marker_a = any(r.get("statement") == marker_a for r in rows_b) if isinstance(rows_b, list) else False
        check("wm1-cross-contamination-direction-a-to-b",
              a_has_marker_a and not b_has_marker_a,
              f"marker written to {world_a} present in {world_a}'s ledger: {a_has_marker_a}; "
              f"present in {world_b}'s ledger (must be False): {b_has_marker_a}", failures)
        check("wm1-cross-contamination-direction-b-to-a",
              b_has_marker_b and not a_has_marker_b,
              f"marker written to {world_b} present in {world_b}'s ledger: {b_has_marker_b}; "
              f"present in {world_a}'s ledger (must be False): {a_has_marker_b}", failures)

        # ------------------------------ WM2: unknown deployment, typed 404 --------------------
        st_unk, body_unk = bs_fixtures.http_get(f"{base}/d/does-not-exist-{RUN_SUFFIX}/health")
        known = sorted([world_a, world_b])
        check("wm2-unknown-deployment-typed-404",
              st_unk == 404 and isinstance(body_unk, dict)
              and body_unk.get("disposition") == "unknown_deployment"
              and sorted(body_unk.get("known", [])) == known,
              f"status={st_unk} body={body_unk} (expected known={known})", failures)

        # ------------------------------ WM4: per-deployment admission bound -------------------
        # A third deployment in a SEPARATE config, pointed at UNROUTABLE_HOST (the same lever
        # seen-red/boundary-service/run_fixtures.py's own W14/W27 use) -- its kernel calls stall
        # for up to PSQL_CONNECT_TIMEOUT_S before ever resolving, so a burst against IT alone
        # drives ITS OWN MAX_INFLIGHT_PER_DEPLOYMENT sub-bound to saturation without the global
        # MAX_INFLIGHT_KERNEL_CALLS bound ever being touched (2 deployments -> per-deployment
        # limit = max(4, 24 // 2) = 12; a burst of 24 against the stalled deployment alone is
        # well beyond its OWN sub-bound of 12 but well under the untouched global bound of 24).
        world_stalled = f"muxstall{RUN_SUFFIX}"
        tmp_cfg4 = Path(tempfile.mkdtemp(prefix="mux-wm4-cfg-"))
        tmps.append(tmp_cfg4)
        config_path4 = write_multiplex_toml(tmp_cfg4, {
            world_a: entry_for_world(world_a),
            world_stalled: {
                "pghost": UNROUTABLE_HOST, "pgdatabase": "toy",
                "pguser": f"{world_stalled}_rw", "pgschema": world_stalled,
                "pgkern": f"{world_stalled}_kernel",
            },
        })
        n_deployments4 = 2
        expected_per_dep_limit = boundary_service.compute_per_deployment_limit(n_deployments4)
        proc4, port4 = start_multiplex_server(config_path4)
        procs.append(proc4)
        base4 = f"http://127.0.0.1:{port4}"
        up4_a = wait_health_d(base4, world_a)
        asgi_up4_stalled = False
        deadline4 = time.time() + 10
        while time.time() < deadline4:
            try:
                with socket.create_connection(("127.0.0.1", port4), timeout=1):
                    asgi_up4_stalled = True
                    break
            except OSError:
                time.sleep(0.2)
        check("wm4-setup-live-deployment-healthy-stalled-deployment-socket-up",
              up4_a and asgi_up4_stalled,
              f"GET /d/{world_a}/health up={up4_a}; ASGI socket for the stalled-deployment "
              f"config up={asgi_up4_stalled}", failures)

        BURST_N = 24  # well over expected_per_dep_limit (12), well under the untouched global bound (24 itself is exactly the global bound -- chosen so this burst alone could ALSO have saturated the global gate if the per-deployment gate did not fire first; the check below proves it is refused under the DEPLOYMENT label, not the server one)
        PROMPT_BOUND_S = 2.0
        results: list[tuple[int, int | None, dict | None, float]] = []
        results_lock = threading.Lock()

        def _burst_one(idx: int) -> None:
            t0 = time.time()
            try:
                req = urllib.request.Request(
                    f"{base4}/d/{world_stalled}/write/ledger",
                    data=json.dumps({"kind": "note", "statement": f"wm4-burst-{idx}"}).encode(),
                    headers={"Content-Type": "application/json"}, method="POST")
                try:
                    with urllib.request.urlopen(req, timeout=40) as resp:
                        status, body = resp.status, json.loads(resp.read())
                except urllib.error.HTTPError as e:
                    status, body = e.code, json.loads(e.read())
            except (urllib.error.URLError, OSError, ValueError) as e:
                status, body = None, {"client_side_error": str(e)}
            elapsed = time.time() - t0
            with results_lock:
                results.append((idx, status, body, elapsed))

        health_result: list[tuple[int | None, dict | None, float]] = []

        def _sibling_health_during_burst() -> None:
            t0 = time.time()
            try:
                status, body = bs_fixtures.http_get(f"{base4}/d/{world_a}/health")
            except (urllib.error.URLError, OSError, ValueError) as e:
                status, body = None, {"client_side_error": str(e)}
            health_result.append((status, body, time.time() - t0))

        burst_threads = [threading.Thread(target=_burst_one, args=(i,)) for i in range(BURST_N)]
        health_thread = threading.Thread(target=_sibling_health_during_burst)
        for t in burst_threads:
            t.start()
        time.sleep(0.05)
        health_thread.start()
        for t in burst_threads:
            t.join(timeout=60)
        health_thread.join(timeout=60)

        dep_saturated = [r for r in results if r[1] == 503 and isinstance(r[2], dict)
                          and r[2].get("disposition") == "deployment_saturated"]
        server_saturated_leaked = [r for r in results if r[1] == 503 and isinstance(r[2], dict)
                                    and r[2].get("disposition") == "server_saturated"]
        prompt = [r for r in dep_saturated if r[3] < PROMPT_BOUND_S]
        expected_excess = BURST_N - expected_per_dep_limit
        check("wm4-per-deployment-saturation-distinct-label-and-prompt",
              len(results) == BURST_N and len(dep_saturated) >= expected_excess
              and len(server_saturated_leaked) == 0 and len(prompt) == len(dep_saturated)
              and all(r[2].get("inflight_limit") == expected_per_dep_limit for r in dep_saturated)
              and all(r[2].get("deployment") == world_stalled for r in dep_saturated),
              f"burst_n={BURST_N} expected_per_dep_limit={expected_per_dep_limit} "
              f"deployment_saturated={len(dep_saturated)} (expected >= {expected_excess}) "
              f"server_saturated LEAKED={len(server_saturated_leaked)} (must be 0) "
              f"prompt(<{PROMPT_BOUND_S}s)={len(prompt)}/{len(dep_saturated)} "
              f"statuses={sorted({r[1] for r in results})}", failures)

        sib_status, sib_body, sib_elapsed = health_result[0] if health_result else (None, None, -1.0)
        SIBLING_MARGIN_S = 5.0  # world_a is a REAL, reachable world -- no PSQL_CONNECT_TIMEOUT_S wait involved at all; generous margin for scheduling jitter under the burst only
        check("wm4-sibling-deployment-unstarved-during-burst",
              sib_status == 200 and sib_elapsed < SIBLING_MARGIN_S,
              f"GET /d/{world_a}/health DURING the {world_stalled} burst: status={sib_status} "
              f"elapsed={sib_elapsed:.2f}s (bound {SIBLING_MARGIN_S}s) body={sib_body}",
              failures)

    finally:
        for proc in procs:
            bs_fixtures.stop_server(proc)
        for w in (world_a, world_b):
            bs_fixtures.teardown(w)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    print()
    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL WM CHECKS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
