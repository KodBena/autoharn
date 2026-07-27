#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s41-principal-bindings-and-
relations.sql (design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md §6 witness plan as amended by
C6 -- the s41 slice; the s40 slice lives in seen-red/s40-principal-identity-events/). Real
infra, no mocks: CLASSIC scaffolds + manual chain applies in the TOY db, one REAL --new-world
run against the s41-wired scaffold, torn down before AND after. Red first, per refusal.

WORLDS:
  WORLD A  -- chain ends at s40 (s41 NOT applied): the detect f-polarity + the s41-verb
              teach-refusal. Genuinely needs this absence (ledger row 1471's own named
              example) -- served (cluster-1 fixture-repairs) since the CLI's own capability
              check is a GET /health READ, needing no s43.
  WORLD C  -- chain ends at s41 ONLY (s43 NOT applied, unserved, no boundary): hosts every
              case (or case-leg) that is ENTIRELY raw SQL against the kernel trigger/CHECK
              layer directly (d6-human-attested-scoping, acts-for-retired, and the raw legs of
              self-edges-refused/snp-canonicalization/competence-lifecycle) -- cluster-1
              fixture-repairs: s43 revokes the role's raw INSERT grant outright, foreclosing
              these probes on any chain that carries it, the same conflict s40's own sibling
              family hit with bare-anchor-refused-at-commit, just at larger scale here.
  WORLD B  -- chain ends at s61 (cluster-1 fixture-repairs -- see CHAIN_B's own comment for
              why s43 alone was not enough and s64 was too much): every OTHER s41 red/green
              polarity, all `led()`-dispatcher-driven, needing a served boundary (hence s43)
              and, as of key-binding-polarity's own fix, a real attest-possession ceremony
              (hence s61 and its own contiguous s44..s60 prerequisite chain).
  WORLD NW -- a REAL `new-project.sh --new-world` run (chain now the full current head, always
              -- --new-world's own derivation), now served (cluster-1 fixture-repairs: it
              scaffolded fine already, but its own `led()` call had no boundary standing over
              it): full birth end-to-end, detect t on the born world, first ordinary write OK.

Cases (each names the witness that would show it false -- see the check() lines):
  detect polarity (t/f); s40-only teach; relate/unrelate assert-retract lifecycle (view drops,
  raw history keeps); self-edge refused for ALL FOUR relation values (CLI, WORLD B) + once raw
  at the kernel trigger (WORLD C); same-natural-person canonicalization (CLI stores lower-id
  subject; the other ordering refused as duplicate; a raw non-canonical INSERT refused by the
  kernel CHECK, WORLD C); key bind human-only (model refused / human passes, both via a REAL
  attest-possession ceremony -- cluster-1 fixture-repairs, `led principal bind-key` now
  unconditionally requires --possession-ref / malformed fingerprint refused at the kernel shape
  CHECK); D-6 (managerial by stamp-distinct MODEL refused; technical by model passes;
  managerial by HUMAN passes -- entirely raw, WORLD C); acts_for retirement (entirely raw,
  WORLD C); competence lifecycle (grant with all fields -> in view; empty value field refused;
  inactive-from-birth refused raw (WORLD C); withdraw -> leaves view, stays raw; stray --band
  on withdrawal refused; duplicate active grant refused; --supersedes re-band replaces;
  stale/mismatched supersession targets refused, also for release-role/revoke-key); C6(iii) an
  s41 column reads back through ledger_current (plus view-definition inspection -- the pre-C3
  stale-view state cannot be reproduced on a chain that carries C3's re-issue, so the
  inspection is the named witness form C6 itself licenses); gates green; ./judge AGREE both
  layers with all NINE principal kinds live (s40's four + s41's four + s61's
  principal_key_possession_verified, cluster-1 fixture-repairs -- the real possession ceremony
  key-binding-polarity now performs); the s41-wired --new-world birth; the Idris freshness gate
  green (the parity pass's own net).

Usage: python3 seen-red/s41-principal-bindings-and-relations/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import hashlib
import hmac as hmac_mod
import importlib.util
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

# cluster-1 fixture-repairs (ledger rows 1459/1464/1471): the served `led` shim now
# unconditionally refuses a deployment.json missing boundary_url/boundary_deployment, and the
# served boundary itself refuses every WRITE with 409 capability_absent unless the schema
# carries the s43 kernel-lineage delta. Every world below drives real `led()` dispatcher
# writes (or, for WORLD A, a client-side capability READ that still needs a served boundary to
# talk to), so each needs a REAL served boundary standing over it -- REUSE (ADR-0012 P1)
# serve_existing_world/stop_server, the s26-row-hash-chain-deletion pattern, rather than
# re-implementing.
_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", REPO / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

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
# WORLD A stays capped EXACTLY at s40 (unchanged) -- "s40-only-kernel-teach" GENUINELY needs a
# schema that carries s40 but NOT s41 (that absence is the very thing under test, named
# verbatim in ledger row 1471's own example: "principal-bindings capability is genuinely ABSENT
# before s41"). This case is still servable, though (see below): the CLI's own s41_identity
# capability check is a GET /health READ, reached BEFORE any write is attempted, so it needs no
# s43 at all -- only a served boundary standing over the (unmodified) s40-only schema.
CHAIN_B_S41_ONLY = CHAIN_COMMON + ["s41-principal-bindings-and-relations.sql"]
# WORLD B -- cluster-1 fixture-repairs (ledger rows 1459/1464/1471): every OTHER s41 red/green
# case drives a real `led()` dispatcher write, which needs a served boundary, which itself
# refuses (409 capability_absent) unless the schema carries s43 (capability detection is a
# straight object-existence probe -- the CapabilityManifest checks for s43's OWN objects by
# name, not "is the chain past generation N"). s41 was never a deliberate era ceiling for these
# cases (nothing here tests "s41 behavior specifically BEFORE some later generation") -- adding
# s42+s43 (s43's own PREREQUISITE) is a pure capability fix, not a weakening.
#
# DATED FINDING (found running this fixture, not assumed): `led principal bind-key` now
# unconditionally requires --possession-ref for a FRESH bind (bootstrap/templates/led.tmpl's own
# dated comment, s61 item 3) -- a client-side requirement that does NOT check whether the
# schema's own kernel carries s61 at all. Witnessing `key-binding-polarity`'s green leg
# faithfully (a real human bind-key that actually succeeds) therefore needs a REAL
# `attest-possession` ceremony, which needs the KERNEL to recognize
# 'principal_key_possession_verified' as a valid kind (s61's own vocabulary) -- so, unlike this
# comment's own earlier draft (which stopped at s43, before this was discovered), the chain
# extends through s61 (and its own contiguous PREREQUISITE chain, s44..s60) after all. Still
# NOT the full current head (s62-s64 stay out -- nothing here needs them, and the "only however
# much the capability gap needs" discipline this comment's own earlier draft named still
# governs, just with a wider true requirement than first assumed): s60's entitlement
# enforcement is fine here (conjunct (a) is vacuous with zero entitlement_class_configured rows;
# conjunct (b) is trivially satisfied because 'author' -- the actor for every authority-bearing
# act below -- IS this world's genesis principal, per s60's own genesis exception). Verified by
# running this fixture, not assumed: scaffold_classic's manual DDL apply never births any ledger
# row regardless of how far the chain reaches, so the empty-ledger genesis-principal
# bootstrapping this fixture's own hand-driven 'author' registration relies on is unaffected.
CHAIN_B = CHAIN_B_S41_ONLY + [
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
]

# cluster-1 fixture-repairs, found running this fixture (not assumed): `led principal bind-key`
# now unconditionally requires --possession-ref for a FRESH bind (bootstrap/templates/led.tmpl's
# own dated comment, s61 item 3, design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §2 item 3) --
# CLIENT-SIDE and NOT gated on whether the schema's own kernel carries s61 at all (this world's
# chain stops at s43, well before s61). A well-shaped but otherwise-arbitrary literal like the
# one this constant used to hold can no longer exercise the green ("human passes") leg at all --
# a real proof-of-possession ceremony (a real throwaway GPG key, a real detached signature, a
# real `attest-possession` call) is now required, so key-binding-polarity generates its own key
# at runtime (see `gen_key()` below) instead of a fixed literal. Kept here ONLY as the malformed-
# shape probe's own well-shaped-but-wrong-format contrast is unaffected by this (that leg fails
# client-side before any server round trip, at KeyBindingPayload's own shape check).
FP_MALFORMED = "abc123"

KEYGEN_BATCH_TEMPLATE = """%no-protection
Key-Type: eddsa
Key-Curve: ed25519
Key-Usage: sign
Name-Real: {name}
Name-Email: {email}
Expire-Date: 0
%commit
"""


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def gen_key(gnupghome: Path, name: str, email: str) -> str:
    """A real, throwaway Ed25519 GPG key -- mirrors seen-red/s61-signature-symmetry-and-key-
    binding/run_fixtures_cli.py's own `gen_key()` (read in full before writing this), the
    existing house idiom for exactly this ceremony; not re-derived from scratch."""
    gnupghome.mkdir(mode=0o700, exist_ok=True)
    batch = gnupghome / f"keygen-{email}.batch"
    batch.write_text(KEYGEN_BATCH_TEMPLATE.format(name=name, email=email), encoding="utf-8")
    r = sh(["gpg", "--homedir", str(gnupghome), "--batch", "--generate-key", str(batch)])
    if r.returncode != 0:
        raise RuntimeError(f"gpg keygen failed: {r.stderr}")
    r = sh(["gpg", "--homedir", str(gnupghome), "--list-secret-keys", "--with-colons"])
    fprs = [ln.split(":")[9] for ln in r.stdout.splitlines() if ln.startswith("fpr")]
    return fprs[-1]


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
    # §6 amendment (2026-07-26, rows 1357/1365/1366/1367): routed through the one dispatcher now.
    return sh(["bash", str(world_dir / "autoharn"), "led", *args], cwd=str(world_dir), env=e)


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


def birth_acts_boundary(world_dir: Path, world: str) -> None:
    """cluster-1 fixture-repairs (ledger rows 1459/1464/1471), the s40-family fixture's own
    sibling fix (seen-red/s40-principal-identity-events/run_fixtures.py, read in full before
    writing this): on a chain that reaches s43, the role's raw INSERT grant on ledger/
    kernel.principal is REVOKED (s43 Element 7), so `birth_acts()`'s own raw-INSERT form above
    (still fine for WORLD A, which stays capped pre-s43) gets "permission denied" here. Routes
    the SAME two acts through the SECURITY DEFINER write-boundary functions instead (mirrors
    bootstrap/new-project.sh's own --new-world birth sequence, read in full there), PLUS two
    acts that sequence also performs and this fixture's OWN served writes now need: registering
    the 'write-boundary' tool principal (s43 Element 6 -- absent it, a REFUSED write cannot even
    be journaled, it 500s) and the s43 Element 8 DUAL standing declaration (the granted role AND
    the login role `serving/boundary_service.py`'s own `_psql` actually authenticates as -- every
    served call's session_user, never the granted role SET ROLE switches CURRENT_USER to)."""
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    r1 = psql_raw(
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"DO $bw$\nDECLARE v {K}.write_verdict;\nBEGIN\n"
        f"  SELECT * INTO v FROM {K}.ledger_write(jsonb_build_object(\n"
        f"    'kind', 'principal_registered',\n"
        f"    'statement', 'author registered (fixture genesis exception): self-attributed, "
        f"the first identity event of this fixture''s hand-driven world',\n"
        f"    'actor', (SELECT id FROM principal WHERE name='author'),\n"
        f"    'principal_subject', (SELECT id FROM principal WHERE name='author'),\n"
        f"    'principal_purpose', 'fixture connection principal'));\n"
        f"  IF v.disposition <> 'accepted' THEN\n"
        f"    RAISE EXCEPTION 'author registration event refused (SQLSTATE %): %', v.sqlstate, v.message;\n"
        f"  END IF;\n"
        f"END $bw$;\n")
    if r1.returncode != 0:
        raise RuntimeError(f"author registration event failed ({world}): {r1.stdout[-500:]} {r1.stderr[-500:]}")

    r2 = psql_raw(
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"DO $bw$\nDECLARE v {K}.write_verdict;\nBEGIN\n"
        f"  SELECT * INTO v FROM {K}.registration_write(jsonb_build_object(\n"
        f"    'name', 'write-boundary', 'agent_class', 'tool',\n"
        f"    'purpose', 'the kernel write boundary''s own recording identity: every "
        f"write_refused meta-event is authored by this principal (fixture bootstrap, mirrors "
        f"bootstrap/new-project.sh''s s43 birth sequence step 4)',\n"
        f"    'statement', 'principal ''write-boundary'' registered (class tool) -- fixture "
        f"bootstrap, registrar: author',\n"
        f"    'actor', (SELECT id FROM principal WHERE name='author')));\n"
        f"  IF v.disposition <> 'accepted' THEN\n"
        f"    RAISE EXCEPTION 'write-boundary registration refused (SQLSTATE %): %', v.sqlstate, v.message;\n"
        f"  END IF;\n"
        f"END $bw$;\n")
    if r2.returncode != 0:
        raise RuntimeError(f"write-boundary registration failed ({world}): {r2.stdout[-500:]} {r2.stderr[-500:]}")

    rd = led(world_dir, "principal", "declare-standing", "author", env={"LED_ACTOR": "author"})
    if rd.returncode != 0:
        raise RuntimeError(f"declare-standing ({R}) failed ({world}): {rd.stdout[-500:]} {rd.stderr[-500:]}")
    login_role = psql_tuples("SELECT session_user;")
    rd2 = led(world_dir, "principal", "declare-standing", "author", "--db-role", login_role,
              env={"LED_ACTOR": "author"})
    if rd2.returncode != 0:
        raise RuntimeError(f"declare-standing (login role {login_role!r}) failed ({world}): "
                           f"{rd2.stdout[-500:]} {rd2.stderr[-500:]}")


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
    world_a, world_b, world_c, world_nw = "s41fxa", "s41fxb", "s41fxc", "s41fxnw"
    for w in (world_a, world_b, world_c, world_nw):
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

        # cluster-1 fixture-repairs: `s40-only-kernel-teach` needs a served boundary to reach
        # the CLI's own client-side s41_identity capability check (`led principal bind-role`'s
        # own GET /health probe, read in full in bootstrap/templates/led.tmpl's `cmd_principal`)
        # -- but that check is a READ, reached BEFORE any write is attempted, so it needs no s43
        # (WORLD A stays capped at s40, unmodified -- see CHAIN_B_S41_ONLY's own comment above
        # for why this case cannot honestly move past s40 at all). Guard shape matches
        # s26-row-hash-chain-deletion verbatim.
        proc_a = bs_fixtures.serve_existing_world(wa / "deployment.json", wa.parent)
        try:
            rteach = led(wa, "principal", "bind-role", "author", "--role", "scout")
            outt = rteach.stdout + rteach.stderr
            check("s40-only-kernel-teach",
                  rteach.returncode != 0 and "carries s40 but not s41" in outt,
                  f"exit={rteach.returncode}; excerpt={outt.strip()[-160:]!r}", failures)
        finally:
            bs_fixtures.stop_server(proc_a)

        # ===================== WORLD C (s41 head, capped, NO s43) =====================
        # cluster-1 fixture-repairs, found running this fixture (not assumed): several s41 cases
        # combine a CLI(`led`)-driven leg with a RAW-SQL kernel-trigger/CHECK leg in the SAME
        # assertion (self-edges-refused, snp-canonicalization, competence-lifecycle), plus two
        # cases that are ENTIRELY raw SQL (acts-for-retired, d6-human-attested-scoping). Once
        # WORLD B (below) carries s43, its role's raw INSERT grant on ledger/kernel.principal is
        # REVOKED (s43 Element 7) -- exactly the same conflict s40's own bare-anchor-refused-at-
        # commit case hit, just at larger scale here (five raw-SQL legs, not one). None of these
        # five need s43 or a served boundary at all (no `led()` call anywhere in any of them) --
        # they need ONLY the unmodified s41-only schema WORLD A already proves exists (raw
        # INSERT still intact), so a SEPARATE world hosts them, kept as simple and close to this
        # fixture's ORIGINAL pre-migration design as possible: `birth_acts()`'s own raw-INSERT
        # form (unchanged, still valid pre-s43) plus hume/botty hand-registered the same way.
        print(f"== scaffolding classic world {world_c} (chain ends {CHAIN_B_S41_ONLY[-1]}, "
              f"s43 NOT applied -- hosts the raw-SQL-only s41 legs) ==")
        wc = scaffold_classic(world_c, CHAIN_B_S41_ONLY)
        tmps.append(wc.parent)
        S3, K3, R3 = world_c, f"{world_c}_kernel", f"{world_c}_rw"
        birth_acts(world_c)
        for nm, cls in (("hume", "human"), ("botty", "model")):
            rreg = psql_raw(
                f"SET ROLE {R3};\nSET search_path = {S3}, {K3};\n"
                f"WITH new_p AS (INSERT INTO principal (name, agent_class) VALUES "
                f"('{nm}','{cls}') RETURNING id)\n"
                f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_purpose)\n"
                f"SELECT 'principal_registered', '{nm} registered (fixture, WORLD C)', "
                f"(SELECT id FROM principal WHERE name='author'), id, '{cls} fixture' FROM new_p;\n")
            if rreg.returncode != 0:
                raise RuntimeError(f"WORLD C: register {nm} failed: {rreg.stderr[-500:]}")

        # D-6: managerial by stamp-distinct model refused / technical passes / human passes.
        # The TARGET row must itself carry a verified stamp: the s21 distinctness pair is
        # fail-safe (a NULL half on either row is never distinct), so an unstamped target would
        # refuse EVERY independence claim before D-6 is even reached. Entirely raw SQL (no
        # `led()` call anywhere in this case), so it runs on WORLD C (s43-free) -- see that
        # world's own setup comment above.
        secret = bytes.fromhex(psql_tuples(f"SELECT encode(secret,'hex') FROM {K3}.stamp_secret;"))
        ts0 = int(time.time())
        mac0 = hmac_mod.new(secret, f"sessFX|agent0|{ts0}".encode(), hashlib.sha256).hexdigest()
        psql_raw(f"SET ROLE {R3};\nSET search_path={S3},{K3};\n"
                 f"SELECT set_config('app.vendor_session','sessFX',false),"
                 f" set_config('app.vendor_agent','agent0',false),"
                 f" set_config('app.vendor_ts','{ts0}',false),"
                 f" set_config('app.vendor_hmac','{mac0}',false) \\gset _\n"
                 f"INSERT INTO ledger (kind,statement,actor) VALUES ('decision','d6 target',"
                 f"(SELECT id FROM principal WHERE name='author'));\n")
        tgt = psql_tuples(f"SELECT id FROM {S3}.ledger WHERE statement='d6 target';")
        rm = stamped_review(world_c, "agentM", "botty", "managerial", tgt, "m-claim")
        rt = stamped_review(world_c, "agentT", "botty", "technical", tgt, "t-claim")
        rh = stamped_review(world_c, "agentH", "hume", "managerial", tgt, "h-claim")
        outm = rm.stdout + rm.stderr
        check("d6-human-attested-scoping",
              rm.returncode != 0 and "no schema can witness" in outm
              and rt.returncode == 0 and rh.returncode == 0,
              f"managerial-by-model exit={rm.returncode} (taught: 'no schema can witness'); "
              f"technical-by-model exit={rt.returncode}; managerial-by-human exit={rh.returncode}",
              failures)

        # acts_for retirement (D-7): a registration supplying acts_for is refused by CHECK.
        # Entirely raw SQL, runs on WORLD C for the same reason as D-6 above.
        raf = psql_raw(f"SET ROLE {R3};\nSET search_path={S3},{K3};\n"
                       f"WITH new_p AS (INSERT INTO principal (name, agent_class, acts_for) "
                       f"VALUES ('af','model',1) RETURNING id) "
                       f"INSERT INTO ledger (kind,statement,actor,principal_subject,principal_purpose) "
                       f"SELECT 'principal_registered','af',"
                       f"(SELECT id FROM principal WHERE name='author'),id,'p' FROM new_p;\n")
        check("acts-for-retired",
              raf.returncode != 0 and "principal_acts_for_retired" in (raf.stdout + raf.stderr),
              f"exit={raf.returncode}; the retirement CHECK named", failures)

        # ===================== WORLD B (s41 head) =====================
        print(f"== scaffolding classic world {world_b} (chain ends {CHAIN_B[-1]}) ==")
        wb = scaffold_classic(world_b, CHAIN_B)
        tmps.append(wb.parent)
        S, K, R = world_b, f"{world_b}_kernel", f"{world_b}_rw"
        # cluster-1 fixture-repairs (ledger rows 1459/1464/1471): full current lineage on
        # this schema (CHAIN_B, extended above) means the role's raw INSERT grant is
        # revoked (s43 Element 7) -- birth_acts_boundary (this file's own function, mirrors
        # the s40 family's own sibling fix) replaces the raw-INSERT birth_acts() used by
        # WORLD A above, routing through the write-boundary functions + a served CLI
        # declare-standing instead; a served boundary must stand up FIRST (it drives two of
        # birth_acts_boundary's own four acts). Guard shape matches
        # s26-row-hash-chain-deletion verbatim: any failure between serve and this block's
        # own end must not leak the boundary-service subprocess.
        proc_b = bs_fixtures.serve_existing_world(wb / "deployment.json", wb.parent)
        try:
            birth_acts_boundary(wb, world_b)
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

            # self-edges: all four relation values via the CLI (WORLD B, served), one raw at
            # the kernel trigger (WORLD C, s43-free -- see WORLD C's own comment above for why
            # the raw leg moved off this schema).
            selfs_ok = True
            for rel in ("acts-for", "dispatched-by", "same-natural-person", "succeeds"):
                rs = led(wb, "principal", "relate", "botty", rel, "botty", env={"LED_ACTOR": "author"})
                selfs_ok = selfs_ok and rs.returncode != 0 and "itself" in (rs.stdout + rs.stderr)
            rk = psql_raw(f"SET ROLE {R3};\nSET search_path={S3},{K3};\n"
                          f"INSERT INTO ledger (kind,statement,actor,principal_subject,principal_object,"
                          f"principal_relation,principal_binding_active) VALUES "
                          f"('principal_relation_asserted','raw self',"
                          f"(SELECT id FROM principal WHERE name='author'),"
                          f"(SELECT id FROM principal WHERE name='botty'),"
                          f"(SELECT id FROM principal WHERE name='botty'),'succeeds',true);\n")
            check("self-edges-refused",
                  selfs_ok and rk.returncode != 0 and "cannot stand in relation" in (rk.stdout + rk.stderr),
                  f"all four CLI self-edges refused={selfs_ok} (WORLD B); raw kernel-trigger "
                  f"self-edge (WORLD C) exit={rk.returncode} with the taught text", failures)

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
            # raw leg on WORLD C (s43-free -- see WORLD C's own comment above): hume/botty are
            # registered there in the SAME order (hume lower id, botty higher), so the identical
            # non-canonical ordering (subject=botty, object=hume) is the one under test.
            rnc = psql_raw(f"SET ROLE {R3};\nSET search_path={S3},{K3};\n"
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

            # key bindings: model refused / human passes / malformed shape refused (kernel CHECK).
            # cluster-1 fixture-repairs (found running this fixture): `led principal bind-key`
            # now unconditionally requires --possession-ref for a FRESH bind (see FP_MALFORMED's
            # own comment above) -- a real throwaway key + a real detached signature + a real
            # `attest-possession` call is generated here so the green ("human passes") leg can
            # still be exercised at all; the model-refused leg ALSO needs a valid possession-ref
            # to get PAST that client-side gate before the kernel's OWN "HUMAN subject" refusal
            # is what's actually witnessed (otherwise both legs would only ever witness the
            # possession-ref gate, never s41's own D-6/human-only semantics this case exists to
            # prove).
            gnupghome = wb.parent / "gnupghome"
            real_fp = gen_key(gnupghome, "AUTOHARN TEST KEY -- THROWAWAY -- s41 seen-red",
                               "s41-seenred-test@example.invalid")
            keys_dir = wb / "keys"
            keys_dir.mkdir(parents=True, exist_ok=True)
            gpg_env = {"GNUPGHOME": str(gnupghome), "PATH": "/usr/bin:/bin:/usr/local/bin"}
            r_export = sh(["gpg", "--homedir", str(gnupghome), "--armor", "--export", real_fp])
            (keys_dir / "test-key.asc").write_text(r_export.stdout, encoding="utf-8")
            possess_statement = f"autoharn key-binding proof-of-possession: fingerprint={real_fp}"
            possess_asc = wb.parent / "possession.asc"
            rsign = sh(["gpg", "--batch", "--yes", "--detach-sign", "--armor", "-o",
                        str(possess_asc), "-"], input=possess_statement, env=gpg_env)
            if rsign.returncode != 0:
                raise RuntimeError(f"gpg detach-sign of the possession statement failed: {rsign.stderr}")
            rattest = led(wb, "principal", "attest-possession", real_fp, "--asc", str(possess_asc),
                          env={"LED_ACTOR": "author"})
            if rattest.returncode != 0:
                raise RuntimeError(f"attest-possession failed: {rattest.stdout[-500:]} {rattest.stderr[-500:]}")
            possess_row = psql_tuples(
                f"SELECT id FROM {S}.ledger WHERE kind='principal_key_possession_verified' "
                f"ORDER BY id DESC LIMIT 1;")

            rkm = led(wb, "principal", "bind-key", "botty", "--fingerprint", real_fp,
                      "--possession-ref", possess_row, env={"LED_ACTOR": "author"})
            rkh = led(wb, "principal", "bind-key", "hume", "--fingerprint", real_fp,
                      "--possession-ref", possess_row, env={"LED_ACTOR": "author"})
            keys_view = psql_tuples(f"SELECT count(*) FROM {S}.principal_keys;")
            rkbad = led(wb, "principal", "bind-key", "hume", "--fingerprint", FP_MALFORMED,
                        "--possession-ref", possess_row, env={"LED_ACTOR": "author"})
            check("key-binding-polarity",
                  rkm.returncode != 0 and "HUMAN subject" in (rkm.stdout + rkm.stderr)
                  and rkh.returncode == 0 and keys_view == "1"
                  and rkbad.returncode != 0 and "principal_key_fingerprint_shape" in (rkbad.stdout + rkbad.stderr),
                  f"model bind exit={rkm.returncode} (taught); human bind exit={rkh.returncode}, "
                  f"view rows={keys_view}; malformed fingerprint exit={rkbad.returncode} "
                  f"(kernel shape CHECK named); real throwaway key {real_fp}, possession row "
                  f"{possess_row}", failures)

            # D-6 (d6-human-attested-scoping) and acts_for retirement (acts-for-retired) moved
            # to WORLD C -- see that world's own setup comment above; both are entirely raw SQL
            # (no `led()` call in either), so they run there, before this WORLD B block, against
            # the unmodified s43-free schema they actually need.

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
            # raw leg on WORLD C (s43-free -- see that world's own setup comment above); 'botty'
            # is registered there too, independent of any competence grants made on WORLD B.
            rinactive = psql_raw(f"SET ROLE {R3};\nSET search_path={S3},{K3};\n"
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
            krev = led(wb, "principal", "revoke-key", "hume", "--fingerprint", real_fp,
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
            # cluster-1 fixture-repairs, dated finding: 9, not the original 8 -- key-binding-
            # polarity's own fix above (CHAIN_B's own comment) now does a REAL attest-possession
            # ceremony to satisfy the CLI's unconditional --possession-ref requirement, which
            # lands a ninth kind (principal_key_possession_verified, s61) alongside the four s40
            # kinds and the four s41 kinds (relation_asserted/role_bound/key_bound/
            # competence_granted) this world already carried before that fix. Verified by
            # reading this world's own ledger (not assumed): a real, current count, not a
            # weakened assertion.
            check("differential-agree-both-layers",
                  v_tnow == "AGREE" and v_work == "AGREE" and kinds == "9",
                  f"tnow={v_tnow} work={v_work} with {kinds} distinct principal_* kinds live "
                  f"(expect AGREE/AGREE/9 -- s40's four + s41's four + s61's "
                  f"principal_key_possession_verified from the attest-possession ceremony "
                  f"key-binding-polarity now performs)", failures)

        finally:
            bs_fixtures.stop_server(proc_b)

        # ===================== WORLD NW (the s41-wired --new-world) =====================
        print(f"== REAL --new-world scaffold run ({world_nw}, chain s15..s41) ==")
        tmpnw = Path(tempfile.mkdtemp(prefix=f"{world_nw}-seenred-"))
        tmps.append(tmpnw)
        nwdir = tmpnw / world_nw
        rnw = sh(["bash", str(NEW_PROJECT), str(nwdir), "--new-world", world_nw,
                  "--db", PGDB, "--host", PGHOST])
        det_nw = detect(world_nw, f"{world_nw}_kernel") if rnw.returncode == 0 else "?"
        rfirst = None
        if rnw.returncode == 0:
            # cluster-1 fixture-repairs (per-family note case (2), mirrored off the s40 family's
            # own sibling fix): WORLD NW's --new-world scaffold already applies the full current
            # lineage (s43 included) and runs the real birth sequence, but this fixture's own
            # `led()` call for the first ordinary write still went through the now-dead legacy
            # path with no served boundary standing over it. Guard shape matches
            # s26-row-hash-chain-deletion verbatim.
            for verb in ("autoharn",):
                p = nwdir / verb
                if p.exists():
                    p.chmod(0o755)
            proc_nw = bs_fixtures.serve_existing_world(nwdir / "deployment.json", tmpnw)
            try:
                rfirst = led(nwdir, "decision", "first write in an s41 world")
            finally:
                bs_fixtures.stop_server(proc_nw)
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
        for w in (world_a, world_b, world_c, world_nw):
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
