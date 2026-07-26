#!/usr/bin/env python3
"""run_fixtures.py — both-polarity proof for gates/fixture_sweep.py (`autoharn fixture-sweep`,
work item fixture-live-sweep, ledger rows 1388/1389).

THREE CASES, all exercising gates/fixture_sweep.py IN-PROCESS (imported as a module, its
`fixture_census.REGISTRY` monkeypatched in memory the same way
seen-red/fixture-census/red-specimen.py already does for the census gate itself) rather than by
shelling out to a second `autoharn fixture-sweep` — this is also HOW THE RECURSION GUARD HOLDS:
this driver never shells out to a nested sweep, so an ordinary outer sweep that reaches the
"fixture-sweep" family and runs THIS file never recurses at all. gates/fixture_sweep.py's own
module docstring documents a second, independent, runtime guard (AUTOHARN_FIXTURE_SWEEP_ACTIVE)
as defense in depth in case a future edit to this driver ever did shell out.

  case_red_leg               a synthetic, deliberately-broken throwaway family (a temp script
                              that always exits 1) is run through `fixture_sweep.run_family`
                              directly — expect status RED, with the tail of its output captured
                              in `detail`. This is the RED evidence red.txt bank (below).
  case_unexercised_env_leg   a synthetic family whose fixture text declares a Postgres-host
                              dependency (the same textual marker `declares_pghost()` looks for)
                              is run with HARNESS_PGHOST/EPISTEMIC_PGHOST cleared and
                              LEDGER_DEPLOYMENT pointed at a path that does not exist, so
                              `pghost_available()` genuinely cannot resolve a host — expect
                              status UNEXERCISED, never RED, and the subprocess must never have
                              been spawned (the temp script, if it ran, would write a marker
                              file this case asserts does NOT exist).
  case_real_roster_leg       the REAL CLI path (`fixture_sweep.main`, not `run_family` directly)
                              against two real, fast, no-declared-env registry entries
                              (`09-relevant-act-classification`, `12-contemporaneity-degrade`) --
                              proves the whole argv -> classification -> summary path end to end
                              against genuine (non-synthetic) families, while staying cheap. Never
                              targets "fixture-sweep" itself (the recursion guard above is what
                              keeps this leg from ever needing to).

Usage: python3 seen-red/fixture-sweep/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
from pathlib import Path

os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"  # FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

sys.path.insert(0, str(REPO / "gates"))
import fixture_sweep  # gates/fixture_sweep.py -- the subject of this both-polarity proof

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}" + (f" -- {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(label)


def case_red_leg() -> None:
    print("case: red_leg -- a deliberately-broken throwaway family classifies RED")
    with tempfile.TemporaryDirectory(prefix="fixture-sweep-red-leg-") as td:
        broken = os.path.join(td, "always_fails.py")
        with open(broken, "w", encoding="utf-8") as f:
            f.write("import sys\n"
                    "print('deliberately-broken throwaway family -- proves the sweep can RED')\n"
                    "sys.exit(1)\n")
        res = fixture_sweep.run_family("deliberately-broken-throwaway", broken, timeout=30)
        check("status is RED", res.status == "RED", res.status)
        check("tail contains the throwaway's own marker text",
              "deliberately-broken throwaway family" in res.detail, res.detail[:200])
        check("exit code recorded in detail", "exit 1" in res.detail, res.detail[:200])
        return res


def case_unexercised_env_leg() -> None:
    print("case: unexercised_env_leg -- missing declared Postgres-host env classifies "
          "UNEXERCISED, never spawns the subprocess")
    with tempfile.TemporaryDirectory(prefix="fixture-sweep-unexercised-leg-") as td:
        marker_file = os.path.join(td, "ran.marker")
        needs_pghost = os.path.join(td, "needs_pghost.py")
        # the substring "pghost_resolve" is the ONLY thing declares_pghost() looks for -- this
        # file is deliberately never valid enough to actually run cleanly (it must never be
        # executed at all if the env pre-probe works); if it EVER runs, it writes marker_file,
        # which this case asserts does not exist afterward.
        with open(needs_pghost, "w", encoding="utf-8") as f:
            f.write("# declares a dependency the same way seen-red/_fixture_env.py's callers do:\n"
                    "# pghost_resolve.resolve_pghost('HARNESS_PGHOST', 'EPISTEMIC_PGHOST')\n"
                    f"open({marker_file!r}, 'w').close()  # must never execute\n")
        saved = {k: os.environ.pop(k, None) for k in
                 ("HARNESS_PGHOST", "EPISTEMIC_PGHOST", "LEDGER_DEPLOYMENT")}
        try:
            os.environ["LEDGER_DEPLOYMENT"] = os.path.join(td, "no-such-deployment.json")
            res = fixture_sweep.run_family("needs-pghost-throwaway", needs_pghost, timeout=30)
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v
                else:
                    os.environ.pop(k, None)
        check("status is UNEXERCISED", res.status == "UNEXERCISED", res.status)
        check("detail names the missing Postgres-host dependency",
              "Postgres-host" in res.detail, res.detail[:200])
        check("subprocess was never spawned (no marker file written)",
              not os.path.exists(marker_file), "marker file exists -- the subprocess ran")
        return res


def case_real_roster_leg() -> None:
    print("case: real_roster_leg -- the real CLI path against two genuine, fast, "
          "no-declared-env registry entries")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fixture_sweep.main([
            "--only", "09-relevant-act-classification",
            "--only", "12-contemporaneity-degrade",
            "--timeout", "120",
        ])
    out = buf.getvalue()
    print(out)
    check("exit code 0 or 1 (a real, meaningful classification, not a crash)", rc in (0, 1), str(rc))
    check("both families appear in the output",
          "09-relevant-act-classification" in out and "12-contemporaneity-degrade" in out, out[:300])
    check("summary line present", "fixture-sweep summary:" in out, out[-300:])
    check("never targets the fixture-sweep family itself (the recursion guard's own precondition)",
          "] fixture-sweep " not in out, out[:300])


if __name__ == "__main__":
    red_res = case_red_leg()
    case_unexercised_env_leg()
    case_real_roster_leg()

    if failures:
        print(f"run_fixtures: {len(failures)} FAILURE(S): {', '.join(failures)}")
        sys.exit(1)
    print("\nall cases GREEN")
    sys.exit(0)
