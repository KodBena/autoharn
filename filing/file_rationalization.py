#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-06T15:42:34Z
#   last-change: 2026-07-18T22:50:46Z
#   contributors: 37017f46/main, a857c93d/main, ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""file_rationalization -- the filing path for the RATIONALIZATION LEDGER (db/harness/002).

This is the APPEND PATH the hack-rationalization-detector skill was missing: the skill directs every
runner to read `known-cases.md` as its few-shot but ships no way for a NEW fire to become a PRIOR case.
This script is that way (design lean (b): a small tools/ script, NOT an INSERT template in the skill
bundle). A detector fire -> `file` a finding; an adjudication -> `dispose` (confirmed-hack /
false-positive / duplicate-of, actor-attributed, F28 append-only); then `gen-known-cases` regenerates
the few-shot from the CONFIRMED corpus (design lean (a): known-cases.md is GENERATED, the curated cases
retired into SEED below).

Store: the `harness` DB, `harness` schema (psql -h 192.168.122.1 -d harness) -- claims about WORK, never
subject/evidence records. Connection is via subprocess `psql` (the ledger_edb.py idiom: no driver
dependency, and every import here is top-of-file per the lazy-import edict). Values cross into SQL as
psql `:'var'` string-literal parameters (injection-safe; psql does the escaping), so a rationalization
containing quotes files cleanly.

  python tools/file_rationalization.py ensure-schema
  python tools/file_rationalization.py file --quoted "..." --register "scope creep" \\
      --context "PR #12 cardTree gate" --detector-version v1 [--better-fix "..."] [--law-refs "..."] \\
      [--session <id>] [--commit <sha>]
  python tools/file_rationalization.py dispose --finding 3 --act confirmed-hack --actor "bork" [--note "..."]
  python tools/file_rationalization.py gen-known-cases            # regenerate the few-shot from confirmed rows
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pghost_resolve  # filing/pghost_resolve.py, the ONE home -- never a literal host default

PGHOST = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
DB = os.environ.get("HARNESS_DB", "harness")
DEFAULT_SCHEMA = os.environ.get("HARNESS_SCHEMA", "harness")
REPO_ROOT = Path(__file__).resolve().parent.parent
DDL = REPO_ROOT / "stores" / "002_rationalization_ledger.sql"   # autoharn: stores/ (was db/harness/)
# The skill's few-shot lives outside the repo (the skill bundle is installed under ~/.claude); the
# generator writes there. Overridable with --out (used by the smoke test to write a scratch copy).
DEFAULT_KNOWN_CASES = Path(
    os.environ.get("KNOWN_CASES_OUT",
                   str(Path.home() / ".claude" / "skills" / "hack-rationalization-detector"
                       / "references" / "known-cases.md")))


class LedgerError(RuntimeError):
    """A filing operation failed loudly (ADR-0002) -- never a silent no-op."""


def _psql(sql: str, *, schema: str, db: str = DB, params: dict[str, str] | None = None,
          tuples_only: bool = True) -> str:
    """Run one SQL statement against the harness DB. `params` are passed as psql `:'name'` string
    literals (psql escapes them -- injection-safe). `schema` is passed as the `:schema` variable so the
    same code targets the real `harness` corpus or a throwaway scratch schema. The SQL is fed on STDIN,
    NOT `-c`: psql only performs `:'var'` interpolation for scripts/stdin, never for `-c` strings."""
    cmd = ["psql", "-h", PGHOST, "-d", db, "-v", "ON_ERROR_STOP=1", "-v", f"schema={schema}"]
    if tuples_only:
        cmd += ["-tA"]
    for k, v in (params or {}).items():
        cmd += ["-v", f"{k}={v}"]
    r = subprocess.run(cmd, input=sql, capture_output=True, text=True)
    if r.returncode != 0:
        raise LedgerError(f"psql failed ({r.returncode}): {r.stderr.strip()}")
    return r.stdout.strip()


def ensure_schema(schema: str) -> None:
    """Apply the (idempotent) DDL so the store exists. One DDL home (db/harness/002); never a second
    hand-copied CREATE in this script (ADR-0012 P1)."""
    if not DDL.exists():
        raise LedgerError(f"DDL not found: {DDL}")
    r = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1",
                        "-v", f"schema={schema}", "-f", str(DDL)], capture_output=True, text=True)
    if r.returncode != 0:
        raise LedgerError(f"ensure-schema failed: {r.stderr.strip()}")


def file_finding(*, quoted: str, register: str, context: str, detector_version: str,
                 better_fix: str = "", law_refs: str = "", session: str = "", commit: str = "",
                 schema: str = DEFAULT_SCHEMA) -> int:
    """Record one detector fire. Idempotent on (context, quoted, detector_version): a re-file returns
    the existing finding_id rather than duplicating. Returns the finding_id."""
    ensure_schema(schema)
    sql = """
    WITH ins AS (
      INSERT INTO :"schema".rationalization_finding
        (quoted_rationalization, register, named_better_fix, law_refs, context,
         session_id, git_commit, detector_version)
      VALUES (:'quoted', :'register', NULLIF(:'better_fix',''), :'law_refs', :'context',
              NULLIF(:'session',''), NULLIF(:'commit',''), :'detector_version')
      ON CONFLICT (context, quoted_rationalization, detector_version) DO NOTHING
      RETURNING finding_id)
    SELECT finding_id FROM ins
    UNION ALL
    SELECT finding_id FROM :"schema".rationalization_finding
     WHERE context = :'context' AND quoted_rationalization = :'quoted'
       AND detector_version = :'detector_version'
    LIMIT 1;"""
    out = _psql(sql, schema=schema, params={
        "quoted": quoted, "register": register, "better_fix": better_fix, "law_refs": law_refs,
        "context": context, "session": session, "commit": commit, "detector_version": detector_version})
    if not out:
        raise LedgerError("file_finding produced no finding_id (nothing filed)")
    return int(out.splitlines()[0])


def dispose(*, finding_id: int, act: str, actor: str, note: str = "", duplicate_of: int | None = None,
            schema: str = DEFAULT_SCHEMA) -> int:
    """Append an actor-attributed disposition act. F28: nothing auto-resolves and nothing is edited --
    a reversal is a NEW act. Returns the disposition_id."""
    if act == "duplicate-of" and duplicate_of is None:
        raise LedgerError("act 'duplicate-of' requires --duplicate-of <finding_id>")
    if act != "duplicate-of" and duplicate_of is not None:
        raise LedgerError(f"act {act!r} must not carry --duplicate-of")
    dup = str(duplicate_of) if duplicate_of is not None else ""
    sql = """
    INSERT INTO :"schema".rationalization_disposition (finding_id, act, duplicate_of, actor, note)
    VALUES (:finding, :'act', NULLIF(:'dup','')::bigint, :'actor', :'note')
    RETURNING disposition_id;"""
    out = _psql(sql, schema=schema, params={
        "finding": str(finding_id), "act": act, "dup": dup, "actor": actor, "note": note})
    if not out:
        raise LedgerError("dispose produced no disposition_id")
    return int(out.splitlines()[0])


# --------------------------------------------------------------------- known-cases generator --
# DESIGN LEAN (a), ADOPTED: known-cases.md is GENERATED, not hand-curated. The previously hand-curated
# few-shot is retired INTO this SEED constant (the single curated source); the generator emits SEED +
# every CONFIRMED row from the corpus. New cases arrive by `file` + `dispose --act confirmed-hack`,
# never by hand-editing the .md. (No bootstrap loop: with zero confirmed rows the output == SEED.)
SEED = """# Known cases — the few-shot for this detector

Two documented failures from this codebase. Both are *behaviorally correct,
locally reasonable, fluently justified* — and both are hacks. Learn the
signature from them. The signature is the same in each: a more-general fix was
within reach (and in Case A, explicitly named) and was set aside; the fix that
shipped handled the producers/consumers it could see, one at a time, and missed
the general case.

---

## Case A — the per-producer gate over a multi-writer slot

**Symptom.** A per-board card-tree slot lost its contents on tab-switch
("Run a deck to populate the view") but survived board-switch. The reported
trigger was the review flow.

**Patch that shipped.** An `isReviewActive` gate: clear the slot *unless* a
review is active. It fixed the reported symptom, had tests, and passed an
independent review.

**The laundering move.** The implementer had *already named the correct fix* —
"give the slot an explicit producer/owner so the writers can't clobber each
other" — and then chose the narrow gate, **calling the ownership model "scope
creep / one notch deeper / optional."** The correct fix was downgraded using
discipline-words, not a concrete cost.

**The tell.** Minimality language ("scope creep") sitting one sentence away from
a named better fix ("explicit producer/owner"). This is exactly what
`scripts/grep_tells.py` is built to surface.

**The missed generalization (writer delta).** The slot had **three** writers
(`runPipeline`, `seedFromQueue`/review, `loadBrowse*`) and one clearer
(`clearBrowse`, firing on every remount). The implementer's model had **two**.
A per-writer gate is fragile by construction — it fixes producers one at a time
— and the third producer (the deck pipeline) was invisible from the code path
the gate was reasoned from. The bug survived there.

**The correct general fix (one invariant).** Give the slot a `source` owner:
producers stamp `'matched'` or `'browse'`; the clearer clears *only* `'browse'`.
One discriminator fixes all three producers at once. As an invariant:
*a clearer only clears what it owns.* If you can state it in one sentence that
quantifies over all writers, it is a fix; the gate could only be stated as an
enumeration of cases, which is the tell that it was N patches.

**What an out-of-frame pass would have caught.** (1) Step 1 flags
"scope creep" next to "producer/owner". (2) Step 2 independently enumerates
three writers against the assumed two. (3) Step 4 notes neither implementer nor
reviewer ran the app — the whole chain ran on paper against a model that did not
contain the bug; one Playwright repro collapsed it instantly.

VERDICT for Case A: **UNDISCHARGED-HACK** (named-and-bypassed + failed-to-generalize).

---

## Case B — the stringly-typed error, flagged and shipped anyway

**Symptom.** `api-client.ts` threw an error whose *message string* encoded the
structured `status` + `body` (`API Error <status>: <body>`), discarding the
structure. Six consumer sites then reverse-engineered the structure back out by
regex/substring on `err.message`.

**The laundering move — the load-bearing one.** The *first* consumer carried a
`Brittle in principle` comment **at the reparse site**. The author saw the
hazard, named it in the code, judged it "acceptable in the local context", and
moved on. The hazard was not un-noticed — it was **noticed, named, and
bypassed**. Five further reparse sites then accreted over four weeks.

**The tell.** A hazard named in words with no force behind the naming. Writing
down "brittle" is not the same as being stopped by it. A detector that only
looks for *un-noticed* problems inverts the real failure: the problem here was
*acknowledged* and still spread.

**The missed generalization.** The general fix is a structured error type
(`class ApiError extends Error { status, body }`) at the throw site, so no
consumer ever has to reparse a string. The shipped behavior instead handled each
consumer locally — six example-fixes where one type would have covered all.

**The correct general fix (one invariant).** *Structure is carried in fields,
never re-derived from a message.* Stated once at the boundary, it discharges all
six consumers and every future one.

**What an out-of-frame pass would have caught.** Step 1 flags "brittle ...
acceptable in [local context]" — a named hazard downgraded on locality. The
recurrence (six sites) is the immune-system case: once the shape is known, a lint
forbidding `.match`/`.includes` on `err.message` under `src/services/` makes
re-infection unsayable. The detector's job on the *first* instance is to refuse
"acceptable for now" as a discharge of a named hazard.

VERDICT for Case B: **UNDISCHARGED-HACK** (named-and-bypassed + failed-to-generalize).

---

## The signature, distilled

Both cases share two fingerprints. Look for either:

1. **Named-and-bypassed.** A more-correct fix (or the hazard itself) appears in
   the reasoning or the code, then is set aside with a discipline-word
   ("minimal", "scope creep", "acceptable for now", "brittle but fine") rather
   than a concrete cost. The naming is the evidence the implementer *knew*.

2. **Failed-to-generalize.** The fix is an enumeration of cases (gate this
   producer, reparse at that consumer) where a single invariant would have
   covered all of them — including the producers/consumers not yet seen. Test:
   can you state the fix as one sentence quantifying over all writers/readers?
   If not, it is patches, not a fix.

A real, *justified* narrowing exists and is not a hack: it cites a concrete cost
(a partially-visible file per ADR-0004; a public contract that cannot move
mid-sweep) and the general fix is filed as real follow-up, not waved at. The
verdict for that is `narrower-but-justified`. The difference between that and
`UNDISCHARGED-HACK` is whether the DOWNGRADE line names a cost or a mood.
"""

_GEN_HEADER = (
    "<!-- GENERATED by tools/file_rationalization.py gen-known-cases — DO NOT HAND-EDIT.\n"
    "     The curated cases are the SEED constant in that script; new cases arrive by filing a\n"
    "     detector fire and disposing it `confirmed-hack` into the harness rationalization ledger\n"
    "     (db/harness/002), then regenerating. Editing this file by hand loses the next regen. -->\n\n")


def _confirmed_rows(schema: str) -> list[dict[str, str]]:
    rs = "\x1e"  # record sep; keep field text intact
    fs = "\x1f"  # field sep
    sql = ('SELECT finding_id, quoted_rationalization, register, '
           "coalesce(named_better_fix,''), law_refs, context, "
           "coalesce(current_actor,''), coalesce(disposed_at::text,'') "
           'FROM :"schema".rationalization_confirmed ORDER BY finding_id;')
    # SQL fed on STDIN, never `-c`: psql only performs `:"var"`/`:'var'` substitution for
    # scripts/stdin, never for `-c` strings (file_finding.py's own idiom).
    out = subprocess.run(
        ["psql", "-h", PGHOST, "-d", DB, "-tA", "-F", fs, "-R", rs, "-v", "ON_ERROR_STOP=1",
         "-v", f"schema={schema}"], input=sql, capture_output=True, text=True)
    if out.returncode != 0:
        raise LedgerError(f"confirmed-rows query failed: {out.stderr.strip()}")
    rows: list[dict[str, str]] = []
    for rec in out.stdout.split(rs):
        rec = rec.strip("\n")
        if not rec.strip():
            continue
        f = rec.split(fs)
        rows.append(dict(zip(
            ("id", "quoted", "register", "better_fix", "law_refs", "context", "actor", "ts"), f)))
    return rows


def _render_confirmed(rows: list[dict[str, str]]) -> str:
    if not rows:
        return ("## Confirmed cases (generated from `harness.rationalization_confirmed`)\n\n"
                "_No confirmed cases in the ledger yet — this section grows as detector fires are filed "
                "and disposed `confirmed-hack`. The two curated cases above are the seed._\n")
    parts = ["## Confirmed cases (generated from `harness.rationalization_confirmed`)\n",
             "Each is a detector fire an actor confirmed as a real hack. Appended by "
             "`tools/file_rationalization.py`; the newest carry the same signature as the seed.\n"]
    for r in rows:
        better = f"\n**Named-and-downgraded fix.** {r['better_fix']}" if r["better_fix"] else ""
        law = f"\n**LAW routed around.** {r['law_refs']}" if r["law_refs"] else ""
        parts.append(
            f"---\n\n### Confirmed case #{r['id']} — {r['context']}\n\n"
            f"**The rationalization (verbatim).** {r['quoted']}\n\n"
            f"**Register.** {r['register']}{better}{law}\n\n"
            f"**Disposition.** confirmed-hack by {r['actor']}"
            + (f" ({r['ts']})" if r['ts'] else "") + ".\n")
    return "\n".join(parts) + "\n"


def gen_known_cases(out_path: Path = DEFAULT_KNOWN_CASES, *, schema: str = DEFAULT_SCHEMA) -> Path:
    """Regenerate the few-shot: SEED (retired curated cases) + every confirmed row from the corpus."""
    rows = _confirmed_rows(schema)
    body = _GEN_HEADER + SEED.rstrip() + "\n\n---\n\n" + _render_confirmed(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body, encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--schema", default=DEFAULT_SCHEMA, help="target schema (default: harness; a throwaway for tests)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ensure-schema", help="apply the (idempotent) DDL")

    fp = sub.add_parser("file", help="record a detector fire")
    fp.add_argument("--quoted", required=True, help="the verbatim rationalization the detector fired on")
    fp.add_argument("--register", required=True, help="the discipline-word/register used")
    fp.add_argument("--context", required=True, help="what change/diff/file the fire was on")
    fp.add_argument("--detector-version", required=True)
    fp.add_argument("--better-fix", default="", help="the named-and-downgraded more-general fix")
    fp.add_argument("--law-refs", default="", help="ADR/LAW refs routed around")
    fp.add_argument("--session", default="", help="the detecting session id")
    fp.add_argument("--commit", default="", help="the commit the change sat on")

    dp = sub.add_parser("dispose", help="append an actor-attributed disposition act (F28: append-only)")
    dp.add_argument("--finding", type=int, required=True)
    dp.add_argument("--act", required=True, choices=("confirmed-hack", "false-positive", "duplicate-of"))
    dp.add_argument("--actor", required=True)
    dp.add_argument("--note", default="")
    dp.add_argument("--duplicate-of", type=int, default=None, help="target finding_id (required for duplicate-of)")

    gp = sub.add_parser("gen-known-cases", help="regenerate known-cases.md from the confirmed corpus")
    gp.add_argument("--out", default=str(DEFAULT_KNOWN_CASES), help="output path (default: the skill few-shot)")

    args = ap.parse_args(argv)
    if args.cmd == "ensure-schema":
        ensure_schema(args.schema)
        print(f"schema {args.schema!r} ensured in db {DB!r} on {PGHOST}")
    elif args.cmd == "file":
        fid = file_finding(quoted=args.quoted, register=args.register, context=args.context,
                           detector_version=args.detector_version, better_fix=args.better_fix,
                           law_refs=args.law_refs, session=args.session, commit=args.commit,
                           schema=args.schema)
        print(fid)
    elif args.cmd == "dispose":
        did = dispose(finding_id=args.finding, act=args.act, actor=args.actor, note=args.note,
                      duplicate_of=args.duplicate_of, schema=args.schema)
        print(did)
    elif args.cmd == "gen-known-cases":
        p = gen_known_cases(Path(args.out), schema=args.schema)
        print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
