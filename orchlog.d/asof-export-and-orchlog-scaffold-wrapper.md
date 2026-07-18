subject: 1449e0c,bd949af
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

Two operator-facing items landed close together in the 2026-07-18 overnight batch (decision
rows 1580/1585), reviewer CLEAN on both, each its own scaffold-gated shim: the ledger-wide
as-of read/export verb (merged at `1449e0c`, scaffolded as `./asof-export`), and the
deployment scaffold now also writing an `./orchlog` wrapper (merged at `bd949af`). If you
are picking up work on a world scaffolded before `1449e0c`, `asof-export` is new to you; if
before `bd949af`, the `orchlog` wrapper is new to you (the two cutoffs are different
commits — see each item below for its own).

**`./asof-export` — ledger-wide AS-OF read plus inspection-copy export
(`asof-export-inspection-copy`, row 1585).** `./asof-export read --asof <ts>` prints the
WHOLE ledger's in-force reading at a timestamp — every kind of row, not just the three
`work_*` kinds `led work asof <ts>` already covered; that older verb is untouched and still
the right tool for work-item state specifically. `./asof-export export --asof <ts> --out
<dir>` writes the same reconstruction as a portable inspection copy: `ledger-asof.txt`
(human-readable, every column of every in-force row, no truncation),
`ledger-asof.json` (machine-readable), and `manifest.sha256` (a plain `sha256sum
-c`-checkable content hash). Re-export at the same `--out` REFUSES without `--force` — an
inspection copy is not silently clobbered. **Signing is deliberately absent, not deferred
behind an inert flag**: no `--sign` option exists at all, per the standing crypto ruling; the
manifest proves bytes match what left the act, nothing about who ran it or whether a
regenerated copy was substituted later. The as-of filter is `ledger.ts` (system insert time),
never the writer-supplied `event_declared_ts` — the same axis choice `led work asof` already
made, for the same reason: a writer can lie about `event_declared_ts`, never about when their
row actually landed. Lives entirely in a new template
(`bootstrap/templates/asof-export.tmpl`, live-exec like every sibling verb), not a `led`
subcommand and not a kernel delta — the file's own module docstring gives the full reasoning
for both calls, worth reading if you're deciding where a future read-only cross-cutting verb
belongs. Read/write-shape: `read` is a pure SELECT; `export`'s only filesystem writes are the
three named files under the operator-given `--out`, never a location it picks itself. Full
witnessed transcript: FAQ's "Ledger-wide as-of read and inspection-copy export" section.

**`./orchlog` scaffold wrapper (`deployment-orchlog-surfacing` half (b), row 1585).** Every
world scaffolded from `bd949af` or later gets an `./orchlog` shim beside `led`/`judge`/
`pickup`/`audit`, exec'ing autoharn's own `orchlog` verb against the harness checkout's repo
root — no `deployment.json`, no ledger connection, because what it reads is autoharn's git
history (`orchlog.d/*.md` notes, this file's own directory), never the deployment's own
ledger. A session working in that deployment can now run `./orchlog` or `./orchlog since
<sha>` directly instead of waiting on a hand-relayed memo row to learn what changed in
autoharn itself. **Half (a) is explicitly NOT this** — `./migrate` printing `./orchlog since
<pre-migration-head>` at the end of a run belongs to the separate, not-yet-maintainer-
approved migrate-verb item, and was left untouched here (decision row 1580 names this
split explicitly). **Existing deployments don't get the wrapper automatically** — there is no
scripted scaffold-refresh verb yet, so a pre-`bd949af` deployment either re-scaffolds or
copies the two-line shim by hand (shown in the FAQ entry: the shebang line and the exec line, plus a separate chmod +x). This is a different thing from
the `./orchlog` verb's own landing (`orchlog-changelog-verb`, already covered by this
directory's own README and reads its own notes) — this item is only the wiring that gets the
wrapper INTO a scaffolded deployment.

Migration: none for either — no kernel delta, nothing for `./migrate` to plan. A checkout on
`bd949af` or later already has both (it is downstream of `1449e0c`); the wrapper is picked
up by any world scaffolded from `bd949af` forward, or by hand for an older one (see above).
