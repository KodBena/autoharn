#!/usr/bin/env python3
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

REFUSE-class vs WARN-class (narrowed 2026-07-15, maintainer ratification -- ledger row 1055):
originally EVERY cwd/cmdline match above was treated as a refusal, which meant a bare shell
sitting in the deployment directory (an interactive terminal, an editor, an unrelated script)
blocked every migration/conversion/upgrade -- the maintainer's own words, hitting this over a
plain zsh prompt: "the shell is not 'running against' autoharn. It's very unergonomical, what
we have now." The hazard this module actually exists to catch (CLAUDE.md: "never modify hooks/
or a user project while a live session runs there") is an ACTIVE CLAUDE CODE SESSION -- the
ledger-writing agent, not every process that happens to reside in the directory. So each match
above is further classified:

  - REFUSE-class ("claude"): the matched process looks like an actual Claude Code invocation --
    argv[0]'s basename is exactly "claude" (the bare-binary shape the maintainer's own session
    showed, cmd='claude'), OR the process's full cmdline contains the substring "claude-code"
    (catches the standard npm/node-wrapped launcher, e.g. `node .../@anthropic-ai/claude-code/
    cli.js`, whose argv[0] is "node" and would otherwise be invisible to an argv[0]-only check).
    These still REFUSE, loudly, exactly as before.
  - WARN-class (everything else matched by cwd/cmdline -- shells, editors, sleep, arbitrary
    scripts, unrelated tooling): no longer a refusal. Listed as informational output only,
    clearly prefixed "not blocking", and the caller proceeds.

MATCHING RULE, STATED HONESTLY, WITH ITS LIMITS: this is a NAME heuristic, not an identity
check. It is trivially spoofable in both directions:
  - FALSE REFUSE: any process can exec itself with argv[0]="claude" (or put "claude-code"
    anywhere on its command line) without being Claude Code at all -- the fixture that proves
    REFUSE-class in seen-red/ does exactly this deliberately, to prove the predicate fires.
  - FALSE WARN (a miss): a genuine Claude Code process invoked through a wrapper that neither
    names its argv[0] "claude" nor carries "claude-code" anywhere on its command line (e.g. a
    from-source dev checkout run as `python cli.py` under a differently-named venv, or a
    renamed/repackaged binary) will NOT be recognized and is silently demoted to WARN-class.
This heuristic is scoped to the two invocation shapes actually observed in the field (the bare
`claude` binary, and the standard node-wrapped npm launcher) -- it is not a security boundary,
and a WARN-class miss on an actual session is not this module's guarantee to make: the operator's
own knowledge of whether they still have a session open remains load-bearing, exactly as for the
pre-existing cwd/cmdline best-effort limits described above.

Exit 0 (clear of REFUSE-class sessions -- WARN-class bystanders, if any, are printed but do not
block) or 1 (one or more REFUSE-class matches found -- printed to stderr, PIDs + cmdlines named
so an operator can go end them). Lazy imports banned (top-of-file only).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass


REFUSE_CLASS = "claude"
WARN_CLASS = "bystander"


@dataclass(frozen=True)
class LiveMatch:
    """One process this scan believes is running against the deployment dir -- WHY it matched
    (cwd vs cmdline), never silently merged, so a report can name its own basis. `session_class`
    is REFUSE_CLASS ("claude") or WARN_CLASS ("bystander") -- see module docstring for the
    matching rule and its stated limits."""
    pid: int
    reason: str
    cmdline: str
    session_class: str


def _is_claude_code_process(argv: list[str], cmdline: str) -> bool:
    """The matching rule, in one place (module docstring states it in prose + names its limits):
    argv[0]'s basename is exactly "claude" (the bare-binary shape), OR the full cmdline contains
    the substring "claude-code" (the standard node-wrapped npm launcher, whose argv[0] is "node"
    and would otherwise be invisible to an argv[0]-only check). A NAME heuristic, not an identity
    check -- spoofable in both directions, honestly documented above."""
    if argv and os.path.basename(argv[0]) == "claude":
        return True
    return "claude-code" in cmdline


def partition_matches(matches: list[LiveMatch]) -> tuple[list[LiveMatch], list[LiveMatch]]:
    """Split a match list into (refuse_matches, warn_matches) by `session_class`. One place for
    every caller (this module's own main(), migrate_core.py) to apply the same split -- ADR-0012
    P1, not a second copy of the partition logic per caller."""
    refuse = [m for m in matches if m.session_class == REFUSE_CLASS]
    warn = [m for m in matches if m.session_class == WARN_CLASS]
    return refuse, warn


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
        argv_list: list[str] = []
        try:
            with open(os.path.join(pid_dir, "cmdline"), "rb") as f:
                raw = f.read()
            argv_list = [a.decode("utf-8", errors="replace") for a in raw.split(b"\x00") if a != b""]
            cmdline = raw.replace(b"\x00", b" ").decode("utf-8", errors="replace").strip()
        except OSError:
            cmdline = ""
        if reason is None and target in cmdline:
            reason = "cmdline references deployment path"
        if reason is not None:
            session_class = REFUSE_CLASS if _is_claude_code_process(argv_list, cmdline) else WARN_CLASS
            matches.append(LiveMatch(pid=pid, reason=reason, cmdline=cmdline, session_class=session_class))
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
    refuse_matches, warn_matches = partition_matches(matches)
    if warn_matches:
        print(f"live_session_check: not blocking -- {len(warn_matches)} process(es) merely "
              f"reside in {deployment_dir} (cwd or cmdline match, but do not look like a Claude "
              f"Code session -- see module docstring's REFUSE-class/WARN-class matching rule):")
        for m in warn_matches:
            print(f"  pid={m.pid}  {m.reason}  cmd={m.cmdline!r}")
    if refuse_matches:
        print(f"live_session_check: {len(refuse_matches)} Claude Code process(es) appear to be "
              f"running against {deployment_dir} -- REFUSING (this is a best-effort scan, not a "
              f"guarantee; if you know these are stale/unrelated, end them or investigate before "
              f"re-running):", file=sys.stderr)
        for m in refuse_matches:
            print(f"  pid={m.pid}  {m.reason}  cmd={m.cmdline!r}", file=sys.stderr)
        return 1
    print(f"live_session_check: clear of Claude Code sessions under "
          f"{os.path.realpath(deployment_dir)} (best-effort Linux /proc scan; see module "
          f"docstring for what this does and does not catch)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
