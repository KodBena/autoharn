#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s65-refusal-attempted-kind.sql
(design/FABLE-S65-REFUSAL-ATTEMPTED-KIND-SPEC.md, RATIFIED 2026-07-27, ledger row 1487). Real
infra, no mocks: a CLASSIC scaffold + manual chain apply (s15..s64..s65) in the TOY db, torn down
before AND after. Modeled directly on seen-red/s64-principal-stamps-delegation-conditions/
run_fixtures.py (birth/bw_call/relate helpers) and seen-red/s43-typed-verdict-write-boundary/
run_fixtures.py (verify_chain/oracle helpers) -- same shape, same both-polarity discipline.

RED, per the spec's own §3 witness plan:
  RED-NON-WRITE-REFUSED-CARRYING-KIND -- an ordinary (kind='note') ledger_write payload that
                                         additionally tries to set refusal_attempted_kind directly
                                         -- REFUSED by the new one-way kind-shape CHECK
                                         (refusal_attempted_kind_kind_shape), journaled itself
                                         (surface='ledger', SQLSTATE 23514).
  RED-baseline-re-witnessed            -- the pre-s65 shape re-witnessed on an s64-head world:
                                         an invalid-kind write journals with NO attempted-kind
                                         information available at all (the column does not
                                         exist there) -- the rows-1474/1476 incident shape this
                                         delta closes.
GREEN:
  GREEN-INVALID-KIND-INCIDENT-SPECIMEN -- ledger_write with kind='row' (not a member of
                                         ledger_kind_check's vocabulary -- the incident's own
                                         probable specimen) -- REFUSED, journaled with
                                         refusal_attempted_kind='row' extracted verbatim.
  GREEN-MISSING-KIND-NULL              -- ledger_write payload with NO `kind` key at all --
                                         REFUSED (kind NOT NULL), journaled with
                                         refusal_attempted_kind NULL (the s49-totality-shaped
                                         "never abort, just NULL" leg -- not_null_violation is
                                         still one of the journaled 22/23/P0 classes).
  GREEN-NONTEXT-KIND-NULL              -- ledger_write payload with `kind` a JSON NUMBER (not a
                                         string) -- REFUSED (the stringified value fails
                                         ledger_kind_check), journaled with
                                         refusal_attempted_kind NULL (present but non-text ->
                                         not extractable).
  GREEN-NON-LEDGER-SURFACE-NULL        -- obligation_write refused (obligation_not_self_assigned
                                         CHECK) -- journaled surface='obligation',
                                         refusal_attempted_kind NULL (that payload contract has
                                         no `kind` key to begin with -- structurally NULL, not a
                                         failed extraction).
  GREEN-ACCEPTED-WRITE-BYTE-IDENTICAL  -- an ordinary accepted (kind='decision') write's verdict
                                         shape, pre-s65 (s64-head world) vs post-s65-birth,
                                         IDENTICAL; its own refusal_attempted_kind stays NULL
                                         (licensed only on write_refused rows).
  ZERO-FRICTION-BIRTH                  -- a fresh classic scaffold's birth sequence through s65,
                                         unaffected.
  VERIFY-CHAIN-INTACT-THROUGH-REFUSALS -- ./autoharn verify-chain INTACT + the s43 refusal-oracle
                                         CONFIRMED, after every refusal above.
  AGREE-sql-asp-differential           -- SQL principal_authority_chain_reaches_genesis(pid) vs
                                         ASP reaches_genesis/1 (unscoped, s60/s62's own
                                         differential) on the s65-head world -- sanity that this
                                         delta's DDL does not disturb the standing entitlement
                                         differential (the spec's own §1 item 4: NO derivation
                                         reads any refusal_* column, so this is a non-regression
                                         check, never a claim of NEW coverage for refusal_
                                         attempted_kind itself).

Each check() names the witness that would show it false. Usage:
    python3 seen-red/s65-refusal-attempted-kind/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports are banned."""
from __future__ import annotations

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
ENGINE = REPO / "engine"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(REPO / "filing"))

import ledger_edb  # noqa: E402
import pghost_resolve  # noqa: E402

os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S64 = [
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
    "s62-delegation-lifecycle-gating.sql", "s63-supersession-body-restoration.sql",
    "s64-principal-stamps-delegation-conditions.sql",
]
CHAIN_S65 = CHAIN_S64 + ["s65-refusal-attempted-kind.sql"]


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
        raise RuntimeError(f"NON-VERDICT: {r.stderr.strip()[-500:]}")
    lines = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("{")]
    if not lines:
        raise RuntimeError(f"NO VERDICT LINE: stdout={r.stdout!r} stderr={r.stderr!r}")
    return json.loads(lines[-1])


def bw_call_raw_kind_key(world: str, fn: str, raw_json_text: str) -> dict:
    """Same as bw_call, but the payload is a LITERAL JSON text fragment the caller has already
    hand-built (used for the non-text-kind leg, where a Python dict/json.dumps would only ever
    produce a JSON string for a Python str -- we need a bare JSON number at the `kind` key,
    which no ordinary payload dict can express)."""
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    pj = raw_json_text.replace("'", "''")
    r = psql_raw(
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"SELECT to_jsonb(v) FROM {K}.{fn}('{pj}'::jsonb) v;\n")
    if r.returncode != 0:
        raise RuntimeError(f"NON-VERDICT: {r.stderr.strip()[-500:]}")
    lines = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("{")]
    if not lines:
        raise RuntimeError(f"NO VERDICT LINE: stdout={r.stdout!r} stderr={r.stderr!r}")
    return json.loads(lines[-1])


def birth_via_boundary(world: str) -> str:
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
                                "purpose": "s65 fixture's own write-boundary registration"}),
    ]:
        v = bw_call(world, fn, payload)
        if v["disposition"] != "accepted":
            raise RuntimeError(f"birth act refused: {v}")
    return author


def verify_chain(world_dir: Path) -> tuple[int, str]:
    cp = sh(["sh", str(world_dir / "autoharn"), "verify-chain"], cwd=str(world_dir))
    return cp.returncode, cp.stdout + cp.stderr


def refusal_row(world: str, refusal_id: str) -> str:
    K = f"{world}_kernel"
    return psql_tuples(
        f"SELECT refusal_surface || '|' || refusal_sqlstate || '|' || "
        f"coalesce(refusal_attempted_kind,'<NULL>') "
        f"FROM {world}.ledger WHERE id = {refusal_id};")


def main() -> int:  # noqa: C901 -- one straight-line witness script, matching s60/s62/s64's shape
    failures: list[str] = []
    tmps: list[Path] = []
    world_main, world_pre, world_birth = "s65fxmain", "s65fxpre", "s65fxbirth"
    for w in (world_main, world_pre, world_birth):
        teardown(w)
    try:
        # ===================== WORLD PRE (s64 head, no s65) =====================
        print(f"== scaffolding classic world {world_pre} (chain ends {CHAIN_S64[-1]}, NO s65) ==")
        wp = scaffold_classic(world_pre, CHAIN_S64)
        tmps.append(wp.parent)
        author_pre = birth_via_boundary(world_pre)
        v_invalid_pre = bw_call(world_pre, "ledger_write",
                                 {"kind": "row", "statement": "pre-s65 invalid-kind write",
                                  "actor": author_pre})
        pre_cols = psql_tuples(
            f"SELECT string_agg(column_name, ',') FROM information_schema.columns "
            f"WHERE table_schema='{world_pre}' AND table_name='ledger' "
            f"AND column_name = 'refusal_attempted_kind';")
        check("RED-baseline-re-witnessed-no-attempted-kind-column",
              v_invalid_pre["disposition"] == "refused" and pre_cols == "",
              f"pre-s65 (s64-head) world: an invalid-kind ('row') write is refused exactly as "
              f"before, but the world's own ledger table carries NO refusal_attempted_kind "
              f"column at all (pre_cols={pre_cols!r}) -- the rows-1474/1476 incident shape this "
              f"delta closes -- verdict={v_invalid_pre}", failures)

        # ===================== WORLD MAIN (s65 head) =====================
        print(f"== scaffolding classic world {world_main} (chain ends {CHAIN_S65[-1]}) ==")
        wm = scaffold_classic(world_main, CHAIN_S65)
        tmps.append(wm.parent)
        author = birth_via_boundary(world_main)

        # ---- RED: a non-write_refused row tries to carry refusal_attempted_kind directly ----
        v_forge = bw_call(world_main, "ledger_write",
                           {"kind": "note", "statement": "forged attempted-kind attempt",
                            "actor": author, "refusal_attempted_kind": "row"})
        check("RED-NON-WRITE-REFUSED-CARRYING-KIND-refused",
              v_forge["disposition"] == "refused" and v_forge["sqlstate"] == "23514"
              and "refusal_attempted_kind_kind_shape" in v_forge["message"],
              f"kind='note' payload additionally supplying refusal_attempted_kind directly -- "
              f"refused by the new one-way kind-shape CHECK -- verdict={v_forge}", failures)

        # ---- GREEN-INVALID-KIND-INCIDENT-SPECIMEN: kind='row' (the incident's own specimen) ----
        v_row = bw_call(world_main, "ledger_write",
                         {"kind": "row", "statement": "s65 fixture: incident specimen",
                          "actor": author})
        row_detail = refusal_row(world_main, v_row["refusal_id"]) if v_row["refusal_id"] else "N/A"
        check("GREEN-INVALID-KIND-INCIDENT-SPECIMEN-accepted-kind-recorded",
              v_row["disposition"] == "refused" and row_detail == "ledger|23514|row",
              f"ledger_write with kind='row' (not a member of ledger_kind_check's vocabulary) -- "
              f"REFUSED, journaled row detail (surface|sqlstate|attempted_kind)={row_detail!r} "
              f"(expect 'ledger|23514|row') -- verdict={v_row}", failures)

        # ---- GREEN-MISSING-KIND-NULL: no `kind` key at all ----
        v_missing = bw_call(world_main, "ledger_write",
                             {"statement": "s65 fixture: no kind key at all", "actor": author})
        missing_detail = (refusal_row(world_main, v_missing["refusal_id"])
                           if v_missing["refusal_id"] else "N/A")
        check("GREEN-MISSING-KIND-NULL-accepted",
              v_missing["disposition"] == "refused" and v_missing["sqlstate"] == "23502"
              and missing_detail == "ledger|23502|<NULL>",
              f"ledger_write payload with NO `kind` key -- REFUSED (kind NOT NULL, 23502), "
              f"journaled detail={missing_detail!r} (expect NULL attempted-kind -- 'not "
              f"extractable', never aborting the refusal recording -- the s49-totality shape) "
              f"-- verdict={v_missing}", failures)

        # ---- GREEN-NONTEXT-KIND-NULL: `kind` is a JSON NUMBER, not a string ----
        v_num = bw_call_raw_kind_key(
            world_main, "ledger_write",
            json.dumps({"statement": "s65 fixture: non-text kind", "actor": author}).rstrip("}")
            + ', "kind": 42}')
        num_detail = refusal_row(world_main, v_num["refusal_id"]) if v_num["refusal_id"] else "N/A"
        check("GREEN-NONTEXT-KIND-NULL-accepted",
              v_num["disposition"] == "refused" and v_num["sqlstate"] == "23514"
              and num_detail == "ledger|23514|<NULL>",
              f"ledger_write payload with `kind` as a JSON NUMBER (42, not a string) -- REFUSED "
              f"(the stringified '42' fails ledger_kind_check), journaled detail={num_detail!r} "
              f"(expect NULL attempted-kind -- present but non-text is NOT extracted) -- "
              f"verdict={v_num}", failures)

        # ---- GREEN-NON-LEDGER-SURFACE-NULL: obligation_write refused, no `kind` key in its
        # own payload contract at all ----
        v_obl = bw_call(world_main, "obligation_write",
                         {"scope": "s65-fixture-scope", "assigned_by": author,
                          "obliges_actor": author})
        obl_detail = refusal_row(world_main, v_obl["refusal_id"]) if v_obl["refusal_id"] else "N/A"
        check("GREEN-NON-LEDGER-SURFACE-NULL-accepted",
              v_obl["disposition"] == "refused" and v_obl["sqlstate"] == "23514"
              and obl_detail == "obligation|23514|<NULL>",
              f"obligation_write with assigned_by=obliges_actor (obligation_not_self_assigned "
              f"CHECK) -- REFUSED, journaled detail={obl_detail!r} (expect NULL -- the "
              f"obligation payload contract has no `kind` key to begin with, structurally NULL, "
              f"never a failed extraction) -- verdict={v_obl}", failures)

        # ---- GREEN-ACCEPTED-WRITE-BYTE-IDENTICAL: ordinary accepted write, verdict shape ----
        v_pre_ok = bw_call(world_pre, "ledger_write",
                            {"kind": "decision", "statement": "an ordinary decision row, pre-s65",
                             "actor": author_pre})
        v_post_ok = bw_call(world_main, "ledger_write",
                             {"kind": "decision", "statement": "an ordinary decision row, "
                                                                "post-s65-birth", "actor": author})
        post_ok_kind_col = psql_tuples(
            f"SELECT coalesce(refusal_attempted_kind,'<NULL>') FROM {world_main}.ledger "
            f"WHERE id = {v_post_ok['row_id']};")
        check("GREEN-ACCEPTED-WRITE-BYTE-IDENTICAL-verdict-shape",
              (v_pre_ok["disposition"], v_pre_ok["sqlstate"], v_pre_ok["message"])
              == (v_post_ok["disposition"], v_post_ok["sqlstate"], v_post_ok["message"])
              == ("accepted", None, None) and post_ok_kind_col == "<NULL>",
              f"an ordinary (kind='decision') write's verdict shape is IDENTICAL pre-s65 vs "
              f"post-s65-birth: pre={v_pre_ok}, post={v_post_ok}; the accepted row's own "
              f"refusal_attempted_kind stays NULL ({post_ok_kind_col!r}, licensed only on "
              f"write_refused rows)", failures)

        # ---- ZERO-FRICTION-BIRTH ----
        print(f"== scaffolding classic world {world_birth} (chain ends {CHAIN_S65[-1]}, fresh "
              f"birth) ==")
        wb = scaffold_classic(world_birth, CHAIN_S65)
        tmps.append(wb.parent)
        author_birth = birth_via_boundary(world_birth)
        v_birth_ok = bw_call(world_birth, "ledger_write",
                              {"kind": "note", "statement": "zero-friction birth note",
                               "actor": author_birth})
        check("ZERO-FRICTION-BIRTH-accepted",
              v_birth_ok["disposition"] == "accepted",
              f"a fresh world's own s40/s43/s65 birth sequence, then an ordinary note write -- "
              f"ACCEPTED, no extra friction from this delta -- verdict={v_birth_ok}", failures)

        # ---- VERIFY-CHAIN-INTACT-THROUGH-REFUSALS + oracle reconciliation ----
        rc_v, out_v = verify_chain(wm)
        oracle_count = psql_tuples(
            f"SELECT count(*) FROM {world_main}.ledger WHERE kind='write_refused';")
        oracle_seq = psql_tuples(
            f"SELECT CASE WHEN is_called THEN last_value ELSE 0 END FROM "
            f"{world_main}_kernel.refusal_seq;")
        check("VERIFY-CHAIN-INTACT-THROUGH-REFUSALS",
              rc_v == 0 and "INTACT" in out_v and "REFUSAL-ORACLE-CONFIRMED" in out_v
              and oracle_count == oracle_seq,
              f"./autoharn verify-chain after five refusals (forged-kind attempt, kind='row', "
              f"missing kind, non-text kind, obligation self-assign) -- exit={rc_v}, "
              f"INTACT+ORACLE-CONFIRMED in output={('INTACT' in out_v) and ('REFUSAL-ORACLE-CONFIRMED' in out_v)}, "
              f"oracle count={oracle_count} == sequence={oracle_seq}", failures)

        # ---- AGREE: SQL/ASP differential sanity (unscoped reaches_genesis) ----
        os.environ["LEDGER_DB"] = PGDB
        os.environ["LEDGER_SCHEMA"] = world_main
        os.environ["LEDGER_KERN"] = f"{world_main}_kernel"
        os.environ.setdefault("EPISTEMIC_PGHOST", PGHOST)
        try:
            exp = ledger_edb.export_entitlement("s65-fixture-oneoff")
            edb_text = exp.edb_text()
            clingo = sh(["clingo", str(ENGINE / "lp" / "ledger_tnow.lp"),
                        str(ENGINE / "lp" / "ledger_entitlement.lp"), "/dev/stdin", "0"],
                       input=edb_text)
            print(f"  [clingo raw stdout]\n{clingo.stdout}\n  [clingo raw stderr]\n{clingo.stderr}\n")
            asp_reaches: set[str] = set()
            for line in clingo.stdout.splitlines():
                if line.startswith("Answer"):
                    continue
                for tok in line.split():
                    if tok.startswith("reaches_genesis(") and tok.endswith(")"):
                        asp_reaches.add(tok[len("reaches_genesis("):-1])
            all_pids = psql_tuples(
                f"SELECT id FROM {world_main}_kernel.principal ORDER BY id;").splitlines()
            sql_reaches: set[str] = set()
            for pid in all_pids:
                r = psql_tuples(
                    f"SELECT {world_main}.principal_authority_chain_reaches_genesis({pid});")
                if r == "t":
                    sql_reaches.add(pid)
            check("AGREE-sql-asp-differential",
                  asp_reaches == sql_reaches,
                  f"SQL principal_authority_chain_reaches_genesis(pid) vs ASP reaches_genesis/1 "
                  f"on the s65-head world -- a non-regression sanity check, since NO derivation "
                  f"reads any refusal_* column (this delta's own §1 item 4 finding) --  "
                  f"symmetric_difference={sorted(asp_reaches ^ sql_reaches)}", failures)
        except ledger_edb.CapabilityError as e:
            check("AGREE-sql-asp-differential", False,
                  f"export_entitlement raised CapabilityError (target resolution gap, not a "
                  f"logic defect): {e}", failures)

    finally:
        for w in (world_main, world_pre, world_birth):
            teardown(w)
        for t in tmps:
            sh(["rm", "-rf", str(t)])

    print(f"\n{'ALL GREEN' if not failures else 'FAILURES: ' + ', '.join(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
