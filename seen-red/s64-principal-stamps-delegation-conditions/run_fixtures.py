#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s64-principal-stamps-delegation-
conditions.sql (design/FABLE-PRINCIPAL-STAMPS-SPEC.md, RATIFIED 2026-07-26, §3 item 1). Real
infra, no mocks: a CLASSIC scaffold + manual chain apply (s15..s63..s64) in the TOY db, torn down
before AND after. Modeled directly on seen-red/s62-delegation-lifecycle-gating/run_fixtures.py
(same helpers, same both-polarity discipline) -- s64 rides the SAME class-ratified fail-safe
family.

RED FIRST, per the commission's own witness plan (design/FABLE-PRINCIPAL-STAMPS-SPEC.md §5):
  RED-DISPATCHED-BY-CHAINLESS       -- a chainless, role-bound actor asserts a fresh
                                       dispatched-by edge -- REFUSED (the hazard-in-reach fix:
                                       before this delta, dispatched-by was classified NULL and
                                       sailed through ungated; s64 classifies it
                                       delegation_lifecycle, same as acts-for).
  RED-DEPTH-EXHAUSTED               -- author grants D1 a NO-REDELEGATE (depth=0) edge; D1
                                       attempts to grant D2 a further acts-for edge -- REFUSED
                                       (conjunct c).
  RED-DEPTH-SECOND-HOP              -- author grants D6 a depth=1 edge; D6 grants D7 (accepted,
                                       consuming the one hop); D7 attempts to grant D_deep a
                                       further edge -- REFUSED (D7's own derived budget is 0).
  RED-SCOPE-OUTSIDE-GRANT           -- author grants D3 an edge scoped to
                                       ['principal_role_bound'] only; D3 attempts
                                       principal_registered (NOT in scope) -- REFUSED (conjunct
                                       b, scope-conjuncted).
  RED-EXPIRED-EDGE                  -- author grants D4 an edge with delegation_expiry already in
                                       the past; D4 attempts any authority-bearing act --
                                       REFUSED (conjunct b, expiry-conjuncted).
  RED-COUNTERSIGN-MISSING           -- author grants D5 an edge requiring countersign by C; D5
                                       attempts an authority-bearing act with NO
                                       signature_symmetry_witness -- REFUSED (conjunct d).
  RED-COUNTERSIGN-WRONG-SIGNER      -- D5 retries citing a signature_symmetry_witness attested by
                                       the WRONG principal -- REFUSED (conjunct d).
  RED-COUNTERSIGN-MULTI-UNSATISFIABLE -- D_multi's chain carries TWO must-countersign edges
                                       naming DIFFERENT principals -- every act through it is
                                       UNCONDITIONALLY refused (the documented LIMIT: a single
                                       signature_symmetry_witness column cannot satisfy two
                                       distinct required signers at once).
  RED-CARVEOUT-DOES-NOT-EXEMPT-ORDINARY-DELEGATION -- D8 (no-redelegate, depth=0) attempts an
                                       ORDINARY (non-independent-verification) further delegation
                                       -- still REFUSED (the carve-out is BY TYPE, not blanket).
GREEN:
  GREEN-DEPTH-WITHIN-BUDGET         -- D6 (depth=1 budget) grants D7 -- ACCEPTED.
  GREEN-SCOPE-WITHIN-GRANT          -- D3 performs principal_role_bound (the ONE class its edge
                                       scopes) -- ACCEPTED.
  GREEN-COUNTERSIGN-SATISFIED       -- D5 retries citing the CORRECT countersigner's attestation
                                       -- ACCEPTED.
  GREEN-INDEPENDENT-VERIFICATION-CARVEOUT -- D8 (no-redelegate, depth=0) dispatches an
                                       independent verifier (delegation_purpose=
                                       'independent-verification') -- ACCEPTED despite budget 0.
  GREEN-DISPATCHED-BY-LEGITIMATE    -- author (chained) asserts a dispatched-by edge -- ACCEPTED
                                       (the widened classification does not close the legitimate
                                       path).
  GREEN-s60-s62-FAMILY-UNCHANGED    -- a plain acts-for grant + an ordinary authority-bearing act
                                       through it, no conditions at all -- byte-shape ACCEPTED,
                                       proving the vacuous-conjunction claim.
  ZERO-FRICTION-BIRTH               -- a fresh classic scaffold's birth sequence, unaffected.
  GREEN-ordinary-act-verdict-shape  -- pre-s60 vs post-s64-birth, identical verdict shape.
  AGREE-scoped                     -- SQL principal_authority_chain_reaches_genesis_scoped(pid,act_class)
                                       vs ASP reaches_genesis_scoped/2, over every registered
                                       principal x every one of the eight act-class tokens, on
                                       the richest post-mutation snapshot this fixture builds.

Each check() names the witness that would show it false. Usage:
    python3 seen-red/s64-principal-stamps-delegation-conditions/run_fixtures.py
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
CHAIN_S63 = CHAIN_S59 + [
    "s60-entitlement-enforcement.sql", "s61-signature-symmetry-and-key-binding.sql",
    "s62-delegation-lifecycle-gating.sql", "s63-supersession-body-restoration.sql",
]
CHAIN_S64 = CHAIN_S63 + ["s64-principal-stamps-delegation-conditions.sql"]


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
                                "purpose": "s64 fixture's own write-boundary registration"}),
    ]:
        v = bw_call(world, fn, payload)
        if v["disposition"] != "accepted":
            raise RuntimeError(f"birth act refused: {v}")
    return author


def s60_birth(world: str, author: str) -> None:
    v = bw_call(world, "ledger_write", {
        "kind": "principal_role_bound",
        "statement": "author bound to role 'authority' (s60 birth sequence)",
        "actor": author, "principal_subject": author,
        "principal_role_name": "authority", "principal_binding_active": "true"})
    if v["disposition"] != "accepted":
        raise RuntimeError(f"s60 birth step 5 refused: {v}")
    for act_class in ("principal_registered", "principal_role_bound", "standing_lifecycle",
                      "milestone_closure", "gate_edge_supersession"):
        v = bw_call(world, "ledger_write", {
            "kind": "entitlement_class_configured",
            "statement": f"act class '{act_class}' requires role 'authority' (s60 birth sequence)",
            "actor": author, "entitlement_act_class": act_class,
            "principal_role_name": "authority"})
        if v["disposition"] != "accepted":
            raise RuntimeError(f"s60 birth step 6 ({act_class}) refused: {v}")


def register(world: str, name: str, agent_class: str, actor: str) -> str:
    v = bw_call(world, "registration_write", {
        "name": name, "agent_class": agent_class, "actor": actor,
        "purpose": f"s64 fixture principal {name}"})
    if v["disposition"] != "accepted":
        raise RuntimeError(f"registering {name} refused: {v}")
    K = f"{world}_kernel"
    return psql_tuples(f"SELECT id FROM {K}.principal WHERE name='{name}';")


def relate(world: str, actor: str, subject: str, obj: str, relation: str,
           depth=None, must_countersign=None, expiry=None, scope=None, purpose=None,
           witness=None) -> dict:
    payload = {
        "kind": "principal_relation_asserted", "actor": actor,
        "statement": f"{subject} {relation} {obj} (s64 fixture)",
        "principal_subject": subject, "principal_object": obj,
        "principal_relation": relation, "principal_binding_active": "true"}
    if depth is not None:
        payload["delegation_redelegate_depth"] = depth
    if must_countersign is not None:
        payload["delegation_must_countersign"] = must_countersign
    if expiry is not None:
        payload["delegation_expiry"] = expiry
    if scope is not None:
        payload["delegation_scope_classes"] = scope
    if purpose is not None:
        payload["delegation_purpose"] = purpose
    if witness is not None:
        payload["signature_symmetry_witness"] = witness
    return bw_call(world, "ledger_write", payload)


def bind_role(world: str, actor: str, subject: str, role_name: str) -> dict:
    return bw_call(world, "ledger_write", {
        "kind": "principal_role_bound", "actor": actor,
        "statement": f"{subject} bound to role {role_name}",
        "principal_subject": subject, "principal_role_name": role_name,
        "principal_binding_active": "true"})


def act_registered(world: str, actor: str, subject: str, witness=None) -> dict:
    """An ordinary principal_registered-classified act (re-registering an EXISTING principal's
    subject id) -- the same act class s60/s62's own fixtures already use for conjunct a/b legs,
    reused here so conjunct c/d legs (which need signature_symmetry_witness, not exposed by
    registration_write's own narrower payload contract) go through the generic ledger_write."""
    payload = {"kind": "principal_registered", "actor": actor,
               "statement": f"{subject} re-registered (s64 conjunct c/d fixture)",
               "principal_subject": subject,
               "principal_purpose": "s64 fixture re-registration"}
    if witness is not None:
        payload["signature_symmetry_witness"] = witness
    return bw_call(world, "ledger_write", payload)


def open_commission(world: str, actor: str, text: str) -> str:
    v = bw_call(world, "ledger_write", {
        "kind": "commission", "actor": actor, "statement": text})
    if v["disposition"] != "accepted":
        raise RuntimeError(f"commission open refused: {v}")
    return v["row_id"]


def attest_commission(world: str, actor: str, commission_id: str, fingerprint: str) -> str:
    v = bw_call(world, "ledger_write", {
        "kind": "commission_signature_verified", "actor": actor,
        "statement": "s64 fixture attestation (no real gpg -- direct kernel-side write, "
                     "matching s61's own disclosed forgeability bound for a fixture)",
        "signature_attests_row": commission_id, "signature_grade": "directory-verified",
        "principal_key_fingerprint": fingerprint})
    if v["disposition"] != "accepted":
        raise RuntimeError(f"attestation refused: {v}")
    return v["row_id"]


def main() -> int:  # noqa: C901 -- one straight-line witness script, matching s60/s62's own shape
    failures: list[str] = []
    tmps: list[Path] = []
    world_main, world_pre, world_birth = "s64fxmain", "s64fxpre", "s64fxbirth"
    for w in (world_main, world_pre, world_birth):
        teardown(w)
    try:
        print(f"== scaffolding classic world {world_main} (chain ends {CHAIN_S64[-1]}) ==")
        wm = scaffold_classic(world_main, CHAIN_S64)
        tmps.append(wm.parent)
        author = birth_via_boundary(world_main)
        s60_birth(world_main, author)

        # ---- RED-DISPATCHED-BY-CHAINLESS: the hazard-in-reach fix ----
        chainless = register(world_main, "chainless", "subagent", author)
        v_bind_chainless = bind_role(world_main, author, chainless, "authority")
        if v_bind_chainless["disposition"] != "accepted":
            raise RuntimeError(f"could not bind chainless's role: {v_bind_chainless}")
        victim = register(world_main, "victim", "subagent", author)
        v_dispatch_ungated = relate(world_main, chainless, victim, chainless, "dispatched-by")
        check("RED-DISPATCHED-BY-CHAINLESS-refused",
              v_dispatch_ungated["disposition"] == "refused"
              and "conjunct b" in v_dispatch_ungated["message"]
              and "delegation_lifecycle" in v_dispatch_ungated["message"],
              f"chainless (role-bound, no chain) asserts a dispatched-by edge -- before s64 this "
              f"kind classified NULL and sailed through ungated -- verdict={v_dispatch_ungated}",
              failures)

        # ---- GREEN-DISPATCHED-BY-LEGITIMATE ----
        v_dispatch_ok = relate(world_main, author, victim, author, "dispatched-by")
        check("GREEN-DISPATCHED-BY-LEGITIMATE-accepted",
              v_dispatch_ok["disposition"] == "accepted",
              f"author (chained) asserts the SAME shape of edge on victim's behalf -- "
              f"verdict={v_dispatch_ok}", failures)

        # ---- RED-DEPTH-EXHAUSTED: D1 (no-redelegate) cannot grant D2 ----
        d1 = register(world_main, "d1", "subagent", author)
        v_d1_bind = bind_role(world_main, author, d1, "authority")
        if v_d1_bind["disposition"] != "accepted":
            raise RuntimeError(f"could not bind d1: {v_d1_bind}")
        v_d1_grant = relate(world_main, author, d1, author, "acts-for", depth=0)
        check("SETUP-d1-no-redelegate-grant-accepted",
              v_d1_grant["disposition"] == "accepted",
              f"author grants d1 a depth=0 (no-redelegate) edge -- verdict={v_d1_grant}", failures)
        d2 = register(world_main, "d2", "subagent", author)
        v_d1_redelegate = relate(world_main, d1, d2, d1, "acts-for")
        check("RED-DEPTH-EXHAUSTED-refused",
              v_d1_redelegate["disposition"] == "refused"
              and "conjunct c" in v_d1_redelegate["message"]
              and "no-redelegate" in v_d1_redelegate["message"],
              f"d1 (granted depth=0) attempts to grant d2 a further acts-for edge -- "
              f"verdict={v_d1_redelegate}", failures)

        # ---- RED-CARVEOUT-DOES-NOT-EXEMPT-ORDINARY-DELEGATION: d1 tries an ordinary (non-IV)
        # delegation again with delegation_purpose unset -- still refused, same as above (the
        # carve-out is BY TYPE, never a blanket exemption for a depth-0 principal).
        d2b = register(world_main, "d2b", "subagent", author)
        v_d1_redelegate_2 = relate(world_main, d1, d2b, d1, "dispatched-by")
        check("RED-CARVEOUT-DOES-NOT-EXEMPT-ORDINARY-DELEGATION-refused",
              v_d1_redelegate_2["disposition"] == "refused"
              and "conjunct c" in v_d1_redelegate_2["message"],
              f"d1 attempts an ORDINARY dispatched-by edge (no delegation_purpose) -- still "
              f"refused, no-redelegate is not exempted merely because the relation differs -- "
              f"verdict={v_d1_redelegate_2}", failures)

        # ---- GREEN-INDEPENDENT-VERIFICATION-CARVEOUT: d1 dispatches an INDEPENDENT VERIFIER ----
        d1_reviewer = register(world_main, "d1-reviewer", "subagent", author)
        v_iv_dispatch = relate(world_main, d1, d1_reviewer, d1, "dispatched-by",
                                purpose="independent-verification")
        check("GREEN-INDEPENDENT-VERIFICATION-CARVEOUT-accepted",
              v_iv_dispatch["disposition"] == "accepted",
              f"d1 (depth=0, no-redelegate) dispatches an independent-verification-purposed "
              f"edge -- ACCEPTED despite exhausted redelegate budget (the row-1420 carve-out, "
              f"exempt BY TYPE, still requires d1's own chain-to-genesis, which holds) -- "
              f"verdict={v_iv_dispatch}", failures)

        # ---- RED-DEPTH-SECOND-HOP: D6 (depth=1) grants D7 (accepted); D7's OWN budget is now 0
        d6 = register(world_main, "d6", "subagent", author)
        v_d6_bind = bind_role(world_main, author, d6, "authority")
        if v_d6_bind["disposition"] != "accepted":
            raise RuntimeError(f"could not bind d6: {v_d6_bind}")
        v_d6_grant = relate(world_main, author, d6, author, "acts-for", depth=1)
        if v_d6_grant["disposition"] != "accepted":
            raise RuntimeError(f"author could not grant d6 depth=1: {v_d6_grant}")
        d7 = register(world_main, "d7", "subagent", author)
        v_d6_grants_d7 = relate(world_main, d6, d7, d6, "acts-for")
        check("GREEN-DEPTH-WITHIN-BUDGET-accepted",
              v_d6_grants_d7["disposition"] == "accepted",
              f"d6 (depth=1 budget) grants d7 a further acts-for edge -- ACCEPTED, one hop "
              f"consumed -- verdict={v_d6_grants_d7}", failures)
        d_deep = register(world_main, "d-deep", "subagent", author)
        v_d7_redelegate = relate(world_main, d7, d_deep, d7, "acts-for")
        check("RED-DEPTH-SECOND-HOP-refused",
              v_d7_redelegate["disposition"] == "refused"
              and "conjunct c" in v_d7_redelegate["message"],
              f"d7 (whose OWN derived budget is 1-1=0) attempts to grant d-deep a further edge "
              f"-- verdict={v_d7_redelegate}", failures)

        # ---- RED-SCOPE-OUTSIDE-GRANT / GREEN-SCOPE-WITHIN-GRANT ----
        d3 = register(world_main, "d3", "subagent", author)
        v_d3_bind = bind_role(world_main, author, d3, "authority")
        if v_d3_bind["disposition"] != "accepted":
            raise RuntimeError(f"could not bind d3: {v_d3_bind}")
        v_d3_grant = relate(world_main, author, d3, author, "acts-for",
                             scope=["principal_role_bound"])
        if v_d3_grant["disposition"] != "accepted":
            raise RuntimeError(f"author could not grant d3 a scoped edge: {v_d3_grant}")
        v_d3_outside = act_registered(world_main, d3, d3)
        check("RED-SCOPE-OUTSIDE-GRANT-refused",
              v_d3_outside["disposition"] == "refused" and "conjunct b" in v_d3_outside["message"],
              f"d3 (edge scoped to ['principal_role_bound'] only) attempts principal_registered "
              f"-- verdict={v_d3_outside}", failures)
        d3_target = register(world_main, "d3-target", "subagent", author)
        v_d3_inside = bind_role(world_main, d3, d3_target, "some-other-role")
        check("GREEN-SCOPE-WITHIN-GRANT-accepted",
              v_d3_inside["disposition"] == "accepted",
              f"d3 performs principal_role_bound (the ONE class its edge scopes) -- "
              f"verdict={v_d3_inside}", failures)

        # ---- RED-EXPIRED-EDGE ----
        d4 = register(world_main, "d4", "subagent", author)
        v_d4_bind = bind_role(world_main, author, d4, "authority")
        if v_d4_bind["disposition"] != "accepted":
            raise RuntimeError(f"could not bind d4: {v_d4_bind}")
        v_d4_grant = relate(world_main, author, d4, author, "acts-for",
                             expiry="2000-01-01T00:00:00Z")
        if v_d4_grant["disposition"] != "accepted":
            raise RuntimeError(f"author could not grant d4 an already-expired edge: {v_d4_grant}")
        v_d4_act = act_registered(world_main, d4, d4)
        check("RED-EXPIRED-EDGE-refused",
              v_d4_act["disposition"] == "refused" and "conjunct b" in v_d4_act["message"],
              f"d4 (edge expired 2000-01-01) attempts principal_registered -- "
              f"verdict={v_d4_act}", failures)

        # ---- MUST-COUNTERSIGN legs: D5's edge requires countersign by C ----
        c_signer = register(world_main, "c-signer", "subagent", author)
        d5 = register(world_main, "d5", "subagent", author)
        v_d5_bind = bind_role(world_main, author, d5, "authority")
        if v_d5_bind["disposition"] != "accepted":
            raise RuntimeError(f"could not bind d5: {v_d5_bind}")
        v_d5_grant = relate(world_main, author, d5, author, "acts-for", must_countersign=c_signer)
        if v_d5_grant["disposition"] != "accepted":
            raise RuntimeError(f"author could not grant d5 a must-countersign edge: {v_d5_grant}")

        v_d5_no_witness = act_registered(world_main, d5, d5)
        check("RED-COUNTERSIGN-MISSING-refused",
              v_d5_no_witness["disposition"] == "refused"
              and "conjunct d" in v_d5_no_witness["message"],
              f"d5 (edge requires countersign by c-signer) attempts principal_registered with NO "
              f"signature_symmetry_witness -- verdict={v_d5_no_witness}", failures)

        commission_id = open_commission(world_main, author, "s64 fixture: commission for the "
                                                              "wrong-signer/correct-signer legs")
        wrong_signer = register(world_main, "wrong-signer", "subagent", author)
        wrong_att = attest_commission(world_main, wrong_signer, commission_id, "A" * 40)
        v_d5_wrong = act_registered(world_main, d5, d5, witness=wrong_att)
        check("RED-COUNTERSIGN-WRONG-SIGNER-refused",
              v_d5_wrong["disposition"] == "refused" and "conjunct d" in v_d5_wrong["message"],
              f"d5 retries citing an attestation by wrong-signer (not c-signer) -- "
              f"verdict={v_d5_wrong}", failures)

        correct_att = attest_commission(world_main, c_signer, commission_id, "B" * 40)
        v_d5_correct = act_registered(world_main, d5, d5, witness=correct_att)
        check("GREEN-COUNTERSIGN-SATISFIED-accepted",
              v_d5_correct["disposition"] == "accepted",
              f"d5 retries citing c-signer's OWN attestation -- verdict={v_d5_correct}", failures)

        # ---- RED-COUNTERSIGN-MULTI-UNSATISFIABLE ----
        c_signer2 = register(world_main, "c-signer2", "subagent", author)
        d_multi = register(world_main, "d-multi", "subagent", author)
        v_dm_bind = bind_role(world_main, author, d_multi, "authority")
        if v_dm_bind["disposition"] != "accepted":
            raise RuntimeError(f"could not bind d-multi: {v_dm_bind}")
        v_dm_grant1 = relate(world_main, author, d_multi, author, "acts-for",
                              must_countersign=c_signer)
        if v_dm_grant1["disposition"] != "accepted":
            raise RuntimeError(f"author could not grant d-multi first edge: {v_dm_grant1}")
        d_multi_mid = register(world_main, "d-multi-mid", "subagent", author)
        # d_multi's OWN act (granting the second edge) is ITSELF a delegation_lifecycle act by
        # actor=d_multi, whose OWN inbound edge (from author) requires countersign by c_signer --
        # satisfied here so the interesting refusal (below) is about d_multi_mid's STACKED
        # requirement, not merely d_multi's own unsatisfied first-hop one.
        dm_commission = open_commission(world_main, author,
                                         "s64 fixture: commission for d-multi's own countersign")
        dm_att = attest_commission(world_main, c_signer, dm_commission, "C" * 40)
        v_dm_grant2 = relate(world_main, d_multi, d_multi_mid, d_multi, "acts-for",
                              must_countersign=c_signer2, witness=dm_att)
        check("SETUP-d-multi-second-edge-accepted",
              v_dm_grant2["disposition"] == "accepted",
              f"d-multi grants d-multi-mid a SECOND acts-for edge requiring a DIFFERENT "
              f"countersigner (c-signer2) -- verdict={v_dm_grant2}", failures)
        v_dm_bind2 = bind_role(world_main, author, d_multi_mid, "authority")
        v_dm_act = act_registered(world_main, d_multi_mid, d_multi_mid)
        check("RED-COUNTERSIGN-MULTI-UNSATISFIABLE-refused",
              v_dm_act["disposition"] == "refused"
              and "conjunct d" in v_dm_act["message"]
              and "MORE THAN ONE" in v_dm_act["message"],
              f"d-multi-mid's chain carries two must-countersign edges naming DIFFERENT "
              f"principals (c-signer, c-signer2) -- unconditionally refused, the documented "
              f"single-witness-column LIMIT -- verdict={v_dm_act}", failures)

        # ---- GREEN-s60-s62-FAMILY-UNCHANGED: a plain, condition-free grant + act ----
        plain_delegate = register(world_main, "plain-delegate", "subagent", author)
        v_plain_bind = bind_role(world_main, author, plain_delegate, "authority")
        if v_plain_bind["disposition"] != "accepted":
            raise RuntimeError(f"could not bind plain-delegate: {v_plain_bind}")
        v_plain_grant = relate(world_main, author, plain_delegate, author, "acts-for")
        v_plain_act = act_registered(world_main, plain_delegate, plain_delegate)
        check("GREEN-s60-s62-FAMILY-UNCHANGED-accepted",
              v_plain_grant["disposition"] == "accepted"
              and v_plain_act["disposition"] == "accepted",
              f"a plain acts-for grant (NO delegation conditions) + an ordinary authority-"
              f"bearing act through it -- both ACCEPTED, proving the vacuous-conjunction claim "
              f"-- grant={v_plain_grant}, act={v_plain_act}", failures)

        # ---- ZERO-FRICTION-BIRTH ----
        print(f"== scaffolding classic world {world_birth} (chain ends {CHAIN_S64[-1]}, fresh birth) ==")
        wb = scaffold_classic(world_birth, CHAIN_S64)
        tmps.append(wb.parent)
        author_birth = birth_via_boundary(world_birth)
        s60_birth(world_birth, author_birth)
        v_relation_rows = psql_tuples(
            f"SELECT count(*) FROM {world_birth}.ledger_current "
            f"WHERE kind='principal_relation_asserted';")
        check("ZERO-FRICTION-BIRTH-no-relation-rows",
              v_relation_rows == "0",
              f"a fresh world's own s40/s43/s60 birth sequence writes NO "
              f"principal_relation_asserted row -- count={v_relation_rows}", failures)

        # ---- GREEN: zero-friction ordinary-act verdict shape, byte-compared vs a pre-s60 world
        print(f"== scaffolding classic world {world_pre} (chain ends {CHAIN_S59[-1]}, NO s60..s64) ==")
        wp = scaffold_classic(world_pre, CHAIN_S59)
        tmps.append(wp.parent)
        author_pre = birth_via_boundary(world_pre)
        v_pre = bw_call(world_pre, "ledger_write", {
            "kind": "decision", "statement": "an ordinary decision row, pre-s60..s64",
            "actor": author_pre})
        v_post = bw_call(world_birth, "ledger_write", {
            "kind": "decision", "statement": "an ordinary decision row, post-s64-birth",
            "actor": author_birth})
        check("GREEN-ordinary-act-verdict-shape",
              (v_pre["disposition"], v_pre["sqlstate"], v_pre["message"])
              == (v_post["disposition"], v_post["sqlstate"], v_post["message"]) == ("accepted", None, None),
              f"an ordinary (non-gated) kind's verdict shape is IDENTICAL pre-s60..s64 vs "
              f"post-s64-birth: pre={v_pre}, post={v_post}", failures)

        # ---- AGREE-scoped: SQL 2-arg reaches_genesis vs ASP reaches_genesis_scoped/2 ----
        os.environ["LEDGER_DB"] = PGDB
        os.environ["LEDGER_SCHEMA"] = world_main
        os.environ["LEDGER_KERN"] = f"{world_main}_kernel"
        os.environ.setdefault("EPISTEMIC_PGHOST", PGHOST)
        act_classes = (
            "principal_registered", "principal_role_bound", "standing_lifecycle",
            "milestone_closure", "gate_edge_supersession", "entitlement_class_configured",
            "delegation_lifecycle", "independent_verification_delegation")
        try:
            exp = ledger_edb.export_entitlement("s64-fixture-oneoff")
            edb_text = exp.edb_text()
            clingo = sh(["clingo", str(ENGINE / "lp" / "ledger_tnow.lp"),
                        str(ENGINE / "lp" / "ledger_entitlement.lp"), "/dev/stdin", "0"],
                       input=edb_text)
            print(f"  [clingo raw stdout]\n{clingo.stdout}\n  [clingo raw stderr]\n{clingo.stderr}\n")
            asp_scoped: set[tuple[str, str]] = set()
            for line in clingo.stdout.splitlines():
                if line.startswith("Answer"):
                    continue
                for tok in line.split():
                    if tok.startswith("reaches_genesis_scoped(") and tok.endswith(")"):
                        inner = tok[len("reaches_genesis_scoped("):-1]
                        pid_s, cls_q = inner.split(",", 1)
                        cls = cls_q.strip('"')
                        asp_scoped.add((pid_s, cls))
            all_pids = psql_tuples(f"SELECT id FROM {world_main}_kernel.principal ORDER BY id;").splitlines()
            sql_scoped: set[tuple[str, str]] = set()
            for pid in all_pids:
                for cls in act_classes:
                    r = psql_tuples(
                        f"SELECT {world_main}.principal_authority_chain_reaches_genesis_scoped"
                        f"({pid}, '{cls}');")
                    if r == "t":
                        sql_scoped.add((pid, cls))
            check("AGREE-scoped-sql-asp-differential",
                  asp_scoped == sql_scoped,
                  f"SQL principal_authority_chain_reaches_genesis_scoped(pid,act_class) vs ASP "
                  f"reaches_genesis_scoped/2, per registered principal x per act-class token, "
                  f"on the post-mutation snapshot: "
                  f"symmetric_difference={sorted(asp_scoped ^ sql_scoped)}", failures)
        except ledger_edb.CapabilityError as e:
            check("AGREE-scoped-sql-asp-differential", False,
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
