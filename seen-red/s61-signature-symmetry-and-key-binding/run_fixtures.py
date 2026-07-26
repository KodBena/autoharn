#!/usr/bin/env python3
"""run_fixtures.py -- KERNEL-LEVEL both-polarity proof for kernel/lineage/
s61-signature-symmetry-and-key-binding.sql (design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §2's
witness plan, items 1 and 3). Real infra, no mocks: a CLASSIC scaffold + manual chain apply
(s15..s61) in the TOY db, torn down before AND after -- the SAME technique
seen-red/s60-entitlement-enforcement/run_fixtures.py already established for a delta whose
PREREQUISITE chain (s58/s59/s60) is not yet wired into bootstrap/new-project.sh's LINEAGE_CHAIN.

SCOPE, STATED HONESTLY: this fixture drives the boundary functions DIRECTLY (kernel.ledger_write/
registration_write), the same way s60's own fixture does -- it proves the KERNEL-SIDE refusals
(Elements 6/7/8 of s61) fire correctly, independent of whether the real gpg check that SHOULD
precede a well-formed commission_signature_verified / principal_key_possession_verified row in
production actually ran. The VERB-SIDE real-gpg legs (bootstrap/templates/verify-commission.tmpl's
--attest mode; bootstrap/templates/led.tmpl's attest-possession/bind-key wiring) are witnessed
SEPARATELY -- see this delta's own report for which legs that covers. This split mirrors how
s60's own fixture proves the SQL/ASP layer while a DIFFERENT witness (seen-red/verify-commission)
proves the gpg-adjacent verb layer -- the two are complementary, never a substitute for each
other.

Per the spec §6, red first:
  RED 1 (item 1)  -- an UNSIGNED supersession of a SIGNED (attested) commission is refused,
                      journaled, taught text naming the missing signature_symmetry_witness.
  RED 1b (item 1) -- a FORGED-shaped attempt: a signature_symmetry_witness naming a row that is
                      NOT a commission_signature_verified row is refused at construction
                      (validate_signature_witness, well-formedness).
  RED 3 (item 3)  -- a FRESH principal_key_bound with NO key_binding_possession_ref is refused
                      by the CHECK constraint (kind-shape mandatory-on-fresh-bind).
  RED 3b (item 3) -- a FRESH bind whose key_binding_possession_ref names a row that is NOT a
                      principal_key_possession_verified row is refused (validate_principal_binding).
  RED 3c (item 3) -- a FRESH bind whose key_binding_possession_ref proves possession of a
                      DIFFERENT fingerprint than the one being bound is refused (fingerprint
                      mismatch).
  GREEN 1         -- a commission SIGNED (attested) supersession, carrying a valid
                      signature_symmetry_witness naming an independent commission_signature_
                      verified row, is ACCEPTED.
  GREEN 3         -- a FRESH principal_key_bound citing a matching principal_key_possession_
                      verified row is ACCEPTED; the retraction (active=false) of that SAME
                      binding needs NO possession ref at all (item 3's own text: revocation is a
                      GPG revocation cert + this retraction event, never a second signature).
  GREEN-zero-friction -- an ORDINARY (non-gated) write's verdict shape is IDENTICAL pre-s61 vs
                      post-s61 (byte-compared), proving this delta adds zero friction to acts it
                      does not concern.

Each check() names the witness that would show it false. Usage:
    python3 seen-red/s61-signature-symmetry-and-key-binding/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports are banned."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LINEAGE = REPO / "kernel" / "lineage"
sys.path.insert(0, str(REPO / "filing"))

import pghost_resolve  # noqa: E402

os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S60 = [
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
    "s60-entitlement-enforcement.sql",
]
CHAIN_S61 = CHAIN_S60 + ["s61-signature-symmetry-and-key-binding.sql"]

FP1 = "AAAA0000111122223333444455556666777788889"[:40].ljust(40, "0")
FP2 = "BBBB0000111122223333444455556666777788889"[:40].ljust(40, "0")


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown(world: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {world} CASCADE; DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "
        f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def psql_raw(script: str) -> subprocess.CompletedProcess[str]:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"],
              input=script)


def scaffold_classic(world: str, chain: list[str]) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    schema, kern, role = world, f"{world}_kernel", f"{world}_rw"
    r = sh(["bash", str(NEW_PROJECT), str(world_dir),
            "--db", PGDB, "--host", PGHOST,
            "--schema", schema, "--kern", kern, "--role", role])
    if r.returncode != 0:
        raise RuntimeError(f"CLASSIC SCAFFOLD FAILED ({world}): {r.stdout[-1500:]} {r.stderr[-1500:]}")
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for name in chain:
        args += ["-f", str(LINEAGE / name)]
    ra = sh(args)
    if ra.returncode != 0:
        raise RuntimeError(f"CLASSIC apply FAILED ({world}): {ra.stdout[-1500:]} {ra.stderr[-1500:]}")
    hexsecret = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"TRUNCATE {kern}.stamp_secret;",
        "-c", f"INSERT INTO {kern}.stamp_secret (secret) VALUES (decode('{hexsecret}','hex'));"])
    genesis_hex = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis_hex}') "
              f"ON CONFLICT (only_one) DO NOTHING;"])
    return world_dir


def bw_call(world: str, fn: str, payload: dict) -> dict:
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    pj = json.dumps(payload).replace("'", "''")
    r = psql_raw(
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"SELECT to_jsonb(v) FROM {K}.{fn}('{pj}'::jsonb) v;\n")
    if r.returncode != 0:
        raise RuntimeError(f"NON-VERDICT: {r.stderr.strip()[-800:]}")
    lines = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("{")]
    if not lines:
        raise RuntimeError(f"NO VERDICT LINE: stdout={r.stdout!r} stderr={r.stderr!r}")
    return json.loads(lines[-1])


def birth_via_boundary(world: str) -> str:
    """s40/s43 birth acts through the boundary: author event, dual standing declarations
    (principal_binding_active true, s45-required), write-boundary registration. Returns author's
    principal id (text)."""
    K = f"{world}_kernel"
    author = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='author';")
    login_role = psql_tuples("SELECT session_user;")
    for fn, payload in [
        ("ledger_write", {"kind": "principal_registered",
                          "statement": "author registered (fixture genesis exception)",
                          "actor": author, "principal_subject": author,
                          "principal_purpose": "fixture connection principal"}),
        ("ledger_write", {"kind": "principal_standing_declared",
                          "statement": f"role {world}_rw -> author", "actor": author,
                          "principal_subject": author, "principal_db_role": f"{world}_rw",
                          "principal_binding_active": "true"}),
        ("ledger_write", {"kind": "principal_standing_declared",
                          "statement": f"login role {login_role} -> author (dual declaration)",
                          "actor": author, "principal_subject": author,
                          "principal_db_role": login_role,
                          "principal_binding_active": "true"}),
        ("registration_write", {"name": "write-boundary", "agent_class": "tool",
                                "actor": author,
                                "purpose": "s61 fixture's own write-boundary registration"}),
    ]:
        v = bw_call(world, fn, payload)
        if v["disposition"] != "accepted":
            raise RuntimeError(f"birth act refused: {v}")
    return author


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    world_red, world_pre = "s61fxred", "s61fxpre"
    for w in (world_red, world_pre):
        teardown(w)
    try:
        # ================= RED/GREEN world (chain s15..s61) =================
        print(f"== scaffolding classic world {world_red} (chain ends {CHAIN_S61[-1]}) ==")
        wr = scaffold_classic(world_red, CHAIN_S61)
        tmps.append(wr.parent)
        author = birth_via_boundary(world_red)

        # ---- item 1 setup: two commission rows, one attested (SIGNED), one not ----
        v_c1 = bw_call(world_red, "ledger_write", {
            "kind": "commission", "actor": author,
            "statement": "the maintainer asked for X (fixture commission C1)"})
        v_c2 = bw_call(world_red, "ledger_write", {
            "kind": "commission", "actor": author,
            "statement": "a SECOND, independent commission (fixture C2, will attest C1)"})
        c1, c2 = v_c1["row_id"], v_c2["row_id"]
        if v_c1["disposition"] != "accepted" or v_c2["disposition"] != "accepted":
            raise RuntimeError(f"could not write commissions: {v_c1} {v_c2}")

        # the attestation row (mirrors what verify-commission --attest would write after its OWN
        # real gpg check -- this fixture drives the boundary directly, per its own module
        # docstring SCOPE note, to isolate the kernel-side refusal from the verb-side gpg leg).
        v_att = bw_call(world_red, "ledger_write", {
            "kind": "commission_signature_verified", "actor": author,
            "statement": f"commission {c1} independently GPG-verified (fixture attestation)",
            "signature_attests_row": c1, "signature_grade": "directory-verified",
            "principal_key_fingerprint": FP1})
        if v_att["disposition"] != "accepted":
            raise RuntimeError(f"could not attest C1: {v_att}")
        att_row = v_att["row_id"]

        # ---- RED 1: an UNSIGNED supersession of the now-SIGNED C1 -- refused ----
        v_unsigned_supersede = bw_call(world_red, "ledger_write", {
            "kind": "commission", "actor": author, "supersedes": c1,
            "statement": "an unsigned attempt to supersede the SIGNED commission C1"})
        check("RED-1-unsigned-supersession-of-signed-act-refused",
              v_unsigned_supersede["disposition"] == "refused"
              and "SIGNED supersession symmetry" in v_unsigned_supersede["message"],
              f"verdict={v_unsigned_supersede}", failures)

        # ---- RED 1b: a signature_symmetry_witness naming a NON-attestation row -- refused ----
        v_malformed_witness = bw_call(world_red, "ledger_write", {
            "kind": "commission", "actor": author, "supersedes": c1,
            "signature_symmetry_witness": c2,  # c2 is a plain commission, NOT an attestation
            "statement": "a supersession claiming a witness that is not an attestation row"})
        check("RED-1b-malformed-witness-refused",
              v_malformed_witness["disposition"] == "refused"
              and "commission_signature_verified row" in v_malformed_witness["message"],
              f"verdict={v_malformed_witness}", failures)

        # ---- GREEN 1: a SIGNED supersession (carrying the genuine attestation row) -- accepted
        v_signed_supersede = bw_call(world_red, "ledger_write", {
            "kind": "commission", "actor": author, "supersedes": c1,
            "signature_symmetry_witness": att_row,
            "statement": "a SIGNED supersession of C1, citing its own attestation row"})
        check("GREEN-1-signed-supersession-accepted",
              v_signed_supersede["disposition"] == "accepted",
              f"verdict={v_signed_supersede}", failures)

        # ---- item 3 setup ----
        holder = psql_tuples(  # a fresh HUMAN principal to bind a key to (s41 D-3: human-only)
            f"SELECT id FROM {world_red}_kernel.principal WHERE name='author';")
        v_reg_human = bw_call(world_red, "registration_write", {
            "name": "keyholder", "agent_class": "human", "actor": author,
            "purpose": "s61 fixture key-binding subject"})
        if v_reg_human["disposition"] != "accepted":
            raise RuntimeError(f"could not register keyholder: {v_reg_human}")
        keyholder = psql_tuples(f"SELECT id FROM {world_red}_kernel.principal WHERE name='keyholder';")

        # ---- RED 3: a FRESH bind with NO key_binding_possession_ref -- refused (CHECK) ----
        v_bind_no_ref = bw_call(world_red, "ledger_write", {
            "kind": "principal_key_bound", "actor": author,
            "statement": "keyholder binds FP1 with no possession proof",
            "principal_subject": keyholder, "principal_key_fingerprint": FP1,
            "principal_binding_active": "true"})
        check("RED-3-fresh-bind-no-possession-ref-refused",
              v_bind_no_ref["disposition"] == "refused",
              f"verdict={v_bind_no_ref}", failures)

        # ---- RED 3b: key_binding_possession_ref names a row that is NOT a possession proof ----
        v_bind_wrong_kind_ref = bw_call(world_red, "ledger_write", {
            "kind": "principal_key_bound", "actor": author,
            "statement": "keyholder binds FP1 citing an ordinary decision row as 'proof'",
            "principal_subject": keyholder, "principal_key_fingerprint": FP1,
            "principal_binding_active": "true", "key_binding_possession_ref": c1})
        check("RED-3b-possession-ref-wrong-kind-refused",
              v_bind_wrong_kind_ref["disposition"] == "refused"
              and "principal_key_possession_verified row" in v_bind_wrong_kind_ref["message"],
              f"verdict={v_bind_wrong_kind_ref}", failures)

        # the GENUINE possession proof for FP1 (mirrors what `led principal attest-possession`
        # would write after its OWN real gpg check -- see this fixture's SCOPE note).
        v_possess_fp1 = bw_call(world_red, "ledger_write", {
            "kind": "principal_key_possession_verified", "actor": author,
            "statement": f"autoharn key-binding proof-of-possession: fingerprint={FP1} "
                         f"principal=keyholder (fixture proof)",
            "principal_key_fingerprint": FP1})
        if v_possess_fp1["disposition"] != "accepted":
            raise RuntimeError(f"could not write possession proof: {v_possess_fp1}")
        possess_fp1_row = v_possess_fp1["row_id"]

        # ---- RED 3c: possession proof for FP1, but the bind claims FP2 -- mismatch refused ----
        v_bind_fp_mismatch = bw_call(world_red, "ledger_write", {
            "kind": "principal_key_bound", "actor": author,
            "statement": "keyholder binds FP2 citing FP1's possession proof",
            "principal_subject": keyholder, "principal_key_fingerprint": FP2,
            "principal_binding_active": "true", "key_binding_possession_ref": possess_fp1_row})
        check("RED-3c-fingerprint-mismatch-refused",
              v_bind_fp_mismatch["disposition"] == "refused"
              and "authorizes ONLY the exact fingerprint" in v_bind_fp_mismatch["message"],
              f"verdict={v_bind_fp_mismatch}", failures)

        # ---- GREEN 3: a FRESH bind citing the MATCHING possession proof -- accepted ----
        v_bind_ok = bw_call(world_red, "ledger_write", {
            "kind": "principal_key_bound", "actor": author,
            "statement": "keyholder binds FP1, proof matches",
            "principal_subject": keyholder, "principal_key_fingerprint": FP1,
            "principal_binding_active": "true", "key_binding_possession_ref": possess_fp1_row})
        check("GREEN-3-matching-possession-ref-accepted",
              v_bind_ok["disposition"] == "accepted",
              f"verdict={v_bind_ok}", failures)
        bind_row = v_bind_ok.get("row_id")

        # ---- GREEN 3 (revocation leg): retraction needs NO possession ref at all ----
        v_revoke_ok = bw_call(world_red, "ledger_write", {
            "kind": "principal_key_bound", "actor": author, "supersedes": bind_row,
            "statement": "keyholder's FP1 binding revoked (GPG revocation certificate, item 3)",
            "principal_subject": keyholder, "principal_key_fingerprint": FP1,
            "principal_binding_active": "false"})
        check("GREEN-3-revocation-needs-no-possession-ref",
              v_revoke_ok["disposition"] == "accepted",
              f"verdict={v_revoke_ok}", failures)

        # ---- GREEN-zero-friction: an ORDINARY write's verdict shape, byte-compared pre/post-s61
        print(f"== scaffolding classic world {world_pre} (chain ends {CHAIN_S60[-1]}, NO s61) ==")
        wp = scaffold_classic(world_pre, CHAIN_S60)
        tmps.append(wp.parent)
        author_pre = birth_via_boundary(world_pre)
        v_pre = bw_call(world_pre, "ledger_write", {
            "kind": "decision", "statement": "an ordinary decision row, pre-s61",
            "actor": author_pre})
        v_post = bw_call(world_red, "ledger_write", {
            "kind": "decision", "statement": "an ordinary decision row, post-s61",
            "actor": author})
        check("GREEN-zero-friction-ordinary-act-verdict-shape",
              (v_pre["disposition"], v_pre["sqlstate"], v_pre["message"])
              == (v_post["disposition"], v_post["sqlstate"], v_post["message"]) == ("accepted", None, None),
              f"pre={v_pre}, post={v_post}", failures)

    finally:
        for w in (world_red, world_pre):
            teardown(w)
        for t in tmps:
            sh(["rm", "-rf", str(t)])

    print(f"\n{'KERNEL-LEVEL: ALL GREEN' if not failures else 'KERNEL-LEVEL FAILURES: ' + ', '.join(failures)}")

    # fixture_census (gates/fixture_census.py) registers ONE fixture PER seen-red DIRECTORY --
    # rather than a second registry entry pointing at a sibling file in this SAME directory (the
    # gate's own key-equals-dirname model, verified live before choosing this shape), this file's
    # own main() ALSO runs the verb-side/served-CLI/real-gpg complement
    # (run_fixtures_cli.py, this same directory -- see ITS module docstring for its own ten
    # cases) and folds its result into this ONE entry point's exit code. Both halves' output is
    # printed in full (never summarized away) so a reader sees exactly which leg, if either,
    # went red.
    print("\n" + "=" * 60)
    print("RUNNING THE VERB-SIDE/SERVED-CLI/REAL-GPG COMPLEMENT (run_fixtures_cli.py)")
    print("=" * 60 + "\n")
    cli_spec = importlib.util.spec_from_file_location(
        "s61_run_fixtures_cli", Path(__file__).resolve().parent / "run_fixtures_cli.py")
    assert cli_spec is not None and cli_spec.loader is not None
    cli_mod = importlib.util.module_from_spec(cli_spec)
    cli_spec.loader.exec_module(cli_mod)
    cli_rc = cli_mod.main()
    print(f"\n{'CLI-LEVEL: ALL GREEN' if cli_rc == 0 else 'CLI-LEVEL: FAILURES (see above)'}")

    overall = 0 if (not failures and cli_rc == 0) else 1
    print(f"\n{'OVERALL: ALL GREEN' if overall == 0 else 'OVERALL: FAILURES PRESENT'}")
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
