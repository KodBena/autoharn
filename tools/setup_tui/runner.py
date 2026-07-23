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

import os
import re
import shlex
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field

# The ONE home (ADR-0012 P1; ledger row 1799 finding 1) for the fact this pattern encodes: every
# write-verb this package drives (`led`, `legacy/led`, `role_charter.py` via `led decision`) ends
# a successful write with a line of the shape `... row <id> written.` (or `row_id=<id>` /
# `row: <id>`) -- the SAME `write_and_report`/`kernel_write` idiom `led.tmpl` and
# `legacy-led.tmpl` both share. This regex, and `parse_row_id` below, are THAT fact's one home;
# before this fix it was hand-copied three times (tools/setup_tui/principals_authority.py,
# tools/setup_tui/signed_genesis.py, tools/setup_tui/screens.py) -- three independent literal
# copies of one fact, the exact P1 violation the anti-pattern checklist's row B names.
ROW_ID_RE = re.compile(r"\brow[_ ]?(?:id)?[:=]?\s*(\d+)\b", re.IGNORECASE)


def parse_row_id(output: str) -> int | None:
    """The row id `led`/`legacy/led` reports on a successful write, parsed from that verb's own
    stdout convention (`ROW_ID_RE`'s docstring above) -- `None` if no such id appears (a caller
    is responsible for deciding what "no id parsed" means for its own dry-run/failure cases; this
    function only ever reports what the text actually says, never a fabricated id)."""
    m = ROW_ID_RE.search(output)
    return int(m.group(1)) if m else None


def legacy_led_path(dest: str) -> str:
    """`<dest>/legacy/led` -- ONE HOME (ADR-0012 P1) for this path string. RETIRED as an
    execution target (legacy-led-retirement inventory pass, ledger row 1149/1150,
    design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md's own retirement act): `bootstrap/templates/
    legacy-led.tmpl` no longer exists in this repository, and the scaffolded `<dest>/legacy/led`
    shim is now a one-line teaching refusal, never a working direct-psql CLI. This path string
    still names a REAL FILE every scaffolded world carries (destination.py's own
    AUTOHARN_COMPLETE classifier guarantee, `_LEGACY_LED_REL`) -- kept for that existence-check
    use (`screens.py`'s "legacy/led present" completeness rows), never for driving a real
    command through it; no caller in this package resolves an execution target to this path
    anymore (see `resolve_led` below)."""
    return os.path.join(dest, "legacy", "led")


def served_led_path(dest: str) -> str:
    """`<dest>/led` -- the rebased, SERVED shim (bootstrap/templates/led.tmpl) that refuses
    outright without `deployment.json`'s `boundary_url`/`boundary_deployment` keys
    (serving/boundary_cli_client.py `load_served_config`) -- those keys are written only once
    `screen_boundary` has actually run. Since legacy-led-retirement (ledger row 1149/1150,
    boundary now mandatory at every birth), this is the ONLY led execution target this whole
    package ever resolves."""
    return os.path.join(dest, "led")


def resolve_led(dest: str) -> str | None:
    """Resolves the led executable an ALREADY-EXISTING world (real files checked live on disk)
    should be driven through for an ordinary attributed write.

    legacy-led-retirement inventory pass (ledger row 1149/1150): this function used to prefer
    `legacy_led_path(dest)`, falling back to `served_led_path(dest)` only for an older pre-split
    scaffold -- mirroring `bootstrap/extract_context.py`'s own (now similarly retired) `_find_led`
    preference. That preference is GONE: legacy-led.tmpl no longer exists in this repository, the
    boundary is mandatory at every birth (no decline option, `screens.screen_boundary`'s own
    docstring), and `legacy_led_path(dest)` resolves to a one-line teaching-refusal stub that
    would never perform the write a caller here is resolving this path FOR. This now checks only
    `served_led_path(dest)`, live, exactly as `bootstrap/extract_context.py`'s own retired
    `_find_led` docstring names it: "no candidate search remains -- there is exactly one lawful
    `led` per world." Returns `None` if it does not exist as an executable file.

    NOT for a `dest` that is still a QUEUED, not-yet-committed plan entry (birth hasn't run yet
    this session) -- there is nothing on disk yet to check; a caller in that position uses
    `served_led_path(dest)` directly, exactly as principals_authority.py/signed_genesis.py
    already do (their own module docstrings) and as `screens.screen_hydration`'s
    `dest_would_exist` branch now does too."""
    cand = served_led_path(dest)
    if os.path.isfile(cand) and os.access(cand, os.X_OK):
        return cand
    return None


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
    # ADDITIVE (fd-inheritance-by-design-outliving-children fix, this dated fix's own closure
    # statement below): the real file `proc`'s stdout+stderr were redirected to, or `None` under
    # `dry_run=True` (nothing started, nothing to name) -- carried back so a caller that wants to
    # tail it, print it in the UI, or clean it up later can, without this function guessing what
    # the caller wants done with that fact. Defaulted so no existing construction call site (there
    # is exactly one today, this module's own) needs to change.
    log_path: str | None = None


def start_background(argv: list[str], *, cwd: str | None = None, echo: bool = True,
                      dry_run: bool = False, log_path: str | None = None) -> BackgroundResult:
    """The non-waited counterpart of `run_command`, for the one act this package starts and
    leaves running rather than runs to completion (the boundary screen's boundary service) --
    same argv-echo discipline (`$ argv`, unconditional, same shape `run_command` uses) so a
    dry run's WOULD-DO line and a live run's printed command line are the SAME text, which is
    what the dry-run amendment's WDR2 parity witness relies on (diffing the two runs' `$ `-
    prefixed lines).
    Under `dry_run=True`, argv is echoed but nothing is Popened -- `proc` is None, and the caller
    must not probe a service that was never started (record the post-start health/meta probes as
    DRY-SKIPPED, per the amendment's own rule for PREPARED-block verification gates).

    STDIN/STDOUT HYGIENE (maintainer field observation f, "after finally answering all
    questions, seems that PTY control is not released to the user"; fresh-context investigator's
    mechanism finding). This function's whole point is a child that OUTLIVES this call -- unlike
    `run_command`, which `.wait()`s before returning, so a daemon-hygiene defect here is a defect
    `run_command` structurally cannot have. Two consequences of that difference, both fixed here,
    named as one class (ADR-0000 Rule 2(a)'s closure statement):

      THE INVARIANT: a child this function starts and does not wait for must never hold, and
      must never be able to fill, a file descriptor this process's own controlling terminal or
      an unread pipe depends on.

      THE QUANTIFICATION UNIVERSE (checked outward, ADR-0000's 2026-07-02 amendment): the two
      axes are stdin (which fd the child inherits) and stdout/stderr (where the child's output
      goes and whether anything drains it). Sibling surface check -- `run_command` (same module,
      the other Popen site) already gets stdin right (`PIPE if stdin_text is not None else
      DEVNULL`) and its stdout is safe from the blocking hazard because it drains `proc.stdout`
      in a loop before `.wait()`; `write_file` never Popens at all. Every other `subprocess.*`
      call site in this package (`probes.py`, `principals_authority.py`, `pghba.py`,
      `signed_genesis.py`, `screens.py`'s `app.py`-level `subprocess.TimeoutExpired` handling)
      uses `subprocess.run(...)`, which always waits for the child before returning -- none of
      them leaves a design-outliving process, so none of them can reproduce either half of this
      hazard. `start_background` is the ONLY choke point in `tools/setup_tui/` that starts a
      process meant to outlive the call (verified by grep over `Popen` and `subprocess.` calls
      across the package, 2026-07-21) -- the class is foreclosed here in full, not partially.

      (1) STDIN: not setting `stdin` at all defaults to fd 0 inherited verbatim from THIS
      process -- normally the operator's controlling PTY, which Textual has put in raw mode for
      the wizard's own UI. A long-lived daemon holding that fd is why the terminal was never
      given back to the operator after a clean wizard exit (the commission's own field
      observation) -- the terminal stays claimed by a process the operator cannot see or
      interact with. Fixed unconditionally: `stdin=subprocess.DEVNULL`. A background daemon has
      no conversational stdin, ever, so there is no `stdin_text` parameter to conditionally
      honor here the way `run_command` does.

      (2) STDOUT/STDERR: `stdout=subprocess.PIPE` with nothing ever draining it -- verified by
      reading every consumer of the `Popen` this function returns (`commit_executor.py`'s
      `_run_entry`/`on_result`, `screens.py`'s health/meta probes) and confirming none of them
      reads `proc.stdout`; they only ever touch `proc.pid`/`proc.poll()`/`proc.returncode` --
      fills the OS pipe buffer (64KiB on Linux) the moment a chatty daemon writes that much, at
      which point the daemon's own next `write()` blocks forever: a silent hang with no
      exception anywhere, exactly the failure ADR-0002 forbids. A real file can never impose that
      backpressure (a filesystem write can block only briefly, never on an unread reader), so
      output is redirected to a log file instead of a pipe.

      LOCATION (deliberate, not incidental -- and revised once against live evidence, see
      below): `log_path`, if the caller supplies it, is used verbatim -- a caller inside this
      package that already knows the operator-facing right place (e.g. `commit_executor.
      execute`'s own `dest`, the destination world directory a commit is landing in) can hand it
      in without this function guessing. `commit_executor.py` is a sibling module outside this
      fix's file scope, so wiring that specific call site to pass a `dest`-based path is NOT
      done here -- filed residue, reported rather than silently left (ADR-0013 Rule 4). Absent
      an explicit `log_path`, the default is the system temp directory (`tempfile.
      gettempdir()`), NEVER beside the child's own `cwd`: a first draft of this fix defaulted to
      `cwd`, reasoning "the natural place to look, symmetric with how a real daemon logs beside
      itself" -- live-witnessed against this fix's own real-Postgres regression run
      (seen-red/setup-tui-boundary-proc-cleanup, whose driver launches the boundary screen with
      `cwd=REPO_ROOT`, the exact shape `screens.py`'s current sole caller passes today) that
      choice drops an untracked dotfile straight into the git checkout root on every real
      background start -- the opposite of "somewhere the operator can find it," and a fresh
      litter hazard this fix would otherwise have introduced into the very checkout it lives in.
      `cwd` is the CHILD's working directory, chosen for what the child needs to run, not a
      location this function has any warrant to assume is safe or appropriate to write into
      (it could just as easily be read-only). The system temp directory carries no such
      assumption and is never silently dropped either (ADR-0002): a background start with no
      `log_path` still gets a real, locatable, named log file, never `/dev/null`. The name is
      predictable (`.setup-tui-background.<random>.log`, mirroring `write_file`'s own
      recognizable-wreckage naming idiom) so a directory listing identifies it as this
      function's own output at a glance; existing content at an explicitly-supplied `log_path`
      is appended to, never truncated, since a caller-named path may be reused across a
      session's multiple background starts."""
    if echo:
        print(f"$ {quote_argv(argv)}   (background)")
    if dry_run:
        print("  [dry-run: not started]")
        return BackgroundResult(argv=list(argv), proc=None, dry_run=True)
    if log_path is None:
        fd, log_path = tempfile.mkstemp(dir=tempfile.gettempdir(),
                                         prefix=".setup-tui-background.", suffix=".log")
        log_file = os.fdopen(fd, "w")
    else:
        log_file = open(log_path, "a", encoding="utf-8")
    try:
        proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                                 stdout=log_file, stderr=subprocess.STDOUT, text=True)
    finally:
        log_file.close()
    return BackgroundResult(argv=list(argv), proc=proc, dry_run=False, log_path=log_path)


def write_file(path: str, content: str, *, dry_run: bool = False,
               encoding: str = "utf-8") -> bool:
    """The second act-execution choke point (module docstring): writes `content` to `path`
    UNLESS `dry_run`, in which case nothing is written -- the caller is responsible for recording
    the WOULD-DO row (path + a one-line content summary, `summarize_content` below), since the
    checklist item names differ per call site. Returns True iff a real write happened, so a
    caller never has to duplicate the `if dry_run` test to decide its own checklist status.

    ATOMIC by construction (ledger row 1810 finding 1): the naive `open(path, "w")` this used to
    be is truncate-then-write -- a kill between the truncate and the write (or mid-write) leaves
    `path` neither pre- nor post-state, which is exactly the hazard the marker-replace machinery
    sitting on top of this choke point (`durable_decisions.compile_claude_md`,
    `signed_genesis.discharge_keys_readme`) exists to survive. So instead this writes the full
    content to a `NamedTemporaryFile` in `path`'s OWN directory (same filesystem -- `os.replace`
    can raise `OSError` across a mount boundary, which is why `/tmp` or any other directory would
    be wrong here) and only then `os.replace`s it onto `path`, which POSIX guarantees is atomic:
    at every instant `path` is either its old content or its new content in full, never a partial
    write, no matter when the process dies. A death between the temp-write and the replace (or a
    `replace` itself failing) leaves `path` untouched and an orphaned temp file behind -- named
    predictably (`.<basename>.<random>.tmp`, so it is recognizable as this function's own
    wreckage) rather than silently cleaned up, which would erase the forensic trail of what
    almost happened. This mirrors bootstrap/migrate_core.py's own
    `tempfile.NamedTemporaryFile("w", ..., delete=False, encoding=...)` write-then-capture-name
    idiom (`_restore_to_scratch`, `_prepare_apply_files`) -- the difference is that migrate_core
    feeds its temp file to `psql` and unlinks it afterward, where this feeds `os.replace` and,
    on success, there is nothing left to unlink (the rename consumed it).

    KNOWN LIMITATION, stated rather than silently accepted (independent adversarial audit,
    ledger row 1810 residual): if `path` is itself a symlink, `os.replace` retargets the symlink
    NODE (this function's temp file replaces the link, not the file it points at) -- a real
    semantics difference from the old `open(path, "w")`, which wrote THROUGH the link. No current
    call site (`durable_decisions.compile_claude_md`, `signed_genesis.discharge_keys_readme`, the
    two `screens.py` sites) ever writes a symlinked target, so this is not fixed here -- adding
    symlink-resolution machinery no caller needs would be scope this function does not carry
    today. A future caller writing through a symlink is the trigger to revisit this, not before.

    PERMISSIONS (independent adversarial audit, ledger row 1810 residual): `tempfile.
    NamedTemporaryFile` creates its file at mode 0600 regardless of umask (Python's own
    `tempfile` module docstring -- deliberate, for the general case of a SECRET scratch file),
    which is the WRONG default here -- silently narrowing every write target (CLAUDE.md, an
    exported public key, a TOML config) from its previous 0644-ish mode to owner-only the moment
    this rewrite landed would be a regression this fix introduced, not one it was asked to
    permit. So before `os.replace`, this explicitly `os.chmod`s the temp file to: the EXISTING
    target's current mode, if `path` already exists (the common case -- every real call site
    writes into an already-templated file); otherwise the umask-adjusted default `open(path,
    "w")` would have produced (`0o666 & ~umask`, read via the `os.umask` get/restore idiom since
    there is no side-effect-free way to just read it)."""
    if dry_run:
        return False
    directory = os.path.dirname(path) or "."
    try:
        target_mode = stat.S_IMODE(os.stat(path).st_mode)
    except FileNotFoundError:
        umask = os.umask(0)
        os.umask(umask)
        target_mode = 0o666 & ~umask
    with tempfile.NamedTemporaryFile("w", dir=directory, prefix=f".{os.path.basename(path)}.",
                                      suffix=".tmp", delete=False, encoding=encoding) as tf:
        tf.write(content)
        tmp_path = tf.name
    os.chmod(tmp_path, target_mode)
    os.replace(tmp_path, path)
    return True


def summarize_content(content: str, limit: int = 100) -> str:
    """A one-line content summary for a WOULD-DO file-write row (spec: 'the exact file paths it
    would write with a one-line content summary each') -- the first non-blank line, truncated,
    plus a byte count, never the full content (a WOULD-DO table row is a summary, not a dump)."""
    first = next((ln for ln in content.splitlines() if ln.strip()), "")
    if len(first) > limit:
        first = first[:limit] + "..."
    return f"{first!r} ({len(content)} bytes total)"
