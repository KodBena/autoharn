"""test_ledger_support -- the qualification gates for Increment 2 (the transitive support-exposure
closure + flag-discharge vocabulary; WORK-UNIT-exposure-discharge.md). Every load-bearing claim is
a mechanized check:

  * §1.1 base relations support_edge/3 + support_star/2 are first-class #shown outputs.
  * §1.2 no verdict vocabulary over the dependent (only descriptive support-graph names).
  * §1.3 zero `:-` constraints: a cycle stays SATISFIABLE (fixture 7), never UNSAT.
  * §1.4 no feedback edges: the three existing programs are byte-identical (no rule body touched).
  * §1.5 monotone base, NAF only at the exposure_undischarged seam.
  * §1.6 additive proof: every banked target's pre-existing #show atoms reproduce byte-identical.
  * The eight fixtures: each hand-computed expectation (consult §0, pre-registered) matches BOTH
    producers; each ships a mutation that flips the differential to DIVERGE_DEFECT.
  * ledger_support.lp grounds standalone (#defined guards) AND composed.
  * the floor CTE cycle-guard is PROVEN by fixture 7 (both producers terminate + agree), not asserted.

These skip (not fail) when the ledger host is unreachable -- a substrate verdict is not a code
verdict (ADR-0015 Rule 3). All writes are on the apparatus-owned scratch lineage
`epistemic.marriage_support_scratch` (never an evidence ledger, never marriage_dto_scratch)."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

import ledger_diff_scratch as F
import ledger_support_scratch as S
from clingo_run import run_clingo
from ledger_differential import AGREE, DIVERGE_DEFECT, run_asp
from ledger_edb import PGHOST, export
from ledger_floor import SUPPORT_PREDS, floor_atoms, support_manifest

HERE = Path(__file__).resolve().parent
LP = HERE.parent / "lp"   # the ASP programs live in engine/lp/ (split-layout migration)
BANKED = ["s10", "s11", "s12", "s13", "nla"]
EXISTING_LP = ["ledger_tnow.lp", "ledger_dto.lp", "ledger_assumes.lp"]


def _db_up() -> bool:
    try:
        r = subprocess.run(["psql", "-h", PGHOST, "-d", "epistemic", "-tAc", "SELECT 1;"],
                           capture_output=True, text=True, timeout=10)
        return r.returncode == 0 and r.stdout.strip() == "1"
    except Exception:  # noqa: BLE001
        return False


needs_db = pytest.mark.skipif(not _db_up(), reason="ledger host unreachable (substrate, not code)")


# =============================================================== §1 non-foreclosure ==
def test_1_1_base_relations_are_first_class_shown() -> None:
    """§1.1: support_edge/3 and support_star/2 are #shown (mechanism, not scaffolding hidden
    inside derived judgments) -- verified against the program text."""
    text = (LP / "ledger_support.lp").read_text(encoding="utf-8")
    assert "#show support_edge/3." in text
    assert "#show support_star/2." in text


def test_1_2_no_verdict_vocabulary_over_the_dependent() -> None:
    """§1.2: nothing names a predicate invalid/1, unsound/1 or similar over the dependent --
    exposure describes the support graph, not the dependent's truth."""
    text = (LP / "ledger_support.lp").read_text(encoding="utf-8")
    heads = {ln.split(":-")[0].split("(")[0].strip()
             for ln in text.splitlines() if ":-" in ln and not ln.strip().startswith("%")}
    forbidden = {"invalid", "unsound", "unsound_dependent", "false", "wrong"}
    assert heads.isdisjoint(forbidden), heads & forbidden


def test_1_3_no_integrity_constraints_cycle_stays_satisfiable() -> None:
    """§1.3: zero `:-` (headless) integrity constraints; a cyclic record stays SATISFIABLE
    (fixture 7 -- two rows citing each other), never made UNSAT."""
    text = (LP / "ledger_support.lp").read_text(encoding="utf-8")
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("%") or not s:
            continue
        assert not s.startswith(":-"), f"integrity constraint found: {s}"
    edb = ("enacts(500,510).\nenacts(510,500).\n"
           "entry(500,1,verification,enactment,none,high).\n"
           "entry(510,2,verification,enactment,none,high).\n")
    atoms = {a for a in run_clingo([LP / "ledger_tnow.lp", LP / "ledger_support.lp"], edb)}
    assert "support_cycle(500)" in atoms and "support_cycle(510)" in atoms  # flagged, not fatal


def test_1_4_no_feedback_existing_programs_unchanged() -> None:
    """§1.4: no feedback edges -- the new judgments appear in NO existing rule body. Two invariants over
    the three existing programs, checked against HEAD: (a) the RULE/FACT content is byte-identical (no
    rule body touched), and (b) `#show` exports are ADDITIVE-ONLY -- every export HEAD had is still
    present (a `#show` removal/retarget is caught), while a NEW export is allowed.

    This checks the two invariants directly rather than raw git-cleanliness (Increment 3 item 3
    hardening, then out-of-frame-audit hardening). A raw `git status --porcelain` check conflates
    file-immutability with §1.4 and false-reds on a LEGITIMATE additive `#show` -- e.g. this increment's
    `#show decomp_attested_authentic/1.` in ledger_dto.lp. But the naive fix (exclude whole `#show`
    LINES) over-loosens two ways the audit caught: it stops guarding a `#show` REMOVAL entirely (only
    test_1_6 would, and that @needs_db test SKIPS when the host is down), and a single physical line may
    legally carry `#show p/1. sneaky(X):-evil(X).` -- excluding the whole line smuggles the rule past.
    So we strip only the `#show NAME/ARITY.` TOKENS (comparing them as a set for additivity) and compare
    the RESIDUAL text: a rule sharing a line with a `#show` still lands in the rule comparison and bites.
    test_1_6 (byte-identical banked derivations) can't substitute: DTO rules never FIRE on s10-s13/nla."""
    show_tok = re.compile(r"#show\s+[A-Za-z_][A-Za-z0-9_]*\s*/\s*\d+\s*\.")

    def rules_and_shows(text: str) -> tuple[list[str], set[str]]:
        shows: set[str] = set()
        rule_lines: list[str] = []
        for ln in text.splitlines():
            s = ln.split("%", 1)[0]                       # drop trailing/whole-line % comments
            shows.update(m.group(0) for m in show_tok.finditer(s))
            residual = show_tok.sub("", s).strip()        # remove ONLY the #show tokens, keep the rest
            if residual:
                rule_lines.append(residual)
        return rule_lines, shows

    for f in EXISTING_LP:
        head = subprocess.run(["git", "show", f"HEAD:experiments/fact-mining/{f}"],
                              cwd="/home/bork/w/vdc/1/claude_harness", capture_output=True, text=True)
        assert head.returncode == 0, f"cannot read HEAD:{f}: {head.stderr!r}"
        cur_rules, cur_shows = rules_and_shows((LP / f).read_text(encoding="utf-8"))
        head_rules, head_shows = rules_and_shows(head.stdout)
        assert cur_rules == head_rules, f"a RULE/fact changed in {f} (not additive #show/comment) -- feedback edge?"
        missing = head_shows - cur_shows
        assert not missing, f"a #show export was REMOVED/RETARGETED in {f}: {sorted(missing)} (only additive #show allowed)"
    # and no existing program's text mentions a support/exposure head (belt-and-braces)
    for f in EXISTING_LP:
        t = (LP / f).read_text(encoding="utf-8")
        for p in SUPPORT_PREDS:
            assert f"{p}(" not in t, f"{f} references {p}"


def test_1_5_naf_only_at_the_discharge_seam() -> None:
    """§1.5: the base (support_edge/support_star) uses no NAF; the ONLY `not` is at the discharge
    seam (affirmed / exposure_undischarged)."""
    text = (LP / "ledger_support.lp").read_text(encoding="utf-8")
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("%") or " not " not in f" {s} ":
            continue
        head = s.split(":-")[0].split("(")[0].strip()
        assert head in {"affirmed", "exposure_undischarged"}, f"NAF outside the seam: {s}"


@needs_db
def test_1_6_banked_derivations_byte_identical() -> None:
    """§1.6: additive proof -- every banked target's pre-existing #show atoms (ASP and SQL)
    reproduce byte-identical to the committed derivation artifacts after this change."""
    for t in BANKED:
        edb = export(t).edb_text()
        asp = sorted(run_asp(t, edb).atoms)
        sql = sorted(floor_atoms(t))
        # autoharn: banked derivations are EVIDENCE-STAYS [A11] — read from the claude_harness archive.
        d = Path("/home/bork/w/vdc/1/claude_harness/experiments/fact-mining/docs/ledger-marriage/derivations") / t
        ba = [l for l in (d / "asp_atoms.txt").read_text().splitlines() if l.strip()]
        bs = [l for l in (d / "sql_atoms.txt").read_text().splitlines() if l.strip()]
        assert asp == ba, f"{t}: banked ASP #show atoms changed"
        assert sql == bs, f"{t}: banked SQL #show atoms changed"


# =========================================================== standalone / composed ==
def test_grounds_standalone_and_composed() -> None:
    """ledger_support.lp grounds standalone (#defined guards make an empty extension silence, not
    a grounding warning) AND composed on top of ledger_tnow.lp."""
    assert run_clingo([LP / "ledger_support.lp"], "") == []  # empty EDB, SATISFIABLE, no atoms
    edb = ("entry(1,1,decision,design,held,high).\nentry(2,2,decision,design,held,high).\n"
           "supersedes(2,1).\nenacts(3,1).\nentry(3,3,verification,enactment,none,high).\n")
    atoms = set(run_clingo([LP / "ledger_tnow.lp", LP / "ledger_support.lp"], edb))
    assert "exposure(3,1)" in atoms  # 3 in-force, rests on superseded 1


# ================================================= the eight fixtures + AGREE + flips ==
@needs_db
def test_fixtures_agree_with_hand_computed_oracle() -> None:
    """The pre-registered oracle (consult §0) matches BOTH producers bit-identically on the base
    record (fixtures 1,2,3,4,6,7,8) -- correlated-authorship mitigation: the hand-computed model,
    not either producer, is the check."""
    S.setup()
    res = S.support_differential()
    assert res.verdict == AGREE, (sorted(res.only_asp), sorted(res.only_sql))
    got = res.asp
    # fixture 1 (depth-3): exposure at every depth via answers->enacts->enacts
    for a in ("exposure(110,100)", "exposure(120,100)", "exposure(130,100)"):
        assert a in got
    # fixture 2 (dead intermediate): F's exposure to the root survives; E's own is absent
    assert "exposure(220,200)" in got and "exposure(220,210)" in got
    assert "exposure(210,200)" not in got
    # fixture 3 (discharge): retained exposure, discharged, no SoD violation
    assert "exposure(310,300)" in got and "affirmed(310,300)" in got
    assert "exposure_undischarged(310,300)" not in got
    assert "affirm_sod_violation(350)" not in got
    # fixture 4 (currency re-raise): the affirmation keyed to 300 does not cover X=320
    assert "exposure_undischarged(310,320)" in got
    # fixture 6 (self-affirmation): NEVER A PASS -- affirmed is gated OUT (mirror of decomp_attested),
    # the exposure stays UNDISCHARGED, and the SoD red flag fires (belt-and-braces). This pins the
    # single most contested behavioral choice of the increment (surfaced as an open ruling), so a
    # future flip to flag-only is a RED gate, not a silent change.
    assert "affirm_sod_violation(450)" in got
    assert "affirmed(410,400)" not in got                  # self-affirmation does not confer discharge
    assert "exposure_undischarged(410,400)" in got         # ... so the exposure is never a pass
    # fixture 7 (cycle): flagged, both producers terminated + agree, SATISFIABLE
    assert "support_cycle(500)" in got and "support_cycle(510)" in got
    assert {"support_star(500,500)", "support_star(510,510)"} <= got
    # fixture 8 (expired-assumption): transitive exposure_expired via enacts->assumes
    assert "exposure_expired(810,800)" in got and "exposure_expired(820,800)" in got


@needs_db
def test_fixture_5_superseded_affirmation_relapses() -> None:
    """Fixture 5: superseding the affirmation row 350 retracts affirmed(310,300) and returns
    exposure_undischarged(310,300) -- on BOTH producers (AGREE)."""
    S.setup()
    assert "affirmed(310,300)" in S.support_differential().asp
    S.add_superseded_affirmation()
    res = S.support_differential()
    assert res.verdict == AGREE
    assert "affirmed(310,300)" not in res.asp
    assert "exposure_undischarged(310,300)" in res.asp


@needs_db
def test_each_fixture_mutation_flips_red(tmp_path: Path) -> None:
    """Every fixture ships a mutation that flips the differential to DIVERGE_DEFECT on the named
    atom -- a gate seen red (ADR-0011: a clause never flipped is a claim, not a net)."""
    S.setup()
    checks = {
        "fix1_drop_recursion": ("exposure(120,100)", "only_sql"),
        "fix2_drop_recursion": ("exposure(220,200)", "only_sql"),
        "fix3_break_affirmed": ("exposure_undischarged(310,300)", "only_asp"),
        "fix4_key_on_F_only": ("exposure_undischarged(310,320)", "only_sql"),
        "fix6_drop_sod": ("affirm_sod_violation(450)", "only_sql"),
        "fix7_drop_cycle": ("support_cycle(500)", "only_sql"),
        "fix8_drop_recursion": ("exposure_expired(820,800)", "only_sql"),
    }
    for name, (atom, side) in checks.items():
        res = S.support_differential(programs=S.mutated_program(name, tmp_path))
        assert res.verdict == DIVERGE_DEFECT, name
        assert atom in getattr(res, side), (name, sorted(res.only_asp), sorted(res.only_sql))
    # fixture 5's mutation (drop the currency guard) needs the superseded-affirmation state
    S.setup()
    S.add_superseded_affirmation()
    res = S.support_differential(programs=S.mutated_program("fix5_drop_currency", tmp_path))
    assert res.verdict == DIVERGE_DEFECT
    assert "exposure_undischarged(310,300)" in res.only_sql


# ============================================================== §5 capability manifest ==
@needs_db
def test_capability_manifest_defers_never_silent_empty() -> None:
    """§5/F49: a target WITH assumes/affirm sources PRODUCES exposure_expired/affirmed; a target
    WITHOUT them marks them DEFERRED (never a silent empty a consumer misreads as 'none exist')."""
    S.setup()
    prod = support_manifest(S.SCHEMA)
    assert prod["exposure_expired"].startswith("PRODUCED")
    assert prod["affirmed"].startswith("PRODUCED")
    F.setup()  # marriage_diff_scratch has no support_assumes / support_affirm side tables
    deferred = support_manifest(F.SCHEMA)
    assert deferred["exposure_expired"].startswith("DEFERRED")
    assert deferred["affirmed"].startswith("DEFERRED")
    assert deferred["exposure"].startswith("PRODUCED")  # exposure needs no scratch side table
