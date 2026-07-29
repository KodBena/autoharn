#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s72-stamp-binding-conjunct.sql
(design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md sec5 item 5, ledger rows 601/639).
Real infra, no mocks: a CLASSIC scaffold (bootstrap/new-project.sh) + the full lineage chain
applied in the TOY db, torn down before AND after. Modeled directly on
seen-red/s70-scope-binding/run_fixtures.py (scaffold_classic/birth_via_boundary/bw_call/detect/
judge_agree helpers, same shape) -- this delta, like s70, does NOT remediate a previously-
accepted-bad write (principal_stamp_bound/stamp_binding_class_configured are UNREPRESENTABLE
before s72), so the two-polarity ceremony is: WORLD PRE (s71 head, NO s72) is byte-identical, and
WORLD MAIN (s72 head) exhibits every new behavior the spec/row-601 adjudication commissions.

STAMP FORGERY, NOT HOOK REPLAY: this fixture computes its OWN valid interception HMAC directly
(the exact scheme kernel/lineage/s17-stamp-mechanism.sql's own stamp_valid() implements:
hmac_sha256(secret, f"{session}|{agent}|{ts}")) against the scratch world's own freshly
provisioned stamp_secret.hex (written by bootstrap/new-project.sh's scaffold step, read back
here) -- never invoking hooks/stamp_intercept.py itself (a Claude-Code-hook mechanism, orthogonal
to this fixture's own psql-session GUC injection), exactly the same "set app.vendor_* directly,
bypass the hook" technique every prior seen-red fixture in this lineage already relies on to
produce a stamp AT ALL from a plain, non-intercepted shell (see sh()'s own PGOPTIONS-stripping
note, inherited unchanged from the s70/s71 fixtures).

WORLD PRE (s71 head, NO s72):
  REGRESSION-DETECT-ABSENT             -- s72-stamp-binding-conjunct.detect.sql reports 'f'.
  REGRESSION-ORDINARY-WRITE-UNAFFECTED -- an ordinary note write, unaffected by this delta's mere
                                     existence, still accepted.

WORLD MAIN (s72 head):
  REGRESSION-DETECT-PRESENT      -- s72-stamp-binding-conjunct.detect.sql reports 't'.
  UNARMED-BYTE-IDENTICAL-UNSTAMPED-ACCEPTED -- with ZERO stamp_binding_class_configured rows
                                     (the shipped default), an UNSTAMPED write in what would be a
                                     gated class elsewhere (principal_role_bound) is accepted
                                     exactly as it always was pre-s72 -- conjunct (c) is a total
                                     no-op until a class is nominated.
  GREEN-STAMP-BIND-ENTITLED-ACCEPTED   -- the genesis-chained actor binds ITSELF to stamp_agent
                                     'main' -- accepted, principal_stamp_bindings renders it.
  GREEN-STAMP-BIND-UNENTITLED-REFUSED  -- a chainless, roleless principal attempting to bind a
                                     stamp (to itself) is refused (conjunct b).
  GREEN-NOMINATE-CLASS-ENTITLED-ACCEPTED -- the genesis-chained actor nominates
                                     principal_role_bound for the stamp-binding conjunct --
                                     accepted, stamp_binding_classes renders it.
  GREEN-NOMINATE-CLASS-UNENTITLED-REFUSED -- a chainless principal attempting to nominate a class
                                     is refused (stamp_binding_class_configured is itself
                                     authority-bearing, conjunct b).
  ARMED-UNSTAMPED-WRITE-REFUSED        -- once principal_role_bound is nominated, an UNSTAMPED
                                     principal_role_bound write (even by a genesis-chained,
                                     correctly-role-entitled actor) is REFUSED -- conjunct (c).
  ARMED-WRONG-AGENT-STAMPED-REFUSED    -- a VERIFIED stamp whose agent is NOT the one bound to
                                     this actor (e.g. a dispatched-subagent-shaped ephemeral id)
                                     is REFUSED -- exactly row 601's "excludes... subagent-stamped
                                     writes" correction, witnessed directly.
  ARMED-CORRECT-AGENT-STAMPED-ACCEPTED -- a VERIFIED stamp whose agent IS the one bound to this
                                     actor ('main') is ACCEPTED.
  ARMED-FORGED-AGENT-STRING-UNVERIFIED-REFUSED -- an UNVERIFIED stamp (missing/invalid HMAC)
                                     merely CLAIMING stamp_agent='main' (the exact forgery this
                                     delta's own header WHY-STAMP_VERIFIED paragraph names) is
                                     REFUSED -- string equality on stamp_agent alone is NEVER
                                     sufficient; stamp_verified is load-bearing.
  ARMED-NON-NOMINATED-CLASS-UNAFFECTED -- an unstamped write in a NON-nominated class (a plain
                                     'note') is accepted, unaffected by any of the above -- the
                                     conjunct's own class-scoping, witnessed directly.
  STAMP-SEVERANCE-CROSS-KIND-REFUSED   -- a chainless actor superseding the LIVE principal_stamp_
                                     bound row with an unrelated kind (note) is refused via the
                                     target-class conjunct.
  STAMP-UNBIND-REMOVES-FROM-VIEW       -- a retraction (principal_binding_active=false) removes
                                     the (subject, agent) pair from principal_stamp_bindings.
  ZERO-FRICTION-BIRTH                  -- a fresh classic scaffold's birth sequence through s72,
                                     unaffected -- zero new friction from two new, un-nominated
                                     act-class tokens.
  VERIFY-CHAIN-INTACT-THROUGH-REFUSALS -- ./autoharn verify-chain INTACT + refusal-oracle
                                     CONFIRMED, after every refusal above.
  AGREE-sql-asp-work-differential      -- judge --layer work SQL/ASP AGREE on the s72-head world
                                     (chain-reachability, generic over act class, unchanged --
                                     s62/s64/s70's own "no new predicate" claim re-verified two
                                     tokens further). NO differential exists for conjunct (c)
                                     itself -- UNEXERCISED, flagged as the engine-side follow-on
                                     this delta's own header names, never silently claimed AGREE.

Usage: python3 seen-red/s72-stamp-binding-conjunct/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports are banned."""
from __future__ import annotations

import hashlib
import hmac as hmac_lib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LINEAGE = REPO / "kernel" / "lineage"
sys.path.insert(0, str(REPO / "filing"))
from pghost_resolve import resolve_pghost  # noqa: E402

os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S71 = [
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
    "s65-refusal-attempted-kind.sql",
    "s66-forged-stamp-journal-totality.sql",
    "s67-refusal-digest-bound.sql",
    "s68-typed-absence-dispositions.sql",
    "s69-role-coherence-refusals.sql",
    "s70-scope-binding.sql",
    "s71-row-level-scope-policies.sql",
]
CHAIN_S72 = CHAIN_S71 + ["s72-stamp-binding-conjunct.sql"]


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    # PGOPTIONS stripped -- see seen-red/s70-scope-binding/run_fixtures.py's own identical note:
    # hooks/stamp_intercept.py injects app.vendor_* into PGOPTIONS ahead of every Bash-tool
    # command; a fresh scratch world's own kernel.stamp_secret is unrelated random, so an
    # inherited GUC would be present-but-invalid and get refused rather than accepted-unstamped.
    env = dict(kw.pop("env", os.environ))
    env.pop("PGOPTIONS", None)
    return subprocess.run(args, capture_output=True, text=True, env=env, **kw)


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


def detect(world: str, sibling: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1",
             "-v", f"schema={world}", "-f", str(LINEAGE / sibling)])
    if cp.returncode != 0:
        raise RuntimeError(f"detect failed: {cp.stderr}")
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
    genesis_hex = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis_hex}') "
              f"ON CONFLICT (only_one) DO NOTHING;"])
    return world_dir


def bw_call(world: str, fn: str, payload: dict, vendor: dict[str, str] | None = None) -> dict:
    """Same shape as the s70/s71 fixtures' own bw_call, with an OPTIONAL `vendor` preamble:
    when given, SETs app.vendor_session/app.vendor_agent/app.vendor_ts/app.vendor_hmac in the
    SAME session before the write, so set_stamp's trigger (kernel/lineage/s17-stamp-mechanism.sql)
    sees them and stamps NEW.stamp_session/stamp_agent/stamp_verified accordingly -- exactly the
    fixture-side stamp-forgery technique this file's own module docstring names."""
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    pj = json.dumps(payload).replace("'", "''")
    preamble = ""
    if vendor:
        for k, v in vendor.items():
            preamble += f"SET app.vendor_{k} = '{v}';\n"
    r = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"],
           input=f"SET ROLE {R};\nSET search_path = {S}, {K};\n{preamble}"
                 f"SELECT to_jsonb(v) FROM {K}.{fn}('{pj}'::jsonb) v;\n")
    if r.returncode != 0:
        raise RuntimeError(f"NON-VERDICT: {r.stderr.strip()[-800:]}")
    lines = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("{")]
    if not lines:
        raise RuntimeError(f"NO VERDICT LINE: stdout={r.stdout!r} stderr={r.stderr!r}")
    return json.loads(lines[-1])


def valid_vendor(secret_hex: str, session: str, agent: str, ts: int | None = None) -> dict[str, str]:
    """The exact scheme kernel/lineage/s17-stamp-mechanism.sql's own stamp_valid() implements,
    computed here directly (never via hooks/stamp_intercept.py -- see module docstring)."""
    ts = ts if ts is not None else int(time.time())
    secret = bytes.fromhex(secret_hex)
    data = f"{session}|{agent}|{ts}".encode()
    digest = hmac_lib.new(secret, data, hashlib.sha256).hexdigest()
    return {"session": session, "agent": agent, "ts": str(ts), "hmac": digest}


def forged_vendor(agent: str, ts: int | None = None) -> dict[str, str]:
    """A syntactically well-formed but WRONG hmac -- fails stamp_valid(), so set_stamp's own
    trigger RAISES (a present-but-invalid stamp is refused at write time, s17's own text) rather
    than silently recording stamp_verified=false. Used to witness that a bare agent-string CLAIM,
    unauthenticated, can never reach conjunct (c)'s EXISTS check at all -- it is refused one layer
    earlier, by set_stamp itself, exactly the layering this delta's own header WHY paragraph
    relies on."""
    ts = ts if ts is not None else int(time.time())
    return {"session": "forged-session", "agent": agent, "ts": str(ts), "hmac": "0" * 64}


def provision_stamp_secret(world_dir: Path, world: str) -> str:
    """scaffold_classic (--schema/--kern/--role, no --new-world) never enters bootstrap/
    new-project.sh's own `if [ "$FULL_LINEAGE" -eq 1 ]` block (FULL_LINEAGE is set only when
    --new-world is given, line ~760 of that script) -- the stamp-secret provisioning step (that
    script's own "seeding the stamp secret" echo, TRUNCATE+INSERT into kern.stamp_secret) lives
    INSIDE that block, so a CLASSIC-scaffolded world's stamp_secret table exists (s17's own DDL)
    but is EMPTY. This fixture needs a REAL, known secret to compute valid interception HMACs
    against (the module docstring's own "stamp forgery" section) -- reproduced here, byte-for-
    byte, mirroring that script's own idiom (openssl rand -hex 32, TRUNCATE, INSERT decode(hex)),
    and additionally written to the SAME conventional path (.claude/secrets/stamp_secret.hex)
    other tooling expects, though this fixture only ever reads back its own in-memory hex."""
    kern = f"{world}_kernel"
    secrets_dir = world_dir / ".claude" / "secrets"
    secrets_dir.mkdir(parents=True, exist_ok=True)
    hex_val = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    (secrets_dir / "stamp_secret.hex").write_text(hex_val + "\n")
    os.chmod(secrets_dir / "stamp_secret.hex", 0o600)
    # psql's :"var"/:'var' bind-variable interpolation is only performed for input parsed as a
    # SCRIPT (stdin or -f) -- a silent no-op under -c (bootstrap/new-project.sh's own documented
    # gotcha, its _psql_in helper's header comment) -- so both statements are fed on stdin here,
    # never via -c.
    r1 = sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1", "-v", f"kern={kern}",
             "-f", "/dev/stdin"], input='TRUNCATE :"kern".stamp_secret;\n')
    if r1.returncode != 0:
        raise RuntimeError(f"stamp_secret TRUNCATE failed: {r1.stdout} {r1.stderr}")
    r2 = sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
             "-v", f"kern={kern}", "-v", f"hex={hex_val}", "-f", "/dev/stdin"],
            input="INSERT INTO :\"kern\".stamp_secret (secret) VALUES (decode(:'hex','hex'));\n")
    if r2.returncode != 0:
        raise RuntimeError(f"stamp_secret INSERT failed: {r2.stdout} {r2.stderr}")
    return hex_val


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
                                "purpose": "s72 fixture's own write-boundary registration"}),
    ]:
        v = bw_call(world, fn, payload)
        if v["disposition"] != "accepted":
            raise RuntimeError(f"birth act refused: {v}")
    return author


def register(world: str, author: str, name: str, agent_class: str = "human") -> str:
    v = bw_call(world, "registration_write",
                {"name": name, "agent_class": agent_class, "actor": author,
                 "purpose": f"fixture principal {name}"})
    if v["disposition"] != "accepted":
        raise RuntimeError(f"registration of {name} refused: {v}")
    K = f"{world}_kernel"
    return psql_tuples(f"SELECT id FROM {K}.principal WHERE name='{name}';")


def verify_chain(world_dir: Path) -> tuple[int, str]:
    cp = sh(["sh", str(world_dir / "autoharn"), "verify-chain"], cwd=str(world_dir))
    return cp.returncode, cp.stdout + cp.stderr


def judge_agree(world: str, failures: list[str], label: str) -> None:
    env = dict(os.environ)
    env["HARNESS_PGHOST"] = PGHOST
    env["EPISTEMIC_PGHOST"] = PGHOST
    env["LEDGER_DB"] = PGDB
    env["LEDGER_SCHEMA"] = world
    env["LEDGER_KERN"] = f"{world}_kernel"
    env["PYTHONPATH"] = f"{REPO / 'engine'}:{REPO / 'filing'}"
    cp = sh(["python3", "-c",
             "import ledger_differential as ld\n"
             "r = ld.run_layer_differential('anyname', layer='work')\n"
             "print(r.verdict())\n"],
            env=env, cwd=str(REPO))
    if cp.returncode != 0:
        raise RuntimeError(f"judge programmatic call failed ({world}): {cp.stderr}")
    out = cp.stdout.strip().splitlines()
    check(label, bool(out) and out[0] == "AGREE", f"judge output ({world}): {out}", failures)


def main() -> int:  # noqa: C901
    failures: list[str] = []
    tmps: list[Path] = []
    world_pre, world_main, world_birth = "s72fxpre", "s72fxmain", "s72fxbirth"
    for w in (world_pre, world_main, world_birth):
        teardown(w)
    try:
        # ===================== WORLD PRE (s71 head, NO s72) =====================
        print(f"== scaffolding classic world {world_pre} (chain ends {CHAIN_S71[-1]}, NO s72) ==")
        wp = scaffold_classic(world_pre, CHAIN_S71)
        tmps.append(wp.parent)

        d_pre = detect(world_pre, "s72-stamp-binding-conjunct.detect.sql")
        check("REGRESSION-DETECT-ABSENT", d_pre == "f",
              f"s72-stamp-binding-conjunct.detect.sql on the s71-head world (no s72 applied): "
              f"{d_pre!r} (expected f)", failures)

        author_pre = birth_via_boundary(world_pre)
        v_note_pre = bw_call(world_pre, "ledger_write",
                              {"kind": "note", "statement": "ordinary note, pre-s72",
                               "actor": author_pre})
        check("REGRESSION-ORDINARY-WRITE-UNAFFECTED",
              v_note_pre["disposition"] == "accepted",
              f"an ordinary note write on the s71-head (pre-s72) world -- ACCEPTED, unaffected "
              f"by this delta's mere existence -- verdict={v_note_pre}", failures)

        # ===================== WORLD MAIN (s72 head) =====================
        print(f"== scaffolding classic world {world_main} (chain ends {CHAIN_S72[-1]}) ==")
        wm = scaffold_classic(world_main, CHAIN_S72)
        tmps.append(wm.parent)
        secret_hex = provision_stamp_secret(wm, world_main)

        d_main = detect(world_main, "s72-stamp-binding-conjunct.detect.sql")
        check("REGRESSION-DETECT-PRESENT", d_main == "t",
              f"s72-stamp-binding-conjunct.detect.sql on the s72-head world: {d_main!r} "
              f"(expected t)", failures)

        author = birth_via_boundary(world_main)
        outsider = register(world_main, author, "outsider")  # NO acts-for edge -- chainless.

        # ---- UNARMED-BYTE-IDENTICAL-UNSTAMPED-ACCEPTED (zero stamp_binding_class_configured
        # rows exist yet -- conjunct (c) is a total no-op for every class) ----
        v_unarmed_rolebind = bw_call(
            world_main, "ledger_write",
            {"kind": "principal_role_bound", "statement": "author binds itself the authority role",
             "actor": author, "principal_subject": author, "principal_binding_active": "true",
             "principal_role_name": "authority"})
        check("UNARMED-BYTE-IDENTICAL-UNSTAMPED-ACCEPTED",
              v_unarmed_rolebind["disposition"] == "accepted",
              f"an UNSTAMPED principal_role_bound write, before ANY class is nominated -- "
              f"ACCEPTED, byte-identical to s71-head behavior (conjunct c is a total no-op with "
              f"an empty stamp_binding_classes) -- verdict={v_unarmed_rolebind}", failures)

        # ---- GREEN-STAMP-BIND-UNENTITLED-REFUSED (conjunct b, checked BEFORE any legitimate
        # bind exists) ----
        v_unentitled = bw_call(world_main, "ledger_write",
                                {"kind": "principal_stamp_bound",
                                 "statement": "outsider tries to stamp-bind itself",
                                 "actor": outsider, "principal_subject": outsider,
                                 "principal_binding_active": "true",
                                 "stamp_binding_agent": "main"})
        check("GREEN-STAMP-BIND-UNENTITLED-REFUSED",
              v_unentitled["disposition"] == "refused"
              and "does not reach this world" in (v_unentitled["message"] or ""),
              f"a chainless, roleless principal (outsider) attempting to bind ITS OWN stamp is "
              f"REFUSED on conjunct (b) -- stamp_binding is authority-bearing, unconditionally -- "
              f"verdict={v_unentitled}", failures)

        # ---- GREEN-STAMP-BIND-ENTITLED-ACCEPTED (author binds itself to 'main') ----
        v_bind = bw_call(world_main, "ledger_write",
                          {"kind": "principal_stamp_bound",
                           "statement": "author binds itself to stamp_agent 'main'",
                           "actor": author, "principal_subject": author,
                           "principal_binding_active": "true",
                           "stamp_binding_agent": "main"})
        check("GREEN-STAMP-BIND-ENTITLED-ACCEPTED",
              v_bind["disposition"] == "accepted",
              f"the genesis-chained actor (author) binds itself to stamp_agent 'main' -- "
              f"ACCEPTED -- verdict={v_bind}", failures)

        rendered = psql_tuples(
            f"SELECT agent FROM {world_main}.principal_stamp_bindings WHERE subject = {author};")
        check("GREEN-STAMP-BIND-RENDERED-IN-VIEW", rendered == "main",
              f"principal_stamp_bindings renders the bound agent for author -- row: {rendered!r}",
              failures)

        # ---- GREEN-NOMINATE-CLASS-UNENTITLED-REFUSED ----
        v_nom_unentitled = bw_call(
            world_main, "ledger_write",
            {"kind": "stamp_binding_class_configured",
             "statement": "outsider tries to nominate a class",
             "actor": outsider, "entitlement_act_class": "principal_role_bound"})
        check("GREEN-NOMINATE-CLASS-UNENTITLED-REFUSED",
              v_nom_unentitled["disposition"] == "refused"
              and "does not reach this world" in (v_nom_unentitled["message"] or ""),
              f"a chainless principal (outsider) attempting to NOMINATE a class is REFUSED -- "
              f"stamp_binding_class_configured is itself authority-bearing (conjunct b) -- "
              f"verdict={v_nom_unentitled}", failures)

        # ---- GREEN-NOMINATE-CLASS-ENTITLED-ACCEPTED (nominate principal_role_bound) ----
        v_nom = bw_call(world_main, "ledger_write",
                         {"kind": "stamp_binding_class_configured",
                          "statement": "author nominates principal_role_bound for the "
                                       "stamp-binding conjunct",
                          "actor": author, "entitlement_act_class": "principal_role_bound"})
        check("GREEN-NOMINATE-CLASS-ENTITLED-ACCEPTED",
              v_nom["disposition"] == "accepted",
              f"the genesis-chained actor nominates principal_role_bound -- ACCEPTED -- "
              f"verdict={v_nom}", failures)

        nominated = psql_tuples(
            f"SELECT act_class FROM {world_main}.stamp_binding_classes "
            f"WHERE act_class = 'principal_role_bound';")
        check("GREEN-NOMINATE-CLASS-RENDERED-IN-VIEW", nominated == "principal_role_bound",
              f"stamp_binding_classes now nominates principal_role_bound -- row: {nominated!r}",
              failures)

        # ---- ARMED-UNSTAMPED-WRITE-REFUSED (principal_role_bound is now nominated; an
        # UNSTAMPED write, even by a genesis-chained, role-map-vacuous actor, is refused) ----
        v_armed_unstamped = bw_call(
            world_main, "ledger_write",
            {"kind": "principal_role_bound", "statement": "author re-binds, unstamped, post-arm",
             "actor": author, "principal_subject": author, "principal_binding_active": "true",
             "principal_role_name": "authority",
             "supersedes": v_unarmed_rolebind["row_id"]})
        check("ARMED-UNSTAMPED-WRITE-REFUSED",
              v_armed_unstamped["disposition"] == "refused"
              and "conjunct c" in (v_armed_unstamped["message"] or ""),
              f"once principal_role_bound is NOMINATED, an UNSTAMPED write in that class is "
              f"REFUSED (conjunct c) even from the genesis-chained actor -- verdict="
              f"{v_armed_unstamped}", failures)

        # ---- ARMED-WRONG-AGENT-STAMPED-REFUSED (a VERIFIED stamp, agent NOT bound to author --
        # the ephemeral-dispatched-agent shape row 601 names) ----
        vendor_wrong_agent = valid_vendor(secret_hex, "sess-subagent", "agent-a47950d7504b5b166")
        v_armed_wrong_agent = bw_call(
            world_main, "ledger_write",
            {"kind": "principal_role_bound", "statement": "a dispatched-subagent-shaped stamp",
             "actor": author, "principal_subject": author, "principal_binding_active": "true",
             "principal_role_name": "authority",
             "supersedes": v_unarmed_rolebind["row_id"]},
            vendor=vendor_wrong_agent)
        check("ARMED-WRONG-AGENT-STAMPED-REFUSED",
              v_armed_wrong_agent["disposition"] == "refused"
              and "conjunct c" in (v_armed_wrong_agent["message"] or ""),
              f"a VERIFIED stamp whose agent ('agent-a47950d7504b5b166', the ephemeral-dispatched-"
              f"agent shape) is NOT bound to author is REFUSED -- row 601's own 'excludes... "
              f"subagent-stamped writes' correction, witnessed directly -- verdict="
              f"{v_armed_wrong_agent}", failures)

        # ---- ARMED-FORGED-AGENT-STRING-UNVERIFIED-REFUSED (an UNVERIFIED stamp merely CLAIMING
        # stamp_agent='main' -- a bogus HMAC) ----
        v_forged = None
        forged_exc = None
        try:
            v_forged = bw_call(
                world_main, "ledger_write",
                {"kind": "principal_role_bound", "statement": "forged main-agent claim",
                 "actor": author, "principal_subject": author, "principal_binding_active": "true",
                 "principal_role_name": "authority",
                 "supersedes": v_unarmed_rolebind["row_id"]},
                vendor=forged_vendor("main"))
        except RuntimeError as exc:
            forged_exc = exc
        # set_stamp itself (s17) RAISES on a present-but-invalid HMAC -- this is refused ONE LAYER
        # EARLIER than conjunct (c), never reaching validate_entitlement's own stamp check at all,
        # exactly the layering this delta's own header WHY paragraph names. Either surfacing (a
        # non-zero-exit bw_call RuntimeError carrying the stamp-mismatch text, or -- if some future
        # refactor ever let it through -- a conjunct (c) refusal) counts as the property witnessed:
        # a bare agent-string CLAIM, unauthenticated, is NEVER accepted.
        forged_refused = (forged_exc is not None
                           and "did not validate" in str(forged_exc)) or (
                          v_forged is not None and v_forged["disposition"] == "refused")
        check("ARMED-FORGED-AGENT-STRING-UNVERIFIED-REFUSED", forged_refused,
              f"an UNVERIFIED stamp (bogus HMAC) merely claiming stamp_agent='main' is REFUSED -- "
              f"either by set_stamp itself (s17's own 'did not validate' raise, one layer "
              f"upstream of conjunct c) or by conjunct (c)'s own stamp_verified check -- "
              f"exc={forged_exc}, verdict={v_forged}", failures)

        # ---- ARMED-CORRECT-AGENT-STAMPED-ACCEPTED (a VERIFIED stamp, agent = 'main', the agent
        # author itself bound above) ----
        vendor_main = valid_vendor(secret_hex, "sess-main-2", "main")
        v_armed_ok = bw_call(
            world_main, "ledger_write",
            {"kind": "principal_role_bound", "statement": "author re-binds, correctly stamped",
             "actor": author, "principal_subject": author, "principal_binding_active": "true",
             "principal_role_name": "authority",
             "supersedes": v_unarmed_rolebind["row_id"]},
            vendor=vendor_main)
        check("ARMED-CORRECT-AGENT-STAMPED-ACCEPTED",
              v_armed_ok["disposition"] == "accepted",
              f"a VERIFIED stamp whose agent ('main') IS bound to author -- ACCEPTED -- "
              f"verdict={v_armed_ok}", failures)

        # ---- ARMED-NON-NOMINATED-CLASS-UNAFFECTED (an unstamped 'note' -- never nominated) ----
        v_note_unaffected = bw_call(world_main, "ledger_write",
                                     {"kind": "note", "statement": "unstamped, non-nominated class",
                                      "actor": author})
        check("ARMED-NON-NOMINATED-CLASS-UNAFFECTED",
              v_note_unaffected["disposition"] == "accepted",
              f"an UNSTAMPED write in a class NEVER nominated ('note') is unaffected by this "
              f"world's own armed conjunct over principal_role_bound -- ACCEPTED -- verdict="
              f"{v_note_unaffected}", failures)

        # ---- STAMP-SEVERANCE-CROSS-KIND-REFUSED ----
        v_sever = bw_call(world_main, "ledger_write",
                           {"kind": "note", "statement": "outsider tries to sever author's "
                                                          "stamp binding",
                            "supersedes": v_bind["row_id"], "actor": outsider})
        check("STAMP-SEVERANCE-CROSS-KIND-REFUSED",
              v_sever["disposition"] == "refused"
              and "does not reach this world" in (v_sever["message"] or ""),
              f"a chainless actor (outsider) superseding the LIVE principal_stamp_bound row with "
              f"an UNRELATED kind (note) is REFUSED via the target-class conjunct -- "
              f"verdict={v_sever}", failures)

        # ---- STAMP-UNBIND-REMOVES-FROM-VIEW ----
        v_unbind = bw_call(world_main, "ledger_write",
                            {"kind": "principal_stamp_bound",
                             "statement": "author unbinds its own stamp binding",
                             "supersedes": v_bind["row_id"],
                             "actor": author, "principal_subject": author,
                             "principal_binding_active": "false",
                             "stamp_binding_agent": "main"},
                            vendor=vendor_main)
        check("STAMP-UNBIND-ACCEPTED", v_unbind["disposition"] == "accepted",
              f"author unbinds (retracts) its own stamp binding -- ACCEPTED -- "
              f"verdict={v_unbind}", failures)
        rows_after_unbind = psql_tuples(
            f"SELECT count(*) FROM {world_main}.principal_stamp_bindings "
            f"WHERE subject = {author} AND agent = 'main';")
        check("STAMP-UNBIND-REMOVES-FROM-VIEW", rows_after_unbind == "0",
              f"after the unbind, author has ZERO ('main') rows in principal_stamp_bindings -- "
              f"rows={rows_after_unbind}", failures)

        # NOTE: author is now UNBOUND from 'main' -- every subsequent write in THIS fixture uses
        # actor=author with NO vendor stamp (unstamped) on classes that remain UN-nominated
        # (stamp_binding_class_configured/principal_stamp_bound themselves were never nominated in
        # this fixture), so the unbind above does not itself block the remaining checks below.

        # ---- ZERO-FRICTION-BIRTH ----
        print(f"== scaffolding classic world {world_birth} (chain ends {CHAIN_S72[-1]}, fresh "
              f"birth) ==")
        wb = scaffold_classic(world_birth, CHAIN_S72)
        tmps.append(wb.parent)
        author_birth = birth_via_boundary(world_birth)
        v_birth_ok = bw_call(world_birth, "ledger_write",
                              {"kind": "note", "statement": "zero-friction birth note",
                               "actor": author_birth})
        check("ZERO-FRICTION-BIRTH-accepted",
              v_birth_ok["disposition"] == "accepted",
              f"a fresh world's own s40/s43/s72 birth sequence, then an ordinary note write -- "
              f"ACCEPTED, no extra friction from this delta's two new, un-nominated act-class "
              f"tokens -- verdict={v_birth_ok}", failures)

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
              f"./autoharn verify-chain after every refusal above -- exit={rc_v}, "
              f"INTACT+ORACLE-CONFIRMED in output="
              f"{('INTACT' in out_v) and ('REFUSAL-ORACLE-CONFIRMED' in out_v)}, oracle count="
              f"{oracle_count} == sequence={oracle_seq}", failures)

        # ---- AGREE: SQL/ASP work-layer differential ----
        judge_agree(world_main, failures, "AGREE-sql-asp-work-differential")
        print("NOTE: no differential covers conjunct (c) itself (the stamp-binding requirement) "
              "or the stamp_binding/stamp_binding_class_configured act classes' own family -- "
              "engine/ledger_edb.py exports no stamp-binding facts and engine/lp/"
              "ledger_entitlement.lp derives no stamp-binding-specific predicate. UNEXERCISED, "
              "flagged as the engine-side follow-on this delta's own header names, never "
              "silently claimed AGREE for that family.")

    finally:
        for w in (world_pre, world_main, world_birth):
            teardown(w)
        for t in tmps:
            sh(["rm", "-rf", str(t)])

    print(f"\n{'ALL GREEN' if not failures else 'FAILURES: ' + ', '.join(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
