#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T02:09:09Z
#   last-change: 2026-07-14T02:26:04Z
#   contributors: e4410ef6/main, a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""preamble_floor -- the SQL FLOOR of the Part 3 preamble-ordering verdicts (design/
ORCH-CONTEMPORANEITY-PART3-SPEC.md §6): producer ONE of the marriage differential
(engine/preamble_differential.py), computing the SAME judgment predicates as
engine/lp/preamble_ordering.lp (ob_discharged/2, ob_violated/2, ob_undecidable/3,
ob_family_forced_undecidable/2, preamble_verdict/2, plus the three Id/Slug-typed base relations
that program #shows) in Postgres SQL -- window functions + set logic for every family EXCEPT
F11's own s22-violation arm, which needs ONE recursive CTE (the dependency-CYCLE member,
mirroring engine/ledger_floor.py's own `work_item_floor_atoms` -- transitive closure over
work_depends_on IS recursion's home turf even though spec §6's own "nothing here even needs
recursion" line, true of F1-F10, undersold F11 by one member; named here rather than silently
contradicting that line without comment).

RE-DERIVES FROM SOURCE, DOES NOT CONSUME engine/contemp_edb.py's STAGED EDB -- the SAME
independence posture engine/contemp_floor.py's own docstring states for the identical reason
("independence of DERIVATION is the point, shared INPUT is the design"): this module queries the
live ledger directly (a SEPARATE query text from contemp_edb.py's own SELECT) and re-reads/
re-parses the raw `.claude/logs/*.jsonl` journal bytes with its OWN small parser, never calling
into contemp_edb.py's helpers. The shared input is the real bytes on disk.

DENOMINATION: every timestamp is emitted as its native ABSOLUTE epoch-millisecond integer
(Postgres bigint has no 32-bit ceiling -- the identical reasoning engine/contemp_floor.py's own
docstring gives). engine/preamble_differential.py normalizes the ASP side's anchor-relative
Anchor argument UP to absolute for the four time-anchored families (F4/F9/F10/F11) before
comparing -- see that module's own docstring for the closed, family-keyed rewrite list.

SCOPE MATCHES engine/lp/preamble_ordering.lp EXACTLY (never more, never less -- an unfaithful
floor is worse than none): F11's question_open and review-gap arms are NOT re-derived here
either (that program's own header names the same deferral); this floor's `s22_violation`
sub-query mirrors engine/ledger_floor.py's own `work_item_floor_atoms` s22-violation logic
(dup_open / shipped_without_witness / dangling_dep / dep_cycle), a SEPARATE SQL text, never a
call into that module (same independence posture).

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

_INVOCATION_JOURNAL = "invocations.jsonl"
_MUTATION_JOURNAL = "mutation_observer.journal.jsonl"
_STOP_JOURNAL = "stop_clean_exit.journal.jsonl"
_DELEGATION_JOURNAL = "delegation_observer.journal.jsonl"
_BASH_COMPLETIONS_JOURNAL = "bash_completions.jsonl"
_VERIFY_COMMISSION_JOURNAL = "verify_commission.jsonl"

# The preamble's own `--refs row:<id>` convention (E2) -- an INDEPENDENT copy of
# engine/contemp_edb.py's `_REFS_ROW_RE` (same independence posture as that module's own
# `_floor_parse_ts_ms` vs contemp_edb.py's `_parse_ts_ms`).
_REFS_ROW_RE = re.compile(r"row:(\d+)")


def _floor_parse_ts_ms(raw: str) -> int | None:
    """Independent timestamp parser -- reads the same two on-disk conventions
    engine/contemp_edb.py's `_parse_ts_ms` reads, as a SEPARATE implementation."""
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
    """Independent best-effort JSONL reader (see engine/contemp_floor.py's own twin for the
    identical posture) -- never raises on a malformed line or a missing file."""
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


def _load_stop_window_ms() -> int:
    """E9's threshold, read as DATA from engine/contemp_thresholds.lp's own text (ONE source of
    truth, ADR-0012 P1) -- mirrors engine/contemp_floor.py's own `_load_thresholds`."""
    text = THRESHOLDS_LP.read_text(encoding="utf-8")
    m = re.search(r"^stop_disposition_window_ms\((\d+)\)\.", text, re.MULTILINE)
    if not m:
        raise RuntimeError(f"preamble_floor: {THRESHOLDS_LP} carries no stop_disposition_window_ms(N). "
                           f"fact -- the SQL floor's threshold source of truth is missing/malformed")
    return int(m.group(1))


def _sql_lit(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def _atom_quote(col: str) -> str:
    """A SQL expression quoting `col` (text) as a clingo double-quoted string term -- the local,
    independent mirror of clingo_run.quote_term (see this module's own docstring)."""
    return "('\"' || replace(replace(" + col + ", '\\', '\\\\'), '\"', '\\\"') || '\"')"


def _values_or_empty(rows: list[tuple], col0: str, col1: str, type1: str) -> str:
    if not rows:
        return f"SELECT NULL::text AS {col0}, NULL::{type1} AS {col1} WHERE false"
    vals = ", ".join(f"({_sql_lit(str(a))}, {int(b)})" for a, b in rows)
    return f"SELECT * FROM (VALUES {vals}) AS v({col0}, {col1})"


def floor_atoms(target_name: str, root: Path) -> tuple[set[str], str]:
    """The set of preamble-ordering atoms the SQL floor derives for world `root` (read-only),
    plus a canonical text snapshot of the true inputs consumed (mirrors
    engine/contemp_floor.py's own `floor_atoms` return shape)."""
    t: Target = resolve(target_name)
    rel = t.rel()
    W = _load_stop_window_ms()

    has_invocation_col = t.has_col("stamp_invocation")
    has_work_cols = t.has_col("work_slug")
    has_refs_col = t.has_col("refs")

    kind_check_def = t.scalar(
        f"SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname='ledger_kind_check' "
        f"AND conrelid = '{t.schema}.ledger'::regclass;")
    has_commission_kind = "commission" in kind_check_def

    ts_expr = "round(extract(epoch FROM ts)*1000)::bigint"
    work_slug_expr = "coalesce(work_slug,'')" if has_work_cols else "''"
    work_res_expr = "coalesce(work_resolution,'')" if has_work_cols else "''"
    work_wit_expr = ("(work_witness IS NOT NULL AND work_witness <> '')" if has_work_cols
                     else "false")
    work_dep_expr = "coalesce(work_depends_on,'')" if has_work_cols else "''"
    refs_expr = "coalesce(refs,'')" if has_refs_col else "''"
    tok_expr = "stamp_invocation" if has_invocation_col else "NULL::text"

    row_cte = (f"SELECT id, kind, {ts_expr} AS ts_ms, {tok_expr} AS token, "
              f"{work_slug_expr} AS work_slug, {work_res_expr} AS work_resolution, "
              f"{work_wit_expr} AS witness, {work_dep_expr} AS work_depends_on, "
              f"{refs_expr} AS refs FROM {rel}")

    # ---- journal reads (independent re-parse, see docstring) ----------------------------------
    logs = root / ".claude" / "logs"

    # tool_use_id -> token: this floor's OWN independent derivation of the E5 identity join
    # (CORRECTED 2026-07-14, vestigial_documentation/design/ORCH-RCA-PAIRING-KEY-DIVERGENCE.md sec-4/6.1: completion
    # lines no longer store a `token` -- pairing is a read-time join on the harness-assigned
    # `tool_use_id` present on both journals' lines. Same JOIN CONTRACT as contemp_edb.py's
    # dispatch_token_by_tool_use_id/join_bash_completions, re-derived here with this module's
    # own parser per the standing independence posture in this docstring: "independence of
    # DERIVATION is the point, shared INPUT is the design" -- never a call into contemp_edb.py.)
    floor_token_by_tool_use_id: dict[str, str] = {}
    inv_rows: list[tuple[str, int]] = []
    for rec in _floor_read_jsonl(logs / _INVOCATION_JOURNAL):
        token, wc, tuid = rec.get("token"), rec.get("wall_clock"), rec.get("tool_use_id")
        if token and tuid:
            floor_token_by_tool_use_id[str(tuid)] = str(token)
        if not token or not wc:
            continue
        ms = _floor_parse_ts_ms(str(wc))
        if ms is not None:
            inv_rows.append((str(token), ms))

    completion_rows: list[tuple[str, int]] = []
    for rec in _floor_read_jsonl(logs / _BASH_COMPLETIONS_JOURNAL):
        tuid, ts_raw = rec.get("tool_use_id"), rec.get("ts")
        if not tuid or not ts_raw:
            continue  # no identity to join on (incl. every pre-fix-era line) -- honestly skipped
        token = floor_token_by_tool_use_id.get(str(tuid))
        if not token:
            continue  # no dispatch line shares this identity -- skipped, never guessed
        ms = _floor_parse_ts_ms(str(ts_raw))
        if ms is not None:
            completion_rows.append((token, ms))

    mutation_ts: list[int] = []
    for rec in _floor_read_jsonl(logs / _MUTATION_JOURNAL):
        ts_raw = rec.get("ts")
        if not ts_raw:
            continue
        ms = _floor_parse_ts_ms(str(ts_raw))
        if ms is not None:
            mutation_ts.append(ms)

    stop_rows: list[tuple[str, int]] = []
    for rec in _floor_read_jsonl(logs / _STOP_JOURNAL):
        outcome, ts_raw = rec.get("outcome"), rec.get("ts")
        if not outcome or not ts_raw:
            continue
        ms = _floor_parse_ts_ms(str(ts_raw))
        if ms is not None:
            stop_rows.append((str(outcome), ms))

    dispatch_ts: list[int] = []
    for rec in _floor_read_jsonl(logs / _DELEGATION_JOURNAL):
        ts_raw = rec.get("ts")
        if not ts_raw or rec.get("kind") == "return":
            continue
        ms = _floor_parse_ts_ms(str(ts_raw))
        if ms is not None:
            dispatch_ts.append(ms)

    verify_rows: list[tuple[str, int]] = []
    for rec in _floor_read_jsonl(logs / _VERIFY_COMMISSION_JOURNAL):
        verdict, ts_raw = rec.get("verdict"), rec.get("ts")
        if not verdict or not ts_raw:
            continue
        ms = _floor_parse_ts_ms(str(ts_raw))
        if ms is not None:
            verify_rows.append((str(verdict), ms))

    inv_cte = _values_or_empty(inv_rows, "token", "lo_ms", "bigint")
    completions_cte = _values_or_empty(completion_rows, "token", "hi_ms", "bigint")
    stop_cte = _values_or_empty(stop_rows, "outcome", "ts_ms", "bigint")
    verify_cte = _values_or_empty(verify_rows, "verdict", "ts_ms", "bigint")
    mutation_vals = (", ".join(f"({m})" for m in mutation_ts)) if mutation_ts else "(NULL::bigint)"
    mutation_cte = (f"SELECT ts_ms FROM (VALUES {mutation_vals}) AS v(ts_ms) WHERE ts_ms IS NOT NULL"
                    if mutation_ts else "SELECT NULL::bigint AS ts_ms WHERE false")
    dispatch_vals = (", ".join(f"({m})" for m in dispatch_ts)) if dispatch_ts else "(NULL::bigint)"
    dispatch_cte = (f"SELECT ts_ms FROM (VALUES {dispatch_vals}) AS v(ts_ms) WHERE ts_ms IS NOT NULL"
                    if dispatch_ts else "SELECT NULL::bigint AS ts_ms WHERE false")

    q_slug = _atom_quote("slug")
    q_resolution = _atom_quote("resolution")

    sql = f"""
    WITH RECURSIVE
      row_all AS ({row_cte}),
      row_win AS (
        SELECT r.id, r.kind, r.token, i.lo_ms AS lo, c.hi_ms AS hi
        FROM row_all r
        LEFT JOIN ({inv_cte}) i ON i.token = r.token AND r.token IS NOT NULL
        LEFT JOIN ({completions_cte}) c ON c.token = r.token AND r.token IS NOT NULL
      ),
      mutation_evt AS ({mutation_cte}),
      first_mutation AS (SELECT min(ts_ms) AS t FROM mutation_evt),
      dispatch_evt AS ({dispatch_cte}),
      stop_evt AS ({stop_cte}),
      verify_evt AS ({verify_cte}),
      row_bounds AS (SELECT min(id) AS mn FROM row_all),
      first_row AS (SELECT r.id, r.kind FROM row_all r JOIN row_bounds b ON r.id = b.mn),
      commission_rows AS (SELECT id FROM row_all WHERE kind = 'commission'),
      review_rows AS (SELECT id FROM row_all WHERE kind = 'review'),
      decision_rows AS (SELECT id FROM row_all WHERE kind = 'decision'),
      verification_rows AS (SELECT id FROM row_all WHERE kind = 'verification'),
      work_opened AS (SELECT work_slug AS slug, id FROM row_all WHERE kind = 'work_opened'),
      work_claimed AS (SELECT work_slug AS slug, id FROM row_all WHERE kind = 'work_claimed'),
      work_closed AS (SELECT work_slug AS slug, work_resolution AS resolution, id, witness
                       FROM row_all WHERE kind = 'work_closed'),
      first_work_opened AS (SELECT min(id) AS mn FROM work_opened),
      -- E2: refs, parsed the SAME row:<id> convention -- one row per (Id,Target) match, plus
      -- a distinct row_refs_present for a non-empty refs value with NO parseable match.
      refs_parsed AS (
        SELECT id, (regexp_matches(refs, 'row:(\\d+)', 'g'))[1]::bigint AS target
        FROM row_all WHERE refs <> ''
      ),
      refs_present_unparsed AS (
        SELECT id FROM row_all WHERE refs <> ''
        AND NOT EXISTS (SELECT 1 FROM refs_parsed rp WHERE rp.id = row_all.id)
      ),

      -- ==== F1 ====================================================================
      f1_discharged AS (
        SELECT fr.id FROM first_row fr WHERE fr.kind = 'commission' AND {has_commission_kind}
      ),
      f1_violated AS (
        SELECT fr.id FROM first_row fr WHERE fr.kind <> 'commission' AND {has_commission_kind}
      ),
      f1_undecidable AS (
        SELECT fr.id, 'pre_s25' AS reason FROM first_row fr WHERE NOT {has_commission_kind}
      ),

      -- ==== F2 ====================================================================
      cr_before AS (
        SELECT rw.id, ve.ts_ms AS e FROM row_win rw JOIN commission_rows cr ON cr.id = rw.id
        CROSS JOIN verify_evt ve WHERE rw.hi IS NOT NULL AND rw.hi < ve.ts_ms
      ),
      cr_overlap AS (
        SELECT rw.id, ve.ts_ms AS e FROM row_win rw JOIN commission_rows cr ON cr.id = rw.id
        CROSS JOIN verify_evt ve
        WHERE rw.lo IS NOT NULL AND rw.hi IS NOT NULL AND rw.lo <= ve.ts_ms AND ve.ts_ms <= rw.hi
      ),
      cr_open AS (
        SELECT rw.id, ve.ts_ms AS e FROM row_win rw JOIN commission_rows cr ON cr.id = rw.id
        CROSS JOIN verify_evt ve
        WHERE rw.lo IS NOT NULL AND rw.hi IS NULL AND rw.lo <= ve.ts_ms
      ),
      evt_before_wo AS (
        SELECT ve.ts_ms AS e FROM verify_evt ve
        JOIN first_work_opened fwo ON true
        JOIN row_win rw ON rw.id = fwo.mn
        WHERE rw.lo IS NOT NULL AND ve.ts_ms < rw.lo
      ),
      f2_discharged AS (
        SELECT DISTINCT cb.id FROM cr_before cb
        WHERE NOT EXISTS (SELECT 1 FROM first_work_opened) OR EXISTS (
          SELECT 1 FROM evt_before_wo ev WHERE ev.e = cb.e)
      ),
      f2_untokened AS (
        SELECT cr.id FROM commission_rows cr JOIN row_win rw ON rw.id = cr.id
        WHERE rw.token IS NULL
      ),
      f2_open AS (
        SELECT DISTINCT cr.id FROM commission_rows cr JOIN cr_open co ON co.id = cr.id
        WHERE cr.id NOT IN (SELECT id FROM f2_discharged)
      ),
      f2_overlap AS (
        SELECT DISTINCT cr.id FROM commission_rows cr JOIN cr_overlap co ON co.id = cr.id
        WHERE cr.id NOT IN (SELECT id FROM cr_before)
        AND cr.id NOT IN (SELECT id FROM f2_discharged)
      ),
      f2_violated AS (
        SELECT cr.id FROM commission_rows cr JOIN row_win rw ON rw.id = cr.id
        WHERE rw.token IS NOT NULL
        AND cr.id NOT IN (SELECT id FROM f2_discharged)
        AND cr.id NOT IN (SELECT id FROM f2_open)
        AND cr.id NOT IN (SELECT id FROM f2_overlap)
      ),

      -- ==== F3 ====================================================================
      wo_trigger AS (SELECT id FROM work_opened),
      f3_discharged AS (
        SELECT wo.id FROM wo_trigger wo
        JOIN refs_parsed rp ON rp.id = wo.id
        JOIN commission_rows cr ON cr.id = rp.target AND cr.id < wo.id
        WHERE {has_commission_kind}
      ),
      f3_undecidable_unparsed AS (
        SELECT wo.id FROM wo_trigger wo JOIN refs_present_unparsed rpu ON rpu.id = wo.id
        WHERE {has_commission_kind} AND wo.id NOT IN (SELECT id FROM f3_discharged)
      ),
      f3_undecidable_pre_s25 AS (
        SELECT wo.id FROM wo_trigger wo WHERE NOT {has_commission_kind}
      ),
      f3_violated AS (
        SELECT wo.id FROM wo_trigger wo WHERE {has_commission_kind}
        AND wo.id NOT IN (SELECT id FROM f3_discharged)
        AND wo.id NOT IN (SELECT id FROM f3_undecidable_unparsed)
      ),

      -- ==== F4 ====================================================================
      f4_discharged AS (
        SELECT fm.t FROM first_mutation fm WHERE fm.t IS NOT NULL AND EXISTS (
          SELECT 1 FROM work_opened wo JOIN row_win rw ON rw.id = wo.id
          WHERE rw.hi IS NOT NULL AND rw.hi < fm.t)
      ),
      f4_undecidable_untok AS (
        SELECT fm.t FROM first_mutation fm WHERE fm.t IS NOT NULL AND EXISTS (
          SELECT 1 FROM work_opened wo JOIN row_win rw ON rw.id = wo.id WHERE rw.token IS NULL)
        AND fm.t NOT IN (SELECT t FROM f4_discharged)
      ),
      f4_undecidable_open AS (
        SELECT fm.t FROM first_mutation fm WHERE fm.t IS NOT NULL AND EXISTS (
          SELECT 1 FROM work_opened wo JOIN row_win rw ON rw.id = wo.id
          WHERE rw.lo IS NOT NULL AND rw.hi IS NULL AND rw.lo <= fm.t)
        AND fm.t NOT IN (SELECT t FROM f4_discharged)
        AND fm.t NOT IN (SELECT t FROM f4_undecidable_untok)
      ),
      f4_violated AS (
        SELECT fm.t FROM first_mutation fm WHERE fm.t IS NOT NULL
        AND fm.t NOT IN (SELECT t FROM f4_discharged)
        AND fm.t NOT IN (SELECT t FROM f4_undecidable_untok)
        AND fm.t NOT IN (SELECT t FROM f4_undecidable_open)
      ),

      -- ==== F5 / F6 ===============================================================
      f5_discharged AS (
        SELECT DISTINCT wc.slug FROM work_claimed wc JOIN work_opened wo ON wo.slug = wc.slug
        WHERE wo.id < wc.id
      ),
      f5_violated AS (
        SELECT DISTINCT wc.slug FROM work_claimed wc
        WHERE wc.slug NOT IN (SELECT slug FROM f5_discharged)
      ),
      f6_discharged AS (
        SELECT DISTINCT wcl.slug FROM work_closed wcl JOIN work_claimed wc ON wc.slug = wcl.slug
        WHERE wc.id < wcl.id
      ),
      f6_violated AS (
        SELECT DISTINCT wcl.slug FROM work_closed wcl
        WHERE wcl.slug NOT IN (SELECT slug FROM f6_discharged)
      ),

      -- ==== F7 ====================================================================
      any_stop AS (SELECT count(*) > 0 AS present FROM stop_evt),
      f7_discharged AS (
        SELECT DISTINCT wo.id FROM work_opened wo JOIN review_rows rr ON rr.id > wo.id
        WHERE (SELECT present FROM any_stop) = false
        UNION
        SELECT DISTINCT wo.id FROM work_opened wo JOIN review_rows rr ON rr.id > wo.id
        JOIN row_win rw ON rw.id = rr.id CROSS JOIN stop_evt se
        WHERE rw.hi IS NOT NULL AND rw.hi < se.ts_ms
      ),
      f7_undecidable_untok AS (
        SELECT DISTINCT wo.id FROM work_opened wo JOIN review_rows rr ON rr.id > wo.id
        JOIN row_win rw ON rw.id = rr.id
        WHERE (SELECT present FROM any_stop) AND rw.token IS NULL
        AND wo.id NOT IN (SELECT id FROM f7_discharged)
      ),
      f7_undecidable_open AS (
        SELECT DISTINCT wo.id FROM work_opened wo JOIN review_rows rr ON rr.id > wo.id
        JOIN row_win rw ON rw.id = rr.id CROSS JOIN stop_evt se
        WHERE rw.lo IS NOT NULL AND rw.hi IS NULL AND rw.lo <= se.ts_ms
        AND wo.id NOT IN (SELECT id FROM f7_discharged)
        AND wo.id NOT IN (SELECT id FROM f7_undecidable_untok)
      ),
      f7_violated AS (
        SELECT id FROM work_opened
        WHERE id NOT IN (SELECT id FROM f7_discharged)
        AND id NOT IN (SELECT id FROM f7_undecidable_untok)
        AND id NOT IN (SELECT id FROM f7_undecidable_open)
      ),

      -- ==== F8 ====================================================================
      criteria_ref AS (
        SELECT vr.id AS vid, rp.target AS cid FROM verification_rows vr
        JOIN refs_parsed rp ON rp.id = vr.id
      ),
      f8_discharged AS (
        SELECT DISTINCT cref.cid FROM criteria_ref cref JOIN row_win rw ON rw.id = cref.cid
        CROSS JOIN first_mutation fm WHERE fm.t IS NOT NULL AND rw.hi IS NOT NULL AND rw.hi < fm.t
        UNION
        SELECT DISTINCT cref.cid FROM criteria_ref cref
        WHERE NOT EXISTS (SELECT 1 FROM first_mutation WHERE t IS NOT NULL)
      ),
      f8_undecidable_untok AS (
        SELECT DISTINCT cref.cid FROM criteria_ref cref JOIN row_win rw ON rw.id = cref.cid
        CROSS JOIN first_mutation fm WHERE fm.t IS NOT NULL AND rw.token IS NULL
        AND cref.cid NOT IN (SELECT cid FROM f8_discharged)
      ),
      f8_undecidable_open AS (
        SELECT DISTINCT cref.cid FROM criteria_ref cref JOIN row_win rw ON rw.id = cref.cid
        CROSS JOIN first_mutation fm
        WHERE fm.t IS NOT NULL AND rw.lo IS NOT NULL AND rw.hi IS NULL AND rw.lo <= fm.t
        AND cref.cid NOT IN (SELECT cid FROM f8_discharged)
      ),
      f8_violated AS (
        SELECT DISTINCT cref.cid FROM criteria_ref cref
        WHERE cref.cid NOT IN (SELECT cid FROM f8_discharged)
        AND cref.cid NOT IN (SELECT cid FROM f8_undecidable_untok)
        AND cref.cid NOT IN (SELECT cid FROM f8_undecidable_open)
      ),
      f8_undecidable_unparsed AS (
        SELECT vr.id AS vid FROM verification_rows vr JOIN refs_present_unparsed rpu ON rpu.id = vr.id
        WHERE vr.id NOT IN (SELECT vid FROM criteria_ref)
      ),

      -- ==== F9 ====================================================================
      decision_before_dispatch AS (
        SELECT dr.id, de.ts_ms AS t FROM decision_rows dr JOIN row_win rw ON rw.id = dr.id
        CROSS JOIN dispatch_evt de WHERE rw.hi IS NOT NULL AND rw.hi < de.ts_ms
      ),
      other_dispatch_between AS (
        SELECT dbd.id, dbd.t FROM decision_before_dispatch dbd
        JOIN row_win rw ON rw.id = dbd.id
        JOIN dispatch_evt de2 ON de2.ts_ms > rw.hi AND de2.ts_ms < dbd.t
      ),
      f9_discharged AS (
        SELECT DISTINCT dbd.t FROM decision_before_dispatch dbd
        WHERE (dbd.id, dbd.t) NOT IN (SELECT id, t FROM other_dispatch_between)
      ),
      f9_undecidable_untok AS (
        SELECT DISTINCT de.ts_ms AS t FROM dispatch_evt de
        WHERE EXISTS (SELECT 1 FROM decision_rows dr JOIN row_win rw ON rw.id = dr.id
                      WHERE rw.token IS NULL)
        AND de.ts_ms NOT IN (SELECT t FROM f9_discharged)
      ),
      f9_undecidable_open AS (
        SELECT DISTINCT de.ts_ms AS t FROM dispatch_evt de
        WHERE EXISTS (SELECT 1 FROM decision_rows dr JOIN row_win rw ON rw.id = dr.id
                      WHERE rw.lo IS NOT NULL AND rw.hi IS NULL AND rw.lo <= de.ts_ms)
        AND de.ts_ms NOT IN (SELECT t FROM f9_discharged)
        AND de.ts_ms NOT IN (SELECT t FROM f9_undecidable_untok)
      ),
      f9_violated AS (
        SELECT DISTINCT de.ts_ms AS t FROM dispatch_evt de
        WHERE de.ts_ms NOT IN (SELECT t FROM f9_discharged)
        AND de.ts_ms NOT IN (SELECT t FROM f9_undecidable_untok)
        AND de.ts_ms NOT IN (SELECT t FROM f9_undecidable_open)
      ),

      -- ==== F10 ===================================================================
      decision_in_stop_window AS (
        SELECT dr.id, se.ts_ms AS st FROM decision_rows dr JOIN row_win rw ON rw.id = dr.id
        CROSS JOIN stop_evt se
        WHERE rw.lo IS NOT NULL AND rw.hi IS NOT NULL
        AND rw.lo >= se.ts_ms - {W} AND rw.hi <= se.ts_ms
      ),
      f10_discharged AS (SELECT DISTINCT st FROM decision_in_stop_window),
      f10_undecidable_untok AS (
        SELECT DISTINCT se.ts_ms AS st FROM stop_evt se
        WHERE EXISTS (SELECT 1 FROM decision_rows dr JOIN row_win rw ON rw.id = dr.id
                      WHERE rw.token IS NULL)
        AND se.ts_ms NOT IN (SELECT st FROM f10_discharged)
      ),
      f10_undecidable_open AS (
        SELECT DISTINCT se.ts_ms AS st FROM stop_evt se
        WHERE EXISTS (SELECT 1 FROM decision_rows dr JOIN row_win rw ON rw.id = dr.id
                      WHERE rw.lo IS NOT NULL AND rw.hi IS NULL
                      AND rw.lo >= se.ts_ms - {W} AND rw.lo <= se.ts_ms)
        AND se.ts_ms NOT IN (SELECT st FROM f10_discharged)
        AND se.ts_ms NOT IN (SELECT st FROM f10_undecidable_untok)
      ),
      f10_violated AS (
        SELECT DISTINCT se.ts_ms AS st FROM stop_evt se
        WHERE se.ts_ms NOT IN (SELECT st FROM f10_discharged)
        AND se.ts_ms NOT IN (SELECT st FROM f10_undecidable_untok)
        AND se.ts_ms NOT IN (SELECT st FROM f10_undecidable_open)
      ),

      -- ==== F11 (s22 violation flags, mirrors engine/ledger_floor.py's own s22 logic --
      -- ALL FOUR members of engine/lp/work_items.lp's own s22_violation disjunction: the two
      -- PROVABLY-VACUOUS-UNDER-NORMAL-OPERATION members (dup_open, shipped_no_witness -- s22's
      -- own write-time triggers/CHECK already refuse both) AND the two GENUINELY REACHABLE ones
      -- (dangling dependency, dependency cycle -- s22 does NOT refuse either at write time,
      -- that program's own header names this) ====
      s22_dup_open AS (SELECT slug FROM work_opened GROUP BY slug HAVING count(*) > 1),
      s22_shipped_no_witness AS (SELECT slug FROM work_closed
        WHERE resolution = 'shipped' AND witness = false),
      work_depends AS (SELECT work_slug AS dependent, work_depends_on AS antecedent
                       FROM row_all WHERE kind = 'work_depends_on'),
      s22_dangling_dep AS (
        SELECT wd.dependent FROM work_depends wd
        WHERE NOT EXISTS (SELECT 1 FROM work_opened wo WHERE wo.slug = wd.antecedent)
      ),
      s22_dep_reach(start_slug, cur) AS (
        SELECT dependent, antecedent FROM work_depends
        UNION
        SELECT r.start_slug, wd.antecedent FROM s22_dep_reach r
        JOIN work_depends wd ON wd.dependent = r.cur
      ),
      s22_dep_cycle AS (SELECT DISTINCT start_slug FROM s22_dep_reach WHERE cur = start_slug),
      s22_violation AS (
        SELECT (EXISTS (SELECT 1 FROM s22_dup_open) OR
                EXISTS (SELECT 1 FROM s22_shipped_no_witness) OR
                EXISTS (SELECT 1 FROM s22_dangling_dep) OR
                EXISTS (SELECT 1 FROM s22_dep_cycle)) AS present
      ),
      f11_violated AS (SELECT ts_ms AS st FROM stop_evt WHERE (SELECT present FROM s22_violation)),
      f11_undecidable AS (SELECT ts_ms AS st FROM stop_evt WHERE NOT (SELECT present FROM s22_violation))
    SELECT 'first_row(' || fr.id || ')' FROM first_row fr
    UNION ALL SELECT 'first_work_opened(' || mn || ')' FROM first_work_opened
    UNION ALL SELECT 'commission_row(' || id || ')' FROM commission_rows
    UNION ALL SELECT 'criteria_ref(' || vid || ',' || cid || ')' FROM criteria_ref

    UNION ALL SELECT 'ob_discharged(f1,' || id || ')' FROM f1_discharged
    UNION ALL SELECT 'ob_violated(f1,' || id || ')' FROM f1_violated
    UNION ALL SELECT 'ob_undecidable(f1,' || id || ',' || reason || ')' FROM f1_undecidable

    UNION ALL SELECT 'ob_discharged(f2,' || id || ')' FROM f2_discharged
    UNION ALL SELECT 'ob_violated(f2,' || id || ')' FROM f2_violated
    UNION ALL SELECT 'ob_undecidable(f2,' || cr.id || ',no_verify_journal)' FROM commission_rows cr
        WHERE NOT {("true" if verify_rows else "false")}
    UNION ALL SELECT 'ob_undecidable(f2,' || id || ',untokened_row)' FROM f2_untokened
        WHERE {("true" if verify_rows else "false")}
    UNION ALL SELECT 'ob_undecidable(f2,' || id || ',open_window)' FROM f2_open
        WHERE {("true" if verify_rows else "false")}
    UNION ALL SELECT 'ob_undecidable(f2,' || id || ',window_overlap)' FROM f2_overlap
        WHERE {("true" if verify_rows else "false")}

    UNION ALL SELECT 'ob_discharged(f3,' || id || ')' FROM f3_discharged
    UNION ALL SELECT 'ob_violated(f3,' || id || ')' FROM f3_violated
    UNION ALL SELECT 'ob_undecidable(f3,' || id || ',refs_unparsed)' FROM f3_undecidable_unparsed
    UNION ALL SELECT 'ob_undecidable(f3,' || id || ',pre_s25)' FROM f3_undecidable_pre_s25

    UNION ALL SELECT 'ob_discharged(f4,' || t || ')' FROM f4_discharged
    UNION ALL SELECT 'ob_violated(f4,' || t || ')' FROM f4_violated
    UNION ALL SELECT 'ob_undecidable(f4,' || t || ',untokened_row)' FROM f4_undecidable_untok
    UNION ALL SELECT 'ob_undecidable(f4,' || t || ',open_window)' FROM f4_undecidable_open

    UNION ALL SELECT 'ob_discharged(f5,' || {q_slug} || ')' FROM f5_discharged
    UNION ALL SELECT 'ob_violated(f5,' || {q_slug} || ')' FROM f5_violated
    UNION ALL SELECT 'ob_discharged(f6,' || {q_slug} || ')' FROM f6_discharged
    UNION ALL SELECT 'ob_violated(f6,' || {q_slug} || ')' FROM f6_violated

    UNION ALL SELECT 'ob_discharged(f7,' || id || ')' FROM f7_discharged
    UNION ALL SELECT 'ob_violated(f7,' || id || ')' FROM f7_violated
    UNION ALL SELECT 'ob_undecidable(f7,' || id || ',untokened_row)' FROM f7_undecidable_untok
    UNION ALL SELECT 'ob_undecidable(f7,' || id || ',open_window)' FROM f7_undecidable_open

    UNION ALL SELECT 'ob_discharged(f8,' || cid || ')' FROM f8_discharged
    UNION ALL SELECT 'ob_violated(f8,' || cid || ')' FROM f8_violated
    UNION ALL SELECT 'ob_undecidable(f8,' || cid || ',untokened_row)' FROM f8_undecidable_untok
    UNION ALL SELECT 'ob_undecidable(f8,' || cid || ',open_window)' FROM f8_undecidable_open
    UNION ALL SELECT 'ob_undecidable(f8,' || vid || ',refs_unparsed)' FROM f8_undecidable_unparsed

    UNION ALL SELECT 'ob_discharged(f9,' || t || ')' FROM f9_discharged
    UNION ALL SELECT 'ob_violated(f9,' || t || ')' FROM f9_violated
    UNION ALL SELECT 'ob_undecidable(f9,' || t || ',untokened_row)' FROM f9_undecidable_untok
    UNION ALL SELECT 'ob_undecidable(f9,' || t || ',open_window)' FROM f9_undecidable_open

    UNION ALL SELECT 'ob_discharged(f10,' || st || ')' FROM f10_discharged
    UNION ALL SELECT 'ob_violated(f10,' || st || ')' FROM f10_violated
    UNION ALL SELECT 'ob_undecidable(f10,' || st || ',untokened_row)' FROM f10_undecidable_untok
    UNION ALL SELECT 'ob_undecidable(f10,' || st || ',open_window)' FROM f10_undecidable_open

    UNION ALL SELECT 'ob_violated(f11,' || st || ')' FROM f11_violated
    UNION ALL SELECT 'ob_undecidable(f11,' || st || ',capability_absent)' FROM f11_undecidable

    UNION ALL SELECT 'ob_family_forced_undecidable(f4,pre_s22)' WHERE NOT {has_work_cols}
        AND EXISTS (SELECT 1 FROM row_all)
    UNION ALL SELECT 'ob_family_forced_undecidable(f5,pre_s22)' WHERE NOT {has_work_cols}
        AND EXISTS (SELECT 1 FROM row_all)
    UNION ALL SELECT 'ob_family_forced_undecidable(f6,pre_s22)' WHERE NOT {has_work_cols}
        AND EXISTS (SELECT 1 FROM row_all)
    UNION ALL SELECT 'ob_family_forced_undecidable(f7,pre_s22)' WHERE NOT {has_work_cols}
        AND EXISTS (SELECT 1 FROM row_all)
    UNION ALL SELECT 'ob_family_forced_undecidable(f10,no_stop_record)'
        WHERE NOT EXISTS (SELECT 1 FROM stop_evt) AND EXISTS (SELECT 1 FROM row_all)
    UNION ALL SELECT 'ob_family_forced_undecidable(f12,capability_absent)'
        WHERE NOT {has_invocation_col} AND EXISTS (SELECT 1 FROM row_all)
    ;"""
    out = t.run(sql).stdout
    atoms = {line.strip() for line in out.splitlines() if line.strip()}

    # ---- F12 -- imported wholesale from Part 2 (contemporaneity.lp is NOT re-derived here;
    # this floor mirrors the SAME token/backfill_suspect/late_declared judgment
    # engine/contemp_floor.py's own floor_atoms already derives -- computed inline, from the
    # SAME row_all + invocation source, matching contemporaneity.lp's own burst/silence rules).
    atoms |= _f12_atoms(t, rel, root, has_invocation_col)
    atoms |= _family_verdicts(atoms)

    snap_cols = ["id", "kind", "coalesce(stamp_invocation,'')" if has_invocation_col else "''",
                 "coalesce(extract(epoch FROM ts)::text,'')"]
    ledger_snap = t.run(f"SELECT {', '.join(snap_cols)} FROM {rel} ORDER BY id;").stdout
    logs_blob = "".join(
        (p.read_text(encoding="utf-8", errors="replace") if p.is_file() else "")
        for p in (logs / f for f in (_INVOCATION_JOURNAL, _MUTATION_JOURNAL, _STOP_JOURNAL,
                                     _DELEGATION_JOURNAL, _BASH_COMPLETIONS_JOURNAL,
                                     _VERIFY_COMMISSION_JOURNAL)))
    snapshot = "# ledger snapshot\n" + ledger_snap + "\n# journal bytes\n" + logs_blob
    return atoms, snapshot


_FAMILIES = tuple(f"f{n}" for n in range(1, 13))
_ANCHOR_RE = re.compile(r"^ob_(discharged|violated)\((f\d+),")
_UNDEC_RE = re.compile(r"^ob_undecidable\((f\d+),")
_FORCED_RE = re.compile(r"^ob_family_forced_undecidable\((f\d+),")


def _family_verdicts(atoms: set[str]) -> set[str]:
    """The FAMILY-STRATUM verdict ladder (spec §5, extended with the forced-undecidable escape
    hatch -- see engine/lp/preamble_ordering.lp's own header for the identical rules), computed
    here as a final Python aggregation over this floor's OWN already-derived instance atoms --
    not a SECOND SQL re-derivation of the same four-way priority (violated > undecidable >
    forced-undecidable > discharged > vacuous), since the priority itself is pure set logic over
    atoms this module already produced independently of the ASP program. E8's twelve families
    are hardcoded here (`_FAMILIES`) exactly as engine/preamble_obligations.lp hardcodes them --
    a facts-file edit there is a `_FAMILIES` edit here, named as the one place both must move
    together (ADR-0012 P1: one obligation catalogue, two encodings, kept in step by inspection)."""
    violated = {m.group(2) for a in atoms if (m := _ANCHOR_RE.match(a)) and m.group(1) == "violated"}
    undecidable = {m.group(1) for a in atoms if (m := _UNDEC_RE.match(a))}
    forced = {m.group(1) for a in atoms if (m := _FORCED_RE.match(a))}
    discharged = {m.group(2) for a in atoms if (m := _ANCHOR_RE.match(a)) and m.group(1) == "discharged"}
    out = set()
    for f in _FAMILIES:
        if f in violated:
            out.add(f"preamble_verdict({f},violated)")
        elif f in undecidable:
            out.add(f"preamble_verdict({f},undecidable)")
        elif f in forced:
            out.add(f"preamble_verdict({f},undecidable)")
        elif f in discharged:
            out.add(f"preamble_verdict({f},discharged)")
        else:
            out.add(f"preamble_verdict({f},vacuous)")
    return out


_TOOL_EVENT_JOURNALS = ("mutation_observer.journal.jsonl", "change_gate.journal.jsonl",
                        "delegation_observer.journal.jsonl")


def _f12_atoms(t: Target, rel: str, root: Path, has_invocation_col: bool) -> set[str]:
    """F12 (ob_record_as_you_go) -- imported wholesale from Part 2's own verdict
    (engine/lp/contemporaneity.lp), re-derived here via the SAME token-burst / silence /
    backfill_suspect / late_declared shape engine/contemp_floor.py's own floor_atoms already
    computes for that domain -- a SEPARATE re-implementation (independence posture, this
    module's own docstring), restricted to the two atoms this file's ob_discharged(f12,_)/
    ob_violated(f12,_) rules actually consume (token/1, backfill_suspect/1, late_declared/1),
    never the whole Part 2 atom set (this file's own scope is F1-F12 only)."""
    if not has_invocation_col:
        return set()
    thresholds_text = THRESHOLDS_LP.read_text(encoding="utf-8")
    burst_m = re.search(r"^burst_threshold_ms\((\d+)\)\.", thresholds_text, re.MULTILINE)
    silence_m = re.search(r"^silence_threshold_ms\((\d+)\)\.", thresholds_text, re.MULTILINE)
    late_m = re.search(r"^late_threshold_ms\((\d+)\)\.", thresholds_text, re.MULTILINE)
    silence_th, late_th = int(silence_m.group(1)), int(late_m.group(1))
    has_declared_col = t.has_col("event_declared_ts")

    te_ts: list[int] = []
    for fname in _TOOL_EVENT_JOURNALS:
        for rec in _floor_read_jsonl(root / ".claude" / "logs" / fname):
            ts_raw = rec.get("ts")
            if not ts_raw:
                continue
            ms = _floor_parse_ts_ms(str(ts_raw))
            if ms is not None:
                te_ts.append(ms)
    te_vals = (", ".join(f"({m})" for m in te_ts)) if te_ts else "(NULL::bigint)"
    te_cte = (f"SELECT DISTINCT ts_ms FROM (VALUES {te_vals}) AS v(ts_ms) WHERE ts_ms IS NOT NULL"
             if te_ts else "SELECT NULL::bigint AS ts_ms WHERE false")

    declared_cte = (f"SELECT id, round(extract(epoch FROM event_declared_ts)*1000)::bigint AS d "
                    f"FROM {rel} WHERE event_declared_ts IS NOT NULL") if has_declared_col \
        else "SELECT NULL::bigint AS id, NULL::bigint AS d WHERE false"
    sql = f"""
    WITH
      tok AS (SELECT id, stamp_invocation AS token,
               round(extract(epoch FROM ts)*1000)::bigint AS ts_ms
               FROM {rel} WHERE stamp_invocation IS NOT NULL),
      all_rows AS (SELECT id, round(extract(epoch FROM ts)*1000)::bigint AS ts_ms FROM {rel}),
      tok_counts AS (SELECT token, count(*) AS n, min(ts_ms) AS tmin FROM tok GROUP BY token),
      tok_burst AS (SELECT token FROM tok_counts WHERE n > 1),
      tok_min_row AS (
        SELECT tk.token, tk.id, tk.ts_ms FROM tok tk
        JOIN tok_counts tc ON tc.token = tk.token AND tk.ts_ms = tc.tmin
      ),
      declared AS ({declared_cte}),
      row_late_gap AS (SELECT dd.id, (ar.ts_ms - dd.d) AS gap FROM declared dd
                        JOIN all_rows ar ON ar.id = dd.id),
      row_honest_late AS (SELECT id FROM row_late_gap WHERE gap > {late_th}),
      te AS ({te_cte}),
      te_next AS (SELECT ts_ms AS t1, lead(ts_ms) OVER (ORDER BY ts_ms) AS t2 FROM te),
      next_te AS (SELECT t1, t2 FROM te_next WHERE t2 IS NOT NULL),
      row_between AS (
        SELECT nt.t1, nt.t2 FROM next_te nt
        WHERE EXISTS (SELECT 1 FROM all_rows r WHERE r.ts_ms > nt.t1 AND r.ts_ms < nt.t2)
      ),
      silence AS (
        SELECT nt.t1, nt.t2 FROM next_te nt
        WHERE (nt.t2 - nt.t1) > {silence_th}
        AND NOT EXISTS (SELECT 1 FROM row_between rb WHERE rb.t1 = nt.t1 AND rb.t2 = nt.t2)
      ),
      first_row_after AS (
        SELECT s.t1, s.t2, min(r.ts_ms) AS min_after FROM silence s
        JOIN all_rows r ON r.ts_ms >= s.t2 GROUP BY s.t1, s.t2
      ),
      silence_breaking_row AS (
        SELECT fra.t1, fra.t2, r.id FROM first_row_after fra
        JOIN all_rows r ON r.ts_ms = fra.min_after
      ),
      backfill_suspect AS (
        SELECT DISTINCT tmr.token FROM tok_min_row tmr JOIN tok_burst tb ON tb.token = tmr.token
        JOIN silence_breaking_row sbr ON sbr.id = tmr.id
        WHERE tmr.id NOT IN (SELECT id FROM row_honest_late)
      ),
      late_declared AS (
        SELECT DISTINCT tmr.token FROM tok_min_row tmr JOIN tok_burst tb ON tb.token = tmr.token
        JOIN silence_breaking_row sbr ON sbr.id = tmr.id
        WHERE tmr.id IN (SELECT id FROM row_honest_late)
      )
    SELECT 'ob_violated(f12,' || {_atom_quote('token')} || ')' FROM backfill_suspect
    UNION ALL SELECT 'ob_discharged(f12,' || {_atom_quote('token')} || ')' FROM late_declared
    UNION ALL SELECT 'ob_discharged(f12,' || {_atom_quote('tc.token')} || ')' FROM tok_counts tc
      WHERE tc.token NOT IN (SELECT token FROM backfill_suspect)
      AND tc.token NOT IN (SELECT token FROM late_declared)
    ;"""
    out = t.run(sql).stdout
    return {line.strip() for line in out.splitlines() if line.strip()}


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2:
        print("usage: preamble_floor.py <target-name> <world-root-dir>", file=sys.stderr)
        return 2
    atoms, _snap = floor_atoms(args[0], Path(args[1]))
    print(f"# preamble_floor(SQL) -- {args[0]}: {len(atoms)} atoms")
    for a in sorted(atoms):
        print(f"  {a}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
