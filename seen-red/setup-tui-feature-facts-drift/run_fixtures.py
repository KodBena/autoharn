#!/usr/bin/env python3
"""seen-red/setup-tui-feature-facts-drift/run_fixtures.py -- both-polarity proof of
tools/setup_tui/feature_facts.py's own drift backstop (design/FABLE-SETUP-TUI-FEATURE-FACTS-
SPEC.md §1/§2/§5's WF2), census-registered in gates/fixture_census.py.

WF2, verbatim: "a synthetic registry with a key for a nonexistent feature (and, separately, a
live feature stripped from a synthetic registry) reads red in the census fixture." Three cases:

  1. GREEN leg: the REAL REGISTRY vs the REAL live derivation agrees -- `check_registry()` with
     no arguments returns zero drift messages. This is the fixture's own proof of itself
     staying green on an unmodified corpus (the same shape every seen-red fixture in this
     project's census carries, e.g. seen-red/setup-tui-scripted-smoke's five green cases).
  2. RED leg A: a SYNTHETIC registry carrying an extra key with no live counterpart
     ("preflight_nonexistent_binary") -- `check_registry` must report it ORPHANED.
  3. RED leg B: a SYNTHETIC registry with a real, live key STRIPPED out (here:
     "hydration_drift_backstops", one of durable_decisions.CATALOG's own slugs) --
     `check_registry` must report it UNREGISTERED.

Both red legs feed `check_registry(registry=..., live_keys=...)` a SYNTHETIC copy (per
feature_facts.py's own docstring: "so a fixture can feed a SYNTHETIC registry/live-set and
observe the red leg without mutating this module's own globals") -- this fixture never mutates
tools.setup_tui.feature_facts.REGISTRY itself, unlike gates/fixture_census.py's/layout_census.py's
own self-test convention of mutating a REGISTRY dict in memory; feature_facts.py's comparator was
built injectable specifically so this fixture does not need to.

Zero residue: pure in-memory comparison, no filesystem/db state. Real functions under test (no
mocks) -- Rule 1's own bar applied to this fixture's own proof of itself. Lazy imports banned."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # repo root, so `tools.setup_tui` imports regardless of cwd
# (same sys.path.insert-then-import convention this project's own seen-red fixtures already
# use, e.g. seen-red/adr-bare-p-label/run_fixtures.py, seen-red/boundary-cli-rebase/
# run_fixtures.py -- not a lazy import: this IS the module's top-of-file import, just preceded
# by the path setup a fixture invoked from an arbitrary cwd needs.)
from tools.setup_tui import feature_facts  # noqa: E402


def main() -> int:
    # --- case 1: GREEN leg -- the real registry and the real live derivation agree ---
    real_drift = feature_facts.check_registry()
    assert real_drift == [], (
        f"case 1 (GREEN leg): the real feature_facts.REGISTRY must agree with the real live "
        f"derivation with ZERO drift messages -- got: {real_drift}"
    )
    print("case 1 ok: the real REGISTRY and the real live-key derivation agree (zero drift)")

    # --- case 2: RED leg A -- synthetic registry with a key that has NO live counterpart ---
    synthetic_registry_extra = dict(feature_facts.REGISTRY)
    synthetic_registry_extra["preflight_nonexistent_binary"] = feature_facts.FeatureFact(
        key="preflight_nonexistent_binary", label="a feature that does not exist",
    )
    drift_a = feature_facts.check_registry(registry=synthetic_registry_extra)
    assert any("preflight_nonexistent_binary" in m and "ORPHANED" in m for m in drift_a), (
        f"case 2 (RED leg A): a registry key with no live counterpart must read ORPHANED -- "
        f"got: {drift_a}"
    )
    print("case 2 ok: a synthetic registry key with no live counterpart reads red "
          "(ORPHANED registry key)")

    # --- case 3: RED leg B -- synthetic registry with a REAL, live key stripped out ---
    stripped_key = "hydration_drift_backstops"
    assert stripped_key in feature_facts.REGISTRY, (
        f"fixture assumption stale: '{stripped_key}' is no longer in the real REGISTRY -- "
        f"update this fixture's chosen stripped key"
    )
    synthetic_registry_missing = dict(feature_facts.REGISTRY)
    del synthetic_registry_missing[stripped_key]
    drift_b = feature_facts.check_registry(registry=synthetic_registry_missing)
    assert any(stripped_key in m and "UNREGISTERED" in m for m in drift_b), (
        f"case 3 (RED leg B): a live feature stripped from the registry must read "
        f"UNREGISTERED -- got: {drift_b}"
    )
    print("case 3 ok: a live feature stripped from a synthetic registry reads red "
          "(UNREGISTERED live feature)")

    # --- bonus case: both red legs stack (extra AND missing) in one synthetic registry ---
    synthetic_both = dict(synthetic_registry_missing)
    synthetic_both["preflight_nonexistent_binary"] = feature_facts.FeatureFact(
        key="preflight_nonexistent_binary", label="a feature that does not exist",
    )
    drift_both = feature_facts.check_registry(registry=synthetic_both)
    assert len(drift_both) == 2, (
        f"bonus case: a registry with both defects should report exactly 2 drift messages -- "
        f"got {len(drift_both)}: {drift_both}"
    )
    print("bonus case ok: a synthetic registry carrying BOTH defects at once reports both, "
          "not just one")

    print("ALL CASES OK -- feature_facts.py drift backstop, both polarities proven")
    return 0


if __name__ == "__main__":
    sys.exit(main())
