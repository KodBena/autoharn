#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-13T17:42:07Z
#   last-change: 2026-07-13T17:56:04Z
#   contributors: 3c50e030/main
# <<< PROVENANCE-STAMP <<<

"""typed_table — EXPERIMENT, NO MANDATE (work item typed-table-constructor-experiment; see
design/ORCH-TYPED-TABLE-EXPERIMENT.md for the write-up and its findings-shaped status). This
tool is a sketch, not a proposal to adopt; no doc in this repository is required to use it.

WHAT THIS IMPLEMENTS, precisely per the maintainer's 2026-07-13 clarification (ledger row
299, which supersedes the question/answer framing in the original work_opened row): a
markdown table is a STRUCTURED PRODUCT TYPE — the label column's header is a TYPE FORMER, and
every row label is a claimed INHABITANT of the type it declares. "Does the row answer the
header's question" was one worked example of this (the original KR-note incident happened to
be a question/answer table); it is never the mandatory schema. The author declares WHATEVER
type former they like (a plain-words string — "capability", "directory", "verification
outcome", anything) and the constructor's job is to force the rows-inhabit-the-declared-type
judgment to be written down, once per row, before the table can be built at all.

WHY "FORCED ARTICULATION" IS THE HONEST MECHANICAL CORE, NOT NLP. Whether a label actually
inhabits an author-chosen type is a SEMANTIC question — no static predicate over the label
string decides it (the same wall design/ORCH-COMPOUND-NOMINAL-DETECTION-2.md's angle
E/D measure and disclose: form-typing catches SHAPE, never MEANING). This constructor does not
pretend otherwise. Instead of judging, it makes judging IMPOSSIBLE TO SKIP: `Table.row()`
takes a mandatory `inhabits=` argument — the author's own distributed reading, spelled out in
prose ("a verification outcome", "'trust story' is NOT a capability, it names no procedure").
Writing that sentence at the row's authoring moment is the check. The incident this experiment
answers (ledger row 293) is precisely a case where nobody performed this articulation — not the
author, not two independent fresh-context Bs — until the maintainer did, by hand, on his sixth
catch. A tool that forces the sentence to exist moves that moment from "reviewer, three rounds
deep" to "author, mid-row, before the table can even render."

MECHANICAL SUB-CHECKS, and what each can and cannot conclude (same soundness-story discipline
as compound_nominal_scan2.py — ADR-0011's measure-first rule applies to a hand-built tool too):

  1. FORCED ARTICULATION (above). CAN conclude: an inhabitation sentence naming both the label
     and the type former was written. CANNOT conclude: that the sentence is TRUE. A false
     articulation ("'cost to stand up' is a capability") is not caught — the mechanism's honesty
     is that it externalizes the judgment so a reader (including the author, rereading) can
     catch a false one, not that the tool verifies truth. This is intake-grammar discipline
     (typed refusal at the write boundary, per ADR-0000) applied to the one part of a table's
     defect class that IS mechanical — a label existing, being non-empty, and being counted —
     not the part that is semantic.
  2. EMPTY-HEADER REFUSAL (angle F, compound_nominal_scan2.py — "the one sound zero-judgment
     lint" per design/ORCH-ABC-AUDIT-LOOP-RECIPE.md's Named Defect Catalogue, Entry 3). A label
     column with no header declares no type former, so nothing can be checked against it.
     Refused outright at Table.__init__, zero judgment required.
  3. COLUMN-COUNT COHERENCE. Every row must supply exactly len(columns)-1 cells (the label plus
     one cell per declared non-label column). Sound structural fact, zero judgment.
  4. FORM-PARALLELISM, a WARN-only sub-check, never a refusal (angle D,
     compound_nominal_scan2.py, imported — not reimplemented, per ADR-0012 P1: one definition,
     transcribed). CAN conclude: the label column's surface forms (VP/NOM/QUESTION/GERUND) are
     mixed, majority vs minority. CANNOT conclude: that a mixed-form column is wrong (a
     column can legitimately mix forms) or that a uniform-form column is right (five nominal
     labels can still mix capabilities with costs — angle E/D's own stated limit,
     ORCH-COMPOUND-NOMINAL-DETECTION-2.md). This sub-check is a cheap, free, zero-cost prompt to
     re-read, offered because the pre-repair KR §5 table happened to have exactly this shape
     (three verb-initial rows, two nominal) — not because form-mixing IS the defect.

PROVENANCE. `Table.render()` appends an HTML-comment line marking the table
constructor-generated, with its declared type former, so a reviewer (human or B) can tell a
constructed table from a hand-authored one at a glance — this is the two-home hazard's own
mitigation (design/ORCH-TYPED-TABLE-EXPERIMENT.md, "Ergonomics assessment" section): if a
constructed table's rendered markdown is ever pasted into a doc without the call site that
produced it, the comment is the only surviving evidence of which one is the SSOT.

WHAT THIS IS NOT: not a gate, not wired into any doc's build, not a mandate. Nothing in this
repository is required to use it; see design/ORCH-TYPED-TABLE-EXPERIMENT.md for the honest
ergonomics assessment and the source-of-truth question an adoption decision would have to
answer first.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Angle D (form-parallelism) is imported, not reimplemented — ADR-0012 P1: one definition,
# transcribed, never a second driftable copy. Safe at module-import time: scan2's own main()
# sits behind an `if __name__ == "__main__"` guard, so importing it here runs no side effect.
from compound_nominal_scan2 import classify_label


class TableConstructionError(ValueError):
    """Refused at construction time — not at review time. Every raise site below names
    exactly which of the three mechanical checks failed and why."""


@dataclass
class _Row:
    label: str
    cells: tuple
    inhabits: str


@dataclass
class Table:
    """A structured-product-typed markdown table. `type_former` is the author's own
    plain-words declaration of what the label column's header names as a type (e.g.
    "capability", "verification outcome", "directory") — never fixed by this tool to any
    particular vocabulary; the maintainer's clarification (ledger row 299) is exactly that
    the constructor enforces rows-inhabit-the-declared-type for WHATEVER type is declared."""

    type_former: str
    columns: list
    caption: str = ""
    rows: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def __post_init__(self):
        if not self.columns:
            raise TableConstructionError("no columns declared — a table needs at least a "
                                          "label column")
        h0 = self.columns[0]
        if not h0 or not h0.strip() or not h0.strip().strip("*_`"):
            # angle F, compound_nominal_scan2.py: empty-header lint, promoted from a report-only
            # finding to a hard refusal here, since construction time can afford to be stricter
            # than review time on the one check that needs zero judgment.
            raise TableConstructionError(
                "EMPTY HEADER: the label column declares no type former — there is no genus "
                "to check row labels against (angle F, compound_nominal_scan2.py; Named "
                "Defect Catalogue Entry 3, design/ORCH-ABC-AUDIT-LOOP-RECIPE.md)"
            )
        if not self.type_former or not self.type_former.strip():
            raise TableConstructionError(
                "no type former declared for the label column — state, in plain words, what "
                "kind of thing every row label must be (e.g. type_former='capability')"
            )
        self.type_former = self.type_former.strip()
        self.columns = [c.strip() for c in self.columns]

    def row(self, label: str, *cells: str, inhabits: str) -> "Table":
        """Add one row. `inhabits` is the mandatory, forced articulation of the distributed
        reading: the author's own sentence stating whether/how `label` inhabits
        `self.type_former`. Both the label and the type former must be named in it — a
        sentence naming neither is boilerplate, not an articulated judgment, and is refused."""
        label = (label or "").strip()
        if not label:
            raise TableConstructionError(
                f"empty row label — cannot be an inhabitant of {self.type_former!r}"
            )
        if not inhabits or not inhabits.strip():
            raise TableConstructionError(
                f"row {label!r}: no inhabits= articulation supplied — state the distributed "
                f"reading ('{label}' : {self.type_former}) before the row can be constructed"
            )
        inhabits = inhabits.strip()
        if (self.type_former.lower() not in inhabits.lower()
                and label.lower() not in inhabits.lower()):
            raise TableConstructionError(
                f"row {label!r}: inhabits={inhabits!r} names neither the label nor the "
                f"declared type former {self.type_former!r} — this reads as boilerplate, not "
                "an articulated judgment; write it in terms of both"
            )
        expected_cells = len(self.columns) - 1
        if len(cells) != expected_cells:
            raise TableConstructionError(
                f"row {label!r}: {len(cells)} cell(s) supplied, table declares "
                f"{expected_cells} non-label column(s) ({self.columns[1:]})"
            )
        self.rows.append(_Row(label, tuple(cells), inhabits))
        return self

    def check_form_parallelism(self) -> list:
        """Angle D, compound_nominal_scan2.py, imported verbatim. WARN-only — never raises —
        because a mixed-form column is a cheap, zero-semantics prompt to re-read, not a
        verdict (see this module's docstring, sub-check 4)."""
        self.warnings = []
        if len(self.rows) < 3:
            return self.warnings
        forms = [classify_label(r.label) for r in self.rows]
        judged = [f for f in forms if f not in ("EMPTY", "CODE")]
        if len(judged) < 2:
            return self.warnings
        counts: dict = {}
        for f in judged:
            counts[f] = counts.get(f, 0) + 1
        majority_form, majority_n = max(counts.items(), key=lambda kv: kv[1])
        minority = [(r.label, f) for r, f in zip(self.rows, forms)
                    if f not in ("EMPTY", "CODE") and f != majority_form]
        if minority and majority_n > len(minority):
            labels = [lb for lb, _ in minority]
            shapes = [f for _, f in minority]
            self.warnings.append(
                f"form-parallelism: label column mostly {majority_form} "
                f"({majority_n}/{len(judged)}); minority form(s) in {labels} ({shapes}) — "
                "angle D, compound_nominal_scan2.py; zero semantics, worth a re-read, "
                "never a refusal"
            )
        return self.warnings

    def render(self) -> str:
        """Render markdown, run the form-parallelism sub-check, and append the
        constructor-generated provenance comment (plus any warnings)."""
        self.check_form_parallelism()
        lines = []
        if self.caption:
            lines.append(self.caption.rstrip())
            lines.append("")
        lines.append("| " + " | ".join(self.columns) + " |")
        lines.append("| " + " | ".join(["---"] * len(self.columns)) + " |")
        for r in self.rows:
            lines.append("| " + " | ".join([r.label, *r.cells]) + " |")
        body = "\n".join(lines)
        prov = (
            f"<!-- constructor-generated: tools/experiments/typed_table.py; "
            f"declared type former = {self.type_former!r}; {len(self.rows)} row(s) "
            f"type-checked at construction (forced articulation + empty-header refusal + "
            f"column-count coherence); see design/ORCH-TYPED-TABLE-EXPERIMENT.md -->"
        )
        parts = [body, prov]
        if self.warnings:
            parts.append("\n".join(f"<!-- WARN: {w} -->" for w in self.warnings))
        return "\n".join(parts) + "\n"


# --------------------------------------------------------------------------------------------
# Demonstration builders — three REAL corpus tables regenerated through the constructor, for
# design/ORCH-TYPED-TABLE-EXPERIMENT.md. None of these functions is imported by, or wired into,
# any document's build; they exist to produce the frozen output files under
# tools/experiments/results/, read by hand and cited in the design note. The source docs
# themselves are untouched (see that note's header for why).
# --------------------------------------------------------------------------------------------

def demo_kr_2_2() -> str:
    """design/ORCH-KR-TITRATION-EXPLORATION.md §2.2 — the four typed-intake grammars table.
    Type former: "typed-intake grammar" (a `kind:` statement prefix at the `./led` write
    boundary). Transcribed from the doc's on-disk table, 2026-07-13."""
    t = Table(
        type_former="typed-intake grammar (a `kind:` statement prefix)",
        columns=["kind", "fields", "write-side witness", "read-side witness"],
        caption="Table: the four typed-intake grammars (design/ORCH-KR-TITRATION-EXPLORATION.md §2.2)",
    )
    t.row(
        "`resource:`",
        "NAME, CLASS, REACH, WHAT-IT-PROVES, GUIDANCE, TIER",
        "`bootstrap/templates/led.tmpl:864-956`",
        "`bootstrap/templates/pickup.tmpl:227,245`",
        inhabits="`resource:` is a typed-intake grammar — it names a closed field list and a "
                 "write-side validator, same as every other row in this column.",
    )
    t.row(
        "`estimate:`",
        "TASK-SLUG, TOOL-CALLS, SUBAGENT-SPAWNS, WALL-CLOCK, TOKEN-OOM, BASIS",
        "`led.tmpl:958-1059`",
        "`pickup.tmpl:327,330`",
        inhabits="`estimate:` is a typed-intake grammar — its TOKEN-OOM field is order-of-"
                 "magnitude estimate, not out-of-memory, and the row still inhabits the "
                 "declared type: a closed vocabulary at the write boundary.",
    )
    t.row(
        "`taxon:`",
        "TAXONOMY, TAXON, PATTERNS, GLOSS",
        "`led.tmpl:1061-1146`",
        "`pickup.tmpl:395`",
        inhabits="`taxon:` is a typed-intake grammar — same closed-field shape as the other "
                 "three rows in this column.",
    )
    t.row(
        "`interface:`",
        "TAXONOMY, ARTIFACT-PATTERN, GLOSS",
        "`led.tmpl:1147` onward",
        "`pickup.tmpl:395` (same renderer)",
        inhabits="`interface:` is a typed-intake grammar — it shares `taxon:`'s read-side "
                 "renderer but is its own write-side grammar, and both facts are visible in "
                 "this row without contradicting its column membership.",
    )
    return t.render()


def demo_kr_5() -> str:
    """design/ORCH-KR-TITRATION-EXPLORATION.md §5 — the Haiku-tier-consumer comparison table.
    Type former: "question a Haiku-tier consumer might ask, answered per candidate substrate"
    (this table's label column happens to be phrased as literal questions — a case where the
    "question/answer" reading the maintainer's clarification demoted from mandatory schema to
    worked example is still the RIGHT type former for THIS particular table)."""
    t = Table(
        type_former="question a Haiku-tier consumer might ask",
        columns=["question, answered per candidate", "(a) OWL/RDF store", "(b) EDB/ASP tier",
                 "(c) typed grammars"],
        caption="Table: Haiku-tier-consumer comparison across three substrate candidates "
                "(design/ORCH-KR-TITRATION-EXPLORATION.md §5)",
    )
    t.row(
        "how does a Haiku-tier consumer look up one fact?",
        "SPARQL SELECT (needs endpoint + syntax)",
        "invoke a pre-authored query",
        "read pickup section / `./led show`; trivial",
        inhabits="'how does a Haiku-tier consumer look up one fact?' is a question a "
                 "Haiku-tier consumer might ask, answered here per candidate.",
    )
    t.row(
        "how does it enumerate current facts?",
        "SPARQL over latest-triples (versioning is manual in RDF)",
        "derived view",
        "pickup renders unsuperseded rows; supersession native",
        inhabits="'how does it enumerate current facts?' is a question a Haiku-tier consumer "
                 "might ask.",
    )
    t.row(
        "how does it detect a contradiction?",
        "ABox inconsistency — but explosion, and only within modeled axioms",
        "absence/join judgments, differential-trusted",
        "write-boundary refusal (malformed), collision detection stays with readers/probes",
        inhabits="'how does it detect a contradiction?' is a question a Haiku-tier consumer "
                 "might ask.",
    )
    t.row(
        "why trust an answer it returns?",
        "reasoner-proof, but encoding untrusted (no differential exists)",
        "two-producer differential, the house bar",
        "grammar refusal witnessed live; byte-exact rows",
        inhabits="'why trust an answer it returns?' is a question a Haiku-tier consumer might "
                 "ask.",
    )
    t.row(
        "what does the option cost to stand up?",
        "new store + TBox + trust machinery",
        "spec ceremony + program pairs",
        "one cloned template block per kind",
        inhabits="'what does the option cost to stand up?' is a question a Haiku-tier "
                 "consumer might ask — NOTE this is exactly the phrase ('cost to stand up') "
                 "that was mis-typed as a capability in the pre-repair incident table; here "
                 "the declared type former is 'question', so this row inhabits it cleanly — "
                 "the same words are ill-typed under one type former and well-typed under "
                 "another, which is the maintainer's point: the type is declared, not fixed.",
    )
    return t.render()


def demo_audit_au_family() -> str:
    """design/ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md — the AU-family walk table (2 columns,
    16 NIST SP 800-53 AU-controls). Type former: "NIST SP 800-53 AU-family control (ID and
    catalog title)". Transcribed from the doc's on-disk table, 2026-07-13; abbreviated here to
    5 representative rows (the full 16-row table is mechanically identical in shape — this
    demonstration is not a repair of the source doc, which is untouched)."""
    t = Table(
        type_former="NIST SP 800-53 AU-family control (ID and catalog title)",
        columns=["AU control (ID and catalog title)", "Posture in autoharn"],
        caption="Table: the AU-family walk, 5 representative rows of 16 "
                "(design/ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md)",
    )
    t.row(
        "AU-1 Policy and Procedures",
        "ABSENT as a formal policy document; the ledger-and-witness doctrine in "
        "CLAUDE.md/ORCH-CAPABILITIES.md is the de-facto policy, unnamed as such.",
        inhabits="'AU-1 Policy and Procedures' is a NIST SP 800-53 AU-family control (ID and "
                 "catalog title) — a control identifier plus its catalog name, same shape as "
                 "every row in this column.",
    )
    t.row(
        "AU-3 Content of Audit Records",
        "IMPLEMENTED for what is logged: ledger rows carry actor, timestamp, kind, statement, "
        "refs, stamp fields (kernel schema); the read-observer journals tool, path, session.",
        inhabits="'AU-3 Content of Audit Records' is an AU-family control ID+title.",
    )
    t.row(
        "AU-9 Protection of Audit Information",
        "PARTIAL: strong against ordinary roles (append-only triggers + integrity gate; "
        "s26 SHA-256 row-hash chain; s27 truncation high-water witness) — a superuser/schema "
        "owner can still disable the triggers or drop the table.",
        inhabits="'AU-9 Protection of Audit Information' is an AU-family control ID+title.",
    )
    t.row(
        "AU-11 Audit Record Retention",
        "ABSENT-AND-NAMED: no backup/retention story for the Postgres instance. Git-tracked "
        "JSONL ledgers (attestations, journals) inherit git's retention; the database does "
        "not.",
        inhabits="'AU-11 Audit Record Retention' is an AU-family control ID+title.",
    )
    t.row(
        "AU-16 Cross-organizational Audit Logging",
        "ABSENT-AND-UNNAMED (single-organization tool; unrecorded judgment, same caveat as "
        "PM/PS).",
        inhabits="'AU-16 Cross-organizational Audit Logging' is an AU-family control ID+title "
                 "— a control identifier plus its catalog name, not a posture judgment (the "
                 "posture is the OTHER column) and not a capability, keeping this column "
                 "single-typed across all 5 rows shown.",
    )
    return t.render()


def cmd_demo(args) -> int:
    demos = {
        "kr-2-2": demo_kr_2_2,
        "kr-5": demo_kr_5,
        "audit-au": demo_audit_au_family,
    }
    which = args.which or list(demos)
    out_dir = Path(args.out) if args.out else None
    for name in which:
        try:
            rendered = demos[name]()
        except TableConstructionError as exc:
            print(f"=== {name}: REFUSED AT CONSTRUCTION ===\n{exc}\n", file=sys.stderr)
            return 1
        print(f"=== {name} ===")
        print(rendered)
        if out_dir:
            out_dir.mkdir(parents=True, exist_ok=True)
            # .out.txt, not .out.md: this is frozen tool output for citation, matching the
            # sibling compound_nominal_scan2.py results' own naming convention -- a `.md`
            # extension would put these in ADR-0017's tracked-markdown scope as if they were
            # authored prose, which they are not (they are regenerated markdown TABLES quoted
            # as evidence, the ADR-0017 Exceptions' "quoted defects"/telegraphic-register case).
            (out_dir / f"typed_table.{name}.out.txt").write_text(rendered)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--demo", nargs="*", dest="which", metavar="NAME",
                     help="run named demo builder(s) (default: all); choices: kr-2-2, kr-5, "
                          "audit-au")
    ap.add_argument("--out", help="directory to also write <name>.out.md files into")
    args = ap.parse_args(argv)
    return cmd_demo(args)


if __name__ == "__main__":
    sys.exit(main())
