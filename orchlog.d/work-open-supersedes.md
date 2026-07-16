subject: fc3ac17
<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->

`led work open` now accepts `--supersedes <id>` — the verb you were missing when the
maintainer's "just supersede" answer met mis-encoded `work_opened` rows. It writes the
same supersedes column the generic path uses and composes with `--refs`/`--parent`/
`--discharge`.

Know the s31 consequences before you use it (an advisory prints them each time):
the superseded open leaves current truth and its SLUG IS PERMANENTLY BURNED — your
replacement row must carry a new slug (the kernel refuses reuse, with a teach-text),
and any surviving claims/edges naming the old slug become `orphaned_by_retraction`
rows in `work violations` until you re-issue them against the new slug. Witnessed
re-issue order that works cleanly: open the replacement (`--supersedes <old-open-id>
--refs <commission-row>`), then re-claim, then re-edge. Historical orphan rows
persist by design (reinstatement-free) — they are record, not debt to chase.

Scope reminder from the maintainer-relayed intervention: re-issue LIVE mis-encoded
rows; leave CLOSED, settled items' refs gaps as disclosed history unless the
maintainer orders otherwise. And the standing instruction stands: no raw ledger
writes, ever, under any gap — a missing verb is a backflow note, never an UPDATE.
