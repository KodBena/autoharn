#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T07:55:59Z
#   last-change: 2026-07-14T22:24:19Z
#   contributors: e4410ef6/main, a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures -- both-polarity live proof for tracker item `content-free-review-audit`
(engine/review_gap_edb.py + engine/lp/review_gap_audit.lp + engine/review_gap_floor.py +
engine/review_gap_differential.py + engine/review_gap_audit.py, wired into `./audit --review-gap`
via engine/contemp_audit.py; plus bootstrap/templates/led.tmpl's `review` subcommand intake
tripwire). Mirrors seen-red/resource-intake-validation/run_fixtures.py's scratch-and-drop
pattern for the STANDING-deployment half (bootstrap/track-work.sh, real `led`/`audit` shims, no
mock) and seen-red/preamble-ordering/run_fixtures.py's two-schema GREEN/RED convention for the
marriage-differential half.

WITNESSED SPECIMEN driving this whole audit family: run12 ledger row 20 -- a `review` row whose
entire statement is `"test"` (4 chars), verdict=attest, independence=technical, regards=4,
written by the reviewer principal while syntax-testing against the LIVE ledger. Under
`<schema>.review_gap`'s discharge semantics (any unsuperseded, distinct-actor attest discharges;
content never examined) that junk row mechanically discharged row 4's countersign obligation.
Row 4 also received a genuine review later (row 22, 935 chars) but the discharge had already
fired via row 20 alone, and none of run12's six reviewer passes ever flagged it. This fixture
reproduces the SAME shape live, on a throwaway scratch deployment, both polarities, plus proves
the retroactive check run against the REAL run12 ledger separately (this file does not touch
run12 -- that check is read-only and reported by the commissioning agent directly, per the work
item's own instruction; this fixture is the SYNTHETIC both-polarity proof gates/fixture_census.py
requires).

TWO SCRATCH DEPLOYMENTS, ONE EACH POLARITY (schema names distinct so a stray leftover from one
never contaminates the other's differential):

  GREEN (schema cfraudg) -- an obligated row (`author`, obliged by `commissioner`) gets a
    GENUINE-length countersign from `reviewer`. `./led review` prints NO content-free warning;
    engine/review_gap_audit.py's report shows the discharge with an EMPTY `flagged` list;
    engine/review_gap_differential.py verdicts AGREE.

  RED (schema cfraudr) -- the SAME setup, but the countersign's statement is `"test"` (run12's
    own specimen, verbatim). `./led review` PROCEEDS (exit 0, the row IS written -- warn-only,
    never a refusal) but prints the content-free warning naming this audit family on stderr;
    engine/review_gap_audit.py's report shows the SAME row in `flagged`; engine/
    review_gap_differential.py STILL verdicts AGREE (the WORLD is red, i.e. it contains a
    genuine finding; the DIFFERENTIAL over that red world is a separate axis and stays green --
    the ASP and SQL producers agree bit-identically about what the world contains, exactly the
    seen-red/preamble-ordering precedent's own "RED world, GREEN differential" distinction).

NEGATIVE CONTROL -- a manufactured DIVERGE_DEFECT (the GREEN world, one forged atom injected into
the SQL floor's OWN RETURNED SET, in an isolated subprocess -- never touching either producer's
real source; the seen-red/preamble-ordering and seen-red/contemporaneity-audit precedent).

`./audit --review-gap` IS ALSO INVOKED, END-TO-END, AS A SUBPROCESS on both worlds to prove the
report text reaches the operator surface -- but its OWN EXIT CODE is not asserted against 0/6
here, named honestly: `bootstrap/track-work.sh` deliberately wires NO hooks (it stands up a
STANDING work-tracker, not a governed WORLD -- see that script's own "WHY NO HOOKS ARE WIRED"
section), so this scratch deployment carries no `invocations.jsonl` journal and `./audit`'s OWN
base verdict (Part 2, contemporaneity) refuses at exit 3 (N/A, capability-gated) REGARDLESS of
what `--review-gap` finds -- `--review-gap`'s own exit-6 addendum only fires when the base exit
is already 0 (engine/contemp_audit.py's own composition rule, "the first problem found stays the
reported one"), so exit 6 is UNEXERCISED through the full CLI on a standing (as opposed to
governed) deployment -- the concrete blocker being the same "no hooks wired here" fact, not a
defect in the composition logic. The composition logic ITSELF (build_report + the addendum
function only firing when nothing else already raised the exit) is witnessed directly in-process
below (DIRECT-EXIT-6), which is the actual unit under test -- exercising it through a governed
`new-project.sh` world's own hooks is a heavier setup out of this fixture's scope.

Scratch-only: schemas cfraudg/cfraudg_kernel (role cfraudg_rw) and cfraudr/cfraudr_kernel (role
cfraudr_rw), TOY db (192.168.122.1) -- both torn down (schema + tempdir) after a clean run, left
standing on a failure (the standing-probe convention every run_fixtures.py in this repo uses).

Usage: python3 seen-red/content-free-review-audit/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)

REPO = Path(__file__).resolve().parents[2]
TRACK_WORK = REPO / "bootstrap" / "track-work.sh"
ENGINE = REPO / "engine"
PGHOST, DB = fixture_pghost(), "toy"

# volatile substrings that differ run-to-run but carry no evidentiary content: scratch tmpdirs,
# derivation-record timestamp/hash stamps, and the worktree-vs-main-checkout path prefix ahead of
# the retained derivation path.
_VOLATILE_RES = (
    re.compile(r"/tmp/[\w.-]+"),
    re.compile(r"\d{8}T\d{6}Z_[0-9a-f]+"),
    re.compile(r"^.*?(?=engine/docs/ledger-marriage/)", re.MULTILINE),
)


def _normalize(text: str) -> str:
    for rx in _VOLATILE_RES:
        text = rx.sub("<VOLATILE>", text)
    return text


def _bank(path: Path, content: str) -> None:
    """Write CONTENT to PATH as banked seen-red evidence -- but only if it differs from what is
    already there beyond ordinary run-to-run churn (see _VOLATILE_RES). Left unconditional, this
    write dirtied the tree on every fixture run even when nothing substantive changed (11 tracked
    witness files, timestamp/run-id-only diffs, found in the 2026-07 release-audit sweep) --
    running a check should not dirty the tree it checks. A genuine content change (a real
    verdict/count/text difference) still writes through, so the file stays honest evidence rather
    than a stub frozen out of date."""
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing is not None and _normalize(existing) == _normalize(content):
        return
    path.write_text(content, encoding="utf-8")

SCHEMA_G, KERN_G, ROLE_G = "cfraudg", "cfraudg_kernel", "cfraudg_rw"
SCHEMA_R, KERN_R, ROLE_R = "cfraudr", "cfraudr_kernel", "cfraudr_rw"

GENUINE_STATEMENT = ("Confirmed: reviewed this decision's statement directly against the stated "
                    "criteria row; matches exactly, no discrepancies found.")  # 105 norm chars
CONTENT_FREE_STATEMENT = "test"  # run12's OWN specimen, verbatim

# `independence='self-review'` (NOT technical/managerial/financial), on BOTH worlds, for a
# mechanical reason named here rather than left to look like a labeling mistake: s17/s21's own
# validate_independence() trigger REFUSES a technical/managerial/financial claim unless the
# reviewing row carries a VERIFIED interception stamp -- and bootstrap/track-work.sh deliberately
# wires NO hooks (a STANDING deployment, not a governed WORLD; see that script's own "WHY NO
# HOOKS ARE WIRED"), so every write here is unstamped. `self-review` is the one independence
# value the trigger admits without a stamp -- it does NOT relax segregation-of-duties (the
# reviewer principal still must differ from the reviewed row's actor; validate_review()'s own
# check is unconditional), and review_gap's own discharge predicate never reads `independence`
# at all (only `verdict='attest'` and actor-distinctness), so this choice does not change what
# this fixture is proving.


def _psql(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, *args], capture_output=True, text=True)


def _drop_scratch(schema: str, kern: str, role: str) -> None:
    _psql("-v", "ON_ERROR_STOP=0", "-q",
          "-c", f"DROP SCHEMA IF EXISTS {schema} CASCADE;",
          "-c", f"DROP SCHEMA IF EXISTS {kern} CASCADE;",
          "-c", f"DROP ROLE IF EXISTS {role};")


def _run(dest: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run([str(dest / args[0]), *args[1:]],
                           capture_output=True, text=True, cwd=str(dest), env=full_env)


def _ledger_row_count(schema: str, role: str) -> int:
    r = _psql("-tAc", f"SET ROLE {role}; SELECT count(*) FROM {schema}.ledger;")
    return int(r.stdout.strip().splitlines()[-1])


def _last_review_id(schema: str, role: str) -> int:
    r = _psql("-tAc", f"SET ROLE {role}; SELECT max(id) FROM {schema}.ledger WHERE kind = 'review';")
    return int(r.stdout.strip().splitlines()[-1])


def adopt(dest: Path, name: str, schema: str, kern: str, role: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(TRACK_WORK), str(dest), "--name", name, "--db", DB,
                           "--host", PGHOST, "--schema", schema, "--kern", kern, "--role", role],
                          capture_output=True, text=True, cwd=str(REPO))


def obligate(dest: Path) -> subprocess.CompletedProcess:
    """`led obligate` DIRECTION per design/MAINT-REVIEW-GAP-SCOPE-SEMANTICS-RULING.md: the
    OBLIGED actor is `author` (the worker whose rows need outside eyes); `commissioner` assigns
    it. Never oblige `reviewer` -- the doctrine this whole file is downstream of."""
    return _run(dest, "led", "obligate", "content-free-review-audit-fixture",
               "commissioner", "author")


def review_gap_report(target: str, deployment_json: Path) -> dict:
    """In-process call into engine/review_gap_audit.build_report -- run with `engine/` on
    sys.path (the same convention every module under `engine/` uses: bare module names, no
    package). Isolated in a subprocess so this fixture's own sys.path/env never leaks into (or
    is polluted by) the real producer modules."""
    script = f"""
import os, sys, json
sys.path.insert(0, {str(ENGINE)!r})
os.environ["LEDGER_DEPLOYMENT"] = {str(deployment_json)!r}
from review_gap_audit import build_report

r = build_report({target!r})
print(json.dumps(r))
"""
    cp = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
    if cp.returncode != 0:
        raise RuntimeError(f"review_gap_report subprocess failed: {cp.stderr}")
    return json.loads(cp.stdout)


def run_differential(target: str, deployment_json: Path, retain: bool = False) -> tuple[int, str]:
    env = dict(os.environ)
    env["LEDGER_DEPLOYMENT"] = str(deployment_json)
    args = [sys.executable, str(ENGINE / "review_gap_differential.py"), target]
    if retain:
        args.append("--retain")
    cp = subprocess.run(args, capture_output=True, text=True, env=env, cwd=str(ENGINE))
    return cp.returncode, cp.stdout + cp.stderr


def run_audit_review_gap(dest: Path) -> tuple[int, str]:
    cp = subprocess.run([str(dest / "audit"), "--review-gap"], capture_output=True, text=True,
                        cwd=str(dest))
    return cp.returncode, cp.stdout + cp.stderr


def main() -> int:
    fails: list[str] = []
    log: list[str] = []
    ck = lambda cond, msg: fails.append(msg) if not cond else None  # noqa: E731

    _drop_scratch(SCHEMA_G, KERN_G, ROLE_G)
    _drop_scratch(SCHEMA_R, KERN_R, ROLE_R)
    tmpdir = Path(tempfile.mkdtemp(prefix="content-free-review-audit-fixture-"))
    dest_g, dest_r = tmpdir / "green", tmpdir / "red"

    try:
        # ============================================================================
        # GREEN WORLD
        # ============================================================================
        r = adopt(dest_g, SCHEMA_G, SCHEMA_G, KERN_G, ROLE_G)
        ok = r.returncode == 0 and (dest_g / "deployment.json").exists()
        ck(ok, f"GREEN ADOPT: exit={r.returncode}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        log.append(f"GREEN ADOPT: track-work.sh exit={r.returncode} -- {'PASS' if ok else 'FAIL'}")

        r = obligate(dest_g)
        ck(r.returncode == 0, f"GREEN OBLIGATE: exit={r.returncode}\nSTDERR:\n{r.stderr}")
        log.append(f"GREEN OBLIGATE: exit={r.returncode} -- {'PASS' if r.returncode == 0 else 'FAIL'}")

        before = _ledger_row_count(SCHEMA_G, ROLE_G)
        r = _run(dest_g, "led", "decision", "Ship the content-free-review-audit fixture.")
        ck(r.returncode == 0, f"GREEN decision insert: exit={r.returncode}\nSTDERR:\n{r.stderr}")
        target_row = int(_psql("-tAc",
            f"SET ROLE {ROLE_G}; SELECT max(id) FROM {SCHEMA_G}.ledger WHERE kind='decision';"
        ).stdout.strip().splitlines()[-1])
        log.append(f"GREEN: obliged row id={target_row} written")

        r_review = _run(dest_g, "led", "review", str(target_row), "attest", "self-review",
                        GENUINE_STATEMENT, env={"LED_ACTOR": "reviewer"})
        after = _ledger_row_count(SCHEMA_G, ROLE_G)
        no_warning = "content-free" not in r_review.stderr.lower() and "very short" not in r_review.stderr
        grew = after == before + 2  # +1 decision, +1 review
        ok = r_review.returncode == 0 and no_warning and grew
        ck(ok, f"GREEN review (genuine statement): exit={r_review.returncode} "
              f"no_warning={no_warning} before={before} after={after}\nSTDERR:\n{r_review.stderr}")
        log.append(f"GREEN review: exit={r_review.returncode} no-content-free-warning={no_warning} "
                  f"row-count before={before} after={after} -- {'PASS' if ok else 'FAIL'}")

        rg_review_id = _last_review_id(SCHEMA_G, ROLE_G)
        rep = review_gap_report(SCHEMA_G, dest_g / "deployment.json")
        discharged = [d for d in rep["discharges"] if d[0] == rg_review_id and d[1] == target_row]
        ck(bool(discharged), f"GREEN report: expected discharges to contain "
                             f"({rg_review_id},{target_row}); got {rep['discharges']}")
        ck(rg_review_id not in rep["flagged"], f"GREEN report: expected flagged=[] (or at least "
                                               f"NOT containing {rg_review_id}); got {rep['flagged']}")
        log.append(f"GREEN report: discharges contains ({rg_review_id},{target_row})="
                  f"{bool(discharged)}, flagged={rep['flagged']} (expected empty of "
                  f"{rg_review_id}) -- {'PASS' if bool(discharged) and rg_review_id not in rep['flagged'] else 'FAIL'}")

        diff_rc, green_diff_out = run_differential(SCHEMA_G, dest_g / "deployment.json", retain=True)
        ck(diff_rc == 0, f"GREEN differential expected exit 0 (AGREE): got {diff_rc}\n{green_diff_out}")
        ck("AGREE" in green_diff_out, f"GREEN differential expected AGREE: {green_diff_out}")
        log.append(f"GREEN differential: exit={diff_rc} AGREE={'AGREE' in green_diff_out} -- "
                  f"{'PASS' if diff_rc == 0 and 'AGREE' in green_diff_out else 'FAIL'}")

        audit_rc, green_audit_out = run_audit_review_gap(dest_g)
        flagged_none = "FLAGGED: none" in green_audit_out
        ck(flagged_none, f"GREEN ./audit --review-gap: expected 'FLAGGED: none' in report:\n{green_audit_out}")
        log.append(f"GREEN ./audit --review-gap: exit={audit_rc} (base exit is N/A/3 on this "
                  f"unwired STANDING deployment, named honestly -- see module docstring) "
                  f"'FLAGGED: none' present={flagged_none} -- {'PASS' if flagged_none else 'FAIL'}")

        # ============================================================================
        # RED WORLD
        # ============================================================================
        r = adopt(dest_r, SCHEMA_R, SCHEMA_R, KERN_R, ROLE_R)
        ok = r.returncode == 0 and (dest_r / "deployment.json").exists()
        ck(ok, f"RED ADOPT: exit={r.returncode}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        log.append(f"RED ADOPT: track-work.sh exit={r.returncode} -- {'PASS' if ok else 'FAIL'}")

        r = obligate(dest_r)
        ck(r.returncode == 0, f"RED OBLIGATE: exit={r.returncode}\nSTDERR:\n{r.stderr}")
        log.append(f"RED OBLIGATE: exit={r.returncode} -- {'PASS' if r.returncode == 0 else 'FAIL'}")

        before = _ledger_row_count(SCHEMA_R, ROLE_R)
        r = _run(dest_r, "led", "decision", "Ship the content-free-review-audit fixture (red twin).")
        ck(r.returncode == 0, f"RED decision insert: exit={r.returncode}\nSTDERR:\n{r.stderr}")
        target_row = int(_psql("-tAc",
            f"SET ROLE {ROLE_R}; SELECT max(id) FROM {SCHEMA_R}.ledger WHERE kind='decision';"
        ).stdout.strip().splitlines()[-1])
        log.append(f"RED: obliged row id={target_row} written")

        # THE SPECIMEN, VERBATIM: run12 row 20's own 4-char statement.
        r_review = _run(dest_r, "led", "review", str(target_row), "attest", "self-review",
                        CONTENT_FREE_STATEMENT, env={"LED_ACTOR": "reviewer"})
        after = _ledger_row_count(SCHEMA_R, ROLE_R)
        has_warning = ("content-free-review-audit" in r_review.stderr
                      and "review-gap" in r_review.stderr and "WARNING" in r_review.stderr)
        grew = after == before + 2  # the write PROCEEDS -- warn-only, never a refusal
        ok = r_review.returncode == 0 and has_warning and grew
        ck(ok, f"RED review (content-free statement 'test'): exit={r_review.returncode} "
              f"has_warning={has_warning} before={before} after={after}\nSTDERR:\n{r_review.stderr}")
        log.append(f"RED review: exit={r_review.returncode} content-free-warning-present="
                  f"{has_warning} row-count before={before} after={after} (write proceeded, "
                  f"never refused) -- {'PASS' if ok else 'FAIL'}")
        log.append("--- led review (content-free statement) stderr ---")
        log.append(r_review.stderr.strip())
        log.append("--- end stderr ---")

        rg_review_id = _last_review_id(SCHEMA_R, ROLE_R)
        rep = review_gap_report(SCHEMA_R, dest_r / "deployment.json")
        discharged = [d for d in rep["discharges"] if d[0] == rg_review_id and d[1] == target_row]
        flagged_ok = rg_review_id in rep["flagged"]
        ck(bool(discharged), f"RED report: expected discharges to contain "
                             f"({rg_review_id},{target_row}); got {rep['discharges']}")
        ck(flagged_ok, f"RED report: expected flagged to contain {rg_review_id}; got {rep['flagged']}")
        log.append(f"RED report: discharges contains ({rg_review_id},{target_row})="
                  f"{bool(discharged)}, flagged contains {rg_review_id}={flagged_ok} -- "
                  f"{'PASS' if bool(discharged) and flagged_ok else 'FAIL'}")

        diff_rc, red_diff_out = run_differential(SCHEMA_R, dest_r / "deployment.json", retain=True)
        ck(diff_rc == 0, f"RED differential expected exit 0 (AGREE -- the WORLD is red, the "
                        f"DIFFERENTIAL over it is still bit-identical, GREEN): got {diff_rc}\n{red_diff_out}")
        ck("AGREE" in red_diff_out, f"RED differential expected AGREE: {red_diff_out}")
        log.append(f"RED differential: exit={diff_rc} AGREE={'AGREE' in red_diff_out} -- "
                  f"{'PASS' if diff_rc == 0 and 'AGREE' in red_diff_out else 'FAIL'}")

        audit_rc, red_audit_out = run_audit_review_gap(dest_r)
        flagged_present = f"FLAGGED" in red_audit_out and str(rg_review_id) in red_audit_out
        ck(flagged_present, f"RED ./audit --review-gap: expected FLAGGED to name row "
                            f"{rg_review_id} in report:\n{red_audit_out}")
        log.append(f"RED ./audit --review-gap: exit={audit_rc} (base exit is N/A/3 on this "
                  f"unwired STANDING deployment, named honestly -- see module docstring) "
                  f"FLAGGED names row {rg_review_id}={flagged_present} -- "
                  f"{'PASS' if flagged_present else 'FAIL'}")

        # ============================================================================
        # DIRECT-EXIT-6 -- the exit-code COMPOSITION LOGIC itself (engine/review_gap_audit.
        # review_gap_exit_addendum), witnessed in-process against the RED world's own real
        # report: a clean base exit (simulated at 0, exactly the condition engine/contemp_audit.py
        # checks before calling this function) PLUS >=1 flagged row raises to 6. See module
        # docstring for why the FULL `./audit` CLI cannot reach exit 6 on this unwired STANDING
        # deployment (the base verdict refuses at 3 first) -- this is the addendum function's own
        # logic, the actual unit under test, exercised directly rather than through a heavier
        # governed-world setup.
        # ============================================================================
        addendum_script = f"""
import sys
sys.path.insert(0, {str(ENGINE)!r})
from review_gap_audit import review_gap_exit_addendum
rep = {json.dumps(rep)!r}
import json
rep = json.loads(rep)
print(review_gap_exit_addendum(rep))
"""
        cp = subprocess.run([sys.executable, "-c", addendum_script], capture_output=True, text=True)
        addendum_ok = cp.returncode == 0 and cp.stdout.strip() == "6"
        ck(addendum_ok, f"DIRECT-EXIT-6: expected review_gap_exit_addendum(RED report) == 6; "
                        f"got stdout={cp.stdout!r} stderr={cp.stderr!r}")
        log.append(f"DIRECT-EXIT-6: review_gap_exit_addendum(RED report) == 6 -- "
                  f"{'PASS' if addendum_ok else 'FAIL'} (raw: {cp.stdout.strip()!r})")

        # ============================================================================
        # NEGATIVE CONTROL -- manufactured DIVERGE_DEFECT (the GREEN world, one forged atom in
        # the SQL floor's own returned set, in an ISOLATED subprocess -- never touching either
        # producer's real source; seen-red/preamble-ordering's own precedent).
        # ============================================================================
        neg_script = f"""
import os, sys
sys.path.insert(0, {str(ENGINE)!r})
os.environ["LEDGER_DEPLOYMENT"] = {str(dest_g / "deployment.json")!r}
import review_gap_differential as rgd
res = rgd.run_differential({SCHEMA_G!r}, sql_atoms_override={{"flagged(999999)"}})
rgd.print_result(res)
print()
print("VERDICT:", res.verdict())
sys.exit(0 if res.verdict() == "AGREE" else 1)
"""
        cp = subprocess.run([sys.executable, "-c", neg_script], capture_output=True, text=True)
        diverge_out = cp.stdout + cp.stderr
        neg_ok = cp.returncode == 1 and "DIVERGE_DEFECT" in diverge_out
        ck(neg_ok, f"NEGATIVE CONTROL: expected exit 1 + DIVERGE_DEFECT: got {cp.returncode}\n{diverge_out}")
        log.append(f"NEGATIVE CONTROL: exit={cp.returncode} DIVERGE_DEFECT present="
                  f"{'DIVERGE_DEFECT' in diverge_out} -- {'PASS' if neg_ok else 'FAIL'}")

        # Filenames mirror seen-red/preamble-ordering/'s own naming convention exactly
        # (differential-agree-{green,red}.txt / differential-diverge-defect.txt / {green,red}-
        # report.txt) -- this also satisfies gates/fixture_census.py's red-evidence check, which
        # looks for a file ending literally in "-red.txt" (differential-agree-red.txt qualifies).
        _bank(Path(__file__).resolve().parent / "differential-agree-green.txt", green_diff_out)
        _bank(Path(__file__).resolve().parent / "differential-agree-red.txt", red_diff_out)
        _bank(Path(__file__).resolve().parent / "differential-diverge-defect.txt", diverge_out)
        _bank(Path(__file__).resolve().parent / "green-report.txt", green_audit_out)
        _bank(Path(__file__).resolve().parent / "red-report.txt", red_audit_out)

    finally:
        pass

    if fails:
        print("# CONTENT-FREE-REVIEW-AUDIT FIXTURES: FAILED")
        for line in log:
            print(f"  {line}")
        print()
        for f in fails:
            print(f"!! {f}")
        print(f"\n(scratch substrate left standing for inspection: tempdir={tmpdir}\n"
             f" schemas: {SCHEMA_G}/{KERN_G}/{ROLE_G}, {SCHEMA_R}/{KERN_R}/{ROLE_R})")
        return 1

    _drop_scratch(SCHEMA_G, KERN_G, ROLE_G)
    _drop_scratch(SCHEMA_R, KERN_R, ROLE_R)
    shutil.rmtree(tmpdir, ignore_errors=True)
    print("# CONTENT-FREE-REVIEW-AUDIT FIXTURES: ALL GREEN")
    for line in log:
        print(f"  {line}")
    print(f"\n  banked: {Path(__file__).resolve().parent}/"
         f"differential-agree-{{green,red}}.txt, differential-diverge-defect.txt, "
         f"{{green,red}}-report.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
