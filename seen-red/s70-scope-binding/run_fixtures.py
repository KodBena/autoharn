#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s70-scope-binding.sql (design/
FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md sec1b/sec1c, ratified ledger row 639). Real
infra, no mocks: a CLASSIC scaffold (bootstrap/new-project.sh, the real --new-world path) + the
full lineage chain applied in the TOY db, torn down before AND after. Modeled directly on
seen-red/s69-role-coherence-refusals/run_fixtures.py (scaffold_classic/birth_via_boundary/bw_call
helpers, judge_agree, same shape) and seen-red/reservation-residue/run_fixtures.py (the detect()
helper, the class-ratified-fail-safe regression shape this delta's own commission asks for:
"a world WITHOUT s70 is untouched").

FIXTURE FAMILY CHOICE: a NEW sibling family -- s70 mints a kind/columns/view/entitlement-token
vocabulary no existing family's own RED/GREEN pair covers.

Unlike s60/s62/s64/s69, this delta does NOT remediate a previously-ACCEPTED-bad write (there is
no pre-existing "gap" to demonstrate on WORLD PRE -- principal_scope_bound is UNREPRESENTABLE
before s70, full stop, by ledger_kind_check alone). The two-polarity ceremony here is therefore:
WORLD PRE (s69 head, NO s70) is BYTE-IDENTICAL/untouched (regression: detect.sql reports absent,
an ordinary write is unaffected), and WORLD MAIN (s70 head) exhibits every new behavior the spec
commissions.

WORLD PRE (s69 head, NO s70):
  REGRESSION-DETECT-ABSENT       -- s70-scope-binding.detect.sql reports 'f' (absent).
  REGRESSION-ORDINARY-WRITE-UNAFFECTED -- an ordinary note write, unaffected by this delta's
                                     existence, still accepted.

WORLD MAIN (s70 head):
  REGRESSION-DETECT-PRESENT      -- s70-scope-binding.detect.sql reports 't' (present).
  GREEN-SCOPE-BIND-ENTITLED-ACCEPTED   -- the genesis-chained actor binds a scope to itself --
                                     accepted, principal_scopes renders it.
  GREEN-SCOPE-BIND-UNENTITLED-REFUSED  -- a chainless, roleless principal attempting to bind a
                                     scope (to itself) is refused (conjunct b).
  GREEN-SCOPE-SEVERANCE-CROSS-KIND-REFUSED -- a chainless principal attempts to supersede a LIVE
                                     principal_scope_bound row with an unrelated kind (note) --
                                     refused via the target-class conjunct (entitlement_act_
                                     class_of_target), the s62-round-2 cross-kind severance
                                     protection extended one token further.
  HAPPY-SCOPE-REBIND-BY-ENTITLED       -- the SAME genesis-chained actor rotates (supersedes) its
                                     own scope binding -- accepted; principal_scopes now renders
                                     the ROTATED payload, not the original.
  HAPPY-SCOPE-UNBIND-RESTORES-OPEN-DEFAULT -- a retraction (principal_binding_active=false)
                                     removes the subject from principal_scopes -- the fail-safe
                                     open-scope default, structural (absence, not a marker row).
  OPEN-SCOPE-DEFAULT-FOR-NEVER-BOUND   -- a principal who was NEVER scope-bound has zero rows in
                                     principal_scopes from birth (the same fail-safe default,
                                     never needing an explicit "unrestricted" row).
  MALFORMED-DISCLOSURE-MODE-REFUSED    -- scope_disclosure_mode='bogus' refused (CHECK).
  MALFORMED-EXCLUSIONS-BAD-FAMILY-REFUSED     -- scope_exclusions family not in the closed
                                     four-member vocabulary -- refused.
  MALFORMED-EXCLUSIONS-ROWS-NOT-NUMERIC-REFUSED -- a "rows" family value containing a non-numeral
                                     element -- refused.
  MALFORMED-EXCLUSIONS-NOT-ARRAY-REFUSED        -- scope_exclusions not a jsonb array at all --
                                     refused.
  MALFORMED-EXCLUSIONS-EXTRA-KEY-REFUSED        -- an exclusion object carrying a third key --
                                     refused (closed {family,value} shape).
  WELL-FORMED-ALL-THREE-DISCLOSURE-MODES-ACCEPTED -- marked/hash_stub/full all representable
                                     from birth (spec sec1c) -- three separate bindings, each
                                     accepted.
  ZERO-FRICTION-BIRTH                  -- a fresh classic scaffold's birth sequence through s70,
                                     unaffected -- zero new friction from a ninth act-class token
                                     with no birth-sequence act of its own.
  VERIFY-CHAIN-INTACT-THROUGH-REFUSALS -- ./autoharn verify-chain INTACT + refusal-oracle
                                     CONFIRMED, after every refusal above.
  AGREE-sql-asp-work-differential      -- judge --layer work SQL/ASP AGREE on the s70-head world
                                     (chain-reachability, generic over act class, unchanged by
                                     this delta -- s62/s64's own "no new predicate" claim
                                     re-verified one token further). NO differential exists for
                                     principal_scopes' OWN family (surfaces/exclusions/disclosure
                                     mode) -- UNEXERCISED, flagged as the engine-side follow-on
                                     this delta's own header names, never silently claimed AGREE.

Usage: python3 seen-red/s70-scope-binding/run_fixtures.py
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
sys.path.insert(0, str(REPO / "filing"))
from pghost_resolve import resolve_pghost  # noqa: E402

os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S69 = [
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
]
CHAIN_S70 = CHAIN_S69 + ["s70-scope-binding.sql"]


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    # PGOPTIONS is stripped for every subprocess this fixture spawns: this agent's own shell
    # runs under hooks/stamp_intercept.py, which injects app.vendor_* GUCs (a valid HMAC keyed
    # to THIS PROJECT's own deployment secret) into PGOPTIONS ahead of every Bash-tool command.
    # A freshly scaffolded scratch world's own kernel.stamp_secret is a FRESH random value
    # (scaffold_classic's own genesis/stamp-secret step below), so that inherited GUC would be
    # PRESENT-but-INVALID against the scratch world -- s17's set_stamp trigger REFUSES a present-
    # but-invalid stamp outright (never silently accepts it), which is a real, once-witnessed
    # failure mode of this exact fixture (see this file's own build report). The correct fixture
    # posture is the SAME one every prior seen-red/*/run_fixtures.py assumes when run from a
    # plain, non-intercepted shell: NO app.vendor_* GUCs at all, which set_stamp's own ELSE
    # branch records as stamp_verified=false and ACCEPTS (unstamped, non-intercepted path) --
    # never refused. Stripping PGOPTIONS here reproduces that plain-shell precondition
    # mechanically rather than depending on the invoking shell happening to lack the hook.
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


def bw_call(world: str, fn: str, payload: dict) -> dict:
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    pj = json.dumps(payload).replace("'", "''")
    r = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"],
           input=f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
                 f"SELECT to_jsonb(v) FROM {K}.{fn}('{pj}'::jsonb) v;\n")
    if r.returncode != 0:
        raise RuntimeError(f"NON-VERDICT: {r.stderr.strip()[-800:]}")
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
                                "purpose": "s70 fixture's own write-boundary registration"}),
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
             "print(r.verdict())\n"
             "print('asp', sorted(r.asp.atoms))\n"
             "print('sql', sorted(r.sql.atoms))\n"],
            env=env, cwd=str(REPO))
    if cp.returncode != 0:
        raise RuntimeError(f"judge programmatic call failed ({world}): {cp.stderr}")
    out = cp.stdout.strip().splitlines()
    check(label, bool(out) and out[0] == "AGREE", f"judge output ({world}): {out}", failures)


def main() -> int:  # noqa: C901
    failures: list[str] = []
    tmps: list[Path] = []
    world_pre, world_main, world_birth = "s70fxpre", "s70fxmain", "s70fxbirth"
    for w in (world_pre, world_main, world_birth):
        teardown(w)
    try:
        # ===================== WORLD PRE (s69 head, NO s70) =====================
        print(f"== scaffolding classic world {world_pre} (chain ends {CHAIN_S69[-1]}, NO s70) ==")
        wp = scaffold_classic(world_pre, CHAIN_S69)
        tmps.append(wp.parent)

        d_pre = detect(world_pre, "s70-scope-binding.detect.sql")
        check("REGRESSION-DETECT-ABSENT", d_pre == "f",
              f"s70-scope-binding.detect.sql on the s69-head world (no s70 applied): {d_pre!r} "
              f"(expected f)", failures)

        author_pre = birth_via_boundary(world_pre)
        v_note_pre = bw_call(world_pre, "ledger_write",
                              {"kind": "note", "statement": "ordinary note, pre-s70",
                               "actor": author_pre})
        check("REGRESSION-ORDINARY-WRITE-UNAFFECTED",
              v_note_pre["disposition"] == "accepted",
              f"an ordinary note write on the s69-head (pre-s70) world -- ACCEPTED, unaffected "
              f"by this delta's mere existence -- verdict={v_note_pre}", failures)

        # ===================== WORLD MAIN (s70 head) =====================
        print(f"== scaffolding classic world {world_main} (chain ends {CHAIN_S70[-1]}) ==")
        wm = scaffold_classic(world_main, CHAIN_S70)
        tmps.append(wm.parent)

        d_main = detect(world_main, "s70-scope-binding.detect.sql")
        check("REGRESSION-DETECT-PRESENT", d_main == "t",
              f"s70-scope-binding.detect.sql on the s70-head world: {d_main!r} (expected t)",
              failures)

        author = birth_via_boundary(world_main)
        outsider = register(world_main, author, "outsider")  # NO acts-for edge -- chainless.

        # ---- OPEN-SCOPE-DEFAULT-FOR-NEVER-BOUND (checked BEFORE any binding exists) ----
        rows_never = psql_tuples(
            f"SELECT count(*) FROM {world_main}.principal_scopes WHERE subject = {author};")
        check("OPEN-SCOPE-DEFAULT-FOR-NEVER-BOUND",
              rows_never == "0",
              f"a principal (author, id {author}) with no principal_scope_bound row of its own "
              f"has ZERO rows in principal_scopes -- the structural, fail-safe open-scope "
              f"default (an absent row, never an explicit 'unrestricted' marker) -- rows="
              f"{rows_never}", failures)

        # ---- GREEN-SCOPE-BIND-UNENTITLED-REFUSED (conjunct b, checked BEFORE any legitimate
        # bind exists, so the ONLY principal_scope_bound row in this world so far is the one
        # attempted here, refused) ----
        v_unentitled = bw_call(world_main, "ledger_write",
                                {"kind": "principal_scope_bound",
                                 "statement": "outsider tries to scope-bind itself",
                                 "actor": outsider, "principal_subject": outsider,
                                 "principal_binding_active": "true",
                                 "scope_surfaces": ["ledger_current"],
                                 "scope_disclosure_mode": "marked"})
        check("GREEN-SCOPE-BIND-UNENTITLED-REFUSED",
              v_unentitled["disposition"] == "refused"
              and "does not reach this world" in (v_unentitled["message"] or ""),
              f"a chainless, roleless principal (outsider) attempting to bind ITS OWN scope is "
              f"REFUSED on conjunct (b) -- scope_binding is authority-bearing, unconditionally -- "
              f"verdict={v_unentitled}", failures)

        # ---- GREEN-SCOPE-BIND-ENTITLED-ACCEPTED ----
        v_bind = bw_call(world_main, "ledger_write",
                          {"kind": "principal_scope_bound",
                           "statement": "author binds its own scope",
                           "actor": author, "principal_subject": author,
                           "principal_binding_active": "true",
                           "scope_surfaces": ["ledger_current", "work_item_current"],
                           "scope_exclusions": [{"family": "kind-class", "value": "belief"}],
                           "scope_disclosure_mode": "marked"})
        check("GREEN-SCOPE-BIND-ENTITLED-ACCEPTED",
              v_bind["disposition"] == "accepted",
              f"the genesis-chained actor (author) binds a scope to itself -- ACCEPTED (conjunct "
              f"b: author trivially chain-reaches genesis, the s60 Element 6 base case) -- "
              f"verdict={v_bind}", failures)

        rendered = psql_tuples(
            f"SELECT scope_surfaces, scope_disclosure_mode FROM {world_main}.principal_scopes "
            f"WHERE subject = {author};")
        check("GREEN-SCOPE-BIND-RENDERED-IN-VIEW",
              "ledger_current" in rendered and "marked" in rendered,
              f"principal_scopes renders the bound scope for author -- row: {rendered!r}",
              failures)

        # ---- GREEN-SCOPE-SEVERANCE-CROSS-KIND-REFUSED (the s62-round-2 cross-kind severance
        # vessel, one token further: an unrelated candidate kind (note) superseding the LIVE
        # principal_scope_bound row above, written by a chainless actor) ----
        v_sever = bw_call(world_main, "ledger_write",
                           {"kind": "note", "statement": "outsider tries to sever author's scope",
                            "supersedes": v_bind["row_id"], "actor": outsider})
        check("GREEN-SCOPE-SEVERANCE-CROSS-KIND-REFUSED",
              v_sever["disposition"] == "refused"
              and "does not reach this world" in (v_sever["message"] or ""),
              f"a chainless actor (outsider) superseding the LIVE principal_scope_bound row with "
              f"an UNRELATED kind (note) is REFUSED via the target-class conjunct "
              f"(entitlement_act_class_of_target classifies the target as scope_binding) -- "
              f"verdict={v_sever}", failures)

        # ---- HAPPY-SCOPE-REBIND-BY-ENTITLED (the SAME entitled actor rotates its own binding) ----
        v_rebind = bw_call(world_main, "ledger_write",
                            {"kind": "principal_scope_bound",
                             "statement": "author rotates its own scope",
                             "supersedes": v_bind["row_id"],
                             "actor": author, "principal_subject": author,
                             "principal_binding_active": "true",
                             "scope_surfaces": ["ledger_current"],
                             "scope_disclosure_mode": "hash_stub"})
        check("HAPPY-SCOPE-REBIND-BY-ENTITLED",
              v_rebind["disposition"] == "accepted",
              f"author (entitled) rotates its OWN scope binding -- ACCEPTED -- verdict={v_rebind}",
              failures)
        rendered2 = psql_tuples(
            f"SELECT scope_disclosure_mode FROM {world_main}.principal_scopes "
            f"WHERE subject = {author};")
        check("HAPPY-SCOPE-REBIND-RENDERS-ROTATED-PAYLOAD",
              rendered2 == "hash_stub",
              f"principal_scopes now renders the ROTATED disclosure mode ({rendered2!r}), not "
              f"the original ('marked') -- supersession-aware, s31's own uniform retraction",
              failures)

        # ---- HAPPY-SCOPE-UNBIND-RESTORES-OPEN-DEFAULT ----
        v_unbind = bw_call(world_main, "ledger_write",
                            {"kind": "principal_scope_bound",
                             "statement": "author unbinds its own scope",
                             "supersedes": v_rebind["row_id"],
                             "actor": author, "principal_subject": author,
                             "principal_binding_active": "false"})
        check("HAPPY-SCOPE-UNBIND-ACCEPTED",
              v_unbind["disposition"] == "accepted",
              f"author unbinds (retracts) its own scope -- ACCEPTED -- verdict={v_unbind}",
              failures)
        rows_after_unbind = psql_tuples(
            f"SELECT count(*) FROM {world_main}.principal_scopes WHERE subject = {author};")
        check("HAPPY-SCOPE-UNBIND-RESTORES-OPEN-DEFAULT",
              rows_after_unbind == "0",
              f"after the unbind, author has ZERO rows in principal_scopes -- restored to the "
              f"OPEN scope default, structurally (not a lingering 'unrestricted' marker row) -- "
              f"rows={rows_after_unbind}", failures)

        # ---- MALFORMED VOCABULARY, each arm refused with a teach-text (all as the ENTITLED
        # actor, so every refusal below is a SHAPE refusal, never conjunct a/b) ----
        v_bad_mode = bw_call(world_main, "ledger_write",
                              {"kind": "principal_scope_bound",
                               "statement": "malformed disclosure mode",
                               "actor": author, "principal_subject": author,
                               "principal_binding_active": "true",
                               "scope_disclosure_mode": "bogus"})
        check("MALFORMED-DISCLOSURE-MODE-REFUSED",
              v_bad_mode["disposition"] == "refused",
              f"scope_disclosure_mode='bogus' -- REFUSED (closed 3-member CHECK) -- "
              f"verdict={v_bad_mode}", failures)

        v_bad_family = bw_call(world_main, "ledger_write",
                                {"kind": "principal_scope_bound",
                                 "statement": "malformed exclusion family",
                                 "actor": author, "principal_subject": author,
                                 "principal_binding_active": "true",
                                 "scope_exclusions": [{"family": "not-a-real-family", "value": "x"}]})
        check("MALFORMED-EXCLUSIONS-BAD-FAMILY-REFUSED",
              v_bad_family["disposition"] == "refused",
              f"scope_exclusions family outside the closed four-member vocabulary -- REFUSED -- "
              f"verdict={v_bad_family}", failures)

        v_bad_rows = bw_call(world_main, "ledger_write",
                              {"kind": "principal_scope_bound",
                               "statement": "malformed rows family",
                               "actor": author, "principal_subject": author,
                               "principal_binding_active": "true",
                               "scope_exclusions": [{"family": "rows", "value": ["not-a-number"]}]})
        check("MALFORMED-EXCLUSIONS-ROWS-NOT-NUMERIC-REFUSED",
              v_bad_rows["disposition"] == "refused",
              f"scope_exclusions 'rows' family carrying a non-numeral element -- REFUSED -- "
              f"verdict={v_bad_rows}", failures)

        v_not_array = bw_call(world_main, "ledger_write",
                               {"kind": "principal_scope_bound",
                                "statement": "malformed top-level shape",
                                "actor": author, "principal_subject": author,
                                "principal_binding_active": "true",
                                "scope_exclusions": {"family": "thread", "value": "x"}})
        check("MALFORMED-EXCLUSIONS-NOT-ARRAY-REFUSED",
              v_not_array["disposition"] == "refused",
              f"scope_exclusions not a jsonb ARRAY at all (a bare object) -- REFUSED -- "
              f"verdict={v_not_array}", failures)

        v_extra_key = bw_call(world_main, "ledger_write",
                               {"kind": "principal_scope_bound",
                                "statement": "malformed extra key",
                                "actor": author, "principal_subject": author,
                                "principal_binding_active": "true",
                                "scope_exclusions": [{"family": "thread", "value": "t1", "extra": "nope"}]})
        check("MALFORMED-EXCLUSIONS-EXTRA-KEY-REFUSED",
              v_extra_key["disposition"] == "refused",
              f"scope_exclusions element carrying a THIRD key beyond {{family,value}} -- "
              f"REFUSED -- verdict={v_extra_key}", failures)

        # ---- WELL-FORMED-ALL-THREE-DISCLOSURE-MODES-ACCEPTED (spec sec1c: all three
        # representable from birth) ----
        modes_ok = True
        modes_detail = []
        for i, mode in enumerate(("marked", "hash_stub", "full")):
            v_mode = bw_call(world_main, "ledger_write",
                              {"kind": "principal_scope_bound",
                               "statement": f"disclosure-mode-witness-{mode}",
                               "actor": author, "principal_subject": author,
                               "principal_binding_active": "true",
                               "scope_disclosure_mode": mode,
                               "scope_surfaces": [f"probe-surface-{i}"]})
            modes_detail.append((mode, v_mode["disposition"]))
            modes_ok = modes_ok and v_mode["disposition"] == "accepted"
        check("WELL-FORMED-ALL-THREE-DISCLOSURE-MODES-ACCEPTED", modes_ok,
              f"marked/hash_stub/full each independently accepted -- {modes_detail}", failures)

        # ---- REFUSALS-JOURNAL-AS-WRITE-REFUSED ----
        refused = (v_unentitled, v_sever, v_bad_mode, v_bad_family, v_bad_rows, v_not_array,
                   v_extra_key)
        refused_ids = [v["refusal_id"] for v in refused if v.get("refusal_id")]
        journaled = psql_tuples(
            f"SELECT count(*) FROM {world_main}.ledger WHERE kind='write_refused' "
            f"AND id IN ({','.join(str(i) for i in refused_ids)});") if refused_ids else "0"
        check("REFUSALS-JOURNAL-AS-WRITE-REFUSED",
              len(refused_ids) == len(refused) and journaled == str(len(refused)),
              f"every s70 refusal above journals as a committed write_refused row -- "
              f"{len(refused_ids)} refusal ids, {journaled} found as write_refused rows",
              failures)

        # ---- ZERO-FRICTION-BIRTH ----
        print(f"== scaffolding classic world {world_birth} (chain ends {CHAIN_S70[-1]}, fresh "
              f"birth) ==")
        wb = scaffold_classic(world_birth, CHAIN_S70)
        tmps.append(wb.parent)
        author_birth = birth_via_boundary(world_birth)
        v_birth_ok = bw_call(world_birth, "ledger_write",
                              {"kind": "note", "statement": "zero-friction birth note",
                               "actor": author_birth})
        check("ZERO-FRICTION-BIRTH-accepted",
              v_birth_ok["disposition"] == "accepted",
              f"a fresh world's own s40/s43/s70 birth sequence, then an ordinary note write -- "
              f"ACCEPTED, no extra friction from this delta's ninth act-class token (no "
              f"birth-sequence act of its own, Element 8's own note) -- verdict={v_birth_ok}",
              failures)

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

        # ---- AGREE: SQL/ASP work-layer differential (chain-reachability, generic over act
        # class -- unchanged by this delta, s62/s64's own "no new predicate needed" claim
        # re-verified one token further; NOT a claim about principal_scopes' own family, which
        # has no ASP export at all -- see this fixture's own module docstring). ----
        judge_agree(world_main, failures, "AGREE-sql-asp-work-differential")
        print("NOTE: no differential covers principal_scopes' own family (scope_surfaces/"
              "scope_exclusions/scope_disclosure_mode) -- engine/ledger_edb.py exports no scope "
              "facts and engine/lp/ledger_entitlement.lp derives no scope-specific predicate. "
              "UNEXERCISED, flagged as the engine-side follow-on this delta's own header names, "
              "never silently claimed AGREE for that family.")

    finally:
        for w in (world_pre, world_main, world_birth):
            teardown(w)
        for t in tmps:
            sh(["rm", "-rf", str(t)])

    print(f"\n{'ALL GREEN' if not failures else 'FAILURES: ' + ', '.join(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
