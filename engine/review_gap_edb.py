#!/usr/bin/env python3
"""review_gap_edb -- the EDB builder for the content-free-review-discharge audit (tracker item
`content-free-review-audit`). WITNESSED SPECIMEN driving this whole file: run12 ledger row 20 --
a `review` row whose entire statement is `"test"` (4 chars), verdict=attest, independence=
technical, regards=4, written by the reviewer principal while syntax-testing against the LIVE
ledger. Under `<schema>.review_gap`'s discharge semantics (kernel/lineage/s13-schema.sql:
"NOT EXISTS (a distinct-actor, unsuperseded, attest review of l)" -- content is NEVER examined by
the view), that junk row MECHANICALLY DISCHARGED row 4's countersign obligation. Row 4 happened
to also get a genuine review (row 22, 935 chars) later, but the discharge had already fired via
row 20 alone -- ANY qualifying attest discharges, the view's own `NOT EXISTS` is satisfied by the
first one found, not the "best" one -- and none of run12's six reviewer passes ever flagged row
20; it stands attested in the append-only record. The maintainer's cosignature-spectre concern
(implementers take undue license and lie) applies to reviewers too: a reviewer can discharge a
countersign obligation with a statement that says nothing about what was actually checked.

WHAT THIS AUDIT FLAGS (the exact predicate, mirroring `<schema>.review_gap`'s own SQL, restated
here because this module's whole job is to give an ASP/SQL pair an EDB shaped to re-derive it
independently): a `review` row R FLAGS iff
  (a) R discharges SOME obliged row L under review_gap's own semantics -- R regards L, R carries
      a review_detail.verdict='attest', R.actor != L.actor, L.actor is under a countersign
      obligation (`countersign_obligation.obliges_actor = L.actor`), and NEITHER L nor R is
      whole-row-superseded (the view's own two `NOT EXISTS (... supersedes = ...)` clauses,
      single-hop -- review_gap does not use the multi-hop sup_star closure ledger_tnow.lp's
      OTHER consumers use; mirrored here exactly, not "improved")
  AND (b) R's OWN statement is content-free: its whitespace-normalized length is strictly below
      engine/review_gap_thresholds.CONTENT_FREE_STATEMENT_THRESHOLD (see that module's own
      docstring for the corpus-measured justification of the exact number).

THE HONEST LIMIT, STATED PLAINLY (per this work item's own instruction, and ADR-0000 Rule 2(a)'s
closure-statement discipline: name what is NOT covered, don't bury it). This check is a LENGTH
HEURISTIC, nothing more. "test" (4 chars) is caught. Hollow-but-plausible prose of normal length
-- "Reviewed and everything looks correct, no issues found, approved for merge." (75+ chars,
content-FREE in substance but not in shape) -- is NOT caught, and this module makes no claim that
it ever could be from length alone. This audit family NEVER substitutes for fresh-eyes review of
reviews: it catches the "test"-shaped instance of the cosignature-spectre class, not the class
itself. Its verdict vocabulary is FLAGGED, never VIOLATED, for exactly this reason (a short
statement is suspicious, not proven dishonest -- a legitimate terse review DOES exist: "Confirmed,
matches row 4's stated criteria exactly." is 42 chars and genuine).

MARRIAGE-GRADE, PER HOUSE DOCTRINE (vestigial_documentation/design/ORCH-LEDGER-LOGIC-MARRIAGE.md; the same discipline
engine/ledger_floor.py / engine/contemp_floor.py / engine/preamble_floor.py already carry): TWO
independent producers -- the ASP program (engine/lp/review_gap_audit.lp) consuming THIS module's
EDB, and the SQL floor (engine/review_gap_floor.py) re-deriving the SAME judgment directly from
the live ledger in one query -- differentialed bit-identically by engine/review_gap_differential.py.

NO TIME CORRELATION, SO NO SHARED-EDB / ONE-ANCHOR CONSTRAINT (unlike engine/contemp_edb.py /
engine/preamble_ordering.lp's Part 2/Part 3, which reason over event TIMESTAMPS and therefore
share one 32-bit-safe anchor across every family per design/ORCH-CONTEMPORANEITY-PART3-SPEC.md
§4's binding rule). This audit is a purely RELATIONAL judgment over ledger ROWS (id-ordered
supersession, actor identity, verdict, statement length) -- no `ts` value crosses into this EDB
at all, so this module owns its OWN small export() rather than riding contemp_edb.py's; there is
no anchor to reuse and no wraparound hazard to protect against (ADR-0000 Rule 2(a): the type that
forecloses "two exports on different anchors compared" is simply "this domain never emits a T",
not a second copy of contemp_edb.py's 32-bit guard).

CAPABILITY-GATED, HONESTLY (mirrors engine/contemp_edb.py's Capability/produced-vs-capable idiom
-- I12/F49: a schema this audit cannot run on DECLARES the absence and its reason, never silently
emits zero facts read as "nothing to flag"). This audit needs FOUR things on the live schema:
the `actor` column (s15), the `regards` column (s15), the `countersign_obligation` table (s15),
and the `review_detail` table (s13/s15) -- all four are s15-era-or-earlier and travel together in
practice (review_gap itself cannot exist without all four), but each is checked independently
rather than assumed, per ledger_edb.py's own established posture.

Read-only. Lazy imports banned (top-of-file only)."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from ledger_edb import Target, resolve
from review_gap_thresholds import is_content_free

HERE = Path(__file__).resolve().parent
REVIEW_GAP_LP = HERE / "lp" / "review_gap_audit.lp"

_REQUIRED_FAMILIES = ("actor_column", "regards_column", "countersign_obligation", "review_detail")


@dataclass(frozen=True)
class Capability:
    """A fact family's status on this target -- mirrors engine/contemp_edb.py's own Capability
    (produced/capable/reason), reused here in miniature since this domain has only four gated
    families and none of the produced-but-empty-vs-unwired distinction contemp_edb.py needs for
    its journal streams (a schema either carries these four DDL objects or it does not; there is
    no "wired but nothing happened yet" axis for a table/column's mere PRESENCE)."""
    family: str
    produced: bool
    reason: str


class CapabilityError(RuntimeError):
    """Raised when a caller requests a fact family this target's schema does not carry."""


@dataclass
class ReviewGapEdbExport:
    target_name: str
    facts: list[str] = field(default_factory=list)
    capabilities: list[Capability] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    def produced_families(self) -> set[str]:
        return {c.family for c in self.capabilities if c.produced}

    def full_capable(self) -> bool:
        return set(_REQUIRED_FAMILIES) <= self.produced_families()

    def exclusions(self) -> list[Capability]:
        return [c for c in self.capabilities if not c.produced]

    def edb_text(self) -> str:
        head = [f"% ==== review-gap-audit EDB: target '{self.target_name}'",
                f"% ==== produced: {sorted(self.produced_families())}"]
        for c in self.exclusions():
            head.append(f"% ==== EXCLUDED {c.family}: {c.reason}")
        return "\n".join(head) + "\n" + "\n".join(self.facts) + "\n"


def export(target_name: str) -> ReviewGapEdbExport:
    """Build the review-gap-audit EDB for `target_name` (a ledger_edb.resolve()-able name, e.g.
    a curated registry target or a scratch/standing deployment). Read-only throughout; never
    raises for an honest capability shortfall (the caller decides how to report an incapable
    target -- see engine/review_gap_audit.py's own build_report())."""
    t: Target = resolve(target_name)
    exp = ReviewGapEdbExport(target_name=target_name)

    has_actor = t.has_col("actor")
    has_regards = t.has_col("regards")
    has_obligation_tbl = t.has_relation(f"{t.schema}.countersign_obligation")
    has_review_detail_tbl = t.has_relation(f"{t.schema}.review_detail")

    exp.capabilities.append(Capability(
        "actor_column", has_actor,
        "actor column present (s15-era schema)" if has_actor
        else "no actor column on this schema (pre-s15) -- capability absent"))
    exp.capabilities.append(Capability(
        "regards_column", has_regards,
        "regards column present (s15-era schema)" if has_regards
        else "no regards column on this schema (pre-s15) -- capability absent"))
    exp.capabilities.append(Capability(
        "countersign_obligation", has_obligation_tbl,
        "countersign_obligation table present" if has_obligation_tbl
        else "no countersign_obligation relation on this schema (pre-s15) -- capability absent"))
    exp.capabilities.append(Capability(
        "review_detail", has_review_detail_tbl,
        "review_detail table present" if has_review_detail_tbl
        else "no review_detail relation on this schema (pre-s13/s15) -- capability absent"))

    if not exp.full_capable():
        return exp  # the caller (build_report) reports the exclusion(s); no facts to emit yet.

    rel = t.rel()

    # ---- obliged/1 -- countersign_obligation.obliges_actor, one fact per DISTINCT obliged actor
    # WHOSE OWN SCOPE IS NOT REVOKED (kernel/lineage/s57-obligation-revocation-event.sql, design/
    # FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part A): revocation is now a typed ledger event
    # (kind='obligation_revoked', obligation_revoked_scope=<scope>) rather than a DELETE of the
    # countersign_obligation row -- the row stands forever, so "in force" is a derivation over
    # events, mirrored HERE independently of kernel/lineage/s32-edge-views-single-home.sql's
    # review_gap view (which s57 re-issues with the SAME exclusion) exactly the way this whole
    # module's docstring already states for the other three families (I6/ADR-0000 INDEP): a
    # SEPARATELY AUTHORED SQL query reaching the same judgment, not an import of the kernel view.
    # GATED on the ledger carrying obligation_revoked_scope AT ALL (not merely on there being zero
    # rows of that kind): a pre-s57 schema has NO such column, so referencing it unconditionally
    # would be a bare "column does not exist" SQL error, not an empty result -- this capability
    # check is what keeps the extension behavior-preserving on every schema this module ran
    # against before s57 existed, rather than merely assuming the column's absence is harmless.
    has_revocation = t.has_col("obligation_revoked_scope")
    obliged_sql = f"SELECT DISTINCT o.obliges_actor FROM {t.schema}.countersign_obligation o"
    if has_revocation:
        obliged_sql += (
            f" WHERE NOT EXISTS (SELECT 1 FROM {rel} rv WHERE rv.kind = 'obligation_revoked' "
            f"AND rv.obligation_revoked_scope = o.scope "
            f"AND NOT EXISTS (SELECT 1 FROM {rel} s2 WHERE s2.supersedes = rv.id))"
        )
    n = 0
    for (actor,) in t.rows(obliged_sql + ";"):
        exp.facts.append(f"obliged({int(actor)}).")
        n += 1
    exp.counts["obliged"] = n

    # ---- row_actor/2 -- every row with a non-NULL actor (matches contemp_edb.py's own E7 family)
    n = 0
    for rid, actor in t.rows(f"SELECT id, actor FROM {rel} WHERE actor IS NOT NULL ORDER BY id;"):
        exp.facts.append(f"row_actor({int(rid)},{int(actor)}).")
        n += 1
    exp.counts["row_actor"] = n

    # ---- superseded/1 -- SINGLE-HOP (matches review_gap's own NOT EXISTS(s.supersedes=id), never
    # the multi-hop sup_star transitive closure ledger_tnow.lp's OTHER consumers use -- this
    # domain's own semantics is what must be mirrored, not a different consumer's).
    n = 0
    for (sid,) in t.rows(f"SELECT DISTINCT supersedes FROM {rel} WHERE supersedes IS NOT NULL;"):
        exp.facts.append(f"superseded({int(sid)}).")
        n += 1
    exp.counts["superseded"] = n

    # ---- review_row/1, review_regards/2, review_attest/1, content_free/1 -- review-kind rows
    # only. `content_free/1` is computed HERE, in Python, via the ONE shared predicate
    # (review_gap_thresholds.is_content_free) -- text stays out of the EDB itself (mirrors
    # ledger_edb.py's own "IDS ARE THE INTERCHANGE; TEXT STAYS HOME" rule; only the BOOLEAN
    # verdict crosses, never the statement text).
    n_review, n_regards, n_attest, n_cf = 0, 0, 0, 0
    for rid, regards, verdict, statement in t.rows(
        f"SELECT l.id, l.regards, d.verdict, l.statement FROM {rel} l "
        f"JOIN {t.schema}.review_detail d ON d.ledger_id = l.id WHERE l.kind = 'review' ORDER BY l.id;"
    ):
        rid_i = int(rid)
        exp.facts.append(f"review_row({rid_i}).")
        n_review += 1
        if regards not in (None, ""):
            exp.facts.append(f"review_regards({rid_i},{int(regards)}).")
            n_regards += 1
        if verdict == "attest":
            exp.facts.append(f"review_attest({rid_i}).")
            n_attest += 1
        if is_content_free(statement or ""):
            exp.facts.append(f"content_free({rid_i}).")
            n_cf += 1
    exp.counts["review_row"] = n_review
    exp.counts["review_regards"] = n_regards
    exp.counts["review_attest"] = n_attest
    exp.counts["content_free"] = n_cf

    return exp


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("usage: review_gap_edb.py <target-name>", file=sys.stderr)
        return 2
    exp = export(args[0])
    print(exp.edb_text())
    print(f"% counts: {exp.counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
