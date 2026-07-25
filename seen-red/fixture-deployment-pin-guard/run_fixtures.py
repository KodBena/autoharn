#!/usr/bin/env python3
"""Both-polarity fixture for gates/fixture_deployment_pin_guard.py (fixture-scratch-pinning-
guard, ledger row 1249 — generalizing beyond serve_existing_world's own tempdir/repo-disjoint
refusal, seen-red/boundary-service/run_fixtures.py).

GREEN: this repo's own current fixture tree (seen-red/, instruments/, kernel/fixtures/) passes
-- no fixture invokes this checkout's own operator verbs directly, and none mutates
os.environ["PICKUP_DEPLOYMENT"] globally.

RED (repo-root verb invocation, the row-1237-1244/1248 leak class): a synthetic fixture file
that builds a subprocess argv from `REPO / "led"` (REPO bound to this checkout's own root, the
same top-of-file convention every real seen-red driver uses) -- refused, naming the offending
line and verb.

RED (repo-root verb invocation via legacy/ path): the same shape, one level deeper --
`REPO / "legacy" / "pickup"` -- also refused.

RED (os.environ global mutation): a synthetic fixture file that does
`os.environ["PICKUP_DEPLOYMENT"] = "/some/path"` directly -- refused, naming the "pin
per-subprocess, never inherited" violation.

GREEN (scratch-scoped invocation stays clean): a synthetic fixture that invokes
`dest / "led"` (dest a tempfile.mkdtemp()-derived scratch path, NOT one of the REPO-like names)
-- the safe, existing convention -- must NOT be flagged.

GREEN (local env dict stays clean): a synthetic fixture that builds
`env = {**os.environ, "PICKUP_DEPLOYMENT": str(p)}` and passes it via a subprocess call's own
`env=` kwarg -- the safe, existing convention -- must NOT be flagged.

Runs against throwaway tempfile copies; zero residue in the repo itself."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
GATE = REPO / "gates" / "fixture_deployment_pin_guard.py"

RED_REPO_LED = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    return subprocess.run([str(REPO / "led"), "finding", "hello"], capture_output=True, text=True)
'''

RED_REPO_LEGACY_PICKUP = '''\
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it():
    return subprocess.run([str(REPO / "legacy" / "pickup")], capture_output=True, text=True)
'''

RED_ENVIRON_MUTATION = '''\
import os
import subprocess

os.environ["PICKUP_DEPLOYMENT"] = "/tmp/whatever/deployment.json"


def run_it():
    return subprocess.run(["true"], capture_output=True, text=True)
'''

GREEN_SCRATCH_SCOPED = '''\
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_it(dest: Path):
    return subprocess.run([str(dest / "led"), "finding", "hello"], capture_output=True, text=True)
'''

GREEN_LOCAL_ENV_DICT = '''\
import os
import subprocess
from pathlib import Path


def run_it(p: Path):
    env = {**os.environ, "PICKUP_DEPLOYMENT": str(p)}
    return subprocess.run(["some-verb"], capture_output=True, text=True, env=env)
'''


def _run_gate(*paths: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GATE), *[str(p) for p in paths]],
                           capture_output=True, text=True)


def main() -> int:
    failures: list[str] = []

    # --- GREEN: the real fixture tree -------------------------------------------------------
    r = _run_gate()
    ok = r.returncode == 0
    check("GREEN-real-tree", ok, f"exit={r.returncode}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}",
          failures)

    with tempfile.TemporaryDirectory(prefix="fixture-deployment-pin-guard-") as tmp:
        tmp_path = Path(tmp)

        specimens = {
            "red-repo-led.py": (RED_REPO_LED, True, "led"),
            "red-repo-legacy-pickup.py": (RED_REPO_LEGACY_PICKUP, True, "pickup"),
            "red-environ-mutation.py": (RED_ENVIRON_MUTATION, True, None),
            "green-scratch-scoped.py": (GREEN_SCRATCH_SCOPED, False, None),
            "green-local-env-dict.py": (GREEN_LOCAL_ENV_DICT, False, None),
        }
        for fname, (content, should_be_bad, verb) in specimens.items():
            spath = tmp_path / fname
            spath.write_text(content, encoding="utf-8")
            r = _run_gate(spath)
            is_bad = r.returncode != 0
            label = fname.rsplit(".", 1)[0].upper().replace("-", "_")
            ok = is_bad == should_be_bad
            detail = f"exit={r.returncode}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"
            if should_be_bad and verb:
                ok = ok and (verb in r.stdout)
            check(label, ok, detail, failures)
            if should_be_bad and ok:
                print("  " + r.stdout.strip().splitlines()[-1])

    print()
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures:
            print(f"\n!! {f}")
        return 1
    print("ALL CASES OK -- fixture-deployment-pin-guard both polarities, zero residue")
    return 0


def check(label: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"{'GREEN' if ok else 'RED  '} {'ok' if ok else 'FAIL'}: {label}")
    if not ok:
        failures.append(f"{label}:\n{detail}")


if __name__ == "__main__":
    raise SystemExit(main())
