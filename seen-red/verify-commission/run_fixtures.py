#!/usr/bin/env python3
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

Cases (five original: the closed VERIFIED/UNSIGNED/FORGED-OR-CORRUPT vocabulary, plus the two
typed REFUSALS verify-commission.tmpl's own module docstring names — gpg missing, and no
committed key to check a claimed signature against; PLUS two v1.1 cases (design/
FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §2 item 2) proving the s41 binding-grade upgrade):
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
  f-directory-verified-grade-before-binding -- case b's own JSON, re-inspected: before ANY s41
                                        key binding exists, a VERIFIED verdict grades
                                        DIRECTORY-VERIFIED (the fail-safe default -- no binding
                                        claimed where none exists).
  g-binding-verified-grade-after-s41-bind -- `commissioner` binds the SAME test fingerprint to
                                        themself (./led principal bind-key), then the SAME good
                                        signature re-verifies at BINDING-VERIFIED grade -- the s41
                                        binding upgrade, witnessed live.
  h-multi-signature-attest-refused  -- FIX-ROUND ADDITION (kernel review, s61 tip c3d773a): a
                                        SECOND throwaway key independently signs the SAME
                                        statement; both detached signatures are concatenated into
                                        ONE `.claude/commission-<id>.asc` (real gpg, both
                                        signatures genuinely verify) -- `verify-commission --attest
                                        --id <id> --json` REFUSES, MULTIPLE-VALID-SIGNATURES, exit
                                        4, naming BOTH fingerprints. Prior to this case, ONLY
                                        seen-red/s61-signature-symmetry-and-key-binding/
                                        run_fixtures_cli.py's case j exercised this refusal, and
                                        only through led.tmpl's attest-possession leg -- this
                                        verb's OWN catch (main()'s `except
                                        gpg_trust.MultipleValidSignatures` block) had zero shipped
                                        fixture coverage, proven only by an ad hoc reviewer probe
                                        (never a shipped case) until now.

Usage: python3 seen-red/verify-commission/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "filing"))
import deployment_record  # noqa: E402 (filing/deployment_record.py -- the ONE home for the deployment.json shape, needed below to apply the s58..s61 chain TAIL onto the schema/kern/role --new-world actually derived, never re-guessed from the world name)

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LINEAGE = REPO / "kernel" / "lineage"

# fix-round finding (kernel review, s61 tip c3d773a): bootstrap/new-project.sh's OWN --new-world
# LINEAGE_CHAIN is stale -- it ends at s57-obligation-revocation-event.sql, so a plain --new-world
# scaffold carries NEITHER s60 (the entitlement acceptance predicate) NOR s61 (this delta's own
# signature-symmetry/key-binding kinds and columns) -- s61's own PREREQUISITE section names s60 as
# a hard dependency, and s60's names s59, which names s58. Case g below needs the REAL
# `principal_key_possession_verified` kind and `key_binding_possession_ref` column s61 adds (the
# possession ceremony the FAQ's §10a now documents), so this fixture applies the s58..s61 TAIL
# additively onto the SAME schema/kern/role --new-world already scaffolded -- mirroring
# seen-red/s61-signature-symmetry-and-key-binding/run_fixtures_cli.py's own CHAIN_S61 tail
# (ADR-0012 P1: the same four filenames, not re-derived). No birth sequence is needed for either
# new act: entitlement_act_class_of (s60 Element 7) returns NULL for principal_key_bound,
# principal_key_possession_verified, AND commission_signature_verified alike -- none of s61's own
# new writes fall inside s60's gated act-class set, verified by reading that function's body
# before relying on it here.
CHAIN_TAIL_S61 = ["s58-missive-substrate.sql", "s59-missive-views.sql",
                   "s60-entitlement-enforcement.sql", "s61-signature-symmetry-and-key-binding.sql"]


def apply_chain_tail(dep) -> subprocess.CompletedProcess[str]:
    args = ["psql", "-h", dep.host, "-d", dep.db, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={dep.schema}", "-v", f"kern={dep.kern}", "-v", f"role={dep.role}"]
    for name in CHAIN_TAIL_S61:
        args += ["-f", str(LINEAGE / name)]
    return sh(args)

# cli-rebase-fixture-repairs (ledger row 1170): REUSE (ADR-0012 P1) serve_existing_world from
# seen-red/boundary-service/run_fixtures.py -- the served `led` shim refuses every write until
# this deployment.json gains boundary_url/boundary_deployment.
_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", REPO / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)
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
                           commission_id: int = 1, attest: bool = False) -> subprocess.CompletedProcess[str]:
    # AUTOHARN is always the real repo now -- verify-commission.tmpl only uses it to import
    # filing/deployment_record.py + filing/gpg_trust.py (generic modules, unaffected by this
    # refactor); the key-residence axis under test is world_dir/keys/, not AUTOHARN.
    env = dict(os.environ)
    env["AUTOHARN"] = str(REPO)
    env["PICKUP_DEPLOYMENT"] = str(world_dir / "deployment.json")
    if path_override is not None:
        env["PATH"] = path_override
    args = ["python3", str(VERIFY_COMMISSION_TMPL), "--id", str(commission_id), "--json"]
    if attest:  # h-multi-signature-attest-refused: mirrors the reviewer's own probe invocation,
        args.insert(2, "--attest")  # ("--attest --id <n> --json") -- not load-bearing for the
        # MULTIPLE-VALID-SIGNATURES catch itself (verify() computes sig_fp unconditionally,
        # before do_attest is even consulted -- see verify-commission.tmpl's own verify()), but
        # matched here so this case exercises the SAME invocation shape the reviewer's ad hoc
        # probe (vc_multisig_probe.py) actually witnessed, not merely an equivalent one.
    return sh(args, env=env)


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
        # §6 amendment (2026-07-26, rows 1357/1365/1366/1367): one dispatcher now, not two shims.
        for verb in ("autoharn",):
            p = world_dir / verb
            if p.exists():
                p.chmod(0o755)
        proc = bs_fixtures.serve_existing_world(world_dir / "deployment.json", tmp)
        print("  scaffold OK.\n")

        statement = "Build the GPG trust layer per design/MAINT-GPG-TRUST-LAYER.md, all three rungs."
        r = sh(["bash", str(world_dir / "autoharn"), "led", "commission", statement],
               env={**os.environ, "LED_ACTOR": "commissioner"}, cwd=str(world_dir))
        if r.returncode != 0:
            print("COMMISSION WRITE FAILED:", r.stdout, r.stderr)
            return 1
        # cli-rebase-fixture-repairs (row 1170): the commission row's own id is no longer
        # guaranteed to be 1 -- the s40/s43 birth sequence writes several rows ahead of it now --
        # parsed from "led: row <id> written." rather than hardcoded.
        m = re.search(r"row (\d+) written", r.stdout)
        if m is None:
            print("COULD NOT PARSE COMMISSION ROW ID:", r.stdout, r.stderr)
            return 1
        commission_id = int(m.group(1))

        # --- a: no .asc banked -> UNSIGNED, exit 0 (world_dir/keys/ does not even exist yet at
        # this point -- deliberately, to prove UNSIGNED is decided before any key lookup) -------
        ra = run_verify_commission(world_dir, commission_id=commission_id)
        body_a = json.loads(ra.stdout) if ra.stdout.strip() else {}
        ok_a = ra.returncode == 0 and body_a.get("verdict") == "UNSIGNED"
        check("a-unsigned", ok_a, f"exit={ra.returncode} verdict={body_a.get('verdict')}", failures)

        # --- b: signed with the byte-fidelity-fixed ceremony, checked against the test key,
        # committed to THIS WORLD's own keys/ (never autoharn's law/keys/) -----------------------
        gpg_env = {"GNUPGHOME": str(gnupghome), "PATH": "/usr/bin:/bin:/usr/local/bin"}
        asc_path = world_dir / ".claude" / f"commission-{commission_id}.asc"
        rsign = sh(["gpg", "--batch", "--yes", "--detach-sign", "--armor", "-o", str(asc_path), "-"],
                   input=statement, env=gpg_env)
        keys_dir.mkdir(parents=True, exist_ok=True)
        r_export = sh(["gpg", "--homedir", str(gnupghome), "--armor", "--export", test_fpr])
        (keys_dir / "test-key.asc").write_text(r_export.stdout, encoding="utf-8")
        rb = run_verify_commission(world_dir, commission_id=commission_id)
        body_b = json.loads(rb.stdout) if rb.stdout.strip() else {}
        ok_b = rsign.returncode == 0 and rb.returncode == 0 and body_b.get("verdict") == "VERIFIED"
        check("b-verified", ok_b, f"sign_exit={rsign.returncode} verify_exit={rb.returncode} "
                                   f"verdict={body_b.get('verdict')}", failures)

        # --- f/g: v1.1 (design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §2 item 2) -- the s41
        # binding grade. At this point the test key verifies (case b) but is not yet bound to
        # ANY principal via s41 -- case b's own JSON body must already carry
        # grade=DIRECTORY-VERIFIED (the committed-keys-only grade). Then `commissioner` binds the
        # SAME fingerprint to themself and a re-verify of the SAME good signature must upgrade to
        # BINDING-VERIFIED, naming the s41 binding explicitly -- never silently staying at
        # DIRECTORY-VERIFIED once a binding exists, and never silently claiming BINDING-VERIFIED
        # before one does (case b is the fail-safe-default control for this very case).
        ok_f = body_b.get("grade") == "DIRECTORY-VERIFIED" and body_b.get("signing_key_fingerprint") == test_fpr
        check("f-directory-verified-grade-before-binding", ok_f,
              f"grade={body_b.get('grade')} signing_key={body_b.get('signing_key_fingerprint')} "
              f"(expected DIRECTORY-VERIFIED / {test_fpr})", failures)

        # apply the s58..s61 chain TAIL now (see CHAIN_TAIL_S61's own comment above) -- additive,
        # onto the SAME schema/kern/role, so case g's ceremony below has the real s61 kinds/
        # columns to write against, never a stale pre-s61 kernel silently accepting a fingerprint
        # bind with no possession proof (that silent acceptance is exactly the false witness this
        # fix round exists to close).
        dep = deployment_record.load_deployment(world_dir / "deployment.json")
        r_chain = apply_chain_tail(dep)
        if r_chain.returncode != 0:
            print("s58..s61 CHAIN TAIL APPLY FAILED:", r_chain.stdout[-2000:], r_chain.stderr[-2000:])
            return 1

        # s61 item 3 (design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §2, landed the SAME commit as
        # this case's own docstring update): a FRESH `bind-key` now REQUIRES proof of possession
        # (`--possession-ref`, citing a `led principal attest-possession` row) -- this case, and
        # user-guide/USER-GPG-TRUST-LAYER-FAQ.md §10a, both thread that ceremony through before
        # binding, mirroring the real operator flow the FAQ teaches rather than the pre-item-3
        # bare `bind-key --fingerprint` shape this case used to exercise.
        possess_statement = f"autoharn key-binding proof-of-possession: fingerprint={test_fpr}"
        possess_asc = tmp / "possession.asc"
        rsign_possess = sh(["gpg", "--batch", "--yes", "--detach-sign", "--armor", "-o",
                             str(possess_asc), "-"], input=possess_statement, env=gpg_env)
        r_attest_poss = sh(["bash", str(world_dir / "led"), "principal", "attest-possession",
                             test_fpr, "--asc", str(possess_asc)],
                            env={**os.environ, "LED_ACTOR": "commissioner"}, cwd=str(world_dir))
        possess_row = None
        if r_attest_poss.returncode == 0:
            m_poss = re.search(r"row (\d+) written", r_attest_poss.stdout)
            possess_row = m_poss.group(1) if m_poss else None
        r_bind = sh(["bash", str(world_dir / "led"), "principal", "bind-key", "commissioner",
                     "--fingerprint", test_fpr,
                     "--possession-ref", possess_row or ""],
                    env={**os.environ, "LED_ACTOR": "commissioner"}, cwd=str(world_dir))
        rg = run_verify_commission(world_dir, commission_id=commission_id)
        body_g = json.loads(rg.stdout) if rg.stdout.strip() else {}
        ok_g = (rsign_possess.returncode == 0 and r_attest_poss.returncode == 0
                and possess_row is not None and r_bind.returncode == 0 and rg.returncode == 0
                and body_g.get("verdict") == "VERIFIED" and body_g.get("grade") == "BINDING-VERIFIED"
                and body_g.get("signing_key_fingerprint") == test_fpr)
        check("g-binding-verified-grade-after-s41-bind", ok_g,
              f"attest_possess_exit={r_attest_poss.returncode} possess_row={possess_row} "
              f"bind_exit={r_bind.returncode} verify_exit={rg.returncode} "
              f"verdict={body_g.get('verdict')} grade={body_g.get('grade')} "
              f"(attest_possess stdout tail: {r_attest_poss.stdout[-200:]!r}; "
              f"bind stdout tail: {r_bind.stdout[-300:]!r})", failures)

        # --- c: same .asc path, signature over a DIFFERENT statement -> FORGED-OR-CORRUPT ------
        sh(["gpg", "--batch", "--yes", "--detach-sign", "--armor", "-o", str(asc_path), "-"],
           input="a completely different ask, never what row 1 actually says", env=gpg_env)
        rc = run_verify_commission(world_dir, commission_id=commission_id)
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
        rd = run_verify_commission(world_dir, commission_id=commission_id)
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
        re_ = run_verify_commission(world_dir, commission_id=commission_id, path_override=no_gpg_path)
        ok_e = re_.returncode == 2 and "gpg" in (re_.stdout + re_.stderr).lower()
        check("e-gpg-absent-typed-refusal", ok_e,
              f"exit={re_.returncode} stderr={(re_.stdout + re_.stderr).strip()[:200]!r}", failures)

        # --- h: FIX-ROUND ADDITION (kernel review, s61 tip c3d773a) -- a SECOND throwaway key
        # independently signs the SAME statement; the two detached signatures (each individually
        # genuine, gpg verifies BOTH) are concatenated into ONE `.claude/commission-<id>.asc` --
        # this verb's OWN MULTIPLE-VALID-SIGNATURES catch (main()'s `except
        # gpg_trust.MultipleValidSignatures` block) had zero shipped fixture coverage before this
        # case: run_fixtures_cli.py's case j only exercises led.tmpl's attest-possession leg,
        # never this verb's. Mirrors the reviewer's own ad hoc probe (never shipped) --
        # gen_key/gpg_env technique already established by case b above, reused rather than
        # re-derived.
        test_fpr2 = gen_key(gnupghome, "AUTOHARN TEST KEY 2 -- THROWAWAY -- SEEN-RED FIXTURE",
                             "verify-commission-seenred-test-2@example.invalid")
        sig1_asc = tmp / "h-sig1.asc"
        sig2_asc = tmp / "h-sig2.asc"
        rsign1 = sh(["gpg", "--homedir", str(gnupghome), "-u", test_fpr, "--batch", "--yes",
                     "--detach-sign", "--armor", "-o", str(sig1_asc), "-"], input=statement, env=gpg_env)
        rsign2 = sh(["gpg", "--homedir", str(gnupghome), "-u", test_fpr2, "--batch", "--yes",
                     "--detach-sign", "--armor", "-o", str(sig2_asc), "-"], input=statement, env=gpg_env)
        asc_path.write_text(sig1_asc.read_text(encoding="utf-8") + sig2_asc.read_text(encoding="utf-8"),
                             encoding="utf-8")
        r_export2 = sh(["gpg", "--homedir", str(gnupghome), "--armor", "--export", test_fpr2])
        (keys_dir / "test-key-2.asc").write_text(r_export2.stdout, encoding="utf-8")
        rh = run_verify_commission(world_dir, commission_id=commission_id, attest=True)
        body_h = json.loads(rh.stdout) if rh.stdout.strip() else {}
        ok_h = (rsign1.returncode == 0 and rsign2.returncode == 0 and rh.returncode == 4
                and body_h.get("refusal") == "MULTIPLE-VALID-SIGNATURES"
                and test_fpr in body_h.get("detail", "") and test_fpr2 in body_h.get("detail", ""))
        check("h-multi-signature-attest-refused", ok_h,
              f"sign1_exit={rsign1.returncode} sign2_exit={rsign2.returncode} exit={rh.returncode} "
              f"refusal={body_h.get('refusal')} detail={body_h.get('detail', '')[:250]!r}", failures)

    finally:
        try:
            bs_fixtures.stop_server(proc)
        except NameError:
            pass  # scaffold itself failed before `proc` was ever assigned
        teardown_world()
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- verify-commission both-polarity proof (UNSIGNED / VERIFIED / "
          "FORGED-OR-CORRUPT / NO-COMMITTED-KEY-refusal / GPG-UNAVAILABLE-refusal / "
          "MULTIPLE-VALID-SIGNATURES-refusal), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
