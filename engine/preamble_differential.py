#!/usr/bin/env python3
"""preamble_differential -- the Part 3 preamble-ordering marriage's load-bearing gate: the ASP
verdict program (engine/lp/preamble_ordering.lp, producer two) differentialed BIT-IDENTICALLY
against the SQL floor (engine/preamble_floor.py, producer one) over one world's real inputs
(design/ORCH-CONTEMPORANEITY-PART3-SPEC.md §6, "the marriage discipline applies whole"). MATCHES
engine/ledger_differential.py's and engine/contemp_differential.py's OWN CONVENTIONS EXACTLY
(imported, not re-derived): the closed verdict vocabulary (AGREE / DIVERGE_BY_DESIGN /
DIVERGE_DEFECT / QUARANTINED), the DerivationRecord shape + retention idiom, the
override-one-producer negative-control seam, and the RED = non-zero-exit set.

SCOPE: this module compares ONLY engine/lp/preamble_ordering.lp's OWN #show set (ob_discharged/2,
ob_violated/2, ob_undecidable/3, ob_family_forced_undecidable/2, preamble_verdict/2,
commission_row/1, first_row/1, first_work_opened/1, criteria_ref/2) -- never the WHOLE clingo
witness, which also carries every #shown atom from engine/lp/contemporaneity.lp and
engine/lp/work_items.lp (loaded alongside per this program's own §4 load order) that this file's
own SQL floor does not, and is not asked to, re-derive. `_OWN_PREDICATE_PREFIXES` is the closed,
named filter.

DENOMINATION NORMALIZATION (mirrors engine/contemp_differential.py's own docstring section):
engine/contemp_edb.py emits every T anchor-relative; engine/preamble_floor.py emits every T
absolute epoch-ms natively (no 32-bit ceiling on the SQL side). Exactly FOUR families carry a
relative-ms Anchor argument in ob_discharged/2, ob_violated/2, and ob_undecidable/3's second
position -- F4 (ToolEventT), F9 (DispatchT), F10 (StopT), F11 (StopT) -- a CLOSED, family-keyed
list (`_TIME_ANCHORED_FAMILIES`), not a blanket numeric-argument heuristic: the other eight
families' Anchor is a RowId/Slug/Token, never time-relative, and must NOT be shifted by the
anchor. `preamble_verdict/2` and `ob_family_forced_undecidable/2` carry no Anchor at all --
untouched either way.

Read-only on every ledger + world directory. Registered in bootstrap/templates/audit.tmpl's
`--preamble` flag. Lazy imports banned (top-of-file only)."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

from clingo_run import run_clingo
from contemp_audit import _resolve_target_name
from contemp_edb import SAFE_32BIT_MS, UnsafeWindowError, export
from ledger_differential import (
    AGREE,
    DIVERGE_DEFECT,
    QUARANTINED,
    RED,
    VERDICTS,
    DerivationRecord,
    ProducerRun,
    _clingo_version,
    _now,
    _pg_version,
    _sha,
)
from ledger_edb import resolve as resolve_ledger
from preamble_floor import floor_atoms

HERE = Path(__file__).resolve().parent
PREAMBLE_LP = HERE / "lp" / "preamble_ordering.lp"
CONTEMP_LP = HERE / "lp" / "contemporaneity.lp"
WORK_ITEMS_LP = HERE / "lp" / "work_items.lp"
THRESHOLDS_LP = HERE / "contemp_thresholds.lp"
OBLIGATIONS_LP = HERE / "preamble_obligations.lp"
RETENTION = HERE / "docs" / "ledger-marriage" / "derivations" / "preamble-ordering"

_PROGRAM_FILES = [PREAMBLE_LP, CONTEMP_LP, THRESHOLDS_LP, OBLIGATIONS_LP, WORK_ITEMS_LP]

# preamble_ordering.lp's OWN #show set -- the closed filter (this module's own docstring SCOPE
# section). A future #show added to that file needs a matching entry here AND a matching SQL
# emission in preamble_floor.py -- named as the one place all three must move together.
_OWN_PREDICATE_PREFIXES = (
    "ob_discharged(", "ob_violated(", "ob_undecidable(", "ob_family_forced_undecidable(",
    "preamble_verdict(", "commission_row(", "first_row(", "first_work_opened(", "criteria_ref(",
)

# The four families whose Anchor argument is a relative-ms timestamp (this module's own
# docstring, DENOMINATION NORMALIZATION) -- a closed, named list, not a heuristic.
_TIME_ANCHORED_FAMILIES = frozenset({"f4", "f9", "f10", "f11"})
_ANCHOR2_RE = re.compile(r'^(ob_discharged|ob_violated)\((f\d+),(-?\d+)\)$')
_ANCHOR3_RE = re.compile(r'^(ob_undecidable)\((f\d+),(-?\d+),(\w+)\)$')


def _filter_own(atoms: set[str]) -> set[str]:
    """This program's OWN #show set only -- see this module's docstring SCOPE section."""
    return {a for a in atoms if a.startswith(_OWN_PREDICATE_PREFIXES)}


def _normalize_asp_atoms(atoms: set[str], anchor_ms: int) -> set[str]:
    """Rewrite the ASP producer's anchor-relative Anchor arguments to ABSOLUTE epoch-ms for the
    four time-anchored families only (this module's own docstring) -- every other atom (the
    other eight families' RowId/Slug/Token anchor, and every anchor-free predicate) passes
    through UNCHANGED."""
    out: set[str] = set()
    for a in atoms:
        m = _ANCHOR2_RE.match(a)
        if m:
            pred, fam, anc = m.groups()
            if fam in _TIME_ANCHORED_FAMILIES:
                out.add(f"{pred}({fam},{int(anc) + anchor_ms})")
                continue
        m = _ANCHOR3_RE.match(a)
        if m:
            pred, fam, anc, reason = m.groups()
            if fam in _TIME_ANCHORED_FAMILIES:
                out.add(f"{pred}({fam},{int(anc) + anchor_ms},{reason})")
                continue
        out.add(a)
    return out


def run_asp(target_name: str, root: Path) -> ProducerRun:
    """The ASP producer, run over world `root`'s real EDB (engine/contemp_edb.py, the SAME
    export Part 2's own differential uses -- Part 3 adds no separate EDB, per spec §4's binding
    one-anchor rule) -- filtered to this program's own #show set and normalized to absolute-ms
    before it is returned."""
    try:
        exp = export(target_name, root)
    except UnsafeWindowError as e:
        return ProducerRun("asp:clingo", quarantine=(
            f"UNSAFE ANCHOR SPAN (caught at the source, engine/contemp_edb.py's own export()): "
            f"{e}"))
    try:
        edb_text = exp.edb_text()
        raw_atoms = {a for a in run_clingo(_PROGRAM_FILES, edb_text) if "(" in a}
    except Exception as e:  # noqa: BLE001 -- a genuine tool/DB/clingo error, not a finding
        return ProducerRun("asp:clingo", quarantine=f"clingo/EDB failed: {type(e).__name__}: {e}")
    own = _filter_own(raw_atoms)
    atoms = _normalize_asp_atoms(own, exp.anchor_ms)
    program_text = "".join(p.read_text(encoding="utf-8") for p in _PROGRAM_FILES)
    rec = DerivationRecord(
        engine="clingo", version=_clingo_version(), config=[p.name for p in _PROGRAM_FILES],
        input_basis="edb-text (contemp EDB export, serialized; engine/contemp_edb.py)",
        input_hash=_sha(edb_text), program_hash=_sha(program_text),
        output_hash=_sha("\n".join(sorted(atoms))), target=target_name, ts=_now())
    return ProducerRun("asp:clingo", atoms=atoms, record=rec)


def run_sql(target_name: str, root: Path) -> ProducerRun:
    """The SQL floor producer, run over world `root`'s real ledger + journal files
    (engine/preamble_floor.py) -- already absolute-ms natively, no normalization needed."""
    try:
        atoms, snapshot = floor_atoms(target_name, root)
    except Exception as e:  # noqa: BLE001
        return ProducerRun("sql:floor", quarantine=f"SQL floor failed: {type(e).__name__}: {e}")
    db = resolve_ledger(target_name).db
    rec = DerivationRecord(
        engine="postgres", version=_pg_version(db), config=["preamble_floor.py::floor_atoms"],
        input_basis=f"live-db ledger rows ({db}) + independently re-read/re-parsed "
                    f"{root}/.claude/logs/*.jsonl journal files",
        input_hash=_sha(snapshot), program_hash=_sha((HERE / "preamble_floor.py").read_text(encoding="utf-8")),
        output_hash=_sha("\n".join(sorted(atoms))), target=target_name, ts=_now())
    return ProducerRun("sql:floor", atoms=atoms, record=rec)


@dataclass
class DifferentialResult:
    target: str
    asp: ProducerRun
    sql: ProducerRun
    only_asp: set[str] = field(default_factory=set)
    only_sql: set[str] = field(default_factory=set)

    def verdict(self) -> str:
        if self.asp.quarantine or self.sql.quarantine:
            return QUARANTINED
        if self.asp.record is None or self.sql.record is None:
            return QUARANTINED
        if not self.only_asp and not self.only_sql:
            return AGREE
        return DIVERGE_DEFECT  # no defeater-lens declared for this domain; any Δ is a defect


def run_differential(target_name: str, root: Path, *,
                     asp_atoms_override: set[str] | None = None,
                     sql_atoms_override: set[str] | None = None) -> DifferentialResult:
    """Differential one world. `asp_atoms_override`/`sql_atoms_override` are the negative-control
    seams (mirrors engine/contemp_differential.py's own): a fixture may inject a deliberately
    WRONG atom set for exactly one producer's OUTPUT, proving the differential catches a
    manufactured divergence, WITHOUT ever touching either producer's real code."""
    asp = run_asp(target_name, root)
    if asp_atoms_override is not None and asp.quarantine is None:
        asp.atoms = asp_atoms_override
    sql = run_sql(target_name, root)
    if sql_atoms_override is not None and sql.quarantine is None:
        sql.atoms = sql_atoms_override
    res = DifferentialResult(target=target_name, asp=asp, sql=sql)
    if asp.quarantine is None and sql.quarantine is None:
        res.only_asp = asp.atoms - sql.atoms
        res.only_sql = sql.atoms - asp.atoms
    return res


def _run_unique_dir(target: str) -> Path:
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    h = hashlib.sha256(f"{target}{ts}".encode("utf-8")).hexdigest()[:12]
    return RETENTION / target / f"{ts}_{h}"


def retain(res: DifferentialResult) -> Path:
    d = _run_unique_dir(res.target)
    d.mkdir(parents=True, exist_ok=False)
    (d / "asp_atoms.txt").write_text("\n".join(sorted(res.asp.atoms)) + "\n", encoding="utf-8")
    (d / "sql_atoms.txt").write_text("\n".join(sorted(res.sql.atoms)) + "\n", encoding="utf-8")
    records = {"target": res.target, "verdict": res.verdict(),
               "only_asp": sorted(res.only_asp), "only_sql": sorted(res.only_sql),
               "asp_record": asdict(res.asp.record) if res.asp.record else None,
               "sql_record": asdict(res.sql.record) if res.sql.record else None,
               "asp_quarantine": res.asp.quarantine, "sql_quarantine": res.sql.quarantine}
    (d / "derivation.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return d


def print_result(res: DifferentialResult) -> None:
    v = res.verdict()
    mark = "OK " if v == AGREE else "!! "
    print(f"  [{mark}] {res.target:12} {v:18} "
          f"asp={len(res.asp.atoms)} sql={len(res.sql.atoms)} atoms; "
          f"Δasp={sorted(res.only_asp)} Δsql={sorted(res.only_sql)}")
    if res.asp.quarantine:
        print(f"          asp QUARANTINED: {res.asp.quarantine}")
    if res.sql.quarantine:
        print(f"          sql QUARANTINED: {res.sql.quarantine}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="world directory (carries deployment.json + .claude/logs/)")
    ap.add_argument("--target", default=None, help="ledger target name (default: this world's own deployment.json 'name' field)")
    ap.add_argument("--retain", action="store_true", help="bank proof artifacts under engine/docs/ledger-marriage/derivations/preamble-ordering/")
    ap.add_argument("--drop-record", action="store_true",
                    help="negative control: drop the ASP derivation record and show the "
                         "consumer refuses (a verdict without its witness is NO RESULT)")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"preamble_differential: no such world directory: {root}", file=sys.stderr)
        return 2
    dep_path = root / "deployment.json"
    if dep_path.is_file():
        os.environ["LEDGER_DEPLOYMENT"] = str(dep_path)
    target_name = _resolve_target_name(root, args.target)

    print(f"# preamble-ordering marriage differential -- ASP (engine/lp/preamble_ordering.lp) vs "
          f"SQL floor (engine/preamble_floor.py)")
    print(f"#   target={target_name!r} root={root}")
    print(f"#   closed verdict vocabulary: {sorted(VERDICTS)}; RED = {sorted(RED)}\n")

    res = run_differential(target_name, root)
    if args.drop_record and res.asp.record is not None:
        res.asp.record = None
    print_result(res)
    if args.retain:
        d = retain(res)
        print(f"\n# retained: {d}")

    red = 1 if res.verdict() in RED else 0
    print(f"\n# {'DIFFERENTIAL RED' if red else 'DIFFERENTIAL GREEN'} -- "
          f"{'diverged/quarantined (NO RESULT)' if red else 'SQL floor bit-identical to the ASP verdict program'}")
    return red


if __name__ == "__main__":
    raise SystemExit(main())
