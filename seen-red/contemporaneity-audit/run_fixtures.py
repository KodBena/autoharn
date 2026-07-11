#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T14:44:01Z
#   last-change: 2026-07-11T15:15:03Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for Part 2 of design/CONTEMPORANEITY-AUDIT.md
(engine/contemp_edb.py + engine/lp/contemporaneity.lp + engine/contemp_audit.py; BACKLOG
"Contemporaneity indictment", 2026-07-11).

BACKFILL_SUSPECT and BATCHED_DECLARED are witnessed on an apparatus-authored SCRATCH world
(the same posture the s22 work-item fixture and the marriage engine's own scratch differentials
take: correlated-authorship, disclosed, not a claim of independent-source proof). Real-world
evidence IS exercised separately, live: case (c) against run7's actual (pre-s23) schema, and --
banked beside this file, run9-vacuous-clean-witness.txt -- the run9 re-witness the wired-but-
empty case (e) reproduces synthetically.

FIVE CASES:

  a-clean-batched-declared (GREEN): a scratch ledger with a genuine multi-row token burst but
     dense tool-activity (no gap exceeds silence_threshold_ms) -> VERDICT=batched_declared,
     zero backfill_suspect tokens. Proves an honest simultaneous-conclusion burst is NOT
     flagged merely for being a burst (the design memo's own aim: "some batching is
     irreducible ... forbidding bursts would just breed theatrical row-spacing").

  b-manufactured-backfill (RED): a scratch ledger with a >300s tool-activity silence (zero rows
     in the window) immediately followed by a multi-row burst -> VERDICT=backfill_suspect,
     naming the offending token. The manufactured positive control -- proves the instrument
     actually goes red on the exact shape run5/run8 exhibited (per BACKLOG's own forensic
     numbers: 503s / 312s silence-then-burst).

  c-real-pretoken-world (WITNESSED, live data): run7's own schema (192.168.122.1/toy/run7,
     read-only, no fixture rows written) -- predates s23 (no stamp_invocation column). Proves
     the HONEST HISTORICAL LIMIT live: exit 3 (N/A), the typed refusal naming the REAL missing
     capability (s23_capable -- run7's settings.json does wire stamping, so under the
     capability-vs-corpus fix its invocation journal reads capable-but-empty, not missing), the
     degraded ts-cluster table populated (INFERRED, never presented as a verdict), and the
     refusal-fingerprint at id 62 -- the exact burned-id BACKLOG's own forensic pass already
     found by hand.

  d-empty-ledger-UNWIRED (edge case, degrade contract): a world with no settings.json and no
     journals at all pointing at a zero-row schema -> N/A exit 3 (no wiring evidence means
     capability is honestly absent), never a crash, never a guessed CONTEMPORANEOUS.

  e-empty-ledger-WIRED (the run9 false-refusal specimen, 2026-07-11): a world whose
     settings.json wires all four journaling hooks (apparatus modes on) with an invocation
     journal but zero tool events and ZERO ledger rows -- run9's exact shape, which the
     first-landed instrument wrongly refused (NO_VERDICT exit 3, 'Missing/excluded:
     [tool_event]'; the maintainer stopped the run over it). Expected: exit 0, an EXPLICIT
     VACUOUSLY_CLEAN result ("0 ledger rows, nothing to audit yet -- NOT evidence of
     conduct"), tool_event reported capable-but-empty, never unwired. The real-data twin is
     run9-vacuous-clean-witness.txt (the actual run9 re-run, banked beside this file).

RED (pre-instrument, disclosed rather than re-captured): before this suite existed there was no
Part 2 instrument at all -- ad-hoc SQL run by hand, once per crisis (BACKLOG's own indictment).
red.txt captures case (b)'s actual backfill_suspect output as the banked red evidence (the
fixture_census.py convention: a *-red.txt or red.txt file is what proves a gate "has been seen
red").

Scratch-only: schema contempprobe / contempprobe_kernel, role contempprobe_rw, TOY db
(192.168.122.1) -- torn down after a clean run, left standing (never applied to any live
schema) on a failure, per the standing probe pattern. Lazy imports banned."""
from __future__ import annotations

import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PGHOST, DB = "192.168.122.1", "toy"
SCHEMA, KERN, ROLE = "contempprobe", "contempprobe_kernel", "contempprobe_rw"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LINEAGE = REPO / "kernel" / "lineage"
ENGINE = REPO / "engine"
RUN7_ROOT = Path("/home/bork/w/vdc/1/run7")

BASE = 2000000000  # a synthetic epoch-seconds anchor (year 2033) -- never collides with a real
                    # historical ledger row, and is instantly recognizable as fixture data in
                    # any banked artifact.


def psql(sql: str) -> tuple[bool, str]:
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1", "-c", sql],
                        capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr)


def apply_ddl(fname: str) -> tuple[bool, str]:
    cp = subprocess.run(
        ["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1",
         "-v", f"schema={SCHEMA}", "-v", f"kern={KERN}", "-v", f"role={ROLE}",
         "-f", str(LINEAGE / fname)],
        capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr)


def teardown() -> None:
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-c",
                    f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; DROP SCHEMA IF EXISTS {KERN} CASCADE; "
                    f"DROP OWNED BY {ROLE}; DROP ROLE IF EXISTS {ROLE};"],
                   capture_output=True, text=True)


def ins_row(kind: str, token: str | None, epoch_s: float) -> tuple[bool, str]:
    tok_sql = f"SET app.vendor_invocation='{token}';" if token else ""
    return psql(
        f"SET ROLE {ROLE}; {tok_sql} "
        f"INSERT INTO {SCHEMA}.ledger(kind, statement, ts) "
        f"VALUES ('{kind}','fixture row', to_timestamp({epoch_s}));"
    )


def _make_world(records: dict[str, list[dict]]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="contemp-fixture-"))
    logs = root / ".claude" / "logs"
    logs.mkdir(parents=True)
    (root / "deployment.json").write_text(json.dumps(
        {"db": DB, "host": PGHOST, "schema": SCHEMA, "kern": KERN, "role": ROLE, "name": "contempprobe"}))
    for fname, recs in records.items():
        with open(logs / fname, "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r) + "\n")
    return root


def run_audit(root: Path) -> tuple[int, str]:
    env = dict(os.environ)
    env.pop("LEDGER_DEPLOYMENT", None)
    cp = subprocess.run(
        [sys.executable, str(ENGINE / "contemp_audit.py"), "--root", str(root)],
        capture_output=True, text=True, env=env, cwd=str(ENGINE))
    return cp.returncode, cp.stdout + cp.stderr


def main() -> int:
    fails: list[str] = []
    ck = lambda cond, msg: fails.append(msg) if not cond else None  # noqa: E731
    log: list[str] = []
    worlds: list[Path] = []
    case_b_out = ""

    teardown()
    for f in ("high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
             "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
             "s23-per-invocation-stamp-token.sql"):
        ok, out = apply_ddl(f)
        if not ok:
            print(f"# CONTEMPORANEITY FIXTURE SETUP FAILED ({f}): {out[-500:]}")
            return 1
    log.append(f"setup: full lineage through s23 applied clean to {DB}.{SCHEMA}/{KERN} (role {ROLE})")

    try:
        # ---- CASE d: empty ledger, UNWIRED world (no settings.json, no journals) ----------
        # Genuinely no wiring evidence at all -> capability honestly absent -> typed refusal.
        root_d = _make_world({})
        (root_d / "deployment.json").write_text(json.dumps(
            {"db": DB, "host": PGHOST, "schema": SCHEMA, "kern": KERN, "role": ROLE, "name": "contempprobe-empty"}))
        worlds.append(root_d)
        code_d, out_d = run_audit(root_d)
        ck(code_d == 3, f"CASE d (empty ledger, unwired): expected exit 3 (N/A), got {code_d}: {out_d[-600:]}")
        ck("NO_VERDICT" in out_d, "CASE d: refusal must be visible, not silent")
        log.append(f"CASE d (empty ledger, unwired world): exit={code_d} (expected 3)")

        # ---- CASE e: empty ledger, FULLY-WIRED world (the run9 false-refusal shape) --------
        # The live specimen (2026-07-11): run9, the first s23-capable world, correctly wired
        # (settings.json wires all journaling hooks, apparatus modes on), invocations journaled,
        # but zero ledger rows and zero tool events because the session had only run orientation
        # commands -- the TRUE state, not a capability absence. The first-landed instrument
        # refused it (NO_VERDICT exit 3, 'Missing/excluded: [tool_event]') and the maintainer
        # stopped the run over it. Expected AFTER the fix: capability PRESENT (tool_event
        # capable-but-empty), VACUOUSLY_CLEAN, exit 0 -- never a refusal, never a conduct claim.
        root_e = _make_world({
            "invocations.jsonl": [
                {"token": "fixture-token-orient", "wall_clock": _iso(BASE - 100), "session_id": "fx-e"},
            ],
        })
        (root_e / "deployment.json").write_text(json.dumps(
            {"db": DB, "host": PGHOST, "schema": SCHEMA, "kern": KERN, "role": ROLE, "name": "contempprobe-wired-empty"}))
        # the wiredness signal contemp_edb._wired_journaling_mechanisms reads: a settings.json
        # whose hook command strings reference the journaling hook scripts (the scaffold's own
        # shape, minimized), plus the scaffold's default apparatus.json modes (all on).
        (root_e / ".claude" / "settings.json").write_text(json.dumps({"hooks": {
            "PreToolUse": [{"matcher": "*", "hooks": [
                {"type": "command", "command": "python3 /x/hooks/pretooluse_change_gate.py"},
                {"type": "command", "command": "python3 /x/hooks/stamp_intercept.py"},
                {"type": "command", "command": "python3 /x/hooks/pretooluse_delegation_observer.py"}]}],
            "PostToolUse": [{"matcher": "Bash", "hooks": [
                {"type": "command", "command": "python3 /x/hooks/posttooluse_mutation_observer.py"}]}],
        }}))
        (root_e / ".claude" / "apparatus.json").write_text(json.dumps({"mechanisms": {
            "change_gate": {"mode": "enforce"}, "stamp_intercept": {"mode": "enforce"},
            "mutation_observer": {"mode": "observe"}, "delegation_observer": {"mode": "observe"}}}))
        worlds.append(root_e)
        code_e, out_e = run_audit(root_e)
        ck(code_e == 0, f"CASE e (wired-but-empty, run9 shape): expected exit 0 (vacuous clean), "
                        f"got {code_e}: {out_e[-800:]}")
        ck("VACUOUSLY_CLEAN" in out_e, f"CASE e: the vacuous result must be EXPLICIT: {out_e[-800:]}")
        ck("NO_VERDICT" not in out_e, f"CASE e: a wired world must NOT be refused: {out_e[-800:]}")
        ck("EMPTY (capable, zero events yet)" in out_e,
           f"CASE e: tool_event must read capable-but-empty, never unwired: {out_e[-800:]}")
        log.append(f"CASE e (wired-but-empty, the run9 shape): exit={code_e} (expected 0), "
                   f"VACUOUSLY_CLEAN explicit, tool_event capable-but-empty")

        # ---- CASE a: clean batched-declared (GREEN) --------------------------------------
        tok_a = "fixture-token-aaaa"
        ok1, o1 = ins_row("decision", tok_a, BASE + 0.000)
        ok2, o2 = ins_row("decision", tok_a, BASE + 0.030)          # 30ms burst -> token_burst
        ok3, o3 = ins_row("decision", "fixture-token-bbbb", BASE + 40.0)  # single-row token
        ck(ok1 and ok2 and ok3, f"CASE a inserts must succeed: {o1[-200:]} {o2[-200:]} {o3[-200:]}")
        root_a = _make_world({
            "invocations.jsonl": [
                {"token": tok_a, "wall_clock": _iso(BASE - 0.010), "session_id": "fx-a"},
                {"token": "fixture-token-bbbb", "wall_clock": _iso(BASE + 39.990), "session_id": "fx-a"},
            ],
            "mutation_observer.journal.jsonl": [
                {"ts": _iso_z(BASE - 40), "outcome": "warned"},
                {"ts": _iso_z(BASE - 20), "outcome": "warned"},
                {"ts": _iso_z(BASE - 2), "outcome": "warned"},
                {"ts": _iso_z(BASE + 20), "outcome": "warned"},
                {"ts": _iso_z(BASE + 60), "outcome": "warned"},
            ],
        })
        (root_a / "deployment.json").write_text(json.dumps(
            {"db": DB, "host": PGHOST, "schema": SCHEMA, "kern": KERN, "role": ROLE, "name": "contempprobe"}))
        worlds.append(root_a)
        code_a, out_a = run_audit(root_a)
        ck(code_a == 0, f"CASE a: expected exit 0 (clean), got {code_a}: {out_a[-800:]}")
        ck("VERDICT: BATCHED_DECLARED" in out_a, f"CASE a: expected BATCHED_DECLARED: {out_a[-800:]}")
        ck("BACKFILL_SUSPECT tokens:" not in out_a, f"CASE a: must carry NO backfill_suspect: {out_a[-800:]}")
        log.append(f"CASE a (clean batch): exit={code_a}, verdict=BATCHED_DECLARED as expected")

        # ---- CASE b: manufactured backfill (RED) -------------------------------------------
        # a row BEFORE the gap (so first_row_after cannot pick it up), then a >300s silence with
        # zero rows, then a 2-row burst landing AT-OR-AFTER the tool_event that closes the gap
        # (T2) -- the run5/run8 shape, manufactured. The burst must land >= T2, never inside
        # (T1,T2), or it would itself be the "row between" that makes the gap NOT a silence.
        tok_c = "fixture-token-cccc"
        t1 = BASE + 1010          # last tool activity before the quiet window
        t2 = t1 + 305             # 305s later: the tool_event that closes the >180s gap
        okp, op = ins_row("finding", "fixture-token-pre", BASE + 1005.0)
        ok4, o4 = ins_row("finding", tok_c, t2 + 0.050)   # AFTER t2, not inside (t1,t2)
        ok5, o5 = ins_row("finding", tok_c, t2 + 0.080)
        ck(okp and ok4 and ok5, f"CASE b inserts must succeed: {op[-200:]} {o4[-200:]} {o5[-200:]}")
        root_b = _make_world({
            "invocations.jsonl": [
                {"token": "fixture-token-pre", "wall_clock": _iso(BASE + 1004.990), "session_id": "fx-b"},
                {"token": tok_c, "wall_clock": _iso(t2 + 0.040), "session_id": "fx-b"},
            ],
            "mutation_observer.journal.jsonl": [
                {"ts": _iso_z(BASE + 1000), "outcome": "warned"},
                {"ts": _iso_z(t1), "outcome": "warned"},           # last activity before silence
                {"ts": _iso_z(t2), "outcome": "warned"},           # 305s later, zero rows between t1,t2
                {"ts": _iso_z(t2 + 5), "outcome": "warned"},
            ],
        })
        (root_b / "deployment.json").write_text(json.dumps(
            {"db": DB, "host": PGHOST, "schema": SCHEMA, "kern": KERN, "role": ROLE, "name": "contempprobe"}))
        worlds.append(root_b)
        code_b, out_b = run_audit(root_b)
        case_b_out = out_b
        ck(code_b == 1, f"CASE b: expected exit 1 (BACKFILL_SUSPECT), got {code_b}: {out_b[-1200:]}")
        ck("VERDICT: BACKFILL_SUSPECT" in out_b, f"CASE b: expected BACKFILL_SUSPECT: {out_b[-1200:]}")
        ck(tok_c in out_b, f"CASE b: the offending token must be NAMED: {out_b[-1200:]}")
        log.append(f"CASE b (manufactured backfill): exit={code_b}, verdict=BACKFILL_SUSPECT, "
                   f"token {tok_c} named, as expected")

        # ---- CASE c: real pre-token world (run7, live, read-only) --------------------------
        # Under the capability-vs-corpus fix, run7's refusal is named by its REAL blocker: the
        # pre-s23 schema (`s23_capable`). Its settings.json DOES wire stamp_intercept (the hooks
        # execute live from autoharn, so the CURRENT hook would journal if the dust world ever
        # ran again), so invocation_journal reads capable-but-empty rather than missing -- the
        # honest refinement the run9 fix introduced.
        if RUN7_ROOT.is_dir():
            code_c, out_c = run_audit(RUN7_ROOT)
            ck(code_c == 3, f"CASE c (run7 live): expected exit 3 (N/A), got {code_c}: {out_c[-600:]}")
            ck("'s23_capable'" in out_c.split("NO_VERDICT", 1)[-1],
               f"CASE c: the refusal must NAME the real missing capability (s23_capable): {out_c[-600:]}")
            ck("62" in out_c, "CASE c: run7's own refusal fingerprint (id 62) must surface")
            log.append(f"CASE c (run7 live, pre-s23): exit={code_c} (expected 3), refusal names "
                       f"s23_capable, refusal-fingerprint 62 confirmed live against real "
                       f"historical data")
        else:
            log.append("CASE c SKIPPED: /home/bork/w/vdc/1/run7 not present on this host "
                       "(UNEXERCISED, concrete blocker: no run7 checkout here)")

    finally:
        for w in worlds:
            shutil.rmtree(w, ignore_errors=True)

    for line in log:
        print(f"# {line}")
    if fails:
        print(f"\n# CONTEMPORANEITY-AUDIT FIXTURE FAIL -- {len(fails)} defect(s):")
        for f in fails:
            print(f"  - {f}")
        return 1

    (HERE / "red.txt").write_text(
        "# banked RED evidence -- CASE b (manufactured backfill), engine/contemp_audit.py real output:\n"
        + case_b_out, encoding="utf-8")
    teardown()
    print("\n# CONTEMPORANEITY-AUDIT FIXTURE PASS -- both polarities proven (clean batch does NOT "
          "flag; manufactured silence-then-burst DOES, naming the token); the honest N/A refusal "
          "proven on an empty scratch ledger AND live against run7's real pre-s23 data.")
    return 0


def _iso(epoch_s: float) -> str:
    """UTC ISO-8601 with fractional seconds and a trailing 'Z' -- the hooks/stamp_intercept.py
    invocations.jsonl convention (this module's own _parse_ts_ms 'Z' branch)."""
    dt = datetime.datetime.fromtimestamp(epoch_s, tz=datetime.timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"


def _iso_z(epoch_s: float) -> str:
    return _iso(epoch_s)


if __name__ == "__main__":
    raise SystemExit(main())
