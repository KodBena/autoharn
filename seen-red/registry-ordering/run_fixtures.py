#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T08:01:37Z
#   last-change: 2026-07-12T08:02:39Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity witness for design/ORCH-SPEC-RESOURCE-REGISTRY.md §5 stage 2
(engine/lp/ordering_violations.lp + engine/ordering_obligations.lp + engine/ordering_edb.py +
engine/ordering_floor.py + engine/ordering_differential.py + engine/ordering_audit.py). Follows
the seen-red/preamble-ordering/run_fixtures.py pattern exactly: apparatus-authored SCRATCH
schemas on the TOY db (correlated-authorship, disclosed, not a claim of independent-source
proof), torn down after a clean run, left standing (never applied to any live schema) on a
failure -- the standing probe pattern.

THREE SCRATCH SCHEMAS, each proving one polarity/capability axis:

  GREEN (schema regordering): every check this build makes DISCHARGES --
    close_before_dependency (alpha depends on beta; beta closes BEFORE alpha), conditional_
    precedence (constraint: precedes theta iota; theta closes before iota), dependency_cycle
    (edges exist, none of them close a cycle).

  RED (schema regorderingneg): every check VIOLATES, plus the two named residues are witnessed
    present-but-unchecked --
    close_before_dependency (gamma depends on delta; gamma closes BEFORE delta -- the exact
    "verified missing check" the spec names), conditional_precedence (constraint: precedes
    epsilon zeta; zeta closes, epsilon never does), dependency_cycle (mu work_depends on nu
    [edge mu->nu] AND a `constraint: precedes mu nu` row [edge nu->mu] together close a cycle
    that SPANS BOTH edge families -- the exact case engine/lp/work_items.lp's own
    work_dependency_cycle/1, which only ever sees work_depends edges, cannot see). A malformed
    `constraint: precedes onlyone` row witnesses constraint_precedes_unparsed (UNDECIDABLE
    reason); a well-formed `constraint: excludes kappa lambda` row witnesses the
    constraint_excludes_deferred residue (recognized, not checked this pass).

  PRE-S22 (schema regorderingpre22): the lineage chain stops at s21 (no s22-work-item-ledger.sql
    applied) -- proves the pre_s22 forced-undecidable escape hatch: all three families read
    UNDECIDABLE(pre_s22), never silently VACUOUS, even though a `constraint: precedes p q` row IS
    on record (constraint: rows need no s22 column to be WRITTEN at all).

NEGATIVE CONTROL: the GREEN world's differential is re-run in an isolated subprocess with a
forged SQL-floor atom (`sql_atoms_override`), proving the differential catches a manufactured
single-producer divergence as DIVERGE_DEFECT -- the SAME seam
seen-red/preamble-ordering/run_fixtures.py's own negative control (and
engine/tests/test_ledger_marriage.py::test_single_producer_mutation_is_diverge_defect before
it) already uses, never touching either producer's real source.

Scratch-only: schemas regordering/regordering_kernel (role regordering_rw),
regorderingneg/regorderingneg_kernel (role regorderingneg_rw), and
regorderingpre22/regorderingpre22_kernel (role regorderingpre22_rw), TOY db (192.168.122.1) --
all torn down after a clean run, left standing on a failure (the standing probe pattern). Lazy
imports banned."""
from __future__ import annotations

import os
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)


PGHOST, DB = fixture_pghost(), "toy"
SCHEMA_G, KERN_G, ROLE_G = "regordering", "regordering_kernel", "regordering_rw"
SCHEMA_R, KERN_R, ROLE_R = "regorderingneg", "regorderingneg_kernel", "regorderingneg_rw"
SCHEMA_P, KERN_P, ROLE_P = "regorderingpre22", "regorderingpre22_kernel", "regorderingpre22_rw"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LINEAGE = REPO / "kernel" / "lineage"
ENGINE = REPO / "engine"

FULL_CHAIN = ("high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
             "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
             "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
             "s25-commission-kind.sql")
PRE_S22_CHAIN = ("high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
                "s21-session-aware-distinctness.sql")


def psql(sql: str) -> tuple[bool, str]:
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1", "-c", sql],
                        capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr)


def apply_ddl(fname: str, schema: str, kern: str, role: str) -> tuple[bool, str]:
    cp = subprocess.run(
        ["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1",
         "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}",
         "-f", str(LINEAGE / fname)],
        capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr)


def teardown(schema: str, kern: str, role: str) -> None:
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-c",
                    f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE; "
                    f"DROP OWNED BY {role}; DROP ROLE IF EXISTS {role};"],
                   capture_output=True, text=True)


def provision_stamp_secret(kern: str) -> None:
    hex_secret = secrets.token_hex(32)
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-q", "-v", "ON_ERROR_STOP=1",
                    "-c", f"TRUNCATE {kern}.stamp_secret;",
                    "-c", f"INSERT INTO {kern}.stamp_secret (secret) VALUES (decode('{hex_secret}','hex'));"],
                   capture_output=True, text=True, check=True)


def setup_schema(schema: str, kern: str, role: str, chain: tuple[str, ...],
                 needs_stamp_secret: bool) -> tuple[bool, str]:
    teardown(schema, kern, role)
    for f in chain:
        ok, out = apply_ddl(f, schema, kern, role)
        if not ok:
            return False, f"{f}: {out[-800:]}"
    if needs_stamp_secret:
        provision_stamp_secret(kern)
    return True, "ok"


def ins_row(schema: str, role: str, kind: str, statement: str, **cols: str | None) -> tuple[bool, str]:
    fields, vals = ["kind", "statement"], [f"'{kind}'", f"'{statement}'"]
    for k, v in cols.items():
        if v is None:
            continue
        fields.append(k)
        vals.append(f"'{v}'")
    return psql(f"SET ROLE {role}; INSERT INTO {schema}.ledger({', '.join(fields)}) "
               f"VALUES ({', '.join(vals)});")


def _target_env(schema: str, kern: str) -> dict[str, str]:
    """The FULL inherited environment (HOME/PATH/PGPASSFILE/etc. -- psql needs these to
    authenticate) plus the three LEDGER_* overrides that point engine/targets.py's
    LEDGER_DB/LEDGER_SCHEMA/LEDGER_KERN one-off resolution path at this fixture's own scratch
    schema (engine/targets.py's own precedence order, §3 "the weakest source")."""
    env = dict(os.environ)
    env["LEDGER_DB"] = DB
    env["LEDGER_SCHEMA"] = schema
    env["LEDGER_KERN"] = kern
    return env


def run_ordering_report(schema: str, kern: str) -> tuple[bool, str]:
    script = (f"from ordering_audit import build_report, print_report\n"
             f"r = build_report({schema!r})\n"
             f"print_report(r)\n")
    cp = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                        env=_target_env(schema, kern), cwd=str(ENGINE))
    return cp.returncode == 0, cp.stdout + cp.stderr


def run_ordering_differential(schema: str, kern: str, retain: bool = False) -> tuple[int, str]:
    args = [sys.executable, str(ENGINE / "ordering_differential.py"), schema]
    if retain:
        args.append("--retain")
    cp = subprocess.run(args, capture_output=True, text=True,
                        env=_target_env(schema, kern), cwd=str(ENGINE))
    return cp.returncode, cp.stdout + cp.stderr


def main() -> int:
    fails: list[str] = []
    ck = lambda cond, msg: fails.append(msg) if not cond else None  # noqa: E731
    log: list[str] = []

    ok, msg = setup_schema(SCHEMA_G, KERN_G, ROLE_G, FULL_CHAIN, needs_stamp_secret=True)
    if not ok:
        print(f"# REGISTRY-ORDERING FIXTURE SETUP FAILED (green schema): {msg}")
        return 1
    log.append(f"setup: GREEN schema {DB}.{SCHEMA_G}/{KERN_G} (role {ROLE_G}) -- full lineage through s25")

    ok, msg = setup_schema(SCHEMA_R, KERN_R, ROLE_R, FULL_CHAIN, needs_stamp_secret=True)
    if not ok:
        print(f"# REGISTRY-ORDERING FIXTURE SETUP FAILED (red schema): {msg}")
        teardown(SCHEMA_G, KERN_G, ROLE_G)
        return 1
    log.append(f"setup: RED schema {DB}.{SCHEMA_R}/{KERN_R} (role {ROLE_R}) -- full lineage through s25")

    ok, msg = setup_schema(SCHEMA_P, KERN_P, ROLE_P, PRE_S22_CHAIN, needs_stamp_secret=True)
    if not ok:
        print(f"# REGISTRY-ORDERING FIXTURE SETUP FAILED (pre-s22 schema): {msg}")
        teardown(SCHEMA_G, KERN_G, ROLE_G)
        teardown(SCHEMA_R, KERN_R, ROLE_R)
        return 1
    log.append(f"setup: PRE-S22 schema {DB}.{SCHEMA_P}/{KERN_P} (role {ROLE_P}) -- lineage stops at s21")

    green_report = red_report = pre22_report = ""
    green_diff = red_diff = pre22_diff = diverge_out = ""

    # ============================================================================
    # GREEN WORLD -- see module docstring.
    # ============================================================================
    ck(ins_row(SCHEMA_G, ROLE_G, "work_opened", "Open beta.", work_slug="beta", work_title="beta item")[0],
      "green: work_opened beta failed")
    ck(ins_row(SCHEMA_G, ROLE_G, "work_closed", "Close beta.", work_slug="beta",
              work_resolution="shipped", work_witness="w1")[0], "green: work_closed beta failed")
    ck(ins_row(SCHEMA_G, ROLE_G, "work_opened", "Open alpha.", work_slug="alpha", work_title="alpha item")[0],
      "green: work_opened alpha failed")
    ck(ins_row(SCHEMA_G, ROLE_G, "work_depends_on", "alpha depends on beta.", work_slug="alpha",
              work_depends_on="beta")[0], "green: work_depends_on alpha->beta failed")
    ck(ins_row(SCHEMA_G, ROLE_G, "work_closed", "Close alpha.", work_slug="alpha",
              work_resolution="shipped", work_witness="w2")[0], "green: work_closed alpha failed")
    ck(ins_row(SCHEMA_G, ROLE_G, "work_opened", "Open theta.", work_slug="theta", work_title="theta item")[0],
      "green: work_opened theta failed")
    ck(ins_row(SCHEMA_G, ROLE_G, "work_opened", "Open iota.", work_slug="iota", work_title="iota item")[0],
      "green: work_opened iota failed")
    ck(ins_row(SCHEMA_G, ROLE_G, "decision", "constraint: precedes theta iota")[0],
      "green: constraint precedes theta iota failed")
    ck(ins_row(SCHEMA_G, ROLE_G, "work_closed", "Close theta.", work_slug="theta",
              work_resolution="shipped", work_witness="w3")[0], "green: work_closed theta failed")
    ck(ins_row(SCHEMA_G, ROLE_G, "work_closed", "Close iota.", work_slug="iota",
              work_resolution="shipped", work_witness="w4")[0], "green: work_closed iota failed")

    ok, green_report = run_ordering_report(SCHEMA_G, KERN_G)
    ck(ok, f"green report run failed:\n{green_report}")
    ck("CLOSE_BEFORE_DEPENDENCY: DISCHARGED" in green_report,
      f"GREEN: expected CLOSE_BEFORE_DEPENDENCY: DISCHARGED, not found:\n{green_report}")
    ck("CONDITIONAL_PRECEDENCE: DISCHARGED" in green_report,
      f"GREEN: expected CONDITIONAL_PRECEDENCE: DISCHARGED, not found:\n{green_report}")
    ck("DEPENDENCY_CYCLE: DISCHARGED" in green_report,
      f"GREEN: expected DEPENDENCY_CYCLE: DISCHARGED, not found:\n{green_report}")
    diff_rc, green_diff = run_ordering_differential(SCHEMA_G, KERN_G, retain=True)
    ck(diff_rc == 0, f"GREEN differential expected exit 0 (AGREE): got {diff_rc}\n{green_diff}")
    ck("AGREE" in green_diff, f"GREEN differential expected AGREE: {green_diff}")

    # ============================================================================
    # RED WORLD -- see module docstring.
    # ============================================================================
    ck(ins_row(SCHEMA_R, ROLE_R, "work_opened", "Open delta.", work_slug="delta", work_title="delta item")[0],
      "red: work_opened delta failed")
    ck(ins_row(SCHEMA_R, ROLE_R, "work_opened", "Open gamma.", work_slug="gamma", work_title="gamma item")[0],
      "red: work_opened gamma failed")
    ck(ins_row(SCHEMA_R, ROLE_R, "work_depends_on", "gamma depends on delta.", work_slug="gamma",
              work_depends_on="delta")[0], "red: work_depends_on gamma->delta failed")
    ck(ins_row(SCHEMA_R, ROLE_R, "work_closed", "Close gamma (too early).", work_slug="gamma",
              work_resolution="shipped", work_witness="w5")[0], "red: work_closed gamma failed")
    ck(ins_row(SCHEMA_R, ROLE_R, "work_closed", "Close delta (late).", work_slug="delta",
              work_resolution="shipped", work_witness="w6")[0], "red: work_closed delta failed")
    ck(ins_row(SCHEMA_R, ROLE_R, "work_opened", "Open zeta.", work_slug="zeta", work_title="zeta item")[0],
      "red: work_opened zeta failed")
    ck(ins_row(SCHEMA_R, ROLE_R, "decision", "constraint: precedes epsilon zeta")[0],
      "red: constraint precedes epsilon zeta failed")
    ck(ins_row(SCHEMA_R, ROLE_R, "work_closed", "Close zeta.", work_slug="zeta",
              work_resolution="shipped", work_witness="w7")[0], "red: work_closed zeta failed")
    ck(ins_row(SCHEMA_R, ROLE_R, "work_opened", "Open mu.", work_slug="mu", work_title="mu item")[0],
      "red: work_opened mu failed")
    ck(ins_row(SCHEMA_R, ROLE_R, "work_opened", "Open nu.", work_slug="nu", work_title="nu item")[0],
      "red: work_opened nu failed")
    ck(ins_row(SCHEMA_R, ROLE_R, "work_depends_on", "mu depends on nu.", work_slug="mu",
              work_depends_on="nu")[0], "red: work_depends_on mu->nu failed")
    ck(ins_row(SCHEMA_R, ROLE_R, "decision", "constraint: precedes mu nu")[0],
      "red: constraint precedes mu nu (cycle-closing edge) failed")
    ck(ins_row(SCHEMA_R, ROLE_R, "decision", "constraint: precedes onlyone")[0],
      "red: malformed constraint (single slug) failed")
    ck(ins_row(SCHEMA_R, ROLE_R, "decision", "constraint: excludes kappa lambda")[0],
      "red: constraint excludes kappa lambda (deferred residue) failed")

    ok, red_report = run_ordering_report(SCHEMA_R, KERN_R)
    ck(ok, f"red report run failed:\n{red_report}")
    ck("CLOSE_BEFORE_DEPENDENCY: VIOLATED" in red_report,
      f"RED: expected CLOSE_BEFORE_DEPENDENCY: VIOLATED, not found:\n{red_report}")
    ck("CONDITIONAL_PRECEDENCE: VIOLATED" in red_report,
      f"RED: expected CONDITIONAL_PRECEDENCE: VIOLATED, not found:\n{red_report}")
    ck("DEPENDENCY_CYCLE: VIOLATED" in red_report,
      f"RED: expected DEPENDENCY_CYCLE: VIOLATED (mu/nu, cross-family), not found:\n{red_report}")
    ck("constraint_unparsed" in red_report,
      f"RED: expected constraint_unparsed reason (the malformed row), not found:\n{red_report}")
    ck("constraint_excludes_deferred" in red_report,
      f"RED: expected the constraint_excludes_deferred count in the counts= dict, not found:\n{red_report}")
    diff_rc, red_diff = run_ordering_differential(SCHEMA_R, KERN_R, retain=True)
    ck(diff_rc == 0, f"RED differential expected exit 0 (AGREE -- the WORLD is red, the "
                     f"DIFFERENTIAL over it is still bit-identical, GREEN): got {diff_rc}\n{red_diff}")
    ck("AGREE" in red_diff, f"RED differential expected AGREE: {red_diff}")

    # ============================================================================
    # PRE-S22 WORLD -- proves the forced-undecidable escape hatch (see module docstring).
    # ============================================================================
    ck(ins_row(SCHEMA_P, ROLE_P, "decision", "constraint: precedes p q")[0],
      "pre-s22: constraint precedes p q failed")
    ok, pre22_report = run_ordering_report(SCHEMA_P, KERN_P)
    ck(ok, f"pre-s22 report run failed:\n{pre22_report}")
    for fam in ("CLOSE_BEFORE_DEPENDENCY", "CONDITIONAL_PRECEDENCE", "DEPENDENCY_CYCLE"):
        ck(f"{fam}: UNDECIDABLE" in pre22_report,
          f"PRE-S22: expected {fam}: UNDECIDABLE, not found:\n{pre22_report}")
    ck("pre_s22" in pre22_report, f"PRE-S22: expected pre_s22 reason, not found:\n{pre22_report}")
    diff_rc, pre22_diff = run_ordering_differential(SCHEMA_P, KERN_P, retain=True)
    ck(diff_rc == 0, f"PRE-S22 differential expected exit 0 (AGREE): got {diff_rc}\n{pre22_diff}")
    ck("AGREE" in pre22_diff, f"PRE-S22 differential expected AGREE: {pre22_diff}")

    # ============================================================================
    # NEGATIVE CONTROL -- manufactured DIVERGE_DEFECT (the GREEN world, one forged atom in the
    # SQL floor's own returned set, in an ISOLATED subprocess -- never touching either producer's
    # real source, the seen-red/preamble-ordering/run_fixtures.py precedent).
    # ============================================================================
    script = f'''\
import os
import sys
sys.path.insert(0, {str(ENGINE)!r})
os.environ["LEDGER_DB"] = {DB!r}
os.environ["LEDGER_SCHEMA"] = {SCHEMA_G!r}
os.environ["LEDGER_KERN"] = {KERN_G!r}
import ordering_differential as od
res = od.run_differential({SCHEMA_G!r},
                          sql_atoms_override={{"ordering_verdict(close_before_dependency,FORGED)"}})
od.print_result(res)
print()
print("VERDICT:", res.verdict())
import sys
sys.exit(0 if res.verdict() == "AGREE" else 1)
'''
    script_path = Path(tempfile.mktemp(suffix=".py"))
    script_path.write_text(script, encoding="utf-8")
    try:
        cp = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True,
                            cwd=str(ENGINE))
        diverge_out = cp.stdout + cp.stderr
        ck(cp.returncode == 1, f"negative control expected exit 1 (DIVERGE_DEFECT): got {cp.returncode}\n{diverge_out}")
        ck("DIVERGE_DEFECT" in diverge_out, f"negative control expected DIVERGE_DEFECT: {diverge_out}")
    finally:
        script_path.unlink(missing_ok=True)

    (HERE / "green-report.txt").write_text(green_report, encoding="utf-8")
    (HERE / "red-report.txt").write_text(red_report, encoding="utf-8")
    (HERE / "pre-s22-report.txt").write_text(pre22_report, encoding="utf-8")
    (HERE / "differential-agree-green.txt").write_text(green_diff, encoding="utf-8")
    (HERE / "differential-agree-red.txt").write_text(red_diff, encoding="utf-8")
    (HERE / "differential-agree-pre-s22.txt").write_text(pre22_diff, encoding="utf-8")
    (HERE / "differential-diverge-defect.txt").write_text(diverge_out, encoding="utf-8")

    if fails:
        print("# REGISTRY-ORDERING FIXTURES: FAILED")
        for f in fails:
            print(f"  [FAIL] {f}")
        print("\n(scratch schemas left standing for inspection: "
             f"{SCHEMA_G}/{KERN_G}, {SCHEMA_R}/{KERN_R}, {SCHEMA_P}/{KERN_P})")
        return 1

    teardown(SCHEMA_G, KERN_G, ROLE_G)
    teardown(SCHEMA_R, KERN_R, ROLE_R)
    teardown(SCHEMA_P, KERN_P, ROLE_P)
    print("# REGISTRY-ORDERING FIXTURES: ALL GREEN")
    for line in log:
        print(f"  {line}")
    print(f"  banked: {HERE}/green-report.txt, red-report.txt, pre-s22-report.txt, "
         f"differential-agree-{{green,red,pre-s22}}.txt, differential-diverge-defect.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
