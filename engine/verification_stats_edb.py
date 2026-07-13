#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-13T20:19:57Z
#   last-change: 2026-07-13T20:19:57Z
#   contributors: 3c942a60/main
# <<< PROVENANCE-STAMP <<<

"""verification_stats_edb -- the EDB builder for work item `verification-stats-asp-harvester`
(maintainer directive 2026-07-13, relayed from a downstream `ent` transcript): their orchestrator
now logs review verdicts as `kind=verification` ledger rows under a `verdict=/role=/workflow=/
round=/task=` evidence convention (engine/verification_evidence.py owns the grammar), and deriving
approve/revise/reject stats by hand was "annoying from an ergonomics perspective." This module is
the house EDB idiom that makes it ergonomic -- clone of engine/review_gap_edb.py's own shape,
consumed by engine/lp/verification_stats.lp exactly as that module feeds engine/lp/review_gap_audit.lp.

WHAT THIS HARVESTER DOES: grounds every `kind='verification'` ledger row into either (a) five typed
facts (verification_row/1, verification_verdict/2, verification_role/2, verification_workflow/2,
verification_round/2, verification_task/2) when its `evidence` column parses under the convention,
or (b) a single `unparseable_verification/1` fact when it does not -- NEVER both, NEVER neither,
and NEVER a silently-dropped row (this work item's own explicit instruction: "an unparseable row is
REFUSED LOUDLY as a typed unparseable fact, never guessed at").

I/O SEPARATED FROM GRAMMAR, ON PURPOSE (ADR-0012 P3/P9 in spirit, applied to a Python module: the
computation is a pure function of already-fetched rows): `facts_from_rows()` below is the ENTIRE
grounding logic and touches no database; `export()` is the thin SQL-fetching shell that calls it.
This is what makes engine/tests/test_verification_stats.py able to exercise BOTH polarities
(parseable rows -> correct distributions; a malformed row -> unparseable fact) WITHOUT a live
database connection -- this repo's own ledger carries no `kind=verification` rows yet (this work
item's own instruction), and reading `ent`'s live db is explicitly not this module's to do, so the
synthesized-rows path through `facts_from_rows()` is the whole witness available here; live-ent
validation of the SQL-fetching half (`export()`'s own query) is UNEXERCISED, named plainly rather
than silently assumed proven by the pure-function tests.

CAPABILITY-GATED, HONESTLY (mirrors engine/review_gap_edb.py's own Capability/produced idiom;
I12/F49: a schema this harvester cannot run on DECLARES the absence and its reason, never silently
emits zero facts read as "nothing to harvest"). This harvester needs exactly ONE thing beyond the
core ledger structure every target already carries (`id`, `kind` -- ledger_edb.py's own ALWAYS
family): an `evidence` text column on the ledger relation. A target without it is EXCLUDED, named.

GENERIC OVER THE DEPLOYMENT SCHEMA (this work item's own mandate): resolution goes through
ledger_edb.resolve() (the ONE home targets.py already provides, ADR-0012 P1), so this module makes
no assumption about which target/schema it runs against beyond the one column it requires -- `ent`
consumes it as a served capability by pointing `export()` at whatever target name its own registry
resolves to, unchanged.

Read-only. Lazy imports banned (top-of-file only)."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from clingo_run import quote_term
from ledger_edb import Target, resolve
from verification_evidence import parse_evidence

HERE = Path(__file__).resolve().parent
VERIFICATION_STATS_LP = HERE / "lp" / "verification_stats.lp"

_REQUIRED_FAMILIES = ("evidence_column",)


@dataclass(frozen=True)
class Capability:
    """A fact family's status on this target -- mirrors engine/review_gap_edb.py's own
    Capability (family/produced/reason) in miniature: this domain gates on exactly one column."""
    family: str
    produced: bool
    reason: str


class CapabilityError(RuntimeError):
    """Raised when a caller requests a fact family this target's schema does not carry."""


@dataclass
class VerificationStatsEdbExport:
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
        head = [f"% ==== verification-stats EDB: target '{self.target_name}'",
                f"% ==== produced: {sorted(self.produced_families())}"]
        for c in self.exclusions():
            head.append(f"% ==== EXCLUDED {c.family}: {c.reason}")
        return "\n".join(head) + "\n" + "\n".join(self.facts) + "\n"


def facts_from_rows(rows: list[tuple[int, str]]) -> tuple[list[str], dict[str, int]]:
    """THE grounding logic, in full, as a pure function of already-fetched `(id, evidence)` pairs
    for every `kind='verification'` row on some target (id-ordering is the caller's job, matching
    ledger_edb.py's own "IDS ARE THE INTERCHANGE" rule -- pass rows already `ORDER BY id`).

    Returns `(facts, counts)`. Every row produces EXACTLY ONE OF: the five typed facts (a
    successful parse) or a single `unparseable_verification/1` fact (an unsuccessful one) --
    engine/verification_evidence.parse_evidence's own closed grammar is the sole arbiter, never a
    second, looser check re-authored here (P1: one home for "what counts as parseable")."""
    facts: list[str] = []
    n_row, n_parsed, n_unparseable = 0, 0, 0
    for rid, evidence in rows:
        rid_i = int(rid)
        n_row += 1
        parsed = parse_evidence(evidence)
        if parsed is None:
            facts.append(f"unparseable_verification({rid_i}).")
            n_unparseable += 1
            continue
        facts.append(f"verification_row({rid_i}).")
        facts.append(f"verification_verdict({rid_i},{parsed.verdict}).")
        facts.append(f"verification_role({rid_i},{quote_term(parsed.role)}).")
        facts.append(f"verification_workflow({rid_i},{quote_term(parsed.workflow)}).")
        facts.append(f"verification_round({rid_i},{parsed.round}).")
        facts.append(f"verification_task({rid_i},{quote_term(parsed.task)}).")
        n_parsed += 1
    counts = {"verification_row": n_row, "parsed": n_parsed, "unparseable": n_unparseable}
    return facts, counts


def export(target_name: str) -> VerificationStatsEdbExport:
    """Build the verification-stats EDB for `target_name` (a ledger_edb.resolve()-able name).
    Read-only throughout; never raises for an honest capability shortfall (the caller decides how
    to report an incapable target -- see engine/verification_stats_audit.py's own build_report())."""
    t: Target = resolve(target_name)
    exp = VerificationStatsEdbExport(target_name=target_name)

    has_evidence = t.has_col("evidence")
    exp.capabilities.append(Capability(
        "evidence_column", has_evidence,
        "evidence column present" if has_evidence
        else "no `evidence` column on this schema -- capability absent, not record-empty"))

    if not exp.full_capable():
        return exp  # the caller (build_report) reports the exclusion; no facts to emit yet.

    rel = t.rel()
    rows = [(int(rid), evidence) for rid, evidence in t.rows(
        f"SELECT id, coalesce(evidence,'') FROM {rel} WHERE kind = 'verification' ORDER BY id;")]
    facts, counts = facts_from_rows(rows)
    exp.facts.extend(facts)
    exp.counts.update(counts)
    return exp


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("usage: verification_stats_edb.py <target-name>", file=sys.stderr)
        return 2
    exp = export(args[0])
    print(exp.edb_text())
    print(f"% counts: {exp.counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
