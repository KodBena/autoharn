#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-21T21:48:32Z
#   last-change: 2026-07-21T21:48:32Z
#   contributors: 43f77bff/main
# <<< PROVENANCE-STAMP <<<

"""seen-red/setup-tui-destination-state/run_fixtures.py -- per-kind unit fixtures for
tools/setup_tui/destination.py's `classify_destination`
(design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md §5's first witness-set item: "one per kind,
plus the contradiction case and the pre-sentinel legacy-world case"), census-registered in
gates/fixture_census.py.

Both-polarity shape: each case is itself a red/green pair -- the fixture asserts the classifier
returns the SPEC-MANDATED kind for a constructed shape (green), and a mutated sibling shape (one
marker added or removed, or a contradicting field) returns a DIFFERENT kind (the implicit red:
if the classifier collapsed two distinct kinds to the same answer, the assertion that follows
would catch it). Real filesystem directories under a scratch tmpdir, zero mocks, zero residue
after cleanup (rmtree in a `finally`).

Cases (spec §2, §5):
  1. FRESH -- absent path.
  2. FRESH -- empty directory (the spec's OWN worked example of "absent, or an empty directory").
  3. AUTOHARN_COMPLETE -- sentinel + deployment.json + legacy/led, all present and consistent.
  4. AUTOHARN_COMPLETE -- pre-sentinel legacy world (deployment.json + legacy/led, NO sentinel;
     "no retro-stamping" -- spec §2).
  5. AUTOHARN_PARTIAL -- contradiction (sentinel `world` != deployment.json `name`).
  6. AUTOHARN_PARTIAL -- strict subset (deployment.json only, missing sentinel + legacy/led).
  7. AUTOHARN_PARTIAL -- sentinel present but unparseable (this module's own documented
     partial-birth reading of a corrupt sentinel).
  8. FOREIGN -- non-empty, no autoharn markers at all.

Lazy imports banned; stdlib only besides the module under test."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from tools.setup_tui import destination as d  # noqa: E402


def _mk(tmp: str, name: str, files: dict[str, str]) -> str:
    dirpath = os.path.join(tmp, name)
    os.makedirs(dirpath, exist_ok=True)
    for rel, content in files.items():
        p = os.path.join(dirpath, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
    return dirpath


def _deployment_json(name: str) -> str:
    return json.dumps({"db": "x", "host": "h", "schema": "s", "kern": "k", "role": "r",
                        "name": name})


def _sentinel_json(world: str) -> str:
    return json.dumps({"world": world, "run": world, "born": "2026-07-21T00:00:00Z",
                        "autoharn_commit": "deadbeef", "schema": d.SENTINEL_SCHEMA})


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="setup-tui-destination-state-")
    ok = True
    try:
        # --- case 1: FRESH, absent path ---
        r = d.classify_destination(os.path.join(tmp, "nonexistent"))
        assert r.kind == d.DestKind.FRESH, f"case 1: expected FRESH, got {r}"
        print("case 1 ok: absent path -> FRESH")

        # --- case 2: FRESH, empty directory ---
        empty = _mk(tmp, "empty", {})
        r = d.classify_destination(empty)
        assert r.kind == d.DestKind.FRESH, f"case 2: expected FRESH, got {r}"
        print("case 2 ok: empty directory -> FRESH")

        # --- case 3: AUTOHARN_COMPLETE, sentinel + deployment.json + legacy/led consistent ---
        complete = _mk(tmp, "complete", {
            "legacy/led": "#!/bin/sh\n",
            "deployment.json": _deployment_json("w1"),
            d.SENTINEL_NAME: _sentinel_json("w1"),
        })
        r = d.classify_destination(complete)
        assert r.kind == d.DestKind.AUTOHARN_COMPLETE, f"case 3: expected AUTOHARN_COMPLETE, got {r}"
        print("case 3 ok: sentinel + deployment.json + legacy/led, consistent -> AUTOHARN_COMPLETE")

        # --- case 4: AUTOHARN_COMPLETE, pre-sentinel legacy world (no retro-stamping) ---
        legacy = _mk(tmp, "legacy_world", {
            "legacy/led": "#!/bin/sh\n",
            "deployment.json": _deployment_json("w2"),
        })
        assert not os.path.exists(os.path.join(legacy, d.SENTINEL_NAME))
        r = d.classify_destination(legacy)
        assert r.kind == d.DestKind.AUTOHARN_COMPLETE, f"case 4: expected AUTOHARN_COMPLETE, got {r}"
        assert any("no sentinel" in e for e in r.evidence), f"case 4: evidence should name the " \
            f"missing sentinel: {r.evidence}"
        print("case 4 ok: deployment.json + legacy/led, NO sentinel -> AUTOHARN_COMPLETE "
              "(behavioral evidence alone, no retro-stamping)")

        # --- case 5: AUTOHARN_PARTIAL, sentinel/deployment.json contradiction ---
        contradiction = _mk(tmp, "contradiction", {
            "legacy/led": "#!/bin/sh\n",
            "deployment.json": _deployment_json("wZ"),
            d.SENTINEL_NAME: _sentinel_json("wY"),
        })
        r = d.classify_destination(contradiction)
        assert r.kind == d.DestKind.AUTOHARN_PARTIAL, f"case 5: expected AUTOHARN_PARTIAL, got {r}"
        assert any("contradicts" in e for e in r.evidence), f"case 5: evidence should name the " \
            f"contradiction: {r.evidence}"
        print("case 5 ok: sentinel world != deployment.json name -> AUTOHARN_PARTIAL, "
              "contradiction named -- NEVER coerced to either reading")

        # --- case 6: AUTOHARN_PARTIAL, strict subset (deployment.json only) ---
        subset = _mk(tmp, "subset", {"deployment.json": _deployment_json("w3")})
        r = d.classify_destination(subset)
        assert r.kind == d.DestKind.AUTOHARN_PARTIAL, f"case 6: expected AUTOHARN_PARTIAL, got {r}"
        assert any("missing" in e and "sentinel" in e and "legacy/led" in e for e in r.evidence), (
            f"case 6: evidence should name both missing markers: {r.evidence}")
        print("case 6 ok: deployment.json only -> AUTOHARN_PARTIAL, missing markers named")

        # --- case 7: AUTOHARN_PARTIAL, sentinel present but unparseable ---
        corrupt = _mk(tmp, "corrupt_sentinel", {
            "legacy/led": "#!/bin/sh\n",
            "deployment.json": _deployment_json("w4"),
        })
        with open(os.path.join(corrupt, d.SENTINEL_NAME), "w", encoding="utf-8") as f:
            f.write("{not valid json")
        r = d.classify_destination(corrupt)
        assert r.kind == d.DestKind.AUTOHARN_PARTIAL, f"case 7: expected AUTOHARN_PARTIAL, got {r}"
        assert any("unparseable" in e for e in r.evidence), f"case 7: evidence should name the " \
            f"unparseable sentinel: {r.evidence}"
        print("case 7 ok: corrupt sentinel -> AUTOHARN_PARTIAL (a write that started, "
              "did not finish cleanly)")

        # --- case 8: FOREIGN, non-empty, no autoharn markers ---
        foreign = _mk(tmp, "foreign", {"README.md": "hello", "src/main.py": "print(1)"})
        r = d.classify_destination(foreign)
        assert r.kind == d.DestKind.FOREIGN, f"case 8: expected FOREIGN, got {r}"
        assert any("sample" in e for e in r.evidence), f"case 8: evidence should sample entries: " \
            f"{r.evidence}"
        print("case 8 ok: non-empty, no autoharn markers -> FOREIGN, evidence samples entries")

        print("ALL CASES OK -- classify_destination, one per kind + contradiction + "
              "pre-sentinel-legacy, all real filesystem, zero mocks")
    except AssertionError as exc:
        print(f"FAILED: {exc}")
        ok = False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
