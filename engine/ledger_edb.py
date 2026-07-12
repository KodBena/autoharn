#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-06T05:33:12Z
#   last-change: 2026-07-09T09:59:53Z
#   contributors: 37017f46/main, be693afb/main
# <<< PROVENANCE-STAMP <<<

"""ledger_edb -- the single home for "what the ledger looks like to a logic engine"
(design ORCH-LEDGER-LOGIC-MARRIAGE.md §3; ADR-0012 P1). The fact-mining-side analog of
`contra_asp.edb_from_claims`, exporting a typed EDB from any ledger target for the
ASP `T_now` program (ledger_tnow.lp) and the SQL floor (ledger_floor.py).

CAPABILITY-DRIVEN, WITH LOUD DECLARED EXCLUSIONS (the F49 lesson; I12 at the
substrate). The real e14 record is `nla.public.ledger` -- 55 rows, actor a *text*
role, NO `regards`, NO `kernel.principal`. The design doc's §3 signature was keyed
to the kernel-lineage shape and would silently emit no `regards/2` on `nla`, leaving
a consumer unable to tell "no regards exist" from "this target cannot say" -- the
vacuous-pass shape F49 names. So this module, per target, DECLARES which fact
families it CAN produce and prints the not-produced families as DECLARED EXCLUSIONS,
each with its reason (a missing column, a text-actor model, an absent apparatus
relation). A capability a caller REQUESTS that the target lacks is refused LOUDLY
(ADR-0015 Rule 4), never a silent empty.

TARGET RESOLUTION derives from the ONE home `engine/targets.py` (design/ORCH-USE-MODE-ENGINE-WIRING.md
item 1; ADR-0012 P1) -- the same home `instruments/ledger_target.py` derives from, so the two are
never hand-synced duplicate copies. The db/schema agreement with the operator SSOT is still PINNED
BY A PARITY TEST (engine/tests/test_ledger_marriage.py :: test_target_parity_against_operator_ssot),
run by subprocess against a fresh interpreter that only has `instruments/` on sys.path -- a kernel/
operator change, or a drift in either consumer's own derivation, lands as a red parity test.

IDS ARE THE INTERCHANGE; TEXT STAYS HOME (design §3 rule 1): no statement/rationale
text crosses into the EDB (`amends_scope` crosses as its length only). Every ordering
downstream keys on id, never ts (design §3 rule 2); ts is emitted for display and I7
temporal bounds only. Read-only psql on every ledger (the SSOT posture).

Closure statement (ADR-0000 2026-07-02 amendment):
  - invariant: the EDB a logic engine reasons over is produced from exactly the fact
    families the target CAN carry, with every not-carried family named as a declared
    exclusion; a requested-but-absent capability refuses loudly, never emits silence.
  - quantification universe: axes = {scalar-vs-array enacts, amends/answers columns
    present-or-absent, regards/kernel-principal present-or-absent, null concern/status};
    targets = {nla (live record), s10 (scalar enacts, lean), s11/s12 (array, lean),
    s13 (kernel-shape skeleton)} and any future kernel-lineage session.
  - denomination: a family is "produced" iff the target's live columns support it,
    resolved from the target's own schema, never from a hardcoded kernel-shape assumption.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from dataclasses import dataclass, field

import targets

PGHOST = os.environ.get("EPISTEMIC_PGHOST", "192.168.122.1")
FS, RS = "\x1f", "\x1e"

# The fact families a logic engine may consume, and the capability each requires. This
# is the closed vocabulary of the EDB signature; a target produces a family iff it has
# the capability. (regards/review/obliged/acts_for/agent_class are the kernel-shape-only
# families the design doc listed -- carried here as declared exclusions on lean/nla
# targets rather than silently omitted.)
ALWAYS = ("entry", "supersedes", "enacts")
COLUMN_GATED = {"amends": "amends", "answers": "answers"}
# kernel-shape families: present only where this target's KERNEL schema (`kern`) carries a
# `principal` relation and the ledger has a `regards` attestation column. Declared-excluded
# (with reason) everywhere else.
KERNEL_SHAPE = ("regards", "review_verdict", "review_independence",
                "obliged", "acts_for", "agent_class")


@dataclass(frozen=True)
class Target:
    """Where a ledger lives (name -> {db, schema, kern}). Constructed from `targets.resolve()`
    (engine/targets.py, the ONE home -- ADR-0012 P1); the same home `instruments/ledger_target.py`
    derives from, so the two are never hand-synced duplicate copies. The db/schema agreement with
    the operator SSOT is pinned by a parity test (test_ledger_marriage.py ::
    test_target_parity_against_operator_ssot), never by a shared import."""
    name: str
    db: str
    schema: str
    kern: str  # this target's KERNEL schema name (e.g. "kernel", or toy's "toycolors_kernel")

    def rel(self, table: str = "ledger") -> str:
        return f"{self.schema}.{table}"

    def run(self, sql: str) -> subprocess.CompletedProcess:
        # Read-only by construction: the SQL passed here is always a SELECT (the module
        # never issues DML on a ledger). psql to the resolved db, RS/FS-delimited.
        return subprocess.run(
            ["psql", "-h", PGHOST, "-d", self.db, "-tA", "-F", FS, "-R", RS, "-c", sql],
            capture_output=True, text=True, check=True)

    def rows(self, sql: str) -> list[list[str]]:
        out = self.run(sql).stdout
        return [r.split(FS) for r in out.rstrip("\n").split(RS) if r.strip()]

    def scalar(self, sql: str) -> str:
        return self.run(sql).stdout.strip()

    def has_col(self, col: str, table: str = "ledger") -> bool:
        return self.scalar(
            f"SELECT 1 FROM information_schema.columns WHERE table_schema='{self.schema}' "
            f"AND table_name='{table}' AND column_name='{col}';") == "1"

    def has_relation(self, qualified: str) -> bool:
        return self.scalar(f"SELECT to_regclass('{qualified}') IS NOT NULL;") == "t"


def resolve(name: str) -> Target:
    """Resolve a target NAME to its Target, via the ONE home `targets.resolve()`
    (engine/targets.py). An unrecognized name is refused loudly there (ADR-0002) --
    never silently mapped to `epistemic` or any other database."""
    ti = targets.resolve(name)
    return Target(name, db=ti.db, schema=ti.schema, kern=ti.kern)


@dataclass(frozen=True)
class Capability:
    """A fact family's status on a target. `produced` means ACTUALLY EMITTED into the EDB --
    the `require()` gate keys on emission, never on mere capability. `capable` is the separate
    I12 axis: does the target's schema even carry this family (columns/kernel-shape present)? A
    family can be capable-but-not-emitted (a kernel-shape family with no T_now consumer this
    increment) -- and that is STILL not produced, so require() refuses it loudly. Collapsing
    `capable` into `produced` was the F49 vacuous-pass the out-of-frame audit caught: s13 has the
    `regards` column, so it was marked produced, yet the exporter emits no regards fact, so
    require('regards') waved through a silent empty on the most-capable target."""
    family: str
    produced: bool   # EMITTED into this EDB (what require() gates on)
    capable: bool    # the schema carries this family (columns/kernel-shape present) -- I12 axis
    reason: str      # why produced, why capable-but-deferred, or why incapable


@dataclass
class EdbExport:
    target: Target
    facts: list[str] = field(default_factory=list)
    capabilities: list[Capability] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    def produced_families(self) -> set[str]:
        return {c.family for c in self.capabilities if c.produced}

    def exclusions(self) -> list[Capability]:
        """Every family NOT emitted -- both capable-but-deferred and incapable. require()
        refuses on any of these; the header prints the two kinds distinctly (I12)."""
        return [c for c in self.capabilities if not c.produced]

    def edb_text(self) -> str:
        """The clingo EDB program text (facts only), with the capability manifest as a
        header comment so a solver file is self-documenting about what it does NOT carry.
        A capable-but-not-emitted family (a kernel-shape column with no consumer this
        increment) is declared DEFERRED, distinct from an INCAPABLE (absent) family --
        never silence, and never a `produced` claim the exporter does not honor."""
        head = [f"% ==== ledger EDB: target '{self.target.name}' -> {self.target.db}.{self.target.rel()}",
                f"% ==== emitted: {sorted(self.produced_families())}"]
        for c in self.exclusions():
            tag = "DEFERRED" if c.capable else "EXCLUDED"
            head.append(f"% ==== {tag} {c.family}: {c.reason}")
        return "\n".join(head) + "\n" + "\n".join(self.facts) + "\n"

    def require(self, family: str) -> None:
        """Refuse LOUDLY (ADR-0015 Rule 4) if a caller depends on a family this EDB did not
        EMIT -- never let a downstream read a silent empty as 'none exist'. Keys on EMISSION,
        not mere capability: a capable-but-deferred family (s13 has the `regards` column but
        this increment emits no regards fact) is refused too, so the guard cannot wave through
        the exact silent empty it exists to catch (the out-of-frame audit's finding 2)."""
        if family not in self.produced_families():
            cap = next((c for c in self.capabilities if c.family == family), None)
            reason = cap.reason if cap else "not a known fact family"
            kind = "capable but NOT EMITTED this increment" if (cap and cap.capable) else "capability absent"
            raise CapabilityError(
                f"target '{self.target.name}' did not emit {family}/n ({kind}): {reason}. "
                f"A silent empty here would be the F49 vacuous-pass; refusing loudly.")

    def edb_hash(self) -> str:
        return hashlib.sha256(self.edb_text().encode("utf-8")).hexdigest()


class CapabilityError(RuntimeError):
    """Raised when a caller requests a fact family the target cannot produce (ADR-0015 R4)."""


def _atom(v: str) -> str:
    """A clingo term for a small categorical value: a bare constant if it is a safe
    identifier (kind/concern -- the closed lowercase vocab), else a quoted string."""
    v = (v or "").strip()
    if v == "":
        return "none"
    if v.replace("_", "a").isalnum() and v[0].isalpha() and v.islower():
        return v
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def export(name: str) -> EdbExport:
    """Export the typed EDB + capability manifest for a target. Read-only."""
    t = resolve(name)
    exp = EdbExport(target=t)
    rel = t.rel()

    # ---- capability discovery (per-target, from the live schema) --------------------
    has_amends = t.has_col("amends")
    has_answers = t.has_col("answers")
    has_regards = t.has_col("regards")
    kernel_principal = t.has_relation(f"{t.kern}.principal")
    kernel_shape = has_regards and kernel_principal

    for fam in ALWAYS:
        exp.capabilities.append(Capability(fam, produced=True, capable=True,
                                           reason="core ledger structure (all targets)"))
    exp.capabilities.append(Capability(
        "amends", produced=has_amends, capable=has_amends,
        reason="amends column present -- emitted" if has_amends
        else "no `amends` column on this schema (pre-e13 lineage) -- capability absent, not record-empty"))
    exp.capabilities.append(Capability(
        "answers", produced=has_answers, capable=has_answers,
        reason="answers column present -- emitted" if has_answers
        else "no `answers` column on this schema (pre-e13 lineage) -- capability absent, not record-empty"))
    # KERNEL-SHAPE families: NEVER emitted this increment (the T_now program has no consumer
    # for them yet). So produced=False on EVERY target -- capable-but-deferred on a kernel-shape
    # target (s13), incapable elsewhere. `produced` never over-claims what the exporter emits;
    # require() refuses either way (the out-of-frame audit's finding 2, s13 vacuous-pass, closed).
    for fam in KERNEL_SHAPE:
        if kernel_shape:
            exp.capabilities.append(Capability(
                fam, produced=False, capable=True,
                reason="kernel-shape lineage (regards + kernel.principal present) carries this "
                       "family, but it is NOT emitted this increment (no T_now consumer yet) -- "
                       "emission DEFERRED; require() refuses, never a silent empty"))
        else:
            why = ("no `regards` column on this schema" if not has_regards
                   else f"no `{t.kern}.principal` relation on this schema")
            exp.capabilities.append(Capability(
                fam, produced=False, capable=False, reason=f"kernel-shape only -- {why}"))

    # ---- entry/6 (id, ts-epoch, kind, concern, status, confidence) ------------------
    # ts is emitted as epoch seconds for display + I7 bounds ONLY; no rule orders on it.
    has_concern = t.has_col("concern")
    has_status = t.has_col("status")
    has_conf = t.has_col("confidence")
    cols = ["id", "extract(epoch FROM ts)::bigint", "kind",
            "coalesce(concern,'')" if has_concern else "''",
            "coalesce(status,'')" if has_status else "''",
            "coalesce(confidence,'')" if has_conf else "''"]
    n_entry = 0
    for i, ts, kind, concern, status, conf in t.rows(f"SELECT {', '.join(cols)} FROM {rel} ORDER BY id;"):
        exp.facts.append(
            f"entry({int(i)},{int(ts)},{_atom(kind)},{_atom(concern)},{_atom(status)},{_atom(conf)}).")
        n_entry += 1
    exp.counts["entry"] = n_entry

    # ---- supersedes/2 ---------------------------------------------------------------
    n = 0
    for a, b in t.rows(f"SELECT id, supersedes FROM {rel} WHERE supersedes IS NOT NULL ORDER BY id;"):
        exp.facts.append(f"supersedes({int(a)},{int(b)}).")
        n += 1
    exp.counts["supersedes"] = n

    # ---- enacts/2 (scalar bigint OR bigint[] -- auto-detected) ----------------------
    is_array = t.scalar(
        f"SELECT data_type FROM information_schema.columns WHERE table_schema='{t.schema}' "
        f"AND table_name='ledger' AND column_name='enacts';") == "ARRAY"
    if is_array:
        edge_sql = (f"SELECT e.id, u.tid FROM {rel} e "
                    f"CROSS JOIN LATERAL unnest(e.enacts) AS u(tid) ORDER BY e.id, u.tid;")
    else:
        edge_sql = f"SELECT id, enacts FROM {rel} WHERE enacts IS NOT NULL ORDER BY id;"
    n = 0
    for e, d in t.rows(edge_sql):
        exp.facts.append(f"enacts({int(e)},{int(d)}).")
        n += 1
    exp.counts["enacts"] = n

    # ---- amends/2 + answers/2 (capability-gated) ------------------------------------
    if has_amends:
        n = 0
        for a, tgt in t.rows(f"SELECT id, amends FROM {rel} WHERE amends IS NOT NULL ORDER BY id;"):
            exp.facts.append(f"amends({int(a)},{int(tgt)}).")
            n += 1
        exp.counts["amends"] = n
    if has_answers:
        n = 0
        for a, q in t.rows(f"SELECT id, answers FROM {rel} WHERE answers IS NOT NULL ORDER BY id;"):
            exp.facts.append(f"answers({int(a)},{int(q)}).")
            n += 1
        exp.counts["answers"] = n

    return exp


def main(argv: list[str] | None = None) -> int:
    names = (argv if argv is not None else sys.argv[1:]) or ["nla"]
    for name in names:
        exp = export(name)
        print(exp.edb_text())
        print(f"% counts: {exp.counts}")
        print(f"% edb_sha256: {exp.edb_hash()}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
