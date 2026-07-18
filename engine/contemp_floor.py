#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T22:20:51Z
#   last-change: 2026-07-11T22:20:51Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""contemp_floor -- the SQL FLOOR of the contemporaneity verdicts: producer ONE of the
contemporaneity marriage differential (engine/contemp_differential.py), the deferred half of
vestigial_documentation/design/ORCH-CONTEMPORANEITY-AUDIT.md's Part 2 ("the SQL-floor differential ... is FILED, not built,
this pass"). Computes the SAME judgment predicates as engine/lp/contemporaneity.lp -- burst,
ts_cluster, silence, intake_shape, backfill_suspect, late_declared, the per-row deltas, and the
closed verdict -- in Postgres SQL (window functions + set logic; no recursion needed, unlike
ledger_floor.py's transitive-closure floors), over the SAME two real sources the ASP producer's
own EDB (engine/contemp_edb.py) reads: the live ledger table and this world's `.claude/logs/*`
hook journals. Returns the atoms as clingo-shaped strings so engine/contemp_differential.py can
compare the two producers by set-equality -- the marriage discipline's own bar
(engine/ledger_differential.py's DerivationRecord / AGREE convention, matched exactly there, not
re-invented here).

RE-DERIVES FROM SOURCE, DOES NOT CONSUME contemp_edb.py's STAGED EDB (the honest choice, stated
per this commission's own mandate: "decide honestly whether the SQL floor reads the same staged
fact files or re-derives from source, and document why"). engine/ledger_floor.py's own precedent
settles this: the SQL floor there reads the LIVE DB rows directly, never ledger_edb.py's exported
EDB text, because consuming the OTHER producer's own staging code would let a bug in that staging
layer (a mis-parsed timestamp, a mis-read column) show up IDENTICALLY in both producers -- the two
sides would silently agree on a wrong answer, defeating the entire reason a differential exists
("independence of DERIVATION is the point, shared INPUT is the design" -- this commission's own
framing). Concretely here: this module (a) queries `ledger` directly via SQL, a SEPARATE query
text from contemp_edb.py's pass-1 SELECT, not a call into contemp_edb.export(); and (b) re-reads
and re-parses the raw `.claude/logs/*.jsonl` journal bytes with ITS OWN small parser
(`_floor_read_jsonl` / `_floor_parse_ts_ms` below), NOT contemp_edb.py's `_read_jsonl` /
`_parse_ts_ms` -- the same "a trivial helper is not the logic under test, so two independent
copies cost nothing and keep the producers genuinely separate" posture engine/ledger_floor.py's
own `_wi_quote` docstring already states for its own local SQL-quoting helper (this module keeps
one too, `_atom_quote`, for the identical reason). The SHARED input is the real bytes on disk (the
ledger table's live rows; the journal files' raw JSON lines) -- exactly as ledger_floor.py's own
"the only thing shared is the EDB source (one ledger, read-only)" docstring already states for its
domain, extended here to a second real source (the journals) this domain also has.

THRESHOLDS: read from the SAME text file the ASP side loads as a program
(engine/contemp_thresholds.lp) -- ONE textual source of truth (ADR-0012 P1), parsed here as DATA
(three integers pulled by regex) rather than loaded as a program. Never a hand-copied duplicate
literal that could silently drift from the ASP side's own measured value.

DENOMINATION (the load-bearing difference from the ASP producer, named because
engine/contemp_edb.py's own docstring names the reason): Postgres `bigint` has no 32-bit ceiling,
so THIS module emits every timestamp as an ABSOLUTE epoch-millisecond integer, natively -- it
never needs contemp_edb.py's anchor-relative encoding (that encoding exists ONLY to dodge
clingo/clasp's 32-bit signed-int wraparound, a clingo-side hazard with no SQL-side analog). The
two producers' emitted denominations therefore DIFFER on the three predicates that carry an
absolute timestamp argument (`token_min_ts/2`, `token_max_ts/2`, `silence/2`); the differences on
`token_row_count/2` (a count), `row_delta_ms/2` and `preceding_activity_age_ms/2` (both already
DIFFERENCES between same-anchor values, so anchor-invariant by construction), and every
Id/Tok-only predicate are non-issues. engine/contemp_differential.py NORMALIZES explicitly before
comparing (see that module's own docstring) -- this module does not paper over the difference by
guessing an anchor; it just emits the true absolute value, honestly, as its native denomination.

CAPABILITY-GATING NOT REPLICATED HERE, ON PURPOSE: contemp_edb.py's `Capability`/`produced`-vs-
`capable` manifest is a REPORTING concern for engine/contemp_audit.py's operator-facing refusal
text (NO_VERDICT vs VACUOUSLY_CLEAN vs a real verdict) -- it is not part of the closed atom
vocabulary contemporaneity.lp #shows. This floor simply derives over whatever the live world's
`ledger`/journals actually contain (a pre-s23 schema naturally yields zero `row_tokened`-shaped
facts because the column does not exist; a missing journal file naturally yields zero
`tool_event`/`invocation` facts) -- the SAME degrade-to-absence contemp_edb.py's own EDB produces,
reached independently rather than by sharing its Capability machinery. The atom-level marriage
compares what BOTH sides derive over that shared absence; the human-facing refusal wording is
contemp_audit.py's own, separate job.

Read-only (DB SELECT only; journal files opened for reading only). Lazy imports banned
(top-of-file only)."""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from ledger_edb import Target, resolve

HERE = Path(__file__).resolve().parent
THRESHOLDS_LP = HERE / "contemp_thresholds.lp"

# The three tool-activity journals + the invocation journal, and the Kind label each contributes
# to tool_event/2 -- the SAME three-file/label mapping vestigial_documentation/design/ORCH-CONTEMPORANEITY-AUDIT.md's Part 2
# directive names ("tool_event(Kind, T) (from the hook journals -- change-gate, mutation-observer
# marker, delegation journal)"). This is CONFIGURATION (which files exist, what to call them), not
# derivation logic -- duplicated locally rather than imported from contemp_edb.py for the same
# reason `_atom_quote` below is a local copy, not an import: a shared config dict is not the thing
# a marriage differential is proving independent, but importing contemp_edb.py's OWN dict would
# still thread this module's import graph through the sibling producer's module, which the
# INDEPENDENCE posture (this file's docstring) deliberately avoids -- a plain tuple literal costs
# nothing to keep separate.
_TOOL_EVENT_JOURNALS: tuple[tuple[str, str], ...] = (
    ("mutation_observer.journal.jsonl", "mutation"),
    ("change_gate.journal.jsonl", "change_gate"),
    ("delegation_observer.journal.jsonl", "delegation"),
)
_INVOCATION_JOURNAL = "invocations.jsonl"


def _floor_parse_ts_ms(raw: str) -> int | None:
    """Independent timestamp parser (see this module's docstring's INDEPENDENCE section) -- reads
    the SAME two on-disk conventions contemp_edb.py's `_parse_ts_ms` reads (a trailing 'Z' is UTC;
    no trailing 'Z' is a naive-local `datetime.now().isoformat()`, for journal lines written before
    the pre-run-9 UTC-Z unification, per contemp_edb.py's own NAMED HAZARD section) but as a
    SEPARATE implementation, never a call into that function. Returns None (never raises) for a
    malformed timestamp."""
    raw = raw.strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            dt = datetime.fromisoformat(raw[:-1]).replace(tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)
        dt = datetime.fromisoformat(raw)
        return int(time.mktime(dt.timetuple()) * 1000 + dt.microsecond // 1000)
    except (ValueError, OverflowError):
        return None


def _floor_read_jsonl(path: Path) -> list[dict]:
    """Independent best-effort JSONL reader (see INDEPENDENCE section above) -- a separate
    implementation from contemp_edb.py's `_read_jsonl`. Never raises on a malformed line or a
    missing file; a missing/unreadable file degrades to the empty list, exactly like the ASP
    side's own EDB degrades a missing journal to zero facts for that family."""
    if not path.is_file():
        return []
    out: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def _load_thresholds() -> dict[str, int]:
    """Pull the three measured threshold facts straight out of engine/contemp_thresholds.lp's own
    text (ONE source of truth, ADR-0012 P1) -- read as DATA (regex over the .lp file's own fact
    lines) rather than loaded as an ASP program, so this SQL producer never hand-copies a literal
    that could silently drift from the value the ASP producer actually reasons over."""
    text = THRESHOLDS_LP.read_text(encoding="utf-8")
    out: dict[str, int] = {}
    for name in ("burst_threshold_ms", "silence_threshold_ms", "late_threshold_ms"):
        m = re.search(rf"^{name}\((\d+)\)\.", text, re.MULTILINE)
        if not m:
            raise RuntimeError(f"contemp_floor: {THRESHOLDS_LP} carries no {name}(N). fact -- "
                               f"the SQL floor's threshold source of truth is missing/malformed")
        out[name] = int(m.group(1))
    return out


def _sql_lit(s: str) -> str:
    """A SQL single-quoted string literal (input-side escaping -- embedding a Python string as a
    VALUES literal). Distinct job from `_atom_quote` below (which formats an OUTPUT clingo term);
    kept as its own tiny helper for the same reason -- neither is the logic under test."""
    return "'" + s.replace("'", "''") + "'"


def _atom_quote(col: str) -> str:
    """A SQL expression quoting `col` (text) as a clingo double-quoted string term -- the local,
    standalone mirror of engine/clingo_run.py's `quote_term` AND of engine/ledger_floor.py's own
    `_wi_quote` (same escaping order: backslash then quote, so both producers' quoted-string atoms
    compare bit-identically) -- NOT imported from either, deliberately, per this module's own
    INDEPENDENCE section."""
    return "('\"' || replace(replace(" + col + ", '\\', '\\\\'), '\"', '\\\"') || '\"')"


def _values_or_empty(rows: list[tuple], col0: str, col1: str, type1: str) -> str:
    """A SQL relation over `rows` (list of (text, int) pairs) -- a `VALUES (...)` list when
    non-empty, or the same declared-empty-relation idiom engine/ledger_floor.py's own
    amends_cte/answers_cte already use (`SELECT NULL::... WHERE false`) when the source (a journal
    family this world lacks) produced zero rows. `VALUES` with zero rows is not legal SQL, so the
    empty branch is not optional here."""
    if not rows:
        return f"SELECT NULL::text AS {col0}, NULL::{type1} AS {col1} WHERE false"
    vals = ", ".join(f"({_sql_lit(str(a))}, {int(b)})" for a, b in rows)
    return f"SELECT * FROM (VALUES {vals}) AS v({col0}, {col1})"


def floor_atoms(target_name: str, root: Path) -> tuple[set[str], str]:
    """The set of contemporaneity atoms the SQL floor derives for world `root` (read-only), plus a
    canonical text snapshot of the TRUE inputs this producer actually consumed (the ledger row
    columns this query reads + the raw journal file bytes) -- for the caller's DerivationRecord
    input_hash (mirrors ledger_floor.py's own `_ledger_snapshot_hash`, but this domain's true input
    spans two real sources, DB and filesystem, so the snapshot text names and hashes both,
    honestly, rather than over-claiming a single-artifact input)."""
    t: Target = resolve(target_name)
    rel = t.rel()
    thresholds = _load_thresholds()

    has_invocation_col = t.has_col("stamp_invocation")
    has_declared_col = t.has_col("event_declared_ts")
    ts_expr = "round(extract(epoch FROM ts)*1000)::bigint"

    if has_invocation_col:
        tok_cte = (f"SELECT id, stamp_invocation AS token, {ts_expr} AS ts_ms "
                   f"FROM {rel} WHERE stamp_invocation IS NOT NULL")
        untok_cte = f"SELECT id, {ts_expr} AS ts_ms FROM {rel} WHERE stamp_invocation IS NULL"
    else:
        tok_cte = "SELECT NULL::bigint AS id, NULL::text AS token, NULL::bigint AS ts_ms WHERE false"
        untok_cte = f"SELECT id, {ts_expr} AS ts_ms FROM {rel}"

    if has_declared_col:
        declared_cte = (f"SELECT id, round(extract(epoch FROM event_declared_ts)*1000)::bigint "
                        f"AS declared_ms FROM {rel} WHERE event_declared_ts IS NOT NULL")
    else:
        declared_cte = "SELECT NULL::bigint AS id, NULL::bigint AS declared_ms WHERE false"

    # ---- the SECOND real source: this world's own journal files, re-read + re-parsed HERE ------
    logs = root / ".claude" / "logs"
    inv_rows: list[tuple[str, int]] = []
    inv_raw_blobs: list[str] = []
    inv_path = logs / _INVOCATION_JOURNAL
    for rec in _floor_read_jsonl(inv_path):
        token, wc = rec.get("token"), rec.get("wall_clock")
        if not token or not wc:
            continue
        ms = _floor_parse_ts_ms(str(wc))
        if ms is None:
            continue
        inv_rows.append((str(token), ms))
    if inv_path.is_file():
        inv_raw_blobs.append(inv_path.read_text(encoding="utf-8", errors="replace"))

    te_rows: list[tuple[str, int]] = []
    te_raw_blobs: list[str] = []
    for fname, kind in _TOOL_EVENT_JOURNALS:
        path = logs / fname
        for rec in _floor_read_jsonl(path):
            ts_raw = rec.get("ts")
            if not ts_raw:
                continue
            ms = _floor_parse_ts_ms(str(ts_raw))
            if ms is None:
                continue
            te_rows.append((kind, ms))
        if path.is_file():
            te_raw_blobs.append(f"# {fname}\n" + path.read_text(encoding="utf-8", errors="replace"))

    inv_cte = _values_or_empty(inv_rows, "token", "wall_ms", "bigint")
    te_cte = _values_or_empty(te_rows, "kind", "ts_ms", "bigint")

    sql = f"""
    WITH
      led_tok AS ({tok_cte}),
      led_untok AS ({untok_cte}),
      led_declared AS ({declared_cte}),
      row_ts_all AS (SELECT id, ts_ms FROM led_tok UNION ALL SELECT id, ts_ms FROM led_untok),
      row_bounds AS (SELECT min(id) AS mn, max(id) AS mx, count(*) AS n FROM row_ts_all),
      refusal_fp AS (
        SELECT gs.id FROM row_bounds rb, generate_series(rb.mn, rb.mx) AS gs(id)
        WHERE rb.n > 0 AND NOT EXISTS (SELECT 1 FROM row_ts_all r WHERE r.id = gs.id)
      ),
      tok_counts AS (
        SELECT token, count(*) AS n, min(ts_ms) AS tmin, max(ts_ms) AS tmax
        FROM led_tok GROUP BY token
      ),
      tok_burst AS (SELECT token FROM tok_counts WHERE n > 1),
      tok_min_row AS (
        SELECT lt.token, lt.id, lt.ts_ms FROM led_tok lt
        JOIN tok_counts tc ON tc.token = lt.token AND lt.ts_ms = tc.tmin
      ),
      -- degraded ts-cluster (pre-token era only): adjacency by ID-RANK among untokened rows
      -- (LAG/LEAD over the filtered set is the exact SQL analog of contemporaneity.lp's
      -- next_untokened "immediate successor, not Id+1 arithmetic" idiom -- a burned id elsewhere
      -- in the id space cannot falsely break or create adjacency here, matching the ASP side).
      untok_ord AS (
        SELECT id, ts_ms, lead(id) OVER (ORDER BY id) AS next_id,
               lead(ts_ms) OVER (ORDER BY id) AS next_ts
        FROM led_untok
      ),
      ts_cluster AS (
        SELECT id AS id1, next_id AS id2 FROM untok_ord
        WHERE next_id IS NOT NULL AND (next_ts - ts_ms) <= {thresholds['burst_threshold_ms']}
      ),
      inv AS ({inv_cte}),
      te AS ({te_cte}),
      te_distinct AS (SELECT DISTINCT ts_ms FROM te),
      te_next AS (
        SELECT ts_ms AS t1, lead(ts_ms) OVER (ORDER BY ts_ms) AS t2 FROM te_distinct
      ),
      next_te AS (SELECT t1, t2 FROM te_next WHERE t2 IS NOT NULL),
      row_between AS (
        SELECT nt.t1, nt.t2 FROM next_te nt
        WHERE EXISTS (SELECT 1 FROM row_ts_all r WHERE r.ts_ms > nt.t1 AND r.ts_ms < nt.t2)
      ),
      silence AS (
        SELECT nt.t1, nt.t2 FROM next_te nt
        WHERE (nt.t2 - nt.t1) > {thresholds['silence_threshold_ms']}
          AND NOT EXISTS (SELECT 1 FROM row_between rb WHERE rb.t1 = nt.t1 AND rb.t2 = nt.t2)
      ),
      first_te AS (SELECT min(ts_ms) AS mn FROM te),
      intake_shape AS (
        SELECT tb.token FROM tok_burst tb JOIN tok_counts tc ON tc.token = tb.token
        WHERE (SELECT mn FROM first_te) IS NULL OR tc.tmax < (SELECT mn FROM first_te)
      ),
      first_row_after AS (
        SELECT s.t1, s.t2, min(r.ts_ms) AS min_after
        FROM silence s JOIN row_ts_all r ON r.ts_ms >= s.t2
        GROUP BY s.t1, s.t2
      ),
      silence_breaking_row AS (
        SELECT fra.t1, fra.t2, r.id FROM first_row_after fra
        JOIN row_ts_all r ON r.ts_ms = fra.min_after
      ),
      row_late_gap AS (
        SELECT rd.id, (rt.ts_ms - rd.declared_ms) AS gap
        FROM led_declared rd JOIN row_ts_all rt ON rt.id = rd.id
      ),
      row_honest_late AS (
        SELECT id FROM row_late_gap WHERE gap > {thresholds['late_threshold_ms']}
      ),
      backfill_suspect AS (
        SELECT DISTINCT tmr.token FROM tok_min_row tmr
        JOIN tok_burst tb ON tb.token = tmr.token
        JOIN silence_breaking_row sbr ON sbr.id = tmr.id
        WHERE tmr.id NOT IN (SELECT id FROM row_honest_late)
      ),
      late_declared AS (
        SELECT DISTINCT tmr.token FROM tok_min_row tmr
        JOIN tok_burst tb ON tb.token = tmr.token
        JOIN silence_breaking_row sbr ON sbr.id = tmr.id
        WHERE tmr.id IN (SELECT id FROM row_honest_late)
      ),
      row_delta AS (
        SELECT lt.id, (lt.ts_ms - i.wall_ms) AS d FROM led_tok lt JOIN inv i ON i.token = lt.token
      ),
      preceding_age AS (
        SELECT r.id, (r.ts_ms - pte.ts_ms) AS age FROM row_ts_all r
        CROSS JOIN LATERAL (
          SELECT ts_ms FROM te_distinct WHERE ts_ms <= r.ts_ms ORDER BY ts_ms DESC LIMIT 1
        ) pte
      ),
      verdict AS (
        SELECT CASE
          WHEN EXISTS (SELECT 1 FROM backfill_suspect) THEN 'backfill_suspect'
          WHEN EXISTS (SELECT 1 FROM late_declared) THEN 'late_declared'
          WHEN EXISTS (SELECT 1 FROM tok_burst) THEN 'batched_declared'
          WHEN EXISTS (SELECT 1 FROM led_tok) THEN 'contemporaneous'
          ELSE NULL
        END AS v
      )
    SELECT 'refusal_fingerprint(' || id || ')' FROM refusal_fp
    UNION ALL SELECT 'token_burst(' || {_atom_quote('token')} || ')' FROM tok_burst
    UNION ALL SELECT 'token_row_count(' || {_atom_quote('token')} || ',' || n || ')' FROM tok_counts
    UNION ALL SELECT 'token_min_ts(' || {_atom_quote('token')} || ',' || tmin || ')' FROM tok_counts
    UNION ALL SELECT 'token_max_ts(' || {_atom_quote('token')} || ',' || tmax || ')' FROM tok_counts
    UNION ALL SELECT 'intake_shape(' || {_atom_quote('token')} || ')' FROM intake_shape
    UNION ALL SELECT 'ts_cluster(' || id1 || ',' || id2 || ')' FROM ts_cluster
    UNION ALL SELECT 'silence(' || t1 || ',' || t2 || ')' FROM silence
    UNION ALL SELECT 'backfill_suspect(' || {_atom_quote('token')} || ')' FROM backfill_suspect
    UNION ALL SELECT 'late_declared(' || {_atom_quote('token')} || ')' FROM late_declared
    UNION ALL SELECT 'row_honest_late(' || id || ')' FROM row_honest_late
    UNION ALL SELECT 'row_delta_ms(' || id || ',' || d || ')' FROM row_delta
    UNION ALL SELECT 'preceding_activity_age_ms(' || id || ',' || age || ')' FROM preceding_age
    UNION ALL SELECT 'verdict(' || v || ')' FROM verdict WHERE v IS NOT NULL
    ;"""
    out = t.run(sql).stdout
    atoms = {line.strip() for line in out.splitlines() if line.strip()}

    # ---- the TRUE-input snapshot text (DB columns this query read + the raw journal bytes) ------
    snap_cols = ["id", "kind", "coalesce(stamp_invocation,'')" if has_invocation_col else "''",
                 "coalesce(extract(epoch FROM ts)::text,'')",
                 "coalesce(extract(epoch FROM event_declared_ts)::text,'')" if has_declared_col
                 else "''"]
    ledger_snap = t.run(f"SELECT {', '.join(snap_cols)} FROM {rel} ORDER BY id;").stdout
    snapshot = ("# ledger snapshot (id,kind,stamp_invocation,ts,event_declared_ts)\n" + ledger_snap
                + "\n# invocations.jsonl raw bytes\n" + "".join(inv_raw_blobs)
                + "\n# tool-event journals raw bytes\n" + "".join(te_raw_blobs))
    return atoms, snapshot


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2:
        print("usage: contemp_floor.py <target-name> <world-root-dir>", file=sys.stderr)
        return 2
    atoms, _snap = floor_atoms(args[0], Path(args[1]))
    print(f"# contemp_floor(SQL) -- {args[0]}: {len(atoms)} atoms")
    for a in sorted(atoms):
        print(f"  {a}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
