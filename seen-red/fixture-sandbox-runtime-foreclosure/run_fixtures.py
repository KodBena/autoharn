#!/usr/bin/env python3
"""seen-red/fixture-sandbox-runtime-foreclosure/run_fixtures.py -- both-polarity live proof for
design/FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md (ledger rows 1237-1248, the class;
1315/1316/1325, the ratification and disposition). Real infra, no mocks: every case below drives
the actual ./autoharn dispatcher, the actual libexec/autoharn/* files, and (case 5) an actual
scratch world scaffolded by bootstrap/new-project.sh.

WHY THIS FIXTURE EXISTS (spec's own §0 framing): five fresh-context review laps on
gates/fixture_deployment_pin_guard.py (now demoted, ledger row 1316) each closed the prior
round's findings and each next lap found a NEW ordinary-Python spelling the static AST census had
never enumerated. This build moves the guarantee from "recognize the call" to "the called thing
refuses" -- case 2 below is the direct answer to that arc: it lifts the exact evasion SHAPES
those five rounds kept finding (keyword argv, match/case, an alias chain, a shell string) and
runs them as REAL subprocess invocations, not as static-analysis specimens, proving each one hits
the identical runtime refusal regardless of spelling.

Cases:
  1-marker-refuses          -- AUTOHARN_FIXTURE_SANDBOX=1, no waiver, `./autoharn led --recent 1`
                                 -> typed refusal, exit 21, teaching text present (both sanctioned
                                 exits named: scratch worlds, the waiver).
  2-evasion-specimens       -- THE CENTERPIECE. The same underlying call (`./autoharn led
                                 --recent 1`, or the direct libexec/./led-alias equivalent),
                                 spelled five different ways a static census either never saw or
                                 (per the pin-guard docstring's own KNOWN-UNCAUGHT section) is
                                 disclosed as unable to see: os.system (a shell string), a
                                 keyword-only `subprocess.run(args=[...])` call, a match/case-
                                 built argv, the deprecated `./led` alias chain, and a direct
                                 `libexec/autoharn/led` invocation that skips ./autoharn
                                 entirely. Every one refuses identically -- exit 21, the same
                                 teaching text -- because the refusal lives in the verb, not in
                                 a parser looking for the verb.
  3-waiver-proceeds         -- AUTOHARN_FIXTURE_SANDBOX_WAIVER="<reason>" -> no refusal text, the
                                 reason is echoed into the verb's own output.
  4-empty-waiver-refuses    -- AUTOHARN_FIXTURE_SANDBOX_WAIVER="" (present but empty) -> refused
                                 exactly like no waiver at all.
  5-scratch-world-unaffected -- a REAL scratch world (bootstrap/new-project.sh --profile tracker)
                                 born under a fixture process that itself carries the marker: its
                                 own ./led works NORMALLY (no refusal at all) because it execs
                                 bootstrap/templates/led.tmpl directly, never this repo's
                                 ./autoharn or libexec/autoharn/* -- the choke-point-IS-the-
                                 discriminator argument, witnessed live rather than merely
                                 argued. UNEXERCISED (not FAILED, not faked) if neither
                                 HARNESS_PGHOST nor EPISTEMIC_PGHOST is set, matching every
                                 sibling new-project.sh fixture's own convention.
  6-census-red-green        -- gates/fixture_census.py's additive marker check (§4), exercised
                                 against a throwaway scratch GIT REPO (real `git ls-files`, no
                                 mocks, and no risk to this repo's own tracked tree): a
                                 registered run_fixtures.py with no marker line -> census RED
                                 naming "MARKER MISSING"; the same file with the marker added ->
                                 census GREEN.

Nothing here ever writes to this repo's own real deployment (every refused case is refused
BEFORE deployment.json is ever opened, per this repo's own worktree lacking one; case 5's world
is fully torn down in a `finally`). Lazy imports are banned (CLAUDE.md, 2026-07-02): every
import here is top of file.

Usage: python3 seen-red/fixture-sandbox-runtime-foreclosure/run_fixtures.py
Exit 0 if every EXERCISED case matches its expected outcome; 1 otherwise.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own environment
# before any subprocess is spawned -- inherited by the whole process tree this fixture starts.
# This is deliberately the SAME line the mechanical sweep put in every OTHER registered fixture
# (gates/fixture_census.py's own additive check, case 6 below, is what proves that).
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
AUTOHARN = REPO / "autoharn"
LED_ALIAS = REPO / "led"
LIBEXEC_LED = REPO / "libexec" / "autoharn" / "led"
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
TEARDOWN = REPO / "bootstrap" / "teardown-world.sh"
PGHOST = os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST") or ""

FAILURES: list[str] = []
UNEXERCISED: list[tuple[str, str]] = []

REFUSAL_MARKERS = ("REFUSED -- fixture sandbox marker set", "Exit code 21")
WAIVER_MARKER = "fixture-sandbox WAIVER in effect"


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"{label}: {'PASS' if ok else 'FAIL'}{(' -- ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


def run(argv: list[str], **kw) -> subprocess.CompletedProcess:
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    kw.setdefault("timeout", 30)
    return subprocess.run(argv, **kw)


def is_refused(cp: subprocess.CompletedProcess) -> bool:
    combined = cp.stdout + cp.stderr
    return cp.returncode == 21 and all(m in combined for m in REFUSAL_MARKERS)


# --------------------------------------------------------------------------------------------
# 1 -- bare marker refuses.
# --------------------------------------------------------------------------------------------

def case1_marker_refuses() -> None:
    cp = run([str(AUTOHARN), "led", "--recent", "1"])
    check("1-marker-refuses", is_refused(cp),
          f"exit={cp.returncode} combined_tail={(cp.stdout + cp.stderr).strip()[-200:]!r}")
    check("1-marker-refuses names both sanctioned exits",
          "SCRATCH world" in (cp.stdout + cp.stderr) and "AUTOHARN_FIXTURE_SANDBOX_WAIVER" in (cp.stdout + cp.stderr),
          "teaching text should name both the scratch-world exit and the waiver")


# --------------------------------------------------------------------------------------------
# 2 -- THE CENTERPIECE: the pin-guard arc's own evasion shapes, as real invocations.
# --------------------------------------------------------------------------------------------

def case2_evasion_specimens() -> None:
    # (a) os.system -- a shell string, the spelling CHECK 1b's shell-string refusal targeted and
    # every static AST census (this repo's demoted pin-guard included) treats as a single opaque
    # string rather than a parseable argv list.
    out_path = HERE / ".case2-os-system-out.txt"
    try:
        rc = os.system(f'"{AUTOHARN}" led --recent 1 > "{out_path}" 2>&1')
        exit_code = os.waitstatus_to_exitcode(rc)
        combined = out_path.read_text() if out_path.exists() else ""
        check("2a-os-system-refused", exit_code == 21 and all(m in combined for m in REFUSAL_MARKERS),
              f"exit={exit_code} tail={combined.strip()[-200:]!r}")
    finally:
        out_path.unlink(missing_ok=True)

    # (b) keyword-only argv: subprocess.run(args=[...]) -- CHECK 1's own docstring names this as
    # the round-4/final-round finding it had to specially widen its scan loop to catch (keyword
    # arguments, not just node.args); this fixture just calls it the way real code would.
    cp_b = subprocess.run(args=[str(AUTOHARN), "led", "--recent", "1"],
                           capture_output=True, text=True, timeout=30)
    check("2b-keyword-argv-refused", is_refused(cp_b),
          f"exit={cp_b.returncode} tail={(cp_b.stdout + cp_b.stderr).strip()[-200:]!r}")

    # (c) match/case-built argv -- the pin-guard docstring's own KNOWN-UNCAUGHT section names
    # ast.Match capture patterns as never swept by _pin_guard_census.py at all; here the argv is
    # genuinely assembled inside a match statement, then spawned.
    verb = "led"
    match verb:
        case "led":
            cmd = [str(AUTOHARN), "led", "--recent", "1"]
        case _:
            cmd = ["true"]
    cp_c = run(cmd)
    check("2c-match-case-argv-refused", is_refused(cp_c),
          f"exit={cp_c.returncode} tail={(cp_c.stdout + cp_c.stderr).strip()[-200:]!r}")

    # (d) alias chain: the deprecated `./led` shim (execs `./autoharn led "$@"` underneath) --
    # proves the refusal survives one full hop of indirection, not just a direct ./autoharn call.
    cp_d = run([str(LED_ALIAS), "--recent", "1"])
    check("2d-alias-chain-refused", is_refused(cp_d),
          f"exit={cp_d.returncode} tail={(cp_d.stdout + cp_d.stderr).strip()[-200:]!r}")

    # (e) direct libexec bypass: skips ./autoharn's own dispatch entirely, landing straight on
    # libexec/autoharn/led -- this is the "alias chain" evasion in the OTHER direction (going
    # straight to the target instead of through the alias), closed by that file's own
    # defense-in-depth preamble sourcing, not the dispatcher's.
    cp_e = run([str(LIBEXEC_LED), "--recent", "1"])
    check("2e-direct-libexec-bypass-refused", is_refused(cp_e),
          f"exit={cp_e.returncode} tail={(cp_e.stdout + cp_e.stderr).strip()[-200:]!r}")


# --------------------------------------------------------------------------------------------
# 3/4 -- the waiver.
# --------------------------------------------------------------------------------------------

def case3_waiver_proceeds() -> None:
    reason = "witness plan leg 3 -- seen-red/fixture-sandbox-runtime-foreclosure's own build-time proof"
    env = {**os.environ, "AUTOHARN_FIXTURE_SANDBOX_WAIVER": reason}
    cp = run([str(AUTOHARN), "led", "--recent", "1"], env=env)
    combined = cp.stdout + cp.stderr
    check("3-waiver-proceeds-no-refusal", not any(m in combined for m in REFUSAL_MARKERS),
          f"exit={cp.returncode} tail={combined.strip()[-200:]!r}")
    check("3-waiver-reason-echoed", WAIVER_MARKER in combined and reason in combined,
          f"combined_tail={combined.strip()[-300:]!r}")


def case4_empty_waiver_refuses() -> None:
    env = {**os.environ, "AUTOHARN_FIXTURE_SANDBOX_WAIVER": ""}
    cp = run([str(AUTOHARN), "led", "--recent", "1"], env=env)
    check("4-empty-waiver-refused", is_refused(cp),
          f"exit={cp.returncode} tail={(cp.stdout + cp.stderr).strip()[-200:]!r}")


# --------------------------------------------------------------------------------------------
# 5 -- the non-false-positive leg: a scratch world's own led is unaffected by the marker.
# --------------------------------------------------------------------------------------------

def case5_scratch_world_unaffected() -> None:
    if not PGHOST:
        UNEXERCISED.append((
            "5-scratch-world-unaffected",
            "BLOCKED: neither HARNESS_PGHOST nor EPISTEMIC_PGHOST is set -- this case scaffolds "
            "a real --profile tracker world (kernel lineage applied, a live boundary service "
            "spawned) and needs a reachable Postgres host to do so live. Re-run this fixture "
            "with HARNESS_PGHOST=192.168.122.1 (this house's standing scratch-infra address) to "
            "exercise it for real."))
        print(f"=== 5-scratch-world-unaffected ===\n  [UNEXERCISED] {UNEXERCISED[-1][1]}\n")
        return

    world = "fsandboxwitness"
    scratch = Path(tempfile.mkdtemp(prefix="fixture-sandbox-witness-"))
    dest = scratch / "world"
    try:
        cp = run([str(NEW_PROJECT), str(dest), "--profile", "tracker", "--name", world,
                  "--db", "toy", "--host", PGHOST], timeout=180)
        check("5 scaffold exit", cp.returncode == 0, f"exit={cp.returncode} stderr_tail={cp.stderr[-500:]!r}")
        if cp.returncode == 0:
            # The scratch world's OWN ./led, run with THIS fixture's own marked environment
            # inherited (no override) -- if the marker leaked into this world's shim the way it
            # leaks into every REPO-root verb, this would refuse exactly like case 1. It does
            # not, because dest/led execs dest/bootstrap/templates/led.tmpl DIRECTLY, never this
            # repo's ./autoharn or libexec/autoharn/* -- the choke-point argument, witnessed live.
            led_cp = run([str(dest / "led"), "--recent", "1"], cwd=str(dest))
            combined = led_cp.stdout + led_cp.stderr
            check("5-scratch-led-not-refused", not any(m in combined for m in REFUSAL_MARKERS),
                  f"exit={led_cp.returncode} tail={combined.strip()[-300:]!r}")
            check("5-scratch-led-actually-ran", led_cp.returncode == 0,
                  f"exit={led_cp.returncode} tail={combined.strip()[-300:]!r}")
    finally:
        # REAL FINDING, surfaced rather than routed around (this build's own report names it):
        # `autoharn service` is handled directly by ./autoharn (spec §2's "'service' included"),
        # so it hits the SAME marker refusal every other verb does -- but unlike every other
        # verb, `service`'s own target is resolved from PICKUP_DEPLOYMENT (libexec/autoharn-
        # service's own DEPLOYMENT_PATH), never cwd/deployment.json, so a fixture stopping a
        # boundary service IT ITSELF SPAWNED for its OWN scratch world (exactly this call) is
        # genuinely as safe as any scratch-world verb -- it just has no scratch-scaffolded shim
        # of its own to route through (there is no `<world>/service`). First-run witnessed this
        # would otherwise refuse and leave the spawned child orphaned. Waived here, reason
        # stated at the use site, per spec §3 -- the same mechanism freeze-at-stamp's two
        # specimens use, not a special case bolted on beside it.
        stop_cp = subprocess.run(
            [str(AUTOHARN), "service", "stop"],
            env={**os.environ, "PICKUP_DEPLOYMENT": str(dest / "deployment.json"),
                 "AUTOHARN_FIXTURE_SANDBOX_WAIVER":
                     "stopping the boundary service this fixture itself spawned for its own "
                     "scratch world (case 5), targeted via PICKUP_DEPLOYMENT override -- never "
                     "this repo's real deployment"},
            capture_output=True, text=True, timeout=30)
        print(f"  (teardown) service stop exit={stop_cp.returncode}")
        subprocess.run([str(TEARDOWN), world, "--db", "toy", "--host", PGHOST, "--force-non-scratch"],
                        input=f"{world}\n", capture_output=True, text=True, timeout=60)
        shutil.rmtree(scratch, ignore_errors=True)


# --------------------------------------------------------------------------------------------
# 6 -- census red/green, against a throwaway scratch git repo (no risk to this repo's own tree).
# --------------------------------------------------------------------------------------------

def _load_fixture_census():
    spec = importlib.util.spec_from_file_location(
        "fixture_census_under_test", str(REPO / "gates" / "fixture_census.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def case6_census_red_green() -> None:
    fc = _load_fixture_census()
    scratch = Path(tempfile.mkdtemp(prefix="fixture-sandbox-census-witness-"))
    try:
        seen_red = scratch / "seen-red"
        fixture_dir = seen_red / "fake-marker-dir"
        fixture_dir.mkdir(parents=True)
        (fixture_dir / "red.txt").write_text("synthetic red evidence for this witness only\n")
        no_marker_src = (
            "#!/usr/bin/env python3\n"
            "import subprocess\n"
            "subprocess.run(['true'])\n"
        )
        (fixture_dir / "run_fixtures.py").write_text(no_marker_src)

        def git(*args: str) -> subprocess.CompletedProcess:
            return subprocess.run(["git", "-C", str(scratch), *args],
                                   capture_output=True, text=True, timeout=30)

        git("init", "-q")
        git("config", "user.email", "witness@example.com")
        git("config", "user.name", "witness")
        git("add", "-A")
        git("commit", "-q", "-m", "seed")

        orig_root, orig_seen_red, orig_registry = fc.ROOT, fc.SEEN_RED, fc.REGISTRY
        fc.ROOT = str(scratch)
        fc.SEEN_RED = str(seen_red)
        fc.REGISTRY = {"fake-marker-dir": "seen-red/fake-marker-dir/run_fixtures.py"}
        try:
            rc_red = fc.main()
            check("6-census-red-without-marker", rc_red == 1, f"exit={rc_red} (expected 1)")

            (fixture_dir / "run_fixtures.py").write_text(
                no_marker_src + '\nos.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"\n')
            git("add", "-A")
            git("commit", "-q", "-m", "add marker")

            rc_green = fc.main()
            check("6-census-green-with-marker", rc_green == 0, f"exit={rc_green} (expected 0)")
        finally:
            fc.ROOT, fc.SEEN_RED, fc.REGISTRY = orig_root, orig_seen_red, orig_registry
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def main() -> int:
    case1_marker_refuses()
    case2_evasion_specimens()
    case3_waiver_proceeds()
    case4_empty_waiver_refuses()
    case5_scratch_world_unaffected()
    case6_census_red_green()

    if UNEXERCISED:
        print("UNEXERCISED cases (named blocker, not faked):")
        for name, blocker in UNEXERCISED:
            print(f"  - {name}: {blocker}")
        print()

    if FAILURES:
        print("FAILURES:", FAILURES)
        return 1
    print(f"ALL EXERCISED CASES OK ({len(UNEXERCISED)} case(s) UNEXERCISED with a concrete, "
          f"named blocker -- see above).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
