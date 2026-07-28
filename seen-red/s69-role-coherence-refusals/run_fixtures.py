#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s69-role-coherence-refusals.sql
(design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md, RATIFIED autoharn3 ledger row 201). Real
infra, no mocks: a CLASSIC scaffold (bootstrap/new-project.sh, the real --new-world path) + the
full lineage chain applied in the TOY db, torn down before AND after. Modeled directly on
seen-red/s68-typed-absence-dispositions/run_fixtures.py (scaffold_classic/birth_via_boundary/
bw_call helpers, same shape) and seen-red/s47-claim-on-closed-refusal/run_fixtures.py
(judge_agree, the work-layer SQL/ASP differential helper).

FIXTURE FAMILY CHOICE: a NEW sibling family (spec §4's own instruction: "new seen-red family,
registered") -- s69 closes three DIFFERENT enforcement gaps (closer/claimant, witness shape,
review staleness) with their own vocabulary, no existing family's own RED/GREEN pair covers any
of them.

WORLD PRE (s68 head, NO s69) -- the four conflations witnessed as ACCEPTED today:
  RED-CLOSE-BY-NEVER-CLAIMANT        -- an item never claimed by anyone is closed regardless.
  RED-CLOSE-BY-SUPERSEDED-CLAIMANT   -- claimant A claims, B reclaims (last-claim-wins), A (the
                                         now-superseded claimant) still closes successfully.
  RED-WITNESS-ROW-WORK-CLAIMED-ACCEPTED -- a --review-witness row:<id> citing a work_claimed row
                                         (the autoharn2 row-1265 shape) is accepted as evidence.
  RED-REVIEW-REGARDS-SUPERSEDED-ACCEPTED -- a review regarding a row that has since been
                                         superseded is accepted (the experience4 431/435 shape).

WORLD MAIN (s69 head) -- each RED leg above now refused, teaching; every happy path unchanged:
  GREEN-CLOSE-BY-NEVER-CLAIMANT-REFUSED / GREEN-CLOSE-BY-SUPERSEDED-CLAIMANT-REFUSED
  GREEN-WITNESS-ROW-WORK-CLAIMED-REFUSED / GREEN-REVIEW-REGARDS-SUPERSEDED-REFUSED
    (naming the successor id)
  HAPPY-ORDINARY-CLAIMANT-CLOSE       -- claim then close as the SAME actor, with a legitimate
                                         review witness -- accepted, unaffected.
  HAPPY-DEFEAT-AND-RECLAIM            -- A claims, B reclaims, B closes -- accepted end-to-end
                                         (row 201 §0's own proviso: a claim must be defeatable and
                                         reclaimable). A subsequently attempting to close is
                                         refused (A is no longer the claimant-of-record).
  HAPPY-PLANNING-CLOSE-CHILD-CARVE-IN -- a parent citing its own child's work_opened row as
                                         witness -- accepted (both polarities: a non-child
                                         work_opened row is refused, same test).
  HAPPY-REVIEW-REGARDS-IN-FORCE-SUCCESSOR -- a review regarding the in-force successor of a
                                         superseded row -- accepted.
  HAPPY-S56-RESERVATION-DISCHARGE-UNAFFECTED -- the reservation-discharge review-of-a-review
                                         shape (its own regarded row is IN FORCE) -- accepted,
                                         reservation clears from reservations_outstanding.
  RIDER-TEACH-TEXT-DIFF                -- validate_supersession_target's s63 body vs this file's
                                         Element 4, mechanically diffed after normalizing
                                         `./led ` -> `./autoharn led ` -- byte-identical.
  REFUSALS-JOURNAL-AS-WRITE-REFUSED    -- every refusal above lands a write_refused row, s43
                                         refusal-oracle reconciling.
  ZERO-FRICTION-BIRTH                  -- a fresh classic scaffold's birth sequence through s69,
                                         unaffected.
  VERIFY-CHAIN-INTACT-THROUGH-REFUSALS -- ./autoharn verify-chain INTACT + refusal-oracle
                                         CONFIRMED, after every refusal above.
  AGREE-sql-asp-work-differential      -- judge --layer work SQL/ASP AGREE on the s69-head world.

Usage: python3 seen-red/s69-role-coherence-refusals/run_fixtures.py
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
sys.path.insert(0, str(REPO / "gates"))
from pghost_resolve import resolve_pghost  # noqa: E402
import lineage_reissue_lineage as lrl  # noqa: E402  (the extractor rider_diff() re-uses)

os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S68 = [
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
]
CHAIN_S69 = CHAIN_S68 + ["s69-role-coherence-refusals.sql"]


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
                                "purpose": "s69 fixture's own write-boundary registration"}),
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


def claimant_of(world: str, slug: str) -> str:
    return psql_tuples(f"SELECT coalesce(claimant::text,'<NULL>') FROM {world}.work_item_current "
                        f"WHERE slug='{slug}';")


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


def rider_diff(failures: list[str]) -> None:
    """Mechanical proof the rider changes ONLY the ./led spelling: extract s63's own
    CREATE FUNCTION validate_supersession_target statement and this file's Element 4 statement,
    normalize s63's copy (./led  -> ./autoharn led ), and assert byte-equality."""
    s63_lines = (LINEAGE / "s63-supersession-body-restoration.sql").read_text().splitlines()
    s69_lines = (LINEAGE / "s69-role-coherence-refusals.sql").read_text().splitlines()

    def find_create(lines: list[str]) -> int:
        for i, ln in enumerate(lines):
            if ln.strip().startswith('CREATE OR REPLACE FUNCTION :"schema".validate_supersession_target('):
                return i
        raise RuntimeError("validate_supersession_target CREATE line not found")

    s63_idx = find_create(s63_lines)
    # s69 defines it twice is false (once, Element 4) -- but find_create returns the first (only) hit.
    s69_idx = find_create(s69_lines)
    s63_body = lrl.extract_function_body(s63_lines, s63_idx)
    s69_body = lrl.extract_function_body(s69_lines, s69_idx)
    normalized_s63 = s63_body.replace("./led ", "./autoharn led ")
    check("RIDER-TEACH-TEXT-DIFF",
          normalized_s63 == s69_body,
          "s63's validate_supersession_target body, with every './led ' occurrence mechanically "
          "replaced by './autoharn led ', is BYTE-IDENTICAL to s69 Element 4's body -- the rider "
          "changes ONLY the printed CLI spelling, nothing else"
          if normalized_s63 == s69_body else
          "MISMATCH beyond spelling -- see diff of normalized_s63 vs s69_body", failures)


def main() -> int:  # noqa: C901
    failures: list[str] = []
    tmps: list[Path] = []
    world_pre, world_main, world_birth = "s69fxpre", "s69fxmain", "s69fxbirth"
    for w in (world_pre, world_main, world_birth):
        teardown(w)
    try:
        # ===================== WORLD PRE (s68 head, NO s69) =====================
        print(f"== scaffolding classic world {world_pre} (chain ends {CHAIN_S68[-1]}, NO s69) ==")
        wp = scaffold_classic(world_pre, CHAIN_S68)
        tmps.append(wp.parent)
        author_pre = birth_via_boundary(world_pre)
        b_pre = register(world_pre, author_pre, "claimant-b")

        # ---- RED-CLOSE-BY-NEVER-CLAIMANT ----
        bw_call(world_pre, "ledger_write",
                {"kind": "work_opened", "statement": "fixture: work_opened", "work_slug": "never-claimed", "work_title": "x",
                 "actor": author_pre})
        v_never = bw_call(world_pre, "ledger_write",
                           {"kind": "work_closed", "statement": "fixture: work_closed", "work_slug": "never-claimed",
                            "work_resolution": "shipped", "work_witness": "n/a",
                            "work_review_disposition": "deferred", "actor": author_pre})
        check("RED-CLOSE-BY-NEVER-CLAIMANT",
              v_never["disposition"] == "accepted",
              f"pre-s69 world: closing an item NOBODY ever claimed is ACCEPTED today -- "
              f"verdict={v_never}", failures)

        # ---- RED-CLOSE-BY-SUPERSEDED-CLAIMANT ----
        bw_call(world_pre, "ledger_write",
                {"kind": "work_opened", "statement": "fixture: work_opened", "work_slug": "reclaim-item", "work_title": "x",
                 "actor": author_pre})
        bw_call(world_pre, "ledger_write",
                {"kind": "work_claimed", "statement": "fixture: work_claimed", "work_slug": "reclaim-item", "actor": author_pre})
        bw_call(world_pre, "ledger_write",
                {"kind": "work_claimed", "statement": "fixture: work_claimed", "work_slug": "reclaim-item", "actor": b_pre})
        claimant_now = claimant_of(world_pre, "reclaim-item")
        v_stale_close = bw_call(world_pre, "ledger_write",
                                 {"kind": "work_closed", "statement": "fixture: work_closed", "work_slug": "reclaim-item",
                                  "work_resolution": "shipped", "work_witness": "n/a",
                                  "work_review_disposition": "deferred", "actor": author_pre})
        check("RED-CLOSE-BY-SUPERSEDED-CLAIMANT",
              v_stale_close["disposition"] == "accepted" and claimant_now == b_pre,
              f"pre-s69 world: current claimant is {b_pre!r} (claimant_now={claimant_now!r}), yet "
              f"the SUPERSEDED claimant {author_pre!r} closes successfully -- verdict="
              f"{v_stale_close}", failures)

        # ---- RED-WITNESS-ROW-WORK-CLAIMED-ACCEPTED (the autoharn2 row-1265 shape) ----
        bw_call(world_pre, "ledger_write",
                {"kind": "work_opened", "statement": "fixture: work_opened", "work_slug": "witness-shape-item", "work_title": "x",
                 "actor": author_pre})
        claim_row = bw_call(world_pre, "ledger_write",
                             {"kind": "work_claimed", "statement": "fixture: work_claimed", "work_slug": "witness-shape-item",
                              "actor": author_pre})
        v_shape = bw_call(world_pre, "ledger_write",
                           {"kind": "work_closed", "statement": "fixture: work_closed", "work_slug": "witness-shape-item",
                            "work_resolution": "shipped", "work_witness": "n/a",
                            "work_review_disposition": "witnessed",
                            "work_review_ref": f"row:{claim_row['row_id']}", "actor": author_pre})
        check("RED-WITNESS-ROW-WORK-CLAIMED-ACCEPTED",
              v_shape["disposition"] == "accepted",
              f"pre-s69 world: a --review-witness citing a work_claimed row (row "
              f"{claim_row['row_id']}, not a review/finding) is ACCEPTED as evidence today -- "
              f"verdict={v_shape}", failures)

        # ---- RED-REVIEW-REGARDS-SUPERSEDED-ACCEPTED (the experience4 431/435 shape) ----
        d1 = bw_call(world_pre, "ledger_write",
                     {"kind": "decision", "statement": "d1 (pre)", "actor": author_pre})
        d2 = bw_call(world_pre, "ledger_write",
                     {"kind": "decision", "statement": "d2 supersedes d1 (pre)",
                      "supersedes": d1["row_id"], "actor": author_pre})
        v_stale_review = bw_call(world_pre, "ledger_write",
                                  {"kind": "review", "regards": d1["row_id"],
                                   "statement": "reviewing d1 (pre, now stale)", "actor": b_pre})
        check("RED-REVIEW-REGARDS-SUPERSEDED-ACCEPTED",
              v_stale_review["disposition"] == "accepted",
              f"pre-s69 world: a review regarding row {d1['row_id']!r}, superseded by "
              f"{d2['row_id']!r}, is ACCEPTED today -- verdict={v_stale_review}", failures)

        # ===================== WORLD MAIN (s69 head) =====================
        print(f"== scaffolding classic world {world_main} (chain ends {CHAIN_S69[-1]}) ==")
        wm = scaffold_classic(world_main, CHAIN_S69)
        tmps.append(wm.parent)
        author = birth_via_boundary(world_main)
        b = register(world_main, author, "claimant-b")
        c = register(world_main, author, "claimant-c")

        # ---- GREEN-CLOSE-BY-NEVER-CLAIMANT-REFUSED ----
        bw_call(world_main, "ledger_write",
                {"kind": "work_opened", "statement": "fixture: work_opened", "work_slug": "never-claimed", "work_title": "x",
                 "actor": author})
        v_never_g = bw_call(world_main, "ledger_write",
                             {"kind": "work_closed", "statement": "fixture: work_closed", "work_slug": "never-claimed",
                              "work_resolution": "shipped", "work_witness": "n/a",
                              "work_review_disposition": "deferred", "actor": author})
        check("GREEN-CLOSE-BY-NEVER-CLAIMANT-REFUSED",
              v_never_g["disposition"] == "refused"
              and "claimant-of-record" in (v_never_g["message"] or ""),
              f"post-s69 world: closing a never-claimed item is REFUSED, teaching -- "
              f"verdict={v_never_g}", failures)

        # ---- GREEN-CLOSE-BY-SUPERSEDED-CLAIMANT-REFUSED ----
        bw_call(world_main, "ledger_write",
                {"kind": "work_opened", "statement": "fixture: work_opened", "work_slug": "reclaim-item", "work_title": "x",
                 "actor": author})
        bw_call(world_main, "ledger_write",
                {"kind": "work_claimed", "statement": "fixture: work_claimed", "work_slug": "reclaim-item", "actor": author})
        bw_call(world_main, "ledger_write",
                {"kind": "work_claimed", "statement": "fixture: work_claimed", "work_slug": "reclaim-item", "actor": b})
        v_stale_close_g = bw_call(world_main, "ledger_write",
                                   {"kind": "work_closed", "statement": "fixture: work_closed", "work_slug": "reclaim-item",
                                    "work_resolution": "shipped", "work_witness": "n/a",
                                    "work_review_disposition": "deferred", "actor": author})
        check("GREEN-CLOSE-BY-SUPERSEDED-CLAIMANT-REFUSED",
              v_stale_close_g["disposition"] == "refused"
              and "claimant-of-record" in (v_stale_close_g["message"] or ""),
              f"post-s69 world: the SUPERSEDED claimant ({author!r}) closing is now REFUSED "
              f"(current claimant {b!r}) -- verdict={v_stale_close_g}", failures)

        # ---- HAPPY-DEFEAT-AND-RECLAIM: B (the new claimant) closes -- ACCEPTED. A retrying is
        # refused (re-checked, not merely assumed). ----
        v_reclaim_close = bw_call(world_main, "ledger_write",
                                   {"kind": "work_closed", "statement": "fixture: work_closed", "work_slug": "reclaim-item",
                                    "work_resolution": "shipped", "work_witness": "n/a",
                                    "work_review_disposition": "deferred", "actor": b})
        check("HAPPY-DEFEAT-AND-RECLAIM",
              v_reclaim_close["disposition"] == "accepted",
              f"row 201 §0: A claims, B reclaims (last-claim-wins), B closes -- ACCEPTED "
              f"end-to-end (a claim is defeatable-and-reclaimable, never frozen) -- verdict="
              f"{v_reclaim_close}", failures)

        # ---- GREEN-WITNESS-ROW-WORK-CLAIMED-REFUSED ----
        bw_call(world_main, "ledger_write",
                {"kind": "work_opened", "statement": "fixture: work_opened", "work_slug": "witness-shape-item", "work_title": "x",
                 "actor": author})
        claim_row_g = bw_call(world_main, "ledger_write",
                               {"kind": "work_claimed", "statement": "fixture: work_claimed", "work_slug": "witness-shape-item",
                                "actor": author})
        v_shape_g = bw_call(world_main, "ledger_write",
                             {"kind": "work_closed", "statement": "fixture: work_closed", "work_slug": "witness-shape-item",
                              "work_resolution": "shipped", "work_witness": "n/a",
                              "work_review_disposition": "witnessed",
                              "work_review_ref": f"row:{claim_row_g['row_id']}", "actor": author})
        check("GREEN-WITNESS-ROW-WORK-CLAIMED-REFUSED",
              v_shape_g["disposition"] == "refused"
              and "is not evidence" in (v_shape_g["message"] or ""),
              f"post-s69 world: a --review-witness citing a work_claimed row is now REFUSED -- "
              f"verdict={v_shape_g}", failures)

        # ---- HAPPY-ORDINARY-CLAIMANT-CLOSE (a legitimate review witness, claimant=closer) ----
        bw_call(world_main, "ledger_write",
                {"kind": "work_opened", "statement": "fixture: work_opened", "work_slug": "ordinary-item", "work_title": "x",
                 "actor": author})
        bw_call(world_main, "ledger_write",
                {"kind": "work_claimed", "statement": "fixture: work_claimed", "work_slug": "ordinary-item", "actor": author})
        opened_row = psql_tuples(
            f"SELECT id FROM {world_main}.ledger WHERE kind='work_opened' "
            f"AND work_slug='ordinary-item';")
        real_review = bw_call(world_main, "ledger_write",
                               {"kind": "review", "regards": opened_row,
                                "statement": "reviewing ordinary-item's opening", "actor": c})
        v_happy_close = bw_call(world_main, "ledger_write",
                                 {"kind": "work_closed", "statement": "fixture: work_closed", "work_slug": "ordinary-item",
                                  "work_resolution": "shipped", "work_witness": "n/a",
                                  "work_review_disposition": "witnessed",
                                  "work_review_ref": f"row:{real_review['row_id']}",
                                  "actor": author})
        check("HAPPY-ORDINARY-CLAIMANT-CLOSE",
              v_happy_close["disposition"] == "accepted",
              f"post-s69 world: claim-then-close as the SAME actor, citing a genuine review row, "
              f"is ACCEPTED, unaffected -- verdict={v_happy_close}", failures)

        # ---- HAPPY-PLANNING-CLOSE-CHILD-CARVE-IN (both polarities) ----
        bw_call(world_main, "ledger_write",
                {"kind": "work_opened", "statement": "fixture: work_opened", "work_slug": "planning-parent", "work_title": "x",
                 "actor": author})
        bw_call(world_main, "ledger_write",
                {"kind": "work_claimed", "statement": "fixture: work_claimed", "work_slug": "planning-parent", "actor": author})
        child_open = bw_call(world_main, "ledger_write",
                              {"kind": "work_opened", "statement": "fixture: work_opened", "work_slug": "planning-child",
                               "work_title": "x", "work_parent": "planning-parent",
                               "actor": author})
        v_planning_close = bw_call(world_main, "ledger_write",
                                    {"kind": "work_closed", "statement": "fixture: work_closed", "work_slug": "planning-parent",
                                     "work_resolution": "shipped", "work_witness": "n/a",
                                     "work_review_disposition": "witnessed",
                                     "work_review_ref": f"row:{child_open['row_id']}",
                                     "actor": author})
        check("HAPPY-PLANNING-CLOSE-CHILD-CARVE-IN-legal",
              v_planning_close["disposition"] == "accepted",
              f"post-s69 world: a parent's close citing its OWN child's work_opened row as "
              f"witness -- ACCEPTED (the planning-close carve-in) -- verdict={v_planning_close}",
              failures)

        bw_call(world_main, "ledger_write",
                {"kind": "work_opened", "statement": "fixture: work_opened", "work_slug": "unrelated-item", "work_title": "x",
                 "actor": author})
        unrelated_open = psql_tuples(
            f"SELECT id FROM {world_main}.ledger WHERE kind='work_opened' "
            f"AND work_slug='unrelated-item';")
        bw_call(world_main, "ledger_write",
                {"kind": "work_opened", "statement": "fixture: work_opened", "work_slug": "planning-parent-2", "work_title": "x",
                 "actor": author})
        bw_call(world_main, "ledger_write",
                {"kind": "work_claimed", "statement": "fixture: work_claimed", "work_slug": "planning-parent-2", "actor": author})
        v_planning_close_neg = bw_call(world_main, "ledger_write",
                                        {"kind": "work_closed", "statement": "fixture: work_closed", "work_slug": "planning-parent-2",
                                         "work_resolution": "shipped", "work_witness": "n/a",
                                         "work_review_disposition": "witnessed",
                                         "work_review_ref": f"row:{unrelated_open}",
                                         "actor": author})
        check("HAPPY-PLANNING-CLOSE-CHILD-CARVE-IN-non-child-refused",
              v_planning_close_neg["disposition"] == "refused"
              and "is not evidence" in (v_planning_close_neg["message"] or ""),
              f"post-s69 world: citing a work_opened row that is NOT a child of the closing slug "
              f"is REFUSED (the same carve-in, negative polarity) -- verdict="
              f"{v_planning_close_neg}", failures)

        # ---- GREEN-REVIEW-REGARDS-SUPERSEDED-REFUSED + HAPPY-REVIEW-REGARDS-IN-FORCE-SUCCESSOR
        d1g = bw_call(world_main, "ledger_write",
                      {"kind": "decision", "statement": "d1 (main)", "actor": author})
        d2g = bw_call(world_main, "ledger_write",
                      {"kind": "decision", "statement": "d2 supersedes d1 (main)",
                       "supersedes": d1g["row_id"], "actor": author})
        v_stale_review_g = bw_call(world_main, "ledger_write",
                                    {"kind": "review", "regards": d1g["row_id"],
                                     "statement": "reviewing d1 (main, now stale)", "actor": b})
        check("GREEN-REVIEW-REGARDS-SUPERSEDED-REFUSED",
              v_stale_review_g["disposition"] == "refused"
              and str(d2g["row_id"]) in (v_stale_review_g["message"] or ""),
              f"post-s69 world: a review of the now-superseded row {d1g['row_id']!r} is REFUSED, "
              f"naming the successor {d2g['row_id']!r} -- verdict={v_stale_review_g}", failures)

        v_fresh_review = bw_call(world_main, "ledger_write",
                                  {"kind": "review", "regards": d2g["row_id"],
                                   "statement": "reviewing d2, the in-force successor",
                                   "actor": b})
        check("HAPPY-REVIEW-REGARDS-IN-FORCE-SUCCESSOR",
              v_fresh_review["disposition"] == "accepted",
              f"post-s69 world: a review regarding the IN-FORCE successor {d2g['row_id']!r} -- "
              f"ACCEPTED -- verdict={v_fresh_review}", failures)

        # ---- HAPPY-S56-RESERVATION-DISCHARGE-UNAFFECTED ----
        target_row = bw_call(world_main, "ledger_write",
                              {"kind": "decision", "statement": "target of a reservation review",
                               "actor": author})
        review1 = bw_call(world_main, "review_write",
                           {"regards": target_row["row_id"], "statement": "attest, with a concern",
                            "verdict": "attest_with_reservations", "independence": "self-review",
                            "basis": "a minor concern, tracked not blocking", "actor": b})
        check("HAPPY-S56-RESERVATION-STEP-1-accepted",
              review1["disposition"] == "accepted",
              f"the reservation-carrying review itself -- accepted -- verdict={review1}", failures)
        outstanding_before = psql_tuples(
            f"SELECT count(*) FROM {world_main}.reservations_outstanding "
            f"WHERE review_id = {review1['row_id']};")
        review2 = bw_call(world_main, "review_write",
                           {"regards": review1["row_id"], "statement": "reservation dispositioned",
                            "verdict": "attest", "independence": "self-review",
                            "basis": "reservation addressed", "actor": c})
        outstanding_after = psql_tuples(
            f"SELECT count(*) FROM {world_main}.reservations_outstanding "
            f"WHERE review_id = {review1['row_id']};")
        check("HAPPY-S56-RESERVATION-DISCHARGE-UNAFFECTED",
              review2["disposition"] == "accepted"
              and outstanding_before == "1" and outstanding_after == "0",
              f"post-s69 world: a review REGARDING an in-force review row (the s56 "
              f"reservation-discharge shape) is ACCEPTED, unaffected by §3 -- before={outstanding_before} "
              f"after={outstanding_after} verdict={review2}", failures)

        # ---- RIDER-TEACH-TEXT-DIFF (mechanical, file-level) ----
        rider_diff(failures)

        # ---- REFUSALS-JOURNAL-AS-WRITE-REFUSED ----
        refused_ids = [v["refusal_id"] for v in
                       (v_never_g, v_stale_close_g, v_shape_g, v_stale_review_g,
                        v_planning_close_neg) if v.get("refusal_id")]
        journaled = psql_tuples(
            f"SELECT count(*) FROM {world_main}.ledger WHERE kind='write_refused' "
            f"AND id IN ({','.join(str(i) for i in refused_ids)});") if refused_ids else "0"
        check("REFUSALS-JOURNAL-AS-WRITE-REFUSED",
              len(refused_ids) == 5 and journaled == "5",
              f"every s69 refusal above journals as a committed write_refused row -- "
              f"{len(refused_ids)} refusal ids, {journaled} found as write_refused rows",
              failures)

        # ---- ZERO-FRICTION-BIRTH ----
        print(f"== scaffolding classic world {world_birth} (chain ends {CHAIN_S69[-1]}, fresh "
              f"birth) ==")
        wb = scaffold_classic(world_birth, CHAIN_S69)
        tmps.append(wb.parent)
        author_birth = birth_via_boundary(world_birth)
        v_birth_ok = bw_call(world_birth, "ledger_write",
                              {"kind": "note", "statement": "zero-friction birth note",
                               "actor": author_birth})
        check("ZERO-FRICTION-BIRTH-accepted",
              v_birth_ok["disposition"] == "accepted",
              f"a fresh world's own s40/s43/s69 birth sequence, then an ordinary note write -- "
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
              f"./autoharn verify-chain after every refusal above -- exit={rc_v}, "
              f"INTACT+ORACLE-CONFIRMED in output="
              f"{('INTACT' in out_v) and ('REFUSAL-ORACLE-CONFIRMED' in out_v)}, oracle count="
              f"{oracle_count} == sequence={oracle_seq}", failures)

        # ---- AGREE: SQL/ASP work-layer differential ----
        judge_agree(world_main, failures, "AGREE-sql-asp-work-differential")

    finally:
        for w in (world_pre, world_main, world_birth):
            teardown(w)
        for t in tmps:
            sh(["rm", "-rf", str(t)])

    print(f"\n{'ALL GREEN' if not failures else 'FAILURES: ' + ', '.join(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
