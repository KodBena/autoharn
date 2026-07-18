#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T20:02:33Z
#   last-change: 2026-07-11T22:01:12Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for bootstrap/templates/verify-commission.tmpl
(design/MAINT-GPG-TRUST-LAYER.md §3, Rung 2). Real infra, no mocks: a throwaway `--new-world` scaffold
in the toy db, a throwaway GNUPGHOME (Ed25519 test key, generated fresh per run, clearly marked
test-only), torn down before AND after this file runs so re-running it never leaves residue.

KEY-RESIDENCE REVISION (2026-07-11 evening, "key-residence refactor" commission): this fixture
used to vary an `AUTOHARN` override to point verify-commission.tmpl at a scratch `law/keys/`
carrying (or lacking) the test key -- that was the OLD, conflated resolution
(verify-commission.tmpl read `AUTOHARN / "law" / "keys"`, autoharn's own directory). The verb now
resolves THIS WORLD's own `keys/` directory instead (a sibling of `deployment.json`, exactly
where `.claude/commission-<id>.asc` already lives) -- so this fixture varies `world_dir/keys/`
directly: writing the test key's public export into it for VERIFIED/FORGED-OR-CORRUPT, and
temporarily moving it OUT (never deleting -- restored before case e) for the
NO-COMMITTED-KEY case. AUTOHARN itself is now only needed for the `filing/` module imports
(deployment_record, gpg_trust) and is simply the real repo throughout -- there is no more
"autoharn with/without a key" axis to vary, because autoharn's own `law/keys/` is no longer on
verify-commission's read path at all (design/MAINT-GPG-TRUST-LAYER.md §7; law/keys/README.md).

Cases (five: the closed VERIFIED/UNSIGNED/FORGED-OR-CORRUPT vocabulary, plus the two typed
REFUSALS verify-commission.tmpl's own module docstring names — gpg missing, and no committed key
to check a claimed signature against):
  a-unsigned                        -- a FULL-mode commission with no .asc banked -> UNSIGNED,
                                        exit 0.
  b-verified                        -- the SAME statement signed with `printf '%s' "$STATEMENT" |
                                        gpg --detach-sign` (the byte-fidelity-fixed ceremony) and
                                        banked at .claude/commission-<id>.asc, checked against
                                        THIS WORLD's OWN `keys/` (never autoharn's law/keys/) now
                                        carrying the test key -> VERIFIED, exit 0.
  c-forged-tampered-bytes           -- the SAME .asc path now holds a signature over a DIFFERENT
                                        statement, checked against the same world-local committed
                                        key -> a genuine cryptographic mismatch,
                                        FORGED-OR-CORRUPT, exit 1 (loud).
  d-no-committed-key-distinct-refusal -- the SAME good signature from case b, checked against
                                        THIS WORLD's OWN `keys/` with the test key TEMPORARILY
                                        removed (an empty deployment keyring -- the honest
                                        AWAITING-KEY state a fresh scaffold starts in) -> the
                                        DISTINCT typed refusal NO-COMMITTED-KEY, exit 3 -- NEVER
                                        FORGED-OR-CORRUPT (an earlier version of this file folded
                                        this case into FORGED-OR-CORRUPT; a hack-rationalization
                                        audit caught the overload before this shipped -- see
                                        verify-commission.tmpl's own REVISION NOTE for the full
                                        account).
  e-gpg-absent-typed-refusal        -- the test key restored to world_dir/keys/, a .asc is
                                        banked, but `gpg` is not on PATH -> the OTHER typed
                                        refusal, GPG-UNAVAILABLE, exit 2 -- never silently folded
                                        into any of the three verdicts either.

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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
VERIFY_COMMISSION_TMPL = REPO / "bootstrap" / "templates" / "verify-commission.tmpl"

PGHOST, PGDB = fixture_pghost(), "toy"
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


def run_verify_commission(world_dir: Path, path_override: str | None = None,
                           commission_id: int = 1) -> subprocess.CompletedProcess[str]:
    # AUTOHARN is always the real repo now -- verify-commission.tmpl only uses it to import
    # filing/deployment_record.py + filing/gpg_trust.py (generic modules, unaffected by this
    # refactor); the key-residence axis under test is world_dir/keys/, not AUTOHARN.
    env = dict(os.environ)
    env["AUTOHARN"] = str(REPO)
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
    # THIS WORLD's own keys/ -- a sibling of deployment.json, the directory verify-commission.tmpl
    # now resolves (never autoharn's law/keys/, per the key-residence refactor -- see this file's
    # own module docstring). new-project.sh does not yet scaffold this directory itself (frozen
    # this pass -- a live session was running in the shared checkout when this commission landed,
    # see the commission's own report for the exact pending diff), so this fixture creates it by
    # hand, exactly what an operator following user-guide/USER-GPG-TRUST-LAYER-FAQ.md §3b would do on an
    # already-scaffolded world today.
    keys_dir = world_dir / "keys"
    saved_key_path = tmp / "test-key.asc.saved"  # case d's temporary move-out target

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

        statement = "Build the GPG trust layer per design/MAINT-GPG-TRUST-LAYER.md, all three rungs."
        r = sh(["bash", str(world_dir / "led"), "commission", statement],
               env={**os.environ, "LED_ACTOR": "commissioner"}, cwd=str(world_dir))
        if r.returncode != 0:
            print("COMMISSION WRITE FAILED:", r.stdout, r.stderr)
            return 1

        # --- a: no .asc banked -> UNSIGNED, exit 0 (world_dir/keys/ does not even exist yet at
        # this point -- deliberately, to prove UNSIGNED is decided before any key lookup) -------
        ra = run_verify_commission(world_dir)
        body_a = json.loads(ra.stdout) if ra.stdout.strip() else {}
        ok_a = ra.returncode == 0 and body_a.get("verdict") == "UNSIGNED"
        check("a-unsigned", ok_a, f"exit={ra.returncode} verdict={body_a.get('verdict')}", failures)

        # --- b: signed with the byte-fidelity-fixed ceremony, checked against the test key,
        # committed to THIS WORLD's own keys/ (never autoharn's law/keys/) -----------------------
        gpg_env = {"GNUPGHOME": str(gnupghome), "PATH": "/usr/bin:/bin:/usr/local/bin"}
        asc_path = world_dir / ".claude" / "commission-1.asc"
        rsign = sh(["gpg", "--batch", "--yes", "--detach-sign", "--armor", "-o", str(asc_path), "-"],
                   input=statement, env=gpg_env)
        keys_dir.mkdir(parents=True, exist_ok=True)
        r_export = sh(["gpg", "--homedir", str(gnupghome), "--armor", "--export", test_fpr])
        (keys_dir / "test-key.asc").write_text(r_export.stdout, encoding="utf-8")
        rb = run_verify_commission(world_dir)
        body_b = json.loads(rb.stdout) if rb.stdout.strip() else {}
        ok_b = rsign.returncode == 0 and rb.returncode == 0 and body_b.get("verdict") == "VERIFIED"
        check("b-verified", ok_b, f"sign_exit={rsign.returncode} verify_exit={rb.returncode} "
                                   f"verdict={body_b.get('verdict')}", failures)

        # --- c: same .asc path, signature over a DIFFERENT statement -> FORGED-OR-CORRUPT ------
        sh(["gpg", "--batch", "--yes", "--detach-sign", "--armor", "-o", str(asc_path), "-"],
           input="a completely different ask, never what row 1 actually says", env=gpg_env)
        rc = run_verify_commission(world_dir)
        body_c = json.loads(rc.stdout) if rc.stdout.strip() else {}
        ok_c = rc.returncode == 1 and body_c.get("verdict") == "FORGED-OR-CORRUPT"
        check("c-forged-tampered-bytes", ok_c, f"exit={rc.returncode} verdict={body_c.get('verdict')}", failures)

        # --- d: restore the GOOD signature, but TEMPORARILY move the test key OUT of
        # world_dir/keys/ (never deleted -- restored before case e) so the deployment's own
        # keyring is genuinely empty -- the honest AWAITING-KEY state a fresh scaffold starts in.
        # This is now a DISTINCT typed refusal (NO-COMMITTED-KEY, exit 3), never
        # FORGED-OR-CORRUPT -- see verify-commission.tmpl's own REVISION NOTE for why (a
        # hack-rationalization audit caught the original overload before this shipped).
        sh(["gpg", "--batch", "--yes", "--detach-sign", "--armor", "-o", str(asc_path), "-"],
           input=statement, env=gpg_env)
        shutil.move(str(keys_dir / "test-key.asc"), str(saved_key_path))
        rd = run_verify_commission(world_dir)
        body_d = json.loads(rd.stdout) if rd.stdout.strip() else {}
        ok_d = (rd.returncode == 3 and body_d.get("refusal") == "NO-COMMITTED-KEY"
                and "NO committed public key" in body_d.get("detail", ""))
        check("d-no-committed-key-distinct-refusal", ok_d,
              f"exit={rd.returncode} refusal={body_d.get('refusal')}", failures)

        # --- e: test key restored to world_dir/keys/, .asc still banked (good signature), but
        # `gpg` is not on PATH -> typed refusal, exit 2, distinct from all three verdicts -------
        shutil.move(str(saved_key_path), str(keys_dir / "test-key.asc"))
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
        re_ = run_verify_commission(world_dir, path_override=no_gpg_path)
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
