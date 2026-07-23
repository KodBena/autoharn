#!/usr/bin/env python3
"""ensure_running -- the ONE shared home for "make the boundary a deployment record names
reachable, spawning it as a detached child if it is not" (design/FABLE-AUTOHARN-UMBRELLA-CLI-
SPEC.md §2). Round-1 review's DIRECTED WORK item: spec §2 ratifies "every invocation that needs
the boundary resolves it: reachable -> use it ... Unreachable -> ... SPAWN ... print ONE line ...
then proceed" for EVERY verb, but the umbrella build's first draft only wired this into the
explicit `autoharn service start/status/stop` control-plane verb (`libexec/autoharn-service`) --
no served shim actually auto-spawned anything. This module factors the STRUCTURALLY-CORRECT
probe/spawn/race-resolution logic (round-1 review SEVERE-2/SEVERE-3/SEVERE-4 fixes) out of
`libexec/autoharn-service` into one place BOTH that script and every served CLI shim's own
`serving/boundary_cli_client.py`-based served-config path can call -- `libexec/autoharn-service`
now imports this module rather than carrying a second copy of the same logic (ADR-0012 P1: one
home, not two drifting copies).

TWO call shapes, two verbosity needs, same underlying `spawn_and_wait`:
  - `libexec/autoharn-service`'s own `autoharn service start` verb wants VERBOSE, multi-line
    diagnosis (an operator explicitly asked for control-plane detail) -- it calls `probe` and
    `spawn_and_wait` directly and formats its own messages, unchanged from before this refactor.
  - `ensure_running_or_leave_unreachable` below is the ONE-LINE policy a served shim's own
    `_load_config()` wants (spec §2, verbatim: "print ONE line saying so, then proceed") -- it is
    the function `serving/boundary_cli_client.py`'s four served callers (`led`, `pickup`,
    `distance-to-clean`, `asof-export`) call when `check_protocol_version` first raises
    `BoundaryUnreachable`, before retrying that SAME check once more and letting whatever it
    raises the second time propagate unchanged (this module never invents a NEW refusal shape;
    "if spawn fails, the existing loud refusal" -- round-1 review DIRECTED WORK, verbatim).
    Ensure-running never fights an explicit `autoharn service stop` within the SAME invocation's
    scope (spec §2) -- there is no such overlap here, since a served shim's own single call
    either succeeds or fails within its own one invocation, never spanning a separate `stop`.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import is top-of-file. No bare types in
new Python (ledger row 1105): every function signature below carries its return-type annotation.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import boundary_cli_client as bcc  # noqa: E402

AUTOHARN_ROOT = _HERE.parent

_POLL_INTERVAL_S = 0.05
_POLL_TIMEOUT_S = 10.0

# Probe outcomes -- named once, read by every call site (ADR-0012 P1).
OK = "ok"                    # a version-compatible autoharn boundary answered its own /health
UNREACHABLE = "unreachable"  # nothing answered at all -- eligible for spawn/adopt
REFUSED = "refused"          # something answered, but it is not a boundary we can trust: a
                              # squatting non-autoharn HTTP responder, OR a version-skewed peer.
                              # Never spawned over (the port is genuinely held) and never adopted.


def probe(url: str, boundary_deployment: str) -> tuple[str, str | None]:
    """The row-1165 "reachable -> use it" check, upgraded past round-1 review's SEVERE-4 finding
    (any HTTP response, even a bare 404, used to count as reachable). Returns (OK, None),
    (UNREACHABLE, None), or (REFUSED, <teaching message, already formatted for stderr>)."""
    base = f"{url}/d/{boundary_deployment}"
    try:
        bcc.check_protocol_version(base, url)
        return OK, None
    except bcc.BoundaryUnreachable:
        return UNREACHABLE, None
    except bcc.ProtocolVersionMismatch as e:
        msg = (f"REFUSED -- something answers at {url} but speaks an incompatible wire "
               f"protocol. This client speaks protocol {e.client_version!r}; it answers "
               f"{e.server_version!r}. Remedy: upgrade this checkout to match the boundary's "
               f"running version, or point it at a boundary running the matching checkout "
               f"(design/FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md §3). Refusing to adopt an "
               f"incompatible peer; nothing was spawned over it either (the port is genuinely "
               f"held).")
        return REFUSED, msg
    except bcc.BoundaryRefusal as e:
        msg = (f"REFUSED -- something answers HTTP at {url} (deployment segment "
               f"/d/{boundary_deployment}) but not with this project's own /health shape "
               f"(HTTP {e.status}: {e.body!r}). This looks like a different, non-autoharn "
               f"process squatting on the port -- refusing to adopt it, and refusing to spawn "
               f"over a port that is genuinely held by something else. Nothing was touched.")
        return REFUSED, msg


def pid_is_boundary_service(pid: int, toml_path: Path) -> bool:
    """Round-1 review SEVERE-3: PID REUSE means a pidfile can outlive the process it named --
    the OS is free to hand that same pid to an unrelated process later. Signaling a pid on trust
    alone risks SIGTERMing a bystander while reporting success. This checks `/proc/<pid>/cmdline`
    (Linux-specific -- this project targets Linux hosts) names `serving.boundary_service` AND
    this same world's own `boundary-multiplex.toml` path."""
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return False
    text = raw.replace(b"\x00", b" ").decode("utf-8", errors="replace")
    return "serving.boundary_service" in text and str(toml_path) in text


@dataclass(frozen=True)
class SpawnOutcome:
    """The structured result of one `spawn_and_wait` call -- deliberately NOT pre-formatted into
    a message string here, so each caller (the verbose `autoharn service start` verb vs. the
    ONE-LINE served-shim policy below) can render what its own verbosity contract needs from the
    same facts (ADR-0012 P1: one place computes the facts, not one place per caller)."""
    status: str          # "own" (this invocation's own spawn won) | "adopted" (someone else's
                          # spawn/process won) | "failed" (still unreachable after the poll
                          # timeout, or refused outright)
    proc_pid: int | None  # this invocation's own spawned child's pid (None if it never spawned,
                          # e.g. no boundary-multiplex.toml to spawn from)
    winner_pid: int | None  # the pid actually holding the port, when known (status == "own" or
                          # "adopted" with a pidfile visible)
    log_path: Path | None
    detail: str | None    # REFUSED-shaped teaching text (status == "failed" only)


def spawn_and_wait(world_dir: Path, url: str, port: int, boundary_deployment: str,
                    *, poll_timeout_s: float = _POLL_TIMEOUT_S) -> SpawnOutcome:
    """Spawns a detached `python3 -m serving.boundary_service` child (unless no
    boundary-multiplex.toml exists to spawn from, in which case this returns "failed"
    immediately) and resolves the bind-as-lock race STRUCTURALLY (round-1 review SEVERE-2 fix:
    the pidfile is written by the spawned child ITSELF, synchronously, immediately after its own
    listen-socket bind succeeds -- see serving/boundary_service.py's own `--pidfile` handling --
    never a timing grace-window here). Caller must have already established the boundary is
    UNREACHABLE (via `probe`) before calling this -- this function does not re-check that itself,
    since callers differ in how much of that check they have already done."""
    toml_path = world_dir / "boundary-multiplex.toml"
    if not toml_path.is_file():
        return SpawnOutcome(
            status="failed", proc_pid=None, winner_pid=None, log_path=None,
            detail=f"REFUSED -- {url} is unreachable and no boundary-multiplex.toml exists at "
                   f"{toml_path} to spawn from. Run the setup wizard against this world to "
                   f"configure a boundary first (python3 tools/setup_tui/app.py {world_dir}). "
                   f"Nothing was touched.")
    log_path = world_dir / "service.log"
    pidfile = world_dir / ".autoharn-service.pid"
    # A STALE pidfile at this exact path (left behind by a service that died without cleanup) is
    # safe to clear here: the caller already established the boundary is UNREACHABLE right now,
    # so whatever pid this file names (if any) is not answering the port any more -- keeping it
    # around would make the child's own O_CREAT|O_EXCL pidfile write below fail spuriously.
    pidfile.unlink(missing_ok=True)
    py = sys.executable
    argv_child = [py, "-m", "serving.boundary_service", "--config", str(toml_path),
                  "--port", str(port), "--pidfile", str(pidfile)]
    log_fh = open(log_path, "ab")
    # Detached child (row 1154: no systemd/D-Bus anywhere) -- start_new_session=True is the
    # portable stdlib equivalent of setsid, so this child survives this invocation's own exit;
    # stdout/stderr redirected to a per-world log file, never inherited.
    proc = subprocess.Popen(
        argv_child, cwd=str(AUTOHARN_ROOT), stdin=subprocess.DEVNULL,
        stdout=log_fh, stderr=log_fh, start_new_session=True,
    )
    log_fh.close()
    # BIND-AS-LOCK RACE, STRUCTURAL RESOLUTION (spec §2; round-1 review SEVERE-2 fix): wait for
    # one of two STRUCTURAL facts -- (a) the pidfile appears (written ONLY by whichever child's
    # own bind() call actually succeeded), or (b) this invocation's own child exits without ever
    # writing it (proof its own bind lost). No sleep-then-trust-poll() timing assumption anywhere.
    deadline = time.monotonic() + poll_timeout_s
    while time.monotonic() < deadline:
        if pidfile.is_file():
            try:
                winner_pid = int(pidfile.read_text(encoding="utf-8").strip())
            except (OSError, ValueError):
                time.sleep(_POLL_INTERVAL_S)
                continue
            outcome, _detail = probe(url, boundary_deployment)
            if outcome != OK:
                time.sleep(_POLL_INTERVAL_S)
                continue
            status = "own" if winner_pid == proc.pid else "adopted"
            return SpawnOutcome(status=status, proc_pid=proc.pid, winner_pid=winner_pid,
                                 log_path=log_path, detail=None)
        if proc.poll() is not None:
            outcome, _detail = probe(url, boundary_deployment)
            if outcome == OK:
                return SpawnOutcome(status="adopted", proc_pid=proc.pid, winner_pid=None,
                                     log_path=log_path, detail=None)
            if outcome == REFUSED:
                return SpawnOutcome(status="failed", proc_pid=proc.pid, winner_pid=None,
                                     log_path=log_path, detail=_detail)
            break
        time.sleep(_POLL_INTERVAL_S)
    child_exit = proc.poll()
    detail = (f"REFUSED -- {url} is still unreachable after {poll_timeout_s}s. Spawned child "
              f"(pid {proc.pid}) "
              + (f"exited with code {child_exit}" if child_exit is not None else "is still running")
              + f" -- see {log_path} for the diagnosis (a genuinely-held port, an invalid "
                f"boundary-multiplex.toml, or a slow-starting process needing a longer wait).")
    return SpawnOutcome(status="failed", proc_pid=proc.pid, winner_pid=None, log_path=log_path,
                        detail=detail)


def ensure_running_or_leave_unreachable(deployment_path: str | Path, prog: str,
                                         *, notify=sys.stderr) -> None:
    """The served-shim policy (spec §2, verbatim: "Unreachable -> ... SPAWN ... print ONE line
    ... then proceed"). Called from `serving/boundary_cli_client.py`'s four served callers'
    `_load_config()` ONLY after their own `check_protocol_version` has already raised
    `bcc.BoundaryUnreachable` once -- this function never probes on its own initiative (the
    caller already knows the boundary was unreachable a moment ago) and never spawns over a
    REFUSED (squatter/version-skewed) peer: that is not this function's problem to fix, and
    attempting to spawn over a port something else genuinely holds would only produce a second,
    confusing failure. On success or failure alike, this prints AT MOST one line to `notify`
    (stderr by default) and returns -- it never raises. The CALLER is expected to retry its own
    `check_protocol_version` once more immediately after this returns, and let whatever THAT
    raises (or does not) propagate unchanged -- "if spawn fails, the existing loud refusal"
    (round-1 review DIRECTED WORK, verbatim): this function invents no new refusal shape."""
    deployment_path = Path(deployment_path)
    try:
        record = json.loads(deployment_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return  # the caller's own retry will hit its own, already-existing refusal for this
    url = record.get("boundary_url") if isinstance(record, dict) else None
    boundary_deployment = record.get("boundary_deployment") if isinstance(record, dict) else None
    if not url or not boundary_deployment:
        return
    parsed = urlparse(url)
    if not parsed.port:
        return
    world_dir = deployment_path.parent
    outcome = spawn_and_wait(world_dir, url, parsed.port, boundary_deployment)
    if outcome.status == "own":
        notify.write(f"{prog}: boundary at {url} was unreachable -- spawned it (pid "
                     f"{outcome.proc_pid}, logs at {outcome.log_path}); proceeding.\n")
    elif outcome.status == "adopted":
        who = f"pid {outcome.winner_pid}" if outcome.winner_pid is not None else "a concurrent process"
        notify.write(f"{prog}: boundary at {url} was unreachable -- {who} is now serving it "
                     f"(this invocation's own spawn attempt lost the race or was unnecessary); "
                     f"proceeding.\n")
    # status == "failed": print nothing extra here -- the caller's own retried
    # check_protocol_version raises BoundaryUnreachable again momentarily, and ITS existing,
    # already-teaching refusal (report_boundary_exception, including the restart-command hint
    # when boundary_url is in scope) is the one message this leaves the caller to show.
