#!/usr/bin/env python3
"""close_sweep — the e14 standing close-sweep instrument set (consult 19 §H, ratified AC11 + R3b).

Three measure-first readouts, each an ADR-0011-Rule-1 DECLARED enforcement surface (the net ships
WITH the deferral, not after its first failure — the 2026-07-02 amendment). None is a gate; each is a
review-queue feed the standing odd link adjudicates. All read-only.

  R3b (§4.3 amendment; the domain-entry measurement of §G leg 1) — after any IN-FORCE subject amends
     edge (A defeats clause `scope` of T), adjudicate EVERY SUBSEQUENT citation of the amended target
     T (supersedes/enacts/amends/answers/regards/refs = T) for FRAGMENT-SIZED reliance and how the
     subject expressed it: does the citing row's rationale narrow its own row-granular edge (a
     scope-narrowing qualifier — the tell the honest target is narrower than the row, case B1), or is
     the reliance whole-row and unqualified? R3b converts "are we in the first-class-fragment domain"
     from an assertion into a datum (consult 19 §G leg 1).

  condition-1 (cannot-quote, §H — mechanized via the tee.log) — scan the run's off-host statement log
     for QUOTATION-CONTRACT REFUSALS (a subject amends INSERT the write boundary rejected: the
     validate_amends RAISE signatures). Every hit is a fired-or-near-fired condition-1 event for
     odd-link adjudication — a defeat the subject could not express as one contiguous verbatim
     quotation (the DTO re-entry condition 1, consult 19 §1.7/§E).

  condition-3 (fragment-sized edge demand, §H — review-only, the weakest surface, stated not hidden)
     — read every edge-carrying row's rationale for scope-narrowing qualifiers ('only', 'except',
     'aside from', and kin) and every subject QUESTION about referencing PART of a row; any hit is a
     condition-3 candidate (an edge demand only a fragment can satisfy — DTO re-entry condition 3).

Consumes {session}.ledger (+ amends/answers/regards/refs where the schema carries them) and, for
condition-1, the off-host tee.log (--log=PATH, repeatable). Read-only; nothing is written.
"""
from __future__ import annotations

import glob
import os
import re
import sys

from ledger_target import LedgerTarget, resolve

# Resolved once per report() from the target NAME; every query and the tee.log role come through it
# (the SSOT foreclosing the wrong-place / missing-apparatus-object class — ledger_target.py). This
# instrument crashed on `nla` before the SSOT because it hardcoded `kernel.principal` (link 21 F49).
TARGET: LedgerTarget
DEFAULT_LOG_GLOB = "/home/bork/pg_log/epistemic-*.log"

# scope-narrowing qualifiers (condition-3): the prose tell that a row-granular edge relies on a
# NARROWER unit than the row — the honest target is a fragment (consult 19 §H condition-3 (i)).
NARROW_RE = re.compile(
    r"\b(only|except|aside from|apart from|other than|excluding|save for|just the|solely|"
    r"not the|the .*? clause|that clause|this clause|one clause|per-clause|clause-only)\b",
    re.IGNORECASE)
# a subject question about referencing PART of a row (condition-3 (ii)).
FRAGMENT_Q_RE = re.compile(
    r"(part of (a|the|this|that) row|reference (part|a clause|a fragment)|which clause|"
    r"cite (part|a clause|a fragment)|refer to (part|a clause))", re.IGNORECASE)
# condition-1: the validate_amends refusal signatures (quotation-contract rejections) in the tee.log.
REFUSAL_RE = re.compile(
    r"amends_scope must be a VERBATIM quotation|amends_scope '.*?' occurs more than once|"
    r"amends_scope must quote the defeated clause|a scopeless amends|"
    r"amends_scope is meaningless without an amends target|"
    r"amends must resolve to an EARLIER own-session row", re.IGNORECASE)
# a role-attributed statement/error line in the tee.log (subject role only, for condition-1).
LOG_LINE_RE = re.compile(r"role=(?P<role>\S+)\b.*?(?P<msg>(ERROR|STATEMENT|LOG):.*)$")


def _rows(sql: str) -> list[list[str]]:
    return TARGET.rows(sql)


def _has_col(col: str) -> bool:
    return TARGET.has_col(col)


def r3b(session: str) -> None:
    rel = TARGET.rel()
    if not _has_col("amends"):
        print("R3b — the schema carries no `amends` column; no clause-defeat domain to sweep.\n")
        return
    # in-force subject amends edges (author not superseded, target not superseded) authored by the
    # subject — whose actor value is resolved per the target's actor model (a kernel.principal id on
    # the epistemic lineage, the text role on the isolated `nla` ledger), never a hardcoded lookup.
    subj = TARGET.subject_actor_sql
    amends = _rows(
        f"SELECT a.id, a.amends, coalesce(a.amends_scope,'') FROM {rel} a "
        f"WHERE a.amends IS NOT NULL AND a.actor = {subj} "
        f"AND NOT EXISTS (SELECT 1 FROM {rel} s WHERE s.supersedes = a.id) "
        f"AND NOT EXISTS (SELECT 1 FROM {rel} s WHERE s.supersedes = a.amends);")
    print(f"R3b — subsequent-citation adjudication over IN-FORCE subject amends edges "
          f"({len(amends)} such edge(s)):")
    if not amends:
        print("  (no in-force subject amends edge — R3 success branch did not fire; nothing to sweep)\n")
        return
    # the citing-edge columns the schema carries
    cite_cols = [c for c in ("supersedes", "enacts", "amends", "answers", "regards", "refs")
                 if _has_col(c)]
    for a_id, t_id, scope in amends:
        a_id, t_id = int(a_id), int(t_id)
        print(f"  amended target #{t_id} (defeated clause: '{scope[:50]}') — subsequent citations:")
        found = False
        for col in cite_cols:
            if col == "enacts":
                cits = _rows(f"SELECT e.id, coalesce(e.rationale,'') FROM {rel} e "
                             f"CROSS JOIN LATERAL unnest(e.enacts) AS u(tid) "
                             f"WHERE u.tid = {t_id} AND e.id > {a_id};")
            elif col == "refs":
                cits = _rows(f"SELECT id, coalesce(rationale,'') FROM {rel} "
                             f"WHERE refs ~ '(^|[^0-9]){t_id}([^0-9]|$)' AND id > {a_id};")
            else:
                cits = _rows(f"SELECT id, coalesce(rationale,'') FROM {rel} "
                             f"WHERE {col} = {t_id} AND id > {a_id};")
            for cid, rat in cits:
                found = True
                narrowed = bool(NARROW_RE.search(rat))
                verdict = ("FRAGMENT-SIZED reliance EXPRESSED (scope-narrowing qualifier in rationale"
                           " -> case B1, DTO re-entry cond. 3 candidate)" if narrowed
                           else "WHOLE-ROW reliance, unqualified (row-granular citation of an amended"
                           " row -> the B1 over-broad-citation domain; review whether the honest"
                           " target is the surviving clause)")
                print(f"    {col}({cid}->{t_id}): {verdict}")
        if not found:
            print("    (no subsequent citation of this amended target — not yet in the domain)")
    print()


def condition1(session: str, log_paths: list[str]) -> None:
    role = TARGET.login_role
    hits: list[str] = []
    for p in log_paths:
        if not os.path.exists(p):
            continue
        for line in open(p, encoding="utf-8", errors="replace"):
            if role in line and REFUSAL_RE.search(line):
                hits.append(line.rstrip("\n").strip())
    print(f"condition-1 (cannot-quote) — quotation-contract refusals by the subject role in the "
          f"tee.log ({len(hits)} hit(s)):")
    if hits:
        for h in hits:
            print(f"  FIRED: {h[-160:]}")
        print("  -> each is a defeat the subject could not express as one contiguous verbatim "
              "quotation; adjudicate for DTO re-entry condition 1 (consult 19 §1.7).")
    else:
        print("  (none — no quotation-contract refusal in the supplied log; supply the run's "
              "off-host tee.log via --log=PATH so this surface is not blind)")
    print()


def condition3(session: str) -> None:
    rel = TARGET.rel()
    cite_cols = [c for c in ("supersedes", "enacts", "amends", "answers", "regards", "refs")
                 if _has_col(c)]
    edge_pred = " OR ".join(
        (f"cardinality({c}) > 0" if c == "enacts" else f"{c} IS NOT NULL") for c in cite_cols) or "false"
    edge_rows = _rows(f"SELECT id, kind, coalesce(statement,''), coalesce(rationale,'') FROM {rel} "
                      f"WHERE {edge_pred};")
    q_rows = _rows(f"SELECT id, coalesce(statement,''), coalesce(rationale,'') FROM {rel} "
                   f"WHERE kind='question';")
    narrow_hits = [(int(i), k, s) for i, k, s, r in edge_rows if NARROW_RE.search(r) or NARROW_RE.search(s)]
    q_hits = [(int(i), s) for i, s, r in q_rows if FRAGMENT_Q_RE.search(s) or FRAGMENT_Q_RE.search(r)]
    print(f"condition-3 (fragment-sized edge demand, review-only) — scope-narrowing qualifiers on "
          f"edge-carrying rows ({len(narrow_hits)}) + fragment-reference questions ({len(q_hits)}):")
    for i, k, s in narrow_hits:
        print(f"  CANDIDATE {k} #{i}: edge rationale/statement narrows its row-granular edge — '{s[:60]}'")
    for i, s in q_hits:
        print(f"  CANDIDATE question #{i}: asks about referencing PART of a row — '{s[:60]}'")
    if not (narrow_hits or q_hits):
        print("  (none — no scope-narrowing qualifier on an edge row, no fragment-reference question)")
    print()


def report(session: str, log_paths: list[str]) -> None:
    global TARGET
    TARGET = resolve(session)
    print(f"# e14 close-sweep (consult 19 §H) — {TARGET.db}.{TARGET.rel()} "
          f"(+ tee.log for condition-1: {len(log_paths)} path(s))\n")
    r3b(session)
    condition1(session, log_paths)
    condition3(session)


def main() -> int:
    args = sys.argv[1:]
    log_paths: list[str] = []
    sessions: list[str] = []
    for a in args:
        if a.startswith("--log="):
            log_paths.append(os.path.expanduser(a.split("=", 1)[1]))
        else:
            sessions.append(a)
    if not log_paths:
        log_paths = sorted(glob.glob(DEFAULT_LOG_GLOB))
    for s in (sessions or ["s14"]):
        report(s, log_paths)
    return 0


if __name__ == "__main__":
    sys.exit(main())
