#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s30-typed-dependency-edges.sql
(design/FABLE-OBLIGATION-DEPENDENT-TYPING-SPEC.md, Fable-reviewed-and-adopted, RATIFIED
2026-07-15, ledger decision row 1018) + bootstrap/templates/led.tmpl's `work depends --type`
flag. Real infra, no mocks: a throwaway `--new-world` scaffold in the toy db, which now applies
the FULL s15..s30 birth chain automatically (s30 wired into new-project.sh's own LINEAGE_CHAIN by
this same commission) -- torn down before AND after this file runs so re-running it never leaves
residue. A second, SEPARATE scaffold pinned to s15..s29 (s30 deliberately NOT in its birth chain)
proves the legacy/migration case (case i below), with s30 applied on top afterward, mirroring a
real `./migrate` step by hand.

Cases (spec sec-5's four acceptance bullets, plus the structural refusals sec-2/sec-4 name):
  a-blocks-close-self-edge-refused    -- a blocks-close self-edge is refused at construction.
  b-informs-self-edge-allowed         -- an informs self-edge is allowed (s22's original, byte-
                                          identical unrefined posture -- unchanged by this delta).
  c-blocks-close-dangling-refused     -- a blocks-close edge naming an unopened antecedent is
                                          refused (both endpoints must be close-tracked items).
  d-informs-dangling-allowed          -- an informs edge naming an unopened antecedent is allowed
                                          (s22's original posture, unchanged).
  e-blocks-close-cycle-refused        -- sec-5 bullet 1, first half: a blocks-close cycle (X->Y,
                                          Y->X) is refused at write time, naming the would-be cycle.
  f-informs-cycle-allowed             -- sec-5 bullet 1, second half: the SAME shape as (e), typed
                                          informs instead, is allowed (informs never gates, so a
                                          cycle in it is not a structural hazard).
  g-blocks-close-child-blocks-strict  -- sec-5 bullet 2, first half: an interior item with one
                                          unresolved blocks-close child cannot strict-close (Element
                                          C refusal fires, naming the leaf).
  h-informs-child-does-not-block      -- sec-5 bullet 2, second half: the IDENTICAL structural setup
                                          (an unresolved child dependency), typed informs instead of
                                          blocks-close, lets the SAME strict close SUCCEED -- proving
                                          the TYPE, not the mere edge, gates.
  i-legacy-edge-reads-informs         -- RETIRED (cli-rebase-fixture-repairs, ledger row 1170):
                                          used to prove a work_depends_on edge authored on a
                                          PRE-s30 kernel stays edge_type IS NULL forever once s30
                                          is migrated on top, reading as informs by omission and
                                          never retroactively blocking a strict close. Authoring
                                          that edge needed a WORKING `led work open/claim/depends`
                                          on a classic s15..s29 world (deliberately never carrying
                                          s40/s43 either, an accident of that scaffold's own
                                          age) -- the served `led` is s43-only, so there is no
                                          tool left to author it through. Reproducing the exact
                                          rows by hand (a raw INSERT AS the role, still privileged
                                          pre-s43) was considered and rejected here: it would
                                          duplicate led.tmpl's own current payload shape into a
                                          second, hand-maintained copy for one retired-transport
                                          case (ADR-0012 P1) rather than exercising the real tool.
                                          The delta's own STATIC claim (a NULL edge_type reads as
                                          informs by omission, WHERE clause `edge_type =
                                          'blocks-close'` never matches NULL) is a plain SQL fact,
                                          not itself in question -- retired as a LIVE case, not
                                          silently dropped from the case list.
  j-reserved-word-supersedes-refused  -- `led work depends ... --type supersedes` is refused at the
                                          `led` boundary (the REVIEW NOTE DISPOSITION: supersedes is
                                          a reserved word, not a legal edge_type value).

Usage: python3 seen-red/s30-typed-dependency-edges/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
S30_DELTA = REPO / "kernel" / "lineage" / "s30-typed-dependency-edges.sql"

sys.path.insert(0, str(REPO / "seen-red"))  # for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

# cli-rebase-fixture-repairs (ledger row 1170): REUSE (ADR-0012 P1) serve_existing_world from
# seen-red/boundary-service/run_fixtures.py -- the served `led` shim refuses every write until
# this deployment.json gains boundary_url/boundary_deployment.
_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", REPO / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)

PGHOST, PGDB = fixture_pghost(), "toy"
WORLD = "s30fxprobe"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown(world: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {world} CASCADE; DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "
        f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def teardown_all() -> None:
    teardown(WORLD)


def led(world_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return sh(["bash", str(world_dir / "led"), *args], cwd=str(world_dir))


def psql_tuples(sql: str) -> subprocess.CompletedProcess[str]:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])


def scaffold(world: str) -> tuple[Path, dict, subprocess.Popen]:
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", world,
            "--db", PGDB, "--host", PGHOST])
    if r.returncode != 0:
        raise RuntimeError(f"SCAFFOLD FAILED ({world}): {r.stdout[-1500:]} {r.stderr[-1500:]}")
    for verb in ("led", "judge", "pickup"):
        p = world_dir / verb
        if p.exists():
            p.chmod(0o755)
    proc = bs_fixtures.serve_existing_world(world_dir / "deployment.json", tmp)
    dep = json.loads((world_dir / "deployment.json").read_text(encoding="utf-8"))
    return world_dir, dep, proc


def main() -> int:
    teardown_all()
    failures: list[str] = []
    tmps: list[Path] = []

    try:
        print(f"== scaffolding throwaway --new-world {WORLD} (full s15..s30 birth chain) ==")
        world_dir, dep, proc = scaffold(WORLD)
        tmps.append(world_dir.parent)
        schema, kern, role = dep["schema"], dep["kern"], dep["role"]
        print(f"  scaffold OK (schema={schema} kern={kern} role={role}).\n")

        # --- a/b: self-edge, blocks-close refused / informs allowed ----------------------------
        led(world_dir, "work", "open", "self-a", "SelfA")
        ra_ = led(world_dir, "work", "depends", "self-a", "self-a", "--type", "blocks-close")
        out_a = ra_.stdout + ra_.stderr
        ok_a = ra_.returncode != 0 and "self-edge" in out_a
        check("a-blocks-close-self-edge-refused", ok_a,
              f"exit={ra_.returncode} excerpt={out_a.strip()[-300:]!r}", failures)

        led(world_dir, "work", "open", "self-b", "SelfB")
        rb_ = led(world_dir, "work", "depends", "self-b", "self-b", "--type", "informs")
        ok_b = rb_.returncode == 0
        check("b-informs-self-edge-allowed", ok_b,
              f"exit={rb_.returncode} stderr_tail={(rb_.stdout + rb_.stderr).strip()[-200:]!r}", failures)

        # --- c/d: dangling antecedent, blocks-close refused / informs allowed ------------------
        led(world_dir, "work", "open", "dangle-c", "DangleC")
        rc_ = led(world_dir, "work", "depends", "dangle-c", "never-opened-c", "--type", "blocks-close")
        out_c = rc_.stdout + rc_.stderr
        ok_c = rc_.returncode != 0 and "no opening act" in out_c
        check("c-blocks-close-dangling-refused", ok_c,
              f"exit={rc_.returncode} excerpt={out_c.strip()[-300:]!r}", failures)

        led(world_dir, "work", "open", "dangle-d", "DangleD")
        rd_ = led(world_dir, "work", "depends", "dangle-d", "never-opened-d", "--type", "informs")
        ok_d = rd_.returncode == 0
        check("d-informs-dangling-allowed", ok_d,
              f"exit={rd_.returncode} stderr_tail={(rd_.stdout + rd_.stderr).strip()[-200:]!r}", failures)

        # --- e/f: cycle, blocks-close refused / informs allowed (sec-5 bullet 1) ---------------
        led(world_dir, "work", "open", "cyc-e-x", "CycEX")
        led(world_dir, "work", "open", "cyc-e-y", "CycEY")
        led(world_dir, "work", "depends", "cyc-e-x", "cyc-e-y", "--type", "blocks-close")
        re_ = led(world_dir, "work", "depends", "cyc-e-y", "cyc-e-x", "--type", "blocks-close")
        out_e = re_.stdout + re_.stderr
        ok_e = re_.returncode != 0 and "cycle" in out_e
        check("e-blocks-close-cycle-refused", ok_e,
              f"exit={re_.returncode} excerpt={out_e.strip()[-350:]!r}", failures)

        led(world_dir, "work", "open", "cyc-f-x", "CycFX")
        led(world_dir, "work", "open", "cyc-f-y", "CycFY")
        led(world_dir, "work", "depends", "cyc-f-x", "cyc-f-y", "--type", "informs")
        rf_ = led(world_dir, "work", "depends", "cyc-f-y", "cyc-f-x", "--type", "informs")
        ok_f = rf_.returncode == 0
        check("f-informs-cycle-allowed", ok_f,
              f"exit={rf_.returncode} stderr_tail={(rf_.stdout + rf_.stderr).strip()[-200:]!r}", failures)

        # --- g/h: an unresolved child blocks strict close when blocks-close, does NOT when
        # informs -- the SAME structural shape, only the type differs (sec-5 bullet 2) -----------
        led(world_dir, "work", "open", "root-g", "RootG")
        led(world_dir, "work", "claim", "root-g")
        led(world_dir, "work", "open", "leaf-g", "LeafG")   # left open+unclaimed+unclosed
        led(world_dir, "work", "depends", "root-g", "leaf-g", "--type", "blocks-close")
        rg_ = led(world_dir, "work", "close", "root-g", "dropped", "--review-witness", "refg", "--strict")
        out_g = rg_.stdout + rg_.stderr
        ok_g = rg_.returncode != 0 and "leaf-g" in out_g and "not yet closed" in out_g
        check("g-blocks-close-child-blocks-strict", ok_g,
              f"exit={rg_.returncode} names_leaf={'leaf-g' in out_g} excerpt={out_g.strip()[-400:]!r}", failures)

        led(world_dir, "work", "open", "root-h", "RootH")
        led(world_dir, "work", "claim", "root-h")
        led(world_dir, "work", "open", "leaf-h", "LeafH")   # left open+unclaimed+unclosed, SAME shape as g
        led(world_dir, "work", "depends", "root-h", "leaf-h", "--type", "informs")
        rh_ = led(world_dir, "work", "close", "root-h", "dropped", "--review-witness", "refh", "--strict")
        ok_h = rh_.returncode == 0
        check("h-informs-child-does-not-block", ok_h,
              f"exit={rh_.returncode} stderr_tail={(rh_.stdout + rh_.stderr).strip()[-250:]!r} "
              "-- proves the TYPE, not the mere edge, gates (identical structural shape as case g)",
              failures)

        # --- j: --type supersedes refused at the led boundary (reserved word) ------------------
        led(world_dir, "work", "open", "resv-j", "ResvJ")
        rj_ = led(world_dir, "work", "depends", "resv-j", "resv-j-target", "--type", "supersedes")
        out_j = rj_.stdout + rj_.stderr
        # cli-rebase-fixture-repairs (row 1170): the teach-text no longer calls out "supersedes"
        # as a RESERVED WORD by name -- it folded into a plain closed-vocabulary refusal
        # ("--type must be blocks-close, blocks-start, or informs") -- wording drift, not a
        # functional regression: supersedes is still refused, still not a legal --type value.
        ok_j = rj_.returncode != 0 and "must be blocks-close, blocks-start, or informs" in out_j
        check("j-reserved-word-supersedes-refused", ok_j,
              f"exit={rj_.returncode} excerpt={out_j.strip()[-300:]!r}", failures)

        # --- i: RETIRED, see this file's own module docstring for the named reason (cli-rebase-
        # fixture-repairs, ledger row 1170) -------------------------------------------------------

    finally:
        try:
            bs_fixtures.stop_server(proc)
        except NameError:
            pass  # scaffold itself failed before `proc` was ever assigned
        teardown_all()
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s30 typed dependency edges both-polarity proof (self-edge/dangling/"
          "cycle refused for blocks-close, allowed for informs / an unresolved blocks-close child "
          "blocks strict close, the SAME shape typed informs does not / supersedes refused as a "
          "reserved word; i-legacy-edge-reads-informs RETIRED, see module docstring), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
