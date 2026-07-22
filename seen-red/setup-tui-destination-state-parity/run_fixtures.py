#!/usr/bin/env python3
"""seen-red/setup-tui-destination-state-parity/run_fixtures.py -- spec §5's second witness-set
item: "shell vs Python classification agree on the five witnessed shapes (fresh / complete /
partial / foreign / legacy-complete)." Census-registered in gates/fixture_census.py.

`bootstrap/classify-destination.sh` is a MINIMAL shell re-derivation of
`tools/setup_tui/destination.py`'s `classify_destination` (ADR-0012 P7's cross-language floor --
the Python module is the authority, the shell script says so in its own header, and THIS fixture
is the drift-catcher the spec names instead of a code generator, which P7 permits when codegen
would be disproportionate). This fixture builds each of the five witnessed shapes as a REAL
filesystem directory, classifies it with BOTH implementations, and asserts they agree -- plus a
sixth (contradiction) shape the shell script's own header names as a load-bearing agreement case
(the `world`/`name` grep it performs). A real subprocess invocation of the shell script, not a
re-implementation of its logic in Python -- drift in the SHIPPED artifact is what this fixture
must catch.

Zero mocks, zero residue (tmpdir rmtree in `finally`). Lazy imports banned."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from tools.setup_tui import destination as d  # noqa: E402

CLASSIFY_SH = os.path.join(REPO, "bootstrap", "classify-destination.sh")


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


def _sh_classify(path: str) -> str:
    r = subprocess.run([CLASSIFY_SH, path], capture_output=True, text=True)
    assert r.returncode == 0, f"classify-destination.sh exited {r.returncode} for {path}: " \
        f"{r.stderr}"
    return r.stdout.strip()


def main() -> int:
    assert os.access(CLASSIFY_SH, os.X_OK), f"{CLASSIFY_SH} must be executable"
    tmp = tempfile.mkdtemp(prefix="setup-tui-destination-state-parity-")
    ok = True
    try:
        shapes = {
            "fresh": os.path.join(tmp, "does-not-exist"),
            "complete": _mk(tmp, "complete", {
                "legacy/led": "#!/bin/sh\n",
                "deployment.json": _deployment_json("w1"),
                d.SENTINEL_NAME: _sentinel_json("w1"),
            }),
            "partial": _mk(tmp, "partial", {"deployment.json": _deployment_json("w2")}),
            "foreign": _mk(tmp, "foreign", {"README.md": "hi"}),
            "legacy-complete": _mk(tmp, "legacy_complete", {
                "legacy/led": "#!/bin/sh\n",
                "deployment.json": _deployment_json("w3"),
            }),
            "contradiction": _mk(tmp, "contradiction", {
                "legacy/led": "#!/bin/sh\n",
                "deployment.json": _deployment_json("wZ"),
                d.SENTINEL_NAME: _sentinel_json("wY"),
            }),
        }
        for shape, path in shapes.items():
            py_kind = d.classify_destination(path).kind.value
            sh_kind = _sh_classify(path)
            assert py_kind == sh_kind, (
                f"PARITY BREAK on shape '{shape}' ({path}): python={py_kind!r} "
                f"shell={sh_kind!r}")
            print(f"case '{shape}' ok: python={py_kind} shell={sh_kind} (agree)")
        print("ALL CASES OK -- shell/Python classification parity, five witnessed shapes + "
              "contradiction, real subprocess, zero mocks")
    except AssertionError as exc:
        print(f"FAILED: {exc}")
        ok = False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
