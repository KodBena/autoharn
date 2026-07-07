#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-07T17:28:25Z
#   last-change: 2026-07-07T18:06:01Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""law_census — the machine-readable law census with ratification-depth marking (engine INC 1;
ruling 110 §5 INC 1, D15/D16/D20).

WHAT THIS IS. One machine-readable register of every law-shaped entry the apparatus cites: the
FINDINGS F-series (F1–F53), the BRIEF G/F/I registers, every `acts.ruling` row, and the
load-bearing ADR clauses — each classified {LAW-MECHANICAL | OBSERVATION | JUDGMENT-RESIDUE}
with a namespaced key (D15) and a ratification depth. It closes refute-adversarial flaw 2 (the
register-diff gate presupposed a machine-readable law register that did not exist) BEFORE any
gate reads it: the INC 3 citation constructor consumes THIS register.

EPISTEMIC LABEL (D20): this is an ENCODING-COVERAGE census, never a detection-power claim —
"every entry classified" means the register covers what the record names, not that the engine
can detect what the entries describe.

THE DEPTH ORDERING (D16's binding note, declared here explicitly — the INC 3 refusal must be
mechanical, not a judgment call):

    RULING(id)  >  FIND  >  BRIEF-INV  >  ADR

  - GATE-FEEDING judgments (write-time deny / close-red gates at P4+) require at least one
    RULING-depth citation.
  - FLAG-ONLY judgments require any depth — FIND, BRIEF-INV, and ADR citations all SUFFICE for
    flag-only judgments (the BRIEF is authoritative on scope per the standing rule).
  Depth derives mechanically from the key prefix: RULING: -> RULING; FIND: -> FIND;
  BRIEF:/INV: -> BRIEF-INV; ADR: -> ADR.

RATIFICATION SLOT. Every classification is PROPOSED (vicar, engine INC 1) until the maintainer
ratifies the census as a scope ruling. `CENSUS_RATIFIED` holds the ratification reference
(acts.ruling id or forward citation) when it lands; None = pending.

APOCRYPHA (INC 1 posture): a rule found in an implementation citing NO law lands here as a loud
QUARANTINED-apocrypha row, never a refusal (the refusal ships INC 3, after this census makes it
satisfiable). Known apocrypha today: NONE — judgment_registry refuses citation-less specs at
construction, so the set is empty by that gate; the register keeps the classification so a
future apocryphal discovery has a place to land loudly.

COMPLETENESS (--check; the census is RED-checked against the streams it covers):
  (a) every acts.ruling row is covered: binding/advisory rows need an EXPLICIT classification
      (law is never default-classified); informational anchor-pattern rows classify OBSERVATION
      by the anchor rule; an informational row matching no rule is RED-uncovered;
  (b) the F-series covers FINDINGS.md's highest F-number (a new finding is RED until censused);
  (c) every law key cited by judgment_registry.SPECS resolves in this census;
  (d) the D16 depth rule holds over the registry (P4+ judgments carry a RULING-depth citation).

Exit: 0 complete · 1 RED · 2 substrate unreachable (QUARANTINE). Lazy imports banned. Read-only.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from judgment_registry import SPECS, superseded_ids  # noqa: E402
from law_census_entries import RULING_BINDING_CLASSIFICATIONS, STATIC_ENTRIES  # noqa: E402

CENSUS_RATIFIED: str | None = "RULING:120"  # maintainer census-ratification forward 2026-07-07, as amended (a)-(d)

CLASSIFICATIONS = ("LAW-MECHANICAL", "OBSERVATION", "JUDGMENT-RESIDUE", "APOCRYPHA-QUARANTINED")
DEPTH_ORDER = ("RULING", "FIND", "BRIEF-INV", "ADR")  # strongest -> weakest (D16, declared)

PGHOST = os.environ.get("HARNESS_PGHOST", os.environ.get("EPISTEMIC_PGHOST", "192.168.122.1"))
FINDINGS_MD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "FINDINGS.md")  # autoharn: repo-root FINDINGS.md

# Informational acts.ruling rows covered by RULE (not per-id entries): the pre-registration /
# packet-freeze anchor idiom. Everything else informational needs an explicit entry.
_ANCHOR_PATTERNS = (
    "ANCHOR", "anchor:", "anchor (", " anchor", "pre-registration", "packet freeze",
)

# Explicit classifications for non-binding rows that are NOT anchors (advisory / informational
# rulings with law force short of binding). Keyed by ruling id.
RULING_OTHER_CLASSIFICATIONS: dict[int, tuple[str, str]] = {
    8: ("OBSERVATION", "self-test record: file_resolution mechanism works (Increment 7 item 5)"),
    9: ("OBSERVATION", "e16 pre-test prompt banked verbatim (adversarial level-field proof input)"),
    24: ("OBSERVATION", "exit-code contradiction resolution recorded informationally (binding twin = 26)"),
}

KNOWN_APOCRYPHA: tuple[tuple[str, str], ...] = ()  # (implementation-ref, note) — empty today


def depth_of(key: str) -> str:
    if key.startswith("RULING:"):
        return "RULING"
    if key.startswith("FIND:"):
        return "FIND"
    if key.startswith(("BRIEF:", "INV:")):
        return "BRIEF-INV"
    if key.startswith("ADR:"):
        return "ADR"
    raise ValueError(f"unnamespaced law key {key!r} (D15)")


def static_keys() -> set[str]:
    return {k for k, _, _, _, _ in STATIC_ENTRIES}


def _rulings_live() -> list[tuple[int, str, str]]:
    """(id, binding_grade, verbatim-head) for every acts.ruling row — live, never cached."""
    cp = subprocess.run(
        ["psql", "-h", PGHOST, "-d", "harness", "-tA", "-F", "\t",
         "-c", "SELECT id, binding_grade, left(replace(verbatim, E'\\n', ' '), 120) "
               "FROM acts.ruling ORDER BY id;"],
        capture_output=True, text=True, timeout=60)
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip()[-200:])
    out = []
    for ln in cp.stdout.splitlines():
        if ln.strip():
            rid, grade, head = ln.split("\t", 2)
            out.append((int(rid), grade, head))
    return out


def check(verbose: bool = True) -> int:
    reds: list[str] = []
    # (a) rulings-stream coverage
    try:
        rulings = _rulings_live()
    except Exception as e:  # noqa: BLE001 — a census that cannot see the law stream is NO RESULT
        print(f"# law-census QUARANTINED — cannot read acts.ruling: {e}")
        return 2
    for rid, grade, head in rulings:
        if grade in ("binding", "advisory"):
            if rid not in RULING_BINDING_CLASSIFICATIONS and rid not in RULING_OTHER_CLASSIFICATIONS:
                reds.append(f"ruling {rid} ({grade}) has NO explicit census classification — law is "
                            f"never default-classified: {head[:80]}")
        else:  # informational: anchor rule or explicit entry
            if rid in RULING_BINDING_CLASSIFICATIONS or rid in RULING_OTHER_CLASSIFICATIONS:
                continue
            if not any(p.lower() in head.lower() for p in _ANCHOR_PATTERNS):
                reds.append(f"ruling {rid} (informational) matches no anchor pattern and has no "
                            f"explicit entry — uncovered: {head[:80]}")
    # (b) F-series coverage vs FINDINGS.md
    try:
        txt = open(FINDINGS_MD, encoding="utf-8").read()
        # headings appear as "### F41 ..." and as ranged "### F52–F53 ..." — take every F<n>
        # on a heading line so a ranged heading's tail member counts too
        max_f = max(int(m) for ln in txt.splitlines() if ln.startswith("#")
                    for m in re.findall(r"\bF(\d+)\b", ln))
    except Exception as e:  # noqa: BLE001
        print(f"# law-census QUARANTINED — cannot read FINDINGS.md: {e}")
        return 2
    censused_f = {int(k.split(":F")[1]) for k in static_keys() if k.startswith("FIND:F")}
    for n in range(1, max_f + 1):
        if n not in censused_f:
            reds.append(f"FINDINGS.md carries F{n} but the census does not (new findings are RED "
                        "until censused)")
    # (c) registry citations resolve
    covered_rulings = set(RULING_BINDING_CLASSIFICATIONS) | set(RULING_OTHER_CLASSIFICATIONS)
    skeys = static_keys()
    for s in SPECS:
        for c in s.law_citations:
            if c.startswith("RULING:"):
                if int(c.split(":")[1]) not in covered_rulings:
                    reds.append(f"{s.judgment_id} cites {c} — not an explicitly-censused ruling")
            elif c not in skeys and not any(k.startswith(c + "/") for k in skeys):
                # a whole-ADR citation (ADR:0013) resolves against its clause-keyed entries
                reds.append(f"{s.judgment_id} cites {c} — no census entry")
    # (d) D16 depth rule over the registry — keyed on BEHAVIOR, not only the stage label (census
    # ratification amendment (d)): any live spec owning a trigger: implementation (an armed deny
    # surface) needs a RULING-depth citation OR the declared substrate-MAC assumption (§2.3's
    # pre-engine grandfathering marker). Superseded rows are citable history, not live owners.
    _SUBSTRATE_MAC = "pre-engine substrate MAC"
    dead = superseded_ids()
    for s in SPECS:
        if s.judgment_id in dead:
            continue
        has_ruling_depth = any(depth_of(c) == "RULING" for c in s.law_citations)
        if s.promotion_stage in ("P4", "P5") and not has_ruling_depth:
            reds.append(f"{s.judgment_id} is {s.promotion_stage} (gate-feeding) with no "
                        "RULING-depth citation (D16)")
        if any(k.startswith("trigger:") for k in s.implementations):
            if not has_ruling_depth and not any(_SUBSTRATE_MAC in a for a in s.assumptions):
                reds.append(f"{s.judgment_id} owns an armed trigger: implementation with neither a "
                            "RULING-depth citation nor the declared substrate-MAC assumption "
                            "(D16 behavior rule, census ratification amendment (d))")
    n_by_cls: dict[str, int] = {}
    for _, cls, _, _, _ in STATIC_ENTRIES:
        n_by_cls[cls] = n_by_cls.get(cls, 0) + 1
    if verbose:
        print(f"# law-census — {len(STATIC_ENTRIES)} static entries "
              f"({', '.join(f'{c}={n}' for c, n in sorted(n_by_cls.items()))}), "
              f"{len(RULING_BINDING_CLASSIFICATIONS)} explicit ruling classifications, "
              f"{len(rulings)} live acts.ruling rows, FINDINGS max=F{max_f}, "
              f"apocrypha={len(KNOWN_APOCRYPHA)}")
        print(f"#   depth ordering (D16, binding): {' > '.join(DEPTH_ORDER)}; gate-feeding needs "
              "RULING; FIND/BRIEF-INV/ADR all suffice for flag-only")
        slot = CENSUS_RATIFIED or "PROPOSED (maintainer slot open — the census classification is a scope ruling)"
        print(f"#   ratification: {slot}")
        for r in reds:
            print(f"  RED  {r}")
    print(f"# law-census {'RED — ' + str(len(reds)) + ' uncovered/unresolved' if reds else 'COMPLETE'}")
    return 1 if reds else 0


def main(argv: list[str]) -> int:
    if "--check" in argv or not argv:
        return check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
