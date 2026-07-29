#!/usr/bin/env python3
"""seen-red/boundary-sse-events/run_fixtures.py -- S1-S11 (S11 added for work item
sse-subscriber-slot-leak, ledger row 429), design/
FABLE-BOUNDARY-SSE-EVENTS-SPEC.md §3 witness plan (work item boundary-sse-events, ledger row
169). Real infra, no mocks: two CLASSIC-scaffolded worlds (WORLD_PRE shape -- s42-headed, no
s43 boundary functions needed; `GET /events` only ever touches `ledger`'s own `max(id)`, never a
write-boundary function), a real `serving.boundary_service` uvicorn subprocess bound to
loopback, `curl -N` as the streaming HTTP client (urllib cannot hold a streaming GET open and
read incrementally without extra machinery; curl is already this project's own house choice for
`led`'s own psql-adjacent shelling-out idiom, and the spec's own witness plan says "curl -N
legs" verbatim).

REUSE, NOT RE-DERIVATION (ADR-0012 P1): every scaffolding helper below (`scaffold_classic`,
`birth_pre_s43`, `teardown`, `psql_tuples`, `psql_raw`, `sh`, `check`, `free_port`,
`start_server`, `wait_health`, `http_get`, `stop_server`, `RUN_SUFFIX`, `CHAIN_PRE`, `PGHOST`,
`PGDB`) is IMPORTED from `seen-red/boundary-service/run_fixtures.py` -- the SAME pattern
`seen-red/boundary-read-surface/run_fixtures.py` already established for its own witnesses. This
file adds ONLY what the SSE spec needs: a two-deployment scratch multiplex config with a small
`max_sse_clients`/`sse_poll_interval_secs` (the spec's own words: "lower the cap via config in
scratch to witness cheaply"), a `curl -N` subscriber helper, a raw ledger-row-insert helper (no
s43 boundary needed for THIS spec -- `/events` never calls a write-boundary function, only
`max(id)`), and the ten witnesses themselves.

WORLD: two WORLD_PRE-shape worlds (s42 head, no s43) in ONE multiplex config, `world_a`/
`world_b` -- s42 is required for the (pre-existing) `chain_genesis` seed `scaffold_classic`
already does; s43 (the write boundary) is deliberately NOT needed here, since this spec's own
route never calls a boundary write function, only reads `max(id)` -- a raw INSERT (the SAME
`birth_pre_s43`-style direct write `bootstrap/new-project.sh`'s own pre-s43 scaffold path uses)
is how this fixture advances each world's own ledger head.

Usage: python3 seen-red/boundary-sse-events/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SIBLING = REPO / "seen-red" / "boundary-service" / "run_fixtures.py"

sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "serving"))
sys.path.insert(0, str(REPO / "bootstrap"))
import deployment_record  # noqa: E402  (boundary_service's own import chain expects filing/ on sys.path first)
import boundary_service  # noqa: E402  (the in-process create_app/_SseHub leak witness, S10)
import boundary_multiplex_config  # noqa: E402  (in-process config load for the leak witness)

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own environment
# before any subprocess is spawned -- inherited by the whole process tree this fixture starts.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

# The sibling module is loaded by FILE PATH (hyphenated directory names are not valid Python
# package components), under its own distinct module name -- the same trick seen-red/
# boundary-read-surface/run_fixtures.py already uses for the identical reason.
_spec = importlib.util.spec_from_file_location("boundary_service_fixtures", SIBLING)
assert _spec is not None and _spec.loader is not None
bs_fixtures = importlib.util.module_from_spec(_spec)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_spec.loader.exec_module(bs_fixtures)

RUN_SUFFIX = bs_fixtures.RUN_SUFFIX
CHAIN_PRE = bs_fixtures.CHAIN_PRE
PGHOST, PGDB = bs_fixtures.PGHOST, bs_fixtures.PGDB
check = bs_fixtures.check
sh = bs_fixtures.sh

# Scratch tunables (spec §3: "lower the cap via config in scratch to witness cheaply") -- a
# poll interval fast enough that the GREEN legs below do not need to wait long, a client cap
# small enough that S3 (saturation) is cheap to reach with only three connections.
SCRATCH_POLL_INTERVAL_S = 0.5
SCRATCH_MAX_SSE_CLIENTS = 2


def write_scratch_multiplex_config_two(tmpdir: Path, world_a: str, world_b: str) -> Path:
    """The SSE spec's own two new top-level TOML keys, alongside TWO `[deployments.*]` tables
    (S8's cross-deployment-isolation leg needs two live deployments on one hub)."""
    path = tmpdir / "sse-boundary-multiplex.toml"
    path.write_text(
        f'sse_poll_interval_secs = {SCRATCH_POLL_INTERVAL_S}\n'
        f'max_sse_clients = {SCRATCH_MAX_SSE_CLIENTS}\n'
        f'[deployments.{world_a}]\n'
        f'pghost = "{PGHOST}"\npgdatabase = "{PGDB}"\npguser = "{world_a}_rw"\n'
        f'pgschema = "{world_a}"\npgkern = "{world_a}_kernel"\n'
        f'[deployments.{world_b}]\n'
        f'pghost = "{PGHOST}"\npgdatabase = "{PGDB}"\npguser = "{world_b}_rw"\n'
        f'pgschema = "{world_b}"\npgkern = "{world_b}_kernel"\n',
        encoding="utf-8")
    return path


def current_head(world: str) -> int:
    return int(bs_fixtures.psql_tuples(f"SELECT coalesce(max(id), 0) FROM {world}.ledger;"))


def insert_decision_row(world: str, statement: str) -> int:
    """Advances `world`'s own ledger head by one row -- a plain `kind='decision'` raw INSERT (no
    s43 boundary function needed; this spec's own `/events` route never calls one, only
    `max(id)`), the SAME direct-write shape `birth_pre_s43` already uses for this world's own
    genesis rows. Returns the new head (the inserted row's own id)."""
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    author = int(bs_fixtures.psql_tuples(f"SELECT id FROM {K}.principal WHERE name='author';"))
    safe_stmt = statement.replace("'", "''")
    r = bs_fixtures.psql_raw(
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"INSERT INTO ledger (kind, statement, actor) VALUES ('decision', '{safe_stmt}', {author});\n"
    )
    if r.returncode != 0:
        raise RuntimeError(f"insert_decision_row FAILED ({world}): {r.stderr[-600:]}")
    return current_head(world)


def curl_subscribe(url: str, headers: dict[str, str] | None = None, max_time: float = 40.0
                    ) -> tuple[subprocess.Popen, Path]:
    """A background `curl -N` subscriber -- output redirected to a real scratch FILE (never an
    anonymous pipe; the SAME reasoning `_spawn_boundary_service`'s own docstring in the sibling
    fixture gives: a long-lived stream's cumulative output can exceed a pipe's fixed OS buffer
    and deadlock). `--max-time` bounds the connection's own maximum lifetime so a leaked
    subscriber this fixture forgets to stop_curl() still exits on its own eventually."""
    fd, log_path_str = tempfile.mkstemp(prefix="sse-curl-", suffix=".log")
    log_path = Path(log_path_str)
    logf = os.fdopen(fd, "w")
    args = ["curl", "-N", "-s", "--max-time", str(max_time)]
    for k, v in (headers or {}).items():
        args += ["-H", f"{k}: {v}"]
    args.append(url)
    try:
        proc = subprocess.Popen(args, stdout=logf, stderr=subprocess.STDOUT)
    finally:
        logf.close()
    return proc, log_path


def stop_curl(proc: subprocess.Popen, log_path: Path) -> str:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    try:
        return log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    finally:
        try:
            log_path.unlink()
        except OSError:
            pass


def curl_status(url: str, headers: dict[str, str] | None = None, max_time: float = 5.0) -> str:
    """A ONE-SHOT curl that reports only the HTTP status code (used for legs that never open a
    long-lived stream: the 404/422/503 refusal legs, each of which answers immediately, before
    any SSE body is ever written)."""
    args = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", str(max_time)]
    for k, v in (headers or {}).items():
        args += ["-H", f"{k}: {v}"]
    args.append(url)
    cp = sh(args)
    return cp.stdout.strip()


def curl_body_and_status(url: str, headers: dict[str, str] | None = None, max_time: float = 5.0
                          ) -> tuple[str, str]:
    args = ["curl", "-s", "-w", "\n---STATUS---%{http_code}", "--max-time", str(max_time)]
    for k, v in (headers or {}).items():
        args += ["-H", f"{k}: {v}"]
    args.append(url)
    cp = sh(args)
    if "---STATUS---" in cp.stdout:
        body, status = cp.stdout.rsplit("---STATUS---", 1)
        return body, status.strip()
    return cp.stdout, ""


def wait_for_head_event(log_path: Path, min_head: int, timeout: float) -> int | None:
    """Polls `log_path`'s own accumulated content for an `event: head` line whose `head_id` is
    >= `min_head`. Returns that head_id, or None on timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            text = log_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        lines = text.splitlines()
        for i, ln in enumerate(lines):
            if ln.strip() == "event: head" and i + 1 < len(lines) and lines[i + 1].startswith("data: "):
                try:
                    payload = json.loads(lines[i + 1][len("data: "):])
                except ValueError:
                    continue
                hid = payload.get("head_id")
                if isinstance(hid, int) and hid >= min_head:
                    return hid
        time.sleep(0.2)
    return None


def main() -> int:
    failures: list[str] = []
    world_a = f"ssefxa{RUN_SUFFIX}"
    world_b = f"ssefxb{RUN_SUFFIX}"
    for w in (world_a, world_b):
        bs_fixtures.teardown(w)
    tmp = Path(tempfile.mkdtemp(prefix="sse-fixtures-"))
    procs: list[subprocess.Popen] = []
    try:
        bs_fixtures.scaffold_classic(world_a, CHAIN_PRE)
        bs_fixtures.scaffold_classic(world_b, CHAIN_PRE)
        bs_fixtures.birth_pre_s43(world_a)
        bs_fixtures.birth_pre_s43(world_b)

        cfg_path = write_scratch_multiplex_config_two(tmp, world_a, world_b)
        proc, port = bs_fixtures.start_server(cfg_path)
        procs.append(proc)
        base_a = f"http://127.0.0.1:{port}/d/{world_a}"
        base_b = f"http://127.0.0.1:{port}/d/{world_b}"
        if not bs_fixtures.wait_health(base_a) or not bs_fixtures.wait_health(base_b):
            tail = bs_fixtures.stop_server(proc)
            raise RuntimeError(f"server never became healthy: {tail[-2000:]}")

        head_a0 = current_head(world_a)
        head_b0 = current_head(world_b)
        check("S0 baseline heads", head_a0 == 2 and head_b0 == 2,
              f"birth_pre_s43 leaves each world at head 2 (two genesis rows); "
              f"got world_a={head_a0} world_b={head_b0}", failures)

        # ---------------------------------------------------------------------------------
        # RED
        # ---------------------------------------------------------------------------------
        status = curl_status(f"http://127.0.0.1:{port}/d/unknown-world-{RUN_SUFFIX}/events")
        check("S1 unknown deployment -> 404", status == "404",
              f"GET /events on an unknown deployment; got HTTP {status}", failures)

        # S2: quiet-ledger silence -- subscribe AT the current head (so the immediate resume
        # catch-up, spec §1 item 2, never fires -- this leg's whole point is "no NEW event"),
        # write NOTHING, witness >=30s of ONLY keepalives.
        qproc, qlog = curl_subscribe(
            base_a + "/events", headers={"Last-Event-ID": str(head_a0)}, max_time=34)
        time.sleep(32)
        quiet_output = qlog.read_text(encoding="utf-8", errors="replace")
        stop_curl(qproc, qlog)
        n_keepalives = quiet_output.count(": keepalive")
        check("S2 quiet ledger: no head events, >=1 keepalive over 32s", (
            "event: head" not in quiet_output and n_keepalives >= 1
        ), f"32s of silence on a quiet ledger; keepalive lines={n_keepalives} "
           f"output={quiet_output!r}", failures)

        # S3: saturation -- SCRATCH_MAX_SSE_CLIENTS=2 concurrent connections admitted, a third
        # refused typed 503 sse_saturated.
        s3a_proc, s3a_log = curl_subscribe(base_a + "/events", max_time=8)
        s3b_proc, s3b_log = curl_subscribe(base_b + "/events", max_time=8)
        time.sleep(1.0)  # let both connections actually establish before probing the cap
        body3, status3 = curl_body_and_status(base_a + "/events", max_time=3)
        stop_curl(s3a_proc, s3a_log)
        stop_curl(s3b_proc, s3b_log)
        try:
            parsed3 = json.loads(body3) if body3.strip() else {}
        except ValueError:
            parsed3 = {}
        check("S3 saturation -> 503 sse_saturated", (
            status3 == "503" and parsed3.get("disposition") == "sse_saturated"
            and parsed3.get("max_clients") == SCRATCH_MAX_SSE_CLIENTS
        ), f"a third connection past MAX_SSE_CLIENTS={SCRATCH_MAX_SSE_CLIENTS}; "
           f"got HTTP {status3} body={body3!r}", failures)
        # Inflight gate untouched: an ordinary GET is still admitted while SSE is saturated.
        h_status, h_body = bs_fixtures.http_get(base_a + "/health")
        check("S3b inflight gate untouched -- /health still admitted while SSE saturated",
              h_status == 200, f"GET /health while 2 SSE clients held the cap; got {h_status}",
              failures)

        # ---------------------------------------------------------------------------------
        # GREEN
        # ---------------------------------------------------------------------------------
        # S4: subscribe, write one row, witness event: head within 2x poll interval.
        s4_proc, s4_log = curl_subscribe(base_a + "/events", max_time=15)
        time.sleep(0.3)  # let the connection establish (and its own catch-up poll settle)
        new_head_a = insert_decision_row(world_a, "S4 head-advance leg")
        seen = wait_for_head_event(s4_log, new_head_a, timeout=2 * SCRATCH_POLL_INTERVAL_S + 3)
        stop_curl(s4_proc, s4_log)
        check("S4 write advances head -> event: head observed", seen == new_head_a,
              f"wrote a row (new head {new_head_a}); observed head_id={seen}", failures)

        # S5: reconnect with Last-Event-ID BELOW current head -> immediate catch-up event.
        below = new_head_a - 1
        s5_proc, s5_log = curl_subscribe(
            base_a + "/events", headers={"Last-Event-ID": str(below)}, max_time=6)
        seen5 = wait_for_head_event(s5_log, new_head_a, timeout=3)
        stop_curl(s5_proc, s5_log)
        check("S5 resume below head -> immediate catch-up", seen5 == new_head_a,
              f"Last-Event-ID={below} (head is {new_head_a}); observed head_id={seen5}", failures)

        # S6: reconnect with Last-Event-ID == current head -> silence (no head event) for a
        # window well under the 15s keepalive interval (so this leg stays cheap).
        s6_proc, s6_log = curl_subscribe(
            base_a + "/events", headers={"Last-Event-ID": str(new_head_a)}, max_time=6)
        time.sleep(2 * SCRATCH_POLL_INTERVAL_S + 1)
        s6_output = s6_log.read_text(encoding="utf-8", errors="replace")
        stop_curl(s6_proc, s6_log)
        check("S6 resume at head -> no new head event", "event: head" not in s6_output,
              f"Last-Event-ID == current head ({new_head_a}); output={s6_output!r}", failures)

        # S7: two concurrent subscribers both receive the SAME head event.
        s7a_proc, s7a_log = curl_subscribe(base_a + "/events", max_time=15)
        s7b_proc, s7b_log = curl_subscribe(base_a + "/events", max_time=15)
        time.sleep(0.3)
        new_head_a2 = insert_decision_row(world_a, "S7 concurrent-subscribers leg")
        seen7a = wait_for_head_event(s7a_log, new_head_a2, timeout=2 * SCRATCH_POLL_INTERVAL_S + 3)
        seen7b = wait_for_head_event(s7b_log, new_head_a2, timeout=2 * SCRATCH_POLL_INTERVAL_S + 3)
        stop_curl(s7a_proc, s7a_log)
        stop_curl(s7b_proc, s7b_log)
        check("S7 two concurrent subscribers, same head event",
              seen7a == new_head_a2 and seen7b == new_head_a2,
              f"new head {new_head_a2}; subscriber A saw {seen7a}, subscriber B saw {seen7b}",
              failures)

        # S8: cross-deployment isolation -- a subscriber on A, resumed AT A's own current head
        # (so no immediate catch-up event fires -- this leg's whole point is "no NEW event"),
        # sees nothing when only B advances.
        head_a_now = current_head(world_a)
        s8_proc, s8_log = curl_subscribe(
            base_a + "/events", headers={"Last-Event-ID": str(head_a_now)}, max_time=8)
        time.sleep(0.3)
        new_head_b = insert_decision_row(world_b, "S8 cross-deployment isolation leg")
        time.sleep(2 * SCRATCH_POLL_INTERVAL_S + 1)
        s8_output = s8_log.read_text(encoding="utf-8", errors="replace")
        stop_curl(s8_proc, s8_log)
        check("S8 cross-deployment isolation -- A silent while only B advances",
              "event: head" not in s8_output,
              f"world_b advanced to {new_head_b}; world_a subscriber output={s8_output!r}",
              failures)

        # S9: kill the hub mid-stream -- witness clean EOF, not a hang. SIGKILL (never SIGTERM):
        # the spec's own words are "kill the hub" -- unambiguous immediate termination, proving
        # the NETWORK-LEVEL property (a dead server's socket closes; the client's read loop
        # observes EOF, never hangs forever). uvicorn's own SIGTERM graceful-drain TIMING for an
        # in-flight streaming response is a separate, pre-existing property of this service's
        # shutdown path (recently reviewed in its own right per this repo's git history) -- spec
        # §1 item 5 says this build adds NOTHING to the restart path, so this witness targets the
        # property this spec actually owns (does a dead hub leave the client hanging forever?),
        # not uvicorn's own graceful-shutdown scheduling.
        s9_proc, s9_log = curl_subscribe(base_a + "/events", max_time=20)
        time.sleep(0.3)
        proc.kill()
        proc.wait(timeout=5)
        try:
            s9_proc.wait(timeout=10)
            s9_clean = True
        except subprocess.TimeoutExpired:
            s9_clean = False
        s9_exit = s9_proc.returncode
        stop_curl(s9_proc, s9_log)
        check("S9 hub SIGKILL mid-stream -> curl observes clean EOF (no hang)", s9_clean,
              f"curl -N exited within 10s of the hub's SIGKILL (curl's own exit code {s9_exit}, "
              f"any code is 'clean' here -- the property under test is TERMINATION, not a "
              f"specific curl exit code, since an SSE body with no declared Content-Length is a "
              f"close-delimited HTTP/1.0-style body by construction)", failures)

        # ---------------------------------------------------------------------------------
        # Existing routes byte-identical + /meta advertisement (spec §3's own closure legs).
        # A fresh server is needed for these -- S9 killed the shared one above.
        # ---------------------------------------------------------------------------------
        proc2, port2 = bs_fixtures.start_server(cfg_path)
        procs.append(proc2)
        base_a2 = f"http://127.0.0.1:{port2}/d/{world_a}"
        if not bs_fixtures.wait_health(base_a2):
            tail = bs_fixtures.stop_server(proc2)
            raise RuntimeError(f"second server never became healthy: {tail[-2000:]}")
        h_status2, h_body2 = bs_fixtures.http_get(base_a2 + "/health")
        check("existing route /health untouched", h_status2 == 200 and isinstance(h_body2, dict)
              and "capabilities" in h_body2 and "world" in h_body2,
              f"GET /health after this build; status={h_status2} body keys="
              f"{sorted(h_body2) if isinstance(h_body2, dict) else h_body2!r}", failures)
        m_status2, m_body2 = bs_fixtures.http_get(base_a2 + "/meta")
        pre_existing_meta_keys = {
            "known_views", "lineage_head", "boundary_version", "protocol_version",
            "authn_mode", "max_tie_group_extra_rows",
        }
        new_meta_keys = {"max_sse_clients", "sse_poll_interval_secs"}
        check("/meta minus the two new SSE fields is byte-shape-identical to pre-build",
              m_status2 == 200 and isinstance(m_body2, dict)
              and (set(m_body2) - new_meta_keys) == pre_existing_meta_keys,
              f"GET /meta; status={m_status2} keys={sorted(m_body2) if isinstance(m_body2, dict) else m_body2!r}",
              failures)
        check("/meta advertises max_sse_clients/sse_poll_interval_secs",
              m_status2 == 200 and isinstance(m_body2, dict)
              and m_body2.get("max_sse_clients") == SCRATCH_MAX_SSE_CLIENTS
              and m_body2.get("sse_poll_interval_secs") == SCRATCH_POLL_INTERVAL_S,
              f"GET /meta; max_sse_clients={m_body2.get('max_sse_clients') if isinstance(m_body2, dict) else '?'} "
              f"sse_poll_interval_secs={m_body2.get('sse_poll_interval_secs') if isinstance(m_body2, dict) else '?'}",
              failures)
        bs_fixtures.stop_server(proc2)
        procs.remove(proc2)

        # ---------------------------------------------------------------------------------
        # S10: the watcher lifecycle leak witness -- IN-PROCESS (no live server needed): build
        # the real app/hub against world_a's real Postgres, drive connect()/disconnect() via
        # asyncio directly, and observe `hub.watcher_task` transition None -> not-None ->
        # None across a subscribe/unsubscribe cycle (never left running with zero subscribers).
        # ---------------------------------------------------------------------------------
        records = boundary_multiplex_config.load_multiplex_config(cfg_path)
        configs = {name: boundary_service.BoundaryConfig(rec) for name, rec in records.items()}
        app = boundary_service.create_app(configs)
        hub = app.state.sse_hubs[world_a]

        async def _leak_cycle() -> tuple[bool, bool, bool]:
            before = hub.watcher_task is None
            q: "asyncio.Queue[int]" = asyncio.Queue()
            await hub.connect(q)
            during = hub.watcher_task is not None and not hub.watcher_task.done()
            await hub.disconnect(q)
            # disconnect() cancels the task synchronously but the task's own CancelledError
            # unwind is a scheduling step -- yield once so it actually completes before this
            # coroutine asserts on it, mirroring how a real event loop would observe it.
            await asyncio.sleep(0)
            after = hub.watcher_task is None
            return before, during, after

        before, during, after = asyncio.run(_leak_cycle())
        check("S10 watcher lazy start/stop -- no task leak across a subscribe/unsubscribe cycle",
              before and during and after,
              f"watcher_task is None before connect ({before}), running during ({during}), "
              f"None again after the last disconnect ({after})", failures)
        # A second cycle -- the FIRST cycle proves start/stop once; a second proves the hub is
        # reusable (a watcher that failed to fully tear down would show up here as `during`
        # already being satisfied by a STALE task, or `before` failing on the second round).
        before2, during2, after2 = asyncio.run(_leak_cycle())
        check("S10b a second subscribe/unsubscribe cycle behaves identically (no residue)",
              before2 and during2 and after2,
              f"second cycle: before={before2} during={during2} after={after2}", failures)

        # ---------------------------------------------------------------------------------
        # S11: work item sse-subscriber-slot-leak (ledger row 429) -- the actual defect this
        # commission fixes, IN-PROCESS: `connect()`'s own one `await` (the head-poll,
        # `_sse_query_head` run via `asyncio.to_thread`) is monkeypatched slow enough to
        # reliably hold a `connect()` task suspended there, then the task is CANCELLED mid-poll
        # (the exact shape of a client aborting/timing out while its own SSE connection is
        # still establishing -- pre-fix this landed the cancellation AFTER `queue` was already
        # added to `hub.subscribers`, leaking the slot for process lifetime; a live hub was
        # witnessed at exactly this state, 16/16 slots held by dead connections). Asserts BOTH
        # that the queue was never left registered (the leak proper) AND that no watcher task
        # was left running for a subscriber set that (from this cycle's own perspective) should
        # be empty -- pre-fix, `during`-style registration leaves `watcher_task` running
        # forever too, since `disconnect()` (the only thing that ever stops it) is never called
        # for a queue nobody knows to disconnect.
        # ---------------------------------------------------------------------------------
        async def _cancel_during_connect_cycle() -> tuple[bool, bool]:
            orig_query_head = boundary_service._sse_query_head

            def _slow_query_head(cfg):
                time.sleep(1.5)
                return orig_query_head(cfg)

            boundary_service._sse_query_head = _slow_query_head
            try:
                q: "asyncio.Queue[int]" = asyncio.Queue()
                task = asyncio.ensure_future(hub.connect(q))
                await asyncio.sleep(0.1)  # let connect() enter the to_thread poll
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                await asyncio.sleep(0)
                leaked_registration = q in hub.subscribers
                leaked_watcher = hub.watcher_task is not None and not hub.watcher_task.done()
                return leaked_registration, leaked_watcher
            finally:
                boundary_service._sse_query_head = orig_query_head
                if hub.watcher_task is not None:
                    hub.watcher_task.cancel()
                    hub.watcher_task = None
                hub.subscribers.clear()

        leaked_registration, leaked_watcher = asyncio.run(_cancel_during_connect_cycle())
        check("S11 cancellation mid-connect() never leaks the subscriber slot (row 429)",
              not leaked_registration and not leaked_watcher,
              f"cancelled hub.connect(q) while suspended in its own head-poll await; "
              f"leaked_registration={leaked_registration} leaked_watcher={leaked_watcher} "
              f"(both must be False -- a True here reproduces the live defect: a dead "
              f"connection holding a subscriber slot for process lifetime)", failures)

    finally:
        for p in procs:
            if p.poll() is None:
                bs_fixtures.stop_server(p)
        for w in (world_a, world_b):
            bs_fixtures.teardown(w)
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"=== {len(failures)} failure(s) ===")
    for f in failures:
        print(f"  FAIL: {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
