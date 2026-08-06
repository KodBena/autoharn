#!/usr/bin/env python3
"""run_fixtures -- both-polarity live proof for ledger item `refuse-verdict-legibility`
(gates/fixture_census.py REGISTRY entry "refuse-verdict-legibility", design/
BRIEF-LED-ERGONOMICS-BUNDLE-2026-08-06.md item 3, ledger rows 1087/1102 family).

THE ITEM (orchestrator decision, the brief's own text): review-gap surfaces conflated
"reviewed-and-refused" with "never reviewed" -- both simply fail review_gap's/work_review_gap's
own discharge test (no un-superseded attest by a DISTINCT reviewer), so a bare row alone cannot
tell a defect that was reviewed and rejected apart from one nobody has looked at yet -- exactly
ADR-0008's fuzzy-matching of two distinct facts into one.

THE FIX (`_review_legibility_for`/`_review_verdicts_by_regards` in bootstrap/templates/
led.tmpl, applied by both `cmd_review_gap` -- bare `led review-gap` -- and `cmd_work_review_gap`
-- `led work review-gap`): every gap row now carries `review_status` ("never-reviewed" |
"reviewed-not-discharging") and, when reviewed, `reviewing_verdicts` (reviewer/verdict/
independence per un-superseded review). Built ENTIRELY from `/views/review_verdicts`
(kernel/lineage/s56-reservation-residue.sql's own general review-legibility surface), already
served -- no kernel/serving change, CLI presentation layer only (the item's own STOP-if-not-
derivable instruction; it WAS derivable, so no gap was routed to spec).

CASES (all live subprocess runs against one real scratch deployment):

  ADOPT                       -- bootstrap/new-project.sh --profile tracker, isolated substrate.
  SEED-NEVER-REVIEWED         -- work item A opened+claimed+closed dropped/--review-deferred,
                                  no review row written against its close row at all.
  SEED-REVIEWED-REFUSED       -- work item B, same close shape, THEN `led review <close_id>
                                  refuse self-review "..."` (authored by a SECOND registered
                                  principal -- segregation of duties refuses a same-actor review
                                  write outright, unconditional of verdict; independence=
                                  self-review because a --profile tracker scratch world writes
                                  UNSTAMPED, and a genuine technical/managerial/financial claim
                                  needs a verified stamp -- irrelevant to what THIS item tests,
                                  the review_status/reviewing_verdicts legibility surface, not
                                  independence semantics) -- a genuine review exists but its
                                  verdict is refuse, so it still fails the discharge test.
  GREEN-NEVER-REVIEWED        -- `led work review-gap`: item A's row carries review_status=
                                  "never-reviewed", no reviewing_verdicts key.
  GREEN-REVIEWED-NOT-DISCHARGING -- item B's row carries review_status="reviewed-not-
                                  discharging" and reviewing_verdicts naming the refuse verdict/
                                  independence actually written.
  GREEN-BARE-SAME-ENRICHMENT  -- bare `led review-gap` (item 2's own fix) applies the IDENTICAL
                                  enrichment to its gap_kind="work_item" rows -- not a second,
                                  divergent presentation.
  RED-WAS-CONFLATED           -- the SAME scratch world read through a TARGETED-REVERTED
                                  standalone copy of led.tmpl (`cmd_work_review_gap`'s own body
                                  reverted to its pre-item-3 unenriched print): items A and B
                                  print BYTE-IDENTICAL row shapes (no review_status key at all
                                  on either) -- the reported conflation, reproduced: a caller
                                  cannot tell them apart from the reverted output alone, though
                                  the unreverted `led show <close_id_B's review row>` proves a
                                  real review row exists for B and not for A.

Usage: python3 seen-red/refuse-verdict-legibility/run_fixtures.py
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

# Claude Code's own stamp_intercept.py PreToolUse hook rewrites the Bash-tool command that
# LAUNCHES this fixture to carry a PGOPTIONS export for the CALLING session's OWN wired
# deployment -- inherited by every subprocess here, which would otherwise stamp a scratch
# world's writes with the wrong secret. Stripped at module scope, before any subprocess spawns.
os.environ.pop("PGOPTIONS", None)

REPO = Path(__file__).resolve().parents[2]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LED_TMPL = REPO / "bootstrap" / "templates" / "led.tmpl"
PGHOST, DB = fixture_pghost(), "toy"
WORLD = "rvlfixture"
TAG = f"seen-red-refuse-verdict-legibility-{int(time.time())}"

# `cmd_work_review_gap`'s CURRENT (post-item-3) body vs. its pre-item-3 shape -- a targeted,
# whole-function-body revert (the same house convention seen-red/led-work-list-state-filter/
# run_fixtures.py's own PRE_FIX_LIST_BODY uses), isolating ONLY the legibility-enrichment axis.
_FUNC_RE = re.compile(
    r'def cmd_work_review_gap\(cfg: bcc\.ServedConfig\) -> int:\n.*?\n(?=\ndef cmd_work_startable)',
    re.DOTALL)
PRE_ITEM3_BODY = '''def cmd_work_review_gap(cfg: bcc.ServedConfig) -> int:
    """Ported off legacy-led.tmpl's `work review-gap` -- work_review_gap, item-keyed (s29's own
    sibling of the ACTOR-keyed top-level `led review-gap`), read via GET /views/work_review_gap
    (already in VIEW_REGISTRY, keyed on slug)."""
    rows = bcc.get_all_rows(cfg.base, "/views/work_review_gap", cursor="after_slug")
    for r in rows:
        print(json.dumps(r, sort_keys=True))
    return 0

'''


def _make_reverted_copy(dest: Path) -> Path:
    text = LED_TMPL.read_text()
    replaced, n = _FUNC_RE.subn(PRE_ITEM3_BODY, text, count=1)
    if n != 1:
        raise RuntimeError("could not locate cmd_work_review_gap's current body to revert -- "
                            "led.tmpl's own function shape changed since this fixture was written")
    out = dest / "refuse-verdict-legibility-PREFIX.tmpl"
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


def _run(dest: Path, *args: str, actor: str | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if actor is not None:
        env["LED_ACTOR"] = actor
    return subprocess.run([str(dest / "autoharn"), *args], capture_output=True, text=True,
                           cwd=str(dest), env=env)


def _run_reverted(dest: Path, reverted: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["AUTOHARN"] = str(REPO)
    env["PICKUP_DEPLOYMENT"] = str(dest / "deployment.json")
    return subprocess.run(["python3", str(reverted), *args], capture_output=True, text=True,
                           cwd=str(dest), env=env)


def _kill_boundary(dest: Path) -> None:
    """See seen-red/led-read-projection-flags/run_fixtures.py's own docstring for the full
    rationale -- same helper, kept per-driver (a shared-file edit two other builders may also be
    touching this same session is a collision risk out of proportion to this small duplication)."""
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
    """Local control-flow only (never escapes `main`) -- see the sibling fixtures' identical
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

        # ------------------------------------------------------------------- SEED-NEVER-REVIEWED
        slug_a = f"{TAG}-a"
        r1 = _run(dest, "led", "work", "open", slug_a, "never reviewed after close")
        r2 = _run(dest, "led", "work", "claim", slug_a)
        r3 = _run(dest, "led", "work", "close", slug_a, "dropped", "--review-deferred")
        ok_a = all(rr.returncode == 0 for rr in (r1, r2, r3))
        if not ok_a:
            failures.append(f"SEED-NEVER-REVIEWED: {r1.stderr}\n{r2.stderr}\n{r3.stderr}")
        print(f"SEED-NEVER-REVIEWED: open/claim/close ok={ok_a} -- {'PASS' if ok_a else 'FAIL'}")

        # ----------------------------------------------------------------- SEED-REVIEWED-REFUSED
        # kernel segregation of duties (a row's own author may not countersign it) refuses a
        # same-actor review write OUTRIGHT, unconditionally of verdict -- a distinct principal
        # registers and authors the refuse-verdict review below via LED_ACTOR.
        reviewer_name = f"{WORLD}-reviewer"
        r_reg = _run(dest, "led", "register-principal", reviewer_name, "human")
        slug_b = f"{TAG}-b"
        r4 = _run(dest, "led", "work", "open", slug_b, "reviewed and refused after close")
        r5 = _run(dest, "led", "work", "claim", slug_b)
        r6 = _run(dest, "led", "work", "close", slug_b, "dropped", "--review-deferred")
        ok_b_close = all(rr.returncode == 0 for rr in (r_reg, r4, r5, r6))
        # find close_id for slug_b via work_review_gap (unenriched-field-agnostic: close_id is
        # always present, pre- and post-item-3 alike).
        r_wrg = _run(dest, "led", "work", "review-gap")
        wrg_rows = _jsonlines(r_wrg.stdout)
        close_id_b = next((row["close_id"] for row in wrg_rows if row.get("slug") == slug_b), None)
        r7 = (_run(dest, "led", "review", str(close_id_b), "refuse", "self-review",
                    f"{TAG}: insufficient evidence, refused on purpose for this fixture",
                    actor=reviewer_name)
              if close_id_b is not None else None)
        ok_b = ok_b_close and close_id_b is not None and r7 is not None and r7.returncode == 0
        if not ok_b:
            failures.append(f"SEED-REVIEWED-REFUSED: reg={r_reg.returncode} "
                             f"ok_b_close={ok_b_close} close_id_b={close_id_b} "
                             f"review_rc={r7.returncode if r7 else None}\n"
                             f"{r_reg.stderr}\n{r4.stderr}\n{r5.stderr}\n{r6.stderr}\n"
                             f"{r7.stderr if r7 else ''}")
        print(f"SEED-REVIEWED-REFUSED: register-principal ok={r_reg.returncode == 0} "
              f"open/claim/close ok={ok_b_close} close_id_b={close_id_b} "
              f"review-refuse (as {reviewer_name}) ok={r7.returncode == 0 if r7 else False} -- "
              f"{'PASS' if ok_b else 'FAIL'}")
        if not (ok_a and ok_b):
            raise _Abort

        # ------------------------------------------------------------------- GREEN-NEVER-REVIEWED
        r = _run(dest, "led", "work", "review-gap")
        rows = _jsonlines(r.stdout)
        row_a = next((row for row in rows if row.get("slug") == slug_a), None)
        ok = (r.returncode == 0 and row_a is not None
              and row_a.get("review_status") == "never-reviewed"
              and "reviewing_verdicts" not in row_a)
        if not ok:
            failures.append(f"GREEN-NEVER-REVIEWED: exit={r.returncode} row_a={row_a}\n{r.stderr}")
        print(f"GREEN-NEVER-REVIEWED: exit={r.returncode} row_a={row_a} -- "
              f"{'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------ GREEN-REVIEWED-NOT-DISCHARGING
        row_b = next((row for row in rows if row.get("slug") == slug_b), None)
        verdicts = row_b.get("reviewing_verdicts") if row_b else None
        has_refuse = bool(verdicts) and any(
            v.get("verdict") == "refuse" and v.get("independence") == "self-review"
            for v in verdicts)
        ok = (row_b is not None and row_b.get("review_status") == "reviewed-not-discharging"
              and has_refuse)
        if not ok:
            failures.append(f"GREEN-REVIEWED-NOT-DISCHARGING: row_b={row_b}")
        print(f"GREEN-REVIEWED-NOT-DISCHARGING: row_b={row_b} -- {'PASS' if ok else 'FAIL'}")

        # --------------------------------------------------------------- GREEN-BARE-SAME-ENRICHMENT
        r = _run(dest, "led", "review-gap")
        bare_rows = _jsonlines(r.stdout)
        bare_b = next((row for row in bare_rows if row.get("slug") == slug_b), None)
        ok = (r.returncode == 0 and bare_b is not None
              and bare_b.get("gap_kind") == "work_item"
              and bare_b.get("review_status") == "reviewed-not-discharging")
        if not ok:
            failures.append(f"GREEN-BARE-SAME-ENRICHMENT: exit={r.returncode} bare_b={bare_b}\n"
                             f"{r.stderr}")
        print(f"GREEN-BARE-SAME-ENRICHMENT: exit={r.returncode} bare_b={bare_b} -- "
              f"{'PASS' if ok else 'FAIL'}")

        # ------------------------------------------------------------------------- RED-WAS-CONFLATED
        r = _run_reverted(dest, reverted, "work", "review-gap")
        reverted_rows = _jsonlines(r.stdout)
        rev_a = next((row for row in reverted_rows if row.get("slug") == slug_a), None)
        rev_b = next((row for row in reverted_rows if row.get("slug") == slug_b), None)
        no_status_field = (rev_a is not None and rev_b is not None
                            and "review_status" not in rev_a and "review_status" not in rev_b)
        indistinguishable = no_status_field and (set(rev_a.keys()) == set(rev_b.keys()))
        ok = r.returncode == 0 and indistinguishable
        if not ok:
            failures.append(f"RED-WAS-CONFLATED: exit={r.returncode} rev_a={rev_a} rev_b={rev_b}\n"
                             f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        print(f"RED-WAS-CONFLATED: exit={r.returncode} rev_a={rev_a} rev_b={rev_b} "
              f"indistinguishable={indistinguishable} -- {'PASS' if ok else 'FAIL'}")

    except _Abort:
        pass
    finally:
        if "dest" in locals():
            _kill_boundary(dest)
        _drop(WORLD)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print(f"\nrefuse-verdict-legibility fixture: {len(failures)} FAILURE(S)")
        for f in failures:
            print(f"\n!! {f}")
        return 1
    print("\nrefuse-verdict-legibility fixture: all cases PASS, scratch substrate torn down to "
          "zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
