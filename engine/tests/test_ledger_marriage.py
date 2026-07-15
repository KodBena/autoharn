# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-06T05:40:08Z
#   last-change: 2026-07-06T15:47:33Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""test_ledger_marriage -- the qualification gates for the ledger-logic marriage
increment 1 (link 24). Every load-bearing claim is a mechanized check here:

  * AC1 -- ledger_edb target resolution is PARITY-PINNED against the operator SSOT
    instruments/ledger_target.py (cross-repo, by subprocess, never imported).
  * AC2 -- id-is-order: a same-second-neighbour fixture proves the sort key is id.
  * AC3 -- the ASP T_now program is BIT-IDENTICAL to the SQL floor on every banked
    target (s10-s13 + nla): empty symmetric difference.
  * AC4 -- the five banked-fixture families each FLIP a verdict under mutation
    (a gate seen red, ADR-0011: a clause never flipped is a claim, not a net).
  * AC5 -- a verdict without both derivation records is NO RESULT (QUARANTINED).
  * AC6 -- a single-producer mutation is caught as DIVERGE_DEFECT; a crashed engine
    QUARANTINES loudly, never silence.

These skip (not fail) when the ledger host is unreachable -- a substrate verdict is
not a code verdict (ADR-0015 Rule 3). The differential itself runs read-only."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import dto_authentic_verify as V
import ledger_differential as D
import ledger_diff_scratch as F
import ledger_dto_scratch as S
from clingo_run import run_clingo
from ledger_edb import CapabilityError, PGHOST, export, resolve

HERE = Path(__file__).resolve().parent
# autoharn: repo-local instruments/ (was the cross-repo epistemic-operator/instruments reach)
OPERATOR_INSTRUMENTS = HERE.parent.parent / "instruments"
BANKED = ["s10", "s11", "s12", "s13", "nla"]


def _db_up() -> bool:
    try:
        r = subprocess.run(["psql", "-h", PGHOST, "-d", "epistemic", "-tAc", "SELECT 1;"],
                           capture_output=True, text=True, timeout=10)
        return r.returncode == 0 and r.stdout.strip() == "1"
    except Exception:  # noqa: BLE001
        return False


needs_db = pytest.mark.skipif(not _db_up(), reason="ledger host unreachable (substrate, not code)")

# The exercise's own throwaway lineage -- NEVER marriage_dto_scratch (which holds the maintainer's
# GENUINE authentic tap, banked in dto-authentic-attestation.witness.txt but preserved LIVE).
DTO_EXERCISE_SCHEMA = "marriage_dto_exercise_scratch"


@pytest.fixture(autouse=True)
def _isolate_dto_exercise(monkeypatch: "pytest.MonkeyPatch", tmp_path: Path) -> None:
    """Structurally forbid a test run from DROP+REBUILDing marriage_dto_scratch. `S.run_scenario`
    calls `setup_scratch()` (DROP SCHEMA ... CASCADE + rebuild), which on the LIVE schema would erase
    the maintainer's authentic:maintainer attestation on every test invocation. Redirecting the
    exercise SCHEMA to an isolated throwaway makes the illegal state "a test wipes the human act"
    UNREPRESENTABLE (ADR-0000: the type-driven fix over a per-test discipline nobody can be trusted
    to remember). The live tap's home is a derive-only surface (dto_authentic_verify.py), never a
    rebuild target -- see WORK-UNIT-exposure-discharge.md §5 (writes scratch-only, isolated).

    The witness path is ALSO redirected: `run_scenario` -> `write_witness` writes to a FIXED file
    (dto-scratch.witness.txt), so an exercise-schema test run would overwrite that COMMITTED artifact
    with throwaway content. Pointing it at tmp keeps the real witness a fact about the real run only."""
    monkeypatch.setattr(S, "SCHEMA", DTO_EXERCISE_SCHEMA)
    monkeypatch.setattr(S, "WITNESS", tmp_path / "dto-exercise-scratch.witness.txt")


# ---------------------------------------------------------------- AC1 parity --
@needs_db
def test_target_parity_against_operator_ssot() -> None:
    """ledger_edb.resolve must agree with instruments/ledger_target.py on (db, schema)
    for every banked target -- cross-repo, by SUBPROCESS (no import), so a kernel/operator
    change lands as a red parity test (design §10)."""
    names = BANKED
    probe = (
        "import sys; sys.path.insert(0, r'%s'); from ledger_target import resolve\n"
        "for n in %r:\n"
        "    t = resolve(n); print(f'{n}\\t{t.db}\\t{t.schema}')\n" % (OPERATOR_INSTRUMENTS, names)
    )
    out = subprocess.run(["python3", "-c", probe], capture_output=True, text=True, check=True)
    ssot = {}
    for line in out.stdout.strip().splitlines():
        n, db, schema = line.split("\t")
        ssot[n] = (db, schema)
    for n in names:
        mine = resolve(n)
        assert (mine.db, mine.schema) == ssot[n], (
            f"target '{n}' resolution diverged from operator SSOT: "
            f"ledger_edb={mine.db}.{mine.schema} vs ledger_target={ssot[n]}")


# ------------------------------------------------------------- AC3 bit-identity --
@needs_db
@pytest.mark.parametrize("name", BANKED)
def test_differential_bit_identical(name: str) -> None:
    res = D.run_differential(name)
    assert res.verdict() == D.AGREE, (
        f"{name}: not bit-identical. Δasp={sorted(res.only_asp)} Δsql={sorted(res.only_sql)}")
    assert res.asp.atoms == res.sql.atoms


# ------------------------------------------------------------ AC5/AC6 quarantine --
@needs_db
def test_dropped_derivation_record_is_no_result() -> None:
    """A verdict without both derivation records is NO RESULT (QUARANTINED), not AGREE."""
    res = D.run_differential("s10")
    assert res.verdict() == D.AGREE
    res.asp.record = None  # lose the witness
    assert res.verdict() == D.QUARANTINED


@needs_db
def test_crashed_engine_quarantines_loudly(tmp_path: Path) -> None:
    """A clingo grounding crash (a malformed program) produces a loud QUARANTINED, never a
    silent pass. Also covers a missing program file (both are substrate/tool failures)."""
    edb = export("s10").edb_text()
    malformed = tmp_path / "malformed.lp"
    malformed.write_text("this is not valid clingo :- ) syntax (\n", encoding="utf-8")
    run = D.run_asp("s10", edb, program=malformed)
    assert run.quarantine is not None and run.atoms == set()
    res = D.run_differential("s10", asp_program=malformed)
    assert res.verdict() == D.QUARANTINED
    # a missing program file is also a quarantine, never an uncaught traceback
    assert D.run_asp("s10", edb, program=HERE / "does_not_exist.lp").quarantine is not None


@needs_db
def test_single_producer_mutation_is_diverge_defect() -> None:
    """Mutate ONLY the ASP producer's EDB (drop the s10 defeater edge); the SQL floor is
    unmutated, so the differential catches the drift as DIVERGE_DEFECT and turns red."""
    edb = export("s10").edb_text()
    mutated = "\n".join(l for l in edb.splitlines() if l.strip() != "supersedes(22,4).")
    res = D.run_differential("s10", edb_text=None, asp_atoms_override=_asp_atoms("s10", mutated))
    assert res.verdict() == D.DIVERGE_DEFECT
    assert res.verdict() in D.RED


def _asp_atoms(name: str, edb_text: str) -> set[str]:
    return D.run_asp(name, edb_text).atoms


# --------------------------------------------------- AC4 mutation flips verdict --
# The five banked-fixture families (design §5). Each mutation is applied IN-MEMORY to the
# EDB (the read-only record is never touched); the ASP verdict-atom set before and after
# must DIFFER on the named atom -- proving the clause is load-bearing (ADR-0011).
def _mutate(edb: str, *, drop: tuple[str, ...] = (), add: tuple[str, ...] = ()) -> str:
    lines = [l for l in edb.splitlines() if l.strip() not in drop]
    lines.extend(add)
    return "\n".join(lines) + "\n"


@needs_db
def test_fixture_unsound_derivation_flips() -> None:
    """Fixture (rows 25/27, e9->s10): removing the supersedes(22,4) defeater edge
    RETRACTS unsound_derivation and launder -- the defeater clause is load-bearing."""
    edb = export("s10").edb_text()
    base = _asp_atoms("s10", edb)
    mut = _asp_atoms("s10", _mutate(edb, drop=("supersedes(22,4).",)))
    assert "unsound_derivation(25,4)" in base and "unsound_derivation(25,4)" not in mut
    assert "launder(25,4,22)" in base and "launder(25,4,22)" not in mut


@needs_db
def test_fixture_alias_surface_flips() -> None:
    """Fixture (gate-integrity, F45 class): retyping the enacts target (row 4) from
    question to decision RETRACTS alias_surface -- the reference-hygiene clause flips."""
    edb = export("s10").edb_text()
    base = _asp_atoms("s10", edb)
    retyped = _mutate(edb,
                      drop=("entry(4,1783264950,question,design,open,medium).",),
                      add=("entry(4,1783264950,decision,design,open,medium).",))
    mut = _asp_atoms("s10", retyped)
    assert "alias_surface(10,4)" in base and "alias_surface(10,4)" not in mut


@needs_db
def test_fixture_in_force_flips() -> None:
    """Fixture (supersession/in-force): removing supersedes(22,4) puts row 4 back in force
    -- the in_force/head closure is load-bearing."""
    edb = export("s10").edb_text()
    base = _asp_atoms("s10", edb)
    mut = _asp_atoms("s10", _mutate(edb, drop=("supersedes(22,4).",)))
    assert "in_force(4)" not in base and "in_force(4)" in mut
    assert "head(4,22)" in base and "head(4,22)" not in mut


@needs_db
def test_fixture_question_status_flips() -> None:
    """Fixture (observed-currency/question-status, F42 class): adding an answers edge to
    the open question (row 4) flips question_open -> question_answered."""
    edb = export("s10").edb_text()
    base = _asp_atoms("s10", edb)
    mut = _asp_atoms("s10", _mutate(edb, add=("answers(30,4).",)))
    assert "question_open(4)" in base and "question_open(4)" not in mut
    assert "question_answered(4)" not in base and "question_answered(4)" in mut


@needs_db
def test_fixture_clause_defeat_flips() -> None:
    """Fixture (aspectual F44 triple): on nla (0 amends), injecting an amends edge between
    two in-force rows makes clause_defeat fire; superseding the target makes it MOOT."""
    edb = export("nla").edb_text()
    base = _asp_atoms("nla", edb)
    assert not any(a.startswith("clause_defeat(") for a in base)  # zero amends anywhere (ground truth)
    live = _asp_atoms("nla", _mutate(edb, add=("amends(50,40).",)))
    assert "clause_defeat(50,40)" in live
    moot = _asp_atoms("nla", _mutate(edb, add=("amends(50,40).", "supersedes(54,40).")))
    assert "clause_defeat_moot(50,40)" in moot and "clause_defeat(50,40)" not in moot


# ---------------------------------------- Increment 1.1 fix-pass fixtures (F-A..F-D) --
# Each new fixture makes a branch FIRE that no BANKED target exercises -- the branches where
# the differential was structurally blind (both producers shared one author, so bit-identity
# proved agreement, not fidelity). Each fixture's mutation FLIPS the verdict (a gate seen red).
@needs_db
def test_fixture_superseded_answer_reopens_question() -> None:
    """F-A: a question whose answering row is later SUPERSEDED must REOPEN (the s13.question_status
    judgment). On the diff scratch, question 21 is answered by 23, then 23 is superseded by 24 ->
    the question is OPEN, not answered. Un-superseding the answer flips it back to answered; and a
    single-producer regression that keeps the retracted answer 'in force' is caught DIVERGE_DEFECT
    -- the branch bit-identity could not see, because no banked target carries a superseded answer."""
    F.setup()
    edb = export(F.SCHEMA).edb_text()
    base = _asp_atoms(F.SCHEMA, edb)
    assert "question_open(21)" in base and "question_answered(21)" not in base
    flipped = _asp_atoms(F.SCHEMA, _mutate(edb, drop=("supersedes(24,23).",)))
    assert "question_answered(21)" in flipped and "question_open(21)" not in flipped
    assert D.run_differential(F.SCHEMA).verdict() == D.AGREE          # both producers agree on the fixture
    res = D.run_differential(F.SCHEMA, edb_text=None,                 # gate seen red: ASP keeps the
                             asp_atoms_override=flipped)              # retracted answer in force, SQL retracts
    assert res.verdict() == D.DIVERGE_DEFECT and res.verdict() in D.RED


@needs_db
def test_fixture_self_superseding_citation_is_sound() -> None:
    """F-D (boundary): diff-scratch row 26 both SUPERSEDES and ENACTS row 22 (a self-superseding
    citation). Under STRICT id-precedence (the ratified id-is-order law) it is SOUND -- no
    unsound_derivation(26,22), because the citer names the antecedent it replaces; under ts-`<=`
    it would be unsound. Adding an EARLIER defeater of 22 makes it unsound, proving the strict
    boundary is load-bearing. This boundary case is absent from every banked record (id==ts order)."""
    F.setup()
    edb = export(F.SCHEMA).edb_text()
    base = _asp_atoms(F.SCHEMA, edb)
    assert "unsound_derivation(26,22)" not in base    # strict id-precedence: self-citation SOUND
    assert "stale_enactment_row(26,22)" in base        # it does enact a now-superseded design (truthful)
    flipped = _asp_atoms(F.SCHEMA, _mutate(edb, add=("supersedes(25,22).",)))
    assert "unsound_derivation(26,22)" in flipped       # an EARLIER defeater -> unsound (boundary is load-bearing)
    assert D.run_differential(F.SCHEMA).verdict() == D.AGREE


@needs_db
def test_premature_eviction_flags_unattested_eviction() -> None:
    """F-B (PROVISIONAL evict-on-attest, ratification pending): evicting a decomposition referent
    while its group is UNATTESTED is the forbidden half-decomposed-original-gone state (§1.5). The
    premature_eviction guard makes it LOUD instead of silent. Self-attest (SoD violation) leaves the
    group unattested, so the eviction fires premature_eviction(1,"g1"); a valid SoD-distinct
    synthetic attestation (attest-before-supersede ordering) clears it."""
    self_atoms = S.run_scenario("self")
    assert 'premature_eviction(1,"g1")' in self_atoms
    syn_atoms = S.run_scenario("synthetic")
    assert not any(a.startswith("premature_eviction(") for a in syn_atoms)


@needs_db
def test_dto_derived_eviction_retains_unattested_referent() -> None:
    """F-B FULL derived eviction (RATIFIED 2026-07-06, beyond the premature_eviction flag): a
    decomposed target's presence in the current view is DERIVED from group attestation, so a DTO
    consumer reads the referent as RETAINED (not gone) until attested -- an AUTHORITATIVE corrected
    view (the raw kernel in_force still renders the append-only eviction; the write-boundary gate that
    makes the forbidden state truly unauthorable is RATIFIED-deferred to a real subject lineage).
    UNATTESTED (self-attest) + superseded -> the bare supersede EVICTS NOTHING:
    referent_in_current(1) STILL holds (retained, the F44 aspectual state) and the referent is NOT
    evicted. Mutation (attest the group) FLIPS the verdict: decomp_evicts_referent(1) fires,
    referent_in_current(1) clears -- the referent genuinely leaves the current view only on
    attestation."""
    unattested = S.run_scenario("self")           # SoD-violation -> group UNATTESTED, referent superseded
    assert "referent_in_current(1)" in unattested          # retained: the eviction evicts nothing
    assert "decomp_evicts_referent(1)" not in unattested   # not evicted while unattested
    attested = S.run_scenario("synthetic")        # SoD-distinct attestation -> group attested
    assert "referent_in_current(1)" not in attested        # verdict FLIPS: referent leaves the current view
    assert "decomp_evicts_referent(1)" in attested         # evicted on attestation (evict-on-attest)


@needs_db
def test_superseded_assumption_not_in_force() -> None:
    """F-C: ledger_assumes.lp composes with the supersession closure. The DTO scratch's assumption
    11 is a ledger row over-ruled (superseded) by 13 with a validity bound in the FUTURE (never
    expires) -- yet it is loudly NOT in force and its scope is flagged resting_on_superseded. An
    in-bound, un-superseded assumption (98) stays in force. Before the fix an unexpired-but-
    superseded assumption still read in-force (the censored-record shape F-A closes for answers)."""
    atoms = S.run_scenario("synthetic")
    assert "assumption_not_in_force(11)" in atoms and "assumption_in_force(11)" not in atoms
    assert "resting_on_superseded(10,11)" in atoms
    assert "assumption_in_force(98)" in atoms


def test_soundness_lp_s10_model_byte_identical() -> None:
    """F-D operator retrofit (item 4): instruments/soundness.lp is retrofitted from ts-`<=` to
    id-`<` keying; its banked s10 model must reproduce BYTE-IDENTICALLY (id-order == ts-order on
    that record). Runs the operator instrument directly (clingo, no DB) and pins the exact shown
    atom set -- a boundary case would have moved it, this record has none."""
    lp = OPERATOR_INSTRUMENTS / "soundness.lp"
    out = subprocess.run(["clingo", str(lp), "--outf=2"], capture_output=True, text=True)
    d = json.loads(out.stdout)
    assert d["Result"] == "SATISFIABLE"
    atoms = set(d["Call"][-1]["Witnesses"][-1]["Value"])
    assert atoms == {
        "alias_surface(10,4)", "alias_surface(25,4)", "alias_surface(27,4)",
        "unsound_derivation(25,4)", "unsound_derivation(27,4)",
        "launder(25,4,22)", "launder(27,4,22)",
        "inexpressible(multi_enacts(13))", "inexpressible(none_enacts(14))",
    }


@needs_db
def test_soundness_operator_twin_agrees() -> None:
    """F-D operator-twin fix (Increment 1.2): the operator-twin differential (soundness.lp ASP vs
    soundness.py live-psql core) must AGREE on the shared judgments {alias_surface,
    unsound_derivation, launder} over the banked s10 record AND the self-superseding-citation
    boundary — the standing net that replaces the pre-retrofit latent divergence (soundness.py keyed
    ts-`<=`, soundness.lp keyed id-`<`; they agreed only because id-order == ts-order on the banked
    record). Runs the operator instrument directly by subprocess (cross-repo, never imported), the
    same shape as the s10-model pin below. Exit 0 == AGREE on every scenario + negative control."""
    twin = OPERATOR_INSTRUMENTS / "soundness_twin.py"
    cp = subprocess.run(["python3", str(twin)], cwd=str(OPERATOR_INSTRUMENTS),
                        capture_output=True, text=True)
    assert cp.returncode == 0, f"operator-twin differential not AGREE (exit {cp.returncode}):\n{cp.stdout}\n{cp.stderr}"
    assert "TWIN AGREE" in cp.stdout


@needs_db
def test_soundness_report_runs_on_amends_bearing_target() -> None:
    """Regression guard (Increment 1.2): soundness.report's clause-defeat block references the
    superseders map, which the F-D retrofit's `derive()` extraction moved out of report's top. Every
    BANKED target (s10-s13/nla) carries ZERO amends, so the byte-identity checks are STRUCTURALLY
    BLIND to that branch (it never runs on them) — an out-of-frame audit surfaced exactly this:
    report() crashed NameError on the amends-bearing s13probe mirror. This guard runs soundness.py on
    an amends-bearing target end-to-end (no crash, clause_defeat emitted). Skips (substrate, not code)
    if the s13probe mirror is absent."""
    probe = subprocess.run(
        ["psql", "-h", PGHOST, "-d", "epistemic", "-tAc", "SELECT to_regclass('s13probe.ledger');"],
        capture_output=True, text=True)
    if probe.stdout.strip() in ("", "\\N"):
        pytest.skip("s13probe mirror absent (substrate, not code)")
    cp = subprocess.run(["python3", str(OPERATOR_INSTRUMENTS / "soundness.py"), "s13probe"],
                        cwd=str(OPERATOR_INSTRUMENTS), capture_output=True, text=True)
    assert cp.returncode == 0, f"soundness.report crashed on an amends-bearing target:\n{cp.stderr}"
    assert "clause_defeat(" in cp.stdout, "the amends/clause-defeat branch did not run"


def test_clingo_run_raises_on_grounding_error(tmp_path: Path) -> None:
    """Item 5 durable fix: a grounding/parse error emits VALID JSON with an empty UNKNOWN model,
    so run_clingo would have returned [] -- a silent non-run banked as an empty derivation (F49 /
    ADR-0015 Rule 3). The closed success-vocabulary guard now RAISES instead. (The opt=True
    'OPTIMUM FOUND' verdict stays a success value -- covered by the contra_asp suite.)"""
    bad = tmp_path / "bad.lp"
    bad.write_text("a :- b, ) syntax (\n", encoding="utf-8")
    with pytest.raises(RuntimeError):
        run_clingo([bad], "")


# ------------------------------------------------------------------- AC2 id-order --
# ------------------------------------------------ AC8 full §1.5 DTO on scratch --
@needs_db
def test_dto_full_shape_synthetic_acceptance() -> None:
    """The full §1.5 DTO shape, apparatus-authored on the scratch lineage, with the ASP
    closures as the consumer. Acceptance completes on LABELED SYNTHETIC principals (SoD
    satisfied structurally); the interim amends is DTO-mooted; the inbound enacts edge is
    re-keyed; fragment standing follows attestation."""
    atoms = S.run_scenario("synthetic")
    assert "decomposed(1)" in atoms                       # referent decomposed
    assert 'decomp_attested("g1")' in atoms               # SoD-distinct synthetic attestation
    assert 'decomp_sod_violation("g1")' not in atoms
    assert "fragment_in_force(10)" in atoms               # attested fragment carries standing
    assert "head(11,13)" in atoms                         # fragment 11 over-ruled by 13
    assert "clause_defeat_moot_dto(3,1)" in atoms         # interim amends DTO-mooted
    assert "rekey_debt(enacts,5,1)" not in atoms          # inbound enacts re-keyed -> debt retracted


@needs_db
def test_dto_sod_violation_rejected() -> None:
    """An author self-attestation is NOT SoD-distinct: the gate rejects it (not attested,
    sod_violation fires, fragments pending)."""
    atoms = S.run_scenario("self")
    assert 'decomp_attested("g1")' not in atoms
    assert 'decomp_sod_violation("g1")' in atoms
    assert "fragment_pending(10)" in atoms and "fragment_pending(11)" in atoms
    assert "fragment_in_force(10)" not in atoms


@needs_db
def test_i7_assumption_expiry() -> None:
    """I7: an assumption past its validity bound is loudly not-in-force, and a scope resting
    on it is flagged; an in-bound assumption stays in force."""
    atoms = S.run_scenario("synthetic")
    assert "assumption_not_in_force(99)" in atoms and "expired_temporal(99)" in atoms
    assert "resting_on_expired(11,99)" in atoms
    assert "assumption_in_force(98)" in atoms


def test_amends_uniqueness_hardening() -> None:
    """The AC2 quote-and-strike uniqueness contract (pure; no DB): verbatim + 10+ chars +
    unique is accepted; too-short or paraphrase or ambiguous is refused."""
    stmt = "Use B-method for the interlocking and run the WCET analysis at SIL-4 margin"
    rat = "the two clauses were bundled into one row"
    assert S.validate_amends(stmt, rat, "run the WCET analysis at SIL-4 margin").ok
    assert not S.validate_amends(stmt, rat, "SIL-4").ok                    # < 10 chars
    assert not S.validate_amends(stmt, rat, "a paraphrase not present").ok  # not verbatim


# ------------------- audit fix 2: capability manifest never over-claims emission --
@needs_db
def test_require_refuses_capable_but_unemitted_family() -> None:
    """s13 is kernel-shape (has the `regards` column) but this increment emits NO regards
    fact -- so require('regards') must REFUSE loudly, not wave through a silent empty (the
    out-of-frame audit's finding 2: the manifest's `produced` must mean *emitted*)."""
    exp = export("s13")
    assert "regards" not in exp.produced_families()
    with pytest.raises(CapabilityError):
        exp.require("regards")
    # a genuinely-emitted family is not refused
    exp.require("supersedes")


# ------------- audit fix 1: the clause-defeat family differentialed on firing input --
@needs_db
def test_differential_covers_every_predicate_on_firing_input() -> None:
    """The five banked targets carry zero amends/answers, so clause_defeat/moot/withdrawn/
    condition2/question_answered were never differentialed on firing input (empty-vs-empty).
    The coverage fixture makes every predicate FIRE; the differential (SQL floor AND ASP) must
    AGREE bit-identically over it -- so the clause-defeat SQL CTEs are verified, not asserted."""
    F.setup()
    res = D.run_differential(F.SCHEMA)
    assert res.verdict() == D.AGREE and res.asp.atoms == res.sql.atoms
    gaps = [c for c in F.COVERAGE if not any(a.startswith(c + "(") for a in res.asp.atoms)]
    assert gaps == [], f"predicates never fired (still empty-vs-empty): {gaps}"


# ---------------- audit fix 3: synthetic vs authentic fragment standing distinguished --
@needs_db
def test_synthetic_standing_flagged_authentic_clears_it() -> None:
    """A fragment whose standing rests only on a labeled SYNTHETIC attestation is flagged
    synthetic_standing (a real lineage must refuse it); an authentic attestation confers
    fragment_in_force_authentic and clears the flag.

    The authentic arm no longer rides a `--attest-authentic` PREVIEW in the production code (deleted,
    Increment 3 item 2: a preview of an authenticity act is an oxymoron). Instead the fixture ITSELF
    completes the reserved authentic slot on the ISOLATED exercise schema and re-derives -- exercising
    the real ledger_dto.lp contract (decomp_attested_authentic -> fragment_in_force_authentic) without
    a production dry-run and without touching the live marriage_dto_scratch tap."""
    syn = S.run_scenario("synthetic")
    assert "synthetic_standing(10)" in syn
    assert not any(a.startswith("fragment_in_force_authentic(") for a in syn)
    # complete the reserved AUTHENTIC slot as a TEST fixture (on the isolated exercise schema), the
    # genuine shape the deleted preview only simulated, then re-derive from the live scratch rows.
    S._psql(f"UPDATE {S.SCHEMA}.attestation SET faithful=true, mece=true, "
            f"ts='2026-07-06 10:00:00+00' WHERE attester='{S.AUTHENTIC_ATTESTER}';")
    auth = S.run_closures(S.dto_edb() + S.assumes_edb(), [S.TNOW_LP, S.DTO_LP, S.ASSUMES_LP])
    assert 'decomp_attested_authentic("g1")' in auth   # the newly-#shown authentic-standing predicate
    assert "fragment_in_force_authentic(10)" in auth
    assert not any(a.startswith("synthetic_standing(") for a in auth)


# ------------------- audit fix 4: each derivation record hashes ITS OWN true input --
@needs_db
def test_derivation_records_hash_own_input() -> None:
    """The ASP record's input is the EDB text; the SQL floor's input is the live DB rows it
    reads directly. Each record's input_basis names its own basis and they hash different
    things -- no false 'shared hashed artifact' claim (finding 4)."""
    res = D.run_differential("s10")
    assert res.asp.record is not None and res.sql.record is not None
    assert "edb-text" in res.asp.record.input_basis
    assert "live-db" in res.sql.record.input_basis
    # the two consume genuinely different serializations, so their input hashes differ
    assert res.asp.record.input_hash != res.sql.record.input_hash


# ---------- Increment 3 item 3: the verifier's F49-shaped DISPLAY-CONTRACT class fix -------------
def test_verifier_display_contract_fails_loud_on_unshown_predicate() -> None:
    """The class fix (no DB): a verifier may DISPLAY only what the program `#show` contract EXPORTS,
    and must FAIL LOUDLY on a queried-but-unshown predicate -- never silently print '(none)' for a
    predicate the program does not emit (the F49 defect that hid decomp_attested_authentic while the
    atom HELD). Three properties, each a hazard the old `show()` walked into:"""
    shown = V.shown_predicates(V.PROGRAMS)
    # (a) item 3 part 1 landed: the authentic-standing predicate is now in the export contract.
    assert "decomp_attested_authentic" in shown
    # decomp_attests is a real DTO predicate that is #defined EDB but deliberately NOT #shown -- the
    # exact shape of the defect: queried, absent from the contract, must not read as FALSE.
    assert "decomp_attests" not in shown

    display = V.make_display({"foo(1)"}, shown)
    # (b) a SHOWN predicate with no atoms is honest absence -> "(none)".
    assert display("decomp_attested_authentic") == "(none)"
    # (c) a queried-but-UNSHOWN predicate raises LOUDLY (ADR-0002), never "(none)".
    with pytest.raises(RuntimeError, match="display-contract violation"):
        display("decomp_attests")


def test_verifier_refuses_a_show_less_program() -> None:
    """The guard behind the contract: a loaded program with NO `#show` means clingo emits EVERYTHING,
    so the exported set is not the union of #show names. shown_predicates refuses that loudly rather
    than returning a silently-too-small contract (the F49 posture applied to its own premise)."""
    prog = tmp_show_less()
    with pytest.raises(RuntimeError, match="display-contract undefined"):
        V.shown_predicates([prog])


def tmp_show_less() -> Path:
    p = HERE / "__pycache__" / "_show_less_fixture.lp"
    p.parent.mkdir(exist_ok=True)
    p.write_text("a(1).\n", encoding="utf-8")  # a program with zero #show directives
    return p


def test_same_second_neighbour_keys_on_id() -> None:
    """Two rows with the SAME ts but different ids: the T_now program must order by id,
    never ts (design §3 rule 2 / consult 17 §5.3). A hand EDB (no DB) proves the sort key:
    row 2 supersedes row 1 at the same epoch second; in_force must be {2}, head(1,2)."""
    edb = ("entry(1,1783264680,decision,design,held,high).\n"
           "entry(2,1783264680,decision,design,held,high).\n"
           "supersedes(2,1).\n")
    atoms = D.run_asp("same-second", edb).atoms
    assert "in_force(2)" in atoms and "in_force(1)" not in atoms
    assert "head(1,2)" in atoms and "head(2,2)" in atoms
