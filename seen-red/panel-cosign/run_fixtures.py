#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T01:31:47Z
#   last-change: 2026-07-15T01:31:47Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity, live-ledger proof for the panel's co-sign write path
(panel/backend/cosign.py) and its live disposition read path (panel/backend/ledger_read.py
`decomposition_items`/`commissions`), against a scratch schema/kernel pair on the `toy` db
(NEVER `autoharn1` -- BUILD SPEC v2 r5 sec 10, WP-4 package).

Real infra, no mocks: mirrors seen-red/s25-commission-kind/'s own two-schema-pair idiom -- the
birth chain applied through s25 (so `note`/`commission` kinds and s17's stamp/independence gate
all exist), a scratch schema/kern/role torn down BEFORE and AFTER this file runs so a re-run
never trips over residue. The panel's own backend modules (`panel.backend.config.PanelConfig`,
`panel.backend.cosign`, `panel.backend.ledger_read`) are exercised DIRECTLY against this scratch
schema -- a `PanelConfig` is hand-built here (not `config.load_config`, which always resolves
this checkout's own real `deployment.json`) pointing at the scratch schema, and the co-sign path
is driven through `bootstrap/templates/led.tmpl` with `PICKUP_DEPLOYMENT` overridden to a scratch
deployment record -- the SAME override mechanism seen-red/s25-commission-kind/run_fixtures.py's
case (g) already uses to run `led` against a schema other than this checkout's default.

Cases (spec sec 10; GREEN(d) is r5/round-4's new case, closing the round-4 finding, and runs
LAST as instructed -- after every earlier case in this file has executed against the same
scratch schema and commission row):

  GREEN        -- maintainer self-review attest against an author `note` item row (the item row
                  itself) succeeds; `maintainer_cosigned` returns it; a live `decomposition_items()`
                  call derives `status=='COSIGNED'` via the item-row fast path (also witnesses a
                  `note` row IS reviewable).
  GREEN(c)     -- a second item citing two further `note` rows as `row:` witnesses: co-signing
                  ONE witness -> `PARTIAL`; co-signing the SECOND too -> `COSIGNED`.
  RED(a)       -- a `managerial` co-sign in this unstamped scratch schema is REFUSED by
                  `validate_independence`; `cosign.cosign` surfaces the teach-text with `ok=False`.
  RED(b)       -- a co-sign with no `LED_ACTOR` against the author item row is refused as
                  self-review by `validate_review` (actor honesty is load-bearing).
  RED(c')      -- a THIRD, independent `note` row citing the SAME `panel-item:<cid>:<iid>` token
                  as an existing item (a duplicate, not a `--supersedes`): `decomposition_items()`
                  returns that item at `status=='AMBIGUOUS'`, `row_id=None`, `ambiguous_row_ids`
                  naming both colliding rows; co-signing ONE of those rows directly still succeeds.
  GREEN(d)     -- (r5/round-4) two more minimal items under a PREFIX-ADJACENT item-id pair
                  (`X1`/`X10`); asserts `commissions()`'s `item_count` agrees with
                  `len(decomposition_items(...).items)`, that `X1`/`X10` are DISTINCT entries, and
                  that the RED(c') ambiguous pair contributes exactly ONE item slot to the total
                  (see that case's own function docstring for how "before vs after" is measured,
                  and a disclosed interpretive note on the package instruction's exact wording).

Usage: python3 seen-red/panel-cosign/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "seen-red"))           # _fixture_env.py lives one level above every
                                                       # seen-red/<case>/, same insert every sibling
                                                       # driver uses (see _fixture_env.py's own docstring)
sys.path.insert(0, str(REPO / "panel" / "backend"))  # config.py/cosign.py/ledger_read.py/disposition.py

from _fixture_env import fixture_pghost  # noqa: E402

import config as panel_config  # noqa: E402
import cosign as panel_cosign  # noqa: E402
import ledger_read  # noqa: E402

PGHOST = fixture_pghost()
PGDB = "toy"
SCHEMA, KERN, ROLE = "pcosignfx", "pcosignfx_kernel", "pcosignfx_rw"
LINEAGE = REPO / "kernel" / "lineage"
LED_TMPL = REPO / "bootstrap" / "templates" / "led.tmpl"

# Same birth-chain list seen-red/s25-commission-kind/run_fixtures.py applies (through s25, so
# `note`/`commission` join ledger_kind_check, and s17 gives the stamp/independence gate this
# fixture's RED(a) exercises).
CHAIN_TO_S25 = [
    "s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
    "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql",
]

SCRATCH_DEPLOYMENT_PATH = Path(f"/tmp/.{SCHEMA}_deployment.json")


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def teardown() -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; DROP SCHEMA IF EXISTS {KERN} CASCADE; "
        f"DROP OWNED BY {ROLE};"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {ROLE};"])
    SCRATCH_DEPLOYMENT_PATH.unlink(missing_ok=True)


def apply_lineage() -> subprocess.CompletedProcess[str]:
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={SCHEMA}", "-v", f"kern={KERN}", "-v", f"role={ROLE}"]
    for f in CHAIN_TO_S25:
        args += ["-f", str(LINEAGE / f)]
    return sh(args)


def psql(sql: str) -> subprocess.CompletedProcess[str]:
    prefix = f"SET ROLE {ROLE};\nSET search_path = {SCHEMA}, {KERN};\n"
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-tA", "-q",
               "-c", prefix + sql])


def insert_note(refs: str, statement: str) -> int:
    """Insert a `kind='note'` row as the default connection principal (`author` -- s15 seeds
    `principal_role` mapping `:role` to it), exactly the shape WP-3's seed script authors.
    Returns the new row's id."""
    r = psql(
        f"INSERT INTO ledger (kind, statement, refs) VALUES "
        f"('note', {_pg_str(statement)}, {_pg_str(refs)}) RETURNING id;"
    )
    assert r.returncode == 0, f"insert_note failed: {r.stderr}"
    return int(r.stdout.strip())


def insert_commission(statement: str) -> int:
    r = psql(f"INSERT INTO ledger (kind, statement) VALUES ('commission', {_pg_str(statement)}) RETURNING id;")
    assert r.returncode == 0, f"insert_commission failed: {r.stderr}"
    return int(r.stdout.strip())


def _pg_str(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def build_cfg() -> panel_config.PanelConfig:
    """Hand-build a PanelConfig pointing at the scratch schema -- `config.load_config` always
    resolves THIS checkout's own real `deployment.json` (autoharn1), which this fixture must
    never touch. `led_path` points at `bootstrap/templates/led.tmpl` directly (not the repo-root
    `./led` shim, which hardcodes `PICKUP_DEPLOYMENT=<repo>/deployment.json`); the scratch
    deployment record this fixture writes to `SCRATCH_DEPLOYMENT_PATH` is supplied via the SAME
    `PICKUP_DEPLOYMENT` env var override seen-red/s25-commission-kind/run_fixtures.py's case (g)
    already uses, set process-wide (`os.environ`) before any `cosign.cosign` call below so
    `cosign._run_led`'s own `env.update(os.environ)` inherits it."""
    deployment = panel_config.deployment_record.DeploymentRecord(
        db=PGDB, host=PGHOST, schema=SCHEMA, kern=KERN, role=ROLE, name=SCHEMA,
    )
    return panel_config.PanelConfig(
        repo_root=REPO,
        deployment=deployment,
        pghost=PGHOST,
        maintainer_principal="maintainer",
        poll_interval=2.0,
        bind_host="127.0.0.1",
        bind_port=8420,
        led_path=LED_TMPL,
    )


def main() -> int:
    teardown()
    failures: list[str] = []

    print("== applying birth chain through s25 to the scratch schema ==")
    r = apply_lineage()
    if r.returncode != 0:
        print("APPLY FAILED:", r.stdout[-1000:], r.stderr[-1000:])
        teardown()
        return 1
    print("scratch schema applied clean.\n")

    # Point every `./led`/led.tmpl invocation this fixture makes at the scratch schema, not this
    # checkout's own autoharn1 deployment.json.
    SCRATCH_DEPLOYMENT_PATH.write_text(json.dumps(
        {"db": PGDB, "host": PGHOST, "schema": SCHEMA, "kern": KERN, "role": ROLE, "name": SCHEMA}
    ), encoding="utf-8")
    os.environ["PICKUP_DEPLOYMENT"] = str(SCRATCH_DEPLOYMENT_PATH)
    os.environ.pop("LED_ACTOR", None)  # RED(b) depends on this being genuinely unset

    cfg = build_cfg()

    # register the maintainer principal (distinct from the default connection principal `author`,
    # seeded by s15 itself and mapped to `:role`) -- the panel's own startup does this idempotently
    # (spec sec 1/6); done here directly since this fixture is not driving app.py's startup path.
    rp = psql("INSERT INTO principal (name, agent_class) VALUES ('maintainer','human') "
              "ON CONFLICT (name) DO NOTHING;")
    assert rp.returncode == 0, f"register maintainer failed: {rp.stderr}"

    cid = insert_commission("seen-red/panel-cosign specimen commission")
    print(f"commission row id = {cid}\n")

    # --- GREEN: item-row fast path -- a note row IS reviewable, maintainer self-review COSIGNS it
    item1_row = insert_note(f"panel-item:{cid}:ITEM1", "ITEM1 -- no witnesses yet, item row itself co-signable")
    res1 = panel_cosign.cosign(cfg, item1_row, "attest", "self-review", "maintainer endorses ITEM1 directly")
    ok_g1 = res1.ok
    check("GREEN-note-row-reviewable-and-cosignable", ok_g1,
          f"cosign(item1_row={item1_row}) ok={res1.ok} exit={res1.exit_code} stderr={res1.stderr.strip()[:200]!r}",
          failures)

    disc1 = ledger_read.maintainer_cosigned(cfg, item1_row)
    ok_g2 = disc1 is not None and disc1["actor_name"] == "maintainer" and disc1["verdict"] == "attest"
    check("GREEN-maintainer-cosigned-reads-back", ok_g2, f"maintainer_cosigned(item1_row)={disc1}", failures)

    decomp1 = ledger_read.decomposition_items(cfg, cid)
    item1 = next((i for i in decomp1.items if getattr(i, "item_id", None) == "ITEM1"), None)
    ok_g3 = (item1 is not None and isinstance(item1, ledger_read.ResolvedItem)
             and item1.status == "COSIGNED")
    check("GREEN-item-row-fast-path-status", ok_g3,
          f"decomposition_items(cid)'s ITEM1 = {item1!r}", failures)

    # --- GREEN(c): per-witness tally -- PARTIAL then COSIGNED as each witness is individually cosigned
    w1 = insert_note("", "a plain note row, ITEM2's first row: witness (not a decomposition item itself)")
    w2 = insert_note("", "a plain note row, ITEM2's second row: witness")
    item2_row = insert_note(f"panel-item:{cid}:ITEM2 row:{w1} row:{w2}",
                             "ITEM2 -- two row: witnesses, neither cosigned yet")

    decomp_pre = ledger_read.decomposition_items(cfg, cid)
    item2_pre = next((i for i in decomp_pre.items if getattr(i, "item_id", None) == "ITEM2"), None)
    ok_c0 = item2_pre is not None and item2_pre.status == "WITNESSED"
    check("GREENc-witnessed-before-any-cosign", ok_c0, f"ITEM2 status before any witness cosign = {item2_pre!r}", failures)

    res_w1 = panel_cosign.cosign(cfg, w1, "attest", "self-review", "maintainer endorses ITEM2's first witness")
    decomp_partial = ledger_read.decomposition_items(cfg, cid)
    item2_partial = next((i for i in decomp_partial.items if getattr(i, "item_id", None) == "ITEM2"), None)
    ok_c1 = res_w1.ok and item2_partial is not None and item2_partial.status == "PARTIAL"
    check("GREENc-partial-one-of-two-witnesses", ok_c1,
          f"cosign(w1) ok={res_w1.ok}, ITEM2 status={item2_partial.status if item2_partial else None!r} (want PARTIAL)",
          failures)

    res_w2 = panel_cosign.cosign(cfg, w2, "attest", "self-review", "maintainer endorses ITEM2's second witness")
    decomp_cosigned = ledger_read.decomposition_items(cfg, cid)
    item2_cosigned = next((i for i in decomp_cosigned.items if getattr(i, "item_id", None) == "ITEM2"), None)
    ok_c2 = res_w2.ok and item2_cosigned is not None and item2_cosigned.status == "COSIGNED"
    check("GREENc-cosigned-both-witnesses", ok_c2,
          f"cosign(w2) ok={res_w2.ok}, ITEM2 status={item2_cosigned.status if item2_cosigned else None!r} (want COSIGNED)",
          failures)

    # --- RED(a): a managerial co-sign in this unstamped scratch schema is REFUSED, teach-text surfaced
    res_managerial = panel_cosign.cosign(cfg, item1_row, "attest", "managerial", "claiming independence with no stamp")
    ok_a = (not res_managerial.ok
            and "claiming independence" in res_managerial.stderr
            and "self-review" in res_managerial.stderr)
    check("REDa-managerial-refused-unstamped", ok_a,
          f"ok={res_managerial.ok} exit={res_managerial.exit_code} stderr={res_managerial.stderr.strip()[-300:]!r}",
          failures)

    # --- RED(b): no LED_ACTOR -> default connection principal is `author`, same as item1's own
    # actor -> validate_review's SoD refusal fires. Exercised one level below cosign.cosign's public
    # function (which always names actor=cfg.maintainer_principal by design -- see cosign.py's own
    # docstring on actor honesty being "hard") via its `_run_led` helper with actor=None, to prove
    # the underlying kernel mechanism cosign.py's design leans on.
    assert "LED_ACTOR" not in os.environ, "RED(b) requires LED_ACTOR genuinely unset in this process's env"
    res_noactor = panel_cosign._run_led(
        cfg, ["review", str(item1_row), "attest", "self-review", "unset-actor probe"], actor=None,
    )
    ok_b = (not res_noactor.ok
            and "author may not countersign it" in res_noactor.stderr)
    check("REDb-no-actor-self-review-refused", ok_b,
          f"ok={res_noactor.ok} exit={res_noactor.exit_code} stderr={res_noactor.stderr.strip()[-300:]!r}",
          failures)

    # --- RED(c'): a duplicate item claim -- item_count BEFORE the duplicate lands (captured here
    # for GREEN(d)'s own before/after comparison below).
    item_count_before_dup = _item_count(cfg, cid)
    item1_dup_row = insert_note(f"panel-item:{cid}:ITEM1", "a duplicate ITEM1 claim, authored via a fresh row, NOT --supersedes")

    decomp_amb = ledger_read.decomposition_items(cfg, cid)
    item1_amb = next((i for i in decomp_amb.items if getattr(i, "item_id", None) == "ITEM1"), None)
    ok_cprime1 = (item1_amb is not None and isinstance(item1_amb, ledger_read.AmbiguousItem)
                  and set(item1_amb.candidate_row_ids) == {item1_row, item1_dup_row})
    check("REDcprime-ambiguous-item-carried-as-data", ok_cprime1,
          f"ITEM1 = {item1_amb!r} (want AmbiguousItem carrying both {item1_row} and {item1_dup_row})", failures)

    res_amb_cosign = panel_cosign.cosign(cfg, item1_dup_row, "attest", "self-review",
                                          "endorsing one of the ambiguous candidates directly")
    ok_cprime2 = res_amb_cosign.ok
    check("REDcprime-ambiguous-candidate-still-cosignable", ok_cprime2,
          f"cosign(item1_dup_row={item1_dup_row}) ok={res_amb_cosign.ok} exit={res_amb_cosign.exit_code} "
          f"stderr={res_amb_cosign.stderr.strip()[:200]!r}", failures)

    item_count_after_dup = _item_count(cfg, cid)

    # --- GREEN(d), r5/round-4: prefix-adjacent item ids under the SAME commission, run LAST -------
    x1_row = insert_note(f"panel-item:{cid}:X1", "X1 -- minimal, no witnesses, renders OPEN")
    x10_row = insert_note(f"panel-item:{cid}:X10", "X10 -- minimal, no witnesses, renders OPEN; X1 is a literal substring of this token")

    commissions_list = ledger_read.commissions(cfg)
    this_commission = next((c for c in commissions_list if c["row_id"] == cid), None)
    decomp_final = ledger_read.decomposition_items(cfg, cid)

    # (i) commissions()'s item_count agrees EXACTLY with the live decomposition_items() item count --
    # the exact agreement the round-4 finding demanded, proven against a real ledger.
    ok_d_i = this_commission is not None and this_commission["item_count"] == len(decomp_final.items)
    check("GREENd-item-count-agrees-with-decomposition", ok_d_i,
          f"commissions()[cid]['item_count']={this_commission['item_count'] if this_commission else None} "
          f"len(decomposition_items(cid).items)={len(decomp_final.items)}", failures)

    # (ii) X1 and X10 both appear as DISTINCT entries -- proves the shared fetch_parsed_item_rows/
    # group_item_rows pipeline is exercised by both call sites without collapsing the prefix-adjacent pair.
    ids_final = [i.item_id for i in decomp_final.items]
    ok_d_ii = "X1" in ids_final and "X10" in ids_final and ids_final.count("X1") == 1 and ids_final.count("X10") == 1
    check("GREENd-prefix-adjacent-ids-distinct-live", ok_d_ii,
          f"item_ids present = {sorted(ids_final)!r} (want both 'X1' and 'X10', each exactly once)", failures)

    # (iii) the RED(c') ambiguous pair contributes exactly ONE item slot, not two.
    #
    # DISCLOSED INTERPRETIVE NOTE (ADR-0013 Rule 2/CLAUDE.md hazard duty -- stated, not silently
    # resolved): the WP-4 package instruction reads "compare item_count before and after RED(c')'s
    # duplicate is authored and confirm it increases by exactly 1, not 2, when the duplicate
    # lands." Read completely literally that cannot be the right assertion for THIS fixture's own
    # ordering: ITEM1 already exists as an ordinary singleton (1 slot) *before* its duplicate is
    # authored (it is the very row GREEN's item-row-fast-path case cosigns), so item_count already
    # counts it once beforehand -- landing a second row under the SAME item_id merges into that
    # existing slot rather than minting a new one, so the correct, checkable delta at THIS
    # boundary is 0 (unchanged), never 1. What both readings agree on, and what actually matters
    # (spec sec 4: "an ambiguous group still counts as one item slot"), is the invariant this
    # assertion checks directly: the pair's own item_id contributes exactly one entry to
    # `item_id_groups`/`item_count`'s output, regardless of whether it has one row or two --
    # i.e. the count is UNCHANGED when the colliding second row lands (never +1, and never the
    # even-more-broken +2 a per-ROW-instead-of-per-item-id count would produce).
    ok_d_iii = item_count_after_dup == item_count_before_dup
    check("GREENd-ambiguous-pair-one-slot-not-two", ok_d_iii,
          f"item_count before RED(c')'s duplicate={item_count_before_dup}, after={item_count_after_dup} "
          f"(want equal -- the pair's item_id contributes exactly one slot, unaffected by the second "
          f"colliding row landing)", failures)

    print()
    if failures:
        print(f"FAILURES ({len(failures)}): {failures}")
        teardown()
        return 1

    teardown()
    r_res1 = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc",
                 f"SELECT nspname FROM pg_namespace WHERE nspname LIKE '{SCHEMA}%';"])
    r_res2 = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc",
                 f"SELECT rolname FROM pg_roles WHERE rolname LIKE '{ROLE}%';"])
    residue_clean = r_res1.stdout.strip() == "" and r_res2.stdout.strip() == ""
    print(f"[{'ok' if residue_clean else 'FAIL'}] zero residue: schemas={r_res1.stdout.strip()!r} roles={r_res2.stdout.strip()!r}")
    if not residue_clean:
        return 1

    print("\nALL CASES OK -- panel co-sign write path + live disposition read path both-polarity proof clean.")
    return 0


def _item_count(cfg: panel_config.PanelConfig, commission_row: int) -> int:
    commissions_list = ledger_read.commissions(cfg)
    entry = next((c for c in commissions_list if c["row_id"] == commission_row), None)
    assert entry is not None, f"commission row {commission_row} not found in commissions(cfg)"
    return entry["item_count"]


if __name__ == "__main__":
    sys.exit(main())
