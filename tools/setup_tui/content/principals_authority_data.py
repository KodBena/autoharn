#!/usr/bin/env python3
"""tools/setup_tui/principals_authority_data.py -- the DATA half of the "Principals & authority"
screen driver, split out of tools/setup_tui/principals_authority.py under law/adr/0012's
2026-07-22 Amendment (P10 -- "data is not code"), phase 1 of design/FABLE-SETUP-TUI-FIELD-
STRATEGY.md Track 2.2. This module is the declared data artifact P10 calls for: typed literals,
ZERO functions, ZERO logic.

Four content groups, moved verbatim (unchanged) from principals_authority.py:

  * `CLASS_CHOICES` / `RELATION_CHOICES` -- the hand-mirrored kernel CHECK vocabularies (each a
    `list[tuple[str, str]]` of (value, teaching-line) pairs). These are content in the P10 sense
    (a writing edit -- rewording a teaching line -- is indistinguishable from a logic edit to the
    drift-check functions that consume them) even though they are also load-bearing for
    `check_vocabulary_drift` in principals_authority.py; the drift-check FUNCTIONS stay logic-
    side, the vocabulary DATA they check moves here. Each constant keeps its original "Mirrors
    kernel/lineage/..." provenance comment immediately above it -- that comment is content
    metadata (which live kernel source this list must agree with), not commentary about the
    split, so it travels with the data.
  * `SCAFFOLD_BASE_PRINCIPALS` -- the static mirror of `bootstrap/new-project.sh`'s s40 birth
    sequence (a `list[tuple[str, str, str]]` of (name, class, teaching-line) triples), with its
    own PHASE-2-ADDITION provenance comment kept above it for the same reason.
  * The five `LESSON_*` propaedeutic teaching strings (spec §2: "the one-line lesson... live in
    the registries (one home), not inline in screen code") -- pure prose, no structure beyond a
    Python string literal.

principals_authority.py imports these five names directly (no reconstruction needed -- none of
this content wraps a dataclass, so there is no logic-side type to route through; a plain typed
literal import is the whole assembly). Every consumer's import path
(`principals_authority.CLASS_CHOICES`, `.RELATION_CHOICES`, `.SCAFFOLD_BASE_PRINCIPALS`,
`.LESSON_REGISTER`, `.LESSON_COMPETENCE`, `.LESSON_RELATION`, `.LESSON_CHARTER`,
`.LESSON_WORKFLOW_POINTER`) is UNCHANGED -- principals_authority.py re-exports each by importing
it at module level, so `pa.CLASS_CHOICES` (the drift fixture's own access pattern) still resolves.

Chosen form (P10's own "choose deliberately" instruction): a data-only Python module, not JSON/
TOML -- same reasoning as feature_facts_data.py's own docstring: this content is typed
(`list[tuple[str, str]]`, not free-form key/value text) and cited by exact kernel source paths a
JSON editor would let drift silently; a Python literal keeps that structure mypy-checkable and
fails loud (a malformed tuple is a SyntaxError, not a silent parse fallback) at zero import cost.
Zero imports, zero functions -- pure literal data, importable standalone, no dependency on
principals_authority.py (no import-order fragility, no dataclass-reconstruction wiring needed
here since none of this content is dataclass-shaped). principals_authority.py is this module's
only intended importer.

Content is UNCHANGED from principals_authority.py's prior literals -- this is a pure relocation
(program-text moved, not rewritten); see the commit message for how this was verified.

Lazy imports are banned (CLAUDE.md, 2026-07-02) -- moot here (zero imports), stated for the
convention's sake.
"""
from __future__ import annotations

# Mirrors kernel/lineage/s15-schema.sql:62's agent_class CHECK ("agent_class text NOT NULL CHECK
# (agent_class IN ('human','model','subagent','tool'))") -- s40/s41 never widen this vocabulary,
# they only add EVENTS about principals that already carry one of these four classes.
CLASS_CHOICES: list[tuple[str, str]] = [
    ("human", "human -- a person; the only class a key binding (led principal bind-key) or a "
              "managerial/financial-independence review claim (s41 D-6) may attach to"),
    ("model", "model -- a named model identity (e.g. a specific Claude model)"),
    ("subagent", "subagent -- a dispatched sub-invocation acting under a model principal"),
    ("tool", "tool -- a non-agentic script/process principal"),
]

# Mirrors kernel/lineage/s41-principal-bindings-and-relations.sql's principal_relation_check
# CHECK ("principal_relation IN ('acts-for','dispatched-by','same-natural-person','succeeds')") --
# the CLOSED vocabulary D-2 states is kernel-structural (unlike principal_role_name's ratified
# free text): the kernel's own refusals (self-edge, same-natural-person canonical ordering) key
# off these exact four values.
RELATION_CHOICES: list[tuple[str, str]] = [
    ("acts-for", "acts-for -- subject is REPRESENTABLE delegation for object (a recorded "
                 "declaration, not enforcement -- s41 D-2)"),
    ("dispatched-by", "dispatched-by -- subject was dispatched by object (the declaration; the "
                      "WITNESS of the fact remains the stamp pair, denominated separately)"),
    ("same-natural-person", "same-natural-person -- subject and object are the same human "
                            "(canonicalized to lower-id subject, kernel-CHECKed; symmetric)"),
    ("succeeds", "succeeds -- subject is the sanctioned successor of object (the v1 path back "
                "from a suspended/revoked principal -- no reinstatement verb exists)"),
]

# PHASE-2 ADDITION (design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md §2.7: "the Principals screen shows
# the scaffold's contractual base ... from the registry that the scaffold itself writes from, not
# from a born world's views"): under the pure-core flow, birth has not actually run yet by the
# time this screen makes its decisions in the NORMAL sequence, so `list_principals(dest)` (a live
# SELECT against a world that may not exist on disk yet) cannot honestly back the "here is what
# you start from" display any more. This is a STATIC mirror of `bootstrap/new-project.sh`'s own
# s40 birth sequence (source lines verified: the REVIEWER_STATUS/COMMISSIONER_STATUS teaching text
# and the s40 birth-sequence comment block naming "author (model)... reviewer (subagent)...
# commissioner (human)") -- every world this package births carries exactly these three,
# unconditionally, in `--new-world` mode. `screen_principals_authority` shows THIS table when
# `dest` does not exist yet (the normal sequence); it still does the LIVE read via
# `list_principals` when `dest` already exists (an out-of-sequence `--start-at` against an
# already-born world -- a genuine read of a real world, the declared exception unchanged).
SCAFFOLD_BASE_PRINCIPALS: list[tuple[str, str, str]] = [
    ("author", "model", "the model identity that authored this world's first commit -- "
                        "self-attributed genesis exception, s40 birth sequence step 1"),
    ("reviewer", "subagent", "registered automatically through the s40 FULL ceremony at birth "
                             "(bootstrap/new-project.sh); do not re-register"),
    ("commissioner", "human", "registered automatically through the s40 FULL ceremony at birth; "
                              "the maintainer's own FULL-mode signing act uses this principal"),
]

# ---------------------------------------------------------------------------------------------
# The propaedeutic lesson lines (spec §2: "the one-line lesson (what this row constitutes, in
# record terms)"), ONE home -- screens.py never carries its own copy. Each states what the row
# CONSTITUTES and what it does NOT (spec §1 item 2's own per-form requirement).
# ---------------------------------------------------------------------------------------------
LESSON_REGISTER = (
    "CONSTITUTES: a new identity anchor row plus its principal_registered event -- append-only, "
    "attributed, dated, with a stated purpose (kernel/lineage/s40-principal-identity-events.sql "
    "Element 3: a bare anchor cannot commit without this event, atomically). "
    "DOES NOT: grant the principal any capability, role, or standing to write under -- "
    "registration is EXISTENCE, not authority. A registered principal cannot write under its own "
    "name until a standing declaration binds a db role to it (led principal declare-standing), "
    "and this screen's charter/competence/relation acts are separate ceremonies again."
)
LESSON_COMPETENCE = (
    "CONSTITUTES: a recorded BELIEF that this principal is competent for a named activity, at a "
    "stated band, on a stated basis -- attributed, dated, retractable only by a superseding "
    "withdrawal (kernel/lineage/s41-principal-bindings-and-relations.sql D-5/G13). "
    "DOES NOT: constitute a permission bit or gate anything -- RECORDABLE, NOT YET GATING in v1 "
    "(no review path consults competence before accepting an act; enforcement is a named "
    "follow-on amendment, s41 D-5). Band/basis are free text in v1, a RATIFIED PLACEHOLDER "
    "(s41 §9(g)), not a settled judgment that no closed vocabulary is ever warranted."
)
LESSON_RELATION = (
    "CONSTITUTES: a typed, attributed, dated declaration of a relationship between two "
    "registered principals, in the kernel's own closed vocabulary (acts-for | dispatched-by | "
    "same-natural-person | succeeds -- kernel/lineage/s41-principal-bindings-and-relations.sql "
    "D-2), retractable only by a superseding retraction restating the same triple. "
    "DOES NOT: enforce anything -- a relation is REPRESENTABLE delegation/supervision/succession, "
    "not an enforced permission; 'acts-for' in particular records a declared fact, it does not "
    "make the object's writes flow through the subject at the kernel level."
)
LESSON_CHARTER = (
    "CONSTITUTES: binding a role's governing charter TEXT (hash-verified against the file on "
    "disk at registration time) to an ALREADY-REGISTERED principal, via an ordinary kind=decision "
    "ledger row in a fixed, parseable statement shape "
    "(design/FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md; tools/role_charter.py). "
    "DOES NOT: itself register the principal -- charter and identity are two separate ceremonies "
    "(this is exactly the trap spec WP3 closes: chartering an unregistered role used to dead-end "
    "at a refusal; this screen offers the missing registration in-flow instead)."
)
LESSON_WORKFLOW_POINTER = (
    "Roles defined here become the principals your workflow units and briefs bind to -- see "
    "roles/README.md and design/FABLE-ROLE-CHARTERS-AND-BRIEFS-SPEC.md (charters and briefs) and "
    "tools/workflow_compile.py (the workflow-unit compiler) in the world you just born. No "
    "workflow authoring happens in this screen (spec §1 item 4: pointer, not machinery)."
)
