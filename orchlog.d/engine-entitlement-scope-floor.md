subject: e1b02f4d
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

`./autoharn judge --layer entitlement` used to report `NO-FLOOR` — the layer's ASP encoding
(`engine/lp/ledger_entitlement.lp`) existed and ran, but had no independent SQL producer to
differential against, so a bare `./judge` run silently skipped it rather than proving anything.
That gap is closed: `engine/ledger_floor.py` now derives the same five predicates in SQL
(`reaches_genesis/1`, `reaches_genesis_scoped/2`, `open_scope/1`, `may_read_surface/2`,
`scope_disclosure/2` — the s70 scope additions alongside the pre-existing s60/s64 entitlement
ones), and `./judge --layer entitlement` (or a bare `./judge` auto-detecting the layer) now
runs a real two-producer differential and reports AGREE/DIVERGE like every other layer.

**What a restarting orchestrator would trip on:** if you remember `entitlement` as the one
layer `judge` always waves through with a NO-FLOOR notice, that's stale — it now actually
checks. A world born before s70 (which is every world today, autoharn3 included —
runs-are-linear, see the scope-binding notes) has no `principal_scope_bound` rows to speak of,
so the scope predicates trivially agree empty; the check becomes live and meaningful once a
world scoped-binds a principal for real. Fail-closed arming and the NULL-mode "no fact" reading
are both encoded on both sides of the differential (SQL and ASP), so a divergence here would
mean the two producers disagree about who may read what — treat it exactly as seriously as any
other judge DIVERGE.
