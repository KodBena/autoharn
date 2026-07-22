#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s41-principal-bindings-and-
relations.sql (design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md §6 witness plan as amended by
C6 -- the s41 slice; the s40 slice lives in seen-red/s40-principal-identity-events/). Real
infra, no mocks: CLASSIC scaffolds + manual chain applies in the TOY db, one REAL --new-world
run against the s41-wired scaffold, torn down before AND after. Red first, per refusal.

WORLDS:
  WORLD A  -- chain ends at s40: the detect f-polarity + the s41-verb teach-refusal.
  WORLD B  -- chain ends at s41: every s41 red/green polarity.
  WORLD NW -- a REAL `new-project.sh --new-world` run (chain now s15..s41): full birth
              end-to-end, detect t on the born world, first ordinary write OK.

Cases (each names the witness that would show it false -- see the check() lines):
  detect polarity (t/f); s40-only teach; relate/unrelate assert-retract lifecycle (view drops,
  raw history keeps); self-edge refused for ALL FOUR relation values (CLI) + once raw at the
  kernel trigger; same-natural-person canonicalization (CLI stores lower-id subject; the other
  ordering refused as duplicate; a raw non-canonical INSERT refused by the kernel CHECK);
  key bind human-only (model refused / human passes / malformed fingerprint refused at the
  kernel shape CHECK); D-6 (managerial by stamp-distinct MODEL refused; technical by model
  passes; managerial by HUMAN passes); acts_for retirement; competence lifecycle (grant with
  all fields -> in view; empty value field refused; inactive-from-birth refused raw; withdraw
  -> leaves view, stays raw; stray --band on withdrawal refused; duplicate active grant
  refused; --supersedes re-band replaces; stale/mismatched supersession targets refused, also
  for release-role/revoke-key); C6(iii) an s41 column reads back through ledger_current (plus
  view-definition inspection -- the pre-C3 stale-view state cannot be reproduced on a chain
  that carries C3's re-issue, so the inspection is the named witness form C6 itself licenses);
  gates green; ./judge AGREE both layers with all EIGHT principal kinds live; the s41-wired
  --new-world birth; the Idris freshness gate green (the parity pass's own net).

Usage: python3 seen-red/s41-principal-bindings-and-relations/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import hashlib
import hmac as hmac_mod
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LINEAGE = REPO / "kernel" / "lineage"
ENGINE = REPO / "engine"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(REPO / "filing"))

import ledger_differential  # noqa: E402
import ledger_edb  # noqa: E402
import pghost_resolve  # noqa: E402

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_COMMON = [
    "s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
    "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql", "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql", "s31-supersession-uniform-retraction.sql",
    "s32-edge-views-single-home.sql", "s33-composite-discharge.sql",
    "s34-computed-grade-refusal.sql", "s35-validation-decomposition.sql",
    "s36-decision-grade.sql", "s37-violation-disposition.sql",
    "s38-bookkeeping-close.sql", "s39-blocks-start.sql",
    "s40-principal-identity-events.sql",
]
CHAIN_A = CHAIN_COMMON
CHAIN_B = CHAIN_COMMON + ["s41-principal-bindings-and-relations.sql"]

FP = "ABCDEF0123456789ABCDEF0123456789ABCDEF01"  # a well-shaped OpenPGP v4 fingerprint


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
        f"DROP SCHEMA IF EXISTS {world} CASCADE; DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "  # declared-drop: scratch reset
        f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def led(world_dir: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    e = dict(os.environ)
    if env:
        e.update(env)
    return sh(["bash", str(world_dir / "led"), *args], cwd=str(world_dir), env=e)


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def psql_raw(script: str) -> subprocess.CompletedProcess[str]:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"],
              input=script)


def detect(schema: str, kern: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tA",
             "-v", f"schema={schema}", "-v", f"kern={kern}",
             "-f", str(LINEAGE / "s41-principal-bindings-and-relations.detect.sql")])
    return cp.stdout.strip()


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


def birth_acts(world: str) -> None:
    """The s40 birth acts, hand-driven (the scaffold's scripted form is witnessed on WORLD NW)."""
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    r = psql_raw(
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_purpose)\n"
        f"VALUES ('principal_registered', 'author registered (fixture genesis exception)',\n"
        f"        (SELECT id FROM principal WHERE name='author'),\n"
        f"        (SELECT id FROM principal WHERE name='author'), 'fixture connection principal');\n"
        f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_db_role)\n"
        f"VALUES ('principal_standing_declared', 'role {R} -> author',\n"
        f"        (SELECT id FROM principal WHERE name='author'),\n"
        f"        (SELECT id FROM principal WHERE name='author'), '{R}');\n")
    if r.returncode != 0:
        raise RuntimeError(f"birth acts failed ({world}): {r.stderr[-600:]}")


def stamped_review(world: str, agent: str, reviewer: str, independence: str,
                   target_id: str, label: str) -> subprocess.CompletedProcess[str]:
    """A review through a VERIFIED interception stamp under a distinct agent id (the s17/s21
    machinery driven for real: HMAC computed against the world's own provisioned secret)."""
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    secret = bytes.fromhex(psql_tuples(f"SELECT encode(secret,'hex') FROM {K}.stamp_secret;"))
    ts = int(time.time())
    mac = hmac_mod.new(secret, f"sessFX|{agent}|{ts}".encode(), hashlib.sha256).hexdigest()
    return psql_raw(
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"SELECT set_config('app.vendor_session','sessFX',false),"
        f" set_config('app.vendor_agent','{agent}',false),"
        f" set_config('app.vendor_ts','{ts}',false),"
        f" set_config('app.vendor_hmac','{mac}',false) \\gset _\n"
        f"BEGIN;\n"
        f"INSERT INTO ledger (kind,statement,regards,actor) VALUES ('review','{label}',{target_id},"
        f"(SELECT id FROM principal WHERE name='{reviewer}')) RETURNING id \\gset r_\n"
        f"INSERT INTO review_detail (ledger_id,verdict,independence,basis) VALUES "
        f"(:r_id,'attest','{independence}','basis text for {label}');\n"
        f"COMMIT;\n")


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    world_a, world_b, world_nw = "s41fxa", "s41fxb", "s41fxnw"
    for w in (world_a, world_b, world_nw):
        teardown(w)
    try:
        # ===================== WORLD A (s40 head) =====================
        print(f"== scaffolding classic world {world_a} (chain ends {CHAIN_A[-1]}) ==")
        wa = scaffold_classic(world_a, CHAIN_A)
        tmps.append(wa.parent)
        birth_acts(world_a)
        check("detect-f-on-s40", detect(world_a, f"{world_a}_kernel") == "f",
              f"s41 detect on an s40-head chain reads {detect(world_a, f'{world_a}_kernel')!r} (expect f)",
              failures)
        rteach = led(wa, "principal", "bind-role", "author", "--role", "scout")
        outt = rteach.stdout + rteach.stderr
        check("s40-only-kernel-teach",
              rteach.returncode != 0 and "carries s40 but not s41" in outt,
              f"exit={rteach.returncode}; excerpt={outt.strip()[-160:]!r}", failures)

        # ===================== WORLD B (s41 head) =====================
        print(f"== scaffolding classic world {world_b} (chain ends {CHAIN_B[-1]}) ==")
        wb = scaffold_classic(world_b, CHAIN_B)
        tmps.append(wb.parent)
        S, K, R = world_b, f"{world_b}_kernel", f"{world_b}_rw"
        birth_acts(world_b)
        check("detect-t-on-s41", detect(S, K) == "t",
              f"s41 detect on the s41 chain reads {detect(S, K)!r} (expect t)", failures)

        # registered fixtures: hume (human, LOWER id) then botty (model, higher id)
        for nm, cls in (("hume", "human"), ("botty", "model")):
            r = led(wb, "register-principal", nm, cls, "--purpose", f"{cls} fixture",
                    env={"LED_ACTOR": "author"})
            if r.returncode != 0:
                raise RuntimeError(f"register {nm} failed: {r.stdout[-400:]} {r.stderr[-400:]}")

        # relate / unrelate lifecycle
        rr = led(wb, "principal", "relate", "botty", "acts-for", "author",
                 env={"LED_ACTOR": "author"})
        rel_row = psql_tuples(f"SELECT row_id FROM {S}.principal_relations WHERE relation='acts-for';")
        ru = led(wb, "principal", "unrelate", "botty", "acts-for", "author",
                 "--supersedes", rel_row, env={"LED_ACTOR": "author"})
        in_view = psql_tuples(f"SELECT count(*) FROM {S}.principal_relations WHERE relation='acts-for';")
        raw_rows = psql_tuples(f"SELECT count(*) FROM {S}.ledger WHERE kind='principal_relation_asserted' AND principal_relation='acts-for';")
        check("relate-then-unrelate",
              rr.returncode == 0 and ru.returncode == 0 and in_view == "0" and raw_rows == "2",
              f"assert exit={rr.returncode}, retract exit={ru.returncode}; view now holds "
              f"{in_view} acts-for rows (expect 0), raw history holds {raw_rows} (expect 2 -- "
              f"assertion + terminal retraction, never thinner)", failures)

        # self-edges: all four relation values via the CLI, one raw at the kernel trigger
        selfs_ok = True
        for rel in ("acts-for", "dispatched-by", "same-natural-person", "succeeds"):
            rs = led(wb, "principal", "relate", "botty", rel, "botty", env={"LED_ACTOR": "author"})
            selfs_ok = selfs_ok and rs.returncode != 0 and "itself" in (rs.stdout + rs.stderr)
        rk = psql_raw(f"SET ROLE {R};\nSET search_path={S},{K};\n"
                      f"INSERT INTO ledger (kind,statement,actor,principal_subject,principal_object,"
                      f"principal_relation,principal_binding_active) VALUES "
                      f"('principal_relation_asserted','raw self',"
                      f"(SELECT id FROM principal WHERE name='author'),"
                      f"(SELECT id FROM principal WHERE name='botty'),"
                      f"(SELECT id FROM principal WHERE name='botty'),'succeeds',true);\n")
        check("self-edges-refused",
              selfs_ok and rk.returncode != 0 and "cannot stand in relation" in (rk.stdout + rk.stderr),
              f"all four CLI self-edges refused={selfs_ok}; raw kernel-trigger self-edge "
              f"exit={rk.returncode} with the taught text", failures)

        # same-natural-person canonicalization (hume has the LOWER id)
        rc = led(wb, "principal", "relate", "botty", "same-natural-person", "hume",
                 env={"LED_ACTOR": "author"})
        stored = psql_tuples(
            f"SELECT ps.name || '>' || po.name FROM {S}.principal_relations pr "
            f"JOIN {K}.principal ps ON ps.id = pr.subject JOIN {K}.principal po ON po.id = pr.object "
            f"WHERE pr.relation = 'same-natural-person';")
        rdup = led(wb, "principal", "relate", "hume", "same-natural-person", "botty",
                   env={"LED_ACTOR": "author"})
        outdup = rdup.stdout + rdup.stderr
        rnc = psql_raw(f"SET ROLE {R};\nSET search_path={S},{K};\n"
                       f"INSERT INTO ledger (kind,statement,actor,principal_subject,principal_object,"
                       f"principal_relation,principal_binding_active) VALUES "
                       f"('principal_relation_asserted','raw non-canonical',"
                       f"(SELECT id FROM principal WHERE name='author'),"
                       f"(SELECT id FROM principal WHERE name='botty'),"
                       f"(SELECT id FROM principal WHERE name='hume'),'same-natural-person',true);\n")
        check("snp-canonicalization",
              rc.returncode == 0 and "canonicalizing" in (rc.stdout + rc.stderr)
              and stored == "hume>botty"
              and rdup.returncode != 0 and "already exists" in outdup
              and rnc.returncode != 0 and "principal_snp_canonical_order" in (rnc.stdout + rnc.stderr),
              f"CLI stored {stored!r} (expect hume>botty, reversed from the typed order, notice "
              f"printed); the OTHER ordering refused as duplicate ({rdup.returncode}); a raw "
              f"non-canonical INSERT refused by the kernel CHECK ({rnc.returncode})", failures)

        # key bindings: model refused / human passes / malformed shape refused (kernel CHECK)
        rkm = led(wb, "principal", "bind-key", "botty", "--fingerprint", FP,
                  env={"LED_ACTOR": "author"})
        rkh = led(wb, "principal", "bind-key", "hume", "--fingerprint", FP,
                  env={"LED_ACTOR": "author"})
        keys_view = psql_tuples(f"SELECT count(*) FROM {S}.principal_keys;")
        rkbad = led(wb, "principal", "bind-key", "hume", "--fingerprint", "abc123",
                    env={"LED_ACTOR": "author"})
        check("key-binding-polarity",
              rkm.returncode != 0 and "HUMAN subject" in (rkm.stdout + rkm.stderr)
              and rkh.returncode == 0 and keys_view == "1"
              and rkbad.returncode != 0 and "principal_key_fingerprint_shape" in (rkbad.stdout + rkbad.stderr),
              f"model bind exit={rkm.returncode} (taught); human bind exit={rkh.returncode}, "
              f"view rows={keys_view}; malformed fingerprint exit={rkbad.returncode} "
              f"(kernel shape CHECK named)", failures)

        # D-6: managerial by stamp-distinct model refused / technical passes / human passes.
        # The TARGET row must itself carry a verified stamp: the s21 distinctness pair is
        # fail-safe (a NULL half on either row is never distinct), so an unstamped target would
        # refuse EVERY independence claim before D-6 is even reached.
        secret = bytes.fromhex(psql_tuples(f"SELECT encode(secret,'hex') FROM {K}.stamp_secret;"))
        ts0 = int(time.time())
        mac0 = hmac_mod.new(secret, f"sessFX|agent0|{ts0}".encode(), hashlib.sha256).hexdigest()
        psql_raw(f"SET ROLE {R};\nSET search_path={S},{K};\n"
                 f"SELECT set_config('app.vendor_session','sessFX',false),"
                 f" set_config('app.vendor_agent','agent0',false),"
                 f" set_config('app.vendor_ts','{ts0}',false),"
                 f" set_config('app.vendor_hmac','{mac0}',false) \\gset _\n"
                 f"INSERT INTO ledger (kind,statement,actor) VALUES ('decision','d6 target',"
                 f"(SELECT id FROM principal WHERE name='author'));\n")
        tgt = psql_tuples(f"SELECT id FROM {S}.ledger WHERE statement='d6 target';")
        rm = stamped_review(world_b, "agentM", "botty", "managerial", tgt, "m-claim")
        rt = stamped_review(world_b, "agentT", "botty", "technical", tgt, "t-claim")
        rh = stamped_review(world_b, "agentH", "hume", "managerial", tgt, "h-claim")
        outm = rm.stdout + rm.stderr
        check("d6-human-attested-scoping",
              rm.returncode != 0 and "no schema can witness" in outm
              and rt.returncode == 0 and rh.returncode == 0,
              f"managerial-by-model exit={rm.returncode} (taught: 'no schema can witness'); "
              f"technical-by-model exit={rt.returncode}; managerial-by-human exit={rh.returncode}",
              failures)

        # acts_for retirement (D-7): a registration supplying acts_for is refused by CHECK
        raf = psql_raw(f"SET ROLE {R};\nSET search_path={S},{K};\n"
                       f"WITH new_p AS (INSERT INTO principal (name, agent_class, acts_for) "
                       f"VALUES ('af','model',1) RETURNING id) "
                       f"INSERT INTO ledger (kind,statement,actor,principal_subject,principal_purpose) "
                       f"SELECT 'principal_registered','af',"
                       f"(SELECT id FROM principal WHERE name='author'),id,'p' FROM new_p;\n")
        check("acts-for-retired",
              raf.returncode != 0 and "principal_acts_for_retired" in (raf.stdout + raf.stderr),
              f"exit={raf.returncode}; the retirement CHECK named", failures)

        # competence lifecycle
        g1 = led(wb, "principal", "grant-competence", "botty", "--activity", "sql-review",
                 "--band", "B", "--basis", "track record", env={"LED_ACTOR": "author"})
        in_comp = psql_tuples(f"SELECT activity || '|' || band FROM {S}.principal_competences;")
        gdup = led(wb, "principal", "grant-competence", "botty", "--activity", "sql-review",
                   "--band", "A", "--basis", "x", env={"LED_ACTOR": "author"})
        gempty = led(wb, "principal", "grant-competence", "botty", "--activity", "other",
                     "--band", "", "--basis", "x", env={"LED_ACTOR": "author"})
        grow = psql_tuples(f"SELECT row_id FROM {S}.principal_competences WHERE activity='sql-review';")
        greband = led(wb, "principal", "grant-competence", "botty", "--activity", "sql-review",
                      "--band", "A", "--basis", "re-derivation", "--supersedes", grow,
                      env={"LED_ACTOR": "author"})
        reband = psql_tuples(f"SELECT band FROM {S}.principal_competences WHERE activity='sql-review';")
        grow2 = psql_tuples(f"SELECT row_id FROM {S}.principal_competences WHERE activity='sql-review';")
        wstray = led(wb, "principal", "withdraw-competence", "botty", "--activity", "sql-review",
                     "--band", "A", "--supersedes", grow2, env={"LED_ACTOR": "author"})
        wstale = led(wb, "principal", "withdraw-competence", "botty", "--activity", "sql-review",
                     "--supersedes", grow, env={"LED_ACTOR": "author"})  # the SUPERSEDED old id
        w1 = led(wb, "principal", "withdraw-competence", "botty", "--activity", "sql-review",
                 "--supersedes", grow2, env={"LED_ACTOR": "author"})
        comp_after = psql_tuples(f"SELECT count(*) FROM {S}.principal_competences WHERE activity='sql-review';")
        comp_raw = psql_tuples(f"SELECT count(*) FROM {S}.ledger WHERE kind='principal_competence_granted' AND principal_competence_activity='sql-review';")
        rinactive = psql_raw(f"SET ROLE {R};\nSET search_path={S},{K};\n"
                             f"INSERT INTO ledger (kind,statement,actor,principal_subject,"
                             f"principal_competence_activity,principal_binding_active) VALUES "
                             f"('principal_competence_granted','raw inactive-from-birth',"
                             f"(SELECT id FROM principal WHERE name='author'),"
                             f"(SELECT id FROM principal WHERE name='botty'),'raw-act',false);\n")
        check("competence-lifecycle",
              g1.returncode == 0 and in_comp == "sql-review|B"
              and gdup.returncode != 0 and "already exists" in (gdup.stdout + gdup.stderr)
              and gempty.returncode != 0
              and greband.returncode == 0 and reband == "A"
              and wstray.returncode != 0 and "forbidden on a withdrawal" in (wstray.stdout + wstray.stderr)
              and wstale.returncode != 0 and "not the active grant" in (wstale.stdout + wstale.stderr)
              and w1.returncode == 0 and comp_after == "0" and comp_raw == "3"
              and rinactive.returncode != 0
              and "principal_binding_inactive_needs_supersedes" in (rinactive.stdout + rinactive.stderr),
              f"grant OK (view: {in_comp!r}); duplicate refused; empty band refused "
              f"({gempty.returncode}); re-band via --supersedes replaced (band now {reband!r}); "
              f"stray --band on withdrawal refused; STALE supersession target refused; withdrawal "
              f"OK (view {comp_after} rows, raw {comp_raw} rows -- grant+re-band+terminal "
              f"withdrawal); raw inactive-from-birth refused by the kernel CHECK", failures)

        # release-role / revoke-key value-continuity refusals + green paths
        b1 = led(wb, "principal", "bind-role", "botty", "--role", "scout", env={"LED_ACTOR": "author"})
        brow = psql_tuples(f"SELECT row_id FROM {S}.principal_role_bindings WHERE role_name='scout';")
        rmis = led(wb, "principal", "release-role", "botty", "--role", "wrong-name",
                   "--supersedes", brow, env={"LED_ACTOR": "author"})
        rrel = led(wb, "principal", "release-role", "botty", "--role", "scout",
                   "--supersedes", brow, env={"LED_ACTOR": "author"})
        ragain = led(wb, "principal", "release-role", "botty", "--role", "scout",
                     "--supersedes", brow, env={"LED_ACTOR": "author"})  # already-inactive target
        krow = psql_tuples(f"SELECT row_id FROM {S}.principal_keys;")
        kmis = led(wb, "principal", "revoke-key", "hume", "--fingerprint", "0" * 40,
                   "--supersedes", krow, env={"LED_ACTOR": "author"})
        krev = led(wb, "principal", "revoke-key", "hume", "--fingerprint", FP,
                   "--supersedes", krow, env={"LED_ACTOR": "author"})
        check("release-revoke-value-continuity",
              b1.returncode == 0
              and rmis.returncode != 0 and "not the active" in (rmis.stdout + rmis.stderr)
              and rrel.returncode == 0
              and ragain.returncode != 0
              and kmis.returncode != 0 and krev.returncode == 0
              and psql_tuples(f"SELECT count(*) FROM {S}.principal_role_bindings;") == "0"
              and psql_tuples(f"SELECT count(*) FROM {S}.principal_keys;") == "0",
              f"bind-role OK; mismatched role name refused ({rmis.returncode}); release OK; "
              f"release against the already-released id refused ({ragain.returncode}); "
              f"mismatched fingerprint refused ({kmis.returncode}); revoke-key OK; both views "
              f"empty, raw history retained", failures)

        # C6(iii): an s41 column reads back through ledger_current + view-definition inspection
        col_read = psql_tuples(
            f"SELECT principal_relation FROM {S}.ledger_current "
            f"WHERE kind='principal_relation_asserted' AND principal_relation='same-natural-person' "
            f"AND principal_binding_active LIMIT 1;")
        viewdef = psql_tuples(f"SELECT pg_get_viewdef('{S}.ledger_current'::regclass) LIKE '%principal_binding_active%';")
        check("c6iii-projection-carries-s41-columns",
              col_read == "same-natural-person" and viewdef == "t",
              f"ledger_current returns {col_read!r} for the fixture row; view definition "
              f"carries the s41 columns ({viewdef}) -- the C3 net (a pre-C3 stale-view red "
              f"cannot be built on a chain whose s41 file carries the re-issue; the definition "
              f"inspection is the C6-licensed witness form)", failures)

        # gates green (their standing CHAINs now end at s41)
        g1g = sh([sys.executable, str(REPO / "gates" / "ledger_reader_allowlist.py")])
        g2g = sh([sys.executable, str(REPO / "gates" / "kind_shape_manifest_gate.py")])
        check("gates-green", g1g.returncode == 0 and g2g.returncode == 0,
              f"ledger_reader_allowlist exit={g1g.returncode}; kind_shape_manifest_gate "
              f"exit={g2g.returncode}", failures)

        # ./judge differential, both layers, with all EIGHT principal kinds live
        led(wb, "work", "open", "s41fx-item", "differential fixture item")
        # ensure the four s40 kinds are also present on THIS world (suspend/revoke a throwaway)
        led(wb, "register-principal", "byebye", "model", "--purpose", "standing fixture",
            env={"LED_ACTOR": "author"})
        led(wb, "principal", "suspend", "byebye", env={"LED_ACTOR": "author"})
        led(wb, "principal", "revoke", "byebye", env={"LED_ACTOR": "author"})
        kinds = psql_tuples(f"SELECT count(DISTINCT kind) FROM {S}.ledger WHERE kind LIKE 'principal_%';")
        os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = PGDB, S, K
        try:
            edb_text = ledger_edb.export(S).edb_text()
            res_tnow = ledger_differential.run_differential(S, edb_text=edb_text)
            res_work = ledger_differential.run_layer_differential(S, "work")
        finally:
            del os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"]
        v_tnow, v_work = res_tnow.verdict(), res_work.verdict()
        check("differential-agree-both-layers",
              v_tnow == "AGREE" and v_work == "AGREE" and kinds == "8",
              f"tnow={v_tnow} work={v_work} with {kinds} distinct principal_* kinds live "
              f"(expect AGREE/AGREE/8)", failures)

        # ===================== WORLD NW (the s41-wired --new-world) =====================
        print(f"== REAL --new-world scaffold run ({world_nw}, chain s15..s41) ==")
        tmpnw = Path(tempfile.mkdtemp(prefix=f"{world_nw}-seenred-"))
        tmps.append(tmpnw)
        nwdir = tmpnw / world_nw
        rnw = sh(["bash", str(NEW_PROJECT), str(nwdir), "--new-world", world_nw,
                  "--db", PGDB, "--host", PGHOST])
        det_nw = detect(world_nw, f"{world_nw}_kernel") if rnw.returncode == 0 else "?"
        rfirst = led(nwdir, "decision", "first write in an s41 world") if rnw.returncode == 0 else None
        check("new-world-s41-birth",
              rnw.returncode == 0 and det_nw == "t"
              and rfirst is not None and rfirst.returncode == 0,
              f"scaffold exit={rnw.returncode}; s41 detect on the born world reads {det_nw!r}; "
              f"first ordinary write exit={(rfirst.returncode if rfirst else '?')}", failures)

        # the Idris parity pass's own net
        gid = sh([sys.executable, str(REPO / "gates" / "idris_model_freshness.py")])
        check("idris-freshness-green", gid.returncode == 0,
              f"gates/idris_model_freshness.py exit={gid.returncode} (AS-OF s41 vs mechanical "
              f"head s41, elaboration clean -- the standing WARN cleared by the parity pass)",
              failures)

    finally:
        for w in (world_a, world_b, world_nw):
            teardown(w)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s41 principal-bindings-and-relations both-polarity proof, zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
