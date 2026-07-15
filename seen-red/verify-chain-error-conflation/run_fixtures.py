#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T22:27:59Z
#   last-change: 2026-07-12T22:28:14Z
#   contributors: 3c50e030/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof that bootstrap/templates/verify-chain.tmpl no longer
conflates "cannot connect to the database at all" with "connected fine, this world predates s26/
s27" (tracker item `verify-chain-error-conflation`, 2026-07-13).

THE DEFECT THIS CLOSES: `has_row_hash_layer()` and `has_high_water_layer()` are EXPLICIT
capability-check probes whose own docstrings already promised "an EXPLICIT capability check...
never a fuzzy match on error text: a real query bug must surface as ERROR, never be silently
miscategorized". Before this fix, both functions read `_psql_json_rows()`'s (rows, err) return
and computed `bool(rows) and rows[0].get("present") is True` -- and `bool(None)` is `False`, so a
QUERY THAT FAILED TO EXECUTE (connection refused, auth failed, timeout, a real query bug) was
silently read as "the column/table is absent", which `verify()` / `compare_witness()` then
reported as the honest, UNRELATED pre-s26/pre-s27 "nothing to verify here" case -- exactly the
two-different-world-states-collapsed-into-one-report ADR-0002 forbids. A verifier that could not
look must never report the benign absence it would have found if it HAD looked.

THE FIX: both capability-check functions now return `(present, err)` with `present is None`
distinguishing "the query itself failed" from `present is True/False` ("the query succeeded and
gave a real answer"). `verify()` surfaces a query failure on `has_row_hash_layer()` as the NEW,
DISTINCT top-level status CANNOT-VERIFY (exit 5, never UNAVAILABLE's exit 0). `compare_witness()`
surfaces a query failure on `has_high_water_layer()` into its ALREADY-DECLARED "ERROR" status
(the same one `read_high_water()` failing already used) -- fixed alongside: `main()`'s dispatch
previously let a witness-level ERROR fall through to `return 0` (the SAME exit code as a
fully-confirmed witness!) for the INTACT/EMPTY branches, and `--head` mode's witness check did not
handle ERROR at all (it would have SIGNED a head whose witness was never actually consulted). Both
are fixed here too -- found in reach of this fix, not routed around (CLAUDE.md's hazard rule).

Cases:
  a-connection-failure-is-cannot-verify -- `./verify-chain` against a deployment.json pointing at
                                 an unreachable host: exit 5, stdout says CANNOT-VERIFY (never
                                 UNAVAILABLE), and the printed reason carries psql's real stderr.
  b-head-refuses-on-cannot-verify -- `./verify-chain --head` against the same bad-host deployment:
                                 exit 1, stdout EMPTY, stderr names CANNOT-VERIFY as the reason
                                 signing was refused.
  c-has-high-water-layer-query-failure-is-error -- direct, in-process proof that
                                 `has_high_water_layer()` itself returns `(None, err)` (not a
                                 collapsed `False`) against the same unreachable host, and that
                                 `compare_witness()` reports "ERROR" (never "WITNESS-UNAVAILABLE")
                                 -- the sibling function the ledger item names ("same audit applies
                                 to has_high_water_layer() one function down").
  d-good-host-control -- the SAME world, reachable host: `./verify-chain` reports INTACT. Proves
                                 case a's failure is genuinely caused by the bad host, not some
                                 unrelated schema problem in the scaffolded world.
  e-pre-s26-honest-absence-preserved -- the OTHER polarity, the ledger item's own requirement: a
                                 genuinely pre-s26 world (s15..s25 applied, s26 withheld) still
                                 reports UNAVAILABLE (exit 0), never CANNOT-VERIFY -- the fix did
                                 not turn the honest degrade into a false alarm.

Usage: python3 seen-red/verify-chain-error-conflation/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Real infra throughout (a throwaway --new-world scaffold
plus a hand-applied pre-s26 schema, both torn down before AND after this file runs); the
connection-failure cases use a `.invalid` TLD hostname (RFC 2606 -- guaranteed never to resolve),
so the failure is a fast DNS-resolution error, never a 30s socket-timeout wait. Lazy imports
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
VERIFY_CHAIN_TMPL = REPO / "bootstrap" / "templates" / "verify-chain.tmpl"
LINEAGE = REPO / "kernel" / "lineage"

PGHOST, PGDB = fixture_pghost(), "toy"
BAD_HOST = "verify-chain-conflation-probe.invalid"  # RFC 2606 .invalid -- never resolves, ever
WORLD = "vccfxprobe"
PRES26_SCHEMA, PRES26_KERN, PRES26_ROLE = "vccfxpres26", "vccfxpres26_kernel", "vccfxpres26_rw"

CHAIN_TO_S25 = ["s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
                "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
                "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
                "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
                "s25-commission-kind.sql"]


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
                                (PRES26_SCHEMA, PRES26_KERN, PRES26_ROLE)):
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


def run_verify_chain(deployment_path: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PICKUP_DEPLOYMENT"] = str(deployment_path)
    return sh(["python3", str(VERIFY_CHAIN_TMPL), *extra], env=env)


def load_verify_chain_module():
    """Imports verify-chain.tmpl as an in-process module (its own docstring notes it executes IN
    PLACE, no copy) so cases can call `has_high_water_layer()` / `compare_witness()` directly with
    a hand-built dep object -- proving the FUNCTION-level fix, not just the whole-script exit code."""
    loader = SourceFileLoader("verify_chain_tmpl_under_test", str(VERIFY_CHAIN_TMPL))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def main() -> int:
    teardown_all()
    tmp = Path(tempfile.mkdtemp(prefix="vcc-seenred-"))
    world_dir = tmp / WORLD
    failures: list[str] = []

    try:
        # --- scaffold the real --new-world (full chain through s28, real rows) ------------------
        print(f"== scaffolding throwaway --new-world {WORLD} ==")
        r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", WORLD,
                "--db", PGDB, "--host", PGHOST])
        if r.returncode != 0:
            print("SCAFFOLD FAILED:", r.stdout[-1500:], r.stderr[-1500:])
            return 1
        for verb in ("led", "verify-chain"):
            (world_dir / verb).chmod(0o755)
        rl = sh(["bash", str(world_dir / "led"), "decision", "row one, via led"], cwd=str(world_dir))
        if rl.returncode != 0:
            print("led write FAILED:", rl.stdout, rl.stderr)
            return 1

        good_deployment = world_dir / "deployment.json"
        good_dep_json = json.loads(good_deployment.read_text(encoding="utf-8"))
        bad_deployment = tmp / "deployment-bad-host.json"
        bad_deployment.write_text(json.dumps({**good_dep_json, "host": BAD_HOST}), encoding="utf-8")

        # --- a: connection failure on the PRIMARY probe surfaces as CANNOT-VERIFY, exit 5 --------
        ra = run_verify_chain(bad_deployment)
        ok_a = (ra.returncode == 5
                and "CANNOT-VERIFY" in ra.stdout
                and "UNAVAILABLE" not in ra.stdout
                and BAD_HOST in ra.stdout)
        check("a-connection-failure-is-cannot-verify", ok_a,
              f"exit={ra.returncode} stdout={ra.stdout.strip()!r}", failures)

        # --- b: --head refuses to sign over a CANNOT-VERIFY chain, empty stdout -----------------
        rb = run_verify_chain(bad_deployment, "--head")
        ok_b = (rb.returncode == 1 and rb.stdout.strip() == ""
                and "CANNOT-VERIFY" in rb.stderr and "REFUSED" in rb.stderr)
        check("b-head-refuses-on-cannot-verify", ok_b,
              f"exit={rb.returncode} stdout={rb.stdout!r} stderr_excerpt={rb.stderr.strip()[:200]!r}",
              failures)

        # --- c: has_high_water_layer() itself returns (None, err); compare_witness() -> ERROR,
        # never WITNESS-UNAVAILABLE (the sibling conflation the ledger item names explicitly) -----
        mod = load_verify_chain_module()
        bad_dep = SimpleNamespace(**{**good_dep_json, "host": BAD_HOST})
        present, probe_err = mod.has_high_water_layer(bad_dep)
        w_status, w_detail = mod.compare_witness(bad_dep, 0)
        ok_c = (present is None and bool(probe_err)
                and w_status == "ERROR" and BAD_HOST in w_detail.get("reason", ""))
        check("c-has-high-water-layer-query-failure-is-error", ok_c,
              f"present={present!r} probe_err_nonempty={bool(probe_err)} w_status={w_status!r} "
              f"w_detail={w_detail}", failures)

        # --- d: control -- the SAME world over the real host is still INTACT ---------------------
        rd = run_verify_chain(good_deployment)
        ok_d = rd.returncode == 0 and rd.stdout.startswith("verify-chain: INTACT -- 1 row(s)")
        check("d-good-host-control", ok_d, rd.stdout.strip(), failures)

        # --- e: the OTHER polarity -- a genuinely pre-s26 world still degrades honestly to
        # UNAVAILABLE (exit 0), never CANNOT-VERIFY -- the fix must not turn the honest case into a
        # false alarm -------------------------------------------------------------------------
        print(f"== applying s15..s25 (NOT s26/s27) to {PRES26_SCHEMA} ==")
        rap = apply_lineage(PRES26_SCHEMA, PRES26_KERN, PRES26_ROLE, CHAIN_TO_S25)
        if rap.returncode != 0:
            print("APPLY FAILED:", rap.stdout[-1500:], rap.stderr[-1500:])
            return 1
        pres26_deployment = tmp / "deployment-pres26.json"
        pres26_deployment.write_text(json.dumps({
            "db": PGDB, "host": PGHOST, "schema": PRES26_SCHEMA, "kern": PRES26_KERN,
            "role": PRES26_ROLE, "name": PRES26_SCHEMA}), encoding="utf-8")
        re_ = run_verify_chain(pres26_deployment)
        ok_e = (re_.returncode == 0 and "UNAVAILABLE" in re_.stdout
                and "CANNOT-VERIFY" not in re_.stdout and "pre-s26" in re_.stdout)
        check("e-pre-s26-honest-absence-preserved", ok_e, re_.stdout.strip(), failures)

    finally:
        teardown_all()
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- verify-chain-error-conflation both-polarity proof (connection-failure "
          "-> CANNOT-VERIFY, distinct exit 5 / --head refuses over it / has_high_water_layer's "
          "sibling conflation closed the same way / good-host control still INTACT / pre-s26 "
          "honest UNAVAILABLE preserved), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
