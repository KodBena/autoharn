#!/usr/bin/env python3
"""run_fixtures -- both-polarity live proof for ledger item `led-work-list-state-filter`
(gates/fixture_census.py REGISTRY entry "led-work-list-state-filter").

THE ITEM (maintainer directive 2026-07-13, RIGHT-NOW priority): `./led work list` used to dump
EVERY work item ever opened, closed items included, with no filter -- at ~60 lifetime items this
made the open-work view unreadable and overflowed an orchestrator context read. `led work list`
now defaults to state<>'closed' (open/claimed only); `--all` restores the pre-existing
full-history view, one explicit flag away. Auditability held constant: nothing is deleted or
hidden from the ledger itself -- this is a read-verb default only, `led work asof <ts>` and the
raw ledger rows stay the complete record.

THIS ITEM'S CODE WAS ALREADY MERGED (git log: commit 5084932, "merge led-work-list-state-filter
(835778b)") -- it predates this build session. This fixture supplies the both-polarity proof and
fixture-census registration that item never got at merge time. RED evidence (below) is captured
by running the SAME cases against a scratch COPY of bootstrap/templates/led.tmpl with ONLY the
`list)` case's body reverted to its pre-fix shape (unconditional SELECT, no --all support, no
show_all branching) -- a targeted revert rather than `git stash` (this delta is not part of the
current session's own uncommitted diff, so stashing the working tree would not reproduce it).
led.tmpl's own AUTOHARN=/PICKUP_DEPLOYMENT= overrides (documented at its own top-of-file, "runs
are strictly linear... live verbs") let this reverted copy run standalone against the same
scratch deployment the GREEN cases use, without touching led.tmpl on disk.

CASES (all live subprocess runs of the real `./led` -- or, for RED, a targeted-reverted copy of
led.tmpl -- against one real scratch deployment):

  ADOPT                -- bootstrap/track-work.sh stands up the scratch deployment.
  GREEN-DEFAULT-EXCLUDES-CLOSED -- two work items opened, one claimed+closed; plain
                          `led work list` includes the open one, excludes the closed one.
  GREEN-ALL-INCLUDES-CLOSED     -- `led work list --all` includes BOTH.
  RED-DEFAULT-INCLUDES-CLOSED   -- the SAME two-item fixture, read via the targeted-reverted
                          `list)` case: the closed item appears in the UNFILTERED default output
                          too (the reported defect, reproduced).
  RED-ALL-FLAG-UNSUPPORTED      -- the reverted case's usage does not recognize --all at all
                          (the pre-fix `list)` body takes no arguments) -- passing it either
                          errors or is silently ignored, never a distinguishing full-vs-filtered
                          view; witnessed and recorded either way, not presumed.

Usage: python3 seen-red/led-work-list-state-filter/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LED_TMPL = REPO / "bootstrap" / "templates" / "led.tmpl"
PGHOST, DB = fixture_pghost(), "toy"
SCRATCH_NAME = "lwlsffixture"
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"
TAG = f"seen-red-led-work-list-state-filter-{int(time.time())}"

# The pre-fix `list)` case body (git show 835778b^:bootstrap/templates/led.tmpl's own shape,
# re-expressed against the CURRENT effective_state-aware SELECT columns so the revert isolates
# ONLY the state-filter axis, not also undoing the unrelated s33 effective_state column this
# session did not touch): no shift/case/--all handling at all, one unconditional SELECT.
PRE_FIX_LIST_BODY = """    list)
      exec psql -h "$PGHOST" -d "$PGDB" -c "
        SELECT w.slug, w.title, w.state, w.resolution, w.witness, p.name AS claimant
        FROM ${SCHEMA}.work_item_current w LEFT JOIN ${KERNEL}.principal p ON p.id = w.claimant
        ORDER BY w.slug;"
      ;;
"""

LIST_BLOCK_RE = re.compile(r"^    list\)\n.*?\n    violations\)\n", re.DOTALL | re.MULTILINE)


def _make_reverted_copy(dest: Path) -> Path:
    text = LED_TMPL.read_text()
    replaced, n = LIST_BLOCK_RE.subn(PRE_FIX_LIST_BODY + "    violations)\n", text, count=1)
    if n != 1:
        raise RuntimeError("could not locate the current `list)` .. `violations)` block to revert "
                            "-- led.tmpl's work-list case shape changed since this fixture was written")
    out = dest / "led-work-list-state-filter-PREFIX.tmpl"
    out.write_text(replaced)
    out.chmod(0o755)
    return out


def _psql(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, *args], capture_output=True, text=True)


def _drop_scratch() -> None:
    _psql("-v", "ON_ERROR_STOP=0", "-q",
          "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;",
          "-c", f"DROP SCHEMA IF EXISTS {KERN} CASCADE;",
          "-c", f"DROP ROLE IF EXISTS {ROLE};")


def _run(dest: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(dest / args[0]), *args[1:]], capture_output=True, text=True, cwd=str(dest))


def _run_reverted(dest: Path, reverted: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["AUTOHARN"] = str(REPO)
    env["PICKUP_DEPLOYMENT"] = str(dest / "deployment.json")
    return subprocess.run(["bash", str(reverted), *args], capture_output=True, text=True,
                           cwd=str(dest), env=env)


def main() -> int:
    failures: list[str] = []
    _drop_scratch()
    tmpdir = Path(tempfile.mkdtemp(prefix="led-work-list-state-filter-fixture-"))
    dest = tmpdir / "project"

    # --------------------------------------------------------------------------------- ADOPT
    # new-project.sh --new-world (not track-work.sh, whose own ceiling stops at s15..s25/s30 --
    # see led-work-depends-default-type-advisory's own fixture note): `led work close
    # --review-deferred` below needs kernel/lineage/s29-obligation-item-key-and-typed-close.sql's
    # work_review_disposition column, which only --new-world's full birth chain carries.
    r = subprocess.run(["bash", str(NEW_PROJECT), str(dest), "--new-world", SCRATCH_NAME,
                        "--db", DB, "--host", PGHOST], capture_output=True, text=True, cwd=str(REPO))
    for verb in ("led", "judge", "pickup"):
        p = dest / verb
        if p.exists():
            p.chmod(0o755)
    ok = r.returncode == 0 and (dest / "deployment.json").exists()
    if not ok:
        failures.append(f"ADOPT: exit={r.returncode}\nSTDOUT:\n{r.stdout[-1500:]}\nSTDERR:\n{r.stderr[-1500:]}")
    print(f"ADOPT: new-project.sh --new-world exit={r.returncode} deployment.json="
          f"{(dest / 'deployment.json').exists()} -- {'PASS' if ok else 'FAIL'}")
    if not ok:
        print(f"\nADOPT FAILED, aborting -- scratch left standing:\n  tempdir: {tmpdir}")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    open_slug = f"{TAG}-open"
    closed_slug = f"{TAG}-closed"
    for slug, title in ((open_slug, "Open item"), (closed_slug, "Closed item")):
        r = _run(dest, "led", "work", "open", slug, title)
        if r.returncode != 0:
            failures.append(f"SETUP open {slug}: exit={r.returncode}\nSTDERR:\n{r.stderr}")
    r = _run(dest, "led", "work", "claim", closed_slug)
    if r.returncode != 0:
        failures.append(f"SETUP claim {closed_slug}: exit={r.returncode}\nSTDERR:\n{r.stderr}")
    r = _run(dest, "led", "work", "close", closed_slug, "dropped", "--review-deferred")
    if r.returncode != 0:
        failures.append(f"SETUP close {closed_slug}: exit={r.returncode}\nSTDERR:\n{r.stderr}")

    # ----------------------------------------------------------- GREEN-DEFAULT-EXCLUDES-CLOSED
    r = _run(dest, "led", "work", "list")
    has_open = open_slug in r.stdout
    has_closed = closed_slug in r.stdout
    ok = r.returncode == 0 and has_open and not has_closed
    if not ok:
        failures.append(f"GREEN-DEFAULT-EXCLUDES-CLOSED: exit={r.returncode} has_open={has_open} "
                         f"has_closed={has_closed}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    print(f"GREEN-DEFAULT-EXCLUDES-CLOSED: exit={r.returncode} open_item_shown={has_open} "
          f"closed_item_shown={has_closed} -- {'PASS' if ok else 'FAIL'}")

    # ----------------------------------------------------------- GREEN-ALL-INCLUDES-CLOSED
    r = _run(dest, "led", "work", "list", "--all")
    has_open = open_slug in r.stdout
    has_closed = closed_slug in r.stdout
    ok = r.returncode == 0 and has_open and has_closed
    if not ok:
        failures.append(f"GREEN-ALL-INCLUDES-CLOSED: exit={r.returncode} has_open={has_open} "
                         f"has_closed={has_closed}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    print(f"GREEN-ALL-INCLUDES-CLOSED: exit={r.returncode} open_item_shown={has_open} "
          f"closed_item_shown={has_closed} -- {'PASS' if ok else 'FAIL'}")

    # ------------------------------------------------------------------- build the reverted copy
    reverted = _make_reverted_copy(tmpdir)

    # ----------------------------------------------------------- RED-DEFAULT-INCLUDES-CLOSED
    r = _run_reverted(dest, reverted, "work", "list")
    has_open = open_slug in r.stdout
    has_closed = closed_slug in r.stdout
    # RED: the DEFECT is that the closed item ALSO shows up with no filter at all -- this
    # reproduces the reported "unfiltered dump" behavior.
    reproduces_defect = r.returncode == 0 and has_open and has_closed
    if not reproduces_defect:
        failures.append(f"RED-DEFAULT-INCLUDES-CLOSED: exit={r.returncode} has_open={has_open} "
                         f"has_closed={has_closed} (expected BOTH present, reproducing the "
                         f"pre-fix unfiltered dump)\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    print(f"RED-DEFAULT-INCLUDES-CLOSED (reverted list) case): exit={r.returncode} "
          f"open_item_shown={has_open} closed_item_shown={has_closed} -- "
          f"{'PASS (defect reproduced)' if reproduces_defect else 'FAIL'}")

    # ----------------------------------------------------------- RED-ALL-FLAG-UNSUPPORTED
    r = _run_reverted(dest, reverted, "work", "list", "--all")
    # pre-fix `list)` takes no positional args at all -- exec'd psql ignores extra shell words
    # silently (they are simply not referenced anywhere in the SQL), so this is expected to
    # behave IDENTICALLY to plain `work list` above (both items shown, --all not a distinguishing
    # flag) -- witnessed, not presumed.
    has_open2 = open_slug in r.stdout
    has_closed2 = closed_slug in r.stdout
    same_as_plain = (has_open2, has_closed2) == (has_open, has_closed)
    ok = same_as_plain
    if not ok:
        failures.append(f"RED-ALL-FLAG-UNSUPPORTED: exit={r.returncode} has_open={has_open2} "
                         f"has_closed={has_closed2} same_as_plain={same_as_plain}\n"
                         f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    print(f"RED-ALL-FLAG-UNSUPPORTED (reverted, --all passed but not recognized): exit={r.returncode} "
          f"open_item_shown={has_open2} closed_item_shown={has_closed2} "
          f"identical_to_plain_list={same_as_plain} -- {'PASS' if ok else 'FAIL'}")

    if failures:
        print(f"\nled-work-list-state-filter fixture: {len(failures)} FAILURE(S) -- scratch "
              f"substrate left standing as evidence:\n  tempdir: {tmpdir}\n  schema:  {SCHEMA} / "
              f"{KERN} / {ROLE} (db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nled-work-list-state-filter fixture: all cases PASS, scratch substrate torn down "
          f"to zero residue (tempdir removed, schema {SCHEMA}/{KERN}/role {ROLE} dropped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
