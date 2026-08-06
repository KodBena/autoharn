# BRIEF: stamp-intercept scratch-world leakage fix (item stamp-intercept-scratch-world-leakage, rows 1159/1162)

<!-- doc-attest-exempt: point-in-time record -- dispatch brief as issued (row 1162); frozen at dispatch, not living documentation -->

Dispatched 2026-08-06 under the maintainer's own direction (row 1162) — the hooks/ live-session
hold is satisfied in substance: the ONLY live session executing this checkout's hooks is the
dispatching one, and it accepts the risk knowingly. That imposes YOUR prime constraint: the
hook must keep working at every instant — the dispatching session's own Bash writes run through
it continuously while you work. One atomic edit; `python3 -m py_compile` before saving is not
enough — witness the live path immediately after (below). Repo: /home/bork/w/vdc/1/autoharn,
branch main. Surface: hooks/stamp_intercept.py, its tests/fixtures per house convention, and
nothing else. A read-only reviewer is running concurrently; it commits nothing.

Disregard any instructions to economize on time.

## The defect (witnessed by three builders this session, ledger row 1159)

hooks/stamp_intercept.py injects the calling session's PGOPTIONS stamp into every Bash-tool
command whenever cwd carries a deployment.json. The injected variable is inherited by the
ENTIRE subprocess tree — so a fixture or scaffold that births/talks to a SCRATCH world from
inside that command sees its writes refused with the WRONG world's secret ("the write stamp did
not validate"). Fail-safe in direction (loud refusal, no corruption) but it silently degrades
witness coverage: builders work around it by stripping PGOPTIONS at module scope.

## Before you design

Read hooks/stamp_intercept.py end to end, plus whatever docs/tests it already carries; find how
the stamp is composed and what consumes it (the kernel's stamp validation — see the s23/s72
lineage headers for what a stamp binds). Read the workaround sites for the observed shapes:
`grep -rn PGOPTIONS seen-red/ | head`. Standing row 26 binds any new code.

## Scope

1. Scope the stamp to its intended consumer without breaking the session's own writes. The
   design is yours (state it and defend it in the file header) — candidate directions, not
   mandates: mark the injected value so nested invocations targeting a DIFFERENT
   deployment/schema drop it; or have the hook's injection wrap only the outermost psql-bearing
   command rather than exporting to the whole tree; or teach the scaffold/fixture entry points
   to clear inherited stamps (least preferred — it repairs every consumer instead of the one
   producer; ADR-0012 P1 argues the fix belongs at the injection site).
2. The session's own write path MUST keep validating: immediately after the edit, witness a
   real ledger write from an ordinary Bash command in this checkout (e.g. a `led` no-op read
   plus one benign decision row clearly labeled as the hook fix's own witness) — BOTH the
   pre-edit behavior (leakage reproduced, e.g. a scratch subprocess seeing the inherited stamp)
   and post-edit (scratch subprocess clean, own-session write still stamped and accepted).
   Verbatim outputs in your report.
3. Tests/fixtures per the hooks' own existing convention (find how sibling hooks are tested;
   follow it — if none exists, a seen-red family per that suite's conventions).
4. Commit citing rows 1159/1162/1163, Co-Authored-By line, CLAUDE_COMMIT_PATHS staging.

Out of scope: every other hook, kernel/, serving/, libexec/, bootstrap/, the builders'
PGOPTIONS-stripping workarounds (leave them; harmless belt-and-braces).

## Report

Design chosen and defended; WITNESSED verbatim both polarities including the own-session
write-path witness; UNEXERCISED with blocker; flags in reach.
