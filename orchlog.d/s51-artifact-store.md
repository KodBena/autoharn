subject: 0c5c382
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

**A new kernel-governed content-addressed blob store, `led artifact put|get|stat`
(kernel/lineage/s51-artifact-store.sql, design/FABLE-ARTIFACT-STORE-SPEC.md, merged
`0c5c382`, 2026-07-18).** `kernel.artifact` is a fifth s43-shaped SECURITY DEFINER write
boundary (`kernel.artifact_write`, alongside `ledger_write`/`review_write`/
`registration_write`/`obligation_write`): sha256 as primary key, `bytea` payload, a
server-derived and CHECK-enforced size column, a closed v1 media-type vocabulary, and
append-only enforcement via trigger plus grant revocation, matching every other
kernel-governed table's shape. `put` computes the hash server-side and refuses on a
mismatch (`artifact_too_large` at 1 MiB, typed and journaled digest-only through s43's
existing refusal journal — never the payload bytes themselves); `get` re-verifies the hash
on the way out and refuses to emit corrupt bytes rather than silently handing them over;
`stat` reports size/media-type/registrant without transferring the payload.
`refusal_surface_check` widened by one member (`'artifact'`) — the only touch this delta
makes on existing s43 surface.

**Transport has since moved on from this commit's own state, note the direction if you're
reading this cold.** At merge time `artifact put|get|stat` landed template-side only in
`legacy-led.tmpl` (the direct-psql original, payload carried through a local temp file and
a `psql` backtick-command value carrier — never an execve argument or a `-c` splice, the
same shape the row-1637/1643 SQL-injection-class fixes established); the served `led.tmpl`
of that day refused the family, teaching `./legacy/led`. As of the later
legacy-led-retirement rebase (ledger row 1149/1150, `legacy-led.tmpl` deleted outright),
`led artifact put|get|stat` is part of the served boundary's full coverage — there is no
longer a `./legacy/led` to fall back to for this family or any other. If you are picking up
a world scaffolded between `0c5c382` and the legacy-led-retirement commit, expect the
legacy-only behavior described above instead.

Where the operator-facing detail lives: `user-guide/USER-RECIPES-FAQ.md`'s "Which `led`
subcommands go over the boundary?" entry names the current served-coverage state; the spec
document has the full write-boundary and refusal shape.
