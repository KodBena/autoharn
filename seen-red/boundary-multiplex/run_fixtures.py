#!/usr/bin/env python3
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
                socket never binds (no world needed at all). WM-INFLIGHT-DEFAULT (no DB either --
                a startup-banner read, design/BRIEF-A1-INFLIGHT-CAP-AND-WOULD-PRODUCE-2026-08-04.md
                item 1/5, RE-CHECKED by design/BRIEF-GLOBAL-INFLIGHT-CAP-2026-08-06.md item 3/5,
                ledger rows 1113/1115): the shipped MAX_INFLIGHT_PER_DEPLOYMENT default (32) and
                the shipped MAX_INFLIGHT_KERNEL_CALLS default (64, raised from 24), both named in
                the startup banner, with the starvation-tradeoff NOTE now correctly QUIET at
                these defaults (32 < 64 -- the relation the global-cap raise restores). WM-
                INFLIGHT-FIRES (no DB either) is the note's OTHER polarity: an explicit
                `max_inflight_kernel_calls` override low enough that the (still-default)
                per-deployment bound reaches or exceeds it, so the NOTE correctly FIRES. WM4's
                own config explicitly OVERRIDES `max_inflight_per_deployment` to 12 (the value the
                retired `max(4, 24 // 2)` formula used to produce for two deployments) so its
                burst can still observe `deployment_saturated` -- the shipped defaults alone
                (32 < 64) can never trigger that label via the per-deployment/global relation
                alone, see WM-INFLIGHT-DEFAULT's own leading comment.

Usage: python3 seen-red/boundary-multiplex/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import anyio
import asyncio
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
import boundary_service  # noqa: E402  (unused directly here as of design/BRIEF-A1-INFLIGHT-CAP-AND-WOULD-PRODUCE-2026-08-04.md item 1 retiring compute_per_deployment_limit -- kept imported for its own filing/ sys.path side effect, matching deployment_record's own comment above)
import boundary_multiplex_config  # noqa: E402

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

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


def write_multiplex_toml(tmpdir: Path, entries: dict[str, dict[str, str]],
                          max_inflight_per_deployment: int | None = None,
                          max_inflight_kernel_calls: int | None = None) -> Path:
    """`entries`: deployment name -> {pghost, pgdatabase, pguser, pgschema, pgkern}. Hand-writes
    TOML text (no library needed for WRITING -- `tomllib` is read-only stdlib) in the exact
    shape `serving/boundary_multiplex_config.py` validates. `max_inflight_per_deployment`
    (design/BRIEF-A1-INFLIGHT-CAP-AND-WOULD-PRODUCE-2026-08-04.md item 1): an optional top-level
    override for the hub-wide per-deployment inflight sub-bound -- omitted entirely leaves the
    shipped default (32) in force, matching every other optional-key convention in this file's
    sibling `boundary_multiplex_config.py`. `max_inflight_kernel_calls` (design/
    BRIEF-GLOBAL-INFLIGHT-CAP-2026-08-06.md item 1, ledger rows 1113/1115): its sibling override
    for the hub-wide GLOBAL inflight bound -- omitted entirely leaves the shipped default (64) in
    force."""
    lines: list[str] = []
    if max_inflight_per_deployment is not None:
        lines.append(f"max_inflight_per_deployment = {max_inflight_per_deployment}")
        lines.append("")
    if max_inflight_kernel_calls is not None:
        lines.append(f"max_inflight_kernel_calls = {max_inflight_kernel_calls}")
        lines.append("")
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

        # ==== WM-INFLIGHT-DEFAULT: default MAX_INFLIGHT_PER_DEPLOYMENT=32/MAX_INFLIGHT_KERNEL_
        #      CALLS=64, printed, starvation note QUIET ====
        # design/BRIEF-A1-INFLIGHT-CAP-AND-WOULD-PRODUCE-2026-08-04.md item 1/5, RE-CHECKED by
        # design/BRIEF-GLOBAL-INFLIGHT-CAP-2026-08-06.md item 3/5 (ledger rows 1113/1115): the
        # shipped defaults' OWN visibility -- no DB needed (startup only validates config SHAPE,
        # never probes deployment health), so an UNROUTABLE_HOST single-deployment config is
        # enough to reach the startup banner cheaply. Also witnesses the honest starvation-
        # tradeoff NOTE's (serving/boundary_service.py's `inflight_per_deployment_starvation_
        # note`) FIRST polarity: at shipped defaults the per-deployment bound (32) is now BELOW
        # the raised global MAX_INFLIGHT_KERNEL_CALLS (64), so the sub-bound-under-global relation
        # holds and the NOTE must be ABSENT -- the exact regression the global-cap raise fixes
        # (before this item, 32 >= 24 fired the note at every shipped-default deployment).
        print("== WM-INFLIGHT-DEFAULT: shipped defaults (32/64) named, starvation note quiet ==")
        world_default_probe = f"muxdefault{RUN_SUFFIX}"
        tmp_cfg_default = Path(tempfile.mkdtemp(prefix="mux-inflight-default-cfg-"))
        tmps.append(tmp_cfg_default)
        config_path_default = write_multiplex_toml(tmp_cfg_default, {
            world_default_probe: {
                "pghost": UNROUTABLE_HOST, "pgdatabase": "toy",
                "pguser": f"{world_default_probe}_rw", "pgschema": world_default_probe,
                "pgkern": f"{world_default_probe}_kernel",
            },
        })
        proc_default, port_default = start_multiplex_server(config_path_default)
        asgi_up_default = False
        deadline_default = time.time() + 10
        while time.time() < deadline_default:
            try:
                with socket.create_connection(("127.0.0.1", port_default), timeout=1):
                    asgi_up_default = True
                    break
            except OSError:
                time.sleep(0.2)
        out_default = bs_fixtures.stop_server(proc_default)
        check("wm-inflight-default-banner-names-32-and-64-no-starvation-note",
              asgi_up_default and "MAX_INFLIGHT_PER_DEPLOYMENT=32" in out_default
              and "MAX_INFLIGHT_KERNEL_CALLS=64" in out_default
              and "max_inflight_per_deployment" in out_default
              and "max_inflight_kernel_calls" in out_default
              and "NOTE -- MAX_INFLIGHT_PER_DEPLOYMENT" not in out_default,
              f"asgi_up={asgi_up_default}; startup output tail={out_default[-1200:]!r}",
              failures)
        # Orchestrator ruling on ledger row 1141's flag (ledgered row 1147/1148): the ASGI
        # threadpool's own anyio CapacityLimiter is now derived STRUCTURALLY as
        # MAX_INFLIGHT_KERNEL_CALLS + NON_KERNEL_THREADPOOL_HEADROOM (16) -- at the shipped
        # default, 64 + 16 = 80, named in both the stderr banner and the diagnostic STARTUP
        # event's own `threadpool_capacity`/`non_kernel_threadpool_headroom` fields.
        check("wm-inflight-default-banner-names-threadpool-capacity-80",
              "THREADPOOL_CAPACITY=80" in out_default
              and '"threadpool_capacity": 80' in out_default
              and '"non_kernel_threadpool_headroom": 16' in out_default,
              f"startup output tail={out_default[-1200:]!r}", failures)

        # ==== WM-INFLIGHT-FIRES: an explicit config where per-deployment >= global, note FIRES ==
        # design/BRIEF-GLOBAL-INFLIGHT-CAP-2026-08-06.md item 3/5's SECOND polarity: the relation
        # is checked against the RESOLVED values of BOTH keys, not a literal -- so lowering
        # `max_inflight_kernel_calls` below the (still-default) per-deployment bound must still
        # correctly FIRE the note, exactly as raising the per-deployment bound above a fixed
        # global would have. No DB needed, same UNROUTABLE_HOST lever as WM-INFLIGHT-DEFAULT.
        print("== WM-INFLIGHT-FIRES: max_inflight_kernel_calls=16 < default per-deployment (32) ==")
        world_fires_probe = f"muxfires{RUN_SUFFIX}"
        tmp_cfg_fires = Path(tempfile.mkdtemp(prefix="mux-inflight-fires-cfg-"))
        tmps.append(tmp_cfg_fires)
        config_path_fires = write_multiplex_toml(tmp_cfg_fires, {
            world_fires_probe: {
                "pghost": UNROUTABLE_HOST, "pgdatabase": "toy",
                "pguser": f"{world_fires_probe}_rw", "pgschema": world_fires_probe,
                "pgkern": f"{world_fires_probe}_kernel",
            },
        }, max_inflight_kernel_calls=16)
        proc_fires, port_fires = start_multiplex_server(config_path_fires)
        asgi_up_fires = False
        deadline_fires = time.time() + 10
        while time.time() < deadline_fires:
            try:
                with socket.create_connection(("127.0.0.1", port_fires), timeout=1):
                    asgi_up_fires = True
                    break
            except OSError:
                time.sleep(0.2)
        out_fires = bs_fixtures.stop_server(proc_fires)
        check("wm-inflight-fires-banner-names-configured-16-and-starvation-note-fires",
              asgi_up_fires and "MAX_INFLIGHT_KERNEL_CALLS=16" in out_fires
              and "MAX_INFLIGHT_PER_DEPLOYMENT=32" in out_fires
              and "NOTE -- MAX_INFLIGHT_PER_DEPLOYMENT=32 is >= the global "
                  "MAX_INFLIGHT_KERNEL_CALLS=16" in out_fires,
              f"asgi_up={asgi_up_fires}; startup output tail={out_fires[-1200:]!r}",
              failures)
        # SECOND polarity of the structural threadpool derivation: 16 + 16 = 32, distinct from
        # the default leg's 80 above -- proving the printed/logged value tracks the CONFIGURED
        # global bound, not a literal.
        check("wm-inflight-fires-banner-names-threadpool-capacity-32",
              "THREADPOOL_CAPACITY=32" in out_fires
              and '"threadpool_capacity": 32' in out_fires,
              f"startup output tail={out_fires[-1200:]!r}", failures)

        # ==== WM-THREADPOOL-STRUCTURAL: the anyio CapacityLimiter is ACTUALLY resized, live ====
        # Orchestrator ruling on ledger row 1141's flag (ledgered row 1147/1148): the banner/log
        # checks above prove the SERVICE PRINTS the right derived value; this leg proves the
        # value is really APPLIED to anyio's own default thread CapacityLimiter -- in-process,
        # not via subprocess stdout, since the limiter is bound to the running event loop and
        # has no HTTP-visible surface. Runs `create_app`'s own `lifespan` context manager
        # directly (the SAME code path uvicorn/Starlette drive before ever accepting a request)
        # at two distinct MAX_INFLIGHT_KERNEL_CALLS values, both polarities.
        print("== WM-THREADPOOL-STRUCTURAL: anyio CapacityLimiter actually resized at ASGI startup ==")

        async def _threadpool_capacity_after_lifespan(kernel_calls: int) -> int:
            boundary_service.configure_max_inflight_kernel_calls(kernel_calls)
            probe_cfg = boundary_service.BoundaryConfig(
                deployment_record.DeploymentRecord(
                    db="toy", host="unused", schema="s", kern="k", role="r", name="probe"))
            probe_app = boundary_service.create_app({"probe": probe_cfg})
            async with probe_app.router.lifespan_context(probe_app):
                return anyio.to_thread.current_default_thread_limiter().total_tokens

        applied_64 = asyncio.run(_threadpool_capacity_after_lifespan(64))
        applied_10 = asyncio.run(_threadpool_capacity_after_lifespan(10))
        check("wm-threadpool-structural-applied-both-polarities",
              applied_64 == 64 + boundary_service.NON_KERNEL_THREADPOOL_HEADROOM
              and applied_10 == 10 + boundary_service.NON_KERNEL_THREADPOOL_HEADROOM
              and applied_64 != applied_10,
              f"applied at MAX_INFLIGHT_KERNEL_CALLS=64: {applied_64} (expected "
              f"{64 + boundary_service.NON_KERNEL_THREADPOOL_HEADROOM}); at 10: {applied_10} "
              f"(expected {10 + boundary_service.NON_KERNEL_THREADPOOL_HEADROOM})",
              failures)
        # Restore the module global to the shipped default so no LATER leg in this same process
        # (none currently reads it in-process, but the module-level global otherwise leaks
        # sideways to whatever runs next) is silently affected by this leg's own probing.
        boundary_service.configure_max_inflight_kernel_calls(
            boundary_multiplex_config.DEFAULT_MAX_INFLIGHT_KERNEL_CALLS)

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
        # MAX_INFLIGHT_KERNEL_CALLS bound ever being touched. design/
        # BRIEF-A1-INFLIGHT-CAP-AND-WOULD-PRODUCE-2026-08-04.md item 1 retired the
        # `max(4, MAX_INFLIGHT_KERNEL_CALLS // len(deployments))` formula this leg used to derive
        # its expectation from -- and design/BRIEF-GLOBAL-INFLIGHT-CAP-2026-08-06.md item 1
        # (ledger rows 1113/1115) raised the global default from 24 to 64, so the shipped
        # per-deployment DEFAULT (32) is now BELOW the shipped global default too (see
        # WM-INFLIGHT-DEFAULT above); either way, an explicit `max_inflight_per_deployment`
        # override is what this leg needs to still observe `deployment_saturated` (a burst against
        # a per-deployment bound that sits above -- or, as now, comfortably below -- the global
        # one would never isolate the per-deployment label from the global one on its own; an
        # explicit LOW override is the reliable lever regardless of where the global default
        # happens to sit). This config explicitly OVERRIDES `max_inflight_per_deployment` to 12
        # (the SAME value the old retired formula produced for n=2, `max(4, 24 // 2)`) so this leg
        # still witnesses the SECOND polarity item 5 asks for: a configured value, distinct from
        # the default, visibly enforced by the refusal.
        world_stalled = f"muxstall{RUN_SUFFIX}"
        tmp_cfg4 = Path(tempfile.mkdtemp(prefix="mux-wm4-cfg-"))
        tmps.append(tmp_cfg4)
        expected_per_dep_limit = 12
        config_path4 = write_multiplex_toml(tmp_cfg4, {
            world_a: entry_for_world(world_a),
            world_stalled: {
                "pghost": UNROUTABLE_HOST, "pgdatabase": "toy",
                "pguser": f"{world_stalled}_rw", "pgschema": world_stalled,
                "pgkern": f"{world_stalled}_kernel",
            },
        }, max_inflight_per_deployment=expected_per_dep_limit)
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

        BURST_N = 64  # well over expected_per_dep_limit (12); MATCHES boundary_multiplex_config.DEFAULT_MAX_INFLIGHT_KERNEL_CALLS (design/BRIEF-GLOBAL-INFLIGHT-CAP-2026-08-06.md item 1, raised from 24 -- this fixture's config carries no max_inflight_kernel_calls override, so the shipped default is what's live) -- chosen so this burst alone could ALSO have saturated the global gate if the per-deployment gate did not fire first; the check below proves it is refused under the DEPLOYMENT label, not the server one
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

        # design/BRIEF-A1-INFLIGHT-CAP-AND-WOULD-PRODUCE-2026-08-04.md item 5, second polarity:
        # the CONFIGURED value (12, distinct from the shipped default 32 -- WM-INFLIGHT-DEFAULT
        # above already covers the default) named in the startup banner, and the starvation NOTE
        # correctly ABSENT (12 < the global MAX_INFLIGHT_KERNEL_CALLS=64 -- this config carries no
        # override for the global key, so the shipped default is what's live -- the
        # sibling-isolation protection genuinely holds at this configuration -- exactly this
        # burst's own proof).
        # `stop_server` here ends proc4 early (the burst is already done); the `finally` block's
        # own `stop_server(proc4)` call below is still safe against an already-exited process.
        out4 = bs_fixtures.stop_server(proc4)
        check("wm4-banner-names-configured-12-no-starvation-note",
              "MAX_INFLIGHT_PER_DEPLOYMENT=12" in out4
              and "NOTE -- MAX_INFLIGHT_PER_DEPLOYMENT" not in out4,
              f"startup output tail={out4[-1200:]!r}", failures)

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
