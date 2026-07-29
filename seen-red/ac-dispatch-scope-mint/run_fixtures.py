#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for the dispatch-time scope-minting CLI extension
(design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §5 item 4, ledger rows 639/815, work
item ac-dispatch-scope-mint). Real infra, no mocks: `bootstrap/new-project.sh --new-world` stands
up a scratch, SERVED deployment (LINEAGE_CHAIN already ends at s70-scope-binding.sql on this
tree, verified below rather than assumed) -- boundary service auto-spawned lazily on first read
by `serving/ensure_running.py` (the SAME path every rebased shim already uses, no manual "service
start" needed) -- and `tools/dispatch_mechanics.py mint --scope-*` is invoked as a REAL subprocess
against it, end-to-end through the served boundary, exactly the path a real dispatch takes.

THIS DELTA IS CLI-ONLY (tools/dispatch_mechanics.py) -- kernel/lineage/s70-scope-binding.sql
itself is untouched (already committed, already carries every kernel object this CLI drives);
serving/ and hooks/ are untouched (kernel.ledger_write's payload-key check is a generic
column-name/blocklist check -- verified by reading kernel/lineage/s65-refusal-attempted-
kind.sql's Element 5 before writing a line of this fixture -- already admits scope_surfaces/
scope_exclusions/scope_disclosure_mode the moment a world's kernel carries s70).

CASES (brief's own text, "both polarities, scratch, red first"):
  PRECONDITION-S70-PRESENT               -- the fresh --new-world scratch deployment's own kernel
                                             already carries s70 (LINEAGE_CHAIN's own current
                                             tail), the object this CLI drives.
  CLI-MINT-NO-SCOPE-BYTE-IDENTICAL       -- mint with NO --scope-* flag: no principal_scope_bound
                                             row written, stamp material emitted, exit 0 -- the
                                             RED-then-GREEN regression this delta's own docstring
                                             commits to (an unarmed mint is unchanged).
  CLI-MINT-WITH-SCOPE-ACCEPTED           -- mint --scope-surface / --scope-exclude / --scope-
                                             disclosure-mode (the §3 reviewer-blindness instance:
                                             exclude the commissioning work item's lineage by
                                             PREDICATE, never a hand-enumerated row id):
                                             principal_scope_bound written THROUGH THE SERVED
                                             BOUNDARY, principal_scopes (read via psql, ground
                                             truth) renders it.
  CLI-MALFORMED-FAMILY-CLIENT-REFUSED    -- --scope-exclude with an out-of-vocabulary family:
                                             refused BY THE CLI's OWN TYPED CONSTRUCTOR (no-bare-
                                             types SSOT, ledger row 1105), naming the SAME closed
                                             vocabulary the kernel CHECK enforces, before any
                                             network touch (defense in depth).
  KERNEL-CHECK-BACKSTOP-MALFORMED-FAMILY-REFUSED -- bypassing this CLI's own typed mirror (a raw
                                             POST through the SAME boundary_cli_client.post_write
                                             surface the verb itself calls, hand-built payload):
                                             the KERNEL's OWN scope_exclusions_shape CHECK
                                             independently refuses -- not merely documented,
                                             exercised, end-to-end through the boundary.
  CLI-MINT-SCOPE-DISCLOSURE-MODES        -- marked/hash_stub/full each independently selectable
                                             via --scope-disclosure-mode, all three rendered.
  KERNEL-BACKSTOP-REFUSAL-JOURNALED      -- the kernel-CHECK refusal above is a committed
                                             write_refused row (s43), not merely a client message.
  VERIFY-CHAIN-INTACT                    -- ./autoharn verify-chain, on this world, after every
                                             write above -- INTACT.

Usage: python3 seen-red/ac-dispatch-scope-mint/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports are banned."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "filing"))
from pghost_resolve import resolve_pghost  # noqa: E402

os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"
# Stripped in THIS process too, not just in `sh()`'s own subprocess env dict: this fixture
# calls `boundary_cli_client.write_and_report`/`post_write` DIRECTLY (in-process, for the
# kernel-CHECK-backstop probe below), and that module's own `_read_vendor_stamp_from_env`
# reads `os.environ["PGOPTIONS"]` straight from THIS process to build outgoing vendor-stamp
# HTTP headers -- carrying it forward would forward THIS agent's own interception-hook stamp
# (valid only for autoharn's own REAL deployment secret) onto a fresh scratch world's own
# fresh stamp secret, which the kernel correctly refuses as present-but-invalid (witnessed once
# during this fixture's own build, fixed here rather than routed around).
os.environ.pop("PGOPTIONS", None)

sys.path.insert(0, str(REPO / "serving"))
import boundary_cli_client as bcc  # noqa: E402

sys.path.insert(0, str(REPO / "tools"))
import dispatch_mechanics as dm  # noqa: E402

NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LINEAGE = REPO / "kernel" / "lineage"
PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"
WORLD = "acdscopefx"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    # PGOPTIONS stripped -- see seen-red/s70-scope-binding/run_fixtures.py's own `sh` docstring
    # for why (this agent's own shell carries an interception-stamp GUC valid only for the REAL
    # autoharn deployment, invalid against this fresh scratch world's own fresh stamp secret).
    env = dict(kw.pop("env", os.environ))
    env.pop("PGOPTIONS", None)
    return subprocess.run(args, capture_output=True, text=True, env=env, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown(world: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=0", "-q",
        "-c", f"DROP SCHEMA IF EXISTS {world} CASCADE;",
        "-c", f"DROP SCHEMA IF EXISTS {world}_kernel CASCADE;",
        "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def detect(world: str, sibling: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1",
             "-v", f"schema={world}", "-f", str(LINEAGE / sibling)])
    if cp.returncode != 0:
        raise RuntimeError(f"detect failed: {cp.stderr}")
    return cp.stdout.strip()


def run_mint(world_dir: Path, actor_name: str, argv: list[str]) -> tuple[int, str, str]:
    """Runs the REAL `tools/dispatch_mechanics.py` module as a subprocess (a fresh Python
    process, exactly how `./autoharn dispatch mint ...` invokes it in THIS repo -- dispatch is
    autoharn-repo-specific, not scaffolded into worlds, per the module's own docstring, so this
    scratch world's own dispatcher carries no `dispatch` verb; targeting it directly via
    --deployment is the sanctioned path a real dispatcher's own repo-root `dispatch` verb also
    takes internally). LED_ACTOR resolves the dispatching principal, LEDGER_DEPLOYMENT names the
    scratch world's own deployment.json -- both the module's own documented conventions."""
    env = dict(os.environ)
    env.pop("PGOPTIONS", None)
    env["LED_ACTOR"] = actor_name
    env["LEDGER_DEPLOYMENT"] = str(world_dir / "deployment.json")
    cp = sh([sys.executable, str(REPO / "tools" / "dispatch_mechanics.py"), "mint", *argv],
            env=env, cwd=str(world_dir))
    return cp.returncode, cp.stdout, cp.stderr


def main() -> int:  # noqa: C901
    failures: list[str] = []
    teardown(WORLD)
    world_dir: Path | None = None
    try:
        tmp = Path(tempfile.mkdtemp(prefix=f"{WORLD}-seenred-"))
        world_dir = tmp / WORLD
        # --profile tracker (not --new-world): applies the FULL CURRENT kernel lineage
        # (identical apply list, new-project.sh's own text) AND wires the boundary via
        # ensure-running (a free port picked now, boundary-multiplex.toml written, boundary_url/
        # boundary_deployment written into deployment.json -- nothing STARTED yet, the first
        # served call spawns it lazily) with NO explicit --boundary-url/--boundary-deployment
        # needed -- --new-world alone leaves those two fields null (requires them passed
        # explicitly), which is exactly the "missing boundary_url/boundary_deployment" refusal
        # this fixture hit on its first draft before this was read carefully.
        print(f"== scaffolding --profile tracker {WORLD} (LINEAGE_CHAIN's own current tail) ==")
        r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--profile", "tracker",
                "--name", WORLD, "--db", PGDB, "--host", PGHOST])
        ok = r.returncode == 0 and (world_dir / "deployment.json").exists()
        check("TRACKER-PROFILE-SCAFFOLD", ok,
              f"bootstrap/new-project.sh --profile tracker --name {WORLD} -- exit={r.returncode} "
              f"deployment.json present={(world_dir / 'deployment.json').exists()}"
              + ("" if ok else f"\nstdout={r.stdout[-1500:]}\nstderr={r.stderr[-1500:]}"),
              failures)
        if not ok:
            raise SystemExit

        d = detect(WORLD, "s70-scope-binding.detect.sql")
        check("PRECONDITION-S70-PRESENT", d == "t",
              f"s70-scope-binding.detect.sql on this fresh --new-world scratch deployment: "
              f"{d!r} (expected t -- s70 is already this tree's LINEAGE_CHAIN tail; no per-delta "
              f"apply act needed by this fixture)", failures)

        dep = json.loads((world_dir / "deployment.json").read_text())
        print(f"deployment: schema={dep.get('schema')} boundary_url={dep.get('boundary_url')} "
              f"boundary_deployment={dep.get('boundary_deployment')}")

        # 'author' is seeded automatically by s15-schema.sql itself (new-project.sh's own header
        # comment, ON CONFLICT DO NOTHING) and this birth sequence provisions a genesis seed
        # (new-project.sh's own chain_genesis step) -- 'author' is this world's genesis-chained
        # principal by construction, entitled for every authority-bearing act class including
        # the NINTH (scope_binding) with no further setup.
        author_name = "author"

        # ---- CLI-MINT-NO-SCOPE-BYTE-IDENTICAL (the pre-existing, no-scope mint path,
        # unchanged by this delta) ----
        rc, out, err = run_mint(world_dir, author_name, ["reviewer-plain", "1"])
        check("CLI-MINT-NO-SCOPE-ACCEPTED", rc == 0,
              f"mint with no --scope-* flag -- exit={rc} stdout={out!r} stderr={err!r}", failures)
        check("CLI-MINT-NO-SCOPE-STAMP-MATERIAL",
              "AUTOHARN_MINTED_PRINCIPAL" in out and "LED_ACTOR=reviewer-plain" in out,
              f"stamp material emitted unchanged -- stdout={out!r}", failures)
        rows_plain = psql_tuples(
            f"SELECT count(*) FROM {WORLD}.ledger_current lc "
            f"JOIN {WORLD}_kernel.principal p ON p.id = lc.principal_subject "
            f"WHERE lc.kind = 'principal_scope_bound' AND p.name = 'reviewer-plain';")
        check("CLI-MINT-NO-SCOPE-BYTE-IDENTICAL", rows_plain == "0",
              f"no principal_scope_bound row was written for a plain (no --scope-*) mint -- "
              f"rows={rows_plain} (expected 0 -- fail-safe-additive, no-op-when-unarmed)",
              failures)

        # ---- CLI-MINT-WITH-SCOPE-ACCEPTED (§3's reviewer-blindness instance itself: exclude the
        # commissioning work item's lineage BY PREDICATE, never a hand-enumerated row id) ----
        rc, out, err = run_mint(
            world_dir, author_name,
            ["reviewer-blind", "1",
             "--scope-surface", "ledger_current",
             "--scope-surface", "work_item_current",
             "--scope-exclude", "work-item-lineage:ac-dispatch-scope-mint",
             "--scope-exclude", "kind-class:decision",
             "--scope-disclosure-mode", "marked"])
        check("CLI-MINT-WITH-SCOPE-ACCEPTED", rc == 0,
              f"mint --scope-surface x2 --scope-exclude x2 --scope-disclosure-mode marked -- "
              f"exit={rc} stdout={out!r} stderr={err!r}", failures)
        rendered = psql_tuples(
            f"SELECT ps.scope_surfaces, ps.scope_exclusions, ps.scope_disclosure_mode "
            f"FROM {WORLD}.principal_scopes ps "
            f"JOIN {WORLD}_kernel.principal p ON p.id = ps.subject "
            f"WHERE p.name = 'reviewer-blind';")
        check("CLI-MINT-WITH-SCOPE-RENDERED-IN-VIEW",
              "ledger_current" in rendered and "work_item_current" in rendered
              and "ac-dispatch-scope-mint" in rendered and "kind-class" in rendered
              and "marked" in rendered,
              f"principal_scopes renders the CLI-minted binding, through the served boundary -- "
              f"row: {rendered!r}", failures)

        # ---- CLI-MALFORMED-FAMILY-CLIENT-REFUSED (the CLI's own typed mirror -- no-bare-types
        # SSOT -- refuses BEFORE any network touch) ----
        rc, out, err = run_mint(
            world_dir, author_name,
            ["reviewer-bad-family", "1", "--scope-exclude", "bogus-family:something"])
        check("CLI-MALFORMED-FAMILY-CLIENT-REFUSED",
              rc == 2 and "not a scope-exclusion family" in err
              and "kind-class, thread, work-item-lineage, rows" in err,
              f"mint --scope-exclude bogus-family:... -- exit={rc} stderr={err!r} (expected "
              f"exit 2, message naming the closed 4-member vocabulary)", failures)
        rows_bad = psql_tuples(
            f"SELECT count(*) FROM {WORLD}_kernel.principal WHERE name = 'reviewer-bad-family';")
        check("CLI-MALFORMED-FAMILY-NEVER-REGISTERED", rows_bad == "0",
              f"the CLI refused before EVEN registering the delegate principal (client-side "
              f"parse happens before any write) -- rows={rows_bad}", failures)

        # ---- KERNEL-CHECK-BACKSTOP-MALFORMED-FAMILY-REFUSED: bypass this CLI's own typed
        # mirror entirely (hand-built payload, posted through the SAME boundary_cli_client.
        # post_write surface `cmd_mint` itself calls) -- proves the KERNEL's OWN
        # scope_exclusions_shape CHECK is the true, independent authority, not merely
        # documented, this mirror's agreement with it. ----
        cfg = bcc.load_served_config(world_dir / "deployment.json")
        by_name = dm._principals_by_name(cfg)
        backstop_delegate = "reviewer-backstop-probe"
        reg_rc = bcc.write_and_report(
            cfg.base, "registration",
            {"name": backstop_delegate, "agent_class": "subagent",
             "purpose": "kernel CHECK backstop probe", "actor": by_name[author_name]})
        check("KERNEL-BACKSTOP-PROBE-DELEGATE-REGISTERED", reg_rc == 0,
              f"probe delegate registration -- rc={reg_rc}", failures)
        by_name = dm._principals_by_name(cfg)
        probe_id = by_name.get(backstop_delegate)
        bad_payload = {
            "kind": "principal_scope_bound",
            "statement": "kernel CHECK backstop probe -- malformed exclusion family, bypassing "
                         "this CLI's own client-side mirror on purpose",
            "principal_subject": probe_id,
            "principal_binding_active": True,
            "actor": by_name[author_name],
            "scope_exclusions": [{"family": "bogus-family-past-the-cli", "value": "x"}],
        }
        exit_code, verdict = bcc.post_write(cfg.base, "ledger", bad_payload)
        check("KERNEL-CHECK-BACKSTOP-MALFORMED-FAMILY-REFUSED",
              exit_code == 1 and verdict.get("disposition") == "refused"
              and "scope_exclusions_shape" in (verdict.get("message") or ""),
              f"a hand-built payload with an out-of-vocabulary family, posted THROUGH THE SAME "
              f"served write surface the verb itself calls but bypassing this CLI's own typed "
              f"constructor -- REFUSED by the kernel's OWN scope_exclusions_shape CHECK "
              f"independently -- verdict={verdict}", failures)

        # ---- CLI-MINT-SCOPE-DISCLOSURE-MODES (all three tiers independently selectable) ----
        modes_ok: list[tuple[str, bool]] = []
        for mode in ("marked", "hash_stub", "full"):
            dname = f"reviewer-mode-{mode}"
            rc, out, err = run_mint(world_dir, author_name,
                                     [dname, "1", "--scope-disclosure-mode", mode])
            observed = psql_tuples(
                f"SELECT ps.scope_disclosure_mode FROM {WORLD}.principal_scopes ps "
                f"JOIN {WORLD}_kernel.principal p ON p.id = ps.subject WHERE p.name = '{dname}';")
            modes_ok.append((mode, rc == 0 and observed == mode))
        check("CLI-MINT-SCOPE-DISCLOSURE-MODES", all(ok for _, ok in modes_ok),
              f"marked/hash_stub/full each independently selectable and rendered -- {modes_ok}",
              failures)

        # ---- KERNEL-BACKSTOP-REFUSAL-JOURNALED (s43: the kernel backstop refusal above is a
        # committed write_refused row, not merely a client-observed message) ----
        wr_count = psql_tuples(
            f"SELECT count(*) FROM {WORLD}.ledger WHERE kind = 'write_refused' "
            f"AND refusal_surface = 'ledger' "
            f"AND refusal_message LIKE '%scope_exclusions_shape%';")
        check("KERNEL-BACKSTOP-REFUSAL-JOURNALED", wr_count == "1",
              f"the kernel CHECK backstop refusal above journaled as a committed write_refused "
              f"row (s43) -- count={wr_count}", failures)

        vc = sh(["sh", str(world_dir / "autoharn"), "verify-chain"], cwd=str(world_dir))
        check("VERIFY-CHAIN-INTACT", vc.returncode == 0,
              f"./autoharn verify-chain after every write above -- exit={vc.returncode}\n"
              f"{vc.stdout}{vc.stderr}", failures)

    finally:
        # Stop the boundary service `dispatch_mechanics.py`'s own ensure-running auto-spawned
        # above (this --profile tracker world carries no `service` verb of its own -- that's a
        # root-repo-only umbrella dispatch table entry, per CLAUDE.md -- so this reads the SAME
        # pidfile `serving/ensure_running.py` writes and SIGTERMs it directly, matching every
        # other served-world fixture's own teardown discipline: a process this fixture started
        # does not outlive it).
        if world_dir is not None:
            pidfile = world_dir / ".autoharn-service.pid"
            if pidfile.exists():
                try:
                    pid = int(pidfile.read_text().strip())
                    os.kill(pid, 15)
                except (ValueError, ProcessLookupError, PermissionError):
                    pass
        teardown(WORLD)

    print()
    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
