#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-13T20:19:07Z
#   last-change: 2026-07-13T20:19:07Z
#   contributors: 3c942a60/main
# <<< PROVENANCE-STAMP <<<

"""verification_evidence -- the SHARED parser for the downstream `ent` orchestrator's `kind=
verification` evidence convention (work item `verification-stats-asp-harvester`; maintainer
directive 2026-07-13, relayed from a downstream `ent` transcript).

THE CONVENTION, VERBATIM (as relayed, not paraphrased): a `kind=verification` ledger row's
`evidence` column carries

    verdict=<approve|revise|reject>;role=<...>;workflow=<label>;round=<n>;task=<id>

five `;`-separated `k=v` fields. `event_declared_ts` (a separate column this module never reads)
carries the historical event time when backfilled; `ts` stays the honest insert time -- neither
matters to this purely relational harvester (no timestamp crosses into this EDB at all, mirroring
engine/review_gap_edb.py's own "NO TIME CORRELATION" posture, for the same reason: this domain
reasons over verdict/role/workflow/round/task, never over when a row landed).

THIS MODULE OWNS THE PARSE, ONLY THE PARSE (ADR-0012 P1/P3: one home, one concern) -- no SQL, no
clingo, no I/O -- so both engine/verification_stats_edb.py (the live-schema EDB builder) and any
test/fixture can call the SAME grammar rather than each re-authoring it (the exact B-cancer
review_gap_thresholds.py's own docstring already names for its sibling domain).

THE GRAMMAR IS INTENTIONALLY STRICT AND NEVER GUESSES (ADR-0000 Rule 2(a)'s closure statement,
stated here for THIS domain):
  - invariant: `parse_evidence` returns a `ParsedVerification` iff EVERY one of the five required
    keys (verdict, role, workflow, round, task) is present with a non-empty value, no key repeats,
    `verdict` is a member of the closed vocabulary {approve, revise, reject}, and `round` parses as
    a non-negative base-10 integer. Anything else -- a missing key, a repeated key (ambiguous: which
    of the two values is "the" value is not this module's to guess), a verdict outside the closed
    vocabulary (a typo, a future value not yet ratified here), a non-integer or negative round, a
    segment with no `=` at all, or an empty/`None` evidence string -- returns `None`. The caller
    (engine/verification_stats_edb.py) turns a `None` into a typed `unparseable_verification/1`
    fact, NEVER a silently-dropped row and NEVER a best-effort guess at the intended value.
  - quantification universe: axes = {missing key, repeated key, unknown verdict value, non-integer
    round, negative round, `=`-less segment, empty/absent evidence string}; this is the CLOSED set
    this module checks. An axis explicitly NOT covered: a key present with a non-empty value that
    is nonetheless semantically wrong for its field (e.g. `role=` populated with a workflow name by
    mistake) -- this module has no oracle for "is this role a real role" and does not pretend to;
    that is exactly the FOLLOW-UP this work item flags (an intake-validated verification-verdict
    grammar, estimate:-style construction-time enforcement, so the convention stops being
    stringly-typed at its SOURCE rather than merely checked at its READER). Filed, not buried.
  - denomination: every field this parser extracts is denominated in exactly the unit the
    convention itself names (`round` as the integer it already is; `verdict`/`role`/`workflow`/
    `task` as the strings the convention already carries) -- no unit conversion, no derived value.
  - unknown EXTRA keys (beyond the five) are tolerated, not flagged: the convention names five
    fields this harvester consumes; a row carrying additional `k=v` pairs this harvester does not
    yet use is forward-compatible, not malformed -- a deliberate, named design choice, not an
    oversight (an unrecognized-but-present KNOWN key would be a different failure mode this module
    does not need to guard against because the five required keys are checked by name, not by
    counting fields).

Read-only in the purest sense possible: no I/O of any kind. Lazy imports banned (there are none to
ban -- stdlib-only, nothing to import lazily)."""
from __future__ import annotations

from dataclasses import dataclass

# The CLOSED verdict vocabulary this convention carries (per the maintainer's relayed grammar).
# Membership, not shape, is the gate -- a lookalike value ("approved", "Approve") is NOT a member
# and is therefore unparseable, not coerced (ADR-0012 P2: a boundary translates-and-validates, it
# does not coerce a plausible-looking value into the nearest legal one).
VERDICT_VOCAB: frozenset[str] = frozenset({"approve", "revise", "reject"})

_REQUIRED_KEYS = ("verdict", "role", "workflow", "round", "task")


@dataclass(frozen=True)
class ParsedVerification:
    """The five fields of one successfully-parsed `kind=verification` row's evidence string.
    `round` is the only non-string field (an int); everything else is the convention's own text,
    verbatim, never re-cased or trimmed of anything but the whitespace directly touching its `=`."""
    verdict: str
    role: str
    workflow: str
    round: int
    task: str


def parse_evidence(evidence: "str | None") -> "ParsedVerification | None":
    """Parse one `evidence` column value under the `kind=verification` convention. Returns `None`
    -- NEVER a guess, NEVER a partial/best-effort result -- for anything outside the closed grammar
    this module's own docstring enumerates. The caller decides how an unparseable row is reported;
    this function only ever answers "parsed" (a `ParsedVerification`) or "did not parse" (`None`)."""
    if not evidence:
        return None  # None or "" -- a verification row with no evidence at all cannot be parsed.

    fields: dict[str, str] = {}
    for raw_segment in evidence.split(";"):
        segment = raw_segment.strip()
        if segment == "":
            continue  # tolerate a stray/trailing empty segment ("a=b;") -- not a content signal
        if "=" not in segment:
            return None  # a segment that is not itself a k=v pair -- unparseable, never guessed
        key, _, value = segment.partition("=")
        key, value = key.strip(), value.strip()
        if key in fields:
            return None  # a REPEATED key is ambiguous -- refuse rather than pick one silently
        fields[key] = value

    if not all(fields.get(k, "") != "" for k in _REQUIRED_KEYS):
        return None  # a required key missing, or present-but-empty

    verdict = fields["verdict"]
    if verdict not in VERDICT_VOCAB:
        return None

    try:
        round_n = int(fields["round"], 10)
    except ValueError:
        return None
    if round_n < 0:
        return None

    return ParsedVerification(
        verdict=verdict, role=fields["role"], workflow=fields["workflow"],
        round=round_n, task=fields["task"])
