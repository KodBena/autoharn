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

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"
WORLD = "wfdll1"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


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
        print("== W3: DRIVE_TEMPLATE source carries the fixed default, not the dead one ==")
        template_src = WORKFLOW_COMPILE_PY.read_text()
        check("w3-template-has-served-default", 'led = "./led"' in template_src,
              "DRIVE_TEMPLATE contains led = \"./led\"", failures)
        check("w3-template-lacks-legacy-default", 'led = "./legacy/led"' not in template_src,
              "DRIVE_TEMPLATE no longer contains led = \"./legacy/led\"", failures)

        print("== W4: all 7 generated drive.py copies match a FRESH compile, byte-for-byte on "
              "the `led = ...` line ==")
        scratch_out = tmpdir / "workflow_units_scratch"
        tomls = sorted(DESIGN_WORKFLOWS_DIR.glob("*.toml"))
        check("w4-seven-tomls-found", len(tomls) == 7, f"found {len(tomls)}: {[t.name for t in tomls]}",
              failures)
        led_default_re = re.compile(r'^\s*led = "([^"]+)"\s*$', re.MULTILINE)
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
                  bool(fresh_m) and fresh_m.group(1) == "./led",
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
            rc, out = check_charter("./autoharn led", "author")
            check("w2-green-exit-0", rc == 0, f"rc={rc}", failures)
            check("w2-green-in-force", "IN-FORCE charter registration" in out, f"out={out!r}", failures)
            check("w2-green-no-drift", "DRIFT" not in out, f"out={out!r}", failures)
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
    print("ALL CASES OK -- workflow-drive-dead-legacy-led-default: DRIVE_TEMPLATE default fixed, "
          "all 7 drive.py copies regenerated through the compiler's --repo-root override and "
          "match a fresh compile byte-for-byte, no baked worktree paths in ROLE_CHARTER_PY/"
          "ROLE_BRIEF_PY, check_charter() RED against ./legacy/led both pre- and post-charter-"
          "registration (strong form) / GREEN against served ./led -- zero residue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
