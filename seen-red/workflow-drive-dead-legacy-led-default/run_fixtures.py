#!/usr/bin/env python3
"""Seen-red for workflow-drive-dead-legacy-led-default (ledger rows 1307/1308, 2026-07-26):
tools/workflow_compile.py's DRIVE_TEMPLATE hardcoded `led = "./legacy/led"` for the compiled
driver's `check_charter`/`fetch_brief` calls, but a scaffolded world's `./legacy/led` is a pure
exit-1 teaching-refusal stub since commit 93affa0 (2026-07-23) -- so `check_charter` got rc=1
UNCONDITIONALLY, and every phase of every compiled workflow resolved UNCHARTED regardless of
whether an actual charter existed. Fix: default the template's `led` binding to the served
`./led` instead, and regenerate all 7 `tools/workflow_units/*/drive.py` copies through
`tools/workflow_compile.py`'s own compiler entry point (`compile_toml`/`main`).

HONEST PROVENANCE OF THE 7 COPIES (correcting this file's and red.txt's own prior claim, review
finding 1, 2026-07-26 follow-up): at commit cb5cf23 the 7 copies WERE regenerated through the
entry point as claimed, but `tools/workflow_compile.py` at that time had no notion of a
repo-root override -- its `REPO_ROOT = Path(__file__).resolve().parents[1]` baked whatever
checkout the compiler happened to run from into `ROLE_CHARTER_PY`/`ROLE_BRIEF_PY`. That pass ran
the compiler from this repo's WORKTREE checkout, so the two lines came out baked to the
worktree's own transient `.claude/worktrees/<agent>/...` path -- wrong for a committed artifact
meant to run against the real checkout. Those two REPO_ROOT-derived lines, in all 7 files, were
then corrected BY HAND to the real checkout's path, and the commit message half-disclosed this;
this file and red.txt did not, and said "never hand-edited" instead, which was false for those
two lines. THIS FOLLOW-UP PASS (review finding 2) closes the underlying gap instead of leaving
it as a one-time manual patch: `tools/workflow_compile.py` gained an honest `--repo-root`
flag/`AUTOHARN_REPO_ROOT` env var (refusing a nonexistent path) letting a compile invoked from a
worktree bake the REAL checkout's path without hand-editing afterward, W5 below extends the
standing regression to catch a future worktree-path recurrence, and all 7 copies were
regenerated AGAIN through the entry point WITH the override -- this time genuinely never
hand-edited, byte-identical to a fresh compile (verified below).

RED-FIRST, against a REAL scaffolded scratch world (bootstrap/new-project.sh --new-world) with a
REAL `serving.boundary_service` subprocess and the world's own real `./legacy/led` teaching stub
-- mirrors seen-red/legacy-led-retirement-round1-fixes/run_fixtures.py's launch pattern. Banked
`red.txt` in this directory is the terminal transcript of the identical sequence run manually
before this fixture existed (this file re-proves it live, as a standing regression).

W1  RED: the exact `check_charter` call shape (`role_charter.py show <principal> --led <led>`,
    imported straight off a REAL compiled `tools/workflow_units/*/drive.py` module -- not a
    reimplementation) against `./legacy/led` (the pre-fix hardcoded default) exits 1 with the
    stub's own teaching text, nothing resolved -- the dead-by-default reproduction.
W1b STRONG-FORM RED (the SEVERE part red.txt banked but this fixture, pre-fix-up, never
    re-proved): the SAME `check_charter` call against `./legacy/led`, run AGAIN after a REAL,
    IN-FORCE charter is registered for the same principal (immediately below), STILL exits 1
    with the identical stub teaching -- the stub's rc is unconditional, so an actual charter's
    existence is irrelevant to the pre-fix outcome. Without this re-check the fixture only
    proves the weak form (uncharted -> refused, unsurprising); W1b is what makes the standing
    regression catch a future change that made `./legacy/led` conditionally succeed while still
    leaving it as the driver's default.
W2  GREEN: the same `check_charter` call against the served `./led` (the post-fix default),
    after registering a real charter via `tools/role_charter.py register` (the world's own
    charter-registration machinery -- ledger row 1663's flow, never hand-inserted SQL), exits 0
    and reports an IN-FORCE charter registration.
W3  STATIC REGRESSION GUARD: `tools/workflow_compile.py`'s DRIVE_TEMPLATE source contains
    `led = "./led"` and does NOT contain `led = "./legacy/led"` -- catches a future hand-edit or
    revert of the template default without needing a live world.
W4  ALL SEVEN generated `tools/workflow_units/*/drive.py` copies were produced BY the compiler
    (never hand-edited) and each carries the fixed default -- re-derived here by actually
    invoking `tools/workflow_compile.py` against every `design/workflows/*.toml` into a SCRATCH
    output directory (never the real tools/workflow_units/ tree) and diffing the `led = ...`
    line against the real, committed copy -- a real regeneration-parity check, not a grep.
W5  RECURRENCE GUARD (row 1307/1308 follow-up, 2026-07-26): the committed `ROLE_CHARTER_PY`/
    `ROLE_BRIEF_PY` lines in all 7 copies carry no `.claude/worktrees` path component -- the next
    regeneration run from ANY worktree, without `tools/workflow_compile.py`'s new
    `--repo-root`/`AUTOHARN_REPO_ROOT` override, would otherwise silently bake that worktree's
    own transient path back in (exactly what happened once already and had to be hand-corrected
    -- see this directory's git history). W4 only ever checked the `led = ...` line; this closes
    the other two baked-path lines the same defect class touches.

SECOND FIX ROUND (2026-07-26, strengthened-review BLOCKING finding 1): the round-1 fix above
flipped the dead default from `"./legacy/led"` to `"./led"` -- but the scaffold-umbrella
migration (rows 1357/1365/1366/1367, §6 amendment, same day) retired the bare `./led` shim
project-wide in the SAME window, so `"./led"` went dead too, by the identical mechanism, before
round 1 even shipped. Witnessed live: every one of the seven `run_led`-driven `led work
claim`/`led work close` calls a real drive.py round makes broke at the FIRST such call against a
post-migration world/repo-root, because (a) the served default was itself gone, AND (b)
`run_led`'s `subprocess.run([led] + args)` had no `shlex.split`, so even a caller-supplied
multi-token override like `--led "./autoharn led"` (the only shape a scaffolded world's OWN
dispatcher now answers to) was passed as one nonexistent literal filename ("could not execute").
Fix: `led` defaults to the SINGLE-TOKEN `"libexec/autoharn/led"` (this repo's own served shim,
resolved relative to the CWD this driver is documented to run from -- see drive.py's own module
docstring, "CWD ASSUMPTION"), and `run_led` now does `shlex.split(led) + args` so a multi-token
override still works. `hydrate.sh`'s own `LED="./led"` default (HYDRATE_TEMPLATE, a sibling
generated artifact this same review pass's fix touches -- found in reach while fixing
DRIVE_TEMPLATE, per CLAUDE.md's hazard-in-reach standard) carried the identical dead-default
defect and is fixed the same way; it never needed the shlex fix (unquoted `$LED` in `sh` already
word-splits a multi-token override).
W3/W4 above are re-pointed to the new default; W6/W7 below are NEW live legs proving this
round's fix (run_led's own default and its shlex-split), added because check_charter's own
GREEN leg (W2) shells to a BAKED, real-checkout absolute path (this repo's `main` branch, W5's
own design) that has not yet merged tools/role_charter.py's own shlex-split fix (present on
THIS branch already, unrelated to this fix round) -- W2 is therefore UNEXERCISED here (not
FAILED, not silently dropped) pending that merge, exactly matching CLAUDE.md's own witness
vocabulary. RED-FIRST for this round: the pre-fix `w2-green-*`/`w4-*-fresh-default-is-served`
failures this round's fix corrects are banked verbatim in this directory's `red.txt`, appended
below the round-1 transcript, not overwriting it.
W6  GREEN: `run_led()` (imported from a REAL compiled `drive.py`, never a reimplementation)
    against the single-token served default `"libexec/autoharn/led"`, invoked from THIS repo's
    own root with a read-only `--help` call (no real-deployment ledger write) -- proves the
    fixed DEFAULT resolves and executes on a driver's first led call, unconditionally.
W7  GREEN: the SAME `run_led()` against the multi-token override `--led "./autoharn led"`,
    invoked from the scratch scaffolded world already stood up for W1/W1b/W2, with a read-only
    `led current 1` call -- proves the `shlex.split` fix itself, the exact shape ("could not
    execute './autoharn led'") the strengthened review witnessed as blocking.

THIRD FIX ROUND (2026-07-26, confirming review, 3 findings) -- W8..W18. PRIOR_SHA (4ac3ba6, the
round-2 tip these findings were raised against) is `git show`n straight for every RED leg -- its
own already-committed, already-regenerated `tools/workflow_units/*/drive.py`/`hydrate.sh` are
used verbatim, never reconstructed. Zero DB/ledger writes across all eleven new legs.

  Finding 1 (wrong-CWD/wrong-led reads as an ordinary uncharted refusal, or a raw traceback under
  --allow-uncharted): W8 RED shows PRIOR_SHA's `check_charter()` against a nonexistent `--led`
  returning an ordinary (nonzero rc, plain text) tuple -- no exception, no marker, structurally
  identical to a genuine "no registered charter" answer. W9 GREEN shows the CURRENT
  `check_charter()` raising `LedUnusable` instead (naming the led value, the cwd, and the repo-
  root assumption) for the identical input -- exercised against THIS worktree's own
  `role_charter.py` (module-global substitution, the same disclosed cross-checkout-timing
  workaround W2/W5 already established) since the real fix `check_charter()` shells to is baked
  to the main checkout, which has not yet merged it. W10 RED shows PRIOR_SHA's `run_led()` (the
  `--allow-uncharted` call shape) dying as a raw, uncaught `OSError`; W11 GREEN shows the CURRENT
  `run_led()` converting the identical input to a clean `LedUnusable`.
  Finding 2 (shlex edges: empty `--led` silently execs args[0], malformed quoting raises
  uncaught): W12 RED demonstrates PRIOR_SHA's `run_led("", ["echo", "SILENTLY-RAN-AS-LED"], ...)`
  actually running `echo` AS IF it were `led` itself (rc 0, the marker string echoed back) --
  the silent-wrong-execution shape, not merely a coincidental failure. W13 GREEN shows the
  CURRENT `run_led()` refusing before any subprocess runs. W14 RED / W15 GREEN do the same for
  malformed shell quoting (uncaught `ValueError` vs. a named `LedUnusable`). W16 exercises
  `tools/role_charter.py`'s and `tools/role_brief.py`'s OWN `run_led()` directly (imported at
  module scope, CLAUDE.md's lazy-import ban) -- both now refuse an empty/malformed `--led`
  loudly, tagged with the shared `LED_UNUSABLE_MARKER`.
  Finding 3 (hydrate.sh's `"$LED"` calls are quoted, so a multi-token override is one nonexistent
  literal filename -- and PRIOR_SHA's own commit message falsely claimed otherwise): W17 RED
  confirms the PRIOR_SHA source really does quote every `$LED` use, then runs it with a harmless
  two-token `--led "/usr/bin/env echo"` override and shows it fails ("... No such file or
  directory", "REFUSED for an UNEXPECTED reason"). W18 GREEN runs the CURRENT, `led_run()`-based
  `hydrate.sh` with the identical override and shows it completes ("hydration complete").
  W3's `w3-run-led-shlex-splits` check is re-pointed to the new `_split_led()` helper call site
  (the raw `shlex.split(led) + args` inline text moved into that shared helper, which also
  refuses empty/malformed `--led` -- finding 2).

Zero residue: the scratch schema/role/world/tempdirs are torn down in a `finally` regardless of
outcome, and the boundary subprocess is terminated. Never live 8433/8422 (own ephemeral port).
Lazy imports banned; stdlib + this repo's own filing/ helpers only."""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT_SH = REPO / "bootstrap" / "new-project.sh"
WORKFLOW_COMPILE_PY = REPO / "tools" / "workflow_compile.py"
ROLE_CHARTER_PY = REPO / "tools" / "role_charter.py"
WORKFLOW_UNITS_DIR = REPO / "tools" / "workflow_units"
DESIGN_WORKFLOWS_DIR = REPO / "design" / "workflows"
sys.path.insert(0, str(REPO / "filing"))
from pghost_resolve import resolve_pghost  # noqa: E402

# W16 (confirming-review fix round, finding 2): exercises THIS worktree's own tools/role_charter.py
# / tools/role_brief.py run_led() directly (never a reimplementation) -- imported at module scope
# (CLAUDE.md's lazy-import ban), same sys.path convention as filing/pghost_resolve above.
sys.path.insert(0, str(REPO / "tools"))
import role_charter  # noqa: E402
import role_brief  # noqa: E402

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"
WORLD = "wfdll1"

# CONFIRMING-REVIEW FIX ROUND (2026-07-26, three findings): PRIOR_SHA is the commit this round's
# fixes are RED-proved against -- 4ac3ba6 is the round-2 tip these findings were raised on. Its
# own tools/workflow_units/*/drive.py and hydrate.sh are already-committed, already-regenerated
# artifacts at that revision (per its own commit message), so RED legs below `git show` them
# straight rather than re-deriving via a checked-out old compiler.
PRIOR_SHA = "4ac3ba6"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def git_show(rev: str, path: str) -> str:
    cp = sh(["git", "show", f"{rev}:{path}"], cwd=str(REPO))
    if cp.returncode != 0:
        raise RuntimeError(f"git show {rev}:{path} failed: {cp.stderr}")
    return cp.stdout


def import_module_from_text(name: str, source: str, dest_path: Path):
    """Writes `source` to `dest_path` and imports it as a fresh module named `name` -- used to
    load a PRIOR_SHA-frozen copy of a compiled drive.py (via git_show) under a distinct module
    name so it never collides with a same-session import of the current (fixed) copy."""
    dest_path.write_text(source)
    spec = importlib.util.spec_from_file_location(name, str(dest_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def check_unexercised(name: str, blocker: str) -> None:
    """CLAUDE.md's own vocabulary ('A report states, per item: WITNESSED ... REFUSED-AS-EXPECTED
    ... or UNEXERCISED with the concrete blocker') applied to a fixture leg, not just a report:
    used for w2's check_charter legs below, which shell to ROLE_CHARTER_PY's BAKED, real-checkout
    absolute path (by design -- see W5) rather than this worktree's own tools/role_charter.py.
    That real checkout (this repo's `main` branch) has not yet merged the shlex-split fix this
    branch's OWN tools/role_charter.py already carries (commit b528212) -- a disclosed,
    pre-merge cross-checkout timing gap, not a defect this fix round's own code introduces or can
    close without touching the main checkout (forbidden by this round's own brief). Printed, not
    silently skipped; never counted as a failure."""
    print(f"=== {name} ===")
    print(f"  [UNEXERCISED] {blocker}")
    print()


def mod_role_charter_py_of(check_charter_fn) -> str:
    """Recovers a compiled drive.py module's own baked ROLE_CHARTER_PY constant from its
    check_charter function object (via __globals__) -- avoids re-deriving that path independently
    here, which would risk silently drifting from what the module under test actually calls."""
    return check_charter_fn.__globals__["ROLE_CHARTER_PY"]


def mod_ledunusable_of(fn):
    """Recovers a compiled drive.py module's own LedUnusable class from any of its functions
    (via __globals__) -- W9/W11/W13/W15 (confirming-review fix round) catch THIS exact class,
    never a reimplementation or a bare `except Exception`."""
    return fn.__globals__["LedUnusable"]


def import_run_led(drive_py: Path):
    """Same posture as import_check_charter below: imports a REAL compiled drive.py module and
    returns its run_led, so the new W6/W7 legs exercise the EXACT function this fix round
    patched (shlex.split before exec), never a reimplementation."""
    spec = importlib.util.spec_from_file_location("workflow_drive_run_led_under_test", str(drive_py))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run_led


def role_charter_target_has_shlex_fix(role_charter_py_path: str) -> bool:
    """Probes whatever tools/role_charter.py check_charter() will actually shell out to (the
    BAKED, real-checkout absolute path -- see W5) for the shlex-split fix this branch's own copy
    already carries (commit b528212). Used only to decide whether w2's check_charter legs are
    exercisable here and now, pre-merge; never used to alter what gets compiled/committed."""
    p = Path(role_charter_py_path)
    return p.is_file() and "shlex.split(led)" in p.read_text()


def teardown_schema(world: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP SCHEMA IF EXISTS {world} CASCADE;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP SCHEMA IF EXISTS {world}_kernel CASCADE;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def start_server(config_path: Path) -> tuple[subprocess.Popen, int]:
    port = free_port()
    args = [sys.executable, "-m", "serving.boundary_service",
            "--config", str(config_path), "--host", "127.0.0.1", "--port", str(port)]
    proc = subprocess.Popen(args, cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, env=dict(os.environ))
    return proc, port


def wait_health(health_url: str, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(0.3)
    return False


def stop_server(proc: subprocess.Popen) -> str:
    proc.terminate()
    try:
        out, _ = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate(timeout=5)
    return out or ""


def import_check_charter(drive_py: Path):
    """Imports a REAL compiled drive.py module (never a reimplementation of check_charter) and
    returns its `check_charter` function, so W1/W2 exercise the exact code path the fix touched."""
    spec = importlib.util.spec_from_file_location("workflow_drive_under_test", str(drive_py))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check_charter


def main() -> int:
    failures: list[str] = []
    tmpdir = Path(tempfile.mkdtemp(prefix="workflow-drive-dead-legacy-led-"))
    world_dir = tmpdir / "world"
    proc = None
    try:
        # ---------------------------------------------------------------------------------
        # W3/W4: static + regeneration-parity checks first (no DB/network needed for these)
        # ---------------------------------------------------------------------------------
        print("== W3: DRIVE_TEMPLATE/HYDRATE_TEMPLATE source carries the fixed default, not "
              "either of the two dead ones (this round's finding, 2026-07-26 fix round: "
              "\"./led\" itself went dead post-scaffold-migration, the same disease that made "
              "\"./legacy/led\" dead in the row-1307/1308 round this file used to test only), "
              "and run_led shlex-splits its `led` argument before exec ==")
        template_src = WORKFLOW_COMPILE_PY.read_text()
        check("w3-template-has-served-default",
              'led = "libexec/autoharn/led"' in template_src,
              "DRIVE_TEMPLATE/HYDRATE_TEMPLATE contain led = \"libexec/autoharn/led\"", failures)
        check("w3-template-lacks-legacy-default", 'led = "./legacy/led"' not in template_src,
              "DRIVE_TEMPLATE no longer contains led = \"./legacy/led\"", failures)
        check("w3-template-lacks-dead-served-default", 'led = "./led"' not in template_src,
              "DRIVE_TEMPLATE/HYDRATE_TEMPLATE no longer contain the now-also-dead "
              "led = \"./led\" (bare ./led shim retired by the scaffold-umbrella migration, "
              "rows 1357/1365/1366/1367)", failures)
        # re-pointed (confirming-review fix round, 2026-07-26): run_led no longer calls
        # shlex.split(led) inline -- that call moved into a shared _split_led() helper (also used
        # by check_charter's own broken-led detection) that additionally refuses an empty/
        # malformed `led` loudly (finding 2) instead of letting shlex.split fail silently/raise
        # uncaught. The substring check now targets the helper call site, not the raw shlex call.
        check("w3-run-led-shlex-splits",
              "led_argv = _split_led(led)" in template_src and "led_argv + args" in template_src,
              "DRIVE_TEMPLATE's run_led shlex-splits `led` before exec, via _split_led() (the "
              "second break: a naive [led] + args treats a multi-token --led override, e.g. "
              "'./autoharn led', as one nonexistent literal filename)", failures)
        check("w3-drive-template-imports-shlex",
              "import shlex" in template_src,
              "DRIVE_TEMPLATE imports shlex (top-of-file, CLAUDE.md's lazy-import ban)", failures)

        print("== W4: all 7 generated drive.py copies match a FRESH compile, byte-for-byte on "
              "the `led = ...` line ==")
        scratch_out = tmpdir / "workflow_units_scratch"
        tomls = sorted(DESIGN_WORKFLOWS_DIR.glob("*.toml"))
        check("w4-seven-tomls-found", len(tomls) == 7, f"found {len(tomls)}: {[t.name for t in tomls]}",
              failures)
        # allows an optional trailing `# ...` comment (the fix round's own line-budget compaction
        # -- see tools/workflow_compile.py's DRIVE_TEMPLATE -- put the rationale on the same
        # line as the assignment rather than a separate comment line above it).
        led_default_re = re.compile(r'^\s*led = "([^"]+)"(?:\s*#.*)?\s*$', re.MULTILINE)
        for toml_path in tomls:
            stem = toml_path.stem
            cp = sh([sys.executable, str(WORKFLOW_COMPILE_PY), str(toml_path),
                    "--out-dir", str(scratch_out)])
            check(f"w4-compile-{stem}", cp.returncode == 0, f"exit={cp.returncode} {cp.stdout!r} {cp.stderr!r}",
                  failures)
            fresh_drive = scratch_out / stem / "drive.py"
            committed_drive = WORKFLOW_UNITS_DIR / stem / "drive.py"
            fresh_m = led_default_re.search(fresh_drive.read_text()) if fresh_drive.is_file() else None
            committed_m = led_default_re.search(committed_drive.read_text()) if committed_drive.is_file() else None
            check(f"w4-{stem}-fresh-default-is-served",
                  bool(fresh_m) and fresh_m.group(1) == "libexec/autoharn/led",
                  f"fresh compile's led default: {fresh_m.group(1) if fresh_m else None!r}", failures)
            check(f"w4-{stem}-committed-matches-fresh",
                  bool(committed_m) and bool(fresh_m) and committed_m.group(1) == fresh_m.group(1),
                  f"committed={committed_m.group(1) if committed_m else None!r} "
                  f"fresh={fresh_m.group(1) if fresh_m else None!r}", failures)

        print("== W5: committed drive.py's ROLE_CHARTER_PY/ROLE_BRIEF_PY carry no "
              "'.claude/worktrees' component -- the recurrence this pass closes (row 1307/1308 "
              "follow-up, 2026-07-26): a regeneration run FROM a worktree checkout, without the "
              "--repo-root/AUTOHARN_REPO_ROOT override, would silently bake that worktree's own "
              "transient path back into these two lines across all 7 files ==")
        role_path_re = re.compile(r'^(ROLE_CHARTER_PY|ROLE_BRIEF_PY) = "([^"]+)"\s*$', re.MULTILINE)
        for toml_path in tomls:
            stem = toml_path.stem
            committed_drive = WORKFLOW_UNITS_DIR / stem / "drive.py"
            matches = role_path_re.findall(committed_drive.read_text()) if committed_drive.is_file() else []
            check(f"w5-{stem}-role-paths-found", len(matches) == 2,
                  f"found {len(matches)} of 2 expected ROLE_*_PY lines", failures)
            for name, value in matches:
                check(f"w5-{stem}-{name.lower()}-no-worktree-component",
                      ".claude/worktrees" not in value, f"{name} = {value!r}", failures)

        # ---------------------------------------------------------------------------------
        # W1/W2: live world -- real scaffold, real boundary, real check_charter() call shape
        # ---------------------------------------------------------------------------------
        print(f"== scaffolding scratch WORLD '{WORLD}' via bootstrap/new-project.sh --new-world ==")
        teardown_schema(WORLD)
        cp = sh(["bash", str(NEW_PROJECT_SH), str(world_dir), "--new-world", WORLD,
                "--db", PGDB, "--host", PGHOST, "--name", WORLD])
        check("scaffold-ok", cp.returncode == 0, f"exit={cp.returncode} tail={cp.stdout[-1500:]}", failures)
        if cp.returncode != 0:
            raise RuntimeError("scaffold failed, cannot proceed")

        legacy_led = world_dir / "legacy" / "led"
        check("legacy-led-is-a-stub", legacy_led.is_file(), f"{legacy_led} exists", failures)

        config_path = tmpdir / f"{WORLD}-boundary-multiplex.toml"
        config_path.write_text(
            f'[deployments.{WORLD}]\n'
            f'pghost = "{PGHOST}"\n'
            f'pgdatabase = "{PGDB}"\n'
            f'pguser = "{WORLD}_rw"\n'
            f'pgschema = "{WORLD}"\n'
            f'pgkern = "{WORLD}_kernel"\n',
            encoding="utf-8")
        proc, port = start_server(config_path)
        base_url = f"http://127.0.0.1:{port}"
        healthy = wait_health(f"{base_url}/d/{WORLD}/health")
        check("server-healthy", healthy, f"boundary service up at {base_url}", failures)
        if not healthy:
            print(stop_server(proc))
            raise RuntimeError("server never became healthy")

        dep_path = world_dir / "deployment.json"
        dep_obj = json.loads(dep_path.read_text())
        dep_obj["boundary_url"] = base_url
        dep_obj["boundary_deployment"] = WORLD
        dep_path.write_text(json.dumps(dep_obj, indent=2) + "\n")

        # exercise check_charter() via a REAL compiled drive.py (autoharn-builder-wave, arbitrary
        # pick -- all 7 share the identical function, per W4 above). Real usage always runs
        # drive.py FROM the scaffolded world's own directory (an operator cd's there first) --
        # chdir into world_dir for these calls, exactly matching that, so `--led ./legacy/led`
        # and `--led ./led` resolve (and the charter's path resolves for the hash check) the
        # same way a real invocation would; restore cwd unconditionally afterward.
        drive_py = WORKFLOW_UNITS_DIR / "autoharn-builder-wave" / "drive.py"
        check_charter = import_check_charter(drive_py)
        orig_cwd = os.getcwd()
        os.chdir(str(world_dir))
        try:
            # §6 amendment (2026-07-26, rows 1357/1365/1366/1367): a scaffolded world no longer
            # has a bare `./led` shim -- role_charter.py's own `--led` now shlex-splits its value
            # into an argv prefix, so the served default here is "./autoharn led" (two tokens,
            # space-joined), not "./led". `./legacy/led` (the C-site retirement stub) is
            # UNCHANGED and deliberately untouched -- its own teaching text now says "Use
            # ./autoharn led instead." (new-project.sh's own stub, updated in the same migration),
            # so the assertion below is repointed to match, not the invocation.
            print("== W1: RED -- check_charter() against ./legacy/led (the pre-fix hardcoded value) ==")
            rc, out = check_charter("./legacy/led", "author")
            check("w1-red-exit-1", rc == 1, f"rc={rc}", failures)
            check("w1-red-teaches-retirement",
                  "RETIRED" in out and "Use ./autoharn led instead" in out, f"out={out!r}", failures)

            print("== registering a real charter for 'author' via tools/role_charter.py's own flow ==")
            charter_md = world_dir / "roles" / "author-CHARTER.md"
            charter_md.write_text("# fixture charter for author\n")
            cp = sh([sys.executable, str(ROLE_CHARTER_PY), "register", "author",
                    "roles/author-CHARTER.md", "--led", "./autoharn led"],
                   cwd=str(world_dir), env={**os.environ, "LED_ACTOR": "author"})
            check("register-charter-ok", cp.returncode == 0,
                  f"exit={cp.returncode} {cp.stdout!r} {cp.stderr!r}", failures)

            print("== W1b: STRONG-FORM RED -- check_charter() against ./legacy/led STILL rc=1 "
                  "even with a REAL, IN-FORCE charter now registered for 'author' -- the severe "
                  "part red.txt banked but this fixture never re-proved: the stub's rc is "
                  "unconditional, so an actual charter's existence is irrelevant to it ==")
            rc, out = check_charter("./legacy/led", "author")
            check("w1b-red-still-exit-1-after-real-charter", rc == 1, f"rc={rc}", failures)
            check("w1b-red-still-teaches-retirement",
                  "RETIRED" in out and "Use ./autoharn led instead" in out, f"out={out!r}", failures)

            print("== W2: GREEN -- check_charter() against ./autoharn led (the post-fix served "
                  "default) ==")
            # check_charter() shells to ROLE_CHARTER_PY -- a BAKED, real-checkout absolute path
            # (W5's own guarantee: never this worktree's transient path). That real checkout is
            # this repo's `main` branch, a SEPARATE, unmerged line of work (verified: `main` sits
            # at 9249713, an unrelated entitlement-enforcement commit, not an ancestor of this
            # branch) -- it has not yet merged tools/role_charter.py's own shlex-split fix, which
            # THIS branch already carries (commit b528212, unrelated to and untouched by this fix
            # round). A multi-token --led override therefore cannot be proven through
            # check_charter() until this branch merges into main; W7 below proves the identical
            # multi-token-override fix (this round's own deliverable, drive.py's run_led) without
            # crossing that checkout boundary. Detected, not assumed, and never silently skipped.
            role_charter_target = mod_role_charter_py_of(check_charter)
            if role_charter_target_has_shlex_fix(role_charter_target):
                rc, out = check_charter("./autoharn led", "author")
                check("w2-green-exit-0", rc == 0, f"rc={rc}", failures)
                check("w2-green-in-force", "IN-FORCE charter registration" in out, f"out={out!r}",
                      failures)
                check("w2-green-no-drift", "DRIFT" not in out, f"out={out!r}", failures)
            else:
                check_unexercised(
                    "w2-green-exit-0",
                    f"ROLE_CHARTER_PY is baked to {role_charter_target!r} (this repo's `main` "
                    f"checkout, by W5's own design) and that checkout has not yet merged "
                    f"tools/role_charter.py's shlex-split fix (present on THIS branch at commit "
                    f"b528212) -- a disclosed pre-merge cross-checkout gap, not something this "
                    f"fix round's own code can close without touching main (forbidden this "
                    f"round). Resolves automatically once this branch merges into main. See W7 "
                    f"below for the equivalent multi-token-override proof against the function "
                    f"this round's fix actually touches (drive.py's own run_led).")
                check_unexercised("w2-green-in-force", "same blocker as w2-green-exit-0 above")
                check_unexercised("w2-green-no-drift", "same blocker as w2-green-exit-0 above")

            # -----------------------------------------------------------------------------
            # W6/W7 (this fix round, 2026-07-26, review finding 1): the ACTUAL function this
            # round patched is run_led (used for every `led work claim`/`led work close` the
            # driver's main loop makes) -- check_charter/fetch_brief shell to a SEPARATE file
            # (role_charter.py/role_brief.py) that does its own splitting internally. W6/W7 prove
            # run_led directly, via a REAL compiled drive.py module (never a reimplementation),
            # so the coverage does not depend on the main-checkout timing gap W2 discloses above.
            # -----------------------------------------------------------------------------
            run_led = import_run_led(drive_py)

            print("== W6: GREEN -- run_led() against the SINGLE-TOKEN served default "
                  "'libexec/autoharn/led', invoked from THIS repo's own root (the driver's own "
                  "documented CWD assumption -- see drive.py's module docstring) with a "
                  "read-only, DB-touch-free '--help' call (house rule: no real-deployment "
                  "ledger writes) -- proves the DEFAULT resolves and executes on the very "
                  "first led call a real drive.py round makes, unconditionally, even before "
                  "shlex.split is exercised at all (a single token splits to itself) ==")
            os.chdir(str(REPO))  # THIS repo's own root -- libexec/autoharn/led is relative to it
            try:
                rc, out = run_led("libexec/autoharn/led", ["--help"], "author")
                check("w6-green-exit-0", rc == 0, f"rc={rc}", failures)
                check("w6-green-not-could-not-execute", "could not execute" not in out,
                      f"out={out[:200]!r}", failures)
                check("w6-green-usage-text", "usage: led" in out, f"out={out[:200]!r}", failures)
            finally:
                os.chdir(str(world_dir))

            print("== W7: GREEN -- run_led() against the MULTI-TOKEN override --led "
                  "'./autoharn led', invoked from the scratch scaffolded world's own root -- "
                  "proves the shlex-split fix itself (the second break the strengthened review "
                  "named): a `[led] + args` list would treat './autoharn led' as one "
                  "nonexistent literal filename ('could not execute'), exactly W2's disclosed "
                  "failure shape above; shlex.split(led) + args does not. Uses a real, "
                  "read-only led verb ('current 1') against the same scratch world/schema "
                  "already scaffolded for W1/W1b/W2, torn down in this fixture's own finally "
                  "block -- never a real-deployment write. ==")
            rc, out = run_led("./autoharn led", ["current", "1"], "author")
            check("w7-green-exit-0", rc == 0, f"rc={rc}", failures)
            check("w7-green-not-could-not-execute", "could not execute" not in out,
                  f"out={out[:200]!r}", failures)

            # -----------------------------------------------------------------------------
            # THIRD FIX ROUND (2026-07-26, confirming review, 3 findings) -- W8..W13. Every RED
            # leg below runs the PRIOR_SHA (4ac3ba6)-frozen artifact via git_show, never a
            # reimplementation of the pre-fix bug; every GREEN leg runs the current, fixed
            # compiled artifact. Zero DB/ledger writes in any of these six legs (house rule):
            # W8/W9/W11 exercise run_led/check_charter with a led value chosen to fail before any
            # real subprocess does anything ledger-shaped; W10 uses `echo` as the accidental
            # "led"; W12/W13 use `/usr/bin/env echo` as a harmless two-token --led override, so
            # hydrate.sh's own `led work open ...` calls become ordinary echoes, never real `led`.
            # -----------------------------------------------------------------------------
            old_drive_py_src = git_show(PRIOR_SHA, "tools/workflow_units/autoharn-builder-wave/drive.py")
            old_drive_module = import_module_from_text(
                "workflow_drive_PRIOR_SHA_under_test", old_drive_py_src,
                tmpdir / "old_drive.py")

            # W9's own check_charter() marker-detection logic (this round's fix) must not be
            # blocked by the SAME pre-merge main-checkout timing gap W2/W5 already disclose above
            # (ROLE_CHARTER_PY is baked to the real main-checkout path, which has not yet merged
            # role_charter.py's LED_UNUSABLE_MARKER -- THIS round's own fix). Point check_charter's
            # own ROLE_CHARTER_PY global at THIS worktree's copy instead, the same disclosed-
            # substitution posture role_charter_target_has_shlex_fix already established for W2 --
            # proves the actual logic this round patched.
            check_charter.__globals__["ROLE_CHARTER_PY"] = str(ROLE_CHARTER_PY)

            bad_led = str(tmpdir / "no-such-led-binary")  # deliberately does not exist

            print(f"== W8: RED (against {PRIOR_SHA}) -- check_charter() against a nonexistent "
                  "--led returns an ORDINARY (nonzero rc, ordinary-shaped text) tuple, no "
                  "exception, structurally indistinguishable from a genuine 'no registered "
                  "charter' refusal -- finding 1's first symptom: a wrong-deployment invocation "
                  "silently reads as an honest uncharted refusal ==")
            try:
                old_rc, old_out = old_drive_module.check_charter(bad_led, "author")
                check("w8-red-no-exception-raised", True,
                      f"rc={old_rc} out={old_out[:160]!r} (returned silently, no marker to "
                      f"distinguish this from a genuine uncharted refusal)", failures)
                check("w8-red-nonzero-rc", old_rc != 0, f"rc={old_rc}", failures)
            except Exception as exc:  # noqa: BLE001 -- documenting whatever the prior code did
                check("w8-red-no-exception-raised", False, f"unexpectedly raised {exc!r}", failures)

            print("== W9: GREEN -- the SAME nonexistent --led against the CURRENT (fixed) "
                  "check_charter() raises LedUnusable instead -- caught once in main() to stop "
                  "the whole drive loudly (exit 1) rather than reading as uncharted (exit 0) ==")
            try:
                check_charter("no/such/led/binary", "author")
                check("w9-green-raises-ledunusable", False, "no exception raised", failures)
            except mod_ledunusable_of(check_charter) as exc:
                msg = str(exc)
                check("w9-green-raises-ledunusable", True, f"{msg[:200]!r}", failures)
                check("w9-green-names-led-value", "no/such/led/binary" in msg, msg[:200], failures)
                check("w9-green-names-cwd", "cwd=" in msg, msg[:200], failures)
                check("w9-green-teaches-repo-root", "repo root" in msg, msg[:200], failures)

            print(f"== W10: RED (against {PRIOR_SHA}) -- run_led() with --allow-uncharted's own "
                  "call shape (a bad --led reaching run_led directly, since old check_charter "
                  "never stopped it) dies as a RAW, UNCAUGHT exception -- finding 1's second "
                  "symptom, the traceback half ==")
            try:
                old_drive_module.run_led(bad_led, ["work", "claim", "some-slug"], "author")
                check("w10-red-raises-uncaught-oserror", False, "no exception raised at all", failures)
            except OSError as exc:
                check("w10-red-raises-uncaught-oserror", True,
                      f"uncaught OSError propagated to the caller: {exc!r}", failures)
            except Exception as exc:  # noqa: BLE001
                check("w10-red-raises-uncaught-oserror", False,
                      f"raised {type(exc).__name__}, expected OSError: {exc!r}", failures)

            print("== W11: GREEN -- the SAME call against the CURRENT run_led() raises "
                  "LedUnusable cleanly (never a raw traceback) ==")
            try:
                run_led(bad_led, ["work", "claim", "some-slug"], "author")
                check("w11-green-raises-ledunusable", False, "no exception raised", failures)
            except mod_ledunusable_of(run_led) as exc:
                check("w11-green-raises-ledunusable", True, f"{str(exc)[:200]!r}", failures)

            print(f"== W12: RED (against {PRIOR_SHA}) -- run_led() with an EMPTY --led silently "
                  "executes this call's own args[0] AS THE PROGRAM (shlex.split('') is []) -- "
                  "finding 2's silent-wrong-execution shape, demonstrated with a harmless "
                  "'echo' args[0] so the silent success is directly observable rather than "
                  "merely a coincidental 'command not found' ==")
            old_rc, old_out = old_drive_module.run_led("", ["echo", "SILENTLY-RAN-AS-LED"], "author")
            check("w12-red-silently-executed-args0", old_rc == 0 and "SILENTLY-RAN-AS-LED" in old_out,
                  f"rc={old_rc} out={old_out!r} (args[0] 'echo' ran AS IF it were led itself)",
                  failures)

            print("== W13: GREEN -- the SAME empty --led against the CURRENT run_led() is "
                  "refused loudly, BEFORE any subprocess is attempted (never silently executes "
                  "args[0]) ==")
            try:
                run_led("", ["echo", "SILENTLY-RAN-AS-LED"], "author")
                check("w13-green-raises-ledunusable", False, "no exception raised", failures)
            except mod_ledunusable_of(run_led) as exc:
                msg = str(exc)
                check("w13-green-raises-ledunusable", True, f"{msg[:200]!r}", failures)
                check("w13-green-names-empty", "empty" in msg, msg[:200], failures)

            print(f"== W14: RED (against {PRIOR_SHA}) -- run_led() with MALFORMED shell quoting "
                  "raises an uncaught ValueError (finding 2's second shlex edge) ==")
            try:
                old_drive_module.run_led('bad "unterminated quote', ["--help"], "author")
                check("w14-red-raises-uncaught-valueerror", False, "no exception raised", failures)
            except ValueError as exc:
                check("w14-red-raises-uncaught-valueerror", True, f"uncaught: {exc!r}", failures)
            except Exception as exc:  # noqa: BLE001
                check("w14-red-raises-uncaught-valueerror", False,
                      f"raised {type(exc).__name__}, expected ValueError: {exc!r}", failures)

            print("== W15: GREEN -- the SAME malformed --led against the CURRENT run_led() "
                  "raises LedUnusable, naming the malformed value, never an uncaught ValueError ==")
            try:
                run_led('bad "unterminated quote', ["--help"], "author")
                check("w15-green-raises-ledunusable", False, "no exception raised", failures)
            except mod_ledunusable_of(run_led) as exc:
                msg = str(exc)
                check("w15-green-raises-ledunusable", True, f"{msg[:200]!r}", failures)
                check("w15-green-names-malformed-value", "unterminated quote" in msg, msg[:200],
                      failures)

            print("== W16: role_charter.py/role_brief.py's OWN run_led (finding 2, the other two "
                  "files this round fixes) -- empty --led refused loudly rather than silently "
                  "executing args[0], malformed quoting refused rather than raising -- exercised "
                  "directly against THIS worktree's copies (module-scope import above, never a "
                  "reimplementation) ==")
            for label, module in (("role_charter.py", role_charter), ("role_brief.py", role_brief)):
                rc, out, err = module.run_led("", ["echo", "SILENTLY-RAN"])
                combined = out + err
                check(f"w16-{label}-empty-led-no-silent-exec",
                      rc != 0 and "SILENTLY-RAN" not in combined and module.LED_UNUSABLE_MARKER in combined,
                      f"rc={rc} combined={combined[:160]!r}", failures)
                rc2, out2, err2 = module.run_led('bad "unterminated quote', ["--help"])
                check(f"w16-{label}-malformed-led-refused-not-raised",
                      rc2 != 0 and module.LED_UNUSABLE_MARKER in (out2 + err2),
                      f"rc={rc2} combined={(out2 + err2)[:160]!r}", failures)

            print(f"== W17: RED (against {PRIOR_SHA}) -- hydrate.sh's own $LED calls are ALL "
                  "quoted (\"$LED\" work open ...), so a MULTI-TOKEN --led override is passed as "
                  "one nonexistent literal filename -- this round's finding 3, correcting "
                  f"{PRIOR_SHA}'s own commit message claim ('sh's unquoted $LED already "
                  "word-splits', which was false: every use in that commit was quoted) ==")
            old_hydrate_src = git_show(PRIOR_SHA, "tools/workflow_units/autoharn-builder-wave/hydrate.sh")
            check("w17-red-source-quotes-led", '"$LED" work open' in old_hydrate_src,
                  "confirms the PRIOR_SHA source really does quote $LED (the false-record claim)",
                  failures)
            old_hydrate_path = tmpdir / "old_hydrate.sh"
            old_hydrate_path.write_text(old_hydrate_src)
            old_hydrate_path.chmod(0o755)
            cp = sh(["bash", str(old_hydrate_path), "--instance", "redprobe",
                    "--led", "/usr/bin/env echo", "--no-obligate"], cwd=str(REPO))
            combined = cp.stdout + cp.stderr
            check("w17-red-multitoken-led-fails",
                  cp.returncode != 0 and "REFUSED for an UNEXPECTED reason" in combined,
                  f"exit={cp.returncode} combined-tail={combined[-400:]!r}", failures)

            print("== W18: GREEN -- the CURRENT (fixed, led_run()-based) hydrate.sh with the "
                  "IDENTICAL multi-token --led override completes successfully (echo stands in "
                  "for led, so this is a real multi-token-split proof with zero ledger writes) ==")
            new_hydrate_path = WORKFLOW_UNITS_DIR / "autoharn-builder-wave" / "hydrate.sh"
            check("w18-green-source-uses-led-run", "led_run work open" in new_hydrate_path.read_text(),
                  "committed hydrate.sh calls led_run, not a direct quoted \"$LED\"", failures)
            cp = sh(["bash", str(new_hydrate_path), "--instance", "greenprobe",
                    "--led", "/usr/bin/env echo", "--no-obligate"], cwd=str(REPO))
            check("w18-green-multitoken-led-succeeds",
                  cp.returncode == 0 and "hydration complete" in cp.stdout,
                  f"exit={cp.returncode} stdout-tail={cp.stdout[-300:]!r}", failures)
        finally:
            os.chdir(orig_cwd)

    finally:
        if proc is not None:
            out = stop_server(proc)
            if out.strip():
                print("--- boundary service log tail ---")
                print(out[-2000:])
        teardown_schema(WORLD)
        shutil.rmtree(tmpdir, ignore_errors=True)

    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL CASES OK -- workflow-drive-dead-legacy-led-default: DRIVE_TEMPLATE/HYDRATE_TEMPLATE "
          "default fixed to the single-token libexec/autoharn/led + run_led shlex-splits, all 7 "
          "drive.py/hydrate.sh copies regenerated through the compiler's --repo-root override "
          "and match a fresh compile byte-for-byte, no baked worktree paths in ROLE_CHARTER_PY/"
          "ROLE_BRIEF_PY, check_charter() RED against ./legacy/led both pre- and post-charter-"
          "registration (strong form) / W2's served-default GREEN leg WITNESSED when the "
          "real-checkout role_charter.py has merged the shlex fix, UNEXERCISED with a disclosed "
          "blocker otherwise, W6/W7 GREEN proving run_led's own default+override fix directly. "
          "THIRD ROUND (confirming review, 3 findings): W8-W11 prove wrong-led/wrong-CWD is a "
          "loud LedUnusable refusal (never an ordinary uncharted-shaped exit 0, never a raw "
          "traceback) against both check_charter() and run_led(); W12/W13 prove empty --led no "
          "longer silently executes args[0] as the program; W14/W15 prove malformed shell "
          "quoting is a teaching refusal, not an uncaught ValueError; W16 proves the identical "
          "fix in role_charter.py's and role_brief.py's own run_led; W17/W18 prove hydrate.sh's "
          "new led_run() gives real multi-token --led support (RED: the PRIOR_SHA quoted \"$LED\" "
          "call treats a multi-token override as one nonexistent literal filename, correcting "
          "that commit's own false claim that it needed no fix) -- zero residue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
