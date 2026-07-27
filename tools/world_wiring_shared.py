#!/usr/bin/env python3
"""tools/world_wiring_shared.py -- the ONE home (ADR-0012 P1) for the plumbing both
tools/world_wiring_backup.py and tools/world_wiring_restore.py need: resolving the AUTOHARN
checkout (for filing/deployment_record.py and the checkout's own git HEAD), the two manifest
constants, and the single sha256-of-a-file helper every hash comparison in either module uses.
Split out of tools/world_wiring.py (ADR-0007 file-size discipline; ADR-0012 P3 one-owner
collaborators) -- see that file's own module docstring for the tool's full contract (the closed
wiring set, the secrets policy, the restore refusal list).

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import below is top-of-file.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

TOOL_VERSION = "world-wiring/1.0"
MANIFEST_NAME = "manifest.json"

HERE = Path(__file__).resolve().parent
AUTOHARN = Path(os.environ.get("AUTOHARN", str(HERE / ".."))).resolve()

sys.path.insert(0, str(AUTOHARN / "filing"))
try:
    import deployment_record  # noqa: E402
except ImportError as e:
    print(f"world_wiring: cannot import autoharn's filing/deployment_record.py under "
          f"AUTOHARN={AUTOHARN} ({e.__class__.__name__}: {e})", file=sys.stderr)
    print("        set AUTOHARN=/path/to/autoharn, or place a sibling checkout at ../autoharn",
          file=sys.stderr)
    sys.exit(2)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head(cwd: Path) -> str:
    """The AUTOHARN checkout's own HEAD commit -- the manifest's provenance fact "which autoharn
    build made this backup", mirrors bootstrap/extract_context.py's own `_git` helper."""
    r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(cwd))
    return r.stdout.strip() if r.returncode == 0 else "UNKNOWN"
