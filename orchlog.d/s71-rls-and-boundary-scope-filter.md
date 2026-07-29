subject: 94b4839d,dc643dfb
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

Two landings that close the enforcement half of scope binding (see the sibling note
`s70-scope-binding-and-dispatch-mint.md` for the minting half): `kernel/lineage/
s71-row-level-scope-policies.sql` (RLS, kernel-grade, future-birth-only — same runs-are-linear
caveat as s70, NOT live on autoharn3) and `serving/boundary_scope_filter.py` (the boundary-side
enforcement, which IS live on main today).

**What a restarting orchestrator needs to know about the live filter:**

- Every GET route that returns row-shaped content funnels through one seam
  (`boundary_service._json_read_response`), so a scoped-out row never reaches a caller as
  content — it reaches as a typed redaction marker: `{id_field: <value>, "redacted": true,
  "scope": {"family": ..., "value": ...}}`, plus `row_hash` when the disclosure mode is
  `hash_stub` and the surface has one. Existence still shows (a count/page is honest); content
  and rationale do not.
- **Fail-closed arming, a real behavior a fix round corrected mid-build (row 889):** a
  `principal_scopes` row existing at all arms the principal onto EXACTLY the surfaces named in
  its own `scope_surfaces`. If `scope_surfaces IS NULL` — an armed principal handed no
  allow-list — every filtered route returns NOTHING for that principal, exclusions
  notwithstanding. An "exclusion-only" scope binding (exclusions set, no explicit
  `scope_surfaces`) does NOT mean "open surface minus these rows" — it means "no surface
  granted, read nothing." A deployment wanting exclusion-only behavior on named surfaces must
  bind `scope_surfaces` explicitly.
- **Cost is disclosed, not hidden, and you should expect it if you're timing anything on a
  scope-armed world:** a minted-but-unbound principal (the common case, fail-safe open) pays
  two small extra round trips per read — roughly +150 to +170 percent on loopback-HTTP-to-
  real-Postgres in the measured scratch run (absolute numbers are box-dependent; the shape is
  the disclosed fact). A `full`-tier-excluded existing row also costs measurably more than a
  genuinely-absent id (~+33-44ms in the same run) even though both now return a byte-identical
  404 body — this is an open known (ledger row 943), named in the module docstring, not
  papered over.
- Anonymous and vendor-stamped callers always resolve to the open scope at this layer — there
  is no verified principal id to bind a scope query to for either channel yet (S3
  stamp-binding, a separate not-yet-built mechanism, would change that for vendor callers).

If you're auditing "does this world enforce scope," check whether it was born after s70/s71
landed (a fresh `--new-world` scaffold does carry both in `LINEAGE_CHAIN` now) — the boundary
filter code runs everywhere on main, but `resolve_scope` probes `principal_scopes`'s own
existence first (`regclass_exists`) and degrades to the open scope, not an error, on a world
that predates the kernel deltas (the view itself doesn't exist there yet).
