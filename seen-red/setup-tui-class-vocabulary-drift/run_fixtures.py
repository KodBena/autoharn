#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T03:47:07Z
#   last-change: 2026-07-19T03:47:07Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""seen-red/setup-tui-class-vocabulary-drift/run_fixtures.py -- both-polarity proof of
tools/setup_tui/principals_authority.py's own drift BACKSTOP (ledger row 1799 finding 3),
census-registered in gates/fixture_census.py.

principals_authority.py's own module docstring ("RULE 1, NEVER A SECOND IMPLEMENTATION") names
the hazard: `CLASS_CHOICES`/`RELATION_CHOICES` are hand-mirrors of the kernel's own CHECK
constraint vocabularies. A hand-mirror with no check is a claim that it stays in sync, not a
fact -- this fixture makes it a checked property, parsing the CHECK vocabularies straight out of
the actual kernel-lineage SQL source text (read-only, never imported or edited -- kernel/lineage
is frozen-record per CLAUDE.md):

  * `agent_class`'s CHECK is DEFINED in kernel/lineage/s15-schema.sql (checked directly:
    s40/s41 add EVENTS about principals that already carry one of the four classes, but neither
    file re-issues or widens the CHECK itself -- `read_kernel_class_vocabulary`'s own docstring
    states this provenance finding explicitly).
  * `principal_relation`'s CHECK genuinely IS defined in
    kernel/lineage/s41-principal-bindings-and-relations.sql.

  1. GREEN leg: the REAL CLASS_CHOICES/RELATION_CHOICES agree (as sets) with the REAL kernel CHECK
     vocabularies, parsed fresh from the real SQL source -- `check_vocabulary_drift()` with no
     arguments returns zero drift messages.
  2. RED leg A: a SYNTHETIC agent_class CHECK clause missing a real class ('subagent') --
     `check_vocabulary_drift` must report the disagreement.
  3. RED leg B: a SYNTHETIC principal_relation CHECK clause missing a real relation
     ('succeeds') -- `check_vocabulary_drift` must report the disagreement.

Both red legs feed `check_vocabulary_drift(class_source_text=..., relation_source_text=...)` a
SYNTHETIC string (per principals_authority.py's own docstring: injectable so a fixture can
observe the red leg without touching kernel/lineage on disk -- that tree stays frozen-record,
never edited by this fixture).

Zero residue: pure in-memory comparison + real file reads of kernel/lineage SQL source text, no
filesystem mutation, no db state. Real functions under test (no mocks). Lazy imports banned."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools.setup_tui import principals_authority as pa  # noqa: E402


def main() -> int:
    # --- case 1: GREEN leg -- the real CHOICES lists agree with the real kernel CHECKs ---
    real_drift = pa.check_vocabulary_drift()
    assert real_drift == [], (
        f"case 1 (GREEN leg): the real CLASS_CHOICES/RELATION_CHOICES must agree with the real "
        f"kernel CHECK vocabularies with ZERO drift messages -- got: {real_drift}"
    )
    print("case 1 ok: CLASS_CHOICES/RELATION_CHOICES and the live kernel CHECK vocabularies "
          "(s15-schema.sql, s41-principal-bindings-and-relations.sql) all agree (zero drift)")

    # --- case 2: RED leg A -- synthetic agent_class CHECK missing a real class ---
    synthetic_class_sql = (
        "    agent_class text NOT NULL CHECK "
        "(agent_class IN ('human','model','tool')),\n"
    )
    drift_a = pa.check_vocabulary_drift(class_source_text=synthetic_class_sql)
    assert any("CLASS_CHOICES" in m for m in drift_a), (
        f"case 2 (RED leg A): a synthetic agent_class CHECK missing 'subagent' must read red -- "
        f"got: {drift_a}"
    )
    print("case 2 ok: a synthetic agent_class CHECK missing a real class reads red")

    # --- case 3: RED leg B -- synthetic principal_relation CHECK missing a real relation ---
    synthetic_relation_sql = (
        "OR principal_relation IN ('acts-for','dispatched-by','same-natural-person'));\n"
    )
    drift_b = pa.check_vocabulary_drift(relation_source_text=synthetic_relation_sql)
    assert any("RELATION_CHOICES" in m for m in drift_b), (
        f"case 3 (RED leg B): a synthetic principal_relation CHECK missing 'succeeds' must read "
        f"red -- got: {drift_b}"
    )
    print("case 3 ok: a synthetic principal_relation CHECK missing a real relation reads red")

    # --- bonus case: both red legs stack ---
    drift_both = pa.check_vocabulary_drift(
        class_source_text=synthetic_class_sql, relation_source_text=synthetic_relation_sql)
    assert len(drift_both) == 2, (
        f"bonus case: both defects at once should report exactly 2 drift messages -- "
        f"got {len(drift_both)}: {drift_both}"
    )
    print("bonus case ok: both synthetic disagreements stack, reported separately")

    print("ALL CASES OK -- principals_authority.py CLASS/RELATION vocabulary drift backstop, "
          "both polarities proven")
    return 0


if __name__ == "__main__":
    sys.exit(main())
