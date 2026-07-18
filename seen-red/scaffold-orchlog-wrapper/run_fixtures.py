#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T10:40:19Z
#   last-change: 2026-07-18T10:40:30Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- proof for ledger item deployment-orchlog-surfacing, half (b): the
scaffold-served orchlog wrapper (bootstrap/new-project.sh writes <dest>/orchlog beside
<dest>/led and <dest>/pickup, execing autoharn's own ../../orchlog verb with `--repo
<harness-root>` so a deployment session can self-serve the harness changelog without a
hand-relayed memo row). Half (a) of the same item (./migrate printing the span) belongs to
./migrate and is untouched by this fixture and by this build.

REAL SCAFFOLD, NO MOCKS: this fixture runs the actual bootstrap/new-project.sh in its
CLASSIC (non-`--new-world`) mode against a throwaway scratch destination directory. Classic
mode never touches postgres (every `psql` call in new-project.sh sits behind `if [ -n
"$NEW_WORLD" ]`, verified by reading the script) -- it only writes deployment.json, the
.claude/ wiring, and the operator-verb shims -- so this fixture needs no toy-DB fixture idiom
and no live database at all, matching this brief's fallback instruction ("else a dry-run leg
honestly scoped"). The db/host/schema/kern/role strings passed below are never dereferenced
by classic mode; they exist only to satisfy new-project.sh's own required-argument check.

Cases:
  GREEN wrapper-written        <dest>/orchlog exists, is executable, and its body execs
                                REPO/orchlog with `--repo REPO` (REPO = this checkout's own
                                root -- new-project.sh's EXEC_ROOT resolves to REPO when run
                                straight out of this checkout, unpinned).
  GREEN wrapper-execs-and-matches
                                actually RUNNING <dest>/orchlog (no args) succeeds (exit 0)
                                and its stdout matches `REPO/orchlog --repo REPO` run
                                directly -- proving the wrapper is not just textually present
                                but a working exec, byte-identical to the thing it wraps.
  GREEN wrapper-force-rescaffold
                                re-running new-project.sh --force over the same destination
                                regenerates the wrapper (still executable, still correct) --
                                the "existing deployments get the wrapper at next
                                scaffold-refresh" half of the commission's own sentence.
  RED   half-a-untouched       ./migrate (half (a)'s home) is byte-identical before and after
                                this fixture runs -- this build's own scope discipline,
                                mechanically checked rather than merely asserted.

Usage: python3 seen-red/scaffold-orchlog-wrapper/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
ORCHLOG = REPO / "orchlog"
MIGRATE = REPO / "migrate"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def scaffold(dest: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return sh([
        "sh", str(NEW_PROJECT), str(dest),
        "--db", "scratchdb", "--host", "scratchhost",
        "--schema", "scratchschema", "--kern", "scratchkern", "--role", "scratchrole",
        *extra,
    ])


def main() -> int:
    failures: list[str] = []

    migrate_before = MIGRATE.read_bytes() if MIGRATE.exists() else None

    tmp = Path(tempfile.mkdtemp(prefix="scaffold-orchlog-wrapper-"))
    dest = tmp / "deployment"
    try:
        r1 = scaffold(dest)
        check("scaffold-ran-clean", r1.returncode == 0,
              f"exit={r1.returncode} stderr_tail={r1.stderr.strip()[-400:]!r}", failures)

        wrapper = dest / "orchlog"
        exists_and_exec = wrapper.exists() and (wrapper.stat().st_mode & 0o111 != 0)
        body = wrapper.read_text(encoding="utf-8") if wrapper.exists() else ""
        expected_fragment = f"exec {REPO}/orchlog --repo {REPO}"
        points_at_repo = expected_fragment in body
        check("wrapper-written", exists_and_exec and points_at_repo,
              f"exists={wrapper.exists()} exec_bit={exists_and_exec} "
              f"fragment_present={points_at_repo} body={body!r}", failures)

        r_direct = sh([sys.executable, str(ORCHLOG), "--repo", str(REPO)])
        r_wrapped = sh([str(wrapper)])
        matches = (
            r_wrapped.returncode == r_direct.returncode == 0
            and r_wrapped.stdout == r_direct.stdout
        )
        check("wrapper-execs-and-matches", matches,
              f"direct_exit={r_direct.returncode} wrapped_exit={r_wrapped.returncode} "
              f"stdout_equal={r_wrapped.stdout == r_direct.stdout} "
              f"direct_len={len(r_direct.stdout)} wrapped_len={len(r_wrapped.stdout)}",
              failures)

        # --force re-scaffold regenerates the wrapper (existing-deployment refresh path).
        wrapper.unlink()
        r2 = scaffold(dest, "--force")
        wrapper_back = wrapper.exists() and (wrapper.stat().st_mode & 0o111 != 0)
        check("wrapper-force-rescaffold", r2.returncode == 0 and wrapper_back,
              f"exit={r2.returncode} wrapper_back={wrapper_back}", failures)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    migrate_after = MIGRATE.read_bytes() if MIGRATE.exists() else None
    half_a_untouched = migrate_before == migrate_after
    check("half-a-untouched (./migrate byte-identical, out of this build's scope)",
          half_a_untouched,
          f"migrate_existed_before={migrate_before is not None} "
          f"migrate_existed_after={migrate_after is not None} unchanged={half_a_untouched}",
          failures)

    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL CASES OK -- scaffold-served orchlog wrapper proof (written, executable, "
          "execs correctly, survives --force re-scaffold), half (a)/./migrate untouched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
