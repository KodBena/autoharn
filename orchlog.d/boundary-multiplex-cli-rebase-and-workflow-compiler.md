subject: f58c1be
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

Two coupled landings, same day (ledger rows 1652-1661; specs
[design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md](../design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md),
[design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md](../design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md),
[design/FABLE-WORKFLOW-UNIT-COMPILER-SPEC.md](../design/FABLE-WORKFLOW-UNIT-COMPILER-SPEC.md)).

**`led`/`pickup`/`asof-export`/`distance-to-clean` are now HTTP clients of the boundary
service, not direct `psql` callers.** The direct-`psql` originals moved to `./legacy/` on any
world scaffolded from this commit forward (existing worlds are untouched — runs are linear, no
in-place migration). Two new *optional* `deployment.json` keys, `boundary_url` and
`boundary_deployment`, are refused-if-absent by the rebased shims; a deployment with neither key
(any `bootstrap/track-work.sh` standing tracker, or a `new-project.sh --new-world` scaffold that
didn't pass `--boundary-url`/`--boundary-deployment`) sees every rebased verb refuse loudly with
exit 4, teaching `./legacy/<verb>` as the working path. `judge`/`audit`/bootstrap scaffolding do
NOT rebase (§5's own closed enumeration). Route table grew eleven → fourteen (row 1652) to give
the CLI rebase a real read surface: `GET /d/{d}/views/{view}` (closed allowlist), `GET
/d/{d}/rows/asof/{ts}`, `GET /d/{d}/meta`. The service itself now multiplexes N deployments from
one process via `--config boundary-multiplex.toml` (the old single-file `--deployment` launch is
retired); every route gained a mandatory `/d/{deployment}` prefix.

**A genuine hazard caught and fixed during this documentation pass, not by the original build:**
`bootstrap/track-work.sh` wrote the four rebased shims but never wrote `./legacy/` — so a fresh
work-tracker deployment's `./led` refused, pointed at a `./legacy/led` that did not exist, and had
no working path at all. Fixed in `bootstrap/track-work.sh` (now writes `./legacy/` identically to
`new-project.sh`); witnessed live against a fresh scratch deployment on the toy database, torn
down with zero residue.

**The workflow-unit compiler** (`tools/workflow_compile.py`, commission row 1658) turns a
fixed-shape `design/workflows/*.toml` into a hydration script (`led work open`/`depends`/an
obligation act) and a driver script (claim/dispatch/close by kernel conversation). Its one design
commitment: no enforcement logic of its own — every blocker (dependency, completion, obligation,
role) is a kernel fact the driver discovers by attempting the act and reading the kernel's own
refusal, never precomputed. `--instance <token>` is mandatory on both scripts (row 1660 amendment
— a TOML is a reusable shape, an instance is one engagement). WC1-WC7 all witnessed both
polarities on the exercise world `omega-lab` at build time (row 1661); this documentation pass
re-witnessed the dependency-blocker refusal/acceptance pair independently on a throwaway
`--new-world` scratch scaffold. Named seams: the driver's own tally undercounts cosmetically; the
J2 obligation-need heuristic fits the four on-file specimens' vocabulary, not a formal grammar;
and every `led work *` call the driver makes runs through `./legacy/led`, because the served
boundary does not cover `led work *` yet (a disclosed, separately-named scope boundary, not an
oversight).

**Where the operator-facing detail lives:** `user-guide/USER-RECIPES-FAQ.md`'s "Boundary
multiplex, CLI rebase, and the workflow-unit compiler (2026-07-18)" section (the exit-code split,
the multiplex TOML shape, the `led work *` coverage gap verbatim from `led.tmpl`'s own SCOPE
section, and the compiler walkthrough); `serving/README.md` for the mechanism reference.
