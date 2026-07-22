#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for hooks/pretooluse_change_gate.py's
`decomposition_review` mechanism (BACKLOG "decomposition-review-blocker", maintainer ruling
2026-07-12: "the decomposition's second-pair-of-eyes review must be a BLOCKER for execution, not
backloggable debt -- if the decomposition is wrong, every discharged subtask is waste").

WITNESSED SPECIMEN driving this: run12, where work item task 1 was CLAIMED at 08:58:10 and its
IMPLEMENTATION BEGAN at 08:58:16 -- six seconds later -- while the decomposition's own countersign
verdicts landed only at 09:00:38-09:01:01: execution ran ~2.5 minutes AHEAD of the planning review
that was supposed to gate it.

THE MECHANISM UNDER TEST: a substantive Write/Edit/NotebookEdit ANYWHERE under a wired
SUBJECT_ROOT (deliberately NOT restricted to `is_governed()`'s `*.py`-pattern set -- see the
hook's own module docstring), or a governed-file-mutating Bash command (`bash_mutates_governed()`,
the gate's existing definition), is DENIED unless the CLAIMED work item's `work_opened` ledger row
has been countersigned -- an unsuperseded `review` row, verdict `attest`, from a DISTINCT actor,
itself unsuperseded, regarding that row -- the SAME discharge test kernel/lineage/s15-schema.sql's
`review_gap` view computes for any obligated row. VACUOUS (no additional deny) in a world whose
`countersign_obligation` table carries no rows at all.

Real infra, no mocks: dedicated scratch schemas (192.168.122.1, toy db), torn down before AND
after this file runs. Each mechanism-under-test is isolated in its own temp SUBJECT_ROOT carrying
its own hand-written `.claude/apparatus.json` with change_gate/permit_to_work turned OFF and only
decomposition_review switched on -- so a case's exit code is never confounded by the OTHER two
mechanisms' own (unconditional, in enforce mode) denials (mirrors
seen-red/apparatus-config/run_fixtures.py's temp-SUBJECT_ROOT + hand-written-apparatus.json
convention).

Cases (run in this order -- the ledger is append-only, so the "before discharge" cases MUST run
before the attest row that discharges the obligation is inserted; this doubles as the run12
specimen replay: claim a work item, attempt a write before any review row exists -> deny; add the
attest -> pass):
  a-enforce-deny             -- undischarged obligation, mode=enforce: Write of a GOVERNED (*.py)
                                 path DENIED, teach-text names the work_opened row id and slug and
                                 the discharge path.
  b-observe-allow-warn       -- IDENTICAL DB state, mode=observe: Write ALLOWED (exit 0), but
                                 additionalContext carries the enforce-would-deny warning.
  e-non-governed-file-denied -- the SAME undischarged obligation, mode=enforce, but the target is
                                 a `.md` file -- NOT matched by permit_to_work's own `*.py`
                                 GOVERNED_PATTERNS default -- proving decomposition_review fires
                                 "anywhere in the world", not only on governed-pattern paths.
  f-bash-mutation-deny       -- a `sed -i` Bash command mutating a governed `.py` path, same
                                 undischarged obligation, mode=enforce: DENIED.
  i-bash-db-error-fails-closed -- a Bash mutation with the DB genuinely UNREACHABLE (bogus
                                 LEDGER_DB), mode=enforce, change_gate/permit_to_work both OFF (so
                                 no other check's own unconditional deny can mask the result):
                                 DENIED, teach-text names the check as unavailable. Regression test
                                 for a real defect an independent second-opinion review caught in
                                 this mechanism's first-shipped version (2026-07-12): the bash-side
                                 check bare `except: pass`-ed a DB error, silently ALLOWING the
                                 mutation whenever CHANGE_GATE_MODE was "off"/"observe" -- exactly
                                 the configuration this mechanism exists to matter in on its own.
  [[ discharge: a distinct-actor attest review row is inserted against the work_opened row ]]
  c-discharged-allow         -- the IDENTICAL Write as (a): ALLOWED (exit 0), no
                                 decomposition-review deny text anywhere in the output.
  g-bash-mutation-discharged -- the IDENTICAL Bash command as (f): ALLOWED (exit 0).
  d-vacuous-no-obligations   -- a SEPARATE scratch schema: work item open+claimed, but
                                 countersign_obligation carries ZERO rows for this world at all --
                                 mode=enforce, Write ALLOWED: the gate adds nothing.
  h-pre-s22-fail-open        -- a THIRD scratch schema built from high_watermark_1.sql ALONE (no
                                 s22 -- no work_item_current view at all): mode=enforce, Write
                                 ALLOWED: the check is skipped entirely, byte-held prior behavior.

Usage: python3 seen-red/decomposition-review-blocker/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HOOK = REPO / "hooks" / "pretooluse_change_gate.py"
LINEAGE = REPO / "kernel" / "lineage"

PGHOST, PGDB = fixture_pghost(), "toy"

# three independent scratch schemas -- (main: enforce/observe/discharge sequence),
# (vacuous: open+claimed, zero obligations), (pre-s22: no work_item_current at all).
MAIN = dict(schema="decompdr_main", kern="decompdr_main_kernel", role="decompdr_main_rw")
VAC = dict(schema="decompdr_vac", kern="decompdr_vac_kernel", role="decompdr_vac_rw")
PRE = dict(schema="decompdr_pre", kern="decompdr_pre_kernel", role="decompdr_pre_rw")

PROBE_ROOT = Path(tempfile.gettempdir()) / ".decompdr_probe"
ROOT_ENFORCE = PROBE_ROOT / "enforce"
ROOT_OBSERVE = PROBE_ROOT / "observe"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def psql(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", *args])
    if check and cp.returncode != 0:
        raise RuntimeError(f"psql failed: {' '.join(args)}\n{cp.stdout}\n{cp.stderr}")
    return cp


def drop_schema(spec: dict) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {spec['schema']} CASCADE; "
        f"DROP SCHEMA IF EXISTS {spec['kern']} CASCADE; "
        f"DROP OWNED BY {spec['role']};"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {spec['role']};"])


def teardown() -> None:
    for spec in (MAIN, VAC, PRE):
        drop_schema(spec)
    shutil.rmtree(PROBE_ROOT, ignore_errors=True)


def apply_lineage(spec: dict, files: list[str]) -> None:
    for f in files:
        psql(["-v", f"schema={spec['schema']}", "-v", f"kern={spec['kern']}",
              "-v", f"role={spec['role']}", "-f", str(LINEAGE / f)])


def seed_main() -> tuple[int, str]:
    """MAIN schema: two principals (author, reviewer), an opened+claimed work item
    ('decomp-fixture'), and a countersign_obligation binding the author to the reviewer's scope --
    undischarged (no attest review yet). Returns (work_opened_id, slug)."""
    apply_lineage(MAIN, ["high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
                          "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql"])
    s, k, r = MAIN["schema"], MAIN["kern"], MAIN["role"]
    psql(["-c", f"INSERT INTO {k}.principal(name, agent_class) VALUES "
                f"('decomp-author','model'),('decomp-reviewer','model') ON CONFLICT (name) DO NOTHING;"])
    psql(["-c", f"SET ROLE {r}; "
                f"WITH a AS (SELECT id FROM {k}.principal WHERE name='decomp-author') "
                f"INSERT INTO {s}.ledger(kind, work_slug, work_title, statement, actor) "
                f"SELECT 'work_opened','decomp-fixture','Decomposition fixture item', "
                f"'work_opened: decomp-fixture -- Decomposition fixture item', id FROM a;"])
    psql(["-c", f"SET ROLE {r}; "
                f"WITH a AS (SELECT id FROM {k}.principal WHERE name='decomp-author') "
                f"INSERT INTO {s}.ledger(kind, work_slug, statement, actor) "
                f"SELECT 'work_claimed','decomp-fixture','work_claimed: decomp-fixture', id FROM a;"])
    psql(["-c", f"SET ROLE {r}; "
                f"INSERT INTO {s}.countersign_obligation(scope, assigned_by, obliges_actor) "
                f"SELECT 'decomposition-review', "
                f"(SELECT id FROM {k}.principal WHERE name='decomp-reviewer'), "
                f"(SELECT id FROM {k}.principal WHERE name='decomp-author');"])
    out = psql(["-tA", "-c", f"SELECT id FROM {s}.ledger WHERE kind='work_opened' "
                             f"AND work_slug='decomp-fixture';"])
    return int(out.stdout.strip()), "decomp-fixture"


def discharge_main(work_opened_id: int) -> None:
    """Countersign the work_opened row: an attest review from the DISTINCT reviewer actor.
    independence='self-review' (not 'technical') is a FIXTURE convenience, not a discharge
    requirement: `review_gap`'s own discharge test (and therefore `undischarged_claimed_work_item`,
    which transcribes it) does not read `independence` at all -- only verdict=attest and a distinct
    actor. A 'technical'/'managerial'/'financial' claim additionally requires a VERIFIED
    interception stamp (s17/s21 `validate_independence`), which a raw psql INSERT run outside a
    real Claude Code session never carries -- 'self-review' is the one independence value the
    kernel does NOT gate on a stamp, so it is what a scratch-DB fixture can produce directly. This
    is also a live witness of the disclosed-self-review fallback CLAUDE.md.tmpl documents for solo
    worlds (bootstrap/templates/CLAUDE.md.tmpl point 3)."""
    s, k, r = MAIN["schema"], MAIN["kern"], MAIN["role"]
    psql(["-c", f"SET ROLE {r}; "
                f"WITH rv AS (INSERT INTO {s}.ledger(kind, regards, statement, actor) "
                f"SELECT 'review', {work_opened_id}, "
                f"'decomposition-review-blocker fixture countersign', id "
                f"FROM {k}.principal WHERE name='decomp-reviewer' RETURNING id) "
                f"INSERT INTO {s}.review_detail(ledger_id, verdict, independence, basis) "
                f"SELECT id, 'attest', 'self-review', "
                f"'fixture countersign -- decomposition sound (disclosed self-review, no stamped "
                f"second session available to this scratch-DB fixture)' FROM rv;"])


def seed_vac() -> None:
    """VAC schema: an open+claimed work item, but ZERO countersign_obligation rows anywhere in
    this world -- proves the gate is vacuous, not merely "no obligation for this actor"."""
    apply_lineage(VAC, ["high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
                         "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql"])
    s, k, r = VAC["schema"], VAC["kern"], VAC["role"]
    psql(["-c", f"INSERT INTO {k}.principal(name, agent_class) VALUES "
                f"('decomp-author','model') ON CONFLICT (name) DO NOTHING;"])
    psql(["-c", f"SET ROLE {r}; "
                f"WITH a AS (SELECT id FROM {k}.principal WHERE name='decomp-author') "
                f"INSERT INTO {s}.ledger(kind, work_slug, work_title, statement, actor) "
                f"SELECT 'work_opened','vac-fixture','Vacuous fixture item', "
                f"'work_opened: vac-fixture -- Vacuous fixture item', id FROM a;"])
    psql(["-c", f"SET ROLE {r}; "
                f"WITH a AS (SELECT id FROM {k}.principal WHERE name='decomp-author') "
                f"INSERT INTO {s}.ledger(kind, work_slug, statement, actor) "
                f"SELECT 'work_claimed','vac-fixture','work_claimed: vac-fixture', id FROM a;"])
    # deliberately NO countersign_obligation row anywhere in this schema.


def seed_pre() -> None:
    """PRE schema: high_watermark_1.sql ALONE -- no s22, so work_item_current does not exist."""
    apply_lineage(PRE, ["high_watermark_1.sql"])


def write_apparatus(root: Path, decomp_mode: str) -> None:
    (root / ".claude").mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "apparatus.json").write_text(json.dumps({"mechanisms": {
        "change_gate": {"mode": "off"},
        "permit_to_work": {"mode": "off"},
        "decomposition_review": {"mode": decomp_mode},
    }}), encoding="utf-8")


def run_hook(root: Path, spec: dict, stdin_obj: dict) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    for var in ("E13_SUBJECT_ROOT", "LEDGER_DEPLOYMENT", "GOVERNED_CONFIG",
                "E13_GATE_HOST", "E13_GATE_DB", "E13_GATE_LEDGER", "E13_GATE_STATE",
                "E13_GATE_JOURNAL"):
        env.pop(var, None)
    env["GATE_SUBJECT_ROOT"] = str(root)
    env["LEDGER_HOST"] = PGHOST
    env["LEDGER_DB"] = PGDB
    env["GATE_LEDGER"] = f"{spec['schema']}.ledger"
    env["GATE_STATE"] = str(root / "scratch_state.json")
    env["GATE_JOURNAL"] = str(root / "scratch_journal.jsonl")
    return sh([sys.executable, str(HOOK)], input=json.dumps(stdin_obj), env=env)


def check(name: str, result: subprocess.CompletedProcess[str], expected_exit: int,
          must_contain: list[str], must_not_contain: list[str]) -> bool:
    combined = result.stdout + result.stderr
    ok = result.returncode == expected_exit
    lines = [f"=== {name} ===", f"exit={result.returncode} (expect {expected_exit})"]
    if not ok:
        lines.append("  ^^ FAIL exit code")
    for s in must_contain:
        present = s in combined
        ok = ok and present
        lines.append(f"  [{'ok' if present else 'FAIL'}] +{s!r}")
    for s in must_not_contain:
        absent = s not in combined
        ok = ok and absent
        lines.append(f"  [{'ok' if absent else 'FAIL'}] -{s!r}")
    lines.append(f"  stdout: {result.stdout.strip()[:220]}")
    print("\n".join(lines))
    print()
    return ok


def main() -> int:
    teardown()  # zero residue from a prior interrupted run
    failures: list[str] = []
    try:
        wid, slug = seed_main()
        seed_vac()
        seed_pre()
        write_apparatus(ROOT_ENFORCE, "enforce")
        write_apparatus(ROOT_OBSERVE, "observe")

        target_py = str(ROOT_ENFORCE / "fixture_target.py")
        target_md = str(ROOT_ENFORCE / "fixture_target.md")

        # a: enforce, undischarged, .py -> deny
        r = run_hook(ROOT_ENFORCE, MAIN,
                     {"tool_name": "Write", "tool_input": {"file_path": target_py}, "cwd": str(ROOT_ENFORCE)})
        if not check("a-enforce-deny", r, 2,
                     ["decomposition-review-blocker", f"work_opened row {wid}", "'decomp-fixture'",
                      "./led review", "self-review", '"permissionDecision": "deny"'], []):
            failures.append("a-enforce-deny")

        # b: observe, IDENTICAL undischarged state, .py -> allow + warning
        target_py_b = str(ROOT_OBSERVE / "fixture_target.py")
        r = run_hook(ROOT_OBSERVE, MAIN,
                     {"tool_name": "Write", "tool_input": {"file_path": target_py_b}, "cwd": str(ROOT_OBSERVE)})
        if not check("b-observe-allow-warn", r, 0,
                     ["decomposition-review-blocker", "would DENY under enforce",
                      '"permissionDecision": "allow"'], ['"permissionDecision": "deny"']):
            failures.append("b-observe-allow-warn")

        # e: enforce, undischarged, .md (NOT governed by permit_to_work's *.py pattern) -> deny
        r = run_hook(ROOT_ENFORCE, MAIN,
                     {"tool_name": "Write", "tool_input": {"file_path": target_md}, "cwd": str(ROOT_ENFORCE)})
        if not check("e-non-governed-file-denied", r, 2,
                     ["decomposition-review-blocker", '"permissionDecision": "deny"'], []):
            failures.append("e-non-governed-file-denied")

        # f: enforce, undischarged, Bash sed -i on a governed .py path -> deny
        bash_target = str(ROOT_ENFORCE / "fixture_bash_target.py")
        r = run_hook(ROOT_ENFORCE, MAIN,
                     {"tool_name": "Bash",
                      "tool_input": {"command": f"sed -i 's/a/b/' {bash_target}"},
                      "cwd": str(ROOT_ENFORCE)})
        if not check("f-bash-mutation-deny", r, 2,
                     ["decomposition-review-blocker", '"permissionDecision": "deny"'], []):
            failures.append("f-bash-mutation-deny")

        # i: enforce, Bash mutation, DB genuinely unreachable (bogus LEDGER_DB) -> fails CLOSED
        # (independent-review finding, 2026-07-12: the first-shipped version of this branch bare
        # `except: pass`-ed a DB error, silently ALLOWING the mutation whenever CHANGE_GATE_MODE
        # was "off"/"observe" -- this case is the regression test for that fix).
        root_err = PROBE_ROOT / "db-error"
        write_apparatus(root_err, "enforce")
        bash_target_err = str(root_err / "fixture_bash_target.py")
        env = dict(os.environ)
        for var in ("E13_SUBJECT_ROOT", "LEDGER_DEPLOYMENT", "GOVERNED_CONFIG",
                    "E13_GATE_HOST", "E13_GATE_DB", "E13_GATE_LEDGER", "E13_GATE_STATE",
                    "E13_GATE_JOURNAL"):
            env.pop(var, None)
        env["GATE_SUBJECT_ROOT"] = str(root_err)
        env["LEDGER_HOST"] = PGHOST
        env["LEDGER_DB"] = "decompdr_nonexistent_probe_db"  # deliberately unreachable
        env["GATE_LEDGER"] = "whatever.ledger"
        env["GATE_STATE"] = str(root_err / "scratch_state.json")
        env["GATE_JOURNAL"] = str(root_err / "scratch_journal.jsonl")
        r = sh([sys.executable, str(HOOK)],
               input=json.dumps({"tool_name": "Bash",
                                  "tool_input": {"command": f"sed -i 's/a/b/' {bash_target_err}"},
                                  "cwd": str(root_err)}),
               env=env)
        if not check("i-bash-db-error-fails-closed", r, 2,
                     ["decomposition-review check unavailable", '"permissionDecision": "deny"'], []):
            failures.append("i-bash-db-error-fails-closed")

        # -- discharge: a distinct-actor attest review row against the work_opened row --
        discharge_main(wid)

        # c: enforce, DISCHARGED, .py (identical case to a) -> allow, no decomposition text
        r = run_hook(ROOT_ENFORCE, MAIN,
                     {"tool_name": "Write", "tool_input": {"file_path": target_py}, "cwd": str(ROOT_ENFORCE)})
        if not check("c-discharged-allow", r, 0, [],
                     ["decomposition-review-blocker", '"permissionDecision": "deny"']):
            failures.append("c-discharged-allow")

        # g: enforce, DISCHARGED, Bash sed -i (identical case to f) -> allow
        r = run_hook(ROOT_ENFORCE, MAIN,
                     {"tool_name": "Bash",
                      "tool_input": {"command": f"sed -i 's/a/b/' {bash_target}"},
                      "cwd": str(ROOT_ENFORCE)})
        if not check("g-bash-mutation-discharged", r, 0, [],
                     ["decomposition-review-blocker", '"permissionDecision": "deny"']):
            failures.append("g-bash-mutation-discharged")

        # d: enforce, VACUOUS world (open+claimed item, zero countersign_obligation rows) -> allow
        root_vac = PROBE_ROOT / "vacuous"
        write_apparatus(root_vac, "enforce")
        target_vac = str(root_vac / "fixture_target.py")
        r = run_hook(root_vac, VAC,
                     {"tool_name": "Write", "tool_input": {"file_path": target_vac}, "cwd": str(root_vac)})
        if not check("d-vacuous-no-obligations", r, 0, [],
                     ["decomposition-review-blocker", '"permissionDecision": "deny"']):
            failures.append("d-vacuous-no-obligations")

        # h: enforce, PRE-S22 world (no work_item_current at all) -> allow, fail-open
        root_pre = PROBE_ROOT / "pre-s22"
        write_apparatus(root_pre, "enforce")
        target_pre = str(root_pre / "fixture_target.py")
        r = run_hook(root_pre, PRE,
                     {"tool_name": "Write", "tool_input": {"file_path": target_pre}, "cwd": str(root_pre)})
        if not check("h-pre-s22-fail-open", r, 0, [],
                     ["decomposition-review-blocker", '"permissionDecision": "deny"']):
            failures.append("h-pre-s22-fail-open")
    finally:
        teardown()

    if failures:
        print(f"run_fixtures: {len(failures)} FAILURE(S): {', '.join(failures)}")
        return 1
    print("run_fixtures: all 9 case(s) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
