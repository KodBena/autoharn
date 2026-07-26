#!/usr/bin/env python3
"""seen-red/deploy-feature-manifest/run_fixtures.py -- both-polarity live proof for the
DECLARATIVE FEATURE MANIFEST (work item deploy-feature-manifest, ledger row 1274/1322,
gates/fixture_census.py REGISTRY entry "deploy-feature-manifest").

WHAT THIS PROVES, against the real `bootstrap/new-project.sh` (no mocks, real subprocess calls,
matching every sibling setup_tui/new-project.sh fixture's own Rule 1 bar):

  1. ABSENCE-IS-FAIL-SAFE -- a scaffold given NEITHER `--features-file` NOR any discrete feature
     flag writes `features.json` reflecting exactly TODAY'S unchanged default behavior (portable
     ADRs on, skills vendored, no panel, no makespan declaration, no extra principals) -- the
     ONE enumerated difference from a pre-manifest scaffold (RED-FIRST's own "manifest absent =
     today's scaffold byte-comparable, or differences enumerated").
  2. Each feature DECLINED genuinely changes nothing: `--no-vendored-skills` -> no
     `.claude/skills/`; `makespan_scheduler_tier=off` -> no `resources/` directory at all.
  3. Each feature ENGAGED is genuinely wired: `--panel-extension` -> a real local (never
     network) clone of `tools/autoharn-panel` at `<dest>/panel`, config-discoverable; a
     non-`off` makespan tier -> a `resources/makespan-scheduler.resource-declaration.txt`
     naming the DECLARATIVE-ONLY disposition and its blocker, never a fabricated install claim.
  4. `principal_set` in a run with NO kernel lineage (neither `--new-world` nor
     `--profile tracker`) is REFUSED loudly, before any act -- there is no principal table to
     register into.
  5. `principal_set` in a `--profile tracker` run (kernel lineage present) is APPLIED LIVE
     through the just-written `led` shim -- a real `principal_registered` ledger row, checked by
     direct psql query against the scratch schema.
  6. Malformed manifest input (unknown JSON key, bad TIER value, a discrete flag AND
     `--features-file` both setting the same decision, a reserved principal name) is REFUSED
     loudly with a message naming the exact problem, nothing written, before any act.

Every scratch destination lives under a fixture-owned tempdir; every scratch world this fixture
BIRTHS (case 5 only) is torn down via the real `bootstrap/teardown-world.sh` in a `finally`,
zero residue regardless of outcome. Cases needing a live Postgres host are UNEXERCISED (not
FAILED) when neither HARNESS_PGHOST nor EPISTEMIC_PGHOST is set, matching every sibling
setup_tui/new-project.sh fixture's own convention.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import here is top of file."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
NEW_PROJECT = os.path.join(REPO, "bootstrap", "new-project.sh")
TEARDOWN = os.path.join(REPO, "bootstrap", "teardown-world.sh")
PGHOST = os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST") or ""
# Classic-mode `new-project.sh` (cases 1/2/3/4/6 below) applies NO kernel lineage at all and
# never opens a live connection (verified: a classic-mode scaffold against an UNREACHABLE host
# still exits 0) -- it only writes deployment.json naming a host/db it never dials. Only case 5
# (`--profile tracker`, which DOES apply the kernel lineage and auto-spawns a real boundary
# service against a real schema) needs a REACHABLE host, so only that case is gated on
# HARNESS_PGHOST/EPISTEMIC_PGHOST being set; the classic-mode cases run unconditionally against
# this house-convention scratch address (never dialed unless case 5 also runs).
CLASSIC_HOST = PGHOST or "192.168.122.1"
PGDB = "toy"

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"{label}: {status}{(' -- ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(f"{label}: {detail}")


def run(argv: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, timeout=120, **kw)


def write_manifest(path: str, manifest: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f)


def teardown(world: str) -> None:
    subprocess.run(
        [TEARDOWN, world, "--db", PGDB, "--host", PGHOST, "--force-non-scratch"],
        input=f"{world}\n", capture_output=True, text=True, timeout=60,
    )


# --------------------------------------------------------------------------------------------
# Case 1: absence is fail-safe.
# --------------------------------------------------------------------------------------------

def case_absence(scratch: str) -> None:
    dest = os.path.join(scratch, "case1-absence")
    cp = run([NEW_PROJECT, dest, "--db", PGDB, "--host", CLASSIC_HOST,
              "--schema", "dfmc1", "--kern", "dfmc1_kernel", "--role", "dfmc1_rw"])
    check("case1 scaffold exit", cp.returncode == 0, f"exit {cp.returncode}: {cp.stderr[-800:]}")
    manifest_path = os.path.join(dest, "features.json")
    check("case1 features.json written", os.path.isfile(manifest_path))
    with open(manifest_path) as f:
        manifest = json.load(f)
    expected = {"features_format": 1, "portable_adrs": True, "vendored_skills": True,
                "panel_extension": False, "makespan_scheduler_tier": "off", "principal_set": []}
    check("case1 features.json matches today's unchanged defaults", manifest == expected,
          json.dumps(manifest))
    check("case1 .claude/skills present (unconditional-vendor default unchanged)",
          os.path.isdir(os.path.join(dest, ".claude", "skills")))
    check("case1 no resources/ directory (makespan tier off)",
          not os.path.isdir(os.path.join(dest, "resources")))
    check("case1 no panel/ directory (panel_extension off)",
          not os.path.isdir(os.path.join(dest, "panel")))


# --------------------------------------------------------------------------------------------
# Case 2: declined features change nothing.
# --------------------------------------------------------------------------------------------

def case_declined(scratch: str) -> None:
    dest = os.path.join(scratch, "case2-declined")
    cp = run([NEW_PROJECT, dest, "--db", PGDB, "--host", CLASSIC_HOST,
              "--schema", "dfmc2", "--kern", "dfmc2_kernel", "--role", "dfmc2_rw",
              "--no-vendored-skills"])
    check("case2 scaffold exit", cp.returncode == 0, f"exit {cp.returncode}: {cp.stderr[-800:]}")
    check("case2 .claude/skills NOT written", not os.path.isdir(os.path.join(dest, ".claude", "skills")))
    check("case2 DECLINED line printed", "vendored skills: DECLINED" in cp.stdout)
    with open(os.path.join(dest, "features.json")) as f:
        manifest = json.load(f)
    check("case2 features.json vendored_skills=false", manifest["vendored_skills"] is False)


# --------------------------------------------------------------------------------------------
# Case 3: engaged features are genuinely wired (panel + makespan tier).
# --------------------------------------------------------------------------------------------

def case_engaged(scratch: str) -> None:
    dest = os.path.join(scratch, "case3-engaged")
    panel_src = os.path.join(REPO, "tools", "autoharn-panel", "README.md")
    if not os.path.isfile(panel_src):
        print("case3 (panel leg) UNEXERCISED: tools/autoharn-panel submodule not populated "
              "in this checkout (git submodule update --init --recursive)")
    else:
        cp = run([NEW_PROJECT, dest, "--db", PGDB, "--host", CLASSIC_HOST,
                  "--schema", "dfmc3", "--kern", "dfmc3_kernel", "--role", "dfmc3_rw",
                  "--panel-extension", "--makespan-tier", "blessed"])
        check("case3 scaffold exit", cp.returncode == 0, f"exit {cp.returncode}: {cp.stderr[-800:]}")
        check("case3 panel/README.md present (real local clone)",
              os.path.isfile(os.path.join(dest, "panel", "README.md")))
        check("case3 panel/.git present (a real clone, not a copy)",
              os.path.isdir(os.path.join(dest, "panel", ".git")))
        decl_path = os.path.join(dest, "resources", "makespan-scheduler.resource-declaration.txt")
        check("case3 resources/ declaration written", os.path.isfile(decl_path))
        if os.path.isfile(decl_path):
            text = open(decl_path).read()
            check("case3 declaration names TIER=blessed", "TIER=blessed" in text)
            check("case3 declaration honestly names its NOT-yet-applied blocker",
                  "NOT yet applied" in text and "NOT automated" in text)
        check("case3 stdout admits declarative-only, never a fake 'installed' claim",
              "DECLARATIVE-ONLY" in cp.stdout and "installed" not in cp.stdout.lower())


# --------------------------------------------------------------------------------------------
# Case 4: principal_set with no kernel lineage is refused loudly, before any act.
# --------------------------------------------------------------------------------------------

def case_principal_set_no_kernel(scratch: str) -> None:
    dest = os.path.join(scratch, "case4-no-kernel")
    manifest_path = os.path.join(scratch, "case4-features.json")
    write_manifest(manifest_path, {"principal_set": [
        {"name": "orchestrator-test", "agent_class": "model", "purpose": "probe"}]})
    cp = run([NEW_PROJECT, dest, "--db", PGDB, "--host", CLASSIC_HOST,
              "--schema", "dfmc4", "--kern", "dfmc4_kernel", "--role", "dfmc4_rw",
              "--features-file", manifest_path])
    check("case4 REFUSED (nonzero exit)", cp.returncode != 0, f"exit {cp.returncode}")
    check("case4 refusal names the real reason (no kernel lineage)",
          "no kernel lineage" in cp.stderr and "principal_set" in cp.stderr, cp.stderr[-600:])
    check("case4 nothing written (dest never created)", not os.path.exists(dest))


# --------------------------------------------------------------------------------------------
# Case 5: principal_set IS applied live under --profile tracker (kernel lineage present).
# --------------------------------------------------------------------------------------------

def case_principal_set_live(scratch: str) -> None:
    dest = os.path.join(scratch, "case5-live")
    # --profile tracker's own --name feeds BOTH the boundary-multiplex deployment-name contract
    # ([a-z0-9-]{1,64}, serving/boundary_multiplex_config.py) and the SQL-identifier allowlist
    # ([A-Za-z0-9_]+) it derives --schema/--kern/--role from -- their checked intersection is
    # plain [a-z0-9]{1,64}, no underscore/hyphen (new-project.sh's own cross-reference check) --
    # so this name is pure lowercase alnum, never the "_scratch" suffix teardown-world.sh's own
    # scratch-safe pattern would otherwise recognize (--force-non-scratch below covers that,
    # exactly like seen-red/setup-tui-config-file's own sibling fixture).
    world = "dfmc5live"
    manifest_path = os.path.join(scratch, "case5-features.json")
    write_manifest(manifest_path, {"principal_set": [
        {"name": "orchestrator-fixture", "agent_class": "model", "purpose": "manifest fixture probe"}]})
    try:
        cp = run([NEW_PROJECT, dest, "--profile", "tracker", "--name", world,
                  "--db", PGDB, "--host", PGHOST, "--features-file", manifest_path])
        check("case5 scaffold exit", cp.returncode == 0, f"exit {cp.returncode}: {cp.stderr[-1200:]}")
        check("case5 register-principal-set.sh written",
              os.path.isfile(os.path.join(dest, "register-principal-set.sh")))
        check("case5 stdout reports live WITNESSED application", "principal_set: WITNESSED" in cp.stdout,
              cp.stdout[-800:])
        row = run(["psql", "-h", PGHOST, "-d", PGDB, "-tA", "-c",
                   f"SELECT statement FROM {world}.ledger WHERE kind='principal_registered' "
                   f"AND statement LIKE '%orchestrator-fixture%';"])
        check("case5 real ledger row exists for the declared principal",
              "orchestrator-fixture" in row.stdout, row.stdout)
    finally:
        # This case's own `led register-principal` call auto-spawns the boundary service
        # (ensure-running) -- a live process outliving this function's own scope unless
        # explicitly stopped first. `autoharn service stop` (serving/ensure_running.py's own
        # pidfile-tracked, /proc-reconciled stop path) is the real verb for this, run from
        # INSIDE `dest` (it resolves the pidfile relative to deployment.json there) -- run
        # BEFORE the schema/role teardown and the directory removal, so nothing is torn out
        # from under a still-running child.
        subprocess.run([os.path.join(REPO, "autoharn"), "service", "stop"], cwd=dest,
                        capture_output=True, text=True, timeout=30)
        teardown(world)
        shutil.rmtree(dest, ignore_errors=True)


# --------------------------------------------------------------------------------------------
# Case 6: malformed manifest input refuses loudly, nothing written.
# --------------------------------------------------------------------------------------------

def case_malformed(scratch: str) -> None:
    cases = [
        ("unknown key", {"not_a_real_key": True}, "unknown key"),
        ("bad tier", {"makespan_scheduler_tier": "urgent"}, "must be one of"),
        ("reserved principal name", {"principal_set": [
            {"name": "reviewer", "agent_class": "human", "purpose": "x"}]}, "reserved"),
        ("bad agent_class", {"principal_set": [
            {"name": "x", "agent_class": "alien", "purpose": "y"}]}, "agent_class"),
    ]
    for label, body, needle in cases:
        dest = os.path.join(scratch, f"case6-{label.replace(' ', '-')}")
        manifest_path = os.path.join(scratch, f"case6-{label.replace(' ', '-')}.json")
        write_manifest(manifest_path, body)
        cp = run([NEW_PROJECT, dest, "--db", PGDB, "--host", CLASSIC_HOST,
                  "--schema", "dfmc6", "--kern", "dfmc6_kernel", "--role", "dfmc6_rw",
                  "--features-file", manifest_path])
        check(f"case6 ({label}) REFUSED", cp.returncode != 0, f"exit {cp.returncode}")
        check(f"case6 ({label}) names the problem", needle in cp.stderr, cp.stderr[-400:])
        check(f"case6 ({label}) nothing written", not os.path.exists(dest))

    # discrete-flag / --features-file overlap.
    dest = os.path.join(scratch, "case6-overlap")
    manifest_path = os.path.join(scratch, "case6-overlap.json")
    write_manifest(manifest_path, {"vendored_skills": False})
    cp = run([NEW_PROJECT, dest, "--db", PGDB, "--host", CLASSIC_HOST,
              "--schema", "dfmc6b", "--kern", "dfmc6b_kernel", "--role", "dfmc6b_rw",
              "--no-vendored-skills", "--features-file", manifest_path])
    check("case6 (discrete-flag/features-file overlap) REFUSED", cp.returncode != 0, f"exit {cp.returncode}")
    check("case6 (overlap) names ambiguity", "ambiguous" in cp.stderr, cp.stderr[-400:])


def main() -> int:
    scratch = tempfile.mkdtemp(prefix="deploy-feature-manifest-")
    try:
        # Cases 1/2/3/4/6 are classic-mode scaffolds -- no kernel lineage, no live DB connection
        # ever opened (module-level CLASSIC_HOST comment), so they run regardless of whether a
        # real Postgres host is configured. Only case 5 (--profile tracker, a real kernel +
        # boundary + live `led register-principal`) needs one.
        case_absence(scratch)
        case_declined(scratch)
        case_engaged(scratch)
        case_principal_set_no_kernel(scratch)
        if PGHOST:
            case_principal_set_live(scratch)
        else:
            print("case5 (principal_set live registration) UNEXERCISED: no HARNESS_PGHOST/"
                  "EPISTEMIC_PGHOST -- needs a reachable Postgres host for a real "
                  "--profile tracker birth + live led register-principal call.")
        case_malformed(scratch)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    if FAILURES:
        print(f"\n{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\ndeploy-feature-manifest fixture: all cases PASS, scratch substrate torn down to "
          "zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
