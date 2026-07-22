#!/usr/bin/env python3
"""branch_attribution — the branch-attribution DERIVED VIEW vestigial_documentation/design/ORCH-WORKTREE-LEDGERING.md 3b
calls for ("Branch attribution as derivation, not schema"). Read-only, observer-grade: joins a
ledger row's `stamp_invocation` token (s23, kernel/lineage/s23-per-invocation-stamp-token.sql) to
the matching line in `<world-root>/.claude/logs/invocations.jsonl` (hooks/stamp_intercept.py's own
per-invocation journal), and reads that line's `cwd` field (added by this same commission) to
answer "which checkout wrote this row" -- then, best-effort, which git branch that checkout is on.

ZERO KERNEL CHANGE (the memo's own words): this is a VIEW over two things that already exist post
this commission -- the s23 column and the now-cwd-carrying journal -- never a new table, column, or
ledger write. Nothing here mutates the ledger or the journal.

HONEST LIMIT, inherited from s23 and restated here rather than silently assumed (design/
ORCH-WORKTREE-LEDGERING.md §4, "Honest limits"): the invocation token is UNAUTHENTICATED (no HMAC
over it -- kernel/lineage/s23-per-invocation-stamp-token.sql's own header) and the journal is a
host-local, hook-written file in the SAME trust domain as every other journal this project reads.
So an attribution this tool prints is EVIDENCE-grade (a same-OS-user subject could self-set
app.vendor_invocation or hand-edit the journal), never PROOF-grade -- it answers "what does the
record say", not "what is cryptographically guaranteed". The branch name itself is a further,
separately-disclosed approximation: it is resolved from `cwd` AT READ TIME (`git -C <cwd> rev-parse
--abbrev-ref HEAD`), not at write time -- a checkout that has since switched branches, or been
removed, reports its CURRENT branch or an explicit UNRESOLVABLE-CHECKOUT, never a stale guess passed
off as history.

THREE ATTRIBUTION OUTCOMES, per tokened row (never silently merged):
  ATTRIBUTED        -- the token has a matching journal line, and that line carries a cwd.
  JOURNALED-NO-CWD   -- the token has a matching journal line, but it predates this commission's
                        cwd field (an honest pre-token-era or pre-cwd-field journal line).
  UNJOURNALED        -- the row carries a token but no journal line matches it at all (a lost/never-
                        written journal line, or a journal from a different world than the one named
                        on the command line).
A row with NO stamp_invocation at all (pre-s23, or an unstamped/non-intercepted write) is excluded
from this view entirely -- it has nothing to attribute; `gates/... ` / `engine/contemp_edb.py`'s own
row_untokened family is the place that fact is already visible.

USAGE:
  python3 tools/branch_attribution.py <target-name> <world-root-dir> [--json]

<target-name> resolves via engine/ledger_edb.resolve() -> engine/targets.py (the ONE home for a
deployment name -> db/schema/kern, ADR-0012 P1) -- pass a registered name, a LEDGER_DEPLOYMENT env
var pointing at a deployment.json, or LEDGER_DB/LEDGER_SCHEMA/LEDGER_KERN, exactly as every other
engine/ consumer does; this module derives no second copy of that resolution logic.
<world-root-dir> is the project directory carrying `.claude/logs/invocations.jsonl` (the same `root`
engine/contemp_edb.py's `export()` reads).

Exit 0 on a clean read (regardless of how many rows are UNJOURNALED -- that is a finding, not a tool
failure); 1 if the target has no stamp_invocation column at all (nothing to join, named loudly rather
than printing an empty, misleadingly-clean report); 2 on a usage error.

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(
    subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
    .stdout.strip())
sys.path.insert(0, str(_REPO_ROOT / "engine"))

import ledger_edb  # engine/ledger_edb.py -- Target/resolve/CapabilityError, the ONE home (ADR-0012 P1)


def _read_invocation_journal(root: Path) -> tuple[dict[str, dict], int]:
    """token -> journal record, from `<root>/.claude/logs/invocations.jsonl`. Best-effort: a
    malformed line is skipped and counted, never raised -- mirrors hooks/stamp_intercept.py's own
    best-effort journal-write posture and engine/contemp_edb.py's `_read_jsonl` precedent (the
    established pattern for reading this exact journal family; not re-derived here as a second
    parser, ADR-0012 P1 -- this module keeps its own copy only because contemp_edb.py's version
    returns a flat list keyed for EDB export, not a token-keyed map, so the two do not share code
    directly, but they read the identical file with the identical malformed-line posture)."""
    path = root / ".claude" / "logs" / "invocations.jsonl"
    by_token: dict[str, dict] = {}
    skipped = 0
    if not path.is_file():
        return by_token, skipped
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        if not isinstance(rec, dict):
            skipped += 1
            continue
        token = rec.get("token")
        if isinstance(token, str) and token:
            by_token[token] = rec
    return by_token, skipped


def _branch_of(cwd: str) -> str | None:
    """Best-effort: the git branch checked out at `cwd` RIGHT NOW (read-time, not write-time --
    see module docstring's honest limit). None if the path is gone, is not a git repo, or the
    command fails -- never raises; a missing branch is a printed None, not a crash."""
    if not cwd or not Path(cwd).is_dir():
        return None
    try:
        r = subprocess.run(["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
                            capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip() or None if r.returncode == 0 else None


def attribute(target_name: str, root: Path) -> list[dict]:
    """One entry per ledger row carrying a non-NULL stamp_invocation token, in id order, joined to
    its invocation-journal line (if any) and that line's cwd / derived branch (if any). Read-only:
    one SELECT against the ledger, one read of the journal file, best-effort git branch lookups --
    never a write anywhere."""
    t = ledger_edb.resolve(target_name)
    if not t.has_col("stamp_invocation"):
        raise ledger_edb.CapabilityError(
            f"target {target_name!r} (schema {t.schema}) has no stamp_invocation column -- "
            f"pre-s23 schema (kernel/lineage/s23-per-invocation-stamp-token.sql not applied here). "
            f"Branch attribution has nothing to join; every row on this schema is, by construction, "
            f"row_untokened (engine/contemp_edb.py's own s23_capable=False family).")
    by_token, journal_skipped = _read_invocation_journal(root)
    rows = t.rows(
        f"SELECT id, kind, stamp_invocation FROM {t.rel()} "
        f"WHERE stamp_invocation IS NOT NULL ORDER BY id;")
    out: list[dict] = []
    for row in rows:
        rid, kind, token = row[0], row[1], row[2]
        rec = by_token.get(token)
        entry: dict = {"ledger_id": int(rid), "kind": kind, "stamp_invocation": token}
        if rec is None:
            entry.update(attribution="UNJOURNALED", cwd=None, branch=None)
        else:
            cwd = rec.get("cwd")
            if isinstance(cwd, str) and cwd:
                entry.update(attribution="ATTRIBUTED", cwd=cwd, branch=_branch_of(cwd))
            else:
                entry.update(attribution="JOURNALED-NO-CWD", cwd=None, branch=None)
        out.append(entry)
    if journal_skipped:
        print(f"branch_attribution: {journal_skipped} malformed journal line(s) skipped "
              f"({root / '.claude' / 'logs' / 'invocations.jsonl'})", file=sys.stderr)
    return out


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    if len(args) != 2:
        print("usage: branch_attribution.py <target-name> <world-root-dir> [--json]", file=sys.stderr)
        return 2
    target_name, root = args[0], Path(args[1])
    try:
        rows = attribute(target_name, root)
    except ledger_edb.CapabilityError as e:
        print(f"branch_attribution: {e}", file=sys.stderr)
        return 1
    if as_json:
        print(json.dumps(rows, indent=2))
        return 0
    print(f"branch_attribution: {len(rows)} tokened row(s) in target {target_name!r} (world {root})")
    for r in rows:
        print(f"  ledger#{r['ledger_id']:>6}  {r['kind']:<12}  {r['attribution']:<16}  "
              f"cwd={r['cwd']}  branch={r['branch']}")
    n_attributed = sum(1 for r in rows if r["attribution"] == "ATTRIBUTED")
    print(f"branch_attribution: {n_attributed}/{len(rows)} row(s) ATTRIBUTED to a checkout")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
