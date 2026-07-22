#!/usr/bin/env python3
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

# Migration note: this file used to live at tools/hooks/ (2 levels below the repo root, hence
# parents[2]); in autoharn it lives at the shallower top-level hooks/ (1 level below repo root),
# so parents[2] silently overshot to the PARENT of autoharn (/home/bork/w/vdc/1 — the directory
# holding claude_harness/ and epistemic-operator/ too). That widened this hook's own stated
# safety invariant ("touches a file only if inside the repo") to cover sibling repos as well —
# found and fixed while fixing the identical parents[N] migration-depth class elsewhere in
# drive/rehearsal/ (same bug shape, discovered in passing; CLAUDE.md: fixed, not routed around).
REPO = Path(__file__).resolve().parents[1]  # hooks/ -> repo root

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


def _find_banner(lines: list[str], lead: str) -> tuple[int, int] | None:
    """Locate a REAL banner: the fixed 5-line shape `_build_block()` emits, matched
    structurally (line-start prefixes at the exact relative offsets), not a bare marker
    substring anywhere in the file.

    Witnessed defect (ADR-0011's 2026-07-02 amendment; re-witnessed 2026-07-13 by the
    compound-nominal-detection-2 builder): the prior implementation matched `BEGIN_MARK in
    ln` -- ANY line containing the marker text ANYWHERE, including a regex literal, a doc
    comment describing the banner format, or a quoted specimen in a fixture file. That line
    was then mistaken for a real banner and REPLACED, corrupting content that merely
    *mentions* the marker rather than *being* one. A content-boundary check closes the
    class: a candidate is a real banner only if the begin-marker text starts the line (col
    0, not embedded mid-line inside other content) AND the following three lines and the
    end-marker line reproduce the exact fixed shape `_build_block()` always emits, at their
    exact relative offsets. A line mentioning the marker inside other code/text will not, in
    general, additionally reproduce that full 5-line shape immediately beneath it, so it is
    no longer mistaken for the banner it merely names.

    Named residual (per ADR-0000's closure-statement discipline -- not silently swept): a
    fixture that deliberately reproduces the full 5-line shape verbatim as CONTENT (e.g. a
    doc quoting the exact banner text as an example) is still indistinguishable from a real
    banner without full per-language quote/comment parsing, which this fix does not attempt.
    That narrower residual is the honest limit of a content-boundary check, distinct from
    (and far narrower than) the witnessed single-line-substring failure this closes.

    Returns (begin_line, end_line) inclusive indices of the first structurally-complete
    match, or None if no real banner is present (a truncated/damaged banner or a stray
    marker mention are both treated as "no real banner here" -- see `stamp()`, which
    disposes of the damaged-banner case separately via `_looks_like_damaged_banner`).
    """
    begin_prefix = f"{lead} {BEGIN_MARK}"
    end_line = f"{lead} {END_MARK}"
    fs_prefix = f"{lead}   first-seen :"
    lc_prefix = f"{lead}   last-change:"
    co_prefix = f"{lead}   contributors:"
    for i, ln in enumerate(lines):
        if not ln.startswith(begin_prefix):
            continue
        if (i + 4 < len(lines)
                and lines[i + 1].startswith(fs_prefix)
                and lines[i + 2].startswith(lc_prefix)
                and lines[i + 3].startswith(co_prefix)
                and lines[i + 4] == end_line):
            return i, i + 4
    return None


def _looks_like_damaged_banner(lines: list[str], lead: str) -> int | None:
    """A begin-marker line at column 0 immediately followed by a first-seen-shaped line, but
    that does not complete to the full valid shape `_find_banner` requires -- plausibly a
    REAL banner damaged by hand-editing (the old "malformed / truncated banner" safety net),
    as opposed to a stray one-line mention of the marker text with unrelated content after
    it. Returns the begin-line index of the first such candidate, or None."""
    begin_prefix = f"{lead} {BEGIN_MARK}"
    fs_prefix = f"{lead}   first-seen :"
    for i, ln in enumerate(lines):
        if ln.startswith(begin_prefix) and i + 1 < len(lines) and lines[i + 1].startswith(fs_prefix):
            return i
    return None


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

    found = _find_banner(lines, lead)
    if found is None and _looks_like_damaged_banner(lines, lead) is not None:
        return  # plausibly a real banner, hand-damaged; refuse to touch (old safety net)
    if found is not None:
        b0, b1 = found
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
