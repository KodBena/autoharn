#!/usr/bin/env python3
"""served_shapes.py -- parsers for `led`'s served output text shapes, shared by tools/
role_brief.py and tools/role_charter.py.

EXTRACTION, this fix round (re-lap review, in-scope finding on the branch tipped at cc12b46):
parse_current_line and parse_served_show lived BYTE-IDENTICAL in both files (ADR-0012 P1, "one
home per fact" -- a duplicate this exact size invites exactly what happened next: role_brief.py's
417b200 and role_charter.py's own cc12b46 each independently fixed parse_current_line's silent-
drop bug, but parse_served_show carried the identical class UNTOUCHED by either fix, because nothing
forced the second copy to be re-reviewed once the first was). Extracted here so the fix is
authored ONCE and both callers get it for free; also the sanctioned way to make ROOM for this
fix without golfing legibility, since both tools/role_brief.py and tools/role_charter.py sit
at the ADR-0007/gates/max_lines.py 400-line ceiling with zero headroom.

Neither parser raises anything of its OWN: each takes the CALLER's own exception class
(`error_cls` -- `BriefError` in role_brief.py, `CharterError` in role_charter.py) so each tool's
`main()` keeps catching exactly the type it always did; this module is a pure parsing library,
not a third error hierarchy every caller would also need to know about.

SHAPES PARSED -- both read from bootstrap/templates/led.tmpl in full before being written (see
role_brief.py's own header for the fuller served-transport inventory this repo relies on):
  - `led current <N>` / `led --recent <N>`: `cmd_recent`'s own `f"[{id}] {kind}: {statement}"`.
  - `led show <id>`: `cmd_show`'s own `f"{k:28s}: {v}"` per non-null column, iterating the
    served row dict in order. `{k:28s}` is a Python format-spec MINIMUM width, not a truncation:
    a column name >=28 characters long is NOT padded, it is printed in full and the literal
    `": "` simply follows it wherever it ends. This is not a hypothetical -- the current schema
    already has one such column (`principal_competence_activity`, 29 characters; see
    kernel/lineage/s41-principal-bindings-and-relations.sql). A naive parser that assumes the
    separator always sits at exactly `line[28:30]` would misparse this column's line as a SHAPE
    DRIFT and refuse a perfectly well-formed `led show` -- a FALSE refusal, the mirror-image
    hazard of the silent-drop bug this fix round exists to kill. parse_served_show instead
    searches for the first `": "` at or after position 28 (never before it, since a value may
    itself contain `": "` and the padding/short-key region before 28 never legitimately does),
    so both a short, padded key and a long, unpadded key resolve to the same real separator.

Fix round itself (the reason this module exists): both parsers used to `continue` silently past
a line that failed to match -- collapsing "the server never emitted this field" (a genuinely
null column, cmd_show's own contract) and "a line WAS emitted but this parser could not read it"
into the exact same observable state: the key simply absent from the returned dict. Every caller
that treats "absent" as "genuinely null" (role_brief.py's own _actor_id_from_show, most acutely)
then silently drops a row it should have counted. Now: a non-blank line that does not match its
expected shape raises `error_cls`, naming the offending line, its 1-based line number (for
`parse_served_show`), and the producing `led` command -- refused loudly, never silently
misparsed. A blank/whitespace-only line is tolerated in `parse_served_show` (cmd_show itself
never emits one, but tolerating it costs nothing and keeps this parser from being pickier than
the shape it documents).

Lazy imports banned; stdlib only; no subprocess/`led` calls of its own -- pure text parsing over
already-captured output, imported by both tools' top-of-file imports.
"""
from __future__ import annotations

import re

# bootstrap/templates/led.tmpl's own `cmd_recent` print shape: `[id] kind: statement`.
_CURRENT_LINE_RE = re.compile(r"^\[(\d+)\] (\S+): (.*)$")


def parse_current_line(error_cls, led_cmd_label: str, line: str) -> tuple[int, str, str]:
    """One line of `led current <N>`/`led --recent <N>` output: `[id] kind: statement`. No actor
    field exists on this line at all (`ledger_current`'s served reading carries no actor-name
    join -- see each caller's own header note on this point).

    Refuses loudly (raises `error_cls`) on a non-matching line rather than silently skipping it
    -- a corrupted or reshaped line could hide a real row (a standing change, a registration, an
    in-force decision) and render an emptier-but-exit-0 result instead of the truth."""
    m = _CURRENT_LINE_RE.match(line)
    if not m:
        raise error_cls(
            f"SHAPE DRIFT -- `{led_cmd_label}` line does not match the expected `[id] kind: "
            f"statement` shape; got {line!r}. Refusing rather than silently skipping a row "
            f"that could hide a real change.")
    return int(m.group(1)), m.group(2), m.group(3)


def parse_served_show(error_cls, led_cmd_label: str, text: str) -> dict[str, str]:
    """`led show <id>`'s served format: one `f"{k:28s}: {v}"` line per non-null field
    (bootstrap/templates/led.tmpl's own `cmd_show`) -- a key padded to a MINIMUM of 28 columns
    (never truncated if the key itself is already >=28 characters -- see this module's own
    header), then the literal `": "`, then the value verbatim. A value may itself contain
    `": "`, so this never splits on the first colon in the line; it splits on the first `": "`
    found at or after column 28, which is always the real separator whether the key was padded
    or not.

    A blank/whitespace-only line is tolerated (cmd_show never emits one, but nothing depends on
    refusing it). Any other line where no `": "` exists at or after column 28 is a SHAPE DRIFT
    -- refused loudly, naming the 1-based line number, the offending text, and the producing
    command, rather than silently dropping a field a caller may need (role_brief.py's own
    _actor_id_from_show relies on "key absent" meaning "the server emitted no such column",
    never "a line was there and this parser failed to read it")."""
    out: dict[str, str] = {}
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        sep = line.find(": ", 28)
        if sep == -1:
            raise error_cls(
                f"SHAPE DRIFT -- `{led_cmd_label}` show output line {lineno} does not match "
                f"the expected `key: value` shape (a key, padded to at least 28 columns, then "
                f"': '); got {line!r}. Refusing rather than silently dropping a field that "
                f"could hide a real value.")
        out[line[:sep].strip()] = line[sep + 2:]
    return out
