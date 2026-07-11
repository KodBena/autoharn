#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T14:44:01Z
#   last-change: 2026-07-11T21:32:32Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for Part 2 of design/CONTEMPORANEITY-AUDIT.md
(engine/contemp_edb.py + engine/lp/contemporaneity.lp + engine/contemp_audit.py; BACKLOG
"Contemporaneity indictment", 2026-07-11) EXTENDED for design/LATE-ENTRY-AND-INTAKE-
SEMANTICS.md's two ratified mechanisms (kernel/lineage/s24-declared-event-time.sql; the
LATE_DECLARED verdict + the intake-shape annotation, this same commission, 2026-07-11).

BACKFILL_SUSPECT and BATCHED_DECLARED are witnessed on an apparatus-authored SCRATCH world
(the same posture the s22 work-item fixture and the marriage engine's own scratch differentials
take: correlated-authorship, disclosed, not a claim of independent-source proof). Real-world
evidence IS exercised separately, live: case (c) against run7's actual (pre-s23) schema, and --
banked beside this file, run9-vacuous-clean-witness.txt -- the run9 re-witness the wired-but-
empty case (e) reproduces synthetically. Cases (f)/(g) reproduce, on the same scratch posture,
the two polarities design/LATE-ENTRY-AND-INTAKE-SEMANTICS.md's ratification packet asked for
by name: a declared late entry verdicts LATE_DECLARED (exit 0), the identical undeclared gap
(case (b), unchanged) verdicts BACKFILL_SUSPECT (exit 1). Case (h) reproduces run-10's own
banked intake-burst SHAPE (BACKLOG "Run-10 first audit verdict adjudicated", 2026-07-11) on this
same scratch posture -- never against the live run-10 world itself (runs are linear; a settled
world is read-only evidence, never touched for a fixture). Cases (i)/(j)/(k) exercise
`bootstrap/templates/led.tmpl`'s own `--event-time` flag through a REAL `led` shim invocation
(subprocess, not a hand-built SQL INSERT) -- closing the gap an out-of-frame hack-rationalization
audit of this same commission found: every OTHER case in this file proves the ENGINE layer
(contemp_edb/contemporaneity.lp/contemp_audit) against hand-built fixture rows, but nothing
before these three cases had exercised the CLI path (the live capability check, the two-INSERT-
shape branch, the coverage-guard refusal) end-to-end. Cases (l)/(m) EXTEND that same real-shim
pattern for BACKLOG "Run-10 closure audit (2026-07-11)" item 1 / change proposal 1: the
ledger_kind_check refusal now teaches its own live valid-kind list rather than leaving the agent
to self-diagnose via a hand-run pg_get_constraintdef query (run-10 row 67's own specimen).

FIFTEEN CASES:

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

  f-manufactured-late-declared (GREEN, the DECLARED twin of case (b)): the SAME silence-then-
     burst shape as case (b) -- a >300s tool-activity silence with zero rows, immediately
     broken by a burst -- but the burst's silence-breaking row carries an `event_declared_ts`
     (s24) claiming the event occurred back near the START of the silence window, so the
     write-vs-declared gap comfortably exceeds late_threshold_ms. VERDICT=late_declared,
     naming the token, exit 0 (design/LATE-ENTRY-AND-INTAKE-SEMANTICS.md Proposal 2: "a
     declared late entry satisfies the mandate"). Proves the mechanism distinguishes an
     HONESTLY-DECLARED late entry from case (b)'s UNDECLARED one over the identical gap shape.

  g-manufactured-backfill-undeclared-twin (RED, re-asserts case (b) is unaffected by s24):
     re-runs case (b)'s own exact scenario (no event_declared_ts on the silence-breaking row)
     AFTER s24 has landed on this same schema, confirming BACKFILL_SUSPECT/exit 1 is BYTE-
     IDENTICAL in shape to case (b)'s pre-extension behavior -- the "nothing existing relaxed"
     claim, demonstrated rather than merely asserted.

  h-intake-shape-benign (the run-10 SHAPE, reproduced synthetically -- design/LATE-ENTRY-AND-
     INTAKE-SEMANTICS.md Proposal 1): a multi-row token burst whose every row precedes this
     world's own first tool_event (run-10 rows 2-11: ten present-tense task declarations,
     written before any tool activity existed to narrate). VERDICT=batched_declared, exit 0,
     with the burst annotated `intake-shape (precedes all tool activity)` in the burst table --
     the engine-side-only annotation Proposal 1 specifies, no vocabulary change.

  i-led-event-time-cli-success (GREEN, the CLI twin of case (f)'s SQL-level proof): a real `led`
     shim (the same 3-line exec-wrapper `bootstrap/new-project.sh` writes into every scaffolded
     world) invoked as `./led --event-time <iso> finding "..."` against the s24-capable
     `contempprobe` schema -> exit 0, the row lands with `event_declared_ts` set to the declared
     value, read back via a direct SELECT.

  j-led-event-time-cli-coverage-refusal (RED): the SAME shim invoked as `./led --event-time <iso>
     work open <slug> <title>` -> exit 1, REFUSED, naming that `--event-time` is only supported
     on the generic path today (the coverage guard `led.tmpl` added after the same audit that
     asked for this fixture) -- never a silent drop of the declared value on a verb whose own
     INSERT does not carry the column.

  k-led-event-time-cli-pre-s24-refusal (RED, the CLI twin of the missing-column path): a SECOND
     scratch schema (`contempprobe_pre24`), applied through s23 only (no s24), with its own `led`
     shim -> `./led --event-time <iso> finding "..."` REFUSES, exit 1, naming the missing
     `event_declared_ts` column -- proving the live `information_schema.columns` capability check
     actually fires against a real pre-s24 schema, not merely asserted from the SQL delta's own
     prose.

  l-led-kind-refusal-teach (RED, run-10 row 67's own specimen): the SAME real `led` shim invoked
     as `./led acceptance-criteria "QEUBO smoke-test acceptance criterion..."` -- an invented
     kind, refused by the kernel's ledger_kind_check CHECK constraint exactly as run-10 row 67
     was. Before BACKLOG "Run-10 closure audit (2026-07-11)" item 1's fix, the agent saw only the
     bare "violates check constraint ledger_kind_check" text and had to separately query
     pg_get_constraintdef by hand to learn the valid vocabulary. Expected AFTER the fix: exit 1
     (unchanged -- the refusal itself is correct and stays a refusal), the ORIGINAL kernel error
     still visible unrewrapped, PLUS a live-queried valid-kind list naming decision/assumption/
     work_opened/review (and the invented kind conspicuously absent from that list).

  m-led-kind-refusal-teach-success-unaffected (GREEN, the byte-identical-to-before proof): a
     VALID kind (`decision`) written through TWO shims -- one pointing at led.tmpl as it stood at
     PRE_KIND_TEACH_FIX_SHA, a PINNED historical commit fixed to immediately before the fix
     landed (`git show <sha>:bootstrap/templates/led.tmpl`, the pre-fix file; pinned rather than
     `HEAD` on purpose -- `HEAD` walks forward past this fix's own commit the moment it lands,
     which would silently turn this into a self-comparison), one at the just-edited current file
     -- proving the fix touches ONLY the failure path: both writes succeed (exit 0) and their
     stdout is compared BYTE-FOR-BYTE, not merely asserted equal to a hardcoded string.

  n-led-show-cli-success (GREEN, small-follow-ups commission item 1): a real `led show <id>`
     shim invocation against a KNOWN-existing row (case i's own inserted row, looked up by its
     unique statement text) -> exit 0, the full untruncated statement text printed (the `-x`
     expanded-display proof: one row, every column, in full).

  o-led-show-cli-missing (RED, the run-11 class-b finding's own fix): the SAME shim invoked as
     `led show 999999999` (an id that certainly does not exist in this scratch schema) -> exit 1,
     REFUSED with teach-text naming the missing id -- proving `show` no longer falls through to
     the generic write path (before the fix: silently absorbed as kind="show", refused by
     ledger_kind_check, burning a sequence id). Also proves NO row of kind='show' was ever
     written (the phantom-burn class this fix forecloses, not merely a refusal that still writes).

RED (pre-instrument, disclosed rather than re-captured): before this suite existed there was no
Part 2 instrument at all -- ad-hoc SQL run by hand, once per crisis (BACKLOG's own indictment).
red.txt captures case (b)'s actual backfill_suspect output as the banked red evidence (the
fixture_census.py convention: a *-red.txt or red.txt file is what proves a gate "has been seen
red"); late-declared-red.txt captures case (g)'s output the same way, and late-declared-
green.txt captures case (f)'s LATE_DECLARED output as the declared-polarity twin.

Scratch-only: schema contempprobe / contempprobe_kernel, role contempprobe_rw (cases a/b/e-j,l,m)
AND contempprobe_pre24 / contempprobe_pre24_kernel / contempprobe_pre24_rw (case k only, s23-only,
no s24), TOY db (192.168.122.1) -- both torn down after a clean run, left standing (never applied
to any live schema) on a failure, per the standing probe pattern. Case (m) also writes one throwaway
temp file holding the pre-fix led.tmpl's own text (read via `git show`, never modified) -- torn
down with its tempdir like every other fixture world. Lazy imports banned."""
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

PGHOST, DB = "192.168.122.1", "toy"
SCHEMA, KERN, ROLE = "contempprobe", "contempprobe_kernel", "contempprobe_rw"
# case (k) only: a SECOND scratch schema, applied through s23 ONLY (no s24), so the led.tmpl
# missing-column refusal path is exercised against a REAL pre-s24 schema, not merely asserted.
SCHEMA_PRE24, KERN_PRE24, ROLE_PRE24 = (
    "contempprobe_pre24", "contempprobe_pre24_kernel", "contempprobe_pre24_rw")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LINEAGE = REPO / "kernel" / "lineage"
ENGINE = REPO / "engine"
LED_TMPL = REPO / "bootstrap" / "templates" / "led.tmpl"
RUN7_ROOT = Path("/home/bork/w/vdc/1/run7")
# case (m)'s "old" comparison target: the commit immediately BEFORE the kind-refusal-teach fix
# (BACKLOG "Run-10 closure audit ... both class-b fixes landed") landed -- pinned to this fixed,
# immutable SHA rather than a moving `HEAD` on purpose. `HEAD` was correct only in the single
# window between editing led.tmpl and committing the fix; once that commit lands, `HEAD` walks
# forward past it and a `HEAD`-relative comparison degrades into comparing the current file
# against itself -- a silently vacuous pass forever after (exactly the class hooks/pre-commit's
# own header warns against, "F49"), never erroring, just no longer proving anything. A fixed
# historical SHA stays a genuine pre-fix specimen indefinitely.
PRE_KIND_TEACH_FIX_SHA = "95622f3"

BASE = 2000000000  # a synthetic epoch-seconds anchor (year 2033) -- never collides with a real
                    # historical ledger row, and is instantly recognizable as fixture data in
                    # any banked artifact.


def psql(sql: str) -> tuple[bool, str]:
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1", "-c", sql],
                        capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr)


def apply_ddl(fname: str, schema: str = SCHEMA, kern: str = KERN, role: str = ROLE) -> tuple[bool, str]:
    cp = subprocess.run(
        ["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1",
         "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}",
         "-f", str(LINEAGE / fname)],
        capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr)


def teardown(schema: str = SCHEMA, kern: str = KERN, role: str = ROLE) -> None:
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-c",
                    f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE; "
                    f"DROP OWNED BY {role}; DROP ROLE IF EXISTS {role};"],
                   capture_output=True, text=True)


def provision_stamp_secret(kern: str) -> None:
    """Seed the stamp secret for a scratch kernel schema (mirrors bootstrap/new-project.sh's own
    idempotent seeding block) -- needed so a `led` shim invocation against this schema does not
    fail on an UNRELATED grounds (no secret provisioned) when cases (i)/(j)/(k) below only care
    about the --event-time coverage/capability paths, not stamp verification."""
    hex_secret = secrets.token_hex(32)
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-q", "-v", "ON_ERROR_STOP=1",
                    "-c", f"TRUNCATE {kern}.stamp_secret;",
                    "-c", f"INSERT INTO {kern}.stamp_secret (secret) VALUES (decode('{hex_secret}','hex'));"],
                   capture_output=True, text=True, check=True)


def _make_led_shim(root: Path, tmpl_path: Path | None = None,
                    extra_env: dict[str, str] | None = None) -> None:
    """Write the SAME 3-line exec-wrapper bootstrap/new-project.sh writes into every scaffolded
    world's `./led` (BACKLOG maintainer ruling 2026-07-11, "live verbs") -- so cases (i)/(j)/(k)/
    (l)/(m) exercise the REAL led.tmpl through the REAL shim mechanism, not a hand-rolled
    substitute. `tmpl_path` overrides the real, current led.tmpl -- case (m) alone uses this, to
    point one shim at this commit's PARENT led.tmpl (the pre-fix file, read via `git show`) for a
    genuine old-vs-new comparison; every other case leaves this at the default (the real file).
    `extra_env` -- case (m)'s OLD shim also passes AUTOHARN explicitly: the production shim
    (bootstrap/new-project.sh) always execs led.tmpl straight out of the real checkout, so
    led.tmpl's own `AUTOHARN_ROOT="${AUTOHARN:-$(cd "$HERE/../.." && pwd)}"` dirname-relative
    fallback always resolves correctly in production; case (m)'s old script is deliberately a
    COPY living outside that tree (so it stays a proof against `git show HEAD:...`'s exact
    bytes, not a second checkout), so the fallback would resolve to the wrong place -- AUTOHARN
    is supplied via led.tmpl's own already-documented override, not a new mechanism."""
    shim = root / "led"
    target = tmpl_path if tmpl_path is not None else LED_TMPL
    env_prefix = "".join(f'{k}="{v}" ' for k, v in (extra_env or {}).items())
    shim.write_text(
        '#!/bin/sh\n'
        'HERE="$(cd "$(dirname "$0")" && pwd)"\n'
        f'exec env PICKUP_DEPLOYMENT="$HERE/deployment.json" {env_prefix}{target} "$@"\n',
        encoding="utf-8")
    shim.chmod(0o755)


def run_led(root: Path, args: list[str]) -> tuple[int, str]:
    cp = subprocess.run([str(root / "led")] + args, capture_output=True, text=True, cwd=str(root))
    return cp.returncode, cp.stdout + cp.stderr


def ins_row(kind: str, token: str | None, epoch_s: float,
            declared_epoch_s: float | None = None) -> tuple[bool, str]:
    """Insert one fixture ledger row. `declared_epoch_s`, if given, sets `event_declared_ts`
    (s24) -- the writer's own claim of when the event occurred, distinct from `ts` (this row's
    write time). Bound the same way the rest of this fixture binds fixture data: a literal
    `to_timestamp(...)` in the SQL text (no untrusted input crosses this boundary -- every value
    here is this module's own synthetic BASE-relative float, never operator/subject input)."""
    tok_sql = f"SET app.vendor_invocation='{token}';" if token else ""
    declared_col = ", event_declared_ts" if declared_epoch_s is not None else ""
    declared_val = f", to_timestamp({declared_epoch_s})" if declared_epoch_s is not None else ""
    return psql(
        f"SET ROLE {ROLE}; {tok_sql} "
        f"INSERT INTO {SCHEMA}.ledger(kind, statement, ts{declared_col}) "
        f"VALUES ('{kind}','fixture row', to_timestamp({epoch_s}){declared_val});"
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
    case_f_out = ""
    case_g_out = ""

    teardown()
    for f in ("high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
             "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
             "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql"):
        ok, out = apply_ddl(f)
        if not ok:
            print(f"# CONTEMPORANEITY FIXTURE SETUP FAILED ({f}): {out[-500:]}")
            return 1
    provision_stamp_secret(KERN)
    log.append(f"setup: full lineage through s24 applied clean to {DB}.{SCHEMA}/{KERN} (role {ROLE}), "
               f"stamp secret provisioned")

    # ---- case (k)'s own SECOND schema: s23 only, NO s24 -- the real pre-s24 schema the led.tmpl
    # missing-column refusal path is exercised against. ----------------------------------------
    teardown(SCHEMA_PRE24, KERN_PRE24, ROLE_PRE24)
    for f in ("high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
             "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
             "s23-per-invocation-stamp-token.sql"):
        ok, out = apply_ddl(f, SCHEMA_PRE24, KERN_PRE24, ROLE_PRE24)
        if not ok:
            print(f"# CONTEMPORANEITY FIXTURE SETUP FAILED (pre-s24 schema, {f}): {out[-500:]}")
            teardown()
            return 1
    provision_stamp_secret(KERN_PRE24)
    log.append(f"setup: SECOND schema {DB}.{SCHEMA_PRE24}/{KERN_PRE24} applied through s23 ONLY "
               f"(deliberately no s24) -- case (k)'s real pre-s24 substrate")

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

        # ---- CASE f: manufactured LATE_DECLARED (GREEN, the DECLARED twin of case b) --------
        # Byte-identical silence-then-burst SHAPE to case (b), at a disjoint offset range (never
        # colliding with case (b)'s own rows in this same cumulative scratch ledger): a >300s
        # tool-activity silence, zero rows, broken by a burst. The ONLY difference: the burst's
        # silence-breaking row (the one at token_min_ts) carries event_declared_ts claiming the
        # event occurred back near the START of the silence window -- a write-vs-declared gap of
        # ~305s, comfortably over late_threshold_ms(60000ms). design/LATE-ENTRY-AND-INTAKE-
        # SEMANTICS.md Proposal 2's own worked example, manufactured.
        tok_f = "fixture-token-declared-late-f"
        t1_f = BASE + 2010
        t2_f = t1_f + 305
        okpf, opf = ins_row("finding", "fixture-token-pre-f", BASE + 2005.0)
        ok6f, o6f = ins_row("finding", tok_f, t2_f + 0.050, declared_epoch_s=t1_f)
        ok7f, o7f = ins_row("finding", tok_f, t2_f + 0.080)
        ck(okpf and ok6f and ok7f, f"CASE f inserts must succeed: {opf[-200:]} {o6f[-200:]} {o7f[-200:]}")
        root_f = _make_world({
            "invocations.jsonl": [
                {"token": "fixture-token-pre-f", "wall_clock": _iso(t1_f - 5.010), "session_id": "fx-f"},
                {"token": tok_f, "wall_clock": _iso(t2_f + 0.040), "session_id": "fx-f"},
            ],
            "mutation_observer.journal.jsonl": [
                {"ts": _iso_z(BASE + 2000), "outcome": "warned"},
                {"ts": _iso_z(t1_f), "outcome": "warned"},          # last activity before silence
                {"ts": _iso_z(t2_f), "outcome": "warned"},          # 305s later, zero rows between
                {"ts": _iso_z(t2_f + 5), "outcome": "warned"},
            ],
        })
        (root_f / "deployment.json").write_text(json.dumps(
            {"db": DB, "host": PGHOST, "schema": SCHEMA, "kern": KERN, "role": ROLE, "name": "contempprobe"}))
        worlds.append(root_f)
        code_f, out_f = run_audit(root_f)
        case_f_out = out_f
        ck(code_f == 0, f"CASE f: expected exit 0 (LATE_DECLARED), got {code_f}: {out_f[-1200:]}")
        ck("VERDICT: LATE_DECLARED" in out_f, f"CASE f: expected LATE_DECLARED: {out_f[-1200:]}")
        ck(tok_f in out_f, f"CASE f: the honestly-late token must be NAMED: {out_f[-1200:]}")
        ck("VERDICT: BACKFILL_SUSPECT" not in out_f,
           f"CASE f: a DECLARED late entry must NOT verdict BACKFILL_SUSPECT: {out_f[-1200:]}")
        log.append(f"CASE f (manufactured late-declared): exit={code_f}, verdict=LATE_DECLARED, "
                   f"token {tok_f} named, as expected")

        # ---- CASE g: manufactured backfill, UNDECLARED twin, re-asserted post-s24 (RED) -------
        # Re-runs case (b)'s own exact scenario (no event_declared_ts on the silence-breaking
        # row) at a disjoint offset range, AFTER s24 has landed on this schema -- proving
        # BACKFILL_SUSPECT/exit 1 is unaffected by the new column: "nothing existing relaxed",
        # demonstrated on the identical gap shape case (f) just verdicted LATE_DECLARED, not
        # merely asserted from the SQL closure statement's prose.
        tok_g = "fixture-token-undeclared-g"
        t1_g = BASE + 3010
        t2_g = t1_g + 305
        okpg, opg = ins_row("finding", "fixture-token-pre-g", BASE + 3005.0)
        ok6g, o6g = ins_row("finding", tok_g, t2_g + 0.050)
        ok7g, o7g = ins_row("finding", tok_g, t2_g + 0.080)
        ck(okpg and ok6g and ok7g, f"CASE g inserts must succeed: {opg[-200:]} {o6g[-200:]} {o7g[-200:]}")
        root_g = _make_world({
            "invocations.jsonl": [
                {"token": "fixture-token-pre-g", "wall_clock": _iso(t1_g - 5.010), "session_id": "fx-g"},
                {"token": tok_g, "wall_clock": _iso(t2_g + 0.040), "session_id": "fx-g"},
            ],
            "mutation_observer.journal.jsonl": [
                {"ts": _iso_z(BASE + 3000), "outcome": "warned"},
                {"ts": _iso_z(t1_g), "outcome": "warned"},
                {"ts": _iso_z(t2_g), "outcome": "warned"},
                {"ts": _iso_z(t2_g + 5), "outcome": "warned"},
            ],
        })
        (root_g / "deployment.json").write_text(json.dumps(
            {"db": DB, "host": PGHOST, "schema": SCHEMA, "kern": KERN, "role": ROLE, "name": "contempprobe"}))
        worlds.append(root_g)
        code_g, out_g = run_audit(root_g)
        case_g_out = out_g
        ck(code_g == 1, f"CASE g: expected exit 1 (BACKFILL_SUSPECT), got {code_g}: {out_g[-1200:]}")
        ck("VERDICT: BACKFILL_SUSPECT" in out_g, f"CASE g: expected BACKFILL_SUSPECT: {out_g[-1200:]}")
        ck(tok_g in out_g, f"CASE g: the offending undeclared token must be NAMED: {out_g[-1200:]}")
        log.append(f"CASE g (undeclared twin, post-s24): exit={code_g}, verdict=BACKFILL_SUSPECT, "
                   f"token {tok_g} named -- byte-identical shape to case b, s24 changes nothing here")

        # ---- CASE h: intake-shape benign (run-10's own SHAPE, reproduced synthetically) -------
        # design/LATE-ENTRY-AND-INTAKE-SEMANTICS.md Proposal 1: a multi-row token burst whose
        # every row precedes THIS world's own first tool_event -- run-10 rows 2-11 (ten
        # present-tense task declarations, written before any tool activity existed to narrate;
        # BACKLOG "Run-10 first audit verdict adjudicated", 2026-07-11). Reproduced here, not
        # against the live run-10 world (runs are linear; a settled world is read-only evidence).
        tok_h = "fixture-token-intake-h"
        ok8, o8 = ins_row("decision", tok_h, BASE + 4000.000)
        ok9, o9 = ins_row("decision", tok_h, BASE + 4000.010)
        ok10, o10 = ins_row("decision", tok_h, BASE + 4000.020)
        ck(ok8 and ok9 and ok10, f"CASE h inserts must succeed: {o8[-200:]} {o9[-200:]} {o10[-200:]}")
        root_h = _make_world({
            "invocations.jsonl": [
                {"token": tok_h, "wall_clock": _iso(BASE + 3999.990), "session_id": "fx-h"},
            ],
            "mutation_observer.journal.jsonl": [
                {"ts": _iso_z(BASE + 4010), "outcome": "warned"},   # AFTER the burst
                {"ts": _iso_z(BASE + 4020), "outcome": "warned"},
            ],
        })
        (root_h / "deployment.json").write_text(json.dumps(
            {"db": DB, "host": PGHOST, "schema": SCHEMA, "kern": KERN, "role": ROLE, "name": "contempprobe"}))
        worlds.append(root_h)
        code_h, out_h = run_audit(root_h)
        ck(code_h == 0, f"CASE h: expected exit 0 (BATCHED_DECLARED), got {code_h}: {out_h[-1200:]}")
        ck("VERDICT: BATCHED_DECLARED" in out_h, f"CASE h: expected BATCHED_DECLARED: {out_h[-1200:]}")
        burst_line_h = next((ln for ln in out_h.splitlines() if tok_h in ln), "")
        ck("intake-shape (precedes all tool activity)" in burst_line_h,
           f"CASE h: the run-10-shape burst must be annotated intake-shape: {burst_line_h!r} "
           f"(full output tail: {out_h[-1200:]})")
        log.append(f"CASE h (intake-shape benign, run-10 shape): exit={code_h}, "
                   f"verdict=BATCHED_DECLARED, token {tok_h} annotated intake-shape, as expected")

        # ---- CASE i: led.tmpl's --event-time CLI, generic path SUCCESS (GREEN) ----------------
        # A REAL `led` shim invocation (subprocess, not a hand-built SQL INSERT) against the
        # s24-capable schema -- closes the CLI-path coverage gap an out-of-frame audit of this
        # commission found (every other case here proves the ENGINE layer only).
        root_i = Path(tempfile.mkdtemp(prefix="contemp-led-fixture-"))
        (root_i / "deployment.json").write_text(json.dumps(
            {"db": DB, "host": PGHOST, "schema": SCHEMA, "kern": KERN, "role": ROLE, "name": "contempprobe"}))
        _make_led_shim(root_i)
        worlds.append(root_i)
        code_i, out_i = run_led(root_i, ["--event-time", "2026-07-11T10:00:00Z", "finding",
                                         "cli --event-time success, case i"])
        ck(code_i == 0, f"CASE i: expected exit 0 (CLI success), got {code_i}: {out_i[-800:]}")
        ok_i, sel_i = psql(
            f"SELECT event_declared_ts = '2026-07-11T10:00:00Z'::timestamptz FROM {SCHEMA}.ledger "
            f"WHERE statement = 'cli --event-time success, case i';")
        ck(ok_i and "t" in sel_i, f"CASE i: the declared value must round-trip exactly: {sel_i}")
        log.append(f"CASE i (led --event-time CLI, generic path): exit={code_i}, row landed with "
                   f"event_declared_ts matching the declared value, as expected")

        # ---- CASE j: led.tmpl's --event-time CLI, COVERAGE REFUSAL on a non-generic verb (RED) -
        code_j, out_j = run_led(root_i, ["--event-time", "2026-07-11T10:00:00Z", "work", "open",
                                         "cliguard-slug", "cli coverage guard test"])
        ck(code_j == 1, f"CASE j: expected exit 1 (coverage refusal), got {code_j}: {out_j[-800:]}")
        ck("REFUSED" in out_j and "only supported on the generic" in out_j,
           f"CASE j: the refusal must be visible and name the reason: {out_j[-800:]}")
        log.append(f"CASE j (led --event-time CLI, non-generic verb): exit={code_j}, REFUSED with "
                   f"teach-text, as expected -- no silent drop")

        # ---- CASE k: led.tmpl's --event-time CLI, PRE-S24 SCHEMA REFUSAL (RED) -----------------
        # The live information_schema.columns capability check, exercised against a REAL
        # pre-s24 schema (SCHEMA_PRE24, applied through s23 only, set up above).
        root_k = Path(tempfile.mkdtemp(prefix="contemp-led-fixture-pre24-"))
        (root_k / "deployment.json").write_text(json.dumps(
            {"db": DB, "host": PGHOST, "schema": SCHEMA_PRE24, "kern": KERN_PRE24,
             "role": ROLE_PRE24, "name": "contempprobe-pre24"}))
        _make_led_shim(root_k)
        worlds.append(root_k)
        code_k, out_k = run_led(root_k, ["--event-time", "2026-07-11T10:00:00Z", "finding",
                                         "cli pre-s24 refusal, case k"])
        ck(code_k == 1, f"CASE k: expected exit 1 (pre-s24 refusal), got {code_k}: {out_k[-800:]}")
        ck("REFUSED" in out_k and "predates s24" in out_k,
           f"CASE k: the refusal must be visible and name the real missing capability: {out_k[-800:]}")
        log.append(f"CASE k (led --event-time CLI, pre-s24 schema): exit={code_k}, REFUSED naming "
                   f"the missing event_declared_ts column, as expected")

        # ---- CASE l: led.tmpl's ledger_kind_check refusal now TEACHES the valid-kind list -----
        # (BACKLOG "Run-10 closure audit (2026-07-11)", item 1 / change proposal 1). run-10 row
        # 67's own specimen, verbatim: an invented kind ('acceptance-criteria'), refused by the
        # kernel's ledger_kind_check CHECK constraint. Before this fix the agent saw only the
        # bare "violates check constraint ledger_kind_check" text and had to separately query
        # pg_get_constraintdef by hand (17s, one extra command) to learn what led.tmpl's own
        # header already lists. Real `led` shim (root_i, already s24-capable from case i above),
        # real refusal, real LIVE re-query -- never a hardcoded second copy of the vocabulary.
        code_l, out_l = run_led(root_i, ["acceptance-criteria",
                                         "QEUBO smoke-test acceptance criterion (run-10 row-67 specimen)"])
        ck(code_l != 0, f"CASE l: an invented kind must still be REFUSED (non-zero exit), got {code_l}: {out_l[-800:]}")
        ck("ledger_kind_check" in out_l,
           f"CASE l: the original kernel refusal must still be visible, unrewrapped: {out_l[-800:]}")
        ck("valid kinds (live" in out_l,
           f"CASE l: the refusal must now TEACH the live valid-kind list: {out_l[-800:]}")
        for known_kind in ("decision", "assumption", "work_opened", "review"):
            ck(known_kind in out_l, f"CASE l: valid-kind list must name '{known_kind}': {out_l[-800:]}")
        ck("acceptance-criteria" not in out_l.split("valid kinds", 1)[-1],
           f"CASE l: the invented kind itself must NOT appear in the live vocabulary list: {out_l[-800:]}")
        log.append(f"CASE l (led kind-refusal teach, run-10 row-67 specimen): exit={code_l}, "
                   f"REFUSED, original ledger_kind_check error preserved, live valid-kind list "
                   f"now taught (decision/assumption/work_opened/review confirmed present)")

        # ---- CASE m: a VALID kind's success path is BYTE-IDENTICAL to the pre-fix script -------
        # The fix above only ever runs AFTER a failed insert (case l); this proves the success
        # path (the overwhelmingly common case) was not touched at all -- one shim points at
        # PRE_KIND_TEACH_FIX_SHA's own led.tmpl (`git show <fixed SHA>:...`, the file as it stood
        # immediately before item 1's fix landed -- a pinned historical commit, NOT `HEAD`, so
        # this stays a genuine two-script diff forever rather than degrading into a self-
        # comparison the moment this fix's own commit becomes an ancestor of HEAD; see that
        # constant's own comment), one at the just-edited current file (root_i, reused). Verified
        # self-checking: the pinned SHA's content is asserted to genuinely PREDATE the fix (no
        # _led_kind_refusal_teach function) before it's trusted as the "old" specimen.
        old_tmpl_src = subprocess.run(
            ["git", "-C", str(REPO), "show", f"{PRE_KIND_TEACH_FIX_SHA}:bootstrap/templates/led.tmpl"],
            capture_output=True, text=True, check=True).stdout
        ck("_led_kind_refusal_teach" not in old_tmpl_src,
           f"CASE m: PRE_KIND_TEACH_FIX_SHA ({PRE_KIND_TEACH_FIX_SHA}) must genuinely PREDATE the "
           f"fix -- it already contains _led_kind_refusal_teach, so it is not a pre-fix specimen")
        root_m_old = Path(tempfile.mkdtemp(prefix="contemp-led-fixture-oldtmpl-"))
        old_tmpl_path = root_m_old / "led.tmpl.old"
        old_tmpl_path.write_text(old_tmpl_src, encoding="utf-8")
        old_tmpl_path.chmod(0o755)
        (root_m_old / "deployment.json").write_text(json.dumps(
            {"db": DB, "host": PGHOST, "schema": SCHEMA, "kern": KERN, "role": ROLE, "name": "contempprobe"}))
        _make_led_shim(root_m_old, tmpl_path=old_tmpl_path, extra_env={"AUTOHARN": str(REPO)})
        worlds.append(root_m_old)
        code_m_old, out_m_old = run_led(root_m_old, ["decision", "byte-identical probe, case m, OLD led.tmpl"])
        code_m_new, out_m_new = run_led(root_i, ["decision", "byte-identical probe, case m, NEW led.tmpl"])
        ck(code_m_old == 0 and code_m_new == 0,
           f"CASE m: both OLD and NEW writes must succeed: old={code_m_old} new={code_m_new}")
        ck(out_m_old == out_m_new,
           f"CASE m: a valid kind's success output must be BYTE-IDENTICAL old vs new: "
           f"old={out_m_old!r} new={out_m_new!r}")
        log.append(f"CASE m (success path, OLD @{PRE_KIND_TEACH_FIX_SHA} vs NEW led.tmpl): "
                   f"exit_old={code_m_old}, exit_new={code_m_new}, stdout byte-identical "
                   f"({out_m_new!r})")

        # ---- CASE n: led.tmpl's `show <id>` CLI, SUCCESS (GREEN) -----------------------------
        # A real `led show <id>` shim invocation (root_i, already s24-capable from case i) against
        # a KNOWN row -- case i's own inserted row, looked up by its unique statement text via a
        # direct -tAc SELECT (bypassing the module's own psql() helper, which returns psql's
        # human-formatted table, not a bare value).
        id_lookup = subprocess.run(
            ["psql", "-h", PGHOST, "-d", DB, "-tAc",
             f"SELECT id FROM {SCHEMA}.ledger WHERE statement = "
             f"'cli --event-time success, case i';"],
            capture_output=True, text=True)
        row_id_n = id_lookup.stdout.strip()
        ck(id_lookup.returncode == 0 and row_id_n.isdigit(),
           f"CASE n setup: could not find case-i's own row id: rc={id_lookup.returncode} "
           f"stdout={id_lookup.stdout!r} stderr={id_lookup.stderr!r}")
        code_n, out_n = run_led(root_i, ["show", row_id_n])
        ck(code_n == 0, f"CASE n: expected exit 0 (show success), got {code_n}: {out_n[-800:]}")
        ck("cli --event-time success, case i" in out_n,
           f"CASE n: the full, untruncated statement must be printed: {out_n[-800:]}")
        ck(bool(re.search(rf"^id\s*\|\s*{row_id_n}\s*$", out_n, re.MULTILINE)),
           f"CASE n: expanded (-x) display must show the id column matching the looked-up row "
           f"id ({row_id_n}), not just the statement text anywhere: {out_n[-800:]}")
        log.append(f"CASE n (led show CLI, success): exit={code_n}, row id={row_id_n}, full "
                   f"untruncated statement text printed, as expected")

        # ---- CASE o: led.tmpl's `show <id>` CLI, MISSING id REFUSAL (RED, run-11 class-b fix) ---
        # An id that certainly does not exist in this scratch schema -> REFUSED, never a silent
        # fall-through into the generic write path (the run-11 finding: before this fix, `show`
        # cleared the arg-count guard and was absorbed as kind='show', refused by
        # ledger_kind_check, burning a SEQUENCE id even though no row landed -- bigserial's
        # nextval() is non-transactional, so a rolled-back INSERT attempt still advances the
        # sequence). The discriminating proof is therefore the SEQUENCE's own last_value, read
        # directly (-tAc, a bare value) before/after: unchanged means the write path was never
        # even attempted, not merely that no row happened to land.
        def _seq_last_value() -> str:
            r = subprocess.run(
                ["psql", "-h", PGHOST, "-d", DB, "-tAc",
                 f"SELECT last_value FROM {SCHEMA}.ledger_id_seq;"],
                capture_output=True, text=True)
            return r.stdout.strip()

        seq_before_o = _seq_last_value()
        code_o, out_o = run_led(root_i, ["show", "999999999"])
        seq_after_o = _seq_last_value()
        ck(code_o != 0, f"CASE o: a missing id must be REFUSED (non-zero exit), got {code_o}: "
                        f"{out_o[-800:]}")
        ck("REFUSED" in out_o and "no ledger row with id=999999999" in out_o,
           f"CASE o: the refusal must be visible and name the missing id: {out_o[-800:]}")
        ck("ledger_kind_check" not in out_o,
           f"CASE o: the OLD fall-through symptom (a bare kernel CHECK-constraint violation on "
           f"kind='show') must never appear -- `show` is dispatched before the write path is "
           f"even reached: {out_o[-800:]}")
        ck(seq_before_o != "" and seq_before_o == seq_after_o,
           f"CASE o: the ledger id sequence's last_value must be UNCHANGED across a missing-id "
           f"`show` (before={seq_before_o!r}, after={seq_after_o!r}) -- a changed value would "
           f"mean an INSERT was attempted (and its id burned) even though it refused, the exact "
           f"run-11 phantom-burn class this fix forecloses")
        log.append(f"CASE o (led show CLI, missing id): exit={code_o}, REFUSED with teach-text "
                   f"naming the missing id, no kernel CHECK-constraint fall-through text, ledger "
                   f"id sequence last_value unchanged ({seq_before_o}), as expected")

    finally:
        for w in worlds:
            shutil.rmtree(w, ignore_errors=True)
        # world tempdirs are always cleaned up regardless of outcome; the two SCHEMAS follow the
        # standing probe pattern below instead (left standing on failure, for post-mortem
        # inspection -- torn down only after a fully clean run).

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
    (HERE / "late-declared-green.txt").write_text(
        "# banked GREEN evidence -- CASE f (manufactured late-declared, DECLARED twin of case b), "
        "engine/contemp_audit.py real output:\n" + case_f_out, encoding="utf-8")
    (HERE / "late-declared-red.txt").write_text(
        "# banked RED evidence -- CASE g (manufactured backfill, UNDECLARED twin, re-asserted "
        "post-s24), engine/contemp_audit.py real output:\n" + case_g_out, encoding="utf-8")
    teardown()
    teardown(SCHEMA_PRE24, KERN_PRE24, ROLE_PRE24)
    print("\n# CONTEMPORANEITY-AUDIT FIXTURE PASS -- both polarities proven (clean batch does NOT "
          "flag; manufactured silence-then-burst DOES, naming the token); the honest N/A refusal "
          "proven on an empty scratch ledger AND live against run7's real pre-s23 data; the "
          "late-entry discipline's own both polarities proven (a DECLARED late entry over the "
          "identical silence-then-burst gap verdicts LATE_DECLARED/exit 0, the UNDECLARED twin "
          "still verdicts BACKFILL_SUSPECT/exit 1); the intake-shape annotation proven on the "
          "run-10 burst shape (BATCHED_DECLARED, annotated, no vocabulary change); led.tmpl's own "
          "--event-time CLI flag proven end-to-end through a real shim (generic-path success, "
          "non-generic-verb coverage refusal, pre-s24-schema capability refusal); the "
          "ledger_kind_check refusal now teaches its live valid-kind list (run-10 row-67 "
          "specimen) while the success path stays byte-identical to the pre-fix script.")
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
