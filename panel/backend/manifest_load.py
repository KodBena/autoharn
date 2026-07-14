# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T23:21:20Z
#   last-change: 2026-07-14T23:25:06Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""panel.backend.manifest_load — loads + validates panel/manifests/*.json (spec S6, shape in
panel/manifests/SCHEMA.md, owned by WP-C).

This module owns ONLY the shape (ADR-0012 P1): a manifest is data describing which ledger facts
witness which commission item, authored once by WP-C, read here, never re-typed. It does not
resolve witnesses against the live ledger (ledger_read.py's job) and does not compute status
(disposition.py's job) -- it turns a JSON file into typed, validated Python values and refuses
loudly (ADR-0002) on a malformed manifest rather than silently dropping or guessing a field.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class ManifestError(Exception):
    """A manifest file is missing, unparseable, or missing/malformed a required field. Raised,
    never swallowed -- a caller that cannot load a manifest must stop loudly, not render a
    partial or guessed commission view."""


@dataclass(frozen=True)
class Witness:
    ref_kind: str  # "work" | "row"
    ref: str
    note: str


@dataclass(frozen=True)
class Item:
    id: str
    parent: str | None
    label: str
    text: str
    witnesses: tuple[Witness, ...]


@dataclass(frozen=True)
class Manifest:
    manifest_id: str
    commission_row: int
    title: str
    items: tuple[Item, ...]

    def item_by_id(self, item_id: str) -> Item | None:
        for item in self.items:
            if item.id == item_id:
                return item
        return None


_VALID_REF_KINDS = ("work", "row")


def _require_str(obj: dict, key: str, where: str) -> str:
    val = obj.get(key)
    if not isinstance(val, str) or not val:
        raise ManifestError(f"{where}: field '{key}' must be a non-empty string, got {val!r}")
    return val


def _load_witness(raw: dict, where: str) -> Witness:
    if not isinstance(raw, dict):
        raise ManifestError(f"{where}: each witness must be a JSON object, got {raw!r}")
    ref_kind = _require_str(raw, "ref_kind", where)
    if ref_kind not in _VALID_REF_KINDS:
        raise ManifestError(f"{where}: ref_kind must be one of {_VALID_REF_KINDS}, got {ref_kind!r}")
    # SCHEMA.md's own documented shape (panel/manifests/SCHEMA.md): a "work" ref is a work-item
    # slug (string); a "row" ref is a ledger row id, authored as a JSON integer (`{"ref_kind":
    # "row", "ref": 681, ...}`), never a quoted string. `Witness.ref` normalizes both to `str`
    # (the one type `ledger_read.resolve_witness` consumes for both kinds) -- this is the
    # boundary translating-and-validating the two legitimate on-the-wire shapes into one native
    # representation (ADR-0012 P2's Port/ACL discipline), not a laxer parse.
    raw_ref = raw.get("ref")
    if ref_kind == "row":
        if not isinstance(raw_ref, int) or isinstance(raw_ref, bool):
            raise ManifestError(
                f"{where}: a 'row' witness's 'ref' must be a JSON integer ledger row id, got {raw_ref!r}")
        ref = str(raw_ref)
    else:
        if not isinstance(raw_ref, str) or not raw_ref:
            raise ManifestError(
                f"{where}: a 'work' witness's 'ref' must be a non-empty work-item-slug string, got {raw_ref!r}")
        ref = raw_ref
    note = raw.get("note", "")
    if not isinstance(note, str):
        raise ManifestError(f"{where}: 'note' must be a string if present, got {note!r}")
    return Witness(ref_kind=ref_kind, ref=ref, note=note)


def _load_item(raw: dict, where: str) -> Item:
    if not isinstance(raw, dict):
        raise ManifestError(f"{where}: each item must be a JSON object, got {raw!r}")
    item_id = _require_str(raw, "id", where)
    item_where = f"{where} (item '{item_id}')"
    parent = raw.get("parent")
    if parent is not None and (not isinstance(parent, str) or not parent):
        raise ManifestError(f"{item_where}: 'parent' must be null or a non-empty string, got {parent!r}")
    label = _require_str(raw, "label", item_where)
    text = _require_str(raw, "text", item_where)
    raw_witnesses = raw.get("witnesses")
    if not isinstance(raw_witnesses, list):
        raise ManifestError(
            f"{item_where}: 'witnesses' must be a JSON array (possibly empty -- an item with no "
            f"genuine witness gets witnesses:[] and renders OPEN, never omitted), got {raw_witnesses!r}")
    witnesses = tuple(_load_witness(w, item_where) for w in raw_witnesses)
    return Item(id=item_id, parent=parent, label=label, text=text, witnesses=witnesses)


def parse_manifest(raw_text: str, source: str) -> Manifest:
    """Parse and validate one manifest's JSON text. `source` is a human-readable path/label used
    only in error messages."""
    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ManifestError(f"{source}: not valid JSON ({e.__class__.__name__}: {e})") from e
    if not isinstance(raw, dict):
        raise ManifestError(f"{source}: manifest must be a JSON object, got a {type(raw).__name__}")
    manifest_id = _require_str(raw, "manifest_id", source)
    commission_row = raw.get("commission_row")
    if not isinstance(commission_row, int) or isinstance(commission_row, bool):
        raise ManifestError(f"{source}: 'commission_row' must be an integer ledger row id, got {commission_row!r}")
    title = _require_str(raw, "title", source)
    raw_items = raw.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise ManifestError(f"{source}: 'items' must be a non-empty JSON array, got {raw_items!r}")
    items = tuple(_load_item(it, source) for it in raw_items)
    seen_ids = set()
    for item in items:
        if item.id in seen_ids:
            raise ManifestError(f"{source}: duplicate item id {item.id!r} -- item ids must be unique")
        seen_ids.add(item.id)
    for item in items:
        if item.parent is not None and item.parent not in seen_ids:
            raise ManifestError(
                f"{source}: item {item.id!r} declares parent {item.parent!r}, which is not any item's id")
    return Manifest(manifest_id=manifest_id, commission_row=commission_row, title=title, items=items)


def load_manifest(manifests_dir: Path, manifest_id: str) -> Manifest:
    """Load `<manifests_dir>/<manifest_id>.json`. Raises `ManifestError` (never returns a
    partial manifest) if the file is absent or fails validation."""
    path = manifests_dir / f"{manifest_id}.json"
    if not path.is_file():
        raise ManifestError(
            f"no manifest found at {path} -- known manifests: "
            f"{sorted(p.stem for p in manifests_dir.glob('*.json'))}")
    return parse_manifest(path.read_text(encoding="utf-8"), str(path))


def list_manifest_ids(manifests_dir: Path) -> list[str]:
    """Every manifest_id with a loadable file under `manifests_dir` (does not validate content --
    callers wanting a validated manifest use `load_manifest`)."""
    return sorted(p.stem for p in manifests_dir.glob("*.json"))
