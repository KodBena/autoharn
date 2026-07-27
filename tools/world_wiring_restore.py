#!/usr/bin/env python3
"""tools/world_wiring_restore.py -- the `restore` subcommand's own module (split out of
tools/world_wiring.py, ADR-0007 file-size discipline / ADR-0012 P3 one-owner collaborators; that
file's own module docstring is the authoritative full contract, including the closed list of
refusal conditions below).

Verifies the manifest and every archive member's path/type/sha256 BEFORE writing a single byte,
refusing wholesale (ADR-0012 P2: a boundary translates-and-validates, it never coerces a
malformed input into a plausible one) on: a missing/unparseable manifest.json, an absolute or
path-escaping member, a non-regular-file member (symlink/hardlink/device -- the classic tar-
extraction escape vector), a member absent from the manifest or a manifest entry absent from the
archive, a sha256 mismatch, a manifest mode carrying setuid/setgid/sticky bits (restore never
mints privileged binaries from an archive), a destination path component that is a symlink on
disk (writing through it would escape --dest -- the on-disk twin of the in-archive symlink
refusal above), or a differing existing destination file without --force.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import below is top-of-file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tarfile
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_wiring_shared as shared  # noqa: E402


class RestoreRefused(Exception):
    """Raised to abort restore before anything is written -- caught once at the top of
    cmd_restore so every refusal path shares one exit/print shape (ADR-0002: fail loud, one
    channel, teaching text)."""


def _validate_member_path(rel: str) -> None:
    if PurePosixPath(rel).is_absolute() or rel.startswith("/"):
        raise RestoreRefused(f"archive member {rel!r} is an absolute path -- refused wholesale, "
                              f"nothing written.")
    if ".." in PurePosixPath(rel).parts:
        raise RestoreRefused(f"archive member {rel!r} contains a '..' path-escape component -- "
                              f"refused wholesale, nothing written.")


def _load_manifest_from_tar(tf: tarfile.TarFile) -> dict:
    try:
        first = tf.next()
    except tarfile.TarError as e:
        raise RestoreRefused(f"archive is not a readable tar stream ({e}). Nothing written.")
    if first is None or first.name != shared.MANIFEST_NAME:
        raise RestoreRefused(
            f"archive's first member is not {shared.MANIFEST_NAME!r} "
            f"(got {first.name if first else None!r}) -- a world_wiring archive always carries "
            f"the manifest first; this is not one, or it has been reordered/tampered with. "
            f"Nothing written.")
    fobj = tf.extractfile(first)
    if fobj is None:
        raise RestoreRefused(f"{shared.MANIFEST_NAME} member has no extractable data. "
                              f"Nothing written.")
    raw = fobj.read()
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RestoreRefused(f"{shared.MANIFEST_NAME} is not valid JSON ({e}). Nothing written.")
    if (not isinstance(manifest, dict) or "files" not in manifest
            or not isinstance(manifest["files"], list)):
        raise RestoreRefused(f"{shared.MANIFEST_NAME} is missing its 'files' list -- unparseable "
                              f"manifest shape. Nothing written.")
    return manifest


def _verify_archive(tf: tarfile.TarFile, dest: Path, force: bool) -> tuple[dict, dict, dict]:
    """Pass 1+2 of restore: everything that can be checked WITHOUT writing a byte. Returns
    (manifest, manifest_files, contents) once every check passes; raises RestoreRefused otherwise
    (nothing written on any path through this function)."""
    manifest = _load_manifest_from_tar(tf)
    manifest_files = {e["path"]: e for e in manifest["files"]}

    members = [m for m in tf.getmembers() if m.name != shared.MANIFEST_NAME]
    member_names = {m.name for m in members}

    for m in members:
        _validate_member_path(m.name)
        if not m.isfile():
            raise RestoreRefused(
                f"archive member {m.name!r} is not a regular file (type {m.type!r}) -- refused "
                f"(a symlink/hardlink/device member is a path-escape vector this tool never "
                f"writes and never restores). Nothing written.")
        if m.name not in manifest_files:
            raise RestoreRefused(
                f"archive member {m.name!r} is not listed in {shared.MANIFEST_NAME} -- refused "
                f"wholesale (a tar member absent from its own manifest cannot be trusted). "
                f"Nothing written.")

    missing_from_archive = sorted(set(manifest_files) - member_names)
    if missing_from_archive:
        raise RestoreRefused(
            f"{shared.MANIFEST_NAME} lists {len(missing_from_archive)} file(s) not present in "
            f"the archive as members: {missing_from_archive} -- refused wholesale (a manifest "
            f"that overclaims its own contents cannot be trusted). Nothing written.")

    contents: dict[str, bytes] = {}
    for m in members:
        fobj = tf.extractfile(m)
        if fobj is None:
            raise RestoreRefused(f"archive member {m.name!r} has no extractable data. "
                                  f"Nothing written.")
        data = fobj.read()
        got = hashlib.sha256(data).hexdigest()
        want = manifest_files[m.name]["sha256"]
        if got != want:
            raise RestoreRefused(
                f"archive member {m.name!r} sha256 mismatch: manifest says {want}, archive bytes "
                f"hash to {got} -- TAMPERED OR CORRUPT. Refused wholesale, nothing written.")
        contents[m.name] = data

    for rel in contents:
        entry = manifest_files[rel]
        try:
            mode = int(entry["mode"], 8)
        except (KeyError, TypeError, ValueError):
            raise RestoreRefused(
                f"manifest entry for {rel!r} carries no parseable octal 'mode' field -- refused "
                f"wholesale, nothing written.")
        if mode & 0o7000:
            raise RestoreRefused(
                f"manifest mode {entry['mode']!r} for {rel!r} carries setuid/setgid/sticky bits -- "
                f"no wiring file legitimately needs them, and restore will not mint privileged "
                f"binaries from an archive. Refused wholesale, nothing written.")
        cur = dest
        for part in PurePosixPath(rel).parts:
            cur = cur / part
            if cur.is_symlink():
                raise RestoreRefused(
                    f"destination path component {cur} is a symlink on disk -- restoring {rel!r} "
                    f"would write THROUGH it to wherever it points, potentially outside --dest. "
                    f"Refused wholesale, nothing written. Remove or replace that symlink first if "
                    f"the restore is intended.")

    conflicts = []
    for rel, data in contents.items():
        dest_file = dest / rel
        if dest_file.is_file() and shared.sha256_file(dest_file) != hashlib.sha256(data).hexdigest():
            conflicts.append(rel)
    if conflicts and not force:
        raise RestoreRefused(
            f"{len(conflicts)} destination file(s) already exist and DIFFER from the incoming "
            f"archive content, and --force was not given -- refused wholesale, nothing written. "
            f"Differing file(s): {conflicts}. Re-run with --force to overwrite (every overwrite "
            f"will be printed by name).")

    return manifest, manifest_files, contents


def _print_followup(dest: Path, manifest: dict) -> None:
    world = manifest.get("world", {})
    print(f"\nmanifest world: name={world.get('name')!r} schema={world.get('schema')!r} "
          f"kern={world.get('kern')!r} role={world.get('role')!r}; "
          f"backed up from autoharn checkout commit {manifest.get('autoharn_checkout_commit')!r}")

    print("\nFOLLOW-UP -- run these next (teach, don't guess):")
    dispatcher = dest / "autoharn"
    if dispatcher.is_file() and os.access(dispatcher, os.X_OK):
        print(f"  1. cd {dest} && ./autoharn doctor          # confirm 0 FAIL against this "
              f"restored wiring")
    else:
        print(f"  1. no ./autoharn dispatcher was restored (this world predates the umbrella-CLI "
              f"migration -- it uses its own per-verb shims instead, e.g. ./led, ./doctor if "
              f"present). Run this world's own doctor-equivalent shim from {dest}.")

    dest_dep = dest / "deployment.json"
    try:
        restored_dep = shared.deployment_record.load_deployment(dest_dep)
    except shared.deployment_record.DeploymentError:
        restored_dep = None
    if restored_dep and restored_dep.boundary_url:
        print(f"  2. this world's deployment.json points at boundary_url="
              f"{restored_dep.boundary_url!r}, deployment={restored_dep.boundary_deployment!r}. "
              f"If THIS machine does not already run a multiplex hub answering that URL (check "
              f"{dest}/boundary-multiplex.toml and run `./autoharn service start` from the "
              f"AUTOHARN checkout that hub belongs to), doctor above will fail at the boundary "
              f"probe -- start the hub, or edit deployment.json's boundary_url/"
              f"boundary_deployment to point at wherever it actually runs on this machine, "
              f"before trusting doctor's result.")
    else:
        print("  2. no boundary_url in the restored deployment.json -- this world is not wired "
              "to a served multiplex hub; nothing further to reconcile there.")


def cmd_restore(args: argparse.Namespace) -> int:
    archive_path = Path(args.archive).resolve()
    dest = Path(args.dest).resolve()
    if not archive_path.is_file():
        print(f"world_wiring restore: REFUSED -- {archive_path} is not a file. Nothing written.",
              file=sys.stderr)
        return 2

    try:
        with tarfile.open(archive_path, "r:gz") as tf:
            manifest, manifest_files, contents = _verify_archive(tf, dest, args.force)
    except RestoreRefused as e:
        print(f"world_wiring restore: REFUSED -- {e}", file=sys.stderr)
        return 1

    # Every check passed -- now, and only now, write.
    restored = skipped = overwritten = 0
    for rel, data in sorted(contents.items()):
        dest_file = dest / rel
        mode = int(manifest_files[rel]["mode"], 8)
        existed = dest_file.is_file()
        if existed and shared.sha256_file(dest_file) == hashlib.sha256(data).hexdigest():
            print(f"  SKIPPED-IDENTICAL  {rel}")
            skipped += 1
            continue
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        dest_file.write_bytes(data)
        os.chmod(dest_file, mode)
        if existed:
            print(f"  OVERWRITTEN        {rel}")
            overwritten += 1
        else:
            print(f"  RESTORED           {rel}")
            restored += 1

    print(f"\nworld_wiring restore: {restored} restored, {skipped} skipped-identical, "
          f"{overwritten} overwritten, into {dest}")
    _print_followup(dest, manifest)
    return 0
