#!/usr/bin/env python3
"""adjudicate_repro — the criterion-phase repro-adjudication harness (consult 37 §1). Every criterion-
review finding carries a repro recipe; this runs each recipe against the built artifact and classifies it:
REPRODUCES -> real (a genuine artifact-residual-defect); FAILS -> noise (the defect does not reproduce).
Noise is DATA (round-cap / nit-manufacturing calibration) — it is banked, never discarded.

A recipe is a self-checking shell script that sets up its inputs, runs the artifact, and EXITS 0 iff the
claimed defect REPRODUCES (the artifact's observed behavior differs from what the finding says the spec
requires) — non-zero iff it does not. Each recipe runs in its own throwaway temp dir with the artifact on
PATH. All output (stdout/stderr/exit) is banked per recipe; the verdict summary is written to the outdir.

  adjudicate_repro.py --artifact <inventory-path> --recipes <dir-of-*.sh> --out <bank-dir>

Lazy imports banned. This is a HARNESS built pre-run; the recipes are produced by the criterion reviewers
at the criterion phase and dropped into --recipes.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def adjudicate_one(recipe: Path, artifact: Path) -> dict:
    """Run one recipe in a throwaway dir with the artifact on PATH; classify reproduces/noise."""
    with tempfile.TemporaryDirectory(prefix="adj_") as td:
        env = dict(os.environ)
        env["PATH"] = f"{artifact.parent}:{env.get('PATH', '')}"
        env["ARTIFACT"] = str(artifact)
        cp = subprocess.run(["bash", str(recipe)], cwd=td, env=env,
                            capture_output=True, text=True, timeout=120)
    reproduces = cp.returncode == 0
    return {
        "recipe": recipe.name,
        "verdict": "real" if reproduces else "noise",
        "exit": cp.returncode,
        "stdout": cp.stdout[-4000:],
        "stderr": cp.stderr[-2000:],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", type=Path, required=True, help="the built inventory tool")
    ap.add_argument("--recipes", type=Path, required=True, help="dir of *.sh repro recipes")
    ap.add_argument("--out", type=Path, required=True, help="bank dir for per-recipe output + summary")
    a = ap.parse_args(argv)
    if not a.artifact.exists():
        print(f"artifact not found: {a.artifact}", file=sys.stderr)
        return 2
    a.out.mkdir(parents=True, exist_ok=True)
    recipes = sorted(a.recipes.glob("*.sh"))
    results = []
    for r in recipes:
        res = adjudicate_one(r, a.artifact)
        (a.out / f"{r.stem}.result.txt").write_text(
            f"# {res['recipe']}: {res['verdict'].upper()} (exit {res['exit']})\n"
            f"--- stdout ---\n{res['stdout']}\n--- stderr ---\n{res['stderr']}\n", encoding="utf-8")
        results.append(res)
        print(f"  [{res['verdict']:5}] {res['recipe']} (exit {res['exit']})")
    real = [r for r in results if r["verdict"] == "real"]
    noise = [r for r in results if r["verdict"] == "noise"]
    (a.out / "SUMMARY.json").write_text(json.dumps(
        {"total": len(results), "real": [r["recipe"] for r in real],
         "noise": [r["recipe"] for r in noise]}, indent=2), encoding="utf-8")
    print(f"# adjudication: {len(real)} REAL, {len(noise)} NOISE (banked in {a.out}); "
          f"real -> file as artifact-residual-defect, noise -> file + dispose explained.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
