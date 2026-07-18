#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T14:40:08Z
#   last-change: 2026-07-14T01:09:47Z
#   contributors: e4410ef6/main, a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""contemp_edb -- the EDB builder for Part 2 of vestigial_documentation/design/ORCH-CONTEMPORANEITY-AUDIT.md (the
correlation verb; BACKLOG "Contemporaneity indictment", 2026-07-11). Exports the typed EDB
`engine/lp/contemporaneity.lp` reasons over, from a WORLD (a project directory carrying the
ledger's deployment.json plus its `.claude/logs/*.jsonl` hook journals) -- the fact-mining-side
analog `engine/ledger_edb.py` is for `ledger_tnow.lp`, mirrored here for the same capability-
manifest discipline (I12: a not-produced family is a DECLARED EXCLUSION with its reason,
never silent -- the F49 vacuous-pass class ADR-0000/ADR-0015 forbid).

THREE INPUT STREAMS, ONE WORLD (a fourth family, `row_declared/2`, rides the SAME ledger stream
as #1 -- see "DECLARED EVENT TIME" below):
  1. the LEDGER (Postgres, via engine/ledger_edb.Target/resolve) -- row_tokened/row_untokened,
     and (s24-era schemas only) row_declared.
  2. `<root>/.claude/logs/invocations.jsonl` (hooks/stamp_intercept.py, s23-era) -- invocation/2.
  3. the three hook-journaled tool-activity logs already on disk for OTHER purposes
     (mutation_observer.journal.jsonl, change_gate.journal.jsonl,
     delegation_observer.journal.jsonl) -- tool_event/2, re-purposed as the design memo's Part 2
     directive names them ("the hook-journaled tool activity that already exists").

DECLARED EVENT TIME (design/MAINT-LATE-ENTRY-AND-INTAKE-SEMANTICS.md Proposal 2; kernel/lineage/
s24-declared-event-time.sql, this same commission). A row may optionally carry
`event_declared_ts` (`led --event-time <iso-ts> ...`) -- the writer's own claim of WHEN the
recorded event occurred, distinct from `ts` (INSERT time). CAPABILITY-GATED exactly like
`stamp_invocation` (s23): `has_col("event_declared_ts")` determines whether `row_declared/2`
facts are emitted at all. A pre-s24 world emits NONE -- never guessed, never backfilled -- so
`engine/lp/contemporaneity.lp`'s LATE_DECLARED verdict member can never fire there, and the
identical-gap-UNDECLARED BACKFILL_SUSPECT path is unchanged (the wiredness-not-corpus-emptiness
discipline, this module's own Capability idiom, applied one delta later). UNAUTHENTICATED, named
plainly (s24's own header carries the same disclosure): a writer can declare anything; this
module reads the claim as-is and lets the ASP layer's threshold decide whether it counts as a
genuine late entry -- it neither verifies nor doubts the declaration itself.

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

ENFORCEMENT ADDENDUM, 2026-07-12 (dated append, this note extends the paragraph above rather than
rewriting it -- BACKLOG "a second latent 32-bit clingo wraparound", found live authoring
engine/contemp_differential.py's own seen-red fixture on the SAME commission that shipped that
module). The paragraph above was, until this addendum, an ANALYSIS, not a GUARANTEE: "even a full
week is ~6e8, safely under the 2^31 ceiling" is true only while the audited window actually stays
narrow, and nothing upstream of it enforced that -- `export()` reads the whole ledger table
unconditionally (PASS 1, `SELECT ... FROM {rel} ORDER BY id` below, no time filter), so a real
world whose ledger spans more than `SAFE_32BIT_MS` (~24.8 days) -- or a fixture that accidentally
mixes widely-separated timestamps -- silently wraps the RELATIVE delta this fix exists to protect,
the identical hazard class this module already documents for the absolute-value case, now shown to
recur one layer down. `engine/contemp_differential.py` shipped a defensive QUARANTINE guard for
its own (opt-in, `--differential`) call path, but the DEFAULT `./audit` path
(`engine/contemp_audit.py::run_audit`, which calls `export()` directly) had no protection at all.
THE FIX, AT THE SOURCE (ADR-0000 Rule 2(a): the class is "a caller of `export()` receives facts
whose T values may already be silently wrapped," and the type that forecloses it is a
construction-time refusal inside `export()` itself, the one place every caller -- differential AND
plain `./audit` alike -- necessarily passes through): `export()` now computes the export's full
relative SPAN (`max(all_abs) - anchor_ms`) immediately after the anchor itself is known, BEFORE
pass 2 ever emits a fact, and raises `UnsafeWindowError` (typed, naming the exact span and the
bound) rather than emitting a single fact once that span would exceed `SAFE_32BIT_MS`. This is the
"enforce-or-refuse" disposition, not "per-window anchoring": the audited window is not narrowed or
re-split here (a real re-windowing of the audit's semantics -- what does "the audit" mean for only
part of a ledger's history? -- is a larger, more invasive design than this fix's remit), the export
simply refuses loudly, by construction, the moment its own anchor-relative encoding would no longer
be safe, exactly as this module's docstring already promises for the absolute-value case one
paragraph up. `engine/contemp_differential.py`'s own `_max_abs_relative_ms` regex guard on the
formatted EDB text is UNCHANGED and stays as belt-and-braces (a second, independent, text-level
check) -- it is now expected to never actually fire in practice, since `export()` itself refuses
first, but it costs nothing to keep as a second line of defense against a future regression in this
very check. `SAFE_32BIT_MS` is defined ONCE, here (this module owns the anchor-relative encoding,
so it is the natural single home per ADR-0012 P1); `contemp_differential.py` imports it rather than
carrying its own copy of the literal, closing the two-independently-typed-copies-can-drift risk
ADR-0000's Specimen 1 (`DECOMP_ANCHOR=0.0941` vs `0.094`) already names as the exact failure this
kind of duplication invites.

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

PART 3 EXTENSION, 2026-07-12 (design/ORCH-CONTEMPORANEITY-PART3-SPEC.md §4, "the EDB -- reused
families and named extensions"; dated append, does not rewrite the Part 2 paragraphs above).
E1-E9 land HERE, in `export()` itself, per the spec's own ONE-ANCHOR RULE (§4, binding): "these
families are added to `contemp_edb.export()` itself -- NOT a sibling module with its own export.
Two exports would mean two anchors, and facts on different anchors compared in one program is
the silent-wraparound hazard class the module's docstring documents, one level up." Every new
absolute-ms value below (E3's stop-event ts, E4's fine-grained dispatch/return ts, E5's
completion ts, E6's verify-commission ts) is folded into the SAME `all_abs` list PASS 1 already
builds, BEFORE the anchor and the `UnsafeWindowError` span guard are computed -- so the
enforcement addendum above protects every Part 3 fact exactly as it protects every Part 2 fact,
by construction, not by a second copy of the check.
  E1 work_claimed(Slug,RowId) / work_opened(Slug,RowId) / work_closed(Slug,Resolution,RowId) /
     work_witness_present(RowId) / work_depends(Dependent,Antecedent,RowId) -- the s22 work-item
     shapes design/ORCH-CONTEMPORANEITY-PART3-SPEC.md §4 lists under "Reused as-is ... same shapes as
     work_items.lp". SPEC-VS-REALITY NOTE, named honestly rather than silently assumed: no live
     Python module actually exported these before this delta (work_items.lp's own docstring
     cites `engine/work_item_scratch.py`, which does not exist as a general exporter -- only
     `kernel/fixtures/s22_work_item_fixture.py`, a TEST fixture generator). Built here instead,
     from the SAME ledger row scan PASS 1 already runs for row_tokened/row_untokened (one extra
     set of SELECT columns, zero extra queries) -- in reach of this commission's own edit, per
     CLAUDE.md's engineering-responsibility corollary, rather than left as a dangling "reused"
     citation to a family nothing produces. work_slug/work_resolution/work_witness/
     work_depends_on are capability-gated on `has_col("work_slug")` (all five s22 columns land in
     one delta, kernel/lineage/s22-work-item-ledger.sql, so one column's presence implies all).
  E2 row_refs_row(Id,TargetId) / row_regards(Id,TargetId) -- `refs` (free text, parsed for the
     preamble's own `row:<id>` convention via `_REFS_ROW_RE`; a non-empty `refs` value with NO
     parseable `row:<id>` token emits `row_refs_present(Id)` with no matching `row_refs_row/2` --
     the EDB-level signal `preamble_ordering.lp` turns into UNDECIDABLE(refs_unparsed)) and
     `regards` (typed bigint FK, direct column read, never parsed). Both capability-gated on
     their own column's presence (pre-s15 schemas carry neither).
  E3 stop_event(Outcome,T) -- `.claude/logs/stop_clean_exit.journal.jsonl`
     (hooks/stop_clean_exit.py's own `_journal()`): the closed `outcome` vocabulary that hook
     itself writes (`clean_allow`, `observed_would_block`, `breaker_fail_open`, `blocked`),
     `ts` UTC-Z milliseconds -- read with the SAME `_parse_ts_ms` this module already uses.
  E4 delegation_dispatch(T) / delegation_return(T) -- a FINER, independent read of
     `.claude/logs/delegation_observer.journal.jsonl`, the SAME file `tool_event(delegation,T)`
     already ingests whole (coarsely) -- a dispatch line carries no `"kind"` key at all
     (hooks/pretooluse_delegation_observer.py's own dispatch-leg `_journal()` call); a return
     line carries `"kind":"return"` (that same module's return-leg call). Reading BOTH shapes
     out of the one file, distinctly, is exactly what F9 (ob_ledger_before_delegation) needs and
     `tool_event/2`'s coarse Kind="delegation" bucket cannot supply on its own.
  E5 invocation_completed(Token,T) -- `.claude/logs/bash_completions.jsonl`
     (hooks/posttooluse_bash_completion.py). CORRECTED 2026-07-14
     (vestigial_documentation/design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md sec-4/6.1/6.3): this hook no longer stores a
     computed `token`/`pairing` verdict (that FIFO-by-content-hash pairing was dead at birth --
     the paired hook rewrites every Bash command between the dispatch hash and the completion
     hash, so the two never agreed; 0 of 2093 completions ever paired in this deployment's
     history). Pairing is now a READ-TIME JOIN, done HERE in `export()`: a completion's own
     `tool_use_id` (the harness-assigned identity, present on both the PreToolUse and PostToolUse
     legs of one tool call) is looked up against a `tool_use_id -> token` map built from the
     dispatch journal (`invocations.jsonl`, which already carries `tool_use_id` per dispatch line
     -- `hooks/stamp_intercept.py`). A completion with no `tool_use_id`, or one that joins to no
     known dispatch, contributes nothing to this family, honestly -- never guessed from FIFO
     proximity or a content hash.
  E6 verify_commission_event(Verdict,T) -- `.claude/logs/verify_commission.jsonl`
     (bootstrap/templates/verify-commission.tmpl, THIS SAME COMMISSION's own addition to that
     live verb -- see its own docstring's EVENT JOURNAL section). Verdict is one of the closed
     FIVE that verb ever journals (VERIFIED, UNSIGNED, FORGED-OR-CORRUPT, GPG-UNAVAILABLE,
     NO-COMMITTED-KEY). CAPABILITY, NAMED HONESTLY: since verify-commission.tmpl executes IN
     PLACE out of the live autoharn checkout (like every other verb), there is no per-world
     "template vintage" to detect -- the only observable signal is whether this world's own
     `.claude/logs/verify_commission.jsonl` FILE exists at all. Its absence means either "this
     verb was never invoked on this world" or "it predates this delta having landed in the
     checkout" -- indistinguishable from artifacts alone, so BOTH read as capability-absent
     (`no_verify_journal`), never guessed apart. A closed, dead world (a settled run whose
     session has ended -- runs are linear, dust, read-only) can never retroactively produce this
     file; that is the honest, permanent shape of its own F2 verdict, not a defect in this EDB.
  E7 row_actor(Id,ActorId) / countersign_obliged(ActorId) -- `actor` (bigint FK to
     `kern.principal`, direct column read, capability-gated on `has_col("actor")`) and
     `countersign_obligation.obliges_actor` (a SEPARATE small table in the SAME ledger schema,
     capability-gated on `has_relation(f"{schema}.countersign_obligation")`) -- needed only for
     F11's review-gap arm and F7's refined form; both families' coarse forms run without it.
  E8/E9 are FACTS FILES, not EDB extensions -- `engine/preamble_obligations.lp` (E8) and
     `stop_disposition_window_ms/1` appended to `engine/contemp_thresholds.lp` (E9) -- loaded as
     PROGRAM text beside `engine/lp/preamble_ordering.lp`, never emitted by this module.
  COMMISSION-KIND CAPABILITY (F1/F2/F3's `pre_s25` reason): whether THIS schema's own
  `ledger_kind_check` CHECK constraint admits `'commission'` as a legal `kind` value -- read
  LIVE via `pg_get_constraintdef` against the schema's own constraint (mirrors
  `bootstrap/templates/led.tmpl`'s own live-queried refusal-teaching convention, never a
  hand-copied kind list that could drift from kernel/lineage/s25-commission-kind.sql's own text).

Read-only. Lazy imports banned (top-of-file only)."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from clingo_run import quote_term
from ledger_edb import Target, resolve

# The preamble's own `--refs row:<id>` convention (E2; CLAUDE.md.tmpl points 1/3/10) -- a
# case-sensitive literal match, mirroring every other `row:<id>` citation site in this project
# (led.tmpl's own `--refs` parser). Findall (not match) -- a `refs` value MAY cite more than one
# antecedent row; every parsed target becomes its own `row_refs_row/2` fact.
_REFS_ROW_RE = re.compile(r"row:(\d+)")

# The three existing hook journals this module re-purposes as the tool_event/2 stream (design
# memo Part 2 directive: "tool_event(Kind, T) (from the hook journals -- change-gate,
# mutation-observer marker, delegation journal)"). Filename -> the Kind atom it contributes.
_TOOL_EVENT_JOURNALS: dict[str, str] = {
    "mutation_observer.journal.jsonl": "mutation",
    "change_gate.journal.jsonl": "change_gate",
    "delegation_observer.journal.jsonl": "delegation",
}
_INVOCATION_JOURNAL = "invocations.jsonl"

# PART 3 (E3/E4/E5) journal filenames -- see this module's docstring "PART 3 EXTENSION" section.
_STOP_JOURNAL = "stop_clean_exit.journal.jsonl"
_DELEGATION_JOURNAL = "delegation_observer.journal.jsonl"  # SAME file as _TOOL_EVENT_JOURNALS'
                                                            # own entry -- E4 re-reads it finely.
_BASH_COMPLETIONS_JOURNAL = "bash_completions.jsonl"
_VERIFY_COMMISSION_JOURNAL = "verify_commission.jsonl"
# E3's closed outcome vocabulary (hooks/stop_clean_exit.py's own `_journal()` call sites) --
# named here so a malformed/future outcome string is distinguishable from these four, not
# silently accepted as a fifth (this module counts it but does not refuse -- the closed-
# vocabulary CHECK belongs to preamble_ordering.lp's own `#show`n atoms, not this EDB layer).
_STOP_OUTCOMES = frozenset({"clean_allow", "observed_would_block", "breaker_fail_open", "blocked"})
# E6's closed verdict vocabulary (bootstrap/templates/verify-commission.tmpl's own
# `_journal_verify_commission` call sites) -- named for the same reason.
_VERIFY_COMMISSION_VERDICTS = frozenset(
    {"VERIFIED", "UNSIGNED", "FORGED-OR-CORRUPT", "GPG-UNAVAILABLE", "NO-COMMITTED-KEY"})

# The journal-writing mechanisms and the hook script whose presence in a world's
# .claude/settings.json means that mechanism is WIRED (the capability signal the run9 fix
# keys on -- see Capability's docstring). apparatus.json key -> hook script basename.
# stamp_intercept writes invocations.jsonl; the rest write the tool-event / Part 3 journals.
_JOURNALING_MECHANISMS: dict[str, str] = {
    "stamp_intercept": "stamp_intercept.py",
    "change_gate": "pretooluse_change_gate.py",
    "mutation_observer": "posttooluse_mutation_observer.py",
    "delegation_observer": "pretooluse_delegation_observer.py",
    "clean_exit": "stop_clean_exit.py",              # E3 (apparatus.json's own key: "clean_exit")
    "bash_completion": "posttooluse_bash_completion.py",  # E5
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


# clingo/clasp's own signed 32-bit integer ceiling (this module's docstring, "TIMESTAMP UNITS").
# The single home of this literal (ADR-0012 P1) -- engine/contemp_differential.py imports it
# rather than carrying its own copy (see this module's docstring, "ENFORCEMENT ADDENDUM").
SAFE_32BIT_MS = 2**31 - 1


class UnsafeWindowError(RuntimeError):
    """Raised by export() when the audited window's own relative span (max(all_abs) - anchor_ms)
    would exceed SAFE_32BIT_MS -- see this module's docstring, "ENFORCEMENT ADDENDUM, 2026-07-12".
    Raised BEFORE any fact is emitted, so a caller never receives a fact whose T value may already
    be silently wrapped. The honest typed refusal for this hazard, exactly as CapabilityError is
    for a missing fact family: never a guessed or corrupted verdict."""


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


def dispatch_token_by_tool_use_id(inv_recs: list[dict]) -> dict[str, str]:
    """The E5 join's LEFT side (vestigial_documentation/design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md sec-4/6.1/6.3): a
    tool_use_id -> token map built from `hooks/stamp_intercept.py`'s own dispatch records
    (`invocations.jsonl`). A dispatch line contributes only when it carries BOTH fields --
    tool_use_id is the harness-assigned identity, token is the per-invocation contemporaneity
    UUID this project's own kernel column captures. Pure function of the records, no I/O, no
    ledger -- factored out so `export()` and this module's own fixtures call the SAME join code
    (ADR-0011's "the counterparty rule for pairing fixtures", RCA §6.4/M1), never a
    fixture-side reimplementation that could silently drift from what `export()` actually does."""
    out: dict[str, str] = {}
    for rec in inv_recs:
        tuid, token = rec.get("tool_use_id"), rec.get("token")
        if tuid and token:
            out[str(tuid)] = str(token)
    return out


def join_bash_completions(
    completions_recs: list[dict], token_by_tool_use_id: dict[str, str]
) -> tuple[list[tuple[str, int]], int]:
    """The E5 join's RIGHT side: for each completion record carrying a `tool_use_id` that
    resolves in `token_by_tool_use_id`, yield (token, completion_ts_ms). A completion with no
    `tool_use_id`, or one that joins to no known dispatch, contributes nothing -- honestly
    skipped, never guessed. Returns (joined tuples, count of records with a resolvable
    tool_use_id whose own `ts` failed to parse -- the caller adds this to its skip tally; a
    record with no `tool_use_id` at all, or one that fails to join, is NOT counted as skipped --
    it is the honest, expected shape of an unpaired or old-era completion line, not malformed
    input). Pure function, no I/O -- see `dispatch_token_by_tool_use_id`'s docstring for why."""
    joined: list[tuple[str, int]] = []
    unparseable_ts = 0
    for rec in completions_recs:
        tool_use_id, ts_raw = rec.get("tool_use_id"), rec.get("ts")
        if not tool_use_id or not ts_raw:
            continue
        token = token_by_tool_use_id.get(str(tool_use_id))
        if not token:
            continue
        ms = _parse_ts_ms(str(ts_raw))
        if ms is None:
            unparseable_ts += 1
            continue
        joined.append((token, ms))
    return joined, unparseable_ts


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

    # ---- capability 2: event_declared_ts column (s24) -- see module docstring "DECLARED EVENT
    # TIME". `capable` == `produced` here (there is no "wired but nothing declared yet" axis for
    # a plain writer-supplied column the way there is for a hook-journaled mechanism): the column
    # either exists on this schema or it does not, and row_declared facts are emitted 1:1 with
    # non-NULL values when it does. A pre-s24 schema is EXCLUDED (not EMPTY-capable-but-zero),
    # named honestly rather than silently read as "zero late entries this session".
    has_declared_col = t.has_col("event_declared_ts")
    exp.capabilities.append(Capability(
        "event_declared_ts_column", produced=has_declared_col, capable=has_declared_col,
        reason="event_declared_ts column present (s24-era schema) -- late-entry declarations, "
               "if any, are readable" if has_declared_col
        else "no event_declared_ts column on this schema (predates s24) -- LATE_DECLARED can "
             "never fire here; the identical-gap-undeclared BACKFILL_SUSPECT path is unaffected"))

    # ---- PART 3 (design/ORCH-CONTEMPORANEITY-PART3-SPEC.md §4) column/relation capabilities --------
    # each becomes a `capable(Family)` EDB marker fact below (PASS 2) so preamble_ordering.lp --
    # which cannot itself query Postgres -- can derive the SAME typed UNDECIDABLE reasons
    # (`pre_s25`, `pre_s22`, `capability_absent`) this module already names in prose.
    has_work_cols = t.has_col("work_slug")          # E1 (s22-era schema; all five columns land
                                                      # together, one column's presence implies all)
    has_refs_col = t.has_col("refs")                 # E2
    has_regards_col = t.has_col("regards")            # E2
    has_actor_col = t.has_col("actor")                # E7
    has_countersign_tbl = t.has_relation(f"{t.schema}.countersign_obligation")  # E7
    # commission-kind capability: LIVE-queried against this schema's OWN ledger_kind_check CHECK
    # constraint (mirrors led.tmpl's own live refusal-teaching query -- never a hand-copied kind
    # list that could drift from kernel/lineage/s25-commission-kind.sql's own text).
    kind_check_def = t.scalar(
        f"SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname='ledger_kind_check' "
        f"AND conrelid = '{t.schema}.ledger'::regclass;")
    has_commission_kind = "commission" in kind_check_def

    # ---- the WIRING signal (the run9 fix): which journal-writing mechanisms this world's own
    # settings.json + apparatus.json declare live -- capability keys on THIS, never on whether
    # anything has been journaled yet (see Capability's docstring for the live specimen).
    wired = _wired_journaling_mechanisms(root)

    # ---- PASS 1: read every raw stream, absolute epoch-ms, no facts emitted yet -------------
    rel = t.rel()
    cols = ["id", "kind"]
    cols.append("coalesce(stamp_invocation,'')" if has_invocation_col else "NULL")
    cols.append("round(extract(epoch FROM ts)*1000)::bigint")
    cols.append("round(extract(epoch FROM event_declared_ts)*1000)::bigint" if has_declared_col
                else "NULL")
    cols.append("coalesce(work_slug,'')" if has_work_cols else "NULL")
    cols.append("coalesce(work_resolution,'')" if has_work_cols else "NULL")
    cols.append("(work_witness IS NOT NULL AND work_witness <> '')" if has_work_cols else "NULL")
    cols.append("coalesce(work_depends_on,'')" if has_work_cols else "NULL")
    cols.append("coalesce(refs,'')" if has_refs_col else "NULL")
    cols.append("regards" if has_regards_col else "NULL")
    cols.append("actor" if has_actor_col else "NULL")
    raw_rows = t.rows(f"SELECT {', '.join(cols)} FROM {rel} ORDER BY id;")
    row_tuples: list[tuple] = []
    for (rid, kind, token, tms, declared_ms, wslug, wres, wwit, wdep, refs, regards,
         actor) in raw_rows:
        row_tuples.append((
            int(rid), kind, token or None, int(tms),
            int(declared_ms) if declared_ms not in (None, "") else None,
            wslug or None, wres or None, (str(wwit).lower() == "t") if wwit not in (None, "") else False,
            wdep or None, refs or None,
            int(regards) if regards not in (None, "") else None,
            int(actor) if actor not in (None, "") else None))

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

    # tool_use_id -> token map (vestigial_documentation/design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md sec-4/6.3): the SOLE
    # join key E5 below uses to correlate a completion line back to its dispatch token. Built
    # from `inv_recs` directly (not `inv_tuples`, which additionally requires a parseable
    # `wall_clock` -- tool_use_id/token presence is independent of that and must not be dropped
    # by it) via the module-level `dispatch_token_by_tool_use_id()` -- the SAME function this
    # module's own fixtures call (RCA §6.4/M1: no fixture-side reimplementation of this join).
    tool_use_id_to_token = dispatch_token_by_tool_use_id(inv_recs)

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

    # ---- E3: stop_event(Outcome,T) -- hooks/stop_clean_exit.py's own journal -----------------
    stop_path = root / ".claude" / "logs" / _STOP_JOURNAL
    stop_recs, stop_skip = _read_jsonl(stop_path)
    stop_tuples: list[tuple[str, int]] = []
    for rec in stop_recs:
        outcome, ts_raw = rec.get("outcome"), rec.get("ts")
        if not outcome or not ts_raw:
            stop_skip += 1
            continue
        ms = _parse_ts_ms(str(ts_raw))
        if ms is None:
            stop_skip += 1
            continue
        stop_tuples.append((str(outcome), ms))
    exp.skipped_lines[_STOP_JOURNAL] = stop_skip
    stop_wired = "clean_exit" in wired

    # ---- E4: delegation_dispatch(T) / delegation_return(T) -- a FINER, independent re-read of --
    # the SAME file _TOOL_EVENT_JOURNALS already ingests coarsely as tool_event(delegation,T).
    deleg_path = root / ".claude" / "logs" / _DELEGATION_JOURNAL
    deleg_recs, _deleg_skip_already_counted = _read_jsonl(deleg_path)  # skip count already
                                                                        # banked under this same
                                                                        # filename by the te_tuples
                                                                        # loop above -- not doubled
    deleg_dispatch_tuples: list[int] = []
    deleg_return_tuples: list[int] = []
    for rec in deleg_recs:
        ts_raw = rec.get("ts")
        if not ts_raw:
            continue
        ms = _parse_ts_ms(str(ts_raw))
        if ms is None:
            continue
        if rec.get("kind") == "return":
            deleg_return_tuples.append(ms)
        else:
            deleg_dispatch_tuples.append(ms)

    # ---- E5: invocation_completed(Token,T) -- hooks/posttooluse_bash_completion.py's journal ---
    # CORRECTED 2026-07-14 (vestigial_documentation/design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md sec-4/6.1/6.3): the
    # completion journal no longer carries a stored `token`/`pairing` verdict (that computed
    # FIFO-by-hash pairing was dead at birth -- 0 of 2093 completions ever paired in this
    # deployment's history, per the RCA). Pairing is now a READ-TIME JOIN, done via the
    # module-level `join_bash_completions()` -- the SAME function this module's own fixtures call
    # (RCA §6.4/M1). Old-era completion lines (pre-fix, carrying `token`/`pairing` but no
    # `tool_use_id`) contribute nothing here by construction (the join reads only `tool_use_id`),
    # exactly as they contributed nothing under the old pairing=="token" filter (that mechanism
    # never once fired) -- no regression, no silent revival of stale data.
    completions_path = root / ".claude" / "logs" / _BASH_COMPLETIONS_JOURNAL
    completions_recs, completions_skip = _read_jsonl(completions_path)
    completed_tuples, completions_unparseable_ts = join_bash_completions(
        completions_recs, tool_use_id_to_token)
    completions_skip += completions_unparseable_ts
    exp.skipped_lines[_BASH_COMPLETIONS_JOURNAL] = completions_skip
    completions_wired = "bash_completion" in wired

    # ---- E6: verify_commission_event(Verdict,T) -- bootstrap/templates/verify-commission.tmpl's
    # own journal (this same commission's addition to that live verb).
    verify_path = root / ".claude" / "logs" / _VERIFY_COMMISSION_JOURNAL
    verify_recs, verify_skip = _read_jsonl(verify_path)
    verify_tuples: list[tuple[str, int]] = []
    for rec in verify_recs:
        verdict, ts_raw = rec.get("verdict"), rec.get("ts")
        if not verdict or not ts_raw:
            verify_skip += 1
            continue
        ms = _parse_ts_ms(str(ts_raw))
        if ms is None:
            verify_skip += 1
            continue
        verify_tuples.append((str(verdict), ms))
    exp.skipped_lines[_VERIFY_COMMISSION_JOURNAL] = verify_skip

    # ---- THE ANCHOR: the minimum absolute epoch-ms across EVERY stream in this export, Part 2
    # AND Part 3 alike (§4's binding one-anchor rule: "the anchor minimum must be taken across
    # ALL families including E3-E6") -------------------------------------------------------------
    all_abs = ([r[3] for r in row_tuples] + [ms for _, ms in inv_tuples]
              + [ms for _, ms in te_tuples] + [r[4] for r in row_tuples if r[4] is not None]
              + [ms for _, ms in stop_tuples] + deleg_dispatch_tuples + deleg_return_tuples
              + [ms for _, ms in completed_tuples] + [ms for _, ms in verify_tuples])
    exp.anchor_ms = min(all_abs) if all_abs else 0

    # ---- THE ENFORCED BOUND (this module's docstring, "ENFORCEMENT ADDENDUM, 2026-07-12"): the
    # widest relative delta this export WOULD emit, checked BEFORE pass 2 emits a single fact. A
    # span this wide means at least one T below would exceed clingo/clasp's signed 32-bit ceiling
    # and silently wrap -- refuse loudly here, at construction, rather than hand every caller
    # (the default ./audit path included) a fact that may already be corrupted.
    span_ms = (max(all_abs) - exp.anchor_ms) if all_abs else 0
    if span_ms > SAFE_32BIT_MS:
        raise UnsafeWindowError(
            f"world '{root}' (target '{target_name}'): audited window spans {span_ms}ms "
            f"(anchor {exp.anchor_ms}ms epoch) -- EXCEEDS clingo/clasp's signed 32-bit ceiling "
            f"({SAFE_32BIT_MS}ms, ~24.8 days). engine/contemp_edb.py's anchor-relative encoding "
            f"is only safe within that bound; emitting facts for a wider window would silently "
            f"wrap at least one T value inside clingo, with no error from clingo itself. "
            f"Refusing loudly instead of emitting a possibly-corrupted EDB (ADR-0000 Rule 2(a); "
            f"ADR-0002). No windowed/narrowed export exists yet -- narrow the audited history at "
            f"the source (e.g. a fresh world, or archiving old ledger rows) to bring the span "
            f"back under the bound, or see this module's docstring 'ENFORCEMENT ADDENDUM' and "
            f"BACKLOG.md's 'a second latent 32-bit clingo wraparound' for the full account.")

    # ---- PASS 2: emit facts, T relative to the anchor ----------------------------------------
    n_tok, n_untok, n_declared = 0, 0, 0
    n_wopen, n_wclaim, n_wclose, n_wwit, n_wdep = 0, 0, 0, 0, 0
    n_refs_row, n_refs_present, n_regards, n_actor = 0, 0, 0, 0
    for (rid, kind, token, tms, declared_ms, wslug, wres, wwit, wdep, refs, regards,
         actor) in row_tuples:
        rel_t = tms - exp.anchor_ms
        if token:
            exp.facts.append(f"row_tokened({rid},{quote_term(token)},{quote_term(kind)},{rel_t}).")
            n_tok += 1
        else:
            exp.facts.append(f"row_untokened({rid},{quote_term(kind)},{rel_t}).")
            n_untok += 1
        if declared_ms is not None:
            exp.facts.append(f"row_declared({rid},{declared_ms - exp.anchor_ms}).")
            n_declared += 1
        # ---- E1: s22 work-item shapes, from the SAME row scan (see docstring's SPEC-VS-REALITY
        # NOTE -- no other exporter produces these today) --------------------------------------
        if kind == "work_opened" and wslug:
            exp.facts.append(f"work_opened({quote_term(wslug)},{rid}).")
            n_wopen += 1
        elif kind == "work_claimed" and wslug:
            exp.facts.append(f"work_claimed({quote_term(wslug)},{rid}).")
            n_wclaim += 1
        elif kind == "work_closed" and wslug:
            exp.facts.append(f"work_closed({quote_term(wslug)},{quote_term(wres or '')},{rid}).")
            n_wclose += 1
            if wwit:
                exp.facts.append(f"work_witness_present({rid}).")
                n_wwit += 1
        elif kind == "work_depends_on" and wslug and wdep:
            exp.facts.append(f"work_depends({quote_term(wslug)},{quote_term(wdep)},{rid}).")
            n_wdep += 1
        # ---- E2: refs (parsed row:<id> convention) + regards (typed FK) ----------------------
        if refs:
            targets = _REFS_ROW_RE.findall(refs)
            if targets:
                for tgt in targets:
                    exp.facts.append(f"row_refs_row({rid},{int(tgt)}).")
                    n_refs_row += 1
            else:
                # a non-empty refs value with NO parseable row:<id> token -- the EDB-level signal
                # preamble_ordering.lp turns into UNDECIDABLE(refs_unparsed) for this row's
                # instance, never a silent skip.
                exp.facts.append(f"row_refs_present({rid}).")
                n_refs_present += 1
        if regards is not None:
            exp.facts.append(f"row_regards({rid},{regards}).")
            n_regards += 1
        # ---- E7: actor (needed only for F11's review-gap arm + F7's refined form) -------------
        if actor is not None:
            exp.facts.append(f"row_actor({rid},{actor}).")
            n_actor += 1
    exp.counts["row_tokened"] = n_tok
    exp.counts["row_untokened"] = n_untok
    exp.counts["row_declared"] = n_declared
    exp.counts["work_opened"] = n_wopen
    exp.counts["work_claimed"] = n_wclaim
    exp.counts["work_closed"] = n_wclose
    exp.counts["work_witness_present"] = n_wwit
    exp.counts["work_depends"] = n_wdep
    exp.counts["row_refs_row"] = n_refs_row
    exp.counts["row_refs_present"] = n_refs_present
    exp.counts["row_regards"] = n_regards
    exp.counts["row_actor"] = n_actor
    exp.capabilities.append(Capability(
        "work_items", produced=has_work_cols, capable=has_work_cols,
        reason="work_slug/work_title/work_depends_on/work_resolution/work_witness columns "
               "present (s22-era schema) -- work_opened/work_claimed/work_closed/work_depends "
               "readable" if has_work_cols
        else "no work_slug column on this schema (predates s22) -- pre_s22: F4-F7's work "
             "vocabulary cannot exist here"))
    exp.capabilities.append(Capability(
        "refs", produced=has_refs_col, capable=has_refs_col,
        reason="refs column present -- row:<id> citations parsed" if has_refs_col
        else "no refs column on this schema (pre-s15) -- capability absent"))
    exp.capabilities.append(Capability(
        "regards", produced=has_regards_col, capable=has_regards_col,
        reason="regards column present -- review attestation targets readable" if has_regards_col
        else "no regards column on this schema (pre-s15) -- capability absent"))
    exp.capabilities.append(Capability(
        "actor", produced=has_actor_col, capable=has_actor_col,
        reason="actor column present -- row_actor/2 readable" if has_actor_col
        else "no actor column on this schema (pre-s15) -- capability absent"))
    exp.capabilities.append(Capability(
        "countersign_obligation", produced=has_countersign_tbl, capable=has_countersign_tbl,
        reason="countersign_obligation table present -- countersign_obliged/1 readable"
        if has_countersign_tbl
        else "no countersign_obligation relation on this schema (pre-s15) -- capability absent"))
    exp.capabilities.append(Capability(
        "commission_kind", produced=has_commission_kind, capable=has_commission_kind,
        reason="'commission' is a legal kind on this schema's own ledger_kind_check "
               "(live-queried, s25-era schema)" if has_commission_kind
        else "'commission' is NOT in this schema's own ledger_kind_check -- pre_s25: F1/F2/F3 "
             "cannot be decided (kernel/lineage/s25-commission-kind.sql not in this world's "
             "birth chain)"))
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

    # ---- E7 (cont.): countersign_obliged/1 -- countersign_obligation.obliges_actor, a SEPARATE
    # small table in the same schema (E7's own query, distinct from the main row scan above) -----
    if has_countersign_tbl:
        for (obliges,) in t.rows(f"SELECT obliges_actor FROM {t.schema}.countersign_obligation;"):
            exp.facts.append(f"countersign_obliged({int(obliges)}).")
        exp.counts["countersign_obliged"] = len(
            [f for f in exp.facts if f.startswith("countersign_obliged(")])

    # ---- E3: stop_event(Outcome,T) -------------------------------------------------------------
    for outcome, ms in stop_tuples:
        exp.facts.append(f"stop_event({quote_term(outcome)},{ms - exp.anchor_ms}).")
    exp.counts["stop_event"] = len(stop_tuples)
    if stop_tuples:
        stop_reason = f"{len(stop_tuples)} stop_event record(s) read from {stop_path}"
    elif stop_wired:
        stop_reason = (f"clean_exit is WIRED in this world's settings.json (mode not off) but "
                       f"{stop_path} carries no records yet -- capable, zero stop events so far "
                       f"(this session has not stopped yet); not an unwired era")
    else:
        stop_reason = (f"no usable stop_event records at {stop_path} AND clean_exit is not "
                       f"wired in this world's settings.json -- hooks off/unwired, or predates "
                       f"hooks/stop_clean_exit.py -- F10/F11's stop-side arms are UNDECIDABLE"
                       f"(no_stop_record) here")
    exp.capabilities.append(Capability(
        "stop_journal", produced=len(stop_tuples) > 0,
        capable=len(stop_tuples) > 0 or stop_wired, reason=stop_reason))

    # ---- E4: delegation_dispatch(T) / delegation_return(T) -- fine read of the SAME file --------
    for ms in deleg_dispatch_tuples:
        exp.facts.append(f"delegation_dispatch({ms - exp.anchor_ms}).")
    for ms in deleg_return_tuples:
        exp.facts.append(f"delegation_return({ms - exp.anchor_ms}).")
    exp.counts["delegation_dispatch"] = len(deleg_dispatch_tuples)
    exp.counts["delegation_return"] = len(deleg_return_tuples)
    deleg_wired = "delegation_observer" in wired
    exp.capabilities.append(Capability(
        "delegation_journal", produced=len(deleg_dispatch_tuples) > 0,
        capable=len(deleg_dispatch_tuples) > 0 or deleg_wired,
        reason=(f"{len(deleg_dispatch_tuples)} dispatch / {len(deleg_return_tuples)} return "
               f"record(s) read from {deleg_path}") if deleg_dispatch_tuples
        else (f"delegation_observer is WIRED (mode not off) but no dispatch recorded yet -- "
             f"capable, zero delegations so far" if deleg_wired
             else f"no usable delegation records AND delegation_observer not wired -- F9's "
                  f"delegation leg is UNDECIDABLE(capability_absent) here")))

    # ---- E5: invocation_completed(Token,T) -------------------------------------------------------
    for token, ms in completed_tuples:
        exp.facts.append(f"invocation_completed({quote_term(token)},{ms - exp.anchor_ms}).")
    exp.counts["invocation_completed"] = len(completed_tuples)
    if completed_tuples:
        completions_reason = (f"{len(completed_tuples)} completion record(s) with a token read "
                              f"from {completions_path}")
    elif completions_wired:
        completions_reason = (f"bash_completion is WIRED (mode not off) but no completion with a "
                              f"token has been journaled yet -- capable, zero so far; the cross-"
                              f"seam upper bound (Hi) is UNDECIDABLE(open_window) per-row until "
                              f"one lands")
    else:
        completions_reason = ("no usable completion records with a token AND bash_completion "
                              "not wired -- every cross-seam 'before'/'after' comparison needing "
                              "the upper bound is UNDECIDABLE(open_window)")
    exp.capabilities.append(Capability(
        "bash_completions_journal", produced=len(completed_tuples) > 0,
        capable=len(completed_tuples) > 0 or completions_wired, reason=completions_reason))

    # ---- E6: verify_commission_event(Verdict,T) --------------------------------------------------
    for verdict, ms in verify_tuples:
        exp.facts.append(f"verify_commission_event({quote_term(verdict)},{ms - exp.anchor_ms}).")
    exp.counts["verify_commission_event"] = len(verify_tuples)
    exp.capabilities.append(Capability(
        "verify_commission_journal", produced=len(verify_tuples) > 0,
        capable=len(verify_tuples) > 0,  # no settings.json toggle exists for a manually-invoked
                                          # verb (see docstring's E6 paragraph) -- file-presence
                                          # IS the only honest capability signal available
        reason=(f"{len(verify_tuples)} verify_commission_event record(s) read from {verify_path}")
        if verify_tuples else
        (f"no {verify_path} on this world -- either ./verify-commission was never invoked here, "
         f"or this world predates the E6 journaling extension landing in the live checkout "
         f"(indistinguishable from artifacts alone, named honestly per this module's own "
         f"docstring) -- F2 is UNDECIDABLE(no_verify_journal) here")))

    # ---- capability/1 marker facts -- the ONLY way preamble_ordering.lp (which cannot itself
    # query Postgres) learns which typed UNDECIDABLE reason (pre_s25 / pre_s22 / capability_absent)
    # applies on this schema (§5's closed reason vocabulary). One marker per Part 3 capability this
    # module discovered above, named consistently with every family's own `produced=True means
    # present` polarity (this module's own "NAMED CONSISTENTLY" comment, applied here too).
    for fam, present in (
        ("work_items", has_work_cols), ("refs", has_refs_col), ("regards", has_regards_col),
        ("actor", has_actor_col), ("countersign_obligation", has_countersign_tbl),
        ("commission_kind", has_commission_kind),
        ("stop_journal", len(stop_tuples) > 0 or stop_wired),
        ("delegation_journal", len(deleg_dispatch_tuples) > 0 or deleg_wired),
        ("bash_completions_journal", len(completed_tuples) > 0 or completions_wired),
        ("verify_commission_journal", len(verify_tuples) > 0),
        # s23_capable itself, so preamble_ordering.lp's own F12 family-level override (pre-token
        # era, other activity on record -> UNDECIDABLE(capability_absent), never silent VACUOUS)
        # has an EDB signal to key on -- mirrors the Capability object of the same name above.
        ("s23_capable", has_invocation_col),
    ):
        if present:
            exp.facts.append(f"capable({fam}).")

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
