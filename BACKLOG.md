# BACKLOG — retired as a file; the work tracker is the ledger

Audience: anyone who followed a link here

This repository's work tracking lives in its append-only Postgres ledger, not in this
file (maintainer ruling, 2026-07-12 afternoon, witnessed as tracker ledger row 137 —
`./led show 137` reads it: while the work is not yet in maintenance mode, the tracker
is maintained in local Postgres only; this file's only remaining job is to say where).
The coordinates, from this repository's own `deployment.json` (untracked; see
`deployment.json.example` + README.md "Configuration" for the field shape):

- database `toy` on this deployment's own `host`
- schema `autoharn` (kernel schema `autoharn_kernel`, role `autoharn_rw`)

To read it: `./pickup` at this repository's root shows the open set, in-force decisions,
and resources; `./led --recent` shows the latest rows; `./led show <id>` shows one row
in full. The ledger is the only liveness surface — nothing in any `.md` file, this one
included, says what is currently open or decided.

The 6,222-line dated narrative record this file carried until 2026-07-12 (the
"BACKLOG's dated tail" that other documents in this repository cite by entry name) is
preserved in git history, not deleted: read it with `git show d6f64ee:BACKLOG.md` (the
last commit carrying the full file). Those citations remain honest pointers into that
frozen record — the same declared-history standing the `judgment/` directory has. New
narrative goes into standalone committed documents (retrospectives, specs, incident
notes) cited by ledger rows, never into a growing file of unknown liveness — a 6k-line
markdown file where nobody can tell live from dust is the disease the SQL tracker
cures, which is exactly why this file retired.

<!-- doc-attest-exempt: pointer stub; the dated-record era it points at is point-in-time history -->
