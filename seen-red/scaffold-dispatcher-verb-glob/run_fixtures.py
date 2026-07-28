#!/usr/bin/env python3
"""run_fixtures.py -- proof for autoharn3 work item scaffold-courier-verb-gap (ledger row 101,
maintainer-amended 2026-07-28): bootstrap/new-project.sh's world-dispatcher generation (the
`_write_world_dispatcher()` function shared by the ordinary --new-world/--profile scaffold flow
and the new --refresh-dispatcher mode) derives its verb roster from the bootstrap/templates/*.tmpl
directory glob (minus the enumerated NON_VERB_TEMPLATES exclusion list), not a hand-maintained
table -- so a template that exists IS a verb, and a template landing in bootstrap/templates/
without the '# autoharn-verb-desc: ...' header line refuses generation loudly rather than
silently shipping a blank description or, worse, silently NOT shipping the verb.

REAL SCAFFOLD, NO MOCKS: this fixture runs bootstrap/new-project.sh in its CLASSIC (non-
`--new-world`) mode against throwaway scratch destinations. Classic mode never touches
postgres (every `psql` call in new-project.sh sits behind `if [ -n "$NEW_WORLD" ]`) -- it only
writes deployment.json, the .claude/ wiring, and the dispatcher/verb templates -- so this
fixture needs no toy-DB fixture idiom and no live database at all.

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

Usage: python3 seen-red/scaffold-dispatcher-verb-glob/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
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
        # Dispatcher generation is near the very END of new-project.sh's own scaffold sequence
        # (deployment.json/.claude/ wiring/legacy/ all run first) -- this refusal fires INSIDE
        # _write_world_dispatcher(), before its own `cat > $PROJECT_ROOT/autoharn` ever runs, so
        # the ONE file this case actually proves absent is the dispatcher itself, never the whole
        # dest directory (which legitimately has earlier-written scaffold content by this point,
        # same as every other refusal path elsewhere in this script -- this scaffold is not
        # transactional/all-or-nothing, and this fixture does not claim otherwise).
        refuses_loud = bool(
            r3.returncode == 2
            and "autoharn-verb-desc" in r3.stderr
            and "courier.tmpl" in r3.stderr
            and not (dest3 / "autoharn").exists()  # the dispatcher itself was never written
        )
        check("missing-header-refuses-generation", refuses_loud,
              f"exit={r3.returncode} dispatcher_written={(dest3 / 'autoharn').exists()} "
              f"stderr_tail={r3.stderr.strip()[-500:]!r}", failures)
    finally:
        shutil.rmtree(tmp2, ignore_errors=True)

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
          "header-less template refuses generation loudly, --refresh-dispatcher upgrades a "
          "stale world's dispatcher in place while leaving the rest of it untouched, and refuses "
          "on a non-world directory).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
