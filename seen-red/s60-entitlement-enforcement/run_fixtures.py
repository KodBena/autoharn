#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s60-entitlement-enforcement.sql
(design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §6's witness plan). Real infra, no mocks: a CLASSIC
scaffold + manual chain apply (s15..s60) in the TOY db, torn down before AND after.

Per the spec §6, red first:
  RED 1  -- per-act-class role refusal: a principal with NO role binding attempts an
            authority-bearing act (principal_registered) -- refused, journaled write_refused,
            taught text naming the missing binding + remedy.
  RED 2  -- no-chain-to-genesis refusal: a principal who HOLDS the required role but has NO
            acts-for chain to genesis attempts an authority-bearing act -- refused on conjunct
            (b) even though conjunct (a) is satisfied.
  RED 3  -- the severed-chain leg (I5 asymmetry): a three-hop delegation chain
            (author -> D1 -> D2, both acts-for), D2 performs an authority-bearing act (accepted,
            credited); D1 is then SUSPENDED (severing the chain through D1 prospectively); D2
            attempts a SECOND authority-bearing act -- refused (conjunct b); D2's FIRST act
            stays credited (still present in ledger_current) -- I5 witnessed via the credited
            view, not merely asserted.
  GREEN  -- zero-friction: after the s60 birth sequence (bind author to role 'authority',
            configure the default act-class map), author performs the SAME acts a pre-s60
            world's birth sequence performs, byte-compared (verdict shape) against a WORLD
            scaffolded WITHOUT s60 in its chain.
  AGREE  -- the SQL/ASP differential: principal_authority_chain_reaches_genesis(pid) compared,
            per registered principal, against engine/lp/ledger_entitlement.lp's reaches_genesis/1
            (engine/ledger_edb.py's export_entitlement()), on the RED-3 world's post-suspension
            snapshot (the shape most likely to disagree if either side drifts).

Each check() names the witness that would show it false. Usage:
    python3 seen-red/s60-entitlement-enforcement/run_fixtures.py
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

CHAIN_S59 = [
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
]
CHAIN_S60 = CHAIN_S59 + ["s60-entitlement-enforcement.sql"]


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
                                "purpose": "s60 fixture's own write-boundary registration"}),
    ]:
        v = bw_call(world, fn, payload)
        if v["disposition"] != "accepted":
            raise RuntimeError(f"birth act refused: {v}")
    return author


def s60_birth(world: str, author: str) -> None:
    """The two NEW s60 birth acts (bootstrap/new-project.sh's own append, mirrored here):
    bind author to role 'authority', then configure the default act-class map (five classes)."""
    v = bw_call(world, "ledger_write", {
        "kind": "principal_role_bound",
        "statement": "author bound to role 'authority' (s60 fixture birth)",
        "actor": author, "principal_subject": author,
        "principal_role_name": "authority", "principal_binding_active": "true"})
    if v["disposition"] != "accepted":
        raise RuntimeError(f"s60 birth step 5 refused: {v}")
    for act_class in ("principal_registered", "principal_role_bound", "standing_lifecycle",
                      "milestone_closure", "gate_edge_supersession"):
        v = bw_call(world, "ledger_write", {
            "kind": "entitlement_class_configured",
            "statement": f"act class '{act_class}' requires role 'authority' (s60 fixture birth)",
            "actor": author, "entitlement_act_class": act_class,
            "principal_role_name": "authority"})
        if v["disposition"] != "accepted":
            raise RuntimeError(f"s60 birth step 6 ({act_class}) refused: {v}")


def register(world: str, name: str, agent_class: str, actor: str) -> str:
    v = bw_call(world, "registration_write", {
        "name": name, "agent_class": agent_class, "actor": actor,
        "purpose": f"s60 fixture principal {name}"})
    if v["disposition"] != "accepted":
        raise RuntimeError(f"registering {name} refused: {v}")
    K = f"{world}_kernel"
    return psql_tuples(f"SELECT id FROM {K}.principal WHERE name='{name}';")


def acts_for(world: str, actor: str, subject: str, obj: str) -> dict:
    return bw_call(world, "ledger_write", {
        "kind": "principal_relation_asserted", "actor": actor,
        "statement": f"{subject} acts-for {obj}",
        "principal_subject": subject, "principal_object": obj,
        "principal_relation": "acts-for", "principal_binding_active": "true"})


def bind_role(world: str, actor: str, subject: str, role_name: str) -> dict:
    return bw_call(world, "ledger_write", {
        "kind": "principal_role_bound", "actor": actor,
        "statement": f"{subject} bound to role {role_name}",
        "principal_subject": subject, "principal_role_name": role_name,
        "principal_binding_active": "true"})


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    world_red, world_pre = "s60fxred", "s60fxpre"
    for w in (world_red, world_pre):
        teardown(w)
    try:
        # ================= RED/GREEN/AGREE world (chain s15..s60) =================
        print(f"== scaffolding classic world {world_red} (chain ends {CHAIN_S60[-1]}) ==")
        wr = scaffold_classic(world_red, CHAIN_S60)
        tmps.append(wr.parent)
        author = birth_via_boundary(world_red)

        # Run the s60 birth sequence FIRST (author gets role 'authority', the default act-class
        # map is configured) -- conjunct (a) is only a live refusal once its act class IS
        # configured; testing role-refusal before configuration would exercise conjunct (b)'s
        # vacuous-role-but-no-chain path instead (a real, but DIFFERENT, leg -- RED 2 below).
        s60_birth(world_red, author)

        # ---- RED 1: per-act-class role refusal ----
        builder = register(world_red, "builder", "subagent", author)
        v_role_refused = bw_call(world_red, "registration_write", {
            "name": "second-victim", "agent_class": "subagent", "actor": builder,
            "purpose": "should be refused -- builder holds no role"})
        check("RED-1-role-refusal",
              v_role_refused["disposition"] == "refused"
              and "conjunct a" in v_role_refused["message"]
              and "authority" in v_role_refused["message"],
              f"builder (registered, no role binding) attempts principal_registered -- "
              f"verdict={v_role_refused}", failures)
        refusal_id = v_role_refused.get("refusal_id")
        r_journal = psql_tuples(
            f"SELECT count(*) FROM {world_red}.ledger_current "
            f"WHERE id={refusal_id} AND kind='write_refused';") if refusal_id else "0"
        check("RED-1-journaled",
              r_journal == "1",
              f"refusal_id={refusal_id} -- a committed write_refused row present in "
              f"ledger_current (count={r_journal})", failures)

        # ---- RED 2: no-chain-to-genesis (actor HOLDS the role, has NO acts-for chain) ----
        stranger = register(world_red, "stranger", "subagent", author)
        v_bind_stranger = bind_role(world_red, author, stranger, "authority")
        if v_bind_stranger["disposition"] != "accepted":
            raise RuntimeError(f"could not bind stranger's role: {v_bind_stranger}")
        v_chain_refused = bw_call(world_red, "registration_write", {
            "name": "stranger-victim", "agent_class": "subagent", "actor": stranger,
            "purpose": "should be refused -- stranger holds the role but no chain to genesis"})
        check("RED-2-chain-refusal",
              v_chain_refused["disposition"] == "refused"
              and "conjunct b" in v_chain_refused["message"]
              and "genesis" in v_chain_refused["message"],
              f"stranger (role bound, NO acts-for chain) attempts principal_registered -- "
              f"verdict={v_chain_refused}", failures)

        # ---- RED 3: severed-chain leg (I5 asymmetry) ----
        d1 = register(world_red, "delegate1", "subagent", author)
        d2 = register(world_red, "delegate2", "subagent", author)
        for p in (d1, d2):
            v = bind_role(world_red, author, p, "authority")
            if v["disposition"] != "accepted":
                raise RuntimeError(f"could not bind delegate role: {v}")
        v_af1 = acts_for(world_red, author, d1, author)
        v_af2 = acts_for(world_red, author, d2, d1)
        if v_af1["disposition"] != "accepted" or v_af2["disposition"] != "accepted":
            raise RuntimeError(f"could not establish chain: {v_af1} {v_af2}")
        v_d2_first = bw_call(world_red, "registration_write", {
            "name": "d2-first-act", "agent_class": "subagent", "actor": d2,
            "purpose": "D2's first act, through the live chain -- should be ACCEPTED"})
        check("RED-3-pre-suspension-accepted",
              v_d2_first["disposition"] == "accepted",
              f"D2 (chain D2->D1->author) performs an authority-bearing act -- verdict={v_d2_first}",
              failures)
        first_act_row_id = v_d2_first.get("row_id")

        # Suspend D1 -- an authority-bearing act itself, performed by author (genesis, trivially
        # chain-connected) -- severs D2's chain PROSPECTIVELY.
        v_suspend = bw_call(world_red, "ledger_write", {
            "kind": "principal_suspended", "actor": author,
            "statement": "D1 suspended -- severs D2's chain prospectively (I5 witness)",
            "principal_subject": d1, "principal_binding_active": "true"})
        if v_suspend["disposition"] != "accepted":
            raise RuntimeError(f"could not suspend D1: {v_suspend}")

        v_d2_second = bw_call(world_red, "registration_write", {
            "name": "d2-second-act", "agent_class": "subagent", "actor": d2,
            "purpose": "D2's SECOND act, chain now severed via D1 -- should be REFUSED"})
        check("RED-3-severed-chain-refusal",
              v_d2_second["disposition"] == "refused" and "conjunct b" in v_d2_second["message"],
              f"D2's second act, after D1's suspension -- verdict={v_d2_second}", failures)

        credited_still = psql_tuples(
            f"SELECT count(*) FROM {world_red}.ledger_current WHERE id={first_act_row_id};") \
            if first_act_row_id else "0"
        check("RED-3-I5-past-act-credited",
              credited_still == "1",
              f"D2's FIRST act (row {first_act_row_id}), written before D1's suspension, is "
              f"still present in ledger_current after the chain severed -- count={credited_still}",
              failures)

        # ---- GREEN: zero-friction, byte-compared against a pre-s60 world ----
        print(f"== scaffolding classic world {world_pre} (chain ends {CHAIN_S59[-1]}, NO s60) ==")
        wp = scaffold_classic(world_pre, CHAIN_S59)
        tmps.append(wp.parent)
        author_pre = birth_via_boundary(world_pre)
        v_pre = bw_call(world_pre, "ledger_write", {
            "kind": "decision", "statement": "an ordinary decision row, pre-s60",
            "actor": author_pre})
        v_post = bw_call(world_red, "ledger_write", {
            "kind": "decision", "statement": "an ordinary decision row, post-s60-birth",
            "actor": author})
        check("GREEN-ordinary-act-verdict-shape",
              (v_pre["disposition"], v_pre["sqlstate"], v_pre["message"])
              == (v_post["disposition"], v_post["sqlstate"], v_post["message"]) == ("accepted", None, None),
              f"an ordinary (non-gated) kind's verdict shape is IDENTICAL pre-s60 vs post-s60-"
              f"birth: pre={v_pre}, post={v_post}", failures)

        v_pre_reg = bw_call(world_pre, "registration_write", {
            "name": "ordinary-registration", "agent_class": "subagent", "actor": author_pre,
            "purpose": "an ordinary authority-bearing act by genesis, pre-s60"})
        v_post_reg = bw_call(world_red, "registration_write", {
            "name": "ordinary-registration-post", "agent_class": "subagent", "actor": author,
            "purpose": "the SAME class of act by genesis, post-s60-birth -- must still be accepted"})
        check("GREEN-genesis-registration-still-accepted",
              v_pre_reg["disposition"] == v_post_reg["disposition"] == "accepted",
              f"genesis registering a principal is ACCEPTED both pre-s60 and post-s60-birth "
              f"(the zero-friction leg): pre={v_pre_reg['disposition']}, "
              f"post={v_post_reg['disposition']}", failures)

        # ---- AGREE: SQL/ASP differential on the RED-3 world's post-suspension snapshot ----
        # engine/targets.py's precedence order puts LEDGER_DB/LEDGER_SCHEMA/LEDGER_KERN ahead of
        # the scratch-naming conventions (which would otherwise wrongly resolve this world's
        # NAME into the `epistemic` database) -- set them for this one-off target, restored after.
        os.environ["LEDGER_DB"] = PGDB
        os.environ["LEDGER_SCHEMA"] = world_red
        os.environ["LEDGER_KERN"] = f"{world_red}_kernel"
        os.environ.setdefault("EPISTEMIC_PGHOST", PGHOST)
        agree_note = ""
        try:
            exp = ledger_edb.export_entitlement("s60-fixture-oneoff")
            edb_text = exp.edb_text()
            clingo = sh(["clingo", str(ENGINE / "lp" / "ledger_tnow.lp"),
                        str(ENGINE / "lp" / "ledger_entitlement.lp"), "/dev/stdin", "0"],
                       input=edb_text)
            print(f"  [clingo raw stdout]\n{clingo.stdout}\n  [clingo raw stderr]\n{clingo.stderr}\n")
            asp_reaches = set()
            for line in clingo.stdout.splitlines():
                if line.startswith("Answer"):
                    continue
                for tok in line.split():
                    if tok.startswith("reaches_genesis(") and tok.endswith(")"):
                        asp_reaches.add(tok[len("reaches_genesis("):-1])
            all_pids = psql_tuples(f"SELECT id FROM {world_red}_kernel.principal ORDER BY id;").splitlines()
            sql_reaches = set()
            for pid in all_pids:
                r = psql_tuples(
                    f"SELECT {world_red}.principal_authority_chain_reaches_genesis({pid});")
                if r == "t":
                    sql_reaches.add(pid)
            check("AGREE-sql-asp-differential",
                  asp_reaches == sql_reaches,
                  f"SQL principal_authority_chain_reaches_genesis vs ASP reaches_genesis/1, "
                  f"per registered principal: SQL={sorted(sql_reaches, key=int)}, "
                  f"ASP={sorted(asp_reaches, key=int)}", failures)
        except ledger_edb.CapabilityError as e:
            agree_note = str(e)
            check("AGREE-sql-asp-differential", False,
                  f"export_entitlement raised CapabilityError (target resolution gap, not a "
                  f"logic defect): {agree_note}", failures)

    finally:
        for w in (world_red, world_pre):
            teardown(w)
        for t in tmps:
            sh(["rm", "-rf", str(t)])

    print(f"\n{'ALL GREEN' if not failures else 'FAILURES: ' + ', '.join(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
