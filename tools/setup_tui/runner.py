# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T21:31:32Z
#   last-change: 2026-07-19T00:59:37Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/runner.py -- the ONE place this package shells out (ADR-0012 P1), AND (as of
the `--dry-run` amendment, design/FABLE-SETUP-TUI-SPEC.md 2026-07-19) the ONE place it decides
whether an act it is about to perform is real or a nondestructive rehearsal of itself. Every
screen that drives an existing verb calls `run_command` here, never `subprocess` directly, and
every screen that starts a background process calls `start_background` here, never
`subprocess.Popen` directly -- this is what makes rule 1 ("every screen shows the EXACT command
it is about to run and streams that command's real output") a structural property instead of a
per-screen promise, and what makes `--dry-run` a property of ONE choke point instead of a
conditional scattered through every screen. `write_file` is the same discipline's second choke
point, for the (much rarer) act of this package writing a file directly rather than shelling out
to a verb that writes one.

Every one of the three takes `dry_run: bool` (screens read it once, from `state["dry_run"]`, set
by `app.py` from `--dry-run` and threaded through the shared `state` dict every screen already
carries -- the parent spec's own "single flag on shared state" shape, not a second parameter
list). Under `dry_run=True`, none of the three performs the act: the exact argv/path is still
echoed (rule 1 is unconditional -- a dry run must show precisely what it would have run), but
`run_command` never Popens, `start_background` never Popens, and `write_file` never opens the
path for writing. `run_command` and `start_background` report a SIMULATED success (`ok=True`)
under `dry_run` -- not because anything actually succeeded, but because a rehearsal's job is to
walk the WHOLE flow through to the end and show every downstream would-be act, not stop at the
first step whose live success it cannot know. Every result carries `dry_run` on its own dataclass
so a screen's checklist status decision reads directly off the result (`ck.WOULD_DO if
res.dry_run else (ck.WITNESSED if res.ok else ck.REFUSED)`, `checklist.status_for`) rather than
needing the flag threaded a second time to every `cl.add` call site.
"""
from __future__ import annotations

import shlex
import subprocess
import sys
from dataclasses import dataclass, field


def quote_argv(argv: list[str]) -> str:
    """A copy-paste-able rendering of argv -- shell-quotes only the tokens that need it, so the
    printed line matches what an operator would actually type (spec: 'the exact command it is
    about to run')."""
    return " ".join(shlex.quote(a) for a in argv)


@dataclass
class CommandResult:
    argv: list[str]
    returncode: int
    output: str
    dry_run: bool = False
    ok: bool = field(init=False)

    def __post_init__(self) -> None:
        self.ok = self.returncode == 0


def run_command(argv: list[str], *, cwd: str | None = None, env: dict | None = None,
                 stdin_text: str | None = None, echo: bool = True,
                 dry_run: bool = False) -> CommandResult:
    """Runs `argv`, printing the exact command line first, then streaming stdout+stderr
    (merged, in real time) to this process's own stdout as it arrives, and finally returning the
    full captured text alongside the exit code. `stdin_text`, if given, is written to the
    child's stdin then closed (used for the teardown verb's typed-world-name confirmation).

    Under `dry_run=True`, the argv is still echoed (unconditionally -- rule 1's show-the-command
    discipline does not bend for a rehearsal) but NOTHING is executed: no Popen, no database act,
    no file write, no ledger write -- whatever `argv` would have done stays undone. The returned
    `CommandResult` reports `returncode=0`, `ok=True` (a SIMULATED success, `dry_run=True` on the
    result so the caller never mistakes it for a real one) and a placeholder `output` naming the
    fact, so the flow can walk on to the acts that would follow a real success -- the WOULD-DO
    table it builds along the way is the full flow, not just the first step."""
    if echo:
        print(f"$ {quote_argv(argv)}")
    if dry_run:
        print("  [dry-run: not executed]")
        return CommandResult(argv=list(argv), returncode=0,
                              output="[dry-run: not executed]", dry_run=True)
    proc = subprocess.Popen(
        argv, cwd=cwd, env=env,
        stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    if stdin_text is not None:
        assert proc.stdin is not None
        proc.stdin.write(stdin_text)
        proc.stdin.close()
    lines: list[str] = []
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        lines.append(line)
    proc.wait()
    return CommandResult(argv=list(argv), returncode=proc.returncode, output="".join(lines))


@dataclass
class BackgroundResult:
    argv: list[str]
    proc: subprocess.Popen | None
    dry_run: bool = False


def start_background(argv: list[str], *, cwd: str | None = None, echo: bool = True,
                      dry_run: bool = False) -> BackgroundResult:
    """The non-waited counterpart of `run_command`, for the one act this package starts and
    leaves running rather than runs to completion (screen 6's boundary service) -- same argv-echo
    discipline (`$ argv`, unconditional, same shape `run_command` uses) so a dry run's WOULD-DO
    line and a live run's printed command line are the SAME text, which is what the dry-run
    amendment's WDR2 parity witness relies on (diffing the two runs' `$ `-prefixed lines).
    Under `dry_run=True`, argv is echoed but nothing is Popened -- `proc` is None, and the caller
    must not probe a service that was never started (record the post-start health/meta probes as
    DRY-SKIPPED, per the amendment's own rule for PREPARED-block verification gates)."""
    if echo:
        print(f"$ {quote_argv(argv)}   (background)")
    if dry_run:
        print("  [dry-run: not started]")
        return BackgroundResult(argv=list(argv), proc=None, dry_run=True)
    proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True)
    return BackgroundResult(argv=list(argv), proc=proc, dry_run=False)


def write_file(path: str, content: str, *, dry_run: bool = False,
               encoding: str = "utf-8") -> bool:
    """The second act-execution choke point (module docstring): writes `content` to `path`
    UNLESS `dry_run`, in which case nothing is written -- the caller is responsible for recording
    the WOULD-DO row (path + a one-line content summary, `summarize_content` below), since the
    checklist item names differ per call site. Returns True iff a real write happened, so a
    caller never has to duplicate the `if dry_run` test to decide its own checklist status."""
    if dry_run:
        return False
    with open(path, "w", encoding=encoding) as f:
        f.write(content)
    return True


def summarize_content(content: str, limit: int = 100) -> str:
    """A one-line content summary for a WOULD-DO file-write row (spec: 'the exact file paths it
    would write with a one-line content summary each') -- the first non-blank line, truncated,
    plus a byte count, never the full content (a WOULD-DO table row is a summary, not a dump)."""
    first = next((ln for ln in content.splitlines() if ln.strip()), "")
    if len(first) > limit:
        first = first[:limit] + "..."
    return f"{first!r} ({len(content)} bytes total)"
