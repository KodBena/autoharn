#!/usr/bin/env python3
"""run_fixtures_cli.py -- VERB-SIDE, SERVED-CLI, REAL-GPG proof for the two v1.1 write paths this
delta's kernel-side checks (kernel/lineage/s61-signature-symmetry-and-key-binding.sql) depend on:
bootstrap/templates/verify-commission.tmpl's `--attest` mode (item 1) and bootstrap/templates/
led.tmpl's `led principal attest-possession` + `bind-key --possession-ref` wiring (item 3).
Complements seen-red/s61-signature-symmetry-and-key-binding/run_fixtures.py (which drives the
kernel boundary functions DIRECTLY to prove the SQL refusals fire correctly) by proving the SAME
mechanism end-to-end through the REAL served `led` CLI and a REAL ed25519 keypair, exactly the
technique seen-red/verify-commission/run_fixtures.py already established for item 2.

Real infra, no mocks: a CLASSIC scaffold (chain s15..s61) + a real `serving.boundary_service`
(seen-red/boundary-service's own `serve_existing_world`) + a throwaway GNUPGHOME (Ed25519 test
key, generated fresh per run, clearly marked test-only). Torn down before AND after.

Cases:
  a-attest-directory-verified -- LED_ACTOR=commissioner writes a commission; the test key signs
                                  it; `./verify-commission --attest --id <id> --json` reports
                                  VERIFIED at DIRECTORY-VERIFIED grade (no s41 binding exists yet)
                                  AND writes the commission_signature_verified marker row.
  b-unsigned-supersession-refused -- `./led commission "..." --supersedes <id>` (no
                                  --signature-witness) is REFUSED by s61's kernel-side symmetry
                                  check, through the served boundary, exit code 1.
  c-signed-supersession-accepted -- the SAME supersession, now carrying
                                  `--signature-witness <attest-row-id>`, is ACCEPTED.
  d-attest-possession-and-bind -- `./led principal attest-possession <fp> --asc <sig>` verifies
                                  proof of possession and writes the marker row; `./led principal
                                  bind-key keyholder --fingerprint <fp> --possession-ref <id>` is
                                  then ACCEPTED.
  e-bind-without-possession-ref-refused -- the SAME bind, omitting --possession-ref, is REFUSED
                                  client-side (led.tmpl's own teaching refusal) before any write
                                  is even attempted.

FIX-ROUND ADDITIONS (kernel review, s61 tip c3d773a -- three legs the reviewer had to witness
personally rather than finding shipped as fixture cases, plus one untested gpg_trust.py finding):
  f-never-signed-zero-friction-supersession -- an ORDINARY, never-signed commission superseded by
                                  an ORDINARY, never-signed commission -- ACCEPTED, no false
                                  symmetry demand (neither act's force rests on a verified
                                  signature, so the symmetry block never fires).
  g-wrong-key-attest-possession-refused -- a SECOND throwaway key signs the possession statement
                                  for the FIRST key's own claimed fingerprint -- REFUSED, teaching,
                                  naming BOTH fingerprints (proof of possession must come from the
                                  EXACT key being proven, never merely some committed key).
  h-revoke-key-missing-supersedes-refused -- `led principal revoke-key` with no --supersedes --
                                  REFUSED, its OWN refusal-path flag parsing (distinct from
                                  bind-key's mandatory-possession-ref).
  i-revoke-key-cli-path-accepted -- `led principal revoke-key` THROUGH THE REAL CLI (never the raw
                                  kernel retraction a reviewer had to fall back to), citing the
                                  case-d bind row via --supersedes -- ACCEPTED, no fresh possession
                                  proof required (item 3: revocation needs none).
  j-multi-signature-attest-possession-refused -- a .asc carrying TWO valid signatures (one per
                                  key, both verifying, concatenated) -- REFUSED:
                                  filing/gpg_trust.py's signing_key_fingerprint cannot honestly
                                  pick ONE signer arbitrarily (an earlier version silently
                                  returned the first VALIDSIG, untested until this case).

Usage: python3 seen-red/s61-signature-symmetry-and-key-binding/run_fixtures_cli.py
Exit 0 if every case matches; 1 otherwise. Lazy imports are banned."""
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

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LINEAGE = REPO / "kernel" / "lineage"

sys.path.insert(0, str(REPO / "seen-red"))
from _fixture_env import fixture_pghost  # noqa: E402

os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", REPO / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)

PGHOST, PGDB = fixture_pghost(), "toy"
WORLD = "s61clifxprobe"

CHAIN_S61 = [
    "high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql", "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql", "s31-supersession-uniform-retraction.sql",
    "s32-edge-views-single-home.sql", "s33-composite-discharge.sql",
    "s34-computed-grade-refusal.sql", "s35-validation-decomposition.sql",
    "s36-decision-grade.sql", "s37-violation-disposition.sql",
    "s38-bookkeeping-close.sql", "s39-blocks-start.sql",
    "s40-principal-identity-events.sql", "s41-principal-bindings-and-relations.sql",
    "s42-row-hash-full-coverage.sql", "s43-typed-verdict-write-boundary.sql",
    "s44-model-identity-attestation.sql", "s45-standing-lifecycle.sql",
    "s46-credited-views.sql", "s47-claim-on-closed-refusal.sql",
    "s48-review-witness-existence.sql", "s49-journaler-overflow-guard.sql",
    "s50-defeat-input-raw-domain.sql", "s51-artifact-store.sql",
    "s52-artifact-witness-check.sql", "s53-belief-substrate.sql",
    "s54-belief-views.sql", "s55-dispatch-grain-independence.sql",
    "s56-reservation-residue.sql", "s57-obligation-revocation-event.sql",
    "s58-missive-substrate.sql", "s59-missive-views.sql",
    "s60-entitlement-enforcement.sql", "s61-signature-symmetry-and-key-binding.sql",
]

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


def teardown_world(schema: str, kern: str, role: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE; "
        f"DROP OWNED BY {role};"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {role};"])


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def gen_key(gnupghome: Path, name: str, email: str) -> str:
    batch = gnupghome / f"keygen-{email}.batch"
    batch.write_text(KEYGEN_BATCH_TEMPLATE.format(name=name, email=email), encoding="utf-8")
    r = sh(["gpg", "--homedir", str(gnupghome), "--batch", "--generate-key", str(batch)])
    if r.returncode != 0:
        raise RuntimeError(f"gpg keygen failed: {r.stderr}")
    r = sh(["gpg", "--homedir", str(gnupghome), "--list-secret-keys", "--with-colons"])
    fprs = [ln.split(":")[9] for ln in r.stdout.splitlines() if ln.startswith("fpr")]
    return fprs[-1]


def led(world_dir: Path, *args: str, env_extra: dict | None = None) -> subprocess.CompletedProcess[str]:
    # §6 amendment (2026-07-26, rows 1357/1365/1366/1367): a scaffolded world no longer has a
    # standalone `led` shim -- routed through the ONE `autoharn` dispatcher instead (root-shim-
    # pruning residue sweep, ledger row 1357).
    env = dict(os.environ)
    env["AUTOHARN"] = str(REPO)
    env["PICKUP_DEPLOYMENT"] = str(world_dir / "deployment.json")
    if env_extra:
        env.update(env_extra)
    return sh(["bash", str(world_dir / "autoharn"), "led", *args], env=env, cwd=str(world_dir))


def verify_commission(world_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["AUTOHARN"] = str(REPO)
    env["PICKUP_DEPLOYMENT"] = str(world_dir / "deployment.json")
    return sh(["python3", str(REPO / "bootstrap" / "templates" / "verify-commission.tmpl"),
               *args], env=env, cwd=str(world_dir))


def row_id_from_stdout(stdout: str) -> int:
    m = re.search(r"row (\d+) written", stdout) or re.search(r'"row_id":\s*(\d+)', stdout)
    if not m:
        raise RuntimeError(f"could not parse a row id from: {stdout!r}")
    return int(m.group(1))


def main() -> int:
    schema, kern, role = WORLD, f"{WORLD}_kernel", f"{WORLD}_rw"
    failures: list[str] = []
    teardown_world(schema, kern, role)
    tmp = Path(tempfile.mkdtemp(prefix="s61-cli-seenred-"))
    world_dir = tmp / WORLD
    gnupghome = tmp / "gnupghome"
    gnupghome.mkdir(mode=0o700)
    keys_dir = world_dir / "keys"
    proc = None
    try:
        print("== generating throwaway test key (Ed25519, test-only) ==")
        test_fpr = gen_key(gnupghome, "AUTOHARN TEST KEY -- THROWAWAY -- S61 CLI SEEN-RED",
                            "s61-cli-seenred-test@example.invalid")
        print(f"  test key: {test_fpr}\n")

        print(f"== classic scaffold {WORLD} + manual chain apply (s15..s61) ==")
        r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--db", PGDB, "--host", PGHOST,
                "--schema", schema, "--kern", kern, "--role", role])
        if r.returncode != 0:
            print("SCAFFOLD FAILED:", r.stdout[-1500:], r.stderr[-1500:]); return 1
        # §6 amendment (2026-07-26, rows 1357/1365/1366/1367): a scaffolded world writes ONE
        # `autoharn` dispatcher now, not separate per-verb shim files (root-shim-pruning residue
        # sweep, ledger row 1357) -- new-project.sh already writes it chmod +x, but re-assert
        # here defensively (matches this fixture's own pre-existing belt-and-suspenders posture).
        (world_dir / "autoharn").chmod(0o755)
        args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
                "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
        for name in CHAIN_S61:
            args += ["-f", str(LINEAGE / name)]
        ra = sh(args)
        if ra.returncode != 0:
            print("CHAIN APPLY FAILED:", ra.stdout[-2000:], ra.stderr[-2000:]); return 1
        hexsecret = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
            "-c", f"TRUNCATE {kern}.stamp_secret;",
            "-c", f"INSERT INTO {kern}.stamp_secret (secret) VALUES (decode('{hexsecret}','hex'));"])
        genesis_hex = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
            "-c", f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis_hex}') "
                  f"ON CONFLICT (only_one) DO NOTHING;"])

        # birth via the boundary functions directly (classic mode applies no lineage chain
        # and performs no birth of its own -- mirrors run_fixtures.py's birth_via_boundary()).
        author = psql_tuples(f"SELECT id FROM {kern}.principal WHERE name='author';")
        login_role = psql_tuples("SELECT session_user;")

        def bw(fn: str, payload: dict) -> dict:
            pj = json.dumps(payload).replace("'", "''")
            rr = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"],
                    input=f"SET ROLE {role};\nSET search_path = {schema}, {kern};\n"
                          f"SELECT to_jsonb(v) FROM {kern}.{fn}('{pj}'::jsonb) v;\n")
            if rr.returncode != 0:
                raise RuntimeError(f"boundary call failed: {rr.stderr[-500:]}")
            lines = [ln for ln in rr.stdout.splitlines() if ln.strip().startswith("{")]
            return json.loads(lines[-1])

        for fn, payload in [
            ("ledger_write", {"kind": "principal_registered",
                              "statement": "author registered (fixture genesis exception)",
                              "actor": author, "principal_subject": author,
                              "principal_purpose": "fixture connection principal"}),
            ("ledger_write", {"kind": "principal_standing_declared",
                              "statement": f"role {role} -> author", "actor": author,
                              "principal_subject": author, "principal_db_role": role,
                              "principal_binding_active": "true"}),
            ("ledger_write", {"kind": "principal_standing_declared",
                              "statement": f"login role {login_role} -> author (dual declaration)",
                              "actor": author, "principal_subject": author,
                              "principal_db_role": login_role,
                              "principal_binding_active": "true"}),
            ("registration_write", {"name": "write-boundary", "agent_class": "tool",
                                    "actor": author,
                                    "purpose": "s61 CLI fixture's own write-boundary registration"}),
            ("registration_write", {"name": "commissioner", "agent_class": "human",
                                    "actor": author, "purpose": "FULL-mode commission signer"}),
            ("registration_write", {"name": "keyholder", "agent_class": "human",
                                    "actor": author, "purpose": "s61 CLI fixture key-binding subject"}),
        ]:
            v = bw(fn, payload)
            if v["disposition"] != "accepted":
                raise RuntimeError(f"birth act refused: {v}")

        print("== standing served boundary_service ==")
        proc = bs_fixtures.serve_existing_world(world_dir / "deployment.json", tmp)
        print("  served OK.\n")

        # ---- a: FULL-mode commission, signed, --attest -> VERIFIED @ DIRECTORY-VERIFIED ----
        statement = "the maintainer asked for X (s61 CLI fixture commission C1)"
        rc1 = led(world_dir, "commission", statement, env_extra={"LED_ACTOR": "commissioner"})
        if rc1.returncode != 0:
            print("COMMISSION WRITE FAILED:", rc1.stdout, rc1.stderr); return 1
        c1 = row_id_from_stdout(rc1.stdout)

        gpg_env = {"GNUPGHOME": str(gnupghome), "PATH": "/usr/bin:/bin:/usr/local/bin"}
        asc_path = world_dir / ".claude" / f"commission-{c1}.asc"
        rsign = sh(["gpg", "--batch", "--yes", "--detach-sign", "--armor", "-o", str(asc_path), "-"],
                   input=statement, env=gpg_env)
        keys_dir.mkdir(parents=True, exist_ok=True)
        r_export = sh(["gpg", "--homedir", str(gnupghome), "--armor", "--export", test_fpr])
        (keys_dir / "test-key.asc").write_text(r_export.stdout, encoding="utf-8")

        ra_attest = verify_commission(world_dir, "--attest", "--id", str(c1), "--json")
        body_a = json.loads(ra_attest.stdout) if ra_attest.stdout.strip() else {}
        ok_a = (rsign.returncode == 0 and ra_attest.returncode == 0
                and body_a.get("verdict") == "VERIFIED" and body_a.get("grade") == "DIRECTORY-VERIFIED"
                and body_a.get("attest", {}).get("disposition") == "accepted")
        check("a-attest-directory-verified", ok_a,
              f"sign_exit={rsign.returncode} attest_exit={ra_attest.returncode} body={body_a}",
              failures)
        att_row = body_a.get("attest", {}).get("row_id")

        # ---- b: unsigned supersession of C1 -- refused by s61's kernel check ----
        # NOTE: shared flags are FRONT-ANCHORED (row 1173 finding 1) -- they must precede the
        # kind/statement words, never follow them (`led --supersedes <id> commission "..."`,
        # not `led commission "..." --supersedes <id>`).
        rb = led(world_dir, "--supersedes", str(c1), "commission",
                 "an unsigned supersession attempt of C1")
        check("b-unsigned-supersession-refused",
              rb.returncode == 1 and "SIGNED supersession symmetry" in (rb.stdout + rb.stderr),
              f"exit={rb.returncode} out={(rb.stdout + rb.stderr)[-400:]!r}", failures)

        # ---- c: the SAME supersession, carrying --signature-witness -- accepted ----
        ok_c = False
        detail_c = ""
        if att_row:
            rcw = led(world_dir, "--supersedes", str(c1), "--signature-witness", str(att_row),
                      "commission", "a SIGNED supersession of C1, citing its attestation")
            ok_c = rcw.returncode == 0
            detail_c = f"exit={rcw.returncode} out={(rcw.stdout + rcw.stderr)[-300:]!r}"
        else:
            detail_c = "SKIPPED -- no attestation row id available from case a"
        check("c-signed-supersession-accepted", ok_c, detail_c, failures)

        # ---- d: attest-possession + bind-key --possession-ref -- accepted ----
        fp = test_fpr
        possess_statement = f"autoharn key-binding proof-of-possession: fingerprint={fp}"
        possess_asc = tmp / "possession.asc"
        rsign2 = sh(["gpg", "--batch", "--yes", "--detach-sign", "--armor", "-o", str(possess_asc), "-"],
                    input=possess_statement, env=gpg_env)
        rd1 = led(world_dir, "principal", "attest-possession", fp, "--asc", str(possess_asc))
        ok_d1 = rd1.returncode == 0
        possess_row = row_id_from_stdout(rd1.stdout) if ok_d1 else None
        ok_d2 = False
        bind_row = None
        if possess_row:
            rd2 = led(world_dir, "principal", "bind-key", "keyholder", "--fingerprint", fp,
                      "--possession-ref", str(possess_row))
            ok_d2 = rd2.returncode == 0
            bind_row = row_id_from_stdout(rd2.stdout) if ok_d2 else None
        check("d-attest-possession-and-bind", ok_d1 and ok_d2,
              f"attest_exit={rd1.returncode} possess_row={possess_row} bind_ok={ok_d2} "
              f"attest_out={rd1.stdout[-300:]!r}", failures)

        # ---- e: bind-key WITHOUT --possession-ref -- refused client-side ----
        re_ = led(world_dir, "principal", "bind-key", "keyholder", "--fingerprint",
                  "0000000000000000000000000000000000000000")
        check("e-bind-without-possession-ref-refused",
              re_.returncode == 1 and "possession-ref" in (re_.stdout + re_.stderr),
              f"exit={re_.returncode} out={(re_.stdout + re_.stderr)[-300:]!r}", failures)

        # fix-round additions (kernel review, s61 tip c3d773a) -- the three named gaps a
        # reviewer had to plug personally rather than finding shipped: never-signed zero-friction
        # supersession, wrong-key attest-possession, and the revoke-key CLI path (accept + its
        # own refusal-path flag parsing) -- plus the gpg_trust.py multi-signature finding.

        # ---- f: an ORDINARY, never-signed commission superseded by an ORDINARY, never-signed
        # commission -- accepted, no false symmetry demand (neither act's force rests on a
        # verified signature, so validate_supersession_target's symmetry block never fires) ----
        rc2 = led(world_dir, "commission", "an ordinary, never-signed commission (C2, fixture)",
                  env_extra={"LED_ACTOR": "commissioner"})
        ok_f1 = rc2.returncode == 0
        c2 = row_id_from_stdout(rc2.stdout) if ok_f1 else None
        ok_f2 = False
        if c2:
            rf = led(world_dir, "--supersedes", str(c2), "commission",
                     "an ordinary, never-signed supersession of C2 (fixture)")
            ok_f2 = rf.returncode == 0
        check("f-never-signed-zero-friction-supersession", ok_f1 and ok_f2,
              f"c2_exit={rc2.returncode} c2={c2} supersede_exit={rf.returncode if c2 else None}",
              failures)

        # ---- g: a SECOND throwaway key signs the possession statement for the FIRST key's own
        # fingerprint -- refused, teaching, naming both fingerprints (never merely "some
        # committed key", the EXACT key being proven) ----
        test_fpr2 = gen_key(gnupghome, "AUTOHARN TEST KEY 2 -- THROWAWAY -- S61 CLI SEEN-RED",
                             "s61-cli-seenred-test2@example.invalid")
        r_export2 = sh(["gpg", "--homedir", str(gnupghome), "--armor", "--export", test_fpr2])
        (keys_dir / "test-key-2.asc").write_text(r_export2.stdout, encoding="utf-8")
        wrongkey_asc = tmp / "wrongkey-possession.asc"
        rsign_wrong = sh(["gpg", "--homedir", str(gnupghome), "-u", test_fpr2, "--batch", "--yes",
                          "--detach-sign", "--armor", "-o", str(wrongkey_asc), "-"],
                         input=possess_statement, env=gpg_env)
        rg1 = led(world_dir, "principal", "attest-possession", fp, "--asc", str(wrongkey_asc))
        out_g = rg1.stdout + rg1.stderr
        check("g-wrong-key-attest-possession-refused",
              rsign_wrong.returncode == 0 and rg1.returncode == 1
              and "produced by fingerprint" in out_g and test_fpr2 in out_g and fp in out_g,
              f"sign_exit={rsign_wrong.returncode} exit={rg1.returncode} out={out_g[-400:]!r}",
              failures)

        # ---- h: revoke-key WITHOUT --supersedes -- refused, its own refusal-path flag parsing
        # (mandatory-supersedes, distinct from bind-key's mandatory-possession-ref) ----
        rh = led(world_dir, "principal", "revoke-key", "keyholder", "--fingerprint", fp)
        out_h = rh.stdout + rh.stderr
        check("h-revoke-key-missing-supersedes-refused",
              rh.returncode == 1 and "--supersedes" in out_h and "mandatory" in out_h,
              f"exit={rh.returncode} out={out_h[-300:]!r}", failures)

        # ---- i: revoke-key THROUGH THE REAL CLI PATH (never the raw kernel retraction a
        # reviewer had to fall back to) -- --supersedes the case-d bind row -- accepted, no fresh
        # possession proof required (item 3's own text: revocation needs none) ----
        ok_i = False
        detail_i = ""
        if bind_row:
            ri = led(world_dir, "principal", "revoke-key", "keyholder", "--fingerprint", fp,
                     "--supersedes", str(bind_row))
            ok_i = ri.returncode == 0
            detail_i = f"exit={ri.returncode} out={(ri.stdout + ri.stderr)[-300:]!r}"
        else:
            detail_i = "SKIPPED -- no bind row id available from case d"
        check("i-revoke-key-cli-path-accepted", ok_i, detail_i, failures)

        # ---- j: a .asc carrying TWO valid signatures (concatenated detached signature packets,
        # one per key, both verifying) -- refused: gpg_trust.py's signing_key_fingerprint cannot
        # honestly pick ONE signer arbitrarily (fix-round finding, first-VALIDSIG-wins was
        # untested) ----
        multisig_asc = tmp / "multisig-possession.asc"
        multisig_asc.write_text(possess_asc.read_text(encoding="utf-8")
                                 + wrongkey_asc.read_text(encoding="utf-8"), encoding="utf-8")
        rj = led(world_dir, "principal", "attest-possession", fp, "--asc", str(multisig_asc))
        out_j = rj.stdout + rj.stderr
        check("j-multi-signature-attest-possession-refused",
              rj.returncode == 1 and "more than one valid signature" in out_j,
              f"exit={rj.returncode} out={out_j[-400:]!r}", failures)

    finally:
        try:
            if proc is not None:
                bs_fixtures.stop_server(proc)
        except Exception:  # noqa: BLE001
            pass
        teardown_world(schema, kern, role)
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'ALL GREEN' if not failures else 'FAILURES: ' + ', '.join(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
