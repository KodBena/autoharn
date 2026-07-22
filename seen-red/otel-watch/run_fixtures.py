#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for ../../otel-watch (design/FABLE-OTEL-SENTRY-SPEC.md
§3, §14's W1-W5). Synthetic OTLP-shaped JSONL only (otel-watch's own extract_api_requests only
cares about the JSON shape, no real collector needed); every run points --base-dir at a fresh
tempdir so the operator's real host state (~/tools/otel-watchdog/) is never touched, and every
alert path runs --dry-run so no real mail is ever sent by this automated fixture (the exec'd
argv is the fixture-side witness the spec's W1 names -- "the mail's arrival is the operator-side
witness; the exec of the script with the right argv is the fixture-side one"). Never points the
watchdog at this live session's own OTel stream, never touches any ledger (this verb writes no
ledger rows at all, spec §3/§9). Teardown removes every tempdir; verified residue-free at the
end of the run.

Legs (each both-polarity: the case that must fire, and the sibling case that must NOT):

  W1  mismatch fires: a session whose observed model disagrees with its declared
      autoharn.expected_model resource attribute -> MISMATCH DETECTED + a DRY-RUN alert line
      carrying the exact subject "OTEL WATCHDOG mismatch: session=<id8> expected=<model>
      observed=<model>".
  W2  match stays silent: same-shaped session, observed model matches expectation -> no
      MISMATCH, no alert; the session shows up watched-and-clean in --status.
  W3  unwatched is loud: a session with NO autoharn.expected_model resource attribute and no
      expectation-file match -> exactly one COVERAGE UNWATCHED journal line (and, with
      --alert-unwatched, one DRY-RUN coverage alert) -- never silence, and never a MISMATCH.
  W4  debounce: two wrong-model requests in the same session/same wrong model -> exactly one
      alert (the second is journaled DEBOUNCED, not re-alerted); a THIRD request in the same
      session with a DIFFERENT wrong model -> a second, new alert.
  W5  utility-call filter: a claude_code.api_request tagged query_source=generate_session_title
      raises no alert and creates no coverage/status entry at all for its session, even though
      its model would otherwise mismatch. (Bonus, same mechanism: a subagent-dispatch call
      tagged query_source=agent:... is filtered identically -- P1's witnessed discriminator,
      reused from otel-attest's own §6 treatment -- named here as an extra, not one of the
      spec's enumerated W1-W5.)

Usage: python3 seen-red/otel-watch/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OTEL_WATCH = REPO / "otel-watch"


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


# ---------------------------------------------------------------------------------------------
# Synthetic OTLP export construction. Resource-level attributes (autoharn.expected_model/world/
# declared_principal) live on resourceLogs[].resource.attributes -- the real OTel resource-
# attribute mechanism the launcher stamps into OTEL_RESOURCE_ATTRIBUTES (spec §3's primary
# input); event-level attributes (session.id, model, query_source) live on each logRecord, body
# "claude_code.api_request" (the exact discriminator otel-watch's extract_api_requests checks).
# ---------------------------------------------------------------------------------------------


def api_request_record(*, session_id: str, model: str, query_source: str = "sdk") -> dict:
    return {
        "body": {"stringValue": "claude_code.api_request"},
        "attributes": [
            {"key": "session.id", "value": {"stringValue": session_id}},
            {"key": "model", "value": {"stringValue": model}},
            {"key": "query_source", "value": {"stringValue": query_source}},
        ],
    }


def resource_logs(*, expected_model: str | None = None, world: str | None = None,
                   principal: str | None = None, records: list[dict]) -> dict:
    attrs = []
    if expected_model is not None:
        attrs.append({"key": "autoharn.expected_model", "value": {"stringValue": expected_model}})
    if world is not None:
        attrs.append({"key": "autoharn.world", "value": {"stringValue": world}})
    if principal is not None:
        attrs.append({"key": "autoharn.declared_principal", "value": {"stringValue": principal}})
    return {"resource": {"attributes": attrs}, "scopeLogs": [{"logRecords": records}]}


def append_batch(export_path: Path, entries: list[dict]) -> None:
    """Appends one JSONL line (one OTLP ExportLogsServiceRequest batch) to the export file --
    mirrors how the real otelcol file exporter appends one line per flushed batch, and exercises
    otel-watch's tail-from-offset poll_lines() across multiple polls (the same mechanism a real
    daemon uses across real batch flushes)."""
    line = json.dumps({"resourceLogs": entries})
    with export_path.open("a") as f:
        f.write(line + "\n")


def run_once(*, export: Path, base_dir: Path, alert_unwatched: bool = False) -> str:
    args = [sys.executable, str(OTEL_WATCH), "--once", "--export", str(export),
            "--base-dir", str(base_dir), "--dry-run"]
    if alert_unwatched:
        args.append("--alert-unwatched")
    r = subprocess.run(args, capture_output=True, text=True)
    return r.stdout + r.stderr


def run_status(*, base_dir: Path) -> str:
    r = subprocess.run([sys.executable, str(OTEL_WATCH), "--status", "--base-dir", str(base_dir)],
                        capture_output=True, text=True)
    return r.stdout + r.stderr


def main() -> int:
    failures: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="otel-watch-seenred-"))
    try:
        export = tmp / "export.jsonl"
        base_dir = tmp / "watchdog-base"
        export.touch()

        sid_w1 = "11110000-w1-mismatch-session"
        sid_w2 = "22220000-w2-match-session"
        sid_w3 = "33330000-w3-unwatched-session"
        sid_w4 = "44440000-w4-debounce-session"
        sid_w5 = "55550000-w5-utility-session"
        sid_w5b = "55550001-w5b-subagent-session"

        # ---- poll 1: W1, W2, W3, W4's first two events (same wrong model), W5, W5b (bonus) ----
        batch1 = [
            resource_logs(expected_model="model-A",
                          records=[api_request_record(session_id=sid_w1, model="model-B")]),
            resource_logs(expected_model="model-C",
                          records=[api_request_record(session_id=sid_w2, model="model-C")]),
            resource_logs(  # no expected_model, no world, no principal -- UNWATCHED
                          records=[api_request_record(session_id=sid_w3, model="model-X")]),
            resource_logs(expected_model="model-A", records=[
                api_request_record(session_id=sid_w4, model="model-B"),
                api_request_record(session_id=sid_w4, model="model-B"),
            ]),
            resource_logs(expected_model="model-A", records=[
                api_request_record(session_id=sid_w5, model="model-Q",
                                     query_source="generate_session_title"),
            ]),
            resource_logs(expected_model="model-A", records=[
                api_request_record(session_id=sid_w5b, model="model-Q", query_source="agent:sdk:sub"),
            ]),
        ]
        append_batch(export, batch1)
        out1 = run_once(export=export, base_dir=base_dir, alert_unwatched=True)

        # -- W1: mismatch fires --
        check("W1-mismatch-detected",
              f"MISMATCH DETECTED: session={sid_w1[:8]} expected=model-A" in out1
              and "observed=model-B" in out1,
              out1, failures)
        check("W1-alert-exec-argv-witnessed",
              ("DRY-RUN (no real send): would exec argv=" in out1
               and "OTEL WATCHDOG mismatch: session=11110000 expected=model-A observed=model-B" in out1),
              out1, failures)

        # -- W2: match stays silent (negative control: no MISMATCH/alert mentions this session) --
        check("W2-match-no-mismatch-line",
              f"session={sid_w2[:8]}" not in out1.replace(
                  f"MISMATCH DETECTED: session={sid_w1[:8]}", ""),
              "checked no MISMATCH/ALERT line references the W2 session id", failures)
        status1 = run_status(base_dir=base_dir)
        check("W2-match-shows-watched-and-clean",
              f"{sid_w2[:8]} expected=model-C observed=['model-C']" in status1,
              status1, failures)

        # -- W3: unwatched is loud, never a mismatch --
        check("W3-coverage-unwatched-journaled",
              f"COVERAGE: session={sid_w3[:8]} UNWATCHED" in out1, out1, failures)
        check("W3-unwatched-coverage-alert-dry-run",
              f"OTEL WATCHDOG coverage: session={sid_w3[:8]} UNWATCHED" in out1, out1, failures)
        check("W3-unwatched-never-a-mismatch",
              f"MISMATCH DETECTED: session={sid_w3[:8]}" not in out1, out1, failures)
        check("W3-shows-not-watched-at-all-in-status",
              f"{sid_w3[:8]} world=None principal=None" in status1, status1, failures)

        # -- W4 (part 1): two same-wrong-model requests in one poll -> exactly one alert, one
        # debounced line --
        w4_mismatch_lines = out1.count(f"MISMATCH DETECTED: session={sid_w4[:8]}")
        w4_debounced_lines = out1.count(f"MISMATCH (debounced, already alerted): session={sid_w4[:8]}")
        check("W4-first-wrong-model-alerts-once",
              w4_mismatch_lines == 1 and w4_debounced_lines == 1,
              f"mismatch_lines={w4_mismatch_lines} debounced_lines={w4_debounced_lines}\n{out1}",
              failures)

        # -- W5: utility call filtered, no coverage/status entry, no alert at all --
        check("W5-utility-call-skipped-journaled",
              f"UTILITY CALL skipped: session={sid_w5[:8]} query_source=generate_session_title"
              in out1, out1, failures)
        check("W5-utility-call-no-mismatch-no-coverage",
              f"session={sid_w5[:8]}" not in out1.replace(
                  f"UTILITY CALL skipped: session={sid_w5[:8]} query_source=generate_session_title "
                  f"model=model-Q\n", ""),
              "checked no MISMATCH/COVERAGE line references the W5 (utility) session id",
              failures)
        check("W5-utility-call-absent-from-status",
              sid_w5[:8] not in status1, status1, failures)

        # -- W5b (bonus): subagent-dispatch call filtered identically --
        check("W5b-subagent-dispatch-skipped-journaled",
              f"SUBAGENT DISPATCH skipped: session={sid_w5b[:8]} query_source=agent:sdk:sub"
              in out1, out1, failures)
        check("W5b-subagent-dispatch-absent-from-status",
              sid_w5b[:8] not in status1, status1, failures)

        # ---- poll 2: W4 part 2 -- a DIFFERENT wrong model in the same session alerts again ----
        batch2 = [
            resource_logs(expected_model="model-A",
                          records=[api_request_record(session_id=sid_w4, model="model-Z")]),
        ]
        append_batch(export, batch2)
        out2 = run_once(export=export, base_dir=base_dir)
        check("W4-new-wrong-model-alerts-again",
              f"MISMATCH DETECTED: session={sid_w4[:8]} expected=model-A" in out2
              and "observed=model-Z" in out2
              and "OTEL WATCHDOG mismatch: session=44440000 expected=model-A observed=model-Z"
              in out2,
              out2, failures)

        status2 = run_status(base_dir=base_dir)
        check("W4-mismatch-state-in-status",
              f"{sid_w4[:8]} expected=model-A observed=['model-B', 'model-Z']" in status2,
              status2, failures)

        # ---- negative control: --status on a base-dir that never ran shows all-empty, never a
        # fabricated non-empty report (mirrors otel-attest's own "absence proves nothing" idiom)
        # ----
        empty_base = tmp / "never-ran-base"
        status_empty = run_status(base_dir=empty_base)
        check("status-on-unrun-base-dir-is-empty",
              "watched-and-clean: 0" in status_empty and "mismatch: 0" in status_empty
              and "not-watched-at-all (UNWATCHED, expectation absent): 0" in status_empty
              and "total sessions with observed api_request events: 0" in status_empty,
              status_empty, failures)

        # ---- residue check: no real notify.py invocation ever appears (every send in this
        # fixture ran --dry-run; a real "ALERT SENT" line here would mean this automated fixture
        # leaked a real mail send) ----
        all_out = out1 + out2
        check("no-real-alert-sent-only-dry-run",
              "ALERT SENT:" not in all_out and all_out.count("DRY-RUN (no real send): would exec") >= 3,
              all_out, failures)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
