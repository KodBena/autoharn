#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for gates/link_integrity.py (the class-not-instance
fix for the maintainer's 2026-07-11 doc-legibility indictment), plus the gitlink-awareness fix
for work_opened `worktree-submodule-link-integrity` (2026-07-19).

Cases, driven against real files in a throwaway temp directory (never against tracked repo
content -- an intentionally-broken link committed as a fixture would itself trip the gate's own
real run, which is exactly the failure this harness exists to prevent):

  RED   -- a fixture doc with a relative link to a target that does not exist. The gate must
            name the file:line and the dangling target, and exit 1.
  GREEN -- the identical shape, but the target exists (a sibling file in the same temp dir).
            The gate must exit 0, clean.
  SUBMODULE-UNINIT   -- a link into a path `uninitialized_submodules()` reports as an
            uninitialized submodule, whose target does not exist (the placeholder-dir-but-
            no-content shape a fresh `git worktree add` produces). The gate must refuse (exit 1)
            with the ONE teaching block, and must NOT list the target in the `broken` wall.
  SUBMODULE-CLEAN    -- the identical submodule path, but now reported as populated (empty set
            from `uninitialized_submodules()`) and the target file actually exists. The gate
            must exit 0, clean -- proving population is what un-refuses it.
  SUBMODULE-STILL-BROKEN -- the submodule path reported as populated, but the link target
            still does not exist (a real typo inside a populated submodule). The gate must
            catch this in the normal `broken` wall, exit 1 -- proving gitlink-awareness never
            masks a genuine defect once the submodule is actually populated.

`link_integrity.tracked_md` is monkeypatched to return the temp fixture's path (absolute --
`os.path.join(ROOT, rel)` short-circuits to an absolute `rel` untouched, so this never depends on
or mutates the real repo tree). `link_integrity.uninitialized_submodules` is monkeypatched per
case for the same reason (a live `git submodule status` call would depend on this checkout's own
init state, not the fixture's). Teardown removes the temp dir unconditionally.

Usage: python3 seen-red/link-integrity/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
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
    """Write fixture.md linking to rel_target, point the gate at just that file, capture output.
    No uninitialized submodules in play for this shape -- explicit empty set so the case is
    hermetic regardless of whether the invoking checkout itself has populated submodules."""
    fixture = tmp / "fixture.md"
    fixture.write_text(f"# Fixture\n\nSee [elsewhere]({rel_target}) for detail.\n", encoding="utf-8")
    g.tracked_md = lambda: [str(fixture)]
    g.uninitialized_submodules = lambda: set()
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = g.main()
    return rc, buf.getvalue()


def run_submodule_case(tmp: Path, populated: bool, target_exists: bool) -> tuple[int, str]:
    """Write fixture.md linking into a 'submod/inner.md' path under tmp. `populated` controls
    whether `uninitialized_submodules()` reports 'submod' as uninitialized (mirrors a fresh
    `git worktree add` gitlink placeholder) or omits it (mirrors a populated checkout);
    `target_exists` controls whether inner.md is actually present on disk."""
    subdir = tmp / "submod"
    subdir.mkdir(exist_ok=True)
    inner = subdir / "inner.md"
    if target_exists:
        inner.write_text("# Inner\n", encoding="utf-8")
    elif inner.exists():
        inner.unlink()
    fixture = tmp / "fixture.md"
    fixture.write_text("# Fixture\n\nSee [inner](submod/inner.md) for detail.\n", encoding="utf-8")
    g.tracked_md = lambda: [str(fixture)]
    sm_rel = os.path.relpath(subdir, g.ROOT)
    g.uninitialized_submodules = (lambda: set()) if populated else (lambda: {sm_rel})
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
        sm_uninit_rc, sm_uninit_out = run_submodule_case(tmp, populated=False, target_exists=False)
        sm_clean_rc, sm_clean_out = run_submodule_case(tmp, populated=True, target_exists=True)
        sm_broken_rc, sm_broken_out = run_submodule_case(tmp, populated=True, target_exists=False)

        if red_rc != 1:
            print(f"SPECIMEN INERT (red) -- expected exit 1 on a dangling link, got {red_rc}.")
            ok = False
        if green_rc != 0:
            print(f"SPECIMEN INERT (green) -- expected exit 0 on a resolving link, got {green_rc}.")
            ok = False
        if sm_uninit_rc != 1:
            print(f"SPECIMEN INERT (submodule-uninit) -- expected exit 1 (refuse+teach), got {sm_uninit_rc}.")
            ok = False
        if "broken link(s)" in sm_uninit_out:
            print("SPECIMEN INERT (submodule-uninit) -- target leaked into the `broken` wall "
                  "instead of the dedicated teaching block.")
            ok = False
        if "uninitialized submodule" not in sm_uninit_out or "git submodule update --init" not in sm_uninit_out:
            print("SPECIMEN INERT (submodule-uninit) -- missing the one-line teaching text.")
            ok = False
        if sm_clean_rc != 0:
            print(f"SPECIMEN INERT (submodule-clean) -- expected exit 0 once populated, got {sm_clean_rc}.")
            ok = False
        if sm_broken_rc != 1:
            print(f"SPECIMEN INERT (submodule-still-broken) -- expected exit 1, a real defect in a "
                  f"populated submodule must still read red, got {sm_broken_rc}.")
            ok = False
        if "uninitialized submodule" in sm_broken_out:
            print("SPECIMEN INERT (submodule-still-broken) -- a populated submodule's real broken "
                  "link was misclassified as an unpopulated-submodule gap.")
            ok = False

        print("# --- RED case: fixture.md links to ./nonexistent-target.md ---")
        print(red_out.rstrip())
        print(f"# link-integrity RED: exit={red_rc} (expect 1)")
        print()
        print("# --- GREEN case: fixture.md links to ./sibling.md (exists) ---")
        print(green_out.rstrip())
        print(f"# link-integrity GREEN: exit={green_rc} (expect 0)")
        print()
        print("# --- SUBMODULE-UNINIT case: link into an uninitialized-submodule path, target absent ---")
        print(sm_uninit_out.rstrip())
        print(f"# link-integrity SUBMODULE-UNINIT: exit={sm_uninit_rc} (expect 1, teaching block only)")
        print()
        print("# --- SUBMODULE-CLEAN case: same path reported populated, target present ---")
        print(sm_clean_out.rstrip())
        print(f"# link-integrity SUBMODULE-CLEAN: exit={sm_clean_rc} (expect 0)")
        print()
        print("# --- SUBMODULE-STILL-BROKEN case: same path reported populated, target absent ---")
        print(sm_broken_out.rstrip())
        print(f"# link-integrity SUBMODULE-STILL-BROKEN: exit={sm_broken_rc} (expect 1, normal wall)")

        if not ok:
            return 1
        print()
        print("# ALL POLARITIES CONFIRMED: dangling link -> exit 1 (named); resolving link -> exit 0 "
              "(clean); link into an uninitialized submodule -> exit 1 with ONE teaching block, never "
              "the broken-link wall; the same path once populated -> exit 0 clean, or exit 1 in the "
              "normal wall if genuinely broken.")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
