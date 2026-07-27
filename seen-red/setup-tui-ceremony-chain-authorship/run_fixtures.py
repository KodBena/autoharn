#!/usr/bin/env python3
"""seen-red/setup-tui-ceremony-chain-authorship/run_fixtures.py -- both-polarity proof for work
item tui-ceremony-chain-authorship (ledger rows 1390/1391, surfaced by the s62 build f099ed0's
own header note, s62 in turn closing the self-servable-chain hole ledger row 1385 found).
Census-registered in gates/fixture_census.py.

THE DEFECT: tools/setup_tui/steps_principals_authority.py's "Principals & authority" ceremony
used to write EVERY founding act (register-principal, competence grant, relate) as
`LED_ACTOR=commissioner` (tools/setup_tui/principals_authority.py's old `_COMMISSIONER_ENV`).
'commissioner' is registered BY 'author' (the scaffold's own genesis-chained connection
principal, bootstrap/new-project.sh's s40/s43 birth sequence) for a narrow, DIFFERENT purpose
(FULL-mode commission SIGNING) and never asserts any acts-for edge of its own -- so it does not
chain-reach genesis. TWO merged/pending kernel deltas gate on exactly that:
  - kernel/lineage/s60-entitlement-enforcement.sql (MERGED, on this worktree's main already):
    `principal_registered` is ALREADY authority-bearing (conjunct a: the default act-class map
    requires role 'authority', which only 'author' holds at birth; conjunct b: chain-to-genesis)
    -- so `register_principal_act` driven as commissioner was ALREADY refused on any s60+ world,
    a hazard broader than ledger row 1390's own framing (found sweeping this file for the SAME
    defect class, CLAUDE.md's hazard-in-reach corollary -- fixed in the same pass, not routed
    around).
  - kernel/lineage/s62-delegation-lifecycle-gating.sql (UPDATE, this build: MERGED directly into
    kernel/lineage/ on main as of commit aa3abfb, past all three review rounds -- round 1 closed a
    critical supersession-classification bypass a fresh-context review found in the first cut,
    f099ed0; round 2 (row 1403) generalized that fix from one candidate kind to a general
    target-class supersession gate, via a new entitlement_act_class_of_target function and an
    entitlement_enforce_class helper applied to BOTH the candidate's own class and (when
    superseding) the target's class; round 3 is a fresh-context review that CLEARS. At THIS
    fixture's own original authoring time s62 was still branch-only (worktree-agent-
    a9b3bd5031b11cd5a, commit 680e6e2) and this fixture cherry-picked its SQL text into this
    worktree's own kernel/lineage/ via `git show 680e6e2:...`, working-tree only, at fixture-setup
    time -- S62_SRC_COMMIT below is KEPT as that historical pin, not re-pinned to a post-merge
    SHA, but the cherry-pick is now a no-op in practice: `main()`'s own `s62_precopied` check finds
    the file already committed and skips the `git show`/write/later-unlink entirely, so re-running
    this fixture against the current tree neither reads S62_SRC_COMMIT nor risks diverging from
    it -- verified live, this build's own witness run printed no "cherry-picked s62 SQL" line):
    the
    founding "orchestrator acts-for maintainer" edge (`relate_act`) is `principal_relation_
    asserted`/'acts-for', s62's own SEVENTH authority-bearing act class (delegation_lifecycle).

THE FIX (tools/setup_tui/principals_authority.py): `register_principal_act`, `grant_competence_
act`, and `relate_act` no longer force `LED_ACTOR=commissioner` -- each now leaves `LED_ACTOR`
UNSET, letting the served connection's own declared-default actor resolve (`bootstrap/templates/
led.tmpl`'s `_resolve_actor`: unset omits `actor` from the payload, the kernel's `set_actor`
resolves it from `session_user`'s own declared standing -- bound to 'author' at birth, BEFORE
this screen ever runs post re-sequencing) -- the SAME actor the scaffold's own birth sequence
already uses to register every principal, 'commissioner' included. `charter_register_act`
(writes a `decision` row, never gated) already had this shape and is unchanged -- the fix simply
brings its three siblings into line. INFORMATIONAL: this declared-default resolution to 'author'
holds absent ambient `LED_ACTOR` contamination in the operator's own environment -- like the
pre-existing `charter_register_act`, these three acts pass `env=None` through to the served
connection, so an operator shell that already has `LED_ACTOR` set to something else would see
that value win; this is not a new gap, and no new machinery (env filtering, etc.) is proposed
here.

THREE WORLDS, CLASSIC scaffold + manual chain apply (real infra, no mocks -- the same technique
seen-red/s41-principal-bindings-and-relations and seen-red/s62-delegation-lifecycle-gating (the
s62 branch's own fixture) both use), each torn down before AND after:

  WORLD S60  (chain s15..s59 + s60, NO s62) -- isolates the PRE-EXISTING, broader hazard:
    RED  -- the OLD principals_authority.py (pinned at PRE_FIX_COMMIT, this worktree's own HEAD
            before this build) drives `steps_principals_authority.submit()` (the step's real,
            UI-free core -- the "headless" driving convention seen-red/setup-tui-pure-core-
            foundation and siblings already use for step-level cores) to register a fresh
            principal 'orchestrator'; `commit_executor.execute()` runs the REAL resulting plan
            against this REAL world. REFUSED (s60 conjunct a/b, 'commissioner' holds neither role
            nor chain) -- banked verbatim.
    GREEN -- the CURRENT (fixed) principals_authority.py, identical submit() call, identical
            plan/commit path. ACCEPTED -- 'orchestrator' lands, authored by 'author'.

  WORLD S62  (chain s15..s59 + s60 + s62) -- isolates the ledger-row-1390 hazard specifically:
    'orchestrator' is pre-registered directly (bypassing the TUI's own register step, which
    WORLD S60 already proved) so the RELATE act's own actor is the only variable.
    RED  -- OLD principals_authority.py drives submit() with a relation-only answers dict
            ({'subject':'orchestrator','relation':'acts-for','object':'author'}); REFUSED (s62
            conjunct b, delegation_lifecycle) -- banked verbatim.
    GREEN -- CURRENT principals_authority.py, identical relation. ACCEPTED; the
            principal_relations view carries the edge; a SUBSEQUENT authority-bearing act
            (register-principal) run AS 'orchestrator' (a fresh, separate `<dest>/led` call, no
            TUI involved) now PASSES conjunct b through the newly-chained edge -- the "a
            subsequent authority-bearing act by the orchestrator principal passes conjunct-b
            through the new chain" witness the work item names.
    GREEN-FULL-CEREMONY -- a SECOND fresh principal ('scout'), the WHOLE ceremony in one
            submit() call (register + relate together, CURRENT code): completes end to end,
            both edges land, and 'scout' itself passes a subsequent authority-bearing act too.

  WORLD PRE  (chain s15..s59, NO s60/s62 at all -- "born before s62") -- zero-friction leg:
    GREEN-ONLY -- CURRENT (fixed) code, the SAME full ceremony (register 'orchestrator' + relate
            'orchestrator acts-for author') in one submit() call. ACCEPTED (as it always was --
            no entitlement family present at all on this chain) -- the fix introduces no
            regression on a world born before either kernel delta.

Zero mocks beyond the ONE pin (the old `principals_authority` module, loaded exactly like every
other PRE_FIX_COMMIT fixture in this family pins its own pre-fix module via `git show`). Zero
residue: every scratch schema/role dropped in `finally`, every scratch boundary_service child
(spawned by `ensure_running` on this fixture's first `<dest>/led` call) killed via its own
`.autoharn-service.pid` (the SAME mechanism seen-red/minimal-profile-tracker already uses), every
scratch directory removed. Ports: `probes.free_port(start=19420)` -- explicitly far from
8420-8620 (mirrors 8422/8433, this project's own LIVE deployment ports -- house rule, never
touched, live or free). Lazy imports banned.

Usage: python3 seen-red/setup-tui-ceremony-chain-authorship/run_fixtures.py
Exit 0 if every case matches; 1 otherwise."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LINEAGE = REPO / "kernel" / "lineage"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "tools" / "setup_tui"))

import pghost_resolve  # noqa: E402
from tools.setup_tui import probes  # noqa: E402
from tools.setup_tui import checklist as ck  # noqa: E402
from tools.setup_tui.plan import CommandAct, Plan  # noqa: E402
from tools.setup_tui import commit_executor as CE  # noqa: E402
import tools.setup_tui.steps_principals_authority as spa  # noqa: E402
from tools.setup_tui import principals_authority as pa_current  # noqa: E402

os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

# The commit immediately before this build touched tools/setup_tui/principals_authority.py --
# pinned by SHA, never HEAD (this family's own PRE_FIX_COMMIT convention, e.g.
# seen-red/setup-tui-destination-foreign-refusal).
PRE_FIX_COMMIT = "0387a5d"

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

S62_SRC_COMMIT = "680e6e2"  # branch worktree-agent-a9b3bd5031b11cd5a's own HEAD after round 3's
# fresh-context review CLEARS (round 1, commit 4b425b3, closed a critical supersession-
# classification bypass in f099ed0, the first cut; round 2, row 1403, generalized that fix from
# one candidate kind to a general target-class supersession gate) -- not yet on main, but becomes
# main-reachable at the coupled merge, so this literal SHA pin survives branch deletion; pinned by
# SHA, never HEAD/a branch ref, per this family's own convention (see module docstring).
# Cherry-picked into kernel/lineage/ (working tree only) at fixture setup time below.


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
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


def psql_raw(script: str) -> subprocess.CompletedProcess:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"],
              input=script)


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


def _write_multiplex_toml(dest: Path, world: str, host: str, db: str, schema: str, kern: str,
                           role: str) -> None:
    """The SAME shape tools/setup_tui/steps_boundary.py's own `submit()` writes -- hand-written
    here since this fixture uses CLASSIC scaffold mode (no --profile tracker auto-write)."""
    text = (f"[deployments.{world}]\npghost = \"{host}\"\npgdatabase = \"{db}\"\n"
            f"pguser = \"{role}\"\npgschema = \"{schema}\"\npgkern = \"{kern}\"\n")
    (dest / "boundary-multiplex.toml").write_text(text, encoding="utf-8")


def scaffold_classic(world: str, chain: list[str], port: int) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    schema, kern, role = world, f"{world}_kernel", f"{world}_rw"
    boundary_url = f"http://127.0.0.1:{port}"
    r = sh(["bash", str(NEW_PROJECT), str(world_dir),
            "--db", PGDB, "--host", PGHOST,
            "--schema", schema, "--kern", kern, "--role", role,
            "--name", world, "--boundary-url", boundary_url, "--boundary-deployment", world])
    if r.returncode != 0:
        raise RuntimeError(f"CLASSIC SCAFFOLD FAILED ({world}): {r.stdout[-1500:]} {r.stderr[-1500:]}")
    _write_multiplex_toml(world_dir, world, PGHOST, PGDB, schema, kern, role)
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


def birth_via_boundary(world: str) -> str:
    """The s40/s43 birth acts, hand-driven exactly as
    seen-red/s62-delegation-lifecycle-gating/run_fixtures.py's own `birth_via_boundary` does
    (CLASSIC mode runs no lineage automatically -- FULL_LINEAGE gate, bootstrap/new-project.sh --
    so this fixture, like that one, discharges the birth sequence by hand through the SAME
    SECURITY DEFINER boundary functions the real scaffold's own birth sequence calls). Also
    registers 'reviewer'/'commissioner'/'write-boundary' (actor=author, matching new-project.sh's
    own step 3/4) so 'commissioner' genuinely exists in this world, unchained, exactly as it does
    in a real deployment -- the whole point of this fixture."""
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
    ]:
        v = bw_call(world, fn, payload)
        if v["disposition"] != "accepted":
            raise RuntimeError(f"birth act refused: {v}")
    for name, agent_class, purpose in [
        ("reviewer", "subagent", "countersigns author's rows"),
        ("commissioner", "human", "FULL-mode commission signing -- NEVER the principals-authority "
                                   "ceremony actor, the exact fact this fixture proves"),
        ("write-boundary", "tool", "the kernel write boundary's own recording identity"),
    ]:
        v = bw_call(world, "registration_write",
                    {"name": name, "agent_class": agent_class, "actor": author, "purpose": purpose})
        if v["disposition"] != "accepted":
            raise RuntimeError(f"birth act (register {name}) refused: {v}")
    return author


def s60_birth(world: str, author: str) -> None:
    """The two s60 birth acts, replayed verbatim (mirrors seen-red/s62-delegation-lifecycle-
    gating's own `s60_birth`): bind author to role 'authority', configure the default act-class
    map (five classes -- 'delegation_lifecycle' deliberately NOT in the default map, s62's own
    Element 2 note)."""
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


def bind_role(world: str, actor: str, subject: str, role_name: str) -> dict:
    """Bind `subject` to `role_name`, authored by `actor` -- mirrors seen-red/s62-delegation-
    lifecycle-gating's own `bind_role` helper. Used so a subsequent-act witness exercises
    conjunct (b) (the chain this fixture's own fix is about) in isolation, without ALSO tripping
    conjunct (a) (the default act-class map's separate role requirement on 'principal_
    registered' -- a different, already-s60-gated fact this fixture is not testing here)."""
    return bw_call(world, "ledger_write", {
        "kind": "principal_role_bound", "actor": actor,
        "statement": f"{subject} bound to role {role_name} (subsequent-act witness setup)",
        "principal_subject": subject, "principal_role_name": role_name,
        "principal_binding_active": "true"})


def register_direct(world: str, name: str, agent_class: str, actor: str) -> str:
    """Register a principal directly through the boundary (bypassing the TUI entirely) --
    WORLD S62 uses this to pre-register 'orchestrator' so the relate-only cases isolate the
    relate_act defect specifically from the (already separately proven, WORLD S60) register_
    principal_act defect."""
    v = bw_call(world, "registration_write", {
        "name": name, "agent_class": agent_class, "actor": actor,
        "purpose": f"fixture principal {name}"})
    if v["disposition"] != "accepted":
        raise RuntimeError(f"registering {name} refused: {v}")
    K = f"{world}_kernel"
    return psql_tuples(f"SELECT id FROM {K}.principal WHERE name='{name}';")


def _load_pinned_principals_authority(commit: str, scratch: str):
    """The `principals_authority` module exactly as it stood at `commit` -- `git show`, executed
    in an isolated namespace, the SAME technique seen-red/setup-tui-pure-core-foundation's own
    `_load_pinned_commit_executor` and seen-red/setup-tui-rehearsal-mid-cancel's own
    `load_old_commit_pane_class` both already use.

    POST-LOAD COMPATIBILITY PATCH (found running this fixture on the post-merge tree, hazard-in-
    reach, CLAUDE.md): PRE_FIX_COMMIT predates `scaffold-umbrella-migration batch 3` (b528212),
    which changed `tools.setup_tui.runner.served_led_path`'s return type from a bare `str` to a
    2-tuple argv PREFIX (`design/FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md` §6 amendment) -- an
    UNRELATED, later, already-merged change that landed on a sibling branch and only met this
    fixture's own pin at the two branches' shared merge commit (7b89d42), never witnessed
    together before now. Because this loader re-executes the pinned file's OWN top-of-file
    `from tools.setup_tui.runner import ... served_led_path` against the CURRENT (not pinned)
    `runner.py`, the pinned module's three act-builders -- written against the OLD str contract,
    `argv = (led, "sub", ...)` -- now receive a tuple where they expect a string, and
    `CommandAct.render()` throws `TypeError: sequence item 0: expected str instance, tuple found`
    before ever reaching the entitlement gate this fixture exists to witness. That crash is pure
    argv-shape noise, not the actor-authorship defect under test (the pin's `_COMMISSIONER_ENV`
    forcing is the ONE fact this fixture isolates) -- so the three act-builders are re-bound here,
    post-load, to the SAME §6-amended splat (`argv = (*led, "sub", ...)`) every OTHER caller in
    this repo already received, while leaving `extra_env=mod._COMMISSIONER_ENV` (the actual
    defect) untouched. `charter_register_act` is not re-bound: it never forced LED_ACTOR and was
    never in this argv-shape bind to begin with (its own docstring, both at this commit and at
    HEAD, already used the pre-tuple str-`led` shape consistently with the OLD runner.py it was
    authored against -- verified by inspection of the pinned text, not assumed)."""
    src = sh(["git", "show", f"{commit}:tools/setup_tui/principals_authority.py"], cwd=str(REPO))
    assert src.returncode == 0 and src.stdout.strip(), (
        f"could not read {commit}:tools/setup_tui/principals_authority.py -- {src.stderr}")
    assert "_COMMISSIONER_ENV" in src.stdout, (
        f"fixture assumption stale: {commit}:tools/setup_tui/principals_authority.py no longer "
        f"carries _COMMISSIONER_ENV -- PRE_FIX_COMMIT needs repinning to a genuinely earlier commit")
    path = os.path.join(scratch, "principals_authority_prefix.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(src.stdout)
    spec = importlib.util.spec_from_file_location("principals_authority_prefix", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["principals_authority_prefix"] = mod
    spec.loader.exec_module(mod)

    def _register_principal_act(dest, name, agent_class, purpose, led=None):
        led = led if led is not None else mod._served_led(dest)
        argv = (*led, "register-principal", name, agent_class, "--purpose", purpose)
        return CommandAct(argv=argv, extra_env=mod._COMMISSIONER_ENV), f"principal-row:{name}"

    def _grant_competence_act(dest, name, activity, band, basis, led=None):
        led = led if led is not None else mod._served_led(dest)
        argv = (*led, "principal", "grant-competence", name,
                "--activity", activity, "--band", band, "--basis", basis)
        return (CommandAct(argv=argv, extra_env=mod._COMMISSIONER_ENV),
                f"competence-row:{name}:{activity}")

    def _relate_act(dest, subject, relation, obj, led=None):
        led = led if led is not None else mod._served_led(dest)
        argv = (*led, "principal", "relate", subject, relation, obj)
        return (CommandAct(argv=argv, extra_env=mod._COMMISSIONER_ENV),
                f"relation-row:{subject}:{relation}:{obj}")

    mod.register_principal_act = _register_principal_act
    mod.grant_competence_act = _grant_competence_act
    mod.relate_act = _relate_act
    return mod


def _fresh_state(dest: Path) -> dict:
    return {"_checklist": ck.Checklist(), "_plan": Plan(), "dest": str(dest),
            "dest_would_exist": False, "planned_principal_names": set()}


def _run_ceremony(dest: Path, pa_module, register_rows: list, relation_rows: list):
    """Drives `steps_principals_authority.submit()` -- the step's real UI-free core, the
    'headless' driving convention this whole fixture family uses for step-level cores (no
    Textual/Pilot needed: these `steps_*.py` modules are BUILT to be called directly, exactly
    like seen-red/setup-tui-pure-core-foundation's own Plan/commit_executor cases already do) --
    with `steps_principals_authority`'s own module-level `pa` reference monkeypatched to
    `pa_module` for the duration of the call, then runs the REAL resulting plan for real through
    `commit_executor.execute()` against `dest`. Returns (submit SectionResult, ExecutionResult)."""
    state = _fresh_state(dest)
    answers = {"register": register_rows, "competences": [], "relations": relation_rows,
               "charters": []}
    orig_pa = spa.pa
    spa.pa = pa_module
    try:
        result = spa.submit(state, answers)
    finally:
        spa.pa = orig_pa
    assert result.ok, f"submit() itself refused (unexpected -- a decision-phase-only failure): {result.errors}"
    exec_result = CE.execute(state["_plan"], str(dest))
    return result, exec_result


def _entry_detail(exec_result, idx: int) -> str:
    if idx >= len(exec_result.entry_results):
        return "(entry never ran -- commit halted at an earlier entry)"
    er = exec_result.entry_results[idx]
    return f"ok={er.ok} detail={er.detail!r}"


def _kill_boundary(dest: Path) -> None:
    """The SAME mechanism seen-red/minimal-profile-tracker/run_fixtures.py already uses: the
    `ensure_running`-spawned boundary_service child records its own pid at
    `<dest>/.autoharn-service.pid`."""
    pidfile = dest / ".autoharn-service.pid"
    if not pidfile.is_file():
        return
    try:
        pid = int(pidfile.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.3)
    except OSError:
        pass


def main() -> int:  # noqa: C901 -- one straight-line witness script, matching the s60/s62 family's own shape
    failures: list[str] = []
    tmps: list[Path] = []
    scratch = tempfile.mkdtemp(prefix="ctj-principals-ceremony-")
    world_s60, world_s62, world_pre = "cauths60", "cauths62", "cauthpre"
    for w in (world_s60, world_s62, world_pre):
        teardown(w)

    s62_sql_path = LINEAGE / "s62-delegation-lifecycle-gating.sql"
    s62_precopied = s62_sql_path.is_file()
    if not s62_precopied:
        got = sh(["git", "show", f"{S62_SRC_COMMIT}:kernel/lineage/s62-delegation-lifecycle-gating.sql"],
                  cwd=str(REPO))
        assert got.returncode == 0 and got.stdout.strip(), (
            f"could not read {S62_SRC_COMMIT}:kernel/lineage/s62-delegation-lifecycle-gating.sql "
            f"-- {got.stderr}")
        s62_sql_path.write_text(got.stdout, encoding="utf-8")
        print(f"-- cherry-picked s62 SQL from {S62_SRC_COMMIT} into {s62_sql_path} "
              f"(working tree only, NEVER committed by this fixture or this build) --")

    old_pa = _load_pinned_principals_authority(PRE_FIX_COMMIT, scratch)

    try:
        # ===================== WORLD S60 (chain s15..s59 + s60, NO s62) =====================
        print(f"== scaffolding classic world {world_s60} (chain ends {CHAIN_S60[-1]}) ==")
        port60 = probes.free_port(start=19420)
        w60 = scaffold_classic(world_s60, CHAIN_S60, port60)
        tmps.append(w60.parent)
        author60 = birth_via_boundary(world_s60)
        s60_birth(world_s60, author60)

        _, red60 = _run_ceremony(
            w60, old_pa,
            register_rows=[{"name": "orchestrator", "agent_class": "subagent",
                            "purpose": "orchestrator connection principal"}],
            relation_rows=[])
        check("WORLD-S60-RED-old-code-register-refused",
              not red60.completed and not red60.entry_results[0].ok
              and "conjunct" in red60.entry_results[0].detail,
              f"OLD principals_authority.py (LED_ACTOR=commissioner) drives register-principal "
              f"'orchestrator' on an s60 (no s62) world -- {_entry_detail(red60, 0)}", failures)
        _kill_boundary(w60)

        _, green60 = _run_ceremony(
            w60, pa_current,
            register_rows=[{"name": "orchestrator", "agent_class": "subagent",
                            "purpose": "orchestrator connection principal"}],
            relation_rows=[])
        check("WORLD-S60-GREEN-fixed-code-register-accepted",
              green60.completed and green60.entry_results[0].ok,
              f"CURRENT (fixed) principals_authority.py, identical call -- "
              f"{_entry_detail(green60, 0)}", failures)
        S60 = world_s60
        orch_actor60 = psql_tuples(
            f"SELECT actor FROM {S60}.ledger_current WHERE kind='principal_registered' "
            f"AND principal_subject=(SELECT id FROM {S60}_kernel.principal WHERE name='orchestrator');")
        author_id60 = psql_tuples(f"SELECT id FROM {S60}_kernel.principal WHERE name='author';")
        check("WORLD-S60-GREEN-authored-by-author",
              orch_actor60 == author_id60,
              f"'orchestrator' registered with actor={orch_actor60!r}, author's own id="
              f"{author_id60!r} -- must match (the declared-default actor resolution)", failures)
        _kill_boundary(w60)

        # ===================== WORLD S62 (chain s15..s59 + s60 + s62) =====================
        print(f"== scaffolding classic world {world_s62} (chain ends {CHAIN_S62[-1]}) ==")
        port62 = probes.free_port(start=19420)
        w62 = scaffold_classic(world_s62, CHAIN_S62, port62)
        tmps.append(w62.parent)
        author62 = birth_via_boundary(world_s62)
        s60_birth(world_s62, author62)
        register_direct(world_s62, "orchestrator", "subagent", author62)

        _, red62 = _run_ceremony(
            w62, old_pa, register_rows=[],
            relation_rows=[{"subject": "orchestrator", "relation": "acts-for", "object": "author"}])
        check("WORLD-S62-RED-old-code-relate-refused",
              not red62.completed and not red62.entry_results[0].ok
              and "delegation_lifecycle" in red62.entry_results[0].detail
              and "conjunct b" in red62.entry_results[0].detail,
              f"OLD principals_authority.py (LED_ACTOR=commissioner) drives 'orchestrator "
              f"acts-for author' on the s62 world -- {_entry_detail(red62, 0)}", failures)
        _kill_boundary(w62)

        _, green62 = _run_ceremony(
            w62, pa_current, register_rows=[],
            relation_rows=[{"subject": "orchestrator", "relation": "acts-for", "object": "author"}])
        check("WORLD-S62-GREEN-fixed-code-relate-accepted",
              green62.completed and green62.entry_results[0].ok,
              f"CURRENT (fixed) principals_authority.py, identical relation -- "
              f"{_entry_detail(green62, 0)}", failures)
        S62 = world_s62
        edge_count = psql_tuples(
            f"SELECT count(*) FROM {S62}.principal_relations WHERE relation='acts-for' "
            f"AND subject=(SELECT id FROM {S62}_kernel.principal WHERE name='orchestrator') "
            f"AND object=(SELECT id FROM {S62}_kernel.principal WHERE name='author');")
        check("WORLD-S62-GREEN-edge-lands-in-view",
              edge_count == "1",
              f"principal_relations carries {edge_count} 'orchestrator acts-for author' row(s) "
              f"(expect 1)", failures)
        _kill_boundary(w62)

        orchestrator_id62 = psql_tuples(
            f"SELECT id FROM {S62}_kernel.principal WHERE name='orchestrator';")
        v_bind_orch = bind_role(world_s62, author62, orchestrator_id62, "authority")
        if v_bind_orch["disposition"] != "accepted":
            raise RuntimeError(f"could not bind orchestrator's role (setup, not the fix under "
                                f"test): {v_bind_orch}")

        # led62: the argv PREFIX for a served `led` call in w62 -- `(<dest>/autoharn, "led")`,
        # matching `runner.served_led_path`'s own §6-amended shape (found broken here as a bare
        # `<dest>/led` path, the SAME post-merge argv-shape skew `_load_pinned_principals_
        # authority`'s own header explains: the per-verb `led` shim this fixture was originally
        # written against no longer exists post scaffold-umbrella-migration -- only `<dest>/
        # autoharn led ...` does, `bootstrap/new-project.sh`'s own dispatcher-writing section).
        led62 = (str(w62 / "autoharn"), "led")
        env_orch = dict(os.environ)
        env_orch["LED_ACTOR"] = "orchestrator"
        r_subsequent = sh([*led62, "register-principal", "probe-one", "subagent",
                           "--purpose", "subsequent act through the new chain"], env=env_orch)
        check("WORLD-S62-GREEN-subsequent-act-passes-conjunct-b",
              r_subsequent.returncode == 0,
              f"a SUBSEQUENT authority-bearing act run AS 'orchestrator' (fresh <dest>/led call, "
              f"no TUI) -- exit={r_subsequent.returncode} out={r_subsequent.stdout[-300:]!r} "
              f"err={r_subsequent.stderr[-300:]!r}", failures)
        _kill_boundary(w62)

        _, green_full = _run_ceremony(
            w62, pa_current,
            register_rows=[{"name": "scout", "agent_class": "subagent",
                            "purpose": "second fixture principal, full ceremony in one call"}],
            relation_rows=[{"subject": "scout", "relation": "acts-for", "object": "author"}])
        check("WORLD-S62-GREEN-FULL-CEREMONY-completes",
              green_full.completed and all(er.ok for er in green_full.entry_results),
              f"CURRENT code, register + relate together in ONE submit() call for a fresh "
              f"principal 'scout' -- entries: {[_entry_detail(green_full, i) for i in range(2)]}",
              failures)
        _kill_boundary(w62)
        scout_id62 = psql_tuples(f"SELECT id FROM {S62}_kernel.principal WHERE name='scout';")
        v_bind_scout = bind_role(world_s62, author62, scout_id62, "authority")
        if v_bind_scout["disposition"] != "accepted":
            raise RuntimeError(f"could not bind scout's role (setup, not the fix under test): "
                                f"{v_bind_scout}")
        env_scout = dict(os.environ)
        env_scout["LED_ACTOR"] = "scout"
        r_scout = sh([*led62, "register-principal", "probe-two", "subagent",
                     "--purpose", "scout's own subsequent act"], env=env_scout)
        check("WORLD-S62-GREEN-FULL-CEREMONY-scout-subsequent-act",
              r_scout.returncode == 0,
              f"'scout' (registered + related in the SAME ceremony call) passes a subsequent "
              f"authority-bearing act too -- exit={r_scout.returncode}", failures)
        _kill_boundary(w62)

        # ===================== WORLD PRE (chain s15..s59, NO s60/s62) =====================
        print(f"== scaffolding classic world {world_pre} (chain ends {CHAIN_S59[-1]}, "
              f"no entitlement family -- 'born before s62') ==")
        port_pre = probes.free_port(start=19420)
        wpre = scaffold_classic(world_pre, CHAIN_S59, port_pre)
        tmps.append(wpre.parent)
        birth_via_boundary(world_pre)

        _, green_pre = _run_ceremony(
            wpre, pa_current,
            register_rows=[{"name": "orchestrator", "agent_class": "subagent",
                            "purpose": "orchestrator connection principal"}],
            relation_rows=[{"subject": "orchestrator", "relation": "acts-for", "object": "author"}])
        check("WORLD-PRE-ZERO-FRICTION-fixed-code-still-completes",
              green_pre.completed and all(er.ok for er in green_pre.entry_results),
              f"CURRENT (fixed) code, full ceremony, on a world born BEFORE s60/s62 (no "
              f"entitlement family present at all) -- must complete exactly as it always did: "
              f"entries: {[_entry_detail(green_pre, i) for i in range(2)]}", failures)
        _kill_boundary(wpre)

    finally:
        for w in (world_s60, world_s62, world_pre):
            teardown(w)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)
        shutil.rmtree(scratch, ignore_errors=True)
        if not s62_precopied and s62_sql_path.is_file():
            s62_sql_path.unlink()
            print(f"-- removed the working-tree-only s62 cherry-pick at {s62_sql_path} "
                  f"(never committed) --")

    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nALL CASES OK -- work item tui-ceremony-chain-authorship: the founding ceremony's "
          "three commissioner-authored acts now leave LED_ACTOR unset (declared-default -> "
          "'author', genesis-chained), fixing BOTH the pre-existing s60-only register_principal_"
          "act hazard and the s62-surfaced relate_act hazard, zero-friction on worlds born "
          "before either kernel delta.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
