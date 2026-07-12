#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T22:24:13Z
#   last-change: 2026-07-11T23:57:58Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""contemp_differential -- the contemporaneity marriage's load-bearing gate: the ASP verdict
program (engine/lp/contemporaneity.lp, producer two) differentialed BIT-IDENTICALLY against the
SQL floor (engine/contemp_floor.py, producer one) over one world's real inputs -- the deferred
half of design/CONTEMPORANEITY-AUDIT.md's Part 2 ("this verb ships ONE producer today, not the
marriage discipline's cross-validated pair"), closed by this module. MATCHES
engine/ledger_differential.py's OWN CONVENTIONS EXACTLY (imported, not re-derived, so the two
marriages cannot drift): the closed verdict vocabulary (AGREE / DIVERGE_BY_DESIGN /
DIVERGE_DEFECT / QUARANTINED), the DerivationRecord shape + retention idiom, the
override-one-producer negative-control seam, and the RED = non-zero-exit set.

CLOSED VERDICT VOCABULARY -- imported from engine/ledger_differential.py (VERDICTS/RED/AGREE/
DIVERGE_BY_DESIGN/DIVERGE_DEFECT/QUARANTINED), never redefined here: a second, textually-drifted
copy of a closed vocabulary is exactly the "cancer B" ADR-0012 P1 exists to foreclose. See that
module's own docstring for what each member means; unchanged here.

DENOMINATION NORMALIZATION (the one place this marriage differs mechanically from the ledger
marriage, named explicitly per this commission's mandate: "the COMPARISON must normalize to one
denomination before diffing, stated explicitly"). engine/contemp_edb.py emits every timestamp
ANCHOR-RELATIVE (a small delta from a per-export minimum, to dodge clingo/clasp's documented
32-bit signed-int wraparound on an absolute 2026-era epoch-ms value); engine/contemp_floor.py, the
SQL floor, has no such ceiling and emits every timestamp as its true ABSOLUTE epoch-ms value
natively (see that module's own docstring). Exactly THREE #show predicates carry an absolute-
timestamp argument -- `token_min_ts/2`, `token_max_ts/2`, `silence/2` -- so `_normalize_asp_atoms`
below rewrites ONLY those three predicate families' numeric argument(s) from anchor-relative to
absolute (adding the SAME `anchor_ms` engine/contemp_edb.py's own export computed), before the
set-difference runs. Every other #show predicate is either an Id/Tok-only atom (no ts argument at
all) or already a DIFFERENCE between two same-anchor values (`row_delta_ms/2`,
`preceding_activity_age_ms/2` -- anchor-invariant by construction, since subtracting a constant
from both operands of a subtraction leaves the result unchanged) -- both left untouched. The
chosen common denomination is ABSOLUTE epoch-ms (the SQL floor's native one, and the one a human
report can reconstruct to an ISO timestamp without consulting a second value) -- normalizing the
ASP side UP to it, rather than normalizing the SQL side DOWN to anchor-relative, because absolute
is the denomination that survives independent of which producer happened to run second.

PER-SOLVER SELF-PROVENANCE -- the SAME DerivationRecord dataclass engine/ledger_differential.py
defines, imported (not copied): every producer invocation banks {engine+version, config/args, EDB
hash, program hash, output hash, target, wall ts}; a verdict WITHOUT both records is QUARANTINED
(NO RESULT), never a silent pass.

RETENTION: banked under engine/docs/ledger-marriage/derivations/ -- the SAME tree the ledger
marriage already uses ("per the house pattern", this commission's own mandate) -- one level deeper
(`.../derivations/contemporaneity/<target>/<ts>_<hash>/`) so a contemporaneity world's own name
(an arbitrary per-project deployment.json `name`, not a curated s10/s11-style registry target)
can never collide with the ledger marriage's own target-keyed subdirectories in the same parent.

QUARANTINE GUARD -- NAMED DIVERGENCE FROM ledger_differential.run_asp's OWN GUARD, not an
oversight: that module additionally quarantines a non-empty-EDB run that yields literally zero
atoms (the F49 "silent grounding failure" heuristic), reasoning "every ledger has an unsuperseded
row" -- an invariant that domain actually has. THIS domain does NOT: engine/contemp_audit.py's own
docstring documents a REAL, legitimate all-untokened-ledger case where the verdict program
correctly yields ZERO shown atoms (every row untokened in a world whose interception is wired --
"that is itself a finding to investigate, not a vacuous pass," but it is not a QUARANTINE either).
Imposing the ledger side's heuristic here would misclassify that legitimate empty result as a
crash. The defense against an ACTUAL clingo grounding/parse failure is unchanged and still fully
present: engine/clingo_run.py's own `run_clingo` raises on any non-SOLVED Result (UNKNOWN/etc,
ADR-0015 Rule 3) rather than returning `[]`, so `run_asp` below still quarantines a genuine solver
failure -- it just does not ALSO second-guess a genuine empty derivation.

Read-only on every ledger + world directory. Registered in bootstrap/templates/audit.tmpl's
`--differential` flag (opt-in; see that file's own header for the latency reasoning). Lazy
imports banned (top-of-file only)."""
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
from contemp_floor import floor_atoms
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

HERE = Path(__file__).resolve().parent
CONTEMP_LP = HERE / "lp" / "contemporaneity.lp"
THRESHOLDS_LP = HERE / "contemp_thresholds.lp"
FLOOR_PY = HERE / "contemp_floor.py"
RETENTION = HERE / "docs" / "ledger-marriage" / "derivations" / "contemporaneity"

# The ONLY three #show predicates carrying an absolute-timestamp argument (see this module's own
# DENOMINATION NORMALIZATION section) -- a closed, named list, not a heuristic regex over every
# predicate, so a FUTURE predicate added to contemporaneity.lp defaults to "no normalization
# needed" (correct for an Id/Tok-only or already-differenced atom) rather than silently being
# mis-normalized by an over-eager pattern match.
_TS_PAIR_PREDS = ("silence",)
_TS_SINGLE_PREDS = ("token_min_ts", "token_max_ts")
_TS_SINGLE_RE = re.compile(
    r'^(' + '|'.join(_TS_SINGLE_PREDS) + r')\((".*?"),(-?\d+)\)$')
_TS_PAIR_RE = re.compile(
    r'^(' + '|'.join(_TS_PAIR_PREDS) + r')\((-?\d+),(-?\d+)\)$')

# NAMED HAZARD, FOUND LIVE DURING THIS COMMISSION'S OWN BUILD (a scratch fixture combining
# synthetic far-future rows with real `led`-shim "now" rows in the SAME accumulated ledger --
# BACKLOG.md's dated entry has the full account): engine/contemp_edb.py's anchor-relative
# encoding protects against clingo/clasp's 32-bit signed-int wraparound only for a BOUNDED
# audited window (its own docstring: "even a full week is ~6e8, safely under the 2^31 ceiling").
# Nothing enforces that bound -- both engine/contemp_edb.py and engine/contemp_floor.py read the
# WHOLE ledger table unconditionally, so a real project's ledger, or a scratch fixture mixing
# widely-separated timestamps, CAN exceed it, and the anchor-relative delta itself then wraps
# SILENTLY (clingo emits a small, wrong T with no error) -- exactly the same class of hazard
# contemp_edb.py's docstring already documents for the ABSOLUTE-value case, now shown to also
# apply to the "safe" relative encoding once the window is wide enough. `_max_abs_relative_ms`
# below is this module's OWN defense (in-scope: this file already owns the anchor-normalization
# step) -- it refuses loudly (QUARANTINED) rather than silently comparing two producers where the
# ASP side's own numeric encoding may already be corrupted.
#
# ADDENDUM, 2026-07-12 (BACKLOG "a second latent 32-bit clingo wraparound"; dated append, does not
# rewrite the paragraph above): engine/contemp_edb.py's own `export()` NOW enforces this same bound
# at the source, raising `UnsafeWindowError` before a single fact is emitted -- see that module's
# docstring, "ENFORCEMENT ADDENDUM, 2026-07-12". That fix protects EVERY caller of `export()`,
# including the default `./audit` path (`contemp_audit.py::run_audit`) this module's own guard
# never covered. `_max_abs_relative_ms` below and the `run_asp` check that uses it are KEPT,
# unremoved, as belt-and-braces (a second, independent, text-level check on the already-formatted
# EDB) -- in the ordinary case `export()` now raises first, so this module's own check is expected
# to never actually fire, but it costs nothing to keep as a second line of defense should a future
# change to contemp_edb.py's enforcement regress. `SAFE_32BIT_MS` is imported from contemp_edb
# (single home, ADR-0012 P1) rather than re-declared here, closing the two-independently-typed-
# copies-can-drift risk a literal like this invites (ADR-0000's own DECOMP_ANCHOR specimen).
_FACT_T_RE = re.compile(
    r'^(?:row_tokened|row_untokened|invocation|tool_event|row_declared)\(.*,(-?\d+)\)\.$')


def _max_abs_relative_ms(edb_text: str) -> int:
    """The largest absolute relative-ms value embedded in `edb_text`'s own fact lines (the T
    argument of row_tokened/row_untokened/invocation/tool_event/row_declared -- always the LAST
    argument, always a bare integer, never quoted, so a greedy `.*,` up to the trailing `)."`
    finds it correctly even when an earlier quoted Token argument itself contains commas/digits)."""
    m = 0
    for line in edb_text.splitlines():
        mm = _FACT_T_RE.match(line)
        if mm:
            v = abs(int(mm.group(1)))
            if v > m:
                m = v
    return m


def _normalize_asp_atoms(atoms: set[str], anchor_ms: int) -> set[str]:
    """Rewrite the ASP producer's anchor-relative ts arguments to ABSOLUTE epoch-ms (adding
    `anchor_ms`, the SAME value engine/contemp_edb.py's export computed for this exact EDB) --
    the one denomination-normalization step this marriage needs that engine/ledger_differential.py
    never had to perform (see this module's own docstring)."""
    out: set[str] = set()
    for a in atoms:
        m = _TS_SINGLE_RE.match(a)
        if m:
            pred, tok, t = m.groups()
            out.add(f"{pred}({tok},{int(t) + anchor_ms})")
            continue
        m = _TS_PAIR_RE.match(a)
        if m:
            pred, t1, t2 = m.groups()
            out.add(f"{pred}({int(t1) + anchor_ms},{int(t2) + anchor_ms})")
            continue
        out.add(a)
    return out


def run_asp(target_name: str, root: Path) -> ProducerRun:
    """The ASP producer, run over world `root`'s real EDB (engine/contemp_edb.py) -- normalized
    to absolute-ms before it is returned, so every caller (the differential's set-comparison AND
    any negative-control override) sees the SAME denomination the SQL floor natively emits."""
    try:
        exp = export(target_name, root)
    except UnsafeWindowError as e:
        # BELT: contemp_edb.py's own export() now refuses this at the source (that module's
        # docstring, "ENFORCEMENT ADDENDUM, 2026-07-12") -- this is expected to be the ONLY path
        # that fires today; the text-level check below (BRACES) is the second, independent layer.
        return ProducerRun("asp:clingo", quarantine=(
            f"UNSAFE ANCHOR SPAN (caught at the source, engine/contemp_edb.py's own export()): "
            f"{e}"))
    try:
        edb_text = exp.edb_text()
        max_rel = _max_abs_relative_ms(edb_text)
        if max_rel > SAFE_32BIT_MS:
            return ProducerRun("asp:clingo", quarantine=(
                f"UNSAFE ANCHOR SPAN (caught by this module's own BELT-AND-BRACES text-level "
                f"check -- contemp_edb.py's own guard should have already refused this; both "
                f"firing on the same world is itself worth investigating): this world's audited "
                f"window carries a relative delta of {max_rel}ms from its own anchor "
                f"({exp.anchor_ms}ms epoch) -- EXCEEDS clingo/clasp's signed 32-bit ceiling "
                f"({SAFE_32BIT_MS}ms, ~24.8 days). Refusing loudly rather than comparing a "
                f"possibly-corrupted producer -- NO RESULT (ADR-0015 Rule 3), never a guessed "
                f"AGREE or DIVERGE. See this module's own NAMED HAZARD comment + BACKLOG.md."))
        raw_atoms = {a for a in run_clingo([CONTEMP_LP, THRESHOLDS_LP], edb_text) if "(" in a}
    except Exception as e:  # noqa: BLE001 -- a genuine tool/DB/clingo error, not a finding
        return ProducerRun("asp:clingo", quarantine=f"clingo/EDB failed: {type(e).__name__}: {e}")
    atoms = _normalize_asp_atoms(raw_atoms, exp.anchor_ms)
    program_text = CONTEMP_LP.read_text(encoding="utf-8") + THRESHOLDS_LP.read_text(encoding="utf-8")
    rec = DerivationRecord(
        engine="clingo", version=_clingo_version(), config=[CONTEMP_LP.name, THRESHOLDS_LP.name],
        input_basis="edb-text (contemp EDB export, serialized; engine/contemp_edb.py)",
        input_hash=_sha(edb_text), program_hash=_sha(program_text),
        output_hash=_sha("\n".join(sorted(atoms))), target=target_name, ts=_now())
    return ProducerRun("asp:clingo", atoms=atoms, record=rec)


def run_sql(target_name: str, root: Path) -> ProducerRun:
    """The SQL floor producer, run over world `root`'s real ledger + journal files
    (engine/contemp_floor.py) -- already absolute-ms natively, no normalization needed."""
    try:
        atoms, snapshot = floor_atoms(target_name, root)
    except Exception as e:  # noqa: BLE001
        return ProducerRun("sql:floor", quarantine=f"SQL floor failed: {type(e).__name__}: {e}")
    db = resolve_ledger(target_name).db
    rec = DerivationRecord(
        engine="postgres", version=_pg_version(db), config=["contemp_floor.py::floor_atoms"],
        input_basis=f"live-db ledger rows ({db}) + independently re-read/re-parsed "
                    f"{root}/.claude/logs/*.jsonl journal files",
        input_hash=_sha(snapshot), program_hash=_sha(FLOOR_PY.read_text(encoding="utf-8")),
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
    seams (mirrors engine/ledger_differential.py's own `asp_atoms_override`): a fixture may inject
    a deliberately WRONG atom set for exactly one producer's OUTPUT, proving the differential
    catches a manufactured divergence, WITHOUT ever touching either producer's real code (this
    commission's own witness mandate: "never touch the real producers' semantics to fake it")."""
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
    """Run-unique retention subdir (mirrors engine/ledger_differential.py's own
    `_run_unique_dir` -- a bare `RETENTION / target` would be clobbered wholesale by a later
    --retain run reusing the same path, the single-mutable-slot defect that idiom forecloses)."""
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    h = hashlib.sha256(f"{target}{ts}".encode("utf-8")).hexdigest()[:12]
    return RETENTION / target / f"{ts}_{h}"


def retain(res: DifferentialResult) -> Path:
    """Bank the proof artifacts under engine/docs/ledger-marriage/derivations/contemporaneity/
    (this commission's mandate: 'DerivationRecord pairs banked ... per the house pattern')."""
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
    ap.add_argument("--retain", action="store_true", help="bank proof artifacts under engine/docs/ledger-marriage/derivations/contemporaneity/")
    ap.add_argument("--drop-record", action="store_true",
                    help="negative control: drop the ASP derivation record and show the "
                         "consumer refuses (a verdict without its witness is NO RESULT)")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"contemp_differential: no such world directory: {root}", file=sys.stderr)
        return 2
    # the SAME deployment.json -> LEDGER_DEPLOYMENT wiring engine/contemp_audit.py's own main()
    # uses (ADR-0012 P1: one resolution mechanism, not a second hand-copy) -- both producers
    # (run_asp via contemp_edb.export -> ledger_edb.resolve, run_sql via contemp_floor.floor_atoms
    # -> ledger_edb.resolve) need this env var set BEFORE targets.resolve() ever runs.
    dep_path = root / "deployment.json"
    if dep_path.is_file():
        os.environ["LEDGER_DEPLOYMENT"] = str(dep_path)
    target_name = _resolve_target_name(root, args.target)

    print(f"# contemporaneity marriage differential -- ASP (engine/lp/contemporaneity.lp) vs "
          f"SQL floor (engine/contemp_floor.py)")
    print(f"#   target={target_name!r} root={root}")
    print(f"#   closed verdict vocabulary: {sorted(VERDICTS)}; RED = {sorted(RED)}\n")

    res = run_differential(target_name, root)
    if args.drop_record and res.asp.record is not None:
        res.asp.record = None  # simulate a lost witness
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
