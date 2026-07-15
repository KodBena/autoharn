#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-06T16:54:20Z
#   last-change: 2026-07-14T01:24:26Z
#   contributors: 37017f46/main, be693afb/main, a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""acts_edb -- the ACTS EDB + SQL floor for the ledger_acts.lp consumers (consult 25 §2.3).

Producer ONE (SQL floor) and the EDB feed for producer TWO (ASP ledger_acts.lp) of the acts<->ledger
differential. INDEPENDENCE (I6, ADR-0000): the SQL floor shares no code path with clingo; the two
agreeing bit-identically is the substance of the differential.

The acts consumers reason over TWO sources: the s15-shaped ledger (the subject's record) and an
independent act stream. On the SCRATCH lineage the act stream is apparatus-authored side tables (the
DTO/support-scratch idiom); on the real e15 run it is acts.act in the harness DB, parsed by the CC
adapter. This module reads the scratch side tables; ledger_acts_scratch.py authors them.

acts EDB families (the oracle §4 classification is applied at fixture-authoring time, into the
`relevant` flag -- apparatus-authored, exactly as the support affirm/assumes EDB is):
  act(A). act_target(A,T). ledger_relevant_act(A). ledger_ref(R,A). ledger_claim(R,T). regards(Rev,T).

regards is a KERNEL-SHAPE family ledger_edb declares-excluded; this module emits it for the s15
lineage so stale_attestation can consume it, leaving ledger_edb.py BYTE-IDENTICAL (non-foreclosure
§1.4). Read-only on every ledger; id-is-order throughout (design §3 rule 2).

REAL-RUN DERIVATION — WHAT INCREMENT 4 PROVES AND WHAT IT DOES NOT (surfaced by the out-of-frame
audit, finding 4). On the SCRATCH fixture, `ledger_ref/2`, `ledger_claim/2`, and per-act
`relevant` are HAND-AUTHORED clean ground truth. That proves the CONSUMER ARITHMETIC (the ASP<->SQL
differential over ledger_acts.lp) is correct — it does NOT prove the acts<->ledger MATCHING is
tractable, and the matching is the real difficulty: the s15 ledger carries NO `act_id` (its columns
are evidence/refs/regards/enacts), so on the real run the row<->act edge must be DERIVED, not read.
The Increment-5 rehearsal wires that derivation over acts.act + the s15 ledger, along these lines,
and NO earlier:
  - `ledger_relevant_act(A)` : the oracle §4 classification applied per acts.act row (plan_item_*,
    delegation_*, and a tool_call that WRITES the fenced dir are relevant; a read tool_call, a
    message, a tool_result are not).
  - `ledger_claim(R,T)`      : a ledger row whose `evidence` names a fenced-dir path T (an
    implementation-milestone claim) → matched against `act.target`.
  - `ledger_ref(R,A)`        : a DERIVED, inherently-fuzzy edge (evidence-path == act.target, within
    a timing window / id order) — the candidate the differential flags; the FUZZY cases are
    DESCRIPTIVE and ADJUDICATION DISPOSES (F28, measurement (a)), never a hard match here.
So "consumers green on the fixtures" is necessary, not sufficient: it certifies the arithmetic; the
derivation + adjudication is the rehearsal/run's load-bearing work, deliberately not built here."""
from __future__ import annotations

import os
import sys

from clingo_run import quote_term
from ledger_edb import PGHOST, Target, export

# The shown vocabulary of ledger_acts.lp -- the differential compares both producers on exactly these.
ACTS_PREDS = ("act_ledgered", "unledgered_lr", "claim_matched",
              "stale_attestation", "stale_attest", "stale_nonattest",
              "claimed_without_act", "unledgered_span")


def _epistemic_target(schema: str) -> Target:
    """This module ALWAYS reasons over an apparatus-authored scratch schema in `epistemic`
    (`marriage_acts_scratch` and kin) -- never a registered deployment target (nla/e15-e18/toy), so
    it constructs its `Target` directly rather than through `ledger_edb.resolve()` / `targets.resolve()`
    (engine/targets.py, design/ORCH-USE-MODE-ENGINE-WIRING.md item 1): those now refuse LOUDLY on a name
    outside the registry (the toy-collision defect they were built to foreclose), and an apparatus
    scratch schema name was never meant to pass through that registry at all."""
    return Target(schema, db="epistemic", schema=schema, kern="kernel")


def acts_manifest(schema: str) -> dict[str, str]:
    """Capability manifest for the acts layer (§5, F49). Every family PRODUCED or DEFERRED with its
    basis -- a scratch lineage lacking the acts side tables gets the consumers DEFERRED, never silent."""
    t = _epistemic_target(schema)
    has_acts = t.has_relation(f"{schema}.acts")
    m: dict[str, str] = {}
    for fam in ("act_ledgered", "unledgered_lr", "unledgered_span"):
        m[fam] = ("PRODUCED (basis: acts + ledger_ref + oracle §4 relevance)" if has_acts
                  else "DEFERRED (no acts side table on this target -- not a silent empty)")
    for fam in ("claim_matched", "claimed_without_act"):
        m[fam] = ("PRODUCED (basis: ledger_claim + acts targets + supersession closure)" if has_acts
                  else "DEFERRED (no acts/ledger_claim side table)")
    m["stale_attestation"] = ("PRODUCED (basis: ledger regards + supersedes/amends, id-ordered)"
                              if t.has_col("regards") else
                              "DEFERRED (no regards column -- a lean/nla target cannot say)")
    # stale_attest/stale_nonattest (finding 29's verdict-aware refinement) are ACTS_PREDS members
    # too (F50: a family neither PRODUCED nor DEFERRED loudly is exactly the silent-family defect
    # this manifest exists to foreclose) -- basis is stale_attestation further split by
    # review_detail.verdict, so their availability tracks THAT relation's presence, not `regards`
    # alone (a target can carry `regards` with no review_detail row).
    for fam in ("stale_attest", "stale_nonattest"):
        m[fam] = ("PRODUCED (basis: stale_attestation refined by review_detail.verdict, id-ordered)"
                  if t.has_relation(f"{schema}.review_detail") else
                  "DEFERRED (no review_detail relation -- verdict split unavailable)")
    # SSOT invariant (ADR-0000/ADR-0012 P1): the manifest's keys are exactly ACTS_PREDS, not a
    # hand-typed subset that can silently drift from it (F50's root cause) -- a future predicate
    # added to ACTS_PREDS with no matching manifest entry now fails loudly here, at construction
    # time, instead of passing the F49 completeness test silently.
    assert set(m) == set(ACTS_PREDS), (
        f"acts_manifest/ACTS_PREDS drift: {set(ACTS_PREDS) ^ set(m)} -- every ACTS_PREDS family "
        f"must be declared PRODUCED or DEFERRED here (F49-class silent-family defect).")
    return m


def acts_edb(schema: str) -> str:
    """The base ledger EDB (ledger_edb over the scratch schema) PLUS the acts families the ASP
    ledger_acts.lp consumes. Apparatus-authored side tables on the scratch schema; regards from the
    ledger.regards column (emitted here, not in ledger_edb -- §1.4)."""
    os.environ["LEDGER_DB"] = "epistemic"
    os.environ["LEDGER_SCHEMA"] = schema
    try:
        base = export(schema).edb_text()
    finally:
        del os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"]
    t = _epistemic_target(schema)
    lines = [base, "% ---- acts EDB (scratch-only; oracle §4 relevance baked into `relevant`) ----"]
    for row in t.rows(f"SELECT id, coalesce(target,'') , relevant::text FROM {schema}.acts ORDER BY id;"):
        aid, tgt, rel = row
        lines.append(f"act({int(aid)}).")
        if tgt:
            lines.append(f"act_target({int(aid)},{quote_term(tgt)}).")
        if rel == "true":
            lines.append(f"ledger_relevant_act({int(aid)}).")
    for row in t.rows(f"SELECT row_id, act_id FROM {schema}.ledger_ref ORDER BY row_id, act_id;"):
        lines.append(f"ledger_ref({int(row[0])},{int(row[1])}).")
    for row in t.rows(f"SELECT row_id, target FROM {schema}.ledger_claim ORDER BY row_id;"):
        lines.append(f"ledger_claim({int(row[0])},{quote_term(row[1])}).")
    for row in t.rows(f"SELECT id, regards FROM {schema}.ledger WHERE regards IS NOT NULL ORDER BY id;"):
        lines.append(f"regards({int(row[0])},{int(row[1])}).")
    # review_verdict/2 for verdict-aware staleness (finding 29) — only where a review_detail relation
    # exists on this lineage (a lean/scratch target without it emits none; stale_attestation stays the
    # union, §1.6 additive). Keyed on the review row id, verdict verbatim.
    if t.has_relation(f"{schema}.review_detail"):
        for row in t.rows(f"SELECT ledger_id, verdict FROM {schema}.review_detail ORDER BY ledger_id;"):
            lines.append(f"review_verdict({int(row[0])},{quote_term(row[1])}).")
    return "\n".join(lines) + "\n"


def acts_floor_atoms(schema: str) -> set[str]:
    """The SQL floor's acts-consumer atoms for `schema` (read-only). Reuses the id-ordered
    supersession closure (P1: one home for in_force/superseded). Gaps-and-islands for the spans."""
    t = _epistemic_target(schema)
    rel = t.rel()
    # verdict-aware staleness (finding 29): split `stale` by review_detail.verdict, but ONLY where the
    # relation exists (matching the ASP, which emits stale_attest/nonattest only where review_verdict is
    # present). A stale attest = load-bearing; a stale non-attest (refuse/reservations) = benign.
    has_rd = t.has_relation(f"{schema}.review_detail")
    stale_v_cte = (f", stale_v AS (SELECT s.rev, s.t, rd.verdict FROM stale s "
                   f"LEFT JOIN {schema}.review_detail rd ON rd.ledger_id = s.rev)" if has_rd else "")
    stale_v_sel = ("""
    UNION ALL SELECT 'stale_attest('||rev||','||t||')' FROM stale_v WHERE verdict = 'attest'
    UNION ALL SELECT 'stale_nonattest('||rev||','||t||')' FROM stale_v WHERE verdict IS NOT NULL AND verdict <> 'attest'
    """ if has_rd else "")
    sql = f"""
    WITH RECURSIVE
      sup AS (SELECT id AS x, supersedes AS y FROM {rel} WHERE supersedes IS NOT NULL),
      sup_star(x,y) AS (
        SELECT x,y FROM sup UNION SELECT s.x, ss.y FROM sup s JOIN sup_star ss ON s.y = ss.x),
      superseded AS (SELECT DISTINCT y AS id FROM sup_star),
      in_force AS (SELECT id FROM {rel} WHERE id NOT IN (SELECT id FROM superseded)),
      lr AS (SELECT id FROM {schema}.acts WHERE relevant),
      refd AS (SELECT DISTINCT act_id AS id FROM {schema}.ledger_ref),
      unl AS (SELECT id FROM lr WHERE id NOT IN (SELECT id FROM refd)),
      island AS (SELECT id, id - row_number() OVER (ORDER BY id) AS g FROM unl),
      spans AS (SELECT min(id) AS f, max(id) AS e FROM island GROUP BY g),
      cm AS (SELECT DISTINCT lc.row_id AS r FROM {schema}.ledger_claim lc
             JOIN {schema}.acts a ON a.target = lc.target AND a.relevant),
      cwa AS (SELECT DISTINCT lc.row_id FROM {schema}.ledger_claim lc
              JOIN in_force f ON f.id = lc.row_id
              WHERE lc.row_id NOT IN (SELECT r FROM cm)),
      stale AS (SELECT l.id AS rev, l.regards AS t FROM {rel} l
                WHERE l.regards IS NOT NULL
                  AND EXISTS (SELECT 1 FROM {rel} s
                              WHERE (s.supersedes = l.regards OR s.amends = l.regards) AND s.id > l.id))
      {stale_v_cte}
    SELECT 'act_ledgered('||id||')' FROM refd
    UNION ALL SELECT 'unledgered_lr('||id||')' FROM unl
    UNION ALL SELECT 'claim_matched('||r||')' FROM cm
    UNION ALL SELECT 'stale_attestation('||rev||','||t||')' FROM stale
    UNION ALL SELECT 'claimed_without_act('||row_id||')' FROM cwa
    UNION ALL SELECT 'unledgered_span('||f||','||e||')' FROM spans
    {stale_v_sel}
    ;"""
    out = t.run(sql).stdout
    return {line.strip() for line in out.splitlines() if line.strip()}


def main(argv: list[str] | None = None) -> int:
    for name in (argv if argv is not None else sys.argv[1:]) or ["marriage_acts_scratch"]:
        atoms = acts_floor_atoms(name)
        print(f"# acts_floor(SQL) -- {name}: {len(atoms)} atoms")
        for a in sorted(atoms):
            print(f"  {a}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
