#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T20:17:26Z
#   last-change: 2026-07-15T21:15:53Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""ledger_reader_allowlist — the s31 standing mechanical detect: every ledger reader is a
DECLARED type (design/FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md §2/§4.3, RATIFIED 2026-07-15;
kernel/lineage/s31-supersession-uniform-retraction.sql, ledger item supersession-semantics-closure).

THE RULE IT MECHANIZES: every view/function reading the ledger is exactly one of two declared
types — a CURRENT-TRUTH reader (factors through `ledger_current`, the one SQL home of the
in-force projection — its definition contains NO raw `ledger` reference) or a HISTORY/FORENSIC
reader (reads raw `ledger` and is NAMED on the closed allowlist below, with its reason). A reader
that is neither is REFUSED with teach-text naming both discharge paths. This is what forecloses
the CLASS — the NEXT misfactored reader, not today's cells (ADR-0011 Rule 4): a future delta
adding a view that quantifies over raw `ledger` on its own judgment turns this gate red until it
either factors through the projection or claims the allowlist with a written reason.

SURFACE CHOICE (spec §4.3 says "the delta's .detect sibling or a gates/ member — choose the
surface that can actually enumerate readers, and justify"): a gates/ member ON A SCRATCH APPLY.
The .detect sibling fingerprints ONE delta's presence on an already-applied schema; it cannot
quantify over the reader universe. Static SQL-file parsing would have to replay fifteen deltas'
CREATE OR REPLACE layering to learn which definition of each object is live — the database does
exactly that for real, so this gate applies the full birth chain (kernel/lineage, s15..s31) to a
throwaway schema pair in the TOY db and interrogates the resulting catalog
(pg_get_viewdef/pg_get_functiondef), the same live-catalog technique every sNN .detect already
trusts. Cost: one scratch apply (~seconds) — accepted; this is a DB-dependent gate and says so
(it is run at delta-authoring/acceptance time and by the s31 seen-red fixture, not wired into a
per-commit hook).

The spec's stronger surface — full raw-table REVOKE (GRANT-level unrepresentability) — was
assessed and NOT taken: the legitimate history readers (row-hash chain, led --recent's marked
display, the write-boundary triggers, duplicate_open's slug-burned read) all need raw SELECT, and
the reading role is ONE role — revoking raw ledger from :role would break every declared history
reader listed below. The allowlist gate is the spec's own named honest floor for that case.

RED POLARITY (--red): creates a deliberately misfactored scratch view (its own inline
NOT EXISTS(supersedes) copy over raw ledger — the exact ADR-0012 P1 two-writers drift s31
collapsed) in the scratch schema, expects THIS gate to refuse it, prints the refusal, exits 0
iff the refusal fired. Banked: seen-red/s31-supersession-uniform-retraction/.

Exit 0 clean; exit 1 listing every undeclared reader. Run from repo root:
    python3 gates/ledger_reader_allowlist.py [--red] [--keep]
Lazy imports banned.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LINEAGE = REPO / "kernel" / "lineage"
sys.path.insert(0, str(REPO / "filing"))
from pghost_resolve import resolve_pghost  # noqa: E402  (the ONE host home -- never a literal default)

PGHOST, DB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"
SCHEMA, KERN, ROLE = "s31gate", "s31gate_kernel", "s31gate_rw"

CHAIN = [
    "s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
    "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s28-work-parent-edge.sql",
    "s29-obligation-item-key-and-typed-close.sql", "s30-typed-dependency-edges.sql",
    "s31-supersession-uniform-retraction.sql", "s32-edge-views-single-home.sql",
    "s33-composite-discharge.sql",
]
# s33 (kernel/lineage/s33-composite-discharge.sql) extends this SAME gate's scratch CHAIN so its
# re-issued objects (work_item_current/work_item_violations/work_item_strict_blockers/
# validate_work_item) are exercised by the scratch apply below -- it introduces NO new raw-`ledger`
# reference anywhere (work_item_current's new effective_state column composes with the already-
# vestigial work_item_strict_blockers(); work_item_violations' three new composite-tracking CTEs
# read ledger_current exclusively, matching orphaned_by_retraction's own posture), so no ALLOWLIST
# dict entry changes.
# s32 (kernel/lineage/s32-edge-views-single-home.sql) extends this SAME gate rather than minting a
# second one (ADR-0012 P1): its own edge-source collapse (F3/F6, the categorical-refactor consult)
# is exactly the class of change this allowlist exists to keep honest -- two of its four new views
# (work_edge_parent/work_edge_blocks_close) are DECLARED RAW/history readers by design (s32's own
# header WHY), added below with their reasons; the other two (work_edge_obligation/
# discharging_attest) read only ledger_current/other named views and classify clean with no entry.

# ---------------------------------------------------------------------------------------------
# THE CLOSED ALLOWLIST (spec §2's declared history readers + the residual correctly-scoped inline
# legs, each with its reason — mirrored from s31's own CLOSURE STATEMENT, which is the prose
# twin of this dict; the two are reviewed together on any change). Key: object name as it
# appears in the scratch schema. An object here may read raw `ledger`; an object NOT here must
# contain no raw-`ledger` reference at all (i.e. factor through ledger_current exclusively).
# ---------------------------------------------------------------------------------------------
ALLOWLIST: dict[str, str] = {
    # -- the projection home itself (cannot factor through itself) --
    "ledger_current": "THE in-force projection home — its inline anti-join IS the one authoritative encoding (s15+).",
    "countersigned_in_force": "the projection home's countersign sibling — same single authoritative anti-join (s15).",
    # -- declared history / forensic readers --
    "review_stamp_distinctness": "row-addressed stamp forensics across review rows (s17/s21) — history by type.",
    "work_item_violations": "mixed by declared design: seven history/defense-in-depth members over raw history "
                            "(duplicate_open is SLUG-BURNED by the ratified fork; the graph members answer "
                            "'did this shape ever get written'); its orphaned_by_retraction member reads "
                            "ledger_current (s31).",
    "zz_set_row_hash": "row-hash chain writer (s26) — every row must chain, superseded or not.",
    "validate_enacts": "write-boundary BEFORE INSERT trigger — cannot read a view excluding the inserting row.",
    "validate_review": "write-boundary BEFORE INSERT trigger — same reason.",
    "validate_amends": "write-boundary BEFORE INSERT trigger — same reason.",
    "validate_answers": "write-boundary BEFORE INSERT trigger — same reason.",
    "validate_work_item": "write-boundary BEFORE INSERT trigger; its identity checks (slug ever opened, "
                          "would-cycle against history) are deliberately history-typed (slug burned, spec §3).",
    "validate_independence": "reads (stamp_session, stamp_agent) off the two named rows — row-addressed "
                             "forensics, not a truth projection (s17/s21/s29).",
    "work_parent_would_cycle": "trigger helper — cycle check against history (s28; slug-burned world: a "
                               "retracted open still occupies its slug's place in the one-open-per-slug order).",
    "work_depends_on_would_cycle": "trigger helper — cycle check over blocks-close history (s30).",
    # -- current-truth readers with a RESIDUAL correctly-scoped inline leg (the spec's own
    #    'already filtered' finding — each raw read is a row-scoped in-force anti-join on the
    #    specific candidate row, not an unfiltered quantification) --
    "review_gap": "actor-keyed obligation view (s15) — both raw reads carry their own row-scoped "
                  "in-force anti-joins, correct since s15; outside s31's four re-issued members.",
    "question_status": "question-row side factors through ledger_current (s31); the per-answer legs are "
                       "row-scoped in-force anti-joins on each answer candidate (already filtered).",
    "work_review_gap": "close-row side factors through ledger_current (s31); the discharge-review leg now "
                       "composes with discharging_attest (s32) — ZERO raw-ledger legs remain; entry kept "
                       "as a record of the collapse, vestigial (s32's own LIMITS disclosure).",
    "work_item_strict_blockers": "edges CTE composes with work_edge_obligation, review_unresolved's discharge "
                                 "leg composes with discharging_attest (both s32) — ZERO raw-ledger legs "
                                 "remain; entry kept as a record of the collapse, vestigial (s32's own "
                                 "LIMITS disclosure).",
    # -- s32 (kernel/lineage/s32-edge-views-single-home.sql): the two RAW edge-source views (F3),
    #    declared history readers by design — every current consumer of this shape (the two
    #    would_cycle trigger helpers above, work_item_violations' dangling_parent/parent_cycle/
    #    blocks_close_cycle members) is itself a declared history reader needing the UNRETRACTED
    #    reading; work_edge_obligation (below, no entry needed) supplies the in-force reading by
    #    joining these two to ledger_current on each edge's own carrying row.
    "work_edge_parent": "single home of the RAW s28 parent-edge relation (s32) — reused by "
                        "work_parent_would_cycle and work_item_violations' dangling_parent/parent_cycle, "
                        "all declared history readers needing every such edge ever written.",
    "work_edge_blocks_close": "single home of the RAW s30 blocks-close edge relation (s32) — reused by "
                              "work_depends_on_would_cycle and work_item_violations.blocks_close_cycle, "
                              "same reasoning one edge kind over.",
}

# A raw-`ledger` TABLE ACCESS: FROM/JOIN/INTO/UPDATE followed by an optionally schema-qualified
# `ledger`. \bledger\b never matches inside ledger_current (underscore is a word character, so
# there is no word boundary before '_'), and requiring the access keyword excludes the word
# "ledger" inside refusal/teach TEXT ("Ledger policy: ..."), which is prose, not a read --
# witnessed on this gate's own first run: one_row_per_insert/set_stamp matched on their exception
# strings alone and were false-positived until this keyword anchor was added.
RAW_LEDGER = re.compile(r"\b(?:FROM|JOIN|INTO|UPDATE)\s+(?:[a-z0-9_]+\.)?ledger\b(?!_)",
                        re.IGNORECASE)

TEACH = (
    "REFUSED — undeclared raw-`ledger` reader(s). Every ledger reader must be a DECLARED type\n"
    "(s31 / FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC §2). Two discharge paths, pick one:\n"
    "  1. FACTOR THROUGH THE IN-FORCE PROJECTION: read `ledger_current` (SQL's one home of the\n"
    "     un-superseded reading) instead of raw `ledger` — the correct path for any reader that\n"
    "     answers a CURRENT-TRUTH question ('what is the state now').\n"
    "  2. CLAIM THE HISTORY ALLOWLIST: if the reader genuinely answers a HISTORY/FORENSIC\n"
    "     question (a hash chain, a marked display, a write-boundary trigger, a slug-burn check),\n"
    "     add it to ALLOWLIST in gates/ledger_reader_allowlist.py WITH ITS REASON — a named,\n"
    "     reviewable declaration, never a silent bypass.\n"
)


def psql(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1", *args],
                        capture_output=True, text=True)
    if check and cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-800:]} {cp.stderr[-800:]}")
    return cp


def teardown() -> None:
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-c",
                    f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; DROP SCHEMA IF EXISTS {KERN} CASCADE; "  # declared-drop: s31gate (declared scratch/test reset)
                    f"DROP OWNED BY {ROLE}; DROP ROLE IF EXISTS {ROLE};"], capture_output=True, text=True)


def scratch_apply() -> None:
    args: list[str] = ["-v", f"schema={SCHEMA}", "-v", f"kern={KERN}", "-v", f"role={ROLE}"]
    for f in CHAIN:
        args += ["-f", str(LINEAGE / f)]
    psql(*args)


def enumerate_readers() -> list[tuple[str, str, str]]:
    """Every (kind, name, definition) in the scratch schema whose live definition references the
    ledger table at all (raw or via ledger_current) — the reader universe, from the live catalog."""
    out: list[tuple[str, str, str]] = []
    views = psql("-tA", "-c",
                 f"SELECT viewname FROM pg_views WHERE schemaname = '{SCHEMA}' ORDER BY viewname;").stdout
    for v in [x for x in views.splitlines() if x.strip()]:
        d = psql("-tA", "-c", f"SELECT pg_get_viewdef('{SCHEMA}.{v}'::regclass);").stdout
        out.append(("view", v, d))
    funcs = psql("-tA", "-c",
                 f"SELECT p.oid FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
                 f"WHERE n.nspname = '{SCHEMA}' ORDER BY p.proname;").stdout
    for oid in [x for x in funcs.splitlines() if x.strip()]:
        d = psql("-tA", "-c", f"SELECT pg_get_functiondef({oid});").stdout
        name = psql("-tA", "-c", f"SELECT proname FROM pg_proc WHERE oid = {oid};").stdout.strip()
        out.append(("function", name, d))
    return out


def classify(readers: list[tuple[str, str, str]]) -> tuple[list[str], list[str]]:
    """Returns (report_lines, violations)."""
    report: list[str] = []
    violations: list[str] = []
    for kind, name, definition in readers:
        raw = bool(RAW_LEDGER.search(definition))
        if not raw:
            report.append(f"  ok   {kind:8} {name:32} no raw-ledger access (current-truth-factored, or reads no ledger at all)")
        elif name in ALLOWLIST:
            report.append(f"  ok   {kind:8} {name:32} ALLOWLISTED: {ALLOWLIST[name]}")
        else:
            report.append(f"  !!   {kind:8} {name:32} UNDECLARED raw-ledger reader")
            violations.append(f"{kind} {SCHEMA}.{name}")
    return report, violations


RED_VIEW = "zz_red_misfactored_probe"
RED_DDL = f"""
CREATE VIEW {SCHEMA}.{RED_VIEW} AS
SELECT l.id, l.kind FROM {SCHEMA}.ledger l
WHERE NOT EXISTS (SELECT 1 FROM {SCHEMA}.ledger s WHERE s.supersedes = l.id);
"""


def main(argv: list[str]) -> int:
    red = "--red" in argv
    keep = "--keep" in argv
    teardown()
    try:
        scratch_apply()
        if red:
            psql("-c", RED_DDL)
        readers = enumerate_readers()
        report, violations = classify(readers)
        print(f"# ledger_reader_allowlist -- scratch apply {DB}.{SCHEMA} (chain {CHAIN[0]}..{CHAIN[-1]})")
        for line in report:
            print(line)
        if red:
            # the negative control: the deliberately misfactored view MUST be refused.
            hit = any(RED_VIEW in v for v in violations)
            others = [v for v in violations if RED_VIEW not in v]
            if hit and not others:
                print(f"\n{TEACH}")
                print(f"RED POLARITY OK -- {RED_VIEW} (a deliberate inline NOT EXISTS(supersedes) copy over "
                      f"raw ledger) was REFUSED as an undeclared reader; every standing reader stayed declared.")
                return 0
            print(f"\nRED POLARITY FAILED -- refusal fired={hit}, unexpected violations={others}")
            return 1
        if violations:
            print(f"\n{TEACH}")
            for v in violations:
                print(f"  !! {v}")
            return 1
        print("\nledger-reader-allowlist: clean -- every ledger reader is a declared type "
              "(current-truth factored through ledger_current, or named on the history allowlist with its reason).")
        return 0
    finally:
        if not keep:
            teardown()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
