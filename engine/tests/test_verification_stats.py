"""test_verification_stats -- work item `verification-stats-asp-harvester`: proves the parser
(engine/verification_evidence.py), the EDB grounding (engine/verification_stats_edb.py's
facts_from_rows()), and the ASP program (engine/lp/verification_stats.lp) against a SYNTHESIZED
fixture spanning BOTH polarities -- correctly-parseable `kind=verification` rows deriving the
right distributions, and a malformed row surfacing as its own `unparseable_verification/1` fact.

WHY SYNTHESIZED, NAMED HONESTLY (per this work item's own instruction): this repo's own ledger
carries no `kind=verification` rows yet, and reading `ent`'s live db is explicitly not this
module's to do. So this fixture never touches a database at all -- it drives
`facts_from_rows()` (the pure grounding function `export()` itself calls after its own SQL fetch)
directly with hand-built `(id, evidence)` pairs, then feeds the resulting facts through the REAL
`clingo` binary via the REAL engine/clingo_run.py path (no DB, but a genuine ASP solve -- this is
not a mock of the logic layer, only of the SQL fetch). `export()`'s own live-schema query
(`SELECT id, coalesce(evidence,'') FROM ... WHERE kind='verification'`) and the capability gate
(`evidence` column presence) are consequently UNEXERCISED here -- named plainly, not silently
assumed proven by these tests. Live-ent validation of the whole pipeline end-to-end is likewise
UNEXERCISED (reading ~/ent's db is not this builder's to do, per the commission)."""
from __future__ import annotations

from clingo_run import run_clingo
from verification_evidence import ParsedVerification, parse_evidence
from verification_stats_edb import VERIFICATION_STATS_LP, facts_from_rows


# ---- parser unit tests (engine/verification_evidence.py), both polarities -------------------

def test_parse_evidence_well_formed():
    p = parse_evidence("verdict=approve;role=reviewer;workflow=sweep;round=2;task=t-17")
    assert p == ParsedVerification(verdict="approve", role="reviewer", workflow="sweep",
                                   round=2, task="t-17")


def test_parse_evidence_tolerates_stray_semicolon_and_unknown_extra_key():
    p = parse_evidence("verdict=revise;role=r;workflow=w;round=0;task=t;extra=ignored;")
    assert p is not None and p.verdict == "revise" and p.round == 0


def test_parse_evidence_rejects_missing_key():
    assert parse_evidence("verdict=approve;role=r;workflow=w;round=1") is None  # no task=


def test_parse_evidence_rejects_unknown_verdict():
    assert parse_evidence("verdict=approved;role=r;workflow=w;round=1;task=t") is None


def test_parse_evidence_rejects_non_integer_round():
    assert parse_evidence("verdict=approve;role=r;workflow=w;round=two;task=t") is None


def test_parse_evidence_rejects_negative_round():
    assert parse_evidence("verdict=approve;role=r;workflow=w;round=-1;task=t") is None


def test_parse_evidence_rejects_repeated_key():
    assert parse_evidence("verdict=approve;role=r;workflow=w;round=1;task=t;role=r2") is None


def test_parse_evidence_rejects_equals_less_segment():
    assert parse_evidence("verdict=approve;role=r;workflow;round=1;task=t") is None


def test_parse_evidence_rejects_empty_and_none():
    assert parse_evidence("") is None
    assert parse_evidence(None) is None


# ---- facts_from_rows() -- the pure grounding function, both polarities ----------------------

def test_facts_from_rows_both_polarities():
    rows = [
        (1, "verdict=approve;role=reviewer;workflow=sweep;round=1;task=t-1"),
        (2, "verdict=revise;role=reviewer;workflow=sweep;round=1;task=t-2"),
        (3, "verdict=approve;role=implementer;workflow=sweep;round=2;task=t-3"),
        (4, "this is not the convention at all"),  # the malformed polarity
    ]
    facts, counts = facts_from_rows(rows)
    assert counts == {"verification_row": 4, "parsed": 3, "unparseable": 1}
    assert "unparseable_verification(4)." in facts
    assert "verification_verdict(1,approve)." in facts
    assert "verification_verdict(2,revise)." in facts
    assert 'verification_role(1,"reviewer").' in facts
    assert "verification_round(3,2)." in facts
    # row 4 NEVER emits any of the five typed facts (never both, never neither)
    assert not any(f.startswith(("verification_row(4)", "verification_verdict(4,",
                                 "verification_role(4,", "verification_workflow(4,",
                                 "verification_round(4,", "verification_task(4,")) for f in facts)


def test_facts_from_rows_empty_is_satisfiable():
    facts, counts = facts_from_rows([])
    assert facts == []
    assert counts == {"verification_row": 0, "parsed": 0, "unparseable": 0}


# ---- full pipeline through the REAL clingo binary (engine/clingo_run.py), both polarities -----

def _edb_text(rows: list[tuple[int, str]]) -> str:
    facts, _ = facts_from_rows(rows)
    return "\n".join(facts) + "\n"


def test_asp_derives_distributions_and_surfaces_unparseable():
    rows = [
        (1, "verdict=approve;role=reviewer;workflow=sweep;round=1;task=t-1"),
        (2, "verdict=revise;role=reviewer;workflow=sweep;round=1;task=t-2"),
        (3, "verdict=approve;role=implementer;workflow=sweep;round=2;task=t-3"),
        (4, "verdict=approve;role=reviewer;workflow=audit;round=1;task=t-4"),
        (5, "garbage evidence with no k=v shape at all except one=here"),  # unparseable
    ]
    atoms = set(run_clingo([VERIFICATION_STATS_LP], _edb_text(rows)))

    # per-workflow distribution (role/workflow/task cross the wire as QUOTED clingo strings --
    # engine/clingo_run.quote_term's own convention, unlike ledger_edb._atom's bare-vs-quoted
    # choice; verdict stays a bare atom, the closed lowercase vocabulary this module trusts).
    # sweep: approve(row1) + revise(row2) + approve(row3)
    assert 'count_workflow_verdict("sweep",approve,2)' in atoms
    assert 'count_workflow_verdict("sweep",revise,1)' in atoms
    assert 'count_workflow_verdict("audit",approve,1)' in atoms

    # per-role distribution
    assert 'count_role_verdict("reviewer",approve,2)' in atoms
    assert 'count_role_verdict("reviewer",revise,1)' in atoms
    assert 'count_role_verdict("implementer",approve,1)' in atoms

    # per-round distribution
    assert 'count_round_verdict(1,approve,2)' in atoms
    assert 'count_round_verdict(1,revise,1)' in atoms
    assert 'count_round_verdict(2,approve,1)' in atoms

    # overall per-verdict totals
    assert 'count_verdict(approve,3)' in atoms
    assert 'count_verdict(revise,1)' in atoms

    # the honest-limit counterpart: the malformed row surfaces, visibly, never dropped
    assert 'unparseable_verification(5)' in atoms
    assert 'count_unparseable(1)' in atoms


def test_asp_all_parseable_yields_zero_unparseable():
    rows = [(1, "verdict=reject;role=r;workflow=w;round=3;task=t")]
    atoms = set(run_clingo([VERIFICATION_STATS_LP], _edb_text(rows)))
    assert 'count_verdict(reject,1)' in atoms
    assert 'count_unparseable(0)' in atoms
    assert not any(a.startswith("unparseable_verification(") for a in atoms)


def test_asp_empty_ledger_is_satisfiable_and_vacuous():
    atoms = set(run_clingo([VERIFICATION_STATS_LP], _edb_text([])))
    assert 'count_unparseable(0)' in atoms
    assert not any(a.startswith("count_verdict(") for a in atoms)
