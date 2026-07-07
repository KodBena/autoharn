#!/usr/bin/env python3
"""persist_claude_ephemera.py — snapshot a Claude Code session's EPHEMERAL artifacts into
the repo, with a checksummed manifest, for audit.

WHY THIS EXISTS. Everything Claude Code produces around a run — the workflow SCRIPT that was
executed, the run record, the workflow JOURNAL, every sub-agent's full transcript, and the
background-task outputs — is written under ~/.claude/projects/... and /tmp/claude-*/... .
Those trees are the user profile and the OS temp dir: prunable, volatile, outside the repo,
outside version control, outside any audit trail. An audit that reasons about "what the
workflow actually did" is reasoning about data that can vanish (and that, once, was very
nearly declared gone). Auditability requires the raw evidence to be captured, immutable, and
provenance-stamped — in the repo, committed, checksummed.

WHAT IT CAPTURES, for a given session id, across ALL of that session's project dirs (Claude
Code makes a separate ~/.claude/projects/<slug> per working directory, so one session can
have several):
  * workflows/scripts/*.js         — the exact script each Workflow run executed
  * workflows/wf_*.json            — per-run records
  * subagents/workflows/wf_*/**    — journal.jsonl + every agent-*.jsonl / *.meta.json
  * subagents/agent-*.jsonl/.meta  — standalone (non-workflow) background agents
  * <scratch>/tasks/*.output       — background-task output files (best effort; /tmp)

For every file it writes MANIFEST.json: source path, sha256, byte size, mtime. The manifest
is the audit spine — it makes the snapshot tamper-evident and ties each archived byte to its
origin. Re-running is idempotent: identical bytes produce an identical manifest entry.

This tool does NOT capture the main conversation transcript (<session>.jsonl) by default — it
is live/growing and enormous; pass --include-session-transcript to snapshot it too.

Usage:
    python filing/persist_claude_ephemera.py --session <SESSION_ID> \
        --dest ephemera/session-<SESSION_ID>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _session_project_dirs(session: str) -> list[Path]:
    """All ~/.claude/projects/<slug> dirs that hold this session (one per working dir)."""
    out = []
    for slug in sorted(PROJECTS.glob("*")):
        if (slug / session).is_dir() or list(slug.glob(f"{session}*.jsonl")):
            out.append(slug)
    return out


def _iter_ephemera(session: str, include_transcript: bool) -> list[tuple[Path, str]]:
    """(absolute source, archive-relative dest) for every ephemeral file to capture."""
    items: list[tuple[Path, str]] = []
    for slug in _session_project_dirs(session):
        tag = slug.name
        sess = slug / session
        if include_transcript:
            for tr in slug.glob(f"{session}*.jsonl"):
                items.append((tr, f"{tag}/session-transcript/{tr.name}"))
        if not sess.is_dir():
            continue
        for sub in ("workflows", "subagents"):
            root = sess / sub
            if not root.is_dir():
                continue
            for f in root.rglob("*"):
                if f.is_file():
                    items.append((f, f"{tag}/{sub}/{f.relative_to(root)}"))
    return items


def _task_outputs(session: str) -> list[tuple[Path, str]]:
    items: list[tuple[Path, str]] = []
    for base in Path("/tmp").glob("claude-*"):
        for tasks in base.rglob(f"{session}/tasks"):
            for f in tasks.glob("*"):
                if f.is_file():
                    items.append((f, f"task-outputs/{f.name}"))
    return items


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", required=True, help="Claude Code session id (uuid)")
    ap.add_argument("--dest", required=True, help="in-repo archive directory")
    ap.add_argument("--include-session-transcript", action="store_true",
                    help="also snapshot the (large) main conversation transcript")
    a = ap.parse_args()

    dest = Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    items = _iter_ephemera(a.session, a.include_session_transcript) + _task_outputs(a.session)

    manifest = []
    total = 0
    for src, rel in items:
        tgt = dest / rel
        tgt.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, tgt)
        digest = _sha256(src)
        size = src.stat().st_size
        total += size
        manifest.append({"archive_path": rel, "source": str(src),
                         "sha256": digest, "bytes": size,
                         "mtime": int(src.stat().st_mtime)})

    manifest.sort(key=lambda m: m["archive_path"])
    (dest / "MANIFEST.json").write_text(
        json.dumps({"session": a.session, "file_count": len(manifest),
                    "total_bytes": total, "files": manifest}, indent=1))
    print(f"archived {len(manifest)} files ({total/1e6:.1f} MB) -> {dest}")
    print(f"manifest: {dest/'MANIFEST.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
