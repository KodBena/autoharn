#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T20:02:33Z
#   last-change: 2026-07-11T20:49:52Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for bootstrap/templates/verify-commission.tmpl
(design/GPG-TRUST-LAYER.md §3, Rung 2). Real infra, no mocks: a throwaway `--new-world` scaffold
in the toy db, a throwaway GNUPGHOME (Ed25519 test key, generated fresh per run, clearly marked
test-only), torn down before AND after this file runs so re-running it never leaves residue.

Cases (five: the closed VERIFIED/UNSIGNED/FORGED-OR-CORRUPT vocabulary, plus the two typed
REFUSALS verify-commission.tmpl's own module docstring names — gpg missing, and no committed key
to check a claimed signature against):
  a-unsigned                        -- a FULL-mode commission with no .asc banked -> UNSIGNED,
                                        exit 0.
  b-verified                        -- the SAME statement signed with `printf '%s' "$STATEMENT" |
                                        gpg --detach-sign` (the byte-fidelity-fixed ceremony) and
                                        banked at .claude/commission-<id>.asc, checked against a
                                        scratch law/keys/-equivalent carrying the test key ->
                                        VERIFIED, exit 0.
  c-forged-tampered-bytes           -- the SAME .asc path now holds a signature over a DIFFERENT
                                        statement, checked against a committed key -> a genuine
                                        cryptographic mismatch, FORGED-OR-CORRUPT, exit 1 (loud).
  d-no-committed-key-distinct-refusal -- the SAME good signature from case b, checked against a
                                        keys directory with ZERO committed keys (this repo's
                                        real, current AWAITING-KEY state) -> the DISTINCT typed
                                        refusal NO-COMMITTED-KEY, exit 3 -- NEVER FORGED-OR-CORRUPT
                                        (an earlier version of this file folded this case into
                                        FORGED-OR-CORRUPT; a hack-rationalization audit caught the
                                        overload before this shipped -- see verify-commission.tmpl's
                                        own REVISION NOTE for the full account).
  e-gpg-absent-typed-refusal        -- a .asc is banked, but `gpg` is not on PATH -> the OTHER
                                        typed refusal, GPG-UNAVAILABLE, exit 2 -- never silently
                                        folded into any of the three verdicts either.

Usage: python3 seen-red/verify-commission/run_fixtures.py
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

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
VERIFY_COMMISSION_TMPL = REPO / "bootstrap" / "templates" / "verify-commission.tmpl"

PGHOST, PGDB = "192.168.122.1", "toy"
WORLD = "vcfxprobe"

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


def teardown_world() -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {WORLD} CASCADE; DROP SCHEMA IF EXISTS {WORLD}_kernel CASCADE; "
        f"DROP OWNED BY {WORLD}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {WORLD}_rw;"])


def gen_key(gnupghome: Path, name: str, email: str) -> str:
    batch = gnupghome / f"keygen-{email}.batch"
    batch.write_text(KEYGEN_BATCH_TEMPLATE.format(name=name, email=email), encoding="utf-8")
    r = sh(["gpg", "--homedir", str(gnupghome), "--batch", "--generate-key", str(batch)])
    if r.returncode != 0:
        raise RuntimeError(f"gpg keygen failed: {r.stderr}")
    r = sh(["gpg", "--homedir", str(gnupghome), "--list-secret-keys", "--with-colons"])
    fprs = [ln.split(":")[9] for ln in r.stdout.splitlines() if ln.startswith("fpr")]
    return fprs[-1]


def run_verify_commission(world_dir: Path, autoharn_override: Path, path_override: str | None = None,
                           commission_id: int = 1) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["AUTOHARN"] = str(autoharn_override)
    env["PICKUP_DEPLOYMENT"] = str(world_dir / "deployment.json")
    if path_override is not None:
        env["PATH"] = path_override
    return sh(["python3", str(VERIFY_COMMISSION_TMPL), "--id", str(commission_id), "--json"], env=env)


def main() -> int:
    teardown_world()
    tmp = Path(tempfile.mkdtemp(prefix="verify-commission-seenred-"))
    world_dir = tmp / WORLD
    gnupghome = tmp / "gnupghome"
    gnupghome.mkdir(mode=0o700)
    keys_dir_with_key = tmp / "keys-dir-with-test-key"
    keys_dir_with_key.mkdir()
    autoharn_with_key = tmp / "autoharn-with-key"
    (autoharn_with_key / "law" / "keys").mkdir(parents=True)
    (autoharn_with_key / "filing").mkdir(parents=True)
    for f in ("deployment_record.py", "gpg_trust.py"):
        os.symlink(REPO / "filing" / f, autoharn_with_key / "filing" / f)
    autoharn_no_key = REPO  # this repo's own law/keys/ is genuinely AWAITING-KEY right now

    failures: list[str] = []
    no_gpg_path = None
    try:
        print("== generating throwaway test key (Ed25519, test-only, never a real maintainer key) ==")
        test_fpr = gen_key(gnupghome, "AUTOHARN TEST KEY -- THROWAWAY -- SEEN-RED FIXTURE",
                            "verify-commission-seenred-test@example.invalid")
        print(f"  test key: {test_fpr}\n")

        print(f"== scaffolding throwaway --new-world {WORLD} ==")
        r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", WORLD,
                "--db", PGDB, "--host", PGHOST])
        if r.returncode != 0:
            print("SCAFFOLD FAILED:", r.stdout[-1500:], r.stderr[-1500:])
            return 1
        for verb in ("led", "verify-commission"):
            (world_dir / verb).chmod(0o755)
        print("  scaffold OK.\n")

        statement = "Build the GPG trust layer per design/GPG-TRUST-LAYER.md, all three rungs."
        r = sh(["bash", str(world_dir / "led"), "commission", statement],
               env={**os.environ, "LED_ACTOR": "commissioner"}, cwd=str(world_dir))
        if r.returncode != 0:
            print("COMMISSION WRITE FAILED:", r.stdout, r.stderr)
            return 1

        # --- a: no .asc banked -> UNSIGNED, exit 0 ------------------------------------------
        ra = run_verify_commission(world_dir, autoharn_no_key)
        body_a = json.loads(ra.stdout) if ra.stdout.strip() else {}
        ok_a = ra.returncode == 0 and body_a.get("verdict") == "UNSIGNED"
        check("a-unsigned", ok_a, f"exit={ra.returncode} verdict={body_a.get('verdict')}", failures)

        # --- b: signed with the byte-fidelity-fixed ceremony, checked against the test key -----
        gpg_env = {"GNUPGHOME": str(gnupghome), "PATH": "/usr/bin:/bin:/usr/local/bin"}
        asc_path = world_dir / ".claude" / "commission-1.asc"
        rsign = sh(["gpg", "--batch", "--yes", "--detach-sign", "--armor", "-o", str(asc_path), "-"],
                   input=statement, env=gpg_env)
        r_export = sh(["gpg", "--homedir", str(gnupghome), "--armor", "--export", test_fpr])
        (autoharn_with_key / "law" / "keys" / "test-key.asc").write_text(r_export.stdout, encoding="utf-8")
        rb = run_verify_commission(world_dir, autoharn_with_key)
        body_b = json.loads(rb.stdout) if rb.stdout.strip() else {}
        ok_b = rsign.returncode == 0 and rb.returncode == 0 and body_b.get("verdict") == "VERIFIED"
        check("b-verified", ok_b, f"sign_exit={rsign.returncode} verify_exit={rb.returncode} "
                                   f"verdict={body_b.get('verdict')}", failures)

        # --- c: same .asc path, signature over a DIFFERENT statement -> FORGED-OR-CORRUPT ------
        sh(["gpg", "--batch", "--yes", "--detach-sign", "--armor", "-o", str(asc_path), "-"],
           input="a completely different ask, never what row 1 actually says", env=gpg_env)
        rc = run_verify_commission(world_dir, autoharn_with_key)
        body_c = json.loads(rc.stdout) if rc.stdout.strip() else {}
        ok_c = rc.returncode == 1 and body_c.get("verdict") == "FORGED-OR-CORRUPT"
        check("c-forged-tampered-bytes", ok_c, f"exit={rc.returncode} verdict={body_c.get('verdict')}", failures)

        # --- d: restore the GOOD signature, but check against a keys dir with ZERO keys -- this
        # is now a DISTINCT typed refusal (NO-COMMITTED-KEY, exit 3), never FORGED-OR-CORRUPT --
        # see verify-commission.tmpl's own REVISION NOTE for why (a hack-rationalization audit
        # caught the original overload before this shipped).
        sh(["gpg", "--batch", "--yes", "--detach-sign", "--armor", "-o", str(asc_path), "-"],
           input=statement, env=gpg_env)
        rd = run_verify_commission(world_dir, autoharn_no_key)
        body_d = json.loads(rd.stdout) if rd.stdout.strip() else {}
        ok_d = (rd.returncode == 3 and body_d.get("refusal") == "NO-COMMITTED-KEY"
                and "NO committed public key" in body_d.get("detail", ""))
        check("d-no-committed-key-distinct-refusal", ok_d,
              f"exit={rd.returncode} refusal={body_d.get('refusal')}", failures)

        # --- e: gpg absent from PATH -> typed refusal, exit 2, distinct from all three ---------
        no_gpg_dir = tmp / "no-gpg-bin"
        no_gpg_dir.mkdir()
        for f in Path("/usr/bin").iterdir():
            if f.name.lower().startswith("gpg"):
                continue
            try:
                (no_gpg_dir / f.name).symlink_to(f)
            except OSError:
                pass
        no_gpg_path = str(no_gpg_dir)
        re_ = run_verify_commission(world_dir, autoharn_with_key, path_override=no_gpg_path)
        ok_e = re_.returncode == 2 and "gpg" in (re_.stdout + re_.stderr).lower()
        check("e-gpg-absent-typed-refusal", ok_e,
              f"exit={re_.returncode} stderr={(re_.stdout + re_.stderr).strip()[:200]!r}", failures)

    finally:
        teardown_world()
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- verify-commission both-polarity proof (UNSIGNED / VERIFIED / "
          "FORGED-OR-CORRUPT / NO-COMMITTED-KEY-refusal / GPG-UNAVAILABLE-refusal), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
