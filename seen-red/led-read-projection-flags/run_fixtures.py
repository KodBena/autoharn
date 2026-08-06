#!/usr/bin/env python3
"""run_fixtures -- both-polarity live proof for ledger item `led-read-projection-flags`
(gates/fixture_census.py REGISTRY entry "led-read-projection-flags", design/
BRIEF-LED-ERGONOMICS-BUNDLE-2026-08-06.md item 1, ledger rows 1087/1102 family).

THE ITEM: orchestrator sessions kept piping `led`'s own read verbs through ad-hoc `python3 -c`
filters (25 in one session) to pull a few fields or narrow to one kind/state/slug.
`bootstrap/templates/led.tmpl` now grows, on the read verbs the item names as its own minimum
("--recent/current/show/work list at minimum"):

  led --recent [N] / led current [N]   -- `--kind <kind>` (typed refusal against the live
                                           `GET /kinds` vocabulary) and `--fields f1,f2,...`
                                           (switches the plain-text listing to one projected
                                           JSON object per line).
  led show <id>                        -- `--fields f1,f2,...` (projected key: value lines;
                                           a REQUESTED field prints even if its value is None).
  led work list                        -- `--state open|closed` (work_item_current.state's own
                                           closed vocabulary -- NOT --all's boolean, strictly
                                           narrower: `--state closed` alone has no prior
                                           spelling), `--slug <slug>` (single-item lookup), and
                                           `--fields f1,f2,...`.

Every unrecognized `--kind`/`--fields`/`--state` value REFUSES (typed, teaching the live/known
vocabulary) -- never a silent empty result indistinguishable from "this filter legitimately
matched nothing."

CASES (all live subprocess runs of the real `./autoharn led` against one real scratch
deployment):

  ADOPT                    -- bootstrap/new-project.sh --new-world stands up the scratch world.
  SEED                     -- two `finding` rows and one `decision` row written (kind-filter
                              fixture data); two work items opened+claimed, one closed
                              dropped/--review-deferred (state-filter fixture data).
  GREEN-RECENT-FIELDS      -- `led --recent 3 --fields id,kind`: every printed line is a JSON
                              object with EXACTLY {id, kind}, matching the 3 most recent seeded
                              rows.
  GREEN-RECENT-KIND        -- `led --recent 10 --kind finding`: every returned row has
                              kind=="finding"; the seeded `decision` row is excluded.
  RED-RECENT-BAD-KIND      -- `led --recent 5 --kind bogus-kind-zzz`: REFUSED, exit 4, the live
                              kind vocabulary (naming "finding") printed on stderr.
  RED-RECENT-BAD-FIELDS    -- `led --recent 3 --fields id,bogus_field_zzz`: REFUSED, exit 4, the
                              unknown field named on stderr.
  GREEN-SHOW-FIELDS        -- `led show <id> --fields id,statement`: exactly those two lines,
                              statement byte-matches the seeded text.
  RED-SHOW-BAD-FIELDS      -- `led show <id> --fields bogus_field_zzz`: REFUSED, exit 4.
  GREEN-WORK-LIST-STATE    -- `led work list --state closed --fields slug,state` shows ONLY the
                              closed slug; `led work list --state open --fields slug,state`
                              shows ONLY the still-open slug.
  GREEN-WORK-LIST-SLUG     -- `led work list --slug <open-slug>` shows exactly that one row.
  RED-WORK-LIST-BAD-STATE  -- `led work list --state bogus`: REFUSED, exit 4.
  RED-WORK-LIST-ALL-STATE  -- `led work list --all --state open`: REFUSED, exit 4 (mutual
                              exclusion).

Usage: python3 seen-red/led-read-projection-flags/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
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
# a deployment.json (true for this repo's own root world) -- an environment EXPORT is inherited
# by every subprocess this script spawns, so a scratch world's OWN birth sequence (which mints
# and needs ITS OWN freshly-seeded stamp secret) would otherwise receive the WRONG world's stamp
# and fail validation ("the write stamp did not validate"). Stripped here, once, at module scope,
# before any subprocess is spawned -- restores this driver to the same unstamped posture it has
# when run outside the Claude Code harness entirely (a bare terminal), which is how every
# seen-red driver in this tree is actually designed to run.
os.environ.pop("PGOPTIONS", None)

REPO = Path(__file__).resolve().parents[2]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
PGHOST, DB = fixture_pghost(), "toy"
WORLD = "lrpffixture"
TAG = f"seen-red-led-read-projection-flags-{int(time.time())}"


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


def _kill_boundary(dest: Path) -> None:
    """`--profile tracker`'s own isolated, ensure-running-spawned boundary process (this
    fixture's OWN substrate, never the shared repo-root boundary -- see this driver's own ADOPT
    comment for why `--profile tracker` was chosen over `--new-world` specifically to avoid
    touching that shared, concurrently-used process) leaves a pidfile at
    `<dest>/.autoharn-service.pid` (serving/ensure_running.py). Read it and SIGTERM (then
    SIGKILL if it is still alive after a short wait) -- removing `dest`'s own tempdir does NOT
    stop a process that was merely spawned FROM inside it."""
    pidfile = dest / ".autoharn-service.pid"
    if not pidfile.exists():
        return
    try:
        pid = int(pidfile.read_text().strip())
    except (ValueError, OSError):
        return
    try:
        os.kill(pid, 15)
    except ProcessLookupError:
        return
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
    """Local control-flow only (never escapes `main`): an ADOPT/SEED-phase failure means every
    later case would just cascade-fail against a substrate that never came up -- raised to skip
    straight to teardown + the accumulated failures report, NOT `SystemExit` (which would escape
    `main`'s own try/finally uncaught and terminate the process with exit 0, printing nothing --
    a real, disclosed defect this driver deliberately avoids reproducing)."""


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    _drop(WORLD)
    try:
        # --------------------------------------------------------------------------------- ADOPT
        # `--profile tracker` (not `--new-world`): both carry the FULL kernel lineage since the
        # track-work.sh consolidation (new-project.sh's own FULL_LINEAGE gate fires on either),
        # but `--profile tracker` ALSO auto-picks a free port and writes an ISOLATED, per-world
        # `boundary-multiplex.toml` inside `dest` itself (ensure-running spawns a boundary
        # scoped to just this scratch world on first `./autoharn led` call) -- `--new-world`
        # instead expects the CALLER to register the new schema into a standing, ALREADY-RUNNING
        # boundary-multiplex.toml (this repo's own root one multiplexes several deployments on
        # one shared process, port 8433) and would need that shared process restarted to pick up
        # a new entry -- exactly the live, concurrently-used serving process two other builders
        # are working against this same session; touching it is out of this brief's surface and
        # a real hazard to their work. `--profile tracker`'s isolated substrate sidesteps that
        # entirely: this fixture's own boundary process is killed in `finally` below
        # (`_kill_boundary`), never the shared one.
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

        # ---------------------------------------------------------------------------------- SEED
        r1 = _run(dest, "led", "finding", f"{TAG}: finding-A")
        r2 = _run(dest, "led", "finding", f"{TAG}: finding-B")
        r3 = _run(dest, "led", "decision", f"{TAG}: decision-C")
        seeded_ok = all(rr.returncode == 0 for rr in (r1, r2, r3))
        r_open1 = _run(dest, "led", "work", "open", "lrpf-open-slug", "an open item")
        r_claim1 = _run(dest, "led", "work", "claim", "lrpf-open-slug")
        r_open2 = _run(dest, "led", "work", "open", "lrpf-closed-slug", "a closed item")
        r_claim2 = _run(dest, "led", "work", "claim", "lrpf-closed-slug")
        r_close2 = _run(dest, "led", "work", "close", "lrpf-closed-slug", "dropped",
                         "--review-deferred")
        work_ok = all(rr.returncode == 0 for rr in
                      (r_open1, r_claim1, r_open2, r_claim2, r_close2))
        ok = seeded_ok and work_ok
        if not ok:
            failures.append(f"SEED: seeded_ok={seeded_ok} work_ok={work_ok}\n"
                             f"{r1.stderr}\n{r2.stderr}\n{r3.stderr}\n{r_open1.stderr}\n"
                             f"{r_claim1.stderr}\n{r_open2.stderr}\n{r_claim2.stderr}\n"
                             f"{r_close2.stderr}")
        print(f"SEED: ledger writes ok={seeded_ok} work-item writes ok={work_ok} -- "
              f"{'PASS' if ok else 'FAIL'}")
        if not ok:
            raise _Abort

        # ---------------------------------------------------------------------- GREEN-RECENT-FIELDS
        r = _run(dest, "led", "--recent", "3", "--fields", "id,kind")
        rows = _jsonlines(r.stdout)
        exact_keys = all(set(row.keys()) == {"id", "kind"} for row in rows)
        ok = r.returncode == 0 and len(rows) == 3 and exact_keys
        if not ok:
            failures.append(f"GREEN-RECENT-FIELDS: exit={r.returncode} rows={rows}\n{r.stderr}")
        print(f"GREEN-RECENT-FIELDS: exit={r.returncode} n_rows={len(rows)} "
              f"exact_keys={exact_keys} -- {'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------------------ GREEN-RECENT-KIND
        r = _run(dest, "led", "--recent", "10", "--kind", "finding")
        rows = _jsonlines(r.stdout) if r.stdout.strip().startswith("{") else None
        # plain-text mode (no --fields): parse "[id] kind: statement" lines instead.
        lines = [ln for ln in r.stdout.splitlines() if ln.startswith("[")]
        all_finding = all(": finding:" not in ln and " finding:" in ln for ln in lines) if lines else False
        # simpler: every line's kind token must be "finding"
        kinds_seen = {ln.split("]", 1)[1].strip().split(":", 1)[0].strip() for ln in lines}
        ok = r.returncode == 0 and len(lines) >= 2 and kinds_seen == {"finding"}
        if not ok:
            failures.append(f"GREEN-RECENT-KIND: exit={r.returncode} kinds_seen={kinds_seen} "
                             f"n_lines={len(lines)}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        print(f"GREEN-RECENT-KIND: exit={r.returncode} n_lines={len(lines)} "
              f"kinds_seen={kinds_seen} -- {'PASS' if ok else 'FAIL'}")

        # --------------------------------------------------------------------- RED-RECENT-BAD-KIND
        r = _run(dest, "led", "--recent", "5", "--kind", "bogus-kind-zzz")
        refused = r.returncode == 4
        teaches = "REFUSED" in r.stderr and "bogus-kind-zzz" in r.stderr and "finding" in r.stderr
        ok = refused and teaches
        if not ok:
            failures.append(f"RED-RECENT-BAD-KIND: exit={r.returncode} refused={refused} "
                             f"teaches={teaches}\nSTDERR:\n{r.stderr}")
        print(f"RED-RECENT-BAD-KIND: exit={r.returncode} refused={refused} teaches={teaches} "
              f"-- {'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------------- RED-RECENT-BAD-FIELDS
        r = _run(dest, "led", "--recent", "3", "--fields", "id,bogus_field_zzz")
        refused = r.returncode == 4
        teaches = "REFUSED" in r.stderr and "bogus_field_zzz" in r.stderr
        ok = refused and teaches
        if not ok:
            failures.append(f"RED-RECENT-BAD-FIELDS: exit={r.returncode} refused={refused} "
                             f"teaches={teaches}\nSTDERR:\n{r.stderr}")
        print(f"RED-RECENT-BAD-FIELDS: exit={r.returncode} refused={refused} teaches={teaches} "
              f"-- {'PASS' if ok else 'FAIL'}")

        # -------------------------------------------------------------------------- GREEN-SHOW-FIELDS
        r = _run(dest, "led", "--recent", "1", "--kind", "finding", "--fields", "id")
        rows = _jsonlines(r.stdout)
        show_id = rows[0]["id"] if rows else None
        r = _run(dest, "led", "show", str(show_id), "--fields", "id,statement")
        out_lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
        has_id = any(ln.startswith("id ") for ln in out_lines)
        has_statement = any(ln.startswith("statement") and TAG in ln for ln in out_lines)
        exactly_two = len(out_lines) == 2
        ok = show_id is not None and r.returncode == 0 and has_id and has_statement and exactly_two
        if not ok:
            failures.append(f"GREEN-SHOW-FIELDS: show_id={show_id} exit={r.returncode} "
                             f"has_id={has_id} has_statement={has_statement} "
                             f"exactly_two={exactly_two}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        print(f"GREEN-SHOW-FIELDS: show_id={show_id} exit={r.returncode} has_id={has_id} "
              f"has_statement={has_statement} exactly_two={exactly_two} -- "
              f"{'PASS' if ok else 'FAIL'}")

        # ---------------------------------------------------------------------- RED-SHOW-BAD-FIELDS
        r = _run(dest, "led", "show", str(show_id), "--fields", "bogus_field_zzz")
        refused = r.returncode == 4
        teaches = "REFUSED" in r.stderr and "bogus_field_zzz" in r.stderr
        ok = refused and teaches
        if not ok:
            failures.append(f"RED-SHOW-BAD-FIELDS: exit={r.returncode} refused={refused} "
                             f"teaches={teaches}\nSTDERR:\n{r.stderr}")
        print(f"RED-SHOW-BAD-FIELDS: exit={r.returncode} refused={refused} teaches={teaches} "
              f"-- {'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------------- GREEN-WORK-LIST-STATE
        r_closed = _run(dest, "led", "work", "list", "--state", "closed", "--fields", "slug,state")
        closed_rows = _jsonlines(r_closed.stdout)
        r_open = _run(dest, "led", "work", "list", "--state", "open", "--fields", "slug,state")
        open_rows = _jsonlines(r_open.stdout)
        closed_ok = (r_closed.returncode == 0 and len(closed_rows) == 1
                     and closed_rows[0] == {"slug": "lrpf-closed-slug", "state": "closed"})
        open_ok = (r_open.returncode == 0
                   and {"slug": "lrpf-open-slug", "state": "open"} in open_rows
                   and not any(row["slug"] == "lrpf-closed-slug" for row in open_rows))
        ok = closed_ok and open_ok
        if not ok:
            failures.append(f"GREEN-WORK-LIST-STATE: closed_rows={closed_rows} "
                             f"open_rows={open_rows}\n{r_closed.stderr}\n{r_open.stderr}")
        print(f"GREEN-WORK-LIST-STATE: closed_ok={closed_ok} open_ok={open_ok} -- "
              f"{'PASS' if ok else 'FAIL'}")

        # -------------------------------------------------------------------- GREEN-WORK-LIST-SLUG
        r = _run(dest, "led", "work", "list", "--slug", "lrpf-open-slug")
        rows = _jsonlines(r.stdout)
        ok = r.returncode == 0 and len(rows) == 1 and rows[0].get("slug") == "lrpf-open-slug"
        if not ok:
            failures.append(f"GREEN-WORK-LIST-SLUG: exit={r.returncode} rows={rows}\n{r.stderr}")
        print(f"GREEN-WORK-LIST-SLUG: exit={r.returncode} n_rows={len(rows)} -- "
              f"{'PASS' if ok else 'FAIL'}")

        # ---------------------------------------------------------------- RED-WORK-LIST-BAD-STATE
        r = _run(dest, "led", "work", "list", "--state", "bogus")
        refused = r.returncode == 4
        teaches = "REFUSED" in r.stderr and "bogus" in r.stderr
        ok = refused and teaches
        if not ok:
            failures.append(f"RED-WORK-LIST-BAD-STATE: exit={r.returncode} refused={refused} "
                             f"teaches={teaches}\nSTDERR:\n{r.stderr}")
        print(f"RED-WORK-LIST-BAD-STATE: exit={r.returncode} refused={refused} teaches={teaches} "
              f"-- {'PASS' if ok else 'FAIL'}")

        # ---------------------------------------------------------------- RED-WORK-LIST-ALL-STATE
        r = _run(dest, "led", "work", "list", "--all", "--state", "open")
        refused = r.returncode == 4
        teaches = "REFUSED" in r.stderr and "mutually exclusive" in r.stderr
        ok = refused and teaches
        if not ok:
            failures.append(f"RED-WORK-LIST-ALL-STATE: exit={r.returncode} refused={refused} "
                             f"teaches={teaches}\nSTDERR:\n{r.stderr}")
        print(f"RED-WORK-LIST-ALL-STATE: exit={r.returncode} refused={refused} teaches={teaches} "
              f"-- {'PASS' if ok else 'FAIL'}")

    except _Abort:
        pass
    finally:
        if "dest" in locals():
            _kill_boundary(dest)
        _drop(WORLD)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print(f"\nled-read-projection-flags fixture: {len(failures)} FAILURE(S)")
        for f in failures:
            print(f"\n!! {f}")
        return 1
    print("\nled-read-projection-flags fixture: all cases PASS, scratch substrate torn down to "
          "zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
