#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T06:36:43Z
#   last-change: 2026-07-18T06:37:21Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity witness for ../../otel-attest (design/FABLE-OTEL-SENTRY-SPEC.md
§4-§7, Amendments A1/A2), covering the review-adjudicated fix pass (ledger row 1505, work item
otel-attest-review-fixes). Real infra, no mocks: CLASSIC scaffolds through s41 in the TOY db
(the exact pattern seen-red/defeat-pipeline/run_fixtures.py and
seen-red/s41-principal-bindings-and-relations/run_fixtures.py already bank), torn down before
and after. Synthetic OTel exports are hand-built OTLP-shaped JSONL (no real collector needed --
otel-attest's own `load_export` only cares about the JSON shape). Never touches kernel/,
bootstrap/, or any live world -- scratch schema pairs only.

Legs (each both-polarity in spirit -- a positive case that must land, a negative/refusal case
that must not silently pass):

  L1  exact-command, single-candidate rule (F3): exactly one candidate api_request bracketing
      a matched tool-detail event grades exact-command; two candidates that happen to AGREE on
      model must NOT (the spec's own "exactly one candidate", not "model agreement among
      several").
  L2  ambiguous writes an attestation, both A1 verdict branches: every candidate model
      contradicting the declared expectation -> verdict=MISMATCH (with model=unresolved and a
      companion finding row); at least one candidate matching -> verdict=unevaluated (still
      writes, still one companion finding row -- the F1 gate fix + Amendment A1's value
      domain).
  L3  write-time delimiter refusal (F2/A2): a field value (here, `model`) containing the `|`
      delimiter is refused AT WRITE TIME with a diagnostic naming the field; nothing is
      written for that row.
  L4  parser rejections (F4/F5), no DB needed: row= restricted to ASCII digits (a Unicode
      full-width numeral is refused), segment trimming restricted to ASCII whitespace (an NBSP
      is preserved, not silently trimmed, so it breaks the segment prefix and is refused), and
      empty model=/session=/basis= are refused.
  L5  idempotency: re-running the verb over the same world+export does not re-attest rows
      already carrying a v1 attestation.
  L6  F7's partial-failure exit code: a verification row lands but its required MISMATCH
      companion finding row fails to write (simulated via a `led` wrapper that refuses only
      `finding` writes) -- the run's exit code must be nonzero.

Usage: python3 seen-red/otel-attest/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from importlib.machinery import SourceFileLoader
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LINEAGE = REPO / "kernel" / "lineage"
OTEL_ATTEST = REPO / "otel-attest"
sys.path.insert(0, str(REPO / "filing"))

import pghost_resolve  # noqa: E402

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_B = [
    "s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
    "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql", "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql", "s31-supersession-uniform-retraction.sql",
    "s32-edge-views-single-home.sql", "s33-composite-discharge.sql",
    "s34-computed-grade-refusal.sql", "s35-validation-decomposition.sql",
    "s36-decision-grade.sql", "s37-violation-disposition.sql",
    "s38-bookkeeping-close.sql", "s39-blocks-start.sql",
    "s40-principal-identity-events.sql", "s41-principal-bindings-and-relations.sql",
]

# The module under test, loaded directly (no .py extension) for the no-DB parser legs (L4),
# exactly the pattern the adversarial review's own test scripts used
# (test_parse.py/test_grade.py, banked at the review's scratchpad).
_loader = SourceFileLoader("otel_attest_module", str(OTEL_ATTEST))
otel_attest = _loader.load_module()  # noqa: DEP001 -- load_module is deprecated but exec_module
                                      # requires spec_from_loader; this is the direct one-liner
                                      # form used consistently across this repo's own fixtures.


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown(world: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {world} CASCADE; DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "
        f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def led(world_dir: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    e = dict(os.environ)
    if env:
        e.update(env)
    return sh(["bash", str(world_dir / "led"), *args], cwd=str(world_dir), env=e)


def led_stamped(world_dir: Path, *args: str, session: str | None = None,
                 invocation: str | None = None, actor: str | None = None
                 ) -> subprocess.CompletedProcess[str]:
    """Writes through `led` carrying a manually-set app.vendor_session / app.vendor_invocation
    GUC (via PGOPTIONS, the exact mechanism hooks/stamp_intercept.py uses on a real session --
    see s17-stamp-mechanism.sql's set_stamp trigger, which captures stamp_session/
    stamp_invocation unconditionally and only needs the HMAC GUCs for stamp_verified=true, not
    for the join columns otel-attest actually reads). No HMAC is set here -- these rows land
    stamp_verified=false, which otel-attest does not consult."""
    e = dict(os.environ)
    if actor:
        e["LED_ACTOR"] = actor
    pgopts = []
    if session:
        pgopts.append(f"-c app.vendor_session={session}")
    if invocation:
        pgopts.append(f"-c app.vendor_invocation={invocation}")
    if pgopts:
        e["PGOPTIONS"] = " ".join(pgopts)
    return sh(["bash", str(world_dir / "led"), *args], cwd=str(world_dir), env=e)


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def scaffold_classic(world: str, chain: list[str]) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    schema, kern, role = world, f"{world}_kernel", f"{world}_rw"
    r = sh(["bash", str(NEW_PROJECT), str(world_dir),
            "--db", PGDB, "--host", PGHOST,
            "--schema", schema, "--kern", kern, "--role", role])
    if r.returncode != 0:
        raise RuntimeError(f"CLASSIC SCAFFOLD FAILED ({world}): {r.stdout[-1500:]} {r.stderr[-1500:]}")
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for name in chain:
        args += ["-f", str(LINEAGE / name)]
    ra = sh(args)
    if ra.returncode != 0:
        raise RuntimeError(f"CLASSIC apply FAILED ({world}): {ra.stdout[-1500:]} {ra.stderr[-1500:]}")
    hexsecret = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"TRUNCATE {kern}.stamp_secret;",
        "-c", f"INSERT INTO {kern}.stamp_secret (secret) VALUES (decode('{hexsecret}','hex'));"])
    genesis_hex = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis_hex}') "
              f"ON CONFLICT (only_one) DO NOTHING;"])
    return world_dir


def birth_acts(world: str) -> None:
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    script = (
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_purpose)\n"
        f"VALUES ('principal_registered', 'author registered (fixture genesis exception)',\n"
        f"        (SELECT id FROM principal WHERE name='author'),\n"
        f"        (SELECT id FROM principal WHERE name='author'), 'fixture connection principal');\n"
        f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_db_role)\n"
        f"VALUES ('principal_standing_declared', 'role {R} -> author',\n"
        f"        (SELECT id FROM principal WHERE name='author'),\n"
        f"        (SELECT id FROM principal WHERE name='author'), '{R}');\n")
    r = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"], input=script)
    if r.returncode != 0:
        raise RuntimeError(f"birth acts failed ({world}): {r.stderr[-600:]}")


def row_id_last(world: str, kind: str, statement: str) -> int:
    out = psql_tuples(
        f"SELECT id FROM {world}.ledger WHERE kind='{kind}' AND statement = $stmt${statement}$stmt$ "
        f"ORDER BY id DESC LIMIT 1;")
    return int(out)


def register_sentry(wdir: Path) -> None:
    r = led(wdir, "register-principal", "sentry", "tool", "--purpose",
             "otel-attest fixture sentry", env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    r = led(wdir, "principal", "grant-competence", "sentry", "--activity",
             "model-identity-attestation", "--band", "n/a", "--basis", "fixture",
             env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr


def run_otel_attest(wdir: Path, export: Path, extra: list[str] | None = None
                     ) -> subprocess.CompletedProcess[str]:
    args = ["python3", str(OTEL_ATTEST), "--world", str(wdir), "--export", str(export),
            "--actor", "sentry", "--recent", "50"]
    if extra:
        args += extra
    return sh(args)


# ---------------------------------------------------------------------------------------------
# Synthetic OTel export construction (OTLP-shaped JSONL; otel-attest's load_export only reads
# the shape, never a real collector).
# ---------------------------------------------------------------------------------------------


def otlp_record(*, session_id: str, event_name: str | None = None, model: str | None = None,
                 query_source: str | None = None, tool_parameters: str | None = None,
                 expected_model: str | None = None, ts: datetime | None = None) -> dict:
    attrs = [{"key": "session.id", "value": {"stringValue": session_id}}]
    if event_name is not None:
        attrs.append({"key": "event.name", "value": {"stringValue": event_name}})
    if model is not None:
        attrs.append({"key": "model", "value": {"stringValue": model}})
    if query_source is not None:
        attrs.append({"key": "query_source", "value": {"stringValue": query_source}})
    if tool_parameters is not None:
        attrs.append({"key": "tool_parameters", "value": {"stringValue": tool_parameters}})
    if expected_model is not None:
        attrs.append({"key": "autoharn.expected_model", "value": {"stringValue": expected_model}})
    rec: dict = {"attributes": attrs}
    if ts is not None:
        rec["timeUnixNano"] = str(int(ts.timestamp() * 1e9))
    return rec


def write_export(path: Path, records: list[dict]) -> None:
    batch = {"resourceLogs": [{"scopeLogs": [{"logRecords": records}]}]}
    path.write_text(json.dumps(batch) + "\n", encoding="utf-8")


FAR_PAST = datetime(2020, 1, 1, tzinfo=timezone.utc)  # far outside any 3s bracket tolerance


# ---------------------------------------------------------------------------------------------
# L4 -- parser rejections (F4/F5), no DB needed.
# ---------------------------------------------------------------------------------------------


def l4_parser_rejections(failures: list[str]) -> None:
    MalformedStatement = otel_attest.MalformedStatement
    parse = otel_attest.parse_v1_statement

    def raises_malformed(stmt: str) -> tuple[bool, str]:
        try:
            parse(stmt)
            return (False, "did not raise")
        except MalformedStatement as e:
            return (True, str(e))

    # Unicode full-width digit row= (F4)
    stmt = ("model-attestation v1 | row=１２ | model=m | grade=exact-command | expected=e "
            "| verdict=match | session=s | basis=b | rebuttals=r")
    ok, detail = raises_malformed(stmt)
    check("L4-row-unicode-digit-rejected", ok, detail, failures)

    # ASCII digit row= still accepted (positive control -- the fix must not over-refuse)
    stmt_ok = ("model-attestation v1 | row=12 | model=m | grade=exact-command | expected=e "
               "| verdict=match | session=s | basis=b | rebuttals=r")
    parsed = parse(stmt_ok)
    check("L4-row-ascii-digit-accepted", parsed is not None and parsed != "VERSION_SKIP"
          and parsed["row"] == "12", f"parsed={parsed!r}", failures)

    # NBSP instead of ASCII space before a segment's key (F4): must NOT be silently trimmed --
    # it breaks the prefix match and is refused, rather than being absorbed as ordinary
    # whitespace the way Python's Unicode-aware str.strip() would.
    nbsp = " "
    stmt_nbsp = (f"model-attestation v1 |{nbsp}row=1 | model=m | grade=exact-command "
                 f"| expected=e | verdict=match | session=s | basis=b | rebuttals=r")
    ok, detail = raises_malformed(stmt_nbsp)
    check("L4-nbsp-segment-not-silently-trimmed", ok, detail, failures)

    # Empty model=/session=/basis= (F5)
    for field in ("model", "session", "basis"):
        parts = {"row": "1", "model": "m", "grade": "exact-command", "expected": "e",
                  "verdict": "match", "session": "s", "basis": "b", "rebuttals": "r"}
        parts[field] = ""
        stmt_empty = (f"model-attestation v1 | row={parts['row']} | model={parts['model']} "
                      f"| grade={parts['grade']} | expected={parts['expected']} "
                      f"| verdict={parts['verdict']} | session={parts['session']} "
                      f"| basis={parts['basis']} | rebuttals={parts['rebuttals']}")
        ok, detail = raises_malformed(stmt_empty)
        check(f"L4-empty-{field}-rejected", ok, detail, failures)

    # expected= empty IS legal ("undeclared" is a normal value, never required non-empty)
    stmt_expected_empty = ("model-attestation v1 | row=1 | model=m | grade=exact-command "
                            "| expected= | verdict=unevaluated | session=s | basis=b "
                            "| rebuttals=r")
    parsed = parse(stmt_expected_empty)
    check("L4-empty-expected-still-accepted", parsed is not None and parsed != "VERSION_SKIP",
          f"parsed={parsed!r}", failures)


# ---------------------------------------------------------------------------------------------
# The DB-backed legs: L1 (exact-command), L2 (ambiguous/A1), L3 (delimiter refusal),
# L5 (idempotency) -- all against ONE scratch world so the scaffold cost is paid once.
# ---------------------------------------------------------------------------------------------


def world_main_check(failures: list[str], tmps: list[Path]) -> None:
    world = "s41oa"
    teardown(world)
    print(f"== scaffolding classic world {world} (chain ends {CHAIN_B[-1]}) ==")
    wdir = scaffold_classic(world, CHAIN_B)
    tmps.append(wdir.parent)
    birth_acts(world)
    register_sentry(wdir)

    now = datetime.now(timezone.utc)

    # ---- L1 positive: exactly one candidate api_request brackets the matched tool call ----
    t1_stmt = "L1-positive target row"
    r = led_stamped(wdir, "decision", t1_stmt, session="SESS-L1-POS", invocation="INV-L1-POS",
                     actor="author")
    assert r.returncode == 0, r.stdout + r.stderr
    t1 = row_id_last(world, "decision", t1_stmt)

    # ---- L1 negative: TWO candidates bracket the same tool call and happen to AGREE on
    # model -- must NOT grade exact-command (F3: "exactly one candidate", not "model
    # agreement") ----
    t2_stmt = "L1-negative (two agreeing candidates) target row"
    r = led_stamped(wdir, "decision", t2_stmt, session="SESS-L1-NEG", invocation="INV-L1-NEG",
                     actor="author")
    assert r.returncode == 0, r.stdout + r.stderr
    t2 = row_id_last(world, "decision", t2_stmt)

    # ---- L2 ambiguous, MISMATCH branch: every candidate model contradicts expected ----
    t3_stmt = "L2-ambiguous-mismatch target row"
    r = led_stamped(wdir, "decision", t3_stmt, session="SESS-L2-MISMATCH", actor="author")
    assert r.returncode == 0, r.stdout + r.stderr
    t3 = row_id_last(world, "decision", t3_stmt)

    # ---- L2 ambiguous, unevaluated branch: one candidate matches expected ----
    t4_stmt = "L2-ambiguous-unevaluated target row"
    r = led_stamped(wdir, "decision", t4_stmt, session="SESS-L2-UNEVAL", actor="author")
    assert r.returncode == 0, r.stdout + r.stderr
    t4 = row_id_last(world, "decision", t4_stmt)

    # ---- L3: model value carries the '|' delimiter -- must be refused at write time ----
    t5_stmt = "L3-delimiter-refusal target row"
    r = led_stamped(wdir, "decision", t5_stmt, session="SESS-L3-DELIM", actor="author")
    assert r.returncode == 0, r.stdout + r.stderr
    t5 = row_id_last(world, "decision", t5_stmt)

    tool_detail_pos = otlp_record(session_id="SESS-L1-POS", event_name="tool_result",
                                   tool_parameters="app.vendor_invocation=INV-L1-POS", ts=now)
    tool_detail_neg = otlp_record(session_id="SESS-L1-NEG", event_name="tool_result",
                                   tool_parameters="app.vendor_invocation=INV-L1-NEG", ts=now)
    records = [
        tool_detail_pos,
        otlp_record(session_id="SESS-L1-POS", event_name="api_request",
                     model="claude-fable-5", query_source="sdk", ts=now + timedelta(seconds=1)),
        tool_detail_neg,
        otlp_record(session_id="SESS-L1-NEG", event_name="api_request",
                     model="claude-fable-5", query_source="sdk", ts=now + timedelta(seconds=1)),
        otlp_record(session_id="SESS-L1-NEG", event_name="api_request",
                     model="claude-fable-5", query_source="sdk", ts=now - timedelta(seconds=1)),
        otlp_record(session_id="SESS-L2-MISMATCH", event_name="api_request",
                     model="claude-fake-1", query_source="sdk",
                     expected_model="claude-real-model", ts=FAR_PAST),
        otlp_record(session_id="SESS-L2-MISMATCH", event_name="api_request",
                     model="claude-fake-2", query_source="sdk", ts=FAR_PAST + timedelta(seconds=5)),
        otlp_record(session_id="SESS-L2-UNEVAL", event_name="api_request",
                     model="claude-fake-1", query_source="sdk",
                     expected_model="claude-fake-1", ts=FAR_PAST),
        otlp_record(session_id="SESS-L2-UNEVAL", event_name="api_request",
                     model="claude-fake-2", query_source="sdk", ts=FAR_PAST + timedelta(seconds=5)),
        otlp_record(session_id="SESS-L3-DELIM", event_name="api_request",
                     model="claude-x|evil-injection", query_source="sdk", ts=now),
    ]
    export_path = wdir.parent / "export.jsonl"
    write_export(export_path, records)

    # ---- run 1: everything attestable gets attested ----
    r1 = run_otel_attest(wdir, export_path)
    out1 = r1.stdout + r1.stderr

    check("L1-exact-command-single-candidate",
          f"attested row {t1}: grade=exact-command" in out1 and "model='claude-fable-5'" in out1,
          f"rc={r1.returncode}\n{out1}", failures)
    check("L1-two-agreeing-candidates-NOT-exact-command",
          (f"attested row {t2}:" in out1) and (f"attested row {t2}: grade=exact-command" not in out1),
          f"rc={r1.returncode}\n{out1}", failures)

    check("L2-ambiguous-mismatch-writes-attestation",
          f"attested row {t3}: grade=ambiguous verdict=MISMATCH model='unresolved'" in out1,
          f"rc={r1.returncode}\n{out1}", failures)
    check("L2-ambiguous-mismatch-companion-finding",
          f"attested row {t3}" in out1
          and "companion finding row written for row {}".format(t3) in out1,
          f"rc={r1.returncode}\n{out1}", failures)

    check("L2-ambiguous-unevaluated-writes-attestation",
          f"attested row {t4}: grade=ambiguous verdict=unevaluated model='unresolved'" in out1,
          f"rc={r1.returncode}\n{out1}", failures)
    check("L2-ambiguous-unevaluated-companion-finding",
          f"attested row {t4}" in out1
          and "companion finding row written for row {}".format(t4) in out1,
          f"rc={r1.returncode}\n{out1}", failures)

    check("L3-delimiter-refused-at-write-time",
          "attestation write REFUSED for row {}".format(t5) in out1
          and "field 'model'" in out1 and "'|' delimiter" in out1
          and f"attested row {t5}:" not in out1,
          f"rc={r1.returncode}\n{out1}", failures)

    # ---- run 2: idempotency (L5) -- every previously-attested target is skipped, nothing
    # re-written; the still-uncovered delimiter row is retried (it was never attested, so it
    # is NOT "already attested" -- it is attempted and refused again, which is correct: a
    # refusal is not a skip) ----
    r2 = run_otel_attest(wdir, export_path)
    out2 = r2.stdout + r2.stderr
    check("L5-idempotency-skips-already-attested",
          all(f"row {t}: skipped (already attested; pass --re-attest to redo)" in out2
              for t in (t1, t2, t3, t4))
          and all(f"attested row {t}:" not in out2 for t in (t1, t2, t3, t4)),
          f"rc={r2.returncode}\n{out2}", failures)

    teardown(world)


def world_f7_check(failures: list[str], tmps: list[Path]) -> None:
    """L6 -- F7: a verification row lands but its required MISMATCH companion finding row
    fails to write. Simulated by swapping the scratch world's `led` shim for a wrapper that
    forwards every call to the real shim EXCEPT one whose positional args include the literal
    kind 'finding', which it deliberately fails -- otel-attest never knows the difference
    between this and a genuine transient write failure, which is exactly the property F7
    exists to make visible via a nonzero exit code."""
    world = "s41oaf7"
    teardown(world)
    print(f"== scaffolding classic world {world} (chain ends {CHAIN_B[-1]}) ==")
    wdir = scaffold_classic(world, CHAIN_B)
    tmps.append(wdir.parent)
    birth_acts(world)
    register_sentry(wdir)

    now = datetime.now(timezone.utc)
    t_stmt = "L6-finding-write-failure target row"
    r = led_stamped(wdir, "decision", t_stmt, session="SESS-L6", actor="author")
    assert r.returncode == 0, r.stdout + r.stderr
    t = row_id_last(world, "decision", t_stmt)

    records = [
        otlp_record(session_id="SESS-L6", event_name="api_request", model="claude-wrong-model",
                     query_source="sdk", expected_model="claude-right-model", ts=now),
    ]
    export_path = wdir.parent / "export.jsonl"
    write_export(export_path, records)

    real_led = wdir / "led"
    real_led_moved = wdir / "led.real"
    shutil.move(str(real_led), str(real_led_moved))
    wrapper = wdir / "led"
    wrapper.write_text(
        "#!/bin/bash\n"
        "for a in \"$@\"; do\n"
        "  if [ \"$a\" = \"finding\" ]; then\n"
        "    echo 'F7 FIXTURE: simulated finding-row write failure' >&2\n"
        "    exit 1\n"
        "  fi\n"
        "done\n"
        f"exec \"{real_led_moved}\" \"$@\"\n",
        encoding="utf-8")
    wrapper.chmod(0o755)

    r = run_otel_attest(wdir, export_path)
    out = r.stdout + r.stderr
    # One api_request event, no matching stamp_invocation (key 1 unavailable) -> the turn-
    # bracketed leg (key 3) grades it: a single non-utility candidate within tolerance of the
    # row's own ts. The grade itself is incidental to this leg (F7 is about the finding-row
    # write failure, not the grade); asserting the concrete grade here still pins the
    # end-to-end shape rather than a vaguer "some grade" check.
    check("L6-verification-lands-finding-fails-nonzero-exit",
          r.returncode != 0
          and f"attested row {t}: grade=turn-bracketed verdict=MISMATCH" in out
          and "F7 FIXTURE: simulated finding-row write failure" in out
          and "finding-row write REFUSED for row {}".format(t) in out,
          f"rc={r.returncode}\n{out}", failures)

    teardown(world)


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    try:
        l4_parser_rejections(failures)
        world_main_check(failures, tmps)
        world_f7_check(failures, tmps)
    finally:
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
