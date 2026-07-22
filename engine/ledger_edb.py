#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-06T05:33:12Z
#   last-change: 2026-07-21T23:58:28Z
#   contributors: 37017f46/main, be693afb/main, a857c93d/main, 9a17b6b9/main, ab5d5bab/main, 1fa3ab69/main
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

TARGET RESOLUTION derives from the ONE home `engine/targets.py` (vestigial_documentation/design/ORCH-USE-MODE-ENGINE-WIRING.md
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

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "filing"))
from pghost_resolve import resolve_pghost  # noqa: E402  (filing/pghost_resolve.py, the ONE home -- never a literal host default)

PGHOST = resolve_pghost("EPISTEMIC_PGHOST")  # unchanged precedence -- this module never checked HARNESS_PGHOST
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


# ===========================================================================
# WORK-LAYER EDB (plan step 8(ii); vestigial_documentation/design/ORCH-CATEGORICAL-REFACTOR-CONSULT-2026-07-15.md F7 --
# "ledger_edb.py exports no work_* fact family" was one of the two named judge-wiring gaps this
# closes). Exports the s22/s28/s29 work-item fact families engine/lp/work_items.lp and
# engine/lp/work_review.lp consume, so engine/lp_registry.py's "work" LAYER can be grounded from a
# real target the same way the "tnow" layer already is -- previously only hand-assembled per
# scratch fixture (kernel/fixtures/s22_work_item_fixture.py's work_item_edb(),
# seen-red/s31-supersession-uniform-retraction/run_fixtures.py's build_edb()). This function is
# the SINGLE HOME those two ad-hoc extractions should have shared (ADR-0012 P1); it is not yet
# retrofitted into either fixture (a minimal-touch call, ADR-0004 -- both already pass their own
# witness protocol against their own extraction, and retiring a working fixture's own EDB builder
# is out of this delta's scope).
#
# CAPABILITY-GATED, same I12 posture as export() above: a target predating s22 (no `work_slug`
# column) emits NOTHING from this family, declared EXCLUDED with reason -- never a silent empty a
# caller misreads as "no work items exist." s28 (work_parent) and s29
# (work_review_disposition/review_detail) are each their OWN sub-capability, independently gated,
# so a s22-only target still gets the base work_* facts. s33 (work_discharge -- composite
# discharge, kernel/lineage/s33-composite-discharge.sql) is its own sub-capability the same way.
WORK_FAMILIES = ("work_base", "work_parent", "work_review_disposition", "work_discharge")


def export_work(name: str) -> EdbExport:
    """Export the work-layer EDB (work_opened/2, work_closed/3, work_witness_present/1,
    work_depends/3, work_claimed/2, work_parent_edge/3 -- work_items.lp's own family; plus
    w_open/2, w_parent_e/3, w_dep_e/3, w_closed/3, w_disposition/2, w_discharged/1 --
    work_review.lp's own s31 row-id-carrying family; plus w_composite/1 -- work_review.lp's own
    s33 composite-discharge family) for a target, read-only, capability-gated."""
    t = resolve(name)
    exp = EdbExport(target=t)
    rel = t.rel()

    has_work = t.has_col("work_slug")
    has_parent = t.has_col("work_parent")
    has_review = t.has_col("work_review_disposition") and t.has_relation(f"{t.schema}.review_detail")
    has_discharge = t.has_col("work_discharge")
    has_edge_type = t.has_col("edge_type")
    has_disposition = t.has_col("work_violation_class")

    exp.capabilities.append(Capability(
        "work_base", produced=has_work, capable=has_work,
        reason="work_slug column present (s22 work-item ledger) -- emitted" if has_work
        else "no `work_slug` column on this schema (pre-s22 lineage) -- capability absent"))
    exp.capabilities.append(Capability(
        "work_parent", produced=has_parent, capable=has_parent,
        reason="work_parent column present (s28) -- emitted" if has_parent
        else "no `work_parent` column on this schema (pre-s28 lineage) -- capability absent"))
    exp.capabilities.append(Capability(
        "work_review_disposition", produced=has_review, capable=has_review,
        reason="work_review_disposition column + review_detail relation present (s29) -- emitted"
        if has_review else
        "no `work_review_disposition` column or no `review_detail` relation (pre-s29 lineage) -- "
        "capability absent"))
    exp.capabilities.append(Capability(
        "work_discharge", produced=has_discharge, capable=has_discharge,
        reason="work_discharge column present (s33 composite discharge) -- emitted" if has_discharge
        else "no `work_discharge` column on this schema (pre-s33 lineage) -- capability absent"))
    exp.capabilities.append(Capability(
        "work_violation_disposition", produced=has_disposition, capable=has_disposition,
        reason="work_violation_class column present (s37 violation disposition) -- emitted"
        if has_disposition else
        "no `work_violation_class` column on this schema (pre-s37 lineage) -- capability absent"))

    if not has_work:
        return exp

    n = 0
    for slug, rid in t.rows(f"SELECT work_slug, id FROM {rel} WHERE kind='work_opened' ORDER BY id;"):
        exp.facts.append(f"work_opened({_atom(slug)},{int(rid)}).")
        exp.facts.append(f"w_open({_atom(slug)},{int(rid)}).")
        n += 1
    exp.counts["work_opened"] = n

    if has_parent:
        n = 0
        for child, parent, rid in t.rows(
                f"SELECT work_slug, work_parent, id FROM {rel} "
                f"WHERE kind='work_opened' AND work_parent IS NOT NULL ORDER BY id;"):
            exp.facts.append(f"work_parent_edge({_atom(child)},{_atom(parent)},{int(rid)}).")
            exp.facts.append(f"w_parent_e({_atom(child)},{_atom(parent)},{int(rid)}).")
            n += 1
        exp.counts["work_parent_edge"] = n

    n = 0
    for slug, rid in t.rows(f"SELECT work_slug, id FROM {rel} WHERE kind='work_claimed' ORDER BY id;"):
        exp.facts.append(f"work_claimed({_atom(slug)},{int(rid)}).")
        n += 1
    exp.counts["work_claimed"] = n

    n = 0
    disp_col = "COALESCE(work_review_disposition,'')" if has_review else "''"
    for slug, resolution, rid, closer, disp in t.rows(
            f"SELECT work_slug, work_resolution, id, COALESCE(actor::text,'0'), {disp_col} "
            f"FROM {rel} WHERE kind='work_closed' ORDER BY id;"):
        exp.facts.append(f"work_closed({_atom(slug)},{resolution},{int(rid)}).")
        exp.facts.append(f"w_closed({_atom(slug)},{int(rid)},{int(closer)}).")
        if disp:
            exp.facts.append(f"w_disposition({int(rid)},{disp}).")
        n += 1
    exp.counts["work_closed"] = n

    n = 0
    for (rid,) in t.rows(f"SELECT id FROM {rel} WHERE kind='work_closed' "
                         f"AND work_witness IS NOT NULL AND btrim(work_witness) <> '' ORDER BY id;"):
        exp.facts.append(f"work_witness_present({int(rid)}).")
        n += 1
    exp.counts["work_witness_present"] = n

    n = 0
    for dep, ant, rid in t.rows(f"SELECT work_slug, work_depends_on, id FROM {rel} "
                                f"WHERE kind='work_depends_on' ORDER BY id;"):
        exp.facts.append(f"work_depends({_atom(dep)},{_atom(ant)},{int(rid)}).")
        exp.facts.append(f"w_dep_e({_atom(dep)},{_atom(ant)},{int(rid)}).")
        n += 1
    exp.counts["work_depends"] = n

    if has_edge_type:
        n = 0
        for rid, etype in t.rows(f"SELECT id, edge_type FROM {rel} "
                                  f"WHERE kind='work_depends_on' AND edge_type IS NOT NULL ORDER BY id;"):
            exp.facts.append(f"work_dep_type({int(rid)},{_atom(etype)}).")
            n += 1
        exp.counts["work_dep_type"] = n

    if has_review:
        n = 0
        for (rid,) in t.rows(
                f"SELECT c.id FROM {rel} c WHERE c.kind='work_closed' AND EXISTS ("
                f"  SELECT 1 FROM {rel} r JOIN {t.rel('review_detail')} rd ON rd.ledger_id = r.id"
                f"  WHERE r.kind='review' AND r.regards = c.id AND rd.verdict='attest' "
                f"    AND r.actor <> c.actor"
                f"    AND NOT EXISTS (SELECT 1 FROM {rel} s2 WHERE s2.supersedes = r.id)) "
                f"ORDER BY c.id;"):
            exp.facts.append(f"w_discharged({int(rid)}).")
            n += 1
        exp.counts["w_discharged"] = n

    if has_discharge:
        n = 0
        for (slug,) in t.rows(f"SELECT work_slug FROM {rel} "
                              f"WHERE kind='work_opened' AND work_discharge='composite' ORDER BY id;"):
            exp.facts.append(f"w_composite({_atom(slug)}).")
            n += 1
        exp.counts["w_composite"] = n

    if has_disposition:
        # s37 (kernel/lineage/s37-violation-disposition.sql): work_items.lp's own disposition
        # family, mirroring the kernel's disposition-narrowing shape (target_id-keyed, resolution
        # + optional witness, "in force" resolved AT EXPORT TIME here rather than re-derived in
        # ASP -- w_vdisp/w_vdisp_resolution read raw history, exactly work_depends/work_claimed's
        # own posture; superseded/1 (composed from ledger_tnow.lp, per this program's own header)
        # narrows them to in-force at the CONSUMER end, matching work_orphaned_by_retraction's
        # own existing composition style). witness-in-force is the ONE fact this exporter resolves
        # itself (a boolean over an arbitrary-kind row, which no other EDB family already
        # generalizes) -- named here, not silently baked into a bigger "everything" export.
        n = 0
        for cls, target, rid in t.rows(
                f"SELECT work_violation_class, work_violation_target_id, id FROM {rel} "
                f"WHERE kind='work_violation_disposition' ORDER BY id;"):
            exp.facts.append(f"w_vdisp({_atom(cls)},{int(target)},{int(rid)}).")
            n += 1
        exp.counts["w_vdisp"] = n

        n = 0
        for rid, resolution in t.rows(
                f"SELECT id, work_resolution FROM {rel} "
                f"WHERE kind='work_violation_disposition' ORDER BY id;"):
            exp.facts.append(f"w_vdisp_resolution({int(rid)},{_atom(resolution)}).")
            n += 1
        exp.counts["w_vdisp_resolution"] = n

        n = 0
        for (rid,) in t.rows(
                f"SELECT id FROM {rel} WHERE kind='work_violation_disposition' "
                f"AND work_violation_witness IS NOT NULL ORDER BY id;"):
            exp.facts.append(f"w_vdisp_witness_present({int(rid)}).")
            n += 1
        exp.counts["w_vdisp_witness_present"] = n

        n = 0
        for (rid,) in t.rows(
                f"SELECT d.id FROM {rel} d WHERE d.kind='work_violation_disposition' "
                f"AND d.work_violation_witness IS NOT NULL AND EXISTS ("
                f"  SELECT 1 FROM {t.rel('ledger_current')} w WHERE w.id = d.work_violation_witness) "
                f"ORDER BY d.id;"):
            exp.facts.append(f"w_vdisp_witness_in_force({int(rid)}).")
            n += 1
        exp.counts["w_vdisp_witness_in_force"] = n

    return exp


# ===========================================================================
# THE DEFEAT-LAYER EDB (design/FABLE-DEFEAT-PIPELINE-SPEC.md §4, amended §4.2 A1 2026-07-19).
# Exports row_actor/2, attest_row/1, mismatch_attest/3, trust_grant/3, grant_row/1,
# agent_class/2, affirms/3, affirm_author/2 for engine/lp/ledger_defeat.lp (composed with
# ledger_support.lp's affirmed/2) and its SQL twin (engine/ledger_floor.py::defeat_floor_atoms).
# Capability-gated exactly like export()/export_work() above (I12): a pre-s41 target
# declares trust_grant/grant_row EXCLUDED with reason, never a silent empty (§4.3 -- the F49
# class, foreclosed the same way run_sql_work already forecloses pre-s22 targets).
#
# THE V1 STATEMENT PARSE (spec §3, pins P-1..P-7 -- the parse contract shared verbatim with the
# sentry verb's own builder; both parse identically by construction, not by convention alone).
# No statement text, model string, session id, or basis crosses into the EDB (P-7); only the
# grade atom (rendered via the existing _atom() helper) and integer ids do.
DEFEAT_FAMILIES = ("row_actor", "attest_row", "mismatch_attest", "trust_grant", "grant_row",
                   "agent_class", "affirms", "affirm_author")

_V1_HEADER = "model-attestation v1"
_V1_PREFIX = "model-attestation "
_V1_KEYS = ("row=", "model=", "grade=", "expected=", "verdict=", "session=", "basis=", "rebuttals=")
_GRADE_VOCAB = frozenset({"exact-command", "turn-bracketed", "session-scoped", "ambiguous"})
_VERDICT_VOCAB = frozenset({"match", "MISMATCH", "unevaluated"})  # exact case (P-5)


class DefeatParseError(RuntimeError):
    """Raised on a malformed v1 attestation statement (spec §3 P-5) -- a loud refusal of the
    WHOLE export, never a skip-and-continue (ADR-0002). The differential reads QUARANTINED."""


def _parse_v1_statement(rid: int, stmt: str) -> tuple[int, str, str] | None:
    """Parse ONE candidate row's statement per §3 P-1/P-2/P-4/P-5. Returns (attested_row_id,
    verdict, grade) for a well-formed v1 row, or None for a version-skipped (non-v1) row --
    counted by the caller, never silently dropped uncounted (P-4). Raises DefeatParseError on
    any P-5 malformedness of a v1 candidate. The grade rides alongside row/verdict (review
    finding F1, ledger row 1506; spec §3 P-7 requires the PARSED grade cross into
    mismatch_attest/3) -- the parser already validated it against _GRADE_VOCAB below, so the
    caller carries it forward as an atom rather than discarding validated data."""
    segs = [s.strip() for s in stmt.split("|")]  # P-1: split on `|`, trim ASCII whitespace
    if segs[0] != _V1_HEADER:
        return None  # non-v1 header: version-skipped (P-4), not malformed
    if len(segs) != 9:
        raise DefeatParseError(
            f"row {rid}: v1 statement has {len(segs)} segments (expected 9, P-2): {stmt!r}")
    for i, key in enumerate(_V1_KEYS):  # segments 2..9 (0-based segs[1..8])
        if not segs[i + 1].startswith(key):
            raise DefeatParseError(
                f"row {rid}: segment {i + 2} does not start with {key!r} (P-2): {segs[i + 1]!r}")
    values = {key[:-1]: segs[i + 1][len(key):] for i, key in enumerate(_V1_KEYS)}
    try:
        attested_row = int(values["row"])
    except ValueError:
        raise DefeatParseError(f"row {rid}: row= value {values['row']!r} is not an integer (P-5)")
    if values["grade"] not in _GRADE_VOCAB:
        raise DefeatParseError(
            f"row {rid}: grade= value {values['grade']!r} outside {_GRADE_VOCAB} (P-5)")
    if values["verdict"] not in _VERDICT_VOCAB:
        raise DefeatParseError(
            f"row {rid}: verdict= value {values['verdict']!r} outside {_VERDICT_VOCAB} "
            f"(P-5, exact case -- 'MISMATCH' uppercase is deliberate)")
    return attested_row, values["verdict"], values["grade"]


def export_defeat(name: str) -> EdbExport:
    """Export the defeat-layer EDB (row_actor/2, attest_row/1, mismatch_attest/3, trust_grant/3,
    grant_row/1, agent_class/2, affirms/3, affirm_author/2 -- the last two per §4.2's A1
    amendment) for a target, read-only, capability-gated (§4). Both attestation arms are
    harvested where present: v1 convention rows (any kind, statement-parsed under §3's pinned
    contract) and, where the world carries s44, typed `model_identity_attested` rows. A row is
    one arm's or the other's by its shape, never both (§3)."""
    t = resolve(name)
    exp = EdbExport(target=t)
    rel = t.rel()

    # row_actor's P (principal id) must be an INTEGER principal id (the s41-lineage shape,
    # `actor bigint NOT NULL REFERENCES kernel.principal(id)`) -- NOT merely "an actor column
    # exists". Some pre-kernel-lineage targets (the real e14 record, `nla`) carry `actor` as a
    # TEXT database ROLE NAME (e.g. 'nla_rw'), which int()-crashes rather than misrepresenting a
    # role as a principal id -- a witnessed hazard, not a hypothetical one (found live grounding
    # this layer against `nla`). Capability-gated on the column's data TYPE, not merely presence.
    has_actor = t.has_col("actor") and t.scalar(
        f"SELECT data_type FROM information_schema.columns WHERE table_schema='{t.schema}' "
        f"AND table_name='ledger' AND column_name='actor';") in ("bigint", "integer", "smallint")
    has_statement = t.has_col("statement")
    has_typed = t.has_col("attest_row_id")
    attest_capable = has_statement or has_typed  # either arm suffices (§3's "both arms may coexist")
    has_active = t.has_col("principal_binding_active")
    has_activity = t.has_col("principal_competence_activity")
    grant_capable = has_active and has_activity
    kernel_principal = t.has_relation(f"{t.kern}.principal")

    exp.capabilities.append(Capability(
        "row_actor", produced=has_actor, capable=has_actor,
        reason="actor column present and integer-typed (a principal id) -- emitted" if has_actor
        else "no `actor` column, or it is not integer-typed (e.g. a text database role name, "
             "as on pre-kernel-lineage targets) -- capability absent, not a principal id"))
    for fam in ("attest_row", "mismatch_attest"):
        exp.capabilities.append(Capability(
            fam, produced=attest_capable, capable=attest_capable,
            reason="statement column (v1 arm) or attest_row_id column (s44 typed arm) present -- "
                   "emitted" if attest_capable else
                   "no `statement` column and no `attest_row_id` column on this schema -- "
                   "neither attestation arm capable"))
    for fam in ("trust_grant", "grant_row"):
        exp.capabilities.append(Capability(
            fam, produced=grant_capable, capable=grant_capable,
            reason="principal_binding_active/principal_competence_activity columns present "
                   "(s41) -- emitted" if grant_capable else
                   "no principal_binding_active/principal_competence_activity columns on this "
                   "schema (pre-s41 lineage) -- capability absent, not record-empty"))
    exp.capabilities.append(Capability(
        "agent_class", produced=kernel_principal, capable=kernel_principal,
        reason="emitted for future countersign-conditioned consumers (reserved, "
               "design/FABLE-DEFEAT-PIPELINE-SPEC.md §13); no rule reads it this increment"
        if kernel_principal else f"no `{t.kern}.principal` relation on this schema -- capability absent"))

    if has_actor:
        n = 0
        for i, p in t.rows(f"SELECT id, actor FROM {rel} WHERE actor IS NOT NULL ORDER BY id;"):
            exp.facts.append(f"row_actor({int(i)},{int(p)}).")
            n += 1
        exp.counts["row_actor"] = n

    n_candidates = n_skipped = n_parsed = n_mismatch = 0
    if has_statement:
        for rid_s, stmt in t.rows(
                f"SELECT id, statement FROM {rel} WHERE btrim(statement) LIKE '{_V1_PREFIX}%' ORDER BY id;"):
            rid = int(rid_s)
            n_candidates += 1
            parsed = _parse_v1_statement(rid, stmt)  # raises DefeatParseError on P-5 malformedness
            if parsed is None:
                n_skipped += 1
                continue
            attested_row, verdict, grade = parsed
            n_parsed += 1
            exp.facts.append(f"attest_row({rid}).")
            if verdict == "MISMATCH":  # P-6: only exact-case MISMATCH yields mismatch_attest
                # F1 fix (ledger row 1506): the PARSED grade crosses as an atom via the existing
                # _atom() helper (P-7) -- never the literal `none` regardless of what was parsed.
                exp.facts.append(f"mismatch_attest({rid},{attested_row},{_atom(grade)}).")
                n_mismatch += 1
    if has_typed:
        n_t = 0
        for rid_s, target_s, verdict, grade in t.rows(
                f"SELECT id, attest_row_id, attest_verdict, COALESCE(attest_grade,'') "
                f"FROM {rel} WHERE kind='model_identity_attested' ORDER BY id;"):
            rid, target = int(rid_s), int(target_s)
            exp.facts.append(f"attest_row({rid}).")
            n_t += 1
            if verdict == "mismatch":  # s44's closed lowercase vocabulary (§3)
                exp.facts.append(f"mismatch_attest({rid},{target},{_atom(grade)}).")
                n_mismatch += 1
        exp.counts["attest_row(typed-arm)"] = n_t
    exp.counts["attest_row(v1-candidates)"] = n_candidates
    exp.counts["attest_row(v1-version-skipped)"] = n_skipped
    exp.counts["attest_row(v1-parsed)"] = n_parsed
    exp.counts["mismatch_attest"] = n_mismatch

    if grant_capable:
        n = 0
        for g, p, act in t.rows(
                f"SELECT id, principal_subject, principal_competence_activity FROM {rel} "
                f"WHERE kind='principal_competence_granted' AND principal_binding_active "
                f"ORDER BY id;"):
            exp.facts.append(f"trust_grant({int(g)},{int(p)},{_atom(act)}).")
            n += 1
        exp.counts["trust_grant"] = n
        n = 0
        for (g,) in t.rows(
                f"SELECT id FROM {rel} WHERE kind='principal_competence_granted' ORDER BY id;"):
            exp.facts.append(f"grant_row({int(g)}).")
            n += 1
        exp.counts["grant_row"] = n

    if kernel_principal:
        n = 0
        for pid, cls in t.rows(f"SELECT id, agent_class FROM {t.kern}.principal ORDER BY id;"):
            exp.facts.append(f"agent_class({int(pid)},{_atom(cls)}).")
            n += 1
        exp.counts["agent_class"] = n

    # SPEC RENEGOTIATION, SURFACED (ADR-0000 Rule 2(a); design/FABLE-DEFEAT-PIPELINE-SPEC.md §4.2's
    # family table does not name affirms/3 or affirm_author/2, yet §5.1's cascade discharge rule
    # (exposure_model_undischarged) grounds `not affirmed(F,D)`, and ledger_support.lp's own
    # affirmed/2 rule (`affirms(R,F,D), not superseded(R), not affirm_sod_violation(R)`) is
    # UNGROUNDABLE-MEANINGFULLY without affirms/affirm_author facts in the composed EDB -- the
    # SQL twin (defeat_floor_atoms) reads the support_affirm scratch table directly and has no
    # such gap, so leaving this unaddressed would be a STRUCTURAL asymmetry between producers,
    # never reaching AGREE on any world exercising discharge (witnessed live building this
    # delta: DIVERGE_DEFECT on exposure_model_undischarged, ASP-only). The smallest honest fix,
    # consistent with ledger_floor.py's own support_manifest capability posture (has_affirm =
    # support_affirm relation present): export_defeat also emits affirms/3 + affirm_author/2 from
    # that SAME scratch stand-in when present -- no new table, no new convention, the identical
    # source ledger_support_scratch.py's own support_edb() already reads. DEFERRED (not emitted)
    # where the scratch table is absent, exactly the DEFERRED posture support_manifest declares.
    #
    # AMENDMENT A1 BINDING TERMS (review finding F2, ledger row 1506): full family discipline, no
    # exemption for lateness -- a Capability manifest entry like every sibling family (gate: the
    # support_affirm relation present; DEFERRED-with-reason where absent, mirroring
    # ledger_floor.py's support_manifest posture exactly), PLUS the actor join carries the SAME
    # int-typed guard as row_actor (has_actor, computed above) rather than assuming l.actor is a
    # principal id -- a text-typed actor (e.g. `nla`'s database-role actor column) would
    # int()-crash exactly the row_actor hazard this module's own header already names.
    has_affirm = t.has_relation(f"{t.schema}.support_affirm")
    affirm_produced = has_affirm and has_actor
    if has_affirm and not has_actor:
        affirm_reason = ("support_affirm relation present but `actor` is not integer-typed on this "
                          "schema -- the affirm_author join would misrepresent a text database role "
                          "as a principal id (the same hazard row_actor guards against); emission "
                          "DEFERRED, mirroring ledger_floor.py's support_manifest posture")
    elif has_affirm:
        affirm_reason = ("support_affirm relation + integer-typed actor present -- emitted "
                          "(scratch stand-in per ledger_support.lp §3 pending ruling)")
    else:
        affirm_reason = ("no support_affirm relation on this schema -- capability absent, mirroring "
                          "ledger_floor.py's support_manifest DEFERRED posture, never a silent empty")
    for fam in ("affirms", "affirm_author"):
        exp.capabilities.append(Capability(fam, produced=affirm_produced, capable=has_affirm,
                                           reason=affirm_reason))
    if affirm_produced:
        n = 0
        for r, dep, ant, actor in t.rows(
                f"SELECT sa.r, sa.dependent, sa.antecedent, l.actor FROM {t.schema}.support_affirm sa "
                f"JOIN {rel} l ON l.id = sa.r ORDER BY sa.r;"):
            exp.facts.append(f"affirms({int(r)},{int(dep)},{int(ant)}).")
            exp.facts.append(f"affirm_author({int(r)},{int(actor)}).")
            n += 1
        exp.counts["affirms"] = n

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
