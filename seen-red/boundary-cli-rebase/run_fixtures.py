#!/usr/bin/env python3
"""seen-red/boundary-cli-rebase/run_fixtures.py -- WM5/WM6, design/
FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md §7 (ratified ledger row 1631; the read-surface
amendment, row 1652, is what makes §5's build possible at all -- see design/
FABLE-BOUNDARY-READ-SURFACE-SPEC.md). Real infra, no mocks: a CLASSIC s43-headed scratch world,
a real `serving.boundary_service` uvicorn subprocess, and the REBASED `bootstrap/templates/
led.tmpl`/`distance-to-clean.tmpl` run as actual subprocesses (not imported and called in-
process) -- this is a CLI-surface witness, so it drives the CLI the way an operator would.

  WM5  a rebased shim's KERNEL-refused write: stderr and exit code byte-faithful to the s43
       verdict (exit 1, matching the legacy tool's own exit for a kernel refusal); a BOUNDARY-
       refused write (never reaching the kernel at all) is distinguishably typed -- a DIFFERENT
       nonzero exit code (3), never dressed as a kernel refusal.
  WM6  a ./legacy/ verb runs green against its world after the rebase -- `legacy-led.tmpl`
       (unmodified since its content is byte-identical to the pre-rebase original, save the one-
       line recovery header) still writes via direct psql, independent of the boundary process
       entirely (proven by running it with the boundary process KILLED).

Extended for the legacy-led-retirement phase-1 pass (ledger row 1149, design/FABLE-BOUNDARY-
MULTIPLEX-AND-CLI-REBASE-SPEC.md §5's own extension point):
  WM7  `led work open|claim|depends|close|list|violations|asof` through the boundary path: a
       full open->claim->depends->close cycle, the claim-before-close led-side gate refusing
       red-first, a kernel-refused duplicate-open, and the three reads reflecting the writes.
  WM8  the generic path's ported statement-grammar pre-flight refuses a malformed `estimate:`
       statement red-first (nothing written, verified by a ledger row-count probe before/after),
       and accepts a well-formed one.
  WM9  `led decomposition-review-status` runs against the boundary and reports mode/verdict.
  WM10 `led briefing` is byte-identical to `legacy-led.tmpl briefing` (both no-DB-access, so both
       run against the SAME served_dep with no server dependency for the legacy leg either).
  WM11 differential courtesy check: `legacy-led.tmpl work list/violations/startable/review-gap`
       against the SAME scratch world the rebased WM7/WM12-14 writes just landed on, confirming
       legacy's own (differently formatted, by disclosed design) reads see the identical
       slugs/rows.

Extended AGAIN for phase 1B (same ledger row 1149, coordinator narrowing corrected -- the
remaining four `led work *` sub-verbs and the `actual:`/`outcome:` grammar prefixes):
  WM12 `led work review-gap` / `led work startable` run against the boundary; startable lists
       the still-open, unclaimed slugB and excludes the claimed-then-closed slugA.
  WM13 `led work resolve-violation`, standalone: an unknown target refused red-first, then a
       genuine orphaned_by_retraction violation (created by directly superseding a parent's own
       opening act) resolved green, then a duplicate disposition on the SAME target kernel-
       refused (in-force uniqueness).
  WM14 `led work supersede-cascade`: a dirty starting state (a slug that was never opened)
       refused red-first, then a genuine parent-with-closed-child cascade succeeds end to end
       (retires the closed child's own orphaned_by_retraction violation automatically, opens the
       new parent slug) -- verified against the DB directly that zero violations remain for the
       child and the new parent slug is present in `work list`.

REUSE (ADR-0012 P1): scaffolding helpers imported from seen-red/boundary-service/run_fixtures.py,
the same pattern every sibling suite in this tree already uses.

Usage: python3 seen-red/boundary-cli-rebase/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import datetime
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SIBLING = REPO / "seen-red" / "boundary-service" / "run_fixtures.py"
PYVENV = Path.home() / "w" / "vdc" / "venvs" / "generic" / "bin" / "python"
LED_TMPL = REPO / "bootstrap" / "templates" / "led.tmpl"
LEGACY_LED_TMPL = REPO / "bootstrap" / "templates" / "legacy-led.tmpl"

sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "serving"))
import deployment_record  # noqa: E402

_spec = importlib.util.spec_from_file_location("boundary_service_fixtures", SIBLING)
assert _spec is not None and _spec.loader is not None
bs_fixtures = importlib.util.module_from_spec(_spec)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_spec.loader.exec_module(bs_fixtures)

RUN_SUFFIX = bs_fixtures.RUN_SUFFIX
CHAIN_B = bs_fixtures.CHAIN_B
check = bs_fixtures.check


def run_cli(script: Path, args: list[str], autoharn: Path, deployment: Path,
            env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    # legacy-led.tmpl is a bash script (its own shebang, `#!/usr/bin/env bash`); the rebased
    # templates are all Python -- interpreter chosen from the file's own first-line shebang
    # rather than hardcoding "PYVENV always" (which would silently mis-invoke a bash template as
    # Python source, exactly the failure this comment exists to name after finding it live).
    first_line = script.read_text(encoding="utf-8").splitlines()[0]
    interpreter = ["bash"] if "bash" in first_line else [str(PYVENV)]
    env = dict(os.environ)
    env["AUTOHARN"] = str(autoharn)
    env["PICKUP_DEPLOYMENT"] = str(deployment)
    if env_extra:
        env.update(env_extra)
    return subprocess.run([*interpreter, str(script), *args], capture_output=True, text=True,
                           env=env, timeout=30)


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    procs: list = []
    world = f"cliwm{RUN_SUFFIX}"
    bs_fixtures.teardown(world)
    try:
        print(f"== scaffolding classic world {world} (s43-headed) ==")
        wdir = bs_fixtures.scaffold_classic(world, CHAIN_B)
        tmps.append(wdir.parent)
        author, _svc = bs_fixtures.birth_via_boundary(world)
        cfg_path = bs_fixtures.write_scratch_multiplex_config(wdir.parent, world)
        proc, port = bs_fixtures.start_server(cfg_path)
        procs.append(proc)
        base = f"http://127.0.0.1:{port}/d/{world}"
        up = bs_fixtures.wait_health(base)
        check("setup-server-healthy", up, f"GET /d/{world}/health up={up}", failures)
        if not up:
            raise RuntimeError("server never became healthy")

        # A served-shim deployment.json (the two new keys), and a LEGACY deployment.json (the
        # five-key original, no served keys at all -- proves ./legacy/ needs no boundary fact).
        served_dep = wdir.parent / f"{world}-served-deployment.json"
        rec = deployment_record.DeploymentRecord(
            db=bs_fixtures.PGDB, host=bs_fixtures.PGHOST, schema=world, kern=f"{world}_kernel",
            role=f"{world}_rw", name=world, boundary_url=f"http://127.0.0.1:{port}",
            boundary_deployment=world)
        deployment_record.write_deployment(served_dep, rec)
        legacy_dep = wdir.parent / f"{world}-legacy-deployment.json"
        rec_legacy = deployment_record.DeploymentRecord(
            db=bs_fixtures.PGDB, host=bs_fixtures.PGHOST, schema=world, kern=f"{world}_kernel",
            role=f"{world}_rw", name=world)
        deployment_record.write_deployment(legacy_dep, rec_legacy)

        # ==================== WM5a: KERNEL refusal, byte-faithful exit code ====================
        print("== WM5a: kernel-refused write (segregation of duties) -> exit 1 ==")
        note = run_cli(LED_TMPL, ["note", f"WM5 fixture note {RUN_SUFFIX}"], REPO, served_dep)
        check("wm5a-setup-note-write-accepted", note.returncode == 0 and "written" in note.stdout,
              f"exit={note.returncode} stdout={note.stdout!r} stderr={note.stderr!r}", failures)
        # Extract the written row id from "led: row <id> written."
        m = re.search(r"row (\d+) written", note.stdout)
        row_id = int(m.group(1)) if m else None
        check("wm5a-parsed-row-id", row_id is not None, f"parsed from: {note.stdout!r}", failures)
        kernel_refused = run_cli(LED_TMPL, ["review", str(row_id), "attest", "self-review",
                                              "self-countersign, must refuse"], REPO, served_dep)
        check("wm5a-kernel-refusal-exit-1-and-teach-text",
              kernel_refused.returncode == 1
              and "REFUSED by the kernel write boundary" in kernel_refused.stderr
              and "segregation of duties" in kernel_refused.stderr
              and "SQLSTATE" in kernel_refused.stderr,
              f"exit={kernel_refused.returncode} stderr={kernel_refused.stderr!r}", failures)

        # ==================== WM5b: BOUNDARY refusal, distinguishably typed =====================
        print("== WM5b: a GENUINE boundary-typed refusal (never reaches the kernel) -> exit 3, "
              "never exit 1 -- an out-of-range id-domain field, typed 422 by "
              "serving/boundary_service.py's own A5.2 write-body id-domain closure ==")
        oor_json = wdir.parent / "oor-payload.json"
        oor_json.write_text(json.dumps({"kind": "note", "statement": "oor probe",
                                         "supersedes": 2**63}), encoding="utf-8")
        boundary_refused = run_cli(LED_TMPL, ["--json", "ledger", str(oor_json)], REPO, served_dep)
        check("wm5b-boundary-typed-422-is-exit-3-never-exit-1",
              boundary_refused.returncode == 3
              and "REFUSED by the boundary SERVICE itself" in boundary_refused.stderr
              and "NOT a kernel verdict" in boundary_refused.stderr,
              f"exit={boundary_refused.returncode} (must be 3, never 1 -- a boundary-typed "
              f"422 must never be dressed as a kernel refusal) stderr="
              f"{boundary_refused.stderr!r}", failures)
        # A CLIENT-side refusal (never even reaches the boundary): a malformed local JSON file.
        bad_json = wdir.parent / "bad-payload.json"
        bad_json.write_text("{not valid json", encoding="utf-8")
        client_refused = run_cli(LED_TMPL, ["--json", "ledger", str(bad_json)], REPO, served_dep)
        check("wm5b-client-side-malformed-json-never-exit-1",
              client_refused.returncode not in (0, 1),
              f"exit={client_refused.returncode} stderr={client_refused.stderr!r}", failures)
        # A CLIENT-side refusal (missing deployment record) -- exit 4, distinct from 1 and 3.
        unknown_view = run_cli(LED_TMPL, ["question-status"], REPO,
                                wdir.parent / "does-not-exist.json")
        check("wm5b-missing-deployment-record-exit-4-not-1",
              unknown_view.returncode == 4 and unknown_view.returncode != 1,
              f"exit={unknown_view.returncode} stderr={unknown_view.stderr!r}", failures)

        # ============ WM7: full work open->claim->depends->close cycle, boundary path =============
        print("== WM7: led work open|claim|depends|close cycle through the boundary path ==")
        slugA = f"wm7-a-{RUN_SUFFIX}"
        slugB = f"wm7-b-{RUN_SUFFIX}"
        r_open_a = run_cli(LED_TMPL, ["work", "open", slugA, "WM7 item A"], REPO, served_dep)
        check("wm7-open-a", r_open_a.returncode == 0 and "written" in r_open_a.stdout,
              f"exit={r_open_a.returncode} stdout={r_open_a.stdout!r} stderr={r_open_a.stderr!r}",
              failures)
        r_open_b = run_cli(LED_TMPL, ["work", "open", slugB, "WM7 item B"], REPO, served_dep)
        check("wm7-open-b", r_open_b.returncode == 0, f"exit={r_open_b.returncode}", failures)
        r_dup_open = run_cli(LED_TMPL, ["work", "open", slugA, "duplicate open"], REPO, served_dep)
        check("wm7-duplicate-open-kernel-refused-exit-1", r_dup_open.returncode == 1,
              f"exit={r_dup_open.returncode} stderr={r_dup_open.stderr!r}", failures)
        r_depends = run_cli(LED_TMPL, ["work", "depends", slugA, slugB, "--type", "blocks-close"],
                             REPO, served_dep)
        check("wm7-depends", r_depends.returncode == 0,
              f"exit={r_depends.returncode} stdout={r_depends.stdout!r} stderr={r_depends.stderr!r}",
              failures)
        r_close_before_claim = run_cli(LED_TMPL, ["work", "close", slugA, "dropped",
                                                    "--review-deferred"], REPO, served_dep)
        check("wm7-close-before-claim-refused-led-side",
              r_close_before_claim.returncode == 1
              and "has no work_claimed row" in r_close_before_claim.stderr,
              f"exit={r_close_before_claim.returncode} stderr={r_close_before_claim.stderr!r}",
              failures)
        r_claim = run_cli(LED_TMPL, ["work", "claim", slugA], REPO, served_dep)
        check("wm7-claim", r_claim.returncode == 0 and "written" in r_claim.stdout,
              f"exit={r_claim.returncode} stdout={r_claim.stdout!r} stderr={r_claim.stderr!r}",
              failures)
        r_close = run_cli(LED_TMPL, ["work", "close", slugA, "dropped", "--review-deferred"],
                           REPO, served_dep)
        check("wm7-close", r_close.returncode == 0 and "written" in r_close.stdout,
              f"exit={r_close.returncode} stdout={r_close.stdout!r} stderr={r_close.stderr!r}",
              failures)
        r_list = run_cli(LED_TMPL, ["work", "list", "--all"], REPO, served_dep)
        list_rows = [json.loads(ln) for ln in r_list.stdout.splitlines() if ln.strip()]
        list_slugs = {r.get("slug") for r in list_rows}
        check("wm7-list-shows-both-slugs", {slugA, slugB} <= list_slugs,
              f"exit={r_list.returncode} slugs={list_slugs} stderr={r_list.stderr!r}", failures)
        closed_row = next((r for r in list_rows if r.get("slug") == slugA), None)
        check("wm7-list-slugA-state-closed", closed_row is not None and closed_row.get("state") == "closed",
              f"row={closed_row}", failures)
        r_list_default = run_cli(LED_TMPL, ["work", "list"], REPO, served_dep)
        default_slugs = {json.loads(ln).get("slug") for ln in r_list_default.stdout.splitlines() if ln.strip()}
        check("wm7-list-default-excludes-closed-slugA", slugA not in default_slugs,
              f"default_slugs={default_slugs}", failures)
        r_violations = run_cli(LED_TMPL, ["work", "violations"], REPO, served_dep)
        check("wm7-violations-runs-clean", r_violations.returncode == 0,
              f"exit={r_violations.returncode} stdout={r_violations.stdout!r} "
              f"stderr={r_violations.stderr!r}", failures)
        r_asof = run_cli(LED_TMPL, ["work", "asof",
                                     datetime.datetime.now(datetime.timezone.utc).isoformat()],
                          REPO, served_dep)
        asof_rows = [json.loads(ln) for ln in r_asof.stdout.splitlines() if ln.strip()]
        asof_slugA = next((r for r in asof_rows if r.get("slug") == slugA), None)
        check("wm7-asof-slugA-closed", asof_slugA is not None and asof_slugA.get("state_asof") == "closed",
              f"exit={r_asof.returncode} row={asof_slugA} stderr={r_asof.stderr!r}", failures)

        # ==================== WM8: grammar pre-flight refusal, red-first =========================
        print("== WM8: generic path's statement-grammar pre-flight refuses a malformed 'estimate:' ==")
        before_count = bs_fixtures.psql_tuples(f"SELECT count(*) FROM {world}.ledger;")
        r_bad_grammar = run_cli(LED_TMPL, ["note", "estimate: bad|only-three-fields|nope"],
                                 REPO, served_dep)
        check("wm8-malformed-estimate-refused-exit-1",
              r_bad_grammar.returncode == 1
              and "malformed 'estimate:' statement" in r_bad_grammar.stderr
              and "NOTHING was written" in r_bad_grammar.stderr,
              f"exit={r_bad_grammar.returncode} stderr={r_bad_grammar.stderr!r}", failures)
        after_count = bs_fixtures.psql_tuples(f"SELECT count(*) FROM {world}.ledger;")
        check("wm8-malformed-estimate-nothing-written", before_count == after_count,
              f"before={before_count!r} after={after_count!r}", failures)
        r_good_grammar = run_cli(LED_TMPL, ["note", "estimate: wm7-task | 1-2 | 0 | 5m | 1K | "
                                             "a basis"], REPO, served_dep)
        check("wm8-well-formed-estimate-accepted",
              r_good_grammar.returncode == 0 and "written" in r_good_grammar.stdout,
              f"exit={r_good_grammar.returncode} stdout={r_good_grammar.stdout!r} "
              f"stderr={r_good_grammar.stderr!r}", failures)
        # actual:/outcome: (phase 1B, ledger row 1149) -- same both-polarity discipline.
        r_bad_actual = run_cli(LED_TMPL, ["note", "actual: bad|only-two-fields"], REPO, served_dep)
        check("wm8-malformed-actual-refused-red-first",
              r_bad_actual.returncode == 1 and "malformed 'actual:' statement" in r_bad_actual.stderr
              and "NOTHING was written" in r_bad_actual.stderr,
              f"exit={r_bad_actual.returncode} stderr={r_bad_actual.stderr!r}", failures)
        r_good_actual = run_cli(LED_TMPL, ["note", "actual: wm7-task | 2 | 0 | 6m | 500 | harness"],
                                 REPO, served_dep)
        check("wm8-well-formed-actual-accepted",
              r_good_actual.returncode == 0 and "written" in r_good_actual.stdout,
              f"exit={r_good_actual.returncode} stdout={r_good_actual.stdout!r} "
              f"stderr={r_good_actual.stderr!r}", failures)
        r_bad_outcome = run_cli(LED_TMPL, ["note", "outcome: bad|sonnet|verdict-only"], REPO, served_dep)
        check("wm8-malformed-outcome-refused-red-first",
              r_bad_outcome.returncode == 1 and "malformed 'outcome:' statement" in r_bad_outcome.stderr
              and "NOTHING was written" in r_bad_outcome.stderr,
              f"exit={r_bad_outcome.returncode} stderr={r_bad_outcome.stderr!r}", failures)
        r_good_outcome = run_cli(LED_TMPL, ["note", "outcome: wm7-task | sonnet | clean | none | none"],
                                  REPO, served_dep)
        check("wm8-well-formed-outcome-accepted",
              r_good_outcome.returncode == 0 and "written" in r_good_outcome.stdout,
              f"exit={r_good_outcome.returncode} stdout={r_good_outcome.stdout!r} "
              f"stderr={r_good_outcome.stderr!r}", failures)

        # ================= WM9: decomposition-review-status / WM10: briefing =====================
        print("== WM9: led decomposition-review-status / WM10: led briefing ==")
        r_drs = run_cli(LED_TMPL, ["decomposition-review-status"], REPO, served_dep)
        check("wm9-decomposition-review-status-runs",
              r_drs.returncode == 0 and "mode:" in r_drs.stdout and "verdict:" in r_drs.stdout,
              f"exit={r_drs.returncode} stdout={r_drs.stdout!r} stderr={r_drs.stderr!r}", failures)
        r_briefing_rebased = run_cli(LED_TMPL, ["briefing"], REPO, served_dep)
        r_briefing_legacy = run_cli(LEGACY_LED_TMPL, ["briefing"], REPO, served_dep)
        check("wm10-briefing-byte-identical-to-legacy",
              r_briefing_rebased.returncode == 0 and r_briefing_rebased.returncode == r_briefing_legacy.returncode
              and r_briefing_rebased.stdout == r_briefing_legacy.stdout,
              f"rebased_exit={r_briefing_rebased.returncode} legacy_exit={r_briefing_legacy.returncode} "
              f"equal={r_briefing_rebased.stdout == r_briefing_legacy.stdout}", failures)

        # ======== WM12: led work review-gap / startable (phase 1B, ledger row 1149) ==============
        print("== WM12: led work review-gap / led work startable ==")
        r_rg = run_cli(LED_TMPL, ["work", "review-gap"], REPO, served_dep)
        check("wm12-review-gap-runs-clean", r_rg.returncode == 0,
              f"exit={r_rg.returncode} stdout={r_rg.stdout!r} stderr={r_rg.stderr!r}", failures)
        r_startable = run_cli(LED_TMPL, ["work", "startable"], REPO, served_dep)
        startable_slugs = {json.loads(ln).get("slug") for ln in r_startable.stdout.splitlines() if ln.strip()}
        check("wm12-startable-lists-unclaimed-open-slugB",
              r_startable.returncode == 0 and slugB in startable_slugs and slugA not in startable_slugs,
              f"exit={r_startable.returncode} slugs={startable_slugs} stderr={r_startable.stderr!r}",
              failures)

        # === WM13: led work resolve-violation, standalone (ordinary, non-ambiguous, non-cascade) ===
        print("== WM13: led work resolve-violation, standalone (red-first, then green) ==")
        r_rv_bad = run_cli(LED_TMPL, ["work", "resolve-violation", "999999999", "retired",
                                       "no such target", "--review-deferred"], REPO, served_dep)
        check("wm13-resolve-violation-unknown-target-refused-red-first",
              r_rv_bad.returncode == 1 and "not currently an in-force" in r_rv_bad.stderr,
              f"exit={r_rv_bad.returncode} stderr={r_rv_bad.stderr!r}", failures)
        slugQ = f"wm13-q-{RUN_SUFFIX}"
        slugR = f"wm13-r-{RUN_SUFFIX}"
        run_cli(LED_TMPL, ["work", "open", slugQ, "WM13 parent Q"], REPO, served_dep)
        run_cli(LED_TMPL, ["work", "open", slugR, "WM13 child R", "--parent", slugQ], REPO, served_dep)
        # Q's own opening row id, read as ground truth off the DB directly (not a CLI round-trip).
        q_open_id = bs_fixtures.psql_tuples(
            f"SELECT id FROM {world}.ledger_current WHERE kind='work_opened' AND work_slug='{slugQ}';")
        r_supersede_q = run_cli(LED_TMPL, ["work", "open", f"{slugQ}-v2", "WM13 parent Q v2",
                                            "--supersedes", q_open_id], REPO, served_dep)
        check("wm13-setup-supersede-q-orphans-r",
              r_supersede_q.returncode == 0, f"exit={r_supersede_q.returncode} "
              f"stdout={r_supersede_q.stdout!r} stderr={r_supersede_q.stderr!r}", failures)
        r_target = bs_fixtures.psql_tuples(
            f"SELECT target_id FROM {world}.work_item_violations WHERE violation="
            f"'orphaned_by_retraction' AND slug='{slugR}';")
        check("wm13-setup-r-shows-as-orphaned", r_target.strip() != "",
              f"work_item_violations target_id query result: {r_target!r}", failures)
        r_rv_good = run_cli(LED_TMPL, ["work", "resolve-violation", r_target.strip(), "retired",
                                        "WM13 standalone resolution, dormant until R closes",
                                        "--review-deferred"], REPO, served_dep)
        check("wm13-resolve-violation-accepted",
              r_rv_good.returncode == 0 and "written" in r_rv_good.stdout,
              f"exit={r_rv_good.returncode} stdout={r_rv_good.stdout!r} stderr={r_rv_good.stderr!r}",
              failures)
        r_rv_dup = run_cli(LED_TMPL, ["work", "resolve-violation", r_target.strip(), "retired",
                                       "duplicate attempt", "--review-deferred"], REPO, served_dep)
        check("wm13-resolve-violation-duplicate-kernel-refused",
              r_rv_dup.returncode == 1,
              f"exit={r_rv_dup.returncode} stderr={r_rv_dup.stderr!r}", failures)

        # ============ WM14: led work supersede-cascade (composition, closed-child branch) ========
        print("== WM14: led work supersede-cascade -- closed-child orphan disposal ==")
        r_cascade_bad = run_cli(LED_TMPL, ["work", "supersede-cascade", "no-such-slug-at-all",
                                            "irrelevant-new-slug", "title"], REPO, served_dep)
        check("wm14-supersede-cascade-dirty-state-refused-red-first",
              r_cascade_bad.returncode == 1 and "not currently an in-force" in r_cascade_bad.stderr,
              f"exit={r_cascade_bad.returncode} stderr={r_cascade_bad.stderr!r}", failures)
        slugP = f"wm14-p-{RUN_SUFFIX}"
        slugC = f"wm14-c-{RUN_SUFFIX}"
        slugP2 = f"wm14-p2-{RUN_SUFFIX}"
        run_cli(LED_TMPL, ["work", "open", slugP, "WM14 parent P"], REPO, served_dep)
        run_cli(LED_TMPL, ["work", "open", slugC, "WM14 child C", "--parent", slugP], REPO, served_dep)
        run_cli(LED_TMPL, ["work", "claim", slugC], REPO, served_dep)
        r_close_c = run_cli(LED_TMPL, ["work", "close", slugC, "dropped", "--review-deferred"],
                             REPO, served_dep)
        check("wm14-setup-close-c", r_close_c.returncode == 0,
              f"exit={r_close_c.returncode} stderr={r_close_c.stderr!r}", failures)
        r_cascade = run_cli(LED_TMPL, ["work", "supersede-cascade", slugP, slugP2, "WM14 parent P v2"],
                             REPO, served_dep)
        check("wm14-supersede-cascade-succeeds",
              r_cascade.returncode == 0
              and "done" in r_cascade.stderr,
              f"exit={r_cascade.returncode} stdout={r_cascade.stdout!r} stderr={r_cascade.stderr!r}",
              failures)
        remaining = bs_fixtures.psql_tuples(
            f"SELECT count(*) FROM {world}.work_item_violations WHERE slug='{slugC}';")
        check("wm14-cascade-resolved-the-closed-child-orphan", remaining.strip() == "0",
              f"remaining violations for {slugC}: {remaining!r}", failures)
        r_list_p2 = run_cli(LED_TMPL, ["work", "list", "--all"], REPO, served_dep)
        p2_present = any(json.loads(ln).get("slug") == slugP2 for ln in r_list_p2.stdout.splitlines()
                          if ln.strip())
        check("wm14-cascade-new-parent-slug-present", p2_present,
              f"stdout={r_list_p2.stdout!r}", failures)

        # ================= WM11: differential courtesy check, legacy vs rebased ==================
        print("== WM11: legacy `led work list`/`led work violations`/`review-gap`/`startable` vs "
              "rebased, same world ==")
        legacy_list = run_cli(LEGACY_LED_TMPL, ["work", "list", "--all"], REPO, served_dep)
        check("wm11-legacy-list-names-every-rebased-slug",
              legacy_list.returncode == 0 and all(s in legacy_list.stdout for s in (slugA, slugB)),
              f"exit={legacy_list.returncode} stdout={legacy_list.stdout!r}", failures)
        legacy_violations = run_cli(LEGACY_LED_TMPL, ["work", "violations"], REPO, served_dep)
        rebased_violations = run_cli(LED_TMPL, ["work", "violations"], REPO, served_dep)
        check("wm11-violations-both-run-clean-same-world",
              legacy_violations.returncode == 0 and rebased_violations.returncode == 0,
              f"legacy_exit={legacy_violations.returncode} rebased_exit={rebased_violations.returncode} "
              f"legacy_stdout={legacy_violations.stdout!r} rebased_stdout={rebased_violations.stdout!r}",
              failures)
        legacy_startable = run_cli(LEGACY_LED_TMPL, ["work", "startable"], REPO, served_dep)
        check("wm11-legacy-startable-names-same-slugB",
              legacy_startable.returncode == 0 and slugB in legacy_startable.stdout
              and slugA not in legacy_startable.stdout,
              f"exit={legacy_startable.returncode} stdout={legacy_startable.stdout!r}", failures)
        legacy_review_gap = run_cli(LEGACY_LED_TMPL, ["work", "review-gap"], REPO, served_dep)
        check("wm11-legacy-review-gap-runs-clean-same-world", legacy_review_gap.returncode == 0,
              f"exit={legacy_review_gap.returncode} stdout={legacy_review_gap.stdout!r} "
              f"stderr={legacy_review_gap.stderr!r}", failures)

        # ==================== WM6: ./legacy/ verb runs green, boundary KILLED =====================
        print("== WM6: legacy-led.tmpl runs green against its world with the boundary DEAD ==")
        bs_fixtures.stop_server(proc)
        procs.remove(proc)
        legacy_write = run_cli(LEGACY_LED_TMPL, ["note", f"WM6 legacy note {RUN_SUFFIX}"], REPO,
                                legacy_dep)
        check("wm6-legacy-led-writes-with-boundary-dead",
              legacy_write.returncode == 0 and "row" in legacy_write.stdout
              and "written" in legacy_write.stdout,
              f"exit={legacy_write.returncode} stdout={legacy_write.stdout!r} "
              f"stderr={legacy_write.stderr!r}", failures)
        verify = bs_fixtures.psql_tuples(
            f"SELECT count(*) FROM {world}.ledger WHERE statement = 'WM6 legacy note {RUN_SUFFIX}';")
        check("wm6-legacy-write-actually-landed", verify.strip() == "1",
              f"count query result: {verify!r}", failures)

    finally:
        for proc in procs:
            bs_fixtures.stop_server(proc)
        bs_fixtures.teardown(world)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    print()
    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL WM5/WM6/WM7/WM8/WM9/WM10/WM11/WM12/WM13/WM14 CHECKS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
