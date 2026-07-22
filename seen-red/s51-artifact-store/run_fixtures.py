#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for kernel/lineage/s51-artifact-store.sql
(design/FABLE-ARTIFACT-STORE-SPEC.md, maintainer decision-queue ratification 2026-07-18). Real
infra, no mocks: scratch schema pairs in the toy db, torn down before and after. Never touches
kernel/, bootstrap/ (beyond reading the templates as fixtures), or any live world.

WITNESSES (spec's own WA1..WA8 enumeration):
  WA1  put -> hash printed; get -> bytes byte-identical (round-trip); stat sane. Exercised BOTH
       at the kernel.artifact_write function level AND through the real CLI
       (bootstrap/templates/legacy-led.tmpl, as an actual subprocess -- the boundary-cli-rebase
       precedent's own `run_cli` pattern).
  WA2  idempotent re-put of identical bytes -> same hash, no second row, verdict says
       already-present.
  WA3  size cap: a >1 MiB input -> artifact_too_large typed refusal, journaled digest-only,
       nothing stored.
  WA4  unknown media type -> typed refusal naming the closed vocabulary.
  WA5  asserted-hash mismatch -> refusal (the server's own computation governs).
  WA6  corruption drill (scratch only, as owner, simulating substrate fault): tamper a stored
       row's bytes directly (via session_replication_role='replica' to bypass the append-only
       trigger, AS THE OWNER); `led artifact get` (the real CLI) refuses loudly on hash mismatch.
  WA7  custody: pg_dump of the scratch pair, restore to a second scratch pair, `get` returns
       byte-identical content -- the backup-covers-referents claim witnessed, not asserted.
  WA8  charter integration: register a charter whose bytes are ALSO in the store;
       tools/role_charter.py `show` resolves the referent (via `led`, unaffected by this delta)
       and reports drift against the working file exactly as before -- proving the store's
       presence changes nothing about role_charter.py's own existing, unmodified contract.

NOT WITNESSED HERE, NAMED (not silently omitted): `./judge` differential AGREE is NOT exercised
against this delta -- kernel.artifact is a wholly new table with no ASP/SQL predicate producer on
either side of the differential (engine/lp/*.lp and engine/ledger_floor.py both operate over
ledger-derived predicates; this delta adds no ledger kind, no ledger column, and no engine-visible
predicate). UNEXERCISED-with-reason, per the standing claims discipline -- not claimed AGREE
vacuously.

Usage: python3 seen-red/s51-artifact-store/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LINEAGE = REPO / "kernel" / "lineage"
LEGACY_LED_TMPL = REPO / "bootstrap" / "templates" / "legacy-led.tmpl"
sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "serving"))
from pghost_resolve import resolve_pghost  # noqa: E402
import deployment_record  # noqa: E402

PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S50 = [
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
    "s45-standing-lifecycle.sql", "s44-model-identity-attestation.sql",
    "s46-credited-views.sql", "s47-claim-on-closed-refusal.sql",
    "s48-review-witness-existence.sql", "s49-journaler-overflow-guard.sql",
    "s50-defeat-input-raw-domain.sql",
]
S51_FILE = "s51-artifact-store.sql"
S51_DETECT = "s51-artifact-store.detect.sql"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown(world: str) -> None:
    # THREE SEPARATE psql -c invocations, deliberately (a hazard found and fixed here, not
    # inherited silently from the s50/s49-fixture precedent this function's shape otherwise
    # mirrors): a single `-c "stmt1; stmt2; stmt3"` string runs as ONE implicit transaction over
    # the whole simple-Query message -- if a LATER statement in that string errors (e.g.
    # `DROP OWNED BY <role>` when <role> does not exist, exactly WA7's own second-pair-name
    # case, whose role is only created AFTER this teardown call on its first invocation), the
    # error aborts the WHOLE batch and ROLLS BACK the EARLIER statements too (`DROP SCHEMA`
    # included) -- witnessed live: a stale schema from an earlier crashed run survived repeated
    # "successful-looking" teardown() calls because DROP OWNED BY kept failing and silently
    # undoing the DROP SCHEMA that ran just before it in the same batch. Each statement in its
    # own invocation means a failure in one never rolls back another.
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP SCHEMA IF EXISTS {world} CASCADE;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP SCHEMA IF EXISTS {world}_kernel CASCADE;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def apply_chain(world: str, chain: list[str]) -> None:
    teardown(world)
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"CREATE ROLE {world}_rw LOGIN PASSWORD 'x';"])
    if cp.returncode != 0:
        raise RuntimeError(f"role create failed: {cp.stderr}")
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={world}", "-v", f"kern={world}_kernel", "-v", f"role={world}_rw"]
    for f in chain:
        args += ["-f", str(LINEAGE / f)]
    cp = sh(args)
    if cp.returncode != 0:
        raise RuntimeError(f"chain apply failed for {world}: {cp.stdout[-2000:]} {cp.stderr[-2000:]}")


def apply_s51(world: str) -> None:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
             "-v", f"schema={world}", "-v", f"kern={world}_kernel", "-v", f"role={world}_rw",
             "-f", str(LINEAGE / S51_FILE)])
    if cp.returncode != 0:
        raise RuntimeError(f"s51 apply failed for {world}: {cp.stdout[-2000:]} {cp.stderr[-2000:]}")


def detect(world: str, sibling: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1",
             "-v", f"schema={world}", "-v", f"kern={world}_kernel", "-f", str(LINEAGE / sibling)])
    if cp.returncode != 0:
        raise RuntimeError(f"detect failed: {cp.stderr}")
    return cp.stdout.strip()


def sql1(world: str, sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"sql1 failed: {sql}\n{cp.stderr}")
    return cp.stdout.strip()


def kernel_write(world: str, fn: str, payload: dict) -> dict:
    """Small-payload path: the JSON payload crosses as ONE `psql -v` execve argument -- fine for
    every payload here except WA3's own >1 MiB oversize probe, which needs kernel_write_large."""
    pj = json.dumps(payload)
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-v", f"payload={pj}"],
            input=f"SET ROLE {world}_rw;\nSET search_path = {world}, {world}_kernel;\n"
                  f"SELECT to_jsonb(v) FROM {world}_kernel.{fn}(:'payload'::jsonb) v;\n")
    if cp.returncode != 0:
        raise RuntimeError(f"kernel_write plumbing failed: {cp.stderr}")
    return json.loads(cp.stdout.strip())


def kernel_write_large(world: str, fn: str, payload: dict, tmpdir: str) -> dict:
    """kernel_write()'s sibling for a payload too large to cross as one execve argument -- the
    SAME transport shape bootstrap/templates/legacy-led.tmpl's own kernel_write_from_file()
    uses: the payload is written to a file, and psql's own `\\set var \\`cat '<file>'\\`` backtick
    -command value carrier loads it (a pipe read, never an execve argument -- WA3's own
    1048577-byte payload base64s to ~1.4 MiB, comfortably past MAX_ARG_STRLEN)."""
    pj = json.dumps(payload)
    payload_path = Path(tmpdir) / "kernel_write_large_payload.json"
    payload_path.write_text(pj, encoding="utf-8")
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1"],
            input=f"\\set payload `cat '{payload_path}'`\n"
                  f"SET ROLE {world}_rw;\nSET search_path = {world}, {world}_kernel;\n"
                  f"SELECT to_jsonb(v) FROM {world}_kernel.{fn}(:'payload'::jsonb) v;\n")
    if cp.returncode != 0:
        raise RuntimeError(f"kernel_write_large plumbing failed: {cp.stderr}")
    return json.loads(cp.stdout.strip())


def birth(world: str) -> str:
    """Genesis + stamp secret + author + write-boundary tool principal + standing declaration --
    the same shape s43/s50's own fixtures use, minimal to what an artifact_write call needs
    (a resolvable session_user standing default, and the write-boundary principal s43's
    journaler requires for ANY refusal path)."""
    seq = f"""
BEGIN;
INSERT INTO {world}_kernel.chain_genesis (seed)
  VALUES (encode(gen_random_bytes(32),'hex')) ON CONFLICT (only_one) DO NOTHING;
INSERT INTO {world}_kernel.stamp_secret (secret) VALUES (gen_random_bytes(32));
INSERT INTO {world}_kernel.principal (name, agent_class)
  VALUES ('author-fixture', 'model') RETURNING id \\gset author_
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered',
          E'principal \\'author-fixture\\' registered (class model)',
          :author_id, :author_id, 'fixture author');
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_db_role, principal_binding_active)
  VALUES ('principal_standing_declared','standing (fixture)', :author_id, :author_id, '{world}_rw', true);
COMMIT;
BEGIN;
INSERT INTO {world}_kernel.principal (name, agent_class)
  VALUES ('write-boundary', 'tool') RETURNING id \\gset wb_
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','write-boundary (fixture)', :author_id, :wb_id, 'refusal journaler');
COMMIT;
"""
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1"], input=seq)
    if cp.returncode != 0:
        raise RuntimeError(f"birth sequence failed ({world}): {cp.stdout}\n{cp.stderr}")
    return sql1(world, f"SELECT id FROM {world}_kernel.principal WHERE name='author-fixture';")


def run_cli(args: list[str], deployment: Path, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Text-mode subprocess capture -- every fixture call site here uses `--out <path>` for
    `get` (bytes land on disk, never on stdout), so stdout/stderr are always safely decodable
    prose (hashes, teach-text, stat output)."""
    env = dict(os.environ)
    env["AUTOHARN"] = str(REPO)
    env["PICKUP_DEPLOYMENT"] = str(deployment)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(["bash", str(LEGACY_LED_TMPL), *args], capture_output=True, text=True,
                           env=env, timeout=60)


def write_legacy_deployment(path: Path, world: str) -> None:
    rec = deployment_record.DeploymentRecord(
        db=PGDB, host=PGHOST, schema=world, kern=f"{world}_kernel", role=f"{world}_rw",
        name=world)
    deployment_record.write_deployment(path, rec)


def main() -> int:
    failures: list[str] = []
    world = "s51fx"
    tmpdir = tempfile.mkdtemp(prefix="s51-artifact-store-")
    dep_path = Path(tmpdir) / f"{world}-legacy-deployment.json"
    try:
        print(f"== scaffolding WORLD (chain ends {CHAIN_S50[-1]}, s51 NOT yet applied) ==")
        apply_chain(world, CHAIN_S50)
        check("detect-negative-pre-s51", detect(world, S51_DETECT) == "f",
              "s51 .detect.sql reads f on the s50-headed (pre-s51) chain", failures)

        author_id = birth(world)
        write_legacy_deployment(dep_path, world)

        print("== applying s51 in place ==")
        apply_s51(world)
        check("detect-positive-post-s51", detect(world, S51_DETECT) == "t",
              "s51 .detect.sql reads t once s51 is applied on top of s50", failures)

        # ==================== WA1: put/get/stat, function level + real CLI ====================
        print("== WA1: put -> hash printed; get -> byte-identical; stat sane ==")
        content1 = b"# WA1 fixture\n\nplain markdown content for the artifact store.\n"
        expected_hash1 = hashlib.sha256(content1).hexdigest()
        payload1 = {"bytes": base64.b64encode(content1).decode("ascii"),
                    "media_type": "text/markdown", "actor": int(author_id)}
        v1 = kernel_write(world, "artifact_write", payload1)
        check("wa1-function-accepted", v1["disposition"] == "accepted", f"{v1}", failures)
        check("wa1-function-hash-in-message", expected_hash1 in (v1.get("message") or ""),
              f"message={v1.get('message')!r} expected hash {expected_hash1}", failures)
        stored_bytes = sql1(world,
            f"SET ROLE {world}_rw; SELECT encode(bytes,'base64') FROM {world}_kernel.artifact "
            f"WHERE hash = '{expected_hash1}';")
        check("wa1-function-bytes-byte-identical",
              base64.b64decode(stored_bytes) == content1,
              "stored bytes decode to the exact submitted content", failures)

        # WA1 via the real CLI: put a second, distinct file.
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, dir=tmpdir) as f:
            f.write(b"# WA1 CLI fixture\n\nregistered via the real `led artifact put` verb.\n")
            cli_path = f.name
        cli_content = Path(cli_path).read_bytes()
        expected_hash_cli = hashlib.sha256(cli_content).hexdigest()
        put_cp = run_cli(["artifact", "put", cli_path], dep_path, env_extra={"LED_ACTOR": "author-fixture"})
        check("wa1-cli-put-exit0", put_cp.returncode == 0,
              f"exit={put_cp.returncode} stdout={put_cp.stdout!r} stderr={put_cp.stderr!r}", failures)
        check("wa1-cli-put-prints-hash", expected_hash_cli in put_cp.stdout,
              f"stdout={put_cp.stdout!r} expected hash {expected_hash_cli}", failures)

        get_out = Path(tmpdir) / "wa1-get-out.md"
        get_cp = run_cli(["artifact", "get", expected_hash_cli, "--out", str(get_out)], dep_path)
        check("wa1-cli-get-exit0", get_cp.returncode == 0,
              f"exit={get_cp.returncode} stderr={get_cp.stderr!r}", failures)
        check("wa1-cli-get-byte-identical", get_out.exists() and get_out.read_bytes() == cli_content,
              f"round-tripped bytes match the original file", failures)

        stat_cp = run_cli(["artifact", "stat", expected_hash_cli], dep_path)
        check("wa1-cli-stat-exit0-and-sane",
              stat_cp.returncode == 0 and expected_hash_cli in stat_cp.stdout
              and "text/markdown" in stat_cp.stdout and str(len(cli_content)) in stat_cp.stdout,
              f"exit={stat_cp.returncode} stdout={stat_cp.stdout!r}", failures)

        # ==================== WA2: idempotent re-put ====================
        print("== WA2: idempotent re-put of identical bytes ==")
        count_before = sql1(world,
            f"SET ROLE {world}_rw; SELECT count(*) FROM {world}_kernel.artifact WHERE hash = "
            f"'{expected_hash1}';")
        v2 = kernel_write(world, "artifact_write", payload1)
        count_after = sql1(world,
            f"SET ROLE {world}_rw; SELECT count(*) FROM {world}_kernel.artifact WHERE hash = "
            f"'{expected_hash1}';")
        check("wa2-idempotent-accepted", v2["disposition"] == "accepted", f"{v2}", failures)
        check("wa2-idempotent-already-present-message",
              "already present" in (v2.get("message") or ""), f"message={v2.get('message')!r}", failures)
        check("wa2-idempotent-no-second-row", count_before == count_after == "1",
              f"count before={count_before} after={count_after} -- expected 1/1", failures)

        # ==================== WA3: size cap ====================
        print("== WA3: size cap -> artifact_too_large, journaled digest-only ==")
        oversize = b"x" * (1048576 + 1)
        refusal_count_before = sql1(world,
            f"SET ROLE {world}_rw; SELECT count(*) FROM {world}.ledger WHERE kind='write_refused' "
            f"AND refusal_surface='artifact';")
        v3 = kernel_write_large(world, "artifact_write", {
            "bytes": base64.b64encode(oversize).decode("ascii"), "media_type": "text/plain",
            "actor": int(author_id)}, tmpdir)
        refusal_count_after = sql1(world,
            f"SET ROLE {world}_rw; SELECT count(*) FROM {world}.ledger WHERE kind='write_refused' "
            f"AND refusal_surface='artifact';")
        check("wa3-refused", v3["disposition"] == "refused", f"{v3}", failures)
        check("wa3-message-names-too-large",
              "artifact_too_large" in (v3.get("message") or ""), f"message={v3.get('message')!r}", failures)
        check("wa3-journaled-once-more",
              int(refusal_count_after) == int(refusal_count_before) + 1,
              f"write_refused/artifact count before={refusal_count_before} after={refusal_count_after}",
              failures)
        oversize_hash = hashlib.sha256(oversize).hexdigest()
        nothing_stored = sql1(world,
            f"SET ROLE {world}_rw; SELECT count(*) FROM {world}_kernel.artifact WHERE hash = "
            f"'{oversize_hash}';")
        check("wa3-nothing-stored", nothing_stored == "0", f"count={nothing_stored}", failures)
        # digest-only: the refused row's own statement/message never contains the oversize
        # payload's raw content (bytes NEVER enter the refusal journal).
        refused_row = sql1(world,
            f"SET ROLE {world}_rw; SELECT refusal_message, refusal_payload_digest FROM "
            f"{world}.ledger WHERE kind='write_refused' AND refusal_surface='artifact' "
            f"ORDER BY id DESC LIMIT 1;")
        check("wa3-digest-only-no-raw-bytes-in-journal",
              "x" * 100 not in refused_row and len(refused_row.split("|")[-1]) == 64,
              f"journaled row (message|digest)={refused_row!r} -- must carry a 64-hex digest, "
              f"never the oversize content itself", failures)

        # ==================== WA4: unknown media type ====================
        print("== WA4: unknown media type -> typed refusal naming the closed vocabulary ==")
        v4 = kernel_write(world, "artifact_write", {
            "bytes": base64.b64encode(b"whatever").decode("ascii"), "media_type": "image/png",
            "actor": int(author_id)})
        check("wa4-refused", v4["disposition"] == "refused", f"{v4}", failures)
        check("wa4-names-vocabulary",
              all(t in (v4.get("message") or "") for t in
                  ("text/markdown", "text/plain", "application/toml", "application/json")),
              f"message={v4.get('message')!r}", failures)

        # ==================== WA5: asserted-hash mismatch ====================
        print("== WA5: asserted-hash mismatch -> refusal ==")
        v5 = kernel_write(world, "artifact_write", {
            "bytes": base64.b64encode(b"real content").decode("ascii"), "media_type": "text/plain",
            "hash": "0" * 64, "actor": int(author_id)})
        check("wa5-refused", v5["disposition"] == "refused", f"{v5}", failures)
        check("wa5-mismatch-message", "mismatch" in (v5.get("message") or "").lower(),
              f"message={v5.get('message')!r}", failures)

        # ==================== WA6: corruption drill (scratch, as owner) ====================
        print("== WA6: corruption drill -- owner tampers stored bytes; get refuses loudly ==")
        cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1"], input=f"""
SET session_replication_role = replica;
UPDATE {world}_kernel.artifact SET bytes = 'corrupted-by-wa6-drill'::bytea,
       size = octet_length('corrupted-by-wa6-drill'::bytea)
WHERE hash = '{expected_hash1}';
SET session_replication_role = DEFAULT;
""")
        check("wa6-owner-tamper-succeeded", cp.returncode == 0,
              f"owner UPDATE (via session_replication_role=replica, bypassing the append-only "
              f"trigger) exit={cp.returncode} stderr={cp.stderr}", failures)
        wa6_get = run_cli(["artifact", "get", expected_hash1], dep_path)
        check("wa6-cli-get-refuses", wa6_get.returncode != 0,
              f"exit={wa6_get.returncode} (expected nonzero)", failures)
        check("wa6-cli-get-names-corruption",
              "CORRUPT" in wa6_get.stderr or "corrupt" in wa6_get.stderr.lower(),
              f"stderr={wa6_get.stderr!r}", failures)
        check("wa6-cli-get-emitted-nothing-on-stdout", wa6_get.stdout == b"" or wa6_get.stdout == "",
              f"stdout={wa6_get.stdout!r} -- must be empty, never the corrupted bytes", failures)

        # ==================== WA7: custody -- pg_dump / restore / byte-identical ====================
        print("== WA7: pg_dump of the scratch pair, restore to a SECOND scratch pair ==")
        world2 = "s51fxrestore"
        teardown(world2)
        dump_path = Path(tmpdir) / "wa7-dump.sql"
        cp = sh(["pg_dump", "-h", PGHOST, "-d", PGDB, "--schema", world, "--schema", f"{world}_kernel",
                 "-f", str(dump_path)])
        check("wa7-pg-dump-succeeded", cp.returncode == 0, f"exit={cp.returncode} stderr={cp.stderr}",
              failures)
        dump_text = dump_path.read_text(encoding="utf-8")
        # Rename the KERNEL schema token first (it is the longer, more specific token; renaming
        # the plain schema token first would also corrupt every "<world>_kernel" occurrence).
        # Two-step token rename via a throwaway sentinel: renaming the KERNEL token directly to
        # "{world2}_kernel" would then be RE-MATCHED by the plain-schema replace below (world2
        # itself starts with world, e.g. s51fx -> s51fxrestore, so "s51fxrestore_kernel" itself
        # contains "s51fx" as a substring and would double-substitute into
        # "s51fxrestorerestore_kernel" -- witnessed live before this fix). A sentinel with no
        # relation to either name sidesteps the self-collision entirely.
        _sentinel = "S51FX_KERNEL_SENTINEL_TOKEN"
        renamed = (dump_text.replace(f"{world}_kernel", _sentinel)
                             .replace(world, world2)
                             .replace(_sentinel, f"{world2}_kernel"))
        renamed_path = Path(tmpdir) / "wa7-dump-renamed.sql"
        renamed_path.write_text(renamed, encoding="utf-8")
        # The dump's OWNER/GRANT statements also renamed "{world}_rw" -> "{world2}_rw" (the same
        # substring rename applied to the role name that appears throughout the DDL) -- that
        # target role must exist before the restore's ALTER ... OWNER TO / GRANT statements can
        # succeed. A fresh role, not a copy of the original's password/other state -- ownership
        # continuity is all this drill needs.
        cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"CREATE ROLE {world2}_rw LOGIN PASSWORD 'x';"])
        check("wa7-target-role-created", cp.returncode == 0, f"stderr={cp.stderr}", failures)
        # NO pre-created target schema: the plain-text dump's own `CREATE SCHEMA <name>;`
        # statement creates it -- pre-creating it here would collide with that statement.
        cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", str(renamed_path)])
        check("wa7-restore-succeeded", cp.returncode == 0,
              f"exit={cp.returncode} stdout_tail={cp.stdout[-1500:]} stderr_tail={cp.stderr[-1500:]}",
              failures)
        restored_bytes_b64 = sql1(world2,
            f"SELECT encode(bytes,'base64') FROM {world2}_kernel.artifact WHERE hash = "
            f"'{expected_hash_cli}';")
        check("wa7-restored-byte-identical",
              base64.b64decode(restored_bytes_b64) == cli_content,
              "the restored second schema pair's row decodes to the exact original bytes -- "
              "the backup-covers-referents claim witnessed, not asserted", failures)
        teardown(world2)

        # ==================== WA8: charter integration (role_charter.py) ====================
        print("== WA8: charter registration whose bytes are also in the store ==")
        charter_path = Path(tmpdir) / "WA8-CHARTER.md"
        charter_path.write_text("# WA8 fixture charter\n\nbinds nothing real -- fixture only.\n",
                                 encoding="utf-8")
        charter_bytes = charter_path.read_bytes()
        put_cp2 = run_cli(["artifact", "put", str(charter_path)], dep_path,
                           env_extra={"LED_ACTOR": "author-fixture"})
        check("wa8-artifact-put-ok", put_cp2.returncode == 0, f"stderr={put_cp2.stderr!r}", failures)
        # role_charter.py's --led default is "./legacy/led" (a scaffolded world's own shim,
        # relative to the caller's CWD) -- this fixture has no scaffolded world, so it overrides
        # --led with legacy-led.tmpl's OWN path directly (the tool's documented override), which
        # is independently executable (its own #!/usr/bin/env bash shebang).
        register_cp = sh(["python3", str(REPO / "tools" / "role_charter.py"), "register",
                           "author-fixture", str(charter_path), "--led", str(LEGACY_LED_TMPL)],
                          cwd=str(REPO), env={**os.environ, "AUTOHARN": str(REPO),
                                               "PICKUP_DEPLOYMENT": str(dep_path),
                                               "LED_ACTOR": "author-fixture"})
        check("wa8-charter-register", register_cp.returncode == 0,
              f"exit={register_cp.returncode} stdout={register_cp.stdout!r} "
              f"stderr={register_cp.stderr!r}", failures)
        show_cp = sh(["python3", str(REPO / "tools" / "role_charter.py"), "show", "author-fixture",
                      "--led", str(LEGACY_LED_TMPL)],
                     cwd=str(REPO), env={**os.environ, "AUTOHARN": str(REPO),
                                          "PICKUP_DEPLOYMENT": str(dep_path)})
        check("wa8-charter-show-resolves-ok",
              show_cp.returncode == 0 and "OK -- on-disk bytes match" in show_cp.stdout,
              f"exit={show_cp.returncode} stdout={show_cp.stdout!r} stderr={show_cp.stderr!r}",
              failures)
        expected_charter_hash = hashlib.sha256(charter_bytes).hexdigest()
        stored_charter_b64 = sql1(world,
            f"SET ROLE {world}_rw; SELECT encode(bytes,'base64') FROM {world}_kernel.artifact "
            f"WHERE hash = '{expected_charter_hash}';")
        check("wa8-store-resolves-same-bytes-charter-cites",
              base64.b64decode(stored_charter_b64) == charter_bytes,
              "the artifact store's own copy (registered via `led artifact put`) decodes to the "
              "exact bytes role_charter.py's independent hash computation also matched", failures)

    finally:
        teardown("s51fx")
        teardown("s51fxrestore")

    if failures:
        print(f"FAIL: {len(failures)} case(s): {failures}")
        return 1
    print("all s51-artifact-store cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
