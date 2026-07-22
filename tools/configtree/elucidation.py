#!/usr/bin/env python3
"""tools/configtree/elucidation.py -- the typed elucidation-content vocabulary
(`DescriptionElement`/`ElucidationHeading`/`ElucidationValue`), split out of `fields.py` on
ADR-0007 grounds (no file over 400 lines, `gates/max_lines.py`'s own ratcheting-baseline gate:
this package has no baselined entry, so growth over 400 is refused outright).

Round 7 (ledger row 1119), following an independent Fable RCA consult
(design/CONSULT-FABLE-ELUCIDATION-RCA-2026-07-22.md) of round 6's own elucidation rendering.
Supersedes round 6's per-fact `aspiration`/`standards`/`mechanism`/`external` four-slot
telegraphy, which the consult diagnosed as CRITICAL: fielding a standard's name into a dedicated
`standards` slot silently PROMOTED an aspiration ("aspires to this standard's decomposition")
into an unqualified conformance claim -- a truth-value change no mechanical check could catch,
because every token survived and only the qualifying edge between them was lost.

ZERO domain knowledge lives here -- same discipline as `fields.py` (ADR-0012 P2)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Union

_PLACEHOLDER_TOKEN_RE = re.compile(r"<[A-Za-z_][A-Za-z0-9_-]*>")

# The label this library's own convention reserves for a DEMOTED, genuinely operator-relevant
# citation (round 7, defect D2: most provenance is maintainer-relevant only and never belongs on
# the operator's own screen at all -- the rare exception the operator really could open and read
# renders LAST, under this ONE name, never "Mechanism"/"Citation"/anything implying the
# platform's own internal machinery).
PROVENANCE_LABEL = "Full basis"


def _check_elucidation_text(value: "str | None", *, owner: str) -> None:
    """The ONE construction-time check every elucidation-carrying string goes through, whatever
    shape it arrived in (a plain string, a `DescriptionElement`'s label/text, an
    `ElucidationHeading`'s text) -- round 7, ledger row 1119:
      - D2/companion-rule-C13 (unchanged from round 6): a bare ' | ' is a homemade multi-fact
        delimiter -- structure belongs in separate typed items, never a string a renderer has to
        re-split.
      - D3: a raw `<placeholder>` token (e.g. `<dest>`) is an unexpanded template variable --
        "if the renderer ships placeholders, the operator must now doubt every other line"
        (the consult's own words). Refused outright, naming the token -- the caller's own job is
        to interpolate a REAL value or fall back to an honest generic phrase before construction,
        never to let the raw variable reach this far."""
    if not value:
        return
    if " | " in value:
        raise ValueError(f"{owner}: a bare ' | ' separator in an elucidation string is a "
                          f"homemade multi-fact delimiter (companion rule C13, ledger row 1117) "
                          f"-- split it into separate typed items instead: {value!r}")
    placeholder = _PLACEHOLDER_TOKEN_RE.search(value)
    if placeholder:
        raise ValueError(f"{owner}: an unexpanded template placeholder {placeholder.group()!r} "
                          f"reached elucidation text (ledger row 1119, defect D3) -- interpolate "
                          f"a real value or fall back to an honest generic phrase before "
                          f"construction, never let a raw <placeholder> token reach the screen: "
                          f"{value!r}")


def _check_no_bare_pipe(value: "str | None", *, owner: str) -> None:
    """Back-compat name for `_check_elucidation_text` -- every existing call site in
    `tools.configtree.fields` already names itself by this function; round 7 extended what it
    checks (now ALSO refuses a raw `<placeholder>` token, D3) without renaming every call site."""
    _check_elucidation_text(value, owner=owner)


@dataclass(frozen=True)
class DescriptionElement:
    """ONE typed, LABELED elucidation line -- a short `label` (round 7, ledger row 1119: reserved
    for a genuinely short, closed set -- e.g. "Constitutes"/"Does not", or the ONE demoted
    `PROVENANCE_LABEL` citation line -- never a per-component telegraphy vocabulary like
    "Aspiration"/"Standards"/"Mechanism"/"External" repeated once per fact, which the Fable
    consult diagnosed as "serialization masquerading as layout" -- D9 -- and, far worse, as the
    mechanism of D1: fielding a compound claim into a dedicated `Standards:` slot silently
    PROMOTED an aspiration into an unqualified conformance claim). The UNLABELED case -- ordinary
    connective prose, D7/D8's own "what this costs/requires, written as a sentence, not
    slot:value telegraphy" -- is a bare `str` item in an `ElucidationValue` tuple, never a
    `DescriptionElement`; see that type's own note. Construction IS validation: a bare ' | ' (a
    homemade multi-fact delimiter) or a raw `<placeholder>` token (D3: an unexpanded template
    variable reaching the screen) inside a label or text raises immediately, naming the
    offending value."""
    label: str
    text: str

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("DescriptionElement.label must be non-empty")
        if not self.text.strip():
            raise ValueError("DescriptionElement.text must be non-empty")
        for name, val in (("label", self.label), ("text", self.text)):
            _check_elucidation_text(val, owner=f"DescriptionElement {self.label!r} {name}")


@dataclass(frozen=True)
class ElucidationHeading:
    """A REAL sub-heading inside a multi-group elucidation value (round 7, ledger row 1119,
    defect D9: "Existing-db path --"/"Dedicated-db path --" repeated as a line PREFIX on every
    row is a flat key-value dump faking a hierarchy the reader must reconstruct by diffing
    prefixes; a genuinely grouped record -- more than one sub-path/sub-section under one field --
    gets a real heading element instead, rendered in its own bold, unprefixed style, with the
    group's own content following it as ordinary elements). Never itself a claim -- just a named
    break between groups, capped at measure like everything else."""
    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("ElucidationHeading.text must be non-empty")
        _check_elucidation_text(self.text, owner="ElucidationHeading")


# The type every elucidation-carrying slot in this library accepts: a plain string (the simple,
# single-paragraph case) OR a tuple whose own items are EACH one of:
#   - a bare `str`  -- ordinary CONNECTIVE PROSE, unlabeled, its own line (round 7, D7/D8: the
#     lead content -- what choosing this costs/requires/changes for the operator -- reads as a
#     sentence, never a "Label: text" telegraphy line);
#   - a `DescriptionElement` -- a short, closed-vocabulary LABELED line (Constitutes/Does not, or
#     the one demoted `PROVENANCE_LABEL` citation -- never a per-component slot vocabulary);
#   - an `ElucidationHeading` -- a real sub-heading breaking a multi-group value into named parts.
# Every item is still capped at MEASURE, still refused if it smuggles a bare ' | ' or a raw
# `<placeholder>` token. `tools.configtree.widgets.elucidation_widgets` is the ONE renderer for
# this type, shared by every consumer (`panes.SectionPane`, `actions.ActionPane`,
# `widgets.MultiChoiceFieldWidget`) so no call site needs its own rendering path per item kind.
ElucidationItem = Union[str, DescriptionElement, ElucidationHeading]
ElucidationValue = Union[str, "tuple[ElucidationItem, ...]"]
