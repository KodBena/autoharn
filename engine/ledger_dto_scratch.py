#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-06T05:46:54Z
#   last-change: 2026-07-06T15:30:01Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""ledger_dto_scratch -- the apparatus-authored FIRST EXERCISE of the full §1.5
decompose-then-overrule (DTO) shape, on a SCRATCH lineage, with the ASP closures
(ledger_dto.lp) as the CONSUMER that ends the "no consumer" deferral.

WHY THE FULL SHAPE, NOT THE DEGENERATE FORM (scheduling ruling 2026-07-06,
deliberations/clause-defeat-decompose-then-overrule.md). The degenerate
"supersede-and-reissue" is expressible since s1 and contains NONE of DTO's
machinery; banking it as "first exercise" is a dressed-up discharge, struck. The
real first exercise is the full §1.5 shape, worked out here:
  1. defeat the referent (whole-row),
  2. decompose it into first-class fragment rows (a `decomposes` edge + a group id),
  3. over-rule the specific fragment (whole-row defeat of the fragment),
plus the faithfulness/MECE ATTESTATION GATE (an attester SoD-distinct from the
decomposition's author) and one INBOUND-EDGE RE-KEY (the conservative re-key debt
made TRUE information).

Also exercised: the interim `amends` quote-and-strike (the AC2 uniqueness hardening,
never fired in anger -- the FIRST live `amends` fixtures anywhere; ground truth: zero
amends rows exist in nla/s13/s14), and I7 (an `assumes` edge with a validity bound +
the expiry closure).

ATTESTER PRINCIPALS -- SYNTHETIC vs AUTHENTIC, DISTINCTLY LABELED (maintainer
refinement 2026-07-06). Mechanical acceptance completes on LABELED SYNTHETIC
principals: the SoD gate (attester distinct from author) is satisfied STRUCTURALLY
by two synthetic principals, each labeled synthetic in the record, so the full DTO
machinery is proven end-to-end WITHOUT waiting on any human. A SEPARATE,
distinctly-labeled AUTHENTIC maintainer attestation SLOT is reserved as a
NON-BLOCKING fixture (faithful/mece unset until the maintainer acts) -- it is never
conflated with the synthetic acceptance and never labeled as done. ATTRIBUTION
HONESTY is the hard constraint: a synthetic principal's act is never labeled human.

SCRATCH DISCIPLINE. The lineage is `epistemic.marriage_dto_scratch` -- created
OUTSIDE every evidence lineage (never nla, never any s* subject ledger), apparatus-
owned and WRITABLE (the read-only posture binds the EVIDENCE ledgers, not this
throwaway). It is NAMED IN THE WITNESS. Subject-facing bytes are untouched anywhere."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from clingo_run import quote_term, run_clingo
from ledger_edb import PGHOST, export

HERE = Path(__file__).resolve().parent
SCHEMA = "marriage_dto_scratch"
DB = "epistemic"  # a scratch SCHEMA in the apparatus db, outside every s*/nla evidence lineage
TNOW_LP = HERE / "ledger_tnow.lp"
DTO_LP = HERE / "ledger_dto.lp"
ASSUMES_LP = HERE / "ledger_assumes.lp"
WITNESS = HERE / "docs" / "ledger-marriage" / "dto-scratch.witness.txt"

# Principals, LABELED. The `synthetic:` / `authentic:` prefix is carried verbatim into
# the record and the EDB so a synthetic act can never be read as a human one.
AUTHOR = "synthetic:apparatus_engineer"       # the decomposition's author (link 24, synthetic)
SYN_ATTESTER = "synthetic:reviewer_B"         # SoD-distinct synthetic attester (acceptance)
AUTHENTIC_ATTESTER = "authentic:maintainer"   # the reserved, NON-BLOCKING human slot


def _psql(sql: str, *, db: str = DB) -> str:
    return subprocess.run(["psql", "-h", PGHOST, "-d", db, "-tAc", sql],
                          capture_output=True, text=True, check=True).stdout.strip()


# --------------------------------------------------------------- scratch schema --
def setup_scratch() -> None:
    """Create the scratch lineage and author the base + DTO rows. Idempotent (DROP+CREATE).
    NEVER touches an evidence ledger -- this schema is apparatus-owned and throwaway."""
    ddl = f"""
    DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;
    CREATE SCHEMA {SCHEMA};
    CREATE TABLE {SCHEMA}.ledger (
      id bigint PRIMARY KEY, ts timestamptz NOT NULL, kind text NOT NULL, concern text,
      status text, confidence text, statement text, rationale text, actor text,
      supersedes bigint, enacts bigint[], answers bigint,
      amends bigint, amends_scope text,
      decomposes bigint, decomp_group text
    );
    CREATE TABLE {SCHEMA}.decomp_group (
      group_id text PRIMARY KEY, target bigint NOT NULL, author text NOT NULL, created_ts timestamptz
    );
    -- principal_kind LABELS every attestation synthetic-vs-authentic (attribution honesty);
    -- faithful/mece are NULL for a RESERVED slot (not yet acted) and true for a completed one.
    CREATE TABLE {SCHEMA}.attestation (
      group_id text NOT NULL, attester text NOT NULL, principal_kind text NOT NULL,
      faithful boolean, mece boolean, ts timestamptz
    );
    CREATE TABLE {SCHEMA}.rekey (
      edge_kind text NOT NULL, citing bigint NOT NULL, old_target bigint NOT NULL, new_fragment bigint NOT NULL
    );
    """
    _psql(ddl)
    rows = f"""
    INSERT INTO {SCHEMA}.ledger (id,ts,kind,concern,status,confidence,statement,rationale,actor,supersedes,enacts,answers,amends,amends_scope,decomposes,decomp_group) VALUES
     (1,'2026-07-06 08:00:00+00','decision','design','held','high',
        'Use B-method for the interlocking and run the WCET analysis at SIL-4 margin',
        'the two clauses were bundled into one row', '{AUTHOR}', NULL, NULL, NULL, NULL, NULL, NULL, NULL),
     (2,'2026-07-06 08:01:00+00','note','process','confirmed','high','scaffolding note','','{AUTHOR}',NULL,NULL,NULL,NULL,NULL,NULL,NULL),
     (5,'2026-07-06 08:05:00+00','verification','enactment','confirmed','high',
        'implemented the interlocking per the compound decision','','{AUTHOR}',NULL,ARRAY[1],NULL,NULL,NULL,NULL,NULL);
    """
    _psql(rows)


def author_interim_amends() -> None:
    """The interim quote-and-strike track: row 3 clause-defeats row 1 by a VERBATIM
    quotation of one clause (the first live `amends` fixture anywhere)."""
    scope = "run the WCET analysis at SIL-4 margin"
    _psql(f"""INSERT INTO {SCHEMA}.ledger (id,ts,kind,concern,status,confidence,statement,rationale,actor,amends,amends_scope)
      VALUES (3,'2026-07-06 08:10:00+00','snag','design','open','high',
        'the WCET clause needs a diverse monitor', 'clause-level defeat', '{AUTHOR}', 1, '{scope}');""")


def author_dto_fragments() -> None:
    """The §1.5 shape MINUS the referent eviction: decompose row 1 into first-class fragments
    (group g1), over-rule the specific fragment (13 supersedes 11), record the group author.
    The referent (row 1) is NOT yet superseded here -- eviction is evict_referent(), authored
    only AFTER attestation (F-B evict-on-attest ordering; RATIFIED 2026-07-06)."""
    _psql(f"""INSERT INTO {SCHEMA}.ledger (id,ts,kind,concern,status,confidence,statement,actor,decomposes,decomp_group) VALUES
      (10,'2026-07-06 09:00:00+00','decision','design','held','high','Use B-method for the interlocking','{AUTHOR}',1,'g1'),
      (11,'2026-07-06 09:00:00+00','decision','design','held','high','Run the WCET analysis at SIL-4 margin','{AUTHOR}',1,'g1');""")
    _psql(f"""INSERT INTO {SCHEMA}.ledger (id,ts,kind,concern,status,confidence,statement,actor,supersedes) VALUES
      (13,'2026-07-06 09:10:00+00','decision','design','held','high','Run the WCET analysis at SIL-4 margin OR provide a diverse monitor','{AUTHOR}',11);""")
    _psql(f"""INSERT INTO {SCHEMA}.decomp_group (group_id,target,author,created_ts)
      VALUES ('g1',1,'{AUTHOR}','2026-07-06 09:00:00+00');""")


def evict_referent() -> None:
    """Whole-row supersede the decomposition referent (row 14 supersedes row 1). F-B
    evict-on-attest ordering (RATIFIED 2026-07-06): authored AFTER attestation on the valid paths.
    With DERIVED eviction (ledger_dto.lp), the referent's current-view membership is now DERIVED
    from group attestation, NOT from this bare supersedes row: on the valid (attested) paths the
    group is attested first, so decomp_evicts_referent(1) fires and referent_in_current(1) clears
    (the referent genuinely leaves the current view). On the SoD-violation (self-attest) path the
    group is UNATTESTED, so this supersedes row EVICTS NOTHING -- referent_in_current(1) STILL holds
    (the F44 aspectual state, retained) AND premature_eviction(1,g1) fires (the void supersede is
    loud). Honors append-only monotonicity: the eviction carries the HIGHEST id (14, after the
    over-rule row 13)."""
    _psql(f"""INSERT INTO {SCHEMA}.ledger (id,ts,kind,concern,status,confidence,statement,actor,supersedes) VALUES
      (14,'2026-07-06 09:40:00+00','decision','design','held','high','decomposition of row 1 into g1 fragments','{AUTHOR}',1);""")


def record_synthetic_attestation() -> None:
    """Mechanical acceptance: a COMPLETED faithfulness+MECE attestation by the SoD-distinct
    SYNTHETIC principal (labeled synthetic). This is what completes acceptance without a human."""
    _psql(f"""INSERT INTO {SCHEMA}.attestation (group_id,attester,principal_kind,faithful,mece,ts)
      VALUES ('g1','{SYN_ATTESTER}','synthetic',true,true,'2026-07-06 09:30:00+00');""")


def reserve_authentic_slot() -> None:
    """A SEPARATE, distinctly-labeled AUTHENTIC maintainer attestation slot -- RESERVED and
    NON-BLOCKING (faithful/mece NULL until the maintainer acts). Present in the record so the
    authentic decision has an honest home; never counted as a completed attestation, never
    conflated with the synthetic acceptance."""
    _psql(f"""INSERT INTO {SCHEMA}.attestation (group_id,attester,principal_kind,faithful,mece,ts)
      VALUES ('g1','{AUTHENTIC_ATTESTER}','authentic',NULL,NULL,NULL);""")


def record_author_self_attestation() -> None:
    """The SoD-VIOLATION demonstration: the author self-attests. The gate must reject it."""
    _psql(f"""INSERT INTO {SCHEMA}.attestation (group_id,attester,principal_kind,faithful,mece,ts)
      VALUES ('g1','{AUTHOR}','synthetic',true,true,'2026-07-06 09:30:00+00');""")


def rekey_inbound() -> None:
    """Re-key the inbound enacts(5,1) edge to fragment 10 (the citation meant the B-method
    clause). This RETRACTS the rekey_debt the DTO closure raised."""
    _psql(f"""INSERT INTO {SCHEMA}.rekey (edge_kind,citing,old_target,new_fragment) VALUES ('enacts',5,1,10);""")


# ---------------------------------------------------------------- amends uniqueness --
@dataclass(frozen=True)
class AmendsCheck:
    ok: bool
    reason: str


def validate_amends(statement: str, rationale: str, scope: str) -> AmendsCheck:
    """The e13 write-boundary quotation contract (AC2 uniqueness hardening), mirrored:
    an `amends_scope` must be a VERBATIM quotation (>=10 chars) of the target's
    statement/rationale, and must locate UNAMBIGUOUSLY (exactly one occurrence). An
    ambiguous or too-short scope is REFUSED (never paraphrased -- escalate)."""
    if len(scope) < 10:
        return AmendsCheck(False, f"scope < 10 chars (contract: verbatim quotation, 10+)")
    hay = f"{statement}\n{rationale}"
    occ = hay.count(scope)
    if occ == 0:
        return AmendsCheck(False, "not a verbatim substring of the target (paraphrase refused)")
    if occ > 1:
        return AmendsCheck(False, f"occurs {occ}x -- ambiguous, cannot locate the clause")
    return AmendsCheck(True, "verbatim, 10+ chars, unique -- accepted")


# -------------------------------------------------------------------- DTO EDB + run --
def dto_edb() -> str:
    """The base EDB (via ledger_edb over the scratch schema) PLUS the DTO/assumes fact
    families ledger_dto.lp consumes, read from the scratch tables. Only COMPLETED
    attestations (faithful AND mece true) reach decomp_attests -- a reserved authentic
    slot (NULLs) never counts as a completed attestation."""
    os.environ["LEDGER_DB"] = DB
    os.environ["LEDGER_SCHEMA"] = SCHEMA
    try:
        base = export(SCHEMA).edb_text()
    finally:
        del os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"]
    lines = [base, "% ---- DTO EDB (decomposes/group/attest/rekey) ----"]
    for r in _psql(f"SELECT id, decomposes FROM {SCHEMA}.ledger WHERE decomposes IS NOT NULL ORDER BY id;").splitlines():
        if r.strip():
            f, t = r.split("|")
            lines.append(f"decomposes({int(f)},{int(t)}).")
    for r in _psql(f"SELECT id, decomp_group FROM {SCHEMA}.ledger WHERE decomp_group IS NOT NULL ORDER BY id;").splitlines():
        if r.strip():
            f, g = r.split("|")
            lines.append(f"decomp_group({quote_term(g)},{int(f)}).")
    for r in _psql(f"SELECT group_id, author FROM {SCHEMA}.decomp_group ORDER BY group_id;").splitlines():
        if r.strip():
            g, a = r.split("|")
            lines.append(f"decomp_author({quote_term(g)},{quote_term(a)}).")
    # completed attestations only (faithful AND mece); a reserved authentic slot has NULLs.
    for r in _psql(f"SELECT group_id, attester, principal_kind FROM {SCHEMA}.attestation "
                   f"WHERE faithful IS TRUE AND mece IS TRUE ORDER BY attester;").splitlines():
        if r.strip():
            g, by, kind = r.split("|")
            lines.append(f"decomp_attests({quote_term(g)},{quote_term(by)}).")
            if kind == "authentic":  # an AUTHENTIC principal's completed attestation confers real standing
                lines.append(f"attester_authentic({quote_term(by)}).")
    for r in _psql(f"SELECT edge_kind, citing, old_target FROM {SCHEMA}.rekey ORDER BY citing;").splitlines():
        if r.strip():
            k, c, t = r.split("|")
            lines.append(f"rekeyed({k},{int(c)},{int(t)}).")
    return "\n".join(lines) + "\n"


def assumes_edb() -> str:
    """I7: an `assumes` edge with a validity bound, plus the run-time `now`/`record_head`
    cursors. Assumption 99 (relied on by fragment 11) has a wall-clock bound in the PAST,
    so the expiry closure fires; assumption 98 (fragment 10) is still in force.

    F-C superseded-assumption fixture (fidelity review §1): assumption 11 -- a ledger row
    (the over-ruled fragment, superseded by 13) relied on as an assumption by scope 10 -- has
    a validity bound in the FUTURE, so it never EXPIRES, yet its whole row is SUPERSEDED. With
    ledger_assumes.lp composing with the supersession closure it is loudly not-in-force and its
    scope is flagged resting_on_superseded(10,11); before the fix, an unexpired-but-superseded
    assumption still read in-force (the same censored-record shape F-A closes for answers). This
    program is loaded stacked on ledger_tnow.lp, which supplies superseded/1."""
    return (
        "% ---- I7 assumptions with validity bounds ----\n"
        "assumes(99,11).\n"
        "valid_until(99,1751788800).\n"   # 2025-07-06 -- a year in the past => expired
        "now(1783324800).\n"              # 2026-07-06
        "assumes(98,10).\n"
        "valid_until(98,1893456000).\n"   # 2030 -- still in force
        "% ---- F-C: an unexpired but SUPERSEDED assumption (row 11, over-ruled by 13) ----\n"
        "assumes(11,10).\n"
        "valid_until(11,1893456000).\n"   # 2030 -- NOT expired; only supersession retracts it
        "record_head(14).\n"              # current max id (the evictor row 14)
    )


def run_closures(edb: str, programs: list[Path]) -> set[str]:
    return {a for a in run_clingo(programs, edb) if "(" in a}


def write_witness(edb: str) -> None:
    WITNESS.parent.mkdir(parents=True, exist_ok=True)
    WITNESS.write_text(
        "# DTO scratch witness (link 24) -- the apparatus-authored §1.5 DTO exercise.\n"
        f"# scratch lineage: {DB}.{SCHEMA}  (OUTSIDE every evidence lineage; apparatus-owned, writable)\n"
        f"# author (SYNTHETIC): {AUTHOR}\n"
        f"# SoD-distinct attester (SYNTHETIC, completes acceptance): {SYN_ATTESTER}\n"
        f"# authentic attester SLOT (RESERVED, NON-BLOCKING): {AUTHENTIC_ATTESTER}\n"
        "#   -- synthetic and authentic principals are DISTINCTLY LABELED; a synthetic act is\n"
        "#      never labeled human, and the synthetic acceptance is never conflated with the\n"
        "#      authentic slot (maintainer refinement 2026-07-06).\n"
        "# subject-facing bytes: UNTOUCHED. Evidence ledgers (nla, s*): READ-ONLY throughout.\n\n"
        + edb, encoding="utf-8")


def show(atoms: set[str], pred: str) -> str:
    got = sorted(a for a in atoms if a.startswith(pred + "("))
    return " ".join(got) if got else "(none)"


def run_scenario(attest: str = "synthetic") -> set[str]:
    """Author the full §1.5 DTO scenario on the scratch lineage and return the derived
    atoms. `attest` in {'synthetic' (SoD-distinct acceptance), 'self' (SoD violation)}.
    The single home both main() and the tests drive, so the demo and the gate agree."""
    setup_scratch()
    author_interim_amends()
    author_dto_fragments()
    reserve_authentic_slot()
    if attest == "self":
        record_author_self_attestation()
    else:
        record_synthetic_attestation()
    # F-B evict-on-attest ORDERING (RATIFIED 2026-07-06) + DERIVED eviction: the referent (row 1) is
    # superseded ONLY NOW -- after attestation has been recorded. With derived eviction, the referent's
    # current-view membership is DERIVED from group attestation: on the valid (synthetic)
    # path the group is attested first, so decomp_evicts_referent(1) fires, referent_in_current(1)
    # clears, and premature_eviction does NOT fire; on the SoD-violation (self-attest) path there is NO
    # valid attestation, so this bare supersede EVICTS NOTHING -- referent_in_current(1) STILL holds
    # (the F44 aspectual state, retained) and premature_eviction(1,"g1") fires (loud).
    evict_referent()
    rekey_inbound()
    edb = dto_edb() + assumes_edb()
    write_witness(edb)
    return run_closures(edb, [TNOW_LP, DTO_LP, ASSUMES_LP])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--attest-self", action="store_true",
                    help="SoD-VIOLATION demo: the author self-attests (no synthetic reviewer); "
                         "the gate must reject it (not attested, sod_violation, fragments pending)")
    # NOTE (Increment 3 item 2, maintainer-ratified 2026-07-06): a `--attest-authentic` PREVIEW
    # mode was DELETED here, not disarmed. A "preview of an authenticity act" is an oxymoron -- an
    # authentic (human) attestation is a genuine act, never a dry-run the apparatus authors on the
    # maintainer's behalf (that would fill the real authentic:maintainer slot with a synthetic tap,
    # the exact attribution lie the SYNTHETIC/AUTHENTIC labeling exists to forbid). The authentic
    # derive path is covered instead by dto_authentic_verify.py (derive-only over the LIVE tap, no
    # rebuild) and by the synthetic fixtures here; the LP contract (fragment_in_force_authentic,
    # decomp_attested_authentic) is exercised by test fixtures on an isolated exercise schema.
    args = ap.parse_args(argv)

    print(f"# DTO scratch exercise -- lineage {DB}.{SCHEMA} (outside every evidence lineage)")
    print(f"#   author (synthetic): {AUTHOR}   attester (synthetic, SoD-distinct): {SYN_ATTESTER}\n")

    print("## interim amends quote-and-strike (AC2 uniqueness hardening; first live amends fixture)")
    stmt = "Use B-method for the interlocking and run the WCET analysis at SIL-4 margin"
    for scope in ("run the WCET analysis at SIL-4 margin", "SIL-4", "the WCET analysis"):
        chk = validate_amends(stmt, "the two clauses were bundled into one row", scope)
        print(f"  amends_scope {scope!r:45} -> {'ACCEPT' if chk.ok else 'REFUSE'}: {chk.reason}")

    mode = "self" if args.attest_self else "synthetic"
    modelabel = {"self": "SoD-VIOLATION (author self-attest)",
                 "synthetic": "acceptance on SYNTHETIC principals"}[mode]
    print(f"\n## full §1.5 DTO: decompose row 1 -> {{10,11}} in group g1; supersede referent; over-rule fragment 11")
    print(f"   attestation mode: {modelabel}")
    atoms = run_scenario(mode)

    print(f"\n  decomposed:                 {show(atoms, 'decomposed')}")
    print(f"  clause_defeat_moot_dto:     {show(atoms, 'clause_defeat_moot_dto')}   (interim amends on row 1, now DTO-moot)")
    print(f"  decomp_attested:            {show(atoms, 'decomp_attested')}")
    print(f"  decomp_pending_attestation: {show(atoms, 'decomp_pending_attestation')}")
    print(f"  decomp_sod_violation:       {show(atoms, 'decomp_sod_violation')}")
    print(f"  fragment_in_force:          {show(atoms, 'fragment_in_force')}")
    print(f"  fragment_in_force_authentic:{show(atoms, 'fragment_in_force_authentic')}")
    print(f"  synthetic_standing:         {show(atoms, 'synthetic_standing')}   <-- standing rests only on a SYNTHETIC attestation; a real lineage must refuse")
    print(f"  fragment_pending:           {show(atoms, 'fragment_pending')}")
    print(f"  referent_in_current:        {show(atoms, 'referent_in_current')}   (F-B DERIVED eviction: referent RETAINED until group attested -- present on the SoD-violation path, cleared once attested)")
    print(f"  decomp_evicts_referent:     {show(atoms, 'decomp_evicts_referent')}   (F-B: referent LEAVES the current view iff group attested -- present ONLY on the attested paths)")
    print(f"  premature_eviction:         {show(atoms, 'premature_eviction')}   (F-B: the bare supersede is VOID while group UNATTESTED -- fires ONLY on the SoD-violation path; RATIFIED evict-on-attest 2026-07-06)")
    print(f"  over-rule of fragment 11:   head(11,*) = {[a for a in sorted(atoms) if a.startswith('head(11,')]}")
    print(f"  rekey_debt (after re-key):  {show(atoms, 'rekey_debt')}   (enacts(5,1) re-keyed to fragment 10 -> debt retracted)")

    print("\n## I7 assumptions with validity bounds + expiry/supersession closure")
    for pred in ("assumption_in_force", "assumption_not_in_force", "expired_temporal",
                 "resting_on_expired", "resting_on_superseded"):
        print(f"  {pred:24} {show(atoms, pred)}")
    print("  (F-C: assumption 11 -- a row over-ruled by 13 -- is NOT expired but IS superseded, so it is")
    print("        loudly not-in-force; ledger_assumes.lp now composes with the supersession closure.)")

    print(f"\n# witness written: {WITNESS}")
    print(f"# acceptance COMPLETE on labeled synthetic principals (SoD satisfied structurally: "
          f"{SYN_ATTESTER} != {AUTHOR}).")
    print(f"# a separate, distinctly-labeled AUTHENTIC attestation slot ({AUTHENTIC_ATTESTER}) is "
          f"RESERVED and NON-BLOCKING -- the maintainer may fill it whenever; never faked as done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
