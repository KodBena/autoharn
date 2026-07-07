# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-06T18:26:29Z
#   last-change: 2026-07-06T18:26:29Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""test_acts_join -- the acts.act<->s15 matching DERIVER (acts_join.py) against the Increment-5
pre-registered oracle (epistemic-operator/harness/e15-build/rehearsal/INCREMENT-5-PRE-REGISTERED-
expectations.md Parts 1/3). The PURE derive() is checked DB-free against the hand-computed edges;
the end-to-end consumer atoms are the rehearsal's job (rehearse.py, the executable oracle). ADR-0013
Rule 5: a regression in the matching is a red test."""
from __future__ import annotations

from acts_join import ActRow, LedgerRow, act_tag, derive

FENCED = "/synthetic/nk4-mock"

# The mock act stream (INCREMENT-5 pre-registration Part 1) as the adapter emits it (id-is-order).
ACTS = [
    ActRow(1, "message_in", "", ""), ActRow(2, "message_out", "", ""),
    ActRow(3, "plan_item_created", "step1 parse header block", ""),
    ActRow(4, "plan_item_created", "step2 validate section structure", ""),
    ActRow(5, "plan_item_created", "step3 checksum over section body only", ""),
    ActRow(6, "plan_item_created", "step4 emit report and exit-code contract", ""),
    ActRow(7, "tool_result", "", ""),
    ActRow(8, "delegation_spawn", "sub:principal-engineer", ""),
    ActRow(9, "delegation_return", "sub:principal-engineer", ""),
    ActRow(10, "tool_call", "Write", f"{FENCED}/report_lint.py"),
    ActRow(11, "tool_result", "Write", f"{FENCED}/report_lint.py"),
    ActRow(12, "tool_call", "Write", f"{FENCED}/header.py"),
    ActRow(13, "tool_result", "Write", f"{FENCED}/header.py"),
    ActRow(14, "tool_call", "Write", f"{FENCED}/sections.py"),
    ActRow(15, "tool_result", "Write", f"{FENCED}/sections.py"),
    ActRow(16, "message_in", "", ""),
    ActRow(17, "tool_call", "Edit", f"{FENCED}/checksum.py"),
    ActRow(18, "tool_result", "Edit", f"{FENCED}/checksum.py"),
    ActRow(19, "delegation_spawn", "sub:validator", ""),
    ActRow(20, "delegation_return", "sub:validator", ""),
    ActRow(21, "message_out", "", ""),
    ActRow(22, "tool_call", "Read", f"{FENCED}/report_lint.py"),
    ActRow(23, "tool_result", "Read", f"{FENCED}/report_lint.py"),
]

# The dishonest mock ledger (Part 2).
LEDGER = [
    LedgerRow(1, "decision", "step1 parse header block", "", "step1"),
    LedgerRow(2, "decision", "COMPOSITE: step2 …; step3 checksum over the section body only; step4 …",
              "", "step2"),
    LedgerRow(3, "review", "countersign decomposition", "", "principal-engineer"),
    LedgerRow(4, "verification", "implemented report-lint entry", f"{FENCED}/report_lint.py", "validator"),
    LedgerRow(5, "verification", "implemented section validation", f"{FENCED}/sections.py", ""),
    LedgerRow(6, "decision", "step3 checksum now over body WITH header line", "", ""),
    LedgerRow(7, "verification", "implemented checksum change", f"{FENCED}/checksum.py", ""),
    LedgerRow(8, "verification", "validated build", f"{FENCED}/validator.py", ""),
]


def test_relevant_matches_oracle_section_4():
    d = derive(ACTS, LEDGER, FENCED)
    got = {a for a, r in d.relevant.items() if r}
    assert got == {3, 4, 5, 6, 8, 9, 10, 12, 14, 17, 19, 20}
    # act 22 is a READ -> NOT relevant; messages/tool_results NOT relevant
    assert not d.relevant[22] and not d.relevant[1] and not d.relevant[11]


def test_ledger_claim_from_evidence():
    d = derive(ACTS, LEDGER, FENCED)
    assert d.ledger_claim == sorted([
        (4, f"{FENCED}/report_lint.py"), (5, f"{FENCED}/sections.py"),
        (7, f"{FENCED}/checksum.py"), (8, f"{FENCED}/validator.py")])


def test_ledger_ref_evidence_and_tag_edges():
    d = derive(ACTS, LEDGER, FENCED)
    assert set(d.ledger_ref) == {
        (4, 10), (5, 14), (7, 17),            # evidence edges
        (1, 3), (2, 4), (3, 8), (3, 9), (4, 19), (4, 20)}  # tag edges


def test_unreferenced_relevant_acts_drive_the_spans():
    """The load-bearing derivation consequence: acts 5,6 (composite-blob dropped plan) and 12
    (unledgered header write) are the ONLY unreferenced relevant acts -> the two pre-registered spans."""
    d = derive(ACTS, LEDGER, FENCED)
    referenced = {a for _, a in d.ledger_ref}
    relevant = {a for a, r in d.relevant.items() if r}
    assert relevant - referenced == {5, 6, 12}


def test_act_tag_scheme():
    assert act_tag(ActRow(3, "plan_item_created", "step1 parse header", "")) == "step1"
    assert act_tag(ActRow(8, "delegation_spawn", "sub:principal-engineer", "")) == "principal-engineer"
    assert act_tag(ActRow(10, "tool_call", "Write", "/x/y.py")) is None  # a write has no tag (evidence edge)
