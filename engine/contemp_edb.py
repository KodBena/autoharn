#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T14:40:08Z
#   last-change: 2026-07-11T15:10:28Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""contemp_edb -- the EDB builder for Part 2 of design/CONTEMPORANEITY-AUDIT.md (the
correlation verb; BACKLOG "Contemporaneity indictment", 2026-07-11). Exports the typed EDB
`engine/lp/contemporaneity.lp` reasons over, from a WORLD (a project directory carrying the
ledger's deployment.json plus its `.claude/logs/*.jsonl` hook journals) -- the fact-mining-side
analog `engine/ledger_edb.py` is for `ledger_tnow.lp`, mirrored here for the same capability-
manifest discipline (I12: a not-produced family is a DECLARED EXCLUSION with its reason,
never silent -- the F49 vacuous-pass class ADR-0000/ADR-0015 forbid).

THREE INPUT STREAMS, ONE WORLD:
  1. the LEDGER (Postgres, via engine/ledger_edb.Target/resolve) -- row_tokened/row_untokened.
  2. `<root>/.claude/logs/invocations.jsonl` (hooks/stamp_intercept.py, s23-era) -- invocation/2.
  3. the three hook-journaled tool-activity logs already on disk for OTHER purposes
     (mutation_observer.journal.jsonl, change_gate.journal.jsonl,
     delegation_observer.journal.jsonl) -- tool_event/2, re-purposed as the design memo's Part 2
     directive names them ("the hook-journaled tool activity that already exists").

CAPABILITY-GATED, HONESTLY (mirrors ledger_edb.py's Capability/EdbExport/require() idiom --
including its produced-vs-capable TWO-AXIS split, adopted here after the run9 live specimen,
2026-07-11: see Capability's own docstring). A world missing a stream is NOT an error here: the
manifest declares the absence and its reason, and `require()` refuses LOUDLY only when a CALLER
depends on a family that was not produced -- so `engine/contemp_audit.py` can request the full
verdict, get refused with the concrete reason (pre-s23; hooks genuinely off/unwired), and print
that refusal instead of a guessed or vacuous verdict (the spec's "HONEST HISTORICAL LIMIT"
binding constraint). CAPABILITY IS WIREDNESS, NOT CORPUS NON-EMPTINESS: whether a journal
family is `capable` is read from the world's own .claude/settings.json (+ apparatus.json off-
switches), so a fully-wired, freshly-born world whose journals are simply still empty reads as
capable-with-zero-events (a vacuously clean state the verdict layer reports as such), never as
"observers off/unwired" (the false refusal that stopped run9).

TIMESTAMP UNITS: every fact carries a MILLISECOND-resolution integer (bursts are sub-second;
clingo has no reliable float comparison, so ms-integers are the one honest denomination --
ADR-0000 2026-07-02 amendment's denomination check, applied to the EDB itself) -- but NOT
absolute epoch-ms. clingo/clasp's integer terms are 32-bit signed C ints (empirically verified:
`echo 'a(2000001010000).' | clingo - --outf=2` prints `a(-1453749936)` -- silent wraparound, no
error, on a value clingo's own CLI accepts and grounds without complaint). An absolute 2026-era
epoch-ms value (~1.78e12) is roughly 800x past the ~2.15e9 signed-32-bit ceiling, so it wraps on
EVERY export, silently, with no warning from clingo -- exactly the kind of hazard CLAUDE.md's
engineering-responsibility corollary exists for (found live, in this module's own first test run
against a real world, before the wraparound was noticed: `silence(-1453749936,-1453444936)`).
Wraparound is (usually) invisible in a same-window DIFFERENCE (T2-T1 is correct mod 2^32
whenever the true difference is small, which it always is here), which is why the burst/cluster
pairing logic tested correct against real run7 data before this was caught -- but it is NOT safe
for an absolute value shown directly (`silence/2`'s own T1/T2) or for a `>=`/`<=` COMPARISON
whose two operands could wrap by different multiples of 2^32 (not reachable within one export's
narrow time window today, but not something to rely on either). The fix: every T this module
emits is RELATIVE to one per-export ANCHOR (the minimum timestamp across every fact family in
this export), so the values clingo actually reasons over are small deltas (bounded by the
audited window's duration in ms -- even a full week is ~6e8, safely under the 2^31 ceiling), and
the anchor (`ContempEdbExport.anchor_ms`) lets a report reconstruct the true absolute time for
display (`to_absolute_ms`) without ever feeding an absolute value back into clingo.

NAMED HAZARD, FLAGGED NOT SILENTLY ROUTED AROUND (CLAUDE.md's engineering-responsibility
corollary): the three hook journals do NOT agree on a timestamp convention.
`posttooluse_mutation_observer.py` and `hooks/stamp_intercept.py` (invocations.jsonl) both write
UTC with a trailing "Z" (`time.strftime(...) + "Z"`); `pretooluse_change_gate.py` and
`pretooluse_delegation_observer.py` write a NAIVE LOCAL `datetime.now().isoformat(...)` with NO
timezone suffix at all. This module parses both shapes explicitly (see `_parse_ts_ms`) rather
than silently mis-reading one as the other, but the naive-local shape is only correct when read
on the SAME host/timezone that wrote it (true for this project's one-operator, one-host use
today, false in general) -- filed in BACKLOG.md by the commission that built this module.
RESOLVED AT THE SOURCE 2026-07-11, same day, in the pre-run-9 liveness window: both naive-local
hooks now write UTC-Z like their siblings. The naive-local parse branch below is KEPT
deliberately -- journal lines written before the fix remain on disk and must stay readable;
same-host reading remains the correct assumption for exactly those historical lines.

Read-only. Lazy imports banned (top-of-file only)."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from clingo_run import quote_term
from ledger_edb import Target, resolve

# The three existing hook journals this module re-purposes as the tool_event/2 stream (design
# memo Part 2 directive: "tool_event(Kind, T) (from the hook journals -- change-gate,
# mutation-observer marker, delegation journal)"). Filename -> the Kind atom it contributes.
_TOOL_EVENT_JOURNALS: dict[str, str] = {
    "mutation_observer.journal.jsonl": "mutation",
    "change_gate.journal.jsonl": "change_gate",
    "delegation_observer.journal.jsonl": "delegation",
}
_INVOCATION_JOURNAL = "invocations.jsonl"

# The journal-writing mechanisms and the hook script whose presence in a world's
# .claude/settings.json means that mechanism is WIRED (the capability signal the run9 fix
# keys on -- see Capability's docstring). apparatus.json key -> hook script basename.
# stamp_intercept writes invocations.jsonl; the other three write the tool-event journals.
_JOURNALING_MECHANISMS: dict[str, str] = {
    "stamp_intercept": "stamp_intercept.py",
    "change_gate": "pretooluse_change_gate.py",
    "mutation_observer": "posttooluse_mutation_observer.py",
    "delegation_observer": "pretooluse_delegation_observer.py",
}
_TOOL_EVENT_MECHANISMS = frozenset({"change_gate", "mutation_observer", "delegation_observer"})


def _wired_journaling_mechanisms(root: Path) -> set[str]:
    """Which journal-writing mechanisms this world's OWN wiring declares live: the hook script
    is referenced in `<root>/.claude/settings.json` (the scaffold writes the hooks' full
    autoharn paths into the command strings, so a basename substring test on the raw text is
    exact for scaffolded worlds and robust to settings-shape changes) AND the mechanism is not
    explicitly `"off"` in `<root>/.claude/apparatus.json` (an off-mode hook returns before any
    journal write -- each hook's own documented contract). A missing/unreadable settings.json
    yields the empty set: with no wiring evidence at all, capability is honestly ABSENT, which
    is exactly the pre-scaffold / hand-rolled-world case the refusal path exists for. A missing
    apparatus.json knocks nothing out (each hook's own default mode journals)."""
    settings_path = root / ".claude" / "settings.json"
    try:
        settings_text = settings_path.read_text(encoding="utf-8")
    except OSError:
        return set()
    wired = {mech for mech, script in _JOURNALING_MECHANISMS.items() if script in settings_text}
    if not wired:
        return wired
    try:
        apparatus = json.loads((root / ".claude" / "apparatus.json").read_text(encoding="utf-8"))
        mechs = apparatus.get("mechanisms", {}) if isinstance(apparatus, dict) else {}
        for mech in list(wired):
            entry = mechs.get(mech)
            if isinstance(entry, dict) and entry.get("mode") == "off":
                wired.discard(mech)
    except (OSError, json.JSONDecodeError):
        pass  # no/unreadable apparatus.json -> hooks run at their own defaults, all journal
    return wired


@dataclass(frozen=True)
class Capability:
    """A fact family's status on a world. TWO AXES, deliberately distinct (the ledger_edb.py
    Capability idiom, adopted here after the run9 live specimen, 2026-07-11): `produced` =
    facts of this family were actually EMITTED into this EDB; `capable` = the world's own
    wiring says this family CAN be recorded here (the journaling hook is wired in
    settings.json and not apparatus-off), regardless of whether anything has happened yet.
    Collapsing the two -- the first-landed draft keyed capability on corpus non-emptiness,
    `produced = len(events) > 0` -- made a healthy, fully-wired, freshly-born world (run9,
    the first s23-capable world) indistinguishable from an unwired one: zero tool events
    because NOTHING JOURNAL-WORTHY HAD HAPPENED YET read as "observer hooks off/unwired",
    and the audit refused a verdict the world was entitled to; the maintainer stopped the
    run over it. Capability means CAPABILITY; emptiness of a wired journal is a (vacuously
    clean) finding, not an absence of the recording apparatus."""
    family: str
    produced: bool   # facts of this family actually emitted into this EDB
    capable: bool    # the world's wiring supports this family (produced implies capable)
    reason: str


class CapabilityError(RuntimeError):
    """Raised when a caller (engine/contemp_audit.py) requests a fact family this world's EDB
    did not produce (ADR-0015 Rule 4) -- the honest typed refusal, never a silent empty read
    as "clean"."""


@dataclass
class ContempEdbExport:
    root: Path
    target_name: str
    facts: list[str] = field(default_factory=list)
    capabilities: list[Capability] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    skipped_lines: dict[str, int] = field(default_factory=dict)
    anchor_ms: int = 0  # the absolute epoch-ms every emitted T is relative to -- see export()'s
                        # "ANCHOR" section for why this exists (clingo/clasp integer overflow).

    def to_absolute_ms(self, relative_t: int) -> int:
        """Reconstruct an absolute epoch-ms value from a relative T this export emitted (report
        display only -- never fed back into clingo, which is the whole point of the anchor)."""
        return self.anchor_ms + relative_t

    def produced_families(self) -> set[str]:
        return {c.family for c in self.capabilities if c.produced}

    def capable_families(self) -> set[str]:
        """The families this world's WIRING supports (the run9-fix axis) -- what a verdict's
        capability gate keys on. produced implies capable; capable does not imply produced
        (a wired journal with zero events yet is capable-but-empty, not excluded)."""
        return {c.family for c in self.capabilities if c.capable}

    def exclusions(self) -> list[Capability]:
        """Families NOT emitted -- both capable-but-empty and genuinely incapable; the EDB
        header prints the two kinds distinctly (EMPTY vs EXCLUDED)."""
        return [c for c in self.capabilities if not c.produced]

    def require(self, family: str) -> None:
        if family not in self.produced_families():
            cap = next((c for c in self.capabilities if c.family == family), None)
            reason = cap.reason if cap else "not a known fact family"
            raise CapabilityError(
                f"world '{self.root}' (target '{self.target_name}') did not produce {family} "
                f"facts: {reason}. A silent empty here would be a vacuous-pass verdict; "
                f"refusing loudly instead.")

    def edb_text(self) -> str:
        anchor_iso = (datetime.fromtimestamp(self.anchor_ms / 1000, tz=timezone.utc)
                     .isoformat(timespec="milliseconds")) if self.anchor_ms else "n/a (no facts)"
        head = [f"% ==== contemporaneity EDB: world '{self.root}' target '{self.target_name}'",
                f"% ==== produced: {sorted(self.produced_families())}",
                f"% ==== ANCHOR (every T below is relative-ms to this): {self.anchor_ms} "
                f"({anchor_iso})"]
        for c in self.exclusions():
            tag = "EMPTY (capable, zero events yet)" if c.capable else "EXCLUDED"
            head.append(f"% ==== {tag} {c.family}: {c.reason}")
        for name, n in sorted(self.skipped_lines.items()):
            if n:
                head.append(f"% ==== WARNING: {n} malformed line(s) skipped in {name}")
        return "\n".join(head) + "\n" + "\n".join(self.facts) + "\n"

    def edb_hash(self) -> str:
        return hashlib.sha256(self.edb_text().encode("utf-8")).hexdigest()


def _parse_ts_ms(raw: str) -> int | None:
    """Parse EITHER journal timestamp convention this world's hooks may have written (see this
    module's docstring "NAMED HAZARD"): a trailing 'Z' is UTC (stamp_intercept.py /
    mutation_observer); no trailing 'Z' is a NAIVE LOCAL `datetime.now().isoformat()`
    (change_gate / delegation_observer), read against THIS process's local timezone. Returns
    None (never raises) for a malformed timestamp -- the caller counts the skip."""
    raw = raw.strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            dt = datetime.fromisoformat(raw[:-1]).replace(tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)
        dt = datetime.fromisoformat(raw)  # naive local
        return int(time.mktime(dt.timetuple()) * 1000 + dt.microsecond // 1000)
    except (ValueError, OverflowError):
        return None


def _read_jsonl(path: Path) -> tuple[list[dict], int]:
    """Best-effort JSONL read: (records, malformed-line-count). Never raises -- a hook's own
    journal write is already best-effort (see hooks/stamp_intercept.py's own docstring), so the
    reader matches that posture, but COUNTS the skip instead of silently absorbing it."""
    if not path.is_file():
        return [], 0
    recs: list[dict] = []
    skipped = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        if isinstance(obj, dict):
            recs.append(obj)
        else:
            skipped += 1
    return recs, skipped


def export(target_name: str, root: Path) -> ContempEdbExport:
    """Build the contemporaneity EDB for one world: `target_name` resolves the ledger (via
    engine/ledger_edb.resolve -- set LEDGER_DEPLOYMENT=<root>/deployment.json for a project's own
    world, exactly as engine/ledger_differential.py's callers already do); `root` is the world's
    own directory, the home of `.claude/logs/*.jsonl`. Read-only throughout.

    TWO PASSES, ON PURPOSE (see this module's docstring, "TIMESTAMP UNITS"): pass 1 reads every
    raw absolute-epoch-ms value from all three streams WITHOUT emitting any fact yet, so the
    ANCHOR (the minimum across everything) is known before a single T is written; pass 2 emits
    every fact with T relative to that anchor. Never emit an absolute epoch-ms into a fact --
    that is exactly the clasp-32-bit-overflow hazard this module's docstring documents."""
    t = resolve(target_name)
    exp = ContempEdbExport(root=root, target_name=target_name)

    # ---- capability 1: stamp_invocation column (s23) --------------------------------------
    has_invocation_col = t.has_col("stamp_invocation")
    exp.capabilities.append(Capability(
        "stamp_invocation_column", produced=True, capable=True,  # ALWAYS: row_tokened/row_untokened
        reason="ledger.kind/id/ts always readable regardless of s23; token split is per-row"))

    # ---- the WIRING signal (the run9 fix): which journal-writing mechanisms this world's own
    # settings.json + apparatus.json declare live -- capability keys on THIS, never on whether
    # anything has been journaled yet (see Capability's docstring for the live specimen).
    wired = _wired_journaling_mechanisms(root)

    # ---- PASS 1: read every raw stream, absolute epoch-ms, no facts emitted yet -------------
    rel = t.rel()
    if has_invocation_col:
        raw_rows = t.rows(f"SELECT id, kind, coalesce(stamp_invocation,''), "
                          f"round(extract(epoch FROM ts)*1000)::bigint FROM {rel} ORDER BY id;")
        row_tuples = [(int(rid), kind, token or None, int(tms)) for rid, kind, token, tms in raw_rows]
    else:
        raw_rows = t.rows(f"SELECT id, kind, round(extract(epoch FROM ts)*1000)::bigint "
                          f"FROM {rel} ORDER BY id;")
        row_tuples = [(int(rid), kind, None, int(tms)) for rid, kind, tms in raw_rows]

    inv_path = root / ".claude" / "logs" / _INVOCATION_JOURNAL
    inv_recs, inv_skip = _read_jsonl(inv_path)
    inv_tuples: list[tuple[str, int]] = []
    for rec in inv_recs:
        token, wc = rec.get("token"), rec.get("wall_clock")
        if not token or not wc:
            inv_skip += 1
            continue
        ms = _parse_ts_ms(str(wc))
        if ms is None:
            inv_skip += 1
            continue
        inv_tuples.append((str(token), ms))

    te_tuples: list[tuple[str, int]] = []
    any_te_file = False
    for fname, kind in _TOOL_EVENT_JOURNALS.items():
        path = root / ".claude" / "logs" / fname
        recs, skip = _read_jsonl(path)
        if path.is_file():
            any_te_file = True
        exp.skipped_lines[fname] = skip
        for rec in recs:
            ts_raw = rec.get("ts")
            if not ts_raw:
                continue
            ms = _parse_ts_ms(str(ts_raw))
            if ms is None:
                exp.skipped_lines[fname] = exp.skipped_lines.get(fname, 0) + 1
                continue
            te_tuples.append((kind, ms))

    # ---- THE ANCHOR: the minimum absolute epoch-ms across every stream in this export --------
    all_abs = ([tms for _, _, _, tms in row_tuples] + [ms for _, ms in inv_tuples]
              + [ms for _, ms in te_tuples])
    exp.anchor_ms = min(all_abs) if all_abs else 0

    # ---- PASS 2: emit facts, T relative to the anchor ----------------------------------------
    n_tok, n_untok = 0, 0
    for rid, kind, token, tms in row_tuples:
        rel_t = tms - exp.anchor_ms
        if token:
            exp.facts.append(f"row_tokened({rid},{quote_term(token)},{quote_term(kind)},{rel_t}).")
            n_tok += 1
        else:
            exp.facts.append(f"row_untokened({rid},{quote_term(kind)},{rel_t}).")
            n_untok += 1
    exp.counts["row_tokened"] = n_tok
    exp.counts["row_untokened"] = n_untok
    # NAMED CONSISTENTLY WITH EVERY OTHER CAPABILITY HERE (found live, in this module's own
    # first end-to-end shim test): produced=True means "the capability is present", uniformly --
    # an earlier draft named this family `pre_token_era` with produced=(NOT has_invocation_col),
    # which meant produced=True signaled the ABSENCE of s23 while every sibling capability's
    # produced=True signals PRESENCE. That polarity inversion fed straight into
    # engine/contemp_audit.py's "missing/excluded" refusal list (`[c.family for c in ... if not
    # c.produced]`), which would then list `pre_token_era` as "missing" on an s23-CAPABLE
    # schema -- a wrong, confusing claim in the exact message the binding constraints require to
    # be honest. `s23_capable` restores one polarity across the whole manifest.
    exp.capabilities.append(Capability(
        "s23_capable", produced=has_invocation_col, capable=has_invocation_col,
        reason="stamp_invocation column present (s23-era schema)" if has_invocation_col
        else "no stamp_invocation column on this schema (predates s23) -- every row is "
             "row_untokened by construction"))

    for token, ms in inv_tuples:
        exp.facts.append(f"invocation({quote_term(token)},{ms - exp.anchor_ms}).")
    exp.counts["invocation"] = len(inv_tuples)
    exp.skipped_lines[_INVOCATION_JOURNAL] = inv_skip
    inv_wired = "stamp_intercept" in wired
    if inv_tuples:
        inv_reason = f"{len(inv_tuples)} invocation record(s) read from {inv_path}"
    elif inv_wired:
        inv_reason = (f"stamp_intercept is WIRED in this world's settings.json (mode not off) "
                      f"but {inv_path} carries no records yet -- capable, zero invocations so "
                      f"far; not an unwired era")
    else:
        inv_reason = (f"no usable invocation records at {inv_path} AND stamp_intercept is not "
                      f"wired in this world's settings.json -- hooks off/unwired, or a genuinely "
                      f"pre-journal era (design memo: 'must report that absence loudly, "
                      f"UNJOURNALED ERA, never as no findings')")
    exp.capabilities.append(Capability(
        "invocation_journal", produced=len(inv_tuples) > 0,
        capable=len(inv_tuples) > 0 or inv_wired, reason=inv_reason))

    for kind, ms in te_tuples:
        exp.facts.append(f"tool_event({kind},{ms - exp.anchor_ms}).")
    exp.counts["tool_event"] = len(te_tuples)
    te_wired = sorted(wired & _TOOL_EVENT_MECHANISMS)
    if te_tuples:
        te_reason = (f"{len(te_tuples)} tool-activity marker(s) read across "
                     f"{sorted(_TOOL_EVENT_JOURNALS)}")
    elif te_wired:
        te_reason = (f"observer mechanism(s) {te_wired} are WIRED in this world's settings.json "
                     f"(mode not off) but no journal-worthy event has occurred yet -- capable, "
                     f"zero events so far; not an unwired era (the run9 false-refusal specimen, "
                     f"2026-07-11)")
    elif any_te_file:
        te_reason = ("tool-activity journal file(s) present but empty, and no observer mechanism "
                     "is wired in this world's settings.json -- residue of an earlier wiring?")
    else:
        te_reason = ("no tool-activity journal files under this world's .claude/logs/ AND no "
                     "observer mechanism wired in its settings.json -- observers off/unwired, "
                     "or a pre-journal era")
    exp.capabilities.append(Capability(
        "tool_event", produced=len(te_tuples) > 0,
        capable=len(te_tuples) > 0 or bool(te_wired), reason=te_reason))

    return exp


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2:
        print("usage: contemp_edb.py <target-name> <world-root-dir>", file=sys.stderr)
        return 2
    exp = export(args[0], Path(args[1]))
    print(exp.edb_text())
    print(f"% counts: {exp.counts}")
    print(f"% edb_sha256: {exp.edb_hash()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
