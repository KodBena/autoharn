#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T02:09:27Z
#   last-change: 2026-07-21T22:59:01Z
#   contributors: ab5d5bab/main, 43f77bff/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/principals_authority.py -- the "Principals & authority" screen's own driver
module (design/FABLE-SETUP-TUI-PRINCIPALS-AUTHORITY-SPEC.md, commission ledger row 1727). ONE
home (ADR-0012 P1) for every `led`/`role_charter.py` act `screens.py`'s
`screen_principals_authority` orchestrates -- the same pghba.py/probes.py/signed_genesis.py split
screens.py already uses for its other screens, applied here: screens.py stays thin (ui prompts,
checklist rows), this module carries the driver logic and the propaedeutic lesson text (spec §2:
"Lesson lines live in the registries (one home), not inline in screen code"). Every act goes
through `runner.run_command` (rule 1's exact-argv discipline + the `--dry-run` choke point), same
as every other screens.py helper module.

SCREEN POSITION AND VERB CHOICE (spec §1, the signed-genesis builder's own finding, cited
verbatim in this build's commission): this screen sits BETWEEN Birth and Signed genesis -- the
boundary service is not configured yet at this point in the flow (`screen_boundary` runs later).
Every write in this module therefore drives `<dest>/legacy/led` (this world's own direct-psql
recovery shim, bootstrap/templates/legacy-led.tmpl) exactly as
`tools/setup_tui/signed_genesis.py` already does for the SAME reason -- see that module's own
docstring for the two-verbs-two-moments explanation. The rebased `<dest>/led` (the SERVED path)
is never used here.

RULE 1, NEVER A SECOND IMPLEMENTATION: this module never re-derives kernel semantics. Class
vocabulary (`CLASS_CHOICES`) and relation vocabulary (`RELATION_CHOICES`) below are MIRRORS,
each with a comment naming its exact kernel source -- the kernel's own CHECK constraint is still
the validator of last resort (spec §1 item 1: "if the verb accepts free text, the screen still
offers the kernel's list and lets the kernel refuse anything else, rendering its teaching"); a
drift between this mirror and the live kernel CHECK is not silently possible to miss because a
value THIS module fails to offer, or wrongly offers, still meets the kernel's own refusal at
write time, never a false accept.

CONTENT SPLIT (law/adr/0012's 2026-07-22 Amendment, P10 -- "data is not code", design/
FABLE-SETUP-TUI-FIELD-STRATEGY.md Track 2.2, phase 1): `CLASS_CHOICES`, `RELATION_CHOICES`,
`SCAFFOLD_BASE_PRINCIPALS`, and the five `LESSON_*` propaedeutic teaching strings -- 44% of this
file by volume, a writing edit (rewording a teaching line, adding a class) indistinguishable in
the diff from a logic edit to `check_vocabulary_drift`/the plan-act builders below -- now live in
tools/setup_tui/principals_authority_data.py (a data-only module: typed literals, zero functions,
zero logic), imported directly below. None of this content is dataclass-shaped, so there is no
reconstruction step -- a plain import IS the assembly. Every consumer's import path
(`principals_authority.CLASS_CHOICES`, `.RELATION_CHOICES`, `.SCAFFOLD_BASE_PRINCIPALS`, each
`.LESSON_*` name) is UNCHANGED.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import here is top of file.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from tools.setup_tui import probes
from tools.setup_tui.plan import CommandAct
from tools.setup_tui.principals_authority_data import (
    CLASS_CHOICES,
    LESSON_CHARTER,
    LESSON_COMPETENCE,
    LESSON_REGISTER,
    LESSON_RELATION,
    LESSON_WORKFLOW_POINTER,
    RELATION_CHOICES,
    SCAFFOLD_BASE_PRINCIPALS,
)
from tools.setup_tui.runner import parse_row_id

REPO_ROOT = Path(__file__).resolve().parents[2]
# The kernel-lineage source files CLASS_CHOICES/RELATION_CHOICES below hand-mirror (ledger row
# 1799 finding 3): `agent_class`'s CHECK is DEFINED in s15-schema.sql (the schema-authoring
# lineage file the docstring below already cites) -- s40/s41 add EVENTS about principals that
# already carry one of these four classes, but never re-issue/widen the CHECK itself, so s15 is
# the true authoritative source, not s40/s41 (checked directly: no `agent_class IN (...)` CHECK
# appears anywhere in s40 or s41). `principal_relation`'s CHECK genuinely IS defined in s41.
KERNEL_CLASS_CHECK_PATH = REPO_ROOT / "kernel" / "lineage" / "s15-schema.sql"
KERNEL_RELATION_CHECK_PATH = (
    REPO_ROOT / "kernel" / "lineage" / "s41-principal-bindings-and-relations.sql"
)

# CLASS_CHOICES, RELATION_CHOICES, and SCAFFOLD_BASE_PRINCIPALS -- imported above from
# tools/setup_tui/principals_authority_data.py (P10 data split, see module docstring's "CONTENT
# SPLIT" note); their provenance comments (which kernel source each mirrors) live with them there.

# ---------------------------------------------------------------------------------------------
# The drift BACKSTOP the module docstring's own "RULE 1, NEVER A SECOND IMPLEMENTATION" mirror
# discipline demands (ledger row 1799 finding 3): CLASS_CHOICES/RELATION_CHOICES above are hand-
# mirrors of a kernel CHECK constraint's vocabulary; a hand-mirror with no check is a claim that
# it stays in sync, not a fact. These functions parse the vocabulary straight out of the kernel
# lineage SQL SOURCE TEXT (read-only, never edited or imported as a module -- kernel/lineage is
# frozen-record per CLAUDE.md) and compare it against this module's own CHOICES lists,
# injectable via parameters so a fixture can feed a SYNTHETIC disagreeing SQL text without
# touching kernel/lineage on disk.
# ---------------------------------------------------------------------------------------------

_CLASS_CHECK_RE = re.compile(
    r"agent_class\s+text\s+NOT\s+NULL\s+CHECK\s*\(\s*agent_class\s+IN\s*\(([^)]*)\)\s*\)"
)
_RELATION_CHECK_RE = re.compile(
    r"principal_relation\s+IN\s*\(([^)]*)\)"
)


def _parse_sql_string_list(inner: str) -> list[str]:
    """Parses a comma-separated `'a','b','c'` SQL string-literal list (the inside of an `IN
    (...)` clause) into a Python list, in source order -- never re-sorted, since the vocabulary
    might be display-ordered deliberately."""
    return [tok.strip().strip("'") for tok in inner.split(",") if tok.strip()]


def read_kernel_class_vocabulary(source_text: str | None = None) -> list[str]:
    """Parses `agent_class`'s CHECK vocabulary out of kernel/lineage/s15-schema.sql's own SOURCE
    TEXT -- the file that actually DEFINES the CHECK (module docstring's own provenance note:
    s40/s41 add events, never re-issue this CHECK). `source_text`, if given, is a SYNTHETIC
    stand-in (the fixture's red-leg injection point); default `None` reads the real file. Raises
    ValueError if the CHECK cannot be found/parsed."""
    if source_text is None:
        source_text = KERNEL_CLASS_CHECK_PATH.read_text(encoding="utf-8")
    m = _CLASS_CHECK_RE.search(source_text)
    if not m:
        raise ValueError(
            f"could not find the 'agent_class ... CHECK (agent_class IN (...))' constraint in "
            f"{KERNEL_CLASS_CHECK_PATH} -- drift check has nothing to compare against"
        )
    return _parse_sql_string_list(m.group(1))


def read_kernel_relation_vocabulary(source_text: str | None = None) -> list[str]:
    """Parses `principal_relation`'s CHECK vocabulary out of
    kernel/lineage/s41-principal-bindings-and-relations.sql's own SOURCE TEXT. `source_text`, if
    given, is a SYNTHETIC stand-in (the fixture's red-leg injection point); default `None` reads
    the real file. Raises ValueError if the CHECK cannot be found/parsed."""
    if source_text is None:
        source_text = KERNEL_RELATION_CHECK_PATH.read_text(encoding="utf-8")
    m = _RELATION_CHECK_RE.search(source_text)
    if not m:
        raise ValueError(
            f"could not find a 'principal_relation IN (...)' clause in "
            f"{KERNEL_RELATION_CHECK_PATH} -- drift check has nothing to compare against"
        )
    return _parse_sql_string_list(m.group(1))


def check_vocabulary_drift(
    class_choices: list[tuple[str, str]] | None = None,
    relation_choices: list[tuple[str, str]] | None = None,
    class_source_text: str | None = None,
    relation_source_text: str | None = None,
) -> list[str]:
    """Compares `class_choices`/`relation_choices` (default: this module's own CLASS_CHOICES/
    RELATION_CHOICES) against the live kernel CHECK vocabularies, read fresh from their own
    source text. Returns a list of drift messages, empty iff both agree AS SETS (order is a
    display choice this module owns, not part of the kernel's own contract). Every parameter is
    injectable (default `None` reads the real, live kernel sources) so a fixture can feed a
    SYNTHETIC disagreeing SQL text and observe the red leg without touching kernel/lineage on
    disk -- that tree stays read-only (frozen-record, CLAUDE.md)."""
    if class_choices is None:
        class_choices = CLASS_CHOICES
    if relation_choices is None:
        relation_choices = RELATION_CHOICES
    local_classes = {c for c, _ in class_choices}
    local_relations = {r for r, _ in relation_choices}
    kernel_classes = set(read_kernel_class_vocabulary(class_source_text))
    kernel_relations = set(read_kernel_relation_vocabulary(relation_source_text))
    drift: list[str] = []
    if local_classes != kernel_classes:
        drift.append(
            f"DRIFT: principals_authority.CLASS_CHOICES={sorted(local_classes)!r} != "
            f"kernel/lineage/s15-schema.sql agent_class CHECK={sorted(kernel_classes)!r}"
        )
    if local_relations != kernel_relations:
        drift.append(
            f"DRIFT: principals_authority.RELATION_CHOICES={sorted(local_relations)!r} != "
            f"kernel/lineage/s41-principal-bindings-and-relations.sql principal_relation "
            f"CHECK={sorted(kernel_relations)!r}"
        )
    return drift

# The five LESSON_* propaedeutic teaching strings -- imported above from
# tools/setup_tui/principals_authority_data.py (P10 data split, see module docstring's "CONTENT
# SPLIT" note); the spec §2 provenance note ("one home, not inline in screen code") lives there.

# ---------------------------------------------------------------------------------------------
# Reads -- BEFORE the boundary exists (module docstring): direct psql, `SET ROLE`, the SAME
# shape signed_genesis.py's own `_validated_dep_fields`/`_psql_json_rows` use, for the SAME reason (this
# screen also sits before screen_boundary in the flow). Kept as this module's own small copy
# rather than reaching into signed_genesis.py's underscore-prefixed internals -- `_validated_dep_fields`/
# the psql-rows helper are a connector thin enough that a shared home is not worth the coupling
# (unlike the row-id regex, which WAS a genuine three-way duplication of one fact and now has
# its one home in `runner.parse_row_id`, ledger row 1799 finding 1).
# ---------------------------------------------------------------------------------------------

def _validated_dep_fields(dest: str) -> dict:
    """Reads `<dest>/deployment.json` AND validates the fields this module later splices into
    SQL text (`schema`/`role` -- ledger row 1799 finding 5) at THIS boundary, before any of them
    reach a query string. Defense-in-depth, not paranoia: `deployment.json` is scaffold-written,
    not operator-typed, but "trusted here because a trusted process wrote it" is exactly the
    exemption law/adr/0012's 2026-07-18 interpreter-boundary amendment rejects ("the input is
    trusted here does not exempt a site") -- every value is re-checked at the splice module's own
    boundary regardless of provenance, the same discipline `probes.pg_connect`'s own schema check
    already applies to an operator-typed value."""
    path = os.path.join(dest, "deployment.json")
    with open(path, encoding="utf-8") as f:
        dep = json.load(f)
    for _field in ("schema", "role"):
        _val = dep.get(_field)
        if not isinstance(_val, str) or not probes.valid_identifier(_val):
            raise ValueError(
                f"deployment.json field {_field!r} = {_val!r} is not a valid SQL identifier "
                f"([A-Za-z0-9_]+) -- refusing to splice it into SQL text (law/adr/0012's "
                f"interpreter-boundary rule)"
            )
    return dep


def _psql_rows(dep: dict, sql: str, timeout: float = 15.0) -> list[str]:
    argv = ["psql", "-h", dep["host"], "-d", dep["db"], "-t", "-A", "-v", "ON_ERROR_STOP=1",
            "-c", sql]
    r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"psql query failed: {r.stderr.strip()}")
    # first line echoes the preceding `SET ROLE` statement -- the same documented quirk
    # signed_genesis.py's own `_psql_json_rows` carries.
    lines = [ln for ln in r.stdout.strip("\n").splitlines() if ln.strip()]
    return lines[1:] if lines else []


def list_principals(dest: str) -> list[dict]:
    """Every principal in `principal_standing_current` (kernel/lineage/s40-principal-identity-
    events.sql), oldest first -- id/name/class/standing/purpose. This is the world's OWN view,
    read raw, never re-derived (spec §1: "existing-principals display read from the world's own
    views"). Read-only; safe under `--dry-run` (a rehearsal that fakes its reads is a lie)."""
    dep = _validated_dep_fields(dest)
    sql = (f"SET ROLE {dep['role']};\n"
           f"SELECT row_to_json(t) FROM (SELECT id, name, agent_class, standing, purpose "
           f"FROM {dep['schema']}.principal_standing_current ORDER BY id) t;")
    return [json.loads(r) for r in _psql_rows(dep, sql)]


def s41_status(dest: str) -> tuple[bool, str]:
    """(available, reason). `available` is True iff `principal_relations` (an s41-only view)
    resolves; `reason` names the live check performed either way. Never a traceback on a
    pre-s41 world -- `to_regclass` is NULL-safe, no missing-relation error possible."""
    dep = _validated_dep_fields(dest)
    sql = (f"SET ROLE {dep['role']};\n"
           f"SELECT to_regclass('{dep['schema']}.principal_relations') IS NOT NULL;")
    rows = _psql_rows(dep, sql)
    available = bool(rows) and rows[0].strip() == "t"
    if available:
        return True, f"{dep['schema']}.principal_relations resolves (s41 present)"
    lineage = lineage_chain_note(dest)
    return False, (
        f"{dep['schema']}.principal_relations does not exist (to_regclass NULL) -- this world's "
        f"kernel lacks kernel/lineage/s41-principal-bindings-and-relations.sql. {lineage}"
    )


def lineage_chain_note(dest: str) -> str:
    """Best-effort ONE-LINE pointer at this world's own recorded lineage chain (HOOKS.md, written
    by bootstrap/new-project.sh's own `__LINEAGE_CHAIN__` template substitution) -- the "lineage
    head shown" spec §1 item 2 asks for on an s41-absent world. Never raises: an unreadable/
    missing HOOKS.md reads as an honest "not found", never a crash in a read-only display path."""
    hooks_path = os.path.join(dest, ".claude", "HOOKS.md")
    try:
        with open(hooks_path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return "(this world's HOOKS.md not found -- cannot show its recorded lineage chain)"
    idx = text.find("LINEAGE_CHAIN")
    if idx == -1:
        # older/hand-built worlds may not carry the literal marker text -- still honest, not a
        # crash: name what was searched for.
        return f"(no 'LINEAGE_CHAIN' marker found in {hooks_path})"
    snippet = text[idx: idx + 160].splitlines()[0]
    return f"this world's {hooks_path} records: {snippet.strip()}..."


# ---------------------------------------------------------------------------------------------
# PHASE-2 (design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md): plan-entry BUILDERS -- every one of these
# used to call `runner.run_command` directly (executing at decision time); each now returns a
# `(CommandAct, produces_key)` pair instead, appended into THE PLAN by screens.py and executed
# only at the one commit boundary. `LED_ACTOR=commissioner` is now `extra_env` on the act (plan.py
# Phase-2 addition), resolved fresh against the ambient environment at COMMIT time, never
# captured at decision time. `produces_key` names the binding a later Hole can reference (the row
# id these `led` verbs print on success, parsed via `runner.parse_row_id` at commit time --
# `_extract_row_id` below is that extractor, the ONE home for it, mirroring `runner.parse_row_id`
# itself); a caller that never needs the row id downstream simply never builds a `Hole` against it
# -- an unused `produces` binding costs nothing (commit_executor.py records it regardless).
# ---------------------------------------------------------------------------------------------

def _legacy_led(dest: str) -> str:
    return os.path.join(dest, "legacy", "led")


def _extract_row_id(output: str) -> str:
    """`Hole.extract` for a `led`/`legacy/led` write's real stdout (the ONE home for this parse,
    `runner.parse_row_id`, applied at commit time) -- the row id as a string if parseable, else
    the raw output verbatim (never a fabricated id; a later argv that actually needed a real id
    and got the raw text instead will fail loudly downstream rather than silently)."""
    row_id = parse_row_id(output)
    return str(row_id) if row_id is not None else output.strip()


_COMMISSIONER_ENV: tuple[tuple[str, str], ...] = (("LED_ACTOR", "commissioner"),)


def register_principal_act(dest: str, name: str, agent_class: str, purpose: str) -> tuple[CommandAct, str]:
    """`LED_ACTOR=commissioner <dest>/legacy/led register-principal <name> <class> --purpose
    "<purpose>"` -- the s40 registration ceremony (kernel/lineage/s40-principal-identity-
    events.sql §3.7), as a plan act. `LED_ACTOR=commissioner` mirrors signed_genesis.py's own
    choice: at this point in the flow the connection principal has no standing declaration of its
    own yet, and `commissioner` is one of the three principals the scaffold's own birth sequence
    already registers and declares standing for."""
    argv = (_legacy_led(dest), "register-principal", name, agent_class, "--purpose", purpose)
    return CommandAct(argv=argv, extra_env=_COMMISSIONER_ENV), f"principal-row:{name}"


def grant_competence_act(dest: str, name: str, activity: str, band: str,
                          basis: str) -> tuple[CommandAct, str]:
    """`<dest>/legacy/led principal grant-competence <name> --activity "<a>" --band "<b>"
    --basis "<c>"` (kernel/lineage/s41-principal-bindings-and-relations.sql D-1a/G13), as a plan
    act."""
    argv = (_legacy_led(dest), "principal", "grant-competence", name,
            "--activity", activity, "--band", band, "--basis", basis)
    return CommandAct(argv=argv, extra_env=_COMMISSIONER_ENV), f"competence-row:{name}:{activity}"


def relate_act(dest: str, subject: str, relation: str, obj: str) -> tuple[CommandAct, str]:
    """`<dest>/legacy/led principal relate <subject> <relation> <object>`
    (kernel/lineage/s41-principal-bindings-and-relations.sql D-2), as a plan act."""
    argv = (_legacy_led(dest), "principal", "relate", subject, relation, obj)
    return CommandAct(argv=argv, extra_env=_COMMISSIONER_ENV), f"relation-row:{subject}:{relation}:{obj}"


def charter_register_act(dest: str, role: str, path: str) -> tuple[CommandAct, str]:
    """`python3 tools/role_charter.py register <role> <path> --led <dest>/legacy/led` -- the SAME
    verb `screen_hydration`'s own role-charter item drives, pointed at `legacy/led` instead of the
    (not-yet-configured) served `led` (module docstring: this screen sits before
    `screen_boundary`), as a plan act."""
    argv = ("python3", str(REPO_ROOT / "tools" / "role_charter.py"), "register",
            role, path, "--led", _legacy_led(dest))
    return CommandAct(argv=argv), f"charter-row:{role}"


def is_registered(dest: str, name: str) -> bool:
    """True iff `name` already appears in `principal_standing_current` -- a LIVE read (spec §2.7's
    declared exception: read-only probes stay live). Under the pure-core flow this answers "is
    `name` registered as of the WORLD'S CURRENT state", not "will `name` be registered once this
    session's still-uncommitted plan entries run" -- a principal this SAME session already queued
    a registration for (not yet committed) will not show up here. `screen_principals_authority`
    carries its own decision-phase-local set of names it has queued a registration act for this
    run and consults BOTH before deciding whether the charter trap's in-flow-registration offer is
    needed (spec WP3) -- this function's own contract (a live read, nothing more) is unchanged."""
    try:
        return any(p["name"] == name for p in list_principals(dest))
    except Exception:  # noqa: BLE001 -- a read-only probe; caller decides how to report a failure
        return False
