#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T02:17:36Z
#   last-change: 2026-07-14T22:24:42Z
#   contributors: e4410ef6/main, a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity witness for Part 3 of design/ORCH-CONTEMPORANEITY-PART3-SPEC.md
(engine/lp/preamble_ordering.lp + engine/preamble_obligations.lp + the E1-E9 extensions to
engine/contemp_edb.py + engine/preamble_floor.py + engine/preamble_differential.py). Follows the
Part 2 fixture pattern (seen-red/contemporaneity-audit/run_fixtures.py) exactly: an
apparatus-authored SCRATCH world (correlated-authorship, disclosed, not a claim of independent-
source proof), torn down after a clean run, left standing (never applied to any live schema) on
a failure -- the standing probe pattern.

TWO LIVE-DB SCRATCH WORLDS, ONE CONSOLIDATED NARRATIVE EACH (not eleven separate tiny worlds --
each family's own green/red condition is individually inspectable in ONE coherent world's own
report, matching the "one apparatus-authored GREEN fixture ... and one RED fixture" plan at the
per-FAMILY granularity while keeping the fixture count tractable):

  GREEN (schema preambleorder): every family this build can DISCHARGE, discharges --
    commission-first, verify-commission ran in window, decomposition refs the commission,
    decompose-before-mutation, open-before-claim, claim-before-close, a review after the
    decomposition before stop, criteria-before-mutation, a fresh decision before the delegation
    dispatch, a decision inside the stop-disposition window, no s22 violation at stop.
    F11's OWN scope note: this build's review-gap/question_open arms are UNCONDITIONALLY
    UNDECIDABLE(capability_absent) (engine/lp/preamble_ordering.lp's own header) -- so F11's
    "green" polarity here reads UNDECIDABLE(capability_absent), never DISCHARGED, honestly
    -- the closest true-clean signal this build can emit for that family.

  RED (schema preambleorderneg): a SEPARATE scratch schema (F1 keys off the GLOBAL min ledger
    id, so green/red rows cannot share one schema) where every family this build can VIOLATE,
    violates -- min row is an assumption, not commission (F1); a commission row exists but its
    verify-commission event landed AFTER the first work_opened row (F2); a work_opened row with
    no refs at all (F3); a mutation event with no preceding decomposition, which ALSO makes the
    verification row's own criteria citation land after it (F4 and F8, one stroke); a review row
    that is UNTOKENED (F7 -> untokened_row, not violated -- the untokened seam witness, see
    below); a delegation dispatch and a stop event with NO decision-kind row anywhere in this
    schema at all (F9 and F10, trivially and unambiguously); a work_depends_on row naming an
    antecedent slug that was never opened (F11, a real, write-time-reachable s22 violation -- see
    the F5/F6 note below for why the OTHER s22 member, shipped-without-witness, could not be used
    this way). A SECOND commission row (id6) whose own sole verify-commission event lands INSIDE
    its own invocation window supplies the window_overlap seam witness (an instance-level atom;
    F2's family verdict stays VIOLATED regardless, via id2 alone -- violated always outranks
    undecidable, spec §5's own priority).

  F5/F6 RED POLARITY -- NAMED RESIDUE, not built: s22's own validate_work_item() trigger
  refuses (at the write boundary, by an EXISTENCE check on `work_opened` for the claimed/closed
  slug) any work_claimed/work_closed row for a slug with no PRE-EXISTING work_opened row -- so a
  live write can never produce a work_claimed/work_closed row that precedes its own work_opened
  row in id order; F5/F6's violation is PROVABLY VACUOUS under normal operation, the SAME class
  engine/lp/work_items.lp's own work_duplicate_open/work_shipped_without_witness members already
  are (that program's own header names this precedent). UNEXERCISED via live DB (the concrete
  blocker: s22's own write-time trigger); GREEN is witnessed live in this file's own GREEN world
  (work_opened id < work_claimed id < work_closed id, the ordinary, only-reachable shape).

SEAM UNDECIDABLE WITNESSES: `untokened_row` is witnessed live in the RED world (F7's review row,
written with NO stamp_invocation token -- `SET app.vendor_invocation` simply omitted for that one
insert). `open_window` and `capability_absent`/`no_verify_journal` are witnessed from the REAL
historical corpus, not synthesized: run11 (`/home/bork/w/vdc/1/run11`, read-only, dust) predates
hooks/posttooluse_bash_completion.py (E5) entirely, so EVERY tokened row in that real world lacks
an invocation_completed record -- F7/F9/F10 all come back open_window there (witnessed by
`preamble_differential.py --root /home/bork/w/vdc/1/run11`, AGREE, this same commission), and F2
comes back no_verify_journal (run11 predates E6 entirely). `window_overlap` is witnessed live
here too (the RED world's own SECOND commission row, id6 -- see above). VACUOUS is witnessed
from the real corpus: run9
(`/home/bork/w/vdc/1/run9`, read-only, dust) is a freshly-scaffolded, fully s23-wired world with
ZERO ledger rows -- all twelve family verdicts come back `vacuous`, none silent (the exact
witness plan's own ask: "an empty-but-wired world emitting twelve family verdicts, none silent").

DIFFERENTIAL: both worlds are run through the REAL `engine/preamble_differential.py` subprocess
path (--retain), proving AGREE on real-shaped fixture data; a THIRD invocation reuses the GREEN
world with a manufactured `sql_atoms_override` (the SAME negative-control seam
engine/tests/test_ledger_marriage.py::test_single_producer_mutation_is_diverge_defect and
seen-red/contemporaneity-audit's own cases (p)/(q) already precedent) to prove DIVERGE_DEFECT is
actually caught, never touching either producer's real source to fake it.

Scratch-only: schemas preambleorder/preambleorder_kernel (role preambleorder_rw) and
preambleorderneg/preambleorderneg_kernel (role preambleorderneg_rw), TOY db (192.168.122.1) --
both torn down after a clean run, left standing on a failure (the standing probe pattern). Lazy
imports banned."""
from __future__ import annotations

import datetime
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)


PGHOST, DB = fixture_pghost(), "toy"
SCHEMA_G, KERN_G, ROLE_G = "preambleorder", "preambleorder_kernel", "preambleorder_rw"
SCHEMA_R, KERN_R, ROLE_R = "preambleorderneg", "preambleorderneg_kernel", "preambleorderneg_rw"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LINEAGE = REPO / "kernel" / "lineage"
ENGINE = REPO / "engine"

# volatile substrings that differ run-to-run but carry no evidentiary content: scratch tmpdirs,
# derivation-record timestamp/hash stamps, and the worktree-vs-main-checkout path prefix ahead of
# the retained derivation path.
_VOLATILE_RES = (
    re.compile(r"/tmp/[\w.-]+"),
    re.compile(r"\d{8}T\d{6}Z_[0-9a-f]+"),
    re.compile(r"^.*?(?=engine/docs/ledger-marriage/)", re.MULTILINE),
)


def _normalize(text: str) -> str:
    for rx in _VOLATILE_RES:
        text = rx.sub("<VOLATILE>", text)
    return text


def _bank(path: Path, content: str) -> None:
    """Write CONTENT to PATH as banked seen-red evidence -- but only if it differs from what is
    already there beyond ordinary run-to-run churn (see _VOLATILE_RES). Left unconditional, this
    write dirtied the tree on every fixture run even when nothing substantive changed (11 tracked
    witness files, timestamp/run-id-only diffs, found in the 2026-07 release-audit sweep) --
    running a check should not dirty the tree it checks. A genuine content change (a real
    verdict/count/text difference) still writes through, so the file stays honest evidence rather
    than a stub frozen out of date."""
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing is not None and _normalize(existing) == _normalize(content):
        return
    path.write_text(content, encoding="utf-8")

BASE = 2100000000  # synthetic epoch-seconds anchor (year ~2036) -- distinct from
                    # seen-red/contemporaneity-audit's own BASE=2000000000, so the two fixture
                    # suites' banked artifacts are never confusable by timestamp alone.
LINEAGE_CHAIN = ("high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
                 "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
                 "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
                 "s25-commission-kind.sql")


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


def setup_schema(schema: str, kern: str, role: str) -> tuple[bool, str]:
    teardown(schema, kern, role)
    for f in LINEAGE_CHAIN:
        ok, out = apply_ddl(f, schema, kern, role)
        if not ok:
            return False, f"{f}: {out[-800:]}"
    provision_stamp_secret(kern)
    # A SECOND principal ('reviewer') -- s15's own set_actor trigger resolves `actor` from
    # `current_user` when the write doesn't supply one explicitly, which would make every row in
    # THIS single-role scratch schema the SAME author -- and s15's own validate_review() trigger
    # REFUSES a review row whose actor equals the row it regards' own author ("segregation of
    # duties"). Real projects avoid this via bootstrap/new-project.sh's own identical
    # registration (mirrored here, same name/agent_class) + `LED_ACTOR=reviewer`; this fixture's
    # own `ins_row(..., actor_principal="reviewer")` supplies `actor` explicitly in the INSERT
    # instead (the trigger only fills a NULL actor, never overrides one already supplied).
    ok, out = psql(f"INSERT INTO {kern}.principal (name, agent_class) VALUES "
                   f"('reviewer','subagent') ON CONFLICT (name) DO NOTHING;")
    if not ok:
        return False, f"reviewer principal registration: {out[-500:]}"
    return True, "ok"


def ins_row(schema: str, role: str, kern: str, kind: str, token: str | None, epoch_s: float, *,
           statement: str = "fixture row", refs: str | None = None,
           work_slug: str | None = None, work_title: str | None = None,
           work_resolution: str | None = None, work_witness: str | None = None,
           work_depends_on: str | None = None, regards: int | None = None,
           actor_principal: str | None = None) -> tuple[bool, str]:
    """One fixture ledger row -- extends seen-red/contemporaneity-audit's own `ins_row` with the
    s22 work_* columns, `refs`, `regards`, and an explicit `actor_principal` (see setup_schema's
    own comment for why a review row needs one) this Part 3 domain needs. `to_timestamp(...)` /
    literal SQL values throughout -- no untrusted input crosses this boundary (this module's own
    synthetic BASE-relative data only)."""
    tok_sql = f"SET app.vendor_invocation='{token}';" if token else ""
    cols, vals = ["kind", "statement", "ts"], [f"'{kind}'", f"'{statement}'", f"to_timestamp({epoch_s})"]
    if actor_principal is not None:
        cols.append("actor")
        vals.append(f"(SELECT id FROM {kern}.principal WHERE name='{actor_principal}')")
    if refs is not None:
        cols.append("refs"); vals.append(f"'{refs}'")
    if work_slug is not None:
        cols.append("work_slug"); vals.append(f"'{work_slug}'")
    if work_title is not None:
        cols.append("work_title"); vals.append(f"'{work_title}'")
    if work_resolution is not None:
        cols.append("work_resolution"); vals.append(f"'{work_resolution}'")
    if work_witness is not None:
        cols.append("work_witness"); vals.append(f"'{work_witness}'")
    if work_depends_on is not None:
        cols.append("work_depends_on"); vals.append(f"'{work_depends_on}'")
    if regards is not None:
        cols.append("regards"); vals.append(str(regards))
    return psql(f"SET ROLE {role}; {tok_sql} "
               f"INSERT INTO {schema}.ledger({', '.join(cols)}) VALUES ({', '.join(vals)});")


def _iso_z(epoch_s: float) -> str:
    return (datetime.datetime.fromtimestamp(epoch_s, tz=datetime.timezone.utc)
           .isoformat(timespec="milliseconds").replace("+00:00", "Z"))


def _make_world(schema: str, kern: str, role: str, name: str,
                records: dict[str, list[dict]]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="preamble-fixture-"))
    logs = root / ".claude" / "logs"
    logs.mkdir(parents=True)
    (root / "deployment.json").write_text(json.dumps(
        {"db": DB, "host": PGHOST, "schema": schema, "kern": kern, "role": role, "name": name}))
    for fname, recs in records.items():
        with open(logs / fname, "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r) + "\n")
    return root


def run_preamble_differential(root: Path, retain: bool = False,
                              extra: list[str] | None = None) -> tuple[int, str]:
    env = dict(os.environ)
    env.pop("LEDGER_DEPLOYMENT", None)
    args = [sys.executable, str(ENGINE / "preamble_differential.py"), "--root", str(root)]
    if retain:
        args.append("--retain")
    args += extra or []
    cp = subprocess.run(args, capture_output=True, text=True, env=env, cwd=str(ENGINE))
    return cp.returncode, cp.stdout + cp.stderr


def _family_verdict_present(report: str, fam: str, want: str) -> bool:
    """Match engine/preamble_audit.py's own `print_report` line shape exactly (`F1 (preamble pt
    10): DISCHARGED ...`) -- a plain substring check on `f"{fam}: {want}"` misses the `(preamble
    pt N)` clause between the family and its verdict."""
    return re.search(rf"^  {fam.upper()} \(preamble pt \d+\): {want}\b", report, re.MULTILINE) is not None


def run_preamble_report(root: Path) -> tuple[int, str]:
    env = dict(os.environ)
    env.pop("LEDGER_DEPLOYMENT", None)
    cp = subprocess.run([sys.executable, str(ENGINE / "contemp_audit.py"), "--root", str(root),
                         "--preamble"], capture_output=True, text=True, env=env, cwd=str(ENGINE))
    return cp.returncode, cp.stdout + cp.stderr


def main() -> int:
    fails: list[str] = []
    ck = lambda cond, msg: fails.append(msg) if not cond else None  # noqa: E731
    log: list[str] = []
    worlds: list[Path] = []

    ok, msg = setup_schema(SCHEMA_G, KERN_G, ROLE_G)
    if not ok:
        print(f"# PREAMBLE FIXTURE SETUP FAILED (green schema): {msg}")
        return 1
    log.append(f"setup: GREEN schema {DB}.{SCHEMA_G}/{KERN_G} (role {ROLE_G}) -- full lineage through s25")

    ok, msg = setup_schema(SCHEMA_R, KERN_R, ROLE_R)
    if not ok:
        print(f"# PREAMBLE FIXTURE SETUP FAILED (red schema): {msg}")
        teardown(SCHEMA_G, KERN_G, ROLE_G)
        return 1
    log.append(f"setup: RED schema {DB}.{SCHEMA_R}/{KERN_R} (role {ROLE_R}) -- full lineage through s25")

    green_out = red_out = green_report = red_report = diverge_out = ""
    try:
        # ============================================================================
        # GREEN WORLD -- see module docstring for the full narrative + timing rationale.
        # ============================================================================
        g = BASE
        ok, out = ins_row(SCHEMA_G, ROLE_G, KERN_G, "commission", "g-t1", g + 0,
                          statement="Ship the Part 3 preamble-ordering program.")
        ck(ok, f"green id1 (commission) insert failed: {out}")
        ok, out = ins_row(SCHEMA_G, ROLE_G, KERN_G, "finding", "g-t2", g + 5,
                          statement="Acceptance: every family F1-F12 gets a verdict, never silence.")
        ck(ok, f"green id2 (finding/criteria) insert failed: {out}")
        ok, out = ins_row(SCHEMA_G, ROLE_G, KERN_G, "verification", "g-t3", g + 10,
                          statement="Criteria met.", refs="row:2")
        ck(ok, f"green id3 (verification) insert failed: {out}")
        ok, out = ins_row(SCHEMA_G, ROLE_G, KERN_G, "work_opened", "g-t4", g + 20,
                          statement="Decompose F1-F12.", refs="row:1",
                          work_slug="alpha", work_title="F1-F12 program")
        ck(ok, f"green id4 (work_opened) insert failed: {out}")
        ok, out = ins_row(SCHEMA_G, ROLE_G, KERN_G, "work_claimed", "g-t5", g + 25,
                          statement="Claiming alpha.", work_slug="alpha")
        ck(ok, f"green id5 (work_claimed) insert failed: {out}")
        ok, out = ins_row(SCHEMA_G, ROLE_G, KERN_G, "decision", "g-t6", g + 30,
                          statement="delegating a review pass; rejected: self-review because SoD")
        ck(ok, f"green id6 (decision, pre-dispatch) insert failed: {out}")
        ok, out = ins_row(SCHEMA_G, ROLE_G, KERN_G, "review", "g-t7", g + 40,
                          statement="Countersigned.", regards=4, actor_principal="reviewer")
        ck(ok, f"green id7 (review) insert failed: {out}")
        ok, out = ins_row(SCHEMA_G, ROLE_G, KERN_G, "work_closed", "g-t8", g + 50,
                          statement="Shipped alpha.", work_slug="alpha",
                          work_resolution="shipped", work_witness="commit abc123")
        ck(ok, f"green id8 (work_closed) insert failed: {out}")
        ok, out = ins_row(SCHEMA_G, ROLE_G, KERN_G, "decision", "g-t9", g + 60,
                          statement="stopping: commission fulfilled; stands: alpha shipped; remains: none")
        ck(ok, f"green id9 (decision, stop disposition) insert failed: {out}")

        green_records = {
            # NEW-SCHEMA journals (2026-07-14, design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md sec-6.1):
            # a completion line carries `tool_use_id`, never a stored `token` -- pairing is the
            # consumers' read-time join (dispatch tool_use_id -> token). The bare-`token`
            # completion shape this fixture previously synthesized was a shape production never
            # actually produced (the stored pairing never once fired, per the RCA).
            "invocations.jsonl": [
                {"token": f"g-t{i}", "wall_clock": _iso_z(g + off - 2), "session_id": "fixture",
                 "command_sha256": "x", "command_head": "led", "tool_use_id": f"toolu-g-{i}"}
                for i, off in ((1, 0), (2, 5), (3, 10), (4, 20), (5, 25), (6, 30), (7, 40), (8, 50), (9, 60))
            ],
            "bash_completions.jsonl": [
                {"tool_use_id": f"toolu-g-{i}", "ts": _iso_z(g + off + 1)}
                for i, off in ((1, 0), (2, 5), (3, 10), (4, 20), (5, 25), (6, 30), (7, 40), (8, 50), (9, 60))
            ],
            "mutation_observer.journal.jsonl": [{"ts": _iso_z(g + 70)}],
            "delegation_observer.journal.jsonl": [
                {"ts": _iso_z(g + 35), "session_id": "fixture", "tool": "Agent",
                 "description": "review pass", "prompt_sha256": "y"},
                {"ts": _iso_z(g + 42), "session_id": "fixture", "tool": "Agent", "kind": "return",
                 "dispatch_ts": _iso_z(g + 35)},
            ],
            "stop_clean_exit.journal.jsonl": [{"ts": _iso_z(g + 100), "outcome": "clean_allow"}],
            "verify_commission.jsonl": [{"ts": _iso_z(g + 10), "verdict": "VERIFIED"}],
        }
        groot = _make_world(SCHEMA_G, KERN_G, ROLE_G, "preambleorder", green_records)
        worlds.append(groot)
        rc, green_report = run_preamble_report(groot)
        for fam, want in (("f1", "DISCHARGED"), ("f2", "DISCHARGED"), ("f3", "DISCHARGED"),
                          ("f4", "DISCHARGED"), ("f5", "DISCHARGED"), ("f6", "DISCHARGED"),
                          ("f7", "DISCHARGED"), ("f8", "DISCHARGED"), ("f9", "DISCHARGED"),
                          ("f10", "DISCHARGED"), ("f11", "UNDECIDABLE"), ("f12", "DISCHARGED")):
            ck(_family_verdict_present(green_report, fam, want),
              f"GREEN world: expected {fam.upper()}: {want} in report, not found:\n{green_report}")
        diff_rc, green_out = run_preamble_differential(groot, retain=True)
        ck(diff_rc == 0, f"GREEN differential expected exit 0 (AGREE): got {diff_rc}\n{green_out}")
        ck("AGREE" in green_out, f"GREEN differential expected AGREE: {green_out}")

        # ============================================================================
        # RED WORLD -- see module docstring for the full narrative.
        # ============================================================================
        r = BASE
        # id1: 'assumption', NOT 'decision' -- deliberately NOT a kind F9 would otherwise treat
        # as a candidate preceding decision (F9's own trigger/discharge shape keys on kind=
        # 'decision' specifically; using 'decision' here would accidentally DISCHARGE the F9
        # dispatch below via an unrelated, far-earlier row -- named, not merely avoided by luck).
        ok, out = ins_row(SCHEMA_R, ROLE_R, KERN_R, "assumption", "r-t1", r + 0,
                          statement="oops -- no commission row filed first")
        ck(ok, f"red id1 (assumption, wrongly-first non-commission row) insert failed: {out}")
        ok, out = ins_row(SCHEMA_R, ROLE_R, KERN_R, "commission", "r-t2", r + 5,
                          statement="The real ask, filed late.")
        ck(ok, f"red id2 (commission, late) insert failed: {out}")
        ok, out = ins_row(SCHEMA_R, ROLE_R, KERN_R, "work_opened", "r-t3", r + 10,
                          statement="Decompose (no refs).", work_slug="beta", work_title="beta item")
        ck(ok, f"red id3 (work_opened, no refs) insert failed: {out}")
        # id4: verification row whose refs target (id2, the commission row) will land AFTER the
        # mutation event below (r+2) -- F8 VIOLATED (the criteria row is NOT before the first
        # mutation; id2's own completion lands at r+6, after the mutation at r+2).
        ok, out = ins_row(SCHEMA_R, ROLE_R, KERN_R, "verification", "r-t4", r + 15,
                          statement="Criteria check.", refs="row:2")
        ck(ok, f"red id4 (verification) insert failed: {out}")
        # id5: the UNTOKENED review row -- the untokened_row seam witness for F7.
        ok, out = ins_row(SCHEMA_R, ROLE_R, KERN_R, "review", None, r + 60,
                          statement="Untokened review.", regards=3, actor_principal="reviewer")
        ck(ok, f"red id5 (review, untokened) insert failed: {out}")
        # id6: a SECOND commission row whose OWN sole verify_commission_event lands INSIDE its own
        # invocation window -- the window_overlap seam witness for F2 (an INSTANCE-level atom;
        # F2's family verdict stays VIOLATED regardless, since id2 alone already carries it --
        # violated always outranks undecidable, spec §5's own priority).
        ok, out = ins_row(SCHEMA_R, ROLE_R, KERN_R, "commission", "r-t6", r + 120,
                          statement="Second ask, for the window_overlap seam witness only.")
        ck(ok, f"red id6 (commission, overlap seam) insert failed: {out}")
        # id7: work_closed(shipped) with NO witness -- s22's own write-time CHECK constraint
        # (work_shipped_requires_witness) refuses this at the write boundary; witnessed refusing,
        # not silently skipped -- see the log line below for why F11's VIOLATED witness instead
        # uses the dangling-dependency member (genuinely reachable, s22 does not refuse it).
        ok, out = ins_row(SCHEMA_R, ROLE_R, KERN_R, "work_closed", "r-t7", r + 130,
                          statement="Shipped beta (no witness).", work_slug="beta",
                          work_resolution="shipped")
        ck(not ok, "red id7 (work_closed shipped, NO witness) expected to be REFUSED by s22's "
                  "own CHECK constraint (work_shipped_requires_witness) -- if it succeeded, the "
                  "kernel's own write-time guard regressed")
        log.append("red id7: s22's write-time CHECK correctly refused a shipped-without-witness "
                  "insert -- the SAME defense-in-depth this build's F11 s22_violation arm exists "
                  "to catch when the write boundary is bypassed; witnessed refusing here, so this "
                  "fixture instead asserts F11 VIOLATED via the DANGLING-DEPENDENCY member "
                  "(work_depends_on_unknown), genuinely reachable at write time (s22 does not "
                  "refuse a dangling antecedent -- that program's own header names this).")
        ok, out = ins_row(SCHEMA_R, ROLE_R, KERN_R, "work_depends_on", "r-t7b", r + 130,
                          statement="beta depends on an unknown item.", work_slug="beta",
                          work_depends_on="never-opened-slug")
        ck(ok, f"red id7b (work_depends_on, dangling) insert failed: {out}")

        red_records = {
            # NEW-SCHEMA journals, same correction as green_records above (RCA sec-6.1).
            "invocations.jsonl": [
                {"token": f"r-t{i}", "wall_clock": _iso_z(r + off - 2), "session_id": "fixture",
                 "command_sha256": "x", "command_head": "led", "tool_use_id": f"toolu-r-{i}"}
                for i, off in ((1, 0), (2, 5), (3, 10), (4, 15), (6, 120), (7, 130), ("7b", 130))
            ],
            "bash_completions.jsonl": [
                {"tool_use_id": f"toolu-r-{i}", "ts": _iso_z(r + off + 1)}
                for i, off in ((1, 0), (2, 5), (3, 10), (4, 15), (6, 120), (7, 130), ("7b", 130))
            ],
            # BEFORE id3's own work_opened completion (r+11) and id2's own commission completion
            # (r+6) alike -- F4 VIOLATED (no decomposition before it) and F8 VIOLATED (the
            # criteria row, id2, is not before it either) in ONE stroke.
            "mutation_observer.journal.jsonl": [{"ts": _iso_z(r + 2)}],
            # ONE dispatch, with NO decision-kind row anywhere in this schema at all (id1 is
            # 'assumption', not 'decision') -- F9 VIOLATED, trivially and unambiguously.
            "delegation_observer.journal.jsonl": [
                {"ts": _iso_z(r + 150), "session_id": "fixture", "tool": "Agent",
                 "description": "dispatch with no preceding decision row at all", "prompt_sha256": "z"},
            ],
            # Same reasoning as the dispatch above -- no decision-kind row exists near the stop
            # either -- F10 VIOLATED, trivially and unambiguously.
            "stop_clean_exit.journal.jsonl": [{"ts": _iso_z(r + 300), "outcome": "clean_allow"}],
            "verify_commission.jsonl": [
                # id2's own event, mistimed (lands AFTER work_opened id3's own Lo=r+8) -- F2
                # VIOLATED (capable, tokened, resolved, simply the wrong order).
                {"ts": _iso_z(r + 50), "verdict": "VERIFIED"},
                # id6's own event, landing INSIDE id6's own [Lo=118,Hi=121] window -- the
                # window_overlap seam witness (see id6's own comment above).
                {"ts": _iso_z(r + 119), "verdict": "UNSIGNED"},
            ],
        }
        rroot = _make_world(SCHEMA_R, KERN_R, ROLE_R, "preambleorderneg", red_records)
        worlds.append(rroot)
        rc, red_report = run_preamble_report(rroot)
        for fam, want in (("f1", "VIOLATED"), ("f2", "VIOLATED"), ("f3", "VIOLATED"),
                          ("f4", "VIOLATED"), ("f7", "UNDECIDABLE"), ("f8", "VIOLATED"),
                          ("f9", "VIOLATED"), ("f10", "VIOLATED"), ("f11", "VIOLATED")):
            ck(_family_verdict_present(red_report, fam, want),
              f"RED world: expected {fam.upper()}: {want} in report, not found:\n{red_report}")
        ck("untokened_row" in red_report, "RED world: expected untokened_row seam reason for F7")
        ck("window_overlap" in red_report, "RED world: expected window_overlap seam reason for F2's id6 instance")
        diff_rc, red_out = run_preamble_differential(rroot, retain=True)
        ck(diff_rc == 0, f"RED differential expected exit 0 (AGREE -- the WORLD is red, the "
                        f"DIFFERENTIAL over it is still bit-identical, GREEN): got {diff_rc}\n{red_out}")
        ck("AGREE" in red_out, f"RED differential expected AGREE: {red_out}")

        # ============================================================================
        # NEGATIVE CONTROL -- manufactured DIVERGE_DEFECT (the GREEN world, one forged atom in
        # the SQL floor's own returned set, in an ISOLATED subprocess -- never touching either
        # producer's real source, the seen-red/contemporaneity-audit cases (p)/(q) precedent).
        # ============================================================================
        script = f'''\
import os
import sys
sys.path.insert(0, {str(ENGINE)!r})
from pathlib import Path
os.environ["LEDGER_DEPLOYMENT"] = {str(groot / "deployment.json")!r}
import preamble_differential as pd
res = pd.run_differential("preambleorder", Path({str(groot)!r}),
                          sql_atoms_override={{"preamble_verdict(f1,FORGED)"}})
pd.print_result(res)
print()
print("VERDICT:", res.verdict())
sys.exit(0 if res.verdict() == "AGREE" else 1)
'''
        script_path = Path(tempfile.mktemp(suffix=".py"))
        script_path.write_text(script, encoding="utf-8")
        try:
            env = dict(os.environ); env.pop("LEDGER_DEPLOYMENT", None)
            cp = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True,
                                env=env, cwd=str(ENGINE))
            diverge_out = cp.stdout + cp.stderr
            ck(cp.returncode == 1, f"negative control expected exit 1 (DIVERGE_DEFECT): got {cp.returncode}\n{diverge_out}")
            ck("DIVERGE_DEFECT" in diverge_out, f"negative control expected DIVERGE_DEFECT: {diverge_out}")
        finally:
            script_path.unlink(missing_ok=True)

    finally:
        for w in worlds:
            try:
                shutil.rmtree(w, ignore_errors=True)
            except Exception:  # noqa: BLE001
                pass

    _bank(HERE / "green-report.txt", green_report)
    _bank(HERE / "red-report.txt", red_report)
    _bank(HERE / "differential-agree-green.txt", green_out)
    _bank(HERE / "differential-agree-red.txt", red_out)
    _bank(HERE / "differential-diverge-defect.txt", diverge_out)

    if fails:
        print("# PREAMBLE-ORDERING FIXTURES: FAILED")
        for f in fails:
            print(f"  [FAIL] {f}")
        print("\n(scratch schemas left standing for inspection: "
             f"{SCHEMA_G}/{KERN_G}, {SCHEMA_R}/{KERN_R})")
        return 1

    teardown(SCHEMA_G, KERN_G, ROLE_G)
    teardown(SCHEMA_R, KERN_R, ROLE_R)
    print("# PREAMBLE-ORDERING FIXTURES: ALL GREEN")
    for line in log:
        print(f"  {line}")
    print(f"  banked: {HERE}/green-report.txt, red-report.txt, "
         f"differential-agree-{{green,red}}.txt, differential-diverge-defect.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
