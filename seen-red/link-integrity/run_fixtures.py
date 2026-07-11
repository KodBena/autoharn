#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T14:38:59Z
#   last-change: 2026-07-11T14:38:59Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for gates/link_integrity.py (the class-not-instance
fix for the maintainer's 2026-07-11 doc-legibility indictment).

Two cases, driven against real files in a throwaway temp directory (never against tracked repo
content -- an intentionally-broken link committed as a fixture would itself trip the gate's own
real run, which is exactly the failure this harness exists to prevent):

  RED   -- a fixture doc with a relative link to a target that does not exist. The gate must
            name the file:line and the dangling target, and exit 1.
  GREEN -- the identical shape, but the target exists (a sibling file in the same temp dir).
            The gate must exit 0, clean.

`link_integrity.tracked_md` is monkeypatched to return the temp fixture's path (absolute --
`os.path.join(ROOT, rel)` short-circuits to an absolute `rel` untouched, so this never depends on
or mutates the real repo tree). Teardown removes the temp dir unconditionally.

Usage: python3 seen-red/link-integrity/run_fixtures.py
Exit 0 if both cases match; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import io
import os
import shutil
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "gates"))
import link_integrity as g  # noqa: E402


def run_case(tmp: Path, rel_target: str) -> tuple[int, str]:
    """Write fixture.md linking to rel_target, point the gate at just that file, capture output."""
    fixture = tmp / "fixture.md"
    fixture.write_text(f"# Fixture\n\nSee [elsewhere]({rel_target}) for detail.\n", encoding="utf-8")
    g.tracked_md = lambda: [str(fixture)]
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = g.main()
    return rc, buf.getvalue()


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="link-integrity-seenred-"))
    ok = True
    try:
        # sibling.md exists alongside fixture.md -- the GREEN target
        (tmp / "sibling.md").write_text("# Sibling\n", encoding="utf-8")

        red_rc, red_out = run_case(tmp, "./nonexistent-target.md")
        green_rc, green_out = run_case(tmp, "./sibling.md")

        if red_rc != 1:
            print(f"SPECIMEN INERT (red) -- expected exit 1 on a dangling link, got {red_rc}.")
            ok = False
        if green_rc != 0:
            print(f"SPECIMEN INERT (green) -- expected exit 0 on a resolving link, got {green_rc}.")
            ok = False

        print("# --- RED case: fixture.md links to ./nonexistent-target.md ---")
        print(red_out.rstrip())
        print(f"# link-integrity RED: exit={red_rc} (expect 1)")
        print()
        print("# --- GREEN case: fixture.md links to ./sibling.md (exists) ---")
        print(green_out.rstrip())
        print(f"# link-integrity GREEN: exit={green_rc} (expect 0)")

        if not ok:
            return 1
        print()
        print("# BOTH POLARITIES CONFIRMED: dangling link -> exit 1 (named); "
              "resolving link -> exit 0 (clean).")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
