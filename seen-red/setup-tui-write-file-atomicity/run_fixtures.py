#!/usr/bin/env python3
"""seen-red/setup-tui-write-file-atomicity/run_fixtures.py -- both-polarity proof of
tools/setup_tui/runner.py's `write_file` atomicity fix (ledger row 1810 finding 1),
census-registered in gates/fixture_census.py.

The hazard (row 1810's own wording): the pre-fix `write_file` was `open(path, "w")` followed by
`f.write(content)` -- truncate-then-write. `open(path, "w")` truncates `path` to zero bytes AT
OPEN TIME, before a single byte of the new content is written, so a process killed anywhere
between that `open()` call and the `write()` call returning leaves `path` in a THIRD state that
is neither its old content nor its new content: empty. This sits directly beneath the
marker-replace machinery (`durable_decisions.compile_claude_md`, `signed_genesis.
discharge_keys_readme`) whose entire purpose is surviving exactly this kind of death mid-flow --
a choke point that is not itself atomic defeats the machinery built on top of it.

RED-BEFORE-GREEN (case 1): loads the OLD `write_file` -- the truncate-then-write implementation
-- straight from git history (commit 7b893f0, the last commit before this fix; `git show
7b893f0:tools/setup_tui/runner.py`, executed in an isolated namespace, never imported as a
module so this fixture never has two `tools.setup_tui.runner` modules alive at once) and proves
it CAN leave a partial (here: truncated-to-empty) file: a fixture-installed `open` wrapper lets
the old function's own `open(path, "w")` truncate the real target file exactly as it always did,
then raises on the very next `write()` call (the "killed mid-write" simulation) -- demonstrating
the pre-fix hazard is real, not hypothetical.

GREEN (cases 2-5): the REAL, current, fixed `runner.write_file` --
  2. a normal call still performs a real write and returns True (the existing contract, unbroken).
  3. a simulated kill BETWEEN the temp-file write and `os.replace` (monkeypatching `os.replace`
     to raise, matching this fixture's own row-1810 "acceptable alternative" witness shape --
     landing a real SIGKILL between temp-write and replace is not reliably reproducible from a
     fixture) leaves the TARGET byte-identical to its pre-write state and orphans exactly one
     predictably-named temp file (`.{basename}.<random>.tmp` in the target's own directory) --
     the temp is deliberately left behind (not silently cleaned up), the forensic trail row
     1810 asked for.
  4. `dry_run=True` still returns False and touches nothing (regression guard: the atomicity
     rewrite must not have disturbed the pre-existing dry-run contract).
  5. the target's file MODE survives a write unchanged (an independent out-of-frame audit of
     this very fix caught: `tempfile.NamedTemporaryFile` creates its file at 0600 regardless of
     umask, so a naive rewrite silently narrows every target -- CLAUDE.md, an exported public
     key, a TOML config -- from its previous, typically world-readable mode to owner-only the
     moment this fix landed. `write_file` now explicitly `os.chmod`s the temp file to the
     EXISTING target's mode before replacing it; this case proves a 0644 target stays 0644
     after a write.

Zero residue: everything happens inside a fixture-owned tempdir, removed in `finally`. No mocks
of the function under test itself -- real `tools.setup_tui.runner.write_file`, only `os.replace`
patched for case 3 (and restored immediately after). Lazy imports banned.

Usage: python3 seen-red/setup-tui-write-file-atomicity/run_fixtures.py
Exit 0 if every case matches; 1 otherwise."""
from __future__ import annotations

import builtins
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO))

from tools.setup_tui import runner  # noqa: E402 -- the REAL, fixed implementation under test

# The last commit before ledger row 1810's atomicity fix -- pinned by SHA (not HEAD, not a
# branch) so this fixture stays reproducible forever regardless of what lands on top of it.
PRE_FIX_COMMIT = "7b893f0"


def load_old_write_file():
    """Fetches `write_file` exactly as it stood in `PRE_FIX_COMMIT` -- the naive
    truncate-then-write version -- via `git show`, executed in an ISOLATED namespace (never
    `sys.modules`-registered, never imported), so this fixture can hold both the old and the
    new implementation live at once without one shadowing the other."""
    src = subprocess.run(
        ["git", "show", f"{PRE_FIX_COMMIT}:tools/setup_tui/runner.py"],
        cwd=str(REPO), capture_output=True, text=True, check=True,
    ).stdout
    ns: dict = {}
    exec(compile(src, f"<{PRE_FIX_COMMIT}:tools/setup_tui/runner.py>", "exec"), ns)
    assert "write_file" in ns, (
        f"case RED setup: {PRE_FIX_COMMIT}:tools/setup_tui/runner.py has no write_file -- wrong "
        f"commit pinned?")
    return ns["write_file"]


def main() -> int:
    scratch = tempfile.mkdtemp(prefix="setup-tui-write-file-atomicity-")
    try:
        target = os.path.join(scratch, "target.txt")
        PRE_STATE = "PRE-STATE-CONTENT\n"

        # =========================== case RED: the OLD implementation ===========================
        with open(target, "w", encoding="utf-8") as f:
            f.write(PRE_STATE)
        old_write_file = load_old_write_file()

        real_open = builtins.open

        def crashing_open(path, mode="r", *a, **kw):
            fh = real_open(path, mode, *a, **kw)
            if os.path.abspath(str(path)) == os.path.abspath(target) and "w" in mode:
                def crashing_write(_data):
                    raise OSError("simulated kill mid-write (case RED)")
                fh.write = crashing_write
            return fh

        builtins.open = crashing_open
        try:
            try:
                old_write_file(target, "NEW-CONTENT-THAT-MUST-NOT-PARTIALLY-LAND\n",
                                dry_run=False)
                raise AssertionError(
                    "case RED: expected the injected mid-write exception to propagate out of "
                    "the OLD write_file -- it was silently swallowed")
            except OSError:
                pass
        finally:
            builtins.open = real_open

        with open(target, encoding="utf-8") as f:
            after_old = f.read()
        assert after_old == "", (
            f"case RED: the OLD (pre-fix, {PRE_FIX_COMMIT}) truncate-then-write write_file must "
            f"leave the target file EMPTY (truncated by open(mode='w') before the crashing "
            f"write ever ran) -- neither the pre-write content nor the new content -- got "
            f"{after_old!r}. (If this now passes without emptying the file, the pinned commit "
            f"no longer represents the truncate-then-write hazard this fixture demonstrates.)")
        print(f"case RED ok: the OLD write_file ({PRE_FIX_COMMIT}) left {target!r} truncated to "
              f"EMPTY (neither pre- nor post-state) after a mid-write kill -- the hazard row "
              f"1810 finding 1 names is real, not hypothetical")

        # ============================ case GREEN 1: normal real write ============================
        with open(target, "w", encoding="utf-8") as f:
            f.write(PRE_STATE)
        ok = runner.write_file(target, "GREEN-CONTENT\n", dry_run=False)
        assert ok is True, f"case GREEN 1: expected write_file to return True, got {ok!r}"
        with open(target, encoding="utf-8") as f:
            after_green1 = f.read()
        assert after_green1 == "GREEN-CONTENT\n", (
            f"case GREEN 1: expected the real new content to land, got {after_green1!r}")
        print("case GREEN 1 ok: a normal write_file call still performs a real write and "
              "returns True -- the pre-existing contract is unbroken")

        # ================ case GREEN 2: kill between temp-write and os.replace =================
        with open(target, "w", encoding="utf-8") as f:
            f.write(PRE_STATE)
        before_entries = set(os.listdir(scratch))

        real_replace = os.replace

        def raising_replace(_src, _dst):
            raise OSError("simulated kill between temp-write and os.replace (case GREEN 2)")

        runner.os.replace = raising_replace
        try:
            try:
                runner.write_file(target, "SHOULD-NEVER-LAND\n", dry_run=False)
                raise AssertionError(
                    "case GREEN 2: expected the injected os.replace failure to propagate out of "
                    "write_file -- it was silently swallowed")
            except OSError:
                pass
        finally:
            runner.os.replace = real_replace

        with open(target, encoding="utf-8") as f:
            after_green2 = f.read()
        assert after_green2 == PRE_STATE, (
            f"case GREEN 2: a simulated kill between the temp-file write and os.replace must "
            f"leave the TARGET byte-identical to its pre-write state -- expected {PRE_STATE!r}, "
            f"got {after_green2!r}")

        new_entries = set(os.listdir(scratch)) - before_entries
        assert len(new_entries) == 1, (
            f"case GREEN 2: expected exactly one orphaned temp file after the simulated kill, "
            f"got {len(new_entries)}: {sorted(new_entries)}")
        orphan = next(iter(new_entries))
        basename = os.path.basename(target)
        assert orphan.startswith(f".{basename}.") and orphan.endswith(".tmp"), (
            f"case GREEN 2: the orphaned temp file's name is not the predictable "
            f".{{basename}}.<random>.tmp shape write_file's own docstring promises -- got "
            f"{orphan!r}")
        print(f"case GREEN 2 ok: a simulated kill between the temp-file write and os.replace "
              f"left {target!r} byte-identical to its pre-write state and orphaned exactly one "
              f"predictably-named temp file ({orphan!r}) rather than silently cleaning it up")

        # ============================ case GREEN 3: dry_run untouched ============================
        with open(target, "w", encoding="utf-8") as f:
            f.write(PRE_STATE)
        before_entries_3 = set(os.listdir(scratch))
        ok3 = runner.write_file(target, "SHOULD-NEVER-LAND-EITHER\n", dry_run=True)
        assert ok3 is False, f"case GREEN 3: expected dry_run to return False, got {ok3!r}"
        with open(target, encoding="utf-8") as f:
            after_green3 = f.read()
        assert after_green3 == PRE_STATE, (
            f"case GREEN 3: dry_run=True must touch nothing -- expected {PRE_STATE!r}, got "
            f"{after_green3!r}")
        assert set(os.listdir(scratch)) == before_entries_3, (
            "case GREEN 3: dry_run=True must not even create a temp file")
        print("case GREEN 3 ok: dry_run=True still returns False and touches nothing -- the "
              "atomicity rewrite left the dry-run contract unchanged")

        # ================== case GREEN 4: target mode survives a write unchanged ==================
        with open(target, "w", encoding="utf-8") as f:
            f.write(PRE_STATE)
        os.chmod(target, 0o644)
        runner.write_file(target, "MODE-CHECK-CONTENT\n", dry_run=False)
        after_mode = stat.S_IMODE(os.stat(target).st_mode)
        assert after_mode == 0o644, (
            f"case GREEN 4: a 0644 target must stay 0644 after a write_file call -- "
            f"NamedTemporaryFile defaults to 0600 regardless of umask, so a write_file that "
            f"does not explicitly chmod the temp file to the target's existing mode before "
            f"os.replace silently narrows every write target's permissions -- got "
            f"{oct(after_mode)}")
        print(f"case GREEN 4 ok: a target chmod'd to 0644 before the write stays 0644 after it "
              f"(NamedTemporaryFile's own 0600 default does not leak through)")

        print("ALL CASES OK -- tools/setup_tui/runner.py write_file: pre-fix truncate-then-write "
              "hazard demonstrated red, then the fixed temp-write+os.replace implementation "
              "proven atomic under a simulated kill between temp-write and replace, plus normal, "
              "dry-run, and file-mode contracts unbroken")
        return 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
