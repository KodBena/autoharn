#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s62-delegation-lifecycle-gating.sql
(design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1 AMENDMENT, 2026-07-26, ledger row 1385). Real
infra, no mocks: a CLASSIC scaffold + manual chain apply (s15..s60..s62) in the TOY db, torn down
before AND after. Modeled directly on seen-red/s60-entitlement-enforcement/run_fixtures.py (same
helpers, same both-polarity discipline) -- s62 is s60's own SEVENTH act class, not a new
mechanism.

Per row 1385's own commission, RED FIRST -- the headline is THE ATTACK ITSELF:
  RED-ATTACK  -- a chainless principal, refused on conjunct (b) for an ordinary authority-bearing
                 act (mirroring s60's own RED-2), attempts the PRE-s62 bypass: self-asserting an
                 acts-for edge to an already-chained principal. Under s60 alone this SUCCEEDED
                 (nothing gated principal_relation_asserted). Under s62 it is REFUSED -- the
                 write is now itself classified 'delegation_lifecycle', authority-bearing, and
                 the attacker's own chain does not reach genesis either. The refusal's remedy
                 text is checked for the ROW 1385 CORRECTION (names the DELEGATOR, not the
                 attacker themselves) and the ABSENCE of s60's own bypass-teaching phrasing.
  RED-ATTACK-STILL-BLOCKED -- after the failed self-assertion, the attacker's ORIGINAL
                 authority-bearing act is retried and STILL refused (no chain was ever
                 established -- the bypass produced no side effect).
  GREEN-DELEGATOR-WRITES-EDGE -- the delegator (chain-connected) writes the SAME edge on the
                 attacker's behalf -- ACCEPTED -- and the attacker's NEXT authority-bearing act
                 now PASSES (the legitimate path this delta must not close).
  RED-SUPERSESSION-WRONG-RELATION -- FIX-ROUND HEADLINE (fresh-context review BLOCKS MERGE
                 finding, 2026-07-26, reviewer-witnessed live): a CHAINLESS AND ROLELESS third
                 party (never bound any role) writes {kind: principal_relation_asserted,
                 principal_relation: 'dispatched-by', supersedes: <live acts-for edge id>}. The
                 candidate row's OWN relation is not 'acts-for', so the pre-fix classifier
                 (reading only the candidate row) returned NULL and let the write through with
                 ZERO entitlement check, severing the target's delegation edge -- full
                 sabotage/DoS on the authority graph. Post-fix, the classifier ALSO reads the
                 TARGET row's own principal_relation (s45 does not enforce value-continuity
                 across a supersession for the s41 relation kinds, so the candidate's claimed
                 relation cannot be trusted alone) -- REFUSED, and a follow-up act through the
                 SAME edge proves no side effect occurred.
  RED-CROSS-KIND-WORK-DEPENDS-ON -- ROUND-2 HEADLINE (SECOND fresh-context re-review, ledger row
                 1403, reviewer-witnessed live): round 1's own fix was itself too narrow -- it
                 special-cased exactly ONE candidate kind (principal_relation_asserted) reading
                 ONE target attribute. A chainless AND roleless saboteur opens an ordinary
                 work_opened item (never gated), then writes a work_depends_on row (a THIRD,
                 completely different candidate kind, never touched by round 1's fix at all)
                 whose supersedes names the SAME live acts-for edge. Pre-round-2,
                 entitlement_act_class_of's work_depends_on branch read only the target's
                 edge_type looking for 'blocks-start'; a principal_relation_asserted target's
                 edge_type is always NULL -- falls through, ungated, ACCEPTED, edge severed.
                 Post-round-2, entitlement_act_class_of_target classifies the TARGET row
                 independently of what KIND the candidate is -- REFUSED.
  RED-CROSS-KIND-ROLE-BINDING -- the SAME vessel shape aimed at a DIFFERENT gated target class
                 (principal_role_bound, not delegation_lifecycle/acts-for) -- proves the round-2
                 fix is general over the TARGET's class, not a second special case bolted onto
                 the first.
  RED-SUPERSESSION-UNAUTHORIZED -- an actor with no chain attempts to supersede (retract) the
                 now-live edge -- REFUSED (conjunct b, same act class).
  GREEN-SUPERSESSION-BY-DELEGATOR -- the delegator (root-chained) supersedes the SAME edge --
                 ACCEPTED -- the maintainer's own "what about revocation?" question (row 1385's
                 own origin) answered mechanically: the edge dies, and a further act by the
                 formerly-delegated principal, through THAT edge alone, is refused again (I5-style
                 prospective severance, re-derived fresh, not retroactive).
  GREEN-s60-FAMILY-UNCHANGED -- s60's own RED-1/RED-2/RED-3/GREEN legs, replayed VERBATIM against
                 a world whose chain now includes s62 -- the additivity proof (a delta that only
                 widens conjunct (b)'s reach and corrects a string must not perturb any
                 pre-existing s60 behavior).
  ZERO-FRICTION-BIRTH -- a fresh classic scaffold's s40/s43/s60 birth sequence completes
                 unaffected (s62 adds no birth act of its own, kernel/lineage/
                 s62-delegation-lifecycle-gating.sql Element 3 -- the birth sequence never writes
                 a principal_relation_asserted row, so this gate never fires during birth).
  AGREE       -- the SQL/ASP differential (principal_authority_chain_reaches_genesis vs
                 reaches_genesis/1) on the post-delegation, post-supersession snapshot -- the
                 shape most likely to disagree if either side drifts (mirrors s60's own AGREE
                 leg, taken on the RICHEST chain-mutation snapshot this fixture builds).

Each check() names the witness that would show it false. Usage:
    python3 seen-red/s62-delegation-lifecycle-gating/run_fixtures.py
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
CHAIN_S62 = CHAIN_S60 + ["s62-delegation-lifecycle-gating.sql"]


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
                                "purpose": "s62 fixture's own write-boundary registration"}),
    ]:
        v = bw_call(world, fn, payload)
        if v["disposition"] != "accepted":
            raise RuntimeError(f"birth act refused: {v}")
    return author


def s60_birth(world: str, author: str) -> None:
    """The two s60 birth acts, replayed verbatim (s62 adds no birth act of its own -- Element 3):
    bind author to role 'authority', then configure the default act-class map (five classes,
    UNCHANGED by s62 -- delegation_lifecycle is deliberately not in the default map)."""
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
        "purpose": f"s62 fixture principal {name}"})
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


def supersede_acts_for(world: str, actor: str, subject: str, obj: str, old_id: str) -> dict:
    return bw_call(world, "ledger_write", {
        "kind": "principal_relation_asserted", "actor": actor,
        "statement": f"retracting {subject} acts-for {obj} (supersedes row {old_id})",
        "principal_subject": subject, "principal_object": obj,
        "principal_relation": "acts-for", "principal_binding_active": "false",
        "supersedes": old_id})


def supersede_with_relation(world: str, actor: str, subject: str, obj: str, relation: str,
                             old_id: str) -> dict:
    """The fix-round attack shape (fresh-context review finding, 2026-07-26): a superseding row
    naming a DIFFERENT principal_relation than its target (s45 does not enforce value-continuity
    across a supersession for the s41 relation kinds, kernel/lineage/
    s45-standing-lifecycle.sql lines ~135-163) -- exercises whether the classifier reads the
    TARGET's own relation, not just the candidate row's own claimed relation."""
    return bw_call(world, "ledger_write", {
        "kind": "principal_relation_asserted", "actor": actor,
        "statement": f"{subject} {relation} {obj} (claims to supersede row {old_id})",
        "principal_subject": subject, "principal_object": obj,
        "principal_relation": relation, "principal_binding_active": "false",
        "supersedes": old_id})


def bind_role(world: str, actor: str, subject: str, role_name: str) -> dict:
    return bw_call(world, "ledger_write", {
        "kind": "principal_role_bound", "actor": actor,
        "statement": f"{subject} bound to role {role_name}",
        "principal_subject": subject, "principal_role_name": role_name,
        "principal_binding_active": "true"})


def open_work(world: str, actor: str, slug: str, title: str) -> dict:
    return bw_call(world, "ledger_write", {
        "kind": "work_opened", "actor": actor, "work_slug": slug, "work_title": title,
        "statement": f"open {slug} (s62 round-2 fixture)"})


def depends_on_supersede(world: str, actor: str, work_slug: str, antecedent_slug: str,
                          old_id: str) -> dict:
    """ROUND-2 FIX ATTACK SHAPE (row 1403, the reviewer's exact witnessed vessel): a
    work_depends_on row whose OWN candidate class is unconditionally NULL for any target that is
    not itself a live blocks-start edge (entitlement_act_class_of's work_depends_on branch reads
    ONLY the target's edge_type, never any other class) -- edge_type is left NULL/'informs' here
    (not subject to any DAG cycle refusal, s39's own disclosed exemption), so the ONLY thing that
    makes this write interesting is `supersedes`, aimed at some OTHER kind's live gated row."""
    return bw_call(world, "ledger_write", {
        "kind": "work_depends_on", "actor": actor, "work_slug": work_slug,
        "work_depends_on": antecedent_slug,
        "statement": f"{work_slug} informs {antecedent_slug} (claims to supersede row {old_id})",
        "supersedes": old_id})


def main() -> int:  # noqa: C901 -- one straight-line witness script, matching s60's own shape
    failures: list[str] = []
    tmps: list[Path] = []
    world_main, world_pre, world_birth = "s62fxmain", "s62fxpre", "s62fxbirth"
    for w in (world_main, world_pre, world_birth):
        teardown(w)
    try:
        # ================= MAIN world (chain s15..s60..s62) =================
        print(f"== scaffolding classic world {world_main} (chain ends {CHAIN_S62[-1]}) ==")
        wm = scaffold_classic(world_main, CHAIN_S62)
        tmps.append(wm.parent)
        author = birth_via_boundary(world_main)
        s60_birth(world_main, author)

        # ---- setup for the headline attack: a chainless-but-role-bound attacker ----
        attacker = register(world_main, "attacker", "subagent", author)
        v_bind_attacker = bind_role(world_main, author, attacker, "authority")
        if v_bind_attacker["disposition"] != "accepted":
            raise RuntimeError(f"could not bind attacker's role: {v_bind_attacker}")
        role_binding_row_id = v_bind_attacker.get("row_id")
        v_pre_attack = bw_call(world_main, "registration_write", {
            "name": "attacker-victim-pre", "agent_class": "subagent", "actor": attacker,
            "purpose": "attacker's ORIGINAL act, chainless -- must be refused (conjunct b)"})
        check("SETUP-attacker-chainless-refused",
              v_pre_attack["disposition"] == "refused" and "conjunct b" in v_pre_attack["message"],
              f"attacker (role bound, no chain) attempts an authority-bearing act before any "
              f"delegation attempt -- verdict={v_pre_attack}", failures)

        # ---- RED-ATTACK: the headline -- the OLD bypass attempt, now refused ----
        v_bypass = acts_for(world_main, attacker, attacker, author)
        old_text_present = "your-principal-name" in (v_bypass.get("message") or "") or \
            "<your-principal-name> acts-for" in (v_bypass.get("message") or "")
        check("RED-ATTACK-self-assert-bypass-refused",
              v_bypass["disposition"] == "refused"
              and "conjunct b" in v_bypass["message"]
              and "delegation_lifecycle" in v_bypass["message"]
              and "DELEGATOR" in v_bypass["message"]
              and not old_text_present,
              f"attacker (chainless) self-asserts 'attacker acts-for author' as their OWN actor "
              f"-- the pre-s62 bypass s60's own remedy text taught -- verdict={v_bypass}",
              failures)

        # ---- RED-ATTACK-STILL-BLOCKED: the bypass produced no side effect ----
        v_post_attack = bw_call(world_main, "registration_write", {
            "name": "attacker-victim-post", "agent_class": "subagent", "actor": attacker,
            "purpose": "attacker's original act, retried after the failed bypass -- still refused"})
        check("RED-ATTACK-STILL-BLOCKED",
              v_post_attack["disposition"] == "refused" and "conjunct b" in v_post_attack["message"],
              f"attacker retries the ORIGINAL authority-bearing act after the failed self-assert "
              f"-- still refused, no chain was ever established -- verdict={v_post_attack}",
              failures)

        # ---- GREEN-DELEGATOR-WRITES-EDGE: the legitimate path ----
        v_legit = acts_for(world_main, author, attacker, author)
        check("GREEN-DELEGATOR-WRITES-EDGE",
              v_legit["disposition"] == "accepted",
              f"the DELEGATOR (author, genesis-chained) writes the SAME edge on attacker's "
              f"behalf -- verdict={v_legit}", failures)
        edge_row_id = v_legit.get("row_id")

        v_now_chained = bw_call(world_main, "registration_write", {
            "name": "attacker-victim-chained", "agent_class": "subagent", "actor": attacker,
            "purpose": "attacker's NEXT act, now chained through the delegator-written edge"})
        check("GREEN-attacker-next-act-accepted",
              v_now_chained["disposition"] == "accepted",
              f"attacker's next authority-bearing act, through the legitimately-written chain "
              f"-- verdict={v_now_chained}", failures)

        # ---- RED-SUPERSESSION-WRONG-RELATION: the fix-round headline attack (fresh-context
        # review BLOCKS MERGE finding, 2026-07-26) -- a CHAINLESS AND ROLELESS third party
        # (no bind_role call at all, unlike attacker/outsider above) writes a
        # principal_relation_asserted row naming a DIFFERENT relation ('dispatched-by', never
        # 'acts-for') while supersedes points at the live acts-for edge. Pre-fix, the classifier
        # read only the CANDIDATE row's own principal_relation, returned NULL for 'dispatched-by',
        # and let the write through ungated -- severing the edge with zero entitlement check.
        # Post-fix, the classifier also reads the TARGET row's principal_relation (mirroring the
        # sibling gate_edge_supersession branch) and classifies this row 'delegation_lifecycle'
        # regardless of what relation it itself claims -- REFUSED.
        saboteur = register(world_main, "saboteur", "subagent", author)
        v_wrong_relation = supersede_with_relation(
            world_main, saboteur, attacker, author, "dispatched-by", edge_row_id) \
            if edge_row_id else {"disposition": "error", "message": "no edge_row_id"}
        check("RED-SUPERSESSION-WRONG-RELATION-refused",
              v_wrong_relation["disposition"] == "refused"
              and "conjunct b" in v_wrong_relation["message"]
              and "delegation_lifecycle" in v_wrong_relation["message"],
              f"saboteur (CHAINLESS, ROLELESS -- no role ever bound) supersedes the live "
              f"acts-for edge with a row claiming relation 'dispatched-by' -- the pre-fix "
              f"classifier read only the candidate's own relation and returned NULL for this "
              f"row, ungating it entirely -- verdict={v_wrong_relation}", failures)

        v_edge_survived = bw_call(world_main, "registration_write", {
            "name": "attacker-victim-post-sabotage", "agent_class": "subagent", "actor": attacker,
            "purpose": "attacker's act after the blocked sabotage attempt -- the edge must "
                       "still be live, proving the refused write had no side effect"})
        check("RED-SUPERSESSION-WRONG-RELATION-no-side-effect",
              v_edge_survived["disposition"] == "accepted",
              f"attacker's authority-bearing act, through the SAME edge, immediately after the "
              f"blocked sabotage attempt -- the edge was never severed -- verdict={v_edge_survived}",
              failures)

        # ---- RED-CROSS-KIND-WORK-DEPENDS-ON: the SECOND round-2 headline (ledger row 1403,
        # reviewer-witnessed live) -- a CHAINLESS AND ROLELESS saboteur, using a COMPLETELY
        # DIFFERENT candidate KIND this time (work_depends_on, never mentioned by round 1's fix
        # at all), opens an ordinary work item then writes a work_depends_on row whose supersedes
        # names the SAME live acts-for edge. Pre-round-2, entitlement_act_class_of's
        # work_depends_on branch read ONLY the target's edge_type (looking for 'blocks-start');
        # the target here is a principal_relation_asserted row, edge_type NULL, never
        # 'blocks-start' -- falls through to RETURN NULL, ungated, ACCEPTED, the edge severed.
        # Post-round-2, entitlement_act_class_of_target independently classifies the TARGET
        # (principal_relation_asserted, relation acts-for) as 'delegation_lifecycle' REGARDLESS
        # of the candidate's own (work_depends_on, unclassified) kind -- REFUSED.
        cross_kind_saboteur = register(world_main, "cross-kind-saboteur", "subagent", author)
        v_open_own_item = open_work(world_main, cross_kind_saboteur, "xk-item-a", "xk item a")
        v_open_own_item_b = open_work(world_main, cross_kind_saboteur, "xk-item-b", "xk item b")
        if v_open_own_item["disposition"] != "accepted" or v_open_own_item_b["disposition"] != "accepted":
            raise RuntimeError(f"cross-kind saboteur could not even open ordinary work items "
                                f"(work_opened is NEVER gated) -- {v_open_own_item} {v_open_own_item_b}")
        v_cross_kind_wdo = depends_on_supersede(
            world_main, cross_kind_saboteur, "xk-item-a", "xk-item-b", edge_row_id) \
            if edge_row_id else {"disposition": "error", "message": "no edge_row_id"}
        check("RED-CROSS-KIND-WORK-DEPENDS-ON-refused",
              v_cross_kind_wdo["disposition"] == "refused"
              and "conjunct b" in v_cross_kind_wdo["message"]
              and "delegation_lifecycle" in v_cross_kind_wdo["message"],
              f"cross-kind saboteur (CHAINLESS, ROLELESS, and using a work_depends_on candidate "
              f"kind entitlement_act_class_of never links to delegation_lifecycle at all) "
              f"supersedes the live acts-for edge -- verdict={v_cross_kind_wdo}", failures)

        v_edge_survived_2 = bw_call(world_main, "registration_write", {
            "name": "attacker-victim-post-cross-kind", "agent_class": "subagent", "actor": attacker,
            "purpose": "attacker's act after the blocked cross-kind sabotage attempt -- the edge "
                       "must still be live"})
        check("RED-CROSS-KIND-WORK-DEPENDS-ON-no-side-effect",
              v_edge_survived_2["disposition"] == "accepted",
              f"attacker's authority-bearing act, through the SAME edge, immediately after the "
              f"blocked cross-kind sabotage attempt -- verdict={v_edge_survived_2}", failures)

        # ---- RED-CROSS-KIND-ROLE-BINDING: the SAME vessel shape (work_depends_on candidate,
        # never itself classified, chainless/roleless writer) aimed at a DIFFERENT gated target
        # CLASS entirely -- attacker's own principal_role_bound row (role 'authority'), never an
        # acts-for edge. Proves the fix is general over TARGET CLASS, not special-cased to
        # delegation_lifecycle/acts-for the way both round-1's fix and the reviewer's own named
        # attack specimen were.
        v_cross_kind_role = depends_on_supersede(
            world_main, cross_kind_saboteur, "xk-item-b", "xk-item-a", role_binding_row_id) \
            if role_binding_row_id else {"disposition": "error", "message": "no role_binding_row_id"}
        check("RED-CROSS-KIND-ROLE-BINDING-refused",
              v_cross_kind_role["disposition"] == "refused"
              and "conjunct a" in v_cross_kind_role["message"]
              and "principal_role_bound" in v_cross_kind_role["message"],
              f"cross-kind saboteur (holds NO role at all, unlike the acts-for-edge saboteurs "
              f"above) supersedes attacker's OWN LIVE principal_role_bound row (role "
              f"'authority') via a work_depends_on candidate -- refused on conjunct a (no role "
              f"binding at all) before conjunct b is even reached, since entitlement_enforce_class "
              f"checks (a) before (b) -- verdict={v_cross_kind_role}",
              failures)

        v_role_binding_survived = bw_call(world_main, "registration_write", {
            "name": "attacker-victim-post-role-sabotage", "agent_class": "subagent", "actor": attacker,
            "purpose": "attacker's act after the blocked role-binding sabotage attempt -- the "
                       "role binding (conjunct a) must still be intact, proving no side effect"})
        check("RED-CROSS-KIND-ROLE-BINDING-no-side-effect",
              v_role_binding_survived["disposition"] == "accepted",
              f"attacker's authority-bearing act (requires role ''authority'' AND chain) "
              f"immediately after the blocked role-binding sabotage attempt -- the role binding "
              f"was never severed -- verdict={v_role_binding_survived}", failures)

        # ---- GREEN-CROSS-KIND-TARGET-SUPERSESSION-BY-ENTITLED-ACTOR: the round-2 mechanism must
        # not falsely refuse a PROPERLY ENTITLED actor -- author (role ''authority'' + genesis
        # chain, satisfying every one of the five default-mapped classes) supersedes a
        # DISPOSABLE role-binding target (bound fresh here, not reused by any later leg, so this
        # leg's own side effect cannot perturb any check downstream) via the SAME cross-kind
        # work_depends_on vessel shape RED-CROSS-KIND-ROLE-BINDING used -- ACCEPTED, proving the
        # new target-class conjunct gates on ENTITLEMENT, not merely on "is this a cross-kind
        # write" (a naive implementation that refused ALL cross-kind supersession of a gated
        # target, entitled or not, would ALSO pass every RED leg above but would be a correctness
        # regression on ordinary legitimate use -- this leg is what would catch that).
        green_party = register(world_main, "green-party", "subagent", author)
        v_green_bind = bind_role(world_main, author, green_party, "authority")
        if v_green_bind["disposition"] != "accepted":
            raise RuntimeError(f"could not bind green-party's role: {v_green_bind}")
        green_role_row_id = v_green_bind.get("row_id")
        v_green_open = open_work(world_main, author, "xk-item-c", "xk item c")
        if v_green_open["disposition"] != "accepted":
            raise RuntimeError(f"author could not open ordinary work item: {v_green_open}")
        v_green_supersede = depends_on_supersede(
            world_main, author, "xk-item-c", "xk-item-a", green_role_row_id) \
            if green_role_row_id else {"disposition": "error", "message": "no green_role_row_id"}
        check("GREEN-CROSS-KIND-TARGET-SUPERSESSION-BY-ENTITLED-ACTOR",
              v_green_supersede["disposition"] == "accepted",
              f"author (properly entitled for principal_role_bound: role ''authority'' + "
              f"genesis chain) supersedes green-party's disposable role-binding row via the "
              f"SAME cross-kind work_depends_on vessel shape the RED leg above used -- must be "
              f"ACCEPTED, not refused merely for being cross-kind -- verdict={v_green_supersede}",
              failures)

        # ---- RED-SUPERSESSION-UNAUTHORIZED: an unchained actor tries to retract the edge ----
        outsider = register(world_main, "outsider", "subagent", author)
        v_bind_outsider = bind_role(world_main, author, outsider, "authority")
        if v_bind_outsider["disposition"] != "accepted":
            raise RuntimeError(f"could not bind outsider's role: {v_bind_outsider}")
        v_unauth_supersede = supersede_acts_for(world_main, outsider, attacker, author, edge_row_id) \
            if edge_row_id else {"disposition": "error", "message": "no edge_row_id"}
        check("RED-SUPERSESSION-UNAUTHORIZED-refused",
              v_unauth_supersede["disposition"] == "refused"
              and "conjunct b" in v_unauth_supersede["message"],
              f"outsider (role-bound, no chain) attempts to SUPERSEDE the live acts-for edge -- "
              f"verdict={v_unauth_supersede}", failures)

        # ---- GREEN-SUPERSESSION-BY-DELEGATOR: the delegator revokes their own grant ----
        v_auth_supersede = supersede_acts_for(world_main, author, attacker, author, edge_row_id) \
            if edge_row_id else {"disposition": "error", "message": "no edge_row_id"}
        check("GREEN-SUPERSESSION-BY-DELEGATOR-accepted",
              v_auth_supersede["disposition"] == "accepted",
              f"the delegator (author, genesis-chained) supersedes/retracts the SAME edge -- "
              f"verdict={v_auth_supersede}", failures)

        v_after_revoke = bw_call(world_main, "registration_write", {
            "name": "attacker-victim-post-revoke", "agent_class": "subagent", "actor": attacker,
            "purpose": "attacker's act AFTER the delegator revoked the edge -- refused again"})
        check("GREEN-revocation-severs-chain",
              v_after_revoke["disposition"] == "refused" and "conjunct b" in v_after_revoke["message"],
              f"attacker's act, after the delegator's own supersession retracted the edge -- "
              f"verdict={v_after_revoke}", failures)

        # ---- GREEN-s60-FAMILY-UNCHANGED: s60's own RED-1/2/3 + GREEN legs, replayed verbatim ----
        builder = register(world_main, "builder", "subagent", author)
        v_role_refused = bw_call(world_main, "registration_write", {
            "name": "second-victim", "agent_class": "subagent", "actor": builder,
            "purpose": "should be refused -- builder holds no role"})
        check("s60replay-RED-1-role-refusal",
              v_role_refused["disposition"] == "refused"
              and "conjunct a" in v_role_refused["message"]
              and "authority" in v_role_refused["message"],
              f"builder (registered, no role binding) attempts principal_registered -- "
              f"verdict={v_role_refused}", failures)
        refusal_id = v_role_refused.get("refusal_id")
        r_journal = psql_tuples(
            f"SELECT count(*) FROM {world_main}.ledger_current "
            f"WHERE id={refusal_id} AND kind='write_refused';") if refusal_id else "0"
        check("s60replay-RED-1-journaled",
              r_journal == "1",
              f"refusal_id={refusal_id} -- a committed write_refused row present in "
              f"ledger_current (count={r_journal})", failures)

        stranger = register(world_main, "stranger", "subagent", author)
        v_bind_stranger = bind_role(world_main, author, stranger, "authority")
        if v_bind_stranger["disposition"] != "accepted":
            raise RuntimeError(f"could not bind stranger's role: {v_bind_stranger}")
        v_chain_refused = bw_call(world_main, "registration_write", {
            "name": "stranger-victim", "agent_class": "subagent", "actor": stranger,
            "purpose": "should be refused -- stranger holds the role but no chain to genesis"})
        check("s60replay-RED-2-chain-refusal",
              v_chain_refused["disposition"] == "refused"
              and "conjunct b" in v_chain_refused["message"]
              and "genesis" in v_chain_refused["message"],
              f"stranger (role bound, NO acts-for chain) attempts principal_registered -- "
              f"verdict={v_chain_refused}", failures)

        d1 = register(world_main, "delegate1", "subagent", author)
        d2 = register(world_main, "delegate2", "subagent", author)
        for p in (d1, d2):
            v = bind_role(world_main, author, p, "authority")
            if v["disposition"] != "accepted":
                raise RuntimeError(f"could not bind delegate role: {v}")
        v_af1 = acts_for(world_main, author, d1, author)
        v_af2 = acts_for(world_main, author, d2, d1)
        if v_af1["disposition"] != "accepted" or v_af2["disposition"] != "accepted":
            raise RuntimeError(f"could not establish s60replay chain: {v_af1} {v_af2}")
        v_d2_first = bw_call(world_main, "registration_write", {
            "name": "d2-first-act", "agent_class": "subagent", "actor": d2,
            "purpose": "D2's first act, through the live chain -- should be ACCEPTED"})
        check("s60replay-RED-3-pre-suspension-accepted",
              v_d2_first["disposition"] == "accepted",
              f"D2 (chain D2->D1->author) performs an authority-bearing act -- verdict={v_d2_first}",
              failures)
        first_act_row_id = v_d2_first.get("row_id")

        v_suspend = bw_call(world_main, "ledger_write", {
            "kind": "principal_suspended", "actor": author,
            "statement": "D1 suspended -- severs D2's chain prospectively (I5 witness)",
            "principal_subject": d1, "principal_binding_active": "true"})
        if v_suspend["disposition"] != "accepted":
            raise RuntimeError(f"could not suspend D1: {v_suspend}")

        v_d2_second = bw_call(world_main, "registration_write", {
            "name": "d2-second-act", "agent_class": "subagent", "actor": d2,
            "purpose": "D2's SECOND act, chain now severed via D1 -- should be REFUSED"})
        check("s60replay-RED-3-severed-chain-refusal",
              v_d2_second["disposition"] == "refused" and "conjunct b" in v_d2_second["message"],
              f"D2's second act, after D1's suspension -- verdict={v_d2_second}", failures)

        credited_still = psql_tuples(
            f"SELECT count(*) FROM {world_main}.ledger_current WHERE id={first_act_row_id};") \
            if first_act_row_id else "0"
        check("s60replay-RED-3-I5-past-act-credited",
              credited_still == "1",
              f"D2's FIRST act (row {first_act_row_id}), written before D1's suspension, is "
              f"still present in ledger_current after the chain severed -- count={credited_still}",
              failures)

        # ---- ZERO-FRICTION-BIRTH: a fresh classic scaffold's own birth sequence, unaffected ----
        print(f"== scaffolding classic world {world_birth} (chain ends {CHAIN_S62[-1]}, fresh birth) ==")
        wb = scaffold_classic(world_birth, CHAIN_S62)
        tmps.append(wb.parent)
        author_birth = birth_via_boundary(world_birth)
        s60_birth(world_birth, author_birth)
        v_relation_rows = psql_tuples(
            f"SELECT count(*) FROM {world_birth}.ledger_current "
            f"WHERE kind='principal_relation_asserted';")
        check("ZERO-FRICTION-BIRTH-no-relation-rows",
              v_relation_rows == "0",
              f"a fresh world's own s40/s43/s60 birth sequence writes NO "
              f"principal_relation_asserted row (s62 Element 3) -- count={v_relation_rows}, "
              f"birth sequence itself completed without any s62 gate firing", failures)

        # ---- GREEN: zero-friction ordinary-act verdict shape, byte-compared vs a pre-s60 world ----
        print(f"== scaffolding classic world {world_pre} (chain ends {CHAIN_S59[-1]}, NO s60/s62) ==")
        wp = scaffold_classic(world_pre, CHAIN_S59)
        tmps.append(wp.parent)
        author_pre = birth_via_boundary(world_pre)
        v_pre = bw_call(world_pre, "ledger_write", {
            "kind": "decision", "statement": "an ordinary decision row, pre-s60/s62",
            "actor": author_pre})
        v_post = bw_call(world_birth, "ledger_write", {
            "kind": "decision", "statement": "an ordinary decision row, post-s62-birth",
            "actor": author_birth})
        check("GREEN-ordinary-act-verdict-shape",
              (v_pre["disposition"], v_pre["sqlstate"], v_pre["message"])
              == (v_post["disposition"], v_post["sqlstate"], v_post["message"]) == ("accepted", None, None),
              f"an ordinary (non-gated) kind's verdict shape is IDENTICAL pre-s60/s62 vs "
              f"post-s62-birth: pre={v_pre}, post={v_post}", failures)

        # ---- AGREE: SQL/ASP differential on the richest chain-mutation snapshot (world_main) ----
        os.environ["LEDGER_DB"] = PGDB
        os.environ["LEDGER_SCHEMA"] = world_main
        os.environ["LEDGER_KERN"] = f"{world_main}_kernel"
        os.environ.setdefault("EPISTEMIC_PGHOST", PGHOST)
        try:
            exp = ledger_edb.export_entitlement("s62-fixture-oneoff")
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
            all_pids = psql_tuples(f"SELECT id FROM {world_main}_kernel.principal ORDER BY id;").splitlines()
            sql_reaches = set()
            for pid in all_pids:
                r = psql_tuples(
                    f"SELECT {world_main}.principal_authority_chain_reaches_genesis({pid});")
                if r == "t":
                    sql_reaches.add(pid)
            check("AGREE-sql-asp-differential",
                  asp_reaches == sql_reaches,
                  f"SQL principal_authority_chain_reaches_genesis vs ASP reaches_genesis/1, "
                  f"per registered principal, on the post-delegation/post-supersession snapshot: "
                  f"SQL={sorted(sql_reaches, key=int)}, ASP={sorted(asp_reaches, key=int)}",
                  failures)
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
