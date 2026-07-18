#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T01:58:07Z
#   last-change: 2026-07-18T01:58:07Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for kernel/lineage/s40-principal-identity-events.sql
(design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md §6 witness plan, as amended by C6 -- the
s40 slice; the s41 slice lives in seen-red/s41-principal-bindings-and-relations/). Real infra,
no mocks: CLASSIC-mode scaffolds (explicit --schema/--kern/--role, manual lineage apply in the
TOY db -- the s30..s39 scaffold_classic idiom), one REAL --new-world scaffold run, torn down
before AND after so re-running leaves no residue. Every refusal is witnessed on BOTH polarities,
red first (a gate never seen red is a claim -- ADR-0011's 2026-07-02 amendment).

WORLDS:
  WORLD A -- chain ends at s39 (s40 NOT applied): the detect sibling's f-polarity, and the
             pre-s40 contrast (a NULL-actor write lands silently under the default principal).
  WORLD B -- chain ends at s40: every s40 red/green polarity lives here.
  WORLD NW -- a REAL `bootstrap/new-project.sh --new-world` scaffold run on a scratch target:
             the birth sequence's three explicit acts land as events, and the world's first
             ordinary ./led write succeeds with NO LED_ACTOR set (strict-on, zero friction --
             the ratified reconciliation, witnessed end-to-end).

Cases (each names the witness that would show it false):
  detect-f-on-s39 / detect-t-on-s40  -- the .detect.sql sibling, both polarities.
  pre-s40-silent-default             -- WORLD A: a NULL-actor write lands under 'author' with no
                                        refusal (the undeclared-fallback class s40 forecloses),
                                        witnessed live before s40 exists anywhere.
  bare-anchor-refused-at-commit      -- WORLD B: INSERT INTO principal with no same-transaction
                                        registration event cannot COMMIT (deferred trigger).
  undeclared-write-refused           -- WORLD B: NULL-actor write, no standing declaration ->
                                        refused with the declare-standing teach-text (this is
                                        ALSO the table->view gap-window polarity: refused, never
                                        misattributed).
  declared-write-resolves            -- WORLD B: after `led principal declare-standing`, the
                                        same NULL-actor write resolves to the declared principal
                                        (the never-refuses leg) and carries
                                        principal_actor_resolution='declared-default' (C6 i).
  explicit-write-marked              -- WORLD B: a LED_ACTOR write carries 'explicit' (C6 i).
  register-duplicate-same-class      -- WORLD B: re-registration refused loudly, teach quotes
                                        id/class/purpose (the Axis 6 silent no-op, closed).
  register-duplicate-class-mismatch  -- WORLD B: refused naming the mismatch + the succession
                                        teach (classes immutable).
  purpose-mandatory                  -- WORLD B: register-principal without --purpose refused.
  suspend-refuses-writes             -- WORLD B: write under a suspended principal refused,
                                        naming the standing event row id.
  revoke-refuses-writes / successor-passes -- WORLD B: revoked principal's writes refuse;
                                        a fresh successor principal's writes pass (the only v1
                                        reinstatement path, witnessed as what it is).
  precedence-both-orders             -- WORLD B: suspend-then-revoke AND revoke-then-suspend
                                        (two subjects) -> principal_standing() = 'revoked' in
                                        both construction orders.
  rotation                           -- WORLD B: a second declare-standing supersedes the first;
                                        the principal_role view shows EXACTLY the new binding
                                        (C6 ii).
  anchor-append-only                 -- WORLD B: UPDATE/DELETE on kernel.principal refused.
  gates-green                        -- gates/ledger_reader_allowlist.py + gates/
                                        kind_shape_manifest_gate.py both exit 0 on their own
                                        standing CHAINs (which include s40 as of this commit).
  differential-agree-both-layers     -- WORLD B (carrying all four s40 kinds): the STANDING
                                        ./judge differential (tnow + work layers) AGREEs -- the
                                        new kinds flow through entry/6 generically, witnessed
                                        not asserted.
  new-world-birth-sequence           -- WORLD NW: the three birth acts land as events; first
                                        ordinary ./led write succeeds with no LED_ACTOR.

Usage: python3 seen-red/s40-principal-identity-events/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import os
import shutil
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

import ledger_differential  # noqa: E402
import ledger_edb  # noqa: E402
import pghost_resolve  # noqa: E402

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
]
CHAIN_A = CHAIN_COMMON
CHAIN_B = CHAIN_COMMON + ["s40-principal-identity-events.sql"]


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
        f"DROP SCHEMA IF EXISTS {world} CASCADE; DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "  # declared-drop: scratch reset
        f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def led(world_dir: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    e = dict(os.environ)
    if env:
        e.update(env)
    return sh(["bash", str(world_dir / "led"), *args], cwd=str(world_dir), env=e)


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def psql_raw(script: str) -> subprocess.CompletedProcess[str]:
    """A script allowed to FAIL (red-polarity probes) -- caller inspects returncode/stderr."""
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"],
              input=script)


def detect(schema: str, kern: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tA",
             "-v", f"schema={schema}", "-v", f"kern={kern}",
             "-f", str(LINEAGE / "s40-principal-identity-events.detect.sql")])
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
        raise RuntimeError(f"CLASSIC apply FAILED ({world}, chain ends {chain[-1]}): "
                           f"{ra.stdout[-1500:]} {ra.stderr[-1500:]}")
    hexsecret = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"TRUNCATE {kern}.stamp_secret;",
        "-c", f"INSERT INTO {kern}.stamp_secret (secret) VALUES (decode('{hexsecret}','hex'));"])
    genesis_hex = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis_hex}') "
              f"ON CONFLICT (only_one) DO NOTHING;"])
    return world_dir


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    world_a, world_b, world_nw = "s40fxa", "s40fxb", "s40fxnw"
    for w in (world_a, world_b, world_nw):
        teardown(w)
    try:
        # =========================================================================================
        # WORLD A -- s39 head: detect f-polarity + the pre-s40 silent-default contrast.
        # =========================================================================================
        print(f"== scaffolding classic world {world_a} (chain ends {CHAIN_A[-1]}, s40 NOT applied) ==")
        wa = scaffold_classic(world_a, CHAIN_A)
        tmps.append(wa.parent)

        check("detect-f-on-s39", detect(world_a, f"{world_a}_kernel") == "f",
              f"s40 detect sibling on an s39-head chain reads {detect(world_a, f'{world_a}_kernel')!r} (expect f)",
              failures)

        ra = led(wa, "note", "pre-s40 contrast: NULL-actor write")
        landed = psql_tuples(f"SELECT p.name FROM {world_a}.ledger l JOIN {world_a}_kernel.principal p "
                             f"ON p.id = l.actor WHERE l.kind='note' ORDER BY l.id DESC LIMIT 1;")
        check("pre-s40-silent-default", ra.returncode == 0 and landed == "author",
              f"WORLD A (pre-s40): NULL-actor `led note` exit={ra.returncode}, landed under "
              f"{landed!r} with no refusal anywhere -- the undeclared silent fallback s40 "
              f"forecloses, witnessed live", failures)

        # =========================================================================================
        # WORLD B -- s40 head. Red polarities FIRST.
        # =========================================================================================
        print(f"== scaffolding classic world {world_b} (chain ends {CHAIN_B[-1]}) ==")
        wb = scaffold_classic(world_b, CHAIN_B)
        tmps.append(wb.parent)
        S, K, R = world_b, f"{world_b}_kernel", f"{world_b}_rw"

        check("detect-t-on-s40", detect(S, K) == "t",
              f"s40 detect sibling on the s40 chain reads {detect(S, K)!r} (expect t)", failures)

        # bare anchor INSERT: cannot COMMIT (deferred trigger)
        rb = psql_raw(f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
                      f"INSERT INTO {K}.principal (name, agent_class) VALUES ('bare-bob','model');\n")
        out = rb.stdout + rb.stderr
        check("bare-anchor-refused-at-commit",
              rb.returncode != 0 and "BARE principal registration is unrepresentable" in out
              and psql_tuples(f"SELECT count(*) FROM {K}.principal WHERE name='bare-bob';") == "0",
              f"exit={rb.returncode}; teach excerpt={out.strip()[-200:]!r}; no anchor row landed",
              failures)

        # undeclared write refused (also the table->view gap-window polarity: refused, never
        # misattributed -- no standing declaration exists yet on this hand-driven chain)
        ru = led(wb, "note", "undeclared write, should refuse")
        out = ru.stdout + ru.stderr
        check("undeclared-write-refused",
              ru.returncode != 0 and "strict attribution (s40)" in out
              and "declare-standing" in out,
              f"exit={ru.returncode}; teach excerpt={out.strip()[-200:]!r}", failures)

        # birth acts, hand-driven (the scaffold's own scripted form is witnessed on WORLD NW):
        r1 = psql_raw(
            f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
            f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_purpose)\n"
            f"VALUES ('principal_registered', 'principal ''author'' registered (class model) -- fixture genesis exception',\n"
            f"        (SELECT id FROM principal WHERE name='author'),\n"
            f"        (SELECT id FROM principal WHERE name='author'), 'fixture connection principal');\n")
        if r1.returncode != 0:
            raise RuntimeError(f"author registration event failed: {r1.stderr[-500:]}")
        rd = led(wb, "principal", "declare-standing", "author", env={"LED_ACTOR": "author"})
        if rd.returncode != 0:
            raise RuntimeError(f"declare-standing failed: {rd.stdout[-500:]} {rd.stderr[-500:]}")

        # never-refuses leg + C6(i) declared-default mark
        rg = led(wb, "note", "declared default write")
        row = psql_tuples(f"SELECT p.name || '|' || l.principal_actor_resolution FROM {S}.ledger l "
                          f"JOIN {K}.principal p ON p.id = l.actor "
                          f"WHERE l.statement = 'declared default write';")
        check("declared-write-resolves", rg.returncode == 0 and row == "author|declared-default",
              f"NULL-actor write exit={rg.returncode}, resolved+marked {row!r} "
              f"(expect author|declared-default)", failures)

        # register reviewer2 through the ceremony (green), then C6(i) explicit mark
        rr2 = led(wb, "register-principal", "reviewer2", "model",
                  "--purpose", "fixture reviewer principal")
        if rr2.returncode != 0:
            raise RuntimeError(f"register reviewer2 failed: {rr2.stdout[-500:]} {rr2.stderr[-500:]}")
        rx = led(wb, "note", "explicit actor write", env={"LED_ACTOR": "reviewer2"})
        rowx = psql_tuples(f"SELECT p.name || '|' || l.principal_actor_resolution FROM {S}.ledger l "
                           f"JOIN {K}.principal p ON p.id = l.actor "
                           f"WHERE l.statement = 'explicit actor write';")
        check("explicit-write-marked", rx.returncode == 0 and rowx == "reviewer2|explicit",
              f"LED_ACTOR write exit={rx.returncode}, resolved+marked {rowx!r} "
              f"(expect reviewer2|explicit)", failures)

        # duplicate registration, both class polarities (red)
        rds = led(wb, "register-principal", "reviewer2", "model", "--purpose", "dup")
        outs = rds.stdout + rds.stderr
        check("register-duplicate-same-class",
              rds.returncode != 0 and "already registered" in outs
              and "fixture reviewer principal" in outs and "never a silent no-op" in outs,
              f"exit={rds.returncode}; teach quotes purpose={'fixture reviewer principal' in outs}; "
              f"excerpt={outs.strip()[-160:]!r}", failures)
        rdm = led(wb, "register-principal", "reviewer2", "human", "--purpose", "dup")
        outm = rdm.stdout + rdm.stderr
        check("register-duplicate-class-mismatch",
              rdm.returncode != 0 and "classes are IMMUTABLE" in outm and "succeeds" in outm,
              f"exit={rdm.returncode}; excerpt={outm.strip()[-160:]!r}", failures)

        rp = led(wb, "register-principal", "nopurpose", "model")
        outp = rp.stdout + rp.stderr
        check("purpose-mandatory", rp.returncode != 0 and "--purpose is mandatory" in outp,
              f"exit={rp.returncode}; excerpt={outp.strip()[-140:]!r}", failures)

        # suspend reviewer2 -> its writes refuse, naming the standing event row
        rs = led(wb, "principal", "suspend", "reviewer2", "fixture suspension",
                 env={"LED_ACTOR": "author"})
        if rs.returncode != 0:
            raise RuntimeError(f"suspend failed: {rs.stdout[-400:]} {rs.stderr[-400:]}")
        rw = led(wb, "note", "write as suspended", env={"LED_ACTOR": "reviewer2"})
        outw = rw.stdout + rw.stderr
        check("suspend-refuses-writes",
              rw.returncode != 0 and "is suspended (standing event row" in outw,
              f"exit={rw.returncode}; excerpt={outw.strip()[-180:]!r}", failures)

        # revoke reviewer2 (suspend-then-revoke order); register successor; successor passes
        rv = led(wb, "principal", "revoke", "reviewer2", "fixture revocation",
                 env={"LED_ACTOR": "author"})
        if rv.returncode != 0:
            raise RuntimeError(f"revoke failed: {rv.stdout[-400:]} {rv.stderr[-400:]}")
        rwr = led(wb, "note", "write as revoked", env={"LED_ACTOR": "reviewer2"})
        outr = rwr.stdout + rwr.stderr
        rsucc = led(wb, "register-principal", "reviewer3", "model",
                    "--purpose", "successor of reviewer2 (fixture)", env={"LED_ACTOR": "author"})
        rws = led(wb, "note", "write as successor", env={"LED_ACTOR": "reviewer3"})
        check("revoke-refuses-writes / successor-passes",
              rwr.returncode != 0 and "is revoked (standing event row" in outr
              and rsucc.returncode == 0 and rws.returncode == 0,
              f"revoked write exit={rwr.returncode} ({outr.strip()[-120:]!r}); successor "
              f"registration exit={rsucc.returncode}; successor write exit={rws.returncode}",
              failures)

        # precedence, both construction orders: reviewer2 was suspend-then-revoke; make a fresh
        # subject for revoke-then-suspend.
        led(wb, "register-principal", "rts", "model", "--purpose", "revoke-then-suspend subject",
            env={"LED_ACTOR": "author"})
        led(wb, "principal", "revoke", "rts", env={"LED_ACTOR": "author"})
        led(wb, "principal", "suspend", "rts", env={"LED_ACTOR": "author"})
        st1 = psql_tuples(f"SELECT {K}.principal_standing(id) FROM {K}.principal WHERE name='reviewer2';")
        st2 = psql_tuples(f"SELECT {K}.principal_standing(id) FROM {K}.principal WHERE name='rts';")
        check("precedence-both-orders", st1 == "revoked" and st2 == "revoked",
              f"suspend-then-revoke reads {st1!r}, revoke-then-suspend reads {st2!r} "
              f"(expect revoked/revoked -- strict severity ordering, both orders)", failures)

        # rotation (C6 ii): re-declare the role's standing to reviewer3; view shows exactly it
        rrot = led(wb, "principal", "declare-standing", "reviewer3", env={"LED_ACTOR": "author"})
        view = psql_tuples(f"SELECT db_role || '|' || p.name FROM {K}.principal_role pr "
                           f"JOIN {K}.principal p ON p.id = pr.principal_id;")
        check("rotation", rrot.returncode == 0 and view == f"{R}|reviewer3"
              and "rotating -- superseding standing declaration row" in (rrot.stdout + rrot.stderr),
              f"exit={rrot.returncode}; principal_role now reads {view!r} (expect exactly "
              f"{R}|reviewer3, one row); rotation notice printed", failures)
        # rotate BACK to author so the differential below runs under a live default
        led(wb, "principal", "declare-standing", "author", env={"LED_ACTOR": "author"})

        # anchor append-only (red)
        rup = psql_raw(f"UPDATE {K}.principal SET agent_class='human' WHERE name='reviewer3';")
        rdel = psql_raw(f"DELETE FROM {K}.principal WHERE name='reviewer3';")
        check("anchor-append-only",
              rup.returncode != 0 and rdel.returncode != 0
              and "append-only" in (rup.stdout + rup.stderr),
              f"UPDATE exit={rup.returncode}, DELETE exit={rdel.returncode} (both refused)",
              failures)

        # gates green on their own standing CHAINs (now including s40)
        g1 = sh([sys.executable, str(REPO / "gates" / "ledger_reader_allowlist.py")])
        g2 = sh([sys.executable, str(REPO / "gates" / "kind_shape_manifest_gate.py")])
        check("gates-green", g1.returncode == 0 and g2.returncode == 0,
              f"ledger_reader_allowlist exit={g1.returncode}; kind_shape_manifest_gate "
              f"exit={g2.returncode}", failures)

        # the standing ./judge differential, both layers, on WORLD B (all four s40 kinds live:
        # registered/suspended/revoked/standing_declared rows all exist above) + a work item so
        # the work layer has substance.
        led(wb, "work", "open", "s40fx-item", "differential fixture item")
        kinds = psql_tuples(f"SELECT count(DISTINCT kind) FROM {S}.ledger WHERE kind LIKE 'principal_%';")
        os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = \
            PGDB, S, K
        try:
            edb_text = ledger_edb.export(S).edb_text()
            res_tnow = ledger_differential.run_differential(S, edb_text=edb_text)
            res_work = ledger_differential.run_layer_differential(S, "work")
        finally:
            del os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"]
        v_tnow, v_work = res_tnow.verdict(), res_work.verdict()
        check("differential-agree-both-layers",
              v_tnow == "AGREE" and v_work == "AGREE" and kinds == "4",
              f"tnow={v_tnow} work={v_work} with {kinds} distinct principal_* kinds on the "
              f"fixture ledger (expect AGREE/AGREE/4)", failures)

        # =========================================================================================
        # WORLD NW -- the REAL --new-world scaffold run (basis §6's scaffold leg).
        # =========================================================================================
        print(f"== REAL --new-world scaffold run ({world_nw}) ==")
        tmpnw = Path(tempfile.mkdtemp(prefix=f"{world_nw}-seenred-"))
        tmps.append(tmpnw)
        nwdir = tmpnw / world_nw
        rnw = sh(["bash", str(NEW_PROJECT), str(nwdir), "--new-world", world_nw,
                  "--db", PGDB, "--host", PGHOST])
        events = psql_tuples(
            f"SELECT count(*) FROM {world_nw}.ledger WHERE kind='principal_registered';") if rnw.returncode == 0 else "?"
        decls = psql_tuples(
            f"SELECT count(*) FROM {world_nw}.ledger WHERE kind='principal_standing_declared';") if rnw.returncode == 0 else "?"
        rfirst = led(nwdir, "decision", "first ordinary write in a strict-on world, no LED_ACTOR") \
            if rnw.returncode == 0 else None
        first_row = psql_tuples(
            f"SELECT p.name || '|' || l.principal_actor_resolution FROM {world_nw}.ledger l "
            f"JOIN {world_nw}_kernel.principal p ON p.id = l.actor "
            f"WHERE l.kind='decision' ORDER BY l.id DESC LIMIT 1;") if rnw.returncode == 0 else "?"
        check("new-world-birth-sequence",
              rnw.returncode == 0 and events == "3" and decls == "1"
              and rfirst is not None and rfirst.returncode == 0
              and first_row == "author|declared-default",
              f"scaffold exit={rnw.returncode}; registration events={events} (author, reviewer, "
              f"commissioner), standing declarations={decls}; first no-LED_ACTOR write "
              f"exit={(rfirst.returncode if rfirst else '?')}, attributed {first_row!r} "
              f"(expect author|declared-default -- strict-on, zero friction)", failures)

    finally:
        for w in (world_a, world_b, world_nw):
            teardown(w)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s40 principal-identity-events both-polarity proof "
          "(detect t/f, bare-anchor commit refusal, strict attribution red+green, ceremony "
          "duplicate refusals both class polarities, suspend/revoke + successor, precedence "
          "both orders, rotation, anchor append-only, gates green, ./judge AGREE both layers, "
          "REAL --new-world birth sequence end-to-end), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
