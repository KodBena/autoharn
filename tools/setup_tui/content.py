#!/usr/bin/env python3
"""tools/setup_tui/content.py -- loads and validates every TOML data file under
tools/setup_tui/data/ (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §6: "all prose, tables, step
definitions, defaults, and choice vocabularies move to declarative data files ... loaded and
validated at startup -- a malformed or incomplete data file REFUSES loudly at load, naming the
key"). This is the ONE place `tomllib.load` is called for this package's own content (ADR-0012
P1); every consumer module (`feature_facts.py`, `durable_decisions.py`, `principals_authority.py`,
`config_file.py`, `steps.py`) imports the already-validated tables from here, never reads a TOML
file itself.

Python holds behavior only (P10's own closing line) -- this module IS behavior (a loader +
validator), not data; the data lives entirely in the sibling `data/*.toml` files.
"""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

_KEY_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


class ContentError(RuntimeError):
    """A data file is missing, malformed, or missing a required key -- always named, never a
    silent default (ADR-0002 rule 1)."""


@dataclass(frozen=True)
class DataKey:
    """A validated row-identifier key from a `data/*.toml` table (a `fact.key`, a
    `decision.slug`). The single-value SHAPE contract (identifier-like: `[a-z][a-z0-9_-]*`, since
    every consumer splices it into a checklist item name / a `hydration_<slug>` feature-facts key
    / a CLAUDE.md marker) is enforced in `__post_init__` -- `DataKey("bad key!")` is
    unconstructable, not merely reviewed. UNIQUENESS within a table is a COLLECTION-level
    property no single instance can check on its own; `DataKey.parse` (the loader's own entry
    point) adds that check against the loader's running `seen` set, but the per-value contract
    below holds regardless of which constructor path is used."""
    value: str

    def __post_init__(self) -> None:
        if not _KEY_RE.match(self.value):
            raise ContentError(
                f"tools/setup_tui/content.py: key {self.value!r} must match [a-z][a-z0-9_-]* "
                f"(it is spliced into checklist/feature-facts identifiers)")

    @staticmethod
    def parse(raw: str, *, table: str, seen: "set[str]") -> "DataKey":
        key = DataKey(raw)  # the real contract enforced by __post_init__ above
        if key.value in seen:
            raise ContentError(f"tools/setup_tui/content.py: {table} key {raw!r} is duplicated")
        seen.add(key.value)
        return key

    def __str__(self) -> str:
        return self.value


def _forbid_pipe_delimiter(value: object, *, path: str) -> None:
    """Refuses a homemade ' | ' multi-fact delimiter ANYWHERE in a loaded data file -- companion
    rule C13 (law/adr/0019 appendix, "content is typed semantic elements; no layout carried
    inside a string"), ledger row 1117's own round-6 conviction: the round-5 elucidation fix
    (MEASURE capping) answered the WIDTH axis but left the STRUCTURE axis unnamed, and
    `feature_facts.toml` was proven to store aspiration/citations/external as ONE string joined
    with a homemade ' | ' field separator, rendered as prose with the separator visible
    mid-paragraph once wrapped. Recurses through every string, list, and nested table so the
    check is TOTAL over a file's own content -- every `_load` call runs this, not a per-file
    opt-in a future data file could forget. `path` names exactly where the offending value lives
    (e.g. "feature_facts.toml fact[3].aspiration"), per ADR-0002 rule 1 (never a silent default,
    always naming the key)."""
    if isinstance(value, str):
        if " | " in value:
            raise ContentError(
                f"tools/setup_tui/content.py: {path} contains a bare ' | ' separator -- a "
                f"homemade multi-fact delimiter is refused at load; schema the structure into "
                f"named keys/lists instead (companion rule C13, ledger row 1117): {value!r}")
        return
    if isinstance(value, list):
        for i, item in enumerate(value):
            _forbid_pipe_delimiter(item, path=f"{path}[{i}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _forbid_pipe_delimiter(item, path=f"{path}.{key}")


def _load(name: str) -> dict:
    path = DATA_DIR / f"{name}.toml"
    if not path.is_file():
        raise ContentError(f"tools/setup_tui/content.py: required data file missing: {path}")
    try:
        doc = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ContentError(f"tools/setup_tui/content.py: {path} is not valid TOML: {exc}") from exc
    _forbid_pipe_delimiter(doc, path=f"{name}.toml")
    return doc


def _require(d: dict, keys: "set[str]", filename: str) -> None:
    missing = keys - set(d)
    if missing:
        raise ContentError(
            f"tools/setup_tui/content.py: {filename}.toml is missing required key(s): "
            f"{sorted(missing)}")


def _require_row_keys(rows: list[dict], keys: "set[str]", filename: str, table: str) -> None:
    for i, row in enumerate(rows):
        missing = keys - set(row)
        if missing:
            raise ContentError(
                f"tools/setup_tui/content.py: {filename}.toml [[{table}]] row {i} is missing "
                f"required key(s): {sorted(missing)}")


# --------------------------------------------------------------------------------------------
# feature_facts.toml -- round-6 restructure (ledger row 1117): `standards`/`mechanism` are
# round-7 restructure (ledger row 1119): `lead`/`external` are each OPTIONAL (D6 -- an empty
# slot is not rendered at all, so a fact with nothing operator-relevant to say may omit both);
# `provenance` (operator-relevant citations, demoted) and `maintainer_refs` (internal-only
# citations, NEVER rendered) are OPTIONAL lists. Only `key`/`label` are truly required.
# --------------------------------------------------------------------------------------------
_ff = _load("feature_facts")
_require(_ff, {"fact"}, "feature_facts")
_require_row_keys(_ff["fact"], {"key", "label"}, "feature_facts", "fact")
_seen: set = set()
for _row in _ff["fact"]:
    DataKey.parse(_row["key"], table="feature_facts.fact", seen=_seen)
    for _list_key in ("provenance", "maintainer_refs"):
        if _list_key in _row and not isinstance(_row[_list_key], list):
            raise ContentError(
                f"tools/setup_tui/content.py: feature_facts.toml fact {_row['key']!r}.{_list_key} "
                f"must be a list of strings, got {type(_row[_list_key]).__name__}")
FEATURE_FACTS: list[dict] = _ff["fact"]

# --------------------------------------------------------------------------------------------
# durable_decisions.toml
# --------------------------------------------------------------------------------------------
_dd = _load("durable_decisions")
_require(_dd, {"decision"}, "durable_decisions")
_require_row_keys(_dd["decision"], {"slug", "rule", "why", "hydrates", "claude_md"},
                   "durable_decisions", "decision")
_seen = set()
for _row in _dd["decision"]:
    DataKey.parse(_row["slug"], table="durable_decisions.decision", seen=_seen)
    # `provenance`/`maintainer_refs` are OPTIONAL (round-6 restructure, ledger row 1117; round-7
    # audience-boundary split, ledger row 1119, defect D2): `why` is a short, citation-free
    # sentence; `provenance` names citations an OPERATOR could open and read (rendered, demoted);
    # `maintainer_refs` names internal-only citations (ledger rows, prior-project pointers) --
    # NEVER rendered.
    for _list_key in ("provenance", "maintainer_refs"):
        if _list_key in _row and not isinstance(_row[_list_key], list):
            raise ContentError(
                f"tools/setup_tui/content.py: durable_decisions.toml decision "
                f"{_row['slug']!r}.{_list_key} must be a list of strings, got "
                f"{type(_row[_list_key]).__name__}")
DURABLE_DECISIONS: list[dict] = _dd["decision"]

# --------------------------------------------------------------------------------------------
# principals_authority.toml
# --------------------------------------------------------------------------------------------
_pa = _load("principals_authority")
_require(_pa, {"class_choice", "relation_choice", "scaffold_principal", "lessons"},
         "principals_authority")
_require_row_keys(_pa["class_choice"], {"value", "label"}, "principals_authority", "class_choice")
_require_row_keys(_pa["relation_choice"], {"value", "label"}, "principals_authority", "relation_choice")
_require_row_keys(_pa["scaffold_principal"], {"name", "agent_class", "purpose"},
                   "principals_authority", "scaffold_principal")
# [lessons.*] SCHEMA (round-6 restructure, ledger row 1117): register/competence/relation/charter
# are each a SUB-TABLE with `constitutes`/`does_not` keys (no longer one hand-rolled
# "CONSTITUTES: ... DOES NOT: ..." string); `workflow_pointer` alone stays a plain scalar (it has
# no constitutes/does-not shape).
_require(_pa["lessons"], {"register", "competence", "relation", "charter", "workflow_pointer"},
         "principals_authority.lessons")
for _lesson_key in ("register", "competence", "relation", "charter"):
    _lesson = _pa["lessons"][_lesson_key]
    if not isinstance(_lesson, dict) or {"constitutes", "does_not"} - set(_lesson):
        raise ContentError(
            f"tools/setup_tui/content.py: principals_authority.toml [lessons.{_lesson_key}] "
            f"must be a sub-table with 'constitutes' and 'does_not' keys")
PA_CLASS_CHOICES: list[tuple[str, str]] = [(r["value"], r["label"]) for r in _pa["class_choice"]]
PA_RELATION_CHOICES: list[tuple[str, str]] = [(r["value"], r["label"]) for r in _pa["relation_choice"]]
PA_SCAFFOLD_PRINCIPALS: list[tuple[str, str, str]] = [
    (r["name"], r["agent_class"], r["purpose"]) for r in _pa["scaffold_principal"]]
PA_LESSONS: dict[str, object] = _pa["lessons"]

# --------------------------------------------------------------------------------------------
# config_schema.toml
# --------------------------------------------------------------------------------------------
_cs = _load("config_schema")
_require(_cs, {"header_keys", "key", "section_gate"}, "config_schema")
_require_row_keys(_cs["key"], {"path", "type"}, "config_schema", "key")
_require_row_keys(_cs["section_gate"], {"section", "gate"}, "config_schema", "section_gate")
CONFIG_HEADER_KEYS: set[str] = set(_cs["header_keys"])
CONFIG_SCHEMA: dict[str, str] = {r["path"]: r["type"] for r in _cs["key"]}
CONFIG_SECTION_GATE: dict[str, "str | None"] = {
    r["section"]: (r["gate"] or None) for r in _cs["section_gate"]}

# --------------------------------------------------------------------------------------------
# screens.toml
# --------------------------------------------------------------------------------------------
_sc = _load("screens")
_require(_sc, {"prompts", "partial_birth_teaching", "genesis_gate_hard_stop_teaching"}, "screens")
_require(_sc["prompts"], {"governed_files_extend", "foreign_scaffold", "principals_authority",
                          "signed_genesis_ceremony"}, "screens.prompts")
_require_row_keys(_sc["partial_birth_teaching"], {"kind", "text"}, "screens", "partial_birth_teaching")
SCREEN_PROMPTS: dict[str, str] = _sc["prompts"]
PARTIAL_BIRTH_TEACHING: list[tuple[str, str]] = [
    (r["kind"], r["text"]) for r in _sc["partial_birth_teaching"]]
GENESIS_GATE_HARD_STOP_TEACHING: list[str] = _sc["genesis_gate_hard_stop_teaching"]

# --------------------------------------------------------------------------------------------
# adr_synopses.toml -- round-6 addendum (maintainer coordinator addendum, same session as ledger
# row 1117): per-ADR digests for the hydration screen's ADR-adoption submenu, ORIENTATION not
# the law (the file's own header comment). A number with no synopsis entry here is a NAMED gap
# (`durable_decisions.adr_synopsis` returns an honest "no synopsis authored yet" marker), never a
# silent blank.
# --------------------------------------------------------------------------------------------
_adr = _load("adr_synopses")
_require(_adr, {"synopsis"}, "adr_synopses")
_require_row_keys(_adr["synopsis"], {"number", "text"}, "adr_synopses", "synopsis")
_seen = set()
for _row in _adr["synopsis"]:
    # NOT `DataKey.parse` -- an ADR number is `[0-9]{4}`, not an `[a-z]...` identifier (it is
    # never spliced into a checklist/feature-facts identifier the way a `DataKey` is); the
    # per-table uniqueness check is still enforced directly, without the identifier-shape half.
    if not re.match(r"^\d+$", _row["number"]):
        raise ContentError(f"tools/setup_tui/content.py: adr_synopses.toml number {_row['number']!r} "
                            f"must be all-digits")
    if _row["number"] in _seen:
        raise ContentError(f"tools/setup_tui/content.py: adr_synopses.toml number "
                            f"{_row['number']!r} is duplicated")
    _seen.add(_row["number"])
ADR_SYNOPSES: dict[str, str] = {r["number"]: r["text"] for r in _adr["synopsis"]}

# --------------------------------------------------------------------------------------------
# app.toml
# --------------------------------------------------------------------------------------------
_app = _load("app")
_require(_app, {"intro"}, "app")
_require(_app["intro"], {"heading", "driver_line", "guarantee_envelope_heading",
                         "guarantee_envelope_paragraphs", "dry_run_notice", "nav_hint"},
         "app.intro")
APP_INTRO: dict[str, object] = _app["intro"]
