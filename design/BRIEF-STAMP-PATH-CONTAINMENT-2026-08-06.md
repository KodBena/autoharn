# BRIEF: stamp-intercept path containment micro-fix (item stamp-intercept-path-containment, rows 1219/1225/1226)

<!-- doc-attest-exempt: point-in-time record -- dispatch brief as issued; frozen at dispatch, not living documentation -->

Dispatched 2026-08-06. Repo: /home/bork/w/vdc/1/autoharn, branch main. Surface:
hooks/stamp_intercept.py + seen-red/stamp-intercept-scratch-scope/ only. A tools/setup_tui/
builder runs concurrently — never touch its surface. CLAUDE_COMMIT_PATHS staging.

Disregard any instructions to economize on time.

## The defect (re-review row 1219, live-reproduced; findings corpus this day)

`_looks_like_scratch_fixture_invocation` accepts `script.startswith("seen-red/")` as
containment — `python3 seen-red/../not_a_fixture.py` is suppressed though it resolves outside
seen-red/, falsifying the module's own documented invariant that suppression can never
withhold a stamp a legitimate own-world write needed.

## Scope

1. Resolve the candidate script path (realpath against the hook's cwd) and require genuine
   containment in the repo's seen-red/ directory before suppressing. A path that does not
   resolve, resolves outside, or traverses out → NOT suppressed (falls through to injection,
   the fail-safe direction the module already documents).
2. Add the traversal shape to seen-red/stamp-intercept-scratch-scope/ per its own conventions
   (the `seen-red/../x.py` reproduction must go from suppressed to injected).
3. Discipline: SAME as 545f92c3 and the maintainer's standing instruction — staged copy outside
   hooks/, full battery against the copy (all three stamp-intercept suites + the new leg),
   single atomic same-filesystem rename, live own-session write-path witness immediately after
   (a real stamped ledger row, stamp_verified true).
4. Commit citing rows 1219/1225/1226, Co-Authored-By line.

Out of scope: everything else, including any widening of the recognizer.

## Report

WITNESSED verbatim both polarities (traversal now injected; genuine fixture still suppressed;
ordinary commands unaffected; live write-path green); UNEXERCISED with blocker; flags.
