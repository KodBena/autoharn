subject: 2d490245
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

New verb `./autoharn setup-schema`: prints `tools/setup_tui/data/config_schema.toml`
byte-verbatim to stdout — the sanctioned, layout-independent access point for external
consumers (dev: sibling checkout; build/CI: pinned checkout), per ledger row 1063. Default mode
never injects a header into stdout; a provenance line (source path, sha256, repo HEAD commit,
read time) prints to stderr unconditionally, and `--provenance` prints the same triple as JSON
on stdout for machine consumers. Missing/unreadable schema refuses loudly, nonzero exit, never
empty stdout with exit 0. WITNESSED, this checkout: `./autoharn setup-schema --provenance` ->
`{"source_path": "tools/setup_tui/data/config_schema.toml", "sha256":
"271303072d0...4f3", "repo_commit": "87d1068...", "read_at": "2026-08-06T07:29:01Z"}`.

**What a restarting orchestrator needs to know — the announce-by-missive contract.** The verb's
own commissioning note is a standing promise: format/path changes to the exported schema are
announced by missive on the originating thread BEFORE they land, so a consumer pinning a hash
knows to re-pull rather than silently drifting. Already exercised for real: when commit
`4440fb34` added `max_inflight_per_deployment`/`max_inflight_kernel_calls` to the schema, missive
row 1241 announced the sha256 change (`b0bb1c8a...` -> `271303072d0...`) on the same thread
that originally requested the tunables — the mechanism the verb committed to, actually used, not
merely documented.
