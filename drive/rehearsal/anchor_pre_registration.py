#!/usr/bin/env python3
"""anchor_pre_registration — file the Increment-5 ANCHOR rows into acts.ruling (binding_grade
`informational`), BEFORE the deriver exists.

WHY (consult 25 §7; POST-FABLE-OPERATING-BRIEF; BACKLOG mechanism 5). Git timestamps are not an
ordering authority; the append-only `acts.ruling` id IS. Anchoring the sha256 + path + commit of the
frames/oracle/brief and THIS increment's own pre-registered fixture expectations gives pre-banked
judgment an append-only ordering authority — so "the pre-registration preceded the deriver" is a
DB-provable fact, not a claim about file mtimes.

These are ANCHORS, not RULINGS: actor is `apparatus:engineer` (the engineer/apparatus principal), NEVER
`human:maintainer`. binding_grade='informational'. A ruling is a maintainer act; an anchor is
bookkeeping. The `acts.ruling` hash-match trigger enforces verbatim_sha256 == sha256(verbatim), so the
anchor's own freight cannot lie.

Idempotent: an anchor whose (path, target-sha) already sits in acts.ruling is skipped (append-only —
we never rewrite; we refuse to duplicate). Read-only on every doc; the only write is the append to
acts.ruling in the harness DB.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "filing"))
import pghost_resolve  # noqa: E402 (filing/pghost_resolve.py -- never a literal host default)

PGHOST = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
DB = "harness"
# Archive-pinned (like ledger_target's e15-e18 entries): the five DOCS below are e15 EVIDENCE that
# stays in the epistemic-operator archive — never migrated into autoharn. The old layout put this file
# at harness/e15-build/rehearsal/<file>, so parents[3] landed on the operator root; in autoharn this
# file lives at drive/rehearsal/, three levels shallower, so the same parents[3] now overshoots past
# the archive entirely. Point straight at the archive instead of trying to re-derive it by ancestry.
OPERATOR = Path("/home/bork/w/vdc/1/epistemic-operator")
ACTOR = "apparatus:engineer"

# The five documents to anchor (path relative to the operator repo). The pre-registration file anchors
# ITSELF (its content sha is the load-bearing pin; its commit is the pre-registration commit).
DOCS = [
    "consults/e15-analysis-consult-27-FRAME.md",
    "consults/e16-design-SEED.md",
    "POST-FABLE-OPERATING-BRIEF.md",
    "harness/e15-build/oracle.md",
    "harness/e15-build/rehearsal/INCREMENT-5-PRE-REGISTERED-expectations.md",
]


def _psql(sql: str, *, params: dict[str, str] | None = None) -> str:
    cmd = ["psql", "-h", PGHOST, "-d", DB, "-tA", "-v", "ON_ERROR_STOP=1"]
    for k, v in (params or {}).items():
        cmd += ["-v", f"{k}={v}"]
    r = subprocess.run(cmd, input=sql, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"psql failed ({r.returncode}): {r.stderr.strip()}")
    return r.stdout.strip()


def _sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _last_commit(rel: str) -> str:
    r = subprocess.run(["git", "-C", str(OPERATOR), "log", "-1", "--format=%H", "--", rel],
                       capture_output=True, text=True)
    return r.stdout.strip() or "(uncommitted-at-anchor)"


def _head() -> str:
    return subprocess.run(["git", "-C", str(OPERATOR), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()


def anchor_text(rel: str, doc_sha: str, doc_commit: str, head: str) -> str:
    """The verbatim ANCHOR manifest — a bookkeeping fact, quoted exactly (the hash-match trigger pins
    verbatim_sha256 == sha256 of this text)."""
    return (
        f"ANCHOR (Increment-5 pre-registration, informational). path={rel} "
        f"sha256={doc_sha} last-commit={doc_commit} operator-HEAD-at-anchor={head}. "
        f"Ordering authority for the pre-registered mock fixture expectations: this row's "
        f"append-only id fixes that the anchor preceded the acts<->s15 deriver (BACKLOG mechanism 5).")


def already_anchored(rel: str, doc_sha: str) -> bool:
    q = _psql(
        "SELECT count(*) FROM acts.ruling WHERE binding_grade='informational' "
        "AND actor=:'actor' AND verbatim LIKE :'pat';",
        params={"actor": ACTOR, "pat": f"ANCHOR (Increment-5%path={rel} sha256={doc_sha}%"})
    return q.isdigit() and int(q) > 0


def file_anchor(rel: str, verbatim: str) -> int:
    vsha = hashlib.sha256(verbatim.encode("utf-8")).hexdigest()
    sid = _psql(
        "WITH ins AS (INSERT INTO acts.ruling (actor, verbatim, verbatim_sha256, binding_grade, regards) "
        "VALUES (:'actor', :'v', :'vsha', 'informational', :'regards') RETURNING id) SELECT id FROM ins;",
        params={"actor": ACTOR, "v": verbatim, "vsha": vsha,
                "regards": f"e15 Increment-5 pre-registration anchor: {rel}"})
    return int(sid)


def main() -> int:
    head = _head()
    filed: list[tuple[str, int]] = []
    skipped: list[str] = []
    for rel in DOCS:
        p = OPERATOR / rel
        if not p.exists():
            raise SystemExit(f"anchor target missing: {rel} (refusing to anchor a phantom — ADR-0002)")
        doc_sha = _sha256_file(p)
        if already_anchored(rel, doc_sha):
            skipped.append(rel)
            continue
        verbatim = anchor_text(rel, doc_sha, _last_commit(rel), head)
        rid = file_anchor(rel, verbatim)
        filed.append((rel, rid))
    print("# Increment-5 anchoring — acts.ruling informational rows (actor apparatus:engineer)")
    for rel, rid in filed:
        print(f"  FILED   id={rid:>3}  {rel}")
    for rel in skipped:
        print(f"  SKIP    (already anchored, identical sha)  {rel}")
    print(f"# operator HEAD at anchor: {head}")
    print("# current acts.ruling anchor rows:")
    rows = _psql("SELECT id||'|'||actor||'|'||left(verbatim,64) FROM acts.ruling "
                 "WHERE binding_grade='informational' ORDER BY id;")
    for line in rows.splitlines():
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
