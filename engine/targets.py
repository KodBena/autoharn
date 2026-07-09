#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T09:53:09Z
#   last-change: 2026-07-09T10:10:56Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

"""targets -- the ONE home mapping a ledger-deployment NAME to (db, schema, kern) (ADR-0012 P1;
design/USE-MODE-ENGINE-WIRING.md item 1). Every consumer of a deployment's names -- engine/ledger_edb.py,
instruments/ledger_target.py -- derives (db, schema, kern) from here; neither hand-authors a second
copy of the registry, and neither hardcodes a schema name as a literal.

The defect class this forecloses (ADR-0000 closure statement, USE-MODE-ENGINE-WIRING.md):
  - `resolve()` on an unknown target name used to fall through to `db="epistemic", schema=<name>` --
    `resolve("toycolors")` targeted the WRONG DATABASE with no error (the silent fallback ADR-0002
    forbids). Here an unknown name is refused LOUDLY, naming the known targets.
  - kernel-shape detection used to test the literal relation name `"kernel.principal"` everywhere.
    Toy's kernel schema is `toycolors_kernel` (a `-v kern` parameter by design), so that literal
    silently excluded toy's whole regards/review/obligation family. `kern` is now a per-target field
    a consumer derives its own `f"{target.kern}.principal"` check from -- never a literal.

Invariant: every consumer of a deployment's names derives them from this one home; a name unknown to
it is refused loudly, never silently mapped to another database.

Quantification universe: axes = {db name, ledger schema, kernel schema}; targets = the explicit
registry (nla, e15-e18, toy) + the `^s\\d+[a-z]*$` scratch pattern (the banked lineage s6-s14 AND
their probe/mirror kin -- s13probe, s14probe -- any future kernel-lineage session or derived mirror)
+ the `.*_scratch$` scratch pattern (the apparatus-authored throwaway schemas engine/*_scratch.py and
engine/tests/*.py hand-author in `epistemic` -- marriage_acts_scratch, marriage_support_scratch,
marriage_dto_scratch, marriage_diff_scratch, marriage_dto_exercise_scratch) + the
LEDGER_DB/LEDGER_SCHEMA/LEDGER_KERN env override (a one-off target, e.g. a scratch mirror). Named as
NOT covered here (filed, not silent): the apply/arm step emitting a machine-readable deployment
record (future arm work, BACKLOG.md); finding 51's `name='subject'` principal-actor assumption
(instruments/ledger_target.py's own remediation, this module does not import it); toy-side env
defaults in toy-project/led + .claude/settings.json (already one home per file, out of this diff);
a handful of ad hoc historical `epistemic` schemas (e15_acts_join, lab_join_a, mock_e15_synth,
perf_join_e15, `ref`, and kin) that exist on disk but are NOT resolved by name anywhere in the
current engine/instruments/tests surface (verified empirically against `pg_namespace` and every
`resolve`/`export`/`*_manifest`/`*_edb` call site in the tree) -- engine/acts_join.py's
`_read_ledger` is the one live, untested exception (BACKLOG.md).

Sibling axis found mid-execution (ADR-0000 2026-07-02 amendment: "the class as first named is
presumed too narrow" -- checked outward before shipping, not after, and re-checked twice more after
the first two "fixes" each proved partial in turn -- ADR-0014's own trigger, resolved by widening the
check rather than by a second opinion since the pattern stayed legible throughout). The spec's own
quantification universe enumerated the special registry + `^s\\d+$`, but did NOT enumerate: (1) the
apparatus-authored `*_scratch` fixture schemas engine/acts_edb.py, engine/ledger_diff_scratch.py, and
every engine/tests/test_ledger_*.py already pass straight to `resolve()`/`export()`; (2) the
`sNNprobe`/`sNNmirror`-style derived-fixture schemas (test_ledger_marriage.py's `s13probe` regression
guard). Loud-refusing either would have broken the banked test suite, not merely the toy-collision
case the spec targeted. Both widenings stay on the SAME closed-pattern footing as the original
`^s\\d+$` (a recognizable naming CONVENTION for a scratch/mirror lineage in `epistemic`, never an
unbounded "anything else"): the toy-collision case (`resolve("toycolors")`) matches none of the three
patterns and still refuses loudly, so the defect class this module forecloses is unweakened.

Denomination: names are opaque strings owned by this registry; no consumer re-types them, no schema
name is a literal in engine/instrument code.

Stdlib-only, top-of-file imports (the lazy-import gate, gates/no_lazy_imports.py, applies)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

_SCRATCH_RE = re.compile(r"^s\d+[a-z]*$")  # s10-s14 AND their probe/mirror kin (s13probe, s14probe)
# the apparatus-authored throwaway-schema convention (discovered mid-execution -- see module
# docstring's "sibling axis" note): a name ending `_scratch` is a hand-authored fixture schema in
# `epistemic`, the same closed-pattern footing as `^s\d+$`, never the unbounded "anything else"
# fallthrough this module forecloses.
_APPARATUS_SCRATCH_RE = re.compile(r".*_scratch$")


@dataclass(frozen=True)
class TargetInfo:
    """Where a ledger deployment lives: its database, its ledger schema, and its KERNEL schema (the
    schema a kernel-shape consumer's `f"{kern}.principal"` capability check resolves against)."""
    db: str
    schema: str
    kern: str


# The ONE registry mapping a target NAME to (db, schema, kern). Explicit entries only; any name not
# listed here and not matching the scratch pattern is refused (see `resolve`), never silently mapped
# to `epistemic` (the defect this module forecloses).
_REGISTRY: dict[str, TargetInfo] = {
    # the live, isolated subject ledger (e14+): own database, schema public, kernel schema literally
    # named "kernel" (though nla itself carries no kernel.principal -- the capability check on `kern`
    # resolves that per-target, never a separate hand-maintained flag).
    "nla": TargetInfo(db="nla", schema="public", kern="kernel"),
    # e15: the s15 subject kernel, opaque db `vsr` (consult 25 §2.3 / A.3).
    "e15": TargetInfo(db="vsr", schema="public", kern="kernel"),
    # e16: the s16 subject kernel (s15 byte-identical), opaque db `hvn` (label zc9).
    "e16": TargetInfo(db="hvn", schema="public", kern="kernel"),
    # e17: the s17 subject kernel (s15 + stamps + independence vocabulary), opaque db `wmb` (label kt3).
    "e17": TargetInfo(db="wmb", schema="public", kern="kernel"),
    # e18: the s18 subject kernel (s18 = s17 byte-identical, Addendum A), opaque db `qbx` (label jm7).
    "e18": TargetInfo(db="qbx", schema="public", kern="kernel"),
    # toy: the toy-project pilot ledger (design/USE-MODE-ENGINE-WIRING.md). Its own database, ledger
    # schema `toycolors`, kernel schema `toycolors_kernel` -- the exact case the literal "kernel.
    # principal" check silently missed before this module existed.
    "toy": TargetInfo(db="toy", schema="toycolors", kern="toycolors_kernel"),
}

_KNOWN_TARGETS_MSG = (
    "known targets: " + ", ".join(sorted(_REGISTRY)) +
    "; or a scratch name matching ^s\\d+[a-z]*$ (e.g. 's10', 's13probe') or ending `_scratch` "
    "(an apparatus-authored fixture schema, e.g. 'marriage_acts_scratch'); "
    "or set LEDGER_DB/LEDGER_SCHEMA/LEDGER_KERN for a one-off target")


def resolve(name: str) -> TargetInfo:
    """Resolve a target NAME to its (db, schema, kern). Env `LEDGER_DB`/`LEDGER_SCHEMA`/`LEDGER_KERN`
    fully override for a one-off target (e.g. a scratch mirror) -- same precedence as before this
    module existed. An unrecognized name is refused LOUDLY (ADR-0002): it is neither silently mapped
    into `epistemic` nor to any other database."""
    if os.environ.get("LEDGER_DB") or os.environ.get("LEDGER_SCHEMA") or os.environ.get("LEDGER_KERN"):
        return TargetInfo(
            db=os.environ.get("LEDGER_DB", "epistemic"),
            schema=os.environ.get("LEDGER_SCHEMA", name),
            kern=os.environ.get("LEDGER_KERN", "kernel"),
        )
    if name in _REGISTRY:
        return _REGISTRY[name]
    if _SCRATCH_RE.match(name):
        # the banked per-session lineages (s10-s13, and any future one): closed-evidence scratch
        # schemas in the historical apparatus database `epistemic`, kernel schema literally "kernel".
        return TargetInfo(db="epistemic", schema=name, kern="kernel")
    if _APPARATUS_SCRATCH_RE.match(name):
        # an apparatus-authored fixture schema (marriage_*_scratch and kin) -- same closed-pattern
        # footing as ^s\d+$, discovered mid-execution (module docstring's "sibling axis" note).
        return TargetInfo(db="epistemic", schema=name, kern="kernel")
    raise ValueError(f"unknown ledger target {name!r} -- {_KNOWN_TARGETS_MSG}")
