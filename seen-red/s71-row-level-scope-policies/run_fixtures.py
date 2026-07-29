#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s71-row-level-scope-policies.sql
(design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §2/§5 item 6, "the RLS slot"). Real
infra, no mocks: a CLASSIC scaffold (bootstrap/new-project.sh, the real --new-world path, which
now ALWAYS runs the S2b split -- 0e2eda39) plus a RAW (non-scaffold, no S2b split) scratch chain
applied directly, both torn down before AND after. Modeled directly on
seen-red/s70-scope-binding/run_fixtures.py (scaffold_classic/birth_via_boundary/bw_call/detect/
judge_agree helpers, same shape).

FIXTURE FAMILY CHOICE: a NEW sibling family -- s71 mints Postgres ROW LEVEL SECURITY machinery
no existing family's own RED/GREEN pair covers.

THE HONEST-BOUND WITNESS (this fixture's own reason for existing, beyond the ordinary RED/GREEN
ceremony): this delta's header states a PRECISE claim about when its policy is inert, narrower
than the folklore "no S2b split ran" -- Postgres's RLS bypass fires for the ACTUAL RELATION
OWNER (and a real superuser), never for a merely-GRANTED role, split or not. This fixture
WITNESSES that precise claim directly rather than assuming it: on a RAW, non-split world, the
SAME armed exclusion is (a) INERT for the identity that owns the schema (the connecting DDL
identity) and (b) NOT INERT for a distinct granted-only role in that SAME non-split world --
proving "inert" tracks owner-identity, not split-status, exactly as the delta's header discloses.

WORLD PRE (s70 head, NO s71):
  REGRESSION-DETECT-ABSENT       -- s71-row-level-scope-policies.detect.sql reports 'f' (absent).
  REGRESSION-ORDINARY-READ-UNAFFECTED -- an ordinary SELECT as :role, unaffected by this delta's
                                     mere existence (no RLS enabled at all pre-s71).

WORLD MAIN (s71 head, CLASSIC scaffold -- split, per 0e2eda39's now-unconditional S2b block):
  REGRESSION-DETECT-PRESENT      -- s71-row-level-scope-policies.detect.sql reports 't'.
  UNARMED-BYTE-IDENTICAL-NO-GUC        -- :role with NO app.scope_principal GUC set reads the
                                     SAME row count as the schema owner -- unarmed fail-safe.
  UNARMED-BYTE-IDENTICAL-NEVER-BOUND   -- :role with the GUC set to a principal who holds no
                                     principal_scopes row reads the SAME full count -- the open-
                                     scope fail-safe default, one layer over from s70's own.
  ARMED-KIND-CLASS-EXCLUSION-FILTERS   -- :role with the GUC set to a principal whose bound scope
                                     excludes kind-class 'note' sees ZERO 'note' rows, while an
                                     UNEXCLUDED kind (finding) is unaffected.
  ARMED-ROWS-FAMILY-EXCLUDES-EXACT-ROW -- a SEPARATE scope excluding an explicit "rows" id hides
                                     exactly that row, no other.
  MALFORMED-GUC-FAILS-OPEN             -- app.scope_principal set to a non-numeral value reads
                                     the full, unfiltered count (fail OPEN, never a hard error).
  SPLIT-OWNER-BYPASSES-POLICY          -- SET ROLE to the split's own non-login $OWNER (a
                                     superuser session can SET ROLE to any role) reads every row
                                     regardless of an armed, excluding GUC bound to that identity
                                     -- the table-owner bypass, unforced, exactly this delta's
                                     own ELEMENT 2 disclosure.
  WRITE-PATH-UNAFFECTED                -- an ordinary note write (through the owner-run SECURITY
                                     DEFINER path) still succeeds after RLS is enabled -- no
                                     INSERT/UPDATE/DELETE policy exists, and the write path never
                                     runs as :role in the first place (s43's own REVOKE).
  VERIFY-CHAIN-INTACT                  -- ./autoharn verify-chain INTACT after every act above.
  AGREE-sql-asp-work-differential      -- judge --layer work SQL/ASP AGREE, unchanged (this delta
                                     touches no entitlement/kind/column surface at all).

WORLD LEGACY (RAW scratch chain s15..s71, NO S2b split -- applied by direct psql -f, exactly the
pre-S2b shape: the connecting DDL identity owns the schema, :role is CREATEd and GRANTed only,
never made owner, matching 0e2eda39's own "that is NOT what happens today" -- pre-split -- note):
  LEGACY-DETECT-PRESENT                -- s71's detect reports 't' (the delta itself applies
                                     cleanly whether or not S2b ever ran -- FAIL-SAFE-ADDITIVE
                                     is unconditional).
  LEGACY-OWNER-IDENTITY-INERT          -- read AS THE SCHEMA-OWNING CONNECTING IDENTITY, with the
                                     SAME armed, excluding GUC bound to that identity's own
                                     principal -- FULL, unfiltered count. THE literal "connecting
                                     role owns the schema... policies inert" configuration this
                                     delta's header names, witnessed directly.
  LEGACY-GRANTED-ROLE-NOT-INERT        -- the SAME armed GUC, read instead as the raw world's
                                     OWN granted-only role (:role, never the owner even here) --
                                     FILTERS, exactly as WORLD MAIN's ARMED case did. Proves
                                     inertness tracks owner-IDENTITY, never "no split ran" alone.

Usage: python3 seen-red/s71-row-level-scope-policies/run_fixtures.py
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

CHAIN_S70 = [
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
]
CHAIN_S71 = CHAIN_S70 + ["s71-row-level-scope-policies.sql"]


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    # PGOPTIONS stripped for every subprocess -- see seen-red/s70-scope-binding/run_fixtures.py's
    # own identical note (hooks/stamp_intercept.py injects app.vendor_* into PGOPTIONS ahead of
    # every Bash-tool command; a fresh scratch world's own kernel.stamp_secret is unrelated
    # random, so an inherited GUC would be present-but-invalid and get refused rather than
    # accepted-unstamped).
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


def psql_as_role(role: str | None, sql: str) -> str:
    """Run SQL in a session that first SET ROLEs (peer/trust superuser connects, then switches
    identity) -- the same technique bw_call uses for definer-function calls, generalized to a
    bare SELECT so this fixture can read `ledger` AS a specific (possibly non-login) identity."""
    preamble = f"SET ROLE {role};\n" if role else ""
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"],
            input=f"{preamble}{sql}\n")
    if cp.returncode != 0:
        raise RuntimeError(f"psql_as_role({role}) failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
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


def scaffold_new_world(world: str) -> Path:
    """A REAL --new-world birth (bootstrap/new-project.sh's own FULL_LINEAGE=1 path): applies
    every kernel/lineage/sNN delta through the live directory's own current head (picking up
    THIS delta automatically via the live glob, no separate -f loop needed here), runs the s40
    birth sequence itself (author registration/standing declaration/reviewer ceremony), AND runs
    the S2b three-identity split (0e2eda39) unconditionally. Used ONLY for the ONE check that
    genuinely needs a real, split-owned world (SPLIT-OWNER-BYPASSES-POLICY) -- every other check
    in this fixture uses the lighter manual-chain-apply scaffold_classic/scaffold_raw helpers
    (the s70 fixture's own precedent), which do NOT exercise FULL_LINEAGE and so do NOT split."""
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", world,
            "--db", PGDB, "--host", PGHOST])
    if r.returncode != 0:
        raise RuntimeError(f"NEW-WORLD SCAFFOLD FAILED ({world}): {r.stdout[-2000:]} {r.stderr[-2000:]}")
    return world_dir


def scaffold_raw(world: str, chain: list[str]) -> None:
    """The RAW, non-CLASSIC scratch apply: schema+kern created and populated by whichever
    identity peer/trust-authenticates this psql connection (the SAME 'Run as the schema owner
    (bork)' identity kernel/lineage/s15-schema.sql's own header names) -- NO S2b split block runs
    (that block lives in bootstrap/new-project.sh, never invoked here). This IS the literal
    pre-S2b shape: the connecting DDL identity owns schema+kern+every relation/function inside
    them; :role is CREATEd LOGIN and merely GRANTed, exactly s15's own ISOLATION GRANTS note,
    never made an owner of anything."""
    schema, kern, role = world, f"{world}_kernel", f"{world}_rw"
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"CREATE ROLE {role} LOGIN;"])
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for name in chain:
        args += ["-f", str(LINEAGE / name)]
    ra = sh(args)
    if ra.returncode != 0:
        raise RuntimeError(f"RAW apply FAILED ({world}): {ra.stdout[-1500:]} {ra.stderr[-1500:]}")
    genesis_hex = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis_hex}') "
              f"ON CONFLICT (only_one) DO NOTHING;"])


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
                                "purpose": "s71 fixture's own write-boundary registration"}),
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
    world_pre, world_main = "s71fxpre", "s71fxmain"
    world_split, world_legacy = "s71fxsplit", "s71fxlegacy"
    for w in (world_pre, world_main, world_split):
        teardown(w)
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP OWNED BY {world_split}_owner; DROP ROLE IF EXISTS {world_split}_owner;"])
    teardown(world_legacy)
    try:
        # ===================== WORLD PRE (s70 head, NO s71) =====================
        print(f"== scaffolding classic world {world_pre} (chain ends {CHAIN_S70[-1]}, NO s71) ==")
        wp = scaffold_classic(world_pre, CHAIN_S70)
        tmps.append(wp.parent)

        d_pre = detect(world_pre, "s71-row-level-scope-policies.detect.sql")
        check("REGRESSION-DETECT-ABSENT", d_pre == "f",
              f"s71-row-level-scope-policies.detect.sql on the s70-head world (no s71 applied): "
              f"{d_pre!r} (expected f)", failures)

        author_pre = birth_via_boundary(world_pre)
        bw_call(world_pre, "ledger_write",
                {"kind": "note", "statement": "ordinary note, pre-s71", "actor": author_pre})
        n_pre = psql_as_role(f"{world_pre}_rw",
                              f"SELECT count(*) FROM {world_pre}.ledger;")
        n_pre_owner = psql_tuples(f"SELECT count(*) FROM {world_pre}.ledger;")
        check("REGRESSION-ORDINARY-READ-UNAFFECTED", n_pre == n_pre_owner,
              f"a pre-s71 world has no RLS at all -- :role's own read count ({n_pre}) matches "
              f"the owner's ({n_pre_owner})", failures)

        # ===================== WORLD MAIN (s71 head, CLASSIC/split) =====================
        print(f"== scaffolding classic world {world_main} (chain ends {CHAIN_S71[-1]}) ==")
        wm = scaffold_classic(world_main, CHAIN_S71)
        tmps.append(wm.parent)

        d_main = detect(world_main, "s71-row-level-scope-policies.detect.sql")
        check("REGRESSION-DETECT-PRESENT", d_main == "t",
              f"s71-row-level-scope-policies.detect.sql on the s71-head world: {d_main!r} "
              f"(expected t)", failures)

        author = birth_via_boundary(world_main)
        reviewer = register(world_main, author, "reviewer")
        rowsprincipal = register(world_main, author, "rowsprincipal")

        # Ordinary content: two 'note' rows, one 'finding' row (an ordinary write, no scope
        # binding involved yet).
        v_note1 = bw_call(world_main, "ledger_write",
                           {"kind": "note", "statement": "note one", "actor": author})
        check("NOTE1-ACCEPTED", v_note1["disposition"] == "accepted",
              f"ordinary note write -- verdict={v_note1}", failures)
        bw_call(world_main, "ledger_write", {"kind": "note", "statement": "note two",
                                              "actor": author})
        v_finding = bw_call(world_main, "ledger_write",
                             {"kind": "finding", "statement": "an unrelated finding",
                              "actor": author, "concern": "other"})
        check("FINDING-ACCEPTED", v_finding["disposition"] == "accepted",
              f"ordinary finding write -- verdict={v_finding}", failures)
        note_row_id = v_note1["row_id"]
        finding_row_id = v_finding["row_id"]

        owner_note_count = psql_tuples(
            f"SELECT count(*) FROM {world_main}.ledger WHERE kind='note';")
        owner_full_count = psql_tuples(f"SELECT count(*) FROM {world_main}.ledger;")

        # ---- UNARMED-BYTE-IDENTICAL-NO-GUC ----
        role_full_no_guc = psql_as_role(f"{world_main}_rw",
                                         f"SELECT count(*) FROM {world_main}.ledger;")
        check("UNARMED-BYTE-IDENTICAL-NO-GUC", role_full_no_guc == owner_full_count,
              f":role with NO app.scope_principal GUC set reads {role_full_no_guc} rows, "
              f"the owner's own full count {owner_full_count} -- byte-identical, unarmed",
              failures)

        # ---- UNARMED-BYTE-IDENTICAL-NEVER-BOUND (GUC set, but to a principal with NO bound
        # scope -- outsider, in the s70-sense: never scope-bound at all). registration itself
        # writes a principal_registered row, so the "expected" full count is read FRESH, right
        # before the comparison, never a stale snapshot taken before that registration. ----
        outsider = register(world_main, author, "outsider")
        owner_full_count_2 = psql_tuples(f"SELECT count(*) FROM {world_main}.ledger;")
        role_full_never_bound = psql_as_role(
            f"{world_main}_rw",
            f"SET app.scope_principal = '{outsider}';\n"
            f"SELECT count(*) FROM {world_main}.ledger;")
        check("UNARMED-BYTE-IDENTICAL-NEVER-BOUND", role_full_never_bound == owner_full_count_2,
              f":role with the GUC set to a NEVER-scope-bound principal ({outsider}) reads "
              f"{role_full_never_bound} rows, the owner's OWN fresh full count "
              f"{owner_full_count_2} -- the s70 open-scope fail-safe default, one layer over",
              failures)

        # ---- ARM the reviewer's scope: exclude kind-class 'note' ----
        v_scope = bw_call(world_main, "ledger_write",
                           {"kind": "principal_scope_bound",
                            "statement": "author binds reviewer's scope (excludes notes)",
                            "actor": author, "principal_subject": reviewer,
                            "principal_binding_active": "true",
                            "scope_surfaces": ["ledger_current"],
                            "scope_exclusions": [{"family": "kind-class", "value": "note"}],
                            "scope_disclosure_mode": "marked"})
        check("SCOPE-BIND-FOR-EXCLUSION-ACCEPTED", v_scope["disposition"] == "accepted",
              f"author (genesis-chained) binds a scope onto reviewer excluding kind-class "
              f"'note' -- verdict={v_scope}", failures)

        # ---- ARMED-KIND-CLASS-EXCLUSION-FILTERS ----
        role_note_count_armed = psql_as_role(
            f"{world_main}_rw",
            f"SET app.scope_principal = '{reviewer}';\n"
            f"SELECT count(*) FROM {world_main}.ledger WHERE kind='note';")
        role_finding_count_armed = psql_as_role(
            f"{world_main}_rw",
            f"SET app.scope_principal = '{reviewer}';\n"
            f"SELECT count(*) FROM {world_main}.ledger WHERE kind='finding';")
        owner_finding_count = psql_tuples(
            f"SELECT count(*) FROM {world_main}.ledger WHERE kind='finding';")
        check("ARMED-KIND-CLASS-EXCLUSION-FILTERS",
              role_note_count_armed == "0" and role_finding_count_armed == owner_finding_count,
              f"reviewer's GUC armed: 'note' rows read as :role = {role_note_count_armed} "
              f"(owner sees {owner_note_count}), 'finding' rows unaffected "
              f"({role_finding_count_armed} == owner's {owner_finding_count})", failures)

        # ---- ARM a second scope on rowsprincipal: exclude the exact finding row by id ----
        v_scope_rows = bw_call(world_main, "ledger_write",
                                {"kind": "principal_scope_bound",
                                 "statement": "author binds rowsprincipal's scope (excludes one row)",
                                 "actor": author, "principal_subject": rowsprincipal,
                                 "principal_binding_active": "true",
                                 "scope_surfaces": ["ledger_current"],
                                 "scope_exclusions": [{"family": "rows",
                                                        "value": [finding_row_id]}],
                                 "scope_disclosure_mode": "marked"})
        check("ROWS-SCOPE-BIND-ACCEPTED", v_scope_rows["disposition"] == "accepted",
              f"author binds rowsprincipal's scope excluding row id {finding_row_id} -- "
              f"verdict={v_scope_rows}", failures)

        role_that_row = psql_as_role(
            f"{world_main}_rw",
            f"SET app.scope_principal = '{rowsprincipal}';\n"
            f"SELECT count(*) FROM {world_main}.ledger WHERE id={finding_row_id};")
        role_other_row = psql_as_role(
            f"{world_main}_rw",
            f"SET app.scope_principal = '{rowsprincipal}';\n"
            f"SELECT count(*) FROM {world_main}.ledger WHERE id={note_row_id};")
        check("ARMED-ROWS-FAMILY-EXCLUDES-EXACT-ROW",
              role_that_row == "0" and role_other_row == "1",
              f"rowsprincipal's GUC armed: the excluded row {finding_row_id} reads "
              f"{role_that_row} (expected 0); an unexcluded row {note_row_id} reads "
              f"{role_other_row} (expected 1)", failures)

        # ---- MALFORMED-GUC-FAILS-OPEN (fresh full-count comparison -- several writes have
        # happened since owner_full_count/owner_full_count_2 were captured, e.g. the two scope
        # binds above) ----
        owner_full_count_3 = psql_tuples(f"SELECT count(*) FROM {world_main}.ledger;")
        role_malformed = psql_as_role(
            f"{world_main}_rw",
            f"SET app.scope_principal = 'not-a-number';\n"
            f"SELECT count(*) FROM {world_main}.ledger;")
        check("MALFORMED-GUC-FAILS-OPEN", role_malformed == owner_full_count_3,
              f"a non-numeral app.scope_principal ('not-a-number') reads {role_malformed} rows, "
              f"the owner's OWN fresh full count {owner_full_count_3} -- fails OPEN, never a "
              f"hard error", failures)

        # ---- WRITE-PATH-UNAFFECTED ----
        v_after = bw_call(world_main, "ledger_write",
                           {"kind": "note", "statement": "a note written after RLS is armed",
                            "actor": author})
        check("WRITE-PATH-UNAFFECTED", v_after["disposition"] == "accepted",
              f"an ordinary write via the owner-run SECURITY DEFINER path after RLS is enabled "
              f"and a policy is armed -- still ACCEPTED (writes never run as :role, s43's own "
              f"REVOKE; no INSERT/UPDATE/DELETE policy exists on this table at all) -- "
              f"verdict={v_after}", failures)

        # ---- VERIFY-CHAIN-INTACT ----
        rc_v, out_v = verify_chain(wm)
        check("VERIFY-CHAIN-INTACT", rc_v == 0 and "INTACT" in out_v,
              f"./autoharn verify-chain after every act above -- exit={rc_v}, "
              f"INTACT in output={'INTACT' in out_v}", failures)

        # ---- AGREE: SQL/ASP work-layer differential (unchanged by this delta -- no
        # entitlement/kind/column surface touched at all; RLS/row-visibility has no ASP twin,
        # UNEXERCISED, this delta's own header LIMITS section, never silently claimed AGREE) ----
        judge_agree(world_main, failures, "AGREE-sql-asp-work-differential")

        # ===================== WORLD SPLIT (REAL --new-world birth, S2b split) =====================
        # A dedicated, genuinely split world (see scaffold_new_world's own header) for the ONE
        # check that needs a real, non-login $OWNER distinct from :role -- world_main above uses
        # the lighter manual-chain-apply scaffold (the s70 fixture's own precedent), which does
        # NOT exercise bootstrap/new-project.sh's FULL_LINEAGE=1 path and so does NOT split.
        print(f"== scaffolding REAL --new-world (split) world {world_split} ==")
        ws = scaffold_new_world(world_split)
        tmps.append(ws.parent)

        d_split = detect(world_split, "s71-row-level-scope-policies.detect.sql")
        check("SPLIT-DETECT-PRESENT", d_split == "t",
              f"s71-row-level-scope-policies.detect.sql on the real --new-world (split) birth: "
              f"{d_split!r} (expected t)", failures)

        owner_role = f"{world_split}_owner"
        actual_owner = psql_tuples(
            f"SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname='{world_split}';")
        check("SPLIT-SCHEMA-OWNED-BY-DEDICATED-ROLE", actual_owner == owner_role,
              f"schema '{world_split}' is owned by {actual_owner!r} (expected the dedicated, "
              f"non-login {owner_role!r} -- 0e2eda39's own S2b split, confirming this world IS "
              f"genuinely split, not merely assumed)", failures)

        author_split = psql_tuples(
            f"SELECT id FROM {world_split}_kernel.principal WHERE name='author';")
        # --new-world's OWN birth sequence already registers 'author' -- no birth_via_boundary
        # call here (it would attempt a SECOND principal_registered for the same subject and be
        # refused as a duplicate). Two ordinary notes, then a self-excluding scope.
        bw_call(world_split, "ledger_write",
                {"kind": "note", "statement": "split-world note one", "actor": author_split})
        bw_call(world_split, "ledger_write",
                {"kind": "note", "statement": "split-world note two", "actor": author_split})
        v_split_scope = bw_call(world_split, "ledger_write",
                                 {"kind": "principal_scope_bound",
                                  "statement": "author self-excludes notes (split world)",
                                  "actor": author_split, "principal_subject": author_split,
                                  "principal_binding_active": "true",
                                  "scope_surfaces": ["ledger_current"],
                                  "scope_exclusions": [{"family": "kind-class", "value": "note"}],
                                  "scope_disclosure_mode": "marked"})
        check("SPLIT-SCOPE-BIND-ACCEPTED", v_split_scope["disposition"] == "accepted",
              f"author (genesis-chained) self-excludes 'note' in the split world -- "
              f"verdict={v_split_scope}", failures)

        split_owner_note_count = psql_tuples(
            f"SELECT count(*) FROM {world_split}.ledger WHERE kind='note';")
        split_role_note_count_armed = psql_as_role(
            f"{world_split}_rw",
            f"SET app.scope_principal = '{author_split}';\n"
            f"SELECT count(*) FROM {world_split}.ledger WHERE kind='note';")
        check("SPLIT-ROLE-FILTERS-AS-EXPECTED", split_role_note_count_armed == "0",
              f"sanity check: :role in the SPLIT world, armed against its own excluding scope, "
              f"reads {split_role_note_count_armed} 'note' rows (expected 0) -- the policy is "
              f"live on this genuinely split world too, not merely on world_main", failures)

        # ---- SPLIT-OWNER-BYPASSES-POLICY (SET ROLE to the split's own $OWNER; a superuser
        # session may SET ROLE to any role including a NOLOGIN one) ----
        owner_as_author_notes = psql_as_role(
            owner_role,
            f"SET app.scope_principal = '{author_split}';\n"
            f"SELECT count(*) FROM {world_split}.ledger WHERE kind='note';")
        check("SPLIT-OWNER-BYPASSES-POLICY", owner_as_author_notes == split_owner_note_count,
              f"reading as the split's own $OWNER ({owner_role}) with the SAME armed, "
              f"self-excluding GUC bound to author -- reads {owner_as_author_notes} 'note' "
              f"rows, the FULL unfiltered count {split_owner_note_count} -- the table-owner "
              f"bypass, unforced, this delta's own ELEMENT 2 disclosure, witnessed on a "
              f"GENUINELY split world (not merely assumed)", failures)

        # ===================== WORLD LEGACY (RAW, NO S2b split) =====================
        print(f"== scaffolding RAW (non-split) world {world_legacy} (chain ends "
              f"{CHAIN_S71[-1]}) ==")
        scaffold_raw(world_legacy, CHAIN_S71)
        connecting_identity = psql_tuples("SELECT current_user;")
        schema_owner = psql_tuples(
            f"SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname='{world_legacy}';")
        check("LEGACY-CONNECTING-IDENTITY-OWNS-SCHEMA", connecting_identity == schema_owner,
              f"RAW apply, no S2b split: the connecting DDL identity ({connecting_identity}) "
              f"IS the schema owner ({schema_owner}) -- the literal pre-split configuration",
              failures)

        d_legacy = detect(world_legacy, "s71-row-level-scope-policies.detect.sql")
        check("LEGACY-DETECT-PRESENT", d_legacy == "t",
              f"s71-row-level-scope-policies.detect.sql on the RAW non-split world: {d_legacy!r} "
              f"(expected t -- FAIL-SAFE-ADDITIVE applies unconditionally, split or not)",
              failures)

        author_legacy = birth_via_boundary(world_legacy)
        bw_call(world_legacy, "ledger_write",
                {"kind": "note", "statement": "legacy note one", "actor": author_legacy})
        bw_call(world_legacy, "ledger_write",
                {"kind": "note", "statement": "legacy note two", "actor": author_legacy})
        v_legacy_scope = bw_call(
            world_legacy, "ledger_write",
            {"kind": "principal_scope_bound",
             "statement": "author self-excludes notes (legacy world)",
             "actor": author_legacy, "principal_subject": author_legacy,
             "principal_binding_active": "true",
             "scope_surfaces": ["ledger_current"],
             "scope_exclusions": [{"family": "kind-class", "value": "note"}],
             "scope_disclosure_mode": "marked"})
        check("LEGACY-SCOPE-BIND-ACCEPTED", v_legacy_scope["disposition"] == "accepted",
              f"author (genesis-chained) self-excludes 'note' in the RAW legacy world -- "
              f"verdict={v_legacy_scope}", failures)

        legacy_owner_note_count = psql_tuples(
            f"SELECT count(*) FROM {world_legacy}.ledger WHERE kind='note';")

        # ---- LEGACY-OWNER-IDENTITY-INERT: read AS the connecting/owning identity itself ----
        legacy_as_owner = psql_as_role(
            None,
            f"SET app.scope_principal = '{author_legacy}';\n"
            f"SELECT count(*) FROM {world_legacy}.ledger WHERE kind='note';")
        check("LEGACY-OWNER-IDENTITY-INERT", legacy_as_owner == legacy_owner_note_count,
              f"reading AS the schema-owning connecting identity ({connecting_identity}), with "
              f"the SAME armed, self-excluding GUC -- reads {legacy_as_owner} 'note' rows, the "
              f"full unfiltered count {legacy_owner_note_count} -- INERT, the literal "
              f"'connecting role owns the schema' configuration this delta's header names",
              failures)

        # ---- LEGACY-GRANTED-ROLE-NOT-INERT: the SAME GUC, read as the raw world's own
        # granted-only role (never the owner, even in this non-split world) ----
        legacy_as_role = psql_as_role(
            f"{world_legacy}_rw",
            f"SET app.scope_principal = '{author_legacy}';\n"
            f"SELECT count(*) FROM {world_legacy}.ledger WHERE kind='note';")
        check("LEGACY-GRANTED-ROLE-NOT-INERT", legacy_as_role == "0",
              f"the SAME armed GUC, read instead as {world_legacy}_rw (granted, never owner, "
              f"even in this non-split RAW world) -- reads {legacy_as_role} 'note' rows "
              f"(expected 0) -- proves inertness tracks OWNER IDENTITY, never 'no split ran' "
              f"alone, exactly this delta's own HONEST BOUND header note", failures)

    finally:
        for w in (world_pre, world_main, world_split):
            teardown(w)
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
            f"DROP OWNED BY {world_split}_owner; DROP ROLE IF EXISTS {world_split}_owner;"])
        teardown(world_legacy)
        for t in tmps:
            sh(["rm", "-rf", str(t)])

    print(f"\n{'ALL GREEN' if not failures else 'FAILURES: ' + ', '.join(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
