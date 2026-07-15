subject: 3032624

Supersession now means uniform retraction from current truth, for every kind including
work items (ratified spec, s31). If you supersede a `work_closed` row, the item reads
OPEN again everywhere current-truth is read (`work_item_current`, strict blockers, the
stop gate's views); a superseded claim reads unclaimed; a superseded `blocks-close` edge
stops gating. Reinstatement-free: superseding the superseder does NOT revive the victim
-- re-issue the content as a new row instead. A retracted `work_opened` permanently
burns its slug (redo = open a NEW slug with `--refs row:<id>` to the old). New
violations member `orphaned_by_retraction` surfaces events whose opening act was
retracted. Worlds scaffolded from this commit on carry s31; existing worlds pick it up
at their next `./migrate`.

<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->
