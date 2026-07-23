#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for ../../attest-tags (design/MAINT-GPG-TRUST-LAYER.md §2,
Rung 1). Real infra, no mocks: a throwaway GNUPGHOME (Ed25519 test key, generated fresh per run,
clearly marked test-only) plus a throwaway scratch git repository, both under this process's own
temp dir, both torn down before AND after this file runs so re-running it never leaves residue.

Cases (five, matching design/MAINT-GPG-TRUST-LAYER.md §7's "both polarities" + attest-tags' own three
verdicts, GOOD/BAD/UNVERIFIABLE, each witnessed in its own right):
  a-no-tags-uncovered-claim  -- a repo with a RATIFIED-marked commit and no ratified/* tag AT ALL
                                (zero tags to even check): attest-tags reports the commit as
                                uncovered, exit 1. (This is NOT the per-tag UNVERIFIABLE case --
                                see b0 below for that; with zero tags the per-tag verdict loop
                                never runs at all.)
  b0-unverifiable-tag-exists-no-committed-key -- a ratified/* tag IS signed, but law/keys/ is
                                STILL EMPTY at this point (before case b commits the test key) --
                                the genuine per-tag UNVERIFIABLE verdict: a tag exists to check,
                                nothing exists to check it against. Exit 1, loud, never a pass.
  b-good-signed-tag-verifies -- the SAME tag, once the test key is committed to a scratch
                                law/keys/, verifies GOOD; exit 0.
  c-unsigned-tag-refused     -- a plain (unsigned/lightweight) ratified/* tag is refused BAD,
                                loudly, with git's own "cannot verify a non-tag object" detail;
                                exit 1.
  d-forged-tag-refused       -- a ratified/* tag signed by a SECOND throwaway key that was never
                                committed to law/keys/ (the forger) is refused BAD -- attest-tags
                                trusts only the committed keyring, never the ambient one; exit 1.

Usage: python3 seen-red/attest-tags/run_fixtures.py
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
# Relocated under libexec/autoharn/ by the umbrella-CLI build (design/
# FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md, ledger rows 1151-1183): the ROOT `attest-tags` is now a
# one-line shell alias shim (`exec ... autoharn attest-tags "$@"`), not the Python script this
# fixture invokes directly via `sys.executable` -- pointing at the real relocated implementation
# instead (the alias shim itself is exercised separately by
# seen-red/umbrella-cli-dispatch-parity/run_fixtures.py's own case c).
ATTEST_TAGS = REPO / "libexec" / "autoharn" / "attest-tags"

KEYGEN_BATCH_TEMPLATE = """%no-protection
Key-Type: eddsa
Key-Curve: ed25519
Key-Usage: sign
Name-Real: {name}
Name-Email: {email}
Expire-Date: 0
%commit
"""


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def gen_key(gnupghome: Path, name: str, email: str) -> str:
    batch = gnupghome / f"keygen-{email}.batch"
    batch.write_text(KEYGEN_BATCH_TEMPLATE.format(name=name, email=email), encoding="utf-8")
    r = sh(["gpg", "--homedir", str(gnupghome), "--batch", "--generate-key", str(batch)])
    if r.returncode != 0:
        raise RuntimeError(f"gpg keygen failed: {r.stderr}")
    r = sh(["gpg", "--homedir", str(gnupghome), "--list-secret-keys", "--with-colons"])
    fprs = [ln.split(":")[9] for ln in r.stdout.splitlines() if ln.startswith("fpr")]
    return fprs[-1]


def export_pub(gnupghome: Path, fpr: str, dest: Path) -> None:
    r = sh(["gpg", "--homedir", str(gnupghome), "--armor", "--export", fpr])
    dest.write_text(r.stdout, encoding="utf-8")


def git(repo: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    return sh(["git", "-C", str(repo)] + list(args), env=env)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="attest-tags-seenred-"))
    gnupghome = tmp / "gnupghome"
    gnupghome.mkdir(mode=0o700)
    scratch_repo = tmp / "scratch-repo"
    scratch_repo.mkdir()
    keys_dir = scratch_repo / "law" / "keys"
    keys_dir.mkdir(parents=True)

    failures: list[str] = []
    try:
        print("== generating throwaway test key (Ed25519, test-only, never a real maintainer key) ==")
        test_fpr = gen_key(gnupghome, "AUTOHARN TEST KEY -- THROWAWAY -- SEEN-RED FIXTURE",
                            "attest-tags-seenred-test@example.invalid")
        forger_fpr = gen_key(gnupghome, "AUTOHARN FORGER TEST KEY -- THROWAWAY -- NEVER COMMITTED",
                              "attest-tags-seenred-forger@example.invalid")
        print(f"  test key: {test_fpr}\n  forger key (never committed to law/keys/): {forger_fpr}\n")

        git(scratch_repo, "init", "-q")
        git(scratch_repo, "config", "user.email", "seenred@example.invalid")
        git(scratch_repo, "config", "user.name", "seen-red fixture")
        (scratch_repo / "README.md").write_text("scratch fixture repo\n", encoding="utf-8")
        git(scratch_repo, "add", "README.md")
        git(scratch_repo, "commit", "-q", "-m", "initial commit")
        (scratch_repo / "ask.txt").write_text("a design note\n", encoding="utf-8")
        git(scratch_repo, "add", "ask.txt")
        git(scratch_repo, "commit", "-q", "-m",
            "RATIFIED: this design note is ratified, no tag exists yet")
        r = git(scratch_repo, "rev-parse", "HEAD")
        commit_a = r.stdout.strip()

        gpg_env = {"GNUPGHOME": str(gnupghome), "PATH": "/usr/bin:/bin:/usr/local/bin"}

        # --- a: no tags at all -> the RATIFIED commit is uncovered, exit 1 ---------------------
        ra = sh([sys.executable, str(ATTEST_TAGS), "--repo", str(scratch_repo),
                  "--keys-dir", str(keys_dir), "--json"])
        ok_a = ra.returncode == 1 and f'"sha": "{commit_a}"' in ra.stdout and '"ok": false' in ra.stdout
        check("a-no-tags-uncovered-claim", ok_a,
              f"exit={ra.returncode} commit={commit_a[:12]} in_output={commit_a in ra.stdout}", failures)

        # --- b: sign a good tag with the test key, commit the pubkey -> GOOD, exit 0 -----------
        git(scratch_repo, "config", "user.signingkey", test_fpr)
        rt = git(scratch_repo, "tag", "-s", "ratified/fixture-adr", "-m",
                 "ratified with fixture proviso", commit_a, env={**__import__("os").environ, **gpg_env})

        # --- b0: the tag is now SIGNED, but law/keys/ (keys_dir) is STILL EMPTY at this point --
        # this is the per-tag UNVERIFIABLE case (distinct from case a's "zero tags at all", which
        # never reaches the per-tag verdict loop): a tag exists to check, but nothing exists to
        # check it against. Tested here, between signing and committing the pubkey, because this
        # is the only window where a tag is present and the keys dir is genuinely empty.
        rb0 = sh([sys.executable, str(ATTEST_TAGS), "--repo", str(scratch_repo),
                   "--keys-dir", str(keys_dir), "--json"])
        ok_b0 = (rt.returncode == 0 and rb0.returncode == 1
                 and '"verdict": "UNVERIFIABLE"' in rb0.stdout and '"ok": false' in rb0.stdout)
        check("b0-unverifiable-tag-exists-no-committed-key", ok_b0,
              f"tag_exit={rt.returncode} attest_exit={rb0.returncode}", failures)

        export_pub(gnupghome, test_fpr, keys_dir / "test-key.asc")
        rb = sh([sys.executable, str(ATTEST_TAGS), "--repo", str(scratch_repo),
                  "--keys-dir", str(keys_dir), "--json"])
        ok_b = (rt.returncode == 0 and rb.returncode == 0
                and '"verdict": "GOOD"' in rb.stdout and '"ok": true' in rb.stdout)
        check("b-good-signed-tag-verifies", ok_b,
              f"tag_exit={rt.returncode} attest_exit={rb.returncode}", failures)

        # --- c: an unsigned (lightweight) tag -> BAD, loud, exit 1 -----------------------------
        (scratch_repo / "f3.txt").write_text("third\n", encoding="utf-8")
        git(scratch_repo, "add", "f3.txt")
        git(scratch_repo, "commit", "-q", "-m", "not a ratification-claiming commit")
        r2 = git(scratch_repo, "rev-parse", "HEAD")
        commit_c = r2.stdout.strip()
        git(scratch_repo, "tag", "ratified/unsigned-fixture", commit_c)
        rc = sh([sys.executable, str(ATTEST_TAGS), "--repo", str(scratch_repo),
                  "--keys-dir", str(keys_dir), "--json"])
        ok_c = (rc.returncode == 1
                and '"tag": "ratified/unsigned-fixture"' in rc.stdout
                and '"verdict": "BAD"' in rc.stdout
                and "cannot verify a non-tag object" in rc.stdout)
        check("c-unsigned-tag-refused", ok_c, f"exit={rc.returncode}", failures)

        # --- d: a tag signed by the FORGER key (never committed) -> BAD, exit 1 ----------------
        git(scratch_repo, "config", "user.signingkey", forger_fpr)
        rt2 = git(scratch_repo, "tag", "-s", "ratified/forged-fixture", "-m",
                  "forged: signed by an uncommitted key", commit_c,
                  env={**__import__("os").environ, **gpg_env})
        rd = sh([sys.executable, str(ATTEST_TAGS), "--repo", str(scratch_repo),
                  "--keys-dir", str(keys_dir), "--json"])
        ok_d = (rt2.returncode == 0 and rd.returncode == 1
                and '"tag": "ratified/forged-fixture"' in rd.stdout
                and '"verdict": "BAD"' in rd.stdout)
        check("d-forged-tag-refused", ok_d, f"tag_exit={rt2.returncode} attest_exit={rd.returncode}", failures)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- attest-tags both-polarity proof (GOOD / UNVERIFIABLE / unsigned-BAD / "
          "forged-BAD / uncovered-claim), zero residue (tmp dir removed).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
