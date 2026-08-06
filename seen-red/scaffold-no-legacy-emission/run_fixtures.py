#!/usr/bin/env python3
"""run_fixtures.py -- permanent ban proof for ledger item omega-hub-join-and-pickup-legacy-text
(rows 160/161). Root cause this fixture guards against: bootstrap/new-project.sh used to write a
separate `./legacy/` directory into every newborn world (a `legacy/led` teaching-refusal stub
plus `legacy/pickup`/`legacy/asof-export`/`legacy/distance-to-clean` direct-psql shims sourced
from bootstrap/templates/legacy-*.tmpl), even though the served ./autoharn dispatcher and its
pickup.tmpl no longer name a working `./legacy/pickup` verb for a newborn world to run. Witnessed
live by the maintainer 2026-08-06: a freshly scaffolded world (~/w/omega) had all four legacy/
shims, and his verbatim ruling was "I refused to push until legacy was *GONE* completely." The
fix removed the emission loop and deleted the three legacy-*.tmpl source templates outright
(legacy-led.tmpl was already deleted by an earlier build, design/
FABLE-LEGACY-LED-RETIREMENT-SPEC.md's retirement act, ledger row 1149/1150).

This fixture makes the regression a MECHANICAL, PERMANENT red rather than something that lives
only in memory or a one-off maintainer report (ADR-0011): a scaffolded world containing ANY
`legacy/` path, or any leftover `bootstrap/templates/legacy-*.tmpl` source file, is a red case
forever, not just today.

REAL SCAFFOLD, NO MOCKS: this fixture runs the actual bootstrap/new-project.sh in its CLASSIC
(non-`--new-world`) mode against a throwaway scratch destination directory -- classic mode never
touches postgres (every `psql` call sits behind `if [ -n "$NEW_WORLD" ]`), so no live database or
toy-DB fixture idiom is needed, matching seen-red/scaffold-orchlog-wrapper's own precedent for
scaffold-shape fixtures.

Cases:
  GREEN scaffold-ran-clean       new-project.sh classic mode exits 0 against a scratch dest.
  GREEN no-legacy-dir            <dest>/legacy does not exist at all (not merely empty).
  GREEN no-legacy-anywhere       a recursive walk of <dest> finds zero path components equal to
                                  "legacy" (belt-and-braces: catches a legacy/ written under a
                                  different top-level name too, not just the exact old path).
  GREEN pickup-carries-new-text  <dest>/autoharn's pickup.tmpl (bootstrap/templates/pickup.tmpl,
                                  exec'd live, not copied per-world) never instructs an operator
                                  to run `./legacy/pickup` -- the NOT-REBASED section names the
                                  rebase spec and stays honest about scope instead.
  GREEN force-rescaffold-stays-legacy-free
                                  re-running new-project.sh --force over the same destination
                                  still writes no legacy/ path (the ban survives the refresh
                                  path, not just first birth).
  RED   templates-deleted        bootstrap/templates/legacy-pickup.tmpl,
                                  legacy-distance-to-clean.tmpl, legacy-asof-export.tmpl do not
                                  exist in this checkout (source-level half of the ban -- the
                                  emission loop cannot resurrect what has no source to read).

Usage: python3 seen-red/scaffold-no-legacy-emission/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import os
# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own environment
# before any subprocess is spawned -- inherited by the whole process tree this fixture starts.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def scaffold(dest: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return sh([
        "sh", str(NEW_PROJECT), str(dest),
        "--db", "scratchdb", "--host", "scratchhost",
        "--schema", "scratchschema", "--kern", "scratchkern", "--role", "scratchrole",
        *extra,
    ])


def any_legacy_path(root: Path) -> list[str]:
    hits = []
    for p in root.rglob("*"):
        if "legacy" in p.relative_to(root).parts:
            hits.append(str(p.relative_to(root)))
    return hits


def main() -> int:
    failures: list[str] = []

    tmp = Path(tempfile.mkdtemp(prefix="scaffold-no-legacy-emission-"))
    dest = tmp / "deployment"
    try:
        r1 = scaffold(dest)
        check("scaffold-ran-clean", r1.returncode == 0,
              f"exit={r1.returncode} stderr_tail={r1.stderr.strip()[-400:]!r}", failures)

        legacy_dir = dest / "legacy"
        check("no-legacy-dir", not legacy_dir.exists(),
              f"legacy_dir_exists={legacy_dir.exists()}", failures)

        hits = any_legacy_path(dest) if dest.exists() else ["<dest missing>"]
        check("no-legacy-anywhere", hits == [],
              f"legacy_path_hits={hits}", failures)

        pickup_tmpl = dest / "autoharn"
        pickup_src = REPO / "bootstrap" / "templates" / "pickup.tmpl"
        pickup_text = pickup_src.read_text(encoding="utf-8") if pickup_src.exists() else ""
        names_dead_verb = "./legacy/pickup" in pickup_text
        check("pickup-carries-new-text",
              pickup_src.exists() and not names_dead_verb,
              f"pickup_tmpl_exists={pickup_src.exists()} "
              f"still_names_legacy_pickup={names_dead_verb} "
              f"world_dispatcher_present={pickup_tmpl.exists()}", failures)

        r2 = scaffold(dest, "--force")
        hits2 = any_legacy_path(dest) if dest.exists() else ["<dest missing>"]
        check("force-rescaffold-stays-legacy-free",
              r2.returncode == 0 and hits2 == [],
              f"exit={r2.returncode} legacy_path_hits={hits2}", failures)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    templates_dir = REPO / "bootstrap" / "templates"
    still_present = [
        name for name in (
            "legacy-pickup.tmpl", "legacy-distance-to-clean.tmpl", "legacy-asof-export.tmpl",
        )
        if (templates_dir / name).exists()
    ]
    check("templates-deleted", still_present == [],
          f"still_present={still_present}", failures)

    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL CASES OK -- no legacy/ path is emitted by a scaffold or its --force refresh, "
          "pickup.tmpl no longer names a dead ./legacy/pickup verb, and the three legacy-*.tmpl "
          "source templates are gone from the repo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
