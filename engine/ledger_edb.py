#!/usr/bin/env python3
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
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field

import targets
import atom_quote

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "filing"))
from pghost_resolve import resolve_pghost  # noqa: E402  (filing/pghost_resolve.py, the ONE home -- never a literal host default)

# design/FABLE-ENGINE-ENTITLEMENT-SCOPE-ASP-TWIN-SPEC.md §1b: surface/1's closed vocabulary lives
# in the SERVING layer's registry module (serving/boundary_service.py's VIEW_REGISTRY -- the
# closed route/view registry every one of that file's own comments names "registry" growth by
# growth), never in any database and never re-derived here. ONE home: THIS is the one import that
# reads it; engine/ledger_differential.py imports SURFACE_VOCABULARY from here (never re-imports
# serving itself) so the exporter and the SQL floor are handed the identical list from the same
# origin (the floor itself never imports serving -- it receives the list as a plain parameter,
# per the spec's own text: "the floor cannot read it and must be handed it through the same
# single home the exporter uses").
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "serving"))
from boundary_service import VIEW_REGISTRY  # noqa: E402

SURFACE_VOCABULARY: tuple[str, ...] = tuple(sorted(VIEW_REGISTRY))

PGHOST = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")  # row 1383: was EPISTEMIC_PGHOST-only, now matches every other caller's precedence
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
        # kernel/lineage/s56-reservation-residue.sql, design/FABLE-RESERVATION-RESIDUE-SPEC.md §7
        # amendment: widened to verdict IN ('attest','attest_with_reservations'), identically to
        # the DDL's own single home (kernel.discharging_attest, s32 widened by s56) and to this
        # module's SQL-floor twin (engine/ledger_floor.py::work_review_floor_atoms) -- a
        # reservation-carrying countersign discharges w_discharged/1 exactly as a clean attest
        # does. w_discharged/1 is, and remains, a boolean NAF fact (work_review.lp's own
        # `not w_discharged(R)`) -- no verdict distinction existed on it before this widening, so
        # none is invented here; the reservation's own tracked residue is the s56 SQL view
        # (`reservations_outstanding`), a display surface this engine layer does not model (s56's
        # own ENGINE -- NONE disclosure).
        n = 0
        for (rid,) in t.rows(
                f"SELECT c.id FROM {rel} c WHERE c.kind='work_closed' AND EXISTS ("
                f"  SELECT 1 FROM {rel} r JOIN {t.rel('review_detail')} rd ON rd.ledger_id = r.id"
                f"  WHERE r.kind='review' AND r.regards = c.id "
                f"    AND rd.verdict IN ('attest', 'attest_with_reservations') "
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


class ScopeExclusionParseError(RuntimeError):
    """Raised when a scope_exclusions jsonb payload violates the kernel CHECK's own admitted shape
    (design/FABLE-ENGINE-ENTITLEMENT-SCOPE-ASP-TWIN-SPEC.md §1b) -- the DefeatParseError-style
    typed refusal of the WHOLE export, never a skip-and-continue (ADR-0002); the differential
    reads QUARANTINED, the same "both producers fail identically" shape export_defeat's own P-5
    parse carries. On a real target this is UNREACHABLE: kernel/lineage/s70-scope-binding.sql's
    own scope_exclusions_shape CHECK already refuses any other shape at write time. It fires only
    when the witness plan stages a kernel-impossible payload on a scratch schema with that CHECK
    deliberately dropped first (spec §4's RED leg -- "the CHECK binds superusers too")."""


_SCOPE_EXCLUSION_FAMILIES = frozenset({"kind-class", "thread", "work-item-lineage", "rows"})


def _parse_scope_exclusions(pid: int, raw: str) -> list[tuple[str, str]]:
    """Decompose ONE principal's scope_exclusions jsonb array into (family, rendered-key-term)
    pairs -- Python-side, never spliced as ASP program text (ADR-0000's value/program amendment).
    One pair per entry for the three scalar families (kind-class, thread, work-item-lineage); one
    pair per (entry, member) for 'rows' (spec §1b: "one fact per (entry, member)" -- 'rows' admits
    an ARRAY of numeral ids). Family tokens are the KERNEL CHECK's own literal vocabulary
    (kernel/lineage/s70-scope-binding.sql's scope_exclusions_shape_ok), refused loudly on anything
    else -- never a prose rename, never a silently-dropped unknown entry."""
    try:
        entries = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as e:
        raise ScopeExclusionParseError(
            f"principal {pid}: scope_exclusions is not valid JSON: {e}") from e
    if not isinstance(entries, list):
        raise ScopeExclusionParseError(
            f"principal {pid}: scope_exclusions is not a JSON array: {raw!r}")
    out: list[tuple[str, str]] = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"family", "value"}:
            raise ScopeExclusionParseError(
                f"principal {pid}: scope_exclusions entry is not a closed {{family,value}} "
                f"object: {entry!r}")
        fam, val = entry["family"], entry["value"]
        if fam not in _SCOPE_EXCLUSION_FAMILIES:
            raise ScopeExclusionParseError(
                f"principal {pid}: scope_exclusions family {fam!r} outside the kernel CHECK's "
                f"closed vocabulary {sorted(_SCOPE_EXCLUSION_FAMILIES)}")
        if fam == "rows":
            if not isinstance(val, list) or not val:
                raise ScopeExclusionParseError(
                    f"principal {pid}: 'rows' family value must be a non-empty array: {val!r}")
            for member in val:
                if not isinstance(member, int) or isinstance(member, bool) or member < 0:
                    raise ScopeExclusionParseError(
                        f"principal {pid}: 'rows' member {member!r} is not a non-negative "
                        f"integer numeral id")
                out.append((fam, str(int(member))))  # a bare integer term, never quoted
        else:
            if not isinstance(val, str) or not val.strip():
                raise ScopeExclusionParseError(
                    f"principal {pid}: {fam!r} value must be a non-empty string: {val!r}")
            out.append((fam, atom_quote.atom_term(val)))
    return out


def export_entitlement(name: str, now_epoch: int | None = None) -> EdbExport:
    """Export the entitlement-layer EDB (principal/1, acts_for_edge/2, genesis/1,
    principal_active/1) for a target, read-only, capability-gated -- the independent SECOND
    derivation input for engine/lp/ledger_entitlement.lp's reaches_genesis/1, the SQL twin of
    kernel/lineage/s60-entitlement-enforcement.sql's principal_authority_chain_reaches_genesis().
    Capable only on an s41+s60 schema (principal_relation/principal_binding_active columns AND
    entitlement_act_class -- the latter is s60's own marker column, so a pre-s60 s41 world reads
    incapable here even though acts-for relations already exist, matching this family's OWN
    reason for being: entitlement enforcement, not mere delegation recording).

    s62 (row 1385) adds a seventh SQL-side act class (delegation_lifecycle, gating acts-for
    rows) but needs no exporter change -- every in-force edge lands in acts_for_edge/2
    regardless of which class gated its write; a refused self-assertion is never committed.

    `now_epoch` (design/FABLE-ENGINE-ENTITLEMENT-SCOPE-ASP-TWIN-SPEC.md §1a): the single-home
    wall-clock cursor the differential injects into BOTH producers for the s64 delegation_expiry
    comparison, replacing this function's own former export-time `now()` -- the exact class
    `ledger_floor.support_floor_atoms(name, now_epoch)` already fixed (an edge expiring between
    two independently-timed reads would otherwise manufacture a false DIVERGE_DEFECT). Defaults to
    the wall clock at call time (`int(time.time())`) so every PRE-EXISTING caller (the s60/s64
    seen-red fixtures, which call this with one positional arg) is unaffected."""
    if now_epoch is None:
        now_epoch = int(time.time())
    t = resolve(name)
    exp = EdbExport(target=t)
    rel = t.rel()

    kernel_principal = t.has_relation(f"{t.kern}.principal")
    has_relation_col = t.has_col("principal_relation")
    has_active = t.has_col("principal_binding_active")
    has_object = t.has_col("principal_object")
    has_marker = t.has_col("entitlement_act_class")
    capable = kernel_principal and has_relation_col and has_active and has_object and has_marker

    for fam in ("principal", "acts_for_edge", "genesis", "principal_active"):
        exp.capabilities.append(Capability(
            fam, produced=capable, capable=capable,
            reason="kernel.principal + principal_relation/principal_binding_active/"
                   "principal_object + entitlement_act_class (s60) all present -- emitted"
            if capable else
            "no kernel.principal relation, or no s41 principal_relation/principal_binding_active/"
            "principal_object columns, or no s60 entitlement_act_class column -- capability "
            "absent (this family is s60-specific, not merely s41-capable)"))

    if not capable:
        return exp

    n_p = 0
    for (pid,) in t.rows(f"SELECT id FROM {t.kern}.principal ORDER BY id;"):
        exp.facts.append(f"principal({int(pid)}).")
        n_p += 1
    exp.counts["principal"] = n_p

    n_g = 0
    for (gid,) in t.rows(
            f"SELECT principal_subject FROM {rel} WHERE kind = 'principal_registered' "
            f"ORDER BY id ASC LIMIT 1;"):
        if gid != "":
            exp.facts.append(f"genesis({int(gid)}).")
            n_g += 1
    exp.counts["genesis"] = n_g

    n_e = 0
    for subj, obj in t.rows(
            f"SELECT lc.principal_subject, lc.principal_object FROM {t.schema}.ledger_current lc "
            f"WHERE lc.kind = 'principal_relation_asserted' AND lc.principal_relation = 'acts-for' "
            f"AND lc.principal_binding_active ORDER BY lc.id;"):
        exp.facts.append(f"acts_for_edge({int(subj)},{int(obj)}).")
        n_e += 1
    exp.counts["acts_for_edge"] = n_e

    n_a = 0
    for (pid,) in t.rows(f"SELECT id FROM {t.kern}.principal ORDER BY id;"):
        standing = t.scalar(f"SELECT {t.kern}.principal_standing({int(pid)});")
        if standing == "active":
            exp.facts.append(f"principal_active({int(pid)}).")
            n_a += 1
    exp.counts["principal_active"] = n_a

    # s64 (kernel/lineage/s64-principal-stamps-delegation-conditions.sql, design/
    # FABLE-PRINCIPAL-STAMPS-SPEC.md §3 item 4): THREE new, PURELY ADDITIVE fact families for the
    # scope/expiry conjunction's own ASP twin (reaches_genesis_scoped/2, engine/lp/
    # ledger_entitlement.lp) -- the four families above (principal, acts_for_edge, genesis,
    # principal_active) are UNCHANGED, byte-identical emission rules, so ./judge's existing AGREE
    # leg on reaches_genesis/1 (the s60/s62 differential) is untouched by this addition. Capable
    # only when the s64 columns exist (delegation_expiry/delegation_scope_classes) -- a pre-s64
    # schema simply never emits these three families (declared, not silently absent: the
    # capability loop below covers them the same way the four s60 families are covered above).
    has_s64 = t.has_col("delegation_expiry") and t.has_col("delegation_scope_classes")
    for fam in ("act_class", "edge_scope_class", "edge_unscoped", "delegation_edge"):
        exp.capabilities.append(Capability(
            fam, produced=has_s64, capable=has_s64,
            reason="delegation_expiry + delegation_scope_classes (s64) present -- emitted"
            if has_s64 else
            "no s64 delegation_expiry/delegation_scope_classes columns -- capability absent "
            "(this family is s64-specific, not merely s60/s62-capable)"))
    if has_s64:
        # The act-class DOMAIN: the kernel-computed vocabulary entitlement_act_class_of/
        # entitlement_act_class_of_target emit (eight tokens as of s64) -- a fixed, named literal
        # list (never corpus-discovered), matching this project's own STANDARDS-REGISTRY posture
        # ("the authoritative set is a maintainer-approved registry... a standard no document
        # operationalizes is exactly the one every corpus-rooted audit will miss").
        act_classes = (
            "principal_registered", "principal_role_bound", "standing_lifecycle",
            "milestone_closure", "gate_edge_supersession", "entitlement_class_configured",
            "delegation_lifecycle", "independent_verification_delegation")
        for c in act_classes:
            exp.facts.append(f'act_class("{c}").')
        exp.counts["act_class"] = len(act_classes)

        n_sc = 0
        n_un = 0
        n_de = 0
        for subj, obj, scope_raw in t.rows(
                f"SELECT lc.principal_subject, lc.principal_object, lc.delegation_scope_classes "
                f"FROM {t.schema}.ledger_current lc "
                f"WHERE lc.kind = 'principal_relation_asserted' "
                f"AND lc.principal_relation IN ('acts-for', 'dispatched-by') "
                f"AND lc.principal_binding_active "
                f"AND (lc.delegation_expiry IS NULL OR lc.delegation_expiry > to_timestamp({int(now_epoch)})) "
                f"ORDER BY lc.id;"):
            # delegation_edge(X,Y): the s64 scoped closure's OWN edge relation -- a superset of
            # acts_for_edge/2 (which stays 'acts-for'-only, byte-identical, so the s60/s62
            # reaches_genesis/1 differential is untouched) that ALSO includes 'dispatched-by'
            # (the hazard-in-reach fix, kernel/lineage/s64-...sql's own header) and excludes any
            # expired edge (the SQL query's own WHERE clause above), matching the SQL 2-arg
            # principal_authority_chain_reaches_genesis(pid, act_class)'s own hop test exactly.
            exp.facts.append(f"delegation_edge({int(subj)},{int(obj)}).")
            n_de += 1
            if scope_raw:
                # Postgres text[] literal, e.g. "{work_closed,milestone_closure}" -- parsed here
                # (Python-side), never spliced as program text (ADR-0000's 2026-07-18 value/
                # program-distinction amendment): each element becomes its OWN edge_scope_class
                # fact, quoted as an ASP string constant, never concatenated into rule text.
                members = scope_raw.strip("{}").split(",")
                for m in members:
                    if m:
                        exp.facts.append(f'edge_scope_class({int(subj)},{int(obj)},"{m}").')
                        n_sc += 1
            else:
                exp.facts.append(f"edge_unscoped({int(subj)},{int(obj)}).")
                n_un += 1
        exp.counts["edge_scope_class"] = n_sc
        exp.counts["edge_unscoped"] = n_un
        exp.counts["delegation_edge"] = n_de

    # s70 (kernel/lineage/s70-scope-binding.sql, design/FABLE-ACCESS-CONTROL-AND-INFORMATION-
    # FLOW-SPEC.md §1b/§1c, design/FABLE-ENGINE-ENTITLEMENT-SCOPE-ASP-TWIN-SPEC.md §1b): FOUR new,
    # PURELY ADDITIVE fact families for ledger_entitlement.lp's scope predicates --
    # scope_binding_row/1, scope_bound/2, scope_exclusion/3, scope_disclosure/2. Every family above
    # (through the s64 block) is UNCHANGED, so ./judge's existing reaches_genesis/1 and
    # reaches_genesis_scoped/2 comparisons are untouched by this addition. Capable only when the
    # three s70 columns exist -- a pre-s70 (but s60/s64-capable) target emits none of the four,
    # declared EXCLUDED with reason (I12), never a silent empty; per the spec's "one semantics,
    # not a capability split" ruling, BOTH producers then degrade IDENTICALLY to everyone-open
    # (ledger_entitlement.lp's own #defined guards on scope_binding_row/1 etc., and
    # entitlement_floor_atoms' matching has_col gate), so the differential still ADJUDICATES
    # (expects AGREE) rather than skipping, exactly as the layer's ONE capability probe (the s60
    # marker column) already governs.
    #
    # surface/1 is DELIBERATELY NOT gated on has_s70 (a hazard caught live building this delta,
    # scratch-witnessed: gating it here made the pre-s70 degrade world emit ZERO may_read_surface
    # atoms on the ASP side while the SQL floor -- which reads `surfaces` as a plain injected
    # parameter, never from a column -- still emitted the full open-scope cross product, a
    # manufactured DIVERGE_DEFECT that had nothing to do with any real defect). The surface
    # vocabulary lives in the SERVING layer's registry, never in any database column, so its
    # availability does not depend on the target's kernel lineage at all -- it is capable (and
    # produced) on EVERY target.
    exp.capabilities.append(Capability(
        "surface", produced=True, capable=True,
        reason="the closed surface vocabulary (serving/boundary_service.py's VIEW_REGISTRY) is a "
               "Python-side constant, not a database fact -- always producible, independent of "
               "kernel lineage"))
    n_surf = 0
    for s in SURFACE_VOCABULARY:
        exp.facts.append(f"surface({atom_quote.atom_term(s)}).")
        n_surf += 1
    exp.counts["surface"] = n_surf

    has_s70 = (t.has_col("scope_surfaces") and t.has_col("scope_exclusions")
               and t.has_col("scope_disclosure_mode"))
    for fam in ("scope_binding_row", "scope_bound", "scope_exclusion", "scope_disclosure"):
        exp.capabilities.append(Capability(
            fam, produced=has_s70, capable=has_s70,
            reason="scope_surfaces + scope_exclusions + scope_disclosure_mode (s70) present -- "
                   "emitted"
            if has_s70 else
            "no s70 scope_surfaces/scope_exclusions/scope_disclosure_mode columns -- capability "
            "absent (this family is s70-specific, not merely s60/s62/s64-capable)"))
    if has_s70:
        n_sbr = n_sb = n_sx = n_sd = 0
        for subj, surfaces_raw, exclusions_raw, mode in t.rows(
                f"SELECT lc.principal_subject, lc.scope_surfaces, lc.scope_exclusions, "
                f"lc.scope_disclosure_mode FROM {t.schema}.ledger_current lc "
                f"WHERE lc.kind = 'principal_scope_bound' AND lc.principal_binding_active "
                f"ORDER BY lc.id;"):
            pid = int(subj)
            # scope_binding_row(P): row EXISTENCE, not surface count -- what arms a scope
            # (fail-closed: emitted even when scope_surfaces is NULL/empty, spec §1c).
            exp.facts.append(f"scope_binding_row({pid}).")
            n_sbr += 1
            if surfaces_raw:  # text[] literal, e.g. "{view_a,view_b}" -- parsed Python-side,
                               # never spliced as program text (ADR-0000's value/program rule).
                for m in surfaces_raw.strip("{}").split(","):
                    if m:
                        exp.facts.append(f"scope_bound({pid},{atom_quote.atom_term(m)}).")
                        n_sb += 1
            if exclusions_raw:  # jsonb array of {family,value} objects (§1b's decomposition).
                for fam_name, key_term in _parse_scope_exclusions(pid, exclusions_raw):
                    exp.facts.append(
                        f"scope_exclusion({pid},{atom_quote.atom_term(fam_name)},{key_term}).")
                    n_sx += 1
            if mode:  # NULL disclosure mode emits NO fact on either side (spec §1b/§1c: absence
                      # of a declared tier is absence, mirroring the kernel's own no-implicit-
                      # default stance -- the floor mirrors the same rule).
                exp.facts.append(f"scope_disclosure({pid},{atom_quote.atom_term(mode)}).")
                n_sd += 1
        exp.counts["scope_binding_row"], exp.counts["scope_bound"] = n_sbr, n_sb
        exp.counts["scope_exclusion"], exp.counts["scope_disclosure"] = n_sx, n_sd

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
