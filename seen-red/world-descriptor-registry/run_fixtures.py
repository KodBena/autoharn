#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for filing/world_descriptor.py (design/
FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md §4). Round-1 review minor-a finding: that module's own
docstring claimed "tested against a scratch registry directory (see the umbrella build's own
witness fixtures)" while no such fixture existed anywhere in the repo. This is that fixture --
runs entirely against a scratch, throwaway registry directory under /tmp, never touching any
real multiplexer registry.

Cases:
  a-write-then-scan-roundtrips -- write_descriptor() for two worlds, scan_registry() reads both
                                 back, sorted by world name, every field byte-identical.
  b-rewrite-same-world-overwrites -- writing the SAME world name twice overwrites (birth is
                                 idempotent by world name, module docstring's own claim) rather
                                 than merging with the stale prior write.
  c-malformed-world-name-refuses -- construction-time DescriptorError (RED case) for a world name
                                 outside the closed alphabet (^[a-z0-9-]{1,64}$) -- e.g. an
                                 uppercase or empty name -- never silently accepted.
  d-malformed-registry-entry-refuses -- scan_registry() raises DescriptorError, naming the
                                 offending file, on a *.json entry that is not valid JSON, not a
                                 JSON object, or has an unrecognized shape -- never silently
                                 skipped (the module's own "a multiplexer refuses to silently
                                 skip a malformed registration" claim).
  e-empty-registry-dir-scans-empty -- scan_registry() on a directory that does not exist yet
                                 returns [] rather than raising.

RUN: python3 seen-red/world-descriptor-registry/run_fixtures.py
"""
from __future__ import annotations

import shutil
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "filing"))
import world_descriptor as wd  # noqa: E402


def case_a_write_then_scan_roundtrips(reg: Path) -> bool:
    d1 = wd.WorldDescriptor(world="alpha-world", host="192.168.1.10",
                             boundary_url="http://127.0.0.1:8420", boundary_deployment="alpha",
                             epoch=3)
    d2 = wd.WorldDescriptor(world="beta-world", host="192.168.1.11",
                             boundary_url="http://127.0.0.1:8421", boundary_deployment="beta",
                             epoch=0)
    wd.write_descriptor(reg, d1)
    wd.write_descriptor(reg, d2)
    got = wd.scan_registry(reg)
    ok = (len(got) == 2 and got[0].world == "alpha-world" and got[1].world == "beta-world"
          and asdict(got[0]) == asdict(d1) and asdict(got[1]) == asdict(d2))
    if not ok:
        print(f"a-write-then-scan-roundtrips: FAIL -- got {[asdict(g) for g in got]}")
        return False
    print("a-write-then-scan-roundtrips: PASS (two worlds written, scanned back byte-identical, "
          "sorted by name)")
    return True


def case_b_rewrite_same_world_overwrites(reg: Path) -> bool:
    d1 = wd.WorldDescriptor(world="gamma-world", host="10.0.0.1",
                             boundary_url="http://127.0.0.1:8422", boundary_deployment="gamma",
                             epoch=0)
    wd.write_descriptor(reg, d1)
    d1_updated = wd.WorldDescriptor(world="gamma-world", host="10.0.0.1",
                                     boundary_url="http://127.0.0.1:8422",
                                     boundary_deployment="gamma", epoch=5)
    wd.write_descriptor(reg, d1_updated)
    got = [d for d in wd.scan_registry(reg) if d.world == "gamma-world"]
    if len(got) != 1 or got[0].epoch != 5:
        print(f"b-rewrite-same-world-overwrites: FAIL -- expected exactly one gamma-world entry "
              f"with epoch=5, got {[asdict(g) for g in got]}")
        return False
    print("b-rewrite-same-world-overwrites: PASS (re-write of the same world name overwrote, "
          "no merge with the stale prior epoch)")
    return True


def case_c_malformed_world_name_refuses() -> bool:
    ok = True
    for bad_name in ("UPPERCASE-NOT-ALLOWED", "", "has a space", "x" * 65):
        try:
            wd.WorldDescriptor(world=bad_name, host="h", boundary_url="http://x",
                                boundary_deployment="d", epoch=0)
            print(f"c-malformed-world-name-refuses: FAIL -- world={bad_name!r} was accepted, "
                  f"never refused")
            ok = False
        except wd.DescriptorError:
            pass
    if ok:
        print("c-malformed-world-name-refuses: PASS (RED case: every out-of-alphabet world name "
              "refused at construction)")
    return ok


def case_d_malformed_registry_entry_refuses(reg: Path) -> bool:
    ok = True
    (reg / "not-json.json").write_text("{not valid json", encoding="utf-8")
    try:
        wd.scan_registry(reg)
        print("d-malformed-registry-entry-refuses: FAIL -- not-json.json (invalid JSON) was "
              "silently accepted/skipped")
        ok = False
    except wd.DescriptorError as e:
        if "not-json.json" not in str(e):
            print(f"d-malformed-registry-entry-refuses: FAIL -- DescriptorError did not name the "
                  f"offending file: {e}")
            ok = False
    finally:
        (reg / "not-json.json").unlink()

    (reg / "not-an-object.json").write_text("[1, 2, 3]", encoding="utf-8")
    try:
        wd.scan_registry(reg)
        print("d-malformed-registry-entry-refuses: FAIL -- not-an-object.json (JSON array, not "
              "object) was silently accepted/skipped")
        ok = False
    except wd.DescriptorError:
        pass
    finally:
        (reg / "not-an-object.json").unlink()

    (reg / "wrong-shape.json").write_text('{"some_unrecognized_key": true}', encoding="utf-8")
    try:
        wd.scan_registry(reg)
        print("d-malformed-registry-entry-refuses: FAIL -- wrong-shape.json (unrecognized "
              "descriptor shape) was silently accepted/skipped")
        ok = False
    except wd.DescriptorError:
        pass
    finally:
        (reg / "wrong-shape.json").unlink()

    if ok:
        print("d-malformed-registry-entry-refuses: PASS (RED case: invalid JSON, a non-object, "
              "and an unrecognized shape all refuse, each naming the offending file)")
    return ok


def case_e_empty_registry_dir_scans_empty() -> bool:
    nonexistent = Path("/tmp") / "world-descriptor-registry-fixture-never-created-xyz"
    shutil.rmtree(nonexistent, ignore_errors=True)
    got = wd.scan_registry(nonexistent)
    if got != []:
        print(f"e-empty-registry-dir-scans-empty: FAIL -- expected [], got {got}")
        return False
    print("e-empty-registry-dir-scans-empty: PASS (a not-yet-created registry dir scans empty, "
          "never raises)")
    return True


def main() -> int:
    reg = Path("/tmp") / "world-descriptor-registry-fixture-scratch"
    shutil.rmtree(reg, ignore_errors=True)
    try:
        results = [
            case_a_write_then_scan_roundtrips(reg),
            case_b_rewrite_same_world_overwrites(reg),
            case_c_malformed_world_name_refuses(),
            case_d_malformed_registry_entry_refuses(reg),
            case_e_empty_registry_dir_scans_empty(),
        ]
    finally:
        shutil.rmtree(reg, ignore_errors=True)
    if all(results):
        print("\nALL CASES PASS")
        return 0
    print("\nAT LEAST ONE CASE FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
