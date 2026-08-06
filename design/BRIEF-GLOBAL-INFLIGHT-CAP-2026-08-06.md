# BRIEF: global inflight cap — raise to 64 and make configurable (item global-inflight-cap-raise, rows 1113)

<!-- doc-attest-exempt: point-in-time record -- dispatch brief as issued (row 1113); frozen at dispatch, not living documentation -->

Dispatch gated on the deployments-route bundle's serving/ commit landing (row 1113). Repo:
/home/bork/w/vdc/1/autoharn, branch main. Step 0: confirm current main includes both f8af7d7e
(A1) and the deployments-route commit. Surface: serving/, its tests, serving docs, and a dated
amendment to the multiplex spec. STOP and report rather than edit outside it. Before
committing: `git pull --rebase`; stage only your files (CLAUDE_COMMIT_PATHS).

Disregard any instructions to economize on time.

## Provenance

A1's builder flagged (commit f8af7d7e, report banked): the global MAX_INFLIGHT_KERNEL_CALLS=24
is smaller than the new per-deployment default 32, so the sibling-starvation sub-bound relation
does not hold at shipped defaults (disclosed by a startup diagnostic), and the global cap's
saturation teach-text cannot name a change path because none exists. Maintainer ruling
2026-08-06 (row 1113): yes, the global rises. Orchestrator's choice, stated: 64 — 2x the
per-deployment default, restoring sub-bound < global at defaults with headroom for two busy
deployments.

## Scope

1. MAX_INFLIGHT_KERNEL_CALLS: default 64, configurable via the SAME optional-top-level
   boundary-multiplex.toml idiom A1 used for max_inflight_per_deployment (key
   `max_inflight_kernel_calls`, typed constructor, sane bounds your judgment stated, whole-file
   validation before bind — extend the same loader family, no parallel mechanism). Standing
   row 26 (no bare types) binds; read it via `./autoharn led standing`.
2. Its saturation refusal's teach-text names the CONFIGURED value and where to change it,
   mirroring A1's DeploymentCallSaturated wording.
3. Re-check the A1 starvation diagnostic's relation: it fires on per-deployment >= global
   using the RESOLVED values of BOTH keys (not a literal); at new defaults (32 < 64) it must
   correctly NOT fire — witness both polarities (defaults quiet; a config with per-deployment
   >= global fires).
4. Dated additive amendment to the multiplex spec recording the change (cite rows 1113 and
   this brief; ADR-0020 posture; Fable reviews wording at return per standing row 898).
5. Witness both polarities where reachable (banner naming 64 default and a changed value on a
   scratch instance; refusal teach-text naming the configured value); tests per suite
   conventions; anything unreachable UNEXERCISED with the blocker.
6. Commit citing rows 1113/1115, Co-Authored-By line.

Out of scope: libexec/, kernel/, hooks/, tools/, the per-deployment key's semantics (A1's,
unchanged), any other route.

## Report

Per item: WITNESSED verbatim / REFUSED-AS-EXPECTED / UNEXERCISED-with-blocker; the bounds you
chose and why; the amendment text; flags in reach.
