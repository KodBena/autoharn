#!/usr/bin/env python3
"""run_fixtures.py -- proof for autoharn3 work item scaffold-courier-verb-gap (ledger row 101,
maintainer-amended 2026-07-28): bootstrap/new-project.sh's world-dispatcher generation (the
`_write_world_dispatcher()` function shared by the ordinary --new-world/--profile scaffold flow
and the new --refresh-dispatcher mode) derives its verb roster from the bootstrap/templates/*.tmpl
directory glob (minus the enumerated NON_VERB_TEMPLATES exclusion list), not a hand-maintained
table -- so a template that exists IS a verb, and a template landing in bootstrap/templates/
without the '# autoharn-verb-desc: ...' header line refuses generation loudly rather than
silently shipping a blank description or, worse, silently NOT shipping the verb.

FIX-ROUND ADDENDUM (fresh-context re-review of commit c395071, 2026-07-28 -- routing/exclusions/
original-six-case fixtures CONFIRMED-SOUND, two MODERATE honesty-of-output findings, both fixed
in the same round this addendum documents):

  FINDING 1: the missing-header refusal's own "Nothing was touched" claim was true on the
  CLASSIC-mode path this family's original case exercised, but FALSE on the --new-world path --
  _write_world_dispatcher() ran near the END of the scaffold sequence, discovering a broken
  template only AFTER deployment.json/.autoharn-world.json/.gitignore/.claude/*/keys/
  attestations/roles/ (and, on --new-world, live kernel DDL) were already written. Fixed by
  factoring the glob-plus-header validation into `_scan_verb_templates()` and calling it at the
  EARLIEST point TEMPLATES becomes resolvable on every scaffold path -- before ANY write, DB
  included. Case `missing-header-refuses-new-world-db-untouched` below is the new, stronger
  witness (a REAL --new-world attempt, real Postgres, asserting no schema/role was created).

  FINDING 2: `--refresh-dispatcher` (and any --force re-scaffold sharing the same function) used
  to `cat >` straight over an existing ./autoharn, discarding a hand-edited file with no trace.
  Fixed: the new content is compared byte-for-byte against any existing file first, and exactly
  one of three named things happens -- SKIPPED-IDENTICAL (no write), REPLACED (the differing
  prior file moved to ./autoharn.pre-refresh before the new one lands), or fresh-write (no prior
  file existed). Three new cases below witness each leg, including that the backup byte-matches
  the pre-refresh original.

REAL SCAFFOLD, NO MOCKS: cases 1-6 run bootstrap/new-project.sh in its CLASSIC (non-`--new-world`)
mode against throwaway scratch destinations (classic mode never touches postgres -- every `psql`
call in new-project.sh sits behind `if [ -n "$NEW_WORLD" ]`). Case 7 (missing-header-refuses-
new-world-db-untouched) is the one exception: a REAL `--new-world` scaffold against a REAL
scratch Postgres host, because that is the exact path finding 1 was about -- proving the fix
requires proving the DB, not just the filesystem, is untouched.

Cases:
  GREEN dispatcher-lists-courier      a fresh classic scaffold's ./autoharn --help lists
                                       'courier' (the new template this work item adds) among
                                       its verb roster, and `./autoharn courier --help` reaches
                                       the real courier.tmpl (not an unrecognized-verb refusal).
  GREEN unknown-verb-still-refuses    the roster-derivation rewrite did not disturb the
                                       existing unrecognized-verb teaching refusal (exit 2, named
                                       roster).
  RED   missing-header-refuses-generation
                                       a bootstrap/templates/*.tmpl file with no
                                       '# autoharn-verb-desc: ...' header line makes the WHOLE
                                       scaffold run refuse (exit 2), naming the offending file
                                       and the header/NON_VERB_TEMPLATES remedy -- run against a
                                       throwaway COPY of this checkout (never this repo's own
                                       real templates) so the negative control cannot leave a
                                       stray mutation in the working tree.
  RED   missing-header-refuses-new-world-db-untouched
                                       (finding 1) the SAME broken template copy, this time
                                       driven via a REAL `--new-world` scaffold against a REAL
                                       scratch Postgres schema -- refuses (exit 2) before the
                                       destination directory carries ANY file AND before the
                                       world's schema/kernel-schema/role exist in Postgres at
                                       all (queried live, not inferred).
  GREEN refresh-dispatcher-upgrades   `--refresh-dispatcher <world-dir>` rewrites ONLY that
                                       world's ./autoharn from the CURRENT template roster
                                       (proven by hand-installing a stale, pre-courier dispatcher
                                       stub over a freshly scaffolded world, then refreshing it
                                       and observing 'courier' reappear) -- and touches nothing
                                       else in that world (deployment.json byte-identical).
  RED   refresh-dispatcher-refuses-non-world
                                       `--refresh-dispatcher` against a directory with no
                                       deployment.json refuses (exit 1), naming the missing file,
                                       and creates nothing.
  GREEN refresh-dispatcher-skipped-identical
                                       (finding 2, leg 1) refreshing an UNCHANGED, just-scaffolded
                                       world prints SKIPPED-IDENTICAL, writes nothing, and creates
                                       no .pre-refresh backup.
  GREEN refresh-dispatcher-replaces-with-backup
                                       (finding 2, leg 2) refreshing a HAND-EDITED ./autoharn
                                       prints REPLACED naming ./autoharn.pre-refresh, and that
                                       backup file is byte-identical to the hand-edited content
                                       that existed immediately before the refresh ran.
  GREEN refresh-dispatcher-fresh-write-disclosed
                                       (finding 2, leg 3) an ordinary first scaffold (no prior
                                       ./autoharn) discloses 'fresh-write' in its own stdout --
                                       the third of the three named outcomes, never silent.

Usage: python3 seen-red/scaffold-dispatcher-verb-glob/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import os
# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own environment
# before any subprocess is spawned -- inherited by the whole process tree this fixture starts,
# so every repo-root verb invocation anywhere downstream carries it (though, per
# filing/fixture_sandbox.py's own SCOPE note, bootstrap/templates/*.tmpl and bootstrap/*.sh are
# never gated by this marker at all -- it is set here regardless, matching every other fixture in
# this family, so a future call site this fixture grows that DOES reach a gated libexec/autoharn/*
# entry point is covered without a second marker-setting edit).
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"

# case 7 (missing-header-refuses-new-world-db-untouched) is the one case in this family that
# touches a real Postgres host -- filing/pghost_resolve.py is this project's ONE home for
# resolving which host, env-var-first, never a hardcoded LAN box (ADR-0012 P1; the same module
# seen-red/belief-substrate-v2/run_fixtures.py and siblings already use).
sys.path.insert(0, str(REPO / "filing"))
import pghost_resolve  # noqa: E402  (after the REPO-relative sys.path insert directly above it)


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def scaffold(new_project: Path, dest: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return sh([
        "sh", str(new_project), str(dest),
        "--db", "scratchdb", "--host", "scratchhost",
        "--schema", "scratchschema", "--kern", "scratchkern", "--role", "scratchrole",
        *extra,
    ])


def new_world(new_project: Path, dest: Path, world: str, pghost: str, pgdb: str,
              *extra: str) -> subprocess.CompletedProcess[str]:
    """A REAL `--new-world` invocation (case 7 only) -- real host, real db, no --schema/--kern/
    --role (--new-world derives them from `world` itself, same as every other --new-world caller
    in this project's own seen-red corpus)."""
    return sh([
        "bash", str(new_project), str(dest), "--new-world", world,
        "--db", pgdb, "--host", pghost,
        *extra,
    ])


def world_schema_exists(pghost: str, pgdb: str, world: str) -> bool:
    """True iff `world`'s schema, `<world>_kernel`, or `<world>_rw` role exist on `pghost`/`pgdb`
    -- the live, queried (never inferred) proof that finding 1's fix stops --new-world's kernel
    DDL from ever running when the roster validation ahead of it refuses."""
    cp = sh(["psql", "-h", pghost, "-d", pgdb, "-tAc",
             f"SELECT (SELECT count(*) FROM information_schema.schemata "
             f"WHERE schema_name IN ('{world}', '{world}_kernel')) "
             f"+ (SELECT count(*) FROM pg_roles WHERE rolname = '{world}_rw');"])
    if cp.returncode != 0:
        raise RuntimeError(f"world_schema_exists query failed: {cp.stderr}")
    return cp.stdout.strip() != "0"


def teardown_world(pghost: str, pgdb: str, world: str) -> None:
    """DEFENSIVE cleanup for case 7 -- runs in a `finally` regardless of outcome, exactly the
    seen-red/belief-substrate-v2/run_fixtures.py::teardown() precedent, in case a real defect
    (not the one this fixture is proving fixed) ever lets DDL through despite the refusal."""
    sh(["psql", "-h", pghost, "-d", pgdb, "-c",
        f"DROP SCHEMA IF EXISTS {world} CASCADE; DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "
        f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", pghost, "-d", pgdb, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def parsed_roster(help_output: str) -> set[str]:
    """The verb column of `autoharn --help`'s own "verbs:" block -- first whitespace-delimited
    token per indented line, mirroring how a human (or seen-red/umbrella-cli-dispatch-parity's
    own case a) would read it."""
    verbs: set[str] = set()
    in_verbs = False
    for line in help_output.splitlines():
        if line.strip() == "verbs:":
            in_verbs = True
            continue
        if in_verbs:
            stripped = line.strip()
            if not stripped:
                break
            verbs.add(stripped.split()[0])
    return verbs


def main() -> int:
    failures: list[str] = []

    # ---- cases 1-2: an ordinary classic scaffold out of THIS checkout (no mutation) ----------
    tmp1 = Path(tempfile.mkdtemp(prefix="scaffold-dispatcher-verb-glob-"))
    dest1 = tmp1 / "deployment"
    try:
        r1 = scaffold(NEW_PROJECT, dest1)
        dispatcher = dest1 / "autoharn"
        help_r = sh([str(dispatcher), "--help"]) if dispatcher.exists() else None
        roster = parsed_roster(help_r.stdout) if help_r else set()
        check("scaffold-ran-clean", r1.returncode == 0 and dispatcher.exists(),
              f"exit={r1.returncode} dispatcher_exists={dispatcher.exists()} "
              f"stderr_tail={r1.stderr.strip()[-400:]!r}", failures)

        courier_help = sh([str(dispatcher), "courier", "--help"]) if dispatcher.exists() else None
        reaches_courier = bool(
            courier_help is not None
            and courier_help.returncode == 0
            and "courier" in (courier_help.stdout + courier_help.stderr).lower()
            and "REFUSED -- unrecognized verb" not in courier_help.stdout
        )
        check("dispatcher-lists-courier", "courier" in roster and reaches_courier,
              f"roster={sorted(roster)} in_roster={'courier' in roster} "
              f"reaches_real_courier_tmpl={reaches_courier} "
              f"courier_help_exit={courier_help.returncode if courier_help else None}",
              failures)

        unknown = sh([str(dispatcher), "totally-bogus-verb"]) if dispatcher.exists() else None
        unknown_refuses = bool(
            unknown is not None and unknown.returncode == 2
            and "REFUSED -- unrecognized verb" in unknown.stderr
            and "courier" in unknown.stderr  # the taught roster now includes the new verb too
        )
        check("unknown-verb-still-refuses", unknown_refuses,
              f"exit={unknown.returncode if unknown else None} "
              f"stderr_tail={(unknown.stderr.strip()[-400:] if unknown else '')!r}", failures)
    finally:
        shutil.rmtree(tmp1, ignore_errors=True)

    # ---- case 3: RED -- a template with no header line refuses generation loudly -------------
    # Never mutate THIS checkout's own templates -- copy the whole repo tree to scratch first
    # (every git-tracked FILE, current on-disk content -- cheap enough for this tree's size, and
    # it means the negative control's mutation lives entirely inside a throwaway directory).
    tmp2 = Path(tempfile.mkdtemp(prefix="scaffold-dispatcher-verb-glob-negctrl-"))
    repo_copy = tmp2 / "autoharn-copy"
    try:
        # --cached (committed) + --others --exclude-standard (untracked-but-not-gitignored, e.g.
        # this very work item's own not-yet-committed courier.tmpl/new-project.sh edits) -- a
        # plain `git ls-files` alone would silently omit any uncommitted file, which is exactly
        # this fixture's own subject mid-build.
        listing = sh(["git", "-C", str(REPO), "ls-files", "-z", "--cached", "--others",
                      "--exclude-standard"])
        names = [n for n in listing.stdout.split("\0") if n]
        for rel in names:
            src = REPO / rel
            if not src.is_file():
                continue
            dst = repo_copy / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        broken_tmpl = repo_copy / "bootstrap" / "templates" / "courier.tmpl"
        lines = broken_tmpl.read_text(encoding="utf-8").splitlines(keepends=True)
        stripped = [l for l in lines if not l.startswith("# autoharn-verb-desc: ")]
        assert len(stripped) < len(lines), "negative control did not actually remove a header line"
        broken_tmpl.write_text("".join(stripped), encoding="utf-8")

        dest3 = tmp2 / "deployment"
        r3 = scaffold(repo_copy / "bootstrap" / "new-project.sh", dest3)
        # FIX-ROUND FINDING 1 (autoharn3 row 101 re-review, 2026-07-28): this validation now runs
        # at _scan_verb_templates()'s new PRE-WRITE call site, the earliest point TEMPLATES is
        # resolvable on this flow -- BEFORE `mkdir -p $PROJECT_ROOT` even runs, so the assertion
        # below is now the WHOLE destination directory, never created at all, not merely the
        # dispatcher file (the original, weaker shape this case had before the fix -- kept only
        # as history in this comment, not as a second assertion).
        refuses_loud = bool(
            r3.returncode == 2
            and "autoharn-verb-desc" in r3.stderr
            and "courier.tmpl" in r3.stderr
            and not dest3.exists()  # the WHOLE destination was never created
        )
        check("missing-header-refuses-generation", refuses_loud,
              f"exit={r3.returncode} dest_created={dest3.exists()} "
              f"stderr_tail={r3.stderr.strip()[-500:]!r}", failures)
    finally:
        shutil.rmtree(tmp2, ignore_errors=True)

    # ---- case 7 (finding 1's stronger witness): the SAME broken template, driven via a REAL
    # --new-world scaffold against a REAL scratch Postgres host -- proves the DB, not just the
    # filesystem, is untouched when the roster validation refuses.
    tmp2b = Path(tempfile.mkdtemp(prefix="scaffold-dispatcher-verb-glob-negctrl-newworld-"))
    repo_copy2 = tmp2b / "autoharn-copy"
    pghost = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
    pgdb = "toy"
    world7 = "scfglob" + uuid.uuid4().hex[:8]
    try:
        listing2 = sh(["git", "-C", str(REPO), "ls-files", "-z", "--cached", "--others",
                       "--exclude-standard"])
        names2 = [n for n in listing2.stdout.split("\0") if n]
        for rel in names2:
            src = REPO / rel
            if not src.is_file():
                continue
            dst = repo_copy2 / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        broken_tmpl2 = repo_copy2 / "bootstrap" / "templates" / "courier.tmpl"
        lines2 = broken_tmpl2.read_text(encoding="utf-8").splitlines(keepends=True)
        stripped2 = [l for l in lines2 if not l.startswith("# autoharn-verb-desc: ")]
        assert len(stripped2) < len(lines2), "negative control did not actually remove a header line"
        broken_tmpl2.write_text("".join(stripped2), encoding="utf-8")

        dest7 = tmp2b / "deployment"
        r7 = new_world(repo_copy2 / "bootstrap" / "new-project.sh", dest7, world7, pghost, pgdb)
        db_touched = world_schema_exists(pghost, pgdb, world7)
        refuses_before_any_touch = bool(
            r7.returncode == 2
            and "autoharn-verb-desc" in r7.stderr
            and "courier.tmpl" in r7.stderr
            and not dest7.exists()   # no file, anywhere in the destination
            and not db_touched       # no schema/kernel-schema/role ever created in Postgres
        )
        check("missing-header-refuses-new-world-db-untouched", refuses_before_any_touch,
              f"exit={r7.returncode} dest_created={dest7.exists()} db_touched={db_touched} "
              f"world={world7!r} stderr_tail={r7.stderr.strip()[-500:]!r}", failures)
    finally:
        teardown_world(pghost, pgdb, world7)  # defensive -- see teardown_world()'s own docstring
        shutil.rmtree(tmp2b, ignore_errors=True)

    # ---- cases 4-5: --refresh-dispatcher ------------------------------------------------------
    tmp3 = Path(tempfile.mkdtemp(prefix="scaffold-dispatcher-verb-glob-refresh-"))
    dest4 = tmp3 / "deployment"
    try:
        r4 = scaffold(NEW_PROJECT, dest4)
        dispatcher4 = dest4 / "autoharn"
        dep_json_before = (dest4 / "deployment.json").read_bytes() if (dest4 / "deployment.json").exists() else None
        ok_birth = r4.returncode == 0 and dispatcher4.exists() and dep_json_before is not None
        check("refresh-fixture-birth-scaffold-clean", ok_birth,
              f"exit={r4.returncode} dispatcher_exists={dispatcher4.exists()} "
              f"deployment_json_exists={dep_json_before is not None}", failures)

        # ---- finding 2, leg 3: fresh-write disclosed (autoharn3 row 101 re-review) -------------
        # This SAME birth scaffold (r4, above) is the fresh-write leg -- no prior ./autoharn
        # existed before it ran, so its own stdout must name that outcome explicitly, never
        # silently.
        check("refresh-dispatcher-fresh-write-disclosed",
              "autoharn dispatcher: fresh-write" in r4.stdout,
              f"'autoharn dispatcher: fresh-write' present={('autoharn dispatcher: fresh-write' in r4.stdout)} "
              f"stdout_tail={r4.stdout.strip()[-300:]!r}", failures)

        # ---- finding 2, leg 1: SKIPPED-IDENTICAL (refresh an UNCHANGED world) ------------------
        dispatcher4_before_noop = dispatcher4.read_bytes()
        backup4 = dest4 / "autoharn.pre-refresh"
        r_noop = sh(["sh", str(NEW_PROJECT), "--refresh-dispatcher", str(dest4)])
        skipped_identical = bool(
            r_noop.returncode == 0
            and "SKIPPED-IDENTICAL" in r_noop.stdout
            and dispatcher4.read_bytes() == dispatcher4_before_noop  # byte-identical, untouched
            and not backup4.exists()  # nothing to back up -- none created
        )
        check("refresh-dispatcher-skipped-identical", skipped_identical,
              f"exit={r_noop.returncode} skipped_identical_disclosed={'SKIPPED-IDENTICAL' in r_noop.stdout} "
              f"dispatcher_unchanged={dispatcher4.read_bytes() == dispatcher4_before_noop} "
              f"backup_created={backup4.exists()} stdout_tail={r_noop.stdout.strip()[-300:]!r}", failures)

        # ---- finding 2, leg 2: REPLACED + backup byte-matches the pre-refresh original ---------
        hand_edit = dispatcher4_before_noop + b'\n#!/bin/sh\necho "hand-edited operator patch"\n'
        dispatcher4.write_bytes(hand_edit)
        dispatcher4.chmod(0o755)
        r_replace = sh(["sh", str(NEW_PROJECT), "--refresh-dispatcher", str(dest4)])
        backup_matches = backup4.exists() and backup4.read_bytes() == hand_edit
        replaced_with_backup = bool(
            r_replace.returncode == 0
            and "REPLACED" in r_replace.stdout
            and str(backup4) in r_replace.stdout
            and backup_matches
            and dispatcher4.read_bytes() != hand_edit  # the live file is the NEW roster, not the edit
        )
        check("refresh-dispatcher-replaces-with-backup", replaced_with_backup,
              f"exit={r_replace.returncode} replaced_disclosed={'REPLACED' in r_replace.stdout} "
              f"backup_path_named={str(backup4) in r_replace.stdout} backup_exists={backup4.exists()} "
              f"backup_byte_matches_pre_refresh={backup_matches} "
              f"stdout_tail={r_replace.stdout.strip()[-400:]!r}", failures)

        # Hand-install a stale, PRE-courier dispatcher stub -- the exact shape a world scaffolded
        # before this work item's own change would carry (a real dispatcher, just missing the new
        # verb), so refreshing it and observing 'courier' reappear is a genuine before/after, not
        # a vacuous no-op re-write of an already-current file.
        stale_stub = (
            "#!/bin/sh\n"
            "echo \"usage: autoharn <verb> [args...]\"\n"
            "echo \"verbs:\"\n"
            "echo \"  led                  (stale pre-courier stub, no other verbs)\"\n"
        )
        dispatcher4.write_text(stale_stub, encoding="utf-8")
        dispatcher4.chmod(0o755)
        stale_help = sh([str(dispatcher4)])
        stale_roster = parsed_roster(stale_help.stdout)

        r5 = sh(["sh", str(NEW_PROJECT), "--refresh-dispatcher", str(dest4)])
        refreshed_help = sh([str(dispatcher4), "--help"]) if dispatcher4.exists() else None
        refreshed_roster = parsed_roster(refreshed_help.stdout) if refreshed_help else set()
        dep_json_after = (dest4 / "deployment.json").read_bytes() if (dest4 / "deployment.json").exists() else None

        upgraded = bool(
            "courier" not in stale_roster
            and r5.returncode == 0
            and "courier" in refreshed_roster
            and dep_json_after == dep_json_before  # nothing else in the world was touched
        )
        check("refresh-dispatcher-upgrades", upgraded,
              f"stale_roster={sorted(stale_roster)} refresh_exit={r5.returncode} "
              f"refreshed_roster={sorted(refreshed_roster)} "
              f"deployment_json_unchanged={dep_json_after == dep_json_before}", failures)
    finally:
        shutil.rmtree(tmp3, ignore_errors=True)

    tmp4 = Path(tempfile.mkdtemp(prefix="scaffold-dispatcher-verb-glob-nonworld-"))
    try:
        non_world = tmp4 / "not-a-world"
        non_world.mkdir()
        r6 = sh(["sh", str(NEW_PROJECT), "--refresh-dispatcher", str(non_world)])
        refuses_non_world = bool(
            r6.returncode == 1
            and "deployment.json" in r6.stderr
            and not (non_world / "autoharn").exists()
        )
        check("refresh-dispatcher-refuses-non-world", refuses_non_world,
              f"exit={r6.returncode} autoharn_created={(non_world / 'autoharn').exists()} "
              f"stderr_tail={r6.stderr.strip()[-400:]!r}", failures)
    finally:
        shutil.rmtree(tmp4, ignore_errors=True)

    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL CASES OK -- scaffold-dispatcher-verb-glob proof (courier reaches a fresh world's "
          "roster via the bootstrap/templates/*.tmpl glob, unknown-verb refusal intact, a "
          "header-less template refuses generation loudly with the WHOLE destination left "
          "absent -- witnessed on both classic and a REAL --new-world scaffold with the DB "
          "schema/role provably never created -- --refresh-dispatcher upgrades a stale world's "
          "dispatcher in place while leaving the rest of it untouched, refuses on a non-world "
          "directory, and discloses exactly which of fresh-write/SKIPPED-IDENTICAL/REPLACED "
          "happened each time, with a REPLACED backup byte-identical to the pre-refresh "
          "original).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
