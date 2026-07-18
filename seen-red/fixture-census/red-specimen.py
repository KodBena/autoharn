#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T10:48:24Z
#   last-change: 2026-07-18T10:48:24Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""Seen-red specimen for the fixture-census gate ([C20]). Two cases, both mutating the gate's
own REGISTRY in memory to force a breach (the gate is self-referential — its own registry entry
is itself: "fixture-census": "gates/fixture_census.py" — so a real, on-disk, uncommitted probe
directory is the only way to exercise the tracked-vs-present distinction without ever landing an
actually-untracked directory in the committed tree).

Case 1 (orphan): emptying the registry, so every real seen-red dir reads as ORPHANED (a gate's
both-polarity proof with no owning registry entry, the exact rot the gate exists to catch).

Case 2 (git-tracked negative control, row 1502): the s45 adversarial review's adjudicated
finding -- commit 94f5b7a bundled a fixture_census registry row for defeat-pipeline before those
files were committed; a concurrent sibling builder's UNCOMMITTED hunk in the shared working tree
made the fixture read PRESENT-ON-DISK, and the pre-fix gate (presence-only) read GREEN on a
commit that, on a clean checkout, was actually RED. This case reproduces that shape directly: a
REAL directory is created under seen-red/, on disk, deliberately never `git add`ed, registered in
memory, and the gate is run against it expecting the UNTRACKED-dir breach specifically (not just
any breach) -- the negative control that proves the tracked-vs-present distinction the fix adds,
not merely that the gate can still go red some other way. The directory is removed in a finally
block so this specimen never leaves an actually-untracked probe sitting in the working tree.

The green half (for both cases) is the gate passing on the real, intact corpus
(gates/fixture_census.py exit 0, exercised directly by CI/pre-commit, not re-proven here). Run
from anywhere. Lazy imports banned."""
from __future__ import annotations

import contextlib
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "gates"))
import fixture_census  # noqa: E402

overall_ok = True

# --- case 1: orphan ---
fixture_census.REGISTRY = {}   # nothing registered -> every real seen-red dir is orphaned
rc1 = fixture_census.main()
ok1 = rc1 == 1
overall_ok = overall_ok and ok1
print(f"# fixture-census red-specimen (case 1, orphan): exit={rc1} (expect 1 — RED on an empty registry)")

# --- case 2: the git-tracked negative control (row 1502) ---
# a seen-red dir genuinely present on disk but never git-added -- the exact shape of the s45
# false-green. gates/fixture_census.py's own ROOT/SEEN_RED are computed from its own file
# location, not cwd, so this probe lands under the real repo's seen-red/ regardless of where
# this specimen is invoked from.
probe_name = "_fixture-census-untracked-probe"
probe_dir = os.path.abspath(os.path.join(fixture_census.SEEN_RED, probe_name))
os.makedirs(probe_dir, exist_ok=True)
with open(os.path.join(probe_dir, "red.txt"), "w", encoding="utf-8") as f:
    f.write("synthetic red evidence for the untracked-dir negative control -- never committed, "
            "removed by this specimen's own cleanup.\n")
try:
    fixture_census.REGISTRY = {probe_name: f"seen-red/{probe_name}/red.txt"}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc2 = fixture_census.main()
    out2 = buf.getvalue()
    print(out2, end="")
    ok2 = rc2 == 1 and f"UNTRACKED seen-red dir: seen-red/{probe_name}/" in out2
    overall_ok = overall_ok and ok2
    print(f"# fixture-census red-specimen (case 2, untracked-dir negative control): exit={rc2}, "
          f"UNTRACKED-dir breach present={('UNTRACKED seen-red dir: seen-red/' + probe_name + '/') in out2} "
          f"(expect exit 1 with that specific breach — presence-on-disk alone must NOT read green)")
finally:
    shutil.rmtree(probe_dir, ignore_errors=True)

raise SystemExit(0 if overall_ok else 1)
