# BRIEF: deployments roster route + principal-name served join (items deployment-listing-route, principal-name-served-join; rows 1102)

<!-- doc-attest-exempt: point-in-time record -- dispatch brief as issued (row 1102); frozen at dispatch, not living documentation -->

Dispatch gated on the A1+A2 builder's serving/ commit landing (row 1102: same-surface
contention). Repo: /home/bork/w/vdc/1/autoharn, branch main. Step 0: confirm current main and
that the multiplex-inflight-cap/banking commit is present (git log will show it); your surface
is serving/, its tests, and the serving docs. If you believe you must edit outside it, STOP and
report. Before committing, `git pull --rebase`; stage only your files (CLAUDE_COMMIT_PATHS).

Disregard any instructions to economize on time.

## Provenance (both FRESH2-adjudicated, maintainer-promoted 2026-08-06, row 1102)

Item 1 — deployment-listing-route (FRESH2 B2): "no route lists the hub's deployments; the
panel hand-maintains KNOWN_DEPLOYMENTS and disowns the TOML as ground truth. A /deployments
route (names + per-deployment health summary) is boundary-general."

Item 2 — principal-name-served-join (FRESH2 C8): "every boundary client re-implements the
actor-id -> principal-name join client-side (the panel's ReviewGapTab discloses the gap in its
own UI copy). A non-SPA client wants the same join. Shape: additive _name-annotated variants or
an annotation flag on the relevant views, VIEW_REGISTRY discipline."

## Before you design

Read law/adr/ ADR-0000, ADR-0008, ADR-0012 in full; the multiplex spec
(design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md) for how deployments are declared and
served; VIEW_REGISTRY's own discipline in serving/; and the s40/s41 lineage headers for what a
principal registration row actually asserts. Standing row 26 (no bare types) binds all new
code — read it verbatim via `./autoharn led standing`.

## Scope

1. **GET /deployments** (or the house-idiomatic path — follow existing route conventions): the
   roster the multiplex TOML already defines, served read-only — deployment names plus a
   per-deployment summary whose vocabulary is HONEST under ADR-0008: state only what the
   service actually knows (declared, reachable, serving), never an umbrella "healthy"; typed
   response model per house conventions. The panel's KNOWN_DEPLOYMENTS hardcode is the named
   consumer; do not edit the panel (their repo, not yours) — the route is the fix.
2. **Principal-name annotation** on the views where an actor id is served to humans (review
   gaps, work items, ledger reads — enumerate what you actually annotate and why): additive
   `_name`-annotated variants or an annotation flag, your judgment against VIEW_REGISTRY's own
   discipline, defended in one line. Absence stays typed absence: an actor id with no
   registration row is served as such, never an invented or empty-string name. No existing
   response shape narrowed or renamed.
3. **Witness.** Both polarities where reachable: the roster route against the live hub config
   (real output pasted) and its refusal/empty shape; annotation with a registered and an
   unregistered actor. Tests per the suite's own conventions. Anything unreachable:
   UNEXERCISED with the concrete blocker.
4. **Docs**: the serving docs' own route table/README per their conventions, witnessed output
   in any example.
5. **Commit** on main, citing rows 1102 and the two item slugs, Co-Authored-By line.

Out of scope: libexec/, kernel/, law/, hooks/, tools/, the panel repo, response-model work
beyond these two features (A4 is a separate item), any write route.

## Report

Per item: what changed where, design choices with one-line rationales (esp. annotation shape
and the health-summary vocabulary), witnessed outputs verbatim both polarities or
UNEXERCISED-with-blocker, docs touched, anything flagged in reach.
