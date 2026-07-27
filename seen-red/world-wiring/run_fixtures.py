#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity live proof for tools/world_wiring.py (maintainer commission
2026-07-27, verbatim: "back up all relevant files with a manifest ... put in a tar.gz ... clone
your upstream repository, then .../tools/whatever_well_call_it.sh backup_scaffold.tar.gz";
gates/fixture_census.py REGISTRY entry "world-wiring"). Mirrors seen-red/extract-context/
run_fixtures.py's own scratch-birth-and-drop convention: ONE throwaway world born in the toy db
(192.168.122.1), backed up, COPIED (the original scaffold output is never mutated), stripped of
its wiring on the copy, restored, served through a freshly-spawned SCRATCH boundary_service on an
unused loopback port (never 8433/8422, never this repo's own boundary-multiplex.toml), and
doctored to 0 FAIL -- then torn down to zero residue unless a case fails (left standing as
evidence).

CASES:
  GREEN-BACKUP-MANIFEST   -- every per-file sha256 in the backup's manifest.json is independently
                     recomputed straight off the SOURCE world's own disk and matches -- never
                     trusting the tool's own self-report.
  GREEN-SECRETS-EXCLUDED -- a planted .claude/secrets/ file's unique marker is (a) named, with
                     its exclusion reason, in the backup command's own stdout, and (b) absent
                     from the tar.gz's bytes entirely (grepped directly against the archive).
  GREEN-RESTORE-DOCTOR   -- a COPY of the source world has its entire wiring set deleted
                     (simulating a fresh clone that has everything EXCEPT the wiring), is
                     restored from the backup tar, served through a scratch boundary_service, and
                     that copy's own `./autoharn doctor` reports 0 FAIL through the restored
                     wiring.
  RED-NO-MANIFEST        -- a manifest-less tarball is refused (exit 1), nothing written.
  RED-PATH-ESCAPE         -- a crafted archive containing a `../evil` member is refused (exit 1),
                     nothing written.
  RED-TAMPERED-HASH       -- a crafted archive whose manifest sha256 disagrees with its own
                     member's real bytes is refused (exit 1), nothing written.
  RED-CONFLICT-NO-FORCE  -- restoring a real backup onto a destination whose deployment.json
                     already exists with DIFFERENT content, without --force, is refused (exit 1)
                     naming the conflicting file; the destination file is provably unchanged
                     afterward.
  RED-SETUID-MODE        -- a crafted archive whose manifest declares mode 4755 (setuid) for a
                     member is refused (exit 1), nothing written.
  RED-DEST-SYMLINK       -- a destination containing a pre-planted symlinked directory component
                     on a member's path is refused (exit 1); the symlink's target directory is
                     provably untouched (nothing written THROUGH the link).

Scratch-only: one throwaway schema/kern/role triple in the TOY db, one scratch boundary_service
child process on a dynamically-chosen free loopback port -- both torn down after, UNLESS a case
FAILS (left standing as evidence, printed at the end).

Usage: python3 seen-red/world-wiring/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own environment
# before any subprocess is spawned -- inherited by the whole process tree this fixture starts.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

REPO = Path(__file__).resolve().parents[2]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
WORLD_WIRING = REPO / "tools" / "world_wiring.py"
PGHOST = fixture_pghost()
DB = "toy"

WORLD_NAME = "wwfixturescratch"
SECRET_MARKER = "SECRET_MARKER_WORLDWIRING_7c2a_fixture"

# The closed wiring set, restated here ONLY to know what to strip off the COPY before restoring
# (world_wiring.py's own module docstring is the authoritative source of this list -- ADR-0012
# P1; this is a TEST-SIDE consumer of that same closed set, not a second definition of it).
WIRING_ENTRIES = ("deployment.json", "autoharn", ".autoharn-world.json", "features.json",
                  "legacy", ".claude", "law", "keys", "attestations", "boundary-multiplex.toml")


def _psql(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, *args], capture_output=True, text=True)


def _drop_scratch(name: str) -> None:
    _psql("-v", "ON_ERROR_STOP=0", "-q",
          "-c", f"DROP SCHEMA IF EXISTS {name} CASCADE;",
          "-c", f"DROP SCHEMA IF EXISTS {name}_kernel CASCADE;",
          "-c", f"DROP ROLE IF EXISTS {name}_rw;")


def _birth(dest: Path, world: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(NEW_PROJECT), str(dest), "--new-world", world, "--db", DB, "--host", PGHOST,
         "--name", world],
        capture_output=True, text=True, cwd=str(REPO), timeout=300)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _run_tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(WORLD_WIRING), *args], capture_output=True,
                          text=True, cwd=str(REPO))


def _craft_archive(path: Path, member_name: str, member_bytes: bytes, files_entries: list[dict]) -> None:
    """A minimal hand-built archive for the RED crafted cases: manifest.json first (whatever
    `files_entries` says, honest or dishonest -- the case decides), then exactly one data member.
    Never uses world_wiring.py itself to build these -- they exist to prove restore distrusts an
    archive it did not build, not to round-trip its own output."""
    manifest = {
        "tool_version": "world-wiring/1.0", "created_ts": "2026-07-27T00:00:00Z",
        "world": {"name": "x", "schema": "x", "kern": "x", "role": "x"},
        "autoharn_checkout_commit": "deadbeef", "excluded_count": 0, "files": files_entries,
    }
    mbytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with tarfile.open(path, "w:gz") as tf:
        ti = tarfile.TarInfo(name="manifest.json"); ti.size = len(mbytes)
        tf.addfile(ti, io.BytesIO(mbytes))
        ti2 = tarfile.TarInfo(name=member_name); ti2.size = len(member_bytes); ti2.mode = 0o644
        tf.addfile(ti2, io.BytesIO(member_bytes))


def main() -> int:
    failures: list[str] = []
    _drop_scratch(WORLD_NAME)
    tmpdir = Path(tempfile.mkdtemp(prefix="world-wiring-fixture-"))
    src = tmpdir / "src"

    # --------------------------------------------------------------------------------- SETUP
    r = _birth(src, WORLD_NAME)
    if r.returncode != 0:
        print(f"SETUP: birth failed, exit={r.returncode}\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
        return 1
    print("SETUP: scratch world born -- PASS")

    secrets_dir = src / ".claude" / "secrets"
    secrets_dir.mkdir(parents=True, exist_ok=True)
    (secrets_dir / "planted.txt").write_text(f"{SECRET_MARKER}: must never leave this directory\n",
                                              encoding="utf-8")

    # Wire boundary_url/boundary_deployment + a boundary-multiplex.toml INTO the source world
    # BEFORE backup -- mirrors WORLD-REBIRTH-RUNBOOK.md Step 4's real sequencing (boundary wired,
    # then the world's own deployment.json/boundary-multiplex.toml both name it), so the backup
    # this fixture takes is of a REALISTIC fully-wired world, not a pre-Step-4 birth.
    port = _free_port()
    dep_path = src / "deployment.json"
    dep = json.loads(dep_path.read_text(encoding="utf-8"))
    dep["boundary_url"] = f"http://127.0.0.1:{port}"
    dep["boundary_deployment"] = WORLD_NAME
    dep_path.write_text(json.dumps(dep, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (src / "boundary-multiplex.toml").write_text(
        f"[deployments.{WORLD_NAME}]\n"
        f"pghost = \"{PGHOST}\"\npgdatabase = \"{DB}\"\npguser = \"{WORLD_NAME}_rw\"\n"
        f"pgschema = \"{WORLD_NAME}\"\npgkern = \"{WORLD_NAME}_kernel\"\n", encoding="utf-8")

    # ------------------------------------------------------------------------------- BACKUP
    out_tar = tmpdir / "backup.tar.gz"
    r = _run_tool("backup", str(src), "--out", str(out_tar))
    backup_ok = r.returncode == 0 and out_tar.is_file()
    if not backup_ok:
        failures.append(f"SETUP-BACKUP: exit={r.returncode}\nstdout={r.stdout}\nstderr={r.stderr}")
    print(f"SETUP: backup -- {'PASS' if backup_ok else 'FAIL'}")

    # --------------------------------------------------------------- GREEN-SECRETS-EXCLUDED
    marker_named = SECRET_MARKER in r.stdout or ".claude/secrets/planted.txt" in r.stdout
    archive_bytes = out_tar.read_bytes()
    marker_leaked = SECRET_MARKER.encode("utf-8") in archive_bytes
    secrets_ok = marker_named and not marker_leaked
    if not secrets_ok:
        failures.append(f"GREEN-SECRETS-EXCLUDED: named_in_stdout={marker_named} "
                        f"leaked_into_archive_bytes={marker_leaked}")
    print(f"GREEN-SECRETS-EXCLUDED: planted secret named in exclusion print, absent from archive "
          f"bytes -- {'PASS' if secrets_ok else 'FAIL'}")

    # --------------------------------------------------------------- GREEN-BACKUP-MANIFEST
    with tarfile.open(out_tar, "r:gz") as tf:
        manifest = json.loads(tf.extractfile("manifest.json").read())
    hash_ok = len(manifest["files"]) > 0
    for entry in manifest["files"]:
        actual = _sha256_file(src / entry["path"])
        if actual != entry["sha256"]:
            hash_ok = False
            failures.append(f"GREEN-BACKUP-MANIFEST: {entry['path']} manifest sha256 "
                            f"{entry['sha256']} != recomputed {actual}")
    print(f"GREEN-BACKUP-MANIFEST: {len(manifest['files'])} manifest sha256(s) independently "
          f"recomputed from source disk -- {'PASS' if hash_ok else 'FAIL'}")

    # -------------------------------------------------------------------------- RED cases
    red_dir = tmpdir / "red"
    red_dir.mkdir()

    nomanifest = red_dir / "nomanifest.tar.gz"
    with tarfile.open(nomanifest, "w:gz") as tf:
        data = b"x"
        ti = tarfile.TarInfo(name="onefile.txt"); ti.size = len(data)
        tf.addfile(ti, io.BytesIO(data))
    dst_nm = red_dir / "dst_nomanifest"
    r = _run_tool("restore", str(nomanifest), "--dest", str(dst_nm))
    ok = r.returncode == 1 and "REFUSED" in r.stderr and not dst_nm.exists()
    if not ok:
        failures.append(f"RED-NO-MANIFEST: exit={r.returncode} stderr={r.stderr!r} "
                        f"dst_exists={dst_nm.exists()}")
    print(f"RED-NO-MANIFEST: manifest-less tarball refused, nothing written -- "
          f"{'PASS' if ok else 'FAIL'}")

    escape_tar = red_dir / "escape.tar.gz"
    _craft_archive(escape_tar, "../evil.txt", b"evil",
                   [{"path": "../evil.txt", "sha256": hashlib.sha256(b"evil").hexdigest(),
                     "mode": "0644", "size": 4}])
    dst_esc = red_dir / "dst_escape"
    r = _run_tool("restore", str(escape_tar), "--dest", str(dst_esc))
    escape_wrote_outside = (red_dir.parent / "evil.txt").exists()
    ok = r.returncode == 1 and "REFUSED" in r.stderr and "path-escape" in r.stderr and not escape_wrote_outside
    if not ok:
        failures.append(f"RED-PATH-ESCAPE: exit={r.returncode} stderr={r.stderr!r} "
                        f"wrote_outside={escape_wrote_outside}")
    print(f"RED-PATH-ESCAPE: '../evil' member refused, nothing written -- {'PASS' if ok else 'FAIL'}")

    data = b"real-content-that-does-not-match-the-manifest"
    tampered_tar = red_dir / "tampered.tar.gz"
    _craft_archive(tampered_tar, "somefile.txt", data,
                   [{"path": "somefile.txt", "sha256": "0" * 64, "mode": "0644", "size": len(data)}])
    dst_tam = red_dir / "dst_tampered"
    r = _run_tool("restore", str(tampered_tar), "--dest", str(dst_tam))
    ok = r.returncode == 1 and "TAMPERED" in r.stderr and not dst_tam.exists()
    if not ok:
        failures.append(f"RED-TAMPERED-HASH: exit={r.returncode} stderr={r.stderr!r} "
                        f"dst_exists={dst_tam.exists()}")
    print(f"RED-TAMPERED-HASH: sha256-mismatched member refused, nothing written -- "
          f"{'PASS' if ok else 'FAIL'}")

    dst_conflict = red_dir / "dst_conflict"
    dst_conflict.mkdir()
    conflicting_content = '{"different": "content-that-does-not-match-the-backup"}\n'
    (dst_conflict / "deployment.json").write_text(conflicting_content, encoding="utf-8")
    r = _run_tool("restore", str(out_tar), "--dest", str(dst_conflict))
    now_content = (dst_conflict / "deployment.json").read_text(encoding="utf-8")
    other_files_absent = not (dst_conflict / "features.json").exists()
    ok = (r.returncode == 1 and "REFUSED" in r.stderr and "deployment.json" in r.stderr
          and now_content == conflicting_content and other_files_absent)
    if not ok:
        failures.append(f"RED-CONFLICT-NO-FORCE: exit={r.returncode} stderr={r.stderr!r} "
                        f"content_unchanged={now_content == conflicting_content} "
                        f"other_files_absent={other_files_absent}")
    print(f"RED-CONFLICT-NO-FORCE: differing existing file refused by name, destination "
          f"untouched -- {'PASS' if ok else 'FAIL'}")

    data = b"innocuous bytes under a privileged mode claim"
    setuid_tar = red_dir / "setuid.tar.gz"
    _craft_archive(setuid_tar, "somefile.txt", data,
                   [{"path": "somefile.txt", "sha256": hashlib.sha256(data).hexdigest(),
                     "mode": "4755", "size": len(data)}])
    dst_suid = red_dir / "dst_setuid"
    r = _run_tool("restore", str(setuid_tar), "--dest", str(dst_suid))
    ok = r.returncode == 1 and "setuid" in r.stderr and not dst_suid.exists()
    if not ok:
        failures.append(f"RED-SETUID-MODE: exit={r.returncode} stderr={r.stderr!r} "
                        f"dst_exists={dst_suid.exists()}")
    print(f"RED-SETUID-MODE: manifest mode 4755 refused, nothing written -- "
          f"{'PASS' if ok else 'FAIL'}")

    data = b"bytes that must never cross the symlink"
    symlink_tar = red_dir / "symlink_dest.tar.gz"
    _craft_archive(symlink_tar, "sub/inner.txt", data,
                   [{"path": "sub/inner.txt", "sha256": hashlib.sha256(data).hexdigest(),
                     "mode": "0644", "size": len(data)}])
    outside = red_dir / "outside_target"
    outside.mkdir()
    dst_sym = red_dir / "dst_symlink"
    dst_sym.mkdir()
    (dst_sym / "sub").symlink_to(outside)
    r = _run_tool("restore", str(symlink_tar), "--dest", str(dst_sym))
    wrote_through = any(outside.iterdir())
    ok = r.returncode == 1 and "symlink" in r.stderr and not wrote_through
    if not ok:
        failures.append(f"RED-DEST-SYMLINK: exit={r.returncode} stderr={r.stderr!r} "
                        f"wrote_through_symlink={wrote_through}")
    print(f"RED-DEST-SYMLINK: pre-planted symlinked destination component refused, nothing "
          f"written through it -- {'PASS' if ok else 'FAIL'}")

    # ------------------------------------------------------------------ GREEN-RESTORE-DOCTOR
    copy_dir = tmpdir / "copy"
    shutil.copytree(src, copy_dir)
    for entry in WIRING_ENTRIES:
        target = copy_dir / entry
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    for dust in copy_dir.glob("deployment.*.json.dust"):
        dust.unlink()
    stripped_ok = not any((copy_dir / e).exists() for e in WIRING_ENTRIES)
    if not stripped_ok:
        failures.append("GREEN-RESTORE-DOCTOR: setup -- wiring strip left residue on the copy")
    print(f"SETUP: copy's wiring set stripped (simulating a fresh clone) -- "
          f"{'PASS' if stripped_ok else 'FAIL'}")

    r = _run_tool("restore", str(out_tar), "--dest", str(copy_dir))
    restore_ok = r.returncode == 0
    if not restore_ok:
        failures.append(f"GREEN-RESTORE-DOCTOR: restore into copy failed, exit={r.returncode}\n"
                        f"{r.stdout}\n{r.stderr}")
    print(f"SETUP: restore into stripped copy -- {'PASS' if restore_ok else 'FAIL'}")

    boundary_proc = None
    doctor_ok = False
    if restore_ok:
        toml_path = copy_dir / "boundary-multiplex.toml"
        boundary_proc = subprocess.Popen(
            [sys.executable, "-m", "serving.boundary_service", "--config", str(toml_path),
             "--port", str(port)],
            cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        health_url = f"http://127.0.0.1:{port}/d/{WORLD_NAME}/health"
        up = False
        for _ in range(50):
            try:
                with urllib.request.urlopen(health_url, timeout=1) as resp:
                    up = resp.status == 200
                    if up:
                        break
            except (urllib.error.URLError, OSError):
                pass
            time.sleep(0.2)
        if not up:
            failures.append(f"GREEN-RESTORE-DOCTOR: scratch boundary_service never answered "
                            f"{health_url}")
        print(f"SETUP: scratch boundary_service up on 127.0.0.1:{port} -- {'PASS' if up else 'FAIL'}")

        if up:
            dispatcher = copy_dir / "autoharn"
            r = subprocess.run([str(dispatcher), "doctor"], cwd=str(copy_dir),
                               capture_output=True, text=True, timeout=60)
            doctor_ok = r.returncode == 0 and "TOTAL: 0 FAIL" in r.stdout
            if not doctor_ok:
                failures.append(f"GREEN-RESTORE-DOCTOR: doctor exit={r.returncode}\n{r.stdout}")
            print(r.stdout)
            print(f"GREEN-RESTORE-DOCTOR: restored copy's own ./autoharn doctor -- "
                  f"{'PASS' if doctor_ok else 'FAIL'}")

    if boundary_proc is not None:
        boundary_proc.terminate()
        try:
            boundary_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            boundary_proc.kill()
            boundary_proc.wait(timeout=10)

    # -------------------------------------------------------------------------------- REPORT
    if failures:
        print(f"\nworld-wiring fixture: {len(failures)} FAILURE(S) -- scratch substrate left "
              f"standing as evidence:\n  tempdir: {tmpdir}\n  world: {WORLD_NAME} (db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch(WORLD_NAME)
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nworld-wiring fixture: all cases PASS, scratch substrate torn down to zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
