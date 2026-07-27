#!/usr/bin/env python3
"""tools/world_wiring_backup.py -- the `backup` subcommand's own module (split out of
tools/world_wiring.py, ADR-0007 file-size discipline / ADR-0012 P3 one-owner collaborators; that
file's own module docstring is the authoritative full contract -- the closed wiring set, the
secrets policy -- restated here only where the code itself needs the exact list to walk).

Enumerates the closed wiring set (deployment.json + dust records, the `autoharn` dispatcher,
.autoharn-world.json, features.json, legacy/, .claude/ minus secrets/logs, law/, keys/,
attestations/, boundary-multiplex.toml), hashes every included file, and writes one tar.gz whose
first member is manifest.json. Secrets are excluded by default and the exclusion is loud (every
`.claude/secrets/`/`.claude/logs/` path found is printed with its reason; no --include-secrets
flag exists).

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import below is top-of-file.
"""
from __future__ import annotations

import argparse
import io
import json
import stat
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_wiring_shared as shared  # noqa: E402

# The closed set's fixed-name members (tools/world_wiring.py's own module docstring is the
# authoritative prose form of this same list -- kept here as the ONE machine-checkable copy,
# ADR-0012 P1).
SINGLE_FILES: tuple[str, ...] = ("deployment.json", "autoharn", ".autoharn-world.json",
                                  "features.json", "boundary-multiplex.toml")
DUST_GLOB = "deployment.*.json.dust"
WHOLE_DIRS: tuple[str, ...] = ("legacy", "law", "keys", "attestations")
CLAUDE_DIR = ".claude"
CLAUDE_SECRET_PREFIX = ".claude/secrets"
CLAUDE_LOGS_PREFIX = ".claude/logs"

SECRET_EXCLUSION_REASON = ("secrets are excluded by default in v1 -- a secret's transport is the "
                            "operator's own explicit act (scp, a password manager, a sealed "
                            "channel), never a tool default; there is no --include-secrets flag")
LOGS_EXCLUSION_REASON = ("session/runtime output, not wiring -- churns every session; excluded "
                          "on the same line the autoharn-panel repo's own committed .gitignore "
                          "draws in its \"scaffold-owned churn\" block")


def _relpath(p: Path, root: Path) -> str:
    return p.relative_to(root).as_posix()


def enumerate_wiring(world_dir: Path) -> tuple[list[Path], list[tuple[str, str]], list[str]]:
    """Walks <world_dir> against the closed set above. Returns (included, excluded, absent):
      included -- absolute Paths to regular files that will be archived.
      excluded -- (relpath, reason) pairs: exists on disk, deliberately left out (secrets/logs).
      absent   -- relpaths of optional closed-set members that simply do not exist here (never
                  an exclusion -- there was nothing to exclude)."""
    included: list[Path] = []
    excluded: list[tuple[str, str]] = []
    absent: list[str] = []

    for name in SINGLE_FILES:
        p = world_dir / name
        if p.is_file():
            included.append(p)
        elif name != "deployment.json":  # deployment.json's own absence is a hard refusal upstream
            absent.append(name)

    dust_matches = sorted(world_dir.glob(DUST_GLOB))
    if dust_matches:
        included.extend(p for p in dust_matches if p.is_file())
    else:
        absent.append(DUST_GLOB)

    for dirname in WHOLE_DIRS:
        d = world_dir / dirname
        if not d.is_dir():
            absent.append(f"{dirname}/")
            continue
        for f in sorted(d.rglob("*")):
            if f.is_file():
                included.append(f)

    claude_dir = world_dir / CLAUDE_DIR
    if not claude_dir.is_dir():
        absent.append(f"{CLAUDE_DIR}/")
    else:
        for f in sorted(claude_dir.rglob("*")):
            if not f.is_file():
                continue
            rel = _relpath(f, world_dir)
            if rel == CLAUDE_SECRET_PREFIX or rel.startswith(CLAUDE_SECRET_PREFIX + "/"):
                excluded.append((rel, SECRET_EXCLUSION_REASON))
                continue
            if rel == CLAUDE_LOGS_PREFIX or rel.startswith(CLAUDE_LOGS_PREFIX + "/"):
                excluded.append((rel, LOGS_EXCLUSION_REASON))
                continue
            included.append(f)

    return included, excluded, absent


def cmd_backup(args: argparse.Namespace) -> int:
    world_dir = Path(args.world_dir).resolve()
    if not world_dir.is_dir():
        print(f"world_wiring backup: REFUSED -- {world_dir} is not a directory. Nothing written.",
              file=sys.stderr)
        return 2

    dep_path = world_dir / "deployment.json"
    try:
        dep = shared.deployment_record.load_deployment(dep_path)
    except shared.deployment_record.DeploymentError as e:
        print(f"world_wiring backup: REFUSED -- {e}\n"
              f"        deployment.json is required (it is this tool's own source for the "
              f"manifest's world/schema/kern/role fields). Nothing written.", file=sys.stderr)
        return 2

    included, excluded, absent = enumerate_wiring(world_dir)

    world_name = dep.name if dep.name else world_dir.name
    world_name_source = "deployment.json" if dep.name else (
        "directory basename (deployment.json has no optional 'name' field)")

    print(f"world_wiring backup: {world_dir}")
    print(f"  world name: {world_name!r} (source: {world_name_source})")
    print()
    print(f"INCLUDED ({len(included)} file(s)):")
    for p in included:
        print(f"  + {_relpath(p, world_dir)}")
    print()
    if excluded:
        print(f"EXCLUDED ({len(excluded)} file(s), found but deliberately left out):")
        for rel, reason in excluded:
            print(f"  - {rel}  [{reason}]")
    else:
        print("EXCLUDED: none found (no .claude/secrets/ or .claude/logs/ content present)")
    print()
    if absent:
        print("ABSENT (optional closed-set member(s) not present here, not an exclusion):")
        for a in absent:
            print(f"  . {a}")
        print()

    files_manifest = []
    for p in included:
        st = p.stat()
        files_manifest.append({
            "path": _relpath(p, world_dir),
            "sha256": shared.sha256_file(p),
            "mode": format(stat.S_IMODE(st.st_mode), "04o"),
            "size": st.st_size,
        })

    manifest = {
        "tool_version": shared.TOOL_VERSION,
        "created_ts": datetime.now(timezone.utc).isoformat(),
        "world": {"name": world_name, "schema": dep.schema, "kern": dep.kern, "role": dep.role},
        "autoharn_checkout_commit": shared.git_head(shared.AUTOHARN),
        "excluded_count": len(excluded),
        "files": files_manifest,
    }

    out_path = Path(args.out) if args.out else Path.cwd() / f"{world_dir.name}-wiring.tar.gz"
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")

    with tarfile.open(out_path, "w:gz") as tf:
        # manifest.json FIRST -- restore reads it before trusting anything else in the archive.
        ti = tarfile.TarInfo(name=shared.MANIFEST_NAME)
        ti.size = len(manifest_bytes)
        ti.mtime = int(datetime.now(timezone.utc).timestamp())
        tf.addfile(ti, io.BytesIO(manifest_bytes))
        for p, entry in zip(included, files_manifest):
            tf.add(str(p), arcname=entry["path"], recursive=False)

    print(f"wrote {out_path} ({len(files_manifest)} file(s) + manifest.json, "
          f"{len(excluded)} excluded, autoharn checkout commit "
          f"{manifest['autoharn_checkout_commit']})")
    return 0
