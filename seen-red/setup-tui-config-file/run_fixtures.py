#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-22T02:15:22Z
#   last-change: 2026-07-22T02:18:55Z
#   contributors: 1fa3ab69/main
# <<< PROVENANCE-STAMP <<<

"""seen-red/setup-tui-config-file/run_fixtures.py -- the six-case witness plan
design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md §6 names, ledger row 1944:

  (i)   --from-config full dry-run birth from the shipped exemplar, deterministic, zero prompts.
  (ii)  missing-key refusal names every missing key at once (red-then-green: per-key red
        controls, then a green control with every required key present).
  (iii) unknown-key refusal (red-then-green, same shape) -- including the two NAMED excluded
        keys ("world"/"dest") that must never validate even though an author might reach for
        them.
  (iv)  world-exists rejection on BOTH the schema leg (a live Postgres probe) and the sentinel
        leg (a destination directory whose `.autoharn-world.json` names a different world).
  (v)   --initial-config's scripted leg: a config default threads through the SAME navigation
        prior-answers seam a real revisit uses, and an individual prompt can still override it.
  (vi)  round-trip (spec §4's self-application property, checked mechanically): a LIVE birth's
        own saved `world-config.toml`, re-applied via `--from-config` to a second world, saves
        the SAME resolved decision set again -- a fixed point, not a byte-for-byte match against
        the hand-authored exemplar (which is archaeology, not machine output).

Cases (i)/(v)/(vi) need a live, reachable Postgres host (HARNESS_PGHOST/EPISTEMIC_PGHOST) --
UNEXERCISED, not FAILED, when neither is set (same convention seen-red/setup-tui-principals-
authority already uses). Every scratch destination lives under a fixture-owned tempdir, and
every scratch world this fixture BIRTHS is torn down in a `finally`, real teardown-world.sh
(`--force-non-scratch` -- fixture-generated world names do not match the scratch-safe pattern),
zero residue regardless of outcome.

Real subprocess invocations of the actual CLI entry point (no mocks), matching every sibling
setup_tui fixture's own Rule 1 bar. Lazy imports banned."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

from tools.setup_tui import config_file, config_seam, destination  # noqa: E402

PGHOST = os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST")
PGDB = "toy"
EXEMPLAR = os.path.join(REPO, "bootstrap", "templates", "known-good-blank.toml")


def run_app(argv: list[str], cwd: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "tools.setup_tui.app"] + argv, cwd=REPO,
                           capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, "HARNESS_PGHOST": PGHOST or ""})


def teardown(world: str, dest: str) -> None:
    subprocess.run(
        ["bash", os.path.join(REPO, "bootstrap", "teardown-world.sh"), world,
         "--db", PGDB, "--host", PGHOST, "--dir", dest, "--force-non-scratch"],
        input=f"{world}\n", capture_output=True, text=True, timeout=60,
    )


def _minimal_valid_values() -> dict[str, object]:
    return {
        "substrate.run": False, "rehearsal.run": False, "birth.run": False,
        "principals_authority.run": False, "signed_genesis.run": False,
        "boundary.configure": False, "observability.run": False, "hydration.run": False,
    }


def _doc(header: dict, values: dict) -> config_file.ConfigDoc:
    return config_file.ConfigDoc(path="<synthetic>", header=header, values=values)


VALID_HEADER = {"config_format": 1, "produced_by": "fixture", "source": "fixture"}


def case_missing_key() -> None:
    for missing in config_file.REQUIRED_GATES:
        values = _minimal_valid_values()
        del values[missing]
        try:
            config_file.validate(_doc(VALID_HEADER, values), require_complete=True)
            raise AssertionError(f"case ii RED control failed: '{missing}' absent did not refuse")
        except config_file.ConfigError as exc:
            assert missing in str(exc), f"case ii: refusal did not name '{missing}': {exc}"
    # all-missing-at-once: every gate absent -> every gate named in ONE refusal (spec §2: "naming
    # every missing key at once", never a first-one-wins early exit).
    try:
        config_file.validate(_doc({}, {}), require_complete=True)
        raise AssertionError("case ii RED control failed: fully empty doc did not refuse")
    except config_file.ConfigError as exc:
        msg = str(exc)
        for gate in config_file.REQUIRED_GATES:
            assert gate in msg, f"case ii: all-at-once refusal missing '{gate}': {msg}"
        for hk in sorted(config_file.HEADER_KEYS if hasattr(config_file, "HEADER_KEYS")
                          else {"config_format", "produced_by", "source"}):
            assert hk in msg, f"case ii: all-at-once refusal missing header field '{hk}': {msg}"
    # GREEN control: every required key present -> no refusal.
    config_file.validate(_doc(VALID_HEADER, _minimal_valid_values()), require_complete=True)
    print("case ii ok: missing-key refusal names every missing key (per-key red controls, "
          "an all-missing-at-once control naming every gate+header field in ONE refusal), "
          "green control passes")


def case_unknown_key() -> None:
    for bad_key in ("world", "dest", "destination", "substrate.bogus_typo_field"):
        values = {**_minimal_valid_values(), bad_key: "anything"}
        try:
            config_file.validate(_doc(VALID_HEADER, values), require_complete=True)
            raise AssertionError(f"case iii RED control failed: '{bad_key}' was not refused")
        except config_file.ConfigError as exc:
            assert bad_key in str(exc), f"case iii: refusal did not name '{bad_key}': {exc}"
    # GREEN control: the same minimal doc, no stray key -> no refusal.
    config_file.validate(_doc(VALID_HEADER, _minimal_valid_values()), require_complete=True)
    print("case iii ok: unknown-key refusal (including the two named-excluded CLI parameters, "
          "'world'/'dest', which are never legal config content), green control passes")


def case_world_exists_schema_leg(scratch: str) -> None:
    probe_world = f"cfgfixprobe{int(time.time())}"
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", PGDB, "-c",
                          f"CREATE SCHEMA {probe_world}"], capture_output=True, text=True,
                         timeout=20)
    assert cp.returncode == 0, f"case iv setup: could not create probe schema: {cp.stderr}"
    try:
        dest = os.path.join(scratch, "iv-schema-leg")
        os.makedirs(dest, exist_ok=True)
        refusal = config_seam.check_world_and_dest(world=probe_world, dest=dest, host=PGHOST,
                                                     db=PGDB)
        assert refusal is not None and probe_world in refusal and "schema" in refusal, (
            f"case iv (schema leg): expected a REFUSED-and-named world-exists rejection, "
            f"got: {refusal!r}")
        # GREEN control: a name that does NOT exist as a schema is not refused on this leg.
        clean = config_seam.check_world_and_dest(
            world=f"{probe_world}neverexists", dest=dest, host=PGHOST, db=PGDB)
        assert clean is None, f"case iv (schema leg) green control: {clean!r}"
    finally:
        subprocess.run(["psql", "-h", PGHOST, "-d", PGDB, "-c",
                         f"DROP SCHEMA IF EXISTS {probe_world} CASCADE"],
                        capture_output=True, text=True, timeout=20)
    print("case iv ok (schema leg): world name REFUSED when its schema already exists on the "
          "target Postgres, named in the refusal; a genuinely-fresh name is not refused "
          "(green control)")


def case_world_exists_sentinel_leg(scratch: str) -> None:
    dest = os.path.join(scratch, "iv-sentinel-leg")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "deployment.json"), "w") as f:
        json.dump({"name": "sentinel-world-a"}, f)
    os.makedirs(os.path.join(dest, "legacy"), exist_ok=True)
    with open(os.path.join(dest, "legacy", "led"), "w") as f:
        f.write("#!/bin/sh\n")
    with open(os.path.join(dest, destination.SENTINEL_NAME), "w") as f:
        json.dump({"world": "sentinel-world-a", "run": "", "born": "2026-01-01T00:00:00Z",
                   "autoharn_commit": "deadbeef", "schema": destination.SENTINEL_SCHEMA}, f)
    refusal = config_seam.check_world_and_dest(world="sentinel-world-b", dest=dest, host=PGHOST,
                                                 db=PGDB)
    assert refusal is not None and "sentinel-world-a" in refusal and "sentinel" in refusal, (
        f"case iv (sentinel leg): expected a refusal naming the sentinel's own world, "
        f"got: {refusal!r}")
    # GREEN control: the SAME world name the sentinel already names is not refused on this leg
    # (still refused on the destination-classification leg below, since the dir is AUTOHARN_
    # COMPLETE -- checked separately so this control isolates the sentinel-contradiction check).
    same_name = config_seam.check_world_and_dest(world="sentinel-world-a", dest=dest, host=PGHOST,
                                                   db=PGDB)
    assert same_name is not None and "classifies as" in same_name, (
        f"case iv (sentinel leg) green control: expected the destination-classification leg "
        f"(not the sentinel-contradiction leg) to be the one refusing: {same_name!r}")
    print("case iv ok (sentinel leg): world name REFUSED when the destination's own sentinel "
          "names a DIFFERENT world, that world named in the refusal")


def case_initial_config_override(scratch: str) -> None:
    values = {**_minimal_valid_values(), "substrate.run": True, "substrate.path": "existing",
              "substrate.host": "192.168.122.1", "substrate.db": "cfgfixtureinitdb"}
    cfg_path = os.path.join(scratch, "v-initial.toml")
    with open(cfg_path, "w") as f:
        f.write(config_file.render_toml(values, produced_by="fixture", source="fixture"))
    # keep-the-default leg: "-" accepts substrate.db's config default. `--start-at substrate`
    # (a fresh --scripted answers file starts at the substrate screen's own first prompt, its
    # own confirm -- no preflight leg to answer first).
    ans_keep = os.path.join(scratch, "v-answers-keep.txt")
    with open(ans_keep, "w") as f:
        f.write("y\nexisting\n192.168.122.1\n-\n" + "n\n" * 8)
    cp_keep = run_app(["--scripted", ans_keep, "--initial-config", cfg_path, "--dry-run",
                        "--start-at", "substrate"], scratch)
    out_keep = cp_keep.stdout + cp_keep.stderr
    assert cp_keep.returncode == 0, f"case v (keep leg): exit {cp_keep.returncode}: {out_keep[-1500:]}"
    assert "Existing database name: cfgfixtureinitdb" in out_keep, (
        f"case v (keep leg): the config default was not offered/kept at the prompt: "
        f"{out_keep[-1500:]}")
    # override leg: a literal answer overrides the SAME config default.
    ans_override = os.path.join(scratch, "v-answers-override.txt")
    with open(ans_override, "w") as f:
        f.write("y\nexisting\n192.168.122.1\noperatorchosendb\n" + "n\n" * 8)
    cp_over = run_app(["--scripted", ans_override, "--initial-config", cfg_path, "--dry-run",
                        "--start-at", "substrate"], scratch)
    out_over = cp_over.stdout + cp_over.stderr
    assert cp_over.returncode == 0, f"case v (override leg): exit {cp_over.returncode}: {out_over[-1500:]}"
    assert "Existing database name: operatorchosendb" in out_over, (
        f"case v (override leg): the operator's own answer did not override the config "
        f"default: {out_over[-1500:]}")
    assert "cfgfixtureinitdb" not in out_over.split("Existing database name:")[-1][:40], (
        "case v (override leg): the config default leaked through despite the override")
    print("case v ok: --initial-config threads a config value as the prompt's own default "
          "(kept via '-', the SAME navigation prior-answers seam a real revisit uses) and an "
          "individual answer still overrides it")


def case_full_dry_run_and_roundtrip(scratch: str) -> None:
    world1 = f"cfgfxa{int(time.time())}"
    dest1 = os.path.join(scratch, "vi-world1")
    # (i) full dry-run birth from the shipped exemplar, deterministic, zero prompts.
    cp = run_app(["--from-config", EXEMPLAR, "--world", world1, dest1, "--dry-run"], scratch)
    out = cp.stdout + cp.stderr
    assert cp.returncode == 0, f"case i: exit {cp.returncode}: {out[-2000:]}"
    assert "ScriptExhausted" not in out and "Traceback" not in out, (
        f"case i: not a clean zero-prompt run: {out[-2000:]}")
    assert "world-config.toml" in out and "WOULD-DO" in out, (
        f"case i: self-save was not queued: {out[-2000:]}")
    for expect in ("register-principal maintainer human", "register-principal orchestrator model",
                   "principal relate orchestrator acts-for maintainer",
                   "new-project.sh", "boundary_service"):
        assert expect in out, f"case i: expected content missing ({expect!r}): {out[-2000:]}"
    print("case i ok: --from-config drives a full eleven-screen dry-run birth from the shipped "
          "exemplar to a clean exit 0, zero prompts left to a human, every queued act visible")

    if not PGHOST:
        print("case vi UNEXERCISED: no HARNESS_PGHOST/EPISTEMIC_PGHOST -- needs a live, "
              "reachable Postgres host for two real births")
        return

    world2 = f"cfgfxb{int(time.time())}"
    dest2 = os.path.join(scratch, "vi-world2")
    try:
        cp1 = run_app(["--from-config", EXEMPLAR, "--world", world1, dest1], scratch, timeout=180)
        out1 = cp1.stdout + cp1.stderr
        assert cp1.returncode == 0, f"case vi: live birth 1 exit {cp1.returncode}: {out1[-2000:]}"
        cfg_a = os.path.join(dest1, "world-config.toml")
        assert os.path.isfile(cfg_a), f"case vi: {cfg_a} was not saved: {out1[-2000:]}"
        doc_a = config_file.load_config_file(cfg_a)
        config_file.validate(doc_a, require_complete=True)

        cp2 = run_app(["--from-config", cfg_a, "--world", world2, dest2], scratch, timeout=180)
        out2 = cp2.stdout + cp2.stderr
        assert cp2.returncode == 0, f"case vi: live birth 2 (re-applied) exit {cp2.returncode}: {out2[-2000:]}"
        cfg_b = os.path.join(dest2, "world-config.toml")
        assert os.path.isfile(cfg_b), f"case vi: {cfg_b} was not saved: {out2[-2000:]}"
        doc_b = config_file.load_config_file(cfg_b)
        config_file.validate(doc_b, require_complete=True)

        assert doc_a.values == doc_b.values, (
            f"case vi: the round-trip is not a fixed point:\n  a={doc_a.values}\n  "
            f"b={doc_b.values}")
        print("case vi ok: a live birth's own saved world-config.toml, re-applied via "
              "--from-config to a SECOND world, saves the SAME resolved decision set again "
              "(a fixed point, checked mechanically)")
    finally:
        _kill_boundary(world1)
        _kill_boundary(world2)
        teardown(world1, dest1)
        teardown(world2, dest2)


def _kill_boundary(world: str) -> None:
    cp = subprocess.run(["pgrep", "-f", f"boundary_service.*{world}"], capture_output=True,
                         text=True, timeout=10)
    for pid in cp.stdout.split():
        subprocess.run(["kill", pid], capture_output=True, timeout=5)


def main() -> int:
    scratch = tempfile.mkdtemp(prefix="setup-tui-config-file-")
    try:
        case_missing_key()
        case_unknown_key()
        if PGHOST:
            case_world_exists_schema_leg(scratch)
        else:
            print("case iv (schema leg) UNEXERCISED: no HARNESS_PGHOST/EPISTEMIC_PGHOST")
        case_world_exists_sentinel_leg(scratch)  # read-only, no live Postgres needed
        if PGHOST:
            case_initial_config_override(scratch)
        else:
            print("case v UNEXERCISED: no HARNESS_PGHOST/EPISTEMIC_PGHOST")
        case_full_dry_run_and_roundtrip(scratch)
        print("ALL CASES OK (or honestly UNEXERCISED) -- setup_tui config-file feature "
              "(design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md), zero residue")
        return 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
