# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T23:21:00Z
#   last-change: 2026-07-14T23:21:00Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""panel.backend.disposition — the PURE derivation of a manifest item's live status (spec S7).

This is the pairing-RCA-safe module in this build: status is NEVER computed once and stored,
it is recomputed from freshly-read ledger facts on EVERY request (ledger_read.py does the
reads; app.py calls `derive_status` with what it read). The lesson this design is built against
(ledger row 8f1cd25's own RCA, cited in this session's CLAUDE.md context) is that a computed
pairing/discharge VERDICT stored on a row can go stale or be wrong-by-construction the moment
the join it was derived from changes -- so this module stores nothing, computes from its
arguments alone, and is trivially unit-testable with no database (seen-red/panel-disposition/).

`derive_status` takes already-read `WitnessFacts` (ledger_read.py's job is turning a manifest
item's declared witness refs into these) and returns one of the four labels in
`config.STATUS_VALUES`. It knows nothing about SQL, HTTP, or the `./led` grammar -- a witness
that could not be resolved at read time (a bad ref) arrives here simply as `exists=False`.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WitnessFacts:
    """The live ledger facts for ONE manifest-item witness, already resolved by
    `ledger_read.py`. Carries no SQL/connection state -- a plain data record so this module's
    derivation is a pure function testable with hand-built values (spec S8's RED/GREEN
    specimens).

    ref_kind / ref: the manifest's own witness identity (a work slug, or a ledger row id as text).
    exists: the ref resolved to a real work item or ledger row at all. False for a dangling/
        invalid ref -- such a witness contributes nothing (never fabricate a witness to make an
        item look complete, spec S6's hack-rationalization warning).
    substantive: the resolved fact is strong enough to WITNESS the item -- a work item in state
        'closed' (an open/unclaimed work item is NOT substantive: an item still being worked is
        not yet witnessed), or any resolved ledger row (a 'row' witness is substantive as soon
        as it resolves -- it names a concrete act already on the ledger).
    cosign_target_row: the ledger row id a co-sign against this witness would `regards` -- the
        work item's `work_closed` row id, or the row id itself for a 'row' witness. None when
        there is nothing a co-sign could target yet (e.g. an open work item).
    maintainer_cosigned: a live, unsuperseded `review` row exists with `regards=cosign_target_row`,
        `verdict='attest'`, actor = the configured maintainer principal -- the SAME join
        `review_gap` uses (verdict + distinct actor), read fresh, never a stored flag.
    """
    ref_kind: str
    ref: str
    exists: bool
    substantive: bool
    cosign_target_row: int | None
    maintainer_cosigned: bool


def derive_status(witnesses: list[WitnessFacts]) -> str:
    """Pure. Rules (spec S7, restated exactly):

    - No witnesses, or every witness resolves to something not-yet-substantive (e.g. an open/
      unclaimed work item) -> OPEN.
    - >=1 substantive witness, none co-signed by the maintainer -> WITNESSED.
    - Some but not all substantive witnesses co-signed -> PARTIAL.
    - Every substantive witness co-signed -> COSIGNED.

    A non-existent (dangling) witness ref is dropped from consideration entirely -- it is
    neither substantive nor co-signed, so it behaves exactly like "no witness" for the purpose
    of this function; an item whose ONLY witnesses are dangling reads OPEN, same as an item
    with an empty witness list.
    """
    substantive = [w for w in witnesses if w.exists and w.substantive]
    if not substantive:
        return "OPEN"
    cosigned = [w for w in substantive if w.maintainer_cosigned]
    if len(cosigned) == len(substantive):
        return "COSIGNED"
    if cosigned:
        return "PARTIAL"
    return "WITNESSED"
