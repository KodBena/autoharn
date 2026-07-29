#!/usr/bin/env python3
"""boundary_read_journal -- the read-observer channel for `serving/boundary_service.py`'s GET
routes (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §1a, work item
ac-read-identity). One line per completed GET request: {ts, deployment, route, view, identity,
row_count} -- no row CONTENT, ever (the spec's own line: "the journal must never become a
second copy of scoped data").

DECISION, STATED HONESTLY (the commission's own question -- "same channel as
hooks/pretooluse_read_observer.py, or a sibling?"): a SIBLING, in the SAME IDIOM, never the
same channel. `hooks/pretooluse_read_observer.py` observes a completely different subject: a
Claude Code AGENT's own filesystem `Read` tool calls, journaled to `<session-cwd>/.claude/logs/
read_observer.journal.jsonl` by a PreToolUse hook wired through `.claude/apparatus.json`'s own
switchboard -- its producer is the harness, its consumer is a session/apparatus audit, and it
has no HTTP request in scope at all. THIS journal's producer is `serving/boundary_service.py`
itself (an HTTP server process, not a Claude Code hook), its subject is a boundary GET request
(vendor-stamped, minted-principal, or anonymous caller -- never necessarily a Claude Code
session), and its consumer is the access-control spec's own read-observer half ("who read
what"). Sharing pretooluse_read_observer.py's file would conflate two unrelated producers
writing two unrelated record shapes into one stream -- exactly the "one file, one shape" rule
`boundary_diagnostic_log.py`'s own docstring states for its EVENT vocabulary, applied here to
files instead of events. So: a NEW file, `<world_dir>/.claude/logs/boundary_reads.jsonl`,
DELIBERATELY placed in the SAME `.claude/logs/` directory every other world-scoped journal in
this project already uses (`bootstrap/new-project.sh` creates that directory at scaffold time
for exactly this class of file -- change_gate.journal.jsonl, mutation_observer.journal.jsonl,
read_observer.journal.jsonl, verify_commission.jsonl, ... -- see those hooks' own docstrings),
so an operator or audit script already knows where to look for a world's own journals without
learning a second convention for the boundary's read-observer half specifically.

`world_dir` IS the directory holding this deployment's `boundary-multiplex.toml`/
`deployment.json` (`serving/ensure_running.py`'s own `world_dir` -- the same directory
`spawn_and_wait` derives `service.log` from). `serving/boundary_service.py`'s `main()` derives
it once, from `--config`'s own parent, and threads it through `create_app` -- never re-derived
per request.

FAIL-OPEN, SAME POSTURE AS EVERY HOOK JOURNAL IN THIS PROJECT: a journal-write failure (a full
disk, a missing/unwritable directory, a passed-in `None` world_dir) must never fail, delay, or
otherwise perturb the read it is merely describing -- this module's own `append_read` swallows
any exception past the point the record is already built, mirroring `hooks/
pretooluse_read_observer.py`'s own `_journal`'s `except Exception: pass` and
`boundary_diagnostic_log.log_event`'s own "RENDER + WRITE ... can never raise past this
function" discipline. This journal is, exactly like every hook journal here, DIAGNOSTIC/
EVIDENTIARY-ADJACENT but NOT the kernel's own evidentiary basis -- the spec's own §2 wording
("the read-observer channel gains who-read-what, which is the witness half of every guarantee
below") makes it the WITNESS, not the enforcement mechanism; enforcement (once §1b's scopes
land) is the boundary-side filter, a separate, later build.

PERFORMANCE HONESTY (spec, verbatim: "journaling must not add a blocking write on the hot read
path in a way that measurably slows reads"): `append_read` does one `os.makedirs(exist_ok=True)`
+ one buffered text-mode append `open(...).write(...)` per call -- no fsync, no flush forced
past Python's own buffering, the SAME cost shape every sibling hook journal above already pays
per tool call. Measured before/after on a 1000-row walk against a scratch deployment (see this
work item's own commit message for the observed numbers) rather than asserted.

Stdlib only, top-of-file imports (the lazy-import gate, gates/no_lazy_imports.py, applies).
"""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
from typing import Any


def journal_path(world_dir: Path) -> Path:
    """The one path this module ever writes to for a given `world_dir` -- see module docstring
    for why this directory (not a new top-level convention) and why this basename (not
    `read_observer.journal.jsonl`, the unrelated hook's own file)."""
    return Path(world_dir, ".claude", "logs", "boundary_reads.jsonl")


def _iso_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds")


def append_read(world_dir: Path | None, *, deployment: str | None, route: str, view: str | None,
                 identity: dict[str, Any], row_count: int | None,
                 redactions: list[dict[str, Any]] | None = None) -> None:
    """Appends ONE journal line for a completed GET request. A no-op, always, when `world_dir`
    is `None` (a direct/unit-shaped `create_app` caller that never wired one -- this project's
    own fixture bank, e.g., which has no `--config`-derived world directory at all) -- the same
    "absence is not itself a refusal" posture `serving/boundary_diagnostic_log.py`'s own
    `bind_identity`/`bind_deployment` already state for a missing request context.

    NO ROW CONTENT: `row_count` is a bare integer (or `None` when this route's response shape
    could not be sized honestly, e.g. a streaming SSE connection) -- never the rows themselves,
    never a hash of them, never enough to reconstruct them. This is the spec's own §1b-forward
    invariant applied a build early: "the journal must never become a second copy of scoped
    data."

    `redactions` (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §1b/§1c, work item
    ac-boundary-scope-filter): THE READ JOURNAL'S OWN TYPED REDACTION EVENT, this build's
    witness half. A SUMMARY only -- `[{family, value, disclosure_mode, count}, ...]`
    (`boundary_scope_filter.ScopeFilterResult.redactions`'s own shape) -- carrying WHICH
    exclusion families/values fired and HOW MANY rows each excluded, never the excluded rows'
    own content or ids: the identical "never a second copy of scoped data" invariant above,
    applied to redactions specifically. `None`/omitted defaults to an empty list in the
    written record (always present as a key, so a consumer can `jq 'select(.redactions != [])'`
    uniformly without a presence check first -- the SAME "one shape per field name, everywhere"
    discipline `boundary_diagnostic_log.py`'s own module docstring states for its event
    vocabulary, applied here to this sibling journal's one record shape).
    """
    if world_dir is None:
        return
    record: dict[str, Any] = {
        "ts": _iso_now(),
        "deployment": deployment,
        "route": route,
        "view": view,
        "identity": identity,
        "row_count": row_count,
        "redactions": redactions or [],
    }
    try:
        path = journal_path(world_dir)
        os.makedirs(path.parent, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception:  # noqa: BLE001 -- a read journal must never break the read it describes
        pass
