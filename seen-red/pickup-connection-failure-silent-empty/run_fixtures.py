#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T01:43:21Z
#   last-change: 2026-07-14T01:43:21Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof that bootstrap/templates/pickup.tmpl no longer
conflates "cannot connect to the database at all" with "connected fine, this section has nothing
to report" (tracker item `pickup-connection-failure-silent-empty`, 2026-07-13).

THE DEFECT THIS CLOSES (ENT TESTBED FINDING 3, 2026-07-13): before this fix, `./pickup` against
an unreachable/unauthorized db printed a per-section "ERROR: <psql stderr>" line (from each of
IN-FORCE-DECISIONS / OPEN-QUESTIONS / REVIEW-DEBT / RECENT-CHANGES / RESOURCES / ESTIMATES /
TAXONOMIES / MAINTAINER-REVIEW-QUEUE / IN-FLIGHT / ROLLUP) yet `main()` UNCONDITIONALLY returned
0 regardless of any of those failures, and the actual OS-level process stderr stayed genuinely
empty (psql's stderr text was captured and printed to STDOUT inside each "ERROR:" line, never to
the process's own stderr) -- so a fresh session hydrating via the resumption doctrine
(CLAUDE.md) would see exit 0 and empty process stderr, a hydration brief indistinguishable, at
the process-exit-code level a caller actually checks, from "the tracker is genuinely empty" when
the truth is "pickup could not even look at it". This is the SAME defect class
`verify-chain-error-conflation` (fixed 2026-07-13, commit 8768a01) already closed one verb over
(has_row_hash_layer()/has_high_water_layer() silently reading a connection failure as the honest
pre-s26/pre-s27 schema-absence case).

THE FIX: a new `check_connectivity(dep) -> (ok, err)` probe (mirroring verify-chain.tmpl's own
(present, err) capability-check shape) runs ONE explicit `SELECT 1;` under `SET ROLE dep.role`
before ANY section is queried. On failure, `main()` prints a typed CANNOT-HYDRATE banner to
STDERR (loud, per ADR-0002) naming psql's real stderr verbatim, prints NOTHING to stdout (never
ten stale-looking per-section "ERROR:" lines masquerading as a brief), and exits 3 -- a code
distinct from `_load_deployment()`'s existing 2 (a config-level defect, diagnosed before any
network attempt) and from every section's own exit-0 "ran fine, found nothing" convention. A
GENUINE per-section absence (a pre-s22 kernel's work_item_current not existing yet) is UNCHANGED
by this fix -- it fires only AFTER check_connectivity() already proved the connection itself is
good, so it stays an honest section-level answer, never conflated with CANNOT-HYDRATE (case e).

Cases:
  a-connection-failure-is-cannot-hydrate -- `./pickup` against a deployment.json pointing at an
                                 unreachable host: exit 3, stdout EMPTY, stderr names
                                 CANNOT-HYDRATE and carries psql's real stderr with the host name.
  b-good-host-control -- the SAME scaffolded world, reachable host: exit 0, real section content
                                 printed (the IN-FORCE-DECISIONS row this fixture itself wrote via
                                 `led`), proving case a's failure is genuinely caused by the bad
                                 host, not an unrelated defect.
  c-check-connectivity-function-level -- direct, in-process proof that `check_connectivity()`
                                 itself returns (False, <psql stderr naming the bad host>) against
                                 the unreachable host, and (True, "") against the good host -- the
                                 function-level fix, not just the whole-script exit code.
  d-pre-s22-honest-absence-preserved -- a genuinely pre-s22 kernel (s15..s21 applied, s22
                                 withheld) over the SAME reachable host: `./pickup` still exits 0,
                                 the IN-FLIGHT section reports its own honest UNAVAILABLE text, and
                                 stdout carries no CANNOT-HYDRATE banner at all -- the fix must not
                                 turn a genuine section-level absence into a false connection alarm.

Usage: python3 seen-red/pickup-connection-failure-silent-empty/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Real infra throughout (a throwaway --new-world scaffold
plus a hand-applied pre-s22 schema, both torn down before AND after this file runs); the
connection-failure cases use a `.invalid` TLD hostname (RFC 2606 -- guaranteed never to resolve),
so the failure is a fast DNS-resolution error, never a 15s socket-timeout wait. Lazy imports
banned.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
PICKUP_TMPL = REPO / "bootstrap" / "templates" / "pickup.tmpl"
LINEAGE = REPO / "kernel" / "lineage"

PGHOST, PGDB = fixture_pghost(), "toy"
BAD_HOST = "pickup-conn-probe.invalid"  # RFC 2606 .invalid -- never resolves, ever
WORLD = "pcfsxprobe"
PRES22_SCHEMA, PRES22_KERN, PRES22_ROLE = "pcfsxpres22", "pcfsxpres22_kernel", "pcfsxpres22_rw"

CHAIN_TO_S21 = ["s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
                "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
                "s21-session-aware-distinctness.sql"]


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown_all() -> None:
    for schema, kern, role in ((WORLD, f"{WORLD}_kernel", f"{WORLD}_rw"),
                                (PRES22_SCHEMA, PRES22_KERN, PRES22_ROLE)):
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
            f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE; "
            f"DROP OWNED BY {role};"])
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {role};"])


def apply_lineage(schema: str, kern: str, role: str, files: list[str]) -> subprocess.CompletedProcess[str]:
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for f in files:
        args += ["-f", str(LINEAGE / f)]
    return sh(args)


def run_pickup(deployment_path: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PICKUP_DEPLOYMENT"] = str(deployment_path)
    return sh(["python3", str(PICKUP_TMPL)], env=env)


def load_pickup_module():
    """Imports pickup.tmpl as an in-process module (mirrors verify-chain-error-conflation's own
    fixture convention) so case c can call `check_connectivity()` directly with a hand-built dep
    object -- proving the FUNCTION-level fix, not just the whole-script exit code."""
    loader = SourceFileLoader("pickup_tmpl_under_test", str(PICKUP_TMPL))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def main() -> int:
    teardown_all()
    tmp = Path(tempfile.mkdtemp(prefix="pcfs-seenred-"))
    world_dir = tmp / WORLD
    failures: list[str] = []

    try:
        # --- scaffold the real --new-world (full chain, real rows) --------------------------
        print(f"== scaffolding throwaway --new-world {WORLD} ==")
        r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", WORLD,
                "--db", PGDB, "--host", PGHOST])
        if r.returncode != 0:
            print("SCAFFOLD FAILED:", r.stdout[-1500:], r.stderr[-1500:])
            return 1
        for verb in ("led", "pickup"):
            (world_dir / verb).chmod(0o755)
        rl = sh(["bash", str(world_dir / "led"), "decision", "row one, via led"], cwd=str(world_dir))
        if rl.returncode != 0:
            print("led write FAILED:", rl.stdout, rl.stderr)
            return 1

        good_deployment = world_dir / "deployment.json"
        good_dep_json = json.loads(good_deployment.read_text(encoding="utf-8"))
        bad_deployment = tmp / "deployment-bad-host.json"
        bad_deployment.write_text(json.dumps({**good_dep_json, "host": BAD_HOST}), encoding="utf-8")

        # --- a: connection failure -> CANNOT-HYDRATE, exit 3, stdout EMPTY -------------------
        ra = run_pickup(bad_deployment)
        ok_a = (ra.returncode == 3 and ra.stdout.strip() == ""
                and "CANNOT-HYDRATE" in ra.stderr and BAD_HOST in ra.stderr)
        check("a-connection-failure-is-cannot-hydrate", ok_a,
              f"exit={ra.returncode} stdout={ra.stdout!r} stderr_excerpt={ra.stderr.strip()[:250]!r}",
              failures)

        # --- b: control -- the SAME world over the real host still hydrates fully ------------
        rb = run_pickup(good_deployment)
        ok_b = (rb.returncode == 0 and "### SECTION: IN-FORCE-DECISIONS" in rb.stdout
                and "row one, via led" in rb.stdout and "CANNOT-HYDRATE" not in rb.stdout)
        check("b-good-host-control", ok_b,
              f"exit={rb.returncode} has_row={'row one, via led' in rb.stdout}", failures)

        # --- c: check_connectivity() itself returns (False, err) / (True, "") ----------------
        mod = load_pickup_module()
        bad_dep = SimpleNamespace(**{**good_dep_json, "host": BAD_HOST})
        good_dep = SimpleNamespace(**good_dep_json)
        ok_bad, err_bad = mod.check_connectivity(bad_dep)
        ok_good, err_good = mod.check_connectivity(good_dep)
        ok_c = (ok_bad is False and bool(err_bad) and BAD_HOST in err_bad
                and ok_good is True and err_good == "")
        check("c-check-connectivity-function-level", ok_c,
              f"bad=({ok_bad!r}, {err_bad!r}) good=({ok_good!r}, {err_good!r})", failures)

        # --- d: the OTHER polarity -- a genuinely pre-s22 world still hydrates (exit 0), IN-
        # FLIGHT reports its own honest UNAVAILABLE, never CANNOT-HYDRATE ---------------------
        print(f"== applying s15..s21 (NOT s22) to {PRES22_SCHEMA} ==")
        rap = apply_lineage(PRES22_SCHEMA, PRES22_KERN, PRES22_ROLE, CHAIN_TO_S21)
        if rap.returncode != 0:
            print("APPLY FAILED:", rap.stdout[-1500:], rap.stderr[-1500:])
            return 1
        pres22_deployment = tmp / "deployment-pres22.json"
        pres22_deployment.write_text(json.dumps({
            "db": PGDB, "host": PGHOST, "schema": PRES22_SCHEMA, "kern": PRES22_KERN,
            "role": PRES22_ROLE, "name": PRES22_SCHEMA}), encoding="utf-8")
        rd = run_pickup(pres22_deployment)
        ok_d = (rd.returncode == 0 and "CANNOT-HYDRATE" not in rd.stdout
                and "CANNOT-HYDRATE" not in rd.stderr
                and "UNAVAILABLE (no work-item layer" in rd.stdout)
        check("d-pre-s22-honest-absence-preserved", ok_d,
              f"exit={rd.returncode} stderr={rd.stderr.strip()[:200]!r}", failures)

    finally:
        teardown_all()
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- pickup-connection-failure-silent-empty both-polarity proof "
          "(connection-failure -> CANNOT-HYDRATE, distinct exit 3, empty stdout, loud stderr / "
          "good-host control still hydrates fully / check_connectivity() function-level proof / "
          "pre-s22 honest UNAVAILABLE preserved, never conflated with CANNOT-HYDRATE), zero "
          "residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
