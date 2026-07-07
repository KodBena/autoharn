#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-01T19:09:04Z
#   last-change: 2026-07-01T23:19:46Z
#   contributors: 3d7629dd/main, a737a042/main, a737a042/wf_40350274-0a4, 306d4c8f/main
# <<< PROVENANCE-STAMP <<<

"""stamp_provenance.py — PostToolUse hook: sign every changed source file in its header.

MANDATE (prime-directive, auditability). Every time Claude Code changes a file, that file's
header must carry WHO changed it (session id + workflow run id where applicable) and WHEN, so
a git diff is never again untraceable to the run that produced it — you read the provenance
off the file itself, and you never resume or trust the wrong run.

Wired as a PostToolUse hook on the edit tools (Edit/Write/MultiEdit/NotebookEdit). Claude Code
delivers the hook a JSON object on stdin with at least `session_id`, `transcript_path`, and
`tool_input.file_path`. The workflow run id is not passed directly, but a workflow sub-agent's
`transcript_path` runs through `.../subagents/workflows/wf_<id>/`, so we recover it from the
path (else 'main' — a non-workflow edit).

SAFETY (this hook mutates source; it must never corrupt one). It NEVER raises and NEVER
blocks: any uncertainty -> exit 0 having changed nothing. It touches a file only if the file
is inside the repo, has known comment syntax, is not in an excluded tree, and decodes utf-8.
The detection SENTINEL is assembled from split literals (see _SENTINEL) so the exact marker
never appears contiguously in this file's own source — a file can therefore never be mistaken
for its own banner (the bug the first version hit when it ate its own constants). The banner
is a fixed-size block: the first stamp inserts it (after any shebang / coding cookie), later
stamps REPLACE it in place, so line count is stable after insertion. History is kept compactly
(first-seen, last-change, deduplicated contributors).
"""
from __future__ import annotations

import datetime
import json
import os
import re
import select
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]  # tools/hooks/ -> repo root

# A live workflow streams sub-agent transcripts into its run dir continuously (observed
# inter-write gaps are seconds while any agent is running); a run that has written nothing
# for this long is dead, paused, or interrupted — its marker is stale evidence, not an
# attribution. Two orders of magnitude above the streaming cadence, well under the gap
# between runs.
STALE_WINDOW_S = 30 * 60

# Assembled from split literals ON PURPOSE: the contiguous marker string does NOT appear
# anywhere in this source, so stamping this very file cannot self-match its own definition.
_SENTINEL = "PROV" "ENANCE-STAMP"
BEGIN_MARK = f">>> {_SENTINEL} >>>"
END_MARK = f"<<< {_SENTINEL} <<<"

COMMENT = {
    ".py": "#", ".sh": "#", ".bash": "#", ".zsh": "#", ".toml": "#", ".cfg": "#",
    ".yaml": "#", ".yml": "#", ".ini": "#", ".rb": "#", ".pl": "#",
    ".js": "//", ".ts": "//", ".jsx": "//", ".tsx": "//", ".c": "//", ".h": "//",
    ".cc": "//", ".cpp": "//", ".hpp": "//", ".go": "//", ".rs": "//", ".java": "//",
}
EXCLUDE_PARTS = {".git", "node_modules", "__pycache__", ".venv", "venvs", ".mypy_cache",
                 ".pytest_cache", "claude-ephemera"}


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _workflow_id(transcript_path: str) -> str:
    """Best-effort workflow run id for the edit that triggered this hook.

    Preferred source: a workflow sub-agent's transcript path carries the run id
    (`.../workflows/wf_<id>/...`). This works if/when the harness passes the sub-agent's own
    transcript to the hook.

    Fallback: the harness currently does NOT expose the run id to hooks fired from workflow
    sub-agent edits — neither `transcript_path` (it is the parent session's) nor any env var
    carries it (verified by dumping the full hook input + os.environ; see the upstream bug
    report, Issue 3). So whoever launches the workflow writes an untracked marker under
    `.git/claude_active_workflow`, TWO lines: the run id, then the absolute path of that
    run's transcript dir. The rid is honored ONLY while the run is demonstrably live —
    something under its transcript dir modified within STALE_WINDOW_S — so the leftover
    marker of a dead/interrupted run degrades to the honest 'main' instead of forging
    attribution (pass 3's interrupted run left exactly such a stale marker, which
    false-stamped a later main-loop edit). A bare one-line marker is an unvalidatable claim
    and is treated as absent. CAVEAT unchanged: while a run is live, main-agent edits are
    attributed to it too (the hook cannot distinguish them), so the operator should avoid
    hand-editing during a run. Absent or stale marker: attribution is the honest 'main'."""
    m = re.search(r"/workflows/(wf_[a-z0-9-]+)/", transcript_path or "")
    if m:
        return m.group(1)
    try:
        marker = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", ""), ".git", "claude_active_workflow")
        with open(marker) as f:
            head = f.read().split("\n")
        rid = head[0].strip()
        rundir = head[1].strip() if len(head) > 1 else ""
        if not re.fullmatch(r"wf_[a-z0-9-]+", rid) or not rundir:
            return "main"  # bare/malformed marker: an unvalidatable claim is not evidence
        run = Path(rundir)
        if run.name != rid:
            return "main"  # marker is internally inconsistent; refuse to attribute on it
        newest = max((f.stat().st_mtime for f in run.iterdir()), default=0.0)
        if time.time() - newest <= STALE_WINDOW_S:
            return rid
    except OSError:
        pass
    return "main"


def _in_repo(p: Path) -> bool:
    try:
        p.relative_to(REPO)
        return True
    except ValueError:
        return False


def _build_block(lead: str, first_seen: str, now: str, contributors: list[str]) -> list[str]:
    return [
        f"{lead} {BEGIN_MARK} (auto; tools/hooks/stamp_provenance.py — do not hand-edit)",
        f"{lead}   first-seen : {first_seen}",
        f"{lead}   last-change: {now}",
        f"{lead}   contributors: {', '.join(contributors)}",
        f"{lead} {END_MARK}",
    ]


def stamp(path: Path, session: str, workflow: str, now: str) -> None:
    ext = path.suffix.lower()
    lead = COMMENT.get(ext)
    if lead is None or not path.is_file():
        return
    if any(part in EXCLUDE_PARTS for part in path.parts):
        return
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return
    lines = text.split("\n")
    tag = f"{session}/{workflow}"

    b0 = next((i for i, ln in enumerate(lines) if BEGIN_MARK in ln), None)
    if b0 is not None:
        b1 = next((j for j in range(b0, len(lines)) if END_MARK in lines[j]), None)
        if b1 is None:
            return  # malformed / truncated banner; refuse to touch
        block = lines[b0:b1 + 1]
        first_seen = next((ln.split("first-seen :", 1)[1].strip()
                           for ln in block if "first-seen :" in ln), now)
        cline = next((ln for ln in block if "contributors:" in ln), "")
        contribs = [c.strip() for c in cline.split("contributors:", 1)[-1].split(",")
                    if c.strip()] if cline else []
        if tag not in contribs:
            contribs.append(tag)
        lines[b0:b1 + 1] = _build_block(lead, first_seen, now, contribs)
    else:
        ins = 0
        if lines and lines[0].startswith("#!"):
            ins = 1
        if len(lines) > ins and re.search(r"coding[:=]", lines[ins]):
            ins += 1
        pad = [""] if (len(lines) > ins and lines[ins].strip() != "") else []
        lines[ins:ins] = _build_block(lead, now, now, [tag]) + pad

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    # NEVER block forever on stdin. A PostToolUse hook that hangs on an unfed stdin leaves a
    # stuck process per invocation; accumulated across a workflow's many edits that starves the
    # whole guest (shell + test processes). Bound the read: if input is not ready promptly, or
    # arrives malformed, do nothing and exit clean.
    try:
        ready, _, _ = select.select([sys.stdin], [], [], 2.0)
        if not ready:
            return 0
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError, OSError):
        return 0
    fp = (data.get("tool_input") or {}).get("file_path")
    if not fp:
        return 0
    path = Path(fp)
    if not path.is_absolute():
        path = Path(data.get("cwd") or os.getcwd()) / path
    path = path.resolve()
    if not _in_repo(path):
        return 0
    try:
        stamp(path, str(data.get("session_id", "unknown"))[:8],
              _workflow_id(data.get("transcript_path", "")), _now())
    except Exception:
        return 0  # a stamping bug must never corrupt a file or block a tool
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
