validate_work_item() (the ledger's work-item write-boundary trigger, s22..s33's accreting
monolith) has an authored, scratch-witnessed successor: `kernel/lineage/s35-validation-
decomposition.sql`. It re-issues the same trigger as a thin dispatcher over four per-concern
leaf functions (validate_work_item_open / validate_work_item_depends /
validate_work_item_close_is_composite / validate_work_item_close), so a future delta that
touches one concern (say, a new depends-edge refusal) re-issues ONE leaf instead of copying
the whole function forward with a prose "unchanged, byte-for-byte" claim nothing checks. Not
wired into LINEAGE_CHAIN — authored and scratch-witnessed only, same posture as s32/s33.

Shape decision, empirically witnessed (not assumed): a dispatcher-with-leaves (one trigger,
leaves called in stated order inside one function body) was compared against multiple
triggers under enforced alphabetical naming, specifically for s30's own default-then-check
ordering pair. The multi-trigger shape's failure mode is real and silent: an innocuous
`ALTER TRIGGER ... RENAME` reversed firing order with zero errors and landed a row the
policy meant to always refuse. The dispatcher shape was taken; see the delta's own header for
the full transcript and `seen-red/s35-validation-decomposition/run_fixtures.py`'s case q for
the live re-run.

New standing gate: `gates/validation_leaf_manifest_gate.py` bank the canonical text of the
four leaves and refuses a future re-issue that silently mutates one without
`--declare-change` naming it — the mechanized half of the byte-identity claim s28..s33's own
"unchanged, byte-for-byte" comments could never check.

<!-- doc-attest-exempt: point-in-time orchestrator changelog entry -->
