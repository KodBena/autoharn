#!/usr/bin/env python3
"""run_fixtures -- both-polarity live proof for ledger item `led-review-gap-false-clean`
(gates/fixture_census.py REGISTRY entry "led-review-gap-false-clean", design/
BRIEF-LED-ERGONOMICS-BUNDLE-2026-08-06.md item 2, ledger rows 1087/1102 family).

THE ITEM: bare `led review-gap` used to read ONLY `/views/review_gap` (actor-keyed,
non-work-item review debt) -- silently empty whenever every outstanding gap was WORK-ITEM debt
(`/views/work_review_gap`), a hazard-class false-clean read: an operator/agent trusting the
empty output would conclude "no review debt" when `led work review-gap` alone showed otherwise.

THE FIX (`cmd_review_gap` in bootstrap/templates/led.tmpl): bare `led review-gap` now reads BOTH
`/views/review_gap` and `/views/work_review_gap`, labeling every row `gap_kind` ("actor" |
"work_item") rather than merging the two distinct shapes into one indistinguishable row (see
that function's own docstring for the one-line rationale against the brief's other offered
option, refuse-and-point-at-'led work review-gap'). This fixture also incidentally exercises
item 3's `review_status`/`reviewing_verdicts` enrichment (refuse-verdict-legibility,
`seen-red/refuse-verdict-legibility/run_fixtures.py` is that item's OWN dedicated fixture; this
one only asserts the field is present and "never-reviewed", not its full legibility surface).

CASES (all live subprocess runs against one real scratch deployment):

  ADOPT                 -- bootstrap/new-project.sh --profile tracker stands up an ISOLATED
                            scratch world (own boundary process, never the shared repo-root
                            one -- see this driver's own ADOPT comment for why).
  SEED                  -- one work item opened+claimed+closed dropped/--review-deferred (mints
                            work_review_gap debt for this item's own slug -- no actor-keyed
                            review_gap debt is deliberately minted).
  GREEN-BARE-SURFACES-WORK-DEBT -- `led review-gap` (the CURRENT, fixed code): the seeded slug's
                            close-row appears, gap_kind="work_item", review_status=
                            "never-reviewed".
  GREEN-WORK-SUBVERB-UNCHANGED  -- `led work review-gap` (unaffected sub-verb) ALSO shows the
                            same debt, confirming the bare verb's new coverage is additive, not a
                            reroute that silently drops the sub-verb's own contract.
  RED-BARE-WAS-FALSE-CLEAN -- the SAME scratch world read through a TARGETED-REVERTED standalone
                            copy of led.tmpl (only the `review-gap` dispatch line reverted to its
                            pre-fix `cmd_view(cfg, "review_gap", "after_id")` shape): bare
                            `review-gap` prints NOTHING even though the identical work-item debt
                            is present and `led work review-gap` (unreverted, run against the
                            SAME world) still shows it -- the reported defect, reproduced.

Usage: python3 seen-red/led-review-gap-false-clean/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
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

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own environment
# before any subprocess is spawned -- inherited by the whole process tree this fixture starts.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

# Claude Code's own stamp_intercept.py PreToolUse hook (hooks/stamp_intercept.py) rewrites the
# Bash-tool command that LAUNCHES this fixture into `export PGOPTIONS=<HMAC for the CALLING
# session's OWN wired cwd deployment>; python3 seen-red/.../run_fixtures.py` whenever cwd carries
# a deployment.json -- inherited by every subprocess this script spawns, which would otherwise
# stamp a SCRATCH world's writes with the WRONG world's secret and fail validation. Stripped
# here, once, at module scope, before any subprocess is spawned.
os.environ.pop("PGOPTIONS", None)

REPO = Path(__file__).resolve().parents[2]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LED_TMPL = REPO / "bootstrap" / "templates" / "led.tmpl"
PGHOST, DB = fixture_pghost(), "toy"
WORLD = "lrgfcfixture"
TAG = f"seen-red-led-review-gap-false-clean-{int(time.time())}"

# The CURRENT (post-fix) dispatch line for bare `review-gap`, and its pre-fix shape -- a
# TARGETED, single-line revert (the same house convention seen-red/led-work-list-state-filter/
# run_fixtures.py's own PRE_FIX_LIST_BODY uses), isolating ONLY the false-clean axis this item
# fixes, touching nothing else `cmd_review_gap`'s own commit also carries (item 3's legibility
# enrichment, the `_JSON_SURFACES` widening, the read-projection flags -- none of those are
# reverted here, this item's own RED case regards ONLY the false-clean behavior).
POST_FIX_LINE = '        return cmd_review_gap(cfg)\n'
PRE_FIX_LINE = '        return cmd_view(cfg, "review_gap", "after_id")\n'


def _make_reverted_copy(dest: Path) -> Path:
    text = LED_TMPL.read_text()
    replaced, n = text.replace(POST_FIX_LINE, PRE_FIX_LINE, 1), text.count(POST_FIX_LINE)
    if n != 1:
        raise RuntimeError(f"expected exactly ONE occurrence of the post-fix review-gap "
                            f"dispatch line, found {n} -- led.tmpl's own dispatch shape changed "
                            f"since this fixture was written")
    out = dest / "led-review-gap-false-clean-PREFIX.tmpl"
    out.write_text(replaced)
    out.chmod(0o755)
    return out


def _drop(name: str) -> None:
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=0", "-q",
                     "-c", f"DROP SCHEMA IF EXISTS {name} CASCADE;",
                     "-c", f"DROP SCHEMA IF EXISTS {name}_kernel CASCADE;",
                     "-c", f"DROP ROLE IF EXISTS {name}_rw;",
                     "-c", f"DROP ROLE IF EXISTS {name}_owner;"],
                    capture_output=True, text=True)


def _run(dest: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(dest / "autoharn"), *args], capture_output=True, text=True,
                           cwd=str(dest))


def _run_reverted(dest: Path, reverted: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["AUTOHARN"] = str(REPO)
    env["PICKUP_DEPLOYMENT"] = str(dest / "deployment.json")
    return subprocess.run(["python3", str(reverted), *args], capture_output=True, text=True,
                           cwd=str(dest), env=env)


def _kill_boundary(dest: Path) -> None:
    """See seen-red/led-read-projection-flags/run_fixtures.py's own docstring for the full
    rationale -- same helper, same reasoning, kept per-driver rather than factored into
    _fixture_env.py (a shared file two other builders may be touching this same session; a
    same-session shared-file edit is a collision risk this brief's own commit discipline warns
    against, and this helper is small enough that the duplication cost is low)."""
    pidfile = dest / ".autoharn-service.pid"
    if not pidfile.exists():
        return
    try:
        pid = int(pidfile.read_text().strip())
    except (ValueError, OSError):
        return
    try:
        os.kill(pid, 15)
    except OSError:
        return
    for _ in range(20):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.25)
    try:
        os.kill(pid, 9)
    except OSError:
        pass


def _jsonlines(text: str) -> list[dict]:
    return [json.loads(ln) for ln in text.splitlines() if ln.strip().startswith("{")]


class _Abort(Exception):
    """Local control-flow only (never escapes `main`) -- see the sibling fixture's identical
    class for the full rationale (avoids the bare-`SystemExit`-escapes-try/finally defect)."""


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    _drop(WORLD)
    try:
        # --------------------------------------------------------------------------------- ADOPT
        tmp = Path(tempfile.mkdtemp(prefix=f"{WORLD}-seenred-"))
        tmps.append(tmp)
        dest = tmp / WORLD
        r = subprocess.run(["bash", str(NEW_PROJECT), str(dest), "--profile", "tracker",
                             "--name", WORLD, "--db", DB, "--host", PGHOST],
                            capture_output=True, text=True)
        ok = r.returncode == 0 and (dest / "deployment.json").exists()
        if not ok:
            failures.append(f"ADOPT: exit={r.returncode}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
        print(f"ADOPT: new-project.sh --profile tracker exit={r.returncode} "
              f"deployment.json={(dest / 'deployment.json').exists()} -- {'PASS' if ok else 'FAIL'}")
        if not ok:
            raise _Abort

        reverted = _make_reverted_copy(tmp)

        # ---------------------------------------------------------------------------------- SEED
        slug = f"{TAG}-slug"
        r_open = _run(dest, "led", "work", "open", slug, "an item closed with deferred review")
        r_claim = _run(dest, "led", "work", "claim", slug)
        r_close = _run(dest, "led", "work", "close", slug, "dropped", "--review-deferred")
        ok = all(rr.returncode == 0 for rr in (r_open, r_claim, r_close))
        if not ok:
            failures.append(f"SEED: open={r_open.returncode} claim={r_claim.returncode} "
                             f"close={r_close.returncode}\n{r_open.stderr}\n{r_claim.stderr}\n"
                             f"{r_close.stderr}")
        print(f"SEED: open/claim/close(--review-deferred) ok={ok} -- {'PASS' if ok else 'FAIL'}")
        if not ok:
            raise _Abort

        # --------------------------------------------------------------- GREEN-BARE-SURFACES-WORK-DEBT
        r = _run(dest, "led", "review-gap")
        rows = _jsonlines(r.stdout)
        mine = [row for row in rows if row.get("slug") == slug]
        ok = (r.returncode == 0 and len(mine) == 1 and mine[0].get("gap_kind") == "work_item"
              and mine[0].get("review_status") == "never-reviewed")
        if not ok:
            failures.append(f"GREEN-BARE-SURFACES-WORK-DEBT: exit={r.returncode} mine={mine}\n"
                             f"ALL ROWS:\n{rows}\nSTDERR:\n{r.stderr}")
        print(f"GREEN-BARE-SURFACES-WORK-DEBT: exit={r.returncode} n_matching={len(mine)} "
              f"row={mine[0] if mine else None} -- {'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------- GREEN-WORK-SUBVERB-UNCHANGED
        r = _run(dest, "led", "work", "review-gap")
        rows = _jsonlines(r.stdout)
        mine = [row for row in rows if row.get("slug") == slug]
        ok = r.returncode == 0 and len(mine) == 1 and mine[0].get("review_status") == "never-reviewed"
        if not ok:
            failures.append(f"GREEN-WORK-SUBVERB-UNCHANGED: exit={r.returncode} mine={mine}\n"
                             f"STDERR:\n{r.stderr}")
        print(f"GREEN-WORK-SUBVERB-UNCHANGED: exit={r.returncode} n_matching={len(mine)} -- "
              f"{'PASS' if ok else 'FAIL'}")

        # ----------------------------------------------------------------- RED-BARE-WAS-FALSE-CLEAN
        r = _run_reverted(dest, reverted, "review-gap")
        rows = _jsonlines(r.stdout)
        mine = [row for row in rows if row.get("slug") == slug]
        false_clean = r.returncode == 0 and len(mine) == 0
        r_work_check = _run(dest, "led", "work", "review-gap")
        work_rows = _jsonlines(r_work_check.stdout)
        work_still_shows_it = any(row.get("slug") == slug for row in work_rows)
        ok = false_clean and work_still_shows_it
        if not ok:
            failures.append(f"RED-BARE-WAS-FALSE-CLEAN: exit={r.returncode} mine={mine} "
                             f"false_clean={false_clean} work_still_shows_it={work_still_shows_it}\n"
                             f"REVERTED STDOUT:\n{r.stdout}\nREVERTED STDERR:\n{r.stderr}")
        print(f"RED-BARE-WAS-FALSE-CLEAN: reverted-bare-exit={r.returncode} "
              f"reverted-bare-n_matching={len(mine)} false_clean={false_clean} "
              f"work-subverb-still-shows-debt={work_still_shows_it} -- {'PASS' if ok else 'FAIL'}")

    except _Abort:
        pass
    finally:
        if "dest" in locals():
            _kill_boundary(dest)
        _drop(WORLD)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print(f"\nled-review-gap-false-clean fixture: {len(failures)} FAILURE(S)")
        for f in failures:
            print(f"\n!! {f}")
        return 1
    print("\nled-review-gap-false-clean fixture: all cases PASS, scratch substrate torn down to "
          "zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
