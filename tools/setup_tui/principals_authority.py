#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T02:09:27Z
#   last-change: 2026-07-19T02:18:15Z
#   contributors: ab5d5bab/main
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

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import here is top of file.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from tools.setup_tui.runner import CommandResult, run_command

REPO_ROOT = Path(__file__).resolve().parents[2]

# Mirrors kernel/lineage/s15-schema.sql:62's agent_class CHECK ("agent_class text NOT NULL CHECK
# (agent_class IN ('human','model','subagent','tool'))") -- s40/s41 never widen this vocabulary,
# they only add EVENTS about principals that already carry one of these four classes.
CLASS_CHOICES = [
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
RELATION_CHOICES = [
    ("acts-for", "acts-for -- subject is REPRESENTABLE delegation for object (a recorded "
                 "declaration, not enforcement -- s41 D-2)"),
    ("dispatched-by", "dispatched-by -- subject was dispatched by object (the declaration; the "
                      "WITNESS of the fact remains the stamp pair, denominated separately)"),
    ("same-natural-person", "same-natural-person -- subject and object are the same human "
                            "(canonicalized to lower-id subject, kernel-CHECKed; symmetric)"),
    ("succeeds", "succeeds -- subject is the sanctioned successor of object (the v1 path back "
                "from a suspended/revoked principal -- no reinstatement verb exists)"),
]

_ROW_ID_RE = re.compile(r"\brow[_ ]?(?:id)?[:=]?\s*(\d+)\b", re.IGNORECASE)

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


# ---------------------------------------------------------------------------------------------
# Reads -- BEFORE the boundary exists (module docstring): direct psql, `SET ROLE`, the SAME
# shape signed_genesis.py's own `_dep_fields`/`_psql_json_rows` use, for the SAME reason (this
# screen also sits before screen_boundary in the flow). Kept as this module's own small copy
# rather than reaching into signed_genesis.py's underscore-prefixed internals -- the row-id-regex
# duplication between screens.py and signed_genesis.py is this codebase's own established
# precedent for a connector this thin.
# ---------------------------------------------------------------------------------------------

def _dep_fields(dest: str) -> dict:
    path = os.path.join(dest, "deployment.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


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
    dep = _dep_fields(dest)
    sql = (f"SET ROLE {dep['role']};\n"
           f"SELECT row_to_json(t) FROM (SELECT id, name, agent_class, standing, purpose "
           f"FROM {dep['schema']}.principal_standing_current ORDER BY id) t;")
    return [json.loads(r) for r in _psql_rows(dep, sql)]


def s41_status(dest: str) -> tuple[bool, str]:
    """(available, reason). `available` is True iff `principal_relations` (an s41-only view)
    resolves; `reason` names the live check performed either way. Never a traceback on a
    pre-s41 world -- `to_regclass` is NULL-safe, no missing-relation error possible."""
    dep = _dep_fields(dest)
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
# Writes -- every one of them `<dest>/legacy/led ...`, via `runner.run_command` (the --dry-run
# choke point; rule 1's exact-argv discipline).
# ---------------------------------------------------------------------------------------------

def _legacy_led(dest: str) -> str:
    return os.path.join(dest, "legacy", "led")


def _parse_row_id(res: CommandResult) -> int | None:
    if res.dry_run or not res.ok:
        return None
    m = _ROW_ID_RE.search(res.output)
    return int(m.group(1)) if m else None


def register_principal(dest: str, name: str, agent_class: str, purpose: str, *,
                        dry_run: bool = False) -> tuple[CommandResult, int | None]:
    """`LED_ACTOR=commissioner <dest>/legacy/led register-principal <name> <class> --purpose
    "<purpose>"` -- the s40 registration ceremony (kernel/lineage/s40-principal-identity-
    events.sql §3.7). `LED_ACTOR=commissioner` mirrors signed_genesis.py's own choice: at this
    point in the flow the connection principal has no standing declaration of its own yet, and
    `commissioner` is one of the three principals the scaffold's own birth sequence already
    registers and declares standing for."""
    led = _legacy_led(dest)
    argv = [led, "register-principal", name, agent_class, "--purpose", purpose]
    env = {**os.environ, "LED_ACTOR": "commissioner"}
    res = run_command(argv, env=env, dry_run=dry_run)
    return res, _parse_row_id(res)


def grant_competence(dest: str, name: str, activity: str, band: str, basis: str, *,
                      dry_run: bool = False) -> tuple[CommandResult, int | None]:
    """`<dest>/legacy/led principal grant-competence <name> --activity "<a>" --band "<b>"
    --basis "<c>"` (kernel/lineage/s41-principal-bindings-and-relations.sql D-1a/G13)."""
    led = _legacy_led(dest)
    argv = [led, "principal", "grant-competence", name,
            "--activity", activity, "--band", band, "--basis", basis]
    env = {**os.environ, "LED_ACTOR": "commissioner"}
    res = run_command(argv, env=env, dry_run=dry_run)
    return res, _parse_row_id(res)


def relate(dest: str, subject: str, relation: str, obj: str, *,
           dry_run: bool = False) -> tuple[CommandResult, int | None]:
    """`<dest>/legacy/led principal relate <subject> <relation> <object>`
    (kernel/lineage/s41-principal-bindings-and-relations.sql D-2)."""
    led = _legacy_led(dest)
    argv = [led, "principal", "relate", subject, relation, obj]
    env = {**os.environ, "LED_ACTOR": "commissioner"}
    res = run_command(argv, env=env, dry_run=dry_run)
    return res, _parse_row_id(res)


def charter_register(dest: str, role: str, path: str, *,
                      dry_run: bool = False) -> CommandResult:
    """`python3 tools/role_charter.py register <role> <path> --led <dest>/legacy/led` -- the
    SAME verb `screen_hydration`'s own role-charter item drives, pointed at `legacy/led` instead
    of the (not-yet-configured) served `led` (module docstring: this screen sits before
    `screen_boundary`). Driven through `runner.run_command` so `--dry-run` never executes
    role_charter.py at all (its own internal `led decision` subprocess calls never fire under a
    rehearsal -- `run_command`'s own choke point, not a second dry-run-awareness this module or
    role_charter.py would otherwise need)."""
    argv = ["python3", str(REPO_ROOT / "tools" / "role_charter.py"), "register",
            role, path, "--led", _legacy_led(dest)]
    return run_command(argv, dry_run=dry_run)


def is_registered(dest: str, name: str) -> bool:
    """True iff `name` already appears in `principal_standing_current` -- the in-flow check the
    charter trap's resolution (spec WP3) needs before offering registration."""
    try:
        return any(p["name"] == name for p in list_principals(dest))
    except Exception:  # noqa: BLE001 -- a read-only probe; caller decides how to report a failure
        return False
