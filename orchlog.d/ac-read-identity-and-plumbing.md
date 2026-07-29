subject: 513c91e2,296353dd,8f0694c8,dfa4eafb,8bda8d14,cb8efc35
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

The access-control batch's foundation landed as six merges the same day (2026-07-29), ahead of
the scope-binding work itself: the served boundary now resolves an identity on every GET (not
just writes) and journals who read what.

**What a restarting orchestrator would trip on:** every completed GET route in
`serving/boundary_service.py` now writes one line to `<world_dir>/.claude/logs/
boundary_reads.jsonl` — `{ts, deployment, route, view, identity, row_count}`, never row
content. This is additive and silent: no client-visible behavior changes, no new refusal, an
anonymous read still resolves and serves exactly as before (open scope). If you go looking for
"why is there a new file under `.claude/logs/`," that's it — it's a sibling of
`hooks/pretooluse_read_observer.py`'s journal, not the same channel (different producer,
different subject: an HTTP GET, not a Claude Code `Read` tool call).

Riding alongside: `tools/stamp_run.py`/`tools/stamp_mint.py` (a fix round closing a CRITICAL —
a hook-shaped stamp used to pass through un-refused; it now exits 4 with a teach-text
tripwire), a `setup_tui` config-extension + bare-types retrofit (five more typed homes,
`tools/setup_tui/boundary_config_values.py` as a new constructing home — no operator-visible
verb changed, just fewer stringly-typed internals), and ten new `.detect.sql` artifacts for
kernel deltas s60 through s69 (lineage-order flip witnesses; if you're auditing which kernel
deltas are behaviorally live versus merely present in a file, these are the mechanized answer
going forward).

None of this six-merge group changes the CLI surface an operator types. See the sibling notes
`s70-scope-binding-and-dispatch-mint.md`, `s71-rls-and-boundary-scope-filter.md`, and
`engine-entitlement-scope-floor.md` for the parts that do.
