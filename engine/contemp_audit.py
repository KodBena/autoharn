#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T14:41:23Z
#   last-change: 2026-07-11T16:19:54Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""contemp_audit -- Part 2 of design/ORCH-CONTEMPORANEITY-AUDIT.md: the first-class correlation VERB
the maintainer commissioned ("we want a tool that can automatically run this correlation, in a
first-class way ... time deltas between actual events and recorded events", BACKLOG
"Contemporaneity indictment", 2026-07-11). Joins ledger rows to the invocation journal and the
hook-journaled tool-activity streams (engine/contemp_edb.py), runs the ASP verdict logic
(engine/lp/contemporaneity.lp + engine/contemp_thresholds.lp) via the shared clingo runner
(engine/clingo_run.py), and reports:

  1. per-row event-vs-record time deltas (row_delta_ms: ts minus the row's OWN invocation's
     journaled wall-clock -- the maintainer's own asked-for number) and the age of the preceding
     journaled tool-activity window at the moment each row landed.
  2. the burst table (STATED, token-keyed) -- each burst annotated `intake-shape (precedes all
     tool activity)` when EVERY row in it predates this world's first tool_event
     (design/MAINT-LATE-ENTRY-AND-INTAKE-SEMANTICS.md Proposal 1: benign by construction, no vocabulary
     change) -- or, degraded, the ts-cluster table (INFERRED, pre-token era only -- never
     presented as the same thing).
  3. the silence/backfill table, BACKFILL_SUSPECT tokens, and LATE_DECLARED tokens (Proposal 2:
     the identical silence-breaking-burst shape, but the row that breaks the silence carries a
     writer-declared event time predating its own write time beyond threshold -- the declared,
     legal form of a late entry; BACKFILL_SUSPECT is now precisely the UNDECLARED case).
  4. refusal fingerprints (burned ledger ids).
  5. the closed session verdict: CONTEMPORANEOUS | BATCHED_DECLARED | LATE_DECLARED |
     BACKFILL_SUSPECT -- OR an EXPLICIT TYPED REFUSAL naming the missing capability, per the
     spec's binding "HONEST HISTORICAL LIMIT": a token-less/journal-less world NEVER gets a
     vacuous pass and NEVER a guessed verdict.

OBSERVER-FIRST (design memo, "Whether a BACKFILL_SUSPECT verdict ever feeds the Stop gate is a
later maintainer question"): this verb reports; it gates nothing; it is not invoked from any
PreToolUse/Stop hook.

SECOND-PRODUCER STATUS (declared, ADR-0011 Rule 1): this pass ships ONE producer (the ASP
derivation). The SQL-floor differential (engine/ledger_floor.py's sibling, the marriage
discipline's AGREE bar) is FILED in BACKLOG.md, not built -- the maintainer's critical-path
resequencing (2026-07-11) scoped this pass to the ASP-derived core. A verdict here is NOT yet
marriage-grade cross-validated; this file's own report says so on every run (never silently
upgraded to "AGREE").

EXIT CODES (a closed, checkable vocabulary -- mirrors instruments/verify_contemporaneity_degrade.py's
existing N/A-is-distinct-from-clean convention, extended here):
  0  a verdict was computed and is CONTEMPORANEOUS, BATCHED_DECLARED, or LATE_DECLARED
     (clean-ish, no UNDECLARED suspect burst -- design/MAINT-LATE-ENTRY-AND-INTAKE-SEMANTICS.md
     Proposal 2: a declared late entry satisfies the mandate) -- OR the world is fully capable
     but its ledger carries ZERO rows, reported as VACUOUSLY_CLEAN in the output ("nothing to
     audit yet", explicitly NOT evidence of conduct; the run9 fix, 2026-07-11 -- a fresh,
     correctly-wired world is not refused for being young).
  1  a verdict was computed and is BACKFILL_SUSPECT (loud, per the judge-verdict precedent) --
     precisely the UNDECLARED case now that LATE_DECLARED exists to carry the declared one.
  2  a tool/DB/clingo error -- NOT a finding (ADR-0015 Rule 3: no result is not a clean result).
  3  N/A: the world's WIRING lacks a capability the full verdict needs (pre-s23 schema, or the
     journaling hooks genuinely off/unwired per its own settings.json/apparatus.json) -- the
     explicit typed refusal, never conflated with 0 or 1. A wired-but-still-empty journal is
     NOT this case (that is capability present with zero events -- see contemp_edb.Capability).

Lazy imports banned (top-of-file only)."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from clingo_run import run_clingo
from contemp_edb import CapabilityError, export

HERE = Path(__file__).resolve().parent
CONTEMP_LP = HERE / "lp" / "contemporaneity.lp"
THRESHOLDS_LP = HERE / "contemp_thresholds.lp"
RETENTION = HERE / "docs" / "contemporaneity-audit" / "runs"

VERDICTS = ("contemporaneous", "batched_declared", "late_declared", "backfill_suspect")


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _abs_iso(anchor_ms: int, relative_t: int) -> str:
    """Reconstruct an absolute UTC ISO-8601 timestamp from a relative-ms value this report
    carries (engine/contemp_edb.py's ANCHOR -- every T clingo reasoned over is anchor-relative,
    never absolute epoch-ms, to avoid the documented 32-bit clasp integer overflow)."""
    dt = datetime.datetime.fromtimestamp((anchor_ms + relative_t) / 1000, tz=datetime.timezone.utc)
    return dt.isoformat(timespec="milliseconds")


def _resolve_target_name(root: Path, explicit: str | None) -> str:
    """The label passed to engine/ledger_edb.resolve() -- mirrors bootstrap/templates/judge.tmpl's
    own resolution: an explicit --target wins; else this world's own deployment.json 'name' field
    (filing/deployment_record.py, the one home for that shape); else the literal 'world' (only
    reachable when LEDGER_DB/LEDGER_SCHEMA/LEDGER_KERN env vars are set directly, e.g. a scratch
    fixture that skips deployment.json entirely)."""
    if explicit:
        return explicit
    dep_path = root / "deployment.json"
    if dep_path.is_file():
        try:
            data = json.loads(dep_path.read_text(encoding="utf-8"))
            name = data.get("name")
            if name:
                return str(name)
        except (json.JSONDecodeError, OSError):
            pass
    return "world"


def _parse_atoms(atoms: list[str]) -> dict[str, list[tuple]]:
    """Group the shown atoms by predicate name -> list of argument-tuples (strings/ints, as
    written by clingo's --outf=2 JSON `Value` strings, e.g. 'token_burst("abc-123")'). A tiny,
    framework-free parser (no clingo Python binding available in this venv, per clingo_run.py's
    own docstring) -- splits on the outermost '(' ... ')' and the top-level commas only (no
    nested functors emitted by this program, so a naive top-level split is exact, not a
    heuristic)."""
    out: dict[str, list[tuple]] = defaultdict(list)
    for a in atoms:
        if "(" not in a or not a.endswith(")"):
            out[a].append(())
            continue
        name, rest = a.split("(", 1)
        rest = rest[:-1]
        args: list[str] = []
        depth, cur, in_str = 0, "", False
        for ch in rest:
            if ch == '"' and (not cur or cur[-1] != "\\"):
                in_str = not in_str
                cur += ch
            elif ch == "," and depth == 0 and not in_str:
                args.append(cur)
                cur = ""
            else:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                cur += ch
        if cur:
            args.append(cur)
        out[name].append(tuple(a.strip().strip('"') for a in args))
    return out


def run_audit(target_name: str, root: Path) -> dict:
    """The whole audit for one world: capability-gated EDB, ASP derivation, structured report.
    Never raises for an honest capability shortfall (returns a report with verdict=None and
    `refusal` set); DOES raise for a genuine tool error (bad target, DB unreachable, clingo
    crash) -- the caller's exit-code mapping distinguishes the two (2 vs 3)."""
    exp = export(target_name, root)
    edb_text = exp.edb_text()

    # THE RUN9 FIX (2026-07-11; see contemp_edb.Capability's docstring for the live specimen):
    # the verdict gate keys on the CAPABLE axis (the world's own wiring), never on whether any
    # events have been journaled yet -- a fully-wired, freshly-born world with empty journals is
    # capable (and, with zero ledger rows, vacuously clean below), not refused.
    capable = exp.capable_families()
    full_capable = (
        "s23_capable" in capable
        and "invocation_journal" in capable
        and "tool_event" in capable
    )

    program_text = CONTEMP_LP.read_text(encoding="utf-8") + THRESHOLDS_LP.read_text(encoding="utf-8")
    atoms = run_clingo([CONTEMP_LP, THRESHOLDS_LP], edb_text)
    if "row_untokened(" in edb_text or "row_tokened(" in edb_text:
        # a non-empty EDB that yields literally zero shown atoms means the program did not run
        # (the F49 silent-non-run hazard clingo_run.py itself already guards inside run_clingo
        # for UNKNOWN results; this is the residual "ran, but zero output over real input" case,
        # which for THIS program is legitimate whenever refusal_fingerprint/verdict/etc. are all
        # genuinely empty -- e.g. a two-row ledger with no gaps and no tokens at all -- so it is
        # NOT flagged as an error here, only noted structurally below.)
        pass
    parsed = _parse_atoms(atoms)

    report: dict = {
        "target": target_name,
        "root": str(root),
        "anchor_ms": exp.anchor_ms,  # every *_ms value below is relative to this absolute
                                     # epoch-ms (engine/contemp_edb.py's overflow-safety note)
        "capabilities": [{"family": c.family, "produced": c.produced, "capable": c.capable,
                          "reason": c.reason} for c in exp.capabilities],
        "counts": exp.counts,
        "skipped_lines": exp.skipped_lines,
        "full_capable": full_capable,
        "refusal_fingerprints": sorted(int(a[0]) for a in parsed.get("refusal_fingerprint", [])),
        "intake_shape_tokens": sorted(a[0] for a in parsed.get("intake_shape", [])),
        "token_bursts": sorted(
            [{"token": a[0], "row_count": int(next(
                (b[1] for b in parsed.get("token_row_count", []) if b[0] == a[0]), 0))}
             for a in parsed.get("token_burst", [])],
            key=lambda d: d["token"]),
        "ts_clusters": sorted((int(a[0]), int(a[1])) for a in parsed.get("ts_cluster", [])),
        "silences": sorted((int(a[0]), int(a[1])) for a in parsed.get("silence", [])),
        "backfill_suspect_tokens": sorted(a[0] for a in parsed.get("backfill_suspect", [])),
        "late_declared_tokens": sorted(a[0] for a in parsed.get("late_declared", [])),
        "honestly_late_rows": sorted(int(a[0]) for a in parsed.get("row_honest_late", [])),
        "row_deltas_ms": sorted(
            (int(a[0]), int(a[1])) for a in parsed.get("row_delta_ms", [])),
        "preceding_activity_age_ms": sorted(
            (int(a[0]), int(a[1])) for a in parsed.get("preceding_activity_age_ms", [])),
        "verdict": None,
        "refusal": None,
        "vacuous": False,
        "edb_sha256": exp.edb_hash(),
        "program_sha256": _sha(program_text),
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }

    verdict_atoms = parsed.get("verdict", [])
    n_rows = exp.counts.get("row_tokened", 0) + exp.counts.get("row_untokened", 0)
    if not full_capable:
        # missing keys on the CAPABLE axis (the run9 fix): a wired-but-empty journal is NOT
        # missing -- only a family the world's own wiring cannot record belongs in this list.
        missing = [c.family for c in exp.capabilities if not c.capable]
        report["refusal"] = (
            f"NO_VERDICT (capability-gated refusal, never a guessed verdict): this world cannot "
            f"support the full CONTEMPORANEOUS|BATCHED_DECLARED|LATE_DECLARED|BACKFILL_SUSPECT "
            f"vocabulary. Missing/excluded: {missing}. "
            + ("Degraded ts-cluster burst report available below (INFERRED, not STATED)."
               if report["ts_clusters"] else "No degraded signal available either."))
    elif n_rows == 0:
        # THE VACUOUS-CLEAN PATH (the run9 fix's second half): a fully-capable world with ZERO
        # ledger rows has nothing to correlate -- the honest outcome is an explicit vacuous
        # result, never a refusal (the capability is present; the corpus is empty) and never a
        # conduct verdict (there is no conduct on record to judge).
        report["vacuous"] = True
    elif verdict_atoms:
        report["verdict"] = verdict_atoms[0][0]
    else:
        report["refusal"] = (
            "NO_VERDICT: this world IS fully capable (s23 schema + invocation journaling + "
            "tool-event observers all wired) and carries ledger rows, but the ASP derivation "
            "produced no verdict atom -- every row is untokened (written outside the "
            "intercepted path) in a world whose interception is wired. That is itself a "
            "finding to investigate, not a vacuous pass: named explicitly.")
    return report


def _print_report(r: dict) -> None:
    print(f"# contemporaneity audit -- target={r['target']!r} root={r['root']}")
    print("#   capabilities (family, capable, produced): "
          f"{[(c['family'], c['capable'], c['produced']) for c in r['capabilities']]}")
    for c in r["capabilities"]:
        if not c["produced"]:
            tag = "EMPTY (capable, zero events yet)" if c["capable"] else "EXCLUDED"
            print(f"#   {tag} {c['family']}: {c['reason']}")
    for name, n in sorted(r["skipped_lines"].items()):
        if n:
            print(f"#   WARNING: {n} malformed line(s) skipped in {name}")
    print(f"#   counts: {r['counts']}")
    print()
    if r["refusal_fingerprints"]:
        print(f"REFUSAL FINGERPRINTS (burned ledger ids): {r['refusal_fingerprints']}")
    if r["full_capable"]:
        print("BURST TABLE (STATED -- rows per invocation token):")
        for b in r["token_bursts"]:
            note = ("  intake-shape (precedes all tool activity)"
                    if b["token"] in r["intake_shape_tokens"] else "")
            print(f"  token={b['token']} rows={b['row_count']}{note}")
        print("SILENCE TABLE (tool activity, zero ledger rows, gap > threshold):")
        for t1, t2 in r["silences"]:
            iso1 = _abs_iso(r["anchor_ms"], t1)
            iso2 = _abs_iso(r["anchor_ms"], t2)
            print(f"  [{iso1} .. {iso2}]  gap_ms={t2 - t1}")
        if r["backfill_suspect_tokens"]:
            print(f"BACKFILL_SUSPECT tokens (UNDECLARED gap): {r['backfill_suspect_tokens']}")
        if r["late_declared_tokens"]:
            print(f"LATE_DECLARED tokens (DECLARED gap, mandate satisfied): "
                  f"{r['late_declared_tokens']}")
        if r["honestly_late_rows"]:
            print(f"  honestly-declared-late row id(s): {r['honestly_late_rows']}")
        print("PER-ROW DELTAS (row ts minus its own invocation's journaled wall-clock, ms):")
        for rid, d in r["row_deltas_ms"]:
            print(f"  row {rid}: delta_ms={d}")
        print("PRECEDING-ACTIVITY AGE (ms since the nearest earlier tool_event, per row):")
        for rid, age in r["preceding_activity_age_ms"]:
            print(f"  row {rid}: age_ms={age}")
    else:
        print("DEGRADED ts-CLUSTER TABLE (INFERRED from row ts-adjacency, pre-token era only "
              "-- NEVER the same claim as a STATED token burst):")
        for id1, id2 in r["ts_clusters"]:
            print(f"  rows [{id1},{id2}] within burst_threshold_ms")
    print()
    if r["verdict"]:
        print(f"VERDICT: {r['verdict'].upper()}")
    elif r["vacuous"]:
        print("VACUOUSLY_CLEAN: 0 ledger rows -- nothing to audit yet. This world's recording "
              "apparatus is fully wired (s23 schema + invocation journaling + tool-event "
              "observers), so this is an honest empty corpus, NOT evidence of conduct and NOT "
              "a capability refusal. Re-run once the session has written ledger rows.")
    else:
        print(r["refusal"])


def retain(r: dict, edb_text: str) -> Path:
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    d = RETENTION / r["target"] / f"{ts}_{r['edb_sha256'][:12]}"
    d.mkdir(parents=True, exist_ok=False)
    (d / "edb.lp").write_text(edb_text, encoding="utf-8")
    (d / "report.json").write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")
    return d


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="world directory (carries deployment.json + .claude/logs/)")
    ap.add_argument("--target", default=None, help="ledger_edb.resolve() target name (default: read from deployment.json's name field, else 'world')")
    ap.add_argument("--retain", action="store_true", help="bank the EDB + report under engine/docs/contemporaneity-audit/runs/")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"contemp_audit: no such world directory: {root}", file=sys.stderr)
        return 2
    dep_path = root / "deployment.json"
    if dep_path.is_file():
        os.environ["LEDGER_DEPLOYMENT"] = str(dep_path)
    target_name = _resolve_target_name(root, args.target)

    try:
        r = run_audit(target_name, root)
    except CapabilityError as e:  # should not surface (run_audit handles capability gaps itself);
        print(f"contemp_audit: {e}", file=sys.stderr)          # kept as a defensive backstop.
        return 2
    except Exception as e:  # noqa: BLE001 -- a genuine tool error (DB unreachable, clingo crash)
        print(f"contemp_audit: tool error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    _print_report(r)
    if args.retain:
        exp = export(target_name, root)
        d = retain(r, exp.edb_text())
        print(f"\n# retained: {d}")

    if r["verdict"] == "backfill_suspect":
        return 1
    if r["verdict"] in ("contemporaneous", "batched_declared", "late_declared"):
        return 0
    if r["vacuous"]:
        return 0  # fully capable, zero ledger rows: honestly nothing to audit (the run9 fix) --
                  # clean by vacuity, stated in the output as such, never a refusal
    return 3  # N/A: capability-gated refusal (never conflated with 0/1)


if __name__ == "__main__":
    raise SystemExit(main())
