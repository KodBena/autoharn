#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T21:18:37Z
#   last-change: 2026-07-14T21:21:45Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""live_session_check -- the ONE shared "is anything running against this deployment right now"
check (ADR-0012 P1) used by bootstrap/convert-to-submodule.sh and bootstrap/upgrade-submodule.sh
before either touches a deployment's pin. CLAUDE.md's standing rule ("Never modify hooks/ or a
user project while a live session runs there") and design/ORCH-DEPLOYMENT-PINNING.md's migration
step 1 both require this: converting or re-pinning a deployment out from under a running operator
mid-session is exactly the class of hazard pinning exists to retire, not a new way to reintroduce it.

METHOD (Linux-only, best-effort, honestly bounded -- ADR-0002: a heuristic that says so beats a
guarantee that lies). This scans /proc for processes whose current working directory or command
line references the target deployment directory:
  - cwd match: /proc/<pid>/cwd resolves (readlink) to the deployment dir or a path under it --
    catches a `claude` (or any shell) actually sitting inside the deployment when invoked.
  - cmdline match: /proc/<pid>/cmdline contains the deployment dir's own path as a substring --
    catches a hook subprocess or a long-running verb invoked WITH the deployment path as an
    argument even if its cwd has since changed.

SELF-EXCLUSION, and its own named limit (an out-of-frame hazard caught live while first exercising
this module: a plain self_pid exclusion still self-refused, because the CALLING script -- e.g.
`convert-to-submodule.sh <dest>` -- necessarily carries `<dest>` as a cmdline argument, and that
shell is this scan's own PARENT, not the scan process itself). The fix: this scan excludes its own
FULL ANCESTRY (self, parent, grandparent, ... up to pid 1), never just self_pid -- a script's own
invocation, naming the deployment path as an argument to itself, must never read as the hazard it
exists to catch. Named consequence, not hidden: if an operator types the migration/upgrade command
FROM INSIDE the very session being converted (that session's own shell is this scan's ancestor),
this scan CANNOT see it -- ancestry-exclusion blinds it to its own caller by construction. Both
callers (bootstrap/convert-to-submodule.sh, bootstrap/upgrade-submodule.sh) print this precondition
in their own banners: run the migration/upgrade from a SEPARATE terminal, never from inside the
session under conversion.

This is NOT a guarantee beyond that: it cannot see a session on a different machine, in a container
this process cannot see into, or one whose process both changed cwd away AND was invoked without
the path as an argument. It is scoped and named as exactly that -- a best-effort net, always run,
never treated as a substitute for the operator's own knowledge of whether they still have a session
open against this deployment. Combined with the caller's own typed confirmation, not offered as a
replacement for one.

Exit 0 (clear -- no live session detected) or 1 (one or more found -- printed to stderr, PIDs +
cmdlines named so an operator can go end them). Lazy imports banned (top-of-file only).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class LiveMatch:
    """One process this scan believes is running against the deployment dir -- WHY it matched
    (cwd vs cmdline), never silently merged, so a report can name its own basis."""
    pid: int
    reason: str
    cmdline: str


def _ancestor_pids(pid: int, proc_root: str) -> set[int]:
    """pid and every one of its ancestors (parent, grandparent, ...) up to pid 1 or the first
    unreadable/self-looping link -- read from /proc/<pid>/status's `PPid:` line. Best-effort: a
    process that exits mid-walk (a race, not a hazard here) just stops the walk early rather than
    raising -- the ancestry gathered so far is still a valid, if possibly incomplete, exclusion
    set (erring toward excluding TOO FEW ancestors, never silently excluding an unrelated pid)."""
    seen: set[int] = set()
    cur = pid
    while cur not in seen and cur > 0:
        seen.add(cur)
        try:
            with open(os.path.join(proc_root, str(cur), "status"), "r") as f:
                status = f.read()
        except OSError:
            break
        ppid = None
        for line in status.splitlines():
            if line.startswith("PPid:"):
                try:
                    ppid = int(line.split(":", 1)[1].strip())
                except ValueError:
                    ppid = None
                break
        if ppid is None or ppid <= 0:
            break
        cur = ppid
    return seen


def find_live_sessions(deployment_dir: str, *, self_pid: int | None = None) -> list[LiveMatch]:
    """Scan /proc for processes whose cwd or cmdline references `deployment_dir`, EXCLUDING this
    scan's own full process ancestry (self, parent, grandparent, ... -- see module docstring for
    why a bare self_pid exclusion is not enough: the calling script's own invocation legitimately
    carries `deployment_dir` as a cmdline argument, and would otherwise self-refuse every time).
    `self_pid` defaults to os.getpid()."""
    if self_pid is None:
        self_pid = os.getpid()
    target = os.path.realpath(deployment_dir)
    matches: list[LiveMatch] = []
    proc_root = "/proc"
    if not os.path.isdir(proc_root):
        # Not Linux, or /proc unavailable -- degrade HONESTLY (raise, not a silent empty pass;
        # ADR-0002). The caller decides whether that is fatal for its own refusal posture.
        raise RuntimeError(
            f"live_session_check: {proc_root} is not available -- this scan only works on Linux; "
            f"it cannot verify the absence of a live session on this platform. Refusing to report "
            f"a false 'clear' (a caller MUST NOT proceed on an unverifiable check)."
        )
    excluded = _ancestor_pids(self_pid, proc_root)
    for entry in os.listdir(proc_root):
        if not entry.isdigit():
            continue
        pid = int(entry)
        if pid in excluded:
            continue
        pid_dir = os.path.join(proc_root, entry)
        reason = None
        try:
            cwd = os.readlink(os.path.join(pid_dir, "cwd"))
        except OSError:
            cwd = None
        if cwd is not None and (cwd == target or cwd.startswith(target + os.sep)):
            reason = f"cwd={cwd}"
        cmdline = ""
        try:
            with open(os.path.join(pid_dir, "cmdline"), "rb") as f:
                raw = f.read()
            cmdline = raw.replace(b"\x00", b" ").decode("utf-8", errors="replace").strip()
        except OSError:
            cmdline = ""
        if reason is None and target in cmdline:
            reason = "cmdline references deployment path"
        if reason is not None:
            matches.append(LiveMatch(pid=pid, reason=reason, cmdline=cmdline))
    return matches


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: live_session_check.py <deployment-dir>", file=sys.stderr)
        return 2
    deployment_dir = argv[1]
    if not os.path.isdir(deployment_dir):
        print(f"live_session_check: {deployment_dir} is not a directory", file=sys.stderr)
        return 2
    try:
        matches = find_live_sessions(deployment_dir)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1
    if matches:
        print(f"live_session_check: {len(matches)} process(es) appear to be running against "
              f"{deployment_dir} -- REFUSING (this is a best-effort scan, not a guarantee; if you "
              f"know these are stale/unrelated, end them or investigate before re-running):",
              file=sys.stderr)
        for m in matches:
            print(f"  pid={m.pid}  {m.reason}  cmd={m.cmdline!r}", file=sys.stderr)
        return 1
    print(f"live_session_check: clear -- no process found with cwd or cmdline under "
          f"{os.path.realpath(deployment_dir)} (best-effort Linux /proc scan; see module "
          f"docstring for what this does and does not catch)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
