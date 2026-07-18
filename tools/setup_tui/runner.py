# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T21:31:32Z
#   last-change: 2026-07-18T21:31:41Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/runner.py -- the ONE place this package shells out (ADR-0012 P1). Every
screen that drives an existing verb calls `run_command` here, never `subprocess` directly --
this is what makes rule 1 ("every screen shows the EXACT command it is about to run and streams
that command's real output") a structural property instead of a per-screen promise.
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
    ok: bool = field(init=False)

    def __post_init__(self) -> None:
        self.ok = self.returncode == 0


def run_command(argv: list[str], *, cwd: str | None = None, env: dict | None = None,
                 stdin_text: str | None = None, echo: bool = True) -> CommandResult:
    """Runs `argv`, printing the exact command line first, then streaming stdout+stderr
    (merged, in real time) to this process's own stdout as it arrives, and finally returning the
    full captured text alongside the exit code. `stdin_text`, if given, is written to the
    child's stdin then closed (used for the teardown verb's typed-world-name confirmation)."""
    if echo:
        print(f"$ {quote_argv(argv)}")
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
